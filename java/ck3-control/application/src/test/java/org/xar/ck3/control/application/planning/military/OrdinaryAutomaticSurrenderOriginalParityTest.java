package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual original driver/query/execute producer -> shared policy and original JSON-domain tuple. No live Game claim. */
final class OrdinaryAutomaticSurrenderOriginalParityTest {
    @TempDir Path temporary;
    private static final String SCRIPT = """
import sys,json,copy,importlib.util
from pathlib import Path
root=Path(sys.argv[1])/"ck3_autonomous_player"
sys.path.insert(0,str(root/"src"))
spec=importlib.util.spec_from_file_location("original_native_fixture",root/"tests/unit/test_native_bridge_driver.py")
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
from xar_autoplayer.bridge import native_driver as n
cases=[];executions=[]
for cb,score,duration in [("individual_county_de_jure_cb",-9,180),("raiktor_claim_cb",-100,100),("raiktor_claim_cb",-1,730),("minor_religious_war",-100,329)]:
    endpoint=f.FakeEndpoint()
    driver=n.NativeHeadlessGameplayDriver(endpoint.pipe_name,endpoint=endpoint,command_timeout_seconds=.1)
    warid=16777290
    endpoint.publish(f._hello("game.state.snapshot","game.command.query-war-termination-options-N","game.command.surrender-war-N"))
    endpoint.publish(f._snapshot(40,played_character={"character_id":707,"alive":True},active_wars=[f._war(war_id=warid,score=score)]))
    def answer(packet):
        step=packet.get("step","")
        if step.startswith("query-war-termination-options-"):
            result={"step":step,"accepted":True,"status":"available","query_sequence":1,
                "war_termination_options":f._termination_options(warid,score=score,white_peace_available=False,
                    casus_belli_database_index=17 if cb=="individual_county_de_jure_cb" else 40,
                    casus_belli_key=cb,war_duration_days=duration)}
        else:
            assert step=="surrender-war-16777290"
            result={"step":step,"accepted":True,"status":"submitted"}
        endpoint.publish({"type":"command_result","protocol_version":1,"request_id":packet["request_id"],"ok":True,"result":result})
    endpoint.send_hook=answer
    driver.execute_step("query-war-termination-options-16777290")
    source=driver.take_snapshot()
    samples=[copy.deepcopy(source)]
    for key in ("context_constructed","native_validator_passed","available","auto_accept_observable","auto_accept"):
        bad=copy.deepcopy(source);bad["war_termination_options"][0]["options"]["surrender"][key]=False;samples.append(bad)
    for key in ("queried_snapshot_id","queried_revision","queried_native_revision","queried_connection_generation","episode_run_id"):
        bad=copy.deepcopy(source);bad["war_termination_options"][0][key]="wrong-original";samples.append(bad)
    bad=copy.deepcopy(source);bad["war_termination_options"][0]["options"]["surrender"]["recipient_response"]["would_accept_now"]=False;samples.append(bad)
    bad=copy.deepcopy(source);bad["active_wars"][0]["player_is_primary_war_leader"]=False;samples.append(bad)
    bad=copy.deepcopy(source);bad["paused"]=False;samples.append(bad)
    bad=copy.deepcopy(source);bad["war_termination_options"]=[];samples.append(bad)
    bad=copy.deepcopy(source)
    bad["active_wars"][0]["player_side"]="defender";bad["war_termination_options"][0]["player_side"]="defender"
    bad["war_termination_options"][0]["options"]["surrender"]["outcome"]="attacker_victory";samples.append(bad)
    bad=copy.deepcopy(source);bad["active_wars"][0]["player_relative_war_score"]=0;bad["war_termination_options"][0]["player_relative_war_score"]=0;samples.append(bad)
    for sample in samples:
        cases.append({"snapshot":sample,"original":n._emergency_surrender_readiness(sample,warid)})
    result=driver.execute_step("surrender-war-16777290")
    before_retry=len(endpoint.frames)
    try: driver.execute_step("surrender-war-16777290");raise AssertionError("original duplicate unexpectedly dispatched")
    except f.BridgeUnavailableError: pass
    assert len(endpoint.frames)==before_retry
    executions.append({"source":source,"result":result,"packet":endpoint.frames[-1],"writes":len([packet for packet in endpoint.frames if packet.get("type")=="execute_step"]),"history":driver.take_snapshot().get("native_command_history",[])})
    driver.close()
print(json.dumps({"cases":cases,"executions":executions},ensure_ascii=False))
""";
    @Test void actualOriginalQueryAndAutomaticExecuteSelectAllFourVariantsWithoutRetry() throws Exception {
        Path repository = required("xar.repository.root"), python = required("xar.python"); assertTrue(Files.isRegularFile(python));
        pin(repository, "src/xar_autoplayer/bridge/native_driver.py", "eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603");
        pin(repository, "tests/unit/test_native_bridge_driver.py", "4cf26ef6804ba46b7e8d1f3ef5aeaffafab136e7ee4f0b3a45462906dcdc1f99");
        Path output = temporary.resolve("original-auto-surrender.json"), errors = temporary.resolve("original-auto-surrender.stderr");
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-B", "-I", "-c", SCRIPT, repository.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.redirectOutput(output.toFile()); builder.redirectError(errors.toFile());
        Process process = builder.start(); process.getOutputStream().close();
        try {
            assertTrue(process.waitFor(60, TimeUnit.SECONDS), "required original automatic surrender producer timed out");
            assertEquals(0, process.exitValue(), Files.readString(errors));
            assertTrue(Files.size(output) <= 8L * 1024 * 1024 && Files.size(errors) <= 32768, "bounded actual oracle output required");
            Obj all = DriverJson.object(Files.readAllBytes(output), DriverJson.MAX_NATIVE_BYTES);
            int count = 0;
            for (Value raw : OpportunityJson.array(all.get("cases"), "actual original emergency cases")) {
                Obj sample = OpportunityJson.object(raw, "actual original case");
                Obj snapshot = OpportunityJson.object(sample.get("snapshot"), "original Driver snapshot");
                Arr actual = OrdinaryAutomaticSurrenderPolicy.originalTuple(OrdinaryAutomaticSurrenderPolicy.evaluate(snapshot, 16777290));
                assertEquals(sample.get("original"), actual, "original full tuple, including ordered reason/variant/evidence");
                assertEquals(actual, OpportunityJson.parse(OpportunityJson.encode(actual))); count++;
            }
            assertEquals(68, count);
            var variants = java.util.EnumSet.noneOf(OrdinaryAutomaticSurrenderPolicy.Variant.class);
            for (Value raw : OpportunityJson.array(all.get("executions"), "actual original execute results")) {
                Obj execution = OpportunityJson.object(raw, "original execution");
                Obj source = OpportunityJson.object(execution.get("source"), "original source frame");
                for (String wrongType : java.util.List.of("true", "-100.0", "\"-100\"")) {
                    var bad = (com.fasterxml.jackson.databind.node.ObjectNode) OpportunityJson.toNode(source);
                    ((com.fasterxml.jackson.databind.node.ObjectNode) bad.get("active_wars").get(0)).set("player_relative_war_score",
                            org.xar.ck3.control.contracts.StrictJson.parse(wrongType.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                    assertThrows(IllegalArgumentException.class, () -> {
                        Obj malformed = OpportunityJson.object(DriverJson.fromNode(bad), "invalid original numeric domain");
                        OrdinaryAutomaticSurrenderPolicy.evaluate(malformed, 16777290);
                    });
                }
                var ready = assertInstanceOf(OrdinaryAutomaticSurrenderPolicy.Ready.class, OrdinaryAutomaticSurrenderPolicy.evaluate(source, 16777290));
                Obj result = OpportunityJson.object(execution.get("result"), "original result");
                Obj termination = OpportunityJson.object(result.get("war_termination_result"), "original termination result");
                if (ready.variant() == OrdinaryAutomaticSurrenderPolicy.Variant.DE_JURE_NO_SAFE_ROUTE) {
                    assertFalse(termination.members().containsKey("surrender_variant"));
                    assertFalse(termination.members().containsKey("absolute_war_scores_observable"));
                } else assertEquals(new Text(ready.variant().wire()), termination.get("surrender_variant"));
                assertEquals(new Text("submitted_pending"), termination.get("status"));
                assertEquals(new Text("attacker_defeat"), termination.get("outcome"));
                assertFalse(termination.members().containsKey("explicit_player_request"));
                assertEquals(new Text("surrender-war-16777290"), OpportunityJson.object(execution.get("packet"), "actual primitive").get("step"));
                assertEquals(new IntegerValue(java.math.BigInteger.TWO), execution.get("writes"));
                var history = new Arr(OpportunityJson.array(execution.get("history"), "actual original command history"));
                assertEquals(termination, OrdinaryAutomaticSurrenderPolicy.previousSubmission(history, 16777290, source.get("episode_run_id")).orElseThrow());
                assertTrue(OrdinaryAutomaticSurrenderPolicy.previousSubmission(history, 16777291, source.get("episode_run_id")).isEmpty());
                variants.add(ready.variant());
            }
            assertEquals(java.util.EnumSet.allOf(OrdinaryAutomaticSurrenderPolicy.Variant.class), variants);
        } finally {
            if (process.isAlive()) process.destroyForcibly();
            pin(repository, "tests/unit/test_native_bridge_driver.py", "4cf26ef6804ba46b7e8d1f3ef5aeaffafab136e7ee4f0b3a45462906dcdc1f99");
            pin(repository, "src/xar_autoplayer/bridge/native_driver.py", "eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603");
        }
    }
    private static Path required(String name) {
        String value = System.getProperty(name); assertNotNull(value, "required actual original producer input missing: " + name);
        Path result = Path.of(value); assertTrue(result.isAbsolute()); return result;
    }
    private static void pin(Path repository, String relative, String sha) throws Exception {
        assertEquals(sha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(repository.resolve("ck3_autonomous_player").resolve(relative)))));
    }
}
