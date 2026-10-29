package org.xar.ck3.control.g2.context;

import java.util.Objects;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.Milestone;

/** Root-installed provenance capability. HTTP input can never install or replace it. */
public final class G2CallContextProducer {
    private G2CallContextProducer() { }

    /** Raw payload is one object token; surrounding envelope whitespace has no caller-byte identity. */
    public static void requirePayloadToken(ProjectionJson payload) {
        Objects.requireNonNull(payload);
        byte[] raw = payload.bytes();
        StrictJson.require(payload.isObject() && raw.length >= 2 && raw[0] == '{' && raw[raw.length - 1] == '}',
                "original object token bytes required without surrounding whitespace");
    }

    public record Context(G2Source source, String requestId, String payloadSha256) {
        public Context {
            Objects.requireNonNull(source, "source");
            StrictJson.require(requestId != null && requestId.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"),
                    "bounded original G2 request identity required");
            StrictJson.require(payloadSha256 != null && payloadSha256.matches("[0-9a-f]{64}"),
                    "exact original payload digest required");
        }
    }
    public sealed interface Result permits Available, Unavailable { }
    public record Available(Context context) implements Result {
        public Available { Objects.requireNonNull(context); }
    }
    public record Unavailable(Reason reason, String detail) implements Result {
        public Unavailable {
            Objects.requireNonNull(reason); StrictJson.text(detail);
            StrictJson.require(detail.length() <= 512, "bounded source diagnostic required");
        }
    }
    public enum Reason {
        ROOT_PROVIDER_MISSING, RETAINED_SOURCE_MISSING, CURRENT_SESSION_UNAVAILABLE,
        SOURCE_IDENTITY_CHANGED, SOURCE_REJECTED, EXACT_BUILD_UNAVAILABLE,
        OWNER_FAILED, REQUEST_SEQUENCE_EXHAUSTED
    }
    @FunctionalInterface
    public interface Provider {
        Result context(Milestone milestone, ProjectionJson payload);
    }

    /** Object identity freezes the one owner; no environment or body-derived fallback exists. */
    public static final class RootBinding {
        private final AtomicReference<Provider> provider = new AtomicReference<>();
        public void install(Provider value) {
            Objects.requireNonNull(value, "Root provenance provider");
            Provider prior = provider.get();
            if (prior == value) { return; }
            if (prior != null || !provider.compareAndSet(null, value)) {
                if (provider.get() != value) { throw new IllegalStateException("Root G2 source owner cannot hot-rebind"); }
            }
        }
        public Result context(Milestone milestone, ProjectionJson payload) {
            Objects.requireNonNull(milestone); Objects.requireNonNull(payload);
            requirePayloadToken(payload);
            Provider actual = provider.get();
            if (actual == null) { return new Unavailable(Reason.ROOT_PROVIDER_MISSING, "Root retained-source provider is unavailable"); }
            Result result = Objects.requireNonNull(actual.context(milestone, payload), "explicit source result required");
            if (provider.get() != actual) { return new Unavailable(Reason.SOURCE_IDENTITY_CHANGED, "Root source owner changed"); }
            if (result instanceof Available available
                    && !available.context().payloadSha256().equals(G2RetainedNativeSourceProvider.sha256(payload.bytes()))) {
                return new Unavailable(Reason.SOURCE_REJECTED, "provider context does not bind the original payload bytes");
            }
            return result;
        }
    }
}
