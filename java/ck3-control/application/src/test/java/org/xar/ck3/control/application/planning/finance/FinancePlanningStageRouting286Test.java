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
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;

/** Application routing only: DATA Sessions/heads grant no writer, archive or Native permission. */
final class FinancePlanningStageRouting286Test {
    private static final ExactRef REF = new ExactRef("D:/fixture/planning-finance286/source.java", 1, "a".repeat(64));
    private static final G2Source SOURCE = new G2Source("xenoamess-full-tower-eb9d2c1186", "2026-11-02T00:00:00Z", "1.20.0.4", REF);
    private static final String GAP = "finite DATA port has no Native transport or original custody";

    @Test void explicitViewIsLazyAndResolvesTheCurrentBorrowedSessionOnEveryRead() {
        var input = request(true, false, Set.of());
        var definitions = definitions();
        var reads = new CountingReads();
        var data = new DataState();
        var base = new OrdinaryFinanceCollector(definitions, reads, data.port);
        var view = base.planningView();
        assertEquals(1, reads.views);
        assertTrue(reads.calls.isEmpty());
        assertEquals(0, data.calls);
        missing(view.query(FinanceReadContracts.Query.ROOT, input));
        missing(base.query(FinanceReadContracts.Query.ROOT, input));
        assertRead(reads.calls.get(0), "P", null, definitions, FinanceReadContracts.Query.ROOT, input);
        assertRead(reads.calls.get(1), "D", null, definitions, FinanceReadContracts.Query.ROOT, input);
        assertEquals(2, reads.calls.size());

        Session a = sessionToken(), b = sessionToken();
        var current = new AtomicReference<Session>();
        var supplies = new AtomicInteger();
        var heldBase = new OrdinaryFinanceCollector(definitions, reads, data.port, () -> {
            supplies.incrementAndGet();
            Session actual = current.get();
            if (actual == null) throw new AssertionError("view creation captured an unheld Session");
            return actual;
        });
        var heldView = heldBase.planningView();
        assertEquals(0, supplies.get());
        assertEquals(2, reads.views);
        current.set(a);
        missing(heldView.query(FinanceReadContracts.Query.ROOT, input));
        current.set(b);
        missing(heldView.query(FinanceReadContracts.Query.ROOT, input));
        missing(heldBase.query(FinanceReadContracts.Query.CASH, input));
        assertRead(reads.calls.get(2), "P", a, definitions, FinanceReadContracts.Query.ROOT, input);
        assertRead(reads.calls.get(3), "P", b, definitions, FinanceReadContracts.Query.ROOT, input);
        assertRead(reads.calls.get(4), "D", b, definitions, FinanceReadContracts.Query.CASH, input);
        assertEquals(3, supplies.get());
        assertEquals("finance collector cannot replace its borrowed writer",
                assertThrows(IllegalArgumentException.class,
                        () -> heldView.query(a, FinanceReadContracts.Query.ROOT, input)).getMessage());
        assertEquals(5, reads.calls.size());
        assertEquals(0, data.calls);
        assertEquals(4, supplies.get());
        current.set(a);
        missing(heldView.query(a, FinanceReadContracts.Query.ROOT, input));
        assertRead(reads.calls.get(5), "P", a, definitions, FinanceReadContracts.Query.ROOT, input);
        assertEquals(6, reads.calls.size());
        assertEquals(5, supplies.get());
        assertEquals(2, reads.views);
        assertEquals(0, data.calls);
    }

