package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.application.driver.DriverCapabilityRuntime;
import org.xar.ck3.control.application.driver.DriverReadHistoryPublisher;
import org.xar.ck3.control.application.driver.DriverActionHistoryPublisher;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeFrontendAuthority;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.platform.ManagedGameSession;

/** Constructs one real Game dispatcher before Controller/baseline admission; it never installs its View. */
public final class RootRuntimeDispatcherFactory {
    private RootRuntimeDispatcherFactory() { }

    /** Actual already-installed domain products. No registry, source or callback is manufactured here. */
    public record Inputs(RootApplicationAssembly.Core core, SessionIdentity identity,
            DriverBootstrap.Adopted driver, ManagedGameSession game, NativeReadinessCollector collector,
            RootExecutableBindings bindings, NativeFrontendAuthority frontend, RootLifecycleAuthority lifecycle, RootLifecycleRuntimeFactory.Installed lifecycleRuntime,
            RootReconciliationAuthority reconciliation, RootLifecycleActionGuard.CloseAdmission closeAdmission,
            RootActionGuard.DerivedChildAdmission derivedChildren,
            NativeRecordedEvidenceVerifier.DerivedGuardVerifier derivedReplay,
            DriverCapabilityRuntime capabilities, DriverReadHistoryPublisher readHistory, DriverActionHistoryPublisher actionHistory,
            List<RootDomainIntentPreparation.Binding> pending, Set<OperationKey> requiredPending,
            RootKnownReadObserver actualKnownReadObserver, Optional<RootMenuSession> originalMenu) {
        public Inputs {
            Objects.requireNonNull(core); Objects.requireNonNull(identity); Objects.requireNonNull(driver);
            Objects.requireNonNull(game); Objects.requireNonNull(collector); Objects.requireNonNull(bindings);
            Objects.requireNonNull(frontend); Objects.requireNonNull(lifecycle); Objects.requireNonNull(lifecycleRuntime); Objects.requireNonNull(reconciliation);
            Objects.requireNonNull(closeAdmission); Objects.requireNonNull(derivedChildren); Objects.requireNonNull(derivedReplay);
            Objects.requireNonNull(capabilities); Objects.requireNonNull(readHistory); Objects.requireNonNull(actionHistory);
            pending = List.copyOf(pending); requiredPending = Set.copyOf(requiredPending);
            Objects.requireNonNull(actualKnownReadObserver);
            originalMenu = Objects.requireNonNull(originalMenu);
        }
    }

