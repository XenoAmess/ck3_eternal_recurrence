package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** Source-derived software DATA through actual receipt/market/project/replay consumers; no Native, writer or quote qualification. */
final class NativeFinanceMercenaryEmployerWireTest {
    private static final String MACHINE="xenoamess-full-tower-eb9d2c1186",EXE="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final ExactRef SOURCE_REF=new ExactRef("D:/source-derived-software/definition",1,"a".repeat(64));
    private static final ExactRef CAP=new ExactRef("D:/source-derived-software/capability",1,"c".repeat(64));
    private static final G2Source SOURCE=new G2Source(MACHINE,"2026-10-29T00:00:00Z","1.20.0.4",SOURCE_REF);
    private static final Instant SUBMITTED=Instant.parse("2026-10-29T00:00:01Z"),AFTER=SUBMITTED.plusSeconds(1),DEADLINE=SUBMITTED.plusSeconds(30);
    private static final List<Integer> ACTORS=List.of(Integer.MIN_VALUE,Integer.MIN_VALUE+5,-67108906,-2,0,1,67108906,Integer.MAX_VALUE);
    private static final Obj EMPTY=obj();
    private static final FinanceReadContracts DEFINITIONS=new FinanceReadContracts(query->new FinanceReadContracts.Registration(SOURCE_REF,
            new FinanceReadContracts.Permission(Optional.of("game.command."+query.operation().value()),"game.command."+query.operation().value(),ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP)));
    private record Fixture(ActionCommand command,ActionState.Attempt attempt,NativeEffectSnapshots.Pair pair,PlanningReadReceipt read,FinanceReadContracts.Packet packet) { }
    private static Complete frame(int actor,int revision) {
        var id=new ObservationIdentity(MACHINE,new GameGeneration(17,new PythonOnlyUInt64(BigInteger.valueOf(100))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor),BigInteger.valueOf(revision),BigInteger.valueOf(100)),"native-"+revision,BigInteger.valueOf(revision),"actual-episode"),1);
        Obj semantic=OrdinaryFinanceCollector.sourceFrame(id).with("played_character",obj("character_id",new IntegerValue(BigInteger.valueOf(actor)),"alive",new Bool(true)))
                .with("paused",new Bool(true)).with("map_ready",new Bool(true))
                .with("diagnostics",obj("hello",obj("expected_ck3_version",new Text("1.20.0.4"),"expected_ck3_sha256",new Text(EXE))));
        return new Complete(id,SOURCE,"software-session",BigInteger.ONE,semantic,new ExactRef("D:/source-derived-software/native-"+revision,1,"b".repeat(64)),
                revision==10?SUBMITTED.minusSeconds(1):AFTER,"d".repeat(64));
    }
    private static GuardEvidence guard(Complete frame,OperationKey operation,Instant observedAt) {
        return new GuardEvidence(frame.identity(),SOURCE,frame.sessionId(),frame.connectionGeneration(),operation,frame.originalEvidence(),CAP,"software-authority",observedAt,DEADLINE);
    }
    private static Obj market(int actor,Value employer,BigInteger epoch,BigInteger company,boolean available) {
        Obj terms=obj("available",new Bool(false),"unavailable_reason",new Text("not-observed"),"can_hire",Nil.INSTANCE,"can_afford",Nil.INSTANCE,
                "payment_status",Nil.INSTANCE,"resource_scale",new IntegerValue(BigInteger.valueOf(100000)),"resource_costs_raw",Nil.INSTANCE,"hire_duration_months",Nil.INSTANCE,
                "can_hire_reasons_available",new Bool(false),"can_hire_reason_literal",Nil.INSTANCE,"can_afford_reasons_available",new Bool(false),"can_afford_reason_literal",Nil.INSTANCE);
        Obj location=obj("company_home_title_id",Nil.INSTANCE,"company_home_province_id",Nil.INSTANCE,"hire_auto_raise_province_id",Nil.INSTANCE,"actor_active_war_count",Nil.INSTANCE,
                "hire_auto_raise_attempted_in_active_war",Nil.INSTANCE,"company_home_ready",new Bool(false),"company_home_failure",new Text("not-observed"),"company_home_source",new Text("native"),
                "hire_auto_raise_position_ready",new Bool(false),"hire_auto_raise_position_failure",new Text("not-observed"),"hire_auto_raise_position_source",new Text("native"));
        Obj row=obj("company_id",new IntegerValue(company),"employer_id",employer,"manager_slot_index",new IntegerValue(BigInteger.ZERO),
                "troop_strength",obj("available",new Bool(false),"unavailable_reason",new Text("not-observed"),"current_soldiers",Nil.INSTANCE),"final_terms",terms,"location",location);
        return obj("schema",new Text("ck3_12004_player_mercenary_context_v1"),"game_version",new Text("1.20.0.4"),"executable_sha256",new Text(EXE),
                "actor_character_id",new IntegerValue(BigInteger.valueOf(actor)),"date_raw",new IntegerValue(BigInteger.valueOf(100)),"capture_epoch",new IntegerValue(epoch),
                "read_only",new Bool(true),"native_hire_mode",new IntegerValue(BigInteger.ONE),"available",new Bool(available),"unavailable_reason",available?Nil.INSTANCE:new Text("unavailable"),"rows",new Arr(List.of(row)));
    }
    private static Fixture fixture(int actor,Value employer,BigInteger epoch,BigInteger company,boolean available) {
        Complete before=frame(actor,10),after=frame(actor,11);
        var expected=new ExpectedPostcondition(1,before.identity(),SOURCE,NativeFinanceEffects.HIRE_SCHEMA,List.of(
                new ExpectedInteger(new FieldKey("company_id"),BigInteger.ZERO),new ExpectedInteger(new FieldKey("actor_id"),BigInteger.valueOf(actor)),
                new ExpectedText(new FieldKey("status"),"employment_observed")));
        Obj arguments=obj("company_id",new IntegerValue(BigInteger.ZERO),"source_frame",OrdinaryFinanceCollector.sourceFrame(before.identity()),"pre_capture_epoch",new IntegerValue(BigInteger.ONE),
                "pre_player_army_ids",new Arr(List.of()),"decision",obj("selected_candidate",obj("company_id",new IntegerValue(BigInteger.ZERO))));
        var command=new ActionCommand("source-derived-hire",before.identity(),SOURCE,before.sessionId(),OrdinaryFinancePolicies.MERCENARY,arguments,expected,
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),DEADLINE);
        var attempt=new ActionState.Attempt("retained-hire-request",SUBMITTED,guard(before,command.operation(),SUBMITTED.minusSeconds(1)),
                new NativeRequest(command.operation().value(),Optional.of("game.command.hire-mercenary-v1"),new RawJson(encode(obj("company_id",new IntegerValue(BigInteger.ZERO))))));
        var operation=FinanceReadContracts.Query.MERCENARIES.operation();var contract=DEFINITIONS.contract(FinanceReadContracts.Query.MERCENARIES);
        var request=new PlanningReadRequest(after.identity(),SOURCE,after.sessionId(),operation,EMPTY,DEADLINE);
        var readGuard=new PlanningReadGuard(guard(after,operation,AFTER),true,true,true,after.fullBindingSha256());
        Obj result=obj("step",new Text(operation.value()),"accepted",new Bool(true),"snapshot_revision",new IntegerValue(BigInteger.valueOf(11)),"player_mercenary_context",market(actor,employer,epoch,company,available));
        String requestId="independent-employer-read";
        var full=new RawJson(encode(obj("type",new Text("command_result"),"protocol_version",new IntegerValue(BigInteger.ONE),"request_id",new Text(requestId),"ok",new Bool(true),"result",result)));
        byte[] packet=ByteBuffer.allocate(full.bytes().length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(full.bytes().length).put(full.bytes()).array();
        var ack=new NativeActionPort.AckReceived(requestId,true,Optional.of(new RawJson(encode(result))),full,packet);
        var read=new PlanningReadReceipt(request,contract.contractId(),requestId,readGuard,readGuard,ack);
        return new Fixture(command,attempt,new NativeEffectSnapshots.Pair(before,after),read,contract.decode(read));
    }
    private static Fixture fixture(int actor,Value employer) { return fixture(actor,employer,BigInteger.TWO,BigInteger.ZERO,true); }
    private static NativeEffectRegistry.Projected project(Fixture fixture) {
        return NativeFinanceEffects.project(fixture.command(),fixture.attempt(),fixture.pair(),fixture.read(),fixture.packet());
    }
    @Test void actualReceiptMarketProjectMatchesOnlyNativeWireBitsAndKeepsSignedResult() {
        var checks=new java.util.ArrayList<org.junit.jupiter.api.function.Executable>();
        for(int actor:ACTORS)checks.add(()->{
            Fixture original=fixture(actor,new IntegerValue(BigInteger.valueOf(Integer.toUnsignedLong(actor))));
            var projected=project(original);assertInstanceOf(ActionPorts.EffectObserved.class,projected.result(),"source-derived signed actor "+actor);
            Obj result=object(parse(projected.compatibleResult().orElseThrow().bytes()),"actual compatible effect");
            assertEquals(new IntegerValue(BigInteger.valueOf(actor)),result.get("employer_character_id"));
            assertEquals(new Bool(true),result.get("employment_verified"));
            for(String flag:List.of("payment_verified","army_creation_verified","company_to_new_army_binding_verified"))assertEquals(new Bool(false),result.get(flag));
        });
        assertAll(checks);
    }
    @Test void wrongEmployerAbsentStaleUnavailableAndWrongCompanyNeverCreateEmployment() {
        for(Value employer:List.of(Nil.INSTANCE,new IntegerValue(BigInteger.TWO),new IntegerValue(BigInteger.valueOf(16777214)),new IntegerValue(new BigInteger("4294967293")),new IntegerValue(new BigInteger("4294967295"))))
            assertInstanceOf(ActionPorts.Pending.class,project(fixture(-2,employer)).result());
        assertInstanceOf(ActionPorts.Pending.class,project(fixture(1,new IntegerValue(BigInteger.ZERO))).result());
        Value matching=new IntegerValue(new BigInteger("4294967294"));
        assertInstanceOf(ActionPorts.Pending.class,project(fixture(-2,matching,BigInteger.ONE,BigInteger.ZERO,true)).result());
        assertInstanceOf(ActionPorts.Pending.class,project(fixture(-2,matching,BigInteger.TWO,BigInteger.ONE,true)).result());
        assertInstanceOf(ActionPorts.Pending.class,project(fixture(-2,matching,BigInteger.TWO,BigInteger.ZERO,false)).result());
        for(Value malformed:List.of(new Bool(true),new Text("4294967294"),new IntegerValue(BigInteger.valueOf(-2)),new IntegerValue(new BigInteger("4294967296"))))
            assertThrows(IllegalArgumentException.class,()->project(fixture(-2,malformed)));
    }
    @Test void originalReadPureReplayMatchesLiveProjectUsingActualEvidenceComparator() {
        for(int actor:ACTORS) {
            Fixture original=fixture(actor,new IntegerValue(BigInteger.valueOf(Integer.toUnsignedLong(actor))));
            var live=project(original);var observed=assertInstanceOf(ActionPorts.EffectObserved.class,live.result());
            var replayPacket=DEFINITIONS.decodeOriginal(FinanceReadContracts.Query.MERCENARIES,original.read(),original.pair().after().semantic());
            var replayed=NativeFinanceEffects.project(original.command(),original.attempt(),original.pair(),original.read(),replayPacket);
            NativeEffectEvidence.requireSame(new ActionState.Applied(observed.observation()),replayed,live.compatibleResult().orElseThrow());
        }
        // Whole archivedVerifier also requires actual quote/source/archive/writer custody; this pure replay grants none.
    }
}
