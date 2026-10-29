package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsCodec;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsContract.*;

/** Strict native normalizers to the actual public serializer. Authored observations do not qualify a Game or Native action. */
final class RootArtifactsPublic64Test {
    private static final BigInteger WIDE=new BigInteger("18446744073709551615");
    private static NativeFrame frame(){var f=RootArtifactsPrivateActionsTest.frame();return new NativeFrame(f.publicRevision(),WIDE,f.dateRaw(),f.actorCharacterId(),f.gamePid(),f.gameCreationFiletime(),WIDE,f.episodeRunId(),f.executableSha256(),true,true,true);}
    private static ObjectNode packet(Request request,boolean claimed,boolean resolved) {
        ObjectNode original=RootArtifactsPrivateActionsTest.windowPacket(request,WIDE,claimed,resolved,10);
        ObjectNode envelope=(ObjectNode)original.get("result"),body=(ObjectNode)envelope.get(request.method().resultKey());
        envelope.put("snapshot_revision",WIDE).put("connection_generation",WIDE);
        for(String key:List.of("current","before","after"))if(body.get(key).isObject()){
            var view=(ObjectNode)body.get(key);view.put("native_revision",WIDE).put("connection_generation",WIDE)
                    .put("capture_epoch",key.equals("before")?WIDE.subtract(BigInteger.ONE):WIDE);
        }
        return original;
    }
    @Test void actualActionAndPostNormalizersKeepNumericOriginalsWhileNamedPublicSerdeRetainsEveryUint64Bit()throws Exception {
        for(Method method:List.of(Method.OPEN,Method.CLOSE,Method.OPEN_POST,Method.CLOSE_POST)){
            Request request=method.readOnly()?new InventoryPost(method,frame().publicRevision(),WIDE):new RevisionRequest(method,frame().publicRevision());
            ObjectNode packet=packet(request,true,method.readOnly());
            Reply reply=ArtifactsCodec.normalize(request,frame(),new NativeEnvelope("authored-original-private",packet,frame()));
            ObjectNode original=reply.payload().original(),publicBody=ArtifactsCodec.encode(reply);
            assertTrue(original.get("intent_sequence").isIntegralNumber());assertEquals(WIDE,original.get("intent_sequence").bigIntegerValue());
            assertEquals(WIDE.toString(),publicBody.get("intent_sequence").textValue());assertEquals(WIDE.toString(),publicBody.get("snapshot_revision").textValue());
            for(String key:List.of("current","before","after")){
                if(original.get(key).isNull()){assertTrue(publicBody.get(key).isNull());continue;}
                for(String field:List.of("native_revision","capture_epoch","connection_generation")){
                    assertTrue(original.get(key).get(field).isIntegralNumber());assertEquals(original.get(key).get(field).bigIntegerValue().toString(),publicBody.get(key).get(field).textValue());
                }
                assertEquals(original.get(key).get("played_character_id"),publicBody.get(key).get("played_character_id"));
            }
            var publicResult=PublicMcpDirectory.CallResult.fromBusinessJson(new RawJson(StrictJson.canonical(publicBody)));
            assertArrayEquals(StrictJson.canonical(publicBody),StrictJson.canonical(StrictJson.parse(publicResult.bytes()).get("structuredContent")));
            assertEquals(original,reply.payload().original(),"public encoding must not mutate ACK comparison material");
            publicBody.put("intent_sequence","0");assertEquals(WIDE.toString(),ArtifactsCodec.encode(reply).get("intent_sequence").textValue());
        }
    }
    @Test void internalInventoryQueryUsesTheSameTypedPublicProjectionAndPreservesNullViews() {
        Request request=new RevisionRequest(Method.OPEN,frame().publicRevision());ObjectNode packet=packet(request,false,false);
        ObjectNode envelope=(ObjectNode)packet.get("result"),body=(ObjectNode)envelope.get(Method.OPEN.resultKey());
        envelope.put("step","query-player-inventory-window-v1-private").put("read_only",true);
        body.put("operation","query").put("read_only",true).put("status","inventory_window_observed").putNull("before").putNull("after");
        ObjectNode output=ArtifactsCodec.normalizeInventoryQuery(frame(),new NativeEnvelope("authored-original-private",packet,frame()));
        assertEquals("0",output.get("intent_sequence").textValue());assertEquals(WIDE.toString(),output.get("current").get("capture_epoch").textValue());
        assertEquals(WIDE.toString(),output.get("current").get("connection_generation").textValue());
        assertTrue(output.get("before").isNull());assertTrue(output.get("after").isNull());
        assertTrue(body.get("current").get("capture_epoch").isIntegralNumber());
    }
    @Test void missingNullBoolFloatAndNativeTextCannotBecomeAValidatedNumericIntent() {
        Request request=new RevisionRequest(Method.OPEN,frame().publicRevision());
        for(JsonNode wrong:List.of(StrictJson.object().putNull("v").get("v"),StrictJson.object().put("v",true).get("v"),
                StrictJson.object().put("v",17.0).get("v"),StrictJson.object().put("v",WIDE.toString()).get("v"))){
            ObjectNode packet=packet(request,true,false);((ObjectNode)packet.get("result").get(Method.OPEN.resultKey())).set("intent_sequence",wrong);
            assertThrows(IllegalArgumentException.class,()->ArtifactsCodec.normalize(request,frame(),new NativeEnvelope("authored-original-private",packet,frame())));
        }
        ObjectNode missing=packet(request,true,false);((ObjectNode)missing.get("result").get(Method.OPEN.resultKey())).remove("intent_sequence");
        assertThrows(IllegalArgumentException.class,()->ArtifactsCodec.normalize(request,frame(),new NativeEnvelope("authored-original-private",missing,frame())));
    }
    @Test void originalPythonPersonalNormalizersAndJavaAgreeOnFullPositiveSubmitPostAndPublicUint64Representation()throws Exception {
        var cases=new ArrayList<ObjectNode>();
        for(Request request:List.of(new ArtifactRead(frame().publicRevision(),73),
                new PersonalSubmit(frame().publicRevision(),73,true,0,new org.xar.ck3.control.contracts.PublicUnsigned64.Missing(),true),
                new PersonalPost(frame().publicRevision(),73,WIDE))){
            boolean item=request.method()==Method.PERSONAL_ITEM,post=request.method()==Method.PERSONAL_POST;
            ObjectNode body=item?item(false,WIDE):personal(post),packet=envelope(request,body);
            var row=StrictJson.object().put("family",item?"item":"personal");row.set("body",body);cases.add(row);
            Reply reply=ArtifactsCodec.normalize(request,frame(),new NativeEnvelope("authored-original-private",packet,frame()));
            ObjectNode result=ArtifactsCodec.encode(reply);assertTrue(reply.facts().available());
            assertFalse(result.get("business_outcome_observed").booleanValue());
            if(item){assertEquals(WIDE.toString(),result.get("capture_epoch").textValue());assertTrue(reply.payload().original().get("capture_epoch").isIntegralNumber());}
            else {
                assertEquals(WIDE.toString(),result.get("intent_sequence").textValue());
                assertEquals(WIDE.toString(),result.get("before_native_revision").textValue());assertEquals(WIDE.toString(),result.get("before_connection_generation").textValue());
                assertEquals(WIDE.subtract(BigInteger.ONE).toString(),result.get("before").get("capture_epoch").textValue());
                if(post){assertEquals(WIDE.toString(),result.get("after").get("capture_epoch").textValue());assertTrue(reply.facts().independentDesiredObserved());}
                else {assertTrue(result.get("after").isNull());assertEquals("0",result.get("after_native_revision").textValue());assertTrue(reply.facts().needsRecovery());}
                assertTrue(reply.payload().original().get("intent_sequence").isIntegralNumber());
            }
            var wire=PublicMcpDirectory.CallResult.fromBusinessJson(new RawJson(StrictJson.canonical(result)));
            assertArrayEquals(StrictJson.canonical(result),StrictJson.canonical(StrictJson.parse(wire.bytes()).get("structuredContent")));
        }
        var accepted=originalNormalizers(cases);assertEquals(cases.size(),accepted.size());
        for(int i=0;i<cases.size();i++)assertArrayEquals(StrictJson.canonical(cases.get(i)),StrictJson.canonical(accepted.get(i)),
                "actual original pure validators must accept and retain the same complete native JSON bodies");
    }
    @Test void anUndeclaredWideBusinessNumberIsRejectedAtItsExactPathRatherThanSilentlyRewrittenByItsName() {
        Request request=new ArtifactRead(frame().publicRevision(),73);ObjectNode body=item(false,WIDE);
        ObjectNode definition=(ObjectNode)body.get("item_modifier_definition");definition.put("available",true);
        definition.putArray("entries").add(StrictJson.object().put("key_raw_u16",17).put("definition_value_raw_q64",Long.MAX_VALUE));
        Reply reply=ArtifactsCodec.normalize(request,frame(),new NativeEnvelope("authored-original-private",envelope(request,body),frame()));
        var rejected=assertThrows(IllegalArgumentException.class,()->ArtifactsCodec.encode(reply));
        assertTrue(rejected.getMessage().contains("$.item_modifier_definition.entries[0].definition_value_raw_q64"));
        assertTrue(reply.payload().original().get("item_modifier_definition").get("entries").get(0).get("definition_value_raw_q64").isIntegralNumber());
    }
    private static ObjectNode item(boolean equipped,BigInteger epoch) {
        ObjectNode r=StrictJson.object().put("schema","ck3_12004_player_artifact_personal_use_v1").put("game_version",VERSION).put("executable_sha256",EXECUTABLE_SHA256)
                .put("available",true).putNull("unavailable_reason").put("loaded_source_pins_verified",true).put("capture_epoch",epoch).put("date_raw",24)
                .put("played_character_id",99).put("requested_artifact_id",73).put("personally_owned",true).put("inventory_artifact",true).put("equipped",equipped)
                .put("native_equipped_observed",true).put("inventory_view_available",true).put("inventory_view_visible",true).put("effective_slot_index",0)
                .put("can_equip_in_effective_slot",!equipped).put("can_unequip",equipped).put("read_only",true);
        r.putArray("owned_ids").add(73);ObjectNode slot=StrictJson.object().put("index",0).put("key","primary").put("personal",true);
        if(equipped){r.put("equipped_slot_index",0).put("replacing_artifact_id",73);slot.put("artifact_id",73);}
        else {r.putNull("equipped_slot_index").putNull("replacing_artifact_id");slot.putNull("artifact_id");}
        r.putArray("slots").add(slot);r.set("item_modifier_definition",StrictJson.object().put("available",false).putNull("entries"));
        r.set("modifier_description",StrictJson.object().put("available",false).putNull("text"));
        for(String key:List.of("modifier_names_bound","actor_aggregate_observed","personal_net_effect_attributed","total_payment_observed","action_ready","business_outcome_observed"))r.put(key,false);
        return r;
    }
    private static ObjectNode personal(boolean post) {
        ObjectNode r=StrictJson.object().put("schema","ck3_12004_player_artifact_personal_use_action_v1").put("game_version",VERSION).put("executable_sha256",EXECUTABLE_SHA256)
                .put("available",true).putNull("unavailable_reason").put("read_only",post).put("played_character_id",99).put("artifact_id",73)
                .put("desired_equipped",true).put("expected_slot_index",0).putNull("expected_replacing_artifact_id").put("intent_sequence",WIDE)
                .put("intent_found",true).put("invoked",true).put("once_intent_consumed",true).put("dispatch_call_returned",true).put("needs_recovery",!post)
                .put("desired_inventory_state_observed",post).put("status",post?"desired_inventory_state_observed":"original_callback_invoked_post_pending")
                .put("before_native_revision",WIDE).put("before_connection_generation",WIDE).put("before_game_pid",123)
                .put("after_native_revision",post?WIDE:BigInteger.ZERO).put("after_connection_generation",post?WIDE:BigInteger.ZERO).put("after_game_pid",post?123:0);
        r.set("before",item(false,WIDE.subtract(BigInteger.ONE)));if(post)r.set("after",item(true,WIDE));else r.putNull("after");
        for(String key:List.of("business_outcome_observed","actor_aggregate_observed","personal_net_effect_attributed","total_payment_observed","automatic_retry"))r.put(key,false);
        return r;
    }
    private static ObjectNode envelope(Request request,ObjectNode body) {
        String backend=request.method()==Method.PERSONAL_ITEM?"ck3-1.20.0.4-native-player-artifact-personal-use-v1":"ck3-1.20.0.4-native-player-artifact-personal-use-action-v1-private";
        ObjectNode env=StrictJson.object().put("step",request.method().step()).put("accepted",true).put("private_build",true).put("read_only",request.method().readOnly())
                .put("advertised",false).put("game_version",VERSION).put("executable_sha256",EXECUTABLE_SHA256).put("backend_id",backend).put("domain_key",request.method().domain())
                .put("snapshot_revision",WIDE).put("date_raw",24).put("status","observed");env.set(request.method().resultKey(),body);
        var packet=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","authored-original-private").put("ok",true);packet.set("result",env);return packet;
    }
    private static List<ObjectNode> originalNormalizers(List<ObjectNode> rows)throws Exception {
        Path root=requiredPath("xar.repository.root",true);
        assertTrue(Files.isRegularFile(root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/artifact_personal_use_action_private_transport_v1.py")),
                "actual original Python migration oracle must be present; this is not a skip");
        var input=StrictJson.object();input.putArray("cases").addAll(rows);
        String program="""
            import base64,json,sys
            from pathlib import Path
            sys.path.insert(0,str(Path(sys.argv[1])/'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge import faith_observers_private_transport_v1 as R
            from xar_autoplayer.bridge import artifact_personal_use_action_private_transport_v1 as A
            w=2**64-1
            snapshot={'snapshot_id':'original-pure-personal','revision':15,'native_revision':w,'date_raw':24,
                'paused':True,'map_ready':True,'played_character':{'character_id':99,'alive':True},
                'diagnostics':{'bridge_pid':123,'connection_generation':w,'hello':{'pid':123,'connection_generation':w,
                    'ck3_build_match':True,'expected_ck3_version':'1.20.0.4',
                    'expected_ck3_sha256':'98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'}}}
            cases=json.loads(base64.b64decode(sys.argv[2]))['cases']
            for row in cases:
                b=row['body']
                if row['family']=='item':R.normalize_player_artifact_personal_use_v1(b,snapshot=snapshot,artifact_id=73)
                else:A.normalize_artifact_personal_use_action_v1(b,snapshot=snapshot,artifact_id=73,
                    post=b['read_only'],expected_intent_sequence=w if b['read_only'] else None,
                    submitted=None if b['read_only'] else {'desired_equipped':True,'expected_slot_index':0,'expected_replacing_artifact_id':None})
            print(json.dumps(cases,separators=(',',':')))
            """;
        Path output=Files.createTempFile("artifact-public64-original-",".json");
        try {
            var builder=new ProcessBuilder(requiredPath("xar.python",false).toString(),"-B","-X","utf8","-c",program,root.toString(),Base64.getEncoder().encodeToString(StrictJson.canonical(input)));
            originalEnvironment(builder,root);var process=builder.redirectErrorStream(true).redirectOutput(output.toFile()).start();
            boolean ended=process.waitFor(45,TimeUnit.SECONDS);if(!ended){process.destroyForcibly();process.waitFor(5,TimeUnit.SECONDS);}assertTrue(ended,"actual original pure normalizer timed out");
            byte[] bytes=Files.readAllBytes(output);assertEquals(0,process.exitValue(),new String(bytes,StandardCharsets.UTF_8));
            var result=new ArrayList<ObjectNode>();for(JsonNode row:StrictJson.parse(bytes))result.add(assertInstanceOf(ObjectNode.class,row));return List.copyOf(result);
        }finally{Files.deleteIfExists(output);}
    }
    private static Path requiredPath(String property,boolean directory)throws java.io.IOException {
        String configured=System.getProperty(property);assertNotNull(configured,property+" is mandatory");
        assertFalse(configured.isBlank(),property+" is mandatory");Path input=Path.of(configured);
        assertTrue(input.isAbsolute(),property+" must be the admitted absolute path");Path actual=input.toRealPath();
        assertTrue(directory?Files.isDirectory(actual):Files.isRegularFile(actual),property+" actual input is missing");return actual;
    }
    private static void originalEnvironment(ProcessBuilder builder,Path root)throws java.io.IOException {
        builder.directory(root.toFile());var environment=builder.environment();
        environment.put("PYTHONPATH",root.resolve("ck3_autonomous_player/src").toRealPath().toString());
        environment.put("XAR_SOURCE_REPOSITORY",root.toString());
        environment.put("PYTHONDONTWRITEBYTECODE","1");environment.put("PYTHONUTF8","1");
    }

}
