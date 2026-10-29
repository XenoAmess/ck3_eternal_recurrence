package org.xar.ck3.control.wave2.planning.jointintake;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalProposals;

/** Pure migration of the real M5 producer's valued-choice expansion. No Native, preparation, writer or completeness authority is minted. */
public final class FamilyProposalPool {
    public static final String SCHEMA="xar.java.m5-family-proposal-source/v2";
    public static final String SUBMIT="submit-observed-first-heir-marriage-v1-private";
    private FamilyProposalPool() { }
    public sealed interface Source permits Pool,ExistingBetrothal {
        Obj originalPlan();
        List<Obj> plans();
    }
    /** Existing bilateral fulfillment is a different real source, not a missing valued-pool fallback. */
    public record ExistingBetrothal(Obj originalPlan) implements Source {
        public ExistingBetrothal {
            Objects.requireNonNull(originalPlan);
            require(new Text(BetrothalProposals.SUBMIT_STEP).equals(originalPlan.get("selected_step")),"actual existing-betrothal fulfillment source required");
        }
        @Override public List<Obj> plans(){return List.of(originalPlan);}
    }
    public record Variant(BigInteger candidateCharacterId,Obj plan) {
        public Variant {
            positive(candidateCharacterId);Objects.requireNonNull(plan);
            require(candidateCharacterId.equals(OpportunityJson.integer(object(plan.get("family_marriage_choice")).get("candidate_character_id"),"actual candidate")),"variant candidate differs from its actual choice");
            require(candidateCharacterId.equals(OpportunityJson.integer(object(plan.get("family_marriage_private_diagnostic")).get("selected_candidate_character_id"),"actual selected diagnostic")),"variant diagnostic selects another candidate");
        }
    }
    public record Pool(Obj originalPlan,List<Variant> variants) implements Source {
        public Pool {
            Objects.requireNonNull(originalPlan);variants=List.copyOf(variants);
            require(new Text(SUBMIT).equals(originalPlan.get("selected_step")),"actual approved first-heir source required");
            List<Value> choices=OpportunityJson.array(originalPlan.get("family_marriage_valued_choices"),"actual valued choices");
            require(!choices.isEmpty()&&choices.size()<=5&&variants.size()==choices.size(),"actual bounded valued-choice vector required; no selected-singleton fallback");
            require(choices.getFirst().equals(originalPlan.get("family_marriage_choice")),"actual selected choice must be the first owning-policy choice");
            require(variants.getFirst().plan().equals(originalPlan),"the selected original plan must be preserved completely");
            Obj diagnostic=object(originalPlan.get("family_marriage_private_diagnostic"));
            List<Value> proof=OpportunityJson.array(diagnostic.get("rows"),"original five-row diagnostic");
            require(proof.size()==5,"the real complete five-row native proof is required");
            Set<BigInteger> candidates=new HashSet<>();
            for(int i=0;i<variants.size();i++) {
                Variant variant=variants.get(i);Obj choice=object(choices.get(i));BigInteger candidate=OpportunityJson.integer(choice.get("candidate_character_id"),"actual choice candidate");
                positive(candidate);require(candidates.add(candidate),"actual valued choices repeat a candidate");
                require(candidate.equals(variant.candidateCharacterId())&&variant.plan().get("family_marriage_choice").equals(choice),"variant reordered or replaced its actual owning-policy choice");
                require(proof.stream().filter(row->candidate.equals(OpportunityJson.integer(object(row).get("candidate_character_id"),"native diagnostic candidate"))).count()==1,
                        "actual valued candidate is not unique in its native five-row proof");
                Obj expected=variantPlan(originalPlan,choice,diagnostic,candidate);
                require(expected.equals(variant.plan()),"variant changed data beyond the original choice/diagnostic and its Java context reference");
            }
        }
        @Override public List<Obj> plans(){return variants.stream().map(Variant::plan).toList();}
        public Variant candidate(BigInteger actualId){positive(actualId);return variants.stream().filter(v->v.candidateCharacterId().equals(actualId)).findFirst().orElseThrow(()->new IllegalArgumentException("candidate absent from actual M5 pool"));}
    }
    public static Pool collect(Obj actualOwningPolicyPlan) {
        Objects.requireNonNull(actualOwningPolicyPlan);
        List<Value> choices=OpportunityJson.array(actualOwningPolicyPlan.get("family_marriage_valued_choices"),"actual valued choices");
        Obj diagnostic=object(actualOwningPolicyPlan.get("family_marriage_private_diagnostic"));
        List<Variant> variants=new ArrayList<>();
        for(Value raw:choices) {
            Obj choice=object(raw);BigInteger candidate=OpportunityJson.integer(choice.get("candidate_character_id"),"actual native candidate");positive(candidate);
            variants.add(new Variant(candidate,variantPlan(actualOwningPolicyPlan,choice,diagnostic,candidate)));
        }
        return new Pool(actualOwningPolicyPlan,variants);
    }
    private static Obj variantPlan(Obj original,Obj choice,Obj diagnostic,BigInteger candidate) {
        Obj result=original.with("family_marriage_choice",choice).with("family_marriage_private_diagnostic",diagnostic.with("selected_candidate_character_id",new IntegerValue(candidate)));
        Value raw=original.get("family_marriage_war_context");
        if(raw!=null&&raw!=Nil.INSTANCE) {
            Obj context=object(raw);
            require(original.get("family_marriage_choice").equals(context.get("proposal")),"Java family resource context references another owning-policy choice");
            result=result.with("family_marriage_war_context",context.with("proposal",choice));
        }
        return result;
    }
    /** One full original plus its complete actual choice vector. No diagnostic or projection is repeated on the wire. */
    public static Obj toJson(Source source) {
        Objects.requireNonNull(source);
        if(source instanceof ExistingBetrothal actual)return new Obj(Map.of("schema",new Text(SCHEMA),"kind",new Text("existing_betrothal"),"original_plan",actual.originalPlan()));
        if(!(source instanceof Pool pool))throw new IllegalArgumentException("unknown typed family source");
        return new Obj(Map.of("schema",new Text(SCHEMA),"kind",new Text("valued_first_heir"),"original_plan",pool.originalPlan(),
                "choice_indices",new Arr(java.util.stream.IntStream.range(0,pool.variants().size()).<Value>mapToObj(i->new IntegerValue(BigInteger.valueOf(i))).toList())));
    }
    public static byte[] encode(Pool pool) {
        return encodeSource(pool);
    }
    public static byte[] encodeSource(Source source) {
        byte[] raw=OpportunityJson.encode(toJson(source));
        require(raw.length<=131072,"M5 pool exceeds its explicit JSON contract bound");return raw;
    }
    public static Pool decode(byte[] raw) {
        return fromJson(object(OpportunityJson.parse(raw)));
    }
    public static Pool fromJson(Obj envelope) {
        Source actual=readSource(envelope);
        if(!(actual instanceof Pool pool))throw new IllegalArgumentException("a valued first-heir pool cannot be replaced by another typed family source");return pool;
    }
    public static Source decodeSource(byte[] raw){return readSource(object(OpportunityJson.parse(raw)));}
    public static Source readSource(Obj envelope) {
        require(new Text(SCHEMA).equals(envelope.get("schema")),"exact compact M5 family v2 schema required");
        String kind=OpportunityJson.text(envelope.get("kind"),"actual family source kind");
        if(kind.equals("existing_betrothal")) {
            require(envelope.members().keySet().equals(Set.of("schema","kind","original_plan")),"exact typed existing-betrothal fields required");
            return new ExistingBetrothal(object(envelope.get("original_plan")));
        }
        require(kind.equals("valued_first_heir")&&envelope.members().keySet().equals(Set.of("schema","kind","original_plan","choice_indices")),"exact compact valued first-heir fields required");
        Pool pool=collect(object(envelope.get("original_plan")));
        List<Value> indices=OpportunityJson.array(envelope.get("choice_indices"),"complete actual choice indices");
        require(indices.size()==pool.variants().size(),"compact source must cover every actual valued choice exactly once");
        for(int i=0;i<indices.size();i++)require(OpportunityJson.integer(indices.get(i),"choice index").equals(BigInteger.valueOf(i)),"compact choice indices must retain complete actual order");
        return pool;
    }
    private static Obj object(Value value){return OpportunityJson.object(value,"actual M5 family object");}
    private static void positive(BigInteger value){require(value!=null&&value.signum()>0&&value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0,"bounded positive native Character ID required");}
    private static void require(boolean valid,String reason){if(!valid)throw new IllegalArgumentException(reason);}
}
