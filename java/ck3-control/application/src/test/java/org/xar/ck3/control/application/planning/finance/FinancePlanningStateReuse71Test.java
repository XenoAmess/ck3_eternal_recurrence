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
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts.Head;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;

/**
 * Public DATA-port routing only. Session exposes head metadata and rejects every authority/write method.
 * This does not qualify canonical storage pins, a Root/lease, Native custody, or an actual cache hit.
 */
final class FinancePlanningStateReuse71Test {
    private static final ExactRef REF = new ExactRef("D:/finite-data/finance71/definition.java", 1, "a".repeat(64));
    private static final G2Source SOURCE = new G2Source("xenoamess-full-tower-eb9d2c1186",
            "2026-11-06T00:00:00Z", "1.20.0.4", REF);

    @Test void secondStateReuseStaysInsideItsOnePreQueryDataScope() throws InterruptedException {
        var once = new Fixture();
        once.collector.withPlanningState(once.request, scoped -> {
            var first = known(scoped.state(once.request));
            assertSame(first, known(scoped.state(once.request)));
            assertEquals(1, once.stateReads);
            assertNotSame(first, known(scoped.state(once.request)));
            known(scoped.state(once.request));
            assertEquals(3, once.stateReads, "a consumed scope cannot prime again");
            return null;
        });
        assertEquals(0, once.nativeReads);

        // The actual construction call chain's state -> current -> ROOT must still issue its READ.
        var root = new Fixture();
        root.collector.withPlanningState(root.request, scoped -> {
            known(scoped.state(root.request));
            var unavailable = assertInstanceOf(OrdinaryFinanceCollector.Unavailable.class, scoped.current(root.request));
            assertEquals("current campaign root unavailable", unavailable.missing().reason());
            assertEquals(1, root.stateReads);
            assertEquals(List.of(FinanceReadContracts.Query.ROOT.operation()), root.operations);
            known(scoped.state(root.request));
            known(scoped.state(root.request));
            assertEquals(3, root.stateReads, "ROOT permanently invalidates this scope, even without a ledger change");
            assertEquals(1, root.nativeReads);
            return null;
        });

        var query = new Fixture();
        query.collector.withPlanningState(query.request, scoped -> {
            known(scoped.state(query.request));
            assertInstanceOf(OrdinaryFinanceCollector.Unavailable.class,
                    scoped.query(FinanceReadContracts.Query.CASH, query.request));
            known(scoped.state(query.request)); known(scoped.state(query.request));
            assertEquals(3, query.stateReads);
            assertEquals(1, query.nativeReads);
            return null;
        });

        var view = new Fixture();
        view.collector.withPlanningState(view.request, scoped -> {
            known(scoped.state(view.request));
            var detached = scoped.planningView();
            known(detached.state(view.request)); known(scoped.state(view.request));
            assertEquals(3, view.stateReads);
            return null;
        });
        var explicit = new Fixture();
        explicit.collector.withPlanningState(explicit.request, scoped -> {
            known(scoped.state(explicit.request));
            known(scoped.state(explicit.current.get(), explicit.request));
            known(scoped.state(explicit.request));
            assertEquals(3, explicit.stateReads, "explicit Session/INTENT-style reads stay fresh");
            return null;
        });

        var escaped = new Fixture();
        var retained = escaped.collector.withPlanningState(escaped.request, scoped -> {
            known(scoped.state(escaped.request)); return scoped;
        });
        known(retained.state(escaped.request)); known(retained.state(escaped.request));
        assertEquals(3, escaped.stateReads);
        var failed = new Fixture();
        var failure = new IllegalStateException("original work failure");
        var failedCopy = new AtomicReference<OrdinaryFinanceCollector>();
        assertSame(failure, assertThrows(IllegalStateException.class,
                () -> failed.collector.withPlanningState(failed.request, scoped -> {
                    known(scoped.state(failed.request)); failedCopy.set(scoped); throw failure;
                })));
        known(failedCopy.get().state(failed.request));
        assertEquals(2, failed.stateReads, "finally disables on the original exception path");

        assertPermanentMiss(f -> f.alternateRequest = new PlanningRequest(f.request.before(), f.request.source(),
                f.request.sessionId(), f.request.deadline(), f.request.observations()));
        assertPermanentMiss(f -> f.current.set(f.metadata.newSession()));
        assertPermanentMiss(f -> f.metadata.head.set(head(2, "new-sequence")));
        assertPermanentMiss(f -> f.metadata.head.set(head(1, "changed-body-same-sequence")));
        assertPermanentMiss(f -> f.metadata.persisted.set(new ExactRef("D:/finite-data/finance71/other-point.json", 1, "b".repeat(64))));
        assertPermanentMiss(f -> f.metadata.headUnavailable = true);

        var foreignThread = new Fixture();
        foreignThread.collector.withPlanningState(foreignThread.request, scoped -> {
            known(scoped.state(foreignThread.request));
            var thrown = new AtomicReference<Throwable>();
            Thread worker = new Thread(() -> {
                try { known(scoped.state(foreignThread.request)); }
                catch (Throwable problem) { thrown.set(problem); }
            }, "finance71-data-only");
            worker.start();
            try { worker.join(); }
            catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new AssertionError(interrupted); }
            if (thrown.get() != null) throw new AssertionError(thrown.get());
            known(scoped.state(foreignThread.request));
            assertEquals(3, foreignThread.stateReads);
            return null;
        });

