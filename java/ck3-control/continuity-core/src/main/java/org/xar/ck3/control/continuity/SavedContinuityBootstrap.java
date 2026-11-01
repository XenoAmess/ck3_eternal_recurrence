package org.xar.ck3.control.continuity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.PublicRevision;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** Pure saved-source projection. The fixed Root authority supplies all current admission checks. */
public final class SavedContinuityBootstrap {
    public static final String KIND = "JAVA_CONFIRMED_SAVED_GAME_ENTRY";
    public static final String FIELD = "java_confirmed_saved_game_entry";
    public static final String SCHEMA = "xar.java-confirmed-saved-game-entry/v1";
    private static final Set<String> FIELDS = Set.of("schema", "evidence_id", "source",
            "saved_state_reference", "confirmation_reference", "source_head_reference",
            "saved_sequence", "saved_state_digest", "source_head_sequence", "source_head_digest",
            "saved_origin", "saved_completed_cycles", "saved_date_raw", "checkpoint_pair",
            "session", "opening", "full_driver", "driver_facts", "driver_version", "episode_epoch");
    private static final Set<String> FRESH_FIELDS = Set.of("schema", "machine_id", "sequence",
            "window_id", "status", "start_date_raw", "target_date_raw", "target_days",
            "last_settled_cycles", "last_settled_date_raw", "manual_repair_count",
            "automatic_recovery_count", "binding_lineage_count", "latest_binding", FreshContinuityGenesis.FIELD);
    private SavedContinuityBootstrap() { }

    /** Detached DATA is never a physical, live-session or private Writer admission. */
    public record Input(ContinuityState savedState, ExactRef savedStateReference, ExactRef confirmationReference,
            ContinuityState sourceHead, ExactRef sourceHeadReference, byte[] checkpointPair,
            byte[] session, byte[] opening, ExactRef fullDriver, ExactRef driverFacts,
            long driverVersion, long episodeEpoch) {
        public Input {
            Objects.requireNonNull(savedState); Objects.requireNonNull(savedStateReference);
            Objects.requireNonNull(confirmationReference); Objects.requireNonNull(sourceHead);
            Objects.requireNonNull(sourceHeadReference); Objects.requireNonNull(fullDriver); Objects.requireNonNull(driverFacts);
            checkpointPair = checkpointPair.clone(); session = session.clone(); opening = opening.clone();
            StrictJson.safe(driverVersion, 0); StrictJson.safe(episodeEpoch, 0);
        }
        @Override public byte[] checkpointPair() { return checkpointPair.clone(); }
        @Override public byte[] session() { return session.clone(); }
        @Override public byte[] opening() { return opening.clone(); }
    }

    public static WriterContracts.Request request(Input input, String evidenceId, JsonNode source) {
        return request(details(input, evidenceId, source));
    }

    /** Reconstruct the closed historical evidence descriptor without performing IO or minting permission. */
    public static WriterContracts.Request request(ObjectNode details) {
        validateDetails(details);
        return new WriterContracts.Request(KIND, ContinuityJson.canonical(details), evidence(details));
    }

