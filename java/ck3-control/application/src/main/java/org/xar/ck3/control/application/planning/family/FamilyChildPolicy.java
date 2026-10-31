package org.xar.ck3.control.application.planning.family;

import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import static org.xar.ck3.control.application.planning.family.FamilyPorts.*;
import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.governance.marriage.MarriageCodec;
import org.xar.ck3.control.governance.marriage.MarriagePolicy;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Existing configured adult pair and split-successor default remain separate consumer branches. */
final class FamilyChildPolicy {
    private FamilyChildPolicy() { }
    static Decision matrilineal(FamilyOrdinaryPolicy owner, PlanningRequest request, Draft previous, Documents docs, Pair pair) {
        Obj snapshot = request.observations().snapshot(), ledger = docs.matrilineal();
        if (ledger.get("pending") instanceof Obj pending && (!sameEpisode(pending, snapshot)
                || !integer(pending.get("heir_character_id")).equals(pair.subject()) || !integer(pending.get("candidate_character_id")).equals(pair.candidate())))
            throw new IllegalArgumentException("unresolved configured child proposal belongs to another target");
        Decision pending = owner.pending(request, previous, ledger, docs, Query.MATRILINEAL_RESULT, "child_matrilineal", false);
        if (pending != null) return pending;
        if (ledger.get("resolved") instanceof Obj resolved) {
            Decision result = owner.resolution(request, previous, resolved, docs,
                    Query.MATRILINEAL_RESULT, Query.MATRILINEAL_ALLIANCE, "child_matrilineal");
            if (result != null) return result;
            return new Keep("configured child marriage result already retained");
        }
        if (docs.family().get("pending") instanceof Obj || !matrilinealEligible(previous, request)) return new Keep("prior family pending or nondeferrable action precedes configured child proposal");
        if (!owner.newMarriageProposalsEnabled()) return new Keep("new_marriage_proposals_enabled=false: configured child matrilineal proposal skipped");
        ObservedRead subjectRead = owner.readObserved(request, Query.CHILD_SUBJECT, obj("expected_native_revision", snapshot.get("native_revision"), "subject_character_id", new IntegerValue(pair.subject())));
        Obj legality = subjectRead.value();
        if (!"available".equals(string(legality.get("status"))) || !yes(legality.get("player_child_verified")))
            return new Keep("configured child native subject is not currently eligible");
        requireSubject(legality, snapshot, pair.subject());
        Obj value = owner.read(request, Query.CHILD_VALUE, obj("legality", legality, "subject_read", FamilyOrdinaryPolicy.originalRef(subjectRead.originalReceipt()), "candidate_character_id", new IntegerValue(pair.candidate()), "request_matrilineal_option", new Bool(true)));
        if (!positiveMatrilineal(legality, value)) return owner.annotate(previous, previous.detail().with("child_matrilineal_legality", legality).with("child_matrilineal_value", value));
        return owner.select(request, previous, "submit-player-child-matrilineal-marriage-v1-private", obj("legality", legality, "value", value),
                previous.detail().with("child_matrilineal_legality", legality).with("child_matrilineal_value", value)
                        .with("child_matrilineal_war_context", FamilyOrdinaryPolicy.warContext(snapshot, value))
                        .with("child_matrilineal_deferred_step",deferrableWarQuery(FamilyOrdinaryPolicy.selected(previous),snapshot)?t(FamilyOrdinaryPolicy.selected(previous)):Nil.INSTANCE)
                        .with("child_matrilineal_wartime_source",deferrableWarQuery(FamilyOrdinaryPolicy.selected(previous),snapshot)?warQuerySource(snapshot):Nil.INSTANCE),
                "child_matrilineal_typed_submit", "submit the configured freshly valued dynasty-preserving adult pair", Purpose.WORLD_ACTION);
    }
    static Decision childDefault(FamilyOrdinaryPolicy owner, PlanningRequest request, Draft previous, Documents docs) {
        Obj snapshot = request.observations().snapshot(), ledger = docs.childDefault();
        if (ledger.get("pending") instanceof Obj p && !sameEpisode(p, snapshot)) return new Keep("other-episode child default proposal is not reused");
        Decision pending = owner.pending(request, previous, ledger, docs, Query.DEFAULT_RESULT, "child_default", true);
        if (pending != null) return pending;
        Obj retry = null; Set<BigInteger> rejected = Set.of(), attempted = Set.of();
        if (ledger.get("resolved") instanceof Obj resolved) {
            if (!sameEpisode(resolved, snapshot)) return new Keep("other-episode child default result is not reused");
            if (material(resolved)) {
                Decision result = owner.resolution(request, previous, resolved, docs, Query.DEFAULT_RESULT, Query.DEFAULT_ALLIANCE, "child_default");
                return result == null ? new Keep("current child default material relation already observed") : result;
            }
            String status = string(resolved.get("status"));
            if (!oneOf(resolved.get("status"), "refused", "invalidated", "gone_unmaterialized")) return new Keep("child result is unresolved; no new proposal");
            Obj source = object(resolved.get("source_pending"));
            if (!sameEpisode(source, snapshot) || !eq(source.get("played_character_id"), object(snapshot.get("played_character")).get("character_id")))
                return new Keep("child retry source does not match current actor and episode");
            if (!eq(source.get("heir_character_id"), resolved.get("heir_character_id")) || !eq(source.get("candidate_character_id"), resolved.get("candidate_character_id")))
                throw new IllegalArgumentException("child retry disposition lacks exact source proposal");
            Set<BigInteger> rejectedMutable = new HashSet<>(FamilyOrdinaryPolicy.candidateHistory(source, "prior_rejected_candidate_ids"));
            Set<BigInteger> attemptedMutable = new HashSet<>(FamilyOrdinaryPolicy.candidateHistory(source, "prior_attempted_candidate_ids"));
            if ("gone_unmaterialized".equals(status)) attemptedMutable.add(positive(resolved.get("candidate_character_id")));
            else if (!rejectedMutable.add(positive(resolved.get("candidate_character_id")))) throw new IllegalArgumentException("duplicate rejected child proposal");
            rejected = Set.copyOf(rejectedMutable); attempted = Set.copyOf(attemptedMutable); retry = resolved;
        }
        if (!defaultEligible(previous, request) || docs.family().get("pending") instanceof Obj || docs.matrilineal().get("pending") instanceof Obj)
            return new Keep("fresh split-successor proposal cannot displace this action or another pending family proposal");
        if (!owner.newMarriageProposalsEnabled()) return new Keep("new_marriage_proposals_enabled=false: split-successor child default proposal skipped");
        Obj root = owner.read(request, Query.CAMPAIGN_ROOT, obj("expected_revision", snapshot.get("revision")));
        Obj split = split(root, snapshot); if (split == null) return new Keep("current held-title partition has no single distinct secondary heir");
        Value subject = split.get("subject_character_id");
        if (retry != null && !eq(retry.get("heir_character_id"), subject)) return new Keep("child retry no longer refers to the split successor");
        ObservedRead subjectRead = owner.readObserved(request, Query.CHILD_SUBJECT, obj("expected_native_revision", snapshot.get("native_revision"), "subject_character_id", subject));
        Obj legality = subjectRead.value();
        if (!"available".equals(string(legality.get("status"))) || !yes(legality.get("player_child_verified"))) return new Keep("split-successor child subject unavailable");
        requireSubject(legality, snapshot, integer(subject));
        if (!unpartnered(legality)) return new Keep("split-successor child already has current native partner");
        Set<BigInteger> excluded = new HashSet<>(rejected); excluded.addAll(attempted);
        Arr exclusions = new Arr(excluded.stream().sorted().<Value>map(IntegerValue::new).toList());
        Obj initial = obj("schema", t(MarriageCodec.SCHEMA), "legality", legality, "values", rows(List.of()),
                "split_successor_verified", new Bool(true), "excluded_candidate_ids", exclusions, "shortlist_limit", n(2));
        List<BigInteger> shortlist = MarriagePolicy.shortlist(MarriageCodec.decode(bytes(initial)));
        List<Value> values = new ArrayList<>();
        for (BigInteger candidate : shortlist) {
            Obj value = owner.read(request, Query.CHILD_VALUE, obj("legality", legality, "subject_read", FamilyOrdinaryPolicy.originalRef(subjectRead.originalReceipt()), "candidate_character_id", new IntegerValue(candidate), "request_matrilineal_option", new Bool(false)));
            if (!integer(value.get("candidate_character_id")).equals(candidate)) throw new IllegalArgumentException("child default comparator set changed");
            values.add(value);
        }
        Obj choice = decode(MarriageCodec.encodeDecision(MarriagePolicy.choose(MarriageCodec.decode(bytes(initial.with("values", rows(values)))))));
        Obj observation = obj("split_successor", split, "shortlist_candidate_ids", new Arr(shortlist.stream().<Value>map(IntegerValue::new).toList()),
                "full_values", rows(values), "policy_decision", choice, "stop_reason", t("complete_shortlist_compared"),
                "rejected_candidate_ids", new Arr(rejected.stream().sorted().<Value>map(IntegerValue::new).toList()),
                "attempted_candidate_ids", new Arr(attempted.stream().sorted().<Value>map(IntegerValue::new).toList()));
        Obj detail = previous.detail().with("child_default_observation", observation)
                .with("child_default_displaced_plan",obj("selected_step",FamilyOrdinaryPolicy.selected(previous)==null?Nil.INSTANCE:t(FamilyOrdinaryPolicy.selected(previous)),
                        "phase",t(previous.phase()),"reason",t(previous.reason())));
        if (!"selected".equals(string(choice.get("status")))) return owner.annotate(previous, detail);
        Obj selected = values.stream().map(FamilyJson::object).filter(value -> eq(value.get("candidate_character_id"), choice.get("selected_candidate_character_id"))).findFirst().orElseThrow();
        if (!defaultAligned(object(selected.get("row")))) return owner.annotate(previous, detail);
        detail = detail.with("child_default_legality", legality).with("child_default_value", selected).with("child_default_full_values", rows(values))
                .with("child_default_retry_source", nil(retry));
        return owner.select(request, previous, "submit-player-child-default-marriage-v1-private", obj("legality", legality, "value", selected, "observation", observation),
                detail, "child_default_typed_submit", "submit one exact native-final split-successor child proposal", Purpose.WORLD_ACTION);
    }
    private static boolean defaultEligible(Draft previous, PlanningRequest request) {
        String step=FamilyOrdinaryPolicy.selected(previous);
        if("life-advance".equals(step))return true;
        if(step!=null)return false;
        return request.observations().snapshot().get("active_wars") instanceof Arr wars&&!wars.items().isEmpty()
                &&previous.phase().startsWith("native_war")&&!previous.reason().isEmpty();
    }
    private static boolean matrilinealEligible(Draft previous, PlanningRequest request) {
        String step=FamilyOrdinaryPolicy.selected(previous);
        return "life-advance".equals(step)||deferrableWarQuery(step,request.observations().snapshot());
    }
    static boolean deferrableWarQuery(String step,Obj snapshot) {
        if(step==null||!(snapshot.get("active_wars") instanceof Arr wars))return false;
        for(Value raw:wars.items())if(raw instanceof Obj war&&war.get("war_id") instanceof IntegerValue id
                &&id.value().signum()>0&&id.value().bitLength()<=31
                &&step.equals("query-war-termination-options-"+id.value()))return true;
        return false;
    }
    static Obj warQuerySource(Obj snapshot) {
        List<Value> ids=new ArrayList<>();
        for(Value raw:array(snapshot.get("active_wars")))if(raw instanceof Obj war)ids.add(nil(war.get("war_id")));
        return obj("date_raw",nil(snapshot.get("date_raw")),"native_revision",nil(snapshot.get("native_revision")),"active_war_ids",rows(ids));
    }
    private static void requireSubject(Obj legality, Obj snapshot, BigInteger subject) {
        FamilyOrdinaryPolicy.requireSameNative(legality, snapshot);
        if (!integer(legality.get("subject_character_id")).equals(subject)
                || !eq(legality.get("played_character_id"), object(snapshot.get("played_character")).get("character_id"))) throw new IllegalArgumentException("child subject crossed actor/frame");
    }
    static Obj split(Obj root, Obj snapshot) {
        if (!"available".equals(string(root.get("status"))))throw new IllegalArgumentException("split-successor campaign root unavailable");
        FamilyRootCurrentFrame.requireSame(root,snapshot);
        Obj context = object(root.get("campaign_root_context"));
        if (!eq(context.get("player_character_id"), object(snapshot.get("played_character")).get("character_id"))) throw new IllegalArgumentException("root actor changed");
        if (!(context.get("held_title_partition") instanceof Arr partition)) return null;
        List<Obj> primary = partition.items().stream().map(FamilyJson::object).filter(row -> yes(row.get("primary"))).toList();
        if (primary.size() != 1 || !(primary.get(0).get("first_heir_character_id") instanceof IntegerValue)) return null;
        Value first = primary.get(0).get("first_heir_character_id"); Set<BigInteger> subjects = new HashSet<>(), titles = new HashSet<>();
        for (Value raw : partition.items()) {
            Obj row = object(raw);
            if (no(row.get("primary")) && row.get("first_heir_character_id") instanceof IntegerValue && !eq(row.get("first_heir_character_id"), first)
                    && row.get("title") instanceof Obj title && title.get("title_id") instanceof IntegerValue) {
                subjects.add(positive(row.get("first_heir_character_id"))); titles.add(positive(title.get("title_id")));
            }
        }
        if (subjects.size() != 1) return null;
        return obj("subject_character_id", new IntegerValue(subjects.iterator().next()), "primary_heir_character_id", first,
                "split_title_ids", new Arr(titles.stream().sorted().<Value>map(IntegerValue::new).toList()), "source_revision", snapshot.get("revision"),
                "source_native_revision", snapshot.get("native_revision"), "source_date_raw", snapshot.get("date_raw"));
    }
    static boolean defaultAligned(Obj row) {
        return n(0).equals(row.get("heir_sex_selector_raw")) && n(1).equals(row.get("candidate_sex_selector_raw"))
                && no(row.get("requested_matrilineal_option")) && no(row.get("matrilineal_option_selected")) && no(row.get("effective_matrilineal_if_accepted"));
    }
    static boolean positiveMatrilineal(Obj legality, Obj value) {
        if (!"available".equals(string(value.get("status"))) || !yes(value.get("request_matrilineal_option")) || !(value.get("row") instanceof Obj row)) return false;
        for (String field : List.of("selected_option_readback", "matrilineal_option_selected", "effective_matrilineal_if_accepted", "complete_can_send", "heir_is_adult", "candidate_is_adult")) if (!yes(row.get(field))) return false;
        if (!(row.get("recipient_answer_status_raw") instanceof IntegerValue answer) || !(answer.value().equals(BigInteger.ZERO) || answer.value().equals(BigInteger.ONE))
                || !(row.get("recipient_ai_accept_raw") instanceof IntegerValue accept) || accept.value().signum() <= 0
                || !"marriage".equals(string(row.get("predicted_outcome_if_accepted"))) || !n(1).equals(row.get("heir_sex_selector_raw"))
                || !n(0).equals(row.get("candidate_sex_selector_raw")) || !no(row.get("grand_wedding_option_selected"))) return false;
        if (!eq(row.get("heir_house_id"), legality.get("house_id")) || !eq(row.get("heir_dynasty_id"), legality.get("dynasty_id"))
                || !eq(row.get("played_dynasty_id"), legality.get("dynasty_id")) || !(row.get("candidate_dynasty_id") instanceof IntegerValue dynasty)
                || dynasty.value().signum() <= 0 || eq(row.get("candidate_dynasty_id"), legality.get("dynasty_id"))) return false;
        return unpartnered(obj("betrothed_character_id", nil(row.get("heir_betrothed_character_id")), "primary_spouse_character_id", nil(row.get("heir_primary_spouse_character_id")), "spouse_character_ids", nil(row.get("heir_spouse_character_ids"))))
                && unpartnered(obj("betrothed_character_id", nil(row.get("candidate_betrothed_character_id")), "primary_spouse_character_id", nil(row.get("candidate_primary_spouse_character_id")), "spouse_character_ids", nil(row.get("candidate_spouse_character_ids"))));
    }
}
