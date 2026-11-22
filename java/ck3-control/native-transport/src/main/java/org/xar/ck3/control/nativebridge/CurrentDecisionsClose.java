package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** No-selector fixed decisions-list close. Public DATA never supplies the private callback/shortcut witness. */
public final class CurrentDecisionsClose {
    public static final String SCHEMA="ck3.decisions_close.current267_request.v1";
    public static final String RESULT_SCHEMA="ck3.decisions_close.current267_result.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-application-main-decisions-close";
    public enum Action {
        QUERY_CLOSE("query_close","query-current-decisions-close-v1","game.query.current-decisions-close.v1"),
        CLOSE_LIST("close_list","close-current-decisions-list-v1","game.command.close-current-decisions-list.v1");
        private final String wire,step,capability;
        Action(String wire,String step,String capability){this.wire=wire;this.step=step;this.capability=capability;}
        public String wire(){return wire;}public String step(){return step;}public String capability(){return capability;}
        public static Action parse(String value)throws IOException{for(var item:values())if(item.wire.equals(value))return item;throw new IOException("Unknown fixed decisions-close action");}
    }
    private CurrentDecisionsClose() { }
    public static NativeRequest request(CoreFrame.Partial actual,Action action,BigInteger provider,BigInteger query){
        Objects.requireNonNull(actual);Objects.requireNonNull(action);CurrentLetter.unsigned(provider,false);CurrentLetter.unsigned(query,false);
        StrictJson.require(actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313,"Exact current267 Core required");CurrentLetter.requirePrefix(actual.prefix());
        StrictJson.require(action==Action.QUERY_CLOSE?provider.signum()==0&&query.signum()==0:provider.signum()>0&&query.signum()>0,"Decisions close query/action private lease role differs");
        var build=actual.build();var claim=StrictJson.object().put("schema",SCHEMA).put("game_version",build.version()).put("executable_sha256",build.executableSha256())
                .put("adapter_id",build.coreFrameAdapterId()).put("backend",BACKEND).put("action",action.wire()).put("provider_generation",provider.toString()).put("query_sequence",query.toString());
        var p=actual.prefix();claim.putObject("expected_core").put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused()).put("local_player_id",p.localPlayerId())
                .put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter()).put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());
        var fields=StrictJson.object();fields.set("decisions_close",claim);fields.set("arguments",StrictJson.object());
        return new NativeRequest(action.step(),action.capability(),new RawJson(StrictJson.canonical(fields)));
    }
}
