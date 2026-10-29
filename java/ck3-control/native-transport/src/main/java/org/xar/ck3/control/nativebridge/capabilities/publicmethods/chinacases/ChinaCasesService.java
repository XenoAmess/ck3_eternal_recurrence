package org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.OriginalReadDecodeFailure;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesFacade;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.Frame;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.B1Frame;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract.*;

/** Public service delegates every native query to the original installed facade and its registered decoder. */
public final class ChinaCasesService {
    public record Context(ChinaCasesFacade.Context query, String bridgeVersion, String gameAdapterId,
            String gameVersion, String executableSha256) {
        public Context {
            Objects.requireNonNull(query); StrictJson.text(bridgeVersion); StrictJson.text(gameAdapterId); StrictJson.text(gameVersion);
            StrictJson.require(executableSha256!=null && executableSha256.matches("[0-9a-fA-F]{64}"),"observed executable SHA-256 required");
            StrictJson.text(query.before().frame().snapshotId());
        }
    }
    public static final class ReadResponse {
        private final Method method;
        private final RawJson publicJson;
        ReadResponse(Method method,RawJson publicJson) {
            this.method=Objects.requireNonNull(method);StrictJson.require(method.readOnly(),"read response method");this.publicJson=Objects.requireNonNull(publicJson);
        }
        public Method method() { return method; }
        public RawJson publicJson() { return publicJson; }
    }
    public sealed interface ReadOutcome permits Known, Unavailable { }
    public record Known(ReadResponse response, PlanningReadReceipt receipt, ExactRef originalReceipt) implements ReadOutcome {
        public Known { Objects.requireNonNull(response); Objects.requireNonNull(receipt); Objects.requireNonNull(originalReceipt); }
    }
    public record Unavailable(String reason, Optional<NativeActionPort.DispatchOutcome> original,
            Optional<OriginalReadDecodeFailure> decodeFailure) implements ReadOutcome {
        public Unavailable {
            StrictJson.text(reason);original=Objects.requireNonNull(original);decodeFailure=Objects.requireNonNull(decodeFailure);
            StrictJson.require(decodeFailure.isEmpty()||original.filter(value->value instanceof NativeActionPort.AckReceived ack&&ack.nativeOk()).isPresent(),
                    "a direct decode cause requires its actual successful original READ ACK");
        }
        public Unavailable(String reason,Optional<NativeActionPort.DispatchOutcome> original){this(reason,original,Optional.empty());}
    }
    private final ChinaCasesFacade queries;
    public ChinaCasesService(ChinaCasesFacade actualOriginal) { this.queries=Objects.requireNonNull(actualOriginal); }
    public ChinaCasesFacade originalFacade() { return queries; }

