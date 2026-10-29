package org.xar.ck3.control.wave2.runtime.savedproof;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.OptionalLong;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.metrics.DecisionMetricRecorder;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Synthetic objects only; actual production qualification encoder -> actual saved-metrics consumer. No physical read. */
public final class DecisionSavedMetricsRegression {
    private DecisionSavedMetricsRegression() { }
    private static final Instant UTC = Instant.parse("2026-10-22T20:45:00Z");
    private static final String MACHINE = "synthetic-metrics-test-machine";
    private static final String SHA = "0".repeat(64);
    private static final Path ROOT = Path.of("D:/synthetic-not-created-decision-metrics").toAbsolutePath();
    private static int checks;
    @FunctionalInterface private interface Checked { void run(); }
    public static void main(String[] args) { run(); }
    public static void run() {
        checks = 0;
        SavedCheckpointMeasurement before = synthetic(240, UTC, MACHINE, false);
        SavedCheckpointMeasurement after = synthetic(288, UTC.plusSeconds(1), MACHINE, false);
        DecisionMetricRecorder recorder = recorder();
        var observed = DecisionSavedMetrics.observeWindow(recorder, before, after);
        check(observed.observedSavedDays() == 2, "actual qualification producer reaches saved metric consumer");
        check(recorder.snapshot().nativeObservation().isEmpty(), "saved observations do not synthesize native progress");
        check(DecisionMetrics.decode(DecisionMetrics.encode(recorder.snapshot())).equals(recorder.snapshot()), "actual save-consumer metric roundtrip");
        expect(() -> DecisionSavedMetrics.observeWindow(recorder, before, after), "saved observation recorded only once");
        expect(() -> DecisionSavedMetrics.observeWindow(recorder(), before, synthetic(288, UTC.minusSeconds(1), MACHINE, false)), "proof chronology rollback");
        expect(() -> DecisionSavedMetrics.observeWindow(recorder(), before, synthetic(288, UTC.plusSeconds(1), "other-machine", false)), "machine mismatch");
        expect(() -> DecisionSavedMetrics.observeWindow(recorder(), before, synthetic(288, UTC.plusSeconds(1), MACHINE, true)), "checkpoint size differs from actual save ref");
        expect(() -> DecisionSavedMetrics.observeWindow(recorder(), after, synthetic(240, UTC.plusSeconds(2), MACHINE, false)), "saved date rollback");
        check(SavedCheckpointMeasurement.class.getConstructors().length == 0, "production measured proof has no public JSON constructor");
        System.out.println("DecisionSavedMetricsRegression PASS " + checks + " checks; synthetic production encoder/consumer only; physical reads=0");
    }
    private static SavedCheckpointMeasurement synthetic(int date, Instant observed, String machine, boolean wrongSize) {
        FileStatIdentity identity = new FileStatIdentity(BigInteger.ONE, "1", "1");
        ExactRef save = new ExactRef(ROOT.resolve("save games/xar_checkpoint.ck3").toString(), 1, SHA);
        ExactRef driver = new ExactRef(ROOT.resolve("synthetic-driver").toString(), 1, SHA);
        ExactRef freeze = new ExactRef(ROOT.resolve("synthetic-freeze").toString(), 1, SHA);
        Path sdk = ROOT.resolve("sdk"); ExactRef validator = new ExactRef(sdk.resolve("xar_autoplayer/cold_checkpoint_validator.py").toString(), 1, SHA);
        RecoveryEvidence release = evidence("synthetic-unused-release", StrictJson.canonical(StrictJson.object()));
        SavedProofReadTicket ticket = new SavedProofReadTicket(release, machine, "0".repeat(32), UTC.minusSeconds(10), UTC.plusSeconds(600),
                Path.of(driver.path()), identity, save, identity, sdk, freeze, validator, "synthetic-never-opened-pipe", ROOT.resolve("python.exe"), ROOT, 1024, 1024, 1);
        ObjectNode checkpoint = StrictJson.object(); checkpoint.put("date_raw", date); checkpoint.put("size", wrongSize ? 2 : 1);
        checkpoint.put("sha256", SHA); checkpoint.put("history_index", 1);
        ObjectNode anchor = StrictJson.object(); anchor.put("saved_date_raw", date);
        var observation = new SavedCheckpointMeasurementCoordinator.Observation(driver, checkpoint, anchor, observed, List.of());
        byte[] canonical = SavedCheckpointMeasurementCoordinator.qualification(ticket, observation);
        RecoveryEvidence proof = evidence("synthetic-canonical-" + date, canonical);
        return new SavedCheckpointMeasurement(ticket, proof, proof, driver, identity, SHA, SHA, observed);
    }
    private static RecoveryEvidence evidence(String name, byte[] raw) {
        return new RecoveryEvidence(new ExactRef(ROOT.resolve(name).toString(), raw.length, RecoveryEvidence.sha256(raw)), raw);
    }
    private static DecisionMetricRecorder recorder() {
        DecisionMetricRecorder.Clock clock = new DecisionMetricRecorder.Clock() {
            @Override public String domainId() { return "synthetic-save-domain"; }
            @Override public DecisionMetrics.Tick now() { return new DecisionMetrics.Tick(domainId(), 0, UTC, Thread.currentThread().threadId(), OptionalLong.empty()); }
        };
        return new DecisionMetricRecorder(new DecisionMetrics.Context(MACHINE, "scope", "batch", "request", clock.domainId()), clock);
    }
    private static void check(boolean value, String message) { if (!value) { throw new IllegalStateException(message); } checks++; }
    private static void expect(Checked action, String message) {
        try { action.run(); } catch (IllegalArgumentException rejected) { checks++; return; }
        throw new IllegalStateException("expected rejection: " + message);
    }
}
