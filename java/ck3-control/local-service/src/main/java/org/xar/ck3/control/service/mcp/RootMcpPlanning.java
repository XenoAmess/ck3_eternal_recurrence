package org.xar.ck3.control.service.mcp;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.service.root.GiftDomainSource;
import org.xar.ck3.control.service.root.RootChangedSuccessionPreflight;
import org.xar.ck3.control.service.root.GiftPendingFrameReadyFailure;
import org.xar.ck3.control.application.effects.RootPlanningReadGuard.HeirPreconditionFailure;
import org.xar.ck3.control.application.effects.RootPlanningReadGuard.RootRevisionPreconditionFailure;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.OriginalTerminalPlanning;
import org.xar.ck3.control.application.planning.ReadonlyPlanningRetry;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.root.RootPublicHandlerProductsFactory;
import org.xar.ck3.control.service.root.RootPublicStepExecution;
import org.xar.ck3.control.service.root.RootRuntimePublicCatalog;
import org.xar.ck3.control.service.root.RootPlanningInputsFactory;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;

/** The two original planning facades over one current Core and its actual installed producers. */
public final class RootMcpPlanning {
    @FunctionalInterface public interface PlanPresentation {
        RawJson encode(PlanningRequest original, PlanningResult actual,
                org.xar.ck3.control.service.root.RootRuntimeDomainSettings.PlanFlags flags) throws IOException;
    }
    public record Admission(boolean originalPublicPlanInstalled, boolean originalPublicStepInstalled,
            List<RootRuntimePublicCatalog.DefinitionGap> gaps) {
        public Admission { gaps = List.copyOf(gaps); }
    }
    public interface Backend {
        Admission admission();
        RawJson plan(PublicPlanningCodec.PlanRequest original) throws IOException, InterruptedException;
        RawJson execute(PublicPlanningCodec.ExecuteRequest original) throws IOException, InterruptedException;
    }
    private record AfterPlanning(GiftDomainSource.PendingFrameWait token, PlanningResult actual) { }
    private sealed interface PlanPass permits Planned, ChangedPending { }
    private record Planned(RawJson bytes, Optional<AfterPlanning> afterPlanning) implements PlanPass { }
    private record ChangedPending(RootChangedSuccessionPreflight.Prepared prepared) implements PlanPass { }
    private final Backend backend;
    public RootMcpPlanning(Backend actual) { backend = Objects.requireNonNull(actual); }

