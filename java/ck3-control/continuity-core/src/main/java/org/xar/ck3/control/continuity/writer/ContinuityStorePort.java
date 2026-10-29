package org.xar.ck3.control.continuity.writer;

import java.io.IOException;
import java.nio.file.Path;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.ContinuityState;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Pure storage boundary shared by the application; only the storage adapter owns physical writes. */
public interface ContinuityStorePort {
    Prepared preview(Request request) throws IOException;
    Receipt commit(Prepared prepared) throws IOException;
    ExactRef persistedHead() throws IOException;
    <T> T locked(SessionWork<T> work) throws IOException;
    /** The actual writer instance must validate the borrowed scope; old adapters cannot imply trust. */
    default void requireSession(Session borrowed) throws IOException {
        throw new IOException("actual original writer session authority is not installed");
    }
    @FunctionalInterface interface SessionWork<T> { T run(Session session) throws IOException; }
    interface Session {
        /** No Game command is sent here; the installed private authority must revalidate actual custody. */
        default org.xar.ck3.control.continuity.EpisodeWindow.CommittedBegin beginEpisodeWindow(org.xar.ck3.control.continuity.EpisodeWindow.Begin begin) throws IOException {
            throw new IOException("actual versioned episode BEGIN writer is not installed");
        }
        /** Commits the already verified first pair; never submits another SAVE or fabricates a cycle. */
        default org.xar.ck3.control.continuity.EpisodeWindow.CommittedBaseline baselineEpisodeWindow(org.xar.ck3.control.continuity.EpisodeWindow.Baseline baseline) throws IOException {
            throw new IOException("actual first SAVE BASELINE writer is not installed");
        }
        /** Read-only ancestry permits this same BEGIN's ACTIVE descendants, never another BEGIN. */
        default void requireEpisodeWindowBegin(org.xar.ck3.control.continuity.EpisodeWindow.CommittedBegin begin) throws IOException {
            throw new IOException("actual canonical episode BEGIN ancestry verifier is not installed");
        }
        /** Read-only full BEGIN/first-SAVE/BASELINE ancestry in this current ACTIVE window. */
        default void requireEpisodeWindowActive(org.xar.ck3.control.continuity.EpisodeWindow.CommittedBaseline baseline) throws IOException {
            throw new IOException("actual canonical episode BASELINE ancestry verifier is not installed");
        }
        /** Historical knowledge only: verifies an older exact BASELINE without granting current-window eligibility. */
        default void requireHistoricalEpisodeWindowBaseline(org.xar.ck3.control.continuity.EpisodeWindow.CommittedBaseline baseline) throws IOException {
            throw new IOException("actual historical episode BASELINE verifier is not installed");
        }
        /** Borrowed scope: every implementation must reject another writer, another thread and escaped sessions. */
        void requireWriter(Path originalWriterLock) throws IOException;
        /** Actual configured writer sources only; no write or current domain permission. */
        default java.util.List<Pin> captureSources() throws IOException {
            throw new IOException("actual configured writer source reader is not installed");
        }
        /** Exact actual canonical event edge DATA; never manufactures Request/Prepared/evidence. */
        default HistoricalTransition readHistoricalTransition(Pin actualEvent) throws IOException {
            throw new IOException("actual canonical transition reader is not installed");
        }
        /** Ordered finite event-edge DATA; the storage adapter may share one verified head across the batch. */
        default java.util.List<HistoricalTransition> readHistoricalTransitions(java.util.List<Pin> actualEvents) throws IOException {
            actualEvents=java.util.List.copyOf(java.util.Objects.requireNonNull(actualEvents));
            org.xar.ck3.control.contracts.StrictJson.require(!actualEvents.isEmpty()
                    &&actualEvents.size()<=org.xar.ck3.control.continuity.ContinuityHistory.MAX_CONTINUITY_EVENTS,
                    "finite actual canonical event batch required");
            java.util.List<HistoricalTransition> results = new java.util.ArrayList<>();
            for (Pin pin : actualEvents) {
                results.add(readHistoricalTransition(pin));
            }
            return java.util.List.copyOf(results);
        }
        Pin capturePin(ExactRef reference, int maximumBytes) throws IOException;
        void verifyPin(Pin pin) throws IOException;
        /** Strict optional capability: old adapters are unavailable rather than implicitly trusted. */
        default byte[] readPinned(Pin pin, int maximumBytes) throws IOException {
            throw new IOException("actual pinned original document reader is not installed");
        }
        /** Read-only canonical-history verification; never submits, recovers or writes a ledger. */
        default void requireCommitted(Prepared original, Receipt receipt) throws IOException {
            throw new IOException("actual committed canonical-history verifier is not installed");
        }
        /** Exact registered DOMAIN_IMPORT history; a PreparedImport is not a generic transition ticket. */
        default void requireCommitted(DomainBodies.PreparedImport original, Receipt receipt) throws IOException {
            throw new IOException("actual committed domain-import history verifier is not installed");
        }
        /** Read-only known result lookup; an absent event never grants retry permission. */
        default java.util.Optional<Receipt> queryCommitted(Prepared original) throws IOException {
            throw new IOException("actual committed canonical-history reader is not installed");
        }
        /** Read-only actual canonical ancestry; a caller-provided digest is not its own proof. */
        default ContinuityState requireHistoricalState(long sequence, String expectedDigest) throws IOException {
            throw new IOException("actual canonical historical-state verifier is not installed");
        }
        /** Read-only ancestor state with its real captured canonical/source/material pins; never a current write permit. */
        default Head requireHistoricalHead(long sequence,String expectedDigest) throws IOException {
            throw new IOException("actual canonical historical-head verifier is not installed");
        }
        /** Read-only historical edge, not a reconstructed warm preparation or current source permission. */
        default DomainBodies.RecordedImport requireHistoricalImport(DomainBodies.Slot slot,long committedSequence,String exactAfterDigest) throws IOException {
            throw new IOException("actual recorded domain-import history reader is not installed");
        }
        /** Only actual canonical DOMAIN_IMPORT reducer edges may continue this exact original attachment point. */
        default void requireDomainImportContinuation(long originalSequence,String originalDigest) throws IOException {
            throw new IOException("actual domain-import-only historical continuation verifier is not installed");
        }
        Head head() throws IOException;
        Prepared preview(Request request) throws IOException;
        Receipt commit(Prepared prepared) throws IOException;
        ExactRef persistedHead() throws IOException;
        default DomainBodies.Read readDomain(DomainBodies.Slot slot) throws IOException {
            return new DomainBodies.Unavailable(DomainBodies.Reason.SLOT_UNREGISTERED, java.util.Optional.of(persistedHead()), "domain reader not installed");
        }
        default DomainBodies.PreparedImport previewImport(DomainBodies.ImportRequest request) throws IOException {
            throw new IOException("canonical domain import not installed");
        }
        default Receipt commitImport(DomainBodies.PreparedImport prepared) throws IOException {
            throw new IOException("canonical domain import not installed");
        }
    }
}

