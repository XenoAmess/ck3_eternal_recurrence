package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.util.EnumMap;
import java.util.Map;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingCodec;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;

/** Read-only adapter over bodies actually imported/read under the one ContinuityStorePort lock. */
public final class FinanceStatePort {
    /** CHILD_MARRIAGE retains the original Python budget's matrilineal body; default marriage has its own actual body. */
    public enum Domain { CONSTRUCTION, FACTION_GIFT, MERCENARY, FEAST, CROWN, FIRST_HEIR_MARRIAGE, CHILD_MARRIAGE, CHILD_DEFAULT_MARRIAGE }
    public enum Pending { CLEAR, PENDING }
    /** A missing document is represented by absence, never this object's null pending. */
    public record Document(Domain domain, ExactRef original, byte[] bytes) {
        public Document {
            Objects.requireNonNull(domain); Objects.requireNonNull(original); bytes = Objects.requireNonNull(bytes).clone();
            StrictJson.require(original.bytes() == bytes.length
                    && original.sha256().equals(org.xar.ck3.control.application.action.ActionCodec.sha256(bytes)),
                    "domain body must match the original immutable archive");
            decodeDocument(bytes);
        }
        @Override public byte[] bytes() { return bytes.clone(); }
    }
    public record Checkpoint(ExactRef saveReference, String episodeRunId, java.math.BigInteger dateRaw) {
        public Checkpoint { Objects.requireNonNull(saveReference); StrictJson.text(episodeRunId); Objects.requireNonNull(dateRaw); }
    }
    public sealed interface Read permits Unavailable, Head { }
    public record Unavailable(String reason) implements Read { public Unavailable { StrictJson.text(reason); } }
    /** Supplied only by the concrete original-writer adapter. Constructor validation grants no storage qualification. */
    public record Head(ObservationIdentity current, ExactRef canonicalHead, List<Document> bodies,
            List<ActionReceipt> actualActionReceipts, Optional<Checkpoint> checkpoint) implements Read {
        public Head {
            Objects.requireNonNull(current); Objects.requireNonNull(canonicalHead); bodies = List.copyOf(bodies);
            actualActionReceipts = List.copyOf(actualActionReceipts); Objects.requireNonNull(checkpoint);
        }
    }
    /** The owning domain installs its strict persistent-body codec; missing registrations never prove CLEAR. */
    @FunctionalInterface public interface BodyReader { Pending decode(Document original); }
    public record ReaderBinding(Domain domain, ExactRef definitionSource, BodyReader reader) {
        public ReaderBinding {
            Objects.requireNonNull(domain); Objects.requireNonNull(definitionSource); Objects.requireNonNull(reader);
            require(definitionSource.bytes() > 0, "actual owning decoder source required");
        }
    }
    public static ReaderBinding giftReader(ExactRef definitionSource) {
        return new ReaderBinding(Domain.FACTION_GIFT, definitionSource, document ->
                GiftPendingCodec.decodeLedger(document.bytes()).pending().isPresent() ? Pending.PENDING : Pending.CLEAR);
    }
    @FunctionalInterface public interface SourcePort {
        /** Use ContinuityStorePort.locked(session -> session.head()), preserving absent body/archive states. No writes. */
        Read readUnderOriginalLock(PlanningRequest request);
        /** Root implements this with the exact borrowed writer, without acquiring another lock. */
        default Read readUnderOriginalLock(Session borrowed, PlanningRequest request) {
            throw new IllegalStateException("finance original-writer borrowed Session reader is not installed");
        }
    }
    public record Ledger(Document document, Obj original, Pending pending) {
        public Ledger { Objects.requireNonNull(document); Objects.requireNonNull(original); Objects.requireNonNull(pending); }
        public Optional<Obj> pendingObject() {
            Value pendingValue = original.get("pending");
            return pendingValue instanceof Obj value ? Optional.of(value) : Optional.empty();
        }
    }
    public static final class Snapshot {
        private final Head head;
        private final EnumMap<Domain, Ledger> ledgers;
        private final EnumMap<Domain, String> unavailable;
        private Snapshot(Head head, EnumMap<Domain, Ledger> ledgers, EnumMap<Domain, String> unavailable) {
            this.head = head; this.ledgers = new EnumMap<>(ledgers); this.unavailable = new EnumMap<>(unavailable);
        }
        public Optional<String> unavailableReason(Domain domain) { return Optional.ofNullable(unavailable.get(domain)); }
        public Head head() { return head; }
        public Optional<Ledger> ledger(Domain domain) { return Optional.ofNullable(ledgers.get(domain)); }
        public boolean spendingLedgersKnownClear() {
            return List.of(Domain.CONSTRUCTION, Domain.FACTION_GIFT, Domain.FEAST, Domain.FIRST_HEIR_MARRIAGE, Domain.CHILD_MARRIAGE, Domain.CHILD_DEFAULT_MARRIAGE)
                    .stream().allMatch(d -> ledger(d).filter(l -> l.pending() == Pending.CLEAR).isPresent());
        }
        public List<ActionReceipt> unresolved() { return head.actualActionReceipts().stream().filter(r -> !r.settled()).toList(); }
    }
    public sealed interface Result permits Known, Missing { }
    public record Known(Snapshot snapshot) implements Result { public Known { Objects.requireNonNull(snapshot); } }
    public record Missing(String reason) implements Result { public Missing { StrictJson.text(reason); } }
    private final SourcePort original;
    private final Map<Domain, ReaderBinding> readers;
    public FinanceStatePort(SourcePort original, List<ReaderBinding> installed) {
        this.original = Objects.requireNonNull(original);
        EnumMap<Domain, ReaderBinding> index = new EnumMap<>(Domain.class);
        for (ReaderBinding binding : List.copyOf(installed))
            require(index.putIfAbsent(binding.domain(), binding) == null, "two owning decoders claim the same domain");
        this.readers = Map.copyOf(index);
    }
    public Result read(PlanningRequest request) {
        return decode(request, Objects.requireNonNull(original.readUnderOriginalLock(request)));
    }
    public Result read(Session borrowed, PlanningRequest request) {
        return decode(request, Objects.requireNonNull(original.readUnderOriginalLock(Objects.requireNonNull(borrowed), request)));
    }
    private Result decode(PlanningRequest request, Read read) {
        if (read instanceof Unavailable unavailable) return new Missing(unavailable.reason());
        Head head = (Head) read;
        if (!head.current().equals(request.before())) return new Missing("canonical finance reader belongs to another complete current Game/frame");
        try {
            EnumMap<Domain, Ledger> ledgers = new EnumMap<>(Domain.class);
            EnumMap<Domain, String> unavailable = new EnumMap<>(Domain.class);
            java.util.EnumSet<Domain> seen = java.util.EnumSet.noneOf(Domain.class);
            for (Document body : head.bodies()) {
                require(seen.add(body.domain()), "duplicate canonical domain body");
                ReaderBinding decoder = readers.get(body.domain());
                if (decoder == null) {
                    unavailable.put(body.domain(), "owning domain decoder is not installed: " + body.domain());
                    continue;
                }
                try {
                    Obj row = decodeDocument(body.bytes());
                    Value pending = row.get("pending");
                    require(pending == Nil.INSTANCE || pending instanceof Obj, "explicit original pending field required");
                    Pending decoded = Objects.requireNonNull(decoder.reader().decode(body));
                    require((decoded == Pending.PENDING) == (pending instanceof Obj), "owning decoder and original pending token differ");
                    ledgers.put(body.domain(), new Ledger(body, row, decoded));
                } catch (IllegalArgumentException invalid) {
                    unavailable.put(body.domain(), "owning persistent decoder rejected original body: " + invalid.getMessage());
                }
            }
            return new Known(new Snapshot(head, ledgers, unavailable));
        } catch (IllegalArgumentException malformed) { return new Missing("canonical domain body is unavailable: " + malformed.getMessage()); }
    }
    private static Obj decodeDocument(byte[] original) {
        byte[] json = original.length >= 3 && original[0] == (byte) 0xef && original[1] == (byte) 0xbb && original[2] == (byte) 0xbf
                ? java.util.Arrays.copyOfRange(original, 3, original.length) : original;
        return org.xar.ck3.control.application.driver.DriverJson.object(json,4*1024*1024);
    }
}


