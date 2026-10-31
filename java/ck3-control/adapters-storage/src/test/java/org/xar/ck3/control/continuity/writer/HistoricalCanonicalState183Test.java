package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.sun.jna.Platform;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class HistoricalCanonicalState183Test {
    @TempDir Path root;

    private static List<ExactRef> sources(WriterFixture fixture) throws IOException {
        return List.of(LedgerFiles.read(fixture.source, 65_536).pin().reference());
    }

    @Test void crossSessionCachedCanonicalProofRejectsCorruptedEvent1() throws Exception {
        assertTrue(Platform.isWindows());
        WriterFixture fixture = new WriterFixture(root.resolve("cross-session-cache"));

        // Setup: Two real commits
        Prepared first = fixture.writer.preview(WriterFixture.settled("first", 1024, 2));
        Receipt firstReceipt = fixture.writer.commit(first);
        Prepared second = fixture.writer.preview(WriterFixture.settled("second", 1048, 3));
        Receipt secondReceipt = fixture.writer.commit(second);
        byte[] beforeSnapshot = Files.readAllBytes(fixture.layout.snapshot());

        // Prime cache in Session 1
        fixture.writer.locked(session -> {
            // Verify genesis (sequence 0) twice to populate cache
            ContinuityState genesis = session.requireHistoricalCanonicalState(0, ContinuityJson.digest(WriterFixture.state()));
            assertNotNull(genesis);
            session.requireHistoricalCanonicalState(0, ContinuityJson.digest(WriterFixture.state()));
            return null;
        });

        // Corrupt event 1 file bytes (not snapshot, not anchor)
        Path event1 = fixture.layout.event(1);
        byte[] originalEvent1 = Files.readAllBytes(event1);
        byte[] corruptedEvent1 = originalEvent1.clone();
        // Flip a byte in the JSON content to ensure it's different but still valid JSON structure if possible,
        // or just change bytes to make it invalid/different. The test requires it to be "actual file corruption".
        // We change the 'details' or 'after' state slightly to break the chain verification.
        // Simplest: change a byte in the middle.
        corruptedEvent1[corruptedEvent1.length / 2] = (byte) (corruptedEvent1[corruptedEvent1.length / 2] ^ 0xFF);
        Files.write(event1, corruptedEvent1);

        // Open NEW Session on SAME writer (cache outlives Session)
        fixture.writer.locked(session -> {
            // This MUST throw IOException because it verifies ALL actual.documents (including event1)
            // even though we are asking for sequence 0 (genesis).
            assertThrows(IOException.class, () -> {
                session.requireHistoricalCanonicalState(0, ContinuityJson.digest(WriterFixture.state()));
            });
            return null;
        });

        // Prove snapshot bytes unchanged and no new event3
        assertArrayEquals(beforeSnapshot, Files.readAllBytes(fixture.layout.snapshot()));
        assertFalse(Files.exists(fixture.layout.event(3)));
    }

    @Test void exactAncestryAndNoUnrelatedMaterialization() throws Exception {
        assertTrue(Platform.isWindows());

        // Part 1: Source Drift
        WriterFixture sourceFixture = new WriterFixture(root.resolve("source-drift"));
        Prepared p1 = sourceFixture.writer.preview(WriterFixture.settled("s1", 1024, 2));
        Receipt r1 = sourceFixture.writer.commit(p1);

        // Get valid digest for sequence 0 (genesis)
        String validDigest0 = ContinuityJson.digest(WriterFixture.state());

        final String currentDigest = ContinuityJson.digest(r1.head().toJson());
        final String changedDigest = (currentDigest.charAt(0) == '0' ? "1" : "0") + currentDigest.substring(1);
        sourceFixture.writer.locked(session -> {
            assertEquals(0L, session.requireHistoricalCanonicalState(0, validDigest0).sequence());
            assertEquals(r1.head().toJson(), session.requireHistoricalCanonicalState(r1.head().sequence(), currentDigest).toJson());
            assertThrows(ContractViolationException.class, () -> session.requireHistoricalCanonicalState(r1.head().sequence() + 1, currentDigest));
            assertThrows(ContractViolationException.class, () -> session.requireHistoricalCanonicalState(r1.head().sequence(), changedDigest));
            assertEquals(r1.head().toJson(), session.requireHistoricalCanonicalState(r1.head().sequence(), currentDigest).toJson());
            return null;
        });

        // Change source file content (drift)
        Files.writeString(sourceFixture.source, "changed actual source");

        sourceFixture.writer.locked(session -> {
            // requireHistoricalCanonicalState should succeed despite source drift
            ContinuityState state0 = session.requireHistoricalCanonicalState(0, validDigest0);
            assertNotNull(state0);
            assertEquals(0L, state0.sequence());

            // requireHistoricalHead should fail due to source drift
            assertThrows(IOException.class, () -> {
                session.requireHistoricalHead(0, validDigest0);
            });
            assertEquals(0L, session.requireHistoricalCanonicalState(0, validDigest0).sequence());
            return null;
        });

        // Part 2: Domain Payload Drift
        WriterFixture domainFixture = new WriterFixture(root.resolve("domain-drift"));
        Path archiveRoot = domainFixture.layout.snapshot().getParent().resolve("archive");
        Files.createDirectory(archiveRoot);
        var artifacts = new ImmutableArtifactStore(
            new ImmutableArtifactStore.Config(archiveRoot, domainFixture.layout.lock(), 4_194_304),
            StorageWriteGuardTestSupport.forOriginalLock(domainFixture.layout.lock())
        );

        List<ExactRef> domSources = sources(domainFixture);
        var registration = new DomainBodies.Registration(
            DomainBodies.Slot.OPENING_GATE,
            "fixture.domain/v1",
            65_536,
            domSources,
            (head, previous, request, body) -> LedgerFiles.sha(body)
        );

        TransitionAuthority unused = new TransitionAuthority() {
            @Override public String revalidate(ContinuityState state, Request request) { throw new AssertionError("domain read cannot call ordinary authority"); }
            @Override public ContinuityState reduce(ContinuityState state, Request request) { throw new AssertionError("domain read cannot replay ordinary authority"); }
        };

        ContinuityWriter writer = new ContinuityWriter(
            domainFixture.layout,
            domSources,
            unused,
            Clock.systemUTC(),
            new ContinuityWriter.Extensions(List.of(registration), Optional.of(artifacts), Optional.empty()),
            StorageWriteGuardTestSupport.forLayout(domainFixture.layout)
        );

        // Import domain
        var row = StrictJson.object();
        row.put("schema", "fixture.domain/v1");
        row.put("ordinal", 1);
        byte[] raw = ContinuityJson.canonical(row);
        Path bodyPath = domainFixture.layout.snapshot().resolveSibling("original-domain-body.json");
        Files.write(bodyPath, raw);

        var input = new DomainBodies.ImportRequest(
            DomainBodies.Slot.OPENING_GATE,
            "fixture.domain/v1",
            LedgerFiles.read(bodyPath, 65_536).pin().reference(),
            raw,
            List.of(),
            "actual-domain"
        );

        Receipt committed = writer.commitImport(writer.previewImport(input));
        assertEquals(Disposition.COMMITTED, committed.disposition());

        // Get the actual payload path from the state
        ContinuityState current = committed.head();
        var bodyRef = DomainBodies.reference(current, DomainBodies.Slot.OPENING_GATE).orElseThrow();
        Path payloadPath = Path.of(bodyRef.payload().path());

        // Corrupt the payload file
        byte[] payloadBytes = Files.readAllBytes(payloadPath);
        payloadBytes[0] = (byte) (payloadBytes[0] ^ 0xFF);
        Files.write(payloadPath, payloadBytes);

        writer.locked(session -> {
            String validDigestCurrent = ContinuityJson.digest(current.toJson());
            long currentSequence = current.sequence();

            // requireHistoricalCanonicalState should succeed (ignores domain payload drift)
            ContinuityState stateCurrent = session.requireHistoricalCanonicalState(currentSequence, validDigestCurrent);
            assertNotNull(stateCurrent);
            assertEquals(currentSequence, stateCurrent.sequence());

            // requireHistoricalHead should fail (verifies domain payload)
            assertThrows(IOException.class, () -> {
                session.requireHistoricalHead(currentSequence, validDigestCurrent);
            });
            return null;
        });
    }

    @Test void oldAdapterDefaultFailclosed() throws Exception {
        assertTrue(Platform.isWindows());

        // Construct minimal anonymous Session implementing abstract methods
        ContinuityStorePort.Session oldAdapter = new ContinuityStorePort.Session() {
            @Override public void requireWriter(Path originalWriterLock) throws IOException { throw new AssertionError("unexpected"); }
            @Override public Pin capturePin(ExactRef reference, int maximumBytes) throws IOException { throw new AssertionError("unexpected"); }
            @Override public void verifyPin(Pin pin) throws IOException { throw new AssertionError("unexpected"); }
            @Override public Head head() throws IOException { throw new AssertionError("unexpected"); }
            @Override public Prepared preview(Request request) throws IOException { throw new AssertionError("unexpected"); }
            @Override public Receipt commit(Prepared prepared) throws IOException { throw new AssertionError("unexpected"); }
            @Override public ExactRef persistedHead() throws IOException { throw new AssertionError("unexpected"); }
        };

        String validDigest = "0".repeat(64);

        // requireHistoricalCanonicalState is a default method in the interface.
        // The default implementation throws IOException("actual canonical historical-state verifier is not installed").
        IOException failure = assertThrows(IOException.class, () -> {
            oldAdapter.requireHistoricalCanonicalState(0, validDigest);
        });

        assertTrue(failure.getMessage().contains("actual canonical historical-state verifier is not installed"));
    }
}
