package org.xar.ck3.control.wave2.prisoners.negotiatedpreview;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.OptionalLong;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedPreview12003.AutoAccept;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedPreview12003.NativeAnswer;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedSourceCopy12004.QuoteBinding;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003;

/** Current native result joined to optional copied-source diagnostics; no action is selected. */
public sealed interface NegotiatedQuoteResult12004 {
    enum Match { MATCH, DIFFERENT, UNKNOWN }

    record Comparison(int sampleIndex, Match nativeCostsMatchQuote, Match nativeAnswerMatchesQuote,
            Match nativeScoreMatchesQuote, Match nativeAutoAcceptMatchesQuote,
            Match costProjectionMatchesNativeCopy, Match answerProjectionMatchesNativeCopy,
            Match scoreProjectionMatchesNativeCopy, boolean sourceAnswerReady,
            boolean sourceAnswerEffectsReady) {
        public Comparison {
            StrictJson.require(sampleIndex >= 0 && sampleIndex < 4, "source comparison sample index");
            Objects.requireNonNull(nativeCostsMatchQuote, "nativeCostsMatchQuote");
            Objects.requireNonNull(nativeAnswerMatchesQuote, "nativeAnswerMatchesQuote");
            Objects.requireNonNull(nativeScoreMatchesQuote, "nativeScoreMatchesQuote");
            Objects.requireNonNull(nativeAutoAcceptMatchesQuote, "nativeAutoAcceptMatchesQuote");
            Objects.requireNonNull(costProjectionMatchesNativeCopy, "costProjectionMatchesNativeCopy");
            Objects.requireNonNull(answerProjectionMatchesNativeCopy, "answerProjectionMatchesNativeCopy");
            Objects.requireNonNull(scoreProjectionMatchesNativeCopy, "scoreProjectionMatchesNativeCopy");
        }
    }

    record Available(QuoteBinding binding, NegotiatedPreview12003.Available nativeResult,
            Optional<NegotiatedSourceCopy12004> source, List<Comparison> comparisons)
            implements NegotiatedQuoteResult12004 {
        public Available {
            Objects.requireNonNull(binding, "binding");
            Objects.requireNonNull(nativeResult, "nativeResult");
            Objects.requireNonNull(source, "source");
            comparisons = List.copyOf(comparisons);
        }
    }

    record Unavailable(QuoteBinding binding, String unavailableReason, boolean sourcePresent)
            implements NegotiatedQuoteResult12004 {
        public Unavailable {
            Objects.requireNonNull(binding, "binding");
            StrictJson.text(unavailableReason);
        }
    }

    static NegotiatedQuoteResult12004 consume(NegotiatedPreview12003 preview,
            Optional<NegotiatedSourceCopy12004> source, QuoteBinding binding) {
        Objects.requireNonNull(preview, "preview");
        Objects.requireNonNull(source, "source");
        Objects.requireNonNull(binding, "binding");
        StrictJson.require(preview.requestedOptionMaskBits() == binding.requestedOptionMaskBits(), "quote requested mask differs");
        source.ifPresent(copy -> {
            StrictJson.require(copy.sourceOrdinal() == binding.sourceOrdinal(), "quote source row differs");
            for (var sample : copy.samples()) {
                var frame = sample.frame();
                StrictJson.require(frame.nativeRevision().equals(binding.frame().nativeRevision())
                        && frame.querySequence().equals(binding.querySequence())
                        && frame.proofEpoch().equals(binding.proofEpoch())
                        && frame.jailerFullId() == binding.frame().playerCharacterId()
                        && frame.prisonerFullId() == binding.frame().prisonerCharacterId()
                        && (frame.dateRaw().isEmpty() || frame.dateRaw().getAsInt() == binding.frame().dateRaw()),
                        "quote copied source differs from the full current frame");
            }
        });
        if (preview instanceof NegotiatedPreview12003.Unavailable unavailable) {
            return new Unavailable(binding, unavailable.unavailableReason(), source.isPresent());
        }
        if (preview instanceof NegotiatedPreview12003.OptionsNotRetained unavailable) {
            return new Unavailable(binding, unavailable.unavailableReason(), source.isPresent());
        }
        var available = (NegotiatedPreview12003.Available) preview;
        StrictJson.require(available.frame().equals(binding.frame()) && available.proofEpoch().equals(binding.proofEpoch()),
                "native negotiated quote differs from full current frame");
        List<Long> nativeCosts = available.costs().entries().stream().map(ReleasePreviewValues12003.CostEntry::raw).toList();
        OptionalInt nativeAnswer = available.acceptance() instanceof NativeAnswer answer
                ? OptionalInt.of(answer.recipientAnswerStatus().raw()) : OptionalInt.empty();
        OptionalLong nativeScore = available.acceptance() instanceof NativeAnswer answer
                ? OptionalLong.of(answer.recipientAcceptanceScoreRaw()) : OptionalLong.empty();
        List<Comparison> comparisons = new ArrayList<>();
        source.ifPresent(copy -> {
            for (var sample : copy.samples()) {
                Optional<List<Long>> copiedCosts = sample.costs().flatMap(NegotiatedSourceCopy12004.CostCopy::nativeFinalQ64);
                Optional<List<Long>> projectedCosts = sample.costs().flatMap(NegotiatedSourceCopy12004.CostCopy::projectedQ64);
                OptionalLong copiedScore = sample.score().map(NegotiatedSourceCopy12004.ScoreCopy::nativeFinalOutputQ64).orElse(OptionalLong.empty());
                OptionalLong projectedScore = sample.score().map(NegotiatedSourceCopy12004.ScoreCopy::projectedQ64).orElse(OptionalLong.empty());
                comparisons.add(new Comparison(sample.sampleIndex(), match(copiedCosts, Optional.of(nativeCosts)),
                        match(sample.nativeAnswerRaw(), nativeAnswer), match(copiedScore, nativeScore),
                        match(sample.nativeAutoAccept(), Optional.of(available.acceptance().autoAccept())),
                        match(projectedCosts, copiedCosts), match(sample.sourceAnswerRaw(), sample.nativeAnswerRaw()),
                        match(projectedScore, copiedScore), sample.answerSourceReady(), sample.answerEffectsSourceReady()));
            }
        });
        return new Available(binding, available, source, comparisons);
    }

