package org.xar.ck3.markets.saveaudit;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.markets.saveaudit.FinancialProjector.LayoutHypothesis;
import org.xar.ck3.markets.saveaudit.FinancialProjector.NumberIdentityEncoding;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.NumberField;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.ReferenceField;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.Story;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.Type;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.SaveContracts.NativeId;
import org.xar.ck3.save.SaveJson;

/** Real existing parser/reader/projector/report path, authored fixtures; no Game/entity qualification. */
final class CoinEntityProjectionTest {
    private static final String MACHINE = "synthetic-coin-entity-audit";
    private static final LayoutHypothesis STRICT = new LayoutHypothesis("synthetic", "999", BigInteger.valueOf(100000), "story", "char");
    private static final LayoutHypothesis ZERO = new LayoutHypothesis("1.21.0", "19", BigInteger.valueOf(100000), "story", "char", NumberIdentityEncoding.unsigned64OmittedZero);
    @TempDir Path directory;

    @Test void actualCoin85SubtreesPreservePersonalTypeAndCharacterBindingWithoutReconstructingReceipt() throws Exception {
        JsonNode fixture;
        try (var input = getClass().getResourceAsStream("/saveaudit/coin85-entity-envelopes.json")) {
            assertNotNull(input); fixture = SaveJson.read(input.readAllBytes(), JsonNode.class);
        }
        assertEquals("bcaa0a9dd00ef8befee680fef765076ce1f5be0fe41ff0026d0b8867eef4aadc", fixture.get("source").get("sha256").textValue());
        List<Clausewitz.Entry> variables = new ArrayList<>();
        for (var item : fixture.get("fields").properties()) {
            Clausewitz.Block data = SaveJson.read(SaveJson.write(item.getValue()), Clausewitz.Block.class);
            variables.add(new Clausewitz.Entry("", "", new Clausewitz.Block(List.of(
                    new Clausewitz.Entry("flag", "=", new Clausewitz.Atom(item.getKey())), new Clausewitz.Entry("data", "=", data)))));
        }
        // Only the selected data subtrees are actual; the small enclosing coin AST is authored software.
        var ast = new Clausewitz.Block(List.of(new Clausewitz.Entry("story_cycle", "=", new Clausewitz.Atom("xfm_finance_coin")),
                new Clausewitz.Entry("variables", "=", new Clausewitz.Block(List.of(new Clausewitz.Entry("data", "=", new Clausewitz.Block(variables)))))));
        var projected = FinancialProjector.projectRecord(new NativeId("33563487"), ast, ZERO);
        assertTrue(projected.issues().isEmpty());
        var coin = projected.story().orElseThrow();
        assertEquals("85", coin.permanentId().orElseThrow().value());
        assertEquals(BigInteger.ONE, coin.number(NumberField.ENTITY_TYPE).orElseThrow());
        assertEquals("char", coin.reference(ReferenceField.BOUND_ENTITY).orElseThrow().serializedType());
        assertEquals("47364", coin.reference(ReferenceField.BOUND_ENTITY).orElseThrow().nativeId().value());
        assertEquals(21, FinancialSnapshot.ReceiptField.values().length);
        assertTrue(coin.issuanceReceipt().fields().isEmpty(), "No issuance fee/history fields invented from current binding");
    }

    @Test void existingTwoPassReaderAndReportPreserveNamespacesWithoutForcingCharacterOrStory() throws Exception {
        // Except char above these are synthetic namespace tokens, not claims about actual engine spellings.
        for (String namespace : List.of("char", "dynasty_house", "dynasty", "title", "faith", "story")) {
            Path save = save(namespace + ".txt", number("xfm_entity_type", 4) + ref("xfm_bound_entity", namespace, "9007199254740993"));
            var output = inspect(save); var coin = evidenceCoin(output);
            assertEquals("4", coin.exactIntegers().get("xfm_entity_type"));
            assertEquals(namespace, coin.scopeReferences().get("xfm_bound_entity").serializedType());
            assertEquals("9007199254740993", coin.scopeReferences().get("xfm_bound_entity").nativeId());
            assertEquals(2, output.first().streamingCoverage().passes());
            assertEquals(5, output.first().streamingCoverage().selectedFinancialRecords());
            assertEquals(FinancialAudit.Assessment.CANDIDATE_INVARIANTS_HOLD, output.first().audit().assessment());
            assertEquals(output, SaveJson.read(SaveJson.write(output), FinancialSaveAuditMain.Output.class));
            var json = SaveJson.read(SaveJson.write(coin), JsonNode.class);
            assertTrue(json.get("exactIntegers").get("xfm_entity_type").isTextual());
            assertTrue(json.get("scopeReferences").get("xfm_bound_entity").get("nativeId").isTextual());
            assertFalse(output.financialCertified());
        }
    }