    public static ObjectNode details(Input input, String evidenceId, JsonNode source) {
        Objects.requireNonNull(input);
        var saved = input.savedState(); var head = input.sourceHead();
        requireStateReference(saved, input.savedStateReference()); requireStateReference(head, input.sourceHeadReference());
        StrictJson.require(saved.status() == ContinuityState.Status.RUNNING || saved.status() == ContinuityState.Status.COMPLETE,
                "saved source must be its confirmed active historical state");
        StrictJson.require(saved.sequence() > 0 && head.sequence() >= saved.sequence()
                && saved.machineId().equals(head.machineId()) && saved.origin().equals(head.origin())
                && saved.settledCycles() == head.settledCycles() && saved.settledDateRaw() == head.settledDateRaw(),
                "source head must retain the exact confirmed saved campaign basis");
        var pair = object(input.checkpointPair()); var savedJson = saved.toJson();
        var slot = StrictJson.object(savedJson.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD), Set.of("pair", "state"));
        StrictJson.require(ContinuityJson.same(slot.get("pair"), pair)
                && ContinuityJson.same(slot, head.toJson().get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD))
                && ContinuityJson.same(slot.get("state"), savedJson.get(WriterContracts.ORDINARY_CYCLE_FIELD)),
                "confirmed pair and saved branch must survive unchanged in the actual source head");
        var cycle = ContinuityJson.object(slot.get("state"));
        StrictJson.require(number(cycle, "completed_cycles", 0) == saved.settledCycles()
                && cycle.has("pending_receipt") && cycle.get("pending_receipt").isNull()
                && cycle.hasNonNull("head") && !(saved.pendingCycle() instanceof ContinuityState.Present),
                "confirmed saved branch must be completed with no pending cycle");
        ExactRef.fromJson(cycle.get("head"));
        var savedObservation = validatePair(pair);
        StrictJson.require(savedObservation.machine().equals(saved.machineId())
                && savedObservation.game().equals(GameGeneration.fromJson(savedJson.get("game_binding")))
                && savedObservation.date() == saved.settledDateRaw(), "saved pair identity differs from confirmed state");
        var row = StrictJson.object(); row.put("schema", SCHEMA); row.put("evidence_id", StrictJson.text(evidenceId));
        row.set("source", Objects.requireNonNull(source).deepCopy());
        row.set("saved_state_reference", input.savedStateReference().toJson());
        row.set("confirmation_reference", input.confirmationReference().toJson());
        row.set("source_head_reference", input.sourceHeadReference().toJson());
        row.put("saved_sequence", saved.sequence()); row.put("saved_state_digest", ContinuityJson.digest(savedJson));
        row.put("source_head_sequence", head.sequence()); row.put("source_head_digest", ContinuityJson.digest(head.toJson()));
        var origin = row.putObject("saved_origin"); origin.put("window_id", saved.origin().windowId());
        origin.put("start_date_raw", saved.origin().startDateRaw()); origin.put("target_date_raw", saved.origin().targetDateRaw());
        origin.put("target_days", saved.origin().targetDays());
        row.put("saved_completed_cycles", saved.settledCycles()); row.put("saved_date_raw", saved.settledDateRaw());
        row.set("checkpoint_pair", pair); row.set("session", object(input.session())); row.set("opening", object(input.opening()));
        row.set("full_driver", input.fullDriver().toJson()); row.set("driver_facts", input.driverFacts().toJson());
        row.put("driver_version", input.driverVersion()); row.put("episode_epoch", input.episodeEpoch());
        // Request also enforces the original finite default details budget and truthy source contract.
        return request(row).detailsObject();
    }

    public static ContinuityState reduce(ContinuityState before, WriterContracts.Request request) {
        Objects.requireNonNull(before); Objects.requireNonNull(request);
        StrictJson.require(KIND.equals(request.kind()), "exact confirmed-saved entry kind required");
        var details = request.detailsObject(); validateDetails(details);
        StrictJson.require(request.evidence().equals(evidence(details)), "saved entry evidence descriptor changed");
        var next = StrictJson.object(before.toJson(), FRESH_FIELDS); FreshContinuityGenesis.requirePreEntry(next);
        StrictJson.require(before.status() == ContinuityState.Status.AWAITING_INITIAL_ENTRY && before.sequence() == 0,
                "saved admission only initializes an independent untouched fresh Writer");
        var origin = origin(details.get("saved_origin")); var opening = observation(details.get("opening"));
        var genesis = ContinuityJson.object(next.get(FreshContinuityGenesis.FIELD));
        StrictJson.require(before.machineId().equals(opening.machine())
                && number(genesis, "planned_window_id", 1) == origin.windowId()
                && number(genesis, "target_days", 1) == origin.targetDays(), "saved entry changed configured machine/window/policy");
        long date = number(details, "saved_date_raw", 0);
        next.put("schema", "root.ck3.continuity-window/v1"); next.put("window_id", origin.windowId());
        next.put("start_date_raw", origin.startDateRaw()); next.put("target_date_raw", origin.targetDateRaw());
        next.put("target_days", origin.targetDays()); next.put("last_settled_cycles", number(details, "saved_completed_cycles", 0));
        next.put("last_settled_date_raw", date); next.put("status", date >= origin.targetDateRaw() ? "complete" : "running");
        next.set("game_binding", opening.game().toJson());
        var binding = next.putObject("latest_binding"); binding.put("date_raw", date);
        binding.put("actor_character_id", opening.player().value()); binding.put("episode_run_id", opening.episode());
        binding.put("snapshot_id", opening.snapshot()); binding.put("revision", opening.revision());
        binding.put("native_revision", opening.nativeRevision());
        next.set(FIELD, details); next.set(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD, details.get("full_driver").deepCopy());
        return ContinuityState.fromJson(next, before.machineId());
    }

    public static void requireSavedAdmissionReduction(ContinuityState before, ContinuityState after,
            WriterContracts.Request request, boolean sequenced) {
        var expected = reduce(before, request).toJson();
        if (sequenced) {
            expected.put("sequence", Math.addExact(before.sequence(), 1)); expected.put("last_event_identity", request.identity());
        }
        StrictJson.require(ContinuityJson.same(expected, after.toJson()), "saved entry differs from its entire pure derived state");
    }

    private static void validateDetails(ObjectNode row) {
        StrictJson.object(row, FIELDS); StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))), "saved entry schema");
        StrictJson.text(row.get("evidence_id"));
        var source = row.get("source");
        StrictJson.require(source != null && !source.isNull() && (!source.isContainerNode() || !source.isEmpty())
                && (!source.isTextual() || !source.textValue().isEmpty()) && (!source.isBoolean() || source.booleanValue())
                && (!source.isNumber() || source.doubleValue() != 0), "saved entry exact source");
        var savedRef = pin(row.get("saved_state_reference")); var headRef = pin(row.get("source_head_reference"));
        pin(row.get("confirmation_reference")); pin(row.get("full_driver")); pin(row.get("driver_facts"));
        StrictJson.require(savedRef.bytes() <= ContinuityJson.LEDGER_MAX_BYTES && headRef.bytes() <= ContinuityJson.LEDGER_MAX_BYTES
                && savedRef.sha256().equals(StrictJson.text(row.get("saved_state_digest")))
                && headRef.sha256().equals(StrictJson.text(row.get("source_head_digest")))
                && number(row, "saved_sequence", 1) <= number(row, "source_head_sequence", 1), "exact bounded saved/source state projection");
        var origin = origin(row.get("saved_origin")); long date = number(row, "saved_date_raw", 0);
        StrictJson.require(date >= origin.startDateRaw(), "saved date predates its original campaign basis");
        number(row, "saved_completed_cycles", 0); number(row, "driver_version", 0); number(row, "episode_epoch", 0);
        var saved = validatePair(ContinuityJson.object(row.get("checkpoint_pair"))); var opening = observation(row.get("opening"));
        var session = StrictJson.object(row.get("session"), Set.of("machine_id", "game", "session_id"));
        StrictJson.text(session.get("session_id"));
        StrictJson.require(saved.date() == date && opening.date() == date && saved.player().equals(opening.player())
                && saved.machine().equals(opening.machine()) && saved.version() == opening.version()
                && opening.machine().equals(StrictJson.text(session.get("machine_id")))
                && opening.game().equals(GameGeneration.fromJson(session.get("game")))
                && !saved.game().equals(opening.game())
                && !saved.game().creationFiletime().equals(opening.game().creationFiletime()),
                "new loaded Game/owner must retain saved actor/date and have an independent actual birth");
    }

    private static List<ExactRef> evidence(ObjectNode row) {
        return List.of(pin(row.get("saved_state_reference")), pin(row.get("confirmation_reference")),
                pin(row.get("source_head_reference")), pin(row.get("full_driver")), pin(row.get("driver_facts")))
                .stream().distinct().toList();
    }
    private static ExactRef pin(JsonNode value) {
        var ref = ExactRef.fromJson(value);
        StrictJson.require(ref.bytes() > 0 && ref.bytes() <= WriterContracts.MAX_PIN_BYTES, "bounded saved entry evidence original required");
        return ref;
    }
    private static void requireStateReference(ContinuityState state, ExactRef ref) {
        StrictJson.require(ref.bytes() == state.canonicalBytes().length && ref.sha256().equals(ContinuityJson.digest(state.toJson())),
                "saved/source reference differs from complete exact archived state bytes");
    }
    private static ContinuityState.Origin origin(JsonNode value) {
        var row = StrictJson.object(value, Set.of("window_id", "start_date_raw", "target_date_raw", "target_days"));
        return new ContinuityState.Origin(number(row, "window_id", 1), number(row, "start_date_raw", 0),
                number(row, "target_date_raw", 0), number(row, "target_days", 1));
    }
    private static Observation validatePair(ObjectNode row) {
        StrictJson.object(row, Set.of("schema", "save", "driver", "frame", "lineage_id", "history_index",
                "save_action_id", "native_ack_ref", "observed_at_utc"));
        StrictJson.require("xar.java-checkpoint-pair/v1".equals(StrictJson.text(row.get("schema"))), "saved pair schema");
        var save = fileWitness(row.get("save")); var driver = fileWitness(row.get("driver"));
        StrictJson.require(save.bytes() > 0 && driver.bytes() > 0 && !save.path().equals(driver.path()), "positive independent saved pair");
        StrictJson.text(row.get("lineage_id")); number(row, "history_index", 1); StrictJson.text(row.get("save_action_id"));
        StrictJson.require(ExactRef.fromJson(row.get("native_ack_ref")).bytes() > 0, "saved ACK original required");
        Instant.parse(StrictJson.utc(StrictJson.text(row.get("observed_at_utc")))); return observation(row.get("frame"));
    }
    private static ExactRef fileWitness(JsonNode value) {
        var row = StrictJson.object(value, Set.of("ref", "identity_schema", "identity")); var ref = ExactRef.fromJson(row.get("ref"));
        var identity = FileStatIdentity.fromJson(row.get("identity"), StrictJson.text(row.get("identity_schema")));
        StrictJson.require(identity.bytes().equals(BigInteger.valueOf(ref.bytes())), "exact physical pair file identity size"); return ref;
    }
    private record Observation(String machine, GameGeneration game, long version, String snapshot,
            BigInteger revision, BigInteger nativeRevision, long date, NativeCharacterId player, String episode) { }
    private static Observation observation(JsonNode value) {
        var row = StrictJson.object(value, Set.of("machine_id", "game", "observation_version", "frame"));
        var frame = StrictJson.object(row.get("frame"), Set.of("played_character_id", "native_revision", "date_raw",
                "snapshot_id", "revision", "episode_run_id"));
        String actor = StrictJson.text(frame.get("played_character_id"));
        StrictJson.require(actor.matches("0|-?[1-9][0-9]*") && actor.length() <= 11, "canonical signed character decimal required");
        var player = NativeCharacterId.of(new BigInteger(actor)); var nativeRevision = decimal(frame.get("native_revision"));
        StrictJson.require(nativeRevision.signum() > 0, "positive native revision required");
        long date = decimal(frame.get("date_raw")).longValueExact(); StrictJson.safe(date, 0);
        return new Observation(StrictJson.text(row.get("machine_id")), GameGeneration.fromJson(row.get("game")),
                number(row, "observation_version", 1), StrictJson.text(frame.get("snapshot_id")),
                PublicRevision.decimal(StrictJson.text(frame.get("revision"))).value(), nativeRevision,
                date, player, StrictJson.text(frame.get("episode_run_id")));
    }
    private static BigInteger decimal(JsonNode value) {
        String text = StrictJson.text(value);
        StrictJson.require(text.matches("0|[1-9][0-9]*") && text.length() <= 20, "canonical uint64 decimal required");
        var result = new BigInteger(text); StrictJson.require(result.compareTo(StrictJson.UINT64_MAX) <= 0, "uint64 decimal range"); return result;
    }
    private static ObjectNode object(byte[] raw) { return ContinuityJson.parseObject(raw, StrictJson.INPUT_MAX_BYTES); }
    private static long number(ObjectNode row, String field, long minimum) {
        return StrictJson.integer(row.get(field), minimum, StrictJson.MAX_SAFE_INTEGER);
    }
}
