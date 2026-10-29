package org.xar.ck3.control.nativebridge.capabilities.family;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original unchanged Python producer -> real Java contract/replay. These are DATA fixtures, not a Root authority. */
final class EpidemicTreatmentPresenceQueriesTest {
    @TempDir static Path directory;
    static JsonNode cases;
    static final ExactRef REF=new ExactRef("controlled/treatment-source",1,"a".repeat(64));
    static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    @BeforeAll static void originalPythonProducer()throws Exception {
        String script="""
                import importlib.util,json,pathlib,sys
                root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
                spec=importlib.util.spec_from_file_location('original_treatment_test',root/'ck3_autonomous_player/tests/unit/test_epidemic_treatment_private_transport.py')
                unit=importlib.util.module_from_spec(spec);spec.loader.exec_module(unit)
                from xar_autoplayer.bridge.epidemic_treatment_private_transport import query_player_epidemic_treatment_presence_private_v1 as query
                out=[]
                for present in (True,False,None):
                    driver=unit._Driver(unit._result(present))
                    value=query(driver,expected_revision=172)
                    out.append({'native':driver.value,'public':value,'snapshot':driver.snapshot})
                print(json.dumps(out,sort_keys=True,separators=(',',':')))
                """;
        Path output=directory.resolve("original-treatment.json");
        var builder=new ProcessBuilder(required("xar.python"),"-B","-c",script,required("xar.repository.root")).redirectErrorStream(true).redirectOutput(output.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        var process=builder.start();if(!process.waitFor(30,TimeUnit.SECONDS)){process.destroyForcibly();fail("original Python treatment producer timeout");}
        assertTrue(Files.size(output)<=131072);assertEquals(0,process.exitValue(),Files.readString(output));
        cases=StrictJson.parse(Files.readAllBytes(output),131072);assertEquals(3,cases.size());
    }
    @Test void originalPresenceAbsenceAndUnavailableMatchCompleteProjectionAndReplay() throws java.io.IOException {
        int[] admission={0};var contract=EpidemicTreatmentPresenceQueries.contract(REF,request->admission[0]++);
        for(JsonNode item:cases) {
            var receipt=receipt(item.get("native"));
            assertEquals(item.get("public"),OpportunityJson.toNode(contract.decode(receipt)));
            assertEquals(contract.decode(receipt),contract.replay(receipt));
            assertEquals(contract.decode(receipt),OpportunityJson.parse(OpportunityJson.encode(contract.decode(receipt))));
            assertEquals(0,admission[0],"archive replay cannot call current admission");
            var prepared=contract.prepare(receipt.request(),"controlled-treatment");
            assertEquals(0,StrictJson.parse(prepared.additionalFields().bytes()).size(),"NativeWire owns actual native expected_revision");
        }
        assertEquals(3,admission[0]);
    }
    @Test void wrongKeyUnverifiedDurationBooleanRevisionAndIncompleteEnvelopeRefuse() {
        ObjectNode original=(ObjectNode)cases.get(0).get("native");
        ObjectNode key=original.deepCopy();((ObjectNode)key.get("player_epidemic_treatment_presence")).put("modifier_key","other");
        assertThrows(IllegalArgumentException.class,()->EpidemicTreatmentPresenceQueries.decode(receipt(key)));
        ObjectNode duration=original.deepCopy();((ObjectNode)duration.get("player_epidemic_treatment_presence").get("remaining_days")).put("value",100);
        assertThrows(IllegalArgumentException.class,()->EpidemicTreatmentPresenceQueries.decode(receipt(duration)));
        ObjectNode wrong=original.deepCopy();wrong.put("query_sequence",true);
        assertThrows(IllegalArgumentException.class,()->EpidemicTreatmentPresenceQueries.decode(receipt(wrong)));
        ObjectNode missing=original.deepCopy();missing.remove("read_only");
        assertThrows(IllegalArgumentException.class,()->EpidemicTreatmentPresenceQueries.decode(receipt(missing)));
    }
    @Test void guardDriftAndNativeErrorCannotBecomeAnObservedPresence() throws java.io.IOException {
        var original=receipt(cases.get(0).get("native"));var before=original.before();
        var after=new PlanningReadGuard(before.binding(),true,true,true,"b".repeat(64));
        var drift=new PlanningReadReceipt(original.request(),original.contractId(),original.requestId(),before,after,original.original());
        assertThrows(IllegalArgumentException.class,()->EpidemicTreatmentPresenceQueries.decode(drift));
        ObjectNode error=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",original.requestId()).put("ok",false).put("error","unsupported");
        RawJson raw=new RawJson(StrictJson.canonical(error));var ack=new NativeActionPort.AckReceived(original.requestId(),false,Optional.empty(),raw,NativeWire.packet(raw.bytes()));
        var rejected=new PlanningReadReceipt(original.request(),original.contractId(),original.requestId(),before,before,ack);
        assertThrows(IllegalArgumentException.class,()->EpidemicTreatmentPresenceQueries.decode(rejected));
    }
    private static PlanningReadReceipt receipt(JsonNode result) throws java.io.IOException {
        var identity=identity();var source=source();
        var request=new PlanningReadRequest(identity,source,"controlled-treatment-session",new OperationKey(EpidemicTreatmentPresenceQueries.STEP),
                EpidemicTreatmentPresenceQueries.arguments(BigInteger.valueOf(172)),NOW.plusSeconds(30));
        ObjectNode packet=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","controlled-treatment").put("ok",true);packet.set("result",result);
        RawJson raw=new RawJson(StrictJson.canonical(packet));var ack=new NativeActionPort.AckReceived("controlled-treatment",true,Optional.of(new RawJson(StrictJson.canonical(result))),raw,NativeWire.packet(raw.bytes()));
        var evidence=new GuardEvidence(identity,source,request.sessionId(),BigInteger.TWO,request.operation(),REF,REF,"controlled-treatment-data",NOW,NOW.plusSeconds(30));
        var guard=new PlanningReadGuard(evidence,true,true,true,"1".repeat(64));
        return new PlanningReadReceipt(request,EpidemicTreatmentPresenceQueries.CONTRACT_ID,"controlled-treatment",guard,guard,ack);
    }
    private static G2Source source(){return new G2Source("controlled-treatment",NOW.toString(),FamilyObligations.Build.CURRENT4.exactBuild(),REF);}
    private static ObservationIdentity identity() {
        var frame=new JointBudgetSelector.Frame(BigInteger.valueOf(36403),BigInteger.valueOf(171),BigInteger.valueOf(53350560));
        var proposal=new JointBudgetSelector.ProposalFrame(frame,"native:171",BigInteger.valueOf(172),"controlled-treatment-episode");
        return new ObservationIdentity(source().machineId(),new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),proposal,1);
    }
    private static String required(String key){String value=System.getProperty(key);assertNotNull(value,"required complete-CI property "+key);assertFalse(value.isBlank());return value;}
}

