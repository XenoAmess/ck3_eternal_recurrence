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
public record CurrentRmtmObservationResult(CurrentRmtmObservation.Action action, Status status,
        boolean effectAttempted, boolean nativeReturned, boolean nativeHandled, boolean cleanupKnown, BigInteger providerGeneration,
        BigInteger querySequence, BigInteger claimSequence, Optional<CoreFrame.Prefix> factsBefore,
        Optional<CurrentLetterResult.OwnerWitness> owner, Optional<CurrentRmtmObservationSource> source,
        Optional<String> unavailableReason) {
    public enum Status {
        UNAVAILABLE("unavailable"), EXPIRED("expired"), STALE_SOURCE("stale_source"), CLAIM_CONSUMED("claim_consumed"),
        AVAILABLE("available"), NAVIGATION_DISPATCHED("navigation_dispatched"), INDETERMINATE("indeterminate");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static Status parse(String text) throws IOException {
            for (var value : values()) if (value.wire.equals(text)) return value;
            throw new IOException("Unknown RMTM observation status");
        }
    }
    public CurrentRmtmObservationResult {
        Objects.requireNonNull(action);Objects.requireNonNull(status);Objects.requireNonNull(factsBefore);Objects.requireNonNull(owner);Objects.requireNonNull(source);Objects.requireNonNull(unavailableReason);
        CurrentRmtmActorTransition.unsigned(providerGeneration,false);CurrentRmtmActorTransition.unsigned(querySequence,false);CurrentRmtmActorTransition.unsigned(claimSequence,false);
        StrictJson.require(factsBefore.isPresent()==owner.isPresent(),"Actual Core/owner nullable pair differs");factsBefore.ifPresent(CurrentRmtmActorTransition::requireCore);
        StrictJson.require(!nativeReturned||effectAttempted,"Return requires actual entry");StrictJson.require(!effectAttempted||claimSequence.signum()>0,"Original spent claim required");
        StrictJson.require(!nativeHandled||action==CurrentRmtmObservation.Action.OPEN_BUDGET,"Only budget Open's actual Toggle boolean DATA may be true");
        if(action.queryOnly())StrictJson.require(claimSequence.signum()==0&&!effectAttempted&&!nativeReturned&&!nativeHandled,"Readonly query has no effect or claim");
        if(source.isPresent()){
            StrictJson.require(factsBefore.isPresent()&&cleanupKnown&&source.orElseThrow().kind()==action.kind(),"Complete actual Source kind/Core/cleanup required");
            source.orElseThrow().requireFacts(factsBefore.orElseThrow());
        }
        if(status==Status.AVAILABLE||status==Status.NAVIGATION_DISPATCHED){
            StrictJson.require(source.isPresent()&&providerGeneration.signum()>0&&querySequence.signum()>0&&cleanupKnown&&unavailableReason.isEmpty(),"Original actual complete Source and informational lease required");
            if(status==Status.AVAILABLE)StrictJson.require(action.queryOnly(),"Available is a readonly query");
            else{
                StrictJson.require(!action.queryOnly()&&claimSequence.signum()>0&&effectAttempted&&nativeReturned,"Actual once UI entry required");
                var s=source.orElseThrow();boolean admitted=switch(action){
                    case OPEN_BUDGET -> s.budget().orElseThrow().openAdmissible();
                    case CANCEL_BUDGET -> s.budget().orElseThrow().cancelAdmissible();
                    case OPEN_OFFER -> s.offer().orElseThrow().openAdmissible();
                    case CANCEL_OFFER -> s.offer().orElseThrow().cancelAdmissible();
                    default -> false;
                };StrictJson.require(admitted,"UI dispatch retains actual beforeSource admission");
            }
        }else{
            StrictJson.require(source.isEmpty()&&unavailableReason.filter(x->!x.isEmpty()).isPresent(),"Refusals/UNKNOWN remain SourceNull with original reason");
            if(status!=Status.INDETERMINATE)StrictJson.require(!effectAttempted&&!nativeReturned,"Known refusal cannot imply UI entry");
        }
        if(!cleanupKnown)StrictJson.require(status==Status.INDETERMINATE,"Unknown cleanup remains UNKNOWN");
    }
    public boolean successful() { return status == Status.AVAILABLE || status == Status.NAVIGATION_DISPATCHED; }
    public boolean sourceAvailable() { return source.isPresent(); }
    public boolean newDateObserved() { return false; }
    public boolean physicalSaveConfirmed() { return false; }

    public static CurrentRmtmObservationResult decode(RawJson raw) throws IOException {
        try {
            var r = StrictJson.object(NativeWire.parse(raw.bytes()), Set.of("schema", "game_version", "executable_sha256", "adapter_id", "backend",
                    "action", "status", "source_available", "provider_generation", "query_sequence", "claim_sequence", "effect_attempted",
                    "native_returned", "native_handled", "cleanup_known", "facts_before", "owner", "source", "addresses_redacted",
                    "new_date_observed", "physical_save_confirmed", "unavailable_reason"));
            var b = ExactCk3Build.CK3_121003_STEAM_26785313;
            CurrentRmtmActorTransition.identity(r, "schema", CurrentRmtmObservation.RESULT_SCHEMA);
            CurrentRmtmActorTransition.identity(r, "game_version", b.version());
            CurrentRmtmActorTransition.identity(r, "executable_sha256", b.executableSha256().toUpperCase(Locale.ROOT));
            CurrentRmtmActorTransition.identity(r, "adapter_id", b.coreFrameAdapterId()); CurrentRmtmActorTransition.identity(r, "backend", CurrentRmtmObservation.BACKEND);
            if (!CurrentRmtmActorTransition.bool(r, "addresses_redacted")) throw new IOException("RMTM observation addresses must be redacted");
            for (String key : Set.of("new_date_observed", "physical_save_confirmed"))
                if (CurrentRmtmActorTransition.bool(r, key)) throw new IOException("Void fixed selection cannot claim: " + key);
            Optional<CoreFrame.Prefix> facts = Optional.empty(); Optional<CurrentLetterResult.OwnerWitness> owner = Optional.empty();
            if (!r.get("facts_before").isNull()) {
                var p = StrictJson.object(r.get("facts_before"), Set.of("date_raw", "speed", "paused", "local_player_id", "map_ready", "has_played_character", "played_character_id", "played_character_alive"));
                facts = Optional.of(new CoreFrame.Prefix(CurrentRmtmActorTransition.i32(p.get("date_raw")), CurrentRmtmActorTransition.i32(p.get("speed")),
                        CurrentRmtmActorTransition.bool(p, "paused"), CurrentRmtmActorTransition.i32(p.get("local_player_id")), CurrentRmtmActorTransition.bool(p, "map_ready"),
                        CurrentRmtmActorTransition.bool(p, "has_played_character"), CurrentRmtmActorTransition.i32(p.get("played_character_id")), CurrentRmtmActorTransition.bool(p, "played_character_alive")));
            }
            if (!r.get("owner").isNull()) {
                var w = StrictJson.object(r.get("owner"), Set.of("connection_generation", "ticket_sequence", "pump_epoch", "thread_id"));
                owner = Optional.of(new CurrentLetterResult.OwnerWitness(CurrentRmtmActorTransition.decimal(w, "connection_generation"),
                        CurrentRmtmActorTransition.decimal(w, "ticket_sequence"), CurrentRmtmActorTransition.decimal(w, "pump_epoch"),
                        NativeWire.integer(w.get("thread_id"), BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact()));
            }
            var source = r.get("source").isNull() ? Optional.<CurrentRmtmObservationSource>empty() : Optional.of(CurrentRmtmObservationSource.decode(r.get("source")));
            if (CurrentRmtmActorTransition.bool(r, "source_available") != source.isPresent()) throw new IOException("RMTM observation Source availability/null mismatch");
            return new CurrentRmtmObservationResult(CurrentRmtmObservation.Action.parse(NativeWire.text(r.get("action"))), Status.parse(NativeWire.text(r.get("status"))),
                    CurrentRmtmActorTransition.bool(r, "effect_attempted"), CurrentRmtmActorTransition.bool(r, "native_returned"), CurrentRmtmActorTransition.bool(r, "native_handled"), CurrentRmtmActorTransition.bool(r, "cleanup_known"),
                    CurrentRmtmActorTransition.decimal(r, "provider_generation"), CurrentRmtmActorTransition.decimal(r, "query_sequence"), CurrentRmtmActorTransition.decimal(r, "claim_sequence"),
                    facts, owner, source, r.get("unavailable_reason").isNull() ? Optional.empty() : Optional.of(NativeWire.text(r.get("unavailable_reason"))));
        } catch (IllegalArgumentException | ArithmeticException invalid) { throw new IOException("Invalid exact RMTM observation DATA", invalid); }
    }

    public static CurrentRmtmObservationResult decodeOutcome(AckReceived original) throws IOException {
        Objects.requireNonNull(original);
        try {
            var e = StrictJson.object(NativeWire.parse(original.originalFrame().bytes()), Set.of("type", "protocol_version", "request_id", "ok", "result"));
            CurrentRmtmActorTransition.identity(e, "type", "command_result"); CurrentRmtmActorTransition.identity(e, "request_id", original.requestId());
            NativeWire.integer(e.get("protocol_version"), BigInteger.ONE, BigInteger.ONE);
            if (CurrentRmtmActorTransition.bool(e, "ok") != original.nativeOk()) throw new IOException("RMTM observation original envelope ok mismatch");
            var token = original.originalResultToken().orElseThrow(() -> new IOException("Original RMTM observation result token absent"));
            if (!NativeWire.parse(token.bytes()).equals(e.get("result"))) throw new IOException("RMTM observation token differs from original envelope");
            var result = decode(new RawJson(token.bytes()));
            if (result.successful() != original.nativeOk()) throw new IOException("Native ok differs from coherent fixed query/dispatch result");
            return result;
        } catch (IllegalArgumentException invalid) { throw new IOException("Invalid original RMTM observation acknowledgement", invalid); }
    }

    public RawJson encode() {
        var b = ExactCk3Build.CK3_121003_STEAM_26785313;
        var r = StrictJson.object().put("schema", CurrentRmtmObservation.RESULT_SCHEMA).put("game_version", b.version())
                .put("executable_sha256", b.executableSha256().toUpperCase(Locale.ROOT)).put("adapter_id", b.coreFrameAdapterId())
                .put("backend", CurrentRmtmObservation.BACKEND).put("action", action.wire()).put("status", status.wire())
                .put("source_available", source.isPresent()).put("provider_generation", providerGeneration.toString()).put("query_sequence", querySequence.toString())
                .put("claim_sequence", claimSequence.toString()).put("effect_attempted", effectAttempted).put("native_returned", nativeReturned)
                .put("native_handled", nativeHandled).put("cleanup_known", cleanupKnown);
        if (factsBefore.isPresent()) {
            r.set("facts_before", CurrentRmtmActorTransition.core(factsBefore.orElseThrow()));
            var w = owner.orElseThrow(); r.putObject("owner").put("connection_generation", w.connectionGeneration().toString())
                    .put("ticket_sequence", w.ticketSequence().toString()).put("pump_epoch", w.pumpEpoch().toString()).put("thread_id", w.threadId());
        } else { r.putNull("facts_before"); r.putNull("owner"); }
        if (source.isPresent()) r.set("source", source.orElseThrow().encode()); else r.putNull("source");

        r.put("addresses_redacted", true).put("new_date_observed", false).put("physical_save_confirmed", false);
        if (unavailableReason.isPresent()) r.put("unavailable_reason", unavailableReason.orElseThrow()); else r.putNull("unavailable_reason");
        return new RawJson(StrictJson.canonical(r));
    }
}
