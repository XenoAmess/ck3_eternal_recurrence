package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.wave2.military.combatwire.CombatRequest;
import org.xar.ck3.control.service.mcp.McpCancellation;
import org.xar.ck3.control.service.mcp.McpCoverage;
import org.xar.ck3.control.service.mcp.PublicMcpBindings;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpNativeAdapter;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Tests real supplied registration and sole shared argument codec, stopping before a physical Root exists. */
final class RootArmySuppliedPublicProductsTest {
    private static final ExactRef SOURCE = new ExactRef("D:/fixture/actual-army-producer.java", 1, "b".repeat(64));
    private static final ArmyCalls.Revision REVISION = new ArmyCalls.Revision(new Present<>(BigInteger.valueOf(7)));
    private static RootArmySuppliedPublicProducts.Sources sources() {
        return new RootArmySuppliedPublicProducts.Sources(SOURCE, SOURCE, SOURCE, SOURCE, SOURCE, SOURCE,
                SOURCE, SOURCE, SOURCE, SOURCE, SOURCE, SOURCE, SOURCE, SOURCE,
                SOURCE, SOURCE, SOURCE,
                List.of(SOURCE, SOURCE, SOURCE, SOURCE, SOURCE, SOURCE));
    }
    private static final class ReachedCurrent extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final PublicMethod method; private transient final ArmyCalls.Call input; private final int generation;
        ReachedCurrent(PublicMethod method, ArmyCalls.Call input, int generation) {
            this.method = method; this.input = input; this.generation = generation;
        }
    }
    private static RootArmySuppliedPublicProducts.Current current(AtomicInteger calls, AtomicInteger generation) {
        return new RootArmySuppliedPublicProducts.Current() {
            @Override public <Q extends ArmyCalls.Call,R> R invoke(PublicMethod method, Q input, Class<R> result,
                    RootArmySuppliedPublicProducts.Invocation<Q,R> original) {
                calls.incrementAndGet(); assertNotNull(original); assertEquals(method, input.method());
                throw new ReachedCurrent(method, input, generation.get());
            }
        };
    }
    @Test void everySuppliedMethodUsesItsSoleTypedCodecAndDefersCurrentRootUntilInvocation() throws Exception {
        var calls = new AtomicInteger(); var generation = new AtomicInteger(1); var registry = new PublicBindings();
        var selectedClasses = new java.util.HashSet<Class<?>>();
        var contribution = RootArmySuppliedPublicProducts.install(registry, (module,type) -> {
            selectedClasses.add(type);
            if (type == ArmyCallCodec.class || type == ArmyWarPublicResultCodec.class || type == ArmyWarOriginalResultCodec.class || type == ArmyPublicWire.class
                    || type == org.xar.ck3.control.application.driver.DriverReadHistoryPublisher.class)
                assertEquals(RootRuntimeSelectedSources.Module.APPLICATION, module);
            else if (type == RootArmySuppliedPublicProducts.class || type == RootApplicationSession.class)
                assertEquals(RootRuntimeSelectedSources.Module.LOCAL_SERVICE, module);
            else assertEquals(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT, module);
            return SOURCE;
        }, current(calls, generation));
        assertTrue(contribution.direct().isEmpty()); assertTrue(contribution.diagnostics().isEmpty());
        assertTrue(contribution.gaps().isEmpty());
        assertTrue(selectedClasses.containsAll(RootArmySuppliedPublicProducts.combatImplementations()));
        assertTrue(selectedClasses.contains(ArmyWarOriginalResultCodec.class),"ordinary Service encoding must retain its actual original Driver producer");
        assertEquals(0, calls.get(), "pre-Core registration cannot resolve a runtime");
        assertEquals(34, registry.coverage().installed().size());
        assertEquals(RootArmySuppliedPublicProducts.METHODS, Set.copyOf(registry.coverage().installed()));
        for (var reserved : RootArmySuppliedPublicProducts.RESERVED) assertTrue(registry.lookup(reserved).isEmpty());
        assertTrue(registry.lookup(PublicMethod.QUERY_WAR_TERMINATION_EXIT_TERMS).isPresent(),
                "retain the original explicit disabled-preview refusal, without a Ready result");
        assertEquals(ArmyDeclarationCollection.Reply.class,
                registry.lookup(PublicMethod.COLLECT_DECLARABLE_WARS_RESULT_V1).orElseThrow().resultType());
        assertEquals(47, RootArmySuppliedPublicProducts.RESERVED.size() + registry.coverage().installed().size());
        var fixtures = new ArrayList<ArmyCalls.Call>();
        for (var method : RootArmySuppliedPublicProducts.METHODS) fixtures.add(input(method));
        for (var original : fixtures) {
            var binding = registry.lookup(original.method()).orElseThrow();
            assertEquals(original.getClass(), binding.requestType());
            assertEquals(original.method(), binding.info().method());
            assertEquals(PublicRoutes.Status.IMPLEMENTED, binding.info().status());
            assertThrows(IllegalArgumentException.class, () -> binding.invoke(PublicBindings.present(ArmyCallCodec.encode(original))),
                    "the actual registry must forbid invocation before Root freeze");
        }
        assertEquals(0, calls.get()); registry.freeze(RootArmySuppliedPublicProducts.METHODS);
        for (var original : fixtures) {
            var binding = registry.lookup(original.method()).orElseThrow();
            var wire = ArmyCallCodec.encode(original);
            assertEquals(original, ArmyCallCodec.decode(original.method(), wire), "sole producer/consumer JSON roundtrip");
            if (original.method() == PublicMethod.QUERY_WAR_ENTRY_ASSESSMENTS) {
                var publicFields = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,
                        StrictJson.parse(wire.bytes(), StrictJson.INPUT_MAX_BYTES));
                assertTrue(publicFields.has("target_character_ids")); assertFalse(publicFields.has("target_province_ids"));
                var oldAlias = publicFields.deepCopy(); oldAlias.set("target_province_ids", oldAlias.remove("target_character_ids"));
                assertThrows(IllegalArgumentException.class, () -> binding.invoke(PublicBindings.present(
                        new RawJson(StrictJson.canonical(oldAlias)))), "the old province alias must not hide an unmigrated caller");
            }
            var reached = assertThrows(ReachedCurrent.class, () -> binding.invoke(PublicBindings.present(wire)));
            assertEquals(original.method(), reached.method); assertEquals(original, reached.input); assertEquals(1, reached.generation);
            assertThrows(IllegalArgumentException.class, () -> binding.invoke(new PublicBindings.Missing()));
            assertThrows(IllegalArgumentException.class, () -> binding.invoke(new PublicBindings.Null()));
            var extra = StrictJson.parse(wire.bytes(), StrictJson.INPUT_MAX_BYTES);
            assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, extra).put("unowned_argument", true);
            assertThrows(IllegalArgumentException.class, () -> binding.invoke(PublicBindings.present(new RawJson(StrictJson.canonical(extra)))));
        }
        assertEquals(34, calls.get(), "invalid arguments must stop before resolving the actual Root");
        generation.set(2);
        var war = registry.lookup(PublicMethod.QUERY_DECLARABLE_WARS).orElseThrow();
        var afterSwitch = assertThrows(ReachedCurrent.class, () -> war.invoke(PublicBindings.present(ArmyCallCodec.encode(input(PublicMethod.QUERY_DECLARABLE_WARS)))));
        assertEquals(2, afterSwitch.generation, "the retained binding resolves the current owner on every invocation");
        assertEquals(35, calls.get());
    }
    @Test void missingActualSourceCannotInstallAnyThrowOnlyProviderOrBorrowCore() throws Exception {
        var required = new ArrayList<Class<?>>(List.of(ArmyForecastService.class, ArmyDeclarationCollection.class,
                ArmyDeclarationCollectionCodec.class, ArmyWarPublicResultCodec.class, ArmyWarOriginalResultCodec.class, ArmyPublicWire.class,
                ArmyForecastPublicResultCodec.class, RootApplicationSession.class,
                ArmyPrivateScalarControl.class,
                ArmyStrengthsDriverResult.class, org.xar.ck3.control.application.driver.DriverReadHistoryPublisher.class,
                org.xar.ck3.control.application.readiness.NativeReadinessCollector.class));
        required.addAll(RootArmySuppliedPublicProducts.combatImplementations());
        for (Class<?> missing : required) {
            var calls = new AtomicInteger(); var registry = new PublicBindings();
            var contribution = RootArmySuppliedPublicProducts.install(registry, (module,type) -> {
                if (type == missing) throw new java.io.IOException("actual selected service/helper missing");
                return SOURCE;
            }, current(calls, new AtomicInteger(1)));
            assertTrue(registry.coverage().installed().isEmpty());
            assertEquals(34, contribution.gaps().size());
            assertEquals(0, calls.get()); assertFalse(registry.frozen());
        }
    }
    @Test void badRevisionTypesAndDuplicateBindingCannotReachAnyRuntime() {
        var calls = new AtomicInteger(); var registry = new PublicBindings();
        RootArmySuppliedPublicProducts.register(registry, sources(), current(calls, new AtomicInteger(1)));
        assertThrows(IllegalArgumentException.class, () -> RootArmySuppliedPublicProducts.register(
                registry, sources(), current(calls, new AtomicInteger(2))));
        registry.freeze(RootArmySuppliedPublicProducts.METHODS);
        var binding = registry.lookup(PublicMethod.SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1).orElseThrow();
        for (String revision : List.of("true", "7.0", "null")) {
            var wire = new RawJson(("{\"enabled\":false,\"expected_revision\":"+revision+"}")
                    .getBytes(java.nio.charset.StandardCharsets.UTF_8));
            assertThrows(IllegalArgumentException.class, () -> binding.invoke(PublicBindings.present(wire)));
        }
        assertEquals(0, calls.get());
    }
    @Test void collectRequiresOriginalRequestAndExactRevisionBeforeCurrentLookup() {
        var calls = new AtomicInteger(); var registry = new PublicBindings();
        RootArmySuppliedPublicProducts.register(registry, sources(), current(calls, new AtomicInteger(1)));
        registry.freeze(RootArmySuppliedPublicProducts.METHODS);
        var collect = registry.lookup(PublicMethod.COLLECT_DECLARABLE_WARS_RESULT_V1).orElseThrow();
        for (String invalid : List.of("{}", "{\"request_id\":\"original\"}",
                "{\"request_id\":\"original\",\"expected_revision\":null}",
                "{\"request_id\":\"original\",\"expected_revision\":true}",
                "{\"request_id\":\"original\",\"expected_revision\":0.0}",
                "{\"request_id\":\"original\",\"expected_revision\":\"00\"}",
                "{\"request_id\":\"\",\"expected_revision\":0}",
                "{\"request_id\":false,\"expected_revision\":0}"))
            assertThrows(IllegalArgumentException.class, () -> collect.invoke(PublicBindings.present(
                    new RawJson(invalid.getBytes(java.nio.charset.StandardCharsets.UTF_8)))));
        assertEquals(0, calls.get());
        for (String revision : List.of("0", "\"18446744073709551615\"")) {
            var wire = new RawJson(("{\"request_id\":\"original\",\"expected_revision\":" + revision + "}")
                    .getBytes(java.nio.charset.StandardCharsets.UTF_8));
            var reached = assertThrows(ReachedCurrent.class, () -> collect.invoke(PublicBindings.present(wire)));
            assertEquals("original", assertInstanceOf(ArmyCalls.Collect.class, reached.input).requestId());
        }
        assertEquals(2, calls.get());
    }
    @Test void originalSdkEmptyArgumentsReachActualWarStateCodecThroughThePublicMcpBoundary() throws Exception {
        String name="ck3_get_war_state";
        var descriptor=RootOriginalPublicTestInputs.tools().stream().filter(tool->tool.name().equals(name)).findFirst().orElseThrow();
        var calls=new AtomicInteger();var generation=new AtomicInteger(1);var registry=new PublicBindings();
        RootArmySuppliedPublicProducts.register(registry,sources(),current(calls,generation));
        registry.freeze(RootArmySuppliedPublicProducts.METHODS);
        var declaration=new McpCoverage.Declaration(name,SOURCE,1,1,
                "software-only actual Army binding DATA; no Root/source admission",List.of());
        var bindings=new PublicMcpBindings(new McpCoverage.Catalog(List.of(declaration)),List.of(new McpCoverage.Decision(
                name,McpCoverage.Admission.ADMITTED,declaration.source(),
                "original SDK empty arguments through actual Army codec; software-only current callback")));
        if (!(registry.lookup(PublicMethod.WAR_STATE).orElseThrow() instanceof PublicBindings.TypedBinding<?,?> typed))
            throw new IllegalStateException("actual typed WarState binding required");
        PublicMcpNativeAdapter.register(bindings,descriptor,typed);
        var directory=bindings.freezeSoftwareScope();assertEquals(0,calls.get());
        var missing=new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.MISSING,Optional.empty());
        var absent=new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.NULL,Optional.of(
                new RawJson("null".getBytes(java.nio.charset.StandardCharsets.UTF_8))));
        var empty=new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(ArmyCallCodec.encode(new ArmyCalls.Empty())));
        for(var arguments:List.of(missing,absent,empty)) {
            var call=new PublicMcpDirectory.ToolCall(name,arguments,Optional.empty(),new McpCancellation());
            var reached=assertThrows(ReachedCurrent.class,()->directory.invoke(call));
            assertEquals(PublicMethod.WAR_STATE,reached.method);assertEquals(new ArmyCalls.Empty(),reached.input);
            assertEquals(generation.get(),reached.generation);generation.incrementAndGet();
        }
        assertEquals(3,calls.get());
        for(String json:List.of("{\"expected_revision\":null}","{\"unowned_argument\":true}")) {
            var wrong=new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(
                    new RawJson(json.getBytes(java.nio.charset.StandardCharsets.UTF_8))));
            assertThrows(PublicMcpDirectory.ToolFailure.class,()->directory.invoke(new PublicMcpDirectory.ToolCall(
                    name,wrong,Optional.empty(),new McpCancellation())));
        }
        assertEquals(3,calls.get());
    }
    private static ArmyCalls.Call input(PublicMethod method) {
        return switch (method) {
            case WAR_STATE -> new ArmyCalls.Empty();
            case QUERY_DECLARABLE_WARS, RAISE_TROOPS_DEFAULT, CLOSE_WAR_DECLARED_OVERVIEW_V1, CLOSE_WAR_RESULTS_WINDOW_V1 ->
                    new ArmyCalls.Frame(method, REVISION);
            case COLLECT_DECLARABLE_WARS_RESULT_V1 -> new ArmyCalls.Collect(REVISION, "fixture-original-native-request");
            case QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1,
                    QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1, QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2, DECLARE_WAR ->
                    new ArmyCalls.Declaration(method, REVISION, "501-3--1");
            case QUERY_WAR_OCCUPATION_TARGETS_V1, QUERY_WAR_TERMINATION_OPTIONS,
                    QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS, QUERY_WAR_TERMINATION_TERMS, QUERY_WAR_TERMINATION_EXIT_TERMS,
                    ENFORCE_DEMANDS, SURRENDER_WAR, OFFER_WHITE_PEACE -> new ArmyCalls.War(method, REVISION, BigInteger.valueOf(99));
            case QUERY_COMBAT_SIMULATION_INPUTS, QUERY_COMBAT_SIMULATION_INPUTS_V3 -> new ArmyCalls.Combat(method,
                    REVISION, new CombatRequest(11, 12, List.of(0), List.of(4), null), new Missing<>());
            case QUERY_WAR_ENTRY_ASSESSMENTS -> new ArmyCalls.WarEntry(REVISION, List.of(new PositiveId(501)));
            case QUERY_CURRENT_BATTLE_KNIGHT_V1 -> new ArmyCalls.Knight(REVISION,
                    new ArmyRequests.Knight(new PublicUnitId(0), new PositiveId(707), new PositiveId(8),
                            new PositiveId(707), 99, new PositiveId(4), new PositiveId(5), new PositiveId(11),
                            24000, UInt64.positive(BigInteger.valueOf(41)), "native:41"));
            case QUERY_COMBAT_PHASE_EVENT_TRACE_V1 -> new ArmyCalls.CombatId(method, REVISION, new FullId(5));
            case QUERY_ARMY_STRENGTHS -> new ArmyCalls.Strengths(REVISION, List.of(new PublicUnitId(0)),
                    new Missing<>(), new Missing<>(), new Missing<>());
            case SUBMIT_CALL_ALLY_TO_WAR_PRIVATE_V1 -> new ArmyCalls.CallAlly(REVISION, new FullId(99), new FullId(501));
            case SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1 -> new ArmyCalls.CreateMaa(REVISION, 3, "fixture-maa-one", new Missing<>());
            case MOVE_ARMY -> new ArmyCalls.Move(REVISION, new PublicUnitId(0), new PositiveId(11));
            case START_ASSAULT, STOP_ASSAULT -> new ArmyCalls.Siege(method, REVISION, new PositiveId(22));
            case DISBAND_ARMY -> new ArmyCalls.Unit(method, REVISION, new PublicUnitId(0));
            case HIRE_MERCENARY_V1, HIRE_HOLY_ORDER_V1 -> new ArmyCalls.Hire(method, REVISION, new HireId(3));
            case ASSIGN_ARMY_COMMANDER_V1 -> new ArmyCalls.AssignCommander(REVISION, new PublicUnitId(0), new PublicUnitId(707));
            case SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1 -> new ArmyCalls.Sampling(REVISION, false);
            default -> throw new IllegalArgumentException("outside the independent supplied Army fixture roster");
        };
    }
}
