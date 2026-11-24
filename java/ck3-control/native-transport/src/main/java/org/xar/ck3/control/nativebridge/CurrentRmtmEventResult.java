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

/** Fixed void-selection result DATA. Dispatch does not establish event closure or game effects. */
public record CurrentRmtmEventResult(CurrentRmtmEvent.Action action, Status status,
        boolean effectAttempted, boolean nativeReturned, boolean cleanupKnown, BigInteger providerGeneration,
        BigInteger querySequence, BigInteger claimSequence, Optional<CoreFrame.Prefix> factsBefore,
        Optional<CurrentLetterResult.OwnerWitness> owner, Optional<CurrentRmtmEventSource> source,
        Optional<String> unavailableReason, Optional<Integer> instanceId) {
    public enum Status {
        UNAVAILABLE("unavailable"), EXPIRED("expired"), STALE_SOURCE("stale_source"), CLAIM_CONSUMED("claim_consumed"),
        AVAILABLE("available"), SELECTION_DISPATCHED("selection_dispatched"), INDETERMINATE("indeterminate");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static Status parse(String text) throws IOException {
            for (var value : values()) if (value.wire.equals(text)) return value;
            throw new IOException("Unknown RMTM event status");
        }
    }
    public CurrentRmtmEventResult {
        Objects.requireNonNull(action); Objects.requireNonNull(status); Objects.requireNonNull(factsBefore);
        Objects.requireNonNull(owner); Objects.requireNonNull(source); Objects.requireNonNull(unavailableReason); Objects.requireNonNull(instanceId);
        CurrentLetter.unsigned(providerGeneration, false); CurrentLetter.unsigned(querySequence, false); CurrentLetter.unsigned(claimSequence, false);
        StrictJson.require(factsBefore.isPresent() == owner.isPresent(), "RMTM event actual Core/owner nullable roles differ");
        factsBefore.ifPresent(CurrentRmtmActorTransition::requireCore);
        instanceId.ifPresent(n -> StrictJson.require(n > 0, "Actual positive event instance required"));
        StrictJson.require(!nativeReturned || effectAttempted, "Native return cannot precede effect entry");
        StrictJson.require(!effectAttempted || claimSequence.signum() > 0, "Effect entry requires the original spent claim");
        if (action.queryOnly()) StrictJson.require(instanceId.isEmpty() && claimSequence.signum() == 0 && !effectAttempted && !nativeReturned,
                "Fixed bookmark query cannot carry selection or effect facts");
        if (source.isPresent()) {
            StrictJson.require(factsBefore.isPresent() && cleanupKnown, "Complete Source requires actual Core/owner and known cleanup");
            var s = source.orElseThrow();
            if (s.fixedInstanceId().isPresent()) StrictJson.require(s.eventCensus().events().get(0).recipientCharacterId()
                    == factsBefore.orElseThrow().playedCharacterId(), "Fixed original recipient differs from actual Core");
        }
        if (status == Status.AVAILABLE) {
            StrictJson.require(action.queryOnly() && source.isPresent() && cleanupKnown && providerGeneration.signum() > 0
                    && querySequence.signum() > 0 && unavailableReason.isEmpty(), "Available fixed query coherence differs");
        } else if (status == Status.SELECTION_DISPATCHED) {
            StrictJson.require(!action.queryOnly() && source.isPresent() && cleanupKnown
                    && providerGeneration.signum() > 0 && querySequence.signum() > 0 && claimSequence.signum() > 0
                    && effectAttempted && nativeReturned && instanceId.isPresent() && unavailableReason.isEmpty(), "Fixed void selection coherence differs");
            var s = source.orElseThrow();
            if (action == CurrentRmtmEvent.Action.CHOOSE_POST_SUCCESSION_FIRST_AVAILABLE) {
                StrictJson.require(CurrentRmtmEvent.postSuccessionChoice(s, factsBefore.orElseThrow().playedCharacterId(),
                        instanceId.orElseThrow()).isPresent(), "Post-succession selection must retain the actual deterministic beforeSource");
            } else {
                StrictJson.require(s.ackAdmissible()&&s.fixedInstanceId().equals(instanceId)&&s.eventCensus().events().get(0).definitionKey().equals(action.definition()), "Selection must retain the exact immutable admitted beforeSource");
            }
        } else {
            StrictJson.require(unavailableReason.filter(reason -> !reason.isEmpty()).isPresent(), "Original RMTM event refusal reason required");
            if (status != Status.INDETERMINATE) StrictJson.require(!effectAttempted && !nativeReturned,
                    "Known refusal must preserve zero effect facts; original Source may remain DATA");
        }
        if (status == Status.INDETERMINATE) StrictJson.require(source.isEmpty(), "UNKNOWN must retain SourceNull");
        if (!cleanupKnown) StrictJson.require(status == Status.INDETERMINATE, "Unknown cleanup must remain indeterminate");
    }
    public boolean successful() { return status == Status.AVAILABLE || status == Status.SELECTION_DISPATCHED; }
    public boolean sourceAvailable() { return source.isPresent(); }
    public boolean nativeHandled() { return false; }
    public boolean eventClosed() { return false; }
    public boolean newDateObserved() { return false; }
    public boolean physicalSaveConfirmed() { return false; }

    public static CurrentRmtmEventResult decode(RawJson raw) throws IOException {
        try {
            var r = StrictJson.object(NativeWire.parse(raw.bytes()), Set.of("schema", "game_version", "executable_sha256", "adapter_id", "backend",
                    "action", "status", "source_available", "provider_generation", "query_sequence", "claim_sequence", "effect_attempted",
                    "native_returned", "native_handled", "cleanup_known", "facts_before", "owner", "source", "instance_id", "addresses_redacted",
                    "event_closed", "new_date_observed", "physical_save_confirmed", "unavailable_reason"));
            var b = ExactCk3Build.CK3_121003_STEAM_26785313;
            CurrentRmtmEvent.identity(r, "schema", CurrentRmtmEvent.RESULT_SCHEMA);
            CurrentRmtmEvent.identity(r, "game_version", b.version());
            CurrentRmtmEvent.identity(r, "executable_sha256", b.executableSha256().toUpperCase(Locale.ROOT));
            CurrentRmtmEvent.identity(r, "adapter_id", b.coreFrameAdapterId()); CurrentRmtmEvent.identity(r, "backend", CurrentRmtmEvent.BACKEND);
            if (!CurrentRmtmEvent.bool(r, "addresses_redacted")) throw new IOException("RMTM event addresses must be redacted");
            for (String key : Set.of("native_handled", "event_closed", "new_date_observed", "physical_save_confirmed"))
                if (CurrentRmtmEvent.bool(r, key)) throw new IOException("Void fixed selection cannot claim: " + key);
            Optional<CoreFrame.Prefix> facts = Optional.empty(); Optional<CurrentLetterResult.OwnerWitness> owner = Optional.empty();
            if (!r.get("facts_before").isNull()) {
                var p = StrictJson.object(r.get("facts_before"), Set.of("date_raw", "speed", "paused", "local_player_id", "map_ready", "has_played_character", "played_character_id", "played_character_alive"));
                facts = Optional.of(new CoreFrame.Prefix(CurrentRmtmEvent.i32(p.get("date_raw")), CurrentRmtmEvent.i32(p.get("speed")),
                        CurrentRmtmEvent.bool(p, "paused"), CurrentRmtmEvent.i32(p.get("local_player_id")), CurrentRmtmEvent.bool(p, "map_ready"),
                        CurrentRmtmEvent.bool(p, "has_played_character"), CurrentRmtmEvent.i32(p.get("played_character_id")), CurrentRmtmEvent.bool(p, "played_character_alive")));
            }
            if (!r.get("owner").isNull()) {
                var w = StrictJson.object(r.get("owner"), Set.of("connection_generation", "ticket_sequence", "pump_epoch", "thread_id"));
                owner = Optional.of(new CurrentLetterResult.OwnerWitness(CurrentRmtmEvent.decimal(w, "connection_generation"),
                        CurrentRmtmEvent.decimal(w, "ticket_sequence"), CurrentRmtmEvent.decimal(w, "pump_epoch"),
                        NativeWire.integer(w.get("thread_id"), BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact()));
            }
            var source = r.get("source").isNull() ? Optional.<CurrentRmtmEventSource>empty() : Optional.of(CurrentRmtmEventSource.decode(r.get("source")));
            if (CurrentRmtmEvent.bool(r, "source_available") != source.isPresent()) throw new IOException("RMTM event Source availability/null mismatch");
            return new CurrentRmtmEventResult(CurrentRmtmEvent.Action.parse(NativeWire.text(r.get("action"))), Status.parse(NativeWire.text(r.get("status"))),
                    CurrentRmtmEvent.bool(r, "effect_attempted"), CurrentRmtmEvent.bool(r, "native_returned"), CurrentRmtmEvent.bool(r, "cleanup_known"),
                    CurrentRmtmEvent.decimal(r, "provider_generation"), CurrentRmtmEvent.decimal(r, "query_sequence"), CurrentRmtmEvent.decimal(r, "claim_sequence"),
                    facts, owner, source, r.get("unavailable_reason").isNull() ? Optional.empty() : Optional.of(NativeWire.text(r.get("unavailable_reason"))),
                    r.get("instance_id").isNull() ? Optional.empty() : Optional.of(CurrentRmtmEvent.i32(r.get("instance_id"))));
        } catch (IllegalArgumentException | ArithmeticException invalid) { throw new IOException("Invalid exact RMTM fixed event DATA", invalid); }
    }

    public static CurrentRmtmEventResult decodeOutcome(AckReceived original) throws IOException {
        Objects.requireNonNull(original);
        try {
            var e = StrictJson.object(NativeWire.parse(original.originalFrame().bytes()), Set.of("type", "protocol_version", "request_id", "ok", "result"));
            CurrentRmtmEvent.identity(e, "type", "command_result"); CurrentRmtmEvent.identity(e, "request_id", original.requestId());
            NativeWire.integer(e.get("protocol_version"), BigInteger.ONE, BigInteger.ONE);
            if (CurrentRmtmEvent.bool(e, "ok") != original.nativeOk()) throw new IOException("RMTM event original envelope ok mismatch");
            var token = original.originalResultToken().orElseThrow(() -> new IOException("Original bookmark result token absent"));
            if (!NativeWire.parse(token.bytes()).equals(e.get("result"))) throw new IOException("RMTM event token differs from original envelope");
            var result = decode(new RawJson(token.bytes()));
            if (result.successful() != original.nativeOk()) throw new IOException("Native ok differs from coherent fixed query/dispatch result");
            return result;
        } catch (IllegalArgumentException invalid) { throw new IOException("Invalid original bookmark acknowledgement", invalid); }
    }

    public RawJson encode() {
        var b = ExactCk3Build.CK3_121003_STEAM_26785313;
        var r = StrictJson.object().put("schema", CurrentRmtmEvent.RESULT_SCHEMA).put("game_version", b.version())
                .put("executable_sha256", b.executableSha256().toUpperCase(Locale.ROOT)).put("adapter_id", b.coreFrameAdapterId())
                .put("backend", CurrentRmtmEvent.BACKEND).put("action", action.wire()).put("status", status.wire())
                .put("source_available", source.isPresent()).put("provider_generation", providerGeneration.toString()).put("query_sequence", querySequence.toString())
                .put("claim_sequence", claimSequence.toString()).put("effect_attempted", effectAttempted).put("native_returned", nativeReturned)
                .put("native_handled", false).put("cleanup_known", cleanupKnown);
        if (factsBefore.isPresent()) {
            r.set("facts_before", CurrentRmtmEvent.core(factsBefore.orElseThrow()));
            var w = owner.orElseThrow(); r.putObject("owner").put("connection_generation", w.connectionGeneration().toString())
                    .put("ticket_sequence", w.ticketSequence().toString()).put("pump_epoch", w.pumpEpoch().toString()).put("thread_id", w.threadId());
        } else { r.putNull("facts_before"); r.putNull("owner"); }
        if (source.isPresent()) r.set("source", source.orElseThrow().encode()); else r.putNull("source");
        if (instanceId.isPresent()) r.put("instance_id", instanceId.orElseThrow()); else r.putNull("instance_id");
        r.put("addresses_redacted", true).put("event_closed", false).put("new_date_observed", false).put("physical_save_confirmed", false);
        if (unavailableReason.isPresent()) r.put("unavailable_reason", unavailableReason.orElseThrow()); else r.putNull("unavailable_reason");
        return new RawJson(StrictJson.canonical(r));
    }
}
