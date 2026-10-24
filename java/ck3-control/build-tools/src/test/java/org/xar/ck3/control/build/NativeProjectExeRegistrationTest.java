package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

/** Software-only persistent CI route. All receipt and launch data below are synthetic. */
public final class NativeProjectExeRegistrationTest {
    private static final ObjectMapper JSON = ControlBuild.strictMapper();
    private static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";
    private static final String START = "2026-10-22T00:00:00Z";
    private static final String DEADLINE = "2026-10-22T00:04:00Z";
    private static final String BUILD = "D:/codex-ck3-demos/2026-10-22-java-phase1/build/native-prisoners-combat05";
    private static final String KINSHIP = "ck3_12003_prisoner_native_kinship_test";
    private static final String COMBAT = "xar_bridge_ck3_12003_army_combat_roles_phase_rule24_pins_test";

    @TempDir Path temporary;

    @Test void originalProductionCallerRegression() throws Exception {
        Path report = temporary.resolve("regression.json");
        NativeProjectExeUacRegression.main(new String[] {temporary.resolve("original-81").toString(), report.toString()});
        JsonNode actual = JSON.readTree(Files.readAllBytes(report));
        assertEquals(81, actual.path("tests").intValue());
        assertEquals(0, actual.path("failures").intValue());
        assertEquals(0, actual.path("uac_calls").longValue());
        assertEquals(0, actual.path("defender_calls").longValue());
        assertEquals(0, actual.path("native_fixture_calls").longValue());
    }

    @Test void actualResultRecordAndCausalReaderRoundtrip() throws Exception {
        Evidence evidence = evidence();
        NativeProjectExeUac.Result parsed = JSON.readValue(JSON.writeValueAsBytes(evidence.result()), NativeProjectExeUac.Result.class);
        assertEquals(evidence.result(), parsed);
        assertEquals(NativeProjectExeUac.ProofScope.DIRECT_ADMIN_EXCLUSION_PATH, qualify(evidence, parsed).proofScope());
        assertEquals(evidence.result().processIdentity(), qualify(evidence, parsed).processIdentity());
        var qualification = new NativeProjectExeRegistration.Qualification("xar.project-exe-registration-qualification/v1", MACHINE,
                START, evidence.review().planRef(), evidence.receiptRef(), evidence.receiptRef(), evidence.receiptRef(),
                evidence.receiptRef(), qualify(evidence, parsed), List.of());
        assertEquals(qualification, JSON.readValue(JSON.writeValueAsBytes(qualification), NativeProjectExeRegistration.Qualification.class));
        NativeProjectExeUac.ReceiptExpectation changedSource = new NativeProjectExeUac.ReceiptExpectation(
                evidence.expectation().nativeBuildRoot(), "f".repeat(64), evidence.expectation().files());
        assertThrows(IOException.class, () -> NativeProjectExeRegistration.qualifyEvidence(START, DEADLINE, evidence.review(),
                evidence.intent(), evidence.launch(), parsed, changedSource, evidence.raw(), evidence.receiptRef()));
    }

    @Test void resultStatusScopeAndTerminalMustAgree() throws Exception {
        Evidence value = evidence();
        rejectResult(value, row -> row.put("schema", "xar.exact-two-exe-uac-result/v3"));
        rejectResult(value, row -> row.put("status", "UNKNOWN"));
        rejectResult(value, row -> row.putNull("proof_scope"));
        rejectResult(value, row -> row.put("launch_call_entered", false));
        rejectResult(value, row -> row.put("shell_acknowledged", false));
        rejectResult(value, row -> row.put("launch_win32_error", 1223));
        rejectResult(value, row -> row.put("wait_timed_out", true));
        rejectResult(value, row -> row.put("automatically_retried", true));
        rejectResult(value, row -> row.put("process_terminated", true));
        rejectResult(value, row -> row.withArray("diagnostics").add("retained actual error"));
        rejectResult(value, row -> ((ObjectNode)row.get("terminal_proof")).put("native_signalled", false));
        rejectResult(value, row -> ((ObjectNode)row.get("terminal_proof")).put("process_exit_code_decimal", "1"));
        rejectResult(value, row -> ((ObjectNode)row.get("terminal_proof")).put("timed_out", true));
        rejectResult(value, row -> ((ObjectNode)row.get("terminal_proof")).put("token_elevated", false));
    }

