package org.xar.ck3.control.nativebridge.capabilities.religion;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.effects.NativeEventEffects.MaterialQuery;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.application.planning.events.EventReadBinding;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.eventmaterial.RiteGrowthMaterial;

/** One installed typed religion contract and argument producer for planning, after-read, and archive replay. */
public final class PlayerReligionEventBinding {
    private PlayerReligionEventBinding() { }
    public static EventReadBinding<PlayerReligionContextRead.Observation> bind(PlayerReligionContextRead actualRead) {
        Objects.requireNonNull(actualRead);
        var query=new MaterialQuery<>(actualRead.contract(),
            observation->new RawJson(StrictJson.canonical(PlayerReligionContextRead.flattened(observation))),
            semantic->new OpportunityJson.Obj(Map.of()));
        return new EventReadBinding<>(query,(request,observation)-> {
            ObjectNode queryResult=PlayerReligionContextRead.flattened(observation);
            ObjectNode snapshot=(ObjectNode)StrictJson.parse(OpportunityJson.encode(request.observations().snapshot()));
            var detached=RiteGrowthMaterial.observe(queryResult,snapshot);
            snapshot.set(RiteGrowthMaterial.SNAPSHOT_FIELD,StrictJson.parse(RiteGrowthMaterial.encode(detached)));
            return new EventPolicies.ReadPublication(object(queryResult),Optional.of(object(snapshot)));
        });
    }
    private static OpportunityJson.Obj object(ObjectNode value) {
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value)),"typed religion event publication");
    }
}
