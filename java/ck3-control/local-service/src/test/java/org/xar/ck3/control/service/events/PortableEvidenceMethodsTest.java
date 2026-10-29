package org.xar.ck3.control.service.events;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.evidence.PortableEvidenceReader;
import org.xar.ck3.control.service.mcp.McpCancellation;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory.DirectBinding;
import org.xar.ck3.control.service.mcp.PublicMcpBindings;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Actual typed Service methods/decoder/handler/result envelope. Full Root source admission remains separate. */
final class PortableEvidenceMethodsTest {
    private static String property(String key){String value=System.getProperty(key);assertNotNull(value,"required typed CI input "+key);return value;}
    private static ExactRef reference(Path path) throws Exception {byte[] bytes=Files.readAllBytes(path);return new ExactRef(path.toAbsolutePath().normalize().toString(),bytes.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));}
    private static ExactRef implementation() throws Exception {
        // The CI input producer pins this exact selected Java body from the actual compiled snapshot.
        // This check alone gives no compiler/source qualification or Root/Game authority.
        var ref=reference(Path.of(property("xar.portable.evidence.methods.source.path")));
        assertEquals(property("xar.portable.evidence.methods.source.sha256"),ref.sha256());
        assertEquals(Long.parseLong(property("xar.portable.evidence.methods.source.bytes")),ref.bytes());return ref;
    }
    private static Path bundle(){return Path.of(property("xar.repository.root")).resolve("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/portable_evidence");}
    private static <Q,R> CallResult invoke(DirectBinding<Q,R> binding,RawJson arguments) throws Exception {
        var call=new ToolCall(binding.name(),new Arguments(Presence.VALUE,Optional.of(arguments)),Optional.empty(),new McpCancellation());
        Q query=binding.decoder().decode(call);R response=binding.actual().invoke(query);return binding.encoder().encode(response);
    }
    @Test void sourcePinnedActualToolMethodsExposeOriginalBusinessFieldsAndBoundedSlices() throws Exception {
        var methods=new PortableEvidenceMethods(new PortableEvidenceReader(reference(bundle().resolve("manifest_v1.json"))));
        var bindings=methods.actualMethods(implementation());assertEquals(2,bindings.size());
        for(var binding:bindings)assertEquals(PublicMcpBindings.Kind.STATIC_KNOWLEDGE,binding.kind());
        var listed=PublicDataJson.object(new RawJson(invoke(bindings.getFirst(),new RawJson("{\"limit\":1}".getBytes(java.nio.charset.StandardCharsets.UTF_8))).bytes()));
        assertFalse(listed.path("isError").booleanValue());var business=listed.path("structuredContent");assertEquals("available",business.path("status").textValue());
        String id=business.path("evidence").get(0).path("evidence_id").textValue();
        byte[] envelope=invoke(bindings.getLast(),new RawJson(StrictJson.canonical(StrictJson.object().put("evidence_id",id).put("max_bytes",65536)))).bytes();
        assertTrue(envelope.length>65536,"real complete public read exceeds the small Map lane");
        var read=PublicDataJson.object(new RawJson(envelope)).path("structuredContent");
        assertEquals("available",read.path("status").textValue());assertEquals(id,read.path("sha256").textValue());assertEquals(65536,read.path("content_bytes").intValue());
        assertFalse(read.has("bundle_root"));assertFalse(read.has("blob_path"));assertEquals(65536,java.util.Base64.getDecoder().decode(read.path("content_base64").textValue()).length);
    }
    @Test void unpinnedBundleAndChangedPinnedManifestNeverInstallAWorkingKnowledgeHandler() throws Exception {
        assertThrows(IllegalStateException.class,()->new PortableEvidenceMethods(new PortableEvidenceReader(bundle())));
        var actual=reference(bundle().resolve("manifest_v1.json"));var changed=new ExactRef(actual.path(),actual.bytes(),"0".repeat(64));
        var methods=new PortableEvidenceMethods(new PortableEvidenceReader(changed));
        var result=PublicDataJson.object(new RawJson(invoke(methods.actualMethods(implementation()).getFirst(),new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8))).bytes())).path("structuredContent");
        assertEquals("unavailable",result.path("status").textValue());assertEquals("bundle_integrity_error",result.path("unavailable_reason").textValue());assertTrue(result.path("evidence").isEmpty());
    }
}
