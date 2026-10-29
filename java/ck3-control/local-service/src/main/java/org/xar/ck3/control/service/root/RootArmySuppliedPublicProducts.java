package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverReadHistoryPublisher;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.service.root.RootPublicHandlerProductsFactory.Context;
import org.xar.ck3.control.service.root.RootPublicHandlerProductsFactory.Contribution;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;

/** Supplied Army service bindings retain no pre-Core or previous-Game runtime. */
public final class RootArmySuppliedPublicProducts {
    private RootArmySuppliedPublicProducts() { }

    static final Set<PublicMethod> RESERVED = Set.of(
            PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1, PublicMethod.QUERY_PLAYER_TRUCE_EXPIRY_V1,
            PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1,
            PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1, PublicMethod.QUERY_BATTLE_TRANSITION_V1,
            PublicMethod.QUERY_BATTLE_TERMINAL_TRANSITION_V1, PublicMethod.PREVIEW_ACTIVE_COMBAT_RETREAT_V1,
            PublicMethod.ORDER_ACTIVE_COMBAT_RETREAT_V1, PublicMethod.QUERY_WAR_DECLARED_OVERVIEW_V1,
            PublicMethod.QUERY_WAR_RESULTS_WINDOW_V1, PublicMethod.QUERY_PLAYER_MERCENARY_CONTEXT_V1,
            PublicMethod.QUERY_ARMY_COMMANDER_CANDIDATES_V1, PublicMethod.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1);
    static final Set<PublicMethod> METHODS = methods();

    record Sources(ExactRef adapter, ExactRef decoder, ExactRef war, ExactRef forecast,
            ExactRef strengths, ExactRef ordinary, ExactRef collection, ExactRef collectionCodec,
            ExactRef heldCollector, ExactRef rootSession, ExactRef warPublicCodec, ExactRef publicWire,
            ExactRef forecastPublicCodec, ExactRef scalarControl, ExactRef strengthsDriverResult,
            ExactRef strengthsPublisher, ExactRef warOriginalCodec, List<ExactRef> combatProjection) {
        Sources {
            combatProjection = List.copyOf(combatProjection);
            StrictJson.require(combatProjection.size() == 6, "all six actual combat projection sources required");
            for (ExactRef source : combatProjection)
                StrictJson.require(source.bytes() > 0, "actual combat projection source required");
            for (var source : List.of(adapter, decoder, war, forecast, strengths, ordinary,
                    collection, collectionCodec, heldCollector, rootSession, warPublicCodec, publicWire, forecastPublicCodec,
                    scalarControl, strengthsDriverResult, strengthsPublisher, warOriginalCodec))
                StrictJson.require(source.bytes() > 0, "actual supplied Army source required");
        }
    }
    /** Only the shared owner factories can produce these concrete services for a physical Root. */
    private record ReadCall(ContinuityStorePort.Session same, Instant deadline) { }
    @FunctionalInterface private interface ReadScopeSource { ReadCall current() throws IOException; }
    record Services(ArmyWarReadService war, ArmyForecastService forecast,
            ArmyStrengthsService strengths, ArmyOrdinaryActionService ordinary, ReadScopeSource readScope) {
        Services {
            Objects.requireNonNull(war); Objects.requireNonNull(forecast);
            Objects.requireNonNull(strengths); Objects.requireNonNull(ordinary); Objects.requireNonNull(readScope);
        }
        ArmyWarReadService.WarStateReply warState(ArmyCalls.Empty input) throws IOException {
            var scope = readScope.current(); return war.war_state(scope.same(), input, scope.deadline());
        }
        ArmyWarReadService.Reply readWar(ArmyCalls.Call input) throws IOException {
            var scope = readScope.current(); return war.read(scope.same(), input, scope.deadline());
        }
        ArmyDeclarationCollection.Reply collect(ArmyCalls.Collect input) throws IOException {
            var scope = readScope.current();
            return war.collect_declarable_wars_result_v1(scope.same(), input, scope.deadline());
        }
        ArmyForecastService.Reply readForecast(ArmyCalls.Call input) throws IOException, InterruptedException {
            var scope = readScope.current(); return forecast.read(scope.same(), input, scope.deadline());
        }
    }
    @FunctionalInterface interface Invocation<Q extends ArmyCalls.Call,R> {
        R call(Services actual, Q input) throws IOException, InterruptedException;
    }
    /** Package-private composition seam; it neither creates a Root nor grants Native admission. */
    interface Current {
        <Q extends ArmyCalls.Call,R> R invoke(PublicMethod method, Q input, Class<R> result,
                Invocation<Q,R> original) throws InterruptedException;
    }
    @FunctionalInterface interface SourceLookup {
        ExactRef source(Module module, Class<?> actual) throws IOException;
    }

