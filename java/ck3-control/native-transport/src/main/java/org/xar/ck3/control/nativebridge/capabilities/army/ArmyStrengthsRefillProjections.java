package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorCodec;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel;
import org.xar.ck3.control.wave2.military.armyselector.OrderedRefillPhysicalCore;
import org.xar.ck3.control.wave2.military.armyselector.RaisedRegimentRefresh;
import org.xar.ck3.control.wave2.military.losssequence.LossSequenceCodec;
import org.xar.ck3.control.wave3.military.landcontext.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsRefill.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPipeline.Stage;

/** Full source-ordered refill composition. Every conditional result retains the exact held-context premise. */
public final class ArmyStrengthsRefillProjections {
    private ArmyStrengthsRefillProjections() { }
    public enum PreparationBranch { UNKNOWN,ORDINARY_GUARD_BYPASS,FIXED_CHUNK0_PERMISSION_FALSE,FIXED_CHUNK0_PERMISSION_TRUE }
    public record Prepared(PreparationPersistent input,Coverage status,boolean ready,Long fraction,PreparationBranch branch,List<String> missing){public Prepared{missing=List.copyOf(missing);}}
    public record PreparationProjection(int armyId,Integer nativeCarmyId,Preparation input,boolean orderedBesieging,boolean ready,Coverage status,List<Prepared> rows,List<String> coverageMissing){public PreparationProjection{rows=List.copyOf(rows);coverageMissing=List.copyOf(coverageMissing);}}
    public record Preparations(List<PreparationProjection> rows){public Preparations{rows=List.copyOf(rows);}}
    public record BesiegingPreparations(List<PreparationProjection> rows){public BesiegingPreparations{rows=List.copyOf(rows);}}
    public record PhysicalStage(ScopedOrdered source,String inputBasis,String contextBasis,OrderedRefillPhysicalCore.Result result) { }
    public sealed interface StrengthValue permits Refreshed,Observed {int storedIndex();int regimentId();boolean ready();Integer current();Integer maximum();}
    public record Refreshed(int storedIndex,RaisedRegimentRefresh.Result result) implements StrengthValue {public int regimentId(){return result.regimentId();}public boolean ready(){return result.ready();}public Integer current(){return result.current();}public Integer maximum(){return result.maximum();}}
    public record Observed(int storedIndex,int regimentId,int currentValue,int maximumValue) implements StrengthValue {public boolean ready(){return true;}public Integer current(){return currentValue;}public Integer maximum(){return maximumValue;}}
    public record RefreshPass(int managerStoredIndex,List<Refreshed> regiments){public RefreshPass{regiments=List.copyOf(regiments);}}
    public record PreparationJoin(int persistentRegimentId,Long observedFraction,Long conditionalFraction,boolean ready,boolean preparationPresent,PreparationBranch branch,List<String> missing){public PreparationJoin{missing=List.copyOf(missing);}}
    public record ScopedProjection(int armyId,Integer nativeCarmyId,ScopedOrdered source,PhysicalStage physical,boolean orderedReady,boolean currentMaximumReady,Integer current,Integer maximum,List<RefreshPass> refreshes,List<StrengthValue> strengths,List<String> missing,boolean preparationProjected,PreparationProjection preparation,List<PreparationJoin> joins) {
        public ScopedProjection{refreshes=List.copyOf(refreshes);strengths=List.copyOf(strengths);missing=List.copyOf(missing);joins=List.copyOf(joins);}
    }
    public record ScopedRefills(List<ScopedProjection> rows){public ScopedRefills{rows=List.copyOf(rows);}}
    public record PositionChunk(int persistentRegimentId,int physicalIndex) { }
    public record NextProjection(int armyId,Integer nativeCarmyId,NextPositionInputs position,ScopedProjection scoped,String state,List<String> missing,List<PositionChunk> replaced,List<PositionChunk> unknown){public NextProjection{missing=List.copyOf(missing);replaced=List.copyOf(replaced);unknown=List.copyOf(unknown);}}
    public record NextRefills(List<NextProjection> rows){public NextRefills{rows=List.copyOf(rows);}}
    public static void install(ArmyStrengthsPipeline pipeline,ExactRef source){
        pipeline.register(Stage.SAME_INPUT_CONDITIONAL_FIXED_CHUNK0_PREPARATION_V1,Preparations.class,List.of(),(input,earlier)->new Preparations(input.selected().stream().map(row->preparation(row,false)).toList()),value->encodeRows(value.rows(),ArmyStrengthsRefillProjections::encodePreparationProjection),value->publicStages(Stage.SAME_INPUT_CONDITIONAL_FIXED_CHUNK0_PREPARATION_V1,encodeRows(value.rows(),ArmyStrengthsRefillProjections::encodePreparationProjection)),source);
        pipeline.register(Stage.SAME_INPUT_CONDITIONAL_SCOPED_ORDERED_REFILL_CURRENT_V1,ScopedRefills.class,List.of(Stage.SAME_INPUT_CONDITIONAL_FIXED_CHUNK0_PREPARATION_V1),(input,earlier)->{
            List<PreparationProjection> preparations=earlier.required(Stage.SAME_INPUT_CONDITIONAL_FIXED_CHUNK0_PREPARATION_V1,Preparations.class).rows();List<ScopedProjection> result=new ArrayList<>();
            for(int index=0;index<input.selected().size();index++){var row=input.selected().get(index);PreparationProjection prep=input.query().refillEntryMode()==ArmyStrengths.EntryMode.FIXED_CHUNK0_PREPARE?preparations.get(index):null;result.add(scoped(row,source(row,ScopedOrdered.class,ArmyStrengthsFamilies.Key.SCOPED_ORDERED_REFILL_INPUTS_V1),prep));}return new ScopedRefills(result);
        },value->encodeRows(value.rows(),ArmyStrengthsRefillProjections::encodeScopedProjection),value->publicStages(Stage.SAME_INPUT_CONDITIONAL_SCOPED_ORDERED_REFILL_CURRENT_V1,encodeRows(value.rows(),ArmyStrengthsRefillProjections::encodeScopedProjection)),source);
        pipeline.register(Stage.NEXT_ROUTE_POSITION_SCOPED_ORDERED_REFILL_V1,NextRefills.class,List.of(),(input,earlier)->new NextRefills(input.selected().stream().map(ArmyStrengthsRefillProjections::next).toList()),value->encodeRows(value.rows(),ArmyStrengthsRefillProjections::encodeNext),value->publicStages(Stage.NEXT_ROUTE_POSITION_SCOPED_ORDERED_REFILL_V1,encodeRows(value.rows(),ArmyStrengthsRefillProjections::encodeNext)),source);
        pipeline.register(Stage.SAME_INPUT_CONDITIONAL_ORDERED_BESIEGING_FIXED_CHUNK0_PREPARATION_V1,BesiegingPreparations.class,List.of(),(input,earlier)->new BesiegingPreparations(input.selected().stream().map(row->preparation(row,true)).toList()),value->encodeRows(value.rows(),ArmyStrengthsRefillProjections::encodePreparationProjection),value->publicStages(Stage.SAME_INPUT_CONDITIONAL_ORDERED_BESIEGING_FIXED_CHUNK0_PREPARATION_V1,encodeRows(value.rows(),ArmyStrengthsRefillProjections::encodePreparationProjection)),source);
        ArmyStrengthsRefillComposition.install(pipeline,source);
    }
    static <T> T source(ArmyStrengths.Row row,Class<T> type,ArmyStrengthsFamilies.Key key){
        var family=row.families().stream().filter(value->value.key()==key).findFirst();if(family.isEmpty())return null;var value=family.orElseThrow();require(value.valueType().equals(type),"actual family DTO differs");return value.value() instanceof Present<?> present?type.cast(present.value()):null;
    }
    static Integer nativeId(ArmyStrengths.Row row){return row.core().nativeArmy() instanceof Present<FullId> value?value.value().value():null;}
    public static PreparationProjection preparation(ArmyStrengths.Row row,boolean orderedB){
        Preparation input=orderedB?java.util.Optional.ofNullable(source(row,OrderedBesiegingPreparation.class,ArmyStrengthsFamilies.Key.ORDERED_BESIEGING_FIXED_CHUNK0_PREPARATION_INPUTS_V1)).map(OrderedBesiegingPreparation::value).orElse(null):
                java.util.Optional.ofNullable(source(row,FixedPreparation.class,ArmyStrengthsFamilies.Key.FIXED_CHUNK0_PREPARATION_INPUTS_V1)).map(FixedPreparation::value).orElse(null);
        return preparation(row.core().army().value(),nativeId(row),input,orderedB);
    }
    public static PreparationProjection preparation(int army,Integer nativeArmy,Preparation input,boolean orderedB){
        List<Prepared> rows=input==null?List.of():input.persistentRegiments().stream().map(ArmyStrengthsRefillProjections::prepare).toList();boolean complete=input!=null&&input.complete(),ready=complete&&rows.stream().allMatch(Prepared::ready);
        return new PreparationProjection(army,nativeArmy,input,orderedB,ready,ready?Coverage.AVAILABLE:!rows.isEmpty()||complete?Coverage.PARTIAL:Coverage.UNAVAILABLE,rows,complete?List.of():List.of(input==null?(orderedB?"ordered_besieging_fixed_chunk0_preparation_inputs_v1":"fixed_chunk0_preparation_inputs_v1"):(orderedB?"target_persistent_ids_complete":"referenced_persistent_ids_complete")));
    }
    static Prepared prepare(PreparationPersistent row){
        Integer guard=row.containingGuardRaw();Long magic=row.containingDefinitionMagic();Boolean permission=row.nativeFixedChunk0CanReplenish();Long fresh=row.freshFractionRaw(),raw=null;PreparationBranch branch=PreparationBranch.UNKNOWN;List<String> missing=new ArrayList<>();Boolean needs;
        if(guard!=null&&guard!=0||Long.valueOf(0x4744624fL).equals(magic))needs=true;else if(Integer.valueOf(0).equals(guard)&&magic!=null)needs=false;else{needs=null;if(guard==null)missing.add("containing_guard_138_raw");if(magic==null)missing.add("containing_definition_magic_38");}
        if(Boolean.FALSE.equals(needs)){branch=PreparationBranch.ORDINARY_GUARD_BYPASS;if(fresh==null)missing.add("fresh_fraction_raw");else raw=fresh;}
        else if(Boolean.TRUE.equals(needs)){if(permission==null)missing.add("native_fixed_chunk0_can_replenish");else if(!permission){branch=PreparationBranch.FIXED_CHUNK0_PERMISSION_FALSE;raw=0L;}else{branch=PreparationBranch.FIXED_CHUNK0_PERMISSION_TRUE;if(fresh==null)missing.add("fresh_fraction_raw");else raw=fresh;}}
        return new Prepared(row,raw!=null?Coverage.AVAILABLE:guard!=null||magic!=null||permission!=null||fresh!=null?Coverage.PARTIAL:Coverage.UNAVAILABLE,raw!=null,raw,branch,missing);
    }
    static ScopedOrdered withFractions(ScopedOrdered input,PreparationProjection preparation,List<PreparationJoin> joins){
        Map<Integer,Prepared> byId=new LinkedHashMap<>();preparation.rows().forEach(p->byId.put(p.input().persistentRegimentId(),p));List<PhysicalPersistent> physical=new ArrayList<>();
        for(PhysicalPersistent p:input.persistentRegiments()){Prepared prepared=byId.get(p.persistentRegimentId());boolean ready=prepared!=null&&prepared.ready();Long fraction=ready?prepared.fraction():null;List<String> missing=prepared==null?List.of((preparation.orderedBesieging()?"ordered_besieging_fixed_chunk0_preparation_inputs_v1":"fixed_chunk0_preparation_inputs_v1")+":persistent_row"):prepared.missing();
            joins.add(new PreparationJoin(p.persistentRegimentId(),p.preparedFractionRaw(),fraction,ready,prepared!=null,prepared==null?PreparationBranch.UNKNOWN:prepared.branch(),missing));physical.add(new PhysicalPersistent(p.persistentRegimentId(),fraction,p.unavailableReason(),p.chunks()));}
        return new ScopedOrdered(input.status(),input.unavailableReason(),input.subjectArmyId(),input.subjectCarmyId(),input.nativePersistentOccurrenceCount(),input.nativeArmyRefreshOccurrenceCount(),input.persistentOccurrences(),input.armyRefreshOccurrenceIndices(),physical);
    }
    public static PhysicalStage physical(ScopedOrdered source,String basis){return new PhysicalStage(source,basis,CONTEXT,OrderedRefillPhysicalCore.project(source.physical()));}
    public static ScopedProjection scoped(ArmyStrengths.Row row,ScopedOrdered inputs,PreparationProjection preparation){
        String basis=preparation==null?OBSERVED_BASIS:PREPARED_BASIS;List<PreparationJoin> joins=new ArrayList<>();ScopedOrdered privateInputs=inputs!=null&&preparation!=null?withFractions(inputs,preparation,joins):inputs;
        PhysicalStage stage=privateInputs==null?null:physical(privateInputs,basis);return scopedFrom(row,inputs,stage,preparation,joins);
    }
    public static ScopedProjection scopedFrom(ArmyStrengths.Row row,ScopedOrdered inputs,PhysicalStage physical,PreparationProjection preparation,List<PreparationJoin> joins){
        List<String> missing=new ArrayList<>();List<RefreshPass> refreshes=new ArrayList<>();List<StrengthValue> strengths=new ArrayList<>();boolean coreReady=false,ready=false;Integer current=null,maximum=null;
        if(inputs==null)missing.add("scoped_ordered_refill_inputs_v1");
        else if(inputs.subjectArmyId()!=row.core().army().value()||!Integer.valueOf(inputs.subjectCarmyId()).equals(nativeId(row)))missing.add("same_capture_subject_identity");
        else if(inputs.nativePersistentOccurrenceCount()==null)missing.add("native_persistent_occurrence_roster");
        else {
            if(physical!=null)missing.addAll(physical.result().missingInputs());FullDataRecords data=source(row,FullDataRecords.class,ArmyStrengthsFamilies.Key.REGIMENT_REPLENISHMENT_RECORDS_V1);
            Integer count=row.core().regimentCount() instanceof Present<Integer> observedCount?observedCount.value():null;
            if(data==null||!Integer.valueOf(data.values().size()).equals(count))missing.add("complete_requested_army_DATA_roster");
            else {Set<Integer> known=new LinkedHashSet<>();inputs.persistentRegiments().forEach(p->known.add(p.persistentRegimentId()));if(data.values().stream().flatMap(s->s.records().stream()).anyMatch(r->!known.contains(r.persistentRegimentId())))missing.add("all_requested_DATA_persistent_inputs");if(data.values().stream().anyMatch(s->s.status()!=FullDataModel.Coverage.AVAILABLE))missing.add("complete_requested_army_DATA");}
            coreReady=missing.isEmpty();
            if(inputs.nativeArmyRefreshOccurrenceCount()==null)missing.add("native_army_refresh_occurrence_roster");
            else if(data!=null){
                List<RaisedRegimentRefresh.PhysicalChunk> chunks=physical==null?List.of():physical.result().finalChunks().stream().map(c->new RaisedRegimentRefresh.PhysicalChunk(c.persistentId(),c.chunkIndex(),c.chunk().current(),c.chunk().maximum())).toList();
                if(!inputs.armyRefreshOccurrenceIndices().isEmpty())for(int managerIndex:inputs.armyRefreshOccurrenceIndices()){
                    List<Refreshed> pass=new ArrayList<>();for(int index=0;index<data.values().size();index++){var snapshot=data.values().get(index);pass.add(new Refreshed(index,RaisedRegimentRefresh.project(LossSequenceCodec.decodeDataProjection(LandContextCodec.encodeData(snapshot)).snapshot(),chunks)));}refreshes.add(new RefreshPass(managerIndex,pass));strengths=new ArrayList<>(pass);
                }else if(row.regiments() instanceof Present<List<ArmyStrengths.Regiment>> observed){int index=0;for(var regiment:observed.value())strengths.add(new Observed(index++,regiment.armyRegimentId(),regiment.currentSoldiers(),regiment.maximumSoldiers()));}
                ready=Integer.valueOf(strengths.size()).equals(count)&&strengths.stream().allMatch(StrengthValue::ready);
                if(ready){int c=0,m=0;for(StrengthValue value:strengths){c+=value.current();m+=value.maximum();}current=c;maximum=m;}else missing.add("requested_raised_current_maximum_refresh_inputs");
            }
        }
        if(preparation!=null&&physical!=null)for(PreparationJoin join:joins)if(physical.result().failedPersistentIds().contains(join.persistentRegimentId()))for(String key:join.missing())missing.add("persistent:"+join.persistentRegimentId()+":preparation:"+key);
        return new ScopedProjection(row.core().army().value(),nativeId(row),inputs,physical,coreReady,ready,current,maximum,refreshes,strengths,new ArrayList<>(new LinkedHashSet<>(missing)),preparation!=null,preparation,joins);
    }
    public static NextProjection next(ArmyStrengths.Row row){
        NextPositionInputs position=source(row,NextPositionInputs.class,ArmyStrengthsFamilies.Key.NEXT_ROUTE_REPLENISHMENT_POSITION_INPUTS_V1);ScopedOrdered input=source(row,ScopedOrdered.class,ArmyStrengthsFamilies.Key.SCOPED_ORDERED_REFILL_INPUTS_V1);List<PositionChunk> replaced=new ArrayList<>(),unknown=new ArrayList<>();List<String> missing=new ArrayList<>();String state="unavailable";ScopedProjection projection=null;
        if(position==null)missing.add("next_route_replenishment_position_inputs_v1");else if(position.status()==PositionStatus.NOT_APPLICABLE){state="not_applicable";missing.add("no_stored_first_route_target");}
        else if(position.unitFullId()!=row.core().army().value()||position.routeReadStatus()!=RouteReadStatus.COMPLETE_NONEMPTY||position.firstTargetProvinceId()==null)missing.add("same_query_actual_complete_first_route_target");
        else if(input==null||input.subjectArmyId()!=row.core().army().value()||!Integer.valueOf(input.subjectCarmyId()).equals(nativeId(row)))missing.add("same_query_scoped_ordered_physical_inputs");
        else {
            List<PhysicalPersistent> persistents=new ArrayList<>();for(PhysicalPersistent p:input.persistentRegiments()){List<PhysicalChunk> chunks=new ArrayList<>();for(PhysicalChunk c:p.chunks()){
                Integer unit=c.associatedUnitResolvedFullId();if(unit!=null&&unit!=position.unitFullId()){chunks.add(c);continue;}PositionChunk key=new PositionChunk(p.persistentRegimentId(),c.operands().physicalIndex());if(unit==null)unknown.add(key);else replaced.add(key);
                var x=c.operands();var changed=new ArmySelectorModel.Chunk(x.physicalIndex(),x.current(),x.maximum(),x.ordinal(),x.armyRegimentId(),x.exclusionByte(),x.state(),x.origin788(),x.origin73c(),x.associatedMagic(),x.associatedRegimentId(),x.armyByte1d4(),x.armyByte1ec(),x.inCombat(),x.unit170(),unit==null?null:position.firstTargetProvinceMagicRaw(),unit==null?null:position.ownerResolvedFullId(),unit==null?null:position.holderResolvedFullId(),unit==null?null:position.nativeFirstTargetPositionEligible(),x.ownerGuard(),x.ownerMagic());chunks.add(new PhysicalChunk(changed,c.ownerPersistentRegimentId(),c.ownerResolvedFullId(),c.originProvinceId(),c.associatedArmyRawFullId(),c.associatedArmyResolvedFullId(),c.associatedUnitRawFullId(),unit,c.contextUnavailableReason(),c.permissionSwitch()));
            }persistents.add(new PhysicalPersistent(p.persistentRegimentId(),p.preparedFractionRaw(),p.unavailableReason(),chunks));}
            ScopedOrdered privateInputs=new ScopedOrdered(input.status(),input.unavailableReason(),input.subjectArmyId(),input.subjectCarmyId(),input.nativePersistentOccurrenceCount(),input.nativeArmyRefreshOccurrenceCount(),input.persistentOccurrences(),input.armyRefreshOccurrenceIndices(),persistents);
            PhysicalStage physical=physical(privateInputs,NEXT_BASIS);physical=new PhysicalStage(physical.source(),physical.inputBasis(),NEXT_CONTEXT,physical.result());projection=scopedFrom(row,input,physical,null,List.of());state=projection.orderedReady()&&projection.currentMaximumReady()?"available":"partial";
        }
        return new NextProjection(row.core().army().value(),nativeId(row),position,projection,state,missing,replaced,unknown);
    }
    static <T> RawJson encodeRows(List<T> values,Function<T,ObjectNode> encode){ArrayNode rows=empty().arrayNode();values.forEach(value->rows.add(encode.apply(value)));return raw(rows);}
    public static ObjectNode encodePreparationProjection(PreparationProjection value){
        String coverage=value.orderedBesieging()?"target_persistent_ids_complete":"referenced_persistent_ids_complete";ObjectNode out=empty().put("projection_kind",value.orderedBesieging()?"conditional_ordered_B_fixed_chunk0_preparation":"conditional_fixed_chunk0_preparation").put("source_contract_game_version","1.20.0.3").put("input_basis","current_frozen_context_preparation").put("army_id",value.armyId()).put("status",wire(value.status())).put("preparation_ready",value.ready()).put(coverage,value.input()!=null&&value.input().complete()).put("actual_preparation",false).put("cache_write",false).put("full_ordered_regular_refill",false);put(out,"native_carmy_id",value.nativeCarmyId());
        if(value.orderedBesieging()){out.put("scope_kind","actual_ordered_besieging_target_physical_union");put(out,"province_id",value.input()==null?null:value.input().provinceId());put(out,"source_scope_status",value.input()==null?null:wire(value.input().sourceScopeStatus()));}
        ArrayNode rows=out.putArray("persistent_regiments"),missing=out.putArray("missing_inputs");for(String gap:value.coverageMissing()){ObjectNode m=missing.addObject();m.putNull("persistent_regiment_id");strings(m,"inputs",List.of(gap));}
        for(Prepared row:value.rows()){PreparationPersistent input=row.input();ObjectNode item=rows.addObject().put("persistent_regiment_id",input.persistentRegimentId()).put("fixed_chunk_index",0).put("status",wire(row.status())).put("native_input_status",wire(input.status())).put("native_input_ready",input.ready()).put("preparation_ready",row.ready()).put("fraction_scale",100000).put("preparation_branch",wire(row.branch())).put("actual_preparation",false).put("cache_write",false).put("full_ordered_regular_refill",false);put(item,"conditional_prepared_fraction_raw",row.fraction());put(item,"containing_guard_138_raw",input.containingGuardRaw());put(item,"containing_definition_magic_38",input.containingDefinitionMagic());put(item,"native_fixed_chunk0_can_replenish",input.nativeFixedChunk0CanReplenish());put(item,"fresh_fraction_raw",input.freshFractionRaw());strings(item,"missing_inputs",row.missing());if(!row.ready()){ObjectNode gap=missing.addObject().put("persistent_regiment_id",input.persistentRegimentId());strings(gap,"inputs",row.missing());}}
        return out;
    }
    public static ObjectNode encodePhysical(PhysicalStage value){
        var result=value.result();ObjectNode out=empty().put("status",!result.rosterObserved()?"unavailable":result.ready()?"available":"partial").put("ordered_core_ready",result.ready()).put("input_basis",value.inputBasis()).put("context_basis",value.contextBasis());strings(out,"missing_inputs",result.missingInputs());ArrayNode failed=out.putArray("failed_persistent_ids");result.failedPersistentIds().stream().sorted().forEach(failed::add);ArrayNode receipts=out.putArray("occurrences");
        for(var r:result.receipts()){ObjectNode row=receipts.addObject().put("stored_index",r.occurrence().storedIndex()).put("persistent_regiment_id",r.occurrence().persistentId()).put("prepared_fraction_raw",r.preparedFraction()).put("native_core_admitted",r.admitted());ArrayNode q=row.putArray("q_buffer");r.qBuffer().forEach(q::add);ArrayNode decisions=row.putArray("chunk_decisions");for(var d:r.decisions())decisions.addObject().put("physical_index",d.physicalIndex()).put("q_ordinal_raw",d.ordinal()).put("predicate",d.predicate()).put("permission_basis",d.permissionBasis()).put("qualified",d.qualified()).put("calculated_q",d.calculatedQ());ArrayNode writes=row.putArray("writes");for(var w:r.writes())writes.addObject().put("physical_index",w.physicalIndex()).put("q_ordinal_raw",w.ordinal()).put("q",w.q()).put("before_current",w.beforeCurrent()).put("before_maximum",w.beforeMaximum()).put("after_current",w.afterCurrent()).put("after_maximum",w.afterMaximum()).put("pair_cleared",w.pairCleared());}
        ArrayNode physical=out.putArray("physical_chunks");for(var chunk:result.finalChunks()){
            PhysicalPersistent original=value.source().persistentRegiments().stream().filter(p->p.persistentRegimentId()==chunk.persistentId()).findFirst().orElseThrow();PhysicalChunk before=original.chunks().get(chunk.chunkIndex());PhysicalChunk changed=new PhysicalChunk(chunk.chunk(),before.ownerPersistentRegimentId(),before.ownerResolvedFullId(),before.originProvinceId(),before.associatedArmyRawFullId(),before.associatedArmyResolvedFullId(),before.associatedUnitRawFullId(),before.associatedUnitResolvedFullId(),before.contextUnavailableReason(),before.permissionSwitch());physical.add(encodeChunk(changed).put("persistent_regiment_id",chunk.persistentId()).put("chunk_index",chunk.chunkIndex()));}
        return out;
    }
    static ObjectNode encodeStrength(StrengthValue value){
        if(value instanceof Refreshed r)return ArmySelectorCodec.refreshNode(r.result()).deepCopy().put("stored_index",r.storedIndex());
        Observed observed=(Observed)value;return empty().put("army_regiment_id",observed.regimentId()).put("stored_index",observed.storedIndex()).put("current_soldiers",observed.currentValue()).put("maximum_soldiers",observed.maximumValue()).put("current_maximum_ready",true).put("input_basis","observed_no_manager_refresh_occurrence");
    }
    public static ObjectNode encodeScopedProjection(ScopedProjection value){
        ObjectNode out=empty().put("army_id",value.armyId()).put("projection_kind",value.preparationProjected()?"conditional_fixed_chunk0_prepare_scoped_ordered_core":"conditional_scoped_observed_prepared_ordered_core").put("input_basis",value.physical()==null?(value.preparationProjected()?PREPARED_BASIS:OBSERVED_BASIS):value.physical().inputBasis()).put("context_basis",CONTEXT).put("status",value.source()==null||value.missing().contains("same_capture_subject_identity")||value.missing().contains("native_persistent_occurrence_roster")?"unavailable":value.orderedReady()&&value.currentMaximumReady()?"available":"partial").put("ordered_core_ready",value.orderedReady()).put("conditional_raised_current_maximum_ready",value.currentMaximumReady()).put("actual_after",false).put("actual_post_stage_observed",false).put("preparation_replayed",false).put("full_manager_replayed",false).put("full_monthly_ready",false);put(out,"native_carmy_id",value.nativeCarmyId());put(out,"conditional_current_soldiers",value.current());put(out,"conditional_maximum_soldiers",value.maximum());strings(out,"missing_inputs",value.missing());out.putArray("occurrences");out.putArray("physical_chunks");if(value.physical()!=null&&value.source()!=null&&!value.missing().contains("same_capture_subject_identity")){ObjectNode physical=encodePhysical(value.physical());out.set("occurrences",physical.get("occurrences"));out.set("physical_chunks",physical.get("physical_chunks"));}
        ArrayNode refreshes=out.putArray("refresh_occurrences");for(RefreshPass pass:value.refreshes()){ObjectNode row=refreshes.addObject().put("manager_stored_index",pass.managerStoredIndex());ArrayNode regiments=row.putArray("regiments");pass.regiments().forEach(r->regiments.add(encodeStrength(r)));}ArrayNode strengths=out.putArray("conditional_regiment_strengths");value.strengths().forEach(s->strengths.add(encodeStrength(s)));
        if(value.preparationProjected()){out.put("ordered_refill_entry_mode","fixed_chunk0_prepare").put("preparation_context_basis","current_frozen_context_preparation").put("conditional_preparation_projected",true).put("preparation_inputs_ready",value.preparation().ready()).put("cache_write",false).put("full_ordered_regular_refill",false);out.set("preparation_join",encodeJoins(value.joins()));}return out;
    }
    static ArrayNode encodeJoins(List<PreparationJoin> joins){ArrayNode values=empty().arrayNode();for(var join:joins){ObjectNode row=values.addObject().put("persistent_regiment_id",join.persistentRegimentId()).put("fixed_chunk_index",0).put("preparation_ready",join.ready()).put("preparation_branch",join.preparationPresent()?wire(join.branch()):"unavailable");put(row,"observed_prepared_fraction_raw",join.observedFraction());put(row,"conditional_prepared_fraction_raw",join.conditionalFraction());strings(row,"missing_inputs",join.missing());}return values;}
    public static ObjectNode encodeNext(NextProjection value){
        ObjectNode out=value.scoped()==null?empty().put("army_id",value.armyId()).put("status",value.state()).put("ordered_core_ready",false).put("conditional_raised_current_maximum_ready",false).put("actual_after",false).put("actual_post_stage_observed",false).put("full_monthly_ready",false).put("preparation_replayed",false):encodeScopedProjection(value.scoped());put(out,"native_carmy_id",value.nativeCarmyId());out.put("projection_kind","conditional_next_route_position_scoped_ordered_refill").put("input_basis",NEXT_BASIS).put("context_basis",NEXT_CONTEXT).put("physical_core_invocations",value.scoped()==null?0:1);if(value.scoped()==null)strings(out,"missing_inputs",value.missing());put(out,"first_target_province_id",value.position()==null?null:value.position().firstTargetProvinceId());ArrayNode replaced=out.putArray("replaced_position_chunks"),unknown=out.putArray("unknown_associated_unit_chunks");for(var chunk:value.replaced())replaced.addObject().put("persistent_regiment_id",chunk.persistentRegimentId()).put("physical_index",chunk.physicalIndex());for(var chunk:value.unknown())unknown.addObject().put("persistent_regiment_id",chunk.persistentRegimentId()).put("physical_index",chunk.physicalIndex());return out;
    }
    static void strings(ObjectNode out,String key,List<String> values){ArrayNode array=out.putArray(key);values.forEach(array::add);}
    static RawJson publicStages(Stage stage,RawJson nativeJson){return ArmyStrengthsRefillComposition.publicStages(stage,nativeJson);}
    static final String CONTEXT="held_nonphysical_native_army_unit_position_political_context",OBSERVED_BASIS="same_capture_prepared148_ordered_occurrences",PREPARED_BASIS="same_capture_fixed_chunk0_conditional_preparation_ordered_occurrences",NEXT_BASIS="same_query_observed_prepared148_actual_first_route_position",NEXT_CONTEXT="actual_first_route_position_for_selected_unit_other_operands_held_current";
}
