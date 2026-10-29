package org.xar.ck3.control.service.mcp;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog.Catalog;
import org.xar.ck3.control.wave2.events.discovery.EventDiscovery;
import org.xar.ck3.control.wave2.events.discovery.EventDiscoveryCodec;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Actual original producer -> complete Java provider -> Service binding -> MCP/strict response differential. No Game. */
final class EventDiscoveryProducerParityTest {
    @TempDir Path temporary;
    private static final int OUTPUT_LIMIT = 8 * 1024 * 1024;
    private record Pin(String path, long bytes, String sha256) { }
    private static final List<Pin> PINS = List.of(
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py", 283568, "b7569231226484b0bdd98c40ace14a82672b2138a0aab77711e559a4d9b8ccbc"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/discovery.py", 14888, "867d5fedf0f061b6f107999beae2189c53b180aef9d5e3072b23302695416398"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/builds.py", 1859, "afd7f9fb5abf7ea91fb4888767135027db9f9390151e5df6edaa719d19e73712"),
            new Pin("ck3_autonomous_player/schemas/vanilla-event-knowledge-index-v1.schema.json", 3479, "e4fba84b215803b56ab4d1e08aef77f4debf4eb7d695914217d3510a821ef208"));
    private static final String ORIGINAL = """
import json,os,sys
from pathlib import Path
from unittest.mock import patch
root=Path(sys.argv[1]).resolve()
os.environ['XAR_AUTOPLAYER_STATE_DIR']=sys.argv[2]
sys.path[:0]=[str(root/'ck3_autonomous_player'/'src')]
from xar_autoplayer.vanilla_events.discovery import ck3_list_vanilla_event_knowledge_v1 as original
from xar_autoplayer.vanilla_events.portable_evidence import EvidenceBundleError
from xar_autoplayer.bridge.mcp_server import _ck3_list_vanilla_event_knowledge_v1 as wrapper
from jsonschema import Draft202012Validator
schema=json.loads((root/'ck3_autonomous_player/schemas/vanilla-event-knowledge-index-v1.schema.json').read_text(encoding='utf-8'))
Draft202012Validator.check_schema(schema)
validator=Draft202012Validator(schema)
rows=json.loads(sys.stdin.buffer.read(4*1024*1024+1))
if not isinstance(rows,list) or len(rows)>4096:raise RuntimeError('bounded discovery differential required')
out=[]
for row in rows:
    args=dict(row['arguments'])
    if row.get('catalog') is not None:
        catalog=row['catalog'];args['build']=args.pop('ck3_build','1.20.0.4')
        value=original(**args,contracts=catalog['contracts'],analysis=catalog['analysis'],observations=catalog['observations'],portable_event_keys=set(row['portable_keys']))
    else:
        effect=EvidenceBundleError('explicit original bundle failure') if row['bundle_failure'] else None
        with patch('xar_autoplayer.bridge.mcp_server.portable_event_keys_v1',return_value=frozenset(row['portable_keys']),side_effect=effect):
            value=wrapper(**args)
    validator.validate(value)
    out.append(value)
raw=json.dumps(out,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')
if len(raw)>8*1024*1024:raise RuntimeError('bounded discovery producer output exceeded')
sys.stdout.buffer.write(raw)
""";

