package org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionContract;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContext;
import org.xar.ck3.control.nativebridge.capabilities.religion.ReligionConversionRead;
import org.xar.ck3.control.nativebridge.capabilities.religion.ReligionConversionActions;
import static org.junit.jupiter.api.Assertions.*;

/** Original Python transports/normalizers are mandatory software oracles; this test grants no Root/native authority. */
final class ReligionConversionCountyPythonParityTest {
    private static final int MAX_ORACLE_BYTES=1<<20;
    private static ObjectNode corpus;
    @Test void thirtyOneOriginalPacketsMatchTheEntireOriginalPublicResponse()throws Exception {
        var kinds=new HashSet<String>();int count=0;
        for(JsonNode row:oracle().get("reads"))if(row.get("provenance").textValue().equals("original_packet")) {
            compareRead(row);kinds.add(row.get("kind").textValue());count++;
        }
        assertEquals(31,count);assertEquals(Set.of("choices","inputs","terms","reasons","outcome"),kinds);
    }
    @Test void declaredFullWidthAndNullableRolesSurviveOriginalNormalizerToPublicSerde()throws Exception {
        int count=0;
        for(JsonNode row:oracle().get("reads"))if(row.get("provenance").textValue().equals("software_boundary")) {compareRead(row);count++;}
        assertEquals(10,count,"five full-width, three sentinel and two fervor boundary cases required");
    }
    @Test void malformedNativeTokensAreRejectedByBothRealNormalizers()throws Exception {
        int count=0;
        for(JsonNode row:oracle().get("read_errors")) {
            assertTrue(row.get("python_rejected").booleanValue(),row.get("name").textValue());
            assertTrue(Set.of("BridgeUnavailableError","ValueError").contains(row.get("error_type").textValue()),"unexpected oracle fixture failure");
            assertThrows(IllegalArgumentException.class,()->normalize(row),row.get("name").textValue());count++;
        }
        assertEquals(25,count,"five malformed native token cases per READ method required");
    }
    @Test void strictPublicArgumentsRoundTripAndKeepNativeAndPublicIntegerDomainsSeparate()throws Exception {
        var seen=new HashSet<String>();
        for(JsonNode row:oracle().get("reads")) {
            String method=kind(row).method();ObjectNode input=object(row.get("public_arguments")).deepCopy();
            var request=ReligionCodec.decode(method,raw(input));var encoded=ReligionCodec.encode(request);
            assertEquals(request,ReligionCodec.decode(method,encoded),row.get("name").textValue());
            assertTrue(object(encoded).get("expected_revision").isTextual());
            assertTrue(ReligionCodec.nativeArguments(request).get("expected_revision").isIntegralNumber());
            if(kind(row)!=ReligionConversionRead.Kind.CHOICES)assertEquals(input.get("target_rite_id"),ReligionCodec.nativeArguments(request).get("target_rite_id"));
            seen.add(method);
        }
        assertEquals(5,seen.size());
        String name=ReligionConversionRead.Kind.TERMS.method();
        for(String token:List.of("true","1.0","null","-1","4294967296"))
            assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(name,raw("{\"expected_revision\":\"1\",\"target_rite_id\":"+token+"}")));
        for(String token:List.of("true","1.0","null","\"01\"","\"18446744073709551616\"","9007199254740992"))
            assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(name,raw("{\"expected_revision\":"+token+",\"target_rite_id\":1}")));
        for(String text:List.of("{}","{\"expected_revision\":\"1\"}","{\"expected_revision\":\"1\",\"target_rite_id\":1,\"alias\":false}"))
            assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(name,raw(text)));
        assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(ReligionConversionRead.Kind.OUTCOME.method(),raw("{\"expected_revision\":\"1\",\"target_rite_id\":4294967295}")),"OUTCOME retains its complete-reference upper bound");
    }
    @Test void originalConversionAndCountySubmissionResponsesMatchAllStatusesWithoutMaterialCredit()throws Exception {
        var methods=new HashSet<String>();var statuses=new HashSet<String>();int count=0;
        for(JsonNode row:oracle().get("actions")) {
            var kind=actionKind(row);var submission=normalizeAction(row);ObjectNode actual=ReligionConversionActions.presentSubmission(submission);
            ObjectNode expected=publicActionOracle(kind,object(row.get("python_response")));
            assertEquals(expected,object(raw(actual)),row.get("name").textValue()+": entire original action response differs");
            assertEquals(row.get("envelope").get("submission"),object(submission.originalOwner()),"original complete owner was rewritten");
            assertFalse(actual.get("material_result").booleanValue());assertFalse(actual.get("automatic_retry").booleanValue());
            if(kind==ReligionConversionActions.Kind.COUNTY){assertFalse(actual.get("task_assignment_material_observed").booleanValue());assertFalse(actual.get("county_conversion_completed").booleanValue());}
            var response=new ReligionContract.Response(ReligionCodec.method(kind.method()),raw(actual));assertEquals(expected,object(ReligionCodec.encode(response)));
            ObjectNode publicArgs=object(row.get("intent")).deepCopy();decimalAt(publicArgs,"expected_revision");
            if(kind==ReligionConversionActions.Kind.CONVERSION)decimalAt(publicArgs,"max_piety_cost_raw");
            var request=ReligionCodec.decode(kind.method(),raw(publicArgs));assertEquals(request,ReligionCodec.decode(kind.method(),ReligionCodec.encode(request)));
            assertEquals(row.get("intent"),ReligionCodec.nativeArguments(request));
            assertEquals(1,row.get("native_sends").intValue());assertEquals(row.get("request_id").textValue(),row.get("request").get("request_id").textValue());
            assertEquals(row.get("snapshot").get("native_revision"),row.get("request").get("expected_snapshot_revision"));
            methods.add(kind.method());statuses.add(row.get("python_response").get("status").textValue());count++;
        }
        assertEquals(Set.of("ck3_convert_player_religion_private_v1","ck3_submit_county_conversion_task"),methods);
        assertTrue(statuses.containsAll(Set.of("rejected_before_submit","noop_preexisting_target_match","submitted_verification_pending","not_submitted","already_active_noop","queued_verification_pending")));
        assertEquals(12,count,"nine original status/build combinations plus three explicit software boundary cases required");
    }
    @Test void malformedActionOwnersFailAtTheSameOriginalBoundary()throws Exception {
        int count=0;
        for(JsonNode row:oracle().get("action_errors")) {
            assertTrue(row.get("python_rejected").booleanValue(),row.get("name").textValue());
            assertTrue(Set.of("BridgeUnavailableError","ValueError").contains(row.get("error_type").textValue()),"unexpected action oracle fixture failure");
            assertThrows(IllegalArgumentException.class,()->normalizeAction(row),row.get("name").textValue());count++;
        }
        assertEquals(10,count);
        String convert="ck3_convert_player_religion_private_v1";
        for(String token:List.of("true","1.0","-1","4294967295"))assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(convert,raw("{\"expected_revision\":\"1\",\"target_rite_id\":"+token+",\"max_piety_cost_raw\":\"0\",\"action_id\":\"a\"}")));
        assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(convert,raw("{\"expected_revision\":\"1\",\"target_rite_id\":1,\"max_piety_cost_raw\":\"9223372036854775808\",\"action_id\":\"a\"}")));
        String county="ck3_submit_county_conversion_task";
        for(String token:List.of("0","1","\"false\"","null"))assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(county,raw("{\"expected_revision\":\"1\",\"expected_active_task_id\":17,\"expected_incumbent_character_id\":29,\"province_id\":42,\"replace_existing_task\":"+token+",\"action_id\":\"a\"}")));
    }
    /** Intentional Java model repair. Original generic public-snapshot parser rejects negative actors. */
    @Test void signedActorModelRepairIsSeparateFromTheOriginalPythonPublicBoundary()throws Exception {
        int oldBoundary=0;
        for(JsonNode row:oracle().get("python_actor_boundary")) {
            JsonNode value=row.get("value");boolean rejected=value.isBoolean()||value.bigIntegerValue().signum()<0;
            assertEquals(rejected,row.get("rejected").booleanValue(),"actual original generic actor guard changed");oldBoundary++;
        }
        assertEquals(6,oldBoundary);
        BigInteger signed=BigInteger.valueOf(Integer.MIN_VALUE);int reads=0;
        for(JsonNode row:oracle().get("reads")) {
            String chosen=switch(kind(row)){case CHOICES->"choices/choices";case INPUTS->"inputs/signed-prediction";case TERMS->"terms/permitted";case REASONS->"reasons/native-allowed-with-text";case OUTCOME->"outcome/current";};
            if(!row.get("name").textValue().equals(chosen))continue;
            ObjectNode repaired=withModelActor(row,signed);var view=normalize(repaired);assertEquals(signed,view.source().actor());
            assertEquals(repaired.get("native"),object(view.nativeData()),"signed native model must not become unsigned");
            JsonNode snapshot=repaired.get("snapshot");var build=PlayerReligionContext.Build.exact(snapshot.path("diagnostics").path("hello").get("expected_ck3_version").textValue(),snapshot.path("diagnostics").path("hello").get("expected_ck3_sha256").textValue());
            ObjectNode publicModel=ReligionConversionRead.present(view,build,snapshot.get("snapshot_id").textValue(),snapshot.get("revision").bigIntegerValue(),snapshot.get("native_revision").bigIntegerValue(),object(repaired.get("envelope")));
            assertEquals(signed,publicModel.get("played_character_id").bigIntegerValue());
            assertEquals(object(raw(publicModel)),object(ReligionCodec.encode(new ReligionContract.Response(ReligionCodec.method(kind(row).method()),raw(publicModel)))));reads++;
        }
        assertEquals(5,reads,"all five Java read models must preserve signed actor identity");
        int county=0,conversion=0;
        for(JsonNode row:oracle().get("actions"))if(row.get("name").textValue().endsWith("/queued_verification_pending/None")) {
            ObjectNode repaired=withModelActor(row,signed);
            if(actionKind(row)==ReligionConversionActions.Kind.COUNTY) {
                ObjectNode result=ReligionConversionActions.presentSubmission(normalizeAction(repaired));
                assertEquals(signed,result.get("player_character_id").bigIntegerValue());assertFalse(result.get("material_result").booleanValue());county++;
            }else {assertThrows(IllegalArgumentException.class,()->normalizeAction(repaired),"conversion retains its original private positive actor guard");conversion++;}
        }
        assertEquals(2,county);assertEquals(1,conversion);
    }
    @Test void nativeActorFrameEnforcesSignedI32AndTheAbsentSentinel()throws Exception {
        var build=PlayerReligionContext.Build.CROZIER3;
        for(BigInteger actor:List.of(BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.ZERO,BigInteger.valueOf(Integer.MAX_VALUE)))assertEquals(actor,new ReligionConversionRead.BoundFrame(build,BigInteger.ZERO,actor).player());
        for(BigInteger actor:List.of(BigInteger.valueOf(-1),BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE),BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE)))assertThrows(IllegalArgumentException.class,()->new ReligionConversionRead.BoundFrame(build,BigInteger.ZERO,actor));
    }
    private static ObjectNode withModelActor(JsonNode original,BigInteger actor) {
        ObjectNode row=object(original).deepCopy();object(object(row.get("snapshot")).get("played_character")).put("character_id",actor);
        for(String field:List.of("native","envelope"))if(row.has(field))replaceModelActor(row.get(field),actor);
        if(row.has("native"))row.put("native_json",new String(raw(row.get("native")).bytes(),StandardCharsets.UTF_8));
        if(row.has("envelope"))row.put("envelope_json",new String(raw(row.get("envelope")).bytes(),StandardCharsets.UTF_8));
        return row;
    }
    private static void replaceModelActor(JsonNode value,BigInteger actor) {
        if(value instanceof ObjectNode object){for(String role:List.of("played_character_id","owner_character_id"))if(object.has(role))object.put(role,actor);}
        if(value.isContainerNode())for(JsonNode child:value)replaceModelActor(child,actor);
    }
    private static ReligionConversionActions.Kind actionKind(JsonNode row){return ReligionConversionActions.Kind.valueOf(row.get("action_kind").textValue());}
    private static ReligionConversionActions.Submission normalizeAction(JsonNode row) {
        JsonNode snapshot=row.get("snapshot"),hello=snapshot.path("diagnostics").path("hello");
        var build=PlayerReligionContext.Build.exact(hello.get("expected_ck3_version").textValue(),hello.get("expected_ck3_sha256").textValue());
        var frame=new ReligionConversionRead.BoundFrame(build,snapshot.get("date_raw").bigIntegerValue(),snapshot.path("played_character").get("character_id").bigIntegerValue());
        return ReligionConversionActions.normalizeSubmission(actionKind(row),raw(row.get("envelope_json").textValue()),frame,snapshot.get("revision").bigIntegerValue(),snapshot.get("native_revision").bigIntegerValue(),row.get("request_id").textValue(),raw(row.get("intent")));
    }
    private static ObjectNode publicActionOracle(ReligionConversionActions.Kind kind,ObjectNode original) {
        ObjectNode result=original.deepCopy();
        for(String field:List.of("owner_submission.native_revision","owner_submission.capture_epoch","owner_submission.request.expected_revision"))decimalAt(result,field);
        if(kind==ReligionConversionActions.Kind.CONVERSION) {
            for(String field:List.of("max_piety_cost_raw","quoted_base_piety_cost_raw","owner_submission.request.max_piety_cost_raw"))decimalAt(result,field);
            for(String field:List.of("before_outcome","paid_terms"))if(result.get(field).isObject())result.set(field,publicNativeDataOracle(field.equals("before_outcome")?ReligionConversionRead.Kind.OUTCOME:ReligionConversionRead.Kind.TERMS,object(result.get(field))));
            ObjectNode owner=object(result.get("owner_submission"));
            if(owner.hasNonNull("before"))owner.set("before",publicNativeDataOracle(ReligionConversionRead.Kind.OUTCOME,object(owner.get("before"))));
            if(owner.hasNonNull("paid_terms"))owner.set("paid_terms",publicNativeDataOracle(ReligionConversionRead.Kind.TERMS,object(owner.get("paid_terms"))));
            for(String field:List.of("native_reasons","owner_submission.native_reasons")) {
                JsonNode selected=field.contains(".")?owner.get("native_reasons"):result.get("native_reasons");if(selected!=null&&selected.isObject())decimalAt(result,field+".capture_epoch");
            }
        }else for(String prefix:List.of("before_task","owner_submission.before"))for(String field:List.of("capture_epoch","percentage_progress_raw"))decimalAt(result,prefix+"."+field);
        return result;
    }
    private static ReligionConversionRead.View normalize(JsonNode row) {
        ObjectNode snapshot=object(row.get("snapshot"));JsonNode hello=snapshot.path("diagnostics").path("hello");
        var build=PlayerReligionContext.Build.exact(hello.get("expected_ck3_version").textValue(),hello.get("expected_ck3_sha256").textValue());
        var frame=new ReligionConversionRead.BoundFrame(build,snapshot.get("date_raw").bigIntegerValue(),snapshot.path("played_character").get("character_id").bigIntegerValue());
        BigInteger target=kind(row)==ReligionConversionRead.Kind.CHOICES?null:row.get("public_arguments").get("target_rite_id").bigIntegerValue();
        return ReligionConversionRead.normalize(kind(row),raw(row.get("native_json").textValue()),frame,target);
    }
    private static void compareRead(JsonNode row) {
        String name=row.get("name").textValue();var view=normalize(row);ObjectNode snapshot=object(row.get("snapshot"));
        assertEquals(row.get("native"),object(view.nativeData()),name+": original native subtree changed");
        assertFalse(row.get("python_response").has("material_result"),name+": readonly query gained action credit");
        var build=PlayerReligionContext.Build.exact(snapshot.path("diagnostics").path("hello").get("expected_ck3_version").textValue(),snapshot.path("diagnostics").path("hello").get("expected_ck3_sha256").textValue());
        ObjectNode actual=ReligionConversionRead.present(view,build,snapshot.get("snapshot_id").textValue(),snapshot.get("revision").bigIntegerValue(),snapshot.get("native_revision").bigIntegerValue(),object(row.get("envelope")));
        ObjectNode expected=publicReadOracle(kind(row),object(row.get("python_response")));
        assertEquals(expected,object(raw(actual)),name+": full response differs from original Python producer");
        var response=new ReligionContract.Response(ReligionCodec.method(kind(row).method()),raw(actual));
        assertEquals(expected,object(ReligionCodec.encode(response)),name+": public serialization changed a role or extra field");
        assertEquals(1,row.get("native_sends").intValue());assertTrue(row.get("request").get("expected_revision").isIntegralNumber());
        assertEquals(snapshot.get("native_revision"),row.get("request").get("expected_revision"));
        assertEquals(snapshot.get("native_revision"),row.get("request").get("expected_snapshot_revision"));
    }
    /** Independent public-role contract applied to the original complete Python response; no Java producer output is used. */
    private static ObjectNode publicReadOracle(ReligionConversionRead.Kind kind,ObjectNode python) {
        ObjectNode result=publicNativeDataOracle(kind,python);
        for(String field:List.of("queried_revision","queried_native_revision","snapshot_revision"))decimalAt(result,field);
        return result;
    }
    private static ObjectNode publicNativeDataOracle(ReligionConversionRead.Kind kind,ObjectNode python) {
        ObjectNode result=python.deepCopy();var paths=new ArrayList<String>(List.of("capture_epoch"));
        switch(kind) {
            case CHOICES->paths.addAll(List.of("faith_choices.capture_epoch","current_faith_rites.capture_epoch"));
            case INPUTS->{paths.addAll(List.of("conversion_gates.capture_epoch","conversion_gates.knowledge_level_raw","predicted_base_fulfillment.capture_epoch","predicted_base_fulfillment.current_rite_base_raw","predicted_base_fulfillment.target_rite_base_raw","predicted_base_fulfillment.expected_base_change_raw"));
                if(result.has("conversion_fervor"))paths.addAll(List.of("conversion_fervor.capture_epoch","conversion_fervor.actor_fervor_raw","conversion_fervor.target_fervor_raw"));}
            case TERMS->paths.addAll(List.of("final_gate.capture_epoch","cost.capture_epoch","cost.piety_cost_raw","cost.actor_piety_raw"));
            case REASONS->{ }
            case OUTCOME->{paths.addAll(List.of("actor.capture_epoch","state.capture_epoch","actor.current_religion.capture_epoch","actor.piety_raw","actor.gold_raw","actor.prestige_raw","actor.current_religion.faith_fervor_raw","actor.current_religion.spiritual_fulfillment_raw","state.knowledge_level_raw","state.spiritual_fulfillment_raw","state.baseline_spiritual_fulfillment_raw"));
                for(String flag:List.of("faith_conversion_recently_converted","conversion_memory_recently_created","recent_convert"))paths.add("state."+flag+".remaining_updates");}
        }
        for(String path:paths)decimalAt(result,path);return result;
    }
    private static void decimalAt(ObjectNode object,String path) {
        String[] parts=path.split("\\.");ObjectNode parent=object;
        for(int index=0;index<parts.length-1;index++)parent=object(parent.get(parts[index]));
        JsonNode n=parent.get(parts[parts.length-1]);assertNotNull(n,"declared original Python role missing: "+path);
        if(!n.isNull()){assertTrue(n.isIntegralNumber(),"actual original integer required: "+path);parent.put(parts[parts.length-1],n.bigIntegerValue().toString());}
    }
    private static ReligionConversionRead.Kind kind(JsonNode row){return ReligionConversionRead.Kind.valueOf(row.get("kind").textValue().toUpperCase(java.util.Locale.ROOT));}
    private static ObjectNode object(JsonNode n){assertInstanceOf(ObjectNode.class,n);return (ObjectNode)n;}
    private static ObjectNode object(RawJson n){return object(StrictJson.parse(n.bytes(),StrictJson.EXPLICIT_MAX_BYTES));}
    private static RawJson raw(JsonNode n){return new RawJson(StrictJson.canonical(n,StrictJson.EXPLICIT_MAX_BYTES));}
    private static RawJson raw(String n){return new RawJson(n.getBytes(StandardCharsets.UTF_8));}
    private static synchronized ObjectNode oracle()throws Exception {
        if(corpus!=null)return corpus;
        String python=System.getProperty("xar.python"),repository=System.getProperty("xar.repository.root");
        assertNotNull(python,"NOT_RUN_REQUIRED: xar.python original oracle fixture must be supplied");assertFalse(python.isBlank());
        assertNotNull(repository,"NOT_RUN_REQUIRED: original source repository fixture must be supplied");assertFalse(repository.isBlank());repository=Path.of(repository).toRealPath().toString();
        requireOriginalInputs(Path.of(repository));
        ProcessBuilder builder=new ProcessBuilder(python,"-c",ORACLE).directory(Path.of(repository).toFile()).redirectErrorStream(true);
        builder.environment().put("XAR_SOURCE_REPOSITORY",repository);builder.environment().put("PYTHONPATH",Path.of(repository).resolve("ck3_autonomous_player/src").toString());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        Process process=builder.start();var output=new CompletableFuture<byte[]>();Thread reader=Thread.ofVirtual().start(()->{try{output.complete(process.getInputStream().readNBytes(MAX_ORACLE_BYTES+1));}catch(java.io.IOException failure){output.completeExceptionally(failure);}});process.getOutputStream().close();
        try{assertTrue(process.waitFor(45,TimeUnit.SECONDS),"original Religion oracle timeout");byte[] bytes=output.get(5,TimeUnit.SECONDS);assertEquals(0,process.exitValue(),new String(bytes,StandardCharsets.UTF_8));assertTrue(bytes.length<=MAX_ORACLE_BYTES,"bounded complete original oracle response required");
            requireOriginalInputs(Path.of(repository));corpus=object(StrictJson.parse(bytes,MAX_ORACLE_BYTES));assertEquals("original-python-religion-conversion-county-oracle/v2",corpus.get("schema").textValue());return corpus;}
        finally{if(process.isAlive()){process.destroyForcibly();assertTrue(process.waitFor(5,TimeUnit.SECONDS),"oracle child did not terminate");}reader.join(5000);}
    }
    /** Pins the declared original oracle modules and all 31 packets; hashes establish fixture custody only. */
    private static void requireOriginalInputs(Path repository)throws Exception {
        var paths=new ArrayList<String>();
        for(String module:("player_religion_conversion_choices_private_transport,player_religion_conversion_inputs_private_transport,player_religion_conversion_terms_private_transport,player_religion_conversion_reasons_private_transport,player_religion_conversion_outcome_private_transport,player_religion_conversion_private_action_v1,county_conversion_task_private_action_v1,player_conversion_fervor_inputs,player_religion_context_private_transport,nonwar_private_build,g2_private_query_transport,version_identity,timeline_blocker_private_transport,native_driver").split(","))
            paths.add("ck3_autonomous_player/src/xar_autoplayer/bridge/"+module+".py");
        for(String kind:List.of("choices","inputs","terms","reasons","outcome")) {
            Path directory=repository.resolve("ck3_autonomous_player/tests/fixtures/native_12002/religion_conversion_"+kind);
            try(var files=Files.list(directory)){files.filter(path->path.getFileName().toString().endsWith(".json")).forEach(path->paths.add(repository.relativize(path).toString().replace('\\','/')));}
        }
        assertEquals(45,paths.size(),"14 declared original modules and 31 original packets required");paths.sort(String::compareTo);
        MessageDigest aggregate=MessageDigest.getInstance("SHA-256");aggregate.update("original-religion-oracle-inputs/v1\n".getBytes(StandardCharsets.UTF_8));long total=0;
        for(String relative:paths) {
            Path file=repository.resolve(relative);assertTrue(Files.isRegularFile(file,LinkOption.NOFOLLOW_LINKS),"plain original fixture required: "+relative);
            byte[] bytes;try(var input=Files.newInputStream(file)){bytes=input.readNBytes(4*1024*1024+1);}total+=bytes.length;
            assertTrue(bytes.length>0&&total<=4*1024*1024,"bounded original fixture set required");
            String digest=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
            aggregate.update((relative+"\0"+bytes.length+"\0"+digest+"\n").getBytes(StandardCharsets.UTF_8));
        }
        assertEquals(1835431,total,"original source/packet set length changed");
        assertEquals("a283ba98bc9e4bff437cb04f5d319f007014035fb3c539b49b7dd37f129845b0",HexFormat.of().formatHex(aggregate.digest()),"original oracle source or packets changed");
    }
    private static final String ORACLE="""
        import copy,importlib,json,os,pathlib,sys
        root=pathlib.Path(os.environ['XAR_SOURCE_REPOSITORY']).resolve(strict=True)
        sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
        from xar_autoplayer.bridge.native_driver import NativeProtocolState
        from xar_autoplayer.bridge.version_identity import CK3_12002,CK3_12003,CK3_12004
        kinds=['choices','inputs','terms','reasons','outcome']
        modules={k:importlib.import_module('xar_autoplayer.bridge.player_religion_conversion_'+k+'_private_transport') for k in kinds}
        fixtures=root/'ck3_autonomous_player/tests/fixtures/native_12002'
        class Driver:
            command_timeout_seconds=1
            def __init__(self,kind,packet,snapshot):
                self.kind=kind;self.packet=copy.deepcopy(packet);self.snapshot=copy.deepcopy(snapshot);self.sent=[];self.endpoint=self
                setattr(self,modules[kind].PERMISSION,True)
                self.state=NativeProtocolState('software-original-religion-parity-'+kind)
                hello=self.snapshot['diagnostics']['hello']
                self.state.ingest(dict(type='hello',protocol_version=1,pid=101,capabilities=[],expected_ck3_version=hello['expected_ck3_version'],expected_ck3_sha256=hello['expected_ck3_sha256']))
            def take_snapshot(self):return copy.deepcopy(self.snapshot)
            def send(self,request):
                self.sent.append(copy.deepcopy(request));packet=copy.deepcopy(self.packet);packet['request_id']=request['request_id'];self.state.ingest(packet)
        def snapshot(packet):
            env=packet['result'];value=env['player_religion_conversion_'+next(k for k in kinds if 'player_religion_conversion_'+k in env)]
            return dict(snapshot_id='software-native:'+str(env['snapshot_revision']),revision=env['snapshot_revision']+4,native_revision=env['snapshot_revision'],date_raw=env['date_raw'],played_character=dict(character_id=value['played_character_id'],alive=True),paused=True,map_ready=True,diagnostics=dict(hello=dict(expected_ck3_version=env['game_version'],expected_ck3_sha256=env['executable_sha256'])))
        def run(kind,name,packet,before,provenance):
            driver=Driver(kind,packet,before);args=dict(expected_revision=before['revision']);native=packet['result']['player_religion_conversion_'+kind]
            if kind!='choices':args['target_rite_id']=native['target_rite_id']
            row=dict(name=name,kind=kind,provenance=provenance,snapshot=before,native=native,native_json=json.dumps(native,separators=(',',':'),allow_nan=False),envelope=packet['result'],public_arguments=args)
            try:
                row['python_response']=getattr(modules[kind],'query_player_religion_conversion_'+kind+'_private_v1')(driver,**args)
                row.update(native_sends=len(driver.sent),request=driver.sent[0]);return row
            except Exception as error:
                row.update(python_rejected=True,error_type=type(error).__name__,error=str(error));return row
        def walk(value,fn):
            if isinstance(value,dict):
                fn(value)
                for child in value.values():walk(child,fn)
            elif isinstance(value,list):
                for child in value:walk(child,fn)
        def rebind(packet,build):
            packet=copy.deepcopy(packet)
            def update(node):
                if 'schema' in node and isinstance(node['schema'],str):node['schema']=node['schema'].replace('ck3_12002_','ck3_'+build.game_version.replace('.','')+'_')
                if 'game_version' in node:node['game_version']=build.game_version
                if 'executable_sha256' in node:node['executable_sha256']=build.executable_sha256
                if 'backend_id' in node:node['backend_id']=node['backend_id'].replace('1.20.0.2',build.game_version)
            walk(packet,update);return packet
        reads=[];errors=[];original_packets={}
        for kind in kinds:
            paths=sorted((fixtures/('religion_conversion_'+kind)).glob('*.json'))
            assert len(paths)==dict(choices=5,inputs=6,terms=6,reasons=8,outcome=6)[kind]
            for path in paths:
                packet=json.loads(path.read_text(encoding='utf-8'));original_packets[(kind,path.stem)]=packet
                row=run(kind,kind+'/'+path.stem,packet,snapshot(packet),'original_packet');assert 'python_response' in row,row;reads.append(row)
        for kind,case in [('choices','choices'),('inputs','signed-prediction'),('terms','permitted'),('reasons','native-allowed-with-text'),('outcome','current')]:
            base=original_packets[(kind,case)]
            wide=copy.deepcopy(base)
            walk(wide,lambda n:n.update(capture_epoch=(1<<64)-1) if 'capture_epoch' in n else None)
            before=snapshot(wide);before['revision']=(1<<64)-1;before['native_revision']=(1<<64)-2;wide['result']['snapshot_revision']=before['native_revision']
            row=run(kind,kind+'/fullwidth',wide,before,'software_boundary');assert 'python_response' in row,row;reads.append(row)
            for label,mutate in [
                ('bool_epoch',lambda n:n.update(capture_epoch=True)),('float_epoch',lambda n:n.update(capture_epoch=3.0)),('null_epoch',lambda n:n.update(capture_epoch=None)),
                ('missing_source',lambda n:n.pop('unavailable_reason')),('extra_field',lambda n:n.update(unknown_alias=False))]:
                changed=copy.deepcopy(base);mutate(changed['result']['player_religion_conversion_'+kind]);row=run(kind,kind+'/'+label,changed,snapshot(base),'negative');assert row.get('python_rejected'),row;errors.append(row)
        for kind in ['inputs','terms','reasons']:
            case=dict(inputs='stale-target-generation',terms='target-unavailable',reasons='target-unavailable')[kind];packet=copy.deepcopy(original_packets[(kind,case)])
            native=packet['result']['player_religion_conversion_'+kind];old=native['target_rite_id']
            walk(native,lambda n:[n.update({key:0xffffffff}) for key in ['target_rite_id','requested_target_rite_id'] if n.get(key)==old])
            row=run(kind,kind+'/full-sentinel',packet,snapshot(packet),'software_boundary');assert 'python_response' in row,row;reads.append(row)
        for build in [CK3_12003,CK3_12004]:
            packet=rebind(original_packets[('inputs','signed-prediction')],build);native=packet['result']['player_religion_conversion_inputs'];g=native['conversion_gates']
            native['conversion_fervor']=dict(schema='ck3_'+build.game_version.replace('.','')+'_conversion_fervor_inputs_v1',read_only=True,available=True,unavailable_reason=None,capture_epoch=native['capture_epoch'],date_raw=native['date_raw'],played_character_id=native['played_character_id'],requested_target_rite_id=native['target_rite_id'],actor_faith_id=g['actor_faith_id'],target_faith_id=g['target_faith_id'],actor_fervor_raw=-(1<<63),target_fervor_raw=(1<<63)-1,raw_scale=100000,unit='fervor_points',is_final_conversion_cost=False,is_final_conversion_desire=False)
            row=run('inputs','inputs/software-fervor-'+build.game_version,packet,snapshot(packet),'software_boundary');assert 'python_response' in row,row;reads.append(row)
        from xar_autoplayer.bridge import player_religion_conversion_private_action_v1 as conversion
        from xar_autoplayer.bridge import county_conversion_task_private_action_v1 as county
        actions=[];action_errors=[]
        class ActionDriver:
            command_timeout_seconds=1
            def __init__(self,module,before,envelope,mutate):
                self.module=module;self.snapshot=copy.deepcopy(before);self.envelope=copy.deepcopy(envelope);self.mutate=mutate;self.sent=[];self.endpoint=self;self.delivered=None
                setattr(self,module.PERMISSION,True);hello=before['diagnostics']['hello'];self.state=NativeProtocolState('software-original-conversion-action')
                self.state.ingest(dict(type='hello',protocol_version=1,pid=101,capabilities=[],expected_ck3_version=hello['expected_ck3_version'],expected_ck3_sha256=hello['expected_ck3_sha256']))
            def take_snapshot(self):return copy.deepcopy(self.snapshot)
            def send(self,request):
                self.sent.append(copy.deepcopy(request));env=copy.deepcopy(self.envelope);env['submission']['request_id']=request['request_id']
                if self.mutate:self.mutate(env['submission'])
                self.delivered=dict(type='command_result',protocol_version=1,request_id=request['request_id'],ok=True,result=env);self.state.ingest(self.delivered)
        def action_case(kind,build,status,boundary=None,mutate=None):
            baseline_packet=rebind(original_packets[('outcome','current')],build);before=snapshot(baseline_packet);baseline=baseline_packet['result']['player_religion_conversion_outcome']
            paid=rebind(original_packets[('terms','permitted')],build)['result']['player_religion_conversion_terms']
            reasons=rebind(original_packets[('reasons','native-refusal-heap')],build)['result']['player_religion_conversion_reasons']
            epoch=baseline['capture_epoch'];target=baseline['target_rite_id'];queued=status=='queued_verification_pending'
            if boundary=='fullwidth':
                epoch=(1<<64)-1;before['revision']=(1<<64)-1;before['native_revision']=(1<<64)-2
                for component in [baseline,paid,reasons]:walk(component,lambda n:n.update(capture_epoch=epoch) if 'capture_epoch' in n else None)
            action_id='software-'+kind.lower()+'-'+status
            module=conversion if kind=='CONVERSION' else county
            if kind=='CONVERSION':
                walk(paid,lambda n:[n.update({k:target}) for k in ['target_rite_id','requested_target_rite_id'] if k in n]);reasons['target_rite_id']=target
                paid['final_gate']['current_faith_id']=baseline['actor']['current_religion']['faith_id']
                intent=dict(expected_revision=before['revision'],target_rite_id=target,max_piety_cost_raw=(1<<63)-1 if boundary else 40000000,action_id=action_id)
                if status=='already_target_noop':baseline['actor']['current_religion']['rite_id']=target;baseline['target_reached']=True
                if boundary=='negative_quote':paid['cost'].update(piety_points=-1,piety_cost_raw=-100000)
                retained_before=baseline;retained_paid=paid if queued else None
                if status=='not_submitted':
                    retained_paid=paid
                    for component in [retained_before,retained_paid,reasons]:
                        walk(component,lambda n:n.update(capture_epoch=0) if 'capture_epoch' in n else None)
                        walk(component,lambda n:n.update(available=False,unavailable_reason='not_sampled') if 'available' in n else None)
                    retained_paid['can_convert']=None;reasons.update(native_paid_validator_passes=None,native_blocker_text_available=False,raw_native_text=None,ui_blocker_text=None)
                owner=dict(request=intent,request_id='pending-nonce',native_revision=before['native_revision'],date_raw=before['date_raw'],capture_epoch=epoch,played_character_id=before['played_character']['character_id'],command_target_rite_id=target,command_pay_piety=True,command_channel=14,native_submit_copy_called=queued,status=status,before=retained_before,paid_terms=retained_paid,native_reasons=reasons,failure='native_final_denied' if status=='not_submitted' else None)
            else:
                intent=dict(expected_revision=before['revision'],expected_active_task_id=17,expected_incumbent_character_id=29,province_id=42,replace_existing_task=True,action_id=action_id)
                available=status!='not_submitted'
                task=dict(available=available,failure='' if available else 'not_sampled',capture_epoch=epoch if available else 0,date_raw=before['date_raw'],owner_character_id=before['played_character']['character_id'],task_key='task_conversion' if status=='already_active_noop' else 'task_collect_taxes',incumbent_character_id=29 if available else None,active_task_id=17 if available else None,target_province_id=42 if status=='already_active_noop' else None,target_county_title_id=-2147483648 if status=='already_active_noop' else None,target_scope_tag=8 if status=='already_active_noop' else None,progress_kind=1 if available else None,percentage_progress_raw=-(1<<63) if boundary else None)
                owner=dict(request=intent,request_id='pending-nonce',native_revision=before['native_revision'],date_raw=before['date_raw'],capture_epoch=epoch,played_character_id=before['played_character']['character_id'],command_channel=14,native_submit_copy_called=queued,status=status,failure='native_final_denied' if status=='not_submitted' else '',native_final_can_dispatch=queued,target_county_title_id=-2147483648 if available else None,before=task)
            owner['original_extension']=dict(label='preserve full owner, not only a DTO',unknown_boolean=False,unknown_rows=[None,7,'text'])
            envelope=dict(step=module.SUBMIT_STEP,accepted=True,private_build=True,advertised=False,read_only=False,backend_id='native-headless',game_version=build.game_version,executable_sha256=build.executable_sha256,snapshot_revision=before['native_revision'],public_revision=before['revision'],date_raw=before['date_raw'],capture_epoch=epoch,submission=owner)
            driver=ActionDriver(module,before,envelope,mutate);row=dict(name=kind+'/'+build.game_version+'/'+status+'/'+str(boundary),action_kind=kind,provenance='synthetic_memory_delivery_original_normalizer',snapshot=before,intent=intent)
            try:
                function=module.submit_player_religion_conversion_private_v1 if kind=='CONVERSION' else module.submit_county_conversion_task_private_v1
                row['python_response']=function(driver,**intent)
            except Exception as error:row.update(python_rejected=True,error_type=type(error).__name__,error=str(error))
            assert driver.delivered is not None,row
            row.update(native_sends=len(driver.sent),request=driver.sent[0],request_id=driver.sent[0]['request_id'],envelope=driver.delivered['result'],envelope_json=json.dumps(driver.delivered['result'],separators=(',',':'),allow_nan=False));return row
        for kind,builds,statuses in [('CONVERSION',[CK3_12003],['not_submitted','already_target_noop','queued_verification_pending']),('COUNTY',[CK3_12003,CK3_12004],['not_submitted','already_active_noop','queued_verification_pending'])]:
            for build in builds:
                for status in statuses:
                    row=action_case(kind,build,status);assert 'python_response' in row,row;actions.append(row)
        for kind,build,boundary in [('CONVERSION',CK3_12003,'fullwidth'),('COUNTY',CK3_12004,'fullwidth'),('CONVERSION',CK3_12003,'negative_quote')]:
            row=action_case(kind,build,'queued_verification_pending',boundary);assert 'python_response' in row,row;actions.append(row)
        for kind in ['CONVERSION','COUNTY']:
            for label,mutate in [('float_epoch',lambda n:n.update(capture_epoch=3.0)),('copy_wrong_type',lambda n:n.update(native_submit_copy_called=1)),('wrong_request',lambda n:n.update(request_id='another-request')),('changed_intent',lambda n:n['request'].update(action_id='changed-owner')),('wrong_date',lambda n:n.update(date_raw=n['date_raw']+1))]:
                row=action_case(kind,CK3_12003,'queued_verification_pending',mutate=mutate);row['name']+='/'+label;assert row.get('python_rejected'),row;action_errors.append(row)
        from xar_autoplayer.bridge.native_driver import _played_character
        python_actor_boundary=[]
        for value in [-(1<<31),-1,0,(1<<31)-1,1<<31,True]:
            row=dict(value=value)
            try:_played_character(dict(character_id=value,alive=True));row['rejected']=False
            except ValueError:row['rejected']=True
            python_actor_boundary.append(row)
        json.dump(dict(schema='original-python-religion-conversion-county-oracle/v2',reads=reads,read_errors=errors,actions=actions,action_errors=action_errors,python_actor_boundary=python_actor_boundary),sys.stdout,separators=(',',':'),allow_nan=False)
        """;
}
