package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.ObservedGameplayEntry;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Exercises the real public Journal wrapper through public software ports only.
 * The synthetic head reaches its first canonical-record read, which deliberately
 * fails. No original record, Driver, semantic proof, physical writer, Native CAS
 * custody, completed history, prefix hit or recovery permission is claimed.
 * The public Session/locked-port shape is derived from
 * SettledSameGameRecoveryRegressionTest; its physical writer methods still refuse.
 */
final class JournalHistoricalProfile79DataTest {
    @Test void realReaderSelectsOneLargerScopeBeforeItsOriginalCanonicalRecordRead() throws Exception {
        var f = new Fixture();
        var thrown = assertThrows(IllegalStateException.class, () -> f.read(f.owner));
        assertSame(f.recordFailure, thrown);
        assertEquals(1, f.scopeCalls);
        assertEquals(1, f.recordCalls);
        assertEquals(new ActionPorts.HistoricalReadLimits(8192, 256L * 1024 * 1024, 16384), f.limits);
        assertEquals(List.of("store.enter", "archive.session.enter", "archive.withSession",
                "history.enter", "archive.loadRecord", "history.exit",
                "archive.session.exit", "store.exit"), f.events);
        assertFalse(f.active);
        assertNull(f.thread);
    }

    @Test void wrongOwnerAndInvalidFrontierRejectBeforeTheHistoricalScope() throws Exception {
        var f = new Fixture();
        var foreign = new SessionIdentity(f.owner.machineId(), f.owner.game(), "other-session");
        var ownerFailure = assertThrows(ContractViolationException.class, () -> f.read(foreign));
        assertEquals("settled recovery crossed the actual Game owner", ownerFailure.getMessage());
        assertEquals(0, f.scopeCalls);
        assertEquals(0, f.recordCalls);
        assertEquals(List.of("store.enter", "archive.session.enter", "archive.session.exit", "store.exit"), f.events);
        assertFalse(f.active);

        f.events.clear();
        ObjectNode badHeader = f.state.toJson();
        badHeader.put("status", ContinuityState.Status.COMPLETE.wire());
        badHeader.remove(WriterContracts.GAMEPLAY_ENTRY_FIELD);
        f.state = ContinuityState.fromJson(badHeader, Fixture.MACHINE);
        var headerFailure = assertThrows(ContractViolationException.class, () -> f.read(f.owner));
        assertEquals("settled recovery requires its unsaved or fully replayable actual saved frontier", headerFailure.getMessage());
        assertEquals(0, f.scopeCalls);
        assertEquals(0, f.recordCalls);
        assertEquals(List.of("store.enter", "archive.session.enter", "archive.session.exit", "store.exit"), f.events);
        assertFalse(f.active);
        assertNull(f.thread);
    }

    @Test void checkedScopeFailureKeepsItsIdentityAndDoesNotLeakTheReaderAuthorityScope() throws Exception {
        var f = new Fixture();
        var failure = new IOException("explicit software historical-scope failure");
        f.scopeFailure = failure;
        assertSame(failure, assertThrows(IOException.class, () -> f.read(f.owner)));
        assertEquals(1, f.scopeCalls);
        assertEquals(0, f.recordCalls);
        assertEquals(List.of("store.enter", "archive.session.enter", "archive.withSession",
                "history.enter", "history.exit", "archive.session.exit", "store.exit"), f.events);
        assertFalse(f.active);
        assertNull(f.thread);

        f.events.clear();
        f.scopeFailure = null;
        assertSame(f.recordFailure, assertThrows(IllegalStateException.class, () -> f.read(f.owner)));
        assertEquals(2, f.scopeCalls);
        assertEquals(1, f.recordCalls);
        assertEquals(new ActionPorts.HistoricalReadLimits(8192, 256L * 1024 * 1024, 16384), f.limits);
        assertEquals(List.of("store.enter", "archive.session.enter", "archive.withSession",
                "history.enter", "archive.loadRecord", "history.exit",
                "archive.session.exit", "store.exit"), f.events);
        assertFalse(f.active);
        assertNull(f.thread);
    }

    private static final class Fixture implements ContinuityStorePort {
        private static final String MACHINE = "journal-profile-software";
        private static final long DATE = 53144328;
        private final List<String> events = new ArrayList<>();
        private final IllegalStateException recordFailure = new IllegalStateException("explicit software first canonical-record failure");
        private final ExactRef record = reference("record");
        private final SessionIdentity owner;
        private final ActionPorts.OutcomeArchive archive;
        private final ContinuityBatchJournal journal;
        private ContinuityState state;
        private boolean active;
        private Thread thread;
        private int scopeCalls;
        private int recordCalls;
        private ActionPorts.HistoricalReadLimits limits;
        private IOException scopeFailure;

        private final Session session = new Session() {
            @Override public void requireWriter(Path ignored) { throw noPhysicalWriter(); }
            @Override public WriterContracts.Head head() {
                requireActive();
                return new WriterContracts.Head(state, List.of(), List.of(), List.of(), false);
            }
            @Override public WriterContracts.Pin capturePin(ExactRef ignored, int maximum) { throw noPhysicalWriter(); }
            @Override public void verifyPin(WriterContracts.Pin ignored) { throw noPhysicalWriter(); }
            @Override public WriterContracts.Prepared preview(WriterContracts.Request ignored) { throw noPhysicalWriter(); }
            @Override public WriterContracts.Receipt commit(WriterContracts.Prepared ignored) { throw noPhysicalWriter(); }
            @Override public ExactRef persistedHead() { throw noPhysicalWriter(); }
        };

