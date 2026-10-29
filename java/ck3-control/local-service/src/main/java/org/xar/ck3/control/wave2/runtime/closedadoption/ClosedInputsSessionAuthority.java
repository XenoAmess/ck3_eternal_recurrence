package org.xar.ck3.control.wave2.runtime.closedadoption;

import java.time.Instant;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.RetainedClosedMeasurement;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Non-serializable, thread-confined continuation of the original measured Java session. */
public final class ClosedInputsSessionAuthority implements AutoCloseable {
    private final Thread owner = Thread.currentThread();
    private final ClosedAdoptionMaterial.CurrentSource source;
    private final OriginalWriterTransaction.Committed committed;
    private final ClosedColdInputsConsumer.CanonicalReceiptSource canonical;
    private final RecoveryEvidence basis;
    private final RecoveryEvidence qualification;
    private final Instant deadline;
    private final String machine;
    private final ClosedAdoptionMaterial closedMaterial;
    private final ClosedColdInputsConsumer.Prepared closedProof;
    private final Optional<RetainedClosedMeasurement> historical;
    private final Optional<OriginalWriterTransaction.RetainedSession> writerSession;
    private final Map<Integer,RestorePrepared> preparedOperations = new HashMap<>();
    private Optional<RestorePrepared> restore = Optional.empty();
    private int restorePreparedSequence;
    private Optional<NativeOwnerResumeSession.OwnerAttempt> nativeOwnerAttempt = Optional.empty();
    private Optional<ColdRestoreProfile.Verified> coldProfile = Optional.empty();
    private Optional<RootColdResumeSession> coldResumeSession = Optional.empty();
    private Optional<ColdRawRestoreQualification> coldRawQualification = Optional.empty();
    private boolean coldRawAttempted;
    private boolean coldCapabilitiesAttempted;
    private Optional<ColdRawRestoreQualification> coldCapabilitiesQualification=Optional.empty();
    private Optional<RootNativeMapMaterializer.JunctionScope> junctionScope=Optional.empty();
    private boolean closed;
    private long callbacks;

    private ClosedInputsSessionAuthority(ClosedAdoptionMaterial.CurrentSource source,
            OriginalWriterTransaction.Committed committed,
            ClosedColdInputsConsumer.CanonicalReceiptSource canonical,
            RecoveryEvidence basis, RecoveryEvidence qualification, Instant deadline, Optional<RetainedClosedMeasurement> historical,
            Optional<OriginalWriterTransaction.RetainedSession> writerSession) {
        this.source = Objects.requireNonNull(source); this.committed = Objects.requireNonNull(committed);
        this.canonical = Objects.requireNonNull(canonical); this.basis = Objects.requireNonNull(basis);
        this.qualification = Objects.requireNonNull(qualification); this.deadline = Objects.requireNonNull(deadline);
        this.historical = Objects.requireNonNull(historical);
        this.writerSession = Objects.requireNonNull(writerSession);
        writerSession.ifPresent(session -> session.requireCommitted(committed));
        closedMaterial = source.current(); machine = closedMaterial.input().machineId();
        closedProof = ClosedColdInputsConsumer.prepare(source,committed,canonical);
    }

    /** Revalidates the real original-writer result and the same live SDK cache before retaining the context. */
    public static ClosedInputsSessionAuthority open(ClosedAdoptionMaterial.CurrentSource source,
            OriginalWriterTransaction.Committed committed,
            ClosedColdInputsConsumer.CanonicalReceiptSource canonical,
            RecoveryEvidence basis, RecoveryEvidence qualification, Instant deadline) {
        return open(source,committed,canonical,basis,qualification,deadline,Optional.empty());
    }
    static ClosedInputsSessionAuthority open(ClosedAdoptionMaterial.CurrentSource source,
            OriginalWriterTransaction.Committed committed, ClosedColdInputsConsumer.CanonicalReceiptSource canonical,
            RecoveryEvidence basis, RecoveryEvidence qualification, Instant deadline, Optional<RetainedClosedMeasurement> historical) {
        return open(source,committed,canonical,basis,qualification,deadline,historical,Optional.empty());
    }
    static ClosedInputsSessionAuthority open(ClosedAdoptionMaterial.CurrentSource source,
            OriginalWriterTransaction.Committed committed, ClosedColdInputsConsumer.CanonicalReceiptSource canonical,
            RecoveryEvidence basis, RecoveryEvidence qualification, Instant deadline, Optional<RetainedClosedMeasurement> historical,
            Optional<OriginalWriterTransaction.RetainedSession> writerSession) {
        var session = new ClosedInputsSessionAuthority(source,committed,canonical,basis,qualification,deadline,historical,writerSession);
        session.qualify(basis.reference(),qualification.reference());
        return session;
    }

