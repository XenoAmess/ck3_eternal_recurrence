package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.CombatProjectionJson.*;

/** Original .3 26344C0/2C06D30/2C4D680 numeric slice. Never writes a Model or infers an Entry stage. */
public final class CombatKnightKernel {
    private CombatKnightKernel() { }
    private static final BigInteger MASK=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE),Q=BigInteger.valueOf(100000),BOUND=BigInteger.valueOf(3037000499L);
    public record PropertyContainer(Optional<List<Optional<BigInteger>>> keys,Optional<List<Optional<BigInteger>>> values,Optional<BigInteger> count) {
        public PropertyContainer {keys=keys.map(List::copyOf);values=values.map(List::copyOf);Objects.requireNonNull(count);}
    }
    public record Input(Optional<BigInteger> linkedCharacter,Optional<BigInteger> prowess,String linkedStage,
            Optional<BigInteger> selectedCharacter,String selectedStage,PropertyContainer context,
            List<Optional<BigInteger>> operands,Optional<BigInteger> damageMultiplier,Optional<BigInteger> toughnessMultiplier,
            Obj selectedSource,Obj externalSource) {
        public Input {Objects.requireNonNull(linkedCharacter);Objects.requireNonNull(prowess);Objects.requireNonNull(linkedStage);Objects.requireNonNull(selectedCharacter);Objects.requireNonNull(selectedStage);Objects.requireNonNull(context);operands=List.copyOf(operands);Objects.requireNonNull(damageMultiplier);Objects.requireNonNull(toughnessMultiplier);Objects.requireNonNull(selectedSource);Objects.requireNonNull(externalSource);}
    }
    public record Result(Optional<BigInteger> linkedCharacter,Optional<BigInteger> selectedCharacter,
            Optional<Obj> statCache,Optional<BigInteger> effectiveness,boolean ready,List<String> missing,Obj ledger) {
        public Result {Objects.requireNonNull(linkedCharacter);Objects.requireNonNull(selectedCharacter);Objects.requireNonNull(statCache);Objects.requireNonNull(effectiveness);missing=List.copyOf(missing);Objects.requireNonNull(ledger);}
    }
    public record Lookup(Optional<BigInteger> value,List<String> missing,Obj detail) {
        public Lookup {Objects.requireNonNull(value);missing=List.copyOf(missing);Objects.requireNonNull(detail);}
    }
    public static BigInteger wrap64(BigInteger value) {return BigInteger.valueOf(value.longValue());}
    /** Signed maximum decomposition is intentionally different from the cached minimum-decomposition primitive. */
    public static BigInteger fixedMultiply(BigInteger a,BigInteger b) {
        a=wrap64(a);b=wrap64(b);
        if(a.add(BOUND).and(MASK).compareTo(BOUND.shiftLeft(1))<=0&&b.add(BOUND).and(MASK).compareTo(BOUND.shiftLeft(1))<=0)
            return wrap64(a.multiply(b)).divide(Q);
        BigInteger minimum=a.min(b),maximum=a.max(b),quotient=maximum.divide(Q);
        BigInteger remainder=wrap64(maximum.subtract(wrap64(quotient.multiply(Q))));
        return wrap64(wrap64(quotient.multiply(minimum)).add(wrap64(remainder.multiply(minimum)).divide(Q)));
    }
    static Optional<BigInteger> optional(JsonNode n) {return n!=null&&n.isIntegralNumber()?Optional.of(n.bigIntegerValue()):Optional.empty();}
    static List<Optional<BigInteger>> optionalList(JsonNode n) {
        List<Optional<BigInteger>> result=new ArrayList<>();if(n!=null&&n.isArray())for(var item:n)result.add(optional(item));return List.copyOf(result);
    }
    static PropertyContainer container(JsonNode keys,JsonNode values,JsonNode count) {
        return new PropertyContainer(keys!=null&&keys.isArray()?Optional.of(optionalList(keys)):Optional.empty(),values!=null&&values.isArray()?Optional.of(optionalList(values)):Optional.empty(),optional(count));
    }
    static final class Calculation {
        final LinkedHashSet<String> missing=new LinkedHashSet<>();final ArrayNode lookups=obj().arrayNode();
        BigInteger number(Optional<BigInteger> n,String path,int bits) {if(n.isEmpty()){missing.add(path);return null;}return bits==32?BigInteger.valueOf(n.orElseThrow().intValue()):wrap64(n.orElseThrow());}
        BigInteger item(Optional<List<Optional<BigInteger>>> list,int index,String path,int bits) {
            if(list.isEmpty()||index>=list.orElseThrow().size()){missing.add(path);return null;}
            return number(list.orElseThrow().get(index),path,bits);
        }
        BigInteger property(PropertyContainer pc,int key) {
            String p="context.aggregate_properties";key&=65535;
            if(key==65535)return observed(p,key,"native_sentinel_zero",BigInteger.ZERO,null);
            BigInteger countRaw=number(pc.count(),p+".count",32);if(countRaw==null)return null;int count=countRaw.intValue();
            if(count==0)return observed(p,key,"native_empty_zero",BigInteger.ZERO,null);
            if(count<0){missing.add(p+".negative_count_address_view");return null;}
            if(pc.keys().isEmpty()){missing.add(p+".keys_u16");return null;}
            int offset=0,remaining=count;
            while(remaining>0){int half=remaining>>>1,probe=offset+half;BigInteger raw=item(pc.keys(),probe,p+".keys_u16["+probe+"]",64);if(raw==null)return null;if(raw.and(BigInteger.valueOf(65535)).intValue()<key)offset+=remaining-half;remaining=half;}
            if(offset==count)return observed(p,key,"native_missing_key_zero",BigInteger.ZERO,null);
            BigInteger raw=item(pc.keys(),offset,p+".keys_u16["+offset+"]",64);if(raw==null)return null;
            if(key<raw.and(BigInteger.valueOf(65535)).intValue())return observed(p,key,"native_missing_key_zero",BigInteger.ZERO,null);
            BigInteger value=item(pc.values(),offset,p+".values_q64["+offset+"]",64);
            return observed(p,key,value==null?"partial":"value",value,offset);
        }
        BigInteger observed(String path,int key,String status,BigInteger value,Integer index) {
            var n=obj().put("path",path).put("key",key).put("status",status);nullable(n,"value_q64",value);if(index!=null)n.put("index",index);lookups.add(n);return value;
        }
    }
    public static Lookup lookup(PropertyContainer pc,int key) {
        var c=new Calculation();var value=c.property(pc,key);var d=obj();d.set("lookups",c.lookups);strings(d,"missing_inputs",c.missing);
        return new Lookup(Optional.ofNullable(value),List.copyOf(c.missing),immutable(d));
    }
    public static Result compute(Input input) {
        var c=new Calculation();if(input.linkedCharacter().isEmpty())c.missing.add("linked_character_full_id");if(input.selectedCharacter().isEmpty())c.missing.add("selected_character_full_id");
        BigInteger effectiveness=Q;var terms=obj().arrayNode();
        for(int i=0;i<9;i++) {
            String path="operand_raw["+i+"]";BigInteger operand=c.number(i<input.operands().size()?input.operands().get(i):Optional.empty(),path,64),modifier=null,term=null;String branch;
            if(operand==null)branch="missing_operand";
            else if(operand.signum()==0){term=BigInteger.ZERO;branch="zero_operand_skips_property";}
            else {modifier=c.property(input.context(),0xc1+i);term=modifier==null?null:fixedMultiply(modifier,operand);branch="mode0_scaled_property";}
            effectiveness=effectiveness==null||term==null?null:wrap64(effectiveness.add(term));
            var n=terms.addObject().put("key",0xc1+i).put("branch",branch);nullable(n,"operand_q64",operand);nullable(n,"modifier_q64",modifier);nullable(n,"term_q64",term);nullable(n,"accumulated_q64",effectiveness);
        }
        var prowess=c.number(input.prowess(),"linked_prowess_points",32);var damage=c.number(input.damageMultiplier(),"loaded_damage_multiplier",32);var toughness=c.number(input.toughnessMultiplier(),"loaded_toughness_multiplier",32);
        var common=prowess==null||effectiveness==null?null:wrap64(prowess.max(BigInteger.ONE).multiply(effectiveness));boolean ready=c.missing.isEmpty();Optional<Obj> stats=Optional.empty();
        if(ready){var s=obj().put("effective_max_size",0).put("effective_siege_raw",0).put("effective_damage_raw",wrap64(common.multiply(damage))).put("effective_toughness_raw",wrap64(common.multiply(toughness))).put("effective_pursuit_raw",0).put("effective_screen_raw",0);stats=Optional.of(immutable(s));}
        var ledger=obj().put("source","26344C0->2C06D30->28BFC70->2C06B00/2C4D680").put("linked_stage",input.linkedStage()).put("selected_stage",input.selectedStage()).put("prowess_lower_bound",1);
        nullable(ledger,"linked_prowess_points",prowess);nullable(ledger,"common_wrap64_product",common);nullable(ledger,"loaded_damage_multiplier",damage);nullable(ledger,"loaded_toughness_multiplier",toughness);
        ledger.set("effectiveness_terms",terms);ledger.set("property_lookups",c.lookups);ledger.set("selected_source",node(input.selectedSource()));ledger.set("external_source",node(input.externalSource()));ledger.put("province_used_by_special_branch",false).put("alive_gate_added",false).put("constructor_final_stage_inferred",false);
        return new Result(input.linkedCharacter(),input.selectedCharacter(),stats,Optional.ofNullable(effectiveness),ready,List.copyOf(c.missing),immutable(ledger));
    }
}
