package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.normalexit.NormalExitProtocol;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real catalog/guard/coordinator/transport/writer/archive edges. Software route DATA never qualifies a live Game or normal exit. */
final class GuardedReadContractWriterTest {
    @TempDir Path directory;
    private static final OperationKey OP=new OperationKey("fixture-two-issued-read-contexts");
    private static final String CAP="game.query.two-issued-read-contexts";
    @Test void twoAlreadyIssuedSameOperationContractsUseTheirActualGuardIdentityAndArchiveTheirOwnDecoder()throws Exception{
        var family=new AtomicReference<RootReadContractCatalog.Family<String,RawJson>>();
        try(var fixture=fixture("two-issued",family)){
            var ready=fixture.ready();var a=fixture.reads.catalog().issue(family.get(),"A");var b=fixture.reads.catalog().issue(family.get(),"B");
            assertNotSame(a,b);assertEquals(a.operation(),b.operation());
            assertEquals(2,fixture.reads.catalog().contracts().stream().filter(value->value.operation().equals(OP)).count());
            var deadline=Instant.now().plusSeconds(20);
            fixture.writer.locked(same->fixture.collector.current(same,ready.request().before(),deadline,lease->{
                String head=same.head().digest();int initial=fixture.scenarioReadWrites();
                var ar=known(fixture.reads.read(same,a,request(fixture,ready.request().before(),a,"A",deadline)));
                var br=known(fixture.reads.read(same,b,request(fixture,ready.request().before(),b,"B",deadline)));
                assertEquals("fixture-context-A/v1",ar.receipt().contractId());assertEquals("fixture-context-B/v1",br.receipt().contractId());
                assertEquals(ar.receipt(),fixture.archive.withSession(same).loadRead(ar.originalReceipt()));
                assertEquals(br.receipt(),fixture.archive.withSession(same).loadRead(br.originalReceipt()));
                assertEquals("A",StrictJson.parse(ar.value().bytes()).get("echo_variant").textValue());
                assertEquals("B",StrictJson.parse(br.value().bytes()).get("echo_variant").textValue());
                assertEquals(initial+2,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());assertEquals(head,same.head().digest());
                int writes=fixture.scenarioReadWrites(),packets=fixture.nativePacketReads();
                var invalid=fixture.reads.read(same,a,request(fixture,ready.request().before(),a,"B",deadline));
                assertInstanceOf(PlanningReadResult.Unavailable.class,invalid);assertEquals(writes,fixture.scenarioReadWrites());assertEquals(packets,fixture.nativePacketReads());
                var foreign=contract(fixture.observationSource().sourceRef(),"A");
                assertThrows(IllegalArgumentException.class,()->fixture.reads.read(same,foreign,request(fixture,ready.request().before(),foreign,"A",deadline)));
                assertEquals(writes,fixture.scenarioReadWrites());assertEquals(packets,fixture.nativePacketReads());return null;
            }));
        }
    }
    @Test void twoIssuedContractsRetainTheOriginalAUnknownAndAdoptItsLateAckWithoutBOrAnotherNativeQuery()throws Exception{
        var family=new AtomicReference<RootReadContractCatalog.Family<String,RawJson>>();
        try(var fixture=fixture("late-two-issued",family)){
            fixture.loseReadAckOnce();var ready=fixture.ready();
            var a=fixture.reads.catalog().issue(family.get(),"A");fixture.reads.catalog().issue(family.get(),"B");
            var original=request(fixture,ready.request().before(),a,"A",Instant.now().plusSeconds(1));
            var attempted=fixture.journal.locked(same->fixture.reads.readOriginal(same.writerSession(),a,original));
            var unavailable=assertInstanceOf(PlanningReadResult.Unavailable.class,attempted.result());
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,unavailable.original().orElseThrow());
            var retained=attempted.original().orElseThrow();assertEquals(retained.requestId(),unknown.requestId());assertEquals(1,fixture.scenarioReadWrites());
            long delay=Duration.between(Instant.now(),original.deadline().plusMillis(30)).toMillis();if(delay>0)Thread.sleep(delay+1);
            fixture.releaseLateReadAck();fixture.physicalInputs().transport().observe(Instant.now().plusSeconds(5));
            fixture.writer.locked(same->{
                var ack=fixture.reads.pollOriginal(same,retained).orElseThrow();assertEquals(retained.requestId(),ack.requestId());
                assertTrue(ack.custody().isPresent());assertArrayEquals(unknown.originalRequestPacket(),ack.outbound().orElseThrow().originalPacket());
                return fixture.collector.withHeldReadScope(same,fixture.observationIdentity(),Instant.now().plusSeconds(10),frame->{
                    int writes=fixture.scenarioReadWrites(),reads=fixture.nativePacketReads();String head=same.head().digest();
                    var current=request(fixture,frame.identity(),a,"A",Instant.now().plusSeconds(5));
                    var adopted=known(fixture.reads.adoptOriginal(same,retained,ack,current,frame.semantic()));
                    assertEquals(a.contractId(),adopted.receipt().contractId());assertEquals("A",StrictJson.parse(adopted.value().bytes()).get("echo_variant").textValue());
                    assertEquals(adopted.receipt(),fixture.archive.withSession(same).loadRead(adopted.originalReceipt()));
                    assertEquals(adopted,known(fixture.reads.adoptOriginal(same,retained,ack,current,frame.semantic())));
                    assertEquals(head,same.head().digest());assertEquals(writes,fixture.scenarioReadWrites());assertEquals(reads,fixture.nativePacketReads());assertEquals(0,fixture.nativeActionWrites());return null;
                });
            });
        }
    }
    @Test void actualFiniteReadAndActionSelectorsShareTheirOriginalWireStepWithoutCrossingKindsOrReportingExit()throws Exception{
        var query=NativeStepDiscriminator.NormalExit.QUERY_CONTEXT;var prepare=NativeStepDiscriminator.NormalExit.PREPARE_CONFIRMATION;
        var readContract=new AtomicReference<ReadContract<RawJson>>();var dispatches=new AtomicInteger();
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"finite-selector-software-edge",source->{
            ReadContract<RawJson> actual=new ReadContract<>("fixture-normal-exit-query/v1",query.operationKey(),Optional.of(query.capability()),query.capability(),
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                    (request,id)->normalRequest(request.before(),source,id,NormalExitProtocol.Action.QUERY_CONTEXT),receipt->receipt.original().originalResultToken().orElseThrow());
            readContract.set(actual);return List.of(actual);
        },request->{assertEquals(query.nativeStep(),request.step());assertEquals("query_context",StrictJson.parse(request.additionalFields().bytes()).get("action").textValue());return raw("{\"fixture_selector\":\"query_context\"}");});
        var action=new ActionWriterIntegrationFixture.SoftwareActionScenario(prepare.operationKey(),prepare.capability(),
                (command,attempt,dispatch)->new ActionPorts.Pending("software ACK is no exit observation",List.of(command.source().sourceRef())),dispatches::incrementAndGet,
                Optional.of(()->raw("{\"fixture_selector\":\"prepare_confirmation\"}")),Optional.empty(),false,
                Optional.of(command->normalRequest(command.before(),command.source().sourceRef(),RequestIds.forCommand(command),NormalExitProtocol.Action.PREPARE_CONFIRMATION)));
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("finite-selector"),false,scenario,List.of(action))){
            var ready=fixture.ready();var contract=readContract.get();
            var request=new PlanningReadRequest(ready.request().before(),fixture.observationSource(),fixture.observationIdentity().sessionId(),query.operationKey(),new OpportunityJson.Obj(Map.of()),Instant.now().plusSeconds(10));
            var actual=known(fixture.reads.read(contract,request));assertEquals(query.operationKey(),actual.receipt().request().operation());
            assertEquals("query_context",StrictJson.parse(actual.value().bytes()).get("fixture_selector").textValue());
            var receipt=fixture.coordinator.execute(fixture.command("finite-selector-prepare"));assertEquals(1,dispatches.get());
            assertEquals(1,fixture.nativeActionWrites());assertEquals(1,fixture.scenarioReadWrites());assertFalse(receipt.settled());assertTrue(receipt.applied().isEmpty());
            assertTrue(receipt.ack().isPresent());assertEquals("prepare_confirmation",StrictJson.parse(receipt.ack().orElseThrow().originalResultToken().orElseThrow().bytes()).get("fixture_selector").textValue());
        }
    }
    private ActionWriterIntegrationFixture fixture(String label,AtomicReference<RootReadContractCatalog.Family<String,RawJson>> family)throws Exception{
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"two-issued-context-software",source->List.of(),request->{
            var args=StrictJson.parse(request.additionalFields().bytes());String variant=args.get("variant").textValue();
            return new RawJson(StrictJson.canonical(StrictJson.object().put("echo_variant",variant)));
        },Optional.empty(),Set.of(),source->{
            var actual=new RootReadContractCatalog.Family<>("fixture-two-contexts/v1",String.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(CAP),source,source,
                    variant->new RawJson(DriverJson.encode(arguments(variant))),ignored->OP,variant->contract(source,variant));family.set(actual);return List.of(actual);
        });return new ActionWriterIntegrationFixture(directory.resolve(label),false,scenario);
    }
    private static ReadContract<RawJson> contract(ExactRef source,String variant){
        java.util.function.Function<PlanningReadReceipt,RawJson> decode=receipt->{
            StrictJson.require(receipt.contractId().equals("fixture-context-"+variant+"/v1"),"original decoder belongs to another context");
            var result=receipt.original().originalResultToken().orElseThrow();StrictJson.require(variant.equals(StrictJson.parse(result.bytes()).get("echo_variant").textValue()),"original native result belongs to another context");return result;
        };
        return new ReadContract<>("fixture-context-"+variant+"/v1",OP,Optional.of(CAP),CAP,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,(request,id)->{
                    StrictJson.require(request.arguments().equals(arguments(variant)),"request changed its original issued context");return new NativeRequest(OP.value(),Optional.of(CAP),new RawJson(DriverJson.encode(request.arguments())));
                },decode,decode,(original,value,current,semantic)->{
                    StrictJson.require(original.request().origin().equals(current.origin())&&original.request().source().equals(current.source())
                            &&original.request().sessionId().equals(current.sessionId())&&original.request().operation().equals(current.operation())
                            &&original.request().arguments().equals(current.arguments())&&current.arguments().equals(arguments(variant)),"late read changed original context/source/frame");
                    StrictJson.require(value.equals(decode.apply(original))&&!semantic.members().isEmpty(),"late read changed the original decoder/full current semantic");
                });
    }
    private static OpportunityJson.Obj arguments(String variant){return new OpportunityJson.Obj(Map.of("variant",new OpportunityJson.Text(variant)));}
    private static PlanningReadRequest request(ActionWriterIntegrationFixture fixture,org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before,
            ReadContract<RawJson> contract,String variant,Instant deadline){return new PlanningReadRequest(before,fixture.observationSource(),fixture.observationIdentity().sessionId(),contract.operation(),arguments(variant),deadline);}
    private static PlanningReadResult.Known<RawJson> known(PlanningReadResult<RawJson> actual){if(actual instanceof PlanningReadResult.Known<RawJson> known)return known;throw new AssertionError(actual);}
    private static NativeRequest normalRequest(org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before,ExactRef source,String id,NormalExitProtocol.Action action){
        var binding=new NormalExitProtocol.Binding(before.frame().identity().nativeRevision(),before.frame().identity().player(),BigInteger.valueOf(before.game().pid()),BigInteger.valueOf(5),before.game().creationFiletime().value(),source.sha256());
        var original=NormalExitProtocol.payload(new NormalExitProtocol.Request(id,action,binding,"independent-software-phase-nonce",action==NormalExitProtocol.Action.QUERY_CONTEXT?Optional.empty():Optional.of("a".repeat(64))));
        var fields=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(original);for(String key:List.of("type","protocol_version","request_id","step","expected_revision"))fields.remove(key);
        return new NativeRequest(NormalExitProtocol.STEP,Optional.of(NormalExitProtocol.STEP),new RawJson(StrictJson.canonical(fields)));
    }
    private static RawJson raw(String text){return new RawJson(text.getBytes(StandardCharsets.UTF_8));}
}
