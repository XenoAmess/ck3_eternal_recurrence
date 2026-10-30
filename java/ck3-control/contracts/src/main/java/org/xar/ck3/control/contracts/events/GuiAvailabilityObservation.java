package org.xar.ck3.control.contracts.events;

import java.util.Objects;

/** Independent stock GUI observation; an absent observation never asserts a GUI result. */
public sealed interface GuiAvailabilityObservation permits GuiAvailabilityObservation.Observed,
        GuiAvailabilityObservation.LegacyNotReported, GuiAvailabilityObservation.Unobserved {
    /** Preserve the existing raw-byte policy only when no stock GUI result was observed. */
    default boolean permitsSelectionWithRawFallback(boolean rawEnabled) {
        return this instanceof Observed observed ? observed.isValid() : rawEnabled;
    }

    record Observed(boolean isValid) implements GuiAvailabilityObservation { }
    /** The exact v1 packet had no GUI-observation member. */
    record LegacyNotReported() implements GuiAvailabilityObservation { }
    enum Reason {
        NATIVE_BINDING_UNAVAILABLE("native_binding_unavailable"),
        NATIVE_READ_UNAVAILABLE("native_read_unavailable");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Reason fromWire(String value) {
            Objects.requireNonNull(value);
            for (Reason reason : values()) if (reason.wire.equals(value)) return reason;
            throw new IllegalArgumentException("unknown GUI observation unavailable reason");
        }
    }
    record Unobserved(Reason reason) implements GuiAvailabilityObservation {
        public Unobserved { Objects.requireNonNull(reason); }
    }
}
