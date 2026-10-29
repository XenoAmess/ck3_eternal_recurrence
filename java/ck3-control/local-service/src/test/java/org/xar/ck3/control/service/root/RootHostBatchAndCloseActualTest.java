package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.ServiceLoader;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.LockSupport;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.session.BatchLimits;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.service.mcp.McpCancellation;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.service.OrdinarySessionHost;

/**
 * Mandatory actual-input acceptance entry. The source-owned service consumes the shared real Startup; missing inputs never pass.
 * A separately qualified startup supplies its real already retained Core/Session/Prepared/Host and original
 * afterCatalog object. This test does not launch/adopt a Game, construct a parent/proof or call fixture.advance.
 */
public final class RootHostBatchAndCloseActualTest {
    /** The registered actual startup producer retains objects; this interface grants it no runtime admission. */
    @FunctionalInterface public interface InputsWork { void consume(Inputs actual)throws Exception; }
    public interface InputsProducer {
        void withActualInputs(InputsWork actualWork) throws Exception;
    }
    @FunctionalInterface public interface OriginalClose { void close()throws Exception; }
    @FunctionalInterface public interface OriginalAfterCatalog {
        RootInstalledCatalog readOriginal(RootApplicationSession actualPublished) throws IOException;
    }
    public record Inputs(RootApplicationAssembly.Core core,RootApplicationSession original,
            RootStartupNextResources.Prepared prepared,OrdinarySessionHost host,BatchLimits nextBatch,
            Instant deadline,Duration closeWait,OriginalAfterCatalog afterCatalog,OriginalClose closeOriginal) {
        public Inputs {
            Objects.requireNonNull(core);Objects.requireNonNull(original);Objects.requireNonNull(prepared);Objects.requireNonNull(host);
            Objects.requireNonNull(nextBatch);Objects.requireNonNull(deadline);Objects.requireNonNull(closeWait);Objects.requireNonNull(afterCatalog);Objects.requireNonNull(closeOriginal);
            if(closeWait.compareTo(Duration.ofMillis(100))<0||closeWait.compareTo(Duration.ofSeconds(30))>0)
                throw new IllegalArgumentException("actual close acceptance requires a finite 100ms..30s wait bound");
        }
    }

    /** Only the actual source-qualified startup supplies these retained objects; no provider is installed here. */
    public interface PendingInputsProducer {
        PendingInputs retainActualPendingInputs() throws Exception;
    }
    @FunctionalInterface public interface RecordedFinalizationCheck {
        void require(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
                org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs actualProducer,
                org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs.Binding actualBinding,
                org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete actualCausalOriginal,
                org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known actualFinalBeforeMetadata) throws IOException;
    }
    @FunctionalInterface public interface CurrentAdoptionCheck {
        void require(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
                org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs actualProducer,
                org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs.CurrentAdoptionBinding actualCurrent,
                org.xar.ck3.control.application.session.ContinuityBatchJournal actualJournal,
                org.xar.ck3.control.application.session.ContinuityBatchJournal.AdmittedEpisode actualAdmitted,
                org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known actualKnown) throws IOException;
    }
    @FunctionalInterface public interface PendingExercise {
        void exercise(RootPendingUiProductionChainFixture actualFixture) throws Exception;
        /** Actual scenario overrides this to expose its genuine recorded-finalization originals while
         * its writer Session remains active. Existing implementations gain no passing default stage. */
        default void exercise(RootPendingUiProductionChainFixture actualFixture,RecordedFinalizationCheck actualCheck) throws Exception {
            Objects.requireNonNull(actualCheck,"actual recorded finalization assertion required");
            exercise(actualFixture);
        }
        /** The genuine late READ/BATCH scenario overrides this; delegation creates no passing credit. */
        default void exercise(RootPendingUiProductionChainFixture actualFixture,RecordedFinalizationCheck finalCheck,
                CurrentAdoptionCheck currentCheck) throws Exception {
            Objects.requireNonNull(currentCheck,"actual admitted-current assertion required");
            exercise(actualFixture,finalCheck);
        }
    }
    public record PendingInputs(RootApplicationAssembly.Core core,RootApplicationSession current,
            RootInstalledCatalog catalog,Instant deadline,PendingExercise exercise) {
        public PendingInputs {
            Objects.requireNonNull(core);Objects.requireNonNull(current);Objects.requireNonNull(catalog);
            Objects.requireNonNull(deadline);Objects.requireNonNull(exercise);
        }
    }

