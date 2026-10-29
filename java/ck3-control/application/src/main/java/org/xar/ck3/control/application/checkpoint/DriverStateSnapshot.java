package org.xar.ck3.control.application.checkpoint;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
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
        public HistoryEntry { StrictJson.safe(index, 1); Objects.requireNonNull(originalRow); ObjectNode row = object(parse(originalRow.json()));
            StrictJson.require(StrictJson.integer(row.get("index"), 1, StrictJson.MAX_SAFE_INTEGER) == index, "history entry typed index equals original integer token"); }
    }
    record Session(String pipeName, long bridgePid, BigInteger actorId, String episodeRunId) {
        public Session { StrictJson.text(pipeName); StrictJson.require(bridgePid > 0 && bridgePid <= 0xffff_ffffL, "uint32 Driver PID"); NativeCharacterId.of(actorId); StrictJson.text(episodeRunId); }
    }
    record Complete(Session session, List<HistoryEntry> commandHistory, Slot lastCheckpoint, Slot rollbackWarFailure,
            Slot managedRestoreTransaction, Slot successionExpectation, Slot successionLifecycle, Slot campaignGoal,
            Slot rollbackWarFailures) implements DriverStateSnapshot {
        public Complete {
            Objects.requireNonNull(session); commandHistory = List.copyOf(commandHistory);
            for (int i = 0; i < commandHistory.size(); i++) StrictJson.require(commandHistory.get(i).index() == i + 1L, "complete ordered Driver history");
            for (Slot slot : List.of(lastCheckpoint, rollbackWarFailure, managedRestoreTransaction, successionExpectation, successionLifecycle, campaignGoal, rollbackWarFailures)) Objects.requireNonNull(slot);
            StrictJson.require(!(lastCheckpoint instanceof Missing) && !(rollbackWarFailure instanceof Missing) && !(managedRestoreTransaction instanceof Missing)
                    && !(successionExpectation instanceof Missing) && !(campaignGoal instanceof Missing), "required original Driver fields may be null, never absent");
        }
        public byte[] encode() {
            ObjectNode row = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode(); row.put("format_version", 2); row.put("pipe_name", session.pipeName()); row.put("bridge_pid", session.bridgePid());
            row.put("episode_character_id", session.actorId()); row.put("episode_run_id", session.episodeRunId());
            var history = row.putArray("command_history"); commandHistory.forEach(entry -> history.add(parse(entry.originalRow().json())));
            put(row,"last_checkpoint",lastCheckpoint); put(row,"rollback_war_failure",rollbackWarFailure); put(row,"managed_restore_transaction",managedRestoreTransaction);
            put(row,"succession_expectation",successionExpectation); put(row,"succession_lifecycle",successionLifecycle); put(row,"campaign_goal",campaignGoal); put(row,"rollback_war_failures",rollbackWarFailures);
            return bytes(row);
        }
    }
    static Complete decodeComplete(byte[] raw) {
        ObjectNode row = object(parse(raw)); Set<String> allowed = Set.of("format_version","pipe_name","bridge_pid","episode_character_id","episode_run_id","last_checkpoint","command_history","rollback_war_failure","managed_restore_transaction","succession_expectation","succession_lifecycle","campaign_goal","rollback_war_failures");
        row.fieldNames().forEachRemaining(key -> StrictJson.require(allowed.contains(key), "unmigrated top-level Driver field: " + key));
        StrictJson.integer(row.get("format_version"), 2, 2); StrictJson.require(row.get("command_history") != null && row.get("command_history").isArray(), "full Driver history required");
        List<HistoryEntry> history = new ArrayList<>(); for (JsonNode item : row.get("command_history")) { ObjectNode entry = object(item); history.add(new HistoryEntry(StrictJson.integer(entry.get("index"), 1, StrictJson.MAX_SAFE_INTEGER), new Value(bytes(entry)))); }
        return new Complete(new Session(StrictJson.text(row.get("pipe_name")), StrictJson.integer(row.get("bridge_pid"), 1, 0xffff_ffffL),
                NativeCharacterId.fromJson(row.get("episode_character_id")).asBigInteger(), StrictJson.text(row.get("episode_run_id"))), history,
                slot(row,"last_checkpoint"),slot(row,"rollback_war_failure"),slot(row,"managed_restore_transaction"),slot(row,"succession_expectation"),slot(row,"succession_lifecycle"),slot(row,"campaign_goal"),slot(row,"rollback_war_failures"));
    }
    private static Slot slot(ObjectNode row, String key) { return !row.has(key) ? new Missing() : row.get(key).isNull() ? new NullValue() : new Value(bytes(row.get(key))); }
    private static void put(ObjectNode row, String key, Slot slot) { switch (slot) { case Missing ignored -> { } case NullValue ignored -> row.putNull(key); case Value value -> row.set(key,parse(value.json())); } }
    private static byte[] checked(byte[] raw) { JsonNode value=parse(raw); StrictJson.require(!value.isNull(),"null has its own explicit Driver slot"); return bytes(value); }
    private static JsonNode parse(byte[] raw) {
        // The sole material parser validates JSON tokens. Opaque decimal lexemes are not binary64 fields.
        return FullJsonTree.parse(raw,DriverCheckpointStore.MAX_DRIVER_BYTES);
    }
    private static ObjectNode object(JsonNode node) { StrictJson.require(node instanceof ObjectNode, "Driver object required"); return (ObjectNode)node; }
    private static byte[] bytes(JsonNode node) { return FullJsonTree.encode(node,DriverCheckpointStore.MAX_DRIVER_BYTES); }
}
