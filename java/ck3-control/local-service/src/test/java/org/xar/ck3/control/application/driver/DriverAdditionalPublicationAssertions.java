package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.history.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Mandatory genuine Root input entrypoints. Private Sources/tokens are never fabricated here.
 * Missing actual Root inputs are NOT_RUN, not successful tests or permission to create replacement DTOs. */
public final class DriverAdditionalPublicationAssertions {
    private DriverAdditionalPublicationAssertions(){ }
    public static void returnedRead(Session same,DriverStateAssembler authority,DriverReadHistoryPublisher publisher,
            DriverReturnedPublicReadHistoryMaterial.Source actualSource,DriverReturnedPublicReadHistoryMaterial.OriginalReturned actual)throws Exception{
        var before=known(authority,same);publisher.bindReturnedPublicReadSource(actualSource);
        var queued=assertInstanceOf(DriverReturnedPublicReadHistoryMaterial.Queued.class,publisher.enqueueReturnedPublicRead(same,actual));
        assertEquals(queued,publisher.enqueueReturnedPublicRead(same,actual));publisher.flushActualReads(same).orElseThrow();
        var after=known(authority,same);oneHistory(before,after);
        var row=DriverReturnedPublicReadHistoryRowProducer.decode(after.driver().commandHistory().getLast().originalRow().json());
        assertEquals(queued.originalRow().sha256(),DriverJson.sha256(row.encode()));assertTrue(row.toJson().members().containsKey("result"));assertFalse(row.toJson().members().containsKey("error"));
    }
    public static void returnedAction(Session same,DriverStateAssembler authority,DriverReadHistoryPublisher publisher,
            DriverReturnedActionHistoryRowProducer.Source actualSource,DriverReturnedActionHistoryRowProducer.OriginalReturned actual,ActionReceipt originalUnknown)throws Exception{
        var before=known(authority,same);assertInstanceOf(ActionState.Unknown.class,originalUnknown.state());publisher.bindReturnedActionHistorySource(actualSource);
        var queued=assertInstanceOf(DriverReturnedActionHistoryRowProducer.Queued.class,publisher.enqueueReturnedAction(same,actual));
        assertEquals(queued,publisher.enqueueReturnedAction(same,actual));publisher.flushActualReads(same).orElseThrow();
        var after=known(authority,same);oneHistory(before,after);var row=DriverReturnedActionHistoryRowProducer.decode(after.driver().commandHistory().getLast().originalRow().json());
        assertTrue(row.ok());assertEquals(queued.originalRow().sha256(),DriverJson.sha256(row.encode()));
    }
    public static void earlyCached(Session same,DriverStateAssembler authority,DriverReadHistoryPublisher publisher,
            DriverEarlyExecuteFailure.Source actualSource,DriverEarlyExecuteFailure.OriginalInvocation actual)throws Exception{
        var before=known(authority,same);publisher.bindEarlyExecuteFailureSource(actualSource);
        var queued=assertInstanceOf(DriverEarlyExecuteFailure.Queued.class,publisher.enqueueEarlyExecuteFailure(same,actual));
        assertEquals(queued,publisher.enqueueEarlyExecuteFailure(same,actual));publisher.flushActualReads(same).orElseThrow();
        var after=known(authority,same);oneHistory(before,after);var row=DriverEarlyExecuteFailureRowProducer.decode(after.driver().commandHistory().getLast().originalRow().json());
        assertFalse(row.ok());assertEquals(queued.originalRow().sha256(),DriverJson.sha256(row.encode()));
    }
    public static void earlyAbsent(Session same,DriverStateAssembler authority,DriverReadHistoryPublisher publisher,
            DriverEarlyExecuteFailure.Source actualSource,DriverEarlyExecuteFailure.OriginalInvocation actual)throws Exception{
        var before=authority.withFrozenFacts(same,frozen->frozen.state());String head=same.head().digest();publisher.bindEarlyExecuteFailureSource(actualSource);
        assertInstanceOf(DriverEarlyExecuteFailure.MissingFacts.class,publisher.enqueueEarlyExecuteFailure(same,actual));
        assertFalse(publisher.hasPending(same));assertTrue(publisher.flushActualReads(same).isEmpty());assertEquals(head,same.head().digest());
        authority.withFrozenFacts(same,frozen->{assertSame(before,frozen.state());return null;});
    }
    public static void fullSnapshot(PublicSnapshotCodec.FullSnapshotOriginals actual)throws Exception{
        var rows=OpportunityJson.array(actual.actual().semantic().get("native_command_history"),"actual full history");
        assertTrue(rows.stream().map(value->OpportunityJson.object(value,"actual row")).anyMatch(row->row.members().containsKey(DriverPostKnownReadFailureRowProducer.SOURCE_FIELD)
                ||row.members().containsKey(DriverReturnedPublicReadHistoryRowProducer.SOURCE_FIELD)||row.members().containsKey(DriverReturnedActionHistoryRowProducer.SOURCE_FIELD)
                ||row.members().containsKey(DriverEarlyExecuteFailureRowProducer.SOURCE_FIELD)),"requires an actual newly published finite row");
        var wire=PublicSnapshotCodec.encode(PublicSnapshotCodec.exportFull(actual,true));assertEquals(actual.actual().semantic(),PublicSnapshotCodec.decode(wire));
    }
    private static DriverSnapshotFacts.Known known(DriverStateAssembler authority,Session same)throws java.io.IOException{return authority.withFrozenFacts(same,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));}
    private static void oneHistory(DriverSnapshotFacts.Known before,DriverSnapshotFacts.Known after){
        assertEquals(before.stamp().driverVersion()+1,after.stamp().driverVersion());assertEquals(before.stamp().episodeEpoch(),after.stamp().episodeEpoch());
        assertEquals(before.driver().session(),after.driver().session());assertEquals(before.actionRows(),after.actionRows());assertEquals(before.driver().commandHistory().size()+1,after.driver().commandHistory().size());
        assertTrue(after.observation().isEmpty());assertEquals(OpportunityJson.Nil.INSTANCE,after.auxiliary().get("capability_observed_native_source"));
        assertArrayEquals(after.driver().encode(),DriverStateSnapshot.decodeComplete(after.driver().encode()).encode());
    }
}
