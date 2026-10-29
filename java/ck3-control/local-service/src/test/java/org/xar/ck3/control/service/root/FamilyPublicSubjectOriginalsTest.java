package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Proxy;
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
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.service.mcp.FamilySupplementPublicCodec;

/** Original subject producer -> public JSON -> retained exact original -> the unique real native value preparer. */
final class FamilyPublicSubjectOriginalsTest {
    @TempDir static Path directory;
    static JsonNode oracle;
    static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    static final ExactRef REF=new ExactRef("controlled/subject-original",1,"a".repeat(64));
    @BeforeAll static void unchangedPythonSubjectProducer()throws Exception {
        String script="""
                import copy,importlib.util,json,pathlib,sys
                root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
                spec=importlib.util.spec_from_file_location('original_subject_test',root/'ck3_autonomous_player/tests/unit/test_player_child_marriage_subject_private_transport.py')
                unit=importlib.util.module_from_spec(spec);spec.loader.exec_module(unit)
                from xar_autoplayer.bridge.player_child_marriage_subject_private_transport import query_player_child_marriage_subject_private_v1 as query
                frame=unit._frame();frame['snapshot_id']='native:3';frame['diagnostics']={'hello':{'game_version':'1.20.0.4','executable_sha256':sys.argv[2]}}
                packet=unit._reply();driver=unit._Driver(packet,[copy.deepcopy(frame),copy.deepcopy(frame)])
                value=query(driver,expected_native_revision=3,subject_character_id=37265)
                print(json.dumps({'native':packet['result'],'public':value},sort_keys=True,separators=(',',':')))
                """;
        String python=System.getProperty("xar.python"),root=System.getProperty("xar.repository.root");assertNotNull(python);assertNotNull(root);
        Path output=directory.resolve("subject-original-python.json");
        var builder=new ProcessBuilder(python,"-B","-c",script,root,Build.CROZIER4.sha256()).redirectErrorStream(true).redirectOutput(output.toFile());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        var process=builder.start();if(!process.waitFor(30,TimeUnit.SECONDS)){process.destroyForcibly();fail("original subject producer timeout");}
        assertTrue(Files.size(output)<=131072);assertEquals(0,process.exitValue(),Files.readString(output));oracle=StrictJson.parse(Files.readAllBytes(output),131072);
    }
    @Test void completeSubjectOriginalSurvivesPublicSerdeAndPreparesTheSameNativeValueFields() throws java.io.IOException {
        Fixture f=fixture();var subjects=new RootFamilySupplementReadPublicProducts.Subjects();subjects.remember(f.known(),f.archive());
        assertEquals(oracle.get("public"),OpportunityJson.toNode(f.known().value()));
        var input=publicValue(f.known().value());var selected=subjects.find(input,f.context(),f.archive());assertSame(f.known(),selected);
        ObjectNode flat=StrictJson.object().put("candidate_character_id",input.candidateCharacterId()).put("request_matrilineal_option",false);
        flat.set("legality",OpportunityJson.toNode(input.legality()));flat.set("subject_read",selected.originalReceipt().toJson());
        Obj canonical=f.queries().canonicalValue(f.context(),DriverJson.object(flat.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES));
        var request=new PlanningReadRequest(f.context().before(),f.context().source(),f.context().sessionId(),f.queries().value().operation(),canonical,f.context().deadline());
        var fields=StrictJson.parse(f.queries().value().prepare(request,"controlled-child-value").additionalFields().bytes());
        assertEquals(5,fields.get("legality_query_sequence").intValue());assertEquals(37265,fields.get("subject_character_id").intValue());
        assertEquals(40001,fields.get("candidate_character_id").intValue());assertFalse(fields.has("expected_revision"));
    }
    @Test void copiedJsonWithoutOriginalOrChangedNativeLegalityCannotGrantAValueRead() throws java.io.IOException {
        Fixture f=fixture();var input=publicValue(f.known().value());var subjects=new RootFamilySupplementReadPublicProducts.Subjects();
        assertThrows(IllegalArgumentException.class,()->subjects.find(input,f.context(),f.archive()));subjects.remember(f.known(),f.archive());
        ObjectNode modified=(ObjectNode)OpportunityJson.toNode(input.legality());
        ((ObjectNode)modified.get("native_legal_candidates").get(0)).put("recipient_ai_accept_raw",501);
        var wrong=new FamilySupplementPublicCodec.ChildValue(DriverJson.object(modified.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES),40001,false);
        assertThrows(IllegalArgumentException.class,()->subjects.find(wrong,f.context(),f.archive()));
        var lost=archive(f.known().receipt(),new ExactRef("controlled/wrong-reference",1,"b".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->subjects.find(input,f.context(),lost));
    }
    private record Fixture(Context context,FamilyChildMarriageQueries queries,PlanningReadResult.Known<Obj> known,ActionPorts.OutcomeArchive archive){}
    private static Fixture fixture() throws java.io.IOException {
        var source=new G2Source("controlled-child-public",NOW.toString(),Build.CROZIER4.version(),REF);
        var frame=new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(3),BigInteger.valueOf(53215920));
        var proposal=new JointBudgetSelector.ProposalFrame(frame,"native:3",BigInteger.valueOf(4),"controlled-child-episode");
        var identity=new ObservationIdentity(source.machineId(),new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),proposal,1);
        var context=new Context(identity,source,"controlled-child-session",BigInteger.TWO,Build.CROZIER4,NOW.plusSeconds(30),
                new ControlFrame(true,true,true,1,19L,29829L,"controlled-child-episode",false,null,null,List.of()));
        var flat=StrictJson.object().put("expected_native_revision",3).put("subject_character_id",37265);
        var request=new PlanningReadRequest(identity,source,context.sessionId(),new OperationKey(FamilyChildMarriageSubject.STEP),
                FamilyChildMarriageQueries.canonicalSubject(context,DriverJson.object(flat.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES)),context.deadline());
        var packet=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","controlled-subject").put("ok",true);packet.set("result",oracle.get("native"));
        var raw=new RawJson(StrictJson.canonical(packet));var ack=new NativeActionPort.AckReceived("controlled-subject",true,Optional.of(new RawJson(StrictJson.canonical(oracle.get("native")))),raw,NativeWire.packet(raw.bytes()));
        var evidence=new GuardEvidence(identity,source,context.sessionId(),BigInteger.TWO,request.operation(),REF,REF,"controlled-subject-data",NOW,context.deadline());
        var guard=new PlanningReadGuard(evidence,true,true,true,"1".repeat(64));
        var receipt=new PlanningReadReceipt(request,FamilyChildMarriageQueries.SUBJECT_ID,"controlled-subject",guard,guard,ack);
        var archive=archive(receipt,REF);
        var originals=new FamilyChildMarriageQueries.Originals(){public PlanningReadReceipt loadRead(ExactRef ref){return archive.loadRead(ref);}public ExactRef referenceOf(PlanningReadReceipt value){return archive.readReferenceOf(value);}};
        var queries=new FamilyChildMarriageQueries(new FamilyChildMarriageQueries.Sources(REF,REF),originals,actual->{});
        return new Fixture(context,queries,new PlanningReadResult.Known<>(queries.subject().replay(receipt),receipt,REF),archive);
    }
    private static FamilySupplementPublicCodec.ChildValue publicValue(Obj actual) {
        ObjectNode input=StrictJson.object().put("candidate_character_id",40001).put("request_matrilineal_option",false);
        input.set("legality",StrictJson.parse(FamilySupplementPublicCodec.publicResult(actual).bytes(),1048576));
        return FamilySupplementPublicCodec.decodeValue(new RawJson(StrictJson.canonical(input)));
    }
    private static ActionPorts.OutcomeArchive archive(PlanningReadReceipt receipt,ExactRef actualRef) {
        return (ActionPorts.OutcomeArchive)Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->switch(method.getName()) {
            case "readReferenceOf"->{assertEquals(receipt,args[0]);yield actualRef;}
            case "loadRead"->{StrictJson.require(actualRef.equals(args[0]),"unknown exact subject original");yield receipt;}
            case "toString"->"controlled DATA archive only";
            default->throw new UnsupportedOperationException("no Root/writer/action authority in this fixture: "+method.getName());
        });
    }
}

