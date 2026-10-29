package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.ArmyWarWindowReads;
import org.xar.ck3.control.application.effects.ArmyWarWindowReads.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContextRead;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Per-request adapters to the same installed producers used by sequential ordinary preflight.
 * Reconstructing original scope never creates Known, publishes a lease or reads Native.
 */
public final class ArmyWarWindowRuntimeRoutes {
    private final RootRuntimeContext context;
    private final ArmyOrdinaryPairedQuotes quotes;
    private final ArmyOrdinaryPairedQuotes.Producers producers;
    public ArmyWarWindowRuntimeRoutes(RootRuntimeContext actualContext, ArmyOrdinaryPairedQuotes actualQuotes) {
        context = Objects.requireNonNull(actualContext); quotes = Objects.requireNonNull(actualQuotes); producers = quotes.producers();
    }
    public Queries queries(Selection selected) {
        Objects.requireNonNull(selected);
        return switch (selected) {
            case Declaration ignored -> Queries.forDeclaration(declarations(), finalRoles());
            case CallAlly ignored -> Queries.forCallAlly(family());
            case HolyHire ignored -> Queries.forHolyHire(holy());
            case Window window -> Queries.forWindow(window.window(), window(window.window()));
        };
    }
    private Query<ArmyWarReadCodec.Observation> declarations() {
        return new Query<>(new OperationKey("query-declarable-wars"),
                request -> declarationPlan(request, false).contract(),
                ArmyWarReadCodec::encode, request -> declarationPlan(request, false).request().arguments());
    }
    private Query<ArmyWarReadCodec.Observation> finalRoles() {
        return new Query<>(new OperationKey("query-prewar-force-coalition-coverage-v2"),
                request -> declarationPlan(request, true).contract(),
                ArmyWarReadCodec::encode, request -> declarationPlan(request, true).request().arguments());
    }
    private ArmyOrdinaryPreflight.Query<ArmyWarReadCodec.Observation> declarationPlan(Request request, boolean finalRoles) {
        gameplay(request);
        StrictJson.require(request.selection() instanceof Declaration, "declaration supplier received another action");
        var selected = (Declaration) request.selection();
        if (!finalRoles) return quotes.declarations(request.frame(), request.deadline());
        // This is a historical receipt reconstruction. The actual live second read is sequenced by PairedQuotes.
        List<PlanningReadReceipt> originals = request.preflightOriginals();
        StrictJson.require(originals.size() == 2, "final CB replay requires the complete original two-phase quote inventory");
        var call = new ArmyCalls.Declaration(PublicMethod.DECLARE_WAR,
                revision(request), selected.declarationId());
        return quotes.declarationFinal(call, request.frame(), request.deadline(), originals.getFirst(), context.archive());
    }
    private Query<Obj> family() {
        return new Query<>(new OperationKey("read-family-obligations-private-12002"), request -> {
            return familyPlan(request).contract();
        }, ArmyOrdinaryPairedQuotes::raw, request -> familyPlan(request).request().arguments());
    }
    private ArmyOrdinaryPreflight.Query<Obj> familyPlan(Request request) {
        gameplay(request);
        StrictJson.require(request.selection() instanceof CallAlly, "family supplier received another selected action");
        var selected = (CallAlly) request.selection();
        var call = new ArmyCalls.CallAlly(revision(request), new ArmyTypes.FullId(selected.warId()), new ArmyTypes.FullId(selected.recipientId()));
        return quotes.family(call, source(request));
    }
    private Query<PlayerHolyOrderContextRead.Observation> holy() {
        return new Query<>(PlayerHolyOrderContextRead.OPERATION, request -> {
            StrictJson.require(request.selection() instanceof HolyHire, "holy-order supplier received another action");
            return request.reconciliation().isPresent()?producers.holyOrders().reconciliationContract():holyPlan(request).contract();
        },
                value -> ArmyOrdinaryPairedQuotes.raw(PlayerHolyOrderContextRead.flattened(value)),
                request -> new Obj(java.util.Map.of()));
    }
    private ArmyOrdinaryPreflight.Query<PlayerHolyOrderContextRead.Observation> holyPlan(Request request) {
        gameplay(request); StrictJson.require(request.selection() instanceof HolyHire, "holy-order supplier received another action");
        return quotes.holy(source(request));
    }
    /** The ordinary and pending families are distinct producer-owned descriptors, resolved against the actual afterframe. */
    public Query<ArmyWindowCodec.Observation> window(WindowKind kind) {
        Objects.requireNonNull(kind);
        OperationKey operation = new OperationKey(kind == WindowKind.OVERVIEW
                ? "query-war-declared-overview-v1" : "query-war-results-window-v1");
        return new Query<>(operation, request -> {
            ArmyCalls.Frame call = windowCall(request, kind);
            if (request.reconciliation().isPresent()) {
                var selected = new ArmyWindowReads.ReconciliationSelection(request.reconciliation().orElseThrow(), call, request.deadline(),
                        ArmyWindowReads.driverGeneration(request.frame()));
                return producers.windows().issueReconciliation(context.readCatalog(), selected);
            }
            var source = new ArmyTypes.Context(request.frame().identity(), request.frame().source(), request.frame().sessionId(), request.deadline());
            return producers.windows().issue(context.readCatalog(), new ArmyWindowReads.Selection(call, source,
                    request.frame().connectionGeneration(), ArmyWindowReads.driverGeneration(request.frame())));
        }, value -> ArmyOrdinaryPairedQuotes.raw(value.normalized()),
                request -> ArmyWindowReads.arguments(windowCall(request, kind)));
    }
    private static ArmyCalls.Frame windowCall(Request request, WindowKind kind) {
        StrictJson.require(request.selection() instanceof Window window && window.window() == kind,
                "window supplier crossed overview/results selected action");
        PublicMethod method = kind == WindowKind.OVERVIEW ? PublicMethod.QUERY_WAR_DECLARED_OVERVIEW_V1
                : PublicMethod.QUERY_WAR_RESULTS_WINDOW_V1;
        return new ArmyCalls.Frame(method, revision(request));
    }
    private static ArmyCalls.Revision revision(Request request) {
        BigInteger original = request.frame().identity().frame().revision();
        return new ArmyCalls.Revision(new ArmyTypes.Present<>(original));
    }
    private static ArmyTypes.Context source(Request request) {
        return new ArmyTypes.Context(request.frame().identity(), request.frame().source(), request.frame().sessionId(), request.deadline());
    }
    private static void gameplay(Request request) {
        StrictJson.require(request.reconciliation().isEmpty(), "this producer has no installed reconciliation family");
    }
}
