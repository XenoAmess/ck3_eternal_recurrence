package com.xenoamess.kaishek.profile;

import java.util.*;

/** Short canonical name for a game profile; equivalent to {@link GameProfile}. */
public record Profile(String id, String gameVersion, BuildFingerprint fingerprint,
                      OpcodeRegistry opcodes, Set<String> certifiedSemantics,
                      Map<ScopeType, Set<ScopeType>> scopeLinks) {
    public Profile {
        if (id == null || id.isBlank()) throw new IllegalArgumentException("id is blank");
        gameVersion = requireNonBlank(gameVersion, "gameVersion"); fingerprint = Objects.requireNonNull(fingerprint, "fingerprint");
        if (!gameVersion.equals(fingerprint.gameVersion())) throw new IllegalArgumentException("fingerprint gameVersion mismatch");
        opcodes = Objects.requireNonNull(opcodes, "opcodes");
        certifiedSemantics = Set.copyOf(Objects.requireNonNull(certifiedSemantics, "certifiedSemantics"));
        var links = new EnumMap<ScopeType, Set<ScopeType>>(ScopeType.class);
        Objects.requireNonNull(scopeLinks, "scopeLinks").forEach((from, tos) -> links.put(Objects.requireNonNull(from), Set.copyOf(Objects.requireNonNull(tos))));
        scopeLinks = Collections.unmodifiableMap(links);
    }
    public boolean supports(ScopeType from, ScopeType to) { return scopeLinks.getOrDefault(from, Set.of()).contains(to); }
    public GameProfile asGameProfile() { return new GameProfile(id, gameVersion, fingerprint, opcodes, certifiedSemantics, scopeLinks); }

    private static String requireNonBlank(String value, String name) {
        if (value == null || value.isBlank()) throw new IllegalArgumentException(name + " is blank");
        return value;
    }
}