    @Test void eligibleStagesReachPlanningRootAndGuardedStagesStayLazy() {
        var definitions = definitions();
        var reads = new CountingReads();
        var data = new DataState();
        var collector = new OrdinaryFinanceCollector(definitions, reads, data.port);
        var policies = policies(collector);
        var peace = request(true, false, Set.of());
        var war = request(true, true, Set.of());
        var quiet = OrdinaryPolicy.Draft.empty();
        var selected = new OrdinaryPolicy.Draft("finite-selected", "retained", "independent work already selected",
                OrdinaryPolicy.Kind.FOREGROUND, Optional.empty(), OrdinaryPolicy.Purpose.READ_ONLY, Optional.empty(), empty());
        assertInstanceOf(OrdinaryPolicy.Defer.class,
                stage(policies, PlanningStage.FACTION_GIFT).evaluate(peace, quiet));
        assertRead(reads.calls.get(0), "P", null, definitions, FinanceReadContracts.Query.ROOT, peace);
        assertInstanceOf(OrdinaryPolicy.Defer.class,
                stage(policies, PlanningStage.WAR_MERCENARY_CURRENT_CASH).evaluate(war, quiet));
        assertRead(reads.calls.get(1), "P", null, definitions, FinanceReadContracts.Query.ROOT, war);
        var recovery = assertInstanceOf(OrdinaryPolicy.NotApplicable.class,
                stage(policies, PlanningStage.WAR_MERCENARY_CURRENT_CASH).evaluate(war, selected));
        assertEquals("no source-qualified prior emergency procurement", recovery.reason());
        assertRead(reads.calls.get(2), "P", null, definitions, FinanceReadContracts.Query.ROOT, war);
        assertEquals(3, reads.calls.size());
        assertEquals(3, reads.views);
        assertEquals(3, data.calls);

        assertInstanceOf(OrdinaryPolicy.NotApplicable.class,
                stage(policies, PlanningStage.WAR_MERCENARY_CURRENT_CASH).evaluate(peace, quiet));
        assertInstanceOf(OrdinaryPolicy.NotApplicable.class,
                stage(policies, PlanningStage.FACTION_GIFT).evaluate(request(false, false, Set.of()), quiet));
        assertInstanceOf(OrdinaryPolicy.NotApplicable.class,
                stage(policies, PlanningStage.FACTION_GIFT).evaluate(peace, selected));
        assertEquals(3, reads.views, "guard-negative stages must not eagerly request a planning facade");
        assertEquals(3, reads.calls.size());
        assertEquals(3, data.calls);
        missing(collector.query(FinanceReadContracts.Query.ROOT, peace));
        assertRead(reads.calls.get(3), "D", null, definitions, FinanceReadContracts.Query.ROOT, peace);
        assertEquals(4, reads.calls.size());
        assertEquals(3, reads.views);
        assertEquals(3, data.calls);
    }

    @Test void publicHireAndGiftKeepTheOrdinaryReadAfterTheirLegalDataPrerequisites() {
        var definitions = definitions();
        var reads = new CountingReads();
        var data = new DataState();
        Session same = sessionToken();
        var collector = new OrdinaryFinanceCollector(definitions, reads, data.port, () -> same);
        var policies = policies(collector);
        var legal = request(true, false, Set.of(OrdinaryFinancePolicies.MERCENARY, OrdinaryFinancePolicies.GIFT));
        assertEquals("actual full finance quote unavailable", assertThrows(IllegalArgumentException.class,
                () -> policies.publicHire(same, legal, BigInteger.ONE, "finite-hire-286")).getMessage());
        assertRead(reads.calls.get(0), "D", same, definitions, FinanceReadContracts.Query.ROOT, legal);
        assertEquals("complete current finance source required for public Gift", assertThrows(IllegalArgumentException.class,
                () -> policies.publicGift(same, legal, empty(), empty(), "finite-gift-286")).getMessage());
        assertRead(reads.calls.get(1), "D", same, definitions, FinanceReadContracts.Query.ROOT, legal);
        assertEquals(2, reads.calls.size());
        assertEquals(0, reads.views);
        assertEquals(2, data.calls);
        assertSame(same, data.sessions.get(0));
        assertSame(same, data.sessions.get(1));
        var unregistered = request(true, false, Set.of());
        assertEquals("actual legal paused hire route unavailable", assertThrows(IllegalArgumentException.class,
                () -> policies.publicHire(same, unregistered, BigInteger.ONE, "unregistered-hire-286")).getMessage());
        assertEquals("actual Gift action registration absent", assertThrows(IllegalArgumentException.class,
                () -> policies.publicGift(same, unregistered, empty(), empty(), "unregistered-gift-286")).getMessage());
        assertEquals(2, reads.calls.size());
        assertEquals(2, data.calls);
        assertEquals(0, reads.views);
    }

