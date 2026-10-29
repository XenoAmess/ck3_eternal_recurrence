package org.xar.ck3.control.application.planning.family;

import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.readiness.ReadinessAuthority.LeaseSnapshot;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** One native producer must rebuild its actual prepared wire and final terms from these original packets. */
public final class FamilyNativePreparation {
    private FamilyNativePreparation() { }
    public record MaterializedSend(long senderId,long recipientId,OptionalLong secondaryActorId,OptionalLong secondaryRecipientId,
            OptionalLong intermediaryId,int roleArity,ExactRef beforeRead) {
        public static final String SCHEMA="xar.java.family-materialized-send/v1";
        public MaterializedSend {
            character(senderId);character(recipientId);Objects.requireNonNull(secondaryActorId);Objects.requireNonNull(secondaryRecipientId);Objects.requireNonNull(intermediaryId);
            secondaryActorId.ifPresent(FamilyNativePreparation::character);secondaryRecipientId.ifPresent(FamilyNativePreparation::character);intermediaryId.ifPresent(FamilyNativePreparation::character);
            Objects.requireNonNull(beforeRead);StrictJson.require(roleArity==5&&beforeRead.bytes()>0,"only actual qualified five-role original before context is supported");
        }
        public Obj toJson() {
            var n=StrictJson.object().put("schema",SCHEMA).put("sender_id",senderId).put("recipient_id",recipientId).put("role_arity",roleArity);
            nullable(n,"secondary_actor_id",secondaryActorId);nullable(n,"secondary_recipient_id",secondaryRecipientId);nullable(n,"intermediary_id",intermediaryId);
            n.set("before_read",beforeRead.toJson());return DriverJson.object(StrictJson.canonical(n,16*1024),16*1024);
        }
        public static MaterializedSend fromJson(Obj value) {
            var n=StrictJson.object(DriverJson.toNode(value),Set.of("schema","sender_id","recipient_id","secondary_actor_id","secondary_recipient_id","intermediary_id","role_arity","before_read"));
            StrictJson.require(SCHEMA.equals(StrictJson.text(n.get("schema"))),"materialized send context version differs");
            return new MaterializedSend(StrictJson.integer(n.get("sender_id"),1,0xFFFF_FFFEL),StrictJson.integer(n.get("recipient_id"),1,0xFFFF_FFFEL),
                    optional(n.get("secondary_actor_id")),optional(n.get("secondary_recipient_id")),optional(n.get("intermediary_id")),
                    (int)StrictJson.integer(n.get("role_arity"),5,5),ExactRef.fromJson(n.get("before_read")));
        }
    }
    public record VerifiedBasis(Obj snapshot,FamilyPorts.BridgeIdentity bridgeIdentity,ExactRef snapshotEvidence,ExactRef bridgeEvidence,
            Optional<Obj> preparedPlan,Optional<MaterializedSend> materializedSend) {
        public VerifiedBasis {Objects.requireNonNull(snapshot);Objects.requireNonNull(bridgeIdentity);Objects.requireNonNull(snapshotEvidence);Objects.requireNonNull(bridgeEvidence);Objects.requireNonNull(preparedPlan);Objects.requireNonNull(materializedSend);}
        public VerifiedBasis(Obj snapshot,FamilyPorts.BridgeIdentity bridgeIdentity,ExactRef snapshotEvidence,ExactRef bridgeEvidence,Optional<Obj> preparedPlan) {
            this(snapshot,bridgeIdentity,snapshotEvidence,bridgeEvidence,preparedPlan,Optional.empty());
        }
        /** Original frame custody alone contains no prepared business plan. */
        public VerifiedBasis(Obj snapshot,FamilyPorts.BridgeIdentity bridgeIdentity,ExactRef snapshotEvidence,ExactRef bridgeEvidence) {
            this(snapshot,bridgeIdentity,snapshotEvidence,bridgeEvidence,Optional.empty(),Optional.empty());
        }
        public VerifiedBasis withMaterializedSend(MaterializedSend actual) {return new VerifiedBasis(snapshot,bridgeIdentity,snapshotEvidence,bridgeEvidence,preparedPlan,Optional.of(actual));}
    }
    @FunctionalInterface public interface Replay {
        VerifiedBasis replay(ActionCommand original,NativeRequest actualPrepared,ActionPorts.OutcomeArchive originalArchive)throws IOException;
    }
    /** Root supplies the actual current held frame originals, without another native query or independently created writer. */
    @FunctionalInterface public interface Origins {
        VerifiedBasis current(Session originalSession,LeaseSnapshot actualLease,ActionCommand actualCommand)throws IOException;
    }
    /** Capture the actual complete planning request; an intent or a reconstructed empty projection is insufficient. */
    @FunctionalInterface public interface PlanningOriginalCapture {
        void capture(org.xar.ck3.control.application.planning.PlanningRequest original,ActionCommand actualCommand)throws IOException;
    }
    /** A transport view never grants qualification; every native preparation must retain this immutable gameplay frame. */
    public static void requireCommandFrame(ActionCommand command,Obj snapshot) {
        Objects.requireNonNull(command);Objects.requireNonNull(snapshot);
        var frame=command.before().frame();var identity=frame.identity();
        if(!(command.origin() instanceof CommandOrigin.Gameplay)
                || !Objects.equals(snapshot.get("snapshot_id"),new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text(frame.snapshotId()))
                || !Objects.equals(snapshot.get("episode_run_id"),new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text(frame.episodeRunId()))
                || !Objects.equals(snapshot.get("revision"),new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(frame.revision()))
                || !Objects.equals(snapshot.get("native_revision"),new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(identity.nativeRevision()))
                || !Objects.equals(snapshot.get("date_raw"),new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(identity.dateRaw()))
                || !Objects.equals(org.xar.ck3.control.planning.opportunity.OpportunityJson.object(snapshot.get("played_character"),"played_character").get("character_id"),
                        new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(identity.player()))
                || !new org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool(true).equals(snapshot.get("paused"))
                || !new org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool(true).equals(snapshot.get("map_ready")))
            throw new IllegalArgumentException("actual family preparation crossed its immutable gameplay command frame");
    }
    private static void character(long value) {StrictJson.require(value>0&&value<0xFFFF_FFFFL,"full actual native character ID required");}
    private static OptionalLong optional(com.fasterxml.jackson.databind.JsonNode value) {return value.isNull()?OptionalLong.empty():OptionalLong.of(StrictJson.integer(value,1,0xFFFF_FFFEL));}
    private static void nullable(com.fasterxml.jackson.databind.node.ObjectNode n,String key,OptionalLong value) {if(value.isPresent())n.put(key,value.getAsLong());else n.putNull(key);}
}
