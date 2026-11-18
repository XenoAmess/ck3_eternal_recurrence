package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.time.Instant;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact event request DATA. A transport-owned Full and observed option occurrence grant submission custody. */
public final class FullSnapshotEventOptionControl {
    public static final String SCHEMA = "ck3_1210_event_option_control_v1";
    public static final String QUERY_STEP = "query-current-event-options-v1";
    public static final String QUERY_CAPABILITY = "game.query.current-event-options.v1";
    public static final String SELECT_PREFIX = "select-event-option-";
    public static final int MAXIMUM_OPTIONS = 512;
    private FullSnapshotEventOptionControl() { }

    public static NativeRequest query(String snapshotId, BigInteger revision, Instant deadline, int eventInstanceId) {
        return new NativeRequest(QUERY_STEP, QUERY_CAPABILITY, fields(snapshotId, revision, deadline, eventInstanceId));
    }
    public static NativeRequest select(String snapshotId, BigInteger revision, Instant deadline, int eventInstanceId, int nativeOptionIndex) {
        StrictJson.require(nativeOptionIndex >= 0 && nativeOptionIndex < MAXIMUM_OPTIONS, "authored native option index must be 0..511");
        String step = SELECT_PREFIX + (nativeOptionIndex + 1);
        return new NativeRequest(step, "game.command." + step, fields(snapshotId, revision, deadline, eventInstanceId));
    }
    public static int selectedIndex(String step) {
        Objects.requireNonNull(step);
        StrictJson.require(step.matches("select-event-option-[1-9][0-9]{0,2}"), "canonical 1-based event selection step required");
        int number = Integer.parseInt(step.substring(SELECT_PREFIX.length()));
        StrictJson.require(number <= MAXIMUM_OPTIONS, "authored native option number exceeds bound");
        return number - 1;
    }
    private static RawJson fields(String snapshotId, BigInteger revision, Instant deadline, int eventInstanceId) {
        Objects.requireNonNull(revision); Objects.requireNonNull(deadline);
        StrictJson.require(revision.signum() > 0 && revision.bitLength() <= 64 && ("native:" + revision).equals(snapshotId), "positive matching native Full revision required");
        StrictJson.require(eventInstanceId > 0, "positive native event instance required");
        long until;
        try { until = deadline.toEpochMilli(); }
        catch (ArithmeticException invalid) { throw new IllegalArgumentException("finite original event deadline required", invalid); }
        StrictJson.require(until > 0, "positive original event deadline required");
        var build = ExactCk3Build.CK3_1210;
        var claim = StrictJson.object();
        claim.put("schema", SCHEMA); claim.put("game_version", build.version());
        claim.put("executable_sha256", build.executableSha256().toUpperCase(Locale.ROOT));
        claim.put("adapter_id", "ck3-1.21.0-msvc-x64"); claim.put("backend", "ck3-1.21.0-native-headless-main-thread");
        claim.put("snapshot_id", snapshotId); claim.put("native_revision", revision); claim.put("deadline_unix_ms", until);
        var row = StrictJson.object(); row.set("event_option_control", claim);
        row.putObject("arguments").put("event_instance_id", eventInstanceId);
        return new RawJson(StrictJson.canonical(row));
    }
}
