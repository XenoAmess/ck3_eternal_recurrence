package org.xar.ck3.control.nativebridge.capabilities.family;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.function.Supplier;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Two exact read routes over the one held coordinator. Submit remains the sole ActionCoordinator's authority. */
public final class ChildEducationFocusQueries {
    public static final String QUERY_CONTRACT = "family/child-education-focus12004/query/v1";
    public static final String RECEIPT_CONTRACT = "family/child-education-focus12004/receipt/v1";
    public static final String RECONCILIATION_RECEIPT_CONTRACT = "family/child-education-focus12004/receipt/reconciliation/v1";
    private static final OperationKey QUERY = new OperationKey(ChildEducationFocus.QUERY_STEP), RECEIPT = new OperationKey(ChildEducationFocus.RECEIPT_STEP);
    private ChildEducationFocusQueries() { }
    /** Root revalidates source-qualified permission and, for a receipt, the original unresolved durable intent under its writer session. */
    @FunctionalInterface public interface Admission { void verify(PlanningReadRequest request, Optional<Pending> pending); }
    /** Actual Root reopens the canonical attempt and original request/dispatch; this interface grants no authority by itself. */
    public interface CanonicalAdmission {
        void verifyCurrent(PlanningReadRequest request,Pending pending);
        void verifyOriginal(PlanningReadReceipt receipt,Pending pending);
    }
    public record QueryArguments(BigInteger expectedRevision, Selection selection) {
        public QueryArguments { FamilyObligations.positive64(expectedRevision); Objects.requireNonNull(selection); }
    }
    public record ReceiptArguments(BigInteger expectedRevision, Pending pending) {
        public ReceiptArguments { FamilyObligations.positive64(expectedRevision); Objects.requireNonNull(pending); ChildEducationFocus.verifyPending(pending); }
    }
    public record Contracts(ReadContract<Obj> query, ReadContract<Obj> receipt) {
        public Contracts { Objects.requireNonNull(query); Objects.requireNonNull(receipt); }
        public List<ReadContract<Obj>> all() { return List.of(query, receipt); }
    }
    public static Contracts contracts(ExactRef definitionSource, Admission admission) {
        Objects.requireNonNull(definitionSource); Objects.requireNonNull(admission);
        ReadContract<Obj> query = new ReadContract<>(QUERY_CONTRACT, QUERY, Optional.empty(), ChildEducationFocus.PERMISSION,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, definitionSource,
                (request, requestId) -> {
                    Context context = context(request); QueryArguments arguments = queryArguments(request.arguments()); revision(context, arguments.expectedRevision());
                    admission.verify(request, Optional.empty()); return nativeRequest(QUERY, context, arguments.selection(), Optional.empty());
                }, ChildEducationFocusQueries::decodeQueryReceipt, ChildEducationFocusQueries::decodeQueryReceipt);
        ReadContract<Obj> receipt = new ReadContract<>(RECEIPT_CONTRACT, RECEIPT, Optional.empty(), ChildEducationFocus.PERMISSION,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, definitionSource,
                (request, requestId) -> {
                    Context context = context(request); ReceiptArguments arguments = receiptArguments(request.arguments()); revision(context, arguments.expectedRevision()); continuity(context.frame(), arguments.pending());
                    admission.verify(request, Optional.of(arguments.pending())); return nativeRequest(RECEIPT, context, arguments.pending().selection(), Optional.of(arguments.pending().actionRequestId()));
                }, ChildEducationFocusQueries::decodeFocusReceipt, ChildEducationFocusQueries::decodeFocusReceipt);
        return new Contracts(query, receipt);
    }
    /** A separate canonical-pending observer over the same original native receipt producer. */
    public static ReadContract<Obj> reconciliationReceipt(ReadContract<Obj> actualOrdinaryReceipt,ExactRef actualProfileSource,
            CanonicalAdmission admission) {
        Objects.requireNonNull(actualOrdinaryReceipt);Objects.requireNonNull(actualProfileSource);Objects.requireNonNull(admission);
        StrictJson.require(actualProfileSource.bytes()>0&&actualOrdinaryReceipt.contractId().equals(RECEIPT_CONTRACT)
                &&actualOrdinaryReceipt.operation().equals(RECEIPT)&&actualOrdinaryReceipt.hasPureReplay()
                &&actualOrdinaryReceipt.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                &&actualOrdinaryReceipt.permissionMode()==ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                &&actualOrdinaryReceipt.permissionKey().equals(ChildEducationFocus.PERMISSION)
                &&actualOrdinaryReceipt.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP
                &&actualOrdinaryReceipt.requiredCapability().isEmpty(),"canonical focus observer requires its original ordinary native receipt contract");
        return new ReadContract<>(RECONCILIATION_RECEIPT_CONTRACT,RECEIPT,Optional.empty(),ChildEducationFocus.PERMISSION,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.RECONCILIATION_OBSERVATION,actualOrdinaryReceipt.sourceRef(),
                (request,requestId)->withProfile(actualProfileSource,()->{
                    ReceiptArguments arguments=canonicalReceiptArguments(request);admission.verifyCurrent(request,arguments.pending());
                    return nativeRequest(RECEIPT,context(request),arguments.pending().selection(),Optional.of(arguments.pending().actionRequestId()));
                }),
                receipt->decodeCanonicalReceipt(receipt,actualProfileSource,admission),
                receipt->decodeCanonicalReceipt(receipt,actualProfileSource,admission));
    }
    private static Obj decodeCanonicalReceipt(PlanningReadReceipt receipt,ExactRef profileSource,CanonicalAdmission admission) {
        return withProfile(profileSource,()->{
            Context actual=canonicalGuard(receipt);ReceiptArguments arguments=canonicalReceiptArguments(receipt.request());
            // Archive and live decode use original-source admission. Neither calls
            // the live preparation callback, legacy Driver history or a fresh query.
            admission.verifyOriginal(receipt,arguments.pending());
            Receipt value=ChildEducationFocus.decodeReceipt(receipt.original().originalResultToken().orElseThrow(),actual.frame(),arguments.pending());
            return project(value,actual,receipt.requestId(),Optional.of(arguments.pending()));
        });
    }
    /** Pure closed pending/request/pre-frame binding. This DATA check is not current or archival Root admission. */
    public static ReceiptArguments canonicalReceiptArguments(PlanningReadRequest request) {
        Objects.requireNonNull(request);StrictJson.require(request.operation().equals(RECEIPT)
                &&request.origin() instanceof CommandOrigin.Reconciliation,"focus canonical receipt has another operation or origin");
        var identity=request.origin().requireReconciliation();ReceiptArguments arguments=receiptArguments(request.arguments());
        Pending pending=arguments.pending();Context current=context(request);revision(current,arguments.expectedRevision());continuity(current.frame(),pending);
        var original=identity.pending().originalBefore().frame();var pre=pending.preFrame();
        StrictJson.require(request.source().equals(identity.source())&&request.sessionId().equals(identity.sessionId())
                &&pending.actionRequestId().equals(identity.pending().requestId())
                &&pre.snapshotId().equals(original.snapshotId())&&pre.episode().equals(original.episodeRunId())
                &&pre.nativeRevision().equals(original.identity().nativeRevision())
                &&BigInteger.valueOf(pre.dateRaw()).equals(original.identity().dateRaw())
                &&pre.controller()==(original.identity().player().longValueExact()&0xFFFF_FFFFL)
                &&pending.sourceContext().publicRevision().equals(original.revision()),
                "focus pending changed its actual canonical request or original pre-frame");
        return arguments;
    }
    private static Context canonicalGuard(PlanningReadReceipt receipt) {
        FamilyObligationsQueries.requireOriginalEnvelope(receipt);PlanningReadRequest request=receipt.request();
        StrictJson.require(receipt.contractId().equals(RECONCILIATION_RECEIPT_CONTRACT),"focus canonical receipt changed its fixed installed profile");
        ReceiptArguments arguments=canonicalReceiptArguments(request);var identity=request.origin().requireReconciliation();
        for(var guard:List.of(receipt.before(),receipt.after())) {
            // Root stores one source-bound basis and reopens its full original closure in canonical admission.
            // This local shape check grants no current or archived authority and does not flatten that basis.
            var binding=guard.binding();
            StrictJson.require(guard.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                    &&binding.origin() instanceof CommandOrigin.Reconciliation
                    &&identity.sameGuardFrame(binding.origin().requireReconciliation())
                    &&binding.source().equals(request.source())&&binding.sessionId().equals(request.sessionId())
                    &&binding.operation().equals(RECEIPT)&&binding.connectionGeneration().equals(identity.connectionGeneration())
                    &&binding.nativeEvidence().equals(identity.nativeEvidence())&&binding.capabilityEvidence().equals(identity.capabilityEvidence())
                    &&binding.supportingEvidence().size()==1
                    &&guard.originalBindingSha256().equals(identity.bindingSha256()),
                    "focus receipt lost its original canonical factual frame/source/custody binding");
        }
        requireCanonicalPacket(receipt,context(request),arguments.pending());return context(request);
    }
    private static void requireCanonicalPacket(PlanningReadReceipt read,Context actual,Pending pending) {
        read.original().custody().orElseThrow(()->new IllegalArgumentException("original focus query request chronology is absent")).verify(read);
        try {
            var response=NativeWire.decode(read.original().originalPacket());
            StrictJson.require(response instanceof NativeWire.CommandResult,"original focus response packet type differs");
            var result=(NativeWire.CommandResult)response;
            StrictJson.require(result.nativeOk()&&result.requestId().equals(read.requestId())
                    &&java.util.Arrays.equals(result.payload().value(),read.original().originalFrame().bytes())
                    &&result.result().token().map(NativeWire.Bytes::value).map(RawJson::new).equals(read.original().originalResultToken()),
                    "original focus response packet/token differs");
            var outgoing=NativeWire.decodeExecuteRequest(read.original().outbound().orElseThrow().originalPacket());
            NativeRequest expected=nativeRequest(RECEIPT,actual,pending.selection(),Optional.of(pending.actionRequestId()));
            StrictJson.require(!read.requestId().equals(pending.actionRequestId())&&outgoing.requestId().equals(read.requestId())
                    &&outgoing.step().equals(ChildEducationFocus.RECEIPT_STEP)
                    &&outgoing.expectedRevision().equals(Optional.of(actual.frame().nativeRevision()))&&outgoing.expectedSnapshotRevision().isEmpty()
                    &&StrictJson.parse(outgoing.normalizedAdditionalFields().value()).equals(StrictJson.parse(expected.additionalFields().bytes())),
                    "independent focus receipt query changed its original request fields or reused the action ACK");
        }catch(IOException failure){throw new UncheckedIOException("original focus native receipt packet is unreadable",failure);}
    }
    private static <T> T withProfile(ExactRef profileSource,Supplier<T> action) {
        try {
            var witness=SharedSourceFiles.observe(Path.of(profileSource.path()));
            StrictJson.require(witness.source().bytes()==profileSource.bytes()&&witness.source().sha256().equals(profileSource.sha256()),
                    "canonical focus profile source changed");
            try{return Objects.requireNonNull(action.get());}
            finally{SharedSourceFiles.assertUnchanged(witness);}
        }catch(IOException failure){throw new UncheckedIOException("canonical focus profile source is unavailable",failure);}
    }
    private static Obj decodeQueryReceipt(PlanningReadReceipt receipt) {
        Context context = guard(receipt, QUERY, QUERY_CONTRACT); QueryArguments arguments = queryArguments(receipt.request().arguments()); revision(context, arguments.expectedRevision());
        Query value = ChildEducationFocus.decodeQuery(receipt.original().originalResultToken().orElseThrow(), context.frame(), arguments.selection());
        return project(value, context, receipt.requestId(), Optional.empty());
    }
    private static Obj decodeFocusReceipt(PlanningReadReceipt actual) {
        Context context = guard(actual, RECEIPT, RECEIPT_CONTRACT); ReceiptArguments arguments = receiptArguments(actual.request().arguments()); revision(context, arguments.expectedRevision()); continuity(context.frame(), arguments.pending());
        Receipt value = ChildEducationFocus.decodeReceipt(actual.original().originalResultToken().orElseThrow(), context.frame(), arguments.pending());
        return project(value, context, actual.requestId(), Optional.of(arguments.pending()));
    }
    public static QueryArguments queryArguments(Obj value) {
        ObjectNode n = StrictJson.object(OpportunityJson.toNode(value), Set.of("child_full_id", "target_key", "expected_revision"));
        return new QueryArguments(StrictJson.integer(n.get("expected_revision"), BigInteger.ONE, StrictJson.UINT64_MAX),
                new Selection(StrictJson.integer(n.get("child_full_id"), 1, 0xffff_fffeL), target(n.get("target_key"))));
    }
    public static Obj queryArguments(QueryArguments value) {
        Objects.requireNonNull(value);var encoded=StrictJson.object().put("child_full_id",value.selection().child())
                .put("target_key",value.selection().target().wire()).put("expected_revision",value.expectedRevision());
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(encoded)),"typed focus query arguments");
    }
    public static ReceiptArguments receiptArguments(Obj value) {
        ObjectNode n = StrictJson.object(OpportunityJson.toNode(value), Set.of("pending", "expected_revision"));
        return new ReceiptArguments(StrictJson.integer(n.get("expected_revision"), BigInteger.ONE, StrictJson.UINT64_MAX), ChildEducationFocus.decodePending(new RawJson(StrictJson.canonical(n.get("pending")))));
    }
    public static Obj receiptArguments(ReceiptArguments value) {
        Objects.requireNonNull(value);var encoded=StrictJson.object().put("expected_revision",value.expectedRevision());
        encoded.set("pending",StrictJson.parse(ChildEducationFocus.verifyPending(value.pending()).bytes()));
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(encoded)),"typed focus receipt arguments");
    }
    public static NativeRequest nativeRequest(OperationKey operation, Context context, Selection selection, Optional<String> actionRequestId) {
        Objects.requireNonNull(operation); Objects.requireNonNull(context); Objects.requireNonNull(selection); Objects.requireNonNull(actionRequestId);
        StrictJson.require(operation.equals(QUERY) && actionRequestId.isEmpty() || operation.equals(RECEIPT) && actionRequestId.isPresent(), "focus query/receipt identity requires the exact route and original action ID");
        Frame frame = context.frame(); ObjectNode fields = StrictJson.object().put("expected_snapshot_id", frame.snapshotId()).put("expected_date_raw", frame.dateRaw())
                .put("expected_player_character_id", frame.controller()).put("episode_run_id", frame.episode()).put("child_full_id", selection.child()).put("target_key", selection.target().wire());
        actionRequestId.ifPresent(value -> fields.put("action_request_id", value));
        return new NativeRequest(operation.value(), Optional.empty(), new RawJson(StrictJson.canonical(fields)));
    }
    public static Obj project(NativeResult result, Context context, String requestId, Optional<Pending> pending) {
        Objects.requireNonNull(result); Objects.requireNonNull(context); StrictJson.text(requestId); Objects.requireNonNull(pending);
        if (result instanceof Query query) {
            StrictJson.require(pending.isEmpty() && query.equals(ChildEducationFocus.decodeQuery(query.original(), context.frame(), query.selection())), "typed focus query differs from original guarded source");
        } else if (result instanceof Receipt receipt) {
            Pending original = pending.orElseThrow(() -> new IllegalArgumentException("focus receipt must retain unresolved original pending"));
            ChildEducationFocus.verifyPending(original); StrictJson.require(receipt.equals(ChildEducationFocus.decodeReceipt(receipt.original(), context.frame(), original)), "typed focus receipt differs from original guarded source");
        } else throw new IllegalArgumentException("submit result must be handled by the unique action authority");
        ObjectNode n = (ObjectNode) StrictJson.parse(result.original().bytes()); n.put("request_id", requestId).put("source_public_revision", context.publicRevision()); n.set("source_context", ChildEducationFocus.encodeContext(context));
        if (result instanceof Receipt) n.put("action_request_id", pending.orElseThrow().actionRequestId());
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(n)), "complete source child-focus result");
    }
    public static Context context(PlanningReadRequest request) {
        Objects.requireNonNull(request); StrictJson.require(request.source().exactBuild().equals(FamilyObligations.Build.CURRENT4.exactBuild()), "actual current4 focus source qualification required");
        StrictJson.require(request.origin() instanceof CommandOrigin.Gameplay || request.origin() instanceof CommandOrigin.Reconciliation,
                "focus context requires an actual gameplay or explicit canonical reconciliation origin");
        var actual=request.origin() instanceof CommandOrigin.Gameplay?request.before():request.origin().requireReconciliation().factual();
        var frame = actual.frame(); var identity = frame.identity(); long controller = identity.player().longValueExact();
        StrictJson.require(controller >= Integer.MIN_VALUE && controller <= 0xffff_fffeL, "original signed/unsigned controller identity required");
        return new Context(new Frame(frame.snapshotId(), frame.episodeRunId(), identity.nativeRevision(), identity.dateRaw().intValueExact(), controller & 0xffff_ffffL), frame.revision());
    }
    private static Context guard(PlanningReadReceipt receipt, OperationKey operation, String contractId) {
        FamilyObligationsQueries.requireOriginalEnvelope(receipt);
        StrictJson.require(receipt.request().origin() instanceof CommandOrigin.Gameplay,"ordinary focus receipt cannot borrow canonical reconciliation admission");
        Objects.requireNonNull(receipt); PlanningReadRequest request = receipt.request(); Context context = context(request);
        StrictJson.require(request.operation().equals(operation) && receipt.contractId().equals(contractId) && receipt.original().nativeOk() && receipt.original().originalResultToken().isPresent(), "original registered successful focus read required");
        for (var guard : List.of(receipt.before(), receipt.after())) StrictJson.require(guard.paused() && guard.mapReady() && guard.playerAlive()
                && guard.binding().operation().equals(operation) && guard.binding().observed().equals(request.before()) && guard.binding().source().equals(request.source()) && guard.binding().sessionId().equals(request.sessionId()), "focus query requires actual same-session paused living source/frame");
        StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()) && receipt.before().binding().connectionGeneration().equals(receipt.after().binding().connectionGeneration()), "focus query crossed current source or held connection");
        return context;
    }
    private static void continuity(Frame current, Pending pending) {
        ChildEducationFocus.verifyPending(pending); StrictJson.require(current.episode().equals(pending.preFrame().episode()) && current.controller() == pending.preFrame().controller(), "pending focus belongs to another controller/episode");
    }
    private static void revision(Context context, BigInteger expected) { StrictJson.require(context.publicRevision().equals(expected), "focus public expected revision is stale"); }
    private static Key target(JsonNode value) {
        String key = StrictJson.text(value); for (Key candidate : Key.values()) if (candidate.wire().equals(key)) return candidate;
        throw new IllegalArgumentException("unknown exact education focus key");
    }
}
