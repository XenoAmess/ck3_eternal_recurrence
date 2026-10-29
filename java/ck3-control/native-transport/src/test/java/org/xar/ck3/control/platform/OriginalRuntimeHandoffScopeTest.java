package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.platform.OriginalRuntimeHandoffObservation.Scope;

/** Actual archived encoder to both finite consumers. Software DATA never becomes an OS custody positive. */
final class OriginalRuntimeHandoffScopeTest {
    private static final String MACHINE = "source-fixture-machine-001";
    @TempDir Path temporary;
    private record Fixture(Path store, List<String> arguments, List<ExactRef> evidence, byte[] raw) { }
    private Fixture fixture(Scope scope) throws Exception {
        String repo = System.getProperty("xar.repository.root");
        if (repo == null || repo.isBlank()) throw new IllegalStateException("Actual original repository source property required");
        Path python = Path.of(repo).resolve("ck3_autonomous_player").toAbsolutePath().normalize();
        Path executable = temporary.resolve("python.exe");
        Files.writeString(executable, "software-source-identity-only; not an executable or owned process");
        var refs = new ArrayList<ExactRef>(); refs.add(ref(executable));
        for (String name : List.of("mcp_server.py", "src/xar_autoplayer/bridge/mcp_server.py",
                "src/xar_autoplayer/bridge/native_driver.py", "src/xar_autoplayer/bridge/relic_action_private_transport.py",
                "src/xar_autoplayer/bridge/title_map_navigation_contract.py", "src/xar_autoplayer/bridge/version_identity.py",
                "src/xar_autoplayer/bridge/player_holy_site_relic_permissions_private_transport.py",
                "src/xar_autoplayer/bridge/driver.py", "src/xar_autoplayer/bridge/ingame_ui_contract.py",
                "src/xar_autoplayer/bridge/nonwar_private_build.py", "src/xar_autoplayer/bridge/player_holy_site_private_transport.py"))
            refs.add(ref(python.resolve(name)));
        if (scope == Scope.HOLY_CREATION)
            for (String name : List.of("holy_site_creation_create_once_private_transport.py",
                    "player_holy_site_creation_context_private_transport.py"))
                refs.add(ref(python.resolve("src/xar_autoplayer/bridge/" + name)));
        Path state = temporary.resolve("original-state");
        var args = List.of("-I", "-B", python.resolve("mcp_server.py").toString(), "--driver", "native-headless",
                "--state-dir", state.toString());
        Path store = state.resolve("native-session").resolve(scope == Scope.RELIC
                ? "holy-site-relic-action-intents" : "holy-site-creation-create-once-intents");
        // Constructor validates DATA values. No OwnedStdio, RetiredCustody or Lease is created here.
        var data = new WindowsJobProcess.RetirementObservation(new WindowsJobProcess.ProcessIdentity(
                4294967295L, "18446744073709551609", executable.toString()), "c".repeat(64), MACHINE,
                "2026-10-24T04:00:00Z", 4294967295L,
                new WindowsJobProcess.Accounting(9007199254740993L, 0, Long.MAX_VALUE, WindowsJobProcess.REQUIRED_FLAGS));
        byte[] raw = WindowsOriginalRuntimeHandoff.encodeObservation(store, refs, temporary, args, data);
        return new Fixture(store, args, List.copyOf(refs), raw);
    }
    private static ExactRef ref(Path path) throws Exception {
        byte[] raw = Files.readAllBytes(path);
        return new ExactRef(path.toString(), raw.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
    }
    private static OriginalRuntimeHandoffObservation.Data decode(Scope scope, Fixture f) throws IOException {
        return OriginalRuntimeHandoffObservation.decode(scope, f.raw(), f.store(), MACHINE, f.evidence());
    }
    @Test void actualProducerRoundTripsBothIndependentScopesAndAllWideIdentitiesExactly() throws Exception {
        for (Scope scope : List.of(Scope.RELIC, Scope.HOLY_CREATION)) {
            Fixture f = fixture(scope);
            var actual = decode(scope, f);
            assertEquals(f.store().toString(), actual.originalStore());
            assertEquals(f.evidence(), actual.originalEvidence());
            assertEquals("18446744073709551609", actual.creationFiletimeDecimal());
            assertEquals("4294967295", actual.pidDecimal());
            assertEquals("4294967295", actual.exitCodeDecimal());
            var mapper = ControlBuild.strictMapper();
            var original = mapper.readTree(f.raw());
            var reencoded = mapper.writeValueAsBytes(original);
            assertEquals(actual, OriginalRuntimeHandoffObservation.decode(scope, reencoded, f.store(), MACHINE, f.evidence()));
            assertEquals(actual.creationFiletimeDecimal(), mapper.readTree(mapper.writeValueAsBytes(actual))
                    .get("creation_filetime_decimal").textValue());
            assertFalse(Files.exists(f.store()), "DATA decode must not inspect or create a live store");
        }
    }
    private static void reject(Scope scope, Fixture f, Consumer<ObjectNode> mutation) throws Exception {
        var mapper = ControlBuild.strictMapper(); ObjectNode root = assertInstanceOf(ObjectNode.class, mapper.readTree(f.raw()));
        mutation.accept(root);
        assertThrows(IOException.class, () -> OriginalRuntimeHandoffObservation.decode(scope,
                mapper.writeValueAsBytes(root), f.store(), MACHINE, f.evidence()));
    }
    @Test void wrongScopeMachineStoreAndAnyMissingChangedProducerSourceReject() throws Exception {
        for (Scope scope : List.of(Scope.RELIC, Scope.HOLY_CREATION)) {
            Fixture f = fixture(scope);
            assertThrows(IOException.class, () -> OriginalRuntimeHandoffObservation.decode(scope, f.raw(),
                    f.store().resolveSibling("rite-creation-actions"), MACHINE, f.evidence()));
            assertThrows(IOException.class, () -> OriginalRuntimeHandoffObservation.decode(scope, f.raw(),
                    f.store(), "different-known-machine", f.evidence()));
            Scope other = scope == Scope.RELIC ? Scope.HOLY_CREATION : Scope.RELIC;
            assertThrows(IOException.class, () -> OriginalRuntimeHandoffObservation.decode(other, f.raw(),
                    f.store(), MACHINE, f.evidence()));
            var missing = new ArrayList<>(f.evidence()); missing.remove(4);
            assertThrows(IOException.class, () -> WindowsOriginalRuntimeHandoff.originalStore(scope, f.arguments(),
                    Path.of(f.evidence().get(0).path()), missing));
            var changed = new ArrayList<>(f.evidence());
            ExactRef original = changed.get(4); changed.set(4, new ExactRef(original.path(), original.bytes(), "0".repeat(64)));
            assertThrows(IOException.class, () -> WindowsOriginalRuntimeHandoff.originalStore(scope, f.arguments(),
                    Path.of(f.evidence().get(0).path()), changed));
            var duplicate = new ArrayList<>(f.evidence()); duplicate.add(f.evidence().get(4));
            assertThrows(IOException.class, () -> WindowsOriginalRuntimeHandoff.originalStore(scope, f.arguments(),
                    Path.of(f.evidence().get(0).path()), duplicate));
            var foreignState = new ArrayList<>(f.arguments()); foreignState.set(6, "relative-state");
            assertThrows(IOException.class, () -> WindowsOriginalRuntimeHandoff.originalStore(scope, foreignState,
                    Path.of(f.evidence().get(0).path()), f.evidence()));
        }
    }
    @Test void strictArchivedDataRejectsMissingNullableWrongTypeDuplicateTrailingAndNonRetiredStates() throws Exception {
        Fixture f = fixture(Scope.RELIC); Scope scope = Scope.RELIC;
        reject(scope, f, root -> root.put("bridge_pid", 50688));
        reject(scope, f, root -> root.remove("original_sources"));
        reject(scope, f, root -> root.putNull("retirement"));
        reject(scope, f, root -> root.put("scope", "DIRECTORY_READABLE"));
        reject(scope, f, root -> assertInstanceOf(ObjectNode.class, root.get("retirement")).put("active_processes_decimal", "1"));
        reject(scope, f, root -> assertInstanceOf(ObjectNode.class, root.get("retirement")).put("pid_decimal", true));
        reject(scope, f, root -> assertInstanceOf(ObjectNode.class, root.get("retirement")).put("creation_filetime_decimal", new BigInteger("18446744073709551609")));
        reject(scope, f, root -> assertInstanceOf(ObjectNode.class, root.get("retirement")).put("creation_filetime_decimal", "018446744073709551609"));
        reject(scope, f, root -> assertInstanceOf(ObjectNode.class, root.get("retirement")).put("creation_filetime_decimal", "18446744073709551616"));
        reject(scope, f, root -> assertInstanceOf(ObjectNode.class, root.get("retirement")).put("limit_flags", 0));
        reject(scope, f, root -> assertInstanceOf(ObjectNode.class, root.get("retirement")).put("limit_flags", 8704.0));
        reject(scope, f, root -> assertInstanceOf(ObjectNode.class, root.get("retirement")).put("observed_at_utc", "2026-10-24T04:00:00+00:00"));
        reject(scope, f, root -> assertInstanceOf(ObjectNode.class, root.get("retirement")).put("observed_at_utc", "2026-10-24T04:00:00.000Z"));
        reject(scope, f, root -> assertInstanceOf(ObjectNode.class, root.get("retirement")).put("observed_at_utc", "broken"));
        reject(scope, f, root -> assertInstanceOf(ObjectNode.class, root.get("retirement")).put("memory_limit_bytes_decimal", "2"));
        String text = new String(f.raw(), java.nio.charset.StandardCharsets.UTF_8);
        byte[] duplicate = (text.substring(0, text.length() - 1) + ",\"scope\":\"ORIGINAL_OWNED_JOB_RETIRED\"}")
                .getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IOException.class, () -> OriginalRuntimeHandoffObservation.decode(scope, duplicate, f.store(), MACHINE, f.evidence()));
        byte[] trailing = (text + " {}").getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IOException.class, () -> OriginalRuntimeHandoffObservation.decode(scope, trailing, f.store(), MACHINE, f.evidence()));
    }
    @Test void realMissingOriginalProviderNeverCallsWholeCensusOrCommitForEitherOldStore() throws Exception {
        for (Scope scope : List.of(Scope.RELIC, Scope.HOLY_CREATION)) {
            Path store = Files.createDirectories(temporary.resolve("native-session").resolve(scope == Scope.RELIC
                    ? "holy-site-relic-action-intents" : "holy-site-creation-create-once-intents"));
            Path pending = store.resolve("a".repeat(64) + ".pending.json");
            byte[] unknown = "{\"automatic_retry\":false,\"business_outcome_observed\":false}"
                    .getBytes(java.nio.charset.StandardCharsets.UTF_8);
            Files.write(pending, unknown);
            var provider = scope == Scope.RELIC ? WindowsOriginalRuntimeHandoff.relicOriginalOwnedLaunch(Optional.empty())
                    : WindowsOriginalRuntimeHandoff.holyCreationOriginalOwnedLaunch(Optional.empty());
            var calls = new AtomicInteger();
            var result = provider.withOriginalStore(store, MACHINE, lease -> { calls.incrementAndGet(); return 1; });
            var unavailable = assertInstanceOf(OriginalRuntimeHandoffProof.Unavailable.class, result);
            assertEquals(OriginalRuntimeHandoffProof.Reason.ORIGINAL_OWNED_LAUNCH_UNAVAILABLE, unavailable.reason());
            assertEquals(0, calls.get(), "Cannot census/clear/prepare/commit without actual original ownership");
            assertArrayEquals(unknown, Files.readAllBytes(pending));
            assertInstanceOf(OriginalRuntimeHandoffProof.Unavailable.class, provider.withOriginalStore(
                    store.resolveSibling("never-created-" + scope.name()), MACHINE, lease -> fail("Absent is not proof")));
        }
    }
}
