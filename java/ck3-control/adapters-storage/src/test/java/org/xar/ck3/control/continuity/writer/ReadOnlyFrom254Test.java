package org.xar.ck3.control.continuity.writer;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** New owned-temp lock witnesses; owner reviewed production. No actual ledger or Game is used. */
final class ReadOnlyFrom254Test {
    @TempDir Path temp;
    private static final TransitionAuthority NEVER = new TransitionAuthority() {
        @Override public String revalidate(ContinuityState before, Request request) {
            throw new AssertionError("readonly source must not prepare a mutation");
        }
        @Override public ContinuityState reduce(ContinuityState before, Request request) {
            throw new AssertionError("readonly source must not reduce a mutation");
        }
    };
    private final class Pair implements AutoCloseable {
        final WriterFixture caller;
        final WriterFixture source;
        final StorageWriteGuard denial = StorageWriteGuard.noWrites();
        final ContinuityWriter reader;
        Pair(String name) throws IOException {
            caller = new WriterFixture(temp.resolve(name).resolve("new"), 1L << 20);
            source = new WriterFixture(temp.resolve(name).resolve("old"), 1L << 20);
            reader = reader(source, denial);
        }
        @Override public void close() throws IOException {
            denial.close(); source.storage.close(); caller.storage.close();
        }
    }
    private static ContinuityWriter reader(WriterFixture f, StorageWriteGuard guard) throws IOException {
        return ContinuityWriter.readOnlyExisting(f.layout,
                List.of(LedgerFiles.read(f.source, 65536).pin().reference()), NEVER,
                java.time.Clock.systemUTC(), ContinuityWriter.Extensions.none(), guard);
    }
    private static void outerRestored(Pair f, ContinuityStorePort.Session same, String digest) throws IOException {
        f.caller.writer.requireSession(same);
        assertSame(same, f.caller.writer.borrowedSession());
        same.requireWriter(f.caller.layout.lock());
        assertEquals(digest, same.head().digest());
    }
    private static ContinuityStorePort.Session foreignSession() {
        return new ContinuityStorePort.Session() {
            @Override public void requireWriter(Path path) { throw new AssertionError("foreign session invoked"); }
            @Override public Pin capturePin(ExactRef ref, int max) { throw new AssertionError("foreign session invoked"); }
            @Override public void verifyPin(Pin pin) { throw new AssertionError("foreign session invoked"); }
            @Override public Head head() { throw new AssertionError("foreign session invoked"); }
            @Override public Prepared preview(Request request) { throw new AssertionError("foreign session invoked"); }
            @Override public Receipt commit(Prepared prepared) { throw new AssertionError("foreign session invoked"); }
            @Override public ExactRef persistedHead() { throw new AssertionError("foreign session invoked"); }
        };
    }

    @Test void genuineOldHeadPinsAndIdentityAreReadAndOuterResumesAfterInnerCloses() throws Exception {
        try (Pair f = new Pair("success")) {
            String oldHead = f.reader.locked(same -> same.head().digest());
            f.caller.writer.locked(same -> {
                String before = same.head().digest();
                ContinuityStorePort.Session escaped = f.reader.readOnlyFrom(same, old -> {
                    f.reader.requireSession(old);
                    assertSame(old, f.reader.borrowedSession());
                    assertThrows(IOException.class, () -> f.caller.writer.requireSession(old));
                    assertThrows(IOException.class, f.caller.writer::borrowedSession);
                    assertThrows(ContractViolationException.class, same::head);
                    assertThrows(ContractViolationException.class,
                            () -> same.preview(WriterFixture.settled("suspended", 1024, 2)));
                    assertEquals(oldHead, old.head().digest());
                    Pin original = old.capturePin(LedgerFiles.read(f.source.source, 65536).pin().reference(), 65536);
                    old.verifyPin(original);
                    assertArrayEquals("reviewed fixture source v1".getBytes(StandardCharsets.UTF_8), old.readPinned(original, 65536));
                    assertThrows(IOException.class, () -> old.preview(WriterFixture.settled("denied", 1024, 2)));
                    assertThrows(IOException.class, () -> f.reader.locked(unused -> null));
                    assertThrows(IOException.class, () -> f.caller.writer.locked(unused -> null));
                    assertThrows(IOException.class, () -> f.reader.readOnlyFrom(old, unused -> null));
                    return old;
                });
                outerRestored(f, same, before);
                assertThrows(ContractViolationException.class, escaped::head);
                assertThrows(IOException.class, () -> f.reader.requireSession(same));
                return null;
            });
            assertEquals(oldHead, f.reader.locked(same -> same.head().digest()));
            assertTrue(f.caller.writer.activeSession().isEmpty());
            assertTrue(f.reader.activeSession().isEmpty());
        }
    }

