package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.StrictJson;

/** Regression for parsed DATA retention in historical reads, ensuring physical validation remains strict. */
final class WriterHistoricalParsedDataRetentionTest {
    @TempDir Path directory;

    private WriterFixture createFixture(String name) throws IOException {
        return new WriterFixture(directory.resolve(name));
    }

    @Test void repeatedHistoricalReadsReturnDetachedImmutableData() throws Exception {
        WriterFixture fixture = createFixture("detached-data");
        fixture.writer.locked(same -> {
            Head anchor = same.head();
            String anchorDigest = anchor.digest();
            ContinuityState anchorData = same.requireHistoricalCanonicalState(anchor.state().sequence(), anchorDigest);
            anchorData.toJson().put("sequence", 999);
            byte[] anchorBytes = anchorData.canonicalBytes(); anchorBytes[0] ^= 1;
            assertEquals(anchorDigest, ContinuityJson.digest(same.requireHistoricalCanonicalState(anchor.state().sequence(), anchorDigest).toJson()));
            // Commit two events to establish history
            Receipt firstReceipt = same.commit(same.preview(WriterFixture.settled("event-1", 1024, 2)));
            Receipt secondReceipt = same.commit(same.preview(WriterFixture.settled("event-2", 1048, 3)));

            // Capture digests from actual receipts BEFORE later commits
            String digest1 = ContinuityJson.digest(firstReceipt.head().toJson());
            String digest2 = ContinuityJson.digest(secondReceipt.head().toJson());

            // First read of historical state at sequence 1
            ContinuityState first = same.requireHistoricalCanonicalState(1, digest1);
            assertEquals(1, first.sequence());
            assertEquals(digest1, ContinuityJson.digest(first.toJson()));

            first.toJson().put("sequence", 999);
            // Mutate the returned object's canonical bytes (detached clone)
            byte[] bytes = first.canonicalBytes();
            bytes[0] = (byte)(bytes[0] ^ 0xFF);

            // Second read of historical state at sequence 1
            ContinuityState second = same.requireHistoricalCanonicalState(1, digest1);
            assertEquals(1, second.sequence());
            assertEquals(digest1, ContinuityJson.digest(second.toJson()));

            // Verify that mutating the first object's canonical bytes didn't affect the second
            assertEquals(ContinuityJson.digest(first.toJson()), ContinuityJson.digest(second.toJson()));

            // Verify current head is still correct
            Head current = same.head();
            assertEquals(2, current.state().sequence());
            assertEquals(digest2, ContinuityJson.digest(current.state().toJson()));
            return null;
        });
    }

    @Test void historicalReadRejectsChangedFileContent() throws Exception {
        WriterFixture fixture = createFixture("reject-content-change");
        fixture.writer.locked(same -> {
            Receipt receipt = same.commit(same.preview(WriterFixture.settled("event-1", 1024, 2)));
            String digest = ContinuityJson.digest(receipt.head().toJson());

            // Read historical state successfully
            same.requireHistoricalCanonicalState(1, digest);

            // Mutate the event file content on disk
            Path eventPath = fixture.layout.event(1);
            byte[] original = Files.readAllBytes(eventPath);
            byte[] mutated = original.clone();
            mutated[0] = (byte)(mutated[0] ^ 0xFF);
            Files.write(eventPath, mutated);

            // Attempt to read again - should fail due to content/identity mismatch
            assertThrows(IOException.class, () -> same.requireHistoricalCanonicalState(1, digest));
            return null;
        });
    }

    @Test void historicalReadRejectsEqualByteEventReplacement() throws Exception {
        WriterFixture fixture = createFixture("reject-equal-byte-replacement");
        fixture.writer.locked(same -> {
            Receipt receipt = same.commit(same.preview(WriterFixture.settled("event-1", 1024, 2)));
            String digest = ContinuityJson.digest(receipt.head().toJson());

            // Read historical state successfully
            same.requireHistoricalCanonicalState(1, digest);

            // Replace the event file with a new file having same content but different native identity
            Path eventPath = fixture.layout.event(1);
            Path tempPath = eventPath.resolveSibling("temp-replacement.json");
            Files.copy(eventPath, tempPath, StandardCopyOption.REPLACE_EXISTING);
            Files.move(tempPath, eventPath, StandardCopyOption.REPLACE_EXISTING);

            // Attempt to read again - should fail due to native identity drift
            assertThrows(IOException.class, () -> same.requireHistoricalCanonicalState(1, digest));
            return null;
        });
    }

