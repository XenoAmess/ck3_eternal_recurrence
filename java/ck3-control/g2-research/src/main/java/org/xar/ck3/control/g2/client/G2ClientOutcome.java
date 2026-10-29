package org.xar.ck3.control.g2.client;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.g2.common.G2HttpError;

/** Consumer result of one pure evaluation; absence and a transport failure are different states. */
public sealed interface G2ClientOutcome {
    record Success(G2Evaluation evaluation) implements G2ClientOutcome {
        public Success { Objects.requireNonNull(evaluation, "evaluation"); }
    }

    enum UnavailableReason { PROVIDER_NOT_CONFIGURED, ENGINE_UNAVAILABLE }

    record Unavailable(UnavailableReason reason, String message,
            Optional<G2ClientException> failure) implements G2ClientOutcome {
        public Unavailable {
            Objects.requireNonNull(reason, "reason");
            requireMessage(message);
            Objects.requireNonNull(failure, "failure");
            if ((reason == UnavailableReason.PROVIDER_NOT_CONFIGURED) != failure.isEmpty()) {
                throw new IllegalArgumentException("only a configured engine refusal has HTTP evidence");
            }
            if (failure.isPresent() && (!engineUnavailable(failure.orElseThrow())
                    || !message.equals(failure.orElseThrow().getMessage()))) {
                throw new IllegalArgumentException("engine unavailable requires the original verified refusal");
            }
        }
    }

    record Failed(G2ClientException failure) implements G2ClientOutcome {
        public Failed {
            Objects.requireNonNull(failure, "failure");
            if (engineUnavailable(failure)) {
                throw new IllegalArgumentException("engine unavailable has its own typed branch");
            }
        }
    }

    static boolean engineUnavailable(G2ClientException failure) {
        return failure.reason() == G2ClientException.Reason.HTTP_REJECTED
                && failure.httpError().map(error -> error.code() == G2HttpError.Code.ENGINE_UNAVAILABLE).orElse(false);
    }

    static void requireMessage(String message) {
        if (message == null || message.isBlank() || message.length() > 512) {
            throw new IllegalArgumentException("bounded consumer outcome message required");
        }
        for (int index = 0; index < message.length(); index++) {
            char value = message.charAt(index);
            if (Character.isHighSurrogate(value)) {
                if (++index >= message.length() || !Character.isLowSurrogate(message.charAt(index))) {
                    throw new IllegalArgumentException("unpaired outcome message surrogate");
                }
            } else if (Character.isLowSurrogate(value)) {
                throw new IllegalArgumentException("unpaired outcome message surrogate");
            }
        }
    }
}
