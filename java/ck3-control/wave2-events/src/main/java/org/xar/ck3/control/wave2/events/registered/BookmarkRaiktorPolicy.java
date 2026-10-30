package org.xar.ck3.control.wave2.events.registered;

import org.xar.ck3.control.wave2.events.unhandledevent.EventOptionAvailability;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.registered.RegistryJson.*;

/** Complete bookmark_raiktor_policy.py producer. Matching incomplete events never enter generic fallback. */
public final class BookmarkRaiktorPolicy {
    public static final String EVENT_KEY = "bookmark.1071";
    public enum Status { RECOMMENDED, BLOCKED, QUERY_REQUIRED }
    public record Input(ObjectValue context, ObjectValue snapshot, Map<BigInteger,ObjectValue> sameFrameAssessments,
            Set<String> actionSteps, Optional<String> crossRunFocus, boolean eventScopeQuerySupported) {
        public Input {
            Objects.requireNonNull(context); Objects.requireNonNull(snapshot);
            sameFrameAssessments = Map.copyOf(sameFrameAssessments); actionSteps = Set.copyOf(actionSteps);
            Objects.requireNonNull(crossRunFocus);
        }
    }
    public record Recommendation(Status status, Optional<BigInteger> nativeIndex, ObjectValue wire) {
        public Recommendation {
            Objects.requireNonNull(status); Objects.requireNonNull(nativeIndex); Objects.requireNonNull(wire);
            org.xar.ck3.control.contracts.StrictJson.require(nativeIndex.isPresent() == (status == Status.RECOMMENDED),
                "only a recommended dedicated event may carry an option");
        }
    }
    private BookmarkRaiktorPolicy() { }
    public static Optional<Recommendation> recommend(Input input) {
        Objects.requireNonNull(input);
        ObjectValue event = input.context(), snapshot = input.snapshot();
        if (!is(event.get("event_definition_key"), EVENT_KEY)) return Optional.empty();
        if (!is(event.get("status"), "available") || !is(event.get("window_match_count"), 1)
                || !object(snapshot.get("active_event")) || !is(get(snapshot.get("active_event"), "option_count"), 3))
            return result(blocked("raiktor_event_identity_or_option_count_drift"));
        BigInteger player = positiveCharacter(get(snapshot.get("played_character"), "character_id"));
        if (player == null || !player.equals(characterScope(event.get("root_scope"))))
            return result(blocked("raiktor_event_player_root_unavailable_or_mismatch"));
        if (!array(event.get("saved_scopes"))) return result(blocked("raiktor_event_saved_scopes_unavailable"));
        Map<String,BigInteger> named = new LinkedHashMap<>();
        for (Value row : seq(event.get("saved_scopes"))) {
            String name = text(get(row, "name"));
            if (!object(row) || name == null || !Set.of("byz_emperor", "raiktor").contains(name)) continue;
            BigInteger id = characterScope(get(row, "scope"));
            if (id == null || named.containsKey(name)) return result(blocked("raiktor_event_saved_character_scope_drift"));
            named.put(name, id);
        }
        if (!named.keySet().equals(Set.of("byz_emperor", "raiktor")) || player.equals(named.get("byz_emperor")))
            return result(blocked("raiktor_event_saved_character_scope_drift"));
        if (!array(event.get("options")) || seq(event.get("options")).size() != 3)
            return result(blocked("raiktor_event_options_unavailable_or_drifted"));
        Map<BigInteger,ObjectValue> options = new LinkedHashMap<>();
        for (Value row : seq(event.get("options"))) {
            BigInteger index = integer(get(row, "native_option_index"));
            if (!object(row) || index == null || options.putIfAbsent(index, obj(row)) != null)
                return result(blocked("raiktor_event_options_unavailable_or_drifted"));
        }
        if (!options.keySet().equals(Set.of(BigInteger.ZERO, BigInteger.ONE, BigInteger.TWO)))
            return result(blocked("raiktor_event_options_unavailable_or_drifted"));
        ObjectValue decline = options.get(BigInteger.TWO);
        if (!yes(decline.get("shown")) || !EventOptionAvailability.selectionAllowed(event,decline))
            return result(blocked("raiktor_no_war_option_not_legal"));
        Value gold = snapshot.get("played_character_gold");
        BigInteger goldRaw = integer(get(gold, "raw"));
        boolean goldKnown = goldRaw != null && is(get(gold, "scale"), 100_000);
        boolean conflict = !array(snapshot.get("active_wars")) || !seq(snapshot.get("active_wars")).isEmpty();
        BigInteger target = named.get("byz_emperor");
        ObjectValue assessment = input.sameFrameAssessments().get(target);
        boolean marginReady = false;
        BigInteger margin = null;
        if (assessment != null) {
            BigInteger actor = integer(assessment.get("actor_power_base_raw")), other = integer(assessment.get("target_power_total_raw"));
            if (actor != null && other != null && actor.signum() >= 0 && other.signum() >= 0) {
                margin = actor.subtract(other); marginReady = actor.multiply(BigInteger.valueOf(4)).compareTo(other.multiply(BigInteger.valueOf(5))) >= 0;
            }
        }
        ObjectValue claim = options.get(BigInteger.ZERO);
        boolean opportunity = yes(claim.get("shown")) && EventOptionAvailability.selectionAllowed(event,claim) && goldKnown
            && goldRaw.compareTo(BigInteger.valueOf(10_000_000)) >= 0 && !conflict
            && input.crossRunFocus().filter(Set.of("marriage", "succession")::contains).isEmpty();
        if (opportunity && assessment == null) {
            boolean declarable = array(snapshot.get("declarable_wars")) && seq(snapshot.get("declarable_wars")).stream()
                .anyMatch(row -> object(row) && eq(get(row, "target_character_id"), v(target)));
            String query = "query-war-entry-assessments-v1-1-" + target;
            if ((declarable || input.eventScopeQuerySupported()) && input.actionSteps().contains(query))
                return result(b().set("status", "query_required").set("reason", "read same-frame native Byzantine strategic power before a claim war")
                    .set("selected_step", query).set("selected_native_option_index", RetainedJson.NULL)
                    .set("target_character_id", target).set("raiktor_character_id", named.get("raiktor")).build());
        }
        if (opportunity && marginReady)
            return result(b().set("status", "recommended").set("reason", "source-reviewed claim war with a >=25% native own-power margin")
                .set("selected_native_option_index", 0).set("target_character_id", target).set("raiktor_character_id", named.get("raiktor"))
                .set("native_power_margin_raw", margin).set("source_capture_required_for_gen034_d", true).build());
        return result(b().set("status", "recommended")
            .set("reason", "decline the special war: budget, conflicting goals, option legality or same-frame own-power margin is not sufficient")
            .set("selected_native_option_index", 2).set("target_character_id", target).set("raiktor_character_id", named.get("raiktor"))
            .set("native_power_margin_raw", margin).set("native_power_observed", assessment != null)
            .set("source_capture_required_for_gen034_d", false).build());
    }
    private static BigInteger positiveCharacter(Value value) {
        BigInteger id = integer(value);
        return id != null && id.signum() > 0 && id.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0 ? id : null;
    }
    private static BigInteger characterScope(Value value) {
        Value identity = get(value, "typed_identity");
        return object(value) && is(get(value, "type_key"), "character") && object(identity) && is(get(identity, "status"), "available")
            ? positiveCharacter(get(identity, "character_id")) : null;
    }
    private static ObjectValue blocked(String reason) {
        return b().set("status", "blocked").set("reason", reason).set("selected_native_option_index", RetainedJson.NULL).build();
    }
    private static Optional<Recommendation> result(ObjectValue wire) {
        Status status = switch (str(wire.get("status"))) {
            case "recommended" -> Status.RECOMMENDED; case "blocked" -> Status.BLOCKED; case "query_required" -> Status.QUERY_REQUIRED;
            default -> throw new IllegalArgumentException("dedicated event producer status");
        };
        return Optional.of(new Recommendation(status, Optional.ofNullable(integer(wire.get("selected_native_option_index"))), wire));
    }
}
