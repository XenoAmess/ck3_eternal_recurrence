package org.xar.ck3.control.wave3.runtime.childexports;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.providerchain.OriginReadbackValues.ProcessKey;
import org.xar.ck3.control.wave3.runtime.childexports.ChildExportValues.Export;
import org.xar.ck3.control.wave3.runtime.childexports.ChildExportValues.Packet;
import org.xar.ck3.control.wave3.runtime.childexports.ChildExportValues.ProcessReadbacks;
import org.xar.ck3.control.wave3.runtime.childexports.ChildExportValues.RemoteLocation;
import static org.junit.jupiter.api.Assertions.*;

final class ChildExportCodecTest {
    private static final int CORPUS_MAX_BYTES = 98_304;
    @Test void actualImportedSourceClosureIsRequiredAndPreservesAllMeasuredSources() throws IOException {
        JsonNode root = golden();
        JsonNode provenance = root.get("source_provenance");
        assertNotNull(provenance, "actual import observer evidence required; fixed producer pins are not complete imports");
        assertEquals("xar.ck3.measured-repo-import-closure/v1", provenance.get("schema").textValue());
        assertEquals("repo-python-excluding-interpreter-prefixes/v1", provenance.get("scope").textValue());
        assertEquals(0, StrictJson.integer(provenance.get("initial_repo_sources"), 0, 0));
        long recorded = StrictJson.integer(provenance.get("recorded_repo_sources"), 1, 10_000);
        assertTrue(StrictJson.integer(provenance.get("after_imports_repo_sources"), 1, 10_000) <= recorded);
        assertTrue(StrictJson.integer(provenance.get("after_suite_repo_sources"), 1, 10_000) <= recorded);
        StrictJson.trueValue(provenance.get("source_pre_post_equal"));
        assertTrue(provenance.get("unrecorded_repo_sources").isArray());
        assertEquals(0, provenance.get("unrecorded_repo_sources").size());
        JsonNode sources = root.get("source_refs");
        assertNotNull(sources);
        assertTrue(sources.isArray() && sources.size() >= recorded);
        java.util.HashSet<String> paths = new java.util.HashSet<>();
        for (JsonNode ref : sources) {
            String path = StrictJson.text(ref.get("path"));
            assertTrue(!path.startsWith("/") && !path.contains(":") && !path.contains("..") && path.endsWith(".py"));
            assertTrue(paths.add(path), "actual source references must be unique");
            StrictJson.integer(ref.get("bytes"), 0, 100_000_000);
            assertTrue(StrictJson.text(ref.get("sha256")).matches("[a-f0-9]{64}"));
        }
        assertTrue(paths.contains("ck3_autonomous_player/src/xar_autoplayer/bridge/__init__.py"));
        assertTrue(paths.contains("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"));
        assertTrue(paths.contains("ck3_autonomous_player/src/xar_autoplayer/bridge/native_loaded_provider_origin_v1.py"));
        assertTrue(paths.contains("ck3_autonomous_player/src/xar_autoplayer/bridge/native_loaded_provider_custody_v1.py"));
        assertTrue(paths.contains("tools/g2_saved_campaign/canonical_native_provider_chain_v1.py"));
    }

