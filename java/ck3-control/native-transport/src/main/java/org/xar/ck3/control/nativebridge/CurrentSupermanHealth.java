package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Fixed health fixture DATA. A private same-receiver query is required for the known option. */
public final class CurrentSupermanHealth {
    public static final String SCHEMA="ck3.superman_health.current267_request.v1";
    public static final String RESULT_SCHEMA="ck3.superman_health.current267_result.v1";
    public static final String SOURCE_SCHEMA="ck3.superman_health.current267_source.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-application-main-superman-health";
    public enum Action {
        QUERY_HEALTH("query_health","query-superman-health-current-v1","game.query.current-superman-health.v1"),
        CHOOSE_KNOWN("choose_known","select-superman-health-known-option-current-v1","game.command.select-current-superman-health-known-option.v1");
        private final String wire,step,capability;
        Action(String wire,String step,String capability){this.wire=wire;this.step=step;this.capability=capability;}
        public String wire(){return wire;}public String step(){return step;}public String capability(){return capability;}
        public static Action parse(String value)throws IOException{for(var a:values())if(a.wire.equals(value))return a;throw new IOException("Unknown fixed Superman health action");}
    }
    public enum Phase {
        BASELINE("baseline","sxat.2","sxat_health_begin"),COMPLETED("completed","sxat.4","sxat_health_done_close");
        private final String wire,eventKey,optionKey;
        Phase(String wire,String eventKey,String optionKey){this.wire=wire;this.eventKey=eventKey;this.optionKey=optionKey;}
        public String wire(){return wire;}public String eventKey(){return eventKey;}public String optionKey(){return optionKey;}
        public static Phase parse(String value)throws IOException{for(var p:values())if(p.wire.equals(value))return p;throw new IOException("Unknown fixed Superman health phase");}
    }
    private CurrentSupermanHealth() { }
    public static NativeRequest request(CoreFrame.Partial actual,Action action,BigInteger provider,BigInteger query,Phase phase){
        Objects.requireNonNull(actual);Objects.requireNonNull(action);Objects.requireNonNull(phase);
        CurrentLetter.unsigned(provider,false);CurrentLetter.unsigned(query,false);
        StrictJson.require(actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313,"Exact current267 Core required");
        CurrentLetter.requirePrefix(actual.prefix());
        StrictJson.require(action==Action.QUERY_HEALTH?provider.signum()==0&&query.signum()==0:provider.signum()>0&&query.signum()>0,"Health query/choice lease roles differ");
        var build=actual.build();var claim=StrictJson.object().put("schema",SCHEMA).put("game_version",build.version())
                .put("executable_sha256",build.executableSha256()).put("adapter_id",build.coreFrameAdapterId()).put("backend",BACKEND)
                .put("action",action.wire()).put("provider_generation",provider.toString()).put("query_sequence",query.toString()).put("phase",phase.wire());
        var p=actual.prefix();claim.putObject("expected_core").put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused())
                .put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter())
                .put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());
        var fields=StrictJson.object();fields.set("superman_health",claim);fields.set("arguments",StrictJson.object());
        return new NativeRequest(action.step(),action.capability(),new RawJson(StrictJson.canonical(fields)));
    }
}
