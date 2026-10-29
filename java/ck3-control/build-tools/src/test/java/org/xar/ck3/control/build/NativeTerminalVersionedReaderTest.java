package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;

/** Preserved C16 bytes are tool observations, never current Java invocation qualification. */
final class NativeTerminalVersionedReaderTest {
    @Test void exactHistoricalTwentySixFieldsKeepBothRawReferencesAndExplicitObservationScope() throws Exception {
        byte[] terminal=resource("terminal"),request=resource("request");
        assertEquals("6b585e703816a12005a146ecf00ecaf07fc388922b938cd297a39dd51acad7f7",sha(terminal));
        assertEquals("2b095825ed044c50704a4677e2c7c00e8815023621b1fa2aeb981cb666b5bef3",sha(request));
        var decoded=SharedOwnedCommand.decodeNativeTerminal(terminal,request);
        assertEquals(SharedOwnedCommand.NativeTerminalVersion.V2_ORIGINAL_26_FIELDS,decoded.version());
        assertEquals(SharedOwnedCommand.NativeTerminalScope.OWNED_TOOL_PROCESS_OBSERVATION_NOT_JAVA_INVOCATION_CUSTODY,decoded.scope());
        var originals=decoded.originalReferences(); var mapper=ControlBuild.strictMapper();
        assertEquals(mapper.readTree(request).get("launcher_source_ref").get("path").textValue(),originals.requestLauncher().path());
        assertEquals(mapper.readTree(terminal).get("launcher_source_ref").get("path").textValue(),originals.terminalLauncher().path());
        assertNotEquals(originals.requestLauncher(),originals.terminalLauncher());
        assertEquals(originals.requestStanding(),originals.terminalStanding());
        assertEquals(SharedOwnedCommand.NativePathRelation.HISTORICAL_WINDOWS_SPELLING_NOT_FILE_ID_OR_CURRENT_SOURCE,originals.relation());
        assertTrue(decoded.terminal().child().identity().executable().endsWith("javac.exe"));
        assertNull(decoded.request().javaInvocation());
        assertThrows(IOException.class,()->mapper.readValue(terminal,SharedOwnedCommand.Terminal.class));
        assertEquals("6b585e703816a12005a146ecf00ecaf07fc388922b938cd297a39dd51acad7f7",sha(terminal));
    }

    @Test void versionFieldSetTypesAndOriginalRequestDigestRemainStrict() throws Exception {
        var mapper=ControlBuild.strictMapper(); byte[] original=resource("terminal"),request=resource("request");
        for(String missing:new String[]{"schema","standing_ref","child","game_rpc_calls"}) {
            ObjectNode node=(ObjectNode)mapper.readTree(original); node.remove(missing);
            assertThrows(IOException.class,()->SharedOwnedCommand.decodeNativeTerminal(mapper.writeValueAsBytes(node),request),missing);
        }
        for(String badSchema:new String[]{"xar.shared-owned-command-terminal/v1","xar.shared-owned-command-terminal/v3","future"}) {
            ObjectNode node=(ObjectNode)mapper.readTree(original); node.put("schema",badSchema);
            assertThrows(IOException.class,()->SharedOwnedCommand.decodeNativeTerminal(mapper.writeValueAsBytes(node),request));
        }
        ObjectNode unknown=(ObjectNode)mapper.readTree(original); unknown.put("legacy_ok",true);
        assertThrows(IOException.class,()->SharedOwnedCommand.decodeNativeTerminal(mapper.writeValueAsBytes(unknown),request));
        ObjectNode integer=(ObjectNode)mapper.readTree(original); integer.put("game_rpc_calls",false);
        assertThrows(IOException.class,()->SharedOwnedCommand.decodeNativeTerminal(mapper.writeValueAsBytes(integer),request));
        ObjectNode wrongBytes=(ObjectNode)mapper.readTree(original);
        ((ObjectNode)wrongBytes.get("request_ref")).put("bytes",request.length+1L);
        assertThrows(IOException.class,()->SharedOwnedCommand.decodeNativeTerminal(mapper.writeValueAsBytes(wrongBytes),request));
        byte[] changed=request.clone(); changed[changed.length-1]^=1;
        assertThrows(IOException.class,()->SharedOwnedCommand.decodeNativeTerminal(original,changed));
        assertThrows(IOException.class,()->SharedOwnedCommand.decodeNativeTerminal(
                (new String(original,java.nio.charset.StandardCharsets.UTF_8)+" {}").getBytes(java.nio.charset.StandardCharsets.UTF_8),request));
    }

    @Test void nativeCompatibilityCannotAdmitJavaChildOrCurrentJavaEvidenceOrDifferentAuthority() throws Exception {
        var mapper=ControlBuild.strictMapper(); byte[] original=resource("terminal"),request=resource("request");
        ObjectNode evidence=(ObjectNode)mapper.readTree(original);
        evidence.set("java_invocation_evidence_ref",evidence.get("request_ref"));
        assertThrows(IOException.class,()->SharedOwnedCommand.decodeNativeTerminal(mapper.writeValueAsBytes(evidence),request));
        for(String image:new String[]{"C:/jdk-21/bin/java.exe","C:/jdk-21/bin/javaw.exe"}) {
            ObjectNode nativeRequest=(ObjectNode)mapper.readTree(request);
            ((ObjectNode)nativeRequest.get("executable")).put("path",image);
            byte[] requestBytes=mapper.writeValueAsBytes(nativeRequest);
            ObjectNode terminal=(ObjectNode)mapper.readTree(original);
            ((ObjectNode)terminal.get("request_ref")).put("bytes",requestBytes.length).put("sha256",sha(requestBytes));
            ((ObjectNode)terminal.get("child").get("identity")).put("executable",image);
            assertThrows(IOException.class,()->SharedOwnedCommand.decodeNativeTerminal(mapper.writeValueAsBytes(terminal),requestBytes));
        }
        ObjectNode crossed=(ObjectNode)mapper.readTree(original);
        ((ObjectNode)crossed.get("standing_ref")).put("path","D:/different-authority.json");
        assertThrows(IOException.class,()->SharedOwnedCommand.decodeNativeTerminal(mapper.writeValueAsBytes(crossed),request));
        ObjectNode launcher=(ObjectNode)mapper.readTree(original);
        ((ObjectNode)launcher.get("launcher_source_ref")).put("sha256","0".repeat(64));
        assertThrows(IOException.class,()->SharedOwnedCommand.decodeNativeTerminal(mapper.writeValueAsBytes(launcher),request));
        ObjectNode nullable=(ObjectNode)mapper.readTree(original);
        nullable.putNull("java_invocation_evidence_ref"); nullable.putNull("auxiliary_cleanup");
        // A new explicit shape cannot borrow the historical spelling exception.
        assertThrows(IOException.class,()->SharedOwnedCommand.decodeNativeTerminal(mapper.writeValueAsBytes(nullable),request));
    }

    private static byte[] resource(String kind) throws IOException {
        try(var input=NativeTerminalVersionedReaderTest.class.getResourceAsStream("/nativefixture/actual-owned-command-"+kind+"-v2.json")) {
            if(input==null) throw new IOException("Preserved original C16 evidence missing: "+kind);
            return input.readAllBytes();
        }
    }
    private static String sha(byte[] bytes) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
}
