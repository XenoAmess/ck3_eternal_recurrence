package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsMonthlyModel.DomainI32.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsMonthlyModel.DomainU32.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsMonthlyModel.DomainBool.*;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsMonthlyModel.*;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Isolated ordered 2C57020 effects from an explicit same-query current helper entry. No real stores. */
public final class ArmyHelperDomainProjection {
    private ArmyHelperDomainProjection(){}
    public enum Status { AVAILABLE,PARTIAL,UNAVAILABLE }
    public enum Branch { NULL_DATA_RECORD,INVALID_CONTAINING_REGIMENT,DATA_NOT_STATE4,RECEIVER_NOT_STATE4,INVALID_PREDICATE_DOMAIN,ZERO_PREDICATE_FLAG,ZERO_NATIVE_COUNT,INVALID_DOMAIN_OWNER_CHARACTER,DOMAIN_UPDATE }
    public enum OwnerRoute { TITLE_HOLDER,DIRECT_CHARACTER,MINUS_ONE_CHARACTER_FALLBACK }
    public enum ValueBasis { UNRESOLVED_EARLIER_DOMAIN_TARGET,PRIOR_CONDITIONAL_DOMAIN_ALIAS_VALUE,OBSERVED_INITIAL_DOMAIN_VALUE }
    public record Count(Integer count,List<Integer> deltas,boolean witnessReady){public Count{deltas=Collections.unmodifiableList(new ArrayList<>(deltas));}}
    public record Item(DomainRow source,Branch branch,Boolean invocationAdmitted,boolean invocationReady,Boolean predicateAdmitted,
            OwnerRoute ownerRoute,Integer selectedCharacter,Count count,Long delta,Boolean storeAdmitted,boolean storeAdmissionReady,
            boolean effectReady,boolean valueReady,ValueBasis valueBasis,Long before,Long after,List<String> missing){public Item{missing=List.copyOf(missing);}}
    public record Alias(int ordinal,Integer domainId,Long initial,Long after){}
    public record Result(Status status,boolean ready,boolean orderReady,Integer entryArmy,Integer groupCount,List<Item> records,
            List<Alias> aliases,Integer storeCount,List<String> missing){public Result{records=List.copyOf(records);aliases=List.copyOf(aliases);missing=List.copyOf(missing);}}
    private static final class Working {
        final DomainRow source;final Count count;final OwnerRoute route;final Integer selected;final Long delta;
        Branch branch;Boolean invocation,predicate,store;boolean invocationReady,storeReady,effectReady,valueReady;ValueBasis basis;Long before,after;final List<String> missing=new ArrayList<>();
        Working(DomainRow row){source=row;count=count(row);var choice=character(row);selected=choice.reference;route=choice.route;delta=count.count()==null?null:count.count()*100000L;}
        void noStore(Branch value,Boolean invoked){branch=value;store=false;storeReady=true;effectReady=true;if(invoked!=null){invocation=invoked;invocationReady=true;}}
        void gap(String field){missing.add(field);}
        Item freeze(){return new Item(source,branch,invocation,invocationReady,predicate,route,selected,count,delta,store,storeReady,effectReady,valueReady,basis,before,after,missing);}
    }
    private record CharacterChoice(Integer reference,OwnerRoute route){}
    public static Integer signed(DomainRow r,DomainI32 k){return r.signed().get(k).orElse(null);}
    public static Long unsigned(DomainRow r,DomainU32 k){return r.unsigned().get(k).orElse(null);}
    public static Boolean predicate(DomainRow r,DomainBool k){return r.predicates().get(k).orElse(null);}
    public static Count count(DomainRow r){
        Integer base=signed(r,COUNT_BASE_128_RAW);if(base==null||r.countRecords().isEmpty())return new Count(null,List.of(),false);
        int acc=base;boolean witness=true,complete=true;List<Integer> deltas=new ArrayList<>();
        for(var row:r.countRecords().orElseThrow()){
            Integer a=row.count00Raw().orElse(null),b=row.count04Raw().orElse(null),state=row.state18Raw().orElse(null),delta;
            witness&=a!=null&&b!=null&&state!=null;
            if(a==null)delta=null;else if(a==0)delta=0;else if(b==null)delta=null;else if(b!=0)delta=b-a;else if(state==null)delta=null;else delta=state==3?0:-a;
            deltas.add(delta);if(delta!=null)acc+=delta;else complete=false;
        }
        return new Count(complete?acc:null,deltas,witness);
    }
    private static CharacterChoice character(DomainRow r){
        Integer title=signed(r,RECEIVER_TITLE_REFERENCE_130_RAW),character=signed(r,RECEIVER_CHARACTER_REFERENCE_12C_RAW);
        if(title==null||character==null)return new CharacterChoice(null,null);
        if(title!=-1&&character==-1){Integer holder=signed(r,OWNER_TITLE_HOLDER_CHARACTER_ID_128_RAW);return new CharacterChoice(signed(r,OWNER_TITLE_RESOLVED_ID)!=null&&predicate(r,OWNER_TITLE_USED_FALLBACK)!=null&&holder!=null?holder:null,OwnerRoute.TITLE_HOLDER);}
        return title==-1&&character!=-1?new CharacterChoice(character,OwnerRoute.DIRECT_CHARACTER):new CharacterChoice(-1,OwnerRoute.MINUS_ONE_CHARACTER_FALLBACK);
    }
    private static Working record(DomainRow r){
        Working w=new Working(r);
        if(Boolean.FALSE.equals(predicate(r,DATA_RECORD_PRESENT))){w.noStore(Branch.NULL_DATA_RECORD,false);return w;}
        Integer resolved=signed(r,RECORD_REGIMENT_RESOLVED_ID);Long magic=unsigned(r,RECORD_REGIMENT_MAGIC_14_RAW);
        if(Integer.valueOf(-1).equals(resolved)||magic!=null&&magic!=0x52656769L){w.noStore(Branch.INVALID_CONTAINING_REGIMENT,false);return w;}
        if(resolved==null||!Long.valueOf(0x52656769L).equals(magic)){w.gap("containing_regiment_identity_10_14");return w;}
        if(!Boolean.TRUE.equals(predicate(r,DATA_RECORD_PRESENT))){w.gap("data_record_present");return w;}
        Integer state=signed(r,DATA_STATE_18_RAW);if(state==null){w.gap("data_state_18_raw");return w;}
        if(state!=4){w.noStore(Branch.DATA_NOT_STATE4,false);return w;}w.invocation=true;w.invocationReady=true;
        Integer receiver=signed(r,RECEIVER_STATE_138_RAW);if(receiver==null){w.gap("receiver_state_138_raw");return w;}
        if(receiver!=4){w.noStore(Branch.RECEIVER_NOT_STATE4,null);return w;}
        if(signed(r,RECEIVER_REGIMENT_RESOLVED_ID)==null){w.gap("selected_persistent_receiver");return w;}
        if(w.selected==null){w.gap("title_holder_or_direct_character_route");return w;}
        if(!Objects.equals(signed(r,SELECTED_CHARACTER_REFERENCE_ID),w.selected)){w.gap("selected_character_reference_matches_source_route");return w;}
        if(signed(r,SELECTED_CHARACTER_RESOLVED_ID)==null||predicate(r,SELECTED_CHARACTER_USED_FALLBACK)==null){w.gap("selected_character_generation_resolution");return w;}
        Boolean child=predicate(r,CHARACTER_DOMAIN_CHILD_PRESENT);Integer reference=signed(r,DOMAIN_REFERENCE_ID);
        if(child==null||reference==null){w.gap("character_domain_child_reference");return w;}
        if(!child&&reference!=-1){w.gap("absent_character_child_selects_minus_one_domain");return w;}
        Integer domain=signed(r,DOMAIN_RESOLVED_ID);Long domainMagic=unsigned(r,DOMAIN_MAGIC_0C_RAW);
        if(Integer.valueOf(-1).equals(domain)||domainMagic!=null&&domainMagic!=0x446f6d69L){w.predicate=false;w.noStore(Branch.INVALID_PREDICATE_DOMAIN,null);return w;}
        if(domain==null||!Long.valueOf(0x446f6d69L).equals(domainMagic)){w.gap("domain_identity_8_0c");return w;}
        if(!Boolean.TRUE.equals(predicate(r,DOMAIN_DATA_30_PRESENT))){w.gap("readable_unchecked_domain_data_30_receiver");return w;}
        Integer flag=r.domainFlag17eRaw().orElse(null);if(flag==null){w.gap("domain_flag_17e_raw");return w;}w.predicate=flag!=0;
        if(flag==0){w.noStore(Branch.ZERO_PREDICATE_FLAG,null);return w;}
        if(w.count.count()==null){w.gap("native_seven_record_count");return w;}if(w.count.count()==0){w.noStore(Branch.ZERO_NATIVE_COUNT,null);return w;}
        Integer owner=signed(r,DOMAIN_OWNER_CHARACTER_RESOLVED_ID);Long ownerMagic=unsigned(r,DOMAIN_OWNER_CHARACTER_MAGIC_1C_RAW);
        if(Integer.valueOf(-1).equals(owner)||ownerMagic!=null&&ownerMagic!=0x43686172L){w.noStore(Branch.INVALID_DOMAIN_OWNER_CHARACTER,null);return w;}
        if(owner==null||!Long.valueOf(0x43686172L).equals(ownerMagic)){w.gap("domain_owner_character_identity_18_1c");return w;}
        w.branch=Branch.DOMAIN_UPDATE;w.store=true;w.storeReady=true;return w;
    }
    public static Result project(Integer nativeArmy,HelperDomain input){
        if(input==null)return absent("monthly_current_helper_domain_inputs_v1");
        Integer entry=input.entryArmyId().orElse(null),count=input.groupCount5cRaw().orElse(null);
        if(entry==null||!entry.equals(nativeArmy))return absent("explicit_entry_matches_current_native_carmy_id");
        if(count==null)return new Result(Status.UNAVAILABLE,false,false,entry,null,List.of(),List.of(),null,List.of("group_count_5c_raw"));
        if(count<=0)return new Result(Status.AVAILABLE,true,true,entry,count,List.of(),List.of(),0,List.of());
        if(input.rows().isEmpty())return new Result(Status.UNAVAILABLE,false,false,entry,count,List.of(),List.of(),null,List.of("ordered_current_group_records"));
        Map<Integer,Long> values=new LinkedHashMap<>(),initial=new LinkedHashMap<>();Map<Integer,Integer> identities=new LinkedHashMap<>();boolean unknownTarget=false;int stores=0;List<Item> projected=new ArrayList<>();
        for(var r:input.rows().orElseThrow()){
            Working w=record(r);Integer alias=signed(r,DOMAIN_ALIAS_ORDINAL);boolean known=alias!=null&&alias>=0;
            if(known){if(!identities.containsKey(alias))identities.put(alias,signed(r,DOMAIN_RESOLVED_ID));if(!initial.containsKey(alias))initial.put(alias,r.domainValue48Raw64().orElse(null));}
            if(Boolean.TRUE.equals(w.store)){
                stores++;
                if(!known){w.gap("native_domain_alias_ordinal");unknownTarget=true;values.replaceAll((k,v)->null);}
                else {
                    if(unknownTarget){w.before=null;w.basis=ValueBasis.UNRESOLVED_EARLIER_DOMAIN_TARGET;}
                    else if(values.containsKey(alias)){w.before=values.get(alias);w.basis=ValueBasis.PRIOR_CONDITIONAL_DOMAIN_ALIAS_VALUE;}
                    else{w.before=r.domainValue48Raw64().orElse(null);w.basis=ValueBasis.OBSERVED_INITIAL_DOMAIN_VALUE;}
                    if(w.before!=null){w.after=Math.max(0L,w.before+w.delta);values.put(alias,w.after);w.valueReady=true;w.effectReady=true;}
                    else{values.put(alias,null);w.gap("domain_value_basis_after_prior_conditional_effects");}
                }
            }else if(w.store==null){if(known)values.put(alias,null);else{unknownTarget=true;values.replaceAll((k,v)->null);}}
            else if(known&&!values.containsKey(alias))values.put(alias,unknownTarget?null:r.domainValue48Raw64().orElse(null));
            projected.add(w.freeze());
        }
        List<Alias> aliases=new ArrayList<>();values.forEach((alias,value)->aliases.add(new Alias(alias,identities.get(alias),initial.get(alias),value)));
        boolean ready=projected.stream().allMatch(Item::effectReady);List<String> missing=new ArrayList<>();
        for(var p:projected)for(String gap:p.missing())missing.add("rows["+signed(p.source(),GROUP_INDEX)+":"+signed(p.source(),STORED_INDEX)+"]."+gap);
        return new Result(ready?Status.AVAILABLE:Status.PARTIAL,ready,true,entry,count,projected,aliases,projected.stream().allMatch(Item::storeAdmissionReady)?stores:null,missing);
    }
    private static Result absent(String gap){return new Result(Status.UNAVAILABLE,false,false,null,null,List.of(),List.of(),null,List.of(gap));}
    public static ObjectNode encode(Result v){
        ObjectNode n=StrictJson.object();n.put("projection_kind","conditional_current_helper_domain_updates");n.put("native_subsystem_rva","0x2C57020");n.put("parent_helper_rva","0x2A98590");n.put("source_contract_game_version","1.20.0.3");n.put("input_basis","isolated_ordered_2C57020_invocations_from_explicit_current_helper_entry");n.put("status",wire(v.status()));n.put("conditional_domain_updates_ready",v.ready());n.put("conditional_invocation_order_ready",v.orderReady());number(n,"entry_army_id",v.entryArmy());number(n,"group_count_5c_raw",v.groupCount());number(n,"conditional_domain_store_count",v.storeCount());
        ArrayNode records=n.putArray("record_projections");for(var p:v.records()){
            DomainRow s=p.source();ObjectNode r=records.addObject();number(r,"group_index",signed(s,GROUP_INDEX));number(r,"stored_index",signed(s,STORED_INDEX));number(r,"record_regiment_reference_id",signed(s,RECORD_REGIMENT_REFERENCE_ID));number(r,"chunk_index",signed(s,CHUNK_INDEX));number(r,"receiver_regiment_resolved_id",signed(s,RECEIVER_REGIMENT_RESOLVED_ID));
            en(r,"conditional_branch",p.branch());bool(r,"conditional_invocation_admitted",p.invocationAdmitted());r.put("conditional_invocation_ready",p.invocationReady());bool(r,"predicate_admitted",p.predicateAdmitted());en(r,"owner_character_route",p.ownerRoute());number(r,"derived_selected_character_reference_id",p.selectedCharacter());r.put("conditional_native_count_ready",p.count().count()!=null);number(r,"conditional_native_count",p.count().count());ArrayNode deltas=r.putArray("conditional_count_record_deltas");for(Integer d:p.count().deltas())if(d==null)deltas.addNull();else deltas.add(d.intValue());r.put("count_source_witness_ready",p.count().witnessReady());longNumber(r,"conditional_delta_raw64",p.delta());number(r,"domain_resolved_id",signed(s,DOMAIN_RESOLVED_ID));number(r,"domain_alias_ordinal",signed(s,DOMAIN_ALIAS_ORDINAL));
            bool(r,"conditional_domain_store_admitted",p.storeAdmitted());r.put("conditional_store_admission_ready",p.storeAdmissionReady());r.put("conditional_effect_ready",p.effectReady());r.put("conditional_domain_value_ready",p.valueReady());en(r,"domain_value_input_basis",p.valueBasis());longNumber(r,"conditional_domain_value_48_before_raw64",p.before());longNumber(r,"conditional_domain_value_48_after_raw64",p.after());strings(r,"missing_inputs",p.missing());r.put("actual_effects_observed",false);r.putNull("actual_domain_value_48_after_raw64");
        }
        ArrayNode aliases=n.putArray("domain_value_projections");for(var a:v.aliases()){ObjectNode r=aliases.addObject();r.put("domain_alias_ordinal",a.ordinal());number(r,"domain_resolved_id",a.domainId());longNumber(r,"observed_initial_domain_value_48_raw64",a.initial());r.put("conditional_ready",a.after()!=null);longNumber(r,"conditional_domain_value_48_after_raw64",a.after());r.putNull("actual_domain_value_48_after_raw64");}
        n.put("actual_effects_observed",false);n.putNull("actual_domain_value_48_after_raw64");n.put("real_late_caller_stage_ready",false);n.put("full_helper_ready",false);n.put("actual_full_army_lifecycle_ready",false);n.put("actual_loss",false);n.putNull("actual_post_state");n.putNull("actual_post_stage_current");n.put("full_monthly_applied_loss_ready",false);strings(n,"missing_inputs",v.missing());return n;
    }
    public static void number(ObjectNode n,String k,Integer v){if(v==null)n.putNull(k);else n.put(k,v.intValue());}
    public static void longNumber(ObjectNode n,String k,Long v){if(v==null)n.putNull(k);else n.put(k,v.longValue());}
    public static void bool(ObjectNode n,String k,Boolean v){if(v==null)n.putNull(k);else n.put(k,v.booleanValue());}
    public static void en(ObjectNode n,String k,Enum<?> v){if(v==null)n.putNull(k);else n.put(k,wire(v));}
    public static void strings(ObjectNode n,String k,List<String> v){ArrayNode a=n.putArray(k);v.forEach(a::add);}
    private static String wire(Enum<?> v){return v.name().toLowerCase(java.util.Locale.ROOT);}
}