    public enum B1Anomaly {
        ACTIVE_STATE_MISMATCH, ACTIVE_ZERO_ROSTER, PROCESSING_EXCEEDS_ROSTER,
        QUOTA_TARGET_PROCESSING_MISMATCH, QUOTA_RECOUNT_PROCESSING_MISMATCH,
        QUOTA_TARGET_RECOUNT_MISMATCH, QUOTA_GENERATION_CASE_MISMATCH,
        NEGATIVE_PENDING_COUNT, CLOSED_STATE_INCOMPLETE;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public record B1Invariants(Optional<Boolean> activeMatchesState,Optional<Boolean> countsNonnegative,
            Optional<Boolean> processingWithinRoster,Optional<Boolean> quotaTargetConserved,
            Optional<Boolean> quotaRecountConserved,Optional<Boolean> quotaTargetMatchesRecount,Optional<Boolean> closedStateCoherent) {
        public B1Invariants {
            Objects.requireNonNull(activeMatchesState);Objects.requireNonNull(countsNonnegative);Objects.requireNonNull(processingWithinRoster);
            Objects.requireNonNull(quotaTargetConserved);Objects.requireNonNull(quotaRecountConserved);Objects.requireNonNull(quotaTargetMatchesRecount);Objects.requireNonNull(closedStateCoherent);
        }
    }
    public record B1Derived(B1Invariants invariants,List<B1Anomaly> anomalies) {
        public B1Derived { Objects.requireNonNull(invariants);anomalies=List.copyOf(anomalies); }
    }
    /** Port of the original B1 _derive. Null-valued unknowns remain distinct from false. */
    public static B1Derived deriveB1(B1Frame frame) {
        var state=frame.cycle().state().optional();var active=frame.cycle().active().optional();
        var subject=frame.roster().subjectCount().optional();var processing=frame.processing().count().optional();
        var quota=frame.quota();var target=List.of(quota.targetTop().optional(),quota.targetMiddle().optional(),quota.targetBottom().optional());
        var recount=List.of(quota.recountTop().optional(),quota.recountMiddle().optional(),quota.recountBottom().optional());
        var open=frame.pending().openCount().optional();var generation=quota.rebuildGeneration().optional();
        var closure=frame.closure().state().optional();var finalized=frame.closure().calibrationFinalized().optional();var rewards=frame.closure().rewardsIssued().optional();
        List<Optional<BigInteger>> counted=new ArrayList<>(List.of(subject,processing,open,generation));counted.addAll(target);counted.addAll(recount);
        boolean targetsKnown=present(target),recountsKnown=present(recount);
        Optional<Boolean> closed;
        if(state.isEmpty())closed=Optional.empty();
        else if(!state.get().equals(BigInteger.valueOf(8)))closed=Optional.of(true);
        else if(closure.isEmpty()||finalized.isEmpty()||rewards.isEmpty())closed=Optional.empty();
        else closed=Optional.of(closure.get().equals(BigInteger.valueOf(4))&&finalized.get()&&rewards.get());
        B1Invariants invariants=new B1Invariants(
                state.isEmpty()||active.isEmpty()?Optional.empty():Optional.of(active.get()==(state.get().compareTo(BigInteger.valueOf(8))<0)),
                present(counted)?Optional.of(counted.stream().allMatch(v->v.orElseThrow().signum()>=0)):Optional.empty(),
                subject.isEmpty()||processing.isEmpty()?Optional.empty():Optional.of(processing.get().compareTo(subject.get())<=0),
                processing.isEmpty()||!targetsKnown?Optional.empty():Optional.of(sum(target).equals(processing.get())),
                processing.isEmpty()||!recountsKnown?Optional.empty():Optional.of(sum(recount).equals(processing.get())),
                !targetsKnown||!recountsKnown?Optional.empty():Optional.of(target.equals(recount)),closed);
        List<B1Anomaly> anomalies=new ArrayList<>();
        if(state.isPresent() && !active.equals(Optional.of(state.get().compareTo(BigInteger.valueOf(8))<0)))anomalies.add(B1Anomaly.ACTIVE_STATE_MISMATCH);
        if(subject.equals(Optional.of(BigInteger.ZERO)) && active.equals(Optional.of(true)))anomalies.add(B1Anomaly.ACTIVE_ZERO_ROSTER);
        if(subject.isPresent()&&processing.isPresent()&&processing.get().compareTo(subject.get())>0)anomalies.add(B1Anomaly.PROCESSING_EXCEEDS_ROSTER);
        if(targetsKnown&&processing.isPresent()&&!sum(target).equals(processing.get()))anomalies.add(B1Anomaly.QUOTA_TARGET_PROCESSING_MISMATCH);
        if(recountsKnown&&processing.isPresent()&&!sum(recount).equals(processing.get()))anomalies.add(B1Anomaly.QUOTA_RECOUNT_PROCESSING_MISMATCH);
        if(targetsKnown&&recountsKnown&&!target.equals(recount))anomalies.add(B1Anomaly.QUOTA_TARGET_RECOUNT_MISMATCH);
        if(generation.isPresent()&&generation.get().signum()>0&&!quota.builtCaseSerial().optional().equals(frame.cycle().caseSerial().optional()))anomalies.add(B1Anomaly.QUOTA_GENERATION_CASE_MISMATCH);
        if(open.isPresent()&&open.get().signum()<0)anomalies.add(B1Anomaly.NEGATIVE_PENDING_COUNT);
        if(state.equals(Optional.of(BigInteger.valueOf(8)))&&closed.equals(Optional.of(false)))anomalies.add(B1Anomaly.CLOSED_STATE_INCOMPLETE);
        return new B1Derived(invariants,anomalies);
    }
    private static boolean present(List<Optional<BigInteger>> values) { return values.stream().allMatch(Optional::isPresent); }
    private static BigInteger sum(List<Optional<BigInteger>> values) { return values.stream().map(Optional::orElseThrow).reduce(BigInteger.ZERO,BigInteger::add); }

