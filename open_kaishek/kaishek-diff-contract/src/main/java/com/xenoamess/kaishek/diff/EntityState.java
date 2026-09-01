package com.xenoamess.kaishek.diff;

import java.util.*;

public record EntityState(String id, String type, Map<String, String> fields) {
    public EntityState {
        if (id == null || id.isBlank() || type == null || type.isBlank()) throw new IllegalArgumentException("entity id/type is blank");
        fields = immutableFields(fields);
    }

    private static Map<String, String> immutableFields(Map<String, String> fields) {
        Objects.requireNonNull(fields, "fields");
        if (fields.entrySet().stream().anyMatch(e -> e.getKey() == null || e.getKey().isBlank()))
            throw new IllegalArgumentException("fields contains blank key");
        if (fields.values().stream().anyMatch(Objects::isNull))
            throw new IllegalArgumentException("fields contains null value");
        return Collections.unmodifiableMap(new TreeMap<>(fields));
    }
}
