package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.math.BigInteger;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Native CREATE dispatch DATA. No callback return establishes Rite/world/SAVE success. */
public record CurrentRiteCreateResult(CurrentRiteCreate.Action action, Status status, boolean effectAttempted,
        boolean nativeReturned, boolean cleanupKnown, BigInteger providerGeneration, BigInteger querySequence,
        BigInteger claimSequence, Optional<CoreFrame.Prefix> factsBefore, Optional<CurrentLetterResult.OwnerWitness> owner,
        Optional<CurrentRiteCreateSource> source, Optional<String> unavailableReason) {
    public enum Status {
        UNAVAILABLE("unavailable"), AVAILABLE("available"), EXPIRED("expired"), STALE_SOURCE("stale_source"),
        CLAIM_CONSUMED("claim_consumed"), PREREQUISITE_REJECTED("prerequisite_rejected"),
        CONFIRMATION_PENDING("confirmation_pending"), CREATE_DISPATCHED("create_dispatched"),
        CONFIRMATION_DISPATCHED("confirmation_dispatched"), INDETERMINATE("indeterminate");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static Status parse(String text) throws IOException {
            for (var value : values()) if (value.wire.equals(text)) return value;
            throw new IOException("Unknown current Rite CREATE status");
        }
    }

    public CurrentRiteCreateResult {
        Objects.requireNonNull(action); Objects.requireNonNull(status);
        CurrentRiteCreate.unsigned(providerGeneration, false); CurrentRiteCreate.unsigned(querySequence, false);
        CurrentRiteCreate.unsigned(claimSequence, false);
        Objects.requireNonNull(factsBefore); Objects.requireNonNull(owner); Objects.requireNonNull(source); Objects.requireNonNull(unavailableReason);
        StrictJson.require(factsBefore.isPresent() == owner.isPresent(), "Actual CREATE Core/owner nullable roles differ");
        factsBefore.ifPresent(CurrentLetter::requirePrefix);
        StrictJson.require(!nativeReturned || effectAttempted, "Native return cannot precede actual effect entry");
        if (action.queryOnly()) StrictJson.require(!effectAttempted && !nativeReturned && claimSequence.signum() == 0,
                "CREATE-family queries cannot consume effects or claims");
        if (source.isPresent()) {
            StrictJson.require(factsBefore.isPresent() && cleanupKnown && providerGeneration.signum() > 0 && querySequence.signum() > 0,
                    "Complete CREATE beforeSource requires actual Core/owner/query identity");
            var s = source.orElseThrow();
            StrictJson.require(s.actorId() == factsBefore.orElseThrow().playedCharacterId(), "CREATE source actor differs from actual Core");
            StrictJson.require((action == CurrentRiteCreate.Action.QUERY || action == CurrentRiteCreate.Action.CREATE)
                    ? s.phase() == CurrentRiteCreateSource.Phase.DRAFT : s.phase() == CurrentRiteCreateSource.Phase.CONFIRMATION,
                    "CREATE action/source phase differs");
        }
        if (status == Status.AVAILABLE) {
            StrictJson.require(action.queryOnly() && cleanupKnown && source.isPresent() && unavailableReason.isEmpty(),
                    "Available CREATE-family query coherence differs");
        } else if (status == Status.CREATE_DISPATCHED || status == Status.CONFIRMATION_DISPATCHED) {
            boolean create = status == Status.CREATE_DISPATCHED;
            StrictJson.require(action == (create ? CurrentRiteCreate.Action.CREATE : CurrentRiteCreate.Action.ACCEPT_CONFIRMATION)
                    && cleanupKnown && source.isPresent() && claimSequence.signum() > 0 && effectAttempted && nativeReturned
                    && unavailableReason.isEmpty(), "Void CREATE dispatch coherence differs");
            var s = source.orElseThrow();
            StrictJson.require(create ? s.draft().orElseThrow().createAdmissible() : s.confirmation().orElseThrow().acceptAdmissible(),
                    "Void CREATE dispatch lacks original admitted beforeSource");
        } else {
            StrictJson.require(unavailableReason.filter(reason -> !reason.isEmpty()).isPresent(), "Original CREATE refusal reason required");
            if (status != Status.INDETERMINATE) StrictJson.require(!effectAttempted && !nativeReturned,
                    "Known CREATE refusal must retain zero effect/return flags even when a claim was spent");
        }
        if (status == Status.CONFIRMATION_PENDING) StrictJson.require(action == CurrentRiteCreate.Action.QUERY_CONFIRMATION
                && source.isEmpty() && cleanupKnown, "Pending confirmation is only a clean original-Create poll, never an available Source");
        if (status == Status.INDETERMINATE) StrictJson.require(source.isEmpty(), "Indeterminate CREATE retains SourceNull/sticky UNKNOWN");
        if (!cleanupKnown) StrictJson.require(status == Status.INDETERMINATE, "Unknown CREATE cleanup must remain indeterminate");
    }
    public boolean successful() {
        return status == Status.AVAILABLE || status == Status.CREATE_DISPATCHED || status == Status.CONFIRMATION_DISPATCHED;
    }
    public boolean sourceAvailable() { return source.isPresent(); }
    public boolean nativeHandled() { return false; }
    public boolean riteCreated() { return false; }
    public boolean initialBindingConfirmed() { return false; }
    public boolean newDateObserved() { return false; }
    public boolean physicalSaveConfirmed() { return false; }

    public static CurrentRiteCreateResult decode(RawJson raw) throws IOException {
        try {
            var r = StrictJson.object(NativeWire.parse(raw.bytes()), Set.of("schema", "game_version", "executable_sha256",
                    "adapter_id", "backend", "action", "status", "source_available", "provider_generation", "query_sequence",
                    "claim_sequence", "effect_attempted", "native_returned", "native_handled", "cleanup_known", "facts_before",
                    "owner", "source", "addresses_redacted", "rite_created", "initial_binding_confirmed", "new_date_observed",
                    "physical_save_confirmed", "unavailable_reason"));
            var b = ExactCk3Build.CK3_121003_STEAM_26785313;
            CurrentRiteCreate.identity(r, "schema", CurrentRiteCreate.RESULT_SCHEMA);
            CurrentRiteCreate.identity(r, "game_version", b.version());
            CurrentRiteCreate.identity(r, "executable_sha256", b.executableSha256().toUpperCase(Locale.ROOT));
            CurrentRiteCreate.identity(r, "adapter_id", b.coreFrameAdapterId()); CurrentRiteCreate.identity(r, "backend", CurrentRiteCreate.BACKEND);
            if (!CurrentRiteCreate.bool(r, "addresses_redacted")) throw new IOException("CREATE addresses must be redacted");
            for (String key : Set.of("native_handled", "rite_created", "initial_binding_confirmed", "new_date_observed", "physical_save_confirmed"))
                if (CurrentRiteCreate.bool(r, key)) throw new IOException("CREATE DATA cannot claim: " + key);
            Optional<CoreFrame.Prefix> facts = Optional.empty(); Optional<CurrentLetterResult.OwnerWitness> owner = Optional.empty();
            Optional<CurrentRiteCreateSource> source = Optional.empty();
            if (!r.get("facts_before").isNull()) {
                var p = StrictJson.object(r.get("facts_before"), Set.of("date_raw", "speed", "paused", "local_player_id", "map_ready",
                        "has_played_character", "played_character_id", "played_character_alive"));
                facts = Optional.of(new CoreFrame.Prefix(CurrentRiteCreate.i32(p.get("date_raw")), CurrentRiteCreate.i32(p.get("speed")),
                        CurrentRiteCreate.bool(p, "paused"), CurrentRiteCreate.i32(p.get("local_player_id")), CurrentRiteCreate.bool(p, "map_ready"),
                        CurrentRiteCreate.bool(p, "has_played_character"), CurrentRiteCreate.i32(p.get("played_character_id")), CurrentRiteCreate.bool(p, "played_character_alive")));
            }
            if (!r.get("owner").isNull()) {
                var w = StrictJson.object(r.get("owner"), Set.of("connection_generation", "ticket_sequence", "pump_epoch", "thread_id"));
                owner = Optional.of(new CurrentLetterResult.OwnerWitness(CurrentRiteCreate.decimal(w, "connection_generation"),
                        CurrentRiteCreate.decimal(w, "ticket_sequence"), CurrentRiteCreate.decimal(w, "pump_epoch"),
                        NativeWire.integer(w.get("thread_id"), BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact()));
            }
            if (!r.get("source").isNull()) source = Optional.of(CurrentRiteCreateSource.decode(r.get("source")));
            if (CurrentRiteCreate.bool(r, "source_available") != source.isPresent()) throw new IOException("CREATE source availability/null mismatch");
            return new CurrentRiteCreateResult(CurrentRiteCreate.Action.parse(NativeWire.text(r.get("action"))),
                    Status.parse(NativeWire.text(r.get("status"))), CurrentRiteCreate.bool(r, "effect_attempted"), CurrentRiteCreate.bool(r, "native_returned"),
                    CurrentRiteCreate.bool(r, "cleanup_known"), CurrentRiteCreate.decimal(r, "provider_generation"),
                    CurrentRiteCreate.decimal(r, "query_sequence"), CurrentRiteCreate.decimal(r, "claim_sequence"), facts, owner, source,
                    r.get("unavailable_reason").isNull() ? Optional.empty() : Optional.of(NativeWire.text(r.get("unavailable_reason"))));
        } catch (IllegalArgumentException | ArithmeticException invalid) {
            throw new IOException("Invalid exact current Rite CREATE DATA", invalid);
        }
    }

    public static CurrentRiteCreateResult decodeOutcome(AckReceived original) throws IOException {
        Objects.requireNonNull(original);
        try {
            var e = StrictJson.object(NativeWire.parse(original.originalFrame().bytes()), Set.of("type", "protocol_version", "request_id", "ok", "result"));
            CurrentRiteCreate.identity(e, "type", "command_result"); CurrentRiteCreate.identity(e, "request_id", original.requestId());
            NativeWire.integer(e.get("protocol_version"), BigInteger.ONE, BigInteger.ONE);
            if (CurrentRiteCreate.bool(e, "ok") != original.nativeOk()) throw new IOException("Original CREATE envelope ok mismatch");
            var token = original.originalResultToken().orElseThrow(() -> new IOException("Original CREATE result token absent"));
            if (!NativeWire.parse(token.bytes()).equals(e.get("result"))) throw new IOException("CREATE token differs from actual original envelope");
            var result = decode(new RawJson(token.bytes()));
            if (result.successful() != original.nativeOk()) throw new IOException("Native ok differs from coherent CREATE query/void-dispatch result");
            return result;
        } catch (IllegalArgumentException invalid) { throw new IOException("Invalid actual Rite CREATE acknowledgement", invalid); }
    }

    public RawJson encode() {
        var b = ExactCk3Build.CK3_121003_STEAM_26785313;
        var r = StrictJson.object().put("schema", CurrentRiteCreate.RESULT_SCHEMA).put("game_version", b.version())
                .put("executable_sha256", b.executableSha256().toUpperCase(Locale.ROOT)).put("adapter_id", b.coreFrameAdapterId())
                .put("backend", CurrentRiteCreate.BACKEND).put("action", action.wire()).put("status", status.wire())
                .put("source_available", source.isPresent()).put("provider_generation", providerGeneration.toString())
                .put("query_sequence", querySequence.toString()).put("claim_sequence", claimSequence.toString())
                .put("effect_attempted", effectAttempted).put("native_returned", nativeReturned).put("native_handled", false).put("cleanup_known", cleanupKnown);
        if (factsBefore.isPresent()) {
            var p = factsBefore.orElseThrow();
            r.putObject("facts_before").put("date_raw", p.dateRaw()).put("speed", p.speed()).put("paused", p.paused())
                    .put("local_player_id", p.localPlayerId()).put("map_ready", p.mapReady()).put("has_played_character", p.hasPlayedCharacter())
                    .put("played_character_id", p.playedCharacterId()).put("played_character_alive", p.playedCharacterAlive());
            var w = owner.orElseThrow(); r.putObject("owner").put("connection_generation", w.connectionGeneration().toString())
                    .put("ticket_sequence", w.ticketSequence().toString()).put("pump_epoch", w.pumpEpoch().toString()).put("thread_id", w.threadId());
        } else { r.putNull("facts_before"); r.putNull("owner"); }
        if (source.isPresent()) r.set("source", source.orElseThrow().encode()); else r.putNull("source");
        r.put("addresses_redacted", true).put("rite_created", false).put("initial_binding_confirmed", false)
                .put("new_date_observed", false).put("physical_save_confirmed", false);
        if (unavailableReason.isPresent()) r.put("unavailable_reason", unavailableReason.orElseThrow()); else r.putNull("unavailable_reason");
        return new RawJson(StrictJson.canonical(r));
    }
}
