package org.xar.ck3.markets.saveaudit;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.markets.acceptance.FollowupContracts;
import org.xar.ck3.markets.acceptance.FollowupObservationScripts;
import org.xar.ck3.save.Clausewitz;

/** Shared-parser compatibility only: synthetic records never qualify a real 1.21 SAVE. */
final class MarketEvolutionSaveCompatibilityTest {
    @TempDir Path directory;
    private static final String MACHINE = "synthetic-evolution-save-compatibility";
    private static final FinancialProjector.LayoutHypothesis LAYOUT =
            new FinancialProjector.LayoutHypothesis("synthetic", "999", BigInteger.valueOf(100000), "story", "char");

    @Test void emittedTypedEvolutionAndRetainedSpotEpochThreeLeaveFinancialColdProjectionExact() throws Exception {
        String base = FinancialSaveAuditSelfTest.scene();
        List<String> types = emittedEvolutionTypes();
        assertEquals(7, types.size(), "active epoch one, passive epochs two/three/four, two record types and real prior spot epoch three");
        assertTrue(types.contains("xfma_spot_e3_observer"));
        assertTrue(types.contains("xfma_market_evolution_e3_observer"));
        assertTrue(types.contains("xfma_market_evolution_e4_observer"));
        StringBuilder records = new StringBuilder();
        for (int n = 0; n < types.size(); n++) records.append(story(800 + n, types.get(n)));
        Path first = write("base", base), second = write("with-observer", append(base, records.toString()));
        var original = FinancialSaveReader.read(first, MACHINE, LAYOUT);
        var strict = FinancialSaveReader.read(second, MACHINE, LAYOUT);
        var retiredMode = FinancialSaveReader.readWithRetiredXfma(second, MACHINE, LAYOUT);
        assertEquals(5 + types.size(), strict.coverage().tableRecords());
        assertEquals(5, strict.coverage().selectedFinancialRecords());
        assertEquals(original.financialStories(), strict.financialStories());
        assertTrue(retiredMode.untypedRecords().isEmpty(), "typed records must not enter the numeric-only retired path");
        assertTrue(FinancialAudit.compareCold(FinancialProjector.project(original, LAYOUT),
                FinancialProjector.project(strict, LAYOUT)).exactSelectedFinancialState());
        assertFalse(FinancialAudit.audit(FinancialProjector.project(strict, LAYOUT)).financialCertified());
    }

    @Test void laterDelistingFixturePreservesTypedEvolutionEpochsOneThroughFourForColdComparison() throws Exception {
        var input = new FollowupContracts.Request(2, FollowupContracts.Profile.DELISTING_GUI, 2,
                new FollowupContracts.ActorBinding(FollowupContracts.ActorMode.CURRENT_PLAYER, null),
                new FollowupContracts.Targets("1", "1", null, null, null, null), null, null);
        byte[] bytes = FollowupObservationScripts.render(input).get("common/story_cycles/" + input.prefix() + ".txt");
        var catalog = Clausewitz.parse(new String(bytes, StandardCharsets.UTF_8));
        List<String> retained = catalog.entries().stream().map(Clausewitz.Entry::key)
                .filter(k -> k.matches("xfma_market_evolution_e[1234]_observer")).toList();
        assertEquals(List.of("xfma_market_evolution_e1_observer", "xfma_market_evolution_e2_observer",
                "xfma_market_evolution_e3_observer", "xfma_market_evolution_e4_observer"), retained);
        for (String type : retained)
            assertTrue(new String(bytes, StandardCharsets.UTF_8).contains(type + " = { visible = no }"),
                    "the later fixture must not reactivate an earlier observer: " + type);
        String base = FinancialSaveAuditSelfTest.scene(); StringBuilder records = new StringBuilder();
        for (int i = 0; i < retained.size(); i++) records.append(story(800 + i, retained.get(i)));
        var original = FinancialSaveReader.read(write("e4-cross-fixture-base", base), MACHINE, LAYOUT);
        Path saved = write("e4-cross-fixture-history", append(base, records.toString()));
        var actual = FinancialSaveReader.read(saved, MACHINE, LAYOUT);
        assertEquals(9, actual.coverage().tableRecords());
        assertEquals(5, actual.coverage().selectedFinancialRecords());
        assertEquals(original.financialStories(), actual.financialStories());
        assertTrue(FinancialSaveReader.readWithRetiredXfma(saved, MACHINE, LAYOUT).untypedRecords().isEmpty());
        assertTrue(FinancialAudit.compareCold(FinancialProjector.project(original, LAYOUT),
                FinancialProjector.project(actual, LAYOUT)).exactSelectedFinancialState());
        assertFalse(FinancialAudit.audit(FinancialProjector.project(actual, LAYOUT)).financialCertified());
    }

