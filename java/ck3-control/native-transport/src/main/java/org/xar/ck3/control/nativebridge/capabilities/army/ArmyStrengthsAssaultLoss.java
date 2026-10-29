package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel;
import org.xar.ck3.control.wave2.military.losssequence.AssociatedChunkWriter;
import org.xar.ck3.control.wave2.military.losssequence.LossSequenceCodec;
import org.xar.ck3.control.wave2.military.losssequence.LossSequenceModel;
import org.xar.ck3.control.wave2.military.landstock.LandStockPolicy;
import org.xar.ck3.control.wave3.military.landcontext.FullDataModel;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsAssaultCodec.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.empty;

/** Literal current-table request ordering with physical alias writes and target-only cached refresh. */
public final class ArmyStrengthsAssaultLoss {
    private ArmyStrengthsAssaultLoss() { }
    public sealed interface Missing permits InputMissing,GroupMissing,WriterMissing { }
    public record InputMissing(String input) implements Missing { }
    public record GroupMissing(int group,List<Missing> inputs) implements Missing {public GroupMissing{inputs=List.copyOf(inputs);}}
    public record WriterMissing(int nativeIndex,List<String> inputs) implements Missing {public WriterMissing{inputs=List.copyOf(inputs);}}
    public record PhysicalKey(int persistent,int chunk) { }
    public record Physical(PhysicalKey key,Integer current,Integer maximum,Integer state,boolean stateObserved) { }
    public record Current(String identity,int regiment,Integer initialCurrent,Integer initialMaximum,Integer current,Integer maximum) { }
    public record BDelta(int provinceIndex,int regimentIndex,int regiment,int delta) { }
    public record Arithmetic(boolean ready,Integer loss,String zeroBasis,Long product,Long divided,String divisionPath,List<String> missing) {public Arithmetic{missing=List.copyOf(missing);}}
    public record Budget(boolean ready,Integer expectedLoss,String basis,Integer b,boolean unchanged,List<BDelta> deltas,Arithmetic arithmetic,List<Missing> missing) {public Budget{deltas=List.copyOf(deltas);missing=List.copyOf(missing);}}
    public record Writer(boolean ready,LossSequenceModel.WriterResult projection,List<String> missing) {public Writer{missing=List.copyOf(missing);}}
    public record Request(int nativeIndex,Long rawFullId,Integer regiment,int before,int remaining,int denominator,int product,int quantity,Writer writer) { }
    public record Allocation(String phase,boolean ready,Integer denominator,Integer cap,Integer overflow,Integer remaining,Integer remainingDenominator,List<Request> requests,List<Missing> missing) {public Allocation{requests=List.copyOf(requests);missing=List.copyOf(missing);}}
    public record Count(int nativeIndex,Long rawFullId,boolean ready,Integer whole,Integer delta,boolean append) { }
    public record QueueRequest(int groupIndex,int armyIndex,Long rawFullId) { }
    public record GroupResult(int nativeIndex,long slot,Integer nativeLoss,boolean entryReached,boolean numericReady,Budget budget,Allocation preferred,Allocation residual,List<Count> counts,boolean queueReady,List<Missing> missing) {public GroupResult{counts=List.copyOf(counts);missing=List.copyOf(missing);}}
    public record Result(int army,ArmyStrengths.Status status,boolean sequentialReady,boolean orderReady,int completed,Integer observed,List<GroupResult> groups,List<QueueRequest> requests,List<Physical> physical,List<Current> currents,List<Missing> missing) {
        public Result{groups=List.copyOf(groups);requests=List.copyOf(requests);physical=List.copyOf(physical);currents=List.copyOf(currents);missing=List.copyOf(missing);}
        public boolean queueRequestsReady(){return sequentialReady;}
    }
    private static String key(Resolution r){return r.state().ready()?r.objectIdentity():null;}
    private static Integer selected(Resolution r){return r.state().ready()&&r.selectedFullId()!=null?r.selectedFullId().intValue():null;}
    private static boolean same(Resolution a,Resolution b){return key(a)!=null&&key(a).equals(key(b))&&Objects.equals(selected(a),selected(b));}
    private static List<Missing> missing(String s){return List.of(new InputMissing(s));}
    private static List<Missing> missingMany(List<String> list){return list.stream().<Missing>map(InputMissing::new).toList();}
    public static Arithmetic arithmetic(LossGroup group,Integer b){
        var c=group.besieging().assaultContext();String zero=null;
        if(b!=null&&b<=0)zero="nonpositive_conditional_B";
        else if(Boolean.FALSE.equals(c.hasActiveSiege()))zero="no_active_group_Siege";
        else if(c.breachLevelRaw()!=null&&c.casualtyPercentageCount()!=null&&((long)c.breachLevelRaw()-1<0||(long)c.breachLevelRaw()-1>=c.casualtyPercentageCount()))zero="breach_index_outside_loaded_table";
        if(zero!=null)return new Arithmetic(true,0,zero,null,null,null,List.of());
        List<String> missing=new ArrayList<>();if(!Objects.equals(group.provinceMagic(),0x50726f76L))missing.add("actual_group_Province_magic_85C");if(b==null)missing.add("conditional_group_B");if(!Boolean.TRUE.equals(c.hasActiveSiege()))missing.add("captured_actual_group_Siege");if(c.breachLevelRaw()==null||c.casualtyPercentageCount()==null)missing.add("actual_group_breach_and_loaded_percentage_count");if(c.casualtyPercentageRaw()==null)missing.add("actual_group_indexed_percentage_raw");
        if(!missing.isEmpty())return new Arithmetic(false,null,null,null,null,null,missing);
        long product=(long)b*c.casualtyPercentageRaw();var divided=LandStockPolicy.nativeFixedDivide(product,10000000L);long raw=divided.value().longValueExact();return new Arithmetic(true,(int)(raw/100000L),null,product,raw,divided.path().name().toLowerCase(java.util.Locale.ROOT),List.of());
    }
    private static Map<String,Integer> changes(Map<String,Current> cache){Map<String,Integer> out=new LinkedHashMap<>();cache.forEach((k,v)->{if(v.current()!=null&&v.initialCurrent()!=null&&!v.current().equals(v.initialCurrent()))out.put(k,v.current()-v.initialCurrent());});return out;}
    private static Budget budget(LossGroup group,Map<String,Integer> changes,Map<Integer,String> ids){
        boolean noChanges=changes.isEmpty();Integer nativeLoss=group.nativeExpectedLoss();var family=group.besieging();
        if(group.provinceMagic()!=null&&group.provinceMagic()!=0x50726f76L)return new Budget(true,0,"source_invalid_Province_magic",null,noChanges,List.of(),null,List.of());
        if(noChanges&&nativeLoss!=null)return new Budget(true,nativeLoss,"native_current_scalar_with_unchanged_B",family==null?null:family.nativeBesiegingStrength(),true,List.of(),null,List.of());
        if(family==null)return new Budget(false,null,null,null,noChanges,List.of(),null,missing("captured_group_Province_B_and_actual_Siege_context"));
        Integer count=family.nativeProvinceUnitCount();boolean complete=family.contributorsReady()&&count!=null&&(count<=0||count==family.occurrences().size());int delta=0;List<BDelta> deltas=new ArrayList<>();
        if(complete)for(var o:family.occurrences()){
            if(Boolean.FALSE.equals(o.eligible()))continue;if(!Boolean.TRUE.equals(o.eligible())){complete=false;break;}
            for(var r:o.regiments()){int difference=changes.getOrDefault(ids.get(r.armyRegimentId()),0);delta+=difference;deltas.add(new BDelta(o.storedIndex(),r.storedIndex(),r.armyRegimentId(),difference));}
        }
        boolean unchanged=complete&&delta==0;Integer b=complete&&family.nativeBesiegingStrength()!=null?family.nativeBesiegingStrength()+delta:null;Arithmetic a=arithmetic(group,b);
        if(a.ready())return new Budget(true,a.loss(),"captured_group_B_plus_actual_target_cached_deltas",b,unchanged,deltas,a,List.of());
        if(unchanged&&nativeLoss!=null)return new Budget(true,nativeLoss,"native_current_scalar_with_proven_unchanged_B",b,true,deltas,a,List.of());
        List<Missing> missing=new ArrayList<>(missingMany(a.missing()));if(!complete)missing.add(new InputMissing("complete_original_group_B_occurrences_to_test_changed_cached_targets"));return new Budget(false,null,null,b,unchanged,deltas,a,missing);
    }
    /** Shared typed adapter into the existing sole DATA writer/refresh kernel. */
    public static ArmySelectorModel.DataSnapshot refreshSnapshot(FullDataModel.Snapshot data,Map<PhysicalKey,Physical> physical,boolean overlayState){
        List<ArmySelectorModel.DataRecord> records=new ArrayList<>();for(var r:data.records()){
            Physical replacement=physical.get(new PhysicalKey(r.persistentRegimentId(),r.chunkIndex()));Integer current=replacement==null?r.currentSoldiers():replacement.current(),maximum=replacement==null?r.maximumSoldiers():replacement.maximum();Integer state=overlayState&&replacement!=null&&replacement.stateObserved()?replacement.state():r.stateRaw();
            records.add(new ArmySelectorModel.DataRecord(r.recordIndex(),r.persistentRegimentId(),r.chunkIndex(),state,current,maximum));
        }return new ArmySelectorModel.DataSnapshot(data.armyRegimentId(),ArmySelectorModel.Coverage.valueOf(data.status().name()),data.nativeLossWriterSkipped(),records);
    }
    private static final class Run {
        final Map<String,Current> cache=new LinkedHashMap<>();final Map<String,Target> targets=new LinkedHashMap<>();final Map<Integer,String> ids=new LinkedHashMap<>();final Map<PhysicalKey,Physical> physical=new LinkedHashMap<>();
        final Map<PhysicalKey,Physical> changed=new LinkedHashMap<>();
        Run(Table table,LossInputs input){
            List<FullDataModel.Snapshot> all=new ArrayList<>();for(Target t:input.targets()){
                String k=key(t.resolution());Integer id=selected(t.resolution());if(k==null||!Boolean.TRUE.equals(t.identityValid())||id==null)continue;ids.put(id,k);
                cache.putIfAbsent(k,new Current(k,id,t.current(),t.maximum(),t.current(),t.maximum()));if(t.data()!=null)all.add(t.data());if(!targets.containsKey(k)||targets.get(k).data()==null&&t.data()!=null)targets.put(k,t);
            }
            for(Group g:table.groups())for(ArRgOccurrence o:g.arrgs().occurrences()){
                String k=key(o.resolution());Integer id=selected(o.resolution());if(k==null||!Boolean.TRUE.equals(o.identityValid())||id==null)continue;ids.put(id,k);Current old=cache.get(k);
                if(old==null)cache.put(k,new Current(k,id,o.current(),null,o.current(),null));else if(old.current()==null&&o.current()!=null)cache.put(k,new Current(k,old.regiment(),o.current(),old.initialMaximum(),o.current(),old.maximum()));
            }
            for(LossGroup g:input.groups())if(g.besieging()!=null)for(var o:g.besieging().occurrences())for(var r:o.regiments())if(r.replenishmentRecords()!=null)all.add(r.replenishmentRecords());
            for(var data:all)for(var r:data.records())if(r.status()==FullDataModel.RecordStatus.AVAILABLE){PhysicalKey k=new PhysicalKey(r.persistentRegimentId(),r.chunkIndex());physical.putIfAbsent(k,new Physical(k,r.currentSoldiers(),r.maximumSoldiers(),r.stateRaw(),true));}
        }
        Writer write(ArRgOccurrence o,int quantity){
            String k=key(o.resolution());Target target=targets.get(k);if(target==null)return new Writer(false,null,List.of("captured_valid_writer_target_admission_and_DATA"));
            if(target.writerSkipped()==null)return new Writer(false,null,List.of("native_loss_writer_skipped"));FullDataModel.Snapshot full=target.data();Current c=cache.get(k);
            if(full==null&&!target.writerSkipped())return new Writer(false,null,List.of("complete_target_DATA"));
            ArmySelectorModel.DataSnapshot snapshot=full==null?new ArmySelectorModel.DataSnapshot(c.regiment(),ArmySelectorModel.Coverage.UNAVAILABLE,true,List.of()):refreshSnapshot(full,changed,false);
            List<LossSequenceModel.RecordMetadata> metadata=full==null?List.of():full.records().stream().map(r->new LossSequenceModel.RecordMetadata(r.status()==FullDataModel.RecordStatus.AVAILABLE,r.chunkArmyRegimentId())).toList();
            LossSequenceModel.Input input=new LossSequenceModel.Input(true,true,null,List.of(new LossSequenceModel.Regiment(c.regiment(),c.current(),c.maximum(),null,null,null)),List.of(new LossSequenceModel.DataRow(snapshot,metadata)));
            LossSequenceModel.WriterResult projected;try{projected=AssociatedChunkWriter.project(input,new LossSequenceModel.WriterRequest(c.regiment(),(long)quantity*100000L,100000));}catch(ArithmeticException e){return new Writer(false,null,List.of("native_signed_division_defined"));}
            if(!projected.ready())return new Writer(false,projected,projected.missingInputs());if(Boolean.TRUE.equals(projected.skipped()))return new Writer(true,projected,projected.missingInputs());
            if(projected.refresh()==null||!projected.refresh().ready())return new Writer(false,projected,projected.missingInputs());
            for(var p:projected.physicalChunksAfter()){PhysicalKey pk=new PhysicalKey(p.persistentId(),p.chunkIndex());Physical value=new Physical(pk,p.current(),p.maximum(),null,false);physical.put(pk,value);changed.put(pk,value);}
            cache.put(k,new Current(k,c.regiment(),c.initialCurrent(),c.initialMaximum(),projected.refresh().current(),projected.refresh().maximum()));return new Writer(true,projected,projected.missingInputs());
        }
        Allocation allocate(Group group,int budget,String phase){
            if(!group.arrgs().referencesReady())return new Allocation(phase,false,null,null,null,null,null,List.of(),missing("complete_original_group_ArRg_occurrences"));
            int total=0;List<ArRgOccurrence> selected=new ArrayList<>();for(ArRgOccurrence o:group.arrgs().occurrences()){
                if(Boolean.FALSE.equals(o.identityValid()))continue;if(!Boolean.TRUE.equals(o.identityValid()))return new Allocation(phase,false,null,null,null,null,null,List.of(),missing("native_ArRg_identity_valid"));
                if(phase.equals("preferred")){if(o.definitionType()==null)return new Allocation(phase,false,null,null,null,null,null,List.of(),missing("native_definition_type_2a0"));if(o.definitionType()>0)continue;}
                Current c=cache.get(key(o.resolution()));if(c==null||c.current()==null)return new Allocation(phase,false,null,null,null,null,null,List.of(),missing("current_cached_valid_group_ArRg"));selected.add(o);total+=c.current();
            }
            int cap=Math.min(budget,total),overflow=budget-cap,remaining=cap,denominator=total;List<Request> requests=new ArrayList<>();
            for(ArRgOccurrence o:selected){if(remaining<=0||denominator<=0)break;int before=cache.get(key(o.resolution())).current(),product=before*remaining,quantity=product/denominator;Writer writer=write(o,quantity);requests.add(new Request(o.nativeIndex(),o.rawFullId(),selected(o.resolution()),before,remaining,denominator,product,quantity,writer));
                if(!writer.ready())return new Allocation(phase,false,total,cap,overflow,remaining,denominator,requests,List.of(new WriterMissing(o.nativeIndex(),writer.missing())));remaining-=quantity;denominator-=before;
            }return new Allocation(phase,true,total,cap,overflow,remaining,denominator,requests,List.of());
        }
    }
    public static Result project(int army,Table table,LossInputs input){
        if(table==null)return new Result(army,ArmyStrengths.Status.UNAVAILABLE,false,false,0,null,List.of(),List.of(),List.of(),List.of(),missing("current_daily_assault_table_v1"));
        boolean order=table.physicalGroupOrderReady();int observed=table.groups().size();if(order&&table.empty())return new Result(army,ArmyStrengths.Status.AVAILABLE,true,true,0,observed,List.of(),List.of(),List.of(),List.of(),List.of());
        if(input==null)return new Result(army,ArmyStrengths.Status.UNAVAILABLE,false,order,0,observed,List.of(),List.of(),List.of(),List.of(),missing("current_daily_assault_loss_inputs_v1"));
        Run run=new Run(table,input);boolean alive=order;int completed=0;List<GroupResult> groups=new ArrayList<>();List<QueueRequest> queues=new ArrayList<>();List<Missing> missing=new ArrayList<>();if(!order)missing.add(new InputMissing("complete_current_physical_group_order"));
        for(int i=0;i<table.groups().size();i++){
            Group g=table.groups().get(i);LossGroup source=i<input.groups().size()?input.groups().get(i):null;boolean entry=alive,numeric=false,queue=false;Budget budget=null;Allocation preferred=null,residual=null;List<Count> counts=new ArrayList<>();List<Missing> gm=new ArrayList<>();
            if(source==null||source.nativeIndex()!=g.nativeIndex()||source.slot()!=g.slot())gm.add(new InputMissing("same_query_loss_group_alignment"));
            else if(alive){budget=budget(source,changes(run.cache),run.ids);if(!budget.ready())gm.addAll(budget.missing());else{
                boolean allocation=true;int whole=budget.expectedLoss();if(whole!=0){preferred=run.allocate(g,whole,"preferred");allocation=preferred.ready();if(allocation&&preferred.overflow()>0){residual=run.allocate(g,preferred.overflow(),"flags0_residual");allocation=residual.ready();}if(!allocation)gm.addAll((residual==null?preferred:residual).missing());}numeric=allocation;
                if(allocation){queue=g.armies().referencesReady()&&source.armies().size()==g.armies().occurrences().size();Map<String,Integer> changes=changes(run.cache);
                    for(int ordinal=0;ordinal<g.armies().occurrences().size();ordinal++){
                        ArmyOccurrence o=g.armies().occurrences().get(ordinal);ArmyCount c=ordinal<source.armies().size()?source.armies().get(ordinal):null;int delta=0;Integer count=null;boolean ready=c!=null&&c.nativeIndex()==o.nativeIndex()&&Objects.equals(c.rawFullId(),o.rawFullId())&&same(c.resolution(),o.resolution())&&c.wholeCurrent()!=null;
                        if(ready&&!changes.isEmpty()){ready=c.state().ready();for(RegimentCount r:c.regiments()){if(Boolean.FALSE.equals(r.identityValid()))continue;String k=key(r.resolution());if(!Boolean.TRUE.equals(r.identityValid())||k==null){ready=false;break;}delta+=changes.getOrDefault(k,0);}}
                        if(ready)count=c.wholeCurrent()+delta;counts.add(new Count(o.nativeIndex(),o.rawFullId(),ready,count,ready?delta:null,ready&&count<=0));if(!ready){queue=false;break;}if(count<=0)queues.add(new QueueRequest(i,ordinal,o.rawFullId()));
                    }if(!queue)gm.add(new InputMissing("complete_group_Army_flags0_count_and_changed_target_intersections"));
                }
            }}
            GroupResult out=new GroupResult(g.nativeIndex(),g.slot(),source==null?null:source.nativeExpectedLoss(),entry,numeric,budget,preferred,residual,counts,queue,gm);if(alive&&(!numeric||!queue)){alive=false;missing.add(new GroupMissing(i,gm));}else if(alive)completed++;groups.add(out);
        }
        boolean ready=alive&&completed==table.groups().size();return new Result(army,ready?ArmyStrengths.Status.AVAILABLE:groups.isEmpty()?ArmyStrengths.Status.UNAVAILABLE:ArmyStrengths.Status.PARTIAL,ready,order,completed,observed,groups,queues,new ArrayList<>(run.physical.values()),new ArrayList<>(run.cache.values()),missing);
    }
    static ArrayNode emitMissing(List<Missing> missing){ArrayNode array=empty().arrayNode();for(Missing m:missing){if(m instanceof InputMissing i)array.add(i.input());else if(m instanceof GroupMissing g){ObjectNode n=array.addObject().put("group_native_index",g.group());n.set("inputs",emitMissing(g.inputs()));}else if(m instanceof WriterMissing w){ObjectNode n=array.addObject().put("writer_native_index",w.nativeIndex());ArrayNode inputs=n.putArray("inputs");w.inputs().forEach(inputs::add);}}return array;}
    static ObjectNode emitArithmetic(Arithmetic a){if(a==null)return null;ObjectNode n=empty().put("ready",a.ready()).put("zero_basis",a.zeroBasis()).put("division_path",a.divisionPath());put(n,"conditional_expected_loss",a.loss());put(n,"wrapped_product_raw",a.product());put(n,"divided_raw",a.divided());ArrayNode missing=n.putArray("missing_inputs");a.missing().forEach(missing::add);return n;}
    static ObjectNode emitBudget(Budget b){if(b==null)return null;ObjectNode n=empty().put("ready",b.ready()).put("basis",b.basis()).put("B_unchanged_proven",b.unchanged());put(n,"expected_loss",b.expectedLoss());put(n,"conditional_besieging_strength",b.b());ArrayNode deltas=n.putArray("B_delta_occurrences");for(BDelta d:b.deltas())deltas.addObject().put("province_stored_index",d.provinceIndex()).put("regiment_stored_index",d.regimentIndex()).put("army_regiment_id",d.regiment()).put("cached_current_delta_i32",d.delta());n.set("assault_projection",emitArithmetic(b.arithmetic()));n.set("missing_inputs",emitMissing(b.missing()));return n;}
    static ObjectNode emitWriter(Writer w){if(w.projection()!=null)return LossSequenceCodec.writerNode(w.projection());ObjectNode n=empty();ArrayNode missing=n.putArray("missing_inputs");w.missing().forEach(missing::add);return n;}
    static ObjectNode emitAllocation(Allocation a){if(a==null)return null;ObjectNode n=empty().put("phase",a.phase()).put("ready",a.ready());put(n,"denominator_i32",a.denominator());put(n,"initial_cap_i32",a.cap());put(n,"original_overflow_i32",a.overflow());put(n,"remaining_budget_i32",a.remaining());put(n,"remaining_denominator_i32",a.remainingDenominator());ArrayNode requests=n.putArray("requests");for(Request r:a.requests()){ObjectNode q=requests.addObject().put("native_index",r.nativeIndex());put(q,"raw_full_id_u32",r.rawFullId());put(q,"army_regiment_id",r.regiment());q.put("current_before_call_i32",r.before()).put("remaining_before_i32",r.remaining()).put("denominator_before_i32",r.denominator()).put("wrapped_product_i32",r.product()).put("requested_loss_soldiers_i32",r.quantity()).put("writer_quantity_raw",(long)r.quantity()*100000L).put("writer_ready",r.writer().ready());q.set("writer_projection",emitWriter(r.writer()));}n.set("missing_inputs",emitMissing(a.missing()));return n;}
    static ObjectNode emitGroup(GroupResult g){ObjectNode n=empty().put("native_index",g.nativeIndex()).put("physical_slot_i64",g.slot()).put("native_current_expected_loss_ready",g.nativeLoss()!=null).put("sequential_entry_reached",g.entryReached()).put("numeric_ready",g.numericReady()).put("queue_requests_ready",g.queueReady());put(n,"native_current_expected_loss",g.nativeLoss());n.set("conditional_budget",emitBudget(g.budget()));n.set("preferred",emitAllocation(g.preferred()));n.set("residual",emitAllocation(g.residual()));ArrayNode counts=n.putArray("army_counts");for(Count c:g.counts()){ObjectNode row=counts.addObject().put("native_index",c.nativeIndex()).put("ready",c.ready()).put("queue_append_requested",c.append());put(row,"raw_full_id_u32",c.rawFullId());put(row,"conditional_whole_current_soldiers_i32",c.whole());put(row,"cached_current_delta_i32",c.delta());}n.set("missing_inputs",emitMissing(g.missing()));return n;}
    public static ObjectNode encode(Result r){ObjectNode n=empty().put("projection_kind","conditional_current_daily_assault_loss").put("source_contract_game_version","1.20.0.3").put("army_id",r.army()).put("input_basis","observed_current_physical_group_order; fixed_actual_group_Siege_context; interleaved_writer_and_target_only_cached_refresh").put("status",r.status().name().toLowerCase(java.util.Locale.ROOT)).put("sequential_numeric_ready",r.sequentialReady()).put("physical_group_order_ready",r.orderReady()).put("completed_group_count",r.completed()).put("queue_requests_ready",r.queueRequestsReady());put(n,"observed_group_count",r.observed());ArrayNode groups=n.putArray("groups");r.groups().forEach(g->groups.add(emitGroup(g)));ArrayNode requests=n.putArray("ordered_queue_append_requests");r.requests().forEach(q->requests.addObject().put("group_native_index",q.groupIndex()).put("army_native_index",q.armyIndex()).put("raw_full_id_u32",q.rawFullId()));ArrayNode physical=n.putArray("conditional_physical_chunks");for(Physical p:r.physical()){ObjectNode row=physical.addObject().put("persistent_regiment_id",p.key().persistent()).put("chunk_index",p.key().chunk());put(row,"current_soldiers",p.current());put(row,"maximum_soldiers",p.maximum());if(p.stateObserved())put(row,"state_raw",p.state());}ArrayNode currents=n.putArray("conditional_regiment_currents");for(Current c:r.currents()){ObjectNode row=currents.addObject().put("object_identity",c.identity()).put("army_regiment_id",c.regiment());put(row,"initial_current_soldiers",c.initialCurrent());put(row,"initial_maximum_soldiers",c.initialMaximum());put(row,"current_soldiers",c.current());put(row,"maximum_soldiers",c.maximum());}n.set("missing_inputs",emitMissing(r.missing()));for(String field:List.of("actual_loss","actual_effects","actual_daily_loss","full_daily_assault_ready","full_regular_refill_ready","full_monthly_ready","full_calendar_ready","release_effects_ready","table_clear_effects_ready"))n.put(field,false);for(String field:List.of("actual_post_stage","actual_post_physical_chunks","actual_post_regiment_currents"))n.putNull(field);n.put("native_writes_executed",0);return n;}
}
