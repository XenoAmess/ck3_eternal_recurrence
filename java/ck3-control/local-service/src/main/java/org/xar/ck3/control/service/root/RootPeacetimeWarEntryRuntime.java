package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.finance.FinanceRuntimeServices;
import org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision;
import org.xar.ck3.control.application.planning.warentry.PeacetimeWarEntryPlanner;
import org.xar.ck3.control.application.planning.warentry.WarEntryForceAdmission;
import org.xar.ck3.control.application.planning.warexit.WarExitReads;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;

/** The original peaceful selector connected to the actual retained Root readers and strong command producer. */
public final class RootPeacetimeWarEntryRuntime implements OrdinaryCorePolicy.CoreProducer {
    public record Sources(ExactRef runtime, ExactRef planner, ExactRef collector, ExactRef candidates,
            ExactRef forceAdmission, ExactRef battlePrior, ExactRef historyAdvance, ExactRef json,
            ExactRef declarationCollection, ExactRef declarationCollectionCodec) {
        public Sources {
            for (ExactRef source : List.of(runtime, planner, collector, candidates, forceAdmission,
                    battlePrior, historyAdvance, json, declarationCollection, declarationCollectionCodec))
                StrictJson.require(source.bytes() > 0, "actual selected peaceful war-entry source required");
        }
    }
    /** Source selection only. This token cannot issue a read, command, current frame or Game qualification. */
    public static final class Prepared {
        private final Sources sources;
        private Prepared(Sources sources) { this.sources = Objects.requireNonNull(sources); }
        public Sources sources() { return sources; }
    }
    public static Prepared prepare(Sources sources) {
        return new Prepared(Objects.requireNonNull(sources));
    }
    public static Prepared prepare(RootRuntimeDefinitions.Inputs actual) throws IOException {
        Objects.requireNonNull(actual);
        return new Prepared(new Sources(
                selected(actual, "local-service", "service/root/RootPeacetimeWarEntryRuntime"),
                selected(actual, "application", "application/planning/warentry/PeacetimeWarEntryPlanner"),
                selected(actual, "application", "application/planning/warentry/WarEntryCollector"),
                selected(actual, "application", "application/planning/warentry/WarEntryCandidates"),
                selected(actual, "application", "application/planning/warentry/WarEntryForceAdmission"),
                selected(actual, "application", "application/planning/warentry/PrewarBattlePrior"),
                selected(actual, "application", "application/planning/warentry/WarEntryHistoryAdvance"),
                selected(actual, "application", "application/planning/warentry/WarEntryJson"),
                selected(actual, "native-transport", "nativebridge/capabilities/army/ArmyDeclarationCollection"),
                selected(actual, "native-transport", "nativebridge/capabilities/army/ArmyDeclarationCollectionCodec")));
    }
    private static ExactRef selected(RootRuntimeDefinitions.Inputs actual, String module, String path) throws IOException {
        String target = module + "/src/main/java/org/xar/ck3/control/" + path + ".java";
        var matches = actual.sourceIndex().stream().filter(row -> row.targetRelative().equals(target)).toList();
        if (matches.size() != 1) throw new IOException("actual unique peaceful war-entry source missing: " + target);
        ExactRef source = matches.getFirst().sourceRef();
        RootRuntimeDefinitions.read(RootApplicationConfiguration.file(source), 64 << 20);
        return source;
    }
    public static RootPeacetimeWarEntryRuntime install(Prepared prepared, RootRuntimeContext context,
            RootRuntimeCommands commands, OrdinaryMilitaryInstaller military,
            ArmyOrdinaryRuntimeBindings.Installed army, RootWarCoreFactory war) throws IOException {
        Objects.requireNonNull(army); Objects.requireNonNull(commands).requireArmy(army.service());
        for (Class<?> body : List.of(RootPeacetimeWarEntryRuntime.class, PeacetimeWarEntryPlanner.class,
                org.xar.ck3.control.application.planning.warentry.WarEntryCollector.class,
                org.xar.ck3.control.application.planning.warentry.WarEntryCandidates.class,
                WarEntryForceAdmission.class, org.xar.ck3.control.application.planning.warentry.PrewarBattlePrior.class,
                ArmyDeclarationCollection.class, ArmyDeclarationCollectionCodec.class))
            context.game().launchPlan().sources().requireLoadedClass(body);
        return new RootPeacetimeWarEntryRuntime(prepared, context, commands, military, war);
    }

