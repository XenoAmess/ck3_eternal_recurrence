package org.xar.ck3.control.application.history;

import java.math.BigInteger;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.history.DriverEarlyExecuteFailure.*;
import org.xar.ck3.control.application.history.DriverEarlyExecuteFailure.Error;
import org.xar.ck3.control.application.history.DriverEarlyExecuteFailureRowProducer.*;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.junit.jupiter.api.Assertions.*;

/** Pure original DATA/oracle tests. No Source, invocation ticket, live Known, fresh frame or read permission is forged. */
final class DriverEarlyExecuteFailureRowProducerTest {
    private static final String COMMAND="query-player-mercenary-context-v1";
    private static final ExactRef SOURCE=new ExactRef("software-early-source",1,"a".repeat(64));
    private record Data(Memory archive,InvocationData invocation,RawHistoryRow row){}
    private static Error publicError(){return new Error(ErrorOrigin.MIGRATED_PUBLIC_FAULT,"ValueError",Optional.of("early source failed"));}
    private static Data data(Optional<Obj> report){return data(report,report.map(value->new PublicNumbers(List.of())));}
    private static Data data(Optional<Obj> report,Optional<PublicNumbers> numbers){
        var archive=new Memory();var driver=HistoryFixtures.driver(List.of());var driverRef=archive.preserveMaterial(RawJson.fullMaterial(driver.encode()));
        var stamp=new Obj(Map.of("driver_version",number(7),"episode_epoch",number(2),"game",DriverJson.fromNode(HistoryFixtures.game().toJson()),"episode_run_id",new Text("ep"),"driver_sha256",new Text(DriverJson.sha256(driver.encode()))));
        var known=new Obj(Map.of("schema",new Text(DriverSnapshotFacts.ORIGINAL_SCHEMA),"driver",DriverJson.object(driver.encode(),DriverJson.MAX_NATIVE_BYTES),"stamp",stamp,"original_history_basis",DriverObservationEvidenceReader.reference(SOURCE),"action_rows",new Arr(List.of()),"auxiliary",new Obj(Map.of("retained_payload",new Text("x".repeat(70_000)))),"loop",Nil.INSTANCE,"observation",Nil.INSTANCE));
        var knownRef=archive.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(known)));
        var caller=archive.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(new Obj(Map.of("step",new Text(COMMAND))))));
        var epoch=archive.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(new Obj(Map.of("original_epoch",number(2))))));
        var result=report.map(value->archive.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(value))));
        var invocation=new InvocationData(new OperationKey(COMMAND),publicError(),result,numbers,new CachedData(driverRef,knownRef,Optional.empty()),caller,epoch,Optional.empty(),Optional.empty(),9,"b".repeat(64),List.of(SOURCE));
        var invocationRef=archive.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(DriverEarlyExecuteFailureRowProducer.invocationJson(invocation))));
        return new Data(archive,invocation,new RawHistoryRow(1,new DriverEarlyExecuteFailureRowProducer.Source(invocation,invocationRef),report));
    }
    @Test void cachedOriginalsProduceOnlyFailedRowAndColdReplayDoesNotReadNativeOrWrite(){
        var data=data(Optional.empty());var archive=data.archive();int before=archive.materials.size();
        assertFalse(data.row().ok());assertFalse(data.row().toJson().members().containsKey("result"));
        var decoded=DriverEarlyExecuteFailureRowProducer.decode(data.row().encode());assertEquals(data.row(),decoded);
        assertEquals(decoded,DriverEarlyExecuteFailureRowProducer.replayOriginals(archive,decoded));assertEquals(before,archive.materials.size());
        assertTrue(((CachedData)data.invocation().retained()).originalKnown().bytes()>65_536);assertEquals(0,archive.nativeCalls);
    }
    @Test void absentAndNullJavaMessageRemainDistinctAndCannotMintHistoryRow(){
        var d=data(Optional.empty());var noFacts=new InvocationData(d.invocation().originalCommand(),new Error(ErrorOrigin.ACTUAL_JAVA_FAILURE,"java.io.IOException",Optional.empty()),Optional.empty(),Optional.empty(),new AbsentData(new Missing(List.of("complete cached Driver unavailable"))),d.invocation().caller(),d.invocation().epochManifest(),Optional.empty(),Optional.empty(),9,"b".repeat(64),List.of(SOURCE));
        var encoded=DriverEarlyExecuteFailureRowProducer.invocationJson(noFacts);assertEquals(Nil.INSTANCE,encoded.get("exception_message"));assertEquals(noFacts,DriverEarlyExecuteFailureRowProducer.decodeInvocation(DriverJson.encode(encoded)));
        assertThrows(IllegalArgumentException.class,()->new RawHistoryRow(1,new DriverEarlyExecuteFailureRowProducer.Source(noFacts,SOURCE),Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->new RawHistoryRow(0,d.row().source(),Optional.empty()));
        var empty=new Error(ErrorOrigin.ACTUAL_JAVA_FAILURE,"java.io.IOException",Optional.of(""));assertNotEquals(noFacts.error(),empty);assertEquals(noFacts.error().recorded(),empty.recorded());
        assertThrows(IllegalArgumentException.class,()->new Error(ErrorOrigin.MIGRATED_PUBLIC_FAULT,"java.io.IOException",Optional.of("bad")));
        assertThrows(IllegalArgumentException.class,()->new Error(ErrorOrigin.MIGRATED_PUBLIC_FAULT,"ValueError",Optional.empty()));
    }
    @Test void resultPresenceAndClosedFieldsRejectNullMissingBoolAndWrongOrigin(){
        var d=data(Optional.of(new Obj(Map.of("step",new Text(COMMAND),"accepted",new Bool(false)))));var row=d.row().toJson();
        assertEquals(d.row(),DriverEarlyExecuteFailureRowProducer.decode(d.row().encode()));
        for(String key:List.of("index","command","ok","error",DriverEarlyExecuteFailureRowProducer.SOURCE_FIELD))assertThrows(IllegalArgumentException.class,()->DriverEarlyExecuteFailureRowProducer.decode(DriverJson.encode(without(row,key))));
        for(Value bad:List.<Value>of(new Bool(true),new Text("1"),new DecimalValue("1.0"),Nil.INSTANCE))assertThrows(IllegalArgumentException.class,()->DriverEarlyExecuteFailureRowProducer.decode(DriverJson.encode(row.with("index",bad))));
        assertThrows(IllegalArgumentException.class,()->DriverEarlyExecuteFailureRowProducer.decode(DriverJson.encode(row.with("result",Nil.INSTANCE))));
        assertThrows(IllegalArgumentException.class,()->DriverEarlyExecuteFailureRowProducer.decode(DriverJson.encode(without(row,"result"))));
        var invocation=DriverEarlyExecuteFailureRowProducer.invocationJson(d.invocation());
        assertThrows(IllegalArgumentException.class,()->DriverEarlyExecuteFailureRowProducer.decodeInvocation(DriverJson.encode(invocation.with("error_origin",new Text("GUESSED_PYTHON")))));
        assertThrows(IllegalArgumentException.class,()->DriverEarlyExecuteFailureRowProducer.decodeInvocation(DriverJson.encode(invocation.with("extra",new Bool(true)))));
        assertThrows(IllegalArgumentException.class,()->DriverEarlyExecuteFailureRowProducer.decodeInvocation(DriverJson.encode(without(invocation,"retained"))));
    }
    @Test void foreignArchiveChangedCallerAndWrongCachedIndexRejectWithoutFallback(){
        var d=data(Optional.empty());assertThrows(RuntimeException.class,()->DriverEarlyExecuteFailureRowProducer.replayOriginals(new Memory(),d.row()));
        var wrongIndex=new RawHistoryRow(2,d.row().source(),Optional.empty());assertThrows(IllegalArgumentException.class,()->DriverEarlyExecuteFailureRowProducer.replayOriginals(d.archive(),wrongIndex));
        var id=d.invocation();var wrong=new InvocationData(new OperationKey("different-original-call"),id.error(),id.result(),id.publicNumbers(),id.retained(),id.caller(),id.epochManifest(),id.unsupportedCapabilities(),id.unresolvedAction(),id.headSequence(),id.headDigest(),id.producerSources());
        var changed=new RawHistoryRow(1,new DriverEarlyExecuteFailureRowProducer.Source(wrong,d.row().source().invocation()),Optional.empty());
        assertThrows(IllegalArgumentException.class,()->DriverEarlyExecuteFailureRowProducer.replayOriginals(d.archive(),changed));assertEquals(0,d.archive().nativeCalls);
    }
    @Test void actualOriginalPythonEarlyCatchNeverObtainsASecondSnapshot(@TempDir Path temporary)throws Exception {
        String repo=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");if(repo==null||python==null)throw new IllegalStateException("NOT_RUN: actual source/original Python inputs required");
        var source=Path.of(repo).resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py");var output=temporary.resolve("early-original.json");var error=temporary.resolve("early-original.stderr");
        var child=new ProcessBuilder(python,"-X","utf8","-c",ORIGINAL,source.toString()).redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if(!child.waitFor(20,TimeUnit.SECONDS)){child.destroyForcibly();throw new java.io.IOException("original early failure process timed out");}if(child.exitValue()!=0)throw new java.io.IOException(Files.readString(error));
        var actual=DriverJson.object(Files.readAllBytes(output),DriverJson.MAX_NATIVE_BYTES);assertEquals(number(1),actual.get("snapshots"));assertEquals(number(0),actual.get("unrecorded_calls"));
        var original=OpportunityJson.object(OpportunityJson.array(actual.get("rows"),"rows").getFirst(),"row");
        var d=data(Optional.empty());assertEquals(new Text("RuntimeError: original initial snapshot failed"),original.get("error"));
        assertEquals(without(original,"error"),without(without(d.row().toJson(),DriverEarlyExecuteFailureRowProducer.SOURCE_FIELD),"error"));
    }
    @Test void explicitPublicIntegerRolesAndLargeResultRetainOriginalNumericAndTextDomains(){
        var maximum=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);var result=new Obj(Map.of("native_revision",new IntegerValue(maximum),"accepted",new Bool(false)));
        var exposed=result.with("native_revision",new Text(maximum.toString()));var roles=PublicNumbers.fromResults(new RawJson(DriverJson.encode(result)),new RawJson(DriverJson.encode(exposed)));
        var d=data(Optional.of(result),Optional.of(roles));assertEquals(d.row(),DriverEarlyExecuteFailureRowProducer.replayOriginals(d.archive(),d.row()));
        assertEquals(exposed,DriverEarlyExecuteFailureRowProducer.publicNumbersFromSource(d.row().toJson().get(DriverEarlyExecuteFailureRowProducer.SOURCE_FIELD)).orElseThrow().toPublic(result));
        assertEquals(result,roles.fromPublic(exposed));assertTrue(d.row().result().orElseThrow().get("native_revision") instanceof IntegerValue);
        var large=data(Optional.of(new Obj(Map.of("partial_result",new Text("r".repeat(70_000))))));assertTrue(large.row().encode().length>65_536);
        assertEquals(large.row(),DriverEarlyExecuteFailureRowProducer.decode(large.row().encode()));assertEquals(large.row(),DriverEarlyExecuteFailureRowProducer.replayOriginals(large.archive(),large.row()));assertEquals(0,large.archive().nativeCalls);
    }
    @Test void historicalManifestIsOnlyAPreservedPointerAndNeverBecomesAFreshFrame(){
        var d=data(Optional.empty());var old=(CachedData)d.invocation().retained();var manifest=d.archive().preserveMaterial(RawJson.fullMaterial(DriverJson.encode(new Obj(Map.of("historical_source_only",new Bool(true))))));
        var original=DriverJson.object(d.archive().loadFullMaterial(old.originalKnown()).bytes(),DriverJson.MAX_NATIVE_BYTES);
        var changed=original.with("observation",DriverObservationEvidenceReader.reference(manifest));var known=d.archive().preserveMaterial(RawJson.fullMaterial(DriverJson.encode(changed)));
        var id=d.invocation();var info=new InvocationData(id.originalCommand(),id.error(),id.result(),id.publicNumbers(),new CachedData(old.beforeDriver(),known,Optional.of(manifest)),id.caller(),id.epochManifest(),id.unsupportedCapabilities(),id.unresolvedAction(),id.headSequence(),id.headDigest(),id.producerSources());
        var invocation=d.archive().preserveMaterial(RawJson.fullMaterial(DriverJson.encode(DriverEarlyExecuteFailureRowProducer.invocationJson(info))));var row=new RawHistoryRow(1,new DriverEarlyExecuteFailureRowProducer.Source(info,invocation),Optional.empty());
        assertEquals(row,DriverEarlyExecuteFailureRowProducer.replayOriginals(d.archive(),row));assertEquals(0,d.archive().nativeCalls);
        // This succeeds as byte/source DATA only; no Known or Native observation was reconstructed from the opaque manifest.
        assertEquals(Optional.of(manifest),((CachedData)row.source().retained()).historicalSource());
        var wrong=new InvocationData(id.originalCommand(),id.error(),id.result(),id.publicNumbers(),new CachedData(old.beforeDriver(),known,Optional.empty()),id.caller(),id.epochManifest(),id.unsupportedCapabilities(),id.unresolvedAction(),id.headSequence(),id.headDigest(),id.producerSources());
        assertThrows(IllegalArgumentException.class,()->DriverEarlyExecuteFailureRowProducer.replayOriginals(d.archive(),new RawHistoryRow(1,new DriverEarlyExecuteFailureRowProducer.Source(wrong,invocation),Optional.empty())));
    }
    @Test void optionalEpochManifestRoundtripsAbsentNullAndPresentWithoutCrossingStrictFields() {
        var d=data(Optional.empty());var id=d.invocation();
        var present=new InvocationData(id.originalCommand(),id.error(),id.result(),id.publicNumbers(),id.retained(),id.caller(),id.epochManifest(),id.unsupportedCapabilities(),id.unresolvedAction(),id.headSequence(),id.headDigest(),id.producerSources());
        var absent=new InvocationData(id.originalCommand(),id.error(),id.result(),id.publicNumbers(),id.retained(),id.caller(),Optional.<ExactRef>empty(),id.unsupportedCapabilities(),id.unresolvedAction(),id.headSequence(),id.headDigest(),id.producerSources());
        assertEquals(present,DriverEarlyExecuteFailureRowProducer.decodeInvocation(DriverJson.encode(DriverEarlyExecuteFailureRowProducer.invocationJson(present))));
        assertEquals(absent,DriverEarlyExecuteFailureRowProducer.decodeInvocation(DriverJson.encode(DriverEarlyExecuteFailureRowProducer.invocationJson(absent))));
        var obj=DriverEarlyExecuteFailureRowProducer.invocationJson(absent);
        var nullEpoch=obj.with("epoch_manifest",Nil.INSTANCE);
        assertEquals(absent,DriverEarlyExecuteFailureRowProducer.decodeInvocation(DriverJson.encode(nullEpoch)));
        var missingEpoch=new LinkedHashMap<String,Value>(obj.members());missingEpoch.remove("epoch_manifest");
        assertEquals(absent,DriverEarlyExecuteFailureRowProducer.decodeInvocation(DriverJson.encode(new Obj(missingEpoch))));
        for(Value bad:List.<Value>of(new Bool(true),new Text("epoch"),new IntegerValue(BigInteger.ONE),new Arr(List.of()),new DecimalValue("1.0"),new Obj(Map.of())))
            assertThrows(IllegalArgumentException.class,()->DriverEarlyExecuteFailureRowProducer.decodeInvocation(DriverJson.encode(obj.with("epoch_manifest",bad))));
        ExactRef invocation=d.archive().preserveMaterial(RawJson.fullMaterial(DriverJson.encode(DriverEarlyExecuteFailureRowProducer.invocationJson(absent))));
        var row=new RawHistoryRow(1,new DriverEarlyExecuteFailureRowProducer.Source(absent,invocation),Optional.empty());
        var cold=DriverEarlyExecuteFailureRowProducer.decode(row.encode());var materials=Map.copyOf(d.archive().materials);
        assertEquals(row,DriverEarlyExecuteFailureRowProducer.replayOriginals(d.archive(),cold));
        assertEquals(materials,d.archive().materials);assertEquals(0,d.archive().nativeCalls);
    }
    private static IntegerValue number(long n){return new IntegerValue(BigInteger.valueOf(n));}
    private static Obj without(Obj row,String key){var fields=new LinkedHashMap<>(row.members());fields.remove(key);return new Obj(fields);}
    private static final String ORIGINAL="""
        import ast,copy,hashlib,json,sys,threading,types
        from pathlib import Path
        source=Path(sys.argv[1])
        if hashlib.sha256(source.read_bytes()).hexdigest()!='eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603':raise RuntimeError('actual native Driver source drift')
        tree=ast.parse(source.read_text(encoding='utf-8-sig'));cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='NativeHeadlessGameplayDriver')
        class StepError(Exception):pass
        class NativeError(Exception):pass
        scope={'copy':copy,'_RESTORE_CHECKPOINT_STEP':'restore-checkpoint','QUERY_ARMY_STRENGTHS_STEP':'query-army-strengths-v1','StepPostconditionError':StepError,'_NativeCommandRejectedError':NativeError,'finish_army_timing':lambda *a,**kw:None}
        def method(name):
            node=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name==name);node.decorator_list=[]
            exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(source),'exec'),scope);return scope[name]
        counts={'snapshots':0,'unrecorded_calls':0}
        owner=types.SimpleNamespace(_history_lock=threading.RLock(),_command_history=[],_persist_driver_state=lambda **kw:None)
        owner._record_command=types.MethodType(method('_record_command'),owner)
        def snapshot():
            counts['snapshots']+=1
            raise RuntimeError('original initial snapshot failed')
        def unrecorded(*a,**kw):
            counts['unrecorded_calls']+=1
            raise AssertionError('must not execute after original early snapshot failure')
        owner.take_snapshot_without_native_command_history=snapshot;owner._execute_step_unrecorded=unrecorded
        try:method('execute_step')(owner,'query-player-mercenary-context-v1',expected_revision=None)
        except RuntimeError as error:
            if str(error)!='original initial snapshot failed':raise
        else:raise AssertionError('actual original exception was swallowed')
        counts['rows']=owner._command_history;print(json.dumps(counts,separators=(',',':')))
        """;
    /** Isolated byte archive DATA, intentionally has no session/Native/source/issuer admission implementation. */
    private static final class Memory implements OutcomeArchive {
        private static final java.util.concurrent.atomic.AtomicInteger IDS=new java.util.concurrent.atomic.AtomicInteger();
        private final String namespace="early-data-"+IDS.incrementAndGet();
        private final Map<ExactRef,RawJson> materials=new LinkedHashMap<>();private int nativeCalls;
        @Override public ExactRef preserveMaterial(RawJson original){byte[] bytes=original.bytes();var ref=new ExactRef(namespace+"/"+DriverJson.sha256(bytes),bytes.length,DriverJson.sha256(bytes));materials.put(ref,RawJson.fullMaterial(bytes));return ref;}
        @Override public RawJson loadMaterial(ExactRef ref){var value=materials.get(ref);if(value==null)throw new IllegalArgumentException("foreign or missing original material");assertEquals(ref.bytes(),value.bytes().length);assertEquals(ref.sha256(),DriverJson.sha256(value.bytes()));return value;}
        @Override public RawJson loadFullMaterial(ExactRef ref){return loadMaterial(ref);}
        @Override public ExactRef materialReferenceOf(RawJson value){var ref=new ExactRef(namespace+"/"+DriverJson.sha256(value.bytes()),value.bytes().length,DriverJson.sha256(value.bytes()));loadMaterial(ref);return ref;}
        private UnsupportedOperationException noNative(){nativeCalls++;return new UnsupportedOperationException("DATA fixture has no Native/receipt/Source authority");}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){throw noNative();}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef value){throw noNative();}
        @Override public ExactRef preserveRequest(NativeRequest value){throw noNative();}
        @Override public NativeRequest loadRequest(ExactRef value){throw noNative();}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){throw noNative();}
        @Override public ExactRef requestReferenceOf(NativeRequest value){throw noNative();}
        @Override public ExactRef preserveRead(PlanningReadReceipt value){throw noNative();}
        @Override public PlanningReadReceipt loadRead(ExactRef value){throw noNative();}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value){throw noNative();}
        @Override public ExactRef preserveRecord(ActionRecord value){throw noNative();}
        @Override public ActionRecord loadRecord(ExactRef value){throw noNative();}
        @Override public ExactRef recordReferenceOf(ActionRecord value){throw noNative();}
        @Override public ExactRef preserveReceipt(ActionReceipt value){throw noNative();}
        @Override public ActionReceipt loadReceipt(ExactRef value){throw noNative();}
        @Override public ExactRef receiptReferenceOf(ActionReceipt value){throw noNative();}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw noNative();}
        @Override public byte[] loadNativeFrame(ExactRef value){throw noNative();}
    }
}
