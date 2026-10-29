package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.effects.RootPlanningReadGuard;
import org.xar.ck3.control.application.readiness.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.capabilities.governance.PrivateCouncilReads;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Genuine software transport/Driver/collector/Root guard; this fixture grants no Game qualification. */
final class RootPlanningHeldSourceRetentionTest {
    @TempDir Path temporary;
    private static final String CAPABILITY="game.query.held-source-retention";

    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(boolean council,AtomicReference<ReadContract<?>> selected) {
        return new ActionWriterIntegrationFixture.SoftwareReadScenario("7".repeat(64),"held-source-retention",source->{
            if(council) {
                var reads=new PrivateCouncilReads(source);selected.set(reads.gates());return reads.registeredContracts();
            }
            var operation=new OperationKey("query-held-source-retention");
            var contract=new ReadContract<RawJson>("held-source-retention/v1",operation,Optional.of(CAPABILITY),"held-source-retention",
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                    (request,id)->new NativeRequest(operation.value(),CAPABILITY,new RawJson("{}".getBytes(StandardCharsets.UTF_8))),
                    receipt->receipt.original().originalResultToken().orElseThrow(),receipt->receipt.original().originalResultToken().orElseThrow());
            selected.set(contract);return List.of(contract);
        },request->new RawJson("{}".getBytes(StandardCharsets.UTF_8)),Optional.of("1.20.0.2"),Set.of(CAPABILITY));
    }

