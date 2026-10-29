package org.xar.ck3.control.application.lifecycle;

import com.fasterxml.jackson.databind.JsonNode;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** The lifecycle proof's declared full-material budget, without widening the small generic JSON boundary. */
public final class LifecycleProofMaterialJson {
    private LifecycleProofMaterialJson() { }
    public static JsonNode proof(byte[] original) {return bounded(original,LifecycleProofCodec.MAX_PROOF_BYTES);}
    public static JsonNode result(byte[] original) {return bounded(original,LifecycleProofCodec.MAX_RESULT_BYTES);}
    static JsonNode bounded(byte[] original,int limit) {
        StrictJson.require(limit>0&&limit<=DriverJson.MAX_NATIVE_BYTES,"explicit lifecycle full-material budget required");
        return OpportunityJson.toNode(DriverJson.object(original,limit));
    }
}
