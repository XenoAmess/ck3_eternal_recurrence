package org.xar.ck3.control.wave2.finance.giftroute;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidateCodec;
import org.xar.ck3.control.wave2.finance.factionthreat.FactionThreatCodec;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingCodec;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel;
import org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFrameCodec;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Read;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransportCodec;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.CandidateReadTrace;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.CheckpointRead;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.ClearStep;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.Context;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.KnownEmptyTrace;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.Patch;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.PlanPatch;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.PlanShape;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.ReadOnlyReplan;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.Result;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.SelectStep;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashCodec;

/** Plan serialization stays in this application boundary; domain patch records contain no JSON trees. */
public final class GiftRouteCodec {
    public static final int MAX_BYTES = 1_048_576;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(64).build()).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
            .configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);
    private GiftRouteCodec() { }
    public static final class OriginalPlan {
        private final byte[] bytes;
        OriginalPlan(byte[] bytes) { this.bytes = bytes.clone(); }
        public byte[] bytes() { return bytes.clone(); }
    }
    public record Input(Context context, OriginalPlan original) {
        public Input { java.util.Objects.requireNonNull(context); java.util.Objects.requireNonNull(original); }
    }

    public static Input decode(byte[] bytes) {
        JsonNode input = StrictJson.object(parse(bytes), Set.of("schema", "planned", "snapshot", "history", "available_steps"));
        StrictJson.require("xar.faction-gift-route-input.v1".equals(text(input.get("schema"))), "faction route input schema required");
        JsonNode planned = object(input.get("planned")); JsonNode snapshot = object(input.get("snapshot"));
        JsonNode plan = planned.get("plan"); boolean hasPlan = plan != null && plan.isObject();
        Read<String> step = hasPlan ? readText(plan, "selected_step") : Read.missing();
        BigInteger revision = integer(planned.get("revision")); JsonNode available = input.get("available_steps");
        StrictJson.require(available.isArray(), "available steps array required"); Set<String> steps = new HashSet<>();
        for (JsonNode value : available) { StrictJson.require(steps.add(text(value)), "duplicate available step"); }
        ObjectNode rootInput = JSON.createObjectNode(); rootInput.set("snapshot", snapshot); rootInput.set("history", input.get("history"));
        Context context = new Context(hasPlan ? PlanShape.OBJECT : PlanShape.NO_OBJECT, step, revision,
                GiftReadTransportCodec.decodeSnapshot(write(snapshot)), readText(snapshot, "episode_run_id"),
                FactionCandidateCodec.decodeRootSearch(write(rootInput)), steps);
        return new Input(context, new OriginalPlan(write(planned)));
    }

    public static byte[] encodePlan(OriginalPlan original, PlanPatch result) {
        ObjectNode planned = (ObjectNode) object(parse(original.bytes())); Patch patch = result.patch();
        JsonNode existingPlan = planned.get("plan");
        if (existingPlan == null || !existingPlan.isObject()) {
            StrictJson.require(patch.equals(Patch.keep()), "cannot patch absent plan"); return write(planned);
        }
        ObjectNode plan = (ObjectNode) existingPlan;
        if (patch.step() instanceof ClearStep) { plan.putNull("selected_step"); }
        else if (patch.step() instanceof SelectStep selected) { plan.put("selected_step", selected.step()); }
        patch.phase().ifPresent(value -> plan.put("phase", value)); patch.reason().ifPresent(value -> plan.put("reason", value));
        patch.pending().ifPresent(pending -> {
            GiftPendingModel.Ledger ledger = new GiftPendingModel.Ledger(Optional.of(pending), Map.of());
            plan.set("faction_gift_pending_action", parse(GiftPendingCodec.encodeLedger(ledger)).get("pending"));
        });
        JsonNode candidate = null;
        if (patch.candidate() instanceof KnownEmptyTrace) {
            ObjectNode empty = JSON.createObjectNode(); empty.put("status", "known_empty"); empty.put("gift_submission_enabled", false);
            empty.put("public_capability_advertised", false); empty.put("faction_dissolved_or_gift_applied", "not_inferred"); candidate = empty;
        } else if (patch.candidate() instanceof CandidateReadTrace trace) { candidate = parse(GiftReadTransportCodec.encodeResult(trace.result())); }
        if (candidate != null) { plan.set("faction_gift_private_candidate_v1", candidate); }
        patch.threat().ifPresent(threat -> plan.set("faction_gift_stock_threat_v1", parse(FactionThreatCodec.encode(threat))));
        patch.cash().ifPresent(cash -> plan.set("faction_gift_wartime_cash_v1", parse(GiftWarCashCodec.encode(cash))));
        patch.newSpendDeferredReason().ifPresent(reason -> {
            ObjectNode deferred = plan.putObject("faction_gift_spending_deferred_v1"); deferred.put("reason", reason);
            deferred.put("new_gift_spending_authorized", false);
        });
        if (patch.attachGiftAction()) {
            StrictJson.require(candidate != null, "actual candidate trace required for selected action plan");
            plan.set("faction_gift_action", candidate.deepCopy());
            plan.set("faction_gift_pre_submit_checkpoint", parse(patch.checkpoint().orElseThrow().original().json().getBytes(StandardCharsets.UTF_8)));
        }
        return write(planned);
    }

    /** Internal outcome wrapper used by a host to retain proof and replan the whole turn. */
    public static byte[] encodeOutcome(OriginalPlan original, Result result) {
        ObjectNode output = JSON.createObjectNode();
        if (result instanceof PlanPatch patch) {
            output.put("kind", "return"); output.set("planned", parse(encodePlan(original, patch)));
        } else if (result instanceof ReadOnlyReplan replan) {
            output.put("kind", "read_only_replan"); output.set("proof", parse(GiftPendingFrameCodec.encodeProof(replan.proof())));
        } else { throw new IllegalArgumentException("typed route result required"); }
        return write(output);
    }

    public static CheckpointRead decodeExistingCheckpoint(byte[] bytes) {
        JsonNode node = object(parse(bytes));
        return new CheckpointRead(node.has("status") && node.get("status").isTextual() ? text(node.get("status")) : "",
                readText(node, "sha256"), readInteger(node, "date_raw"), readText(node, "episode_run_id"),
                new GiftPendingModel.ObjectEvidence(new String(write(node), StandardCharsets.UTF_8)));
    }
    private static Read<String> readText(JsonNode node, String key) {
        JsonNode value = node.get(key); return value == null ? Read.missing() : value.isNull() ? Read.nil() : Read.of(text(value));
    }
    private static Read<BigInteger> readInteger(JsonNode node, String key) {
        JsonNode value = node.get(key); return value == null ? Read.missing() : value.isNull() ? Read.nil() : Read.of(integer(value));
    }
    private static String text(JsonNode node) {
        StrictJson.require(node != null && node.isTextual(), "actual string token required");
        if (!node.textValue().isEmpty()) { StrictJson.text(node.textValue()); } return node.textValue();
    }
    private static BigInteger integer(JsonNode node) {
        StrictJson.require(node != null && node.isIntegralNumber(), "actual integer token required, no bool/float/string");
        return node.bigIntegerValue();
    }
    private static JsonNode object(JsonNode node) { StrictJson.require(node != null && node.isObject(), "object required"); return node; }
    private static JsonNode parse(byte[] bytes) {
        StrictJson.require(bytes != null && bytes.length > 0 && bytes.length <= MAX_BYTES, "bounded plan JSON required");
        try {
            String value = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            JsonNode node = JSON.readTree(value); StrictJson.require(node != null, "JSON value required"); return node;
        } catch (IOException error) { throw new ContractViolationException("invalid UTF-8/duplicate/trailing plan JSON", error); }
    }
    private static byte[] write(JsonNode node) {
        byte[] bytes = GiftReadTransportCodec.encodeObjectProjection(node);
        StrictJson.require(bytes.length <= MAX_BYTES, "plan exceeds role budget"); return bytes;
    }
}
