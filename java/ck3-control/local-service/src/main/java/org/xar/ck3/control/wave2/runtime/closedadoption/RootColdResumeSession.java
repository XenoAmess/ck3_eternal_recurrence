package org.xar.ck3.control.wave2.runtime.closedadoption;

import org.xar.ck3.control.platform.NativeLaunchPolicy;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.WindowsPreloadCustody;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeColdAdoptionProjection;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.context.RootNativeRuntimeBinding;
import org.xar.ck3.control.g2.context.RootSteamOfflineGate;
import org.xar.ck3.control.g2.context.RootSavedLoadReadiness;

/** Private-minted finite cold lifecycle, available before either a Game or an MCP owner exists. */
public final class RootColdResumeSession implements AutoCloseable {
    public static final String BINDINGS_PATH_ENV="XAR_ROOT_COLD_BINDINGS_PATH";
    public static final String BINDINGS_BYTES_ENV="XAR_ROOT_COLD_BINDINGS_BYTES";
    public static final String BINDINGS_SHA256_ENV="XAR_ROOT_COLD_BINDINGS_SHA256";
    public enum Phase { OPEN, GAME_SUBMITTED, GAME_HELD, MCP_SUBMITTED, MCP_HELD, INJECT_SUBMITTED, INJECTED,
        CAP_SUBMITTED, CAP_COMPLETED, LINEAGE_CONFIRMED, UNKNOWN, CLOSED }
    public interface Workflow {
        void run(RootColdResumeSession session) throws IOException,InterruptedException;
        /** Root's Java materializer consumes actual bytes only after the original producer has exited zero. */
        default RootNativeMapMaterializer.JunctionScope materialize(OriginalColdConsumerSession.ComposedBundle bundle) throws IOException {
            throw new IOException("COMPOSE_BUNDLE requires the concrete Root Java materializer");
        }
    }
    public record ColdPlan(RootNativeRuntimeBinding runtime,WindowsJobProcess.CommandSpec game,
            RootSteamOfflineGate.Plan steamOfflinePlan,Path injectorEvidenceRoot,Map<String,String> injectorEnvironment,
            long injectorMemoryBytes,Duration injectorTimeout,Instant deadline) {
        public ColdPlan {
            Objects.requireNonNull(runtime); Objects.requireNonNull(game); Objects.requireNonNull(steamOfflinePlan);
            Objects.requireNonNull(injectorEvidenceRoot); injectorEnvironment=Map.copyOf(injectorEnvironment);
            Objects.requireNonNull(injectorTimeout); Objects.requireNonNull(deadline);
            StrictJson.require(injectorEvidenceRoot.isAbsolute() && injectorEvidenceRoot.normalize().equals(injectorEvidenceRoot)
                    && injectorMemoryBytes >= (64L<<20) && !injectorTimeout.isNegative() && !injectorTimeout.isZero()
                    && injectorTimeout.compareTo(Duration.ofSeconds(60))<=0,"finite original saved-cold injector plan");
        }
    }
    /** Genuine original Windows creator and DLL lease, with no public adoption constructor. */
    public static final class HeldGame {
        private final RootColdResumeSession session;
        private final WindowsJobProcess creator;
        private final WindowsPreloadCustody.Lease lease;
        private HeldGame(RootColdResumeSession session,WindowsJobProcess creator,WindowsPreloadCustody.Lease lease) {
            this.session=session; this.creator=creator; this.lease=lease;
        }
        public WindowsJobProcess.ProcessIdentity identity() { return creator.identity(); }
        public RootColdResumeSession session() { return session; }
        public String pipeName() { return session.inputs.pipeName(); }
        public WindowsPreloadCustody.Lease custody() { return lease; }
        public RootNativeRuntimeBinding runtime() { return session.plan.orElseThrow().runtime(); }
        public Instant deadline() { return session.plan.orElseThrow().deadline(); }
        public void verify() throws IOException {
            session.requireScope(); lease.verify();
            if (!creator.identity().equals(lease.targetIdentity()) || !creator.isRunning()) { throw new IOException("same original retained cold Game generation alive"); }
        }
    }
    /** Actual same-Game Root-reviewed data, never reconstructed from an input sidecar or a boolean. */
    public static final class ActualBindings {
        private final RootColdResumeSession session;
        private final ColdModAbsenceProof.Verified actual;
        private ActualBindings(RootColdResumeSession session,ColdModAbsenceProof.Verified actual) { this.session=session;this.actual=actual; }
        public ExactRef sidecarRef() { return actual.sidecarRef(); }
        public ExactRef proofRef() { return actual.proofRef(); }
        public ExactRef launchRef() { return actual.launchRef(); }
        public List<ExactRef> sourcePins() { return actual.sourcePins(); }
        public void requireCurrent() throws IOException { session.requireScope(); requireSourcesUnchanged(); }
        void requireSourcesUnchanged() throws IOException { actual.requireSourcesUnchanged(); }
    }
    /** Decoded raw cache projection only; it neither contains an episode nor grants Native admission. */
    public record RawColdFrame(String snapshotId,long publicRevision,long nativeRevision,long dateRaw,long actorCharacterId,
            boolean mapReady,boolean paused,WindowsJobProcess.ProcessIdentity game,String pipeName,String connectionGeneration,
            String responseSha256,long arrivalSequence,NativeColdAdoptionProjection ownerColdAdoption) {
        public RawColdFrame {
            Objects.requireNonNull(ownerColdAdoption,"actual mandatory v2 owner cold-adoption projection; no v1 fallback");
            StrictJson.text(snapshotId); StrictJson.safe(publicRevision,0); StrictJson.safe(nativeRevision,1);
            StrictJson.safe(dateRaw,0); StrictJson.safe(actorCharacterId,1); Objects.requireNonNull(game);
            StrictJson.text(pipeName); StrictJson.safe(arrivalSequence,1);
            StrictJson.require(connectionGeneration!=null && connectionGeneration.matches("[1-9][0-9]{0,19}")
                    && new java.math.BigInteger(connectionGeneration).compareTo(StrictJson.UINT64_MAX)<=0,"canonical positive uint64 Native connection generation");
            StrictJson.require(snapshotId.equals("native:"+nativeRevision) && responseSha256.matches("[0-9a-f]{64}"),"exact decoded raw packet and actual RPC completion binding");
        }
        public com.fasterxml.jackson.databind.node.ObjectNode toJson() {
            var value=StrictJson.object(); value.put("snapshot_id",snapshotId); value.put("public_revision",publicRevision);
            value.put("native_revision",nativeRevision); value.put("date_raw",dateRaw); value.put("actor_character_id",actorCharacterId);
            value.put("map_ready",mapReady); value.put("paused",paused); var identity=value.putObject("actual_game");
            identity.put("pid",game.pid()); identity.put("creation_filetime_decimal",game.creationFiletimeDecimal()); identity.put("executable",game.executable());
            value.put("pipe_name",pipeName); value.put("connection_generation",connectionGeneration);
            value.put("response_sha256",responseSha256); value.put("arrival_sequence",arrivalSequence);
            value.set("owner_cold_adoption",ownerColdAdoption.toJson());return value;
        }
    }
    /** Projection of the same private completed CAP response. This data cannot mint a poststate ticket. */
    public record CapabilitiesCompletion(String responseSha256,long arrivalSequence,
            WindowsJobProcess.ProcessIdentity owner,WindowsJobProcess.ProcessIdentity game,String pipeName,
            String connectionGeneration) {
        public CapabilitiesCompletion {
            Objects.requireNonNull(owner);Objects.requireNonNull(game);StrictJson.text(pipeName);
            StrictJson.safe(arrivalSequence,1);
            StrictJson.require(responseSha256!=null && responseSha256.matches("[0-9a-f]{64}"),"actual completed CAP RPC SHA256");
            StrictJson.require(connectionGeneration!=null && connectionGeneration.matches("[1-9][0-9]{0,19}")
                    && new java.math.BigInteger(connectionGeneration).compareTo(StrictJson.UINT64_MAX)<=0,
                    "canonical positive uint64 CAP connection generation");
        }
        public com.fasterxml.jackson.databind.node.ObjectNode toJson() {
            var value=StrictJson.object();value.put("response_sha256",responseSha256);value.put("arrival_sequence",arrivalSequence);
            putIdentity(value.putObject("actual_owner"),owner);putIdentity(value.putObject("actual_game"),game);
            value.put("pipe_name",pipeName);value.put("connection_generation",connectionGeneration);return value;
        }
        private static void putIdentity(com.fasterxml.jackson.databind.node.ObjectNode node,WindowsJobProcess.ProcessIdentity identity) {
            node.put("pid",identity.pid());node.put("creation_filetime_decimal",identity.creationFiletimeDecimal());node.put("executable",identity.executable());
        }
    }
    /** Can only be minted by this actual retained session after independent review and original writer preview. */
    public static final class RawFrameTicket {
        private final RootColdResumeSession session;
        private final RawColdFrame frame;
        private final ExactRef approval;
        private boolean consumed;
        private RawFrameTicket(RootColdResumeSession session,RawColdFrame frame,ExactRef approval) {
            this.session=session; this.frame=frame; this.approval=approval;
        }
        public ExactRef approvalRef() { return approval; }
        public void consume(RootColdResumeSession actualSession,RawColdFrame actualFrame,
                WindowsJobProcess.OwnedStdio actualOwner) throws IOException {
            if (actualSession!=session || !frame.equals(actualFrame) || consumed) { throw new IOException("same once Root raw ticket and actual completed raw projection required"); }
            session.requireNativeOwner(actualOwner); session.validateRaw(actualFrame);
            session.authority.requireColdRawTicketCurrent(session,actualFrame,approval);
            StrictJson.require(session.phase==Phase.INJECTED && session.acceptedRaw.isEmpty(),"one actual completed raw frame admitted before bootstrap CAP");
            session.acceptedRaw=Optional.of(frame);session.rawApproval=Optional.of(approval);consumed=true;
        }
    }
    /** Private result of the new post-CAP SDK read, independent Root review and original writer read lock. */
    public static final class CapabilitiesTicket {
        private final RootColdResumeSession session;
        private final CapabilitiesCompletion completion;
        private final ExactRef approval;
        private boolean consumed;
        private CapabilitiesTicket(RootColdResumeSession session,CapabilitiesCompletion completion,ExactRef approval) {
            this.session=session;this.completion=completion;this.approval=approval;
        }
        public ExactRef approvalRef() { return approval; }
        public void consume(RootColdResumeSession actualSession,CapabilitiesCompletion actual,
                WindowsJobProcess.OwnedStdio actualOwner) throws IOException {
            if(actualSession!=session || !completion.equals(actual) || consumed) { throw new IOException("same once post-CAP ticket and actual private completion required"); }
            session.validateCapabilities(actual,actualOwner);
            session.authority.requireColdCapabilitiesTicketCurrent(session,actual,approval);
            StrictJson.require(session.phase==Phase.CAP_COMPLETED,"new actual post-CAP measurement before Native source activation");
            consumed=true;session.phase=Phase.LINEAGE_CONFIRMED;
        }
    }
    private final Thread thread=Thread.currentThread();
    private final ClosedInputsSessionAuthority authority;
    private final int preparedSequence;
    private final ClosedInputsSessionAuthority.NativeRestoreInputs inputs;
    private final Path reviewDirectory;
    private final String nonce=UUID.randomUUID().toString().replace("-","");
    private final ColdStageAttempts submissions=new ColdStageAttempts();
    private Optional<ColdPlan> plan=Optional.empty();
    private Optional<HeldGame> game=Optional.empty();
    private Optional<NativeOwnerResumeSession> owner=Optional.empty();
    private Optional<RootSavedLoadReadiness.Prepared> logEpoch=Optional.empty();
    private Optional<RootSavedLoadReadiness.Ready> savedLoad=Optional.empty();
    private Optional<Instant> actualInjectionCompleted=Optional.empty();
    private Optional<ActualBindings> actualBindings=Optional.empty();
    private Optional<RawColdFrame> acceptedRaw=Optional.empty();
    private Optional<ExactRef> rawApproval=Optional.empty();
    private Optional<CapabilitiesCompletion> actualCapabilities=Optional.empty();
    private Optional<Instant> actualCapabilitiesCompleted=Optional.empty();
    private boolean rawQualificationStarted;
    private boolean bootstrapClaimed;
    private Phase phase=Phase.OPEN;
    private RootColdResumeSession(ClosedInputsSessionAuthority authority,int preparedSequence,Path reviewDirectory) {
        this.authority=authority; this.preparedSequence=preparedSequence; this.inputs=authority.nativeRestoreInputs(preparedSequence);
        this.reviewDirectory=reviewDirectory;
    }
    static RootColdResumeSession open(ClosedInputsSessionAuthority authority,int preparedSequence,Path actualOwnedDirectory) {
        RootColdResumeSession session=new RootColdResumeSession(authority,preparedSequence,actualOwnedDirectory);
        authority.registerColdResumeSession(session); return session;
    }
    public ClosedInputsSessionAuthority.NativeRestoreInputs restoreInputs() throws IOException { requireScope(); return inputs; }
    public ClosedInputsSessionAuthority.NativeRestoreInputs runtimeInputs() throws IOException { return restoreInputs(); }
    public List<ControlBuild.FileRef> approvedProgramSources() throws IOException {
        requireScope();
        try { return authority.approvedNativeProgramSources(preparedSequence); }
        catch(InterruptedException failure) { Thread.currentThread().interrupt(); throw new IOException("original profile writer handoff interrupted",failure); }
    }
    public NativeOwnerResumeSession.SharedStatePaths statePaths() throws IOException { requireScope(); return NativeOwnerResumeSession.sharedStatePaths(inputs); }
    public NativeOwnerResumeSession.SavedCheckpoint checkpoint() throws IOException { requireScope(); return NativeOwnerResumeSession.savedCheckpoint(inputs); }
    public SavedFrame savedFrame() throws IOException { requireScope(); return NativeOwnerResumeSession.savedFrame(inputs); }
    public Phase phase() { requireThread(); return phase; }
    public void requireCurrent() throws IOException { requireScope(); if (game.isPresent()) { game.orElseThrow().verify(); } }
    public Path ownedDirectory() throws IOException { requireScope(); return reviewDirectory; }
    public Instant actualInjectionCompletedAt() throws IOException { requireScope(); return actualInjectionCompleted.orElseThrow(); }
    public Instant actualCapabilitiesCompletedAt() throws IOException { requireScope();return actualCapabilitiesCompleted.orElseThrow(); }
    RawColdFrame retainedRawFrame() throws IOException { requireScope();return acceptedRaw.orElseThrow(); }
    String scopeNonce() { requireThread(); return nonce; }
    RootSavedLoadReadiness.Ready actualSavedLoad() throws IOException { requireScope(); return savedLoad.orElseThrow(); }
    Optional<ActualBindings> actualBindingsIfPresent() { requireThread(); return actualBindings; }
    boolean coldStageSubmitted(RootColdStageReview.Stage stage) { requireThread();return submissions.submitted(stage); }
    public ActualBindings actualBindings() throws IOException { requireScope(); ActualBindings actual=actualBindings.orElseThrow();actual.requireSourcesUnchanged();return actual; }
    public Map<String,String> bindOwnerEnvironment(Map<String,String> original) throws IOException {
        ActualBindings actual=actualBindings();var result=new java.util.HashMap<>(original);ExactRef sidecar=actual.sidecarRef();
        result.put(BINDINGS_PATH_ENV,sidecar.path());result.put(BINDINGS_BYTES_ENV,Long.toString(sidecar.bytes()));result.put(BINDINGS_SHA256_ENV,sidecar.sha256());return Map.copyOf(result);
    }
    public boolean grantsWarmAttachment() { return false; }
    public boolean replayAllowed() { return false; }
    public HeldGame heldGame() throws IOException { requireScope(); HeldGame actual=game.orElseThrow(); actual.verify(); return actual; }
    public NativeOwnerResumeSession nativeOwnerSession() throws IOException {
        requireScope(); NativeOwnerResumeSession actual=owner.orElseThrow(); actual.requireBeforeHelloOrCapabilities(actual.ownedStdio()); return actual;
    }

