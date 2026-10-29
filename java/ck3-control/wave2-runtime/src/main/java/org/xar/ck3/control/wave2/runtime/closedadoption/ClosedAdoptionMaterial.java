package org.xar.ck3.control.wave2.runtime.closedadoption;

import java.util.Objects;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialAdmissionVerifier;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialSources;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryInput;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** A host rereads sources/current identities before supplying each application phase. */
public record ClosedAdoptionMaterial(ClosedFailureRecoveryInput input, ClosedPartialSources sources,
        RecoveryEvidence publishedEpoch, RecoveryEvidence publishedPrefix, ClosedAdoptionSources business,
        ClosedAdoptionSources.SourceVerifier sourceVerifier, ClosedPartialAdmissionVerifier.OriginalSdkVerifier originalSdk) {
    public ClosedAdoptionMaterial {
        Objects.requireNonNull(input); Objects.requireNonNull(sources); Objects.requireNonNull(publishedEpoch);
        Objects.requireNonNull(publishedPrefix); Objects.requireNonNull(business); Objects.requireNonNull(sourceVerifier); Objects.requireNonNull(originalSdk);
    }
    @FunctionalInterface public interface CurrentSource {
        /** Actual current metadata and cache fresh-stat; never invokes measureOnce implicitly. */
        ClosedAdoptionMaterial current();
    }
}
