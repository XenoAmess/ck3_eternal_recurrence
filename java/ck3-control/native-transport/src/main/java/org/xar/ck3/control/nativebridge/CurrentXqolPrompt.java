package org.xar.ck3.control.nativebridge;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** DATA encoder. Only the retained same-receiver actual known prompt can authorize a fixed confirm or cancel. */
public final class CurrentXqolPrompt {
    public static final String SCHEMA="ck3.xqol_conversion_prompt.current267_request.v1";
    public static final String RESULT_SCHEMA="ck3.xqol_conversion_prompt.current267_result.v1";
    public static final String SOURCE_SCHEMA="ck3.xqol_conversion_prompt.current267_source.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-application-main-xqol-conversion-prompt";
    public static final String EVENT_SCHEMA="ck3.xqol_conversion_prompt.current267_event.v1";
    public static final String KNOWN_DEFINITION="xqol.100",CONFIRM_OPTION="xqol_mass_conversion_event_confirm",CANCEL_OPTION="xqol_mass_conversion_event_cancel";
    public enum Action {
        QUERY_PROMPT("query_prompt","query-xqol-conversion-prompt-current-v1","game.query.current-xqol-conversion-prompt.v1"),
        CONFIRM_CONVERSION("confirm_conversion","confirm-xqol-conversion-prompt-current-v1","game.command.confirm-current-xqol-conversion-prompt.v1"),
        CANCEL_CONVERSION("cancel_conversion","cancel-xqol-conversion-prompt-current-v1","game.command.cancel-current-xqol-conversion-prompt.v1");
        private final String wire,step,capability;
        Action(String wire,String step,String capability){this.wire=wire;this.step=step;this.capability=capability;}
        public String wire(){return wire;}public String step(){return step;}public String capability(){return capability;}
        static Action parse(String value)throws java.io.IOException {for(var action:values())if(action.wire.equals(value))return action;throw new java.io.IOException("Unknown current XQOL prompt action");}
    }
    private CurrentXqolPrompt() { }
    public static NativeRequest request(CoreFrame.Partial actual,Action action,BigInteger provider,BigInteger query,Optional<Integer> instanceId) {
        Objects.requireNonNull(actual);Objects.requireNonNull(action);Objects.requireNonNull(instanceId);
        CurrentLetter.unsigned(provider,false);CurrentLetter.unsigned(query,false);
        StrictJson.require(actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313,"Exact current267 Core required");
        CurrentLetter.requirePrefix(actual.prefix());
        requireRole(action,provider,query,instanceId);
        var build=actual.build();var claim=StrictJson.object().put("schema",SCHEMA).put("game_version",build.version())
                .put("executable_sha256",build.executableSha256()).put("adapter_id",build.coreFrameAdapterId()).put("backend",BACKEND)
                .put("action",action.wire()).put("provider_generation",provider.toString()).put("query_sequence",query.toString());
        if(instanceId.isPresent())claim.put("instance_id",instanceId.orElseThrow());else claim.putNull("instance_id");
        var p=actual.prefix();claim.putObject("expected_core").put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused())
                .put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter())
                .put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());
        var fields=StrictJson.object();fields.set("xqol_prompt",claim);fields.set("arguments",StrictJson.object());
        return new NativeRequest(action.step(),action.capability(),new RawJson(StrictJson.canonical(fields)));
    }
    static void requireRole(Action action,BigInteger provider,BigInteger query,Optional<Integer> instanceId) {
        StrictJson.require(action==Action.QUERY_PROMPT?provider.signum()==0&&query.signum()==0&&instanceId.isEmpty()
                :provider.signum()>0&&query.signum()>0&&instanceId.filter(n->n>0).isPresent(),"XQOL query/action lease or actual-instance role mismatch");
    }
}