    @Test void removingEvolutionDiscriminatorDoesNotWidenRetiredNumericObserverAdmission() throws Exception {
        String typed = story(800, emittedEvolutionTypes().getFirst());
        String untyped = typed.replaceFirst("story_cycle=[a-z0-9_]+ ", "");
        assertThrows(IOException.class, () -> FinancialSaveReader.readWithRetiredXfma(
                write("untyped-reference-observer", append(FinancialSaveAuditSelfTest.scene(), untyped)), MACHINE, LAYOUT));
    }

    @Test void unrelatedUnknownFinancialTypesRemainSelectedAndIncomplete() throws Exception {
        for (String type : List.of("xfm_finance_unknown_evolution_wallet", "xfm_futures_unknown_evolution_position",
                "xfm_debt_claim_unknown_evolution")) {
            var read = FinancialSaveReader.readWithRetiredXfma(write(type,
                    append(FinancialSaveAuditSelfTest.scene(), story(800, type))), MACHINE, LAYOUT);
            assertEquals(6, read.financial().coverage().selectedFinancialRecords(), type);
            assertEquals(FinancialAudit.Assessment.INCOMPLETE,
                    FinancialAudit.audit(FinancialProjector.project(read.financial(), LAYOUT)).assessment(), type);
            assertTrue(read.untypedRecords().isEmpty());
        }
    }

    @Test void delistingFixtureKeepsActualOldEpochOneAndNewTypedObserverReferencesReadable() throws Exception {
        var input = new FollowupContracts.Request(2, FollowupContracts.Profile.DELISTING_GUI, 2,
                new FollowupContracts.ActorBinding(FollowupContracts.ActorMode.CURRENT_PLAYER, null),
                new FollowupContracts.Targets("1", "1", null, null, null, null), null, null);
        byte[] cycleBytes = FollowupObservationScripts.render(input).get("common/story_cycles/" + input.prefix() + ".txt");
        String cycles = new String(cycleBytes, StandardCharsets.UTF_8);
        assertTrue(cycles.contains("xfma_delisting_gui_e1_observer = { visible = no }"));
        assertTrue(cycles.contains("xfma_market_evolution_e1_observer = { visible = no }"));
        assertTrue(cycles.contains("xfma_spot_e3_observer = { visible = no }"));
        String base = FinancialSaveAuditSelfTest.scene();
        String records = story(800, "xfma_delisting_gui_e1_observer")
                + story(801, "xfma_delisting_gui_e2_observer") + story(802, "xfma_market_evolution_e1_observer");
        Path save = write("delisting-typed-old-and-active", append(base, records));
        var original = FinancialSaveReader.read(write("delisting-base", base), MACHINE, LAYOUT);
        var actual = FinancialSaveReader.read(save, MACHINE, LAYOUT);
        assertEquals(8, actual.coverage().tableRecords());
        assertEquals(original.financialStories(), actual.financialStories());
        assertTrue(FinancialSaveReader.readWithRetiredXfma(save, MACHINE, LAYOUT).untypedRecords().isEmpty());
        assertTrue(FinancialAudit.compareCold(FinancialProjector.project(original, LAYOUT),
                FinancialProjector.project(actual, LAYOUT)).exactSelectedFinancialState());
        assertThrows(IOException.class, () -> FinancialSaveReader.readWithRetiredXfma(write("delisting-no-discriminator",
                append(base, story(800, "xfma_delisting_gui_e1_observer").replaceFirst("story_cycle=[a-z0-9_]+ ", ""))), MACHINE, LAYOUT));
    }

    private static List<String> emittedEvolutionTypes() {
        var input = new FollowupContracts.Request(2, FollowupContracts.Profile.MARKET_EVOLUTION, 1,
                new FollowupContracts.ActorBinding(FollowupContracts.ActorMode.CURRENT_PLAYER, null),
                new FollowupContracts.Targets("1", "1", null, null, null, null), null, null);
        var files = FollowupObservationScripts.render(input);
        byte[] cycles = files.entrySet().stream().filter(e -> e.getKey().startsWith("common/story_cycles/"))
                .map(java.util.Map.Entry::getValue).findFirst().orElseThrow();
        return Clausewitz.parse(new String(cycles, StandardCharsets.UTF_8)).entries().stream()
                .map(Clausewitz.Entry::key).filter(k -> k.startsWith("xfma_market_evolution_") || k.equals("xfma_spot_e3_observer")).toList();
    }
    private static String story(int id, String type) {
        return id + "={story_cycle=" + type + " owner=31254 seed=1 variables={data={"
                + "{flag=xfma_record_id data={type=value identity=100000}}"
                + "{flag=xfma_observer data={type=story identity=801}}"
                + "{flag=xfma_coin_source data={type=story identity=4}}"
                + "}} variable_lists={xfma_subscription_sources={3}}} ";
    }
    private static String append(String scene, String record) { return scene.substring(0, scene.length() - 2) + record + "}}"; }
    private Path write(String name, String content) throws IOException {
        Path path = directory.resolve(name + ".txt"); Files.writeString(path, content); return path;
    }
}
