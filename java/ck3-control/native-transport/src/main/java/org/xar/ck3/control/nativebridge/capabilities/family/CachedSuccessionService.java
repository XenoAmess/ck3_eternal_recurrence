package org.xar.ck3.control.nativebridge.capabilities.family;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Public Service route over the sole registered planner reader; the caller supplies only its expected public revision. */
public final class CachedSuccessionService {
    public record Query(BigInteger expectedRevision) {
        public Query { StrictJson.require(expectedRevision != null && expectedRevision.signum() > 0
                && expectedRevision.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 expected revision required"); }
    }
    public record Context(ObservationIdentity before, G2Source source, String sessionId, Instant deadline) {
        public Context { Objects.requireNonNull(before); Objects.requireNonNull(source); StrictJson.text(sessionId); Objects.requireNonNull(deadline); }
    }
    @FunctionalInterface public interface RuntimeContext { Context current(Query request); }
    /** Must verify the actual current exact-build/source-qualified private permission. A DTO constructor is insufficient. */
    @FunctionalInterface public interface Admission { void verify(PlanningReadRequest request); }
    private static final OperationKey OPERATION = new OperationKey(CachedSuccession12004.STEP);
    private static final OpportunityJson.Obj EMPTY = (OpportunityJson.Obj) OpportunityJson.parse(new byte[] {'{', '}'});
    private final PlanningReadPort reads;
    private final RuntimeContext context;
    private final ReadContract<CachedSuccession12004.Observation> contract;
    public CachedSuccessionService(PlanningReadPort reads, RuntimeContext context, ReadContract<CachedSuccession12004.Observation> contract) {
        this.reads = Objects.requireNonNull(reads); this.context = Objects.requireNonNull(context); this.contract = Objects.requireNonNull(contract);
        StrictJson.require(contract.operation().equals(OPERATION)
                && contract.wireProfile() == ReadContract.WireProfile.SNAPSHOT_REVISION_ONLY
                && contract.permissionMode() == ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                && contract.permissionKey().equals(CachedSuccession12004.PERMISSION), "exact cached-succession read contract required");
    }
    /** The composition root installs this exact object in PlanningReadCoordinator before creating the public facade. */
    public static ReadContract<CachedSuccession12004.Observation> contract(ExactRef source, Admission admission) {
        Objects.requireNonNull(source); Objects.requireNonNull(admission);
        return new ReadContract<>("family/actor-cached-succession12004", OPERATION, Optional.empty(), CachedSuccession12004.PERMISSION,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.SNAPSHOT_REVISION_ONLY, source,
                request -> {
                    StrictJson.require(request.arguments().equals(EMPTY), "cached succession does not accept caller selectors");
                    admission.verify(request);
                    return new NativeRequest(CachedSuccession12004.STEP, Optional.empty(), new RawJson(new byte[] {'{', '}'}));
                }, CachedSuccessionService::decode);
    }
    public CachedSuccession12004.Observation query_actor_cached_succession_v1(Query request) {
        Context current = Objects.requireNonNull(context.current(Objects.requireNonNull(request)), "actual current runtime context required");
        StrictJson.require(current.before().frame().revision().equals(request.expectedRevision()), "public expected revision is stale");
        PlanningReadRequest actual = new PlanningReadRequest(current.before(), current.source(), current.sessionId(), OPERATION, EMPTY, current.deadline());
        PlanningReadResult<CachedSuccession12004.Observation> result = reads.read(contract, actual);
        if (result instanceof PlanningReadResult.Known<CachedSuccession12004.Observation> known) {
            StrictJson.require(known.receipt().request().equals(actual) && known.receipt().contractId().equals(contract.contractId())
                    && known.originalReceipt().bytes() > 0, "public cached query lost its original guarded archived read");
            StrictJson.require(known.value().equals(decode(known.receipt())), "cached public result differs from its actual original receipt");
            return known.value();
        }
        throw new IllegalStateException(((PlanningReadResult.Unavailable<CachedSuccession12004.Observation>) result).reason());
    }
    public static Query decodeQuery(RawJson arguments) {
        ObjectNode n = StrictJson.object(StrictJson.parse(arguments.bytes()), Set.of("expected_revision"));
        return new Query(StrictJson.integer(n.get("expected_revision"), BigInteger.ONE, StrictJson.UINT64_MAX));
    }
    public static CachedSuccession12004.Observation decode(PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt); var request = receipt.request(); var before = request.before();
        StrictJson.require(request.operation().equals(OPERATION) && request.arguments().equals(EMPTY)
                && receipt.original().nativeOk() && receipt.original().originalResultToken().isPresent(), "actual successful cached query token required");
        for (var guard : java.util.List.of(receipt.before(), receipt.after())) {
            StrictJson.require(guard.paused() && guard.mapReady() && guard.playerAlive()
                    && guard.binding().source().equals(request.source()) && guard.binding().sessionId().equals(request.sessionId())
                    && guard.binding().operation().equals(OPERATION), "actual living paused cached-query guard/source/session required");
        }
        StrictJson.require(receipt.before().binding().observed().equals(before)
                && receipt.after().binding().observed().equals(before)
                && receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256())
                && receipt.before().binding().connectionGeneration().equals(receipt.after().binding().connectionGeneration()), "cached query crossed its actual paused owner/frame");
        var frame = before.frame(); var identity = frame.identity();
        var binding = new CachedSuccession12004.Binding(frame.snapshotId(), frame.revision(), identity.nativeRevision(),
                identity.dateRaw().intValueExact(), before.game().pid(), receipt.before().binding().connectionGeneration(), identity.player().longValueExact());
        return CachedSuccession12004.decodeNative(receipt.original().originalResultToken().orElseThrow(), binding);
    }
}
