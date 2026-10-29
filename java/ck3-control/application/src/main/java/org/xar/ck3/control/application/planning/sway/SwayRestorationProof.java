package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Replays the SWAY source from the actual committed restore and saved writer head. No new restore authority. */
public final class SwayRestorationProof {
    private SwayRestorationProof() { }
    public static ExactRef material(ContinuityState actualHead) {
        JsonNode details = actualHead.toJson().get("last_current_saved_cold"); require(details != null && details.isObject(), "Sway historical continuation needs an actual committed restore");
        JsonNode sources = details.get(SavedAttachmentSourceStore.SOURCES_DETAIL); require(sources != null && sources.isObject(), "committed restore lacks original saved material source");
        SwayNativeWire.equals(sources, "schema", SavedAttachmentSourceStore.SOURCES_SCHEMA); return ExactRef.fromJson(sources.get("material"));
    }
    /** The caller must obtain binding through the actual Context.requireRestoration, which reruns service.requireCurrent. */
    public static void requireBinding(RestoreCheckpointService.RestoreBinding actual, ContinuityState head,
            SwayNativeWire.TargetRead fresh, ActionPorts.OutcomeArchive archive) {
        requireBinding(actual, head, fresh.binding().before(), fresh.binding().sessionId(), archive);
    }
    public static void requireBinding(RestoreCheckpointService.RestoreBinding actual, ContinuityState head,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity fresh, String sessionId, ActionPorts.OutcomeArchive archive) {
        require(actual.session().machineId().equals(fresh.machineId()) && actual.session().game().equals(fresh.game())
                && actual.session().sessionId().equals(sessionId) && actual.episodeRunId().equals(fresh.frame().episodeRunId()), "actual restoration belongs to another Sway source");
        JsonNode retained = StrictJson.parse(archive.loadMaterial(material(head)).bytes(), SwayFormalCodec.MAX);
        require(actual.pair().equals(CheckpointPairCodec.decode(StrictJson.canonical(retained.get("pair")))), "Sway saved material belongs to another actual restore pair");
    }
    public static void verify(ActionPorts.OutcomeArchive archive, ContinuityState actualHead, ExactRef material,
            SwayFormalState.Ledger predecessor, SwayNativeWire.TargetRead fresh) {
        verifyScope(archive, actualHead, material, predecessor, fresh.binding().before());
    }
    public static void verifyScope(ActionPorts.OutcomeArchive archive, ContinuityState actualHead, ExactRef material,
            SwayFormalState.Ledger predecessor, org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity fresh) {
        require(material(actualHead).equals(material), "Sway restore source is not the canonical committed attachment");
        JsonNode game = actualHead.toJson().get("game_binding"); require(game != null && game.isObject() && actualHead.machineId().equals(predecessor.machineId()) && game.equals(fresh.game().toJson()), "Sway restoration crossed physical Game");
        JsonNode row = StrictJson.parse(archive.loadMaterial(material).bytes(), SwayFormalCodec.MAX);
        SwayNativeWire.equals(row, "schema", SavedAttachmentSourceStore.MATERIAL_SCHEMA);
        var pair = CheckpointPairCodec.decode(StrictJson.canonical(row.get("pair")));
        require(pair.frame().machineId().equals(predecessor.machineId()) && pair.frame().frame().episodeRunId().equals(predecessor.episodeRunId())
                && pair.frame().frame().identity().player().equals(fresh.frame().identity().player()), "saved original Sway scope differs");
        var original = ContinuityState.fromJson(org.xar.ck3.control.continuity.ContinuityJson.object(row.get("original_writer_head")), predecessor.machineId());
        require(org.xar.ck3.control.continuity.ContinuityJson.digest(original.toJson()).equals(SwayNativeWire.string(row, "original_writer_head_sha256")), "saved original writer head digest differs");
        var body = DomainBodies.reference(original, DomainBodies.Slot.SWAY).orElseThrow(() -> new IllegalArgumentException("saved original has no SWAY domain source; historical JSON cannot grant cross-Game continuation"));
        var saved = SwayFormalCodec.decode(archive.loadMaterial(body.payload()).bytes());
        require(saved.originalMigrationInput().equals(predecessor.originalMigrationInput()), "selected canonical Sway original is not in the actual saved checkpoint");
        if (predecessor.pending().isPresent()) require(saved.pending().equals(predecessor.pending()), "saved original Java pending differs; tuple alone cannot rebind it");
        else if (predecessor.resolved().isPresent()) {
            var current = predecessor.resolved().orElseThrow(); var retained = saved.resolved().orElseThrow();
            require(retained.identity().equals(current.identity()) && retained.originalIntent().equals(current.originalIntent()) && retained.independentActive().equals(current.independentActive()) && retained.lifecycle().equals(current.lifecycle()) && retained.stop().equals(current.stop()), "saved original Java resolved source differs");
        } else require(saved.imported().isPresent() && predecessor.imported().isPresent() && saved.imported().orElseThrow().archivedOriginal().equals(predecessor.imported().orElseThrow().archivedOriginal()), "selected legacy original is not in the actual saved checkpoint");
    }
}
