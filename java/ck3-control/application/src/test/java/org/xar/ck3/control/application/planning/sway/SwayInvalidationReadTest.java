package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.build.CanonicalOracleEnvironment;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject;

/** Retained .2 serializer fixture content and original Python normalizer, not a current native/Game qualification. */
final class SwayInvalidationReadTest {
    @TempDir Path temp;
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final ExactRef SOURCE=new ExactRef("software:notification-source",1,"a".repeat(64));
    private static final long ACTOR=50331649,TARGET=67108866,ID=33554443;
    private static final SwayObservationReads.InvalidationQuery QUERY=new SwayObservationReads.InvalidationQuery(new NativeSubject(ACTOR,TARGET,ID,2),BigInteger.ZERO);
    @Test void actualRetainedSerializerBranchesReachInstalledFamilyPureReplayAndOriginalPythonNormalizer()throws Exception {
        var reads=new SwayRootReads(new SwayRootReads.Sources(SOURCE,SOURCE,SOURCE),true);
        var catalog=new RootReadContractCatalog(List.of(),reads.families());reads.attach(catalog);
        for(String role:List.of("dead","range","opaque")) {
            var packet=vector(role);var query=new SwayObservationReads.InvalidationQuery(QUERY.subject(),packet.at("/result/sway_completion_invalidation_reason/after_sequence").bigIntegerValue());
            var contract=reads.invalidation(query);assertSame(contract,reads.invalidation(query));assertTrue(catalog.containsIdentity(contract));
            var request=request(contract,"1.20.0.2",query);var nativeRequest=contract.prepare(request,packet.get("request_id").textValue());
            assertEquals(ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,contract.permissionMode());assertEquals(ReadContract.WireProfile.G2_PRIVATE_QUERY,contract.wireProfile());
            var sent=StrictJson.parse(nativeRequest.additionalFields().bytes());assertEquals(ACTOR,sent.get("actor_character_id").longValue());assertEquals(ID,sent.get("scheme_instance_id").longValue());assertFalse(sent.has("action_id"));
            var receipt=receipt(contract,request,packet);var actual=contract.decode(receipt);assertArrayEquals(actual.normalized().bytes(),contract.replay(receipt).normalized().bytes());
            assertArrayEquals(actual.normalized().bytes(),org.xar.ck3.control.contracts.projection.ProjectionJson.object(actual.normalized().bytes(),SwayNativeWire.MAX).bytes());
            var normalized=StrictJson.parse(actual.normalized().bytes());var expected=oracle(role,packet);
            var selected=StrictJson.object();expected.fieldNames().forEachRemaining(name->selected.set(name,normalized.get(name)));assertEquals(expected,selected);
            var publicValue=StrictJson.parse(SwayPublicCodec.publicNormalized(actual).bytes());
            String sequence=switch(role){case "dead"->"1";case "range"->"2";case "opaque"->"3";default->throw new AssertionError(role);};
            assertEquals(sequence,publicValue.at("/records/0/sequence").textValue());assertEquals("7",publicValue.get("snapshot_revision").textValue());
            assertEquals("8",publicValue.get("queried_revision").textValue());assertFalse(publicValue.has("action_id"));assertFalse(publicValue.has("sway_terminal_sources_12004"));
            for(String field:List.of("message_enqueue_observed","render_observed","material_effect_observed","native_end_cause_observed","native_terminal_state_observed"))assertFalse(publicValue.get(field).booleanValue());
        }
    }
    @Test void strictSourceIdentityAndNotificationFieldsRejectWithoutInventingCurrentBuildOrCause()throws Exception {
        var contract=SwayObservationReads.invalidationContract(SOURCE,QUERY,true);
        for(String defect:List.of("wrong-exe","wrong-build","wrong-actor","wrong-fullID","wrong-generation","bool-sequence","float-sequence","replayed-cursor","missing","null","unknown-branch","scope","join","material","command","frame")) {
            var packet=vector("dead");var result=(ObjectNode)packet.get("result");var body=(ObjectNode)result.get("sway_completion_invalidation_reason");var row=(ObjectNode)body.at("/records/0");
            switch(defect) {
                case "wrong-exe"->result.put("executable_sha256","0".repeat(64));case "wrong-build"->result.put("build_version","1.20.0.4");
                case "wrong-actor"->row.put("actor_character_id",ACTOR+1);case "wrong-fullID"->row.put("scheme_instance_id",ID+1);case "wrong-generation"->row.put("scheme_instance_generation",3);
                case "bool-sequence"->row.put("sequence",true);case "float-sequence"->row.put("sequence",1.0);case "replayed-cursor"->row.put("sequence",0);
                case "missing"->body.remove("session_records_only");case "null"->body.putNull("observer_attached");case "unknown-branch"->row.put("source_branch","cause_inferred_from_enum");
                case "scope"->row.put("root_scope_kind",true);case "join"->row.put("exact_scope_join_ready",false);case "material"->body.put("material_effect_observed",true);
                case "command"->row.put("authored_command","send_notification");case "frame"->result.put("snapshot_revision",8);default->throw new AssertionError(defect);
            }
            assertThrows(IllegalArgumentException.class,()->contract.decode(receipt(contract,request(contract,"1.20.0.2",QUERY),packet)),defect);
        }
        assertThrows(IllegalArgumentException.class,()->contract.prepare(request(contract,"1.20.0.5",QUERY),"software-unsupported"));
        var disabled=SwayObservationReads.invalidationContract(SOURCE,QUERY,false);
        assertThrows(IllegalArgumentException.class,()->disabled.prepare(request(disabled,"1.20.0.2",QUERY),"software-disabled"));
        var old3=vector("dead");((ObjectNode)old3.get("result")).put("build_version","1.20.0.3").put("executable_sha256","94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6");
        assertEquals("1.20.0.3",StrictJson.parse(contract.decode(receipt(contract,request(contract,"1.20.0.3",QUERY),old3)).normalized().bytes()).get("exact_ck3_build").textValue());
        var unavailable=vector("dead");var envelope=(ObjectNode)unavailable.get("result");envelope.put("status","unavailable");
        var body=(ObjectNode)envelope.get("sway_completion_invalidation_reason");body.put("available",false).put("observer_attached",false).put("unavailable_reason","observer_not_attached").put("earliest_sequence",0).put("latest_sequence",0);body.putArray("records");
        assertFalse(StrictJson.parse(contract.decode(receipt(contract,request(contract,"1.20.0.2",QUERY),unavailable)).normalized().bytes()).get("available").booleanValue());
    }
    @Test void exactPublicDecimalCursorRoundTripsAndNativeNonzeroCursorDoesNotReplayARecord()throws Exception {
        var publicRequest=new SwayPublicCodec.InvalidationRequest(StrictJson.UINT64_MAX,TARGET,ID,StrictJson.UINT64_MAX);
        assertEquals(publicRequest,SwayPublicCodec.decodeInvalidation(SwayPublicCodec.encodeInvalidationRequest(publicRequest)));
        var missing=raw("{\"expected_revision\":1,\"target_character_id\":67108866,\"scheme_instance_id\":33554443}");assertEquals(BigInteger.ZERO,SwayPublicCodec.decodeInvalidation(missing).afterSequence());
        for(String token:List.of("null","true","1.0","9007199254740993","\"01\"","\"18446744073709551616\"","\"1\\n\""))
            assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeInvalidation(raw("{\"expected_revision\":1,\"target_character_id\":67108866,\"scheme_instance_id\":33554443,\"after_sequence\":"+token+"}")));
        var query=new SwayObservationReads.InvalidationQuery(QUERY.subject(),BigInteger.ONE);var contract=SwayObservationReads.invalidationContract(SOURCE,query,true);var request=request(contract,"1.20.0.2",query);
        assertEquals(BigInteger.ONE,StrictJson.parse(contract.prepare(request,"cursor").additionalFields().bytes()).get("after_sequence").bigIntegerValue());
        var packet=vector("dead");((ObjectNode)packet.at("/result/sway_completion_invalidation_reason")).put("after_sequence",1);
        assertThrows(IllegalArgumentException.class,()->contract.decode(receipt(contract,request,packet)));
        ((ObjectNode)packet.at("/result/sway_completion_invalidation_reason")).putArray("records");
        var read=contract.decode(receipt(contract,request,packet));assertEquals("1",StrictJson.parse(SwayPublicCodec.publicNormalized(read).bytes()).get("after_sequence").textValue());
    }
    private static PlanningReadRequest request(ReadContract<?> contract,String version,SwayObservationReads.InvalidationQuery query) {
        var binding=SwayNativeFormalTest.binding(73,7,53220000);return new PlanningReadRequest(binding.before(),new G2Source(binding.before().machineId(),NOW.toString(),version,SOURCE),binding.sessionId(),contract.operation(),SwayObservationReads.arguments(query),NOW.plusSeconds(30));
    }
    private static PlanningReadReceipt receipt(ReadContract<?> contract,PlanningReadRequest request,ObjectNode packet) {
        String id=packet.get("request_id").textValue();var binding=SwayNativeFormalTest.binding(73,7,53220000);
        var evidence=new GuardEvidence(request.before(),request.source(),request.sessionId(),binding.connectionGeneration(),contract.operation(),SOURCE,SOURCE,binding.authorityId(),NOW,NOW.plusSeconds(30));
        var guard=new PlanningReadGuard(evidence,true,true,true,"b".repeat(64));byte[] bytes=StrictJson.canonical(packet,SwayNativeWire.MAX);
        byte[] framed=java.nio.ByteBuffer.allocate(bytes.length+4).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).put(bytes).array();
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(StrictJson.canonical(packet.get("result"),SwayNativeWire.MAX))),new RawJson(bytes),framed);
        return new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack);
    }
    private static ObjectNode vector(String role)throws Exception {
        Path path=Path.of(required("xar.repository.root")).resolve("ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_sway_completion_invalidation_reason/"+role+"-command-result.json");byte[] bytes=Files.readAllBytes(path);
        String sha=switch(role){case "dead"->"87c81e1e7d6e514157483b31adc58feaa217be2a5b6054baa3e41eceaed3be01";case "range"->"3cb14b6ee64a3acf652bb60c6fc95909f88cc6a92a164a535e0df557ddd5e577";case "opaque"->"07fbb106c9e10ec8e0a0e69681653401a2f60892f6c141a988e509e8566e7152";default->throw new AssertionError(role);};
        assertEquals(sha,ActionCodec.sha256(bytes));
        // Repository transport fixtures use LF. Their historical native emitter evidence pins CRLF.
        // Verify that one explicit line-ending projection; it grants no fresh native custody or Game readiness.
        assertEquals(10,bytes[bytes.length-1]);var nativeLine=java.util.Arrays.copyOf(bytes,bytes.length+1);nativeLine[bytes.length-1]=13;nativeLine[bytes.length]=10;
        String emitted=switch(role){case "dead"->"a1081d269c5215823759de81fdde8e4d0a51f99b1e24c86d35b7ccec0e4b1156";case "range"->"6f91164567eca32c4fbe24c1289f58f2a4a6dc4e4157518c49733c6799985ff3";case "opaque"->"e2150cae9984955dc9ae8ece422072dc2b926152bdbe4fdd6356374fc31897e5";default->throw new AssertionError(role);};
        assertEquals(emitted,ActionCodec.sha256(nativeLine));return (ObjectNode)StrictJson.parse(bytes,SwayNativeWire.MAX);
    }
    private JsonNode oracle(String role,ObjectNode packet)throws Exception {
        String script="""
            import hashlib,json,pathlib,sys
            root=pathlib.Path(sys.argv[1]);path=root/'ck3_autonomous_player/src/xar_autoplayer/bridge/active_scheme_sway_completion_invalidation_reason_private_transport.py'
            assert hashlib.sha256(path.read_bytes()).hexdigest()=='1a1fbe48cc10afb96dc8d11cf73a758e0cc53bc2ba72e230e9a0168d1a94c0c9'
            sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge.active_scheme_sway_completion_invalidation_reason_private_transport import normalize_active_scheme_sway_completion_invalidation_reason_v1
            v=json.loads(sys.argv[2]);snapshot={'played_character':{'character_id':50331649}}
            print(json.dumps(normalize_active_scheme_sway_completion_invalidation_reason_v1(v,snapshot=snapshot,target_character_id=67108866,scheme_instance_id=33554443,after_sequence=v['after_sequence']),separators=(',',':'),sort_keys=True))
            """;
        Path repo=Path.of(required("xar.repository.root")),python=Path.of(required("xar.python")),output=temp.resolve(role+"-original.log"),error=temp.resolve(role+"-original.err");
        var spec=new WindowsJobProcess.CommandSpec(python,List.of("-B","-c",script,repo.toString(),packet.at("/result/sway_completion_invalidation_reason").toString()),repo,
                CanonicalOracleEnvironment.bind(repo,python,System.getenv()),output,error,128L<<20);
        Instant deadline=Instant.now().plusSeconds(30);WindowsJobProcess.CommandResult terminal;
        try(var child=WindowsJobProcess.start(spec)){terminal=child.await(Duration.ofSeconds(30),deadline,()->{boundedOriginalOutput(output);boundedOriginalOutput(error);});}
        assertTrue(terminal.passed(),"actual original normalizer Job must naturally pass: "+terminal);assertTrue(Files.size(output)<=65536);
        return StrictJson.parse(Files.readAllBytes(output),65536);
    }
    private static void boundedOriginalOutput(Path output) {
        try{if(Files.exists(output)&&Files.size(output)>65536)throw new java.io.IOException("bounded original normalizer output exceeded");}
        catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
    }
    private static String required(String name){String value=System.getProperty(name);assertNotNull(value,"mandatory CI input missing: "+name);assertFalse(value.isBlank());return value;}
    private static RawJson raw(String value){return new RawJson(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
}
