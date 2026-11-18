package org.xar.ck3.control.nativebridge.capabilities.registry;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Locale;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativePlayedResources;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Partial signed resource DATA, retaining original paused actor and wallet interval. */
public sealed interface ActorResourceLeafV2 permits ActorResourceLeafV2.Partial, ActorResourceLeafV2.Unavailable {
    String SCHEMA="ck3_1210_actor_resource_leaf_v2", STEP="query-actor-resource-leaf-v2";
    String CAPABILITY="game.query.actor-resource-leaf.v2";
    String ADAPTER="ck3-1.21.0-msvc-x64", BACKEND="ck3-1.21.0-native-headless-main-thread";
    String SOURCE="exact_1210_actor_foundation_personal_gold_interval";
    String RENOWN_UNKNOWN="dynasty_renown_main_owner_not_qualified";
    String TREASURY_UNKNOWN="government_treasury_main_owner_not_qualified";
    ExactCk3Build BUILD=ExactCk3Build.CK3_1210;
    Set<String> FIELDS=Set.of("step","schema","game_version","executable_sha256","adapter_id","steam_build_id",
            "executable_file_size","backend","status","read_only","resources_available","source_identity_verified",
            "application_main_observed","complete_snapshot","root_ready","formal_action_ready","actor_character_id",
            "source_kind","getter_sources","core_before","core_after","personal_gold_interval","resources","unavailable_reason");
    Set<String> PREFIX_FIELDS=Set.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character",
            "played_character_id","played_character_alive");
    boolean sourceIdentityVerified();
    boolean applicationMainObserved();
    ResourceRow prestige();
    ResourceRow piety();
    default Unknown renown(){return new Unknown(RENOWN_UNKNOWN);}
    default Unknown trueTreasury(){return new Unknown(TREASURY_UNKNOWN);}
    sealed interface ResourceRow permits Observed,Unknown { }
    record Observed(NativePlayedResources.Amount amount) implements ResourceRow {
        public Observed {Objects.requireNonNull(amount,"signed native amount");}
    }
    record Unknown(String reason) implements ResourceRow {
        public Unknown {requireReason(reason);}
    }
    /** These values describe PERSONAL wallet coherence; they are never treasury. */
    record PersonalGoldInterval(NativePlayedResources.Amount before,NativePlayedResources.Amount actorFoundation,
            NativePlayedResources.Amount after) {
        public PersonalGoldInterval {
            Objects.requireNonNull(before);Objects.requireNonNull(actorFoundation);Objects.requireNonNull(after);
            RegistryJson.require(before.equals(actorFoundation)&&actorFoundation.equals(after),"personal wallet interval changed");
        }
    }
    record Partial(CoreFrame.Prefix coreBefore,CoreFrame.Prefix coreAfter,PersonalGoldInterval goldInterval,
            Observed prestige,Observed piety) implements ActorResourceLeafV2 {
        public Partial {
            pausedActor(coreBefore);pausedActor(coreAfter);Objects.requireNonNull(goldInterval);
            Objects.requireNonNull(prestige);Objects.requireNonNull(piety);
            RegistryJson.require(coreBefore.equals(coreAfter),"resource Core interval changed");
        }
        @Override public boolean sourceIdentityVerified(){return true;}
        @Override public boolean applicationMainObserved(){return true;}
    }
    record Unavailable(boolean sourceIdentityVerified,boolean applicationMainObserved,Unknown prestige,
            Unknown piety,String reason) implements ActorResourceLeafV2 {
        public Unavailable {
            Objects.requireNonNull(prestige);Objects.requireNonNull(piety);requireReason(reason);
            RegistryJson.require(!applicationMainObserved||sourceIdentityVerified,"main owner cannot outlive source identity");
            RegistryJson.require(reason.equals(prestige.reason())&&reason.equals(piety.reason()),"atomic unavailable reasons differ");
        }
    }
    /** Consumption exit retains the actor/frame instead of exporting loose raw amounts. */
    record ObservedNonCash(int actorCharacterId,CoreFrame.Prefix core,
            NativePlayedResources.Amount prestige,NativePlayedResources.Amount piety) {
        public ObservedNonCash {
            pausedActor(core);Objects.requireNonNull(prestige);Objects.requireNonNull(piety);
            RegistryJson.require(actorCharacterId==core.playedCharacterId(),"resource consumer actor drift");
        }
    }
    default Optional<ObservedNonCash> observedNonCash(){
        return this instanceof Partial p ? Optional.of(new ObservedNonCash(p.coreBefore().playedCharacterId(),
                p.coreBefore(),p.prestige().amount(),p.piety().amount())) : Optional.empty();
    }
    private static void requireReason(String reason){RegistryJson.require(reason!=null&&!reason.isEmpty(),"original unavailable reason required");}
    private static void pausedActor(CoreFrame.Prefix p){
        Objects.requireNonNull(p);RegistryJson.require(p.paused()&&p.mapReady()&&p.localPlayerId()>=0&&
                p.hasPlayedCharacter()&&p.playedCharacterAlive()&&p.playedCharacterId()!=-1,"paused living resource actor required");
    }
    static ActorResourceLeafV2 decode(RawJson originalResult){
        ObjectNode r=RegistryJson.object(originalResult);RegistryJson.keys(r,FIELDS);
        RegistryJson.require(SCHEMA.equals(RegistryJson.text(r.get("schema")))&&STEP.equals(RegistryJson.text(r.get("step")))&&
                BUILD.matches(RegistryJson.text(r.get("game_version")),RegistryJson.text(r.get("executable_sha256")))&&
                ADAPTER.equals(RegistryJson.text(r.get("adapter_id")))&&BACKEND.equals(RegistryJson.text(r.get("backend")))&&
                "26622941".equals(RegistryJson.text(r.get("steam_build_id"))),"resource exact image/step/source drift");
        RegistryJson.integer(r.get("executable_file_size"),BigInteger.valueOf(114756216),BigInteger.valueOf(114756216));
        RegistryJson.require(RegistryJson.bool(r.get("read_only"))&&!RegistryJson.bool(r.get("complete_snapshot"))&&
                !RegistryJson.bool(r.get("root_ready"))&&!RegistryJson.bool(r.get("formal_action_ready")),"resource DATA role expansion");
        RegistryJson.require(SOURCE.equals(RegistryJson.text(r.get("source_kind"))),"resource source kind drift");
        ObjectNode getters=RegistryJson.object(r.get("getter_sources"));RegistryJson.keys(getters,Set.of("prestige","piety","personal_gold"));
        RegistryJson.require("0x2DA2810".equals(RegistryJson.text(getters.get("prestige")))&&
                "0x2DA27E0".equals(RegistryJson.text(getters.get("piety")))&&
                "0xD9E760".equals(RegistryJson.text(getters.get("personal_gold"))),"resource getter/module caller drift");
        boolean available=RegistryJson.bool(r.get("resources_available"));
        boolean image=RegistryJson.bool(r.get("source_identity_verified"));
        boolean main=RegistryJson.bool(r.get("application_main_observed"));
        ObjectNode rows=RegistryJson.object(r.get("resources"));RegistryJson.keys(rows,Set.of("prestige","piety","renown","true_treasury"));
        ResourceRow prestige=row(rows.get("prestige")),piety=row(rows.get("piety"));
        RegistryJson.require(row(rows.get("renown")).equals(new Unknown(RENOWN_UNKNOWN))&&
                row(rows.get("true_treasury")).equals(new Unknown(TREASURY_UNKNOWN)),"unqualified renown/treasury became observed");
        if(!available){
            RegistryJson.require("unavailable".equals(RegistryJson.text(r.get("status")))&&
                    prestige instanceof Unknown&&piety instanceof Unknown,"unavailable resource group drift");
            for(String key:Set.of("core_before","core_after","actor_character_id","personal_gold_interval"))
                RegistryJson.require(r.get(key).isNull(),"unavailable source must retain null: "+key);
            return new Unavailable(image,main,(Unknown)prestige,(Unknown)piety,RegistryJson.text(r.get("unavailable_reason")));
        }
        RegistryJson.require(image&&main&&"partial".equals(RegistryJson.text(r.get("status")))&&
                r.get("unavailable_reason").isNull()&&prestige instanceof Observed&&piety instanceof Observed,"partial resource evidence missing");
        CoreFrame.Prefix before=prefix(r.get("core_before")),after=prefix(r.get("core_after"));
        RegistryJson.require(RegistryJson.int32(r.get("actor_character_id"))==before.playedCharacterId(),"resource source actor drift");
        ObjectNode interval=RegistryJson.object(r.get("personal_gold_interval"));RegistryJson.keys(interval,Set.of("before","actor_foundation","after"));
        return new Partial(before,after,new PersonalGoldInterval(amount(interval.get("before")),amount(interval.get("actor_foundation")),
                amount(interval.get("after"))),(Observed)prestige,(Observed)piety);
    }
    /** Pure archived original packet decoder; no endpoint/session/ACK or live claim is manufactured. */
    static ActorResourceLeafV2 decodePacket(RawJson original,String expectedRequestId)throws IOException {
        Objects.requireNonNull(original);Objects.requireNonNull(expectedRequestId);
        ObjectNode envelope=RegistryJson.object(original);
        RegistryJson.keys(envelope,Set.of("type","protocol_version","request_id","ok","result"));
        RegistryJson.require("command_result".equals(RegistryJson.text(envelope.get("type")))&&
                RegistryJson.integer(envelope.get("protocol_version"),BigInteger.ONE,BigInteger.ONE).equals(BigInteger.ONE)&&
                expectedRequestId.equals(RegistryJson.text(envelope.get("request_id")))&&RegistryJson.bool(envelope.get("ok")),
                "resource original command envelope/request/status differs");
        var decoded=NativeWire.decode(NativeWire.packet(original.bytes()));
        RegistryJson.require(decoded instanceof NativeWire.CommandResult,"original resource command_result required");
        var result=(NativeWire.CommandResult)decoded;
        RegistryJson.require(result.result().presence()==NativeWire.Presence.VALUE,"original resource result missing/null");
        return decode(new RawJson(result.result().token().orElseThrow().value()));
    }
    /** Archived original outcome only; live occurrence requires the receiver private issuer/custody wrapper. */
    static ActorResourceLeafV2 decodeOutcome(NativeActionPort.DispatchOutcome original)throws IOException {
        Objects.requireNonNull(original);
        if(original instanceof NativeActionPort.RejectedBeforeDispatch rejected)
            throw new IOException("actual actor resource leaf v2 source unavailable before dispatch: "+rejected.proof().reason());
        if(original instanceof NativeActionPort.Unknown unknown)
            throw new IOException("actual actor resource leaf v2 result unknown; original request is never replayed: "+unknown.reason());
        var ack=(NativeActionPort.AckReceived)original;
        try {
            var outbound=ack.outbound().orElseThrow(()->new IOException("actor resource leaf v2 original outbound missing"));
            var request=NativeWire.decodeExecuteRequest(outbound.originalPacket());
            RegistryJson.require(outbound.requestId().equals(ack.requestId())&&request.requestId().equals(ack.requestId())
                    &&STEP.equals(request.step())&&request.expectedRevision().equals(Optional.of(BigInteger.ZERO))
                    &&request.expectedSnapshotRevision().isEmpty(),"actor resource leaf v2 request identity/step/revision differs");
            RegistryJson.keys(RegistryJson.object(new RawJson(request.normalizedAdditionalFields().value())),Set.of());
            var decoded=NativeWire.decode(ack.originalPacket());
            RegistryJson.require(decoded instanceof NativeWire.CommandResult,"actor resource leaf v2 original response is not command_result");
            var result=(NativeWire.CommandResult)decoded;
            RegistryJson.require(result.requestId().equals(ack.requestId())&&result.nativeOk()==ack.nativeOk()
                    &&Arrays.equals(result.payload().value(),ack.originalFrame().bytes()),"actor resource leaf v2 retained envelope differs");
            RegistryJson.require(result.result().presence()==NativeWire.Presence.VALUE&&ack.originalResultToken().isPresent()
                    &&Arrays.equals(result.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes()),
                    "actor resource leaf v2 retained result differs from the original response");
            return decodePacket(ack.originalFrame(),ack.requestId());
        }catch(IllegalArgumentException invalid){throw new IOException("actor resource leaf v2 original profile or partial result is invalid",invalid);}
    }
    private static ResourceRow row(JsonNode input){
        ObjectNode row=RegistryJson.object(input);RegistryJson.keys(row,Set.of("status","amount","unavailable_reason"));
        return switch(RegistryJson.text(row.get("status"))){
            case "available" -> {
                RegistryJson.require(row.get("unavailable_reason").isNull(),"observed resource retains null reason");
                yield new Observed(amount(row.get("amount")));
            }
            case "unavailable" -> {
                RegistryJson.require(row.get("amount").isNull(),"unknown resource retains explicit null amount");
                yield new Unknown(RegistryJson.text(row.get("unavailable_reason")));
            }
            default -> throw new IllegalArgumentException("resource row status differs");
        };
    }
    private static NativePlayedResources.Amount amount(JsonNode input){
        var value=NativePlayedResources.decode(input);
        RegistryJson.require(value instanceof NativePlayedResources.Amount,"observed signed Q100000 amount required");
        return (NativePlayedResources.Amount)value;
    }
    private static CoreFrame.Prefix prefix(JsonNode input){
        ObjectNode p=RegistryJson.object(input);RegistryJson.keys(p,PREFIX_FIELDS);
        return new CoreFrame.Prefix(RegistryJson.int32(p.get("date_raw")),RegistryJson.int32(p.get("speed")),
                RegistryJson.bool(p.get("paused")),RegistryJson.int32(p.get("local_player_id")),RegistryJson.bool(p.get("map_ready")),
                RegistryJson.bool(p.get("has_played_character")),RegistryJson.int32(p.get("played_character_id")),
                RegistryJson.bool(p.get("played_character_alive")));
    }
    static RawJson encode(ActorResourceLeafV2 value){
        Objects.requireNonNull(value);ObjectNode r=StrictJson.object();
        r.put("step",STEP).put("schema",SCHEMA).put("game_version",BUILD.version()).put("executable_sha256",BUILD.executableSha256().toUpperCase(Locale.ROOT))
                .put("adapter_id",ADAPTER).put("steam_build_id","26622941").put("executable_file_size",114756216).put("backend",BACKEND);
        boolean ready=value instanceof Partial;r.put("status",ready?"partial":"unavailable").put("read_only",true)
                .put("resources_available",ready).put("source_identity_verified",value.sourceIdentityVerified())
                .put("application_main_observed",value.applicationMainObserved()).put("complete_snapshot",false)
                .put("root_ready",false).put("formal_action_ready",false).put("source_kind",SOURCE);
        r.putObject("getter_sources").put("prestige","0x2DA2810").put("piety","0x2DA27E0").put("personal_gold","0xD9E760");
        if(value instanceof Partial p){
            r.put("actor_character_id",p.coreBefore().playedCharacterId());r.set("core_before",prefix(p.coreBefore()));r.set("core_after",prefix(p.coreAfter()));
            ObjectNode interval=r.putObject("personal_gold_interval");
            interval.set("before",NativePlayedResources.encode(p.goldInterval().before()));
            interval.set("actor_foundation",NativePlayedResources.encode(p.goldInterval().actorFoundation()));
            interval.set("after",NativePlayedResources.encode(p.goldInterval().after()));r.putNull("unavailable_reason");
        }else{
            r.putNull("actor_character_id").putNull("core_before").putNull("core_after").putNull("personal_gold_interval");
            r.put("unavailable_reason",((Unavailable)value).reason());
        }
        ObjectNode rows=r.putObject("resources");rows.set("prestige",row(value.prestige()));rows.set("piety",row(value.piety()));
        rows.set("renown",row(value.renown()));rows.set("true_treasury",row(value.trueTreasury()));return RegistryJson.encode(r);
    }
    private static ObjectNode row(ResourceRow value){
        ObjectNode row=StrictJson.object();
        if(value instanceof Observed observed){row.put("status","available");row.set("amount",NativePlayedResources.encode(observed.amount()));row.putNull("unavailable_reason");}
        else {row.put("status","unavailable").putNull("amount").put("unavailable_reason",((Unknown)value).reason());}
        return row;
    }
    private static ObjectNode prefix(CoreFrame.Prefix p){
        return StrictJson.object().put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused())
                .put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter())
                .put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());
    }
}
