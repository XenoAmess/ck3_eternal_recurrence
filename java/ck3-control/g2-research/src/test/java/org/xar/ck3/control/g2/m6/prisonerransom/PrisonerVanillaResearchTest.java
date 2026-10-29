package org.xar.ck3.control.g2.m6.prisonerransom;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.Assignment;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.Atom;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.AvailableQuote;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.Catalog;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.Gate;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.Interaction;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.Knowledge;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.OptionCounts;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.OptionMask;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.Source;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.UnavailableQuote;
import org.xar.ck3.control.wave2.prisoners.releasepreview.NativeKinship12003;
import org.xar.ck3.control.wave2.prisoners.releasepreview.NativeKinshipCodec12003;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleaseCollectionProjection12003.SupportedBuild;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;

/** Real original-byte differentials plus synthetic malformed-token boundaries; no native producer or game is invoked. */
public final class PrisonerVanillaResearchTest {
    private static final FrameBinding FRAME = new FrameBinding(BigInteger.valueOf(1014), 53286360, 29829, 61540);
    private static final BigInteger EPOCH = BigInteger.valueOf(1926335);
    private static final List<String> CASES = List.of("gate_true", "gate_false", "old11", "selected_change_prison", "puppet_role_mismatch");
    private static Catalog catalog;
    private static byte[] stock;
    private static Path resources;
    private enum InputMode { EXACT_EXTERNAL_SOURCE, PINNED_PORTABLE_FIXTURES }
    private static InputMode inputMode;

    @BeforeAll
    static void requiredOriginalSources() throws IOException {
        inputMode = InputMode.valueOf(System.getProperty("prisoner.research.inputMode", "PINNED_PORTABLE_FIXTURES"));
        G2Source source;
        if (inputMode == InputMode.EXACT_EXTERNAL_SOURCE) {
            String stockPath = required("prisoner.research.stock");
            resources = Path.of(required("prisoner.research.resources"));
            stock = Files.readAllBytes(Path.of(stockPath));
            source = new G2Source(required("prisoner.research.machine"), required("prisoner.research.observedAt"),
                    PrisonerVanillaResearch.EXACT_BUILD, new ExactRef(stockPath, stock.length, PrisonerVanillaResearch.sha256(stock)));
        } else {
            for (String property : List.of("prisoner.research.stock", "prisoner.research.resources", "prisoner.research.machine", "prisoner.research.observedAt"))
                if (System.getProperty(property) != null) throw new IllegalArgumentException("external source properties require explicit EXACT_EXTERNAL_SOURCE mode");
            JsonNode manifest = StrictJson.parse(classpath("fixture-source.json"));
            StrictJson.object(manifest, Set.of("schema", "machine_id", "observed_at_utc", "stock_ref", "exact_build", "exe_sha256", "scope"));
            assertEquals("xar.prisoner-research-portable-fixture-source/v1", StrictJson.text(manifest.get("schema")));
            assertEquals(PrisonerVanillaResearch.EXE_SHA256, StrictJson.text(manifest.get("exe_sha256")));
            stock = classpath("00_prison_interactions.txt");
            source = new G2Source(StrictJson.text(manifest.get("machine_id")), StrictJson.text(manifest.get("observed_at_utc")),
                    StrictJson.text(manifest.get("exact_build")), ExactRef.fromJson(manifest.get("stock_ref")));
        }
        catalog = PrisonerVanillaResearch.inspect(stock, new Source(source, PrisonerVanillaResearch.EXE_SHA256));
        System.out.println("PRISONER_RESEARCH_INPUT_MODE=" + inputMode + " source_machine=" + source.machineId()
                + " new_native_execution=false current_installation_qualified=false");
    }

    @Test
    void exactCurrentSourceContainsFiveSeparateOpportunitiesAndUnknownNativeArbitration() {
        assertEquals(5, catalog.interactions().size());
        assertEquals(1886, catalog.tree(Interaction.RANSOM).span().startLine());
        assertEquals(4282, catalog.tree(Interaction.RELEASE).span().startLine());
        assertEquals(PrisonerVanillaResearch.RANSOM_AUTHORED_OPTION_COUNT, catalog.tree(Interaction.RANSOM).sections("send_option").size());
        assertEquals(3, catalog.edges().stream().filter(edge -> edge.state() == PrisonerVanillaResearch.EdgeState.UNKNOWN).count());
        for (Interaction interaction : List.of(Interaction.RANSOM, Interaction.RELEASE, Interaction.EXECUTE)) {
            assertEquals("prisoners", atom(PrisonerVanillaResearch.assignments(
                    catalog.tree(interaction).sections("ai_targets").getFirst().expression(), "ai_recipients").getFirst()));
        }
    }

