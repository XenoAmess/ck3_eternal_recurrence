package org.xar.ck3.control.application.planning.family;

import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import static org.xar.ck3.control.application.planning.family.FamilyPorts.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave3.governance.betrothalvalue.BetrothalValueCodec;
import org.xar.ck3.control.wave3.governance.betrothalvalue.BetrothalValuePolicy;
import org.xar.ck3.control.governance.marriage.MarriageCodec;
import org.xar.ck3.control.governance.marriage.MarriagePolicy;

/** Pure original pre-send pending producer. It never submits, creates an empty ledger, or clears UNKNOWN. */
public final class FamilyPendingProducer {
    private FamilyPendingProducer() { }
    public enum Branch {
        HEIR("submit-observed-first-heir-marriage-v1-private", Slot.FAMILY, "xar.ck3.observed-first-heir-marriage-private-action.v1"),
        FULFILLMENT("submit-current-first-heir-betrothal-fulfillment-v1-private", Slot.FAMILY, "xar.ck3.observed-first-heir-marriage-private-action.v1"),
        MATRILINEAL("submit-player-child-matrilineal-marriage-v1-private", Slot.CHILD_MATRILINEAL, "xar.ck3.player-child-matrilineal-private-action.v1"),
        DEFAULT("submit-player-child-default-marriage-v1-private", Slot.DEFAULT_MARRIAGE, "xar.ck3.player-child-default-private-action.v1");
        private final OperationKey operation; private final Slot slot; private final String schema;
        Branch(String operation, Slot slot, String schema) { this.operation = new OperationKey(operation); this.slot = slot; this.schema = schema; }
        public OperationKey operation() { return operation; }
        public Slot slot() { return slot; }
        public String schema() { return schema; }
    }
    public record State(Obj family, Obj matrilineal, Obj childDefault) {
        public State { Objects.requireNonNull(family); Objects.requireNonNull(matrilineal); Objects.requireNonNull(childDefault); }
        public Obj body(Slot slot) { return switch (slot) { case FAMILY -> family; case CHILD_MATRILINEAL -> matrilineal; case DEFAULT_MARRIAGE -> childDefault; default -> throw new IllegalArgumentException("family slot required"); }; }
    }
    public record Produced(Branch branch, Obj body, Obj pending) {
        public Produced { Objects.requireNonNull(branch); Objects.requireNonNull(body); Objects.requireNonNull(pending); }
    }
    public static Set<OperationKey> operations() { return Set.of(Branch.HEIR.operation(), Branch.FULFILLMENT.operation(), Branch.MATRILINEAL.operation(), Branch.DEFAULT.operation()); }
    public static boolean supports(ActionCommand command) { Objects.requireNonNull(command); return operations().contains(command.operation()); }
    public static Branch branch(OperationKey operation) {
        for (Branch branch : Branch.values()) if (branch.operation().equals(operation)) return branch;
        throw new IllegalArgumentException("not a family pre-intent operation");
    }
    public static Produced produce(ActionCommand command, Obj snapshot, BridgeIdentity bridge, State state, Obj preparedPlan,FamilyNativePreparation.MaterializedSend send) {
        Objects.requireNonNull(command); Objects.requireNonNull(snapshot); Objects.requireNonNull(bridge); Objects.requireNonNull(state);
        FamilyNativePreparation.requireCommandFrame(command, snapshot);
        var intent = FamilyMarriageIntent.fromJson(command.arguments());
        if (!intent.step().equals(command.operation().value())) throw new IllegalArgumentException("actual private intent differs from command operation");
        Objects.requireNonNull(send);
        if(send.senderId()!=intent.actorId()||send.recipientId()!=intent.recipientId()||send.secondaryActorId().isEmpty()||send.secondaryRecipientId().isEmpty()
                ||send.secondaryActorId().getAsLong()!=intent.subjectId()||send.secondaryRecipientId().getAsLong()!=intent.candidateId())
            throw new IllegalArgumentException("actual materialized private send roles differ from immutable intent");
        var actual = derive(intent, snapshot, bridge, state, preparedPlan);
        Obj pending = actual.pending().with("java_action_id", t(command.actionId())).with("java_preparation_schema",t(FamilyNativePreparation.MaterializedSend.SCHEMA))
                .with("native_send_context",send.toJson());
        return new Produced(actual.branch(), actual.body().with("pending", pending), pending);
    }
    /** Pure complete validation; construction or planning_proof never grants native or writer qualification. */
    public static void validate(FamilyMarriageIntent intent, Obj snapshot, BridgeIdentity bridge, State state, Obj preparedPlan) {
        derive(intent, snapshot, bridge, state, preparedPlan);
    }
    private static Produced derive(FamilyMarriageIntent intent, Obj snapshot, BridgeIdentity bridge, State state, Obj plan) {
        Objects.requireNonNull(intent);Objects.requireNonNull(snapshot);Objects.requireNonNull(bridge);Objects.requireNonNull(state);Objects.requireNonNull(plan);
        Branch branch = branch(new OperationKey(intent.step()));
        if (!FamilyMarriagePreparationReview.SCHEMA.equals(string(plan.get("schema")))) throw new IllegalArgumentException("actual prepared family plan version is required; planning proof is not preparation");
        for (Slot slot : List.of(Slot.FAMILY, Slot.CHILD_MATRILINEAL, Slot.DEFAULT_MARRIAGE))
            FamilyDomainSource.validate(slot, org.xar.ck3.control.continuity.ContinuityJson.canonical(
                    org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(state.body(slot)), org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES));
        Obj ledger = state.body(branch.slot());
        if (ledger.get("pending") != Nil.INSTANCE) throw new IllegalArgumentException("family unresolved pending cannot be replaced or replayed");
        if (!t(intent.step()).equals(plan.get("selected_step"))) throw new IllegalArgumentException("pending operation differs from actual freshly prepared plan");
        Obj pending = switch (branch) {
            case HEIR -> heir(snapshot, bridge, state, plan);
            case FULFILLMENT -> fulfillment(snapshot, bridge, ledger, plan);
            case MATRILINEAL, DEFAULT -> child(branch, snapshot, bridge, state, plan);
        };
        requireIntent(intent, branch, snapshot, plan, pending);
        return new Produced(branch, ledger.with("pending", pending), pending);
    }
    private static void requireIntent(FamilyMarriageIntent intent, Branch branch, Obj snapshot, Obj plan, Obj pending) {
        if (!eq(object(snapshot.get("played_character")).get("character_id"), n(intent.actorId()))
                || !eq(pending.get("heir_character_id"), n(intent.subjectId())) || !eq(pending.get("candidate_character_id"), n(intent.candidateId()))
                || !eq(pending.get("recipient_character_id"), n(intent.recipientId()))) throw new IllegalArgumentException("fresh prepared roles differ from the immutable private intent");
        Value matrilineal = branch == Branch.HEIR ? object(pending.get("selected_value_projection")).get("matrilineal_option_selected") : pending.get("matrilineal_option_selected");
        if (!new Bool(intent.matrilineal()).equals(matrilineal)) throw new IllegalArgumentException("fresh native selected option differs from the immutable intent");
        if (branch == Branch.HEIR) {
            List<Integer> comparison = array(object(plan.get("family_marriage_projection")).get("rows")).stream().map(FamilyJson::object)
                    .map(row -> positive(row.get("candidate_character_id")).intValueExact()).toList();
            if (!comparison.equals(intent.comparisonCandidateIds())) throw new IllegalArgumentException("fresh complete five-row order differs from the requested comparison");
        }
    }
    private static Obj base(Branch branch, Obj snapshot, BridgeIdentity bridge, Value subject, Value candidate, Value recipient) {
        positive(subject); positive(candidate); positive(recipient);
        if (eq(subject, candidate)) throw new IllegalArgumentException("family proposal pair must differ");
        return obj("schema", t(branch.schema()), "status", t("receipt_pending"), "material_result", new Bool(false),
                "submission_state", t("may_have_submitted"), "pre_native_revision", snapshot.get("native_revision"),
                "source_date_raw", snapshot.get("date_raw"), "episode_run_id", snapshot.get("episode_run_id"),
                "played_character_id", object(snapshot.get("played_character")).get("character_id"),
                "heir_character_id", subject, "candidate_character_id", candidate, "recipient_character_id", recipient,
                "source_bridge_pid", n(bridge.pid()), "source_bridge_creation_date", t(bridge.creationDate()));
    }
    private static Obj heir(Obj snapshot, BridgeIdentity bridge, State state, Obj plan) {
        Obj legality = object(plan.get("family_marriage_legality")), choice = object(plan.get("family_marriage_choice"));
        Obj diagnostic = object(plan.get("family_marriage_private_diagnostic")); Value candidate = choice.get("candidate_character_id");
        FamilyOrdinaryPolicy.requireSameNative(legality, snapshot);
        Obj legal = unique(array(legality.get("native_legal_candidates")), "candidate_character_id", candidate);
        Obj row = unique(array(diagnostic.get("rows")), "candidate_character_id", candidate);
        if (!eq(diagnostic.get("selected_candidate_character_id"), candidate) || !eq(diagnostic.get("native_revision"), legality.get("native_revision"))
                || !eq(diagnostic.get("legality_query_sequence"), legality.get("query_sequence")) || !eq(diagnostic.get("date_raw"), snapshot.get("date_raw"))
                || !eq(diagnostic.get("episode_run_id"), snapshot.get("episode_run_id")) || !eq(diagnostic.get("exact_ck3_build"), legality.get("exact_ck3_build"))
                || !"xar.ck3.first-heir-candidate-alliance-projection.v1".equals(string(diagnostic.get("source_projection_schema")))
                || !array(row.get("rejection_reasons")).isEmpty()) throw new IllegalArgumentException("first-heir selected final proof changed");
        Value recipient = legal.get("recipient_matchmaker_character_id"); positive(recipient);
        if (!eq(row.get("recipient_character_id"), recipient) || !eq(row.get("recipient_matchmaker_character_id"), recipient))
            throw new IllegalArgumentException("first-heir selected recipient changed");
        Obj relation = object(plan.get("family_marriage_current_relationship"));
        if (!"available".equals(string(relation.get("status"))) || !yes(relation.get("bilateral_verified")) || !unpartnered(relation)
                || !eq(relation.get("native_revision"), snapshot.get("native_revision"))
                || !eq(relation.get("heir_character_id"), legality.get("observed_first_heir_character_id"))
                || !eq(row.get("heir_betrothed_character_id"), relation.get("betrothed_character_id"))
                || !eq(row.get("heir_primary_spouse_character_id"), relation.get("primary_spouse_character_id"))
                || !eq(row.get("heir_spouse_count"), n(array(relation.get("spouse_character_ids")).size())))
            throw new IllegalArgumentException("first-heir same-frame bilateral relation changed");
        Value actor = object(snapshot.get("played_character")).get("character_id");
        List<Obj> pairs = array(row.get("possible_alliance_pairs")).stream().map(FamilyJson::object)
                .filter(pair -> eq(pair.get("first_character_id"), actor) && eq(pair.get("second_character_id"), recipient)).toList();
        Value priorAllied = pairs.size() == 1 && pairs.get(0).get("already_allied") instanceof Bool b ? b : Nil.INSTANCE;
        boolean alliance = pairs.stream().anyMatch(pair -> no(pair.get("already_allied")) && yes(pair.get("both_have_realm_data")) && yes(pair.get("would_attempt_if_accepted")));
        if (!eq(choice.get("realm_alliance_attempt_if_accepted"), new Bool(alliance))) throw new IllegalArgumentException("first-heir prospective alliance claim changed");
        Obj projection = selectedProjection(snapshot, legality, diagnostic, row, choice, recipient);
        Arr rejected = ids(plan.get("family_marriage_rejected_candidate_ids"), false);
        if (array(rejected).contains(candidate)) throw new IllegalArgumentException("previously refused pair cannot be resent");
        Obj resolved = state.family().get("resolved") instanceof Obj value ? value : null;
        if (resolved != null && sameEpisode(resolved, snapshot) && eq(resolved.get("heir_character_id"), relation.get("heir_character_id"))
                && oneOf(resolved.get("status"), "refused", "invalidated")) {
            Value priorRejected = resolved.get("rejected_candidate_ids");
            if (priorRejected == null) priorRejected = rows(List.of(resolved.get("candidate_character_id")));
            if (!bridge.matches(resolved, "post_") || !new HashSet<>(array(rejected)).equals(new HashSet<>(array(ids(priorRejected, false)))))
                throw new IllegalArgumentException("first-heir refusal disposition changed");
        } else if (!array(rejected).isEmpty()) throw new IllegalArgumentException("first-heir refusal history lacks actual source");
        Obj pending = base(Branch.HEIR, snapshot, bridge, legality.get("observed_first_heir_character_id"), candidate, recipient)
                .with("preproposal_played_has_recipient_alliance", priorAllied).with("preproposal_realm_alliance_attempt_if_accepted", new Bool(alliance))
                .with("selected_value_projection", projection).with("prior_rejected_candidate_ids", rejected);
        if (choice.get("wartime_resource_context") instanceof Obj wartime) {
            requireWar(snapshot, wartime, List.of(actor, relation.get("heir_character_id"), candidate, recipient));
            pending = pending.with("wartime_resource_context", wartime);
        }
        return pending;
    }
    private static Obj selectedProjection(Obj snapshot, Obj legality, Obj diagnostic, Obj row, Obj choice, Value recipient) {
        Obj projection = obj("schema", t("xar.ck3.first-heir-marriage-selected-value-projection.v1"), "evidence_kind", t("preproposal_native_projection"),
                "exact_ck3_build", legality.get("exact_ck3_build"), "source_projection_schema", diagnostic.get("source_projection_schema"),
                "source_native_revision", legality.get("native_revision"), "source_legality_query_sequence", legality.get("query_sequence"),
                "source_date_raw", snapshot.get("date_raw"), "source_episode_run_id", snapshot.get("episode_run_id"),
                "played_character_id", object(snapshot.get("played_character")).get("character_id"), "heir_character_id", legality.get("observed_first_heir_character_id"),
                "candidate_character_id", choice.get("candidate_character_id"), "recipient_character_id", recipient);
        List<Value> missing = new ArrayList<>();
        for (String field : SELECTED_FIELDS) { Value value = nil(row.get(field)); projection = projection.with(field, value); if (value == Nil.INSTANCE) missing.add(t(field)); }
        for (String field : List.of("candidate_betrothed_character_id", "candidate_primary_spouse_character_id", "candidate_spouse_character_ids")) projection = projection.with(field, nil(row.get(field)));
        projection = projection.with("child_dynasty_prediction_basis_fields", strings(List.of("heir_dynasty_id", "candidate_dynasty_id", "heir_sex_selector_raw", "candidate_sex_selector_raw", "effective_matrilineal_if_accepted")))
                .with("child_dynasty_prediction_status", t("basis_only_unpriced")).with("predicted_child_dynasty_id", Nil.INSTANCE)
                .with("unobserved_at_submission", strings(List.of("actual_marriage_or_betrothal_result", "native_child_dynasty_result", "future_child_identity_and_dynasty", "actual_alliance_result")))
                .with("missing_preproposal_fields", rows(missing));
        if (choice.get("native_reproductive_branch_preference_v1") instanceof Obj preference) projection = projection.with("native_reproductive_branch_preference_v1", preference);
        if (choice.get("native_child_house_preview") instanceof Obj preview) {
            projection = projection.with("native_child_house_preview", preview).with("child_dynasty_prediction_status", t("native_preview"))
                    .with("predicted_child_dynasty_id", object(preview.get("native_child_house_preview")).get("dynasty_id"))
                    .with("unobserved_at_submission", strings(List.of("actual_marriage_or_betrothal_result", "future_child_identity_and_dynasty", "actual_alliance_result")));
        }
        return projection;
    }
    private static final List<String> SELECTED_FIELDS = List.of("played_house_id", "played_dynasty_id", "heir_house_id", "heir_dynasty_id", "candidate_house_id", "candidate_dynasty_id",
            "heir_sex_selector_raw", "candidate_sex_selector_raw", "matrilineal_option_selected", "effective_matrilineal_if_accepted", "predicted_outcome_if_accepted", "heir_is_adult", "candidate_is_adult",
            "heir_adult_measure_raw", "candidate_adult_measure_raw", "heir_adult_threshold_raw", "candidate_adult_threshold_raw", "grand_wedding_option_selected", "heir_native_fertility", "candidate_native_fertility",
            "native_candidate_fertility_floor_raw", "candidate_native_fertility_floor_comparison_v1", "heir_native_scorer_age_override_raw", "candidate_native_scorer_age_override_raw", "native_candidate_scorer_age_upper_raw",
            "heir_native_scorer_effective_age_v1", "candidate_native_scorer_effective_age_v1", "candidate_native_scorer_age_branch_v1");
    private static Obj fulfillment(Obj snapshot, BridgeIdentity bridge, Obj ledger, Obj plan) {
        Obj relation = object(plan.get("current_betrothal_relationship")), choice = object(plan.get("current_betrothal_choice"));
        Obj evaluated = decode(BetrothalValueCodec.encodeChoice(BetrothalValuePolicy.evaluate(BetrothalValueCodec.decode(bytes(
                obj("schema", t(BetrothalValueCodec.SCHEMA), "snapshot", snapshot, "relationship", relation))))));
        if (!"selected".equals(string(choice.get("status"))) || !choice.equals(evaluated)) throw new IllegalArgumentException("betrothal selected fixed-pair value changed");
        if (ledger.get("resolved") instanceof Obj resolved && resolved.get("source_pending") instanceof Obj previous
                && yes(previous.get("fulfill_existing_betrothal")) && sameEpisode(previous, snapshot)
                && eq(previous.get("heir_character_id"), choice.get("heir_character_id")) && eq(previous.get("candidate_character_id"), choice.get("candidate_character_id")))
            throw new IllegalArgumentException("fulfillment pair already consumed a reply");
        return base(Branch.FULFILLMENT, snapshot, bridge, choice.get("heir_character_id"), choice.get("candidate_character_id"), choice.get("recipient_character_id"))
                .with("schema_version", n(1)).with("step", t(Branch.FULFILLMENT.operation().value())).with("advertised", new Bool(false)).with("fulfill_existing_betrothal", new Bool(true))
                .with("exact_ck3_build", relation.get("exact_ck3_build")).with("exe_sha256", relation.get("exe_sha256"))
                .with("intermediary_character_id", choice.get("intermediary_character_id")).with("matrilineal_option_selected", choice.get("effective_matrilineal_if_accepted"))
                .with("prior_betrothal_relationship", relation).with("selected_value_projection", relation.get("betrothal_actionability")).with("resource_proposal", choice.get("resource_proposal"));
    }
    private static Obj child(Branch branch, Obj snapshot, BridgeIdentity bridge, State state, Obj plan) {
        boolean defaultRoute = branch == Branch.DEFAULT; String prefix = defaultRoute ? "child_default" : "child_matrilineal";
        Obj legality = object(plan.get(prefix + "_legality")), value = object(plan.get(prefix + "_value")), row = object(value.get("row"));
        FamilyOrdinaryPolicy.requireSameNative(legality, snapshot); FamilyOrdinaryPolicy.requireSameNative(value, snapshot);
        if (!eq(value.get("legality_query_sequence"), legality.get("query_sequence")) || !eq(row.get("heir_character_id"), legality.get("subject_character_id"))
                || !eq(row.get("actor_character_id"), object(snapshot.get("played_character")).get("character_id")) || !yes(row.get("complete_can_send"))
                || !eq(value.get("request_matrilineal_option"), new Bool(!defaultRoute))) throw new IllegalArgumentException("child selected native-final proof changed");
        if ((defaultRoute ? row.get("selected_option_readback") != Nil.INSTANCE : !yes(row.get("selected_option_readback"))) || !eq(row.get("matrilineal_option_selected"), new Bool(!defaultRoute))
                || !eq(row.get("effective_matrilineal_if_accepted"), new Bool(!defaultRoute)) || !no(row.get("grand_wedding_option_selected"))
                || !eq(row.get("heir_sex_selector_raw"), n(defaultRoute ? 0 : 1)) || !eq(row.get("candidate_sex_selector_raw"), n(defaultRoute ? 1 : 0)))
            throw new IllegalArgumentException("child selected lineality changed");
        if (!defaultRoute && (!yes(row.get("heir_is_adult")) || !yes(row.get("candidate_is_adult")) || !"marriage".equals(string(row.get("predicted_outcome_if_accepted")))
                || !(row.get("recipient_answer_status_raw") instanceof IntegerValue answer) || !(answer.value().equals(BigInteger.ZERO) || answer.value().equals(BigInteger.ONE))
                || !(row.get("recipient_ai_accept_raw") instanceof IntegerValue accept) || accept.value().signum() <= 0
                || !eq(row.get("heir_house_id"), legality.get("house_id")) || !eq(row.get("heir_dynasty_id"), legality.get("dynasty_id"))
                || !eq(row.get("played_dynasty_id"), legality.get("dynasty_id")) || eq(row.get("candidate_dynasty_id"), legality.get("dynasty_id"))))
            throw new IllegalArgumentException("configured adult child pair lost its positive native value");
        if (!defaultRoute) {
            positive(row.get("candidate_dynasty_id"));
            for (String partnerPrefix : List.of("heir", "candidate"))
                if (!unpartnered(obj("betrothed_character_id", row.get(partnerPrefix + "_betrothed_character_id"),
                        "primary_spouse_character_id", row.get(partnerPrefix + "_primary_spouse_character_id"), "spouse_character_ids", row.get(partnerPrefix + "_spouse_character_ids"))))
                    throw new IllegalArgumentException("configured child pair already has a native partner");
        }
        Obj ledger = state.body(branch.slot());
        if (!defaultRoute && ledger.get("resolved") != Nil.INSTANCE) throw new IllegalArgumentException("configured child pair already consumed");
        if (state.family().get("pending") != Nil.INSTANCE || defaultRoute && state.matrilineal().get("pending") != Nil.INSTANCE)
            throw new IllegalArgumentException("another family proposal owns the shared characters");
        Value actor = object(snapshot.get("played_character")).get("character_id"), subject = legality.get("subject_character_id"), candidate = value.get("candidate_character_id"), recipient = row.get("recipient_character_id");
        Obj pending = base(branch, snapshot, bridge, subject, candidate, recipient).with("matrilineal_option_selected", new Bool(!defaultRoute))
                .with("claimed_character_ids", rows(List.of(actor, subject, candidate, recipient))).with("selected_value_projection", row);
        if (!defaultRoute) return pending.with("deferred_war_query", nil(plan.get("child_matrilineal_deferred_step")));
        Obj observation = object(plan.get("child_default_observation")), split = object(observation.get("split_successor"));
        Value retry = plan.get("child_default_retry_source");
        if (!eq(nil(retry), ledger.get("resolved")) || !eq(split.get("subject_character_id"), subject)
                || !eq(object(observation.get("policy_decision")).get("selected_candidate_character_id"), candidate)) throw new IllegalArgumentException("child default split/retry disposition changed");
        if (observation.get("rejected_candidate_ids") == null) throw new IllegalArgumentException("child default refusal history is explicitly required");
        Arr rejected = ids(observation.get("rejected_candidate_ids"), true), attempted = ids(observation.get("attempted_candidate_ids"), true);
        if (array(rejected).contains(candidate) || array(attempted).contains(candidate)) throw new IllegalArgumentException("child previously attempted or refused candidate");
        if (retry == null || retry == Nil.INSTANCE) { if (!array(rejected).isEmpty() || !array(attempted).isEmpty()) throw new IllegalArgumentException("child history lacks a source proposal"); }
        else {
            Obj disposition = object(retry), source = object(disposition.get("source_pending"));
            if (!sameEpisode(source, snapshot) || !eq(source.get("played_character_id"), actor) || !eq(source.get("heir_character_id"), subject)) throw new IllegalArgumentException("child retry actor/episode/subject changed");
            Set<BigInteger> expectedRejected = new HashSet<>(FamilyOrdinaryPolicy.candidateHistory(source, "prior_rejected_candidate_ids"));
            Set<BigInteger> expectedAttempted = new HashSet<>(FamilyOrdinaryPolicy.candidateHistory(source, "prior_attempted_candidate_ids"));
            if ("gone_unmaterialized".equals(string(disposition.get("status")))) expectedAttempted.add(positive(disposition.get("candidate_character_id")));
            else if (oneOf(disposition.get("status"), "refused", "invalidated")) expectedRejected.add(positive(disposition.get("candidate_character_id")));
            else throw new IllegalArgumentException("unresolved child outcome grants no retry");
            if (!expectedRejected.equals(numbers(rejected)) || !expectedAttempted.equals(numbers(attempted))) throw new IllegalArgumentException("child refusal/attempt lineage changed");
        }
        Set<BigInteger> excluded = new HashSet<>(numbers(rejected)); excluded.addAll(numbers(attempted));
        Obj input = obj("schema", t(MarriageCodec.SCHEMA), "legality", legality, "values", rows(List.of()), "split_successor_verified", new Bool(true),
                "excluded_candidate_ids", new Arr(excluded.stream().sorted().<Value>map(IntegerValue::new).toList()), "shortlist_limit", n(2));
        List<BigInteger> shortlist = MarriagePolicy.shortlist(MarriageCodec.decodeFullMaterial(bytes(input)));
        Arr fullValues = new Arr(array(plan.get("child_default_full_values")));
        List<BigInteger> observedIds = array(fullValues).stream().map(FamilyJson::object).map(item -> positive(item.get("candidate_character_id"))).toList();
        Obj choice = decode(MarriageCodec.encodeDecision(MarriagePolicy.choose(MarriageCodec.decodeFullMaterial(bytes(input.with("values", fullValues))))));
        if (!observedIds.equals(shortlist) || !eq(observation.get("shortlist_candidate_ids"), new Arr(shortlist.stream().<Value>map(IntegerValue::new).toList()))
                || !choice.equals(observation.get("policy_decision")) || !"selected".equals(string(choice.get("status")))
                || !eq(choice.get("selected_candidate_character_id"), candidate) || !unique(array(fullValues), "candidate_character_id", candidate).equals(value))
            throw new IllegalArgumentException("child full shortlist/comparator or selected native value changed");
        return pending.with("split_title_ids", split.get("split_title_ids")).with("prior_rejected_candidate_ids", rejected).with("prior_attempted_candidate_ids", attempted)
                .with("deferred_prior_plan", plan.get("child_default_displaced_plan") instanceof Obj prior ? prior : obj());
    }
    private static Obj unique(List<Value> rows, String field, Value identity) {
        List<Obj> matches = rows.stream().map(FamilyJson::object).filter(row -> eq(row.get(field), identity)).toList();
        if (matches.size() != 1) throw new IllegalArgumentException("one exact selected native row required"); return matches.get(0);
    }
    private static Arr ids(Value value, boolean sorted) {
        if (value == null) return rows(List.of()); List<Value> ids = array(value); Set<BigInteger> seen = new HashSet<>(); BigInteger last = null;
        for (Value raw : ids) { BigInteger id = positive(raw); if (!seen.add(id) || sorted && last != null && last.compareTo(id) >= 0) throw new IllegalArgumentException("unique ordered family candidate history required"); last = id; }
        return rows(ids);
    }
    private static Set<BigInteger> numbers(Arr ids) { Set<BigInteger> values = new HashSet<>(); for (Value value : array(ids)) values.add(positive(value)); return Set.copyOf(values); }
    private static Arr strings(List<String> values) { return new Arr(values.stream().<Value>map(Text::new).toList()); }
    private static void requireWar(Obj snapshot, Obj wartime, List<Value> characters) {
        List<Value> wars = array(snapshot.get("active_wars"));
        if (wars.isEmpty() || !eq(wartime.get("source_date_raw"), snapshot.get("date_raw")) || !eq(wartime.get("native_revision"), snapshot.get("native_revision"))
                || !eq(wartime.get("active_war_ids"), rows(wars.stream().map(FamilyJson::object).map(row -> row.get("war_id")).toList()))
                || !eq(wartime.get("observed_treasury"), snapshot.get("played_character_gold")) || !eq(wartime.get("character_claims"), rows(characters)))
            throw new IllegalArgumentException("family wartime resource observation changed");
    }
}
