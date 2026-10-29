package org.xar.ck3.control.application.action;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

public sealed interface PlanningReadResult<T> permits PlanningReadResult.Known, PlanningReadResult.Unavailable {
    record Known<T>(T value, PlanningReadReceipt receipt, org.xar.ck3.control.contracts.ExactRef originalReceipt) implements PlanningReadResult<T> {
        public Known { Objects.requireNonNull(value); Objects.requireNonNull(receipt); Objects.requireNonNull(originalReceipt); }
    }
    record Unavailable<T>(String reason, Optional<NativeActionPort.DispatchOutcome> original,
            Optional<OriginalReadDecodeFailure> decodeFailure,
            Optional<PlanningReadFailure> observedFailure) implements PlanningReadResult<T> {
        /** Failures without a qualified real after guard remain explicitly unobserved. */
        public Unavailable(String reason, Optional<NativeActionPort.DispatchOutcome> original) {
            this(reason, original, Optional.empty(), Optional.empty());
        }
        public Unavailable(String reason, Optional<NativeActionPort.DispatchOutcome> original,
                Optional<OriginalReadDecodeFailure> decodeFailure) {
            this(reason, original, decodeFailure, Optional.empty());
        }
        public Unavailable {
            StrictJson.text(reason); original = Objects.requireNonNull(original);
            decodeFailure = Objects.requireNonNull(decodeFailure); observedFailure = Objects.requireNonNull(observedFailure);
            StrictJson.require(decodeFailure.isEmpty() || original.orElse(null) instanceof NativeActionPort.AckReceived ack && ack.nativeOk(),
                    "live decode failure requires the actual successful original READ ACK");
            if (observedFailure.isPresent())
                StrictJson.require(original.filter(observedFailure.orElseThrow().original()::equals).isPresent(),
                        "failed-read after observation belongs to another original outcome");
        }
    }
}
