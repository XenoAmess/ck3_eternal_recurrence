package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Exact readonly target material. Native evaluator availability is not ordinary CanDeclare, cost or a war receipt. */
public record CurrentDjcTargetWarQueryResult(Status status,boolean scratchCleanupKnown,Optional<NativeCharacterId> target,
        BigInteger providerGeneration,BigInteger querySequence,Optional<CoreFrame.Prefix> coreBefore,
        Optional<OwnerWitness> ownerWitness,Optional<List<CasusBelli>> casusBelli,Optional<String> unavailableReason) {
    public enum Status {
        UNAVAILABLE("unavailable"),EXPIRED("expired"),STALE_CORE("stale_core"),AVAILABLE("available"),INDETERMINATE("indeterminate");
        private final String wire;Status(String s){wire=s;}public String wire(){return wire;}
        static Status parse(String s)throws IOException {for(var v:values())if(v.wire.equals(s))return v;throw new IOException("Unknown current DJC target query status");}
    }
    public enum CasusBelliKey {
        DUCHY("duchy_de_jure_greatwar"),KINGDOM("kingdom_de_jure_greatwar"),EMPIRE("empire_de_jure_greatwar");
        private final String wire;CasusBelliKey(String s){wire=s;}public String wire(){return wire;}
        static CasusBelliKey parse(String s)throws IOException {for(var v:values())if(v.wire.equals(s))return v;throw new IOException("Unknown fixed current DJC CB key");}
    }
    public record OwnerWitness(BigInteger connectionGeneration,BigInteger ticketSequence,BigInteger pumpEpoch,long threadId) {
        public OwnerWitness {unsigned(connectionGeneration,true);unsigned(ticketSequence,true);unsigned(pumpEpoch,true);
            StrictJson.require(threadId>0&&threadId<=0xffff_ffffL,"Positive exact uint32 owner thread required");}
    }
    public record Choice(int casusBelliIndex,int configurationIndex,Optional<NativeCharacterId> claimant,
            List<Integer> targetTitleIds,List<Integer> extraConfigurationIds) {
        public Choice {
            Objects.requireNonNull(claimant);targetTitleIds=List.copyOf(targetTitleIds);extraConfigurationIds=List.copyOf(extraConfigurationIds);
            StrictJson.require(casusBelliIndex>=0&&configurationIndex>=-1&&targetTitleIds.size()<=10000&&extraConfigurationIds.size()<=10000,"Exact bounded native choice indexes/vectors required");
            StrictJson.require(targetTitleIds.stream().noneMatch(n->n==-1),"Target title -1 is absent; do not reinterpret unsigned bits");
            // These are ordered native int32 vectors. Duplicates and every signed extra-ID value retain their actual domain.
        }
    }
    public record CasusBelli(CasusBelliKey key,boolean definitionPresent,boolean enabled,boolean nativeEvaluationReturned,
            boolean selectionMaterializationAvailable,Optional<Boolean> nativeAvailable,List<Choice> choices) {
        public CasusBelli {
            Objects.requireNonNull(key);Objects.requireNonNull(nativeAvailable);choices=List.copyOf(choices);
            StrictJson.require(definitionPresent,"Actual fixed CB definition required in available query");
            StrictJson.require(enabled?nativeEvaluationReturned&&nativeAvailable.isPresent():!nativeEvaluationReturned&&nativeAvailable.isEmpty()&&choices.isEmpty(),"CB enabled/evaluator/null roles disagree");
            StrictJson.require(nativeAvailable.orElse(false)||choices.isEmpty(),"Native unavailable CB cannot contain choices");
        }
    }
    public CurrentDjcTargetWarQueryResult {
        Objects.requireNonNull(status);Objects.requireNonNull(target);unsigned(providerGeneration,false);unsigned(querySequence,false);
        Objects.requireNonNull(coreBefore);Objects.requireNonNull(ownerWitness);Objects.requireNonNull(casusBelli);Objects.requireNonNull(unavailableReason);
        coreBefore.ifPresent(CurrentDjcTargetWarQuery::requirePrefix);
        StrictJson.require(coreBefore.isPresent()==ownerWitness.isPresent(),"Actual Core/owner must be present or null together");
        casusBelli=casusBelli.map(List::copyOf);
        if(status==Status.AVAILABLE) {
            StrictJson.require(scratchCleanupKnown&&target.isPresent()&&coreBefore.isPresent()&&ownerWitness.isPresent()
                    &&providerGeneration.signum()>0&&querySequence.signum()>0&&casusBelli.isPresent()&&unavailableReason.isEmpty(),"Available query requires actual Core/owner/source cleanup and positive private lease");
            StrictJson.require(target.orElseThrow().value()!=coreBefore.orElseThrow().playedCharacterId(),"Actual target cannot be self");
            var rows=casusBelli.orElseThrow();StrictJson.require(rows.size()==3,"All three current production CBs required");
            for(int i=0;i<3;i++)StrictJson.require(rows.get(i).key()==CasusBelliKey.values()[i],"Actual fixed CB ordering differs");
        } else StrictJson.require(casusBelli.isEmpty()&&unavailableReason.filter(s->!s.isEmpty()).isPresent(),"Unavailable query preserves explicit null CBs and original reason");
    }
    public boolean available(){return status==Status.AVAILABLE;}
    public static CurrentDjcTargetWarQueryResult decode(RawJson raw)throws IOException {
        try {
            ObjectNode r=StrictJson.object(NativeWire.parse(raw.bytes()),Set.of("schema","game_version","executable_sha256","adapter_id","backend","step","status","available","scratch_cleanup_known","target_character_id","provider_generation","query_sequence","core_before","owner_witness","casus_belli","addresses_redacted","read_only","ordinary_can_declare_war","total_debit","submission_available","war_submission_attempted","war_submitted","war_id","unavailable_reason"));
            var b=ExactCk3Build.CK3_121003_STEAM_26785313;require(r,"schema",CurrentDjcTargetWarQuery.RESULT_SCHEMA);require(r,"game_version",b.version());require(r,"executable_sha256",b.executableSha256().toUpperCase(Locale.ROOT));require(r,"adapter_id",b.coreFrameAdapterId());require(r,"backend",CurrentDjcTargetWarQuery.BACKEND);require(r,"step",CurrentDjcTargetWarQuery.STEP);
            if(!bool(r,"addresses_redacted")||!bool(r,"read_only")||bool(r,"submission_available")||bool(r,"war_submission_attempted")||bool(r,"war_submitted")
                    ||!r.get("ordinary_can_declare_war").isNull()||!r.get("total_debit").isNull()||!r.get("war_id").isNull())throw new IOException("Readonly evaluator cannot grant ordinary CanDeclare/debit/submit/war");
            var status=Status.parse(NativeWire.text(r.get("status")));if(bool(r,"available")!=(status==Status.AVAILABLE))throw new IOException("Actual available/status mismatch");
            Optional<CoreFrame.Prefix> core=Optional.empty();Optional<OwnerWitness> owner=Optional.empty();
            if(!r.get("core_before").isNull()) {var c=StrictJson.object(r.get("core_before"),Set.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"));core=Optional.of(new CoreFrame.Prefix(i32(c.get("date_raw")),i32(c.get("speed")),bool(c,"paused"),i32(c.get("local_player_id")),bool(c,"map_ready"),bool(c,"has_played_character"),i32(c.get("played_character_id")),bool(c,"played_character_alive")));}
            if(!r.get("owner_witness").isNull()) {var w=StrictJson.object(r.get("owner_witness"),Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));owner=Optional.of(new OwnerWitness(decimal(w,"connection_generation",true),decimal(w,"ticket_sequence",true),decimal(w,"pump_epoch",true),NativeWire.integer(w.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));}
            Optional<List<CasusBelli>> cbs=Optional.empty();
            if(!r.get("casus_belli").isNull()) {
                if(!r.get("casus_belli").isArray()||r.get("casus_belli").size()!=3)throw new IOException("Three actual CB rows required");var list=new ArrayList<CasusBelli>();
                for(var cb:r.get("casus_belli")) {
                    var c=StrictJson.object(cb,Set.of("key","definition_present","enabled","native_evaluation_returned","selection_materialization_available","native_available","choices"));
                    Optional<Boolean> na=c.get("native_available").isNull()?Optional.empty():Optional.of(bool(c,"native_available"));if(!c.get("choices").isArray())throw new IOException("Actual ordered choice array required");var choices=new ArrayList<Choice>();
                    for(var value:c.get("choices")) {var v=StrictJson.object(value,Set.of("casus_belli_index","configuration_index","claimant_character_id","target_title_ids","extra_configuration_ids"));choices.add(new Choice(i32(v.get("casus_belli_index")),i32(v.get("configuration_index")),character(i32(v.get("claimant_character_id"))),ids(v.get("target_title_ids")),ids(v.get("extra_configuration_ids"))));}
                    list.add(new CasusBelli(CasusBelliKey.parse(NativeWire.text(c.get("key"))),bool(c,"definition_present"),bool(c,"enabled"),bool(c,"native_evaluation_returned"),bool(c,"selection_materialization_available"),na,choices));
                }cbs=Optional.of(list);
            }
            return new CurrentDjcTargetWarQueryResult(status,bool(r,"scratch_cleanup_known"),character(i32(r.get("target_character_id"))),decimal(r,"provider_generation",false),decimal(r,"query_sequence",false),core,owner,cbs,r.get("unavailable_reason").isNull()?Optional.empty():Optional.of(NativeWire.text(r.get("unavailable_reason"))));
        }catch(IllegalArgumentException|ArithmeticException bad){throw new IOException("Invalid exact current DJC query result",bad);}
    }
    public static CurrentDjcTargetWarQueryResult decodeOutcome(AckReceived original)throws IOException {
        try {
            var e=StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));require(e,"type","command_result");require(e,"request_id",original.requestId());NativeWire.integer(e.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);if(bool(e,"ok")!=original.nativeOk())throw new IOException("Actual DJC envelope ok mismatch");
            var token=original.originalResultToken().orElseThrow(()->new IOException("Original DJC result token required"));if(!NativeWire.parse(token.bytes()).equals(e.get("result")))throw new IOException("DJC actual result token differs from envelope");var result=decode(new RawJson(token.bytes()));if(result.available()!=original.nativeOk())throw new IOException("Outer DJC ok differs from actual available");return result;
        }catch(IllegalArgumentException bad){throw new IOException("Invalid original DJC result envelope",bad);}
    }
    public RawJson encode() {
        var b=ExactCk3Build.CK3_121003_STEAM_26785313;var r=StrictJson.object().put("schema",CurrentDjcTargetWarQuery.RESULT_SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256().toUpperCase(Locale.ROOT)).put("adapter_id",b.coreFrameAdapterId()).put("backend",CurrentDjcTargetWarQuery.BACKEND).put("step",CurrentDjcTargetWarQuery.STEP).put("status",status.wire()).put("available",available()).put("scratch_cleanup_known",scratchCleanupKnown).put("target_character_id",target.map(NativeCharacterId::value).orElse(-1)).put("provider_generation",providerGeneration.toString()).put("query_sequence",querySequence.toString());
        if(coreBefore.isPresent()){var p=coreBefore.orElseThrow();r.putObject("core_before").put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused()).put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter()).put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());var w=ownerWitness.orElseThrow();r.putObject("owner_witness").put("connection_generation",w.connectionGeneration().toString()).put("ticket_sequence",w.ticketSequence().toString()).put("pump_epoch",w.pumpEpoch().toString()).put("thread_id",w.threadId());}else{r.putNull("core_before");r.putNull("owner_witness");}
        if(casusBelli.isPresent()){var a=r.putArray("casus_belli");for(var cb:casusBelli.orElseThrow()){var c=a.addObject().put("key",cb.key().wire()).put("definition_present",cb.definitionPresent()).put("enabled",cb.enabled()).put("native_evaluation_returned",cb.nativeEvaluationReturned()).put("selection_materialization_available",cb.selectionMaterializationAvailable());if(cb.nativeAvailable().isPresent())c.put("native_available",cb.nativeAvailable().orElseThrow());else c.putNull("native_available");var q=c.putArray("choices");for(var v:cb.choices()){var n=q.addObject().put("casus_belli_index",v.casusBelliIndex()).put("configuration_index",v.configurationIndex()).put("claimant_character_id",v.claimant().map(NativeCharacterId::value).orElse(-1));var ts=n.putArray("target_title_ids");v.targetTitleIds().forEach(ts::add);var xs=n.putArray("extra_configuration_ids");v.extraConfigurationIds().forEach(xs::add);}}}else r.putNull("casus_belli");
        r.put("addresses_redacted",true).put("read_only",true).putNull("ordinary_can_declare_war").putNull("total_debit").put("submission_available",false).put("war_submission_attempted",false).put("war_submitted",false).putNull("war_id");if(unavailableReason.isPresent())r.put("unavailable_reason",unavailableReason.orElseThrow());else r.putNull("unavailable_reason");return new RawJson(StrictJson.canonical(r));
    }
    private static Optional<NativeCharacterId> character(int n){return n==-1?Optional.empty():Optional.of(new NativeCharacterId(n));}
    private static List<Integer> ids(JsonNode n)throws IOException {if(!n.isArray()||n.size()>10000)throw new IOException("Bounded ordered native int32 vector required");var a=new ArrayList<Integer>();for(var v:n)a.add(i32(v));return List.copyOf(a);}
    private static int i32(JsonNode n)throws IOException{return NativeWire.integer(n,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
    private static void unsigned(BigInteger n,boolean positive){Objects.requireNonNull(n);StrictJson.require(n.signum()>=0&&(!positive||n.signum()>0)&&n.compareTo(NativeWire.UINT64_MAX)<=0,"Exact unsigned uint64 required");}
    private static BigInteger decimal(ObjectNode r,String k,boolean positive)throws IOException {String s=NativeWire.text(r.get(k));if(!s.matches("0|[1-9][0-9]{0,19}"))throw new IOException("Canonical uint64 string required: "+k);BigInteger n=new BigInteger(s);try{unsigned(n,positive);}catch(IllegalArgumentException bad){throw new IOException("Uint64 range mismatch: "+k,bad);}return n;}
    private static void require(ObjectNode r,String k,String expected)throws IOException{if(!NativeWire.text(r.get(k)).equals(expected))throw new IOException("Exact current DJC source mismatch: "+k);}
    private static boolean bool(ObjectNode r,String k)throws IOException{var n=r.get(k);if(n==null||!n.isBoolean())throw new IOException("Actual DJC bool required: "+k);return n.booleanValue();}
}
