package org.xar.ck3.control.wave2.runtime.stdioidentity;

import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Expected Game/Queue/App identities and bounded entry sources, without a custody claim. */
public record StdioIdentityPlanV1(String machineId, ProcessIdentityClaimV1 game,
        ProcessIdentityClaimV1 queue, ProcessIdentityClaimV1 app, List<SourcePinV1> entrySources) {
    public static final String SCHEMA = "xar.owned-stdio-identity-plan/v1";
    public static final int MAX_SOURCES = 8;
    public static final int MAX_SOURCE_BYTES = 1_048_576;

    public record SourcePinV1(Path path, long bytes, String sha256) {
        public SourcePinV1 {
            StrictJson.require(path != null && path.isAbsolute() && path.toString().indexOf('\0') < 0,
                    "absolute entry source path required");
            StrictJson.text(path.toString());
            path = path.normalize();
            StrictJson.require(bytes >= 0 && bytes <= MAX_SOURCE_BYTES, "bounded exact entry source size required");
            StrictJson.require(sha256 != null && sha256.matches("[0-9a-f]{64}"), "canonical entry source SHA-256 required");
        }
    }

    public StdioIdentityPlanV1 {
        StrictJson.require(machineId != null && !machineId.isBlank() && machineId.indexOf('\0') < 0,
                "expected machine_id required");
        StrictJson.text(machineId);
        Objects.requireNonNull(game); Objects.requireNonNull(queue); Objects.requireNonNull(app);
        StrictJson.require(game.pid() != queue.pid() && queue.pid() != app.pid() && game.pid() != app.pid(),
                "distinct Game, Queue and App PIDs required");
        StrictJson.require(entrySources != null && !entrySources.isEmpty() && entrySources.size() <= MAX_SOURCES,
                "one to eight frozen entry source pins required");
        entrySources = List.copyOf(entrySources);
        Set<Path> unique = new HashSet<>();
        for (SourcePinV1 source : entrySources) {
            StrictJson.require(unique.add(source.path()), "duplicate entry source path");
        }
    }
}
