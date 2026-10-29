package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original Service read-port differential is a declared callback fixture, never native event qualification. */
final class EventOptionPublicCodecTest {
    private static final String PROGRAM = """
            import ast,copy,hashlib,json,pathlib,sys
            m=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
            def pin(r):
                b=pathlib.Path(r['path']).read_bytes()
                if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:raise RuntimeError('event original source drift: '+r['path'])
            refs=m['source_refs']+[m['example']]
            for r in refs:pin(r)
            sys.path.insert(0,m['python_source_root']);sys.path.insert(0,m['tools_root'])
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from xar_autoplayer.bridge.event_contract import event_option_step
            tree=ast.parse(pathlib.Path(m['example']['path']).read_text(encoding='utf-8'));base=None
            for cls in [n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='EventContractTests']:
                for fn in [n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='test_service_selects_typed_event_option_with_revision']:
                    for row in fn.body:
                        if isinstance(row,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='snapshot' for t in row.targets):base=ast.literal_eval(row.value)
            if not isinstance(base,dict) or base.get('revision')!=17 or base.get('active_event',{}).get('instance_id')!=812:raise RuntimeError('actual original Service example changed')
            good=[];bad=[]
            for number in [1,2]:
                for presence in ['missing','null','value']:
                    for frame_revision in [17,(1<<64)-1]:
                        snapshot=copy.deepcopy(base);snapshot['revision']=frame_revision;calls=[];service=object.__new__(GameplayBridgeService)
                        def take_snapshot(*,include_native_command_history=True):
                            if include_native_command_history is not False:raise RuntimeError('original select requested command history')
                            calls.append(['snapshot']);return copy.deepcopy(snapshot)
                        def execute(step,*,expected_revision):
                            calls.append(['execute',step,expected_revision]);return {'accepted':True,'status':'fixture_ack_only','step':step,'revision':expected_revision,'opaque_original':'preserve'}
                        service.snapshot=take_snapshot;service.capabilities=lambda:{'action_steps':['select-event-option-1','select-event-option-2']};service.execute_step=execute
                        arguments={'option_number':number}
                        if presence=='null':arguments.update(event_instance_id=None,expected_revision=None)
                        if presence=='value':arguments.update(event_instance_id=812,expected_revision=frame_revision)
                        original=service.select_event_option(**arguments)
                        if calls!=[['snapshot'],['execute',event_option_step(number),frame_revision]]:raise RuntimeError('original selection did not execute exactly once')
                        public=copy.deepcopy(arguments)
                        if public.get('expected_revision') is not None:public['expected_revision']=str(public['expected_revision'])
                        good.append(dict(arguments=public,snapshot=snapshot,original=original,calls=calls,presence=presence,label='actual_unchanged_Service_with_original_declared_callback_example_and_explicit_derived_wide_revision'))
            for arguments in [{'option_number':True},{'option_number':2.0},{'option_number':0},{'option_number':-1},{'option_number':1,'event_instance_id':True},{'option_number':1,'event_instance_id':0},{'option_number':1,'event_instance_id':812.0}]:
                service=object.__new__(GameplayBridgeService);service.snapshot=lambda **kwargs:copy.deepcopy(base);service.capabilities=lambda:{'action_steps':['select-event-option-1','select-event-option-2']};service.execute_step=lambda *args,**kwargs:(_ for _ in ()).throw(RuntimeError('negative must never dispatch'))
                try:service.select_event_option(**arguments)
                except (ValueError,TypeError):bad.append(arguments)
                else:raise RuntimeError('actual original Service accepted malformed public identity')
            for r in refs:pin(r)
            print(json.dumps({'good':good,'bad':bad,'scope':'Original select_event_option and event_option_step on retained declared callback example; ACK-only result is intentionally not event consumption.'},separators=(',',':')))
            """;
    @Test void missingNullAndCanonicalWideRevisionRoundTripWithoutTypeCoercion() {
        for (EventOptionPublicCodec.Presence instance : EventOptionPublicCodec.Presence.values())
            for (EventOptionPublicCodec.Presence revision : EventOptionPublicCodec.Presence.values()) {
                var request = new EventOptionPublicCodec.Request(new EventActionPreparation.OptionNumber(3), field(instance, 812), field(revision, new BigInteger("18446744073709551615")));
                var encoded = EventOptionPublicCodec.encodeRequest(request); assertEquals(request, EventOptionPublicCodec.decode(PublicBindings.present(encoded)));
                JsonNode n = StrictJson.parse(encoded.bytes(), EventOptionPublicCodec.MAXIMUM_REQUEST_BYTES);
                assertEquals(revision != EventOptionPublicCodec.Presence.MISSING, n.has("expected_revision"));
                if (revision == EventOptionPublicCodec.Presence.VALUE) assertEquals("18446744073709551615", n.get("expected_revision").textValue());
                assertEquals("select-event-option-3", request.optionNumber().operation().value());
            }
    }
    @Test void malformedPublicTokensUnknownFieldsAndNoncanonicalRevisionsFailBeforeAnyAction() {
        assertThrows(IllegalArgumentException.class, () -> EventOptionPublicCodec.decode(new PublicBindings.Missing()));
        assertThrows(IllegalArgumentException.class, () -> EventOptionPublicCodec.decode(new PublicBindings.Null()));
        for (String bad : List.of("{}", "[]", "{\"option_number\":true}", "{\"option_number\":1.0}", "{\"option_number\":0}", "{\"option_number\":1000000000}", "{\"option_number\":1,\"event_instance_id\":0}", "{\"option_number\":1,\"event_instance_id\":true}", "{\"option_number\":1,\"expected_revision\":1}", "{\"option_number\":1,\"expected_revision\":\"01\"}", "{\"option_number\":1,\"expected_revision\":\"+1\"}", "{\"option_number\":1,\"expected_revision\":\"-0\"}", "{\"option_number\":1,\"expected_revision\":\"18446744073709551616\"}", "{\"option_number\":1,\"unknown\":true}", "{\"option_number\":1,\"option_number\":2}", "{\"option_number\":1} null"))
            assertThrows(IllegalArgumentException.class, () -> EventOptionPublicCodec.decode(PublicBindings.present(raw(bad))), bad);
        assertThrows(IllegalArgumentException.class, () -> EventOptionPublicCodec.decode(PublicBindings.present(new RawJson(new byte[]{(byte) 0xc0,(byte) 0x80}))));
    }
    @Test void actualOriginalServicePreservesAuthoredOptionAndSelectedRevision() throws Exception {
        JsonNode corpus = originalCorpus(); int count = 0;
        for (JsonNode sample : corpus.get("good")) {
            var request = EventOptionPublicCodec.decode(PublicBindings.present(new RawJson(sample.get("arguments").toString().getBytes(StandardCharsets.UTF_8))));
            assertEquals(sample.get("original").get("option_number").intValue(), request.optionNumber().value());
            assertEquals(sample.get("original").get("step").textValue(), request.optionNumber().operation().value());
            assertEquals(request.optionNumber().value() - 1, sample.get("original").get("option_index").intValue());
            BigInteger selectedRevision = request.expectedRevision().presence() == EventOptionPublicCodec.Presence.VALUE ? request.expectedRevision().value() : sample.get("snapshot").get("revision").bigIntegerValue();
            assertEquals(sample.get("calls").get(1).get(2).bigIntegerValue(), selectedRevision); assertEquals("fixture_ack_only", sample.get("original").get("status").textValue());
            assertEquals(request, EventOptionPublicCodec.decode(PublicBindings.present(EventOptionPublicCodec.encodeRequest(request)))); count++;
        }
        assertEquals(12, count);
        for (JsonNode bad : corpus.get("bad")) assertThrows(IllegalArgumentException.class, () -> EventOptionPublicCodec.decode(PublicBindings.present(new RawJson(bad.toString().getBytes(StandardCharsets.UTF_8)))));
    }
    static JsonNode originalCorpus() throws Exception {
        Path manifestPath = Path.of(required("xar.event.option.oracle.manifest")); byte[] bytes = Files.readAllBytes(manifestPath); assertEquals(required("xar.event.option.oracle.manifest.sha256"), digest(bytes));
        JsonNode manifest = StrictJson.parse(bytes,131072); verify(manifest);
        Process process = new ProcessBuilder(required("xar.python"),"-I","-B","-X","utf8","-c",PROGRAM,manifestPath.toString()).redirectErrorStream(true).start();
        try (var executor = Executors.newSingleThreadExecutor()) {
            var output = executor.submit(() -> process.getInputStream().readNBytes(1048577));
            if (!process.waitFor(60,TimeUnit.SECONDS)) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); throw new IllegalStateException("actual original event Service timeout"); }
            byte[] result = output.get(); assertEquals(0,process.exitValue(),new String(result,StandardCharsets.UTF_8)); assertTrue(result.length<=1048576); verify(manifest);
            return OpportunityJson.toNode(DriverJson.object(result,1048576));
        } finally { if (process.isAlive()) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); } }
    }
    private static <T> EventOptionPublicCodec.Field<T> field(EventOptionPublicCodec.Presence presence,T value) { return switch (presence) { case MISSING -> EventOptionPublicCodec.Field.missing(); case NULL -> EventOptionPublicCodec.Field.nullValue(); case VALUE -> EventOptionPublicCodec.Field.of(value); }; }
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static void verify(JsonNode manifest) throws Exception { for (JsonNode ref : manifest.get("source_refs")) pin(ref); pin(manifest.get("example")); }
    private static void pin(JsonNode ref) throws Exception { byte[] b = Files.readAllBytes(Path.of(ref.get("path").textValue())); assertEquals(ref.get("bytes").longValue(),b.length); assertEquals(ref.get("sha256").textValue(),digest(b)); }
    private static String digest(byte[] b) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b)); }
    private static String required(String property) { String value = System.getProperty(property); if (value==null || value.isBlank()) throw new IllegalStateException("Mandatory event original producer setting is missing: "+property); return value; }
}
