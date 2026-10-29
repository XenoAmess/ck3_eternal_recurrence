package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.military.OrdinaryWhitePeacePolicy;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.family.FamilyObligations;
import org.xar.ck3.control.nativebridge.capabilities.family.FamilyObligationsQueries;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContextRead;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryPreflight.Role;

/** Actual sequential quote producers, shared by public/ordinary preparation and original-receipt replay. */
public final class ArmyOrdinaryPairedQuotes implements ArmyOrdinaryPreflight.Queries {
    public record Producers(ArmyRetreatFrames frames, ArmyWarReads wars, ArmyClosedReadContracts closed,
            ArmyWindowReads windows, ReadContract<Obj> family, PlayerHolyOrderContextRead holyOrders) {
        public Producers {
            Objects.requireNonNull(frames); Objects.requireNonNull(wars); Objects.requireNonNull(closed); Objects.requireNonNull(windows);
            Objects.requireNonNull(family); Objects.requireNonNull(holyOrders);
            StrictJson.require(family.contractId().equals(FamilyObligationsQueries.CONTRACT_ID), "the identical installed family obligations contract is required");
        }
    }
    private final RootRuntimeContext context;
    private final Producers producers;
    public ArmyOrdinaryPairedQuotes(RootRuntimeContext actualContext, Producers actualProducers) {
        context = Objects.requireNonNull(actualContext); producers = Objects.requireNonNull(actualProducers);
    }
    public Producers producers() { return producers; }
    @Override public List<ArmyOrdinaryPreflight.Query<?>> plans(ArmyCalls.Call call, ArmyTypes.Context source) {
        StrictJson.require(!(call instanceof ArmyCalls.Declaration) && call.method() != PublicMethod.OFFER_WHITE_PEACE,
                "dependent quote plans require their first actual Known receipt");
        try {
            var actual = producers.frames().current(source.deadline()); requireCurrent(actual.actual(), source);
            return simple(call, actual.actual(), source.deadline());
        } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IllegalStateException("actual Army quote observation interrupted", interrupted); }
    }
    @Override public List<ArmyOrdinaryPreflight.Read> observe(Session same, ArmyCalls.Call call, ArmyTypes.Context source,
            Complete actual, PlanningReadPort reads, ActionPorts.OutcomeArchive archive) {
        try {
            context.writer().requireSession(same); requireCurrent(actual, source);
            var frame = new ArmyRetreatFrames.Current(actual, source.deadline());
            if (call instanceof ArmyCalls.Declaration declaration) {
                var known = currentDeclarationOriginal(same, producers.wars(), context.readCatalog(), source, actual, context.clock());
                // The original DECL request/timeout is immutable. Only the different dependent quote uses this fresh continuation deadline.
                var first = declarations(actual, known.receipt().request().deadline());
                var original = ArmyOrdinaryPreflight.accept(first, known, actual, archive);
                // The owning producer has now decoded/published the original receipt and privately minted this lease.
                var lease = producers.wars().requireCurrentDeclarations(frame); lease.selected(frame, declaration.declarationId());
                sameFrame(frame);
                var second = declarationFinal(declaration, frame, lease);
                var last = ArmyOrdinaryPreflight.observeOne(same, second, actual, reads, archive); sameFrame(frame);
                return List.of(original, last);
            }
            if (call.method() == PublicMethod.OFFER_WHITE_PEACE) {
                var selected = (ArmyCalls.War) call;
                var first = war(Role.WAR_OPTIONS, new ArmyWarReads.Selection(new ArmyCalls.War(PublicMethod.QUERY_WAR_TERMINATION_OPTIONS, revision(actual), selected.warId()), frame, Optional.empty()));
                var original = ArmyOrdinaryPreflight.observeOne(same, first, actual, reads, archive);
                if (!needsTerms(actual, original, archive, selected.warId())) return List.of(original);
                sameFrame(frame);
                var terms = war(Role.WAR_TERMS, new ArmyWarReads.Selection(new ArmyCalls.War(PublicMethod.QUERY_WAR_TERMINATION_TERMS, revision(actual), selected.warId()), frame, Optional.empty()));
                return List.of(original, ArmyOrdinaryPreflight.observeOne(same, terms, actual, reads, archive));
            }
            List<ArmyOrdinaryPreflight.Query<?>> plans = simple(call, actual, source.deadline()); ArmyOrdinaryPreflight.requireInventory(plans);
            List<ArmyOrdinaryPreflight.Read> result = new ArrayList<>();
            for (var query : plans) result.add(ArmyOrdinaryPreflight.observeOne(same, query, actual, reads, archive));
            return List.copyOf(result);
        } catch (IOException failure) { throw new UncheckedIOException("actual sequential Army quotes unavailable", failure); }
    }
    @Override public List<ArmyOrdinaryPreflight.Read> replay(ArmyCalls.Call call, ArmyTypes.Context source, Complete actual,
            List<ExactRef> references, ActionPorts.OutcomeArchive archive) {
        List<ArmyOrdinaryPreflight.Query<?>> plans = originalPlans(call, source, actual, references, archive);
        List<ArmyOrdinaryPreflight.Read> result = new ArrayList<>();
        for (int i = 0; i < references.size(); i++) result.add(ArmyOrdinaryPreflight.replayOne(plans.get(i), actual, references.get(i), archive));
        return List.copyOf(result);
    }
    /** Rebuild the exact installed before-quote contract from its full original inventory. No current frame, Native read or submit. */
    public ArmyOrdinaryPreflight.Query<?> originalPlan(ArmyCalls.Call call, Complete actualBefore, List<ExactRef> fullOriginalReferences,
            PlanningReadReceipt selectedOriginal, ActionPorts.OutcomeArchive sameArchive) {
        Objects.requireNonNull(selectedOriginal); fullOriginalReferences = List.copyOf(fullOriginalReferences);
        ExactRef selectedReference = sameArchive.readReferenceOf(selectedOriginal);
        int index = fullOriginalReferences.indexOf(selectedReference);
        StrictJson.require(index >= 0 && sameArchive.loadRead(selectedReference).equals(selectedOriginal), "selected Army quote is outside its original canonical inventory");
        Instant continuation = selectedOriginal.request().deadline();
        if (call instanceof ArmyCalls.Declaration) {
            StrictJson.require(fullOriginalReferences.size() == 2, "declaration requires the original choices and its continuation quote");
            continuation = original(fullOriginalReferences.getLast(), actualBefore, sameArchive).request().deadline();
        }
        var source = new ArmyTypes.Context(actualBefore.identity(), actualBefore.source(), actualBefore.sessionId(), continuation);
        return originalPlans(call, source, actualBefore, fullOriginalReferences, sameArchive).get(index);
    }
    private List<ArmyOrdinaryPreflight.Query<?>> originalPlans(ArmyCalls.Call call, ArmyTypes.Context source, Complete actual,
            List<ExactRef> references, ActionPorts.OutcomeArchive archive) {
        requireCurrent(actual, source); references = List.copyOf(references);
        StrictJson.require(references.size() <= 16 && references.stream().distinct().count() == references.size(), "Army original quote inventory is oversized or duplicated");
        // DECL alone has an explicit original late-read/canonical reuse predicate. Other families still require the exact caller deadline.
        if (!(call instanceof ArmyCalls.Declaration))
            for (ExactRef ref : references) StrictJson.require(original(ref, actual, archive).request().deadline().equals(source.deadline()), "Army original quotes changed the caller deadline");
        if (call instanceof ArmyCalls.Declaration declaration) {
            StrictJson.require(references.size() == 2, "declaration requires both original choices and finalized-CB receipts");
            var firstReceipt = original(references.getFirst(), actual, archive);
            var first = declarations(actual, firstReceipt.request().deadline());
            ArmyOrdinaryPreflight.replayOne(first, actual, references.getFirst(), archive);
            var secondReceipt = original(references.getLast(), actual, archive);
            StrictJson.require(secondReceipt.request().deadline().equals(source.deadline()), "declaration continuation quote changed its exact caller deadline");
            requireCurrentDeclaration(first, firstReceipt, declarations(actual, source.deadline()), actual);
            var second = declarationFinal(declaration, actual, secondReceipt.request().deadline(), firstReceipt, archive);
            ArmyOrdinaryPreflight.replayOne(second, actual, references.getLast(), archive);
            return List.of(first, second);
        }
        if (call.method() == PublicMethod.OFFER_WHITE_PEACE) {
            StrictJson.require(references.size() == 1 || references.size() == 2, "white-peace original quote inventory is absent or oversized");
            var selected = (ArmyCalls.War) call; var firstReceipt = original(references.getFirst(), actual, archive);
            var first = war(Role.WAR_OPTIONS, new ArmyWarReads.Selection(new ArmyCalls.War(PublicMethod.QUERY_WAR_TERMINATION_OPTIONS, revision(actual), selected.warId()), new ArmyRetreatFrames.Current(actual, firstReceipt.request().deadline()), Optional.empty()));
            var read = ArmyOrdinaryPreflight.replayOne(first, actual, references.getFirst(), archive);
            boolean needsTerms = needsTerms(actual, read, archive, selected.warId());
            StrictJson.require(references.size() == (needsTerms ? 2 : 1), "white-peace original dependent terms inventory changed");
            if (!needsTerms) return List.of(first);
            var termsReceipt = original(references.getLast(), actual, archive);
            var terms = war(Role.WAR_TERMS, new ArmyWarReads.Selection(new ArmyCalls.War(PublicMethod.QUERY_WAR_TERMINATION_TERMS, revision(actual), selected.warId()), new ArmyRetreatFrames.Current(actual, termsReceipt.request().deadline()), Optional.empty()));
            ArmyOrdinaryPreflight.replayOne(terms, actual, references.getLast(), archive);
            return List.of(first, terms);
        }
        List<ArmyOrdinaryPreflight.Query<?>> templates = simple(call, actual, source.deadline());
        StrictJson.require(templates.size() == references.size(), "ordinary Army original quote inventory changed");
        ArmyOrdinaryPreflight.requireInventory(templates);
        return List.copyOf(templates);
    }
    private List<ArmyOrdinaryPreflight.Query<?>> simple(ArmyCalls.Call call, Complete frame, Instant deadline) {
        var source = new ArmyTypes.Context(frame.identity(), frame.source(), frame.sessionId(), deadline);
        return switch (ArmyOrdinaryActionPreparation.kind(call)) {
            case RAISE_TROOPS_DEFAULT -> List.of(closed(Role.DEFAULT_RAISE, new ArmyCalls.Frame(PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1, revision(frame)), source));
            case SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1 -> List.of(closed(Role.GATHERING, new ArmyCalls.Frame(PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1, revision(frame)), source));
            case SURRENDER_WAR -> List.of(war(Role.WAR_OPTIONS, new ArmyWarReads.Selection(new ArmyCalls.War(PublicMethod.QUERY_WAR_TERMINATION_OPTIONS, revision(frame), ((ArmyCalls.War) call).warId()), new ArmyRetreatFrames.Current(frame, deadline), Optional.empty())));
            case START_ASSAULT, STOP_ASSAULT -> assault((ArmyCalls.Siege) call, frame, deadline);
            case SUBMIT_CALL_ALLY_TO_WAR_PRIVATE_V1 -> List.of(family((ArmyCalls.CallAlly) call, source));
            case HIRE_HOLY_ORDER_V1 -> List.of(holy(source));
            case CLOSE_WAR_DECLARED_OVERVIEW_V1, CLOSE_WAR_RESULTS_WINDOW_V1 -> List.of(window((ArmyCalls.Frame) call, frame, deadline));
            case DECLARE_WAR, OFFER_WHITE_PEACE -> throw new IllegalStateException("dependent quote must run its first original receipt phase");
            case MOVE_ARMY, DISBAND_ARMY, ENFORCE_DEMANDS, SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1 -> List.of();
            case HIRE_MERCENARY_V1, ASSIGN_ARMY_COMMANDER_V1 -> throw new IllegalArgumentException("existing finance/commander domain owns its actual quotes");
        };
    }
    private List<ArmyOrdinaryPreflight.Query<?>> assault(ArmyCalls.Siege call, Complete frame, Instant deadline) {
        if (ArmyAssaultSelection.select(frame.semantic(), List.of(), call.siege().value()).isPresent()) return List.of();
        List<ArmyOrdinaryPreflight.Query<?>> result = new ArrayList<>(); var unique = new java.util.HashSet<BigInteger>();
        for (Value raw : OpportunityJson.array(frame.semantic().get("active_wars"), "complete active wars")) {
            BigInteger id = OpportunityJson.integer(OpportunityJson.object(raw, "actual war").get("war_id"), "full WarID");
            StrictJson.require(id.signum() >= 0 && id.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0 && unique.add(id), "occupation query requires bounded unique original full WarIDs");
            result.add(war(Role.HOLDING_SIEGE, new ArmyWarReads.Selection(new ArmyCalls.War(PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1, revision(frame), id), new ArmyRetreatFrames.Current(frame, deadline), Optional.empty())));
        }
        StrictJson.require(result.size() <= 15, "original assault quote closure exceeds the actual postcondition read budget"); return List.copyOf(result);
    }
    private ArmyOrdinaryPreflight.Query<ArmyWarReadCodec.Observation> war(Role role, ArmyWarReads.Selection selection) {
        return war(producers.wars(), context.readCatalog(), role, selection);
    }
    private static ArmyOrdinaryPreflight.Query<ArmyWarReadCodec.Observation> war(ArmyWarReads wars, RootReadContractCatalog catalog,
            Role role, ArmyWarReads.Selection selection) {
        var contract = wars.contract(catalog, selection); var c = selection.context();
        return new ArmyOrdinaryPreflight.Query<>(role, contract, new PlanningReadRequest(c.before(), c.source(), c.sessionId(), contract.operation(), ArmyWarReads.arguments(selection.input()), c.deadline()), ArmyWarReadCodec::encode);
    }
    private ArmyOrdinaryPreflight.Query<ArmyClosedReads.Observation> closed(Role role, ArmyCalls.Frame call, ArmyTypes.Context source) {
        var selection = new ArmyClosedReadContracts.Selection(call, source);
        return new ArmyOrdinaryPreflight.Query<>(role, producers.closed().issue(context.readCatalog(), selection), producers.closed().request(selection), value -> ArmyClosedReadCodec.encode(value, source));
    }
    public ArmyOrdinaryPreflight.Query<Obj> family(ArmyCalls.CallAlly call, ArmyTypes.Context source) {
        var arguments = new FamilyObligations.Request(source.before().frame().revision(), Optional.empty(), false, OptionalLong.empty(), OptionalLong.of(Integer.toUnsignedLong(call.recipient().value())), false);
        var contract = producers.family();
        return new ArmyOrdinaryPreflight.Query<>(Role.FAMILY_OBLIGATIONS, contract, new PlanningReadRequest(source.before(), source.source(), source.sessionId(), contract.operation(), FamilyObligationsQueries.arguments(arguments), source.deadline()), ArmyOrdinaryPairedQuotes::raw);
    }
    public ArmyOrdinaryPreflight.Query<PlayerHolyOrderContextRead.Observation> holy(ArmyTypes.Context source) {
        var contract = producers.holyOrders().contract();
        return new ArmyOrdinaryPreflight.Query<>(Role.HOLY_ORDER_CONTEXT, contract, new PlanningReadRequest(source.before(), source.source(), source.sessionId(), contract.operation(), new Obj(java.util.Map.of()), source.deadline()), value -> raw(PlayerHolyOrderContextRead.flattened(value)));
    }
    private ArmyOrdinaryPreflight.Query<ArmyWindowCodec.Observation> window(ArmyCalls.Frame action, Complete frame, Instant deadline) {
        PublicMethod method = action.method() == PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1 ? PublicMethod.QUERY_WAR_DECLARED_OVERVIEW_V1 : PublicMethod.QUERY_WAR_RESULTS_WINDOW_V1;
        var source = new ArmyTypes.Context(frame.identity(), frame.source(), frame.sessionId(), deadline);
        var selection = new ArmyWindowReads.Selection(new ArmyCalls.Frame(method, revision(frame)), source, frame.connectionGeneration(), ArmyWindowReads.driverGeneration(frame));
        return new ArmyOrdinaryPreflight.Query<>(method == PublicMethod.QUERY_WAR_DECLARED_OVERVIEW_V1 ? Role.OVERVIEW : Role.RESULTS, producers.windows().issue(context.readCatalog(), selection), producers.windows().request(selection), value -> raw(value.normalized()));
    }
    public ArmyOrdinaryPreflight.Query<ArmyWarReadCodec.Observation> declarations(Complete actual, Instant deadline) {
        return declarations(producers.wars(), context.readCatalog(), actual, deadline);
    }
    private static ArmyOrdinaryPreflight.Query<ArmyWarReadCodec.Observation> declarations(ArmyWarReads wars,
            RootReadContractCatalog catalog, Complete actual, Instant deadline) {
        var frame = new ArmyRetreatFrames.Current(actual, deadline);
        var call = new ArmyCalls.Frame(PublicMethod.QUERY_DECLARABLE_WARS, revision(actual));
        var selected = new ArmyWarReads.Selection(call, frame, Optional.empty());
        return war(wars, catalog, Role.DECLARATIONS, selected);
    }
    /** The actual observe path and its real writer regression share this one first phase. No Root proof, Known or pending store is constructed here. */
    public static PlanningReadResult.Known<ArmyWarReadCodec.Observation> currentDeclarationOriginal(Session same, ArmyWarReads wars,
            RootReadContractCatalog catalog, ArmyTypes.Context source, Complete actual, Clock clock) throws IOException {
        Objects.requireNonNull(same); Objects.requireNonNull(wars); Objects.requireNonNull(catalog); Objects.requireNonNull(clock);
        requireCurrent(actual, source);
        StrictJson.require(clock.instant().isBefore(source.deadline()), "declaration continuation deadline expired; no query or action is allowed");
        var frame = new ArmyRetreatFrames.Current(actual, source.deadline());
        var current = declarations(wars, catalog, actual, source.deadline());
        PlanningReadResult.Known<ArmyWarReadCodec.Observation> known;
        var pending = wars.pendingDeclaration();
        if (pending.isPresent()) {
            var original = pending.orElseThrow();
            var collected = wars.collectOriginal(same, new ArmyCalls.Collect(revision(actual), original.originalUnknown().requestId()), actual, source.deadline());
            if (!(collected instanceof ArmyDeclarationCollection.Available))
                throw new IllegalStateException("actual original declaration quote is " + collected.status().wire() + "; no new DECL query was submitted");
            known = wars.requireCurrentDeclarations(frame).originalRead();
        } else if (wars.currentDeclarations(frame).isPresent()) {
            // Another actual consumer may already have collected the same original. The private lease retains its real central Known.
            known = wars.requireCurrentDeclarations(frame).originalRead();
        } else {
            var selection = new ArmyWarReads.Selection(new ArmyCalls.Frame(PublicMethod.QUERY_DECLARABLE_WARS, revision(actual)), frame, Optional.empty());
            var result = wars.read(same, current.contract(), selection, Duration.between(clock.instant(), source.deadline()));
            if (!(result instanceof PlanningReadResult.Known<ArmyWarReadCodec.Observation> observed))
                throw new IllegalStateException(((PlanningReadResult.Unavailable<ArmyWarReadCodec.Observation>) result).reason());
            known = observed;
        }
        var original = declarations(wars, catalog, actual, known.receipt().request().deadline());
        requireCurrentDeclaration(original, known.receipt(), current, actual);
        StrictJson.require(original.contract().replay(known.receipt()).equals(known.value()), "retained central declaration Known differs from its sole original decoder");
        return known;
    }
    private static void requireCurrentDeclaration(ArmyOrdinaryPreflight.Query<ArmyWarReadCodec.Observation> original,
            PlanningReadReceipt receipt, ArmyOrdinaryPreflight.Query<ArmyWarReadCodec.Observation> current, Complete actual) {
        var decoded = original.contract().replay(receipt);
        // The current request/semantic come from the actual caller's held frame. Presence of late DATA alone grants no continuation.
        current.contract().requireCanonicalReuse(receipt, decoded, current.request(), actual.semantic());
    }
    /** Historical reconstruction uses the real producer's replay decoder. It never publishes a live declaration lease. */
    public ArmyOrdinaryPreflight.Query<ArmyWarReadCodec.Observation> declarationFinal(ArmyCalls.Declaration selected,
            Complete actual, Instant deadline, PlanningReadReceipt firstOriginal, ActionPorts.OutcomeArchive archive) {
        return declarationFinal(producers.wars(), context.readCatalog(), selected, actual, deadline, firstOriginal, archive);
    }
    /** Shared exact original -> dependent contract builder. It issues neither a Native query nor action authority. */
    public static ArmyOrdinaryPreflight.Query<ArmyWarReadCodec.Observation> declarationFinal(ArmyWarReads wars,
            RootReadContractCatalog catalog, ArmyCalls.Declaration selected, Complete actual, Instant deadline,
            PlanningReadReceipt firstOriginal, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(selected.method() == PublicMethod.DECLARE_WAR, "final declaration quote requires the selected declaration action");
        ArmyOrdinaryPreflight.bind(firstOriginal, actual); NativeRecordedEvidenceVerifier.requireRead(firstOriginal, archive);
        ExactRef ref = archive.readReferenceOf(firstOriginal);
        StrictJson.require(archive.loadRead(ref).equals(firstOriginal), "declaration lease changed its original quote custody");
        requireCurrentDeclaration(declarations(wars, catalog, actual, firstOriginal.request().deadline()), firstOriginal,
                declarations(wars, catalog, actual, deadline), actual);
        var frame = new ArmyRetreatFrames.Current(actual, deadline);
        var firstSelection = new ArmyWarReads.Selection(new ArmyCalls.Frame(PublicMethod.QUERY_DECLARABLE_WARS, revision(actual)), frame, Optional.empty());
        var lease = ArmyWarReads.replayDeclarationLease(firstSelection, firstOriginal, ref, archive);
        return declarationFinal(wars, catalog, selected, frame, lease);
    }
    private ArmyOrdinaryPreflight.Query<ArmyWarReadCodec.Observation> declarationFinal(ArmyCalls.Declaration selected,
            ArmyRetreatFrames.Current frame, ArmyWarReads.DeclarationLease lease) {
        return declarationFinal(producers.wars(), context.readCatalog(), selected, frame, lease);
    }
    private static ArmyOrdinaryPreflight.Query<ArmyWarReadCodec.Observation> declarationFinal(ArmyWarReads wars,
            RootReadContractCatalog catalog, ArmyCalls.Declaration selected, ArmyRetreatFrames.Current frame, ArmyWarReads.DeclarationLease lease) {
        lease.selected(frame, selected.declarationId());
        var call = new ArmyCalls.Declaration(PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2, revision(frame.actual()), selected.declarationId());
        return war(wars, catalog, Role.DECLARATION_FINAL_ROLES, new ArmyWarReads.Selection(call, frame, Optional.of(lease)));
    }
    public static ArmyCalls.Revision revision(Complete actual) { return new ArmyCalls.Revision(new ArmyTypes.Present<>(actual.identity().frame().revision())); }
    private static boolean needsTerms(Complete actual, ArmyOrdinaryPreflight.Read original, ActionPorts.OutcomeArchive archive, BigInteger id) {
        return OrdinaryWhitePeacePolicy.needsClaimTerms(NativeOrdinaryWarAdmission.policyView(actual, List.of(original), archive), id.intValueExact());
    }
    private static PlanningReadReceipt original(ExactRef ref, Complete frame, ActionPorts.OutcomeArchive archive) {
        var read = archive.loadRead(ref); NativeRecordedEvidenceVerifier.requireRead(read, archive);
        StrictJson.require(archive.readReferenceOf(read).equals(ref), "Army original quote custody changed"); ArmyOrdinaryPreflight.bind(read, frame); return read;
    }
    private void sameFrame(ArmyRetreatFrames.Current original) {
        try { ArmyRetreatFrames.same(original, producers.frames().current(original.deadline())); }
        catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IllegalStateException("dependent Army quote frame changed", interrupted); }
    }
    private static void requireCurrent(Complete actual, ArmyTypes.Context source) {
        StrictJson.require(actual.identity().equals(source.before()) && actual.source().equals(source.source()) && actual.sessionId().equals(source.sessionId()), "Army quote crossed its original full source frame");
    }
    public static RawJson raw(Obj value) { return new RawJson(DriverJson.encode(value)); }
    public static RawJson raw(JsonNode value) { return new RawJson(value.toString().getBytes(StandardCharsets.UTF_8)); }
}