    /** Pre-Core registration retains only source-bound ports; invocation resolves the committed current Root. */
    public static RootPublicHandlerProductsFactory.Contribution install(
            RootPublicHandlerProductsFactory.Context context, PublicBindings registry) throws IOException {
        Objects.requireNonNull(context); Objects.requireNonNull(registry);
        ExactRef source = context.source(RootMcpPlanning.class);
        context.source(PublicPlanningCodec.class);
        context.source(RootPublicPlanPresentation.class);
        context.source(OriginalPlanningFrameProjection.class);
        context.source(OriginalPlanDomainEnvelope.class);
        context.source(RootPublicStepExecution.class);
        context.sourceAt("wave2-planning/src/main/java/org/xar/ck3/control/wave2/planning/playerrisk/PlayerRiskCodec.java",
                org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskCodec.class);
        context.sourceAt("application/src/main/java/org/xar/ck3/control/application/planning/OriginalPlanRouting.java",
                org.xar.ck3.control.application.planning.OriginalPlanRouting.class);
        context.sourceAt("application/src/main/java/org/xar/ck3/control/application/planning/OrdinaryCorePolicy.java",
                org.xar.ck3.control.application.planning.OrdinaryCorePolicy.class);
        context.sourceAt("application/src/main/java/org/xar/ck3/control/application/planning/OriginalTerminalPlanning.java",
                OriginalTerminalPlanning.class);
        context.sourceAt("application/src/main/java/org/xar/ck3/control/application/planning/ReadonlyPlanningRetry.java",
                ReadonlyPlanningRetry.class);
        context.source(RootChangedSuccessionPreflight.class);
        for (var dependency : GiftDomainSource.pendingFrameSourceTypes())
            context.sourceAt(dependency.targetRelative(), dependency.actualClass());
        context.sourceAt("application/src/main/java/org/xar/ck3/control/application/effects/RootPlanningReadGuard.java",
                org.xar.ck3.control.application.effects.RootPlanningReadGuard.class);
        RootMcpPlanning actual = new RootMcpPlanning(new Backend() {
            @Override public Admission admission() { return new Admission(true, true, List.of()); }
            @Override public RawJson plan(PublicPlanningCodec.PlanRequest caller) throws IOException, InterruptedException {
                Objects.requireNonNull(caller);
                Instant deadline = context.clock().instant().plus(context.observationTimeout());
                return ReadonlyPlanningRetry.plan(() -> context.withCurrent(root -> {
                    var installed = context.installed(root);
                    Optional<RootChangedSuccessionPreflight.Prepared> refreshed = Optional.empty();
                    while (true) {
                    final Optional<RootChangedSuccessionPreflight.Prepared> applied = refreshed;
                    PlanPass pass = root.withPublicPlanning(deadline, (observed, same) -> {
                        if (applied.isPresent()) applied.orElseThrow().requireRefreshed(observed, same);
                        if (observed instanceof NativeReadinessCollector.PublicObserved
                                && OriginalTerminalPlanning.terminalFrame(observed.frame().snapshot().semantic())) {
                            var realm = installed.pipeline().realmMembershipPublication();
                            var scope = realm.beginPublicTerminalData(observed.frame(), same);
                            try {
                                if (applied.isEmpty()) {
                                    var changed = installed.remainingDomains().lifecycle()
                                            .changedPreflight(same, observed, deadline);
                                    if (changed.isPresent()) {
                                        // The original preflight READ runs after this actual raw freeze/realm scope exits.
                                        realm.cancelPublicTerminalData(scope);
                                        return new ChangedPending(changed.orElseThrow());
                                    }
                                }
                                var input = RootPlanningInputsFactory.publicTerminalInputs(observed, same, deadline);
                                var terminal = OriginalTerminalPlanning.plan(input).orElseThrow(
                                        () -> new IOException("actual terminal frame produced no original terminal DATA"));
                                var presented = RootPublicPlanPresentation.produceTerminal(input, terminal);
                                observed.assertCurrent(same);
                                if (context.installed(root) != installed)
                                    throw new IOException("public terminal PLAN lost its identical installed current catalog");
                                realm.finalizePublicTerminalData(scope,
                                        org.xar.ck3.control.planning.opportunity.OpportunityJson.object(
                                                presented.original().get("plan"), "actual final terminal plan"));
                                observed.assertCurrent(same);
                                return new Planned(presented.bytes(), Optional.empty());
                            } catch (IOException | RuntimeException | Error failure) {
                                try { realm.cancelPublicTerminalData(scope); }
                                catch (RuntimeException | Error cleanup) { failure.addSuppressed(cleanup); }
                                throw failure;
                            }
                        }
                        // The actual collector union is DATA; only its real input producer may form a request.
                        PlanningRequest original = RootPlanningInputsFactory.publicRequest(observed, same, deadline);
                        observed.assertCurrent(same);
                        var pendingFrame = context.definitions().finance().preparePendingFrame(
                                installed.context(), same, original, observed);
                        // Controller owns this exact complete ordinary planner, including realm lifecycle.
                        PlanningResult result = root.planPublic(original);
                        observed.assertCurrent(same);
                        if (context.installed(root) != installed)
                            throw new IOException("public PLAN lost its identical installed current catalog");
                        RawJson bytes = RootPublicPlanPresentation.produce(original, result, context.planningFlags(original)).bytes();
                        return new Planned(bytes, pendingFrame.map(token -> new AfterPlanning(token, result)));
                    });
                    if (pass instanceof ChangedPending changed) {
                        if (refreshed.isPresent()) throw new IOException("changed succession preflight attempted a second normal refresh");
                        changed.prepared().perform(deadline);
                        refreshed = Optional.of(changed.prepared());
                        continue;
                    }
                    Planned planned = (Planned) pass;
                    if (planned.afterPlanning().isPresent()) {
                        AfterPlanning post = planned.afterPlanning().orElseThrow();
                        post.token().afterPlanning(post.actual());
                    }
                    return planned.bytes();
                    }
                }));
            }
            @Override public RawJson execute(PublicPlanningCodec.ExecuteRequest caller) throws IOException, InterruptedException {
                Objects.requireNonNull(caller);
                Instant deadline = context.clock().instant().plus(context.actionTimeout());
                if (caller.step().value().equals("restore-checkpoint"))
                    return RootPublicStepExecution.executeRetainedRestore(context, caller, deadline);
                return context.withCurrent(root -> RootPublicStepExecution.execute(
                        root, context.installed(root), caller, deadline));
            }
        });
        actual.register(registry, source);
        return new RootPublicHandlerProductsFactory.Contribution(List.of(), List.of(), actual.admission().gaps());
    }

