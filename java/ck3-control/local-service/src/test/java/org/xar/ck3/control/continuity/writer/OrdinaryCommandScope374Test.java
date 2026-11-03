package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Owned Windows temporary DATA fixtures, not a Game process, native observation or dispatch permit. */
final class OrdinaryCommandScope374Test {
    private static final String MACHINE = "ordinary-command374";
    private static final Instant NOW = Instant.parse("2026-11-03T00:00:00Z");
    private static final ActionPorts.HistoricalReadLimits LIMITS =
            new ActionPorts.HistoricalReadLimits(8, 4L * 1024 * 1024, 32);
    @TempDir Path temp;
    private final List<StorageWriteGuardTestSupport> storageScopes = new ArrayList<>();

    @AfterEach void closeStorage() throws IOException {
        IOException failure = null;
        for (var storage : storageScopes) try { storage.close(); }
        catch (IOException problem) {
            if (failure == null) failure = problem; else failure.addSuppressed(problem);
        }
        storageScopes.clear();
        if (failure != null) throw failure;
    }

    private final class Fixture {
        final Layout layout;
        final ExactRef source;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        Fixture(String name) throws IOException {
            Path root = Files.createDirectory(temp.resolve(name));
            byte[] state = ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.txt"), "finite software DATA source374", StandardOpenOption.CREATE_NEW);
            source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),
                    LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            var storage = StorageWriteGuardTestSupport.create(layout);
            storageScopes.add(storage);
            var store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(
                    root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), storage);
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) {
                    return ContinuityJson.digest(request.detailsObject());
                }
                @Override public ContinuityState reduce(ContinuityState before, Request request) {
                    throw new IllegalStateException("fixture must never commit a ledger event");
                }
            }, Clock.fixed(NOW, ZoneOffset.UTC),
                    new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(store, writer);
        }
        ActionCommand command(String id, String json) {
            var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(
                    BigInteger.ONE, BigInteger.ONE, BigInteger.valueOf(1000)),
                    "snapshot374", BigInteger.ONE, "episode374");
            var before = new ProposalLifecycle.ObservationIdentity(MACHINE,
                    new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))), frame, 1);
            var provenance = new G2Source(MACHINE, NOW.toString(), "software374", source);
            var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, provenance, "software-observer374/v1",
                    List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("ready"), true)));
            return new ActionCommand(id, before, provenance, "session374", new OperationKey("fixture-command374"),
                    DriverJson.object(bytes(json), ActionCodec.MAX_COMMAND_BYTES), expected,
                    new JointBudgetSelector.Claims(Set.of(BigInteger.ONE), Set.of(), Set.of(), Set.of("claim374")),
                    NOW.plusSeconds(30));
        }
        ActionCommand frontendCommand(String id) {
            var gameplay = command(id, "{}");
            // These public constructors represent syntactic DATA only. They issue no native or frontend proof.
            var before = new FrontendIdentity(MACHINE, gameplay.origin().game(), "frontend374", BigInteger.ONE,
                    gameplay.origin().game().pid(), new FrontendFrame.Menu(BigInteger.ONE), source, source);
            var expected = new FrontendExpectedPostcondition(before, gameplay.source(), "software-frontend374/v1",
                    List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("ready"), true)));
            return new ActionCommand(id, new CommandOrigin.Frontend(before), gameplay.source(), "frontend374",
                    gameplay.operation(), gameplay.arguments(), new CommandExpectation.Frontend(expected),
                    new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), gameplay.deadline());
        }
    }
    private static ObjectNode state() {
        ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
        row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958);
        row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000);
        row.put("target_date_raw", 263992); row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1);
        row.put("manual_repair_count", 1); row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0);
        row.putObject("game_binding").put("pid", 123).put("creation_date", "2026-10-23T01:00:00Z"); row.putNull("latest_binding");
        row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); row.put("NEXT", 11559);
        return row;
    }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    @FunctionalInterface private interface IoCall<T> { T run() throws IOException; }
    private static <T> T io(IoCall<T> work) {
        try { return work.run(); } catch (IOException failure) { throw new UncheckedIOException(failure); }
    }

    @Test void ordinaryGameplayReusePrivateBytesAndImmutableGraph() throws IOException {
        var f = new Fixture("identity");
        var original = f.command("alias374-a", "{\"obj\":{\"rows\":[-0.0,1.00E+2,18446744073709551617]}}");
        byte[] canonical = ActionCodec.encodeCommand(original);
        byte[] changed = ActionCodec.encodeCommand(f.command("alias374-b",
                "{\"obj\":{\"rows\":[-0.0,1.00E+2,18446744073709551617]}}"));
        assertEquals(canonical.length, changed.length);
        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            var first = bound.decodeCanonicalCommand(canonical);
            assertEquals(original, first);
            assertSame(first, f.archive.decodeCanonicalCommand(canonical.clone()), "owner and same actual borrowed scope share DATA");
            byte[] caller = canonical.clone();
            assertSame(first, bound.decodeCanonicalCommand(caller));
            System.arraycopy(changed, 0, caller, 0, changed.length);
            var different = bound.decodeCanonicalCommand(caller);
            assertEquals("alias374-b", different.actionId());
            assertNotSame(first, different, "same-size changed input is compared in full");
            System.arraycopy(canonical, 0, caller, 0, canonical.length);
            assertSame(first, bound.decodeCanonicalCommand(caller), "old key owns a detached private snapshot");
            assertSame(different, bound.decodeCanonicalCommand(changed));

            var object = assertInstanceOf(OpportunityJson.Obj.class, first.arguments().get("obj"));
            var rows = assertInstanceOf(OpportunityJson.Arr.class, object.get("rows"));
            assertEquals(new OpportunityJson.DecimalValue("-0.0"), rows.items().get(0));
            assertEquals(new OpportunityJson.DecimalValue("1.00E+2"), rows.items().get(1));
            var integer = assertInstanceOf(OpportunityJson.IntegerValue.class, rows.items().get(2));
            assertEquals(new BigInteger("18446744073709551617"), integer.value());
            assertEquals(BigInteger.class, integer.value().getClass(), "private byte parser does not retain caller subclass state");
            assertThrows(UnsupportedOperationException.class, () -> first.arguments().members().clear());
            assertThrows(UnsupportedOperationException.class, () -> object.members().put("changed", OpportunityJson.Nil.INSTANCE));
            assertThrows(UnsupportedOperationException.class, () -> rows.items().add(OpportunityJson.Nil.INSTANCE));
            assertThrows(UnsupportedOperationException.class, () -> first.claims().armyIds().add(BigInteger.TEN));
            assertThrows(UnsupportedOperationException.class, () -> first.claims().commitmentKeys().clear());
            assertThrows(UnsupportedOperationException.class, () -> first.expected().values().clear());
            assertSame(first, bound.decodeCanonicalCommand(canonical));
            return null;
        }));
    }

    @Test void pureFallbackSurvivesEscapedBorrowedAndNoScope() throws IOException {
        var f = new Fixture("fallback");
        var command = f.command("fallback374", "{}");
        byte[] canonical = ActionCodec.encodeCommand(command);
        ExactRef material = f.archive.preserveMaterial(new RawJson(bytes("{\"owned374\":true}")));
        byte[] ledger = Files.readAllBytes(f.layout.snapshot());
        assertEquals(command, f.archive.decodeCanonicalCommand(canonical));
        assertNotSame(f.archive.decodeCanonicalCommand(canonical), f.archive.decodeCanonicalCommand(canonical));
        var escaped = new AtomicReference<ActionPorts.OutcomeArchive>();
        var previous = new AtomicReference<ActionCommand>();
        f.writer.locked(session -> {
            assertNotSame(f.archive.decodeCanonicalCommand(canonical), f.archive.decodeCanonicalCommand(canonical),
                    "writer.locked alone does not create an explicit archive cache");
            return f.archive.inSession(session, bound -> {
                escaped.set(bound);
                var first = bound.decodeCanonicalCommand(canonical);
                previous.set(first);
                assertSame(first, bound.decodeCanonicalCommand(canonical));
                return null;
            });
        });
        var outside = escaped.get().decodeCanonicalCommand(canonical);
        assertEquals(command, outside);
        assertNotSame(previous.get(), outside);
        assertNotSame(outside, escaped.get().decodeCanonicalCommand(canonical), "closed borrowed Session remains pure fallback");
        assertThrows(IllegalArgumentException.class, () -> escaped.get().loadFullMaterial(material));
        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            var current = bound.decodeCanonicalCommand(canonical);
            assertNotSame(previous.get(), current);
            assertSame(current, f.archive.decodeCanonicalCommand(canonical));
            var stale = escaped.get().decodeCanonicalCommand(canonical);
            assertEquals(command, stale);
            assertNotSame(current, stale, "foreign borrowed identity cannot consume the current scope cache");
            assertNotSame(stale, escaped.get().decodeCanonicalCommand(canonical));
            assertThrows(IllegalArgumentException.class, () -> escaped.get().loadFullMaterial(material));
            assertSame(current, bound.decodeCanonicalCommand(canonical), "ordinary physical failure grants no authority and no decode poison");
            assertArrayEquals(bytes("{\"owned374\":true}"), bound.loadFullMaterial(material).bytes());
            return null;
        }));
        assertArrayEquals(ledger, Files.readAllBytes(f.layout.snapshot()), "no ledger event is committed by these DATA scopes");
    }

    @Test void scopeFinallyNestedHistoryAndThreadBoundaries() throws IOException {
        var f = new Fixture("lifetime");
        byte[] canonical = ActionCodec.encodeCommand(f.command("lifetime374", "{}"));
        var firstScope = new AtomicReference<ActionCommand>();
        var failureScope = new AtomicReference<ActionCommand>();
        f.writer.locked(session -> f.archive.inSession(session, bound -> io(() -> {
            var first = bound.decodeCanonicalCommand(canonical);
            firstScope.set(first);
            assertSame(first, f.archive.inSession(session, nested -> nested.decodeCanonicalCommand(canonical)));
            var nestedFault = new IllegalStateException("nested callback fault374");
            assertSame(nestedFault, assertThrows(IllegalStateException.class,
                    () -> f.archive.inSession(session, nested -> { throw nestedFault; })));
            assertSame(first, bound.decodeCanonicalCommand(canonical), "nested exception restores outer memory context");

            var anotherThread = CompletableFuture.supplyAsync(() -> bound.decodeCanonicalCommand(canonical)).join();
            assertEquals(first, anotherThread);
            assertNotSame(first, anotherThread, "another thread has no inherited cache or new Session gate");

            f.archive.inHistoricalReadScope(session, LIMITS, historical -> {
                assertSame(first, historical.decodeCanonicalCommand(canonical));
                assertSame(first, f.archive.decodeCanonicalCommand(canonical));
                return null;
            });
            var resumed = bound.decodeCanonicalCommand(canonical);
            assertEquals(first, resumed);
            assertNotSame(first, resumed, "historical finally cleared its Command entries");
            assertSame(resumed, bound.decodeCanonicalCommand(canonical), "ordinary memory context resumes");

            assertThrows(IOException.class, () -> f.archive.inHistoricalReadScope(session, LIMITS, historical -> {
                assertThrows(IllegalArgumentException.class, () -> historical.decodeCanonicalCommand(bytes("{}")));
                assertThrows(UncheckedIOException.class, () -> historical.decodeCanonicalCommand(canonical));
                return null;
            }));
            var afterFailedHistory = bound.decodeCanonicalCommand(canonical);
            assertEquals(first, afterFailedHistory);
            assertSame(afterFailedHistory, bound.decodeCanonicalCommand(canonical),
                    "closed failed history cannot leave a dead guard on ordinary pure decoding");
            return null;
        })));
        assertNotSame(firstScope.get(), f.archive.decodeCanonicalCommand(canonical));

        var outerFault = new AssertionError("outer callback fault374");
        f.writer.locked(session -> {
            assertSame(outerFault, assertThrows(AssertionError.class, () -> f.archive.inSession(session, bound -> {
                failureScope.set(bound.decodeCanonicalCommand(canonical));
                throw outerFault;
            })));
            assertNotSame(failureScope.get(), f.archive.decodeCanonicalCommand(canonical));
            assertNotSame(f.archive.decodeCanonicalCommand(canonical), f.archive.decodeCanonicalCommand(canonical),
                    "writer.locked alone does not keep an escaped cache after exceptional scope exit");
            return null;
        });
        var next = f.writer.locked(session -> f.archive.inSession(session, bound -> bound.decodeCanonicalCommand(canonical)));
        assertEquals(firstScope.get(), next);
        assertNotSame(firstScope.get(), next);
        assertNotSame(failureScope.get(), next);

        var foreign = new Fixture("foreign");
        var called = new AtomicBoolean();
        foreign.writer.locked(session -> {
            assertThrows(UncheckedIOException.class, () -> f.archive.inSession(session, bound -> {
                called.set(true); return bound.decodeCanonicalCommand(canonical);
            }));
            return null;
        });
        assertFalse(called.get(), "actual foreign writer Session is still rejected before physical scope entry");
    }

    @Test void strictFailuresFiniteAdmissionAndNonGameplay() throws IOException {
        var f = new Fixture("strict");
        var command = f.command("strict374", "{}");
        byte[] canonical = ActionCodec.encodeCommand(command);
        byte[][] invalid = {null, new byte[0], bytes("{}"), new byte[] {(byte) 0xc3, 0x28},
                new byte[ActionCodec.MAX_COMMAND_BYTES + 1]};
        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            var first = bound.decodeCanonicalCommand(canonical);
            for (byte[] input : invalid) {
                RuntimeException original = assertThrows(RuntimeException.class, () -> ActionCodec.decodeCommand(input));
                RuntimeException actual = assertThrows(RuntimeException.class, () -> bound.decodeCanonicalCommand(input));
                assertEquals(original.getClass(), actual.getClass(), "ordinary fallback retains strict failure category");
                assertSame(first, bound.decodeCanonicalCommand(canonical), "failed ordinary pure decode cannot poison a prior entry");
            }
            var frontend = f.frontendCommand("frontend374");
            byte[] frontendBytes = ActionCodec.encodeCommand(frontend);
            var decoded = bound.decodeCanonicalCommand(frontendBytes);
            assertEquals(frontend, decoded);
            assertNotSame(decoded, bound.decodeCanonicalCommand(frontendBytes), "nonGameplay public DATA is never admitted");
            assertSame(first, bound.decodeCanonicalCommand(canonical));
            return null;
        }));
        var commands = new ArrayList<byte[]>();
        for (int i = 0; i < 17; i++) commands.add(ActionCodec.encodeCommand(f.command("entry374-" + i, "{}")));
        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            var first = bound.decodeCanonicalCommand(commands.get(0));
            var second = bound.decodeCanonicalCommand(commands.get(1));
            for (int i = 2; i < 16; i++) bound.decodeCanonicalCommand(commands.get(i));
            assertSame(first, bound.decodeCanonicalCommand(commands.get(0)));
            bound.decodeCanonicalCommand(commands.get(16));
            assertSame(first, bound.decodeCanonicalCommand(commands.get(0)), "the refreshed entry remains within finite capacity");
            assertNotSame(second, bound.decodeCanonicalCommand(commands.get(1)), "the least recently used entry was evicted");
            return null;
        }));
    }
}