    @Test void historicalReadRejectsEqualByteAnchorReplacement() throws Exception {
        WriterFixture fixture = createFixture("reject-anchor-replacement");
        fixture.writer.locked(same -> {
            Receipt receipt = same.commit(same.preview(WriterFixture.settled("event-1", 1024, 2)));
            String digest = ContinuityJson.digest(receipt.head().toJson());

            // Read historical state successfully
            same.requireHistoricalCanonicalState(1, digest);

            // Replace the anchor file with equal bytes but different native identity
            Path anchorPath = Path.of(fixture.layout.anchor().path());
            Path tempPath = anchorPath.resolveSibling("temp-anchor.json");
            Files.copy(anchorPath, tempPath, StandardCopyOption.REPLACE_EXISTING);
            Files.move(tempPath, anchorPath, StandardCopyOption.REPLACE_EXISTING);

            // Attempt to read again - should fail due to anchor identity drift
            assertThrows(IOException.class, () -> same.requireHistoricalCanonicalState(1, digest));
            return null;
        });
    }

    @Test void commitAfterHistoricalReadMaintainsCorrectAncestry() throws Exception {
        WriterFixture fixture = createFixture("commit-after-read");
        fixture.writer.locked(same -> {
            // Commit first event
            Receipt first = same.commit(same.preview(WriterFixture.settled("event-1", 1024, 2)));
            String firstDigest = ContinuityJson.digest(first.head().toJson());

            // Read historical state at sequence 1
            ContinuityState historical = same.requireHistoricalCanonicalState(1, firstDigest);
            assertEquals(1, historical.sequence());

            // Commit second event
            Receipt second = same.commit(same.preview(WriterFixture.settled("event-2", 1048, 3)));
            assertEquals(2, second.head().sequence());

            // Verify current head is correct
            Head current = same.head();
            assertEquals(2, current.state().sequence());

            // Verify older ancestry is still readable and correct
            ContinuityState old = same.requireHistoricalCanonicalState(1, firstDigest);
            assertEquals(1, old.sequence());
            assertEquals(firstDigest, ContinuityJson.digest(old.toJson()));

            // Verify wrong digest is rejected
            assertThrows(IllegalArgumentException.class, () -> same.requireHistoricalCanonicalState(1, "0".repeat(64)));

            // Verify future sequence is rejected
            assertThrows(IllegalArgumentException.class, () -> same.requireHistoricalCanonicalState(3, firstDigest));
            return null;
        });
    }

    @Test void activeForeignWriterRejection() throws Exception {
        WriterFixture fixture1 = createFixture("foreign-writer-1");
        WriterFixture fixture2 = createFixture("foreign-writer-2");

        fixture1.writer.locked(same -> {
            // Try to use session1 with writer2's requireSession - should fail
            assertThrows(IOException.class, () -> fixture2.writer.requireSession(same));
            return null;
        });
    }

    @Test void activeWrongThreadRejection() throws Exception {
        WriterFixture fixture = createFixture("wrong-thread");
        AtomicReference<Throwable> capturedError = new AtomicReference<>();
        fixture.writer.locked(same -> {
            String digest = same.head().digest();
            Thread thread = new Thread(() -> {
                try { same.requireHistoricalCanonicalState(0, digest); }
                catch (Throwable failure) { capturedError.set(failure); }
            }, "foreign-historical-reader");
            thread.setDaemon(true); thread.start();
            try { thread.join(5000); }
            catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt(); throw new IOException(interrupted);
            }
            assertFalse(thread.isAlive(), "foreign-thread query must terminate within the actual held scope");
            assertInstanceOf(IllegalArgumentException.class, capturedError.get());
            assertEquals(0, same.requireHistoricalCanonicalState(0, digest).sequence());
            return null;
        });
    }

    @Test void escapedSessionRejection() throws Exception {
        WriterFixture fixture = createFixture("escaped-session");
        AtomicReference<ContinuityStorePort.Session> capturedSession = new AtomicReference<>();

        fixture.writer.locked(same -> {
            capturedSession.set(same);
            return null;
        });

        // Session is now escaped (locked block finished)
        assertThrows(RuntimeException.class, () -> capturedSession.get().requireWriter(fixture.layout.lock()));
    }

    @Test void freshSessionRejectsChangedCanonicalOriginalFromEarlierSession() throws Exception {
        WriterFixture fixture = createFixture("cross-session-tamper");
        String digest = fixture.writer.locked(same -> {
            Receipt receipt = same.commit(same.preview(WriterFixture.settled("event-1", 1024, 2)));
            String value = ContinuityJson.digest(receipt.head().toJson());
            same.requireHistoricalCanonicalState(1, value); return value;
        });
        Path event = fixture.layout.event(1);
        Path replacement = event.resolveSibling("new-session-replacement.json");
        Files.copy(event, replacement); Files.move(replacement, event, StandardCopyOption.REPLACE_EXISTING);
        assertThrows(IOException.class, () -> fixture.writer.locked(same -> same.requireHistoricalCanonicalState(1, digest)));
        assertFalse(Files.exists(fixture.layout.event(2)));
    }
}