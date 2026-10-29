package org.xar.ck3.control.wave2.finance.feastterminal;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.JournalField;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.ParsedJournal;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.UnusableJournal;
import org.xar.ck3.control.wave2.finance.feastterminal.NativeTerminalJournal.Cut;
import org.xar.ck3.control.wave2.finance.feastterminal.NativeTerminalJournal.Frame;

/** Complete optional-journal leaf from the existing native transport. Invalid journals stay unavailable. */
final class NativeTerminalJournalCodec {
    private static final Set<String> FAMILY = Set.of("schema", "available", "unavailable_reason", "observer_attached", "process_lifetime",
            "read_only", "query_thread_id_u32", "query_actor_full_id_u32", "record_capacity", "earliest_retained_sequence_u64",
            "latest_capture_sequence_u64", "overflow_dropped_count_u64", "record_count", "records");
    private static final Set<String> CUT = Set.of("capture_sequence_u64", "capture_thread_id_u32", "source_cut_rva_u64", "manager_identity_u64",
            "activity_identity_u64", "type_identity_u64", "activity_full_id_u32", "activity_instance_generation_u8", "host_character_id_i32",
            "type_key", "completed_observed", "completed_raw_u8", "invalidated_observed", "invalidated_raw_u8",
            "native_completion_stamp_observed", "native_completion_stamp_raw_u64", "capture_frame");
    private static final Set<String> FRAME = Set.of("date_raw_i64", "actor_character_id_i32", "owner_thread_id_u32",
            "paused", "map_ready", "has_played_character", "played_character_alive");

    private NativeTerminalJournalCodec() { }

    static JournalField readOptional(JsonNode node, long targetActor) {
        if (node == null || node.isNull()) return new UnusableJournal();
        try {
            TerminalJson.fields(node, FAMILY);
            TerminalJson.require(TerminalJson.text(node.get("schema")).equals(NativeTerminalJournal.SCHEMA));
            boolean available = TerminalJson.bool(node.get("available"));
            Optional<String> reason = node.get("unavailable_reason").isNull() ? Optional.empty()
                    : Optional.of(TerminalJson.text(node.get("unavailable_reason")));
            boolean attached = TerminalJson.bool(node.get("observer_attached"));
            TerminalJson.require(TerminalJson.bool(node.get("process_lifetime")) && TerminalJson.bool(node.get("read_only")));
            long thread = TerminalJson.number(node.get("query_thread_id_u32"), 0, NativeTerminalJournal.MAX_U32);
            long actor = TerminalJson.number(node.get("query_actor_full_id_u32"), 0, NativeTerminalJournal.MAX_U32);
            TerminalJson.require(!available || actor == targetActor);
            TerminalJson.require(TerminalJson.number(node.get("record_capacity"), 64, 64) == 64);
            int count = Math.toIntExact(TerminalJson.number(node.get("record_count"), 0, 64));
            JsonNode records = node.get("records");
            TerminalJson.require(records.isArray() && records.size() == count);
            ArrayList<Cut> cuts = new ArrayList<>(count);
            for (JsonNode row : records) cuts.add(readCut(row));
            return new ParsedJournal(new NativeTerminalJournal(available, reason, attached, thread, actor,
                    u64(node.get("earliest_retained_sequence_u64"), false), u64(node.get("latest_capture_sequence_u64"), false),
                    u64(node.get("overflow_dropped_count_u64"), false), cuts));
        } catch (IllegalArgumentException exception) {
            return new UnusableJournal();
        }
    }

    private static Cut readCut(JsonNode row) {
        TerminalJson.fields(row, CUT);
        TerminalJson.require(TerminalJson.text(row.get("type_key")).equals("activity_feast"));
        JsonNode frame = row.get("capture_frame"); TerminalJson.fields(frame, FRAME);
        Frame captured = new Frame(TerminalJson.number(frame.get("date_raw_i64"), Long.MIN_VALUE, Long.MAX_VALUE),
                Math.toIntExact(TerminalJson.number(frame.get("actor_character_id_i32"), Integer.MIN_VALUE, Integer.MAX_VALUE)),
                TerminalJson.number(frame.get("owner_thread_id_u32"), 1, NativeTerminalJournal.MAX_U32),
                TerminalJson.bool(frame.get("paused")), TerminalJson.bool(frame.get("map_ready")),
                TerminalJson.bool(frame.get("has_played_character")), TerminalJson.bool(frame.get("played_character_alive")));
        return new Cut(u64(row.get("capture_sequence_u64"), true),
                TerminalJson.number(row.get("capture_thread_id_u32"), 1, NativeTerminalJournal.MAX_U32),
                TerminalJson.number(row.get("source_cut_rva_u64"), NativeTerminalJournal.SOURCE_CUT_RVA, NativeTerminalJournal.SOURCE_CUT_RVA),
                u64(row.get("manager_identity_u64"), false), u64(row.get("activity_identity_u64"), false), u64(row.get("type_identity_u64"), false),
                TerminalJson.number(row.get("activity_full_id_u32"), 0, 0xFFFF_FFFEL),
                Math.toIntExact(TerminalJson.number(row.get("activity_instance_generation_u8"), 0, 255)),
                Math.toIntExact(TerminalJson.number(row.get("host_character_id_i32"), Integer.MIN_VALUE, Integer.MAX_VALUE)),
                rawByte(row.get("completed_observed"), row.get("completed_raw_u8")),
                rawByte(row.get("invalidated_observed"), row.get("invalidated_raw_u8")),
                rawStamp(row.get("native_completion_stamp_observed"), row.get("native_completion_stamp_raw_u64")), captured);
    }

