package org.xar.ck3.control.warpolicy;

import java.util.Objects;
import java.util.Optional;

/** Missing, explicit null and a present value have different JSON representations. */
public sealed interface JsonPresence<T> {
    Optional<T> valueIfPresent();
    record Missing<T>() implements JsonPresence<T> {
        @Override public Optional<T> valueIfPresent() { return Optional.empty(); }
    }
    record Null<T>() implements JsonPresence<T> {
        @Override public Optional<T> valueIfPresent() { return Optional.empty(); }
    }
    record Value<T>(T value) implements JsonPresence<T> {
        public Value { Objects.requireNonNull(value, "present JSON value"); }
        @Override public Optional<T> valueIfPresent() { return Optional.of(value); }
    }
}
