package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.registry.FactionAlertReadService.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;
import org.xar.ck3.control.contracts.StrictJson;

/** Finite software packet/process edge; the actual read coordinator issues the private failed-attempt proof.
 * Public boundary tests reuse this producer, rather than constructing QueryFailure or copying an ACK DTO. */
public final class FactionAlertFailureProducerFixture {
    private FactionAlertFailureProducerFixture() { }
    public record NativeRejectedCase(QueryFailure failure,int nativeReads,int nativeActions) { }
    private record Fixture(ActionWriterIntegrationFixture actual,Contracts contracts,AtomicReference<RawJson> payload) implements AutoCloseable {
        @Override public void close()throws IOException{actual.close();}
    }
    private static Fixture fixture(Path root)throws IOException {
        var selected=new AtomicReference<Contracts>();var payload=new AtomicReference<>(new RawJson("{}".getBytes(StandardCharsets.UTF_8)));
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("e".repeat(64),"faction-public-failure-fixture",
                ignored->List.of(),request->payload.get(),Optional.of("1.20.0.4"),Set.of(FactionAlertReadService.CAPABILITY),source->{
                    var contracts=new Contracts(source,source);assertTrue(selected.compareAndSet(null,contracts));return contracts.families();
                });
        var actual=new ActionWriterIntegrationFixture(root,false,scenario);
        return new Fixture(actual,selected.get(),payload);
    }
    private static Context context(Complete frame,java.time.Instant deadline) {
        var semantic=frame.semantic();return new Context(frame.identity(),frame.source(),frame.sessionId(),deadline,
                new SameFrameWars(frame.identity(),new RawJson(OpportunityJson.encode(semantic.get("active_wars")))),
                OpportunityJson.text(semantic.get("backend_id"),"actual fixture backend"));
    }
    private static PlanningReadPort reads(ActionWriterIntegrationFixture actual,Session same) {
        return new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
                return actual.reads.read(same,contract,request);
            }
            @Override public <T> PlanningReadResult<T> readWithFailureEvidence(ReadContract<T> contract,PlanningReadRequest request,
                    PlanningReadPort.FailureEvidenceObserver observer) {
                return actual.reads.readWithFailureEvidence(same,contract,request,observer);
            }
        };
    }
    public static NativeRejectedCase actualNativeRejected(Path root)throws Exception {
        try(var fixture=fixture(root)) {
            var actual=fixture.actual();actual.rejectNextScenarioRead();
            NativeRejectedCase result=actual.writer.locked(same->actual.collector.currentOwned(same,actual.observationIdentity(),java.time.Instant.now().plusSeconds(20),lease->{
                Context current=context(lease.frame(),java.time.Instant.now().plusSeconds(15));
                var service=new FactionAlertReadService(()->current,reads(actual,same),actual.actualReadCatalog(),fixture.contracts());
                QueryFailure failure=assertThrows(QueryFailure.class,()->service.query_player_faction_alerts_v1(new Query(current.before().frame().revision())));
                assertEquals(QueryFailureKind.NATIVE_COMMAND_REJECTED,failure.kind());
                assertEquals("native gameplay step failed: controlled scenario READ rejected",failure.getMessage());
                var original=actual.archive.withSession(same).load(failure.originalCandidate().orElseThrow());
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,original);assertFalse(ack.nativeOk());
                assertEquals(failure.actualRequestId().orElseThrow(),ack.requestId());
                assertEquals(FactionAlertReadService.STEP,actual.archive.withSession(same).loadRequest(failure.preparedCandidate().orElseThrow()).step());
                assertEquals(1,actual.nativeReadWrites());assertEquals(0,actual.nativeActionWrites());
                return new NativeRejectedCase(failure,actual.nativeReadWrites(),actual.nativeActionWrites());
            }));
            assertTrue(actual.sourceChecks.get()>0,"the producer must retain the actual finite source guard");return result;
        }
    }
    public static QueryFailure actualRevisionMismatch(Path root)throws Exception {
        try(var fixture=fixture(root)) {
            var actual=fixture.actual();return actual.writer.locked(same->actual.collector.currentOwned(same,actual.observationIdentity(),java.time.Instant.now().plusSeconds(20),lease->{
                Context current=context(lease.frame(),java.time.Instant.now().plusSeconds(15));
                var service=new FactionAlertReadService(()->current,reads(actual,same),actual.actualReadCatalog(),fixture.contracts());
                BigInteger expected=current.before().frame().revision().add(BigInteger.ONE);
                QueryFailure failure=assertThrows(QueryFailure.class,()->service.query_player_faction_alerts_v1(new Query(expected)));
                assertEquals(QueryFailureKind.BRIDGE_UNAVAILABLE,failure.kind());
                assertEquals("player faction alert revision mismatch: expected "+expected+", current "+current.before().frame().revision(),failure.getMessage());
                assertTrue(failure.originalCandidate().isEmpty());assertTrue(failure.actualRequestId().isEmpty());assertEquals(0,actual.nativeReadWrites());return failure;
            }));
        }
    }
    public static void actualUnknownIsNeverGuessedToBeARejectedCommandOrTimeout(Path root)throws Exception {
        try(var fixture=fixture(root)) {
            var actual=fixture.actual();actual.loseReadAckOnce();
            actual.writer.locked(same->actual.collector.currentOwned(same,actual.observationIdentity(),java.time.Instant.now().plusSeconds(20),lease->{
                Context current=context(lease.frame(),java.time.Instant.now().plusSeconds(15));
                var service=new FactionAlertReadService(()->current,reads(actual,same),actual.actualReadCatalog(),fixture.contracts());
                RuntimeException failure=assertThrows(RuntimeException.class,()->service.query_player_faction_alerts_v1(new Query(current.before().frame().revision())));
                assertFalse(failure instanceof QueryFailure,"an actual post-write receive failure is not typed response-deadline or Native rejection evidence");
                assertEquals(1,actual.nativeReadWrites());assertEquals(0,actual.nativeActionWrites());return null;
            }));
        }
    }
    public static void actualPublicationFailureDoesNotReuseAnEarlierNativeClassification(Path root)throws Exception {
        try(var fixture=fixture(root)) {
            var actual=fixture.actual();actual.bindKnownReadObserver(new PlanningReadCoordinator.KnownReadObserver() {
                @Override public void afterKnown(Session same,ReadContract<?> contract,PlanningReadResult.Known<?> known) { }
                @Override public void afterUnavailable(Session same,ReadContract<?> contract,PlanningReadRequest request,
                        PlanningReadResult.Unavailable<?> unavailable,Optional<PlanningReadCoordinator.FailedReadAttempt> attempted) {
                    throw new IllegalStateException("actual fixed-window publication failed after the original read");
                }
            });
            actual.rejectNextScenarioRead();
            actual.writer.locked(same->actual.collector.currentOwned(same,actual.observationIdentity(),java.time.Instant.now().plusSeconds(20),lease->{
                Context current=context(lease.frame(),java.time.Instant.now().plusSeconds(15));
                var service=new FactionAlertReadService(()->current,reads(actual,same),actual.actualReadCatalog(),fixture.contracts());
                RuntimeException failure=assertThrows(RuntimeException.class,()->service.query_player_faction_alerts_v1(new Query(current.before().frame().revision())));
                assertFalse(failure instanceof QueryFailure,"a changed current result cannot use the old authenticated failure object");
                assertTrue(failure.getMessage().contains("actual fixed-window publication failed after the original read"));
                assertEquals(1,actual.nativeReadWrites());assertEquals(0,actual.nativeActionWrites());return null;
            }));
        }
    }
    public static void actualBusinessUnavailableRemainsANormalCodecReply(Path root)throws Exception {
        try(var fixture=fixture(root)) {
            var actual=fixture.actual();actual.writer.locked(same->actual.collector.currentOwned(same,actual.observationIdentity(),java.time.Instant.now().plusSeconds(20),lease->{
                Context current=context(lease.frame(),java.time.Instant.now().plusSeconds(15));
                fixture.payload().set(businessUnavailable(current.nativeRevision()));
                var service=new FactionAlertReadService(()->current,reads(actual,same),actual.actualReadCatalog(),fixture.contracts());
                Reply reply=service.query_player_faction_alerts_v1(new Query(current.before().frame().revision()));
                assertInstanceOf(FactionAlertModel.Unavailable.class,reply.original().value().frame());
                assertEquals(new OpportunityJson.Text("unavailable"),DriverJson.object(FactionAlertReadService.encode(reply).bytes(),RawJson.MAXIMUM_BYTES).get("status"));
                assertEquals(1,actual.nativeReadWrites());assertEquals(0,actual.nativeActionWrites());return null;
            }));
        }
    }
    private static RawJson businessUnavailable(BigInteger nativeRevision)throws IOException {
        byte[] source;
        try(var input=FactionAlertFailureProducerFixture.class.getResourceAsStream("/factionalerts/original-producer-golden.json")) {
            if(input==null)throw new IOException("selected existing original Faction fixture is absent; this producer test was not executed");source=input.readAllBytes();
        }
        var corpus=StrictJson.parse(source,RawJson.MAXIMUM_BYTES);var frame=(com.fasterxml.jackson.databind.node.ObjectNode)corpus.get("bases").get("unavailable").deepCopy();
        frame.put("snapshot_revision",nativeRevision);
        for(var candidate:corpus.get("cases"))if(candidate.get("name").textValue().equals("exact-build-1.20.0.4"))
            frame.set("provenance",candidate.get("operations").get(0).get("value").deepCopy());
        var result=StrictJson.object().put("step",FactionAlertReadService.STEP).put("accepted",true).put("status","unavailable")
                .put("query_sequence",BigInteger.ONE).put("snapshot_revision",nativeRevision).put("player_faction_alerts_ready",false).put("backend_id","native-headless");
        result.set("player_faction_alerts",frame);return new RawJson(StrictJson.canonical(result,RawJson.MAXIMUM_BYTES));
    }
}
