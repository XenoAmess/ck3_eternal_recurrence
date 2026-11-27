package org.xar.ck3.control.application.planning.finance;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.LinkedHashSet;
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
            requireSameHead(same);
            for (var pin : pins) same.verifyPin(pin);
        }
        private void requireSameHead(Session same) throws IOException {
            same.requireHistoricalState(head.sequence(), ContinuityJson.digest(head.toJson()));
        }
    }

    public static final class Recorded {
        private final Saved saved;
        private final DomainBodies.RecordedImport publication;

        private Recorded(Saved saved, DomainBodies.RecordedImport publication) {
            this.saved = saved;
            this.publication = publication;
        }

        public Saved saved() { return saved; }
        public ExactRef publication() { return publication.canonicalEvent(); }

        public void requireUnchanged(Session original) throws IOException {
            saved.requireSameHead(original);
            var pins = new LinkedHashSet<>(saved.pins);
            pins.addAll(publication.currentInputs());
            for (var pin : pins) original.verifyPin(pin);
        }
    }

    /** Recovers old source approvals from the writer's actual DOMAIN_IMPORT at the selected Saved frontier. */
    public static Recorded readRecorded(Session original, ContinuityState savedHead) throws IOException {
        var actual = original.requireHistoricalCanonicalState(savedHead.sequence(), ContinuityJson.digest(savedHead.toJson()));
        var body = DomainBodies.reference(actual, DomainBodies.Slot.CONSTRUCTION)
                .orElseThrow(() -> new IOException("original Saved frontier has no canonical construction body"));
        var directory = Path.of(original.persistedHead().path()).toAbsolutePath().normalize().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS");
        var events = original.head().documents().stream().filter(pin -> {
            var path = Path.of(pin.reference().path()).toAbsolutePath().normalize();
            String name = path.getFileName().toString();
            return directory.equals(path.getParent()) && name.matches("[0-9]{8}[.]json")
                    && Long.parseLong(name.substring(0, 8)) <= actual.sequence();
        }).sorted(Comparator.comparing((WriterContracts.Pin pin) -> pin.reference().path()).reversed()).toList();
        if (events.isEmpty()) throw new IOException("original Saved construction has no producing writer event");
        var edge = original.withHistoricalTransitions(events, history -> {
            for (var transition : history) {
                StrictJson.require(DomainBodies.reference(transition.after(), DomainBodies.Slot.CONSTRUCTION)
                        .filter(body::equals).isPresent(), "original Saved construction body changed before its producing event");
                if (DomainBodies.reference(transition.before(), DomainBodies.Slot.CONSTRUCTION).filter(body::equals).isEmpty())
                    return transition;
            }
            throw new IOException("original Saved construction has no producing writer event");
        });
        StrictJson.require(DomainBodies.IMPORT_KIND.equals(edge.kind()), "original Saved construction requires a canonical domain import");
        var publication = original.requireHistoricalImport(DomainBodies.Slot.CONSTRUCTION, edge.sequence(), ContinuityJson.digest(edge.after().toJson()));
        StrictJson.require(publication.body().equals(body) && publication.canonicalEvent().equals(edge.eventPin().reference()),
                "recorded construction approval differs from the selected Saved body or canonical original event");
        return new Recorded(read(original, actual, publication.body().producerSources()), publication);
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
