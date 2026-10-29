package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual NTFS producer tests. Minimal basis fixtures grant filesystem scope only, never Root,
 * real recovery, Prepared, SDK, Native, Game, SAVE or continuation qualification. */
final class CampaignScoreJunctionTest {
    @TempDir Path temporary;
    private record Fixture(Path runtime, CampaignScoreJunction.Binding binding, ObjectNode basis, ObjectNode anchor) {
        byte[] basisBytes() { return StrictJson.canonical(basis); }
        CampaignScoreJunction.Prepared prepare() throws IOException {
            return CampaignScoreJunction.prepare(binding, basisBytes(), runtime, Instant.now().plusSeconds(30), () -> { });
        }
    }
    private Fixture fixture(String name) throws IOException {
        assertTrue(com.sun.jna.Platform.isWindows(), "Windows NTFS environment required; absence is a failure, not a skipped pass");
        Path root = Files.createDirectory(temporary.resolve(name));
        Path home = Files.createDirectory(root.resolve("original shared source"));
        Path target = Files.createDirectory(home.resolve("campaign-score"));
        Path runtime = Files.createDirectory(root.resolve("new runtime"));
        Path state = Files.createDirectory(home.resolve("state"));
        Path driver = Files.writeString(Files.createDirectories(state.resolve("native-session")).resolve("driver-state.json"), "{}\n");
        Path save = Files.writeString(Files.createDirectories(state.resolve("profile").resolve("save games")).resolve("checkpoint.ck3"), "fixture\n");
        String machine = WindowsJobProcess.currentMachineId();
        ObjectNode anchor = StrictJson.object(); anchor.put("schema", "xar.ck3.campaign-score-fixed-anchor/v1");
        anchor.put("machine_id", machine); anchor.put("campaign_id", "robert-first30-v20261019");
        anchor.put("founder_character_id", 7); anchor.put("start_date_raw", 100); anchor.put("endpoint_date_raw", 200);
        anchor.put("fixed_across_ruler_and_sdk_changes", true); anchor.put("old_campaign_inputs_copied", 0);
        anchor.put("observed_at_utc", Instant.now().toString());
        Path anchorPath = Files.write(target.resolve("CAMPAIGN-ANCHOR.json"), StrictJson.canonical(anchor));
        var nativeId = CampaignScoreJunction.observeDirectory(target);
        var binding = new CampaignScoreJunction.Binding(runtime.resolve("campaign-score"), target,
                nativeId.fileId(), nativeId.device(), exact(anchorPath));
        ObjectNode basis = StrictJson.object(); basis.put("schema", "xar.current-saved-basis/v1"); basis.put("machine_id", machine);
        var refs = basis.putObject("refs"); refs.set("driver", exact(driver).toJson()); refs.set("save", exact(save).toJson());
        basis.putObject("checkpoint").put("path", save.toString());
        basis.putObject("campaign_goal_anchor").put("origin_character_id", 7);
        basis.putObject("origin").put("start_date_raw", 100).put("target_date_raw", 200);
        return new Fixture(runtime, binding, basis, anchor);
    }
    @Test void realJavaProducerCreatesMountPointAndPreservesOriginalIdentityWithoutCopying() throws Exception {
        var fixture = fixture("actual"); var original = CampaignScoreJunction.observeDirectory(fixture.binding().target());
        var prepared = fixture.prepare(); prepared.requireCurrent();
        assertTrue(Files.isSameFile(fixture.binding().path(), fixture.binding().target()));
        assertEquals(original, CampaignScoreJunction.observeDirectory(fixture.binding().target()));
        assertEquals(fixture.binding(), prepared.receipt().binding());
        assertNotEquals(prepared.receipt().targetIdentity(), prepared.receipt().junctionIdentity());
        assertEquals(prepared.receipt(), CampaignScoreJunction.PreparedReceipt.decode(prepared.bytes()));
        assertEquals(0, prepared.receipt().toJson().get("copied_files").intValue());
        assertEquals(0, prepared.receipt().toJson().get("game_day_credit").intValue());
        assertFalse(prepared.receipt().toJson().get("original_actions_replayed").booleanValue());
        // SharedSourceFiles rejects reparse paths; success here requires the dedicated physical verifier.
        assertThrows(IOException.class, () -> CampaignScoreJunction.observeDirectory(fixture.binding().path()));
    }
    @Test void nativeDirectoryIdentityMatchesOriginalPythonOsStatDecimalDomains() throws Exception {
        var fixture = fixture("original-stat"); var identity = CampaignScoreJunction.observeDirectory(fixture.binding().target());
        String interpreter = System.getProperty("xar.python");
        if (interpreter == null) interpreter = System.getenv("XAR_ORACLE_PYTHON");
        if (interpreter == null) interpreter = "python";
        if (interpreter.isBlank()) throw new IllegalArgumentException("explicit original oracle interpreter must be nonblank");
        Process process = new ProcessBuilder(interpreter, "-B", "-c",
                "import os,sys;s=os.stat(sys.argv[1],follow_symlinks=False);print(str(s.st_ino)+':'+str(s.st_dev))",
                fixture.binding().target().toString()).redirectErrorStream(true).start();
        try {
            if (!process.waitFor(30, TimeUnit.SECONDS)) throw new IOException("original stat oracle timed out");
            byte[] output = process.getInputStream().readNBytes(4097);
            assertTrue(output.length <= 4096); assertEquals(0, process.exitValue());
            assertEquals(identity.fileId() + ":" + identity.device(), new String(output, StandardCharsets.UTF_8).strip());
        } finally { if (process.isAlive()) { process.destroyForcibly(); assertTrue(process.waitFor(30, TimeUnit.SECONDS)); } }
    }
    @Test void createOnlyRejectsAnExistingOrdinaryChildWithoutModifyingIt() throws Exception {
        var fixture = fixture("existing"); Files.createDirectory(fixture.binding().path());
        var original = CampaignScoreJunction.observeDirectory(fixture.binding().path());
        assertThrows(IOException.class, fixture::prepare);
        assertEquals(original, CampaignScoreJunction.observeDirectory(fixture.binding().path()));
    }
    @Test void wrongTargetIdentityRejectsBeforeAnyFilesystemMutation() throws Exception {
        var fixture = fixture("wrong-id"); var binding = fixture.binding();
        var wrong = new CampaignScoreJunction.Binding(binding.path(), binding.target(),
                binding.fileId().equals("1") ? "2" : "1", binding.device(), binding.anchor());
        assertThrows(ContractViolationException.class, () -> CampaignScoreJunction.prepare(wrong, fixture.basisBytes(),
                fixture.runtime(), Instant.now().plusSeconds(30), () -> { }));
        assertFalse(Files.exists(binding.path(), LinkOption.NOFOLLOW_LINKS));
    }
    @Test void anotherSharedStateCannotBeSubstitutedForTheQualifiedDriverSavePair() throws Exception {
        var fixture = fixture("wrong-state"); var second = fixture("other-state");
        assertThrows(ContractViolationException.class, () -> CampaignScoreJunction.prepare(fixture.binding(), second.basisBytes(),
                fixture.runtime(), Instant.now().plusSeconds(30), () -> { }));
        assertFalse(Files.exists(fixture.binding().path(), LinkOption.NOFOLLOW_LINKS));
    }
    @Test void wrongAnchorBusinessFieldsAndIntegerTypesRejectBeforeCreation() throws Exception {
        for (String field : List.of("founder_character_id", "start_date_raw", "endpoint_date_raw", "old_campaign_inputs_copied")) {
            var fixture = fixture("wrong-anchor-" + field); var changed = fixture.anchor().deepCopy(); changed.put(field, true);
            Files.write(Path.of(fixture.binding().anchor().path()), StrictJson.canonical(changed));
            var binding = fixture.binding(); var fresh = new CampaignScoreJunction.Binding(binding.path(), binding.target(),
                    binding.fileId(), binding.device(), exact(Path.of(binding.anchor().path())));
            assertThrows(ContractViolationException.class, () -> CampaignScoreJunction.prepare(fresh, fixture.basisBytes(),
                    fixture.runtime(), Instant.now().plusSeconds(30), () -> { }));
            assertFalse(Files.exists(binding.path(), LinkOption.NOFOLLOW_LINKS));
        }
    }
    @Test void sameBytesAnchorReplacementDoesNotSurviveTheActualPreparedWitness() throws Exception {
        var fixture = fixture("anchor-replaced"); var prepared = fixture.prepare(); Path anchor = Path.of(fixture.binding().anchor().path());
        byte[] raw = Files.readAllBytes(anchor); Files.move(anchor, anchor.resolveSibling("retained-original-anchor.json")); Files.write(anchor, raw);
        assertThrows(IOException.class, prepared::requireCurrent);
    }
    @Test void samePathAndAnchorBytesCannotHideReplacementOfTheTargetDirectory() throws Exception {
        var fixture = fixture("target-replaced"); var prepared = fixture.prepare(); Path target = fixture.binding().target();
        Path retained = target.resolveSibling("retained-original-target"); Files.move(target, retained); Files.createDirectory(target);
        Files.copy(retained.resolve("CAMPAIGN-ANCHOR.json"), target.resolve("CAMPAIGN-ANCHOR.json"));
        assertThrows(ContractViolationException.class, prepared::requireCurrent);
    }
    @Test void failureAfterMutationRetainsTheRealChildAndCannotReplayCreation() throws Exception {
        var fixture = fixture("failed-after-create"); AtomicBoolean reject = new AtomicBoolean(true);
        assertThrows(IOException.class, () -> CampaignScoreJunction.prepare(fixture.binding(), fixture.basisBytes(), fixture.runtime(),
                Instant.now().plusSeconds(30), () -> { if (reject.get() && Files.exists(fixture.binding().path(), LinkOption.NOFOLLOW_LINKS))
                    throw new IllegalStateException("actual post-mutation scope revoked"); }));
        assertTrue(Files.exists(fixture.binding().path(), LinkOption.NOFOLLOW_LINKS)); reject.set(false);
        assertThrows(IOException.class, fixture::prepare);
        assertTrue(Files.isSameFile(fixture.binding().path(), fixture.binding().target()));
    }
    @Test void expiredOrWrongMachineScopeCannotCreateAChild() throws Exception {
        var fixture = fixture("expired");
        assertThrows(IOException.class, () -> CampaignScoreJunction.prepare(fixture.binding(), fixture.basisBytes(), fixture.runtime(),
                Instant.now().minusSeconds(1), () -> { }));
        fixture.basis().put("machine_id", "different-machine");
        assertThrows(IOException.class, fixture::prepare);
        assertFalse(Files.exists(fixture.binding().path(), LinkOption.NOFOLLOW_LINKS));
    }
    @Test void receiptRoundtripRejectsWrongTypesExtraFieldsAndAlteredIdentity() throws Exception {
        var fixture = fixture("wire"); var receipt = fixture.prepare().receipt();
        for (String field : List.of("schema", "machine_id", "observed_at_utc", "status", "campaign_score_junction",
                "target_identity", "junction_identity", "copied_files", "ordinary_cycle_credit", "game_day_credit", "original_actions_replayed")) {
            var missing = receipt.toJson(); missing.remove(field);
            assertThrows(ContractViolationException.class, () -> CampaignScoreJunction.PreparedReceipt.decode(StrictJson.canonical(missing)));
            var nil = receipt.toJson(); nil.putNull(field);
            assertThrows(ContractViolationException.class, () -> CampaignScoreJunction.PreparedReceipt.decode(StrictJson.canonical(nil)));
        }
        for (String field : List.of("copied_files", "ordinary_cycle_credit", "game_day_credit")) {
            var wrong = receipt.toJson(); wrong.put(field, false);
            assertThrows(ContractViolationException.class, () -> CampaignScoreJunction.PreparedReceipt.decode(StrictJson.canonical(wrong)));
        }
        var extra = receipt.toJson(); extra.put("restoration_granted", true);
        assertThrows(ContractViolationException.class, () -> CampaignScoreJunction.PreparedReceipt.decode(StrictJson.canonical(extra)));
        var numericId = receipt.toJson(); ((ObjectNode)numericId.get("target_identity")).put("file_id", 1);
        assertThrows(ContractViolationException.class, () -> CampaignScoreJunction.PreparedReceipt.decode(StrictJson.canonical(numericId)));
        var wrongTarget = receipt.toJson(); ((ObjectNode)wrongTarget.get("target_identity")).put("file_id", "1");
        assertThrows(ContractViolationException.class, () -> CampaignScoreJunction.PreparedReceipt.decode(StrictJson.canonical(wrongTarget)));
    }
    private static ExactRef exact(Path path) throws IOException {
        var ref = ControlBuild.FileRef.measure(path); return new ExactRef(ref.path(), ref.bytes(), ref.sha256());
    }
}
