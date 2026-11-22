package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Typed catalogue DATA. Only a private complete query can mint a selectable original row. */
public final class CurrentCourtierChoices {
    public static final String SCHEMA="ck3.courtier_creator_choices.current267_request.v1";
    public static final String RESULT_SCHEMA="ck3.courtier_creator_choices.current267_result.v1";
    public static final String SOURCE_SCHEMA="ck3.courtier_creator_choices.current267_source.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-application-main-courtier-creator-choices";
    public enum Action {
        QUERY_CHOICES("query_choices","query-courtier-creator-choices-current-v1","game.query.current-courtier-creator-choices.v1"),
        SELECT_CHOICE("select_choice","select-courtier-creator-choice-current-v1","game.command.select-current-courtier-creator-choice.v1");
        private final String wire,step,capability;
        Action(String wire,String step,String capability){this.wire=wire;this.step=step;this.capability=capability;}
        public String wire(){return wire;}public String step(){return step;}public String capability(){return capability;}
        public static Action parse(String value)throws IOException{for(var item:values())if(item.wire.equals(value))return item;throw new IOException("Unknown courtier choices action");}
    }
    public enum Catalog {
        EDUCATION("education"),COMMANDER("commander"),PHYSICAL("physical"),PERSONALITY("personality"),OTHER("other"),CULTURE("culture"),FAITH("faith");
        private final String wire;Catalog(String wire){this.wire=wire;}public String wire(){return wire;}
        public static Catalog parse(String value)throws IOException{for(var item:values())if(item.wire.equals(value))return item;throw new IOException("Unknown fixed courtier catalogue");}
    }
    private CurrentCourtierChoices() { }
    public static String exactKey(String key){Objects.requireNonNull(key);StrictJson.require(key.matches("[A-Za-z0-9_.-]{1,128}"),"Actual canonical catalogue key required");return key;}
    static String token(String token){Objects.requireNonNull(token);StrictJson.require(token.matches("[A-Za-z0-9_.-]{1,96}"),"Actual opaque private-query token required");return token;}
    public static NativeRequest request(CoreFrame.Partial actual,Action action,BigInteger provider,BigInteger query,CurrentCourtierControls.Product product,Catalog catalog,String choiceToken){
        Objects.requireNonNull(actual);Objects.requireNonNull(action);Objects.requireNonNull(product);Objects.requireNonNull(catalog);Objects.requireNonNull(choiceToken);
        CurrentLetter.unsigned(provider,false);CurrentLetter.unsigned(query,false);
        StrictJson.require(actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313,"Exact current267 Core required");
        CurrentLetter.requirePrefix(actual.prefix());requireRole(action,provider,query,choiceToken);
        var b=actual.build();var claim=StrictJson.object().put("schema",SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256()).put("adapter_id",b.coreFrameAdapterId()).put("backend",BACKEND)
                .put("action",action.wire()).put("provider_generation",provider.toString()).put("query_sequence",query.toString()).put("product",product.wire()).put("catalog",catalog.wire()).put("choice_token",choiceToken);
        var p=actual.prefix();claim.putObject("expected_core").put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused()).put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter()).put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());
        var fields=StrictJson.object();fields.set("courtier_choices",claim);fields.set("arguments",StrictJson.object());return new NativeRequest(action.step(),action.capability(),new RawJson(StrictJson.canonical(fields)));
    }
    static void requireRole(Action action,BigInteger provider,BigInteger query,String choiceToken){
        if(action==Action.QUERY_CHOICES)StrictJson.require(provider.signum()==0&&query.signum()==0&&choiceToken.isEmpty(),"Query requires zero lease and empty token");
        else{StrictJson.require(provider.signum()>0&&query.signum()>0,"Select requires positive original private lease");token(choiceToken);}
    }
}