    @Test void changedCodeFileDoesNotBlockActualHeldOriginalAndOriginalHistory() throws Exception {
        var selected=new AtomicReference<ReadContract<?>>();
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve("held-changed-code"),false,scenario(false,selected))) {
            actual.ready();var probe=new Probe(actual);var contract=selected.get();var guard=guard(actual,probe);
            int packets=actual.nativePacketReads(),queries=actual.nativeReadWrites();
            actual.writer.locked(same->{
                var retained=contract.sourceRef();assertEquals(actual.observationSource().sourceRef(),retained);
                Files.writeString(Path.of(retained.path()),"changed installed CODE only",StandardOpenOption.TRUNCATE_EXISTING);
                return probe.collector.withHeldReadScope(same,actual.observationIdentity(),Instant.now().plusSeconds(20),frame->{
                    var request=request(frame.identity(),frame.source(),frame.sessionId(),contract);
                    String head=same.head().digest();int checks=probe.dataChecks.get();
                    PlanningReadGuard result;
                    try { result=guard.verifyOriginalCurrent(same.head(),request,contract); }
                    catch(UncheckedIOException obsoleteGate) {
                        assertTrue(hasCodeExactFailure(obsoleteGate),"baseline must fail the retained code file, not Native DATA");
                        assertEquals(checks,probe.dataChecks.get(),"obsolete code gate precedes real held authority");throw obsoleteGate;
                    }
                    assertTrue(probe.dataChecks.get()>checks);requireOriginal(actual,same,result,frame.identity());
                    assertEquals(head,same.head().digest());return null;
                });
            });
            assertEquals(packets,actual.nativePacketReads());assertEquals(queries,actual.nativeReadWrites());assertEquals(0,actual.nativeActionWrites());
        }
    }

    @Test void missingCodeFileDoesNotBlockCouncilPhysicalScopeOrItsHeldGuard() throws Exception {
        var selected=new AtomicReference<ReadContract<?>>();
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve("council-missing-code"),false,scenario(true,selected))) {
            var ready=actual.ready().request();var probe=new Probe(actual);var contract=selected.get();var guard=guard(actual,probe);
            var request=request(ready.before(),ready.source(),ready.sessionId(),contract);
            int packets=actual.nativePacketReads(),queries=actual.nativeReadWrites();var entered=new AtomicInteger();
            actual.writer.locked(same->{
                assertEquals(contract.sourceRef(),actual.observationSource().sourceRef());Files.delete(Path.of(contract.sourceRef().path()));
                var lockedHead=same.head();String head=lockedHead.digest();
                try {
                    assertEquals(1,guard.withOriginalReadSource(lockedHead,request,contract,()->{
                        entered.incrementAndGet();
                        var result=guard.verifyOriginalCurrent(lockedHead,request,contract);
                        try { requireOriginal(actual,same,result,request.before()); }
                        catch(IOException failure) { throw new UncheckedIOException(failure); }
                        assertThrows(IllegalArgumentException.class,()->guard.withOriginalReadSource(lockedHead,request,contract,()->null));
                        return 1;
                    }));
                } catch(UncheckedIOException obsoleteGate) {
                    assertTrue(hasCodeExactFailure(obsoleteGate),"baseline must fail missing retained code, not Native DATA");
                    assertEquals(0,entered.get());throw obsoleteGate;
                }
                assertEquals(head,same.head().digest());
                assertThrows(IllegalArgumentException.class,()->guard.verifyOriginalCurrent(same.head(),request,contract));return null;
            });
            assertEquals(1,entered.get());assertTrue(probe.dataChecks.get()>0);
            assertEquals(packets,actual.nativePacketReads());assertEquals(queries,actual.nativeReadWrites());assertEquals(0,actual.nativeActionWrites());
        }
    }

    @Test void heldAuthorityStillRejectsForeignObjectsExpiredRequestsEscapesAndUnavailableDataWitness() throws Exception {
        var selected=new AtomicReference<ReadContract<?>>();
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve("held-controls"),false,scenario(false,selected))) {
            actual.ready();var probe=new Probe(actual);var contract=selected.get();var guard=guard(actual,probe);
            var escaped=new AtomicReference<PlanningReadRequest>();int packets=actual.nativePacketReads(),queries=actual.nativeReadWrites();
            actual.writer.locked(same->{
                probe.collector.withHeldReadScope(same,actual.observationIdentity(),Instant.now().plusSeconds(20),frame->{
                    var request=request(frame.identity(),frame.source(),frame.sessionId(),contract);escaped.set(request);
                    assertNotNull(guard.verifyOriginalCurrent(same.head(),request,contract));
                    var clone=ActionWriterIntegrationFixture.contract(contract.sourceRef());
                    assertThrows(IllegalArgumentException.class,()->guard.verifyOriginalCurrent(same.head(),request,clone));
                    var wrongSession=new PlanningReadRequest(request.before(),request.source(),request.sessionId()+"-other",request.operation(),request.arguments(),request.deadline());
                    assertThrows(IllegalArgumentException.class,()->guard.verifyOriginalCurrent(same.head(),wrongSession,contract));
                    var source=request.source();var changed=new G2Source(source.machineId(),Instant.now().toString(),"other-source",source.sourceRef());
                    var wrongSource=new PlanningReadRequest(request.before(),changed,request.sessionId(),request.operation(),request.arguments(),request.deadline());
                    assertThrows(IllegalArgumentException.class,()->guard.verifyOriginalCurrent(same.head(),wrongSource,contract));
                    var expired=new PlanningReadRequest(request.before(),source,request.sessionId(),request.operation(),request.arguments(),Instant.now().minusSeconds(1));
                    assertThrows(IllegalArgumentException.class,()->guard.verifyOriginalCurrent(same.head(),expired,contract));
                    int checks=probe.dataChecks.get();probe.dataValid.set(false);
                    var denied=assertThrows(UncheckedIOException.class,()->guard.verifyOriginalCurrent(same.head(),request,contract));
                    assertTrue(denied.getCause().getMessage().contains("actual held DATA witness unavailable"));assertTrue(probe.dataChecks.get()>checks);
                    probe.dataValid.set(true);assertNotNull(guard.verifyOriginalCurrent(same.head(),request,contract));return null;
                });
                assertThrows(IllegalArgumentException.class,()->guard.verifyOriginalCurrent(same.head(),escaped.get(),contract));return null;
            });
            assertEquals(packets,actual.nativePacketReads());assertEquals(queries,actual.nativeReadWrites());assertEquals(0,actual.nativeActionWrites());
        }
    }

    @Test void actualNativeAndSemanticArchiveBytesRemainRequiredInsideHeldScope() throws Exception {
        for(boolean nativePacket:List.of(true,false)) {
            var selected=new AtomicReference<ReadContract<?>>();
            try(var actual=new ActionWriterIntegrationFixture(temporary.resolve(nativePacket?"native-data":"semantic-data"),false,scenario(false,selected))) {
                actual.ready();var probe=new Probe(actual);var contract=selected.get();var guard=guard(actual,probe);
                int packets=actual.nativePacketReads(),queries=actual.nativeReadWrites();
                actual.writer.locked(same->probe.collector.withHeldReadScope(same,actual.observationIdentity(),Instant.now().plusSeconds(20),frame->{
                    var request=request(frame.identity(),frame.source(),frame.sessionId(),contract);
                    var verified=guard.verifyOriginalCurrent(same.head(),request,contract);
                    var data=nativePacket?frame.originalEvidence():RootGuardEvidence.semanticReference(verified.binding(),actual.archive.withSession(same));
                    Files.write(Path.of(data.path()),"changed actual DATA".getBytes(StandardCharsets.UTF_8),StandardOpenOption.TRUNCATE_EXISTING);
                    int checks=probe.dataChecks.get();String head=same.head().digest();
                    assertThrows(UncheckedIOException.class,()->guard.verifyOriginalCurrent(same.head(),request,contract));
                    assertTrue(probe.dataChecks.get()>checks);assertEquals(head,same.head().digest());return null;
                }));
                assertEquals(packets,actual.nativePacketReads());assertEquals(queries,actual.nativeReadWrites());assertEquals(0,actual.nativeActionWrites());
            }
        }
    }

    private static PlanningReadRequest request(org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before,
            G2Source source,String session,ReadContract<?> contract) {
        return new PlanningReadRequest(before,source,session,contract.operation(),new Obj(Map.of()),Instant.now().plusSeconds(15));
    }
    private static void requireOriginal(ActionWriterIntegrationFixture actual,ContinuityStorePort.Session same,PlanningReadGuard result,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity expected) throws IOException {
        assertTrue(result.paused()&&result.mapReady()&&result.playerAlive());assertEquals(expected,result.binding().observed());
        assertEquals(actual.observationSource(),result.binding().source());
        RootGuardEvidence.requireHistory(result.binding(),actual.archive.withSession(same),same);
        assertEquals(expected,RootGuardEvidence.loadFrame(result.binding(),actual.archive.withSession(same),actual.frameLoader()).identity());
    }
    private static RootPlanningReadGuard guard(ActionWriterIntegrationFixture actual,Probe probe) {
        return new RootPlanningReadGuard(probe.collector,()->{
            try { return actual.writer.borrowedSession(); }catch(IOException failure) { throw new UncheckedIOException(failure); }
        },actual.archive,actual.observationSource(),Clock.systemUTC(),"held-code-retention-regression",actual.physicalInputs().originals(),actual.actualReadCatalog());
    }
    private static boolean hasCodeExactFailure(Throwable failure) {
        for(Throwable current=failure;current!=null;current=current.getCause()) {
            if(Arrays.stream(current.getStackTrace()).anyMatch(frame->frame.getClassName().endsWith("RootGuardChecks")&&frame.getMethodName().equals("source")))return true;
        }
        return false;
    }
    private static final class Probe {
        final NativeReadinessCollector collector;
        final AtomicBoolean dataValid=new AtomicBoolean(true);
        final AtomicInteger dataChecks=new AtomicInteger();
        Probe(ActionWriterIntegrationFixture actual) {
            var physical=actual.physicalInputs();
            collector=new NativeReadinessCollector(actual.observationIdentity(),actual.writer,physical.transport(),physical.driverAssembler(),physical.observationAssembler(),
                    (game,deadline)->new GameLifecycle.Running(game,physical.source().sourceRef()),
                    (same,role,bytes)->actual.archive.preserveArtifact(same,bytes,role.maximumBytes()),
                    new NativeSemanticEvidenceVerifier((same,ref,maximum)->actual.archive.readArtifact(same,ref,maximum)),
                    (same,identity,frame,known,received,process,deadline)->{
                        actual.writer.requireSession(same);assertEquals(actual.observationIdentity(),identity);assertEquals(physical.source(),frame.source());
                        assertEquals(identity.game(),process.measured());
                        ExactRef proof=actual.archive.preserveArtifact(same,"{\"schema\":\"fixture.actual-held-data/v1\",\"received\":true}".getBytes(StandardCharsets.UTF_8),65_536);
                        var pin=same.capturePin(proof,65_536);same.verifyPin(pin);
                        return new NativeReadinessCollector.SourceQualification(proof,borrowed->{
                            assertSame(same,borrowed);actual.writer.requireSession(borrowed);borrowed.verifyPin(pin);dataChecks.incrementAndGet();
                            if(!dataValid.get())throw new IOException("actual held DATA witness unavailable");
                        });
                    },(same,frame,known,received,deadline)->{throw new AssertionError("held scope cannot collect ordinary executable capabilities");},
                    (same,frame,known,received,deadline)->{throw new AssertionError("held scope cannot collect planning inputs");},
                    new NativeReadiness.Policy(false,false,Optional.of(BigInteger.valueOf(73)),Duration.ZERO,false),Duration.ofSeconds(30),Clock.systemUTC());
            collector.bindObservationSession(actual.writer::requireSession);collector.bindActiveObservationSession(actual.writer::activeSession);
            collector.bindReadyPublication((same,request,frame,known,source)->{throw new AssertionError("held scope cannot publish Ready");});
        }
    }
}