    private final Prepared prepared;
    private final RootRuntimeContext context;
    private final RootRuntimeCommands commands;
    private final OrdinaryMilitaryInstaller military;
    private final RootWarCoreFactory war;
    private final WarExitReads exits;
    private RootPeacetimeWarEntryRuntime(Prepared prepared, RootRuntimeContext context,
            RootRuntimeCommands commands, OrdinaryMilitaryInstaller military, RootWarCoreFactory war) {
        this.prepared = Objects.requireNonNull(prepared); this.context = Objects.requireNonNull(context);
        this.commands = Objects.requireNonNull(commands); this.military = Objects.requireNonNull(military);
        this.war = Objects.requireNonNull(war);
        exits = new WarExitReads(this::readExit);
    }
    public Sources sources() { return prepared.sources(); }
    /** No duplicate M0 collector is installed: its formal policy keeps its own two-query/three-capture state machine. */
    public WarExitReads actualExitReads() { return exits; }
    public WarExitReads.DeclarationLeaseSource declarationLeaseSource() { return this::declarationLease; }

    @Override public OrdinaryPolicy.Decision evaluate(PlanningRequest request, OrdinaryPolicy.Draft previous) {
        Objects.requireNonNull(request); Objects.requireNonNull(previous);
        try {
            return context.withSession(same -> {
                InspectedCurrent inspected = inspectCurrent(same, request, true);
                if (inspected.collection().isPresent())
                    return collectionDecision(inspected.collection().orElseThrow());
                ArmyRetreatFrames.Current current = inspected.current();
                Set<String> steps = request.observations().actionSteps().stream()
                        .map(OperationKey::value).collect(java.util.stream.Collectors.toUnmodifiableSet());
                final Optional<Obj> choice;
                try { choice = PeacetimeWarEntryPlanner.select(request.observations().snapshot(),
                        request.observations().history(), steps); }
                catch (IllegalArgumentException | NullPointerException invalid) {
                    return new OrdinaryPolicy.Stop(PlanningResult.StopReason.INVALID_FRAME,
                            "peacetime war-entry producer input rejected: " + invalid.getMessage());
                }
                if (choice.isEmpty()) return new OrdinaryPolicy.NotApplicable(
                        "the original peacetime war-entry branch has no declaration or discovery opportunity");
                Obj plan = choice.orElseThrow(); Optional<OperationKey> operation = selectedOperation(plan);
                if (operation.isPresent() && operation.orElseThrow().value().startsWith("query-"))
                    return readSelected(same, request, current, operation.orElseThrow(), plan);
                if (operation.isPresent() && operation.orElseThrow().value().startsWith("declare-war-"))
                    requireDeclaration(same, request, current, plan, operation.orElseThrow());
                return finishSelected(request, plan, this::command);
            });
        } catch (IOException | UncheckedIOException | IllegalArgumentException | IllegalStateException unavailable) {
            return missing("actual current peacetime war-entry producer unavailable: "
                    + Objects.toString(unavailable.getMessage(), unavailable.getClass().getSimpleName()));
        }
    }

