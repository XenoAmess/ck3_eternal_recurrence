package org.xar.ck3.control.application.checkpoint;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import org.xar.ck3.control.contracts.NativeCharacterId;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;

/** Complete original Driver v2 envelope. Legacy nested business values are retained, never invented. */
public sealed interface DriverStateSnapshot permits DriverStateSnapshot.Complete, DriverStateSnapshot.Incomplete {
    record Incomplete(List<String> missingOrUnreconciledFields) implements DriverStateSnapshot {
        public Incomplete { missingOrUnreconciledFields = List.copyOf(missingOrUnreconciledFields); StrictJson.require(!missingOrUnreconciledFields.isEmpty(), "explicit incomplete Driver reasons"); }
    }
    sealed interface Slot permits Missing, NullValue, Value { }
    record Missing() implements Slot { }
    record NullValue() implements Slot { }
    record Value(byte[] json) implements Slot {
        public Value { json = checked(json); }
        @Override public byte[] json() { return json.clone(); }
        @Override public boolean equals(Object other) { return other instanceof Value value && java.util.Arrays.equals(json,value.json); }
        @Override public int hashCode() { return java.util.Arrays.hashCode(json); }
    }
    record HistoryEntry(long index, Value originalRow) {
        public HistoryEntry { StrictJson.safe(index, 1); Objects.requireNonNull(originalRow);
            StrictJson.require(historyIndex(originalRow) == index, "history entry typed index equals original integer token"); }
    }
    record Session(String pipeName, long bridgePid, BigInteger actorId, String episodeRunId) {
        public Session { StrictJson.text(pipeName); StrictJson.require(bridgePid > 0 && bridgePid <= 0xffff_ffffL, "uint32 Driver PID"); NativeCharacterId.of(actorId); StrictJson.text(episodeRunId); }
    }
    record Complete(Session session, List<HistoryEntry> commandHistory, Slot lastCheckpoint, Slot rollbackWarFailure,
            Slot managedRestoreTransaction, Slot successionExpectation, Slot successionLifecycle, Slot campaignGoal,
            Slot rollbackWarFailures) implements DriverStateSnapshot {
        // Exact, one-use constructor identities; never a cache or a caller-declared trust flag.
        private static final ThreadLocal<java.util.IdentityHashMap<Object, Object>> CONSTRUCTION = new ThreadLocal<>();
        // Same factory configuration as the unchanged complete-material encoder; private parser trees only.
        private static final com.fasterxml.jackson.databind.ObjectMapper PARSED_JSON = new com.fasterxml.jackson.databind.ObjectMapper(
                com.fasterxml.jackson.core.JsonFactory.builder()
                        .enable(com.fasterxml.jackson.core.StreamReadFeature.STRICT_DUPLICATE_DETECTION)
                        .streamReadConstraints(com.fasterxml.jackson.core.StreamReadConstraints.builder().maxNestingDepth(64)
                                .maxStringLength(FullJsonTree.MAXIMUM_DRIVER_BYTES)
                                .maxNumberLength(FullJsonTree.MAXIMUM_DRIVER_BYTES).build()).build());
        public Complete {
            Objects.requireNonNull(session); commandHistory = List.copyOf(commandHistory);
            for (int i = 0; i < commandHistory.size(); i++) StrictJson.require(commandHistory.get(i).index() == i + 1L, "complete ordered Driver history");
            for (Slot slot : List.of(lastCheckpoint, rollbackWarFailure, managedRestoreTransaction, successionExpectation, successionLifecycle, campaignGoal, rollbackWarFailures)) Objects.requireNonNull(slot);
            StrictJson.require(!(lastCheckpoint instanceof Missing) && !(rollbackWarFailure instanceof Missing) && !(managedRestoreTransaction instanceof Missing)
                    && !(successionExpectation instanceof Missing) && !(campaignGoal instanceof Missing), "required original Driver fields may be null, never absent");
        }
        /** Strict bytes stay local; only detached typed DATA reaches the fixed anchor verifier. */
        static Complete decodeAndVerify(byte[] raw, java.util.function.BiConsumer<Complete, ObjectNode> verifier) {
            Objects.requireNonNull(verifier);
            byte[] owned = raw == null || raw.length == 0 || raw.length > DriverCheckpointStore.MAX_DRIVER_BYTES ? raw : raw.clone();
            ObjectNode row = object(parse(owned));
            Complete complete = decodeParsedComplete(row, provenStable(owned));
            verifier.accept(complete, row);
            return complete;
        }
        public byte[] encode() {
            if (!canEmbedOwnedValues()) return legacyEncode();
            return encodeOwnedValues();
        }
        /** Only immutable private Value bytes enter this lane. Borderline domains keep the entire old encoder. */
        private boolean canEmbedOwnedValues() {
            if (session.actorId().getClass() != BigInteger.class || hasSurrogate(session.pipeName())
                    || hasSurrogate(session.episodeRunId())) return false;
            for (HistoryEntry entry : commandHistory) if (!embeddableOwned(entry.originalRow().json, 2)) return false;
            for (Slot slot : List.of(lastCheckpoint, rollbackWarFailure, managedRestoreTransaction, successionExpectation,
                    successionLifecycle, campaignGoal, rollbackWarFailures))
                if (slot instanceof Value value && !embeddableOwned(value.json, 1)) return false;
            return true;
        }
        /** Structural depth of already validated canonical bytes, never an alternative JSON parser. */
        private static boolean embeddableOwned(byte[] raw, int enclosingDepth) {
            int containers = 0; boolean quoted = false, escaped = false;
            for (int index = 0; index < raw.length; index++) {
                int token = raw[index] & 0xff;
                // Match the existing private stable round-trip domain. Non-BMP/escaped Unicode is legacy.
                if (token >= 0xf0 || token == 0x5c && index + 1 < raw.length && raw[index + 1] == 0x75) return false;
                if (quoted) {
                    if (escaped) escaped = false;
                    else if (token == 0x5c) escaped = true;
                    else if (token == 0x22) quoted = false;
                    continue;
                }
                if (token == 0x7d || token == 0x5d) { if (--containers < 0) return false; continue; }
                if (token == 0x20 || token == 0x09 || token == 0x0a || token == 0x0d || token == 0x2c || token == 0x3a) continue;
                // Deliberately leave depth64 and its adjacent boundary to the original full-tree validation.
                if (containers + enclosingDepth >= 64) return false;
                if (token == 0x22) quoted = true;
                else if (token == 0x7b || token == 0x5b) containers++;
            }
            return containers == 0 && !quoted && !escaped;
        }
        private byte[] encodeOwnedValues() {
            ObjectNode row = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode(); row.put("format_version", 2); row.put("pipe_name", session.pipeName()); row.put("bridge_pid", session.bridgePid());
            row.put("episode_character_id", session.actorId()); row.put("episode_run_id", session.episodeRunId());
            // The original sole tree encoder owns scalar quoting and integer representation.
            byte[] header = bytes(row);
            long size;
            try {
                size = Math.addExact(header.length - 1L, "command_history".length() + 7L);
                for (int index = 0; index < commandHistory.size(); index++)
                    size = Math.addExact(size, commandHistory.get(index).originalRow().json.length + (index == 0 ? 0L : 1L));
                size = Math.addExact(size, ownedSlotBytes("last_checkpoint", lastCheckpoint));
                size = Math.addExact(size, ownedSlotBytes("rollback_war_failure", rollbackWarFailure));
                size = Math.addExact(size, ownedSlotBytes("managed_restore_transaction", managedRestoreTransaction));
                size = Math.addExact(size, ownedSlotBytes("succession_expectation", successionExpectation));
                size = Math.addExact(size, ownedSlotBytes("succession_lifecycle", successionLifecycle));
                size = Math.addExact(size, ownedSlotBytes("campaign_goal", campaignGoal));
                size = Math.addExact(size, ownedSlotBytes("rollback_war_failures", rollbackWarFailures));
            } catch (ArithmeticException unprovenLength) { return legacyEncode(); }
            if (size > DriverCheckpointStore.MAX_DRIVER_BYTES) return legacyEncode();
            var output = new java.io.ByteArrayOutputStream((int) size);
            output.write(header, 0, header.length - 1); ownedField(output, "command_history"); output.write(0x5b);
            for (int index = 0; index < commandHistory.size(); index++) {
                if (index != 0) output.write(0x2c);
                output.writeBytes(commandHistory.get(index).originalRow().json);
            }
            output.write(0x5d);
            putOwned(output,"last_checkpoint",lastCheckpoint); putOwned(output,"rollback_war_failure",rollbackWarFailure); putOwned(output,"managed_restore_transaction",managedRestoreTransaction);
            putOwned(output,"succession_expectation",successionExpectation); putOwned(output,"succession_lifecycle",successionLifecycle); putOwned(output,"campaign_goal",campaignGoal); putOwned(output,"rollback_war_failures",rollbackWarFailures);
            output.write(0x7d);
            return output.toByteArray();
        }
        private static long ownedSlotBytes(String name, Slot slot) {
            return slot instanceof Missing ? 0L : name.length() + 4L + (slot instanceof Value value ? value.json.length : 4L);
        }
        private static void ownedField(java.io.ByteArrayOutputStream output, String name) {
            output.write(0x2c); output.write(0x22); output.writeBytes(name.getBytes(java.nio.charset.StandardCharsets.US_ASCII)); output.write(0x22); output.write(0x3a);
        }
        private static void putOwned(java.io.ByteArrayOutputStream output, String name, Slot slot) {
            if (slot instanceof Missing) return;
            ownedField(output, name);
            if (slot instanceof Value value) output.writeBytes(value.json);
            else { output.write(0x6e); output.write(0x75); output.write(0x6c); output.write(0x6c); }
        }
        private byte[] legacyEncode() {
            ObjectNode row = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode(); row.put("format_version", 2); row.put("pipe_name", session.pipeName()); row.put("bridge_pid", session.bridgePid());
            row.put("episode_character_id", session.actorId()); row.put("episode_run_id", session.episodeRunId());
            var history = row.putArray("command_history"); commandHistory.forEach(entry -> history.add(parse(entry.originalRow().json)));
            put(row,"last_checkpoint",lastCheckpoint); put(row,"rollback_war_failure",rollbackWarFailure); put(row,"managed_restore_transaction",managedRestoreTransaction);
            put(row,"succession_expectation",successionExpectation); put(row,"succession_lifecycle",successionLifecycle); put(row,"campaign_goal",campaignGoal); put(row,"rollback_war_failures",rollbackWarFailures);
            return bytes(row);
        }
    }
    static Complete decodeComplete(byte[] raw) {
        byte[] owned = raw == null || raw.length == 0 || raw.length > DriverCheckpointStore.MAX_DRIVER_BYTES ? raw : raw.clone();
        ObjectNode row = object(parse(owned));
        return decodeParsedComplete(row, provenStable(owned));
    }
    private static Complete decodeParsedComplete(ObjectNode row, boolean provenStable) {
        Set<String> allowed = Set.of("format_version","pipe_name","bridge_pid","episode_character_id","episode_run_id","last_checkpoint","command_history","rollback_war_failure","managed_restore_transaction","succession_expectation","succession_lifecycle","campaign_goal","rollback_war_failures");
        row.fieldNames().forEachRemaining(key -> StrictJson.require(allowed.contains(key), "unmigrated top-level Driver field: " + key));
        StrictJson.integer(row.get("format_version"), 2, 2); StrictJson.require(row.get("command_history") != null && row.get("command_history").isArray(), "full Driver history required");
        List<HistoryEntry> history = new ArrayList<>(); for (JsonNode item : row.get("command_history")) { ObjectNode entry = object(item); history.add(parsedEntry(entry, provenStable)); }
        return new Complete(new Session(StrictJson.text(row.get("pipe_name")), StrictJson.integer(row.get("bridge_pid"), 1, 0xffff_ffffL),
                NativeCharacterId.fromJson(row.get("episode_character_id")).asBigInteger(), StrictJson.text(row.get("episode_run_id"))), history,
                slot(row,"last_checkpoint",provenStable),slot(row,"rollback_war_failure",provenStable),slot(row,"managed_restore_transaction",provenStable),slot(row,"succession_expectation",provenStable),slot(row,"succession_lifecycle",provenStable),slot(row,"campaign_goal",provenStable),slot(row,"rollback_war_failures",provenStable));
    }
    private static Slot slot(ObjectNode row, String key, boolean provenStable) { return !row.has(key) ? new Missing() : row.get(key).isNull() ? new NullValue() : parsedValue(row.get(key), provenStable); }
    private static void put(ObjectNode row, String key, Slot slot) { switch (slot) { case Missing ignored -> { } case NullValue ignored -> row.putNull(key); case Value value -> row.set(key,parse(value.json)); } }
    private static byte[] checked(byte[] raw) {
        var scope = Complete.CONSTRUCTION.get();
        if (raw != null && scope != null && scope.remove(raw) == raw) return raw.clone();
        JsonNode value=parse(raw); StrictJson.require(!value.isNull(),"null has its own explicit Driver slot"); return bytes(value);
    }
    private static long historyIndex(Value value) {
        var scope = Complete.CONSTRUCTION.get();
        Object index = scope == null ? null : scope.remove(value);
        if (index instanceof Long original) return original;
        ObjectNode row = object(parse(value.json));
        return StrictJson.integer(row.get("index"), 1, StrictJson.MAX_SAFE_INTEGER);
    }
    // Private parsing supplies tree checks; encoding retains the original byte lease.
    private static Value parsedValue(JsonNode node, boolean provenStable) {
        byte[] raw = encodeParsed(node);
        if (!provenStable && !stableParserTree(node)) return new Value(raw);
        var previous = Complete.CONSTRUCTION.get();
        var scope = new java.util.IdentityHashMap<Object, Object>();
        scope.put(raw, raw); Complete.CONSTRUCTION.set(scope);
        try { return new Value(raw); }
        finally { if (previous == null) Complete.CONSTRUCTION.remove(); else Complete.CONSTRUCTION.set(previous); }
    }
    private static HistoryEntry parsedEntry(ObjectNode node, boolean provenStable) {
        long index = StrictJson.integer(node.get("index"), 1, StrictJson.MAX_SAFE_INTEGER);
        byte[] raw = encodeParsed(node);
        if (!provenStable && !stableParserTree(node)) return new HistoryEntry(index, new Value(raw));
        var previous = Complete.CONSTRUCTION.get();
        var scope = new java.util.IdentityHashMap<Object, Object>();
        scope.put(raw, raw); Complete.CONSTRUCTION.set(scope);
        try {
            Value value = new Value(raw);
            scope.put(value, index);
            return new HistoryEntry(index, value);
        } finally { if (previous == null) Complete.CONSTRUCTION.remove(); else Complete.CONSTRUCTION.set(previous); }
    }
    // Surrogate handling can affect an encode/parse round trip; retain the original constructors for that domain.
    private static boolean stableParserTree(JsonNode node) {
        if (node.isTextual() && hasSurrogate(node.textValue())) return false;
        if (node.isObject()) {
            var names = node.fieldNames();
            while (names.hasNext()) if (hasSurrogate(names.next())) return false;
        }
        for (JsonNode child : node) if (!stableParserTree(child)) return false;
        return true;
    }
    private static boolean hasSurrogate(String text) {
        for (int i = 0; i < text.length(); i++) if (Character.isSurrogate(text.charAt(i))) return true;
        return false;
    }

