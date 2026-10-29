package org.xar.ck3.control.g2.m1;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.context.G2CallContextProducer;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;

final class M1RootRequestSupplierTest {
    private static final byte[] ORIGINAL = utf8("{\"decimal\":1.0,\"identity\":18446744073709551615,\"unknown\":null,\"known_empty\":[]}");

    @ParameterizedTest @EnumSource(M1Operation.class)
    void allEightOperationsRemainUnavailableWithoutTheTrueRootProvider(M1Operation operation) {
        var supplier = new M1RootRequestSupplier(new G2CallContextProducer.RootBinding());
        var unavailable = assertInstanceOf(M1RootRequestSupplier.Unavailable.class, supplier.prepare(operation, ORIGINAL));
        assertEquals(G2CallContextProducer.Reason.ROOT_PROVIDER_MISSING, unavailable.sourceFailure().reason());
    }

    @ParameterizedTest @EnumSource(M1Operation.class)
    void rootContextAloneSuppliesSourceAndIdForTheExactOperationPayload(M1Operation operation) {
        var binding = new G2CallContextProducer.RootBinding();
        var captured = new AtomicReference<byte[]>();
        G2Source synthetic = new G2Source("synthetic-m1-test", "2026-10-22T00:00:00Z", "synthetic-unit-provider",
                new ExactRef("synthetic:/retained-native-unit", 1, "a".repeat(64)));
        binding.install((milestone, payload) -> {
            assertEquals(Milestone.M1, milestone); captured.set(payload.bytes());
            return new G2CallContextProducer.Available(new G2CallContextProducer.Context(synthetic,
                    "synthetic-m1-context", G2RetainedNativeSourceProvider.sha256(payload.bytes())));
        });
        var prepared = assertInstanceOf(M1RootRequestSupplier.Prepared.class,
                new M1RootRequestSupplier(binding).prepare(operation, ORIGINAL));
        var request = G2Wire.decodeRequest(G2Wire.encodeRequest(prepared.request()));
        assertSame(synthetic, prepared.request().source()); assertEquals(synthetic, request.source());
        assertEquals("synthetic-m1-context", request.requestId());
        assertArrayEquals(operation.payload(ORIGINAL).bytes(), captured.get());
        assertArrayEquals(captured.get(), request.payload().bytes());
        assertTrue(new String(request.payload().bytes(), StandardCharsets.UTF_8)
                .contains(new String(ORIGINAL, StandardCharsets.UTF_8)));
    }

    @Test void missingNativeOrExeFailureIsPreservedWithoutFallbackOrDomainExecution() {
        for (var reason : new G2CallContextProducer.Reason[] {G2CallContextProducer.Reason.RETAINED_SOURCE_MISSING,
                G2CallContextProducer.Reason.EXACT_BUILD_UNAVAILABLE, G2CallContextProducer.Reason.CURRENT_SESSION_UNAVAILABLE}) {
            var failure = new G2CallContextProducer.Unavailable(reason, "synthetic missing source diagnostic");
            var calls = new AtomicInteger(); var binding = new G2CallContextProducer.RootBinding();
            binding.install((milestone, payload) -> { calls.incrementAndGet(); return failure; });
            var result = assertInstanceOf(M1RootRequestSupplier.Unavailable.class,
                    new M1RootRequestSupplier(binding).prepare(M1Operation.REALM_FEEDBACK, utf8("{}")));
            assertSame(failure, result.sourceFailure()); assertEquals(1, calls.get());
        }
    }

    @Test void sourceContextForDifferentBytesCannotPrepareARequest() {
        G2CallContextProducer.Provider provider = (milestone, payload) -> new G2CallContextProducer.Available(new G2CallContextProducer.Context(
                new G2Source("synthetic-m1-test", "2026-10-22T00:00:00Z", "synthetic-unit-provider",
                        new ExactRef("synthetic:/retained-native-unit", 1, "a".repeat(64))), "synthetic-mismatch", "0".repeat(64)));
        var unavailable = assertInstanceOf(M1RootRequestSupplier.Unavailable.class,
                new M1RootRequestSupplier(provider).prepare(M1Operation.REALM_FEEDBACK, ORIGINAL));
        assertEquals(G2CallContextProducer.Reason.SOURCE_REJECTED, unavailable.sourceFailure().reason());
    }

    @Test void malformedInputAndUnknownOperationsNeverReachTheSourceCapability() {
        var calls = new AtomicInteger(); var binding = new G2CallContextProducer.RootBinding();
        binding.install((milestone, payload) -> { calls.incrementAndGet(); throw new AssertionError("source lookup must not run"); });
        var supplier = new M1RootRequestSupplier(binding);
        for (String raw : new String[] {"null", "[]", "true", "{} {}", "{\"x\":1,\"x\":2}"}) {
            assertThrows(IllegalArgumentException.class, () -> supplier.prepare(M1Operation.REALM_FEEDBACK, utf8(raw)));
        }
        assertThrows(IllegalArgumentException.class, () -> M1Operation.parse("REALM_FEEDBACK"));
        assertEquals(0, calls.get());
    }

    @Test void inputMutationAfterPreparationCannotChangeTheBoundPayload() {
        byte[] raw = utf8("{\"id\":1}"); ProjectionJson payload = M1Operation.SAVED_MEMBERSHIP.payload(raw);
        raw[raw.length - 2] = '2';
        assertTrue(new String(payload.bytes(), StandardCharsets.UTF_8).contains("\"id\":1"));
        assertEquals(M1Operation.SAVED_MEMBERSHIP, M1Operation.parse(M1Operation.SAVED_MEMBERSHIP.wire()));
    }
    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }
}
