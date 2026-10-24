package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Replays the actual C18 admission failure through the shared typed lease reader. */
final class ControlBuildOwnerQuotaTest {
    @TempDir Path temporary;

    private record Fixture(ControlBuild.Config config, ObjectNode original,
            String machineId, Instant authorityAt, Path ownerProof) { }

    @Test void genuineRejectedLeaseRetainsItsActualQuotaAndPassesTheSharedReader() throws Exception {
        Fixture fixture = fixture();
        ObjectNode original = fixture.original();
        JsonNode volume = onlyObject(original, "volumes");
        JsonNode override = onlyObject(original, "quota_overrides");
        assertEquals(13_960_000_000_000L, override.required("max_project_bytes").longValue());
        assertEquals(13_202_768_887_808L, volume.required("current_project_usage_conservative_upper").longValue());
        assertNotEquals(8L << 30, override.required("max_project_bytes").longValue());
        assertEquals(override.required("max_project_bytes"), volume.required("effective_project_quota"));
        JsonNode rejected = ControlBuild.strictMapper().readTree(resource("actual-c18-rejection.stderr.log",
                "656aaad26dd39a9134a14f6f8f2bc75432fdcc6e8370a814dce4d49c6063cd60"));
        assertEquals("xar.java-control.build-rejected/v1", rejected.required("schema").textValue());
        assertEquals("RED", rejected.required("status").textValue());
        assertEquals("IOException: Explicit finite CI quota override required only for an insufficient default quota",
                rejected.required("error").textValue());
        // Only the physical fixture paths are rebound. The genuine machine,
        // owner, chronology, observed volume and 13.96 TB authority stay intact.
        write(fixture, original);
        assertDoesNotThrow(() -> {
            ControlBuild.readLeaseAt(fixture.config(), fixture.machineId(), fixture.authorityAt());
        });
        var decoded = ControlBuild.strictMapper().treeToValue(original, ControlBuild.CapacityRelease.class);
        byte[] encoded = ControlBuild.strictMapper().writeValueAsBytes(decoded);
        assertEquals(decoded, ControlBuild.strictMapper().readValue(encoded, ControlBuild.CapacityRelease.class));
    }

    @Test void theActualReaderStillRejectsCrossedMissingExpiredOrFalseQuotaAuthority() throws Exception {
        Fixture fixture = fixture();
        for (String mode : List.of("missing", "writer", "mismatch", "expired", "deadline", "digest", "unneeded")) {
            ObjectNode changed = fixture.original().deepCopy();
            ObjectNode override = onlyObject(changed, "quota_overrides");
            switch (mode) {
                case "missing" -> changed.set("quota_overrides", ControlBuild.strictMapper().createObjectNode());
                case "writer" -> override.put("task", "/root/another_writer");
                case "mismatch" -> override.put("max_project_bytes", 13_960_000_000_001L);
                case "expired" -> override.put("review_at_utc", fixture.authorityAt().toString());
                case "deadline" -> override.put("review_at_utc",
                        Instant.parse(changed.required("review_at_utc").textValue()).plusSeconds(1).toString());
                case "digest" -> ((ObjectNode) override.required("source_ref")).put("sha256", "0".repeat(64));
                case "unneeded" -> {
                    ObjectNode volume = onlyObject(changed, "volumes");
                    volume.put("current_project_usage_conservative_upper", 1L);
                    volume.put("effective_project_quota", 100L << 30);
                }
                default -> throw new IllegalArgumentException("Exact quota regression case required");
            }
            write(fixture, changed);
            assertThrows(IOException.class, () -> {
                ControlBuild.readLeaseAt(fixture.config(), fixture.machineId(), fixture.authorityAt());
            }, mode);
        }
    }

