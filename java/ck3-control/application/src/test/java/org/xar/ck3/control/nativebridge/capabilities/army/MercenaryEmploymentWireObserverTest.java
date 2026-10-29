package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Original Python normalizer over source-derived SOFTWARE DATA; no native capture, live employment or read/action authority. */
final class MercenaryEmploymentWireObserverTest {
    private static final String MACHINE="xenoamess-full-tower-eb9d2c1186";
    private static final String EXE="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final Instant NOW=Instant.parse("2026-10-29T16:00:00Z");
    private static final ExactRef REF=new ExactRef("software-data-not-native-authority",1,"a".repeat(64));
    private static ObjectNode originals;
    @BeforeAll static void originalNormalizer() throws Exception {
        originals=BattleOriginalOracle.call("""
                import importlib.util,json,copy
                path=root/'ck3_autonomous_player'/'tests'/'unit'/'test_mercenary_query_mcp_result.py'
                spec=importlib.util.spec_from_file_location('xar_employment_original_fixture',path)
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                from xar_autoplayer.bridge.player_mercenary_context import normalize_player_mercenary_context_v1
                case=module.MercenaryQueryMcpResultTests('test_registered_AUTO_keeps_complete_numbers_frame_and_hire_terms_without_pretty_copy')
                case.setUp()
                try:
                    cases=[]
                    for actor in (-2147483648,-2147483643,-67108906,-2,0,1,67108906,2147483647):
                        snapshot=copy.deepcopy(case.snapshot)
                        snapshot['played_character']['character_id']=actor
                        market=copy.deepcopy(case.query['player_mercenary_context'])
                        market['actor_character_id']=actor
                        market['rows']=market['rows'][:1]
                        market['rows'][0]['employer_id']=actor & 0xFFFFFFFF
                        normalized=normalize_player_mercenary_context_v1(market,snapshot=snapshot)
                        cases.append({'actor':actor,'market':normalized})
                    print(json.dumps({'software_source_derived_not_native':True,'cases':cases},allow_nan=False))
                finally:case.tearDown()
                """,ArmyJson.empty());
        assertTrue(originals.path("software_source_derived_not_native").asBoolean());
    }
    private static Obj asObject(com.fasterxml.jackson.databind.JsonNode node){return DriverJson.object(ArmyJson.bytes(node),DriverJson.MAX_NATIVE_BYTES);}
    private static ObservationIdentity observation(BigInteger actor,BigInteger date,long revision){
        var nativeFrame=new JointBudgetSelector.Frame(NativeCharacterId.of(actor).asBigInteger(),BigInteger.valueOf(revision),date);
        var frame=new JointBudgetSelector.ProposalFrame(nativeFrame,"software-"+revision,BigInteger.valueOf(revision),"software-episode");
        return new ObservationIdentity(MACHINE,new GameGeneration(17,new PythonOnlyUInt64(BigInteger.valueOf(100))),frame,1);
    }
    private static Obj snapshot(ObservationIdentity identity){
        return OrdinaryFinanceCollector.sourceFrame(identity)
                .with("played_character",obj("character_id",new IntegerValue(identity.frame().identity().player()),"alive",new Bool(true)))
                .with("active_wars",new Arr(List.of())).with("player_armies",new Arr(List.of(obj(
                        "army_id",new IntegerValue(new BigInteger("4294967294")),"soldiers",new IntegerValue(BigInteger.valueOf(50)),
                        "current_province_id",new IntegerValue(BigInteger.valueOf(12)),"controllable",new Bool(true)))))
                .with("paused",new Bool(true)).with("map_ready",new Bool(true))
                .with("played_character_gold",obj("raw",new IntegerValue(BigInteger.valueOf(49000000)),"scale",new IntegerValue(BigInteger.valueOf(100000))))
                .with("diagnostics",obj("hello",obj("expected_ck3_version",new Text("1.20.0.4"),"expected_ck3_sha256",new Text(EXE))));
    }
    private static MercenaryProcurement.Ledger pending(ObservationIdentity before,BigInteger company){
        Obj selected=obj("company_id",new IntegerValue(company),"gold_cost_raw",new IntegerValue(BigInteger.valueOf(1000000)),
                "predicted_auto_raise_province_id",Nil.INSTANCE,"purpose_war_ids",new Arr(List.of()),
                "finance",obj("observed_treasury_raw",new IntegerValue(BigInteger.valueOf(50000000))));
        Obj claim=obj("action_request_id",new Text("software-pending-hire"),"company_id",new IntegerValue(company),
                "status",new Text("submission_unresolved"),"pre_capture_epoch",new IntegerValue(BigInteger.ONE),
                "pre_player_army_ids",new Arr(List.of()),"source_frame",OrdinaryFinanceCollector.sourceFrame(before),
                "decision",obj("selected_candidate",selected));
        return MercenaryProcurement.decode(DriverJson.encode(obj("schema",new Text(MercenaryProcurement.SCHEMA),"pending",claim,"observed",new Arr(List.of()))));
    }
    private record Sample(MercenaryProcurement.Ledger pending,Obj snapshot,NativeMercenaryMarket.Observation market,
                          BigInteger actor,BigInteger company) { }
    private static Obj originalMarket(int ordinal){return asObject(originals.withArray("cases").get(ordinal).get("market"));}
    private static Obj companyRow(Obj market){return object(array(market.get("rows"),"normalizer rows").getFirst(),"normalizer company");}
    private static Obj withRow(Obj market,Obj company){return market.with("rows",new Arr(List.of(company)));}
    private static Obj withCompany(Obj market,BigInteger company){
        Obj row=companyRow(market).with("company_id",new IntegerValue(company))
                .with("manager_slot_index",new IntegerValue(company.and(new BigInteger("16777215"))));
        if(row.get("composition_v1") instanceof Obj composition)row=row.with("composition_v1",composition.with("company_id",new IntegerValue(company)));
        return withRow(market,row);
    }
    private static Sample sample(int ordinal,Obj market,BigInteger company){
        Obj original=originalMarket(ordinal);
        BigInteger actor=integer(original.get("actor_character_id"),"normalizer actor"),date=integer(original.get("date_raw"),"normalizer date");
        var current=observation(actor,date,11);Obj actual=snapshot(current);
        var source=new G2Source(MACHINE,NOW.toString(),"software-source-derived",REF);
        var definitions=new FinanceReadContracts(query->new FinanceReadContracts.Registration(REF,new FinanceReadContracts.Permission(
                Optional.of("game.command."+query.operation().value()),"game.command."+query.operation().value(),
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP)));
        var profile=definitions.contract(FinanceReadContracts.Query.MERCENARIES);
        var query=new PlanningReadRequest(current,source,"software-session",profile.operation(),obj(),NOW.plusSeconds(30));
        var binding=new GuardEvidence(current,source,"software-session",BigInteger.ONE,profile.operation(),REF,REF,"software-no-authority",NOW,NOW.plusSeconds(30));
        var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));
        Obj result=obj("step",new Text(profile.operation().value()),"accepted",new Bool(true),"snapshot_revision",new IntegerValue(BigInteger.valueOf(11)),"player_mercenary_context",market);
        String requestId="software-independent-employer-"+ordinal;
        RawJson frame=new RawJson(DriverJson.encode(obj("type",new Text("command_result"),"protocol_version",new IntegerValue(BigInteger.ONE),
                "request_id",new Text(requestId),"ok",new Bool(true),"result",result)));
        byte[] packet=ByteBuffer.allocate(frame.bytes().length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(frame.bytes().length).put(frame.bytes()).array();
        var ack=new NativeActionPort.AckReceived(requestId,true,Optional.of(new RawJson(DriverJson.encode(result))),frame,packet);
        var receipt=new PlanningReadReceipt(query,profile.contractId(),requestId,guard,guard,ack);
        var decoded=profile.replay(receipt);
        var observed=NativeMercenaryMarket.decode(decoded,current,source,"software-session",actual);
        return new Sample(pending(observation(actor,date,10),company),actual,observed,actor,company);
    }
    private static MercenaryProcurement.Ledger observe(Sample sample){
        return MercenaryProcurement.observeEmployment(sample.pending(),"software-pending-hire",sample.snapshot(),sample.market());
    }
    private static void proveObserved(Sample sample){
        var employment=observe(sample);BigInteger actor=sample.actor();
        assertTrue(employment.pending().isEmpty(),"original uint32 employer must match signed actor "+actor);
        assertEquals(MercenaryProcurement.Status.EMPLOYMENT_OBSERVED,employment.observed().getFirst().status());
        assertEquals(sample.company(),employment.observed().getFirst().company());
        assertEquals(new IntegerValue(actor),employment.observed().getFirst().original().get("employer_character_id"));
        assertEquals(new Bool(false),employment.observed().getFirst().original().get("payment_verified"));
        assertEquals(new Bool(false),employment.observed().getFirst().original().get("army_creation_verified"));
        assertEquals(employment.original(),MercenaryProcurement.decode(MercenaryProcurement.encode(employment)).original());
        Obj inventory=object(employment.observed().getFirst().original().get("post_hire_observations_v1"),"independent inventory");
        Obj army=object(array(inventory.get("new_observed_player_armies"),"full army IDs").getFirst(),"independent army");
        assertEquals(new IntegerValue(new BigInteger("4294967294")),army.get("army_id"));
        assertEquals(new IntegerValue(BigInteger.valueOf(12)),army.get("current_province_id"));
        for(String flag:List.of("payment_verified","army_creation_verified","company_to_new_army_binding_verified"))assertEquals(new Bool(false),inventory.get(flag));
    }
    @Test void originalNormalizerUInt32EmployerMatchesEverySignedActorIncludingZeroAndRetainsFullCompanyAndArmyDomains(){
        for(int i=0;i<originals.withArray("cases").size();i++)proveObserved(sample(i,originalMarket(i),BigInteger.ZERO));
        BigInteger company=new BigInteger("2164260867");proveObserved(sample(3,withCompany(originalMarket(3),company),company));
    }
    @Test void unknownRemainsPendingForSentinelNullWrongGenerationOtherCompanyStaleEpochAndUnavailableCollection(){
        Obj market=originalMarket(3),row=companyRow(market);
        var nonmatches=new java.util.ArrayList<Obj>();
        for(Value employer:List.of(Nil.INSTANCE,new IntegerValue(new BigInteger("4294967295")),new IntegerValue(BigInteger.TWO),
                new IntegerValue(new BigInteger("16777214")),new IntegerValue(new BigInteger("4294967293")),new IntegerValue(BigInteger.ZERO)))
            nonmatches.add(withRow(market,row.with("employer_id",employer)));
        nonmatches.add(withCompany(market,BigInteger.ONE));
        nonmatches.add(market.with("capture_epoch",new IntegerValue(BigInteger.ONE)));
        nonmatches.add(market.with("available",new Bool(false)).with("unavailable_reason",new Text("source-derived unavailable"))
                .with("rows",new Arr(List.of())));
        for(Obj value:nonmatches){
            var sample=sample(3,value,BigInteger.ZERO);var unresolved=observe(sample);
            assertTrue(unresolved.pending().isPresent());assertTrue(unresolved.observed().isEmpty());
            assertEquals(MercenaryProcurement.Status.SUBMISSION_UNRESOLVED,unresolved.pending().orElseThrow().status());
            assertEquals(MercenaryProcurement.NewHireBarrier.UNKNOWN_PENDING,MercenaryProcurement.barrier(sample.snapshot(),unresolved));
            assertEquals(unresolved.original(),MercenaryProcurement.decode(MercenaryProcurement.encode(unresolved)).original());
        }
    }
    @Test void malformedEmployerWireCannotBeCoercedIntoAnIdentity(){
        Obj market=originalMarket(3),row=companyRow(market);
        for(Value invalid:List.of(new IntegerValue(BigInteger.valueOf(-2)),new IntegerValue(new BigInteger("4294967296")),new Bool(true),
                new Text("4294967294"),parse("1.0".getBytes(java.nio.charset.StandardCharsets.UTF_8))))
            assertThrows(IllegalArgumentException.class,()->sample(3,withRow(market,row.with("employer_id",invalid)),BigInteger.ZERO));
        var absent=new java.util.LinkedHashMap<String,Value>(row.members());absent.remove("employer_id");
        assertThrows(IllegalArgumentException.class,()->sample(3,withRow(market,new Obj(absent)),BigInteger.ZERO));
    }
    @Test void originalPendingRequestCurrentActorEpisodeReceiptFrameAndUniqueCompanyStillBindTheObserver(){
        var sample=sample(3,originalMarket(3),BigInteger.ZERO);Obj actual=sample.snapshot();
        Obj otherActor=actual.with("played_character_id",new IntegerValue(BigInteger.ONE))
                .with("played_character",obj("character_id",new IntegerValue(BigInteger.ONE),"alive",new Bool(true)));
        for(Obj drift:List.of(otherActor,actual.with("episode_run_id",new Text("different-episode")),
                actual.with("revision",new IntegerValue(BigInteger.valueOf(12))),actual.with("snapshot_id",new Text("different-snapshot"))))
            assertThrows(IllegalArgumentException.class,()->MercenaryProcurement.observeEmployment(sample.pending(),"software-pending-hire",drift,sample.market()));
        assertThrows(IllegalArgumentException.class,()->MercenaryProcurement.observeEmployment(sample.pending(),"other-request",actual,sample.market()));
        Obj market=originalMarket(3),row=companyRow(market);var duplicate=sample(3,market.with("rows",new Arr(List.of(row,row))),BigInteger.ZERO);
        assertThrows(IllegalArgumentException.class,()->observe(duplicate));
        assertTrue(sample.pending().pending().isPresent());assertTrue(sample.pending().observed().isEmpty());
    }
}
