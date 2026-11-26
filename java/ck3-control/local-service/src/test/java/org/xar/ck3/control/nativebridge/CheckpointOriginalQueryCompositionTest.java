package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.lifecycle.SeedAdoption;

/** Software packet/file edges use the real SAVE, action ledger, poststate, material and pair consumers. */
final class CheckpointOriginalQueryCompositionTest {
    @TempDir Path temporary;
    private static final class FiniteClock extends Clock {
        final AtomicReference<Instant> now=new AtomicReference<>(Instant.now());
        final AtomicReference<Instant> afterRead=new AtomicReference<>();
        final AtomicInteger readsToAdvance=new AtomicInteger();
        @Override public ZoneId getZone(){return ZoneOffset.UTC;}
        @Override public Clock withZone(ZoneId zone){
            if(!ZoneOffset.UTC.equals(zone))throw new IllegalArgumentException("software deadline clock remains UTC");
            return this;
        }
        @Override public Instant instant(){
            Instant observed=now.get();
            if(readsToAdvance.get()>0&&readsToAdvance.decrementAndGet()==0)now.set(afterRead.getAndSet(null));
            return observed;
        }
        void expireAfterOriginalEntry(Instant originalDeadline){
            now.set(Instant.now());advanceAfterReads(1,originalDeadline.plusSeconds(1));
        }
        void advanceAfterReads(int reads,Instant target){
            afterRead.set(target);readsToAdvance.set(reads);
        }
    }
    private CheckpointSourceCompositionTest.Fixture fixture(String directory,boolean loseAck,Clock clock)throws Exception {
        Path root=temporary.resolve(directory);
        return new CheckpointSourceCompositionTest.Fixture(root,loseAck,clock,Optional.empty(),Optional.empty(),List.of(),
                Duration.ofSeconds(90),root.resolve("profile"),Optional.empty(),
                Optional.of(CheckpointSourceCompositionTest.freshReconciliationReads()));
    }
    @Test void lateOriginalPositiveAckProducesSameCanonicalPairAndMaterialWithoutSecondSave()throws Exception {
        var clock=new FiniteClock();
        try(var f=fixture("positive-original",false,clock)){
            Instant originalDeadline=f.request.saveCommand().deadline();
            byte[] body=ActionCodec.encodeCommand(f.request.saveCommand());
            clock.expireAfterOriginalEntry(originalDeadline);
            var unknown=assertInstanceOf(CheckpointResult.Unknown.class,f.service.checkpoint(f.request));
            var retained=unknown.action().orElseThrow();
            assertFalse(retained.settled(),"first actual stable-file observation remains pending");
            assertEquals(1,f.actual.nativeActionWrites());
            assertFalse(clock.instant().isBefore(originalDeadline));
            Instant readDeadline=clock.instant().plusSeconds(30);
            Instant originalObservationDeadline=f.lastCheckpointObservationDeadline.get();
            int originalFreshWrites=f.actual.softwareFreshWrites179();
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,
                    f.service.queryOriginal(unknown.actionId(),readDeadline));
            assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,confirmed.action().outcome());
            assertArrayEquals(body,ActionCodec.encodeCommand(confirmed.action().command()));
            assertEquals(originalDeadline,confirmed.action().command().deadline());
            assertEquals(retained.bodySha256(),confirmed.action().bodySha256());
            assertEquals(unknown.actionId(),confirmed.pair().saveActionId());
            assertEquals(originalFreshWrites+1,f.actual.softwareFreshWrites179(),
                    "late original reconciliation uses the actual independent Fresh source");
            assertEquals(originalObservationDeadline,f.lastCheckpointObservationDeadline.get(),
                    "held reconciliation must not fall back to a second generic poststate observation");
            assertInstanceOf(SeedAdoption.Available.class,confirmed.seedAdoption());
            f.drivers.verify(confirmed.pair());
            assertEquals(confirmed.pair(),CheckpointPairCodec.decode(CheckpointPairCodec.encode(confirmed.pair())));
            var full=f.drivers.readVerified(confirmed.pair());
            assertEquals(confirmed.pair().historyIndex(),full.commandHistory().size());
            var canonical=f.actual.writer.locked(same->f.actual.archive.withSession(same).receiptReferenceOf(confirmed.action()));
            f.actual.writer.locked(same->{
                assertEquals(confirmed.action(),f.actual.archive.withSession(same).loadReceipt(canonical));return null;
            });
            f.saveBoundary(confirmed.pair());
            f.actual.writer.locked(same->{
                var material=f.sources.load(confirmed.pair());
                material.requireRetained(same);
                assertEquals(confirmed.pair(),material.pair());
                assertArrayEquals(full.encode(),material.savedDriver().encode());return null;
            });
            var again=assertInstanceOf(CheckpointResult.Confirmed.class,
                    f.service.queryOriginal(unknown.actionId(),clock.instant().plusSeconds(30)));
            assertEquals(confirmed.pair(),again.pair());assertEquals(confirmed.action(),again.action());
            assertArrayEquals(full.encode(),f.drivers.readVerified(confirmed.pair()).encode());
            assertEquals(1,f.actual.nativeActionWrites(),"query cannot execute another native SAVE");
        }
    }
    @Test void absentAckStaysUnknownAndForeignOrExpiredQueriesCannotCreateAnAttempt()throws Exception {
        var clock=new FiniteClock();
        try(var f=fixture("missing-ack",true,clock)){
            clock.expireAfterOriginalEntry(f.request.saveCommand().deadline());
            var original=assertInstanceOf(CheckpointResult.Unknown.class,f.service.checkpoint(f.request));
            Instant fresh=clock.instant().plusSeconds(30);
            var queried=assertInstanceOf(CheckpointResult.Unknown.class,f.service.queryOriginal(original.actionId(),fresh));
            assertEquals(original.actionId(),queried.actionId());
            assertArrayEquals(ActionCodec.encodeCommand(f.request.saveCommand()),
                    ActionCodec.encodeCommand(queried.action().orElseThrow().command()));
            assertFalse(Files.exists(f.actual.root.resolve("saved-driver.json")));
            String head=f.actual.writer.locked(same->same.head().digest());
            assertInstanceOf(CheckpointResult.Unknown.class,f.service.queryOriginal("foreign-unissued-save",fresh));
            assertInstanceOf(CheckpointResult.Unknown.class,f.service.queryOriginal(original.actionId(),clock.instant()));
            assertEquals(head,f.actual.writer.locked(same->same.head().digest()),
                    "foreign and expired query windows cannot append canonical events");
            assertEquals(1,f.actual.nativeActionWrites());
        }
    }
    @Test void warmOriginalQueryExpiresAfterReconciliationWithoutChangingTheSavedReceipt()throws Exception {
        var clock=new FiniteClock();
        try(var f=fixture("warm-expiry",false,clock)){
            var original=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
            f.saveBoundary(original.pair());
            var cutoff=clock.instant().plusSeconds(5);
            String head=f.actual.writer.locked(same->same.head().digest());
            // Entry and the post-reconciliation check are inside the window. Pair and seed work follow.
            clock.advanceAfterReads(2,cutoff);
            var expired=assertInstanceOf(CheckpointResult.Unknown.class,
                    f.service.queryOriginal(original.pair().saveActionId(),cutoff));
            assertEquals(cutoff,clock.instant());
            assertTrue(expired.reason().contains("read window expired"),expired.reason());
            assertEquals(original.action(),expired.action().orElseThrow());
            assertExactRetained(f,original,head);
            var later=assertInstanceOf(CheckpointResult.Confirmed.class,
                    f.service.queryOriginal(original.pair().saveActionId(),cutoff.plusSeconds(20)));
            assertEquals(original.action(),later.action());assertEquals(original.pair(),later.pair());
            assertExactRetained(f,original,head);
        }
    }

    @Test void coldOriginalQueryExpiresAtFinalPhysicalVerificationWithoutChangingTheSavedReceipt()throws Exception {
        var clock=new FiniteClock();
        try(var f=fixture("cold-expiry",false,clock)){
            var original=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
            f.saveBoundary(original.pair());
            String head=f.actual.writer.locked(same->same.head().digest());
            Instant cutoff=clock.instant().plusSeconds(5);
            var expiry=new AtomicReference<>(cutoff);
            var ackVerifications=new AtomicInteger();
            var files=new CheckpointFiles(){
                @Override public Optional<CheckpointPair.FileWitness> observe(Path path)throws IOException{return f.files.observe(path);}
                @Override public byte[] read(CheckpointPair.FileWitness file,int limit)throws IOException{return f.files.read(file,limit);}
                @Override public void verify(CheckpointPair.FileWitness file)throws IOException{
                    f.files.verify(file);
                    if(file.reference().equals(original.pair().nativeAckRef())){
                        ackVerifications.incrementAndGet();
                        var at=expiry.getAndSet(null);if(at!=null)clock.now.set(at);
                    }
                }
                @Override public CheckpointPair.FileWitness replace(Path path,byte[] bytes){return fail("cold query attempted a file replace");}
                @Override public CheckpointPair.FileWitness createNew(Path path,byte[] bytes){return fail("cold query attempted a file create");}
                @Override public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness file,Path target){return fail("cold query attempted a file copy");}
            };
            var cold=new CheckpointService(files,f.drivers,deadline->fail("cold confirmed query attempted a native observation"),
                    f.actual.root.resolve("cold-query-evidence"),clock,f.seedLink);
            cold.bindEvidence(f.actual.archive,f.actual.writer::borrowedSession,f.actual.writer::requireSession);
            cold.bindColdRecovery(Path.of(original.pair().save().reference().path()),original.pair().lineageId());
            cold.bindOriginalCollection(work->f.actual.writer.locked(work::collect));
            var expired=assertInstanceOf(CheckpointResult.Unknown.class,cold.queryOriginal(original.pair().saveActionId(),cutoff));
            assertEquals(1,ackVerifications.get());assertEquals(cutoff,clock.instant());
            assertTrue(expired.reason().contains("read window expired"),expired.reason());
            assertEquals(original.action(),expired.action().orElseThrow());
            assertExactRetained(f,original,head);
            var later=assertInstanceOf(CheckpointResult.Confirmed.class,
                    cold.queryOriginal(original.pair().saveActionId(),cutoff.plusSeconds(20)));
            assertEquals(original.action(),later.action());assertEquals(original.pair(),later.pair());
            assertEquals(2,ackVerifications.get());assertExactRetained(f,original,head);
        }
    }

    private static void assertExactRetained(CheckpointSourceCompositionTest.Fixture f,
            CheckpointResult.Confirmed original,String head)throws IOException {
        f.drivers.verify(original.pair());
        assertEquals(1,f.actual.nativeActionWrites());
        f.actual.writer.locked(same->{
            assertEquals(head,same.head().digest());
            var archive=f.actual.archive.withSession(same);
            assertEquals(original.action(),archive.loadReceipt(archive.receiptReferenceOf(original.action())));
            return null;
        });
    }

    @Test void sourceDriftAfterConfirmationCannotBeRequalifiedByAReadWindow()throws Exception {
        try(var f=fixture("changed-source",false,Clock.systemUTC())){
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
            Files.writeString(Path.of(confirmed.pair().save().reference().path()),"actual later physical SAVE bytes");
            var result=assertInstanceOf(CheckpointResult.Unknown.class,
                    f.service.queryOriginal(confirmed.pair().saveActionId(),Instant.now().plusSeconds(30)));
            assertTrue(result.action().isPresent());
            assertEquals(1,f.actual.nativeActionWrites());
        }
    }
}
