package org.xar.ck3.control.wave3.runtime.processcustody;

import java.io.IOException;
import java.io.InvalidObjectException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.ObjectStreamException;
import java.io.Serial;
import java.io.Serializable;
import java.nio.file.Path;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import org.xar.ck3.control.wave2.runtime.stdioidentity.ProcessIdentityClaimV1;
import org.xar.ck3.control.wave3.runtime.processcustody.ProcessObservationV1.ErrorStage;
import org.xar.ck3.control.wave3.runtime.processcustody.ProcessObservationV1.KernelSignal;
import org.xar.ck3.control.wave3.runtime.processcustody.ProcessObservationV1.ObservationError;

public final class ProcessCustodyUnavailableException extends IOException {
    @Serial private static final long serialVersionUID = 1L;
    // Only the validated immutable value is retained in memory. Its platform Path and Optional
    // implementation objects are deliberately absent from the Java serialization object graph.
    private transient ProcessObservationV1 observation;

    public ProcessCustodyUnavailableException(String message, ProcessObservationV1 observation) {
        super(message);
        this.observation = Objects.requireNonNull(observation);
    }

    public ProcessObservationV1 observation() { return observation; }

    @Serial private void writeObject(ObjectOutputStream output) throws IOException {
        output.defaultWriteObject();
        output.writeObject(SerializedObservation.from(Objects.requireNonNull(observation)));
    }
    @Serial private void readObject(ObjectInputStream input) throws IOException, ClassNotFoundException {
        input.defaultReadObject();
        Object encoded = input.readObject();
        if (!(encoded instanceof SerializedObservation value)) {
            throw new InvalidObjectException("typed serialized process observation required");
        }
        try { observation = value.toObservation(); }
        catch (RuntimeException error) {
            InvalidObjectException invalid = new InvalidObjectException("invalid serialized process observation");
            invalid.initCause(error); throw invalid;
        }
    }
    @Serial private void readObjectNoData() throws ObjectStreamException {
        throw new InvalidObjectException("serialized process observation is missing");
    }

    /** Flat scalar transport only; reconstruction runs the existing identity/observation contracts. */
    private record SerializedObservation(long pid, String creationFiletimeDecimal, String executable,
            boolean waitPresent, long waitResult, KernelSignal signal, boolean exitPresent, long exitCode,
            ErrorStage errorStage, String errorType, String errorMessage) implements Serializable {
        @Serial private static final long serialVersionUID = 1L;
        private SerializedObservation {
            Objects.requireNonNull(creationFiletimeDecimal); Objects.requireNonNull(executable); Objects.requireNonNull(signal);
            if ((!waitPresent && waitResult != 0) || (!exitPresent && exitCode != 0)
                    || (errorStage == null ? errorType != null || errorMessage != null : errorType == null || errorMessage == null)) {
                throw new IllegalArgumentException("exact serialized optional process fields required");
            }
        }
        private static SerializedObservation from(ProcessObservationV1 value) {
            ObservationError error = value.error().orElse(null);
            return new SerializedObservation(value.identity().pid(), value.identity().creationFiletimeDecimal(),
                    value.identity().executable().toString(), value.waitResult().isPresent(), value.waitResult().orElse(0),
                    value.signal(), value.exitCode().isPresent(), value.exitCode().orElse(0),
                    error == null ? null : error.stage(), error == null ? null : error.type(), error == null ? null : error.message());
        }
        private ProcessObservationV1 toObservation() {
            ProcessIdentityClaimV1 identity = new ProcessIdentityClaimV1(pid, creationFiletimeDecimal, Path.of(executable));
            Optional<ObservationError> error = errorStage == null ? Optional.empty()
                    : Optional.of(new ObservationError(errorStage, errorType, errorMessage));
            return new ProcessObservationV1(identity, waitPresent ? OptionalLong.of(waitResult) : OptionalLong.empty(), signal,
                    exitPresent ? OptionalLong.of(exitCode) : OptionalLong.empty(), error);
        }
    }
}
