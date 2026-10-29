package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessment;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessmentCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.FinancingGapCodec;

/** Strict software CASH packet -> real registered decoder/collector -> ordinary assessment consumer.
 * Synthetic source-shaped observations confer no live Native, writer or loan qualification. */
final class OrdinaryLoanObservationTest {
    private static final ExactRef REF=new ExactRef("D:/software-fixture/loan-source.java",1,"a".repeat(64));
    private static final String SHA="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final G2Source SOURCE=new G2Source("software-fixture-machine","2026-10-27T00:00:00Z","1.20.0.4",REF);
    private static final Instant DEADLINE=Instant.parse("2026-10-28T00:00:00Z");
    private static PlanningRequest request() {
        Obj snapshot=json("""
                {"snapshot_id":"native:7","revision":1,"native_revision":7,"date_raw":100,"episode_run_id":"loan-episode",
                 "paused":true,"map_ready":true,"played_character":{"character_id":1,"alive":true},
                 "played_character_gold":{"raw":1000000,"scale":100000},"active_wars":[{"war_id":9}],"player_armies":[],
                 "active_event":null,"pending_character_interaction":null,"diagnostics":{"bridge_pid":123,"connection_generation":1}}
                """);
        Obj diagnostics=object(snapshot.get("diagnostics"),"diagnostics").with("hello",obj("expected_ck3_version",new Text("1.20.0.4"),"expected_ck3_sha256",new Text(SHA)));
        snapshot=snapshot.with("diagnostics",diagnostics);
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,BigInteger.valueOf(7),BigInteger.valueOf(100)),
                "native:7",BigInteger.ONE,"loan-episode");
        var before=new ObservationIdentity(SOURCE.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),frame,1);
        return withSnapshot(new PlanningRequest(before,SOURCE,"loan-session",DEADLINE,new PlanningObservation(snapshot,List.of(),Set.of(),Set.of(),
                Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false)),snapshot);
    }
    private static PlanningRequest withSnapshot(PlanningRequest original,Obj snapshot) {
        return new PlanningRequest(original.before(),original.source(),original.sessionId(),original.deadline(),new PlanningObservation(snapshot,List.of(),Set.of(),Set.of(),
                Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static FinanceReadContracts definitions() {
        return new FinanceReadContracts(query->new FinanceReadContracts.Registration(REF,new FinanceReadContracts.Permission(Optional.empty(),
                query.operation().value(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
    }
    private static final class OriginalCash implements PlanningReadPort {
        Obj cash=rawCash(false,900_000_000); boolean unavailable; boolean wrongPublicFrame; BigInteger connection=BigInteger.ONE;
        int calls; Session borrowed;
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) { return original(contract,request); }
        @Override public <T> PlanningReadResult<T> read(Session same,ReadContract<T> contract,PlanningReadRequest request) {
            borrowed=same;return original(contract,request);
        }
        private <T> PlanningReadResult<T> original(ReadContract<T> contract,PlanningReadRequest input) {
            calls++;assertEquals(FinanceReadContracts.Query.CASH.operation(),input.operation());
            if(unavailable)return new PlanningReadResult.Unavailable<>("original CASH unavailable",Optional.empty());
            PlanningReadRequest actual=input;
            if(wrongPublicFrame) {
                var old=input.before();var f=old.frame();var changed=new JointBudgetSelector.ProposalFrame(f.identity(),f.snapshotId(),f.revision().add(BigInteger.ONE),f.episodeRunId());
                actual=new PlanningReadRequest(new ObservationIdentity(old.machineId(),old.game(),changed,old.observationVersion()),input.source(),input.sessionId(),input.operation(),input.arguments(),input.deadline());
            }
            Obj result=obj("step",new Text(input.operation().value()),"accepted",new Bool(true),"war_cash_current_resources",cash);
            Obj frame=obj("type",new Text("command_result"),"protocol_version",n(1),"request_id",new Text("loan-original-read"),"ok",new Bool(true),"result",result);
            byte[] wire=DriverJson.encode(frame),packet=ByteBuffer.allocate(wire.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(wire.length).put(wire).array();
            var ack=new NativeActionPort.AckReceived("loan-original-read",true,Optional.of(new RawJson(DriverJson.encode(result))),new RawJson(wire),packet);
            var binding=new GuardEvidence(actual.before(),actual.source(),actual.sessionId(),connection,input.operation(),REF,REF,"software-cash-owner",DEADLINE.minusSeconds(30),DEADLINE);
            var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));
            var receipt=new PlanningReadReceipt(actual,contract.contractId(),ack.requestId(),guard,guard,ack);
            return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,REF);
        }
    }
    private static OrdinaryFinanceCollector collector(OriginalCash port) {
        var state=new FinanceStatePort(ignored->new FinanceStatePort.Unavailable("loan observation does not read or clear spending bodies"),List.of());
        return new OrdinaryFinanceCollector(definitions(),port,state);
    }
    private static OrdinaryPolicy.Draft prior() {
        return new OrdinaryPolicy.Draft("original-ordinary-war","current-war-choice","keep real war choice",OrdinaryPolicy.Kind.ORDINARY,
                Optional.empty(),OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),obj("selected_step",new Text("life-advance")));
    }
    private static Obj gap(PlanningRequest request) {
        return obj("schema",new Text(FinancingGapCodec.REQUEST_SCHEMA),"snapshot",request.observations().snapshot(),
                "priority",obj("wars",new Arr(List.of(obj("war_id",n(9),"primary_player_war",new Bool(true),"player_relative_war_score",n(-50),"raised_force_deficit",new Bool(true))))),
                "root",Nil.INSTANCE,"construction_ledger",obj("pending",Nil.INSTANCE),"bridge_capabilities",new Arr(List.of()));
    }
    private static EmergencyFinancingAssessment.Assessment consumed(PlanningRequest request,OrdinaryFinanceCollector.Read<OrdinaryFinanceCollector.LoanObservation> loan) {
        var before=prior();var after=OrdinaryFinancePolicies.financingObservation(before,gap(request),loan);
        assertEquals(before.command(),after.command());assertEquals(before.purpose(),after.purpose());assertEquals(before.phase(),after.phase());
        assertEquals(before.reason(),after.reason());assertEquals(before.detail().get("selected_step"),after.detail().get("selected_step"));
        Obj result=object(after.detail().get("emergency_financing_assessment"),"actual ordinary diagnostic");
        var assessed=EmergencyFinancingAssessmentCodec.decodeResult(DriverJson.encode(result));
        assertFalse(assessed.submitPlanned());assertFalse(assessed.loan().submitPlanned());assertFalse(assessed.loan().completeLoanTermsVerified());
        assertFalse(assessed.loan().typedDebtReadbackVerified());assertFalse(assessed.loan().independentlyAttributedReceivedFundsVerified());
        assertEquals(0,assessed.unreceivedFundingCreditedRaw());assertFalse(assessed.optionalConstructionMayUseProspectiveFunding());
        assertEquals(EmergencyFinancingAssessment.ReplayGuard.LEDGER_UNAVAILABLE,assessed.replay());
        assertEquals(result,parse(EmergencyFinancingAssessmentCodec.encode(assessed)));return assessed;
    }
    private static OrdinaryFinanceCollector.LoanObservation observed(OrdinaryFinanceCollector.Read<OrdinaryFinanceCollector.LoanObservation> read) {
        return assertInstanceOf(OrdinaryFinanceCollector.LoanObservation.class,assertInstanceOf(OrdinaryFinanceCollector.Known.class,read).value());
    }
    @Test void actualCashProducerSuppliesKnownFalseEligibilityAndQuoteToTheOrdinaryDiagnosticWithoutGrantingFunds() {
        var request=request();var port=new OriginalCash();Obj original=port.cash;
        var read=collector(port).loan(request);var actual=observed(read);
        assertInstanceOf(LoanFinancingCodec.Projected.class,actual.input());assertEquals(original,port.cash);assertEquals(1,port.calls);
        assertEquals(n(1),object(actual.request().get("cash_resources"),"cash").get("queried_revision"));
        assertEquals(actual.original().receipt().request().before(),request.before());
        var assessed=consumed(request,read);assertEquals(EmergencyFinancingAssessment.LoanStatus.NATIVE_GATES_REJECTED,assessed.loan().status());
        assertEquals(EmergencyFinancingAssessment.Eligibility.DENIED,assessed.loan().eligibility());assertEquals(900_000_000,assessed.loan().prospectivePrincipalRaw().orElseThrow());
        assertEquals(10,assessed.loan().declaredCostsRaw().orElseThrow().size());
    }
    @Test void allowedGateAndZeroQuoteRemainObservationsWithIncompleteTermsAndNoSubmission() {
        var request=request();var port=new OriginalCash();port.cash=rawCash(true,0);
        var assessed=consumed(request,collector(port).loan(request));
        assertEquals(EmergencyFinancingAssessment.LoanStatus.COMPLETE_LOAN_TERMS_MISSING,assessed.loan().status());
        assertEquals(EmergencyFinancingAssessment.Eligibility.ALLOWED,assessed.loan().eligibility());assertEquals(0,assessed.loan().prospectivePrincipalRaw().orElseThrow());
    }
    @Test void changedNativeIdentityOrSuppliedQueryMetadataCannotBeStampedAsCurrent() {
        var request=request();
        for(Obj bad:List.of(rawCash(false,1).with("snapshot_revision",n(8)),rawCash(false,1).with("played_character_id",n(2)),
                rawCash(false,1).with("date_raw",n(101)),rawCash(false,1).with("queried_snapshot_id",new Text("another-snapshot")),
                rawCash(false,1).with("queried_revision",new DecimalValue("1.0")),rawCash(false,1).with("queried_native_revision",new Bool(true)))) {
            var port=new OriginalCash();port.cash=bad;var read=collector(port).loan(request);
            assertInstanceOf(OrdinaryFinanceCollector.Unavailable.class,read);assertTrue(consumed(request,read).loan().prospectivePrincipalRaw().isEmpty());
        }
    }
    @Test void originalReceiptPublicFrameProcessAndConnectionMustMatchTheFullCurrentSnapshot() {
        var request=request();var stale=new OriginalCash();stale.wrongPublicFrame=true;
        assertInstanceOf(OrdinaryFinanceCollector.Unavailable.class,collector(stale).loan(request));
        var connection=new OriginalCash();connection.connection=BigInteger.TWO;
        assertInstanceOf(OrdinaryFinanceCollector.Unavailable.class,collector(connection).loan(request));
        Obj diagnostics=object(request.observations().snapshot().get("diagnostics"),"diagnostics");
        for(Value bad:List.of(n(124),Nil.INSTANCE,new Bool(true),new DecimalValue("123.0"))) {
            var changed=withSnapshot(request,request.observations().snapshot().with("diagnostics",diagnostics.with("bridge_pid",bad)));
            assertInstanceOf(OrdinaryFinanceCollector.Unavailable.class,collector(new OriginalCash()).loan(changed));
        }
    }
    @Test void unqualifiedLoanChildKeepsCashButCannotAcquireEligibilityOrPrincipal() {
        var request=request();var port=new OriginalCash();Obj loan=object(port.cash.get("holy_order_loan_observation_v1"),"loan");
        port.cash=port.cash.with("holy_order_loan_observation_v1",loan.with("source_frame",object(loan.get("source_frame"),"source").with("ticket_sequence",n(0))));
        var read=collector(port).loan(request);assertInstanceOf(OrdinaryFinanceCollector.Known.class,read);
        var assessed=consumed(request,read);assertEquals(EmergencyFinancingAssessment.LoanStatus.NATIVE_INPUT_UNAVAILABLE,assessed.loan().status());
        assertEquals(EmergencyFinancingAssessment.Eligibility.UNKNOWN,assessed.loan().eligibility());assertTrue(assessed.loan().prospectivePrincipalRaw().isEmpty());
    }
    @Test void missingCashIsRecordedWithoutRemovingTheExistingWarChoiceOrInventingAPendingClear() {
        var request=request();var port=new OriginalCash();port.unavailable=true;var read=collector(port).loan(request);
        assertInstanceOf(OrdinaryFinanceCollector.Unavailable.class,read);assertEquals(1,port.calls);
        var after=OrdinaryFinancePolicies.financingObservation(prior(),gap(request),read);
        assertInstanceOf(Text.class,after.detail().get("war_financing_loan_read_unavailable"));
        assertEquals(EmergencyFinancingAssessment.LoanStatus.NOT_PROVIDED,consumed(request,read).loan().status());
    }
    @Test void floatingNativeCostSurvivesTheNewLoanRequestBoundaryAndCannotAcquireEligibility() {
        var request=request();var port=new OriginalCash();Obj loan=object(port.cash.get("holy_order_loan_observation_v1"),"loan");
        Obj costs=object(loan.get("decision_costs"),"costs"),borrow=object(costs.get("borrow_decision"),"borrow");
        var vector=new java.util.ArrayList<>(array(borrow.get("costs_raw_by_native_index"),"cost vector"));vector.set(0,new DecimalValue("1.0"));
        costs=costs.with("borrow_decision",borrow.with("costs_raw_by_native_index",new Arr(vector)));
        port.cash=port.cash.with("holy_order_loan_observation_v1",loan.with("decision_costs",costs));
        var read=collector(port).loan(request);var actual=observed(read);
        Obj input=OrdinaryFinanceCollector.financingRequest(gap(request),Optional.of(actual),Nil.INSTANCE);
        assertTrue(new String(DriverJson.encode(input),StandardCharsets.UTF_8).contains("[1.0,"));
        var assessed=consumed(request,read);assertEquals(EmergencyFinancingAssessment.Eligibility.UNKNOWN,assessed.loan().eligibility());
        assertTrue(assessed.loan().declaredCostsRaw().isEmpty());assertEquals(900_000_000,assessed.loan().prospectivePrincipalRaw().orElseThrow());
    }
    @Test void constructionAndBorrowedReadersReuseTheIdenticalOriginalCashAndSerializeTheSameLoanRequest() {
        var request=request();var port=new OriginalCash();var collector=collector(port);var cash=collector.cash(request);
        var read=OrdinaryFinanceCollector.loanFromCash(request,cash);assertEquals(1,port.calls);
        var actual=observed(read);
        Obj input=OrdinaryFinanceCollector.financingRequest(gap(request),Optional.of(actual),obj("status",new Text("no_pending_action")));
        var restored=EmergencyFinancingAssessmentCodec.decode(DriverJson.encode(input));
        assertInstanceOf(LoanFinancingCodec.Projected.class,restored.loanInput());
        assertEquals(EmergencyFinancingAssessment.LoanStatus.NATIVE_GATES_REJECTED,EmergencyFinancingAssessmentCodec.assess(restored).loan().status());
        Session same=(Session)java.lang.reflect.Proxy.newProxyInstance(Session.class.getClassLoader(),new Class<?>[]{Session.class},
                (proxy,method,args)->{throw new AssertionError("loan READ must preserve the borrowed writer without replacing it");});
        assertInstanceOf(OrdinaryFinanceCollector.Known.class,collector.loan(same,request));assertSame(same,port.borrowed);assertEquals(2,port.calls);
    }
    private static Obj rawCash(boolean allowed,long principal) {
        Obj expense=json("""
                {"status":"unavailable","owner_character_id":1,"resource_id":"1","war_ids":[9],"raw_scale":100000,"time_basis":"month",
                 "source_scope":"actor_owned_military_once_across_all_wars","future_war_cost_upper_ready":false,
                 "resource_raw_native":null,"gold_raw":null,"treasury_raw":null,"unavailable_reason":"not sampled"}
                """);
        Obj costs=json("""
                {"schema":"ck3_12004_holy_order_loan_decision_costs_v1","game_version":"1.20.0.4","read_only":true,
                 "scope":"decision_gates_and_costs_only","available":true,"unavailable_reason":null,"capture_epoch":123,"date_raw":100,
                 "played_character_id":1,"raw_scale":100000,"resource_slot_count":10,"complete_loan_terms":false,"principal_quote_raw":null,
                 "typed_debt":null,"funding_credit_raw":0,"submit_planned":false,
                 "borrow_decision":{"decision_id":"borrow_from_holy_order_decision","is_shown":true,"can_take":false,"affordable":true,"costs_raw_by_native_index":[-5,-4,-3,-2,-1,0,1,2,3,4]},
                 "repay_decision":{"decision_id":"repay_loan_decision","is_shown":false,"can_take":true,"affordable":true,"costs_raw_by_native_index":[0,0,0,0,0,0,0,0,0,0]}}
                """).with("executable_sha256",new Text(SHA));
        costs=costs.with("borrow_decision",object(costs.get("borrow_decision"),"borrow").with("can_take",new Bool(allowed)));
        Obj loan=json("""
                {"schema":"xar.ck3.holy-order-loan-war-cash.v1","status":"available","read_only":true,"advertised":false,"formal_action_ready":false,
                 "source_frame":{"snapshot_revision":7,"ticket_sequence":12,"local_player_id":0,"played_character_id":1,"date_raw":100,
                  "full_snapshot_owner_retained":true,"same_frame_ready":true,"execution_stamp":{"pump_epoch":123,"thread_id":2,"rng_wrapper":3,
                   "rng_state":4,"rng_owner_thread_id":2,"tls_initialized_flag_address":5,"tls_initialized":1,"tls_context":6,
                   "tls_main_thread_marker":1,"jomini_state":7,"game_state":8,"date_raw":100,"paused":true}},
                 "decision_costs_unavailable_reason":null,"complete_loan_terms":false,"existing_debt_principal_raw":null,
                 "received_funds_verified":false,"funding_credit_raw":0,"submit_planned":false}
                """).with("decision_costs",costs).with("principal",obj("status",new Text("available"),"value_key",new Text("holy_order_gold_value"),
                        "raw_scale",n(100000),"prospective_principal_raw",n(principal),"owned_temporaries_released",new Bool(true),"unavailable_reason",Nil.INSTANCE));
        return obj("schema",new Text("xar.ck3.war-cash-current-resources.v1"),"game_version",new Text("1.20.0.4"),"executable_sha256",new Text(SHA),
                "status",new Text("partial"),"read_only",new Bool(true),"advertised",new Bool(false),"formal_action_ready",new Bool(false),
                "played_character_id",n(1),"snapshot_revision",n(7),"date_raw",n(100),"active_war_ids",new Arr(List.of(n(9))),"player_army_ids",new Arr(List.of()),
                "current_treasury",obj("raw",n(1000000),"scale",n(100000)),"player_monthly_net_income",Nil.INSTANCE,
                "military_expenses",obj("current",expense,"all_raised",expense),"readiness",obj("same_frame_ready",new Bool(true)),"holy_order_loan_observation_v1",loan);
    }
    private static Obj json(String value) {return DriverJson.object(value.getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES);}
    private static IntegerValue n(long value) {return new IntegerValue(BigInteger.valueOf(value));}
}