    @Test void planningViewDoesNotReplaceTheExternalFeastOrFactionOwners() {
        var original = request(true, false, Set.of());
        Session held = sessionToken();
        var owners = new ArrayList<ExternalCall>();
        var definitions = new FinanceReadContracts(registrations(), new FinanceReadContracts.ExternalFeastInputs() {
            @Override public PlanningReadResult<PlanningReadReceipt> read(PlanningRequest actual) {
                owners.add(new ExternalCall("FEAST", null, actual)); return externalMissing();
            }
            @Override public PlanningReadResult<PlanningReadReceipt> read(Session same, PlanningRequest actual) {
                owners.add(new ExternalCall("FEAST", same, actual)); return externalMissing();
            }
        }, new FinanceReadContracts.ExternalFactionAlerts() {
            @Override public ExactRef definitionSource() { return REF; }
            @Override public PlanningReadResult<PlanningReadReceipt> read(PlanningRequest actual) {
                owners.add(new ExternalCall("FACTION", null, actual)); return externalMissing();
            }
            @Override public PlanningReadResult<PlanningReadReceipt> read(Session same, PlanningRequest actual) {
                owners.add(new ExternalCall("FACTION", same, actual)); return externalMissing();
            }
            @Override public void verifyOriginal(PlanningReadReceipt receipt, Obj snapshot) {
                throw new AssertionError("Unavailable cannot enter original receipt verification");
            }
        });
        var reads = new CountingReads();
        var data = new DataState();
        var base = new OrdinaryFinanceCollector(definitions, reads, data.port);
        var view = base.planningView();
        missing(view.query(FinanceReadContracts.Query.FEAST_INPUTS, original));
        missing(view.query(held, FinanceReadContracts.Query.FACTION_ALERTS, original));
        missing(base.query(held, FinanceReadContracts.Query.FEAST_INPUTS, original));
        missing(base.query(FinanceReadContracts.Query.FACTION_ALERTS, original));
        assertEquals(4, owners.size());
        assertExternal(owners.get(0), "FEAST", null, original);
        assertExternal(owners.get(1), "FACTION", held, original);
        assertExternal(owners.get(2), "FEAST", held, original);
        assertExternal(owners.get(3), "FACTION", null, original);
        assertTrue(reads.calls.isEmpty(), "typed owner routes must not fall through to either generic port");
        assertEquals(1, reads.views);
        assertEquals(0, data.calls);
        assertFalse(definitions.registeredContracts().stream().anyMatch(contract ->
                Set.of(FinanceReadContracts.Query.FEAST_INPUTS.operation(), FinanceReadContracts.Query.FEAST_DIAGNOSTIC.operation(),
                        FinanceReadContracts.Query.FEAST_HOSTED.operation(), FinanceReadContracts.Query.FACTION_ALERTS.operation())
                        .contains(contract.operation())));
    }

