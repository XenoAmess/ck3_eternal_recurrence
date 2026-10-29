package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.family.CachedSuccession12004;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.driverregistry.DriverRegistryCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.driverregistry.DriverRegistryContract;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.McpCancellation;
import org.xar.ck3.control.service.mcp.PublicMcpBindings;

/** Real unchanged original producer -> existing typed decoder -> actual direct boundary -> sole public serializer.
 * This software fixture grants no Core, permission, Game or succession credit. Required source/tool inputs fail if absent. */
final class RootDriverRegistryPublicProductsTest {
    @TempDir Path temporary;
    private static final String SOURCE_SHA="ffec5d1dbc4af7a5a38198c24f58628656f160812c8b93706d6c9d4b8e10e030";
    private static final BigInteger U64=new BigInteger("18446744073709551615");
    private static final String ORACLE="""
        import hashlib,json,sys
        from pathlib import Path
        anchor=Path(sys.argv[1])
        if hashlib.sha256(anchor.read_bytes()).hexdigest()!=sys.argv[2]: raise RuntimeError('native anchor changed')
        original=anchor.with_name('actor_cached_succession_private_v1.py')
        raw=original.read_bytes()
        if len(raw)!=8328 or hashlib.sha256(raw).hexdigest()!=sys.argv[3]: raise RuntimeError('original cached producer changed')
        sys.path.insert(0,str(anchor.parents[2]))
        from xar_autoplayer.bridge import actor_cached_succession_private_v1 as producer
        row=json.loads(Path(sys.argv[4]).read_bytes())
        result=producer.project_native_query(row['native'],row['binding'])
        if original.read_bytes()!=raw or hashlib.sha256(anchor.read_bytes()).hexdigest()!=sys.argv[2]: raise RuntimeError('source drift during actual producer')
        sys.stdout.buffer.write(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode('utf-8'))
        """;

    @Test void unchangedOriginalProducerFlowsThroughActualDescriptorDirectDecoderHandlerAndSerializer() throws Exception {
        var binding=binding(BigInteger.valueOf(7)); var nativeResult=nativeResult(true);
        var original=original(nativeResult,binding);
        var typed=CachedSuccession12004.decodeNative(raw(nativeResult),binding);
        assertEquals(original,parse(CachedSuccession12004.encodePublic(typed)));
        assertEquals(List.of(42L,7L,42L),((CachedSuccession12004.Available)typed.roster()).completeCachedSuccessorIds());
        var direct=RootDriverRegistryPublicProducts.cachedBinding(
                new ExactRef("software/RootDriverRegistryPublicProducts.java",1,"a".repeat(64)),request->{
                    assertEquals(BigInteger.valueOf(7),request.expectedRevision());
                    return new DriverRegistryContract.CachedResponse(typed);
                });
        var descriptor=RootOriginalPublicTestInputs.tools().stream().filter(x->x.name().equals(DriverRegistryContract.CACHED_NAME)).findFirst().orElseThrow();
        var arguments=new Arguments(Presence.VALUE,Optional.of(raw("{\"expected_revision\":7}")));
        descriptor.validateArguments(arguments);
        var call=new ToolCall(direct.name(),arguments,Optional.empty(),new McpCancellation());
        var request=direct.decoder().decode(call);
        var response=direct.actual().invoke(request);
        var complete=direct.encoder().encode(response); descriptor.validateResult(complete);
        assertEquals(PublicMcpBindings.Kind.DRIVER_DIRECT,direct.kind());
        var publicRaw=DriverRegistryCodec.encode(response);
        assertEquals(response,DriverRegistryCodec.decode(publicRaw));
        assertEquals(U64.toString(),parse(publicRaw).at("/native_result/actor_cached_succession/native_data_pointer").textValue());
        assertEquals(U64.toString(),parse(publicRaw).at("/native_result/actor_cached_succession/capture_epoch").textValue());
        assertFalse(parse(publicRaw).get("business_postcondition_verified").booleanValue());
        assertFalse(parse(publicRaw).get("full_product_acceptance_credit").booleanValue());
    }

