package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.List;
import java.util.OptionalLong;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;

/** Actual physical commits and durable proofs, with observation at the original storage callback return. */
final class WriterCommitReadbackRetentionTest {
    @TempDir Path directory;

    @Test void completedReadbackSurvivesCommitReturnButFailureAndChangedDataDoNotBorrowIt() throws Exception {
        WriterFixture fixture = new WriterFixture(directory.resolve("actual-commits"));
        StorageWriteGuard delegate = StorageWriteGuardTestSupport.forLayout(fixture.layout);
        var held = new AtomicReference<ContinuityStorePort.Session>();
        var insideReturn = new AtomicReference<Head>();
        var failAfterReadback = new AtomicBoolean();
        StorageWriteGuard observed = new StorageWriteGuard() {
            @Override public void close() throws IOException { delegate.close(); }
            @Override public void requireInitialization(Path lock, List<Path> roots) throws IOException {
                delegate.requireInitialization(lock, roots);
            }
            @Override public OptionalLong enforcedAggregateMaximumBytes(Path lock, Path root) throws IOException {
                return delegate.enforcedAggregateMaximumBytes(lock, root);
            }
            @Override public <T> T write(WritePlan plan, PhysicalWrite<T> io) throws IOException {
                T actual = delegate.write(plan, io);
                if (actual instanceof Receipt receipt && receipt.disposition() == Disposition.COMMITTED) {
                    insideReturn.set(held.get().head());
                    if (failAfterReadback.getAndSet(false)) throw new AssertionError("actual storage return failed");
                }
                return actual;
            }
        };
        var writer = new ContinuityWriter(fixture.layout,
                List.of(LedgerFiles.read(fixture.source, 65536).pin().reference()), new TransitionAuthority() {
            @Override public String revalidate(ContinuityState before, Request request) {
                return ContinuityJson.digest(request.detailsObject());
            }
            @Override public ContinuityState reduce(ContinuityState before, Request request) {
                return OriginalWindowReducer.reduce(before, request);
            }
        }, observed);
        writer.locked(same -> {
            held.set(same);
            Prepared first = same.preview(WriterFixture.settled("readback-first", 1024, 2));
            Receipt firstReceipt = same.commit(first);
            Head firstReadback = insideReturn.get();
            assertSame(firstReadback, same.head(), "do not re-project the just-validated complete commit head");
            same.requireCommitted(first, firstReceipt);
            assertSame(firstReadback, same.head());

            Prepared next = same.preview(WriterFixture.settled("readback-next", 1048, 3));
            Receipt nextReceipt = same.commit(next);
            Head nextReadback = insideReturn.get();
            assertNotSame(firstReadback, nextReadback);
            assertSame(nextReadback, same.head());
            assertEquals(2, same.head().state().sequence());
            same.requireCommitted(first, firstReceipt);
            same.requireCommitted(next, nextReceipt);

            Prepared uncertain = same.preview(WriterFixture.settled("readback-uncertain", 1072, 4));
            failAfterReadback.set(true);
            assertThrows(AssertionError.class, () -> same.commit(uncertain));
            Head failedReturn = insideReturn.get();
            assertNotSame(failedReturn, same.head(), "a failed storage return discards its retained head");
            Receipt durable = same.queryCommitted(uncertain).orElseThrow();
            assertEquals(Disposition.ALREADY_COMMITTED, durable.disposition());
            assertEquals(0, durable.writes());
            assertEquals(3, durable.head().sequence());
            assertFalse(Files.exists(fixture.layout.event(4)));

            Path original = fixture.layout.event(1);
            Path replacement = original.resolveSibling("equal-byte-replacement.json");
            Files.write(replacement, Files.readAllBytes(original));
            Files.move(replacement, original, StandardCopyOption.REPLACE_EXISTING);
            assertThrows(IOException.class, () -> same.requireCommitted(first, firstReceipt));
            assertFalse(Files.exists(fixture.layout.event(4)));
            return null;
        });
    }
}
