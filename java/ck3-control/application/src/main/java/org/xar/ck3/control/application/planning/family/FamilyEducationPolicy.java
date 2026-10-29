package org.xar.ck3.control.application.planning.family;

import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import static org.xar.ck3.control.application.planning.family.FamilyPorts.*;
import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsComposer;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceCodec;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationRequestPreference;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsAssembly;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsCodec;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsModel;
import org.xar.ck3.control.wave3.governance.guardianskills.GuardianSkillsCodec;
import org.xar.ck3.control.wave3.governance.guardianskills.GuardianSkillInputs;

/** Real relation -> needs -> focus -> observed pair -> preference -> selected/all-off preflight. */
final class FamilyEducationPolicy {
    private FamilyEducationPolicy() { }
    static Decision evaluate(FamilyOrdinaryPolicy owner, PlanningRequest request, Draft previous, Obj relation, Obj detail, boolean focusEnabled) {
        if (!"life-advance".equals(FamilyOrdinaryPolicy.selected(previous))) return owner.annotate(previous, detail);
        if (!(relation.get("family_generation_education_decision_inputs_v1") instanceof Obj decision)) return owner.annotate(previous, detail);
        Obj needs = decode(EducationNeedsComposer.composeDecision(bytes(decision), optionalBytes(relation.get("current_child_relation_materials_v1")),
                optionalBytes(relation.get("current_child_education_provider_inputs_v1")), optionalBytes(relation.get("current_child_education_provider_inputs_source_v1"))));
        detail = detail.with("family_education_inputs", decision).with("family_education_needs", needs);
        if (focusEnabled) {
            Decision focus = focus(owner, request, previous, needs, detail);
            if (!(focus instanceof Replace replaced) || !replaced.draft().command().equals(previous.command())) return focus;
            detail = replaced.draft().detail();
        }
        List<Value> observations = new ArrayList<>(); List<Value> cadence = new ArrayList<>();
        Map<BigInteger, Optional<FamilyGuardianCadence.Scope>> scopes = new LinkedHashMap<>();
        FamilyGuardianCadence negative = owner.guardianCadence();
        List<EducationOptionsAssembly.Observation> assembly = new ArrayList<>(); Set<BigInteger> seen = new HashSet<>();
        for (Value raw : array(needs.get("rows"))) {
            Obj child = object(raw); BigInteger id = positive(child.get("raw_character_id")); if (!seen.add(id)) continue;
            var scope = negative.scope(request.observations().snapshot(), child, relation.get("heir_character_id")); scopes.put(id, scope);
            var deferred = negative.deferred(scope);
            if (deferred.isPresent()) {
                cadence.add(deferred.get());
                observations.add(obj("child_full_id", new IntegerValue(id), "needs", child,
                        "default_request_intent", Nil.INSTANCE, "request_preference_pair", Nil.INSTANCE,
                        "request_attempts", rows(List.of()), "guardian_negative_cadence", deferred.get()));
                assembly.add(new EducationOptionsAssembly.Observation(Optional.empty(), Optional.empty()));
                continue;
            }
            Obj query = owner.read(request, Query.EDUCATION_CONTEXT, obj("interaction_key", t("educate_child_interaction"), "recipient_id", new IntegerValue(id),
                    "expected_revision", request.observations().snapshot().get("revision")));
            Obj context = object(query.get("character_interaction_ordinary_context"));
            Obj candidate = decode(EducationNeedsComposer.requestCandidate(bytes(child), bytes(context)));
            Obj observation = obj("child_full_id", new IntegerValue(id), "needs", child, "candidate", candidate, "default_query", query,
                    "default_request_intent", Nil.INSTANCE, "request_preference_pair", Nil.INSTANCE, "request_attempts", rows(List.of()),
                    "default_request_guardian_focus_skills", skills(child, context));
            Optional<EducationOptionsModel.Pair> pair = Optional.empty(); Optional<EducationOptionsAssembly.RequestIntent> intent = Optional.empty();
            if (yes(candidate.get("available"))) {
                pair = Optional.of(new EducationOptionsModel.Pair(id.longValueExact(), positive(candidate.get("guardian_full_id")).longValueExact()));
                var options = EducationOptionsCodec.decode(bytes(obj("schema", t(EducationOptionsCodec.INPUT_SCHEMA), "context", context)));
                intent = EducationOptionsAssembly.selectedIntent(pair, options.rows());
                Obj identity = obj("child_full_id", new IntegerValue(id), "guardian_full_id", candidate.get("guardian_full_id"));
                observation = observation.with("request_preference_pair", identity);
                if (intent.isPresent()) observation = observation.with("default_request_intent", intent(intent.get()));
            }
            observations.add(observation); assembly.add(new EducationOptionsAssembly.Observation(pair, intent));
        }
        List<Value> preferenceInputs = new ArrayList<>();
        for (Value raw : observations) {
            Obj observation = object(raw); Value intent = observation.get("default_request_intent");
            preferenceInputs.add(observation.with("default_request_intent", intent == Nil.INSTANCE ? observation.get("request_preference_pair") : intent));
        }
        var preference = EducationRequestPreference.order(EducationPreferenceCodec.decode(bytes(obj("schema", t(EducationPreferenceCodec.INPUT_SCHEMA), "observations", rows(preferenceInputs)))));
        Obj preferenceJson = decode(EducationPreferenceCodec.encodeResult(preference))
                .with("input_basis", t("observed post-final pair identity; missing default option keys remain unknown"))
                .with("attempt_order", t("all observed selected-option intents, then one explicit all-off intent per pair"));
        List<Value> candidates = new ArrayList<>();
        for (Value raw : array(preferenceJson.get("candidates"))) {
            Obj candidate = object(raw); int index = integer(candidate.get("observation_index")).intValueExact();
            candidates.add(candidate.with("intent_identity_source", t(object(observations.get(index)).get("default_request_intent") == Nil.INSTANCE
                    ? "observed_pair_only" : "observed_selected_options")));
        }
        preferenceJson = preferenceJson.with("candidates", rows(candidates));
        // Only actual pair observations are present in this existing preference's ordered indices.
        for (var attempt : EducationOptionsAssembly.attempts(assembly, preference.orderedObservationIndices())) {
            int index = attempt.observationIndex(); Obj observation = object(observations.get(index)); Obj child = object(observation.get("needs"));
            Obj intent = intent(attempt.intent());
            Obj query = owner.read(request, Query.EDUCATION_CONTEXT, intent.with("expected_revision", request.observations().snapshot().get("revision")));
            Obj context = object(query.get("character_interaction_ordinary_context"));
            Obj candidate = decode(EducationNeedsComposer.requestCandidate(bytes(child), bytes(context)));
            Obj review = FamilyEducationReview.prepare(query, request.observations().snapshot(), intent);
            Obj skills = skills(child, context);
            Obj evidence = obj("variant", t(attempt.variant().wire()), "request_intent", intent, "query", query,
                    "semantic_request_review", review, "candidate", candidate, "request_guardian_focus_skills", skills);
            List<Value> attempts = new ArrayList<>(array(observation.get("request_attempts"))); attempts.add(evidence);
            observations.set(index, observation.with("request_attempts", rows(attempts)).with("selected_request_query", query).with("semantic_request_review", review)
                    .with("selected_request_candidate", candidate).with("selected_request_guardian_focus_skills", skills));
            if (yes(context.get("ready_to_initiate")) && yes(context.get("can_send")) && "available".equals(string(review.get("status")))) {
                negative.selectableIntentObserved();
                return owner.select(request, previous, "initiate-character-interaction-ordinary-v1", intent.with("source_query", query).with("semantic_request_review", review),
                        detail.with("family_education_observations", rows(observations)).with("family_education_request", intent)
                                .with("family_education_request_variant", t(attempt.variant().wire())).with("family_education_request_preference", preferenceJson),
                        "family_education_ordinary_submission", "submit the preferred native-ready ward and guardian education intent", Purpose.WORLD_ACTION);
            }
        }
        for (Value raw : observations) {
            Obj observation = object(raw); if (observation.get("guardian_negative_cadence") != null) continue;
            BigInteger id = positive(observation.get("child_full_id"));
            negative.observe(id, scopes.get(id), observation.get("default_query"),
                    new Arr(array(observation.get("request_attempts")))).ifPresent(cadence::add);
        }
        return owner.annotate(previous, detail.with("family_education_observations", rows(observations)).with("family_education_request_preference", preferenceJson)
                .with("family_education_guardian_negative_cadence_v1", rows(cadence)));
    }
    private static Obj skills(Obj child, Obj context) {
        return decode(GuardianSkillsCodec.encodeProjection(GuardianSkillInputs.project(GuardianSkillsCodec.decode(bytes(
                obj("schema", t(GuardianSkillsCodec.INPUT_SCHEMA), "needs", child, "context", context))))));
    }
    private static Obj intent(EducationOptionsAssembly.RequestIntent value) {
        return obj("interaction_key", t("educate_child_interaction"), "recipient_id", n(value.pair().childFullId()),
                "child_full_id", n(value.pair().childFullId()), "guardian_full_id", n(value.pair().guardianFullId()),
                "requested_option_keys", new Arr(value.requestedOptionKeys().stream().<Value>map(Text::new).toList()));
    }
    private static byte[] optionalBytes(Value value) { return value == null || value == Nil.INSTANCE ? null : bytes(value); }
    private record Signature(boolean affinity, boolean disaffinity) { }
    private record Focus(int sourceIndex, String key, Signature availability, Integer known, Obj original) { }
    static List<String> focusKeys(Obj needs) {
        List<Focus> source = new ArrayList<>(); Map<Signature, List<Focus>> groups = new LinkedHashMap<>();
        for (Value raw : array(needs.get("stock_skill_options"))) {
            Obj option = object(raw), affinity = object(option.get("childhood_affinity")), disaffinity = object(option.get("childhood_disaffinity"));
            boolean a = org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(affinity.get("available"), "affinity availability");
            boolean d = org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(disaffinity.get("available"), "disaffinity availability");
            int score = 0; if (a && org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(affinity.get("raw_value"), "affinity")) score += 20;
            if (d && org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(disaffinity.get("raw_value"), "disaffinity")) score -= 20;
            Focus focus = new Focus(source.size(), text(option.get("focus_key")), new Signature(a, d), a || d ? score : null, option);
            source.add(focus); groups.computeIfAbsent(focus.availability(), ignored -> new ArrayList<>()).add(focus);
        }
        groups.values().forEach(group -> group.sort(Comparator.comparing((Focus focus) -> focus.known() == null ? 0 : -focus.known()).thenComparingInt(Focus::sourceIndex)));
        Map<Signature, Integer> positions = new LinkedHashMap<>(); List<String> result = new ArrayList<>();
        for (Focus focus : source) {
            int index = positions.getOrDefault(focus.availability(), 0); positions.put(focus.availability(), index + 1);
            result.add(groups.get(focus.availability()).get(index).key());
        }
        return List.copyOf(result);
    }
    private static Decision focus(FamilyOrdinaryPolicy owner, PlanningRequest request, Draft previous, Obj needs, Obj detail) {
        Obj snapshot = request.observations().snapshot(); Optional<Obj> pending = FamilyHistory.focusPending(request.observations().history(), snapshot);
        Obj state = obj("policy", t("source_informed_childhood_focus_preference_12004.v1"), "pending", pending.<Value>map(value -> value).orElse(Nil.INSTANCE),
                "receipt", Nil.INSTANCE, "observations", rows(List.of()));
        if (pending.isPresent()) {
            Obj pre = object(pending.get().get("pre_frame"));
            if (integer(snapshot.get("native_revision")).compareTo(integer(pre.get("native_revision"))) <= 0)
                return owner.annotate(previous, detail.with("family_child_education_focus", state));
            Obj receipt = owner.read(request, Query.CHILD_FOCUS_RECEIPT, obj("pending", pending.get(), "expected_revision", snapshot.get("revision")));
            state = state.with("receipt", receipt);
            if (!"observed_applied".equals(string(receipt.get("status"))) || !yes(receipt.get("observed_applied")))
                return owner.annotate(previous, detail.with("family_child_education_focus", state));
            state = state.with("pending", Nil.INSTANCE).with("observed_applied", receipt);
        }
        Set<BigInteger> seen = new HashSet<>(); List<Value> observations = new ArrayList<>();
        for (Value raw : array(needs.get("rows"))) {
            Obj child = object(raw); BigInteger id = positive(child.get("raw_character_id")); if (!seen.add(id)) continue;
            List<String> keys = focusKeys(child); List<Value> queries = new ArrayList<>();
            Obj observation = obj("child_full_id", new IntegerValue(id), "needs", child, "focus_source_frame", child.get("frame"),
                    "ordered_target_keys", new Arr(keys.stream().<Value>map(Text::new).toList()), "queries", rows(List.of()));
            for (String key : keys) {
                Obj query = owner.read(request, Query.CHILD_FOCUS, obj("child_full_id", new IntegerValue(id), "target_key", t(key), "expected_revision", snapshot.get("revision")));
                queries.add(query); Obj focus = object(query.get("current_focus"));
                if (yes(focus.get("available")) && "present".equals(string(focus.get("presence")))) {
                    observation = observation.with("current_focus_present", new Bool(true)); break;
                }
                if ("available".equals(string(query.get("status"))) && yes(query.get("native_legal")) && yes(focus.get("available")) && "absent".equals(string(focus.get("presence")))) {
                    observations.add(observation.with("queries", rows(queries)));
                    return owner.select(request, previous, "private-select-child-education-focus-v1", obj("query", query),
                            detail.with("family_child_education_focus", state.with("observations", rows(observations))).with("family_child_education_focus_query", query),
                            "family_child_education_focus_submission", "select the preferred native-legal focus for the observed child", Purpose.WORLD_ACTION);
                }
            }
            observations.add(observation.with("queries", rows(queries)));
        }
        return owner.annotate(previous, detail.with("family_child_education_focus", state.with("observations", rows(observations))));
    }
    /** Exact selection/option semantics. The command preparation owner still revalidates build/source and materialization. */
    static Obj review(Obj query, Obj snapshot, Obj intent) {
        return FamilyEducationReview.prepare(query, snapshot, intent);
    }
}
