package org.xar.ck3.control.nativebridge.capabilities.interactions;

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

/** Original Python oracle -> actual Finance ROOT/v2 decoder -> Family binding. Software packets grant no Root custody. */
final class FamilyRootBindingV2Test {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final BigInteger NATIVE=BigInteger.valueOf(17),DATE=BigInteger.valueOf(53182008);
    private static final ExactRef REF=new ExactRef("synthetic/root-original",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source("synthetic-family-root",NOW.toString(),Build.CROZIER4.version(),REF);
    @Test void publicVersionedProducerBindsItsOriginalFrameAndRejectsAliasesInternalCaptureAndBareNativeEquivalence() throws Exception {
        var definitions=new FinanceReadContracts(query->new FinanceReadContracts.Registration(REF,
                new FinanceReadContracts.Permission(Optional.empty(),query.operation().value(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
        var contract=definitions.contract(FinanceReadContracts.Query.ROOT);var context=context(56);
        var request=new PlanningReadRequest(context.before(),SOURCE,context.sessionId(),contract.operation(),
                FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY),context.deadline());
        assertEquals(StrictJson.object(),StrictJson.parse(contract.prepare(request,"root-query").additionalFields().bytes()));
        var receipt=receipt(request,contract.contractId(),oracle());var decoded=contract.replay(receipt);
        var value=decoded.result().with("queried_snapshot_id",new Text(context.before().frame().snapshotId()))
                .with("queried_revision",new IntegerValue(context.before().frame().revision())).with("queried_native_revision",new IntegerValue(NATIVE));
        var original=new PlanningReadResult.Known<>(value,receipt,REF);var basis=FamilyRootBinding.fromOriginal(original,context);
        assertEquals(98765,basis.binding().observedFirstHeir().orElseThrow());assertEquals(REF,basis.originalRootReceipt());
        var flat=new Obj(Map.of("expected_native_revision",new IntegerValue(NATIVE)));
        var args=FamilyRootBinding.arguments(basis,flat);
        var leaf=new PlanningReadRequest(context.before(),SOURCE,context.sessionId(),new OperationKey(FamilyHeirLegality.STEP),args,context.deadline());
        assertEquals(basis,FamilyRootBinding.decodeArguments(leaf,context,ref->{assertEquals(REF,ref);return original;}));
        var encoded=OpportunityJson.object(OpportunityJson.parse(OpportunityJson.encode(args)),"persisted root binding");assertEquals(args,encoded);
        var legacy=receipt(request,"ordinary-finance-read:ROOT",decoded.originalResult());
        assertThrows(IllegalArgumentException.class,()->FamilyRootBinding.fromOriginal(new PlanningReadResult.Known<>(value,legacy,REF),context));
        for(var invalid:List.of(new Obj(Map.of()),FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS))) {
            var changed=new PlanningReadRequest(context.before(),SOURCE,context.sessionId(),contract.operation(),invalid,context.deadline());
            var changedReceipt=receipt(changed,contract.contractId(),decoded.originalResult());
            assertThrows(IllegalArgumentException.class,()->FamilyRootBinding.fromOriginal(new PlanningReadResult.Known<>(value,changedReceipt,REF),context));
        }
        assertThrows(IllegalArgumentException.class,()->FamilyRootBinding.fromOriginal(original,context(57)),
                "same Native bytes/date/player do not grant a new public Driver lineage");
        var denied=new IllegalStateException("actual private historical lineage unavailable");
        var calls=new java.util.concurrent.atomic.AtomicInteger();
        var admission=new FamilyRootBinding.ReadLineageAdmission(){
            @Override public FamilyRootBinding.QualifiedOrigin origin(){return FamilyRootBinding.QualifiedOrigin.HISTORICAL_CANONICAL_READ;}
            @Override public void verifyOriginal(PlanningReadResult.Known<Obj> read,Context target){
                assertSame(original,read);assertEquals(context(57),target);calls.incrementAndGet();throw denied;
            }
        };
        assertSame(denied,assertThrows(IllegalStateException.class,()->FamilyRootBinding.fromQualifiedOriginal(original,context(57),admission)));
        assertEquals(1,calls.get(),"an origin marker cannot replace the actual Root admission");
        var closingCalls=new java.util.concurrent.atomic.AtomicInteger();
        var closingAdmission=new FamilyRootBinding.ReadLineageAdmission(){
            @Override public FamilyRootBinding.QualifiedOrigin origin(){return FamilyRootBinding.QualifiedOrigin.CURRENT_CANONICAL_READ;}
            @Override public void verifyOriginal(PlanningReadResult.Known<Obj> read,Context target){if(closingCalls.incrementAndGet()==2)throw denied;}
        };
        assertSame(denied,assertThrows(IllegalStateException.class,()->FamilyRootBinding.fromQualifiedOriginal(original,context(57),closingAdmission)));
        assertEquals(2,closingCalls.get(),"loss of the actual issuer at the closing boundary cannot return a qualified binding");
        var issuedOriginals=new FamilyRootBinding.Originals(){
            @Override public PlanningReadResult.Known<Obj> read(ExactRef reference){throw new AssertionError("leaf decoder must consume bind rather than bypass its qualified issuer");}
            @Override public FamilyRootBinding.Basis bind(ExactRef reference,Context target){assertEquals(REF,reference);throw denied;}
        };
        assertSame(denied,assertThrows(IllegalStateException.class,()->FamilyRootBinding.decodeArguments(leaf,context,issuedOriginals)));
        assertEquals(new IntegerValue(BigInteger.valueOf(56)),original.value().get("queried_revision"));
        var changedValue=value.with("queried_revision",new IntegerValue(BigInteger.valueOf(57)));
        assertThrows(IllegalArgumentException.class,()->FamilyRootBinding.fromOriginal(new PlanningReadResult.Known<>(changedValue,receipt,REF),context));
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
    private static String required(String key){String value=System.getProperty(key);assertTrue(value!=null&&!value.isBlank(),"required original producer property missing: "+key);return value;}
}
