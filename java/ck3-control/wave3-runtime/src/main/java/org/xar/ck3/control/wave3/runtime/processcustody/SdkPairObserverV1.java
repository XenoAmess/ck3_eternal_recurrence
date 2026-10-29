package org.xar.ck3.control.wave3.runtime.processcustody;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.wave3.runtime.processcustody.ProcessObservationV1.KernelSignal;
import org.xar.ck3.control.wave3.runtime.processcustody.PublishedSdkPairClaimV1.Role;

/** In-memory counterpart of runtime_repair_status_v2.observe_sdk_pair, without file/incident writes. */
public final class SdkPairObserverV1 implements AutoCloseable {
    public enum Phase { NEW, CAPTURED, PARTIAL_CAPTURE_FAILURE, CLOSED }
    public record RoleObservation(Role role, ProcessObservationV1 observation) {
        public RoleObservation { Objects.requireNonNull(role); Objects.requireNonNull(observation); }
    }
    public record CaptureFailure(Role role, String type, String message) {
        public CaptureFailure { Objects.requireNonNull(role); Objects.requireNonNull(type); Objects.requireNonNull(message); }
    }
    public record Report(Phase phase, String originalPairSha256, List<RoleObservation> observations,
            Optional<CaptureFailure> captureFailure, boolean firstIncident) {
        public Report {
            Objects.requireNonNull(phase); Objects.requireNonNull(originalPairSha256);
            observations = List.copyOf(observations); Objects.requireNonNull(captureFailure);
        }
    }
    private record Captured(Role role, RetainedProcessGenerationV1 generation) { }

    private final PublishedSdkPairClaimV1 pair;
    private final RetainedProcessApi api;
    private final List<Captured> handles = new ArrayList<>(2);
    private Optional<CaptureFailure> captureFailure = Optional.empty();
    private Phase phase = Phase.NEW;
    private boolean incidentReported;

    public SdkPairObserverV1(PublishedSdkPairClaimV1 pair, RetainedProcessApi api) {
        this.pair = Objects.requireNonNull(pair); this.api = Objects.requireNonNull(api);
    }

    public static SdkPairObserverV1 system(PublishedSdkPairClaimV1 pair) {
        return new SdkPairObserverV1(pair, new Win32RetainedProcessApi());
    }

    public synchronized Report observe() {
        if (phase == Phase.NEW) {
            phase = Phase.CAPTURED;
            for (PublishedSdkPairClaimV1.Row row : pair.processes()) {
                try {
                    handles.add(new Captured(row.role(), RetainedProcessGenerationV1.capture(
                            ProcessExpectationV1.exact(row.identity()), api)));
                } catch (IOException | RuntimeException error) {
                    phase = Phase.PARTIAL_CAPTURE_FAILURE;
                    String message = error.getMessage() == null ? error.toString() : error.getMessage();
                    captureFailure = Optional.of(new CaptureFailure(row.role(), error.getClass().getSimpleName(),
                            truncateCodePoints(message, 1024)));
                    break; // Retain every prior handle; no second capture/retry is hidden here.
                }
            }
        }
        List<RoleObservation> observations = new ArrayList<>(handles.size());
        for (Captured handle : handles) {
            observations.add(new RoleObservation(handle.role(), handle.generation().observe()));
        }
        boolean failure = captureFailure.isPresent()
                || observations.stream().anyMatch(row -> row.observation().signal() == KernelSignal.SIGNALED);
        boolean first = !incidentReported && failure;
        if (first) { incidentReported = true; }
        return new Report(phase, pair.originalSha256(), observations, captureFailure, first);
    }

    @Override public synchronized void close() throws IOException {
        if (phase == Phase.CLOSED) { return; }
        phase = Phase.CLOSED;
        Throwable failure = null;
        for (Captured handle : handles) {
            try { handle.generation().close(); }
            catch (IOException | RuntimeException | Error error) {
                if (failure == null) { failure = error; }
                else if (failure != error) { failure.addSuppressed(error); }
            }
        }
        handles.clear();
        if (failure instanceof IOException error) { throw error; }
        if (failure instanceof RuntimeException error) { throw error; }
        if (failure instanceof Error error) { throw error; }
    }

    private static String truncateCodePoints(String value, int maximum) {
        return value.codePointCount(0, value.length()) <= maximum ? value
                : value.substring(0, value.offsetByCodePoints(0, maximum));
    }
}
