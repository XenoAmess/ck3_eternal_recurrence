package org.xar.ck3.control.wave2.military.armytransfer;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.ArmyId;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Missing;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Family;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputsCodec;
import org.xar.ck3.control.wave2.military.armytransfer.DailyQueueTransferProjection.Occurrence;
import org.xar.ck3.control.wave2.military.armytransfer.DailyQueueTransferProjection.ResolvedOccurrence;
import org.xar.ck3.control.wave2.military.armytransfer.DailyQueueTransferProjection.Result;
import org.xar.ck3.control.wave2.military.armytransfer.DailyQueueTransferProjection.StrengthAvailability;

/** Declared snapshot projection and exact old output shape; no mutation or execution authority. */
public final class DailyQueueTransferCodec {
    public static final int MAX_BYTES = 65_536;
    private DailyQueueTransferCodec() { }

    public record Input(StrengthAvailability availability, Family queueFamily) {
        public Input { Objects.requireNonNull(availability); Objects.requireNonNull(queueFamily); }
    }

    public static Input decode(byte[] bytes) { return decodeStrength(StrictJson.parse(bytes, MAX_BYTES)); }

    public static Result project(byte[] bytes) {
        Input input = decode(bytes);
        return DailyQueueTransferProjection.project(input.availability(), input.queueFamily());
    }

    /** Extra strength fields are valid. Nonavailable strength ignores unused queue operands. */
    public static Input decodeStrength(JsonNode strength) {
        StrictJson.require(strength != null && strength.isObject(), "army strength object required");
        JsonNode status = strength.get("status");
        boolean available = status != null && status.isTextual() && "available".equals(status.textValue());
        return new Input(available ? StrengthAvailability.AVAILABLE : StrengthAvailability.UNAVAILABLE,
                available ? ArmyDailyQueueInputsCodec.projectFamily(strength) : new Missing());
    }

    public static Result projectStrength(JsonNode strength) {
        Input input = decodeStrength(strength);
        return DailyQueueTransferProjection.project(input.availability(), input.queueFamily());
    }

    public static byte[] encode(Result value) { return StrictJson.canonical(toJson(value), MAX_BYTES); }

    public static ObjectNode toJson(Result value) {
        ObjectNode root = StrictJson.object();
        root.put("projection_kind", "conditional_daily_army_id_transfer");
        root.put("source_contract_game_version", "1.20.0.3");
        root.put("input_basis", "same_query_ordered_source_ids_and_initial_native_army_resolution");
        root.put("conditional_transfer_basis", "explicit_consumer_entry_with_ordinary_successful_native_transfer");
        root.put("status", wire(value.status()));
        root.put("conditional_transfer_ready", value.conditionalTransferReady());
        if (value.transfer().isPresent()) {
            var transfer = value.transfer().orElseThrow();
            root.put("transfer_branch", wire(transfer.branch()));
            ids(root.putArray("source_manager_army_id_list_before"), transfer.sourceIds());
            ids(root.putArray("conditional_temporary_ordered_army_ids"), transfer.sourceIds());
            root.putArray("conditional_source_manager_army_id_list_after_transfer");
        } else {
            root.putNull("transfer_branch"); root.putNull("source_manager_army_id_list_before");
            root.putNull("conditional_temporary_ordered_army_ids"); root.putNull("conditional_source_manager_army_id_list_after_transfer");
        }
        root.put("initial_removal_selection_ready", value.selectionReady());
        ArrayNode prefix = root.putArray("initial_invalid_prefix_occurrences");
        for (ResolvedOccurrence occurrence : value.invalidPrefix()) {
            ObjectNode row = resolved(occurrence);
            row.put("reason", "native_army_magic_or_full_id_invalid");
            prefix.add(row);
        }
        root.put("first_removal_call_request_ready", value.firstRemovalRequestReady());
        if (value.firstRemovalRequest().isPresent()) {
            ObjectNode request = resolved(value.firstRemovalRequest().orElseThrow());
            request.put("native_entry_rva", "0x2A978A0");
            request.put("receiver_basis", "primary_army_manager");
            request.put("argument_basis", "same_query_initial_native_army_resolution");
            root.set("first_removal_call_request", request);
        } else { root.putNull("first_removal_call_request"); }
        ArrayNode suffix = root.putArray("remaining_occurrences");
        value.remainingOccurrences().forEach(occurrence -> suffix.add(occurrence(occurrence)));
        root.put("post_removal_stage_required", value.postRemovalStageRequired());
        nullableEnum(root, "remaining_occurrences_basis", value.remainingBasis());
        ArrayNode missing = root.putArray("missing_inputs");
        value.missingInputs().forEach(missing::add);
        root.put("actual_transfer", false); root.put("actual_removal", false);
        root.putNull("actual_source_queue_after"); root.putNull("actual_removal_post_state");
        root.put("full_ordered_removal_requests_ready", false); root.put("full_monthly_lifecycle_ready", false);
        return root;
    }

    private static ObjectNode occurrence(Occurrence value) {
        ObjectNode node = StrictJson.object();
        node.put("stored_index", value.storedIndex());
        node.put("raw_army_reference_id", value.rawArmyReference().value());
        return node;
    }
    private static ObjectNode resolved(ResolvedOccurrence value) {
        ObjectNode node = occurrence(value.occurrence());
        node.put("resolved_army_id", value.resolvedArmy().value());
        node.put("used_fallback", value.usedFallback());
        node.put("army_magic_14_raw", value.armyMagic().value());
        node.put("native_army_identity_valid", value.nativeIdentityValid());
        return node;
    }
    private static void ids(ArrayNode target, java.util.List<ArmyId> values) {
        values.forEach(value -> target.add(value.value()));
    }
    private static void nullableEnum(ObjectNode target, String field, Optional<? extends Enum<?>> value) {
        if (value.isPresent()) { target.put(field, wire(value.orElseThrow())); }
        else { target.putNull(field); }
    }
    private static String wire(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
}
