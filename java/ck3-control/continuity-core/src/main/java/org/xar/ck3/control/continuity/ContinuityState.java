package org.xar.ck3.control.continuity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Immutable state with a typed origin/status and exact retained legacy history. */
public record ContinuityState(String machineId, long sequence, Origin origin, Status status,
                              long settledCycles, long settledDateRaw, byte[] canonicalBytes) {
    public enum Status {
        RUNNING("running"), REPAIR_REQUIRED("repair_required"), COMPLETE("complete"), AWAITING_FIRST_SAVE("awaiting_first_save"), AWAITING_INITIAL_ENTRY("awaiting_initial_entry");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Status fromWire(JsonNode value) {
            String wire = StrictJson.text(value);
            for (Status status : values()) { if (status.wire.equals(wire)) { return status; } }
            throw new ContractViolationException("continuity status");
        }
    }
    public record Origin(long windowId, long startDateRaw, long targetDateRaw, long targetDays) {
        public Origin {
            StrictJson.safe(windowId, 1); StrictJson.safe(startDateRaw, 0);
            StrictJson.safe(targetDateRaw, 0); StrictJson.safe(targetDays, 1);
            StrictJson.require(targetDateRaw - startDateRaw == Math.multiplyExact(targetDays, 24),
                    "continuity original target");
        }
    }
    public sealed interface PendingValue permits Missing, NullValue, Present { }
    public record Missing() implements PendingValue { }
    public record NullValue() implements PendingValue { }
    public record Present(byte[] canonicalBytes) implements PendingValue {
        public Present { canonicalBytes = canonicalBytes.clone(); }
        @Override public byte[] canonicalBytes() { return canonicalBytes.clone(); }
    }
    public ContinuityState {
        StrictJson.text(machineId); StrictJson.safe(sequence, 0);
        Objects.requireNonNull(status);
        if(status!=Status.AWAITING_INITIAL_ENTRY)Objects.requireNonNull(origin);
        StrictJson.safe(settledCycles, 0); StrictJson.safe(settledDateRaw, 0);
        canonicalBytes = canonicalBytes.clone();
        ObjectNode row = ContinuityJson.parseObject(canonicalBytes, ContinuityJson.LEDGER_MAX_BYTES);
        if(status==Status.AWAITING_INITIAL_ENTRY) {
            FreshContinuityGenesis.requirePreEntry(row);
            StrictJson.require(origin==null&&settledCycles==0&&settledDateRaw==0
                    &&StrictJson.text(row.get("machine_id")).equals(machineId)
                    &&number(row,"sequence",0)==sequence,"explicit unobserved genesis memory/JSON branch required");
        } else StrictJson.require(supportedSchema(row)
                && StrictJson.text(row.get("machine_id")).equals(machineId)
                && number(row, "sequence", 0) == sequence
                && number(row, "window_id", 1) == origin.windowId()
                && number(row, "start_date_raw", 0) == origin.startDateRaw()
                && number(row, "target_date_raw", 0) == origin.targetDateRaw()
                && number(row, "target_days", 1) == origin.targetDays()
                && Status.fromWire(row.get("status")) == status
                && number(row, "last_settled_cycles", 0) == settledCycles
                && number(row, "last_settled_date_raw", 0) == settledDateRaw,
                "typed continuity state equals its exact retained JSON");
        if(status!=Status.AWAITING_INITIAL_ENTRY)validateEpisode(row,origin,status); canonicalBytes = ContinuityJson.canonical(row);
    }
    @Override public byte[] canonicalBytes() { return canonicalBytes.clone(); }

    public static ContinuityState fromJson(JsonNode value, String machine) {
        ObjectNode row = ContinuityJson.object(value);
        StrictJson.require(supportedSchema(row)
                && StrictJson.text(row.get("machine_id")).equals(machine), "continuity schema/machine");
        if(FreshContinuityGenesis.STATE_SCHEMA.equals(StrictJson.text(row.get("schema"))))
            return new ContinuityState(machine,number(row,"sequence",0),null,Status.AWAITING_INITIAL_ENTRY,0,0,ContinuityJson.canonical(row));
        return new ContinuityState(machine, number(row, "sequence", 0),
                new Origin(number(row, "window_id", 1), number(row, "start_date_raw", 0),
                    number(row, "target_date_raw", 0), number(row, "target_days", 1)),
                Status.fromWire(row.get("status")), number(row, "last_settled_cycles", 0),
                number(row, "last_settled_date_raw", 0), ContinuityJson.canonical(row));
    }
    /** Historical pre-entry has no observed origin; business consumers must not turn absence into date zero. */
    public java.util.Optional<Origin> initializedOrigin() { return java.util.Optional.ofNullable(origin); }
    @Override public Origin origin() { return initializedOrigin().orElseThrow(()->new ContractViolationException("initial Game entry has not established an observed continuity origin")); }
    @Override public long settledDateRaw() {
        StrictJson.require(status!=Status.AWAITING_INITIAL_ENTRY,"pre-entry has no observed settled date");return settledDateRaw;
    }
    public ObjectNode toJson() { return ContinuityJson.parseObject(canonicalBytes, ContinuityJson.LEDGER_MAX_BYTES); }

    private static boolean supportedSchema(ObjectNode row) {
        String schema=StrictJson.text(row.get("schema"));
        return schema.equals("root.ck3.continuity-window/v1")||schema.equals(EpisodeWindow.STATE_SCHEMA)||schema.equals(FreshContinuityGenesis.STATE_SCHEMA);
    }
    private static void validateEpisode(ObjectNode row,Origin origin,Status status) {
        boolean version2=StrictJson.text(row.get("schema")).equals(EpisodeWindow.STATE_SCHEMA);
        StrictJson.require(version2==row.has(EpisodeWindow.FIELD),"explicit v2 window requires its versioned episode contract");
        if(!version2){StrictJson.require(status!=Status.AWAITING_FIRST_SAVE,"v1 has no first SAVE state");return;}
        EpisodeWindow.State episode=EpisodeWindow.State.fromJson(row.get(EpisodeWindow.FIELD));
        StrictJson.require(episode.begin().after().machineId().equals(StrictJson.text(row.get("machine_id"))),"episode machine differs from state");
        if(episode.phase()==EpisodeWindow.Phase.AWAITING_FIRST_SAVE){
            StrictJson.require(status==Status.AWAITING_FIRST_SAVE&&origin.windowId()==episode.begin().oldWindowId(),"BEGIN must retain old origin and await first SAVE");
        }else{
            StrictJson.require(status!=Status.AWAITING_FIRST_SAVE&&origin.windowId()==episode.begin().newWindowId()
                    &&origin.startDateRaw()==episode.baseline().orElseThrow().savedIdentity().dateRaw(),"ACTIVE origin differs from actual first SAVE baseline");
        }
    }

    /** No interpretation or replay: preserves missing, null and a present pending payload. */
    public PendingValue pendingCycle() {
        ObjectNode row = toJson();
        if (!row.has("pending_cycle")) { return new Missing(); }
        if (row.get("pending_cycle").isNull()) { return new NullValue(); }
        return new Present(ContinuityJson.canonical(row.get("pending_cycle")));
    }
    static long number(ObjectNode row, String field, long minimum) {
        return StrictJson.integer(row.get(field), minimum, StrictJson.MAX_SAFE_INTEGER);
    }
}
