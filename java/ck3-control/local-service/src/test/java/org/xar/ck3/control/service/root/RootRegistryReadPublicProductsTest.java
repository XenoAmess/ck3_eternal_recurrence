package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.CampaignProjection.*;

/** Original producer -> strict projection -> actual registered handler -> sole existing public serializer.
 * This exercises the data/route boundary, not a fabricated physical Root or Native permission. */
final class RootRegistryReadPublicProductsTest {
    private static final Map<String,String> ORIGINALS = Map.of(
            "src/xar_autoplayer/bridge/campaign_root_context_contract.py", "06fa8e6399672106409a8f840ee96e8c1897b09688176a8704484bd18e6cb3f3",
            "tests/unit/test_campaign_root_context_v1_bridge.py", "602e8b19cfdca2af35bb8723bdb445114005695a3280390516b5a4fc30e8ce82",
            "src/xar_autoplayer/bridge/entity_directory_contract.py", "70dd4a84adc94e937d3bce85cd4262bec0bbc523eab444c143ef66818c3ed9bc",
            "src/xar_autoplayer/bridge/turn_bundle_contract.py", "d02a8e56a83494a9643d9ded350e125ad96d6d6922eef75132e37d711ed91acc",
            "src/xar_autoplayer/bridge/player_vitals_contract.py", "e7be0216b2a37ac39f4545f9f8c352f9bcd0bb79ba6709067bf8b9771d8d1d0a");
    private static final Binding BINDING = new Binding("registry-original-17", BigInteger.valueOf(4),
            BigInteger.valueOf(17), 53182008, BigInteger.valueOf(4));

    @Test void originalProducersReachBothRegisteredConsumersAndPublicRoundTrip() throws Exception {
        for (Value value : array(oracle().get("cases"), "original registry cases")) {
            Obj example = object(value, "original registry case");
            var material = material(example); var invocations = new AtomicInteger();
            PublicBindings registry = registry(revision -> {
                assertEquals(BINDING.revision(), revision); invocations.incrementAndGet(); return material;
            });
            for (String relation : List.of("any", "self", "direct_landed_vassal", "adjacent_external_province_holder")) {
                RawJson actual = registry.lookup(PublicMethod.SEARCH_ENTITIES_V1).orElseThrow().invoke(arguments(
                        "{\"expected_revision\":4,\"relation_filter\":\"" + relation + "\",\"after_character_id\":null,\"limit\":2}"));
                assertEquals(object(example.get("directories"), "directory goldens").get(relation), internalTree(actual),
                        text(example.get("label"), "case") + "/" + relation);
                assertRoundTrip(actual);
            }
            RawJson actual = registry.lookup(PublicMethod.QUERY_TURN_BUNDLE_V1).orElseThrow().invoke(arguments("{\"expected_revision\":4}"));
            assertEquals(example.get("bundle"), internalTree(actual), text(example.get("label"), "case"));
            assertRoundTrip(actual); assertEquals(5, invocations.get());
        }
    }

