package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReconciliationScope;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Real SAVE/reconciliation/Store publication; the test decorates only the actual Store's consumer edge. */
final class CheckpointFrozenDriverPublicationTest {
    @TempDir Path temporary;

    private static final class FiniteClock extends Clock {
        private final AtomicReference<Instant> now=new AtomicReference<>(Instant.now());
        private final AtomicReference<Instant> afterEntry=new AtomicReference<>();
        @Override public ZoneId getZone(){return ZoneOffset.UTC;}
        @Override public Clock withZone(ZoneId zone){
            if(!ZoneOffset.UTC.equals(zone))throw new IllegalArgumentException("software SAVE clock remains UTC");
            return this;
        }
        @Override public Instant instant(){
            Instant original=now.get();Instant next=afterEntry.getAndSet(null);
            if(next!=null)now.set(next);return original;
        }
        void expireAfterEntry(Instant deadline){now.set(Instant.now());afterEntry.set(deadline.plusSeconds(1));}
    }

    private static DriverSnapshotFacts.Known known(CheckpointSourceCompositionTest.Fixture fixture){
        try {
            return fixture.actual.driverAuthority().withFrozenFacts(fixture.actual.writer.borrowedSession(),
                    frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
        }catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private static DriverStateSnapshot.Complete changed(DriverStateSnapshot.Complete actual,Obj document){
        var decoded=DriverStateSnapshot.decodeComplete(DriverJson.encode(document));
        assertNotEquals(DriverJson.object(actual.encode(),DriverCheckpointStore.MAX_DRIVER_BYTES),document);
        return decoded;
    }
    private static Obj document(DriverStateSnapshot.Complete actual){
        return DriverJson.object(actual.encode(),DriverCheckpointStore.MAX_DRIVER_BYTES);
    }
    private static List<DriverStateSnapshot.Complete> invalidReplacements(DriverStateSnapshot.Complete actual){
        Obj original=document(actual);var invalid=new ArrayList<DriverStateSnapshot.Complete>();
        invalid.add(changed(actual,original.with("episode_character_id",new IntegerValue(actual.session().actorId().add(BigInteger.ONE)))));
        invalid.add(changed(actual,original.with("campaign_goal",new Obj(Map.of("tampered",new Bool(true))))));
        var history=new ArrayList<>(array(original.get("command_history"),"history"));
        Obj last=object(history.getLast(),"actual SAVE row");
        Obj foreign=object(original.get("last_checkpoint"),"checkpoint").with("java_action_id",new Text("another-original-save"));
        history.set(history.size()-1,last.with("result",object(last.get("result"),"result").with("checkpoint",foreign)));
        invalid.add(changed(actual,original.with("last_checkpoint",foreign).with("command_history",new Arr(history))));
        var twice=new ArrayList<>(array(original.get("command_history"),"history"));
        twice.add(last.with("index",new IntegerValue(BigInteger.valueOf(twice.size()+1L))));
        invalid.add(changed(actual,original.with("command_history",new Arr(twice))));
        return List.copyOf(invalid);
    }

    @Test void originalPositiveAckAllowsExactlyOneStoreCasAndRejectsOtherReplacementsInsideThatSameRawScope()throws Exception {
        var clock=new FiniteClock();var armed=new AtomicBoolean();
        var fixture=new AtomicReference<CheckpointSourceCompositionTest.Fixture>();
        var before=new AtomicReference<DriverSnapshotFacts.Known>();var after=new AtomicReference<DriverSnapshotFacts.Known>();
        var rejected=new AtomicInteger();var publications=new AtomicInteger();var secondOpenings=new AtomicInteger();
        CheckpointSourceCompositionTest.SnapshotSupplierDecorator decorate=actual->new DriverCheckpointStore.SnapshotSupplier(){
            @Override public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work)throws IOException {
                return actual.withFrozen((snapshot,publisher)->work.run(snapshot,(expected,replacement)->{
                    if(!armed.get()){publisher.publish(expected,replacement);return;}
                    var f=fixture.get();assertNotNull(f);assertTrue(ActionReconciliationScope.activeFor(f.request.saveCommand()));
                    var opening=known(f);before.set(opening);assertTrue(opening.observation().isPresent());
                    String head=f.actual.writer.borrowedSession().head().digest();
                    for(var invalid:invalidReplacements(replacement)){
                        assertThrows(IllegalArgumentException.class,()->publisher.publish(expected,invalid));
                        assertSame(opening,known(f));assertEquals(head,f.actual.writer.borrowedSession().head().digest());
                        rejected.incrementAndGet();
                    }
                    publisher.publish(expected,replacement);publications.incrementAndGet();
                    var committed=known(f);after.set(committed);
                    assertNotSame(opening,committed);
                    assertEquals(opening.stamp().driverVersion()+1,committed.stamp().driverVersion());
                    assertEquals(opening.stamp().episodeEpoch(),committed.stamp().episodeEpoch());
                    assertEquals(opening.stamp().game(),committed.stamp().game());
                    assertEquals(opening.driver().session(),committed.driver().session());
                    assertEquals(opening.auxiliary(),committed.auxiliary());
                    assertTrue(committed.observation().isEmpty(),"old completed semantic facts cannot be attached to the published Driver");
                    assertArrayEquals(replacement.encode(),committed.driver().encode());
                    assertEquals(head,f.actual.writer.borrowedSession().head().digest());
                    assertThrows(IllegalArgumentException.class,()->publisher.publish(expected,replacement));
                    assertSame(committed,known(f));rejected.incrementAndGet();
                }));
            }
        };
        CheckpointSourceCompositionTest.AfterPostcondition inspect=(command,attempt,dispatch,result)->{
            if(!armed.get()||!(result instanceof ActionPorts.EffectObserved))return;
            var f=fixture.get();assertTrue(ActionReconciliationScope.activeFor(command));var committed=known(f);
            assertSame(after.get(),committed);var entered=new AtomicInteger();
            assertThrows(IllegalArgumentException.class,()->f.actual.driverAuthority().withFrozen((snapshot,publisher)->{
                entered.incrementAndGet();return snapshot;
            }));
            assertEquals(0,entered.get());assertSame(committed,known(f));secondOpenings.incrementAndGet();
        };
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("one-original-cas"),false,clock,
                Optional.of(decorate),Optional.of(inspect))){
            fixture.set(f);clock.expireAfterEntry(f.request.saveCommand().deadline());
            var original=assertInstanceOf(CheckpointResult.Unknown.class,f.service.checkpoint(f.request));
            assertEquals(1,f.actual.nativeActionWrites());assertFalse(Files.exists(f.actual.root.resolve("saved-driver.json")));
            armed.set(true);
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,
                    f.service.queryOriginal(original.actionId(),clock.instant().plusSeconds(30)));
            assertEquals(1,publications.get());assertEquals(5,rejected.get());assertEquals(1,secondOpenings.get());
            assertEquals(before.get().driver().commandHistory().size()+1,after.get().driver().commandHistory().size());
            assertEquals(original.actionId(),confirmed.pair().saveActionId());f.drivers.verify(confirmed.pair());
            assertArrayEquals(after.get().driver().encode(),f.drivers.readVerified(confirmed.pair()).encode());
            assertEquals(1,f.actual.nativeActionWrites(),"read reconciliation cannot submit another SAVE");
        }
    }

    @Test void originalWithoutAckCannotEvenOpenTheCheckpointPublisherInsideItsActualRawReconciliation()throws Exception {
        var clock=new FiniteClock();var armed=new AtomicBoolean();var checks=new AtomicInteger();
        var fixture=new AtomicReference<CheckpointSourceCompositionTest.Fixture>();
        CheckpointSourceCompositionTest.AfterPostcondition inspect=(command,attempt,dispatch,result)->{
            if(!armed.get())return;
            assertInstanceOf(ActionPorts.Pending.class,result);assertTrue(ActionReconciliationScope.activeFor(command));
            try {
                var f=fixture.get();var before=known(f);var entered=new AtomicInteger();String head=f.actual.writer.borrowedSession().head().digest();
                assertThrows(IllegalArgumentException.class,()->f.actual.driverAuthority().withFrozen((snapshot,publisher)->{
                    entered.incrementAndGet();return snapshot;
                }));
                assertEquals(0,entered.get());assertSame(before,known(f));assertEquals(head,f.actual.writer.borrowedSession().head().digest());
                checks.incrementAndGet();
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        };
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("no-original-ack"),true,clock,
                Optional.empty(),Optional.of(inspect))){
            fixture.set(f);clock.expireAfterEntry(f.request.saveCommand().deadline());
            var original=assertInstanceOf(CheckpointResult.Unknown.class,f.service.checkpoint(f.request));armed.set(true);
            assertInstanceOf(CheckpointResult.Unknown.class,f.service.queryOriginal(original.actionId(),clock.instant().plusSeconds(30)));
            assertEquals(1,checks.get());assertFalse(Files.exists(f.actual.root.resolve("saved-driver.json")));
            assertEquals(1,f.actual.nativeActionWrites());
        }
    }
}
