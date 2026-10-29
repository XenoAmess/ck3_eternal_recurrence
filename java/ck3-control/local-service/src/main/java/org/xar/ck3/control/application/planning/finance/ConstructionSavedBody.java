package org.xar.ck3.control.application.planning.finance;

import java.io.IOException;
import java.util.Arrays;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** The physical full-body part of Root's actual saved-pair qualification; this alone is not restore admission. */
public final class ConstructionSavedBody {
    private ConstructionSavedBody() { }
    public static final class Saved {
        private final ContinuityState head;
        private final DomainBodies.BodyRef reference;
        private final ConstructionLedgerCodec.Ledger ledger;
        private final List<WriterContracts.Pin> pins;
        private Saved(ContinuityState head, DomainBodies.BodyRef reference, ConstructionLedgerCodec.Ledger ledger, List<WriterContracts.Pin> pins) {
            this.head = head; this.reference = reference; this.ledger = ledger; this.pins = List.copyOf(pins);
        }
        public ContinuityState head() { return head; }
        public DomainBodies.BodyRef reference() { return reference; }
        public ConstructionLedgerCodec.Ledger ledger() { return ledger; }
        public List<ExactRef> evidence() { return pins.stream().map(WriterContracts.Pin::reference).toList(); }
        public void requireUnchanged(Session same) throws IOException {
            same.requireHistoricalState(head.sequence(), ContinuityJson.digest(head.toJson()));
            for (var pin : pins) same.verifyPin(pin);
        }
    }
    public static Saved read(Session same, ContinuityState claimedSavedHead, List<ExactRef> completeActualProducerSources) throws IOException {
        Objects.requireNonNull(same); Objects.requireNonNull(claimedSavedHead); completeActualProducerSources = List.copyOf(completeActualProducerSources);
        StrictJson.require(!completeActualProducerSources.isEmpty() && claimedSavedHead.machineId().equals(same.head().state().machineId()),
                "saved construction must belong to this actual writer machine and frozen producer closure");
        ContinuityState actual = same.requireHistoricalState(claimedSavedHead.sequence(), ContinuityJson.digest(claimedSavedHead.toJson()));
        StrictJson.require(ContinuityJson.same(actual.toJson(), claimedSavedHead.toJson()), "saved construction head is not the complete surviving canonical state");
        DomainBodies.BodyRef original = DomainBodies.reference(actual, DomainBodies.Slot.CONSTRUCTION)
                .orElseThrow(() -> new IOException("actual saved head has no construction body; no empty or late initialization is allowed"));
        StrictJson.require(original.slot() == DomainBodies.Slot.CONSTRUCTION && original.contractSchema().equals(ConstructionLedgerCodec.SCHEMA)
                && original.producerSources().equals(completeActualProducerSources), "saved construction contract/producer closure is outside this frozen runtime");
        var pins = new ArrayList<WriterContracts.Pin>();
        for (ExactRef source : completeActualProducerSources) pins.add(same.capturePin(source, WriterContracts.MAX_PIN_BYTES));
        var body = same.capturePin(original.payload(), ConstructionDomainLifecycle.MAX_BYTES);
        StrictJson.require(body.identity().equals(original.identity()), "same bytes cannot replace the native identity of the original saved construction body");
        byte[] raw = same.readPinned(body, ConstructionDomainLifecycle.MAX_BYTES);
        var ledger = ConstructionLedgerCodec.decodeLedger(raw);
        StrictJson.require(Arrays.equals(raw, org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(ledger.original())),
                "saved construction body is not its original canonical full body");
        pins.add(body); for (var pin : pins) same.verifyPin(pin);
        return new Saved(actual, original, ledger, pins);
    }
}