    public static Contribution install(Context context, PublicBindings registry) {
        Objects.requireNonNull(context); Objects.requireNonNull(registry);
        return install(registry, context::source, new ActualCurrent(context));
    }
    static Contribution install(PublicBindings registry, SourceLookup selected, Current current) {
        Objects.requireNonNull(registry); Objects.requireNonNull(selected); Objects.requireNonNull(current);
        Sources sources;
        try {
            var combatSources = new ArrayList<ExactRef>();
            for (Class<?> implementation : combatImplementations())
                combatSources.add(selected.source(Module.NATIVE_TRANSPORT, implementation));
            sources = new Sources(selected.source(Module.LOCAL_SERVICE, RootArmySuppliedPublicProducts.class),
                    selected.source(Module.APPLICATION, ArmyCallCodec.class),
                    selected.source(Module.NATIVE_TRANSPORT, ArmyWarReadService.class),
                    selected.source(Module.NATIVE_TRANSPORT, ArmyForecastService.class),
                    selected.source(Module.NATIVE_TRANSPORT, ArmyStrengthsService.class),
                    selected.source(Module.NATIVE_TRANSPORT, ArmyOrdinaryActionService.class),
                    selected.source(Module.NATIVE_TRANSPORT, ArmyDeclarationCollection.class),
                    selected.source(Module.NATIVE_TRANSPORT, ArmyDeclarationCollectionCodec.class),
                    selected.source(Module.NATIVE_TRANSPORT, NativeReadinessCollector.class),
                    selected.source(Module.LOCAL_SERVICE, RootApplicationSession.class),
                    selected.source(Module.APPLICATION, ArmyWarPublicResultCodec.class),
                    selected.source(Module.APPLICATION, ArmyPublicWire.class),
                    selected.source(Module.NATIVE_TRANSPORT, ArmyForecastPublicResultCodec.class),
                    selected.source(Module.NATIVE_TRANSPORT, ArmyPrivateScalarControl.class),
                    selected.source(Module.NATIVE_TRANSPORT, ArmyStrengthsDriverResult.class),
                    selected.source(Module.APPLICATION, DriverReadHistoryPublisher.class),
                    selected.source(Module.APPLICATION, ArmyWarOriginalResultCodec.class), combatSources);
        } catch (IOException missing) {
            var gaps = new ArrayList<RootRuntimePublicCatalog.DefinitionGap>();
            for (var method : METHODS) gaps.add(new RootRuntimePublicCatalog.DefinitionGap(method.pythonName(),
                    "actual supplied Army product source closure unavailable: " + missing.getMessage()));
            return new Contribution(List.of(), List.of(), gaps);
        }
        register(registry, sources, current);
        return new Contribution(List.of(), List.of(), List.of());
    }

