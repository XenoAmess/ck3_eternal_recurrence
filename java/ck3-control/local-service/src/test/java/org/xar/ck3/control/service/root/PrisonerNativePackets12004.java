package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Arrays;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.*;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.*;

/** Synthetic original wire packets for actual producer/archive regressions; no live native qualification. */
public final class PrisonerNativePackets12004 {
    public enum TerminalSource { DEAD, TRANSFERRED }
    private PrisonerNativePackets12004() { }
    public static byte[] selectedCollection(long actor, long target, int date, BigInteger revision, BigInteger sequence, BigInteger epoch) {
        ObjectNode root = root(actor, date, revision, sequence, epoch, 1);
        ObjectNode row = ((ObjectNode) root.get("player_prisoner_collection")).withArray("prisoners").addObject()
                .put("source_ordinal", 0).put("prisoner_character_id", target).put("collection_owner_character_id", actor)
                .put("jailer_character_id", actor).put("custody_relation_verified", true).putNull("house_id").putNull("dynasty_id")
                .put("same_house", false).put("same_dynasty", false).put("is_child_of_played_character", false).putNull("primary_title_tier_raw");
        var frame = new FrameBinding(revision, date, actor, target);
        row.set("unconditional_release_preview", ReleasePreviewCodec12003.toNode(new ReleasePreview12003.Available(frame, epoch,
                new Definition(123, 1), true, new Costs(Arrays.stream(Resource.values()).map(resource -> new CostEntry(resource, 0)).toList()))));
        row.set("ransom_quote_preview", unavailable("no_offer"));
        return StrictJson.canonical(root, 1_048_576);
    }
    public static byte[] terminalCollection(long actor, long target, long otherJailer, int date, BigInteger revision,
            BigInteger sequence, BigInteger epoch, TerminalSource source) {
        ObjectNode root = root(actor, date, revision, sequence, epoch, 0);
        var frame = new PrisonerMaterial12004.Frame(revision, date, actor, target);
        root.set("prisoner_release_material_opinion", StrictJson.parse(PrisonerMaterial12004.encode(
                new PrisonerMaterial12004.UnavailableMaterial(frame, "controlled_test_material_not_observed"))));
        ObjectNode custody = StrictJson.object().put("schema", "xar.ck3.prisoner-retained-target-state-12004-v1")
                .put("build_version", "1.20.0.4").put("executable_sha256", PrisonerMaterial12004.EXE_SHA256)
                .put("available", true).put("unavailable_reason", "").put("snapshot_revision", revision).put("date_raw", date)
                .put("actor_character_id", actor).put("target_character_id", target);
        if (source == TerminalSource.DEAD) custody.put("target_alive", false).putNull("is_imprisoned").putNull("jailer_character_id").put("custody_state", "dead");
        else {
            StrictJson.require(otherJailer > 0 && otherJailer < 0xffffffffL && otherJailer != actor, "actual different fixture jailer required");
            custody.put("target_alive", true).put("is_imprisoned", true).put("jailer_character_id", otherJailer).put("custody_state", "held_by_other");
        }
        root.set("prisoner_retained_target_state", custody); return StrictJson.canonical(root, 1_048_576);
    }
    private static ObjectNode root(long actor, int date, BigInteger revision, BigInteger sequence, BigInteger epoch, int count) {
        ObjectNode root = StrictJson.object().put("step", "query-player-prisoner-collection-private-v1").put("accepted", true)
                .put("status", "available").put("query_sequence", sequence).put("observation_revision", epoch).put("snapshot_revision", revision)
                .put("private_build", true).put("read_only", true).put("advertised", false).put("backend_id", "native-headless");
        root.putObject("player_prisoner_collection").put("schema", "player-prisoner-collection-private-v1").put("schema_version", 6)
                .put("snapshot_revision", revision).put("status", "available").putNull("unavailable_reason").put("date_raw", date)
                .put("played_character_id", actor).put("played_house_id", 1).put("played_dynasty_id", 1).put("played_dread_raw", 0)
                .put("total_count", count).put("returned_count", count).put("collection_complete", true).putArray("prisoners");
        return root;
    }
    private static ObjectNode unavailable(String reason) {
        return StrictJson.object().put("private_build", true).put("read_only", true).put("advertised", false)
                .put("action_surface_present", false).put("status", "unavailable").put("unavailable_reason", reason);
    }
}
