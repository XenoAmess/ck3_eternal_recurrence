package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.OptionalLong;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Actual source-pinned C++ synthetic-memory producer to the sole Java codec. Zero native Game or source-admission credit. */
final class FamilyOutgoingNativeV4Test {
    private static final String EXECUTABLE="xar.family.outgoing.v4.native.fixture";
    private static final String EXECUTABLE_SHA="xar.family.outgoing.v4.native.fixture.sha256";
    private static final int MAX_STDOUT_BYTES=65_536;
    private static final Frame FRAME=new Frame(BigInteger.ONE,BigInteger.valueOf(100),BigInteger.valueOf(1001),Build.CROZIER4,BigInteger.ONE);
    private static JsonNode original;

    @BeforeAll static void actualNativeScannerAndSerializer() throws Exception {
        Path executable=verifiedExecutable();
        Process process=new ProcessBuilder(executable.toString()).directory(executable.getParent().toFile()).redirectErrorStream(true).start();
        if(!process.waitFor(30,TimeUnit.SECONDS)){
            process.destroyForcibly();process.waitFor(5,TimeUnit.SECONDS);
            throw new AssertionError("actual pending-role v4 fixture timed out; no Java/native qualification recorded");
        }
        byte[] raw=process.getInputStream().readNBytes(MAX_STDOUT_BYTES+1);
        assertEquals(0,process.exitValue(),new String(raw,StandardCharsets.UTF_8));
        assertTrue(raw.length>0&&raw.length<=MAX_STDOUT_BYTES,"bounded original native fixture stdout required");
        original=StrictJson.parse(raw,MAX_STDOUT_BYTES);
        assertEquals(executable,verifiedExecutable(),"exact fixture bytes must remain unchanged after execution");
    }
    @Test void actualNativeV4ReadWriteFlowsThroughSharedJavaCodecWithoutManualFixtureReplacement() {
        var observed=FamilyOutgoingCodec.decodeGroup(original,FRAME,FamilyOutgoingCodec.Profile.ARRANGE_MARRIAGE);
        assertTrue(observed.complete());assertEquals(OptionalLong.of(1234),observed.definitionHash());
        assertEquals(OptionalLong.of(1001),observed.senderCharacterId());assertEquals(2,observed.scannedSlots().orElseThrow());
        assertEquals(List.of(1L),observed.occupiedPendingIds());assertEquals(1,observed.candidates().size());
        var candidate=observed.candidates().getFirst();assertEquals(1,candidate.pendingFullId());
        assertEquals(new FamilyOutgoingCodec.Roles(1001L,1002L,null,null,null),candidate.roles());
        assertEquals(List.of(new FamilyOutgoingCodec.OptionRow(0,303,1)),candidate.options());
        assertTrue(candidate.knownActiveRoute());
        var encoded=new RawJson(StrictJson.canonical(FamilyOutgoingCodec.encodeGroup(observed),MAX_STDOUT_BYTES));
        assertEquals(observed,FamilyOutgoingCodec.decodeGroup(encoded,FRAME,FamilyOutgoingCodec.Profile.ARRANGE_MARRIAGE));
        assertEquals(original,StrictJson.parse(encoded.bytes(),MAX_STDOUT_BYTES),"same agreed JSON type domain after serialization round-trip");
        assertFalse(original.toString().contains("sixth"),"actor shadow is not an additional public role");
    }
    @Test void sourceProfileWrongTypesAndMissingRolesCannotBeRequalifiedFromActualProducerOutput() {
        var legacy=((ObjectNode)original).deepCopy().put("schema","ck3-family-outgoing-storage-12004-v3");
        assertThrows(IllegalArgumentException.class,()->FamilyOutgoingCodec.decodeGroup(legacy,FRAME,FamilyOutgoingCodec.Profile.ARRANGE_MARRIAGE));
        var wrong=((ObjectNode)original).deepCopy().put("sender_character_id",true);
        assertThrows(IllegalArgumentException.class,()->FamilyOutgoingCodec.decodeGroup(wrong,FRAME,FamilyOutgoingCodec.Profile.ARRANGE_MARRIAGE));
        var missing=((ObjectNode)original).deepCopy();
        ((ObjectNode)missing.get("candidates").get(0).get("effective_roles")).remove("secondary_actor_id");
        assertThrows(IllegalArgumentException.class,()->FamilyOutgoingCodec.decodeGroup(missing,FRAME,FamilyOutgoingCodec.Profile.ARRANGE_MARRIAGE));
        var alias=((ObjectNode)original).deepCopy().put("role_arity_callback_qualified",true);
        assertThrows(IllegalArgumentException.class,()->FamilyOutgoingCodec.decodeGroup(alias,FRAME,FamilyOutgoingCodec.Profile.ARRANGE_MARRIAGE));
    }
    private static Path verifiedExecutable() throws Exception {
        Path path=Path.of(required(EXECUTABLE)).toAbsolutePath().normalize();
        assertTrue(Files.isRegularFile(path),"actual current-inputs native fixture file required");
        long bytes=Files.size(path);assertTrue(bytes>0&&bytes<=67_108_864,"bounded actual executable required");
        String expected=required(EXECUTABLE_SHA);assertTrue(expected.matches("[a-f0-9]{64}"),"canonical exact fixture SHA256 required");
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        try(var input=Files.newInputStream(path)){
            byte[] buffer=new byte[8192];int count;while((count=input.read(buffer))!=-1)digest.update(buffer,0,count);
        }
        assertEquals(expected,HexFormat.of().formatHex(digest.digest()),"actual native fixture changed");return path;
    }
    private static String required(String property) {
        String value=System.getProperty(property);assertNotNull(value,"required current-inputs CI property: "+property);
        assertFalse(value.isBlank(),"required current-inputs CI property: "+property);return value;
    }
}
