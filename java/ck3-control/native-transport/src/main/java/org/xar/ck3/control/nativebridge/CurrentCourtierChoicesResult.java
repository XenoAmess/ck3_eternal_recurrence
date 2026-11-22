package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
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

/** Exact catalogue result DATA; opaque original row tokens are never caller authority. */
public record CurrentCourtierChoicesResult(CurrentCourtierChoices.Action action,Status status,boolean effectAttempted,boolean nativeReturned,
        boolean cleanupKnown,BigInteger providerGeneration,BigInteger querySequence,BigInteger claimSequence,
        Optional<CoreFrame.Prefix> factsBefore,Optional<CurrentLetterResult.OwnerWitness> owner,Optional<CurrentCourtierChoicesSource> source,
        Optional<String> unavailableReason,CurrentCourtierControls.Product product,CurrentCourtierChoices.Catalog catalog,String choiceToken) {
    public enum Status {
        UNAVAILABLE("unavailable"),EXPIRED("expired"),STALE_SOURCE("stale_source"),CLAIM_CONSUMED("claim_consumed"),
        AVAILABLE("available"),CHOICE_DISPATCHED("choice_dispatched"),INDETERMINATE("indeterminate");
        private final String wire;Status(String wire){this.wire=wire;}public String wire(){return wire;}
        static Status parse(String value)throws IOException {for(var status:values())if(status.wire.equals(value))return status;throw new IOException("Unknown current courtier controls status");}
    }
    public CurrentCourtierChoicesResult {
        Objects.requireNonNull(action);Objects.requireNonNull(status);CurrentLetter.unsigned(providerGeneration,false);
        CurrentLetter.unsigned(querySequence,false);CurrentLetter.unsigned(claimSequence,false);
        Objects.requireNonNull(factsBefore);Objects.requireNonNull(owner);Objects.requireNonNull(source);Objects.requireNonNull(unavailableReason);Objects.requireNonNull(product);Objects.requireNonNull(catalog);Objects.requireNonNull(choiceToken);
        if(action==CurrentCourtierChoices.Action.QUERY_CHOICES)StrictJson.require(choiceToken.isEmpty()&&claimSequence.signum()==0&&!effectAttempted&&!nativeReturned,"Courtier query never takes an effect claim or enters a callback");
        else{CurrentCourtierChoices.token(choiceToken);StrictJson.require(providerGeneration.signum()>0&&querySequence.signum()>0,"Every parsed select retains its original positive private lease");}
        StrictJson.require(!nativeReturned||effectAttempted,"A returned prompt callback requires its actual effect attempt");
        StrictJson.require(factsBefore.isPresent()==owner.isPresent(),"Actual Core/owner nullable roles differ");
        factsBefore.ifPresent(CurrentLetter::requirePrefix);
        if(source.isPresent()) {
            StrictJson.require(factsBefore.isPresent()&&cleanupKnown,"Actual full census requires observed Core/owner/cleanup");
            var actual=source.orElseThrow();
            StrictJson.require(actual.product()==product&&actual.catalog()==catalog,"Courtier source product/catalog differs from original result");
        }
        if(status==Status.AVAILABLE)StrictJson.require(action==CurrentCourtierChoices.Action.QUERY_CHOICES&&source.isPresent()&&providerGeneration.signum()>0
                &&querySequence.signum()>0&&!effectAttempted&&!nativeReturned&&claimSequence.signum()==0&&unavailableReason.isEmpty(),"Available complete courtier controls query coherence differs");
        else if(status==Status.CHOICE_DISPATCHED) {
            StrictJson.require(action!=CurrentCourtierChoices.Action.QUERY_CHOICES&&status==dispatchedStatus(action)&&source.isPresent()&&providerGeneration.signum()>0
                    &&querySequence.signum()>0&&claimSequence.signum()>0&&effectAttempted&&nativeReturned&&unavailableReason.isEmpty(),"Void actual-instance reply coherence differs");
            var actual=source.orElseThrow();StrictJson.require(actual.rows().stream().anyMatch(row->row.choiceToken().equals(choiceToken)&&row.executeAdmissible()),"Original actual private row does not admit selection");
        } else {
            StrictJson.require(unavailableReason.filter(s->!s.isEmpty()).isPresent(),"Original courtier controls refusal reason required");
            if(status!=Status.INDETERMINATE)StrictJson.require(!effectAttempted&&!nativeReturned,"Known prompt refusal must retain zero effect/callback flags even if a once claim was spent");
        }
    }
    public boolean successful(){return status==Status.AVAILABLE||status==Status.CHOICE_DISPATCHED;}
    public static Status dispatchedStatus(CurrentCourtierChoices.Action action){if(action!=CurrentCourtierChoices.Action.SELECT_CHOICE)throw new IllegalArgumentException("Query has no dispatch status");return Status.CHOICE_DISPATCHED;}
    public static CurrentCourtierChoicesResult decode(RawJson raw)throws IOException {
        try {
            var r=StrictJson.object(NativeWire.parse(raw.bytes()),Set.of("schema","game_version","executable_sha256","backend","adapter_id","action","status","source_available","effect_attempted","native_returned","native_handled","cleanup_known","provider_generation","query_sequence","claim_sequence","facts_before","owner","source","addresses_redacted","creator_closed","courtier_created","selection_changed","new_date_observed","physical_save_confirmed","unavailable_reason","product","catalog","choice_token"));
            var b=ExactCk3Build.CK3_121003_STEAM_26785313;require(r,"schema",CurrentCourtierChoices.RESULT_SCHEMA);require(r,"game_version",b.version());
            require(r,"executable_sha256",b.executableSha256().toUpperCase(Locale.ROOT));require(r,"adapter_id",b.coreFrameAdapterId());require(r,"backend",CurrentCourtierChoices.BACKEND);
            if(!bool(r,"addresses_redacted")||bool(r,"native_handled")||bool(r,"creator_closed")||bool(r,"courtier_created")||bool(r,"selection_changed")||bool(r,"new_date_observed")||bool(r,"physical_save_confirmed"))throw new IOException("Courtier DATA cannot claim native handling/closed/date/SAVE");
            Optional<CoreFrame.Prefix> core=Optional.empty();Optional<CurrentLetterResult.OwnerWitness> owner=Optional.empty();Optional<CurrentCourtierChoicesSource> source=Optional.empty();
            if(!r.get("facts_before").isNull()){var p=StrictJson.object(r.get("facts_before"),Set.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"));core=Optional.of(new CoreFrame.Prefix(i32(p.get("date_raw")),i32(p.get("speed")),bool(p,"paused"),i32(p.get("local_player_id")),bool(p,"map_ready"),bool(p,"has_played_character"),i32(p.get("played_character_id")),bool(p,"played_character_alive")));}
            if(!r.get("owner").isNull()){var w=StrictJson.object(r.get("owner"),Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));owner=Optional.of(new CurrentLetterResult.OwnerWitness(decimal(w,"connection_generation"),decimal(w,"ticket_sequence"),decimal(w,"pump_epoch"),NativeWire.integer(w.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));}
            if(!r.get("source").isNull())source=Optional.of(CurrentCourtierChoicesSource.decode(r.get("source")));
            if(bool(r,"source_available")!=source.isPresent())throw new IOException("Courtier source availability/null mismatch");
            return new CurrentCourtierChoicesResult(CurrentCourtierChoices.Action.parse(NativeWire.text(r.get("action"))),Status.parse(NativeWire.text(r.get("status"))),bool(r,"effect_attempted"),bool(r,"native_returned"),bool(r,"cleanup_known"),decimal(r,"provider_generation"),decimal(r,"query_sequence"),decimal(r,"claim_sequence"),core,owner,source,r.get("unavailable_reason").isNull()?Optional.empty():Optional.of(NativeWire.text(r.get("unavailable_reason"))),CurrentCourtierControls.Product.parse(NativeWire.text(r.get("product"))),CurrentCourtierChoices.Catalog.parse(NativeWire.text(r.get("catalog"))),choiceTokenData(r.get("choice_token")));
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid exact current courtier controls DATA",invalid);}
    }
    public static CurrentCourtierChoicesResult decodeOutcome(AckReceived original)throws IOException {
        try {
            var e=StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));
            require(e,"type","command_result");require(e,"request_id",original.requestId());NativeWire.integer(e.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            if(bool(e,"ok")!=original.nativeOk())throw new IOException("Original courtier controls envelope ok mismatch");
            var token=original.originalResultToken().orElseThrow(()->new IOException("Original courtier controls result token absent"));
            if(!NativeWire.parse(token.bytes()).equals(e.get("result")))throw new IOException("Courtier result differs from original envelope");
            var result=decode(new RawJson(token.bytes()));if(result.successful()!=original.nativeOk())throw new IOException("Native ok differs from coherent actual-source/void-dispatch result");return result;
        }catch(IllegalArgumentException invalid){throw new IOException("Invalid actual courtier controls acknowledgement",invalid);}
    }
    public RawJson encode() {
        var b=ExactCk3Build.CK3_121003_STEAM_26785313;
        var r=StrictJson.object().put("schema",CurrentCourtierChoices.RESULT_SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256().toUpperCase(Locale.ROOT))
                .put("backend",CurrentCourtierChoices.BACKEND).put("adapter_id",b.coreFrameAdapterId()).put("action",action.wire()).put("status",status.wire())
                .put("source_available",source.isPresent()).put("effect_attempted",effectAttempted).put("native_returned",nativeReturned).put("native_handled",false).put("cleanup_known",cleanupKnown)
                .put("provider_generation",providerGeneration.toString()).put("query_sequence",querySequence.toString()).put("claim_sequence",claimSequence.toString());
        if(factsBefore.isPresent()){var p=factsBefore.orElseThrow();r.putObject("facts_before").put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused()).put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter()).put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());var w=owner.orElseThrow();r.putObject("owner").put("connection_generation",w.connectionGeneration().toString()).put("ticket_sequence",w.ticketSequence().toString()).put("pump_epoch",w.pumpEpoch().toString()).put("thread_id",w.threadId());}
        else{r.putNull("facts_before");r.putNull("owner");}
        if(source.isPresent())r.set("source",source.orElseThrow().encode());else r.putNull("source");
        r.put("product",product.wire()).put("catalog",catalog.wire()).put("choice_token",choiceToken);
        r.put("addresses_redacted",true).put("creator_closed",false).put("courtier_created",false).put("selection_changed",false).put("new_date_observed",false).put("physical_save_confirmed",false);
        if(unavailableReason.isPresent())r.put("unavailable_reason",unavailableReason.orElseThrow());else r.putNull("unavailable_reason");return new RawJson(StrictJson.canonical(r));
    }
    private static String choiceTokenData(JsonNode n)throws IOException{if(n==null||!n.isTextual())throw new IOException("Actual choice token text required; query alone uses empty text");return n.textValue();}
    private static int i32(JsonNode n)throws IOException{return NativeWire.integer(n,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
    private static boolean bool(ObjectNode r,String k)throws IOException {var n=r.get(k);if(n==null||!n.isBoolean())throw new IOException("Actual courtier controls bool required: "+k);return n.booleanValue();}
    private static BigInteger decimal(ObjectNode r,String k)throws IOException {String s=NativeWire.text(r.get(k));if(!s.matches("0|[1-9][0-9]{0,19}"))throw new IOException("Canonical uint64 string required: "+k);var n=new BigInteger(s);CurrentLetter.unsigned(n,false);return n;}
    private static void require(ObjectNode r,String k,String expected)throws IOException {if(!NativeWire.text(r.get(k)).equals(expected))throw new IOException("Exact current courtier controls identity mismatch: "+k);}
}
