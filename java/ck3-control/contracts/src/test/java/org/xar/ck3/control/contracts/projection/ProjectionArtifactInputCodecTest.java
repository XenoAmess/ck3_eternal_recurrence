package org.xar.ck3.control.contracts.projection;

import java.nio.file.Path;
import java.time.Instant;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.build.ControlBuild;
import static org.xar.ck3.control.build.ProjectionArtifactAuthority.*;
import static org.xar.ck3.control.contracts.projection.ProjectionArtifactInputContract.fileRef;
import static org.junit.jupiter.api.Assertions.*;

class ProjectionArtifactInputCodecTest {
    private static Path path(String name) { return Path.of(name).toAbsolutePath().normalize(); }
    private static ExactRef ref(String name) { return new ExactRef(path(name).toString(), 1, "a".repeat(64)); }
    private static ProcessIdentity process() { return new ProcessIdentity(42, "18446744073709551615", path("java.exe")); }
    private static Scope scope() {
        return new Scope("scope-1", "owner-1", "fixture-machine", process(), InputOperation.MILITARY_COMBAT_ROLES_NORMALIZE,
                path("input-slot"), path("lease.json"), StrictJson.MAX_SAFE_INTEGER, Instant.parse("2026-10-23T00:00:00Z"), Instant.parse("2026-10-23T00:01:00Z"),
                fileRef(ref("sources.json")), fileRef(ref("producer.jar")), fileRef(ref("build.json")), fileRef(ref("runtime.json")), "fixture.Producer");
    }
    @Test void exactScopeLeaseAndDecimalKernelIdentityRoundTripWithoutAJsonNumberConversion() {
        var scope = scope(); assertEquals(scope, ProjectionArtifactInputCodec.decodeScope(ProjectionArtifactInputCodec.encodeScope(scope)));
        var lease = new Lease(fileRef(ref("scope.json")), process(), scope.issuedAtUtc(), scope.expiresAtUtc(), Purpose.FULL);
        assertEquals(lease, ProjectionArtifactInputCodec.decodeLease(ProjectionArtifactInputCodec.encodeLease(lease)));
        var encoded = StrictJson.object(StrictJson.parse(ProjectionArtifactInputCodec.encodeScope(scope)), java.util.Set.of("schema", "scope_id", "owner_session_id", "machine_id", "owner_process", "operation", "input_root", "lease_path", "max_input_bytes", "issued_at_utc", "expires_at_utc", "source_snapshot_ref", "producer_artifact_ref", "build_receipt_ref", "runtime_binding_ref", "producer_class"));
        assertEquals("18446744073709551615", encoded.path("owner_process").path("creation_filetime").textValue());
        // The four declared event evidence/UI operations are part of the closed inventory.
        assertEquals(155, ProjectionOperation.values().length);
        assertEquals(8_388_608, ProjectionJson.MAX_BYTES); assertEquals(8_392_704, ProjectionWire.MAX_ENVELOPE_BYTES);
    }
    @Test void scopeBudgetAndNativeIdentitiesRejectBooleanDecimalStringNullAndAliasedFields() {
        var original = ProjectionArtifactInputCodec.scope(scope());
        for (String value : new String[]{"true", "1.0", "1e0", "\"1\"", "null", "0", "9007199254740992"}) {
            String changed = new String(ProjectionArtifactInputCodec.encodeScope(scope()), java.nio.charset.StandardCharsets.UTF_8)
                    .replace("\"max_input_bytes\":9007199254740991", "\"max_input_bytes\":" + value);
            assertThrows(IllegalArgumentException.class, () -> ProjectionArtifactInputCodec.decodeScope(changed.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        }
        var extra = original.deepCopy(); extra.put("budget", 1);
        assertThrows(IllegalArgumentException.class, () -> ProjectionArtifactInputCodec.decodeScope(StrictJson.canonical(extra, 65_536)));
        var wrongOp = original.deepCopy(); wrongOp.put("operation", "warcash-evaluate");
        assertThrows(IllegalArgumentException.class, () -> ProjectionArtifactInputCodec.decodeScope(StrictJson.canonical(wrongOp, 65_536)));
        assertThrows(IllegalArgumentException.class, () -> new ProcessIdentity(1, "01", path("java.exe")));
        assertThrows(IllegalArgumentException.class, () -> new ProcessIdentity(1, "18446744073709551616", path("java.exe")));
    }
    @Test void claimIsNotAuthorityAndFullPurposeIsTheOnlyLeaseBranch() {
        var row = StrictJson.object(); row.set("input_ref", ref("payload.json").toJson()); row.set("lease_ref", ref("lease.json").toJson());
        assertEquals(new ProjectionArtifactInputRef(ref("payload.json"), ref("lease.json")), ProjectionArtifactInputRef.fromJson(row));
        row.set("input", row.remove("input_ref"));
        assertThrows(IllegalArgumentException.class, () -> ProjectionArtifactInputRef.fromJson(row));
        var lease = new Lease(fileRef(ref("scope.json")), process(), scope().issuedAtUtc(), scope().expiresAtUtc(), Purpose.FULL);
        var raw = new String(ProjectionArtifactInputCodec.encodeLease(lease), java.nio.charset.StandardCharsets.UTF_8).replace("\"full\"", "\"capture\"");
        assertThrows(IllegalArgumentException.class, () -> ProjectionArtifactInputCodec.decodeLease(raw.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }
    @Test void disabledContextKeepsAnExplicitNullAndOriginalContextAndCallContractsStaySeparate() {
        var context = new Context("fixture-machine", Instant.parse("2026-10-23T00:00:00Z"), Optional.empty());
        var encoded = StrictJson.parse(ProjectionArtifactInputCodec.encodeContext(context));
        assertEquals(4, encoded.size()); assertTrue(encoded.has("artifact_inputs")); assertTrue(encoded.get("artifact_inputs").isNull());
        assertEquals(CONTEXT_SCHEMA, encoded.path("schema").textValue());
        assertEquals(context, ProjectionArtifactInputCodec.decodeContext(ProjectionArtifactInputCodec.encodeContext(context)));
        assertThrows(IllegalArgumentException.class, () -> new Context("unknown", context.observedAtUtc(), Optional.empty()));
        assertTrue(ProjectionHostContext.empty().artifactInputs().isEmpty());
        assertTrue(new ProjectionHostContext(Optional.empty()).artifactInputs().isEmpty());
    }
}
