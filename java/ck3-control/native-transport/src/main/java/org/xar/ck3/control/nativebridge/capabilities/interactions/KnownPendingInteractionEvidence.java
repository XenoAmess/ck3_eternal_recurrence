package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.OrdinaryHistory;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.warexit.WarExitEvidence;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleaseCollectionProjection12003;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Actual expanded history producer -> full strict native codec -> the known reply consumer. */
public final class KnownPendingInteractionEvidence {
    public record Current(PendingContext value, OpportunityJson.Obj originalWrapper) { }
    private KnownPendingInteractionEvidence() { }

    public static Optional<Current> pending(PlanningRequest request,Context held) {
        PendingSummary pending=held.controls().pending(); if(pending==null)return Optional.empty();
        List<OpportunityJson.Obj> history=OrdinaryHistory.collect(request.observations().history()).rows();
        for(int index=history.size()-1;index>=0;index--) {
            OpportunityJson.Obj row=history.get(index);
            if(!OrdinaryHistory.successful(row)||!OrdinaryHistory.effectiveCommand(row).filter(PendingContextCodec.STEP::equals).isPresent())continue;
            Optional<OpportunityJson.Obj> effective=OrdinaryHistory.effectiveCommandResult(row);
            if(effective.isEmpty())continue;
            ObjectNode result=InteractionArguments.parseApp(effective.orElseThrow());
            JsonNode context=result.get("pending_character_interaction_context");
            if(context==null||!context.isObject()||!same(result,request)
                    ||!equalText(result.get("step"),PendingContextCodec.STEP)
                    ||!equalBoolean(result.get("accepted"),true)
                    ||!java.util.Objects.equals(result.get("status"),context.get("status"))
                    ||!equalInt(context.get("pending_interaction_id"),BigInteger.valueOf(pending.instance().value()))
                    ||!equalInt(result.get("snapshot_revision"),held.revision())
                    ||!equalInt(context.get("snapshot_revision"),held.revision())
                    ||!equalInt(context.get("date_raw"),held.date()))continue;
            // Do not catch strict decoder failures as an absent observation: malformed current data is a real boundary error.
            PendingContext decoded=PendingContextCodec.decode(new RawJson(OpportunityJson.encode(effective.orElseThrow())),held,pending.instance());
            return Optional.of(new Current(decoded,effective.orElseThrow()));
        }
        return Optional.empty();
    }

    public static Optional<ReleaseCollectionProjection12003.Observation> prisoners(PlanningRequest request,Context held,long prisoner) {
        if(prisoner<=0||prisoner==held.actor().longValueExact())return Optional.empty();
        List<OpportunityJson.Obj> history=OrdinaryHistory.collect(request.observations().history()).rows();
        for(int index=history.size()-1;index>=0;index--) {
            OpportunityJson.Obj row=history.get(index);
            if(!OrdinaryHistory.successful(row))continue;
            Optional<OpportunityJson.Obj> effective=OrdinaryHistory.effectiveCommandResult(row);
            if(effective.isEmpty())continue;
            ObjectNode result=InteractionArguments.parseApp(effective.orElseThrow());
            if(!equalText(result.get("step"),"query-player-prisoner-collection-private-v1")||!equalText(result.get("status"),"available")
                    ||!same(result,request)||!equalInt(result.get("snapshot_revision"),held.revision()))continue;
            JsonNode collection=result.get("player_prisoner_collection");
            if(collection==null||!collection.isObject()||!equalInt(collection.get("snapshot_revision"),held.revision())
                    ||!equalInt(collection.get("date_raw"),held.date()))continue;
            var build=ReleaseCollectionProjection12003.SupportedBuild.exact(held.build().version(),held.build().sha256());
            return Optional.of(ReleaseCollectionProjection12003.decode(OpportunityJson.encode(effective.orElseThrow()),build,
                    new FrameBinding(held.revision(),held.date().intValueExact(),held.actor().longValueExact(),prisoner)));
        }
        return Optional.empty();
    }

    /** The original signature preserves explicit null leader/opponent and all target IDs, and sorts only by WarID. */
    public static Optional<List<KnownPendingInteractionRules.WarSignature>> warSignature(ObjectNode snapshot) {
        JsonNode rows=snapshot.get("active_wars"); if(rows==null||!rows.isArray())return Optional.empty();
        List<KnownPendingInteractionRules.WarSignature> signatures=new ArrayList<>();
        for(JsonNode row:rows) {
            if(!row.isObject()||!integral(row.get("war_id"))||row.get("war_id").bigIntegerValue().signum()<=0
                    ||!row.get("war_id").canConvertToInt()||!integral(row.get("player_relative_war_score"))
                    ||!row.get("player_relative_war_score").canConvertToInt())return Optional.empty();
            String side=nullableString(row.get("player_side"));
            if(!"attacker".equals(side)&&!"defender".equals(side))return Optional.empty();
            JsonNode primary=row.get("player_is_primary_war_leader"),opponent=row.get("primary_opponent_character_id"),targets=row.get("targeted_title_ids");
            if(primary!=null&&!primary.isNull()&&!primary.isBoolean()
                    ||opponent!=null&&!opponent.isNull()&&(!integral(opponent)||!opponent.canConvertToInt()||opponent.intValue()<0)
                    ||targets==null||!targets.isArray())return Optional.empty();
            List<Integer> titleIds=new ArrayList<>();
            for(JsonNode target:targets) {
                if(!integral(target)||!target.canConvertToInt()||target.intValue()<0)return Optional.empty();
                titleIds.add(target.intValue());
            }
            signatures.add(new KnownPendingInteractionRules.WarSignature(row.get("war_id").intValue(),
                    "attacker".equals(side)?WarExitEvidence.Side.ATTACKER:WarExitEvidence.Side.DEFENDER,
                    primary==null||primary.isNull()?null:primary.booleanValue(),
                    opponent==null||opponent.isNull()?null:opponent.intValue(),row.get("player_relative_war_score").intValue(),titleIds));
        }
        signatures.sort(Comparator.comparingInt(KnownPendingInteractionRules.WarSignature::warId));
        return Optional.of(List.copyOf(signatures));
    }

    public static boolean same(ObjectNode result,PlanningRequest request) {
        return equalText(result.get("queried_snapshot_id"),request.before().frame().snapshotId())
                &&equalInt(result.get("queried_revision"),request.before().frame().revision())
                &&equalInt(result.get("queried_native_revision"),request.before().frame().identity().nativeRevision());
    }
    static boolean integral(JsonNode n) { return n!=null&&n.isIntegralNumber(); }
    static boolean equalInt(JsonNode n,BigInteger value) { return integral(n)&&n.bigIntegerValue().equals(value); }
    static boolean equalText(JsonNode n,String value) { return n!=null&&n.isTextual()&&n.textValue().equals(value); }
    static boolean equalBoolean(JsonNode n,boolean value) { return n!=null&&n.isBoolean()&&n.booleanValue()==value; }
    static String nullableString(JsonNode n) { return n!=null&&n.isTextual()?n.textValue():null; }
}

