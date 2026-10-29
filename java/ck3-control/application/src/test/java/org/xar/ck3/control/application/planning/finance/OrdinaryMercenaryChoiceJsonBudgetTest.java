package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.warbudget.OrdinaryWarPriority;

/** Pure public chooser and original-receipt decoder DATA. No writer, query or action is authorized. */
final class OrdinaryMercenaryChoiceJsonBudgetTest {
    private static final String EXE="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final ExactRef REF=new ExactRef("D:/fixture/mercenary-budget-source.java",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source("xenoamess-full-tower-eb9d2c1186","2026-10-29T00:00:00Z","1.20.0.4",REF);
    private static final Instant NOW=Instant.parse("2026-10-29T00:00:00Z"),DEADLINE=NOW.plusSeconds(30);
    private static final Obj EMPTY=new Obj(Map.of());

    @Test void emptyMarketWithAbsentRootStillProducesAssessment() {
        assertEmptyAssessment(assess(Optional.empty()));
    }
    @Test void emptyMarketWithPresentRootStillProducesAssessment() {
        assertEmptyAssessment(assess(Optional.of(EMPTY)));
    }
    @Test void publicAssessmentAboveOneMiBRetainsEveryOriginalCompanyWithoutAuthority() {
        var actual=assess(Optional.of(EMPTY),500);
        byte[] encoded=DriverJson.encode(actual.original());
        System.out.println("chooser_result_bytes="+encoded.length);
        assertTrue(encoded.length>1_048_576,"real chooser result must cross both old parser budgets");
        assertTrue(encoded.length<=4_194_304,"fixture must remain within the chooser output budget");
        List<Value> candidates=array(actual.original().get("candidates"),"actual chooser candidates");
        assertEquals(500,candidates.size());
        assertEquals(new IntegerValue(BigInteger.ZERO),object(candidates.getFirst(),"first original company").get("company_id"));
        assertEquals(new IntegerValue(new BigInteger("4294967294")),object(candidates.getLast(),"last original company").get("company_id"));
        assertEquals(Nil.INSTANCE,actual.original().get("selected_company_id"));assertTrue(actual.selected().isEmpty());
        assertFalse(actual.actionSubmissionQualified());assertEquals(BigInteger.ZERO,actual.fundingCreditRaw());
        assertEquals(actual.original(),DriverJson.object(encoded,4_194_304));
    }
    @Test void publicAssessmentStillRejectsResultsAboveFourMiB() {
        var rejected=assertThrows(IllegalArgumentException.class,()->assess(Optional.of(EMPTY),2000));
        assertEquals("chooser output exceeds 4 MiB",rejected.getMessage());
    }
    private static void assertEmptyAssessment(OrdinaryMercenaryChoice.Assessment actual) {
        assertEquals(new Text("xar.mercenary-reinforcement-tradeoff.v1"),actual.original().get("schema"));
        assertEquals(new Text("continue_existing_war_action"),actual.original().get("recommendation"));
        assertEquals(new Arr(List.of()),actual.original().get("candidates"));
        assertEquals(Nil.INSTANCE,actual.original().get("selected_company_id"));
        assertTrue(actual.selected().isEmpty());assertFalse(actual.actionSubmissionQualified());
        assertEquals(BigInteger.ZERO,actual.fundingCreditRaw());
        assertEquals(actual.original(),DriverJson.object(DriverJson.encode(actual.original()),4_194_304));
    }
    private static OrdinaryMercenaryChoice.Assessment assess(Optional<Obj> root) {
        return assess(root,0);
    }
    private static OrdinaryMercenaryChoice.Assessment assess(Optional<Obj> root,int companyCount) {
        var before=new ProposalLifecycle.ObservationIdentity(SOURCE.machineId(),
                new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,BigInteger.ONE,BigInteger.valueOf(100)),
                        "native:mercenary-budget",BigInteger.ONE,"episode-mercenary-budget"),1);
        Obj snapshot=row("""
                {"snapshot_id":"native:mercenary-budget","revision":1,"native_revision":1,"date_raw":100,
                 "episode_run_id":"episode-mercenary-budget","paused":true,"map_ready":true,
                 "played_character":{"character_id":1,"alive":true},"active_wars":[],"player_armies":[],
                 "played_character_gold":{"raw":50000000,"scale":100000},
                 "diagnostics":{"hello":{"expected_ck3_version":"1.20.0.4","expected_ck3_sha256":"%s"}}}
                """.formatted(EXE));
        var request=new PlanningRequest(before,SOURCE,"mercenary-budget-session",DEADLINE,
                new PlanningObservation(snapshot,List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        var priority=OrdinaryWarPriority.observe(new OrdinaryWarPriority.Input(DriverJson.encode(snapshot),
                root.<byte[]>map(DriverJson::encode).orElse(new byte[]{'n','u','l','l'})));
        var defs=new FinanceReadContracts(query->new FinanceReadContracts.Registration(REF,new FinanceReadContracts.Permission(
                Optional.empty(),query.operation().value(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
        var query=FinanceReadContracts.Query.MERCENARIES;var contract=defs.contract(query);
        var read=new PlanningReadRequest(before,SOURCE,request.sessionId(),query.operation(),EMPTY,DEADLINE);
        Obj context=row("""
                {"schema":"ck3_12004_player_mercenary_context_v1","game_version":"1.20.0.4","executable_sha256":"%s",
                 "actor_character_id":1,"date_raw":100,"capture_epoch":1,"read_only":true,"native_hire_mode":1,
                 "available":true,"unavailable_reason":null,"rows":[]}
                """.formatted(EXE));
        if(companyCount>0) {
            Obj company=row("""
                    {"company_id":0,"employer_id":null,"manager_slot_index":0,
                     "troop_strength":{"available":false,"unavailable_reason":"not observed","current_soldiers":null},
                     "final_terms":{"available":false,"unavailable_reason":"not observed","can_hire":null,"can_afford":null,
                      "payment_status":null,"resource_scale":100000,"resource_costs_raw":null,"hire_duration_months":null,
                      "can_hire_reasons_available":false,"can_hire_reason_literal":null,
                      "can_afford_reasons_available":false,"can_afford_reason_literal":null},
                     "location":{"company_home_title_id":null,"company_home_province_id":null,"hire_auto_raise_province_id":null,
                      "actor_active_war_count":0,"hire_auto_raise_attempted_in_active_war":false,"company_home_ready":false,
                      "company_home_failure":"not observed","company_home_source":"software DATA","hire_auto_raise_position_ready":false,
                      "hire_auto_raise_position_failure":"not observed","hire_auto_raise_position_source":"software DATA"}}
                    """);
            var companies=new java.util.ArrayList<Value>();
            for(int index=0;index<companyCount;index++)companies.add(company.with("company_id",new IntegerValue(
                    index==companyCount-1?new BigInteger("4294967294"):BigInteger.valueOf(index)))
                    .with("manager_slot_index",new IntegerValue(BigInteger.valueOf(index))));
            context=context.with("rows",new Arr(companies));
        }
        Obj result=new Obj(Map.of("step",new Text(query.operation().value()),"accepted",new Bool(true),
                "snapshot_revision",new IntegerValue(BigInteger.ONE),"player_mercenary_context",context));
        String id="software-mercenary-budget";
        var frame=new RawJson(DriverJson.encode(new Obj(Map.of("type",new Text("command_result"),
                "protocol_version",new IntegerValue(BigInteger.ONE),"request_id",new Text(id),"ok",new Bool(true),"result",result))));
        byte[] bytes=frame.bytes();byte[] packet=ByteBuffer.allocate(bytes.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).put(bytes).array();
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(DriverJson.encode(result))),frame,packet);
        var binding=new GuardEvidence(read.origin(),SOURCE,request.sessionId(),BigInteger.ONE,query.operation(),REF,REF,
                "software-data-only",NOW,DEADLINE,List.of());
        var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));
        var receipt=new PlanningReadReceipt(read,contract.contractId(),id,guard,guard,ack);
        var market=NativeMercenaryMarket.decode(contract.replay(receipt),request);
        Obj body=MercenaryProcurement.emptyFreshEpisode().original();byte[] original=DriverJson.encode(body);
        var document=new FinanceStatePort.Document(FinanceStatePort.Domain.MERCENARY,
                new ExactRef("D:/fixture/mercenary-budget-body.json",original.length,ActionCodec.sha256(original)),original);
        var ledger=new FinanceStatePort.Ledger(document,body,FinanceStatePort.Pending.CLEAR);
        var spending=new FeastBudgetPolicy.Observed(new FeastBudgetPolicy.Frame(BigInteger.ONE,BigInteger.ONE,BigInteger.valueOf(100),
                "native:mercenary-budget"),0,null,null);
        return OrdinaryMercenaryChoice.assess(request,OrdinaryPolicy.Draft.empty(),priority,market,root,ledger,spending);
    }
    private static Obj row(String json) {
        return DriverJson.object(json.getBytes(java.nio.charset.StandardCharsets.UTF_8),4_194_304);
    }
}
