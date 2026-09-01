package com.xenoamess.kaishek.diff;

import java.util.*;

public record EventState(String id, String eventType, String dueAt, Map<String, String> context) {
    public EventState {
        if (id == null || id.isBlank() || eventType == null || eventType.isBlank()) throw new IllegalArgumentException("event id/type is blank");
        dueAt = requireNonBlank(dueAt, "dueAt"); context = immutableContext(context);
    }

    private static String requireNonBlank(String value, String name) {
        if (value == null || value.isBlank()) throw new IllegalArgumentException(name + " is blank");
        return value;
    }

    private static Map<String, String> immutableContext(Map<String, String> context) {
        Objects.requireNonNull(context, "context");
        if (context.entrySet().stream().anyMatch(e -> e.getKey() == null || e.getKey().isBlank()))
            throw new IllegalArgumentException("context contains blank key");
        if (context.values().stream().anyMatch(Objects::isNull))
            throw new IllegalArgumentException("context contains null value");
        return Collections.unmodifiableMap(new TreeMap<>(context));
    }
}