    static byte[] encode(NegotiatedQuoteResult12004 result) { return StrictJson.canonical(toJson(result), 16_384); }

    static ObjectNode toJson(NegotiatedQuoteResult12004 result) {
        Objects.requireNonNull(result, "result");
        ObjectNode out = StrictJson.object().put("schema", "prisoner-negotiated-quote-result-12004")
                .put("action_selected", false).put("material_result", false);
        QuoteBinding binding = result instanceof Available available ? available.binding() : ((Unavailable) result).binding();
        ObjectNode frame = out.putObject("binding");
        frame.put("native_revision", binding.frame().nativeRevision()).put("query_sequence", binding.querySequence())
                .put("proof_epoch", binding.proofEpoch()).put("date_raw", binding.frame().dateRaw())
                .put("player_full_id", binding.frame().playerCharacterId()).put("prisoner_full_id", binding.frame().prisonerCharacterId())
                .put("source_ordinal", binding.sourceOrdinal()).put("requested_option_mask_bits", binding.requestedOptionMaskBits());
        if (result instanceof Unavailable unavailable) {
            out.put("status", "unavailable").put("unavailable_reason", unavailable.unavailableReason())
                    .put("source_present", unavailable.sourcePresent());
            out.putNull("native_result");
            out.putArray("copied_source_comparisons");
            return out;
        }
        Available available = (Available) result;
        out.put("status", "available").put("source_present", available.source().isPresent());
        out.putNull("unavailable_reason");
        if (available.source().isPresent()) {
            var source = available.source().orElseThrow();
            out.put("source_query_completed", source.selectedQueryCompleted());
            if (source.unavailableReason().isPresent()) { out.put("source_unavailable_reason", source.unavailableReason().orElseThrow()); }
            else { out.putNull("source_unavailable_reason"); }
        } else { out.putNull("source_query_completed").putNull("source_unavailable_reason"); }
        var preview = available.nativeResult();
        ObjectNode nativeResult = out.putObject("native_result");
        nativeResult.put("can_send", preview.canSend()).put("answer_evaluated", preview.acceptance() instanceof NativeAnswer)
                .put("auto_accept", preview.acceptance().autoAccept()).put("score_is_probability", false);
        if (preview.acceptance() instanceof NativeAnswer answer) {
            nativeResult.put("would_accept_now", answer.wouldAcceptNow()).put("recipient_answer_status_raw", answer.recipientAnswerStatus().raw())
                    .put("recipient_acceptance_score_raw", answer.recipientAcceptanceScoreRaw());
        } else {
            if (preview.acceptance() instanceof AutoAccept) { nativeResult.put("would_accept_now", true); }
            else { nativeResult.putNull("would_accept_now"); }
            nativeResult.putNull("recipient_answer_status_raw").putNull("recipient_acceptance_score_raw");
        }
        nativeResult.set("costs", ReleasePreviewValues12003.writeCosts(preview.costs()));
        var comparisons = out.putArray("copied_source_comparisons");
        for (Comparison item : available.comparisons()) {
            ObjectNode row = comparisons.addObject().put("sample_index", item.sampleIndex())
                    .put("source_answer_ready", item.sourceAnswerReady()).put("source_answer_effects_ready", item.sourceAnswerEffectsReady());
            writeMatch(row, "native_costs_match_quote", item.nativeCostsMatchQuote());
            writeMatch(row, "native_answer_matches_quote", item.nativeAnswerMatchesQuote());
            writeMatch(row, "native_score_matches_quote", item.nativeScoreMatchesQuote());
            writeMatch(row, "native_auto_accept_matches_quote", item.nativeAutoAcceptMatchesQuote());
            writeMatch(row, "cost_projection_matches_native_copy", item.costProjectionMatchesNativeCopy());
            writeMatch(row, "answer_projection_matches_native_copy", item.answerProjectionMatchesNativeCopy());
            writeMatch(row, "score_projection_matches_native_copy", item.scoreProjectionMatchesNativeCopy());
        }
        return out;
    }

    private static <T> Match match(Optional<T> left, Optional<T> right) {
        return left.isEmpty() || right.isEmpty() ? Match.UNKNOWN : left.get().equals(right.get()) ? Match.MATCH : Match.DIFFERENT;
    }
    private static Match match(OptionalLong left, OptionalLong right) {
        return left.isEmpty() || right.isEmpty() ? Match.UNKNOWN : left.getAsLong() == right.getAsLong() ? Match.MATCH : Match.DIFFERENT;
    }
    private static Match match(OptionalInt left, OptionalInt right) {
        return left.isEmpty() || right.isEmpty() ? Match.UNKNOWN : left.getAsInt() == right.getAsInt() ? Match.MATCH : Match.DIFFERENT;
    }
    private static void writeMatch(ObjectNode out, String key, Match value) {
        if (value == Match.UNKNOWN) { out.putNull(key); }
        else { out.put(key, value == Match.MATCH); }
    }
}
