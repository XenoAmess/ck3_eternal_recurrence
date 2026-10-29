package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.coatofarms.extensions.CoaUpload;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaService;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.*;
import static org.junit.jupiter.api.Assertions.*;

/** Real shared decoder -> original bounded manager -> native-envelope decoder -> shared public encoder.
 * The native packets here are software fixtures, never evidence of a live CK3 paste or rendered texture. */
final class CoaUploadProductionTest {
    private static final Binding MENU=new FrontendBinding(BigInteger.valueOf(3),4242);
    private static final String EXPORT_SOURCE="coa={\r\n pattern=\"pattern_solid.dds\"\r\n color1=blue\r\n}\r\n";
    private static final class Native implements CoaUpload.Runtime {
        Binding current=MENU;int calls;boolean fail;boolean driftAfter;
        java.util.concurrent.CountDownLatch entered,release;
        @Override public Binding current(BigInteger revision,String capability){assertEquals(current.revision(),revision);assertTrue(Set.of(CoaUpload.capability(PROBE_STEP),CoaUpload.capability(EXPORT_STEP)).contains(capability));return current;}
        @Override public ProbeResult probe(EncodedSource source,Binding binding,boolean large,boolean apply)throws IOException{
            calls++;if(entered!=null){entered.countDown();try{if(!release.await(5,java.util.concurrent.TimeUnit.SECONDS))throw new IOException("software native fixture timed out");}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}}
            if(fail)throw new IOException("software native UNKNOWN after possible submission");
            ProbeResult result=CoaCodec.nativeProbe(raw(nativeProbe(source,binding,apply)),source,binding,apply);
            if(driftAfter)current=new FrontendBinding(BigInteger.valueOf(4),4242);return result;
        }
        @Override public ExportResult export(Binding binding){calls++;return CoaCodec.nativeExport(raw(nativeExport(binding,EXPORT_SOURCE)),binding);}
    }
    private record Fixture(CoaUpload upload,FrontendCoaService service,Native nativePort,AtomicLong now){ }
    private static Fixture fixture(){AtomicLong now=new AtomicLong();AtomicLong token=new AtomicLong();Native actual=new Native();
        CoaUpload upload=new CoaUpload(new CoaUploads(now::get,()->String.format("%032x",token.incrementAndGet())),actual);
        return new Fixture(upload,new FrontendCoaService(List.of(new FrontendCoaService.ComponentBinding(CoaUpload.METHODS,upload))),actual,now);
    }
    private static ObjectNode invoke(Fixture f,Method method,ObjectNode args)throws Exception{return object(encode(f.service.execute(decode(method,raw(args)))));}
    private static ObjectNode metadata(byte[] source){return empty().put("source_sha256",sha256(source)).put("expected_revision","0").put("apply",true).put("expected_game_version",GAME_VERSION).put("expected_executable_sha256",EXE_SHA256);}
    private static ObjectNode beginArgs(byte[] source){int chunks=(source.length+CoaUploads.MAX_CHUNK-1)/CoaUploads.MAX_CHUNK;return metadata(source).put("total_bytes",source.length).put("chunk_count",chunks).put("chunk_encoding","base64");}
    private static ObjectNode commitArgs(ObjectNode received){ObjectNode n=empty();for(String key:List.of("upload_id","generation","chunk_count","source_sha256","expected_revision","apply","expected_game_version","expected_executable_sha256"))n.set(key,received.get(key));return n;}
    private static ObjectNode appendArgs(ObjectNode received,int index,byte[] chunk){return commitArgs(received).put("chunk_index",index).put("chunk_encoding","base64").put("chunk_bytes",chunk.length).put("chunk_sha256",sha256(chunk)).put("chunk_base64",Base64.getEncoder().encodeToString(chunk));}
    private static ObjectNode ready(Fixture f,byte[] source)throws Exception{
        ObjectNode received=invoke(f,Method.BEGIN,beginArgs(source));
        for(int offset=0,index=0;offset<source.length;offset+=CoaUploads.MAX_CHUNK,index++)invoke(f,Method.APPEND,appendArgs(received,index,java.util.Arrays.copyOfRange(source,offset,Math.min(source.length,offset+CoaUploads.MAX_CHUNK))));
        return received;
    }
    @Test void largeActualSourceConsumerCommitsOnceAndKeepsNativeResultSeparateFromGameEffect()throws Exception{
        Fixture f=fixture();byte[] source=("coat_of_arms={\r\n"+" colored_emblem={ depth=1 }\r\n".repeat(6000)+"}\r\n").getBytes(StandardCharsets.US_ASCII);
        assertTrue(source.length>V1_MAX_BYTES);ObjectNode received=ready(f,source);assertEquals(0,f.nativePort.calls);
        ObjectNode result=invoke(f,Method.COMMIT,commitArgs(received));assertEquals("committed",result.path("status").textValue());assertEquals(source.length,result.path("upload").path("received_bytes").intValue());
        assertEquals(sha256(source),result.path("result").path("source_sha256").textValue());assertTrue(result.path("result").path("applied").booleanValue());assertEquals(1,f.nativePort.calls);
        assertFalse(result.has("game_effect_verified"));assertFalse(result.has("rendered_texture_verified"));
        assertEquals(result,object(encode(new Response(raw(result)))));assertThrows(IllegalArgumentException.class,()->invoke(f,Method.COMMIT,commitArgs(received)));assertEquals(1,f.nativePort.calls);
    }
    @Test void consumedCommitDoesNotResubmitUnknownAndCompleteBindingDriftCannotBeAccepted()throws Exception{
        byte[] source="coa={}\r\n".getBytes(StandardCharsets.US_ASCII);
        Fixture unknown=fixture();ObjectNode pending=ready(unknown,source);unknown.nativePort.fail=true;
        assertThrows(IOException.class,()->invoke(unknown,Method.COMMIT,commitArgs(pending)));assertThrows(IllegalArgumentException.class,()->invoke(unknown,Method.COMMIT,commitArgs(pending)));assertEquals(1,unknown.nativePort.calls);
        Fixture changed=fixture();ObjectNode old=ready(changed,source);changed.nativePort.current=new FrontendBinding(BigInteger.valueOf(4),4242);
        assertThrows(IllegalArgumentException.class,()->invoke(changed,Method.COMMIT,commitArgs(old)));assertEquals(0,changed.nativePort.calls);
        Fixture after=fixture();ObjectNode first=ready(after,source);after.nativePort.driftAfter=true;assertThrows(IllegalArgumentException.class,()->invoke(after,Method.COMMIT,commitArgs(first)));assertEquals(1,after.nativePort.calls);
    }
    @Test void reservedWholePayloadExpiryConflictAndCanonicalWireBoundariesAreTheOriginalManager()throws Exception{
        Fixture budget=fixture();byte[] largest=new byte[V2_MAX_BYTES];java.util.Arrays.fill(largest,(byte)'a');
        invoke(budget,Method.BEGIN,beginArgs(largest));assertThrows(IllegalArgumentException.class,()->invoke(budget,Method.BEGIN,beginArgs(largest)));
        budget.now.set(60_000_000_000L);invoke(budget,Method.BEGIN,beginArgs(largest));
        Fixture order=fixture();byte[] payload="coa={}\r\n".getBytes(StandardCharsets.US_ASCII);ObjectNode received=invoke(order,Method.BEGIN,beginArgs(payload));
        ObjectNode bad=appendArgs(received,0,payload).put("chunk_base64","YQ==");assertThrows(IllegalArgumentException.class,()->invoke(order,Method.APPEND,bad));
        assertThrows(IllegalArgumentException.class,()->invoke(order,Method.APPEND,appendArgs(received,0,payload)));
        for(byte[] invalid:List.of(new byte[]{0},new byte[]{(byte)0x80})){Fixture f=fixture();ObjectNode r=invoke(f,Method.BEGIN,beginArgs(invalid));assertThrows(IllegalArgumentException.class,()->invoke(f,Method.APPEND,appendArgs(r,0,invalid)));}
        Fixture lf=fixture();ObjectNode r=ready(lf,"coa={}\n".getBytes(StandardCharsets.US_ASCII));assertThrows(IllegalArgumentException.class,()->invoke(lf,Method.COMMIT,commitArgs(r)));assertEquals(0,lf.nativePort.calls);
    }
    @Test void allSixUseOneSharedTypedContractRejectWrongKindsMissingNullUnsafeIdentityAndPaths()throws Exception{
        Fixture f=fixture();Set<String> original=new HashSet<>();for(var row:RootOriginalPublicTestInputs.tools())assertTrue(original.add(row.name()));for(Method m:CoaUpload.METHODS)assertTrue(original.contains(m.publicName()));
        for(JsonNode wrong:List.of(empty().booleanNode(true),empty().numberNode(1.0),empty().nullNode(),empty().numberNode(new BigInteger("18446744073709551615")))){
            ObjectNode args=empty();args.set("expected_revision",wrong);assertThrows(IllegalArgumentException.class,()->decode(Method.EXPORT,raw(args)));
        }
        assertEquals(new BigInteger("18446744073709551615"),((Revision)decode(Method.EXPORT,raw(empty().put("expected_revision","18446744073709551615")))).expectedRevision());
        for(String invalid:List.of("{}","{\"expected_revision\":null}","{\"expected_revision\":0,\"path\":\"C:/arbitrary\"}"))assertThrows(IllegalArgumentException.class,()->decode(Method.EXPORT,new RawJson(invalid.getBytes(StandardCharsets.US_ASCII))));
        ObjectNode r=invoke(f,Method.BEGIN,beginArgs("coa={}\r\n".getBytes(StandardCharsets.US_ASCII)));ObjectNode abort=empty();abort.set("upload_id",r.get("upload_id"));abort.set("generation",r.get("generation"));invoke(f,Method.ABORT,abort);
        assertEquals(0,f.nativePort.calls);assertThrows(IllegalArgumentException.class,()->f.upload.execute(new Empty(Method.TREE)));
    }
    @Test void probeCanonicalizesEditorNewlinesWhileExportCopiesEachExplicitInvocation()throws Exception{
        Fixture f=fixture();ObjectNode value=invoke(f,Method.PROBE,empty().put("source","coa={\n color1=blue\n}\n").put("expected_revision",0).put("apply",false));
        assertEquals(sha256("coa={\r\n color1=blue\r\n}\r\n".getBytes(StandardCharsets.US_ASCII)),value.path("source_sha256").textValue());assertFalse(value.path("paste_invoked").booleanValue());
        ObjectNode first=invoke(f,Method.EXPORT,empty().put("expected_revision",0));ObjectNode second=invoke(f,Method.EXPORT,empty().put("expected_revision",0));assertEquals(first,second);assertEquals(3,f.nativePort.calls);
        assertEquals(EXPORT_SOURCE,first.get("source").textValue());
    }
    @Test void boundedRamSessionDoesNotHoldTheNativeDispatchMonitor()throws Exception{
        Fixture f=fixture();byte[] source="coa={}\r\n".getBytes(StandardCharsets.US_ASCII);ObjectNode first=ready(f,source);ObjectNode second=invoke(f,Method.BEGIN,beginArgs(source));
        f.nativePort.entered=new java.util.concurrent.CountDownLatch(1);f.nativePort.release=new java.util.concurrent.CountDownLatch(1);
        try(var workers=java.util.concurrent.Executors.newFixedThreadPool(2)){
            var committing=workers.submit(()->invoke(f,Method.COMMIT,commitArgs(first)));assertTrue(f.nativePort.entered.await(2,java.util.concurrent.TimeUnit.SECONDS));
            try{var receiving=workers.submit(()->invoke(f,Method.APPEND,appendArgs(second,0,source)));assertEquals("ready",receiving.get(2,java.util.concurrent.TimeUnit.SECONDS).get("status").textValue());}
            finally{f.nativePort.release.countDown();}
            assertEquals("committed",committing.get(2,java.util.concurrent.TimeUnit.SECONDS).get("status").textValue());
        }
        assertEquals(1,f.nativePort.calls);
    }
    @Test void actualOriginalPythonMcpServiceAndManagerReachAllSixSharedJavaConsumers()throws Exception{
        // Mandatory explicit executables and repository. Never skip, use ambient Python, or import before configuring fixture paths.
        Path repository=Path.of(required("xar.repository.root")).toRealPath();Path python=Path.of(required("xar.python")).toRealPath();
        var process=new ProcessBuilder(python.toString(),"-c",ORIGINAL);
        process.directory(repository.toFile());process.redirectErrorStream(true);
        process.environment().put("XAR_SOURCE_REPOSITORY",repository.toString());process.environment().put("PYTHONPATH",repository.resolve("ck3_autonomous_player/src").toString());process.environment().put("PYTHONDONTWRITEBYTECODE","1");
        Process child=process.start();byte[] captured;
        try{captured=child.getInputStream().readNBytes(RawJson.MAXIMUM_BYTES+1);assertTrue(child.waitFor(60,java.util.concurrent.TimeUnit.SECONDS),"original Python producer timed out");assertEquals(0,child.exitValue(),new String(captured,StandardCharsets.UTF_8));}
        finally{if(child.isAlive())child.destroyForcibly();}
        assertTrue(captured.length<=RawJson.MAXIMUM_BYTES,"original producer output exceeded complete bounded corpus");JsonNode corpus=FullJsonTree.parse(captured,RawJson.MAXIMUM_BYTES);JsonNode rows=corpus.get("trace");assertTrue(rows.isArray());Fixture f=fixture();Set<Method> seen=new HashSet<>();
        for(JsonNode row:rows){Method method=Method.named(row.get("name").textValue());seen.add(method);assertTrue(row.get("arguments") instanceof ObjectNode);assertEquals(public64((ObjectNode)row.get("expected")),invoke(f,method,(ObjectNode)row.get("arguments")),method.publicName());}
        assertEquals(CoaUpload.METHODS,seen);assertEquals(3,f.nativePort.calls,"one commit, one direct probe, one direct Copy; RAM calls never dispatch");
        assertEquals(4,corpus.get("bindings").size());
        for(JsonNode original:corpus.get("bindings"))checkAllPublicBindingFormatters((ObjectNode)original);
    }
    private static void checkAllPublicBindingFormatters(ObjectNode original){
        // Original production binding normalizer supplies this corpus; native Copy has its own int32 date gate.
        // Formatting an admitted in-memory binding never grants that gate or claims a live native result.
        Binding b=CoaCodec.binding(raw(original));ObjectNode expected=original.deepCopy();
        for(String field:List.of("revision","native_revision","connection_generation","date_raw"))expected.put(field,expected.get(field).bigIntegerValue().toString());
        assertEquals(expected,binding(b));EncodedSource source=EncodedSource.encode("coa={}\r\n",false);
        CoaUploads manager=new CoaUploads(()->0L,()->"a".repeat(32));CoaUploads.Receipt received=manager.begin(new CoaUploads.Begin(source.sourceBytes(),source.sourceSha256(),1,"base64",new CoaUploads.Intent(b.revision(),false,GAME_VERSION,EXE_SHA256)),b);
        var probeResult=CoaCodec.nativeProbe(raw(nativeProbe(source,b,false)),source,b,false);
        var exportResult=new ExportResult(ExportStatus.EXPORTED,true,true,true,Optional.of(source.source()),Optional.of(source.sourceSha256()),source.sourceBytes(),Optional.empty(),b,BigInteger.ONE);
        for(ObjectNode result:List.of(upload(received),probe(probeResult),exported(exportResult))){assertEquals(expected,result.get("binding"));assertEquals(result,object(encode(new Response(raw(result)))));assertTrue(result.path("binding").path("date_raw").isTextual());}
        assertThrows(IllegalArgumentException.class,()->CoaCodec.binding(raw(expected)),"public decimal strings must not alias the original internal integer profile");
    }
    private static ObjectNode public64(ObjectNode original){
        ObjectNode out=original.deepCopy();String schema=out.path("schema").asText();
        if(schema.equals("coat-of-arms-source-upload-commit-v2")){out.set("upload",public64((ObjectNode)out.get("upload")));out.set("result",public64((ObjectNode)out.get("result")));return out;}
        for(String field:List.of("generation","expected_revision"))if(out.has(field)){assertTrue(out.get(field).isIntegralNumber());out.put(field,out.get(field).bigIntegerValue().toString());}
        if(out.get("binding") instanceof ObjectNode b)for(String field:List.of("revision","native_revision","connection_generation","date_raw"))if(b.has(field)){assertTrue(b.get(field).isIntegralNumber());b.put(field,b.get(field).bigIntegerValue().toString());}
        return out;
    }
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN_REQUIRED_ORIGINAL_COA_INPUT: missing -D"+key);return value;}
    private static final String ORIGINAL="""
import base64, copy, hashlib, importlib.util, itertools, json, os, pathlib, sys
repo=pathlib.Path(os.environ['XAR_SOURCE_REPOSITORY']).resolve(strict=True)
sys.path.insert(0,str(repo/'ck3_autonomous_player/src'))
def load(name,filename):
    spec=importlib.util.spec_from_file_location(name,repo/'ck3_autonomous_player/tests/unit'/filename)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
u=load('original_coa_upload_bridge','test_coat_of_arms_source_upload_v2_bridge.py')
e=load('original_coa_export_bridge','test_coat_of_arms_source_export_v1_bridge.py')
from xar_autoplayer.bridge.coat_of_arms_source_upload_v2 import CoatOfArmsSourceUploadManagerV2
from xar_autoplayer.bridge.coat_of_arms_source_probe_contract import normalize_coat_of_arms_source_v1_binding
from xar_autoplayer.bridge.mcp_server import _ck3_probe_coat_of_arms_source_v1, _ck3_export_coat_of_arms_source_v1
driver=u._Driver();driver.probe_coat_of_arms_source_v1=driver.probe_coat_of_arms_source_transport_v2
service=u.GameplayBridgeService(driver);tokens=itertools.count(1)
service._coat_of_arms_source_uploads_v2=CoatOfArmsSourceUploadManagerV2(clock=lambda:0,token_factory=lambda:format(next(tokens),'032x'))
trace=[]
def emit(name,fn,args):
    expected=fn(service,**args);trace.append({'name':name,'arguments':copy.deepcopy(args),'expected':copy.deepcopy(expected)});return expected
payload=u._payload();meta=u._metadata(payload);count=(len(payload)+49151)//49152
received=emit('ck3_begin_coat_of_arms_source_upload_v2',u._ck3_begin_coat_of_arms_source_upload_v2,dict(meta,total_bytes=len(payload),chunk_count=count,chunk_encoding='base64'))
commit=dict(meta,upload_id=received['upload_id'],generation=received['generation'],chunk_count=count)
for index,start in enumerate(range(0,len(payload),49152)):
    chunk=payload[start:start+49152]
    emit('ck3_append_coat_of_arms_source_chunk_v2',u._ck3_append_coat_of_arms_source_chunk_v2,dict(commit,chunk_index=index,chunk_encoding='base64',chunk_bytes=len(chunk),chunk_sha256=hashlib.sha256(chunk).hexdigest(),chunk_base64=base64.b64encode(chunk).decode('ascii')))
emit('ck3_commit_coat_of_arms_source_upload_v2',u._ck3_commit_coat_of_arms_source_upload_v2,commit)
small=b'coa={}\\r\\n';args=dict(u._metadata(small),total_bytes=len(small),chunk_count=1,chunk_encoding='base64')
received=emit('ck3_begin_coat_of_arms_source_upload_v2',u._ck3_begin_coat_of_arms_source_upload_v2,args)
emit('ck3_abort_coat_of_arms_source_upload_v2',u._ck3_abort_coat_of_arms_source_upload_v2,dict(upload_id=received['upload_id'],generation=received['generation']))
emit('ck3_probe_coat_of_arms_source_v1',_ck3_probe_coat_of_arms_source_v1,dict(source='coa={}\\n',expected_revision=0,apply=False))
export=_ck3_export_coat_of_arms_source_v1(e.GameplayBridgeService(e._ExportDriver()),expected_revision=0)
trace.append(dict(name='ck3_export_coat_of_arms_source_v1',arguments=dict(expected_revision=0),expected=export))
bindings=[]
for mode in ('gameplay','frontend_snapshot'):
    for date in (-(2**63),2**63-1):
        value=dict(mode=mode,snapshot_id='native:wide',revision=2**64-1,native_revision=2**64-1,date_raw=date,connection_generation=2**64-1,bridge_pid=4242)
        if mode=='gameplay':value['episode_run_id']='original-wide-binding'
        bindings.append(normalize_coat_of_arms_source_v1_binding(value))
print(json.dumps(dict(trace=trace,bindings=bindings),ensure_ascii=True,separators=(',',':')))
""";
    static ObjectNode nativeProbe(EncodedSource source,Binding b,boolean apply){
        String status=apply?"applied":"detected";ObjectNode p=empty().put("schema","xar.ck3.coat-of-arms-designer-probe.v1").put("schema_version",1).put("status",status).put("date_raw",b.dateRaw()).put("source_bytes",source.sourceBytes()).put("designer_observed",true).put("clipboard_written",true).put("clipboard_readback_matched",true).put("detected",true).put("apply_requested",apply).put("paste_invoked",apply).put("applied",apply).put("candidate_index",123).put("preview_coat_of_arms_handle",456).put("active_coat_of_arms_index",apply?123:789).putNull("reason");p.putObject("provenance").put("backend_id","ck3-1.19.0.6-native-coat-of-arms-designer-probe-v1");
        ObjectNode n=empty().put("step",PROBE_STEP).put("accepted",true).put("status",status).put("query_sequence",1).put("snapshot_revision",b.nativeRevision());n.set("coat_of_arms_probe",p);return n;
    }
    static ObjectNode nativeExport(Binding b,String source){
        ObjectNode p=empty().put("schema","xar.ck3.coat-of-arms-designer-export.v1").put("schema_version",1).put("status","exported").put("date_raw",b.dateRaw()).put("source_bytes",source.length()).put("designer_observed",true).put("copy_invoked",true).put("clipboard_read",true).put("source",source).putNull("reason");p.putObject("provenance").put("backend_id","ck3-1.19.0.6-native-coat-of-arms-designer-export-v1");
        ObjectNode n=empty().put("step",EXPORT_STEP).put("accepted",true).put("status","exported").put("query_sequence",1).put("snapshot_revision",b.nativeRevision());n.set("coat_of_arms_export",p);return n;
    }
}
