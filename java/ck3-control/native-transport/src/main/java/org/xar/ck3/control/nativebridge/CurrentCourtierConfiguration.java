package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Exact fixed product/setting DATA. Only a same-receiver private actual query can authorize Execute. */
public final class CurrentCourtierConfiguration {
    public static final String SCHEMA="ck3.courtier_creator_configuration.current267_request.v1";
    public static final String RESULT_SCHEMA="ck3.courtier_creator_configuration.current267_result.v1";
    public static final String SOURCE_SCHEMA="ck3.courtier_creator_configuration.current267_source.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-application-main-courtier-creator-configuration";
    public enum Action {
        QUERY_CONFIGURATION("query_configuration","query-courtier-creator-configuration-current-v1","game.query.current-courtier-creator-configuration.v1"),
        EXECUTE_SETTING("execute_setting","execute-courtier-creator-configuration-current-v1","game.command.execute-current-courtier-creator-configuration.v1");
        private final String wire,step,capability;
        Action(String wire,String step,String capability){this.wire=wire;this.step=step;this.capability=capability;}
        public String wire(){return wire;}public String step(){return step;}public String capability(){return capability;}
        public static Action parse(String value)throws IOException{for(var item:values())if(item.wire.equals(value))return item;throw new IOException("Unknown fixed courtier action");}
    }
    public enum Setting {
        CHOOSE_FEMALE("choose_female"),DIPLOMACY_PLUS_TEN("diplomacy_plus_ten"),PROWESS_PLUS_TEN("prowess_plus_ten"),CHOOSE_SAME_HOUSE("choose_same_house");
        private final String wire;Setting(String wire){this.wire=wire;}public String wire(){return wire;}
        public static Setting parse(String value)throws IOException{for(var item:values())if(item.wire.equals(value))return item;throw new IOException("Unknown fixed courtier setting");}
    }
    private CurrentCourtierConfiguration() { }
    public static NativeRequest request(CoreFrame.Partial actual,Action action,BigInteger provider,BigInteger query,CurrentCourtierControls.Product product,Setting setting){
        Objects.requireNonNull(actual);Objects.requireNonNull(action);Objects.requireNonNull(product);Objects.requireNonNull(setting);
        CurrentLetter.unsigned(provider,false);CurrentLetter.unsigned(query,false);
        StrictJson.require(actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313,"Exact current267 Core required");
        CurrentLetter.requirePrefix(actual.prefix());requireRole(action,provider,query);
        var build=actual.build();var claim=StrictJson.object().put("schema",SCHEMA).put("game_version",build.version())
                .put("executable_sha256",build.executableSha256()).put("adapter_id",build.coreFrameAdapterId()).put("backend",BACKEND)
                .put("action",action.wire()).put("provider_generation",provider.toString()).put("query_sequence",query.toString())
                .put("product",product.wire()).put("setting",setting.wire());
        var p=actual.prefix();claim.putObject("expected_core").put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused())
                .put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter())
                .put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());
        var fields=StrictJson.object();fields.set("courtier_configuration",claim);fields.set("arguments",StrictJson.object());
        return new NativeRequest(action.step(),action.capability(),new RawJson(StrictJson.canonical(fields)));
    }
    static void requireRole(Action action,BigInteger provider,BigInteger query){
        StrictJson.require(action==Action.QUERY_CONFIGURATION?provider.signum()==0&&query.signum()==0:provider.signum()>0&&query.signum()>0,"Courtier query/Execute original lease role differs");
    }
}
