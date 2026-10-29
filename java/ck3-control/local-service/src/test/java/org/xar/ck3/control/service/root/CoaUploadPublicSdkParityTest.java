package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaCodec;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaUploads;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.coatofarms.extensions.CoaUpload;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaService;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Mandatory original SDK -> actual shared Root binder -> typed directory -> sole service/manager/codec.
 * The native result inputs are controlled software packets. This test constructs no Core, Root or Game. */
final class CoaUploadPublicSdkParityTest {
    @TempDir Path temporary;
    private static final Binding MENU=new FrontendBinding(BigInteger.valueOf(3),4242);
    private static final String EXPORT_SOURCE="coa={\r\n pattern=\"pattern_solid.dds\"\r\n color1=blue\r\n}\r\n";
    private record Original(ObjectNode corpus,ExactRef mcp) { }
    private record Fixture(McpExecutableDirectory.Partial assembled,ControlledNative nativePort,AtomicInteger calls) {
        PublicMcpDirectory directory(){return assembled.softwareDirectory();}
    }
    private static List<ToolDescriptor> descriptors()throws IOException {
        List<ToolDescriptor> original=RootOriginalPublicTestInputs.tools();Set<String> names=new HashSet<>();
        for(ToolDescriptor descriptor:original)assertTrue(names.add(descriptor.name()),"duplicate original SDK tool");
        List<ToolDescriptor> selected=original.stream().filter(d->CoaUpload.METHODS.stream().anyMatch(m->m.publicName().equals(d.name()))).toList();
        assertEquals(6,selected.size(),"mandatory actual SDK capture must contain all six upload/source tools");
        return selected;
    }
    private static List<ToolDescriptor> executable(List<ToolDescriptor> original){
        return original.stream().map(RootPublicCatalogCodec::executableTool).toList();
    }
    @Test void actualOriginalSixToolSdkSchemaDirectoryNativeCodecAndResponseSerdeAgree()throws Exception {
        Original original=original();List<ToolDescriptor> originals=descriptors();
        List<byte[]> before=originals.stream().map(d->d.original().bytes()).toList();
        Fixture fixture=fixture(original,executable(originals));Set<Method> seen=new HashSet<>();int rows=0;
        for(JsonNode row:original.corpus().withArray("trace")){
            Method method=Method.named(row.path("name").textValue());assertTrue(CoaUpload.METHODS.contains(method));seen.add(method);rows++;
            ObjectNode actual=invoke(fixture,method,(ObjectNode)row.get("arguments"));
            assertEquals(public64((ObjectNode)row.get("expected")),actual,method.publicName());
            assertFalse(actual.has("game_effect_verified"));assertFalse(actual.has("rendered_texture_verified"));
        }
        assertEquals(CoaUpload.METHODS,seen);assertEquals(rows,fixture.calls().get());
        assertEquals(3,fixture.nativePort().calls,"one original commit, one probe and one Copy; RAM calls do not dispatch");
        for(int i=0;i<before.size();i++)assertArrayEquals(before.get(i),originals.get(i).original().bytes(),"original SDK bytes are immutable");
    }
    @Test void canonicalUploadResponseCanFeedActualSdkAppendCommitAndAbortWithoutNumericCoercion()throws Exception {
        Original original=original();List<ToolDescriptor> originals=descriptors();List<ToolDescriptor> projected=executable(originals);
        Fixture fixture=fixture(original,projected);byte[] source="coa={}\r\n".getBytes(StandardCharsets.US_ASCII);
        ObjectNode received=invoke(fixture,Method.BEGIN,begin(source));assertTrue(received.get("generation").isTextual());assertTrue(received.get("expected_revision").isTextual());
        ObjectNode append=commit(received).put("chunk_index",0).put("chunk_encoding","base64").put("chunk_bytes",source.length).put("chunk_sha256",sha256(source)).put("chunk_base64",Base64.getEncoder().encodeToString(source));
        ToolDescriptor rawAppend=originals.stream().filter(d->d.name().equals(Method.APPEND.publicName())).findFirst().orElseThrow();
        assertThrows(IllegalArgumentException.class,()->rawAppend.validateArguments(new Arguments(Presence.VALUE,Optional.of(raw(append)))),"raw original integer schema is retained as evidence, not silently changed");
        assertEquals("ready",invoke(fixture,Method.APPEND,append).path("status").textValue());
        ObjectNode committed=invoke(fixture,Method.COMMIT,commit(received));assertEquals("committed",committed.path("status").textValue());
        assertEquals(sha256(source),committed.path("result").path("source_sha256").textValue());assertEquals(1,fixture.nativePort().calls);
        ObjectNode next=invoke(fixture,Method.BEGIN,begin(source));ObjectNode abort=empty();abort.set("upload_id",next.get("upload_id"));abort.set("generation",next.get("generation"));
        assertTrue(abort.get("generation").isTextual());assertEquals("aborted",invoke(fixture,Method.ABORT,abort).path("status").textValue());assertEquals(1,fixture.nativePort().calls);
    }
    @Test void actualSdkRejectsMissingNullExtraAndMalformedU64BeforeAnyServiceDispatch()throws Exception {
        Original original=original();List<ToolDescriptor> projected=executable(descriptors());Fixture fixture=fixture(original,projected);
        for(Method method:CoaUpload.METHODS){
            ObjectNode valid=null;for(JsonNode row:original.corpus().withArray("trace"))if(method.publicName().equals(row.path("name").textValue())){valid=(ObjectNode)row.get("arguments");break;}
            assertNotNull(valid);ToolDescriptor descriptor=projected.stream().filter(d->d.name().equals(method.publicName())).findFirst().orElseThrow();
            ObjectNode extra=valid.deepCopy().put("unexpected_path","C:/not-an-upload-input");
            assertRejected(fixture,method,extra);
            JsonNode schema=object(descriptor.original()).get("inputSchema");String required=schema.path("required").get(0).textValue();
            ObjectNode missing=valid.deepCopy();missing.remove(required);assertRejected(fixture,method,missing);
            ObjectNode nullField=valid.deepCopy();nullField.putNull(required);assertRejected(fixture,method,nullField);
            String field=method==Method.ABORT?"generation":"expected_revision";
            for(String token:List.of("true","1.0","null","-1","9007199254740992","\"01\"","\"18446744073709551616\"")){
                ObjectNode bad=valid.deepCopy();bad.set(field,FullJsonTree.parse(token.getBytes(StandardCharsets.UTF_8),1024));assertRejected(fixture,method,bad);
            }
            ObjectNode wide=valid.deepCopy().put(field,"18446744073709551615");
            descriptor.validateArguments(new Arguments(Presence.VALUE,Optional.of(raw(wide))));
            assertEquals(method,decode(method,raw(wide)).method());
            if(method==Method.ABORT)assertRejected(fixture,method,valid.deepCopy().put(field,"0"));
            int before=fixture.calls().get();
            assertThrows(ToolFailure.class,()->fixture.directory().invoke(new ToolCall(method.publicName(),new Arguments(Presence.MISSING,Optional.empty()),Optional.empty(),new McpCancellation())));
            assertEquals(before,fixture.calls().get());
        }
        assertEquals(0,fixture.calls().get());assertEquals(0,fixture.nativePort().calls);
    }
    private static void assertRejected(Fixture fixture,Method method,ObjectNode arguments){
        int before=fixture.calls().get();
        assertThrows(ToolFailure.class,()->fixture.directory().invoke(new ToolCall(method.publicName(),new Arguments(Presence.VALUE,Optional.of(raw(arguments))),Optional.empty(),new McpCancellation())));
        assertEquals(before,fixture.calls().get(),"schema/typed decode failure must precede the actual service");
    }
    private static final class ControlledNative implements CoaUpload.Runtime {
        int calls;
        @Override public Binding current(BigInteger revision,String capability){
            assertEquals(MENU.revision(),revision);
            assertTrue(Set.of(CoaUpload.capability(PROBE_STEP),CoaUpload.capability(EXPORT_STEP)).contains(capability));
            return MENU;
        }
        @Override public ProbeResult probe(EncodedSource source,Binding binding,boolean large,boolean apply){
            calls++;assertEquals(MENU,binding);assertTrue(!large||source.sourceBytes()<=V2_MAX_BYTES);
            return CoaCodec.nativeProbe(raw(nativeProbe(source,binding,apply)),source,binding,apply);
        }
        @Override public ExportResult export(Binding binding){
            calls++;assertEquals(MENU,binding);return CoaCodec.nativeExport(raw(nativeExport(binding,EXPORT_SOURCE)),binding);
        }
    }
    private static Fixture fixture(Original original,List<ToolDescriptor> descriptors)throws IOException {
        assertEquals(6,descriptors.size());AtomicLong tokens=new AtomicLong();ControlledNative actual=new ControlledNative();
        CoaUpload upload=new CoaUpload(new CoaUploads(()->0L,()->String.format("%032x",tokens.incrementAndGet())),actual);
        FrontendCoaService service=new FrontendCoaService(List.of(new FrontendCoaService.ComponentBinding(CoaUpload.METHODS,upload)));
        ExactRef implementation=implementation();AtomicInteger calls=new AtomicInteger();
        var bindings=RootFrontendCoaPublicProducts.componentMethods(CoaUpload.METHODS,request->{
            calls.incrementAndGet();try{return service.execute(request);}catch(IOException error){throw new UncheckedIOException(error);}
        },implementation);
        assertEquals(CoaUpload.METHODS.stream().map(Method::publicName).collect(java.util.stream.Collectors.toSet()),bindings.stream().map(McpExecutableDirectory.DirectBinding::name).collect(java.util.stream.Collectors.toSet()));
        var declarations=descriptors.stream().map(descriptor->{
            JsonNode found=null;
            for(JsonNode row:original.corpus().withArray("declarations"))if(descriptor.name().equals(row.path("name").textValue())){assertNull(found,"ambiguous original declaration");found=row;}
            assertNotNull(found,"actual original AST declaration required");
            return new McpCoverage.Declaration(descriptor.name(),original.mcp(),found.path("line").intValue(),found.path("end_line").intValue(),"actual original MCP source declaration",List.of());
        }).toList();
        var decisions=descriptors.stream().map(d->new McpCoverage.Decision(d.name(),McpCoverage.Admission.ADMITTED,implementation,"controlled real CoA service/codec component; software scope only")).toList();
        PublicBindings empty=new PublicBindings();empty.freeze(Set.of());
        var assembled=assertInstanceOf(McpExecutableDirectory.Partial.class,McpExecutableDirectory.assemble(new McpCoverage.Catalog(declarations),decisions,descriptors,List.of(),empty,bindings));
        assertEquals(Scope.SOFTWARE_ONLY,assembled.softwareDirectory().scope());
        assertTrue(assembled.missing().stream().allMatch(m->m.reason()==McpExecutableDirectory.MissingReason.NO_ACTUAL_RESOURCE_PROVIDER));
        return new Fixture(assembled,actual,calls);
    }
    /** Maven's actual selected module source, never an invented byte/hash source identity. */
    private static ExactRef implementation()throws IOException {
        Path module=Path.of(System.getProperty("basedir",".")).toAbsolutePath().normalize();
        if(!Files.isDirectory(module.resolve("src/main/java")))module=module.resolve("local-service");
        Path source=module.resolve("src/main/java/org/xar/ck3/control/service/root/RootFrontendCoaPublicProducts.java").toRealPath();
        byte[] bytes=Files.readAllBytes(source);return new ExactRef(source.toString(),bytes.length,ActionCodec.sha256(bytes));
    }
    private static ObjectNode invoke(Fixture fixture,Method method,ObjectNode arguments)throws Exception {
        ToolCall call=new ToolCall(method.publicName(),new Arguments(Presence.VALUE,Optional.of(raw(arguments))),Optional.empty(),new McpCancellation());
        CallResult original=fixture.directory().invoke(call);
        assertArrayEquals(original.bytes(),CallResult.fromRaw(new RawJson(original.bytes())).bytes());
        ObjectNode response=object(new RawJson(original.bytes()));assertFalse(response.path("isError").asBoolean(false));
        JsonNode result=response.get("structuredContent");assertNotNull(result);assertTrue(result.isObject());
        JsonNode content=response.path("content");assertEquals(1,content.size());assertEquals("text",content.get(0).path("type").textValue());
        assertEquals(result,FullJsonTree.parse(content.get(0).path("text").textValue().getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES));
        ObjectNode business=(ObjectNode)result;
        assertEquals(business,object(encode(new Response(raw(business)))));
        return business;
    }
    private static ObjectNode public64(ObjectNode original){
        ObjectNode out=original.deepCopy();
        if(out.path("schema").asText().equals("coat-of-arms-source-upload-commit-v2")){
            out.set("upload",public64((ObjectNode)out.get("upload")));out.set("result",public64((ObjectNode)out.get("result")));return out;
        }
        for(String field:List.of("generation","expected_revision"))if(out.has(field)){assertTrue(out.get(field).isIntegralNumber());out.put(field,out.get(field).bigIntegerValue().toString());}
        if(out.get("binding") instanceof ObjectNode binding)for(String field:List.of("revision","native_revision","connection_generation","date_raw"))if(binding.has(field)){assertTrue(binding.get(field).isIntegralNumber());binding.put(field,binding.get(field).bigIntegerValue().toString());}
        return out;
    }
    private static ObjectNode commit(ObjectNode receipt){
        ObjectNode out=empty();for(String field:List.of("upload_id","generation","chunk_count","source_sha256","expected_revision","apply","expected_game_version","expected_executable_sha256"))out.set(field,receipt.get(field));return out;
    }
    private static ObjectNode begin(byte[] source){
        return empty().put("total_bytes",source.length).put("source_sha256",sha256(source)).put("chunk_count",1).put("chunk_encoding","base64").put("expected_revision","0").put("apply",false).put("expected_game_version",GAME_VERSION).put("expected_executable_sha256",EXE_SHA256);
    }
    private Original original()throws Exception {
        Path root=Path.of(required("xar.repository.root")).toRealPath();Path python=Path.of(required("xar.python")).toRealPath();
        Path out=temporary.resolve("original-"+System.nanoTime()+".json"),error=temporary.resolve("original-"+System.nanoTime()+".stderr");
        ProcessBuilder builder=new ProcessBuilder(python.toString(),"-X","utf8","-c",ORACLE);builder.directory(root.toFile());
        builder.environment().put("XAR_SOURCE_REPOSITORY",root.toString());builder.environment().put("PYTHONPATH",root.resolve("ck3_autonomous_player/src").toString());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        builder.redirectOutput(out.toFile());builder.redirectError(error.toFile());Process child=builder.start();
        try{assertTrue(child.waitFor(45,TimeUnit.SECONDS),"mandatory original CoA producer timed out");assertEquals(0,child.exitValue(),Files.readString(error,StandardCharsets.UTF_8));}
        finally{if(child.isAlive())child.destroyForcibly();}
        assertTrue(Files.size(out)<=RawJson.MAXIMUM_BYTES,"complete bounded original corpus required");ObjectNode corpus=object(new RawJson(Files.readAllBytes(out)));
        Path mcp=root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py");byte[] bytes=Files.readAllBytes(mcp);
        assertEquals("b7569231226484b0bdd98c40ace14a82672b2138a0aab77711e559a4d9b8ccbc",ActionCodec.sha256(bytes));
        return new Original(corpus,new ExactRef(mcp.toString(),bytes.length,ActionCodec.sha256(bytes)));
    }
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN_REQUIRED_COA_SDK_INPUT: missing -D"+key);return value;}
    private static ObjectNode nativeProbe(EncodedSource source,Binding binding,boolean apply){
        String status=apply?"applied":"detected";
        ObjectNode body=empty().put("schema","xar.ck3.coat-of-arms-designer-probe.v1").put("schema_version",1).put("status",status).put("date_raw",binding.dateRaw()).put("source_bytes",source.sourceBytes()).put("designer_observed",true).put("clipboard_written",true).put("clipboard_readback_matched",true).put("detected",true).put("apply_requested",apply).put("paste_invoked",apply).put("applied",apply).put("candidate_index",123).put("preview_coat_of_arms_handle",456).put("active_coat_of_arms_index",apply?123:789).putNull("reason");
        body.putObject("provenance").put("backend_id","ck3-1.19.0.6-native-coat-of-arms-designer-probe-v1");
        ObjectNode result=empty().put("step",PROBE_STEP).put("accepted",true).put("status",status).put("query_sequence",1).put("snapshot_revision",binding.nativeRevision());result.set("coat_of_arms_probe",body);return result;
    }
    private static ObjectNode nativeExport(Binding binding,String source){
        ObjectNode body=empty().put("schema","xar.ck3.coat-of-arms-designer-export.v1").put("schema_version",1).put("status","exported").put("date_raw",binding.dateRaw()).put("source_bytes",source.length()).put("designer_observed",true).put("copy_invoked",true).put("clipboard_read",true).put("source",source).putNull("reason");
        body.putObject("provenance").put("backend_id","ck3-1.19.0.6-native-coat-of-arms-designer-export-v1");
        ObjectNode result=empty().put("step",EXPORT_STEP).put("accepted",true).put("status","exported").put("query_sequence",1).put("snapshot_revision",binding.nativeRevision());result.set("coat_of_arms_export",body);return result;
    }
    private static final String ORACLE="""
        import ast,base64,copy,hashlib,importlib.util,itertools,json,os,pathlib,sys
        repo=pathlib.Path(os.environ['XAR_SOURCE_REPOSITORY']).resolve(strict=True)
        sys.path.insert(0,str(repo/'ck3_autonomous_player/src'))
        expected={
          'ck3_autonomous_player/tests/unit/test_coat_of_arms_source_upload_v2_bridge.py':'c1c697c7450a1e32b0503e9ee725db474787bd4c3148ba0bf5735a7808b4e8ce',
          'ck3_autonomous_player/tests/unit/test_coat_of_arms_source_export_v1_bridge.py':'9921fc7bd731843add7bca563320f0fb1f801c39abab3c5434485d9e37783d46',
          'ck3_autonomous_player/src/xar_autoplayer/bridge/coat_of_arms_source_upload_v2.py':'9644507d9ee5fa942d94a53cef906f243044a79d3dcc4769e4d762c8ce28b5db',
          'ck3_autonomous_player/src/xar_autoplayer/bridge/coat_of_arms_source_probe_contract.py':'7569dfe659be07fbdbd3ea1246e9c5126cd9f138d4976a02816373d7c796421a',
          'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py':'b7569231226484b0bdd98c40ace14a82672b2138a0aab77711e559a4d9b8ccbc'}
        for name,sha in expected.items():
            if hashlib.sha256((repo/name).read_bytes()).hexdigest()!=sha:raise RuntimeError('original CoA source drift: '+name)
        def load(name,filename):
            spec=importlib.util.spec_from_file_location(name,repo/'ck3_autonomous_player/tests/unit'/filename)
            module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
        u=load('sdk_original_coa_upload','test_coat_of_arms_source_upload_v2_bridge.py')
        e=load('sdk_original_coa_export','test_coat_of_arms_source_export_v1_bridge.py')
        from xar_autoplayer.bridge.coat_of_arms_source_upload_v2 import CoatOfArmsSourceUploadManagerV2
        from xar_autoplayer.bridge.mcp_server import _ck3_probe_coat_of_arms_source_v1,_ck3_export_coat_of_arms_source_v1
        driver=u._Driver();driver.probe_coat_of_arms_source_v1=driver.probe_coat_of_arms_source_transport_v2
        service=u.GameplayBridgeService(driver);tokens=itertools.count(1)
        service._coat_of_arms_source_uploads_v2=CoatOfArmsSourceUploadManagerV2(clock=lambda:0,token_factory=lambda:format(next(tokens),'032x'))
        trace=[]
        def emit(name,fn,args):
            value=fn(service,**args);trace.append(dict(name=name,arguments=copy.deepcopy(args),expected=copy.deepcopy(value)));return value
        payload=u._payload();meta=u._metadata(payload);count=(len(payload)+49151)//49152
        first=emit('ck3_begin_coat_of_arms_source_upload_v2',u._ck3_begin_coat_of_arms_source_upload_v2,dict(meta,total_bytes=len(payload),chunk_count=count,chunk_encoding='base64'))
        commit=dict(meta,upload_id=first['upload_id'],generation=first['generation'],chunk_count=count)
        for index,start in enumerate(range(0,len(payload),49152)):
            chunk=payload[start:start+49152]
            emit('ck3_append_coat_of_arms_source_chunk_v2',u._ck3_append_coat_of_arms_source_chunk_v2,dict(commit,chunk_index=index,chunk_encoding='base64',chunk_bytes=len(chunk),chunk_sha256=hashlib.sha256(chunk).hexdigest(),chunk_base64=base64.b64encode(chunk).decode('ascii')))
        emit('ck3_commit_coat_of_arms_source_upload_v2',u._ck3_commit_coat_of_arms_source_upload_v2,commit)
        small=b'coa={}\\r\\n'
        received=emit('ck3_begin_coat_of_arms_source_upload_v2',u._ck3_begin_coat_of_arms_source_upload_v2,dict(u._metadata(small),total_bytes=len(small),chunk_count=1,chunk_encoding='base64'))
        emit('ck3_abort_coat_of_arms_source_upload_v2',u._ck3_abort_coat_of_arms_source_upload_v2,dict(upload_id=received['upload_id'],generation=received['generation']))
        emit('ck3_probe_coat_of_arms_source_v1',_ck3_probe_coat_of_arms_source_v1,dict(source='coa={}\\n',expected_revision=0,apply=False))
        result=_ck3_export_coat_of_arms_source_v1(e.GameplayBridgeService(e._ExportDriver()),expected_revision=0)
        trace.append(dict(name='ck3_export_coat_of_arms_source_v1',arguments=dict(expected_revision=0),expected=result))
        mcp=repo/'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py'
        declarations=[dict(name=n.name,line=n.lineno,end_line=n.end_lineno) for n in ast.walk(ast.parse(mcp.read_text(encoding='utf-8-sig'))) if isinstance(n,ast.FunctionDef) and n.name.startswith('ck3_')]
        print(json.dumps(dict(trace=trace,declarations=declarations),separators=(',',':')))
        """;
}
