package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.g2.m0.RaiktorExitPostwarEvidence;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;

/** Full legacy generic Driver result from the retained read only. Current .4 player-truce is a distinct contract.
 * The actual Root caller first performs its installed same-family read. This pure projection grants no read,
 * source, build or runtime authority, and never substitutes another native packet or issues a new query.
 */
public final class ArmyLegacyTruceResultCodec {
    private ArmyLegacyTruceResultCodec() { }
    public static RawJson encode(ArmyCalls.Truce call,ArmyTypes.Context context,PlanningReadReceipt original) {
        Objects.requireNonNull(call);Objects.requireNonNull(context);Objects.requireNonNull(original);
        require(call.method()==PublicMethod.QUERY_PLAYER_TRUCE_EXPIRY_V1,"selected actual-truce read required");
        call.revision().requireCurrent(context.before().frame().revision());
        require(original.request().arguments().equals(DriverJson.object(ArmyCallCodec.encode(call).bytes(),DriverJson.MAX_NATIVE_BYTES)),
                "legacy truce projection changed the original typed request");
        ObjectNode result=ArmyNativeReadEvidence.result(context,original).deepCopy();
        String step="query-raiktor-actual-truce-expiry-v1-"+call.toward().value();
        equal(get(result,"step"),step);
        // This original Python normalizer binds its historical backend; .4's extended DTO is never aliased.
        require(context.source().exactBuild().equals("1.19.0.6"),
                "original generic actual-truce proof unavailable for observed build "+context.source().exactBuild()+"; legacy requires 1.19.0.6 and its exact packet, current player-truce remains distinct");
        if(result.has("backend_id"))equal(get(result,"backend_id"),"native-headless");
        else result.put("backend_id","native-headless");
        var proof=RaiktorExitPostwarEvidence.normalizeLegacyTruce(result,call.toward().value(),context.nativeRevision());
        positive(get(result,"query_sequence"));
        equal(get(proof,"owner_character_id"),context.playerId());equal(get(proof,"current_date_raw"),context.dateRaw());
        result.set("actual_truce_expiry_proof",proof);
        return new RawJson(bytes(result));
    }
}