    @Test void goldenRequiresOriginalSourcesAndExplicitPureCaptureScope() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.java.actual-child-exports-pure-golden/v1", golden.get("schema").textValue());
        assertEquals("xenoamess-full-tower-eb9d2c1186", golden.get("machine_id").textValue());
        StrictJson.utc(golden.get("captured_at_utc").textValue());
        Set<String> sourceDigests = Set.of(
                "54475da0a10dce93fe306880df502e977cd41c056195b3a429bd7465e79a1ef4",
                "f2b80f772ac7d15698791680643d9ec965c46730b92438eff134dd5e8152ecfd",
                "a0a2d667c2b56e105182a7c9ef2a8db992d5039690f801c9fa1323db870bd0c4",
                "0515d6873c07ad114220ed709e9f5d75792fbe1abbeb6e27e5f18b3c84ba6cca");
        assertEquals(4, golden.get("source_files").size());
        for (JsonNode row : golden.get("source_files")) {
            assertTrue(sourceDigests.contains(row.get("sha256").textValue()));
            assertTrue(row.get("bytes").intValue() > 0);
        }
        assertEquals(10, golden.get("expression_ast_sha256").size());
        assertEquals(4_300, golden.get("private_integer_max_decimal_digits").intValue());
        assertTrue(golden.get("scope").textValue().contains("no native"));
    }

    @Test void originalProducerBytesAllRolesAndCountFailuresMatch() throws IOException {
        for (JsonNode sample : golden().get("producer_cases")) {
            ChildRole role = ChildRole.parse(sample.get("role").textValue());
            List<Export> exports = exports(role, sample.get("locations"));
            if (!sample.get("accepted").booleanValue()) {
                assertThrows(ContractViolationException.class, () -> new Packet(role, exports), sample.get("name").textValue());
                continue;
            }
            Packet packet = new Packet(role, exports);
            byte[] actual = ChildExportCodec.encode(packet);
            assertArrayEquals(bytes(sample.get("expected_wire_json").textValue()), actual, sample.get("name").textValue());
            assertTrue(sample.get("consumer_accept").booleanValue());
            assertEquals(packet, ChildExportCodec.decode(role, actual));
            assertEquals(packet, ChildExportCodec.parse(role, ChildExportCodec.toJson(packet)));
        }
    }

    @Test void originalConsumerUsesRawTokensForAllShapeRoleAndLocationFailures() throws IOException {
        int samples = 0;
        for (JsonNode sample : golden().get("consumer_cases")) {
            String wire = sample.get("wire_json").textValue();
            ChildRole role = ChildRole.parse(sample.get("role").textValue());
            if (sample.get("accepted").booleanValue()) {
                assertEquals(2, ChildExportCodec.decode(role, bytes(wire)).exports().size());
            } else {
                assertThrows(ContractViolationException.class, () -> ChildExportCodec.decode(role, bytes(wire)),
                        sample.get("name").textValue());
            }
            if (sample.get("name").textValue().equals("location_float")) {
                assertTrue(wire.contains("501.0"), "float rejection must retain its original raw token");
            }
            samples++;
        }
        assertEquals(22, samples);
    }

    @Test void originalReadbackChecksPidIdentityAfterTheActualReaderStage() throws IOException {
        for (JsonNode sample : golden().get("process_readback_cases")) {
            ChildRole role = ChildRole.parse(sample.get("role").textValue());
            if (sample.get("accepted").booleanValue()) {
                ProcessReadbacks value = ChildExportCodec.parseReadbacks(role, sample.get("keys"));
                assertEquals(role.exportedRoles().size() + 1, value.processes().size());
            } else {
                JsonNode keys = sample.get("keys");
                assertEquals(keys.get(0).get(0), keys.get(1).get(0));
                assertNotEquals(keys.get(0), keys.get(1), "PID reuse rejection is not full-key equality");
                assertThrows(ContractViolationException.class, () -> ChildExportCodec.parseReadbacks(role, keys));
            }
        }
    }

    @Test void originalPrivateJsonAcceptsLargeIntegersWithItsIndependentDigitProfile() throws IOException {
        JsonNode boundaries = golden().get("numeric_boundary_cases");
        assertEquals(6, boundaries.size());
        Set<Integer> expectedDigits = Set.of(1_100, 4_300, 4_301);
        java.util.HashSet<String> seen = new java.util.HashSet<>();
        for (JsonNode sample : boundaries) {
            int digits = sample.get("digits").intValue();
            boolean negative = sample.get("negative").booleanValue();
            assertTrue(expectedDigits.contains(digits));
            assertTrue(seen.add(digits + ":" + negative), "each original numeric/sign boundary must occur once");
            boolean received = digits <= ChildExportCodec.PRIVATE_INTEGER_MAX_DECIMAL_DIGITS;
            assertEquals(received, sample.get("receive_accepted").booleanValue(),
                    "the original JSON integer digit bound excludes its optional minus sign");
            assertEquals(received && !negative, sample.get("accepted").booleanValue(),
                    "the original remote-location guard still rejects every negative integer");
            byte[] raw = bytes(sample.get("wire_json").textValue());
            if (received) {
                JsonNode location = StrictJson.parse(raw, ChildExportCodec.PRIVATE_MESSAGE_MAX_BYTES,
                        StrictJson.NumericProfile.PYTHON_CHILD_EXPORTS_4300)
                        .get("exports").get(0).get("location");
                assertEquals(digits, location.bigIntegerValue().abs().toString().length());
                assertEquals(negative, location.bigIntegerValue().signum() < 0);
                assertNull(sample.get("receive_error_type").textValue());
            } else {
                assertEquals("ValueError", sample.get("receive_error_type").textValue());
                assertThrows(ContractViolationException.class, () -> StrictJson.parse(raw,
                        ChildExportCodec.PRIVATE_MESSAGE_MAX_BYTES,
                        StrictJson.NumericProfile.PYTHON_CHILD_EXPORTS_4300));
            }
            if (sample.get("accepted").booleanValue()) {
                Packet packet = ChildExportCodec.decode(ChildRole.QUEUE, raw);
                assertEquals(sample.get("digits").intValue(), packet.exports().get(0).location().value().toString().length());
                assertArrayEquals(raw, ChildExportCodec.encode(packet));
            } else {
                assertThrows(ContractViolationException.class, () -> ChildExportCodec.decode(ChildRole.QUEUE, raw));
            }
        }
        assertEquals(Set.of("1100:false", "1100:true", "4300:false", "4300:true", "4301:false", "4301:true"), seen);
        RemoteLocation memoryOnly = new RemoteLocation(BigInteger.TEN.pow(ChildExportCodec.PRIVATE_INTEGER_MAX_DECIMAL_DIGITS));
        assertEquals(4_301, memoryOnly.value().toString().length());
        Packet unencodable = new Packet(ChildRole.QUEUE, List.of(new Export(ChildRole.MCP_APP, memoryOnly)));
        assertThrows(ContractViolationException.class, () -> ChildExportCodec.encode(unencodable));
    }

    @Test void packetValuesKeepDuplicateLocationsAndEmptyAppExportsDistinctFromMissingOrNull() {
        RemoteLocation same = new RemoteLocation(BigInteger.valueOf(501));
        Packet owner = new Packet(ChildRole.OWNER,
                List.of(new Export(ChildRole.QUEUE, same), new Export(ChildRole.MCP_APP, same)));
        assertEquals(owner, ChildExportCodec.decode(ChildRole.OWNER, ChildExportCodec.encode(owner)));
        Packet app = new Packet(ChildRole.MCP_APP, List.of());
        assertEquals(app, ChildExportCodec.decode(ChildRole.MCP_APP, ChildExportCodec.encode(app)));
        for (String wire : List.of("{\"kind\":\"actual_child_exports\"}",
                "{\"kind\":\"actual_child_exports\",\"exports\":null}",
                "{\"kind\":\"actual_child_exports\",\"exports\":{}}")) {
            assertThrows(ContractViolationException.class, () -> ChildExportCodec.decode(ChildRole.MCP_APP, bytes(wire)));
        }
    }

    @Test void modelsDetachListsAndRejectNullsInvalidOrderAndInvalidReadbackCount() {
        RemoteLocation location = new RemoteLocation(BigInteger.ONE);
        ArrayList<Export> source = new ArrayList<>(List.of(new Export(ChildRole.MCP_APP, location)));
        Packet packet = new Packet(ChildRole.QUEUE, source); source.clear();
        assertEquals(1, packet.exports().size());
        assertThrows(UnsupportedOperationException.class, () -> packet.exports().clear());
        ProcessKey process = new ProcessKey(BigInteger.ONE, "134368602545256921", "c:/own/python.exe");
        ArrayList<ProcessKey> keys = new ArrayList<>(List.of(process));
        ProcessReadbacks readbacks = new ProcessReadbacks(ChildRole.MCP_APP, keys); keys.clear();
        assertEquals(1, readbacks.processes().size());
        assertThrows(UnsupportedOperationException.class, () -> readbacks.processes().clear());
        assertThrows(ContractViolationException.class, () -> new RemoteLocation(null));
        assertThrows(ContractViolationException.class, () -> new RemoteLocation(BigInteger.ZERO));
        assertThrows(ContractViolationException.class, () -> new RemoteLocation(BigInteger.ONE.negate()));
        assertThrows(ContractViolationException.class, () -> new Packet(ChildRole.QUEUE, null));
        assertThrows(ContractViolationException.class, () -> new Packet(null, List.of()));
        assertThrows(ContractViolationException.class, () -> new Export(null, location));
        assertThrows(ContractViolationException.class, () -> new Export(ChildRole.MCP_APP, null));
        assertThrows(ContractViolationException.class, () -> new Packet(ChildRole.QUEUE, java.util.Collections.singletonList(null)));
        assertThrows(ContractViolationException.class, () -> new Packet(ChildRole.QUEUE,
                List.of(new Export(ChildRole.OWNER, location))));
        assertThrows(ContractViolationException.class, () -> new ProcessReadbacks(ChildRole.QUEUE, List.of(process)));
        assertThrows(ContractViolationException.class,
                () -> new ProcessReadbacks(ChildRole.MCP_APP, java.util.Collections.singletonList(null)));
        assertThrows(ContractViolationException.class, () -> ChildRole.parse("queue"));
        assertThrows(ContractViolationException.class, () -> ChildRole.parse("supervisor"));
    }

    @Test void projectedReadbackStillRejectsWrongTokenTypesBirthEncodingAndMissingKeys() {
        for (String wire : List.of("null", "{}", "[]", "[[true,\"134368602545256921\",\"c:/own/python.exe\"]]",
                "[[71.0,\"134368602545256921\",\"c:/own/python.exe\"]]",
                "[[\"71\",\"134368602545256921\",\"c:/own/python.exe\"]]",
                "[[71,134368602545256921,\"c:/own/python.exe\"]]",
                "[[71,\"0134368602545256921\",\"c:/own/python.exe\"]]",
                "[[71,\"134368602545256921\",\"relative.exe\"]]",
                "[[71,\"134368602545256921\"]]")) {
            assertThrows(ContractViolationException.class,
                    () -> ChildExportCodec.parseReadbacks(ChildRole.MCP_APP, StrictJson.parse(bytes(wire))), wire);
        }
    }

    @Test void rootTokensDuplicateFieldsTrailingContentAndInvalidUtf8AreRejected() {
        for (String wire : List.of("null", "true", "[]", "1", "1.0", "{}",
                "{\"kind\":\"actual_child_exports\",\"kind\":\"actual_child_exports\",\"exports\":[]}",
                "{\"kind\":\"actual_child_exports\",\"exports\":[]} {}")) {
            assertThrows(ContractViolationException.class, () -> ChildExportCodec.decode(ChildRole.MCP_APP, bytes(wire)));
        }
        assertThrows(ContractViolationException.class,
                () -> ChildExportCodec.decode(ChildRole.MCP_APP, new byte[] {(byte) 0xc3, (byte) 0x28}));
        assertThrows(ContractViolationException.class, () -> ChildExportCodec.decode(null,
                ChildExportCodec.encode(new Packet(ChildRole.MCP_APP, List.of()))));
    }

    @Test void privateMessageBudgetIncludesFinalNewlineAndKeepsTheExactBoundary() {
        byte[] raw = ChildExportCodec.encode(new Packet(ChildRole.MCP_APP, List.of()));
        assertEquals('\n', raw[raw.length - 1]);
        String padded = new String(raw, StandardCharsets.UTF_8).stripTrailing()
                + " ".repeat(ChildExportCodec.PRIVATE_MESSAGE_MAX_BYTES - raw.length) + "\n";
        assertEquals(ChildExportCodec.PRIVATE_MESSAGE_MAX_BYTES, bytes(padded).length);
        assertEquals(0, ChildExportCodec.decode(ChildRole.MCP_APP, bytes(padded)).exports().size());
        assertThrows(ContractViolationException.class, () -> ChildExportCodec.decode(ChildRole.MCP_APP, bytes(padded + " ")));
        Packet oversizedInteger = new Packet(ChildRole.QUEUE,
                List.of(new Export(ChildRole.MCP_APP, new RemoteLocation(BigInteger.TEN.pow(16_384)))));
        assertThrows(ContractViolationException.class, () -> ChildExportCodec.encode(oversizedInteger));
    }

    private static List<Export> exports(ChildRole role, JsonNode locations) {
        ArrayList<Export> result = new ArrayList<>();
        for (int index = 0; index < locations.size(); index++) {
            ChildRole entryRole = index < role.exportedRoles().size() ? role.exportedRoles().get(index) : ChildRole.MCP_APP;
            result.add(new Export(entryRole, new RemoteLocation(locations.get(index).bigIntegerValue())));
        }
        return result;
    }

    private static JsonNode golden() throws IOException {
        try (InputStream stream = ChildExportCodecTest.class.getResourceAsStream("/childexports/child-exports-golden.json")) {
            assertNotNull(stream, "committed original producer/consumer golden required; never skip");
            byte[] raw = stream.readNBytes(CORPUS_MAX_BYTES + 1);
            StrictJson.require(raw.length <= CORPUS_MAX_BYTES, "bounded independent child-export corpus required");
            return StrictJson.parse(raw, CORPUS_MAX_BYTES,
                    StrictJson.NumericProfile.PYTHON_CHILD_EXPORTS_4300);
        }
    }

    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
