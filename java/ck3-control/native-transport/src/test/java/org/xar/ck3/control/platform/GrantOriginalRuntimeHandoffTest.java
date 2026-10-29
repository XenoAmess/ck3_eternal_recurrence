package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
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

/** The production archived encoder and decoder are exercised as DATA, without inventing an owned child. */
final class GrantOriginalRuntimeHandoffTest {
    private static final String MACHINE = "source-fixture-machine-001";
    @TempDir Path temporary;
    private record Fixture(Path store, List<String> arguments, List<ExactRef> sources, byte[] original) { }
    private Fixture original() throws Exception {
        String repository = System.getProperty("xar.repository.root");
        if (repository == null || repository.isBlank())
            throw new IllegalStateException("Actual retained original repository is mandatory");
        Path python = Path.of(repository).toRealPath().resolve("ck3_autonomous_player");
        Path executable = temporary.resolve("python.exe");
        Files.writeString(executable, "software DATA source, never executed and never an OwnedStdio");
        var sources = new ArrayList<ExactRef>(); sources.add(ref(executable));
        for (String name : List.of("mcp_server.py", "src/xar_autoplayer/bridge/mcp_server.py",
                "src/xar_autoplayer/bridge/native_driver.py", "src/xar_autoplayer/bridge/grant_title_picker_v1.py",
                "src/xar_autoplayer/bridge/ingame_decisions_open_contract.py", "src/xar_autoplayer/bridge/nonwar_private_build.py",
                "src/xar_autoplayer/bridge/version_identity.py", "src/xar_autoplayer/bridge/service.py",
                "src/xar_autoplayer/bridge/driver.py")) sources.add(ref(python.resolve(name)));
        Path state = temporary.resolve("retained-original-state");
        var args = List.of("-I", "-B", python.resolve("mcp_server.py").toString(), "--driver", "native-headless",
                "--state-dir", state.toString());
        Path store = state.resolve("native-session/grant-title-picker-actions");
        var observed = new WindowsJobProcess.RetirementObservation(new WindowsJobProcess.ProcessIdentity(
                4294967295L, "18446744073709551609", executable.toString()), "f".repeat(64), MACHINE,
                "2026-10-24T08:00:00Z", 4294967295L,
                new WindowsJobProcess.Accounting(9007199254740993L, 0, Long.MAX_VALUE, WindowsJobProcess.REQUIRED_FLAGS));
        return new Fixture(store, args, List.copyOf(sources), WindowsOriginalRuntimeHandoff.encodeObservation(
                store, sources, temporary, args, observed));
    }
    private static ExactRef ref(Path path) throws Exception {
        byte[] bytes = Files.readAllBytes(path);
        return new ExactRef(path.toString(), bytes.length,
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    }
    private static OriginalRuntimeHandoffObservation.Data decode(Fixture value) throws IOException {
        return OriginalRuntimeHandoffObservation.decode(Scope.GRANT, value.original(), value.store(), MACHINE, value.sources());
    }
    @Test void actualSourceClosureAndProductionArchivedEncoderRoundTripGrantWithoutCreatingAuthority() throws Exception {
        Fixture f = original(); var data = decode(f);
        assertEquals(f.store().toString(), data.originalStore()); assertEquals(f.sources(), data.originalEvidence());
        assertEquals("18446744073709551609", data.creationFiletimeDecimal());
        assertEquals("4294967295", data.pidDecimal()); assertEquals("4294967295", data.exitCodeDecimal());
        var mapper = ControlBuild.strictMapper();
        assertEquals(data, OriginalRuntimeHandoffObservation.decode(Scope.GRANT,
                mapper.writeValueAsBytes(mapper.readTree(f.original())), f.store(), MACHINE, f.sources()));
        assertFalse(Files.exists(f.store()), "Archive replay must not inspect/create the current store");
        for (Scope other : List.of(Scope.RELIC, Scope.HOLY_CREATION))
            assertThrows(IOException.class, () -> OriginalRuntimeHandoffObservation.decode(other,
                    f.original(), f.store(), MACHINE, f.sources()));
    }
    @Test void everyRequiredOriginalRejectsMissingChangedAliasedOrDuplicateSourceAndWrongLaunch() throws Exception {
        Fixture f = original(); Path executable = Path.of(f.sources().getFirst().path());
        for (int i = 1; i < f.sources().size(); i++) {
            var missing = new ArrayList<>(f.sources()); missing.remove(i);
            assertThrows(IOException.class, () -> WindowsOriginalRuntimeHandoff.originalStore(
                    Scope.GRANT, f.arguments(), executable, missing));
            var changed = new ArrayList<>(f.sources()); ExactRef source = changed.get(i);
            changed.set(i, new ExactRef(source.path(), source.bytes(), "0".repeat(64)));
            assertThrows(IOException.class, () -> WindowsOriginalRuntimeHandoff.originalStore(
                    Scope.GRANT, f.arguments(), executable, changed));
            var alias = new ArrayList<>(f.sources());
            alias.set(i, new ExactRef(temporary.resolve("copied-source-" + i).toString(), source.bytes(), source.sha256()));
            assertThrows(IOException.class, () -> WindowsOriginalRuntimeHandoff.originalStore(
                    Scope.GRANT, f.arguments(), executable, alias));
        }
        var duplicates = new ArrayList<>(f.sources()); duplicates.add(f.sources().getLast());
        assertThrows(IOException.class, () -> WindowsOriginalRuntimeHandoff.originalStore(Scope.GRANT,
                f.arguments(), executable, duplicates));
        for (int index : List.of(0, 1, 2, 3, 4, 5, 6)) {
            var wrong = new ArrayList<>(f.arguments()); wrong.set(index, "unsupported");
            assertThrows(IOException.class, () -> WindowsOriginalRuntimeHandoff.originalStore(Scope.GRANT, wrong, executable, f.sources()));
        }
        assertThrows(IOException.class, () -> OriginalRuntimeHandoffObservation.decode(Scope.GRANT,
                f.original(), f.store().resolveSibling("rite-creation-actions"), MACHINE, f.sources()));
        assertThrows(IOException.class, () -> OriginalRuntimeHandoffObservation.decode(Scope.GRANT,
                f.original(), f.store(), "different-known-machine", f.sources()));
    }
    private static void reject(Fixture f, Consumer<ObjectNode> mutation) throws Exception {
        var mapper = ControlBuild.strictMapper(); ObjectNode n = assertInstanceOf(ObjectNode.class, mapper.readTree(f.original()));
        mutation.accept(n);
        assertThrows(IOException.class, () -> OriginalRuntimeHandoffObservation.decode(Scope.GRANT,
                mapper.writeValueAsBytes(n), f.store(), MACHINE, f.sources()));
    }
    @Test void exactRetirementDataRejectsNonRetiredJobMissingFieldsWrongTypesAndUnsafeIdentities() throws Exception {
        Fixture f = original();
        reject(f, n -> n.remove("retirement")); reject(f, n -> n.putNull("original_sources"));
        reject(f, n -> n.put("original_store", true)); reject(f, n -> n.put("scope", "DIRECTORY_EMPTY"));
        reject(f, n -> assertInstanceOf(ObjectNode.class, n.get("retirement")).put("active_processes_decimal", "1"));
        reject(f, n -> assertInstanceOf(ObjectNode.class, n.get("retirement")).put("pid_decimal", 4294967295L));
        reject(f, n -> assertInstanceOf(ObjectNode.class, n.get("retirement")).put("creation_filetime_decimal", "18446744073709551616"));
        reject(f, n -> assertInstanceOf(ObjectNode.class, n.get("retirement")).put("creation_filetime_decimal", "018446744073709551609"));
        reject(f, n -> assertInstanceOf(ObjectNode.class, n.get("retirement")).put("limit_flags", 0));
        reject(f, n -> assertInstanceOf(ObjectNode.class, n.get("retirement")).put("limit_flags", WindowsJobProcess.REQUIRED_FLAGS + 0.0));
        reject(f, n -> assertInstanceOf(ObjectNode.class, n.get("retirement")).put("observed_at_utc", "2026-10-24T08:00:00+00:00"));
        String raw = new String(f.original(), StandardCharsets.UTF_8);
        byte[] duplicate = (raw.substring(0, raw.length() - 1) + ",\"scope\":\"ORIGINAL_OWNED_JOB_RETIRED\"}").getBytes(StandardCharsets.UTF_8);
        assertThrows(IOException.class, () -> OriginalRuntimeHandoffObservation.decode(Scope.GRANT,
                duplicate, f.store(), MACHINE, f.sources()));
        assertThrows(IOException.class, () -> OriginalRuntimeHandoffObservation.decode(Scope.GRANT,
                (raw + " {}").getBytes(StandardCharsets.UTF_8), f.store(), MACHINE, f.sources()));
    }
    @Test void readableEmptyAbsentPendingOrResolvedStoresCannotReplaceActualOriginalOwnedChild() throws Exception {
        var provider = WindowsOriginalRuntimeHandoff.grantOriginalOwnedLaunch(Optional.empty());
        var called = new AtomicInteger();
        Path store = temporary.resolve("native-session/grant-title-picker-actions");
        for (int state = 0; state < 3; state++) {
            if (state == 1) Files.createDirectories(store);
            if (state == 2) {
                Files.writeString(store.resolve("a".repeat(64) + ".claim.json"), "{\"status\":\"claimed_result_unknown_no_retry\"}");
                Files.writeString(store.resolve("a".repeat(64) + ".claim.resolved.json"), "{\"status\":\"original_result_observed\"}");
            }
            var result = provider.withOriginalStore(store, MACHINE, lease -> { called.incrementAndGet(); return 1; });
            var unavailable = assertInstanceOf(OriginalRuntimeHandoffProof.Unavailable.class, result);
            assertEquals(OriginalRuntimeHandoffProof.Reason.ORIGINAL_OWNED_LAUNCH_UNAVAILABLE, unavailable.reason());
            assertTrue(unavailable.originalEvidence().isEmpty());
        }
        assertEquals(0, called.get(), "No census/reducer/INTENT/native callback before actual retirement custody");
        assertEquals("{\"status\":\"claimed_result_unknown_no_retry\"}", Files.readString(store.resolve("a".repeat(64) + ".claim.json")));
        assertThrows(IllegalArgumentException.class, () -> provider.withOriginalStore(Path.of("relative"), MACHINE, lease -> 1));
        assertThrows(IllegalArgumentException.class, () -> provider.withOriginalStore(store, "unknown", lease -> 1));
        assertThrows(NullPointerException.class, () -> WindowsOriginalRuntimeHandoff.grantOriginalOwnedLaunch(null));
    }
}
