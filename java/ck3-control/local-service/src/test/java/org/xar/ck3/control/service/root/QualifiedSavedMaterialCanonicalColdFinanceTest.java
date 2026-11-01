package org.xar.ck3.control.service.root;

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

import java.util.ArrayList;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.application.planning.finance.FinanceStatePort;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;

/** Real controlled SAVE -> canonical original witness -> production Finance cold material-store integration. */
public final class QualifiedSavedMaterialCanonicalColdFinanceTest {
    @TempDir Path temporary;
    private static final String LINEAGE="software-save-lineage";
    private record CaptureSample(String headDigest,SavedCheckpointMaterialEvidence evidence) { }
    /** Construction-order edge only; every successful operation still delegates to the actual SeedStore. */
    private static final class DeferredSeeds implements CheckpointService.SeedAdoptionPort,LifecycleComposites.ActualSeeds {
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
    @FunctionalInterface private interface AfterPostcondition {
        void after(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,
                ActionPorts.PostconditionResult actualResult);
    }
    /** Test-only wrapper of the actual frozen Store input and its actual publisher. */
    @FunctionalInterface private interface SnapshotSupplierDecorator {
        DriverCheckpointStore.SnapshotSupplier decorate(DriverCheckpointStore.SnapshotSupplier actual);
    }
    private static final class Support implements AutoCloseable {
        final ActionWriterIntegrationFixture actual;
        final NativeCheckpointFiles files=new NativeCheckpointFiles();
        final DriverCheckpointStore drivers;
        final CheckpointService service;
        final CheckpointRequest request;
        final CompletedCycleProof proof;
        final ContinuityBatchJournal batch;
        SavedAttachmentSourceStore sources;
        CheckpointCommitVerifier pairs;
        OrdinaryCycleTransitions cycles;
        RootCheckpointVerifier concrete;
        RootCheckpointVerifierRouter router;
        Path materialRoot;
        final List<CaptureSample> captures=new ArrayList<>();
        final boolean legacy;
        final SavedFirstCheckpointMaterialStore firstSources;
        final SavedCheckpointMaterialStore materials;
        final SessionIdentity owner;
        final DeferredSeeds seedLink=new DeferredSeeds();
        final AtomicReference<Instant> lastCheckpointObservationDeadline=new AtomicReference<>();
        final AtomicReference<IOException> retainedReconciliationFailure=new AtomicReference<>();
        Support(Path root,boolean loseAck)throws Exception {this(root,loseAck,false);}
        Support(Path root,boolean loseAck,boolean legacy)throws Exception {
            this(root,loseAck,Clock.systemUTC(),Optional.empty(),Optional.empty(),List.of(),java.time.Duration.ofSeconds(8),legacy);
        }
        Support(Path root,boolean loseAck,Clock serviceClock)throws Exception {
            this(root,loseAck,serviceClock,Optional.empty(),Optional.empty());
        }
        Support(Path root,boolean loseAck,Clock serviceClock,Optional<SnapshotSupplierDecorator> snapshots,
                Optional<AfterPostcondition> afterPostcondition)throws Exception {
            this(root,loseAck,serviceClock,snapshots,afterPostcondition,List.of());
        }
        /** Test-only extra physical actions share this actual SAVE/Driver/writer graph. */
        Support(Path root,boolean loseAck,Clock serviceClock,Optional<SnapshotSupplierDecorator> snapshots,
                Optional<AfterPostcondition> afterPostcondition,
                List<ActionWriterIntegrationFixture.SoftwareActionScenario> additionalActions)throws Exception {
            this(root,loseAck,serviceClock,snapshots,afterPostcondition,additionalActions,java.time.Duration.ofSeconds(8),false);
        }
        Support(Path root,boolean loseAck,Clock serviceClock,Optional<SnapshotSupplierDecorator> snapshots,
                Optional<AfterPostcondition> afterPostcondition,
                List<ActionWriterIntegrationFixture.SoftwareActionScenario> additionalActions,java.time.Duration commandBudget,boolean legacy)throws Exception {
            System.out.println("M5_FINANCE_PHASE " + Instant.now() + " PHASE: SupportConstructorEntry");System.out.flush();
            this.legacy=legacy;
            Objects.requireNonNull(commandBudget);
            StrictJson.require(!commandBudget.isNegative()&&!commandBudget.isZero()
                    &&commandBudget.compareTo(java.time.Duration.ofMinutes(2))<=0,"bounded software SAVE command budget required");
            Objects.requireNonNull(snapshots);Objects.requireNonNull(afterPostcondition);additionalActions=List.copyOf(additionalActions);
            AtomicReference<CheckpointService> serviceRef=new AtomicReference<>();
            AtomicReference<ActionWriterIntegrationFixture> actualRef=new AtomicReference<>();
            AtomicReference<byte[]> afterPacket=new AtomicReference<>();Path save=root.resolve("profile").resolve("save games").resolve("xar_checkpoint.ck3");
            var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("save-checkpoint"),"game.save-checkpoint",
                    (command,attempt,dispatch)->{
                        ActionPorts.PostconditionResult actualResult=serviceRef.get().observe(command,attempt,dispatch);
                        afterPostcondition.ifPresent(after->after.after(command,attempt,dispatch,actualResult));
                        return actualResult;
                    },()->{
                        Files.writeString(save,"actual controlled SAVE bytes from the original native write");
                        actualRef.get().enqueueSoftwareNativePacket(afterPacket.get());
                    },Optional.empty(),Optional.empty(),true);
            System.out.println("M5_FINANCE_PHASE " + Instant.now() + " PHASE: BeforeActionWriterFixtureConstruction");System.out.flush();
            var actions=new java.util.ArrayList<ActionWriterIntegrationFixture.SoftwareActionScenario>();
            actions.add(scenario);actions.addAll(additionalActions);
            var readScenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(
                    "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518",
                    "ck3-1.20.0.4-msvc-x64",
                    reviewed->List.of(),
                    request->{throw new AssertionError("no extra software READ was installed");},
                    java.util.Optional.of("1.20.0.4"),
                    java.util.Set.of("game.query.fresh-full-state.v1"));
            actual=new ActionWriterIntegrationFixture(root,loseAck,readScenario,List.copyOf(actions));
            actualRef.set(actual);owner=actual.observationIdentity();
            System.out.println("M5_FINANCE_PHASE " + Instant.now() + " PHASE: AfterActionWriterFixtureConstruction");System.out.flush();
            actual.configureSoftwareFreshRead179("success");
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
            configureGraph(root,semantic,originals);
            var firstVerifier=new FirstCheckpointVerifier(files,drivers,(same,source,material)->semantic.verify(same,source,material).materialDigest(),
                    root.resolve("ROOT-CONTINUITY-WINDOW.lock"),actual.writer::requireSession,originals);
            firstSources=new SavedFirstCheckpointMaterialStore(files,firstVerifier,actual.writer::borrowedSession,root.resolve("first-material"));
            materials=new SavedCheckpointMaterialStore(sources,firstSources);
            var attachments=new SavedAttachmentAuthority(drivers,materials);
            for(String kind:SavedAttachmentAuthority.kinds())actual.bindAdditionalTransitionAuthority(kind,attachments);
            batch=new ContinuityBatchJournal(actual.writer,cycles);
            System.out.println("M5_FINANCE_PHASE " + Instant.now() + " PHASE: BeforeReadyAndGraphSetup");System.out.flush();
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
            System.out.println("M5_FINANCE_PHASE " + Instant.now() + " PHASE: AfterReadyAndGraphSetup");System.out.flush();
        }
        private void configureGraph(Path root, NativeSemanticEvidenceVerifier semantic, CanonicalSaveReceiptVerifier originals) throws IOException {
            // 1. Construct the actual CheckpointCommitVerifier (pairs)
            pairs = new CheckpointCommitVerifier(files, drivers, (same, source, material) -> semantic.verify(same, source, material).materialDigest(),
                    root.resolve("ROOT-CONTINUITY-WINDOW.lock"), actual.writer::requireSession, originals);

            // 2. Construct the actual RootCheckpointVerifier (concrete)
            concrete = new RootCheckpointVerifier(actual.writer, pairs);

            // 3. Construct the actual RootCheckpointVerifierRouter (router)
            router = new RootCheckpointVerifierRouter(actual.writer);

            // 4. Prepare material root directory
            materialRoot = root.resolve("saved-material");
            Files.createDirectories(materialRoot.resolve("checkpoints"));

            // 5. Construct the actual SavedAttachmentSourceStore (sources)
            //    It requires cycle verifiers which depend on the router, so we use a forward reference via lambda or bind later.
            //    However, SavedAttachmentSourceStore constructor takes CycleProofVerifier and HistoricalCycleProofVerifier.
            //    These are methods on OrdinaryCycleTransitions. We need to create OrdinaryCycleTransitions first.

            // 6. Construct OrdinaryCycleTransitions (cycles)
            //    It needs a CheckpointVerifier. In non-legacy mode, we pass the router itself.
            //    In legacy mode, we pass a lambda that delegates to router.verify.
            OrdinaryCycleTransitions.CheckpointVerifier verifierForCycles;
            if (legacy) {
                verifierForCycles = (same, source, pair, proof) -> router.verify(same, source, pair, proof);
            } else {
                verifierForCycles = router;
            }

            cycles = new OrdinaryCycleTransitions(actual.archive, semantic, verifierForCycles, new OriginalWindowReducer.Policy(10958), actual.writer::requireSession);
            cycles.bindTerminalFrameLoader(actual.frameLoader());

            // 7. Bind additional transition authorities for cycle kinds
            for (String kind : cycles.kinds()) {
                actual.bindAdditionalTransitionAuthority(kind, cycles);
            }

            // 8. Construct SavedAttachmentSourceStore using the cycles methods
            sources = new SavedAttachmentSourceStore(files, drivers, pairs, actual.writer::borrowedSession, materialRoot,
                    cycles::verifyCompletedCycleProof, cycles::verifyHistoricalCompletedCycleProof);

            // 9. Bind the source store to the concrete verifier
            concrete.bind(sources);

            // 10. Bind the capture observer to the concrete verifier
            concrete.bindCapture((borrowed, identity, verified, material) -> {
                // Enforce actual writer session and unchanged head
                actual.writer.requireSession(borrowed);
                String headDigest = borrowed.head().digest();

                // Append capture sample
                captures.add(new CaptureSample(headDigest, SavedCheckpointMaterialEvidence.fromMaterial(material)));
            });

            // 11. Register the initial route in the router under the actual writer session
            actual.writer.locked(same -> {
                router.registerInitial(same, owner, concrete);
                return null;
            });
        }
        SavedAttachmentSourceStore freshSources() {
            return new SavedAttachmentSourceStore(files,drivers,pairs,actual.writer::borrowedSession,materialRoot,
                    cycles::verifyCompletedCycleProof,cycles::verifyHistoricalCompletedCycleProof);
        }
        JournalCommit saveBoundary(CheckpointPair pair)throws IOException {
            return batch.commit(new JournalInput(owner,"software-save-composition",JournalKind.SAVE_CONFIRMED,Optional.of(pair.frame()),
                    Optional.of(pair),Optional.of(proof),List.of(pair.save().reference(),pair.driver().reference(),pair.nativeAckRef())));
        }
        @Override public void close()throws IOException {actual.close();}
    }

