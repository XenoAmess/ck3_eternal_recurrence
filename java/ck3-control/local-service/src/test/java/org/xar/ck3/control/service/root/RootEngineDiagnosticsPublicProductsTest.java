package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.EngineDiagnostics.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.EnumMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.mcp.McpCancellation;
import org.xar.ck3.control.service.mcp.McpCoverage;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpBindings;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog;

/** Binding/codec DATA tests. No configured-plan Prepared, private Core, or filesystem admission is manufactured. */
class RootEngineDiagnosticsPublicProductsTest {
    @TempDir Path temp;
    @Test void diagnosticsQueryDefaultsAndStrictNamedNumbersRejectAllOtherDomains() {
        assertEquals(new Query(50,25),RootEngineDiagnosticsPublicProducts.decodeDiagnostics(new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.MISSING,Optional.empty())));
        assertEquals(new Query(50,25),RootEngineDiagnosticsPublicProducts.decodeDiagnostics(arguments("{}")));
        assertEquals(new Query(100,1),RootEngineDiagnosticsPublicProducts.decodeDiagnostics(arguments("{\"fingerprint_limit\":100,\"tail_limit\":1}")));
        assertThrows(IllegalArgumentException.class,()->RootEngineDiagnosticsPublicProducts.decodeDiagnostics(nullArguments()));
        for(String json:List.of("{\"fingerprint_limit\":true}","{\"fingerprint_limit\":1.0}","{\"fingerprint_limit\":\"1\"}",
                "{\"fingerprint_limit\":null}","{\"fingerprint_limit\":0}","{\"fingerprint_limit\":101}","{\"tail_limit\":false}",
                "{\"tail_limit\":0}","{\"tail_limit\":101}","{\"path\":\"error.log\"}","{\"regex\":\".*\"}","{\"extra\":0}"))
            assertThrows(IllegalArgumentException.class,()->RootEngineDiagnosticsPublicProducts.decodeDiagnostics(arguments(json)),json);
    }

    @Test void literalQueryRetainsRequiredMissingNullEmptyAndCodepointBoundaries() {
        String base="{\"log_name\":\"error.log\",\"literals\":[\"hello\"]";
        assertEquals(new LiteralQuery(LogName.ERROR,List.of("hello"),3),RootEngineDiagnosticsPublicProducts.decodeLiterals(arguments(base+"}")));
        assertEquals(0,RootEngineDiagnosticsPublicProducts.decodeLiterals(arguments(base+",\"sample_limit\":0}")).sampleLimit());
        assertThrows(IllegalArgumentException.class,()->RootEngineDiagnosticsPublicProducts.decodeLiterals(new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.MISSING,Optional.empty())));
        assertThrows(IllegalArgumentException.class,()->RootEngineDiagnosticsPublicProducts.decodeLiterals(nullArguments()));
        for(String json:List.of("{}","{\"log_name\":null,\"literals\":[\"a\"]}","{\"log_name\":\"../error.log\",\"literals\":[\"a\"]}",
                "{\"log_name\":\"error.log\"}","{\"log_name\":\"error.log\",\"literals\":null}","{\"log_name\":\"error.log\",\"literals\":\"a\"}",
                "{\"log_name\":\"error.log\",\"literals\":[]}","{\"log_name\":\"error.log\",\"literals\":[true]}",
                "{\"log_name\":\"error.log\",\"literals\":[\"a\",\"a\"]}","{\"log_name\":\"error.log\",\"literals\":[\"\"]}",
                "{\"log_name\":\"error.log\",\"literals\":[\"a\\n\"]}","{\"log_name\":\"error.log\",\"literals\":[\"a\\u0000\"]}",
                base+",\"sample_limit\":true}",base+",\"sample_limit\":1.0}",base+",\"sample_limit\":-1}",base+",\"sample_limit\":6}",base+",\"regex\":true}"))
            assertThrows(IllegalArgumentException.class,()->RootEngineDiagnosticsPublicProducts.decodeLiterals(arguments(json)),json);
        String supplementary="\uD83D\uDE00".repeat(160);
        assertEquals(supplementary,RootEngineDiagnosticsPublicProducts.decodeLiterals(arguments("{\"log_name\":\"debug.log\",\"literals\":[\""+supplementary+"\"]}")).literals().getFirst());
        assertThrows(IllegalArgumentException.class,()->new LiteralQuery(LogName.ERROR,List.of(supplementary+"x"),3));
        assertThrows(IllegalArgumentException.class,()->new LiteralQuery(LogName.ERROR,java.util.stream.IntStream.range(0,17).mapToObj(Integer::toString).toList(),3));
    }

    @Test void realAccumulatorFlowsThroughBothActualBindingsAndCompleteMcpEnvelope()throws Exception {
        byte[] original="[a][E] STRASSE 4\nStraße Straße\nSTRASSE 5\n".getBytes(StandardCharsets.UTF_8);
        AtomicInteger diagnosticsCalls=new AtomicInteger(),literalCalls=new AtomicInteger();ExactRef source=metadataSource();
        var diagnostics=RootEngineDiagnosticsPublicProducts.diagnosticsBinding(source,query->{
            diagnosticsCalls.incrementAndGet();var logs=new EnumMap<LogName,LogRecord>(LogName.class);
            for(var name:LogName.values())logs.put(name,MissingLog.INSTANCE);
            try{logs.put(LogName.ERROR,EngineDiagnosticsReader.summarize(LogName.ERROR,original,query,VanillaEventCatalog.load().textRules()));}
            catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
            return EngineDiagnostics.encode(new Diagnostics(temp.toAbsolutePath(),logs,new Crashes(false,List.of())));
        });
        var diag=invoke(diagnostics,"{\"fingerprint_limit\":1,\"tail_limit\":1}");
        assertEquals(SCHEMA,diag.path("schema").textValue());assertEquals(5,diag.path("fixed_log_names").size());
        assertEquals(1,diag.path("logs").path("debug.log").size());assertFalse(diag.path("logs").path("debug.log").path("exists").booleanValue());
        assertEquals(3,diag.path("logs").path("error.log").path("line_count").longValue());
        assertEquals("STRASSE 5",diag.path("logs").path("error.log").path("tail").get(0).textValue());
        assertFalse(diag.path("path_argument_accepted").booleanValue());assertTrue(diag.path("read_only").booleanValue());
        var literals=RootEngineDiagnosticsPublicProducts.literalsBinding(source,query->{
            literalCalls.incrementAndGet();try{return EngineDiagnostics.encode(EngineDiagnosticsReader.summarize(original,query));}
            catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
        });
        var result=invoke(literals,"{\"log_name\":\"error.log\",\"literals\":[\"Straße\",\"STRASSE\"],\"sample_limit\":1}");
        assertEquals(LITERALS_SCHEMA,result.path("schema").textValue());assertEquals(1,result.path("matches").get(0).path("line_count").longValue());
        assertEquals(2,result.path("matches").get(0).path("samples").get(0).path("line_number").longValue());
        assertEquals(2,result.path("matches").get(1).path("line_count").longValue());assertTrue(result.path("case_sensitive").booleanValue());
        var missing=StrictJson.parse(EngineDiagnostics.encode(new Literals(LogName.ERROR,false,0,null,0,List.of())).bytes(),65536);
        assertEquals(4,missing.size());assertFalse(missing.has("bytes"));assertFalse(missing.has("sha256"));assertFalse(missing.has("scanned_line_count"));
        assertEquals(1,diagnosticsCalls.get());assertEquals(1,literalCalls.get());
    }
    @Test void originalSdkDefaultArgumentsReachActualDiagnosticsBindingAndCompleteEnvelope() throws Exception {
        var name=RootEngineDiagnosticsPublicProducts.DIAGNOSTICS;
        var descriptor=RootOriginalPublicTestInputs.tools().stream().filter(tool->tool.name().equals(name)).findFirst().orElseThrow();
        byte[] original="[time][E] default diagnostics 7\n".getBytes(StandardCharsets.UTF_8);
        AtomicInteger calls=new AtomicInteger();
        var binding=RootEngineDiagnosticsPublicProducts.diagnosticsBinding(metadataSource(),query->{
            assertEquals(new Query(50,25),query);calls.incrementAndGet();
            var logs=new EnumMap<LogName,LogRecord>(LogName.class);
            for(var log:LogName.values())logs.put(log,MissingLog.INSTANCE);
            try { logs.put(LogName.ERROR,EngineDiagnosticsReader.summarize(LogName.ERROR,original,query,VanillaEventCatalog.load().textRules())); }
            catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
            return EngineDiagnostics.encode(new Diagnostics(temp.toAbsolutePath(),logs,new Crashes(false,List.of())));
        });
        var declaration=new McpCoverage.Declaration(name,binding.target().implementationSource(),1,1,
                "software-only actual diagnostics binding DATA; no Root/source admission",List.of());
        var bindings=new PublicMcpBindings(new McpCoverage.Catalog(List.of(declaration)),List.of(new McpCoverage.Decision(
                name,McpCoverage.Admission.ADMITTED,declaration.source(),"original SDK absent/null default arguments through actual diagnostic binding")));
        bindings.registerDirect(descriptor,binding.kind(),binding.requestType(),binding.resultType(),binding.actual(),binding.decoder(),binding.encoder(),binding.target());
        var directory=bindings.freezeSoftwareScope();
        for(var input:List.of(new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.MISSING,Optional.empty()),nullArguments(),arguments("{}"))) {
            var call=new PublicMcpDirectory.ToolCall(name,input,Optional.empty(),new McpCancellation());
            var response=StrictJson.parse(directory.invoke(call).bytes(),65536);var business=response.get("structuredContent");
            assertEquals(SCHEMA,business.path("schema").textValue());
            assertEquals(1,business.path("logs").path("error.log").path("line_count").intValue());
            assertEquals(business,StrictJson.parse(response.path("content").get(0).path("text").textValue().getBytes(StandardCharsets.UTF_8),65536));
            assertFalse(response.path("isError").booleanValue());assertEquals("complete",response.path("resultType").textValue());
        }
        assertEquals(3,calls.get());
        assertThrows(PublicMcpDirectory.ToolFailure.class,()->directory.invoke(new PublicMcpDirectory.ToolCall(
                name,arguments("{\"fingerprint_limit\":null}"),Optional.empty(),new McpCancellation())));
        assertEquals(3,calls.get());
    }

    private ExactRef metadataSource()throws Exception {
        byte[] bytes="binding source DATA fixture; no source admission".getBytes(StandardCharsets.UTF_8);
        Path path=temp.resolve("binding-source-data.txt");Files.write(path,bytes);
        return new ExactRef(path.toString(),bytes.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    }
    private static <Q> JsonNode invoke(McpExecutableDirectory.DirectBinding<Q,RawJson> binding,String json)throws Exception {
        var call=new PublicMcpDirectory.ToolCall(binding.name(),arguments(json),Optional.empty(),new McpCancellation());
        RawJson body=binding.actual().invoke(binding.decoder().decode(call));
        var encoded=StrictJson.parse(binding.encoder().encode(body).bytes(),65536);var value=StrictJson.parse(body.bytes(),65536);
        assertEquals(value,encoded.get("structuredContent"));assertEquals(value,StrictJson.parse(encoded.path("content").get(0).path("text").textValue().getBytes(StandardCharsets.UTF_8),65536));
        assertFalse(encoded.path("isError").booleanValue());assertEquals("complete",encoded.path("resultType").textValue());return value;
    }
    private static PublicMcpDirectory.Arguments arguments(String json){return new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(new RawJson(json.getBytes(StandardCharsets.UTF_8))));}
    private static PublicMcpDirectory.Arguments nullArguments(){return new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.NULL,Optional.of(new RawJson("null".getBytes(StandardCharsets.UTF_8))));}
}
