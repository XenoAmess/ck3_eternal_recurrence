package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsRosterContract.*;

/** Literal source-derived current admission. Deliberately does not import or call a transport normalizer. */
final class ArmyRosterDerivation {
    private ArmyRosterDerivation() { }
    private static final class Missing extends RuntimeException {
        private static final long serialVersionUID=1L;
        Missing(String reason){super(reason);}
    }
    private static <T> T need(T value,String reason){if(value==null)throw new Missing(reason);return value;}
    private static boolean selected(OperandResolution r){return r.selected_object_ready() && r.object_identity()!=null;}
    private static void operand(OperandResolution r,String name){if(!selected(r))throw new Missing(name+"_selected_operand_unavailable");}
    static long fnv(long id){long hash=0x811C9DC5L;for(int shift=0;shift<=24;shift+=8)hash=((hash^((id>>>shift)&255))*0x01000193L)&0xFFFFFFFFL;return hash;}
    static boolean referencesReady(RawReferences r){
        Integer count=r.count_raw_i32();List<RawReferenceOccurrence> rows=r.occurrences();
        if(count==null || count<0 || rows.size()!=count)return false;
        for(int i=0;i<rows.size();i++)if(rows.get(i).native_index()!=i || rows.get(i).raw_full_id_u32()==null)return false;
        return true;
    }
    private static boolean membership(RawReferences refs,long target,String name){
        int count=need(refs.count_raw_i32(),name+"_count_unavailable");
        if(count<0)throw new Missing(name+"_negative_count_native_precondition_unclosed");
        if(count==0)return false;
        Map<Integer,RawReferenceOccurrence> rows=new HashMap<>();
        for(RawReferenceOccurrence row:refs.occurrences())rows.put(row.native_index(),row);
        for(int i=0;i<count;i++){
            RawReferenceOccurrence row=rows.get(i);
            if(row==null || row.raw_full_id_u32()==null)throw new Missing(name+"_occurrence_unavailable");
            if(row.raw_full_id_u32()==target)return true;
        }
        return false;
    }
    private static DerivedRelation emptyRelation(){return new DerivedRelation(false,"not_demanded",null,null,null,null,List.of());}
    private static final class RelationBuilder{
        boolean ready;String reason="not_demanded";Long candidate;String selection,identity;Long war;List<RelationProbe> ledger=new ArrayList<>();
        DerivedRelation result(){return new DerivedRelation(ready,reason,candidate,selection,identity,war,ledger);}
    }
    private static final class RelationReader {
        final List<RelationProbe> probes;final RelationBuilder result;int cursor;
        RelationReader(List<RelationProbe> probes,RelationBuilder result){this.probes=probes;this.result=result;}
        long key(String kind,long slot){
            if(cursor>=probes.size())throw new Missing("relation_"+kind+"_key_unavailable");
            RelationProbe probe=probes.get(cursor);
            if(!probe.kind().equals(kind) || probe.slot_index_i64()!=slot)throw bad("relation","probes do not follow literal native lookup order");
            cursor++;result.ledger.add(probe);
            return need(probe.key_character_id_raw_u32(),"relation_"+kind+"_key_unavailable");
        }
    }
    private static DerivedRelation relation(RelationLookup raw){
        RelationBuilder r=new RelationBuilder();RelationReader reader=new RelationReader(raw.probes(),r);
        try{
            boolean present=need(raw.component_present(),"relation_component_pointer_unavailable");
            if(!present)r.selection="native_fallback";
            else{
                int count=need(raw.table_count_raw_i32(),"relation_count_unavailable");
                if(count<0)throw new Missing("relation_negative_count_native_precondition_unclosed");
                long end=count,base=0,candidate=0;int remaining=count;Long target=null;
                if(remaining>0){
                    if(!Boolean.TRUE.equals(raw.table_data_present()))throw new Missing("relation_table_data_native_read_precondition_unclosed");
                    target=need(raw.target_character_full_id_raw_u32(),"relation_target_full_id_unavailable");
                    while(true){
                        int half=remaining>>1;long pivot=reader.key("pivot",base+half);
                        if(pivot<target)base+=remaining-half;
                        candidate=base;remaining=half;if(half==0)break;
                    }
                }
                r.candidate=candidate;
                if(candidate==end)r.selection="native_fallback";
                else if(target<reader.key("candidate",candidate))r.selection="native_fallback";
                else if((int)candidate<0)r.selection="native_fallback";
                else r.selection="pair_map";
            }
            String identity;
            if(r.selection.equals("native_fallback")){
                if(!Boolean.TRUE.equals(raw.default_relationship_present()))throw new Missing("default_relationship_native_read_precondition_unclosed");
                identity=need(raw.default_relationship_identity(),"default_relationship_pointer_unavailable");
            }else{
                if(!Boolean.TRUE.equals(raw.selected_relationship_present()))throw new Missing("selected_relationship_native_read_precondition_unclosed");
                identity=need(raw.selected_relationship_identity(),"selected_relationship_pointer_unavailable");
            }
            if(!Objects.equals(raw.selected_relationship_identity(),identity))throw bad("relation","selected relationship lost actual native selection");
            r.identity=identity;
            r.war=need(raw.selected_relationship_war_id_raw_u32(),"selected_relationship_war_id_unavailable");
            r.ready=true;r.reason=null;
        }catch(Missing missing){r.reason=missing.getMessage();}
        return r.result();
    }
    private static final class GateBuilder {
        boolean ready;Boolean verdict;String reason="not_demanded";DerivedRelation relation=emptyRelation();List<GateSource> ledger=new ArrayList<>();
        <T> T demand(T value,GateField field){
            need(value,field.wire()+"_unavailable");
            SourceValue source;
            if(value instanceof Boolean flag)source=new FlagValue(flag);
            else if(value instanceof Number number)source=new NumberValue(number.longValue());
            else if(value instanceof String text)source=new TextValue(text);
            else throw bad(field.wire(),"unsupported typed demand");
            ledger.add(new GateSource(field,source));return value;
        }
        DerivedGate finish(boolean verdict){this.ready=true;this.verdict=verdict;this.reason=null;return result();}
        DerivedGate result(){return new DerivedGate(ready,verdict,reason,relation,ledger);}
    }
    private static DerivedGate emptyGate(){return new DerivedGate(false,null,"not_demanded",emptyRelation(),List.of());}
    private static DerivedGate gate(AdmissionGate raw,OperandResolution originalResolution){
        GateBuilder r=new GateBuilder();
        try{
            operand(originalResolution,"original_army");
            r.demand(raw.original_army_unit_id_raw_u32(),GateField.ORIGINAL_ARMY_UNIT_ID_RAW_U32);
            operand(raw.original_unit_resolution(),"original_unit");
            if(r.demand(raw.original_unit_kind_raw_u32(),GateField.ORIGINAL_UNIT_KIND_RAW_U32)!=0)return r.finish(false);
            if(!r.demand(raw.original_unit_province_present(),GateField.ORIGINAL_UNIT_PROVINCE_PRESENT))throw new Missing("original_province_pointer_native_read_precondition_unclosed");
            long original=r.demand(raw.original_province_identity_raw_u32(),GateField.ORIGINAL_PROVINCE_IDENTITY_RAW_U32);
            if(original!=r.demand(raw.selected_province_comparison_identity_raw_u32(),GateField.SELECTED_PROVINCE_COMPARISON_IDENTITY_RAW_U32))return r.finish(false);
            if(r.demand(raw.original_unit_counter_170_raw_i32(),GateField.ORIGINAL_UNIT_COUNTER_170_RAW_I32)>0)return r.finish(false);
            r.demand(raw.associated_army_id_raw_u32(),GateField.ASSOCIATED_ARMY_ID_RAW_U32);
            operand(raw.associated_army_resolution(),"associated_army");
            if(r.demand(raw.province_siege_id_raw_u32(),GateField.PROVINCE_SIEGE_ID_RAW_U32)==0xFFFFFFFFL)return r.finish(false);
            if(r.demand(raw.province_counter_850_raw_i32(),GateField.PROVINCE_COUNTER_850_RAW_I32)<=0)return r.finish(false);
            if(r.demand(raw.associated_army_flag_1d4_raw_u8(),GateField.ASSOCIATED_ARMY_FLAG_1D4_RAW_U8)!=0)return r.finish(false);
            if(r.demand(raw.associated_army_flag_1ec_raw_u8(),GateField.ASSOCIATED_ARMY_FLAG_1EC_RAW_U8)!=0)return r.finish(false);
            r.demand(raw.associated_army_unit_id_raw_u32(),GateField.ASSOCIATED_ARMY_UNIT_ID_RAW_U32);
            operand(raw.associated_unit_resolution(),"associated_unit");
            r.demand(raw.associated_unit_character_id_raw_u32(),GateField.ASSOCIATED_UNIT_CHARACTER_ID_RAW_U32);
            operand(raw.associated_character_resolution(),"associated_character");
            if(r.demand(raw.province_character_id_73c_raw_u32(),GateField.PROVINCE_CHARACTER_ID_73C_RAW_U32)==0xFFFFFFFFL){
                if(raw.native_2c099f0_character_identity()==null && raw.native_2c099f0_province_identity()==null &&
                        raw.native_2c099f0_third_argument_is_null()==null && !raw.native_2c099f0_returned() &&
                        raw.native_2c099f0_classification_raw_i32()==null)throw new Missing("province_73c_requires_2c099f0_inputs");
                String character=r.demand(raw.native_2c099f0_character_identity(),GateField.NATIVE_2C099F0_CHARACTER_IDENTITY);
                String province=r.demand(raw.native_2c099f0_province_identity(),GateField.NATIVE_2C099F0_PROVINCE_IDENTITY);
                if(!character.equals(raw.associated_character_resolution().object_identity()))throw new Missing("province_73c_2c099f0_character_operand_mismatch");
                if(!province.equals(raw.original_unit_province_identity()))throw new Missing("province_73c_2c099f0_province_operand_mismatch");
                if(!r.demand(raw.native_2c099f0_third_argument_is_null(),GateField.NATIVE_2C099F0_THIRD_ARGUMENT_IS_NULL))throw new Missing("province_73c_2c099f0_third_argument_not_null");
                if(!r.demand(raw.native_2c099f0_returned(),GateField.NATIVE_2C099F0_RETURNED))throw new Missing("province_73c_2c099f0_getter_unbound");
                return r.finish(r.demand(raw.native_2c099f0_classification_raw_i32(),GateField.NATIVE_2C099F0_CLASSIFICATION_RAW_I32)==0);
            }
            operand(raw.province_character_resolution(),"province_character");
            long associated=r.demand(raw.associated_character_full_id_raw_u32(),GateField.ASSOCIATED_CHARACTER_FULL_ID_RAW_U32);
            if(associated==r.demand(raw.province_character_full_id_raw_u32(),GateField.PROVINCE_CHARACTER_FULL_ID_RAW_U32))return r.finish(false);
            r.relation=relation(raw.relation_lookup());
            if(!r.relation.ready())throw new Missing(r.relation.unavailable_reason());
            if(r.relation.selected_relationship_war_id_raw_u32()==0xFFFFFFFFL)throw new Missing("2c09640_remaining_relation_predicates_unclosed");
            operand(raw.selected_war_resolution(),"selected_war");
            if(r.demand(raw.selected_war_ended_358_raw_u8(),GateField.SELECTED_WAR_ENDED_358_RAW_U8)!=0)throw new Missing("2c09640_remaining_relation_predicates_unclosed");
            return r.finish(true);
        }catch(Missing missing){r.reason=missing.getMessage();return r.result();}
    }
    private static DerivedPending emptyPending(){return new DerivedPending(false,"not_demanded",null,null,null,null,null,null,List.of());}
    private static DerivedPending pending(PendingSelection raw,long target){
        boolean ready=false;String reason="not_demanded";long hash=fnv(target);Long home=null,selected=null;Boolean end=null;Integer selectedControl=null;List<PendingProbe> ledger=new ArrayList<>();
        int cursor=0,distance=1;
        try{
            if(!Boolean.TRUE.equals(raw.entries_present()))throw new Missing("pending_entries_native_read_precondition_unclosed");
            int mask=need(raw.mask_raw_i32(),"pending_mask_unavailable");
            long slot=(int)hash & mask;home=slot;
            while(true){
                if(cursor>=raw.probes().size())throw new Missing("pending_probe_unavailable");
                PendingProbe probe=raw.probes().get(cursor++);
                if(probe.physical_slot_i64()!=slot || probe.distance_raw_u8()!=distance)throw bad("pending","probes do not follow native full-ID probe order");
                ledger.add(probe);
                int control=need(probe.control_raw_u8(),"pending_probe_control_unavailable");
                if(control<distance){
                    int tail=need(raw.tail_distance_raw_u8(),"pending_tail_unavailable");
                    slot=(int)((long)mask+tail+1);end=true;break;
                }
                long key=need(probe.key_raw_full_id_u32(),"pending_probe_key_unavailable");
                if(key==target){end=false;break;}
                slot++;distance=(distance+1)&255;
            }
            selected=slot;
            selectedControl=need(raw.selected_control_raw_u8(),"pending_selected_control_unavailable");
            ready=true;reason=null;
        }catch(Missing missing){reason=missing.getMessage();}
        return new DerivedPending(ready,reason,target,hash,home,selected,end,selectedControl,ledger);
    }
    private static final class OccurrenceBuilder{
        final int index;final Long raw;final boolean originalSelected;boolean ready;String reason;DerivedGate gate=emptyGate();Boolean removed;boolean armyReady;Boolean append;Long siege,army;DerivedPending pending=emptyPending();List<DerivedArRg> arrgs=new ArrayList<>();boolean arrgReady;List<Long> ids;List<OccurrenceSource> ledger=new ArrayList<>();
        OccurrenceBuilder(RosterAdmissionOccurrence raw){index=raw.native_index();this.raw=raw.raw_full_id_u32();originalSelected=selected(raw.original_army_resolution());}
        DerivedOccurrence result(){return new DerivedOccurrence(index,raw,ready,reason,originalSelected,gate,removed,armyReady,append,siege,army,pending,arrgs,arrgReady,ids,ledger);}
        DerivedOccurrence skip(String reason){ready=true;armyReady=true;append=false;arrgReady=true;ids=List.of();ledger.add(new SourceBoundSkip(reason));return result();}
    }
    private static DerivedOccurrence occurrence(RosterAdmissionOccurrence raw,RawReferences removal){
        OccurrenceBuilder r=new OccurrenceBuilder(raw);
        try{
            need(raw.raw_full_id_u32(),"original_army_raw_reference_unavailable");
            r.gate=gate(raw.gate(),raw.original_army_resolution());
            if(!r.gate.ready())throw new Missing(r.gate.unavailable_reason());
            if(!r.gate.verdict())return r.skip("24e8560_false");
            need(raw.caller_army_unit_id_raw_u32(),"caller_army_unit_id_unavailable");
            operand(raw.caller_unit_resolution(),"caller_unit");
            if(!Boolean.TRUE.equals(raw.caller_province_present()))throw new Missing("caller_selected_province_native_read_precondition_unclosed");
            need(raw.caller_province_siege_id_raw_u32(),"caller_province_siege_id_unavailable");
            operand(raw.siege_resolution(),"caller_siege");
            int flag=need(raw.siege_flag_44c_raw_u8(),"siege_flag_44c_unavailable");
            if(flag==0)return r.skip("siege_44c_zero");
            long army=need(raw.selected_army_full_id_raw_u32(),"selected_army_full_id_unavailable");
            boolean removed=membership(removal,army,"removal_queue");r.removed=removed;
            if(removed)return r.skip("removal_queue_match");
            long siege=need(raw.siege_resolution().selected_full_id_u32(),"selected_siege_full_id_unavailable");
            r.armyReady=true;r.append=true;r.siege=siege;r.army=army;r.ledger.add(new VerifiedConditionalArmyAppend(siege,army));
            r.pending=pending(raw.pending_selection(),army);
            if(!r.pending.ready())throw new Missing(r.pending.unavailable_reason());
            if(r.pending.selected_control_raw_u8()==255){r.ready=true;r.arrgReady=true;r.ids=List.of();return r.result();}
            RawReferences refs=raw.original_arrg_references();
            int count=need(refs.count_raw_i32(),"original_arrg_count_unavailable");
            if(count<0)throw new Missing("original_arrg_negative_count_native_precondition_unclosed");
            if(count==0){r.ready=true;r.arrgReady=true;r.ids=List.of();return r.result();}
            if(!Boolean.TRUE.equals(refs.data_present()))throw new Missing("original_arrg_data_unavailable");
            RawReferences suppression=raw.pending_selection().suppression_references();String firstReason=null;
            for(RawReferenceOccurrence observed:refs.occurrences()){
                boolean ready=false;Boolean contains=null,append=null;String reason=null;
                try{
                    long id=need(observed.raw_full_id_u32(),"original_arrg_occurrence_unavailable");
                    contains=membership(suppression,id,"pending_suppression");append=!contains;ready=true;
                }catch(Missing missing){reason=missing.getMessage();if(firstReason==null)firstReason=reason;}
                r.arrgs.add(new DerivedArRg(observed.native_index(),observed.raw_full_id_u32(),ready,contains,append,reason));
            }
            boolean complete=referencesReady(refs) && r.arrgs.stream().allMatch(DerivedArRg::ready);
            if(!complete)throw new Missing(firstReason==null?"original_arrg_references_incomplete":firstReason);
            r.ids=r.arrgs.stream().filter(row->Boolean.TRUE.equals(row.append())).map(DerivedArRg::raw_full_id_u32).toList();
            r.ready=true;r.arrgReady=true;return r.result();
        }catch(Missing missing){r.reason=missing.getMessage();return r.result();}
    }
    private static PlacementRequest request(DerivedOccurrence occurrence,RosterAdmissionOccurrence observed){
        RequestProvenance provenance=new RequestProvenance(occurrence.native_index(),occurrence.raw_full_id_u32(),observed.original_army_resolution(),observed.siege_resolution(),occurrence.gate().source_ledger(),occurrence.gate().relation_lookup(),occurrence.pending_selection(),occurrence.arrg_occurrences().stream().filter(row->Boolean.TRUE.equals(row.append())).map(DerivedArRg::native_index).toList());
        return new PlacementRequest(occurrence.army_append_siege_full_id_u32(),occurrence.army_append_full_id_u32(),occurrence.arrg_append_full_ids_u32(),provenance);
    }
    static Projection project(Root raw){
        if(raw==null)return new Projection(Status.UNAVAILABLE,false,"current_daily_assault_roster_admission_unavailable",false,false,false,false,false,null,null,null,List.of(),List.of(),null,List.of(),List.of(),List.of(),null,List.of(new MissingField("current_daily_assault_roster_admission_v1")));
        RawReferences original=raw.original_roster(),removal=raw.removal_queue();
        boolean rawReady=referencesReady(original);Integer count=original.count_raw_i32();
        List<DerivedOccurrence> rows=raw.occurrences().stream().map(row->occurrence(row,removal)).toList();
        boolean coverage=count!=null && count>=0 && rows.size()==count;
        for(int i=0;i<rows.size();i++)if(rows.get(i).native_index()!=i)coverage=false;
        boolean complete=rawReady && coverage && rows.stream().allMatch(DerivedOccurrence::ready);
        boolean prefixOpen=count!=null && count>=0;int prefixIndex=0;Integer firstPartial=null;
        List<MissingInput> missing=new ArrayList<>();List<VerifiedArmyAppend> facts=new ArrayList<>();List<PlacementRequest> prefix=new ArrayList<>(),independent=new ArrayList<>();
        for(int i=0;i<rows.size();i++){
            DerivedOccurrence row=rows.get(i);RosterAdmissionOccurrence observed=raw.occurrences().get(i);
            if(row.native_index()!=prefixIndex){prefixOpen=false;if(firstPartial==null)firstPartial=prefixIndex;}
            prefixIndex=row.native_index()+1;
            if(!row.ready()){
                missing.add(new OccurrenceMissing(row.native_index(),row.unavailable_reason()));
                if(firstPartial==null)firstPartial=row.native_index();prefixOpen=false;
            }
            if(row.army_append_ready() && Boolean.TRUE.equals(row.army_append()))facts.add(new VerifiedArmyAppend(row.native_index(),row.army_append_siege_full_id_u32(),row.army_append_full_id_u32(),row.arrg_append_ready()));
            if(row.ready() && Boolean.TRUE.equals(row.army_append())){
                PlacementRequest request=request(row,observed);independent.add(request);if(prefixOpen)prefix.add(request);
            }
        }
        if(!rawReady || !coverage)missing.add(new MissingField("complete_original_roster_references_and_occurrence_coverage"));
        return new Projection(complete?Status.AVAILABLE:Boolean.TRUE.equals(raw.manager_loaded())?Status.PARTIAL:Status.UNAVAILABLE,complete,complete?null:"current_conditional_admission_inputs_incomplete",
                rawReady,referencesReady(removal),rawReady && coverage && rows.stream().allMatch(DerivedOccurrence::original_army_selection_ready),
                rawReady && coverage && rows.stream().allMatch(DerivedOccurrence::army_append_ready),rawReady && coverage && rows.stream().allMatch(DerivedOccurrence::arrg_append_ready),
                raw,original,removal,rows,original.occurrences(),count,prefix,independent,facts,firstPartial,missing);
    }
}

