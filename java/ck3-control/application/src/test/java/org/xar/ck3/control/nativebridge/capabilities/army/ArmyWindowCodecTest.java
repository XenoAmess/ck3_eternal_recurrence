package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Original Python production normalizers and fixtures are differential oracles, never Native business evidence. */
final class ArmyWindowCodecTest {
    private static ObjectNode originals() throws Exception {
        verifyPins();
        return BattleOriginalOracle.call("""
                import importlib.util,json,sys
                sys.path.insert(0,str(root/'ck3_autonomous_player'/'tests'/'unit'))
                path=root/'ck3_autonomous_player'/'tests'/'unit'/'test_war_declared_overview_transport.py'
                spec=importlib.util.spec_from_file_location('xar_overview_original_fixture',path)
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                from xar_autoplayer.bridge.war_declared_overview_transport import _result
                before={'played_character':{'character_id':31254},'date_raw':53169792,'native_revision':617}
                top=module._reply({'request_id':'original-overview'},before)
                binding={'snapshot_id':'fixture:617','revision':9,'native_revision':617,'date_raw':53169792,'actor_character_id':31254,'connection_generation':17,'episode_run_id':'fixture-episode'}
                normalized=_result(top,'original-overview','query',binding,17)
                path=root/'ck3_autonomous_player'/'tests'/'test_war_results_window_contract_b15.py'
                spec=importlib.util.spec_from_file_location('xar_results_original_fixture',path)
                results=importlib.util.module_from_spec(spec);spec.loader.exec_module(results)
                leaf=results.old_leaf();leaf.update(dismiss_stage='callback_returned',dismiss_exception_code=0,dispatch_invoked=True,native_handled=True)
                owner={'request_id':leaf['request_id'],'ticket_sequence':303,'executor_started_sequence':303,'completed_sequence':303,'pump_epoch':101,'thread_id':202,'date_raw':53169792,'connection_generation':13}
                normalized_results=results.normalize(leaf)
                result_top={'type':'command_result','protocol_version':1,'request_id':leaf['request_id'],'ok':True,'result':leaf,'war_results_window_owner_receipt':owner}
                from copy import deepcopy
                from xar_autoplayer.bridge.war_results_window_transport import _result as results_result
                role_cases=[]
                for name,source,operation,producer,owner_key in (
                    ('OVERVIEW',top,'query',_result,'war_declared_overview_owner_receipt'),
                    ('RESULTS',result_top,'close',results_result,'war_results_window_owner_receipt')):
                    for driver_generation in (0,17):
                        packet=deepcopy(source)
                        packet['result']['connection_generation']=23
                        packet[owner_key]['connection_generation']=23
                        driver_binding={**binding,'connection_generation':driver_generation}
                        value=producer(packet,packet['request_id'],operation,driver_binding,23)
                        role_cases.append({'kind':name,'operation':operation.upper(),'top':packet,'normalized':value,'driver_generation':driver_generation})
                print(json.dumps({'overview':{'top':top,'normalized':normalized},'results':{'top':result_top,'normalized':normalized_results},'role_cases':role_cases},allow_nan=False))
                """,ArmyJson.empty());
    }
    @Test void realOriginalQueryNormalizerAndIndependentOwnerArePreservedExactly() throws Exception {
        var row = (ObjectNode)originals().get("overview"); var observed = decode((ObjectNode)row.get("top"),ArmyWindowCodec.Kind.OVERVIEW,ArmyWindowCodec.Operation.QUERY,17,17);
        assertEquals(row.get("normalized"),observed.normalized()); assertEquals("visible",observed.status()); assertTrue(observed.available());
        var detached = observed.normalized(); detached.withObject("native_command_result").withObject("war_declared_overview_owner_receipt").put("thread_id",99);
        assertEquals(31,observed.owner().get("thread_id").intValue());
    }
    @Test void wrongOwnerMissingFieldsBooleanIntegersAndFalseAbsenceFailClosed() throws Exception {
        var row = (ObjectNode)originals().get("overview").get("top");
        for (String corruption : List.of("owner","started","pump","boolean","absence","null","extra","partial_trace")) {
            ObjectNode top = row.deepCopy(); var leaf = (ObjectNode)top.get("result"); var owner = (ObjectNode)top.get("war_declared_overview_owner_receipt");
            switch(corruption) {
                case "owner" -> owner.put("request_id","another-request"); case "started" -> owner.put("executor_started_sequence",14);
                case "pump" -> leaf.put("pump_epoch",24); case "boolean" -> leaf.put("post_observed",1);
                case "absence" -> { leaf.put("window_present",false).put("effective_visible",false).put("post_window_present",false).put("post_effective_visible",false).put("status","absent"); }
                case "null" -> top.putNull("war_declared_overview_owner_receipt"); case "extra" -> leaf.put("invented",true); case "partial_trace" -> leaf.put("close_stage","not_attempted");
                default -> throw new AssertionError();
            }
            assertThrows(IllegalArgumentException.class,()->decode(top,ArmyWindowCodec.Kind.OVERVIEW,ArmyWindowCodec.Operation.QUERY,17,17),corruption);
        }
    }
    @Test void callbackCompletedStillVisibleRetainsUnknownAndCannotClaimClosure() throws Exception {
        var row = (ObjectNode)originals().get("results"); var top = (ObjectNode)row.get("top"); var observed = decode(top,ArmyWindowCodec.Kind.RESULTS,ArmyWindowCodec.Operation.CLOSE,13,13);
        assertEquals(row.get("normalized"),observed.leaf()); assertFalse(observed.available()); assertEquals("verification_pending",observed.status());
        var forged = top.deepCopy(); ((ObjectNode)forged.get("result")).put("available",true).put("accepted",true).put("closure_verified",true).put("status","closed_verified").put("unavailable_reason","");
        assertThrows(IllegalArgumentException.class,()->decode(forged,ArmyWindowCodec.Kind.RESULTS,ArmyWindowCodec.Operation.CLOSE,13,13));
        ((ObjectNode)forged.get("result")).put("post_effective_visible",false); assertEquals("closed_verified",decode(forged,ArmyWindowCodec.Kind.RESULTS,ArmyWindowCodec.Operation.CLOSE,13,13).status());
    }
    @Test void sourceLeaseAndFullUnsignedOwnerDomainsAreCheckedWithoutRounding() throws Exception {
        var top = (ObjectNode)originals().get("overview").get("top"); var max = new BigInteger("18446744073709551615");
        ((ObjectNode)top.get("result")).put("pump_epoch",max); ((ObjectNode)top.get("war_declared_overview_owner_receipt")).put("pump_epoch",max);
        assertEquals(max,decode(top,ArmyWindowCodec.Kind.OVERVIEW,ArmyWindowCodec.Operation.QUERY,17,17).owner().get("pump_epoch").bigIntegerValue());
        assertThrows(IllegalArgumentException.class,()->decode(top,ArmyWindowCodec.Kind.OVERVIEW,ArmyWindowCodec.Operation.QUERY,18,18));
        ((ObjectNode)top.get("result")).put("native_revision",618); assertThrows(IllegalArgumentException.class,()->decode(top,ArmyWindowCodec.Kind.OVERVIEW,ArmyWindowCodec.Operation.QUERY,17,17));
    }
    @Test void originalBothWindowTransportsKeepNative23AndDriverZeroOr17Independent() throws Exception {
        var cases = originals().withArray("role_cases"); assertEquals(4,cases.size());
        for (var value : cases) {
            var kind = ArmyWindowCodec.Kind.valueOf(value.get("kind").textValue());
            var operation = ArmyWindowCodec.Operation.valueOf(value.get("operation").textValue());
            ObjectNode top = ArmyJson.object(value.get("top")); BigInteger driver = value.get("driver_generation").bigIntegerValue();
            var observed = ArmyWindowCodec.decode(kind,operation,ArmyJson.bytes(top),top.get("request_id").textValue(),context(),BigInteger.valueOf(23),driver);
            assertEquals(value.get("normalized"),observed.normalized());
            assertEquals(BigInteger.valueOf(23),observed.leaf().get("connection_generation").bigIntegerValue());
            assertEquals(driver,observed.normalized().get("queried_connection_generation").bigIntegerValue());
            assertEquals(observed.normalized(),ArmyJson.parse(ArmyJson.bytes(observed.normalized())));
            assertThrows(IllegalArgumentException.class,()->ArmyWindowCodec.decode(kind,operation,ArmyJson.bytes(top),top.get("request_id").textValue(),context(),driver,BigInteger.valueOf(23)));
        }
    }
    @Test void driverAndNativeUnsignedBoundsAreValidatedSeparately() throws Exception {
        ObjectNode row = ArmyJson.object(originals().withArray("role_cases").get(0)); ObjectNode top = ArmyJson.object(row.get("top"));
        BigInteger max = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
        var value = ArmyWindowCodec.decode(ArmyWindowCodec.Kind.OVERVIEW,ArmyWindowCodec.Operation.QUERY,ArmyJson.bytes(top),top.get("request_id").textValue(),context(),BigInteger.valueOf(23),max);
        assertEquals(max,value.normalized().get("queried_connection_generation").bigIntegerValue());
        for (BigInteger bad : List.of(BigInteger.valueOf(-1),max.add(BigInteger.ONE)))
            assertThrows(IllegalArgumentException.class,()->ArmyWindowCodec.decode(ArmyWindowCodec.Kind.OVERVIEW,ArmyWindowCodec.Operation.QUERY,ArmyJson.bytes(top),top.get("request_id").textValue(),context(),BigInteger.valueOf(23),bad));
    }
    private static ArmyWindowCodec.Observation decode(ObjectNode top,ArmyWindowCodec.Kind kind,ArmyWindowCodec.Operation operation,long nativeGeneration,long driverGeneration) { return ArmyWindowCodec.decode(kind,operation,ArmyJson.bytes(top),top.get("request_id").textValue(),context(),BigInteger.valueOf(nativeGeneration),BigInteger.valueOf(driverGeneration)); }
    private static Context context() {
        var ref = new ExactRef("original-fixture-source",1,"a".repeat(64)); var source = new G2Source("source-shaped-test-machine","2026-10-24T00:00:00Z","1.20.0.4",ref);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(31254),BigInteger.valueOf(617),BigInteger.valueOf(53169792)),"fixture:617",BigInteger.valueOf(9),"fixture-episode");
        return new Context(new ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),frame,1),source,"fixture-session",Instant.parse("2026-10-24T00:01:00Z"));
    }
    private static void verifyPins() throws Exception {
        String configured = System.getProperty("xar.repository.root"); if(configured == null || configured.isBlank()) throw new IllegalStateException("required actual original source property missing: xar.repository.root"); var root = java.nio.file.Path.of(configured).toRealPath();
        String[][] pins = {
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/war_declared_overview_contract.py","86ebfb0fc5ba6a0150f28c8ac4aeceb3c65116b03d0f5175a99fc9659377ece0"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/war_results_window_contract.py","3373fd42fc1cf8da88caf515061b4d8909816bf4ace66a6e01b25ac091a6cd66"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/war_declared_overview_transport.py","52183d4339e407bdbc29f9b222d28a7b80c5691a5b67e6ef158e9313a6f77b4c"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/war_results_window_transport.py","e1a3d7d5ae36ccf2a17055d166742f3fd49b11529bdbd383c7b2b9d5640fd86e"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/prewar_force_coalition_transport.py","28ffe1bc6cd9f8042417e16c97bb7c76fe812d5d1386f9015909010eb7203299"},
            {"ck3_autonomous_player/tests/unit/test_war_declared_overview_transport.py","9396dbd32df16530dceaa9b928b5d4c29eaf693e711f7ae27017c62fc6933365"},
            {"ck3_autonomous_player/tests/test_war_results_window_contract_b15.py","37264573cfca1d344146a17f5756df60f4e730f26b42e21d1457543f7e065237"}};
        for(var pin:pins) { var path=root.resolve(pin[0]).toRealPath(); assertTrue(path.startsWith(root)); assertEquals(pin[1],java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(java.nio.file.Files.readAllBytes(path))),"original window producer source drift"); }
    }
}
