package org.xar.ck3.control.recovery;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;

/** Original metadata and current file identities, never large persistence bodies. */
public record ClosedFailureRecoveryInput(
        String machineId, String observedAtUtc, RecoveryEvidence predecessor,
        RecoveryEvidence savedBasis, RecoveryEvidence priorQualification,
        RecoveryEvidence fullRequest, RecoveryEvidence failedFull,
        RecoveryEvidence autoRequest, RecoveryEvidence failedAuto,
        RecoveryEvidence rawState, RecoveryEvidence rawGovernance, RecoveryEvidence actualNext,
        ExactRef currentDriver, FileStatIdentity currentDriverIdentity,
        ExactRef currentSave, FileStatIdentity currentSaveIdentity) {
    public ClosedFailureRecoveryInput {
        StrictJson.text(machineId); StrictJson.utc(observedAtUtc);
        Objects.requireNonNull(predecessor); Objects.requireNonNull(savedBasis);
        Objects.requireNonNull(priorQualification); Objects.requireNonNull(fullRequest);
        Objects.requireNonNull(failedFull); Objects.requireNonNull(autoRequest); Objects.requireNonNull(failedAuto);
        Objects.requireNonNull(rawState); Objects.requireNonNull(rawGovernance); Objects.requireNonNull(actualNext);
        Objects.requireNonNull(currentDriver); Objects.requireNonNull(currentDriverIdentity);
        Objects.requireNonNull(currentSave); Objects.requireNonNull(currentSaveIdentity);
        StrictJson.require(currentDriverIdentity.bytes().longValueExact() == currentDriver.bytes()
                && currentSaveIdentity.bytes().longValueExact() == currentSave.bytes(), "current file size identities");
    }

    public List<ExactRef> metadataSources() {
        return List.of(predecessor.reference(), savedBasis.reference(), priorQualification.reference(),
                fullRequest.reference(), failedFull.reference(), autoRequest.reference(), failedAuto.reference(),
                rawState.reference(), rawGovernance.reference(), actualNext.reference());
    }
}
