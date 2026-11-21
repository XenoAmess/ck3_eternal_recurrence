package org.xar.ck3.control.nativebridge;

import java.util.Objects;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Fixed request DATA. Actual authority remains the transport's original received Core. */
public final class CurrentAubObserverFixture {
    public static final String STEP="run-current-aub-observer-fixture-v1";
    public static final String CAPABILITY="game.command.run-current-aub-observer-fixture.v1";
    public static final String SCHEMA="ck3.private_fixture_inbox.current267_request.v1";
    public static final String RESULT_SCHEMA="ck3.private_fixture_inbox.current267_result.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-headless-main-thread";
    public static final String FILENAME="xar_mcp_inbox.txt";
    private CurrentAubObserverFixture() { }
    public static NativeRequest request(CoreFrame.Partial actual) {
        Objects.requireNonNull(actual);var p=actual.prefix();
        StrictJson.require(actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313,
                "Dedicated exact current267 Core required for the fixed observer fixture");
        requirePrefix(p);
        var claim=StrictJson.object().put("schema",SCHEMA).put("game_version",actual.build().version())
                .put("executable_sha256",actual.build().executableSha256()).put("adapter_id",actual.build().coreFrameAdapterId())
                .put("backend",BACKEND).put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused())
                .put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter())
                .put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());
        var fields=StrictJson.object();fields.set("aub_observer_fixture",claim);fields.set("arguments",StrictJson.object());
        return new NativeRequest(STEP,CAPABILITY,new RawJson(StrictJson.canonical(fields)));
    }
    static void requirePrefix(CoreFrame.Prefix p) {
        Objects.requireNonNull(p);
        StrictJson.require(p.speed()>=1&&p.speed()<=5&&p.paused()&&p.localPlayerId()>=0&&p.mapReady()
                &&p.hasPlayedCharacter()&&p.playedCharacterId()!=-1&&p.playedCharacterAlive(),
                "Actual paused living map Core required; no caller path, console body or fabricated owner");
    }
}
