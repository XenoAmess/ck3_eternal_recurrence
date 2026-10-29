package org.xar.ck3.control.application.effects;

import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;

/** Stable permission binding; fresh original packets and query sequences remain independently verified evidence. */
public final class FrontendGuardBinding {
    private FrontendGuardBinding() { }
    public static String digest(FrontendIdentity identity) {
        var row = StrictJson.object(); row.put("machine_id", identity.machineId()); row.set("game", identity.game().toJson());
        row.put("frontend_session_id", identity.frontendSessionId()); row.put("connection_generation", identity.connectionGeneration().toString());
        row.put("bridge_pid", identity.bridgePid());
        if (identity.frame() instanceof FrontendFrame.Menu) row.put("frame", "menu");
        else {
            var frame = (FrontendFrame.Snapshot) identity.frame(); row.put("frame", "snapshot"); row.put("snapshot_id", frame.snapshotId());
            row.put("revision", frame.revision().toString()); row.put("native_revision", frame.nativeRevision().toString()); row.put("date_raw", frame.dateRaw());
        }
        return ActionCodec.sha256(EffectJson.raw(row).bytes());
    }
}
