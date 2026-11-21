package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Fixed current-build DATA. Effects require the transport's original private observation. */
public final class CurrentCuratedDecisions {
    public static final String SCHEMA="ck3.curated_decisions.current267_request.v1";
    public static final String RESULT_SCHEMA="ck3.curated_decisions.current267_result.v1";
    public static final String SOURCE_SCHEMA="ck3.curated_decisions.current267_source.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-application-main-curated-decisions";
    public enum Action {
        QUERY("query","query-curated-decisions-current-v1","game.query.current-curated-decisions.v1"),
        OPEN_LIST("open_list","open-curated-decisions-current-v1","game.command.open-current-curated-decisions.v1"),
        OPEN_DETAIL("open_detail","open-curated-decision-current-v1","game.command.open-current-curated-decision.v1"),
        CONFIRM("confirm","confirm-curated-decision-current-v1","game.command.confirm-current-curated-decision.v1");
        private final String wire,step,capability;
        Action(String wire,String step,String capability){this.wire=wire;this.step=step;this.capability=capability;}
        public String wire(){return wire;}public String step(){return step;}public String capability(){return capability;}
        public static Action parse(String value)throws IOException{for(var a:values())if(a.wire.equals(value))return a;throw new IOException("Unknown fixed curated-decision action");}
    }
    public enum DecisionKey {
        ENABLE_AUTO_APPOINTMENT("xqol_enable_auto_appointment_decision"),DISABLE_AUTO_APPOINTMENT("xqol_disable_auto_appointment_decision"),
        ENABLE_NO_VASSAL_TRANSFERS("xqol_enable_no_vassal_transfers_decision"),DISABLE_NO_VASSAL_TRANSFERS("xqol_disable_no_vassal_transfers_decision"),
        ENABLE_AUTO_CALL_DEFENDERS("xqol_enable_auto_call_defenders_decision"),DISABLE_AUTO_CALL_DEFENDERS("xqol_disable_auto_call_defenders_decision"),
        MASS_CONVERSION("xqol_mass_conversion_decision"),MAIN_CREATOR("xar_courtier_creator_decision"),VIVHITE_CREATOR("ervc_courtier_creator_decision");
        private final String wire;DecisionKey(String wire){this.wire=wire;}public String wire(){return wire;}
        public static DecisionKey parse(String value)throws IOException{for(var k:values())if(k.wire.equals(value))return k;throw new IOException("Decision is outside the nine fixed current keys");}
    }
    private CurrentCuratedDecisions() { }
    static void requireRole(Action action,BigInteger provider,BigInteger query,Optional<DecisionKey> decision) {
        Objects.requireNonNull(action);Objects.requireNonNull(decision);CurrentLetter.unsigned(provider,false);CurrentLetter.unsigned(query,false);
        StrictJson.require(action==Action.QUERY?provider.signum()==0&&query.signum()==0&&decision.isEmpty()
                :provider.signum()>0&&query.signum()>0&&(action==Action.OPEN_LIST?decision.isEmpty():decision.isPresent()),"Curated action/key/private-lease role differs");
    }
    public static NativeRequest request(CoreFrame.Partial actual,Action action,BigInteger provider,BigInteger query,Optional<DecisionKey> decision) {
        Objects.requireNonNull(actual);requireRole(action,provider,query,decision);
        StrictJson.require(actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313,"Exact current267 Core required");CurrentLetter.requirePrefix(actual.prefix());
        var b=actual.build();var claim=StrictJson.object().put("schema",SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256())
                .put("adapter_id",b.coreFrameAdapterId()).put("backend",BACKEND).put("action",action.wire()).put("provider_generation",provider.toString()).put("query_sequence",query.toString());
        if(decision.isPresent())claim.put("decision_key",decision.orElseThrow().wire());else claim.putNull("decision_key");
        var p=actual.prefix();claim.putObject("expected_core").put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused()).put("local_player_id",p.localPlayerId())
                .put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter()).put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());
        var fields=StrictJson.object();fields.set("curated_decisions",claim);fields.set("arguments",StrictJson.object());
        return new NativeRequest(action.step(),action.capability(),new RawJson(StrictJson.canonical(fields)));
    }
}
