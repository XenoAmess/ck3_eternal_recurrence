package org.xar.ck3.control.wave3.development.wartimesequencing;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyCodec;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.NoCashObservation;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.ObservedCash;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.QuoteCashObservation;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.UnavailableCashObservation;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessmentCodec;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.Opportunity;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.NativeQuote;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.QuotedOutlay;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.Request;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.Result;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.Selection;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.Stage;

/** Closed sequencing envelope; native cash/quote payloads still use their single existing codecs. */
public final class OrdinaryWartimeConstructionCodec {
    public static final String SCHEMA = "xar.ordinary-wartime-construction-input.v1";
    public static final String RESULT_SCHEMA = "xar.ordinary-wartime-construction.v1";
    public static final int MAX_BYTES = 262_144;
    private OrdinaryWartimeConstructionCodec() { }
    /** Original bytes and the sole decoded contract stay together through local/HTTP consumers. */
    public static final class ObservedRequest {
        private final byte[] original;
        private final Request input;
        public ObservedRequest(byte[] original) { this.input = decode(original); this.original = original.clone(); }
        public byte[] original() { return original.clone(); }
        public Request input() { return input; }
    }

    public static Request decode(byte[] original) {
        ObjectNode root = StrictJson.object(StrictJson.parse(original, MAX_BYTES), Set.of(
                "schema", "stage", "original_selected_step", "original_phase", "opportunity", "cash_input", "quoted_outlay", "financing_request"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(root.get("schema"))), "ordinary wartime construction schema");
        Stage stage = enumValue(Stage.class, root.get("stage"));
        Opportunity opportunity = enumValue(Opportunity.class, root.get("opportunity"));
        JsonNode selected = root.get("original_selected_step");
        Optional<String> step = selected.isNull() ? Optional.empty() : Optional.of(StrictJson.text(selected));
        Optional<String> phase = root.get("original_phase").isNull() ? Optional.empty() : Optional.of(StrictJson.text(root.get("original_phase")));
        Optional<QuotedOutlay> quoted = Optional.empty();
        if (!root.get("quoted_outlay").isNull()) {
            ObjectNode outlay = StrictJson.object(root.get("quoted_outlay"), Set.of("query_observation", "cash_observation"));
            quoted = Optional.of(new QuotedOutlay(new NativeQuote(bytes(outlay.get("query_observation"))),
                    observation(outlay.get("cash_observation"))));
        }
        return new Request(new Selection(step, phase, opportunity), stage,
                WartimeConstructionCodec.decode(bytes(root.get("cash_input"))), quoted,
                root.get("financing_request").isNull() ? Optional.empty()
                        : Optional.of(EmergencyFinancingAssessmentCodec.decode(bytes(root.get("financing_request")))));
    }

    public static byte[] evaluate(byte[] original) { return encode(OrdinaryWartimeConstruction.compose(decode(original))); }

    /** The authority's payload keeps its own writer/receipt codec; this encodes only our diagnostic review. */
    public static byte[] encodeFinalReview(OrdinaryWartimeConstructionConsumer.FinalReview review) {
        ObjectNode output = StrictJson.object(); output.put("schema", "xar.ordinary-wartime-construction-before-intent-review.v1");
        output.put("status", review.status().name()); output.put("existing_authority_called", review.existingAuthorityCalled());
        output.put("native_action_applied_verified", review.nativeActionAppliedVerified()); output.put("continue_ordinary_planner", review.continueOrdinaryPlanner());
        output.put("review_grants_authority", false);
        if (review.currentAssessment().isPresent()) output.set("current_assessment", StrictJson.parse(encode(review.currentAssessment().orElseThrow()), MAX_BYTES));
        else output.putNull("current_assessment");
        return bytes(output);
    }

    /** Data round-trip only: it never acquires a writer lock or grants an authority callback. */
    public static OrdinaryWartimeConstructionConsumer.FinalReview decodeFinalReview(byte[] raw, Optional<Request> currentRequest) {
        java.util.Objects.requireNonNull(currentRequest);
        ObjectNode node = StrictJson.object(StrictJson.parse(raw, MAX_BYTES), Set.of("schema", "status", "existing_authority_called",
                "native_action_applied_verified", "continue_ordinary_planner", "review_grants_authority", "current_assessment"));
        StrictJson.require("xar.ordinary-wartime-construction-before-intent-review.v1".equals(StrictJson.text(node.get("schema"))),
                "before-intent review schema");
        Optional<Result> assessment = Optional.empty();
        if (!node.get("current_assessment").isNull()) {
            StrictJson.require(currentRequest.isPresent(), "original current request required to read its review");
            Result produced = OrdinaryWartimeConstruction.compose(currentRequest.orElseThrow());
            StrictJson.require(StrictJson.parse(encode(produced), MAX_BYTES).equals(node.get("current_assessment")), "review differs from actual current producer");
            assessment = Optional.of(produced);
        } else StrictJson.require(currentRequest.isEmpty(), "review without current assessment cannot claim a current request");
        var result = new OrdinaryWartimeConstructionConsumer.FinalReview(
                enumValue(OrdinaryWartimeConstructionConsumer.FinalStatus.class, node.get("status")), assessment);
        StrictJson.require(node.equals(StrictJson.parse(encodeFinalReview(result), MAX_BYTES)), "before-intent review invariant flags differ");
        return result;
    }

