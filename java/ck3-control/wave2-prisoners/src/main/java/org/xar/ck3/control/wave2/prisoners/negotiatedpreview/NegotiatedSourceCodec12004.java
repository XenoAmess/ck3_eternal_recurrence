package org.xar.ck3.control.wave2.prisoners.negotiatedpreview;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedSourceCopy12004.CostCopy;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedSourceCopy12004.QuoteBinding;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedSourceCopy12004.Sample;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedSourceCopy12004.SampleFrame;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedSourceCopy12004.ScoreCopy;

/** Full source validation precedes the consumer's small declared diagnostic projection. */
public final class NegotiatedSourceCodec12004 {
    public static final String EXECUTABLE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    public static final int MAXIMUM_BYTES = 1_048_576;
    private static final Set<String> TOP = Set.of("schema", "schema_version", "source_ordinal", "quote_kind",
            "selected_query_completed", "unavailable_reason", "read_only", "native_callbacks_added", "samples");
    private static final Set<String> FRAME = Set.of("executable_sha256", "module_base", "native_revision", "query_sequence",
            "proof_epoch", "date_raw", "jailer_full_id", "prisoner_full_id", "recipient_full_id", "definition_identity",
            "interaction_context_identity", "original_scope_identity", "roles_verified_in_owned_context", "same_frame_confirmed");
    private static final Set<String> SAMPLE = Set.of("sample_index", "frame", "copied_at_existing_query_call",
            "source_answer_raw_u8", "native_answer_raw_u8", "answer_source_ready", "answer_effects_source_ready",
            "source_auto_accept", "native_auto_accept", "recipient_score", "actor_on_send_costs");
    private static final Set<String> SCORE = Set.of("producer_rva", "score_block_identity", "base_q64", "modifiers_data_identity",
            "modifier_count_raw_i32", "raw_inputs_complete", "numeric_source_ready", "projected_q64", "native_getter_called",
            "native_getter_returned_output_pointer", "native_final_output_q64", "projected_value_matches_native_final",
            "unavailable_reason", "ordered_modifier_occurrences");
    private static final Set<String> ROW = Set.of("native_occurrence_index", "stored_receiver_identity", "vtable_identity",
            "slot30_target_identity", "raw_receiver_ready");
    private static final Set<String> COST = Set.of("cost_block_identity", "numeric_source_ready", "native_getter_called",
            "clamp_nonnegative_raw_u8", "round_raw_u8", "projected_q64", "native_final_q64", "original_output_copied",
            "original_output_q64", "unavailable_reason", "lanes");
    private static final Set<String> LANE = Set.of("lane_index", "lane_identity", "mode_c0_i32", "raw_temp_q64", "branch", "unavailable_reason");

    private NegotiatedSourceCodec12004() { }

    public static NegotiatedSourceCopy12004 decode(byte[] raw, QuoteBinding binding) {
        return decode(StrictJson.parse(raw, MAXIMUM_BYTES), binding);
    }

