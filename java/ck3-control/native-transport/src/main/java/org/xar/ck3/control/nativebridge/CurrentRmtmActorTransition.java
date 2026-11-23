package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** RMTM DATA only. Transport owns actual Core custody, leases, original IDs/deadlines and once fencing. */
public final class CurrentRmtmActorTransition {
    public static final String SCHEMA="ck3.rmtm_actor_transition.current267_request.v1";
    public static final String RESULT_SCHEMA="ck3.rmtm_actor_transition.current267_result.v1";
    public static final String SOURCE_SCHEMA="ck3.rmtm_actor_transition.current267_source.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-application-main-rmtm-actor-transition";
    public static final String CLAIM_KEY="rmtm_actor_transition";
    public enum Action {
        QUERY_ROLE("query_role","query-current-rmtm-role-v1","game.query.current-rmtm-actor-transition.v1"),
        ADVANCE_DAY("advance_day","advance-current-rmtm-one-day-v1","game.command.current-rmtm-one-day.v1"),
        QUERY_OPERATION("query_operation","query-current-rmtm-one-day-v1","game.query.current-rmtm-actor-transition.v1"),
        CONFIRM_EPOCH("confirm_epoch","confirm-current-rmtm-actor-epoch-v1","game.command.confirm-current-rmtm-actor-epoch.v1");
        private final String wire,step,capability;
        Action(String wire,String step,String capability){this.wire=wire;this.step=step;this.capability=capability;}
        public String wire(){return wire;}
        public String step(){return step;}
        public String capability(){return capability;}
        public static Action parse(String value)throws IOException{
            for(var action:values())if(action.wire.equals(value))return action;
            throw new IOException("Unknown current RMTM transition action");
        }
    }
    private CurrentRmtmActorTransition() { }

    /** Produces only arguments + the eleven-field claim. Outer ID/step/deadline are added by Transport. */
    public static NativeRequest request(CoreFrame.Partial actual,Action action,String operationId,
            BigInteger provider,BigInteger query,BigInteger actorEpoch) {
        Objects.requireNonNull(actual);Objects.requireNonNull(action);Objects.requireNonNull(operationId);
        unsigned(provider,false);unsigned(query,false);epoch(actorEpoch);
        StrictJson.require(actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313,"Exact current267 Core required");
        requireCore(actual.prefix());
        if(action==Action.QUERY_ROLE) {
            StrictJson.require(operationId.isEmpty()&&provider.signum()==0&&query.signum()==0&&actorEpoch.signum()==0,
                    "Role query has no operation/lease/caller epoch");
        } else {
            identifier(operationId);
            StrictJson.require(provider.signum()>0&&query.signum()>0,"Actual private role/original operation lease required");
            StrictJson.require(actorEpoch.compareTo(BigInteger.ONE)<=0,"Only RMTM frontier0 or1 is valid");
            if(action==Action.CONFIRM_EPOCH)StrictJson.require(actorEpoch.signum()==0,"Pending epoch confirmation starts at epoch0");
        }
        var build=actual.build();
        var claim=StrictJson.object().put("schema",SCHEMA).put("game_version",build.version())
                .put("executable_sha256",build.executableSha256()).put("adapter_id",build.coreFrameAdapterId())
                .put("backend",BACKEND).put("action",action.wire()).put("operation_id",operationId)
                .put("provider_generation",provider.toString()).put("query_sequence",query.toString())
                .put("actor_epoch",actorEpoch.toString());
        claim.set("expected_core",core(actual.prefix()));
        var fields=StrictJson.object();fields.set("arguments",StrictJson.object());fields.set(CLAIM_KEY,claim);
        return new NativeRequest(action.step(),action.capability(),new RawJson(StrictJson.canonical(fields)));
    }

    public static final int MAXIMUM_NATURAL_DAYS=14;

    static void unsigned(BigInteger value,boolean positive){
        Objects.requireNonNull(value);
        StrictJson.require(value.signum()>=0&&(!positive||value.signum()>0)&&value.compareTo(NativeWire.UINT64_MAX)<=0,"Canonical uint64 required");
    }
    static void epoch(BigInteger value){unsigned(value,false);StrictJson.require(value.compareTo(BigInteger.ONE)<=0,"RMTM epoch must be0 or1");}
    static void identifier(String value){Objects.requireNonNull(value);StrictJson.require(value.matches("[A-Za-z0-9_.-]{1,96}"),"Exact ASCII operation/request ID required");}
    static void requireCore(CoreFrame.Prefix p){
        Objects.requireNonNull(p);
        StrictJson.require(p.speed()>=1&&p.speed()<=5&&p.paused()&&p.localPlayerId()>=0&&p.mapReady()
                &&p.hasPlayedCharacter()&&p.playedCharacterId()!=-1&&p.playedCharacterAlive(),"Actual paused living map Core required");
    }
    static int i32(JsonNode node)throws IOException{
        return NativeWire.integer(node,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();
    }
    static long u32(JsonNode node)throws IOException{return NativeWire.integer(node,BigInteger.ZERO,BigInteger.valueOf(0xffff_ffffL)).longValueExact();}
    static BigInteger decimal(ObjectNode object,String key)throws IOException{
        String text=NativeWire.text(object.get(key));
        if(!text.matches("0|[1-9][0-9]{0,19}"))throw new IOException("Canonical uint64 string required: "+key);
        var value=new BigInteger(text);unsigned(value,false);return value;
    }
    static BigInteger deadline(ObjectNode object,String key)throws IOException{
        return NativeWire.integer(object.get(key),BigInteger.ONE,NativeWire.UINT64_MAX);
    }
    static boolean bool(ObjectNode object,String key)throws IOException{
        var value=object.get(key);if(value==null||!value.isBoolean())throw new IOException("Actual RMTM boolean required: "+key);return value.booleanValue();
    }
    static CoreFrame.Prefix readCore(JsonNode node)throws IOException{
        var p=StrictJson.object(node,Set.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"));
        var result=new CoreFrame.Prefix(i32(p.get("date_raw")),i32(p.get("speed")),bool(p,"paused"),i32(p.get("local_player_id")),
                bool(p,"map_ready"),bool(p,"has_played_character"),i32(p.get("played_character_id")),bool(p,"played_character_alive"));
        requireCore(result);return result;
    }
    static ObjectNode core(CoreFrame.Prefix p){
        requireCore(p);return StrictJson.object().put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused())
                .put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter())
                .put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());
    }
    static int days(JsonNode node)throws IOException{return NativeWire.integer(node,BigInteger.ZERO,BigInteger.valueOf(14)).intValueExact();}
    static void requireDays(int value){StrictJson.require(value>=0&&value<=14,"RMTM original maximum14 natural days");}
    static void identity(ObjectNode r,String key,String expected)throws IOException{
        if(!NativeWire.text(r.get(key)).equals(expected))throw new IOException("Exact RMTM identity mismatch: "+key);
    }
}
