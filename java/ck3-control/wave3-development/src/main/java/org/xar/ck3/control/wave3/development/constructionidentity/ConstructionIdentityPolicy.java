package org.xar.ck3.control.wave3.development.constructionidentity;

import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.wave2.runtime.creationtime.ProcessCreationTime;
import org.xar.ck3.control.wave2.runtime.stdioidentity.ProcessIdentityClaimV1;

/** Pure source-cache proposals. Claims supplied to this policy never become measured process proof. */
public final class ConstructionIdentityPolicy {
    private static final BigInteger TICKS_PER_SECOND = BigInteger.valueOf(10_000_000);
    private static final BigInteger TICKS_PER_MICROSECOND = BigInteger.TEN;
    private static final Instant FILETIME_EPOCH = Instant.parse("1601-01-01T00:00:00Z");
    private ConstructionIdentityPolicy() { }

    public record WmiFields(BigInteger pid, String executable, String creationDate) { }
    public record PinClaim(ProcessIdentityClaimV1 kernel, String originalCreationDate) {
        public PinClaim {
            Objects.requireNonNull(kernel);
            Objects.requireNonNull(originalCreationDate);
        }
    }
    public enum BeforeDecision { USE_EXISTING_PIN, REJECT_GENERATION_CHANGE, READ_ORIGINAL_PRODUCER }

    public static BeforeDecision beforeRead(Optional<PinClaim> pin, Optional<ProcessIdentityClaimV1> before) {
        Objects.requireNonNull(pin);
        Objects.requireNonNull(before);
        if (pin.isPresent() && before.isPresent() && pin.orElseThrow().kernel().sameGeneration(before.orElseThrow())) {
            return BeforeDecision.USE_EXISTING_PIN;
        }
        if (pin.isPresent() && before.isPresent() && before.orElseThrow().pid() == pin.orElseThrow().kernel().pid()) {
            return BeforeDecision.REJECT_GENERATION_CHANGE;
        }
        return BeforeDecision.READ_ORIGINAL_PRODUCER;
    }

    /** The source truncates only this WMI comparison to microseconds; the retained kernel claim stays full 100ns. */
    public static boolean matchesOriginalProducer(WmiFields identity, ProcessIdentityClaimV1 kernel) {
        Objects.requireNonNull(identity);
        Objects.requireNonNull(kernel);
        if (!BigInteger.valueOf(kernel.pid()).equals(identity.pid()) || identity.executable() == null
                || identity.executable().isEmpty() || identity.creationDate() == null) { return false; }
        try {
            Path image = Path.of(identity.executable()).toAbsolutePath().normalize();
            ProcessIdentityClaimV1 imageClaim = new ProcessIdentityClaimV1(kernel.pid(), kernel.creationFiletimeDecimal(), image);
            if (!kernel.sameGeneration(imageClaim)) { return false; }
            BigInteger ticks = new BigInteger(kernel.creationFiletimeDecimal());
            BigInteger[] seconds = ticks.divideAndRemainder(TICKS_PER_SECOND);
            Instant kernelMicrosecond = FILETIME_EPOCH.plusSeconds(seconds[0].longValueExact())
                    .plusNanos(seconds[1].divide(TICKS_PER_MICROSECOND).longValueExact() * 1000);
            return ProcessCreationTime.parse(identity.creationDate()).instant().equals(kernelMicrosecond);
        } catch (RuntimeException error) {
            return false;
        }
    }

    public static boolean mayProposePin(WmiFields identity, ProcessIdentityClaimV1 before,
                                        Optional<ProcessIdentityClaimV1> after) {
        Objects.requireNonNull(after);
        return after.isPresent() && before.sameGeneration(after.orElseThrow())
                && matchesOriginalProducer(identity, before);
    }
}
