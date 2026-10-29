package org.xar.ck3.control.wave2.runtime.savedproof;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/**
 * Synthetic ordinary metadata exercises the same production check.
 * No test double issues a production measurement token and no SDK/body is opened.
 * The actual registered-retention/restore/warm positive remains separately unexecuted.
 */
class RetainedClosedMeasurementTest {
    @TempDir Path temporary;
    private static final String MACHINE = "synthetic-history-policy-only";
    private static final String SHA = "a".repeat(64), WORKER = "b".repeat(64);
    private static final Instant OBSERVED = Instant.parse("2026-10-22T14:00:00Z");
    private static final Instant RETAINED = Instant.parse("2026-10-22T14:00:30Z");
    private static final Instant NOW = Instant.parse("2026-10-22T14:01:00Z");
    private static final Instant DEADLINE = Instant.parse("2026-10-22T15:00:00Z");
    private static Clock at(Instant instant) { return Clock.fixed(instant,ZoneOffset.UTC); }
    private ExactRef reference(String relative, long bytes) {
        return new ExactRef(temporary.resolve(relative).toAbsolutePath().toString(),bytes,SHA);
    }
    private RetainedClosedMeasurement.HistoricalInputs ordinaryFacts() {
        var value = StrictJson.object(); value.put("schema","synthetic-facts-NOT-AUTHORITY/v1");
        byte[] raw = StrictJson.canonical(value);
        var receipt = new RecoveryEvidence(new ExactRef(temporary.resolve("synthetic-receipt.json")
                .toAbsolutePath().toString(),raw.length,RecoveryEvidence.sha256(raw)),raw);
        ExactRef validator = reference("src32/xar_autoplayer/cold_checkpoint_validator.py",6093);
        return new RetainedClosedMeasurement.HistoricalInputs(MACHINE,OBSERVED,DEADLINE,RETAINED,"1".repeat(32),
                reference("original-release.json",1234),receipt,validator,reference("original-freeze.json",409_923),
                SHA,WORKER,reference("driver-state.json",41_000_000),
                new FileStatIdentity(BigInteger.valueOf(41_000_000),"6755399453430489","1792672762678085200"),
                reference("save games/xar_checkpoint.ck3",8192),
                new FileStatIdentity(BigInteger.valueOf(8192),"281474988852756","1792638019516614900"),
                List.of(validator,reference("src32/xar_autoplayer/native_session.py",60_000)));
    }
    private static final class Metadata implements RetainedClosedMeasurement.MetadataReader {
        private final RetainedClosedMeasurement.HistoricalInputs original;
        private final List<Path> statPaths = new ArrayList<>();
        private final List<ExactRef> sourceChecks = new ArrayList<>();
        private FileStatIdentity observedSave;
        private ExactRef unavailableSource;
        private boolean driftAfterSources;
        private Metadata(RetainedClosedMeasurement.HistoricalInputs original) {
            this.original = original; observedSave = original.saveIdentity();
        }
        @Override public FileStatIdentity statSave(Path path) {
            statPaths.add(path);
            if (!path.equals(Path.of(original.save().path()))) {
                throw new AssertionError("historical inputs must never stat or qualify the current Driver");
            }
            if (driftAfterSources && !sourceChecks.isEmpty()) {
                return new FileStatIdentity(original.saveIdentity().bytes(),original.saveIdentity().fileId(),
                    new BigInteger(original.saveIdentity().mtimeNs()).add(BigInteger.ONE).toString());
            }
            return observedSave;
        }
        @Override public void requireExact(ExactRef reference, int maximumBytes) throws IOException {
            sourceChecks.add(reference); assertTrue(reference.bytes() <= maximumBytes,"complete source-specific byte cap");
            if (reference.equals(unavailableSource)) { throw new IOException("synthetic original source drift"); }
        }
    }
    private static void require(RetainedClosedMeasurement.HistoricalInputs facts, Metadata metadata) throws IOException {
        RetainedClosedMeasurement.requireMetadata(facts,metadata,at(NOW),MACHINE,WORKER);
    }
    private static SavedCheckpointMeasurementCoordinator unmeasuredCoordinator() {
        // Real production runner constructed but never called. No injectable fake runner can mint cache authority.
        return new SavedCheckpointMeasurementCoordinator(
                new WindowsJobSdkMeasurementRunner(() -> { }),new WindowsSavedProofIdentityReader());
    }

    @Test void historicalMetadataKeepsOriginalDriverFactsWithoutTouchingCurrentDriver() throws IOException {
        var facts = ordinaryFacts(); var metadata = new Metadata(facts); require(facts,metadata);
        assertFalse(facts.currentDriverQualified()); assertFalse(facts.grantsWarmAttachment());
        assertEquals(41_000_000,facts.historicalDriver().bytes());
        assertEquals("6755399453430489",facts.historicalDriverIdentity().fileId());
        assertTrue(metadata.statPaths.stream().allMatch(path -> path.equals(Path.of(facts.save().path()))));
        assertTrue(metadata.sourceChecks.contains(facts.sdkFreeze()));
        assertTrue(metadata.sourceChecks.contains(facts.validatorSource()));
        assertTrue(metadata.sourceChecks.containsAll(facts.importedSources()));
        assertTrue(metadata.sourceChecks.contains(facts.canonicalReceipt().reference()));
        assertThrows(UnsupportedOperationException.class,() -> facts.importedSources().clear());
    }