    private static boolean provenStable(byte[] raw) {
        if (raw == null) return false;
        for (int i = 0; i < raw.length; i++) {
            int b = raw[i] & 0xFF;
            if (b == 0x5C && i + 1 < raw.length && raw[i + 1] == 0x75) return false;
            if (b >= 0xF0) return false;
        }
        return true;
    }
    private static JsonNode parse(byte[] raw) {
        // The sole material parser validates JSON tokens. Opaque decimal lexemes are not binary64 fields.
        return FullJsonTree.parse(raw,DriverCheckpointStore.MAX_DRIVER_BYTES);
    }
    private static ObjectNode object(JsonNode node) { StrictJson.require(node instanceof ObjectNode, "Driver object required"); return (ObjectNode)node; }
    private static byte[] bytes(JsonNode node) { return FullJsonTree.encode(node,DriverCheckpointStore.MAX_DRIVER_BYTES); }

    /** Only private strict-parser subtrees reach this encoder before any verifier callback. */
    private static byte[] encodeParsed(JsonNode node) {
        StrictJson.require(DriverCheckpointStore.MAX_DRIVER_BYTES > 0
                && DriverCheckpointStore.MAX_DRIVER_BYTES <= FullJsonTree.MAXIMUM_DRIVER_BYTES,
                "finite complete JSON material lease required");
        try {
            byte[] result = Complete.PARSED_JSON.writeValueAsBytes(node);
            StrictJson.require(result.length <= DriverCheckpointStore.MAX_DRIVER_BYTES, "complete JSON material exceeds its explicit lease");
            return result;
        } catch (IOException failure) {
            throw new IllegalArgumentException("complete JSON encoding failed", failure);
        }
    }
}
