package org.xar.ck3.control.wave3.development.constructionidentity;

import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.stdioidentity.MeasuredProcessIdentity;
import org.xar.ck3.control.wave2.runtime.stdioidentity.ProcessIdentityClaimV1;
import org.xar.ck3.control.wave2.runtime.stdioidentity.ProcessIdentityReader;
import org.xar.ck3.control.wave3.development.constructionidentity.ConstructionIdentityPolicy.BeforeDecision;
import org.xar.ck3.control.wave3.development.constructionidentity.ConstructionIdentityPolicy.PinClaim;

/** Read-only original construction identity cache. Reuses the shared reader; owns no Win32 implementation. */
public final class ConstructionProcessIdentityCache {
    @FunctionalInterface
    public interface OriginalIdentityProducer {
        Optional<OriginalProcessIdentity> read(long pid) throws IOException;
    }

    /** A driver owns its one retention slot. A slot-only driver can return false from tryRetain. */
    public interface PinRetention {
        Optional<VerifiedPin> current();
        boolean tryRetain(VerifiedPin pin);
    }

    /** Only this cache can construct a pin, after two actual kernel observations and the original WMI match. */
    public static final class VerifiedPin {
        private final PinClaim claim;
        private VerifiedPin(MeasuredProcessIdentity before, MeasuredProcessIdentity after, String originalCreationDate) {
            StrictJson.require(before.identity().sameGeneration(after.identity()), "kernel changed while learning construction pin");
            claim = new PinClaim(before.identity(), originalCreationDate);
        }
        public PinClaim claim() { return claim; }
    }

    public static final class MemoryRetention implements PinRetention {
        private VerifiedPin pin;
        @Override public synchronized Optional<VerifiedPin> current() { return Optional.ofNullable(pin); }
        @Override public synchronized boolean tryRetain(VerifiedPin value) {
            pin = Objects.requireNonNull(value);
            return true;
        }
    }

    public static final class DisabledRetention implements PinRetention {
        @Override public Optional<VerifiedPin> current() { return Optional.empty(); }
        @Override public boolean tryRetain(VerifiedPin pin) { Objects.requireNonNull(pin); return false; }
    }

    public sealed interface Result permits CachedIdentity, ProducerIdentity, NoIdentity { }
    public static final class CachedIdentity implements Result {
        private final long pid;
        private final String originalCreationDate;
        private final MeasuredProcessIdentity freshKernelObservation;
        private CachedIdentity(long pid, String originalCreationDate, MeasuredProcessIdentity observed) {
            this.pid = pid;
            this.originalCreationDate = Objects.requireNonNull(originalCreationDate);
            freshKernelObservation = Objects.requireNonNull(observed);
        }
        public long pid() { return pid; }
        public String originalCreationDate() { return originalCreationDate; }
        public MeasuredProcessIdentity freshKernelObservation() { return freshKernelObservation; }
    }
    public record ProducerIdentity(OriginalProcessIdentity original) implements Result {
        public ProducerIdentity { Objects.requireNonNull(original); }
    }
    public record NoIdentity() implements Result { }

    public static final class GenerationChangedException extends IOException {
        private static final long serialVersionUID = 1L;
        public GenerationChangedException() { super("construction process generation or image changed"); }
    }

    private final ProcessIdentityReader kernelReader;
    private final PinRetention retention;
    public ConstructionProcessIdentityCache(ProcessIdentityReader kernelReader, PinRetention retention) {
        this.kernelReader = Objects.requireNonNull(kernelReader);
        this.retention = Objects.requireNonNull(retention);
    }

    /** Kernel access/platform failures preserve the original producer path; its own exceptions propagate. */
    public synchronized Result read(long pid, OriginalIdentityProducer originalProducer) throws IOException {
        StrictJson.require(pid >= 1 && pid <= 0xffff_ffffL, "positive DWORD construction PID required");
        Objects.requireNonNull(originalProducer);
        Optional<VerifiedPin> pin = Objects.requireNonNull(retention.current());
        Optional<MeasuredProcessIdentity> before = tryKernel(pid);
        BeforeDecision decision = ConstructionIdentityPolicy.beforeRead(pin.map(VerifiedPin::claim), before.map(MeasuredProcessIdentity::identity));
        if (decision == BeforeDecision.USE_EXISTING_PIN) {
            return new CachedIdentity(pid, pin.orElseThrow().claim().originalCreationDate(), before.orElseThrow());
        }
        if (decision == BeforeDecision.REJECT_GENERATION_CHANGE) { throw new GenerationChangedException(); }
        Optional<OriginalProcessIdentity> identity = Objects.requireNonNull(originalProducer.read(pid));
        if (before.isPresent() && identity.isPresent()
                && ConstructionIdentityPolicy.matchesOriginalProducer(identity.orElseThrow().fields(), before.orElseThrow().identity())) {
            Optional<MeasuredProcessIdentity> after = tryKernel(pid);
            if (after.isPresent() && before.orElseThrow().identity().sameGeneration(after.orElseThrow().identity())) {
                retention.tryRetain(new VerifiedPin(before.orElseThrow(), after.orElseThrow(), identity.orElseThrow().fields().creationDate()));
            }
        }
        return identity.<Result>map(ProducerIdentity::new).orElseGet(NoIdentity::new);
    }

    public static byte[] encode(Result result) {
        Objects.requireNonNull(result);
        return switch (result) {
            case CachedIdentity cached -> OriginalProcessIdentityJson.cached(cached.pid(), cached.originalCreationDate());
            case ProducerIdentity producer -> producer.original().originalUtf8();
            case NoIdentity ignored -> new byte[]{'n', 'u', 'l', 'l'};
        };
    }

    private Optional<MeasuredProcessIdentity> tryKernel(long pid) {
        try {
            MeasuredProcessIdentity observed = kernelReader.observe(pid);
            return observed != null && observed.pid() == pid ? Optional.of(observed) : Optional.empty();
        } catch (IOException | RuntimeException error) { return Optional.empty(); }
    }
}