    @Test void unsafeAndWrongTypeInputsNeverReachBusinessAndUint64SerdeRetainsExactIdentity() throws Exception {
        var direct=RootDriverRegistryPublicProducts.cachedBinding(new ExactRef("software/test",1,"b".repeat(64)),
                request->{throw new AssertionError("invalid arguments reached business");});
        for(var input:List.of("{}","{\"expected_revision\":null}","{\"expected_revision\":true}","{\"expected_revision\":7.0}",
                "{\"expected_revision\":9007199254740992}","{\"expected_revision\":\"07\"}",
                "{\"expected_revision\":\"18446744073709551616\"}","{\"expected_revision\":7,\"actor_id\":42}")) {
            var call=new ToolCall(direct.name(),new Arguments(Presence.VALUE,Optional.of(raw(input))),Optional.empty(),new McpCancellation());
            assertThrows(IllegalArgumentException.class,()->direct.decoder().decode(call),input);
        }
        for(var presence:List.of(Presence.MISSING,Presence.NULL)) {
            var call=new ToolCall(direct.name(),new Arguments(presence,presence==Presence.MISSING?Optional.empty():Optional.of(raw("null"))),Optional.empty(),new McpCancellation());
            assertThrows(IllegalArgumentException.class,()->direct.decoder().decode(call));
        }
        assertEquals(U64,DriverRegistryCodec.cached(new PublicBindings.Value(raw("{\"expected_revision\":\"18446744073709551615\"}"))).expectedRevision());
        var bound=binding(U64); var typed=CachedSuccession12004.decodeNative(raw(nativeResult(true)),bound);
        var response=new DriverRegistryContract.CachedResponse(typed);
        assertEquals(parse(CachedSuccession12004.encodePublic(typed)),original(nativeResult(true),bound));
        var encoded=DriverRegistryCodec.encode(response);
        assertEquals(U64.toString(),parse(encoded).get("queried_revision").textValue());
        assertEquals(response,DriverRegistryCodec.decode(encoded));
    }

