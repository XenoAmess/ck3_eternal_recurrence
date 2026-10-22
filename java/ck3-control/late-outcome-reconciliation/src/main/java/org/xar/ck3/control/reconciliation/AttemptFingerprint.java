package org.xar.ck3.control.reconciliation;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Attempt;
import org.xar.ck3.control.reconciliation.LateOutcome.ContentEvidenceRef;
import org.xar.ck3.control.reconciliation.LateOutcome.ProcessIdentity;

/** Versioned new-domain canonical binding; not original JSON bytes or source authentication. */
public final class AttemptFingerprint {
    private AttemptFingerprint() { }
    public static String sha256(Attempt attempt) {
        ObjectNode root = StrictJson.object(); root.put("schema", "xar.clock-late-attempt-binding/v1");
        var scope = attempt.scope(); ObjectNode s = root.putObject("scope"); s.put("machine_id", scope.machineId());
        s.set("game", process(scope.game())); s.set("queue", process(scope.queue())); s.set("application", process(scope.application()));
        s.put("session_id", scope.sessionId()); s.put("connection_generation", scope.connectionGeneration());
        s.put("actor_id", scope.actorId()); s.put("episode_id", scope.episodeId());
        ObjectNode world = s.putObject("world"); world.put("game_state", scope.world().gameState().decimal());
        world.put("jomini_state", scope.world().jominiState().decimal());
        var source = scope.source(); ObjectNode sourceRow = s.putObject("source");
        sourceRow.put("closure_sha256", source.closureSha256()); sourceRow.put("java_build_sha256", source.javaBuildSha256());
        sourceRow.put("provider_sha256", source.providerSha256()); sourceRow.put("executable_sha256", source.executableSha256());
        sourceRow.put("qualification_receipt_sha256", source.qualificationReceiptSha256());
        var failure = attempt.original(); ObjectNode original = root.putObject("original"); original.set("receipt", ref(failure.receipt()));
        original.put("full_sequence", failure.fullSequence()); original.put("auto_sequence", failure.autoSequence());
        original.put("normal_status_query_attempted", failure.normalStatusQueryAttempted());
        original.put("stop_validation_attempted", failure.stopValidationAttempted());
        original.put("original_credit", 0); original.put("never_replay", true);
        var arm = attempt.arm(); ObjectNode armRow = root.putObject("arm"); armRow.put("generation", arm.generation().decimal());
        armRow.put("starting_date_raw", arm.startingDateRaw()); armRow.put("target_date_raw", arm.targetDateRaw());
        armRow.put("speed", arm.speed()); armRow.put("mode", arm.mode().name()); armRow.put("combat_count", arm.combatCount());
        var ids = armRow.putArray("watch_army_ids"); arm.watchArmyIds().forEach(ids::add);
        root.set("expected_head", ref(attempt.expectedHead())); root.put("min_native_revision", attempt.minNativeRevision());
        root.put("min_verified_pump_epoch", attempt.minVerifiedPumpEpoch().decimal());
        root.put("min_heartbeat_sequence", attempt.minHeartbeatSequence().decimal());
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(StrictJson.canonical(root))); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("JDK SHA-256 unavailable", error); }
    }
    private static ObjectNode process(ProcessIdentity process) {
        ObjectNode row = StrictJson.object(); row.put("pid", process.pid()); row.put("creation_filetime", process.creationFiletime().decimal()); return row;
    }
    private static ObjectNode ref(ContentEvidenceRef ref) {
        ObjectNode row = StrictJson.object(); row.put("sha256", ref.sha256()); row.put("bytes", ref.bytes()); row.put("evidence_key", ref.evidenceKey()); return row;
    }
}
