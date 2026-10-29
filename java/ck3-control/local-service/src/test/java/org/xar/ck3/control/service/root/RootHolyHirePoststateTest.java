package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.effects.HolyHirePoststate.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Controlled source/serialization tests. The existing whole Native corpus remains the native producer qualification. */
final class RootHolyHirePoststateTest {
    @TempDir Path temporary;
    private static final Instant NOW=Instant.parse("2026-10-27T00:00:00Z");
    private static final ExactRef REF=new ExactRef("metadata-only/source.java",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source("metadata-only-machine",NOW.toString(),"1.20.0.4",REF);
    private static final OperationKey HIRE=new OperationKey("hire-holy-order-v1");
    private static BigInteger n(long value){return BigInteger.valueOf(value);}
    private static ObservationIdentity identity(int revision){
        return new ObservationIdentity(SOURCE.machineId(),new GameGeneration(42,new PythonOnlyUInt64(n(1))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(n(73),n(revision),n(100)),"native:"+revision,n(revision),"episode"),1);
    }
    private static Complete frame(int revision,long piety){
        ObjectNode semantic=StrictJson.object();semantic.putArray("player_armies");
        semantic.putObject("played_character_gold").put("raw",100).put("scale",100000);
        semantic.putObject("played_character_prestige").put("raw",200).put("scale",100000);
        semantic.putObject("played_character_piety").put("raw",piety).put("scale",100000);
        return new Complete(identity(revision),SOURCE,"session",n(1),(OpportunityJson.Obj)OpportunityJson.parse(StrictJson.canonical(semantic)),REF,NOW.plusSeconds(revision),"b".repeat(64));
    }
    private static ActionCommand command(){
        var expected=new ExpectedPostcondition(1,identity(10),SOURCE,NativeArmyWarWindowEffects.SCHEMA,List.of(new ExpectedText(new FieldKey("effect"),"employer_relationship_observed")));
        return new ActionCommand("action",identity(10),SOURCE,"session",HIRE,new OpportunityJson.Obj(Map.of()),expected,new JointBudgetSelector.Claims(java.util.Set.of(),java.util.Set.of(),java.util.Set.of(),java.util.Set.of()),NOW.plusSeconds(86400));
    }
    private static ActionState.Attempt attempt(ActionCommand command){
        var guard=new GuardEvidence(command.before(),SOURCE,"session",n(1),HIRE,REF,REF,"metadata-only-guard",NOW,NOW.plusSeconds(86400));
        return new ActionState.Attempt("request",NOW,guard,new NativeRequest(HIRE.value(),Optional.of("game.command.hire-holy-order-v1"),new RawJson(StrictJson.canonical(StrictJson.object().put("holy_order_id",0)))));
    }
    private static ObjectNode context(boolean after){
        ObjectNode context=StrictJson.object().put("available",true).put("played_character_id",73);
        var order=context.putArray("rows").addObject().put("holy_order_id",0).put("is_military",true);
        if(after)order.put("employer_id",73);else order.putNull("employer_id");
        var terms=order.putObject("military_terms").put("available",true).put("can_hire",true).put("can_afford",true);
        var quote=terms.putArray("resource_costs_raw");for(int i=0;i<10;i++)quote.add(i==2?200000:0);
        return context;
    }
    private static final class MemoryArchive {
        final Map<ExactRef,RawJson> data=new HashMap<>();
        final ActionPorts.OutcomeArchive port=(ActionPorts.OutcomeArchive)Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
            if(method.getName().equals("preserveMaterial")){
                RawJson raw=(RawJson)args[0];String hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw.bytes()));
                ExactRef ref=new ExactRef("metadata-only/material-"+hash+".json",raw.bytes().length,hash);data.put(ref,raw);return ref;
            }
            if(method.getName().equals("loadMaterial"))return java.util.Objects.requireNonNull(data.get((ExactRef)args[0]));
            if(method.getName().equals("toString"))return "metadata-only-memory-archive";
            throw new AssertionError("unexpected archive call "+method.getName());
        });
    }
    private static final class Runtime implements RootHolyHirePoststate.RuntimeAccess {
        final MemoryArchive archive=new MemoryArchive();final AtomicInteger reads=new AtomicInteger(),frames=new AtomicInteger();
        final Complete expected;
        Runtime(Complete expected){this.expected=expected;}
        @Override public void requireFrame(Complete frame,Instant deadline){assertEquals(expected,frame);frames.incrementAndGet();}
        @Override public ActionPorts.OutcomeArchive archive(){return archive.port;}
        @Override public PlanningReadPort reads(){return new PlanningReadPort(){
            @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){
                reads.incrementAndGet();assertEquals(expected.identity(),request.before());assertEquals(expected.source(),request.source());assertEquals(expected.sessionId(),request.sessionId());
                assertEquals("query-war-cash-current-resources-v1",request.operation().value());return new PlanningReadResult.Unavailable<>("controlled current cash unavailable",Optional.empty());
            }
        };}
        @Override public RootReadContractCatalog catalog(){throw new AssertionError("no strengths contract requested without an association");}
        @Override public ArmyStrengthsContracts strengths(){throw new AssertionError("no strengths producer requested without an association");}
        @Override public NativeWire.Hello hello(){throw new AssertionError("no HELLO requested without an association");}
        @Override public ReadContract<FinanceReadContracts.Packet> cash(){
            return new ReadContract<>("metadata-only-cash",new OperationKey("query-war-cash-current-resources-v1"),Optional.of("metadata-only-cash-cap"),"metadata-only-cash",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                    ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,REF,
                    (request,id)->{throw new AssertionError("controlled unavailable read has no send");},receipt->{throw new AssertionError("no original cash packet");},receipt->{throw new AssertionError("no archived cash packet");});
        }
    }
    @Test void actualCollectorRetainsSameFrameUnavailableExpenseAndReplaysArchiveWithoutAnyRead(){
        var command=command();var attempt=attempt(command);var pair=new NativeEffectSnapshots.Pair(frame(10,500000),frame(11,300000));
        var runtime=new Runtime(pair.after());var sources=new Sources(REF,REF);var collector=new RootHolyHirePoststate(sources,runtime);
        var selected=new ArmyWarWindowReads.HolyHire(0);
        var observed=collector.collect(command,attempt,pair,selected,context(false),context(true));
        assertEquals(1,runtime.reads.get());assertEquals(1,runtime.frames.get());assertEquals(QuoteMatch.MATCH,observed.report().wallet().quoteMatch());
        assertEquals(Status.NOT_REQUESTED,observed.report().troops().strengthStatus());assertFalse(observed.report().troops().usableArmyObserved());
        assertEquals(Status.UNAVAILABLE,observed.report().expenses().status());
        assertEquals(Presence.UNAVAILABLE,observed.report().expenses().currentMilitaryGoldRaw().presence());
        int reads=runtime.reads.get(),frames=runtime.frames.get();
        var restored=collector.replay(command,attempt,pair,selected,context(false),context(true),observed.originalMaterial(),runtime.archive.port);
        assertEquals(observed,restored);assertEquals(reads,runtime.reads.get());assertEquals(frames,runtime.frames.get(),"archive replay cannot acquire a current frame");
        var stored=StrictJson.object(StrictJson.parse(runtime.archive.port.loadMaterial(observed.originalMaterial()).bytes()),java.util.Set.of("schema","model_source","collector_source","strengths_read","cash_read","hello_packet_base64","strengths_status","strengths_reason","cash_reason","report"));
        ((ObjectNode)stored.get("report")).put("full_hire_loop_complete",true);
        var changed=runtime.archive.port.preserveMaterial(new RawJson(StrictJson.canonical(stored)));
        assertThrows(IllegalArgumentException.class,()->collector.replay(command,attempt,pair,selected,context(false),context(true),changed,runtime.archive.port));
        assertEquals(reads,runtime.reads.get());
    }
    @Test void sourceBoundaryDistinguishesNullMissingAndWrongNumericTypesAndRejectsAnotherActor(){
        var semantic=StrictJson.object();semantic.putNull("played_character_gold");
        semantic.putObject("played_character_prestige").put("scale",100000).put("raw",true);
        var values=RootHolyHirePoststate.stocks(semantic);assertEquals(Presence.NULL,values.gold().presence());assertEquals(Presence.UNAVAILABLE,values.prestige().presence());assertEquals(Presence.UNAVAILABLE,values.piety().presence());
        var command=command();var pair=new NativeEffectSnapshots.Pair(frame(10,500000),frame(11,300000));var scope=Scope.of(command,attempt(command),pair,0);
        var other=context(true);other.put("played_character_id",74);assertThrows(IllegalArgumentException.class,()->RootHolyHirePoststate.association(other,scope));
        var wrong=context(true);((ObjectNode)wrong.path("rows").get(0).path("military_terms")).putObject("troop_association").put("available",true).put("applies_to_player",false).putArray("rows");
        assertThrows(IllegalArgumentException.class,()->RootHolyHirePoststate.association(wrong,scope));
    }
    @Test void realSoleWriterUnknownHireCannotBeSubmittedAgain()throws Exception{
        var dispatches=new AtomicInteger();
        var preparation=new ActionPorts.PreparationPort(){
            @Override public NativeRequest prepare(ActionCommand command){return new NativeRequest(HIRE.value(),Optional.of("game.command.hire-holy-order-v1"),new RawJson(StrictJson.canonical(StrictJson.object().put("holy_order_id",0))));}
        };
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(HIRE,"game.command.hire-holy-order-v1",
                (command,attempt,original)->new ActionPorts.Pending("controlled independent employer unavailable",List.of(attempt.guard().nativeEvidence())),
                dispatches::incrementAndGet,Optional.empty(),Optional.empty(),false,Optional.of(preparation));
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("same-writer-unknown"),true,scenario)){
            var template=fixture.command("holy-original", java.time.Duration.ofMinutes(2));
            ExactRef before=fixture.writer.locked(same->fixture.archive.inSession(same,archive->archive.readReferenceOf(fixture.lastNestedRead.get())));
            var call=new ArmyCalls.Hire(PublicMethod.HIRE_HOLY_ORDER_V1,new ArmyCalls.Revision(new ArmyTypes.Present<>(template.before().frame().revision())),new ArmyTypes.HireId(0));
            var arguments=new ArmyOrdinaryActionArguments(ArmyOrdinaryActionArguments.Kind.HIRE_HOLY_ORDER_V1,ArmyCallCodec.encode(call),List.of(before));
            var expected=NativeArmyWarWindowEffects.expected(template.before(),template.source(),HIRE,arguments.raw());
            var command=new ActionCommand(template.actionId(),template.before(),template.source(),template.sessionId(),HIRE,arguments.encode(),expected,template.claims(),template.deadline());
            var pending=fixture.coordinator.execute(command);assertInstanceOf(ActionState.Unknown.class,pending.state());
            byte[] durable=fixture.ledgerBytes();
            assertEquals(pending,fixture.coordinator.execute(command));
            assertArrayEquals(durable,fixture.ledgerBytes());
            assertEquals(1,dispatches.get());assertEquals(1,fixture.nativeActionWrites());
            fixture.writer.locked(same->fixture.archive.inSession(same,archive->{var ref=archive.receiptReferenceOf(pending);assertEquals(pending,archive.loadReceipt(ref));return null;}));
            assertEquals(1,dispatches.get(),"archive readback cannot submit the hire");
        }
    }
}