    @Test void saveIdentityDriftBeforeOrDuringSourceChecksRejectsHistoricalFacts() {
        var facts = ordinaryFacts(); var changedBefore = new Metadata(facts);
        changedBefore.observedSave = new FileStatIdentity(facts.saveIdentity().bytes(),
                "281474988852757",facts.saveIdentity().mtimeNs());
        assertThrows(ContractViolationException.class,() -> require(facts,changedBefore));
        var changedDuring = new Metadata(facts); changedDuring.driftAfterSources = true;
        assertThrows(ContractViolationException.class,() -> require(facts,changedDuring));
    }

    @Test void completeInventoryImportsValidatorAndCanonicalReceiptRemainPinned() {
        var facts = ordinaryFacts(); List<ExactRef> required = new ArrayList<>(facts.importedSources());
        required.add(facts.sdkFreeze()); required.add(facts.validatorSource()); required.add(facts.canonicalReceipt().reference());
        for (ExactRef original : required) {
            var metadata = new Metadata(facts); metadata.unavailableSource = original;
            assertThrows(IOException.class,() -> require(facts,metadata),original.path());
        }
    }

    @Test void machineWorkerOriginalDeadlineAndClockBeforeRetentionRejectWithoutRenewal() {
        var facts = ordinaryFacts();
        assertThrows(ContractViolationException.class,() -> RetainedClosedMeasurement.requireMetadata(
                facts,new Metadata(facts),at(NOW),"another-machine",WORKER));
        assertThrows(ContractViolationException.class,() -> RetainedClosedMeasurement.requireMetadata(
                facts,new Metadata(facts),at(NOW),MACHINE,"c".repeat(64)));
        assertThrows(ContractViolationException.class,() -> RetainedClosedMeasurement.requireMetadata(
                facts,new Metadata(facts),at(DEADLINE),MACHINE,WORKER));
        assertThrows(ContractViolationException.class,() -> RetainedClosedMeasurement.requireMetadata(
                facts,new Metadata(facts),at(RETAINED.minusNanos(1)),MACHINE,WORKER));
        assertEquals(DEADLINE,facts.reviewAtUtc());
    }

    @Test void greenJsonAndOrdinaryFactsCannotMintOrRebuildRegisteredCoordinatorContext() throws IOException {
        var coordinator = unmeasuredCoordinator();
        assertFalse(coordinator.hasMeasuredCache());
        assertThrows(ContractViolationException.class,coordinator::requireCurrentCached);
        assertThrows(ContractViolationException.class,coordinator::retainClosedMeasurement);
        // Deliberately unregistered, so it cannot stand in for a context minted by the live measured coordinator.
        var unregistered = RetainedClosedMeasurement.retainFor(coordinator,ordinaryFacts());
        assertThrows(ContractViolationException.class,unregistered::requireHistoricalInputs);
        assertFalse(coordinator.hasMeasuredCache());
        assertEquals(0,RetainedClosedMeasurement.class.getConstructors().length);
        String green = "{\"schema\":\"xar.current-saved-recovery-checkpoint-qualification/v1\","
                +"\"status\":\"ORIGINAL_SDK_SAVED_CHECKPOINT_QUALIFIED\",\"currentDriverQualified\":true}";
        assertThrows(IOException.class,() -> new ObjectMapper().readValue(green,RetainedClosedMeasurement.class));
        RetainedClosedMeasurement parsedNull = new ObjectMapper().readValue("null",RetainedClosedMeasurement.class);
        assertThrows(ContractViolationException.class,() -> coordinator.requireRetainedHistoricalInputs(parsedNull));
    }

    @Test void originalThreadAndClosedStateRejectBeforeUnregisteredContextCanReachMetadata() throws Exception {
        var coordinator = unmeasuredCoordinator();
        var unregistered = RetainedClosedMeasurement.retainFor(coordinator,ordinaryFacts());
        AtomicReference<Throwable> failure = new AtomicReference<>();
        Thread other = new Thread(() -> {
            try { unregistered.requireHistoricalInputs(); }
            catch (IOException | RuntimeException rejected) { failure.set(rejected); }
        });
        other.start(); other.join(5000); assertFalse(other.isAlive());
        assertTrue(failure.get() instanceof ContractViolationException);
        assertTrue(failure.get().getMessage().contains("original owning Java thread"));
        unregistered.close();
        var closed = assertThrows(ContractViolationException.class,unregistered::requireHistoricalInputs);
        assertTrue(closed.getMessage().contains("closed")); assertFalse(coordinator.hasMeasuredCache());
    }
}
