package org.xar.ck3.control.continuity.writer.publicscope;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.FreshContinuityGenesis;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.ImmutableArtifactStore;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.continuity.writer.StorageWriteGuard;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

/**
 * Public API control-flow cases using actual readonly writers and real locked Sessions.
 * Zero CAS entries: no retention-budget, physical close-count, fallback-payload or live authority claim.
 */
public final class BorrowedHistoricalReadPublicTest {
    private static final String MACHINE = "borrowed-scope-software-test";
    private static final ActionPorts.HistoricalReadLimits OUTER =
            new ActionPorts.HistoricalReadLimits(2, 65_536L, 8);
    private static final ActionPorts.HistoricalReadLimits OWN =
            new ActionPorts.HistoricalReadLimits(1, 1L, 4);

    @TempDir Path temporary;
    private final List<StorageWriteGuard> guards = new ArrayList<>();

    @AfterEach void closeOwnedGuards() throws IOException {
        for (int index = guards.size() - 1; index >= 0; index--) {
            guards.get(index).close();
        }
        guards.clear();
    }

    @Test void borrowingDoesNotRetireOuterScope() throws IOException {
        NativeOutcomeArchive owner = existingReadonlyArchive("borrow");
        owner.writer().locked(session -> {
            assertEquals(0L, session.head().state().sequence());
            AtomicBoolean outerEntered = new AtomicBoolean();
            AtomicInteger borrowedEntries = new AtomicInteger();
            AtomicInteger strictEntries = new AtomicInteger();
            assertThrows(IOException.class, () -> owner.inHistoricalReadScope(session, OUTER, outer -> {
                outerEntered.set(true);
                String result = owner.inHistoricalReadScopeOrBorrow(session, OWN, borrowed -> {
                    borrowedEntries.incrementAndGet();
                    return "borrowed-result";
                });
                assertEquals("borrowed-result", result);
                // A completed borrow must leave the strict outer scope attached.
                // This intentional strict probe poisons it, even though rejection is caught here.
                assertThrows(IOException.class, () -> owner.inHistoricalReadScope(session, OWN, nested -> {
                    strictEntries.incrementAndGet();
                    return "forbidden-nested";
                }));
                return "caught-rejection";
            }));
            assertEquals(true, outerEntered.get());
            assertEquals(1, borrowedEntries.get());
            assertEquals(0, strictEntries.get());
            assertEquals("fresh-after-outer", owner.inHistoricalReadScopeOrBorrow(
                    session, OWN, fresh -> "fresh-after-outer"));
            return null;
        });
    }

    @Test void freshOwnerScopeRestoresAfterNormalAndExceptionalExit() throws IOException {
        NativeOutcomeArchive owner = existingReadonlyArchive("fresh");
        owner.writer().locked(session -> {
            assertEquals(0L, session.head().state().sequence());
            assertEquals("normal", owner.inHistoricalReadScopeOrBorrow(session, OWN, fresh -> "normal"));
            for (Throwable original : callbackFailures()) {
                Throwable escaped = assertThrows(original.getClass(),
                        () -> owner.inHistoricalReadScopeOrBorrow(session, OWN, fresh -> {
                            throwOriginal(original);
                            return null;
                        }));
                assertSame(original, escaped);
                assertEquals("fresh-after-failure", owner.inHistoricalReadScopeOrBorrow(
                        session, OWN, fresh -> "fresh-after-failure"));
            }
            return null;
        });
    }