    @Test
    void authoredCadenceIsRetainedAsRawTierValuesRatherThanInventedSchedulerTime() {
        assertEquals("36", cadence(Interaction.RANSOM, "barony"));
        assertEquals("6", cadence(Interaction.RANSOM, "county"));
        assertEquals("0", cadence(Interaction.PAY_RANSOM, "barony"));
        assertEquals("12", cadence(Interaction.RELEASE, "barony"));
        assertEquals("1", cadence(Interaction.RELEASE, "county"));
        assertEquals("72", cadence(Interaction.EXECUTE, "barony"));
        assertEquals("12", cadence(Interaction.EXECUTE, "county"));
    }

    @Test
    void orderedSenderZeroFactorsStaySeparateFromLegalityAndAnswer() {
        assertEquals(3, zeroFactors(Interaction.RANSOM));
        assertEquals(1, zeroFactors(Interaction.RELEASE));
        assertEquals(3, zeroFactors(Interaction.EXECUTE));
        assertFalse(catalog.tree(Interaction.RANSOM).sections("ai_accept").isEmpty());
        assertFalse(catalog.tree(Interaction.RELEASE).sections("auto_accept").isEmpty());
        assertTrue(PrisonerVanillaResearch.assignments(catalog.tree(Interaction.RANSOM).sections("ai_will_do").getFirst().expression(),
                "has_character_flag").stream().anyMatch(entry -> atom(entry).equals("character_ransom_refused_by_player")));
    }

    @Test
    void declineWritesTenYearFlagWithoutInventingAReevaluationSchedule() {
        var decline = catalog.tree(Interaction.RANSOM).sections("on_decline").getFirst();
        assertTrue(PrisonerVanillaResearch.assignments(decline.expression(), "flag").stream()
                .anyMatch(entry -> atom(entry).equals("character_ransom_refused_by_player")));
        assertTrue(PrisonerVanillaResearch.assignments(decline.expression(), "years").stream().anyMatch(entry -> atom(entry).equals("10")));
        assertTrue(catalog.edges().stream().anyMatch(edge -> edge.to().equals("opportunity-reevaluation")
                && edge.state() == PrisonerVanillaResearch.EdgeState.UNKNOWN));
    }

    @Test
    void everySourceSectionHasTheExactOriginalSpanHashAndOrder() {
        String text = new String(stock, StandardCharsets.UTF_8);
        for (var tree : catalog.interactions()) {
            int previous = -1;
            for (var section : tree.sections()) {
                assertTrue(section.span().startOffset() > previous);
                previous = section.span().startOffset();
                byte[] fragment = text.substring(section.span().startOffset(), section.span().endOffset()).getBytes(StandardCharsets.UTF_8);
                assertEquals(section.sha256(), PrisonerVanillaResearch.sha256(fragment));
                assertEquals(section.key(), new String(fragment, StandardCharsets.UTF_8).split("\\s|=", 2)[0]);
            }
        }
        var json = PrisonerVanillaResearch.catalogJson(catalog);
        assertJsonRepresentation(json, StrictJson.parse(StrictJson.canonical(json, 1048576), 1048576));
        assertFalse(json.get("native_execution_performed").booleanValue());
    }

