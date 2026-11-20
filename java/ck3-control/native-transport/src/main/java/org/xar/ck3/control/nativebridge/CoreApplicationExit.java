package org.xar.ck3.control.nativebridge;

import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Exact request DATA only. An original requested ACK does not establish a natural process exit. */
public final class CoreApplicationExit {
    public static final String STEP="normal-exit-application-v1";
    public static final String CAPABILITY="game.command."+STEP;
    public static final String SCHEMA="ck3_1210_application_exit_v1";
    private CoreApplicationExit() { }

    public static NativeRequest request(CoreFrame.Partial frame) {
        java.util.Objects.requireNonNull(frame,"frame");
        if(frame.build()==ExactCk3Build.CK3_121003_STEAM_26785313)return current267Request(frame);
        var claim=CoreClockControl.claim(frame).put("schema",SCHEMA);
        var fields=StrictJson.object();fields.set("core_application_exit",claim);
        return new NativeRequest(STEP,CAPABILITY,new RawJson(StrictJson.canonical(fields)));
    }
    /** Dedicated current267 quit ABI only; this does not widen old clock/save or Full claim qualification. */
    private static NativeRequest current267Request(CoreFrame.Partial frame) {
        var p=frame.prefix();
        StrictJson.require(p.paused()&&p.mapReady()&&p.localPlayerId()>=0&&p.hasPlayedCharacter()
                &&p.playedCharacterId()!=-1&&p.playedCharacterAlive(),"current267 quit requires its actual paused living map Core");
        var claim=StrictJson.object().put("schema",SCHEMA).put("game_version",frame.build().version())
                .put("executable_sha256",frame.build().executableSha256()).put("adapter_id",frame.build().coreFrameAdapterId())
                .put("backend","ck3-1.21.0.3-native-headless-main-thread").put("date_raw",p.dateRaw()).put("speed",p.speed())
                .put("paused",p.paused()).put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady())
                .put("has_played_character",p.hasPlayedCharacter()).put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());
        var fields=StrictJson.object();fields.set("core_application_exit",claim);
        return new NativeRequest(STEP,CAPABILITY,new RawJson(StrictJson.canonical(fields)));
    }
}
