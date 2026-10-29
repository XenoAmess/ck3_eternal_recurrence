package org.xar.ck3.control.nativebridge.capabilities.army;

import java.io.IOException;
import java.time.Instant;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeDirectFixedWindowObservation;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Actual public query and same-frame observation cache. Closing a window belongs to the sole action service. */
public final class ArmyWindowService {
    @FunctionalInterface public interface Deadline { Instant open(); }
    /** Installed once by the same actual Root before exposure; the port owns the calls-before-writer lock order. */
    @FunctionalInterface public interface PublicQueryAccess {
        Reply read(ArmyCalls.Frame input, Instant deadline) throws IOException, InterruptedException;
    }
    public sealed interface Reply permits KnownQuery,ReadDeferred { ArmyCalls.Frame input(); Context context(); }
    public record ReadDeferred(ArmyWindowQueryDeferred.Deferred original) implements Reply {
        public ReadDeferred { Objects.requireNonNull(original); }
        public ArmyCalls.Frame input() { return original.input(); }
        public Context context() { return original.context(); }
    }
    public record KnownQuery(ArmyCalls.Frame input, Context context, PlanningReadResult.Known<ArmyWindowCodec.Observation> original,
                        Optional<NativeDirectFixedWindowObservation.Original> priorClose) implements Reply {
        public KnownQuery {
            Objects.requireNonNull(input); Objects.requireNonNull(context); Objects.requireNonNull(original);
            priorClose = Objects.requireNonNull(priorClose);
            require(ArmyWindowReads.kind(input.method()) == original.value().kind()
                    && original.value().operation() == ArmyWindowCodec.Operation.QUERY, "fixed-window response belongs to another public query");
            var request = original.receipt().request();
            require(request.origin() instanceof CommandOrigin.Gameplay && request.before().equals(context.before())
                    && request.source().equals(context.source()) && request.sessionId().equals(context.sessionId())
                    && request.deadline().equals(context.deadline())
                    && request.operation().value().equals(original.value().kind().step(ArmyWindowCodec.Operation.QUERY)),
                    "public window QUERY requires its same original Gameplay frame/source/session/deadline/operation");
            priorClose.ifPresent(prior -> requirePublicQueryPresentation(input, context, original, prior));
        }
        public KnownQuery(ArmyCalls.Frame input, Context context, PlanningReadResult.Known<ArmyWindowCodec.Observation> original) {
            this(input, context, original, Optional.empty());
        }
    }
    public record Captured(ArmyRetreatFrames.Current frame, PlanningReadResult.Known<ArmyWindowCodec.Observation> original) {
        public Captured { Objects.requireNonNull(frame); Objects.requireNonNull(original); }
    }
    private final ContinuityWriter writer; private final ArmyRetreatFrames frames; private final ArmyWindowReads reads;
    private final Supplier<RootReadContractCatalog> catalog; private final Deadline deadline;
    private final EnumMap<ArmyWindowCodec.Kind,Captured> observations = new EnumMap<>(ArmyWindowCodec.Kind.class);
    private final AtomicReference<PublicQueryAccess> publicQueries = new AtomicReference<>();
    public ArmyWindowService(ContinuityWriter originalWriter, ArmyRetreatFrames frames, ArmyWindowReads reads, Supplier<RootReadContractCatalog> catalog, Deadline deadline) {
        writer = Objects.requireNonNull(originalWriter); this.frames = Objects.requireNonNull(frames); this.reads = Objects.requireNonNull(reads); this.catalog = Objects.requireNonNull(catalog); this.deadline = Objects.requireNonNull(deadline);
    }
    public Reply query_war_declared_overview_v1(ArmyCalls.Frame input) { require(input.method() == PublicMethod.QUERY_WAR_DECLARED_OVERVIEW_V1, "wrong overview public method"); return run(input); }
    public Reply query_war_results_window_v1(ArmyCalls.Frame input) { require(input.method() == PublicMethod.QUERY_WAR_RESULTS_WINDOW_V1, "wrong results public method"); return run(input); }
    public void bindPublicQueryAccess(PublicQueryAccess actualSameRootAccess) {
        require(publicQueries.compareAndSet(null, Objects.requireNonNull(actualSameRootAccess)), "actual Root public window query access already installed");
    }
    private Reply run(ArmyCalls.Frame input) {
        try {
            Instant end = Objects.requireNonNull(deadline.open()); PublicQueryAccess access = publicQueries.get();
            // Root must acquire its actual calls lock before borrowing the canonical writer.
            if (access != null) {
                Reply reply = Objects.requireNonNull(access.read(input,end));
                require(reply.input().equals(input), "actual Root returned another public window query selection");
                return reply;
            }
            return writer.locked(session -> read(session,input,end));
        } catch (IOException error) { throw new java.io.UncheckedIOException(error); }
        catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IllegalStateException("actual Root public window query interrupted",interrupted); }
    }
    /** Uses the same actual negative dispatch; never fabricates a Known or queries a second time. */
    public Reply presentUnavailable(ArmyCalls.Frame input, org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete actualBefore,
            PlanningReadRequest actualRequest, PlanningReadResult.Unavailable<ArmyWindowCodec.Observation> unavailable) {
        try {
            var deferred = ArmyWindowQueryDeferred.from(input,actualBefore,actualRequest,unavailable);
            if (deferred.isPresent()) return new ReadDeferred(deferred.orElseThrow());
        } catch (IOException malformedOriginal) {
            throw new java.io.UncheckedIOException(malformedOriginal);
        }
        throw ArmyWindowQueryFailure.from(ArmyWindowReads.kind(input.method()),unavailable);
    }
    /** No reads, writes, reconciliation or observation here: presents the same private canonical query proof. */
    public Reply presentPublicQuery(ArmyCalls.Frame input, PlanningReadResult.Known<ArmyWindowCodec.Observation> sameKnown,
                                   NativeDirectFixedWindowObservation.Original actualCanonicalOriginal) {
        Objects.requireNonNull(actualCanonicalOriginal);
        var owner = actualCanonicalOriginal.ownerQuery().orElseThrow(() -> new IllegalArgumentException("canonical original has no retained actual owner query"));
        var current = owner.current(); var request = owner.originalQuery().request();
        var context = new Context(current.identity(), current.source(), current.sessionId(), request.deadline());
        Reply reply = new KnownQuery(input, context, sameKnown, Optional.of(actualCanonicalOriginal));
        observations.remove(ArmyWindowReads.kind(input.method()));
        return reply;
    }
    private static void requirePublicQueryPresentation(ArmyCalls.Frame input, Context context,
            PlanningReadResult.Known<ArmyWindowCodec.Observation> known, NativeDirectFixedWindowObservation.Original prior) {
        var owner = prior.ownerQuery().orElseThrow(() -> new IllegalArgumentException("private original lacks its actual owner query"));
        var query = owner.originalQuery(); var current = owner.current();
        NativeDirectFixedWindowObservation.requirePublicOwnerQuery(query.request(), current);
        require(query.equals(known.receipt()) && context.before().equals(current.identity()) && context.source().equals(current.source())
                && context.sessionId().equals(current.sessionId()) && context.deadline().equals(query.request().deadline()),
                "public owner query crossed its exact canonical receipt/current/context");
        input.revision().requireCurrent(current.identity().frame().revision());
        var decoded = ArmyWindowCodec.decode(ArmyWindowReads.kind(input.method()), ArmyWindowCodec.Operation.QUERY,
                query.original().originalFrame().bytes(), query.requestId(), context, current.connectionGeneration(), ArmyWindowCodec.driverGeneration(current));
        require(decoded.equals(known.value()), "public owner query value differs from its strict original TOP/owner/source decoder");
        var presented = ArmyJson.parse(owner.normalizedQuery().bytes());
        boolean observation = presented.has("prior_close_execution_observation"), deferred = presented.has("close_retry_deferred_for_native_frame");
        require(observation == owner.executionResolved() && deferred == owner.executionResolved(), "public prior-close metadata differs from the private canonical resolution");
        presented.remove(List.of("prior_close_execution_observation","close_retry_deferred_for_native_frame"));
        require(presented.equals(decoded.normalized()), "public owner query changed its original full response outside canonical prior-close metadata");
        // available=false is a genuine full QUERY result; its unresolved canonical UNKNOWN is retained.
    }
    public Reply read(ContinuityStorePort.Session same, ArmyCalls.Frame input, Instant deadline) {
        try {
            var before = frames.current(deadline); input.revision().requireCurrent(before.context().before().frame().revision()); var kind = ArmyWindowReads.kind(input.method()); observations.remove(kind);
            var selection = new ArmyWindowReads.Selection(input,before.context(),before.actual().connectionGeneration(),ArmyWindowReads.driverGeneration(before.actual()));
            var capture = reads.capture(same,Objects.requireNonNull(catalog.get()),selection);
            if (capture.result() instanceof PlanningReadResult.Unavailable<ArmyWindowCodec.Observation> unavailable)
                return presentUnavailable(input,before.actual(),capture.request(),unavailable);
            var known = (PlanningReadResult.Known<ArmyWindowCodec.Observation>) capture.result();
            var after = frames.current(deadline); ArmyRetreatFrames.same(before,after);
            require(known.value().normalized().equals(ArmyWindowReads.decode(selection,known.receipt()).normalized()), "fixed-window captured response differs from its actual original receipt");
            observations.put(kind,new Captured(before,known)); return new KnownQuery(input,before.context(),known);
        } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IllegalStateException("fixed-window actual read interrupted; no cached outcome was published",interrupted); }
    }
    /** Consumers obtain only a full validated same-frame observation; missing/stale remains unobserved. */
    public Optional<Captured> project(ArmyRetreatFrames.Current actual, ArmyWindowCodec.Kind kind) {
        var captured = observations.get(kind); if (captured == null) return Optional.empty();
        var before = captured.frame().actual(); var now = actual.actual();
        if (!before.identity().equals(now.identity()) || !before.source().equals(now.source()) || !before.sessionId().equals(now.sessionId()) || !before.connectionGeneration().equals(now.connectionGeneration()) || !before.fullBindingSha256().equals(now.fullBindingSha256())) return Optional.empty();
        return Optional.of(captured);
    }
    public List<PublicBindings.BoundBinding> install(PublicBindings bindings, ExactRef serviceSource) {
        return List.of(register(bindings,PublicMethod.QUERY_WAR_DECLARED_OVERVIEW_V1,this::query_war_declared_overview_v1,serviceSource),register(bindings,PublicMethod.QUERY_WAR_RESULTS_WINDOW_V1,this::query_war_results_window_v1,serviceSource));
    }
    private static PublicBindings.TypedBinding<ArmyCalls.Frame,Reply> register(PublicBindings bindings, PublicMethod method, PublicRoutes.Handler<ArmyCalls.Frame,Reply> handler, ExactRef source) {
        return bindings.register(method,ArmyCalls.Frame.class,Reply.class,handler,args -> {
            if (!(args instanceof PublicBindings.Value value)) throw new IllegalArgumentException("fixed-window public query requires named arguments"); return (ArmyCalls.Frame)ArmyCallCodec.decode(method,value.original());
        },ArmyWindowService::encode,new PublicRoutes.Target(ArmyWindowService.class.getName(),method.pythonName(),source),PublicRoutes.Status.IMPLEMENTED,"actual fixed-window producer and complete independent TOP owner decoder; source candidate requires Root verification");
    }
    public static RawJson encode(Reply reply) {
        if (reply instanceof ReadDeferred deferred)
            return ArmyPublicWire.encodeExactSourceBound(org.xar.ck3.control.application.driver.DriverJson.object(
                    deferred.original().normalized().bytes(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES),reply.context());
        KnownQuery known = (KnownQuery) reply;
        var payload = known.priorClose().map(prior -> ArmyJson.parse(prior.ownerQuery().orElseThrow().normalizedQuery().bytes()))
                .orElseGet(() -> known.original().value().normalized());
        // The same three source values are encoded by the sole public-wire metadata encoder.
        payload.remove(List.of("queried_snapshot_id","queried_revision","queried_native_revision"));
        return ArmyPublicWire.encode(org.xar.ck3.control.application.driver.DriverJson.object(ArmyJson.bytes(payload),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES),reply.context());
    }
}