    /** Available ordinary quote operands are joined to the copied final sample, never inferred from a pointer. */
    public record OrdinaryQuoteJoin(long payerCharacterId, int recipientAnswerStatusRaw, long recipientAcceptanceRaw) {
        public OrdinaryQuoteJoin {
            StrictJson.require(payerCharacterId > 0 && payerCharacterId < 0xffff_ffffL
                    && recipientAnswerStatusRaw >= 0 && recipientAnswerStatusRaw <= 2, "actual ordinary quote operands required");
        }
    }
    /** An ordinary ransom has no negotiated release mask. */
    public record OrdinaryQuoteBinding(
            org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding frame,
            BigInteger querySequence, BigInteger proofEpoch, int sourceOrdinal) {
        public OrdinaryQuoteBinding {
            java.util.Objects.requireNonNull(frame);
            NegotiatedPreview12003.positiveUInt64(querySequence); NegotiatedPreview12003.positiveUInt64(proofEpoch);
            StrictJson.require(sourceOrdinal >= 0 && sourceOrdinal < 64, "selected source ordinal outside collection");
        }
    }
    private record SourceBinding(
            org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding frame,
            BigInteger querySequence, BigInteger proofEpoch, int sourceOrdinal) { }
    /** Ordinary ransom and negotiated release share this one full source validator. */
    public static NegotiatedSourceCopy12004 decodeOrdinary(JsonNode raw, OrdinaryQuoteBinding binding,
            Optional<OrdinaryQuoteJoin> existingQuote) {
        java.util.Objects.requireNonNull(binding);
        return decode(raw, new SourceBinding(binding.frame(), binding.querySequence(), binding.proofEpoch(), binding.sourceOrdinal()),
                true, java.util.Objects.requireNonNull(existingQuote));
    }
    /** Validates every strict source field; only comparison operands enter the domain projection. */
    public static NegotiatedSourceCopy12004 decode(JsonNode raw, QuoteBinding binding) {
        java.util.Objects.requireNonNull(binding);
        return decode(raw, new SourceBinding(binding.frame(), binding.querySequence(), binding.proofEpoch(), binding.sourceOrdinal()), false, Optional.empty());
    }
    private static NegotiatedSourceCopy12004 decode(JsonNode raw, SourceBinding binding,
            boolean ordinary, Optional<OrdinaryQuoteJoin> existingQuote) {
        java.util.Objects.requireNonNull(binding, "binding");
        ObjectNode source = StrictJson.object(raw, TOP);
        exactText(source.get("schema"), "prisoner-selected-quote-source-12004");
        equal(source.get("schema_version"), 1);
        equal(source.get("source_ordinal"), binding.sourceOrdinal());
        exactText(source.get("quote_kind"), ordinary ? "ordinary_ransom" : "negotiated_preview");
        boolean completed = bool(source.get("selected_query_completed"));
        Optional<String> reason = reason(source.get("unavailable_reason"));
        StrictJson.trueValue(source.get("read_only"));
        equal(source.get("native_callbacks_added"), 0);
        JsonNode inputs = array(source.get("samples"), 4);
        List<Sample> samples = new ArrayList<>();
        for (int index = 0; index < inputs.size(); index++) {
            ObjectNode sample = StrictJson.object(inputs.get(index), SAMPLE);
            equal(sample.get("sample_index"), index);
            ObjectNode frame = StrictJson.object(sample.get("frame"), FRAME);
            exactText(frame.get("executable_sha256"), EXECUTABLE_SHA256);
            equal(frame.get("native_revision"), binding.frame().nativeRevision());
            equal(frame.get("query_sequence"), binding.querySequence());
            equal(frame.get("proof_epoch"), binding.proofEpoch());
            equal(frame.get("jailer_full_id"), binding.frame().playerCharacterId());
            equal(frame.get("prisoner_full_id"), binding.frame().prisonerCharacterId());
            OptionalLong copiedDate = nullableLong(frame.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE);
            StrictJson.require(copiedDate.isEmpty() || copiedDate.getAsLong() == binding.frame().dateRaw(), "copied source date differs");
            BigInteger module = pointer(frame.get("module_base"));
            BigInteger definition = pointer(frame.get("definition_identity"));
            BigInteger context = pointer(frame.get("interaction_context_identity"));
            BigInteger scope = pointer(frame.get("original_scope_identity"));
            OptionalLong recipient = nullableLong(frame.get("recipient_full_id"), 0, 0xffff_ffffL);
            boolean roles = bool(frame.get("roles_verified_in_owned_context"));
            boolean sameFrame = bool(frame.get("same_frame_confirmed"));
            boolean ready = copiedDate.isPresent() && roles && sameFrame && module.signum() > 0
                    && definition.signum() > 0 && context.signum() > 0 && scope.signum() > 0;
            if (roles) {
                StrictJson.require(recipient.isPresent() && recipient.getAsLong() >= 1 && recipient.getAsLong() <= 0xffff_fffeL
                        && scope.equals(context.add(BigInteger.valueOf(8)))
                        && (ordinary || recipient.getAsLong() == binding.frame().prisonerCharacterId()), "owned source role scope differs");
            }
            StrictJson.trueValue(sample.get("copied_at_existing_query_call"));
            OptionalInt sourceAnswer = byteValue(sample.get("source_answer_raw_u8"));
            OptionalInt nativeAnswer = byteValue(sample.get("native_answer_raw_u8"));
            boolean answerReady = bool(sample.get("answer_source_ready"));
            boolean effectsReady = bool(sample.get("answer_effects_source_ready"));
            Optional<Boolean> sourceAuto = nullableBool(sample.get("source_auto_accept"));
            Optional<Boolean> nativeAuto = nullableBool(sample.get("native_auto_accept"));
            StrictJson.require(answerReady == sourceAnswer.isPresent() && (!answerReady || ready)
                    && (!effectsReady || answerReady) && (sourceAuto.isEmpty() || ready), "source answer qualification differs");
            Optional<ScoreCopy> score = sample.get("recipient_score").isNull() ? Optional.empty()
                    : Optional.of(readScore(sample.get("recipient_score"), definition, ready));
            StrictJson.require(!ordinary || sample.get("actor_on_send_costs").isNull(), "ordinary ransom has no actor on-send cost capture");
            Optional<CostCopy> costs = sample.get("actor_on_send_costs").isNull() ? Optional.empty()
                    : Optional.of(readCosts(sample.get("actor_on_send_costs"), definition, roles, ready));
            OptionalInt date = copiedDate.isEmpty() ? OptionalInt.empty() : OptionalInt.of((int) copiedDate.getAsLong());
            SampleFrame sampleFrame = new SampleFrame(binding.frame().nativeRevision(), binding.querySequence(), binding.proofEpoch(),
                    date, binding.frame().playerCharacterId(), binding.frame().prisonerCharacterId());
            samples.add(new Sample(index, sampleFrame, sourceAnswer, nativeAnswer, answerReady, effectsReady, nativeAuto, score, costs));
        }
        if (existingQuote.isPresent()) {
            StrictJson.require(ordinary && completed, "available ordinary quote needs the completed original capture");
            if (!inputs.isEmpty()) {
                JsonNode last = inputs.get(inputs.size() - 1);
                OrdinaryQuoteJoin quote = existingQuote.orElseThrow();
                JsonNode recipient = last.get("frame").get("recipient_full_id");
                StrictJson.require(recipient.isNull() || StrictJson.integer(recipient, 1, 0xffff_fffeL) == quote.payerCharacterId(),
                        "copied final recipient differs from current ordinary payer");
                JsonNode answer = last.get("native_answer_raw_u8");
                StrictJson.require(answer.isNull() || StrictJson.integer(answer, 0, 255) == quote.recipientAnswerStatusRaw(),
                        "copied final native answer differs from current ordinary quote");
                JsonNode score = last.get("recipient_score");
                if (!score.isNull()) {
                    JsonNode output = score.get("native_final_output_q64");
                    StrictJson.require(output.isNull() || StrictJson.integer(output, Long.MIN_VALUE, Long.MAX_VALUE) == quote.recipientAcceptanceRaw(),
                            "copied native getter output differs from current ordinary quote");
                }
            }
        }
        return new NegotiatedSourceCopy12004(binding.sourceOrdinal(), completed, reason, samples);
    }