    private static Optional<Integer> rawByte(JsonNode observed, JsonNode raw) {
        if (TerminalJson.bool(observed)) return Optional.of(Math.toIntExact(TerminalJson.number(raw, 0, 255)));
        TerminalJson.require(raw != null && raw.isNull()); return Optional.empty();
    }
    private static Optional<BigInteger> rawStamp(JsonNode observed, JsonNode raw) {
        if (TerminalJson.bool(observed)) return Optional.of(u64(raw, false));
        TerminalJson.require(raw != null && raw.isNull()); return Optional.empty();
    }
    private static BigInteger u64(JsonNode node, boolean positive) {
        return TerminalJson.integer(node, positive ? BigInteger.ONE : BigInteger.ZERO, NativeTerminalJournal.MAX_U64);
    }

    static ObjectNode write(ObjectMapper mapper, NativeTerminalJournal journal, boolean includeRecords) {
        ObjectNode root = mapper.createObjectNode(); root.put("schema", NativeTerminalJournal.SCHEMA);
        root.put("available", journal.available());
        if (journal.unavailableReason().isPresent()) root.put("unavailable_reason", journal.unavailableReason().orElseThrow());
        else root.putNull("unavailable_reason");
        root.put("observer_attached", journal.observerAttached()); root.put("process_lifetime", true); root.put("read_only", true);
        root.put("query_thread_id_u32", journal.queryThreadId()); root.put("query_actor_full_id_u32", journal.queryActorId());
        root.put("record_capacity", 64); root.put("earliest_retained_sequence_u64", journal.earliestSequence());
        root.put("latest_capture_sequence_u64", journal.latestSequence()); root.put("overflow_dropped_count_u64", journal.overflowDroppedCount());
        root.put("record_count", journal.records().size());
        if (includeRecords) {
            ArrayNode records = root.putArray("records");
            for (Cut cut : journal.records()) records.add(writeCut(mapper, cut));
        }
        return root;
    }

    static ObjectNode writeCut(ObjectMapper mapper, Cut cut) {
        ObjectNode root = mapper.createObjectNode();
        root.put("capture_sequence_u64", cut.sequence()); root.put("capture_thread_id_u32", cut.threadId());
        root.put("source_cut_rva_u64", cut.sourceCutRva()); root.put("manager_identity_u64", cut.managerIdentity());
        root.put("activity_identity_u64", cut.activityIdentity()); root.put("type_identity_u64", cut.typeIdentity());
        root.put("activity_full_id_u32", cut.activityFullId()); root.put("activity_instance_generation_u8", cut.instanceGeneration());
        root.put("host_character_id_i32", cut.hostCharacterId()); root.put("type_key", "activity_feast");
        root.put("completed_observed", cut.completedRaw().isPresent());
        if (cut.completedRaw().isPresent()) root.put("completed_raw_u8", cut.completedRaw().orElseThrow()); else root.putNull("completed_raw_u8");
        root.put("invalidated_observed", cut.invalidatedRaw().isPresent());
        if (cut.invalidatedRaw().isPresent()) root.put("invalidated_raw_u8", cut.invalidatedRaw().orElseThrow()); else root.putNull("invalidated_raw_u8");
        root.put("native_completion_stamp_observed", cut.completionStampRaw().isPresent());
        if (cut.completionStampRaw().isPresent()) root.put("native_completion_stamp_raw_u64", cut.completionStampRaw().orElseThrow());
        else root.putNull("native_completion_stamp_raw_u64");
        Frame captured = cut.frame(); ObjectNode frame = root.putObject("capture_frame");
        frame.put("date_raw_i64", captured.dateRaw()); frame.put("actor_character_id_i32", captured.actorCharacterId());
        frame.put("owner_thread_id_u32", captured.ownerThreadId()); frame.put("paused", captured.paused());
        frame.put("map_ready", captured.mapReady()); frame.put("has_played_character", captured.hasPlayedCharacter());
        frame.put("played_character_alive", captured.playedCharacterAlive());
        return root;
    }
}
