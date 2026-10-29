package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;

final class PublicBindingsTest {
    record Query(BigInteger expectedRevision) { }
    record Result(BigInteger expectedRevision, boolean observed) { }
    private static RawJson raw(String json) { return new RawJson(json.getBytes(StandardCharsets.UTF_8)); }
    private static PublicRoutes.Target target() {
        return new PublicRoutes.Target("org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindingsTest",
                "observe", new ExactRef("fixture-source.java", 1, "0".repeat(64)));
    }
    private static Query decode(PublicBindings.Arguments input) {
        if (!(input instanceof PublicBindings.Value value)) throw new IllegalArgumentException("named argument object required");
        var object = RegistryJson.object(value.original());
        RegistryJson.keys(object, Set.of("expected_revision"));
        return new Query(RegistryJson.integer(RegistryJson.field(object, "expected_revision"), BigInteger.ONE, null));
    }
    private static RawJson encode(Result result) {
        return raw("{\"expected_revision\":" + result.expectedRevision() + ",\"observed\":" + result.observed() + "}");
    }
    private static PublicBindings.TypedBinding<Query,Result> install(PublicBindings registry, AtomicInteger calls) {
        return registry.register(PublicMethod.QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1, Query.class, Result.class,
                query -> { calls.incrementAndGet(); return new Result(query.expectedRevision(), true); },
                PublicBindingsTest::decode, PublicBindingsTest::encode, target(), PublicRoutes.Status.DELEGATED,
                "software typed boundary; no native admission");
    }
    @Test void inventoryDeclarationsNeverBecomeExecutableBindings() {
        PublicBindings registry = new PublicBindings();
        assertEquals(240, registry.inventory().size());
        assertEquals(0, registry.coverage().installed().size());
        assertEquals(238, registry.coverage().unimplemented().size());
        assertEquals(2, registry.coverage().retired().size());
        assertTrue(registry.lookup(PublicMethod.QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1).isEmpty());
        assertThrows(IllegalArgumentException.class, () -> registry.freeze(Set.of(PublicMethod.QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1)));
        assertFalse(registry.frozen());
    }
    @Test void rootFreezeRequiredEvenWhenCallerRetainsTypedRoute() throws Exception {
        PublicBindings registry = new PublicBindings(); AtomicInteger calls = new AtomicInteger();
        var binding = install(registry, calls);
        assertThrows(IllegalArgumentException.class, () -> binding.route().invoke(new Query(BigInteger.ONE)));
        assertEquals(0, calls.get());
        registry.freeze(Set.of(PublicMethod.QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1));
        assertEquals(new Result(BigInteger.ONE, true), binding.invokeTyped(new Query(BigInteger.ONE)));
        assertEquals(1, calls.get());
        assertThrows(IllegalArgumentException.class, () -> install(registry, calls));
    }
    @Test void exactArgumentsValidateBeforeHandlerAndRoundTripLargeIntegers() throws Exception {
        PublicBindings registry = new PublicBindings(); AtomicInteger calls = new AtomicInteger();
        var binding = install(registry, calls); registry.freeze(Set.of(binding.info().method()));
        for (String invalid : new String[] { "{}", "{\"expected_revision\":true}", "{\"expected_revision\":1.0}",
                "{\"expected_revision\":null}", "{\"expected_revision\":1,\"extra\":2}", "[]", "\"x\"" }) {
            assertThrows(IllegalArgumentException.class, () -> binding.invoke(PublicBindings.present(raw(invalid))));
        }
        assertThrows(IllegalArgumentException.class, () -> binding.invoke(new PublicBindings.Missing()));
        assertThrows(IllegalArgumentException.class, () -> binding.invoke(new PublicBindings.Null()));
        assertEquals(0, calls.get());
        String integer = "184467440737095516160001";
        RawJson output = registry.lookup(binding.info().method()).orElseThrow()
                .invoke(PublicBindings.present(raw("{\"expected_revision\":" + integer + "}")));
        var parsed = RegistryJson.object(output);
        assertEquals(new BigInteger(integer), RegistryJson.integer(parsed.get("expected_revision"), BigInteger.ONE, null));
        assertTrue(RegistryJson.bool(parsed.get("observed")));
        assertEquals(1, calls.get());
    }
    @Test void explicitNullMissingAndEmptyObjectAreThreeBranches() {
        assertInstanceOf(PublicBindings.Null.class, PublicBindings.present(raw(" \n null \t")));
        assertInstanceOf(PublicBindings.Missing.class, new PublicBindings.Missing());
        assertInstanceOf(PublicBindings.Value.class, PublicBindings.present(raw("{}")));
        assertThrows(IllegalArgumentException.class, () -> new PublicBindings.Value(raw("null")));
        assertThrows(IllegalArgumentException.class, () -> raw("{\"expected_revision\":1,\"expected_revision\":1}"));
    }
    @Test void retiredAndDuplicateRoutesCannotRegister() {
        PublicBindings registry = new PublicBindings(); AtomicInteger calls = new AtomicInteger(); install(registry, calls);
        assertThrows(IllegalArgumentException.class, () -> install(registry, calls));
        assertThrows(IllegalArgumentException.class, () -> registry.register(PublicMethod.AUTO_NONWAR_TURN,
                Query.class, Result.class, query -> new Result(query.expectedRevision(), true),
                PublicBindingsTest::decode, PublicBindingsTest::encode, target(), PublicRoutes.Status.IMPLEMENTED, "retired"));
        assertEquals(1, registry.coverage().installed().size());
    }
    @Test void typedBoundaryRefusesNullHandlerAndEncoderResults() {
        PublicBindings registry = new PublicBindings();
        var binding = registry.register(PublicMethod.QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1, Query.class, Result.class,
                query -> null, PublicBindingsTest::decode, result -> null, target(), PublicRoutes.Status.IMPLEMENTED, "test null refusal");
        registry.freeze(Set.of(binding.info().method()));
        assertThrows(NullPointerException.class, () -> binding.invokeTyped(new Query(BigInteger.ONE)));
        assertThrows(NullPointerException.class, () -> binding.encode(new Result(BigInteger.ONE, true)));
    }
}