    @Test void resultProcessPlanAndOriginalReceiptCannotBeSubstituted() throws Exception {
        Evidence value = evidence();
        rejectResult(value, row -> ((ObjectNode)row.get("process_identity")).put("pid_decimal", "1235"));
        rejectResult(value, row -> ((ObjectNode)row.get("process_identity")).put("creation_filetime_decimal", "18446744073709551614"));
        rejectResult(value, row -> ((ObjectNode)row.get("review")).put("lp_file", "C:/other.exe"));
        rejectResult(value, row -> ((ObjectNode)row.get("helper_receipt_ref")).put("sha256", "f".repeat(64)));
        rejectResult(value, row -> row.put("observed_at_utc", DEADLINE));
        rejectResult(value, row -> row.put("observed_at_utc", "2026-10-21T23:59:59Z"));
        ObjectNode intent = JSON.valueToTree(value.intent());
        ((ObjectNode)intent.get("review")).put("lp_parameters", "substituted-command");
        NativeProjectExeUac.Intent changedIntent = JSON.treeToValue(intent, NativeProjectExeUac.Intent.class);
        assertThrows(IOException.class, () -> NativeProjectExeRegistration.qualifyEvidence(START, DEADLINE, value.review(),
                changedIntent, value.launch(), value.result(), value.expectation(), value.raw(), value.receiptRef()));
        ObjectNode receipt = (ObjectNode)JSON.readTree(value.raw()); receipt.withArray("after").remove(1);
        byte[] changedBytes = JSON.writeValueAsBytes(receipt);
        assertThrows(IOException.class, () -> NativeProjectExeRegistration.qualifyEvidence(START, DEADLINE, value.review(),
                value.intent(), value.launch(), value.result(), value.expectation(), changedBytes, value.receiptRef()));
    }

    @Test void strictPersistedResultRejectsMissingNullWrongTypesAndUnknownFields() throws Exception {
        Evidence value = evidence();
        rejectDecode(value, row -> row.remove("terminal_proof"));
        rejectResult(value, row -> row.putNull("terminal_proof"));
        rejectDecode(value, row -> row.put("launch_call_entered", 1));
        rejectDecode(value, row -> row.put("wait_timed_out", "false"));
        rejectDecode(value, row -> row.put("unknown_field", false));
        rejectDecode(value, row -> ((ObjectNode)row.get("terminal_proof")).put("native_signalled", 1.0));
        rejectDecode(value, row -> ((ObjectNode)row.get("process_identity")).put("creation_filetime_decimal", 9007199254740992L));
        rejectDecode(value, row -> ((ObjectNode)row.get("review")).put("wait_seconds", true));
    }

    @Test void fileReaderRejectsChangedReviewedBytesBeforeFollowingSyntheticPlan() throws Exception {
        Path plan = temporary.resolve("invalid-synthetic-plan.json");
        Files.writeString(plan, "{}", StandardCharsets.UTF_8);
        ControlBuild.FileRef ref = ControlBuild.FileRef.measure(plan);
        assertThrows(IOException.class, () -> NativeProjectExeRegistration.readVerified(plan, "0".repeat(64), DEADLINE, ref));
        assertThrows(IOException.class, () -> NativeProjectExeRegistration.readVerified(plan, ref.sha256(), DEADLINE, ref));
        assertEquals("{}", Files.readString(plan));
    }