    @Test void strictArgumentErrorsDoNotReachTheActualReadProducer() throws Exception {
        var calls = new AtomicInteger(); PublicBindings registry = registry(revision -> {
            calls.incrementAndGet(); throw new AssertionError("invalid input reached the ROOT producer");
        });
        var search = registry.lookup(PublicMethod.SEARCH_ENTITIES_V1).orElseThrow();
        for (String invalid : List.of("{}", "[]", "{\"expected_revision\":true}", "{\"expected_revision\":4.0}",
                "{\"expected_revision\":-1}", "{\"expected_revision\":\"01\"}", "{\"expected_revision\":\"+4\"}",
                "{\"expected_revision\":4,\"limit\":null}", "{\"expected_revision\":4,\"limit\":101}",
                "{\"expected_revision\":4,\"limit\":true}", "{\"expected_revision\":4,\"relation_filter\":null}",
                "{\"expected_revision\":4,\"relation_filter\":\"unknown\"}", "{\"expected_revision\":4,\"after_character_id\":false}",
                "{\"expected_revision\":4,\"after_character_id\":0}", "{\"expected_revision\":4,\"unexpected\":null}"))
            assertThrows(IllegalArgumentException.class, () -> search.invoke(arguments(invalid)), invalid);
        assertThrows(IllegalArgumentException.class, () -> search.invoke(new PublicBindings.Missing()));
        assertThrows(IllegalArgumentException.class, () -> search.invoke(new PublicBindings.Null()));
        assertThrows(IllegalArgumentException.class, () -> registry.lookup(PublicMethod.QUERY_TURN_BUNDLE_V1).orElseThrow()
                .invoke(arguments("{\"expected_revision\":4,\"_planning_root_result\":{}}")));
        assertThrows(IllegalArgumentException.class, () -> arguments("{\"expected_revision\":4,\"expected_revision\":4}"));
        assertEquals(0, calls.get());
        var defaults = RootRegistryReadPublicProducts.decodeSearch(arguments("{\"expected_revision\":4}"));
        assertEquals(new EntityDirectory.Request(Relation.ANY, null, 50), defaults.directory());
        assertEquals(defaults, RootRegistryReadPublicProducts.decodeSearch(arguments("{\"expected_revision\":4,\"after_character_id\":null}")));
        assertEquals(new BigInteger("18446744073709551616"), RootRegistryReadPublicProducts.decodeBundle(
                arguments("{\"expected_revision\":18446744073709551616}")).expectedRevision());
        assertEquals(new BigInteger("18446744073709551616"), RootRegistryReadPublicProducts.decodeBundle(
                arguments("{\"expected_revision\":\"18446744073709551616\"}")).expectedRevision());
        assertEquals(defaults, RootRegistryReadPublicProducts.decodeSearch(arguments("{\"expected_revision\":\"4\"}")));
    }