    /** The sole callback method: no success flag, reconstructed measurement, fallback or warm grant. */
    public ClosedColdInputsConsumer.Qualified qualify(ExactRef requestedBasis, ExactRef requestedQualification) {
        requireOpen();
        StrictJson.require(basis.reference().equals(requestedBasis)
                && qualification.reference().equals(requestedQualification), "same retained Java session basis and qualification");
        ClosedColdInputsConsumer.Qualified result;
        if (restore.isPresent()) {
            requirePrepared(restore.orElseThrow());
            try { result = ClosedColdInputsConsumer.qualifyRetained(closedProof,historical.orElseThrow(),basis,qualification); }
            catch (IOException error) { throw new java.io.UncheckedIOException(error); }
            requirePrepared(restore.orElseThrow());
        } else { result = ClosedColdInputsConsumer.qualifyPublished(source,committed,canonical,basis,qualification); }
        requireOpen();
        callbacks = Math.addExact(callbacks,1);
        return result;
    }

    public String machineId() { requireOpen(); return machine; }
    public ExactRef basisRef() { requireOpen(); return basis.reference(); }
    public ExactRef qualificationRef() { requireOpen(); return qualification.reference(); }
    public byte[] basisBytes() { requireOpen(); return basis.bytes(); }
    public long committedSequence() {
        requireOpen();
        return StrictJson.integer(committed.head().value().get("sequence"),1,StrictJson.MAX_SAFE_INTEGER);
    }
    public ExactRef committedHeadRef() { requireOpen(); return committed.head().evidence().reference(); }
    /** Verify the actual loaded canonical or deployed mechanical source against the retained approved source. */
    public void verifyTransportSource(ExactRef actual, ExactRef approved) {
        requireOpen();
        StrictJson.require(actual.bytes() == approved.bytes() && actual.sha256().equals(approved.sha256()),
                "actual loaded transport source matches the existing approved exact source");
        if (restore.isPresent()) {
            var actualPath = java.nio.file.Path.of(actual.path()); var canonicalPath = java.nio.file.Path.of(approved.path());
            var deployed = restore.orElseThrow().runtimeRoot().resolve("tools/g2_saved_campaign").resolve(canonicalPath.getFileName());
            StrictJson.require(actualPath.equals(canonicalPath) || actualPath.equals(deployed),"same explicitly Prepared canonical or deployed transport source tuple");
        }
        closedMaterial.sourceVerifier().verify(actual);
        requireOpen();
    }
    public long callbackCount() { requireThread(); return callbacks; }
    public Instant deadline() { requireThread(); return deadline; }
    public boolean grantsWarmAttachment() { return false; }
    public boolean isClosed() { requireThread(); return closed; }
    private void requireThread() {
        StrictJson.require(Thread.currentThread() == owner, "retained Java authority belongs to its original owning thread");
    }
    private void requireOpen() {
        requireThread();
        StrictJson.require(!closed && Instant.now().isBefore(deadline), "retained Java session is open within the original finite lease");
    }
    @Override public void close() {
        requireThread(); closed = true;
        try {
            try { nativeOwnerAttempt.ifPresent(NativeOwnerResumeSession.OwnerAttempt::close); }
            finally { coldResumeSession.ifPresent(RootColdResumeSession::close); }
        }
        finally { historical.ifPresent(RetainedClosedMeasurement::close); }
    }

    private record RestorePrepared(java.nio.file.Path runtimeRoot, Instant reviewAt, String attemptNonce, String taskNonce,
            ExactRef plan, ExactRef quote, ExactRef preflight) { }

