package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.time.Duration;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls.*;

/** Replays original Python producers and retained native serializer fixtures; no current Game qualification is claimed. */
final class ArmyOrdinaryOriginalProducerTest {
    @TempDir Path temporary;
    private static final Map<String,String> PINS = Map.ofEntries(
        Map.entry("src/xar_autoplayer/bridge/war_contract.py", "ae960cc6a928eb9d26f2f9c93f30463a978951c374021558d08860c8f9125b2a"),
        Map.entry("src/xar_autoplayer/bridge/declaration_contract.py", "b5ed2eb40f8f52298886d764259501559a551b4096ecaa839e39fa45a12e151c"),
        Map.entry("src/xar_autoplayer/bridge/public_unit_contract.py", "0de76f3bf10ae24d3202177bb527bcb3ec903432a38af64f55e08c95698cab4e"),
        Map.entry("src/xar_autoplayer/bridge/call_ally_to_war_private_action_v1.py", "295910d6d8d67bee3eb75db6b5bc77887cc13e45b63bb8b63ae5fc2287d6b394"),
        Map.entry("src/xar_autoplayer/bridge/regular_maa_create_private_action_v1.py", "6fc9ab51477cee3377f09a0390c35dc141e74572a90463d7c7043daa6d31d134"),
        Map.entry("src/xar_autoplayer/bridge/nonwar_private_build.py", "fe1a53ca0f01e60ae37231e3b1a566442454f3bb77afd33b616849b25f6d53e9"),
        Map.entry("src/xar_autoplayer/bridge/army_gathering_research_sampling_contract.py", "e0d210d1e47a59e0eb71d8f7534d04354e7994c1964cff409839dccd308ca5e3"),
        Map.entry("tests/unit/test_call_ally_to_war_private_action_v1.py", "e84148cc28245e3d0c3be0a08f7744ca6ef11ff0cc5050378cba8ab0d464c35a"),
        Map.entry("native_bridge/research/fixtures/ck3_12003_call_ally_to_war_family_quote.json", "531e2ac0d1125af3632d3366d9e1e382d84245961666b935160fe7b4b66daee7"),
        Map.entry("native_bridge/research/fixtures/ck3_12003_call_ally_to_war_submit.json", "afb0d8b3590e3cb96f1b1e79289fa27384979171c054fa319b111fe37855a6fa"));
    private static final String SCRIPT = """
import json,sys,os,importlib.util
from pathlib import Path
root=Path(sys.argv[1])/"ck3_autonomous_player"
sys.path.insert(0,str(root/"src"))
os.environ["XAR_CALL_ALLY_FIXTURE_DIR"]=str(root/"native_bridge/research/fixtures")
spec=importlib.util.spec_from_file_location("actual_ally_fixture",root/"tests/unit/test_call_ally_to_war_private_action_v1.py")
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
from xar_autoplayer.bridge import war_contract as w
from xar_autoplayer.bridge import declaration_contract as d
from xar_autoplayer.bridge import army_gathering_research_sampling_contract as g
from xar_autoplayer.bridge import regular_maa_create_private_action_v1 as m
from xar_autoplayer.bridge.driver import BridgeUnavailableError
driver=fixture.NativeFixtureDriver()
ally=driver.submit_call_ally_to_war_private_v1(**driver.arguments())
ally_packet=driver.requests[-1]
class MAA:
    def __init__(self):
        self.endpoint=self.state=self
        self.requests=[]
    def take_snapshot(self): return driver.take_snapshot()
    def send(self,packet): self.requests.append(packet)
    def wait_for_command_result(self,request_id,timeout): return None
maa=MAA();unknown=False
try:
    m.submit_regular_maa_create_private_v1(maa,expected_revision=driver.snapshot["revision"],type_index=0,action_id="source-producer-maa",timeout_seconds=.125)
except BridgeUnavailableError:
    unknown=True
steps={"raise":w.RAISE_TROOPS_STEP,"move":w.move_army_step(0,123),"disband":w.disband_army_step(0),
       "start":w.start_assault_step(7),"stop":w.stop_assault_step(7),"enforce":w.enforce_demands_step(1),
       "surrender":w.surrender_war_step(1),"white_peace":w.offer_white_peace_step(1),
       "declare":d.declare_war_step("8-9--1"),"enable":g.ENABLE_STEP,"disable":g.DISABLE_STEP}
print(json.dumps({"snapshot":driver.snapshot,"ally_public":driver.arguments(),"ally_packet":ally_packet,
      "ally_result":ally,"maa_packet":maa.requests[-1],"maa_unknown":unknown,"steps":steps},ensure_ascii=False))
""";
    @Test void actualPrivateSendProducersAndOriginalStepContractsMatchJavaWire() throws Exception {
        Path repository = required("xar.repository.root"); Path python = required("xar.python"); assertTrue(Files.isRegularFile(python));
        pin(repository); ObjectNode oracle;
        Path output = temporary.resolve("original-producer.stdout.json"), error = temporary.resolve("original-producer.stderr.txt");
        var environment = new java.util.TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);
        environment.putAll(System.getenv()); environment.put("PYTHONDONTWRITEBYTECODE", "1");
        for (String variable : List.of("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")) environment.put(variable, "1");
        var command = new WindowsJobProcess.CommandSpec(python, List.of("-B", "-I", "-c", SCRIPT, repository.toString()),
                Path.of("").toAbsolutePath(), environment, output.toAbsolutePath(), error.toAbsolutePath(), 256L << 20);
        try (var process = WindowsJobProcess.start(command)) {
            var actual = process.await(Duration.ofSeconds(60), Instant.now().plusSeconds(60), () -> {});
            assertTrue(Files.size(output) <= 1024 * 1024 && Files.size(error) <= 16384, "bounded original oracle output required: " + actual);
            String diagnostic = actual + " stderr=" + Files.readString(error);
            assertEquals(0, actual.exitCode(), diagnostic); assertEquals(0, actual.accounting().activeProcesses(), diagnostic);
            assertTrue(actual.passed(), () -> actual + " stderr=" + diagnostic);
            oracle = ArmyJson.parse(Files.readAllBytes(output));
        } finally { pin(repository); }
        ObjectNode snapshot = ArmyJson.object(oracle.get("snapshot")); Context context = context(snapshot);
        CallAlly ally = (CallAlly) ArmyCallCodec.decode(PublicMethod.SUBMIT_CALL_ALLY_TO_WAR_PRIVATE_V1, new org.xar.ck3.control.application.action.RawJson(ArmyJson.bytes(oracle.get("ally_public"))));
        List<Long> costs = new ArrayList<>(); oracle.get("ally_packet").get("expected_send_cost_raw").forEach(value -> costs.add(value.bigIntegerValue().longValueExact()));
        var actualAlly = ArmyOrdinaryActionPreparation.primitive(ally, context, costs);
        assertEquals(oracle.get("ally_packet").get("step").textValue(), actualAlly.step()); assertEquals(extras(ArmyJson.object(oracle.get("ally_packet"))), ArmyJson.parse(actualAlly.additionalFields().bytes()));
        assertFalse(oracle.get("ally_result").get("material_result").booleanValue()); assertTrue(oracle.get("ally_result").get("verification_pending").booleanValue());
        assertFalse(oracle.get("ally_result").has("ally_joined")); assertTrue(oracle.get("maa_unknown").booleanValue());
        var rev = new Revision(new Present<>(snapshot.get("revision").bigIntegerValue()));
        var maa = new CreateMaa(rev, 0, "source-producer-maa", new Present<>(new java.math.BigDecimal("0.125")));
        var actualMaa = ArmyOrdinaryActionPreparation.primitive(maa, context, List.of());
        assertEquals(extras(ArmyJson.object(oracle.get("maa_packet"))), ArmyJson.parse(actualMaa.additionalFields().bytes()));
        List<Call> calls = List.of(new ArmyCalls.Frame(PublicMethod.RAISE_TROOPS_DEFAULT, rev),new Move(rev,new PublicUnitId(0),new PositiveId(123)),
                new Unit(PublicMethod.DISBAND_ARMY,rev,new PublicUnitId(0)),new Siege(PublicMethod.START_ASSAULT,rev,new PositiveId(7)),new Siege(PublicMethod.STOP_ASSAULT,rev,new PositiveId(7)),
                new War(PublicMethod.ENFORCE_DEMANDS,rev,BigInteger.ONE),new War(PublicMethod.SURRENDER_WAR,rev,BigInteger.ONE),new War(PublicMethod.OFFER_WHITE_PEACE,rev,BigInteger.ONE),
                new Declaration(PublicMethod.DECLARE_WAR,rev,"8-9--1"),new Sampling(rev,true),new Sampling(rev,false));
        List<String> keys=List.of("raise","move","disband","start","stop","enforce","surrender","white_peace","declare","enable","disable");
        for(int i=0;i<calls.size();i++) assertEquals(oracle.get("steps").get(keys.get(i)).textValue(),ArmyOrdinaryActionPreparation.primitive(calls.get(i),context,List.of()).step());
    }

    @Test void originalTerminalSelectionSurvivesCanonicalV3WithoutChangingTheNativePrimitiveOrUnknownFence() throws Exception {
        var scope = ArmyOrdinaryActionBoundaryTest.context();
        for (String route : List.of("player_victory", "surrender", "white_peace")) {
            var outcome = ArmyOrdinaryActionArguments.TerminalOutcome.exact(route);
            String literal = switch (outcome) {
                case PLAYER_VICTORY -> "enforce-demands-"; case SURRENDER -> "surrender-war-"; case WHITE_PEACE -> "offer-white-peace-";
            } + "16777239";
            ObjectNode arguments = ArmyJson.empty().put("war_id", 16777239).put("requested_outcome", route);
            arguments.putNull("postcondition_plan");
            var selectedArguments = org.xar.ck3.control.application.driver.DriverJson.object(ArmyJson.bytes(arguments), 65536);
            var operation = new org.xar.ck3.control.application.action.OperationKey(literal);
            var selected = ArmyOrdinaryPlannerSelection.decode(operation, selectedArguments, scope.before().frame().revision());
            var call = ArmyOrdinaryPlannerCalls.decode(operation, selectedArguments, scope.before().frame().revision(), "original-plan-action");
            var defaults = new ArmyOrdinaryActionArguments(selected.kind(), ArmyCallCodec.encode(call), List.of());
            assertEquals(ArmyOrdinaryActionArguments.SCHEMA, org.xar.ck3.control.planning.opportunity.OpportunityJson.text(defaults.encode().get("schema"), "schema"));
            assertEquals(defaults, ArmyOrdinaryActionArguments.decode(defaults.raw()));
            var retained = defaults.withTerminalSelection(selected.terminalSelection());
            assertEquals(ArmyOrdinaryActionArguments.TERMINAL_SCHEMA, org.xar.ck3.control.planning.opportunity.OpportunityJson.text(retained.encode().get("schema"), "schema"));
            assertEquals(retained, ArmyOrdinaryActionArguments.decode(retained.raw()));
            assertEquals(selectedArguments, retained.terminalSelection().orElseThrow().encode());
            ArmyOrdinaryPlannerSelection.requirePrepared(operation, selectedArguments, scope.before().frame().revision(), retained);
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryPlannerSelection.requirePrepared(operation, selectedArguments, scope.before().frame().revision(), defaults));
            var primitive = ArmyOrdinaryActionPreparation.primitive(call, scope, List.of());
            var restoredCall = ArmyCallCodec.decode(call.method(), ArmyOrdinaryActionArguments.decode(retained.raw()).publicArguments());
            assertEquals(primitive, ArmyOrdinaryActionPreparation.primitive(restoredCall, scope, List.of()));
            assertFalse(ArmyJson.parse(primitive.additionalFields().bytes()).has("postcondition_plan"));
            var expected = new ProposalLifecycle.ExpectedPostcondition(1, scope.before(), scope.source(), "software-terminal-custody-only/v1",
                    List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("observed"), true)));
            var original = new org.xar.ck3.control.application.action.ActionCommand("original-plan-action", scope.before(), scope.source(), scope.sessionId(),
                    operation, retained.encode(), expected, ArmyOrdinaryActionPreparation.claims(call, scope), scope.deadline());
            var cold = org.xar.ck3.control.application.action.ActionCodec.decodeCommand(org.xar.ck3.control.application.action.ActionCodec.encodeCommand(original));
            assertEquals(original, cold);
            assertEquals(org.xar.ck3.control.application.action.ActionCodec.bodySha256(original), org.xar.ck3.control.application.action.ActionCodec.bodySha256(cold));
            var unknown = new org.xar.ck3.control.application.action.ActionReceipt(1, 1, cold,
                    org.xar.ck3.control.application.action.ActionCodec.bodySha256(cold),
                    new org.xar.ck3.control.application.action.ActionState.Unknown(java.util.Optional.empty(), java.util.Optional.empty(),
                            "software original native outcome remains UNKNOWN", List.of(scope.source().sourceRef())));
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionService.rejectReplay(List.of(unknown), restoredCall, scope));
            for (String field : List.of("war_id", "requested_outcome", "postcondition_plan")) {
                ObjectNode missing = arguments.deepCopy(); missing.remove(field);
                assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryPlannerSelection.decode(operation,
                        org.xar.ck3.control.application.driver.DriverJson.object(ArmyJson.bytes(missing), 65536), scope.before().frame().revision()));
            }
            ObjectNode wrong = arguments.deepCopy(); wrong.put("war_id", true);
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryPlannerSelection.decode(operation,
                    org.xar.ck3.control.application.driver.DriverJson.object(ArmyJson.bytes(wrong), 65536), scope.before().frame().revision()));
            var lost = retained.encode().with("schema", new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text(ArmyOrdinaryActionArguments.SCHEMA));
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionArguments.decode(lost));
        }
        var surrender = new War(PublicMethod.SURRENDER_WAR, ArmyOrdinaryActionBoundaryTest.REV, BigInteger.valueOf(23));
        var legacy = new ArmyOrdinaryActionArguments(ArmyOrdinaryActionArguments.Kind.SURRENDER_WAR, ArmyCallCodec.encode(surrender),
                List.of(scope.source().sourceRef()), ArmyOrdinaryActionArguments.ExecutionProfile.GENERIC_AUTOMATIC_SURRENDER,
                java.util.Optional.of(org.xar.ck3.control.application.planning.military.OrdinaryAutomaticSurrenderPolicy.Variant.values()[0]));
        assertEquals(ArmyOrdinaryActionArguments.PROFILE_SCHEMA, org.xar.ck3.control.planning.opportunity.OpportunityJson.text(legacy.encode().get("schema"), "schema"));
        assertEquals(legacy, ArmyOrdinaryActionArguments.decode(legacy.raw()));
        assertTrue(ArmyOrdinaryActionArguments.decode(legacy.raw()).terminalSelection().isEmpty());
    }
    private static ObjectNode extras(ObjectNode packet) { ObjectNode result = packet.deepCopy(); result.remove(List.of("type","protocol_version","request_id","step","expected_revision")); return result; }
    private static Context context(ObjectNode fixture) {
        var now=Instant.parse("2026-10-24T00:00:00Z");var ref=new ExactRef("D:/source-fixture-only/ally-source.json",1,"a".repeat(64));
        var source=new G2Source("xenoamess-full-tower-eb9d2c1186",now.toString(),"1.20.0.3",ref);
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(fixture.get("played_character").get("character_id").bigIntegerValue(),fixture.get("native_revision").bigIntegerValue(),fixture.get("date_raw").bigIntegerValue()),"source-fixture-only",fixture.get("revision").bigIntegerValue(),"synthetic-replay-scope");
        var before=new ProposalLifecycle.ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),frame,1);
        return new Context(before,source,"source-fixture-only",now.plusSeconds(30));
    }
    private static Path required(String key) { String value=System.getProperty(key);assertNotNull(value,"required original producer configuration missing: "+key);Path path=Path.of(value);assertTrue(path.isAbsolute(),"required absolute original producer path: "+key);return path; }
    private static void pin(Path repository) throws Exception { for(var entry:PINS.entrySet()) assertEquals(entry.getValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(repository.resolve("ck3_autonomous_player").resolve(entry.getKey())))),entry.getKey()); }
}
