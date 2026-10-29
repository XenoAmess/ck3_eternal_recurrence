package org.xar.ck3.control.g2.planning;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Shared synthetic test inputs for lifecycle and the real M5/G2 consumers. No native/file/action fixture. */
public final class ProposalLifecycleFixtures {
    private ProposalLifecycleFixtures() { }
    public static G2Source source() { return new G2Source("synthetic-proposal", "2026-10-22T00:00:00Z", "synthetic-build", new ExactRef("metadata-only-not-opened", 1, "0".repeat(64))); }
    public static ObjectNode request() {
        ObjectNode root = StrictJson.object(); root.put("schema", ProposalLifecycleCodec.REQUEST_SCHEMA);
        ObjectNode observed = root.putObject("observation"); observed.put("observation_version", 1); ObjectNode game = observed.putObject("game"); game.put("pid", 7); game.put("creation_filetime", "18446744073709551615");
        ObjectNode budget = root.putObject("joint_budget_request"), intake = budget.putObject("intake"); intake.put("policy", "g2-m5-same-frame-intake-v1"); frame(intake);
        ArrayNode candidates = intake.putArray("candidates");
        ObjectNode snapshot = budget.putObject("snapshot"); frame(snapshot); snapshot.put("paused", true); snapshot.put("map_ready", true);
        ObjectNode gold = snapshot.putObject("played_character_gold"); gold.put("raw", 1_000_000); gold.put("scale", 100000); snapshot.putArray("active_wars");
        ObjectNode army = snapshot.putArray("player_armies").addObject(); army.put("army_id", 7); army.put("controllable", true);
        ArrayNode assessments = budget.putArray("assessments");
        for (int index = 0; index < 5; index++) {
            ObjectNode candidate = candidates.addObject(); candidate.put("candidate_id", "war" + index); candidate.put("domain", "war");
            ObjectNode assessment = assessments.addObject(); frame(assessment); assessment.put("candidate_id", "war" + index); assessment.put("benefit_units", 100 - index);
            for (String name : java.util.List.of("war_cost_units", "family_cost_units", "diplomacy_cost_units", "supply_cost_units", "long_term_cost_units")) assessment.put(name, 0);
            assessment.put("gold_raw", 1); assessment.put("projected_supply_margin_units", 1); claims(assessment, 7, "claim:" + index);
        }
        ObjectNode commitments = budget.putObject("commitments"); commitments.put("gold_raw", 0); commitments.put("pending_war_slots", 0); claims(commitments, -1, null);
        budget.put("gold_reserve_raw", 0); budget.put("max_active_wars", 5);
        ObjectNode intent = root.putArray("intents").addObject(); intent.put("action_id", "lifecycle-war0"); intent.put("candidate_id", "war0");
        ObjectNode expected = intent.putObject("expected"); expected.put("version", 1); expected.put("observer_schema", "xar.synthetic-observation/v1");
        ObjectNode value = expected.putArray("values").addObject(); value.put("field", "native_effect"); value.put("kind", "BOOLEAN"); value.put("value", true);
        root.putArray("external_facts"); return root;
    }
    public static ObjectNode fact(String actionId, String bodySha, String state, String scope, String domain, long armyId) {
        ObjectNode row = StrictJson.object(); row.put("schema", ProposalLifecycleCodec.FACT_SCHEMA); row.put("action_id", actionId); row.put("body_sha256", bodySha);
        row.set("origin", ProposalLifecycleCodec.observation(ProposalLifecycleCodec.decode(StrictJson.canonical(request()), source()).observed()));
        row.put("state", state); row.put("scope", scope); row.put("domain", domain);
        claims(row.putObject("claims"), armyId, null); row.set("original_evidence_ref", source().sourceRef().toJson()); return row;
    }
    private static void frame(ObjectNode row) { row.put("played_character_id", 1); row.put("native_revision", 2); row.put("date_raw", 3); row.put("snapshot_id", "synthetic:2"); row.put("revision", 4); row.put("episode_run_id", "synthetic-episode"); }
    private static void claims(ObjectNode row, long armyId, String key) {
        ArrayNode armies = row.putArray("army_ids"); if (armyId >= 0) armies.add(armyId); row.putArray("ally_character_ids"); row.putArray("character_ids"); ArrayNode keys = row.putArray("commitment_keys"); if (key != null) keys.add(key);
    }
}
