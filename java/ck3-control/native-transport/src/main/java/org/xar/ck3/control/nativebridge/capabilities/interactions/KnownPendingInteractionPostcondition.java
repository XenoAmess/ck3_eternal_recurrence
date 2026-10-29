package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.Plan;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleaseCollectionProjection12003;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.*;

/**
 * Independent reply lifecycle, branch-specific war invariants and received-ransom material checks.
 * Native "submitted" is an ACK. Compatibility interaction_result is built only after these checks.
 */
public final class KnownPendingInteractionPostcondition {
    public static final String SCHEMA="xar.java.known-pending-interaction-independent-effect/v1";
    public static final FieldKey VERIFIED=new FieldKey("known_pending_independent_effect_verified");
    public record PrisonerAfter(ObservationIdentity frame,ReleaseCollectionProjection12003.Observation collection) {
        public PrisonerAfter { Objects.requireNonNull(frame);Objects.requireNonNull(collection); }
    }
    public record Input(Plan plan,ObservationIdentity before,ObservationIdentity after,
            OpportunityJson.Obj beforeSnapshot,OpportunityJson.Obj afterSnapshot,RawJson originalNativeAck,
            Optional<PrisonerAfter> afterPrisoners) {
        public Input {
            Objects.requireNonNull(plan);Objects.requireNonNull(before);Objects.requireNonNull(after);
            Objects.requireNonNull(beforeSnapshot);Objects.requireNonNull(afterSnapshot);
            Objects.requireNonNull(originalNativeAck);Objects.requireNonNull(afterPrisoners);
            need(plan.selected().isPresent(),"postcondition needs the durable selected action");
        }
    }
    public record Result(boolean verified,List<String> missing,OpportunityJson.Obj compatibleResult,
            Optional<BigInteger> observedGoldIncreaseRaw) {
        public Result {
            missing=List.copyOf(missing);Objects.requireNonNull(compatibleResult);Objects.requireNonNull(observedGoldIncreaseRaw);
            need(verified==missing.isEmpty(),"independent result readiness differs from real evidence");
        }
        public List<ExpectedValue> actual() { return List.of(new ExpectedBoolean(VERIFIED,verified)); }
    }
    private KnownPendingInteractionPostcondition() { }
    public static ExpectedPostcondition expected(PlanningRequest request,Plan plan) {
        return expected(request.before(),request.source(),plan);
    }
    public static ExpectedPostcondition expected(ObservationIdentity before,G2Source source,Plan plan) {
        need(plan.selected().isPresent(),"only an actual selected known action has an expected effect");
        return new ExpectedPostcondition(1,before,source,SCHEMA,List.of(new ExpectedBoolean(VERIFIED,true)));
    }
    public static Result verify(Input input) {
        List<String> gaps=new ArrayList<>();
        ObjectNode before=InteractionArguments.parseApp(input.beforeSnapshot()),after=InteractionArguments.parseApp(input.afterSnapshot());
        ObjectNode ack=parse(input.originalNativeAck());
        Action action=input.plan().selected().orElseThrow();
        if(!KnownPendingInteractionEvidence.equalText(ack.get("step"),action.step())
                ||!KnownPendingInteractionEvidence.equalBoolean(ack.get("accepted"),true)
                ||!KnownPendingInteractionEvidence.equalText(ack.get("status"),"submitted"))
            gaps.add("original_native_reply_not_submitted");
        if(!sameCampaign(input.before(),input.after())
                ||!snapshotMatches(before,input.before())||!snapshotMatches(after,input.after())
                ||!KnownPendingInteractionEvidence.equalBoolean(before.get("paused"),true)
                ||!KnownPendingInteractionEvidence.equalBoolean(after.get("paused"),true)
                ||!input.before().frame().identity().dateRaw().equals(input.after().frame().identity().dateRaw())
                ||input.after().frame().revision().compareTo(input.before().frame().revision())<=0
                ||input.after().frame().identity().nativeRevision().compareTo(input.before().frame().identity().nativeRevision())<=0
                ||input.before().frame().snapshotId().equals(input.after().frame().snapshotId()))
            gaps.add("independent_later_paused_same_campaign_frame_required");
        JsonNode old=before.get("pending_character_interaction"),remaining=after.get("pending_character_interaction");
        Integer oldId=pendingId(old);
        if(oldId==null||remaining==null||!remaining.isNull()&&!(remaining instanceof ObjectNode)
                ||oldId!=null&&Objects.equals(oldId,pendingId(remaining)))
            gaps.add("old_full_pending_id_not_independently_absent");
        if(remaining!=null&&!remaining.isNull()&&remaining.isObject()&&pendingId(remaining)==null)
            gaps.add("remaining_pending_full_identity_invalid");
        if(old!=null&&old.isObject()) {
            JsonNode notification=old.get("auto_accept_notification");
            if(!KnownPendingInteractionEvidence.equalBoolean(notification,action==Action.ACKNOWLEDGE))
                gaps.add("original_pending_reply_channel_changed");
        }
        Optional<List<WarSignature>> beforeWars=KnownPendingInteractionEvidence.warSignature(before);
        Optional<List<WarSignature>> afterWars=KnownPendingInteractionEvidence.warSignature(after);
        if(input.plan().classification()==Classification.KNOWN_GRANT_VASSAL) {
            if(action!=Action.REJECT||beforeWars.isEmpty()||afterWars.isEmpty()||!beforeWars.equals(afterWars))
                gaps.add("grant_vassal_active_war_signature_not_preserved");
        }
        if(input.plan().classification()==Classification.KNOWN_CALL_ALLY) {
            Optional<List<WarSignature>> planned=input.plan().originalWarSignature();
            if(action!=Action.REJECT||planned.isEmpty()||planned.orElseThrow().isEmpty()||!planned.equals(beforeWars)
                    ||afterWars.isEmpty())gaps.add("call_ally_planned_original_war_signature_mismatch");
            else {
                Set<Integer> oldWars=new HashSet<>();planned.orElseThrow().forEach(w->oldWars.add(w.warId()));
                Set<Integer> nowWars=new HashSet<>();afterWars.orElseThrow().forEach(w->nowWars.add(w.warId()));
                if(afterWars.orElseThrow().size()>planned.orElseThrow().size()||!oldWars.containsAll(nowWars))
                    gaps.add("call_ally_new_active_war_id_observed");
            }
        }
        if(input.plan().ruleId().equals("raiktor-inbound-white-peace-v1")) {
            if(action!=Action.ACCEPT||input.plan().warId().isEmpty()||beforeWars.isEmpty()||afterWars.isEmpty())
                gaps.add("raiktor_bound_war_postcondition_unavailable");
            else {
                int id=input.plan().warId().orElseThrow();
                if(beforeWars.orElseThrow().stream().noneMatch(w->w.warId()==id)
                        ||afterWars.orElseThrow().stream().anyMatch(w->w.warId()==id))
                    gaps.add("raiktor_bound_war_not_independently_absent");
            }
        }
        Optional<BigInteger> increase=Optional.empty();
        if(input.plan().classification()==Classification.KNOWN_RECEIVED_RANSOM) {
            BigInteger oldGold=gold(before),newGold=gold(after);
            if(action!=Action.ACCEPT||oldGold==null||newGold==null||newGold.compareTo(oldGold)<=0)
                gaps.add("received_ransom_independent_positive_gold_change_required");
            else increase=Optional.of(newGold.subtract(oldGold));
            if(input.plan().prisonerId().isEmpty()||input.afterPrisoners().isEmpty()
                    ||!input.afterPrisoners().orElseThrow().frame().equals(input.after()))
                gaps.add("received_ransom_current_complete_custody_read_required");
            else {
                long id=input.plan().prisonerId().orElseThrow();
                if(input.afterPrisoners().orElseThrow().collection().rows().stream().anyMatch(row->row.prisonerCharacterId()==id))
                    gaps.add("received_ransom_prisoner_still_in_player_custody");
            }
        }
        ObjectNode compatible=ack.deepCopy();
        compatible.put("native_ack_verified",gaps.stream().noneMatch("original_native_reply_not_submitted"::equals))
                .put("postcondition_verified",gaps.isEmpty()).put("material_effects_verified",
                        gaps.isEmpty()&&input.plan().classification()==Classification.KNOWN_RECEIVED_RANSOM)
                .put("alliance_semantic_postcondition_ready",false);
        if(gaps.isEmpty()) {
            compatible.putObject("interaction_result").put("status",switch(action) {
                case ACCEPT -> "accepted";case REJECT -> "rejected";case ACKNOWLEDGE -> "acknowledged";
            }).put("instance_id",oldId).set("sender_character_id",field(old,"sender_character_id").deepCopy());
            compatible.set("remaining_pending_character_interaction",remaining.deepCopy());
            compatible.put("paused",true).put("snapshot_id",input.after().frame().snapshotId())
                    .put("revision",input.after().frame().revision()).put("native_revision",input.after().frame().identity().nativeRevision());
            increase.ifPresent(value->compatible.put("observed_player_gold_increase_raw",value));
        }
        var missing=compatible.putArray("missing_postconditions");gaps.forEach(missing::add);
        compatible.put("replay_allowed",false);
        return new Result(gaps.isEmpty(),gaps,InteractionArguments.app(compatible),increase);
    }
    private static boolean sameCampaign(ObservationIdentity before,ObservationIdentity after) {
        return before.machineId().equals(after.machineId())&&before.game().equals(after.game())
                &&before.frame().episodeRunId().equals(after.frame().episodeRunId())
                &&before.frame().identity().player().equals(after.frame().identity().player());
    }
    private static boolean snapshotMatches(ObjectNode snapshot,ObservationIdentity identity) {
        JsonNode actor=snapshot.get("played_character");
        return KnownPendingInteractionEvidence.equalText(snapshot.get("snapshot_id"),identity.frame().snapshotId())
                &&KnownPendingInteractionEvidence.equalText(snapshot.get("episode_run_id"),identity.frame().episodeRunId())
                &&KnownPendingInteractionEvidence.equalInt(snapshot.get("revision"),identity.frame().revision())
                &&KnownPendingInteractionEvidence.equalInt(snapshot.get("native_revision"),identity.frame().identity().nativeRevision())
                &&KnownPendingInteractionEvidence.equalInt(snapshot.get("date_raw"),identity.frame().identity().dateRaw())
                &&actor!=null&&actor.isObject()&&KnownPendingInteractionEvidence.equalInt(actor.get("character_id"),identity.frame().identity().player());
    }
    private static Integer pendingId(JsonNode pending) {
        if(pending==null||!pending.isObject())return null;
        JsonNode id=pending.get("instance_id");
        if(!KnownPendingInteractionEvidence.integral(id)||!id.canConvertToInt()||id.intValue()==-1)return null;
        return id.intValue();
    }
    private static BigInteger gold(ObjectNode snapshot) {
        JsonNode wallet=snapshot.get("played_character_gold");
        if(wallet==null||!wallet.isObject()||!KnownPendingInteractionEvidence.equalInt(wallet.get("scale"),BigInteger.valueOf(100000))
                ||!KnownPendingInteractionEvidence.integral(wallet.get("raw")))return null;
        BigInteger raw=wallet.get("raw").bigIntegerValue();
        return raw.compareTo(I64_MIN)>=0&&raw.compareTo(I64_MAX)<=0?raw:null;
    }
}