    public static BigInteger requireExpected(ReadRequest request, ChinaCasesFacade.Context context) {
        Objects.requireNonNull(request); Objects.requireNonNull(context);
        BigInteger actual=context.before().frame().revision();
        PublicUnsigned64.canonical(actual,PublicUnsigned64.Minimum.ZERO);
        BigInteger expected=request.expectedRevision() instanceof PublicUnsigned64.Value value?value.value():actual;
        StrictJson.require(actual.equals(expected),"expected_revision does not match the current snapshot revision");
        return expected;
    }
    /** No fallback read, retry, synthetic unavailable frame or second read coordinator. */
    public ReadOutcome query(ReadRequest request, Context context) {
        requireExpected(request,context.query());
        var c=context.query(); var nonce=request.nativeNonce();
        return switch(request.method()) {
            case B1 -> complete(request,context,queries.query_zhongguo_b1_cycle_snapshot_v1(c,nonce));
            case CASE -> complete(request,context,queries.query_zhongguo_case_snapshot_v1(c,ChinaCasesFacade.CaseKind.B1_PERFORMANCE,nonce,request.subject(),request.owner()));
            case AI_OWNED -> complete(request,context,queries.query_zhongguo_ai_owned_case_snapshot_v1(c,request.owner().orElseThrow(),request.subject().orElseThrow(),nonce));
            case RESULT -> complete(request,context,queries.query_zhongguo_result_case_snapshot_v1(c,request.owner().orElseThrow(),nonce));
            case PIP -> complete(request,context,queries.query_zhongguo_b2_pip_snapshot_v1(c,request.owner().orElseThrow(),nonce));
            case PROMOTION -> complete(request,context,queries.query_zhongguo_promotion_compensation_postcondition_v1(c,nonce));
            case AF5 -> complete(request,context,queries.query_zhongguo_compensation_af5_snapshot_v1(c,nonce));
            case PROJECTS -> complete(request,context,queries.query_zhongguo_projects_metrics_postcondition_v1(c,request.owner().orElseThrow(),request.subject(),nonce));
            case INCIDENT -> complete(request,context,queries.query_zhongguo_incident_snapshot_v1(c,request.owner().orElseThrow(),request.profile().orElseThrow(),nonce));
            case SCOREBOARD -> complete(request,context,queries.query_zhongguo_scoreboard_state_v1(c,nonce));
            case ACTIVATE_SCOREBOARD -> throw new IllegalArgumentException("activation must use Root's action authority");
        };
    }
    private <T extends Frame> ReadOutcome complete(ReadRequest request,Context context,PlanningReadResult<T> result) {
        var c=context.query();
        if (result instanceof PlanningReadResult.Unavailable<?> unavailable) {
            unavailable.decodeFailure().ifPresent(failure->{
                if(failure instanceof ChinaCasesFacade.OriginalDriverFailure actual)
                    queries.requireDirectOriginalFailure(actual,request.method().family(),c);
            });
            return new Unavailable(unavailable.reason(),unavailable.original(),unavailable.decodeFailure());
        }
        if (!(result instanceof PlanningReadResult.Known<T> known)) throw new IllegalArgumentException("unknown original China query outcome");
        PlanningReadReceipt receipt=known.receipt();
        StrictJson.require(receipt.request().before().equals(c.before()) && receipt.request().source().equals(c.source())
                && receipt.request().sessionId().equals(c.sessionId()) && receipt.request().operation().value().equals(request.method().family().step()),
                "original query request/frame/source/session differs");
        StrictJson.require(receipt.before().paused() && receipt.after().paused() && receipt.before().mapReady() && receipt.after().mapReady()
                && receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"query crossed the original paused frame");
        for (var guard:java.util.List.of(receipt.before(),receipt.after())) {
            var binding=guard.binding();
            StrictJson.require(binding.observed().equals(c.before()) && binding.source().equals(c.source())
                    && binding.sessionId().equals(c.sessionId()) && binding.connectionGeneration().equals(c.connectionGeneration()),
                    "query guard frame/source/session/generation changed");
        }
        // Re-run the actual registered original family decoder against the retained receipt. A supplied record is not a substitute.
        Frame original=ChinaCasesCodec.decodeOriginal(request.method(),receipt);
        StrictJson.require(original.equals(known.value()),"supplied China frame differs from its original decoder");
        ReadResponse response=ChinaCasesCodec.render(request,context,receipt,original);
        return new Known(response,receipt,known.originalReceipt());
    }
}
