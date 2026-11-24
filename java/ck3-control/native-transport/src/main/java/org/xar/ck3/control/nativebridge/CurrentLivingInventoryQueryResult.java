package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.node.ObjectNode;
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

/** Readonly inventory DATA. Even AVAILABLE grants no ownership lease, selection, equipment or other action authority. */
public record CurrentLivingInventoryQueryResult(Status status, boolean cleanupKnown, BigInteger providerGeneration,
        BigInteger querySequence, Optional<CoreFrame.Prefix> factsBefore,
        Optional<CurrentLetterResult.OwnerWitness> owner, Optional<CurrentLivingInventoryQuerySource> source,
        Optional<String> unavailableReason) {
    public enum Status {
        UNAVAILABLE("unavailable"), EXPIRED("expired"), STALE_SOURCE("stale_source"),
        AVAILABLE("available"), INDETERMINATE("indeterminate");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static Status parse(String text) throws IOException {
            for (var value : values()) if (value.wire.equals(text)) return value;
            throw new IOException("Unknown Living inventory query status");
        }
    }

    public CurrentLivingInventoryQueryResult {
        Objects.requireNonNull(status);
        CurrentLivingInventoryQuery.unsigned(providerGeneration, false);
        CurrentLivingInventoryQuery.unsigned(querySequence, false);
        Objects.requireNonNull(factsBefore); Objects.requireNonNull(owner);
        Objects.requireNonNull(source); Objects.requireNonNull(unavailableReason);
        StrictJson.require(factsBefore.isPresent() == owner.isPresent(), "Actual Core/owner nullable roles differ");
        factsBefore.ifPresent(CurrentLivingInventoryQuery::requirePrefix);
        if (status == Status.AVAILABLE) {
            StrictJson.require(cleanupKnown && factsBefore.isPresent() && source.isPresent()
                    && providerGeneration.signum() > 0 && querySequence.signum() > 0 && unavailableReason.isEmpty(),
                    "Available readonly inventory coherence differs");
            StrictJson.require(source.orElseThrow().actorFullId() == Integer.toUnsignedLong(factsBefore.orElseThrow().playedCharacterId()),
                    "Inventory source differs from actual played actor");
        } else {
            StrictJson.require(source.isEmpty(), "Refused or unknown title must retain SourceNull");
            StrictJson.require(providerGeneration.signum() == 0 && querySequence.signum() == 0,
                    "Refused readonly query cannot retain an available-query identity");
            StrictJson.require(unavailableReason.filter(x -> !x.isEmpty()).isPresent(),
                    "Original title refusal reason required");
        }
        if (!cleanupKnown) StrictJson.require(status == Status.INDETERMINATE && source.isEmpty(),
                "Unknown cleanup must remain indeterminate without source");
    }

    public boolean successful() { return status == Status.AVAILABLE; }
    public boolean sourceAvailable() { return source.isPresent(); }
    public boolean effectAttempted() { return false; }
    public boolean nativeReturned() { return false; }
    public boolean nativeHandled() { return false; }
    public BigInteger claimSequence() { return BigInteger.ZERO; }
    public boolean newDateObserved() { return false; }
    public boolean physicalSaveConfirmed() { return false; }

    public static CurrentLivingInventoryQueryResult decode(RawJson raw) throws IOException {
        try {
            var result = StrictJson.object(NativeWire.parse(raw.bytes()), Set.of("schema", "game_version",
                    "executable_sha256", "adapter_id", "backend", "action", "status", "source_available",
                    "provider_generation", "query_sequence", "claim_sequence", "effect_attempted", "native_returned",
                    "native_handled", "cleanup_known", "facts_before", "owner", "source", "addresses_redacted",
                    "new_date_observed", "physical_save_confirmed",
                    "unavailable_reason"));
            var build = ExactCk3Build.CK3_121003_STEAM_26785313;
            CurrentLivingInventoryQuery.identity(result, "schema", CurrentLivingInventoryQuery.RESULT_SCHEMA);
            CurrentLivingInventoryQuery.identity(result, "game_version", build.version());
            CurrentLivingInventoryQuery.identity(result, "executable_sha256", build.executableSha256().toUpperCase(Locale.ROOT));
            CurrentLivingInventoryQuery.identity(result, "adapter_id", build.coreFrameAdapterId());
            CurrentLivingInventoryQuery.identity(result, "backend", CurrentLivingInventoryQuery.BACKEND);
            CurrentLivingInventoryQuery.identity(result, "action", CurrentLivingInventoryQuery.ACTION);
            if (!CurrentLivingInventoryQuery.bool(result, "addresses_redacted")) throw new IOException("Inventory addresses must be redacted");
            for (var key : Set.of("effect_attempted", "native_returned", "native_handled", "new_date_observed", "physical_save_confirmed"))
                if (CurrentLivingInventoryQuery.bool(result, key)) throw new IOException("Readonly title cannot claim: " + key);

            if (CurrentLivingInventoryQuery.decimal(result, "claim_sequence").signum() != 0)
                throw new IOException("Readonly Living inventory cannot consume a claim");
            Optional<CoreFrame.Prefix> facts = Optional.empty();
            Optional<CurrentLetterResult.OwnerWitness> owner = Optional.empty();
            Optional<CurrentLivingInventoryQuerySource> source = Optional.empty();
            if (!result.get("facts_before").isNull()) {
                var prefix = StrictJson.object(result.get("facts_before"), Set.of("date_raw", "speed", "paused",
                        "local_player_id", "map_ready", "has_played_character", "played_character_id", "played_character_alive"));
                facts = Optional.of(new CoreFrame.Prefix(CurrentLivingInventoryQuery.i32(prefix.get("date_raw")),
                        CurrentLivingInventoryQuery.i32(prefix.get("speed")), CurrentLivingInventoryQuery.bool(prefix, "paused"),
                        CurrentLivingInventoryQuery.i32(prefix.get("local_player_id")), CurrentLivingInventoryQuery.bool(prefix, "map_ready"),
                        CurrentLivingInventoryQuery.bool(prefix, "has_played_character"), CurrentLivingInventoryQuery.i32(prefix.get("played_character_id")),
                        CurrentLivingInventoryQuery.bool(prefix, "played_character_alive")));
            }
            if (!result.get("owner").isNull()) {
                var witness = StrictJson.object(result.get("owner"), Set.of("connection_generation", "ticket_sequence", "pump_epoch", "thread_id"));
                owner = Optional.of(new CurrentLetterResult.OwnerWitness(CurrentLivingInventoryQuery.decimal(witness, "connection_generation"),
                        CurrentLivingInventoryQuery.decimal(witness, "ticket_sequence"), CurrentLivingInventoryQuery.decimal(witness, "pump_epoch"),
                        NativeWire.integer(witness.get("thread_id"), BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact()));
            }
            if (!result.get("source").isNull()) source = Optional.of(CurrentLivingInventoryQuerySource.decode(result.get("source")));
            if (CurrentLivingInventoryQuery.bool(result, "source_available") != source.isPresent())
                throw new IOException("Inventory source availability/null mismatch");
            Optional<String> reason = result.get("unavailable_reason").isNull() ? Optional.empty()
                    : Optional.of(actualReason(result.get("unavailable_reason")));
            return new CurrentLivingInventoryQueryResult(Status.parse(NativeWire.text(result.get("status"))),
                    CurrentLivingInventoryQuery.bool(result, "cleanup_known"), CurrentLivingInventoryQuery.decimal(result, "provider_generation"),
                    CurrentLivingInventoryQuery.decimal(result, "query_sequence"),
                    facts, owner, source, reason);
        } catch (IllegalArgumentException | ArithmeticException invalid) {
            throw new IOException("Invalid exact current Living inventory query DATA", invalid);
        }
    }

    public static CurrentLivingInventoryQueryResult decodeOutcome(AckReceived original) throws IOException {
        Objects.requireNonNull(original);
        try {
            var envelope = StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),
                    Set.of("type", "protocol_version", "request_id", "ok", "result"));
            CurrentLivingInventoryQuery.identity(envelope, "type", "command_result");
            CurrentLivingInventoryQuery.identity(envelope, "request_id", original.requestId());
            NativeWire.integer(envelope.get("protocol_version"), BigInteger.ONE, BigInteger.ONE);
            if (CurrentLivingInventoryQuery.bool(envelope, "ok") != original.nativeOk()) throw new IOException("Original inventory envelope ok mismatch");
            var token = original.originalResultToken().orElseThrow(() -> new IOException("Original inventory result token absent"));
            if (!NativeWire.parse(token.bytes()).equals(envelope.get("result"))) throw new IOException("Inventory token differs from original envelope");
            var result = decode(new RawJson(token.bytes()));
            if (result.successful() != original.nativeOk()) throw new IOException("Native ok differs from coherent readonly inventory status");
            return result;
        } catch (IllegalArgumentException invalid) {
            throw new IOException("Invalid actual Living inventory query acknowledgement", invalid);
        }
    }

    private static String actualReason(com.fasterxml.jackson.databind.JsonNode value) throws IOException {
        if (!value.isTextual()) throw new IOException("Actual refusal reason must be a string, including empty");
        return value.textValue();
    }

    public RawJson encode() {
        var build = ExactCk3Build.CK3_121003_STEAM_26785313;
        var result = StrictJson.object().put("schema", CurrentLivingInventoryQuery.RESULT_SCHEMA).put("game_version", build.version())
                .put("executable_sha256", build.executableSha256().toUpperCase(Locale.ROOT)).put("adapter_id", build.coreFrameAdapterId())
                .put("backend", CurrentLivingInventoryQuery.BACKEND).put("action", CurrentLivingInventoryQuery.ACTION).put("status", status.wire())
                .put("source_available", source.isPresent()).put("provider_generation", providerGeneration.toString())
                .put("query_sequence", querySequence.toString()).put("claim_sequence", "0")
                .put("effect_attempted", false).put("native_returned", false).put("native_handled", false).put("cleanup_known", cleanupKnown);
        if (factsBefore.isPresent()) {
            result.set("facts_before", CurrentLivingInventoryQuery.prefix(factsBefore.orElseThrow()));
            var witness = owner.orElseThrow();
            result.putObject("owner").put("connection_generation", witness.connectionGeneration().toString())
                    .put("ticket_sequence", witness.ticketSequence().toString()).put("pump_epoch", witness.pumpEpoch().toString())
                    .put("thread_id", witness.threadId());
        } else { result.putNull("facts_before"); result.putNull("owner"); }
        if (source.isPresent()) result.set("source", source.orElseThrow().encode()); else result.putNull("source");
        result.put("addresses_redacted", true)
                .put("new_date_observed", false).put("physical_save_confirmed", false);
        if (unavailableReason.isPresent()) result.put("unavailable_reason", unavailableReason.orElseThrow());
        else result.putNull("unavailable_reason");
        return new RawJson(StrictJson.canonical(result));
    }
}
