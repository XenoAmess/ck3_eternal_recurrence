package org.xar.ck3.control.wave2.finance.feastterminal;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;

/** Copied original native CALL intervals, independent from whole-Feast payoff. */
public final class CompletionCallJournal {
    public static final String V1 = "activity_completion_effect_counter_observations_12004_v1";
    public static final String V2 = "activity_completion_effect_counter_observations_12004_v2";
    public static final String BUILD = "1.20.0.4";
    public static final String EXE = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    public static final int MAX_BYTES = 1_048_576;
    private static final BigInteger U64 = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final BigInteger I64_MIN = BigInteger.ONE.shiftLeft(63).negate();
    private static final BigInteger I64_MAX = BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE);
    private static final BigInteger SAFE = BigInteger.valueOf(9_007_199_254_740_991L);
    private static final Set<String> FAMILY = Set.of("schema", "available", "unavailable_reason",
            "observer_attached", "read_only", "process_lifetime", "query_thread_id_u32",
            "query_actor_full_id_u32", "record_capacity", "earliest_retained_sequence_u64",
            "latest_capture_sequence_u64", "overflow_dropped_count_u64", "pairing_dropped_count_u64",
            "record_count", "records");
    private static final Set<String> ROW = Set.of("capture_sequence_u64", "observer_invocation_sequence_u64",
            "capture_thread_id_u32", "source_call_rva_u64", "source_callee_rva_u64", "source_return_rva_u64",
            "activity_identity_u64", "participant_identity_u64", "effect_identity_u64", "native_context_identity_u64",
            "original_parent_rsp_u64", "original_call_return_observed", "before", "after",
            "same_activity_full_id_observed", "same_activity_full_id", "same_participant_full_id_observed",
            "same_participant_full_id");
    private static final Set<String> SCOPED = Set.of("source_after_cut_rva_u64", "intervening_call_rva_u64",
            "intervening_callee_rva_u64", "observation_scope");
    private static final Set<String> FACE = Set.of("frame_observed", "frame", "activity_full_id_observed",
            "activity_full_id_u32", "activity_instance_generation_u8", "host_observed", "host_character_id_i32",
            "type_observed", "type_identity_u64", "type_key_observed", "type_key", "participant_full_id_observed",
            "participant_full_id_u32", "participant_instance_generation_u8", "resource_extension_observed",
            "resource_extension_identity_u64", "prestige_observed", "prestige_raw_i64", "stress_observed",
            "stress_raw_i32", "reveler_xp_observed", "reveler_xp_raw_i64", "reveler_xp_unavailable_reason");
    private static final Set<String> TERMINAL = Set.of("completed_observed", "completed_raw_u8",
            "invalidated_observed", "invalidated_raw_u8", "native_completion_stamp_observed",
            "native_completion_stamp_raw_u64");
    private CompletionCallJournal() { }

    /** Supplied by the owning validated native read; constructing it grants no provenance qualification. */
    public record Source(String machineId, long gamePid, String gameBirthFiletime, BigInteger queryNativeRevision,
            int queryDateRaw, long actorFullId, String build, String exeSha256) {
        public Source {
            require(machineId != null && !machineId.isBlank(), "source machine missing");
            require(gamePid > 0, "source Game PID missing");
            decimal(gameBirthFiletime, BigInteger.ONE, U64);
            bounded(queryNativeRevision, BigInteger.ONE, U64); u32(actorFullId);
            require(BUILD.equals(build) && EXE.equalsIgnoreCase(exeSha256), "source exact build differs");
        }
    }
    public record CaptureFrame(BigInteger dateRaw, int actorId, long ownerThreadId, boolean paused,
            boolean mapReady, boolean hasPlayer, boolean playerAlive) {
        public CaptureFrame { bounded(dateRaw, I64_MIN, I64_MAX); require(ownerThreadId > 0 && ownerThreadId <= 0xffff_ffffL, "capture thread"); }
    }
    /** Empty is unread; zero and overlapping nonzero bytes remain independently known. */
    public record NativeFields(Optional<Integer> completed, Optional<Integer> invalidated,
            Optional<BigInteger> completionStampRaw) {
        public NativeFields {
            Objects.requireNonNull(completed); Objects.requireNonNull(invalidated); Objects.requireNonNull(completionStampRaw);
            completed.ifPresent(value -> require(value >= 0 && value <= 255, "completed byte"));
            invalidated.ifPresent(value -> require(value >= 0 && value <= 255, "invalidated byte"));
            completionStampRaw.ifPresent(value -> bounded(value, BigInteger.ZERO, U64));
        }
    }
    public record Face(Optional<CaptureFrame> frame, Optional<Long> activityFullId, Optional<Integer> hostId,
            Optional<BigInteger> typeIdentity, Optional<String> typeKey, Optional<Long> participantFullId,
            Optional<BigInteger> resourceExtension, Optional<BigInteger> prestigeRaw, Optional<Integer> stressRaw,
            Optional<NativeFields> nativeFields) {
        public Face {
            Objects.requireNonNull(frame); Objects.requireNonNull(activityFullId); Objects.requireNonNull(hostId);
            Objects.requireNonNull(typeIdentity); Objects.requireNonNull(typeKey); Objects.requireNonNull(participantFullId);
            Objects.requireNonNull(resourceExtension); Objects.requireNonNull(prestigeRaw); Objects.requireNonNull(stressRaw);
            Objects.requireNonNull(nativeFields);
        }
    }
    public enum Scope { ORIGINAL_COMPLETION_CALL, COMPLETION_AND_FOLLOWING_NATIVE_CALL }
    public record PhysicalIdentity(BigInteger activity, BigInteger participant, BigInteger effect,
            BigInteger nativeContext, BigInteger parentRsp) {
        public PhysicalIdentity {
            for (BigInteger value : List.of(activity, participant, effect, nativeContext, parentRsp)) bounded(value, BigInteger.ZERO, U64);
        }
    }
    public record Row(BigInteger captureSequence, BigInteger invocationSequence, long captureThreadId, Scope scope,
            PhysicalIdentity physical, boolean originalReturnObserved, Face before, Face after,
            Optional<Boolean> sameActivity, Optional<Boolean> sameParticipant, ProjectionJson copied) {
        public Row {
            bounded(captureSequence, BigInteger.ONE, U64); bounded(invocationSequence, BigInteger.ONE, U64);
            require(captureThreadId > 0 && captureThreadId <= 0xffff_ffffL, "capture thread");
            Objects.requireNonNull(scope); Objects.requireNonNull(physical); Objects.requireNonNull(before);
            Objects.requireNonNull(after); Objects.requireNonNull(sameActivity); Objects.requireNonNull(sameParticipant);
            Objects.requireNonNull(copied);
        }
    }
    public record Journal(Source source, boolean available, Optional<String> unavailableReason, boolean attached,
            long queryThreadId, BigInteger earliest, BigInteger latest, BigInteger overflowDropped,
            BigInteger pairingDropped, List<Row> records, ProjectionJson copied) {
        public Journal {
            Objects.requireNonNull(source); Objects.requireNonNull(unavailableReason); records = List.copyOf(records);
            Objects.requireNonNull(copied);
        }
        /** Canonical JSON-domain copy; original transport bytes remain the owning archive's responsibility. */
        public byte[] copiedJson() { return copied.bytes(); }
    }
    public record Observation(Source source, long activityFullId, Row row, boolean pairedIdentities,
            Optional<BigInteger> prestigeDeltaRaw, Optional<BigInteger> stressDeltaRaw,
            Optional<NativeFields> beforeNativeFields, Optional<NativeFields> afterNativeFields) {
        public Observation {
            Objects.requireNonNull(source); Objects.requireNonNull(row); Objects.requireNonNull(prestigeDeltaRaw);
            Objects.requireNonNull(stressDeltaRaw); Objects.requireNonNull(beforeNativeFields); Objects.requireNonNull(afterNativeFields);
        }
        public boolean counterChangesAttributedToFeast() { return false; }
        public boolean terminalCauseObserved() { return false; }
        public boolean benefitVerified() { return false; }
        public boolean wholeM6Complete() { return false; }
    }

    /** v1 numeric identities above JS's safe range are refused; recover their original bytes before use. */
    public static Journal decode(byte[] raw, Source source) {
        Objects.requireNonNull(source);
        JsonNode root = StrictJson.parse(raw, MAX_BYTES); exact(root, FAMILY);
        String schema = text(root, "schema"); boolean v2 = V2.equals(schema);
        require(v2 || V1.equals(schema), "journal schema differs");
        boolean available = bool(root, "available"), attached = bool(root, "observer_attached");
        require(bool(root, "read_only") && bool(root, "process_lifetime"), "journal lifetime/read-only differs");
        long thread = integer(root, "query_thread_id_u32", 0, 0xffff_ffffL);
        long actor = integer(root, "query_actor_full_id_u32", 0, 0xffff_ffffL);
        require(integer(root, "record_capacity", 64, 64) == 64, "journal capacity");
        BigInteger earliest = wide(root, "earliest_retained_sequence_u64", v2, false);
        BigInteger latest = wide(root, "latest_capture_sequence_u64", v2, false);
        BigInteger overflow = wide(root, "overflow_dropped_count_u64", v2, false);
        BigInteger pairing = wide(root, "pairing_dropped_count_u64", v2, false);
        require((earliest.signum() == 0) == (latest.signum() == 0) && earliest.compareTo(latest) <= 0, "journal sequence coverage");
        JsonNode entries = root.get("records"); require(entries.isArray() && entries.size() <= 64, "journal records");
        require(integer(root, "record_count", 0, 64) == entries.size(), "journal count differs");
        Optional<String> reason;
        if (available) {
            require(root.get("unavailable_reason").isNull() && attached && thread != 0 && actor == source.actorFullId(), "journal available binding");
            reason = Optional.empty();
        } else {
            String value = text(root, "unavailable_reason"); require(!value.isBlank() && entries.isEmpty(), "journal unavailable rows");
            reason = Optional.of(value);
        }
        ArrayList<Row> records = new ArrayList<>(); BigInteger previous = BigInteger.ZERO;
        for (JsonNode entry : entries) {
            boolean scoped = entry.has("source_after_cut_rva_u64");
            exact(entry, scoped ? union(ROW, SCOPED) : ROW); require(!v2 || scoped, "v2 requires exact call descriptor");
            BigInteger sequence = wide(entry, "capture_sequence_u64", v2, false);
            require(sequence.compareTo(previous) > 0 && sequence.compareTo(earliest) >= 0 && sequence.compareTo(latest) <= 0, "journal order");
            long captureThread = integer(entry, "capture_thread_id_u32", 1, 0xffff_ffffL);
            require(integer(entry, "source_callee_rva_u64", 0, Long.MAX_VALUE) == 0x3765760L, "completion callee differs");
            Scope scope = scope(entry, scoped);
            Face before = face(entry.get("before"), v2, captureThread), after = face(entry.get("after"), v2, captureThread);
            require(captureThread == thread && before.frame().isPresent() && before.activityFullId().isPresent() && before.hostId().isPresent()
                    && before.typeIdentity().isPresent() && before.typeKey().filter("activity_feast"::equals).isPresent()
                    && before.participantFullId().orElse(-1L) == source.actorFullId()
                    && Integer.toUnsignedLong(before.frame().orElseThrow().actorId()) == source.actorFullId()
                    && before.frame().orElseThrow().mapReady() && before.frame().orElseThrow().hasPlayer()
                    && before.frame().orElseThrow().playerAlive(), "owned entry binding");
            PhysicalIdentity physical = new PhysicalIdentity(wide(entry, "activity_identity_u64", v2, false),
                    wide(entry, "participant_identity_u64", v2, false), wide(entry, "effect_identity_u64", v2, false),
                    wide(entry, "native_context_identity_u64", v2, false), wide(entry, "original_parent_rsp_u64", v2, false));
            records.add(new Row(sequence, wide(entry, "observer_invocation_sequence_u64", v2, false), captureThread,
                    scope, physical, bool(entry, "original_call_return_observed"), before, after,
                    same(entry, "activity", before.activityFullId(), after.activityFullId()),
                    same(entry, "participant", before.participantFullId(), after.participantFullId()), copied(entry)));
            previous = sequence;
        }
        return new Journal(source, available, reason, attached, thread, earliest, latest, overflow, pairing, records, copied(root));
    }

    /** Same full Activity, host, type and player participant. Never sums records or infers flags from deltas. */
    public static List<Observation> consume(Journal journal, long activityFullId) {
        Objects.requireNonNull(journal); u32(activityFullId);
        ArrayList<Observation> observations = new ArrayList<>();
        if (!journal.available()) return List.of();
        for (Row row : journal.records()) {
            Face before = row.before(), after = row.after(); long actor = journal.source().actorFullId();
            if (before.activityFullId().orElse(-1L) != activityFullId
                    || before.hostId().isEmpty() || Integer.toUnsignedLong(before.hostId().orElseThrow()) != actor
                    || before.participantFullId().orElse(-1L) != actor || before.typeKey().filter("activity_feast"::equals).isEmpty()) continue;
            boolean paired = row.originalReturnObserved() && row.sameActivity().orElse(false) && row.sameParticipant().orElse(false);
            // After host/type can fail independently. Preserve fields but do not promote a mismatched face.
            boolean afterBound = paired && after.hostId().isPresent() && Integer.toUnsignedLong(after.hostId().orElseThrow()) == actor
                    && after.typeKey().filter("activity_feast"::equals).isPresent();
            observations.add(new Observation(journal.source(), activityFullId, row, paired,
                    paired ? delta(before.prestigeRaw(), after.prestigeRaw()) : Optional.empty(),
                    paired ? delta(before.stressRaw().map(BigInteger::valueOf), after.stressRaw().map(BigInteger::valueOf)) : Optional.empty(),
                    before.nativeFields(), afterBound ? after.nativeFields() : Optional.empty()));
        }
        return List.copyOf(observations);
    }

    private static Face face(JsonNode node, boolean v2, long captureThread) {
        exact(node, v2 ? union(FACE, TERMINAL) : FACE);
        Optional<Long> activity = observedInteger(node, "activity_full_id_observed", "activity_full_id_u32", 0, 0xffff_ffffL);
        Optional<Long> participant = observedInteger(node, "participant_full_id_observed", "participant_full_id_u32", 0, 0xffff_ffffL);
        generation(node, "activity", activity); generation(node, "participant", participant);
        Optional<Integer> host = observedInteger(node, "host_observed", "host_character_id_i32", Integer.MIN_VALUE, Integer.MAX_VALUE).map(Math::toIntExact);
        Optional<BigInteger> type = observedWide(node, "type_observed", "type_identity_u64", v2, false);
        Optional<BigInteger> resource = observedWide(node, "resource_extension_observed", "resource_extension_identity_u64", v2, false);
        Optional<BigInteger> prestige = observedWide(node, "prestige_observed", "prestige_raw_i64", v2, true);
        Optional<Integer> stress = observedInteger(node, "stress_observed", "stress_raw_i32", Integer.MIN_VALUE, Integer.MAX_VALUE).map(Math::toIntExact);
        if (prestige.isPresent() || stress.isPresent()) require(resource.isPresent(), "counter requires extension observation");
        if (resource.filter(BigInteger.ZERO::equals).isPresent()) {
            require(prestige.map(BigInteger.ZERO::equals).orElse(true) && stress.map(value -> value == 0).orElse(true), "null extension domain is zero");
        }
        Optional<String> key;
        if (bool(node, "type_key_observed")) { String value = text(node, "type_key"); require(!value.isEmpty() && value.length() <= 64, "type key"); key = Optional.of(value); }
        else { require(node.get("type_key").isNull(), "unread type key remains null"); key = Optional.empty(); }
        require(!bool(node, "reveler_xp_observed") && node.get("reveler_xp_raw_i64").isNull()
                && text(node, "reveler_xp_unavailable_reason").equals("no_raw_only_reveler_xp_reader"), "raw XP source unavailable");
        Optional<CaptureFrame> frame;
        if (bool(node, "frame_observed")) {
            JsonNode value = node.get("frame"); exact(value, Set.of("date_raw_i64", "actor_character_id_i32", "owner_thread_id_u32", "paused", "map_ready", "has_played_character", "played_character_alive"));
            long thread = integer(value, "owner_thread_id_u32", 1, 0xffff_ffffL); require(thread == captureThread, "capture frame thread differs");
            frame = Optional.of(new CaptureFrame(wide(value, "date_raw_i64", v2, true), Math.toIntExact(integer(value, "actor_character_id_i32", Integer.MIN_VALUE, Integer.MAX_VALUE)),
                    thread, bool(value, "paused"), bool(value, "map_ready"), bool(value, "has_played_character"), bool(value, "played_character_alive")));
        } else { require(node.get("frame").isNull(), "unread frame remains null"); frame = Optional.empty(); }
        Optional<NativeFields> fields = v2 ? Optional.of(new NativeFields(
                observedInteger(node, "completed_observed", "completed_raw_u8", 0, 255).map(Math::toIntExact),
                observedInteger(node, "invalidated_observed", "invalidated_raw_u8", 0, 255).map(Math::toIntExact),
                observedWide(node, "native_completion_stamp_observed", "native_completion_stamp_raw_u64", true, false))) : Optional.empty();
        return new Face(frame, activity, host, type, key, participant, resource, prestige, stress, fields);
    }
    private static Scope scope(JsonNode row, boolean scoped) {
        long call = integer(row, "source_call_rva_u64", 0, Long.MAX_VALUE), returned = integer(row, "source_return_rva_u64", 0, Long.MAX_VALUE);
        if (!scoped) { require(call == 0x23F6B82 && returned == 0x23F6B87, "legacy first-call scope differs"); return Scope.ORIGINAL_COMPLETION_CALL; }
        long after = integer(row, "source_after_cut_rva_u64", 0, Long.MAX_VALUE);
        if (call == 0x23F6B82 && returned == 0x23F6B87 && after == 0x23F6B87
                && row.get("intervening_call_rva_u64").isNull() && row.get("intervening_callee_rva_u64").isNull()
                && text(row, "observation_scope").equals("original_completion_call")) return Scope.ORIGINAL_COMPLETION_CALL;
        require(call == 0x23F6B9A && returned == 0x23F6B9F && after == 0x23F6BA7
                && integer(row, "intervening_call_rva_u64", 0, Long.MAX_VALUE) == 0x23F6BA2
                && integer(row, "intervening_callee_rva_u64", 0, Long.MAX_VALUE) == 0x28BEF00
                && text(row, "observation_scope").equals("original_completion_call_and_following_native_call"), "composite scope differs");
        return Scope.COMPLETION_AND_FOLLOWING_NATIVE_CALL;
    }
    private static Optional<Boolean> same(JsonNode row, String key, Optional<Long> before, Optional<Long> after) {
        String prefix = "same_" + key + "_full_id"; boolean observed = bool(row, prefix + "_observed");
        if (!observed) { require(row.get(prefix).isNull(), "unread comparison remains null"); return Optional.empty(); }
        boolean same = bool(row, prefix); require(before.isPresent() && after.isPresent() && same == before.equals(after), "copied full-ID comparison differs");
        return Optional.of(same);
    }
    private static void generation(JsonNode node, String key, Optional<Long> fullId) {
        String field = key + "_instance_generation_u8";
        if (fullId.isEmpty()) require(node.get(field).isNull(), "unread generation remains null");
        else require(integer(node, field, 0, 255) == fullId.orElseThrow() >>> 24, "generation differs");
    }
    private static Optional<BigInteger> delta(Optional<BigInteger> before, Optional<BigInteger> after) {
        return before.isPresent() && after.isPresent() ? Optional.of(after.orElseThrow().subtract(before.orElseThrow())) : Optional.empty();
    }
    private static Optional<Long> observedInteger(JsonNode node, String flag, String raw, long min, long max) {
        if (bool(node, flag)) return Optional.of(integer(node, raw, min, max));
        require(node.get(raw).isNull(), "unread raw remains null: " + raw); return Optional.empty();
    }
    private static Optional<BigInteger> observedWide(JsonNode node, String flag, String raw, boolean v2, boolean signed) {
        if (bool(node, flag)) return Optional.of(wide(node, raw, v2, signed));
        require(node.get(raw).isNull(), "unread raw remains null: " + raw); return Optional.empty();
    }
    private static BigInteger wide(JsonNode node, String key, boolean v2, boolean signed) {
        JsonNode raw = node.get(key); BigInteger min = signed ? I64_MIN : BigInteger.ZERO, max = signed ? I64_MAX : U64;
        if (v2) { require(raw != null && raw.isTextual(), "v2 canonical decimal string required: " + key); return decimal(raw.textValue(), min, max); }
        require(raw != null && raw.isIntegralNumber(), "v1 exact integer required: " + key);
        BigInteger value = raw.bigIntegerValue(); bounded(value, min.max(SAFE.negate()), max.min(SAFE)); return value;
    }
    private static BigInteger decimal(String value, BigInteger min, BigInteger max) {
        require(value != null && value.matches("0|-?[1-9][0-9]*") && value.length() <= 20, "canonical decimal required");
        BigInteger parsed = new BigInteger(value); bounded(parsed, min, max); return parsed;
    }
    private static void bounded(BigInteger value, BigInteger min, BigInteger max) {
        require(value != null && value.compareTo(min) >= 0 && value.compareTo(max) <= 0, "integer range differs");
    }
    private static void u32(long value) { require(value > 0 && value < 0xffff_ffffL, "full uint32 identity excludes sentinel"); }
    private static Set<String> union(Set<String> left, Set<String> right) { Set<String> value = new HashSet<>(left); value.addAll(right); return Set.copyOf(value); }
    private static void exact(JsonNode node, Set<String> fields) { StrictJson.object(node, fields); }
    private static long integer(JsonNode node, String field, long min, long max) { return StrictJson.integer(node.get(field), min, max); }
    private static String text(JsonNode node, String field) { return StrictJson.text(node.get(field)); }
    private static boolean bool(JsonNode node, String field) { JsonNode value = node.get(field); require(value != null && value.isBoolean(), "boolean required: " + field); return value.booleanValue(); }
    private static ProjectionJson copied(JsonNode node) { return ProjectionJson.object(StrictJson.canonical(node, MAX_BYTES), MAX_BYTES); }
    private static void require(boolean condition, String reason) { if (!condition) throw new IllegalArgumentException(reason); }
}
