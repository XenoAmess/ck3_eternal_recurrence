package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Replays the actual producer's original callback envelope; it has no SDK result_type field. */
final class OriginalRollbackPlanProducerTest {
    @Test void originalBeforeSubmitProducerDoesNotInventSdkResultType()throws Exception {
        ObjectNode original=original();
        assertFalse(original.get("result").has("result_type"));
        var body=OriginalRollbackInventory.plannedBody(original);
        assertEquals("planned",body.get("status").textValue());assertFalse(body.get("plan").isEmpty());
        ObjectNode redecoded=(ObjectNode)StrictJson.parse(StrictJson.canonical(original));
        assertEquals(body,OriginalRollbackInventory.plannedBody(redecoded));
        assertFalse(redecoded.get("result").has("result_type"),"pure parsing cannot alter the retained actual wire");
    }
    @Test void callbackAckMalformedNullAndEmptyPlanCannotQualifyTheActualPlan()throws Exception {
        ObjectNode original=original();
        for(var bad:java.util.List.of(StrictJson.object().put("is_error",true),StrictJson.object().put("is_error",0),StrictJson.object().put("is_error","false"))) {
            ObjectNode row=original.deepCopy();row.set("result",bad);assertThrows(IllegalArgumentException.class,()->OriginalRollbackInventory.plannedBody(row));
        }
        ObjectNode nil=original.deepCopy();((ObjectNode)nil.get("result")).putNull("structured_content");assertThrows(IllegalArgumentException.class,()->OriginalRollbackInventory.plannedBody(nil));
        ObjectNode empty=original.deepCopy();((ObjectNode)empty.get("result").get("structured_content")).set("plan",StrictJson.object());assertThrows(IllegalArgumentException.class,()->OriginalRollbackInventory.plannedBody(empty));
    }
    private static ObjectNode original()throws Exception {
        try(var input=OriginalRollbackPlanProducerTest.class.getResourceAsStream("/org/xar/ck3/control/service/root/decision-callback-original.json")) {
            assertNotNull(input,"exact retained producer fixture must be present");return (ObjectNode)StrictJson.parse(input.readAllBytes());
        }
    }
}
