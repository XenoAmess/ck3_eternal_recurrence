package org.xar.ck3.control.wave2.runtime.stdioidentity;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.stdioidentity.IdentityUnavailableException.Reason;
import org.xar.ck3.control.wave2.runtime.stdioidentity.StdioIdentityPlanV1.SourcePinV1;

/**
 * Actual bounded process/source measurements around an original owned transport.
 * It never creates or infers parent/child, stdio, inherited-handle or native custody.
 */
public final class SourceBoundStdioIdentityVerifier {
    @FunctionalInterface public interface MachineIdentityReader {
        String currentMachineId() throws IOException;
    }

    /** Source content/metadata observation; it does not pretend to expose a Win32 FileID. */
    public record SourceMeasurement(Path realPath, long bytes, String sha256,
            Instant createdAtUtc, Instant modifiedAtUtc, Instant observedAtUtc) {
        public SourceMeasurement {
            Objects.requireNonNull(realPath); Objects.requireNonNull(sha256); Objects.requireNonNull(createdAtUtc);
            Objects.requireNonNull(modifiedAtUtc); Objects.requireNonNull(observedAtUtc);
            StrictJson.require(realPath.isAbsolute() && bytes >= 0 && bytes <= StdioIdentityPlanV1.MAX_SOURCE_BYTES
                    && sha256.matches("[0-9a-f]{64}"), "validated source content observation required");
        }
    }

    /** No public constructor or JSON decoder can turn claimed metadata into a measured snapshot. */
    public static final class Snapshot {
        private final StdioIdentityPlanV1 plan;
        private final MeasuredProcessIdentity game, queue, app;
        private final List<SourceMeasurement> sources;
        private final Instant completedAtUtc;

        private Snapshot(StdioIdentityPlanV1 plan, MeasuredProcessIdentity game,
                MeasuredProcessIdentity queue, MeasuredProcessIdentity app,
                List<SourceMeasurement> sources, Instant completedAtUtc) {
            this.plan = plan; this.game = game; this.queue = queue; this.app = app;
            this.sources = List.copyOf(sources); this.completedAtUtc = completedAtUtc;
        }

        public StdioIdentityPlanV1 plan() { return plan; }
        public MeasuredProcessIdentity game() { return game; }
        public MeasuredProcessIdentity queue() { return queue; }
        public MeasuredProcessIdentity app() { return app; }
        public List<SourceMeasurement> sources() { return sources; }
        public Instant completedAtUtc() { return completedAtUtc; }
    }

    private final ProcessIdentityReader processReader;
    private final MachineIdentityReader machineReader;

    public SourceBoundStdioIdentityVerifier(ProcessIdentityReader processReader, MachineIdentityReader machineReader) {
        this.processReader = Objects.requireNonNull(processReader);
        this.machineReader = Objects.requireNonNull(machineReader);
    }

    public static SourceBoundStdioIdentityVerifier system() {
        return new SourceBoundStdioIdentityVerifier(new Win32ProcessIdentityReader(), () -> {
            try { return WindowsJobProcess.currentMachineId(); }
            catch (RuntimeException error) {
                throw new IdentityUnavailableException(Reason.NATIVE_UNAVAILABLE,
                        "actual machine identity is unavailable", error);
            }
        });
    }

    /** Fresh measurements; there is no cached/GREEN shortcut. */
    public Snapshot requireCurrent(StdioIdentityPlanV1 plan) throws IOException {
        Objects.requireNonNull(plan);
        if (!plan.machineId().equals(machineReader.currentMachineId())) {
            throw new IdentityUnavailableException(Reason.MACHINE_MISMATCH, "actual machine identity differs");
        }
        MeasuredProcessIdentity game = process(plan.game());
        MeasuredProcessIdentity queue = process(plan.queue());
        MeasuredProcessIdentity app = process(plan.app());
        List<SourceMeasurement> sources = new ArrayList<>(plan.entrySources().size());
        Set<Path> actualSources = new HashSet<>();
        for (SourcePinV1 pin : plan.entrySources()) {
            SourceMeasurement measured = source(pin);
            if (!actualSources.add(measured.realPath())) {
                throw new IdentityUnavailableException(Reason.SOURCE_MISMATCH, "duplicate resolved entry source path");
            }
            sources.add(measured);
        }
        return new Snapshot(plan, game, queue, app, sources, Instant.now());
    }

    /** Repeat actual measurements after the original read; changed source content/metadata refuses. */
    public Snapshot requireUnchanged(Snapshot before) throws IOException {
        Objects.requireNonNull(before);
        Snapshot after = requireCurrent(before.plan());
        for (int index = 0; index < before.sources().size(); index++) {
            SourceMeasurement previous = before.sources().get(index), current = after.sources().get(index);
            if (!previous.realPath().equals(current.realPath()) || !previous.createdAtUtc().equals(current.createdAtUtc())
                    || !previous.modifiedAtUtc().equals(current.modifiedAtUtc())) {
                throw new IdentityUnavailableException(Reason.SOURCE_MISMATCH, "entry source metadata changed across read");
            }
        }
        return after;
    }

    private MeasuredProcessIdentity process(ProcessIdentityClaimV1 expected) throws IOException {
        MeasuredProcessIdentity actual = processReader.observe(expected.pid());
        if (actual == null || !expected.sameGeneration(actual.identity())) {
            throw new IdentityUnavailableException(Reason.GENERATION_MISMATCH,
                    "actual process PID, kernel birth or image differs from original generation");
        }
        return actual;
    }

    private static SourceMeasurement source(SourcePinV1 pin) throws IOException {
        try {
            Path real = pin.path().toRealPath();
            BasicFileAttributes before = Files.readAttributes(real, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            if (!before.isRegularFile() || before.size() != pin.bytes()) {
                throw new IdentityUnavailableException(Reason.SOURCE_MISMATCH, "entry source size or regular-file state differs");
            }
            byte[] raw;
            try (InputStream input = Files.newInputStream(real)) {
                raw = input.readNBytes(Math.toIntExact(pin.bytes() + 1));
            }
            String sha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
            BasicFileAttributes after = Files.readAttributes(real, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            if (raw.length != pin.bytes() || !sha.equals(pin.sha256()) || !after.isRegularFile()
                    || before.size() != after.size() || !before.creationTime().equals(after.creationTime())
                    || !before.lastModifiedTime().equals(after.lastModifiedTime())) {
                throw new IdentityUnavailableException(Reason.SOURCE_MISMATCH, "frozen entry source bytes or metadata changed");
            }
            return new SourceMeasurement(real, raw.length, sha, before.creationTime().toInstant(),
                    before.lastModifiedTime().toInstant(), Instant.now());
        } catch (IdentityUnavailableException error) { throw error; }
        catch (IOException | SecurityException error) {
            throw new IdentityUnavailableException(Reason.SOURCE_UNAVAILABLE, "entry source could not be measured", error);
        } catch (NoSuchAlgorithmException error) { throw new IllegalStateException("required SHA-256 unavailable", error); }
    }
}
