package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

final class LifecycleProofMaterialJsonTest {
    @Test void declaredLifecycleBudgetsAcceptSmallOriginalsEvenThoughGenericJsonRefusesTheirLimit() {
        byte[] original="{\"committed_event_identity\":\"actual\"}".getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class,()->StrictJson.parse(original,LifecycleProofCodec.MAX_PROOF_BYTES));
        assertEquals("actual",LifecycleProofMaterialJson.proof(original).get("committed_event_identity").textValue());
        assertEquals(LifecycleProofMaterialJson.proof(original),LifecycleProofMaterialJson.result(original));
    }
    @Test void fullMaterialAboveGenericOneMiBLimitRoundTripsWithoutChangingDecimalIdentity() {
        var original=new OpportunityJson.Obj(Map.of("identity",new OpportunityJson.Text("9007199254740993"),
                "payload",new OpportunityJson.Text("x".repeat(StrictJson.EXPLICIT_MAX_BYTES+1))));
        byte[] bytes=DriverJson.encode(original);assertTrue(bytes.length>StrictJson.EXPLICIT_MAX_BYTES);
        var proof=LifecycleProofMaterialJson.proof(bytes);var result=LifecycleProofMaterialJson.result(bytes);
        assertEquals("9007199254740993",proof.get("identity").textValue());assertTrue(proof.get("identity").isTextual());
        assertEquals(proof,result);assertEquals(OpportunityJson.toNode(original),proof);
    }
    @Test void narrowBoundaryStillRejectsDuplicateFieldsBadUtf8WrongRootTrailingDataAndExceededBudget() {
        for(String invalid:new String[]{"{\"id\":1,\"id\":2}","[]","{}{}","{\"id\":true"})
            assertThrows(IllegalArgumentException.class,()->LifecycleProofMaterialJson.proof(invalid.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class,()->LifecycleProofMaterialJson.result(new byte[]{'{','"','x','"',':','"',(byte)0xff,'"','}'}));
        byte[] value="{\"x\":\"long\"}".getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class,()->LifecycleProofMaterialJson.bounded(value,value.length-1));
        assertThrows(IllegalArgumentException.class,()->LifecycleProofMaterialJson.bounded(value,DriverJson.MAX_NATIVE_BYTES+1));
    }
}