    private static ScoreCopy readScore(JsonNode raw, BigInteger definition, boolean ready) {
        ObjectNode score = StrictJson.object(raw, SCORE);
        equal(score.get("producer_rva"), 0x3761780);
        BigInteger block = pointer(score.get("score_block_identity"));
        StrictJson.require(definition.signum() == 0 || block.equals(definition.add(BigInteger.valueOf(0x1918))), "recipient source score block differs");
        OptionalLong base = q64(score.get("base_q64"));
        OptionalLong projected = q64(score.get("projected_q64"));
        OptionalLong nativeFinal = q64(score.get("native_final_output_q64"));
        Optional<BigInteger> data = nullablePointer(score.get("modifiers_data_identity"));
        OptionalLong count = nullableLong(score.get("modifier_count_raw_i32"), Integer.MIN_VALUE, Integer.MAX_VALUE);
        boolean complete = bool(score.get("raw_inputs_complete"));
        boolean numeric = bool(score.get("numeric_source_ready"));
        boolean called = bool(score.get("native_getter_called"));
        boolean returnedPointer = bool(score.get("native_getter_returned_output_pointer"));
        Optional<Boolean> reportedMatch = nullableBool(score.get("projected_value_matches_native_final"));
        Optional<String> unavailable = reason(score.get("unavailable_reason"));
        JsonNode rows = array(score.get("ordered_modifier_occurrences"), 4096);
        boolean allReceiversReady = true;
        for (int index = 0; index < rows.size(); index++) {
            ObjectNode row = StrictJson.object(rows.get(index), ROW);
            equal(row.get("native_occurrence_index"), index);
            Optional<BigInteger> receiver = nullablePointer(row.get("stored_receiver_identity"));
            Optional<BigInteger> vtable = nullablePointer(row.get("vtable_identity"));
            Optional<BigInteger> target = nullablePointer(row.get("slot30_target_identity"));
            boolean receiverReady = bool(row.get("raw_receiver_ready"));
            allReceiversReady &= receiverReady;
            StrictJson.require(!receiverReady || positive(receiver) && positive(vtable) && positive(target), "ready source modifier lacks receiver");
        }
        if (complete) {
            StrictJson.require(base.isPresent() && data.isPresent() && count.isPresent() && count.getAsLong() >= 0
                    && count.getAsLong() <= 4096 && rows.size() == count.getAsLong() && allReceiversReady,
                    "complete source modifiers differ");
        }
        StrictJson.require(numeric == projected.isPresent(), "score source numeric/null differs");
        if (numeric) {
            StrictJson.require(ready && complete && count.isPresent() && count.getAsLong() == 0
                    && base.equals(projected) && unavailable.isEmpty(), "source score numeric qualification differs");
        }
        StrictJson.require(!returnedPointer || called, "source getter pointer without call");
        StrictJson.require(nativeFinal.isEmpty() || called && returnedPointer, "source getter output without returned pointer");
        Optional<Boolean> expectedMatch = projected.isEmpty() || nativeFinal.isEmpty() ? Optional.empty()
                : Optional.of(projected.getAsLong() == nativeFinal.getAsLong());
        StrictJson.require(reportedMatch.equals(expectedMatch), "separate source score match differs");
        return new ScoreCopy(projected, nativeFinal);
    }

