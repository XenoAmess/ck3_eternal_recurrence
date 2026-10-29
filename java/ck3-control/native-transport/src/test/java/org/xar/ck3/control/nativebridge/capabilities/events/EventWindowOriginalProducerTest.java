package org.xar.ck3.control.nativebridge.capabilities.events;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** Original pinned Python normalizer and original fixture functions execute in an independent process. */
final class EventWindowOriginalProducerTest {
    private static final String ORACLE="""
        import ast,base64,hashlib,json,sys
        from pathlib import Path
        root=Path(sys.argv[1]); sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
        sources=[('ck3_autonomous_player/src/xar_autoplayer/bridge/event_window_context_contract.py','c98985f1afe9196331e30c0f9b0cc2a7fadc9507ef6d3c2b77292bc82e619ef4'),
          ('ck3_autonomous_player/tests/unit/test_event_window_context_v1_bridge.py','384208bffa65e183d82a1dd4510f7f7bb99ccb553b3928fac9c7b7f1f6f08463')]
        for name,digest in sources:
            if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest: raise RuntimeError('original event producer/fixture drift')
        from xar_autoplayer.bridge.event_window_context_contract import normalize_current_event_window_context_v1
        if sys.argv[2]=='fixture':
            tree=ast.parse((root/sources[1][0]).read_text(encoding='utf-8-sig')); nodes=[]
            for n in tree.body:
                if isinstance(n,ast.Assign) and (isinstance(n.value,ast.Constant) or (isinstance(n.value,ast.UnaryOp) and isinstance(n.value.op,ast.USub) and isinstance(n.value.operand,ast.Constant) and type(n.value.operand.value) is int)): nodes.append(n)
                elif isinstance(n,ast.FunctionDef) and n.name in ('_scope','_indicator_rows','_frame'): nodes.append(n)
            scope={}; exec(compile(ast.Module(body=nodes,type_ignores=[]),str(root/sources[1][0]),'exec'),scope)
            print(json.dumps(scope['_frame'](sys.argv[3]),ensure_ascii=True))
        else:
            value=json.loads(base64.b64decode(sys.argv[3]))
            try:
                result=normalize_current_event_window_context_v1(value,expected_event_instance_id=0x01000029,expected_date_raw=741221,expected_snapshot_revision=17)
                print(json.dumps({'accepted':True,'value':result},ensure_ascii=True))
            except ValueError: print(json.dumps({'accepted':False}))
        """;
    private static Binding binding(Build build) { return new Binding(build,BigInteger.valueOf(17),741221,0x01000029); }
    private static RawJson raw(JsonNode value) { return new RawJson(value.toString().getBytes(StandardCharsets.UTF_8)); }
    static ObjectNode fixture(String status,Build build) throws Exception {
        ObjectNode f=oracle("fixture",status); ObjectNode p=(ObjectNode)f.get("provenance");
        p.put("root",build.root()).put("idler_vtable_rva",build.vtable()).put("backend_id",build.backend());
        if (f.get("options").isArray()) for (JsonNode option:f.get("options")) ((ObjectNode)option.get("effect_indicators")).put("coverage",build.coverage());
        return f;
    }
    private static ObjectNode oracle(String mode,String value) throws Exception {
        String repository=System.getProperty("xar.repository.root"), python=System.getProperty("xar.python");
        assertNotNull(repository,"required xar.repository.root; never skip"); assertNotNull(python,"required absolute xar.python; never skip");
        assertTrue(Path.of(python).isAbsolute(),"xar.python must be an explicit absolute interpreter");
        Process process=new ProcessBuilder(python,"-c",ORACLE,Path.of(repository).toString(),mode,value).redirectErrorStream(true).start();
        try {
            assertTrue(process.waitFor(30,TimeUnit.SECONDS),"original event producer process timed out");
            byte[] output=process.getInputStream().readAllBytes(); assertEquals(0,process.exitValue(),new String(output,StandardCharsets.UTF_8));
            return EventWindowCodec.parse(new RawJson(output));
        } finally { if (process.isAlive()) process.destroyForcibly(); }
    }
    private static boolean accepted(ObjectNode f) throws Exception { return oracle("normalize",Base64.getEncoder().encodeToString(raw(f).bytes())).get("accepted").booleanValue(); }
    @Test void originalProducerAllExactBuildsRoundTripAndOptionIdentity() throws Exception {
        for (Build build:Build.values()) {
            ObjectNode f=fixture("available",build); assertTrue(accepted(f));
            Available context=assertInstanceOf(Available.class,EventWindowCodec.decode(raw(f),binding(build)));
            assertEquals(f,EventWindowCodec.parse(EventWindowCodec.encode(context)));
            assertEquals(context,EventWindowCodec.decode(EventWindowCodec.encode(context),binding(build)));
            Option first=context.firstDisplayed().orElseThrow(); assertFalse(first.enabled());
            assertEquals(0,first.renderedIndex()); assertEquals(3,first.nativeOptionIndex()); assertEquals(BigInteger.valueOf(4),first.publicOptionNumber());
            assertFalse(context.readiness().effectPreview()); assertFalse(context.readiness().semanticDecision());
        }
    }
    @Test void originalProducerRejectsWrongFieldsTypesReadinessAndLocator() throws Exception {
        ObjectNode base=fixture("available",Build.CROZIER4); List<ObjectNode> bad=new ArrayList<>();
        ObjectNode row=base.deepCopy(); row.remove("saved_scopes"); bad.add(row);
        row=base.deepCopy(); row.put("unexpected",1); bad.add(row);
        row=base.deepCopy(); row.put("snapshot_revision",17.0); bad.add(row);
        row=base.deepCopy(); row.put("date_raw",true); bad.add(row);
        row=base.deepCopy(); ((ObjectNode)row.get("provenance")).put("idler_vtable_rva","0x44BC408"); bad.add(row);
        row=base.deepCopy(); ((ObjectNode)row.get("readiness")).put("effect_preview_ready",true); bad.add(row);
        row=base.deepCopy(); ((ObjectNode)row.get("options").get(0)).put("native_option_index",false); bad.add(row);
        for (ObjectNode malformed:bad) { assertFalse(accepted(malformed)); assertThrows(IllegalArgumentException.class,()->EventWindowCodec.decode(raw(malformed),binding(Build.CROZIER4))); }
    }
    @Test void partialUnavailableRetainsOnlyDiagnosticDefinition() throws Exception {
        ObjectNode f=fixture("unavailable",Build.CROZIER4); assertTrue(accepted(f));
        assertInstanceOf(Unavailable.class,EventWindowCodec.decode(raw(f),binding(Build.CROZIER4)));
        f.put("unavailable_reason","event_saved_scope_invalid").put("event_definition_key","health.1101").put("calculated_event_id",1101).put("runtime_stats_ordinal",3);
        ((ObjectNode)f.get("readiness")).put("event_definition_identity_ready",true); assertTrue(accepted(f));
        Unavailable context=assertInstanceOf(Unavailable.class,EventWindowCodec.decode(raw(f),binding(Build.CROZIER4)));
        assertEquals("health.1101",context.partialDefinition().orElseThrow().key()); assertFalse(context.readiness().optionPresentation());
        f.putArray("options"); assertFalse(accepted(f)); assertThrows(IllegalArgumentException.class,()->EventWindowCodec.decode(raw(f),binding(Build.CROZIER4)));
    }
    @Test void publicArgumentsRejectMissingNullWrongFieldBoolAndFloat() {
        assertThrows(IllegalArgumentException.class,()->EventWindowService.decode(new PublicBindings.Missing()));
        assertThrows(IllegalArgumentException.class,()->EventWindowService.decode(new PublicBindings.Null()));
        for (String body:List.of("{}","{\"event_instance_id\":true,\"expected_revision\":9}","{\"event_instance_id\":1,\"expected_revision\":9.0}","{\"event_id\":1,\"expected_revision\":9}"))
            assertThrows(IllegalArgumentException.class,()->EventWindowService.decode(new PublicBindings.Value(new RawJson(body.getBytes(StandardCharsets.UTF_8)))));
    }
}
