package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.CampaignProjection.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.RegistryCampaignProjection.PendingObject;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** One same-Root internal service aggregate, not a Native operation or an observation factory. */
public final class RootTurnBundleReadSource {
    /** The true original read is retained separately from the current aggregate binding. */
    public record RootRead(Root root, Complete frame, PlanningReadResult.Known<FinanceReadContracts.Packet> original) {
        public RootRead { Objects.requireNonNull(root); Objects.requireNonNull(frame); requireOriginal(original);
            StrictJson.require(root.binding().snapshotId().equals(frame.identity().frame().snapshotId())
                    && root.binding().revision().equals(frame.identity().frame().revision())
                    && root.binding().nativeRevision().equals(frame.identity().frame().identity().nativeRevision())
                    && root.binding().dateRaw() == frame.identity().frame().identity().dateRaw().intValueExact()
                    && root.source().querySequence().equals(org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(
                        original.value().result().get("query_sequence"), "original ROOT query sequence")),
                    "typed ROOT aggregate material changed its held complete frame"); }
    }
    public record BundleRead(TurnBundle.Result<PendingObject,PendingObject> bundle,
            PlanningReadResult.Known<FinanceReadContracts.Packet> original) {
        public BundleRead { Objects.requireNonNull(bundle); requireOriginal(original);
            StrictJson.require(bundle.binding().nativeRevision().equals(original.receipt().request().before().frame().identity().nativeRevision())
                    && bundle.binding().dateRaw() == original.receipt().request().before().frame().identity().dateRaw().intValueExact()
                    && bundle.source().querySequence().equals(org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(
                        original.value().result().get("query_sequence"), "original ROOT query sequence")),
                    "typed turn-bundle aggregate changed the original ROOT native frame/date"); }
        /** Internal service wire uses the existing exact integer codec; no public decimal conversion. */
        public RawJson internalJson() { return RegistryWire.encodeBundle(bundle); }
    }
    private final RootRuntimeContext context;
    /** Construction neither reads Finance nor obtains Core/Native authority. Actual runtime use is once bound by its owner. */
    public RootTurnBundleReadSource(RootRuntimeContext context) { this.context = Objects.requireNonNull(context); }
    public void requireOwner(RootRuntimeContext same) {
        StrictJson.require(context == Objects.requireNonNull(same), "turn-bundle producer crossed its actual Root context");
    }

    /** The caller must already hold the collector's exact whole planning/public read scope and original writer. */
    public BundleRead read(Session same, PlanningRequest retained, Complete heldFrame) throws IOException {
        Objects.requireNonNull(retained); Objects.requireNonNull(heldFrame);
        requirePlanningFrame(retained, heldFrame);
        RootRead root = readRoot(same, heldFrame, retained.deadline());
        BundleRead result = new BundleRead(aggregate(root.root(), root.frame().semantic()), root.original());
        context.collector().requireHeldFrame(same, heldFrame);
        context.requireCurrent(retained.deadline());
        return result;
    }

    /** Public directory and bundle share this exact ROOT original producer. It never observes another frame. */
    public RootRead readRoot(Session same, Complete heldFrame, Instant deadline) throws IOException {
        Objects.requireNonNull(same); Objects.requireNonNull(heldFrame); Objects.requireNonNull(deadline);
        context.writer().requireSession(same); context.requireCurrent(deadline);
        context.collector().requireHeldFrame(same, heldFrame);
        StrictJson.require(heldFrame.identity().game().equals(context.game().generation())
                && heldFrame.identity().machineId().equals(context.game().machineId())
                && heldFrame.source().equals(context.source()) && heldFrame.sessionId().equals(context.game().sessionId()),
                "turn-bundle producer crossed the held physical Root Game/source/session");
        var finance = context.finance(); var contract = finance.definitions().contract(FinanceReadContracts.Query.ROOT);
        StrictJson.require(context.readCatalog().containsIdentity(contract)
                && finance.game().equals(context.game().generation()) && finance.source().equals(heldFrame.source())
                && finance.sessionId().equals(heldFrame.sessionId()), "turn-bundle needs the identical actual installed ROOT v2 producer");
        var request = new PlanningReadRequest(heldFrame.identity(), heldFrame.source(), heldFrame.sessionId(), contract.operation(),
                FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY), deadline);
        var observed = finance.readPort().read(same, contract, request);
        if (observed instanceof PlanningReadResult.Unavailable<FinanceReadContracts.Packet> unavailable)
            throw new IOException("actual installed turn-bundle ROOT read unavailable: " + unavailable.reason());
        var known = (PlanningReadResult.Known<FinanceReadContracts.Packet>) observed; var packet = known.value();
        requireOriginal(known);
        StrictJson.require(context.archive().withSession(same).readReferenceOf(known.receipt()).equals(known.originalReceipt())
                && contract.replay(known.receipt()).result().equals(packet.result()),
                "turn-bundle lost the actual ROOT decoder or archived original receipt");
        contract.requireCanonicalReuse(known.receipt(), packet, request, heldFrame.semantic());
        var frame = heldFrame.identity().frame();
        Binding binding = new Binding(frame.snapshotId(), frame.revision(), frame.identity().nativeRevision(),
                frame.identity().dateRaw().intValueExact(), frame.revision());
        RootRead result = new RootRead(RegistryCampaignProjection.root(packet.result(), binding), heldFrame, known);
        context.collector().requireHeldFrame(same, heldFrame); context.writer().requireSession(same); context.requireCurrent(deadline);
        return result;
    }

    /** The sole pure aggregate call used by both the internal source and public registered handler. */
    public static TurnBundle.Result<PendingObject,PendingObject> aggregate(Root root, Obj sameSnapshot) {
        Objects.requireNonNull(root); Objects.requireNonNull(sameSnapshot);
        return TurnBundle.build(RegistryCampaignProjection.snapshot(sameSnapshot, root.binding()), root);
    }
    static void requirePlanningFrame(PlanningRequest retained, Complete held) {
        Objects.requireNonNull(retained); Objects.requireNonNull(held);
        StrictJson.require(retained.before().equals(held.identity()) && retained.source().equals(held.source())
                && retained.sessionId().equals(held.sessionId()) && retained.observations().snapshot().equals(held.semantic()),
                "turn-bundle planning request differs from the exact complete held source/frame/snapshot");
    }
    private static void requireOriginal(PlanningReadResult.Known<FinanceReadContracts.Packet> value) {
        Objects.requireNonNull(value);
        StrictJson.require(value.value().receipt().equals(value.receipt())
                && value.originalReceipt().bytes() > 0
                && FinanceReadContracts.ROOT_CONTRACT_ID.equals(value.receipt().contractId())
                && value.receipt().request().operation().equals(FinanceReadContracts.Query.ROOT.operation())
                && FinanceReadContracts.rootCapture(value.receipt().request().arguments()) == FinanceReadContracts.RootCapture.PUBLIC_QUERY,
                "turn-bundle must retain the true original public ROOT v2 receipt and reference");
    }
}
