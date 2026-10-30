package org.xar.ck3.control.events.vanilla;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.events.GuiAvailabilityObservation;

final class VanillaGuiAvailabilityTest {
    private static final ObjectMapper JSON=new ObjectMapper();
    private static ObjectNode request() throws Exception {
        try(InputStream input=VanillaGuiAvailabilityTest.class.getResourceAsStream("/vanilla/option-projection-golden-v1.json")) {
            assertNotNull(input);
            return ((ObjectNode)JSON.readTree(input).get("cases").get(0).get("request")).deepCopy();
        }
    }
    private static ObjectNode v2(boolean valid) throws Exception {
        ObjectNode raw=request();raw.put("schema_version",2);
        for(var value:raw.get("options")) ((ObjectNode)value).putObject("gui_availability").put("status","observed").put("is_valid",valid);
        return raw;
    }
    @Test void fullProjectionObservedFalseBlocksAndRetainsRawTrueInSerializedResult() throws Exception {
        var input=VanillaProjectionCodec.decode(JSON.writeValueAsBytes(v2(false)));
        var result=VanillaOptionProjection.project(input);
        assertEquals(VanillaOptionProjection.Status.BLOCKED,result.status());
        assertFalse(result.checks().get("selected_native_option_enabled"));
        assertTrue(result.selectedOption().enabled());
        var wire=JSON.readTree(VanillaProjectionCodec.encode(result));
        assertEquals(2,wire.get("schema_version").intValue());
        assertFalse(wire.get("selected_option").get("gui_availability").get("is_valid").booleanValue());
        assertEquals(input,VanillaProjectionCodec.decode(VanillaProjectionCodec.encode(input)));
    }
    @Test void observedTrueOverridesRawFalseAndUnobservedKeepsFallback() throws Exception {
        ObjectNode raw=v2(true);
        for(var value:raw.get("options")) ((ObjectNode)value).put("enabled",false);
        var input=VanillaProjectionCodec.decode(JSON.writeValueAsBytes(raw));
        assertEquals(VanillaOptionProjection.Status.PROJECTION_READY,VanillaOptionProjection.project(input).status());
        for(var value:raw.get("options")) ((ObjectNode)value).putObject("gui_availability").put("status","unobserved").put("reason","native_binding_unavailable");
        input=VanillaProjectionCodec.decode(JSON.writeValueAsBytes(raw));
        assertEquals(VanillaOptionProjection.Status.BLOCKED,VanillaOptionProjection.project(input).status());
        assertInstanceOf(GuiAvailabilityObservation.Unobserved.class,input.options().getFirst().guiAvailability());
    }
    @Test void strictVersionedWireRejectsMissingAndWrongShapesAndRetainsEmptyV2() throws Exception {
        ObjectNode raw=v2(true);((ObjectNode)raw.get("options").get(0)).remove("gui_availability");
        assertThrows(IllegalArgumentException.class,()->VanillaProjectionCodec.decode(JSON.writeValueAsBytes(raw)));
        ObjectNode wrong=v2(true);((ObjectNode)wrong.get("options").get(0).get("gui_availability")).put("is_valid",1);
        assertThrows(IllegalArgumentException.class,()->VanillaProjectionCodec.decode(JSON.writeValueAsBytes(wrong)));
        ObjectNode v1=v2(true);v1.put("schema_version",1);
        assertThrows(IllegalArgumentException.class,()->VanillaProjectionCodec.decode(JSON.writeValueAsBytes(v1)));
        ObjectNode empty=v2(true);empty.putArray("options");
        var decoded=VanillaProjectionCodec.decode(JSON.writeValueAsBytes(empty));
        assertEquals(2,decoded.schemaVersion());assertEquals(decoded,VanillaProjectionCodec.decode(VanillaProjectionCodec.encode(decoded)));
    }
}