    @Test void caughtBorrowFailuresAndForeignOwnerRemainFatalToOuter() throws IOException {
        NativeOutcomeArchive owner = existingReadonlyArchive("poison");
        NativeOutcomeArchive foreignOwner = new NativeOutcomeArchive(owner.artifactStore(), owner.writer());
        owner.writer().locked(session -> {
            assertEquals(0L, session.head().state().sequence());
            for (Throwable original : callbackFailures()) {
                AtomicBoolean laterEntered = new AtomicBoolean();
                assertThrows(IOException.class, () -> owner.inHistoricalReadScope(session, OUTER, outer -> {
                    Throwable caught = assertThrows(original.getClass(),
                            () -> owner.inHistoricalReadScopeOrBorrow(session, OWN, borrowed -> {
                                throwOriginal(original);
                                return null;
                            }));
                    assertSame(original, caught);
                    assertThrows(IOException.class,
                            () -> owner.inHistoricalReadScopeOrBorrow(session, OWN, later -> {
                                laterEntered.set(true);
                                return "must-not-run";
                            }));
                    assertFalse(laterEntered.get());
                    return "caught-borrow-failure";
                }));
                assertFalse(laterEntered.get());
                assertEquals("fresh", owner.inHistoricalReadScopeOrBorrow(session, OWN, fresh -> "fresh"));
            }

            AtomicBoolean foreignEntered = new AtomicBoolean();
            assertThrows(IOException.class, () -> owner.inHistoricalReadScope(session, OUTER, outer -> {
                assertThrows(IOException.class,
                        () -> foreignOwner.inHistoricalReadScopeOrBorrow(session, OWN, foreign -> {
                            foreignEntered.set(true);
                            return "must-not-run";
                        }));
                assertFalse(foreignEntered.get());
                return "caught-foreign-rejection";
            }));
            assertFalse(foreignEntered.get());
            assertEquals("fresh", owner.inHistoricalReadScopeOrBorrow(session, OWN, fresh -> "fresh"));
            return null;
        });
    }

    private NativeOutcomeArchive existingReadonlyArchive(String name) throws IOException {
        Path root = Files.createDirectory(temporary.resolve(name)).toAbsolutePath().normalize();
        Path requestPath = root.resolve("genesis-request.json");
        FreshContinuityGenesis.Plan plan = new FreshContinuityGenesis.Plan(MACHINE, 1L, 1L);
        byte[] request = FreshContinuityGenesis.encode(plan);
        writeNew(requestPath, request);
        ExactRef requestRef = reference(requestPath, request);
        byte[] state = FreshContinuityGenesis.initial(plan, requestRef).canonicalBytes();

        Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json");
        Path anchor = root.resolve("anchor.json");
        writeNew(snapshot, state);
        writeNew(anchor, state);
        Path lock = root.resolve("ROOT-CONTINUITY-WINDOW.lock");
        writeNew(lock, new byte[0]);
        Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        Path artifacts = Files.createDirectory(root.resolve("artifacts"));
        Path source = root.resolve("fixture-source.txt");
        byte[] sourceBytes = "finite readonly public Session fixture".getBytes(StandardCharsets.UTF_8);
        writeNew(source, sourceBytes);

        WriterContracts.Layout layout = new WriterContracts.Layout(snapshot, reference(anchor, state), MACHINE);
        StorageWriteGuard guard = StorageWriteGuard.noWrites();
        guards.add(guard);
        ImmutableArtifactStore store = ImmutableArtifactStore.readOnlyExisting(
                new ImmutableArtifactStore.Config(artifacts, layout.lock(), 1_048_576L), guard);
        WriterContracts.TransitionAuthority unusedAuthority = new WriterContracts.TransitionAuthority() {
            @Override public String revalidate(ContinuityState before, WriterContracts.Request request)
                    throws IOException {
                throw new IOException("readonly scope test must not revalidate a write");
            }
            @Override public ContinuityState reduce(ContinuityState before, WriterContracts.Request request)
                    throws IOException {
                throw new IOException("readonly scope test must not reduce a write");
            }
        };
        ContinuityWriter writer = ContinuityWriter.readOnlyExisting(
                layout, List.of(reference(source, sourceBytes)), unusedAuthority,
                Clock.fixed(Instant.parse("2026-01-02T03:04:05Z"), ZoneOffset.UTC),
                new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), guard);
        return new NativeOutcomeArchive(store, writer);
    }

    private static void writeNew(Path path, byte[] bytes) throws IOException {
        Files.write(path, bytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
    }

    private static ExactRef reference(Path path, byte[] original) throws IOException {
        try {
            String sha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original));
            return new ExactRef(path.toAbsolutePath().normalize().toString(), original.length, sha);
        } catch (NoSuchAlgorithmException unavailable) {
            throw new IOException("SHA-256 is unavailable", unavailable);
        }
    }

    private static List<Throwable> callbackFailures() {
        return List.of(new IOException("checked callback failure"),
                new IllegalStateException("unchecked callback failure"),
                new AssertionError("error callback failure"));
    }

    private static void throwOriginal(Throwable original) throws IOException {
        if (original instanceof IOException checked) throw checked;
        if (original instanceof RuntimeException unchecked) throw unchecked;
        if (original instanceof Error error) throw error;
        throw new AssertionError("unexpected Test failure type", original);
    }
}
