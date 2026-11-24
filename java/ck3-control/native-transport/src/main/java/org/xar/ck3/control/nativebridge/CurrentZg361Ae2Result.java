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

/** Actual AE2 dispatch/diagnostic DATA. No payment, verifier result, event absence or Save is inferred. */
public record CurrentZg361Ae2Result(CurrentZg361Ae2.Action action, Status status, boolean effectAttempted,
        boolean nativeReturned, boolean cleanupKnown, BigInteger providerGeneration, BigInteger querySequence,
        BigInteger claimSequence, Optional<CoreFrame.Prefix> factsBefore, Optional<CurrentLetterResult.OwnerWitness> owner,
        Optional<CurrentZg361Ae2Source> source, Optional<String> unavailableReason) {
    public enum Status {
        UNAVAILABLE("unavailable"), EXPIRED("expired"), STALE_SOURCE("stale_source"), CLAIM_CONSUMED("claim_consumed"),
        AVAILABLE("available"), NAVIGATION_DISPATCHED("navigation_dispatched"), SELECTION_DISPATCHED("selection_dispatched"),
        CONFIRMATION_DISPATCHED("confirmation_dispatched"), INDETERMINATE("indeterminate");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public boolean dispatched() {
            return this == NAVIGATION_DISPATCHED || this == SELECTION_DISPATCHED || this == CONFIRMATION_DISPATCHED;
        }
        public static Status parse(String text) throws IOException {
            for (var status : values()) if (status.wire.equals(text)) return status;
            throw new IOException("Unknown AE2 result status");
        }
    }

    public CurrentZg361Ae2Result {
        Objects.requireNonNull(action); Objects.requireNonNull(status); Objects.requireNonNull(factsBefore);
        Objects.requireNonNull(owner); Objects.requireNonNull(source); Objects.requireNonNull(unavailableReason);
        CurrentLivingInventoryQuery.unsigned(providerGeneration,false);
        CurrentLivingInventoryQuery.unsigned(querySequence,false);
        CurrentLivingInventoryQuery.unsigned(claimSequence,false);
        StrictJson.require(factsBefore.isPresent() == owner.isPresent(), "AE2 actual Core/owner nullable roles differ");
        factsBefore.ifPresent(CurrentZg361Ae2::requirePrefix);
        if (status != Status.INDETERMINATE) {
            StrictJson.require(!nativeReturned || effectAttempted, "AE2 native return cannot precede actual entry");
            StrictJson.require(!effectAttempted || claimSequence.signum() > 0, "AE2 effect entry needs original spent claim");
            if (action.queryOnly()) StrictJson.require(claimSequence.signum() == 0 && !effectAttempted && !nativeReturned,
                    "AE2 readonly query cannot consume an action claim");
        }
        // Native forces invalid raw entry/return/query flags to INDETERMINATE but retains those actual diagnostics.
        if (status == Status.AVAILABLE || status.dispatched()) {
            StrictJson.require(source.isPresent() && factsBefore.isPresent() && cleanupKnown
                    && providerGeneration.signum() > 0 && querySequence.signum() > 0 && unavailableReason.isEmpty(),
                    "Successful AE2 needs actual immutable beforeSource/Core/owner and positive informational identity");
            var before = source.orElseThrow();
            StrictJson.require(before.kind() == action.sourceKind(), "AE2 action/immutable beforeSource kind differs");
            if (status == Status.AVAILABLE) StrictJson.require(action.queryOnly(), "AE2 available belongs only to query actions");
            else {
                StrictJson.require(!action.queryOnly() && status == dispatchStatus(action) && claimSequence.signum() > 0
                        && effectAttempted && nativeReturned && before.actionAdmissible(action),
                        "AE2 dispatched needs original entered/returned claim and admitted immutable beforeSource");
                if (action == CurrentZg361Ae2.Action.CHOOSE_PAY_NOW) StrictJson.require(before.events().orElseThrow().ae2()
                        .orElseThrow().recipientCharacterId() == Integer.toUnsignedLong(factsBefore.orElseThrow().playedCharacterId()),
                        "AE2 pay-now actual full recipient/Core actor differs");
            }
        } else {
            StrictJson.require(source.isEmpty(), "AE2 refusal/UNKNOWN must retain SourceNull");
            StrictJson.require(unavailableReason.filter(value -> !value.isEmpty()).isPresent(), "Actual nonempty AE2 refusal reason required");
        }
        if (!cleanupKnown) StrictJson.require(status == Status.INDETERMINATE, "Unknown AE2 cleanup stays indeterminate");
    }

    private static Status dispatchStatus(CurrentZg361Ae2.Action action) {
        return switch (action) {
            case CHOOSE_PAY_NOW -> Status.SELECTION_DISPATCHED;
            case CONFIRM_PRESENT, CONFIRM_VERIFY -> Status.CONFIRMATION_DISPATCHED;
            default -> Status.NAVIGATION_DISPATCHED;
        };
    }
    public boolean successful() { return status == Status.AVAILABLE || status.dispatched(); }
    public boolean sourceAvailable() { return source.isPresent(); }
    public boolean nativeHandled() { return false; }

    public static CurrentZg361Ae2Result decode(RawJson raw) throws IOException {
        try {
            var r = StrictJson.object(NativeWire.parse(raw.bytes()), Set.of("schema", "game_version", "executable_sha256", "adapter_id",
                    "backend", "action", "status", "source_available", "provider_generation", "query_sequence", "claim_sequence",
                    "effect_attempted", "native_returned", "native_handled", "cleanup_known", "facts_before", "owner", "source",
                    "addresses_redacted", "unavailable_reason"));
            var build = ExactCk3Build.CK3_121003_STEAM_26785313;
            CurrentLivingInventoryQuery.identity(r,"schema",CurrentZg361Ae2.RESULT_SCHEMA);
            CurrentLivingInventoryQuery.identity(r,"game_version",build.version());
            CurrentLivingInventoryQuery.identity(r,"executable_sha256",build.executableSha256());
            CurrentLivingInventoryQuery.identity(r,"adapter_id",build.coreFrameAdapterId());
            CurrentLivingInventoryQuery.identity(r,"backend",CurrentZg361Ae2.BACKEND);
            if (!CurrentLivingInventoryQuery.bool(r,"addresses_redacted") || CurrentLivingInventoryQuery.bool(r,"native_handled"))
                throw new IOException("AE2 addresses must be redacted and void native_handled false");
            Optional<CoreFrame.Prefix> facts = r.get("facts_before").isNull() ? Optional.empty()
                    : Optional.of(CurrentZg361Ae2.readCore(r.get("facts_before")));
            Optional<CurrentLetterResult.OwnerWitness> owner = Optional.empty();
            if (!r.get("owner").isNull()) {
                var w = StrictJson.object(r.get("owner"), Set.of("connection_generation", "ticket_sequence", "pump_epoch", "thread_id"));
                owner = Optional.of(new CurrentLetterResult.OwnerWitness(CurrentLivingInventoryQuery.decimal(w,"connection_generation"),
                        CurrentLivingInventoryQuery.decimal(w,"ticket_sequence"), CurrentLivingInventoryQuery.decimal(w,"pump_epoch"),
                        NativeWire.integer(w.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));
            }
            Optional<CurrentZg361Ae2Source> source = r.get("source").isNull() ? Optional.empty()
                    : Optional.of(CurrentZg361Ae2Source.decode(r.get("source")));
            if (CurrentLivingInventoryQuery.bool(r,"source_available") != source.isPresent()) throw new IOException("AE2 Source availability/null differs");
            return new CurrentZg361Ae2Result(CurrentZg361Ae2.Action.parse(NativeWire.text(r.get("action"))),
                    Status.parse(NativeWire.text(r.get("status"))), CurrentLivingInventoryQuery.bool(r,"effect_attempted"),
                    CurrentLivingInventoryQuery.bool(r,"native_returned"), CurrentLivingInventoryQuery.bool(r,"cleanup_known"),
                    CurrentLivingInventoryQuery.decimal(r,"provider_generation"), CurrentLivingInventoryQuery.decimal(r,"query_sequence"),
                    CurrentLivingInventoryQuery.decimal(r,"claim_sequence"), facts, owner, source,
                    r.get("unavailable_reason").isNull() ? Optional.empty() : Optional.of(NativeWire.text(r.get("unavailable_reason"))));
        } catch (IllegalArgumentException | ArithmeticException invalid) { throw new IOException("Invalid exact AE2 result DATA",invalid); }
    }

    public static CurrentZg361Ae2Result decodeOutcome(AckReceived original) throws IOException {
        Objects.requireNonNull(original);
        try {
            var e = StrictJson.object(NativeWire.parse(original.originalFrame().bytes()), Set.of("type", "protocol_version", "request_id", "ok", "result"));
            CurrentLivingInventoryQuery.identity(e,"type","command_result");
            CurrentLivingInventoryQuery.identity(e,"request_id",original.requestId());
            NativeWire.integer(e.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            if (CurrentLivingInventoryQuery.bool(e,"ok") != original.nativeOk()) throw new IOException("Original AE2 envelope ok differs");
            var token = original.originalResultToken().orElseThrow(() -> new IOException("Original AE2 result token absent"));
            if (!NativeWire.parse(token.bytes()).equals(e.get("result"))) throw new IOException("AE2 token differs from original envelope");
            var result = decode(new RawJson(token.bytes()));
            if (result.successful() != original.nativeOk()) throw new IOException("Original Native ok differs from AE2 result");
            return result;
        } catch (IllegalArgumentException invalid) { throw new IOException("Invalid actual AE2 acknowledgement",invalid); }
    }

    public RawJson encode() {
        var build = ExactCk3Build.CK3_121003_STEAM_26785313;
        var r = StrictJson.object().put("schema",CurrentZg361Ae2.RESULT_SCHEMA).put("game_version",build.version())
                .put("executable_sha256",build.executableSha256().toUpperCase(Locale.ROOT)).put("adapter_id",build.coreFrameAdapterId())
                .put("backend",CurrentZg361Ae2.BACKEND).put("action",action.wire()).put("status",status.wire())
                .put("source_available",source.isPresent()).put("provider_generation",providerGeneration.toString())
                .put("query_sequence",querySequence.toString()).put("claim_sequence",claimSequence.toString())
                .put("effect_attempted",effectAttempted).put("native_returned",nativeReturned).put("native_handled",false).put("cleanup_known",cleanupKnown);
        if (factsBefore.isPresent()) {
            r.set("facts_before",CurrentLivingInventoryQuery.prefix(factsBefore.orElseThrow()));
            var w = owner.orElseThrow(); r.putObject("owner").put("connection_generation",w.connectionGeneration().toString())
                    .put("ticket_sequence",w.ticketSequence().toString()).put("pump_epoch",w.pumpEpoch().toString()).put("thread_id",w.threadId());
        } else { r.putNull("facts_before"); r.putNull("owner"); }
        if (source.isPresent()) r.set("source",source.orElseThrow().encode()); else r.putNull("source");
        r.put("addresses_redacted",true);
        if (unavailableReason.isPresent()) r.put("unavailable_reason",unavailableReason.orElseThrow()); else r.putNull("unavailable_reason");
        return new RawJson(StrictJson.canonical(r));
    }
}
