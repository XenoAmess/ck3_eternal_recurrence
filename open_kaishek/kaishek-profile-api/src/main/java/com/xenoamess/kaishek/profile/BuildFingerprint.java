package com.xenoamess.kaishek.profile;

import java.util.List;
import java.util.Objects;

/** Exact game/build identity. A profile must never silently drift to another build. */
public record BuildFingerprint(
        String gameId,
        String gameVersion,
        String exeSha256,
        List<String> assetHashes,
        String modTreeHash,
        String configurationHash) {
    public BuildFingerprint {
        gameId = require(gameId, "gameId");
        gameVersion = require(gameVersion, "gameVersion");
        exeSha256 = requireHash(exeSha256, "exeSha256");
        assetHashes = List.copyOf(Objects.requireNonNull(assetHashes, "assetHashes"));
        assetHashes = assetHashes.stream().map(h -> requireHash(h, "assetHashes entry")).toList();
        modTreeHash = optionalHash(modTreeHash, "modTreeHash");
        configurationHash = optionalHash(configurationHash, "configurationHash");
    }

    private static String require(String value, String name) {
        if (value == null || value.isBlank()) throw new IllegalArgumentException(name + " is blank");
        return value;
    }
    private static String requireHash(String value, String name) {
        value = require(value, name);
        if (!value.matches("[0-9a-fA-F]{64}")) throw new IllegalArgumentException(name + " must be SHA-256 hex");
        return value.toLowerCase(java.util.Locale.ROOT);
    }
    private static String optionalHash(String value, String name) {
        return value == null || value.isBlank() ? null : requireHash(value, name);
    }
}