    private static CostCopy readCosts(JsonNode raw, BigInteger definition, boolean roles, boolean ready) {
        ObjectNode cost = StrictJson.object(raw, COST);
        BigInteger block = pointer(cost.get("cost_block_identity"));
        StrictJson.require(!roles || block.equals(definition.add(BigInteger.valueOf(0x40))), "source actor cost block differs");
        boolean numeric = bool(cost.get("numeric_source_ready"));
        bool(cost.get("native_getter_called"));
        boolean copied = bool(cost.get("original_output_copied"));
        OptionalInt clamp = byteValue(cost.get("clamp_nonnegative_raw_u8"));
        OptionalInt rounding = byteValue(cost.get("round_raw_u8"));
        Optional<List<Long>> projected = vector(cost.get("projected_q64"));
        Optional<List<Long>> nativeFinal = vector(cost.get("native_final_q64"));
        Optional<List<Long>> original = vector(cost.get("original_output_q64"));
        Optional<String> unavailable = reason(cost.get("unavailable_reason"));
        StrictJson.require(copied == original.isPresent(), "source original cost copy/null differs");
        JsonNode lanes = array(cost.get("lanes"), 10);
        StrictJson.require(lanes.size() == 10, "ten source cost lanes required");
        List<OptionalLong> rawTemps = new ArrayList<>();
        for (int index = 0; index < lanes.size(); index++) {
            ObjectNode lane = StrictJson.object(lanes.get(index), LANE);
            equal(lane.get("lane_index"), index);
            equal(lane.get("lane_identity"), block.add(BigInteger.valueOf(0x40L + index * 0xf0L)));
            nullableLong(lane.get("mode_c0_i32"), Integer.MIN_VALUE, Integer.MAX_VALUE);
            rawTemps.add(q64(lane.get("raw_temp_q64")));
            StrictJson.text(lane.get("branch"));
            reason(lane.get("unavailable_reason"));
        }
        StrictJson.require(numeric == projected.isPresent(), "source cost numeric/null differs");
        if (numeric) {
            StrictJson.require(ready && copied && clamp.isPresent() && rounding.isPresent()
                    && rawTemps.stream().allMatch(OptionalLong::isPresent), "source cost numeric qualification differs");
            List<Long> expected = new ArrayList<>();
            List<Long> originalValues = original.orElseThrow();
            for (int index = 0; index < 10; index++) {
                long amount = originalValues.get(index) + rawTemps.get(index).orElseThrow();
                if (clamp.getAsInt() != 0) { amount = Math.max(amount, 0); }
                if (rounding.getAsInt() != 0) { amount = roundNative(amount); }
                expected.add(amount);
            }
            StrictJson.require(projected.orElseThrow().equals(expected) && unavailable.isEmpty(), "source cost parent arithmetic differs");
        }
        return new CostCopy(projected, nativeFinal);
    }

