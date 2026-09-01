package com.xenoamess.kaishek.profile;

import java.util.*;

/** Immutable opcode allow-list for one exact profile. */
public final class OpcodeRegistry {
    private final Map<String, OpcodeDescriptor> descriptors;

    public OpcodeRegistry(Collection<OpcodeDescriptor> descriptors) {
        Objects.requireNonNull(descriptors, "descriptors");
        var map = new TreeMap<String, OpcodeDescriptor>();
        for (var descriptor : descriptors) {
            Objects.requireNonNull(descriptor, "descriptors contains null");
            if (map.putIfAbsent(descriptor.id(), descriptor) != null)
                throw new IllegalArgumentException("duplicate opcode: " + descriptor.id());
        }
        this.descriptors = Collections.unmodifiableMap(map);
    }
    public OpcodeRegistry(Map<String, OpcodeDescriptor> descriptors) {
        Objects.requireNonNull(descriptors, "descriptors");
        var values = new ArrayList<OpcodeDescriptor>(descriptors.size());
        for (var entry : descriptors.entrySet()) {
            Objects.requireNonNull(entry.getKey(), "descriptors contains null key");
            var descriptor = Objects.requireNonNull(entry.getValue(),
                    "descriptors contains null value");
            if (!entry.getKey().equals(descriptor.id())) {
                throw new IllegalArgumentException("opcode map key does not match descriptor id: "
                        + entry.getKey() + " != " + descriptor.id());
            }
            values.add(descriptor);
        }
        var map = new TreeMap<String, OpcodeDescriptor>();
        for (var descriptor : values) {
            if (map.putIfAbsent(descriptor.id(), descriptor) != null)
                throw new IllegalArgumentException("duplicate opcode: " + descriptor.id());
        }
        this.descriptors = Collections.unmodifiableMap(map);
    }
    public static OpcodeRegistry empty() { return new OpcodeRegistry(List.of()); }
    public Optional<OpcodeDescriptor> find(String id) {
        return id == null ? Optional.empty() : Optional.ofNullable(descriptors.get(id));
    }
    public OpcodeDescriptor require(String id) {
        return find(id).orElseThrow(() -> new IllegalArgumentException("unregistered opcode: " + id));
    }
    public boolean contains(String id) { return id != null && descriptors.containsKey(id); }
    public int size() { return descriptors.size(); }
    public Collection<OpcodeDescriptor> all() { return descriptors.values(); }
    public OpcodeRegistry with(OpcodeDescriptor descriptor) {
        Objects.requireNonNull(descriptor, "descriptor");
        var copy = new ArrayList<>(descriptors.values()); copy.add(descriptor); return new OpcodeRegistry(copy);
    }
}
