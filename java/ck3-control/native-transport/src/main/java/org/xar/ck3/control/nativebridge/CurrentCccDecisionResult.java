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
public record CurrentCccDecisionResult(CurrentCccDecision.Action action, Status status,
        boolean effectAttempted, boolean nativeReturned, boolean nativeHandled, boolean cleanupKnown, BigInteger providerGeneration,
        BigInteger querySequence, BigInteger claimSequence, Optional<CoreFrame.Prefix> factsBefore,
        Optional<CurrentLetterResult.OwnerWitness> owner, Optional<CurrentCccDecisionSource> source,
        Optional<String> unavailableReason, Optional<CurrentCccDecision.DecisionKey> decisionKey) {
    public enum Status {
        UNAVAILABLE("unavailable"), EXPIRED("expired"), STALE_SOURCE("stale_source"), CLAIM_CONSUMED("claim_consumed"),
        AVAILABLE("available"), NAVIGATION_DISPATCHED("navigation_dispatched"), SELECTION_DISPATCHED("selection_dispatched"), CONFIRMATION_DISPATCHED("confirmation_dispatched"), INDETERMINATE("indeterminate");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static Status parse(String text) throws IOException {
            for (var value : values()) if (value.wire.equals(text)) return value;
            throw new IOException("Unknown CCC event status");
        }
    }
    public CurrentCccDecisionResult {
        Objects.requireNonNull(action);Objects.requireNonNull(status);Objects.requireNonNull(factsBefore);Objects.requireNonNull(owner);Objects.requireNonNull(source);Objects.requireNonNull(unavailableReason);Objects.requireNonNull(decisionKey);
        CurrentCccActorTransition.unsigned(providerGeneration,false);CurrentCccActorTransition.unsigned(querySequence,false);CurrentCccActorTransition.unsigned(claimSequence,false);
        StrictJson.require(factsBefore.isPresent()==owner.isPresent(),"Actual CCC Core/owner nullable roles differ");factsBefore.ifPresent(CurrentCccActorTransition::requireCore);
        StrictJson.require(!nativeReturned||effectAttempted,"Return requires actual dispatch entry");
        StrictJson.require(!effectAttempted||claimSequence.signum()>0,"Actual dispatch retains the spent once claim");
        StrictJson.require(!nativeHandled||action==CurrentCccDecision.Action.OPEN_LIST,"Only original Toggle OpenList has boolean handled DATA");
        if(action==CurrentCccDecision.Action.QUERY)StrictJson.require(decisionKey.isEmpty()&&claimSequence.signum()==0&&!effectAttempted&&!nativeReturned&&!nativeHandled,"Readonly query cannot claim an action");
        if(action==CurrentCccDecision.Action.OPEN_LIST)StrictJson.require(decisionKey.isEmpty(),"List navigation carries no fabricated selected key");
        if(source.isPresent())StrictJson.require(factsBefore.isPresent()&&cleanupKnown,"Complete immutable beforeSource requires original Core/owner and known cleanup");
        if(status==Status.AVAILABLE){
            StrictJson.require(action==CurrentCccDecision.Action.QUERY&&source.isPresent()&&cleanupKnown&&providerGeneration.signum()>0&&querySequence.signum()>0&&unavailableReason.isEmpty(),"Available fixed query requires complete actual Source");
        }else if(status==Status.NAVIGATION_DISPATCHED||status==Status.SELECTION_DISPATCHED||status==Status.CONFIRMATION_DISPATCHED){
            StrictJson.require(source.isPresent()&&cleanupKnown&&providerGeneration.signum()>0&&querySequence.signum()>0&&claimSequence.signum()>0&&effectAttempted&&nativeReturned&&unavailableReason.isEmpty(),"Dispatch requires original admitted beforeSource and spent private claim");
            var before=source.orElseThrow();
            if(status==Status.NAVIGATION_DISPATCHED)StrictJson.require(action==CurrentCccDecision.Action.OPEN_LIST&&decisionKey.isEmpty()&&before.openListAdmissible(),"Navigation must retain actual open admission");
            else if(status==Status.SELECTION_DISPATCHED)StrictJson.require(action==CurrentCccDecision.Action.OPEN_DETAIL&&decisionKey.isPresent()&&before.rows().stream().anyMatch(r->r.decisionKey()==decisionKey.orElseThrow()&&r.canOpenDetail()),"Detail selection binds exact original row");
            else StrictJson.require(action==CurrentCccDecision.Action.CONFIRM&&decisionKey.isPresent()&&before.confirmAdmissible()&&before.selectedDecisionKey().equals(decisionKey),"Confirmation binds actual selected fixed decision and original Can");
        }else{
            StrictJson.require(unavailableReason.filter(v->!v.isEmpty()).isPresent(),"Original known refusal/UNKNOWN reason required");
            if(status!=Status.INDETERMINATE)StrictJson.require(!effectAttempted&&!nativeReturned,"Known before-effect refusal cannot imply dispatch");
        }
        if(status==Status.INDETERMINATE)StrictJson.require(source.isEmpty(),"Unknown cleanup/dispatch has SourceNull");
        if(!cleanupKnown)StrictJson.require(status==Status.INDETERMINATE,"Unknown cleanup remains indeterminate");
    }
    public boolean successful() { return status == Status.AVAILABLE || status == Status.NAVIGATION_DISPATCHED || status == Status.SELECTION_DISPATCHED || status == Status.CONFIRMATION_DISPATCHED; }
    public boolean sourceAvailable() { return source.isPresent(); }
    public boolean decisionApplied() { return false; }
    public boolean newDateObserved() { return false; }
    public boolean physicalSaveConfirmed() { return false; }

    public static CurrentCccDecisionResult decode(RawJson raw) throws IOException {
        try {
            var r = StrictJson.object(NativeWire.parse(raw.bytes()), Set.of("schema", "game_version", "executable_sha256", "adapter_id", "backend",
                    "action", "status", "source_available", "provider_generation", "query_sequence", "claim_sequence", "effect_attempted",
                    "native_returned", "native_handled", "cleanup_known", "facts_before", "owner", "source", "decision_key", "addresses_redacted",
                    "decision_applied", "new_date_observed", "physical_save_confirmed", "unavailable_reason"));
            var b = ExactCk3Build.CK3_121003_STEAM_26785313;
            CurrentCccActorTransition.identity(r, "schema", CurrentCccDecision.RESULT_SCHEMA);
            CurrentCccActorTransition.identity(r, "game_version", b.version());
            CurrentCccActorTransition.identity(r, "executable_sha256", b.executableSha256().toUpperCase(Locale.ROOT));
            CurrentCccActorTransition.identity(r, "adapter_id", b.coreFrameAdapterId()); CurrentCccActorTransition.identity(r, "backend", CurrentCccDecision.BACKEND);
            if (!CurrentCccActorTransition.bool(r, "addresses_redacted")) throw new IOException("CCC event addresses must be redacted");
            for (String key : Set.of("decision_applied", "new_date_observed", "physical_save_confirmed"))
                if (CurrentCccActorTransition.bool(r, key)) throw new IOException("Void fixed selection cannot claim: " + key);
            Optional<CoreFrame.Prefix> facts = Optional.empty(); Optional<CurrentLetterResult.OwnerWitness> owner = Optional.empty();
            if (!r.get("facts_before").isNull()) {
                var p = StrictJson.object(r.get("facts_before"), Set.of("date_raw", "speed", "paused", "local_player_id", "map_ready", "has_played_character", "played_character_id", "played_character_alive"));
                facts = Optional.of(new CoreFrame.Prefix(CurrentCccActorTransition.i32(p.get("date_raw")), CurrentCccActorTransition.i32(p.get("speed")),
                        CurrentCccActorTransition.bool(p, "paused"), CurrentCccActorTransition.i32(p.get("local_player_id")), CurrentCccActorTransition.bool(p, "map_ready"),
                        CurrentCccActorTransition.bool(p, "has_played_character"), CurrentCccActorTransition.i32(p.get("played_character_id")), CurrentCccActorTransition.bool(p, "played_character_alive")));
            }
            if (!r.get("owner").isNull()) {
                var w = StrictJson.object(r.get("owner"), Set.of("connection_generation", "ticket_sequence", "pump_epoch", "thread_id"));
                owner = Optional.of(new CurrentLetterResult.OwnerWitness(CurrentCccActorTransition.decimal(w, "connection_generation"),
                        CurrentCccActorTransition.decimal(w, "ticket_sequence"), CurrentCccActorTransition.decimal(w, "pump_epoch"),
                        NativeWire.integer(w.get("thread_id"), BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact()));
            }
            var source = r.get("source").isNull() ? Optional.<CurrentCccDecisionSource>empty() : Optional.of(CurrentCccDecisionSource.decode(r.get("source")));
            if (CurrentCccActorTransition.bool(r, "source_available") != source.isPresent()) throw new IOException("CCC event Source availability/null mismatch");
            return new CurrentCccDecisionResult(CurrentCccDecision.Action.parse(NativeWire.text(r.get("action"))), Status.parse(NativeWire.text(r.get("status"))),
                    CurrentCccActorTransition.bool(r, "effect_attempted"), CurrentCccActorTransition.bool(r, "native_returned"), CurrentCccActorTransition.bool(r, "native_handled"), CurrentCccActorTransition.bool(r, "cleanup_known"),
                    CurrentCccActorTransition.decimal(r, "provider_generation"), CurrentCccActorTransition.decimal(r, "query_sequence"), CurrentCccActorTransition.decimal(r, "claim_sequence"),
                    facts, owner, source, r.get("unavailable_reason").isNull() ? Optional.empty() : Optional.of(NativeWire.text(r.get("unavailable_reason"))),
                    CurrentCccDecision.key(r.get("decision_key")));
        } catch (IllegalArgumentException | ArithmeticException invalid) { throw new IOException("Invalid exact CCC fixed event DATA", invalid); }
    }

    public static CurrentCccDecisionResult decodeOutcome(AckReceived original) throws IOException {
        Objects.requireNonNull(original);
        try {
            var e = StrictJson.object(NativeWire.parse(original.originalFrame().bytes()), Set.of("type", "protocol_version", "request_id", "ok", "result"));
            CurrentCccActorTransition.identity(e, "type", "command_result"); CurrentCccActorTransition.identity(e, "request_id", original.requestId());
            NativeWire.integer(e.get("protocol_version"), BigInteger.ONE, BigInteger.ONE);
            if (CurrentCccActorTransition.bool(e, "ok") != original.nativeOk()) throw new IOException("CCC event original envelope ok mismatch");
            var token = original.originalResultToken().orElseThrow(() -> new IOException("Original bookmark result token absent"));
            if (!NativeWire.parse(token.bytes()).equals(e.get("result"))) throw new IOException("CCC event token differs from original envelope");
            var result = decode(new RawJson(token.bytes()));
            if (result.successful() != original.nativeOk()) throw new IOException("Native ok differs from coherent fixed query/dispatch result");
            return result;
        } catch (IllegalArgumentException invalid) { throw new IOException("Invalid original bookmark acknowledgement", invalid); }
    }

    public RawJson encode() {
        var b = ExactCk3Build.CK3_121003_STEAM_26785313;
        var r = StrictJson.object().put("schema", CurrentCccDecision.RESULT_SCHEMA).put("game_version", b.version())
                .put("executable_sha256", b.executableSha256().toUpperCase(Locale.ROOT)).put("adapter_id", b.coreFrameAdapterId())
                .put("backend", CurrentCccDecision.BACKEND).put("action", action.wire()).put("status", status.wire())
                .put("source_available", source.isPresent()).put("provider_generation", providerGeneration.toString()).put("query_sequence", querySequence.toString())
                .put("claim_sequence", claimSequence.toString()).put("effect_attempted", effectAttempted).put("native_returned", nativeReturned)
                .put("native_handled", nativeHandled).put("cleanup_known", cleanupKnown);
        if (factsBefore.isPresent()) {
            r.set("facts_before", CurrentCccActorTransition.core(factsBefore.orElseThrow()));
            var w = owner.orElseThrow(); r.putObject("owner").put("connection_generation", w.connectionGeneration().toString())
                    .put("ticket_sequence", w.ticketSequence().toString()).put("pump_epoch", w.pumpEpoch().toString()).put("thread_id", w.threadId());
        } else { r.putNull("facts_before"); r.putNull("owner"); }
        if (source.isPresent()) r.set("source", source.orElseThrow().encode()); else r.putNull("source");
        if (decisionKey.isPresent()) r.put("decision_key", decisionKey.orElseThrow().wire()); else r.putNull("decision_key");
        r.put("addresses_redacted", true).put("decision_applied", false).put("new_date_observed", false).put("physical_save_confirmed", false);
        if (unavailableReason.isPresent()) r.put("unavailable_reason", unavailableReason.orElseThrow()); else r.putNull("unavailable_reason");
        return new RawJson(StrictJson.canonical(r));
    }
}
