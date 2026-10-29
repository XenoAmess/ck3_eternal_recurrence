package org.xar.ck3.control.wave2.prisoners.releasepreview;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.Costs;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.Definition;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;

/** Observed read-only inputs. Available, including Can Send, is never an applied release. */
public sealed interface ReleasePreview12003
        permits ReleasePreview12003.Available, ReleasePreview12003.Unavailable {
    record Available(FrameBinding binding, BigInteger proofEpoch, Definition definition,
                     boolean canSend, Costs costs) implements ReleasePreview12003 {
        public Available {
            Objects.requireNonNull(binding, "binding");
            ReleasePreviewValues12003.unsigned64(proofEpoch, "proof epoch");
            Objects.requireNonNull(definition, "definition");
            Objects.requireNonNull(costs, "costs");
        }
    }

    /** Native reason is retained verbatim, including reasons unknown to this code. */
    record Unavailable(String reason) implements ReleasePreview12003 {
        public Unavailable { StrictJson.text(reason); }
    }
}
