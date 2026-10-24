package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

/** Synthetic production-contract regression. Never constructs a valid registration Plan or calls a launcher. */
public final class NativeProjectExeUacRegression {
    private static final ObjectMapper JSON = ControlBuild.strictMapper();
    private static final String KINSHIP = "ck3_12003_prisoner_native_kinship_test";
    private static final String COMBAT = "xar_bridge_ck3_12003_army_combat_roles_phase_rule24_pins_test";
    private static final String FIXED_BUILD = "D:/codex-ck3-demos/2026-10-22-java-phase1/build/native-prisoners-combat04";
    private static final List<String> passed = new ArrayList<>();
    private NativeProjectExeUacRegression() { }

    @FunctionalInterface private interface Checked { void run() throws Exception; }
    public record Actual(String schema, String machineId, String observedAtUtc, String scope, int tests, int failures,
            List<String> passedCases, long uacCalls, long defenderCalls, long nativeFixtureCalls) { }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) throw new IllegalArgumentException("fresh-synthetic-fixture-root new-report.json");
        Path fixtures = Path.of(args[0]).toAbsolutePath().normalize();
        Path report = Path.of(args[1]).toAbsolutePath().normalize();
        if (Files.exists(fixtures) || Files.exists(report)) throw new IOException("synthetic outputs are append-only");
        Files.createDirectory(fixtures);
        String interpreter = fixtures.resolve("not-an-executable-interpreter-source-only.exe").toString();
        var identity = new NativeProjectExeUac.ProcessIdentity("1234", "18446744073709551615", interpreter);
        var terminal = new NativeProjectExeUac.TerminalProof(true, identity, true, true, false, "0");
        ObjectNode manifest = manifest();
        var build04 = new NativeProjectExeUac.NativeBuildRoot(FIXED_BUILD);
        var expected = NativeProjectExeUac.receiptExpectation(build04, manifest);
        ObjectNode receipt = receipt(expected);
        byte[] raw = bytes(receipt);
        var pin = pin(fixtures, raw);

        check("verified-receipt-original-byte-and-identity-roundtrip", () -> {
            var qualified = NativeProjectExeUac.qualifyCompletion(terminal, interpreter, expected, raw, pin);
            equal(pin.sha256(), qualified.rawSha256()); equal(identity, qualified.processIdentity());
            equal(NativeProjectExeUac.ProofScope.DIRECT_ADMIN_EXCLUSION_PATH, qualified.proofScope());
            equal(qualified, JSON.readValue(JSON.writeValueAsBytes(qualified), NativeProjectExeUac.ReceiptQualification.class));
        });
        check("actual-empty-before-array-is-distinct-from-null-and-missing", () -> {
            ObjectNode changed = receipt.deepCopy(); changed.putArray("before"); changed.withArray("after").remove(0);
            byte[] changedRaw = bytes(changed); qualify(terminal, interpreter, expected, changedRaw, pin(fixtures, changedRaw));
        });
        check("explicit-build05-receipt-bound-to-the-same-reviewed-root", () -> {
            var build05 = new NativeProjectExeUac.NativeBuildRoot(FIXED_BUILD.replace("04", "05"));
            ObjectNode manifest05 = manifest.deepCopy();
            for (JsonNode row : manifest05.withArray("files")) ((ObjectNode)row).put("path", row.path("path").textValue().replace("combat04/", "combat05/"));
            var expectation05 = NativeProjectExeUac.receiptExpectation(build05, manifest05);
            byte[] raw05 = bytes(receipt(expectation05)); qualify(terminal, interpreter, expectation05, raw05, pin(fixtures, raw05));
            mustReject(() -> NativeProjectExeUac.receiptExpectation(build04, manifest05));
        });
        reject("mixed-build04-build05-exe-roots-rejected", () -> {
            ObjectNode mixed = manifest.deepCopy(); ObjectNode row = (ObjectNode)mixed.withArray("files").get(0);
            row.put("path", row.path("path").textValue().replace("combat04/", "combat05/"));
            NativeProjectExeUac.receiptExpectation(build04, mixed);
        });
        reject("nonapproved-build-root-rejected", () -> new NativeProjectExeUac.NativeBuildRoot("C:/unapproved-native-root"));
        reject("noncanonical-build-root-rejected", () -> new NativeProjectExeUac.NativeBuildRoot(FIXED_BUILD + "/../native-prisoners-combat05"));
        check("existing-wildcard-environment-directory-entries-remain-uninterpreted", () -> {
            ObjectNode changed = receipt.deepCopy();
            changed.withArray("before").add("%ProgramData%\\synthetic\\*").add("C:\\synthetic-directory\\");
            changed.withArray("after").add("%ProgramData%\\synthetic\\*").add("C:\\synthetic-directory\\");
            byte[] changedRaw = bytes(changed); qualify(terminal, interpreter, expected, changedRaw, pin(fixtures, changedRaw));
        });
        reject("ack-without-process-does-not-qualify", () -> qualify(new NativeProjectExeUac.TerminalProof(true, null, true, true, false, "0"), interpreter, expected, raw, pin));
        reject("missing-shell-ack-does-not-qualify", () -> qualify(new NativeProjectExeUac.TerminalProof(false, identity, true, true, false, "0"), interpreter, expected, raw, pin));
        reject("not-elevated-native-token-does-not-qualify", () -> qualify(new NativeProjectExeUac.TerminalProof(true, identity, false, true, false, "0"), interpreter, expected, raw, pin));
        reject("unknown-native-token-does-not-qualify", () -> qualify(new NativeProjectExeUac.TerminalProof(true, identity, null, true, false, "0"), interpreter, expected, raw, pin));
        reject("live-child-receipt-is-not-completion", () -> qualify(new NativeProjectExeUac.TerminalProof(true, identity, true, false, false, "0"), interpreter, expected, raw, pin));
        reject("timeout-even-with-late-verified-json-does-not-qualify", () -> qualify(new NativeProjectExeUac.TerminalProof(true, identity, true, true, true, "0"), interpreter, expected, raw, pin));
        reject("nonzero-child-even-with-verified-json-does-not-qualify", () -> qualify(new NativeProjectExeUac.TerminalProof(true, identity, true, true, false, "1"), interpreter, expected, raw, pin));
        reject("still-active-code-does-not-qualify", () -> qualify(new NativeProjectExeUac.TerminalProof(true, identity, true, true, false, "259"), interpreter, expected, raw, pin));
        reject("exit-missing-does-not-qualify", () -> qualify(new NativeProjectExeUac.TerminalProof(true, identity, true, true, false, null), interpreter, expected, raw, pin));
        reject("different-process-image-does-not-qualify", () -> qualify(terminal, fixtures.resolve("wrong-interpreter.exe").toString(), expected, raw, pin));
        reject("zero-pid-rejected", () -> new NativeProjectExeUac.ProcessIdentity("0", "1", interpreter));
        reject("leading-zero-pid-rejected", () -> new NativeProjectExeUac.ProcessIdentity("01234", "1", interpreter));
        reject("uint32-pid-overflow-rejected", () -> new NativeProjectExeUac.ProcessIdentity("4294967296", "1", interpreter));
        reject("fractional-filetime-string-rejected", () -> new NativeProjectExeUac.ProcessIdentity("1", "1.0", interpreter));
        reject("uint64-filetime-overflow-rejected", () -> new NativeProjectExeUac.ProcessIdentity("1", "18446744073709551616", interpreter));
        reject("numeric-filetime-json-rejected", () -> JSON.readValue("{\"pid_decimal\":\"1\",\"creation_filetime_decimal\":18446744073709551615,\"executable\":\"C:/synthetic.exe\"}", NativeProjectExeUac.ProcessIdentity.class));
        reject("boolean-pid-json-rejected", () -> JSON.readValue("{\"pid_decimal\":true,\"creation_filetime_decimal\":\"1\",\"executable\":\"C:/synthetic.exe\"}", NativeProjectExeUac.ProcessIdentity.class));
        check("root-reviewed-plan-sha-binds-exact-bytes", () -> NativeProjectExeUac.requireReviewedPlan(pin, pin.sha256()));
        reject("different-root-reviewed-plan-sha-rejected", () -> NativeProjectExeUac.requireReviewedPlan(pin, "0".repeat(64)));
        reject("noncanonical-root-plan-sha-rejected", () -> NativeProjectExeUac.requireReviewedPlan(pin, pin.sha256().toUpperCase(java.util.Locale.ROOT)));
        reject("float-plan-budget-rejected-before-construction", () -> NativeProjectExeUac.parsePlan("{\"wait_seconds\":240.0}".getBytes(StandardCharsets.UTF_8)));
        reject("bool-plan-budget-rejected-before-construction", () -> NativeProjectExeUac.parsePlan("{\"wait_seconds\":true}".getBytes(StandardCharsets.UTF_8)));
        reject("duplicate-plan-key-rejected", () -> NativeProjectExeUac.parsePlan("{\"wait_seconds\":240,\"wait_seconds\":240}".getBytes(StandardCharsets.UTF_8)));
        reject("unknown-plan-key-rejected", () -> NativeProjectExeUac.parsePlan("{\"unexpected\":true}".getBytes(StandardCharsets.UTF_8)));
        reject("missing-plan-fields-rejected", () -> NativeProjectExeUac.parsePlan("{}".getBytes(StandardCharsets.UTF_8)));

        reject("raw-receipt-size-drift-rejected", () -> qualify(terminal, interpreter, expected, raw,
                new ControlBuild.FileRef(pin.path(), pin.bytes() + 1, pin.sha256())));
        reject("raw-receipt-sha-drift-rejected", () -> qualify(terminal, interpreter, expected, raw,
                new ControlBuild.FileRef(pin.path(), pin.bytes(), "0".repeat(64))));
        rejectReceipt("receipt-manifest-source-sha-drift-rejected", receipt, fixtures, terminal, interpreter, expected,
                value -> value.put("manifest_sha256", "f".repeat(64)));
        rejectReceipt("receipt-exe-byte-pin-drift-rejected", receipt, fixtures, terminal, interpreter, expected,
                value -> ((ObjectNode) value.withArray("files").get(0)).put("sha256", "f".repeat(64)));
        rejectReceipt("receipt-foreign-exe-path-rejected", receipt, fixtures, terminal, interpreter, expected,
                value -> ((ObjectNode) value.withArray("files").get(0)).put("path", "C:/synthetic-foreign.exe"));
        rejectReceipt("receipt-missing-exe-row-rejected", receipt, fixtures, terminal, interpreter, expected,
                value -> value.withArray("files").remove(0));
        rejectReceipt("receipt-extra-exe-row-rejected", receipt, fixtures, terminal, interpreter, expected,
                value -> value.withArray("files").add(value.withArray("files").get(0).deepCopy()));
        rejectReceipt("receipt-disabled-status-rejected", receipt, fixtures, terminal, interpreter, expected,
                value -> value.put("status", "disabled"));
        rejectReceipt("receipt-missing-admin-token-rejected", receipt, fixtures, terminal, interpreter, expected,
                value -> value.remove("admin_token"));
        rejectReceipt("receipt-admin-token-number-rejected", receipt, fixtures, terminal, interpreter, expected,
                value -> value.put("admin_token", 1));
        rejectReceipt("receipt-admin-token-false-rejected", receipt, fixtures, terminal, interpreter, expected,
                value -> value.put("admin_token", false));
        rejectReceipt("receipt-forged-runtime-trust-rejected", receipt, fixtures, terminal, interpreter, expected,
                value -> value.put("settings_success_is_runtime_trust", true));
        rejectReceipt("receipt-missing-before-rejected", receipt, fixtures, terminal, interpreter, expected,
                value -> value.remove("before"));
        rejectReceipt("receipt-null-before-distinct-from-empty-rejected", receipt, fixtures, terminal, interpreter, expected,
                value -> value.putNull("before"));
        rejectReceipt("receipt-lost-prior-path-rejected", receipt, fixtures, terminal, interpreter, expected,
                value -> value.withArray("after").remove(0));
        rejectReceipt("receipt-missing-selected-after-path-rejected", receipt, fixtures, terminal, interpreter, expected,
                value -> value.withArray("after").remove(1));
        rejectReceipt("receipt-partial-mutation-rejected", receipt, fixtures, terminal, interpreter, expected,
                value -> value.put("partial_mutation", true));
        rejectReceipt("receipt-missing-paths-not-empty-rejected", receipt, fixtures, terminal, interpreter, expected,
                value -> value.withArray("missing_requested_paths").add("C:/missing.exe"));
        rejectReceipt("receipt-broker-provenance-cannot-masquerade-as-direct-admin", receipt, fixtures, terminal, interpreter, expected,
                value -> value.put("broker_schema", "forged-broker"));
        reject("expectation-third-target-rejected", () -> new NativeProjectExeUac.ManifestFile("C:/foreign.exe", 1,
                "0".repeat(64), "not-a-target", "synthetic"));
        reject("expectation-foreign-selected-exe-path-rejected", () -> new NativeProjectExeUac.ManifestFile("C:/foreign.exe", 1,
                "0".repeat(64), KINSHIP, "synthetic"));
        reject("expectation-exe-float-size-rejected", () -> {
            ObjectNode changed = manifest.deepCopy(); ((ObjectNode)changed.withArray("files").get(0)).put("size", 1.0);
            NativeProjectExeUac.receiptExpectation(build04, changed);
        });
        reject("expectation-exe-bool-size-rejected", () -> {
            ObjectNode changed = manifest.deepCopy(); ((ObjectNode)changed.withArray("files").get(0)).put("size", true);
            NativeProjectExeUac.receiptExpectation(build04, changed);
        });
        reject("expectation-missing-target-id-rejected", () -> {
            ObjectNode changed = manifest.deepCopy(); ((ObjectNode)changed.withArray("files").get(0)).remove("target_id");
            NativeProjectExeUac.receiptExpectation(build04, changed);
        });
        reject("expectation-unknown-row-field-rejected", () -> {
            ObjectNode changed = manifest.deepCopy(); ((ObjectNode)changed.withArray("files").get(0)).put("invented", true);
            NativeProjectExeUac.receiptExpectation(build04, changed);
        });

        check("unicode-semantic-json-preserves-python-ensure-ascii-domain", () -> {
            JsonNode input = JSON.readTree("{\"s\":\"琉焰\\n\\u007f😀\",\"i\":1,\"b\":false,\"n\":null,\"a\":[2,3]}");
            String golden = "{\"a\": [2, 3], \"b\": false, \"i\": 1, \"n\": null, \"s\": \"\\u7409\\u7130\\n\\u007f\\ud83d\\ude00\"}";
            equal(NativeProjectExeUac.sha(golden.getBytes(StandardCharsets.UTF_8)), NativeProjectExeUac.semanticSha(input));
        });
        check("argv-empty-argument-quoted", () -> equal("\"\"", NativeProjectExeUac.quote("")));
        check("argv-space-and-trailing-backslash-quoted", () -> equal("\"C:\\path with spaces\\tail\\\\\"", NativeProjectExeUac.quote("C:\\path with spaces\\tail\\")));
        check("argv-embedded-quote-escaped", () -> equal("\"a\\\"b\"", NativeProjectExeUac.quote("a\"b")));
        reject("argv-nul-rejected", () -> NativeProjectExeUac.quote("a\0b"));
        check("source-byte-drift-runs-production-verifier", () -> {
            Path source = fixtures.resolve("source-guard-synthetic.txt"); Files.writeString(source, "original", StandardOpenOption.CREATE_NEW);
            ControlBuild.FileRef original = ControlBuild.FileRef.measure(source);
            NativeProjectExeUac.verifySourceRefs(List.of(original));
            Files.writeString(source, "changed!");
            mustReject(() -> NativeProjectExeUac.verifySourceRefs(List.of(original)));
        });
        check("actual-readonly-native-file-identity-layout-and-handle-release", () -> {
            Path source = fixtures.resolve("native-guard-synthetic.txt"); Files.writeString(source, "synthetic-native-input", StandardOpenOption.CREATE_NEW);
            ControlBuild.FileRef original = ControlBuild.FileRef.measure(source);
            var guarded = NativeProjectExeUac.probeSoftwareNativeInput(original);
            if (!guarded.identity().volumeSerialDecimal().matches("0|[1-9][0-9]*")
                    || !guarded.identity().fileIdDecimal().matches("0|[1-9][0-9]*")
                    || !guarded.identity().sizeDecimal().equals(Long.toString(original.bytes())) || guarded.identity().directory())
                throw new AssertionError("actual native identity layout/decimal contract mismatch");
            Files.writeString(source, "released-handle-still-writable");
        });
        check("actual-current-process-token-readonly-layout-no-elevation", () -> {
            boolean observed = NativeProjectExeUac.probeCurrentTokenElevation();
            if (observed != NativeProjectExeUac.probeCurrentTokenElevation()) throw new AssertionError("current token changed within read-only software probe");
        });
        check("unknown-intent-remains-exclusive-and-original-bytes-readable", () -> {
            Path intentPath = fixtures.resolve("unknown-intent-synthetic.json");
            var intent = new NativeProjectExeUac.Intent("SYNTHETIC_INTENT_ONLY_NO_PLAN_OR_LAUNCH", "synthetic-machine", Instant.now().toString(),
                    null, List.of(), "UNKNOWN: do not resubmit");
            NativeProjectExeUac.claimIntent(intentPath, intent);
            byte[] original = Files.readAllBytes(intentPath);
            mustReject(() -> NativeProjectExeUac.claimIntent(intentPath, intent));
            if (!java.util.Arrays.equals(original, Files.readAllBytes(intentPath))) throw new AssertionError("exclusive intent was overwritten");
        });
        var cardExpected = new NativeProjectExeUac.RegisterCardExpectation("/root/native_fixture09", build04, fixtures, Instant.parse("2026-10-22T21:40:00Z"));
        ObjectNode card = JSON.createObjectNode();
        card.put("schema", "xar.shared-native-stage-resource-card/v1"); card.put("machine_id", "xenoamess-full-tower-eb9d2c1186");
        card.put("owner", "/root/native_fixture09"); card.put("allowed_stage", "REGISTER"); card.put("status", "ADMITTED_SINGLE_STAGE");
        card.put("timeout_seconds", 240); card.put("review_at_utc", "2026-10-22T21:50:00Z");
        card.putArray("output_roots").add(fixtures.toString()).add(FIXED_BUILD);
        check("exact-current-owner-card-runs-production-gate", () -> NativeProjectExeUac.qualifyRegisterCard(card, cardExpected));
        reject("legacy-owner-card-rejected-without-alias", () -> {
            ObjectNode changed = card.deepCopy(); changed.put("owner", "/root/native_fixture_execution");
            NativeProjectExeUac.qualifyRegisterCard(changed, cardExpected);
        });
        reject("missing-owner-card-rejected", () -> {
            ObjectNode changed = card.deepCopy(); changed.remove("owner"); NativeProjectExeUac.qualifyRegisterCard(changed, cardExpected);
        });
        reject("wrong-machine-card-rejected", () -> {
            ObjectNode changed = card.deepCopy(); changed.put("machine_id", "other-machine"); NativeProjectExeUac.qualifyRegisterCard(changed, cardExpected);
        });
        reject("register-card-budget-float-rejected", () -> {
            ObjectNode changed = card.deepCopy(); changed.put("timeout_seconds", 240.0); NativeProjectExeUac.qualifyRegisterCard(changed, cardExpected);
        });
        reject("register-card-lease-does-not-cover-plan", () -> {
            ObjectNode changed = card.deepCopy(); changed.put("review_at_utc", "2026-10-22T21:39:59Z"); NativeProjectExeUac.qualifyRegisterCard(changed, cardExpected);
        });
        reject("register-card-missing-build-root-rejected", () -> {
            ObjectNode changed = card.deepCopy(); changed.putArray("output_roots").add(fixtures.toString()); NativeProjectExeUac.qualifyRegisterCard(changed, cardExpected);
        });
        reject("register-card-missing-caller-output-root-rejected", () -> {
            ObjectNode changed = card.deepCopy(); changed.putArray("output_roots").add(FIXED_BUILD); NativeProjectExeUac.qualifyRegisterCard(changed, cardExpected);
        });
        check("plan-record-snake-case-serialization-roundtrip-actual-mapper", () -> {
            var synthetic = new NativeProjectExeUac.Plan("SYNTHETIC_INVALID_REGISTRATION_PLAN_NO_REVIEW_OR_LAUNCH",
                    "synthetic-machine", "2026-10-22T00:00:00Z", "2026-10-22T00:01:00Z", "synthetic-owner", 190, build04,
                    pin, pin, pin, pin, pin, pin, List.of(pin), List.of(new NativeProjectExeUac.SelectedExecutable(KINSHIP, pin)),
                    fixtures.toString(), "synthetic-receipt", "synthetic-intent", "synthetic-launch", "synthetic-result");
            JsonNode tree = JSON.valueToTree(synthetic);
            java.util.Set<String> fields = new java.util.HashSet<>(); tree.fieldNames().forEachRemaining(fields::add);
            equal(java.util.Set.of("schema", "machine_id", "observed_at_utc", "deadline_at_utc", "owner", "wait_seconds",
                    "native_build_root", "resource_card_ref", "manifest_ref", "build_actual_ref", "dependency_ref", "python_ref",
                    "helper_ref", "source_refs", "executables", "output_root", "helper_receipt_path", "intent_path",
                    "launch_observation_path", "result_path"), fields);
            equal(synthetic, NativeProjectExeUac.parsePlan(bytes(tree)));
            if (!tree.path("executables").get(0).has("file_ref")) throw new AssertionError("SelectedExecutable JSON contract changed");
            ObjectNode wrongAlias = ((ObjectNode) tree).deepCopy();
            wrongAlias.set("nativeBuildRoot", wrongAlias.remove("native_build_root"));
            mustReject(() -> NativeProjectExeUac.parsePlan(bytes(wrongAlias)));
        });
        check("direct-admin-proof-scope-serialization-cannot-claim-system", () -> {
            var qualified = NativeProjectExeUac.qualifyCompletion(terminal, interpreter, expected, raw, pin);
            JsonNode scope = JSON.valueToTree(qualified);
            equal("DIRECT_ADMIN_EXCLUSION_PATH", scope.path("proof_scope").textValue());
            ObjectNode forged = ((ObjectNode) scope).deepCopy(); forged.put("proof_scope", "SYSTEM");
            mustReject(() -> JSON.treeToValue(forged, NativeProjectExeUac.ReceiptQualification.class));
        });
        check("actual-shared-stage-deadline-matches-reviewed-plan", () -> NativeProjectExeUac.requireSharedStageDeadline("2026-10-22T21:40:00Z", "2026-10-22T21:40:00Z"));
        reject("actual-shared-stage-deadline-cannot-extend-plan", () -> NativeProjectExeUac.requireSharedStageDeadline("2026-10-22T21:40:00Z", "2026-10-22T21:40:01Z"));
        reject("actual-shared-stage-deadline-cannot-outlive-outer-stage", () -> NativeProjectExeUac.requireSharedStageDeadline("2026-10-22T21:40:01Z", "2026-10-22T21:40:00Z"));
        reject("missing-actual-shared-stage-deadline-rejected", () -> NativeProjectExeUac.requireSharedStageDeadline("2026-10-22T21:40:00Z", null));
        reject("source-empty-is-not-known-zero", () -> NativeProjectExeUac.verifySourceRefs(List.of()));

        Actual actual = new Actual("xar.native-uac-synthetic-regression/v2", WindowsJobProcess.currentMachineId(), Instant.now().toString(),
                "actual production pure methods and tiny synthetic files only; no valid registration Plan, native launch, UAC, Defender or fixture", passed.size(), 0,
                List.copyOf(passed), 0, 0, 0);
        Files.write(report, JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(actual), StandardOpenOption.CREATE_NEW);
        System.out.println("PASS synthetic_cases=" + passed.size() + " UAC=0 Defender=0 NativeFixture=0");
    }

    @FunctionalInterface private interface Mutation { void apply(ObjectNode value); }
    private static void rejectReceipt(String name, ObjectNode original, Path fixtures,
            NativeProjectExeUac.TerminalProof terminal, String interpreter,
            NativeProjectExeUac.ReceiptExpectation expected, Mutation mutation) throws Exception {
        reject(name, () -> { ObjectNode changed = original.deepCopy(); mutation.apply(changed);
            byte[] raw = bytes(changed); qualify(terminal, interpreter, expected, raw, pin(fixtures, raw)); });
    }
    private static void qualify(NativeProjectExeUac.TerminalProof terminal, String interpreter,
            NativeProjectExeUac.ReceiptExpectation expected, byte[] raw, ControlBuild.FileRef pin) throws IOException {
        NativeProjectExeUac.qualifyCompletion(terminal, interpreter, expected, raw, pin);
    }
    private static ObjectNode manifest() throws IOException {
        ObjectNode value = JSON.createObjectNode(); value.put("fixture_only", "SYNTHETIC_NO_REAL_PLAN_OR_SOURCE_AUTHORITY");
        ArrayNode rows = value.putArray("files");
        for (String target : List.of(KINSHIP, COMBAT)) {
            ObjectNode row = rows.addObject(); row.put("path", FIXED_BUILD + "/bin/" + target + ".exe"); row.put("size", 7);
            row.put("sha256", NativeProjectExeUac.sha(target.getBytes(StandardCharsets.UTF_8))); row.put("target", target); row.put("target_id", "synthetic-" + target);
        }
        return value;
    }
    private static ObjectNode receipt(NativeProjectExeUac.ReceiptExpectation expected) {
        ObjectNode value = JSON.createObjectNode(); value.put("schema", "xar.project-exe-exclusions.v1"); value.put("status", "verified");
        value.put("admin_token", true); value.put("settings_success_is_runtime_trust", false); value.put("manifest_sha256", expected.manifestSemanticSha256());
        value.set("files", JSON.valueToTree(expected.files())); value.putArray("before").add("C:/synthetic-previous.exe");
        ArrayNode after = value.putArray("after"); after.add("C:/synthetic-previous.exe"); expected.files().forEach(row -> after.add(row.path()));
        ArrayNode verified = value.putArray("verified_requested_paths"); expected.files().forEach(row -> verified.add(row.path()));
        value.putArray("missing_requested_paths"); value.put("observed_prior_settings_preserved", true); value.put("partial_mutation", false);
        return value;
    }
    private static byte[] bytes(JsonNode value) throws IOException { return JSON.writeValueAsBytes(value); }
    private static ControlBuild.FileRef pin(Path fixtures, byte[] raw) { return new ControlBuild.FileRef(fixtures.resolve("synthetic-in-memory-receipt-not-real.json").toString(), raw.length, NativeProjectExeUac.sha(raw)); }
    private static void equal(Object expected, Object actual) { if (!java.util.Objects.equals(expected, actual)) throw new AssertionError("expected=" + expected + " actual=" + actual); }
    private static void check(String name, Checked body) throws Exception { body.run(); passed.add(name); }
    private static void reject(String name, Checked body) throws Exception { mustReject(body); passed.add(name); }
    private static void mustReject(Checked body) throws Exception {
        try { body.run(); } catch (IOException | IllegalArgumentException expected) { return; }
        throw new AssertionError("production boundary incorrectly accepted malformed/unknown input");
    }
}

