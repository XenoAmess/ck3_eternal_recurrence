package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.Opportunity;

/** Finite application-routing DATA only; no Session token, source ref or head is actual writer/archive authority. */
final class ConstructionPlanningStageRouting290Test {
    private static final ExactRef REF = new ExactRef("D:/fixture/planning-construction290/source.java", 1, "a".repeat(64));
    private static final G2Source SOURCE = new G2Source("xenoamess-full-tower-eb9d2c1186", "2026-11-02T00:00:00Z", "1.20.0.4", REF);
    private static final String GAP = "finite construction DATA read has no transport, original custody or write permission";

    @Test void explicitBeforeViewIsLazyAndKeepsTheOriginalCollectorAndLiveSession() {
        var input = request(true);
        var definitions = definitions();
        var reads = new CountingReads();
        var state = new DataState();
        var callbacks = new EndingAndFunding();
        Session a = sessionToken(), b = sessionToken();
        var current = new AtomicReference<Session>();
        var supplies = new AtomicInteger();
        var finance = new OrdinaryFinanceCollector(definitions, reads, state.port, () -> {
            supplies.incrementAndGet();
            Session actual = current.get();
            if (actual == null) throw new AssertionError("construction view captured a Session before the read");
            return actual;
        });
        var original = new OrdinaryConstructionCollector(finance, callbacks, callbacks);
        var view = original.planningView();
        assertEquals(0, supplies.get());
        assertEquals(1, reads.views);
        assertTrue(reads.calls.isEmpty());
        assertEquals(0, state.calls);
        callbacks.assertNotCalled();
        var selection = OrdinaryConstructionPolicy.selection(eligibleDraft());
        assertEquals(Opportunity.ORDINARY_ADVANCE, selection.opportunity());

        current.set(a);
        beforeMissing(original.before(a, input, selection, empty(), "new_building"));
        beforeMissing(view.before(input, selection, empty(), "new_building"));
        current.set(b);
        beforeMissing(view.before(input, selection, empty(), "new_building"));
        beforeMissing(original.before(b, input, selection, empty(), "new_building"));
        assertEquals(4, reads.calls.size());
        assertRead(reads.calls.get(0), "D", a, definitions, FinanceReadContracts.Query.ROOT, input);
        assertRead(reads.calls.get(1), "P", a, definitions, FinanceReadContracts.Query.ROOT, input);
        assertRead(reads.calls.get(2), "P", b, definitions, FinanceReadContracts.Query.ROOT, input);
        assertRead(reads.calls.get(3), "D", b, definitions, FinanceReadContracts.Query.ROOT, input);
        assertEquals(4, state.calls);
        assertSame(a, state.sessions.get(0));
        assertSame(a, state.sessions.get(1));
        assertSame(b, state.sessions.get(2));
        assertSame(b, state.sessions.get(3));
        var rejected = assertInstanceOf(OrdinaryConstructionCollector.Missing.class,
                view.before(a, input, selection, empty(), "new_building"));
        assertTrue(rejected.reason().contains("finance collector cannot replace its borrowed writer"));
        assertEquals(4, reads.calls.size(), "foreign writer must be rejected before a generic READ");
        assertEquals(4, state.calls, "foreign writer must be rejected before the DATA head read");
        assertEquals(1, reads.views);
        callbacks.assertNotCalled();
    }

