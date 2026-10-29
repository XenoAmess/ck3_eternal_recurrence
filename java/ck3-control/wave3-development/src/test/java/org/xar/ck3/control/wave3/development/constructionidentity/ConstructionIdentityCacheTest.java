package org.xar.ck3.control.wave3.development.constructionidentity;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.stdioidentity.ProcessIdentityClaimV1;
import org.xar.ck3.control.wave3.development.constructionidentity.ConstructionIdentityPolicy.BeforeDecision;
import org.xar.ck3.control.wave3.development.constructionidentity.ConstructionIdentityPolicy.PinClaim;

class ConstructionIdentityCacheTest {
    @Test
    void originalWmiMicrosecondPredicateMatchesTenSourceFixturesWithoutLosingKernelTicks() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.constructionidentity-golden/v1", golden.path("schema").textValue());
        assertEquals("31f0f776d5b9790f4c4b2c972ddb696d186e53e09a63b1c943c979cd48473da9",
                golden.path("source_refs").get(0).path("sha256").textValue());
        assertTrue(golden.path("synthetic_kernel_claims_not_live_measurement").booleanValue());
        assertEquals(0, golden.path("native_process_reads").intValue());
        assertEquals(10, golden.path("match_cases").size());
        for (JsonNode row : golden.path("match_cases")) {
            var fields = original(row.get("identity")).orElseThrow().fields();
            ProcessIdentityClaimV1 kernel = claim(row.get("kernel"));
            assertEquals(row.path("expected").booleanValue(), ConstructionIdentityPolicy.matchesOriginalProducer(fields, kernel),
                    row.path("name").textValue());
            assertEquals(row.path("kernel").path("creation_filetime_decimal").textValue(), kernel.creationFiletimeDecimal());
        }
    }

    @Test
    void fullOriginalCacheAndTransportConsumerOutcomesMatchPureProposals() throws IOException {
        JsonNode rows = golden().path("read_cases");
        assertEquals(15, rows.size());
        for (JsonNode row : rows) {
            JsonNode expected = row.get("expected");
            Optional<PinClaim> pin = row.path("pin").isNull() ? Optional.empty()
                    : Optional.of(new PinClaim(claim(row.path("pin").get("kernel")), row.path("pin").path("creation_date").textValue()));
            Optional<ProcessIdentityClaimV1> before = optionalClaim(row.get("before"));
            BeforeDecision decision = ConstructionIdentityPolicy.beforeRead(pin, before);
            assertEquals(expected.path("before_decision").textValue(), decision.name(), row.path("name").textValue());
            boolean needsProducer = decision == BeforeDecision.READ_ORIGINAL_PRODUCER;
            assertEquals(needsProducer ? 1 : 0, expected.path("producer_calls").intValue());
            Optional<OriginalProcessIdentity> original = original(row.get("identity"));
            boolean producerThrows = !row.path("producer_error").isNull();
            boolean needsAfter = needsProducer && !producerThrows && before.isPresent() && original.isPresent()
                    && ConstructionIdentityPolicy.matchesOriginalProducer(original.orElseThrow().fields(), before.orElseThrow());
            assertEquals(1 + (needsAfter ? 1 : 0), expected.path("kernel_calls").intValue(), row.path("name").textValue());
            boolean mayRetain = needsAfter && ConstructionIdentityPolicy.mayProposePin(original.orElseThrow().fields(),
                    before.orElseThrow(), optionalClaim(row.get("after"))) && !row.path("slot_only").booleanValue();
            assertEquals(expected.path("pin_learned").booleanValue(), mayRetain, row.path("name").textValue());
            if (decision == BeforeDecision.USE_EXISTING_PIN) {
                String creation = row.path("transport").booleanValue() ? expected.path("result").get(1).textValue()
                        : expected.path("result").path("creation_date").textValue();
                assertEquals(pin.orElseThrow().originalCreationDate(), creation);
            }
        }
    }

    @Test
    void unavailableKernelAlwaysInvokesOriginalProducerAndNeverUsesOrCreatesSyntheticPin() throws IOException {
        AtomicInteger kernelReads = new AtomicInteger();
        AtomicInteger producerReads = new AtomicInteger();
        var retention = new ConstructionProcessIdentityCache.MemoryRetention();
        var cache = new ConstructionProcessIdentityCache(pid -> {
            kernelReads.incrementAndGet();
            throw new IOException("kernel denied");
        }, retention);
        byte[] raw = utf8("{\"pid\":226540,\"creation_date\":\"20261015123736.520398+480\","
                + "\"executable\":\"original image\",\"extra\":{\"float\":1.25,\"null\":null,\"empty\":[]}}");
        var identity = OriginalProcessIdentityJson.parse(raw).orElseThrow();
        ConstructionProcessIdentityCache.OriginalIdentityProducer producer = pid -> {
            producerReads.incrementAndGet();
            return Optional.of(identity);
        };
        for (int index = 0; index < 2; index++) {
            var result = cache.read(226540, producer);
            assertTrue(result instanceof ConstructionProcessIdentityCache.ProducerIdentity);
            assertArrayEquals(raw, ConstructionProcessIdentityCache.encode(result));
        }
        var tuple = ConstructionTransportIdentityReader.read(226540, cache, producer);
        assertEquals("20261015123736.520398+480", tuple.originalCreationDate());
        assertEquals(3, kernelReads.get());
        assertEquals(3, producerReads.get());
        assertTrue(retention.current().isEmpty());
    }

    @Test
    void originalProducerExceptionsAndMissingIdentityAreNotHiddenByFallback() throws IOException {
        var cache = new ConstructionProcessIdentityCache(pid -> { throw new IOException("kernel unknown"); },
                new ConstructionProcessIdentityCache.DisabledRetention());
        IOException failure = new IOException("original WMI error");
        assertSame(failure, assertThrows(IOException.class, () -> cache.read(226540, pid -> { throw failure; })));
        RuntimeException runtime = new RuntimeException("original WMI runtime error");
        assertSame(runtime, assertThrows(RuntimeException.class, () -> cache.read(226540, pid -> { throw runtime; })));
        var absent = cache.read(226540, pid -> Optional.empty());
        assertTrue(absent instanceof ConstructionProcessIdentityCache.NoIdentity);
        assertEquals("null", new String(ConstructionProcessIdentityCache.encode(absent), StandardCharsets.UTF_8));
        assertThrows(ConstructionTransportIdentityReader.IdentityUnavailableException.class,
                () -> ConstructionTransportIdentityReader.read(226540, cache, pid -> Optional.empty()));
    }

    @Test
    void strictPidAndDeclaredProducerFieldsRejectOriginalRawTypeSubstitutesBeforeObservation() {
        for (String token : new String[]{"true", "226540.0", "\"226540\"", "null", "0", "-1", "4294967296"}) {
            assertThrows(ContractViolationException.class,
                    () -> ConstructionTransportIdentityReader.parseSessionPid(utf8(token)), token);
        }
        assertEquals(226540, ConstructionTransportIdentityReader.parseSessionPid(utf8("226540")));
        for (String token : new String[]{"true", "226540.0", "\"226540\""}) {
            assertThrows(ContractViolationException.class,
                    () -> OriginalProcessIdentityJson.parse(utf8("{\"pid\":" + token + "}")), token);
        }
        assertThrows(ContractViolationException.class, () -> OriginalProcessIdentityJson.parse(utf8("{\"creation_date\":true}")));
        assertThrows(ContractViolationException.class, () -> OriginalProcessIdentityJson.parse(utf8("{\"pid\":1,\"pid\":1}")));
        assertThrows(ContractViolationException.class, () -> OriginalProcessIdentityJson.parse(utf8("{} []")));
        AtomicInteger calls = new AtomicInteger();
        var cache = new ConstructionProcessIdentityCache(pid -> { calls.incrementAndGet(); throw new IOException("unavailable"); },
                new ConstructionProcessIdentityCache.MemoryRetention());
        assertThrows(ContractViolationException.class, () -> cache.read(0, pid -> { calls.incrementAndGet(); return Optional.empty(); }));
        assertEquals(0, calls.get());
    }

    @Test
    void originalBytesRemainImmutableAndLegitimateLongCommandLineDoesNotUseMapReceiptLimit() {
        byte[] raw = utf8("{\"pid\":226540,\"creation_date\":\"20261015123736.520398+480\","
                + "\"executable\":\"original image\",\"command_line\":\"" + "大".repeat(30_000) + "\"}");
        assertTrue(raw.length > StrictJson.INPUT_MAX_BYTES);
        OriginalProcessIdentity identity = OriginalProcessIdentityJson.parse(raw).orElseThrow();
        assertArrayEquals(raw, identity.originalUtf8());
        byte[] copy = identity.originalUtf8();
        copy[0] = '[';
        assertEquals('{', identity.originalUtf8()[0]);
        assertTrue(java.util.Arrays.stream(ConstructionProcessIdentityCache.VerifiedPin.class.getDeclaredConstructors())
                .allMatch(constructor -> Modifier.isPrivate(constructor.getModifiers())));
        assertTrue(java.util.Arrays.stream(ConstructionProcessIdentityCache.CachedIdentity.class.getDeclaredConstructors())
                .allMatch(constructor -> Modifier.isPrivate(constructor.getModifiers())));
        assertThrows(ContractViolationException.class,
                () -> OriginalProcessIdentityJson.parse(new byte[OriginalProcessIdentityJson.MAX_ORIGINAL_BYTES + 1]));
    }

    private static Optional<OriginalProcessIdentity> original(JsonNode value) {
        if (value == null || value.isNull()) { return Optional.empty(); }
        ObjectNode copy = (ObjectNode) value.deepCopy();
        JsonNode image = copy.get("executable");
        if (image != null && image.isTextual()) { copy.put("executable", expand(image.textValue())); }
        return OriginalProcessIdentityJson.parse(StrictJson.canonical(copy));
    }
    private static Optional<ProcessIdentityClaimV1> optionalClaim(JsonNode value) {
        return value == null || value.isNull() ? Optional.empty() : Optional.of(claim(value));
    }
    private static ProcessIdentityClaimV1 claim(JsonNode value) {
        return new ProcessIdentityClaimV1(StrictJson.integer(value.get("pid"), 1, 0xffff_ffffL),
                StrictJson.text(value.get("creation_filetime_decimal")), Path.of(expand(StrictJson.text(value.get("executable")))));
    }
    private static String expand(String value) {
        return value.startsWith("$CWD/") ? Path.of("").toAbsolutePath().normalize().resolve(value.substring(5)).toString() : value;
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = ConstructionIdentityCacheTest.class.getResourceAsStream("/constructionidentity/golden.json")) {
            assertNotNull(stream, "original cache and transport consumer capture is mandatory");
            byte[] raw = stream.readAllBytes();
            JsonNode document = StrictJson.parse(raw);
            ConstructionIdentityGoldenCapture.validateOutput(raw, document.path("machine_id").asText());
            return document;
        }
    }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
