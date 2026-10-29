package org.xar.ck3.control.g2.client;

import java.net.URI;
import java.time.Duration;
import java.util.Objects;
import org.xar.ck3.control.g2.common.G2Wire;

/** Explicit local pure-evaluation transport budget; never an action authority. */
public record G2ClientConfig(URI baseUri, Duration deadline, int maximumResponseBytes) {
    public G2ClientConfig {
        Objects.requireNonNull(baseUri, "baseUri");
        Objects.requireNonNull(deadline, "deadline");
        String path = baseUri.getRawPath();
        if (!"http".equals(baseUri.getScheme()) || !"127.0.0.1".equals(baseUri.getHost())
                || baseUri.getPort() < 1 || baseUri.getPort() > 65535
                || baseUri.getRawUserInfo() != null || baseUri.getRawQuery() != null
                || baseUri.getRawFragment() != null || !(path.isEmpty() || "/".equals(path))) {
            throw new IllegalArgumentException("explicit http://127.0.0.1:<port> base URI required");
        }
        if (deadline.isNegative() || deadline.isZero() || maximumResponseBytes < 1 || maximumResponseBytes > G2Wire.MAX_RESPONSE_BYTES) {
            throw new IllegalArgumentException("positive finite deadline and response budget within G2 wire role required");
        }
        try {
            deadline.toNanos();
        } catch (ArithmeticException error) {
            throw new IllegalArgumentException("deadline cannot exceed the monotonic timer range", error);
        }
    }
}
