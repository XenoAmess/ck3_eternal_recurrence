package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionSnapshotReader;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.session.SessionPorts.*;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** Real explicit SAVE -> ordinary boundary -> original material -> actual restore source gate. No Managed grant. */
final class PublicCheckpointMaterialCaptureCompositionTest {
    @TempDir Path temporary;
    private static PublicCheckpointMaterialCapture capture(CheckpointSourceCompositionTest.Fixture f){
        return new PublicCheckpointMaterialCapture(f.actual.writer,f.batch,f.materials,new ActionSnapshotReader(f.actual.journal));
    }
    private static PublicCheckpointMaterialCapture.Pending begin(CheckpointSourceCompositionTest.Fixture f,
            PublicCheckpointMaterialCapture producer)throws IOException{
        return f.actual.writer.locked(same->producer.begin(same,f.owner,f.proof.semantic(),f.request));
    }
    private static final class FiniteClock extends Clock{
        private final AtomicReference<Instant> now=new AtomicReference<>(Instant.now()),afterEntry=new AtomicReference<>();
        public ZoneId getZone(){return ZoneOffset.UTC;}
        public Clock withZone(ZoneId zone){if(!ZoneOffset.UTC.equals(zone))throw new IllegalArgumentException("UTC fixture");return this;}
        public Instant instant(){Instant value=now.get(),next=afterEntry.getAndSet(null);if(next!=null)now.set(next);return value;}
        void expireAfterEntry(Instant deadline){now.set(Instant.now());afterEntry.set(deadline.plusSeconds(1));}
    }
    @Test void actualPublicSaveProducesOriginalMaterialAndTheRealRestoreGateConsumesIt()throws Exception{
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("public-source"),false)){
            var producer=capture(f);var pending=begin(f,producer);
            var saved=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
            var captured=f.actual.writer.locked(same->producer.confirm(same,pending,saved));
            assertTrue(pending.materialConfirmed());assertEquals(saved,pending.confirmedResult().orElseThrow());
            assertEquals(saved.pair(),captured.pair());assertEquals(1,f.actual.nativeActionWrites());
            f.actual.ready();
            var readiness=f.actual.collector.checkpoint("software-save-lineage").observe(Instant.now().plusSeconds(30));
            var request=f.actual.writer.locked(same->{
                captured.requirePhysical(same);var material=producer.currentPhysical(same,Optional.empty());
                assertEquals(captured.material().witness(),material.witness());
                var witness=CheckpointPairCodec.fileWitnessFromJson(CheckpointPairCodec.fileWitnessToJson(material.witness()));
                var loaded=f.materials.loadOriginal(same,material.kind(),witness,material.pair());
                assertArrayEquals(captured.material().savedDriver().encode(),loaded.savedDriver().encode());
                assertEquals(material.originalHeadDigest(),loaded.originalHeadDigest());
                assertEquals(material.pair(),CheckpointPairCodec.decode(CheckpointPairCodec.encode(material.pair())));
                return new RestoreCheckpointService.Request("public-material-restore",material.pair(),readiness,
                        same.head().digest(),Instant.now().plusSeconds(30),loaded);
            });
            var launches=new AtomicInteger();var queries=new AtomicInteger();
            class RealPorts implements RestoreCheckpointService.AttachmentPort,RestoreCheckpointService.PublicationPort{
                public RestoreCheckpointService.Attachment prepare(RestoreCheckpointService.Request actual,
                        RestoreCheckpointService.NativeCandidate nativeFrame,DriverStateSnapshot.Complete full,RestoreCheckpointService.ReadWindow reads)throws IOException{
                    reads.requireOriginal(actual);
                    return f.materials.prepare(actual,nativeFrame,full);
                }
                public RestoreCheckpointService.PublishedDriver publish(RestoreCheckpointService.Request actual,
                        RestoreCheckpointService.NativeCandidate nativeFrame,DriverStateSnapshot.Complete full,
                        WriterContracts.Prepared prepared,WriterContracts.Receipt receipt,RestoreCheckpointService.ReadWindow reads){
                    throw new AssertionError("unresolved lifecycle cannot publish an admitted Driver");
                }
                public void requireCurrent(RestoreCheckpointService.PublishedDriver published,
                        RestoreCheckpointService.NativeCandidate nativeFrame,WriterContracts.Receipt receipt,RestoreCheckpointService.ReadWindow reads){
                    throw new AssertionError("no Managed or post-replacement authority is supplied by this fixture");
                }
            }
            var ports=new RealPorts();
            var restore=new RestoreCheckpointService(f.files,f.drivers,new RestoreCheckpointService.LifecyclePort(){
                public RestoreCheckpointService.LaunchResult replaceOnce(RestoreCheckpointService.Request original){
                    launches.incrementAndGet();assertSame(request,original);
                    return new RestoreCheckpointService.LaunchUnknown("controlled replacement outcome remains unresolved");
                }
                public RestoreCheckpointService.LaunchResult query(String originalId,Instant deadline){
                    queries.incrementAndGet();assertEquals(request.requestId(),originalId);
                    return new RestoreCheckpointService.LaunchUnknown("query the same actual restore attempt");
                }
            },(ack,reads)->{throw new AssertionError("UNKNOWN lifecycle has no replacement Native packet");},
                    f.actual.writer,f.materials,ports,ports,Clock.systemUTC());
            assertInstanceOf(RestoreCheckpointService.Unknown.class,restore.restore(request));
            assertInstanceOf(RestoreCheckpointService.Unknown.class,restore.restore(request));
            assertEquals(1,launches.get());assertEquals(1,queries.get());assertEquals(1,f.actual.nativeActionWrites());
        }
    }
    @Test void lateOriginalSaveRetainsOnePendingAndRepeatedConfirmationAddsNoBoundary()throws Exception{
        var clock=new FiniteClock();
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("public-late"),false,clock)){
            var producer=capture(f);var pending=begin(f,producer);
            clock.expireAfterEntry(f.request.saveCommand().deadline());
            var original=assertInstanceOf(CheckpointResult.Unknown.class,f.service.checkpoint(f.request));
            assertFalse(pending.materialConfirmed());assertTrue(pending.confirmedResult().isEmpty());
            var saved=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.queryOriginal(original.actionId(),clock.instant().plusSeconds(30)));
            f.actual.writer.locked(same->{
                var captured=producer.confirm(same,pending,saved);String head=same.head().digest();
                assertSame(captured,producer.confirm(same,pending,saved));assertEquals(head,same.head().digest());
                assertEquals(captured.pair(),producer.currentPhysical(same,Optional.empty()).pair());return null;
            });
            assertEquals(1,f.actual.nativeActionWrites());assertTrue(pending.materialConfirmed());
        }
    }
    @Test void foreignCaptureAndPhysicalDriftCannotQualifyOrSilentlyChooseAControllerPair()throws Exception{
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("public-invalid"),false)){
            var producer=capture(f);var other=capture(f);var pending=begin(f,producer);
            var saved=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
            f.actual.writer.locked(same->{
                String head=same.head().digest();
                assertThrows(IllegalArgumentException.class,()->other.confirm(same,pending,saved));
                assertEquals(head,same.head().digest());return null;
            });
            Files.writeString(Path.of(saved.pair().save().reference().path()),"actual physical source changed before the public boundary");
            f.actual.writer.locked(same->{
                String head=same.head().digest();
                assertThrows(Exception.class,()->producer.confirm(same,pending,saved));
                assertTrue(pending.confirmedResult().isPresent());assertFalse(pending.materialConfirmed());
                assertThrows(IOException.class,()->producer.currentPhysical(same,Optional.of(saved.pair())));
                assertThrows(IOException.class,()->producer.confirm(same,pending,saved));
                assertEquals(head,same.head().digest());return null;
            });
            assertEquals(1,f.actual.nativeActionWrites());
        }
    }
    @Test void genuinelyLaterControllerSaveWinsOverTheNowReplacedPublicPhysicalPair()throws Exception{
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("public-then-controller"),false)){
            var producer=capture(f);var pending=begin(f,producer);
            var first=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
            var captured=f.actual.writer.locked(same->producer.confirm(same,pending,first));
            var before=f.actual.ready();var proof=f.batch.cycleProof(f.owner,before.semanticEvidence().orElseThrow()).orElseThrow();
            var observations=f.actual.collector.checkpoint("software-save-lineage");
            var next=new CheckpointRequestFactory(Path.of(first.pair().save().reference().path()),observations)
                    .prepare(before.request().before(),before.request().source(),f.owner.sessionId(),Optional.of(first.pair()),Instant.now().plusSeconds(30));
            // Controlled file edge preserves the first original, then the genuine second native write creates a different FileID.
            Path old=Path.of(first.pair().save().reference().path());Files.move(old,old.resolveSibling("first-original.ck3"));
            var second=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(next));
            f.batch.commit(new JournalInput(f.owner,"actual-controller-after-public",JournalKind.SAVE_CONFIRMED,
                    Optional.of(second.pair().frame()),Optional.of(second.pair()),Optional.of(proof),
                    List.of(second.pair().save().reference(),second.pair().driver().reference(),second.pair().nativeAckRef())));
            f.actual.writer.locked(same->{
                assertThrows(Exception.class,()->captured.requirePhysical(same));
                var selected=producer.currentPhysical(same,Optional.of(second.pair()));
                assertEquals(second.pair(),selected.pair());selected.requirePhysical(same);return null;
            });
            assertEquals(2,f.actual.nativeActionWrites(),"two distinct explicit actions; UNKNOWN was never replayed");
        }
    }
    @Test void privateCaptureQualifiesOnlyItsOriginalJournalOwnerAndUnchangedPhysicalFrontier()throws Exception{
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("adopt-original"),false);
                var foreign=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("adopt-foreign"),false)){
            var producer=capture(f);var pending=begin(f,producer);
            var saved=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
            var captured=f.actual.writer.locked(same->producer.confirm(same,pending,saved));
            assertArrayEquals(org.xar.ck3.control.application.action.ActionCodec.encodeCommand(f.request.saveCommand()),
                    org.xar.ck3.control.application.action.ActionCodec.encodeCommand(captured.originalCommand()));
            f.actual.writer.locked(same->{
                String head=same.head().digest();
                assertSame(captured.journalCommit(),captured.requireAdoption(same,f.owner,f.batch));
                assertSame(captured.journalCommit(),captured.requireAdoption(same,f.owner,f.batch));
                var wrongOwner=new SessionIdentity(f.owner.machineId(),f.owner.game(),"foreign-owned-session");
                assertThrows(IllegalArgumentException.class,()->captured.requireAdoption(same,wrongOwner,f.batch));
                assertThrows(IllegalArgumentException.class,()->captured.requireAdoption(same,f.owner,foreign.batch));
                assertEquals(head,same.head().digest());return null;
            });
            foreign.actual.writer.locked(same->{
                assertThrows(Exception.class,()->captured.requireAdoption(same,f.owner,f.batch));return null;
            });
            Files.writeString(Path.of(saved.pair().save().reference().path()),"genuine captured material physically changed");
            f.actual.writer.locked(same->{
                String head=same.head().digest();
                assertThrows(Exception.class,()->captured.requireAdoption(same,f.owner,f.batch));
                assertEquals(head,same.head().digest());return null;
            });
            assertEquals(1,f.actual.nativeActionWrites());assertEquals(0,foreign.actual.nativeActionWrites());
        }
    }
}
