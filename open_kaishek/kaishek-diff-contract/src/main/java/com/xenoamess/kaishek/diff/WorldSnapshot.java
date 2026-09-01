package com.xenoamess.kaishek.diff;

import com.xenoamess.kaishek.profile.BuildFingerprint;
import java.time.Instant;
import java.util.*;

/** Canonical finite-world snapshot used by VM and CK3 differential runners. */
public record WorldSnapshot(BuildFingerprint fingerprint, Instant currentDate, long revision,
                            Map<String, EntityState> entities, Map<String, ResourceState> resources,
                            Map<String, String> variables, List<EventState> eventQueue) {
    public WorldSnapshot {
        fingerprint = Objects.requireNonNull(fingerprint, "fingerprint"); currentDate = Objects.requireNonNull(currentDate, "currentDate");
        if (revision < 0) throw new IllegalArgumentException("revision cannot be negative");
        entities = immutableMap(entities, "entities"); resources = immutableMap(resources, "resources");
        variables = immutableMap(variables, "variables");
        eventQueue = List.copyOf(Objects.requireNonNull(eventQueue, "eventQueue"));
    }
    private static <T> Map<String,T> immutableMap(Map<String,T> map, String name) {
        Objects.requireNonNull(map, name);
        if (map.entrySet().stream().anyMatch(e -> e.getKey() == null || e.getKey().isBlank()))
            throw new IllegalArgumentException(name + " contains blank key");
        if (map.values().stream().anyMatch(Objects::isNull))
            throw new IllegalArgumentException(name + " contains null value");
        return Collections.unmodifiableMap(new TreeMap<>(map));
    }
}
