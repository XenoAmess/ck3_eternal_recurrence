package org.xar.ck3.control.wave2.prisoners.negotiatedpreview;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.OptionalLong;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;

/** Declared comparison projection of a fully validated source copy, never an action gate. */
public record NegotiatedSourceCopy12004(int sourceOrdinal, boolean selectedQueryCompleted,
        Optional<String> unavailableReason, List<Sample> samples) {
    public NegotiatedSourceCopy12004 {
        StrictJson.require(sourceOrdinal >= 0 && sourceOrdinal < 64, "selected source ordinal outside collection");
        Objects.requireNonNull(unavailableReason, "unavailableReason").ifPresent(StrictJson::text);
        samples = List.copyOf(samples);
        StrictJson.require(samples.size() <= 4, "at most four source samples");
        for (int index = 0; index < samples.size(); index++) {
            StrictJson.require(samples.get(index).sampleIndex() == index, "sample order differs");
        }
    }

    public record QuoteBinding(FrameBinding frame, BigInteger querySequence, BigInteger proofEpoch,
            int sourceOrdinal, int requestedOptionMaskBits) {
        public QuoteBinding {
            Objects.requireNonNull(frame, "frame");
            NegotiatedPreview12003.positiveUInt64(querySequence);
            NegotiatedPreview12003.positiveUInt64(proofEpoch);
            StrictJson.require(sourceOrdinal >= 0 && sourceOrdinal < 64, "selected source ordinal outside collection");
            NegotiatedPreview12003.requestedMask(requestedOptionMaskBits);
        }
    }

    public record SampleFrame(BigInteger nativeRevision, BigInteger querySequence, BigInteger proofEpoch,
            OptionalInt dateRaw, long jailerFullId, long prisonerFullId) {
        public SampleFrame {
            NegotiatedPreview12003.positiveUInt64(nativeRevision);
            NegotiatedPreview12003.positiveUInt64(querySequence);
            NegotiatedPreview12003.positiveUInt64(proofEpoch);
            Objects.requireNonNull(dateRaw, "dateRaw");
            new FrameBinding(nativeRevision, dateRaw.orElse(0), jailerFullId, prisonerFullId);
        }
    }

    public record Sample(int sampleIndex, SampleFrame frame, OptionalInt sourceAnswerRaw,
            OptionalInt nativeAnswerRaw, boolean answerSourceReady, boolean answerEffectsSourceReady,
            Optional<Boolean> nativeAutoAccept, Optional<ScoreCopy> score, Optional<CostCopy> costs) {
        public Sample {
            StrictJson.require(sampleIndex >= 0 && sampleIndex < 4, "source sample index outside bound");
            Objects.requireNonNull(frame, "frame");
            byteAnswer(sourceAnswerRaw);
            byteAnswer(nativeAnswerRaw);
            StrictJson.require(answerSourceReady == sourceAnswerRaw.isPresent()
                    && (!answerEffectsSourceReady || answerSourceReady), "source answer facts differ");
            Objects.requireNonNull(nativeAutoAccept, "nativeAutoAccept");
            Objects.requireNonNull(score, "score");
            Objects.requireNonNull(costs, "costs");
        }
    }

    public record ScoreCopy(OptionalLong projectedQ64, OptionalLong nativeFinalOutputQ64) {
        public ScoreCopy {
            Objects.requireNonNull(projectedQ64, "projectedQ64");
            Objects.requireNonNull(nativeFinalOutputQ64, "nativeFinalOutputQ64");
        }
    }

    public record CostCopy(Optional<List<Long>> projectedQ64, Optional<List<Long>> nativeFinalQ64) {
        public CostCopy {
            projectedQ64 = vector(projectedQ64);
            nativeFinalQ64 = vector(nativeFinalQ64);
        }
    }

    private static Optional<List<Long>> vector(Optional<List<Long>> input) {
        Objects.requireNonNull(input, "cost vector");
        return input.map(rows -> {
            List<Long> result = List.copyOf(rows);
            StrictJson.require(result.size() == 10, "ten cost lanes required");
            return result;
        });
    }

    private static void byteAnswer(OptionalInt input) {
        Objects.requireNonNull(input, "answer byte");
        StrictJson.require(input.isEmpty() || input.getAsInt() >= 0 && input.getAsInt() <= 255,
                "source answer must retain its unsigned byte");
    }
}