    public static byte[] encode(Result result) {
        ObjectNode output = StrictJson.object(); output.put("schema", RESULT_SCHEMA);
        output.put("stage", result.stage().name()); output.put("disposition", result.disposition().name());
        output.put("opportunity", result.originalSelection().opportunity().name());
        if (result.selectedStep().isPresent()) output.put("selected_step", result.selectedStep().orElseThrow()); else output.putNull("selected_step");
        if (result.originalSelection().phase().isPresent()) output.put("original_phase", result.originalSelection().phase().orElseThrow()); else output.putNull("original_phase");
        if (result.reason().isPresent()) output.put("reason", result.reason().orElseThrow().name()); else output.putNull("reason");
        output.put("continue_ordinary_planner", result.continueOrdinaryPlanner());
        output.put("can_submit_action", result.canSubmitAction()); output.put("unknown_replay_allowed", false);
        output.put("unreceived_funding_credited_raw", result.unreceivedFundingCreditedRaw());
        output.put("financing_status", result.financing().status().name());
        if (result.financing().assessment().isPresent()) output.set("financing", StrictJson.parse(
                EmergencyFinancingAssessmentCodec.encode(result.financing().assessment().orElseThrow())));
        else output.putNull("financing");
        output.set("wartime_cash", StrictJson.parse(WartimeConstructionCodec.encode(result.cash()), WartimeConstructionCodec.MAX_BYTES));
        if (result.monthly().isPresent()) output.set("monthly_cash", StrictJson.parse(
                ConstructionEconomyCodec.encodeQuoteProjection(result.monthly().orElseThrow()), ConstructionEconomyCodec.MAX_BYTES));
        else output.putNull("monthly_cash");
        if (result.candidate().isPresent()) output.set("candidate", StrictJson.parse(
                result.candidate().orElseThrow().original().bytes(), ConstructionEconomyCodec.MAX_BYTES).get("candidate"));
        else output.putNull("candidate");
        return bytes(output);
    }

    /** Persisted/HTTP output is an analysis receipt: replay the real producer before consuming it. */
    public static Result verifyResponse(byte[] originalRequest, byte[] response) {
        Result recomputed = OrdinaryWartimeConstruction.compose(decode(originalRequest));
        StrictJson.require(StrictJson.parse(encode(recomputed), MAX_BYTES).equals(StrictJson.parse(response, MAX_BYTES)),
                "ordinary wartime result differs from its current request producer");
        return recomputed;
    }

    private static QuoteCashObservation observation(JsonNode raw) {
        StrictJson.require(raw.isObject(), "cash observation object required");
        String kind = StrictJson.text(raw.get("kind"));
        return switch (kind) {
            case "missing" -> { StrictJson.object(raw, Set.of("kind")); yield new NoCashObservation(); }
            case "unavailable" -> { StrictJson.object(raw, Set.of("kind")); yield new UnavailableCashObservation(); }
            case "observed" -> {
                StrictJson.object(raw, Set.of("kind", "cash", "reserve_gold_raw"));
                JsonNode reserve = raw.get("reserve_gold_raw");
                StrictJson.require(reserve.isIntegralNumber() && reserve.bigIntegerValue().signum() >= 0,
                        "nonnegative exact reserve required");
                yield new ObservedCash(ConstructionEconomyCodec.decodeCash(bytes(raw.get("cash"))), reserve.bigIntegerValue());
            }
            default -> throw new IllegalArgumentException("unknown cash observation kind");
        };
    }
    private static <E extends Enum<E>> E enumValue(Class<E> type, JsonNode raw) {
        return Enum.valueOf(type, StrictJson.text(raw));
    }
    private static byte[] bytes(JsonNode node) {
        return SdkProjectionJson.encode(node, MAX_BYTES);
    }
}