    @Test void materialAndPeacetimeStayDurableUnlessTheirCollectorIsExplicitlyViewed() {
        var input = request(true);
        var definitions = definitions();
        var reads = new CountingReads();
        var state = new DataState();
        var callbacks = new EndingAndFunding();
        Session same = sessionToken();
        var finance = new OrdinaryFinanceCollector(definitions, reads, state.port);
        var original = new OrdinaryConstructionCollector(finance, callbacks, callbacks);
        var view = original.planningView();
        assertTrue(reads.calls.isEmpty());
        assertEquals(0, state.calls);
        assertEquals("registered current material Native source unavailable",
                assertInstanceOf(OrdinaryConstructionCollector.MaterialMissing.class, original.material(same, input)).reason());
        assertEquals("registered current material Native source unavailable",
                assertInstanceOf(OrdinaryConstructionCollector.MaterialMissing.class, view.material(same, input)).reason());
        assertTrue(assertInstanceOf(OrdinaryConstructionCollector.PeacetimeMissing.class,
                original.peacetime(same, input)).reason().contains(GAP));
        assertTrue(assertInstanceOf(OrdinaryConstructionCollector.PeacetimeMissing.class,
                view.peacetime(same, input)).reason().contains(GAP));
        assertEquals(8, reads.calls.size());
        assertRead(reads.calls.get(0), "D", same, definitions, FinanceReadContracts.Query.ROOT, input);
        assertRead(reads.calls.get(1), "D", same, definitions, FinanceReadContracts.Query.CASH, input);
        assertRead(reads.calls.get(2), "D", same, definitions, FinanceReadContracts.Query.CONSTRUCTION, input);
        assertRead(reads.calls.get(3), "P", same, definitions, FinanceReadContracts.Query.ROOT, input);
        assertRead(reads.calls.get(4), "P", same, definitions, FinanceReadContracts.Query.CASH, input);
        assertRead(reads.calls.get(5), "P", same, definitions, FinanceReadContracts.Query.CONSTRUCTION, input);
        assertRead(reads.calls.get(6), "D", same, definitions, FinanceReadContracts.Query.CONSTRUCTION, input);
        assertRead(reads.calls.get(7), "P", same, definitions, FinanceReadContracts.Query.CONSTRUCTION, input);
        assertEquals(1, reads.views);
        assertEquals(0, state.calls);
        callbacks.assertNotCalled();
    }

    @Test void eligibleConstructionStageActuallyReadsPlanningRootAfterOriginalGuards() {
        var input = request(true);
        var definitions = definitions();
        var reads = new CountingReads();
        var state = new DataState();
        var callbacks = new EndingAndFunding();
        Session same = sessionToken();
        var finance = new OrdinaryFinanceCollector(definitions, reads, state.port, () -> same);
        var collector = new OrdinaryConstructionCollector(finance, callbacks, callbacks);
        var policy = new OrdinaryConstructionPolicy(REF, collector, (actual, arguments) -> {
            throw new AssertionError("Unavailable cannot construct an expected result or action");
        }, (actual, previous, ledger, receipt, reason) -> {
            throw new AssertionError("strict clear construction ledger must not publish material");
        });
        var deferred = assertInstanceOf(OrdinaryPolicy.Defer.class, policy.evaluate(input, eligibleDraft()));
        assertEquals("current campaign root unavailable", deferred.reason());
        assertEquals(new IntegerValue(BigInteger.ZERO), deferred.evidence().get("future_funding_credited_raw"));
        assertEquals(new Bool(true), deferred.evidence().get("continue_ordinary_war"));
        assertEquals(new Bool(false), deferred.evidence().get("business_submission"));
        assertEquals(1, reads.calls.size());
        assertRead(reads.calls.getFirst(), "P", same, definitions, FinanceReadContracts.Query.ROOT, input);
        assertEquals(2, state.calls, "policy ledger read precedes finance's independent spending-head read");
        assertSame(same, state.sessions.get(0));
        assertSame(same, state.sessions.get(1));
        assertEquals(1, reads.views);
        callbacks.assertNotCalled();

        assertInstanceOf(OrdinaryPolicy.NotApplicable.class, policy.evaluate(request(false), eligibleDraft()));
        assertEquals(1, reads.calls.size());
        assertEquals(2, state.calls, "front frame guard must not reach the original DATA reader");
        assertEquals(1, reads.views, "front frame guard must not request a planning facade");
        assertInstanceOf(OrdinaryPolicy.NotApplicable.class, policy.evaluate(input, OrdinaryPolicy.Draft.empty()));
        assertEquals(1, reads.calls.size());
        assertEquals(3, state.calls, "noneligible selection still consumes the original pending barrier first");
        assertEquals(1, reads.views, "noneligible original selection must not start the optional quote read path");
        callbacks.assertNotCalled();
    }

