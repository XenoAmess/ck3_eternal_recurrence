package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.wave2.development.constructionvalue.ConstructionValuePolicy;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessment;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessmentCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.FinancingGapCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.WarFinancingCapabilityGap;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.Selection;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec.ObservedRequest;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionConsumer;

/** Actual registered reads in the original zero-spend gate -> quote -> current-cash order. No submit or writer. */
public final class OrdinaryConstructionCollector {
    @FunctionalInterface public interface EndingSnapshot {
        /** Real current snapshot from the same source-bound Driver assembler, after the actual native read. */
        Obj readCurrent(PlanningRequest request);
        default Obj readCurrent(Session session, PlanningRequest request) {
            Objects.requireNonNull(session);
            throw new IllegalArgumentException("borrowed original-writer ending snapshot reader is not installed");
        }
    }
    @FunctionalInterface public interface FinancingPending {
        /** Only the unique same-writer owned-submission producer mints Observed; native debt completeness is independent. */
        CanonicalFundingPending.Result readUnderOriginalWriterLock(PlanningRequest request);
        default CanonicalFundingPending.Result readUnderOriginalWriterLock(Session session, PlanningRequest request) {
            Objects.requireNonNull(session);
            throw new IllegalArgumentException("borrowed original-writer funding reader is not installed");
        }
    }
    public sealed interface Read permits Available, Missing, FrameChanged { }
    public record Available(Prepared value) implements Read { public Available { Objects.requireNonNull(value); } }
    public record Missing(String reason) implements Read { public Missing { require(reason != null && !reason.isEmpty(), "missing reason required"); } }
    public record FrameChanged(String reason) implements Read { public FrameChanged { require(reason != null && !reason.isEmpty(), "frame reason required"); } }
    public record Prepared(PlanningRequest request, Selection selection, OrdinaryFinanceCollector.Current current,
            Obj procurementDecision, Obj financing, CanonicalFundingPending.Result fundingSource, ObservedRequest before) {
        public Prepared { Objects.requireNonNull(request); Objects.requireNonNull(selection); Objects.requireNonNull(current);
            Objects.requireNonNull(procurementDecision); Objects.requireNonNull(financing); Objects.requireNonNull(fundingSource); Objects.requireNonNull(before);
            require(before.input().stage() == OrdinaryWartimeConstruction.Stage.BEFORE_OPTIONAL_QUERY, "actual pre-query stage required"); }
    }
    public sealed interface Quote permits Quoted, QuoteMissing, QuoteFrameChanged { }
    public record Quoted(ObservedRequest value, PlanningReadReceipt nativeRead, PlanningReadReceipt cashRead,
            Obj financing, CanonicalFundingPending.Result fundingSource) implements Quote {
        public Quoted { Objects.requireNonNull(value); Objects.requireNonNull(nativeRead); Objects.requireNonNull(cashRead);
            Objects.requireNonNull(financing); Objects.requireNonNull(fundingSource);
            require(value.input().stage() == OrdinaryWartimeConstruction.Stage.QUOTED_OUTLAY, "actual quoted stage required"); }
    }
    public record QuoteMissing(String reason) implements Quote { public QuoteMissing { require(reason != null && !reason.isEmpty(), "quote reason required"); } }
    public record QuoteFrameChanged(String reason) implements Quote { public QuoteFrameChanged { require(reason != null && !reason.isEmpty(), "quote frame reason required"); } }
    public sealed interface MaterialRead permits MaterialAvailable, MaterialMissing, MaterialFrameChanged { }
    public record MaterialAvailable(Obj queryInput, Optional<Obj> root, Optional<Obj> cash, List<PlanningReadReceipt> originalReads) implements MaterialRead {
        public MaterialAvailable { Objects.requireNonNull(queryInput); Objects.requireNonNull(root); Objects.requireNonNull(cash); originalReads = List.copyOf(originalReads); }
    }
    public record MaterialMissing(String reason) implements MaterialRead { public MaterialMissing { require(reason != null && !reason.isEmpty(), "material reason required"); } }
    public record MaterialFrameChanged(String reason) implements MaterialRead { public MaterialFrameChanged { require(reason != null && !reason.isEmpty(), "material frame reason required"); } }
    public sealed interface PeacetimeRead permits PeacetimeAvailable, PeacetimeMissing, PeacetimeFrameChanged { }
    public record PeacetimeAvailable(Obj finalizedQuery,
            org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.QuoteCashObservation cash,
            List<PlanningReadReceipt> originalReads) implements PeacetimeRead {
        public PeacetimeAvailable { Objects.requireNonNull(finalizedQuery); Objects.requireNonNull(cash); originalReads = List.copyOf(originalReads); }
    }
    public record PeacetimeMissing(String reason) implements PeacetimeRead { public PeacetimeMissing { require(reason != null && !reason.isEmpty(), "peacetime source reason required"); } }
    public record PeacetimeFrameChanged(String reason) implements PeacetimeRead { public PeacetimeFrameChanged { require(reason != null && !reason.isEmpty(), "peacetime frame reason required"); } }
    private final OrdinaryFinanceCollector finance;
    private final EndingSnapshot ending;
    private final FinancingPending funding;
    public OrdinaryConstructionCollector(OrdinaryFinanceCollector finance, EndingSnapshot ending, FinancingPending funding) {
        this.finance = Objects.requireNonNull(finance); this.ending = Objects.requireNonNull(ending); this.funding = Objects.requireNonNull(funding);
    }
    public FinanceStatePort.Result state(PlanningRequest request) { return finance.state(request); }
    public FinanceStatePort.Result state(Session session, PlanningRequest request) { return finance.state(Objects.requireNonNull(session), request); }
    public Read before(PlanningRequest request, Selection selection, Obj procurementDecision, String expenditureKind) {
        return before(Optional.empty(), request, selection, procurementDecision, expenditureKind);
    }
    public Read before(Session session, PlanningRequest request, Selection selection, Obj procurementDecision, String expenditureKind) {
        return before(Optional.of(Objects.requireNonNull(session)), request, selection, procurementDecision, expenditureKind);
    }
    private Read before(Optional<Session> session, PlanningRequest request, Selection selection, Obj procurementDecision, String expenditureKind) {
        Objects.requireNonNull(request); Objects.requireNonNull(selection); Objects.requireNonNull(procurementDecision);
        try {
            require(List.of("new_building", "upgrade_building", "new_holding").contains(expenditureKind), "closed original construction kind required");
            var read = session.isPresent() ? finance.current(session.orElseThrow(), request) : finance.current(request);
            if (!(read instanceof OrdinaryFinanceCollector.Known<OrdinaryFinanceCollector.Current> known))
                return new Missing(((OrdinaryFinanceCollector.Unavailable<?>) read).missing().reason());
            var current = known.value();
            requireStableSnapshot(request, ending(session, request));
            FinancingCapture financing = financing(session, request, current);
            Obj cash = cash(request, current, procurementDecision, expenditureKind, BigInteger.ZERO);
            ObservedRequest observed = envelope(selection, "BEFORE_OPTIONAL_QUERY", cash, Nil.INSTANCE, financing.input());
            return new Available(new Prepared(request, selection, current, procurementDecision, financing.input(), financing.source(), observed));
        } catch (Changed rejected) { return new FrameChanged(rejected.getMessage()); }
        catch (IllegalArgumentException rejected) { return new Missing("current construction cash/source unavailable: " + rejected.getMessage()); }
    }
    public Quote quote(Prepared prepared) {
        return quote(Optional.empty(), prepared);
    }
    public Quote quote(Session session, Prepared prepared) {
        return quote(Optional.of(Objects.requireNonNull(session)), prepared);
    }
    private Quote quote(Optional<Session> session, Prepared prepared) {
        Objects.requireNonNull(prepared); PlanningRequest request = prepared.request();
        try {
            var nativeRead = query(session, FinanceReadContracts.Query.CONSTRUCTION, request);
            if (!(nativeRead instanceof OrdinaryFinanceCollector.Known<FinanceReadContracts.Packet> nativeKnown))
                return new QuoteMissing("registered original construction native query unavailable");
            FinanceReadContracts.Packet packet = nativeKnown.value(); stableReceipt(request, packet.receipt());
            Obj actualEnding = ending(session, request); requireStableSnapshot(request, actualEnding);
            Obj nativeInput = obj("schema", new Text(ConstructionQueryCodec.SCHEMA), "starting_snapshot", request.observations().snapshot(),
                    "ending_snapshot", actualEnding, "native_envelope", DriverJson.object(packet.originalFrame(), ConstructionQueryCodec.MAX_BYTES),
                    "expected_revision", new IntegerValue(request.before().frame().revision()), "native_query_request_id", new Text(packet.receipt().requestId()),
                    "material_receipt", new Bool(false), "wartime_observation", new Bool(false));
            OrdinaryWartimeConstruction.NativeQuote selected = new OrdinaryWartimeConstruction.NativeQuote(encode(nativeInput));
            if (selected.selected().isEmpty()) return new QuoteMissing("original native finalizer has no qualified positive legal budgeted construction");
            var candidate = selected.selected().orElseThrow();
            var cashRead = query(session, FinanceReadContracts.Query.CASH, request);
            if (!(cashRead instanceof OrdinaryFinanceCollector.Known<FinanceReadContracts.Packet> cashKnown))
                return new QuoteMissing("registered native current/all-raised cash read unavailable");
            FinanceReadContracts.Packet cashPacket = cashKnown.value(); stableReceipt(request, cashPacket.receipt());
            requireStableSnapshot(request, ending(session, request));
            Obj rawCash = object(cashPacket.result().get("war_cash_current_resources"), "actual native current cash resources");
            var actualCash = RawCashCodec.normalize(DriverJson.encode(rawCash), DriverJson.encode(request.observations().snapshot()));
            Obj normalized = object(parse(actualCash.toJson()), "normalized native cash");
            var frame = request.before().frame();
            normalized = normalized.with("queried_snapshot_id", new Text(frame.snapshotId())).with("queried_revision", new IntegerValue(frame.revision()))
                    .with("queried_native_revision", new IntegerValue(frame.identity().nativeRevision()));
            Obj cashObservation = obj("kind", new Text("observed"), "cash", normalized,
                    "reserve_gold_raw", new IntegerValue(ConstructionValuePolicy.RESERVE_RAW));
            Obj outlay = obj("query_observation", nativeInput, "cash_observation", cashObservation);
            Obj cash = cash(request, prepared.current(), prepared.procurementDecision(), selected.constructionKind().orElseThrow(),
                    candidate.candidate().cost().orElseThrow());
            // Funding pending is reread; neither a prior no-pending projection nor a loan/refund quote is money.
            FinancingCapture financing = financing(session, request, prepared.current(), Optional.of(OrdinaryFinanceCollector.loanFromCash(request,
                    new OrdinaryFinanceCollector.Known<>(new OrdinaryFinanceCollector.Cash(actualCash, cashPacket)))));
            ObservedRequest quoted = envelope(prepared.selection(), "QUOTED_OUTLAY", cash, outlay, financing.input());
            return new Quoted(quoted, packet.receipt(), cashPacket.receipt(), financing.input(), financing.source());
        } catch (Changed rejected) { return new QuoteFrameChanged(rejected.getMessage()); }
        catch (IllegalArgumentException rejected) { return new QuoteMissing("native construction quote rejected: " + rejected.getMessage()); }
    }
    private OrdinaryFinanceCollector.Read<FinanceReadContracts.Packet> query(Optional<Session> session, FinanceReadContracts.Query query, PlanningRequest request) {
        return session.isPresent() ? finance.query(session.orElseThrow(), query, request) : finance.query(query, request);
    }
    /** Real peaceful M5 proposal source. This is observation only; the sole normal construction policy still gates any spend. */
    public PeacetimeRead peacetime(Session session, PlanningRequest request) {
        Objects.requireNonNull(session); Objects.requireNonNull(request);
        try {
            require(request.observations().paused() && request.observations().mapReady() && !request.observations().foregroundPresent()
                    && !request.observations().warInProgress()
                    && array(request.observations().snapshot().get("player_armies"), "actual player armies").isEmpty(),
                    "peaceful M5 source requires the actual paused idle map with no active war or player army");
            var nativeRead = finance.query(session, FinanceReadContracts.Query.CONSTRUCTION, request);
            if (!(nativeRead instanceof OrdinaryFinanceCollector.Known<FinanceReadContracts.Packet> known))
                return new PeacetimeMissing("registered actual construction query unavailable");
            stableReceipt(request, known.value().receipt());
            Obj current = ending.readCurrent(session, request); requireStableSnapshot(request, current);
            Obj input = obj("schema", new Text(ConstructionQueryCodec.SCHEMA), "starting_snapshot", request.observations().snapshot(),
                    "ending_snapshot", current, "native_envelope", DriverJson.object(known.value().originalFrame(), ConstructionQueryCodec.MAX_BYTES),
                    "expected_revision", new IntegerValue(request.before().frame().revision()), "native_query_request_id", new Text(known.value().receipt().requestId()),
                    "material_receipt", new Bool(false), "wartime_observation", new Bool(false));
            Obj finalized = finalizePeacetime(input);
            var original = new java.util.ArrayList<PlanningReadReceipt>(); original.add(known.value().receipt());
            org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.QuoteCashObservation cash =
                    new org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.UnavailableCashObservation();
            var cashRead = finance.query(session, FinanceReadContracts.Query.CASH, request);
            if (cashRead instanceof OrdinaryFinanceCollector.Known<FinanceReadContracts.Packet> cashKnown) {
                stableReceipt(request, cashKnown.value().receipt()); original.add(cashKnown.value().receipt());
                Obj raw = object(cashKnown.value().result().get("war_cash_current_resources"), "actual peaceful current cash resources");
                Obj normalized = object(parse(RawCashCodec.normalize(encode(raw), encode(request.observations().snapshot())).toJson()), "normalized peaceful cash");
                var frame = request.before().frame();
                normalized = normalized.with("queried_snapshot_id", new Text(frame.snapshotId())).with("queried_revision", new IntegerValue(frame.revision()))
                        .with("queried_native_revision", new IntegerValue(frame.identity().nativeRevision()));
                cash = new org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.ObservedCash(
                        org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyCodec.decodeCash(encode(normalized)), ConstructionValuePolicy.RESERVE_RAW);
            }
            requireStableSnapshot(request, ending.readCurrent(session, request));
            return new PeacetimeAvailable(finalized, cash, original);
        } catch (Changed rejected) { return new PeacetimeFrameChanged(rejected.getMessage()); }
        catch (IllegalArgumentException rejected) { return new PeacetimeMissing("actual peaceful construction source rejected: " + rejected.getMessage()); }
    }
    static Obj finalizePeacetime(Obj actualInput) {
        require(new Bool(false).equals(actualInput.get("material_receipt")) && new Bool(false).equals(actualInput.get("wartime_observation")),
                "M5 peaceful proposal input cannot borrow completion or wartime-only observation");
        Obj finalized = DriverJson.object(ConstructionQueryCodec.finalizeObservation(encode(actualInput)), ConstructionQueryCodec.MAX_BYTES);
        require(List.of(new Text("selected"), new Text("no_legal_budgeted_building")).contains(finalized.get("status")),
                "actual native construction finalizer is incomplete: " + finalized.get("status"));
        return finalized;
    }
    /** Cold/completion material reads borrow the actual writer session; absent optional income/cash stays absent. */
    public MaterialRead material(Session session, PlanningRequest request) {
        Objects.requireNonNull(session); Objects.requireNonNull(request);
        try {
            var original = new java.util.ArrayList<PlanningReadReceipt>(); Optional<Obj> root = Optional.empty(), cash = Optional.empty();
            var rootRead = finance.query(session, FinanceReadContracts.Query.ROOT, request);
            if (rootRead instanceof OrdinaryFinanceCollector.Known<FinanceReadContracts.Packet> known) {
                stableReceipt(request, known.value().receipt()); original.add(known.value().receipt());
                if (new Text("available").equals(known.value().result().get("status")))
                    root = Optional.of(object(known.value().result().get("campaign_root_context"), "actual current income root"));
            }
            var cashRead = finance.query(session, FinanceReadContracts.Query.CASH, request);
            if (cashRead instanceof OrdinaryFinanceCollector.Known<FinanceReadContracts.Packet> known) {
                stableReceipt(request, known.value().receipt()); original.add(known.value().receipt());
                Obj raw = object(known.value().result().get("war_cash_current_resources"), "actual material cash resources");
                Obj normalized = object(parse(RawCashCodec.normalize(encode(raw), encode(request.observations().snapshot())).toJson()), "normalized material cash");
                var frame = request.before().frame();
                cash = Optional.of(normalized.with("queried_snapshot_id", new Text(frame.snapshotId())).with("queried_revision", new IntegerValue(frame.revision()))
                        .with("queried_native_revision", new IntegerValue(frame.identity().nativeRevision())));
            }
            var nativeRead = finance.query(session, FinanceReadContracts.Query.CONSTRUCTION, request);
            if (!(nativeRead instanceof OrdinaryFinanceCollector.Known<FinanceReadContracts.Packet> known)) return new MaterialMissing("registered current material Native source unavailable");
            stableReceipt(request, known.value().receipt()); original.add(known.value().receipt());
            Obj actualEnding = ending.readCurrent(session, request); requireStableSnapshot(request, actualEnding);
            Obj queryInput = obj("schema", new Text(ConstructionQueryCodec.SCHEMA), "starting_snapshot", request.observations().snapshot(),
                    "ending_snapshot", actualEnding, "native_envelope", DriverJson.object(known.value().originalFrame(), ConstructionQueryCodec.MAX_BYTES),
                    "expected_revision", new IntegerValue(request.before().frame().revision()), "native_query_request_id", new Text(known.value().receipt().requestId()),
                    "material_receipt", new Bool(true), "wartime_observation", new Bool(false));
            Obj finalized = DriverJson.object(ConstructionQueryCodec.finalizeObservation(encode(queryInput)), ConstructionQueryCodec.MAX_BYTES);
            require(new Text("material_source").equals(finalized.get("status")), "current material query is not source_available");
            return new MaterialAvailable(queryInput, root, cash, original);
        } catch (Changed rejected) { return new MaterialFrameChanged(rejected.getMessage()); }
        catch (IllegalArgumentException rejected) { return new MaterialMissing("current material observation rejected: " + rejected.getMessage()); }
    }
    private Obj ending(Optional<Session> session, PlanningRequest request) {
        return session.isPresent() ? ending.readCurrent(session.orElseThrow(), request) : ending.readCurrent(request);
    }
    private record FinancingCapture(Obj input, CanonicalFundingPending.Result source) {
        private FinancingCapture { Objects.requireNonNull(input); Objects.requireNonNull(source); }
    }
    private FinancingCapture financing(Optional<Session> session, PlanningRequest request, OrdinaryFinanceCollector.Current current) {
        return financing(session, request, current, Optional.empty());
    }
    private FinancingCapture financing(Optional<Session> session, PlanningRequest request, OrdinaryFinanceCollector.Current current,
            Optional<OrdinaryFinanceCollector.Read<OrdinaryFinanceCollector.LoanObservation>> originalCash) {
        var source = Objects.requireNonNull(session.isPresent()
                ? funding.readUnderOriginalWriterLock(session.orElseThrow(), request) : funding.readUnderOriginalWriterLock(request));
        EmergencyFinancingAssessment.PendingObservation pending = source instanceof CanonicalFundingPending.Observed observed
                ? observed.pending() : new EmergencyFinancingAssessment.PendingUnavailable();
        Value observed;
        if (pending instanceof EmergencyFinancingAssessment.PendingUnavailable) observed = Nil.INSTANCE;
        else if (pending instanceof EmergencyFinancingAssessment.NoPendingAction) observed = obj("status", new Text("no_pending_action"));
        else {
            var action = (EmergencyFinancingAssessment.PendingAction) pending;
            observed = obj("status", new Text(action.state().name()), "kind", new Text(action.kind().name()),
                    "action_id", new Text(action.actionId()), "procurement_epoch", new Text(action.procurementEpoch()));
        }
        Obj gap = OrdinaryFinanceCollector.financingGap(request, current);
        Optional<OrdinaryFinanceCollector.LoanObservation> loan = Optional.empty();
        if (WarFinancingCapabilityGap.observe(FinancingGapCodec.decode(DriverJson.encode(gap))).isPresent()) {
            var read = originalCash.orElseGet(() -> session.isPresent() ? finance.loan(session.orElseThrow(), request) : finance.loan(request));
            if (read instanceof OrdinaryFinanceCollector.Known<OrdinaryFinanceCollector.LoanObservation> known) loan = Optional.of(known.value());
        }
        Obj input = OrdinaryFinanceCollector.financingRequest(gap, loan, observed);
        EmergencyFinancingAssessmentCodec.decode(DriverJson.encode(input)); return new FinancingCapture(input, source);
    }
    private static Obj cash(PlanningRequest request, OrdinaryFinanceCollector.Current current, Obj procurement, String kind, BigInteger cost) {
        return OrdinaryFinanceCollector.cashContext(request, current, WartimeConstructionCodec.SCHEMA, null)
                .with("kind", new Text(kind)).with("construction_gold_raw", new IntegerValue(cost)).with("procurement_decision", procurement);
    }
    public static ObservedRequest envelope(Selection selection, String stage, Obj cash, Value quoted, Value financing) {
        return new ObservedRequest(DriverJson.encode(obj("schema", new Text(OrdinaryWartimeConstructionCodec.SCHEMA), "stage", new Text(stage),
                "original_selected_step", selection.step().<Value>map(Text::new).orElse(Nil.INSTANCE),
                "original_phase", selection.phase().<Value>map(Text::new).orElse(Nil.INSTANCE), "opportunity", new Text(selection.opportunity().name()),
                "cash_input", cash, "quoted_outlay", quoted, "financing_request", financing)));
    }
    private static void stableReceipt(PlanningRequest request, PlanningReadReceipt receipt) {
        if (!receipt.before().binding().observed().equals(request.before()) || !receipt.after().binding().observed().equals(request.before())
                || !receipt.before().paused() || !receipt.after().paused() || !receipt.before().mapReady() || !receipt.after().mapReady())
            throw new Changed("native query changed the actual complete planning frame; refresh ordinary planning");
    }
    public static void requireStableSnapshot(PlanningRequest request, Obj current) {
        Obj original = request.observations().snapshot();
        for (String key : List.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id", "paused", "map_ready", "active_event", "pending_character_interaction"))
            if (current.get(key) == null || !current.get(key).equals(original.get(key))) throw new Changed("current snapshot changed at " + key);
        if (!object(current.get("played_character"), "current actor").get("character_id").equals(new IntegerValue(request.before().frame().identity().player())))
            throw new Changed("current construction actor changed");
    }
    private static final class Changed extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        private Changed(String message) { super(message); }
    }
}