    /** Called only with the result of this live host's actual, fully verified PREPARED consumer process. */
    void recordPrepared(int sequence, OriginalColdConsumerSession.Prepared expected, OriginalColdConsumerSession.Consumed consumed) {
        requireOpen(); StrictJson.require(restore.isEmpty() && sequence > 0 && sequence <= RootConsumerSession.MAX_OPERATIONS,
                "Prepared is retained only in the original closed phase");
        StrictJson.require(consumed.processExit().kernelExitObserved() && consumed.processExit().exitCode() == 0,"actual Prepared consumer process completed");
        var result = SettledQueryClassifier.object(StrictJson.parse(consumed.originalConsumerReceipt(),OriginalWriterTransaction.MAX_PROTOCOL_BYTES));
        SettledQueryClassifier.equal(result,"operation","PREPARED");
        var row = StrictJson.object(result.get("operation_result"),Set.of("schema","stage","machine_id","runtime_root","observed_at_utc","review_at_utc",
                "attempt_nonce","task_nonce","basis_ref","validation_ref","plan_ref","quote_ref","preflight_ref","fresh_native_qualification",
                "full_loop_permitted","ordinary_cycle_credit","game_day_credit","original_actions_replayed"));
        SettledQueryClassifier.equal(row,"schema","xar.current-saved-prepared/v1"); SettledQueryClassifier.equal(row,"stage","OFFLINE_CONTRACT_PREPARED");
        SettledQueryClassifier.equal(row,"machine_id",machine); SettledQueryClassifier.equal(row,"attempt_nonce",expected.attemptNonce());
        SettledQueryClassifier.equal(row,"task_nonce",expected.taskNonce());
        StrictJson.require(java.nio.file.Path.of(StrictJson.text(row.get("runtime_root"))).equals(expected.runtimeRoot())
                && ExactRef.fromJson(row.get("basis_ref")).equals(basis.reference())
                && ExactRef.fromJson(row.get("validation_ref")).equals(qualification.reference()),"one actual Prepared source tuple and closed inputs");
        Instant observed = Instant.parse(StrictJson.utc(StrictJson.text(row.get("observed_at_utc"))));
        Instant review = Instant.parse(StrictJson.utc(StrictJson.text(row.get("review_at_utc"))));
        StrictJson.require(observed.isBefore(review),"Prepared observation precedes its actual review");
        for (String field : Set.of("fresh_native_qualification","full_loop_permitted","original_actions_replayed")) {
            SettledQueryClassifier.falseValue(row.get(field));
        }
        StrictJson.integer(row.get("ordinary_cycle_credit"),0,0); StrictJson.integer(row.get("game_day_credit"),0,0);
        var prepared = new RestorePrepared(expected.runtimeRoot(),review,expected.attemptNonce(),expected.taskNonce(),
                ExactRef.fromJson(row.get("plan_ref")),ExactRef.fromJson(row.get("quote_ref")),ExactRef.fromJson(row.get("preflight_ref")));
        requirePrepared(prepared);
        StrictJson.require(preparedOperations.putIfAbsent(sequence,prepared) == null,"one actual Prepared result per original operation sequence");
    }

    /** Explicit Root state transition; neither Driver drift nor a JSON GREEN flag selects historical mode. */
    void beginRestoreReads(int preparedSequence) {
        requireOpen(); StrictJson.require(restore.isEmpty() && historical.isPresent(),"registered original historical measurement and explicit new restore phase required");
        RestorePrepared selected = preparedOperations.get(preparedSequence);
        StrictJson.require(selected != null,"Prepared must have actually executed in this same live Java session");
        qualify(basis.reference(),qualification.reference()); // Original current-Driver check must still pass before the transition.
        requirePrepared(selected);
        try { historical.orElseThrow().requireHistoricalInputs(); }
        catch (IOException error) { throw new java.io.UncheckedIOException(error); }
        restore = Optional.of(selected);
        restorePreparedSequence = preparedSequence;
        qualify(basis.reference(),qualification.reference());
    }
    private void requirePrepared(RestorePrepared selected) {
        requireOpen(); StrictJson.require(Instant.now().isBefore(selected.reviewAt()),"actual Prepared source tuple remains within its own earlier review");
        for (ExactRef ref : java.util.List.of(selected.plan(),selected.quote(),selected.preflight())) { closedMaterial.sourceVerifier().verify(ref); }
    }
    String qualificationScope() { requireThread(); return restore.isPresent() ? ClosedColdInputsConsumer.RETAINED_SCOPE : ClosedColdInputsConsumer.SCOPE; }

