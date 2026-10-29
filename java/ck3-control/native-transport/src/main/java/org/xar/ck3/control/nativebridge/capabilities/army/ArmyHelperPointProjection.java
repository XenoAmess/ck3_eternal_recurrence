package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsMonthlyModel.PointRecordI32.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsMonthlyModel.PointRecordBool.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyHelperDomainProjection.number;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyHelperDomainProjection.bool;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyHelperDomainProjection.strings;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsMonthlyModel.*;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Current helper leaf stores in native order; source ordinary-return proof remains an independent guard. */
public final class ArmyHelperPointProjection {
    private ArmyHelperPointProjection(){}
    public enum Status { AVAILABLE,PARTIAL,UNAVAILABLE }
    public enum ReturnBasis { NO_PRECEDING_STATE4_CALL,HELPER_PHYSICAL_RECEIVER_NOT_PROVEN_SAME_CURRENT_ARMY,SAME_QUERY_CURRENT_DOMAIN_INPUTS_UNAVAILABLE,
        SAME_QUERY_DOMAIN_RECORD_RECEIVER_BASIS_NOT_MATCHED,SOURCE_CLOSED_SAME_QUERY_DOMAIN_RECORD_ORDINARY_RETURN,
        PRECEDING_DOMAIN_CALL_ORDINARY_CONTINUATION_UNRESOLVED,PRECEDING_STATE4_CALL_ADMISSION_UNRESOLVED }
    public enum MembershipBasis { NATIVE_NONPOSITIVE_COUNT_NO_WRITE,PRIOR_CONDITIONAL_MEMBERSHIP_HEADER_VALUE,OBSERVED_EMPTY_ERASE_ONLY_INVARIANT,
        UNRESOLVED_EARLIER_MEMBERSHIP_HEADER,OBSERVED_INITIAL_MEMBERSHIP_VECTOR,MEMBERSHIP_COUNT_AND_ORDERED_IDS_UNAVAILABLE }
    public record DataClear(boolean ready,Boolean admitted,Integer alias,Integer observed,Integer before,Integer after,Boolean changed){}
    public record Membership(boolean ready,Boolean admitted,Integer target,Integer receiver,Integer alias,boolean ordinaryReturnReady,
            ReturnBasis returnBasis,MembershipBasis valueBasis,List<Integer> before,List<Integer> after,Integer removed,Integer countAfter,List<String> missing) {
        public Membership{before=copy(before);after=copy(after);missing=List.copyOf(missing);}}
    public record RecordResult(int groupIndex,int storedIndex,DataClear clear,Membership membership){}
    public record ChildResult(int groupIndex,PointCharacter source,boolean ready,Boolean admitted,Integer alias,Integer byteBefore,Integer refBefore,
            Integer byteAfter,Integer refAfter,Boolean byteChanged,Boolean refChanged){}
    public sealed interface Effect permits ClearEffect,MembershipEffect,ChildEffect {}
    public record ClearEffect(RecordResult record) implements Effect {}
    public record MembershipEffect(RecordResult record) implements Effect {}
    public record ChildEffect(ChildResult child) implements Effect {}
    public record MembershipValue(int alias,List<Integer> after){public MembershipValue{after=copy(after);}}
    public record DataValue(int alias,int after){}
    public record ChildValue(int alias,int byteAfter,int refAfter){}
    public record Result(Status status,boolean ready,boolean dataReady,boolean membershipReady,boolean childReady,boolean continuationReady,
            HelperPointStore source,List<RecordResult> records,List<ChildResult> characters,List<Effect> effects,List<MembershipValue> memberships,
            List<DataValue> dataValues,List<ChildValue> childValues,List<String> missing) {
        public Result{records=List.copyOf(records);characters=List.copyOf(characters);effects=List.copyOf(effects);memberships=List.copyOf(memberships);dataValues=List.copyOf(dataValues);childValues=List.copyOf(childValues);missing=List.copyOf(missing);}}
    private record ReturnProof(boolean ready,ReturnBasis basis){}
    private static final class MutableMember {
        boolean ready;Boolean admitted;final Integer target,receiver,alias;final ReturnProof proof;MembershipBasis basis;List<Integer> before,after;Integer removed,countAfter;final List<String> missing=new ArrayList<>();
        MutableMember(PointRecord r,ReturnProof p){target=i(r,DATA_OWNER_REGIMENT_REFERENCE_ID);receiver=i(r,RECEIVER_REGIMENT_RESOLVED_ID);alias=i(r,MEMBERSHIP_ALIAS_ORDINAL);proof=p;}
        Membership freeze(){return new Membership(ready,admitted,target,receiver,alias,proof.ready(),proof.basis(),basis,before,after,removed,countAfter,missing);}
    }
    private static final class Memberships {
        final Map<Integer,List<Integer>> values=new LinkedHashMap<>();boolean unknown;
        void poison(Integer alias){if(alias!=null&&alias>=0){if(!List.of().equals(values.get(alias)))values.put(alias,null);}else{unknown=true;values.replaceAll((k,v)->List.of().equals(v)?v:null);}}
        void erase(PointRecord row,MutableMember out){
            Integer alias=i(row,MEMBERSHIP_ALIAS_ORDINAL),count=i(row,MEMBERSHIP_COUNT_2B4_RAW),target=i(row,DATA_OWNER_REGIMENT_REFERENCE_ID);List<Integer> observed=row.orderedPersistentRegimentIds2a8().orElse(null);
            if(count!=null&&count<=0){out.ready=true;out.removed=0;out.countAfter=count;out.after=count==0?List.of():null;out.basis=MembershipBasis.NATIVE_NONPOSITIVE_COUNT_NO_WRITE;if(alias!=null&&count==0)values.put(alias,List.of());return;}
            if(alias==null||alias<0||target==null){poison(alias);out.missing.add("membership_alias_and_raw_DATA8_target");return;}
            if(values.containsKey(alias)){out.before=values.get(alias);out.basis=MembershipBasis.PRIOR_CONDITIONAL_MEMBERSHIP_HEADER_VALUE;}
            else if(observed!=null&&observed.isEmpty()&&Integer.valueOf(0).equals(count)){out.before=List.of();out.basis=MembershipBasis.OBSERVED_EMPTY_ERASE_ONLY_INVARIANT;}
            else if(unknown){out.before=null;out.basis=MembershipBasis.UNRESOLVED_EARLIER_MEMBERSHIP_HEADER;}
            else if(count!=null&&count>0&&observed!=null&&observed.size()==count){out.before=observed;out.basis=MembershipBasis.OBSERVED_INITIAL_MEMBERSHIP_VECTOR;}
            else{out.before=null;out.basis=MembershipBasis.MEMBERSHIP_COUNT_AND_ORDERED_IDS_UNAVAILABLE;}
            if(out.before==null){poison(alias);out.missing.add("membership_value_after_prior_conditional_effects");return;}
            out.after=out.before.stream().filter(v->!v.equals(target)).toList();values.put(alias,out.after);out.ready=true;out.removed=out.before.size()-out.after.size();out.countAfter=out.after.size();
        }
    }
    public static Integer i(PointRecord row,PointRecordI32 key){return row.signed().get(key).orElse(null);}
    public static Boolean p(PointRecord row,PointRecordBool key){return row.predicates().get(key).orElse(null);}
    private static Integer ci(PointCharacter row,PointCharacterI32 key){return row.signed().get(key).orElse(null);}
    private static Boolean cp(PointCharacter row,PointCharacterBool key){return row.predicates().get(key).orElse(null);}
    private static Boolean admit(PointRecord row){
        Integer identity=i(row,RECORD_REGIMENT_RESOLVED_ID);Long magic=row.recordRegimentMagic14Raw().orElse(null);
        if(Boolean.FALSE.equals(p(row,DATA_RECORD_PRESENT))||Integer.valueOf(-1).equals(identity)||magic!=null&&magic!=0x52656769L)return false;
        return identity!=null&&Long.valueOf(0x52656769L).equals(magic)&&Boolean.TRUE.equals(p(row,DATA_RECORD_PRESENT))?Boolean.TRUE:null;
    }
    private static Integer character(PointRecord row){
        Integer title=i(row,RECEIVER_TITLE_REFERENCE_130_RAW),character=i(row,RECEIVER_CHARACTER_REFERENCE_12C_RAW);
        if(title==null||character==null)return null;
        if(title!=-1&&character==-1)return i(row,OWNER_TITLE_RESOLVED_ID)!=null&&p(row,OWNER_TITLE_USED_FALLBACK)!=null?i(row,OWNER_TITLE_HOLDER_CHARACTER_ID_128_RAW):null;
        return title==-1&&character!=-1?character:-1;
    }
    private static ReturnProof ordinary(Integer nativeArmy,HelperPointStore input,int group,PointRecord row,HelperDomain source,ArmyHelperDomainProjection.Result domain){
        if(!input.helperSameCurrentArmyPointer().orElse(false))return new ReturnProof(false,ReturnBasis.HELPER_PHYSICAL_RECEIVER_NOT_PROVEN_SAME_CURRENT_ARMY);
        if(source==null||source.entryArmyId().isEmpty()||!Objects.equals(source.entryArmyId().orElseThrow(),nativeArmy))return new ReturnProof(false,ReturnBasis.SAME_QUERY_CURRENT_DOMAIN_INPUTS_UNAVAILABLE);
        DomainRow match=source.rows().orElse(List.of()).stream().filter(r->Integer.valueOf(group).equals(ArmyHelperDomainProjection.signed(r,DomainI32.GROUP_INDEX))&&Objects.equals(i(row,STORED_INDEX),ArmyHelperDomainProjection.signed(r,DomainI32.STORED_INDEX))).findFirst().orElse(null);
        var projected=domain.records().stream().filter(r->Integer.valueOf(group).equals(ArmyHelperDomainProjection.signed(r.source(),DomainI32.GROUP_INDEX))&&Objects.equals(i(row,STORED_INDEX),ArmyHelperDomainProjection.signed(r.source(),DomainI32.STORED_INDEX))).findFirst().orElse(null);
        boolean matched=match!=null&&projected!=null&&i(row,RECEIVER_REGIMENT_RESOLVED_ID)!=null;
        if(matched)for(PointRecordI32 key:List.of(RECORD_REGIMENT_REFERENCE_ID,CHUNK_INDEX,RECORD_REGIMENT_RESOLVED_ID,DATA_STATE_18_RAW,DATA_OWNER_REGIMENT_REFERENCE_ID,RECEIVER_REGIMENT_RESOLVED_ID))
            matched&=Objects.equals(i(row,key),ArmyHelperDomainProjection.signed(match,DomainI32.valueOf(key.name())));
        if(matched)for(PointRecordBool key:List.of(RECORD_REGIMENT_USED_FALLBACK,DATA_RECORD_PRESENT,RECEIVER_REGIMENT_USED_FALLBACK))matched&=Objects.equals(p(row,key),ArmyHelperDomainProjection.predicate(match,DomainBool.valueOf(key.name())));
        if(matched)matched=Objects.equals(row.recordRegimentMagic14Raw().orElse(null),ArmyHelperDomainProjection.unsigned(match,DomainU32.RECORD_REGIMENT_MAGIC_14_RAW));
        if(!matched)return new ReturnProof(false,ReturnBasis.SAME_QUERY_DOMAIN_RECORD_RECEIVER_BASIS_NOT_MATCHED);
        return Boolean.TRUE.equals(projected.invocationAdmitted())&&projected.effectReady()?new ReturnProof(true,ReturnBasis.SOURCE_CLOSED_SAME_QUERY_DOMAIN_RECORD_ORDINARY_RETURN):new ReturnProof(false,ReturnBasis.PRECEDING_DOMAIN_CALL_ORDINARY_CONTINUATION_UNRESOLVED);
    }
    public static Result project(Integer nativeArmy,HelperPointStore input,HelperDomain domainSource,ArmyHelperDomainProjection.Result domain){
        if(input==null)return absent(null,"monthly_current_helper_point_store_inputs_v1");
        if(input.entryArmyId().isEmpty()||!Objects.equals(input.entryArmyId().orElseThrow(),nativeArmy))return absent(null,"explicit_entry_matches_current_native_army");
        Integer count=input.groupCount5cRaw().orElse(null);if(count==null)return absent(input,"helper_group_count_5c");
        if(count<=0)return new Result(Status.AVAILABLE,true,true,true,true,true,input,List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        if(input.groups().isEmpty())return absent(input,"ordered_helper_groups");
        boolean traversal=input.groups().orElseThrow().size()==count,dataReady=traversal,membershipReady=traversal,childReady=traversal,continuationReady=traversal;
        Map<Integer,Integer> dataValues=new LinkedHashMap<>();Map<Integer,ChildValue> childValues=new LinkedHashMap<>();Set<Integer> possibleData=new HashSet<>(),possibleChild=new HashSet<>();boolean unknownData=false,unknownChild=false;Memberships memberships=new Memberships();
        List<RecordResult> records=new ArrayList<>();List<ChildResult> characters=new ArrayList<>();List<Effect> effects=new ArrayList<>();List<String> missing=new ArrayList<>();
        for(var group:input.groups().orElseThrow()){
            Integer recordCount=group.recordCount14Raw().orElse(null);boolean known=recordCount!=null&&(recordCount<=0||group.recordRows().isPresent()&&group.recordRows().orElseThrow().size()==recordCount);
            List<PointRecord> sourceRecords=recordCount!=null&&recordCount<=0?List.of():group.recordRows().orElse(List.of());
            if(!known){dataReady=false;membershipReady=false;continuationReady=false;memberships.poison(null);unknownData=true;missing.add("groups["+group.groupIndex()+"].record_traversal");}
            for(var row:sourceRecords){
                Boolean admitted=admit(row);Integer alias=i(row,DATA_ALIAS_ORDINAL),observed=row.dataByte14Raw().orElse(null);
                Integer before=dataValues.containsKey(alias)?dataValues.get(alias):unknownData||possibleData.contains(alias)?null:observed;
                DataClear clear=new DataClear(admitted!=null,admitted,alias,observed,before,Boolean.TRUE.equals(admitted)?0:null,Boolean.TRUE.equals(admitted)&&before!=null?before!=0:null);
                if(Boolean.TRUE.equals(admitted)&&alias!=null)dataValues.put(alias,0);else if(!Boolean.FALSE.equals(admitted)){if(alias!=null)possibleData.add(alias);else unknownData=true;}
                Integer state=i(row,DATA_STATE_18_RAW);ReturnProof normal=new ReturnProof(true,ReturnBasis.NO_PRECEDING_STATE4_CALL);
                if(Boolean.TRUE.equals(admitted)&&Integer.valueOf(4).equals(state))normal=ordinary(nativeArmy,input,group.groupIndex(),row,domainSource,domain);
                else if(admitted==null&&!(state!=null&&state!=4)||Boolean.TRUE.equals(admitted)&&state==null)normal=new ReturnProof(false,ReturnBasis.PRECEDING_STATE4_CALL_ADMISSION_UNRESOLVED);
                MutableMember member=new MutableMember(row,normal);
                if(Boolean.FALSE.equals(admitted)||state!=null&&state!=4){member.ready=true;member.admitted=false;member.removed=0;}
                else if(Boolean.TRUE.equals(admitted)&&Integer.valueOf(4).equals(state)&&Boolean.FALSE.equals(p(row,CHARACTER_CHILD_1C0_PRESENT))){member.ready=true;member.admitted=false;member.removed=0;}
                else if(Boolean.TRUE.equals(admitted)&&Integer.valueOf(4).equals(state)){
                    Integer reference=character(row);if(reference!=null&&Objects.equals(i(row,SELECTED_CHARACTER_REFERENCE_ID),reference)&&i(row,SELECTED_CHARACTER_RESOLVED_ID)!=null&&p(row,SELECTED_CHARACTER_USED_FALLBACK)!=null&&Boolean.TRUE.equals(p(row,CHARACTER_CHILD_1C0_PRESENT))){member.admitted=true;memberships.erase(row,member);}
                }
                if(!member.ready){memberships.poison(i(row,MEMBERSHIP_ALIAS_ORDINAL));if(member.missing.isEmpty())member.missing.add("state4_owner_route_and_child_membership_inputs");}
                dataReady&=clear.ready();membershipReady&=member.ready;continuationReady&=normal.ready();
                RecordResult result=new RecordResult(group.groupIndex(),i(row,STORED_INDEX),clear,member.freeze());records.add(result);effects.add(new ClearEffect(result));effects.add(new MembershipEffect(result));
            }
            Integer charCount=group.characterCount2cRaw().orElse(null);boolean charsKnown=charCount!=null&&(charCount==0||charCount>0&&group.characterRows().isPresent()&&group.characterRows().orElseThrow().size()==charCount);
            List<PointCharacter> chars=charCount!=null&&charCount==0?List.of():charsKnown?group.characterRows().orElse(List.of()):List.of();
            if(!charsKnown){childReady=false;unknownChild=true;missing.add("groups["+group.groupIndex()+"].character_pointer_bound_traversal");}
            for(var row:chars){
                Boolean admitted=cp(row,PointCharacterBool.CHARACTER_CHILD_1B8_PRESENT);Integer alias=ci(row,PointCharacterI32.CHILD_1B8_ALIAS_ORDINAL);
                ChildValue prior=childValues.get(alias);Integer oldByte,oldReference;
                if(prior!=null){oldByte=prior.byteAfter();oldReference=prior.refAfter();}
                else if(unknownChild||possibleChild.contains(alias)){oldByte=null;oldReference=null;}
                else{oldByte=row.childByte108Raw().orElse(null);oldReference=ci(row,PointCharacterI32.CHILD_CHARACTER_REFERENCE_FC_RAW);}
                ChildResult result=new ChildResult(group.groupIndex(),row,admitted!=null,admitted,alias,oldByte,oldReference,Boolean.TRUE.equals(admitted)?0:null,Boolean.TRUE.equals(admitted)?-1:null,
                    Boolean.TRUE.equals(admitted)&&oldByte!=null?oldByte!=0:null,Boolean.TRUE.equals(admitted)&&oldReference!=null?oldReference!=-1:null);
                if(Boolean.TRUE.equals(admitted)&&alias!=null)childValues.put(alias,new ChildValue(alias,0,-1));else if(!Boolean.FALSE.equals(admitted)){if(alias!=null)possibleChild.add(alias);else unknownChild=true;}
                childReady&=result.ready();characters.add(result);effects.add(new ChildEffect(result));
            }
        }
        List<MembershipValue> members=new ArrayList<>();memberships.values.forEach((k,v)->members.add(new MembershipValue(k,v)));List<DataValue> data=new ArrayList<>();dataValues.forEach((k,v)->data.add(new DataValue(k,v)));
        boolean ready=dataReady&&membershipReady&&childReady&&continuationReady;
        return new Result(ready?Status.AVAILABLE:Status.PARTIAL,ready,dataReady,membershipReady,childReady,continuationReady,input,records,characters,effects,members,data,new ArrayList<>(childValues.values()),missing);
    }
    private static Result absent(HelperPointStore source,String gap){return new Result(Status.UNAVAILABLE,false,false,false,false,false,source,List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(gap));}
    public static ObjectNode encode(Result v){
        ObjectNode n=StrictJson.object();n.put("projection_kind","conditional_current_helper_point_stores");n.put("native_helper_rva","0x2A98590");n.put("source_contract_game_version","1.20.0.3");n.put("status",wire(v.status()));n.put("input_basis","isolated_current_helper_point_stores_under_explicit_ordinary_return_conditions");
        n.put("conditional_point_stores_ready",v.ready());n.put("data_clears_ready",v.dataReady());n.put("conditional_membership_erases_ready",v.membershipReady());n.put("group_child_stores_ready",v.childReady());n.put("membership_source_continuations_ready",v.continuationReady());
        HelperPointStore s=v.source();number(n,"entry_army_id",s==null?null:s.entryArmyId().orElse(null));number(n,"helper_resolved_army_id",s==null?null:s.helperResolvedArmyId().orElse(null));bool(n,"helper_used_fallback",s==null?null:s.helperUsedFallback().orElse(null));bool(n,"helper_same_current_army_pointer",s==null?null:s.helperSameCurrentArmyPointer().orElse(null));number(n,"group_count_5c_raw",s==null?null:s.groupCount5cRaw().orElse(null));
        ArrayNode records=n.putArray("record_projections");for(var r:v.records()){ObjectNode row=records.addObject();row.put("group_index",r.groupIndex());row.put("stored_index",r.storedIndex());row.set("data_clear",clear(r.clear()));row.set("membership_erase",membership(r.membership()));row.put("actual_effects_observed",false);row.putNull("actual_post_state");}
        ArrayNode chars=n.putArray("character_projections");v.characters().forEach(c->chars.add(child(c)));
        ArrayNode effects=n.putArray("ordered_effects");for(var e:v.effects())switch(e){case ClearEffect x->{ObjectNode r=clear(x.record().clear());r.put("kind","data_byte_14_clear");r.put("group_index",x.record().groupIndex());r.put("stored_index",x.record().storedIndex());effects.add(r);}case MembershipEffect x->{ObjectNode r=membership(x.record().membership());r.put("kind","membership_erase");r.put("group_index",x.record().groupIndex());r.put("stored_index",x.record().storedIndex());effects.add(r);}case ChildEffect x->{ObjectNode r=child(x.child());r.put("kind","group_child_constants");effects.add(r);}}
        ArrayNode members=n.putArray("membership_value_projections");for(var m:v.memberships()){ObjectNode r=members.addObject();r.put("membership_alias_ordinal",m.alias());r.put("conditional_ready",m.after()!=null);ids(r,"conditional_ordered_ids_after",m.after());}
        ArrayNode data=n.putArray("data_value_projections");for(var d:v.dataValues()){ObjectNode r=data.addObject();r.put("data_alias_ordinal",d.alias());r.put("conditional_byte_14_after",d.after());}
        ArrayNode children=n.putArray("child_value_projections");for(var c:v.childValues()){ObjectNode r=children.addObject();r.put("child_1b8_alias_ordinal",c.alias());r.put("conditional_byte_108_after",c.byteAfter());r.put("conditional_character_reference_fc_after",c.refAfter());}
        n.put("actual_effects_observed",false);n.put("actual_loss",false);n.putNull("actual_post_state");n.put("real_late_caller_stage_ready",false);n.put("full_helper_ready",false);n.put("actual_full_army_lifecycle_ready",false);strings(n,"missing_inputs",v.missing());return n;
    }
    private static ObjectNode clear(DataClear c){ObjectNode n=StrictJson.object();n.put("conditional_ready",c.ready());bool(n,"conditional_store_admitted",c.admitted());number(n,"data_alias_ordinal",c.alias());number(n,"observed_byte_14_raw",c.observed());number(n,"conditional_byte_14_before",c.before());number(n,"conditional_byte_14_after",c.after());bool(n,"conditional_changed",c.changed());return n;}
    private static ObjectNode membership(Membership m){ObjectNode n=StrictJson.object();n.put("conditional_ready",m.ready());bool(n,"conditional_call_admitted",m.admitted());number(n,"raw_DATA8_target",m.target());number(n,"receiver_regiment_resolved_id",m.receiver());number(n,"membership_alias_ordinal",m.alias());n.put("ordinary_return_condition","preceding_2C57020_call_returns_ordinarily");n.put("ordinary_return_ready",m.ordinaryReturnReady());n.put("ordinary_return_basis",wire(m.returnBasis()));if(m.valueBasis()==null)n.putNull("value_basis");else n.put("value_basis",wire(m.valueBasis()));ids(n,"conditional_ordered_ids_before",m.before());ids(n,"conditional_ordered_ids_after",m.after());number(n,"conditional_removed_count",m.removed());number(n,"conditional_count_after",m.countAfter());strings(n,"missing_inputs",m.missing());return n;}
    private static ObjectNode child(ChildResult c){ObjectNode n=StrictJson.object();n.put("group_index",c.groupIndex());number(n,"stored_index",ci(c.source(),PointCharacterI32.STORED_INDEX));number(n,"character_reference_id",ci(c.source(),PointCharacterI32.CHARACTER_REFERENCE_ID));number(n,"character_resolved_id",ci(c.source(),PointCharacterI32.CHARACTER_RESOLVED_ID));number(n,"child_1b8_alias_ordinal",c.alias());n.put("conditional_ready",c.ready());bool(n,"conditional_store_admitted",c.admitted());number(n,"conditional_byte_108_before",c.byteBefore());number(n,"conditional_character_reference_fc_before",c.refBefore());number(n,"conditional_byte_108_after",c.byteAfter());number(n,"conditional_character_reference_fc_after",c.refAfter());bool(n,"conditional_byte_108_changed",c.byteChanged());bool(n,"conditional_character_reference_fc_changed",c.refChanged());ArrayNode order=n.putArray("source_store_order");order.add("byte108=0").add("reload_Character_child1B8").add("DWORD_FC=-1");n.put("actual_effects_observed",false);n.putNull("actual_post_state");return n;}
    private static void ids(ObjectNode n,String key,List<Integer> value){n.putNull(key);if(value!=null){ArrayNode a=n.putArray(key);value.forEach(a::add);}}
    private static <T> List<T> copy(List<T> value){return value==null?null:List.copyOf(value);}
    private static String wire(Enum<?> value){return value.name().toLowerCase(java.util.Locale.ROOT);}
}