    @Test void ioRuntimeAndErrorKeepTheirIdentityWhileBothRealLocksRemainReusable() throws Exception {
        try (Pair f = new Pair("exceptions")) {
            String oldDigest = f.reader.locked(ReadOnlyFrom254Test::sameDigest);
            f.caller.writer.locked(same -> {
                String before = same.head().digest();
                IOException io = new IOException("source callback io");
                assertSame(io, assertThrows(IOException.class, () -> f.reader.readOnlyFrom(same, old -> { throw io; })));
                outerRestored(f, same, before);
                IllegalStateException runtime = new IllegalStateException("source callback runtime");
                assertSame(runtime, assertThrows(IllegalStateException.class,
                        () -> f.reader.readOnlyFrom(same, old -> { throw runtime; })));
                outerRestored(f, same, before);
                AssertionError error = new AssertionError("source callback error");
                assertSame(error, assertThrows(AssertionError.class,
                        () -> f.reader.readOnlyFrom(same, old -> { throw error; })));
                outerRestored(f, same, before);
                assertEquals(oldDigest, f.reader.readOnlyFrom(same, ReadOnlyFrom254Test::sameDigest));
                return null;
            });
            f.reader.locked(same -> { same.head(); return null; });
            f.caller.writer.locked(same -> { same.head(); return null; });
        }
    }
    private static String sameDigest(ContinuityStorePort.Session same) throws IOException { return same.head().digest(); }

    @Test void absentStaleSameLayoutMutableAndReadonlyOuterRolesFailBeforeCallback() throws Exception {
        try (Pair f = new Pair("roles"); StorageWriteGuard otherDenial = StorageWriteGuard.noWrites()) {
            AtomicBoolean called = new AtomicBoolean();
            ContinuityStorePort.Session stale = f.caller.writer.locked(same -> same);
            assertThrows(IOException.class, () -> f.reader.readOnlyFrom(stale, old -> { called.set(true); return null; }));
            ContinuityWriter sameLayout = reader(f.caller, otherDenial);
            f.caller.writer.locked(same -> {
                String before = same.head().digest();
                assertThrows(IOException.class, () -> f.reader.readOnlyFrom(null, old -> { called.set(true); return null; }));
                assertThrows(IOException.class, () -> f.reader.readOnlyFrom(stale, old -> { called.set(true); return null; }));
                assertThrows(IOException.class, () -> f.reader.readOnlyFrom(foreignSession(), old -> { called.set(true); return null; }));
                assertThrows(IOException.class, () -> sameLayout.readOnlyFrom(same, old -> { called.set(true); return null; }));
                assertThrows(IOException.class, () -> f.caller.writer.readOnlyFrom(same, old -> { called.set(true); return null; }));
                outerRestored(f, same, before);
                return null;
            });
            f.reader.locked(old -> {
                assertThrows(IOException.class, () -> sameLayout.readOnlyFrom(old, unused -> { called.set(true); return null; }));
                return null;
            });
            f.denial.close();
            f.caller.writer.locked(same -> {
                String before = same.head().digest();
                assertThrows(IOException.class, () -> f.reader.readOnlyFrom(same, old -> { called.set(true); return null; }));
                outerRestored(f, same, before); return null;
            });
            assertFalse(called.get());
        }
    }

    @Test void restorationFailureIsSuppressedOnPrimaryAndClosingSourceCannotReturnSuccess() throws Exception {
        try (Pair f = new Pair("suppressed")) {
            f.caller.writer.locked(same -> {
                String before = same.head().digest(); IOException primary = new IOException("primary survives closed source");
                IOException actual = assertThrows(IOException.class, () -> f.reader.readOnlyFrom(same, old -> {
                    old.head(); f.denial.close(); throw primary;
                }));
                assertSame(primary, actual); assertEquals(1, actual.getSuppressed().length);
                assertInstanceOf(IOException.class, actual.getSuppressed()[0]);
                assertEquals("NoWrites role is closed", actual.getSuppressed()[0].getMessage());
                outerRestored(f, same, before); return null;
            });
        }
        try (Pair f = new Pair("close-return")) {
            f.caller.writer.locked(same -> {
                String before = same.head().digest();
                IOException actual = assertThrows(IOException.class, () -> f.reader.readOnlyFrom(same, old -> {
                    old.head(); f.denial.close(); return 1;
                }));
                assertEquals("NoWrites role is closed", actual.getMessage());
                outerRestored(f, same, before); return null;
            });
        }
    }
}
