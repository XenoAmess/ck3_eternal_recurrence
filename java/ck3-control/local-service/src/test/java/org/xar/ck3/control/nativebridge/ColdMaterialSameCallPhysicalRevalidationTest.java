package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionJournal;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.action.ObservationProvenance;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointCommitVerifier;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.application.checkpoint.CheckpointRequest;
import org.xar.ck3.control.application.checkpoint.CheckpointRequestFactory;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialStore;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec;
import org.xar.ck3.control.application.driver.DriverActionHistoryPublisher;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Real SAVE/receipt/Driver/material chain. Reflection only reads existing verifier delegates or invokes pure DATA checks. */
final class ColdMaterialSameCallPhysicalRevalidationTest {
    @TempDir Path temporary;
    private static CheckpointSourceCompositionTest.Fixture fixture(Path root)throws Exception {
        return new CheckpointSourceCompositionTest.Fixture(root,false,Clock.systemUTC(),Optional.empty(),Optional.empty(),List.of(),
                Duration.ofSeconds(30),root.resolve("profile"),Optional.empty(),
                Optional.of(CheckpointSourceCompositionTest.freshReconciliationReads()),false,false);
    }
    private static CheckpointResult.Confirmed save(CheckpointSourceCompositionTest.Fixture fixture)throws Exception {
        byte[] body=ActionCodec.encodeCommand(fixture.request.saveCommand());Instant deadline=fixture.request.saveCommand().deadline();
        var result=fixture.service.checkpoint(fixture.request);
        if(result instanceof CheckpointResult.Unknown unknown){
            var retained=unknown.action().orElseThrow(()->new AssertionError("unknown SAVE must retain its original actual action"));
            assertTrue(retained.ack().orElseThrow(()->new AssertionError("unknown SAVE has no original Native ACK")).nativeOk(),
                    "only original ACK=true may use this single read-only collection path");
            assertEquals(fixture.request.saveCommand(),retained.command());
            result=fixture.service.queryOriginal(unknown.actionId(),Instant.now().plusSeconds(30));
        }
        var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,result,result.toString());
        assertArrayEquals(body,ActionCodec.encodeCommand(confirmed.action().command()));
        assertEquals(deadline,confirmed.action().command().deadline());assertEquals(1,fixture.actual.nativeActionWrites());
        fixture.saveBoundary(confirmed.pair());return confirmed;
    }
    private static final class CountingFiles implements CheckpointFiles {
        private final CheckpointFiles actual;private final Path manifest;private final AtomicInteger materialReads=new AtomicInteger();
        private CountingFiles(CheckpointFiles actual,Path manifest){this.actual=actual;this.manifest=manifest;}
        @Override public Optional<CheckpointPair.FileWitness> observe(Path path)throws IOException{return actual.observe(path);}
        @Override public byte[] read(CheckpointPair.FileWitness witness,int maximum)throws IOException {
            if(Path.of(witness.reference().path()).equals(manifest))materialReads.incrementAndGet();return actual.read(witness,maximum);
        }
        @Override public CheckpointPair.FileWitness replace(Path target,byte[] body)throws IOException{return actual.replace(target,body);}
        @Override public CheckpointPair.FileWitness createNew(Path target,byte[] body)throws IOException{return actual.createNew(target,body);}
        @Override public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness source,Path target)throws IOException{return actual.copyNew(source,target);}
        @Override public void verify(CheckpointPair.FileWitness witness)throws IOException{actual.verify(witness);}
        @Override public void verify(CheckpointPair pair)throws IOException{actual.verify(pair);}
        @Override public Verification beginVerification(CheckpointPair pair)throws IOException{return actual.beginVerification(pair);}
    }
    private record Counted(SavedAttachmentSourceStore ordinary,SavedCheckpointMaterialStore materials,CountingFiles files,AtomicInteger historicalChecks){
        private void reset(){files.materialReads.set(0);historicalChecks.set(0);}
        private void requireExactlyOneMaterialReplay(){assertEquals(1,files.materialReads.get(),"one complete material-manifest read in this call");
            assertEquals(1,historicalChecks.get(),"one delegate call to the actual historical completed-cycle verifier");}
    }
    /** A new legitimate issuer delegates to the original complete verifier, lease and historical authority. No private field is written. */
    private static Counted counted(CheckpointSourceCompositionTest.Fixture fixture,SavedAttachmentSourceStore.SavedMaterial original)throws Exception {
        var actual=fixture.sources;
        var files=new CountingFiles(field(actual,"files",CheckpointFiles.class),Path.of(original.reference().path()));
        var historical=field(actual,"historicalCycles",SavedAttachmentSourceStore.HistoricalCycleProofVerifier.class);
        var checks=new AtomicInteger();
        var store=new SavedAttachmentSourceStore(files,fixture.drivers,field(actual,"verifier",CheckpointCommitVerifier.class),
                field(actual,"sessions",SavedAttachmentSourceStore.BorrowedSession.class),field(actual,"root",Path.class),
                field(actual,"cycles",SavedAttachmentSourceStore.CycleProofVerifier.class),
                (same,source,proof,head)->{checks.incrementAndGet();return historical.verify(same,source,proof,head);});
        return new Counted(store,new SavedCheckpointMaterialStore(store,fixture.firstSources),files,checks);
    }
    private static final OperationKey CYCLE_OPERATION=new OperationKey("software-material-cycle-v1");
    private record CycleFixture(CheckpointSourceCompositionTest.Fixture source,DriverActionHistoryPublisher history)implements AutoCloseable{
        @Override public void close()throws IOException{source.close();}
    }
    /** Same existing software source path used by the real dirty-cycle fixture: actual ACTION/ACK, Push and archived SEM. */
    private static CycleFixture cycleFixture(Path root)throws Exception {
        var actual=new java.util.concurrent.atomic.AtomicReference<ActionWriterIntegrationFixture>();
        var packet=new java.util.concurrent.atomic.AtomicReference<byte[]>();
        var action=new ActionWriterIntegrationFixture.SoftwareActionScenario(CYCLE_OPERATION,"game.command.software-material-cycle-v1",
                (command,attempt,dispatch)->{
                    try{
                        var fixture=actual.get();var same=fixture.writer.borrowedSession();
                        var ready=assertInstanceOf(SessionPorts.Ready.class,fixture.collector.observe(same,fixture.observationIdentity(),command.deadline()));
                        var semantic=ready.semanticEvidence().orElseThrow();var identity=ready.request().before();
                        return new ActionPorts.EffectObserved(new ActionState.EffectObservation(identity,command.source(),command.sessionId(),
                                command.expected().observerSchema(),command.expected().values(),
                                new ObservationProvenance.Push(identity.frame().snapshotId(),identity.frame().identity().nativeRevision(),semantic.originalNativePacket()),
                                semantic.observedAt(),semantic.originalNativePacket(),List.of(semantic.semantic())));
                    }catch(Exception failure){try{Throwable c=failure;for(int n=0;n<3&&c!=null;n++,c=c.getCause()){String s=c.toString();System.err.println(s.substring(0,Math.min(256,s.length())));var a=c.getStackTrace();for(int j=0;j<Math.min(2,a.length);j++){s=a[j].toString();System.err.println(s.substring(0,Math.min(160,s.length())));}}}catch(RuntimeException ignored){}throw new IllegalStateException("actual software cycle postcondition unavailable",failure);}
                },()->actual.get().enqueueSoftwareNativePacket(packet.get()),Optional.empty(),Optional.empty(),true);
        var fixture=new CheckpointSourceCompositionTest.Fixture(root,false,Clock.systemUTC(),Optional.empty(),Optional.empty(),List.of(action),
                Duration.ofSeconds(30),root.resolve("profile"),Optional.empty(),
                Optional.of(CheckpointSourceCompositionTest.freshReconciliationReads()),false,true,2);
        try{
            actual.set(fixture.actual);
            var initial=(NativeWire.Snapshot)NativeWire.decode(Files.readAllBytes(Path.of(fixture.proof.semantic().originalNativePacket().path())));
            var revision=initial.revision().add(java.math.BigInteger.ONE);
            var post=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","native:"+revision).put("revision",revision);
            post.set("state",org.xar.ck3.control.contracts.FullJsonTree.parse(initial.state().value(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES));
            packet.set(NativeWire.packet(org.xar.ck3.control.contracts.FullJsonTree.encode(post,org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES)));
            var binding=new NativeRecordedEvidenceVerifier.Binding(
                    CYCLE_OPERATION,fixture.actual.observationSource().sourceRef(),(head,receipt,archive)->{
                assertEquals(CYCLE_OPERATION,receipt.command().operation());var effect=receipt.applied().orElseThrow().observation();
                try{
                    var original=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(archive.loadNativeFrame(effect.originalEvidence())));
                    assertEquals(original.snapshotId(),effect.after().frame().snapshotId());assertEquals(original.revision(),effect.after().frame().identity().nativeRevision());
                    var raw=org.xar.ck3.control.contracts.FullJsonTree.parse(original.state().value(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
                    assertTrue(raw.get("paused").booleanValue());assertEquals(1,effect.supportingEvidence().size());
                    var semantic=org.xar.ck3.control.contracts.FullJsonTree.parse(archive.loadMaterial(effect.supportingEvidence().getFirst()).bytes(),
                            org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
                    assertEquals(effect.after().frame().snapshotId(),semantic.get("snapshot_id").textValue());
                    assertTrue(semantic.get("native_revision").isIntegralNumber());
                    assertEquals(effect.after().frame().identity().nativeRevision(),semantic.get("native_revision").bigIntegerValue());
                    assertTrue(semantic.get("paused").booleanValue());
                }catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
            });
            fixture.actual.bindAdditionalArchivedVerifier(binding);
            var history=cycleHistory(fixture.actual,binding);
            fixture.actual.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_ACTION_HISTORY_KIND,history);
            return new CycleFixture(fixture,history);
        }catch(Exception|Error failure){try{fixture.close();}catch(IOException closing){failure.addSuppressed(closing);}throw failure;}
    }
    /** Actual receipt/ACK/raw/SEM material enters the existing publisher; it alone creates coverage rows and full Driver history. */
    private static DriverActionHistoryPublisher cycleHistory(ActionWriterIntegrationFixture fixture,NativeRecordedEvidenceVerifier.Binding binding){
        ExactRef source=fixture.observationSource().sourceRef();
        var materials=new DriverActionHistoryPublisher.MaterialSource(){
            public void requireOwner(DriverStateAssembler authority,ActionJournal journal,ActionPorts.OutcomeArchive archive){
                assertSame(fixture.driverAuthority(),authority);assertSame(fixture.journal,journal);assertSame(fixture.archive,archive);
            }
            public List<ExactRef> sources(){return List.of(source);}
            private DriverActionHistoryCodec.CanonicalOnly material(ActionReceipt receipt,ActionPorts.OutcomeArchive originals){
                var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow();var effect=receipt.applied().orElseThrow().observation();
                var refs=new java.util.ArrayList<DriverActionHistoryCodec.Evidence>();
                refs.add(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME,attempt.guard().nativeEvidence()));
                refs.add(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME,effect.originalEvidence()));
                refs.add(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,originals.referenceOf(ActionTransitions.dispatch(receipt.state()).orElseThrow())));
                effect.supportingEvidence().forEach(ref->refs.add(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,ref)));
                return new DriverActionHistoryCodec.CanonicalOnly(DriverActionHistoryCodec.CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,refs,sources());
            }
            public DriverActionHistoryCodec.OriginalMaterial capture(ContinuityStorePort.Session same,ActionReceipt receipt,ActionPorts.OutcomeArchive originals)throws IOException{
                var captured=material(receipt,originals);requireOriginal(same,receipt,captured,originals);return captured;
            }
            public void requireOriginal(ContinuityStorePort.Session same,ActionReceipt receipt,DriverActionHistoryCodec.OriginalMaterial captured,ActionPorts.OutcomeArchive originals)throws IOException{
                fixture.writer.requireSession(same);assertEquals(material(receipt,originals),captured);
                assertTrue(receipt.settled());assertTrue(receipt.visibleGameplay());assertEquals(receipt,originals.loadReceipt(originals.receiptReferenceOf(receipt)));
                new NativeRecordedEvidenceVerifier(fixture.archive,fixture.journal::borrowedWriterSession,
                        (held,ref,max)->fixture.archive.readArtifact(held,ref,max),fixture.frameLoader(),List.of(binding)).verify(same.head(),receipt);
            }
        };
        return new DriverActionHistoryPublisher(fixture.driverAuthority(),fixture.journal,fixture.archive,materials,List.of(source));
    }
    /** One new actual request, fixed before its only SAVE dispatch; collection never changes that body or deadline. */
    private static CheckpointResult.Confirmed saveCurrentCycle(CheckpointSourceCompositionTest.Fixture fixture,CheckpointRequest request,
            SessionPorts.CompletedCycleProof proof)throws Exception {
        assertTrue(proof.completedCycles()>=1);int before=fixture.actual.nativeActionWrites();
        byte[] body=ActionCodec.encodeCommand(request.saveCommand());Instant deadline=request.saveCommand().deadline();
        var result=fixture.service.checkpoint(request);
        if(result instanceof CheckpointResult.Unknown unknown){
            var retained=unknown.action().orElseThrow();assertTrue(retained.ack().orElseThrow().nativeOk());
            assertEquals(request.saveCommand(),retained.command());result=fixture.service.queryOriginal(unknown.actionId(),Instant.now().plusSeconds(30));
        }
        var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,result,result.toString());
        assertArrayEquals(body,ActionCodec.encodeCommand(confirmed.action().command()));assertEquals(deadline,confirmed.action().command().deadline());
        assertEquals(before+1,fixture.actual.nativeActionWrites(),"exactly one SAVE write after the separately counted software cycle action");
        var pair=confirmed.pair();fixture.batch.commit(new SessionPorts.JournalInput(fixture.owner,"software-save-composition",SessionPorts.JournalKind.SAVE_CONFIRMED,
                Optional.of(pair.frame()),Optional.of(pair),Optional.of(proof),List.of(pair.save().reference(),pair.driver().reference(),pair.nativeAckRef())));
        return confirmed;
    }
    @Test void realPhysicalMaterialAndSavedDriverCasAreFullyCheckedOnceInTheSameCall()throws Exception {
        try(var fixture=fixture(temporary.resolve("whole-physical"))){
            var confirmed=save(fixture);
            fixture.actual.writer.locked(same->{
                try{
                    var original=fixture.sources.load(confirmed.pair());var counted=counted(fixture,original);
                    var material=counted.ordinary().loadOriginal(same,original.witness(),original.pair());
                    byte[] expected=material.savedDriver().encode();var driver=fixture.actual.archive.withSession(same).preserveMaterial(new RawJson(expected));
                    String head=same.head().digest();counted.reset();
                    physical(same,counted.materials(),material,fixture.actual.archive,driver,material.savedDriver());
                    counted.requireExactlyOneMaterialReplay();assertArrayEquals(expected,fixture.actual.archive.readArtifact(same,driver,expected.length));
                    fixture.files.verify(confirmed.pair());assertEquals(head,same.head().digest());return null;
                }catch(IOException|RuntimeException failure){throw failure;}catch(Exception failure){throw new IOException(failure);}
            });
            assertEquals(1,fixture.actual.nativeActionWrites());
        }
    }
    @Test void wrongRetainedDriverBytesAndChangedActualSaveCannotPassThePhysicalMaterialCheck()throws Exception {
        try(var fixture=fixture(temporary.resolve("physical-drift"))){
            var confirmed=save(fixture);
            fixture.actual.writer.locked(same->{
                try{
                    var original=fixture.sources.load(confirmed.pair());var counted=counted(fixture,original);
                    var material=counted.ordinary().loadOriginal(same,original.witness(),original.pair());
                    var archive=fixture.actual.archive.withSession(same);
                    var driver=archive.preserveMaterial(new RawJson(material.savedDriver().encode()));
                    var wrong=archive.preserveMaterial(new RawJson(new byte[]{'{','}'}));String head=same.head().digest();
                    counted.reset();requireMaterialFailure(()->physical(same,counted.materials(),material,fixture.actual.archive,wrong,material.savedDriver()));
                    counted.requireExactlyOneMaterialReplay();assertEquals(head,same.head().digest());
                    Files.writeString(Path.of(material.pair().save().reference().path()),"changed real software SAVE after qualification");
                    requireMaterialFailure(()->physical(same,counted.materials(),material,fixture.actual.archive,driver,material.savedDriver()));
                    assertEquals(head,same.head().digest());return null;
                }catch(IOException|RuntimeException failure){throw failure;}catch(Exception failure){throw new IOException(failure);}
            });
            assertEquals(1,fixture.actual.nativeActionWrites());
        }
    }
    @Test void realQualifiedCurrentIsReusedWithoutASecondReplayAndForeignEncodingOrWitnessIsRejected()throws Exception {
        try(var cycle=cycleFixture(temporary.resolve("same-call-reuse"))){
            var fixture=cycle.source();
            var input=fixture.actual.command("material-revalidation-real-cycle");
            var command=new ActionCommand(input.actionId(),input.before(),input.source(),input.sessionId(),CYCLE_OPERATION,input.arguments(),input.expected(),input.claims(),input.deadline());
            var completed=fixture.actual.coordinator.execute(command);
            assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,completed.outcome(),completed::toString);assertTrue(completed.visibleGameplay());
            assertEquals(1,fixture.actual.nativeActionWrites(),"separate genuine software cycle ACTION write");
            fixture.actual.writer.locked(same->{
                assertInstanceOf(DriverActionHistoryPublisher.Published.class,cycle.history().completed(same,completed));
                assertFalse(cycle.history().hasPending(same));return null;
            });
            fixture.batch.retainCycle(fixture.owner,completed);
            byte[] sourcePacket=Files.readAllBytes(Path.of(completed.applied().orElseThrow().observation().originalEvidence().path()));
            var transport=fixture.actual.physicalInputs().transport();var captureUntil=Instant.now().plusSeconds(30);
            var terminal=completed.applied().orElseThrow().observation().observedAt();
            fixture.actual.enqueueSoftwareNativePacket(sourcePacket);var post=transport.observe(captureUntil);
            if(!post.observedAt().isAfter(terminal))post=transport.observe(captureUntil);
            assertTrue(post.observedAt().isAfter(terminal));transport.acceptedSnapshotRevision(post).requireOriginal(post);
            var fresh=fixture.actual.ready();var semantic=fresh.semanticEvidence().orElseThrow();
            assertEquals(post.observedAt(),semantic.observedAt());
            assertArrayEquals(post.originalPacket(),Files.readAllBytes(Path.of(semantic.originalNativePacket().path())));
            var proof=fixture.batch.settleCycle(fixture.owner,completed,fresh.semanticEvidence().orElseThrow());assertTrue(proof.completedCycles()>=1);
            // The fresh SEM retains the actual ACTION revision+1; this explicit SAVE producer emits initial revision+2.
            assertEquals(completed.applied().orElseThrow().observation().after(),fresh.request().before());
            fixture.batch.commit(new org.xar.ck3.control.application.session.SessionPorts.JournalInput(fixture.owner,"software-save-composition",
                    org.xar.ck3.control.application.session.SessionPorts.JournalKind.BATCH_STARTED,
                    Optional.of(proof.frame()),Optional.empty(),Optional.empty(),List.of()));
            fixture.actual.enqueueSoftwareNativePacket(sourcePacket);
            var request=new CheckpointRequestFactory(fixture.request.expectedSavePath(),fixture.actual.collector.checkpoint(fixture.request.lineageId()))
                    .prepare(fresh.request().before(),fresh.request().source(),fixture.owner.sessionId(),Optional.empty(),Instant.now().plusSeconds(30));
            fixture.actual.enqueueSoftwareNativePacket(sourcePacket);var confirmed=saveCurrentCycle(fixture,request,proof);
            fixture.actual.writer.locked(same->{
                try{
                    var captured=fixture.sources.load(confirmed.pair());var counted=counted(fixture,captured);
                    var original=counted.ordinary().loadOriginal(same,captured.witness(),captured.pair());
                    String name=String.format(java.util.Locale.ROOT,"%08d.json",Math.addExact(original.originalHeadSequence(),1));
                    var matches=same.head().documents().stream().filter(pin->Path.of(pin.reference().path()).getFileName().toString().equals(name)).toList();
                    assertEquals(1,matches.size());var confirmation=matches.getFirst();
                    diagnoseSameOwnerBranch(same,confirmation,original.pair());
                    var qualified=counted.ordinary().requalifyConfirmed(same,confirmation,original.pair());
                    byte[] canonical=original.savedDriver().encode();String head=same.head().digest();counted.reset();
                    var current=qualified.requireCurrent(same);counted.requireExactlyOneMaterialReplay();
                    assertSame(original,reuse(counted.materials(),original,current,canonical));counted.requireExactlyOneMaterialReplay();
                    var foreignStore=counted(fixture,captured);
                    var foreign=foreignStore.ordinary().loadOriginal(same,captured.witness(),captured.pair());
                    requireMaterialFailure(()->reuse(counted.materials(),original,foreign,canonical));
                    byte[] wrong=canonical.clone();wrong[wrong.length-1]^=1;
                    requireMaterialFailure(()->reuse(counted.materials(),original,current,wrong));
                    Path path=Path.of(original.reference().path());byte[] unchanged=Files.readAllBytes(path);
                    Files.move(path,path.resolveSibling(path.getFileName()+".original"));Files.write(path,unchanged);
                    var witness=fixture.files.observe(path).orElseThrow();assertEquals(original.reference(),witness.reference());
                    assertNotEquals(original.witness().identity(),witness.identity());
                    var requalifiedAfterReplacement=counted.ordinary().requalifyConfirmed(same,confirmation,original.pair());
                    var changed=requalifiedAfterReplacement.requireCurrent(same);
                    requireMaterialFailure(()->reuse(counted.materials(),original,changed,canonical));
                    var driver=fixture.actual.archive.withSession(same).preserveMaterial(new RawJson(canonical));
                    requireMaterialFailure(()->physical(same,counted.materials(),original,fixture.actual.archive,driver,original.savedDriver()));
                    assertEquals(head,same.head().digest());return null;
                }catch(IOException|RuntimeException failure){throw failure;}catch(Exception failure){throw new IOException(failure);}
            });
            assertEquals(2,fixture.actual.nativeActionWrites(),"one real cycle ACTION plus one SAVE; no material-check replay");
        }
    }
    /** Observe the original Store predicate only. Any diagnostic failure is recorded; the original requalification still runs. */
    private static void diagnoseSameOwnerBranch(ContinuityStorePort.Session same,WriterContracts.Pin confirmation,CheckpointPair pair){
        ObjectNode report=StrictJson.object().put("schema","xar.test-saved-material-same-owner-predicate/v1");
        try{
            var edge=same.readHistoricalTransition(confirmation);
            var detail=ContinuityJson.parseObject(edge.details(),1024*1024);var before=edge.before().toJson();
            var cycle=before.get(WriterContracts.ORDINARY_CYCLE_FIELD);var boundary=before.get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD);
            report.put("before_status",edge.before().status().name()).put("before_sequence",edge.before().sequence()).put("edge_kind",edge.kind());
            report.put("confirmation_path",confirmation.reference().path());
            diagnostic(report,"cycleobject",()->json(cycle!=null&&cycle.isObject()));
            diagnostic(report,"boundaryobject",()->json(boundary!=null&&boundary.isObject()));
            diagnostic(report,"pending_exists_null",()->json(cycle.has("pending_receipt")&&cycle.get("pending_receipt").isNull()));
            diagnostic(report,"cycleownerEq",()->json(OrdinaryCycleTransitions.sessionFromJson(cycle.get("session"))
                    .equals(OrdinaryCycleTransitions.sessionFromJson(detail.get("session")))));
            diagnostic(report,"boundaryownerEq",()->json(OrdinaryCycleTransitions.sessionFromJson(boundary.get("session"))
                    .equals(OrdinaryCycleTransitions.sessionFromJson(detail.get("session")))));
            diagnostic(report,"boundarykind",()->json("BATCH_STARTED".equals(StrictJson.text(boundary.get("boundary")))));
            diagnostic(report,"batchEq",()->json(StrictJson.text(detail.get("batch_id")).equals(StrictJson.text(boundary.get("batch_id")))));
            diagnostic(report,"cycleDigestEq",()->json(ContinuityJson.digest(cycle)
                    .equals(OrdinaryCycleTransitions.proofFromJson(detail.get("completed_cycle_proof")).cycleStateDigest())));
            diagnostic(report,"countEq",()->json(StrictJson.integer(cycle.get("completed_cycles"),1,StrictJson.MAX_SAFE_INTEGER)
                    ==OrdinaryCycleTransitions.proofFromJson(detail.get("completed_cycle_proof")).completedCycles()));
            diagnostic(report,"machineEq",()->json(OrdinaryCycleTransitions.sessionFromJson(detail.get("session")).machineId().equals(pair.frame().machineId())));
            diagnostic(report,"gameEq",()->json(OrdinaryCycleTransitions.sessionFromJson(detail.get("session")).game().equals(pair.frame().game())));
            diagnostic(report,"cycle_digest",()->json(ContinuityJson.digest(cycle)));
            diagnostic(report,"completed_cycle_digest",()->json(OrdinaryCycleTransitions.proofFromJson(detail.get("completed_cycle_proof")).cycleStateDigest()));
            diagnostic(report,"cycle_count",()->json(StrictJson.integer(cycle.get("completed_cycles"),1,StrictJson.MAX_SAFE_INTEGER)));
            diagnostic(report,"completed_cycle_count",()->json(OrdinaryCycleTransitions.proofFromJson(detail.get("completed_cycle_proof")).completedCycles()));
            diagnostic(report,"detail_batch_id",()->json(StrictJson.text(detail.get("batch_id"))));
            diagnostic(report,"boundary_batch_id",()->json(StrictJson.text(boundary.get("batch_id"))));
            diagnostic(report,"detail_boundary_kind",()->json(StrictJson.text(detail.get("boundary"))));
            diagnostic(report,"boundary_kind",()->json(StrictJson.text(boundary.get("boundary"))));
            diagnostic(report,"detail_evidence_id",()->json(StrictJson.text(detail.get("evidence_id"))));
            diagnostic(report,"boundary_evidence_id",()->json(StrictJson.text(boundary.get("evidence_id"))));
            diagnostic(report,"boundary_evidence_digest",()->json(ContinuityJson.digest(boundary)));
            diagnostic(report,"detail_session",()->OrdinaryCycleTransitions.sessionToJson(OrdinaryCycleTransitions.sessionFromJson(detail.get("session"))));
            diagnostic(report,"cycle_session",()->OrdinaryCycleTransitions.sessionToJson(OrdinaryCycleTransitions.sessionFromJson(cycle.get("session"))));
            diagnostic(report,"boundary_session",()->OrdinaryCycleTransitions.sessionToJson(OrdinaryCycleTransitions.sessionFromJson(boundary.get("session"))));
            diagnostic(report,"actual_boundary",()->boundary);
        }catch(Exception failure){report.put("diagnostic_exception",diagnosticMessage(failure));}
        try{
            byte[] bytes=ControlBuild.strictMapper().writeValueAsBytes(report);
            if(bytes.length>16384){
                report.remove(List.of("actual_boundary","detail_session","cycle_session","boundary_session"));
                report.put("diagnostic_oversize_bytes",bytes.length).put("omitted_large_fields_exception","canonical session/boundary values omitted because the diagnostic exceeded 16KiB");
                bytes=ControlBuild.strictMapper().writeValueAsBytes(report);
            }
            if(bytes.length<=16384)System.err.println(new String(bytes,java.nio.charset.StandardCharsets.UTF_8));
            else System.err.println("{\"schema\":\"xar.test-saved-material-same-owner-predicate/v1\",\"diagnostic_exception\":\"diagnostic exceeds 16KiB after explicit bounded omission\"}");
        }catch(Exception failure){System.err.println("{\"schema\":\"xar.test-saved-material-same-owner-predicate/v1\",\"diagnostic_exception\":\"diagnostic serialization failed; original Store check will still run\"}");}
    }
    @FunctionalInterface private interface DiagnosticField {JsonNode read()throws Exception;}
    private static void diagnostic(ObjectNode report,String name,DiagnosticField field){
        try{JsonNode value=field.read();if(value==null){report.putNull(name);report.put(name+"_exception","actual field is absent");}else report.set(name,value);}
        catch(Exception failure){report.putNull(name);report.put(name+"_exception",diagnosticMessage(failure));}
    }
    private static String diagnosticMessage(Exception failure){String value=failure.getClass().getName()+": "+failure.getMessage();return value.substring(0,Math.min(512,value.length()));}
    private static JsonNode json(boolean value){return com.fasterxml.jackson.databind.node.BooleanNode.valueOf(value);}
    private static JsonNode json(long value){return com.fasterxml.jackson.databind.node.LongNode.valueOf(value);}
    private static JsonNode json(String value){return com.fasterxml.jackson.databind.node.TextNode.valueOf(value);}
    @FunctionalInterface private interface Check {void run()throws Exception;}
    private static void requireMaterialFailure(Check work){
        Exception actual=assertThrows(Exception.class,work::run);
        assertTrue(actual instanceof IOException||actual instanceof ContractViolationException,"must reject material, not fail reflection or fixture ABI: "+actual);
    }
    private static <T>T field(Object actual,String name,Class<T> type)throws ReflectiveOperationException {
        Field field=actual.getClass().getDeclaredField(name);field.setAccessible(true);return type.cast(field.get(actual));
    }
    private static void physical(ContinuityStorePort.Session same,SavedCheckpointMaterialStore materials,SavedCheckpointMaterial material,
            NativeOutcomeArchive archive,ExactRef driver,DriverStateSnapshot.Complete expected)throws Exception {
        Class<?> owner=Class.forName("org.xar.ck3.control.service.root.RootApplicationAssembly$Core$ColdRestoreSource");
        Method check=owner.getDeclaredMethod("requireCurrentPhysicalMaterial",ContinuityStorePort.Session.class,SavedCheckpointMaterialStore.class,
                SavedCheckpointMaterial.class,NativeOutcomeArchive.class,ExactRef.class,DriverStateSnapshot.Complete.class);
        invoke(check,same,materials,material,archive,driver,expected);
    }
    private static SavedAttachmentSourceStore.SavedMaterial reuse(SavedCheckpointMaterialStore materials,
            SavedAttachmentSourceStore.SavedMaterial original,SavedAttachmentSourceStore.SavedMaterial current,byte[] canonical)throws Exception {
        Class<?> owner=Class.forName("org.xar.ck3.control.service.root.RootJavaSavedBootstrap");
        Method check=owner.getDeclaredMethod("reuseCurrentMaterial",SavedCheckpointMaterialStore.class,
                SavedAttachmentSourceStore.SavedMaterial.class,SavedAttachmentSourceStore.SavedMaterial.class,byte[].class);
        return (SavedAttachmentSourceStore.SavedMaterial)invoke(check,materials,original,current,canonical);
    }
    private static Object invoke(Method check,Object... arguments)throws Exception {
        check.setAccessible(true);
        try{return check.invoke(null,arguments);}catch(InvocationTargetException failed){
            Throwable cause=failed.getCause();if(cause instanceof Exception exception)throw exception;if(cause instanceof Error error)throw error;
            throw new AssertionError("unexpected pure material check failure",cause);
        }
    }
}
