package org.xar.ck3.control.g2.client;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.g2.common.G2Request;

/** Borrowed-client port for resident consumers. It performs one evaluation and never retries. */
public final class G2ClientEvaluationPort {
    private final Optional<G2JavaClient> client;
    private final String unavailableMessage;

    public G2ClientEvaluationPort(G2JavaClient client) {
        this.client = Optional.of(Objects.requireNonNull(client, "client"));
        unavailableMessage = "";
    }

    private G2ClientEvaluationPort(String unavailableMessage) {
        G2ClientOutcome.requireMessage(unavailableMessage);
        client = Optional.empty();
        this.unavailableMessage = unavailableMessage;
    }

    public static G2ClientEvaluationPort unavailable(String reason) {
        return new G2ClientEvaluationPort(reason);
    }

    public G2ClientOutcome evaluate(G2Request request) {
        if (client.isEmpty()) {
            return new G2ClientOutcome.Unavailable(G2ClientOutcome.UnavailableReason.PROVIDER_NOT_CONFIGURED,
                    unavailableMessage, Optional.empty());
        }
        try {
            return new G2ClientOutcome.Success(client.orElseThrow().evaluateWithEvidence(request));
        } catch (G2ClientException failure) {
            if (G2ClientOutcome.engineUnavailable(failure)) {
                return new G2ClientOutcome.Unavailable(G2ClientOutcome.UnavailableReason.ENGINE_UNAVAILABLE,
                        failure.getMessage(), Optional.of(failure));
            }
            return new G2ClientOutcome.Failed(failure);
        }
    }
}
