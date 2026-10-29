package org.xar.ck3.control.application.routecontact;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.history.DriverHistoryImport;
import org.xar.ck3.control.application.history.DriverSurvivingHistory;
import org.xar.ck3.control.application.history.RouteContactHistoryAdapter;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Rebuilds the complete surviving Driver branch from the same archived producer manifest as the guarded start. */
public final class RouteContactArchivedHistory implements RouteContactArchivedVerifier.HistoryReplay {
    @Override public List<RouteContactProofs.QueryEntry> queries(WriterContracts.Head head, ActionCommand parent,
            AdvanceObservationPort.Frame starting, ActionPorts.OutcomeArchive archive) {
        var rows = rows(head, parent, starting, archive);
        return RouteContactHistoryAdapter.queries(DriverSurvivingHistory.afterLatestRestore(rows), RouteContactCodec.frame(starting));
    }
    @Override public List<RouteContactModel.TimelineEntry> timeline(WriterContracts.Head head, ActionCommand parent,
            AdvanceObservationPort.Frame starting, ActionPorts.OutcomeArchive archive) {
        return RouteContactHistoryAdapter.timeline(rows(head, parent, starting, archive));
    }
    private static List<DriverSurvivingHistory.Row> rows(WriterContracts.Head head, ActionCommand parent,
            AdvanceObservationPort.Frame starting, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(head); Objects.requireNonNull(archive);
        StrictJson.require(parent.before().equals(starting.identity()) && parent.source().equals(starting.source())
                && parent.sessionId().equals(starting.sessionId()), "archived route history crossed its original parent");
        var manifestRef = DriverObservationEvidenceReader.reference(starting.semantic().get("java_driver_facts_evidence"));
        var manifest = archive.loadFullMaterial(manifestRef);
        byte[] nativePacket = archive.loadNativeFrame(starting.originalEvidence());
        StrictJson.require(starting.originalEvidence().bytes() == nativePacket.length
                && starting.originalEvidence().sha256().equals(DriverJson.sha256(nativePacket)), "archived route native packet changed");
        var actual = DriverObservationEvidenceReader.nativeFrame(manifestRef, manifest, nativePacket);
        var driverRef = DriverObservationEvidenceReader.currentDriverReference(manifestRef, manifest);
        var driver = archive.loadFullMaterial(driverRef);
        var facts = DriverObservationEvidenceReader.decode(manifestRef, manifest, driver, actual);
        StrictJson.require(facts.source().equals(parent.source()) && actual.session().game().equals(parent.before().game())
                && actual.session().sessionId().equals(parent.sessionId()) && actual.snapshotId().equals(starting.identity().frame().snapshotId())
                && actual.nativeRevision().equals(starting.identity().frame().identity().nativeRevision()), "archived route history producer/source differs");
        OpportunityJson.Obj row = DriverJson.object(manifest.bytes(), DriverJson.MAX_NATIVE_BYTES);
        long version = OpportunityJson.integer(row.get("driver_version"), "driver_version").longValueExact();
        long epoch = OpportunityJson.integer(row.get("episode_epoch"), "episode_epoch").longValueExact();
        var auxiliary = OpportunityJson.object(row.get("original_semantic_fields"), "original_semantic_fields");
        return DriverHistoryImport.originalV2(driverRef, driver.bytes(), version, epoch, parent.before().game(), auxiliary).completeSurvivingBranch();
    }
}
