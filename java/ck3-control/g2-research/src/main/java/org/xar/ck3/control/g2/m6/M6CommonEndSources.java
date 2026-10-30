package org.xar.ck3.control.g2.m6;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.g2.m6.M6TerminalSourceComposition.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Exact actual4 copied common entry/return normalization; this family never names a cause. */
final class M6CommonEndSources {
    private M6CommonEndSources() { }
    private static final Set<String> FAMILY = Set.of("schema", "source_contract", "available", "unavailable_reason", "read_only",
            "observer_attached", "observer_session_identity", "owner_thread_id", "actor_character_id", "target_character_id",
            "scheme_instance_id", "scheme_instance_generation", "after_sequence", "earliest_sequence", "latest_sequence",
            "retention_gap", "session_records_only", "records");
    private static final Set<String> RECORD = Set.of("sequence", "observer_session_identity", "owner_thread_id", "original_invocation_id",
            "callsite_rva", "callee_rva", "call_return_rva", "incoming_return_address_observed", "caller_return_rva",
            "incoming_dl_observed", "incoming_dl_raw_u8", "entry", "original_forwarded_once", "original_returned", "returned",
            "return_same_scheme_full_id_observed", "return_same_scheme_full_id");
    private static final Set<String> FRAME = Set.of("scheme_header_observed", "scheme_full_id_observed", "scheme_full_id_raw_u32",
            "scheme_instance_generation_u8", "status_observed", "status_raw_i32", "owner_observed", "owner_character_full_id_raw_u32",
            "other_kind_observed", "other_kind_raw_u32", "target_observed", "target_character_full_id_raw_u32", "core_frame_observed", "core_frame");
    private static final Set<String> CORE = Set.of("date_raw", "speed", "paused", "local_player_id", "map_ready",
            "has_played_character", "played_character_id", "played_character_alive");

    static JsonNode normalize(JsonNode family, JsonNode context) {
        StrictJson.object(family, FAMILY); textEquals(family, "schema", "xar.ck3.sway-common-native-end.v1");
        textEquals(family, "source_contract", "actual_2a48877_2a4adf0_v1");
        for (String flag : List.of("available", "read_only", "observer_attached", "retention_gap", "session_records_only")) bool(family, flag);
        require(bool(family, "read_only") && bool(family, "session_records_only"), "common end read-only session required");
        JsonNode reason = family.get("unavailable_reason"); require(reason.isTextual() && reason.textValue().isEmpty() == bool(family, "available"), "common end availability reason differs");
        for (String field : List.of("observer_session_identity", "after_sequence", "earliest_sequence", "latest_sequence")) u64(family, field, 0);
        integer(family, "owner_thread_id", 0, 0xffff_ffffL);
        for (String field : IDS.subList(0, 2)) require(NativeCharacterId.fromJson(family.get(field)).equals(NativeCharacterId.fromJson(context.get(field))), "common end query identity differs");
        require(integer(family, "scheme_instance_id", 0, 0xffff_ffffL) == integer(context, "scheme_instance_id", 0, 0xffff_ffffL), "common end query identity differs");
        require(integer(family, "scheme_instance_generation", 0, 255) == integer(family, "scheme_instance_id", 0, 0xffff_ffffL) >> 24, "common end generation differs");
        require(u64(family, "after_sequence", 0).signum() == 0, "common end independent sequence begins at zero"); array(family.get("records"));
        if (bool(family, "available")) require(bool(family, "observer_attached") && u64(family, "observer_session_identity", 0).signum() > 0
                && integer(family, "owner_thread_id", 0, 0xffff_ffffL) > 0, "common end admitted session/thread missing");
        BigInteger earliest = u64(family, "earliest_sequence", 0), latest = u64(family, "latest_sequence", 0);
        require((earliest.signum() == 0) == (latest.signum() == 0) && earliest.compareTo(latest) <= 0
                && (bool(family, "available") || family.get("records").isEmpty()), "common ring bounds differ");
        BigInteger previous = BigInteger.ZERO;
        for (JsonNode row : family.get("records")) {
            StrictJson.object(row, RECORD); BigInteger sequence = u64(row, "sequence", 1);
            require(u64(row, "observer_session_identity", 1).equals(u64(family, "observer_session_identity", 0))
                    && integer(row, "owner_thread_id", 1, 0xffff_ffffL) == integer(family, "owner_thread_id", 0, 0xffff_ffffL), "common invocation session/thread differs");
            u64(row, "original_invocation_id", 1);
            require(sequence.compareTo(earliest) >= 0 && sequence.compareTo(latest) <= 0 && sequence.compareTo(previous) > 0, "common record sequence differs");
            require(u64(row, "callsite_rva", 0).equals(BigInteger.valueOf(0x2a48877))
                    && u64(row, "callee_rva", 0).equals(BigInteger.valueOf(0x2a4adf0))
                    && u64(row, "call_return_rva", 0).equals(BigInteger.valueOf(0x2a4887c)), "common native source edges differ");
            for (String flag : List.of("incoming_return_address_observed", "incoming_dl_observed", "original_forwarded_once", "original_returned", "return_same_scheme_full_id_observed")) bool(row, flag);
            require(!bool(row, "incoming_return_address_observed") && row.get("caller_return_rva").isNull(), "common unobserved caller was filled");
            nullableInteger(row, "incoming_dl_observed", "incoming_dl_raw_u8", 0, 255);
            JsonNode entry = frame(row.get("entry")), returned = frame(row.get("returned"));
            require(bool(entry, "scheme_full_id_observed") && integer(entry, "scheme_full_id_raw_u32", 0, 0xffff_ffffL) == integer(family, "scheme_instance_id", 0, 0xffff_ffffL)
                    && bool(entry, "owner_observed") && integer(entry, "owner_character_full_id_raw_u32", 0, 0xffff_ffffL) == Integer.toUnsignedLong(NativeCharacterId.fromJson(family.get("actor_character_id")).value())
                    && bool(entry, "target_observed") && integer(entry, "target_character_full_id_raw_u32", 0, 0xffff_ffffL) == Integer.toUnsignedLong(NativeCharacterId.fromJson(family.get("target_character_id")).value()), "common entry differs from original identities");
            JsonNode sameId = row.get("return_same_scheme_full_id");
            if (bool(row, "return_same_scheme_full_id_observed")) {
                require(sameId.isBoolean() && bool(entry, "scheme_header_observed") && bool(returned, "scheme_header_observed")
                        && bool(entry, "scheme_full_id_observed") && bool(returned, "scheme_full_id_observed")
                        && sameId.booleanValue() == exactIntegerEquals(entry.get("scheme_full_id_raw_u32"), returned.get("scheme_full_id_raw_u32")), "common same-id diagnostic differs");
            } else require(sameId.isNull(), "unobserved same-id diagnostic was filled");
            previous = sequence;
        }
        return family.deepCopy();
    }

