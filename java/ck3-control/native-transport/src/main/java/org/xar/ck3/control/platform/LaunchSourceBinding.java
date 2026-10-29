package org.xar.ck3.control.platform;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild;

/** Launch configuration only. It does not attest historical source or build qualification. */
public final class LaunchSourceBinding {
    public record Review(String machineId, Instant expiresAt, ControlBuild.FileRef gameExecutable,
            ControlBuild.FileRef bridgeDll, ControlBuild.FileRef injector, NativeLaunchEvidence.Inputs nativeEvidence,
            Path nativeSourceRoot, List<ControlBuild.FileRef> completeRuntimeSources) {
        public Review {
            Objects.requireNonNull(gameExecutable);
            Objects.requireNonNull(bridgeDll);
            Objects.requireNonNull(injector);
            completeRuntimeSources = completeRuntimeSources == null ? List.of() : List.copyOf(completeRuntimeSources);
        }
    }

    private final Review review;
    private LaunchSourceBinding(Review review) { this.review = Objects.requireNonNull(review); }

    public static LaunchSourceBinding accept(Review review) {
        return new LaunchSourceBinding(review);
    }

    /** The historical reader parameter remains source compatible and is not invoked by launch. */
    public static LaunchSourceBinding accept(Review review, NativeLaunchEvidence.Port nativeReader) throws IOException {
        return accept(review);
    }

    public Review review() { return review; }

    /** No Native proof is created from ordinary configuration. */
    public NativeLaunchEvidence.Proof nativeProof() {
        throw new IllegalStateException("Ordinary launch configuration does not contain a Native proof");
    }

    /** Compatibility hook; launch configuration is not a source qualification. */
    public void verify() throws IOException { }

    /** Compatibility hook; loading code does not require a reviewed deployment manifest. */
    public void requireLoadedClass(Class<?> type) throws IOException {
        Objects.requireNonNull(type);
    }
}