    @Test void unknownPositiveEntityCodeAndNamespaceRemainLiteralNotAnInventedKnownEntity() {
        var p = project(number("xfm_entity_type", 99) + ref("xfm_bound_entity", "future_domain", "18446744073709551615"), STRICT);
        assertTrue(p.issues().isEmpty()); var coin = p.story().orElseThrow();
        assertEquals(BigInteger.valueOf(99), coin.number(NumberField.ENTITY_TYPE).orElseThrow());
        assertEquals("future_domain", coin.reference(ReferenceField.BOUND_ENTITY).orElseThrow().serializedType());
        assertEquals("18446744073709551615", coin.reference(ReferenceField.BOUND_ENTITY).orElseThrow().nativeId().value());
        assertFalse(ReferenceField.BOUND_ENTITY.characterReference());
        assertFalse(ReferenceField.BOUND_ENTITY.financialStoryReference(), "Namespace remains uninterpreted, not a financial-story lookup");
    }

    @Test void absentLegacyFieldsStayUnknownWhileExplicitZeroAndPartialBindingRemainDistinct() {
        var old = project("", STRICT).story().orElseThrow();
        assertTrue(old.number(NumberField.ENTITY_TYPE).isEmpty()); assertTrue(old.reference(ReferenceField.BOUND_ENTITY).isEmpty());
        var explicit = project(number("xfm_entity_type", 0), STRICT).story().orElseThrow();
        assertEquals(BigInteger.ZERO, explicit.number(NumberField.ENTITY_TYPE).orElseThrow());
        assertTrue(explicit.reference(ReferenceField.BOUND_ENTITY).isEmpty()); assertNotEquals(old, explicit);
        var scopeOnly = project(ref("xfm_bound_entity", "title", "0"), STRICT).story().orElseThrow();
        assertTrue(scopeOnly.number(NumberField.ENTITY_TYPE).isEmpty());
        assertEquals("0", scopeOnly.reference(ReferenceField.BOUND_ENTITY).orElseThrow().nativeId().value());
        var omitted = project("{flag=xfm_entity_type data={type=value}}", ZERO);
        assertTrue(omitted.issues().isEmpty()); assertEquals(BigInteger.ZERO, omitted.story().orElseThrow().number(NumberField.ENTITY_TYPE).orElseThrow());
        assertFalse(project("{flag=xfm_bound_entity data={type=title}}", ZERO).issues().isEmpty(), "A scope identity is never manufactured by numeric omitted-zero rules");
    }

    @Test void malformedNumbersScopesDuplicateFieldsAndUnsignedOverflowRemainIncomplete() {
        for (String invalid : List.of(
                "{flag=xfm_entity_type data={type=value identity=400001}}",
                ref("xfm_entity_type", "story", "4"),
                "{flag=xfm_entity_type data={type=value identity=400000 extra=1}}",
                ref("xfm_bound_entity", "value", "400000"),
                ref("xfm_bound_entity", "title", "01"),
                ref("xfm_bound_entity", "title", "18446744073709551616"),
                "{flag=xfm_bound_entity data={type=title identity=12 identity=13}}",
                "{flag=xfm_bound_entity data={type=title identity={12}}}",
                "{flag=xfm_bound_entity data={type=title identity=12 extra=1}}",
                ref("xfm_bound_entity", "title", "12") + ref("xfm_bound_entity", "title", "12"),
                number("xfm_entity_type", 4) + number("xfm_entity_type", 4))) {
            assertFalse(project(invalid, STRICT).issues().isEmpty(), invalid);
        }
        var nonCoin = FinancialProjector.projectRecord(new NativeId("2"), Clausewitz.parse("story_cycle=xfm_finance_account variables={data={"
                + number("xfm_account_id", 1) + number("xfm_entity_type", 4) + ref("xfm_bound_entity", "title", "12") + "}}"), STRICT).story().orElseThrow();
        assertTrue(nonCoin.number(NumberField.ENTITY_TYPE).isEmpty()); assertTrue(nonCoin.reference(ReferenceField.BOUND_ENTITY).isEmpty());
    }

    @Test void externalBindingDoesNotWeakenOrdinaryFinancialReferenceObligationChecks() throws Exception {
        var good = inspect(save("external.txt", number("xfm_entity_type", 4) + ref("xfm_bound_entity", "title", "999999")));
        assertEquals(FinancialAudit.Assessment.CANDIDATE_INVARIANTS_HOLD, good.first().audit().assessment());
        var bad = inspect(save("financial-dangling.txt", number("xfm_entity_type", 4) + ref("xfm_bound_entity", "title", "999999") + ref("xfm_issuer_account", "story", "999998")));
        assertEquals(FinancialAudit.Assessment.INCOMPLETE, bad.first().audit().assessment());
        assertTrue(bad.first().audit().issues().stream().anyMatch(i -> i.field().equals("xfm_issuer_account") && i.detail().contains("unresolved")));
        assertFalse(bad.first().audit().issues().stream().anyMatch(i -> i.field().equals("xfm_bound_entity")));
        for (ReferenceField field : ReferenceField.values())
            assertEquals(!field.characterReference() && field != ReferenceField.BOUND_ENTITY, field.financialStoryReference());
    }

