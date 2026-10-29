package org.xar.ck3.control.wave2.planning.mercenarypurchaseneed;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.StrictJson;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;

import static org.xar.ck3.control.wave2.planning.mercenarypurchaseneed.MercenaryPurchaseNeed.*;

/** Strict envelope and declared projection of the existing extensible priority output. */
public final class MercenaryPurchaseNeedCodec {
    public static final String REQUEST_SCHEMA = "xar.mercenary-purchase-model-need.request.v1";
    private MercenaryPurchaseNeedCodec() { }

    public static Input decode(byte[] raw) {
        ObjectNode envelope = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "priority"));
        StrictJson.require(REQUEST_SCHEMA.equals(StrictJson.text(envelope.get("schema"))), "unknown query-model schema");
        JsonNode priority = envelope.get("priority");
        StrictJson.require(priority.isObject(), "priority must be an object");
        List<War> wars = new ArrayList<>();
        JsonNode rows = priority.path("wars");
        if (rows.isArray()) {
            for (JsonNode row : rows) {
                if (!row.isObject()) { continue; }
                Optional<BigInteger> score = exactInteger(row.get("player_relative_war_score"));
                List<String> reasons = reasons(row.get("protect_cash_reasons"));
                if (reasons.isEmpty() || score.isEmpty() || score.orElseThrow().compareTo(BigInteger.valueOf(-100)) <= 0) {
                    continue;
                }
                wars.add(new War(reasons, score, soldiers(row.get("observed_player_raised_soldiers")),
                        soldiers(row.get("observed_enemy_raised_soldiers")), truth(row.get("raised_force_deficit"))));
            }
        }
        JsonNode union = priority.path("primary_war_hostile_union_v1");
        List<BigInteger> warIds = new ArrayList<>();
        if (union.isObject()) {
            JsonNode identities = union.get("war_ids");
            if (identities != null) {
                StrictJson.require(identities.isArray(), "union war_ids must be an explicit array");
                for (JsonNode identity : identities) {
                    warIds.add(exactInteger(identity).orElseThrow(() -> new IllegalArgumentException("union WarID needs an integer token")));
                }
            }
        }
        return new Input(wars, new HostileUnion(warIds, truth(union.get("shared_force_deficit"))));
    }

    public static byte[] encode(Need need) {
        ObjectNode result = StrictJson.object();
        result.put("query_can_change_current_headcount_flip_model", need.queryCanChangeCurrentHeadcountFlipModel());
        result.put("reason", need.reason().wire());
        result.put("scope", "only the existing current-headcount-flip purchase model");
        result.put("future_enemy_reinforcements_bounded", false);
        result.putNull("overall_war_safe");
        result.put("pending_hire_observations_must_bypass", true);
        return StrictJson.canonical(result);
    }

    public static Need decodeResult(byte[] raw) {
        JsonNode result = StrictJson.parse(raw);
        StrictJson.object(result, Set.of("query_can_change_current_headcount_flip_model", "reason", "scope",
                "future_enemy_reinforcements_bounded", "overall_war_safe", "pending_hire_observations_must_bypass"));
        JsonNode flag = result.get("query_can_change_current_headcount_flip_model");
        StrictJson.require(flag.isBoolean(), "query model requires an actual boolean");
        Need need = new Need(flag.booleanValue(), flag.booleanValue()
                ? Reason.CURRENT_DEFICIT_OR_UNKNOWN : Reason.NO_RECOVERABLE_CURRENT_DEFICIT);
        StrictJson.require(result.equals(StrictJson.parse(encode(need))), "query-model result fields or safety limits changed");
        return need;
    }

    private static List<String> reasons(JsonNode value) {
        if (value == null || value.isNull()) { return List.of(); }
        StrictJson.require(value.isArray(), "protect_cash_reasons must be an explicit collection");
        List<String> reasons = new ArrayList<>();
        for (JsonNode reason : value) { reasons.add(StrictJson.text(reason)); }
        return List.copyOf(reasons);
    }
    private static Optional<BigInteger> exactInteger(JsonNode value) {
        return value != null && value.isIntegralNumber() ? Optional.of(value.bigIntegerValue()) : Optional.empty();
    }
    private static Optional<BigInteger> soldiers(JsonNode value) {
        if (value == null || value.isNull()) { return Optional.empty(); }
        BigInteger count = exactInteger(value).orElseThrow(() -> new IllegalArgumentException("soldier count requires an integer token"));
        StrictJson.require(count.signum() >= 0, "soldier count must be nonnegative");
        return Optional.of(count);
    }
    private static Truth truth(JsonNode value) {
        if (value == null || value.isNull() || value.isMissingNode()) { return Truth.UNKNOWN; }
        StrictJson.require(value.isBoolean(), "force-deficit branch must be boolean or null");
        return value.booleanValue() ? Truth.TRUE : Truth.FALSE;
    }
}
