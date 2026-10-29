package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Independent versioned private read. The original six-field public TERMS contract is unchanged. */
public final class WarCurrentClaimInputsRead {
    public static final String PREFIX = "query-war-current-claim-inputs-v1-";
    public static final String PERMISSION = "allow_private_war_current_claim_inputs_v1";
    public record Selection(ArmyRetreatFrames.Current current, int warId) {
        public Selection {
            Objects.requireNonNull(current); require(warId > 0, "current claim inputs require a positive selected WarID");
            require(current.context().source().exactBuild().equals(WarCurrentClaimInputs.VERSION), "current claim inputs require exact actual4 source");
            ObjectNode snapshot = object(OpportunityJson.toNode(current.actual().semantic()));
            long count = NativeActiveWarsCodec.normalize(get(snapshot, "active_wars")).stream().filter(war -> war.warId().equals(java.math.BigInteger.valueOf(warId))).count();
            require(count == 1, "current claim inputs require one actual active selected WarID");
            ObjectNode hello = object(get(object(get(snapshot, "diagnostics")), "hello"));
            equal(get(hello, "expected_ck3_version"), WarCurrentClaimInputs.VERSION);
            require(text(get(hello, "expected_ck3_sha256")).equalsIgnoreCase(WarCurrentClaimInputs.EXE), "current claim input source EXE differs");
        }
        public NativeActiveWarsCodec.War selectedWar() {
            return NativeActiveWarsCodec.normalize(get(object(OpportunityJson.toNode(current.actual().semantic())), "active_wars"))
                    .stream().filter(war -> war.warId().equals(java.math.BigInteger.valueOf(warId))).findFirst().orElseThrow();
        }
        public Context context() { return current.context(); }
        public OperationKey operation() { return new OperationKey(PREFIX + warId); }
    }
    public record Observation(WarCurrentClaimInputs.Observation inputs, UInt64 querySequence, Obj normalizedResult) {
        public Observation { Objects.requireNonNull(inputs); Objects.requireNonNull(querySequence); Objects.requireNonNull(normalizedResult); }
        public boolean actionAuthority() { return false; }
    }
    private final PlanningReadPort reads;
    private final RootReadContractCatalog.Family<Selection, Observation> family;
    public WarCurrentClaimInputsRead(ExactRef definition, ExactRef decoder, PlanningReadPort actualReads) {
        reads = Objects.requireNonNull(actualReads); Objects.requireNonNull(definition); Objects.requireNonNull(decoder);
        family = new RootReadContractCatalog.Family<>("war-current-claim-inputs-v1", Selection.class, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.empty(), definition, decoder, WarCurrentClaimInputsRead::key, Selection::operation, selected ->
                new ReadContract<>("war-current-claim-inputs-v1-" + ArmyReadKey.digest(key(selected)), selected.operation(), Optional.empty(), PERMISSION,
                        ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.G2_PRIVATE_QUERY, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                        definition, (request, id) -> { verify(request, selected); return new NativeRequest(selected.operation().value(), Optional.empty(), new RawJson(bytes(empty()))); },
                        receipt -> decode(selected, receipt), receipt -> decode(selected, receipt)));
    }
    public List<RootReadContractCatalog.Family<?, ?>> families() { return List.of(family); }
    public ReadContract<Observation> contract(RootReadContractCatalog catalog, Selection selected) { return catalog.issue(family, selected); }
    public PlanningReadRequest request(Selection selected) {
        Context c = selected.context(); return new PlanningReadRequest(c.before(), c.source(), c.sessionId(), selected.operation(), arguments(selected), c.deadline());
    }
    public PlanningReadResult<Observation> read(ContinuityStorePort.Session same, RootReadContractCatalog catalog, Selection selected) {
        return reads.read(same, contract(catalog, selected), request(selected));
    }
    public static Observation decode(Selection selected, PlanningReadReceipt receipt) {
        verify(receipt.request(), selected);
        ObjectNode n = closed(ArmyNativeReadEvidence.result(ArmyNativeReadEvidence.contextForRequest(selected.context(), receipt.request()), receipt),
                "step", "accepted", "status", "query_sequence", "snapshot_revision", "backend_id", WarCurrentClaimInputs.DOMAIN);
        equal(get(n, "step"), selected.operation().value()); yes(get(n, "accepted")); equal(get(n, "status"), "observed");
        equal(get(n, "snapshot_revision"), selected.context().nativeRevision()); equal(get(n, "backend_id"), "native-headless");
        UInt64 sequence = positive(get(n, "query_sequence"));
        var inputs = WarCurrentClaimInputs.normalize(object(get(n, WarCurrentClaimInputs.DOMAIN)), selected.warId(), selected.context());
        require(inputs.targets().stream().map(target -> java.math.BigInteger.valueOf(target.titleId())).toList().equals(selected.selectedWar().targetedTitleIds()),
                "native current claim targets differ from the selected complete current War frame");
        ObjectNode normalized = n.deepCopy(); normalized.set(WarCurrentClaimInputs.DOMAIN, WarCurrentClaimInputs.encode(inputs));
        normalized.put("queried_snapshot_id", selected.context().before().frame().snapshotId());
        normalized.put("queried_revision", selected.context().before().frame().revision());
        normalized.put("queried_native_revision", selected.context().nativeRevision());
        return new Observation(inputs, sequence, DriverJson.object(bytes(normalized), DriverJson.MAX_NATIVE_BYTES));
    }
    private static Obj arguments(Selection selected) {
        return DriverJson.object(bytes(empty().put("war_id", selected.warId())), DriverJson.MAX_NATIVE_BYTES);
    }
    private static RawJson key(Selection selected) {
        Context c = selected.context(); ObjectNode key = empty().put("schema", "xar.war-current-claim-inputs-key/v1").put("war_id", selected.warId())
                .put("snapshot_id", c.before().frame().snapshotId()).put("public_revision", c.before().frame().revision())
                .put("native_revision", c.nativeRevision()).put("date_raw", c.dateRaw()).put("actor", c.playerId())
                .put("machine_id", c.before().machineId()).put("observation_version", c.before().observationVersion())
                .put("source_observed_at_utc", c.source().observedAtUtc()).put("source_exact_build", c.source().exactBuild())
                .put("episode", c.before().frame().episodeRunId()).put("session_id", c.sessionId()).put("binding", selected.current().actual().fullBindingSha256());
        key.set("game", c.before().game().toJson()); key.set("source", c.source().sourceRef().toJson()); key.set("original_native", selected.current().actual().originalEvidence().toJson()); return new RawJson(bytes(key));
    }
    private static void verify(PlanningReadRequest request, Selection selected) {
        Context c = selected.context(); require(request.before().equals(c.before()) && request.source().equals(c.source()) && request.sessionId().equals(c.sessionId())
                && request.operation().equals(selected.operation()) && request.arguments().equals(arguments(selected)), "current claim read crossed its exact source/frame/selection");
    }
}
