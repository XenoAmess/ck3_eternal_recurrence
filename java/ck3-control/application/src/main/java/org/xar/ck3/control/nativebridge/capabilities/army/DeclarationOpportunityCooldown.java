package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Original two-round declaration opportunity cooldown. Pure transitions; the sole Driver auxiliary writer persists the returned state. */
public final class DeclarationOpportunityCooldown {
    public static final String SCHEMA = "xar.ck3.declaration-opportunity-cooldown/v1";
    public static final String VIEW_KEY = "declaration_opportunity_cooldown_v1";
    public static final String LEGACY_FILENAME = "declaration-opportunity-cooldown-v1.json";
    public static final BigInteger COOLDOWN_RAW_DAYS = BigInteger.valueOf(30 * 24);
    private DeclarationOpportunityCooldown() { }
    public record Frame(BigInteger actorCharacterId, String episodeRunId, BigInteger dateRaw, BigInteger nativeRevision,
            BigInteger bridgePid, Optional<String> snapshotId) {
        public Frame { positiveValue(actorCharacterId); nonemptyValue(episodeRunId); positiveValue(dateRaw); positiveValue(nativeRevision);
            positiveValue(bridgePid); Objects.requireNonNull(snapshotId); snapshotId.ifPresent(DeclarationOpportunityCooldown::nonemptyValue); }
    }
    public sealed interface WarId permits NumericWarId, TextWarId { }
    /** Stored legacy identities retain numeric versus textual JSON token kind; a numeric zero is not verified-war credit in the original reducer. */
    public record NumericWarId(BigInteger value) implements WarId { public NumericWarId { Objects.requireNonNull(value); } }
    public record TextWarId(String value) implements WarId { public TextWarId { nonemptyValue(value); } }
    public record Pending(UInt64 querySequence, Optional<String> sourceSnapshotId, BigInteger sourceNativeRevision,
            BigInteger sourceDateRaw, BigInteger sourceBridgePid) {
        public Pending { Objects.requireNonNull(querySequence); positiveValue(querySequence.value()); Objects.requireNonNull(sourceSnapshotId); sourceSnapshotId.ifPresent(DeclarationOpportunityCooldown::nonemptyValue);
            positiveValue(sourceNativeRevision); positiveValue(sourceDateRaw); positiveValue(sourceBridgePid); }
    }
    public record State(BigInteger actorCharacterId, String episodeRunId, int consecutiveNoWarRounds, Optional<BigInteger> cooldownUntilDateRaw,
            Optional<Pending> pendingQuery, Optional<UInt64> lastClosedQuerySequence, Optional<WarId> lastConfirmedWarId) {
        public State { positiveValue(actorCharacterId); nonemptyValue(episodeRunId); require(consecutiveNoWarRounds >= 0 && consecutiveNoWarRounds <= 2, "cooldown streak outside 0..2");
            Objects.requireNonNull(cooldownUntilDateRaw); Objects.requireNonNull(pendingQuery); Objects.requireNonNull(lastClosedQuerySequence); lastClosedQuerySequence.ifPresent(value -> positiveValue(value.value())); Objects.requireNonNull(lastConfirmedWarId); }
    }
    public record View(boolean active, int consecutiveNoWarRounds, Optional<BigInteger> cooldownUntilDateRaw, BigInteger remainingDays,
            Optional<UInt64> pendingQuerySequence, BigInteger actorCharacterId, String episodeRunId) {
        public View { Objects.requireNonNull(cooldownUntilDateRaw); Objects.requireNonNull(remainingDays); Objects.requireNonNull(pendingQuerySequence); positiveValue(actorCharacterId); nonemptyValue(episodeRunId);
            require(consecutiveNoWarRounds >= 0 && consecutiveNoWarRounds <= 2 && remainingDays.signum() >= 0, "malformed cooldown view count");
            require(active ? cooldownUntilDateRaw.isPresent() && remainingDays.signum() > 0 : remainingDays.signum() == 0, "cooldown view status/deadline/day contradiction");
            pendingQuerySequence.ifPresent(value -> positiveValue(value.value())); }
    }
    public record Reduction(State state, View view) { public Reduction { Objects.requireNonNull(state); Objects.requireNonNull(view); } }
    public record War(WarId id, boolean playerAttacker) { public War { Objects.requireNonNull(id); } }
    public record Continuity(boolean schemaMatches, Optional<String> status, boolean nativeAccepted, boolean postconditionVerified, Optional<WarId> warId) {
        public Continuity { Objects.requireNonNull(status); Objects.requireNonNull(warId); }
    }
    /** Presence means an actual array was observed; event/interaction are the original object-presence predicates. */
    public record Snapshot(boolean paused, Optional<List<War>> activeWars, boolean activeEvent, boolean pendingInteraction, Optional<Continuity> continuity) {
        public Snapshot { Objects.requireNonNull(activeWars); activeWars = activeWars.map(List::copyOf); Objects.requireNonNull(continuity); }
        public static Snapshot empty() { return new Snapshot(false, Optional.empty(), false, false, Optional.empty()); }
    }
    public record TurnResult(String step, String progressStatus, boolean paused, Optional<BigInteger> startingDateRaw, Optional<BigInteger> endingDateRaw) {
        public TurnResult { Objects.requireNonNull(step); Objects.requireNonNull(progressStatus); Objects.requireNonNull(startingDateRaw); Objects.requireNonNull(endingDateRaw); }
    }
    public record Outcome(boolean executed, Optional<String> selectedStep, Optional<TurnResult> result) {
        public Outcome { Objects.requireNonNull(selectedStep); Objects.requireNonNull(result); }
    }
    public static State initial(Frame frame) {
        Objects.requireNonNull(frame); return new State(frame.actorCharacterId(), frame.episodeRunId(), 0, Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty());
    }
    public static Frame frame(Context actual) {
        Objects.requireNonNull(actual); return new Frame(actual.playerId(), actual.before().frame().episodeRunId(), actual.dateRaw(), actual.nativeRevision(),
                BigInteger.valueOf(actual.before().game().pid()), Optional.of(actual.before().frame().snapshotId()));
    }
    public static Frame frame(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete actual) {
        Objects.requireNonNull(actual); var frame = actual.identity().frame();
        return new Frame(frame.identity().player(), frame.episodeRunId(), frame.identity().dateRaw(), frame.identity().nativeRevision(),
                BigInteger.valueOf(actual.identity().game().pid()), Optional.of(frame.snapshotId()));
    }
    /** Strict old-schema input. Earlier v1 saved deadlines imply streak2 even after expiry; different owners start clean. */
    public static State decode(JsonNode saved, Frame current) {
        Objects.requireNonNull(current); if (saved == null || saved.isNull()) return initial(current);
        ObjectNode n = closed(saved, "schema", "actor_character_id", "episode_run_id", "consecutive_no_war_rounds", "cooldown_until_date_raw", "pending_query", "last_closed_query_sequence", "last_confirmed_war_id");
        equal(n.get("schema"), SCHEMA); BigInteger actor = integer(n.get("actor_character_id")); positiveValue(actor); String episode = nonempty(n.get("episode_run_id"));
        int rounds = nonnegative(n.get("consecutive_no_war_rounds")); require(rounds <= 2, "cooldown streak outside 0..2");
        Optional<BigInteger> until = nullable(n.get("cooldown_until_date_raw"), ArmyJson::integer);
        Optional<Pending> pending = nullable(n.get("pending_query"), value -> {
            ObjectNode p = closed(value, "query_sequence", "source_snapshot_id", "source_native_revision", "source_date_raw", "source_bridge_pid");
            return new Pending(positive(p.get("query_sequence")), nullable(p.get("source_snapshot_id"), ArmyJson::nonempty),
                    integer(p.get("source_native_revision")), integer(p.get("source_date_raw")), integer(p.get("source_bridge_pid")));
        });
        Optional<UInt64> closed = nullable(n.get("last_closed_query_sequence"), ArmyJson::positive);
        Optional<WarId> war = nullable(n.get("last_confirmed_war_id"), DeclarationOpportunityCooldown::warId);
        if (!actor.equals(current.actorCharacterId()) || !episode.equals(current.episodeRunId())) return initial(current);
        return new State(actor, episode, until.isPresent() ? 2 : rounds, until, pending, closed, war);
    }
    private static State owned(State state, Frame frame) {
        Objects.requireNonNull(state); Objects.requireNonNull(frame);
        if (!state.actorCharacterId().equals(frame.actorCharacterId()) || !state.episodeRunId().equals(frame.episodeRunId())) return initial(frame);
        return state.cooldownUntilDateRaw().isPresent() && state.consecutiveNoWarRounds() != 2
                ? replace(state, 2, state.cooldownUntilDateRaw(), state.pendingQuery(), state.lastClosedQuerySequence(), state.lastConfirmedWarId()) : state;
    }
    public static Reduction view(State original, Snapshot observed, Frame current) {
        Objects.requireNonNull(observed); State state = owned(original, current);
        if (state.pendingQuery().isPresent() && !state.pendingQuery().orElseThrow().sourceBridgePid().equals(current.bridgePid()))
            state = replace(state, state.consecutiveNoWarRounds(), state.cooldownUntilDateRaw(), Optional.empty(), state.lastClosedQuerySequence(), state.lastConfirmedWarId());
        Optional<WarId> verified = verifiedWar(observed);
        if (verified.isPresent() && !verified.equals(state.lastConfirmedWarId()))
            state = replace(state, 0, Optional.empty(), Optional.empty(), state.lastClosedQuerySequence(), verified);
        else if (observed.activeWars().isPresent() && !observed.activeWars().orElseThrow().isEmpty() && state.pendingQuery().isPresent())
            state = replace(state, state.consecutiveNoWarRounds(), state.cooldownUntilDateRaw(), Optional.empty(), state.lastClosedQuerySequence(), state.lastConfirmedWarId());
        boolean active = state.cooldownUntilDateRaw().filter(until -> current.dateRaw().compareTo(until) < 0).isPresent();
        BigInteger days = active ? state.cooldownUntilDateRaw().orElseThrow().subtract(current.dateRaw()).add(BigInteger.valueOf(23)).divide(BigInteger.valueOf(24)) : BigInteger.ZERO;
        return new Reduction(state, new View(active, state.consecutiveNoWarRounds(), state.cooldownUntilDateRaw(), days,
                state.pendingQuery().map(Pending::querySequence), state.actorCharacterId(), state.episodeRunId()));
    }
    /** Called solely after the actual successful strict declaration query; Unknown/pending collection is never a Completed input. */
    public static Reduction completed(State original, Frame source, UInt64 actualCompletedQuerySequence) {
        Objects.requireNonNull(actualCompletedQuerySequence); positiveValue(actualCompletedQuerySequence.value()); State state = owned(original, source);
        if (!state.lastClosedQuerySequence().equals(Optional.of(actualCompletedQuerySequence))
                && !state.pendingQuery().map(Pending::querySequence).equals(Optional.of(actualCompletedQuerySequence)))
            state = replace(state, state.consecutiveNoWarRounds(), state.cooldownUntilDateRaw(),
                    Optional.of(new Pending(actualCompletedQuerySequence, source.snapshotId(), source.nativeRevision(), source.dateRaw(), source.bridgePid())),
                    state.lastClosedQuerySequence(), state.lastConfirmedWarId());
        return view(state, Snapshot.empty(), source);
    }
    /** Runtime invokes this once from its actual afterExecution path, using verified life-advance and real post-state. Observation alone cannot close a round. */
    public static Reduction afterTurn(State original, Frame source, Outcome outcome, Snapshot post, Frame after) {
        Objects.requireNonNull(outcome); Objects.requireNonNull(post); State state = owned(original, source);
        require(source.actorCharacterId().equals(after.actorCharacterId()) && source.episodeRunId().equals(after.episodeRunId()), "cooldown post frame changed actor or episode");
        Optional<WarId> war = verifiedWar(post);
        if (war.isPresent() && !war.equals(state.lastConfirmedWarId()))
            return view(replace(state, 0, Optional.empty(), Optional.empty(), state.lastClosedQuerySequence(), war), post, after);
        Optional<Pending> pending = state.pendingQuery(); Optional<TurnResult> result = outcome.result();
        boolean unresolved = post.continuity().filter(value -> value.status().isEmpty() || !List.of("war_started", "native_rejected", "not_submitted").contains(value.status().orElseThrow())).isPresent();
        boolean ready = pending.isPresent() && outcome.executed() && outcome.selectedStep().equals(Optional.of("life-advance")) && result.isPresent();
        if (ready) {
            Pending query = pending.orElseThrow(); TurnResult turn = result.orElseThrow();
            ready = turn.step().equals("life-advance") && turn.progressStatus().equals("postcondition") && turn.paused()
                    && turn.startingDateRaw().equals(Optional.of(source.dateRaw())) && turn.endingDateRaw().equals(Optional.of(after.dateRaw()))
                    && after.dateRaw().compareTo(source.dateRaw()) > 0 && post.paused() && post.activeWars().isPresent() && post.activeWars().orElseThrow().isEmpty()
                    && !post.activeEvent() && !post.pendingInteraction() && !unresolved && source.dateRaw().compareTo(query.sourceDateRaw()) >= 0
                    && source.bridgePid().equals(query.sourceBridgePid()) && after.bridgePid().equals(query.sourceBridgePid())
                    && after.nativeRevision().compareTo(query.sourceNativeRevision()) > 0;
        }
        if (!ready) return view(state, post, after);
        int rounds = Math.min(2, state.consecutiveNoWarRounds() + 1); UInt64 sequence = pending.orElseThrow().querySequence();
        Optional<BigInteger> until = rounds == 2 ? Optional.of(after.dateRaw().add(COOLDOWN_RAW_DAYS)) : state.cooldownUntilDateRaw();
        return view(replace(state, rounds, until, Optional.empty(), Optional.of(sequence), state.lastConfirmedWarId()), post, after);
    }
    private static Optional<WarId> verifiedWar(Snapshot snapshot) {
        if (snapshot.continuity().isEmpty() || snapshot.activeWars().isEmpty()) return Optional.empty(); Continuity c = snapshot.continuity().orElseThrow();
        if (!c.schemaMatches() || !c.status().equals(Optional.of("war_started")) || !c.nativeAccepted() || !c.postconditionVerified() || c.warId().isEmpty()) return Optional.empty();
        WarId id = c.warId().orElseThrow(); if (id instanceof NumericWarId number && number.value().signum() == 0) return Optional.empty();
        return snapshot.activeWars().orElseThrow().stream().anyMatch(war -> war.playerAttacker() && war.id().equals(id)) ? Optional.of(id) : Optional.empty();
    }
    public static ObjectNode encode(State state) {
        ObjectNode n = empty().put("schema", SCHEMA).put("actor_character_id", state.actorCharacterId()).put("episode_run_id", state.episodeRunId()).put("consecutive_no_war_rounds", state.consecutiveNoWarRounds());
        put(n, "cooldown_until_date_raw", state.cooldownUntilDateRaw());
        if (state.pendingQuery().isEmpty()) n.putNull("pending_query"); else {
            Pending p = state.pendingQuery().orElseThrow(); ObjectNode row = empty().put("query_sequence", p.querySequence().value()).put("source_native_revision", p.sourceNativeRevision())
                    .put("source_date_raw", p.sourceDateRaw()).put("source_bridge_pid", p.sourceBridgePid());
            if (p.sourceSnapshotId().isPresent()) row.put("source_snapshot_id", p.sourceSnapshotId().orElseThrow()); else row.putNull("source_snapshot_id"); n.set("pending_query", row);
        }
        put(n, "last_closed_query_sequence", state.lastClosedQuerySequence().map(UInt64::value));
        if (state.lastConfirmedWarId().isEmpty()) n.putNull("last_confirmed_war_id"); else n.set("last_confirmed_war_id", warNode(state.lastConfirmedWarId().orElseThrow())); return n;
    }
    public static ObjectNode encodeView(View view) {
        ObjectNode n = empty().put("schema", SCHEMA).put("status", view.active() ? "active" : "inactive").put("consecutive_no_war_rounds", view.consecutiveNoWarRounds())
                .put("remaining_days", view.remainingDays()).put("actor_character_id", view.actorCharacterId()).put("episode_run_id", view.episodeRunId());
        put(n, "cooldown_until_date_raw", view.cooldownUntilDateRaw()); put(n, "pending_query_sequence", view.pendingQuerySequence().map(UInt64::value)); return n;
    }
    /** Same strict view decoder for ordinary declaration selection and archived current-frame consumers. Source qualification stays with its actual producer. */
    public static View decodeView(JsonNode raw, Frame current) {
        ObjectNode n = closed(raw, "schema", "status", "consecutive_no_war_rounds", "cooldown_until_date_raw", "remaining_days", "pending_query_sequence", "actor_character_id", "episode_run_id");
        equal(n.get("schema"), SCHEMA); equal(n.get("actor_character_id"), current.actorCharacterId()); equal(n.get("episode_run_id"), current.episodeRunId());
        int rounds = nonnegative(n.get("consecutive_no_war_rounds")); require(rounds <= 2, "cooldown view streak outside 0..2");
        Optional<BigInteger> until = nullable(n.get("cooldown_until_date_raw"), ArmyJson::integer); boolean active = until.filter(date -> current.dateRaw().compareTo(date) < 0).isPresent();
        equal(n.get("status"), active ? "active" : "inactive");
        BigInteger remaining = active ? until.orElseThrow().subtract(current.dateRaw()).add(BigInteger.valueOf(23)).divide(BigInteger.valueOf(24)) : BigInteger.ZERO;
        equal(n.get("remaining_days"), remaining); Optional<UInt64> pending = nullable(n.get("pending_query_sequence"), ArmyJson::positive);
        require(until.isEmpty() || rounds == 2, "saved cooldown deadline must retain original threshold streak2");
        return new View(active, rounds, until, remaining, pending, current.actorCharacterId(), current.episodeRunId());
    }
    /** Narrow identity/status projection after the existing full Driver producers. It neither normalizes armies nor qualifies continuity. */
    public static Snapshot snapshot(JsonNode actual) {
        ObjectNode n = object(actual); Optional<List<War>> wars = Optional.empty(); JsonNode rawWars = n.get("active_wars");
        if (rawWars != null && rawWars.isArray()) {
            List<War> rows = new ArrayList<>(); for (JsonNode row : rawWars) if (row.isObject() && row.has("war_id") && !row.get("war_id").isNull())
                rows.add(new War(warId(row.get("war_id")), isText(row.get("player_side"), "attacker"))); wars = Optional.of(List.copyOf(rows));
        }
        Optional<Continuity> continuity = Optional.empty(); JsonNode raw = n.get("war_declaration_continuity_v1");
        if (raw != null && raw.isObject()) {
            Optional<WarId> id = raw.has("war_id") && !raw.get("war_id").isNull() ? Optional.of(warId(raw.get("war_id"))) : Optional.empty();
            continuity = Optional.of(new Continuity(isText(raw.get("schema"), "war-declaration-continuity-v1"), optionalText(raw.get("status")), isText(raw.get("native_response"), "accepted"), isTrue(raw.get("postcondition_verified")), id));
        }
        return new Snapshot(isTrue(n.get("paused")), wars, n.path("active_event").isObject(), n.path("pending_character_interaction").isObject(), continuity);
    }
    public static Outcome outcome(JsonNode actual) {
        ObjectNode n = object(actual); Optional<TurnResult> result = Optional.empty(); JsonNode raw = n.get("result");
        if (raw != null && raw.isObject()) result = Optional.of(new TurnResult(optionalText(raw.get("step")).orElse(""), optionalText(raw.get("progress_status")).orElse(""),
                isTrue(raw.get("paused")), optionalInteger(raw.get("starting_date_raw")), optionalInteger(raw.get("ending_date_raw"))));
        return new Outcome(isText(n.get("status"), "executed"), optionalText(n.get("selected_step")), result);
    }
    private static State replace(State s, int rounds, Optional<BigInteger> until, Optional<Pending> pending, Optional<UInt64> closed, Optional<WarId> war) {
        return new State(s.actorCharacterId(), s.episodeRunId(), rounds, until, pending, closed, war);
    }
    private static Optional<String> optionalText(JsonNode n) { return n != null && n.isTextual() ? Optional.of(n.textValue()) : Optional.empty(); }
    private static Optional<BigInteger> optionalInteger(JsonNode n) { return n == null || n.isNull() ? Optional.empty() : Optional.of(integer(n)); }
    private static boolean isText(JsonNode n, String value) { return n != null && n.isTextual() && n.textValue().equals(value); }
    private static boolean isTrue(JsonNode n) { return n != null && n.isBoolean() && n.booleanValue(); }
    private static WarId warId(JsonNode n) { return n.isTextual() ? new TextWarId(nonempty(n)) : new NumericWarId(integer(n)); }
    private static JsonNode warNode(WarId id) { return id instanceof NumericWarId n ? empty().numberNode(n.value()) : empty().textNode(((TextWarId) id).value()); }
    private static void put(ObjectNode n, String key, Optional<BigInteger> value) { if (value.isPresent()) n.put(key, value.orElseThrow()); else n.putNull(key); }
    private static <T> Optional<T> nullable(JsonNode n, java.util.function.Function<JsonNode,T> decoder) { require(n != null, "required cooldown slot absent"); return n.isNull() ? Optional.empty() : Optional.of(decoder.apply(n)); }
    private static void positiveValue(BigInteger n) { require(n != null && n.signum() > 0, "positive bound cooldown identity/date/revision required"); }
    private static void nonemptyValue(String n) { require(n != null && !n.isEmpty(), "nonempty cooldown owner/snapshot identity required"); }
}
