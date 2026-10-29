package org.xar.ck3.control.application.history;

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
final class DriverPostKnownReadFailureRowProducerTest {
    @TempDir Path temporary;
    private static final String STEP="query-army-strengths-v1",CAP="game.command.query-army-strengths-v1";
    private static final OperationKey OP=new OperationKey(STEP);
    private record Scenario(Kind kind,boolean fails,boolean hook,AtomicInteger liveCalls,AtomicInteger pureCalls,
            AtomicReference<ReadContract<RawJson>> installed,AtomicReference<DriverReadHistoryPublisher> publisher) {
        private ReadContract<RawJson> contract(ExactRef source){
            var base=new ReadContract<RawJson>("software-post-known-"+kind.name(),OP,Optional.of(CAP),"software-post-known-permission",
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                    (request,id)->new NativeRequest(STEP,Optional.of(CAP),new RawJson(StrictJson.canonical(OpportunityJson.toNode(request.arguments())))),
                    original->{liveCalls.incrementAndGet();return value(original);},DriverPostKnownReadFailureRowProducerTest::value)
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
        fixture.bindKnownReadObserver((same,contract,known)->{if(contract==actual)publisher.enqueue(same,contract,known);});return actual;
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
    private static Candidate prepare(ActionWriterIntegrationFixture fixture,Scenario scenario,ContinuityStorePort.Session same,ActionPorts.OutcomeArchive bound,
            ReadContract<RawJson> contract,PlanningReadResult.Known<RawJson> last,List<? extends PlanningReadResult.Known<?>> peers)throws IOException{
        return fixture.driverAuthority().withFrozenFacts(same,frozen->{var before=(DriverSnapshotFacts.Known)frozen.state();return DriverPostKnownReadFailureRowProducer.prepare(same,bound,fixture.actualReadCatalog(),
                fixture.driverAuthority(),scenario.publisher().get(),contract,last,peers,before,before.driver().commandHistory().size()+1L,List.of(contract.sourceRef()));});
    }
    @Test void actualKnownCustodyRetainsCompletePredecessorAndOneErrorRowWithColdZeroWrites()throws Exception{
        for(var kind:Kind.values()){
            var scenario=scenario(kind,true,true);try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve(kind.name()),false,scenario.nativeScenario())){
                var contract=install(fixture,scenario);Candidate candidate=scope(fixture,(same,bound,frame)->{
                    var peers=new ArrayList<PlanningReadResult.Known<?>>();for(int i=0;i<kind.requiredEarlierReads();i++)peers.add(read(fixture,same,contract,frame));
                    var last=read(fixture,same,contract,frame);byte[] ledger=fixture.ledgerBytes();Set<Path> before=files(fixture.root);int reads=fixture.nativeReadWrites(),live=scenario.liveCalls().get();
                    var actual=prepare(fixture,scenario,same,bound,contract,last,peers);var row=actual.row();assertEquals(STEP,row.command());assertFalse(row.ok());assertFalse(row.toJson().has("result"));
                    assertEquals("IllegalStateException: fixed software computation failed",row.error());assertSame(last,actual.finalKnown());assertSame(contract,actual.identicalFinal());assertEquals(kind,row.source().failure().kind());
                    assertEquals(row,DriverPostKnownReadFailureRowProducer.decode(row.encode()));assertArrayEquals(row.encode(),actual.historyEntry().originalRow().json());
                    Set<Path> archived=files(fixture.root);assertTrue(archived.containsAll(before));assertTrue(archived.size()-before.size()<=4,"at most real Known plus row artifact pairs");
                    var decoded=DriverSnapshotFacts.decodeKnownOriginal(bound.loadFullMaterial(actual.beforeKnownReference()),actual.before().observation());assertArrayEquals(actual.before().driver().encode(),decoded.driver().encode());
                    assertSame(actual,DriverPostKnownReadFailureRowProducer.replay(same,bound,fixture.actualReadCatalog(),fixture.driverAuthority(),scenario.publisher().get(),contract,last,peers,actual));
                    assertEquals(archived,files(fixture.root));assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(reads,fixture.nativeReadWrites());assertEquals(live,scenario.liveCalls().get());return actual;
                });
                Set<Path> archived=files(fixture.root);byte[] ledger=fixture.ledgerBytes();int reads=fixture.nativeReadWrites();fixture.writer.locked(same->{
                    assertEquals(candidate.row(),DriverPostKnownReadFailureRowProducer.replayOriginals(same,fixture.archive.withSession(same),fixture.actualReadCatalog(),candidate.row()));return null;});
                assertEquals(archived,files(fixture.root));assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(reads,fixture.nativeReadWrites());assertEquals(0,fixture.nativeActionWrites());
            }
        }
    }
    @Test void missingHookNoFailureWrongPeersAndCopiedKnownRejectBeforeAnyNewArtifact()throws Exception{
        for(var scenario:List.of(scenario(Kind.ARMY_EXPLICIT_PROJECT,true,false),scenario(Kind.ARMY_EXPLICIT_PROJECT,false,true),scenario(Kind.ARMY_AUTO_CORE_COMPARE,true,true))){
            try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("deny-"+scenario.kind()+scenario.fails()+scenario.hook()),false,scenario.nativeScenario())){
                var contract=install(fixture,scenario);scope(fixture,(same,bound,frame)->{var last=read(fixture,same,contract,frame);Set<Path> before=files(fixture.root);byte[] ledger=fixture.ledgerBytes();int reads=fixture.nativeReadWrites();
                    assertThrows(RuntimeException.class,()->prepare(fixture,scenario,same,bound,contract,last,List.of()));var copied=new PlanningReadResult.Known<>(last.value(),last.receipt(),last.originalReceipt());int pure=scenario.pureCalls().get();
                    assertThrows(RuntimeException.class,()->prepare(fixture,scenario,same,bound,contract,copied,List.of()));assertEquals(pure,scenario.pureCalls().get(),"copied DATA must fail private custody before fixed calculation");assertEquals(before,files(fixture.root));assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(reads,fixture.nativeReadWrites());return null;});
                assertEquals(0,fixture.nativeActionWrites());
            }
        }
    }
    @Test void closedSerdeRejectsResultWrongTypesForeignCommandAndUnknownSourceFields()throws Exception{
        var scenario=scenario(Kind.ARMY_EXPLICIT_PROJECT,true,true);try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("serde"),false,scenario.nativeScenario())){
            var contract=install(fixture,scenario);Candidate candidate=scope(fixture,(same,bound,frame)->prepare(fixture,scenario,same,bound,contract,read(fixture,same,contract,frame),List.of()));var row=candidate.row().toJson();var invalid=new ArrayList<ObjectNode>();
            var result=row.deepCopy();result.putNull("result");invalid.add(result);var command=row.deepCopy();command.put("command","compare-army-core-control");invalid.add(command);var ok=row.deepCopy();ok.put("ok",0);invalid.add(ok);var missing=row.deepCopy();missing.remove("error");invalid.add(missing);
            var kind=row.deepCopy();((ObjectNode)kind.get(DriverPostKnownReadFailureRowProducer.SOURCE_FIELD).get("failure")).put("kind","NATIVE_FAILED_ATTEMPT");invalid.add(kind);
            var extra=row.deepCopy();((ObjectNode)extra.get(DriverPostKnownReadFailureRowProducer.SOURCE_FIELD)).put("caller_qualification",true);invalid.add(extra);var generation=row.deepCopy();((ObjectNode)generation.get(DriverPostKnownReadFailureRowProducer.SOURCE_FIELD)).put("connection_generation",1.0);invalid.add(generation);
            for(var bad:invalid)assertThrows(RuntimeException.class,()->DriverPostKnownReadFailureRowProducer.decode(StrictJson.canonical(bad,RawJson.MAXIMUM_BYTES)));
            var empty=row.deepCopy();((ObjectNode)empty.get(DriverPostKnownReadFailureRowProducer.SOURCE_FIELD).get("failure")).put("message","");empty.put("error","IllegalStateException: ");assertEquals("",DriverPostKnownReadFailureRowProducer.decode(StrictJson.canonical(empty,RawJson.MAXIMUM_BYTES)).source().failure().message());
            assertThrows(RuntimeException.class,()->DriverReadHistoryRowProducer.decode(candidate.row().encode()));assertThrows(RuntimeException.class,()->DriverExecuteQueryHistoryRowProducer.decode(candidate.row().encode()));
        }
    }
    @Test void coldLocalPermissionAndCorruptOriginalRejectWithoutReplacement()throws Exception{
        var scenario=scenario(Kind.ARMY_EXPLICIT_PROJECT,true,true);try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("cold"),false,scenario.nativeScenario())){
            var contract=install(fixture,scenario);Candidate candidate=scope(fixture,(same,bound,frame)->prepare(fixture,scenario,same,bound,contract,read(fixture,same,contract,frame),List.of()));var changed=candidate.row().toJson();
            ((ObjectNode)changed.get(DriverPostKnownReadFailureRowProducer.SOURCE_FIELD).get("final_read")).put("permission_key","foreign-local-key");var foreign=DriverPostKnownReadFailureRowProducer.decode(StrictJson.canonical(changed,RawJson.MAXIMUM_BYTES));Set<Path> archived=files(fixture.root);byte[] ledger=fixture.ledgerBytes();int reads=fixture.nativeReadWrites();
            fixture.writer.locked(same->{assertThrows(RuntimeException.class,()->DriverPostKnownReadFailureRowProducer.replayOriginals(same,fixture.archive.withSession(same),fixture.actualReadCatalog(),foreign));return null;});
            Path original=Path.of(candidate.source().before().manifest().path());Files.write(original,new byte[]{1,2,3});fixture.writer.locked(same->{assertThrows(Exception.class,()->DriverPostKnownReadFailureRowProducer.replayOriginals(same,fixture.archive.withSession(same),fixture.actualReadCatalog(),candidate.row()));return null;});
            assertArrayEquals(new byte[]{1,2,3},Files.readAllBytes(original));assertEquals(archived,files(fixture.root));assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(reads,fixture.nativeReadWrites());assertEquals(0,fixture.nativeActionWrites());
        }
    }
}
