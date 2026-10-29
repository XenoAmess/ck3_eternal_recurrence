package org.xar.ck3.control.application.capabilities;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;

final class NativeCapabilityProjectionTest {
    private static final String SOURCE_SHA="eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603";
    private static final String SNAPSHOT="""
      {"paused":true,"active_event":null,"pending_character_interaction":null,
       "active_wars":[{"war_id":9,"player_side":"defender","enemy_armies":[]}],
       "player_armies":[{"army_id":0,"controllable":true,"current_province_id":10,"move_target_province_id":null,
         "route_province_ids":[],"army_state":"regular","in_combat":false}],"declarable_wars":[]}
      """;
    private static Obj snapshot() { return DriverJson.object(SNAPSHOT.getBytes(StandardCharsets.UTF_8),65536); }
    @Test void occupationRouteRequiresTheActualNativeCapabilityAtThePrimitiveBoundary() {
        Set<String> movement=Set.of(NativeActionSteps.MOVE,NativeActionSteps.PREVIEW);
        Set<String> absent=NativeActionSteps.candidates(new NativeActionSteps.Input(movement,snapshot(),List.of(),Set.of(99)));
        assertFalse(absent.contains("move-army-0-to-99"));assertFalse(absent.contains("preview-move-army-0-to-99"));
        Set<String> present=new TreeSet<>(movement);present.add(NativeActionSteps.OCCUPATION);
        Set<String> admitted=NativeActionSteps.candidates(new NativeActionSteps.Input(present,snapshot(),List.of(),Set.of(99)));
        assertTrue(admitted.contains("move-army-0-to-99"));assertTrue(admitted.contains("preview-move-army-0-to-99"));
    }
    @Test void fullPublicFlagsRequireRealBindingInAdditionToHello() {
        String capability=CapabilityFlags.CAMPAIGN_ROOT_CONTEXT_V1_QUERY_SUPPORTED.capability();
        assertEquals(new Bool(false),CapabilityFlags.project(Set.of(capability),ignored -> false,true).get("campaign_root_context_v1_query_supported"));
        assertEquals(new Bool(true),CapabilityFlags.project(Set.of(capability),capability::equals,true).get("campaign_root_context_v1_query_supported"));
        assertEquals(new Bool(false),CapabilityFlags.project(Set.of(),ignored -> true,true).get("campaign_root_context_v1_query_supported"));
        assertEquals(new Bool(false),CapabilityFlags.project(Set.of(CapabilityFlags.WAR_TERMINATION_EXIT_TERMS_QUERY_SUPPORTED.capability()),ignored -> true,true).get("war_termination_exit_terms_query_supported"));
        assertEquals(CapabilityFlags.values().length,CapabilityFlags.project(Set.of(),ignored -> false,false).members().size());
    }
    @Test void noIndependentProofCannotBecomeLiveBattleQualification() {
        var config=new DynamicCapabilities.Configuration(java.util.Optional.empty(),java.util.Optional.empty(),3,3,false,false);
        Obj flags=DynamicCapabilities.battleReadiness(config,java.util.Optional.empty(),Set.of("battle-decision-epoch-advance","battle-terminal-cruise"));
        assertEquals(new Bool(false),flags.get("decision_sentinel_live_ready"));assertEquals(new Bool(false),flags.get("terminal_sentinel_live_ready"));
        Obj proof=new Obj(Map.of("decision_sentinel_live_ready",new Bool(true)));
        assertEquals(new Bool(false),DynamicCapabilities.battleReadiness(config,java.util.Optional.of(proof),Set.of()).get("decision_sentinel_live_ready"));
        assertEquals(new Bool(true),DynamicCapabilities.battleReadiness(config,java.util.Optional.of(proof),Set.of("battle-decision-epoch-advance")).get("decision_sentinel_live_ready"));
    }
    @Test void missingInputsEncodeIdenticallyOnBothPublicSurfacesAndRetainNoExecutableSteps() {
        Obj encoded=DynamicCapabilities.toJson(new DynamicCapabilities.Incomplete(List.of("actual_runtime_owner_missing")));
        assertEquals(new Text("unavailable"),encoded.get("status"));assertEquals(new Bool(false),encoded.get("snapshot"));
        assertEquals(new Bool(false),encoded.get("wait_for_change"));assertEquals(new Arr(List.of()),encoded.get("action_steps"));
        assertEquals(encoded,DriverJson.object(org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(encoded),65536));
    }
    @Test void integerIdentitiesRejectEqualBooleanAndFloatTypes() {
        for(String bad:List.of(SNAPSHOT.replace("\"army_id\":0","\"army_id\":false"),SNAPSHOT.replace("\"army_id\":0","\"army_id\":0.0")))
            assertThrows(IllegalArgumentException.class,() -> new NativeActionSteps.Input(Set.of(),DriverJson.object(bad.getBytes(StandardCharsets.UTF_8),65536),List.of(),Set.of()));
    }
    @Test void actualOriginalProducerMatchesTheMigratedPrimitiveConsumer() throws Exception {
        for(Set<String> caps:List.of(Set.of(NativeActionSteps.MOVE,NativeActionSteps.PREVIEW),
                Set.of(NativeActionSteps.MOVE,NativeActionSteps.PREVIEW,NativeActionSteps.OCCUPATION),
                Set.of("game.command.disband-army-N","game.command.split-army-half-N","game.command.query-war-termination-options-N"))) {
            Set<Integer> occupation=caps.contains(NativeActionSteps.OCCUPATION)?Set.of(99):Set.of();
            Set<String> actual=NativeActionSteps.candidates(new NativeActionSteps.Input(caps,snapshot(),List.of(),occupation));
            Obj request=new Obj(Map.of("capabilities",new Arr(caps.stream().sorted().map(Text::new).map(v -> (Value)v).toList()),
                    "snapshot",snapshot(),"occupation",new Arr(occupation.stream().map(n -> (Value)new IntegerValue(BigInteger.valueOf(n))).toList())));
            assertEquals(original(request),actual);
        }
    }
    private static Set<String> original(Obj request) throws Exception {
        Path repository=Path.of(required("xar.repository.root")).toAbsolutePath().normalize();
        Path producer=Path.of(required("xar.native.producer.source")).toAbsolutePath().normalize();
        assertEquals(SOURCE_SHA,required("xar.native.producer.sha256"));assertEquals(SOURCE_SHA,DriverJson.sha256(Files.readAllBytes(producer)));
        String script="""
            import json,pathlib,sys
            sys.dont_write_bytecode=True
            repository=pathlib.Path(sys.argv[1]);expected=pathlib.Path(sys.argv[2]).resolve()
            sys.path.insert(0,str(repository/'ck3_autonomous_player'/'src'))
            from xar_autoplayer.bridge import native_driver
            assert pathlib.Path(native_driver.__file__).resolve()==expected
            value=json.load(sys.stdin);snapshot=value['snapshot']
            result=native_driver._action_steps(value['capabilities'],active_event=snapshot['active_event'],
              pending_character_interaction=snapshot['pending_character_interaction'],active_wars=snapshot['active_wars'],
              player_armies=snapshot['player_armies'],declarable_wars=snapshot['declarable_wars'],
              arrange_marriage_choices=[],paused=snapshot['paused'],occupation_target_province_ids=set(value['occupation']))
            print(json.dumps({'value':result},separators=(',',':')))
            """;
        ProcessBuilder command=new ProcessBuilder(List.of(required("xar.native.producer.python"),"-I","-B","-c",script,repository.toString(),producer.toString()));
        command.environment().put("PYTHONDONTWRITEBYTECODE","1");Process child=command.start();
        try {
            try(var stdin=child.getOutputStream()) { stdin.write(org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(request)); }
            assertTrue(child.waitFor(30,TimeUnit.SECONDS),"actual original producer exceeded finite timeout");
            byte[] output=child.getInputStream().readAllBytes(),error=child.getErrorStream().readAllBytes();
            assertEquals(0,child.exitValue(),new String(error,StandardCharsets.UTF_8));assertTrue(output.length>0 && output.length<=1048576);
            Set<String> result=new TreeSet<>();for(Value row:array(DriverJson.object(output,1048576).get("value"),"value"))result.add(text(row,"step"));
            return Set.copyOf(result);
        } finally { if(child.isAlive())child.destroyForcibly(); }
    }
    private static String required(String property) {
        String value=System.getProperty(property);assertTrue(value!=null && !value.isBlank(),"original producer differential NOT RUN: missing "+property);return value;
    }
}
