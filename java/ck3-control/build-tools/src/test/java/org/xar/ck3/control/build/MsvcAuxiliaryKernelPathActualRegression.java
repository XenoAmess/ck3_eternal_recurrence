package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Explicit metadata-only regression of the retained failed build; never starts or terminates a process. */
final class MsvcAuxiliaryKernelPathActualRegression {
    private record Original(MsvcAuxiliaryPolicy.ExecutionBinding binding, MsvcAuxiliaryPolicy.Root root,
            WindowsJobProcess.ProcessIdentity member) { }
    private static Path required(String property) throws IOException {
        String value = System.getProperty(property);
        if (value == null || value.isBlank()) throw new IOException("Actual retained failure input required: " + property);
        Path path = Path.of(value);
        if (!path.isAbsolute()) throw new IOException("Absolute retained failure input required");
        return path;
    }
    private static JsonNode original(Path path, long bytes, String sha256) throws IOException {
        var ref = new ControlBuild.FileRef(path.toString(), bytes, sha256);
        ref.verify();
        JsonNode value = ControlBuild.strictMapper().readTree(Files.readAllBytes(path));
        ref.verify();
        return value;
    }
    private static Original load() throws IOException {
        var mapper = ControlBuild.strictMapper();
        JsonNode terminal = original(required("xar.msvcKernelPath.terminal"), 254432,
                "94804951d005b53910a989b3cd00720a0eabe8bbe5d1aebf4b8c47db31dd2e94");
        JsonNode before = original(required("xar.msvcKernelPath.beforeCleanup"), 1170,
                "ed9a1230e5f05ee4e8fb88273a74639eb4deaba6a25f087aaf96c7771ed37722");
        assertEquals("xenoamess-full-tower-eb9d2c1186", terminal.path("machine_id").textValue());
        assertEquals(terminal.path("machine_id"), before.path("machine_id"));
        assertEquals("RED", terminal.path("status").textValue());
        assertEquals("msvc_auxiliary_cleanup_failed: java.lang.IllegalArgumentException: Same kernel image path and held file required",
                terminal.path("child").path("stop_reason").textValue());
        assertEquals("COMPLETE", before.path("list_state").textValue());
        assertEquals(1, before.path("members").size());
        var row = before.path("members").get(0);
        assertTrue(row.path("in_owned_job").booleanValue());
        assertEquals(258, row.path("wait_zero").intValue());
        var member = mapper.treeToValue(row.path("identity"), WindowsJobProcess.ProcessIdentity.class);
        assertEquals(34092, member.pid());
        assertEquals("134374327516050267", member.creationFiletimeDecimal());
        var binding = mapper.treeToValue(terminal.path("auxiliary_cleanup").path("binding"), MsvcAuxiliaryPolicy.ExecutionBinding.class);
        ObjectNode rootFields = ((ObjectNode) before.path("root")).deepCopy();
        rootFields.remove(List.of("win32_error", "error"));
        var root = mapper.treeToValue(rootFields, MsvcAuxiliaryPolicy.Root.class);
        assertEquals(0, root.waitZero());
        assertEquals(0, root.exitCode());
        assertFalse(MsvcAuxiliaryPolicy.samePath(member.executable(), binding.toolchain().vctip().canonicalPath()));
        return new Original(binding, root, member);
    }
    private static final class Boundary implements MsvcAuxiliaryPolicy.Backend {
        private final Original original;
        private long now;
        private boolean terminated;
        private int closes;
        Boundary(Original original) { this.original = original; }
        @Override public MsvcAuxiliaryPolicy.Root root() { return original.root(); }
        @Override public int active() { return terminated ? 0 : 1; }
        @Override public List<Long> members() { return terminated ? List.of() : List.of(original.member().pid()); }
        @Override public MsvcAuxiliaryPolicy.Member retain(long pid) {
            assertEquals(original.member().pid(), pid);
            return new MsvcAuxiliaryPolicy.Member() {
                @Override public MsvcAuxiliaryPolicy.MemberObservation observe() {
                    return new MsvcAuxiliaryPolicy.MemberObservation(original.member(), original.binding().toolchain().vctip(), true, 258);
                }
                @Override public MsvcAuxiliaryPolicy.Termination terminate74() {
                    assertFalse(terminated); terminated = true;
                    return new MsvcAuxiliaryPolicy.Termination(true, null, null);
                }
                @Override public long waitZero() { return terminated ? 0 : 258; }
                @Override public long exitCode() { return terminated ? 74 : 259; }
                @Override public void close() { closes++; }
            };
        }
        MsvcAuxiliaryPolicy.Outcome finish() {
            Instant utc = Instant.now();
            var budget = new MsvcAuxiliaryPolicy.Budget(10_000_000_000L, utc.plusSeconds(20),
                    () -> now, () -> utc.plusNanos(now), millis -> now += millis * 1_000_000L);
            return MsvcAuxiliaryPolicy.finish(this, original.binding(), budget, () -> { });
        }
    }
    @Test void actualShortKernelPathAndHeldLongImageReachSharedCleanupAndRoundTripWithoutChangingRawIdentity() throws Exception {
        Original original = load();
        try (var held = MsvcAuxiliaryPolicy.retain(original.binding(), Instant.now().plusSeconds(20), () -> { })) {
            held.verify();
            Boundary boundary = new Boundary(original);
            var outcome = boundary.finish();
            assertEquals(MsvcAuxiliaryPolicy.State.FORCED_AUXILIARY_CLEANUP, outcome.state(), outcome.error());
            assertEquals(1, boundary.closes);
            assertEquals(original.member(), outcome.forcedCleanup().getFirst().identity());
            assertEquals(original.binding().toolchain().vctip(), outcome.forcedCleanup().getFirst().image());
            assertEquals(MsvcAuxiliaryPolicy.Tool.VCTIP, outcome.forcedCleanup().getFirst().tool());
            assertEquals(74L, outcome.forcedCleanup().getFirst().actualExitCode().longValue());
            assertEquals(0, outcome.ownedActiveAfter().intValue());
            assertFalse(outcome.failureJobTerminationRequested());
            var mapper = ControlBuild.strictMapper();
            assertEquals(outcome, mapper.readValue(mapper.writeValueAsBytes(outcome), MsvcAuxiliaryPolicy.Outcome.class));
            held.verify();
        }
    }
    @Test void differentCanonicalFileOrHeldFileIdentityCannotUseTheShortPathAsAnAlias() throws Exception {
        Original original = load();
        try (var held = MsvcAuxiliaryPolicy.retain(original.binding(), Instant.now().plusSeconds(20), () -> { })) {
            var image = original.binding().toolchain().vctip();
            assertThrows(IllegalArgumentException.class, () -> new MsvcAuxiliaryPolicy.MemberObservation(
                    original.member(), original.binding().toolchain().mspdbsrv(), true, 258));
            var wrongId = new MsvcAuxiliaryPolicy.Image(image.canonicalPath(), image.volumeSerialDecimal(),
                    original.binding().toolchain().mspdbsrv().fileIdDecimal(), image.bytes(), image.sha256());
            assertThrows(IllegalArgumentException.class, () -> new MsvcAuxiliaryPolicy.MemberObservation(original.member(), wrongId, true, 258));
            assertThrows(IllegalArgumentException.class, () -> new MsvcAuxiliaryPolicy.ForcedCleanup(MsvcAuxiliaryPolicy.Tool.VCTIP,
                    original.member(), wrongId, new MsvcAuxiliaryPolicy.Termination(true, null, null), null, null));
            held.verify();
        }
    }
}
