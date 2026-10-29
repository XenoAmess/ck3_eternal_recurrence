package org.xar.ck3.control.wave3.runtime.processcustody;

import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.stdioidentity.ProcessIdentityClaimV1;

/** Independent native wait signal and exit-code observations; 259 never decides liveness. */
public record ProcessObservationV1(ProcessIdentityClaimV1 identity, OptionalLong waitResult,
        KernelSignal signal, OptionalLong exitCode, Optional<ObservationError> error) {
    public enum KernelSignal { UNKNOWN, UNSIGNALED, SIGNALED }
    public enum ErrorStage { CLOSED, WAIT, EXIT_CODE }

    public record ObservationError(ErrorStage stage, String type, String message) {
        public ObservationError {
            Objects.requireNonNull(stage); Objects.requireNonNull(type); Objects.requireNonNull(message);
            StrictJson.text(type);
            if (!message.isEmpty()) { StrictJson.text(message); }
        }
    }

    public ProcessObservationV1 {
        Objects.requireNonNull(identity); Objects.requireNonNull(waitResult); Objects.requireNonNull(signal);
        Objects.requireNonNull(exitCode); Objects.requireNonNull(error);
        if (exitCode.isPresent()) {
            StrictJson.require(exitCode.getAsLong() >= 0 && exitCode.getAsLong() <= 0xffff_ffffL,
                    "actual exit code must be a DWORD");
        }
        if (signal != KernelSignal.UNKNOWN) {
            StrictJson.require(waitResult.isPresent()
                    && waitResult.getAsLong() == (signal == KernelSignal.SIGNALED ? 0 : 258),
                    "native wait result and signal must agree");
        }
        if (error.isEmpty()) {
            StrictJson.require(signal != KernelSignal.UNKNOWN && exitCode.isPresent(),
                    "complete actual wait and exit-code observations required");
        } else {
            ErrorStage stage = error.orElseThrow().stage();
            StrictJson.require(exitCode.isEmpty(), "failed observation cannot invent an exit code");
            if (stage == ErrorStage.EXIT_CODE) {
                StrictJson.require(signal != KernelSignal.UNKNOWN, "exit query error must retain known wait signal");
            } else {
                StrictJson.require(signal == KernelSignal.UNKNOWN, "wait/closed error must remain unknown");
                StrictJson.require(waitResult.isEmpty()
                        || waitResult.getAsLong() != 0 && waitResult.getAsLong() != 258,
                        "known native wait signal cannot be discarded by a wait error");
                if (stage == ErrorStage.CLOSED) {
                    StrictJson.require(waitResult.isEmpty(), "closed handle must not perform a new wait");
                }
            }
        }
    }
}