    @Test
    void tenPinnedNativeWholeProducerSamplesRoundtripTheirExistingQuoteLeaves() throws IOException {
        JsonNode pins = StrictJson.parse(resource("source-pins.json"), 131072);
        int cases = 0;
        for (JsonNode pin : pins.get("vectors")) {
            byte[] raw = resource(pin.get("resource").textValue());
            assertEquals(pin.get("sha256").textValue(), PrisonerVanillaResearch.sha256(raw));
            JsonNode rows = StrictJson.parse(raw, 131072).get("player_prisoner_collection").get("prisoners");
            for (int ordinal = 0; ordinal < rows.size(); ordinal++) {
                FrameBinding binding = new FrameBinding(FRAME.nativeRevision(), FRAME.dateRaw(), FRAME.playerCharacterId(),
                        rows.get(ordinal).get("prisoner_character_id").longValue());
                JsonNode nativeLeaf = rows.get(ordinal).get("ransom_quote_preview");
                var quote = PrisonerVanillaResearch.decodeQuote(StrictJson.canonical(nativeLeaf), binding, EPOCH);
                assertJsonRepresentation(nativeLeaf, PrisonerVanillaResearch.quoteJson(quote));
                assertEquals(quote, PrisonerVanillaResearch.decodeQuote(StrictJson.canonical(PrisonerVanillaResearch.quoteJson(quote)), binding, EPOCH));
            }
            cases++;
        }
        assertEquals(10, cases);
    }

    @Test
    void exactCurrentCandidateAdapterPreservesEveryIdentityAndPublicNativeRevisionSeparation() throws IOException {
        for (String name : CASES) {
            byte[] raw = resource("native12004/" + name + ".json");
            var explanation = PrisonerVanillaResearch.explain(raw, SupportedBuild.CK3_12004, FRAME, BigInteger.valueOf(37), catalog);
            assertEquals(List.of(54235L, 56063L, 61540L, 70766L), explanation.candidates().stream().map(PrisonerVanillaResearch.Candidate::prisonerCharacterId).toList());
            assertEquals(BigInteger.valueOf(37), explanation.publicPlanningRevision());
            assertEquals(FRAME.nativeRevision(), explanation.nativeWireRevision());
            assertNotEquals(explanation.publicPlanningRevision(), explanation.nativeWireRevision());
            for (int ordinal : List.of(0, 1, 3)) assertEquals(Gate.NOT_EVALUATED, explanation.candidates().get(ordinal).ransomGate());
            assertTrue(explanation.candidates().stream().allMatch(candidate -> candidate.closeFamily() == Knowledge.UNKNOWN
                    && candidate.closeOrExtendedFamily() == Knowledge.UNKNOWN));
            ObjectNode out = PrisonerVanillaResearch.explanationJson(explanation);
            assertJsonRepresentation(out, StrictJson.parse(StrictJson.canonical(out)));
            assertFalse(out.get("action_selected").booleanValue());
            assertFalse(out.get("material_result").booleanValue());
            assertFalse(out.get("native_ai_score_computed").booleanValue());
        }
    }

    @Test
    void observedReleaseRefusalAndRansomAnswerRefusalDoNotBecomeMissingCandidates() throws IOException {
        var falseRelease = explain("gate_false");
        assertEquals(4, falseRelease.candidates().size());
        assertEquals(Gate.REFUSED, falseRelease.candidates().get(2).releaseGate());
        assertEquals(Gate.UNAVAILABLE, falseRelease.candidates().get(2).ransomGate());
        assertEquals("final_can_send_false", assertInstanceOf(UnavailableQuote.class, falseRelease.candidates().get(2).ransomQuote()).reason());
        var falseRansom = explain("selected_change_prison");
        assertEquals(Gate.REFUSED, falseRansom.candidates().get(2).ransomGate());
        assertEquals(Gate.UNAVAILABLE, falseRansom.candidates().get(2).releaseGate());
    }

