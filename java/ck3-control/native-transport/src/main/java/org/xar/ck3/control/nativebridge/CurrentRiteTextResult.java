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

/** Native TEXT dispatch DATA. No callback return establishes text/date/SAVE success. */
public record CurrentRiteTextResult(CurrentRiteText.Action action, Status status, boolean effectAttempted,
        boolean nativeReturned, boolean cleanupKnown, BigInteger providerGeneration, BigInteger querySequence,
        BigInteger claimSequence, Optional<CoreFrame.Prefix> factsBefore, Optional<CurrentLetterResult.OwnerWitness> owner,
        Optional<CurrentRiteTextSource> source, Optional<String> unavailableReason) {
    public enum Status {
        UNAVAILABLE("unavailable"), AVAILABLE("available"), EXPIRED("expired"), STALE_SOURCE("stale_source"),
        CLAIM_CONSUMED("claim_consumed"), PREREQUISITE_REJECTED("prerequisite_rejected"),
        TEXT_DISPATCHED("text_dispatched"), INDETERMINATE("indeterminate");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static Status parse(String text) throws IOException {
            for (var value : values()) if (value.wire.equals(text)) return value;
            throw new IOException("Unknown current Rite TEXT status");
        }
    }

    public CurrentRiteTextResult {
        Objects.requireNonNull(action); Objects.requireNonNull(status);
        CurrentRiteText.unsigned(providerGeneration, false); CurrentRiteText.unsigned(querySequence, false);
        CurrentRiteText.unsigned(claimSequence, false);
        Objects.requireNonNull(factsBefore); Objects.requireNonNull(owner); Objects.requireNonNull(source); Objects.requireNonNull(unavailableReason);
        StrictJson.require(factsBefore.isPresent() == owner.isPresent(), "Actual TEXT Core/owner nullable roles differ");
        factsBefore.ifPresent(CurrentLetter::requirePrefix);
        StrictJson.require(!nativeReturned || effectAttempted, "Native return cannot precede actual effect entry");
        if (action.queryOnly()) StrictJson.require(!effectAttempted && !nativeReturned && claimSequence.signum() == 0,
                "TEXT-family queries cannot consume effects or claims");
        if (source.isPresent()) {
            StrictJson.require(factsBefore.isPresent() && cleanupKnown && providerGeneration.signum() > 0 && querySequence.signum() > 0,
                    "Complete TEXT beforeSource requires actual Core/owner/query identity");
            var s = source.orElseThrow();
            StrictJson.require(s.actorId() == factsBefore.orElseThrow().playedCharacterId(), "TEXT source actor differs from actual Core");
        }
        if (status == Status.AVAILABLE) {
            StrictJson.require(action.queryOnly() && cleanupKnown && source.isPresent() && unavailableReason.isEmpty(),
                    "Available TEXT-family query coherence differs");
        } else if (status == Status.TEXT_DISPATCHED) {
            StrictJson.require(!action.queryOnly() && cleanupKnown && source.isPresent()
                    && claimSequence.signum() > 0 && effectAttempted && nativeReturned && unavailableReason.isEmpty(),
                    "Void text dispatch coherence differs");
            StrictJson.require(source.orElseThrow().writeAdmissible(), "Text dispatch lacks immutable admitted beforeSource");
        } else {
            StrictJson.require(unavailableReason.filter(reason -> !reason.isEmpty()).isPresent(), "Original TEXT refusal reason required");
            StrictJson.require(source.isEmpty(), "Text refusal cannot expose an available Source");
            if (status != Status.INDETERMINATE) StrictJson.require(!effectAttempted && !nativeReturned,
                    "Known TEXT refusal must retain zero effect/return flags even when a claim was spent");
        }
        if (status == Status.INDETERMINATE) StrictJson.require(source.isEmpty(), "Indeterminate TEXT retains SourceNull/sticky UNKNOWN");
        if (!cleanupKnown) StrictJson.require(status == Status.INDETERMINATE, "Unknown TEXT cleanup must remain indeterminate");
    }
    public boolean successful() {
        return status == Status.AVAILABLE || status == Status.TEXT_DISPATCHED;
    }
    public boolean sourceAvailable() { return source.isPresent(); }
    public boolean nativeHandled() { return false; }
    public boolean textApplied() { return false; }
    public boolean newDateObserved() { return false; }
    public boolean physicalSaveConfirmed() { return false; }

    public static CurrentRiteTextResult decode(RawJson raw) throws IOException {
        try {
            var r = StrictJson.object(NativeWire.parse(raw.bytes()), Set.of("schema", "game_version", "executable_sha256",
                    "adapter_id", "backend", "action", "status", "source_available", "provider_generation", "query_sequence",
                    "claim_sequence", "effect_attempted", "native_returned", "native_handled", "cleanup_known", "facts_before",
                    "owner", "source", "addresses_redacted", "text_applied", "new_date_observed",
                    "physical_save_confirmed", "unavailable_reason"));
            var b = ExactCk3Build.CK3_121003_STEAM_26785313;
            CurrentRiteText.identity(r, "schema", CurrentRiteText.RESULT_SCHEMA);
            CurrentRiteText.identity(r, "game_version", b.version());
            CurrentRiteText.identity(r, "executable_sha256", b.executableSha256().toUpperCase(Locale.ROOT));
            CurrentRiteText.identity(r, "adapter_id", b.coreFrameAdapterId()); CurrentRiteText.identity(r, "backend", CurrentRiteText.BACKEND);
            if (!CurrentRiteText.bool(r, "addresses_redacted")) throw new IOException("TEXT addresses must be redacted");
            for (String key : Set.of("native_handled", "text_applied", "new_date_observed", "physical_save_confirmed"))
                if (CurrentRiteText.bool(r, key)) throw new IOException("TEXT DATA cannot claim: " + key);
            Optional<CoreFrame.Prefix> facts = Optional.empty(); Optional<CurrentLetterResult.OwnerWitness> owner = Optional.empty();
            Optional<CurrentRiteTextSource> source = Optional.empty();
            if (!r.get("facts_before").isNull()) {
                var p = StrictJson.object(r.get("facts_before"), Set.of("date_raw", "speed", "paused", "local_player_id", "map_ready",
                        "has_played_character", "played_character_id", "played_character_alive"));
                facts = Optional.of(new CoreFrame.Prefix(CurrentRiteText.i32(p.get("date_raw")), CurrentRiteText.i32(p.get("speed")),
                        CurrentRiteText.bool(p, "paused"), CurrentRiteText.i32(p.get("local_player_id")), CurrentRiteText.bool(p, "map_ready"),
                        CurrentRiteText.bool(p, "has_played_character"), CurrentRiteText.i32(p.get("played_character_id")), CurrentRiteText.bool(p, "played_character_alive")));
            }
            if (!r.get("owner").isNull()) {
                var w = StrictJson.object(r.get("owner"), Set.of("connection_generation", "ticket_sequence", "pump_epoch", "thread_id"));
                owner = Optional.of(new CurrentLetterResult.OwnerWitness(CurrentRiteText.decimal(w, "connection_generation"),
                        CurrentRiteText.decimal(w, "ticket_sequence"), CurrentRiteText.decimal(w, "pump_epoch"),
                        NativeWire.integer(w.get("thread_id"), BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact()));
            }
            if (!r.get("source").isNull()) source = Optional.of(CurrentRiteTextSource.decode(r.get("source")));
            if (CurrentRiteText.bool(r, "source_available") != source.isPresent()) throw new IOException("TEXT source availability/null mismatch");
            return new CurrentRiteTextResult(CurrentRiteText.Action.parse(NativeWire.text(r.get("action"))),
                    Status.parse(NativeWire.text(r.get("status"))), CurrentRiteText.bool(r, "effect_attempted"), CurrentRiteText.bool(r, "native_returned"),
                    CurrentRiteText.bool(r, "cleanup_known"), CurrentRiteText.decimal(r, "provider_generation"),
                    CurrentRiteText.decimal(r, "query_sequence"), CurrentRiteText.decimal(r, "claim_sequence"), facts, owner, source,
                    r.get("unavailable_reason").isNull() ? Optional.empty() : Optional.of(NativeWire.text(r.get("unavailable_reason"))));
        } catch (IllegalArgumentException | ArithmeticException invalid) {
            throw new IOException("Invalid exact current Rite TEXT DATA", invalid);
        }
    }

    public static CurrentRiteTextResult decodeOutcome(AckReceived original) throws IOException {
        Objects.requireNonNull(original);
        try {
            var e = StrictJson.object(NativeWire.parse(original.originalFrame().bytes()), Set.of("type", "protocol_version", "request_id", "ok", "result"));
            CurrentRiteText.identity(e, "type", "command_result"); CurrentRiteText.identity(e, "request_id", original.requestId());
            NativeWire.integer(e.get("protocol_version"), BigInteger.ONE, BigInteger.ONE);
            if (CurrentRiteText.bool(e, "ok") != original.nativeOk()) throw new IOException("Original TEXT envelope ok mismatch");
            var token = original.originalResultToken().orElseThrow(() -> new IOException("Original TEXT result token absent"));
            if (!NativeWire.parse(token.bytes()).equals(e.get("result"))) throw new IOException("TEXT token differs from actual original envelope");
            var result = decode(new RawJson(token.bytes()));
            if (result.successful() != original.nativeOk()) throw new IOException("Native ok differs from coherent TEXT query/void-dispatch result");
            return result;
        } catch (IllegalArgumentException invalid) { throw new IOException("Invalid actual Rite TEXT acknowledgement", invalid); }
    }

    public RawJson encode() {
        var b = ExactCk3Build.CK3_121003_STEAM_26785313;
        var r = StrictJson.object().put("schema", CurrentRiteText.RESULT_SCHEMA).put("game_version", b.version())
                .put("executable_sha256", b.executableSha256().toUpperCase(Locale.ROOT)).put("adapter_id", b.coreFrameAdapterId())
                .put("backend", CurrentRiteText.BACKEND).put("action", action.wire()).put("status", status.wire())
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
        r.put("addresses_redacted", true).put("text_applied", false)
                .put("new_date_observed", false).put("physical_save_confirmed", false);
        if (unavailableReason.isPresent()) r.put("unavailable_reason", unavailableReason.orElseThrow()); else r.putNull("unavailable_reason");
        return new RawJson(StrictJson.canonical(r));
    }
}