    private record InspectedCurrent(ArmyRetreatFrames.Current current,
            Optional<ArmyDeclarationCollection.Result> collection) {
        private InspectedCurrent { Objects.requireNonNull(current); Objects.requireNonNull(collection); }
    }
    /** Ordinary reads retain their previous path; collecting an original result must borrow the held lease. */
    private ArmyRetreatFrames.Current current(Session same, PlanningRequest request) throws IOException {
        return inspectCurrent(same, request, false).current();
    }
    private InspectedCurrent inspectCurrent(Session same, PlanningRequest request, boolean collectPending) throws IOException {
        context.writer().requireSession(same); context.requireCurrent(request.deadline());
        StrictJson.require(request.source().equals(context.source())
                && request.before().machineId().equals(context.game().machineId())
                && request.before().game().equals(context.game().generation())
                && request.sessionId().equals(context.game().sessionId()),
                "peacetime war-entry belongs to another physical Game/source/session");
        return context.collector().currentPlanning(same, request, request.deadline(), (original, lease) -> {
            var actual = lease.frame();
            StrictJson.require(original == request && actual.identity().equals(request.before())
                    && actual.source().equals(request.source()) && actual.sessionId().equals(request.sessionId())
                    && actual.semantic().equals(request.observations().snapshot()),
                    "peacetime planning differs from its actual complete current producer");
            var current = new ArmyRetreatFrames.Current(actual, request.deadline());
            Optional<ArmyDeclarationCollection.Result> collection = Optional.empty();
            if (collectPending) {
                var pending = military.warReads().pendingDeclaration(context.reads());
                if (pending.isPresent()) {
                    var input = new ArmyCalls.Collect(new ArmyCalls.Revision(
                            new ArmyTypes.Present<>(actual.identity().frame().revision())),
                            pending.orElseThrow().originalUnknown().requestId());
                    // The same Army owner polls its opaque original ticket and alone publishes any available result.
                    collection = Optional.of(military.warReads().collectOriginal(same, input, actual, request.deadline()));
                }
            }
            return new InspectedCurrent(current, collection);
        });
    }
    /** Data-only policy consumption. A decoded result cannot grant a read, command, receipt or current lease. */
    static OrdinaryPolicy.Decision collectionDecision(ArmyDeclarationCollection.Result result) {
        Objects.requireNonNull(result);
        String original = result.scope().requestId();
        return switch (result.status()) {
            case AVAILABLE -> new OrdinaryPolicy.Refresh("original declaration result available for " + original
                    + "; the sole Army publisher restored its original read; recapture before planning");
            case PENDING -> new OrdinaryPolicy.Wait("original declaration result pending for " + original
                    + "; wait for passive delivery without resubmitting the original query");
            case STALE -> new OrdinaryPolicy.Stop(PlanningResult.StopReason.INVALID_FRAME, "original declaration result stale for " + original
                    + "; actual current binding changed; no declaration cache or command was restored");
            case NATIVE_REJECTED -> new OrdinaryPolicy.Stop(PlanningResult.StopReason.POLICY_BLOCKED, "original declaration result native-rejected for " + original
                    + "; the original native response rejected the query; no command was prepared");
        };
    }
    private OrdinaryPolicy.Decision readSelected(Session same, PlanningRequest request,
            ArmyRetreatFrames.Current current, OperationKey operation, Obj plan) throws IOException {
        if (operation.value().equals("query-declarable-wars")) {
            var call = new ArmyCalls.Frame(PublicMethod.QUERY_DECLARABLE_WARS, revision(request));
            var selection = military.warReads().selection(same, context.readCatalog(), call, current);
            var contract = military.warReads().contract(context.readCatalog(), selection);
            var query = query(selection, contract);
            // The shared Army owner retains UNKNOWN declaration custody for both public and Root callers.
            java.time.Duration requestedTimeout = java.time.Duration.between(context.clock().instant(), request.deadline());
            var result = military.warReads().read(same, contract, selection, requestedTimeout);
            if (result instanceof PlanningReadResult.Unavailable<ArmyWarReadCodec.Observation> unavailable) {
                var pending = military.warReads().pendingDeclaration(context.reads());
                if (pending.isPresent()) {
                    var original = pending.orElseThrow();
                    StrictJson.require(original.request().equals(query)
                            && unavailable.original().orElse(null) == original.originalUnknown(),
                            "initial declaration UNKNOWN differs from its sole original custody");
                    return new OrdinaryPolicy.Wait("original declaration query pending for " + original.originalUnknown().requestId()
                            + "; retain its original request and collect passive delivery on the next actual planning scope");
                }
                return missing("actual declaration query unavailable; original request is not retried: " + unavailable.reason());
            }
            var known = (PlanningReadResult.Known<ArmyWarReadCodec.Observation>) result;
            StrictJson.require(known.receipt().request().equals(query)
                    && contract.replay(known.receipt()).equals(known.value())
                    && known.value() instanceof ArmyWarReadCodec.Declarations,
                    "declaration read differs from its sole full original producer/decoder");
            return new OrdinaryPolicy.Refresh("actual native declarations published; recapture the original current frame before planning");
        }
        if (operation.value().equals("query-campaign-root-context-v1")
                || operation.value().equals("query-player-faction-alerts-v1")) {
            FinanceRuntimeServices finance = context.finance();
            StrictJson.require(finance.game().equals(context.game().generation())
                    && finance.sessionId().equals(request.sessionId()) && finance.source().equals(request.source()),
                    "peacetime scope read crossed the identical installed finance/M1 producer");
            FinanceReadContracts.Query kind = operation.value().equals("query-campaign-root-context-v1")
                    ? FinanceReadContracts.Query.ROOT : FinanceReadContracts.Query.FACTION_ALERTS;
            PlanningReadPort actualReads = kind == FinanceReadContracts.Query.ROOT ? finance.readPort() : context.reads();
            var result = finance.definitions().read(same, kind, actualReads, request);
            if (result instanceof PlanningReadResult.Unavailable<FinanceReadContracts.Packet> unavailable)
                return missing("actual peaceful scope read unavailable: " + unavailable.reason());
            var known = (PlanningReadResult.Known<FinanceReadContracts.Packet>) result;
            FinanceReadContracts.Packet replay = finance.definitions().decodeOriginal(kind,
                    known.receipt(), request.observations().snapshot());
            StrictJson.require(known.value().receipt().equals(known.receipt())
                    && replay.result().equals(known.value().result())
                    && replay.originalResult().equals(known.value().originalResult()),
                    "peaceful scope result differs from its actual original typed owner");
            return new OrdinaryPolicy.Refresh("actual " + operation.value() + " published; recapture its same-frame planning observation");
        }
        var selected = readSelection(plan);
        StrictJson.require(selected.operation().equals(operation), "military read changed the original selected operation");
        var result = military.readDispatcher().read(request, selected);
        if (result instanceof PlanningReadResult.Unavailable<Obj> unavailable)
            return missing("actual peaceful military read unavailable: " + unavailable.reason());
        var known = (PlanningReadResult.Known<Obj>) result;
        StrictJson.require(known.receipt().request().operation().equals(operation),
                "peaceful military reader changed the selected exact operation");
        return new OrdinaryPolicy.Refresh("actual " + operation.value() + " published; recapture before evaluating its original consumers");
    }
    static MilitaryPlanningDecision.Select readSelection(Obj plan) {
        OperationKey operation = selectedOperation(plan).orElseThrow(
                () -> new IllegalArgumentException("an actual selected read operation is required"));
        StrictJson.require(operation.value().startsWith("query-"), "only the original selected read may enter this adapter");
        return new MilitaryPlanningDecision.Select(text(plan, "policy"), text(plan, "phase"),
                text(plan, "reason"), operation, empty(), OrdinaryPolicy.Purpose.READ_ONLY, plan);
    }

