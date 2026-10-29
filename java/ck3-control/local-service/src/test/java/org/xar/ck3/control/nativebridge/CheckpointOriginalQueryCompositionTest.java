package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
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
        final AtomicReference<Instant> afterNextRead=new AtomicReference<>();
        @Override public ZoneId getZone(){return ZoneOffset.UTC;}
        @Override public Clock withZone(ZoneId zone){
            if(!ZoneOffset.UTC.equals(zone))throw new IllegalArgumentException("software deadline clock remains UTC");
            return this;
        }
        @Override public Instant instant(){
            Instant observed=now.get();Instant next=afterNextRead.getAndSet(null);
            if(next!=null)now.set(next);return observed;
        }
        void expireAfterOriginalEntry(Instant originalDeadline){
            now.set(Instant.now());afterNextRead.set(originalDeadline.plusSeconds(1));
        }
    }
    @Test void lateOriginalPositiveAckProducesSameCanonicalPairAndMaterialWithoutSecondSave()throws Exception {
        var clock=new FiniteClock();
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("positive-original"),false,clock)){
            Instant originalDeadline=f.request.saveCommand().deadline();
            byte[] body=ActionCodec.encodeCommand(f.request.saveCommand());
            clock.expireAfterOriginalEntry(originalDeadline);
            var unknown=assertInstanceOf(CheckpointResult.Unknown.class,f.service.checkpoint(f.request));
            var retained=unknown.action().orElseThrow();
            assertFalse(retained.settled(),"first actual stable-file observation remains pending");
            assertEquals(1,f.actual.nativeActionWrites());
            assertFalse(clock.instant().isBefore(originalDeadline));
            Instant readDeadline=clock.instant().plusSeconds(30);
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,
                    f.service.queryOriginal(unknown.actionId(),readDeadline));
            assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,confirmed.action().outcome());
            assertArrayEquals(body,ActionCodec.encodeCommand(confirmed.action().command()));
            assertEquals(originalDeadline,confirmed.action().command().deadline());
            assertEquals(retained.bodySha256(),confirmed.action().bodySha256());
            assertEquals(unknown.actionId(),confirmed.pair().saveActionId());
            assertTrue(f.lastCheckpointObservationDeadline.get().isAfter(originalDeadline),
                    "the real poststate collector must receive the central original-action read window");
            assertFalse(f.lastCheckpointObservationDeadline.get().isAfter(readDeadline));
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
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("missing-ack"),true,clock)){
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
    @Test void sourceDriftAfterConfirmationCannotBeRequalifiedByAReadWindow()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("changed-source"),false)){
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
            Files.writeString(Path.of(confirmed.pair().save().reference().path()),"actual later physical SAVE bytes");
            var result=assertInstanceOf(CheckpointResult.Unknown.class,
                    f.service.queryOriginal(confirmed.pair().saveActionId(),Instant.now().plusSeconds(30)));
            assertTrue(result.action().isPresent());
            assertEquals(1,f.actual.nativeActionWrites());
        }
    }
}