    /** Original Core owns creation/reuse and publication. A constructed dispatcher is not an admitted Session. */
    public static Installed create(String authorityId, Inputs actual) throws IOException {
        StrictJson.text(authorityId); Objects.requireNonNull(actual);
        var core = actual.core(); var game = actual.game(); var bindings = actual.bindings();
        var driver = actual.driver(); var collector = actual.collector(); G2Source source = driver.source();
        game.verify();
        RootDecisionDisplay.requireSources(game.launchPlan());
        StrictJson.require(actual.identity().machineId().equals(driver.session().machineId())
                && actual.identity().game().equals(driver.session().game())
                && actual.identity().sessionId().equals(driver.session().sessionId())
                && actual.identity().equals(collector.identity())
                && actual.identity().machineId().equals(game.machineId())
                && actual.identity().game().equals(game.generation())
                && actual.identity().sessionId().equals(game.sessionId())
                && source.machineId().equals(game.machineId())
                && core.archive().writer() == core.writer(),
                "dispatcher must retain the original Core/archive/Driver/collector/physical Game identity");
        NativeGameTransport transport = game.nativeTransport();
        driver.producer().requireSameTransport(transport, source);
        bindings.requireCompleteArchiveCoverage();
        actual.reconciliation().requireOwner(core.writer(), core.archive(), bindings.readCatalog(), actual.lifecycle());
        actual.capabilities().requireOwner(driver.authority(), core.archive(), bindings);
        actual.readHistory().requireOwner(driver.authority(), core.archive(), bindings.readCatalog());
        actual.actionHistory().requireOwner(driver.authority(), core.journal(), core.archive());
        StrictJson.require(actual.capabilities().readHistoryPublisher() == actual.readHistory(),
                "dispatcher cannot replace the installed capability runtime's actual read-history publisher");

        Supplier<ContinuityStorePort.Session> borrowed = core.borrowedSessions();
        var gameplay = actual.lifecycleRuntime().wrapActions(new RootActionGuard(collector, borrowed, core.archive(), source, core.clock(), authorityId,
                core.originals(), bindings, actual.derivedChildren()));
        var menus = new RootFrontendActionGuard(actual.frontend(), borrowed, core.archive(), source, core.clock(),
                authorityId, core.originals(), bindings);
        var terminalActions = new RootLifecycleActionGuard(actual.lifecycle(), borrowed, core.archive(), source,
                core.clock(), authorityId, core.originals(), bindings, actual.closeAdmission());
        var terminalReads = new RootLifecycleReadGuard(actual.lifecycle(), borrowed, core.archive(), source,
                core.clock(), authorityId, core.originals(), bindings.readCatalog());
        var reconciliationReads = new RootReconciliationReadGuard(actual.reconciliation(), borrowed, core.archive(),
                source, core.clock(), authorityId, core.originals(), bindings.readCatalog());
        var gameplayReads = actual.lifecycleRuntime().wrapReads(new RootPlanningReadGuard(collector, borrowed, core.archive(), source, core.clock(),
                authorityId, core.originals(), bindings.readCatalog()));
        var menuReads = new RootFrontendReadGuard(actual.frontend(), borrowed, core.archive(), source, core.clock(),
                authorityId, core.originals(), bindings.readCatalog());
        var physicalReads = new RootMenuPhysicalStatusReads(bindings, source, borrowed);
        ActionPorts.GuardPort actionGuard = new OriginActions(gameplay, menus, terminalActions);
        PlanningReadCoordinator.ReadGuardPort readGuard = new OriginReads(gameplayReads, menuReads, terminalReads, reconciliationReads, physicalReads);
        RootMenuSession menu = actual.originalMenu().orElse(null);
        if (menu != null) {
            StrictJson.require(menu.authorityId.equals(authorityId) && menu.writer == core.writer() && menu.game == game
                    && menu.source.equals(source) && menu.bindings == bindings && menu.frontend == actual.frontend(),
                    "dispatcher must reuse its identical actual frontend startup graph");
        }
        PlanningReadCoordinator queries = menu == null
                ? new PlanningReadCoordinator(bindings.readCatalog(), core.journal(), core.submissionSwitchboard(),
                        transport, core.archive(), core.clock(), actual.actualKnownReadObserver())
                : menu.queries;
        var evidence = new NativeRecordedEvidenceVerifier(core.archive(), borrowed, core.originals(), core.frameLoader(),
                bindings, RootLifecycleGuardEvidence::verify, actual.derivedReplay(), actual.reconciliation()::verifyArchived,
                (command, guard, archive, same, originals) -> RootOperatorGuardEvidence.requireHistorical(same, command, guard, archive));
        var intents = new RootDomainIntentPreparation(core.writer(), actual.pending(), actual.requiredPending());
        // Existing menu objects retain their original authority identity and deferred bindings.
        // Only Root's private first-SAVE scope or later atomic publication selects a new Game View.
        var view = menu == null ? new RootSessionSwitchboard.View(actual.identity(), actionGuard, readGuard, evidence)
                : core.submissionSwitchboard().current();
        StrictJson.require(view.identity().equals(actual.identity()), "startup dispatcher View crossed its original physical Game");
        ActionCoordinatorPort dispatch;
        if (menu != null) dispatch = menu.coordinator;
        else {
            ActionCoordinator sole = new ActionCoordinator(authorityId, core.journal(), core.submissionSwitchboard(),
                    bindings, transport, bindings.effects(), core.clock(), bindings.composites(), intents,
                    (same, receipt) -> {
                        // Observe marriage cache before the sole Driver publication changes its complete state.
                        actual.capabilities().afterMarriageAttempt(same, receipt);
                        actual.actionHistory().completed(same, receipt);
                    }, actual.readHistory()::requireBeforeIntent);
            sole.bindDecisionDisplay(core.audienceDisplay());
            sole.bindPhysicalActions(core.physicalActions());
            sole.bindReconciliationObservation((same, pending, deadline, work) -> actual.reconciliation().observe(same, pending,
                    deadline, lease -> work.apply(lease.complete(), lease.provenance(), lease.identity(), lease.observationGuard())));
            dispatch = core.scopedCoordinator(sole, transport);
        }
        ActionCoordinatorPort coordinator = new RootReadPublicationActions(core, dispatch, actual.readHistory(), actual.actionHistory());
        return new Installed(view, dispatch, coordinator, queries, evidence, intents, gameplay, gameplayReads,
                terminalActions, terminalReads, reconciliationReads);
    }

