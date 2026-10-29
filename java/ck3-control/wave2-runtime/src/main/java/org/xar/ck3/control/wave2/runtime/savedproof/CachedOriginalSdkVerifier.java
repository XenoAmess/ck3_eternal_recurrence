package org.xar.ck3.control.wave2.runtime.savedproof;

import java.io.IOException;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialAdmissionVerifier;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialEpochProducer;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialSources;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryInput;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryReducer;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.recovery.RecoveryPrerequisiteVerifier;

/** Reuses one actual SDK measurement; it never starts another process or physical read. */
public final class CachedOriginalSdkVerifier implements ClosedPartialAdmissionVerifier.OriginalSdkVerifier {
    private final SavedCheckpointMeasurementCoordinator coordinator;
    public CachedOriginalSdkVerifier(SavedCheckpointMeasurementCoordinator coordinator) {
        this.coordinator = Objects.requireNonNull(coordinator);
    }
    /**
     * Existing integer-only wire domain: integral node implementations are not JSON identities.
     * Full content remains exact; canonical rejects float tokens rather than converting them.
     */
    static boolean sameRawNativeCheckpoint(com.fasterxml.jackson.databind.JsonNode measured,
            com.fasterxml.jackson.databind.JsonNode original) {
        StrictJson.require(measured != null && measured.isObject() && original != null && original.isObject(),
                "two complete raw Native checkpoint objects required");
        return Arrays.equals(StrictJson.canonical(measured), StrictJson.canonical(original));
    }

    @Override public RecoveryPrerequisiteVerifier.Check verifyCurrent(ClosedFailureRecoveryInput input,
            String inputDigest, RecoveryEvidence closedEpoch, RecoveryEvidence settledPrefix, ClosedPartialSources sources) {
        try {
            if (!coordinator.hasMeasuredCache()) {
                return new RecoveryPrerequisiteVerifier.Unavailable("No actual original-SDK measurement has completed in this coordinator");
            }
            SavedCheckpointMeasurement proof = coordinator.requireCurrentCached();
            StrictJson.require(input.machineId().equals(proof.machineId())
                    && input.currentDriver().equals(proof.driver()) && input.currentDriverIdentity().equals(proof.driverIdentity())
                    && input.currentSave().equals(proof.save()) && input.currentSaveIdentity().equals(proof.saveIdentity())
                    && ClosedFailureRecoveryReducer.inputDigest(input).equals(inputDigest), "actual measured current SAVE input binding");
            var measuredCheckpoint = StrictJson.parse(proof.canonicalReceipt().bytes()).get("checkpoint");
            var rawSavedCheckpoint = StrictJson.parse(input.rawState().bytes()).get("actual_saved_checkpoint");
            StrictJson.require(measuredCheckpoint != null && measuredCheckpoint.isObject()
                    && sameRawNativeCheckpoint(measuredCheckpoint, rawSavedCheckpoint),
                    "same complete raw Native checkpoint in current SDK measurement and original Queue state");
            ClosedPartialEpochProducer.Produced produced = ClosedPartialEpochProducer.compose(input, sources);
            StrictJson.require(Arrays.equals(closedEpoch.bytes(), produced.epochBytes())
                    && Arrays.equals(settledPrefix.bytes(), produced.prefixBytes()), "same source-bound closed/prefix producer output");
            return new RecoveryPrerequisiteVerifier.Verified(inputDigest, closedEpoch.reference(), settledPrefix.reference(),
                proof.canonicalCheckpointProof(), proof.validatorSource(), proof.checkpointDigest(), proof.driver(), proof.driverIdentity(),
                proof.save(), proof.saveIdentity(), produced.epoch().settledCycles(), produced.epoch().unknownSequence());
        } catch (IOException error) {
            return new RecoveryPrerequisiteVerifier.Unavailable("Current measured SDK cache metadata unavailable: " + error.getMessage());
        } catch (ContractViolationException error) {
            return new RecoveryPrerequisiteVerifier.Rejected(error.getMessage());
        }
    }
}
