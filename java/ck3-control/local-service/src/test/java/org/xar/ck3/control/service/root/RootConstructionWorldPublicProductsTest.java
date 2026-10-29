package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Source-only submission: Root must run this in the real full selected graph; missing fixture is failure. */
class RootConstructionWorldPublicProductsTest {
    static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    @Test void publicRevisionRejectsMissingNullBoolFloatExtraAndUnsafeNumber() {
        for(String value:new String[]{"{}","{\"expected_revision\":null}","{\"expected_revision\":true}","{\"expected_revision\":1.0}","{\"expected_revision\":0}","{\"expected_revision\":1,\"material_receipt\":false}","{\"expected_revision\":9007199254740992}"})
            assertThrows(IllegalArgumentException.class,()->RootConstructionWorldPublicProducts.decode(raw(value)),value);
        assertEquals(new BigInteger("18446744073709551615"),RootConstructionWorldPublicProducts.decode(raw("{\"expected_revision\":\"18446744073709551615\"}")).expectedRevision());
    }
    @Test void declaredRawNumbersAndIdentitiesRoundTripWithoutJavascriptRounding() {
        var response=new RootConstructionWorldPublicProducts.Response(raw("{\"status\":\"material_source\",\"proof_epoch\":18446744073709551615,\"world\":{\"player_gold_raw\":9223372036854775807,\"cost_raw_native\":[-9223372036854775808,0],\"context_identity\":\"0xAB\",\"legal_samples\":[],\"completed_buildings\":null}}"));
        var wire=RootConstructionWorldPublicProducts.encode(response);var n=PublicDataJson.object(wire);
        assertEquals("18446744073709551615",n.path("proof_epoch").textValue());
        assertEquals("-9223372036854775808",n.path("world").path("cost_raw_native").get(0).textValue());
        assertEquals("0xAB",n.path("world").path("context_identity").textValue());
        assertEquals(PublicDataJson.object(response.originalMemory()),PublicDataJson.object(RootConstructionWorldPublicProducts.restore(wire).originalMemory()));
        assertTrue(n.path("world").path("completed_buildings").isNull());
    }
    @Test void unknownWideIntegerAndWrongDeclaredTypeCannotBePublished() {
        for(String json:new String[]{"{\"new_unknown_integer\":9007199254740992}","{\"proof_epoch\":true}","{\"player_gold_raw\":1.0}","{\"cost_raw_native\":{}}"})
            assertThrows(IllegalArgumentException.class,()->RootConstructionWorldPublicProducts.encode(new RootConstructionWorldPublicProducts.Response(raw(json))));
    }
    @Test void actualDirectBindingInvokesItsTypedConsumerAndUsesOnePublicName()throws Exception {
        var calls=new AtomicInteger();var expected=new RootConstructionWorldPublicProducts.Response(raw("{\"status\":\"source_red\"}"));
        var binding=RootConstructionWorldPublicProducts.binding(new ExactRef("source-only-test",1,"0".repeat(64)),request->{calls.incrementAndGet();assertEquals(BigInteger.ONE,request.expectedRevision());return expected;});
        assertEquals("ck3_query_domain_construction_world_private_v1",binding.name());
        assertSame(expected,binding.actual().invoke(new RootConstructionWorldPublicProducts.Request(BigInteger.ONE)));
        assertEquals(1,calls.get());assertNotNull(binding.encoder().encode(expected));
    }
    @Test void originalPythonPublicQueryMatchesActualJavaMaterialFinalizer()throws Exception {
        Path fixture=Path.of(required("xar.construction.world.original.input"));byte[] bytes=Files.readAllBytes(fixture);
        assertEquals(required("xar.construction.world.original.sha256"),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        JsonNode input=StrictJson.parse(bytes,262144);assertTrue(input.path("material_receipt").isBoolean()&&input.get("material_receipt").booleanValue());
        assertEquals(false,input.path("wartime_observation").booleanValue());
        var before=DriverJson.object(PublicDataJson.encode(input.get("starting_snapshot")).bytes(),262144);
        var after=DriverJson.object(PublicDataJson.encode(input.get("ending_snapshot")).bytes(),262144);
        var request=new RootConstructionWorldPublicProducts.Request(input.get("expected_revision").bigIntegerValue());
        var actual=RootConstructionWorldPublicProducts.finalizeOriginal(request,before,after,PublicDataJson.encode(input.get("native_envelope")),input.get("native_query_request_id").textValue());
        var child=new ProcessBuilder(required("xar.original.python"),"-c",ORIGINAL,fixture.toString(),required("xar.original.python.source.root")).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] output=child.getInputStream().readAllBytes();assertEquals(0,child.waitFor(),"original Python public world producer failed");
        assertEquals(PublicDataJson.object(new RawJson(output)),PublicDataJson.object(actual.originalMemory()));
        assertEquals(PublicDataJson.object(actual.originalMemory()),PublicDataJson.object(RootConstructionWorldPublicProducts.restore(RootConstructionWorldPublicProducts.encode(actual)).originalMemory()));
        var changed=input.get("ending_snapshot").deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)changed).put("snapshot_id","changed-actual-frame");
        var stale=RootConstructionWorldPublicProducts.finalizeOriginal(request,before,DriverJson.object(PublicDataJson.encode(changed).bytes(),262144),PublicDataJson.encode(input.get("native_envelope")),input.get("native_query_request_id").textValue());
        assertEquals("source_red",PublicDataJson.object(stale.originalMemory()).path("status").textValue());
    }
    private static String required(String key){String v=System.getProperty(key);if(v==null||v.isBlank())throw new IllegalStateException("actual full CI prerequisite missing: "+key);return v;}
    static final String ORIGINAL="""
import json,sys,types,copy
from pathlib import Path
sys.path.insert(0,sys.argv[2])
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as m
x=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
rid=x['native_query_request_id'];assert rid.startswith('construction-read-')
frames=iter([x['starting_snapshot'],x['ending_snapshot']])
class Driver:
 def take_snapshot_without_native_command_history(self):return copy.deepcopy(next(frames))
def send(driver,step,revision,request_id):
 assert step==m.QUERY_NATIVE and revision==x['starting_snapshot']['native_revision'] and request_id==rid
 return copy.deepcopy(x['native_envelope']['result'])
m._send=send
m.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=rid[len('construction-read-'):]))
answer=m.query_domain_construction_world_private_v1(Driver(),expected_revision=x['expected_revision'])
print(json.dumps(answer,ensure_ascii=False,separators=(',',':')))
""";
}