    private static OrdinaryFinancePolicies policies(OrdinaryFinanceCollector collector) {
        return new OrdinaryFinancePolicies(REF, collector, (operation, request, arguments) -> {
            throw new AssertionError("typed Unavailable must stop before Effects, quote or action construction");
        }, List.of());
    }
    private static OrdinaryPolicy stage(OrdinaryFinancePolicies policies, PlanningStage stage) {
        return policies.stages().stream().filter(value -> value.stage() == stage).findFirst().orElseThrow();
    }
    private static FinanceReadContracts definitions() { return new FinanceReadContracts(registrations()); }
    private static FinanceReadContracts.Registrations registrations() {
        return query -> new FinanceReadContracts.Registration(REF, new FinanceReadContracts.Permission(
                Optional.empty(), query.operation().value(), ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                ReadContract.WireProfile.EXECUTE_STEP));
    }
    private static Session sessionToken() {
        return (Session) Proxy.newProxyInstance(Session.class.getClassLoader(), new Class<?>[]{Session.class},
                (proxy, method, arguments) -> { throw new AssertionError("DATA Session token was dereferenced: " + method.getName()); });
    }
    private static Obj empty() { return new Obj(Map.of()); }
    private static PlanningRequest request(boolean paused, boolean war, Set<OperationKey> operations) {
        var before = new ProposalLifecycle.ObservationIdentity(SOURCE.machineId(),
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE, BigInteger.ONE, BigInteger.valueOf(100)),
                        "native:finance286", BigInteger.ONE, "episode-finance286"), 1);
        Obj snapshot = object(parse(("{\"paused\":" + paused + ",\"map_ready\":true,\"snapshot_id\":\"native:finance286\","
                + "\"revision\":1,\"native_revision\":1,\"date_raw\":100,\"episode_run_id\":\"episode-finance286\","
                + "\"played_character\":{\"character_id\":1,\"alive\":true},\"active_wars\":" + (war ? "[{}]" : "[]")
                + ",\"player_armies\":[],\"active_event\":null,\"pending_character_interaction\":null}")
                .getBytes(StandardCharsets.UTF_8)), "complete finite planning DATA");
        return new PlanningRequest(before, SOURCE, "session-finance286", Instant.parse("2099-01-01T00:00:00Z"),
                new PlanningObservation(snapshot, List.of(), operations, Set.of(), Optional.empty(), List.of(),
                        Optional.empty(), Optional.empty(), false));
    }
    private static void missing(OrdinaryFinanceCollector.Read<?> result) {
        var unavailable = assertInstanceOf(OrdinaryFinanceCollector.Unavailable.class, result);
        assertTrue(unavailable.missing().reason().contains(GAP));
    }
    private record Call(String mode, Session session, ReadContract<?> contract, PlanningReadRequest request) { }
    private static void assertRead(Call call, String mode, Session session, FinanceReadContracts definitions,
            FinanceReadContracts.Query query, PlanningRequest original) {
        assertEquals(mode, call.mode());
        assertSame(session, call.session());
        assertSame(definitions.contract(query), call.contract());
        Obj arguments = query == FinanceReadContracts.Query.ROOT
                ? FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY) : empty();
        assertEquals(new PlanningReadRequest(original.before(), original.source(), original.sessionId(), query.operation(), arguments,
                original.deadline()), call.request());
    }
    private static final class CountingReads implements PlanningReadPort {
        private final List<Call> calls = new ArrayList<>();
        private int views;
        private final PlanningReadPort planning = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
                return record("P", null, contract, request);
            }
            @Override public <T> PlanningReadResult<T> read(Session session, ReadContract<T> contract, PlanningReadRequest request) {
                return record("P", session, contract, request);
            }
        };
        @Override public PlanningReadPort planningReads() { views++; return planning; }
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
            return record("D", null, contract, request);
        }
        @Override public <T> PlanningReadResult<T> read(Session session, ReadContract<T> contract, PlanningReadRequest request) {
            return record("D", session, contract, request);
        }
        private <T> PlanningReadResult<T> record(String mode, Session session, ReadContract<T> contract, PlanningReadRequest request) {
            calls.add(new Call(mode, session, contract, request));
            return new PlanningReadResult.Unavailable<>(GAP, Optional.empty());
        }
    }
    /** Finite in-memory explicit pending documents; deliberately not canonical source/owning-codec qualification. */
    private static final class DataState {
        private int calls;
        private final List<Session> sessions = new ArrayList<>();
        private final FinanceStatePort port;
        private DataState() {
            var documents = new ArrayList<FinanceStatePort.Document>();
            var readers = new ArrayList<FinanceStatePort.ReaderBinding>();
            for (var domain : List.of(FinanceStatePort.Domain.CONSTRUCTION, FinanceStatePort.Domain.FACTION_GIFT,
                    FinanceStatePort.Domain.FEAST, FinanceStatePort.Domain.FIRST_HEIR_MARRIAGE,
                    FinanceStatePort.Domain.CHILD_MARRIAGE, FinanceStatePort.Domain.CHILD_DEFAULT_MARRIAGE)) {
                documents.add(document(domain, "{\"pending\":null}"));
                readers.add(new FinanceStatePort.ReaderBinding(domain, REF, original -> {
                    assertSame(Nil.INSTANCE, object(parse(original.bytes()), "finite explicit ledger DATA").get("pending"));
                    return FinanceStatePort.Pending.CLEAR;
                }));
            }
            documents.add(document(FinanceStatePort.Domain.MERCENARY,
                    "{\"schema\":\"xar.war-mercenary-pending.v1\",\"pending\":null,\"observed\":[]}"));
            readers.add(new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.MERCENARY, REF, original ->
                    MercenaryProcurement.decode(original.bytes()).pending().isPresent()
                            ? FinanceStatePort.Pending.PENDING : FinanceStatePort.Pending.CLEAR));
            port = new FinanceStatePort(new FinanceStatePort.SourcePort() {
                @Override public FinanceStatePort.Read readUnderOriginalLock(PlanningRequest request) { return head(null, request); }
                @Override public FinanceStatePort.Read readUnderOriginalLock(Session session, PlanningRequest request) { return head(session, request); }
                private FinanceStatePort.Head head(Session session, PlanningRequest request) {
                    calls++; sessions.add(session);
                    return new FinanceStatePort.Head(request.before(), REF, documents, List.of(), Optional.empty());
                }
            }, readers);
        }
    }
    private static FinanceStatePort.Document document(FinanceStatePort.Domain domain, String json) {
        byte[] raw = json.getBytes(StandardCharsets.UTF_8);
        return new FinanceStatePort.Document(domain,
                new ExactRef("D:/fixture/planning-finance286/" + domain + ".json", raw.length, ActionCodec.sha256(raw)), raw);
    }
    private record ExternalCall(String owner, Session session, PlanningRequest request) { }
    private static PlanningReadResult<PlanningReadReceipt> externalMissing() {
        return new PlanningReadResult.Unavailable<>(GAP, Optional.empty());
    }
    private static void assertExternal(ExternalCall call, String owner, Session session, PlanningRequest request) {
        assertEquals(owner, call.owner());
        assertSame(session, call.session());
        assertSame(request, call.request());
    }
}
