package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.OrdinaryPolicy.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContext;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContextRead;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual pinned C++ collector outputs -> existing strict model -> real chooser -> original Python policy parity.
 * This exercises no fabricated writer or complete-pipeline authority.
 */
class RootHolyWarPlanningPoliciesTest {
    record Input(Obj snapshot,PlayerHolyOrderContextRead.Observation observation) { }
    @Test void actualWholeNativeOutputsReachSameChooserAndOriginalPythonWithLosslessSerde() throws Exception {
        int count=0;
        for(Input input:inputs()) {
            var previous=blocked();var actual=RootHolyWarPlanningPolicies.choose(input.snapshot(),previous,input.observation());
            assertEquals(python(input,previous),OpportunityJson.toNode(actual.detail()));
            assertEquals(actual.detail(),DriverJson.object(DriverJson.encode(actual.detail()),DriverJson.MAX_NATIVE_BYTES));
            if(actual.selected().isPresent())assertEquals("hire-holy-order-v1",((Text)actual.detail().get("selected_step")).value());
            count++;
        }
        assertTrue(count>=5,"mandatory five actual native fixture providers");
    }
    @Test void existingSelectedOrForegroundWorkAndNonblockedSiegeNeverAcquireReinforcement() throws Exception {
        Input input=inputs().getFirst();
        var selected=blocked();selected=new Draft(selected.policy(),selected.phase(),selected.reason(),selected.kind(),selected.command(),selected.purpose(),selected.domain(),selected.detail().with("selected_step",new Text("move-army-1-to-2")));
        assertTrue(RootHolyWarPlanningPolicies.choose(input.snapshot(),selected,input.observation()).need().isEmpty());
        var unrelated=new Draft("p","other","r",Kind.ORDINARY,Optional.empty(),Purpose.READ_ONLY,Optional.empty(),new Obj(java.util.Map.of()));
        assertTrue(RootHolyWarPlanningPolicies.choose(input.snapshot(),unrelated,input.observation()).selected().isEmpty());
        var event=input.snapshot().with("active_event",new Obj(java.util.Map.of("instance_id",new Text("retained"))));
        assertTrue(RootHolyWarPlanningPolicies.choose(event,blocked(),input.observation()).need().isEmpty());
    }
    @Test void exactMoneyTypesAndFrameIdentityRemainMandatoryAndAnnotationRetainsAction() throws Exception {
        for(Input input:inputs()) {
            var hugeScale=StrictJson.object().put("raw",1_000_000_000L).put("scale",BigInteger.ONE.shiftLeft(64).add(BigInteger.valueOf(100000)));
            var changed=input.snapshot().with("played_character_gold",DriverJson.fromNode(hugeScale));
            assertEquals(python(new Input(changed,input.observation()),blocked()),OpportunityJson.toNode(RootHolyWarPlanningPolicies.choose(changed,blocked(),input.observation()).detail()));
            var drift=input.snapshot().with("revision",new IntegerValue(BigInteger.valueOf(101)));
            assertThrows(IllegalArgumentException.class,()->RootHolyWarPlanningPolicies.choose(drift,blocked(),input.observation()));
            var previous=blocked();var annotation=new Obj(java.util.Map.of("read_only",new Bool(true),"automatic_declaration_enabled",new Bool(false)));
            var decision=(Annotate)RootHolyWarPlanningPolicies.annotate(previous,"ordinary_holy_war_candidate_observation",annotation);
            assertEquals(previous.command(),decision.retained().command());assertEquals(previous.phase(),decision.retained().phase());
            assertEquals(previous.kind(),decision.retained().kind());assertEquals(previous.purpose(),decision.retained().purpose());
            assertEquals(annotation,decision.retained().detail().get("ordinary_holy_war_candidate_observation"));
        }
    }
    private static Draft blocked() {
        var plan=StrictJson.object().put("policy","one-life-turn-v1").put("phase","native_war_siege_exit_blocked").put("reason","native measured deficit");plan.putNull("selected_step");
        plan.putObject("siege_state").put("status","insufficient_strength").put("player_army_besieging",true).put("province_id",2).put("garrison_size",100).put("besieging_strength",99);
        plan.putObject("pursuit").put("war_id",1);
        return new Draft("one-life-turn-v1","native_war_siege_exit_blocked","native measured deficit",Kind.ORDINARY,Optional.empty(),Purpose.READ_ONLY,Optional.empty(),object(plan));
    }
    private static List<Input> inputs() throws Exception {
        byte[] body=Files.readAllBytes(Path.of(required("xar.holyOrder.fixtureCorpus")));assertEquals(required("xar.holyOrder.fixtureCorpusSha256"),DriverJson.sha256(body));
        JsonNode corpus=StrictJson.parse(body,StrictJson.EXPLICIT_MAX_BYTES);assertEquals("xar.ck3.holy-order-native-fixture-corpus/v1",corpus.path("schema").textValue());
        assertFalse(corpus.path("machine_id").textValue().isBlank());var result=new ArrayList<Input>();
        for(JsonNode run:corpus.path("runs")) {
            ExactRef output=ExactRef.fromJson(run.get("output_ref"));byte[] raw=Files.readAllBytes(Path.of(output.path()));assertEquals(output.bytes(),raw.length);assertEquals(output.sha256(),DriverJson.sha256(raw));
            JsonNode values=StrictJson.parse(raw,StrictJson.EXPLICIT_MAX_BYTES);
            for(JsonNode packet:values.path("samples")) {
                JsonNode payload=packet.path("result");var context=PlayerHolyOrderContext.decode(payload.get("player_holy_order_context"));
                var snapshot=StrictJson.object().put("snapshot_id","fixture-holy-native-"+payload.path("snapshot_revision").asText()).put("revision",100)
                        .put("native_revision",payload.get("snapshot_revision").bigIntegerValue()).put("date_raw",context.dateRaw()).put("paused",true).put("map_ready",true);
                snapshot.putObject("played_character").put("character_id",context.actorCharacterId()).put("alive",true);snapshot.putNull("active_event");snapshot.putNull("pending_character_interaction");
                snapshot.putArray("active_wars").addObject().put("war_id",1);
                for(String stock:List.of("gold","prestige","piety"))snapshot.putObject("played_character_"+stock).put("raw",1_000_000_000_000L).put("scale",100000);
                snapshot.putObject("diagnostics").putObject("hello").put("expected_ck3_version",context.build().version()).put("expected_ck3_sha256",context.build().sha256());
                var metadata=new PlayerHolyOrderContextRead.Metadata(snapshot.get("snapshot_id").textValue(),BigInteger.valueOf(100),payload.get("snapshot_revision").bigIntegerValue(),context.dateRaw(),BigInteger.valueOf(context.actorCharacterId()),payload.get("backend_id").textValue(),context.available()?"observed":"unavailable");
                result.add(new Input(object(snapshot),new PlayerHolyOrderContextRead.Observation(context,metadata)));
            }
        }
        return List.copyOf(result);
    }
    private static JsonNode python(Input input,Draft previous) throws Exception {
        Path root=Path.of(required("xar.repository.root")).toRealPath();
        assertEquals("3ba4621da526a0cc4e10c5ca6bb33fe491e84805aee964ca08b54ff85a90673a",DriverJson.sha256(Files.readAllBytes(root.resolve("ck3_autonomous_player/src/xar_autoplayer/holy_order_siege_reinforcement_v1.py"))));
        var builder=new ProcessBuilder(required("xar.python"),"-B","-I","-c","import json,sys;sys.path.insert(0,sys.argv[1]+'/ck3_autonomous_player/src');from xar_autoplayer.holy_order_siege_reinforcement_v1 import choose_holy_order_siege_reinforcement_v1 as choose;n=json.load(sys.stdin);print(json.dumps(choose(snapshot=n['snapshot'],plan=n['plan'],holy_context=n['holy_context']),allow_nan=False))",root.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        Process process=builder.start();var body=StrictJson.object();body.set("snapshot",OpportunityJson.toNode(input.snapshot()));body.set("plan",OpportunityJson.toNode(previous.detail()));body.set("holy_context",PlayerHolyOrderContextRead.flattened(input.observation()));
        try(var stdin=process.getOutputStream()){stdin.write(StrictJson.canonical(body,StrictJson.EXPLICIT_MAX_BYTES));}
        boolean finished=process.waitFor(30,TimeUnit.SECONDS);if(!finished)process.destroyForcibly();assertTrue(finished,"original Python policy timeout");assertEquals(0,process.exitValue(),"actual original Python policy failed");
        return StrictJson.parse(process.getInputStream().readAllBytes(),StrictJson.EXPLICIT_MAX_BYTES);
    }
    private static Obj object(JsonNode value){return OpportunityJson.object(DriverJson.fromNode(value),"holy test typed object");}
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("mandatory actual fixture setting missing: "+key);return value;}
}
