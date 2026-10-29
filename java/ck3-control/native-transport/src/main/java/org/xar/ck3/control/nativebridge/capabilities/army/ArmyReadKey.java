package org.xar.ck3.control.nativebridge.capabilities.army;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Complete immutable identity for finite dynamic Army read factories. */
final class ArmyReadKey {
    private ArmyReadKey() { }
    static RawJson key(ArmyCalls.Call input, ArmyTypes.Context c) {
        var f = c.before().frame(); var source = c.source();
        var n = empty().put("method", input.method().pythonName()).put("machine_id", c.before().machineId()).put("session_id", c.sessionId())
                .put("snapshot_id", f.snapshotId()).put("public_revision", f.revision().toString()).put("native_revision", c.nativeRevision().toString())
                .put("date_raw", c.dateRaw().toString()).put("player", c.playerId().toString()).put("episode_run_id", f.episodeRunId())
                .put("observation_version", c.before().observationVersion())
                .put("source_observed_at_utc", source.observedAtUtc()).put("source_exact_build", source.exactBuild());
        n.set("game", c.before().game().toJson()); n.set("source_ref", source.sourceRef().toJson()); n.set("public_arguments", parse(ArmyCallCodec.encode(input).bytes()));
        return new RawJson(bytes(n));
    }
    static String digest(RawJson key) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(key.bytes())); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException("SHA256 unavailable", impossible); }
    }
}