    private PeacetimeWarEntryPlanner.CommandProposal command(PlanningRequest request, String step, Obj plan) {
        try {
            var operation = new OperationKey(step);
            var selected = new MilitaryPlanningDecision.Select(text(plan, "policy"), text(plan, "phase"),
                    text(plan, "reason"), operation, empty(), purpose(operation), plan);
            var prepared = commands.prepare(request, selected);
            ActionCommand actual = prepared.requireOriginalChoice(request, operation, empty(), plan);
            OriginalCommandClocks.requireCurrentProposal(request, actual);
            return new PeacetimeWarEntryPlanner.Ready(actual);
        } catch (IllegalArgumentException | IllegalStateException | UncheckedIOException unavailable) {
            return new PeacetimeWarEntryPlanner.Unavailable("actual shared Army/Life strong preparation: "
                    + Objects.toString(unavailable.getMessage(), unavailable.getClass().getSimpleName()));
        }
    }
    /** Single final protocol adapter; policy selection and scoring remain with PeacetimeWarEntryPlanner. */
    static OrdinaryPolicy.Decision finishSelected(PlanningRequest request, Obj plan,
            PeacetimeWarEntryPlanner.CommandFactory commands) {
        Optional<OperationKey> operation = selectedOperation(plan);
        StrictJson.require(operation.isEmpty() || !operation.orElseThrow().value().startsWith("query-"),
                "an actual read must refresh through its real producer, never become an ActionCommand");
        Optional<ActionCommand> command = Optional.empty();
        if (operation.isPresent()) {
            var proposed = Objects.requireNonNull(commands.propose(request, operation.orElseThrow().value(), plan));
            if (proposed instanceof PeacetimeWarEntryPlanner.Unavailable unavailable) return missing(unavailable.missingProducer());
            ActionCommand actual = ((PeacetimeWarEntryPlanner.Ready) proposed).command();
            OriginalCommandClocks.requireCurrentProposal(request, actual);
            StrictJson.require(actual.operation().equals(operation.orElseThrow()), "peacetime strong producer changed the original operation");
            command = Optional.of(actual);
        }
        return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft(text(plan, "policy"), text(plan, "phase"),
                text(plan, "reason"), OrdinaryPolicy.Kind.ORDINARY, command,
                operation.map(RootPeacetimeWarEntryRuntime::purpose).orElse(OrdinaryPolicy.Purpose.READ_ONLY),
                Optional.empty(), plan), text(plan, "reason"));
    }

    private WarExitReads.DeclarationLeaseResult declarationLease(PlanningRequest request) {
        try { return context.withSession(same -> new WarExitReads.AvailableDeclarationLease(
                canonicalDeclaration(same, request, current(same, request)))); }
        catch (IOException | UncheckedIOException | IllegalArgumentException | IllegalStateException unavailable) {
            return new WarExitReads.UnavailableDeclarationLease("actual source-bound canonical declaration unavailable: " + unavailable.getMessage());
        }
    }
    private WarExitReads.DeclarationLease canonicalDeclaration(Session same, PlanningRequest request,
            ArmyRetreatFrames.Current current) throws IOException {
        var call = new ArmyCalls.Frame(PublicMethod.QUERY_DECLARABLE_WARS, revision(request));
        var selection = new ArmyWarReads.Selection(call, current, Optional.empty());
        var contract = military.warReads().contract(context.readCatalog(), selection);
        var query = query(selection, contract);
        var witness = context.readHistoryPublisher().canonicalReadWitness(same, contract, query)
                .orElseThrow(() -> new IOException("actual current declaration publication missing; no prerequisite query was sent"));
        var original = witness.requireCurrent(same, contract, query);
        StrictJson.require(witness.originalContract().replay(original.receipt()).equals(original.value())
                && original.value() instanceof ArmyWarReadCodec.Declarations,
                "canonical declarations differ from the identical installed original decoder");
        var army = military.warReads().canonicalDeclarations(same, context.readCatalog(), current)
                .orElseThrow(() -> new IOException("identical Army current declaration lease unavailable"));
        StrictJson.require(army.evidence().equals(original.originalReceipt()),
                "Root declaration adapter replaced the Army owner's original ExactRef");
        var archived = context.archive().withSession(same);
        StrictJson.require(archived.loadRead(army.evidence()).equals(original.receipt())
                && archived.readReferenceOf(original.receipt()).equals(army.evidence()),
                "Root declaration lease is not its actual immutable original");
        return WarExitReads.DeclarationLease.fromCurrentCanonicalRead(same, witness, contract, query, request);
    }
    private void requireDeclaration(Session same, PlanningRequest request, ArmyRetreatFrames.Current current,
            Obj plan, OperationKey operation) throws IOException {
        var lease = canonicalDeclaration(same, request, current);
        StrictJson.require(lease.matches(request), "selected declaration lost its actual current read proof");
        String id = operation.value().substring("declare-war-".length());
        requireSelectedDeclaration(plan, lease.selected(id), operation);
    }
    /** Complete original identity, including claimant/title list and absent -1 sentinels; no ordinal or invented sequence. */
    static void requireSelectedDeclaration(Obj plan, DeclarationContract.Choice actual, OperationKey operation) {
        StrictJson.require(operation.value().equals(actual.step().wire()), "selected declaration step differs from actual native tuple");
        Obj original = DriverJson.object(StrictJson.canonical(DeclarationContract.encodeChoice(actual)), DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(plan.get("selected_declaration") instanceof Obj selected
                && selected.equals(WarEntryForceAdmission.selectedDeclaration(original)),
                "peaceful declaration plan changed the complete same-frame original declaration");
    }

    private PlanningReadResult<WarExitReads.Query> readExit(PlanningRequest request, WarExitReads.Key key, Obj arguments) {
        if (key.kind() != WarExitReads.Kind.PREWAR_COALITION) return war.actualExitReads().read(request, key, arguments);
        try {
            return context.withSession(same -> {
                var current = current(same, request); var lease = canonicalDeclaration(same, request, current);
                StrictJson.require(lease.matches(request), "formal prewar read lost its current original declaration");
                var fields = StrictJson.object(OpportunityJson.toNode(arguments),
                        Set.of("declaration_id", "selected_declaration", "declaration_query_sequence"));
                String id = StrictJson.text(fields.get("declaration_id")); var choice = lease.selected(id);
                StrictJson.require(StrictJson.integer(fields.get("declaration_query_sequence"), java.math.BigInteger.ONE,
                        StrictJson.UINT64_MAX).equals(lease.querySequence()), "formal prewar query invented or changed the real declaration sequence");
                Obj selected = WarEntryForceAdmission.selectedDeclaration(DriverJson.object(
                        StrictJson.canonical(DeclarationContract.encodeChoice(choice)), DriverJson.MAX_NATIVE_BYTES));
                var expected = (ObjectNode) OpportunityJson.toNode(selected); expected.remove("declaration_id");
                StrictJson.require(fields.get("selected_declaration").equals(expected), "formal prewar query changed the original declaration identity");
                var call = new ArmyCalls.Declaration(PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2, revision(request), id);
                var selection = military.warReads().selection(same, context.readCatalog(), call, current);
                var contract = military.warReads().contract(context.readCatalog(), selection);
                var result = military.warReads().read(same, contract, selection);
                if (result instanceof PlanningReadResult.Unavailable<ArmyWarReadCodec.Observation> unavailable)
                    return new PlanningReadResult.Unavailable<WarExitReads.Query>(unavailable.reason(), unavailable.original());
                var known = (PlanningReadResult.Known<ArmyWarReadCodec.Observation>) result;
                StrictJson.require(contract.replay(known.receipt()).equals(known.value()), "formal prewar result differs from its actual original decoder");
                var node = OpportunityJson.toNode(known.value().normalizedResult());
                StrictJson.require(node instanceof ObjectNode, "formal prewar producer must retain its complete typed envelope");
                return new PlanningReadResult.Known<>(new WarExitReads.Query(key, (ObjectNode) node, known.receipt()),
                        known.receipt(), known.originalReceipt());
            });
        } catch (IOException | UncheckedIOException | IllegalArgumentException | IllegalStateException unavailable) {
            return new PlanningReadResult.Unavailable<>("actual source-bound formal prewar producer unavailable: " + unavailable.getMessage(), Optional.empty());
        }
    }
    private static PlanningReadRequest query(ArmyWarReads.Selection selection, ReadContract<ArmyWarReadCodec.Observation> contract) {
        var current = selection.context();
        return new PlanningReadRequest(current.before(), current.source(), current.sessionId(), contract.operation(),
                ArmyWarReads.arguments(selection.input()), current.deadline());
    }
    private static ArmyCalls.Revision revision(PlanningRequest request) {
        return new ArmyCalls.Revision(new ArmyTypes.Present<>(request.before().frame().revision()));
    }
    private static Optional<OperationKey> selectedOperation(Obj plan) {
        Value step = plan.get("selected_step");
        StrictJson.require(step == Nil.INSTANCE || step instanceof Text, "original selected_step must be explicit string/null");
        return step == Nil.INSTANCE ? Optional.empty() : Optional.of(new OperationKey(((Text) step).value()));
    }
    private static OrdinaryPolicy.Purpose purpose(OperationKey operation) {
        return LifeAdvanceComposite.accepts(operation.value()) ? OrdinaryPolicy.Purpose.DATE_ADVANCE : OrdinaryPolicy.Purpose.WORLD_ACTION;
    }
    private static OrdinaryPolicy.Stop missing(String reason) {
        return new OrdinaryPolicy.Stop(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN, reason);
    }
    private static String text(Obj plan, String field) {
        return OpportunityJson.text(plan.get(field), "original peacetime " + field);
    }
    private static Obj empty() { return new Obj(java.util.Map.of()); }
}
