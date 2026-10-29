package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.offline.OfflineAnalysisFiles;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisWire;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.service.OfflineAnalysisWorker;
import org.xar.ck3.control.service.OfflineEventAnalysisHost;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;
import org.xar.ck3.control.wave2.events.unhandledevent.OfflineEventBatchAnalyzer;
import org.xar.ck3.control.wave2.events.unhandledevent.OfflineEventSourceAnalyzer;
import org.xar.ck3.control.wave2.events.unhandledevent.OfflineEventSourceIndex;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedEventConsumer;

/** Core lifetime owns the pool; each physical Game installs the actual current catalog's journal and sources.
 * Installation validates the real loaded Java graph. Background work retains only offline roots/inputs and
 * the original incident completion, and does not query a retired Game or mint readiness/action authority. */
public final class RootOfflineAnalysisWorker {
    private RootOfflineAnalysisWorker() { }
    public record Settings(OfflineAnalysisWorker.Settings worker, Path knowledgeRoot, Path grantsManifest) {
        public Settings {
            Objects.requireNonNull(worker);knowledgeRoot=fixed(knowledgeRoot);grantsManifest=fixed(grantsManifest);
            if(grantsManifest.getFileName()==null)throw new IllegalArgumentException("fixed shared knowledge manifest file required");
        }
    }
    public static final class Prepared implements AutoCloseable {
        private final Settings settings;
        private final RootRuntimeStorageGuard storage;
        private final CheckpointFiles files;
        private OfflineAnalysisWorker worker;
        private Installed current;
        private RootApplicationAssembly.Core core;
        private boolean closed;
        private CompletionStage<Void> storageDrainClose;
        public Prepared(Settings settings,RootRuntimeStorageGuard sameStorage,CheckpointFiles sameGuardedFiles)throws IOException {
            this.settings=Objects.requireNonNull(settings);storage=Objects.requireNonNull(sameStorage);files=Objects.requireNonNull(sameGuardedFiles);
            storage.requireFilePort(files);
        }
        public synchronized Installed install(RootInstalledCatalog actual,EventSourceReadContext actualSources)throws IOException {
            Objects.requireNonNull(actual);Objects.requireNonNull(actualSources);
            if(closed)throw new IOException("Core offline analysis preparation is closed");
            RootRuntimeContext context=actual.context();
            if(actualSources!=actual.remainingDomains().events().eventSources())
                throw new IOException("offline worker requires the identical EventSourceReadContext used by the actual next-batch event consumer");
            if(current!=null&&current.catalog==actual){current.requireContext(actual);return current;}
            if(core==null)core=context.core();else if(core!=context.core())throw new IOException("offline worker cannot cross its actual original Core/writer");
            if(!actualSources.machineId().equals(context.source().machineId())||!actualSources.machineId().equals(context.game().machineId()))
                throw new IOException("offline source roots belong to another actual catalog machine");
            for(Class<?> loaded:List.of(RootOfflineAnalysisWorker.class,OfflineAnalysisWorker.class,OfflineAnalysisFiles.class,
                    OfflineEventAnalysisWire.class,OfflineEventAnalysisHost.class,OfflineEventBatchAnalyzer.class,
                    OfflineEventSourceAnalyzer.class,OfflineEventSourceIndex.class,SourceReviewedEventConsumer.class,
                    EvidenceGrantManifestPublisher.class,RootIncidentRuntime.class,EventRuntimeInstaller.class,
                    RootRuntimeStorageGuard.class,SessionPorts.class))context.game().launchPlan().sources().requireLoadedClass(loaded);
            if(actualSources.stateRoot().startsWith(actualSources.stockGameRoot())||settings.worker().workRoot().startsWith(actualSources.stockGameRoot())
                    ||settings.knowledgeRoot().startsWith(actualSources.stockGameRoot()))throw new IOException("offline outputs cannot be installed stock content");
            // Original current context is checked only during installation, never by the background parser after retirement.
            context.requireCurrent(context.clock().instant().plusSeconds(30));
            storage.createManagedDirectories(settings.worker().workRoot());storage.createManagedDirectories(settings.knowledgeRoot());
            storage.createManagedDirectories(settings.grantsManifest().getParent());
            var incident=actual.offline();
            List<Path> outputs=List.of(settings.worker().workRoot(),settings.knowledgeRoot(),settings.grantsManifest().getParent(),actualSources.stateRoot(),incident.incidentBase(),incident.scanBase());
            storage.requireManagedRoots(outputs);
            OfflineAnalysisFiles.Port io=files(outputs);
            OfflineEventAnalysisHost host=OfflineAnalysisFiles.with(io,()->new OfflineEventAnalysisHost(Optional.of(actualSources),
                    new OfflineEventAnalysisHost.Settings(true,false,Optional.of(settings.grantsManifest()),Optional.of(incident.incidentBase()),
                            Optional.of(settings.knowledgeRoot()),Optional.of(incident.scanBase())),Optional.of(incident.reviewCompletion())));
            if(worker==null)worker=new OfflineAnalysisWorker(settings.worker(),files,io);
            var binding=new OfflineAnalysisWorker.Binding(actualSources.machineId(),actualSources.stateRoot(),actualSources.stockGameRoot(),
                    incident.incidentBase(),incident.scanBase(),settings.knowledgeRoot(),settings.grantsManifest());
            SessionPorts.OfflineAnalysisPort port=worker.bind(host,binding,io);
            if(current!=null)current.close();
            current=new Installed(this,actual,context,incident,actualSources,host,port);return current;
        }
        private OfflineAnalysisFiles.Port files(List<Path> roots)throws IOException {
            var legacy=storage.incidentGuard(roots);
            return new OfflineAnalysisFiles.Port() {
                private void target(Path path)throws IOException {
                    if(path==null||!path.isAbsolute()||!path.equals(path.normalize())||roots.stream().noneMatch(root->path.startsWith(root)&&!path.equals(root)))
                        throw new IOException("offline physical output escaped its actual admitted root");
                }
                @Override public void directories(Path path)throws IOException {
                    if(roots.stream().noneMatch(path::startsWith))throw new IOException("offline directory escaped its exact roots");
                    storage.createManagedDirectories(path);
                }
                @Override public ExactRef createNew(Path target,byte[] bytes)throws IOException {target(target);return files.createNew(target,bytes.clone()).reference();}
                @Override public ExactRef replace(Path target,byte[] bytes)throws IOException {
                    target(target);return (files.observe(target).isPresent()?files.replace(target,bytes.clone()):files.createNew(target,bytes.clone())).reference();
                }
                @Override public void beforeLock(Path target)throws IOException {
                    target(target);
                    if(!Files.exists(target,LinkOption.NOFOLLOW_LINKS))legacy.require(4096);
                }
                @Override public void beforeLink(Path target,long bytes)throws IOException {
                    target(target);
                    // Existing immutable publisher owns link creation. Its exact legacy quote is deliberately retained,
                    // not guessed released or credited as a physical saving before a complete allocation census.
                    legacy.require(Math.addExact(bytes,4096));
                }
            };
        }
        @Override public synchronized void close(){if(!closed){closed=true;if(current!=null)current.close();if(worker!=null)worker.close();}}
        /** Core shutdown retires new capture immediately; the identical storage lease is released only
         * after every accepted worker task has returned and its worker ownership resources have closed.
         * The Core owner retains this stage and reports its failure; this method never blocks its thread. */
        public synchronized CompletionStage<Void> closeStorageAfterDrain(RootRuntimeStorageGuard sameStorage) {
            if(sameStorage!=storage)throw new IllegalArgumentException("offline drain must close its identical actual storage guard");
            if(storageDrainClose!=null)return storageDrainClose;
            var completed=new CompletableFuture<Void>();storageDrainClose=completed.minimalCompletionStage();
            close();
            CompletionStage<Void> original=worker==null?CompletableFuture.completedFuture(null):worker.drainCompletion();
            original.whenComplete((ignored,drainFailure)->{
                Throwable failure=drainFailure;
                try { storage.close(); } catch(IOException|RuntimeException|Error closing) { if(failure==null)failure=closing;else if(failure!=closing)failure.addSuppressed(closing); }
                if(failure==null)completed.complete(null);else completed.completeExceptionally(failure);
            });
            return storageDrainClose;
        }
        public synchronized boolean isTerminated(){return worker==null||worker.isTerminated();}
    }
    public static final class Installed implements AutoCloseable {
        private final Prepared owner;
        private final RootInstalledCatalog catalog;
        private final RootRuntimeContext context;
        private final RootIncidentRuntime incidents;
        private final EventSourceReadContext sources;
        private final OfflineEventAnalysisHost host;
        private final SessionPorts.OfflineAnalysisPort actual;
        private final SessionPorts.OfflineAnalysisPort exposed;
        private boolean retired;
        private Installed(Prepared owner,RootInstalledCatalog catalog,RootRuntimeContext context,RootIncidentRuntime incidents,
                EventSourceReadContext sources,OfflineEventAnalysisHost host,SessionPorts.OfflineAnalysisPort actual) {
            this.owner=owner;this.catalog=catalog;this.context=context;this.incidents=incidents;this.sources=sources;this.host=host;this.actual=actual;
            exposed=captured->{
                synchronized(this){if(retired)throw new IOException("retired per-Game offline port cannot enqueue new captured originals");}
                return this.actual.enqueue(captured);
            };
        }
        public void requireContext(RootInstalledCatalog same)throws IOException {
            if(same!=catalog||same.context()!=context||same.offline()!=incidents||same.context().core()!=owner.core)
                throw new IOException("offline port crossed its actual catalog/context/journal/Core objects");
        }
        public SessionPorts.OfflineAnalysisPort port(){return exposed;}
        public EventSourceReadContext sources(){return sources;}
        public OfflineEventAnalysisHost host(){return host;}
        /** Game retirement stops new capture only; already accepted analysis and original journal ACK continue on Core pool. */
        @Override public synchronized void close(){retired=true;}
    }
    private static Path fixed(Path path){if(path==null||!path.isAbsolute()||!path.normalize().equals(path))throw new IllegalArgumentException("canonical fixed offline root required");return path;}
}