    /** Private construction prevents a caller from presenting detached ports as this factory's actual result. */
    public static final class Installed {
        private final RootSessionSwitchboard.View view;
        private final ActionCoordinatorPort dispatch;
        private final ActionCoordinatorPort coordinator;
        private final PlanningReadCoordinator queries;
        private final NativeRecordedEvidenceVerifier evidence;
        private final RootDomainIntentPreparation intents;
        private final ActionPorts.GuardPort gameplay;
        private final PlanningReadCoordinator.ReadGuardPort gameplayReads;
        private final RootLifecycleActionGuard terminalActions;
        private final RootLifecycleReadGuard terminalReads;
        private final RootReconciliationReadGuard reconciliationReads;
        private Installed(RootSessionSwitchboard.View view, ActionCoordinatorPort dispatch,
                ActionCoordinatorPort coordinator, PlanningReadCoordinator queries,
                NativeRecordedEvidenceVerifier evidence, RootDomainIntentPreparation intents, ActionPorts.GuardPort gameplay,
                PlanningReadCoordinator.ReadGuardPort gameplayReads, RootLifecycleActionGuard terminalActions,
                RootLifecycleReadGuard terminalReads, RootReconciliationReadGuard reconciliationReads) {
            this.view = Objects.requireNonNull(view); this.dispatch = Objects.requireNonNull(dispatch);
            this.coordinator = Objects.requireNonNull(coordinator);
            this.queries = Objects.requireNonNull(queries); this.evidence = Objects.requireNonNull(evidence);
            this.intents = Objects.requireNonNull(intents); this.gameplay = Objects.requireNonNull(gameplay);
            this.gameplayReads = Objects.requireNonNull(gameplayReads); this.terminalActions = Objects.requireNonNull(terminalActions);
            this.terminalReads = Objects.requireNonNull(terminalReads); this.reconciliationReads = Objects.requireNonNull(reconciliationReads);
        }
        public RootSessionSwitchboard.View view() { return view; }
        public ActionCoordinatorPort dispatch() { return dispatch; }
        public ActionCoordinatorPort coordinator() { return coordinator; }
        public PlanningReadCoordinator queries() { return queries; }
        public NativeRecordedEvidenceVerifier evidence() { return evidence; }
        public RootDomainIntentPreparation intents() { return intents; }
        public ActionPorts.GuardPort gameplay() { return gameplay; }
        public PlanningReadCoordinator.ReadGuardPort gameplayReads() { return gameplayReads; }
        public RootLifecycleActionGuard terminalActions() { return terminalActions; }
        public RootLifecycleReadGuard terminalReads() { return terminalReads; }
        public RootReconciliationReadGuard reconciliationReads() { return reconciliationReads; }
    }

    private record OriginActions(ActionPorts.GuardPort gameplay, ActionPorts.GuardPort frontend,
            ActionPorts.GuardPort terminal) implements ActionPorts.GuardPort {
        @Override public GuardEvidence verify(WriterContracts.Head head, ActionCommand command) {
            if (command.origin() instanceof CommandOrigin.Gameplay) return gameplay.verify(head, command);
            if (command.origin() instanceof CommandOrigin.LifecycleTerminal) return terminal.verify(head, command);
            if (command.origin() instanceof CommandOrigin.Frontend) return frontend.verify(head, command);
            throw new IllegalArgumentException("a read-only reconciliation origin cannot submit any primitive or composite action");
        }
    }
    private record OriginReads(PlanningReadCoordinator.ReadGuardPort gameplay, PlanningReadCoordinator.ReadGuardPort frontend,
            PlanningReadCoordinator.ReadGuardPort terminal, PlanningReadCoordinator.ReadGuardPort reconciliation,
            PlanningReadCoordinator.ReadGuardPort physical)
            implements PlanningReadCoordinator.ReadGuardPort {
        @Override public <T> T withOriginalReadSource(WriterContracts.Head head,PlanningReadRequest request,
                ReadContract<?> contract,java.util.function.Supplier<T> work) {
            Objects.requireNonNull(work);
            if(request.origin() instanceof CommandOrigin.Gameplay)return gameplay.withOriginalReadSource(head,request,contract,work);
            if(request.origin() instanceof CommandOrigin.LifecycleTerminal)return terminal.withOriginalReadSource(head,request,contract,work);
            if(request.origin() instanceof CommandOrigin.Reconciliation)return reconciliation.withOriginalReadSource(head,request,contract,work);
            if(request.origin() instanceof CommandOrigin.Frontend)return frontend.withOriginalReadSource(head,request,contract,work);
            if(request.origin() instanceof CommandOrigin.PhysicalStatusOnly)return physical.withOriginalReadSource(head,request,contract,work);
            throw new IllegalArgumentException("no installed Root read guard accepts this origin");
        }
        @Override public PlanningReadGuard verify(WriterContracts.Head head, PlanningReadRequest request, ReadContract<?> contract) {
            if (request.origin() instanceof CommandOrigin.Gameplay) return gameplay.verify(head, request, contract);
            if (request.origin() instanceof CommandOrigin.LifecycleTerminal) return terminal.verify(head, request, contract);
            if (request.origin() instanceof CommandOrigin.Reconciliation) return reconciliation.verify(head, request, contract);
            if (request.origin() instanceof CommandOrigin.Frontend) return frontend.verify(head, request, contract);
            if (request.origin() instanceof CommandOrigin.PhysicalStatusOnly) return physical.verify(head, request, contract);
            throw new IllegalArgumentException("no installed Root read guard accepts this origin");
        }
        @Override public void verifyFrontendReadContinuation(WriterContracts.Head head, PlanningReadRequest request,
                ReadContract<?> contract, PlanningReadGuard before, PlanningReadGuard after) {
            StrictJson.require(request.origin() instanceof CommandOrigin.Frontend,
                    "only the actual frontend origin can reuse its issued source-bound whole-read guard");
            frontend.verifyFrontendReadContinuation(head, request, contract, before, after);
        }
        @Override public PlanningReadGuard verifyOriginalCurrent(WriterContracts.Head head, PlanningReadRequest request, ReadContract<?> contract) {
            StrictJson.require(request.origin() instanceof CommandOrigin.Gameplay, "late original reads cannot borrow another origin's held scope");
            return gameplay.verifyOriginalCurrent(head, request, contract);
        }
    }
}
