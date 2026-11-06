package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

/** Request-header DATA only: no owner descriptor, writer, marker, attachment, custody, READ or launch is issued. */
class LoadedSavedEntryRoute94Test {
    @org.junit.jupiter.api.io.TempDir java.nio.file.Path directory;
    @Test void exactSchemasPreserveRetainedAndSelectPreentryWithoutMarkerInference() throws Exception {
        var retained=request("xar.java-loaded-saved-resume-request/v1");
        assertFalse(RootLoadedSavedResumeMain250.preentryRequest(retained));
        var preentry=retained.deepCopy();preentry.put("schema","xar.java-loaded-saved-preentry-request/v1");
        assertTrue(RootLoadedSavedResumeMain250.preentryRequest(preentry));
        assertEquals(7,retained.size());assertEquals(7,preentry.size());
        for(String field:new String[]{"machineId","sourceRuntimeConfiguration","newRuntimeConfiguration","sourceConfirmation","checkpointPair","ownerDirectory"})assertEquals(retained.get(field),preentry.get(field));
        assertFalse(RootLoadedSavedResumeMain250.preentryRequest(StrictJson.parse(StrictJson.canonical(retained),1024*1024)));
        assertTrue(RootLoadedSavedResumeMain250.preentryRequest(StrictJson.parse(StrictJson.canonical(preentry),1024*1024)));
        for(String bad:new String[]{"xar.java-loaded-saved-resume-request/v2","xar.java-loaded-saved-preentry-request/v2","xar.java-confirmed-saved-bootstrap-request/v1","preentry",""}) {
            var unknown=retained.deepCopy();unknown.put("schema",bad);
            assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.preentryRequest(unknown));
        }
        for(ObjectNode base:new ObjectNode[]{retained,preentry}) {
            var missing=base.deepCopy();missing.remove("sourceConfirmation");assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.preentryRequest(missing));
            var extra=base.deepCopy();extra.put("saved_entry_marker",true);assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.preentryRequest(extra));
            var implicit=base.deepCopy();implicit.put("entry_mode","PRE_ENTRY");assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.preentryRequest(implicit));
            var noSchema=base.deepCopy();noSchema.remove("schema");assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.preentryRequest(noSchema));
            var wrongType=base.deepCopy();wrongType.put("schema",false);assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.preentryRequest(wrongType));
        }
        assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.preentryRequest(com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode()));
        var passive=request("xar.java-loaded-saved-passive-observer-request/v1");
        assertEquals(0,RootLoadedSavedResumeMain250.requestMode(retained));
        assertEquals(1,RootLoadedSavedResumeMain250.requestMode(preentry));
        assertEquals(2,RootLoadedSavedResumeMain250.requestMode(passive));
        assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.preentryRequest(passive));
        var extraPassive=passive.deepCopy();extraPassive.put("entry_mode","PRE_ENTRY");
        assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.requestMode(extraPassive));
        var unknownPassive=passive.deepCopy();unknownPassive.put("schema","xar.java-loaded-saved-passive-observer-request/v2");
        assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.requestMode(unknownPassive));
        byte[] body="{\"type\":\"heartbeat\",\"protocol_version\":1,\"sequence\":7}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        byte[] packet=java.nio.ByteBuffer.allocate(body.length+4).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        byte[] original=packet.clone();
        var ref=RootLoadedSavedResumeMain250.writePassivePacket(directory,"heartbeat",packet);
        assertEquals(original.length,ref.bytes());assertEquals(org.xar.ck3.control.application.driver.DriverJson.sha256(original),ref.sha256());
        packet[4]^=1;assertArrayEquals(original,java.nio.file.Files.readAllBytes(java.nio.file.Path.of(ref.path())));
        assertThrows(java.nio.file.FileAlreadyExistsException.class,()->RootLoadedSavedResumeMain250.writePassivePacket(directory,"heartbeat",original));
        byte[] broken=original.clone();broken[0]^=1;
        assertThrows(java.io.IOException.class,()->RootLoadedSavedResumeMain250.writePassivePacket(directory,"error",broken));
        assertFalse(java.nio.file.Files.exists(directory.resolve("error.packet")));
        byte[] tooLarge=new byte[65537];java.nio.ByteBuffer.wrap(tooLarge).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(tooLarge.length-4);
        assertThrows(java.io.IOException.class,()->RootLoadedSavedResumeMain250.writePassivePacket(directory,"error",tooLarge));
        assertFalse(java.nio.file.Files.exists(directory.resolve("error.packet")));
        assertThrows(java.io.IOException.class,()->RootLoadedSavedResumeMain250.writePassivePacket(directory,"../escape",original));
        System.out.println("LOADED_SAVED_ROUTE_DATA_PASS originalV1Retained/explicitPreentrySameSevenFields/noUnknownSchema/noModeExtra/noMarkerInference/noMissingOrWrongType; actualCustody=false actualRoot=false actualREAD=false actualLaunch=false");
    }
    private static ObjectNode request(String schema) {
        var row=StrictJson.object().put("schema",schema).put("machineId","UNISSUED_HEADER_DATA_ONLY");
        var ref=new ExactRef("UNISSUED_HEADER_DATA_ONLY/not-a-real-material.json",2,"0".repeat(64));
        for(String field:new String[]{"sourceRuntimeConfiguration","newRuntimeConfiguration","sourceConfirmation","checkpointPair"})row.set(field,ref.toJson());
        row.put("ownerDirectory","UNISSUED_HEADER_DATA_ONLY/not-an-owner");return row;
    }
}