        var noBorrow = new Fixture();
        var plain = new OrdinaryFinanceCollector(definitions(), noBorrow.reads, noBorrow.port);
        plain.withPlanningState(noBorrow.request, scoped -> {
            known(scoped.state(noBorrow.request)); known(scoped.state(noBorrow.request)); return null;
        });
        assertEquals(2, noBorrow.stateReads);
        var firstFailure = new Fixture();
        firstFailure.metadata.headUnavailable = true;
        firstFailure.collector.withPlanningState(firstFailure.request, scoped -> {
            // Failure to capture optional metadata cannot replace an already successful full read.
            known(scoped.state(firstFailure.request));
            known(scoped.state(firstFailure.request));
            assertEquals(2, firstFailure.stateReads);
            return null;
        });
        System.out.println("FINANCE_STATE_REUSE_DATA_PASS singleHit=1 noReprime=true ROOTfresh=true queryInvalidates=true "
                + "viewAndExplicitFresh=true escapeAndExceptionClosed=true metadataMisses=6 threadMiss=true "
                + "noBorrowFresh=true privateRoot=false physicalStorageQualification=false");
    }

    private static void assertPermanentMiss(java.util.function.Consumer<Fixture> change) {
        var f = new Fixture();
        f.collector.withPlanningState(f.request, scoped -> {
            known(scoped.state(f.request)); change.accept(f);
            known(scoped.state(f.alternateRequest == null ? f.request : f.alternateRequest));
            known(scoped.state(f.request));
            assertEquals(3, f.stateReads, "a failed eligibility check cannot re-prime the same scope");
            assertEquals(0, f.nativeReads);
            return null;
        });
    }
    private static FinanceStatePort.Known known(FinanceStatePort.Result result) {
        return assertInstanceOf(FinanceStatePort.Known.class, result);
    }
    private static FinanceReadContracts definitions() {
        return new FinanceReadContracts(query -> new FinanceReadContracts.Registration(REF,
                new FinanceReadContracts.Permission(Optional.empty(), query.operation().value(),
                        ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP)));
    }
    private static final class Metadata {
        private final AtomicReference<Head> head = new AtomicReference<>(head(1, "initial"));
        private final AtomicReference<ExactRef> persisted = new AtomicReference<>(new ExactRef(
                "D:/finite-data/finance71/point.json", 1, "c".repeat(64)));
        private boolean headUnavailable;
        private Session newSession() {
            return (Session) Proxy.newProxyInstance(Session.class.getClassLoader(), new Class<?>[]{Session.class},
                    (proxy, method, arguments) -> switch (method.getName()) {
                        case "head" -> {
                            if (headUnavailable) throw new java.io.IOException("finite DATA metadata unavailable");
                            yield head.get();
                        }
                        case "persistedHead" -> persisted.get();
                        default -> throw new AssertionError("DATA Session forbids authority/write: " + method.getName());
                    });
        }
    }
    private static final class Fixture {
        private final PlanningRequest request = request();
        private PlanningRequest alternateRequest;
        private final Metadata metadata = new Metadata();
        private final AtomicReference<Session> current = new AtomicReference<>(metadata.newSession());
        private int stateReads;
        private int nativeReads;
        private final List<org.xar.ck3.control.application.action.OperationKey> operations = new ArrayList<>();
        private final PlanningReadPort reads = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest input) {
                return unavailable(contract, input);
            }
            @Override public <T> PlanningReadResult<T> read(Session session, ReadContract<T> contract, PlanningReadRequest input) {
                assertSame(current.get(), session); return unavailable(contract, input);
            }
            private <T> PlanningReadResult<T> unavailable(ReadContract<T> contract, PlanningReadRequest input) {
                assertSame(request.before(), input.before());
                operations.add(contract.operation()); nativeReads++;
                return new PlanningReadResult.Unavailable<>("finite DATA has no Native transport or custody", Optional.empty());
            }
        };
        private final FinanceStatePort port;
        private final OrdinaryFinanceCollector collector;
        private Fixture() {
            var documents = new ArrayList<FinanceStatePort.Document>();
            var readers = new ArrayList<FinanceStatePort.ReaderBinding>();
            for (var domain : List.of(FinanceStatePort.Domain.CONSTRUCTION, FinanceStatePort.Domain.FACTION_GIFT,
                    FinanceStatePort.Domain.FEAST, FinanceStatePort.Domain.FIRST_HEIR_MARRIAGE,
                    FinanceStatePort.Domain.CHILD_MARRIAGE, FinanceStatePort.Domain.CHILD_DEFAULT_MARRIAGE)) {
                documents.add(document(domain, "{\"pending\":null}"));
                readers.add(new FinanceStatePort.ReaderBinding(domain, REF, original -> {
                    assertSame(Nil.INSTANCE, object(parse(original.bytes()), "finite ledger DATA").get("pending"));
                    return FinanceStatePort.Pending.CLEAR;
                }));
            }
            documents.add(document(FinanceStatePort.Domain.MERCENARY,
                    "{\"schema\":\"xar.war-mercenary-pending.v1\",\"pending\":null,\"observed\":[]}"));
            readers.add(new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.MERCENARY, REF, original ->
                    MercenaryProcurement.decode(original.bytes()).pending().isPresent()
                            ? FinanceStatePort.Pending.PENDING : FinanceStatePort.Pending.CLEAR));
            port = new FinanceStatePort(new FinanceStatePort.SourcePort() {
                @Override public FinanceStatePort.Read readUnderOriginalLock(PlanningRequest input) { return data(null, input); }
                @Override public FinanceStatePort.Read readUnderOriginalLock(Session session, PlanningRequest input) {
                    assertSame(current.get(), session); return data(session, input);
                }
                private FinanceStatePort.Head data(Session session, PlanningRequest input) {
                    stateReads++;
                    return new FinanceStatePort.Head(input.before(), metadata.persisted.get(), documents, List.of(), Optional.empty());
                }
            }, readers);
            collector = new OrdinaryFinanceCollector(definitions(), reads, port, current::get);
        }
    }
    private static FinanceStatePort.Document document(FinanceStatePort.Domain domain, String json) {
        byte[] raw = json.getBytes(StandardCharsets.UTF_8);
        return new FinanceStatePort.Document(domain, new ExactRef("D:/finite-data/finance71/" + domain + ".json",
                raw.length, ActionCodec.sha256(raw)), raw);
    }
    private static Head head(long sequence, String label) {
        byte[] raw = ("{\"schema\":\"root.ck3.continuity-window/v1\",\"machine_id\":\"" + SOURCE.machineId()
                + "\",\"sequence\":" + sequence + ",\"window_id\":1,\"start_date_raw\":100,\"target_date_raw\":124,"
                + "\"target_days\":1,\"status\":\"running\",\"last_settled_cycles\":0,\"last_settled_date_raw\":100,"
                + "\"data_label\":\"" + label + "\"}").getBytes(StandardCharsets.UTF_8);
        var state = new ContinuityState(SOURCE.machineId(), sequence, new ContinuityState.Origin(1, 100, 124, 1),
                ContinuityState.Status.RUNNING, 0, 100, raw);
        return new Head(state, List.of(), List.of(), List.of(), false);
    }
    private static PlanningRequest request() {
        var before = new ProposalLifecycle.ObservationIdentity(SOURCE.machineId(),
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE, BigInteger.ONE, BigInteger.valueOf(100)),
                        "native:finance71", BigInteger.ONE, "episode-finance71"), 1);
        Obj snapshot = object(parse(("{\"paused\":true,\"map_ready\":true,\"snapshot_id\":\"native:finance71\","
                + "\"revision\":1,\"native_revision\":1,\"date_raw\":100,\"episode_run_id\":\"episode-finance71\","
                + "\"played_character\":{\"character_id\":1,\"alive\":true},\"active_wars\":[],\"player_armies\":[],"
                + "\"active_event\":null,\"pending_character_interaction\":null}").getBytes(StandardCharsets.UTF_8)), "finite DATA snapshot");
        return new PlanningRequest(before, SOURCE, "session-finance71", Instant.parse("2099-01-01T00:00:00Z"),
                new PlanningObservation(snapshot, List.of(), Set.of(), Set.of(), Optional.empty(), List.of(),
                        Optional.empty(), Optional.empty(), false));
    }
}