    @Test void actualRegisteredDirectoryAcceptsDecimalRevisionAboveUint64WithoutChangingOriginalRoot() throws Exception {
        BigInteger revision = BigInteger.ONE.shiftLeft(100), nativeRevision = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
        Binding binding = new Binding("original-unavailable-registry-data", revision, nativeRevision, 53182008, revision);
        Source source = new Source("game.command.query-campaign-root-context-v1", nativeRevision, "1.20.0.4",
                "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
        var root = new UnavailableRoot(binding, source, "unavailable original DATA; no physical Root qualification");
        var calls = new AtomicInteger();
        PublicBindings registry = registry(expected -> {
            assertEquals(revision, expected); calls.incrementAndGet();
            return new RootRegistryReadPublicProducts.Material(root, new Obj(Map.of()));
        });
        RawJson publicResult = registry.lookup(PublicMethod.SEARCH_ENTITIES_V1).orElseThrow()
                .invoke(arguments("{\"expected_revision\":\"" + revision + "\"}"));
        Obj wire = DriverJson.object(publicResult.bytes(), RawJson.MAXIMUM_BYTES);
        assertEquals(new Text(nativeRevision.toString()), wire.get("snapshot_revision"));
        assertEquals(new Text(nativeRevision.toString()), object(wire.get("source"), "source").get("query_sequence"));
        assertEquals(DriverJson.object(RegistryWire.encodeDirectory(EntityDirectory.build(root,
                new EntityDirectory.Request(Relation.ANY, null, 50))).bytes(), RawJson.MAXIMUM_BYTES), internalTree(publicResult));
        assertEquals(1, calls.get());
    }

    @Test void originalProducerReachesActualMcpAdapterDirectoryAndBothRpcTransports() throws Exception {
        Obj example = object(array(oracle().get("cases"), "original cases").getFirst(), "original case");
        var original = material(example); var calls = new AtomicInteger();
        PublicBindings registry = registry(expected -> {
            assertEquals(BINDING.revision(), expected); calls.incrementAndGet(); return original;
        });
        for (PublicMethod method : List.of(PublicMethod.SEARCH_ENTITIES_V1, PublicMethod.QUERY_TURN_BUNDLE_V1)) {
            String arguments = "{\"expected_revision\":\"4\"}";
            RawJson actual = registry.lookup(method).orElseThrow().invoke(arguments(arguments));
            org.xar.ck3.control.service.mcp.PublicRegistryRpcAssertions.assertRegistryRpc(
                    registry, "ck3_" + method.pythonName(), arguments, actual);
            Obj expected = method == PublicMethod.SEARCH_ENTITIES_V1
                    ? object(object(example.get("directories"), "directory goldens").get("any"), "directory")
                    : object(example.get("bundle"), "bundle");
            // Search's original default limit is 50, while the differential corpus also tests explicit limit=2.
            if (method == PublicMethod.QUERY_TURN_BUNDLE_V1) assertEquals(expected, internalTree(actual));
            else assertEquals(new IntegerValue(BigInteger.valueOf(50)), internalTree(actual).get("limit"));
        }
        assertEquals(8, calls.get()); // one direct handler + directory + two independent RPC invocations per tool
    }

    @Test void originalSourceFrameBuildAndIntegerMutationsFailBeforeProjection() throws Exception {
        Obj example = object(array(oracle().get("cases"), "cases").getFirst(), "first original case");
        Obj original = object(example.get("native"), "original root envelope");
        Obj root = object(original.get("campaign_root_context"), "original root");
        for (Obj invalid : List.of(original.with("query_sequence", new Bool(true)), original.with("accepted", new IntegerValue(BigInteger.ONE)),
                original.with("snapshot_revision", new IntegerValue(BigInteger.valueOf(18))), original.with("unexpected", Nil.INSTANCE),
                original.with("campaign_root_context", root.with("player_character_id", new Bool(true))),
                original.with("campaign_root_context", root.with("provenance", object(root.get("provenance"), "provenance")
                    .with("executable_sha256", new Text("0".repeat(64)))))))
            assertThrows(IllegalArgumentException.class, () -> RegistryCampaignProjection.root(invalid, BINDING));
        Obj snapshot = object(example.get("snapshot"), "snapshot");
        assertThrows(IllegalArgumentException.class, () -> RegistryCampaignProjection.snapshot(snapshot.with("revision", new IntegerValue(BigInteger.valueOf(5))), BINDING));
        assertThrows(IllegalArgumentException.class, () -> RegistryCampaignProjection.snapshot(snapshot.with("active_event", new Bool(false)), BINDING));
        assertThrows(IllegalArgumentException.class, () -> RegistryCampaignProjection.snapshot(snapshot.with("played_character_gold",
                new Obj(Map.of("raw", new Bool(true), "scale", new IntegerValue(BigInteger.valueOf(100000))))), BINDING));
    }

    @Test void pendingOriginalObjectIsSerializedAsItsOwnPayloadAndAvailabilityStaysExplicit() throws Exception {
        List<Value> cases = array(oracle().get("cases"), "cases");
        var original = material(object(cases.stream().filter(value -> new Text("pending").equals(object(value, "case").get("label"))).findFirst().orElseThrow(), "pending"));
        var result = TurnBundle.build(RegistryCampaignProjection.snapshot(original.snapshot(), BINDING), original.root());
        RawJson output = RegistryWire.encodeBundle(result);
        Obj wire = DriverJson.object(output.bytes(), RawJson.MAXIMUM_BYTES);
        Obj pending = object(object(wire.get("pending_state"), "pending component").get("value"), "pending payload");
        assertEquals(new Obj(Map.of("instance_id", new Text("event-17"), "nested", new Obj(Map.of("original", new Bool(true))))),
                object(pending.get("active_event"), "event component").get("value"));
        assertFalse(new String(output.bytes(), StandardCharsets.UTF_8).contains("\"members\""));
        var missing = material(object(cases.stream().filter(value -> new Text("missing-pending").equals(object(value, "case").get("label"))).findFirst().orElseThrow(), "missing"));
        assertFalse(TurnBundle.build(RegistryCampaignProjection.snapshot(missing.snapshot(), BINDING), missing.root()).readiness().eventPendingReady());
        var actual4 = material(object(cases.stream().filter(value -> new Text("actual4-family").equals(object(value, "case").get("label"))).findFirst().orElseThrow(), "actual4"));
        assertFalse(TurnBundle.build(RegistryCampaignProjection.snapshot(actual4.snapshot(), BINDING), actual4.root()).readiness().realmCouncilReady());
        assertEquals("c_registry_family", ((AvailableRoot) actual4.root()).heldTitlePartition().getLast().titleKey());
        assertThrows(IllegalArgumentException.class, () -> new PartitionRow(new Title(900000, 2, "county"), 23456, null, false, true, "d_nf_bad"));
    }

    @Test void entityReadDoesNotConsumeUnrelatedOptionalBundlePayload() throws Exception {
        Obj example = object(array(oracle().get("cases"), "cases").getFirst(), "original case");
        var original = material(example);
        var input = new RootRegistryReadPublicProducts.Material(original.root(), original.snapshot().with("active_event", new Bool(false)));
        PublicBindings registry = registry(revision -> input);
        assertNotNull(registry.lookup(PublicMethod.SEARCH_ENTITIES_V1).orElseThrow().invoke(arguments("{\"expected_revision\":4}")));
        assertThrows(IllegalArgumentException.class, () -> registry.lookup(PublicMethod.QUERY_TURN_BUNDLE_V1).orElseThrow()
                .invoke(arguments("{\"expected_revision\":4}")));
    }

    private static RootRegistryReadPublicProducts.Material material(Obj example) {
        return new RootRegistryReadPublicProducts.Material(RegistryCampaignProjection.root(object(example.get("native"), "original native root"), BINDING),
                object(example.get("snapshot"), "actual snapshot"));
    }
    private static PublicBindings registry(RootRegistryReadPublicProducts.Current current) throws IOException {
        Path source = Path.of("src/main/java/org/xar/ck3/control/service/root/RootRegistryReadPublicProducts.java").toAbsolutePath().normalize();
        byte[] bytes = Files.readAllBytes(source); ExactRef exact = new ExactRef(source.toString(), bytes.length, DriverJson.sha256(bytes));
        PublicBindings registry = new PublicBindings(); RootRegistryReadPublicProducts.register(registry, exact, current);
        assertEquals(RootRegistryReadPublicProducts.METHODS, java.util.Set.copyOf(registry.coverage().installed()));
        registry.freeze(RootRegistryReadPublicProducts.METHODS); return registry;
    }
    private static PublicBindings.Arguments arguments(String value) { return PublicBindings.present(new RawJson(value.getBytes(StandardCharsets.UTF_8))); }
    private static Obj internalTree(RawJson actual) {
        Obj wire = DriverJson.object(actual.bytes(), RawJson.MAXIMUM_BYTES);
        var profile = switch (text(wire.get("schema"), "Registry public schema")) {
            case EntityDirectory.SCHEMA -> RegistryPublicProfile.Profile.ENTITY_DIRECTORY;
            case TurnBundle.SCHEMA -> RegistryPublicProfile.Profile.TURN_BUNDLE;
            default -> throw new IllegalArgumentException("unexpected Registry public schema");
        };
        return DriverJson.object(RegistryPublicProfile.decode(profile, actual).bytes(), RawJson.MAXIMUM_BYTES);
    }
    private static void assertRoundTrip(RawJson actual) {
        var value = internalTree(actual);
        assertEquals(value, DriverJson.object(encode(value), RawJson.MAXIMUM_BYTES));
    }
    private static Obj oracle() throws Exception {
        Path repo = Path.of(required("xar.repository.root")).toAbsolutePath().normalize();
        Path python = repo.resolve("ck3_autonomous_player");
        for (var original : ORIGINALS.entrySet()) assertEquals(original.getValue(), DriverJson.sha256(Files.readAllBytes(python.resolve(original.getKey()))), original.getKey());
        String script = """
            import ast,copy,json,pathlib,sys
            sys.dont_write_bytecode=True
            base=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(base/'src'))
            from xar_autoplayer.bridge import campaign_root_context_contract as p
            from xar_autoplayer.bridge.entity_directory_contract import build_entity_directory_v1
            from xar_autoplayer.bridge.turn_bundle_contract import build_turn_bundle_v1
            fixture=base/'tests/unit/test_campaign_root_context_v1_bridge.py'
            namespace=dict(vars(p));namespace.update(NATIVE_REVISION=17,DATE_RAW=53182008,PLAYER_CHARACTER_ID=12345)
            names={'_readiness','_provenance','_related_contexts','_council','_frame'}
            definitions=[n for n in ast.parse(fixture.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name in names]
            exec(compile(ast.Module(body=definitions,type_ignores=[]),str(fixture),'exec'),namespace)
            raw=namespace['_frame']();binding=dict(snapshot_id='registry-original-17',revision=4,native_revision=17,date_raw=53182008,expected_revision=4)
            snapshot=dict(snapshot_id=binding['snapshot_id'],revision=4,native_revision=17,date_raw=53182008,paused=True,backend_id='native-headless',
                played_character=dict(character_id=12345,alive=True,stress_points=100),played_character_gold=dict(raw=2000000,scale=100000),
                active_event=None,pending_character_interaction=None,active_wars=[dict(war_id=77,player_side='defender',primary_opponent_character_id=45678,player_relative_war_score=-12)])
            cases=[]
            def add(label,root,state):
                normalized=p.normalize_campaign_root_context_v1(root,expected_date_raw=53182008,expected_snapshot_revision=17)
                native=dict(step='query-campaign-root-context-v1',accepted=True,status=normalized['status'],query_sequence=4,snapshot_revision=17,campaign_root_context=normalized,backend_id='native-headless')
                public=dict(native,binding=binding)
                cases.append(dict(label=label,native=native,snapshot=state,directories={relation:build_entity_directory_v1(public,relation_filter=relation,after_character_id=None,limit=2)
                    for relation in ['any','self','direct_landed_vassal','adjacent_external_province_holder']},bundle=build_turn_bundle_v1(state,public)))
            add('full',raw,copy.deepcopy(snapshot))
            state=copy.deepcopy(snapshot);state['active_event']={'instance_id':'event-17','nested':{'original':True}};state['pending_character_interaction']={'request_id':'interaction-17'};add('pending',raw,state)
            state=copy.deepcopy(snapshot);del state['active_event'];add('missing-pending',raw,state)
            state=copy.deepcopy(snapshot);del state['active_wars'];add('missing-wars',raw,state)
            state=copy.deepcopy(snapshot);state['played_character'].pop('stress_points');state.pop('played_character_gold');add('missing-vitals',raw,state)
            add('unavailable',namespace['_frame']('unavailable'),copy.deepcopy(snapshot))
            root=copy.deepcopy(raw);root['provenance']=dict(p._PROVENANCE_BY_BUILD['1.20.0.4'])
            root['council']=dict(status='unavailable',coverage_key='standard_landed_non_nomadic_core_v1',owner_character_id=12345,positions=[],auxiliary_vacancies_complete=False,unavailable_reason='actual4_council_position_key_source_unavailable')
            root['readiness']['council_ready']=False;root['readiness']['ready']=False
            root['held_title_partition'].append(dict(title=dict(title_id=900000,tier_raw=2,tier_key='county'),first_heir_character_id=23456,capital_province_id=None,primary=False,capital_province_kind='landless_noble_family_no_province',title_key='c_registry_family'))
            add('actual4-family',root,copy.deepcopy(snapshot))
            print(json.dumps({'cases':cases},ensure_ascii=False,separators=(',',':')))
            """;
        ProcessBuilder builder = new ProcessBuilder(required("xar.native.producer.python"), "-I", "-B", "-c", script, python.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); Process child = builder.start();
        try {
            var output = CompletableFuture.supplyAsync(() -> read(child.getInputStream()));
            var error = CompletableFuture.supplyAsync(() -> read(child.getErrorStream()));
            assertTrue(child.waitFor(30, TimeUnit.SECONDS), "original registry producer timed out");
            assertEquals(0, child.exitValue(), new String(error.get(5, TimeUnit.SECONDS), StandardCharsets.UTF_8));
            return DriverJson.object(output.get(5, TimeUnit.SECONDS), RawJson.MAXIMUM_BYTES);
        } finally { if (child.isAlive()) child.destroyForcibly(); }
    }
    private static byte[] read(InputStream input) { try { return input.readAllBytes(); } catch (IOException failure) { throw new UncheckedIOException(failure); } }
    private static String required(String name) { String value = System.getProperty(name); assertTrue(value != null && !value.isBlank(), "original producer differential NOT RUN: missing " + name); return value; }
}
