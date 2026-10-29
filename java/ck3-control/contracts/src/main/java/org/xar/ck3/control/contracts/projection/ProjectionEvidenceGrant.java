package org.xar.ck3.control.contracts.projection;

import java.nio.file.Path;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Server-declared exact file pin. Domain readers still verify original provenance and per-role limits. */
public record ProjectionEvidenceGrant(Path path, long bytes, String sha256, String originMachineId,
        ProjectionEvidenceRole role) {
    public ProjectionEvidenceGrant {
        Objects.requireNonNull(path); Objects.requireNonNull(sha256); Objects.requireNonNull(originMachineId); Objects.requireNonNull(role);
        if (!path.isAbsolute() || bytes < 0 || bytes > StrictJson.MAX_SAFE_INTEGER
                || !sha256.matches("[a-f0-9]{64}") || !originMachineId.matches("[a-z0-9][a-z0-9-]{0,63}")) {
            throw new IllegalArgumentException("exact absolute evidence pin and explicit origin machine or unknown required");
        }
        path = path.normalize();
    }
}