    /** The consumer must finish inside the actual Main admission/cleanup lifetime. */
    @FunctionalInterface public interface ResumeInputsWork { void consume(ResumeInputs actual)throws Exception; }
    /** Only the real startup can supply its installed Complete/private Inputs. Returning retained
     * objects after Main cleanup would close their physical Game, Core and writer authority. */
    public interface ResumeInputsProducer {
        void withActualResumeInputs(ResumeInputsWork actualWork) throws Exception;
    }
    public record ResumeInputs(RootApplicationAssembly.Core core,RootApplicationSession current,
            RootInstalledCatalog catalog,org.xar.ck3.control.service.mcp.McpExecutableDirectory.Complete complete,
            RootRuntimeDefinitions.Inputs privateInputs,java.time.Clock clock,
            org.xar.ck3.control.service.mcp.PublicMcpDirectory.ToolCall originalCall) {
        public ResumeInputs {
            if(core==null||current==null||catalog==null||complete==null||privateInputs==null||clock==null||originalCall==null)
                throw new IllegalArgumentException("MISSING_ACTUAL_RESUME_INPUTS: genuine retained Root and private original MCP inputs are required; NOT_RUN is not PASS");
        }
    }
    @Test public void actualRootResumeConsumesTheInstalledDirectoryAndWholeResult() throws Exception {
        List<ServiceLoader.Provider<ResumeInputsProducer>> supplied=ServiceLoader.load(ResumeInputsProducer.class).stream().toList();
        if(supplied.size()!=1)throw new IOException("MISSING_ACTUAL_RESUME_INPUTS: exactly one source-qualified actual startup ResumeInputsProducer is required; NOT_RUN is not PASS");
        AtomicBoolean consumed=new AtomicBoolean();
        supplied.getFirst().get().withActualResumeInputs(input->{
            if(!consumed.compareAndSet(false,true))throw new IOException("actual Resume inputs were delivered twice; no second invocation");
            exerciseActualResume(input);
        });
        if(!consumed.get())throw new IOException("MISSING_ACTUAL_RESUME_INPUTS: actual startup supplied no inputs inside its original lifetime; NOT_RUN is not PASS");
    }
    private static void exerciseActualResume(ResumeInputs input)throws Exception {
        if(input==null)throw new IOException("MISSING_ACTUAL_RESUME_INPUTS: actual startup supplied no retained inputs; NOT_RUN is not PASS");
        var context=input.catalog().context();
        if(context.core()!=input.core()||context.writer()!=input.core().writer()||context.archive()!=input.core().archive()
                ||context.actions()!=input.current()||context.adopted()!=input.current().driver()
                ||input.core().sessionAccess().current()!=input.current())
            throw new IOException("MISSING_ACTUAL_RESUME_INPUTS: Root/catalog/actions/Driver must be the original same installed objects");
        input.catalog().additionalDomains().requireContext(context);
        exercisePendingUiAdoptedIdentity(input);
        // The shared hook reopens original source custody before/after exactly one real Directory invocation.
        // A pending/unresolved public result remains pending; successful formatting grants no clear/Goal/day credit.
        RootDriverLifecycleResumeCodecTest.assertActualResume(input.complete(),input.privateInputs(),input.clock(),input.originalCall());
        exerciseOriginalMcpCapture(input);
    }

    /** The same live actual startup scope must retain one actual adopted PendingUI issuer. */
    private static void exercisePendingUiAdoptedIdentity(ResumeInputs input)throws IOException {
        var context=input.catalog().context();var natural=context.remainingDomains().lifecycle().natural();
        var pending=natural.pendingRuntime();pending.requireContext(context);assertSame(natural,pending.natural());
        assertSame(input.current().driver(),context.adopted());
        context.withSession(same->{
            String head=same.head().digest();boolean first=pending.hasPending();
            assertEquals(first,pending.hasPending(),"same actual adopted issuer must retain its read-only pending result");
            pending.requireContext(context);assertSame(input.current().driver(),context.adopted());
            assertEquals(head,same.head().digest(),"same-issuer metadata/facts lookups must not mutate the writer");return null;
        });
    }

