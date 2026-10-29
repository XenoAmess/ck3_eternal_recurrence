package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Locale;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import org.xar.ck3.control.evidence.PortableEvidenceReader;
import org.xar.ck3.control.service.events.PortableEvidenceMethods;
import org.xar.ck3.control.service.mcp.McpCancellation;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory.DirectBinding;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Real checked-in bundle through the same mandatory SDK role and actual public bindings.
 * Source fixtures prove no installed DATA root, complete runtime, lease or Game qualification.
 */
final class RootPortableEvidenceDataTest {
    private static String property(String key) {
        String value=System.getProperty(key);assertNotNull(value,"required persistent CI input "+key);return value;
    }
    private static FileRef measure(Path supplied) throws Exception {
        Path path=supplied.toAbsolutePath().normalize();byte[] bytes=Files.readAllBytes(path);
        return new FileRef(path.toString(),bytes.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    }
    private static ExactRef exact(FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static FileRef actualManifest() throws Exception {
        return measure(Path.of(property("xar.repository.root")).resolve("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/portable_evidence/manifest_v1.json"));
    }
    private static ExactRef compiledMethods() throws Exception {
        FileRef actual=measure(Path.of(property("xar.portable.evidence.methods.source.path")));
        assertEquals(property("xar.portable.evidence.methods.source.sha256"),actual.sha256());
        assertEquals(Long.parseLong(property("xar.portable.evidence.methods.source.bytes")),actual.bytes());return exact(actual);
    }
    private static <Q,R> CallResult invoke(DirectBinding<Q,R> binding,String json) throws Exception {
        var call=new ToolCall(binding.name(),new Arguments(Presence.VALUE,Optional.of(new RawJson(json.getBytes(StandardCharsets.UTF_8)))),Optional.empty(),new McpCancellation());
        return binding.encoder().encode(binding.actual().invoke(binding.decoder().decode(call)));
    }
    @Test void actualBundleOriginalFlowsThroughSdkRoleIdentityReaderAndTypedPublicSerialization() throws Exception {
        FileRef original=actualManifest();var pin=new DataPin(DataRole.PORTABLE_EVENT_EVIDENCE_MANIFEST,original);
        byte[] retained=RootRuntimeDefinitions.readData(pin);assertArrayEquals(Files.readAllBytes(Path.of(original.path())),retained);
        var stamp=IdentityBearingFileAttributes.read(Path.of(original.path()));assertNotNull(stamp.fileKey());
        if(System.getProperty("os.name").toLowerCase(Locale.ROOT).startsWith("windows")) {
            var identity=assertInstanceOf(IdentityBearingFileAttributes.WindowsFileIdentity.class,stamp.fileKey());
            for(String value:new String[]{identity.volumeSerialDecimal(),identity.fileIdDecimal(),identity.creationFiletimeDecimal()})
                assertEquals(value,new java.math.BigInteger(value).toString(),"native identity stays a canonical decimal string");
        }
        var reader=new PortableEvidenceReader(exact(pin.originalRef()));
        assertEquals(exact(original),reader.requireManifestSource());assertEquals(299,reader.manifest().evidence().size());
        var bindings=new PortableEvidenceMethods(reader).actualMethods(compiledMethods());
        var listed=PublicDataJson.object(new RawJson(invoke(bindings.getFirst(),"{\"limit\":1}").bytes())).path("structuredContent");
        assertEquals("available",listed.path("status").textValue());String id=listed.path("evidence").get(0).path("evidence_id").textValue();
        var content=PublicDataJson.object(new RawJson(invoke(bindings.getLast(),"{\"evidence_id\":\""+id+"\",\"max_bytes\":37}").bytes())).path("structuredContent");
        assertEquals("available",content.path("status").textValue());assertEquals(id,content.path("sha256").textValue());
        assertEquals(37,java.util.Base64.getDecoder().decode(content.path("content_base64").textValue()).length);
        assertFalse(content.has("blob_path"));assertEquals(exact(original),reader.requireManifestSource());
        assertArrayEquals(retained,RootRuntimeDefinitions.readData(pin));
    }
    @Test void forgedOriginalPinIsRefusedByBothActualSdkReadAndActualPublicHandler() throws Exception {
        FileRef original=actualManifest();String wrong=original.sha256().charAt(0)=='0'?"1"+original.sha256().substring(1):"0"+original.sha256().substring(1);
        FileRef changed=new FileRef(original.path(),original.bytes(),wrong);
        assertThrows(IOException.class,()->RootRuntimeDefinitions.readData(new DataPin(DataRole.PORTABLE_EVENT_EVIDENCE_MANIFEST,changed)));
        var bindings=new PortableEvidenceMethods(new PortableEvidenceReader(exact(changed))).actualMethods(compiledMethods());
        var listed=PublicDataJson.object(new RawJson(invoke(bindings.getFirst(),"{}").bytes())).path("structuredContent");
        assertEquals("unavailable",listed.path("status").textValue());assertEquals("bundle_integrity_error",listed.path("unavailable_reason").textValue());
        assertTrue(listed.path("evidence").isEmpty());assertArrayEquals(Files.readAllBytes(Path.of(original.path())),RootRuntimeDefinitions.readData(new DataPin(DataRole.PORTABLE_EVENT_EVIDENCE_MANIFEST,original)));
    }
}
