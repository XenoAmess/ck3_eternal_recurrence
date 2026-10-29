package org.xar.ck3.control.wave2.planning.jointintake;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.wave2.planning.jointintake.IntakeWire.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Frame;

/** Wire adapters of the existing domain-approved producer results, before joint arbitration. */
final class FormalDomainAdapters {
    private FormalDomainAdapters() { }
    static Obj council(Frame frame, Obj source) {
        Obj decision = object(source.get("decision"), "council decision");
        require(new Text("council-composition-steward-v1").equals(decision.get("policy"))
                && List.of(new Text("ASSIGN_REQUIRED"), new Text("REPLACE_REQUIRED")).contains(decision.get("outcome"))
                && new Bool(true).equals(decision.get("action_routable"))
                && new Text("game.action.assign-councillor-v1").equals(decision.get("required_capability")), "action-ready steward decision required");
        Obj observation = object(source.get("observation"), "council observation");
        Obj observed = object(observation.get("snapshot"), "council snapshot"); Obj position = object(observation.get("position"), "council position");
        Obj expected = frameNode(frame);
        for (String key : List.of("snapshot_id", "native_revision", "date_raw")) equalsValue(observed.get(key), expected.get(key), "council frame " + key);
        equalsValue(observed.get("public_revision"), number(frame.revision()), "council public revision");
        equalsValue(observed.get("paused"), new Bool(true), "council paused");
        equalsValue(observation.get("owner_character_id"), number(frame.playedCharacterId()), "council actor");
        equalsValue(observation.get("candidate_collection_complete"), new Bool(true), "council candidates complete");
        Obj selected = object(decision.get("selected_candidate"), "selected steward");
        BigInteger selectedId = positive(selected.get("character_id"), "steward id"); Obj skill = object(selected.get("main_skill"), "steward skill");
        equalsValue(skill.get("key"), new Text("stewardship"), "steward skill key"); BigInteger skillValue = nonnegative(skill.get("value"), "steward skill value");
        List<Value> matched = array(observation.get("candidates"), "council candidates").stream()
                .filter(row -> row instanceof Obj candidate && number(selectedId).equals(candidate.get("character_id"))).toList();
        require(matched.size() == 1 && skill.equals(object(matched.getFirst(), "matched steward").get("main_skill")), "steward not uniquely observed");
        Value incumbent = presentOrNull(decision, "incumbent_character_id"), incumbentSkill = presentOrNull(decision, "incumbent_main_skill");
        require(Objects.equals(presentOrNull(position, "incumbent_character_id"), incumbent)
                && Objects.equals(presentOrNull(position, "incumbent_main_skill"), incumbentSkill), "steward incumbent crossed frame");
        if (new Text("REPLACE_REQUIRED").equals(decision.get("outcome"))) {
            positive(incumbent, "incumbent"); BigInteger previous = integer(object(incumbentSkill, "incumbent skill").get("value"), "incumbent skill value");
            require(skillValue.compareTo(previous) > 0, "steward replacement lacks measured gain");
        }
        Value previous = incumbentSkill instanceof Obj previousSkill ? presentOrNull(previousSkill, "value") : Nil.INSTANCE;
        return proposal(frame, "council:steward:" + selectedId, "council", "council-composition-steward-v1", BigInteger.ZERO, BigInteger.ZERO,
                Nil.INSTANCE, 0, List.of(), List.of(), List.of(selectedId), List.of("council-seat:councillor_steward"),
                obj(f("outcome", decision.get("outcome")), f("candidate_stewardship", number(skillValue)), f("incumbent_stewardship", previous)), Nil.INSTANCE);
    }
    static Obj construction(Frame frame, Obj source) {
        Obj query = object(source.get("query"), "construction query"); equalsValue(query.get("status"), new Text("selected"), "selected construction required");
        sourceFrame(query.get("source_frame"), frame, "actor_character_id"); Obj candidate = object(query.get("candidate"), "construction candidate");
        BigInteger barony = positive(candidate.get("barony_title_id"), "barony"), province = positive(candidate.get("province_id"), "province"), building = positive(candidate.get("building_type_id"), "building");
        BigInteger slot = nonnegative(candidate.get("slot_index"), "slot"), gold = positive(candidate.get("stock_gold_cost_raw"), "construction cost");
        BigInteger before = integer(candidate.get("gold_before_raw"), "construction treasury"); require(before.compareTo(gold) >= 0, "construction unaffordable quoted cost");
        return proposal(frame, "building:" + barony + ":" + building + ":" + slot, "building", "private-native-budgeted-construction-v1",
                gold, BigInteger.valueOf(20000000), Nil.INSTANCE, 0, List.of(), List.of(), List.of(), List.of("building-slot:" + barony + ":" + slot),
                obj(f("barony_title_id", number(barony)), f("province_id", number(province)), f("building_type_id", number(building)), f("slot_index", number(slot)),
                        f("gold_before_raw", number(before)), f("authored_monthly_income_hundredths", presentOrNull(candidate, "authored_monthly_income_hundredths"))), Nil.INSTANCE);
    }
    static Obj diplomacy(Frame frame, Obj source) {
        Obj candidate = object(source.get("candidate"), "gift candidate"); equalsValue(candidate.get("status"), new Text("selected"), "selected gift required");
        Obj choice = object(candidate.get("choice"), "gift choice");
        equalsValue(choice.get("snapshot_revision"), number(frame.nativeRevision()), "gift snapshot revision");
        equalsValue(choice.get("native_snapshot_revision"), number(frame.nativeRevision()), "gift native revision");
        equalsValue(choice.get("date_raw"), number(frame.dateRaw()), "gift date"); equalsValue(choice.get("player_character_id"), number(frame.playedCharacterId()), "gift actor");
        BigInteger faction = positive(choice.get("source_faction_id"), "faction"), recipient = positive(choice.get("recipient_character_id"), "gift recipient");
        BigInteger cost = positive(choice.get("gold_cost_raw"), "gift cost"), reserve = nonnegative(choice.get("minimum_gold_reserve_raw"), "gift reserve");
        BigInteger opinion = positive(choice.get("opinion_delta"), "gift opinion");
        return proposal(frame, "diplomacy:faction-gift:" + faction + ":" + recipient, "diplomacy", "faction-gift-v1", cost, reserve,
                Nil.INSTANCE, 0, List.of(), List.of(), List.of(recipient), List.of("faction-gift:" + faction + ":" + recipient),
                obj(f("source_faction_id", number(faction)), f("opinion_delta", number(opinion)), f("stock_threat_response", presentOrNull(candidate, "stock_threat_response"))), Nil.INSTANCE);
    }
    static Obj lifestyle(Frame frame, Obj source) {
        Obj query = object(source.get("query"), "lifestyle query"), decision = object(source.get("decision"), "lifestyle decision"), war = object(source.get("current_war_plan"), "current war plan");
        Value selectedStep = war.get("selected_step");
        require(new Text("one-life-turn-v1").equals(war.get("policy")) && (missingOrNull(selectedStep)
                || selectedStep instanceof Text step && step.value().startsWith("query-")), "formal war action has priority over lifestyle");
        Obj sourceFrame = object(query.get("source_frame"), "lifestyle source").with("episode_run_id", presentOrNull(query, "episode_run_id"));
        sourceFrame(sourceFrame, frame, "player_character_id");
        equalsValue(query.get("status"), new Text("available"), "lifestyle query status"); equalsValue(query.get("formal_precondition_status"), new Text("ready"), "lifestyle preconditions");
        equalsValue(decision.get("policy_id"), new Text("g2-lifestyle-wartime-stewardship-perk-v1"), "lifestyle policy"); equalsValue(decision.get("status"), new Text("recommend_action"), "lifestyle recommendation");
        Obj life = object(query.get("snapshot"), "lifestyle snapshot"), action = object(decision.get("selected_action"), "lifestyle action"), expected = object(action.get("expected"), "lifestyle expected");
        equalsValue(action.get("kind"), new Text("perk"), "lifestyle action kind");
        Obj identity = frameNode(frame);
        for (String key : List.of("snapshot_id", "episode_run_id", "native_revision", "date_raw")) {
            equalsValue(life.get(key), identity.get(key), "lifestyle snapshot " + key);
            equalsValue(expected.get("expected_" + key), identity.get(key), "lifestyle expected " + key);
        }
        equalsValue(life.get("public_revision"), number(frame.nativeRevision()), "lifestyle public revision");
        equalsValue(expected.get("expected_public_revision"), number(frame.nativeRevision()), "lifestyle expected public revision");
        equalsValue(life.get("player_character_id"), number(frame.playedCharacterId()), "lifestyle actor");
        equalsValue(expected.get("expected_player_character_id"), number(frame.playedCharacterId()), "lifestyle expected actor");
        equalsValue(action.get("target_key"), new Text("cutting_corners_perk"), "lifestyle target"); equalsValue(action.get("target_lifestyle_key"), new Text("stewardship_lifestyle"), "lifestyle tree");
        Obj readiness = object(life.get("readiness"), "lifestyle readiness");
        for (String key : List.of("current_focus_ready", "lifestyle_progress_ready", "owned_perks_ready", "legal_perk_candidates_ready", "same_frame_ready")) equalsValue(readiness.get(key), new Bool(true), key);
        Obj focus = object(life.get("current_focus"), "current focus"), progress = object(life.get("current_lifestyle_progress"), "lifestyle progress"), legal = object(life.get("legal_perk_candidates"), "legal perks");
        for (Obj row : List.of(focus, progress)) { equalsValue(row.get("presence"), new Text("present"), "lifestyle presence"); equalsValue(row.get("lifestyle_key"), new Text("stewardship_lifestyle"), "lifestyle current tree"); }
        text(focus.get("key"), "focus key"); BigInteger points = positive(progress.get("unspent_perk_points"), "perk points"), used = nonnegative(progress.get("used_perk_points"), "used points");
        List<String> owned = new ArrayList<>(); for (Value value : array(life.get("owned_perk_keys"), "owned perks")) owned.add(text(value, "owned perk"));
        require(!owned.contains("cutting_corners_perk"), "perk already owned");
        long matches = array(legal.get("items"), "legal perk items").stream().filter(value -> value instanceof Obj row
                && new Text("cutting_corners_perk").equals(row.get("key")) && new Text("stewardship_lifestyle").equals(row.get("lifestyle_key"))).count();
        require(matches == 1, "perk not uniquely native legal");
        return proposal(frame, "lifestyle:perk:cutting_corners_perk", "lifestyle", "g2-lifestyle-wartime-stewardship-perk-v1", BigInteger.ZERO, BigInteger.ZERO,
                Nil.INSTANCE, 0, List.of(), List.of(), List.of(), List.of("lifestyle-perk-point:stewardship_lifestyle"), obj(f("current_focus_key", focus.get("key")),
                        f("target_lifestyle_key", new Text("stewardship_lifestyle")), f("target_perk_key", new Text("cutting_corners_perk")), f("unspent_perk_points", number(points)),
                        f("used_perk_points", number(used)), f("date_advance_expected", new Bool(false)), f("war_plan_selected_step", missingOrNull(selectedStep) ? Nil.INSTANCE : selectedStep)), Nil.INSTANCE);
    }

    // Local input aliases deliberately leave shared parser/encoder and internal result invariants unmarked.
    private static void require(boolean condition, String reason) { IntakeWire.domain(condition, reason); }
    private static Obj object(Value value, String name) { return IntakeWire.inputObject(value, name); }
    private static List<Value> array(Value value, String name) { return IntakeWire.inputArray(value, name); }
    private static String text(Value value, String name) { return IntakeWire.inputText(value, name); }
    private static BigInteger integer(Value value, String name) { return IntakeWire.inputInteger(value, name); }
    private static BigInteger nonnegative(Value value, String name) { return IntakeWire.inputNonnegative(value, name); }
    private static boolean bool(Value value, String name) { return IntakeWire.inputBool(value, name); }
}
