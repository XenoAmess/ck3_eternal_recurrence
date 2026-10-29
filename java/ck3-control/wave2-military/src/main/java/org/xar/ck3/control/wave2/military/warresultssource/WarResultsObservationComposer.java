package org.xar.ck3.control.wave2.military.warresultssource;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Binding;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.DispatchAck;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Field;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Observation;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.ValidatedWire;

/** Bridges validated wire content to the selected policy projection, preserving the caller's original lease. */
public final class WarResultsObservationComposer {
    private WarResultsObservationComposer() { }

    public static Observation compose(ValidatedWire wire, Binding originalLease) {
        Objects.requireNonNull(wire); Objects.requireNonNull(originalLease);
        require(originalLease.snapshotId().isValue() && originalLease.revision().isValue() && originalLease.episodeRunId().isValue(), "complete original SDK lease required");
        require(originalLease.nativeRevision().is(wire.input().binding().nativeRevision())
                && originalLease.actorId().is(BigInteger.valueOf(wire.input().binding().actorId()))
                && originalLease.dateRaw().is(BigInteger.valueOf(wire.input().binding().dateRaw()))
                && originalLease.connectionGeneration().is(wire.input().nativeGeneration()), "original lease differs from independent before binding");
        var leaf = wire.leaf();
        return new Observation(Field.of(WarResultsPolicy.SOURCE_SCHEMA), originalLease,
                Field.of(leaf.availability().available()), Field.of(leaf.post().visibility().observed()),
                Field.of(leaf.post().scopeUnchanged()), Field.of(leaf.post().visibility().windowPresent()),
                Field.of(leaf.post().visibility().effectiveVisible()), Field.missing(),
                new DispatchAck(Field.of(leaf.availability().accepted()), Field.of(leaf.dispatch().attempted()), Field.of(leaf.dispatch().invoked())));
    }

    private static void require(boolean valid, String message) { if (!valid) { throw new IllegalArgumentException(message); } }
}