    @Test @Timeout(90) void everyBuildWalksActualKeysetPagesAndPreservesWholeDatasetAndFilteredCounters() throws Exception {
        VanillaEventCatalog catalog = VanillaEventCatalog.load();
        List<Value> requests = new ArrayList<>(), actual = new ArrayList<>();
        var service = new EventDiscoveryPublicService(catalog, Set::of, "1.20.0.4");
        for (String build : RegisteredEventKnowledge.EXE.keySet().stream().sorted().toList()) {
            String cursor = null, digest = null; List<String> keys = new ArrayList<>();
            do {
                ObjectValue args = object("ck3_build", v(build), "limit", n(7)); if (cursor != null) args = args.with("after_key", v(cursor));
                ObjectValue wire = invoke(service, args); requests.add(original(args, Set.of(), false)); actual.add(wire);
                var result = EventDiscoveryCodec.decodeResponse(wire); assertTrue(result.available());
                if (digest == null) digest = result.datasetSha256(); else assertEquals(digest, result.datasetSha256());
                keys.addAll(result.items().stream().map(EventDiscovery.Item::eventDefinitionKey).toList()); cursor = result.nextAfterKey();
            } while (cursor != null);
            assertEquals(catalog.catalog(build).contracts().keySet().stream().sorted(EventDiscovery.KEY_ORDER).toList(), keys);
            assertEquals(keys.size(), Set.copyOf(keys).size());
            for (ObjectValue filter : List.of(object("query", v("events/dlc/tgp/tgp_dynastic_cycle_events.txt")),
                    object("namespace", v("tgp_dynastic_cycle")), object("evidence_class", v("source-reviewed")),
                    object("evidence_class", v("migration-only")), object("has_observations", new BooleanValue(true)),
                    object("has_observations", new BooleanValue(false)), object("query", v("\u00a0\u2003HEALTH\u00a0")),
                    object("query", v("\n")), object("query", v("不存在的事件")))) {
                ObjectValue args = filter.with("ck3_build", v(build)).with("limit", n(100));
                actual.add(invoke(service, args)); requests.add(original(args, Set.of(), false));
            }
            if (!keys.isEmpty()) {
                ObjectValue args = object("ck3_build", v(build), "namespace", v("filter_with_no_matches"), "after_key", v(keys.getFirst()));
                ObjectValue wire = invoke(service, args); assertTrue(EventDiscoveryCodec.decodeResponse(wire).available());
                actual.add(wire); requests.add(original(args, Set.of(), false));
            }
            // Mapping insertion order is visible when a search spans adjacent source paths.
            for (ObjectValue analysis : catalog.catalog(build).analysis().values()) {
                if (!(analysis.get("source_sha256") instanceof ObjectValue paths) || paths.fields().size() < 2) continue;
                List<String> ordered = new ArrayList<>(paths.fields().keySet());
                ObjectValue args = object("ck3_build", v(build), "query", v(ordered.get(0) + "\n" + ordered.get(1)), "limit", n(100));
                actual.add(invoke(service, args)); requests.add(original(args, Set.of(), false));
            }
        }
        assertEquals(new ArrayValue(actual), oracle(requests), "actual original full response, counters, digest, nullable cursor and page order");
    }

    @Test @Timeout(90) void invalidParameterPriorityNullableEchoAndStrictSerializationMatchActualProducer() throws Exception {
        var catalog = VanillaEventCatalog.load(); var service = new EventDiscoveryPublicService(catalog, Set::of, "1.20.0.4");
        List<Value> requests = new ArrayList<>(), actual = new ArrayList<>();
        List<ObjectValue> cases = new ArrayList<>(List.of(object("ck3_build", v("1.19.0.7")), object("ck3_build", RetainedJson.NULL),
                object("query", n(4)), object("namespace", v("\u00a0")), object("evidence_class", v("reviewed")),
                object("evidence_class", new ArrayValue(List.of())), object("has_observations", v("yes")),
                object("limit", n(0)), object("limit", n(101)), object("limit", new BooleanValue(true)),
                object("limit", new FloatingValue(50.0)), object("limit", v("50")), object("after_key", v("")),
                object("after_key", v("not_registered.1")), object("ck3_build", n(4), "query", n(5), "limit", n(0)),
                object("namespace", RetainedJson.NULL), object("query", RetainedJson.NULL), object("has_observations", RetainedJson.NULL)));
        for (String field : List.of("ck3_build", "evidence_class", "limit", "after_key")) cases.add(object(field, RetainedJson.NULL));
        for (ObjectValue args : cases) {
            ObjectValue wire = invoke(service, args); var decoded = EventDiscoveryCodec.decodeResponse(wire);
            assertEquals(wire, EventDiscoveryCodec.response(decoded)); actual.add(wire); requests.add(original(args, Set.of(), false));
        }
        ObjectValue good = invoke(service, object());
        for (String field : good.fields().keySet()) {
            Map<String, Value> missing = new LinkedHashMap<>(good.fields()); missing.remove(field);
            assertThrows(IllegalArgumentException.class, () -> EventDiscoveryCodec.decodeResponse(new ObjectValue(missing)), field);
        }
        assertThrows(IllegalArgumentException.class, () -> service.decode(arguments(object("unexpected", n(1)))));
        assertThrows(IllegalArgumentException.class, () -> EventDiscoveryCodec.decodeResponse(good.with("schema_version", new BooleanValue(true))));
        assertEquals(new ArrayValue(actual), oracle(requests));
    }