    @Test void originalUnavailableRetainsNullsAndEveryCorruptedPublicFieldIsRejected() throws Exception {
        var bound=binding(BigInteger.valueOf(7)); var source=nativeResult(false);
        var typed=CachedSuccession12004.decodeNative(raw(source),bound);
        assertEquals(parse(CachedSuccession12004.encodePublic(typed)),original(source,bound));
        var response=new DriverRegistryContract.CachedResponse(typed); var encoded=DriverRegistryCodec.encode(response);
        assertTrue(parse(encoded).at("/native_result/actor_cached_succession/native_data_pointer").isNull());
        assertEquals(response,DriverRegistryCodec.decode(encoded));
        for(var field:List.of("queried_revision","queried_native_revision","connection_generation","business_postcondition_verified")) {
            ObjectNode missing=(ObjectNode)parse(encoded); missing.remove(field);
            assertThrows(IllegalArgumentException.class,()->DriverRegistryCodec.decode(raw(missing)),field);
        }
        for(var value:List.of("true","7.0","7","null")) {
            ObjectNode wrong=(ObjectNode)parse(encoded); wrong.set("queried_revision",StrictJson.parse(value.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->DriverRegistryCodec.decode(raw(wrong)),value);
        }
        ObjectNode credit=(ObjectNode)parse(encoded);credit.put("full_product_acceptance_credit",true);
        assertThrows(IllegalArgumentException.class,()->DriverRegistryCodec.decode(raw(credit)));
        ObjectNode missingPointer=(ObjectNode)parse(encoded);
        ((ObjectNode)missingPointer.at("/native_result/actor_cached_succession")).remove("native_data_pointer");
        assertThrows(IllegalArgumentException.class,()->DriverRegistryCodec.decode(raw(missingPointer)));
    }

    private CachedSuccession12004.Binding binding(BigInteger revision) {
        return new CachedSuccession12004.Binding("actual-paused-frame",revision,U64,12345,59077,U64,42);
    }
    private ObjectNode nativeResult(boolean available) {
        var root=StrictJson.object().put("step",CachedSuccession12004.STEP).put("accepted",true)
                .put("status",available?"observed":"unavailable").put("private_build",true).put("read_only",true).put("advertised",false)
                .put("game_version","1.20.0.4").put("executable_sha256",CachedSuccession12004.EXE_SHA256)
                .put("domain_key","actor_cached_succession_v1").put("backend_id","ck3-1.20.0.4-native-actor-cached-succession-v1")
                .put("snapshot_revision",U64).put("date_raw",12345);
        var payload=StrictJson.object().put("schema","ck3-1.20.0.4-actor-cached-succession-v1").put("read_only",true)
                .put("game_version","1.20.0.4").put("executable_sha256",CachedSuccession12004.EXE_SHA256)
                .put("available",available).put("capture_epoch",U64).put("date_raw",12345)
                .put("played_character_id",42).put("played_character_full_id",42).put("roster_complete",available);
        if(available) {
            payload.putNull("unavailable_reason").put("native_count",3).put("native_data_pointer",U64).put("land_state_pointer",U64);
            payload.putArray("complete_cached_successor_ids").add(42).add(7).add(42);
        } else {
            payload.put("unavailable_reason","actual native cache unavailable");
            for(var key:List.of("native_count","complete_cached_successor_ids","native_data_pointer","land_state_pointer"))payload.putNull(key);
        }
        root.set("actor_cached_succession",payload); return root;
    }
    private JsonNode original(ObjectNode nativeResult,CachedSuccession12004.Binding binding) throws Exception {
        Path anchor=Path.of(required("xar.native.producer.source"));
        Path python=Path.of(required("xar.native.producer.python"));
        String anchorSha=required("xar.native.producer.sha256");
        if(!anchor.isAbsolute()||!python.isAbsolute()||!anchorSha.matches("[a-f0-9]{64}"))
            throw new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_CACHED_PRODUCER");
        assertEquals(anchorSha,sha(Files.readAllBytes(anchor)));
        Path module=anchor.resolveSibling("actor_cached_succession_private_v1.py");
        assertEquals(SOURCE_SHA,sha(Files.readAllBytes(module)));
        var row=StrictJson.object();row.set("native",nativeResult);
        row.set("binding",StrictJson.object().put("snapshot_id",binding.snapshotId()).put("revision",binding.revision())
                .put("native_revision",binding.nativeRevision()).put("date_raw",binding.dateRaw()).put("game_pid",binding.gamePid())
                .put("connection_generation",binding.connectionGeneration()).put("played_character_id",binding.playedCharacterId()));
        Path input=temporary.resolve("original-input.json"),output=temporary.resolve("original-output.json"),error=temporary.resolve("original-stderr.txt");
        Files.write(input,StrictJson.canonical(row));
        var process=new ProcessBuilder(python.toString(),"-X","utf8","-B","-c",ORACLE,anchor.toString(),anchorSha,SOURCE_SHA,input.toString())
                .redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if(!process.waitFor(20,TimeUnit.SECONDS)){process.destroyForcibly();throw new IOException("original cached producer timed out");}
        if(process.exitValue()!=0)throw new IOException("original cached producer failed: "+Files.readString(error));
        assertEquals(anchorSha,sha(Files.readAllBytes(anchor)));assertEquals(SOURCE_SHA,sha(Files.readAllBytes(module)));
        return StrictJson.parse(Files.readAllBytes(output));
    }
    private static JsonNode parse(RawJson raw){return StrictJson.parse(raw.bytes());}
    private static RawJson raw(JsonNode value){return new RawJson(StrictJson.canonical(value));}
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_INPUT: "+key);return value;}
    private static String sha(byte[] bytes)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
}

