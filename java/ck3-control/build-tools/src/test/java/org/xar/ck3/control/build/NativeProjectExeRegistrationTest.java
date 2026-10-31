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
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
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
        NativeProjectExeUacRegression.main(new String[] {temporary.resolve("original-86").toString(), report.toString()});
        JsonNode actual = JSON.readTree(Files.readAllBytes(report));
        assertEquals(86, actual.path("tests").intValue());
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

    @Test void currentSingleInjectorTypedPlanRoundtripCannotWidenTheLegacyTargets() throws Exception {
        String sourceRoot = "D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/native10/dev61/ck3_autonomous_player/native_bridge";
        String buildRoot = "D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/native10/build61/dev";
        ControlBuild.FileRef data = new ControlBuild.FileRef(temporary.resolve("DATA-only-not-a-live-input.json").toString(), 1, "0".repeat(64));
        ControlBuild.FileRef tools = new ControlBuild.FileRef(temporary.resolve("DATA-only-S26-build.json").toString(), 202195,
                "b88971ee1680a659363ba41a685a8ba4766c746787b46a9431aa730d8aefe461");
        ControlBuild.FileRef injector = new ControlBuild.FileRef(Path.of(buildRoot).resolve("xar_ck3_bridge_injector.exe").toString(), 39936,
                "5337dd8be7c5aa44e4b7f48f9086ba6ee973f085316a74ff86881f73db59a185");
        var current = new NativeProjectExeUac.CurrentNativeBuild("xar.current-native-build-uac-input/v1",
                sourceRoot, buildRoot, data, data, data, data, tools, injector);
        String sid = "S-1-5-21-11-22-33-1001";
        var plan = new NativeProjectExeUac.CurrentNativeBuildPlan("xar.current-native-build-uac-plan/v1", MACHINE,
                START, DEADLINE, "/root/native_execution", sid, 2700, current, data, data, data, data,
                List.of(data), List.of(data), "C:/jdk-21", List.of(data), temporary.toString(),
                temporary.resolve("intent.json").toString(), temporary.resolve("launch.json").toString(),
                temporary.resolve("result.json").toString(), temporary.resolve("child-intent.json").toString(),
                temporary.resolve("child-outcome.json").toString(), temporary.resolve("shared.stdout").toString(),
                temporary.resolve("shared.stderr").toString());
        byte[] raw = JSON.writeValueAsBytes(plan);
        assertEquals(plan, NativeProjectExeUac.parseCurrentNativeBuildPlan(raw));
        ObjectNode value = (ObjectNode)JSON.readTree(raw);
        ObjectNode badSid = value.deepCopy(); badSid.put("expected_owner_sid", 1001);
        assertThrows(IOException.class, () -> NativeProjectExeUac.parseCurrentNativeBuildPlan(JSON.writeValueAsBytes(badSid)));
        ObjectNode missing = value.deepCopy(); missing.remove("uac_capacity_ref");
        assertThrows(IOException.class, () -> NativeProjectExeUac.parseCurrentNativeBuildPlan(JSON.writeValueAsBytes(missing)));
        ObjectNode wrongWait = value.deepCopy(); wrongWait.put("wait_seconds", true);
        assertThrows(IOException.class, () -> NativeProjectExeUac.parseCurrentNativeBuildPlan(JSON.writeValueAsBytes(wrongWait)));
        ObjectNode widened = value.deepCopy();
        ((ObjectNode)widened.get("current_native_build").get("injector")).put("path", "D:/arbitrary.exe");
        assertThrows(IOException.class, () -> NativeProjectExeUac.parseCurrentNativeBuildPlan(JSON.writeValueAsBytes(widened)));
        assertThrows(IllegalArgumentException.class, () -> new NativeProjectExeUac.NativeBuildRoot(buildRoot));
        assertEquals(2700, plan.waitSeconds()); // DATA shape only: the original deadline/capacity qualification is not invoked.
    }

    @Test void successorCarrierUsesProductionCompletedProofAndRejectsCrossCarrierAndOldS26Execution() throws Exception {
        // Existing fixture supplies a real native0/Job0 terminal and synthetic bounded archive.
        // This tests software proof consumption, never a genuine Maven build or UAC launch.
        var first = ControlBuildTest.completedReceiptFixture(temporary.resolve("provider-first"));
        var other = ControlBuildTest.completedReceiptFixture(temporary.resolve("provider-other"));
        var firstRef = first.receiptRef(); var otherRef = other.receiptRef();
        assertEquals(first.receipt(), ControlBuild.verifiedCompletedReceipt(firstRef));
        if (MACHINE.equals(first.receipt().machineId())) {
            assertEquals(first.receipt(), NativeProjectExeUac.qualifyCurrentCarrier(firstRef, firstRef, first.receipt().completeDeployment()));
        } else {
            // This retained Native adapter is bound to its original machine. A valid local
            // receipt on another host must be rejected rather than relabeled as that machine.
            IOException foreign = assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyCurrentCarrier(
                    firstRef, firstRef, first.receipt().completeDeployment()));
            assertEquals("actual complete qualified carrier and exact current standing binding required", foreign.getMessage());
        }
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyCurrentCarrier(
                firstRef, otherRef, first.receipt().completeDeployment()), "A standing cannot substitute another qualified carrier");
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyCurrentCarrier(
                firstRef, firstRef, other.receipt().completeDeployment()), "Exact complete deployment identities cannot be crossed");
        var successor = providerPlan(firstRef, true);
        assertEquals(successor, NativeProjectExeUac.parseCurrentNativeBuildPlan(JSON.writeValueAsBytes(successor)));
        NativeProjectExeUac.requireCurrentProviderExecution(successor);
        var legacy = providerPlan(new ControlBuild.FileRef(temporary.resolve("historical-S26-ref.json").toString(), 202195,
                "b88971ee1680a659363ba41a685a8ba4766c746787b46a9431aa730d8aefe461"), false);
        assertThrows(IOException.class, () -> NativeProjectExeUac.requireCurrentProviderExecution(legacy),
                "Original S26 v1 fields remain historical and cannot authorize another process");
        assertThrows(IllegalArgumentException.class, () -> providerPlan(firstRef, false), "V1 must retain its original exact carrier pin");
        assertThrows(IllegalArgumentException.class, () -> providerPlan(legacy.currentNativeBuild().qualifiedToolsBuildRef(), true),
                "V2 must not relabel the old S26 carrier");
        ObjectNode mixed = (ObjectNode) JSON.readTree(JSON.writeValueAsBytes(successor));
        mixed.put("schema", "xar.current-native-build-uac-plan/v1");
        assertThrows(IOException.class, () -> NativeProjectExeUac.parseCurrentNativeBuildPlan(JSON.writeValueAsBytes(mixed)));
        ObjectNode missing = (ObjectNode) JSON.readTree(JSON.writeValueAsBytes(successor));
        ((ObjectNode) missing.get("current_native_build")).remove("qualified_tools_build_ref");
        assertThrows(IOException.class, () -> NativeProjectExeUac.parseCurrentNativeBuildPlan(JSON.writeValueAsBytes(missing)));
        Path actualArchive = first.deploymentRoot().resolve("ck3-control-build-tools-0.1.0-SNAPSHOT.jar");
        Files.writeString(actualArchive, "changed after the recorded completion");
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyCurrentCarrier(firstRef, firstRef, first.receipt().completeDeployment()),
                "Actual completed source/deployment/runtime/terminal proof checks must remain in the execution carrier reader");
    }

    @Test void publicCliDispatchesCurrentV2ReviewExecuteAndAdminChildBeforeAnyLaunchAndRejectsUnknownSchemas() throws Exception {
        var carrier = new ControlBuild.FileRef(temporary.resolve("CLI-DATA-current-tools.json").toString(), 7, "1".repeat(64));
        var plan = providerPlan(carrier, true);
        ObjectNode wire = (ObjectNode) JSON.readTree(JSON.writeValueAsBytes(plan));
        // A deterministic first current-plan business guard proves the real public dispatcher selected the v2 reader.
        // The failure precedes all injector/runtime/native token reads and every process-launch path.
        wire.put("expected_owner_sid", "not-a-Windows-account-SID");
        Path path = temporary.resolve("cli-current-v2.json"); Files.write(path, JSON.writeValueAsBytes(wire));
        var ref = ControlBuild.FileRef.measure(path);
        String expectedMessage = MACHINE.equals(WindowsJobProcess.currentMachineId())
                ? "full canonical Windows SID required" : "current native plan schema/machine differs";
        IOException review = assertThrows(IOException.class, () -> NativeProjectExeUac.main(new String[]{"review", path.toString()}));
        assertEquals(expectedMessage, review.getMessage());
        IOException execute = assertThrows(IOException.class, () -> NativeProjectExeUac.main(new String[]{
                "execute-approved-plan", path.toString(), ref.sha256(), plan.deadlineAtUtc()}));
        assertEquals(expectedMessage, execute.getMessage());
        IOException admin = assertThrows(IOException.class, () -> NativeProjectExeUac.main(new String[]{
                "current-native-build-admin-child", path.toString(), Long.toString(ref.bytes()), ref.sha256(), plan.deadlineAtUtc()}));
        assertEquals(expectedMessage, admin.getMessage());
        assertFalse(Files.exists(Path.of(plan.intentPath())));
        assertFalse(Files.exists(Path.of(plan.adminChildIntentPath())));
        for (String schema : List.of("xar.current-native-build-uac-plan/v99", "xar.current-native-build-uac-input/v2",
                "xar.exact-two-exe-uac-plan/v99")) {
            wire.put("schema", schema); Files.write(path, JSON.writeValueAsBytes(wire));
            var wrong = ControlBuild.FileRef.measure(path);
            IOException wrongReview = assertThrows(IOException.class, () -> NativeProjectExeUac.main(new String[]{"review", path.toString()}));
            assertEquals("unsupported versioned UAC plan schema", wrongReview.getMessage(), schema);
            IOException wrongExecute = assertThrows(IOException.class, () -> NativeProjectExeUac.main(new String[]{
                    "execute-approved-plan", path.toString(), wrong.sha256(), plan.deadlineAtUtc()}));
            assertEquals("unsupported versioned UAC plan schema", wrongExecute.getMessage(), schema);
        }
        var oldCarrier = new ControlBuild.FileRef(temporary.resolve("CLI-DATA-old-S26.json").toString(), 202195,
                "b88971ee1680a659363ba41a685a8ba4766c746787b46a9431aa730d8aefe461");
        var legacy = providerPlan(oldCarrier, false);
        Files.write(path, JSON.writeValueAsBytes(legacy)); var legacyRef = ControlBuild.FileRef.measure(path);
        IOException oldExecute = assertThrows(IOException.class, () -> NativeProjectExeUac.main(new String[]{
                "execute-approved-plan", path.toString(), legacyRef.sha256(), legacy.deadlineAtUtc()}));
        assertTrue(oldExecute.getMessage().contains("historical only"));
        IOException oldAdmin = assertThrows(IOException.class, () -> NativeProjectExeUac.main(new String[]{
                "current-native-build-admin-child", path.toString(), Long.toString(legacyRef.bytes()), legacyRef.sha256(), legacy.deadlineAtUtc()}));
        assertTrue(oldAdmin.getMessage().contains("historical only"));
        assertFalse(Files.exists(Path.of(legacy.intentPath())));
        assertFalse(Files.exists(Path.of(legacy.adminChildIntentPath())));
    }

    private NativeProjectExeUac.CurrentNativeBuildPlan providerPlan(ControlBuild.FileRef carrier, boolean successor) {
        String sourceRoot = "D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/native10/dev61/ck3_autonomous_player/native_bridge";
        String buildRoot = "D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/native10/build61/dev";
        var data = new ControlBuild.FileRef(temporary.resolve("provider-plan-DATA.json").toString(), 1, "0".repeat(64));
        var injector = new ControlBuild.FileRef(Path.of(buildRoot).resolve("xar_ck3_bridge_injector.exe").toString(), 39936,
                "5337dd8be7c5aa44e4b7f48f9086ba6ee973f085316a74ff86881f73db59a185");
        var build = new NativeProjectExeUac.CurrentNativeBuild(
                successor ? "xar.current-native-build-uac-input/v2" : "xar.current-native-build-uac-input/v1",
                sourceRoot, buildRoot, data, data, data, data, carrier, injector);
        return new NativeProjectExeUac.CurrentNativeBuildPlan(
                successor ? "xar.current-native-build-uac-plan/v2" : "xar.current-native-build-uac-plan/v1",
                MACHINE, START, DEADLINE, "/root/native_execution", "S-1-5-21-11-22-33-1001", 2700, build,
                data, data, data, data, List.of(data), List.of(data), "C:/jdk-21", List.of(data), temporary.toString(),
                temporary.resolve("provider-intent.json").toString(), temporary.resolve("provider-launch.json").toString(),
                temporary.resolve("provider-result.json").toString(), temporary.resolve("provider-child-intent.json").toString(),
                temporary.resolve("provider-child-outcome.json").toString(), temporary.resolve("provider-shared.stdout").toString(),
                temporary.resolve("provider-shared.stderr").toString());
    }

    @Test void currentThreeSettingsUsesFullHelperIdentityAndPreservesNonPathSets() throws Exception {
        var helper = new WindowsJobProcess.ProcessIdentity(1234, "18446744073709551615", temporary.resolve("DATA-python.exe").toString());
        String sid = "S-1-5-21-11-22-33-1001";
        ObjectNode receipt = currentSettingsData(sid, helper.pid());
        var proof = NativeProjectExeUac.qualifyThreeSettings(JSON.readTree(JSON.writeValueAsBytes(receipt)), sid, helper);
        assertEquals("1234", proof.processIdDecimal());
        assertEquals(sid, proof.tokenUserSid());
        assertEquals(proof, JSON.readValue(JSON.writeValueAsBytes(proof), NativeProjectExeUac.ThreeSettingsReadback.class));
        ObjectNode reordered = receipt.deepCopy();
        ((ObjectNode)reordered.get("after_settings")).putArray("ExclusionExtension").add(".a").add(".b").add(".a");
        NativeProjectExeUac.qualifyThreeSettings(reordered, sid, helper);
        for (Mutation mutation : List.<Mutation>of(
                row -> row.put("settings_readback_complete", 1),
                row -> row.put("settings_readback_process_id", true),
                row -> row.put("settings_readback_process_id", 1235),
                row -> row.put("settings_readback_token_user_sid", "S-1-5-21-99-22-33-1001"),
                row -> row.put("observed_extensions_unchanged", false),
                row -> row.put("settings_readback_error", "latched read failure"),
                row -> row.putNull("before_settings"),
                row -> row.remove("after_settings"),
                row -> row.put("broker_schema", "DATA-broker-is-another-proof-scope"),
                row -> ((ObjectNode)row.get("after_settings")).putArray("ExclusionProcess").add("changed.exe"),
                row -> ((ObjectNode)row.get("after_settings")).put("ExclusionExtension", false),
                row -> ((ObjectNode)row.get("after_settings")).putArray("ExclusionPath").add("different-original-path"))) {
            ObjectNode changed = receipt.deepCopy(); mutation.apply(changed);
            assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyThreeSettings(changed, sid, helper));
        }
        NativeProjectExeUac.requireSameOwnerSid(sid, sid);
        assertThrows(IOException.class, () -> NativeProjectExeUac.requireSameOwnerSid(sid, "S-1-5-21-99-22-33-1001"));
        assertThrows(IOException.class, () -> NativeProjectExeUac.requireCanonicalSid("S-1-5-21-11-22-33-01001"));
        assertThrows(IOException.class, () -> NativeProjectExeUac.requireCanonicalSid("S-1-281474976710656-1"));
        assertThrows(IOException.class, () -> NativeProjectExeUac.requireCanonicalSid("S-1-5-4294967296"));
    }

    @Test void originalS26V2JavaProducerFeedsOnlyItsExactVersionedDecoder() throws Exception {
        ControlBuild.FileRef pin = new ControlBuild.FileRef(temporary.resolve("DATA-only-pin.json").toString(), 1, "0".repeat(64));
        var identity = new WindowsJobProcess.ProcessIdentity(1234, "18446744073709551615", temporary.resolve("DATA-java.exe").toString());
        var command = new WindowsJobProcess.CommandResult(identity, 0, .1,
                new WindowsJobProcess.Accounting(1024, 0, 1L << 30, WindowsJobProcess.REQUIRED_FLAGS), null);
        var producer = new SharedOwnedCommand.Terminal("xar.shared-owned-command-terminal/v2", MACHINE, START,
                SharedOwnedCommand.Status.PASS, "/root/native_execution", "r4-slot1", null, pin, pin, pin, List.of(pin),
                new SharedOwnedCommand.Outer("1234", 256L << 20, false, "DATA conservative outer reservation"),
                true, command, new WindowsJobProcess.JobDiagnosticOutcome(WindowsJobProcess.DiagnosticWriteState.NOT_REQUESTED,
                        null, null, null), SharedOwnedCommand.Check.MATCH, SharedOwnedCommand.Check.MATCH, SharedOwnedCommand.Check.MATCH,
                null, List.of(), List.of("DATA-only-no-launch"), pin, pin, 1024, 0, 0);
        byte[] raw = SharedOwnedCommand.encodeTerminal(producer, false);
        var decoded = NativeProjectExeUac.parseCurrentSharedJavaTerminal(raw);
        assertEquals(producer.schema(), decoded.schema());
        assertEquals(producer.child(), decoded.child());
        assertEquals(producer.outer(), decoded.outer());
        assertEquals(26, JSON.readTree(raw).size());
        for (Mutation mutation : List.<Mutation>of(
                row -> row.put("schema", "xar.shared-owned-command-terminal/v4"),
                row -> row.putNull("java_invocation_evidence_ref"),
                row -> row.remove("runtime_postcheck"),
                row -> row.put("child_started", 1))) {
            ObjectNode changed = (ObjectNode)JSON.readTree(raw); mutation.apply(changed);
            assertThrows(IOException.class, () -> NativeProjectExeUac.parseCurrentSharedJavaTerminal(JSON.writeValueAsBytes(changed)));
        }
    }

    /** Exact new helper wire DATA; it grants no source, process-launch or current manifest qualification. */
    private ObjectNode currentSettingsData(String sid, long pid) throws Exception {
        ObjectNode receipt = (ObjectNode)JSON.readTree(evidence().raw());
        receipt.put("settings_readback_schema", "xar.project-exe-three-settings-readback/v1");
        receipt.put("settings_readback_complete", true); receipt.putNull("settings_readback_error");
        receipt.put("observed_extensions_unchanged", true); receipt.put("observed_processes_unchanged", true);
        receipt.put("settings_readback_process_id", pid); receipt.put("settings_readback_token_user_sid", sid);
        ObjectNode before = receipt.putObject("before_settings"); before.set("ExclusionPath", receipt.get("before").deepCopy());
        before.putArray("ExclusionExtension").add(".a").add(".b"); before.putArray("ExclusionProcess").add("old.exe");
        ObjectNode after = receipt.putObject("after_settings"); after.set("ExclusionPath", receipt.get("after").deepCopy());
        after.putArray("ExclusionExtension").add(".b").add(".a"); after.putArray("ExclusionProcess").add("old.exe");
        return receipt;
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
