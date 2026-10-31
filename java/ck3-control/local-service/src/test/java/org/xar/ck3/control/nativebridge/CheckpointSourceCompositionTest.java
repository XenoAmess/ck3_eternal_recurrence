package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.lifecycle.SeedAdoption;
import org.xar.ck3.control.application.lifecycle.SeedStore;
import org.xar.ck3.control.application.lifecycle.LifecycleComposites;
import org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.application.session.SessionPorts.*;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.root.CanonicalSaveReceiptVerifier;

/** Controlled raw packet/file edges compose the actual SAVE producer, canonical writer and saved source consumer. */
public final class CheckpointSourceCompositionTest {
    @TempDir Path temporary;
    private static final String LINEAGE="software-save-lineage";
    /** Construction-order edge only; every successful operation still delegates to the actual SeedStore. */
    static final class DeferredSeeds implements CheckpointService.SeedAdoptionPort,LifecycleComposites.ActualSeeds {
        private SeedStore actual;private CheckpointService owner;
        void bind(CheckpointService service,SeedStore store)throws IOException {
            if(actual!=null)throw new IOException("actual staged seeds were already bound");
            service.requireSeedStore(this,store);owner=service;actual=store;
        }
        @Override public SeedStore require()throws IOException {
            if(actual==null)throw new IOException("actual staged SeedStore not yet bound");
            owner.requireSeedStore(this,actual);return actual;
        }
        @Override public SeedAdoption freezeFirst(CheckpointPair pair,ActionReceipt receipt)throws IOException {
            return require().freezeFirst(pair,receipt);
        }
    }
    /** Test-only observation of the unchanged result from the actual production postcondition. */
    @FunctionalInterface interface AfterPostcondition {
        void after(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,
                ActionPorts.PostconditionResult actualResult);
    }
    /** Test-only wrapper of the actual frozen Store input and its actual publisher. */
    @FunctionalInterface interface SnapshotSupplierDecorator {
        DriverCheckpointStore.SnapshotSupplier decorate(DriverCheckpointStore.SnapshotSupplier actual);
    }
    static final class Fixture implements AutoCloseable {
        final ActionWriterIntegrationFixture actual;
        final NativeCheckpointFiles files=new NativeCheckpointFiles();
        final DriverCheckpointStore drivers;
        final CheckpointService service;
        final CheckpointRequest request;
        final CompletedCycleProof proof;
        final ContinuityBatchJournal batch;
        final SavedAttachmentSourceStore sources;
        final SavedFirstCheckpointMaterialStore firstSources;
        final SavedCheckpointMaterialStore materials;
        final SessionIdentity owner;
        final DeferredSeeds seedLink=new DeferredSeeds();
        final AtomicReference<Instant> lastCheckpointObservationDeadline=new AtomicReference<>();
        final AtomicReference<IOException> retainedReconciliationFailure=new AtomicReference<>();
        Fixture(Path root,boolean loseAck)throws Exception {this(root,loseAck,Clock.systemUTC());}
        Fixture(Path root,boolean loseAck,Clock serviceClock)throws Exception {
            this(root,loseAck,serviceClock,Optional.empty(),Optional.empty());
        }
        Fixture(Path root,boolean loseAck,Clock serviceClock,Optional<SnapshotSupplierDecorator> snapshots,
                Optional<AfterPostcondition> afterPostcondition)throws Exception {
            this(root,loseAck,serviceClock,snapshots,afterPostcondition,List.of());
        }
        /** Test-only extra physical actions share this actual SAVE/Driver/writer graph. */
        Fixture(Path root,boolean loseAck,Clock serviceClock,Optional<SnapshotSupplierDecorator> snapshots,
                Optional<AfterPostcondition> afterPostcondition,
                List<ActionWriterIntegrationFixture.SoftwareActionScenario> additionalActions)throws Exception {
            this(root,loseAck,serviceClock,snapshots,afterPostcondition,additionalActions,java.time.Duration.ofSeconds(8));
        }
        Fixture(Path root,boolean loseAck,Clock serviceClock,Optional<SnapshotSupplierDecorator> snapshots,
                Optional<AfterPostcondition> afterPostcondition,
                List<ActionWriterIntegrationFixture.SoftwareActionScenario> additionalActions,java.time.Duration commandBudget)throws Exception {
            this(root,loseAck,serviceClock,snapshots,afterPostcondition,additionalActions,commandBudget,root.resolve("profile"));
        }
        Fixture(Path root,boolean loseAck,Clock serviceClock,Optional<SnapshotSupplierDecorator> snapshots,
                Optional<AfterPostcondition> afterPostcondition,
                List<ActionWriterIntegrationFixture.SoftwareActionScenario> additionalActions,java.time.Duration commandBudget,Path physicalSaveRoot)throws Exception {
            this(root,loseAck,serviceClock,snapshots,afterPostcondition,additionalActions,commandBudget,physicalSaveRoot,Optional.empty());
        }
        Fixture(Path root,boolean loseAck,Clock serviceClock,Optional<SnapshotSupplierDecorator> snapshots,
                Optional<AfterPostcondition> afterPostcondition,
                List<ActionWriterIntegrationFixture.SoftwareActionScenario> additionalActions,java.time.Duration commandBudget,Path physicalSaveRoot,
                Optional<ActionWriterIntegrationFixture.SoftwareDispatch> physicalSaveWrite)throws Exception {
            Objects.requireNonNull(commandBudget);
            StrictJson.require(!commandBudget.isNegative()&&!commandBudget.isZero()
                    &&commandBudget.compareTo(java.time.Duration.ofMinutes(2))<=0,"bounded software SAVE command budget required");
            Objects.requireNonNull(snapshots);Objects.requireNonNull(afterPostcondition);additionalActions=List.copyOf(additionalActions);
            Objects.requireNonNull(physicalSaveWrite);
            AtomicReference<CheckpointService> serviceRef=new AtomicReference<>();
            AtomicReference<ActionWriterIntegrationFixture> actualRef=new AtomicReference<>();
            AtomicReference<byte[]> afterPacket=new AtomicReference<>();Path save=physicalSaveRoot.resolve("save games").resolve("xar_checkpoint.ck3");
            var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("save-checkpoint"),"game.save-checkpoint",
                    (command,attempt,dispatch)->{
                        ActionPorts.PostconditionResult actualResult=serviceRef.get().observe(command,attempt,dispatch);
                        afterPostcondition.ifPresent(after->after.after(command,attempt,dispatch,actualResult));
                        return actualResult;
                    },()->{
                        if(physicalSaveWrite.isPresent())physicalSaveWrite.orElseThrow().run();
                        else Files.writeString(save,"actual controlled SAVE bytes from the original native write");
                        actualRef.get().enqueueSoftwareNativePacket(afterPacket.get());
                    },Optional.empty(),Optional.empty(),true);
            if(additionalActions.isEmpty())actual=new ActionWriterIntegrationFixture(root,loseAck,scenario);
            else {
                var actions=new java.util.ArrayList<ActionWriterIntegrationFixture.SoftwareActionScenario>();
                actions.add(scenario);actions.addAll(additionalActions);
                var noAdditionalReads=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"fixture-adapter",
                        reviewed->List.of(),request->{throw new AssertionError("no extra software READ was installed");});
                actual=new ActionWriterIntegrationFixture(root,loseAck,noAdditionalReads,List.copyOf(actions));
            }
            actualRef.set(actual);owner=actual.observationIdentity();
            actual.preserveInitialObservationData();
            var inputs=actual.physicalInputs();
            var physical=new org.xar.ck3.control.service.root.RootLifecycleAuthority(actual.writer,actual.archive,
                    inputs.transport(),inputs.driverAssembler(),inputs.observationAssembler(),inputs.source(),
                    (same,session,source,packet,diagnostics,deadline)->{
                        actual.writer.requireSession(same);assertEquals(inputs.source(),source);
                        assertEquals(session,diagnostics.session().orElseThrow());
                        actual.archive.readArtifact(same,packet,WriterContracts.MAX_PIN_BYTES);
                        return org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification.none();
                    },Clock.systemUTC(),java.time.Duration.ofSeconds(30));
            var pending=new org.xar.ck3.control.application.action.ReconciliationPendingBinding(actual.writer,actual.archive,inputs.originals());
            var reconciliation=new org.xar.ck3.control.service.root.RootReconciliationAuthority(actual.writer,actual.archive,
                    physical,pending,inputs.originals(),inputs.frameLoader(),actual.actualReadCatalog(),
                    (original,identity,data,deadline)->{
                        assertEquals(new OperationKey("save-checkpoint"),original.command().operation());
                        assertEquals(original.command().before(),identity.pending().originalBefore());
                        assertEquals(data.identity(),identity.factual());return List.of();
                    },Clock.systemUTC());
            reconciliation.requireOwner(actual.writer,actual.archive,actual.actualReadCatalog(),physical);
            actual.bindReconciliationArchivedVerifier(reconciliation::verifyArchived);
            actual.coordinator.bindReconciliationObservation((same,original,deadline,work)->{
                try {
                    return reconciliation.observe(same,original,deadline,lease->{
                        lastCheckpointObservationDeadline.set(deadline);
                        return work.apply(lease.complete(),lease.provenance(),lease.identity(),lease.observationGuard());
                    });
                } catch (IOException failure) {
                    retainedReconciliationFailure.compareAndSet(null,failure);
                    throw failure;
                }
            });
            Files.createDirectories(save.getParent());
            Path evidence=Files.createDirectory(root.resolve("checkpoint-evidence"));
            Path seedRoot=Files.createDirectory(root.resolve("seed-state"));Files.createDirectory(seedRoot.resolve("native-session"));
            Path saves=Files.createDirectory(root.resolve("save-games"));
            DriverCheckpointStore.SnapshotSupplier originalSnapshots=new FrozenDriverSnapshotSupplier(actual.driverAuthority());
            DriverCheckpointStore.SnapshotSupplier selectedSnapshots=snapshots.isPresent()
                    ?Objects.requireNonNull(snapshots.orElseThrow().decorate(originalSnapshots)):originalSnapshots;
            drivers=new DriverCheckpointStore(files,root.resolve("saved-driver.json"),"\\\\.\\pipe\\action-writer-software-fixture",
                    selectedSnapshots);
            var originalObservations=actual.collector.checkpoint(LINEAGE);
            CheckpointRequest.ObservationPort observations=deadline->{
                lastCheckpointObservationDeadline.set(deadline);return originalObservations.observe(deadline);
            };
            service=new CheckpointService(files,drivers,observations,evidence,serviceClock,seedLink);
            assertThrows(IOException.class,seedLink::require,"missing staged seeds must reject before any SAVE");
            var seeds=new SeedStore(files,drivers,seedRoot,saves,bytes->assertTrue(bytes<1024*1024,"bounded controlled seed copy"));
            seedLink.bind(service,seeds);
            service.bindEvidence(actual.archive,actual.writer::borrowedSession,actual.writer::requireSession);
            service.bindActions(actual.coordinator);serviceRef.set(service);
            var originals=new CanonicalSaveReceiptVerifier(actual.writer,new ActionSnapshotReader(actual.journal),actual.archive,files,drivers);
            // The controlled source is still pinned and replayed by the same real central verifier.
            var definition=files.observe(root.resolve("reviewed-fixture-source.txt")).orElseThrow().reference();
            actual.bindAdditionalArchivedVerifier(originals.archivedBinding(definition,actual.writer::borrowedSession));
            var semantic=new NativeSemanticEvidenceVerifier((same,ref,maximum)->actual.archive.readArtifact(same,ref,maximum));
            var pairs=new CheckpointCommitVerifier(files,drivers,(same,source,material)->semantic.verify(same,source,material).materialDigest(),
                    root.resolve("ROOT-CONTINUITY-WINDOW.lock"),actual.writer::requireSession,originals);
            AtomicReference<SavedAttachmentSourceStore> sourceRef=new AtomicReference<>();
            var cycles=new OrdinaryCycleTransitions(actual.archive,semantic,(same,source,pair,completed)->{
                var checked=pairs.verifyCheckpoint(same,source,pair,completed);sourceRef.get().capture(checked);return checked.digest();
            },new OriginalWindowReducer.Policy(10958),actual.writer::requireSession);
            cycles.bindTerminalFrameLoader(actual.frameLoader());
            for(String kind:cycles.kinds())actual.bindAdditionalTransitionAuthority(kind,cycles);
            var materialRoot = root.resolve("saved-material");
            Files.createDirectories(materialRoot.resolve("checkpoints"));
            sources=new SavedAttachmentSourceStore(files,drivers,pairs,actual.writer::borrowedSession,materialRoot,
                    cycles::verifyCompletedCycleProof,cycles::verifyHistoricalCompletedCycleProof);sourceRef.set(sources);
            var firstVerifier=new FirstCheckpointVerifier(files,drivers,(same,source,material)->semantic.verify(same,source,material).materialDigest(),
                    root.resolve("ROOT-CONTINUITY-WINDOW.lock"),actual.writer::requireSession,originals);
            firstSources=new SavedFirstCheckpointMaterialStore(files,firstVerifier,actual.writer::borrowedSession,root.resolve("first-material"));
            materials=new SavedCheckpointMaterialStore(sources,firstSources);
            var attachments=new SavedAttachmentAuthority(drivers,materials);
            for(String kind:SavedAttachmentAuthority.kinds())actual.bindAdditionalTransitionAuthority(kind,attachments);
            batch=new ContinuityBatchJournal(actual.writer,cycles);
            Ready before=actual.ready();proof=batch.cycleProof(owner,before.semanticEvidence().orElseThrow()).orElseThrow();
            byte[] original=Files.readAllBytes(Path.of(proof.semantic().originalNativePacket().path()));
            var initial=(NativeWire.Snapshot)NativeWire.decode(original);var post=StrictJson.object();post.put("type","state_snapshot");post.put("protocol_version",1);
            post.put("snapshot_id","fixture-save-snapshot-2");post.put("revision",initial.revision().add(java.math.BigInteger.ONE));
            var postState=(com.fasterxml.jackson.databind.node.ObjectNode)org.xar.ck3.control.contracts.FullJsonTree.parse(
                    initial.state().value(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
            postState.put("retained_save_poststate_original","x".repeat(70000));post.set("state",postState);
            afterPacket.set(NativeWire.packet(org.xar.ck3.control.contracts.FullJsonTree.encode(post,
                    org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES)));
            request=new CheckpointRequestFactory(save,observations).prepare(before.request().before(),before.request().source(),owner.sessionId(),Optional.empty(),Instant.now().plus(commandBudget));
        }
        JournalCommit saveBoundary(CheckpointPair pair)throws IOException {
            return batch.commit(new JournalInput(owner,"software-save-composition",JournalKind.SAVE_CONFIRMED,Optional.of(pair.frame()),
                    Optional.of(pair),Optional.of(proof),List.of(pair.save().reference(),pair.driver().reference(),pair.nativeAckRef())));
        }
        @Override public void close()throws IOException {actual.close();}
    }
    @Test void actualCanonicalSaveAndStableFilesProduceSavedMaterialAndCanonicalSavedBoundary()throws Exception {
        try(var f=new Fixture(temporary.resolve("confirmed"),false)){
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
            assertInstanceOf(SeedAdoption.Available.class,confirmed.seedAdoption());assertEquals(1,f.actual.nativeActionWrites());
            assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,confirmed.action().outcome());
            assertTrue(confirmed.pair().frame().frame().identity().nativeRevision().compareTo(f.proof.frame().frame().identity().nativeRevision())>0);
            var committed=f.saveBoundary(confirmed.pair());assertEquals(0,committed.committedSavedDays());
            Ready after=f.actual.ready();
            assertEquals(f.proof.completedCycles(),f.batch.cycleProof(f.owner,after.semanticEvidence().orElseThrow()).orElseThrow().completedCycles(),
                    "the actual post-SAVE native revision continues without inventing another ordinary cycle");
            f.actual.writer.locked(same->{
                var material=f.sources.load(confirmed.pair());assertEquals(confirmed.pair(),material.pair());
                assertEquals(material.reference(),f.sources.loadRetainedOriginal(same,material.witness(),confirmed.pair()).reference());
                assertTrue(same.head().state().toJson().has(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD));
                Files.writeString(Path.of(confirmed.pair().save().reference().path()),"a later physical SAVE legitimately replaced the old file");
                assertThrows(Exception.class,()->f.sources.load(confirmed.pair()));
                assertEquals(material.reference(),f.sources.loadRetainedOriginal(same,material.witness(),confirmed.pair()).reference());return null;
            });assertEquals(1,f.actual.nativeActionWrites());
        }
    }
    @Test void unknownOriginalSaveDoesNotConstructPairOrReplayThePhysicalWrite()throws Exception {
        try(var f=new Fixture(temporary.resolve("unknown"),true)){
            assertInstanceOf(CheckpointResult.Unknown.class,f.service.checkpoint(f.request));
            assertInstanceOf(CheckpointResult.Unknown.class,f.service.checkpoint(f.request));assertEquals(1,f.actual.nativeActionWrites());
            assertFalse(Files.exists(f.actual.root.resolve("saved-driver.json")));
            f.actual.writer.locked(same->{assertFalse(same.head().state().toJson().has(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD));return null;});
        }
    }
    @Test void physicalPairDriftAfterConfirmedSaveRejectsSavedBoundaryWithoutResubmittingSave()throws Exception {
        try(var f=new Fixture(temporary.resolve("drift"),false)){
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
            long sequence=f.actual.writer.locked(same->same.head().state().sequence());
            Files.writeString(Path.of(confirmed.pair().save().reference().path()),"changed before original SAVED publication");
            assertThrows(Exception.class,()->f.saveBoundary(confirmed.pair()));assertEquals(1,f.actual.nativeActionWrites());
            assertEquals(sequence,f.actual.writer.<Long>locked(same->same.head().state().sequence()).longValue());
        }
    }
    @Test void sameBytesAtReplacedMaterialPathCannotRecreateTheRetainedOriginalIdentity()throws Exception {
        try(var f=new Fixture(temporary.resolve("material-file-id"),false)){
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
            f.saveBoundary(confirmed.pair());
            f.actual.writer.locked(same->{
                var material=f.sources.load(confirmed.pair());var witness=material.witness();
                Path original=Path.of(witness.reference().path());byte[] bytes=Files.readAllBytes(original);
                Files.move(original,original.resolveSibling(original.getFileName()+".original"));Files.write(original,bytes);
                var changed=f.files.observe(original).orElseThrow();assertEquals(witness.reference(),changed.reference());
                assertNotEquals(witness.identity(),changed.identity());
                assertThrows(Exception.class,()->f.sources.load(confirmed.pair()));
                assertThrows(Exception.class,()->f.sources.loadRetainedOriginal(same,witness,confirmed.pair()));return null;
            });
            assertEquals(1,f.actual.nativeActionWrites());
        }
    }
    @Test void lateSeedBindingUsesTheActualSaveStoreAndRejectsEqualLookingOtherInstances()throws Exception {
        try(var f=new Fixture(temporary.resolve("seed-construction"),false)){
            var duplicateDrivers=new DriverCheckpointStore(f.files,f.actual.root.resolve("saved-driver.json"),"\\\\.\\pipe\\action-writer-software-fixture",
                    new FrozenDriverSnapshotSupplier(f.actual.driverAuthority()));
            var duplicateSeeds=new SeedStore(f.files,duplicateDrivers,f.actual.root.resolve("seed-state"),f.actual.root.resolve("save-games"),bytes->{});
            assertThrows(IOException.class,()->f.service.requireSeedStore(f.seedLink,duplicateSeeds));
            assertThrows(IOException.class,()->f.service.requireSeedAdoptionPort(f.seedLink.require()));
            f.service.requireSeedStore(f.seedLink,f.seedLink.require());assertEquals(0,f.actual.nativeActionWrites());
            var actual=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
            assertInstanceOf(SeedAdoption.Available.class,actual.seedAdoption());assertEquals(1,f.actual.nativeActionWrites());
        }
    }
}
