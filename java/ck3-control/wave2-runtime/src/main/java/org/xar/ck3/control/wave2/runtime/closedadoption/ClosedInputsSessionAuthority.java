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
    private final Map<Integer,RestorePrepared> preparedOperations = new HashMap<>();
    private Optional<RestorePrepared> restore = Optional.empty();
    private boolean closed;
    private long callbacks;

    private ClosedInputsSessionAuthority(ClosedAdoptionMaterial.CurrentSource source,
            OriginalWriterTransaction.Committed committed,
            ClosedColdInputsConsumer.CanonicalReceiptSource canonical,
            RecoveryEvidence basis, RecoveryEvidence qualification, Instant deadline, Optional<RetainedClosedMeasurement> historical) {
        this.source = Objects.requireNonNull(source); this.committed = Objects.requireNonNull(committed);
        this.canonical = Objects.requireNonNull(canonical); this.basis = Objects.requireNonNull(basis);
        this.qualification = Objects.requireNonNull(qualification); this.deadline = Objects.requireNonNull(deadline);
        this.historical = Objects.requireNonNull(historical);
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
        var session = new ClosedInputsSessionAuthority(source,committed,canonical,basis,qualification,deadline,historical);
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
    @Override public void close() { requireThread(); closed = true; historical.ifPresent(RetainedClosedMeasurement::close); }

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
        qualify(basis.reference(),qualification.reference());
    }
    private void requirePrepared(RestorePrepared selected) {
        requireOpen(); StrictJson.require(Instant.now().isBefore(selected.reviewAt()),"actual Prepared source tuple remains within its own earlier review");
        for (ExactRef ref : java.util.List.of(selected.plan(),selected.quote(),selected.preflight())) { closedMaterial.sourceVerifier().verify(ref); }
    }
    String qualificationScope() { requireThread(); return restore.isPresent() ? ClosedColdInputsConsumer.RETAINED_SCOPE : ClosedColdInputsConsumer.SCOPE; }
}