    private static OrdinaryPolicy.Draft eligibleDraft() {
        return new OrdinaryPolicy.Draft("finite-original-planner", "current_life_loop", "ordinary date advancement selected",
                OrdinaryPolicy.Kind.ORDINARY, Optional.empty(), OrdinaryPolicy.Purpose.DATE_ADVANCE, Optional.empty(),
                empty().with("selected_step", new Text("life-advance")));
    }
    private static void beforeMissing(OrdinaryConstructionCollector.Read result) {
        assertEquals("current campaign root unavailable",
                assertInstanceOf(OrdinaryConstructionCollector.Missing.class, result).reason());
    }
    private static FinanceReadContracts definitions() {
        return new FinanceReadContracts(query -> new FinanceReadContracts.Registration(REF, new FinanceReadContracts.Permission(
                Optional.empty(), query.operation().value(), ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                ReadContract.WireProfile.EXECUTE_STEP)));
    }
    private static Session sessionToken() {
        return (Session) Proxy.newProxyInstance(Session.class.getClassLoader(), new Class<?>[]{Session.class},
                (proxy, method, arguments) -> { throw new AssertionError("DATA Session token dereferenced: " + method.getName()); });
    }
    private static Obj empty() { return new Obj(Map.of()); }
    private static PlanningRequest request(boolean paused) {
        var before = new ProposalLifecycle.ObservationIdentity(SOURCE.machineId(),
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE, BigInteger.ONE, BigInteger.valueOf(100)),
                        "native:construction290", BigInteger.ONE, "episode-construction290"), 1);
        Obj snapshot = object(parse(("{\"paused\":" + paused + ",\"map_ready\":true,\"snapshot_id\":\"native:construction290\","
                + "\"revision\":1,\"native_revision\":1,\"date_raw\":100,\"episode_run_id\":\"episode-construction290\","
                + "\"played_character\":{\"character_id\":1,\"alive\":true},\"active_wars\":[],\"player_armies\":[],"
                + "\"active_event\":null,\"pending_character_interaction\":null}")
                .getBytes(StandardCharsets.UTF_8)), "complete finite construction planning DATA");
        return new PlanningRequest(before, SOURCE, "session-construction290", Instant.parse("2099-01-01T00:00:00Z"),
                new PlanningObservation(snapshot, List.of(), Set.of(), Set.of(), Optional.empty(), List.of(),
                        Optional.empty(), Optional.empty(), false));
    }
    private record Call(String mode, Session session, ReadContract<?> contract, PlanningReadRequest request) { }
    private static void assertRead(Call call, String mode, Session same, FinanceReadContracts definitions,
            FinanceReadContracts.Query query, PlanningRequest actual) {
        assertEquals(mode, call.mode());
        assertSame(same, call.session());
        assertSame(definitions.contract(query), call.contract());
        Obj arguments = query == FinanceReadContracts.Query.ROOT
                ? FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY) : empty();
        assertEquals(new PlanningReadRequest(actual.before(), actual.source(), actual.sessionId(), query.operation(), arguments,
                actual.deadline()), call.request());
    }
    /** Owner mechanical recording-port shape reused from 286; every scene and expected route is new 290 source-derived DATA. */
    private static final class CountingReads implements PlanningReadPort {
        private final List<Call> calls = new ArrayList<>();
        private int views;
        private final PlanningReadPort planning = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
                return record("P", null, contract, request);
            }
            @Override public <T> PlanningReadResult<T> read(Session same, ReadContract<T> contract, PlanningReadRequest request) {
                return record("P", same, contract, request);
            }
        };
        @Override public PlanningReadPort planningReads() { views++; return planning; }
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
            return record("D", null, contract, request);
        }
        @Override public <T> PlanningReadResult<T> read(Session same, ReadContract<T> contract, PlanningReadRequest request) {
            return record("D", same, contract, request);
        }
        private <T> PlanningReadResult<T> record(String mode, Session same, ReadContract<T> contract, PlanningReadRequest request) {
            calls.add(new Call(mode, same, contract, request));
            return new PlanningReadResult.Unavailable<>(GAP, Optional.empty());
        }
    }
    private static final class EndingAndFunding implements OrdinaryConstructionCollector.EndingSnapshot,
            OrdinaryConstructionCollector.FinancingPending {
        private int endings;
        private int funding;
        @Override public Obj readCurrent(PlanningRequest request) {
            endings++; throw new AssertionError("Unavailable prefix unexpectedly reached ending snapshot");
        }
        @Override public Obj readCurrent(Session same, PlanningRequest request) {
            endings++; throw new AssertionError("Unavailable prefix unexpectedly reached borrowed ending snapshot");
        }
        @Override public CanonicalFundingPending.Result readUnderOriginalWriterLock(PlanningRequest request) {
            funding++; throw new AssertionError("Unavailable prefix unexpectedly reached funding");
        }
        @Override public CanonicalFundingPending.Result readUnderOriginalWriterLock(Session same, PlanningRequest request) {
            funding++; throw new AssertionError("Unavailable prefix unexpectedly reached borrowed funding");
        }
        private void assertNotCalled() { assertEquals(0, endings); assertEquals(0, funding); }
    }
    /** Explicit test DATA documents are not canonical archived bodies or an installation of owning-domain authority. */
    private static final class DataState {
        private int calls;
        private final List<Session> sessions = new ArrayList<>();
        private final FinanceStatePort port;
        private DataState() {
            var documents = new ArrayList<FinanceStatePort.Document>();
            var readers = new ArrayList<FinanceStatePort.ReaderBinding>();
            documents.add(document(FinanceStatePort.Domain.CONSTRUCTION,
                    "{\"schema\":\"xar.ck3.construction_formal_pending_v1\",\"pending\":null,\"applied\":null}"));
            readers.add(new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.CONSTRUCTION, REF, original ->
                    ConstructionLedgerCodec.decodeLedger(original.bytes()).pending().isPresent()
                            ? FinanceStatePort.Pending.PENDING : FinanceStatePort.Pending.CLEAR));
            for (var domain : List.of(FinanceStatePort.Domain.FACTION_GIFT, FinanceStatePort.Domain.FEAST,
                    FinanceStatePort.Domain.FIRST_HEIR_MARRIAGE, FinanceStatePort.Domain.CHILD_MARRIAGE,
                    FinanceStatePort.Domain.CHILD_DEFAULT_MARRIAGE)) {
                documents.add(document(domain, "{\"pending\":null}"));
                readers.add(new FinanceStatePort.ReaderBinding(domain, REF, original -> {
                    assertSame(Nil.INSTANCE, object(parse(original.bytes()), "finite explicit pending DATA").get("pending"));
                    return FinanceStatePort.Pending.CLEAR;
                }));
            }
            port = new FinanceStatePort(new FinanceStatePort.SourcePort() {
                @Override public FinanceStatePort.Read readUnderOriginalLock(PlanningRequest request) { return head(null, request); }
                @Override public FinanceStatePort.Read readUnderOriginalLock(Session same, PlanningRequest request) { return head(same, request); }
                private FinanceStatePort.Head head(Session same, PlanningRequest request) {
                    calls++; sessions.add(same);
                    return new FinanceStatePort.Head(request.before(), REF, documents, List.of(), Optional.empty());
                }
            }, readers);
        }
    }
    private static FinanceStatePort.Document document(FinanceStatePort.Domain domain, String json) {
        byte[] raw = json.getBytes(StandardCharsets.UTF_8);
        return new FinanceStatePort.Document(domain,
                new ExactRef("D:/fixture/planning-construction290/" + domain + ".json", raw.length, ActionCodec.sha256(raw)), raw);
    }
}