    /** Exact signed wrapping bias, IMUL-high/SAR14 correction, MOVSXD EDX and Q100000. */
    static long roundNative(long value) {
        long biased = value + (value < 0 ? -50_000 : 50_000);
        long shifted = BigInteger.valueOf(biased).multiply(new BigInteger("29F16B11C6D1E109", 16)).shiftRight(78).longValueExact();
        long quotient = shifted + (shifted < 0 ? 1 : 0);
        return (long) (int) quotient * 100_000;
    }

    private static boolean bool(JsonNode node) { return NegotiatedPreviewCodec.booleanValue(node); }
    private static Optional<Boolean> nullableBool(JsonNode node) { requireNode(node); return node.isNull() ? Optional.empty() : Optional.of(bool(node)); }
    private static Optional<String> reason(JsonNode node) { requireNode(node); return node.isNull() ? Optional.empty() : Optional.of(StrictJson.text(node)); }
    private static OptionalLong q64(JsonNode node) { return nullableLong(node, Long.MIN_VALUE, Long.MAX_VALUE); }
    private static OptionalLong nullableLong(JsonNode node, long low, long high) {
        requireNode(node);
        return node.isNull() ? OptionalLong.empty() : OptionalLong.of(StrictJson.integer(node, low, high));
    }
    private static OptionalInt byteValue(JsonNode node) {
        OptionalLong value = nullableLong(node, 0, 255);
        return value.isEmpty() ? OptionalInt.empty() : OptionalInt.of((int) value.getAsLong());
    }
    private static BigInteger pointer(JsonNode node) { return StrictJson.integer(node, BigInteger.ZERO, StrictJson.UINT64_MAX); }
    private static Optional<BigInteger> nullablePointer(JsonNode node) { requireNode(node); return node.isNull() ? Optional.empty() : Optional.of(pointer(node)); }
    private static boolean positive(Optional<BigInteger> pointer) { return pointer.isPresent() && pointer.get().signum() > 0; }
    private static JsonNode array(JsonNode node, int maximum) {
        StrictJson.require(node != null && node.isArray() && node.size() <= maximum, "bounded source array required");
        return node;
    }
    private static Optional<List<Long>> vector(JsonNode node) {
        requireNode(node);
        if (node.isNull()) { return Optional.empty(); }
        JsonNode values = array(node, 10);
        StrictJson.require(values.size() == 10, "ten exact source int64 cost operands required");
        List<Long> result = new ArrayList<>();
        for (JsonNode value : values) { result.add(StrictJson.integer(value, Long.MIN_VALUE, Long.MAX_VALUE)); }
        return Optional.of(List.copyOf(result));
    }
    private static void exactText(JsonNode node, String expected) { StrictJson.require(StrictJson.text(node).equals(expected), "source text binding differs"); }
    private static void equal(JsonNode node, long expected) { StrictJson.integer(node, expected, expected); }
    private static void equal(JsonNode node, BigInteger expected) { StrictJson.integer(node, expected, expected); }
    private static void requireNode(JsonNode node) { StrictJson.require(node != null, "source field missing; null is separate"); }
}

