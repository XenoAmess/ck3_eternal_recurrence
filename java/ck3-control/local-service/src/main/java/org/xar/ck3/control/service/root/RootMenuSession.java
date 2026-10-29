package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeFrontendAuthority;
import org.xar.ck3.control.platform.ManagedGameSession;

/** Frontend startup retains the same query coordinator, then its one bound Driver cache observer. */
public final class RootMenuSession implements ActionCoordinatorPort {
    final ContinuityWriter writer;
    final String authorityId;
    final ManagedGameSession game;
    final G2Source source;
    final RootExecutableBindings bindings;
    final NativeFrontendAuthority frontend;
    final ActionCoordinatorPort coordinator;
    final PlanningReadCoordinator queries;
    final RootDeferredAuthorities.ActionGuard gameplay;
    final RootDeferredAuthorities.ReadGuard gameplayReads;
    final RootDeferredAuthorities.Intent intents;
    final RootDeferredAuthorities.Attempts attempts;
    final RootDeferredAuthorities.TerminalActions terminalActions;
    final RootDeferredAuthorities.TerminalReads terminalReads;
    final RootDeferredAuthorities.DerivedReplay derivedReplay;
    final RootDeferredAuthorities.ReadBarrier readBarrier;
    final RootDeferredAuthorities.Transition cycles;
    final RootDeferredAuthorities.Transition saved;
    final RootDeferredAuthorities.Transition entry;
    private volatile boolean admittedGameplay;
    RootMenuSession(String authorityId, ContinuityWriter writer, ManagedGameSession game, G2Source source, RootExecutableBindings bindings,
            NativeFrontendAuthority frontend, ActionCoordinatorPort coordinator, PlanningReadCoordinator queries,
            RootDeferredAuthorities.ActionGuard gameplay, RootDeferredAuthorities.ReadGuard gameplayReads,
            RootDeferredAuthorities.Intent intents, RootDeferredAuthorities.Attempts attempts,
            RootDeferredAuthorities.TerminalActions terminalActions, RootDeferredAuthorities.TerminalReads terminalReads,
            RootDeferredAuthorities.DerivedReplay derivedReplay,RootDeferredAuthorities.ReadBarrier readBarrier,
            RootDeferredAuthorities.Transition cycles, RootDeferredAuthorities.Transition saved,
            RootDeferredAuthorities.Transition entry) {
        this.authorityId = StrictJson.text(authorityId); this.writer = writer; this.game = game; this.source = source; this.bindings = bindings; this.frontend = frontend;
        this.coordinator = coordinator; this.queries = queries; this.gameplay = gameplay; this.gameplayReads = gameplayReads;
        this.intents = intents; this.cycles = cycles; this.saved = saved;
        this.attempts = Objects.requireNonNull(attempts);
        this.terminalActions = Objects.requireNonNull(terminalActions); this.terminalReads = Objects.requireNonNull(terminalReads);
        this.derivedReplay = Objects.requireNonNull(derivedReplay);
        this.readBarrier=Objects.requireNonNull(readBarrier);
        this.entry = entry;
    }
    @Override public synchronized ActionReceipt execute(ActionCommand command) {
        frontend.requireOutsideSourceBoundFrontendRead();requireFrontend(command);return coordinator.execute(command);
    }
    @Override public synchronized ActionReceipt reconcile(String actionId) {
        frontend.requireOutsideSourceBoundFrontendRead();
        StrictJson.require(!admittedGameplay, "frontend startup facade retired after actual gameplay admission"); return coordinator.reconcile(actionId);
    }
    public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request)throws IOException {
        var held=writer.activeSession();
        if(held.isPresent())return read(held.orElseThrow(),contract,request);
        return writer.locked(same->read(same,contract,request));
    }
    /** A whole frontend read may borrow only the same actual writer and source-bound capture. */
    public <T> PlanningReadResult<T> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            ReadContract<T> contract,PlanningReadRequest request)throws IOException {
        writer.requireSession(same);Objects.requireNonNull(contract);Objects.requireNonNull(request);
        StrictJson.require(!admittedGameplay&&request.origin() instanceof CommandOrigin.Frontend
                &&request.sessionId().equals(game.sessionId())&&request.source().equals(source)
                &&request.origin().game().equals(game.generation()),"frontend read crossed its actual original startup owner");
        var frame=request.origin().requireFrontend().frame();
        var mode=frame instanceof FrontendFrame.Menu
                ?org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRouteAdmission.FrameMode.MENU
                :org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRouteAdmission.FrameMode.SNAPSHOT;
        return frontend.withSourceBoundFrontendRead(same,mode,request.deadline(),lease->queries.read(same,contract,request));
    }
    public <T> PlanningReadResult<T> readEntry(ReadContract<T> contract, PlanningReadRequest request) throws IOException {
        StrictJson.require(!admittedGameplay && request.origin() instanceof CommandOrigin.Gameplay
                && request.sessionId().equals(game.sessionId()) && request.source().equals(source)
                && request.origin().game().equals(game.generation()), "initial gameplay read crossed its actual startup owner");
        return writer.locked(borrowed -> queries.read(borrowed, contract, request));
    }
    public <T> PlanningReadResult<T> readEntry(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed,
            ReadContract<T> contract, PlanningReadRequest request) throws IOException {
        writer.requireSession(borrowed);
        StrictJson.require(!admittedGameplay && request.origin() instanceof CommandOrigin.Gameplay
                && request.sessionId().equals(game.sessionId()) && request.source().equals(source)
                && request.origin().game().equals(game.generation()), "initial gameplay read crossed original startup owner");
        return queries.read(borrowed, contract, request);
    }
    /** Diagnostic observation is attached at the sole coordinator's real request-ID and native receive boundaries. */
    public <T> PlanningReadResult<T> readEntry(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed,
            ReadContract<T> contract,PlanningReadRequest request,PlanningReadCoordinator.ReadLifecycleObserver observer)throws IOException {
        writer.requireSession(borrowed);Objects.requireNonNull(observer);
        StrictJson.require(!admittedGameplay&&request.origin() instanceof CommandOrigin.Gameplay
                &&request.sessionId().equals(game.sessionId())&&request.source().equals(source)
                &&request.origin().game().equals(game.generation()),"initial gameplay read crossed original startup owner");
        return queries.read(borrowed,contract,request,observer);
    }
    /** Initial entry installs one source-reviewed, exact-contract scoped read guard; ordinary writes remain denied. */
    public synchronized void installEntryReads(PlanningReadCoordinator.ReadGuardPort actual, ExactRef source) throws IOException {
        StrictJson.require(!admittedGameplay && !actual.getClass().isSynthetic() && !actual.getClass().isAnonymousClass(),
                "named initial gameplay read guard required before full admission");
        game.launchPlan().sources().requireLoadedClass(actual.getClass());
        sameSession(borrowed -> {
            var pin = borrowed.capturePin(source, org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES);
            gameplayReads.bindBootstrap(actual); borrowed.verifyPin(pin); return null;
        });
    }
    public synchronized void installEntryAuthority(org.xar.ck3.control.continuity.writer.WriterContracts.TransitionAuthority actual, ExactRef source) throws IOException {
        StrictJson.require(!admittedGameplay && !actual.getClass().isSynthetic() && !actual.getClass().isAnonymousClass(),
                "named real first-episode reducer required before full gameplay admission");
        game.launchPlan().sources().requireLoadedClass(actual.getClass());
        sameSession(borrowed -> {
            var pin = borrowed.capturePin(source, org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES);
            entry.bind(actual); borrowed.verifyPin(pin); return null;
        });
    }
    private <T>T sameSession(org.xar.ck3.control.continuity.writer.ContinuityStorePort.SessionWork<T> work)throws IOException {
        var held=writer.activeSession();
        if(held.isPresent()){var same=held.orElseThrow();writer.requireSession(same);return work.run(same);}
        return writer.locked(work);
    }
    public enum PublicPhase { FRONTEND, GAMEPLAY }
    /** A factual phase only: callers still acquire the selected branch's original source/host guards. */
    public synchronized PublicPhase publicPhase(){return admittedGameplay?PublicPhase.GAMEPLAY:PublicPhase.FRONTEND;}
    synchronized void admitted() { StrictJson.require(!admittedGameplay, "startup facade already admitted"); admittedGameplay = true; }
    private void requireFrontend(ActionCommand command) {
        Objects.requireNonNull(command);
        StrictJson.require(!admittedGameplay && command.origin() instanceof CommandOrigin.Frontend && command.source().equals(source)
                && command.origin().game().equals(game.generation()) && command.sessionId().equals(game.sessionId()),
                "frontend startup accepts only its actual held origin");
    }
}

