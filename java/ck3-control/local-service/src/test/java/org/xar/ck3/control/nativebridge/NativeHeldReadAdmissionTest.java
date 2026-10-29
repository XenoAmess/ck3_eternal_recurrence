package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.file.Path;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Actual ordinary held-read admission: the typed request never authorizes another Native sample. */
final class NativeHeldReadAdmissionTest {
    @TempDir Path temporary;

    @Test void typedReadBorrowsTheActualLeaseAndRejectsSourceOrSessionDriftBeforeNativeIo() throws Exception {
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve("held-read"),false)){
            actual.writer.locked(same->actual.collector.withOwnedPlanning(same,actual.observationIdentity(),Instant.now().plusSeconds(20),(original,lease)->{
                var request=new PlanningReadRequest(original.before(),original.source(),original.sessionId(),actual.readContract.operation(),new Obj(Map.of()),original.deadline());
                int packets=actual.nativePacketReads(),queries=actual.nativeReadWrites();String head=same.head().digest();
                assertSame(lease,actual.collector.currentHeldRead(same,request,current->current));
                var otherSource=new G2Source(original.source().machineId(),Instant.now().toString(),"other-exact-source",original.source().sourceRef());
                var changedSource=new PlanningReadRequest(request.before(),otherSource,request.sessionId(),request.operation(),request.arguments(),request.deadline());
                assertThrows(IllegalArgumentException.class,()->actual.collector.currentHeldRead(same,changedSource,current->current));
                var changedSession=new PlanningReadRequest(request.before(),request.source(),request.sessionId()+"-other",request.operation(),request.arguments(),request.deadline());
                assertThrows(IllegalArgumentException.class,()->actual.collector.currentHeldRead(same,changedSession,current->current));
                assertEquals(packets,actual.nativePacketReads());assertEquals(queries,actual.nativeReadWrites());assertEquals(head,same.head().digest());return null;
            }));
        }
    }

    @Test void typedReadWithoutAnActualCollectorScopeRefusesInsteadOfRecapturing() throws Exception {
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve("no-held-read"),false)){
            var original=actual.ready().request();int packets=actual.nativePacketReads(),queries=actual.nativeReadWrites();
            var request=new PlanningReadRequest(original.before(),original.source(),original.sessionId(),actual.readContract.operation(),new Obj(Map.of()),Instant.now().plusSeconds(20));
            actual.writer.locked(same->{assertThrows(IllegalArgumentException.class,()->actual.collector.currentHeldRead(same,request,current->current));return null;});
            assertEquals(packets,actual.nativePacketReads());assertEquals(queries,actual.nativeReadWrites());assertEquals(0,actual.nativeActionWrites());
        }
    }
}