    /** Consumes the same real Main directory and private Inputs; observer clocks do not change Root. */
    private static void exerciseOriginalMcpCapture(ResumeInputs input)throws IOException {
        var directory=input.complete().directory();
        var snapshot=directory.tools().stream().filter(value->value.name().equals("ck3_take_snapshot"))
                .findFirst().orElseThrow(()->new IOException("actual original snapshot descriptor is missing"));
        var resource=directory.resources().stream().filter(value->value.uri().equals("ck3://state/current"))
                .findFirst().orElseThrow(()->new IOException("actual original current-state resource is missing"));
        var arguments=new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,
                Optional.of(new RawJson("{}".getBytes(StandardCharsets.UTF_8))));
        snapshot.validateArguments(arguments);
        var snapshotCall=new PublicMcpDirectory.ToolCall(snapshot.name(),arguments,Optional.empty(),new McpCancellation());
        var resourceCall=new PublicMcpDirectory.ResourceCall(resource.uri(),Optional.empty(),new McpCancellation());
        RootOriginalMcpInvocationDirectoryAssertions.metadataRetainsActualDirectory(input.complete(),input.privateInputs(),input.clock());
        RootOriginalMcpInvocationDirectoryAssertions.expiredInputsRejectBeforeDispatch(
                input.complete(),input.privateInputs(),input.clock(),snapshotCall,resourceCall);
        // Each late-expiry assertion forwards exactly one original read; none retries its unconfirmed result.
        RootOriginalMcpInvocationDirectoryAssertions.expiryAfterActualSnapshotDoesNotAcceptOrRepeatTheResult(
                input.complete(),input.privateInputs(),input.clock(),snapshotCall);
        RootOriginalMcpInvocationDirectoryAssertions.expiryAfterActualResourceReadDoesNotAcceptOrRepeatTheResult(
                input.complete(),input.privateInputs(),input.clock(),resourceCall);
        RootOriginalMcpInvocationDirectoryAssertions.expiryAfterRejectedInvocationIsVisibleAndPreservesItsOriginalCause(
                input.complete(),input.privateInputs(),input.clock(),snapshotCall);
    }

    @Test public void pendingUiActualProductionChain() throws Exception {
        List<ServiceLoader.Provider<PendingInputsProducer>> supplied=ServiceLoader.load(PendingInputsProducer.class).stream().toList();
        if(supplied.size()!=1)throw new IOException("MISSING_ACTUAL_PENDING_INPUTS: exactly one source-qualified real startup PendingInputsProducer is required; NOT_RUN is not PASS");
        PendingInputs input=Objects.requireNonNull(supplied.getFirst().get().retainActualPendingInputs(),"actual pending Root fixture inputs required");
        RootPendingUiProductionChainFixture actual=RootPendingUiProductionChainFixture.attach(
                input.core(),input.current(),input.catalog(),input.deadline());
        AtomicBoolean recordedFinalizationChecked=new AtomicBoolean();
        AtomicBoolean admittedCurrentChecked=new AtomicBoolean();
        input.exercise().exercise(actual,(same,producer,binding,causal,finalBeforeMetadata)->{
            if(recordedFinalizationChecked.get())throw new IOException("MISSING_ACTUAL_RECORDED_FINALIZATION: scenario repeated the required original callback");
            M7RootEpisodeChainAssertions.afterRecordedNaturalPendingFinalization(same,producer,binding,causal,finalBeforeMetadata);
            recordedFinalizationChecked.set(true);
        },(same,producer,current,journal,admitted,known)->{
            if(admittedCurrentChecked.get())throw new IOException("MISSING_ACTUAL_ADMITTED_CURRENT: scenario repeated the required original callback");
            if(current.historical().transportEvidence().isPresent()){
                M7RootEpisodeChainAssertions.afterTransportedCurrent(same,producer,current,journal,admitted,known);
            }else{
                M7RootEpisodeChainAssertions.afterAdmittedReadOrBatchCurrent(same,producer,current,journal,admitted,known);
            }
            org.xar.ck3.control.application.lifecycle.LifecycleHistoricalPublicationAssertions
                    .requireHistoricalAfterProgress(same,producer,current,known);
            admittedCurrentChecked.set(true);
        });
        actual.requireFullCoverage();
        if(!recordedFinalizationChecked.get())throw new IOException("MISSING_ACTUAL_RECORDED_FINALIZATION: actual cold EVENT/FINAL and private Continue original inputs were not supplied; NOT_RUN is not PASS");
        if(!admittedCurrentChecked.get())throw new IOException("MISSING_ACTUAL_ADMITTED_CURRENT: actual later READ/BATCH private current and journal originals were not supplied; NOT_RUN is not PASS");
    }

    @Test public void actualHostNextAndStandaloneReadCloseShareOneOriginalLifetime() throws Exception {
        List<ServiceLoader.Provider<InputsProducer>> supplied=ServiceLoader.load(InputsProducer.class).stream().toList();
        if(supplied.size()!=1)throw new IOException("MISSING_ACTUAL_ROOT_INPUTS: exactly one source-qualified real startup InputsProducer is required; NOT_RUN is not PASS");
        supplied.getFirst().get().withActualInputs(RootHostBatchAndCloseActualTest::exerciseActualInputs);
    }
    private static void exerciseActualInputs(Inputs input)throws Exception {
        Objects.requireNonNull(input,"actual Root fixture inputs required");
        input.prepared().requireCore(input.core());
        RootEpisodeChainFixture fixture=RootEpisodeChainFixture.attach(input.core(),input.original(),input.prepared());
        AtomicBoolean closeCalled=new AtomicBoolean();
        try {
            var observed=RootManagedEpisodeChainInvocation.runBatch(fixture,input.host(),input.nextBatch(),input.deadline());
            var published=observed.publication().orElseThrow(()->new IOException("MISSING_ACTUAL_NEXT: Host returned without the required canonical NEXT; no empty acceptance pass"));
            RootInstalledCatalog catalog=Objects.requireNonNull(input.afterCatalog().readOriginal(published.session()),"original published catalog reference required");
            requireCatalog(input,published.session(),catalog);
            published.session().withPublicStandaloneRead(input.deadline(),same->{
                RootArmyReturnedHistoryInitializationAssertions.requirePublished(input.core(),catalog,same);
                return null;
            });
            assertSame(published.session(),input.core().sessionAccess().current());
            assertSame(input.host(),published.session().hostForPublication());
            assertTrue(input.original().isRetired());assertNotSame(input.original(),published.session());
            closeWaitsForActualStandaloneRead(input,published.session(),catalog,closeCalled);
        } finally {
            // Cleanup never retries Host/NEXT or invents a normal-exit proof.
            if(closeCalled.compareAndSet(false,true)) {
                input.closeOriginal().close();
                input.core().closeCompletion().toCompletableFuture().get(input.closeWait().toMillis(),TimeUnit.MILLISECONDS);
            }
        }
    }

    private static void requireCatalog(Inputs input,RootApplicationSession current,RootInstalledCatalog catalog)throws IOException {
        if(catalog.context().core()!=input.core()||catalog.context().writer()!=input.core().writer()
                ||catalog.context().archive()!=input.core().archive()||catalog.context().actions()!=current
                ||catalog.context().adopted()!=current.driver()||!catalog.context().game().sessionId().equals(current.identity().sessionId()))
            throw new IOException("actual afterCatalog must be the same published Core/session/actions/Driver object, not a reconstructed value");
        catalog.additionalDomains().requireContext(catalog.context());
    }

    private static void closeWaitsForActualStandaloneRead(Inputs input,RootApplicationSession current,RootInstalledCatalog catalog,AtomicBoolean closeCalled)throws Exception {
        var core=input.core();
        if(!(core.storageGuard() instanceof RootRuntimeStorageGuard storage))
            throw new IOException("MISSING_ACTUAL_STORAGE_GUARD: the retained original runtime allocation owner is required");
        storage.requireReadAuthorityCurrent();
        assertThrows(IllegalStateException.class,input.prepared()::closeCompletion,"the original storage/worker pool is still open before close");
        CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1),closeStarted=new CountDownLatch(1);
        long until=System.nanoTime()+input.closeWait().toNanos();
        ExecutorService threads=Executors.newFixedThreadPool(2,Thread.ofPlatform().daemon(true).name("actual-root-close-test-",0).factory());
        try {
            Future<WriterContracts.Head> reading=threads.submit(()->current.withPublicStandaloneRead(input.deadline(),same->{
                core.writer().requireSession(same);WriterContracts.Head retained=same.head();entered.countDown();
                if(!release.await(input.closeWait().toMillis(),TimeUnit.MILLISECONDS))throw new IOException("actual standalone writer/calls latch was not released within its bound");
                core.writer().requireSession(same);
                if(!same.head().digest().equals(retained.digest()))throw new IOException("close changed the retained writer head while actual calls were held");
                return retained;
            }));
            assertTrue(entered.await(remainingMillis(until),TimeUnit.MILLISECONDS),"actual standalone read never entered its real calls and writer locks");
            Future<Void> closing=threads.submit(()->{
                if(!closeCalled.compareAndSet(false,true))throw new IOException("the actual Core close was already attempted");
                closeStarted.countDown();input.closeOriginal().close();return null;
            });
            assertTrue(closeStarted.await(remainingMillis(until),TimeUnit.MILLISECONDS),"actual close thread did not enter");
            awaitPublicRequestClosure(core,until);
            assertFalse(closing.isDone(),"Core.close released resources before the original calls/writer callback returned");
            catalog.additionalDomains().requireContext(catalog.context());
            storage.requireReadAuthorityCurrent();
            assertThrows(IllegalStateException.class,input.prepared()::closeCompletion,"actual storage/worker close must follow the held call");
            release.countDown();
            WriterContracts.Head actualHeld=reading.get(remainingMillis(until),TimeUnit.MILLISECONDS);
            closing.get(remainingMillis(until),TimeUnit.MILLISECONDS);
            assertSame(core.closeCompletion(),input.prepared().closeCompletion(),"Core must retain the original pool/storage drain completion");
            core.closeCompletion().toCompletableFuture().get(remainingMillis(until),TimeUnit.MILLISECONDS);
            input.prepared().closeCompletion().toCompletableFuture().get(remainingMillis(until),TimeUnit.MILLISECONDS);
            assertNotNull(actualHeld);
            assertTrue(current.isRetired());assertTrue(input.host().current().orElseThrow().isRetired());
            assertThrows(IOException.class,()->catalog.additionalDomains().requireContext(catalog.context()),"the identical original catalog must be disposed after releasing calls");
            assertThrows(IOException.class,storage::requireReadAuthorityCurrent,"actual drain must close the original storage owner");
            assertThrows(IOException.class,()->core.sessionAccess().current(),"closed Core cannot mint a current public owner");
        } finally {
            release.countDown();threads.shutdown();
            // Do not interrupt/cancel accepted close work or manufacture its drain result after a failure.
            if(!threads.awaitTermination(input.closeWait().toMillis(),TimeUnit.MILLISECONDS))
                throw new IOException("UNKNOWN_ACTUAL_ROOT_CLOSE: accepted cleanup has not returned; no retry or success credit");
        }
    }
    private static void awaitPublicRequestClosure(RootApplicationAssembly.Core core,long until)throws IOException {
        for(;;) {
            try {core.sessionAccess().current();}
            catch(IOException actuallyClosed) {return;}
            if(until-System.nanoTime()<=0)throw new IOException("actual Core.close never closed new public requests");
            LockSupport.parkNanos(TimeUnit.MILLISECONDS.toNanos(1));
            if(Thread.interrupted()){Thread.currentThread().interrupt();throw new IOException("actual close wait interrupted");}
        }
    }
    private static long remainingMillis(long until)throws IOException {
        long nanos=until-System.nanoTime();
        if(nanos<=0)throw new IOException("actual Root close acceptance deadline expired; no completion inferred");
        return Math.max(1,TimeUnit.NANOSECONDS.toMillis(nanos));
    }
}
