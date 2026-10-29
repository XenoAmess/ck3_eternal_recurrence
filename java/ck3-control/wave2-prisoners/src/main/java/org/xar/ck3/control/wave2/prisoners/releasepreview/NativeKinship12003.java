package org.xar.ck3.control.wave2.prisoners.releasepreview;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;

/** Two independent native family predicates; neither is inferred from dynasty identity. */
public sealed interface NativeKinship12003
        permits NativeKinship12003.Missing, NativeKinship12003.Unavailable, NativeKinship12003.Available {
    record Missing() implements NativeKinship12003 { }
    record Unavailable(String reason) implements NativeKinship12003 {
        public Unavailable { StrictJson.text(reason); }
    }
    record Available(FrameBinding binding, BigInteger proofEpoch, int sourceOrdinal,
                     boolean closeFamily, boolean closeOrExtendedFamily) implements NativeKinship12003 {
        public Available {
            Objects.requireNonNull(binding, "binding");
            ReleasePreviewValues12003.unsigned64(proofEpoch, "kinship proof epoch");
            StrictJson.require(sourceOrdinal >= 0 && sourceOrdinal <= 63, "kinship ordinal outside 0..63");
        }
    }
}
