package org.xar.ck3.control.application.driver;
import org.xar.ck3.control.application.history.*;
import org.xar.ck3.control.continuity.writer.WriterContracts;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.atomic.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.history.DriverPostKnownReadFailureMaterial.*;
import org.xar.ck3.control.application.history.DriverPostKnownReadFailureRowProducer.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual writer/publisher/central Known/archive at software packet edges, never an installed Native Army or Managed Root proof. */
final class DriverAdditionalReadPublicationTest {
    @TempDir Path temporary;
    private static final String STEP="query-army-strengths-v1",CAP="game.command.query-army-strengths-v1";
    private static final OperationKey OP=new OperationKey(STEP);
    private record Scenario(Kind kind,boolean fails,boolean hook,AtomicInteger liveCalls,AtomicInteger pureCalls,
            AtomicReference<ReadContract<RawJson>> installed,AtomicReference<DriverReadHistoryPublisher> publisher) {
        private ReadContract<RawJson> contract(ExactRef source){
            var base=new ReadContract<RawJson>("software-post-known-"+kind.name(),OP,Optional.of(CAP),"software-post-known-permission",
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                    (request,id)->new NativeRequest(STEP,Optional.of(CAP),new RawJson(StrictJson.canonical(OpportunityJson.toNode(request.arguments())))),
                    original->{liveCalls.incrementAndGet();return value(original);},DriverAdditionalReadPublicationTest::value)
                    .withOriginalHistoryProjection(DriverReadHistoryRichMaterial.Kind.ARMY_STRENGTHS,(original,replayed)->{throw new AssertionError("not a successful Army projector");});
            if(!hook)return base;
            return base.withPostKnownFailureProjection(kind,(original,replayed,earlier)->{
                StrictJson.require(earlier.size()==kind.requiredEarlierReads(),"actual software peer count required");
                for(var peer:earlier)StrictJson.require(peer.request().source().equals(original.request().source())&&peer.request().sessionId().equals(original.request().sessionId())
                        &&peer.request().before().equals(original.request().before()),"software peer crossed its actual frame");
                pureCalls.incrementAndGet();try{pureCalculation(replayed);return Optional.empty();}
                catch(IllegalStateException computation){return Optional.of(new Failure(kind,computation.getClass().getSimpleName(),computation.getMessage(),List.of(source)));}
            });
        }
        private ActionWriterIntegrationFixture.SoftwareReadScenario nativeScenario(){return new ActionWriterIntegrationFixture.SoftwareReadScenario("a".repeat(64),"software-post-known",
                source->{var actual=contract(source);assertTrue(installed.compareAndSet(null,actual));return List.of(actual);},
                request->new RawJson(StrictJson.canonical(StrictJson.object().put("step",STEP).put("software_failure",fails))));}
    }
    private static Scenario scenario(Kind kind,boolean fails,boolean hook){return new Scenario(kind,fails,hook,new AtomicInteger(),new AtomicInteger(),new AtomicReference<>(),new AtomicReference<>());}
    private static RawJson value(PlanningReadReceipt original){var body=(ObjectNode)StrictJson.parse(original.original().originalFrame().bytes());return new RawJson(StrictJson.canonical(body.get("result")));}
    private static void pureCalculation(RawJson raw){var row=(ObjectNode)StrictJson.parse(raw.bytes());StrictJson.require(row.get("software_failure").isBoolean(),"fixed calculation input required");if(row.get("software_failure").booleanValue())throw new IllegalStateException("fixed software computation failed");}
    private static ReadContract<RawJson> install(ActionWriterIntegrationFixture fixture,Scenario scenario)throws IOException{
        var actual=Objects.requireNonNull(scenario.installed().get());assertSame(actual,fixture.extraReadContracts().getFirst());assertTrue(fixture.actualReadCatalog().containsIdentity(actual));
        var publisher=new DriverReadHistoryPublisher(fixture.driverAuthority(),fixture.archive,fixture.actualReadCatalog(),List.of(actual.sourceRef()));assertTrue(scenario.publisher().compareAndSet(null,publisher));
        fixture.bindKnownReadObserver((same,contract,known)->{if(contract==actual)publisher.enqueue(same,contract,known);});fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_READ_HISTORY_KIND,publisher);return actual;
    }
    private static Set<Path> files(Path root)throws IOException{try(var paths=Files.walk(root)){return paths.filter(Files::isRegularFile).map(path->path.toAbsolutePath().normalize()).collect(java.util.stream.Collectors.toUnmodifiableSet());}}
    @FunctionalInterface private interface Work<T>{T run(ContinuityStorePort.Session same,ActionPorts.OutcomeArchive bound,ActionCommand frame)throws IOException;}
    private static <T>T scope(ActionWriterIntegrationFixture fixture,Work<T> work)throws Exception{
        var frame=fixture.command("software-post-known-frame");return fixture.physicalInputs().transport().withMailbox(frame.deadline(),mailbox->fixture.writer.locked(same->fixture.archive.inSession(same,bound->{
            try{return work.run(same,bound,frame);}catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
        })));
    }
    private static PlanningReadResult.Known<RawJson> read(ActionWriterIntegrationFixture fixture,ContinuityStorePort.Session same,ReadContract<RawJson> contract,ActionCommand frame)throws IOException{
        var request=new PlanningReadRequest(frame.before(),frame.source(),frame.sessionId(),OP,new OpportunityJson.Obj(Map.of()),frame.deadline());
        return switch(fixture.reads.read(same,contract,request)){
            case PlanningReadResult.Known<RawJson> known -> known;
            case PlanningReadResult.Unavailable<RawJson> failed -> throw new AssertionError("actual software read unavailable: "+failed.reason());
        };
    }
    @Test void actualPrivateKnownQueueCommitsOneErrorAndColdReplayDoesNotQueryOrWrite()throws Exception{
        for(var kind:Kind.values()){
            var scenario=scenario(kind,true,true);
            try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve(kind.name()),false,scenario.nativeScenario())){
                var contract=install(fixture,scenario);var rowRef=new AtomicReference<ExactRef>();
                scope(fixture,(same,bound,frame)->{
                    var peers=new ArrayList<PlanningReadResult.Known<?>>();for(int i=0;i<kind.requiredEarlierReads();i++)peers.add(read(fixture,same,contract,frame));
                    var last=read(fixture,same,contract,frame);var publisher=scenario.publisher().get();
                    var copied=new PlanningReadResult.Known<>(last.value(),last.receipt(),last.originalReceipt());
                    assertThrows(IllegalArgumentException.class,()->publisher.enqueuePostKnownFailure(contract,copied,peers));
                    var result=assertInstanceOf(Queued.class,publisher.enqueuePostKnownFailure(contract,last,peers));rowRef.set(result.originalRow());
                    assertEquals(result,publisher.enqueuePostKnownFailure(contract,last,peers));assertTrue(publisher.statusSnapshot().dirty());
                    int queries=fixture.nativeReadWrites();publisher.flushActualReads(same).orElseThrow();
                    assertFalse(publisher.statusSnapshot().dirty());assertFalse(publisher.hasPending(same));
                    var current=fixture.driverAuthority().withFrozenFacts(same,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
                    assertEquals(1,current.driver().commandHistory().size());assertTrue(current.observation().isEmpty());
                    var row=DriverPostKnownReadFailureRowProducer.decode(current.driver().commandHistory().getFirst().originalRow().json());
                    assertEquals(result.originalRow(),bound.materialReferenceOf(new RawJson(row.encode())));assertFalse(row.toJson().has("result"));
                    assertEquals("IllegalStateException: fixed software computation failed",row.error());
                    assertEquals(queries,fixture.nativeReadWrites());assertEquals(1,same.head().state().sequence());return null;
                });
                Set<Path> before=files(fixture.root);byte[] ledger=fixture.ledgerBytes();int queries=fixture.nativeReadWrites();
                fixture.writer.locked(same->{var bound=fixture.archive.withSession(same);var row=DriverPostKnownReadFailureRowProducer.decode(bound.loadMaterial(rowRef.get()).bytes());
                    assertEquals(row,DriverPostKnownReadFailureRowProducer.replayOriginals(same,bound,fixture.actualReadCatalog(),row));return null;});
                assertEquals(before,files(fixture.root));assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(queries,fixture.nativeReadWrites());assertEquals(0,fixture.nativeActionWrites());
            }
        }
    }
}
