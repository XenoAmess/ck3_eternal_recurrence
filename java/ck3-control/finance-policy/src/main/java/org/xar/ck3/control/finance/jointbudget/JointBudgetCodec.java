package org.xar.ck3.control.finance.jointbudget;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Army;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.AssessedInput;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Assessment;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Candidate;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Commitments;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Evaluated;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Input;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Intake;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.MissingAssessments;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Proposal;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Result;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Snapshot;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Values;

/** Narrow JSON boundary; native containers are projected, never passed into the policy. */
public final class JointBudgetCodec {
    private JointBudgetCodec() { }

    public static Input decode(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw), Set.of("intake", "snapshot", "assessments",
                "commitments", "gold_reserve_raw", "max_active_wars"));
        ObjectNode sourceIntake = object(root.get("intake"));
        ObjectNode sourceSnapshot = object(root.get("snapshot"));
        object(root.get("commitments"));
        Frame identity = frame(sourceIntake);
        require(frame(sourceSnapshot).equals(identity), "crossed the paused native frame");
        StrictJson.trueValue(sourceSnapshot.get("paused")); StrictJson.trueValue(sourceSnapshot.get("map_ready"));
        require(text(sourceIntake.get("policy")).equals("g2-m5-same-frame-intake-v1"), "same-frame legal intake required");
        List<Candidate> candidates = new ArrayList<>();
        for (JsonNode rawCandidate : array(sourceIntake.get("candidates"))) {
            ObjectNode candidate = object(rawCandidate);
            String domain = text(candidate.get("domain"));
            JsonNode proposal = candidate.get("observed_proposal");
            candidates.add(new Candidate(text(candidate.get("candidate_id")), domain,
                    nullableInteger(candidate.get("subject_character_id")), nullableInteger(candidate.get("candidate_character_id")),
                    proposal == null || proposal.isNull() ? null : proposal(object(proposal))));
        }
        Intake intake = new Intake(proposalFrame(sourceIntake), candidates);
        ArrayNode rows = array(root.get("assessments"));
        if (rows.isEmpty()) { return new MissingAssessments(intake); }
        require(rows.size() >= 5, "at least five assessed legal rows required");
        ObjectNode gold = object(sourceSnapshot.get("played_character_gold"));
        require(integer(gold.get("scale")).equals(BigInteger.valueOf(100_000)), "gold scale must be 100000");
        Set<BigInteger> wars = new HashSet<>();
        for (JsonNode war : array(sourceSnapshot.get("active_wars"))) {
            require(wars.add(integer(object(war).get("war_id"))), "duplicate current war identity");
        }
        List<Army> armies = new ArrayList<>();
        for (JsonNode rawArmy : array(sourceSnapshot.get("player_armies"))) {
            ObjectNode army = object(rawArmy);
            JsonNode controllable = army.get("controllable");
            require(controllable != null && controllable.isBoolean(), "controllable must be boolean");
            armies.add(new Army(integer(army.get("army_id")), controllable.booleanValue()));
        }
        Snapshot snapshot = new Snapshot(identity, integer(gold.get("raw")), wars, armies);
        List<Assessment> assessments = new ArrayList<>();
        for (JsonNode rawAssessment : rows) {
            ObjectNode assessment = object(rawAssessment);
            assessments.add(new Assessment(text(assessment.get("candidate_id")), frame(assessment), values(assessment),
                    nonnegative(assessment.get("gold_raw")), integer(assessment.get("projected_supply_margin_units")), claims(assessment)));
        }
        ObjectNode sourceCommitments = object(root.get("commitments"));
        JsonNode pending = sourceCommitments.get("pending_war_slots");
        Commitments commitments = new Commitments(nonnegative(sourceCommitments.get("gold_raw")),
                pending == null ? BigInteger.ZERO : nonnegative(pending), claims(sourceCommitments));
        return new AssessedInput(intake, snapshot, assessments, commitments, nonnegative(root.get("gold_reserve_raw")),
                nonnegative(root.get("max_active_wars")));
    }

    public static byte[] select(byte[] raw) { return encode(JointBudgetSelector.select(decode(raw))); }

    public static byte[] encode(Result result) {
        ObjectNode output = StrictJson.object();
        output.put("policy", "g2-m5-assessed-budget-selector-v1");
        output.put("status", result.status().name().toLowerCase(java.util.Locale.ROOT));
        putFrame(output, result.frame());
        output.put("assessed_candidate_count", result.evaluated().size());
        output.put("unassessed_legal_candidate_count", result.unassessedLegalCandidateCount());
        ArrayNode evaluated = output.putArray("evaluated");
        for (Evaluated row : result.evaluated()) {
            ObjectNode value = evaluated.addObject();
            value.put("candidate_id", row.candidateId()); value.put("domain", row.domain());
            value.put("net_units", row.netUnits()); value.put("reason", row.reason().name().toLowerCase(java.util.Locale.ROOT));
            ObjectNode components = value.putObject("value_components");
            components.put("benefit_units", row.valueComponents().benefitUnits());
            components.put("war_cost_units", row.valueComponents().warCostUnits());
            components.put("family_cost_units", row.valueComponents().familyCostUnits());
            components.put("diplomacy_cost_units", row.valueComponents().diplomacyCostUnits());
            components.put("supply_cost_units", row.valueComponents().supplyCostUnits());
            components.put("long_term_cost_units", row.valueComponents().longTermCostUnits());
            value.put("gold_raw", row.goldRaw()); value.put("war_slot_claim", row.warSlotClaim());
            value.put("minimum_gold_reserve_raw", row.minimumGoldReserveRaw());
            value.put("projected_supply_margin_units", row.projectedSupplyMarginUnits());
            putClaims(value.putObject("claims"), row.claims());
        }
        if (result.selectedCandidateId() == null) { output.putNull("selected_candidate_id"); }
        else { output.put("selected_candidate_id", result.selectedCandidateId()); }
        output.putNull("selected_step"); output.put("formal_action_ready", false);
        return StrictJson.canonical(output);
    }

    private static Proposal proposal(ObjectNode source) {
        JsonNode ready = source.get("domain_policy_ready");
        require(ready != null && ready.isBoolean(), "proposal policy readiness must be boolean");
        ObjectNode frame = StrictJson.object(source.get("frame"), Set.of("played_character_id", "native_revision",
                "date_raw", "snapshot_id", "revision", "episode_run_id"));
        return new Proposal(text(source.get("candidate_id")), text(source.get("domain")), ready.booleanValue(),
                proposalFrame(frame), nonnegative(source.get("gold_cost_raw")), claims(source),
                nullableInteger(source.get("projected_supply_margin_raw")), nonnegative(source.get("war_slot_claim")),
                nonnegative(source.get("minimum_gold_reserve_raw")));
    }
    private static Values values(ObjectNode source) {
        return new Values(nonnegative(source.get("benefit_units")), nonnegative(source.get("war_cost_units")),
                nonnegative(source.get("family_cost_units")), nonnegative(source.get("diplomacy_cost_units")),
                nonnegative(source.get("supply_cost_units")), nonnegative(source.get("long_term_cost_units")));
    }
    private static Claims claims(ObjectNode source) {
        return new Claims(numericClaims(source.get("army_ids")), characterClaims(source.get("ally_character_ids")),
                characterClaims(source.get("character_ids")), stringClaims(source.get("commitment_keys")));
    }
    private static Set<BigInteger> numericClaims(JsonNode source) {
        Set<BigInteger> result = new HashSet<>();
        for (JsonNode item : array(source)) {
            BigInteger value = integer(item);
            require(value.signum() >= 0, "claim outside integer domain");
            require(result.add(value), "duplicate resource claim");
        }
        return result;
    }
    private static Set<BigInteger> characterClaims(JsonNode source) {
        Set<BigInteger> result = new HashSet<>();
        for (JsonNode item : array(source)) {
            BigInteger value = NativeCharacterId.fromJson(item).asBigInteger();
            require(result.add(value), "duplicate resource claim");
        }
        return result;
    }
    private static Set<String> stringClaims(JsonNode source) {
        Set<String> result = new HashSet<>();
        for (JsonNode item : array(source)) {
            String value = text(item);
            require(!value.isEmpty() && result.add(value), "empty or duplicate commitment key");
        }
        return result;
    }
    private static Frame frame(ObjectNode source) {
        JsonNode player = source.get("played_character_id");
        if ((player == null || player.isNull()) && source.get("played_character") instanceof ObjectNode played) {
            player = played.get("character_id");
        }
        return new Frame(integer(player), integer(source.get("native_revision")), integer(source.get("date_raw")));
    }
    private static ProposalFrame proposalFrame(ObjectNode source) {
        return new ProposalFrame(frame(source), nullableText(source.get("snapshot_id")), nullableInteger(source.get("revision")),
                nullableText(source.get("episode_run_id")));
    }
    private static void putFrame(ObjectNode target, Frame frame) {
        target.put("played_character_id", frame.player()); target.put("native_revision", frame.nativeRevision());
        target.put("date_raw", frame.dateRaw());
    }
    private static void putClaims(ObjectNode target, Claims claims) {
        ArrayNode armies = target.putArray("army_ids"); claims.armyIds().stream().sorted().forEach(armies::add);
        ArrayNode allies = target.putArray("ally_character_ids"); claims.allyCharacterIds().stream().sorted().forEach(allies::add);
        ArrayNode characters = target.putArray("character_ids"); claims.characterIds().stream().sorted().forEach(characters::add);
        ArrayNode keys = target.putArray("commitment_keys");
        claims.commitmentKeys().stream().sorted(JointBudgetSelector::comparePythonText).forEach(keys::add);
    }
    private static ObjectNode object(JsonNode value) {
        require(value instanceof ObjectNode, "JSON object required"); return (ObjectNode) value;
    }
    private static ArrayNode array(JsonNode value) {
        require(value instanceof ArrayNode, "JSON list required"); return (ArrayNode) value;
    }
    private static BigInteger integer(JsonNode value) {
        require(value != null && value.isIntegralNumber(), "integer token required; no bool, float, null, or string");
        return value.bigIntegerValue();
    }
    private static BigInteger nonnegative(JsonNode value) {
        BigInteger result = integer(value); require(result.signum() >= 0, "nonnegative integer required"); return result;
    }
    private static BigInteger nullableInteger(JsonNode value) { return value == null || value.isNull() ? null : integer(value); }
    private static String nullableText(JsonNode value) { return value == null || value.isNull() ? null : text(value); }
    private static String text(JsonNode value) {
        require(value != null && value.isTextual(), "JSON string required");
        String result = value.textValue(); if (!result.isEmpty()) { StrictJson.text(result); } return result;
    }
    private static void require(boolean condition, String message) { JointBudgetSelector.require(condition, message); }
}

