package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.time.Instant;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;

/** Request data only. An actual transport-owned Full and GUI observation must authorize activation. */
public final class FullSnapshotGuiControl {
    public static final String SCHEMA = "ck3_1210_gui_control_v1";
    public static final String QUERY_STEP = "query-scripted-widget-controls-v1";
    public static final String ACTIVATE_STEP = "activate-scripted-widget-control-v1";
    public static final String QUERY_CAPABILITY = "game.query.scripted-widget-controls.v1";
    public static final String ACTIVATE_CAPABILITY = "game.command.activate-scripted-widget-control.v1";
    public static final int MAXIMUM_CONTROLS = 2048;
    private static final BigInteger UINT64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private FullSnapshotGuiControl() { }

    public static NativeRequest query(String snapshotId, BigInteger revision, Instant deadline, String rootName) {
        return request(QUERY_STEP, QUERY_CAPABILITY, snapshotId, revision, deadline, rootName, BigInteger.ZERO, BigInteger.ZERO);
    }

    public static NativeRequest activate(String snapshotId, BigInteger revision, Instant deadline,
            String rootName, BigInteger queryGeneration, BigInteger widgetId) {
        requirePositive(queryGeneration, "query generation");
        requirePositive(widgetId, "widget id");
        return request(ACTIVATE_STEP, ACTIVATE_CAPABILITY, snapshotId, revision, deadline, rootName, queryGeneration, widgetId);
    }

    private static NativeRequest request(String step, String capability, String snapshotId, BigInteger revision,
            Instant deadline, String rootName, BigInteger generation, BigInteger widgetId) {
        Objects.requireNonNull(deadline);
        requirePositive(revision, "Full revision");
        StrictJson.require(("native:" + revision).equals(snapshotId), "GUI request requires its matching Full snapshot id");
        StrictJson.require(rootName != null && rootName.matches("[A-Za-z_][A-Za-z0-9_]{0,127}"), "bounded native root name required");
        long until;
        try { until = deadline.toEpochMilli(); }
        catch (ArithmeticException invalid) { throw new IllegalArgumentException("finite original GUI deadline required", invalid); }
        StrictJson.require(until > 0, "positive original GUI deadline required");
        var build = ExactCk3Build.CK3_1210;
        var claim = StrictJson.object();
        claim.put("schema", SCHEMA);
        claim.put("game_version", build.version());
        claim.put("executable_sha256", build.executableSha256().toUpperCase(Locale.ROOT));
        claim.put("adapter_id", "ck3-1.21.0-msvc-x64");
        claim.put("backend", "ck3-1.21.0-native-headless-main-thread");
        claim.put("snapshot_id", snapshotId);
        claim.put("native_revision", revision);
        claim.put("deadline_unix_ms", until);
        claim.put("root_name", rootName);
        claim.put("query_generation", generation.toString());
        claim.put("widget_id", widgetId.toString());
        var additional = StrictJson.object();
        additional.set("gui_control_v1", claim);
        additional.putObject("arguments");
        return new NativeRequest(step, capability, new RawJson(StrictJson.canonical(additional)));
    }

    private static void requirePositive(BigInteger value, String field) {
        Objects.requireNonNull(value, field);
        StrictJson.require(value.signum() > 0 && value.compareTo(UINT64_MAX) <= 0, "positive uint64 " + field + " required");
    }
}
