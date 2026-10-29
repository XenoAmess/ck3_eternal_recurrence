package org.xar.ck3.control.nativebridge.capabilities.religion;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionService;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionTemporalFinance.Frame;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionTemporalFinance.*;

/** Public typed access to the sole original decoder. This bridge grants no source or read admission. */
public final class EpidemicOriginalDecoder {
    private EpidemicOriginalDecoder(){ }
    public static ReligionModels.EpidemicResult decode(PlanningReadReceipt original,int requestedTitle,BigInteger expectedEvent){
        return ObservationDecoders.epidemic(original,requestedTitle,expectedEvent);
    }
    /** Actual read caller decodes before presentation; this pure projection never grants read or event qualification. */
    public static ObjectNode publicResult(ObjectNode actualEnvelope,Frame frame,BigInteger expectedEvent){
        var business=actualEnvelope.deepCopy();
        need(expectedEvent==null||expectedEvent.signum()>0&&expectedEvent.compareTo(I32_MAX)<=0,"actual event identity must be positive signed32");
        need(text(business,"step").startsWith("query-player-epidemic-recovery-v1"),"not an original epidemic query");
        yes(business,"accepted");yes(business,"private_build");yes(business,"read_only");no(business,"advertised");
        eq(business,"backend_id","native-headless");eq(business,"snapshot_revision",frame.nativeRevision());
        var body=object(business.get("player_epidemic_recovery"));
        eq(body,"schema","player-epidemic-recovery-v1");eq(body,"schema_version",BigInteger.ONE);
        eq(body,"snapshot_revision",frame.nativeRevision());eq(body,"date_raw",frame.date());eq(body,"played_character_id",frame.actor());
        metadata(business,frame);if(expectedEvent==null)business.putNull("queried_event_instance_id");else business.put("queried_event_instance_id",expectedEvent);
        for(String key:java.util.List.of("query_sequence","observation_revision","snapshot_revision"))u64(business,key,1);
        u64(body,"snapshot_revision",1);return business;
    }
    public static ObjectNode publicResult(PlanningReadReceipt actual,int requestedTitle,BigInteger expectedEvent){
        decode(actual,requestedTitle,expectedEvent);
        return publicResult(ReligionService.originalResult(actual),Frame.from(actual),expectedEvent);
    }
}
