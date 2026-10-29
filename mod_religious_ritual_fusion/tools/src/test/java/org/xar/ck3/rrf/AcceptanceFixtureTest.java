package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.rrf.acceptance.FixtureContracts;
import org.xar.ck3.rrf.acceptance.FixtureContracts.ActorHistoryId;
import org.xar.ck3.rrf.acceptance.FixtureContracts.CaseKind;
import org.xar.ck3.rrf.acceptance.FixtureContracts.FreshSetup;
import org.xar.ck3.rrf.acceptance.FixtureContracts.Mode;
import org.xar.ck3.rrf.acceptance.FixtureContracts.Request;
import org.xar.ck3.rrf.acceptance.FixtureContracts.SavedSetup;
import org.xar.ck3.rrf.acceptance.FixtureEmitter;

final class AcceptanceFixtureTest {
    private static final ExpectedSelection DEFAULT_SELECTION = new ExpectedSelection(List.of(new ExpectedSelection.TenetKey("tenet_esotericism"), new ExpectedSelection.TenetKey("tenet_astrology"), new ExpectedSelection.TenetKey("tenet_communal_identity")));
    private static final ActorHistoryId ROBERT = new ActorHistoryId("1128");
    @TempDir Path directory;
    @Test void versionFourColdSnapshotBindsActualWalletHistoryAndStaysAnEightFileReadOnlyFixture() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        var setup = coldEvidence(repository, "wallet", "5400");
        // Historical checkpoints may have been overwritten; their retained reports remain the inputs.
        for (FixtureContracts.FilePin history : List.of(setup.creationHistory().beforeInspection(), setup.creationHistory().afterInspection())) {
            var original = org.xar.ck3.save.SaveJson.read(Files.readAllBytes(Path.of(history.path())), org.xar.ck3.save.Inspection.Report.class);
            Files.delete(Path.of(original.decoded().save().path()));
        }
        Request request = new Request(4, CaseKind.COLD_RELOAD, Mode.RITE, ROBERT, setup, DEFAULT_SELECTION);
        assertEquals(request, Json.read(Json.write(request), Request.class));
        FixtureEmitter.Emission emitted = FixtureEmitter.emit(repository, directory.resolve("cold-wallet"), "synthetic-fixture-machine", request);
        assertEquals(8, emitted.payload().files().size());
        assertFalse(emitted.payload().receipt().containsBusinessEffects());
        assertTrue(emitted.payload().files().keySet().stream().noneMatch(n -> n.contains("seed") || n.contains("on_action") || n.contains("fresh")));
        String observed = Files.readString(emitted.fixture().resolve("common/scripted_triggers/rrfa_observation_triggers.txt"));
        assertTrue(observed.contains("piety = 5400\n    var:rrfa_piety_before = 6000"));
        assertTrue(observed.contains("var:rrf_charged_cost = 500"));
        assertFalse(observed.contains("piety = rrfa_expected_post_piety_value"));
        assertReadOnly(keys(Clausewitz.parse(observed)));
        var bound = org.xar.ck3.rrf.acceptance.FrozenFixtureReader.read(manifestPin(emitted.manifest()), emitted.payload().machineId(), repository);
        assertEquals(request, bound.request());
        Path receipt = Path.of(emitted.fixture() + ".inputs.json");
        var inputs = Json.read(Files.readAllBytes(receipt), FixtureContracts.PrebuiltInputs.class);
        assertEquals(manifestPin(emitted.manifest()), inputs.manifest());
        assertEquals(manifestPin(emitted.fixture().resolve(FixtureContracts.REQUEST_FILE)), inputs.request());
        assertEquals(org.xar.ck3.rrf.acceptance.ColdSnapshotReader.inputPins(request), inputs.inputPins());
        byte[] receiptBytes = Files.readAllBytes(receipt);
        Files.delete(receipt);
        assertThrows(IOException.class, () -> org.xar.ck3.rrf.acceptance.FrozenFixtureReader.read(manifestPin(emitted.manifest()), emitted.payload().machineId(), repository));
        Files.write(receipt, receiptBytes);
        assertTrue(emitted.payload().producerSourcePins().stream().anyMatch(p -> p.path().endsWith("ColdSnapshotReader.java")));
        // A detached, subsequently edited V4 report is not accepted by the real frozen consumer.
        Path report = Path.of(setup.sourceInspection().path()); byte[] original = Files.readAllBytes(report);
        Files.writeString(report, Files.readString(report) + " ");
        assertThrows(IOException.class, () -> org.xar.ck3.rrf.acceptance.FrozenFixtureReader.read(manifestPin(emitted.manifest()), emitted.payload().machineId(), repository));
        Files.write(report, original);
        var wrong = new FixtureContracts.SavedSnapshotSetup(setup.actorId(), setup.sourceSave(), setup.sourceInspection(), new FixtureContracts.PietyAmount("5500"), setup.creationHistory());
        assertThrows(IOException.class, () -> FixtureEmitter.emit(repository, directory.resolve("wrong-cold-wallet"), "synthetic-fixture-machine", new Request(4, CaseKind.COLD_RELOAD, Mode.RITE, ROBERT, wrong, DEFAULT_SELECTION)));
        assertFalse(Files.exists(directory.resolve("wrong-cold-wallet")));
        Files.writeString(Path.of(setup.sourceSave().path()), "changed source");
        assertThrows(IOException.class, () -> org.xar.ck3.rrf.acceptance.FrozenFixtureReader.read(manifestPin(emitted.manifest()), emitted.payload().machineId(), repository));
        FixtureEmitter.Emission legacy = FixtureEmitter.emit(repository, directory.resolve("legacy-cold-wallet"), "synthetic-fixture-machine", bundledRequest(repository, "cold-rite"));
        assertTrue(Files.readString(legacy.fixture().resolve("common/scripted_triggers/rrfa_observation_triggers.txt")).contains("piety = rrfa_expected_post_piety_value"));
    }
    @Test void coldSnapshotVersionsTypesHistoryAndCrossedObservationsAreRejected() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        var setup = coldEvidence(repository, "strict-wallet", "5400.25");
        Request request = new Request(4, CaseKind.COLD_RELOAD, Mode.RITE, ROBERT, setup, DEFAULT_SELECTION);
        String json = new String(Json.write(request), StandardCharsets.UTF_8);
        assertEquals(request, Json.read(json.getBytes(StandardCharsets.UTF_8), Request.class));
        for (String invalid : List.of(json.replace("\"schemaVersion\" : 4", "\"schemaVersion\" : 3"),
                json.replace("\"cold_reload\"", "\"core\""), json.replace("\"rite\"", "\"faith\""),
                json.replace("\"expectedCurrentPiety\"", "\"unknownWallet\""), json.replace("\"5400.25\"", "5400.25"),
                json.replace("\"expectedCurrentPiety\" : \"5400.25\",", ""),
                json.replace("\"5400.25\"", "true"), json.replace("\"5400.25\"", "null"), json.replace("\"5400.25\"", "\"05400.25\""),
                json.replace("\"chargedCost\" : 500", "\"chargedCost\" : 500.0"),
                json.replace("\"chargedCost\" : 500", "\"chargedCost\" : true"),
                json.replace("\"chargedCost\" : 500", "\"chargedCost\" : 400")))
            assertThrows(IOException.class, () -> Json.read(invalid.getBytes(StandardCharsets.UTF_8), Request.class));
        for (String invalid : List.of("5400.0", "-0", "1e3", "NaN", "5400 # injected", "1000001", "-1000001"))
            assertThrows(IllegalArgumentException.class, () -> new FixtureContracts.PietyAmount(invalid));
        assertThrows(IOException.class, () -> FixtureEmitter.emit(repository, directory.resolve("wrong-machine-wallet"), "different-machine", request));
        var crossed = new FixtureContracts.SavedSnapshotSetup(new org.xar.ck3.save.SaveContracts.NativeId("31255"), setup.sourceSave(), setup.sourceInspection(), setup.expectedCurrentPiety(), setup.creationHistory());
        assertThrows(IOException.class, () -> FixtureEmitter.emit(repository, directory.resolve("wrong-actor-wallet"), "synthetic-fixture-machine", new Request(4, CaseKind.COLD_RELOAD, Mode.RITE, ROBERT, crossed, DEFAULT_SELECTION)));
        FixtureEmitter.emit(repository, directory.resolve("fractional-wallet"), "synthetic-fixture-machine", request);
    }
    @Test void signedCurrentWalletAndOmittedCreationZeroCrossTheActualFrozenFixtureReader() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        var setup = faithColdEvidence(repository, "signed-wallet", "piety={currency=-0.4 accumulated=1850}", "-0.4");
        Request request = new Request(4, CaseKind.COLD_RELOAD, Mode.FAITH, ROBERT, setup,
                bundledRequest(repository, "cold-faith-four").expectedSelection());
        assertEquals(request, Json.read(Json.write(request), Request.class));
        byte[] afterBytes = Files.readAllBytes(Path.of(setup.creationHistory().afterInspection().path()));
        var after = org.xar.ck3.save.SaveJson.read(afterBytes, org.xar.ck3.save.Inspection.Report.class);
        var actor = after.decoded().projection().scopes().stream()
                .filter(scope -> scope.kind() == org.xar.ck3.save.SaveContracts.ScopeKind.ACTOR).findFirst().orElseThrow().ast();
        assertTrue(actor.block("alive_data").block("piety").named("currency").isEmpty());
        assertEquals("1850", actor.block("alive_data").block("piety").atom("accumulated", ""));
        var emitted = FixtureEmitter.emit(repository, directory.resolve("signed-current-fixture"), "synthetic-fixture-machine", request);
        assertEquals(8, emitted.payload().files().size());
        String trigger = Files.readString(emitted.fixture().resolve("common/scripted_triggers/rrfa_observation_triggers.txt"));
        assertTrue(trigger.contains("piety = -0.4\n    var:rrfa_piety_before = 1000"));
        assertTrue(trigger.contains("var:rrf_charged_cost = 1000"));
        assertReadOnly(keys(Clausewitz.parse(trigger)));
        var bound = org.xar.ck3.rrf.acceptance.FrozenFixtureReader.read(manifestPin(emitted.manifest()), "synthetic-fixture-machine", repository);
        assertEquals(request, bound.request());
        var inputs = Json.read(Files.readAllBytes(Path.of(emitted.fixture() + ".inputs.json")), FixtureContracts.PrebuiltInputs.class);
        assertEquals(org.xar.ck3.rrf.acceptance.ColdSnapshotReader.inputPins(request), inputs.inputPins());
        assertTrue(inputs.inputPins().contains(setup.creationHistory().afterInspection()));
        assertArrayEquals(afterBytes, Files.readAllBytes(Path.of(setup.creationHistory().afterInspection().path())));
        for (String wrong : List.of("0", "-0.40001")) {
            var crossed = new FixtureContracts.SavedSnapshotSetup(setup.actorId(), setup.sourceSave(), setup.sourceInspection(),
                    new FixtureContracts.PietyAmount(wrong), setup.creationHistory());
            Path output = directory.resolve("wrong-signed-" + wrong);
            assertThrows(IOException.class, () -> FixtureEmitter.emit(repository, output, "synthetic-fixture-machine",
                    new Request(4, CaseKind.COLD_RELOAD, Mode.FAITH, ROBERT, crossed, request.expectedSelection())));
            assertFalse(Files.exists(output));
        }
        for (String zero : List.of("piety={accumulated=1850}", "piety={}")) {
            var zeroSetup = faithColdEvidence(repository, "zero-" + zero.length(), zero, "0");
            FixtureEmitter.emit(repository, directory.resolve("zero-fixture-" + zero.length()), "synthetic-fixture-machine",
                    new Request(4, CaseKind.COLD_RELOAD, Mode.FAITH, ROBERT, zeroSetup, request.expectedSelection()));
        }
    }
    @Test void signedWalletCanonicalStringsDoNotRelaxNonnegativeCreationHistoryOrItsSingleBill() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        var setup = faithColdEvidence(repository, "history-sign", "piety={currency=-0.4}", "-0.4");
        for (String amount : List.of("-0.4", "-1", "0", "1000000", "-1000000", "-0.00001")) {
            var value = new FixtureContracts.PietyAmount(amount);
            var snapshot = new FixtureContracts.SavedSnapshotSetup(setup.actorId(), setup.sourceSave(), setup.sourceInspection(), value, setup.creationHistory());
            Request request = new Request(4, CaseKind.COLD_RELOAD, Mode.FAITH, ROBERT, snapshot, DEFAULT_SELECTION);
            assertEquals(request, Json.read(Json.write(request), Request.class));
        }
        for (String invalid : List.of("-0", "-0.0", "-01", "+1", "--1", "-1.0", "-0.400000", "-1000001", "-1000000.00001", "NaN", "1e3"))
            assertThrows(IllegalArgumentException.class, () -> new FixtureContracts.PietyAmount(invalid));
        String serialized = new String(Json.write(new Request(4, CaseKind.COLD_RELOAD, Mode.FAITH, ROBERT, setup, DEFAULT_SELECTION)), StandardCharsets.UTF_8);
        for (String invalidJson : List.of("-0.4", "true", "null", "{}", "[]")) {
            String invalid = serialized.replace("\"expectedCurrentPiety\" : \"-0.4\"", "\"expectedCurrentPiety\" : " + invalidJson);
            assertFalse(invalid.equals(serialized));
            assertThrows(IOException.class, () -> Json.read(invalid.getBytes(StandardCharsets.UTF_8), Request.class));
        }
        var before = setup.creationHistory().beforeInspection(); var after = setup.creationHistory().afterInspection();
        for (List<String> pair : List.of(List.of("-1", "-1001"), List.of("0", "-1000")))
            assertThrows(IllegalArgumentException.class, () -> new FixtureContracts.CreationWalletHistory(
                    new FixtureContracts.PietyAmount(pair.getFirst()), new FixtureContracts.PietyAmount(pair.getLast()), 1000, before, after));
        for (int wrong : List.of(0, 500, 1001))
            assertThrows(IllegalArgumentException.class, () -> new FixtureContracts.CreationWalletHistory(
                    new FixtureContracts.PietyAmount("1000"), new FixtureContracts.PietyAmount("0"), wrong, before, after));
        assertThrows(IllegalArgumentException.class, () -> new Request(4, CaseKind.COLD_RELOAD, Mode.RITE, ROBERT, setup, DEFAULT_SELECTION));
    }
    @Test void omittedCurrencyRequiresAnExistingUniqueWalletBlockAndExplicitCurrencyRemainsStrict() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        // These two expressions are invalid save ASTs and are rejected by the
        // actual inspection parser before a V4 report can reach the wallet reader.
        for (String invalidSyntax : List.of("piety>= {}", "piety={currency>=0}"))
            assertThrows(IOException.class, () -> faithColdEvidence(repository, "invalid-wallet-syntax-" + invalidSyntax.length(), invalidSyntax, "0"));
        List<String> malformed = List.of("", "piety=0", "piety={} piety={}", "piety={currency={}}",
                "piety={currency=0 currency=0}", "piety={currency=true}",
                "piety={currency=\"0\"}", "piety={currency=-0}", "piety={currency=0.0}", "piety={currency=1e3}");
        for (int index = 0; index < malformed.size(); index++) {
            var setup = faithColdEvidence(repository, "malformed-wallet-" + index, malformed.get(index), "0");
            Path output = directory.resolve("malformed-wallet-fixture-" + index);
            assertThrows(IOException.class, () -> FixtureEmitter.emit(repository, output, "synthetic-fixture-machine",
                    new Request(4, CaseKind.COLD_RELOAD, Mode.FAITH, ROBERT, setup, DEFAULT_SELECTION)));
            assertFalse(Files.exists(output));
        }
    }
    @Test void completedSnapshotKeepsCurrentAndHistoricalDivorceSeparateAcrossSerdeAndFrozenReader() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        List<String> origin = completedOrigin();
        assertEquals(24, origin.size());
        var setup = completedEvidence(repository, "completed", origin, origin, true, true);
        Request request = new Request(5, CaseKind.COLD_RELOAD, Mode.FAITH, ROBERT, setup, bundledRequest(repository, "cold-faith-four").expectedSelection());
        assertEquals(request, Json.read(Json.write(request), Request.class));
        var rules = org.xar.ck3.rrf.acceptance.ColdSnapshotReader.verifiedDivorceRules(request, "synthetic-fixture-machine", repository);
        assertEquals(FixtureContracts.DivorceRule.ALLOWED, rules.result());
        assertEquals(FixtureContracts.DivorceRule.DISALLOWED, rules.origin());
        var emitted = FixtureEmitter.emit(repository, directory.resolve("completed-fixture"), "synthetic-fixture-machine", request);
        assertEquals(8, emitted.payload().files().size());
        String trigger = Files.readString(emitted.fixture().resolve("common/scripted_triggers/rrfa_observation_triggers.txt"));
        assertTrue(trigger.contains("rite_has_doctrine = doctrine_divorce_allowed"));
        assertTrue(trigger.contains("name = rrf_origin_doctrines target = doctrine:doctrine_divorce_disallowed"));
        assertTrue(trigger.contains("piety = -0.4"));
        assertTrue(trigger.contains("var:rrf_charged_cost = 1000"));
        assertTrue(trigger.contains("has_character_flag = rrf_fusion_cooldown"));
        assertTrue(trigger.contains("variable_list_size = { name = rrf_origin_core_tenets value = 4 }"));
        assertReadOnly(keys(Clausewitz.parse(trigger)));
        assertEquals(request, org.xar.ck3.rrf.acceptance.FrozenFixtureReader.read(manifestPin(emitted.manifest()), "synthetic-fixture-machine", repository).request());
        var inputs = Json.read(Files.readAllBytes(Path.of(emitted.fixture() + ".inputs.json")), FixtureContracts.PrebuiltInputs.class);
        assertEquals(org.xar.ck3.rrf.acceptance.ColdSnapshotReader.inputPins(request), inputs.inputPins());
        for (int version : List.of(3, 4))
            assertThrows(IllegalArgumentException.class, () -> new Request(version, CaseKind.COLD_RELOAD, Mode.FAITH, ROBERT, setup, request.expectedSelection()));
        var legacySetup = new FixtureContracts.SavedSnapshotSetup(setup.actorId(), setup.sourceSave(), setup.sourceInspection(), setup.expectedCurrentPiety(), setup.creationHistory());
        assertThrows(IllegalArgumentException.class, () -> new Request(5, CaseKind.COLD_RELOAD, Mode.FAITH, ROBERT, legacySetup, request.expectedSelection()));
    }
    @Test void completedSnapshotRejectsMissingFullRiteAndChangedOrDuplicateOriginWithoutStrengtheningVersionFour() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        List<String> origin = completedOrigin();
        for (boolean afterRite : List.of(false, true)) {
            var setup = completedEvidence(repository, "missing-rite-" + afterRite, origin, origin, afterRite, !afterRite);
            assertThrows(IOException.class, () -> FixtureEmitter.emit(repository, directory.resolve("missing-rite-fixture-" + afterRite), "synthetic-fixture-machine",
                    new Request(5, CaseKind.COLD_RELOAD, Mode.FAITH, ROBERT, setup, DEFAULT_SELECTION)));
            var legacy = new FixtureContracts.SavedSnapshotSetup(setup.actorId(), setup.sourceSave(), setup.sourceInspection(), setup.expectedCurrentPiety(), setup.creationHistory());
            FixtureEmitter.emit(repository, directory.resolve("legacy-no-new-rite-requirement-" + afterRite), "synthetic-fixture-machine",
                    new Request(4, CaseKind.COLD_RELOAD, Mode.FAITH, ROBERT, legacy, DEFAULT_SELECTION));
        }
        List<String> reversed = new ArrayList<>(origin); java.util.Collections.reverse(reversed);
        List<String> duplicate = new ArrayList<>(origin); duplicate.add(origin.getFirst());
        for (List<String> changed : List.of(reversed, duplicate)) {
            var setup = completedEvidence(repository, "origin-" + changed.size(), origin, changed, true, true);
            assertThrows(IOException.class, () -> FixtureEmitter.emit(repository, directory.resolve("wrong-origin-" + changed.size()), "synthetic-fixture-machine",
                    new Request(5, CaseKind.COLD_RELOAD, Mode.FAITH, ROBERT, setup, DEFAULT_SELECTION)));
        }
        var setup = completedEvidence(repository, "coverage", origin, origin, true, true);
        for (String defect : List.of("selection", "coverage", "status", "id")) {
            JsonNode json = Json.read(Files.readAllBytes(Path.of(setup.sourceInspection().path())), JsonNode.class);
            String pointer = defect.equals("selection") ? "/request/selection/tables" : defect.equals("coverage") ? "/decoded/projection/scopes" : "/decoded/projection/records";
            for (JsonNode row : json.at(pointer)) {
                if (!row.path("kind").asText().equals("RITE")) continue;
                if (!(row instanceof com.fasterxml.jackson.databind.node.ObjectNode object)) throw new AssertionError("typed report row required");
                switch (defect) {
                    case "selection" -> object.set("ids", object.arrayNode().add("156"));
                    case "coverage" -> object.put("coverage", "DIRECT_SCALARS");
                    case "status" -> object.put("status", "NOT_FOUND");
                    case "id" -> object.put("id", "156");
                    default -> throw new AssertionError(defect);
                }
            }
            Path malformed = directory.resolve("coverage-" + defect + ".json"); Files.write(malformed, Json.write(json));
            var crossed = new FixtureContracts.CompletedSnapshotSetup(setup.actorId(), setup.sourceSave(), manifestPin(malformed), setup.expectedCurrentPiety(), setup.creationHistory());
            assertThrows(IOException.class, () -> FixtureEmitter.emit(repository, directory.resolve("coverage-fixture-" + defect), "synthetic-fixture-machine",
                    new Request(5, CaseKind.COLD_RELOAD, Mode.FAITH, ROBERT, crossed, DEFAULT_SELECTION)));
        }
    }
    private static List<String> completedOrigin() {
        List<String> keys = new ArrayList<>(List.of("doctrine_divorce_disallowed", "doctrine_monogamy"));
        for (int index = 2; index < 24; index++) keys.add("doctrine_authored_origin_" + index);
        return List.copyOf(keys);
    }
    private FixtureContracts.CompletedSnapshotSetup completedEvidence(Path repository, String name, List<String> afterOrigin,
            List<String> currentOrigin, boolean afterRite, boolean currentRite) throws IOException {
        var before = coldReport(repository, name + "-before", "piety={currency=1000}", false, 1000, 1000, 155);
        var after = coldReport(repository, name + "-after", "piety={accumulated=1850}", true, 1000, 1000, 155, completedRite(afterOrigin, false), afterRite);
        var current = coldReport(repository, name + "-current", "piety={currency=-0.4}", true, 1000, 1000, 155, completedRite(currentOrigin, true), currentRite);
        var source = org.xar.ck3.save.SaveJson.read(Files.readAllBytes(Path.of(current.path())), org.xar.ck3.save.Inspection.Report.class).decoded().save();
        return new FixtureContracts.CompletedSnapshotSetup(new org.xar.ck3.save.SaveContracts.NativeId("31254"),
                new FixtureContracts.FilePin(source.path(), source.bytes(), source.sha256()), current, new FixtureContracts.PietyAmount("-0.4"),
                new FixtureContracts.CreationWalletHistory(new FixtureContracts.PietyAmount("1000"), new FixtureContracts.PietyAmount("0"), 1000, before, after));
    }
    private static String completedRite(List<String> origin, boolean completed) {
        StringBuilder items = new StringBuilder();
        for (String key : origin) items.append("item={type=doctrine key=\"").append(key).append("\"}");
        return " rites={database={155={data={doctrine=\"doctrine_divorce_" + (completed ? "allowed" : "disallowed")
                + "\"} variables={list={{name=\"rrf_origin_doctrines\" " + items + "}}}}}}";
    }
    private FixtureContracts.SavedSnapshotSetup faithColdEvidence(Path repository, String name, String currentWallet, String expectedCurrent) throws IOException {
        FixtureContracts.FilePin before = coldReport(repository, name + "-before", "piety={currency=1000 accumulated=1850}", false, 1000, 1000, 155);
        FixtureContracts.FilePin after = coldReport(repository, name + "-after", "piety={accumulated=1850}", true, 1000, 1000, 155);
        FixtureContracts.FilePin observed = coldReport(repository, name + "-current", currentWallet, true, 1000, 1000, 155);
        var source = org.xar.ck3.save.SaveJson.read(Files.readAllBytes(Path.of(observed.path())), org.xar.ck3.save.Inspection.Report.class).decoded().save();
        return new FixtureContracts.SavedSnapshotSetup(new org.xar.ck3.save.SaveContracts.NativeId("31254"),
                new FixtureContracts.FilePin(source.path(), source.bytes(), source.sha256()), observed, new FixtureContracts.PietyAmount(expectedCurrent),
                new FixtureContracts.CreationWalletHistory(new FixtureContracts.PietyAmount("1000"), new FixtureContracts.PietyAmount("0"), 1000, before, after));
    }
    private FixtureContracts.SavedSnapshotSetup coldEvidence(Path repository, String name, String current) throws IOException {
        FixtureContracts.FilePin before = coldReport(repository, name + "-before", "6000", false);
        FixtureContracts.FilePin after = coldReport(repository, name + "-after", "5500", true);
        FixtureContracts.FilePin observed = coldReport(repository, name + "-current", current, true);
        var report = org.xar.ck3.save.SaveJson.read(Files.readAllBytes(Path.of(observed.path())), org.xar.ck3.save.Inspection.Report.class);
        var source = report.decoded().save();
        return new FixtureContracts.SavedSnapshotSetup(new org.xar.ck3.save.SaveContracts.NativeId("31254"),
                new FixtureContracts.FilePin(source.path(), source.bytes(), source.sha256()), observed, new FixtureContracts.PietyAmount(current),
                new FixtureContracts.CreationWalletHistory(new FixtureContracts.PietyAmount("6000"), new FixtureContracts.PietyAmount("5500"), 500, before, after));
    }
    private FixtureContracts.FilePin coldReport(Path repository, String name, String piety, boolean created) throws IOException {
        return coldReport(repository, name, "piety={currency=" + piety + "}", created, 6000, 500, 153);
    }
    private FixtureContracts.FilePin coldReport(Path repository, String name, String wallet, boolean created, int before, int cost, int result) throws IOException {
        return coldReport(repository, name, wallet, created, before, cost, result, "", false);
    }
    private FixtureContracts.FilePin coldReport(Path repository, String name, String wallet, boolean created, int before, int cost, int result, String rites, boolean selectRite) throws IOException {
        String data = "{flag=\"rrfa_piety_before\" data={type=value identity=" + before * 100000L + "}}"
                + (created ? "{flag=\"rrf_charged_cost\" data={type=value identity=" + cost * 100000L + "}}{flag=\"rrf_last_result_rite\" data={type=rite identity=" + result + "}}" : "");
        String text = "meta_data={version=\"1.20.0.4\"} playthrough_id=\"authored-wallet-campaign\" date=1066.9.17 living={31254={rite="
                + (created ? Integer.toString(result) : "150") + " alive_data={" + wallet + " variables={data={" + data + "}}}}}" + rites;
        Path save = directory.resolve(name + ".ck3"); Files.writeString(save, text);
        List<org.xar.ck3.save.SaveContracts.TableSelection> tables = new ArrayList<>();
        tables.add(new org.xar.ck3.save.SaveContracts.TableSelection(org.xar.ck3.save.SaveContracts.ScopeKind.ACTOR, List.of("living"), List.of(new org.xar.ck3.save.SaveContracts.NativeId("31254")), true));
        if (selectRite) tables.add(new org.xar.ck3.save.SaveContracts.TableSelection(org.xar.ck3.save.SaveContracts.ScopeKind.RITE, List.of("rites", "database"), List.of(new org.xar.ck3.save.SaveContracts.NativeId(Integer.toString(result))), true));
        var selected = new org.xar.ck3.save.SaveContracts.Selection(tables, List.of(), true, false, List.of());
        var pin = org.xar.ck3.save.FilePins.pin(save);
        var request = new org.xar.ck3.save.Inspection.Request(4, "synthetic-fixture-machine", repository.toString(), pin, pin, selected);
        var projection = new org.xar.ck3.save.SaveStream(new java.io.StringReader(text), selected).read();
        var decoded = new org.xar.ck3.save.SaveContracts.Decoded(pin, pin, 0, "", org.xar.ck3.save.FilePins.sha256(text.getBytes(StandardCharsets.UTF_8)), Integer.toString(text.getBytes(StandardCharsets.UTF_8).length), projection, true);
        // Explicitly authored observation; this exercises the shared AST/typed report reader, not a live decoder claim.
        var report = new org.xar.ck3.save.Inspection.Report("ck3-save-inspection-v4", request.machineId(), "2026-10-27T00:00:00Z", request, decoded,
                org.xar.ck3.save.ProducerSources.verify(repository), org.xar.ck3.save.Inspection.BusinessAssessment.NOT_ASSESSED, false);
        Path target = directory.resolve(name + ".report.json"); Files.write(target, org.xar.ck3.save.SaveJson.write(report));
        return manifestPin(target);
    }
    @Test void longDisplayNameInputIsFreshOnlyAndCrossesFrozenFixtureReader() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        for (String recipe : List.of("core-rite", "core-faith-four", "ui-rejection", "cold-rite")) {
            Request request = bundledRequest(repository, recipe);
            FixtureEmitter.Emission emitted = FixtureEmitter.emit(repository, directory.resolve("long-name-" + recipe), "synthetic-fixture-machine", request);
            org.xar.ck3.rrf.acceptance.FrozenFixtureReader.read(manifestPin(emitted.manifest()), emitted.payload().machineId(), repository);
            Path seed = emitted.fixture().resolve("common/scripted_effects/rrfa_seed_effects.txt");
            if (request.kind() == CaseKind.COLD_RELOAD) {
                assertFalse(Files.exists(seed));
                for (String relative : emitted.payload().files().keySet()) {
                    if (relative.endsWith(".txt")) assertFalse(keys(Clausewitz.parse(Files.readString(emitted.fixture().resolve(relative)))).contains("change_first_name"));
                }
            } else {
                List<String> seedKeys = keys(Clausewitz.parse(Files.readString(seed)));
                assertEquals(1, seedKeys.stream().filter("change_first_name"::equals).count());
                assertEquals(1, seedKeys.stream().filter("random_vassal"::equals).count());
                assertTrue(Files.readString(seed).contains("value = scope:rrfa_long_name_vassal"));
                for (String language : List.of("english", "simp_chinese")) {
                    String loc = Files.readString(emitted.fixture().resolve("localization/" + language + "/rrfa_observation_l_" + language + ".yml"));
                    assertTrue(loc.contains("rrfa_fixture_long_vassal_name:0"));
                }
            }
        }
    }
    @Test void sharedParserProducerPinsCannotBeRemovedFromFrozenFixture() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        FixtureEmitter.Emission emitted = FixtureEmitter.emit(repository, directory.resolve("shared-source-fixture"), "synthetic-fixture-machine", bundledRequest(repository, "core-rite"));
        FixtureContracts.Manifest original = emitted.payload();
        assertTrue(original.producerSourcePins().stream().anyMatch(p -> p.path().replace((char) 92, '/').contains("java/ck3-save-core/")));
        org.xar.ck3.rrf.acceptance.FrozenFixtureReader.read(manifestPin(emitted.manifest()), original.machineId(), repository);
        List<FixtureContracts.FilePin> omitted = original.producerSourcePins().stream()
                .filter(p -> !p.path().replace((char) 92, '/').contains("java/ck3-save-core/")).toList();
        FixtureContracts.Manifest changed = new FixtureContracts.Manifest(original.schema(), original.product(), original.caseId(), original.machineId(),
                original.observedAtUtc(), original.fixtureRoot(), omitted, original.files(), original.receipt());
        Files.write(emitted.manifest(), Json.write(changed));
        assertThrows(IOException.class, () -> org.xar.ck3.rrf.acceptance.FrozenFixtureReader.read(manifestPin(emitted.manifest()), original.machineId(), repository));
    }
    private static FixtureContracts.FilePin manifestPin(Path path) throws IOException {
        return new FixtureContracts.FilePin(path.toRealPath().toString(), Files.size(path), ReleaseBuilder.sha256(Files.readAllBytes(path)));
    }
    @Test void realFixtureProducerCreatesExactSourcePinnedPublicImportAndReadOnlyObservations() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        Request request = bundledRequest(repository, "core-rite");
        FixtureEmitter.Emission emitted = FixtureEmitter.emit(repository, directory.resolve("fixture"), "synthetic-fixture-machine", request);
        FixtureContracts.Manifest decoded = Json.read(Files.readAllBytes(emitted.manifest()), FixtureContracts.Manifest.class);
        assertEquals(decoded, emitted.payload()); assertEquals(11, decoded.files().size());
        assertEquals(request, Json.read(Files.readAllBytes(emitted.requestSnapshot()), Request.class));
        assertEquals(List.of("RRFAT: TEST PASS fixture_ready", "RRFAT: TEST PASS rite_success_readback"), decoded.receipt().requiredMarkers());
        for (FixtureContracts.FilePin pin : decoded.producerSourcePins()) {
            assertTrue(Path.of(pin.path()).startsWith(repository));
            assertEquals(pin.sha256(), ReleaseBuilder.sha256(Files.readAllBytes(Path.of(pin.path()))));
        }
        assertEquals(decoded.files().keySet(), ContentValidator.inventory(emitted.fixture(), true).keySet());
        List<String> allKeys = new ArrayList<>();
        for (String relative : decoded.files().keySet()) {
            byte[] bytes = Files.readAllBytes(emitted.fixture().resolve(relative));
            assertEquals(decoded.files().get(relative).sha256(), ReleaseBuilder.sha256(bytes));
            String text = new String(bytes, StandardCharsets.UTF_8); assertFalse(text.contains("${"));
            if (relative.equals(FixtureContracts.REQUEST_FILE)) {
                assertEquals(request, Json.read(bytes, Request.class)); continue;
            }
            if (!relative.equals("descriptor.mod")) assertTrue(text.startsWith("\ufeff"));
            if (relative.endsWith(".yml")) continue;
            Clausewitz.Block body = Clausewitz.parse(text); allKeys.addAll(keys(body));
            assertFalse(keys(body).contains("rrf_commit_effect"));
            if (relative.contains("observation")) assertReadOnly(keys(body));
        }
        assertEquals(3, allKeys.stream().filter("create_dynamic_rite"::equals).count());
        assertEquals(1, allKeys.stream().filter("detach_rite_to_new_faith"::equals).count());
        assertHistoryLinks(emitted.fixture(), decoded.files().keySet(), 6);
        JsonNode identityEvidence = Json.read(Files.readAllBytes(repository.resolve("mod_religious_ritual_fusion/tools/src/main/resources/acceptance/native-source-evidence.json")), JsonNode.class).path("actor_identity");
        assertEquals(request.actorHistoryId().value(), identityEvidence.path("actor_history_id").textValue());
        assertEquals(request.actorHistoryId().value(), identityEvidence.path("history_definition").path("definition_key").textValue());
        assertEquals(request.actorHistoryId().value(), identityEvidence.path("bookmark").path("history_id").textValue());
        assertEquals("character:" + request.actorHistoryId().value(), Clausewitz.parse(identityEvidence.path("native_script_link").path("clause").textValue()).atom("this", ""));
        assertObservationDecision(emitted.fixture(), request);
        assertTrue(allKeys.contains("add_known_tenet")); assertTrue(allKeys.contains("add_known_doctrine"));
        assertThrows(IllegalArgumentException.class, () -> FixtureEmitter.emit(repository, emitted.fixture(), "synthetic-fixture-machine", request));
        assertEquals(89, ContentValidator.validate(repository.resolve("mod_religious_ritual_fusion")).runtimeFiles());
    }
    @Test void faithRejectionAndColdClosuresUseActualModeAndColdCannotSeed() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        for (String recipe : List.of("core-faith", "ui-rejection", "cold-rite", "cold-faith")) {
            Request request = bundledRequest(repository, recipe);
            Path target = directory.resolve(request.kind().wire() + "-" + request.mode().wire());
            FixtureEmitter.Emission emitted = FixtureEmitter.emit(repository, target, "synthetic-fixture-machine", request);
            assertEquals(request.kind().wire(), emitted.payload().caseId());
            assertHistoryLinks(target, emitted.payload().files().keySet(), request.kind() == CaseKind.COLD_RELOAD ? 4 : 6);
            if (request.kind() == CaseKind.COLD_RELOAD) {
                assertEquals(Set.of(FixtureContracts.REQUEST_FILE, "descriptor.mod", "common/scripted_triggers/rrfa_observation_triggers.txt",
                        "common/script_values/rrfa_observation_values.txt", "events/rrfa_observation_events.txt",
                        "common/decisions/rrfa_cold_observation_decisions.txt", "localization/english/rrfa_observation_l_english.yml",
                        "localization/simp_chinese/rrfa_observation_l_simp_chinese.yml"), emitted.payload().files().keySet());
                assertEquals(8, emitted.payload().files().size());
                assertEquals(emitted.payload(), Json.read(Files.readAllBytes(emitted.manifest()), FixtureContracts.Manifest.class));
                assertFalse(emitted.payload().receipt().containsBusinessEffects());
                assertTrue(emitted.payload().files().keySet().stream().noneMatch(p -> p.contains("seed") || p.contains("fresh") || p.contains("on_action")));
                for (String relative : emitted.payload().files().keySet()) if (!relative.endsWith(".yml") && !relative.endsWith(".json")) {
                    List<String> coldKeys = keys(Clausewitz.parse(Files.readString(target.resolve(relative))));
                    assertReadOnly(coldKeys);
                    for (String registrar : List.of("on_actions", "on_game_start_after_lobby", "events")) assertFalse(coldKeys.contains(registrar));
                }
                assertObservationDecision(target, request);
            } else { assertEquals(11, emitted.payload().files().size()); assertObservationDecision(target, request); }
            assertTrue(Files.readString(target.resolve("events/rrfa_observation_events.txt")).contains(request.mode().wire() + "_persisted_readback"));
        }
    }
    @Test void strictInputTypesAndCampaignKindsRejectInvalidOrAmbiguousRecipes() throws IOException {
        Request valid = new Request(3, CaseKind.CORE, Mode.RITE, ROBERT, new FreshSetup(500), DEFAULT_SELECTION);
        String json = new String(Json.write(valid), StandardCharsets.UTF_8);
        assertEquals(valid, Json.read(json.getBytes(StandardCharsets.UTF_8), Request.class));
        assertTrue(json.contains("\"actorHistoryId\" : \"1128\""));
        for (String identity : List.of("true", "1128", "1128.0", "null", "[]", "{}", "\"\"", "\"01128\"", "\"1128.0\"", "\"29829\"")) {
            String invalid = json.replace("\"1128\"", identity);
            assertThrows(IOException.class, () -> Json.read(invalid.getBytes(StandardCharsets.UTF_8), Request.class), identity);
        }
        for (String invalid : List.of(json.replace("\"piety\" : 500", "\"piety\" : 500.0"), json.replace("\"piety\" : 500", "\"piety\" : true"), json.replace("\"rite\"", "\"cross_religion\""), json.replace("\"schemaVersion\" : 3", "\"schemaVersion\" : 1"), json.replace("\"schemaVersion\" : 3", "\"schemaVersion\" : 3, \"extra\" : true"), json.replace("\"actorHistoryId\" : \"1128\"", "\"actorId\" : 29829"), json.replace("\"actorHistoryId\" : \"1128\"", "\"actorHistoryId\" : \"1128\", \"actorId\" : 29829"), json.replace("  \"actorHistoryId\" : \"1128\",\n", ""))) assertThrows(IOException.class, () -> Json.read(invalid.getBytes(StandardCharsets.UTF_8), Request.class));
        assertThrows(IllegalArgumentException.class, () -> new Request(3, CaseKind.CORE, Mode.RITE, ROBERT, new FreshSetup(499), DEFAULT_SELECTION));
        assertThrows(IllegalArgumentException.class, () -> new Request(3, CaseKind.COLD_RELOAD, Mode.RITE, ROBERT, new FreshSetup(500), DEFAULT_SELECTION));
        assertThrows(IllegalArgumentException.class, () -> new Request(3, CaseKind.CORE, Mode.RITE, ROBERT, new SavedSetup(), DEFAULT_SELECTION));
        assertThrows(IllegalArgumentException.class, () -> new Request(1, CaseKind.CORE, Mode.RITE, ROBERT, new FreshSetup(500), DEFAULT_SELECTION));
        assertThrows(IllegalArgumentException.class, () -> new ActorHistoryId("29829"));
        assertThrows(IOException.class, () -> Json.read("{\"schemaVersion\":1,\"kind\":\"cold_reload\",\"mode\":\"rite\",\"actorId\":29829,\"setup\":{\"type\":\"saved\"}}".getBytes(StandardCharsets.UTF_8), Request.class));
        assertThrows(IOException.class, () -> Json.read("{\"schemaVersion\":3,\"kind\":\"cold_reload\",\"mode\":\"rite\",\"actorHistoryId\":\"1128\",\"setup\":{\"type\":\"saved\",\"piety\":500}}".getBytes(StandardCharsets.UTF_8), Request.class));
    }
    @Test void freshSourceCorePreparationSnapshotsBeforeMutationAndReportsActualReadOnlyConditions() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        FixtureEmitter.Emission emitted = FixtureEmitter.emit(repository, directory.resolve("joint-fixture"), "synthetic-fixture-machine", bundledRequest(repository, "core-rite"));
        Clausewitz.Block effects = Clausewitz.parse(Files.readString(emitted.fixture().resolve("common/scripted_effects/rrfa_seed_effects.txt")));
        Clausewitz.Block seed = effects.block("rrfa_seed_inputs_effect");
        assertEquals(3, keys(seed).stream().filter("rrfa_align_seed_core_effect"::equals).count());
        assertEquals(3, keys(seed).stream().filter("create_dynamic_rite"::equals).count());
        assertEquals(1, keys(seed).stream().filter("detach_rite_to_new_faith"::equals).count());
        Clausewitz.Block align = effects.block("rrfa_align_seed_core_effect");
        List<Clausewitz.Block> snapshotScopes = new ArrayList<>();
        for (Clausewitz.Entry entry : align.entries()) {
            if (entry.key().equals("scope:rrfa_seed_target") && entry.value() instanceof Clausewitz.Block block
                    && keys(block).contains("add_to_list")) snapshotScopes.add(block);
        }
        assertEquals(1, snapshotScopes.size());
        Clausewitz.Block snapshot = snapshotScopes.getFirst().block("every_rite_tenet");
        assertTrue(keys(snapshot).contains("add_to_list"));
        assertFalse(keys(snapshot).contains("remove_rite_tenet"));
        assertFalse(keys(snapshot).contains("add_rite_tenet"));
        int snapshotIndex = -1, mutationIndex = -1;
        for (int index = 0; index < align.entries().size(); index++) {
            Clausewitz.Entry entry = align.entries().get(index);
            if (entry.key().equals("scope:rrfa_seed_target") && snapshotIndex < 0) snapshotIndex = index;
            if (entry.value() instanceof Clausewitz.Block block && keys(block).contains("remove_rite_tenet")) {
                assertEquals("every_in_list", entry.key());
                assertEquals("rrfa_seed_cores_to_remove", block.atom("list", ""));
                assertEquals("scope:rrfa_seed_item", block.block("scope:rrfa_seed_target").atom("remove_rite_tenet", ""));
                mutationIndex = index;
            }
        }
        assertTrue(snapshotIndex >= 0 && mutationIndex > snapshotIndex);
        assertEquals(3, keys(align).stream().filter("add_rite_tenet"::equals).count());
        Clausewitz.Block diagnostics = effects.block("rrfa_seed_readiness_diagnostics_effect");
        assertReadOnly(keys(diagnostics));
        assertEquals(27, diagnostics.entries().stream().filter(e -> e.key().equals("if")).count());
        String text = Files.readString(emitted.fixture().resolve("common/scripted_effects/rrfa_seed_effects.txt"));
        for (String source : List.of("SOURCE_A", "SOURCE_B_RITE", "SOURCE_B_FAITH")) {
            assertTrue(text.contains(source + "_CORE_PREPARATION_BEGIN"));
            assertTrue(text.contains(source + "_CORE_PREPARATION_END"));
        }
        for (String phase : List.of("BEFORE", "AFTER")) {
            assertTrue(text.contains("RRFAT: DIAG CORE_" + phase + "_ENTRY"));
        }
        assertFalse(keys(align).contains("debug_log_scopes"));
        assertFalse(keys(diagnostics).contains("debug_log_scopes"));
        assertTrue(text.contains("RRFAT: DIAG EXPECTED_B_CONVERTIBLE YES"));
        assertTrue(text.contains("RRFAT: DIAG EXPECTED_B_CONVERTIBLE NO"));
        assertFalse(keys(seed).stream().anyMatch(key -> key.startsWith("rrf_")));
    }
    @Test void threeAndFourRecipesFreezeOneCanonicalSelectionInsideTheActualImportClosure() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        for (String recipe : List.of("core-rite", "core-faith", "cold-rite", "cold-faith", "core-rite-four", "core-faith-four", "cold-rite-four", "cold-faith-four")) {
            Request request = bundledRequest(repository, recipe);
            FixtureEmitter.Emission emitted = FixtureEmitter.emit(repository, directory.resolve(recipe), "synthetic-fixture-machine", request);
            FixtureContracts.FileContent metadata = emitted.payload().files().get(FixtureContracts.REQUEST_FILE);
            byte[] bytes = Files.readAllBytes(emitted.fixture().resolve(FixtureContracts.REQUEST_FILE));
            assertEquals(metadata.sha256(), ReleaseBuilder.sha256(bytes)); assertEquals(metadata.bytes(), bytes.length);
            assertEquals(request, Json.read(bytes, Request.class));
            assertTrue(java.util.Arrays.equals(bytes, Files.readAllBytes(emitted.requestSnapshot())));
            org.xar.ck3.rrf.acceptance.FrozenFixtureReader.BoundRequest bound = org.xar.ck3.rrf.acceptance.FrozenFixtureReader.read(
                    new FixtureContracts.FilePin(emitted.manifest().toRealPath().toString(), Files.size(emitted.manifest()), ReleaseBuilder.sha256(Files.readAllBytes(emitted.manifest()))), "synthetic-fixture-machine", repository);
            assertEquals(request, bound.request());
            String observed = Files.readString(emitted.fixture().resolve("common/scripted_triggers/rrfa_observation_triggers.txt"));
            Clausewitz.Block result = Clausewitz.parse(observed).block("rrfa_result_core_trigger");
            assertEquals(Integer.toString(request.expectedSelection().coreTenets().size()), ((Clausewitz.Block) result.entries().getFirst().value()).atom("count", ""));
            assertTrue(observed.contains("variable_list_size = { name = rrf_origin_core_tenets value = " + request.expectedSelection().coreTenets().size() + " }"));
            for (ExpectedSelection.TenetKey key : request.expectedSelection().coreTenets()) assertTrue(observed.contains("name = rrf_origin_core_tenets target = tenet:" + key.value()));
            Files.write(emitted.fixture().resolve(FixtureContracts.REQUEST_FILE), new byte[]{10}, java.nio.file.StandardOpenOption.APPEND);
            assertThrows(IOException.class, () -> org.xar.ck3.rrf.acceptance.FrozenFixtureReader.read(bound.manifestPin(), "synthetic-fixture-machine", repository));
        }
    }
    @Test void actualCliCanonicalPinsSurviveWindowsOutputAliasesAndRejectNoncanonicalReferences() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        Path parent = Files.createDirectory(directory.resolve("MiXeDFixtureParent")).toRealPath();
        boolean windows = System.getProperty("os.name").startsWith("Windows");
        Path requestedParent = windows ? Path.of(parent.toString().toLowerCase(Locale.ROOT)) : parent;
        assertTrue(Files.isSameFile(parent, requestedParent));
        for (String recipe : List.of("core-rite", "core-rite-four", "cold-rite", "cold-snapshot")) {
            Request request = recipe.equals("cold-snapshot")
                    ? new Request(4, CaseKind.COLD_RELOAD, Mode.RITE, ROBERT, coldEvidence(repository, "cli-wallet", "5400"), DEFAULT_SELECTION)
                    : bundledRequest(repository, recipe);
            Path inputs = directory.resolve(recipe + "-cli-request.json"); Files.write(inputs, Json.write(request));
            ByteArrayOutputStream bytes = new ByteArrayOutputStream(); PrintStream original = System.out;
            int code;
            try (PrintStream capture = new PrintStream(bytes, true, StandardCharsets.UTF_8)) {
                System.setOut(capture);
                try {
                    code = FixtureEmitter.run(new String[]{"--repo-root", repository.toString(), "--output", requestedParent.resolve(recipe).toString(),
                            "--machine-id", "synthetic-fixture-machine", "--inputs", inputs.toString()});
                } finally { System.setOut(original); }
            }
            assertEquals(0, code);
            FixtureEmitter.Report produced = Json.read(bytes.toByteArray(), FixtureEmitter.Report.class);
            assertEquals(produced, Json.read(Json.write(produced), FixtureEmitter.Report.class));
            com.fasterxml.jackson.databind.JsonNode body = Json.read(bytes.toByteArray(), com.fasterxml.jackson.databind.JsonNode.class);
            assertEquals(5, body.size()); assertFalse(produced.gameStarted());
            assertEquals(FixtureEmitter.BusinessAcceptance.NOT_RUN, produced.businessAcceptance());
            if (!(body instanceof com.fasterxml.jackson.databind.node.ObjectNode fields)) throw new AssertionError("CLI object required");
            var missing = fields.deepCopy(); missing.remove("manifest");
            assertThrows(IOException.class, () -> Json.read(Json.write(missing), FixtureEmitter.Report.class));
            var nullManifest = fields.deepCopy(); nullManifest.putNull("manifest");
            assertThrows(IOException.class, () -> Json.read(Json.write(nullManifest), FixtureEmitter.Report.class));
            FixtureContracts.FilePin canonical = produced.manifest(); Path manifest = Path.of(canonical.path());
            assertEquals(manifest.toRealPath().toString(), canonical.path());
            List<Path> aliases = new ArrayList<>(List.of(manifest.getParent().resolve(".").resolve(manifest.getFileName())));
            if (windows) aliases.add(Path.of(canonical.path().toLowerCase(Locale.ROOT)));
            for (Path alias : aliases) {
                assertFalse(alias.toString().equals(canonical.path())); assertTrue(Files.isSameFile(manifest, alias));
                FixtureContracts.FilePin noncanonical = new FixtureContracts.FilePin(alias.toString(), canonical.bytes(), canonical.sha256());
                assertThrows(IOException.class, () -> org.xar.ck3.rrf.acceptance.FrozenFixtureReader.read(noncanonical, "synthetic-fixture-machine", repository));
            }
            var accepted = org.xar.ck3.rrf.acceptance.FrozenFixtureReader.read(canonical, "synthetic-fixture-machine", repository);
            assertEquals(canonical, accepted.manifestPin()); assertEquals(request, accepted.request());
            Path receiptPath = Path.of(produced.fixture() + ".inputs.json");
            if (request.schemaVersion() == 4) {
                var receipt = Json.read(Files.readAllBytes(receiptPath), FixtureContracts.PrebuiltInputs.class);
                assertEquals(canonical, receipt.manifest());
                assertEquals(manifestPin(Path.of(produced.fixture()).resolve(FixtureContracts.REQUEST_FILE)), receipt.request());
                assertEquals(org.xar.ck3.rrf.acceptance.ColdSnapshotReader.inputPins(request), receipt.inputPins());
            } else assertFalse(Files.exists(receiptPath));
        }
    }
    @Test void selectionRejectsWrongTypesDuplicatesFalseCatalogKindsAndEveryUnreachableFiveToHundredRecipe() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        Request valid = bundledRequest(repository, "core-rite-four");
        String json = new String(Json.write(valid), StandardCharsets.UTF_8);
        for (String value : List.of("true", "1", "1.0", "null", "[]", "{}", "\"tenet_\"")) {
            assertThrows(IOException.class, () -> Json.read(json.replace("\"tenet_legalism\"", value).getBytes(StandardCharsets.UTF_8), Request.class));
        }
        assertThrows(IOException.class, () -> Json.read(json.replace("\"tenet_legalism\"", "\"tenet_esotericism\"").getBytes(StandardCharsets.UTF_8), Request.class));
        assertThrows(IOException.class, () -> Json.read(json.replace("\"expectedSelection\"", "\"unknownSelection\"").getBytes(StandardCharsets.UTF_8), Request.class));
        assertThrows(IllegalArgumentException.class, () -> new ExpectedSelection(valid.expectedSelection().coreTenets().subList(0, 2)));
        for (int size = 5; size <= 100; size++) {
            List<ExpectedSelection.TenetKey> values = new ArrayList<>(valid.expectedSelection().coreTenets());
            for (int index = values.size(); index < size; index++) values.add(new ExpectedSelection.TenetKey("tenet_unreachable_" + index));
            ExpectedSelection structural = new ExpectedSelection(values);
            assertEquals(size, structural.coreTenets().size());
            assertThrows(IllegalArgumentException.class, () -> new Request(3, CaseKind.CORE, Mode.RITE, ROBERT, new FreshSetup(500), structural));
        }
        List<ExpectedSelection.TenetKey> overflow = java.util.stream.IntStream.range(0, 101).mapToObj(index -> new ExpectedSelection.TenetKey("tenet_unreachable_" + index)).toList();
        assertThrows(IllegalArgumentException.class, () -> new ExpectedSelection(overflow));
        for (List<ExpectedSelection.TenetKey> missingSide : List.of(FixtureContracts.SOURCE_A, FixtureContracts.SOURCE_B)) assertThrows(IllegalArgumentException.class,
                () -> new Request(3, CaseKind.CORE, Mode.RITE, ROBERT, new FreshSetup(500), new ExpectedSelection(missingSide)));
        Contracts.Catalog catalog = Json.read(Files.readAllBytes(repository.resolve("mod_religious_ritual_fusion/catalog/generated-catalog.json")), Contracts.Catalog.class);
        List<Contracts.Definition> wrongDefinitions = catalog.definitions().stream().map(row -> row.id().equals("tenet_legalism")
                ? new Contracts.Definition(Contracts.Kind.DOCTRINE, row.id(), "doctrine_divorce", row.sourcePath(), row.shown(), row.canPick(), row.requiresDlc(), row.visible(), row.blockedReasons()) : row).toList();
        Contracts.Catalog wrongKind = new Contracts.Catalog(1, catalog.machineId(), catalog.observedAt(), catalog.sources(), catalog.groups(), wrongDefinitions);
        assertThrows(IllegalArgumentException.class, () -> valid.expectedSelection().requireCatalog(wrongKind));
        assertThrows(IllegalArgumentException.class, () -> FixtureEmitter.validateCatalog(wrongKind));
        List<ExpectedSelection.TenetKey> reversed = new ArrayList<>(valid.expectedSelection().coreTenets()); java.util.Collections.reverse(reversed);
        valid.expectedSelection().requireExact(reversed, "authored reordered saved set");
        reversed.set(0, reversed.get(1)); assertThrows(IllegalArgumentException.class, () -> valid.expectedSelection().requireExact(reversed, "authored duplicate saved set"));
    }
    private static List<String> keys(Clausewitz.Block block) { List<String> keys = new ArrayList<>(); for (Clausewitz.Entry e : block.entries()) { keys.add(e.key()); if (e.value() instanceof Clausewitz.Block child) keys.addAll(keys(child)); } return keys; }
    private static void assertObservationDecision(Path fixture, Request request) throws IOException {
        boolean cold = request.kind() == CaseKind.COLD_RELOAD;
        String key = cold ? "rrfa_observe_cold_decision" : "rrfa_observe_" + request.kind().wire() + "_decision";
        String decisionFile = cold ? "rrfa_cold_observation_decisions.txt" : "rrfa_observation_decisions.txt";
        Clausewitz.Block decision = Clausewitz.parse(Files.readString(fixture.resolve("common/decisions/" + decisionFile))).block(key);
        for (String gate : List.of("is_shown", "is_valid")) {
            assertEquals("no", decision.block(gate).atom("is_ai", ""));
            assertEquals("character:" + request.actorHistoryId().value(), decision.block(gate).atom("this", ""));
            assertEquals(cold ? "rrfa_mode" : "rrfa_seed_done", decision.block(gate).atom(cold ? "has_variable" : "has_character_flag", ""));
        }
        Clausewitz.Block effect = decision.block("effect"); assertEquals(1, effect.entries().size());
        assertEquals("trigger_event", effect.entries().getFirst().key());
        Clausewitz.Block trigger = effect.block("trigger_event"); assertEquals(1, trigger.entries().size());
        assertEquals(cold ? "rrfa.22" : request.kind() == CaseKind.UI_REJECTION ? "rrfa.30" : request.mode() == Mode.RITE ? "rrfa.20" : "rrfa.21", trigger.atom("id", ""));
        assertReadOnly(keys(effect));
        for (String forbidden : List.of("cost", "cooldown", "days")) assertFalse(keys(decision).contains(forbidden));
        // The shared locale also carries the fresh-only seed's name; a cold
        // fixture keeps this inert text while excluding every seed effect.
        Set<String> expected = Set.of(key, "rrfa_observation_decision_desc", "rrfa_observation_decision_tooltip", "rrfa_observation_decision_confirm", "rrfa_fixture_long_vassal_name");
        for (String language : List.of("english", "simp_chinese")) {
            String text = Files.readString(fixture.resolve("localization/" + language + "/rrfa_observation_l_" + language + ".yml"));
            assertTrue(text.startsWith("\ufeffl_" + language + ":\n"));
            Set<String> actual = new java.util.LinkedHashSet<>();
            for (String line : text.lines().skip(1).toList()) if (!line.isBlank()) { assertTrue(line.matches(" [A-Za-z_][A-Za-z0-9_]*:0 \\\".*\\\"")); actual.add(line.substring(1, line.indexOf(':'))); }
            assertEquals(expected, actual);
        }
    }
    private static void assertReadOnly(List<String> keys) {
        Set<String> writes = Set.of("set_variable", "remove_variable", "change_variable", "save_scope_as", "clear_saved_scope", "add_character_flag", "remove_character_flag", "add_to_variable_list", "clear_variable_list", "add_piety", "set_character_rite", "change_rite_doctrine", "create_dynamic_rite", "detach_rite_to_new_faith", "add_rite_tenet", "remove_rite_tenet", "add_known_tenet", "add_known_doctrine");
        assertTrue(keys.stream().noneMatch(writes::contains), keys.toString());
    }
    private static Request bundledRequest(Path repository, String recipe) throws IOException {
        Request request = Json.read(Files.readAllBytes(repository.resolve("mod_religious_ritual_fusion/tools/src/main/resources/acceptance/requests/" + recipe + ".json")), Request.class);
        assertEquals(3, request.schemaVersion()); assertEquals(ROBERT, request.actorHistoryId());
        return request;
    }
    private static void assertHistoryLinks(Path fixture, Set<String> files, int expectedCount) throws IOException {
        List<String> links = new ArrayList<>();
        for (String relative : files) if (relative.endsWith(".txt")) collectHistoryLinks(Clausewitz.parse(Files.readString(fixture.resolve(relative))), links);
        assertEquals(java.util.Collections.nCopies(expectedCount, "character:1128"), links);
    }
    private static void collectHistoryLinks(Clausewitz.Block block, List<String> links) {
        for (Clausewitz.Entry entry : block.entries()) {
            if (entry.key().startsWith("character:")) links.add(entry.key());
            if (entry.value() instanceof Clausewitz.Block child) collectHistoryLinks(child, links);
            else if (entry.value() instanceof Clausewitz.Atom atom && atom.token().startsWith("character:")) links.add(atom.token());
        }
    }
}
