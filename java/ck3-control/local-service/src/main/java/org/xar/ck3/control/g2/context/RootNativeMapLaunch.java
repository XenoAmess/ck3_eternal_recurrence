package org.xar.ck3.control.g2.context;

import java.io.IOException;
import java.util.List;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.NativeServerLocator;
import org.xar.ck3.control.wave2.runtime.closedadoption.RootColdResumeSession;
import org.xar.ck3.control.platform.NativeLaunchPolicy;

/** Concrete consumer invoked by ClosedAdoptionMain.runRootColdSession's actual Root workflow. */
public final class RootNativeMapLaunch {
    private RootNativeMapLaunch() { }
    public record Started(RootColdResumeSession.HeldGame game,
            RootNativePreloadAuthority.NativeAdmission admission,
            RootMcpSemanticClient.NativeOpenResult mapTransport) {
        public Started { Objects.requireNonNull(game); Objects.requireNonNull(admission); Objects.requireNonNull(mapTransport); }
        public RootMcpSemanticClient.NativeSession requireNativeSession() throws IOException {
            if (mapTransport instanceof RootMcpSemanticClient.NativeSession actual) return actual;
            throw new IOException("Original cold stages completed without a qualified Native map transport; no replay");
        }
    }
    /**
     * One actual private Root session owns every submission. Each Game/MOD/MCP/inject stage consumes
     * its independent Root review in the original writer lock. The old checkpoint/profile/pipe and
     * quoted deployed entry are checked by those production consumers, never inferred from this call.
     * This entry does not start an empty Game or construct an old Python SessionHandle.
     */
    public static Started launchAndOpen(RootColdResumeSession session, RootColdResumeSession.ColdPlan plan,
            WindowsJobProcess.OwnedStdioSpec plannedOwner, RootNativePreloadAuthority.SourcePlan sources,
            RootMcpWire.Handshake handshake, Instant deadline) throws IOException, InterruptedException {
        Objects.requireNonNull(session); Objects.requireNonNull(plan); Objects.requireNonNull(plannedOwner);
        Objects.requireNonNull(sources); Objects.requireNonNull(handshake); Objects.requireNonNull(deadline);
        plan.runtime().requireColdResumeSession(session);
        plan.runtime().requireOwnerSpecification(plannedOwner);
        if (!Instant.now().isBefore(deadline) || deadline.isAfter(plan.deadline())
                || deadline.isAfter(plannedOwner.deadline())
                || !sources.expectedEpisode().equals(Optional.of(session.savedFrame().episodeRunId())))
            throw new IOException("Finite original saved episode/runtime/owner plan required before Game CREATE");
        try {
            var paths = session.statePaths();
            NativeLaunchPolicy.requireGameCommand(plan.game(), session.restoreInputs().pipeName(),
                    List.of(paths.stateRoot(), paths.profileRoot(), session.ownedDirectory(), plan.injectorEvidenceRoot()), deadline);
            NativeLaunchPolicy.requireOutputLocations(List.of(plannedOwner.command().stdout(), plannedOwner.command().stderr()),
                    plannedOwner.command().environment(), deadline);
            session.createSavedGame(plan);
            session.awaitSavedLoad();
            session.prepareActualBindings(plannedOwner);
            WindowsJobProcess.OwnedStdioSpec actualSpec = bindOwner(session, plannedOwner);
            var resumedOwner = session.startOwner(actualSpec);
            var actualOwner = resumedOwner.ownedStdio();
            var serverLocator=NativeServerLocator.receive(actualOwner,session.heldGame().pipeName(),deadline);
            session.injectAfterSavedLoad();
            var game = session.heldGame();
            var admission = RootNativePreloadAuthority.prepareWhenReady(game, actualOwner, serverLocator, sources, deadline);
            var opened = RootMcpSemanticClient.openRawPreflight(actualOwner, Optional.of(admission), handshake,
                    new RootMcpWire.Limits(RootMcpEnvelope.RPC_LINE_MAX_BYTES, 128), deadline);
            if (opened instanceof RootMcpSemanticClient.Unknown unknown) return new Started(game, admission, unknown);
            if (opened instanceof RootMcpSemanticClient.Unavailable missing) return new Started(game, admission, missing);
            if (!(opened instanceof RootMcpSemanticClient.RawPreflight raw)) throw new IOException("Closed raw-open contract rejected");
            var observed = raw.observeRaw(deadline);
            if (observed instanceof RootMcpSemanticClient.Unknown unknown) return new Started(game, admission, unknown);
            if (observed instanceof RootMcpSemanticClient.Unavailable missing) return new Started(game, admission, missing);
            if (!(observed instanceof RootMcpSemanticClient.RawSnapshot snapshot)) throw new IOException("Closed raw-observation contract rejected");
            var original = snapshot.completion();
            var frame = admission.projectRawPreflight(original);
            var ticket = session.qualifyRawFrame(frame);
            admission.completeRawPreflight(original, ticket);
            // Same initialized exchange. The concrete authority claims CAP once before its first byte,
            // then consumes distinct actual post-CAP Root measurement/review before issuing Native.
            return new Started(game, admission, raw.activateNative(deadline));
        } catch (IOException | InterruptedException | RuntimeException failure) {
            if (failure instanceof InterruptedException) Thread.currentThread().interrupt();
            if (session.phase() == RootColdResumeSession.Phase.OPEN) throw failure;
            // The session retains original process/DLL/owner resources for Root. No cleanup or new
            // Game/loader/initialize is inferred from a failed review, timeout or UNKNOWN outcome.
            throw new CreatedGameUnavailable(session, failure);
        }
    }
    private static WindowsJobProcess.OwnedStdioSpec bindOwner(RootColdResumeSession session,
            WindowsJobProcess.OwnedStdioSpec planned) throws IOException {
        var command = planned.command();
        var bound = new WindowsJobProcess.CommandSpec(command.executable(), command.arguments(), command.cwd(),
                session.bindOwnerEnvironment(command.environment()), command.stdout(), command.stderr(), command.memoryLimitBytes());
        return new WindowsJobProcess.OwnedStdioSpec(bound, planned.consoleMode(), planned.executableRef(),
                planned.programSourceRefs(), planned.deadline(), planned.maxFrameBytes(), planned.maxSentBytes(),
                planned.maxReceivedBytes(), planned.guard());
    }
    public static final class CreatedGameUnavailable extends IOException {
        private static final long serialVersionUID = 1L;
        private final transient RootColdResumeSession session;
        private CreatedGameUnavailable(RootColdResumeSession session, Throwable cause) {
            super("Original saved-cold Game submission exists; map qualification unavailable, no repeated Game/load", cause);
            this.session = session;
        }
        public RootColdResumeSession session() { return session; }
        public boolean replayAllowed() { return false; }
    }
}