        private Fixture() {
            ObjectNode game = StrictJson.object();
            game.put("pid", 42);
            game.put("creation_filetime", "134300000000000000");
            owner = new SessionIdentity(MACHINE, GameGeneration.fromJson(game), "software-journal-session");
            var entry = new ObservedGameplayEntry.Details(MACHINE, owner.sessionId(), "software-episode", "software-snapshot",
                    owner.game(), 1, DATE, 31254, BigInteger.ONE, BigInteger.ONE,
                    new ObservedGameplayEntry.Origin.CurrentMap(), reference("read"), reference("native"),
                    reference("driver"), reference("facts"));
            ObjectNode row = StrictJson.object();
            row.put("schema", "root.ck3.continuity-window/v1");
            row.put("machine_id", MACHINE);
            row.put("sequence", 1);
            row.put("window_id", 1);
            row.put("start_date_raw", DATE);
            row.put("target_date_raw", DATE + 8 * 24);
            row.put("target_days", 8);
            row.put("status", ContinuityState.Status.RUNNING.wire());
            row.put("last_settled_cycles", 0);
            row.put("last_settled_date_raw", DATE);
            row.set(WriterContracts.GAMEPLAY_ENTRY_FIELD, entry.toJson());
            row.set(ContinuityActionJournal.STATE_FIELD, record.toJson());
            state = ContinuityState.fromJson(row, MACHINE);
            archive = ActionPorts.OutcomeArchive.class.cast(Proxy.newProxyInstance(
                    ActionPorts.OutcomeArchive.class.getClassLoader(), new Class<?>[]{ActionPorts.OutcomeArchive.class},
                    (proxy, method, args) -> {
                        String name = method.getName();
                        if (name.equals("inSession")) {
                            requireSession((Session) args[0]);
                            events.add("archive.session.enter");
                            try { return runSession(args[1], (ActionPorts.OutcomeArchive) proxy); }
                            finally { events.add("archive.session.exit"); }
                        }
                        if (name.equals("withSession")) {
                            requireSession((Session) args[0]);
                            events.add("archive.withSession");
                            return proxy;
                        }
                        if (name.equals("inHistoricalReadScope")) {
                            requireSession((Session) args[0]);
                            limits = (ActionPorts.HistoricalReadLimits) args[1];
                            assertNotNull(limits);
                            scopeCalls++;
                            events.add("history.enter");
                            try {
                                if (scopeFailure != null) throw scopeFailure;
                                return ((ActionPorts.CheckedArchiveRead<?>) args[2]).read((ActionPorts.OutcomeArchive) proxy);
                            } finally { events.add("history.exit"); }
                        }
                        if (name.equals("loadRecord")) {
                            requireActive();
                            assertEquals(record, args[0]);
                            recordCalls++;
                            events.add("archive.loadRecord");
                            throw recordFailure;
                        }
                        throw new AssertionError("unexpected software archive operation: " + name);
                    }));
            var transitions = new OrdinaryCycleTransitions(archive,
                    (same, expected, semantic) -> { throw noPhysicalWriter(); },
                    (same, expected, pair, proof) -> { throw noPhysicalWriter(); },
                    new OriginalWindowReducer.Policy(8), this::requireSession);
            journal = new ContinuityBatchJournal(this, transitions);
        }

        private ContinuityBatchJournal.SettledSameGameData read(SessionIdentity expected) throws IOException {
            return locked(same -> journal.readSettledSameGame(same, expected));
        }

        @Override public void requireSession(Session same) {
            requireActive();
            assertSame(session, same);
        }

        @Override public <T> T locked(SessionWork<T> work) throws IOException {
            assertFalse(active);
            active = true;
            thread = Thread.currentThread();
            events.add("store.enter");
            try { return work.run(session); }
            finally {
                events.add("store.exit");
                active = false;
                thread = null;
            }
        }

        private void requireActive() {
            assertTrue(active);
            assertSame(Thread.currentThread(), thread);
        }

        @Override public WriterContracts.Prepared preview(WriterContracts.Request ignored) { throw noPhysicalWriter(); }
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared ignored) { throw noPhysicalWriter(); }
        @Override public ExactRef persistedHead() { throw noPhysicalWriter(); }

        private static AssertionError noPhysicalWriter() {
            return new AssertionError("software DATA ports have no physical writer, Native, semantic or execution authority");
        }
    }

    @SuppressWarnings("unchecked")
    private static Object runSession(Object callback, ActionPorts.OutcomeArchive same) {
        return ((Function<ActionPorts.OutcomeArchive, ?>) callback).apply(same);
    }

    /** These are deliberately unmaterialized DATA refs, never verified original artifacts. */
    private static ExactRef reference(String role) {
        return new ExactRef("software-only:journal-profile-" + role, 2,
                "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a");
    }
}
