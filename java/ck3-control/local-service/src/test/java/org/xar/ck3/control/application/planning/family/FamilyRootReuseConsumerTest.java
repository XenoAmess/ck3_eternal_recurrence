package org.xar.ck3.control.application.planning.family;

import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.service.root.RootFamilyCampaignRead;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual Python producer -> Finance decoder -> Family projection/serde/policy and shared heir consumer. Private Root proofs are not forged. */
final class FamilyRootReuseConsumerTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final BigInteger NATIVE=BigInteger.valueOf(17),DATE=BigInteger.valueOf(53182008);
    private static final ExactRef REF=new ExactRef("synthetic/root-original",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source("synthetic-family-root",NOW.toString(),Build.CROZIER4.version(),REF);
    private static PlanningReadResult.Known<Obj> root() throws Exception {
        var definitions=new FinanceReadContracts(q->new FinanceReadContracts.Registration(REF,new FinanceReadContracts.Permission(Optional.empty(),q.operation().value(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
        var contract=definitions.contract(FinanceReadContracts.Query.ROOT);var actual=context(56);
        var request=new PlanningReadRequest(actual.before(),SOURCE,actual.sessionId(),contract.operation(),FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY),actual.deadline());
        var receipt=receipt(request,contract.contractId(),oracle());var packet=contract.replay(receipt);
        return new PlanningReadResult.Known<>(RootFamilyCampaignRead.project(packet.result(),receipt),receipt,REF);
    }
    private static Obj snapshot(int revision) {
        var row=StrictJson.object().put("snapshot_id","native:17").put("revision",revision).put("native_revision",NATIVE).put("date_raw",DATE).put("episode_run_id","synthetic-family-root-episode");
        row.putObject("played_character").put("character_id",12345);return DriverJson.object(StrictJson.canonical(row),RawJson.MAXIMUM_BYTES);
    }
    @Test void actualProducerProjectionAndCurrentDataRoundTripReachSplitSuccessorWithoutRewritingOriginal()throws Exception {
        var original=root();var exact=FamilyChildPolicy.split(original.value(),snapshot(56));assertNotNull(exact);
        assertEquals(new IntegerValue(BigInteger.valueOf(87654)),exact.get("subject_character_id"));
        assertThrows(IllegalArgumentException.class,()->FamilyChildPolicy.split(original.value(),snapshot(57)));
        var data=FamilyRootCurrentFrame.observed(REF,original.receipt().request().before(),context(57).before());
        var view=original.value().with(FamilyRootCurrentFrame.FIELD,data.toJson());
        var restored=DriverJson.object(DriverJson.encode(view),RawJson.MAXIMUM_BYTES);
        assertEquals(data,FamilyRootCurrentFrame.fromJson((Obj)restored.get(FamilyRootCurrentFrame.FIELD)));
        var split=FamilyChildPolicy.split(restored,snapshot(57));assertEquals(exact.get("subject_character_id"),split.get("subject_character_id"));
        assertEquals(new IntegerValue(BigInteger.valueOf(57)),split.get("source_revision"));
        assertEquals(new IntegerValue(BigInteger.valueOf(56)),restored.get("queried_revision"));
        assertEquals(BigInteger.valueOf(56),original.receipt().request().before().frame().revision());
        // DATA passes a pure policy comparison, but cannot satisfy the mandatory native Root issuer.
        assertThrows(IllegalArgumentException.class,()->FamilyRootBinding.fromOriginal(new PlanningReadResult.Known<>(restored,original.receipt(),REF),context(57)));
        var denied=new IllegalStateException("no actual private lineage");
        var originals=new FamilyRootBinding.Originals(){
            @Override public PlanningReadResult.Known<Obj> read(ExactRef ref){assertEquals(REF,ref);return original;}
            @Override public FamilyRootBinding.Basis bind(ExactRef ref,Context target){throw denied;}
        };
        assertSame(denied,assertThrows(IllegalStateException.class,()->FamilyHeirNativeProjection.subject(original,context(57),originals)));
    }
    @Test void missingNullWrongTypedAndChangedTargetDataAreRejectedByTheActualPolicyConsumer()throws Exception {
        var original=root();var data=FamilyRootCurrentFrame.observed(REF,original.receipt().request().before(),context(57).before());
        var encoded=jsonObject(DriverJson.toNode(data.toJson()));
        for(String key:List.of("original_revision","public_revision","native_revision")) {
            var numeric=encoded.deepCopy();numeric.put(key,57);assertThrows(IllegalArgumentException.class,()->FamilyRootCurrentFrame.fromJson(DriverJson.object(StrictJson.canonical(numeric),RawJson.MAXIMUM_BYTES)));
            var changed=encoded.deepCopy();changed.put(key,"057");var invalid=changed;assertThrows(IllegalArgumentException.class,()->FamilyRootCurrentFrame.fromJson(DriverJson.object(StrictJson.canonical(invalid),RawJson.MAXIMUM_BYTES)));
        }
        for(String key:List.of("snapshot_id","episode_run_id","played_character_id","date_raw","public_revision")) {
            var changed=encoded.deepCopy();if(key.equals("snapshot_id")||key.equals("episode_run_id"))changed.put(key,"changed");else if(key.equals("public_revision"))changed.put(key,"58");else changed.put(key,1);
            Obj view=original.value().with(FamilyRootCurrentFrame.FIELD,DriverJson.object(StrictJson.canonical(changed),RawJson.MAXIMUM_BYTES));
            assertThrows(IllegalArgumentException.class,()->FamilyChildPolicy.split(view,snapshot(57)));
        }
        for(Value invalid:List.of(Nil.INSTANCE,new Bool(true),new Text("marker")))
            assertThrows(IllegalArgumentException.class,()->FamilyChildPolicy.split(original.value().with(FamilyRootCurrentFrame.FIELD,invalid),snapshot(57)));
    }
    @Test void currentFrameDataUsesFullWidthDecimalRevisionsAndRejectsBooleanFloatingAndExtraFields() {
        var data=new FamilyRootCurrentFrame(REF,BigInteger.valueOf(56),"native:17",new BigInteger("18446744073709551615"),NATIVE,DATE,"synthetic-family-root-episode",BigInteger.valueOf(12345));
        var row=jsonObject(DriverJson.toNode(data.toJson()));assertTrue(row.get("public_revision").isTextual());
        assertEquals(data,FamilyRootCurrentFrame.fromJson(DriverJson.object(StrictJson.canonical(row),RawJson.MAXIMUM_BYTES)));
        for(String field:List.of("played_character_id","date_raw")) {
            var bool=row.deepCopy();bool.put(field,true);assertThrows(IllegalArgumentException.class,()->FamilyRootCurrentFrame.fromJson(DriverJson.object(StrictJson.canonical(bool),RawJson.MAXIMUM_BYTES)));
            var floating=row.deepCopy();floating.put(field,12345.0);assertThrows(IllegalArgumentException.class,()->FamilyRootCurrentFrame.fromJson(DriverJson.object(StrictJson.canonical(floating),RawJson.MAXIMUM_BYTES)));
        }
        var extra=row.deepCopy();extra.put("ready",true);assertThrows(IllegalArgumentException.class,()->FamilyRootCurrentFrame.fromJson(DriverJson.object(StrictJson.canonical(extra),RawJson.MAXIMUM_BYTES)));
    }
    @Test void actualHeirProducerAndSharedValidatorReachTheSoleFacadeBeforeLeafReadAndRejectChangedSubject()throws Exception {
        var original=root();var roots=(FamilyRootBinding.Originals)(reference->{assertEquals(REF,reference);return original;});
        var projected=FamilyHeirNativeProjection.subject(original,context(56),roots);
        assertInstanceOf(PlanningReadResult.Known.class,projected);
        var subject=((PlanningReadResult.Known<HeirSubject>)projected).value();
        assertEquals(98765,subject.firstHeir().value());
        var validationCalls=new java.util.concurrent.atomic.AtomicInteger();var readCalls=new java.util.concurrent.atomic.AtomicInteger();
        var corrupt=new java.util.concurrent.atomic.AtomicBoolean();
        var source=new InteractionCapabilities.RootHeirSource(){
            @Override public PlanningReadResult<HeirSubject> read(Context target){
                var value=corrupt.get()?new HeirSubject(new CharacterId(87654),subject.rootQuerySequence(),REF):subject;
                return new PlanningReadResult.Known<>(value,original.receipt(),original.originalReceipt());
            }
            @Override public PlanningReadResult<HeirSubject> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,Context target){throw new AssertionError("no private borrowed Session fixture");}
            @Override public HeirSubject requireSubject(Context target,PlanningReadResult.Known<HeirSubject> actual){
                validationCalls.incrementAndGet();return FamilyHeirNativeProjection.requireSubject(actual,target,roots);
            }
        };
        var refs=new InteractionCapabilities.Sources(REF,REF,REF,REF,REF,REF,REF,REF,REF,REF);
        var installation=new InteractionCapabilities.Installation(refs,new InteractionCapabilities.ReadPlan(List.of(),List.of(),List.of()),source);
        var reads=new PlanningReadPort(){
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){
                assertSame(installation.heirLegality(),contract);readCalls.incrementAndGet();
                var args=DriverJson.toNode(request.arguments());assertEquals(98765,args.get("first_heir_id").intValue());
                assertEquals(REF,ExactRef.fromJson(args.get("root_evidence")));
                assertEquals(StrictJson.object(),StrictJson.parse(contract.prepare(request,"actual-heir-leaf").additionalFields().bytes()));
                return new PlanningReadResult.Unavailable<>("software_read_stops_before_native",Optional.empty());
            }
        };
        var actions=new ActionCoordinatorPort(){
            @Override public ActionReceipt execute(ActionCommand command){throw new AssertionError("read cannot submit");}
            @Override public ActionReceipt reconcile(String actionId){throw new AssertionError("read cannot reconcile");}
        };
        var facade=new InteractionCapabilities(installation,reads,actions);
        assertInstanceOf(PlanningReadResult.Unavailable.class,facade.queryObservedFirstHeirMarriageLegalityV1(context(56)));
        assertEquals(1,validationCalls.get());assertEquals(1,readCalls.get());
        corrupt.set(true);assertThrows(IllegalArgumentException.class,()->facade.queryObservedFirstHeirMarriageLegalityV1(context(56)));
        assertEquals(2,validationCalls.get());assertEquals(1,readCalls.get());
    }
    private static Context context(int publicRevision) {
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(12345),NATIVE,DATE),
                "native:17",BigInteger.valueOf(publicRevision),"synthetic-family-root-episode");
        var before=new ObservationIdentity(SOURCE.machineId(),new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),frame,1);
        return new Context(before,SOURCE,"synthetic-family-root-session",BigInteger.TWO,Build.CROZIER4,NOW.plusSeconds(30),
                new ControlFrame(true,true,true,1,19L,12345,"synthetic-family-root-episode",false,null,null,List.of()));
    }
    private static PlanningReadReceipt receipt(PlanningReadRequest request,String contractId,Obj result)throws Exception {
        var frame=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","root-query").put("ok",true);
        frame.set("result",OpportunityJson.toNode(result));byte[] bytes=StrictJson.canonical(frame);
        var ack=new NativeActionPort.AckReceived("root-query",true,Optional.of(new RawJson(OpportunityJson.encode(result))),new RawJson(bytes),NativeWire.packet(bytes));
        var binding=new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.TWO,request.operation(),REF,REF,"synthetic-root-authority",NOW,NOW.plusSeconds(60));
        var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));return new PlanningReadReceipt(request,contractId,"root-query",guard,guard,ack);
    }
    private static Obj oracle()throws Exception {
        Path root=Path.of(required("xar.repository.root")).toAbsolutePath().normalize();
        Path producer=root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/campaign_root_context_contract.py");
        Path fixture=root.resolve("ck3_autonomous_player/tests/unit/test_campaign_root_context_v1_bridge.py");
        assertEquals("06fa8e6399672106409a8f840ee96e8c1897b09688176a8704484bd18e6cb3f3",DriverJson.sha256(Files.readAllBytes(producer)));
        assertEquals("602e8b19cfdca2af35bb8723bdb445114005695a3280390516b5a4fc30e8ce82",DriverJson.sha256(Files.readAllBytes(fixture)));
        String script="""
            import ast,json,pathlib,sys
            sys.dont_write_bytecode=True
            root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge import campaign_root_context_contract as producer
            assert pathlib.Path(producer.__file__).resolve()==pathlib.Path(sys.argv[2]).resolve()
            namespace=dict(vars(producer));namespace.update(NATIVE_REVISION=17,DATE_RAW=53182008,PLAYER_CHARACTER_ID=12345)
            tree=ast.parse(pathlib.Path(sys.argv[3]).read_text(encoding='utf-8'))
            names={'_readiness','_provenance','_related_contexts','_council','_frame'}
            exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),sys.argv[3],'exec'),namespace)
            raw=namespace['_frame']();raw['provenance']=dict(producer._PROVENANCE_BY_BUILD['1.20.0.4'])
            normalized=producer.normalize_campaign_root_context_v1(raw,expected_date_raw=53182008,expected_snapshot_revision=17)
            print(json.dumps(dict(step='query-campaign-root-context-v1',accepted=True,status=normalized['status'],query_sequence=7,snapshot_revision=17,campaign_root_context=raw,backend_id='native-headless'),separators=(',',':')))
            """;
        var builder=new ProcessBuilder(required("xar.native.producer.python"),"-I","-B","-c",script,root.toString(),producer.toString(),fixture.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.redirectErrorStream(true);var child=builder.start();
        try {
            var output=java.util.concurrent.CompletableFuture.supplyAsync(()->{try{return child.getInputStream().readNBytes(1_048_577);}catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}});
            assertTrue(child.waitFor(30,TimeUnit.SECONDS),"original campaign root producer timed out");byte[] bytes=output.get(5,TimeUnit.SECONDS);
            assertEquals(0,child.exitValue(),new String(bytes,StandardCharsets.UTF_8));assertTrue(bytes.length<=1_048_576);
            return DriverJson.object(bytes,1_048_576);
        }finally{if(child.isAlive())child.destroyForcibly();}
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode jsonObject(com.fasterxml.jackson.databind.JsonNode value){if(value instanceof com.fasterxml.jackson.databind.node.ObjectNode object)return object;throw new IllegalArgumentException("JSON object required");}
    private static String required(String key){String value=System.getProperty(key);assertTrue(value!=null&&!value.isBlank(),"required original producer property missing: "+key);return value;}
}
