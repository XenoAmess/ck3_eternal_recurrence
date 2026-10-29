package org.xar.ck3.control.wave2.prisoners.negotiatedpreview;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.Costs;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.Definition;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.ReleaseOption;

/** Selected native offer inputs. None of these branches proves a release or payment. */
public sealed interface NegotiatedPreview12003 {
    int MAXIMUM_MASK = (1 << ReleaseOption.values().length) - 1;

    int requestedOptionMaskBits();

    record Available(FrameBinding frame, BigInteger proofEpoch, Definition definition,
            int requestedOptionMaskBits, boolean canSend, Costs costs, Acceptance acceptance)
            implements NegotiatedPreview12003 {
        public Available {
            Objects.requireNonNull(frame, "frame");
            positiveUInt64(proofEpoch);
            Objects.requireNonNull(definition, "definition");
            requestedMask(requestedOptionMaskBits);
            Objects.requireNonNull(costs, "costs");
            Objects.requireNonNull(acceptance, "acceptance");
            StrictJson.require(canSend != (acceptance instanceof NotEvaluatedUnsendable),
                    "CanSend and native acceptance evaluation differ");
        }
    }

    record Unavailable(int requestedOptionMaskBits, String unavailableReason)
            implements NegotiatedPreview12003 {
        public Unavailable {
            requestedMask(requestedOptionMaskBits);
            StrictJson.text(unavailableReason);
            StrictJson.require(!"requested_release_options_not_retained".equals(unavailableReason),
                    "mask mismatch requires its observed mask diagnostic");
        }
    }

    record OptionsNotRetained(int requestedOptionMaskBits, int observedOptionMaskBits)
            implements NegotiatedPreview12003 {
        public OptionsNotRetained {
            requestedMask(requestedOptionMaskBits);
            StrictJson.require(observedOptionMaskBits >= 0 && observedOptionMaskBits <= MAXIMUM_MASK
                    && observedOptionMaskBits != requestedOptionMaskBits,
                    "observed mask must differ from the requested current mask");
        }

        public String unavailableReason() { return "requested_release_options_not_retained"; }
    }

    /** An unevaluated answer has no score or would-accept value; it is not a refusal. */
    sealed interface Acceptance permits NotEvaluatedUnsendable, AutoAccept, NativeAnswer {
        boolean autoAccept();
    }

    record NotEvaluatedUnsendable(boolean autoAccept) implements Acceptance { }

    record AutoAccept() implements Acceptance {
        @Override public boolean autoAccept() { return true; }
        public boolean wouldAcceptNow() { return true; }
    }

    /** Q100000 is a signed native operand, never an acceptance probability. */
    record NativeAnswer(long recipientAcceptanceScoreRaw, AnswerStatus recipientAnswerStatus)
            implements Acceptance {
        public NativeAnswer { Objects.requireNonNull(recipientAnswerStatus, "recipientAnswerStatus"); }
        @Override public boolean autoAccept() { return false; }
        public boolean wouldAcceptNow() { return recipientAnswerStatus != AnswerStatus.REFUSED; }
    }

    enum AnswerStatus {
        ACCEPTED(0), ACCEPTED_ALTERNATE(1), REFUSED(2);
        private final int raw;
        AnswerStatus(int raw) { this.raw = raw; }
        public int raw() { return raw; }
        public static AnswerStatus fromRaw(int raw) {
            return switch (raw) {
                case 0 -> ACCEPTED;
                case 1 -> ACCEPTED_ALTERNATE;
                case 2 -> REFUSED;
                default -> throw new IllegalArgumentException("native answer must be 0, 1 or 2");
            };
        }
    }

    static int releaseOptionMask(List<ReleaseOption> options) {
        StrictJson.require(options != null && !options.isEmpty()
                && options.stream().allMatch(Objects::nonNull)
                && new HashSet<>(options).size() == options.size(),
                "release options must be a nonempty distinct current subset");
        int mask = 0;
        for (ReleaseOption option : options) { mask |= 1 << option.ordinal(); }
        return mask;
    }

    static void requestedMask(int mask) {
        StrictJson.require(mask >= 1 && mask <= MAXIMUM_MASK, "requested current option mask required");
    }

    static void positiveUInt64(BigInteger value) {
        StrictJson.require(value != null && value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0,
                "positive native uint64 required");
    }
}
