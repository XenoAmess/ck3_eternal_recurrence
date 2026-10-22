package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/** Initial provenance of a fixed server-owned mutable knowledge source, never a new read grant or immutable artifact. */
public final class ProjectionRuntimeSources {
    public static final int MAX_RESPONSE_BYTES = (1 << 20) + 4096;
    private static final String ROLE_CLASS = "org.xar.ck3.control.contracts.projection.ProjectionEvidenceRole";
    private ProjectionRuntimeSources() {}

    public record EvidenceGrant(String role, String path, long bytes, String sha256, String originMachineId) {
        public EvidenceGrant {
            if (role == null || !role.matches("[a-z][a-z0-9]*(?:-[a-z0-9]+)*") || role.length() > 128
                    || path == null || !Path.of(path).isAbsolute() || bytes < 0 || bytes > 9007199254740991L
                    || sha256 == null || !sha256.matches("[a-f0-9]{64}")
                    || originMachineId == null || !originMachineId.matches("[a-z0-9][a-z0-9-]{0,63}")) {
                throw new IllegalArgumentException("Exact declared grant wire and original provenance required");
            }
            path = Path.of(path).normalize().toString();
        }
    }

    public record GrantsSnapshot(String schema, String machineId, String observedAtUtc, List<EvidenceGrant> grants) {
        public GrantsSnapshot {
            if (!"xar.projection-host-evidence-grants/v1".equals(schema) || machineId == null
                    || !machineId.matches("[a-z0-9][a-z0-9-]{0,63}") || machineId.equals("unknown")) {
                throw new IllegalArgumentException("Actual machine-bound server grant observation required");
            }
            Instant.parse(observedAtUtc); grants = List.copyOf(grants);
            if (grants.size() > 1024) throw new IllegalArgumentException("Finite server grant inventory required");
            record Identity(String role, Path path) {}
            Set<Identity> identities = new HashSet<>();
            for (EvidenceGrant grant : grants) {
                if (!identities.add(new Identity(grant.role(), Path.of(grant.path())))) throw new IllegalArgumentException("Duplicate server evidence path/role");
            }
        }
    }

    public record ConfiguredManifest(String manifestPath, ControlBuild.FileRef initialSnapshotRef, int initialGrantCount) {
        public ConfiguredManifest {
            if (manifestPath == null || !Path.of(manifestPath).isAbsolute() || initialGrantCount < 0 || initialGrantCount > 1024) {
                throw new IllegalArgumentException("Explicit fixed server manifest path and initial observation count required");
            }
            manifestPath = Path.of(manifestPath).normalize().toString(); Objects.requireNonNull(initialSnapshotRef);
            if (initialSnapshotRef.bytes() < 1 || initialSnapshotRef.bytes() > MAX_RESPONSE_BYTES) {
                throw new IllegalArgumentException("Actual bounded initial GET response reference required");
            }
        }
    }

    /** Decode uses typed strict JSON; accepted deployed shared role enum remains the only wire registry. */
    public static void requireCurrentSnapshot(GrantsSnapshot snapshot, String machine,
            List<ControlBuild.FileRef> deployment) throws IOException {
        Objects.requireNonNull(snapshot); Objects.requireNonNull(machine);
        Instant observed = Instant.parse(snapshot.observedAtUtc()), now = Instant.now();
        if (!machine.equals(snapshot.machineId()) || observed.isAfter(now.plusSeconds(5)) || observed.isBefore(now.minusSeconds(30))) {
            throw new IOException("Fresh same-machine actual server grant observation required");
        }
        Set<String> wires = ProjectionDeploymentProof.sharedEnumWires(deployment, ROLE_CLASS);
        for (ControlBuild.FileRef artifact : deployment) artifact.verify();
        for (EvidenceGrant grant : snapshot.grants()) {
            if (!wires.contains(grant.role())) throw new IOException("Declared evidence role is not in the deployed shared enum");
        }
        // Grants are declarations. The existing domain reader owns each actual file/provenance check at use.
        // Do not pin the mutable configured manifest as an immutable deployment file or require future snapshots to equal this one.
    }
}