    private static JsonNode frame(JsonNode frame) {
        StrictJson.object(frame, FRAME);
        for (String flag : List.of("scheme_header_observed", "scheme_full_id_observed", "status_observed", "owner_observed", "other_kind_observed", "target_observed", "core_frame_observed")) bool(frame, flag);
        nullableInteger(frame, "scheme_full_id_observed", "scheme_full_id_raw_u32", 0, 0xffff_ffffL);
        nullableInteger(frame, "scheme_full_id_observed", "scheme_instance_generation_u8", 0, 255);
        nullableInteger(frame, "status_observed", "status_raw_i32", Integer.MIN_VALUE, Integer.MAX_VALUE);
        nullableInteger(frame, "owner_observed", "owner_character_full_id_raw_u32", 0, 0xffff_ffffL);
        nullableInteger(frame, "other_kind_observed", "other_kind_raw_u32", 0, 0xffff_ffffL);
        nullableInteger(frame, "target_observed", "target_character_full_id_raw_u32", 0, 0xffff_ffffL);
        if (bool(frame, "scheme_full_id_observed")) require(integer(frame, "scheme_instance_generation_u8", 0, 255) == integer(frame, "scheme_full_id_raw_u32", 0, 0xffff_ffffL) >> 24, "common frame generation differs");
        if (bool(frame, "target_observed")) require(bool(frame, "other_kind_observed") && integer(frame, "other_kind_raw_u32", 0, 0xffff_ffffL) == 0, "common character target lacks kind0");
        JsonNode core = frame.get("core_frame");
        if (bool(frame, "core_frame_observed")) {
            StrictJson.object(core, CORE);
            for (String field : List.of("date_raw", "speed", "local_player_id", "played_character_id")) signed(core, field);
            for (String field : List.of("paused", "map_ready", "has_played_character", "played_character_alive")) bool(core, field);
        } else require(core.isNull(), "common missing Core was filled");
        return frame;
    }

    static JsonNode retained(JsonNode family, JsonNode read, JsonNode original) {
        if (family == null || !bool(family, "available") || read == null) return null;
        JsonNode records = family.get("records");
        for (int index = records.size() - 1; index >= 0; index--) {
            JsonNode row = records.get(index), entry = row.get("entry"), returned = row.get("returned");
            if (!bool(row, "original_forwarded_once") || !bool(row, "original_returned")) continue;
            boolean matches = true;
            for (JsonNode frame : List.of(entry, returned)) matches &= bool(frame, "scheme_full_id_observed")
                    && exactIntegerEquals(frame.get("scheme_full_id_raw_u32"), original.get("scheme_instance_id"))
                    && exactIntegerEquals(frame.get("scheme_instance_generation_u8"), original.get("scheme_instance_generation"));
            if (!matches || !bool(returned, "status_observed") || signed(returned, "status_raw_i32") != 1 || !bool(returned, "owner_observed")) continue;
            long owner = integer(returned, "owner_character_full_id_raw_u32", 0, 0xffff_ffffL);
            if (owner != Integer.toUnsignedLong(NativeCharacterId.fromJson(original.get("actor_character_id")).value()) && owner != 0xffff_ffffL) continue;
            ObjectNode result = StrictJson.object(); result.set("original_instance", original); result.put("source_kind", "copied_common_native_end_original_return");
            result.put("native_status_raw", 1); result.put("native_status_key", "terminated_unattributed");
            result.put("native_terminal_state_observed", true); result.put("terminal_cause_observed", false);
            result.set("copied_common_native_end_record", row); ObjectNode provenance = ((ObjectNode)family).deepCopy(); provenance.remove("records");
            result.set("copied_common_native_end_provenance", provenance); result.set("source_read", sourceRead(read, true)); return result;
        }
        return null;
    }

    private static void nullableInteger(JsonNode value, String observed, String field, long min, long max) {
        if (bool(value, observed)) integer(value, field, min, max); else require(value.get(field).isNull(), "common unobserved raw value was filled: " + field);
    }
}
