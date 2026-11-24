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

/** Dispatch is only the original entered/returned fact. It does not prove an opened view or applied product effect. */
public record CurrentLivingEntryResult(CurrentLivingEntry.Action action, Status status, boolean effectAttempted,
        boolean nativeReturned, boolean cleanupKnown, BigInteger providerGeneration, BigInteger querySequence,
        BigInteger claimSequence, Optional<CoreFrame.Prefix> factsBefore, Optional<CurrentLetterResult.OwnerWitness> owner,
        Optional<CurrentLivingEntrySource> source, Optional<String> unavailableReason) {
    public enum Status {
        UNAVAILABLE("unavailable"), AVAILABLE("available"), DISPATCHED("dispatched"), REJECTED("rejected"),
        EXPIRED("expired"), STALE_SOURCE("stale_source"), INDETERMINATE("indeterminate");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Status parse(String text) throws IOException {
            for (var status : values()) if (status.wire.equals(text)) return status;
            throw new IOException("Unknown Living entry status");
        }
    }

    public CurrentLivingEntryResult {
        Objects.requireNonNull(action); Objects.requireNonNull(status); Objects.requireNonNull(factsBefore);
        Objects.requireNonNull(owner); Objects.requireNonNull(source); Objects.requireNonNull(unavailableReason);
        CurrentLivingInventoryQuery.unsigned(providerGeneration,false);
        CurrentLivingInventoryQuery.unsigned(querySequence,false);
        CurrentLivingInventoryQuery.unsigned(claimSequence,false);
        StrictJson.require(factsBefore.isPresent()==owner.isPresent(),"Actual entry Core/owner nullable roles differ");
        factsBefore.ifPresent(CurrentLivingEntry::requirePrefix);
        StrictJson.require(!nativeReturned||effectAttempted,"Native return cannot precede actual effect entry");
        StrictJson.require(!effectAttempted||claimSequence.signum()>0,"Effect entry must retain original spent claim");
        if(action.queryOnly()) StrictJson.require(claimSequence.signum()==0&&!effectAttempted&&!nativeReturned,
                "Readonly entry query cannot consume an action claim");
        if(status==Status.AVAILABLE||status==Status.DISPATCHED) {
            StrictJson.require(source.isPresent()&&factsBefore.isPresent()&&cleanupKnown&&providerGeneration.signum()>0
                    &&querySequence.signum()>0&&unavailableReason.isEmpty(),"Successful entry must retain complete actual Source/Core/owner");
            var before=source.orElseThrow();
            StrictJson.require(before.kind()==action.sourceKind()
                    &&before.actorFullId()==Integer.toUnsignedLong(factsBefore.orElseThrow().playedCharacterId()),
                    "Immutable entry beforeSource must match actual kind and full actor");
            if(status==Status.AVAILABLE) StrictJson.require(action.queryOnly(),"Available belongs only to entry queries");
            else StrictJson.require(!action.queryOnly()&&claimSequence.signum()>0&&effectAttempted&&nativeReturned
                    &&before.actionAdmissible(action),"Dispatched requires original admitted immutable beforeSource");
        } else {
            StrictJson.require(source.isEmpty(),"Refusal/UNKNOWN must retain SourceNull");
            StrictJson.require(unavailableReason.filter(x->!x.isEmpty()).isPresent(),"Actual refusal reason required");
            // Native wire retains actual provider/query/claim and entry/return facts; a refusal is not a synthetic zero-effect result.
        }
        if(!cleanupKnown) StrictJson.require(status==Status.INDETERMINATE,"Unknown cleanup must remain indeterminate");
        if(status==Status.INDETERMINATE) StrictJson.require(source.isEmpty(),"UNKNOWN must not borrow complete Source");
    }

    public boolean successful(){return status==Status.AVAILABLE||status==Status.DISPATCHED;}
    public boolean sourceAvailable(){return source.isPresent();}
    public boolean nativeHandled(){return false;}
    public boolean newDateObserved(){return false;}
    public boolean physicalSaveConfirmed(){return false;}

    public static CurrentLivingEntryResult decode(RawJson raw)throws IOException {
        try {
            var r=StrictJson.object(NativeWire.parse(raw.bytes()),Set.of("schema","game_version","executable_sha256","adapter_id",
                    "backend","action","status","source_available","provider_generation","query_sequence","claim_sequence",
                    "effect_attempted","native_returned","native_handled","cleanup_known","facts_before","owner","source",
                    "addresses_redacted","new_date_observed","physical_save_confirmed","unavailable_reason"));
            var build=ExactCk3Build.CK3_121003_STEAM_26785313;
            CurrentLivingInventoryQuery.identity(r,"schema",CurrentLivingEntry.RESULT_SCHEMA);
            CurrentLivingInventoryQuery.identity(r,"game_version",build.version());
            CurrentLivingInventoryQuery.identity(r,"executable_sha256",build.executableSha256());
            CurrentLivingInventoryQuery.identity(r,"adapter_id",build.coreFrameAdapterId());
            CurrentLivingInventoryQuery.identity(r,"backend",CurrentLivingEntry.BACKEND);
            if(!CurrentLivingInventoryQuery.bool(r,"addresses_redacted"))throw new IOException("Entry addresses must be redacted");
            for(var key:Set.of("native_handled","new_date_observed","physical_save_confirmed"))
                if(CurrentLivingInventoryQuery.bool(r,key))throw new IOException("Entry cannot claim applied business facts: "+key);
            Optional<CoreFrame.Prefix> facts=r.get("facts_before").isNull()?Optional.empty():Optional.of(CurrentLivingEntry.readCore(r.get("facts_before")));
            Optional<CurrentLetterResult.OwnerWitness> owner=Optional.empty();
            if(!r.get("owner").isNull()) {
                var w=StrictJson.object(r.get("owner"),Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));
                owner=Optional.of(new CurrentLetterResult.OwnerWitness(CurrentLivingInventoryQuery.decimal(w,"connection_generation"),
                        CurrentLivingInventoryQuery.decimal(w,"ticket_sequence"),CurrentLivingInventoryQuery.decimal(w,"pump_epoch"),
                        NativeWire.integer(w.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));
            }
            Optional<CurrentLivingEntrySource> source=r.get("source").isNull()?Optional.empty():Optional.of(CurrentLivingEntrySource.decode(r.get("source")));
            if(CurrentLivingInventoryQuery.bool(r,"source_available")!=source.isPresent())throw new IOException("Entry Source availability/null differs");
            return new CurrentLivingEntryResult(CurrentLivingEntry.Action.parse(NativeWire.text(r.get("action"))),
                    Status.parse(NativeWire.text(r.get("status"))),CurrentLivingInventoryQuery.bool(r,"effect_attempted"),
                    CurrentLivingInventoryQuery.bool(r,"native_returned"),CurrentLivingInventoryQuery.bool(r,"cleanup_known"),
                    CurrentLivingInventoryQuery.decimal(r,"provider_generation"),CurrentLivingInventoryQuery.decimal(r,"query_sequence"),
                    CurrentLivingInventoryQuery.decimal(r,"claim_sequence"),facts,owner,source,
                    r.get("unavailable_reason").isNull()?Optional.empty():Optional.of(NativeWire.text(r.get("unavailable_reason"))));
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid exact Living entry result DATA",invalid);}
    }

    public static CurrentLivingEntryResult decodeOutcome(AckReceived original)throws IOException {
        Objects.requireNonNull(original);
        try {
            var envelope=StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));
            CurrentLivingInventoryQuery.identity(envelope,"type","command_result");
            CurrentLivingInventoryQuery.identity(envelope,"request_id",original.requestId());
            NativeWire.integer(envelope.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            if(CurrentLivingInventoryQuery.bool(envelope,"ok")!=original.nativeOk())throw new IOException("Original entry envelope ok differs");
            var token=original.originalResultToken().orElseThrow(()->new IOException("Original entry result token absent"));
            if(!NativeWire.parse(token.bytes()).equals(envelope.get("result")))throw new IOException("Entry token differs from original envelope");
            var result=decode(new RawJson(token.bytes()));
            if(result.successful()!=original.nativeOk())throw new IOException("Original native ok differs from entry result");
            return result;
        }catch(IllegalArgumentException invalid){throw new IOException("Invalid actual Living entry acknowledgement",invalid);}
    }

    public RawJson encode() {
        var build=ExactCk3Build.CK3_121003_STEAM_26785313;
        var r=StrictJson.object().put("schema",CurrentLivingEntry.RESULT_SCHEMA).put("game_version",build.version())
                .put("executable_sha256",build.executableSha256().toUpperCase(Locale.ROOT)).put("adapter_id",build.coreFrameAdapterId())
                .put("backend",CurrentLivingEntry.BACKEND).put("action",action.wire()).put("status",status.wire())
                .put("source_available",source.isPresent()).put("provider_generation",providerGeneration.toString())
                .put("query_sequence",querySequence.toString()).put("claim_sequence",claimSequence.toString())
                .put("effect_attempted",effectAttempted).put("native_returned",nativeReturned).put("native_handled",false).put("cleanup_known",cleanupKnown);
        if(factsBefore.isPresent()) {
            r.set("facts_before",CurrentLivingInventoryQuery.prefix(factsBefore.orElseThrow()));
            var w=owner.orElseThrow();r.putObject("owner").put("connection_generation",w.connectionGeneration().toString())
                    .put("ticket_sequence",w.ticketSequence().toString()).put("pump_epoch",w.pumpEpoch().toString()).put("thread_id",w.threadId());
        }else{r.putNull("facts_before");r.putNull("owner");}
        if(source.isPresent())r.set("source",source.orElseThrow().encode());else r.putNull("source");
        r.put("addresses_redacted",true).put("new_date_observed",false).put("physical_save_confirmed",false);
        if(unavailableReason.isPresent())r.put("unavailable_reason",unavailableReason.orElseThrow());else r.putNull("unavailable_reason");
        return new RawJson(StrictJson.canonical(r));
    }
}
