package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.Proxy;
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

/** New bounded software DATA tests. Real owned Windows writer/archive scope, no Game or speed claim. */
final class HistoricalCommandReuse320Test {
    private static final String MACHINE = "historical-command320";
    private static final Instant NOW = Instant.parse("2026-11-02T00:00:00Z");
    private static final ActionPorts.HistoricalReadLimits LIMITS = new ActionPorts.HistoricalReadLimits(8, 4L * 1024 * 1024, 32);
    @TempDir Path temp;
    private final List<StorageWriteGuardTestSupport> storageScopes = new ArrayList<>();

    @AfterEach void closeStorage() throws IOException {
        IOException failure = null;
        for (var storage : storageScopes) try { storage.close(); }
        catch (IOException problem) { if (failure == null) failure = problem; else failure.addSuppressed(problem); }
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
            Files.writeString(root.resolve("source.txt"), "finite software source320", StandardOpenOption.CREATE_NEW);
            source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),
                    LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            var storage = StorageWriteGuardTestSupport.create(layout);
            storageScopes.add(storage);
            var store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), storage);
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState before, Request request) { throw new IllegalStateException("no fixture ledger commits"); }
            }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(store, writer);
        }
        ActionCommand command(String id, String json) {
            var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE, BigInteger.ONE, BigInteger.valueOf(1000)),
                    "snapshot320", BigInteger.ONE, "episode320");
            var before = new ProposalLifecycle.ObservationIdentity(MACHINE,
                    new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))), frame, 1);
            var provenance = new G2Source(MACHINE, NOW.toString(), "software320", source);
            var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, provenance, "software-observer320/v1",
                    List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("ready"), true)));
            return new ActionCommand(id, before, provenance, "session320", new OperationKey("fixture-command320"),
                    DriverJson.object(bytes(json), ActionCodec.MAX_COMMAND_BYTES), expected,
                    new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(30));
        }
    }
    private static ObjectNode state() {
        ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
        row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958);
        row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
        row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
        row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0);
        row.putObject("game_binding").put("pid", 123).put("creation_date", "2026-10-23T01:00:00Z"); row.putNull("latest_binding");
        row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); row.put("NEXT", 11559); return row;
    }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }

    @Test void exactBytesAliasAndImmutableGameplayOnlyInsideRealScope() throws IOException {
        var f = new Fixture("identity");
        var original = f.command("same320", "{\"negative\":-0.0,\"scaled\":1.00E+2,\"large\":18446744073709551617,\"list\":[1]}");
        byte[] canonical = ActionCodec.encodeCommand(original);
        f.writer.locked(session -> f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
            var first = bound.decodeCanonicalCommand(canonical);
            assertEquals(original, first);
            assertSame(first, f.archive.decodeCanonicalCommand(canonical.clone()), "owner and borrowed view share this actual scope");
            assertSame(first, bound.inSession(session, nested -> nested.decodeCanonicalCommand(canonical)), "ordinary nested view retains the actual outer scope");
            byte[] aliased = canonical.clone();
            assertSame(first, bound.decodeCanonicalCommand(aliased));
            aliased[0] = '[';
            assertSame(first, bound.decodeCanonicalCommand(canonical), "retained key must not alias caller bytes");
            assertThrows(UnsupportedOperationException.class, () -> first.arguments().members().put("mutate", OpportunityJson.Nil.INSTANCE));
            assertThrows(UnsupportedOperationException.class, () -> first.claims().armyIds().add(BigInteger.TEN));
            assertThrows(UnsupportedOperationException.class, () -> first.expected().values().clear());
            byte[] changed = bytes(new String(canonical, StandardCharsets.UTF_8).replace("-0.0", "0.0"));
            var other = bound.decodeCanonicalCommand(changed);
            assertNotSame(first, other);
            assertEquals(new OpportunityJson.DecimalValue("-0.0"), first.arguments().get("negative"));
            assertEquals(new OpportunityJson.DecimalValue("0.0"), other.arguments().get("negative"));
            assertSame(other, bound.decodeCanonicalCommand(changed.clone()));
            return null;
        }));
    }

    @Test void scopeLifetimeNestedFailureAndCaughtInvalidCannotReturnCachedSuccess() throws IOException {
        var f = new Fixture("lifetime");
        byte[] canonical = ActionCodec.encodeCommand(f.command("lifetime320", "{}"));
        assertNotSame(f.archive.decodeCanonicalCommand(canonical), f.archive.decodeCanonicalCommand(canonical));
        var escaped = new AtomicReference<ActionPorts.OutcomeArchive>();
        var old = new AtomicReference<ActionCommand>();
        f.writer.locked(session -> {
            f.archive.inSession(session, bound -> {
                assertNotSame(bound.decodeCanonicalCommand(canonical), bound.decodeCanonicalCommand(canonical)); return null;
            });
            f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
                escaped.set(bound); old.set(bound.decodeCanonicalCommand(canonical)); return null;
            });
            assertNotSame(old.get(), escaped.get().decodeCanonicalCommand(canonical));
            f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
                assertNotSame(old.get(), bound.decodeCanonicalCommand(canonical)); return null;
            });
            assertThrows(IOException.class, () -> f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
                bound.decodeCanonicalCommand(canonical);
                assertThrows(IllegalArgumentException.class, () -> bound.decodeCanonicalCommand(bytes("{}")));
                assertThrows(UncheckedIOException.class, () -> bound.decodeCanonicalCommand(canonical)); return null;
            }));
            assertThrows(IOException.class, () -> f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
                bound.decodeCanonicalCommand(canonical);
                assertThrows(IOException.class, () -> bound.inHistoricalReadScope(session, LIMITS, nested -> null));
                assertThrows(UncheckedIOException.class, () -> bound.decodeCanonicalCommand(canonical)); return null;
            }));
            return null;
        });
        f.writer.locked(session -> {
            assertThrows(IOException.class, () -> f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
                bound.decodeCanonicalCommand(canonical);
                assertThrows(org.xar.ck3.control.contracts.ContractViolationException.class, () -> escaped.get().decodeCanonicalCommand(canonical));
                return null;
            }));
            return null;
        });
    }

    @Test void entryAndByteBoundsUseLruForOlderCommands() throws IOException {
        var f = new Fixture("lru");
        var raw = new ArrayList<byte[]>();
        for (int i = 0; i < 17; i++) raw.add(ActionCodec.encodeCommand(f.command("entry320-" + i, "{}")));
        f.writer.locked(session -> f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
            var first = bound.decodeCanonicalCommand(raw.get(0));
            var second = bound.decodeCanonicalCommand(raw.get(1));
            for (int i = 2; i < 16; i++) bound.decodeCanonicalCommand(raw.get(i));
            assertSame(first, bound.decodeCanonicalCommand(raw.get(0)), "refresh entry0 as most recently used");
            bound.decodeCanonicalCommand(raw.get(16));
            assertSame(first, bound.decodeCanonicalCommand(raw.get(0)));
            assertNotSame(second, bound.decodeCanonicalCommand(raw.get(1)), "least recently used, not most recent, was evicted");
            return null;
        }));
        byte[] large = ActionCodec.encodeCommand(f.command("bytes320-0", "{\"pad\":\"" + "x".repeat(950_000) + "\"}"));
        assertTrue(large.length < ActionCodec.MAX_COMMAND_BYTES);
        f.writer.locked(session -> f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
            var first = bound.decodeCanonicalCommand(large);
            for (int i = 1; i <= 8; i++) bound.decodeCanonicalCommand(bytes(new String(large, StandardCharsets.UTF_8).replace("bytes320-0", "bytes320-" + i)));
            assertNotSame(first, bound.decodeCanonicalCommand(large), "9 large keys exceed 8MiB before the 16-entry bound");
            return null;
        }));
    }

    @Test void eachReceiptStillDecodesStateAndVerifiesBodyEvenWhenCommandHits() throws IOException {
        var f = new Fixture("receipt");
        var command = f.command("receipt320", "{\"negative\":-0.0}");
        var request = new NativeRequest("fixture-command320", "game.command.fixture320", new RawJson(bytes("{}")));
        var guard = new GuardEvidence(command.before(), command.source(), command.sessionId(), BigInteger.ONE,
                command.operation(), f.source, f.source, "software320", NOW, NOW.plusSeconds(20));
        var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command),
                new ActionState.Submitting(new ActionState.Attempt("request320", NOW, guard, request)));
        f.writer.locked(session -> f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
            var calls = new ArrayList<String>();
            var allowCommandMemo = new java.util.concurrent.atomic.AtomicBoolean(false);
            var adapter = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                    new Class<?>[] {ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                        calls.add(method.getName());
                        return switch (method.getName()) {
                            case "decodeCanonicalCommand" -> {
                                assertTrue(allowCommandMemo.get(), "legacy codec must not invoke the newly added archive helper");
                                yield bound.decodeCanonicalCommand((byte[]) args[0]);
                            }
                            case "requestReferenceOf" -> f.source;
                            case "loadRequest" -> request;
                            default -> throw new AssertionError("unexpected callback " + method.getName());
                        };
                    });
            byte[] wire = ActionReceiptCodec.encodeReceipt(receipt, adapter); calls.clear();
            assertEquals(receipt, ActionReceiptCodec.decodeReceipt(wire, adapter));
            assertEquals(List.of("loadRequest"), calls, "original two-argument API keeps the legacy callback contract");
            calls.clear(); allowCommandMemo.set(true);
            var first = ActionReceiptCodec.decodeReceiptUsingCanonicalCommand(wire, adapter);
            var second = ActionReceiptCodec.decodeReceiptUsingCanonicalCommand(wire, adapter);
            assertNotSame(first, second); assertSame(first.command(), second.command());
            assertNotSame(first.state(), second.state());
            assertEquals(List.of("decodeCanonicalCommand", "loadRequest", "decodeCanonicalCommand", "loadRequest"), calls);
            byte[] wrongBody = bytes(new String(wire, StandardCharsets.UTF_8).replace(receipt.bodySha256(), "0".repeat(64)));
            assertThrows(IllegalArgumentException.class, () -> ActionReceiptCodec.decodeReceiptUsingCanonicalCommand(wrongBody, adapter));
            byte[] changedCommand = bytes(new String(wire, StandardCharsets.UTF_8).replace("-0.0", "0.0"));
            assertThrows(IllegalArgumentException.class, () -> ActionReceiptCodec.decodeReceiptUsingCanonicalCommand(changedCommand, adapter));
            return null;
        }));
    }

    @Test void actualFreshReceiptReadsRemainAndBadReferencePoisonsScopeAfterMemoHit() throws IOException {
        var f = new Fixture("fresh");
        var command = f.command("fresh320", "{}");
        var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
        ExactRef ref = f.archive.preserveReceipt(receipt);
        f.writer.locked(session -> {
            assertThrows(IOException.class, () -> f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
                var first = bound.loadReceipt(ref);
                var second = bound.loadReceipt(ref);
                assertNotSame(first, second); assertSame(first.command(), second.command());
                var wrong = new ExactRef(ref.path(), ref.bytes() + 1, ref.sha256());
                assertThrows(UncheckedIOException.class, () -> bound.loadReceipt(wrong));
                assertThrows(UncheckedIOException.class, () -> bound.decodeCanonicalCommand(ActionCodec.encodeCommand(command)));
                return null;
            }));
            return null;
        });
    }

    @Test void nullArchiveAndDefaultAndNonGameplayRemainFullCodec() throws IOException {
        var f = new Fixture("fallback");
        var command = f.command("fallback320", "{}");
        var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
        byte[] wire = ActionReceiptCodec.encodeReceipt(receipt, null);
        assertEquals(receipt, ActionReceiptCodec.decodeReceipt(wire, null));
        var defaultPort = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                new Class<?>[] {ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                    if (method.isDefault()) return java.lang.reflect.InvocationHandler.invokeDefault(proxy, method, args);
                    throw new AssertionError("unexpected default-adapter callback " + method.getName());
                });
        byte[] canonical = ActionCodec.encodeCommand(command);
        assertEquals(command, defaultPort.decodeCanonicalCommand(canonical));
        assertNotSame(defaultPort.decodeCanonicalCommand(canonical), defaultPort.decodeCanonicalCommand(canonical));
        var game = command.origin().game();
        var identity = new FrontendIdentity(MACHINE, game, "frontend320", BigInteger.ONE, game.pid(),
                new FrontendFrame.Menu(BigInteger.ONE), f.source, f.source);
        var expected = new FrontendExpectedPostcondition(identity, command.source(), "frontend320/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("ready"), true)));
        var frontend = new ActionCommand("frontend320", new CommandOrigin.Frontend(identity), command.source(), "frontend320",
                command.operation(), command.arguments(), new CommandExpectation.Frontend(expected), command.claims(), command.deadline());
        byte[] raw = ActionCodec.encodeCommand(frontend);
        f.writer.locked(session -> f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
            assertEquals(frontend, bound.decodeCanonicalCommand(raw));
            assertNotSame(bound.decodeCanonicalCommand(raw), bound.decodeCanonicalCommand(raw));
            return null;
        }));
    }
}
