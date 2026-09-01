package com.xenoamess.kaishek.runtime;

import java.util.Objects;

public record TypedValue(Type type, Object value) {
    public enum Type { INTEGER, DECIMAL, BOOLEAN, STRING, SCOPE, LIST }
    public TypedValue { Objects.requireNonNull(type); Objects.requireNonNull(value); }
    public static TypedValue of(Object value) {
        if (value instanceof Integer || value instanceof Long) return new TypedValue(Type.INTEGER, value);
        if (value instanceof Number) return new TypedValue(Type.DECIMAL, value);
        if (value instanceof Boolean) return new TypedValue(Type.BOOLEAN, value);
        if (value instanceof String) return new TypedValue(Type.STRING, value);
        if (value instanceof ScopeRef) return new TypedValue(Type.SCOPE, value);
        if (value instanceof java.util.List<?>) return new TypedValue(Type.LIST, java.util.List.copyOf((java.util.List<?>) value));
        throw new IllegalArgumentException("unsupported value type: " + value.getClass());
    }
}
