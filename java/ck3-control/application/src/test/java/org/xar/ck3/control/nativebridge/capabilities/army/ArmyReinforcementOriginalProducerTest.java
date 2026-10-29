package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ReinforcementArrivalFirstCorpus;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Untouched native production-serializer FIRST wires plus original Python normalizer. No Game or actual join credit. */
final class ArmyReinforcementOriginalProducerTest {
    private static final Set<String> CASES=Set.of("help_attacker_en_route","help_defender_en_route","ordinary_last_compatible","help_retreating_arrived","help_empty_en_route","already_participating","ordinary_no_compatible");
    private static void pins() throws Exception {
        ArmyOriginalSourcePins.verify("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_reinforcement_assignment_contract.py","f1fc21aa298296655eb7a785ca697c597a1bc7555baea087b6271bc9d27c01ec");
        ArmyOriginalSourcePins.verify("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_reinforcement_arrival_admission_contract.py","47cf6f20121213acc9198caf650f96e34fe5e90c6457f5b23f42a88fa7860887");
        ArmyOriginalSourcePins.verify("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_reinforcement_arrival_assessment.py","68c9a1d324d10314f8400ff842f9cb0dd1205f090bd0ab71a6d5adcb5828c413");
        ArmyOriginalSourcePins.verify("ck3_autonomous_player/tests/unit/test_battle_reinforcement_assignment_v1_bridge.py","677efadca527be2280a77851054c280566ee87a1a25dd9981e5d10ecf74b7949");
    }
    private static ObjectNode fixture() throws Exception {
        pins();return BattleOriginalOracle.call("""
                import importlib.util,json
                path=root/'ck3_autonomous_player'/'tests'/'unit'/'test_battle_reinforcement_assignment_v1_bridge.py'
                spec=importlib.util.spec_from_file_location('xar_reinforcement_original_fixture',path)
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                print(json.dumps({'available':module._native_result(),'unavailable':module._native_result('unavailable')},allow_nan=False))
                """,ArmyJson.empty());
    }
    private static ObjectNode originalConsumer(ObjectNode frame) throws Exception {return BattleOriginalOracle.call("""
            import json,sys
            from dataclasses import asdict
            from xar_autoplayer.bridge.battle_reinforcement_assignment_contract import normalize_battle_reinforcement_assignment_v1
            from xar_autoplayer.bridge.battle_reinforcement_arrival_assessment import derive_battle_reinforcement_arrival_assessment
            v=json.load(sys.stdin)
            normalized=normalize_battle_reinforcement_assignment_v1(v,expected_selected_public_cunit_id=v['selected_public_cunit_id'],expected_snapshot_revision=v['snapshot_revision'],expected_observed_date_raw=v['observed_date_raw'])
            print(json.dumps({'normalized':normalized,'assessment':asdict(derive_battle_reinforcement_arrival_assessment(normalized))},allow_nan=False))
            """,frame);}
    private static ObjectNode normalizeOriginal(ObjectNode frame) throws Exception {return (ObjectNode)originalConsumer(frame).get("normalized");}
    @Test void allSevenUntouchedNativeFirstWiresReachOriginalNormalizerTypedConsumerAndPublicSerde() throws Exception {
        pins();String configured=property("xar.army.reinforcementArrivalFirst.root"),manifestPath=property("xar.army.reinforcementArrivalFirst.manifest"),manifestSha=property("xar.army.reinforcementArrivalFirst.manifest.sha256");
        Path manifest=Path.of(manifestPath).toRealPath();byte[] originalManifest=Files.readAllBytes(manifest);assertTrue(originalManifest.length>0&&originalManifest.length<=65536);assertEquals(manifestSha,sha(originalManifest));
        var manifestRef=new ControlBuild.FileRef(manifest.toString(),originalManifest.length,manifestSha);var qualified=ReinforcementArrivalFirstCorpus.require(manifestRef,configured);Set<String> seen=new HashSet<>();
            for(var supplied:qualified.files()) {
                Path path=Path.of(supplied.sourceRef().path()).toRealPath();byte[] original=Files.readAllBytes(path);assertEquals(supplied.sourceRef().bytes(),original.length);assertEquals(supplied.sourceRef().sha256(),sha(original));ObjectNode wire=ArmyJson.parse(original);String name=ArmyJson.text(wire.get("case_name"));assertEquals(supplied.caseName(),name);assertTrue(CASES.contains(name));assertTrue(seen.add(name),"duplicate original FIRST case");
                assertTrue(wire.get("fixture").get("synthetic").booleanValue());assertEquals("df87fd85",wire.get("fixture").get("source_baseline").textValue());
                ObjectNode result=(ObjectNode)wire.get("result"),frame=(ObjectNode)result.get("battle_reinforcement_assignment");assertTrue(frame.get("contact_projection").has("arrival_admission"));
                var expected=originalConsumer(frame);assertEquals(expected.get("normalized"),ArmyReinforcementCodec.normalize(frame,frame.get("selected_public_cunit_id").intValue(),frame.get("snapshot_revision").bigIntegerValue(),frame.get("observed_date_raw").longValue()));
                var context=context(frame);var typed=ArmyReinforcementCodec.decode(ArmyJson.bytes(result),context,new ArmyRequests.Unit(new PublicUnitId(frame.get("selected_public_cunit_id").intValue())));
                assertEquals(frame,OpportunityJson.toNode(typed.originalFrame()));assertTrue(typed.state() instanceof Present<BattleResponses.ReinforcementState>);
                var state=((Present<BattleResponses.ReinforcementState>)typed.state()).value();assertTrue(state.contact().arrivalAdmission() instanceof Present<ArmyReinforcementCodec.Arrival>);
                var assessment=ArmyReinforcementAssessment.derive(typed);assertEquals(expected.get("assessment"),OpportunityJson.toNode(ArmyReinforcementAssessment.json(assessment)));assertFalse(assessment.futureBinding());
                var publicWire=ArmyPublicWire.encode(typed.originalFrame(),context);assertEquals(typed.originalFrame(),ArmyPublicWire.decode(publicWire,context));assertEquals(frame,ArmyReinforcementCodec.normalize(OpportunityJson.toNode(ArmyPublicWire.decode(publicWire,context)),typed.selected().value(),context.nativeRevision(),context.dateRaw().longValueExact()));
                assertArrayEquals(original,Files.readAllBytes(path),"raw producer file must remain untouched");
            }
        assertEquals(CASES,seen,"the complete original seven-case producer corpus is mandatory");
        assertArrayEquals(originalManifest,Files.readAllBytes(manifest));assertEquals(qualified.files(),ReinforcementArrivalFirstCorpus.require(manifestRef,configured).files());
    }
    @Test void nullablePowerDuplicateStoredRouteAndUnavailableRemainExact() throws Exception {
        var raw=fixture();var result=(ObjectNode)raw.get("available");var frame=(ObjectNode)result.get("battle_reinforcement_assignment");var source=context(frame);var typed=ArmyReinforcementCodec.decode(ArmyJson.bytes(result),source,new ArmyRequests.Unit(new PublicUnitId(frame.get("selected_public_cunit_id").intValue())));
        var state=((Present<BattleResponses.ReinforcementState>)typed.state()).value();assertTrue(state.signal().requestPowerBasisRaw() instanceof NullValue<Long>);assertEquals(2,state.route().provinces().size());assertEquals(state.route().provinces().getFirst(),state.route().provinces().getLast());
        var unavailable=(ObjectNode)raw.get("unavailable");var denied=ArmyReinforcementCodec.decode(ArmyJson.bytes(unavailable),source,new ArmyRequests.Unit(typed.selected()));assertFalse(denied.ready());assertTrue(denied.state() instanceof NullValue<BattleResponses.ReinforcementState>);assertEquals(normalizeOriginal((ObjectNode)unavailable.get("battle_reinforcement_assignment")),OpportunityJson.toNode(denied.originalFrame()));
    }
    @Test void independentNativeSlotRouteFinalTimelineAndParentMembershipMustAllAgree() throws Exception {
        var frame=(ObjectNode)fixture().get("available").get("battle_reinforcement_assignment");
        for(String corruption:List.of("native_slot","eta","timeline","parent","power","bool","extra","missing")) {
            var bad=frame.deepCopy();switch(corruption) {
                case "native_slot"->((ObjectNode)bad.get("route")).put("move_target_province_id",2580);
                case "eta"->((ObjectNode)bad.get("route")).put("assignment_eta_date_raw",1);
                case "timeline"->((ObjectNode)bad.get("route")).putNull("arrival_date_raws");
                case "parent"->((ObjectNode)bad.get("native_order").get("parent_subunits_in_stored_order").get(0)).withArray("public_cunit_ids_in_stored_order").removeAll();
                case "power"->((ObjectNode)bad.get("signal")).put("request_power_basis_raw",0);
                case "bool"->bad.put("schema_version",true);case "extra"->bad.put("invented",false);case "missing"->bad.remove("contact_projection");default->throw new AssertionError();
            }
            assertThrows(IllegalArgumentException.class,()->ArmyReinforcementCodec.normalize(bad,frame.get("selected_public_cunit_id").intValue(),frame.get("snapshot_revision").bigIntegerValue(),frame.get("observed_date_raw").longValue()),corruption);
        }
    }
    private static Context context(ObjectNode frame) {
        BigInteger revision=frame.get("snapshot_revision").bigIntegerValue(),date=frame.get("observed_date_raw").bigIntegerValue();var ref=new ExactRef("original-fixture-source",1,"a".repeat(64));var source=new G2Source("source-shaped-test-machine","2026-10-24T00:00:00Z","1.20.0.3",ref);
        var observed=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,revision,date),"fixture:"+revision,BigInteger.valueOf(9),"fixture-episode");return new Context(new ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),observed,1),source,"fixture-session",Instant.parse("2026-10-24T00:01:00Z"));
    }
    private static String property(String name){String value=System.getProperty(name);if(value==null||value.isBlank())throw new IllegalStateException("required source-bound corpus property missing: "+name);return value;}
    private static String sha(byte[] bytes)throws Exception{return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes));}
}
