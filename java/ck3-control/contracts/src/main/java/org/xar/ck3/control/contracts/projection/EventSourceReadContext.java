package org.xar.ck3.control.contracts.projection;

import java.nio.file.Path;
import java.util.List;
import java.util.Objects;

/** Fixed server roots and grant source; each domain opens one current immutable snapshot per projection. */
public record EventSourceReadContext(String machineId, Path stateRoot, Path stockGameRoot,
        ProjectionEvidenceGrants evidenceSource) {
    public EventSourceReadContext(String machineId, Path stateRoot, Path stockGameRoot) {
        this(machineId, stateRoot, stockGameRoot, ProjectionEvidenceGrants.fixed(List.of()));
    }
    public EventSourceReadContext(String machineId, Path stateRoot, Path stockGameRoot, List<ProjectionEvidenceGrant> grants) {
        this(machineId, stateRoot, stockGameRoot, ProjectionEvidenceGrants.fixed(grants));
    }
    public EventSourceReadContext {
        Objects.requireNonNull(machineId); Objects.requireNonNull(stateRoot); Objects.requireNonNull(stockGameRoot); Objects.requireNonNull(evidenceSource);
        if (!machineId.matches("[a-z0-9][a-z0-9-]{0,63}") || "unknown".equals(machineId)) {
            throw new IllegalArgumentException("explicit event source machine identity required");
        }
        if (!stateRoot.isAbsolute() || !stockGameRoot.isAbsolute()) {
            throw new IllegalArgumentException("absolute fixed event source roots required");
        }
        stateRoot = stateRoot.normalize(); stockGameRoot = stockGameRoot.normalize();
        if (stateRoot.startsWith(stockGameRoot) || stockGameRoot.startsWith(stateRoot)) {
            throw new IllegalArgumentException("separate state and stock game roots required");
        }
    }
    public List<ProjectionEvidenceGrant> evidenceGrants() {
        try { return ProjectionEvidenceCodec.validated(evidenceSource.currentGrants()); }
        catch (ProjectionProtocolException unavailable) { throw unavailable; }
        catch (RuntimeException invalid) {
            throw new ProjectionProtocolException(ProjectionError.Code.OPERATION_UNAVAILABLE, "fixed server evidence manifest unavailable");
        }
    }
}
