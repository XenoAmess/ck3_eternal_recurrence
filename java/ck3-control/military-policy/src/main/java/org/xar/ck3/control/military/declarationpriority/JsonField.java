package org.xar.ck3.control.military.declarationpriority;

import java.util.Objects;

/** Preserves the three JSON field states instead of silently coalescing them. */
public record JsonField<T>(Presence presence, T value) {
    public enum Presence { MISSING, NULL, VALUE }

    public JsonField {
        Objects.requireNonNull(presence, "presence");
        if ((presence == Presence.VALUE) != (value != null)) {
            throw new IllegalArgumentException("only VALUE fields have a non-null value");
        }
    }

    public static <T> JsonField<T> missing() { return new JsonField<>(Presence.MISSING, null); }
    public static <T> JsonField<T> nullValue() { return new JsonField<>(Presence.NULL, null); }
    public static <T> JsonField<T> of(T value) {
        return new JsonField<>(Presence.VALUE, Objects.requireNonNull(value, "value"));
    }

    public boolean hasValue() { return presence == Presence.VALUE; }
}
