package org.xar.ck3.control.nativebridge.capabilities.religion;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.xar.ck3.control.nativebridge.capabilities.religion.ReligionJson.*;

/** Single actual current-player query; source qualification, held-frame guards and full original packet are independent requirements. */
public final class PlayerHolyOrderContextRead {
    public static final String STEP = "query-player-holy-order-context-v1";
    public static final String DOMAIN = "player_holy_order_context_v1";
    public static final String PERMISSION = "allow_private_player_religion_context_query";
    public static final String CONTRACT_ID = "religion/player-holy-order-context-v1";
    public static final String RECONCILIATION_CONTRACT_ID = "religion/original-holy-hire-employer-observation-v1";
    public static final OperationKey OPERATION = new OperationKey(STEP);
    public record Sources(ExactRef pythonProducer, ExactRef pythonCostNormalizer, ExactRef pythonReinforcementNormalizer,
            ExactRef nativeMailbox, ExactRef nativeWire, ExactRef nativeContext, ExactRef nativeReinforcement, ExactRef nativeBuild4Binding) {
        public Sources {
            for (ExactRef source : List.of(pythonProducer, pythonCostNormalizer, pythonReinforcementNormalizer, nativeMailbox,
                    nativeWire, nativeContext, nativeReinforcement, nativeBuild4Binding)) need(source.bytes() > 0, "actual original holy-order source required");
        }
        public List<ExactRef> all() { return List.of(pythonProducer, pythonCostNormalizer, pythonReinforcementNormalizer,
                nativeMailbox, nativeWire, nativeContext, nativeReinforcement, nativeBuild4Binding); }
    }
    @FunctionalInterface public interface Admission { void verify(Sources sources, PlanningReadRequest request); }
    public record Metadata(String queriedSnapshotId, BigInteger queriedRevision, BigInteger queriedNativeRevision,
            int queryDateRaw, BigInteger queriedPlayerCharacterId, String backendId, String status) {
        public Metadata {
            need(queriedSnapshotId != null && !queriedSnapshotId.isEmpty(), "actual queried snapshot required");
            range(queriedRevision, BigInteger.ONE, U64); range(queriedNativeRevision, BigInteger.ONE, U64);
            range(queriedPlayerCharacterId, BigInteger.ZERO, U32.subtract(BigInteger.ONE));
            need(backendId != null && !backendId.isEmpty() && ("observed".equals(status) || "unavailable".equals(status)), "actual holy-order backend/status required");
        }
    }
    public record Observation(PlayerHolyOrderContext context, Metadata metadata) {
        public Observation {
            Objects.requireNonNull(context); Objects.requireNonNull(metadata);
            need(metadata.backendId().equals("ck3-" + context.build().version() + "-native-player-holy-order-context-v1"), "holy-order backend/build drift");
            need(metadata.status().equals(context.available() ? "observed" : "unavailable"), "holy-order source status drift");
            context.requireFrame(context.build(), metadata.queriedPlayerCharacterId(), BigInteger.valueOf(metadata.queryDateRaw()));
        }
    }
    private final PlanningReadPort reads;
    private final ReadContract<Observation> contract;
    private final ReadContract<Observation> reconciliationContract;
    public PlayerHolyOrderContextRead(PlanningReadPort reads, Sources sources, Admission admission) {
        this.reads = Objects.requireNonNull(reads); Objects.requireNonNull(sources); Objects.requireNonNull(admission);
        contract = descriptor(sources,admission,false);
        reconciliationContract = descriptor(sources,admission,true);
    }
    private static ReadContract<Observation> descriptor(Sources sources,Admission admission,boolean reconciliation) {
        return new ReadContract<>(reconciliation?RECONCILIATION_CONTRACT_ID:CONTRACT_ID, OPERATION, Optional.empty(), PERMISSION,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.G2_PRIVATE_QUERY,
                reconciliation?ReadContract.GuardMode.RECONCILIATION_OBSERVATION:ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, sources.pythonProducer(), (request, requestId) -> {
                    need(request.arguments().members().isEmpty(), "current holy-order query requires exact empty arguments");
                    need(reconciliation==(request.origin() instanceof CommandOrigin.Reconciliation),"holy-order query changed its original gameplay/reconciliation phase");
                    factualFrame(request);
                    verifySources(sources); admission.verify(sources, request);
                    return new NativeRequest(STEP, Optional.empty(), new RawJson(new byte[]{'{','}'}));
                }, receipt -> { verifySources(sources); return decode(receipt); }, PlayerHolyOrderContextRead::decode);
    }
    public ReadContract<Observation> contract() { return contract; }
    public ReadContract<Observation> reconciliationContract() { return reconciliationContract; }
    public RootReadContractCatalog.InstalledRead reconciliationInstalledRead(ExactRef actualDecoderSource) {
        need(actualDecoderSource!=null&&actualDecoderSource.bytes()>0,"actual holy-order Java decoder source required");
        return new RootReadContractCatalog.InstalledRead(reconciliationContract,actualDecoderSource);
    }
    /** DATA profile only. Root still verifies the identical installed object and original canonical writer membership. */
    public static void requireReconciliationProfile(ReadContract<?> actual) {
        need(actual.contractId().equals(RECONCILIATION_CONTRACT_ID)&&actual.operation().equals(OPERATION)
                &&actual.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                &&actual.permissionMode()==ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                &&actual.permissionKey().equals(PERMISSION)&&actual.requiredCapability().isEmpty()
                &&actual.wireProfile()==ReadContract.WireProfile.G2_PRIVATE_QUERY&&actual.hasPureReplay(),
                "only the exact independent holy-hire employer observation profile is eligible");
    }
    /** Pure original-attempt binding; it grants neither a query permit nor permission to repeat the hire. */
    public static void requireCanonicalReconciliation(ActionReceipt original,ActionState.Attempt attempt,
            ReconciliationIdentity identity,ReadContract<?> actual,PlanningReadRequest query) {
        requireReconciliationProfile(actual);
        need(original.state() instanceof ActionState.Unknown unknown&&unknown.attempt().filter(attempt::equals).isPresent()
                &&original.command().origin() instanceof CommandOrigin.Gameplay
                &&original.bodySha256().equals(ActionCodec.bodySha256(original.command())),
                "holy-order employer query requires the exact retained UNKNOWN gameplay Attempt");
        var rebound=identity.driverRelation()==ReconciliationIdentity.DriverRelation.EXACT
                ?ReconciliationIdentity.fromCanonical(original,identity.factual(),identity.source(),identity.sessionId(),identity.connectionGeneration(),
                    identity.pending().originalReceipt(),identity.pending().originalBeforeDriver(),identity.evidence(),identity.observedAt())
                :ReconciliationIdentity.fromCanonicalHistoryAppend(original,identity.factual(),identity.source(),identity.sessionId(),identity.connectionGeneration(),
                    identity.pending().originalReceipt(),identity.pending().originalBeforeDriver(),identity.evidence(),identity.observedAt(),identity.historyPoint().orElseThrow());
        need(rebound.equals(identity)&&query.origin() instanceof CommandOrigin.Reconciliation
                &&query.origin().requireReconciliation().sameGuardFrame(identity)&&query.operation().equals(OPERATION)
                &&query.arguments().members().isEmpty()&&query.source().equals(identity.source())&&query.sessionId().equals(identity.sessionId()),
                "holy-order employer query changed its actual canonical pending/full factual source binding");
        var outer=org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.decode(original.command().arguments());
        need(outer.kind()==org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.Kind.HIRE_HOLY_ORDER_V1
                &&outer.executionProfile()==org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.ExecutionProfile.SDK_ORDINARY
                &&outer.preflightReads().size()==1&&original.command().operation().value().equals("hire-holy-order-v1"),
                "only the original ordinary holy-hire action owns this reconciliation query");
        need(original.command().expected().equals(org.xar.ck3.control.application.effects.NativeArmyWarWindowEffects.expected(
                original.command().before(),original.command().source(),original.command().operation(),
                new RawJson(org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(original.command().arguments())))),
                "holy-order original expected employer profile drift");
        var call=(org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls.Hire)
                org.xar.ck3.control.nativebridge.capabilities.army.ArmyCallCodec.decode(
                    org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod.HIRE_HOLY_ORDER_V1,outer.publicArguments());
        call.revision().requireCurrent(original.command().before().frame().revision());
        var prepared=attempt.preparedRequest();
        need(prepared.step().equals("hire-holy-order-v1")&&prepared.requiredCapability().filter("game.command.hire-holy-order-v1"::equals).isPresent(),
                "holy-order original prepared request changed its operation/capability");
        var fields=StrictJson.object(StrictJson.parse(prepared.additionalFields().bytes()),Set.of("holy_order_id"));
        need(StrictJson.integer(fields.get("holy_order_id"),0,0xffff_fffeL)==call.id().value(),"holy-order original selected full ID drift");
    }
    /** The operation admits exactly ordinary gameplay or its independently installed original-pending phase. */
    public static org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity factualFrame(PlanningReadRequest request) {
        need(request.operation().equals(OPERATION)&&request.arguments().members().isEmpty(),"exact empty holy-order current-player query required");
        if(request.origin() instanceof CommandOrigin.Reconciliation)return request.reconciliationBefore();
        need(request.origin() instanceof CommandOrigin.Gameplay,"holy-order query has no terminal/frontend origin");
        return request.before();
    }
    private static BigInteger nativeRevision(PlanningReadReceipt receipt){return factualFrame(receipt.request()).frame().identity().nativeRevision();}
    private static BigInteger date(PlanningReadReceipt receipt){return factualFrame(receipt.request()).frame().identity().dateRaw();}
    private static BigInteger player(PlanningReadReceipt receipt){return factualFrame(receipt.request()).frame().identity().player();}
    /** The composition root registers this identical producer object once, with its exact Java decoder source.
     * The contract itself retains its source-qualified readonly permission; no mutation permission is created.
     */
    public RootReadContractCatalog.InstalledRead installedRead(ExactRef actualDecoderSource) {
        need(actualDecoderSource != null && actualDecoderSource.bytes() > 0, "actual holy-order Java decoder source required");
        return new RootReadContractCatalog.InstalledRead(contract, actualDecoderSource);
    }
    public PlanningReadResult<Observation> query_player_holy_order_context_private_v1(PlanningReadRequest request) {
        need(request.operation().equals(OPERATION), "exact holy-order route required"); return reads.read(contract, request);
    }
    public PlanningReadResult<Observation> query_player_holy_order_context_private_v1(Session borrowed, PlanningReadRequest request) {
        Objects.requireNonNull(borrowed); need(request.operation().equals(OPERATION), "exact holy-order route required");
        return reads.read(borrowed, contract, request);
    }
    private static void verifySources(Sources sources) {
        for (ExactRef ref : sources.all()) {
            try {
                var witness = SharedSourceFiles.observe(Path.of(ref.path()));
                need(witness.source().bytes() == ref.bytes() && witness.source().sha256().equals(ref.sha256()), "holy-order original source bytes/SHA drift");
                SharedSourceFiles.assertUnchanged(witness);
            } catch (IOException failure) { throw new IllegalArgumentException("holy-order actual original source unavailable", failure); }
        }
    }
    public static Observation decode(PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt);
        boolean reconciliation=receipt.request().origin() instanceof CommandOrigin.Reconciliation;
        need(receipt.contractId().equals(reconciliation?RECONCILIATION_CONTRACT_ID:CONTRACT_ID) && receipt.request().operation().equals(OPERATION) &&
                receipt.request().arguments().members().isEmpty(), "wrong holy-order contract/request/arguments");
        var factual=factualFrame(receipt.request());
        for (var guard : List.of(receipt.before(), receipt.after())) {
            boolean sameOrigin=reconciliation
                    ?guard.binding().origin() instanceof CommandOrigin.Reconciliation&&guard.readiness() instanceof PlanningReadGuard.Reconciliation
                        &&guard.binding().origin().requireReconciliation().sameGuardFrame(receipt.request().origin().requireReconciliation())
                        &&guard.originalBindingSha256().equals(receipt.request().origin().requireReconciliation().bindingSha256())
                    :guard.binding().origin() instanceof CommandOrigin.Gameplay&&guard.readiness() instanceof PlanningReadGuard.Gameplay
                        &&guard.binding().observed().equals(factual)&&guard.paused()&&guard.mapReady()&&guard.playerAlive();
            need(sameOrigin&&guard.binding().operation().equals(OPERATION)&&
                    guard.binding().source().equals(receipt.request().source()) &&
                    guard.binding().sessionId().equals(receipt.request().sessionId()) &&
                    (!reconciliation||guard.binding().nativeEvidence().equals(receipt.request().origin().requireReconciliation().nativeEvidence())),
                    "holy-order read crossed its actual complete gameplay or original-pending frame");
        }
        need(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()) &&
                receipt.before().binding().capabilityEvidence().equals(receipt.after().binding().capabilityEvidence()) &&
                receipt.before().binding().connectionGeneration().equals(receipt.after().binding().connectionGeneration()),
                "holy-order native/modal/source/connection binding changed during read");
        ObjectNode result = originalResult(receipt);
        StrictJson.object(result, Set.of("step", "accepted", "status", "private_build", "read_only", "advertised",
                "game_version", "executable_sha256", "domain_key", "backend_id", "snapshot_revision", "date_raw", "player_holy_order_context"));
        equal(result, "step", STEP); yes(result, "accepted"); yes(result, "private_build");
        yes(result, "read_only"); no(result, "advertised"); equal(result, "domain_key", DOMAIN);
        var build = PlayerReligionContext.Build.exact(text(result, "game_version"), text(result, "executable_sha256"));
        need(build == connectedBuild(receipt), "holy-order query build differs from actual connected native hello");
        equal(result, "backend_id", "ck3-" + build.version() + "-native-player-holy-order-context-v1");
        equal(result, "snapshot_revision", nativeRevision(receipt)); equal(result, "date_raw", date(receipt));
        PlayerHolyOrderContext context = PlayerHolyOrderContext.decode(field(result, "player_holy_order_context"));
        context.requireFrame(build, player(receipt), date(receipt));
        String status = text(result, "status"); need(status.equals(context.available() ? "observed" : "unavailable"), "holy-order source availability/status drift");
        return new Observation(context, new Metadata(factual.frame().snapshotId(), factual.frame().revision(),
                nativeRevision(receipt), date(receipt).intValueExact(), player(receipt), text(result, "backend_id"), status));
    }
    private static ObjectNode originalResult(PlanningReadReceipt receipt) {
        try {
            var decoded = NativeWire.decode(receipt.original().originalPacket());
            need(decoded instanceof NativeWire.CommandResult, "actual holy-order original packet must be command_result");
            var packet = (NativeWire.CommandResult) decoded;
            need(packet.requestId().equals(receipt.requestId()) && packet.nativeOk() && receipt.original().nativeOk() &&
                    Arrays.equals(packet.payload().value(), receipt.original().originalFrame().bytes()), "holy-order original packet/frame/request drift");
            ObjectNode frame = object(NativeWire.parse(packet.payload().value()));
            StrictJson.object(frame, Set.of("type", "protocol_version", "request_id", "ok", "result"));
            ObjectNode result = object(field(frame, "result"));
            need(receipt.original().originalResultToken().isPresent() &&
                    parse(receipt.original().originalResultToken().orElseThrow()).equals(result), "holy-order original token differs from complete native packet");
            return result;
        } catch (IOException failure) { throw new IllegalArgumentException("malformed actual holy-order native packet", failure); }
    }
    private static PlayerReligionContext.Build connectedBuild(PlanningReadReceipt receipt) {
        try {
            var decoded = NativeWire.decode(originalPacket(receipt.before().binding().capabilityEvidence()));
            need(decoded instanceof NativeWire.Hello, "actual qualified hello required");
            var hello = (NativeWire.Hello) decoded;
            need(hello.pid() == factualFrame(receipt.request()).game().pid() &&
                    hello.connectionGeneration().equals(receipt.before().binding().connectionGeneration()) &&
                    hello.buildMatch() && hello.adapterStatus().equals("ready"), "holy-order original hello PID/connection/source drift");
            for (var build : PlayerReligionContext.Build.values()) if (build.sha256().equalsIgnoreCase(hello.gameSha256())) return build;
            throw new IllegalArgumentException("unknown actual holy-order executable SHA");
        } catch (IOException failure) { throw new IllegalArgumentException("malformed actual holy-order hello", failure); }
    }
    public static ObjectNode flattened(Observation observation) {
        Objects.requireNonNull(observation); var context = observation.context(); var metadata = observation.metadata();
        ObjectNode n = context.encode();
        n.put("backend_id", metadata.backendId()).put("domain_key", DOMAIN).put("status", metadata.status()).put("read_only", true)
                .put("advertised", false).put("exact_ck3_build", context.build().version()).put("exe_sha256", context.build().sha256())
                .put("queried_snapshot_id", metadata.queriedSnapshotId()).put("queried_revision", metadata.queriedRevision())
                .put("queried_native_revision", metadata.queriedNativeRevision()).put("snapshot_revision", metadata.queriedNativeRevision())
                .put("query_date_raw", metadata.queryDateRaw());
        return n;
    }
}
