package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.InputStream;
import java.io.ByteArrayInputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.family.FamilyOrdinaryPolicy;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel;
import org.xar.ck3.control.wave3.planning.m5peacetimeassembly.PeacetimeAssemblyCodec;
import org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreats;
import org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreatsCodec;

/** Actual unchanged Python wartime tests -> same read-only policy -> complete immutable plan serialization.
 * Query snapshots/identities are software oracle inputs; no Native/Game, funding or action qualification is asserted. */
final class M5WartimeObservationOriginalTest {
    private static final Map<String,String> PINS=Map.of(
            "ck3_autonomous_player/src/xar_autoplayer/m5_formal_proposal_collector.py","6488c6f3ab6d930e37d8f9730285214ebbc700a8a6ec968124826b81b1c8172e",
            "ck3_autonomous_player/src/xar_autoplayer/m5_war_cash_resource_v1.py","9407f55149271a5bb7503d6bbbb2177b1ee734fc48fa176354a531b8bd9387ab",
            "ck3_autonomous_player/tests/unit/test_m5_formal_proposal_collector.py","dc31d3a5062a7568add69de9eae619e44302cdd8e463d9131148cc94d0814e2f");
    private static final String PROGRAM="""
            import copy,hashlib,inspect,json,pathlib,runpy,sys,unittest
            repo=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(repo/'ck3_autonomous_player'/'src'));sys.path.insert(0,str(repo/'ck3_autonomous_player'/'tests'/'unit'))
            names=['ck3_autonomous_player/src/xar_autoplayer/m5_formal_proposal_collector.py','ck3_autonomous_player/src/xar_autoplayer/m5_war_cash_resource_v1.py','ck3_autonomous_player/tests/unit/test_m5_formal_proposal_collector.py']
            before={n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in names}
            fixture=runpy.run_path(str(repo/names[2]));cls=fixture['M5WartimeObservationTests'];namespace=cls._plan.__globals__;original=namespace['plan_m5_wartime_query_only'];cases=[]
            def capture(driver,planned,**kwargs):
                frozen=copy.deepcopy(planned);snapshot=copy.deepcopy(kwargs['snapshot']);expected=original(driver,planned,**kwargs)
                cases.append({'name':inspect.currentframe().f_back.f_code.co_name,'snapshot':snapshot,'plan':frozen['plan'],'expected':copy.deepcopy(expected['plan'])})
                assert planned==frozen
                return expected
            namespace['plan_m5_wartime_query_only']=capture
            result=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromTestCase(cls).run(result)
            assert result.testsRun==8 and not result.failures and not result.errors and not result.skipped
            helper=cls();base=helper._construction();both=copy.deepcopy(base)
            both['candidate'].update(authored_monthly_income_delta_hundredths=5,old_authored_monthly_income_hundredths=65)
            capture(object(),helper._plan(both),snapshot=namespace['_snapshot'](),history=[],available_steps=set())
            for wrong in (True,70.0,'70'):
                changed=copy.deepcopy(base);changed['candidate']['authored_monthly_income_hundredths']=wrong;changed['candidate']['authored_monthly_income_delta_hundredths']=70
                capture(object(),helper._plan(changed),snapshot=namespace['_snapshot'](),history=[],available_steps=set())
            after={n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in names};assert before==after
            print(json.dumps({'pins':before,'original_tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'cases':cases},ensure_ascii=False,separators=(',',':')))
            """;
    private static Obj cached;
    @Test void actualWartimeProducerRetainsTotalAndDeltaAsDifferentFieldsAcrossCompleteSerialization()throws Exception {
        Obj corpus=oracle();assertEquals(12,rows(corpus.get("cases")).size());
        for(Obj sample:rows(corpus.get("cases"))) {
            Obj snapshot=object(sample.get("snapshot")),plan=object(sample.get("plan")),expected=object(sample.get("expected"));
            Obj actual=M5WartimeObservationPolicy.observe(snapshot,plan,MilitaryPlanInputs.frame(request(snapshot)));
            compare(expected,actual);assertEquals(actual,DriverJson.object(DriverJson.encode(actual),2*1024*1024));
            Obj observed=object(actual.get("m5_joint_wartime_observation"));
            assertEquals(new Bool(false),observed.get("formal_action_ready"));assertEquals(new Bool(true),observed.get("read_only"));
            assertEquals(plan.get("selected_step"),actual.get("selected_step"));assertEquals(plan.get("phase"),actual.get("phase"));
        }
    }
    @Test void actualMissingStaleAndCompleteFundingDiagnosticsAnnotateTheSameSelectedWarWork()throws Exception {
        ExactRef source=new ExactRef("software-original-wartime-observer",1,"a".repeat(64));
        var policy=new M5WartimeObservationPolicy(source,true);
        for(Obj sample:rows(oracle().get("cases"))) {
            Obj snapshot=object(sample.get("snapshot")),plan=object(sample.get("plan"));
            var prior=new OrdinaryPolicy.Draft(text(plan.get("policy")),text(plan.get("phase")),"original selected war read",
                    OrdinaryPolicy.Kind.ORDINARY,Optional.empty(),OrdinaryPolicy.Purpose.READ_ONLY,
                    Optional.of(org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain.war),plan);
            var result=assertInstanceOf(OrdinaryPolicy.Annotate.class,policy.evaluate(request(snapshot),prior));
            assertEquals(prior.command(),result.retained().command());assertEquals(prior.phase(),result.retained().phase());
            assertEquals(prior.reason(),result.retained().reason());assertEquals(prior.kind(),result.retained().kind());
            assertEquals(prior.domain(),result.retained().domain());assertEquals(prior.purpose(),result.retained().purpose());
            Obj annotated=result.retained().detail();
            var actualRisk=ParticipatingWarThreatsCodec.decodeNonPrimaryRisk(OpportunityJson.encode(annotated.get("m5_nonprimary_war_risk")));
            assertEquals(ParticipatingWarThreats.nonPrimaryRisk(ParticipatingWarThreatsCodec.observeSnapshot(OpportunityJson.encode(snapshot))),actualRisk);
            assertFalse(actualRisk.actionAuthorized());assertFalse(actualRisk.politicalAndTerritorialConsequencesAssessed());
            var originalFields=new LinkedHashMap<>(annotated.members());originalFields.remove("m5_nonprimary_war_risk");
            compare(object(sample.get("expected")),new Obj(originalFields));
            assertEquals(annotated,DriverJson.object(DriverJson.encode(annotated),2*1024*1024));
            assertEquals(prior.detail(),plan,"read-only annotation must retain the original immutable input");
        }
    }
    @Test void actualAnnotateKeepsNonleadingConsequencesUnassessedAndRetainsTheOriginalWarChoice()throws Exception {
        Obj sample=rows(oracle().get("cases")).getFirst();Obj snapshot=object(sample.get("snapshot"));
        Obj player=object(snapshot.get("played_character")).with("alive",new Bool(true));
        Obj first=object(OpportunityJson.array(snapshot.get("active_wars"),"original wars").getFirst());
        var enemy=new Obj(Map.of("army_id",new IntegerValue(BigInteger.valueOf(55)),"soldiers",new IntegerValue(BigInteger.valueOf(400))));
        first=first.with("source",new Text("native")).with("player_side",new Text("defender"))
                .with("player_is_primary_war_leader",new Bool(false)).with("enemy_armies",new Arr(List.of(enemy)));
        snapshot=snapshot.with("played_character",player).with("active_wars",new Arr(List.of(first)));
        Obj originalPlan=object(sample.get("plan"));
        ExactRef source=new ExactRef("software-original-risk-annotation",1,"c".repeat(64));
        var prior=new OrdinaryPolicy.Draft("original-policy","original-phase","original-reason",OrdinaryPolicy.Kind.ORDINARY,
                Optional.empty(),OrdinaryPolicy.Purpose.READ_ONLY,Optional.empty(),originalPlan);
        var policy=new M5WartimeObservationPolicy(source,true);
        var actual=assertInstanceOf(OrdinaryPolicy.Annotate.class,policy.evaluate(request(snapshot),prior));
        assertEquals(prior.command(),actual.retained().command());assertEquals(prior.policy(),actual.retained().policy());
        assertEquals(prior.phase(),actual.retained().phase());assertEquals(prior.reason(),actual.retained().reason());
        originalPlan.members().forEach((key,value)->assertEquals(value,actual.retained().detail().get(key)));
        var risk=assertInstanceOf(ParticipatingWarThreats.ObservedNonPrimaryRisk.class,
                ParticipatingWarThreatsCodec.decodeNonPrimaryRisk(OpportunityJson.encode(actual.retained().detail().get("m5_nonprimary_war_risk"))));
        assertEquals(List.of(integer(first.get("war_id")).intValueExact()),risk.nonPrimaryWarIds());
        assertEquals(ParticipatingWarThreats.NonPrimaryRiskStatus.UNASSESSED,risk.status());
        assertFalse(risk.actionAuthorized());assertFalse(risk.politicalAndTerritorialConsequencesAssessed());
        assertEquals(originalPlan,prior.detail());
    }
    /** The actual original producer's total-only building reaches the real current-cash adapter.
     * Domain submission is forbidden here because cash is explicitly unavailable; this is a deferral regression, not an owner-submit fixture. */
    @Test void originalBuildingSourceDefersOnlyItsSpendAndUsesAValidPlainPlannerReplacement()throws Exception {
        Obj input;
        try(var stream=getClass().getResourceAsStream("/m5peacetimeassembly/producer-golden-v1.json.gz")) {
            assertNotNull(stream,"the unchanged original source corpus is mandatory");byte[] compressed=stream.readNBytes(65537);assertTrue(compressed.length<=65536);
            assertEquals("61374f70cb7398c98bf88a16d7a797106ecdd47e1e8ee86c83b483461b5df6e6",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(compressed)));
            byte[] raw;try(var gzip=new GZIPInputStream(new ByteArrayInputStream(compressed))){raw=gzip.readNBytes(1048577);assertTrue(raw.length<=1048576);assertEquals(-1,gzip.read());}
            var corpus=StrictJson.parse(raw,1048576);assertEquals("MATCH",corpus.get("source_postcheck").textValue());
            var sample=java.util.stream.StreamSupport.stream(corpus.get("cases").spliterator(),false).filter(row->row.get("name").textValue().equals("gift-disabled")).findFirst().orElseThrow();
            assertTrue(sample.get("actual_native_driver_entry_executed").booleanValue());assertTrue(sample.get("actual_collector_executed").booleanValue());
            input=object(OpportunityJson.parse(StrictJson.canonical(sample.get("input"),131072)));
        }
        var source=new ExactRef("software-original-m5-total-cash-deferral",1,"c".repeat(64));
        var actual=PeacetimeAssemblyCodec.decodeHistoricalV1(OpportunityJson.encode(input));
        Obj candidate=object(actual.construction().originalQuery().get("candidate"));
        assertTrue(integer(candidate.get("authored_monthly_income_hundredths")).signum()>0);
        assertFalse(candidate.members().containsKey("authored_monthly_income_delta_hundredths"),"retain the real historical producer field contract rather than inserting an alias");
        var original=request(actual.initialSnapshot());
        var baseline=new OrdinaryPolicy.Draft("one-life-turn-v1","peace_growth","actual original life-advance baseline",OrdinaryPolicy.Kind.ORDINARY,
                Optional.empty(),OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),actual.baselinePlan());
        var family=new FamilyOrdinaryPolicy(source,new PlanningReadPort() {
            @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("no family query is allowed in this disabled-family cash-deferral fixture");}
        },new FamilyPorts.Reads(Map.of(),Map.of()),request->{throw new AssertionError("no family ledger query expected");},
                (r,o,a,p)->{throw new AssertionError("no family command is allowed");},(r,q,a,o)->{throw new AssertionError("no family material publication is allowed");},
                new FamilyPorts.Settings(true,false,false,false,Optional.empty()));
        var prior=new M5PeacetimePolicy.Prior(actual.before(),actual.constructionRelease());
        var policy=new M5PeacetimePolicy(source,new M5PeacetimePolicy.Options(true,false,false),new M5PeacetimePolicy.SourceCollector() {
            @Override public M5PeacetimePolicy.Prior prior(PlanningRequest request,OrdinaryPolicy.Draft draft){assertSame(original,request);return prior;}
            @Override public M5PeacetimePolicy.Capture capture(PlanningRequest request,OrdinaryPolicy.Draft draft,M5PeacetimePolicy.Prior preceding){
                assertSame(original,request);assertSame(prior,preceding);return new M5PeacetimePolicy.Capture(actual,new ConstructionEconomyModel.UnavailableCashObservation(),Optional.empty());
            }
        },new M5PeacetimePolicy.Consumers(forbidden(PlanningStage.CONSTRUCTION,source),forbidden(PlanningStage.FACTION_GIFT,source),family),
                (request,draft,decision)->{throw new AssertionError("the retained original source needs no new Root query");});
        var result=assertInstanceOf(OrdinaryPolicy.Replace.class,policy.evaluate(original,baseline),"a changed phase/reason must not violate Root's detail-only Annotate contract");
        assertEquals("m5_joint_construction_cash_budget_deferred",result.draft().phase());
        assertEquals(baseline.command(),result.draft().command());assertEquals(baseline.kind(),result.draft().kind());
        assertEquals(baseline.purpose(),result.draft().purpose());assertEquals(baseline.domain(),result.draft().domain());
        assertEquals(new Text("life-advance"),result.draft().detail().get("selected_step"));assertEquals(new Bool(false),result.draft().detail().get("m5_joint_formal_action_ready"));
        Obj quote=object(result.draft().detail().get("construction_private_query"));assertEquals(candidate,quote.get("candidate"));
        assertEquals(result.draft().detail(),DriverJson.object(DriverJson.encode(result.draft().detail()),2*1024*1024));
    }
    private static OrdinaryPolicy forbidden(PlanningStage actualStage,ExactRef source) {
        return new OrdinaryPolicy() {
            @Override public PlanningStage stage(){return actualStage;}
            @Override public ExactRef implementationSource(){return source;}
            @Override public Decision evaluate(PlanningRequest request,Draft previous){throw new AssertionError("an unavailable cash proof must never reach domain submission: "+actualStage);}
        };
    }
    private static void compare(Obj expected,Obj actual) {
        Obj a=object(actual.get("m5_joint_wartime_observation")),e=object(expected.get("m5_joint_wartime_observation"));
        // Language-specific rejection wording is diagnostic; error presence/type and every semantic field remain exact.
        Value ae=a.get("war_cash_error"),ee=e.get("war_cash_error");assertEquals(ee==Nil.INSTANCE,ae==Nil.INSTANCE);
        if(ee!=Nil.INSTANCE){assertFalse(text(ee).isBlank());assertFalse(text(ae).isBlank());}
        var ac=new LinkedHashMap<>(a.members());var ec=new LinkedHashMap<>(e.members());ac.remove("war_cash_error");ec.remove("war_cash_error");
        assertEquals(expected.with("m5_joint_wartime_observation",new Obj(ec)),actual.with("m5_joint_wartime_observation",new Obj(ac)));
    }
    private static PlanningRequest request(Obj snapshot) {
        var source=new G2Source("software-original-wartime-no-game","2026-10-24T00:00:00Z","1.20.0.4",new ExactRef("software-original-wartime-identity",1,"b".repeat(64)));
        var identity=new JointBudgetSelector.Frame(integer(object(snapshot.get("played_character")).get("character_id")),integer(snapshot.get("native_revision")),integer(snapshot.get("date_raw")));
        var frame=new JointBudgetSelector.ProposalFrame(identity,text(snapshot.get("snapshot_id")),integer(snapshot.get("revision")),text(snapshot.get("episode_run_id")));
        var before=new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),frame,1);
        return new PlanningRequest(before,source,"software-original-wartime-session",Instant.parse("2026-10-24T00:01:00Z"),
                new PlanningObservation(snapshot,List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static synchronized Obj oracle()throws Exception {
        Path repository=Path.of(required("xar.repository.root"));
        for(var pin:PINS.entrySet())assertEquals(pin.getValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(repository.resolve(pin.getKey())))),pin.getKey());
        if(cached!=null)return cached;
        Process process=new ProcessBuilder(required("xar.python"),"-B","-c",PROGRAM,repository.toString()).directory(repository.toFile()).start();
        try(var readers=Executors.newVirtualThreadPerTaskExecutor()) {
            var output=readers.submit(()->read(process.getInputStream()));var error=readers.submit(()->read(process.getErrorStream()));
            try {
                process.getOutputStream().close();assertTrue(process.waitFor(45,TimeUnit.SECONDS),"original producer timeout remains RED");
                byte[] raw=output.get(5,TimeUnit.SECONDS),err=error.get(5,TimeUnit.SECONDS);assertEquals(0,process.exitValue(),new String(err,StandardCharsets.UTF_8));
                cached=DriverJson.object(raw,2*1024*1024);assertEquals(new IntegerValue(BigInteger.valueOf(8)),cached.get("original_tests_run"));
                for(String field:List.of("failures","errors","skipped"))assertEquals(new IntegerValue(BigInteger.ZERO),cached.get(field));
                Obj pins=object(cached.get("pins"));PINS.forEach((name,sha)->assertEquals(new Text(sha),pins.get(name)));return cached;
            } finally {if(process.isAlive())process.destroyForcibly();}
        }
    }
    private static byte[] read(InputStream stream)throws IOException {byte[] raw=stream.readNBytes(2*1024*1024+1);if(raw.length>2*1024*1024)throw new IOException("bounded original wartime corpus exceeded");return raw;}
    private static String required(String key){String value=System.getProperty(key);assertNotNull(value,"complete CI step requires "+key);assertFalse(value.isBlank());return value;}
    private static Obj object(Value value){return OpportunityJson.object(value,"original wartime object");}
    private static List<Obj> rows(Value value){return OpportunityJson.array(value,"original wartime rows").stream().map(M5WartimeObservationOriginalTest::object).toList();}
    private static String text(Value value){return OpportunityJson.text(value,"original wartime text");}
    private static BigInteger integer(Value value){return OpportunityJson.integer(value,"original wartime integer");}
}