    @Test void qualifiedSavePersistsOriginalWitnessForColdFinance() throws Exception {
    System.out.println("M5_FINANCE_PHASE " + Instant.now() + " OWNER: QualifiedTestEntry");System.out.flush();
        try (var support=new Support(temporary.resolve("qualified"),false)) {
        System.out.println("M5_FINANCE_PHASE " + Instant.now() + " PHASE: TestEntrySupportCreated");System.out.flush();
            support.actual.writer.locked(same->{
                assertTrue(FinanceRuntimeInstaller.checkpointInternal(support.actual.writer,same,
                        ()->{throw new AssertionError("no saved branch must not request a source store");},
                        ()->{throw new AssertionError("no saved branch must not request a machine ID");}).isEmpty());
                return null;
            });
            System.out.println("M5_FINANCE_PHASE " + Instant.now() + " PHASE: BeforeControlledCheckpoint");System.out.flush();
            var checkpointResult=support.service.checkpoint(support.request);
            System.out.println("M5_FINANCE_DIAGNOSTIC " + Instant.now() + " TYPE: " + checkpointResult.getClass().getSimpleName() + " UNKNOWN_REASON: " + (checkpointResult instanceof CheckpointResult.Unknown unknownReason ? unknownReason.reason() : "N/A") + " UNKNOWN_ACTION_PRESENT: " + (checkpointResult instanceof CheckpointResult.Unknown unknownAction ? unknownAction.action().isPresent() : false) + " RETAINED_RECONCILIATION_FAILURE: " + support.retainedReconciliationFailure.get() + " LAST_OBSERVATION_DEADLINE: " + support.lastCheckpointObservationDeadline.get());
            System.out.flush();
            System.out.println("M5_FINANCE_DIAGNOSTIC " + Instant.now() + " NATIVE_WRITES: " + support.actual.nativeActionWrites() + " FRESH_WRITES: " + support.actual.softwareFreshWrites179() + " EMPTY_AFTER_MUTATION: " + support.actual.softwareEmptyAfterMutation179() + " FRESH_SNAPSHOT_LEN: " + support.actual.softwareFreshSnapshot179().length + " FRESH_ACK_LEN: " + support.actual.softwareFreshAck179().length);
            System.out.flush();
            if (support.retainedReconciliationFailure.get() != null) {
                System.out.println("M5_FINANCE_DIAGNOSTIC_STACKTRACE_START");
                System.out.flush();
                support.retainedReconciliationFailure.get().printStackTrace(System.out);
                System.out.println("M5_FINANCE_DIAGNOSTIC_STACKTRACE_END");
                System.out.flush();
            }
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,checkpointResult);
            var pair=confirmed.pair();
            System.out.println("M5_FINANCE_PHASE " + Instant.now() + " PHASE: BeforeSaveBoundary");System.out.flush();
            assertEquals(0,support.saveBoundary(pair).committedSavedDays());
            System.out.println("M5_FINANCE_PHASE " + Instant.now() + " OWNER: SaveBoundaryReturned");System.out.flush();
            assertEquals(1,support.actual.nativeActionWrites());
            support.actual.writer.locked(same->{
                var edge=actualSavedEdge(support,same);
                var details=ContinuityJson.parseObject(edge.details(),ContinuityJson.DOCUMENT_MAX_BYTES);
                assertEquals(OrdinaryCycleTransitions.BATCH_KIND,edge.kind());
                assertEquals("java-ordinary-session/v2",StrictJson.text(details.get("source")));
                var originalHead=same.head();
                var state=originalHead.state().toJson();
                assertTrue(state.has(SavedCheckpointMaterialEvidence.FIELD));
                var canonical=SavedCheckpointMaterialEvidence.decode(state.get(SavedCheckpointMaterialEvidence.FIELD));
                assertEquals(canonical,SavedCheckpointMaterialEvidence.decode(details.get(SavedCheckpointMaterialEvidence.FIELD)));
                canonical.requireSavedBranch(pair,support.owner);
                var saved=ContinuityJson.object(state.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD));
                assertEquals(pair,CheckpointPairCodec.decode(StrictJson.canonical(saved.get("pair"))));
                assertEquals(support.owner,OrdinaryCycleTransitions.sessionFromJson(saved.get("state").get("session")));
                assertFalse(support.captures.isEmpty());
                for(var capture:support.captures) {
                    assertEquals(canonical,capture.evidence());
                    assertEquals(ContinuityJson.digest(edge.before().toJson()),capture.headDigest());
                }

                var fresh=support.freshSources();
                assertThrows(IOException.class,()->fresh.load(pair));
                System.out.println("M5_FINANCE_PHASE " + Instant.now() + " OWNER: BeforeColdFinance");System.out.flush();
                var checkpoint=FinanceRuntimeInstaller.checkpointInternal(support.actual.writer,same,()->fresh,()->support.owner.machineId());
                assertEquals(Optional.of(expectedCheckpoint(pair)),checkpoint);
                assertThrows(IOException.class,()->fresh.load(pair),"retained Finance read must not populate the original witness map");
                assertEquals(originalHead.digest(),same.head().digest());
                assertEquals(1,support.actual.nativeActionWrites());

                System.out.println("M5_FINANCE_PHASE " + Instant.now() + " OWNER: BeforePureReplay");System.out.flush();
                assertPureReplay(support,same,edge);
                int captures=support.captures.size();
                String headDigest=same.head().digest();
                var legacyWithMaterial=details.deepCopy();
                legacyWithMaterial.put("source","java-ordinary-session/v1");
                assertThrows(IllegalArgumentException.class,()->support.cycles.reduce(edge.before(),
                        new WriterContracts.Request(edge.kind(),ContinuityJson.canonical(legacyWithMaterial),List.of())));
                var otherRole=details.deepCopy();
                otherRole.put("boundary",JournalKind.BATCH_INTERRUPTED.name());
                assertThrows(IllegalArgumentException.class,()->support.cycles.reduce(edge.before(),
                        new WriterContracts.Request(edge.kind(),ContinuityJson.canonical(otherRole),List.of())));
                var missingOriginal=details.deepCopy();
                missingOriginal.remove(SavedCheckpointMaterialEvidence.FIELD);
                assertThrows(IllegalArgumentException.class,()->support.cycles.reduce(edge.before(),
                        new WriterContracts.Request(edge.kind(),ContinuityJson.canonical(missingOriginal),List.of())));
                assertEquals(captures,support.captures.size());
                assertEquals(1,support.actual.nativeActionWrites());
                assertEquals(headDigest,same.head().digest());

                // The original full canonical witness, rather than a new observation, owns identity.
                var witness=canonical.material();
                Path manifest=Path.of(witness.reference().path());
                assertEquals(witness,support.files.observe(manifest).orElseThrow());
                byte[] originalBytes=support.files.read(witness,1024*1024);
                var replacement=support.files.replace(manifest,originalBytes);
                assertEquals(witness.reference(),replacement.reference());
                assertNotEquals(witness.identity(),replacement.identity());
                // A DATA decoder still accepts the original DATA; the actual consumer checks custody.
                assertEquals(canonical,SavedCheckpointMaterialEvidence.decode(state.get(SavedCheckpointMaterialEvidence.FIELD)));
                var replacedCold=support.freshSources();
                assertThrows(IOException.class,()->FinanceRuntimeInstaller.checkpointInternal(
                        support.actual.writer,same,()->replacedCold,()->support.owner.machineId()));
                // The pinned material was replaced: do not request another canonical head/history read.
                assertEquals(captures,support.captures.size());
                assertEquals(1,support.actual.nativeActionWrites());
                return null;
            });
        }
    }

    @Test void realLegacySaveRetainsWarmCompatibilityAndPureHistory() throws Exception {
        try(var support=new Support(temporary.resolve("legacy"),false,true)) {
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,support.service.checkpoint(support.request));
            var pair=confirmed.pair();
            assertEquals(0,support.saveBoundary(pair).committedSavedDays());
            assertEquals(1,support.actual.nativeActionWrites());
            support.actual.writer.locked(same->{
                var edge=actualSavedEdge(support,same);
                var details=ContinuityJson.parseObject(edge.details(),ContinuityJson.DOCUMENT_MAX_BYTES);
                assertEquals(OrdinaryCycleTransitions.BATCH_KIND,edge.kind());
                assertEquals("java-ordinary-session/v1",StrictJson.text(details.get("source")));
                assertFalse(details.has(SavedCheckpointMaterialEvidence.FIELD));
                assertFalse(same.head().state().toJson().has(SavedCheckpointMaterialEvidence.FIELD));
                assertFalse(support.captures.isEmpty());
                var actualCaptured=support.captures.get(0).evidence();
                actualCaptured.requireSavedBranch(pair,support.owner);
                for(var capture:support.captures) {
                    assertEquals(actualCaptured,capture.evidence());
                    assertEquals(ContinuityJson.digest(edge.before().toJson()),capture.headDigest());
                }
                assertEquals(Optional.of(expectedCheckpoint(pair)),FinanceRuntimeInstaller.checkpointInternal(
                        support.actual.writer,same,()->support.sources,()->support.owner.machineId()));
                var fresh=support.freshSources();
                assertThrows(IOException.class,()->fresh.load(pair));
                assertThrows(IOException.class,()->FinanceRuntimeInstaller.checkpointInternal(
                        support.actual.writer,same,()->fresh,()->support.owner.machineId()));
                assertThrows(IOException.class,()->fresh.load(pair));
                assertPureReplay(support,same,edge);
                assertFalse(same.head().state().toJson().has(SavedCheckpointMaterialEvidence.FIELD));
                assertEquals(1,support.actual.nativeActionWrites());
                return null;
            });
        }
    }

    private static FinanceStatePort.Checkpoint expectedCheckpoint(CheckpointPair pair) {
        return new FinanceStatePort.Checkpoint(pair.save().reference(),pair.frame().frame().episodeRunId(),
                pair.frame().frame().identity().dateRaw());
    }

    private static WriterContracts.HistoricalTransition actualSavedEdge(Support support,ContinuityStorePort.Session same)throws IOException {
        var head=same.head();
        Path event=support.actual.root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS")
                .resolve(String.format(java.util.Locale.ROOT,"%08d.json",head.state().sequence())).toAbsolutePath().normalize();
        var pin=head.documents().stream().filter(candidate->Path.of(candidate.reference().path()).toAbsolutePath().normalize().equals(event))
                .findFirst().orElseThrow(()->new IOException("actual committed SAVE has no captured historical event pin"));
        return same.readHistoricalTransition(pin);
    }

    private static void assertPureReplay(Support support,ContinuityStorePort.Session same,WriterContracts.HistoricalTransition edge)throws IOException {
        int captures=support.captures.size();
        int nativeWrites=support.actual.nativeActionWrites();
        String head=same.head().digest();
        // A DATA view of the actual recorded edge; never a new Prepared or publication.
        var request=new WriterContracts.Request(edge.kind(),edge.details(),List.of());
        var reduced=support.cycles.reduce(edge.before(),request).toJson();
        reduced.put("sequence",edge.sequence());
        reduced.put("last_event_identity",edge.eventIdentity());
        assertTrue(ContinuityJson.same(edge.after().toJson(),reduced));
        assertEquals(captures,support.captures.size());
        assertEquals(nativeWrites,support.actual.nativeActionWrites());
        assertEquals(head,same.head().digest());
    }

}