    @Test @Timeout(90) void originalHistoricalPortableLookupAndBundleFailureDoNotChangeKnowledgeMembership() throws Exception {
        var catalog = VanillaEventCatalog.load(); String key = catalog.catalog("1.19.0.6").contracts().keySet().stream().sorted().findFirst().orElseThrow();
        Set<String> keys = Set.of(key); AtomicInteger reads = new AtomicInteger();
        var service = new EventDiscoveryPublicService(catalog, () -> { reads.incrementAndGet(); return keys; }, "1.20.0.4");
        List<Value> requests = new ArrayList<>(), actual = new ArrayList<>();
        for (String build : List.of("1.20.0.4", "1.19.0.6")) {
            ObjectValue args = object("ck3_build", v(build), "query", v(key)); actual.add(invoke(service, args)); requests.add(original(args, keys, false));
        }
        assertEquals(1, reads.get(), "only historical exact build may access portable evidence");
        var failed = new EventDiscoveryPublicService(catalog, () -> { throw new IOException("actual bundle unavailable fixture"); }, "1.20.0.4");
        ObjectValue args = object("ck3_build", v("1.19.0.6"), "limit", n(3));
        ObjectValue unavailableBundle = invoke(failed, args), absentPortable = invoke(new EventDiscoveryPublicService(catalog, Set::of, "1.20.0.4"), args);
        assertEquals(absentPortable, unavailableBundle, "bundle failure affects only portable evidence, never the knowledge dataset");
        actual.add(unavailableBundle); requests.add(original(args, keys, true));
        assertEquals(new ArrayValue(actual), oracle(requests));
    }

    @Test @Timeout(90) void injectedUnicodeOpaqueFloatAndSourcePathRecordsUseSharedCanonicalProducer() throws Exception {
        var full = VanillaEventCatalog.load();
        ObjectValue contract = object("root_character_id", v("$player"), "opaque_float", new FloatingValue(1e-7), "negative_zero", new FloatingValue(-0.0));
        Map<String, ObjectValue> contracts = Map.of("alpha.1", contract, "zeta.2", object(), "\ue000.1", object(), "𐀀.1", object());
        Map<String, ObjectValue> analysis = Map.of("alpha.1", object("review_summary", v("Straße Σς𐐀\n末尾")),
                "zeta.2", object("review_summary", v("Zeta route"), "source_sha256",
                        object("events/second.txt", v("B".repeat(64)), "events/资料.txt", v("A".repeat(64)))));
        Map<String, ObjectValue> observations = Map.of("alpha.1", object("exemplars", new ArrayValue(List.of(object("run", v("fixture"))))));
        var custom = new Catalog("1.19.0.6", contracts, analysis, observations);
        var discovery = new EventDiscovery(build -> custom, full.textRules());
        ObjectValue rawCatalog = object("contracts", table(contracts), "analysis", table(analysis), "observations", table(observations));
        List<Value> requests = new ArrayList<>(), actual = new ArrayList<>();
        for (String query : List.of("", "STRASSE", "σσ", "𐐨", "资料", "\n", "\u00a0STRASSE\u00a0", "events/second.txt\nevents/资料.txt")) {
            ObjectValue args = object("ck3_build", v("1.19.0.6"), "query", v(query));
            var result = discovery.list(EventDiscoveryCodec.decodeRequest(args, full.textRules(), "1.20.0.4"), Set.of("alpha.1"));
            actual.add(EventDiscoveryCodec.response(result)); requests.add(original(args, Set.of("alpha.1"), false).with("catalog", rawCatalog));
        }
        assertEquals(new ArrayValue(actual), oracle(requests), "full original canonical record digests and Unicode text rules");
    }

    @Test void descriptorDrivenDefaultAndAbsentNullArgumentsUseTheSameActualProvider() throws Exception {
        var catalog = VanillaEventCatalog.load();
        // Descriptor metadata is a software constructor vector; only Root's exact original descriptor can qualify installation.
        var descriptor = new ToolDescriptor(EventDiscoveryPublicService.NAME, new RawJson(("{\"name\":\"" + EventDiscoveryPublicService.NAME
                + "\",\"inputSchema\":{\"type\":\"object\",\"properties\":{\"ck3_build\":{\"type\":\"string\",\"default\":\"1.20.0.4\"}}}}")
                .getBytes(StandardCharsets.UTF_8)));
        var service = EventDiscoveryPublicService.fromOriginalDescriptor(catalog, Set::of, descriptor);
        assertSame(catalog, service.catalog(), "query and discovery Root composition must borrow the same complete immutable catalog");
        var empty = service.decode(arguments(object()));
        assertEquals(empty, service.decode(new Arguments(Presence.MISSING, Optional.empty())));
        assertEquals(empty, service.decode(new Arguments(Presence.NULL, Optional.of(new RawJson("null".getBytes(StandardCharsets.UTF_8))))));
        assertEquals("1.20.0.4", empty.parameters().ck3Build());
        assertThrows(IllegalArgumentException.class, () -> new EventDiscoveryPublicService(catalog, Set::of, "unsupported"));
    }

