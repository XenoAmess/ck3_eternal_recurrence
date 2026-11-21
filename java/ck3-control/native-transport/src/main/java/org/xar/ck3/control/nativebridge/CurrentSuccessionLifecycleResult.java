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
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** Lifecycle DATA never aliases a living CoreFrame. Continue callback return is not inheritance or SAVE confirmation. */
public record CurrentSuccessionLifecycleResult(CurrentSuccessionLifecycle.Action action,Status status,boolean sourceAvailable,
        boolean effectAttempted,boolean nativeReturned,BigInteger providerGeneration,BigInteger querySequence,BigInteger claimSequence,
        Optional<CurrentSuccessionLifecycle.WorldBefore> worldBefore,Optional<CurrentSuccessionLifecycle.SourceBefore> source,
        Optional<OwnerWitness> ownerWitness,Optional<String> unavailableReason) {
    public enum Status { UNAVAILABLE,EXPIRED,STALE_SOURCE,CLAIM_CONSUMED,AVAILABLE,DISPATCHED,INDETERMINATE;
        public String wire(){return name().toLowerCase(Locale.ROOT);}
    }
    public record OwnerWitness(BigInteger connectionGeneration,BigInteger ticketSequence,BigInteger pumpEpoch,long threadId) {
        public OwnerWitness {u64(connectionGeneration,true);u64(ticketSequence,true);u64(pumpEpoch,true);StrictJson.require(threadId>0&&threadId<=0xffff_ffffL,"Actual positive uint32 owner thread required");}
    }
    public CurrentSuccessionLifecycleResult {
        Objects.requireNonNull(action);Objects.requireNonNull(status);u64(providerGeneration,false);u64(querySequence,false);u64(claimSequence,false);
        Objects.requireNonNull(worldBefore);Objects.requireNonNull(source);Objects.requireNonNull(ownerWitness);Objects.requireNonNull(unavailableReason);
        StrictJson.require(worldBefore.isPresent()==ownerWitness.isPresent(),"Lifecycle world and owner are present or explicit null together");
        StrictJson.require(sourceAvailable==source.isPresent(),"Wire source is explicit null unless native source_available qualified");
        if(sourceAvailable)StrictJson.require(worldBefore.isPresent()&&ownerWitness.isPresent()&&worldBefore.orElseThrow().paused()
                &&source.orElseThrow().qualifiedRelation(worldBefore.orElseThrow()),"Actual paused lifecycle world, native source and typed relation required");
        if(status==Status.AVAILABLE)StrictJson.require(action==CurrentSuccessionLifecycle.Action.QUERY_DEFAULT&&sourceAvailable&&providerGeneration.signum()>0&&querySequence.signum()>0&&!effectAttempted&&!nativeReturned&&claimSequence.signum()==0&&unavailableReason.isEmpty(),"Available is a readonly query with a positive private lease, never a continuation effect");
        if(status==Status.DISPATCHED)StrictJson.require(action==CurrentSuccessionLifecycle.Action.CONTINUE_DEFAULT&&sourceAvailable&&providerGeneration.signum()>0&&querySequence.signum()>0&&effectAttempted&&nativeReturned&&claimSequence.signum()>0&&unavailableReason.isEmpty(),"Official void Close dispatch requires its actual source and once claim; it is not handled=true or a confirmed inheritance");
        if(status!=Status.AVAILABLE&&status!=Status.DISPATCHED)StrictJson.require(unavailableReason.filter(s->!s.isEmpty()).isPresent(),"Original lifecycle refusal/uncertainty reason required");
    }
    public boolean nativeOk(){return status==Status.AVAILABLE||status==Status.DISPATCHED;}
    public RawJson encode() {
        var b=ExactCk3Build.CK3_121003_STEAM_26785313;
        var r=StrictJson.object().put("schema",CurrentSuccessionLifecycle.RESULT_SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256().toUpperCase(Locale.ROOT))
                .put("adapter_id",b.coreFrameAdapterId()).put("backend",CurrentSuccessionLifecycle.BACKEND).put("step",action.step()).put("action",action.wire()).put("status",status.wire())
                .put("source_available",sourceAvailable).put("effect_attempted",effectAttempted).put("native_returned",nativeReturned).put("native_handled",false)
                .put("provider_generation",providerGeneration.toString()).put("query_sequence",querySequence.toString()).put("claim_sequence",claimSequence.toString());
        if(worldBefore.isPresent()) {
            var w=worldBefore.orElseThrow();r.putObject("world_before").put("schema",CurrentSuccessionLifecycle.WORLD_SCHEMA).put("date_raw",w.dateRaw()).put("speed",w.speed()).put("paused",w.paused()).put("local_player_id",w.localPlayerId())
                    .put("map_ready",w.mapReady()).put("has_played_character",w.hasPlayedCharacter()).put("played_character_id",w.playedCharacter().map(NativeCharacterId::value).orElse(-1)).put("played_character_alive",w.playedCharacterAlive());
        } else r.putNull("world_before");
        if(source.isPresent()) {
            var s=source.orElseThrow();r.putObject("source").put("schema",CurrentSuccessionLifecycle.SOURCE_SCHEMA).put("dead_character_id",s.deadCharacter().map(NativeCharacterId::value).orElse(-1)).put("continue_character_id",s.continueCharacter().map(NativeCharacterId::value).orElse(-1))
                    .put("player_relation",s.playerRelation().name().toLowerCase(Locale.ROOT)).put("dead_character_dead",s.deadCharacterDead()).put("continue_character_alive",s.continueCharacterAlive()).put("handler_source_verified",s.handlerSourceVerified()).put("named_root_bound",s.namedRootBound())
                    .put("window_visible",s.windowVisible()).put("window_enabled",s.windowEnabled()).put("default_button_admissible",s.defaultButtonAdmissible()).put("default_native_route",s.defaultNativeRoute()).put("stable_two_pass_verified",s.stableTwoPassVerified());
        } else r.putNull("source");
        if(ownerWitness.isPresent()){var w=ownerWitness.orElseThrow();r.putObject("owner_witness").put("connection_generation",w.connectionGeneration().toString()).put("ticket_sequence",w.ticketSequence().toString()).put("pump_epoch",w.pumpEpoch().toString()).put("thread_id",w.threadId());}else r.putNull("owner_witness");
        r.put("addresses_redacted",true).put("continuation_confirmed",false).put("physical_save_confirmed",false);if(unavailableReason.isPresent())r.put("unavailable_reason",unavailableReason.orElseThrow());else r.putNull("unavailable_reason");
        return new RawJson(StrictJson.canonical(r));
    }
    public static CurrentSuccessionLifecycleResult decode(RawJson raw)throws IOException {
        try {
            var r=StrictJson.object(NativeWire.parse(raw.bytes()),Set.of("schema","game_version","executable_sha256","adapter_id","backend","step","action","status","source_available","effect_attempted","native_returned","native_handled","provider_generation","query_sequence","claim_sequence","world_before","source","owner_witness","addresses_redacted","continuation_confirmed","physical_save_confirmed","unavailable_reason"));
            var b=ExactCk3Build.CK3_121003_STEAM_26785313;eq(r,"schema",CurrentSuccessionLifecycle.RESULT_SCHEMA);eq(r,"game_version",b.version());eq(r,"executable_sha256",b.executableSha256().toUpperCase(Locale.ROOT));eq(r,"adapter_id",b.coreFrameAdapterId());eq(r,"backend",CurrentSuccessionLifecycle.BACKEND);
            CurrentSuccessionLifecycle.Action action=action(text(r,"action"));eq(r,"step",action.step());Status status=status(text(r,"status"));
            if(bool(r,"native_handled")||bool(r,"continuation_confirmed")||bool(r,"physical_save_confirmed")||!bool(r,"addresses_redacted"))throw new IOException("Lifecycle void callback cannot grant handled/continuation/SAVE or expose addresses");
            Optional<CurrentSuccessionLifecycle.WorldBefore> world=Optional.empty();Optional<OwnerWitness> owner=Optional.empty();Optional<CurrentSuccessionLifecycle.SourceBefore> source=Optional.empty();
            if(!r.get("world_before").isNull()) {
                var w=StrictJson.object(r.get("world_before"),Set.of("schema","date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"));eq(w,"schema",CurrentSuccessionLifecycle.WORLD_SCHEMA);
                world=Optional.of(new CurrentSuccessionLifecycle.WorldBefore(i32(w.get("date_raw")),i32(w.get("speed")),bool(w,"paused"),i32(w.get("local_player_id")),bool(w,"map_ready"),bool(w,"has_played_character"),character(i32(w.get("played_character_id"))),bool(w,"played_character_alive")));
            }
            if(!r.get("owner_witness").isNull()) {var w=StrictJson.object(r.get("owner_witness"),Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));owner=Optional.of(new OwnerWitness(decimal(w,"connection_generation",true),decimal(w,"ticket_sequence",true),decimal(w,"pump_epoch",true),NativeWire.integer(w.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));}
            if(!r.get("source").isNull()) {
                var s=StrictJson.object(r.get("source"),Set.of("schema","dead_character_id","continue_character_id","player_relation","dead_character_dead","continue_character_alive","handler_source_verified","named_root_bound","window_visible","window_enabled","default_button_admissible","default_native_route","stable_two_pass_verified"));eq(s,"schema",CurrentSuccessionLifecycle.SOURCE_SCHEMA);
                source=Optional.of(new CurrentSuccessionLifecycle.SourceBefore(character(i32(s.get("dead_character_id"))),character(i32(s.get("continue_character_id"))),relation(text(s,"player_relation")),bool(s,"dead_character_dead"),bool(s,"continue_character_alive"),bool(s,"handler_source_verified"),bool(s,"named_root_bound"),bool(s,"window_visible"),bool(s,"window_enabled"),bool(s,"default_button_admissible"),bool(s,"default_native_route"),bool(s,"stable_two_pass_verified")));
            }
            return new CurrentSuccessionLifecycleResult(action,status,bool(r,"source_available"),bool(r,"effect_attempted"),bool(r,"native_returned"),decimal(r,"provider_generation",false),decimal(r,"query_sequence",false),decimal(r,"claim_sequence",false),world,source,owner,r.get("unavailable_reason").isNull()?Optional.empty():Optional.of(text(r,"unavailable_reason")));
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid exact current lifecycle result",invalid);}
    }
    public static CurrentSuccessionLifecycleResult decodeOutcome(AckReceived original)throws IOException {
        try {
            var e=StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));eq(e,"type","command_result");eq(e,"request_id",original.requestId());NativeWire.integer(e.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            var token=original.originalResultToken().orElseThrow(()->new IOException("Original lifecycle result required"));if(!NativeWire.parse(token.bytes()).equals(e.get("result")))throw new IOException("Actual lifecycle token differs from original envelope");
            var frame=decode(new RawJson(token.bytes()));if(bool(e,"ok")!=original.nativeOk()||frame.nativeOk()!=original.nativeOk())throw new IOException("Actual lifecycle outer ok incoherent");return frame;
        }catch(IllegalArgumentException invalid){throw new IOException("Invalid actual lifecycle envelope",invalid);}
    }
    private static CurrentSuccessionLifecycle.Action action(String s)throws IOException {for(var a:CurrentSuccessionLifecycle.Action.values())if(a.wire().equals(s))return a;throw new IOException("Unknown fixed lifecycle action");}
    private static Status status(String s)throws IOException{for(var v:Status.values())if(v.wire().equals(s))return v;throw new IOException("Unknown exact lifecycle status");}
    private static CurrentSuccessionLifecycle.PlayerRelation relation(String s)throws IOException{for(var v:CurrentSuccessionLifecycle.PlayerRelation.values())if(v.name().toLowerCase(Locale.ROOT).equals(s))return v;throw new IOException("Unknown exact lifecycle player relation");}
    private static Optional<NativeCharacterId> character(int n){return n==-1?Optional.empty():Optional.of(new NativeCharacterId(n));}
    private static int i32(JsonNode n)throws IOException{return NativeWire.integer(n,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
    private static void u64(BigInteger n,boolean positive){Objects.requireNonNull(n);StrictJson.require(n.signum()>=0&&(!positive||n.signum()>0)&&n.compareTo(NativeWire.UINT64_MAX)<=0,"Exact uint64 lease or witness required");}
    private static BigInteger decimal(ObjectNode r,String k,boolean positive)throws IOException {String s=text(r,k);if(!s.matches("0|[1-9][0-9]{0,19}"))throw new IOException("Canonical unsigned decimal string required");var n=new BigInteger(s);u64(n,positive);return n;}
    private static String text(ObjectNode n,String k)throws IOException{return NativeWire.text(n.get(k));}
    private static void eq(ObjectNode n,String k,String v)throws IOException{if(!text(n,k).equals(v))throw new IOException("Exact lifecycle tuple/schema/action mismatch: "+k);}
    private static boolean bool(ObjectNode n,String k)throws IOException{var v=n.get(k);if(v==null||!v.isBoolean())throw new IOException("Actual lifecycle bool required: "+k);return v.booleanValue();}
}
