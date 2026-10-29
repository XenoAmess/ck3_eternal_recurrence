package org.xar.ck3.control.wave2.military.combatwire.phaseevent;

import static org.xar.ck3.control.wave2.military.combatwire.phaseevent.PhaseJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.wave2.military.forecast.CombatCore;

/** Original same-root daily research consumer. It cannot resolve combat or authorize a planner action. */
public final class PhaseFeedbackResearchKernel {
    public enum Role { COMMANDER("commander"),KNIGHT("knight");private final String wire;Role(String wire){this.wire=wire;}public String wire(){return wire;} }
    public record EffectTape(BigInteger dayIndex,String eventKey,List<Integer> draws){public EffectTape{Objects.requireNonNull(dayIndex);require(dayIndex.signum()>=0,"negative effect day");require(eventKey!=null&&!eventKey.isEmpty(),"empty effect key");draws=List.copyOf(draws);new PhaseDrawTape(draws);}}
    public static final class Input {
        private final ObjectNode context;private final Role role;private final BigInteger startDay;private final List<EffectTape> tapes;
        public Input(JsonNode context,Role role,BigInteger startDay,List<EffectTape> tapes){this.context=object(context,"phase feedback context").deepCopy();this.role=Objects.requireNonNull(role);this.startDay=Objects.requireNonNull(startDay);require(startDay.signum()>=0,"start day must be nonnegative");this.tapes=List.copyOf(tapes);Set<String> seen=new HashSet<>();for(EffectTape tape:this.tapes)require(seen.add(tape.dayIndex+":"+tape.eventKey),"duplicate day/event effect tape");}
        public ObjectNode context(){return context.deepCopy();}public Role role(){return role;}public BigInteger startDay(){return startDay;}public List<EffectTape> tapes(){return tapes;}
        List<Integer> tape(BigInteger day,String event){for(EffectTape tape:tapes)if(tape.dayIndex.equals(day)&&tape.eventKey.equals(event))return tape.draws;throw new IllegalArgumentException("missing effect draw tape for day "+day+" event "+event);}
    }
    public static final class Projection {
        private final ObjectNode json;private final CombatCore.DrawState selectionState;
        private Projection(ObjectNode json,CombatCore.DrawState selectionState){this.json=json.deepCopy();this.selectionState=selectionState;}
        public ObjectNode toJson(){return json.deepCopy();}public ObjectNode finalState(){return object(json.get("final_state"),"final state").deepCopy();}public CombatCore.DrawState selectionState(){return selectionState;}public boolean plannerUsable(){return false;}public boolean activeAttackAllowed(){return false;}
    }
    public static final CombatCore.Manifest MANIFEST=new CombatCore.Manifest("ck3-1.19.0.6-same-root-phase-feedback-research-v1",false,CombatCore.BOUNDED_CORE_MANIFEST.battleEndExact(),CombatCore.BOUNDED_CORE_MANIFEST.retreatAndForcedResultExact(),null,List.of("same_root_daily_phase_selection_and_ast_effect_state"));
    private final StockPhaseManifest manifest;
    public PhaseFeedbackResearchKernel(){manifest=StockPhaseManifest.load();new StockPhaseEventRuntime();}
    public Projection projectTrial(Input input,CombatCore.DrawState selectionState,int horizonDays){Objects.requireNonNull(input);Objects.requireNonNull(selectionState);require(horizonDays>0,"horizon days must be positive");PhaseTrialState state=new PhaseTrialState(input.context,null);require(state.roles.contains(input.role.wire),"root has no requested phase-event role");List<StockPhaseManifest.Row> rows=manifest.rows.stream().filter(r->r.type.equals(input.role.wire)).toList();ArrayNode records=arr();for(int offset=0;offset<horizonDays;offset++){BigInteger day=input.startDay.add(BigInteger.valueOf(offset));String before=state.snapshot().path("state_sha256").asText();ObjectNode record=obj().put("day_index",day).put("before_state_sha256",before);if(!CombatCore.phaseEventDue(BigInteger.valueOf(state.rootId),day,5)){record.put("due",false).putNull("selected_candidate_key").putNull("executable_event_key").putNull("selection_random31").putNull("weights_source_order").put("after_state_sha256",before);record.putArray("transition_log");records.add(record);continue;}
            List<ObjectNode> evaluated=new ArrayList<>();List<CombatCore.PhaseEventCandidate> candidates=new ArrayList<>();for(StockPhaseManifest.Row row:rows){ObjectNode e=PhaseAst.evaluateRow(row,state);evaluated.add(e);candidates.add(new CombatCore.PhaseEventCandidate(row.key,bool(e.get("trigger_valid"),"valid"),integer(e.get("int_weight"),"weight"),row.tags.contains("empty_effect_maps_to_null_event")));}CombatCore.PhaseEventSelection selection=CombatCore.selectPhaseEvent(candidates,selectionState);selectionState=selection.state();String event=selection.executableEventKey();ArrayNode logs=arr();if(event!=null){PhaseDrawTape tape=new PhaseDrawTape(input.tape(day,event));StockPhaseManifest.Row selected=null;for(StockPhaseManifest.Row row:rows)if(row.key.equals(event))selected=row;require(selected!=null,"selected row absent");int previous=state.log.size();PhaseAst.execute(selected.effect,state,tape,event+".effect_ast");require(tape.position==tape.draws.size(),"unused effect draws for day "+day+" event "+event);for(int i=previous;i<state.log.size();i++)logs.add(state.log.get(i).deepCopy());}record.put("due",true);if(selection.selectedCandidateKey()==null)record.putNull("selected_candidate_key");else record.put("selected_candidate_key",selection.selectedCandidateKey());if(event==null)record.putNull("executable_event_key");else record.put("executable_event_key",event);if(selection.random31()==null)record.putNull("selection_random31");else record.put("selection_random31",selection.random31());ArrayNode weights=record.putArray("weights_source_order");for(ObjectNode e:evaluated){ArrayNode pair=arr();pair.add(e.get("key").deepCopy());pair.add(e.get("selectable_int_weight").deepCopy());weights.add(pair);}record.put("after_state_sha256",state.snapshot().path("state_sha256").asText());record.set("transition_log",logs);records.add(record);}
        ObjectNode out=obj();out.set("days",records);out.set("final_state",state.snapshot());out.putObject("selection_state").put("counter",selectionState.counter()).put("salt",selectionState.salt());out.put("planner_usable",false).put("active_attack_allowed",false);return new Projection(out,selectionState);
    }
    public CombatCore.TrialOutcome simulateTrial(Input input,CombatCore.TrialRandomStreams streams,int horizonDays){Projection projection=projectTrial(input,Objects.requireNonNull(streams).phaseScheduleState(),horizonDays);return new CombatCore.TrialOutcome(CombatCore.TrialResult.NO_RESOLUTION,horizonDays,BigInteger.ZERO,BigInteger.ZERO,false,!bool(projection.finalState().path("root").get("alive"),"root alive"));}
}
