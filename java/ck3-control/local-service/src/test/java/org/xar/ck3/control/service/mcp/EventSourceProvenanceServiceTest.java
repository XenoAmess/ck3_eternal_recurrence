package org.xar.ck3.control.service.mcp;

import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.wave2.events.registered.*;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.junit.jupiter.api.Assertions.*;

/** Original frozen index -> strict shared DTO -> actual public handler/binding -> MCP serialization. */
final class EventSourceProvenanceServiceTest {
    @Test void everyFrozenBuildHasTheOriginalDatasetAndPublicActualHandlerPreservesLexicalBoundary()throws Exception {
        var knowledge=RegisteredEventKnowledge.load();var service=new EventSourceProvenanceService(knowledge);
        Map<String,Integer> counts=Map.of("1.19.0.6",195,"1.20.0.2",193,"1.20.0.3",193,"1.20.0.4",196);
        for(String build:counts.keySet()) {
            var index=knowledge.sourceIndex(build);assertEquals(counts.get(build).intValue(),index.events().size());
            assertSame(index,knowledge.sourceIndex(build));assertEquals(knowledge.sourceDatasetSha256(build),index.datasetSha256());
            var binding=service.actualMethod(new ExactRef("synthetic-source-provenance-handler",1,"a".repeat(64)));
            assertEquals(PublicMcpBindings.Kind.STATIC_KNOWLEDGE,binding.kind());
            for(var entry:index.events().values()) {
                RawJson args=raw(new ObjectValue(Map.of("key",new StringValue(entry.key().value()),"build",new StringValue(build))));
                var call=new PublicMcpDirectory.ToolCall(EventSourceProvenanceService.TOOL,
                        new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(args)),Optional.empty(),new McpCancellation());
                var request=binding.decoder().decode(call);var response=binding.actual().invoke(request);var encoded=binding.encoder().encode(response);
                ObjectValue envelope=RetainedJson.object(RetainedJson.parse(encoded.bytes()));
                ObjectValue returned=RetainedJson.object(envelope.get("structuredContent"));
                assertEquals(response.json(),returned);assertEquals(entry.definition().json(),returned.get("definition"));
                assertEquals(new BooleanValue(true),returned.get("caller_candidates_are_lexical_only"));
                assertEquals(new StringValue("not_manually_reviewed_as_call_edges"),returned.get("caller_candidates_review_status"));
                assertFalse(returned.contains("runtime_call_edge_verified"));
                assertEquals(build.equals("1.20.0.4"),returned.contains("source_reuse_1_20_0_4"));
            }
        }
    }
    @Test void publicArgumentsDistinguishMissingNullWrongTypeAndUseOriginalCurrentBuildDefault()throws Exception {
        var service=new EventSourceProvenanceService(RegisteredEventKnowledge.load());
        var query=EventSourceProvenanceService.decode(raw("{\"key\":\"faith_creation.1021\"}"));
        assertEquals(new EventSourceProvenance.Text("1.20.0.4"),query.build());assertTrue(service.query(query).available());
        for(String bad:List.of("{}","{\"key\":null}","{\"key\":true}","{\"key\":1.0}",
                "{\"key\":\"x.1\",\"build\":null}","{\"key\":\"x.1\",\"build\":true}","{\"key\":\"x.1\",\"extra\":1}"))
            assertThrows(IllegalArgumentException.class,()->EventSourceProvenanceService.decode(raw(bad)));
        var missing=service.query(new EventSourceProvenance.Query("unknown.999","1.20.0.4"));
        assertEquals(EventSourceProvenance.Reason.NOT_INDEXED,missing.reason().orElseThrow());assertTrue(missing.datasetSha256().isPresent());
        assertEquals(RetainedJson.NULL,missing.json().get("definition"));assertEquals(new ArrayValue(List.of()),missing.json().get("caller_candidates"));
        var invalid=service.query(new EventSourceProvenance.Query("x.1","unsupported"));assertTrue(invalid.datasetSha256().isEmpty());
        assertEquals(EventSourceProvenance.InvalidParameter.BUILD,invalid.invalidParameter().orElseThrow());
        var unavailable=EventSourceProvenance.query(new EventSourceProvenance.Query("x.1","1.20.0.4"),build->{throw new java.io.IOException("original unavailable");});
        assertEquals(EventSourceProvenance.Reason.INTEGRITY,unavailable.reason().orElseThrow());
        var mismatched=EventSourceProvenance.query(new EventSourceProvenance.Query("x.1","1.20.0.4"),build->RegisteredEventKnowledge.load().sourceIndex("1.19.0.6"));
        assertEquals(EventSourceProvenance.Reason.INTEGRITY,mismatched.reason().orElseThrow());
    }
    @Test void strictSourceValidationRejectsWrongTypesOrderPathsAuditAndDatasetDriftBeforeExposingRows()throws Exception {
        ObjectValue root=originalIndex("1.19.0.6");
        for(Value wrong:List.of(new BooleanValue(true),new FloatingValue(1.0),new StringValue("1"))) {
            ObjectValue malformed=root.with("schema_version",wrong);malformed=rehash(malformed);ObjectValue finalRow=malformed;
            assertThrows(IllegalArgumentException.class,()->EventSourceIndex.decode(finalRow));
        }
        assertThrows(IllegalArgumentException.class,()->EventSourceIndex.decode(root.with("dataset_sha256",new StringValue("A".repeat(64)))));
        var events=RetainedJson.object(root.get("events"));String first=events.fields().keySet().iterator().next();
        ObjectValue row=RetainedJson.object(events.get(first)),definition=RetainedJson.object(row.get("definition"));
        ObjectValue wrongNamespace=rehash(root.with("events",events.with(first,row.with("namespace",new StringValue("another_namespace")))));
        assertThrows(IllegalArgumentException.class,()->EventSourceIndex.decode(wrongNamespace));
        ObjectValue wrongField=rehash(root.with("events",events.with(first,row.with("proven_runtime_caller",new BooleanValue(true)))));
        assertThrows(IllegalArgumentException.class,()->EventSourceIndex.decode(wrongField));
        for(String escape:List.of("../events/a.txt","events/../a.txt","C:/events/a.txt","events\\a.txt")) {
            ObjectValue malformed=rehash(root.with("events",events.with(first,row.with("definition",definition.with("relative_path",new StringValue(escape))))));
            assertThrows(IllegalArgumentException.class,()->EventSourceIndex.decode(malformed));
        }
        ObjectValue malformed=rehash(root.with("events",events.with(first,row.with("definition",definition.with("line",new BooleanValue(true))))));
        assertThrows(IllegalArgumentException.class,()->EventSourceIndex.decode(malformed));
        ObjectValue audit=RetainedJson.object(root.get("audit"));ObjectValue wrongAudit=rehash(root.with("audit",audit.with("missing_definition_count",new IntegerValue(BigInteger.ONE))));
        assertThrows(IllegalArgumentException.class,()->EventSourceIndex.decode(wrongAudit));
        var reversed=new ArrayList<>(events.fields().keySet());java.util.Collections.reverse(reversed);Map<String,Value> unordered=new LinkedHashMap<>();
        reversed.forEach(key->unordered.put(key,events.get(key)));ObjectValue wrongOrder=rehash(root.with("events",new ObjectValue(unordered)));
        assertThrows(IllegalArgumentException.class,()->EventSourceIndex.decode(wrongOrder));
    }
    @Test void actualOriginalPythonProducerMatchesEveryIndexedRowAndUnavailableBranch()throws Exception {
        String python=System.getProperty("xar.python");String repositoryProperty=System.getProperty("xar.repository.root");
        assertNotNull(python,"required xar.python property absent; original Python producer differential must not silently skip");
        assertFalse(python.isBlank(),"required xar.python property is blank");
        assertNotNull(repositoryProperty,"required xar.repository.root property absent; original Python producer differential must not silently skip");
        assertFalse(repositoryProperty.isBlank(),"required xar.repository.root property is blank");
        String repository=Path.of(repositoryProperty).toRealPath().toString();
        var knowledge=RegisteredEventKnowledge.load();var service=new EventSourceProvenanceService(knowledge);List<Value> cases=new ArrayList<>(),expected=new ArrayList<>();
        for(String build:RegisteredEventKnowledge.EXE.keySet()) {
            for(var entry:knowledge.sourceIndex(build).events().values())add(cases,expected,service,entry.key().value(),build);
            add(cases,expected,service,"not.indexed.999",build);add(cases,expected,service,"\u00a0\t",build);
        }
        add(cases,expected,service,"x.1","unsupported");
        String script="import json,sys; from xar_autoplayer.vanilla_events.source_index import query_vanilla_event_source_provenance_v1 as query; cases=json.load(sys.stdin); json.dump([query(row['key'],row['build']) for row in cases],sys.stdout,ensure_ascii=False,separators=(',',':'),allow_nan=False)";
        ProcessBuilder builder=new ProcessBuilder(python,"-c",script).directory(Path.of(repository).toFile()).redirectErrorStream(true);
        builder.environment().put("XAR_SOURCE_REPOSITORY",repository);builder.environment().put("PYTHONPATH",Path.of(repository,"ck3_autonomous_player","src").toString());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        Process process=builder.start();var result=new java.util.concurrent.CompletableFuture<byte[]>();
        Thread reader=Thread.ofVirtual().start(()->{try { result.complete(process.getInputStream().readNBytes(8*1024*1024+1)); }catch(java.io.IOException failure){result.completeExceptionally(failure);}});
        try {
            process.getOutputStream().write(RetainedJson.encode(new ArrayValue(cases)));process.getOutputStream().close();
            assertTrue(process.waitFor(30,TimeUnit.SECONDS),"original Python producer timed out");byte[] bytes=result.get(5,TimeUnit.SECONDS);
            assertEquals(0,process.exitValue(),new String(bytes,StandardCharsets.UTF_8));assertTrue(bytes.length<=8*1024*1024,"bounded original differential output required");
            assertEquals(new ArrayValue(expected),RetainedJson.parse(bytes,new RetainedJson.ParseBudget(8*1024*1024,1_000_000,96)));
        }finally { if(process.isAlive())process.destroyForcibly();reader.join(5000); }
    }
    private static void add(List<Value> cases,List<Value> expected,EventSourceProvenanceService service,String key,String build) {
        cases.add(new ObjectValue(Map.of("key",new StringValue(key),"build",new StringValue(build))));expected.add(service.query(new EventSourceProvenance.Query(key,build)).json());
    }
    private static ObjectValue originalIndex(String build)throws Exception {
        try(InputStream input=RegisteredEventKnowledge.class.getResourceAsStream(RegisteredEventKnowledge.RESOURCE)) {
            assertNotNull(input);try(var gzip=new GZIPInputStream(input)) {
                ObjectValue root=RetainedJson.object(RetainedJson.parse(gzip.readNBytes(2_239_613),new RetainedJson.ParseBudget(2_239_612,500_000,96)));
                return RetainedJson.object(RetainedJson.object(root.get(build)).get("source_index"));
            }
        }
    }
    private static ObjectValue rehash(ObjectValue value) { return value.with("dataset_sha256",new StringValue(EventSourceIndex.datasetSha256(value))); }
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static RawJson raw(Value value) { return new RawJson(RetainedJson.encode(value)); }
}