    public Admission admission() { return backend.admission(); }
    public RawJson plan(PublicPlanningCodec.PlanRequest caller) throws InterruptedException {
        try { return Objects.requireNonNull(backend.plan(Objects.requireNonNull(caller))); }
        catch (RootRevisionPreconditionFailure failure) {
            throw new PublicServiceFailure(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,
                    failure.getMessage(), Optional.empty());
        }
        catch (HeirPreconditionFailure failure) {
            throw new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                    failure.getMessage(), Optional.empty());
        }
        catch (GiftPendingFrameReadyFailure failure) {
            throw new PublicServiceFailure(PublicServiceFailure.Kind.FACTION_GIFT_PENDING_FRAME_READY,
                    failure.getMessage(), Optional.empty());
        }
        catch (ReadonlyPlanningRetry.Exhausted failure) {
            throw new PublicServiceFailure(PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED,
                    failure.getMessage(), java.util.Optional.of(failure.original()));
        }
        catch (IOException failure) { throw new UncheckedIOException("actual public PLAN unavailable", failure); }
    }
    public RawJson execute(PublicPlanningCodec.ExecuteRequest caller) throws InterruptedException {
        try { return Objects.requireNonNull(backend.execute(Objects.requireNonNull(caller))); }
        catch (IOException failure) { throw new UncheckedIOException("actual public EXECUTE unavailable; an entered UNKNOWN is never resent", failure); }
    }
    public List<PublicBindings.BoundBinding> register(PublicBindings registry, ExactRef source) {
        Objects.requireNonNull(registry); Objects.requireNonNull(source);
        org.xar.ck3.control.contracts.StrictJson.require(source.bytes() > 0, "actual public implementation source required");
        Admission installed = admission();
        var result = new java.util.ArrayList<PublicBindings.BoundBinding>();
        if (installed.originalPublicPlanInstalled())
            result.add(registry.register(PublicMethod.PLAN_TURN, PublicPlanningCodec.PlanRequest.class, RawJson.class,
                    this::plan, PublicPlanningCodec::decodePlan, value -> value,
                    new PublicRoutes.Target(RootMcpPlanning.class.getName(), "plan", source), PublicRoutes.Status.IMPLEMENTED,
                    "same Core complete ordinary planner, detached complete original public plan"));
        if (installed.originalPublicStepInstalled())
            result.add(registry.register(PublicMethod.EXECUTE_STEP, PublicPlanningCodec.ExecuteRequest.class, RawJson.class,
                    this::execute, PublicPlanningCodec::decodeExecute, value -> value,
                    new PublicRoutes.Target(RootMcpPlanning.class.getName(), "execute", source), PublicRoutes.Status.IMPLEMENTED,
                    "actual source-owned arbitrary step preparation/read; original public result, separate H2743 READ"));
        return List.copyOf(result);
    }
}
