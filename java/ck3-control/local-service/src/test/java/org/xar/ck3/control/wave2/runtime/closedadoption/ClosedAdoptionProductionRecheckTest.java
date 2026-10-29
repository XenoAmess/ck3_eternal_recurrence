package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.FileTime;
import java.time.Instant;
import java.util.ArrayList;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialEpochProducer;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryInput;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.CachedOriginalSdkVerifier;
import org.xar.ck3.control.wave2.runtime.savedproof.SavedCheckpointMeasurementCoordinator;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsJobSdkMeasurementRunner;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;

/** Actual original writer transport/lock; only the initial SDK authority remains the existing explicit synthetic seam. */
class ClosedAdoptionProductionRecheckTest {
    private static SavedCheckpointMeasurementCoordinator unmeasured() {
        return new SavedCheckpointMeasurementCoordinator(new WindowsJobSdkMeasurementRunner(() -> {
            throw new AssertionError("This regression must never measure or read SDK persistence bodies");
        }),new WindowsSavedProofIdentityReader());
    }
    private static ClosedAdoptionRequest request(ClosedAdoptionTransactionTest.Fixture fixture) {
        var material=fixture.material();var input=material.input();var source=material.sources();var business=material.business();
        var inputs=new ClosedAdoptionRequest.InputRefs(input.predecessor().reference(),input.savedBasis().reference(),input.priorQualification().reference(),
                input.fullRequest().reference(),input.failedFull().reference(),input.autoRequest().reference(),input.failedAuto().reference(),
                input.rawState().reference(),input.rawGovernance().reference(),input.actualNext().reference());
        var closed=new ClosedAdoptionRequest.ClosedRefs(source.sdkClosed().reference(),source.gameExit().reference(),source.supervisorClosed().reference(),
                source.recordingClosed().reference(),source.captureClosed().reference(),source.screenReleased().reference());
        var tasks=new ArrayList<ClosedAdoptionRequest.TaskRefs>();
        for(var task:source.tasks()) { tasks.add(new ClosedAdoptionRequest.TaskRefs(task.role(),task.spec().reference(),task.closed().reference(),task.unregistered().reference())); }
        var cycles=new ArrayList<ClosedAdoptionRequest.CycleRefs>();
        for(int i=0;i<source.settledCycles().size();i++) {
            var rpc=source.settledCycles().get(i);var metadata=business.cycles().get(i);
            cycles.add(new ClosedAdoptionRequest.CycleRefs(rpc.auto().reference(),rpc.metrics().reference(),metadata.event().reference(),metadata.ordinaryCredit().reference(),
                    metadata.autoAfter().reference(),metadata.metricsAfter().reference(),metadata.beforePlan().reference(),metadata.readonlySaveSkip().map(RecoveryEvidence::reference)));
        }
        var refs=new ClosedAdoptionRequest.BusinessRefs(business.savedSeed().reference(),business.savedGovernance().reference(),business.coldBound().reference(),
                business.openingSemantic().reference(),business.openingCapabilities().reference(),business.classifierPin().reference(),business.classifierSource(),business.queueSource(),
                business.captureProbe().reference(),business.captureCleanup().reference());
        return new ClosedAdoptionRequest(input.machineId(),input.observedAtUtc(),inputs,closed,tasks,cycles,refs,fixture.target().canonicalPath(),fixture.root(),fixture.target().originalWriter());
    }
    private static ClosedAdoptionMaterial materialWithBusiness(ClosedAdoptionMaterial old,ClosedAdoptionSources business,
            ClosedAdoptionSources.SourceVerifier verifier) {
        return new ClosedAdoptionMaterial(old.input(),old.sources(),old.publishedEpoch(),old.publishedPrefix(),business,verifier,old.originalSdk());
    }
    private static WindowsFileWriterSession launch(ClosedAdoptionTransactionTest.Fixture fixture,
            AtomicReference<WindowsFileWriterSession> process) throws IOException {
        var actual=WindowsFileWriterSession.start(ClosedAdoptionTransactionTest.settings(fixture),WindowsFileWriterSession.Mode.WRITER);
        process.set(actual);return actual;
    }
    private static void assertNoCommit(ClosedAdoptionTransactionTest.Fixture fixture,OriginalWriterTransaction.Target production,
            AtomicReference<WindowsFileWriterSession> process) throws IOException {
        assertNotEquals(fixture.target().canonicalPath(),production.canonicalPath());
        assertNotEquals(Path.of(fixture.material().input().predecessor().reference().path()),production.canonicalPath());
        assertArrayEquals(fixture.material().input().predecessor().bytes(),Files.readAllBytes(production.canonicalPath()));
        assertFalse(Files.exists(production.canonicalPath().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS/00000241.json")));
        var terminal=process.get().actualCommandResult().orElseThrow();assertEquals(0,terminal.accounting().activeProcesses());
        assertNotEquals(0,terminal.exitCode());assertTrue(Files.exists(process.get().terminalPath()));
    }
    @Test void sourceLoaderCacheDetectsSmallCreditIdentityDriftUnderTheActualOriginalWriterLock() throws Exception {
        var fixture=ClosedAdoptionTransactionTest.fixture();var production=ClosedAdoptionTransactionTest.productionFixture(fixture);
        var old=fixture.material();var original=old.business().cycles().get(0);
        Path creditPath=fixture.root().resolve("independent-credit-source.json");
        RecoveryEvidence credit=ClosedAdoptionTransactionTest.publish(creditPath,original.ordinaryCredit().bytes());
        var entries=new ArrayList<>(old.business().cycles());
        entries.set(0,new ClosedAdoptionSources.CycleSources(original.event(),credit,original.autoAfter(),original.metricsAfter(),original.beforePlan(),original.readonlySaveSkip()));
        var b=old.business();var business=new ClosedAdoptionSources(b.savedSeed(),b.savedGovernance(),b.coldBound(),b.openingSemantic(),b.openingCapabilities(),
                b.classifierPin(),b.classifierSource(),b.queueSource(),b.captureProbe(),b.captureCleanup(),entries);
        var coordinator=unmeasured();var sourceCache=new ClosedAdoptionSourceLoader(request(fixture),coordinator);
        ClosedAdoptionSources.SourceVerifier verifier=ref -> {
            if(ref.equals(credit.reference())) { sourceCache.verify(ref); } else { old.sourceVerifier().verify(ref); }
        };
        var current=materialWithBusiness(old,business,verifier);AtomicInteger reads=new AtomicInteger();
        AtomicReference<WindowsFileWriterSession> process=new AtomicReference<>();
        var error=assertThrows(ContractViolationException.class,() -> OriginalWriterTransaction.execute(production,() -> {
            reads.incrementAndGet();return current;
        },target -> {
            FileTime before=Files.getLastModifiedTime(creditPath);Files.setLastModifiedTime(creditPath,FileTime.from(before.toInstant().plusSeconds(2)));
            return launch(fixture,process);
        }));
        assertTrue(error.getMessage().contains("cached source identity drift"));assertEquals(2,reads.get());
        assertFalse(coordinator.hasMeasuredCache());assertNoCommit(fixture,production,process);
        assertArrayEquals(original.ordinaryCredit().bytes(),Files.readAllBytes(creditPath));
    }
    @Test void missingActualCacheAtTheLockedRecheckCannotReuseTheEarlierSyntheticSdkProof() throws Exception {
        var fixture=ClosedAdoptionTransactionTest.fixture();var production=ClosedAdoptionTransactionTest.productionFixture(fixture);
        var old=fixture.material();var coordinator=unmeasured();
        var unavailable=new ClosedAdoptionMaterial(old.input(),old.sources(),old.publishedEpoch(),old.publishedPrefix(),old.business(),old.sourceVerifier(),new CachedOriginalSdkVerifier(coordinator));
        AtomicInteger reads=new AtomicInteger();AtomicReference<WindowsFileWriterSession> process=new AtomicReference<>();
        var error=assertThrows(ContractViolationException.class,() -> OriginalWriterTransaction.execute(production,
                () -> reads.incrementAndGet()==1?old:unavailable,target -> launch(fixture,process)));
        assertTrue(error.getMessage().contains("No actual original-SDK measurement"));assertEquals(2,reads.get());
        assertFalse(coordinator.hasMeasuredCache());assertNoCommit(fixture,production,process);
    }
    @Test void realReducerRecomputesChangedObservationUnderTheLockAndRejectsItsDifferentCandidate() throws Exception {
        var fixture=ClosedAdoptionTransactionTest.fixture();var production=ClosedAdoptionTransactionTest.productionFixture(fixture);var old=fixture.material();var i=old.input();
        var changedInput=new ClosedFailureRecoveryInput(i.machineId(),Instant.parse(i.observedAtUtc()).plusSeconds(1).toString(),i.predecessor(),i.savedBasis(),i.priorQualification(),
                i.fullRequest(),i.failedFull(),i.autoRequest(),i.failedAuto(),i.rawState(),i.rawGovernance(),i.actualNext(),i.currentDriver(),i.currentDriverIdentity(),i.currentSave(),i.currentSaveIdentity());
        var composed=ClosedPartialEpochProducer.compose(changedInput,old.sources());
        var epoch=ClosedAdoptionTransactionTest.publish(fixture.root().resolve("changed-observation-epoch.json"),composed.epochBytes());
        var prefix=ClosedAdoptionTransactionTest.publish(fixture.root().resolve("changed-observation-prefix.json"),composed.prefixBytes());
        var changed=new ClosedAdoptionMaterial(changedInput,old.sources(),epoch,prefix,old.business(),old.sourceVerifier(),old.originalSdk());
        assertNotEquals(OriginalWriterTransaction.evaluate(old).candidate().inputDigest(),OriginalWriterTransaction.evaluate(changed).candidate().inputDigest());
        AtomicInteger reads=new AtomicInteger();AtomicReference<WindowsFileWriterSession> process=new AtomicReference<>();
        var error=assertThrows(ContractViolationException.class,() -> OriginalWriterTransaction.execute(production,
                () -> reads.incrementAndGet()==1?old:changed,target -> launch(fixture,process)));
        assertTrue(error.getMessage().contains("same actual source and SDK cache qualification under the original writer lock"));
        assertEquals(2,reads.get());assertNoCommit(fixture,production,process);
    }
    private static OriginalWriterTransaction.ManagedProcess dropActualCompletion(WindowsFileWriterSession actual) {
        InputStream original=actual.stdout();
        InputStream dropped=new InputStream() {
            private boolean lockedLine;
            @Override public int read() throws IOException {
                if(lockedLine) {
                    actual.closeOwnedInput();
                    try {
                        var exit=actual.awaitActualExit();
                        if(exit.exitCode()!=0) { throw new IOException("original writer did not actually complete before injected reply loss"); }
                    } catch(InterruptedException error) {Thread.currentThread().interrupt();throw new IOException(error);}
                    throw new IOException("synthetic loss of actual committed completion frame after native exit");
                }
                int value=original.read();if(value=='\n') {lockedLine=true;}return value;
            }
        };
        return new OriginalWriterTransaction.ManagedProcess() {
            @Override public InputStream stdout(){return dropped;}
            @Override public OutputStream stdin(){return actual.stdin();}
            @Override public OriginalWriterTransaction.ActualExit awaitActualExit() throws IOException,InterruptedException{return actual.awaitActualExit();}
            @Override public void closeOwnedInput() throws IOException{actual.closeOwnedInput();}
        };
    }
    @Test void actualCommittedFrameLossReturnsNoCommitAndNeverRetriesTheUnknownWriterOutcome() throws Exception {
        var fixture=ClosedAdoptionTransactionTest.fixture();var production=ClosedAdoptionTransactionTest.productionFixture(fixture);
        byte[] rawPending=fixture.material().input().rawState().bytes();AtomicInteger launches=new AtomicInteger();
        AtomicReference<WindowsFileWriterSession> process=new AtomicReference<>();AtomicReference<OriginalWriterTransaction.Committed> returned=new AtomicReference<>();
        var error=assertThrows(IOException.class,() -> returned.set(OriginalWriterTransaction.execute(production,fixture::material,target -> {
            launches.incrementAndGet();return dropActualCompletion(launch(fixture,process));
        })));
        assertTrue(error.getMessage().contains("loss of actual committed completion frame"));assertNull(returned.get());assertEquals(1,launches.get());
        var terminal=process.get().actualCommandResult().orElseThrow();assertEquals(0,terminal.exitCode());assertEquals(0,terminal.accounting().activeProcesses());
        assertTrue(Files.exists(process.get().terminalPath()));
        assertEquals(241,StrictJson.parse(Files.readAllBytes(production.canonicalPath())).get("sequence").longValue());
        Path events=production.canonicalPath().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS");
        assertTrue(Files.exists(events.resolve("00000241.json")));assertFalse(Files.exists(events.resolve("00000242.json")));
        // The original _load() recovers the preseed event240 index before apply() creates event241's distinct index.
        var expectedIndexes=new java.util.HashSet<Path>();
        for(int sequence:new int[]{240,241}) {
            var event=StrictJson.parse(Files.readAllBytes(events.resolve(String.format(java.util.Locale.ROOT,"%08d.json",sequence))));
            StrictJson.integer(event.get("sequence"),sequence,sequence);
            var sourceKey=StrictJson.object();sourceKey.put("kind",StrictJson.text(event.get("kind")));
            sourceKey.put("evidence_id",StrictJson.text(event.get("details").get("evidence_id")));
            Path indexPath=events.resolve("source-"+RecoveryEvidence.sha256(StrictJson.canonical(sourceKey))+".json");
            assertTrue(expectedIndexes.add(indexPath),"predecessor recovery and new commit retain distinct source identities");
            var index=StrictJson.object(StrictJson.parse(Files.readAllBytes(indexPath)),java.util.Set.of("sequence","identity"));
            assertEquals(event.get("sequence"),index.get("sequence"));
            assertEquals(StrictJson.text(event.get("identity")),StrictJson.text(index.get("identity")));
        }
        try(var files=Files.list(events)) {
            assertEquals(expectedIndexes,new java.util.HashSet<>(files.filter(path -> path.getFileName().toString().startsWith("source-")).toList()));
        }
        assertArrayEquals(rawPending,fixture.material().input().rawState().bytes());
        assertEquals(5190,StrictJson.parse(rawPending).get("pending_cycle").get("global_turn").longValue());
        // Main's consumed-approval UNKNOWN regression independently prevents restarting this real transaction.
    }
}
