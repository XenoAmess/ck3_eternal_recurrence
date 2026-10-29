package org.xar.ck3.control.wave2.planning.jointshortlist;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetCodec;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.planning.opportunity.ObservedOpportunitySelector;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.CurrentWarResources;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Frame;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Prepared;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.RaisedSupply;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.UnpricedCandidate;

/** Strict wrapper plus declared native projections. No action or reservation side effects. */
public final class JointShortlistCodec {
    private JointShortlistCodec() { }
    private static final Set<String> FRAME_FIELDS = Set.of("played_character_id", "native_revision", "date_raw", "snapshot_id", "revision", "episode_run_id");
    private static final ObjectMapper ENCODER = new ObjectMapper();
    private record Decoded(Prepared prepared, ObjectNode originalWarResources) { }

    public static Prepared decode(byte[] raw) { return prepare(raw).prepared(); }

    /** JSON projection for differential verification, explicitly excluding the original reservation side effect. */
    public static byte[] compare(byte[] raw) {
        Decoded decoded = prepare(raw); Prepared prepared = decoded.prepared();
        ObjectNode result = StrictJson.object();
        result.put("phase", prepared.phase().name()); result.set("frame", encodeFrame(prepared.frame()));
        result.put("legal_candidate_count", prepared.legalCandidateCount()); result.put("priced_candidate_count", prepared.pricedCandidateCount());
        ArrayNode missing = result.putArray("unpriced_candidates");
        for (UnpricedCandidate candidate : prepared.unpricedCandidates()) {
            ObjectNode row = missing.addObject(); row.put("candidate_id", candidate.candidateId()); row.put("domain", candidate.domain().name());
            ArrayNode needed = row.putArray("needed"); candidate.needed().forEach(needed::add);
        }
        if (decoded.originalWarResources() == null) { result.putNull("current_war_resources"); }
        else { result.set("current_war_resources", decoded.originalWarResources()); }
        JointBudgetSelector.Result analysis = prepared.analyze();
        if (analysis == null) { result.putNull("analysis"); }
        else { result.set("analysis", StrictJson.parse(JointBudgetCodec.encode(analysis))); }
        result.put("reservation_created", false); result.putNull("selected_step"); result.put("formal_action_ready", false);
        return encodeJson(result);
    }

    private static Decoded prepare(byte[] raw) {
        require(raw != null && raw.length > 0 && raw.length <= 65536, "bounded nonempty shortlist request required");
        // Preserve decimal tokens in opaque native/domain extension fields. Integer consumers still reject them.
        ObjectNode request = StrictJson.object(OpportunityJson.toNode(OpportunityJson.parse(raw)), Set.of("snapshot", "intake", "observed_proposals", "assessments",
                "marriage_projection", "war_current", "existing_commitments", "gold_reserve_raw", "max_active_wars"));
        ObjectNode snapshot = object(request.get("snapshot")); ObjectNode intake = object(request.get("intake"));
        require(text(intake.get("policy")).equals("g2-m5-same-frame-intake-v1"), "current legal intake required");
        Frame frame = frame(snapshot, false);
        require(intake.hasNonNull("played_character_id"), "intake player identity required");
        require(frame.equals(frame(intake, false)), "shortlist crossed the paused frame");
        ArrayNode legal = array(intake.get("candidates")).deepCopy();
        Map<String, ObjectNode> byId = new LinkedHashMap<>();
        for (JsonNode value : legal) {
            ObjectNode row = object(value); require(byId.put(textAllowEmpty(row.get("candidate_id")), row) == null, "duplicate legal candidate identity");
        }
        for (JsonNode value : array(request.get("observed_proposals"))) {
            ObjectNode normalize = StrictJson.object(); normalize.set("frame", encodeFrame(frame)); normalize.set("proposal", value);
            ObjectNode proposal = object(OpportunityJson.toNode(OpportunityJson.parse(ObservedOpportunitySelector.normalizeProposal(encodeJson(normalize)))));
            String id = text(proposal.get("candidate_id")); require(!byId.containsKey(id), "proposal duplicates native legal candidate");
            ObjectNode row = StrictJson.object(); row.put("candidate_id", id); row.set("domain", proposal.get("domain")); row.set("observed_proposal", proposal);
            legal.add(row); byId.put(id, row);
        }
        ArrayNode assessments = array(request.get("assessments")); Set<String> quoted = new HashSet<>();
        Set<String> valuePolicies = new HashSet<>();
        for (JsonNode value : assessments) {
            ObjectNode row = object(value); String id = textAllowEmpty(row.get("candidate_id"));
            require(byId.containsKey(id) && quoted.add(id), "assessment absent or duplicated");
            valuePolicies.add(text(row.get("common_value_policy")));
        }
        require(assessments.isEmpty() || valuePolicies.size() == 1, "one explicit common-value policy required");
        List<ObjectNode> pricedFamily = new ArrayList<>(); List<ObjectNode> pricedWar = new ArrayList<>();
        for (String id : quoted) {
            ObjectNode row = byId.get(id); String domain = text(row.get("domain"));
            if (domain.equals("first_heir_marriage")) { pricedFamily.add(row); }
            if (domain.equals("war") && !row.has("observed_proposal")) { pricedWar.add(row); }
        }
        if (!pricedFamily.isEmpty()) { requireMarriage(request.get("marriage_projection"), intake, pricedFamily); }
        ObjectNode warResources = pricedWar.isEmpty() ? null : requireWar(request.get("war_current"), snapshot, pricedWar);
        CurrentWarResources current = warResources == null ? null : warResources(warResources);
        List<UnpricedCandidate> missing = new ArrayList<>();
        for (Map.Entry<String, ObjectNode> entry : byId.entrySet()) {
            if (quoted.contains(entry.getKey())) { continue; }
            Domain domain;
            try { domain = Domain.valueOf(text(entry.getValue().get("domain"))); }
            catch (IllegalArgumentException error) { throw new IllegalArgumentException("unknown candidate domain", error); }
            missing.add(new UnpricedCandidate(entry.getKey(), domain, JointShortlist.missingInputs(domain)));
        }
        JointBudgetSelector.AssessedInput selectorInput = null;
        if (assessments.size() >= 5) {
            // The original dispatcher adds the full-frame check and explicit observed commitment requirements.
            StrictJson.trueValue(snapshot.get("paused")); StrictJson.trueValue(snapshot.get("map_ready"));
            for (JsonNode assessment : assessments) { require(frame.equals(frame(object(assessment), false)), "assessment crossed full paused frame"); }
            ObjectNode commitments = object(request.get("existing_commitments"));
            require(frame.equals(frame(object(commitments.get("frame")), true)), "commitments crossed paused frame");
            BigInteger pending = nonnegative(commitments.get("pending_war_slots"));
            require(pending.compareTo(nonnegative(request.get("max_active_wars"))) <= 0, "pending war slots exceed budget");
            ObjectNode combined = intake.deepCopy(); combined.set("candidates", legal);
            ObjectNode selector = StrictJson.object(); selector.set("intake", combined); selector.set("snapshot", snapshot);
            selector.set("assessments", assessments); selector.set("commitments", commitments);
            selector.set("gold_reserve_raw", request.get("gold_reserve_raw")); selector.set("max_active_wars", request.get("max_active_wars"));
            JointBudgetSelector.Input decoded = JointBudgetCodec.decode(encodeJson(selector));
            require(decoded instanceof JointBudgetSelector.AssessedInput, "complete selector input required");
            selectorInput = (JointBudgetSelector.AssessedInput) decoded;
        }
        return new Decoded(new Prepared(frame, legal.size(), assessments.size(), missing, current, selectorInput), warResources);
    }

