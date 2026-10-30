import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.nio.file.Path;
import org.xar.ck3.save.SaveContracts.Pin;

/** Pure frozen-V7 producer equivalence. Synthetic plans never grant actual hold or business credit. */
public final class CoreTailPreparationEquivalenceTest {
    private static final ObjectMapper JSON=new ObjectMapper();
    private CoreTailPreparationEquivalenceTest() { }
    private static void same(Object first,Object second) {
        if(!JSON.valueToTree(first).equals(JSON.valueToTree(second))) throw new AssertionError("frozen V7 plan changed");
    }
    private static ObjectNode report(CoreTailPreparation.Input input) {
        ObjectNode report=JSON.createObjectNode().put("phase","hold");
        ObjectNode frame=JSON.createObjectNode().put("paused",true).put("map_ready",true)
                .put("date_raw",input.currentFrame().dateRaw()).put("revision",7).put("native_revision",7);
        frame.putObject("played_character").put("alive",true).put("character_id",input.currentFrame().actorId());
        frame.putObject("diagnostics").put("bridge_pid",33).put("connection_generation",2);
        frame.putObject("managed_campaign_run_binding").put("run_id",input.runId());
        boolean event=input.stage()==CoreTailPreparation.Stage.EVENT_OBSERVE||input.stage()==CoreTailPreparation.Stage.EVENT_FIRST_OPTION;
        if(event)frame.putObject("active_event").put("instance_id",900);
        ObjectNode row=report.putArray("steps").addObject().put("id","observed").put("ok",true).put("finished_at","synthetic");
        row.set("after_snapshot",frame);
        ObjectNode plan=row.putObject("plan");ObjectNode result=row.putObject("result");
        String stage=input.stage().name();
        if(stage.contains("COLLECT_ORIGINAL")||stage.contains("VERIFY_ORIGINAL")){
            plan.put("tool","ck3_execute_player_rite_creation_action_v1");
            plan.putObject("args").put("operation","confirm_once").put("expected_source_rite_id",55);
            result.put("action_request_id",input.action().actionRequestId());
        }else if(event){
            plan.put("tool","ck3_query_current_event_window_context_v1");
            ObjectNode context=result.putObject("current_event_window_context").put("current_event_instance_id",900);
            context.putArray("options").addObject().put("shown",true).put("enabled",true).put("native_option_index",0);
        }else if(input.stage()==CoreTailPreparation.Stage.PARDON_INITIATE_ONCE){
            plan.put("tool","ck3_query_character_interaction_ordinary_v1");
            plan.putObject("args").put("interaction_key","pardon_interaction").put("recipient_id",77);
            result.putObject("character_interaction_ordinary_context").put("ready_to_initiate",true);
        }else {
            plan.put("tool","ck3_query_player_rite_creation_action_context_v1");
            ObjectNode leaf=result.putObject("rite_creation_action").put("preview_identity","a".repeat(64));
            leaf.putObject("full_can").put("can_create",true).put("can_edit",true);
            leaf.putObject("quote").put("has_enough_piety",true);
            leaf.putObject("draft").put("source_rite_id",55).put("actual_outcome_kind",stage.startsWith("CREATE_")?"create_rite":"edit_rite");
            leaf.putObject("modal").put("stage","confirmation").put("active",true).put("native_can_accept",true).put("same_draft_window_bound",true);
        }
        return report;
    }
    public static void main(String[] args)throws Exception {
        if(args.length!=1)throw new IllegalArgumentException("explicit actual base required");
        Path base=Path.of(args[0]),runtime=base.resolve("resume-product-a20/runtime-a20/retest-source98-a01");
        String machine="desktop-3fevhd2-1c74096080",head="c0a9e71115e7263fa318f96f484e385d17b6eb4d";
        Pin placeholder=new Pin(base.resolve("UNUSED-CODEC-ONLY").toString(),0,"0".repeat(64));
        var binding=new CoreTailPreparation.Binding(1,machine,head,base,runtime,
                base.resolve("resume-product-a20/operations-core-a41/source99-a01/operation-support"),placeholder,placeholder);
        Constructor<CoreTailPreparation> ctor=CoreTailPreparation.class.getDeclaredConstructor(CoreTailPreparation.Binding.class);
        ctor.setAccessible(true);CoreTailPreparation engine=ctor.newInstance(binding);
        Class<?> old=Class.forName("CoreTailPreparationV7"),oldInput=Class.forName("CoreTailPreparationV7$Input");
        Method oldPlan=old.getMethod("plan",oldInput,JsonNode.class);
        Method fixture=CoreTailPreparation.class.getDeclaredMethod("fixtureInput",CoreTailPreparation.Stage.class);fixture.setAccessible(true);
        int stages=0,early=0,negative=0;
        for(var stage:CoreTailPreparation.Stage.values()){
            var source=(CoreTailPreparation.Input)fixture.invoke(engine,stage);
            ObjectNode wire=JSON.valueToTree(source);wire.put("live",runtime.resolve("runs/"+source.runId()).toString());
            var input=JSON.treeToValue(wire,CoreTailPreparation.Input.class);ObjectNode nativeShape=report(input);
            same(engine.plan(input,nativeShape),oldPlan.invoke(null,JSON.treeToValue(wire,oldInput),nativeShape));stages++;
            ObjectNode unknown=nativeShape.deepCopy();((ObjectNode)unknown.path("steps").get(0)).remove("finished_at");
            try{engine.plan(input,unknown);throw new AssertionError("UNKNOWN replay admitted");}catch(IllegalArgumentException expected){negative++;}
            if(stage==CoreTailPreparation.Stage.BIRTH_PLUS24_SAVE||stage==CoreTailPreparation.Stage.PARDON_PLUS31_SAVE){
                ObjectNode late=wire.deepCopy();((ObjectNode)late.path("currentFrame")).put("dateRaw",input.currentFrame().dateRaw()+24);
                var lateInput=JSON.treeToValue(late,CoreTailPreparation.Input.class);
                try{engine.plan(lateInput,report(lateInput));throw new AssertionError("late date relabeled");}catch(IllegalArgumentException expected){negative++;}
            }
            if(stage==CoreTailPreparation.Stage.PIN_ORIGINAL_HEIR){
                for(var decision:CoreTailPreparation.EarlyDecision.values()){
                    var ei=new CoreTailPreparation.EarlyInput(input,decision,0);
                    Class<?> oldEarly=Class.forName("CoreTailPreparationV7$EarlyInput");
                    same(engine.earlyPlan(ei,nativeShape),old.getMethod("earlyPlan",oldEarly,JsonNode.class)
                            .invoke(null,JSON.treeToValue(JSON.valueToTree(ei),oldEarly),nativeShape));early++;
                }
            }
        }
        System.out.println("FROZEN_V7_EQUIVALENT stages="+stages+" early="+early+" unknown_and_exact_date_rejections="+negative+"; pure synthetic plan equality only; no actual admission or business credit");
    }
}