    /** Data projection only. Possessing this record does not grant owner creation or Native reads. */
    public record NativeRestoreInputs(java.nio.file.Path runtimeRoot, ExactRef plan, ExactRef quote, ExactRef preflight,
            String attemptNonce, String taskNonce, RecoveryEvidence basis, ExactRef qualificationRef,
            ExactRef committedHeadRef, String pipeName, ExactRef entrypoint, java.nio.file.Path sdkRoot, ExactRef sdkFreeze) { }

    public NativeRestoreInputs nativeRestoreInputs(int preparedSequence) {
        requireNativeOwnerInputs(preparedSequence);
        RestorePrepared selected = restore.orElseThrow();
        var qualified = StrictJson.parse(qualify(basis.reference(),qualification.reference()).wireBytes());
        String pipe = StrictJson.text(qualified.get("closed").get("pipe_name"));
        NativeProgramSources program = nativeProgramSources(selected);
        return new NativeRestoreInputs(selected.runtimeRoot(),selected.plan(),selected.quote(),selected.preflight(),
                selected.attemptNonce(),selected.taskNonce(),basis,qualification.reference(),committedHeadRef(),pipe,
                program.entrypoint(),program.sdkRoot(),program.sdkFreeze());
    }
    private NativeProgramSources nativeProgramSources(RestorePrepared selected) {
        try {
            return writerSession.orElseThrow().nativeProgramSources(selected.runtimeRoot(),selected.plan(),selected.quote(),
                    basis.reference(),qualification.reference());
        } catch (IOException error) { throw new java.io.UncheckedIOException(error); }
    }
    void verifyNativeProgramSources(int preparedSequence, WindowsJobProcess.OwnedStdioSpec spec) throws IOException {
        requireNativeOwnerInputs(preparedSequence);
        var sources = nativeProgramSources(restore.orElseThrow());
        var profile = requireColdProfile(preparedSequence,sources);
        sources.verifyMembership(spec,profile);
    }
    void requireNativeRestoreSourcePurposeUnderLock(int sequence) {
        requireNativeOwnerInputs(sequence);nativeProgramSources(restore.orElseThrow()).requireNativeRestoreSourcePurpose();
    }
    private ColdRestoreProfile.Verified requireColdProfile(int preparedSequence, NativeProgramSources sources) throws IOException {
        if (coldProfile.isEmpty()) {
            coldProfile = Optional.of(ColdRestoreProfile.verify(nativeRestoreInputs(preparedSequence),sources.prelaunch()));
        }
        coldProfile.orElseThrow().requireUnchanged(); return coldProfile.orElseThrow();
    }
    java.util.List<org.xar.ck3.control.build.ControlBuild.FileRef> approvedNativeProgramSourcesUnderLock(int preparedSequence)
            throws IOException {
        requireNativeOwnerInputs(preparedSequence); var sources = nativeProgramSources(restore.orElseThrow());
        var profile = requireColdProfile(preparedSequence,sources);
        java.util.Map<java.nio.file.Path,ExactRef> pins = new java.util.HashMap<>(sources.approved());
        for (ExactRef ref : profile.sourcePins()) {
            ExactRef previous = pins.putIfAbsent(java.nio.file.Path.of(ref.path()),ref);
            StrictJson.require(previous == null || previous.equals(ref),"one exact source pin across original quote/SDK/profile");
        }
        return pins.values().stream().map(ref -> new org.xar.ck3.control.build.ControlBuild.FileRef(ref.path(),ref.bytes(),ref.sha256())).toList();
    }
    public java.util.List<org.xar.ck3.control.build.ControlBuild.FileRef> approvedNativeProgramSources(int preparedSequence) throws IOException, InterruptedException {
        requireNativeOwnerInputs(preparedSequence);
        if (coldProfile.isPresent()) { return approvedNativeProgramSourcesUnderLock(preparedSequence); }
        return writerSession.orElseThrow().qualifyProgramSources(this,preparedSequence);
    }
    void registerColdResumeSession(RootColdResumeSession actual) {
        requireOpen(); Objects.requireNonNull(actual);
        StrictJson.require(coldResumeSession.isEmpty() && nativeOwnerAttempt.isEmpty(),"one concrete cold lifecycle per actual Root authority");
        coldResumeSession = Optional.of(actual);
    }
    boolean coldStageSubmitted(RootColdStageReview.Stage stage) { requireThread();return coldResumeSession.orElseThrow().coldStageSubmitted(stage); }
    void releaseNativeOwnerAttemptBeforeSubmission(NativeOwnerResumeSession.OwnerAttempt actual,OriginalWriterTransaction.ColdStageNotSubmitted proof) {
        requireThread();StrictJson.require(nativeOwnerAttempt.orElseThrow()==actual && proof.stage()==RootColdStageReview.Stage.MCP_OWNER
                && !coldStageSubmitted(proof.stage()),"actual same unsubmitted owner attempt and private original-writer cleanup proof");nativeOwnerAttempt=Optional.empty();
    }
    <T> T withColdStageOwnerReadLock(int sequence,RootColdStageReview.Reviewed reviewed,
            WindowsJobProcess.OwnedStdioSpec spec,NativeOwnerResumeSession.OwnerCreation<T> creation) throws IOException,InterruptedException {
        requireNativeOwnerInputs(sequence);StrictJson.require(coldResumeSession.isPresent() && nativeOwnerAttempt.isPresent(),"actual cold lifecycle and concrete owner creation attempt");
        return writerSession.orElseThrow().withColdStageOwnerReadLock(this,sequence,reviewed,spec,creation);
    }
    <T> T withColdStageReadLock(int preparedSequence, RootColdStageReview.Reviewed reviewed,
            NativeOwnerResumeSession.OwnerCreation<T> creation) throws IOException, InterruptedException {
        requireNativeOwnerInputs(preparedSequence);
        StrictJson.require(coldResumeSession.isPresent(),"actual private cold lifecycle registered before any cold-stage submission");
        return writerSession.orElseThrow().withColdStageReadLock(this,preparedSequence,reviewed,creation);
    }
    /** Retain only the concrete scope returned by the registered workflow's actual materialization. */
    void recordMaterialized(OriginalColdConsumerSession.Consumed composed,RootNativeMapMaterializer.JunctionScope scope)
            throws IOException {
        requirePreparationPhase();
        StrictJson.require(junctionScope.isEmpty(),"one actual materialization per retained Root session");
        scope.bind(this,composed);junctionScope=Optional.of(scope);
    }
    private void requirePreparationPhase() {
        requireOpen();
        StrictJson.require(writerSession.isPresent() && historical.isPresent() && restore.isEmpty()
                && preparedOperations.isEmpty() && nativeOwnerAttempt.isEmpty() && coldResumeSession.isEmpty(),
                "pre-Prepared actual Root writer continuation and retained closed measurement required");
        writerSession.orElseThrow().requireCommitted(committed);
        writerSession.orElseThrow().requireRetainedScope();
        qualify(basis.reference(),qualification.reference());
    }
    void requireJunctionInputs(RootNativeMapMaterializer.JunctionScope actual) throws IOException {
        requirePreparationPhase();
        StrictJson.require(junctionScope.isPresent() && junctionScope.orElseThrow()==actual,
                "same non-reconstructed scope from the actual registered Root materializer");
        actual.requireCurrent(this);
    }
    CampaignScoreJunction.Prepared prepareJunction(OriginalColdConsumerSession.PrepareJunction operation) throws IOException,InterruptedException {
        requirePreparationPhase();
        var actual=junctionScope.orElseThrow(()->new org.xar.ck3.control.contracts.ContractViolationException(
                "actual same-session Root materialization scope is required before junction submission"));
        actual.select(this,operation);
        requireJunctionInputs(actual);
        return writerSession.orElseThrow().withPreparationReadLock(this,operation,actual);
    }
    void requireCompletedJunction(OriginalColdConsumerSession.PrepareOffline operation) throws IOException {
        requirePreparationPhase();
        var actual=junctionScope.orElseThrow(()->new org.xar.ck3.control.contracts.ContractViolationException(
                "actual Root junction completion is required before offline preparation"));
        actual.requireCompleted(this,operation);
    }
    com.fasterxml.jackson.databind.node.ObjectNode junctionHandoffEvidence() throws IOException {
        var actual=junctionScope.orElseThrow();
        requireJunctionInputs(actual);
        return actual.handoffEvidence(this);
    }
    void requireNativeOwnerInputs(int preparedSequence) {
        requireOpen();
        StrictJson.require(writerSession.isPresent() && historical.isPresent() && restore.isPresent()
                && restorePreparedSequence == preparedSequence && preparedOperations.get(preparedSequence) == restore.orElseThrow(),
                "actual Root production writer, original cold consumer, same-session Prepared and explicit restore phase required");
        if(coldResumeSession.isPresent()) {
            var bindings=coldResumeSession.orElseThrow().actualBindingsIfPresent();
            if(bindings.isPresent()) {
                try { bindings.orElseThrow().requireSourcesUnchanged(); }
                catch(IOException failure) { throw new java.io.UncheckedIOException(failure); }
            }
        }
        writerSession.orElseThrow().requireCommitted(committed);
        writerSession.orElseThrow().requireRetainedScope();
        qualify(basis.reference(),qualification.reference());
        if (coldProfile.isPresent()) {
            try { coldProfile.orElseThrow().requireUnchanged(); }
            catch (IOException error) { throw new java.io.UncheckedIOException(error); }
        }
    }
    RootColdResumeSession.RawFrameTicket qualifyColdRawFrame(RootColdResumeSession actual,int preparedSequence,
            RootColdResumeSession.RawColdFrame frame) throws IOException,InterruptedException {
        requireNativeOwnerInputs(preparedSequence);
        StrictJson.require(coldResumeSession.orElseThrow()==actual && !coldRawAttempted,
                "one actual registered post-HELLO qualification; a failed or UNKNOWN read is never replayed");
        coldRawAttempted=true;
        var retained=writerSession.orElseThrow();
        var context=ColdRawRestoreQualification.begin(this,actual,preparedSequence,frame,retained);
        coldRawQualification=Optional.of(context);
        return retained.withColdRawReadLock(this,preparedSequence,context,()->actual.mintRawTicket(frame,context.approvalRef()));
    }
    void requireColdRawTicketCurrent(RootColdResumeSession actual,RootColdResumeSession.RawColdFrame frame,
            ExactRef approval) throws IOException {
        requireOpen();StrictJson.require(coldResumeSession.orElseThrow()==actual && coldRawAttempted,
                "original concrete cold session before one bootstrap CAP");
        coldRawQualification.orElseThrow().requireTicket(actual,frame,approval);
    }
    RootColdResumeSession.CapabilitiesTicket qualifyColdCapabilities(RootColdResumeSession actual,int sequence,
            RootColdResumeSession.CapabilitiesCompletion completed) throws IOException,InterruptedException {
        requireNativeOwnerInputs(sequence);StrictJson.require(coldResumeSession.orElseThrow()==actual && coldRawAttempted && !coldCapabilitiesAttempted,
                "one actual same-session independent capabilities poststate qualification");coldCapabilitiesAttempted=true;
        var retained=writerSession.orElseThrow();var context=ColdRawRestoreQualification.beginCapabilities(this,actual,sequence,completed,retained,coldRawQualification.orElseThrow());
        coldCapabilitiesQualification=Optional.of(context);
        return retained.withColdCapabilitiesReadLock(this,sequence,context,()->actual.mintCapabilitiesTicket(completed,context.approvalRef()));
    }
    void requireColdCapabilitiesTicketCurrent(RootColdResumeSession actual,RootColdResumeSession.CapabilitiesCompletion completed,ExactRef approval) throws IOException {
        requireOpen();StrictJson.require(coldResumeSession.orElseThrow()==actual && coldCapabilitiesAttempted,"actual original capabilities poststate owner");
        coldCapabilitiesQualification.orElseThrow().requireCapabilitiesTicket(actual,completed,approval);
    }
    void registerNativeOwnerAttempt(NativeOwnerResumeSession.OwnerAttempt attempt) {
        requireOpen(); Objects.requireNonNull(attempt);
        StrictJson.require(nativeOwnerAttempt.isEmpty(),"one Native owner creation attempt in the actual retained Root session");
        nativeOwnerAttempt = Optional.of(attempt);
    }
    <T> T withNativeOwnerReadLock(int preparedSequence, WindowsJobProcess.OwnedStdioSpec spec,
            NativeOwnerResumeSession.OwnerCreation<T> creation) throws IOException, InterruptedException {
        requireNativeOwnerInputs(preparedSequence);
        StrictJson.require(nativeOwnerAttempt.isPresent(),"concrete one-use Native owner lifecycle registered before original writer handoff");
        return writerSession.orElseThrow().withNativeOwnerReadLock(this,preparedSequence,spec,creation);
    }
}
