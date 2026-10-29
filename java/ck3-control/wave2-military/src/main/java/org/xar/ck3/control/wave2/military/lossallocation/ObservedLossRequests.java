package org.xar.ck3.control.wave2.military.lossallocation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.losssequence.AssociatedChunkWriter;
import org.xar.ck3.control.wave2.military.losssequence.LossSequenceCodec;
import org.xar.ck3.control.wave2.military.losssequence.LossSequenceModel;

/** Actual-stage integer requests are separate from the derived four-pass replay. Requests never stand for post-write soldiers. */
public final class ObservedLossRequests {
    private ObservedLossRequests(){}
    public enum Phase { SUPPLY_PREFERRED,SUPPLY_RESIDUAL,SIEGE_RAID_PREFERRED,SIEGE_RAID_RESIDUAL }
    public enum Status { AVAILABLE,PARTIAL,UNAVAILABLE,NOT_APPLICABLE }
    public record Eligible(int armyRegimentId,int currentSoldiers){}
    public record StageInputs(int nativeEligibleTotal,List<Eligible> rows){public StageInputs{rows=List.copyOf(rows);}}
    public record Request(int armyRegimentId,int currentRead,int remainingBudgetBefore,int remainingEligibleBefore,int multiplySigned32,int requestedSoldiers){}
    public record Pass(Phase phase,int budget,int nativeEligibleTotal,int cappedBudget,int overflow,int remainingBudget,int remainingEligible,List<Request> requests){public Pass{requests=List.copyOf(requests);}}
    public record Input(LossSequenceModel.Input writer,Integer preferredTotal,Integer supplyPreferredTotal){}
    public record Result(Status status,boolean ready,int supply,int siege,int raid,int combined,List<Pass> passes,List<String> missing){
        public Result{passes=List.copyOf(passes);missing=List.copyOf(missing);}}
    public record InitialWriteback(Phase phase,Status status,boolean ready,List<LossSequenceModel.WriterResult> requests,List<WritebackGap> missing){
        public InitialWriteback{requests=List.copyOf(requests);missing=List.copyOf(missing);}}
    public sealed interface WritebackGap permits MissingPass,MissingWriter {}
    public record MissingPass(String input) implements WritebackGap {}
    public record MissingWriter(int armyRegimentId,List<String> inputs) implements WritebackGap{public MissingWriter{inputs=List.copyOf(inputs);}}
    public static Input decode(JsonNode row){
        var writer=LossSequenceCodec.decodeArmyProjection(row);JsonNode losses=row.get("loss_application_inputs_v1");
        return new Input(writer,losses==null||losses.isNull()?null:integer(losses.get("definition_le_zero_soldiers")),losses==null||losses.isNull()?null:integer(losses.get("definition_le_zero_supply_eligible_soldiers")));
    }
    public static Pass requests(int budget,StageInputs inputs,Phase phase){
        int total=inputs.nativeEligibleTotal(),remaining=Math.min(budget,total),capped=remaining,overflow=budget-capped;List<Request> requests=new ArrayList<>();
        for(var row:inputs.rows()){
            if(remaining<=0||total<=0)break;
            int product=row.currentSoldiers()*remaining,quantity=product/total;
            requests.add(new Request(row.armyRegimentId(),row.currentSoldiers(),remaining,total,product,quantity));
            remaining-=quantity;total-=row.currentSoldiers();
        }
        return new Pass(phase,budget,inputs.nativeEligibleTotal(),capped,overflow,remaining,total,requests);
    }
    public static Result sequence(int supply,int siege,int raid,StageInputs supplyPreferred,StageInputs supplyResidual,StageInputs siegePreferred,StageInputs siegeResidual){
        List<Pass> passes=new ArrayList<>();List<String> missing=new ArrayList<>();int combined=siege+raid;
        boolean complete=pair(supply,supplyPreferred,supplyResidual,Phase.SUPPLY_PREFERRED,Phase.SUPPLY_RESIDUAL,passes,missing);
        if(complete)pair(combined,siegePreferred,siegeResidual,Phase.SIEGE_RAID_PREFERRED,Phase.SIEGE_RAID_RESIDUAL,passes,missing);else missing.add("post_supply_current_soldiers");
        return new Result(missing.isEmpty()?Status.AVAILABLE:passes.isEmpty()?Status.UNAVAILABLE:Status.PARTIAL,missing.isEmpty(),supply,siege,raid,combined,passes,missing);
    }
    private static boolean pair(int budget,StageInputs preferred,StageInputs residual,Phase first,Phase second,List<Pass> passes,List<String> missing){
        int overflow=0;for(int i=0;i<2;i++){Phase phase=i==0?first:second;int selected=i==0?budget:overflow;StageInputs input=i==0?preferred:residual;
            if(selected>0&&input==null){missing.add(wire(phase)+"_stage_inputs");return false;}
            Pass pass=requests(selected,selected>0?input:new StageInputs(0,List.of()),phase);passes.add(pass);if(i==0)overflow=pass.overflow();}
        return true;
    }
    public static Result project(Input input){
        var nativeInput=input.writer();if(!nativeInput.available()||!nativeInput.lossInputsAvailable()||nativeInput.budgets()==null)return null;
        var budgets=nativeInput.budgets();List<LossSequenceModel.Regiment> rows=nativeInput.regiments();
        boolean tiers=rows!=null&&rows.stream().allMatch(r->Boolean.TRUE.equals(r.siegeTierObservable()));
        boolean eligible=rows!=null&&rows.stream().allMatch(r->r.nativeSupplyLossEligible()!=null);
        StageInputs supply=null,siege=null;
        if(budgets.currentSupplyLossBudget()>0&&tiers&&eligible){
            StrictJson.require(input.supplyPreferredTotal()!=null,"observed initial supply eligible total required");
            supply=new StageInputs(input.supplyPreferredTotal(),rows.stream().filter(r->r.siegeTier()!=null&&r.siegeTier()<=0&&Boolean.TRUE.equals(r.nativeSupplyLossEligible())).map(r->new Eligible(r.regimentId(),r.current())).toList());
        }
        if(budgets.currentSupplyLossBudget()==0&&tiers){
            StrictJson.require(input.preferredTotal()!=null,"observed initial siege eligible total required");
            siege=new StageInputs(input.preferredTotal(),rows.stream().filter(r->r.siegeTier()!=null&&r.siegeTier()<=0).map(r->new Eligible(r.regimentId(),r.current())).toList());
        }
        Result result=sequence(budgets.currentSupplyLossBudget(),budgets.siegeLossBudget(),budgets.raidLossBudget(),supply,null,siege,null);List<String> missing=new ArrayList<>(result.missing());
        if(result.supply()>0&&!eligible)missing.add("per_regiment_native_2a956d0");
        if(result.supply()>0&&result.combined()>0&&!missing.contains("post_supply_current_soldiers"))missing.add("post_supply_current_soldiers");
        // Preserve original status/readiness from actual-stage availability; extra diagnostic does not manufacture a stage.
        return new Result(result.status(),result.ready(),result.supply(),result.siege(),result.raid(),result.combined(),result.passes(),missing);
    }
    public static InitialWriteback initial(Input input,Result allocation){
        boolean positive=allocation.supply()>0;Phase phase=positive?Phase.SUPPLY_PREFERRED:Phase.SIEGE_RAID_PREFERRED;int budget=positive?allocation.supply():allocation.combined();
        if(budget<=0)return new InitialWriteback(phase,Status.NOT_APPLICABLE,false,List.of(),List.of());
        Pass preferred=allocation.passes().stream().filter(p->p.phase()==phase).findFirst().orElse(null);
        if(preferred==null)return new InitialWriteback(phase,Status.UNAVAILABLE,false,List.of(),List.of(new MissingPass("initial_preferred_writer_requests")));
        List<LossSequenceModel.WriterResult> outputs=new ArrayList<>();List<WritebackGap> missing=new ArrayList<>();
        for(var request:preferred.requests()){
            var writer=AssociatedChunkWriter.project(input.writer(),new LossSequenceModel.WriterRequest(request.armyRegimentId(),request.requestedSoldiers()*100000L,100000));outputs.add(writer);
            if(!writer.ready())missing.add(new MissingWriter(writer.regimentId(),writer.missingInputs()));
        }
        boolean complete=missing.isEmpty();return new InitialWriteback(phase,complete?Status.AVAILABLE:outputs.stream().anyMatch(LossSequenceModel.WriterResult::ready)?Status.PARTIAL:Status.UNAVAILABLE,complete,outputs,missing);
    }
    public static ObjectNode encode(Result v){
        ObjectNode n=StrictJson.object();if(v==null){n.put("status","unavailable");n.put("writer_requests_ready",false);n.put("applied_loss_ready",false);n.putNull("applied_soldier_loss");n.putArray("passes");n.putArray("missing_inputs").add("available_loss_application_inputs_v1");return n;}
        n.put("projection_kind","native_integer_writer_requests");n.put("source_contract_game_version","1.20.0.3");n.put("status",wire(v.status()));n.put("writer_requests_ready",v.ready());n.put("applied_loss_ready",false);n.putNull("applied_soldier_loss");
        n.put("supply_budget_soldiers",v.supply());n.put("siege_budget_soldiers",v.siege());n.put("raid_budget_soldiers",v.raid());n.put("combined_siege_raid_budget_soldiers",v.combined());ArrayNode passes=n.putArray("passes");
        for(var p:v.passes()){
            ObjectNode r=passes.addObject();r.put("projection_kind","native_integer_writer_requests");r.put("phase",wire(p.phase()));r.put("request_budget_soldiers",p.budget());r.put("native_eligible_total_soldiers",p.nativeEligibleTotal());r.put("capped_request_budget_soldiers",p.cappedBudget());r.put("caller_overflow_residual_soldiers",p.overflow());r.put("remaining_request_budget_soldiers",p.remainingBudget());r.put("remaining_eligible_soldiers",p.remainingEligible());
            ArrayNode requests=r.putArray("requests");for(var q:p.requests()){ObjectNode x=requests.addObject();x.put("army_regiment_id",q.armyRegimentId());x.put("current_soldiers_read",q.currentRead());x.put("remaining_budget_before",q.remainingBudgetBefore());x.put("remaining_eligible_before",q.remainingEligibleBefore());x.put("multiply_signed32",q.multiplySigned32());x.put("requested_soldiers",q.requestedSoldiers());x.put("writer_quantity_raw",q.requestedSoldiers()*100000L);x.put("writer_quantity_scale",100000);}
        }
        ArrayNode missing=n.putArray("missing_inputs");v.missing().forEach(missing::add);n.put("application_boundary","Actual post-write stage current and complete monthly applied loss are not observed");return n;
    }
    public static ObjectNode encodeInitial(InitialWriteback v){
        ObjectNode n=StrictJson.object();n.put("projection_kind","conditional_initial_preferred_chunk_writeback");n.put("input_basis","initial_same_query_DATA_and_preferred_writer_requests");n.put("phase",wire(v.phase()));n.put("status",wire(v.status()));n.put("same_input_chunk_writeback_ready",v.ready());n.put("actual_loss",false);n.putNull("actual_post_stage_current");
        ArrayNode requests=n.putArray("requests");v.requests().forEach(r->requests.add(LossSequenceCodec.writerNode(r)));ArrayNode missing=n.putArray("missing_inputs");
        for(var g:v.missing())switch(g){case MissingPass p->missing.add(p.input());case MissingWriter w->{ObjectNode x=missing.addObject();x.put("army_regiment_id",w.armyRegimentId());ArrayNode a=x.putArray("inputs");w.inputs().forEach(a::add);}}
        return n;
    }
    private static Integer integer(JsonNode value){return value==null||value.isNull()?null:(int)StrictJson.integer(value,Integer.MIN_VALUE,Integer.MAX_VALUE);}
    private static String wire(Enum<?> value){return value.name().toLowerCase(Locale.ROOT);}
}
