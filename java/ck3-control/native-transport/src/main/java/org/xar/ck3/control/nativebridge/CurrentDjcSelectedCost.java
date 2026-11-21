package org.xar.ck3.control.nativebridge;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Request DATA only. The transport alone supplies the identical private UI-query witness. */
public final class CurrentDjcSelectedCost {
    public static final String STEP="query-current-djc-selected-cost-v1";
    public static final String CAPABILITY="game.query.current-djc-selected-cost.v1";
    public static final String ACTION="query_selected_cost";
    public static final String REQUEST_SCHEMA="ck3.djc_selected_cost.current267_request.v1";
    public static final String RESULT_SCHEMA="ck3.djc_selected_cost.current267_result.v1";
    public static final String SOURCE_SCHEMA="ck3.djc_selected_cost.current267_source.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-application-main-djc-selected-cost";
    private CurrentDjcSelectedCost() { }
    static NativeRequest request(CoreFrame.Partial actual,NativeCharacterId target,
            CurrentDjcTargetWarQueryResult.CasusBelliKey cb,BigInteger provider,BigInteger query) {
        CurrentDjcTargetWarQuery.request(actual,target);Objects.requireNonNull(cb);
        positive(provider);positive(query);var p=actual.prefix();
        var core=StrictJson.object().put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused())
                .put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter())
                .put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());
        var claim=StrictJson.object().put("schema",REQUEST_SCHEMA).put("game_version",actual.build().version())
                .put("executable_sha256",actual.build().executableSha256()).put("adapter_id",actual.build().coreFrameAdapterId())
                .put("backend",BACKEND).put("action",ACTION).put("target_character_id",target.value()).put("cb_key",cb.wire())
                .put("provider_generation",provider.toString()).put("query_sequence",query.toString());
        claim.set("expected_core",core);var fields=StrictJson.object();fields.set("djc_selected_cost",claim);fields.set("arguments",StrictJson.object());
        return new NativeRequest(STEP,CAPABILITY,new RawJson(StrictJson.canonical(fields)));
    }
    private static void positive(BigInteger n) {Objects.requireNonNull(n);StrictJson.require(n.signum()>0&&n.compareTo(NativeWire.UINT64_MAX)<=0,"Original positive unsigned64 UI-query lease required");}
}
