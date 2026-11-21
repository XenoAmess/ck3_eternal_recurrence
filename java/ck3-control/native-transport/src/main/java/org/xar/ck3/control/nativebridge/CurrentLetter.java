package org.xar.ck3.control.nativebridge;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** DATA encoding only. Private same-transport material supplies reply authority. */
public final class CurrentLetter {
    public static final String SCHEMA="ck3.letter.current267_request.v1";
    public static final String RESULT_SCHEMA="ck3.letter.current267_result.v1";
    public static final String SOURCE_SCHEMA="ck3.letter.current267_source.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-application-main-letter";
    public static final String KNOWN_DEFINITION="ep3_laamps.0003",KNOWN_OPTION="ep3_laamps.0003.a";
    public enum Action {
        QUERY_LETTER("query_letter","query-current-letter-v1","game.query.current-letter.v1"),
        REPLY_KNOWN("reply_known","reply-known-current-letter-v1","game.command.reply-known-current-letter.v1");
        private final String wire,step,capability;
        Action(String wire,String step,String capability){this.wire=wire;this.step=step;this.capability=capability;}
        public String wire(){return wire;}public String step(){return step;}public String capability(){return capability;}
        static Action parse(String s)throws java.io.IOException {for(var a:values())if(a.wire.equals(s))return a;throw new java.io.IOException("Unknown current letter action");}
    }
    private CurrentLetter() { }
    public static NativeRequest request(CoreFrame.Partial actual,Action action,BigInteger provider,BigInteger query) {
        Objects.requireNonNull(actual);Objects.requireNonNull(action);unsigned(provider,false);unsigned(query,false);
        StrictJson.require(actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313,"Exact current267 Core required");
        requirePrefix(actual.prefix());
        StrictJson.require(action==Action.QUERY_LETTER?provider.signum()==0&&query.signum()==0:provider.signum()>0&&query.signum()>0,"Letter query/reply lease role mismatch");
        var b=actual.build();var c=StrictJson.object().put("schema",SCHEMA).put("game_version",b.version())
                .put("executable_sha256",b.executableSha256()).put("adapter_id",b.coreFrameAdapterId()).put("backend",BACKEND)
                .put("action",action.wire()).put("provider_generation",provider.toString()).put("query_sequence",query.toString());
        var p=actual.prefix();c.putObject("expected_core").put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused())
                .put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter())
                .put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());
        var fields=StrictJson.object();fields.set("letter",c);fields.set("arguments",StrictJson.object());
        return new NativeRequest(action.step(),action.capability(),new RawJson(StrictJson.canonical(fields)));
    }
    static void requirePrefix(CoreFrame.Prefix p) {
        Objects.requireNonNull(p);StrictJson.require(p.speed()>=1&&p.speed()<=5&&p.paused()&&p.localPlayerId()>=0
                &&p.mapReady()&&p.hasPlayedCharacter()&&p.playedCharacterId()!=-1&&p.playedCharacterAlive(),"Actual paused living map Core required");
    }
    static void unsigned(BigInteger n,boolean positive){Objects.requireNonNull(n);StrictJson.require(n.signum()>=0&&(!positive||n.signum()>0)&&n.compareTo(NativeWire.UINT64_MAX)<=0,"Canonical uint64 required");}
}