    @Test void actualV2BuildProducerMustAgreeWithTypedNativeLifecycle() throws Exception {
        var owner = new WindowsJobProcess.ProcessIdentity(17, "134371745963270833", "D:/synthetic/build.exe");
        var terminal = new WindowsJobProcess.CommandResult(owner, 0, .1,
                new WindowsJobProcess.Accounting(1024, 0, 268435456, WindowsJobProcess.REQUIRED_FLAGS), null);
        ObjectNode actual = JSON.createObjectNode(); actual.put("schema", "xar.shared-native-stage-actual/v2");
        actual.put("machine_id", MACHINE); actual.put("stage_id", "two-target-build"); actual.put("status", "PASS");
        actual.put("source_unchanged", true); actual.putNull("error"); actual.put("stage_deadline_at_utc", DEADLINE);
        actual.set("result", JSON.valueToTree(terminal)); actual.set("owner_identity", JSON.valueToTree(owner));
        actual.set("lifecycle", JSON.valueToTree(NativeLifecycleTerminal.assess(terminal)));
        assertEquals(terminal, NativeProjectExeUac.qualifyBuildActual(JSON.readTree(JSON.writeValueAsBytes(actual))));
        ObjectNode legacy = actual.deepCopy(); legacy.put("schema", "xar.shared-native-stage-actual/v1");
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyBuildActual(legacy));
        ObjectNode missing = actual.deepCopy(); missing.remove("stage_deadline_at_utc");
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyBuildActual(missing));
        ObjectNode changedOwner = actual.deepCopy(); ((ObjectNode)changedOwner.get("owner_identity")).put("pid", 18);
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyBuildActual(changedOwner));
        ObjectNode cleanup = actual.deepCopy(); ((ObjectNode)cleanup.get("result")).put("stop_reason", "timeout_or_release_expired");
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyBuildActual(cleanup));
        ObjectNode live = actual.deepCopy(); ((ObjectNode)live.get("result").get("accounting")).put("active_processes", 1);
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyBuildActual(live));
    }

    private record Evidence(NativeProjectExeUac.Review review, NativeProjectExeUac.Intent intent,
            NativeProjectExeUac.LaunchObservation launch, NativeProjectExeUac.Result result,
            NativeProjectExeUac.ReceiptExpectation expectation, byte[] raw, ControlBuild.FileRef receiptRef) { }

    private Evidence evidence() throws Exception {
        ControlBuild.FileRef source = new ControlBuild.FileRef(temporary.resolve("synthetic-only-not-a-plan.json").toString(), 1, "0".repeat(64));
        NativeProjectExeUac.NativeBuildRoot root = new NativeProjectExeUac.NativeBuildRoot(BUILD);
        ObjectNode manifest = JSON.createObjectNode();
        for (String target : List.of(KINSHIP, COMBAT)) {
            ObjectNode row = manifest.withArray("files").addObject();
            row.put("path", BUILD + "/bin/" + target + ".exe"); row.put("size", 7);
            row.put("sha256", NativeProjectExeUac.sha(target.getBytes(StandardCharsets.UTF_8)));
            row.put("target", target); row.put("target_id", "synthetic-" + target);
        }
        NativeProjectExeUac.ReceiptExpectation expected = NativeProjectExeUac.receiptExpectation(root, manifest);
        ObjectNode receipt = JSON.createObjectNode(); receipt.put("schema", "xar.project-exe-exclusions.v1");
        receipt.put("status", "verified"); receipt.put("admin_token", true); receipt.put("settings_success_is_runtime_trust", false);
        receipt.put("manifest_sha256", expected.manifestSemanticSha256()); receipt.set("files", JSON.valueToTree(expected.files()));
        receipt.putArray("before").add("C:/synthetic-previous.exe"); receipt.putArray("after").add("C:/synthetic-previous.exe");
        for (NativeProjectExeUac.ManifestFile row : expected.files()) {
            receipt.withArray("after").add(row.path()); receipt.withArray("verified_requested_paths").add(row.path());
        }
        receipt.putArray("missing_requested_paths"); receipt.put("observed_prior_settings_preserved", true); receipt.put("partial_mutation", false);
        byte[] raw = JSON.writeValueAsBytes(receipt);
        ControlBuild.FileRef receiptRef = new ControlBuild.FileRef(temporary.resolve("synthetic-raw-receipt.json").toString(), raw.length, NativeProjectExeUac.sha(raw));
        String interpreter = temporary.resolve("not-a-real-executable.exe").toString();
        NativeProjectExeUac.Review review = new NativeProjectExeUac.Review("xar.exact-two-exe-uac-review/v2", MACHINE, START,
                source, source, source, root, expected.manifestSemanticSha256(), "runas", interpreter, "SYNTHETIC_NO_EXECUTION",
                temporary.toString(), 0, 190, List.of());
        NativeProjectExeUac.ProcessIdentity identity = new NativeProjectExeUac.ProcessIdentity("1234", "18446744073709551615", interpreter);
        NativeProjectExeUac.Intent intent = new NativeProjectExeUac.Intent("xar.exact-two-exe-uac-intent/v2", MACHINE, START, review,
                List.of(new NativeProjectExeUac.GuardedInput(source.path(), new NativeProjectExeUac.NativeFileIdentity("1", "2", "1", source.path(), false))), "UNKNOWN must remain exclusive");
        NativeProjectExeUac.LaunchObservation launch = new NativeProjectExeUac.LaunchObservation("xar.exact-two-exe-uac-launch/v1", MACHINE, START, true, identity, true);
        NativeProjectExeUac.TerminalProof terminal = new NativeProjectExeUac.TerminalProof(true, identity, true, true, false, "0");
        NativeProjectExeUac.Result result = new NativeProjectExeUac.Result("xar.exact-two-exe-uac-result/v4", MACHINE,
                Instant.parse(START).plusSeconds(1).toString(), NativeProjectExeUac.Status.VERIFIED,
                NativeProjectExeUac.ProofScope.DIRECT_ADMIN_EXCLUSION_PATH, review, true, true, null, identity, true,
                "0", false, receiptRef, List.of(), false, false, terminal);
        return new Evidence(review, intent, launch, result, expected, raw, receiptRef);
    }

    @FunctionalInterface private interface Mutation { void apply(ObjectNode value); }
    private void rejectResult(Evidence evidence, Mutation mutation) throws Exception {
        ObjectNode row = JSON.valueToTree(evidence.result()); mutation.apply(row);
        NativeProjectExeUac.Result changed = JSON.treeToValue(row, NativeProjectExeUac.Result.class);
        assertThrows(IOException.class, () -> qualify(evidence, changed));
    }
    private void rejectDecode(Evidence evidence, Mutation mutation) {
        ObjectNode row = JSON.valueToTree(evidence.result()); mutation.apply(row);
        assertThrows(IOException.class, () -> JSON.readValue(JSON.writeValueAsBytes(row), NativeProjectExeUac.Result.class));
    }
    private NativeProjectExeUac.ReceiptQualification qualify(Evidence evidence, NativeProjectExeUac.Result result) throws IOException {
        return NativeProjectExeRegistration.qualifyEvidence(START, DEADLINE, evidence.review(), evidence.intent(), evidence.launch(),
                result, evidence.expectation(), evidence.raw(), evidence.receiptRef());
    }
}
