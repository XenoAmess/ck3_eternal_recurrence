package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.Kind;

/** Concrete sequential quotes -> same-writer preparation -> single coordinator -> independent effect/replay graph.
 * All existing producer instances and both delegated domains are mandatory. This installs no second read registry.
 */
public final class ArmyOrdinaryRuntimeBindings {
    private ArmyOrdinaryRuntimeBindings() { }
    private static final Set<Kind> WAR_WINDOW = Set.of(Kind.DECLARE_WAR, Kind.SUBMIT_CALL_ALLY_TO_WAR_PRIVATE_V1,
            Kind.HIRE_HOLY_ORDER_V1, Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1, Kind.CLOSE_WAR_RESULTS_WINDOW_V1);
    private static final Set<Kind> DELEGATED = Set.of(Kind.HIRE_MERCENARY_V1, Kind.ASSIGN_ARMY_COMMANDER_V1);
    public record Inputs(ArmyOrdinaryPairedQuotes.Producers producers, ArmyOrdinaryActionService.Sources sources,
            ExactRef warWindowObserverSource, ExactRef holyOrderDecoderSource, HolyHirePoststate.Sources holyPoststateSources, ArmyOrdinaryActionService.ActionIds actionIds,
            ArmyOrdinaryActionPreparation.OccupationProjection occupation,
            ArmyOrdinaryActionPreparation.FinalGates remainingFinalGates,
            List<ArmyOrdinaryActionService.Effect> remainingEffects,
            ArmyOrdinaryActionService.Commander commander, ArmyOrdinaryActionService.Mercenary mercenary,
            Duration commandTimeout) {
        public Inputs {
            Objects.requireNonNull(producers); Objects.requireNonNull(sources); Objects.requireNonNull(actionIds); Objects.requireNonNull(holyPoststateSources);
            StrictJson.require(warWindowObserverSource != null && warWindowObserverSource.bytes() > 0,
                    "actual war/window effect source required");
            StrictJson.require(holyOrderDecoderSource != null && holyOrderDecoderSource.bytes() > 0,
                    "actual holy-order Java decoder source required");
            Objects.requireNonNull(occupation); Objects.requireNonNull(remainingFinalGates);
            remainingEffects = List.copyOf(remainingEffects); Objects.requireNonNull(commander); Objects.requireNonNull(mercenary);
            requireRemainingEffects(remainingEffects);
            StrictJson.require(commandTimeout != null && !commandTimeout.isNegative() && !commandTimeout.isZero()
                    && commandTimeout.compareTo(Duration.ofMinutes(1)) <= 0, "bounded Army command timeout required");
        }
    }
    /** Full required effect inventory; a missing leaf cannot turn an incomplete installation into Ready. */
    public static void requireRemainingEffects(List<ArmyOrdinaryActionService.Effect> actual) {
        var expected = EnumSet.allOf(Kind.class); expected.removeAll(WAR_WINDOW); expected.removeAll(DELEGATED);
        var observed = EnumSet.noneOf(Kind.class);
        for (var effect : List.copyOf(actual)) StrictJson.require(observed.add(effect.kind()), "duplicate Army effect kind");
        StrictJson.require(observed.equals(expected), "full original remaining Army effect inventory required; missing or foreign leaf");
    }
    public static Installed install(RootRuntimeContext context, Inputs inputs) throws IOException {
        return new Installed(Objects.requireNonNull(context), Objects.requireNonNull(inputs));
    }
    public static final class Installed {
        private final RootRuntimeContext context;
        private final Inputs inputs;
        private final ArmyOrdinaryPairedQuotes quotes;
        private final ArmyWarWindowRuntimeRoutes routes;
        private final NativeArmyWarWindowEffects warWindow;
        private final NativeOrdinaryWarAdmission warAdmission;
        private final ArmyOrdinaryActionPreparation preparation;
        private final ArmyOrdinaryActionService service;
        private final RootDomainInstallation installation;
        private Installed(RootRuntimeContext context, Inputs inputs) throws IOException {
            this.context = context; this.inputs = inputs;
            for (Class<?> actual : List.of(ArmyOrdinaryRuntimeBindings.class, ArmyWarWindowRuntimeRoutes.class,
                    ArmyOrdinaryPairedQuotes.class, ArmyOrdinaryActionPreparation.class, ArmyOrdinaryActionService.class,
                    ArmyOrdinaryActionArguments.class, org.xar.ck3.control.application.planning.military.OrdinaryAutomaticSurrenderPolicy.class,
                    NativeArmyWarWindowEffects.class, ArmyWarWindowReads.class, ArmyWindowCodec.class, NativeOrdinaryWarAdmission.class,
                    NativeDirectFixedWindowObservation.class, NativeEffectSnapshots.class,
                    org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContextRead.class))
                context.game().launchPlan().sources().requireLoadedClass(actual);
            quotes = new ArmyOrdinaryPairedQuotes(context, inputs.producers());
            routes = new ArmyWarWindowRuntimeRoutes(context, quotes);
            var snapshots = new NativeEffectSnapshots(() -> context.adopted().observations(), context.archive(), context.frameLoader());
            warWindow = new NativeArmyWarWindowEffects(snapshots, context.reads(), routes::queries,
                    new RootHolyHirePoststate(context, inputs.holyPoststateSources()));
            warAdmission = new NativeOrdinaryWarAdmission(context.writer(), context.archive(), context.frameLoader());
            ArmyOrdinaryActionPreparation.FinalGates gates = new ArmyOrdinaryActionPreparation.FinalGates() {
                @Override public void verify(Complete frame, ArmyOrdinaryActionArguments arguments, NativeRequest primitive) {
                    throw new IllegalStateException("Army final gate requires the original writer Session");
                }
                @Override public void verify(Session same, Complete frame, ArmyOrdinaryActionArguments arguments, NativeRequest primitive) {
                    if (arguments.kind() == Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1
                            || arguments.kind() == Kind.CLOSE_WAR_RESULTS_WINDOW_V1) {
                        var call = ArmyCallCodec.decode(PublicMethod.valueOf(arguments.kind().name()), arguments.publicArguments());
                        StrictJson.require(call instanceof ArmyCalls.Frame, "fixed-window final gate requires the original frame call");
                        context.archive().inSession(same, bound -> {
                            try {
                                ArmyOrdinaryActionService.rejectDirectWindowDeferred(
                                        ContinuityActionJournal.receipts(same.head().state(), bound),
                                        (ArmyCalls.Frame) call, frame, bound, context.frameLoader());
                                return null;
                            } catch (IOException failure) {
                                throw new UncheckedIOException("same-writer fixed-window retry basis unavailable", failure);
                            }
                        });
                    }
                    if (WAR_WINDOW.contains(arguments.kind())) warWindow.verifyPrepared(frame, arguments, primitive);
                    else inputs.remainingFinalGates().verify(same, frame, arguments, primitive);
                }
            };
            preparation = new ArmyOrdinaryActionPreparation(context.writer(), () -> context.adopted().observations(),
                    context.reads(), context.archive(), quotes, warAdmission, inputs.occupation(), warAdmission.finalGates(gates));
            List<ArmyOrdinaryActionService.Effect> effects = new ArrayList<>();
            for (var effect : inputs.remainingEffects()) {
                if (effect.kind() != Kind.OFFER_WHITE_PEACE) effects.add(effect);
                else effects.add(new ArmyOrdinaryActionService.Effect(effect.kind(), effect.source(), effect.observer(),
                        effect.expected(), operation -> {
                            var original = effect.replay().binding(operation);
                            return new NativeRecordedEvidenceVerifier.Binding(operation, original.definitionSource(), (head, receipt, archive) -> {
                                warAdmission.replayAdmission(head, receipt, archive); original.verifier().verify(head, receipt, archive);
                            });
                        }));
            }
            for (Kind kind : Kind.values()) if (WAR_WINDOW.contains(kind)) {
                effects.add(new ArmyOrdinaryActionService.Effect(kind, inputs.warWindowObserverSource(), warWindow,
                        NativeArmyWarWindowEffects::expected, operation -> {
                            var effect = warWindow.archivedVerifier(operation, inputs.warWindowObserverSource(), context.frameLoader());
                            if (kind != Kind.DECLARE_WAR) return effect;
                            return new NativeRecordedEvidenceVerifier.Binding(operation, effect.definitionSource(), (head, receipt, archive) -> {
                                warAdmission.replayAdmission(head, receipt, archive); effect.verifier().verify(head, receipt, archive);
                            });
                        }));
            }
            ActionCoordinatorPort sameCoordinator = new ActionCoordinatorPort() {
                @Override public ActionReceipt execute(ActionCommand command) { return context.actions().execute(command); }
                @Override public ActionReceipt execute(Session same, ActionCommand command) { return context.actions().execute(same, command); }
                @Override public ActionReceipt reconcile(String id) { return context.actions().reconcile(id); }
                @Override public ActionReceipt reconcile(Session same, String id) { return context.actions().reconcile(same, id); }
            };
            service = new ArmyOrdinaryActionService(context.writer(), sameCoordinator, context.archive(), preparation,
                    context::bindings, this::current, inputs.actionIds(), inputs.sources(), effects,
                    Optional.of(inputs.commander()), Optional.of(inputs.mercenary()), context.clock(), context.frameLoader());
            StrictJson.require(service.supported().equals(EnumSet.allOf(Kind.class)), "full seventeen Army action installation required");
            var families = service.actionFamilies();
            var holyOrderRead = inputs.producers().holyOrders().installedRead(inputs.holyOrderDecoderSource());
            var holyOrderReconciliation=inputs.producers().holyOrders().reconciliationInstalledRead(inputs.holyOrderDecoderSource());
            installation = new RootDomainInstallation("army-ordinary-original-runtime", List.of(), List.of(holyOrderRead,holyOrderReconciliation), List.of(),
                    List.of(), List.of(), List.of(), families, List.of(), List.of(), List.of(), Set.of(), List.of(), List.of(),
                    List.of(), families.stream().map(family -> new RootDomainInstallation.FamilyDomain(family, Domain.war)).toList(), List.of());
        }
        public ArmyOrdinaryActionService service() { return service; }
        public ArmyOrdinaryActionPreparation preparation() { return preparation; }
        public ArmyOrdinaryPairedQuotes quotes() { return quotes; }
        public ArmyWarWindowRuntimeRoutes routes() { return routes; }
        /** Same observer used by this installation's Effect and archived verifier; this getter issues no query or proof. */
        public NativeDirectFixedWindowObservation directWindows() { return warWindow.directWindows(); }
        /** The identical producer whose source-bound private read is already in this installation. */
        public org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContextRead holyOrders() { return inputs.producers().holyOrders(); }
        public RootDomainInstallation installation() { return installation; }
        public List<PublicBindings.BoundBinding> installPublic(PublicBindings publicBindings) {
            return service.install(publicBindings, inputs.sources().service());
        }
        /** Independent Window2 and original holy-hire candidates. Root still verifies canonical pending membership. */
        public List<RootReconciliationAuthority.AllowedRead> reconciliationReads(ActionReceipt original,
                ReconciliationIdentity identity, Complete actual, Instant deadline) {
            Objects.requireNonNull(original); Objects.requireNonNull(identity); Objects.requireNonNull(actual); Objects.requireNonNull(deadline);
            if (!Set.of(NativeArmyWarWindowEffects.SCHEMA, NativeArmyWarWindowEffects.DIRECT_SCHEMA)
                    .contains(original.command().expected().observerSchema())) return List.of();
            String operation = original.command().operation().value();
            if (!operation.equals("close-war-declared-overview-v1") && !operation.equals("close-war-results-window-v1")
                    &&!operation.equals("hire-holy-order-v1")) return List.of();
            StrictJson.require(original.command().actionId().equals(identity.pending().actionId())
                    && original.bodySha256().equals(identity.pending().bodySha256())
                    && ActionTransitions.attempt(original.state()).orElseThrow().requestId().equals(identity.pending().requestId()),
                    "window reconciliation changed its original canonical pending action/request");
            var arguments = ArmyOrdinaryActionArguments.decode(original.command().arguments());
            StrictJson.require(original.command().expected().equals(NativeArmyWarWindowEffects.expected(original.command().before(),
                    original.command().source(), original.command().operation(), new RawJson(DriverJson.encode(original.command().arguments())))),
                    "Window2 reconciliation profile/schema differs from its original preparation");
            if(operation.equals("hire-holy-order-v1")) {
                var selected=(ArmyWarWindowReads.HolyHire)ArmyWarWindowReads.selection(arguments,original.command().operation());
                var scope=new ArmyWarWindowReads.Request(actual,selected,deadline,Optional.of(identity));
                var query=routes.queries(selected).holyOrder();var contract=query.contract(scope);
                var request=scope.planning(query.operation(),query.arguments().apply(scope));
                org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContextRead.requireCanonicalReconciliation(
                        original,ActionTransitions.attempt(original.state()).orElseThrow(),identity,contract,request);
                return List.of(new RootReconciliationAuthority.AllowedRead(contract,request.arguments(),RootReconciliationAuthority.QueryKind.HOLY_ORDER_EMPLOYER));
            }
            var selected = (ArmyWarWindowReads.Window) ArmyWarWindowReads.selection(arguments, original.command().operation());
            var scope = new ArmyWarWindowReads.Request(actual, selected, deadline, Optional.of(identity));
            var query = routes.window(selected.window()); var contract = query.contract(scope);
            var request = scope.planning(query.operation(), query.arguments().apply(scope));
            ArmyWindowReconciliationBinding.verify(original, ActionTransitions.attempt(original.state()).orElseThrow(),
                    identity, contract, request, ArmyWindowReads.driverGeneration(actual));
            return List.of(new RootReconciliationAuthority.AllowedRead(contract, request.arguments(), RootReconciliationAuthority.QueryKind.WINDOW2));
        }
        private ArmyTypes.Context current() {
            try {
                var actual = inputs.producers().frames().current(context.clock().instant().plus(inputs.commandTimeout()));
                StrictJson.require(actual.actual().source().equals(context.source())
                        && actual.actual().sessionId().equals(context.game().sessionId())
                        && actual.actual().identity().game().equals(context.game().generation()),
                        "Army public current producer belongs to another actual Game/source/session");
                return actual.context();
            }
            catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IllegalStateException("actual Army frame interrupted", interrupted); }
        }
    }
}
