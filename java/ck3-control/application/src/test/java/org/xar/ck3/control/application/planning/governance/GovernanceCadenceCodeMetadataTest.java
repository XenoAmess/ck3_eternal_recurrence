package org.xar.ck3.control.application.planning.governance;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.optionalcadence.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceFixtures.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Component software values; reaches the real publication/import producer, no physical writer or Game. */
final class GovernanceCadenceCodeMetadataTest {
    private static final ExactRef CODE=new ExactRef("missing-old-MB/RootOrdinaryRuntimeAssembly.class",19394,"8".repeat(64));
    private static final ExactRef READ=new ExactRef("unit-actual-read-receipt.json",17,"2".repeat(64));
    private static ExactRef ref(String path,byte[] bytes) {return new ExactRef(path,bytes.length,ActionCodec.sha256(bytes));}
    private static final class Fixture implements ContinuityStorePort.Session {
        final byte[] before=CadenceJson.writeState(CadenceModels.State.empty("unit-episode"));
        final org.xar.ck3.control.g2.common.G2Source source=new org.xar.ck3.control.g2.common.G2Source(SOURCE.machineId(),NOW.toString(),SOURCE.exactBuild(),CODE);
        final GovernanceCadencePublication.Plan plan=new GovernanceCadencePublication.Plan(identity(9),source,"unit-session",CadenceModels.State.empty("unit-episode"),List.of(CadenceModels.Domain.FEAST));
        final DomainBodies.BodyRef body=new DomainBodies.BodyRef(DomainBodies.Slot.OPTIONAL_CADENCE,CadenceModels.SCHEMA,
                ref("unit-cadence-before.json",before),new FileIdentity("1","2","3",NOW.toString(),before.length),List.of(CODE));
        final Path lock=Path.of("unit-cadence.lock").toAbsolutePath().normalize();
        ContinuityState state;byte[] materialBefore=before;DomainBodies.ImportRequest prepared;
        boolean failBody,failSession;int bodyReads,previewCalls,writerChecks;
        Fixture() {
            var row=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",SOURCE.machineId())
                    .put("sequence",0).put("window_id",1).put("status","running").put("start_date_raw",100)
                    .put("target_days",1).put("target_date_raw",124).put("last_settled_cycles",0).put("last_settled_date_raw",100);
            state=DomainBodies.reduceImport(ContinuityState.fromJson(row,SOURCE.machineId()),body);
        }
        GovernanceCadencePublication publication() {
            return new GovernanceCadencePublication(lock,same->{assertSame(this,same);if(failSession)throw new IOException("actual session unavailable");},List.of(CODE),
                    (head,previous,requested,evidence)->{
                        assertEquals(body,previous);assertEquals(plan,requested);assertEquals(List.of(READ),evidence);
                        bodyReads++;if(failBody)throw new IOException("actual previous-body IO failed");
                        return new GovernanceCadencePublication.Material(materialBefore,plan,evidence);
                    },(id,bytes)->ref("unit-next-cadence.json",bytes));
        }
        @Override public void requireWriter(Path actual) {assertEquals(lock,actual);writerChecks++;}
        @Override public Head head() {return new Head(state,List.of(),List.of(),List.of(),false);}
        @Override public ExactRef persistedHead() {return REF;}
        @Override public DomainBodies.Read readDomain(DomainBodies.Slot slot) {assertEquals(DomainBodies.Slot.OPTIONAL_CADENCE,slot);return new DomainBodies.Available(body,before,REF,List.of());}
        @Override public DomainBodies.PreparedImport previewImport(DomainBodies.ImportRequest request)throws IOException {
            previewCalls++;prepared=request;throw new IOException("actual-preview-boundary");
        }
        @Override public Pin capturePin(ExactRef ignored,int maximum) {throw new AssertionError("publication must not source-audit code");}
        @Override public void verifyPin(Pin ignored) {throw new AssertionError("publication must not source-audit code");}
        @Override public Prepared preview(Request ignored) {throw new AssertionError("domain path only");}
        @Override public Receipt commit(Prepared ignored) {throw new AssertionError("test stops before writes");}
    }
    @Test void historicalCodeStaysRecordedButOnlyBodyAndReadReceiptReachImport() throws Exception {
        var fixture=new Fixture();var publication=fixture.publication();
        var stopped=assertThrows(IOException.class,()->publication.publish(fixture,fixture.plan,List.of(READ)));
        assertEquals("actual-preview-boundary",stopped.getMessage());assertEquals(1,fixture.previewCalls);
        assertEquals(List.of(fixture.body.payload(),READ),fixture.prepared.evidence());
        assertFalse(fixture.prepared.evidence().contains(CODE));
        assertEquals(CODE,fixture.plan.source().sourceRef());assertEquals(List.of(CODE),publication.registration().producerSources());
        assertTrue(new String(fixture.prepared.producerInput(),java.nio.charset.StandardCharsets.UTF_8).contains(CODE.path()));
        var after=CadenceJson.writeState(GovernanceCadencePublication.reduce(fixture.plan));
        assertNotNull(publication.verify(fixture.head(),Optional.of(fixture.body),fixture.prepared,after));
        assertEquals(1,GovernanceCadencePublication.reduce(fixture.plan).row(CadenceModels.Domain.FEAST).consecutiveNoAction());
    }
    @Test void materialMismatchStillFailsBeforeImport() {
        var fixture=new Fixture();fixture.materialBefore="{}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class,()->fixture.publication().publish(fixture,fixture.plan,List.of(READ)));
        assertEquals(0,fixture.previewCalls);
    }
    @Test void wrongCurrentHeadStillFailsBeforeMaterialRead() {
        var fixture=new Fixture();var row=fixture.state.toJson();row.remove(DomainBodies.FIELD);
        fixture.state=ContinuityState.fromJson(row,SOURCE.machineId());
        assertThrows(IllegalArgumentException.class,()->fixture.publication().publish(fixture,fixture.plan,List.of(READ)));
        assertEquals(0,fixture.bodyReads);assertEquals(0,fixture.previewCalls);
    }
    @Test void actualBodyIoAndBorrowedSessionFailuresStillPropagate() {
        for(boolean sessionFailure:List.of(false,true)) {
            var fixture=new Fixture();fixture.failSession=sessionFailure;fixture.failBody=!sessionFailure;
            var error=assertThrows(IOException.class,()->fixture.publication().publish(fixture,fixture.plan,List.of(READ)));
            assertTrue(error.getMessage().contains(sessionFailure?"session unavailable":"body IO failed"));
            assertEquals(0,fixture.previewCalls);assertEquals(sessionFailure?0:1,fixture.bodyReads);
        }
    }
}
