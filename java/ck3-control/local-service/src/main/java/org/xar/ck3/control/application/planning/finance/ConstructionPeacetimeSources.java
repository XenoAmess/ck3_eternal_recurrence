package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist;
import org.xar.ck3.control.wave3.planning.constructionrelease.ConstructionRelease;
import org.xar.ck3.control.wave3.planning.constructionrelease.ConstructionReleaseCodec;
import org.xar.ck3.control.wave3.planning.m5peacetimeassembly.PeacetimeAssembly;

/** The genuine construction part of the single M5 aggregate. This creates no submission or body-import authority. */
public final class ConstructionPeacetimeSources {
    public record Prior(PlanningRequest original, ConstructionLedgerCodec.Ledger ledger, ConstructionReleaseCodec.Request release) {
        public Prior { Objects.requireNonNull(original); Objects.requireNonNull(ledger); Objects.requireNonNull(release); }
    }
    public record Capture(ConstructionLedgerCodec.Ledger after, PeacetimeAssembly.Construction construction,
            ConstructionEconomyModel.QuoteCashObservation cash, List<PlanningReadReceipt> originalReads) {
        public Capture { Objects.requireNonNull(after); Objects.requireNonNull(construction); Objects.requireNonNull(cash); originalReads = List.copyOf(originalReads); }
    }
    private final ConstructionDomainLifecycle.Prepared domain;
    private final OrdinaryConstructionCollector collector;
    public ConstructionPeacetimeSources(ConstructionDomainLifecycle.Prepared domain, OrdinaryConstructionCollector collector) {
        this.domain = Objects.requireNonNull(domain); this.collector = Objects.requireNonNull(collector);
    }
    /** Root wraps this with its actual currentPlanning scope and the same original writer Session. */
    public Prior prior(Session same, PlanningRequest original) throws IOException {
        return project(original, domain.read(same));
    }
    public Capture capture(Session same, PlanningRequest original, Prior before) throws IOException {
        Objects.requireNonNull(same); Objects.requireNonNull(original); Objects.requireNonNull(before);
        require(before.original() == original, "M5 construction must retain its exact original planning request");
        ConstructionLedgerCodec.Ledger current = domain.read(same);
        require(current.original().equals(before.ledger().original()) && current.pending().isEmpty(), "M5 construction body changed or still has an unresolved original");
        var release = ConstructionRelease.assess(before.release().frame(), before.release().applied(), before.release().processObservation());
        if (release.blocksCandidate()) return new Capture(current,
                new PeacetimeAssembly.Construction(PeacetimeAssembly.ConstructionStatus.PRIOR_RECEIPT_NOT_RELEASED,
                        obj("status", new Text("prior_receipt_not_released"), "reason", new Text(release.reason().name()))),
                new ConstructionEconomyModel.NoCashObservation(), List.of());
        var actual = collector.peacetime(same, original);
        if (actual instanceof OrdinaryConstructionCollector.PeacetimeFrameChanged changed)
            throw new IOException("actual M5 construction frame changed: " + changed.reason());
        if (actual instanceof OrdinaryConstructionCollector.PeacetimeMissing missing)
            throw new IOException("actual M5 construction source incomplete: " + missing.reason());
        var known = (OrdinaryConstructionCollector.PeacetimeAvailable) actual;
        var after = domain.read(same);
        require(after.original().equals(before.ledger().original()), "M5 construction full canonical body changed during native reads");
        return new Capture(after, assembly(known.finalizedQuery()), known.cash(), known.originalReads());
    }
    static Prior project(PlanningRequest original, ConstructionLedgerCodec.Ledger ledger) {
        Objects.requireNonNull(original); Objects.requireNonNull(ledger);
        var current = original.before().frame(); var identity = current.identity();
        var frame = new JointShortlist.Frame(identity.player(), identity.nativeRevision(), identity.dateRaw(), current.snapshotId(), current.revision(), current.episodeRunId());
        var applied = ConstructionReleaseCodec.project(ledger.original().get("applied"), frame);
        ConstructionRelease.ProcessObservation process = ConstructionRelease.IdentityUnused.INSTANCE;
        if (ConstructionRelease.sameEpisode(frame, applied)) {
            process = ConstructionRelease.IdentityUnavailable.INSTANCE;
            if (original.observations().snapshot().get("diagnostics") instanceof Obj diagnostic
                    && diagnostic.get("bridge_pid") != null && diagnostic.get("bridge_creation_date") != null) {
                BigInteger pid = integer(diagnostic.get("bridge_pid"), "actual bridge PID");
                require(pid.signum() > 0 && pid.compareTo(BigInteger.valueOf(4_294_967_295L)) <= 0, "actual observed bridge PID range");
                // The actual currentPlanning source authenticates these diagnostics. The bridge and Game are distinct identities.
                process = new ConstructionRelease.ObservedIdentity(new ConstructionRelease.ProcessIdentity(pid,
                        text(diagnostic.get("bridge_creation_date"), "actual original process birth spelling")));
            }
        }
        return new Prior(original, ledger, new ConstructionReleaseCodec.Request(frame, applied, process));
    }
    static PeacetimeAssembly.Construction assembly(Obj actualFinalizedQuery) {
        Objects.requireNonNull(actualFinalizedQuery);
        PeacetimeAssembly.ConstructionStatus status;
        if (new Text("selected").equals(actualFinalizedQuery.get("status"))) status = PeacetimeAssembly.ConstructionStatus.SELECTED;
        else {
            require(new Text("no_legal_budgeted_building").equals(actualFinalizedQuery.get("status")),
                    "missing, RED, material-only or incomplete construction input cannot become a no-candidate source");
            status = PeacetimeAssembly.ConstructionStatus.NO_LEGAL_BUDGETED_BUILDING;
        }
        return new PeacetimeAssembly.Construction(status, actualFinalizedQuery);
    }
}
