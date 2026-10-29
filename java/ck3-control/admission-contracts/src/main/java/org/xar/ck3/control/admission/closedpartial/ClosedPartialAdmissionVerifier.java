package org.xar.ck3.control.admission.closedpartial;

import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryInput;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryReducer;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.recovery.RecoveryPrerequisiteVerifier;

/** Host-installed fixed adapter into the sole recovery proof model. Never grants ready. */
public final class ClosedPartialAdmissionVerifier implements RecoveryPrerequisiteVerifier {
    /**
     * Must execute the measured original SDK predicate against current Driver/SAVE,
     * verify the source classifier and complete capture/Task closures, and bind all
     * supplied references. Reading an old GREEN JSON or constructing Verified is insufficient.
     * The original writer invokes this same adapter again while holding its existing lock.
     */
    @FunctionalInterface
    public interface OriginalSdkVerifier {
        Check verifyCurrent(ClosedFailureRecoveryInput input, String inputDigest,
                RecoveryEvidence closedEpoch, RecoveryEvidence settledPrefix, ClosedPartialSources sources);
    }
    private final ClosedPartialSources sources;
    private final RecoveryEvidence epoch;
    private final RecoveryEvidence prefix;
    private final OriginalSdkVerifier originalSdk;
    public ClosedPartialAdmissionVerifier(ClosedPartialSources sources, RecoveryEvidence epoch,
            RecoveryEvidence prefix, OriginalSdkVerifier originalSdk) {
        this.sources = Objects.requireNonNull(sources); this.epoch = Objects.requireNonNull(epoch);
        this.prefix = Objects.requireNonNull(prefix); this.originalSdk = Objects.requireNonNull(originalSdk);
    }
    public static OriginalSdkVerifier unavailableOriginalSdk() {
        return (input, digest, epoch, prefix, sources) -> new Unavailable(
                "UNAVAILABLE: current original-SDK canonical SAVE/prefix/capture validation has not actually executed");
    }
    @Override public Check verify(ClosedFailureRecoveryInput input, String exactInputDigest) {
        try {
            org.xar.ck3.control.contracts.StrictJson.require(
                    ClosedFailureRecoveryReducer.inputDigest(input).equals(exactInputDigest), "same exact recovery input digest");
            ClosedPartialEpochProducer.Produced produced = ClosedPartialEpochProducer.compose(input, sources);
            org.xar.ck3.control.contracts.StrictJson.require(Arrays.equals(produced.epochBytes(), epoch.bytes())
                    && Arrays.equals(produced.prefixBytes(), prefix.bytes()), "exact published new epoch/prefix producer bytes");
            Check result = Objects.requireNonNull(originalSdk.verifyCurrent(input, exactInputDigest, epoch, prefix, sources));
            if (result instanceof Verified proof) {
                org.xar.ck3.control.contracts.StrictJson.require(proof.inputDigest().equals(exactInputDigest)
                        && proof.closedEpochProof().equals(epoch.reference())
                        && proof.settledPrefixProof().equals(prefix.reference())
                        && proof.settledPrefixCycles() == produced.epoch().settledCycles()
                        && proof.unknownSequence() == produced.epoch().unknownSequence(), "sole actual original SDK proof source binding");
            }
            return result;
        } catch (ContractViolationException error) {
            return new Rejected(error.getMessage());
        }
    }
}