    /** Each invocation publishes a fresh nonce challenge and waits for a separate actual Root review. */
    public HeldGame createSavedGame(ColdPlan requested) throws IOException,InterruptedException {
        requireScope(); StrictJson.require(phase==Phase.OPEN && plan.isEmpty(),"one original saved-cold Game creation attempt");
        submissions.requireAvailable(RootColdStageReview.Stage.SAVED_GAME_CREATE);validateColdPlan(requested);
        RootColdStageReview.PlannedCommand command=gameCommand(requested);
        var reviewed=review(RootColdStageReview.Stage.SAVED_GAME_CREATE,command,Optional.empty());
        plan=Optional.of(requested);
        AtomicReference<WindowsPreloadCustody.Lease> retained=new AtomicReference<>();
        try {
            WindowsJobProcess actual=authority.withColdStageReadLock(preparedSequence,reviewed,()->submissions.submit(
                    RootColdStageReview.Stage.SAVED_GAME_CREATE,()->{
                requested.runtime().verify();
                requireLaunchOutputs(requested);
                Path logsAttempt=reviewDirectory.resolve("game-logs-"+UUID.randomUUID().toString().replace("-",""));
                java.nio.file.Files.createDirectory(logsAttempt);
                logEpoch=Optional.of(RootSavedLoadReadiness.prepare(statePaths().profileRoot(),logsAttempt));
                // This is the same actual qualified background producer, observed after the independent review wait.
                var offline=RootSteamOfflineGate.observe(requested.runtime(),requested.steamOfflinePlan());
                offline.consumeBeforeGameCreate(requested.runtime()); requireScope(); requested.runtime().verify();
                requireLaunchOutputs(requested);
            },()->{
                phase=Phase.GAME_SUBMITTED;
                WindowsJobProcess created=WindowsJobProcess.start(requested.game(),WindowsJobProcess.ConsoleMode.NO_WINDOW,target->{
                    WindowsPreloadCustody.Lease lease=WindowsPreloadCustody.prepare(target,
                            new WindowsPreloadCustody.DllRef(requested.runtime().request().nativeDll(),requested.deadline(),()->{
                                requested.runtime().verify(); requireScope();
                            }));
                    if (!retained.compareAndSet(null,lease)) { lease.close(); throw new IOException("original pre-resume callback repeated; no replay"); }
                    // Saved cold deliberately resumes without PrepareStartup; injection is a separate once stage.
                    return lease;
                });
                var lease=retained.get(); StrictJson.require(lease!=null,"actual original held DLL lease before primary resume");
                game=Optional.of(new HeldGame(this,created,lease)); // Retain before writer release/exit can fail.
                return created;
            }));
            var lease=retained.get(); StrictJson.require(lease!=null,"actual original held DLL lease before primary resume");
            HeldGame held=new HeldGame(this,actual,lease); game=Optional.of(held); phase=Phase.GAME_HELD;
            held.verify(); return held;
        } catch(IOException|InterruptedException|RuntimeException|Error failure) {
            if(failure instanceof OriginalWriterTransaction.ColdStageNotSubmitted clean
                    && clean.stage()==RootColdStageReview.Stage.SAVED_GAME_CREATE && !coldStageSubmitted(clean.stage())) {
                plan=Optional.empty();logEpoch=Optional.empty();phase=Phase.OPEN;
            } else { phase=Phase.UNKNOWN; }
            throw failure;
        }
    }
    /** Original current-epoch log readiness only; this never grants Native or mutating CAP. */
    public RootSavedLoadReadiness.Ready awaitSavedLoad() throws IOException,InterruptedException {
        HeldGame held=heldGame(); StrictJson.require(phase==Phase.GAME_HELD,"saved-load readiness before owner and injection");
        if (savedLoad.isEmpty()) {
            savedLoad=Optional.of(RootSavedLoadReadiness.await(logEpoch.orElseThrow(),held.creator,held.lease,
                    plan.orElseThrow().runtime(),plan.orElseThrow().deadline()));
        }
        held.verify(); return savedLoad.orElseThrow();
    }
    /** No automatic log interpretation. Root explicitly approves the actual fixed profile and recorded startup snapshot. */
    public ActualBindings prepareActualBindings(WindowsJobProcess.OwnedStdioSpec plannedOwner) throws IOException,InterruptedException {
        heldGame().verify();StrictJson.require(phase==Phase.GAME_HELD && savedLoad.isPresent() && actualBindings.isEmpty(),
                "one actual same-Game mod-absence Root review before MCP creation");
        ColdModAbsenceProof.Prepared prepared=ColdModAbsenceProof.prepare(this);
        var sources=new java.util.ArrayList<>(plannedOwner.programSourceRefs().stream().map(RootColdResumeSession::exact).toList());
        sources.addAll(prepared.sourcePins());
        var command=new RootColdStageReview.PlannedCommand(plannedOwner.command(),exact(plannedOwner.executableRef()),sources,plannedOwner.deadline());
        var reviewed=review(RootColdStageReview.Stage.MOD_ABSENCE_ROOT_REVIEW,command,Optional.of(heldGame().identity()));
        try {
            var result=authority.withColdStageReadLock(preparedSequence,reviewed,()->submissions.submit(
                    RootColdStageReview.Stage.MOD_ABSENCE_ROOT_REVIEW,prepared::requireCurrent,()->{
                var produced=prepared.publish(reviewed);var bindings=new ActualBindings(this,produced);
                actualBindings=Optional.of(bindings);return bindings;
            }));
            result.requireCurrent();return result;
        } catch(IOException|InterruptedException|RuntimeException|Error failure) {
            if(failure instanceof OriginalWriterTransaction.ColdStageNotSubmitted clean
                    && clean.stage()==RootColdStageReview.Stage.MOD_ABSENCE_ROOT_REVIEW && !coldStageSubmitted(clean.stage())) {
                phase=Phase.GAME_HELD;
            } else { phase=Phase.UNKNOWN; }throw failure;
        }
    }
    public NativeOwnerResumeSession startOwner(WindowsJobProcess.OwnedStdioSpec spec) throws IOException,InterruptedException {
        heldGame().verify(); StrictJson.require(phase==Phase.GAME_HELD && savedLoad.isPresent() && actualBindings.isPresent(),"actual original saved-load readiness and independent same-Game mod review before one MCP owner attempt");
        submissions.requireAvailable(RootColdStageReview.Stage.MCP_OWNER);
        plan.orElseThrow().runtime().requireOwnerSpecification(spec);
        ExactRef sidecar=actualBindings().sidecarRef();
        StrictJson.require(sidecar.path().equals(spec.command().environment().get(BINDINGS_PATH_ENV))
                && Long.toString(sidecar.bytes()).equals(spec.command().environment().get(BINDINGS_BYTES_ENV))
                && sidecar.sha256().equals(spec.command().environment().get(BINDINGS_SHA256_ENV)),"same actual private Root sidecar data binding in the reviewed immutable MCP environment");
        var planned=new RootColdStageReview.PlannedCommand(spec.command(),exact(spec.executableRef()),
                spec.programSourceRefs().stream().map(RootColdResumeSession::exact).toList(),spec.deadline());
        var reviewed=review(RootColdStageReview.Stage.MCP_OWNER,planned,Optional.of(heldGame().identity()));
        try {
            NativeLaunchPolicy.requireOutputLocations(List.of(spec.command().stdout(), spec.command().stderr()),
                    spec.command().environment(), spec.deadline());
            phase=Phase.MCP_SUBMITTED;
            var started=NativeOwnerResumeSession.startOwnerAfterStageReview(authority,preparedSequence,spec,reviewed,submissions);
            if (started instanceof NativeOwnerResumeSession.Started actual) {
                owner=Optional.of(actual.session()); phase=Phase.MCP_HELD;
                plan.orElseThrow().runtime().requireOwner(actual.session().ownedStdio()); return actual.session();
            }
            if (started instanceof NativeOwnerResumeSession.Unavailable missing) {
                boolean known=missing.cleanBeforeSubmission().filter(proof->proof.stage()==RootColdStageReview.Stage.MCP_OWNER).isPresent()
                        && !coldStageSubmitted(RootColdStageReview.Stage.MCP_OWNER);
                phase=known || missing.reason()==NativeOwnerResumeSession.Reason.MCP_SPEC_REJECTED ? Phase.GAME_HELD : Phase.UNKNOWN;
                throw new IOException("independently reviewed MCP owner unavailable: "+missing.detail(),missing.cleanBeforeSubmission().orElse(null));
            }
            phase=Phase.UNKNOWN;throw new IOException("MCP owner submission unknown; no replay");
        } catch(IOException|InterruptedException|RuntimeException|Error failure) {
            if(phase==Phase.MCP_SUBMITTED || phase==Phase.MCP_HELD) { phase=Phase.UNKNOWN; }throw failure;
        }
    }
    public WindowsJobProcess.CommandResult injectAfterSavedLoad() throws IOException,InterruptedException {
        requireScope(); StrictJson.require(phase==Phase.MCP_HELD && savedLoad.isPresent(),"one injection after original saved-load readiness and actual MCP owner");
        submissions.requireAvailable(RootColdStageReview.Stage.INJECT);
        HeldGame held=heldGame(); ColdPlan selected=plan.orElseThrow();
        WindowsJobProcess.CommandSpec command=injectorCommand(selected,held.identity());
        var planned=new RootColdStageReview.PlannedCommand(command,exact(selected.runtime().request().injector()),
                List.of(exact(selected.runtime().request().nativeDll()),exact(selected.runtime().request().gameExecutable())),selected.deadline());
        var reviewed=review(RootColdStageReview.Stage.INJECT,planned,Optional.of(held.identity()));
        try {
            WindowsJobProcess.CommandResult result=authority.withColdStageReadLock(preparedSequence,reviewed,()->submissions.submit(
                    RootColdStageReview.Stage.INJECT,()->{
                held.verify(); requireNativeOwner(owner.orElseThrow().ownedStdio()); selected.runtime().verify();
                NativeLaunchPolicy.requireOutputLocations(List.of(command.cwd(), command.stdout(), command.stderr()),
                        command.environment(), selected.deadline());
            },()->{
                phase=Phase.INJECT_SUBMITTED;
                try (WindowsJobProcess injector=WindowsJobProcess.start(command)) {
                    WindowsJobProcess.CommandResult terminal=injector.await(selected.injectorTimeout(),selected.deadline(),()->{
                        try { held.verify(); selected.runtime().verify(); } catch(IOException failure) { throw new java.io.UncheckedIOException(failure); }
                    });
                    java.nio.file.Files.write(command.cwd().resolve("terminal.json"),ControlBuild.strictMapper().writeValueAsBytes(terminal),
                            java.nio.file.StandardOpenOption.CREATE_NEW);
                    StrictJson.require(terminal.passed(),"actual original --pipe injector exit zero and whole Job empty");
                    held.custody().observeLoaded(); return terminal;
                }
            }));
            actualInjectionCompleted=Optional.of(Instant.now()); phase=Phase.INJECTED; held.verify(); return result;
        } catch(IOException|InterruptedException|RuntimeException|Error failure) {
            phase=failure instanceof OriginalWriterTransaction.ColdStageNotSubmitted clean
                    && clean.stage()==RootColdStageReview.Stage.INJECT && !coldStageSubmitted(clean.stage()) ? Phase.MCP_HELD : Phase.UNKNOWN;
            throw failure;
        }
    }
    public RawFrameTicket qualifyRawFrame(RawColdFrame actualFrame) throws IOException,InterruptedException {
        requireScope(); StrictJson.require(phase==Phase.INJECTED && !rawQualificationStarted,"one actual raw qualification after once injector completion"); validateRaw(actualFrame);
        rawQualificationStarted=true;
        // A distinct fresh-measurement writer operation supplies this stage; the old pre-owner current-Driver cache cannot authorize it.
        return authority.qualifyColdRawFrame(this,preparedSequence,actualFrame);
    }
    RawFrameTicket mintRawTicket(RawColdFrame frame,ExactRef approval) throws IOException {
        validateRaw(frame); return new RawFrameTicket(this,frame,approval);
    }
    /** The fixed actual channel calls this immediately before its one CAP write. Failure never permits replay. */
    public void claimBootstrapCapabilities(WindowsJobProcess.OwnedStdio actualOwner) throws IOException {
        requireNativeOwner(actualOwner);
        StrictJson.require(phase==Phase.INJECTED && acceptedRaw.isPresent() && !bootstrapClaimed,
                "one bootstrap CAP after same actual raw completion and original writer ticket");
        bootstrapClaimed=true;
        try {
            authority.requireColdRawTicketCurrent(this,acceptedRaw.orElseThrow(),rawApproval.orElseThrow());
            phase=Phase.CAP_SUBMITTED;
        } catch(IOException|RuntimeException|Error failure) { phase=Phase.UNKNOWN;throw failure; }
    }
    /** CAP may persist Driver. Its poststate uses a new Root read release and current-game lineage, never the old raw cache. */
    public CapabilitiesTicket qualifyCapabilitiesCompletion(CapabilitiesCompletion actual) throws IOException,InterruptedException {
        StrictJson.require(phase==Phase.CAP_SUBMITTED && actualCapabilities.isEmpty(),"one actual CAP completion after its write-before claim");
        validateCapabilities(actual,owner.orElseThrow().ownedStdio());
        actualCapabilities=Optional.of(actual);actualCapabilitiesCompleted=Optional.of(Instant.now());phase=Phase.CAP_COMPLETED;
        try { return authority.qualifyColdCapabilities(this,preparedSequence,actual); }
        catch(IOException|InterruptedException|RuntimeException|Error failure) { phase=Phase.UNKNOWN;throw failure; }
    }
    CapabilitiesTicket mintCapabilitiesTicket(CapabilitiesCompletion actual,ExactRef approval) throws IOException {
        validateCapabilities(actual,owner.orElseThrow().ownedStdio());
        StrictJson.require(phase==Phase.CAP_COMPLETED && actualCapabilities.orElseThrow().equals(actual),"same actually retained CAP completion");
        return new CapabilitiesTicket(this,actual,approval);
    }
    private void validateCapabilities(CapabilitiesCompletion actual,WindowsJobProcess.OwnedStdio actualOwner) throws IOException {
        requireNativeOwner(actualOwner);RawColdFrame raw=acceptedRaw.orElseThrow();
        StrictJson.require(actual.owner().equals(actualOwner.identity()) && actual.game().equals(heldGame().identity())
                && actual.pipeName().equals(inputs.pipeName()) && actual.connectionGeneration().equals(raw.connectionGeneration())
                && actual.arrivalSequence()>raw.arrivalSequence(),"same actual owner, held Game, pipe, Native generation and later private CAP arrival");
    }
    private void validateRaw(RawColdFrame frame) throws IOException {
        HeldGame held=heldGame(); SavedFrame saved=savedFrame();
        StrictJson.require(frame.mapReady() && frame.paused() && frame.game().equals(held.identity())
                && frame.pipeName().equals(inputs.pipeName()) && frame.dateRaw()==saved.dateRaw()
                && frame.actorCharacterId()==saved.actorCharacterId(),"actual loaded cold date/actor/map/pause, same held Game/pipe; old episode remains basis-owned");
    }
    public void requireNativeOwner(WindowsJobProcess.OwnedStdio actualOwner) throws IOException {
        requireScope(); var actual=owner.orElseThrow(); actual.requireBeforeHelloOrCapabilities(actualOwner); heldGame().verify();
    }
    private RootColdStageReview.Reviewed review(RootColdStageReview.Stage stage,RootColdStageReview.PlannedCommand command,
            Optional<WindowsJobProcess.ProcessIdentity> actualGame) throws IOException,InterruptedException {
        var challenge=RootColdStageReview.create(authority,preparedSequence,reviewDirectory,nonce,stage,command,actualGame);
        while (true) {
            var actual=RootColdStageReview.poll(challenge); if (actual.isPresent()) { return actual.orElseThrow(); }
            Thread.sleep(100);
        }
    }
    private void validateColdPlan(ColdPlan requested) throws IOException {
        requested.runtime().verify(); var paths=NativeOwnerResumeSession.sharedStatePaths(inputs);
        requireLaunchOutputs(requested);
        requested.runtime().requireColdResumeSession(this);
        StrictJson.require(!requested.deadline().isAfter(authority.deadline())
                && !requested.deadline().isAfter(requested.runtime().request().reviewAt())
                && requested.game().executable().equals(Path.of(requested.runtime().request().gameExecutable().path()))
                && requested.game().arguments().equals(List.of("-gdpr-compliant","-userdir="+paths.profileRoot(),"-loadsave=xar_checkpoint"))
                && inputs.pipeName().equals(requested.game().environment().get("XAR_CK3_BRIDGE_PIPE"))
                && "native-headless".equals(requested.game().environment().get("XAR_CK3_BRIDGE_MODE")),"exact original saved-cold EXE/profile/loadsave/pipe tuple");
    }
    private void requireLaunchOutputs(ColdPlan requested) throws IOException {
        var paths = statePaths();
        NativeLaunchPolicy.requireGameCommand(requested.game(), inputs.pipeName(),
                List.of(paths.stateRoot(), paths.profileRoot(), reviewDirectory, requested.injectorEvidenceRoot()),
                requested.deadline());
        NativeLaunchPolicy.requireOutputLocations(List.of(requested.injectorEvidenceRoot()),
                requested.injectorEnvironment(), requested.deadline());
    }
    private RootColdStageReview.PlannedCommand gameCommand(ColdPlan selected) {
        var runtime=selected.runtime().request();
        var sources=new java.util.ArrayList<>(List.of(exact(runtime.nativeDll()),exact(runtime.injector()),
                inputs.plan(),inputs.quote(),inputs.preflight(),exact(selected.steamOfflinePlan().steamExecutable())));
        return new RootColdStageReview.PlannedCommand(selected.game(),exact(runtime.gameExecutable()),
                sources,selected.deadline());
    }
    private WindowsJobProcess.CommandSpec injectorCommand(ColdPlan selected,WindowsJobProcess.ProcessIdentity actualGame) throws IOException {
        NativeLaunchPolicy.requireOutputLocations(List.of(selected.injectorEvidenceRoot()),
                selected.injectorEnvironment(), selected.deadline());
        java.nio.file.Files.createDirectories(selected.injectorEvidenceRoot());
        Path attempt=selected.injectorEvidenceRoot().resolve("attempt-"+UUID.randomUUID().toString().replace("-",""));
        java.nio.file.Files.createDirectory(attempt);
        return new WindowsJobProcess.CommandSpec(Path.of(selected.runtime().request().injector().path()),
                List.of("--pipe",inputs.pipeName(),Long.toString(actualGame.pid()),selected.runtime().request().nativeDll().path()),
                attempt,selected.injectorEnvironment(),attempt.resolve("stdout.log"),
                attempt.resolve("stderr.log"),selected.injectorMemoryBytes());
    }
    private void requireScope() throws IOException {
        requireThread(); if (phase==Phase.CLOSED || phase==Phase.UNKNOWN) { throw new IOException("original finite cold session closed or UNKNOWN; no replay"); }
        authority.requireNativeOwnerInputs(preparedSequence);
    }
    private void requireThread() { StrictJson.require(Thread.currentThread()==thread,"same original Root cold session JVM/thread"); }
    private static ExactRef exact(ControlBuild.FileRef ref) { return new ExactRef(ref.path(),ref.bytes(),ref.sha256()); }
    @Override public void close() {
        requireThread(); if (phase==Phase.CLOSED) { return; } phase=Phase.CLOSED;
        try { owner.ifPresent(NativeOwnerResumeSession::close); }
        finally { game.ifPresent(value->value.creator.close()); }
    }
}

