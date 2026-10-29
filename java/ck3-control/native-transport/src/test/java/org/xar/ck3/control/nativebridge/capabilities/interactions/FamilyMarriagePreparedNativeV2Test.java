package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageSendReads.*;

/** Actual native WritePrepared(v2) output to the unique Java consumer; software values grant no builder/Game source authority. */
final class FamilyMarriagePreparedNativeV2Test {
    private static final int MAX_STDOUT_BYTES=1_048_576;
    private static String stdout;
    @BeforeAll static void actualNativePreparedSerializer() throws Exception {
        Path executable=verifiedExecutable();
        Process process=new ProcessBuilder(executable.toString()).directory(executable.getParent().toFile()).redirectErrorStream(true).start();
        if(!process.waitFor(30,TimeUnit.SECONDS)){
            process.destroyForcibly();process.waitFor(5,TimeUnit.SECONDS);
            throw new AssertionError("actual native Prepared(v2) serializer fixture timed out");
        }
        byte[] bytes=process.getInputStream().readNBytes(MAX_STDOUT_BYTES+1);
        assertEquals(0,process.exitValue(),new String(bytes,StandardCharsets.UTF_8));
        assertTrue(bytes.length>0&&bytes.length<=MAX_STDOUT_BYTES,"bounded original native stdout required");
        stdout=new String(bytes,StandardCharsets.UTF_8);
        assertEquals(executable,verifiedExecutable(),"exact executable must remain unchanged after actual execution");
    }
    @Test void nativeSelectedAndEffectiveBitsStayIndependentThroughStrictJavaAndJsonRoundTrip() {
        var optionOff=packet("FAMILY_PREPARED_SELECTED_FALSE_EFFECTIVE_TRUE");
        var optionOn=packet("FAMILY_PREPARED_SELECTED_TRUE_EFFECTIVE_FALSE");
        var off=assertInstanceOf(Prepared.class,FamilyMarriageSendReads.prepared(optionOff));
        var on=assertInstanceOf(Prepared.class,FamilyMarriageSendReads.prepared(optionOn));
        assertFalse(off.matrilineal());assertEquals(Optional.of(true),off.effectiveMatrilineal());
        assertTrue(on.matrilineal());assertEquals(Optional.of(false),on.effectiveMatrilineal());
        assertEquals(off,FamilyMarriageSendReads.prepared(StrictJson.parse(StrictJson.canonical(optionOff,MAX_STDOUT_BYTES),MAX_STDOUT_BYTES)));
        assertEquals(on,FamilyMarriageSendReads.prepared(StrictJson.parse(StrictJson.canonical(optionOn,MAX_STDOUT_BYTES),MAX_STDOUT_BYTES)));
    }
    @Test void actualPublicNullAndUnavailableNullRemainDifferentFromFalseEffectiveOutcome() {
        var available=assertInstanceOf(Prepared.class,FamilyMarriageSendReads.prepared(packet("FAMILY_PREPARED_PUBLIC_EFFECTIVE_NULL")));
        assertTrue(available.effectiveMatrilineal().isEmpty());
        var unavailable=packet("FAMILY_PREPARED_FRAME_UNAVAILABLE");
        assertInstanceOf(NotPrepared.class,FamilyMarriageSendReads.prepared(unavailable));
        assertTrue(unavailable.get("effective_matrilineal_if_accepted").isNull());
        var invented=unavailable.deepCopy().put("effective_matrilineal_if_accepted",false);
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageSendReads.prepared(invented));
        var missing=packet("FAMILY_PREPARED_SELECTED_FALSE_EFFECTIVE_TRUE");missing.remove("effective_matrilineal_if_accepted");
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageSendReads.prepared(missing));
        var wrong=packet("FAMILY_PREPARED_SELECTED_TRUE_EFFECTIVE_FALSE").put("effective_matrilineal_if_accepted",0);
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageSendReads.prepared(wrong));
        var old=packet("FAMILY_PREPARED_PUBLIC_EFFECTIVE_NULL").put("schema","ck3-marriage-materialized-send-context-12004-v1");
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageSendReads.prepared(old));
    }
    private static ObjectNode packet(String prefix) {
        List<String> lines=stdout.lines().filter(line->line.startsWith(prefix+" ")).toList();
        assertEquals(1,lines.size(),"actual fixture must emit exactly one "+prefix+" original");
        JsonNode result=StrictJson.parse(lines.getFirst().substring(prefix.length()+1).getBytes(StandardCharsets.UTF_8),MAX_STDOUT_BYTES);
        return assertInstanceOf(ObjectNode.class,result);
    }
    private static Path verifiedExecutable() throws Exception {
        Path path=Path.of(required("xar.family.prepared.native.fixture")).toAbsolutePath().normalize();
        assertTrue(Files.isRegularFile(path),"actual current-inputs native executable required");
        long bytes=Files.size(path);assertTrue(bytes>0&&bytes<=67_108_864,"bounded actual executable required");
        String expected=required("xar.family.prepared.native.fixture.sha256");
        assertTrue(expected.matches("[a-f0-9]{64}"),"canonical fixture SHA-256 required");
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        try(var input=Files.newInputStream(path)){
            byte[] buffer=new byte[8192];int count;while((count=input.read(buffer))!=-1)digest.update(buffer,0,count);
        }
        assertEquals(expected,HexFormat.of().formatHex(digest.digest()),"native serializer executable changed");return path;
    }
    private static String required(String property) {
        String value=System.getProperty(property);assertNotNull(value,"required current-inputs CI property: "+property);
        assertFalse(value.isBlank(),"required current-inputs CI property: "+property);return value;
    }
}
