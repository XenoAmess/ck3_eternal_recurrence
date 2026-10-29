package org.xar.ck3.control.wave2.finance.factionthreat;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;

import static org.xar.ck3.control.wave2.finance.factionthreat.FactionThreatObserver.*;

/** Narrow adapter for the already owned driver; it has no native pipe or arbitrary command API. */
public final class ExistingFactionAlertAdapter implements ExistingAlertReader {
    public interface ExistingDriverPort {
        List<String> existingBridgeCapabilities();
        Invocation queryPlayerFactionAlerts(BigInteger expectedRevision);
    }

    public sealed interface Invocation permits ObserverPacket, ObserverUnavailable { }
    public static final class ObserverPacket implements Invocation {
        private final byte[] json;
        public ObserverPacket(byte[] json) {
            Objects.requireNonNull(json, "json");
            if (json.length == 0 || json.length > FactionThreatCodec.MAX_BYTES) {
                throw new IllegalArgumentException("observer packet byte limit");
            }
            this.json = json.clone();
        }
        public byte[] json() { return json.clone(); }
    }
    public record ObserverUnavailable(ReadFailureKind kind, String error) implements Invocation {
        public ObserverUnavailable {
            Objects.requireNonNull(kind, "kind");
            Objects.requireNonNull(error, "error");
        }
    }

    private final ExistingDriverPort driver;

    public ExistingFactionAlertAdapter(ExistingDriverPort driver) { this.driver = Objects.requireNonNull(driver, "driver"); }

    @Override public boolean supportsExistingObserver() {
        return List.copyOf(driver.existingBridgeCapabilities()).contains(CAPABILITY);
    }

    @Override public ReadResult readExistingObserver(BigInteger expectedRevision) {
        Objects.requireNonNull(expectedRevision, "expectedRevision");
        if (expectedRevision.signum() <= 0 || expectedRevision.bitLength() > 64) {
            throw new IllegalArgumentException("expected revision must be uint64");
        }
        Invocation invocation = Objects.requireNonNull(driver.queryPlayerFactionAlerts(expectedRevision), "invocation");
        if (invocation instanceof ObserverUnavailable unavailable) {
            return new ReadUnavailable(unavailable.kind(), unavailable.error());
        }
        return new AlertRead(FactionThreatCodec.decodeExistingObserverResult(((ObserverPacket) invocation).json()));
    }
}
