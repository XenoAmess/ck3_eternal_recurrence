package org.xar.ck3.control.wave2.runtime.deadlinetransport;

import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.metrics.DecisionMetricRecorder;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Acknowledgements;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.NativeObservation;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Stage;

/** One invocation through existing authority. This adapter creates no pipe, process, HTTP client or ledger writer. */
public final class DeadlineTransportAdapter {
    private DeadlineTransportAdapter() { }

    @FunctionalInterface
    public interface OriginalDeadlineAuthority {
        /** Must call the existing driver under its original custody and retain full snapshots/actions itself. */
        byte[] advance(DeadlineTransport.PreparedRequest request) throws IOException;
    }

    public enum State { PREPARED, IN_FLIGHT, OBSERVED, UNKNOWN }

    public static final class UnknownOutcomeException extends IOException {
        private static final long serialVersionUID = 1L;
        private final String invocationId;
        UnknownOutcomeException(String invocationId, Throwable cause) {
            super("native deadline outcome requires original authority reconciliation; replay forbidden", cause);
            this.invocationId = invocationId;
        }
        public String invocationId() { return invocationId; }
        public boolean replayAllowed() { return false; }
    }

    /** In-memory duplicate suppression supplements, and never replaces, the original durable UNKNOWN/ledger guard. */
    public static final class Invocation {
        private final DeadlineTransport.PreparedRequest request;
        private final AtomicReference<State> state = new AtomicReference<>(State.PREPARED);
        public Invocation(DeadlineTransport.PreparedRequest request) { this.request = Objects.requireNonNull(request); }
        public State state() { return state.get(); }
        public String invocationId() { return request.invocationId(); }

        public DeadlineTransport.Observation run(OriginalDeadlineAuthority authority) throws UnknownOutcomeException {
            return execute(authority, Optional.empty());
        }

        /** Observes this same original authority invocation; metrics grant no deadline, dispatch or replay permission. */
        public DeadlineTransport.Observation run(OriginalDeadlineAuthority authority, DecisionMetricRecorder metrics) throws UnknownOutcomeException {
            return execute(authority, Optional.of(Objects.requireNonNull(metrics, "metrics")));
        }

        private DeadlineTransport.Observation execute(OriginalDeadlineAuthority authority, Optional<DecisionMetricRecorder> recording)
                throws UnknownOutcomeException {
            Objects.requireNonNull(authority, "authority");
            Objects.requireNonNull(recording, "recording");
            recording.ifPresent(metrics -> StrictJson.require(metrics.context().requestId().equals(request.invocationId()),
                    "metrics request differs from actual native invocation"));
            if (!state.compareAndSet(State.PREPARED, State.IN_FLIGHT)) {
                throw new IllegalStateException("original invocation has already started; replay forbidden");
            }
            try {
                byte[] originalProjection = recording.isEmpty() ? authority.advance(request)
                        : recording.orElseThrow().measure(Stage.NATIVE_AUTHORITY, () -> authority.advance(request));
                DeadlineTransport.Completion completion = recording.isEmpty() ? DeadlineTransportCodec.completion(originalProjection)
                        : recording.orElseThrow().measure(Stage.NATIVE_ACK_OBSERVATION, () -> DeadlineTransportCodec.completion(originalProjection));
                recording.ifPresent(metrics -> {
                    int accepted = Math.toIntExact(completion.ownActions().stream().filter(action -> action.result().accepted()).count());
                    metrics.acknowledged(new Acknowledgements(completion.ownActions().size(), accepted,
                            DecisionMetricRecorder.sha256(originalProjection)));
                });
                DeadlineTransport.Observation observation = recording.isEmpty() ? DeadlineTransport.observe(request, completion)
                        : recording.orElseThrow().measure(Stage.POSTSTATE_VALIDATION, () -> DeadlineTransport.observe(request, completion));
                if (recording.isPresent()) {
                    DecisionMetricRecorder metrics = recording.orElseThrow();
                    metrics.measure(Stage.GAME_DATE_OBSERVATION, () -> {
                        var actions = observation.completion().ownActions();
                        int accepted = Math.toIntExact(actions.stream().filter(action -> action.result().accepted()).count());
                        metrics.nativeObserved(new NativeObservation(actions.size(), accepted, request.starting().dateRaw(),
                                observation.completion().current().dateRaw(), DecisionMetricRecorder.sha256(originalProjection)));
                        return observation;
                    });
                }
                state.set(State.OBSERVED);
                return observation;
            } catch (InterruptedException failure) {
                Thread.currentThread().interrupt(); state.set(State.UNKNOWN);
                throw new UnknownOutcomeException(request.invocationId(), failure);
            } catch (IOException | RuntimeException failure) {
                // A transport return or malformed poststate cannot prove that effects never happened.
                state.set(State.UNKNOWN);
                throw new UnknownOutcomeException(request.invocationId(), failure);
            } finally {
                state.compareAndSet(State.IN_FLIGHT, State.UNKNOWN);
            }
        }
    }
}