    private static void requireMarriage(JsonNode raw, ObjectNode intake, List<ObjectNode> pricedFamily) {
        ObjectNode projection = object(raw);
        require(text(projection.get("schema")).equals("xar.ck3.first-heir-candidate-alliance-projection.v1")
                && text(projection.get("status")).equals("available")
                && integer(projection.get("native_revision")).equals(integer(intake.get("native_revision")))
                && integer(projection.get("legality_query_sequence")).equals(integer(intake.get("family_legality_query_sequence"))), "current five-row family projection required");
        ArrayNode rows = array(projection.get("rows")); Set<BigInteger> candidates = new HashSet<>();
        require(rows.size() == 5, "five current family rows required");
        for (JsonNode rawRow : rows) {
            ObjectNode row = object(rawRow);
            require(text(row.get("status")).equals("available")
                    && integer(row.get("actor_character_id")).equals(integer(intake.get("played_character_id")))
                    && integer(row.get("heir_character_id")).equals(integer(intake.get("first_heir_character_id")))
                    && candidates.add(integer(row.get("candidate_character_id"))), "five distinct current family projections required");
        }
        for (ObjectNode row : pricedFamily) { require(candidates.contains(integer(row.get("candidate_character_id"))), "priced family absent from projection"); }
    }
    private static ObjectNode requireWar(JsonNode raw, ObjectNode snapshot, List<ObjectNode> pricedWars) {
        ObjectNode readback = object(raw); ObjectNode readiness = object(readback.get("readiness"));
        ObjectNode current = object(readback.get("m5_war_primary_current"));
        require(text(readback.get("status")).equals("available"), "current war resources unavailable");
        StrictJson.trueValue(readback.get("read_only")); requireBoolean(readback.get("advertised"), false);
        require(text(readback.get("queried_snapshot_id")).equals(text(snapshot.get("snapshot_id")))
                && integer(readback.get("queried_revision")).equals(integer(snapshot.get("revision")))
                && integer(readback.get("queried_native_revision")).equals(integer(snapshot.get("native_revision")))
                && integer(readback.get("date_raw")).equals(integer(snapshot.get("date_raw"))), "current war resources crossed paused frame");
        for (String key : List.of("current_treasury_ready", "current_raised_armies_ready", "current_raised_supply_ready")) { StrictJson.trueValue(readiness.get(key)); }
        ObjectNode currentTreasury = object(current.get("current_treasury"));
        require(integer(current.get("actor_character_id")).equals(integer(snapshot.get("played_character_id")))
                && currentTreasury.equals(object(snapshot.get("played_character_gold"))), "current treasury differs from snapshot");
        ArrayNode wars = StrictJson.object().putArray("ids");
        for (JsonNode value : array(snapshot.get("active_wars"))) { wars.add(integer(object(value).get("war_id"))); }
        require(wars.equals(current.get("active_war_ids")), "active wars differ from snapshot");
        ObjectNode declaration = object(current.get("declaration"));
        for (ObjectNode candidate : pricedWars) {
            for (String key : List.of("target_character_id", "casus_belli_index", "casus_belli_key", "configuration_index", "claimant_character_id", "target_title_ids")) {
                require(java.util.Objects.equals(declaration.get(key), candidate.get(key)), "priced war differs from current declaration");
            }
        }
        Set<BigInteger> armyIds = new HashSet<>();
        for (JsonNode value : array(snapshot.get("player_armies"))) { armyIds.add(integer(object(value).get("army_id"))); }
        Set<BigInteger> suppliedIds = new HashSet<>(); ArrayNode supply = array(current.get("actor_current_raised_supply"));
        for (JsonNode value : supply) {
            ObjectNode row = object(value); BigInteger id = integer(row.get("army_id"));
            require(armyIds.contains(id) && suppliedIds.add(id), "raised supply lacks distinct current army");
            nonnegative(row.get("current_supply_raw")); require(integer(row.get("current_supply_scale")).equals(BigInteger.valueOf(100000)), "current supply scale");
        }
        ObjectNode output = StrictJson.object(); output.set("current_treasury_raw", current.get("current_treasury").get("raw"));
        output.set("active_war_ids", wars); output.set("actor_current_raised_supply", supply.deepCopy());
        output.put("future_supply_ready", isTrue(readiness.get("future_supply_ready")));
        output.put("campaign_cost_ready", isTrue(readiness.get("campaign_cost_ready"))); return output;
    }
    private static CurrentWarResources warResources(ObjectNode source) {
        List<BigInteger> wars = new ArrayList<>(); for (JsonNode row : array(source.get("active_war_ids"))) { wars.add(integer(row)); }
        List<RaisedSupply> supply = new ArrayList<>();
        for (JsonNode row : array(source.get("actor_current_raised_supply"))) {
            supply.add(new RaisedSupply(integer(row.get("army_id")), nonnegative(row.get("current_supply_raw")), integer(row.get("current_supply_scale"))));
        }
        return new CurrentWarResources(integer(source.get("current_treasury_raw")), wars, supply, isTrue(source.get("future_supply_ready")), isTrue(source.get("campaign_cost_ready")));
    }
    private static Frame frame(ObjectNode source, boolean exact) {
        if (exact) { require(source.size() == FRAME_FIELDS.size() && FRAME_FIELDS.stream().allMatch(source::has), "exact six-field frame required"); }
        JsonNode player = source.get("played_character_id");
        if ((player == null || player.isNull()) && source.get("played_character") instanceof ObjectNode played) { player = played.get("character_id"); }
        return new Frame(integer(player), integer(source.get("native_revision")), nonnegative(source.get("date_raw")), text(source.get("snapshot_id")), integer(source.get("revision")), text(source.get("episode_run_id")));
    }
    private static ObjectNode encodeFrame(Frame frame) {
        ObjectNode output = StrictJson.object(); output.put("played_character_id", frame.player()); output.put("native_revision", frame.nativeRevision());
        output.put("date_raw", frame.dateRaw()); output.put("snapshot_id", frame.snapshotId()); output.put("revision", frame.revision()); output.put("episode_run_id", frame.episodeRunId()); return output;
    }
    private static ObjectNode object(JsonNode value) { require(value instanceof ObjectNode, "JSON object required"); return (ObjectNode) value; }
    private static ArrayNode array(JsonNode value) { require(value instanceof ArrayNode, "JSON array required"); return (ArrayNode) value; }
    private static BigInteger integer(JsonNode value) { require(value != null && value.isIntegralNumber(), "integer token required"); return value.bigIntegerValue(); }
    private static BigInteger nonnegative(JsonNode value) { BigInteger result = integer(value); require(result.signum() >= 0, "nonnegative integer required"); return result; }
    private static String text(JsonNode value) { String result = textAllowEmpty(value); require(!result.isEmpty(), "nonempty text required"); return result; }
    private static String textAllowEmpty(JsonNode value) { require(value != null && value.isTextual(), "string token required"); String result = value.textValue(); if (!result.isEmpty()) { StrictJson.text(result); } return result; }
    private static boolean isTrue(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    private static byte[] encodeJson(JsonNode value) {
        try {
            byte[] raw = ENCODER.writeValueAsBytes(value);
            require(raw.length <= 65536, "shortlist projection exceeds finite byte allowance"); return raw;
        } catch (IOException error) { throw new IllegalArgumentException("shortlist JSON encoding failed", error); }
    }
    private static void requireBoolean(JsonNode value, boolean expected) { require(value != null && value.isBoolean() && value.booleanValue() == expected, "boolean token value required"); }
    private static void require(boolean condition, String message) { JointShortlist.require(condition, message); }
}
