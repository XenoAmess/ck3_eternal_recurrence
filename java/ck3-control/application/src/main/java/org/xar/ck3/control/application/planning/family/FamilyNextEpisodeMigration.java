package org.xar.ck3.control.application.planning.family;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.Arrays;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Pure full-body NEXT bookkeeping. Only Root's private proof may authorize persistence of its output. */
public final class FamilyNextEpisodeMigration {
    public static final String FIELD="java_next_episode";
    public static final String SCHEMA="xar.java.family-next-episode-binding/v1";
    public record Episode(String runId,BigInteger player) {
        public Episode {StrictJson.text(runId);player=preservedPlayer(player);}
        public static Episode fromDriver(DriverStateSnapshot.Complete driver) {return new Episode(driver.session().episodeRunId(),driver.session().actorId());}
    }
    public record Transition(SessionIdentity beforeOwner,SessionIdentity afterOwner,Episode before,Episode after,
            ExactRef baselineMaterial,ExactRef previousBody) {
        public Transition {
            Objects.requireNonNull(beforeOwner);Objects.requireNonNull(afterOwner);Objects.requireNonNull(before);Objects.requireNonNull(after);
            Objects.requireNonNull(baselineMaterial);Objects.requireNonNull(previousBody);
            StrictJson.require(beforeOwner.machineId().equals(afterOwner.machineId())&&!beforeOwner.game().equals(afterOwner.game())
                    &&!before.runId().equals(after.runId())&&baselineMaterial.bytes()>0&&previousBody.bytes()>0,
                    "episode initialization requires a real different physical Game/episode and original full material");
        }
        public ObjectNode toJson() {
            var value=StrictJson.object().put("schema",SCHEMA);
            value.set("before_owner",OrdinaryCycleTransitions.sessionToJson(beforeOwner));value.set("after_owner",OrdinaryCycleTransitions.sessionToJson(afterOwner));
            value.set("before_episode",episode(before));value.set("after_episode",episode(after));
            value.set("baseline_material",baselineMaterial.toJson());value.set("previous_body",previousBody.toJson());return value;
        }
        public static Transition fromJson(JsonNode original) {
            var value=StrictJson.object(original,Set.of("schema","before_owner","after_owner","before_episode","after_episode","baseline_material","previous_body"));
            StrictJson.require(SCHEMA.equals(StrictJson.text(value.get("schema"))),"exact family NEXT binding schema required");
            return new Transition(OrdinaryCycleTransitions.sessionFromJson(value.get("before_owner")),OrdinaryCycleTransitions.sessionFromJson(value.get("after_owner")),
                    readEpisode(value.get("before_episode")),readEpisode(value.get("after_episode")),ExactRef.fromJson(value.get("baseline_material")),ExactRef.fromJson(value.get("previous_body")));
        }
    }
    /** Historical DATA keeps its original positive uint32 representation; current native IDs retain their sign. */
    static BigInteger preservedPlayer(BigInteger value) {
        Objects.requireNonNull(value);
        if(value.signum()>0&&value.compareTo(new BigInteger("4294967294"))<=0)return value;
        return NativeCharacterId.of(value).asBigInteger();
    }
    static BigInteger preservedPlayer(JsonNode value) {
        return preservedPlayer(StrictJson.integer(value,BigInteger.valueOf(Integer.MIN_VALUE),new BigInteger("4294967294")));
    }
    static BigInteger currentPlayer(JsonNode value) {
        return NativeCharacterId.fromJson(value).asBigInteger();
    }
    private FamilyNextEpisodeMigration() { }
    /** A FIRST restore reuses the original BASELINE input. It never archives an already initialized body twice. */
    public static void requireCompatibleCurrent(Slot slot,byte[] original,byte[] current,Transition desired) {
        FamilyDomainSource.validate(slot,current);
        if(Arrays.equals(original,current))return;
        JsonNode parsed=StrictJson.parse(current,ContinuityJson.DOMAIN_MAX_BYTES);
        StrictJson.require(parsed instanceof ObjectNode,"JSON object required for current family body");
        ObjectNode actual=(ObjectNode)parsed;
        StrictJson.require(actual.has(FIELD),"current family body is neither the actual BASELINE original nor its exact initialization");
        var prior=Transition.fromJson(actual.get(FIELD));
        StrictJson.require(prior.beforeOwner().equals(desired.beforeOwner())&&prior.before().equals(desired.before())&&prior.after().equals(desired.after())
                &&prior.baselineMaterial().equals(desired.baselineMaterial())&&prior.previousBody().equals(desired.previousBody()),
                "FIRST initialization cannot replace another original campaign or episode");
        StrictJson.require(Arrays.equals(current,derive(slot,original,prior)),"current family initialization contains unrelated changes or lost original records");
    }
    public static byte[] derive(Slot slot,byte[] original,Transition transition) {
        Objects.requireNonNull(transition);Obj validated=FamilyDomainSource.validate(slot,original);
        StrictJson.require(transition.previousBody().bytes()==original.length&&transition.previousBody().sha256().equals(org.xar.ck3.control.application.action.ActionCodec.sha256(original)),"full previous family body differs from its exact retained original");
        JsonNode parsed=DriverJson.toNode(validated);
        StrictJson.require(parsed instanceof ObjectNode,"JSON object required for original family body");
        ObjectNode before=(ObjectNode)parsed;ObjectNode after=before.deepCopy();
        FamilyNaturalEpisodeMigration.requireBeforeBinding(before,transition.beforeOwner(),transition.before());
        for(String key:List.of("pending","resolved")) {
            var value=before.get(key);StrictJson.require(value!=null&&(value.isNull()||value.isObject()),"full explicit family records required");
            if(value.isObject()) {
                StrictJson.require(transition.before().runId().equals(StrictJson.text(value.get("episode_run_id"))),"unrelated old episode record cannot become new clear state");
                if(value.has("played_character_id"))StrictJson.require(transition.before().player().equals(preservedPlayer(value.get("played_character_id"))),"old active family record has another actual player");
            }
        }
        ArrayNode history;
        if(before.has("episode_history")) {
            StrictJson.require(before.get("episode_history") instanceof ArrayNode,"original episode_history must be an array");
            history=((ArrayNode)after.get("episode_history"));for(JsonNode entry:history)StrictJson.require(entry.isObject(),"full original family history entries required");
        } else history=after.putArray("episode_history");
        var entry=history.addObject().put("source","matched_next_episode_first_baseline").put("source_episode_run_id",transition.before().runId())
                .put("successor_episode_run_id",transition.after().runId()).put("predecessor_character_id",transition.before().player()).put("successor_character_id",transition.after().player())
                .put("pending_status",before.get("pending").isObject()?"retained_original_unresolved_no_replay":"no_active_predecessor_pending").put("ck3_command_submitted",false).put("relation_completion_credit",false);
        entry.set("pending",before.get("pending").deepCopy());entry.set("resolved",before.get("resolved").deepCopy());
        entry.set("previous_body",transition.previousBody().toJson());entry.set("baseline_material",transition.baselineMaterial().toJson());
        if(before.has(FIELD))entry.set("previous_next_episode_binding",before.get(FIELD).deepCopy());
        if(before.has(FamilyNaturalEpisodeMigration.FIELD))entry.set("previous_natural_episode_binding",before.get(FamilyNaturalEpisodeMigration.FIELD).deepCopy());
        after.putNull("pending");after.putNull("resolved");after.remove(FamilyNaturalEpisodeMigration.FIELD);after.set(FIELD,transition.toJson());
        byte[] result=StrictJson.canonical(after,ContinuityJson.DOMAIN_MAX_BYTES);FamilyDomainSource.validate(slot,result);return result;
    }
    /** Consumer guard for a migrated body: the new owner/player/episode must be the actual requested frame. */
    public static void requireCurrent(Obj body,PlanningRequest actual) {
        JsonNode value=DriverJson.toNode(body);
        if(value.has(FamilyNaturalEpisodeMigration.FIELD)){FamilyNaturalEpisodeMigration.requireCurrent(body,actual);return;}
        if(!value.has(FIELD))return;
        var binding=Transition.fromJson(value.get(FIELD));var after=binding.after();
        binding.afterOwner().require(actual);
        JsonNode snapshot=DriverJson.toNode(actual.observations().snapshot());
        StrictJson.require(after.runId().equals(actual.before().frame().episodeRunId())&&after.player().equals(actual.before().frame().identity().player())
                &&after.runId().equals(StrictJson.text(snapshot.get("episode_run_id")))&&after.player().equals(currentPlayer(snapshot.path("played_character").get("character_id"))),
                "initialized family document crossed actual new episode/player");
    }
    private static ObjectNode episode(Episode value) {return StrictJson.object().put("episode_run_id",value.runId()).put("played_character_id",value.player());}
    private static Episode readEpisode(JsonNode value) {var object=StrictJson.object(value,Set.of("episode_run_id","played_character_id"));return new Episode(StrictJson.text(object.get("episode_run_id")),preservedPlayer(object.get("played_character_id")));}
}
