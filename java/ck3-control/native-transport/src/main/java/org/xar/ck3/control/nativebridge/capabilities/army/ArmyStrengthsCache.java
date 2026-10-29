package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;

/** Single exact-frame/profile complete-scope cache. Failed refresh and subset reads never expose stale results. */
public final class ArmyStrengthsCache {
    private SnapshotProjection entry;
    private List<ScopeArmy> orderedScope = List.of();
    public synchronized void invalidate() { entry = null; orderedScope = List.of(); }
    public synchronized void publish(Snapshot actualFrame, Read actualRead, boolean actualScopedExport) {
        Objects.requireNonNull(actualFrame); Objects.requireNonNull(actualRead);
        invalidate();
        if (actualScopedExport) return;
        List<ScopeArmy> actual = actualRead.rows().stream().map(row -> row.core().scope()).toList();
        ArmyTypes.require(actual.equals(actualFrame.scope()), "only complete exact-scope native reads may publish the cache");
        orderedScope = List.copyOf(actualFrame.scope());
        entry = new SnapshotProjection(actualFrame.binding(), actualRead.profile(), actualRead.status(), actualRead.sequence(), actualRead.rows().stream().map(Row::core).toList());
    }
    public synchronized Optional<SnapshotProjection> forSnapshot(Snapshot current, Profile profile) {
        Objects.requireNonNull(current); Objects.requireNonNull(profile);
        if (entry == null) return Optional.empty();
        if (!entry.binding().equals(current.binding()) || entry.profile() != profile || !orderedScope.equals(current.scope())) { invalidate(); return Optional.empty(); }
        return Optional.of(entry);
    }
}
