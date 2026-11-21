package org.xar.ck3.control.nativebridge;

import java.math.BigInteger;
import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Six fixed request DATA shapes. Transport-held originals alone grant private phase/choice/send authority. */
public final class CurrentDjcDeclarationUi {
    public static final String REQUEST_SCHEMA="ck3.djc_declaration_ui.current267_request.v1";
    public static final String RESULT_SCHEMA="ck3.djc_declaration_ui.current267_result.v1";
    public static final String SOURCE_SCHEMA="ck3.djc_declaration_ui.current267_source.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-application-main-djc-ui";
    public enum Action {
        QUERY_UI("query_ui","query-current-djc-declaration-ui-v1","game.query.current-djc-declaration-ui.v1"),
        OPEN_UI("open_ui","open-current-djc-declaration-ui-v1","game.command.open-current-djc-declaration-ui.v1"),
        SELECT_CHOICE("select_choice","select-current-djc-declaration-choice-v1","game.command.select-current-djc-declaration-choice.v1"),
        SEND_UI("send_ui","send-current-djc-declaration-ui-v1","game.command.send-current-djc-declaration-ui.v1"),
        QUERY_WARNING("query_warning","query-current-djc-declaration-warning-v1","game.query.current-djc-declaration-warning.v1"),
        ACCEPT_WARNING("accept_warning","accept-current-djc-declaration-warning-v1","game.command.accept-current-djc-declaration-warning.v1");
        private final String wire,step,capability;
        Action(String wire,String step,String capability){this.wire=wire;this.step=step;this.capability=capability;}
        public String wire(){return wire;}public String step(){return step;}public String capability(){return capability;}
        public boolean readOnly(){return this==QUERY_UI||this==QUERY_WARNING;}
         static Action parse(String s)throws IOException {for(var a:values())if(a.wire.equals(s))return a;throw new IOException("Unknown fixed current DJC UI action");}
    }
    private CurrentDjcDeclarationUi() { }
    public static NativeRequest query(CoreFrame.Partial actual,NativeCharacterId target,CurrentDjcTargetWarQueryResult.CasusBelliKey cb){
        return request(Action.QUERY_UI,actual,target,cb,BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO);
    }
    static NativeRequest request(Action action,CoreFrame.Partial actual,NativeCharacterId target,CurrentDjcTargetWarQueryResult.CasusBelliKey cb,
            BigInteger provider,BigInteger query,BigInteger choice,BigInteger originClaim) {
        Objects.requireNonNull(action);Objects.requireNonNull(cb);
        // The dedicated current-query factory rejects old Full/94b aliases, self, absent and nonliving/unpaused Core DATA.
        CurrentDjcTargetWarQuery.request(actual,target);
        u64(provider);u64(query);u64(choice);u64(originClaim);
        if(action==Action.QUERY_UI)StrictJson.require(provider.signum()==0&&query.signum()==0&&choice.signum()==0&&originClaim.signum()==0,"Initial UI observation cannot supply private authority");
        else {
            StrictJson.require(provider.signum()>0&&query.signum()>0,"Actual native private UI query lease required");
            StrictJson.require(action==Action.SELECT_CHOICE?choice.signum()>0:choice.signum()==0,"Only Select consumes its actual native choice token; no ordinal/address");
            StrictJson.require(action==Action.QUERY_WARNING||action==Action.ACCEPT_WARNING?originClaim.signum()>0:originClaim.signum()==0,"Only warning phases retain the original Send claim");
        }
        var p=actual.prefix();var expected=StrictJson.object().put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused()).put("local_player_id",p.localPlayerId())
                .put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter()).put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());
        var c=StrictJson.object().put("schema",REQUEST_SCHEMA).put("game_version",actual.build().version()).put("executable_sha256",actual.build().executableSha256()).put("adapter_id",actual.build().coreFrameAdapterId())
                .put("backend",BACKEND).put("action",action.wire());c.set("expected_core",expected);c.put("target_character_id",target.value()).put("cb_key",cb.wire()).put("provider_generation",provider.toString())
                .put("query_sequence",query.toString()).put("choice_token",choice.toString()).put("origin_claim_sequence",originClaim.toString());
        var f=StrictJson.object();f.set("djc_ui",c);f.set("arguments",StrictJson.object());return new NativeRequest(action.step(),action.capability(),new RawJson(StrictJson.canonical(f)));
    }
    private static void u64(BigInteger n){Objects.requireNonNull(n);StrictJson.require(n.signum()>=0&&n.compareTo(NativeWire.UINT64_MAX)<=0,"Exact unsigned64 DATA required");}
}
