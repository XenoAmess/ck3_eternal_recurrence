package org.xar.ck3.control.recovery;

import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Port implemented only by the source-qualified admission/original-SDK adapter.
 * A JSON GREEN flag or construction of Verified is not an authority provider.
 * The original writer must call this same fixed provider again while locked.
 */
@FunctionalInterface
public interface RecoveryPrerequisiteVerifier {
    Check verify(ClosedFailureRecoveryInput input, String exactInputDigest);

    sealed interface Check permits Verified, Unavailable, Rejected { }
    record Unavailable(String reason) implements Check {
        public Unavailable { StrictJson.text(reason); }
    }
    record Rejected(String reason) implements Check {
        public Rejected { StrictJson.text(reason); }
    }

    /** Result of actual closed-epoch/prefix and original SDK verification, not its replacement. */
    record Verified(String inputDigest, ExactRef closedEpochProof, ExactRef settledPrefixProof,
            ExactRef canonicalCheckpointProof, ExactRef validatorSource, String checkpointDigest,
            ExactRef driver, FileStatIdentity driverIdentity, ExactRef save, FileStatIdentity saveIdentity,
            long settledPrefixCycles, long unknownSequence) implements Check {
        public Verified {
            sha(inputDigest); sha(checkpointDigest);
            Objects.requireNonNull(closedEpochProof); Objects.requireNonNull(settledPrefixProof);
            Objects.requireNonNull(canonicalCheckpointProof); Objects.requireNonNull(validatorSource);
            Objects.requireNonNull(driver); Objects.requireNonNull(driverIdentity);
            Objects.requireNonNull(save); Objects.requireNonNull(saveIdentity);
            StrictJson.safe(settledPrefixCycles, 1); StrictJson.safe(unknownSequence, 1);
        }
        private static void sha(String value) {
            StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "exact SHA256 required");
        }
    }

    static RecoveryPrerequisiteVerifier unavailable() {
        return (input, digest) -> new Unavailable(
                "No source-qualified closed-epoch/prefix and current original-SDK checkpoint provider installed");
    }
}