    @Test
    void quoteIntegerAndBooleanTokensRejectCoercionsMissingExtraDuplicateAndTrailingFields() throws IOException {
        String canonical = new String(StrictJson.canonical(availableQuote()), StandardCharsets.UTF_8);
        for (String field : List.of("native_revision", "public_revision", "proof_epoch", "payer_character_id", "quoted_gold_raw", "recipient_answer_status_raw")) {
            JsonNode value = availableQuote().get(field);
            String needle = "\"" + field + "\":" + value;
            for (String replacement : List.of("true", value + ".0", "\"" + value + "\"", "null")) {
                byte[] raw = canonical.replace(needle, "\"" + field + "\":" + replacement).getBytes(StandardCharsets.UTF_8);
                assertThrows(IllegalArgumentException.class, () -> PrisonerVanillaResearch.decodeQuote(raw, FRAME, EPOCH), field + "/" + replacement);
            }
        }
        for (String field : List.of("proof_epoch", "unavailable_reason", "would_accept_now", "selected_option")) {
            ObjectNode missing = availableQuote(); missing.remove(field);
            assertThrows(IllegalArgumentException.class, () -> PrisonerVanillaResearch.readQuote(missing, FRAME, EPOCH));
        }
        ObjectNode extra = availableQuote(); extra.put("applied", true);
        assertThrows(IllegalArgumentException.class, () -> PrisonerVanillaResearch.readQuote(extra, FRAME, EPOCH));
        ObjectNode bool = availableQuote(); bool.put("can_send", 1);
        assertThrows(IllegalArgumentException.class, () -> PrisonerVanillaResearch.readQuote(bool, FRAME, EPOCH));
        assertThrows(IllegalArgumentException.class, () -> PrisonerVanillaResearch.decodeQuote(
                canonical.replace("\"can_send\":true", "\"can_send\":true,\"can_send\":false").getBytes(StandardCharsets.UTF_8), FRAME, EPOCH));
        assertThrows(IllegalArgumentException.class, () -> PrisonerVanillaResearch.decodeQuote((canonical + "{}").getBytes(StandardCharsets.UTF_8), FRAME, EPOCH));
    }

    @Test
    void acceptanceTimeQuoteIsNotAFixedPaymentPromiseAndNativeScoreIsNotAProbability() throws IOException {
        ObjectNode value = availableQuote(); value.put("selected_option", "current_gold").put("amount_is_acceptance_time_quote", true)
                .put("recipient_acceptance_raw", Long.MIN_VALUE).put("recipient_answer_status_raw", 2).put("would_accept_now", false);
        AvailableQuote quote = assertInstanceOf(AvailableQuote.class, PrisonerVanillaResearch.readQuote(value, FRAME, EPOCH));
        assertTrue(quote.amountIsAcceptanceTimeQuote()); assertFalse(quote.wouldAcceptNow());
        assertEquals(Long.MIN_VALUE, quote.recipientAcceptanceRaw());
        assertJsonRepresentation(value, PrisonerVanillaResearch.quoteJson(quote));
        value.put("amount_is_acceptance_time_quote", false);
        assertThrows(IllegalArgumentException.class, () -> PrisonerVanillaResearch.readQuote(value, FRAME, EPOCH));
    }