    private ObjectValue invoke(EventDiscoveryPublicService service, ObjectValue args) throws Exception {
        var binding = service.actualMethods(new ExactRef("software-only/EventDiscoveryPublicService.java", 1, "1".repeat(64))).getFirst();
        return invokeTyped(binding, args);
    }
    private static <Q, R> ObjectValue invokeTyped(McpExecutableDirectory.DirectBinding<Q, R> binding, ObjectValue args) throws Exception {
        var call = new ToolCall(EventDiscoveryPublicService.NAME, arguments(args), Optional.empty(), new McpCancellation());
        Q request = binding.decoder().decode(call); R response = binding.actual().invoke(request);
        CallResult result = binding.encoder().encode(response);
        ObjectValue envelope = RetainedJson.object(RetainedJson.parse(result.bytes()));
        assertEquals(new BooleanValue(false), envelope.get("isError"));
        ObjectValue wire = RetainedJson.object(envelope.get("structuredContent"));
        assertEquals(wire, EventDiscoveryCodec.response(EventDiscoveryCodec.decodeResponse(wire))); return wire;
    }
    private static Arguments arguments(ObjectValue args) { return new Arguments(Presence.VALUE, Optional.of(new RawJson(RetainedJson.encode(args)))); }
    private static ObjectValue original(ObjectValue args, Set<String> portable, boolean failure) {
        return object("arguments", args, "portable_keys", new ArrayValue(portable.stream().sorted().map(EventDiscoveryProducerParityTest::v).map(Value.class::cast).toList()),
                "bundle_failure", new BooleanValue(failure));
    }
    private ArrayValue oracle(List<Value> requests) throws Exception {
        String repository = System.getProperty("xar.repository.root"), python = System.getProperty("xar.python");
        if (repository == null || python == null) throw new IllegalStateException("discovery parity requires explicit xar.repository.root/xar.python; never skip as pass");
        Path root = Path.of(repository).toRealPath(); verify(root);
        ProcessBuilder command = new ProcessBuilder(python, "-I", "-B", "-c", ORIGINAL, root.toString(), temporary.resolve("original-state").toString());
        command.environment().put("PYTHONDONTWRITEBYTECODE", "1"); command.environment().put("PYTHONNOUSERSITE", "1"); command.environment().put("PYTHONUTF8", "1");
        command.redirectErrorStream(true); Process process = command.start();
        CompletableFuture<byte[]> output = CompletableFuture.supplyAsync(() -> {
            try { return process.getInputStream().readNBytes(OUTPUT_LIMIT + 1); }
            catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
        });
        try {
            try (var stdin = process.getOutputStream()) { stdin.write(RetainedJson.encode(new ArrayValue(requests))); }
            assertTrue(process.waitFor(60, TimeUnit.SECONDS), "actual original discovery process timed out");
            byte[] raw = output.get(5, TimeUnit.SECONDS); verify(root);
            assertEquals(0, process.exitValue(), "actual original producer failed: " + new String(raw, StandardCharsets.UTF_8));
            assertTrue(raw.length <= OUTPUT_LIMIT, "bounded original discovery output required");
            return (ArrayValue) RetainedJson.parse(raw, new RetainedJson.ParseBudget(OUTPUT_LIMIT, 1_000_000, 128));
        } finally { if (process.isAlive()) process.destroyForcibly(); }
    }
    private static void verify(Path root) throws Exception {
        for (Pin pin : PINS) {
            Path path = root.resolve(pin.path()).toRealPath(); assertTrue(path.startsWith(root), "original source escaped repository");
            byte[] raw = Files.readAllBytes(path); assertEquals(pin.bytes(), raw.length, pin.path());
            assertEquals(pin.sha256(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)), pin.path());
        }
    }
    private static ObjectValue table(Map<String, ObjectValue> values) { return new ObjectValue(new LinkedHashMap<>(values)); }
    private static ObjectValue object(Object... fields) {
        Map<String, Value> values = new LinkedHashMap<>();
        for (int index = 0; index < fields.length; index += 2) values.put((String) fields[index], (Value) fields[index + 1]);
        return new ObjectValue(values);
    }
    private static StringValue v(String value) { return new StringValue(value); }
    private static IntegerValue n(int value) { return new IntegerValue(BigInteger.valueOf(value)); }
}
