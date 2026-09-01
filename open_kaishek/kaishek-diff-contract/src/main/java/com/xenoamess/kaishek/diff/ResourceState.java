package com.xenoamess.kaishek.diff;

public record ResourceState(String ownerId, String resource, long amount, long reserved) {
    public ResourceState {
        if (ownerId == null || ownerId.isBlank() || resource == null || resource.isBlank()) throw new IllegalArgumentException("owner/resource is blank");
        if (amount < 0) throw new IllegalArgumentException("amount cannot be negative");
        if (reserved < 0) throw new IllegalArgumentException("reserved cannot be negative");
        if (reserved > amount) throw new IllegalArgumentException("reserved cannot exceed amount");
    }
}