    @Test
    void nativeFullWidthsAndFrameRolesRemainExact() throws IOException {
        FrameBinding wide = new FrameBinding(StrictJson.UINT64_MAX, Integer.MIN_VALUE, 0xffff_ffffL, 0xffff_fffeL);
        AvailableQuote quote = new AvailableQuote(wide, StrictJson.UINT64_MAX, 0xffff_fffdL, PrisonerVanillaResearch.Option.GOLD,
                Long.MAX_VALUE, Long.MIN_VALUE, 0);
        assertEquals(quote, PrisonerVanillaResearch.decodeQuote(StrictJson.canonical(PrisonerVanillaResearch.quoteJson(quote)), wide, StrictJson.UINT64_MAX));
        ObjectNode wrong = availableQuote(); wrong.put("prisoner_character_id", 61541);
        assertThrows(IllegalArgumentException.class, () -> PrisonerVanillaResearch.readQuote(wrong, FRAME, EPOCH));
        ObjectNode wrongEpoch = availableQuote(); wrongEpoch.put("proof_epoch", EPOCH.add(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> PrisonerVanillaResearch.readQuote(wrongEpoch, FRAME, EPOCH));
    }

    @Test
    void unavailableDiagnosticsPreserveNullAndAbsentAndUnknownReasons() {
        for (var quote : List.of(new UnavailableQuote("future_reason_未知", new PrisonerVanillaResearch.NoQuoteDiagnostic()),
                new UnavailableQuote("option_definition_count_unexpected", new OptionCounts(-1, null)),
                new UnavailableQuote("option_definition_count_unexpected", new OptionCounts(9, 8)),
                new UnavailableQuote("option_mask_unexpected", new OptionMask(2, 8)),
                new UnavailableQuote("option_mask_unexpected", new OptionMask(2, 256)),
                new UnavailableQuote("option_mask_unexpected", new OptionMask(2, 511)),
                new UnavailableQuote("option_mask_unexpected", new PrisonerVanillaResearch.NoQuoteDiagnostic()))) {
            assertEquals(quote, PrisonerVanillaResearch.decodeQuote(StrictJson.canonical(PrisonerVanillaResearch.quoteJson(quote)), FRAME, EPOCH));
        }
        ObjectNode missing = PrisonerVanillaResearch.quoteJson(new UnavailableQuote("option_definition_count_unexpected", new OptionCounts(-1, null)));
        missing.remove("observed_context_option_count");
        assertThrows(IllegalArgumentException.class, () -> PrisonerVanillaResearch.readQuote(missing, FRAME, EPOCH));
        assertThrows(IllegalArgumentException.class, () -> new OptionMask(2, 4));
        assertThrows(IllegalArgumentException.class, () -> new OptionMask(2, 512));
    }

    @Test
    void schemaOnlyKinshipPreservesBothPredicatesWithoutPromotingOldBuildQualification() throws IOException {
        ObjectNode root = (ObjectNode) StrictJson.parse(resource("native12004/gate_true.json"), 131072);
        ((ObjectNode) root.get("player_prisoner_collection")).put("schema_version", 7);
        JsonNode rows = root.get("player_prisoner_collection").get("prisoners");
        for (int ordinal = 0; ordinal < rows.size(); ordinal++) {
            NativeKinship12003 observation = ordinal == 2
                    ? new NativeKinship12003.Available(FRAME, EPOCH, 2, false, true)
                    : new NativeKinship12003.Unavailable("not_evaluated");
            ((ObjectNode) rows.get(ordinal)).set("native_kinship", NativeKinshipCodec12003.toNode(observation));
        }
        var explanation = PrisonerVanillaResearch.explain(StrictJson.canonical(root), SupportedBuild.CK3_12004, FRAME, BigInteger.valueOf(37), catalog);
        var preserved = assertInstanceOf(NativeKinship12003.Available.class, explanation.candidates().get(2).originalProjection().nativeKinship());
        assertFalse(preserved.closeFamily()); assertTrue(preserved.closeOrExtendedFamily());
        assertEquals(Knowledge.UNKNOWN, explanation.candidates().get(2).closeFamily());
        assertEquals(Knowledge.UNKNOWN, explanation.candidates().get(2).closeOrExtendedFamily());
        assertFalse(PrisonerVanillaResearch.explanationJson(explanation).get("current_build_kinship_qualified").booleanValue());
    }

    @Test
    void sourceDriftUnsupportedBuildAndWrongSelectedOrdinalRemainRed() throws IOException {
        byte[] changed = stock.clone(); changed[changed.length - 1] ^= 1;
        assertThrows(IllegalArgumentException.class, () -> PrisonerVanillaResearch.inspect(changed, catalog.source()));
        byte[] raw = resource("native12004/gate_true.json");
        assertThrows(IllegalArgumentException.class, () -> PrisonerVanillaResearch.explain(raw, SupportedBuild.CK3_12003, FRAME, BigInteger.ONE, catalog));
        ObjectNode root = (ObjectNode) StrictJson.parse(raw, 131072);
        root.put("step", "query-player-prisoner-collection-private-v1-ransom-ordinal-1");
        assertThrows(IllegalArgumentException.class, () -> PrisonerVanillaResearch.explain(StrictJson.canonical(root), SupportedBuild.CK3_12004,
                new FrameBinding(FRAME.nativeRevision(), FRAME.dateRaw(), FRAME.playerCharacterId(), 56063), BigInteger.ONE, catalog));
    }

    @Test
    void typedSourceAndCandidateCollectionsAreImmutable() throws IOException {
        assertThrows(UnsupportedOperationException.class, () -> catalog.interactions().clear());
        assertThrows(UnsupportedOperationException.class, () -> catalog.tree(Interaction.RANSOM).sections().clear());
        var explanation = explain("gate_true");
        assertThrows(UnsupportedOperationException.class, () -> explanation.candidates().clear());
        assertThrows(UnsupportedOperationException.class, () -> explanation.unresolvedInputs().clear());
        var original = explanation.candidates().get(2);
        assertThrows(IllegalArgumentException.class, () -> new PrisonerVanillaResearch.Candidate(original.sourceOrdinal(),
                original.prisonerCharacterId(), Gate.REFUSED, original.ransomQuote(), original.releaseGate(),
                Knowledge.UNKNOWN, Knowledge.UNKNOWN, original.originalProjection()));
        assertThrows(IllegalArgumentException.class, () -> new PrisonerVanillaResearch.Explanation(explanation.source(),
                explanation.originalCollectionSha256(), explanation.publicPlanningRevision(), explanation.nativeWireRevision(),
                explanation.proofEpoch(), List.of(original), explanation.unresolvedInputs()));
    }

    @Test
    void sourceTreeAndConcreteCandidateExplanationAreWrittenOnlyToFreshDeclaredArtifactPaths() throws IOException {
        String declaredOutput = System.getProperty("prisoner.research.output");
        Path output = declaredOutput == null ? Files.createTempDirectory(Path.of(System.getProperty("java.io.tmpdir")), "prisoner-research-")
                : Files.createDirectory(Path.of(declaredOutput)).toRealPath();
        assertTrue(Files.isDirectory(output));
        Files.write(output.resolve("PRISONER-SOURCE-TREE01.json"), StrictJson.canonical(PrisonerVanillaResearch.catalogJson(catalog), 1048576),
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        Files.writeString(output.resolve("PRISONER-SOURCE-TREE01.md"), PrisonerVanillaResearch.catalogMarkdown(catalog), StandardCharsets.UTF_8,
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        Files.write(output.resolve("PRISONER-CANDIDATE-EXPLANATION01.json"), StrictJson.canonical(PrisonerVanillaResearch.explanationJson(explain("gate_true"))),
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
    }

    private static void assertJsonRepresentation(JsonNode expected, JsonNode actual) {
        // JSON has one integral token domain; Jackson's IntNode/LongNode/BigIntegerNode storage choice is not content.
        // Runtime decoders separately reject booleans, floats, strings, missing fields and role/proof drift.
        assertArrayEquals(StrictJson.canonical(expected, 1048576), StrictJson.canonical(actual, 1048576));
    }
    private static String required(String property) {
        String value = System.getProperty(property);
        if (value == null || value.isBlank()) throw new IllegalArgumentException("required exact offline source input is absent: " + property);
        return value;
    }
    private static String atom(Assignment entry) { return assertInstanceOf(Atom.class, entry.value()).text(); }
    private static String cadence(Interaction kind, String tier) {
        return atom(PrisonerVanillaResearch.assignments(catalog.tree(kind).sections("ai_frequency_by_tier").getFirst().expression(), tier).getFirst());
    }
    private static long zeroFactors(Interaction kind) {
        return PrisonerVanillaResearch.assignments(catalog.tree(kind).sections("ai_will_do").getFirst().expression(), "factor").stream()
                .filter(entry -> entry.value() instanceof Atom value && value.text().equals("0")).count();
    }
    private static ObjectNode availableQuote() throws IOException {
        return (ObjectNode) StrictJson.parse(resource("native12004/gate_true.json"), 131072)
                .get("player_prisoner_collection").get("prisoners").get(2).get("ransom_quote_preview").deepCopy();
    }
    private static PrisonerVanillaResearch.Explanation explain(String name) throws IOException {
        return PrisonerVanillaResearch.explain(resource("native12004/" + name + ".json"),
                SupportedBuild.CK3_12004, FRAME, BigInteger.valueOf(37), catalog);
    }
    private static byte[] resource(String relative) throws IOException {
        return inputMode == InputMode.EXACT_EXTERNAL_SOURCE ? Files.readAllBytes(resources.resolve(relative)) : classpath("releasepreview/" + relative);
    }
    private static byte[] classpath(String relative) throws IOException {
        try (var stream = PrisonerVanillaResearchTest.class.getResourceAsStream("/prisoner-research/" + relative)) {
            if (stream == null) throw new IOException("required original-byte portable fixture missing: " + relative);
            return stream.readAllBytes();
        }
    }
}