    @Test void exactSourceProofAndTheActualFreeSpaceAndQuotaFormulasRemainMandatory() throws Exception {
        Fixture fixture = fixture();
        write(fixture, fixture.original());
        Files.writeString(fixture.ownerProof(), "changed actual authority source");
        assertThrows(IOException.class, () -> {
            ControlBuild.readLeaseAt(fixture.config(), fixture.machineId(), fixture.authorityAt());
        });
        Fixture budget = fixture(temporary.resolve("budget-boundary"));
        for (String mode : List.of("quota", "free", "formula", "policy-age")) {
            ObjectNode changed = budget.original().deepCopy();
            ObjectNode volume = onlyObject(changed, "volumes");
            ObjectNode override = onlyObject(changed, "quota_overrides");
            switch (mode) {
                case "quota" -> {
                    long insufficient = Math.addExact(volume.required("current_project_usage_conservative_upper").longValue(),
                            volume.required("this_write_peak").longValue()) - 1;
                    volume.put("effective_project_quota", insufficient);
                    override.put("max_project_bytes", insufficient);
                }
                case "free" -> volume.put("available_bytes", volume.required("required_free").longValue() - 1);
                case "formula" -> volume.put("required_free", volume.required("required_free").longValue() - 1);
                case "policy-age" -> {
                    String later = Instant.parse(changed.required("observed_at_utc").textValue())
                            .plusSeconds(169L * 3600).toString();
                    changed.put("review_at_utc", later);
                    override.put("review_at_utc", later);
                }
                default -> throw new IllegalArgumentException("Exact budget regression case required");
            }
            write(budget, changed);
            Class<? extends Exception> expected = mode.equals("formula")
                    ? IOException.class : IllegalArgumentException.class;
            assertThrows(expected, () -> {
                ControlBuild.readLeaseAt(budget.config(), budget.machineId(), budget.authorityAt());
            }, mode);
        }
    }

    @Test void ownerQuotaUsesTheExistingStrictIntegerContract() throws Exception {
        Fixture fixture = fixture();
        for (String token : List.of("true", "13960000000000.0", "13960000000000e0", "null", "\"13960000000000\"")) {
            ObjectNode changed = fixture.original().deepCopy();
            onlyObject(changed, "quota_overrides").set("max_project_bytes", ControlBuild.strictMapper().readTree(token));
            write(fixture, changed);
            assertThrows(IOException.class, () -> {
                ControlBuild.readLeaseAt(fixture.config(), fixture.machineId(), fixture.authorityAt());
            }, token);
        }
    }

    private Fixture fixture() throws Exception { return fixture(temporary.resolve("real-owner-quota")); }

    private Fixture fixture(Path root) throws Exception {
        Files.createDirectories(root);
        ObjectNode original = assertInstanceOf(ObjectNode.class,
                ControlBuild.strictMapper().readTree(resource("actual-c18-typed-lease.json",
                        "0130b789526c6167eb3264f54c0d5e976ed39be68a0e062d32f9af60f978c880")));
        Path work = Files.createDirectory(root.resolve("work"));
        Path source = Files.createDirectory(root.resolve("source"));
        Path policy = root.resolve("storage-policy.json");
        Files.write(policy, resource("actual-storage-policy.json",
                "ca60e36bef8e59ffafa939689a6ba4106420f20b7c2db19a1199d6408b3131e5"));
        Path proof = root.resolve("actual-owner-financial-proof.json");
        Files.write(proof, resource("actual-owner-financial-proof.json",
                "14e095a5f3f6292c70e55c5fe3126ab1022a6813d0d4dd08727c05061e3b5fee"));
        original.set("approved_output_roots", ControlBuild.strictMapper().createArrayNode()
                .add(work.toString()).add(source.toString()));
        original.put("temporary_root", work.resolve("scratch").toString());
        original.set("policy_ref", ControlBuild.strictMapper().valueToTree(ControlBuild.FileRef.measure(policy)));
        onlyObject(original, "quota_overrides").set("source_ref",
                ControlBuild.strictMapper().valueToTree(ControlBuild.FileRef.measure(proof)));
        Path release = root.resolve("lease.json");
        ControlBuild.Config config = new ControlBuild.Config(source, work, release, "owner-quota-regression",
                original.required("owner_task").textValue(), null, Path.of(System.getProperty("java.home")),
                "3.10.0", 60, ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME, ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
        return new Fixture(config, original, original.required("machine_id").textValue(),
                Instant.parse(original.required("observed_at_utc").textValue()).plusSeconds(1), proof);
    }

    private static ObjectNode onlyObject(ObjectNode root, String key) {
        JsonNode value = root.required(key);
        assertTrue(value.isObject()); assertEquals(1, value.size());
        return assertInstanceOf(ObjectNode.class, value.properties().iterator().next().getValue());
    }

    private static void write(Fixture fixture, ObjectNode value) throws IOException {
        Files.write(fixture.config().capacityRelease(), ControlBuild.strictMapper().writeValueAsBytes(value));
    }

    private static byte[] resource(String name, String expectedSha256) throws Exception {
        try (var stream = ControlBuildOwnerQuotaTest.class.getResourceAsStream("/ownerquota/" + name)) {
            assertNotNull(stream, "Exact original failure resource required: " + name);
            byte[] bytes = stream.readAllBytes();
            assertEquals(expectedSha256, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
            return bytes;
        }
    }
}