    /** Definitions only: obtaining the actual Core and physical products is deferred until invocation. */
    static void register(PublicBindings registry, Sources sources, Current current) {
        Objects.requireNonNull(registry); Objects.requireNonNull(sources); Objects.requireNonNull(current);
        var collision = registry.coverage().installed().stream().filter(METHODS::contains).findFirst();
        StrictJson.require(collision.isEmpty(), "supplied Army service already has another actual producer");
        bind(registry, sources, current, PublicMethod.WAR_STATE, ArmyCalls.Empty.class,
                ArmyWarReadService.WarStateReply.class, (s,q) -> s.warState(q), ArmyWarReadService::encodeWarState);
        war(registry, sources, current, PublicMethod.QUERY_DECLARABLE_WARS, ArmyCalls.Frame.class,
                (s,q) -> s.readWar(q));
        bind(registry, sources, current, PublicMethod.COLLECT_DECLARABLE_WARS_RESULT_V1, ArmyCalls.Collect.class,
                ArmyDeclarationCollection.Reply.class, (s,q) -> s.collect(q),
                ArmyWarReadService::encodeCollection);
        war(registry, sources, current, PublicMethod.QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1,
                ArmyCalls.Declaration.class, (s,q) -> s.readWar(q));
        war(registry, sources, current, PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1, ArmyCalls.War.class,
                (s,q) -> s.readWar(q));
        war(registry, sources, current, PublicMethod.QUERY_WAR_TERMINATION_OPTIONS, ArmyCalls.War.class,
                (s,q) -> s.readWar(q));
        war(registry, sources, current, PublicMethod.QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS, ArmyCalls.War.class,
                (s,q) -> s.readWar(q));
        war(registry, sources, current, PublicMethod.QUERY_WAR_TERMINATION_TERMS, ArmyCalls.War.class,
                (s,q) -> s.readWar(q));
        // The original service deliberately rejects this preview. It has no original MCP route.
        war(registry, sources, current, PublicMethod.QUERY_WAR_TERMINATION_EXIT_TERMS, ArmyCalls.War.class,
                (s,q) -> s.war().query_war_termination_exit_terms(q));
        war(registry, sources, current, PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1, ArmyCalls.Declaration.class,
                (s,q) -> s.readWar(q));
        war(registry, sources, current, PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2, ArmyCalls.Declaration.class,
                (s,q) -> s.readWar(q));
        forecast(registry, sources, current, PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS, ArmyCalls.Combat.class,
                (s,q) -> s.readForecast(q));
        forecast(registry, sources, current, PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS_V3, ArmyCalls.Combat.class,
                (s,q) -> s.readForecast(q));
        forecast(registry, sources, current, PublicMethod.QUERY_WAR_ENTRY_ASSESSMENTS, ArmyCalls.WarEntry.class,
                (s,q) -> s.readForecast(q));
        forecast(registry, sources, current, PublicMethod.QUERY_CURRENT_BATTLE_KNIGHT_V1, ArmyCalls.Knight.class,
                (s,q) -> s.readForecast(q));
        forecast(registry, sources, current, PublicMethod.QUERY_COMBAT_PHASE_EVENT_TRACE_V1, ArmyCalls.CombatId.class,
                (s,q) -> s.readForecast(q));
        bind(registry, sources, current, PublicMethod.QUERY_ARMY_STRENGTHS, ArmyCalls.Strengths.class,
                ArmyStrengthsService.Reply.class, (s,q) -> s.strengths().query_army_strengths(q), ArmyStrengthsService::encodePublicV2);
        ordinary(registry, sources, current, PublicMethod.SUBMIT_CALL_ALLY_TO_WAR_PRIVATE_V1, ArmyCalls.CallAlly.class,
                (s,q) -> s.ordinary().submit_call_ally_to_war_private_v1(q));
        ordinary(registry, sources, current, PublicMethod.SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1, ArmyCalls.CreateMaa.class,
                (s,q) -> s.ordinary().submit_regular_maa_create_private_v1(q));
        ordinary(registry, sources, current, PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1, ArmyCalls.Frame.class,
                (s,q) -> s.ordinary().close_war_declared_overview_v1(q));
        ordinary(registry, sources, current, PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1, ArmyCalls.Frame.class,
                (s,q) -> s.ordinary().close_war_results_window_v1(q));
        ordinary(registry, sources, current, PublicMethod.DECLARE_WAR, ArmyCalls.Declaration.class,
                (s,q) -> s.ordinary().declare_war(q));
        ordinary(registry, sources, current, PublicMethod.RAISE_TROOPS_DEFAULT, ArmyCalls.Frame.class,
                (s,q) -> s.ordinary().raise_troops_default(q));
        ordinary(registry, sources, current, PublicMethod.MOVE_ARMY, ArmyCalls.Move.class,
                (s,q) -> s.ordinary().move_army(q));
        ordinary(registry, sources, current, PublicMethod.START_ASSAULT, ArmyCalls.Siege.class,
                (s,q) -> s.ordinary().start_assault(q));
        ordinary(registry, sources, current, PublicMethod.STOP_ASSAULT, ArmyCalls.Siege.class,
                (s,q) -> s.ordinary().stop_assault(q));
        ordinary(registry, sources, current, PublicMethod.DISBAND_ARMY, ArmyCalls.Unit.class,
                (s,q) -> s.ordinary().disband_army(q));
        ordinary(registry, sources, current, PublicMethod.ENFORCE_DEMANDS, ArmyCalls.War.class,
                (s,q) -> s.ordinary().enforce_demands(q));
        ordinary(registry, sources, current, PublicMethod.SURRENDER_WAR, ArmyCalls.War.class,
                (s,q) -> s.ordinary().surrender_war(q));
        ordinary(registry, sources, current, PublicMethod.OFFER_WHITE_PEACE, ArmyCalls.War.class,
                (s,q) -> s.ordinary().offer_white_peace(q));
        ordinary(registry, sources, current, PublicMethod.HIRE_MERCENARY_V1, ArmyCalls.Hire.class,
                (s,q) -> s.ordinary().hire_mercenary_v1(q));
        ordinary(registry, sources, current, PublicMethod.HIRE_HOLY_ORDER_V1, ArmyCalls.Hire.class,
                (s,q) -> s.ordinary().hire_holy_order_v1(q));
        ordinary(registry, sources, current, PublicMethod.ASSIGN_ARMY_COMMANDER_V1, ArmyCalls.AssignCommander.class,
                (s,q) -> s.ordinary().assign_army_commander_v1(q));
        ordinary(registry, sources, current, PublicMethod.SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1, ArmyCalls.Sampling.class,
                (s,q) -> s.ordinary().set_army_gathering_research_sampling_v1(q));
    }
    private static <Q extends ArmyCalls.Call> void war(PublicBindings registry, Sources sources, Current current,
            PublicMethod method, Class<Q> type, Invocation<Q,ArmyWarReadService.Reply> call) {
        bind(registry, sources, current, method, type, ArmyWarReadService.Reply.class, call, ArmyWarReadService::encode);
    }
    private static <Q extends ArmyCalls.Call> void forecast(PublicBindings registry, Sources sources, Current current,
            PublicMethod method, Class<Q> type, Invocation<Q,ArmyForecastService.Reply> call) {
        bind(registry, sources, current, method, type, ArmyForecastService.Reply.class, call,
                reply -> ArmyForecastService.encode(method, reply));
    }
    private static <Q extends ArmyCalls.Call> void ordinary(PublicBindings registry, Sources sources, Current current,
            PublicMethod method, Class<Q> type, Invocation<Q,ArmyOrdinaryActionService.Reply> call) {
        bind(registry, sources, current, method, type, ArmyOrdinaryActionService.Reply.class, call, ArmyOrdinaryActionService::encode);
    }
    private static <Q extends ArmyCalls.Call,R> void bind(PublicBindings registry, Sources sources, Current current,
            PublicMethod method, Class<Q> type, Class<R> result, Invocation<Q,R> call, PublicBindings.Encoder<R> encode) {
        Class<?> owner; ExactRef source;
        if (result == ArmyWarReadService.Reply.class || result == ArmyWarReadService.WarStateReply.class
                || result == ArmyDeclarationCollection.Reply.class) {
            owner = ArmyWarReadService.class; source = sources.war();
        } else if (result == ArmyForecastService.Reply.class) { owner = ArmyForecastService.class; source = sources.forecast(); }
        else if (result == ArmyStrengthsService.Reply.class) { owner = ArmyStrengthsService.class; source = sources.strengths(); }
        else if (result == ArmyOrdinaryActionService.Reply.class) { owner = ArmyOrdinaryActionService.class; source = sources.ordinary(); }
        else throw new IllegalArgumentException("closed supplied Army reply family required");
        String actualMethod = (result == ArmyForecastService.Reply.class
                || result == ArmyWarReadService.Reply.class && method != PublicMethod.QUERY_WAR_TERMINATION_EXIT_TERMS)
                ? "read" : method.pythonName();
        registry.register(method, type, result, input -> {
            StrictJson.require(input.method() == method, "supplied Army typed invocation changed its selected method");
            return current.invoke(method, input, result, call);
        }, arguments -> decode(method, type, arguments), encode,
                new PublicRoutes.Target(owner.getName(), actualMethod, source), PublicRoutes.Status.IMPLEMENTED,
                "actual current Root lookup; sole Army codec/service, installed families, original writer receipt and native permissions; original encoder profile retained, registration grants no original Python ABI or Game qualification");
    }
    static <Q extends ArmyCalls.Call> Q decode(PublicMethod method, Class<Q> type, PublicBindings.Arguments arguments) {
        if (!(arguments instanceof PublicBindings.Value value))
            throw new IllegalArgumentException("Army supplied method requires its exact named argument object");
        return type.cast(ArmyCallCodec.decode(method, value.original()));
    }
    /** Closed implementation list, including the two package-private producer helpers, without class initialization. */
    static List<Class<?>> combatImplementations() throws IOException {
        try {
            ClassLoader loader = CombatPublicProjection.class.getClassLoader();
            return List.of(CombatPublicProjection.class, CombatLoadedPlaysetProof.class,
                    CombatKnightKernel.class, CombatKnightConsumption.class,
                    Class.forName("org.xar.ck3.control.nativebridge.capabilities.army.CombatKnightOwnedPreparation", false, loader),
                    Class.forName("org.xar.ck3.control.nativebridge.capabilities.army.CombatProjectionJson", false, loader));
        } catch (ClassNotFoundException missing) {
            throw new IOException("actual complete combat projection implementation is not loaded", missing);
        }
    }
    private static final class ActualCurrent implements Current {
        private final Context context;
        private final IdentityHashMap<RootInstalledCatalog,Services> products = new IdentityHashMap<>();
        private final ThreadLocal<ActiveCall> active = new ThreadLocal<>();
        private final ThreadLocal<ReadCall> readCall = new ThreadLocal<>();
        private record ActiveCall(RootApplicationSession root, RootInstalledCatalog catalog) { }
        @FunctionalInterface private interface ReadWork<T> { T run() throws IOException, InterruptedException; }
        private static final class InterruptedQuery extends IOException {
            private final InterruptedException original;
            InterruptedQuery(InterruptedException original) { super(original); this.original = original; }
        }
        /** A negative result for the actual playset probe; this class grants no frame or read authority. */
        private static final class PlaysetSnapshotChanged extends RuntimeException { }
        ActualCurrent(Context context) { this.context = Objects.requireNonNull(context); }
        @Override public <Q extends ArmyCalls.Call,R> R invoke(PublicMethod method, Q input, Class<R> result,
                Invocation<Q,R> original) throws InterruptedException {
            try { return context.withCurrent(root -> {
                var same = context.installed(root);
                StrictJson.require(active.get() == null, "supplied Army cannot replace an active current-Root call");
                active.set(new ActiveCall(root, same));
                try {
                    var services = current(same);
                    var deadline = context.clock().instant().plus(
                            result == ArmyOrdinaryActionService.Reply.class ? context.actionTimeout() : context.observationTimeout());
                    if (result == ArmyOrdinaryActionService.Reply.class)
                        return root.withPublicSuppliedAction(deadline, () -> result.cast(original.call(services, input)));
                    if (method == PublicMethod.COLLECT_DECLARABLE_WARS_RESULT_V1)
                        return root.withPublicStandalonePublication(deadline, borrowed -> {
                            same.context().writer().requireSession(borrowed);
                            return inReadScope(borrowed, deadline, () -> result.cast(original.call(services, input)));
                        });
                    if (method == PublicMethod.QUERY_WAR_TERMINATION_EXIT_TERMS)
                        return result.cast(original.call(services, input)); // Original disabled error; no Native sampling.
                    try {
                        return root.withPublicObservation(deadline, (frame, known, borrowed) -> {
                            same.context().writer().requireSession(borrowed);
                            StrictJson.require(frame.source().equals(same.context().source())
                                    && frame.sessionId().equals(root.identity().sessionId())
                                    && frame.identity().game().equals(root.identity().game()),
                                    "public Army query crossed the actual current Root scope");
                            try { return inReadScope(borrowed, deadline, () -> result.cast(original.call(services, input))); }
                            catch (InterruptedException interrupted) {
                                Thread.currentThread().interrupt(); throw new InterruptedQuery(interrupted);
                            }
                        });
                    } catch (InterruptedQuery interrupted) { throw interrupted.original; }
                } finally { active.remove(); }
            }); }
            catch (IOException unavailable) { throw new UncheckedIOException("actual current supplied Army product unavailable", unavailable); }
        }
        private <T> T inReadScope(ContinuityStorePort.Session same, Instant deadline, ReadWork<T> work)
                throws IOException, InterruptedException {
            StrictJson.require(readCall.get() == null, "supplied Army read cannot replace its original borrowed writer scope");
            readCall.set(new ReadCall(same, deadline));
            try { return work.run(); } finally { readCall.remove(); }
        }
        private ReadCall currentReadScope() throws IOException {
            ActiveCall call = active.get(); ReadCall read = readCall.get();
            StrictJson.require(call != null && read != null && context.installed(call.root()) == call.catalog(),
                    "supplied Army read escaped its actual Root callback");
            call.catalog().context().writer().requireSession(read.same()); return read;
        }
        private Complete currentPlaysetFrame(RootInstalledCatalog expected) throws IOException {
            ActiveCall call = active.get(); ReadCall scope = currentReadScope();
            StrictJson.require(call != null && call.catalog() == expected,
                    "loaded playset probe crossed its actual current Root/catalog");
            var runtime = expected.context();
            return runtime.collector().withHeldReadScope(scope.same(), call.root().identity(), scope.deadline(), actual -> {
                runtime.collector().requireHeldFrame(scope.same(), actual);
                // This is an extra DATA stability check for this file probe, without observation or Native submission.
                var received = runtime.transport().currentSnapshot(scope.deadline());
                byte[] packet = received.originalPacket();
                if (!received.session().machineId().equals(actual.identity().machineId())
                        || !received.session().game().equals(actual.identity().game())
                        || !received.session().sessionId().equals(actual.sessionId())
                        || !received.session().connectionGeneration().equals(actual.connectionGeneration())
                        || !received.snapshotId().equals(actual.identity().frame().snapshotId())
                        || !received.nativeRevision().equals(actual.identity().frame().identity().nativeRevision())
                        || !received.observedAt().equals(actual.observedAt())
                        || packet.length != actual.originalEvidence().bytes()
                        || !DriverJson.sha256(packet).equals(actual.originalEvidence().sha256())
                        || !OpportunityJson.bool(actual.semantic().get("paused"), "paused"))
                    throw new PlaysetSnapshotChanged();
                runtime.collector().requireHeldFrame(scope.same(), actual);
                return actual;
            });
        }
        private CombatPublicProjection.LoadedPlaysetSource loadedPlayset(RootInstalledCatalog same) {
            var actual = CombatLoadedPlaysetProof.managed(same.context().game().launchPlan().stateDirectory(),
                    () -> currentPlaysetFrame(same));
            return input -> {
                try { return actual.observe(input); }
                catch (PlaysetSnapshotChanged changed) {
                    return CombatLoadedPlaysetProof.unavailable(input.after(), "snapshot_changed_during_loaded_playset_proof");
                }
            };
        }
        private synchronized Services current(RootInstalledCatalog same) throws IOException {
            Services previous = products.get(same);
            if (previous != null) return previous;
            StrictJson.require(products.size() < 64, "bounded actual physical Army service product history required");
            var runtime = same.context(); var army = same.army().products(); var military = same.military();
            for (Class<?> implementation : List.of(RootArmySuppliedPublicProducts.class, RootApplicationSession.class, ArmyCallCodec.class,
                    NativeReadinessCollector.class, ArmyDeclarationCollection.class, ArmyDeclarationCollectionCodec.class,
                    ArmyWarPublicResultCodec.class, ArmyWarOriginalResultCodec.class, ArmyPublicWire.class, ArmyForecastPublicResultCodec.class, ArmyWarReadService.class,
                    ArmyForecastService.class, ArmyStrengthsService.class, ArmyOrdinaryActionService.class,
                    ArmyPrivateScalarControl.class, ArmyStrengthsDriverResult.class, DriverReadHistoryPublisher.class))
                runtime.game().launchPlan().sources().requireLoadedClass(implementation);
            for (Class<?> implementation : combatImplementations())
                runtime.game().launchPlan().sources().requireLoadedClass(implementation);
            var strength = same.remainingDomains().strengths();
            var ordinary = same.remainingDomains().armyOrdinary().service();
            StrictJson.require(ordinary.supported().equals(EnumSet.allOf(ArmyOrdinaryActionArguments.Kind.class)),
                    "the same actual complete seventeen-action Army service is required");
            var war = new ArmyWarReadService(runtime.writer(), military.warReads(), runtime.readCatalog(),
                    army.frames(), context.clock(), context.observationTimeout(), new ArmyWarReadService.CollectionCurrent() {
                        @Override public <T> T withCurrent(ContinuityStorePort.Session borrowed, Instant deadline,
                                ArmyWarReadService.CollectionWork<T> work) throws IOException {
                            ActiveCall call = active.get();
                            StrictJson.require(call != null && call.catalog() == same
                                    && context.installed(call.root()) == same,
                                    "declaration collection escaped its actual current Root/catalog call");
                            runtime.writer().requireSession(borrowed);
                            StrictJson.require(currentReadScope().same() == borrowed,
                                    "declaration collection changed the actual Root borrowed writer");
                            return runtime.collector().withHeldReadScope(borrowed, call.root().identity(), deadline, work::apply);
                        }
                    });
            var forecast = new ArmyForecastService(runtime.writer(), army.frames(), military.forecasts(),
                    runtime::readCatalog, () -> context.clock().instant().plus(context.observationTimeout()), loadedPlayset(same));
            var strengths = new ArmyStrengthsService(strength.current(), runtime.reads(), runtime.readCatalog(),
                    strength.contracts(), strength.cache(), strength.pipeline(), strength.scalarControl(), runtime.readHistoryPublisher());
            Services actual = new Services(war, forecast, strengths, ordinary, this::currentReadScope);
            products.put(same, actual); return actual;
        }
    }
    private static Set<PublicMethod> methods() {
        var methods = EnumSet.of(PublicMethod.WAR_STATE, PublicMethod.QUERY_DECLARABLE_WARS,
                PublicMethod.COLLECT_DECLARABLE_WARS_RESULT_V1, PublicMethod.QUERY_WAR_TERMINATION_EXIT_TERMS,
                PublicMethod.QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1,
                PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1, PublicMethod.QUERY_WAR_TERMINATION_OPTIONS,
                PublicMethod.QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS, PublicMethod.QUERY_WAR_TERMINATION_TERMS,
                PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1, PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2,
                PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS, PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS_V3,
                PublicMethod.QUERY_WAR_ENTRY_ASSESSMENTS, PublicMethod.QUERY_CURRENT_BATTLE_KNIGHT_V1,
                PublicMethod.QUERY_COMBAT_PHASE_EVENT_TRACE_V1, PublicMethod.QUERY_ARMY_STRENGTHS);
        for (var kind : ArmyOrdinaryActionArguments.Kind.values()) methods.add(PublicMethod.valueOf(kind.name()));
        StrictJson.require(java.util.Collections.disjoint(methods, RESERVED), "supplied Army methods overlap the current Root thirteen");
        return Set.copyOf(methods);
    }
}
