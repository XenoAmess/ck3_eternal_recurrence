package org.xar.ck3.control.nativebridge;

import java.util.Objects;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Exact request DATA only; neither this factory nor a Native submitted result proves a physical SAVE. */
public final class CurrentCoreCheckpointSave {
    public static final String STEP="save-checkpoint";
    public static final String CAPABILITY="game.command.current-core-checkpoint-save.v1";
    public static final String SCHEMA="ck3_121003_core_checkpoint_save_v1";
    public static final String RESULT_SCHEMA="ck3_121003_core_checkpoint_save_result_v1";
    public static final String BACKEND="ck3-1.21.0.3-native-headless-main-thread";
    public static final String SAVE_NAME="xar_checkpoint",FILENAME=SAVE_NAME+".ck3";
    private CurrentCoreCheckpointSave() { }
    public static NativeRequest request(CoreFrame.Partial actual) {
        Objects.requireNonNull(actual);var p=actual.prefix();
        StrictJson.require(actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313,
                "Dedicated current267 narrow Core required; no old clock or Full111 alias");
        StrictJson.require(p.speed()>=1&&p.speed()<=5&&p.paused()&&p.mapReady()&&p.localPlayerId()>=0
                &&p.hasPlayedCharacter()&&p.playedCharacterId()!=-1&&p.playedCharacterAlive(),"Actual paused living map Core required for checkpoint request");
        var claim=StrictJson.object().put("schema",SCHEMA).put("game_version",actual.build().version())
                .put("executable_sha256",actual.build().executableSha256()).put("adapter_id",actual.build().coreFrameAdapterId())
                .put("backend",BACKEND).put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused())
                .put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter())
                .put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());
        var fields=StrictJson.object();fields.set("core_checkpoint_save",claim);
        return new NativeRequest(STEP,CAPABILITY,new RawJson(StrictJson.canonical(fields)));
    }
}
