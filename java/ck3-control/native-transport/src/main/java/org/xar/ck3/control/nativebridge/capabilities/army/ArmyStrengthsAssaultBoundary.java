package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputsCodec;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsAssaultCodec.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsAssaultCurrent.*;

/** Codec adapters for the independently source-validated .4 stage consumers. No second numerical implementation. */
final class ArmyStrengthsAssaultBoundary {
    private ArmyStrengthsAssaultBoundary() { }
    static List<Integer> pending(ObjectNode army){JsonNode raw=army.get("monthly_daily_queue_inputs_v1");ArmyDailyQueueInputs queue=raw==null||raw.isNull()?null:ArmyDailyQueueInputsCodec.decodeNullable(raw);return queue==null?null:queue.orderedIds().map(ids->ids.stream().map(ArmyDailyQueueInputs.ArmyId::value).toList()).orElse(null);}
    static List<ArmyStrengthsAssaultLoss.Missing> lossMissing(JsonNode node){return array(node,value->{if(value.isTextual())return new ArmyStrengthsAssaultLoss.InputMissing(value.textValue());ObjectNode n=object(value);if(n.has("group_native_index")){closed(n,"group_native_index","inputs");return new ArmyStrengthsAssaultLoss.GroupMissing(i32(get(n,"group_native_index")),lossMissing(get(n,"inputs")));}closed(n,"writer_native_index","inputs");return new ArmyStrengthsAssaultLoss.WriterMissing(i32(get(n,"writer_native_index")),array(get(n,"inputs"),ArmyJson::text));});}
    static NextGroup nextGroup(JsonNode node){if(node==null||node.isNull())return null;ObjectNode n=object(node);return new NextGroup(i32(get(n,"native_index")),i64(get(n,"physical_slot_i64")),bool(get(n,"sequential_entry_reached")),lossMissing(get(n,"missing_inputs")));}
    static NumericPrefix numeric(JsonNode node){
        if(node==null||node.isNull())return null;ObjectNode n=object(node);List<ArmyStrengthsAssaultLoss.QueueRequest> requests=array(get(n,"ordered_queue_append_requests"),value->{ObjectNode r=closed(value,"group_native_index","army_native_index","raw_full_id_u32");Long id=unsignedOrNull(r,"raw_full_id_u32");return new ArmyStrengthsAssaultLoss.QueueRequest(i32(get(r,"group_native_index")),i32(get(r,"army_native_index")),id);});
        List<GroupCompletion> groups=array(get(n,"groups"),value->{ObjectNode g=object(value);return new GroupCompletion(nextGroup(g),bool(get(g,"numeric_ready")),bool(get(g,"queue_requests_ready")));});
        return new NumericPrefix(bool(get(n,"physical_group_order_ready")),bool(get(n,"queue_requests_ready"))&&bool(get(n,"sequential_numeric_ready")),intOrNull(n,"completed_group_count"),intOrNull(n,"observed_group_count"),requests,groups,lossMissing(get(n,"missing_inputs")));
    }
    static List<QueueMissing> queueMissingDecode(JsonNode node){return array(node,value->{if(value.isTextual())return new QueueInput(value.textValue());ObjectNode n=closed(value,"stage","next_missing_group","inputs");equal(get(n,"stage"),"remaining_daily_assault_groups");return new RemainingGroups(nextGroup(get(n,"next_missing_group")),lossMissing(get(n,"inputs")));});}
    static PendingOccurrence pendingOccurrence(JsonNode node){ObjectNode n=object(node);Integer stored=intOrNull(n,"stored_index"),observed=intOrNull(n,"observed_stored_index"),append=n.has("append_request_index")?intOrNull(n,"append_request_index"):null;Long raw=unsignedOrNull(n,"raw_full_id_u32");require(raw!=null,"pending DWORD missing");int signed=i32(get(n,"stored_army_id_i32"));require((int)(long)raw==signed,"pending signed DWORD conversion changed");return new PendingOccurrence(stored,signed,raw,text(get(n,"provenance")),observed,append,intOrNull(n,"group_native_index"),intOrNull(n,"army_native_index"),n.has("append_request_index"));}
    static Queue queue(JsonNode node){
        if(node==null||node.isNull())return null;ObjectNode n=object(node);JsonNode observed=get(n,"observed_pending_army_ids_i32"),prefix=get(n,"conditional_pre_release_pending_prefix"),occurrences=get(n,"conditional_pre_release_occurrences");
        Queue q=new Queue(i32(get(n,"army_id")),observed.isNull()?null:array(observed,ArmyJson::i32),array(get(n,"observed_pending_occurrences"),ArmyStrengthsAssaultBoundary::pendingOccurrence),bool(get(n,"known_append_prefix_ready")),bool(get(n,"append_requests_complete")),array(get(n,"known_append_occurrences"),ArmyStrengthsAssaultBoundary::pendingOccurrence),prefix.isNull()?null:array(prefix,ArmyJson::i32),occurrences.isNull()?null:array(occurrences,ArmyStrengthsAssaultBoundary::pendingOccurrence),intOrNull(n,"completed_loss_group_count"),intOrNull(n,"observed_loss_group_count"),nextGroup(get(n,"next_missing_group")),lossMissing(get(n,"loss_missing_inputs")),queueMissingDecode(get(n,"missing_inputs")));
        require(q.compositePrefixReady()==bool(get(n,"conditional_pre_release_pending_prefix_ready"))&&q.compositeReady()==bool(get(n,"conditional_pre_release_pending_sequence_ready"))&&(q.observed()!=null)==bool(get(n,"observed_pending_ready")),"append prefix publication inconsistent");require(q.compositePrefixReady()==(q.prefix()!=null&&q.occurrences()!=null),"append prefix data missing");
        if(q.compositePrefixReady()){List<Integer> expected=new ArrayList<>(q.observed());q.appended().forEach(o->expected.add(o.storedArmyId()));require(expected.equals(q.prefix()),"append prefix sequence changed");require(q.occurrences().stream().map(PendingOccurrence::storedArmyId).toList().equals(expected),"append occurrence sequence changed");}
        return q;
    }
}
