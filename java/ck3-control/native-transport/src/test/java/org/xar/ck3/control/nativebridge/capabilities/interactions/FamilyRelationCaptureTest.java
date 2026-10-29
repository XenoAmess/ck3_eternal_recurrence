package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyCurrentRelationTest.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.writer.StorageWriteGuard;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual sole reader->native-hash/CAS->capture producer. The local gate measures no runtime storage or Game qualification. */
final class FamilyRelationCaptureTest {
    @TempDir Path directory;
    private final Clock clock=Clock.fixed(NOW,ZoneOffset.UTC);
    private Fixture fixture(String id)throws Exception {
        Path root=directory.resolve(id);Files.createDirectory(root);var actual=new FamilyCurrentRelationTest();actual.directory=root;
        return actual.fixture(id,relation(),sidecar(id));
    }
    private static FamilyRelationCapture.Original original(Fixture fixture){
        var value=fixture.queries().contract().decode(fixture.receipt());
        return new FamilyRelationCapture.Original(fixture.queries(),new PlanningReadResult.Known<>(value,fixture.receipt(),SOURCE),fixture.queries().decodeReceipt(fixture.receipt()),fixture.archive());
    }
    @Test void actualCapturedOriginalsAndPublic64DecisionKeepTheSameQueryAndNoOutcomeCredit()throws Exception {
        var fixture=fixture("capture-actual");var source=original(fixture);Path output=directory.resolve("fresh/output");var guard=new SoftwareGate(directory);
        var result=FamilyRelationCapture.capture(new FamilyRelationCapture.Request(output,59077),clock,guard,directory.resolve("writer.lock"),()->source);
        assertEquals(1,guard.calls);assertEquals(1,fixture.admissions().get());assertEquals(1,fixture.archive().writes);
        assertArrayEquals(Files.readAllBytes(fixture.sidecar()),Files.readAllBytes(output.resolve("guardian-two-factory-source.json")));
        assertArrayEquals(fixture.receipt().original().originalFrame().bytes(),Files.readAllBytes(output.resolve("guardian-family-command-result.json")));
        var typed=fixture.queries().decodeReceipt(fixture.receipt());
        assertEquals(FamilyCurrentRelationPublic.captureFamily(typed),DriverJson.object(Files.readAllBytes(output.resolve("family-result.json")),64*1024*1024));
        assertEquals(result.body(),DriverJson.object(Files.readAllBytes(output.resolve(FamilyRelationCapture.RECEIPT)),64*1024*1024));
        var body=OpportunityJson.toNode(result.body());assertEquals("FRAME_QUALIFIED_DISCOVERY_WRITTEN",body.get("status").textValue());
        assertEquals("18446744073709551615",body.path("native_factory_discovery_v1").get("pump_epoch").textValue());
        assertEquals("3",body.path("guardian_family_decision_inputs_v1").path("frame").get("native_revision").textValue());
        assertEquals("3",body.get("actual_native_revision_before").textValue());assertFalse(body.get("guardian_membership_observed").booleanValue());
        assertFalse(body.get("guardian_pair_ready").booleanValue());assertEquals(0,body.get("G2_outcome_credit").intValue());
        assertEquals(FamilyCurrentRelationPublic.SCHEMA,body.get("public_numeric_schema").textValue());
        assertThrows(IllegalArgumentException.class,()->FamilyRelationCapture.capture(new FamilyRelationCapture.Request(output,59077),clock,guard,directory.resolve("writer.lock"),()->{throw new AssertionError("existing path cannot query");}));
    }
    @Test void finiteGuardRefusalPrecedesDirectoryAndQueryIo()throws Exception {
        var guard=new SoftwareGate(directory);guard.deny=true;var calls=new AtomicInteger();Path output=directory.resolve("denied");
        assertThrows(IOException.class,()->FamilyRelationCapture.capture(new FamilyRelationCapture.Request(output,59077),clock,guard,directory.resolve("writer.lock"),()->{calls.incrementAndGet();throw new AssertionError();}));
        assertFalse(Files.exists(output));assertEquals(0,calls.get());assertEquals(1,guard.calls);
    }
    @Test void actualQueryFailureWritesRedFinallyReceiptWithoutInventingNativeOriginals()throws Exception {
        Path output=directory.resolve("failed-query");var guard=new SoftwareGate(directory);
        assertThrows(IOException.class,()->FamilyRelationCapture.capture(new FamilyRelationCapture.Request(output,59077),clock,guard,directory.resolve("writer.lock"),()->{throw new IOException("actual query unavailable");}));
        var body=OpportunityJson.toNode(DriverJson.object(Files.readAllBytes(output.resolve(FamilyRelationCapture.RECEIPT)),64*1024*1024));
        assertEquals("RED",body.get("status").textValue());assertTrue(body.get("failure").textValue().contains("actual query unavailable"));
        assertTrue(body.has("ended_at_utc"));assertFalse(Files.exists(output.resolve("family-result.json")));assertFalse(Files.exists(output.resolve("guardian-two-factory-source.json")));
    }
    @Test void unavailableCoordinatorRetainsItsActualAckOriginalWithoutSuccessCredit()throws Exception {
        var fixture=fixture("capture-rejected-original");Path output=directory.resolve("failed-with-original");
        assertThrows(FamilyRelationCapture.QueryUnavailable.class,()->FamilyRelationCapture.capture(new FamilyRelationCapture.Request(output,59077),clock,
                new SoftwareGate(directory),directory.resolve("writer.lock"),()->{throw new FamilyRelationCapture.QueryUnavailable("actual decoder rejected original",java.util.Optional.of(fixture.receipt().original()));}));
        assertArrayEquals(fixture.receipt().original().originalFrame().bytes(),Files.readAllBytes(output.resolve("guardian-family-command-result.json")));
        var body=OpportunityJson.toNode(DriverJson.object(Files.readAllBytes(output.resolve(FamilyRelationCapture.RECEIPT)),64*1024*1024));
        assertEquals("RED",body.get("status").textValue());assertEquals(0,body.get("G2_outcome_credit").intValue());assertFalse(body.get("guardian_membership_observed").booleanValue());
        assertNotNull(body.get("native_factory_export"));assertFalse(Files.exists(output.resolve("family-result.json")));
    }
    @Test void wrongOwnedGameAndAlteredCasCannotBecomeACaptureSuccess()throws Exception {
        var fixture=fixture("capture-pid");var source=original(fixture);Path wrong=directory.resolve("wrong-pid");
        assertThrows(IllegalArgumentException.class,()->FamilyRelationCapture.capture(new FamilyRelationCapture.Request(wrong,59078),clock,new SoftwareGate(directory),directory.resolve("writer.lock"),()->source));
        assertEquals("RED",OpportunityJson.toNode(DriverJson.object(Files.readAllBytes(wrong.resolve(FamilyRelationCapture.RECEIPT)),64*1024*1024)).get("status").textValue());
        var reference=fixture.archive().originals.keySet().iterator().next();fixture.archive().originals.put(reference,raw(InteractionJson.F.objectNode()));
        Path corrupt=directory.resolve("corrupt-cas");assertThrows(RuntimeException.class,()->FamilyRelationCapture.capture(new FamilyRelationCapture.Request(corrupt,59077),clock,new SoftwareGate(directory),directory.resolve("writer.lock"),()->source));
        assertEquals("RED",OpportunityJson.toNode(DriverJson.object(Files.readAllBytes(corrupt.resolve(FamilyRelationCapture.RECEIPT)),64*1024*1024)).get("status").textValue());
    }
    @Test void originalPythonCaptureProducerMatchesTheSameActualQueryFilesAndDerivedBusinessFields()throws Exception {
        FamilyRelationOriginalPins.verify();Path repository=FamilyRelationOriginalPins.repository();
        Path producer=repository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/guardian_factory_capture_private_v1.py");
        byte[] producerBytes=Files.readAllBytes(producer);assertEquals(7855,producerBytes.length);
        assertEquals("e9e680fd94923c2dc5937cbc7aa7820bcae071b6e04b5e98cc3359dd1fa7bc0e",DriverJson.sha256(producerBytes));
        var fixture=fixture("capture-original-python");var source=original(fixture);var typed=source.observation();
        Path javaOutput=directory.resolve("java-capture"),pythonOutput=directory.resolve("python-capture"),input=directory.resolve("capture-input.json");
        var request=InteractionJson.F.objectNode().put("sidecar_utf8",Files.readString(fixture.sidecar()));
        request.set("family",OpportunityJson.toNode(FamilyCurrentRelationPublic.captureFamily(typed)));
        request.set("command",InteractionJson.parse(fixture.receipt().original().originalFrame()));Files.write(input,raw(request).bytes());
        String script="""
            import json,pathlib,sys
            from copy import deepcopy
            root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge import guardian_factory_capture_private_v1 as producer
            assert pathlib.Path(producer.__file__).resolve()==pathlib.Path(sys.argv[4]).resolve()
            data=json.loads(pathlib.Path(sys.argv[2]).read_text('utf-8'))
            class Driver:
                def __init__(self):self.queries=0
                def diagnostics(self):return dict(connected=True,bridge_pid=59077)
                def take_internal_semantic_snapshot(self):
                    return dict(snapshot_id='native:3',revision=4,native_revision=3,date_raw=53215920,paused=True,map_ready=True,played_character_id=29829,
                      played_character=dict(character_id=29829,alive=True),episode_run_id='fixture-relation',diagnostics=dict(bridge_pid=59077,connection_generation=2,
                      hello=dict(expected_ck3_version='1.20.0.4',expected_ck3_sha256='98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518')))
                def query_current_first_heir_relationship_private_v1(self,**args):
                    assert args['expected_native_revision']==3 and args['timeout_seconds']==12
                    self.queries+=1;assert self.queries==1
                    sidecar=pathlib.Path(args['guardian_factory_sidecar_path']);sidecar.write_text(data['sidecar_utf8'],encoding='utf-8')
                    (sidecar.parent/'guardian-family-command-result.json').write_text(json.dumps(data['command']),encoding='utf-8')
                    return deepcopy(data['family'])
            driver=Driver();result=producer.capture_with_runtime_owner_driver(driver,owned_game_pid=59077,output_directory=pathlib.Path(sys.argv[3]),timeout_seconds=12)
            assert driver.queries==1;print(json.dumps(result,separators=(',',':')))
            """;
        var builder=new ProcessBuilder(FamilyRelationOriginalPins.required("xar.python"),"-B","-c",script,repository.toString(),input.toString(),pythonOutput.toString(),producer.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");Path stdout=directory.resolve("capture-oracle.out"),stderr=directory.resolve("capture-oracle.err");
        builder.redirectOutput(stdout.toFile());builder.redirectError(stderr.toFile());var child=builder.start();
        try {assertTrue(child.waitFor(30,java.util.concurrent.TimeUnit.SECONDS));assertEquals(0,child.exitValue(),()->{try{return Files.readString(stderr);}catch(IOException error){return error.toString();}});
            assertTrue(Files.size(stdout)<=16*1024*1024);var expected=org.xar.ck3.control.nativebridge.NativeWire.parse(Files.readAllBytes(stdout));
            var actual=OpportunityJson.toNode(FamilyRelationCapture.capture(new FamilyRelationCapture.Request(javaOutput,59077),clock,new SoftwareGate(directory),directory.resolve("writer.lock"),()->source).body());
            for(String field:List.of("status","owned_game_pid","actual_date_raw_before","actual_played_character_id_before","sidecar_request_id","sidecar_frame_qualified","actual_factory_found_count","fixed_record_statuses","public_family_result_changed","registered_MCP_consumer_count","guardian_membership_observed","guardian_pair_ready","G2_outcome_credit"))assertEquals(expected.get(field),actual.get(field),field);
            for(String field:List.of("actual_native_revision_before","actual_public_revision_before","sidecar_native_revision"))assertEquals(expected.get(field).bigIntegerValue().toString(),actual.get(field).textValue(),field);
            assertEquals(expected.get("native_factory_discovery_v1"),OpportunityJson.toNode(typed.materials().orElseThrow().original()));
            assertEquals(expected.get("guardian_family_decision_inputs_v1"),OpportunityJson.toNode(FamilyRelationGuardianMaterials.decision(typed.materials(),typed.descendants(),REV,HEIR)));
            assertArrayEquals(Files.readAllBytes(pythonOutput.resolve("guardian-two-factory-source.json")),Files.readAllBytes(javaOutput.resolve("guardian-two-factory-source.json")));
            assertEquals(DriverJson.object(Files.readAllBytes(pythonOutput.resolve("family-result.json")),64*1024*1024),DriverJson.object(Files.readAllBytes(javaOutput.resolve("family-result.json")),64*1024*1024));
        }finally{if(child.isAlive())child.destroyForcibly();}
        assertEquals("e9e680fd94923c2dc5937cbc7aa7820bcae071b6e04b5e98cc3359dd1fa7bc0e",DriverJson.sha256(Files.readAllBytes(producer)));FamilyRelationOriginalPins.verify();
    }
    private static final class SoftwareGate implements StorageWriteGuard {
        private final Path root;int calls;boolean deny;
        SoftwareGate(Path root){this.root=root.toAbsolutePath().normalize();}
        @Override public void close(){ }
        @Override public void requireInitialization(Path lock,List<Path> roots){throw new AssertionError("software capture does not initialize a writer");}
        @Override public <T>T write(WritePlan plan,PhysicalWrite<T> io)throws IOException {
            calls++;assertEquals(root.resolve("writer.lock"),plan.originalLock());assertTrue(plan.mutations().size()>=5&&plan.mutations().size()<=132);
            for(var mutation:plan.mutations()){assertTrue(mutation.target().startsWith(root));if(mutation instanceof FileCreate file)assertTrue(file.maxLogicalBytes()>0&&file.maxLogicalBytes()<=64L*1024*1024);}
            if(deny)throw new IOException("software finite card denied");return io.run();
        }
    }
}
