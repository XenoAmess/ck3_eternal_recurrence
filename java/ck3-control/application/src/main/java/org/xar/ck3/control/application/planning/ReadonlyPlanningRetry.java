package org.xar.ck3.control.application.planning;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.math.BigInteger;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.RootPlanningReadGuard.HeirPreflightFailure;
import org.xar.ck3.control.application.effects.RootPlanningReadGuard.LocalRootRevisionFailure;
import org.xar.ck3.control.service.root.GiftPendingFrameReadyFailure;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/**
 * The original one-retry public planning budget. Only an authenticated actual failed READ can
 * mint its private control-flow marker. A copied packet, Unavailable reason or UNKNOWN is not a retry.
 * This class never invokes EXECUTE, dispatches an action or retains a failed planning view.
 */
public final class ReadonlyPlanningRetry {
    private ReadonlyPlanningRetry() { }
    private static final String ROOT = "query-campaign-root-context-v1";
    private static final String EXECUTOR_ERROR = "application-main typed query failed or its snapshot changed";
    private static final ThreadLocal<Budget> CURRENT = new ThreadLocal<>();
    @FunctionalInterface public interface PlanOnce { RawJson plan() throws IOException, InterruptedException; }
    public interface FailureSink {
        boolean active();
        void failed(Session same, ReadContract<?> contract, PlanningReadRequest request,
                PlanningReadResult.Unavailable<?> unavailable, PlanningReadCoordinator.FailedReadAttempt attempted,
                ActionPorts.OutcomeArchive originals) throws IOException;
    }
    private static final FailureSink SINK = new FailureSink() {
        @Override public boolean active() { return CURRENT.get() != null; }
        @Override public void failed(Session same, ReadContract<?> contract, PlanningReadRequest request,
                PlanningReadResult.Unavailable<?> unavailable, PlanningReadCoordinator.FailedReadAttempt attempted,
                ActionPorts.OutcomeArchive originals) throws IOException {
            Budget budget = CURRENT.get();
            if (budget == null) return;
            Objects.requireNonNull(attempted);
            attempted.requireOriginal(same, contract, request, unavailable, originals);
            if (!request.operation().value().equals(ROOT) || !attempted.prepared().step().equals(ROOT)
                    || !(attempted.original() instanceof NativeActionPort.AckReceived ack)
                    || ack.nativeOk() || ack.outbound().isEmpty()) return;
            Obj outbound;
            try { outbound = framed(ack.outbound().orElseThrow().originalPacket()); }
            catch (IllegalArgumentException malformed) { return; }
            Obj returned = DriverJson.object(ack.originalFrame().bytes(), RawJson.MAXIMUM_BYTES);
            if (!new Text(attempted.requestId()).equals(outbound.get("request_id"))
                    || !new Text(attempted.requestId()).equals(returned.get("request_id"))) return;
            Optional<Obj> classification = classifyCampaign(outbound, returned);
            if (classification.isEmpty()) return;
            String nativeError = OpportunityJson.text(returned.get("error"), "actual native error");
            if (nativeError.equals(EXECUTOR_ERROR)) {
                Obj failure = OpportunityJson.object(returned.get("typed_query_failure_v1"), "typed query failure");
                nativeError += "; typed_query_failure_v1=" + new String(DriverJson.encode(sorted(failure)),
                        java.nio.charset.StandardCharsets.UTF_8);
            }
            throw new QualifiedRejection(budget, same, contract, request, unavailable, attempted,
                    classification.orElseThrow(), "native gameplay step failed: " + nativeError);
        }
    };
    public static FailureSink sink() { return SINK; }
    private static final class Budget {
        private int remaining = 1;
        private final List<Obj> rejected = new ArrayList<>();
    }
    /** Constructor is private: only the checked live FailedReadAttempt callback above creates it. */
    // This control-flow marker retains live object identity; Java serialization is unsupported.
    @SuppressWarnings("serial")
    public static final class QualifiedRejection extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final Budget budget;
        private final Session same;
        private final ReadContract<?> contract;
        private final PlanningReadRequest request;
        private final PlanningReadResult.Unavailable<?> unavailable;
        private final PlanningReadCoordinator.FailedReadAttempt attempted;
        private final Obj projection;
        private QualifiedRejection(Budget budget, Session same, ReadContract<?> contract, PlanningReadRequest request,
                PlanningReadResult.Unavailable<?> unavailable, PlanningReadCoordinator.FailedReadAttempt attempted,
                Obj projection, String originalMessage) {
            super(originalMessage); this.budget=budget;this.same=same;this.contract=contract;this.request=request;
            this.unavailable=unavailable;this.attempted=attempted;this.projection=projection;
        }
        /** The coordinator's narrow pass-through cannot accept a foreign observer exception or copied DATA. */
        public void requireOriginalCallback(Session current, ReadContract<?> identical, PlanningReadRequest actual,
                PlanningReadResult.Unavailable<?> exact, Optional<PlanningReadCoordinator.FailedReadAttempt> origin,
                ActionPorts.OutcomeArchive originals) throws IOException {
            StrictJson.require(CURRENT.get()==budget && current==same && identical==contract && actual==request
                    && exact==unavailable && origin.filter(value->value==attempted).isPresent(),
                    "readonly planning marker lost its actual private callback and budget");
            attempted.requireOriginal(current, identical, actual, exact, originals);
        }
    }
    private record GuardPreflightOrigin(Session session, ReadContract<?> contract, PlanningReadRequest request) { }
    private record PlanPreflightOrigin(Session session, PlanningRequest request) { }
    /**
     * A live source-owned preflight proof is authenticated before its native/physical callback exits.
     * The retained marker is private and cannot be recreated from a copied exception or pure JSON proof.
     */
    // This control-flow marker retains live object identity; Java serialization is unsupported.
    @SuppressWarnings("serial")
    public static final class QualifiedPreflightRejection extends RuntimeException {
        private static final long serialVersionUID=1L;
        private final Budget budget;
        private final Session session;
        private final long headSequence;
        private final String headDigest;
        private final Optional<GuardPreflightOrigin> guard;
        private final Optional<PlanPreflightOrigin> plan;
        private final Obj projection;
        private final RuntimeException originalFailure;
        private boolean actualBeforeReadConfirmed;
        private QualifiedPreflightRejection(Budget budget, Session session,
                Optional<GuardPreflightOrigin> guard, Optional<PlanPreflightOrigin> plan,
                Obj projection, RuntimeException originalFailure, RuntimeException actualPrivateProof) throws IOException {
            super(originalFailure.getMessage(),actualPrivateProof);
            this.budget=budget;this.session=session;this.guard=guard;this.plan=plan;
            this.headSequence=session.head().state().sequence();this.headDigest=session.head().digest();
            this.projection=projection;this.originalFailure=originalFailure;
            StrictJson.require(guard.isPresent()!=plan.isPresent(),"one actual preflight origin required");
        }
        /**
         * The coordinator additionally checks its actual phase has no prepared/attempted native READ.
         * This rechecks the authenticated callback identity/head, not an already-closed physical lease.
         */
        public void requireGuardCallback(Session current, ReadContract<?> identical, PlanningReadRequest exact) throws IOException {
            GuardPreflightOrigin origin=guard.orElseThrow(
                    ()->new IllegalArgumentException("a post-planning marker is not a guard failure"));
            StrictJson.require(CURRENT.get()==budget && current==session && origin.session()==current
                    && origin.contract()==identical && origin.request()==exact
                    && current.head().state().sequence()==headSequence && current.head().digest().equals(headDigest),
                    "readonly preflight marker crossed its actual private guard/budget/head");
            actualBeforeReadConfirmed=true;
        }
    }
    /** Called only inside the original heir producer's private live callback window. */
    public static void heirPreflightFailed(HeirPreflightFailure actual) throws IOException {
        Objects.requireNonNull(actual); actual.requireOriginal();
        Budget budget=CURRENT.get();
        if(budget==null)throw actual.originalFailure();
        throw new QualifiedPreflightRejection(budget,actual.session(),
                Optional.of(new GuardPreflightOrigin(actual.session(),actual.contract(),actual.request())),
                Optional.empty(),actual.projection(),actual.originalFailure(),actual);
    }
    /** The actual ROOT service preflight compares its expected and observed public revision before READ preparation. */
    public static void rootRevisionFailed(LocalRootRevisionFailure actual) throws IOException {
        Objects.requireNonNull(actual); actual.requireOriginal();
        Budget budget=CURRENT.get();
        if(budget==null || !actual.retryEligible())throw new QualifiedRootRevisionFailure(actual);
        throw new QualifiedPreflightRejection(budget,actual.session(),
                Optional.of(new GuardPreflightOrigin(actual.session(),actual.contract(),actual.request())),
                Optional.empty(),actual.projection(),actual.originalFailure(),actual);
    }
    /** Authenticated original ROOT fault, independent of the retry classifier and budget. */
    // This control-flow marker retains live object identity; Java serialization is unsupported.
    @SuppressWarnings("serial")
    public static final class QualifiedRootRevisionFailure extends RuntimeException {
        private static final long serialVersionUID=1L;
        private final Session session;
        private final ReadContract<?> contract;
        private final PlanningReadRequest request;
        private final long sequence;
        private final String digest;
        private final Thread thread=Thread.currentThread();
        private final org.xar.ck3.control.application.effects.RootPlanningReadGuard.RootRevisionPreconditionFailure original;
        private boolean claimed;
        private QualifiedRootRevisionFailure(LocalRootRevisionFailure actual) throws IOException {
            super(actual.originalFailure().getMessage(),actual);
            // The caller validated this private proof inside the actual live source callback.
            session=actual.session();contract=actual.contract();request=actual.request();original=actual.originalFailure();
            sequence=session.head().state().sequence();digest=session.head().digest();
        }
        public void requireGuardCallback(Session same,ReadContract<?> identical,PlanningReadRequest exact) throws IOException {
            StrictJson.require(!claimed && Thread.currentThread()==thread && same==session && identical==contract && exact==request
                    && same.head().state().sequence()==sequence && same.head().digest().equals(digest),
                    "original ROOT fault crossed its actual before-read source/request/head");
            claimed=true;
        }
        public org.xar.ck3.control.application.effects.RootPlanningReadGuard.RootRevisionPreconditionFailure originalFailure() { return original; }
    }
    /** Called by the actual Gift source after its real bounded wait and full-source qualification. */
    public static void giftPendingFrameFailed(GiftPendingFrameReadyFailure actual) throws IOException {
        Objects.requireNonNull(actual); actual.requireOriginal();
        Budget budget=CURRENT.get();
        if(budget==null)throw actual.originalFailure();
        throw new QualifiedPreflightRejection(budget,actual.session(),Optional.empty(),
                Optional.of(new PlanPreflightOrigin(actual.session(),actual.request())),
                actual.projection(),actual.originalFailure(),actual);
    }
    /** A second proven original failure must preserve its original public fault and candidate, never a third plan. */
    // This control-flow marker retains live object identity; Java serialization is unsupported.
    @SuppressWarnings("serial")
    public static final class Exhausted extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final ExactRef original;
        private Exhausted(QualifiedRejection rejected) { super(rejected.getMessage(),rejected); original=rejected.attempted.originalRef(); }
        public ExactRef original() { return original; }
    }
    public static RawJson plan(PlanOnce actualWholePlan) throws IOException, InterruptedException {
        Objects.requireNonNull(actualWholePlan);
        Budget previous = CURRENT.get();
        boolean outer = previous == null;
        Budget budget = outer ? new Budget() : previous;
        if (outer) CURRENT.set(budget);
        try {
            while (true) {
                try {
                    RawJson planned = Objects.requireNonNull(actualWholePlan.plan());
                    if (!outer || budget.rejected.isEmpty()) return planned;
                    Obj result = DriverJson.object(planned.bytes(), RawJson.MAXIMUM_BYTES);
                    Obj marker = object("schema",new Text("xar.readonly-planning-replan/v1"),
                            "fresh_replans",number(1),"original_rejections",new Arr(new ArrayList<Value>(budget.rejected)),
                            "fresh_snapshot_id",optional(result,"snapshot_id"),"fresh_revision",optional(result,"revision"),
                            "business_actions_replayed",number(0));
                    return new RawJson(DriverJson.encode(result.with("readonly_planning_replan_v1",marker)));
                } catch (QualifiedPreflightRejection rejected) {
                    StrictJson.require(rejected.budget==budget && CURRENT.get()==budget,
                            "readonly preflight escaped its actual public planning budget");
                    if (rejected.guard.isPresent() && !rejected.actualBeforeReadConfirmed) throw rejected.originalFailure;
                    if (budget.remaining==0) throw rejected.originalFailure;
                    budget.remaining=0;budget.rejected.add(rejected.projection);
                } catch (QualifiedRejection rejected) {
                    StrictJson.require(rejected.budget==budget && CURRENT.get()==budget,
                            "readonly retry escaped its actual public planning scope");
                    if (budget.remaining == 0) throw new Exhausted(rejected);
                    budget.remaining=0; budget.rejected.add(rejected.projection);
                    // The callback re-enters the entire source-owned planner after its old scope/flush exits.
                }
            }
        } finally { if (outer) CURRENT.remove(); }
    }
    /** The source-owned guarded ROOT reader can share the same budget; this grants no retry proof by itself. */
    public static boolean claimGuardedCampaignRootRetry() {
        Budget current = CURRENT.get();
        if (current == null) return true;
        if (current.remaining != 1) return false;
        current.remaining=0; return true;
    }

    /**
     * Pure classification DATA for differential tests. It cannot create QualifiedRejection or a current scope.
     * Runtime calls it only after original consumed-READ/contract/request/head/archive verification.
     */
    public static Optional<Obj> classifyCampaign(Obj request, Obj result) {
        Objects.requireNonNull(request); Objects.requireNonNull(result);
        try {
            if (!new Text("execute_step").equals(request.get("type"))
                    || !number(1).equals(request.get("protocol_version"))
                    || !(request.get("request_id") instanceof Text id) || id.value().isEmpty()
                    || !new Text(ROOT).equals(request.get("step"))
                    || !new Text("command_result").equals(result.get("type"))
                    || !number(1).equals(result.get("protocol_version"))
                    || !id.equals(result.get("request_id")) || !new Bool(false).equals(result.get("ok"))) return Optional.empty();
            BigInteger revision = integer(request.get("expected_revision"));
            if (revision.signum() <= 0) return Optional.empty();
            if (new Text(EXECUTOR_ERROR).equals(result.get("error"))) {
                if (optional(result,"result") != Nil.INSTANCE || !(result.get("typed_query_failure_v1") instanceof Obj failure))
                    return Optional.empty();
                if (!failure.members().keySet().equals(Set.of("executor_enter","executor_exception","executor_finish",
                        "executor_typed_result","final_equal","final_read","frame_stable","query_type","stage",
                        "typed_result","wait_completed","wait_result"))
                        || !new Text("campaign").equals(failure.get("query_type"))
                        || !new Text("wait").equals(failure.get("stage"))
                        || !new Text("executor_failed").equals(failure.get("wait_result"))
                        || !new Bool(false).equals(failure.get("wait_completed"))
                        || !new Bool(false).equals(failure.get("executor_enter"))
                        || !object("code",number(0),"image",new Text("none"),"rva",Nil.INSTANCE).equals(failure.get("executor_exception")))
                    return Optional.empty();
                for (String key:List.of("executor_finish","executor_typed_result","final_equal","final_read","frame_stable","typed_result"))
                    if (failure.get(key)!=Nil.INSTANCE) return Optional.empty();
                return Optional.of(object("class",new Text("campaign_root_executor_not_entered"),
                        "business_submission",new Bool(false),"native_request_id",id,
                        "source_native_revision",new IntegerValue(revision),"typed_query_failure_v1",failure));
            }
            // The original Native driver appends every typed-query diagnostic to native_error.
            // Such a frame no longer has the exact original state_changed error required for this class.
            if (result.get("typed_query_failure_v1") instanceof Obj) return Optional.empty();
            if (!new Text("state_changed").equals(result.get("error"))
                    || !(result.get("campaign_root_preflight_failure_v1") instanceof Obj failure)
                    || !(failure.get("predicates") instanceof Obj predicates)
                    || !new Text("campaign").equals(failure.get("query_type"))) return Optional.empty();
            BigInteger requested = integer(failure.get("request_native_revision"));
            BigInteger worker = integer(failure.get("worker_native_revision"));
            if (new Text("preflight_revision_changed").equals(failure.get("stage"))) {
                if (!failure.members().keySet().equals(Set.of("query_type","stage","request_native_revision",
                        "worker_native_revision","predicates","read_attempted","cached_scalars","observed_scalars",
                        "differing_fields","truncated"))
                        || !new Bool(false).equals(failure.get("read_attempted"))
                        || !new Bool(false).equals(failure.get("truncated"))
                        || requested.signum()<=0 || requested.compareTo(worker)>=0 || !requested.equals(revision)
                        || !(failure.get("cached_scalars") instanceof Text cached) || cached.value().isEmpty()
                        || failure.get("observed_scalars")!=Nil.INSTANCE || failure.get("differing_fields")!=Nil.INSTANCE
                        || !object("revision_matches",new Bool(false),"worker_ready",new Bool(true),"previous_present",new Bool(true),
                                "observed_read",new Bool(false),"observed_equal",new Bool(false)).equals(predicates))
                    return Optional.empty();
                return Optional.of(object("class",new Text("campaign_root_preflight_revision_changed_before_read"),
                        "business_submission",new Bool(false),"native_request_id",id,"source_native_revision",new IntegerValue(requested),
                        "worker_native_revision",new IntegerValue(worker),"read_attempted",new Bool(false)));
            }
            if (!new Text("preflight_native_snapshot_changed").equals(failure.get("stage"))
                    || !new Bool(true).equals(failure.get("read_attempted"))
                    || !new Bool(false).equals(failure.get("truncated"))
                    || !new Bool(false).equals(predicates.get("observed_equal"))
                    || requested.signum()<=0 || !requested.equals(worker) || !requested.equals(revision)) return Optional.empty();
            for (String key:List.of("revision_matches","worker_ready","previous_present","observed_read"))
                if (!new Bool(true).equals(predicates.get(key))) return Optional.empty();
            return Optional.of(object("class",new Text("campaign_root_preflight_state_changed"),"business_submission",new Bool(false),
                    "native_request_id",id,"source_native_revision",new IntegerValue(requested),
                    "differing_fields",optional(failure,"differing_fields")));
        } catch (IllegalArgumentException malformed) { return Optional.empty(); }
    }
    private static Obj framed(byte[] original) {
        StrictJson.require(original.length>=5,"actual outbound packet is incomplete");
        int length=ByteBuffer.wrap(original,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt();
        StrictJson.require(length>0&&length<=RawJson.MAXIMUM_BYTES&&original.length==length+4,"actual outbound frame length differs");
        return DriverJson.object(Arrays.copyOfRange(original,4,original.length),RawJson.MAXIMUM_BYTES);
    }
    private static Value sorted(Value value) {
        if(value instanceof Obj object) {
            var result=new LinkedHashMap<String,Value>();
            object.members().keySet().stream().sorted().forEach(key->result.put(key,sorted(object.get(key))));
            return new Obj(result);
        }
        if(value instanceof Arr array)return new Arr(array.items().stream().map(ReadonlyPlanningRetry::sorted).toList());
        return value;
    }
    private static BigInteger integer(Value value) { return OpportunityJson.integer(value,"original native retry integer"); }
    private static IntegerValue number(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static Value optional(Obj object,String field) { return object.members().containsKey(field)?object.get(field):Nil.INSTANCE; }
    private static Obj object(Object... pairs) {
        var fields=new LinkedHashMap<String,Value>();
        for(int i=0;i<pairs.length;i+=2)fields.put((String)pairs[i],(Value)pairs[i+1]);
        return new Obj(fields);
    }
}
