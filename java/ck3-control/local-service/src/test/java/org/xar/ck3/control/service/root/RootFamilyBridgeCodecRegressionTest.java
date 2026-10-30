package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ArrayNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Production Complete assembler -> small manifest codec -> typed semantic consumer, without a physical lease. */
final class RootFamilyBridgeCodecRegressionTest {
    @TempDir Path temporary;

    @Test void rebuiltCompletePublishesAndDecodesTheSmallManifestWithoutBorrowingTheFullFrameBudget()throws Exception {
        var input=PortableFamilyFrame.materialize(temporary);var frame=input.frame();
        assertTrue(input.originalSemantic().length>StrictJson.INPUT_MAX_BYTES);
        byte[] encoded=RootFamilyBridge.encodeManifest(frame,input.semantic());
        assertTrue(encoded.length<StrictJson.INPUT_MAX_BYTES);var decoded=RootFamilyBridge.decodeManifest(encoded);
        assertEquals(RootFamilyBridge.SCHEMA,decoded.path("schema").textValue());
        assertTrue(RootFamilyBridge.matchesPersistedGame(decoded.get("game"),frame.identity().game()));
        assertEquals(frame.identity().game().pid(),StrictJson.integer(decoded.get("bridge_pid"),1,0xffff_ffffL));
        assertEquals(RootFamilyBridge.creationToken(frame.identity().game()),decoded.path("bridge_creation_date").textValue());
        var basis=NativeEffectEvidence.basis(frame);
        assertEquals(basis.nativeFrame(),ExactRef.fromJson(decoded.get("native_frame")));
        assertEquals(basis.driverFacts(),ExactRef.fromJson(decoded.get("driver_facts")));
        assertEquals(input.semantic(),ExactRef.fromJson(decoded.get("semantic")));
        assertTrue(RootFamilyBridge.matchesSemantic(frame,input.originalSemantic()));
        assertThrows(IllegalArgumentException.class,()->StrictJson.canonical(decoded,DriverJson.MAX_NATIVE_BYTES),"old producer's explicit maximum is outside the receipt API even for this small body");
        assertThrows(IllegalArgumentException.class,()->StrictJson.parse(encoded,DriverJson.MAX_NATIVE_BYTES));
    }

    @Test void semanticComparisonIgnoresObjectOrderButRejectsChangedValuesIdentityTypesAndArrayOrder()throws Exception {
        var input=PortableFamilyFrame.materialize(temporary);var frame=input.frame();
        var original=DriverJson.toNode(DriverJson.object(input.originalSemantic(),DriverJson.MAX_NATIVE_BYTES));
        var reordered=StrictJson.object();var names=new java.util.ArrayList<String>();original.fieldNames().forEachRemaining(names::add);
        java.util.Collections.reverse(names);for(String name:names)reordered.set(name,original.get(name));
        assertTrue(RootFamilyBridge.matchesSemantic(frame,DriverJson.encodeNode(reordered)));
        for(String identity:List.of("revision","native_revision")) {
            var wrong=((com.fasterxml.jackson.databind.node.ObjectNode)original).deepCopy();wrong.put(identity,true);
            assertFalse(RootFamilyBridge.matchesSemantic(frame,DriverJson.encodeNode(wrong)));
        }
        var changed=((com.fasterxml.jackson.databind.node.ObjectNode)original).deepCopy();changed.put("paused",false);
        assertFalse(RootFamilyBridge.matchesSemantic(frame,DriverJson.encodeNode(changed)));
        var rows=(ArrayNode)changed.get("native_command_history");assertTrue(rows.size()>1);
        changed=((com.fasterxml.jackson.databind.node.ObjectNode)original).deepCopy();rows=(ArrayNode)changed.get("native_command_history");
        var first=rows.get(0).deepCopy();var last=rows.get(rows.size()-1).deepCopy();assertNotEquals(first,last);
        rows.set(0,last);rows.set(rows.size()-1,first);
        assertFalse(RootFamilyBridge.matchesSemantic(frame,DriverJson.encodeNode(changed)));
    }

    @Test void manifestCodecRejectsWrongSchemaShapeMalformedUtf8AndReceiptOverflow()throws Exception {
        var input=PortableFamilyFrame.materialize(temporary);byte[] original=RootFamilyBridge.encodeManifest(input.frame(),input.semantic());
        var wrong=RootFamilyBridge.decodeManifest(original);wrong.put("schema","other-schema");
        assertThrows(IllegalArgumentException.class,()->RootFamilyBridge.decodeManifest(StrictJson.canonical(wrong)));
        var extra=RootFamilyBridge.decodeManifest(original);extra.put("extra",true);
        assertThrows(IllegalArgumentException.class,()->RootFamilyBridge.decodeManifest(StrictJson.canonical(extra)));
        for(byte[] bad:List.of("{\"schema\":1,\"schema\":2}".getBytes(StandardCharsets.UTF_8),new byte[]{(byte)0xc3,0x28},
                "{} {}".getBytes(StandardCharsets.UTF_8),new byte[StrictJson.INPUT_MAX_BYTES+1]))
            assertThrows(IllegalArgumentException.class,()->RootFamilyBridge.decodeManifest(bad));
    }
}
