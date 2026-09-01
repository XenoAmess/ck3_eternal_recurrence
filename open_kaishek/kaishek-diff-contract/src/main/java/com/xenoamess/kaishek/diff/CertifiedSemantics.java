package com.xenoamess.kaishek.diff;

import com.xenoamess.kaishek.profile.BuildFingerprint;
import java.time.Instant;
import java.util.*;

public record CertifiedSemantics(String profileId, BuildFingerprint fingerprint, Set<String> opcodeIds,
                                 String inputShape, Set<String> scopeTypes, Map<String, String> artifactIndex,
                                 Instant certifiedAt, String runtimeCommit, String modCommit, String mcpCapability,
                                 Set<String> limitations, Set<String> failureConditions, CertificationStatus status) {
    public CertifiedSemantics {
        if (profileId == null || profileId.isBlank() || inputShape == null || inputShape.isBlank()) throw new IllegalArgumentException("profileId/inputShape is blank");
        fingerprint = Objects.requireNonNull(fingerprint, "fingerprint");
        opcodeIds = nonBlankSet(opcodeIds, "opcodeIds");
        scopeTypes = nonBlankSet(scopeTypes, "scopeTypes");
        artifactIndex = immutableArtifactIndex(artifactIndex);
        certifiedAt = Objects.requireNonNull(certifiedAt, "certifiedAt"); runtimeCommit = require(runtimeCommit, "runtimeCommit"); modCommit = require(modCommit, "modCommit"); mcpCapability = require(mcpCapability, "mcpCapability");
        limitations = nonBlankSet(limitations, "limitations");
        failureConditions = nonBlankSet(failureConditions, "failureConditions");
        status = Objects.requireNonNull(status, "status");
    }
    private static String require(String s, String n) { if (s == null || s.isBlank()) throw new IllegalArgumentException(n + " is blank"); return s; }
    private static Set<String> nonBlankSet(Set<String> values, String name) {
        Objects.requireNonNull(values, name);
        if (values.stream().anyMatch(v -> v == null || v.isBlank()))
            throw new IllegalArgumentException(name + " contains blank value");
        return Set.copyOf(values);
    }
    private static Map<String, String> immutableArtifactIndex(Map<String, String> values) {
        Objects.requireNonNull(values, "artifactIndex");
        if (values.entrySet().stream().anyMatch(e -> e.getKey() == null || e.getKey().isBlank()
                || e.getValue() == null || e.getValue().isBlank()))
            throw new IllegalArgumentException("artifactIndex contains blank entry");
        return Collections.unmodifiableMap(new TreeMap<>(values));
    }
}
