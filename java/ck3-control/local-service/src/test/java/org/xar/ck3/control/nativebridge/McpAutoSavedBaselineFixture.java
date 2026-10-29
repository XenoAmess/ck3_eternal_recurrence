package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.application.session.SessionPorts.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.g2.common.G2Source;

/** Test-only access to the unchanged physical SAVE producer; no live ManagedGame or Root grant. */
public final class McpAutoSavedBaselineFixture implements AutoCloseable {
    private final CheckpointSourceCompositionTest.Fixture actual;
    private final CheckpointPair pair;
    private final AtomicInteger proofCalls=new AtomicInteger();
    private final BatchJournal batch;

    private McpAutoSavedBaselineFixture(CheckpointSourceCompositionTest.Fixture actual,CheckpointPair pair) {
        this.actual=actual;this.pair=pair;
        batch=new BatchJournal() {
            @Override public JournalCommit commit(JournalInput input)throws IOException {return actual.batch.commit(input);}
            @Override public Optional<CompletedCycleProof> cycleProof(SessionIdentity owner,SemanticEvidence semantic)throws IOException {
                proofCalls.incrementAndGet();return actual.batch.cycleProof(owner,semantic);
            }
            @Override public void retainCycle(SessionIdentity owner,ActionReceipt receipt)throws IOException {actual.batch.retainCycle(owner,receipt);}
            @Override public CompletedCycleProof settleCycle(SessionIdentity owner,ActionReceipt receipt,SemanticEvidence semantic)throws IOException {
                return actual.batch.settleCycle(owner,receipt,semantic);
            }
        };
    }
    public static McpAutoSavedBaselineFixture open(Path root)throws Exception {
        var pause=new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"),"game.command.pause-map",
                (command,attempt,dispatch)->new ActionPorts.Pending("software native ACK has no independent pause poststate",
                        List.of(attempt.guard().nativeEvidence())),()->{});
        // Bounded software composition time; the production frame lifetime and every guard remain authoritative.
        var actual=new CheckpointSourceCompositionTest.Fixture(root,false,Clock.systemUTC(),Optional.empty(),Optional.empty(),List.of(pause),java.time.Duration.ofMinutes(2));
        try {
            var result=actual.service.checkpoint(actual.request);
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,result,result::toString);
            assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,confirmed.action().outcome());
            assertEquals(0,actual.saveBoundary(confirmed.pair()).committedSavedDays());
            assertEquals(1,actual.actual.nativeActionWrites(),"one actual software SAVE establishes the paired baseline");
            return new McpAutoSavedBaselineFixture(actual,confirmed.pair());
        } catch(Exception|Error failure) {
            try {actual.close();}catch(IOException close){failure.addSuppressed(close);}throw failure;
        }
    }
    public SessionIdentity owner(){return actual.owner;}
    public G2Source source(){return actual.actual.observationSource();}
    public CheckpointPair pair(){return pair;}
    public CheckpointService checkpoints(){return actual.service;}
    public BatchJournal batchJournal(){return batch;}
    public NativeOutcomeArchive archive(){return actual.actual.archive;}
    public ActionCoordinatorPort actions(){return actual.actual.coordinator;}
    public int proofCalls(){return proofCalls.get();}
    public int nativeActionWrites(){return actual.actual.nativeActionWrites();}
    public CheckpointRequestFactory checkpointRequests() {
        return new CheckpointRequestFactory(Path.of(pair.save().reference().path()),
                deadline->{throw new AssertionError("AUTO must consume its existing pair, never start another SAVE");});
    }
    public Ready observe(SessionIdentity owner,Instant deadline)throws IOException,InterruptedException {
        assertEquals(actual.owner,owner);
        return assertInstanceOf(Ready.class,actual.actual.collector.observe(owner,deadline));
    }
    public DriverSnapshotFacts.Known heldDriver()throws IOException {
        return actual.actual.driverAuthority().withFrozenFacts(frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
    }
    public void requireOriginalReceipt(ActionReceipt receipt)throws IOException {
        actual.actual.writer.locked(same->{
            var archive=actual.actual.archive.withSession(same);ExactRef reference=archive.receiptReferenceOf(receipt);
            assertEquals(receipt,archive.loadReceipt(reference));return null;
        });
    }
    @Override public void close()throws IOException {actual.close();}
}
