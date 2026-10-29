package org.xar.ck3.control.wave2.planning.playerrisk;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Binding;
import org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Context;
import org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Status;

/** Single-direction risk fallback for the two queue classifiers' legacy gameplay frame readers. */
public final class LegacyRiskFrameAdapter {
    private LegacyRiskFrameAdapter() { }
    public record CampaignGoal(String campaignId, int currentCharacterId) {
        public CampaignGoal { StrictJson.text(campaignId); positive(currentCharacterId); }
    }
    public record InitialCampaign(int actorCharacterId, String episodeRunId) {
        public InitialCampaign { positive(actorCharacterId); StrictJson.text(episodeRunId); }
    }
    /** Frame identity only: risk has no bridge process witness and cannot qualify a Game. */
    public record LegacyFrame(Binding binding, String episodeRunId, BigInteger connectionGeneration) { }

    public static LegacyFrame legacyRiskFallback(Context risk, CampaignGoal goal, InitialCampaign initial) {
        StrictJson.require(risk != null && risk.status() != Status.UNAVAILABLE && risk.binding() != null && risk.currentScope() != null,
                "independent legacy gameplay frame is malformed");
        Binding binding = risk.binding();
        StrictJson.require(goal.currentCharacterId() == binding.characterId(), "legacy gameplay actor sources differ");
        BigInteger generation = risk.currentScope().connectionGeneration();
        StrictJson.require(binding.characterId() == initial.actorCharacterId() && goal.campaignId().equals(initial.episodeRunId())
                && binding.revision().signum() > 0 && binding.nativeRevision().signum() > 0 && binding.dateRaw() > 0
                && generation != null && generation.signum() > 0 && binding.snapshotId().equals("native:" + binding.nativeRevision()),
                "gameplay starting actor/episode/frame binding differs");
        return new LegacyFrame(binding, goal.campaignId(), generation);
    }

    public static ObjectNode encode(LegacyFrame frame) {
        Binding binding = frame.binding(); ObjectNode result = StrictJson.object();
        result.put("snapshot_id", binding.snapshotId()); result.put("revision", binding.revision());
        result.put("native_revision", binding.nativeRevision()); result.put("date_raw", binding.dateRaw());
        result.put("character_id", binding.characterId()); result.put("actor_character_id", binding.characterId());
        result.put("episode_run_id", frame.episodeRunId()); result.put("connection_generation", frame.connectionGeneration());
        return result;
    }
    private static void positive(int value) { StrictJson.require(value > 0, "positive native actor required"); }
}
