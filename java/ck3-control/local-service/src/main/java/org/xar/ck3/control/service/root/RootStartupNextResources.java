package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Clock;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.CompletionStage;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.session.SessionClock;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.ManagedGameSession;

/** Same startup products -> actual lifecycle-created next Game -> one actual replacement catalog/resource set.
 * This producer creates no Game, first SAVE, lifecycle receipt, candidate, ordinary admission or Host. */
public final class RootStartupNextResources {
    private RootStartupNextResources(){ }
    public record Shared(RootApplicationAssembly.Core core,JavaGameLifecycle lifecycle,RootRuntimeCatalogFactory catalogs,
            G2Source source,RootStartupConfiguration startup,RootRuntimeDomainSettings.Bound domainSettings,
            RootRuntimeStorageGuard storage,CheckpointFiles files,RootRuntimeReadiness readiness,int retainedFrames,
            OriginalWindowReducer.Policy cyclePolicy,RootOfflineAnalysisWorker.Prepared offline,SessionClock sessionClock,
            RootEpisodeContinuationRuntime episodes,RootM7CheckpointCaptureFactory savedCaptureFactory,
            RootRestoreMaterialFactory restoreMaterials,RootPostAdoptionCollector restorePublication,Clock clock) {
        public Shared {
            Objects.requireNonNull(core);Objects.requireNonNull(lifecycle);Objects.requireNonNull(catalogs);Objects.requireNonNull(source);
            Objects.requireNonNull(startup);Objects.requireNonNull(domainSettings);Objects.requireNonNull(storage);Objects.requireNonNull(files);
            Objects.requireNonNull(readiness);Objects.requireNonNull(cyclePolicy);Objects.requireNonNull(offline);Objects.requireNonNull(sessionClock);
            Objects.requireNonNull(episodes);Objects.requireNonNull(savedCaptureFactory);Objects.requireNonNull(restoreMaterials);
            Objects.requireNonNull(restorePublication);Objects.requireNonNull(clock);
            if(retainedFrames<2||retainedFrames>4096)throw new IllegalArgumentException("bounded actual NEXT retained frames required");
            if(!source.equals(startup.source()))throw new IllegalArgumentException("actual NEXT source must remain the exact startup original");
        }
    }
    private static final class Attempt {
        final RootApplicationSession previous;final ActionReceipt parent;final ManagedGameSession game;final Instant deadline;
        final RootPlanningReads reads;RootNextEpisodeAssemblyInputs.SessionResources resources;boolean entered;IOException failure;
        Attempt(RootApplicationSession previous,ActionReceipt parent,ManagedGameSession game,Instant deadline,RootPlanningReads reads){
            this.previous=previous;this.parent=parent;this.game=game;this.deadline=deadline;this.reads=reads;
        }
    }
    public static final class Prepared implements AutoCloseable {
        private final Shared shared;private final Map<String,Attempt> attempts=new LinkedHashMap<>();private boolean closed;private CompletionStage<Void> closeCompletion;
        public Prepared(Shared actual)throws IOException {shared=Objects.requireNonNull(actual);requireCore(actual.core());}
        public void requireCore(RootApplicationAssembly.Core actual)throws IOException {
            if(actual!=shared.core()||actual.archive().writer()!=actual.writer())throw new IOException("actual NEXT resource producer crossed its sole Core/writer/archive");
            shared.catalogs().requireBoundCore(actual);shared.storage().requireFilePort(shared.files());
            shared.episodes().requireCore(actual,shared.catalogs());
        }
        public RootNextEpisodeAssemblyInputs.SessionResources prepare(RootApplicationSession previous,ActionReceipt canonicalParent,
                Instant deadline)throws IOException,InterruptedException {
            Objects.requireNonNull(previous);Objects.requireNonNull(canonicalParent);Objects.requireNonNull(deadline);
            requireCore(shared.core());
            var active=shared.core().writer().activeSession();
            if(active.isPresent())return prepareBorrowed(active.orElseThrow(),previous,canonicalParent,deadline);
            return shared.core().withBorrowed(()->prepareBorrowed(shared.core().writer().borrowedSession(),previous,canonicalParent,deadline));
        }
        private synchronized RootNextEpisodeAssemblyInputs.SessionResources prepareBorrowed(ContinuityStorePort.Session same,
                RootApplicationSession previous,ActionReceipt canonicalParent,Instant deadline)throws IOException {
            if(closed)throw new IOException("actual startup NEXT resource lifetime is closed");
            var core=shared.core();core.writer().requireSession(same);shared.startup().requireCurrent(shared.clock());
            shared.domainSettings().requireCurrent(shared.clock());shared.domainSettings().requireManagedRoots(shared.storage());
            shared.storage().requireCompleteAdmission();
            ManagedGameSession actualGame=shared.lifecycle().currentSession().orElseThrow(()->new IOException("actual lifecycle has no retained created next Game"));
            // Authenticate the actual private lifecycle result before installing any replacement product.
            core.requireCreatedNextGame(same,previous,canonicalParent,actualGame,shared.source(),deadline);
            actualGame.launchPlan().sources().requireLoadedClass(RootStartupNextResources.class);
            actualGame.launchPlan().sources().requireLoadedClass(RootEpisodeContinuationRuntime.class);
            String id=canonicalParent.command().actionId();Attempt attempt=attempts.get(id);
            if(attempt==null){
                if(attempts.size()>=64)throw new IOException("bounded original NEXT resource attempts require reconciliation");
                attempt=new Attempt(previous,canonicalParent,actualGame,deadline,new RootPlanningReads(core.writer()));attempts.put(id,attempt);
            }
            if(attempt.previous!=previous||!attempt.parent.equals(canonicalParent)||attempt.game!=actualGame||!attempt.deadline.equals(deadline))
                throw new IOException("retained NEXT resource attempt cannot change canonical parent/actual Game/deadline");
            if(attempt.resources!=null){requireRetained(same,attempt);return attempt.resources;}
            if(attempt.entered)throw new IOException("original partial NEXT resource installation is retained and cannot be replayed",attempt.failure);
            attempt.entered=true;
            try{
                RootInstalledCatalog catalog=shared.catalogs().install(core,actualGame,shared.source(),attempt.reads,shared.clock(),deadline);
                var context=catalog.context();
                if(context.core()!=core||context.game()!=actualGame||context.reads()!=attempt.reads||context.clock()!=shared.clock()
                        ||context.writer()!=core.writer()||context.archive()!=core.archive()||!context.source().equals(shared.source()))
                    throw new IOException("actual NEXT catalog installation lost its exact startup-owned physical products");
                var offline=shared.offline().install(catalog,catalog.remainingDomains().events().eventSources());offline.requireContext(catalog);
                shared.episodes().requireCore(core,shared.catalogs());
                attempt.resources=new RootNextEpisodeAssemblyInputs.SessionResources(core,catalog,shared.catalogs(),shared.startup(),shared.domainSettings(),
                        shared.storage(),shared.files(),shared.readiness(),shared.retainedFrames(),shared.cyclePolicy(),offline.port(),shared.sessionClock(),
                        shared.episodes(),shared.savedCaptureFactory(),shared.restoreMaterials(),shared.restorePublication());
                requireRetained(same,attempt);return attempt.resources;
            }catch(IOException failure){attempt.failure=failure;throw failure;}
            catch(RuntimeException failure){attempt.failure=new IOException("actual NEXT resource installation incomplete",failure);throw attempt.failure;}
        }
        private void requireRetained(ContinuityStorePort.Session same,Attempt actual)throws IOException {
            shared.core().writer().requireSession(same);shared.core().requireCreatedNextGame(same,actual.previous,actual.parent,actual.game,shared.source(),actual.deadline);
            var current=shared.lifecycle().currentSession().orElseThrow(()->new IOException("actual created Game disappeared during NEXT preparation"));
            if(current!=actual.game||actual.resources.catalog().context().game()!=current
                    ||actual.resources.catalog().context().reads()!=actual.reads||actual.resources.savedCaptureFactory()!=shared.savedCaptureFactory())
                throw new IOException("retained NEXT resource set was rebound to another actual Game/read/capture producer");
            shared.storage().requireFilePort(actual.resources.files());shared.episodes().requireCore(shared.core(),shared.catalogs());
        }
        /** Retire the sole pool; its real termination closes storage after all accepted original work returns. */
        @Override public synchronized void close(){
            if(closed)return;
            closeCompletion=shared.offline().closeStorageAfterDrain(shared.storage());closed=true;
        }
        /** Same actual drain/cleanup stage retained by the original worker; no successful stage is invented here. */
        public synchronized CompletionStage<Void> closeCompletion(){
            if(!closed||closeCompletion==null)throw new IllegalStateException("actual NEXT lifetime has not begun its original close");
            return closeCompletion;
        }
    }
}
