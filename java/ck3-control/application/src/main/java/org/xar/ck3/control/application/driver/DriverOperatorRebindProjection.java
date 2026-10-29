package org.xar.ck3.control.application.driver;

import java.util.LinkedHashMap;
import java.util.Map;
import org.xar.ck3.control.application.capabilities.DriverRuntimeCapabilities;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure proposal only. The installed original-ACK/Window source and the sole CAS supply publication authority. */
public final class DriverOperatorRebindProjection {
    private DriverOperatorRebindProjection(){ }
    public static OperatorPlayerSwitch.Replacement propose(DriverSnapshotFacts.Known before,OperatorPlayerSwitch.Request request) {
        return propose(before.driver(),before.auxiliary(),request);
    }
    public static OperatorPlayerSwitch.Replacement propose(org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete before,
            OpportunityJson.Obj auxiliary,OperatorPlayerSwitch.Request request) {
        var original=OperatorPlayerSwitch.replacement(before,auxiliary,request);
        if(!original.rebindPerformed())return original;
        // Clear the existing fixed semantic slots and their receipt tables through their sole owner.
        var fields=new LinkedHashMap<>(DriverSemanticReadState.initializeFresh(original.auxiliary()).members());
        fields.put(DriverRuntimeCapabilities.AUXILIARY_KEY,OpportunityJson.Nil.INSTANCE);
        fields.put("capability_observed_native_source",OpportunityJson.Nil.INSTANCE);
        fields.put("campaign_root_context_query",OpportunityJson.Nil.INSTANCE);
        fields.put("independent_battle_speed_readiness",OpportunityJson.Nil.INSTANCE);
        fields.put("capability_read_sources",new OpportunityJson.Obj(Map.of("marriage",OpportunityJson.Nil.INSTANCE,"campaign_root",OpportunityJson.Nil.INSTANCE)));
        for(String key:java.util.List.of("capability_retreat_source","capability_succession_source","capability_marriage_attempt_source",
                "capability_independent_source",DriverPreclockExpectationProducer.SOURCE_KEY))fields.remove(key);
        return new OperatorPlayerSwitch.Replacement(original.driver(),new OpportunityJson.Obj(fields),true);
    }
}
