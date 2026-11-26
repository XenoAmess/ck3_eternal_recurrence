package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.Arrays;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.SavedContinuityAttachment;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.application.driver.DriverJson;

/** Actual SAVE and private material producer feed restore rejection/UNKNOWN consumers, never a fake admitted Root. */
final class CheckpointMaterialRestoreCompositionTest {
    @TempDir Path temporary;
    private record Harness(CheckpointSourceCompositionTest.Fixture f,CheckpointPair pair,
            CheckpointRequest.Readiness ready,RestoreCheckpointService.Request request)implements AutoCloseable {
        public void close()throws IOException{f.close();}
    }
    private Harness actualSaved(String name)throws Exception{
        return actualSaved(name,false);
    }
    private Harness actualSaved(String name,boolean nativeAttachment)throws Exception{
        Path root=temporary.resolve(name);
        var f=new CheckpointSourceCompositionTest.Fixture(root,false,Clock.systemUTC(),java.util.Optional.empty(),java.util.Optional.empty(),
                java.util.List.of(),java.time.Duration.ofSeconds(8),root.resolve("profile"),java.util.Optional.empty(),
                java.util.Optional.of(CheckpointSourceCompositionTest.freshReconciliationReads()),nativeAttachment,nativeAttachment);
        try{
            var actual=f.service.checkpoint(f.request);
            if(actual instanceof CheckpointResult.Unknown unknown&&unknown.action().flatMap(receipt->receipt.ack()).filter(ack->ack.nativeOk()).isPresent()) {
                var original=f.request.saveCommand();int writes=f.actual.nativeActionWrites();
                String body=org.xar.ck3.control.application.action.ActionCodec.bodySha256(original);Instant deadline=original.deadline();
                actual=f.service.queryOriginal(original.actionId(),Instant.now().plusSeconds(30));
                assertEquals(writes,f.actual.nativeActionWrites(),"second stable observation collects the original SAVE without another write");
                assertEquals(body,org.xar.ck3.control.application.action.ActionCodec.bodySha256(f.request.saveCommand()));
                assertEquals(deadline,f.request.saveCommand().deadline());
            }
            var collected=actual;
            var saved=assertInstanceOf(CheckpointResult.Confirmed.class,collected,()->"actual saved-material fixture "+name+" returned "+collected);
            f.saveBoundary(saved.pair());f.actual.ready();
            var ready=f.actual.collector.checkpoint("software-save-lineage").observe(Instant.now().plusSeconds(30));
            var request=f.actual.writer.locked(same->{
                var material=f.materials.currentPhysical(same,saved.pair());
                assertEquals(SavedCheckpointMaterial.Kind.ORDINARY,material.kind());
                assertArrayEquals(material.savedDriver().encode(),f.sources.readRetainedDriver(same,(SavedAttachmentSourceStore.SavedMaterial)material).encode());
                return new RestoreCheckpointService.Request("actual-private-"+name,saved.pair(),ready,
                        same.head().digest(),Instant.now().plusSeconds(30),material);
            });
            return new Harness(f,saved.pair(),ready,request);
        }catch(Exception failure){f.close();throw failure;}
    }
    private RestoreCheckpointService service(Harness h,RestoreCheckpointService.LifecyclePort lifecycle,
            RestoreCheckpointService.RestoreNativePort nativeFrames){
        var f=h.f;
        class ActualMaterialsPorts implements RestoreCheckpointService.AttachmentPort,RestoreCheckpointService.PublicationPort {
            public RestoreCheckpointService.Attachment prepare(RestoreCheckpointService.Request request,
                    RestoreCheckpointService.NativeCandidate candidate,DriverStateSnapshot.Complete saved,RestoreCheckpointService.ReadWindow reads)throws IOException {
                reads.requireOriginal(request);
                return f.materials.prepare(request,candidate,saved);
            }
            public RestoreCheckpointService.PublishedDriver publish(RestoreCheckpointService.Request request,
                    RestoreCheckpointService.NativeCandidate candidate,DriverStateSnapshot.Complete saved,
                    WriterContracts.Prepared prepared,WriterContracts.Receipt receipt,RestoreCheckpointService.ReadWindow reads){
                throw new AssertionError("these rejection/UNKNOWN paths must not publish");
            }
            public void requireCurrent(RestoreCheckpointService.PublishedDriver published,
                    RestoreCheckpointService.NativeCandidate candidate,WriterContracts.Receipt receipt,RestoreCheckpointService.ReadWindow reads){
                throw new AssertionError("these paths must not mint admission");
            }
        }
        var ports=new ActualMaterialsPorts();
        return new RestoreCheckpointService(f.files,f.drivers,lifecycle,nativeFrames,f.actual.writer,f.materials,ports,ports,Clock.systemUTC());
    }
    private static RestoreCheckpointService.NativeCandidate cannotObserve(RestoreCheckpointService.ReplacementAck ack,RestoreCheckpointService.ReadWindow reads){
        throw new AssertionError("unresolved lifecycle must not observe a replacement");
    }
    @Test void unknownLifecycleQueriesOnlyAndDoesNotSaveAgain()throws Exception {
        try(var h=actualSaved("unknown-lifecycle")){
            var launches=new AtomicInteger();var queries=new AtomicInteger();
            var service=service(h,new RestoreCheckpointService.LifecyclePort(){
                public RestoreCheckpointService.LaunchResult replaceOnce(RestoreCheckpointService.Request request){
                    launches.incrementAndGet();return new RestoreCheckpointService.LaunchUnknown("controlled lifecycle unresolved");
                }
                public RestoreCheckpointService.LaunchResult query(String id,Instant deadline){
                    queries.incrementAndGet();return new RestoreCheckpointService.LaunchUnknown("still unresolved");
                }
            },CheckpointMaterialRestoreCompositionTest::cannotObserve);
            long before=h.f.actual.writer.locked(same->same.head().state().sequence());
            h.f.actual.writer.locked(same->{
                assertTrue(service.originalReboundOrigin(same,h.request.requestId()).isEmpty());
                assertTrue(service.originalReboundOrigin(same,"no-actual-private-attempt").isEmpty());return null;
            });
            assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restore(h.request));
            h.f.actual.writer.locked(same->{assertTrue(service.originalReboundOrigin(same,h.request.requestId()).isEmpty());return null;});
            assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restore(h.request));
            h.f.actual.writer.locked(same->{assertTrue(service.originalReboundOrigin(same,h.request.requestId()).isEmpty());return null;});
            assertEquals(1,launches.get());assertEquals(1,queries.get());assertEquals(1,h.f.actual.nativeActionWrites());
            assertEquals(before,h.f.actual.writer.<Long>locked(same->same.head().state().sequence()).longValue());
        }
    }
    @Test void existingLoadedApplicationEntryQueriesWithFreshReadWindowAndKeepsOriginalExpiredRequest()throws Exception {
        try(var h=actualSaved("existing-query-only")) {
            var original=new RestoreCheckpointService.Request(h.request.requestId(),h.pair,h.ready,h.request.expectedHeadDigest(),
                    Instant.now().minusSeconds(1),h.request.savedMaterial());
            var queries=new AtomicInteger();Instant fresh=Instant.now().plusSeconds(30);
            var service=service(h,new RestoreCheckpointService.LifecyclePort(){
                public RestoreCheckpointService.LaunchResult replaceOnce(RestoreCheckpointService.Request request){
                    throw new AssertionError("existing-loaded application recovery cannot create or replace Game");
                }
                public RestoreCheckpointService.LaunchResult query(String id,Instant deadline){
                    assertEquals(original.requestId(),id);assertEquals(fresh,deadline);queries.incrementAndGet();
                    return new RestoreCheckpointService.LaunchUnknown("fixture query has no original Native issuer");
                }
            },CheckpointMaterialRestoreCompositionTest::cannotObserve);
            String before=h.f.actual.writer.locked(same->same.head().digest());
            assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restoreExisting(original,fresh));
            assertEquals(1,queries.get());assertTrue(original.deadline().isBefore(Instant.now()));
            var changed=new RestoreCheckpointService.Request(original.requestId(),original.pair(),original.current(),original.expectedHeadDigest(),
                    original.deadline().plusSeconds(1),original.savedMaterial());
            var refused=assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restoreExisting(changed,fresh));
            assertTrue(refused.reason().contains("changed its exact body"),refused.reason());assertEquals(1,queries.get());
            h.f.actual.writer.locked(same->{assertEquals(before,same.head().digest());return null;});
            assertEquals(1,h.f.actual.nativeActionWrites(),"only the fixture's original SAVE exists; no Native recovery role was fabricated");
        }
    }
    @Test void existingLoadedEntryRequiresFiniteFreshWindowBeforeRetainingAnAttempt()throws Exception {
        try(var h=actualSaved("existing-window")) {
            var queries=new AtomicInteger();var service=service(h,new RestoreCheckpointService.LifecyclePort(){
                public RestoreCheckpointService.LaunchResult replaceOnce(RestoreCheckpointService.Request request){throw new AssertionError("query only");}
                public RestoreCheckpointService.LaunchResult query(String id,Instant deadline){queries.incrementAndGet();return new RestoreCheckpointService.LaunchUnknown("fixture only");}
            },CheckpointMaterialRestoreCompositionTest::cannotObserve);
            assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restoreExisting(h.request,Instant.now().minusSeconds(1)));
            assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restoreExisting(h.request,Instant.now().plusSeconds(1801)));
            var absent=assertInstanceOf(RestoreCheckpointService.Unknown.class,service.queryOriginal(h.request.requestId(),Instant.now().plusSeconds(30)));
            assertTrue(absent.reason().contains("no original private restore attempt"),absent.reason());assertEquals(0,queries.get());
            assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restoreExisting(h.request,Instant.now().plusSeconds(30)));
            assertEquals(1,queries.get());
        }
    }
    @Test void existingLoadedEntryPreservesHeadPhysicalSourceAndUnlaunchedFailureGuards()throws Exception {
        try(var h=actualSaved("existing-source-guards")) {
            var queries=new AtomicInteger();var service=service(h,new RestoreCheckpointService.LifecyclePort(){
                public RestoreCheckpointService.LaunchResult replaceOnce(RestoreCheckpointService.Request request){throw new AssertionError("source failure must not launch");}
                public RestoreCheckpointService.LaunchResult query(String id,Instant deadline){queries.incrementAndGet();throw new AssertionError("invalid predecessor cannot query a replacement");}
            },CheckpointMaterialRestoreCompositionTest::cannotObserve);
            var wrongHead=new RestoreCheckpointService.Request("existing-wrong-head",h.pair,h.ready,"0".repeat(64),
                    Instant.now().plusSeconds(30),h.request.savedMaterial());
            assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restore(wrongHead));
            var unlaunched=assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restoreExisting(wrongHead,Instant.now().plusSeconds(30)));
            assertTrue(unlaunched.reason().contains("unlaunched restore attempt"),unlaunched.reason());
            var freshWrongHead=new RestoreCheckpointService.Request("fresh-existing-wrong-head",h.pair,h.ready,"0".repeat(64),
                    Instant.now().minusSeconds(1),h.request.savedMaterial());
            assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restoreExisting(freshWrongHead,Instant.now().plusSeconds(30)));
            Files.writeString(Path.of(h.pair.save().reference().path()),"changed original physical SAVE");
            assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restoreExisting(h.request,Instant.now().plusSeconds(30)));
            assertEquals(0,queries.get());assertEquals(1,h.f.actual.nativeActionWrites());
        }
    }
    @Test void existingLoadedQueryAckStillNeedsTwoIndependentOriginalReadProofs()throws Exception {
        try(var h=actualSaved("existing-two-read-proof")) {
            var candidate=actualReplacementPacket(h,"existing-cache");var queries=new AtomicInteger();var observed=new AtomicInteger();
            var ack=new RestoreCheckpointService.ReplacementAck(h.request.requestId(),h.pair.frame().game(),candidate.actual().session().game(),
                    h.pair.save().reference(),candidate.originalNativePacket());
            var service=service(h,new RestoreCheckpointService.LifecyclePort(){
                public RestoreCheckpointService.LaunchResult replaceOnce(RestoreCheckpointService.Request request){throw new AssertionError("existing recovery cannot replace");}
                public RestoreCheckpointService.LaunchResult query(String id,Instant deadline){queries.incrementAndGet();return ack;}
            },(original,reads)->{
                assertSame(ack,original);assertSame(h.request,reads.original());assertTrue(reads.queryOnly());reads.requireReplacement(original);
                observed.incrementAndGet();return candidate;
            });
            String before=h.f.actual.writer.locked(same->same.head().digest());
            var first=assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restoreExisting(h.request,Instant.now().plusSeconds(30)));
            assertTrue(first.reason().contains("independent restore READ custody unavailable"),first.reason());
            var later=assertInstanceOf(RestoreCheckpointService.Unknown.class,service.queryOriginal(h.request.requestId(),Instant.now().plusSeconds(30)));
            assertTrue(later.reason().contains("independent restore READ custody unavailable"),later.reason());
            assertEquals(1,queries.get());assertEquals(4,observed.get());
            h.f.actual.writer.locked(same->{assertEquals(before,same.head().digest());assertTrue(service.originalReboundOrigin(same,h.request.requestId()).isEmpty());return null;});
            assertEquals(1,h.f.actual.nativeActionWrites(),"software LifecyclePort ACK and cached DATA do not mint a Native role or attachment");
        }
    }
    @Test void physicalSourceDriftAndWrongHeadRefuseBeforeAnyLifecycleDispatch()throws Exception {
        try(var h=actualSaved("drift")){
            var launches=new AtomicInteger();
            var service=service(h,new RestoreCheckpointService.LifecyclePort(){
                public RestoreCheckpointService.LaunchResult replaceOnce(RestoreCheckpointService.Request request){
                    launches.incrementAndGet();throw new AssertionError("invalid source cannot replace Game");
                }
                public RestoreCheckpointService.LaunchResult query(String id,Instant deadline){throw new AssertionError("not dispatched");}
            },CheckpointMaterialRestoreCompositionTest::cannotObserve);
            var wrongHead=new RestoreCheckpointService.Request("head-drift",h.pair,h.ready,"0".repeat(64),
                    Instant.now().plusSeconds(30),h.request.savedMaterial());
            assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restore(wrongHead));assertEquals(0,launches.get());
            Files.writeString(Path.of(h.pair.save().reference().path()),"a later actual physical SAVE replaced the file");
            assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restore(h.request));assertEquals(0,launches.get());
        }
    }
    @Test void exceptionAfterPossibleReplacementStillOnlyQueries()throws Exception {
        try(var h=actualSaved("lost-replacement-ack")){
            var launches=new AtomicInteger();var queries=new AtomicInteger();
            var service=service(h,new RestoreCheckpointService.LifecyclePort(){
                public RestoreCheckpointService.LaunchResult replaceOnce(RestoreCheckpointService.Request request)throws IOException{
                    launches.incrementAndGet();throw new IOException("connection failed after possible launch");
                }
                public RestoreCheckpointService.LaunchResult query(String id,Instant deadline){
                    queries.incrementAndGet();return new RestoreCheckpointService.LaunchUnknown("outcome unknown");
                }
            },CheckpointMaterialRestoreCompositionTest::cannotObserve);
            assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restore(h.request));
            assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restore(h.request));
            assertEquals(1,launches.get());assertEquals(1,queries.get());assertEquals(1,h.f.actual.nativeActionWrites());
        }
    }
    @Test void replacementAckAndRawWrongActorCannotPrepareAnAttachment()throws Exception {
        try(var h=actualSaved("wrong-restored-actor")){
            var original=h.pair.frame().game();
            var replacement=new GameGeneration(original.pid()+1,new PythonOnlyUInt64(original.creationFiletime().value().add(BigInteger.ONE)));
            byte[] old=Files.readAllBytes(Path.of(h.request.savedMaterial().sourceSemantic().originalNativePacket().path()));
            var envelope=(com.fasterxml.jackson.databind.node.ObjectNode)FullJsonTree.parse(Arrays.copyOfRange(old,4,old.length),DriverJson.MAX_NATIVE_BYTES);
            var state=(com.fasterxml.jackson.databind.node.ObjectNode)envelope.get("state");
            ((com.fasterxml.jackson.databind.node.ObjectNode)state.get("played_character")).put("character_id",999);
            byte[] json=FullJsonTree.encode(envelope,DriverJson.MAX_NATIVE_BYTES),packet=ByteBuffer.allocate(json.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();
            var ref=h.f.files.createNew(h.f.actual.root.resolve("wrong-restored-raw.bin"),packet).reference();
            var frame=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(originalMachine(h),replacement,BigInteger.ONE,"actual-new-transport"),
                    StrictJson.text(envelope.get("snapshot_id")),envelope.get("revision").bigIntegerValue(),new RawJson(FullJsonTree.encode(state,DriverJson.MAX_NATIVE_BYTES)),packet,Instant.now());
            var candidate=new RestoreCheckpointService.NativeCandidate(frame,h.ready.source(),h.pair.lineageId(),ref);
            var service=service(h,new RestoreCheckpointService.LifecyclePort(){
                public RestoreCheckpointService.LaunchResult replaceOnce(RestoreCheckpointService.Request request){
                    return new RestoreCheckpointService.ReplacementAck(request.requestId(),original,replacement,h.pair.save().reference(),ref);
                }
                public RestoreCheckpointService.LaunchResult query(String id,Instant deadline){throw new AssertionError("retained ACK should not relaunch");}
            },(ack,deadline)->candidate);
            long before=h.f.actual.writer.locked(same->same.head().state().sequence());
            assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restore(h.request));
            assertEquals(before,h.f.actual.writer.<Long>locked(same->same.head().state().sequence()).longValue());assertEquals(1,h.f.actual.nativeActionWrites());
        }
    }
    @Test void ordinaryManifestAndSameBytesReplacementCannotMintFirstBaselineMaterial()throws Exception {
        try(var h=actualSaved("first-branch-refusal")){
            h.f.actual.writer.locked(same->{
                var material=h.request.savedMaterial();
                assertThrows(Exception.class,()->h.f.materials.loadOriginal(same,SavedCheckpointMaterial.Kind.FIRST_BASELINE,material.witness(),h.pair));
                Path path=Path.of(material.reference().path());byte[] raw=Files.readAllBytes(path);
                Files.move(path,path.resolveSibling(path.getFileName()+".original"));Files.write(path,raw);
                assertThrows(Exception.class,()->h.f.materials.loadRetainedOriginal(same,material.kind(),material.witness(),h.pair));return null;
            });
        }
    }

    /** Raw packet/file edge only. This is canonical reducer input, never Managed or a private RestoreBinding. */
    private RestoreCheckpointService.NativeCandidate actualReplacementPacket(Harness h,String suffix)throws Exception {
        var original=h.pair.frame().game();
        var replacement=new GameGeneration(original.pid()+1,new PythonOnlyUInt64(original.creationFiletime().value().add(BigInteger.ONE)));
        byte[] packet=Files.readAllBytes(Path.of(h.request.savedMaterial().sourceSemantic().originalNativePacket().path()));
        var snapshot=(NativeWire.Snapshot)NativeWire.decode(packet);
        var ref=h.f.files.createNew(h.f.actual.root.resolve("replacement-"+suffix+".bin"),packet).reference();
        var frame=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(originalMachine(h),replacement,BigInteger.ONE,"replacement-"+suffix),
                snapshot.snapshotId(),snapshot.revision(),new RawJson(snapshot.state().value()),packet,Instant.now());
        return new RestoreCheckpointService.NativeCandidate(frame,h.ready.source(),h.pair.lineageId(),ref);
    }
    @Test void repeatedCachedRawPacketWithoutOriginalReadIssuerCannotPrepareOrGainRestoreCredit()throws Exception {
        try(var h=actualSaved("cached-restored-packet")) {
            var candidate=actualReplacementPacket(h,"cache");var launches=new AtomicInteger();var observed=new AtomicInteger();
            var service=service(h,new RestoreCheckpointService.LifecyclePort(){
                public RestoreCheckpointService.LaunchResult replaceOnce(RestoreCheckpointService.Request request){
                    launches.incrementAndGet();return new RestoreCheckpointService.ReplacementAck(request.requestId(),h.pair.frame().game(),
                            candidate.actual().session().game(),h.pair.save().reference(),candidate.originalNativePacket());
                }
                public RestoreCheckpointService.LaunchResult query(String id,Instant deadline){throw new AssertionError("retained original ACK must not relaunch");}
            },(ack,reads)->{reads.requireReplacement(ack);observed.incrementAndGet();return candidate;});
            String before=h.f.actual.writer.locked(same->same.head().digest());
            var first=assertInstanceOf(RestoreCheckpointService.Unknown.class,service.restore(h.request));
            assertTrue(first.reason().contains("independent restore READ custody unavailable"),first.reason());
            var later=assertInstanceOf(RestoreCheckpointService.Unknown.class,service.queryOriginal(h.request.requestId(),Instant.now().plusSeconds(30)));
            assertTrue(later.reason().contains("independent restore READ custody unavailable"),later.reason());
            assertEquals(1,launches.get());assertEquals(4,observed.get());
            h.f.actual.writer.locked(same->{assertEquals(before,same.head().digest());assertTrue(service.originalReboundOrigin(same,h.request.requestId()).isEmpty());return null;});
            assertEquals(1,h.f.actual.nativeActionWrites(),"the sole actual software SAVE is unchanged; no private Managed or restoration is fabricated");
        }
    }
    @Test void actualSavedAttachmentKeepsOriginalCyclePhysicalEligibilityAfterGameBindingChanges()throws Exception {
        try(var h=actualSaved("historical-after-attachment",true)){
            var candidate=actualReplacementPacket(h,"historical");
            h.f.actual.writer.locked(same->{
                var material=h.request.savedMaterial();var original=material.session();
                var attachment=h.f.materials.prepare(h.request,candidate,material.savedDriver());
                var small=attachment.request().detailsObject().get(SavedAttachmentSourceStore.SOURCES_DETAIL);
                assertEquals(SavedAttachmentSourceStore.SOURCES_SCHEMA,small.get("schema").textValue());
                assertTrue(attachment.request().evidence().contains(h.pair.save().reference()));
                assertTrue(SavedAttachmentSourceStore.Sources.decode(small).physicalSaveWitness().isEmpty());
                var loadedAttachment=h.f.sources.prepareLoaded(h.request,candidate,material.savedDriver());
                var alwaysWitnessed=loadedAttachment.request().detailsObject().get(SavedAttachmentSourceStore.SOURCES_DETAIL);
                assertEquals(SavedAttachmentSourceStore.SOURCES_SCHEMA_PHYSICAL_SAVE_WITNESS,alwaysWitnessed.get("schema").textValue());
                assertEquals(Optional.of(h.pair.save()),SavedAttachmentSourceStore.Sources.decode(alwaysWitnessed).physicalSaveWitness());
                assertFalse(loadedAttachment.request().evidence().contains(h.pair.save().reference()));
                var prepared=same.preview(attachment.request());var committed=same.commit(prepared);
                assertNotEquals(WriterContracts.Disposition.NO_CHANGE,committed.disposition());
                assertNotEquals(original.game(),candidate.actual().session().game());
                String head=same.head().digest();long sequence=same.head().state().sequence();
                // Current-cycle ownership must remain strict; immutable saved-source eligibility is a separate check.
                assertThrows(Exception.class,()->h.f.batch.cycleProof(same,original,material.sourceSemantic()));
                material.requireRetained(same);material.requirePhysical(same);
                var witness=CheckpointPairCodec.fileWitnessFromJson(CheckpointPairCodec.fileWitnessToJson(material.witness()));
                var loaded=h.f.materials.loadOriginal(same,SavedCheckpointMaterial.Kind.ORDINARY,witness,h.pair);
                assertEquals(original,loaded.session());assertEquals(material.sourceSemantic(),loaded.sourceSemantic());
                assertArrayEquals(material.savedDriver().encode(),loaded.savedDriver().encode());
                assertEquals(material.originalHeadDigest(),loaded.originalHeadDigest());
                assertEquals(h.pair,CheckpointPairCodec.decode(CheckpointPairCodec.encode(loaded.pair())));
                // The live preview loader still rejects an old predecessor. Historical replay is a distinct service-owned path.
                assertThrows(Exception.class,()->h.f.sources.load(prepared.predecessor().state(),prepared.request()));
                assertEquals(head,same.head().digest());assertEquals(sequence,same.head().state().sequence());return null;
            });
            assertEquals(1,h.f.actual.nativeActionWrites(),"no additional SAVE or Managed replacement is fabricated");
        }
    }
    @Test void changedOriginalFileIdentityStillRefusesAfterAnActualAttachment()throws Exception {
        try(var h=actualSaved("attachment-original-identity")){
            var candidate=actualReplacementPacket(h,"identity");
            h.f.actual.writer.locked(same->{
                var material=h.request.savedMaterial();var attachment=h.f.materials.prepare(h.request,candidate,material.savedDriver());
                same.commit(same.preview(attachment.request()));String head=same.head().digest();
                var witness=material.witness();Path path=Path.of(witness.reference().path());byte[] raw=Files.readAllBytes(path);
                Files.move(path,path.resolveSibling(path.getFileName()+".original"));Files.write(path,raw);
                var changed=h.f.files.observe(path).orElseThrow();
                assertEquals(witness.reference(),changed.reference());assertNotEquals(witness.identity(),changed.identity());
                assertThrows(Exception.class,()->material.requireRetained(same));assertThrows(Exception.class,()->material.requirePhysical(same));
                assertThrows(Exception.class,()->h.f.materials.loadOriginal(same,material.kind(),witness,h.pair));
                assertEquals(head,same.head().digest());return null;
            });
            assertEquals(1,h.f.actual.nativeActionWrites());
        }
    }

    @Test void actualOrdinaryBasisUsesSharedPreflightBeforeAnyReplacementAndRejectsStaleDataFrontiers()throws Exception {
        try(var h=actualSaved("ordinary-preflight")){
            var candidate=actualReplacementPacket(h,"preflight");
            h.f.actual.writer.locked(same->{
                String head=same.head().digest();var actual=h.f.materials.prepare(h.request,candidate,h.request.savedMaterial().savedDriver());
                byte[] basis=actual.input().basis();
                assertDoesNotThrow(()->SavedContinuityAttachment.requireOrdinaryPredecessor(same.head().state(),basis));
                // These are explicit negative DATA coordinates, never committed state or a new private source.
                var later=same.head().state().toJson().deepCopy();
                later.put("last_settled_cycles",Math.addExact(same.head().state().settledCycles(),1));
                var stale=ContinuityState.fromJson(later,same.head().state().machineId());
                assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.requireOrdinaryPredecessor(stale,basis));
                var changed=(com.fasterxml.jackson.databind.node.ObjectNode)FullJsonTree.parse(basis,1024*1024);
                var origin=(com.fasterxml.jackson.databind.node.ObjectNode)changed.get("origin");
                origin.put("window_id",Math.addExact(origin.get("window_id").longValue(),1));
                assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.requireOrdinaryPredecessor(
                        same.head().state(),FullJsonTree.encode(changed,1024*1024)));
                var wrongType=(com.fasterxml.jackson.databind.node.ObjectNode)FullJsonTree.parse(basis,1024*1024);
                ((com.fasterxml.jackson.databind.node.ObjectNode)wrongType.get("frame")).put("actor_character_id",true);
                assertThrows(IllegalArgumentException.class,()->SavedContinuityAttachment.requireOrdinaryPredecessor(
                        same.head().state(),FullJsonTree.encode(wrongType,1024*1024)));
                assertEquals(head,same.head().digest());return null;
            });
            assertEquals(1,h.f.actual.nativeActionWrites(),"basis preflight never issues another SAVE or replacement");
        }
    }
    private static String originalMachine(Harness h){return h.pair.frame().machineId();}
}