    @Test void sameStateColdEqualityIncludesBothFieldsAndOldMapAbsenceNeverBecomesZero() throws Exception {
        String fields = number("xfm_entity_type", 4) + ref("xfm_bound_entity", "title", "12");
        Path plain = save("before.txt", fields), zipPath = directory.resolve("cold.ck3");
        try (var zip = new ZipOutputStream(Files.newOutputStream(zipPath))) { zip.putNextEntry(new ZipEntry("gamestate")); zip.write(Files.readAllBytes(plain)); zip.closeEntry(); }
        var before = snapshot(plain); assertTrue(FinancialAudit.compareCold(before, snapshot(zipPath)).exactSelectedFinancialState());
        for (String changed : List.of(fields.replace("identity=400000", "identity=300000"), fields.replace("identity=12", "identity=13"), fields.replace("type=title", "type=dynasty"), ""))
            assertFalse(FinancialAudit.compareCold(before, snapshot(save("change-" + Math.abs(changed.hashCode()) + ".txt", changed))).exactSelectedFinancialState());
        var legacyReport = inspect(save("legacy.txt", ""));
        var decoded = SaveJson.read(SaveJson.write(legacyReport), FinancialSaveAuditMain.Output.class);
        assertFalse(evidenceCoin(decoded).exactIntegers().containsKey("xfm_entity_type"));
        assertFalse(evidenceCoin(decoded).scopeReferences().containsKey("xfm_bound_entity"));
        assertEquals(legacyReport, decoded); assertFalse(decoded.financialCertified());
    }

    @Test void bothNewFieldsConsumeOriginalFiniteBudgetAndMalformedTailStillRejects() throws Exception {
        Path old = save("budget-old.txt", ""), added = save("budget-new.txt", number("xfm_entity_type", 4) + ref("xfm_bound_entity", "title", "12"));
        var before = FinancialSaveReader.read(old, MACHINE, STRICT); var after = FinancialSaveReader.read(added, MACHINE, STRICT);
        assertEquals(before.coverage().projectedFields() + 2, after.coverage().projectedFields());
        var standard = FinancialSaveReader.Budgets.standard();
        var shortBudget = new FinancialSaveReader.Budgets(standard.maxTableRecords(), standard.maxFinancialRecords(), standard.maxRecordBytes(), standard.maxStreamedBytes(), after.coverage().projectedFields() - 1);
        assertThrows(IOException.class, () -> FinancialSaveReader.read(added, MACHINE, STRICT, shortBudget));
        Files.writeString(added, Files.readString(added) + "malformed_unselected_tail={");
        assertThrows(IOException.class, () -> FinancialSaveReader.read(added, MACHINE, STRICT));
    }

    private FinancialSaveAuditMain.Output inspect(Path save) throws IOException {
        return FinancialSaveAuditMain.inspect(new FinancialSaveAuditMain.Inputs(MACHINE, FilePins.pin(save), List.of(), STRICT, List.of()));
    }
    private FinancialSnapshot snapshot(Path save) throws IOException { return FinancialProjector.project(FinancialSaveReader.read(save, MACHINE, STRICT), STRICT); }
    private Path save(String name, String fields) throws IOException {
        Path target = directory.resolve(name); String scene = FinancialSaveAuditSelfTest.scene();
        String anchor = "4={story_cycle=xfm_finance_coin owner=31254 variables={data={";
        assertTrue(scene.contains(anchor)); Files.writeString(target, scene.replace(anchor, anchor + fields)); return target;
    }
    private static FinancialSaveAuditMain.StoryEvidence evidenceCoin(FinancialSaveAuditMain.Output output) {
        return output.first().stories().stream().filter(s -> s.type().equals("xfm_finance_coin")).findFirst().orElseThrow();
    }
    private static FinancialProjector.RecordProjection project(String fields, LayoutHypothesis layout) {
        return FinancialProjector.projectRecord(new NativeId("4"), Clausewitz.parse("story_cycle=xfm_finance_coin variables={data={" + number("xfm_coin_id", 1) + fields + "}}"), layout);
    }
    private static String number(String field, long value) { return "{flag=" + field + " data={type=value identity=" + BigInteger.valueOf(value).multiply(BigInteger.valueOf(100000)) + "}}"; }
    private static String ref(String field, String type, String id) { return "{flag=" + field + " data={type=" + type + " identity=" + id + "}}"; }
}
