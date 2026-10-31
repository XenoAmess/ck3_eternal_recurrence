package org.xar.ck3.control.application.planning.family;

import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.application.planning.family.FamilyPorts.BridgeIdentity;
import org.xar.ck3.control.application.planning.family.FamilyPendingProducer.State;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.governance.heirpreference.HeirPreferenceCodec;
import org.xar.ck3.control.governance.marriage.MarriageCodec;
import org.xar.ck3.control.governance.marriage.MarriagePolicy;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineageConsumerPort;
import org.xar.ck3.control.wave3.governance.betrothalvalue.BetrothalValueCodec;
import org.xar.ck3.control.wave3.governance.betrothalvalue.BetrothalValuePolicy;
import org.xar.ck3.control.wave3.governance.heirdiagnostic.HeirCandidateDiagnosticConsumerPort;
import org.xar.ck3.control.wave3.governance.heirintake.HeirCandidateIntakeConsumerPort;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRankingConsumerPort;

/** Fresh-read pure strategy. The native owner separately proves every packet, policy and original domain source. */
public final class FamilyMarriagePreparationReview {
    public static final String SCHEMA="xar.ck3.family-marriage-prepared-plan/v1";
    private FamilyMarriagePreparationReview() { }
    /** This value does not qualify its own goal/config source; the native manifest must retain that actual original. */
    public record Policy(boolean dynastyHeirPreference) { }
    public sealed interface FreshReads permits FirstHeir,Fulfillment,ChildMatrilineal,ChildDefault { }
    public record FirstHeir(Obj currentRelationship,Obj legality,Obj projection,List<Obj> childHousePreviews) implements FreshReads {
        public FirstHeir {Objects.requireNonNull(currentRelationship);Objects.requireNonNull(legality);Objects.requireNonNull(projection);childHousePreviews=List.copyOf(childHousePreviews);}
    }
    public record Fulfillment(Obj currentRelationship) implements FreshReads {public Fulfillment {Objects.requireNonNull(currentRelationship);}}
    public record ChildMatrilineal(Obj subject,Obj value) implements FreshReads {public ChildMatrilineal {Objects.requireNonNull(subject);Objects.requireNonNull(value);}}
    public record ChildDefault(Obj campaignRoot,Obj subject,List<Obj> completeValues) implements FreshReads {
        public ChildDefault {Objects.requireNonNull(campaignRoot);Objects.requireNonNull(subject);completeValues=List.copyOf(completeValues);}
    }
    public static Obj review(FamilyMarriageIntent intent,Obj snapshot,BridgeIdentity bridge,State domains,Policy policy,FreshReads reads) {
        Objects.requireNonNull(intent);Objects.requireNonNull(policy);Objects.requireNonNull(reads);requireDomains(snapshot,domains);requireOpen(domains,intent.route());
        Obj plan=switch(intent.route()) {
            case FIRST_HEIR -> {if(!(reads instanceof FirstHeir actual))throw wrongRoute();yield heir(snapshot,bridge,domains,policy,actual);}
            case FULFILL_BETROTHAL -> {if(!(reads instanceof Fulfillment actual))throw wrongRoute();yield fulfillment(snapshot,actual);}
            case CHILD_MATRILINEAL -> {if(!(reads instanceof ChildMatrilineal actual))throw wrongRoute();yield matrilineal(snapshot,actual);}
            case CHILD_DEFAULT -> {if(!(reads instanceof ChildDefault actual))throw wrongRoute();yield childDefault(snapshot,domains,actual);}
        };
        plan=plan.with("schema",t(SCHEMA)).with("selected_step",t(intent.step()))
                .with("planning_proof",intent.planningProof().<Value>map(value->value).orElse(Nil.INSTANCE));
        plan=retainChildDeferral(intent,snapshot,plan);
        FamilyPendingProducer.validate(intent,snapshot,bridge,domains,plan);return plan;
    }
    private static Obj retainChildDeferral(FamilyMarriageIntent intent,Obj snapshot,Obj plan) {
        Obj original=intent.planningProof().orElseGet(FamilyJson::obj);
        if(intent.route()==FamilyMarriageIntent.Route.CHILD_DEFAULT) {
            Value displaced=original.get("child_default_displaced_plan");
            return plan.with("child_default_displaced_plan",displaced==null?obj():object(displaced));
        }
        if(intent.route()==FamilyMarriageIntent.Route.CHILD_MATRILINEAL) {
            Value deferred=nil(original.get("child_matrilineal_deferred_step"));
            Value source=nil(original.get("child_matrilineal_wartime_source"));
            if(source!=Nil.INSTANCE)object(source);
            if(deferred!=Nil.INSTANCE&&(!FamilyChildPolicy.deferrableWarQuery(text(deferred),snapshot)
                    ||!FamilyChildPolicy.warQuerySource(snapshot).equals(object(source))))
                throw new IllegalArgumentException("deferred read-only war query changed before child proposal");
            return plan.with("child_matrilineal_deferred_step",deferred).with("child_matrilineal_wartime_source",source);
        }
        return plan;
    }
    /** Ordered not-yet-read preview candidates. Reinvoke after each actual preview; a satisfied prefix returns empty. */
    public static List<BigInteger> heirPreviewCandidates(Obj snapshot,BridgeIdentity bridge,State domains,Policy policy,FirstHeir actual) {
        requireDomains(snapshot,domains);requireOpen(domains,FamilyMarriageIntent.Route.FIRST_HEIR);Objects.requireNonNull(policy);var ranked=rankHeir(snapshot,bridge,domains,actual);
        if(!policy.dynastyHeirPreference()) {
            if(!actual.childHousePreviews().isEmpty())throw new IllegalArgumentException("unrequested dynasty previews do not belong to this actual policy");
            return List.of();
        }
        List<Obj> ordered=orderedHeirChoices(ranked.choices(),actual.projection());int consumed=0;boolean satisfied=false;
        for(Obj observed:actual.childHousePreviews()) {
            if(satisfied || consumed>=ordered.size())throw new IllegalArgumentException("native lineage previews extend beyond the required ordered prefix");
            Obj choice=ordered.get(consumed++),preview=object(observed.get("native_child_house_preview"));
            Value candidate=choice.get("candidate_character_id");Obj row=one(array(actual.projection().get("rows")),candidate);
            if(!eq(preview.get("candidate_character_id"),candidate) || !eq(preview.get("subject_character_id"),actual.legality().get("observed_first_heir_character_id")))
                throw new IllegalArgumentException("native lineage preview changed its exact ordered pair");
            satisfied="available".equals(string(preview.get("status"))) && yes(preview.get("complete_can_send")) && eq(preview.get("dynasty_id"),row.get("played_dynasty_id"));
        }
        if(satisfied)return List.of();return ordered.subList(consumed,ordered.size()).stream().map(row->positive(row.get("candidate_character_id"))).toList();
    }
    /** The original complete top-two comparator; native preparation reads precisely these values in this order. */
    public static List<BigInteger> defaultComparisonCandidates(Obj snapshot,Obj campaignRoot,Obj subject,State domains) {
        requireDomains(snapshot,domains);requireOpen(domains,FamilyMarriageIntent.Route.CHILD_DEFAULT);return MarriagePolicy.shortlist(MarriageCodec.decodeFullMaterial(bytes(defaultInput(snapshot,campaignRoot,subject,domains).input())));
    }
    private record HeirRank(Obj intake,Arr choices,Arr exclusions) { }
    /** Fresh legal intake determines precisely which five rich rows must be queried before ranking. */
    public static List<BigInteger> heirComparisonCandidates(Obj snapshot,BridgeIdentity bridge,State domains,Obj relation,Obj legality) {
        requireDomains(snapshot,domains);requireOpen(domains,FamilyMarriageIntent.Route.FIRST_HEIR);
        if(!"available".equals(string(relation.get("status"))) || !yes(relation.get("bilateral_verified")) || !unpartnered(relation)
                || !"available".equals(string(legality.get("status"))) || !eq(relation.get("heir_character_id"),legality.get("observed_first_heir_character_id")))
            throw new IllegalArgumentException("fresh first-heir relation/legality is not the exact unpartnered subject");
        FamilyOrdinaryPolicy.requireSameNative(relation,snapshot);FamilyOrdinaryPolicy.requireSameNative(legality,snapshot);
        Arr exclusions=ids(heirRejections(snapshot,bridge,domains,relation));
        return HeirCandidateIntakeConsumerPort.evaluate(bytes(obj("legal_rows",legality.get("native_legal_candidates"),"rejected_candidate_ids",exclusions)))
                .nextRichCandidateIds().orElseThrow(()->new IllegalArgumentException("fresh complete five-row shortlist is not selected"));
    }
    private static HeirRank rankHeir(Obj snapshot,BridgeIdentity bridge,State domains,FirstHeir actual) {
        Obj relation=actual.currentRelationship(),legality=actual.legality();
        if(!"available".equals(string(relation.get("status"))) || !yes(relation.get("bilateral_verified")) || !unpartnered(relation)
                || !"available".equals(string(legality.get("status"))) || !eq(relation.get("heir_character_id"),legality.get("observed_first_heir_character_id")))
            throw new IllegalArgumentException("fresh first-heir relation/legality is not the exact unpartnered subject");
        FamilyOrdinaryPolicy.requireSameNative(relation,snapshot);FamilyOrdinaryPolicy.requireSameNative(legality,snapshot);
        Set<BigInteger> rejected=heirRejections(snapshot,bridge,domains,relation);
        Arr exclusions=new Arr(rejected.stream().sorted().<Value>map(IntegerValue::new).toList());
        var intake=HeirCandidateIntakeConsumerPort.evaluate(bytes(obj("legal_rows",legality.get("native_legal_candidates"),"rejected_candidate_ids",exclusions)));
        List<BigInteger> expected=intake.nextRichCandidateIds().orElseThrow(()->new IllegalArgumentException("fresh complete five-row shortlist is not selected"));
        List<BigInteger> observed=array(actual.projection().get("rows")).stream().map(FamilyJson::object).map(row->positive(row.get("candidate_character_id"))).toList();
        if(!expected.equals(observed))throw new IllegalArgumentException("fresh projection changed the complete five candidates or native order");
        FamilyOrdinaryPolicy.requireSameNative(actual.projection(),snapshot);
        for(Value raw:array(actual.projection().get("rows"))) {
            Obj row=object(raw);
            if(!eq(row.get("heir_character_id"),relation.get("heir_character_id")) || !eq(row.get("heir_betrothed_character_id"),relation.get("betrothed_character_id"))
                    || !eq(row.get("heir_primary_spouse_character_id"),relation.get("primary_spouse_character_id")) || !eq(row.get("heir_spouse_character_ids"),relation.get("spouse_character_ids")))
                throw new IllegalArgumentException("fresh projection crossed the same-frame bilateral relation");
        }
        var ranking=HeirCandidateRankingConsumerPort.evaluate(HeirCandidateRankingConsumerPort.decode(bytes(obj("legality",legality,"projection",actual.projection(),"rejected_candidate_ids",exclusions))));
        Value parsed=OpportunityJson.parse(ranking.choices());Arr choices=new Arr(array(parsed));
        if(choices.items().isEmpty())throw new IllegalArgumentException("fresh complete ranking contains no positive native proposal");
        return new HeirRank(decode(intake.result()),choices,exclusions);
    }
    private static Set<BigInteger> heirRejections(Obj snapshot,BridgeIdentity bridge,State domains,Obj relation) {
        Set<BigInteger> rejected=new HashSet<>();
        if(domains.family().get("resolved") instanceof Obj resolved && sameEpisode(resolved,snapshot)) {
            if(oneOf(resolved.get("status"),"refused","invalidated") && eq(resolved.get("heir_character_id"),relation.get("heir_character_id"))) {
                if(!bridge.matches(resolved,"post_"))throw new IllegalArgumentException("cold refusal is not current actual Bridge evidence");
                rejected.addAll(FamilyOrdinaryPolicy.candidateHistory(object(resolved.get("source_pending")),"prior_rejected_candidate_ids"));
                rejected.add(positive(resolved.get("candidate_character_id")));
            } else if(!material(resolved) && !oneOf(resolved.get("status"),"refused","invalidated"))
                throw new IllegalArgumentException("unresolved first-heir disposition cannot authorize another proposal");
        }
        return Set.copyOf(rejected);
    }
    private static List<Obj> orderedHeirChoices(Arr choices,Obj projection) {
        Value ordered=OpportunityJson.parse(HeirPreferenceCodec.prioritize(bytes(obj("choices",choices,"rows",projection.get("rows")))));
        return array(ordered).stream().map(FamilyJson::object).toList();
    }
    private static Obj heir(Obj snapshot,BridgeIdentity bridge,State domains,Policy policy,FirstHeir actual) {
        var ranked=rankHeir(snapshot,bridge,domains,actual);Obj choice=object(ranked.choices().items().getFirst());
        Obj plan=obj("family_marriage_current_relationship",actual.currentRelationship(),"family_marriage_legality",actual.legality(),
                "family_marriage_projection",actual.projection(),"family_marriage_intake",ranked.intake(),"family_marriage_choices",ranked.choices(),
                "family_marriage_valued_choices",ranked.choices(),"family_marriage_rejected_candidate_ids",ranked.exclusions());
        if(policy.dynastyHeirPreference()) {
            if(!heirPreviewCandidates(snapshot,bridge,domains,policy,actual).isEmpty())throw new IllegalArgumentException("actual ordered child-house preview prefix is incomplete");
            Obj lineage=decode(HeirLineageConsumerPort.evaluate(bytes(obj("snapshot",snapshot,"legality",actual.legality(),"projection",actual.projection(),
                    "choices",ranked.choices(),"previews",rows(actual.childHousePreviews())))).result());
            if(!(lineage.get("choice") instanceof Obj selected))throw new IllegalArgumentException("fresh native lineage policy did not select a proposal");
            choice=selected;plan=plan.with("family_marriage_lineage",lineage);
        } else if(!actual.childHousePreviews().isEmpty())throw new IllegalArgumentException("unexpected lineage inputs for actual policy");
        Obj diagnostic=decode(HeirCandidateDiagnosticConsumerPort.project(bytes(obj("legality",actual.legality(),"projection",actual.projection(),"snapshot",snapshot,
                "choice",choice,"ranking",ranked.intake().get("ranking"),"rejected_candidate_ids",ranked.exclusions()))));
        return plan.with("family_marriage_choice",choice).with("family_marriage_private_diagnostic",diagnostic)
                .with("family_marriage_war_context",FamilyOrdinaryPolicy.warContext(snapshot,choice));
    }
    private static Obj fulfillment(Obj snapshot,Fulfillment actual) {
        Obj relation=actual.currentRelationship();FamilyOrdinaryPolicy.requireSameNative(relation,snapshot);
        Obj choice=decode(BetrothalValueCodec.encodeChoice(BetrothalValuePolicy.evaluate(BetrothalValueCodec.decode(bytes(
                obj("schema",t(BetrothalValueCodec.SCHEMA),"snapshot",snapshot,"relationship",relation))))));
        if(!"selected".equals(string(choice.get("status"))))throw new IllegalArgumentException("fresh current bilateral betrothal is not actionable");
        return obj("current_betrothal_relationship",relation,"current_betrothal_choice",choice);
    }
    private static void childSubject(Obj snapshot,Obj subject) {
        if(!"available".equals(string(subject.get("status"))) || !yes(subject.get("player_child_verified"))
                || !eq(subject.get("played_character_id"),object(snapshot.get("played_character")).get("character_id")))
            throw new IllegalArgumentException("fresh native subject is not an actual child of the current actor");
        positive(subject.get("subject_character_id"));FamilyOrdinaryPolicy.requireSameNative(subject,snapshot);
    }
    private static Obj matrilineal(Obj snapshot,ChildMatrilineal actual) {
        childSubject(snapshot,actual.subject());FamilyOrdinaryPolicy.requireSameNative(actual.value(),snapshot);
        if(!FamilyChildPolicy.positiveMatrilineal(actual.subject(),actual.value()))throw new IllegalArgumentException("fresh configured adult child value is no longer positive");
        return obj("child_matrilineal_legality",actual.subject(),"child_matrilineal_value",actual.value(),
                "child_matrilineal_war_context",FamilyOrdinaryPolicy.warContext(snapshot,actual.value()));
    }
    private record DefaultInput(Obj input,Obj split,Value retry,Arr rejected,Arr attempted) { }
    private static DefaultInput defaultInput(Obj snapshot,Obj root,Obj subject,State domains) {
        childSubject(snapshot,subject);if(!unpartnered(subject))throw new IllegalArgumentException("fresh split-successor child already has a partner");
        Obj split=FamilyChildPolicy.split(root,snapshot);
        if(split==null || !eq(split.get("subject_character_id"),subject.get("subject_character_id")))throw new IllegalArgumentException("fresh ROOT does not prove the exact unique split-successor child");
        Set<BigInteger> rejected=new HashSet<>(),attempted=new HashSet<>();Value retry=domains.childDefault().get("resolved");
        if(retry instanceof Obj disposition) {
            if(!sameEpisode(disposition,snapshot) || material(disposition) || !oneOf(disposition.get("status"),"refused","invalidated","gone_unmaterialized"))
                throw new IllegalArgumentException("unresolved or material child disposition cannot authorize a fresh comparator");
            Obj source=object(disposition.get("source_pending"));
            if(!sameEpisode(source,snapshot) || !eq(source.get("played_character_id"),object(snapshot.get("played_character")).get("character_id"))
                    || !eq(source.get("heir_character_id"),subject.get("subject_character_id")) || !eq(source.get("heir_character_id"),disposition.get("heir_character_id"))
                    || !eq(source.get("candidate_character_id"),disposition.get("candidate_character_id")))throw new IllegalArgumentException("child retry lineage differs from actual actor/episode/subject");
            rejected.addAll(FamilyOrdinaryPolicy.candidateHistory(source,"prior_rejected_candidate_ids"));attempted.addAll(FamilyOrdinaryPolicy.candidateHistory(source,"prior_attempted_candidate_ids"));
            if("gone_unmaterialized".equals(string(disposition.get("status"))))attempted.add(positive(disposition.get("candidate_character_id")));
            else if(!rejected.add(positive(disposition.get("candidate_character_id"))))throw new IllegalArgumentException("duplicate original child refusal");
        } else if(retry!=Nil.INSTANCE)throw new IllegalArgumentException("explicit nullable child result required");
        Arr rejectedIds=ids(rejected),attemptedIds=ids(attempted);Set<BigInteger> excluded=new HashSet<>(rejected);excluded.addAll(attempted);
        Obj input=obj("schema",t(MarriageCodec.SCHEMA),"legality",subject,"values",rows(List.of()),"split_successor_verified",new Bool(true),
                "excluded_candidate_ids",ids(excluded),"shortlist_limit",n(2));
        return new DefaultInput(input,split,retry,rejectedIds,attemptedIds);
    }
    private static Obj childDefault(Obj snapshot,State domains,ChildDefault actual) {
        var input=defaultInput(snapshot,actual.campaignRoot(),actual.subject(),domains);
        List<BigInteger> expected=MarriagePolicy.shortlist(MarriageCodec.decodeFullMaterial(bytes(input.input())));
        List<BigInteger> observed=actual.completeValues().stream().map(value->positive(value.get("candidate_character_id"))).toList();
        if(!expected.equals(observed))throw new IllegalArgumentException("fresh child preparation omitted or reordered a complete comparison value");
        for(Obj value:actual.completeValues()) {
            FamilyOrdinaryPolicy.requireSameNative(value,snapshot);
            if(!eq(value.get("legality_query_sequence"),actual.subject().get("query_sequence")) || !no(value.get("request_matrilineal_option")))
                throw new IllegalArgumentException("fresh child comparison crossed its subject query or default option");
        }
        Arr values=rows(actual.completeValues());Obj choice=decode(MarriageCodec.encodeDecision(MarriagePolicy.choose(MarriageCodec.decodeFullMaterial(bytes(input.input().with("values",values))))));
        if(!"selected".equals(string(choice.get("status"))))throw new IllegalArgumentException("fresh complete child comparator did not select a proposal");
        Obj selected=one(actual.completeValues().stream().<Value>map(value->value).toList(),choice.get("selected_candidate_character_id"));
        if(!FamilyChildPolicy.defaultAligned(object(selected.get("row"))))throw new IllegalArgumentException("fresh child default branch changed its native options");
        Obj observation=obj("split_successor",input.split(),"shortlist_candidate_ids",new Arr(expected.stream().<Value>map(IntegerValue::new).toList()),
                "full_values",values,"policy_decision",choice,"stop_reason",t("complete_shortlist_compared"),"rejected_candidate_ids",input.rejected(),"attempted_candidate_ids",input.attempted());
        return obj("child_default_legality",actual.subject(),"child_default_value",selected,"child_default_full_values",values,
                "child_default_observation",observation,"child_default_retry_source",input.retry());
    }
    private static void requireDomains(Obj snapshot,State domains) {
        Objects.requireNonNull(snapshot);Objects.requireNonNull(domains);
        if(!yes(snapshot.get("paused")) || !yes(snapshot.get("map_ready")))throw new IllegalArgumentException("fresh family review requires the actual paused map");
        for(Slot slot:List.of(Slot.FAMILY,Slot.CHILD_MATRILINEAL,Slot.DEFAULT_MARRIAGE))FamilyDomainSource.validate(slot,bytesDomain(domains.body(slot)));
    }
    private static void requireOpen(State domains,FamilyMarriageIntent.Route route) {
        boolean blocked=domains.family().get("pending")!=Nil.INSTANCE;
        if(route==FamilyMarriageIntent.Route.CHILD_MATRILINEAL)blocked|=domains.matrilineal().get("pending")!=Nil.INSTANCE;
        if(route==FamilyMarriageIntent.Route.CHILD_DEFAULT)blocked|=domains.matrilineal().get("pending")!=Nil.INSTANCE || domains.childDefault().get("pending")!=Nil.INSTANCE;
        if(blocked)throw new IllegalArgumentException("the original route or shared family proposal remains unresolved");
    }
    private static byte[] bytesDomain(Obj value) {return org.xar.ck3.control.continuity.ContinuityJson.canonical(OpportunityJson.toNode(value),org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES);}
    private static Arr ids(Set<BigInteger> values) {return new Arr(values.stream().sorted().<Value>map(IntegerValue::new).toList());}
    private static Obj one(List<Value> rows,Value candidate) {
        List<Obj> selected=rows.stream().map(FamilyJson::object).filter(row->eq(row.get("candidate_character_id"),candidate)).toList();
        if(selected.size()!=1)throw new IllegalArgumentException("one exact selected value required");return selected.getFirst();
    }
    private static IllegalArgumentException wrongRoute() {return new IllegalArgumentException("fresh native terms belong to a different immutable marriage intent route");}
}
