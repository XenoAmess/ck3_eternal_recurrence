package org.xar.ck3.markets.saveaudit;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.markets.saveaudit.FinancialProjector.LayoutHypothesis;
import org.xar.ck3.markets.saveaudit.FinancialProjector.NumberIdentityEncoding;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.ReceiptField;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.ReceiptProjection;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.Story;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.Type;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.SaveContracts.NativeId;
import org.xar.ck3.save.SaveJson;

/** Synthetic SAVE fixtures exercise the real existing reader/projector/report path; no Game/payment qualification. */
final class IssuanceReceiptProjectionTest {
    private static final String MACHINE = "synthetic-issuance-receipt-audit";
    private static final LayoutHypothesis STRICT = new LayoutHypothesis("synthetic", "999", BigInteger.valueOf(100000), "story", "char");
    private static final LayoutHypothesis ZERO = new LayoutHypothesis("1.21.0", "19", BigInteger.valueOf(100000), "story", "char", NumberIdentityEncoding.unsigned64OmittedZero);
    @TempDir Path directory;

    @Test void actualCoin85TypedSubtreesKeepFractionalGoldOmittedZeroAndLandedBaronIdentity() throws Exception {
        JsonNode fixture;
        try (var input = getClass().getResourceAsStream("/saveaudit/issuance-coin85-receipt-envelopes.json")) {
            assertNotNull(input); fixture = SaveJson.read(input.readAllBytes(), JsonNode.class);
        }
        assertEquals("e17f0fe982709756766e1563b82e11e379d29f5efc822f6e1b8eec2a67fb646b", fixture.get("source").get("sha256").textValue());
        List<Clausewitz.Entry> variables = new ArrayList<>();
        var fields = fixture.get("fields").properties().iterator();
        while (fields.hasNext()) {
            var field = fields.next();
            Clausewitz.Block data = SaveJson.read(SaveJson.write(field.getValue()), Clausewitz.Block.class);
            variables.add(new Clausewitz.Entry("", "", new Clausewitz.Block(List.of(
                    new Clausewitz.Entry("flag", "=", new Clausewitz.Atom(field.getKey())),
                    new Clausewitz.Entry("data", "=", data)))));
        }
        // The AST wrapper is authored software: this is not a complete actual coin/SAVE fixture.
        var ast = new Clausewitz.Block(List.of(
                new Clausewitz.Entry("story_cycle", "=", new Clausewitz.Atom("xfm_finance_coin")),
                new Clausewitz.Entry("variables", "=", new Clausewitz.Block(List.of(new Clausewitz.Entry("data", "=", new Clausewitz.Block(variables)))))));
        var projection = FinancialProjector.projectRecord(new NativeId("999999"), ast, ZERO);
        assertTrue(projection.issues().stream().allMatch(i -> i.field().equals("permanent_id")), "Software wrapper has no financial permanent ID");
        var receipt = projection.story().orElseThrow().issuanceReceipt();
        assertEquals(21, receipt.fields().size());
        assertEquals("4839355", receipt.fields().get(ReceiptField.GOLD_BEFORE).rawIdentity());
        assertEquals("4739355", receipt.fields().get(ReceiptField.GOLD_AFTER).rawIdentity());
        assertEquals("47364", receipt.fields().get(ReceiptField.ACTOR).rawIdentity());
        assertEquals("char", receipt.fields().get(ReceiptField.ACTOR).serializedType());
        assertEquals("14201", receipt.fields().get(ReceiptField.PAYER).rawIdentity());
        assertEquals("story", receipt.fields().get(ReceiptField.PAYER).serializedType());
        assertEquals("100000", receipt.fields().get(ReceiptField.IS_LANDED).rawIdentity());
        assertEquals("100000", receipt.fields().get(ReceiptField.HIGHEST_TIER).rawIdentity());
        assertFalse(receipt.fields().get(ReceiptField.FREE_AFTER).identityPresent());
        assertEquals("", receipt.fields().get(ReceiptField.FREE_AFTER).rawIdentity());
        assertEquals(receipt, SaveJson.read(SaveJson.write(receipt), ReceiptProjection.class));
    }

    @Test void existingTwoPassProducerProjectsAllTwentyOneEnvelopesWithoutFractionalGoldLoss() throws Exception {
        Path save = save("all.txt", allFields());
        var read = FinancialSaveReader.read(save, MACHINE, STRICT);
        var coin = coin(FinancialProjector.project(read, STRICT));
        assertTrue(coin.issuanceReceipt().observed());
        assertEquals(21, coin.issuanceReceipt().fields().size());
        assertEquals("812345", coin.issuanceReceipt().fields().get(ReceiptField.GOLD_BEFORE).rawIdentity());
        assertEquals("752345", coin.issuanceReceipt().fields().get(ReceiptField.GOLD_AFTER).rawIdentity());
        assertEquals("value", coin.issuanceReceipt().fields().get(ReceiptField.GOLD_BEFORE).serializedType());
        assertEquals("char", coin.issuanceReceipt().fields().get(ReceiptField.ACTOR).serializedType());
        assertEquals("31254", coin.issuanceReceipt().fields().get(ReceiptField.ACTOR).rawIdentity());
        assertEquals("story", coin.issuanceReceipt().fields().get(ReceiptField.PAYER).serializedType());
        assertEquals("2", coin.issuanceReceipt().fields().get(ReceiptField.PAYER).rawIdentity());
        assertEquals(2, read.coverage().passes(), "No added census or read pass");
        assertEquals(5, read.coverage().selectedFinancialRecords());
        assertEquals(FinancialAudit.Assessment.CANDIDATE_INVARIANTS_HOLD, FinancialAudit.audit(FinancialProjector.project(read, STRICT)).assessment());
        var output = inspect(save);
        var evidence = output.first().stories().stream().filter(s -> s.type().equals("xfm_finance_coin")).findFirst().orElseThrow();
        assertEquals(coin.issuanceReceipt(), evidence.issuanceReceipt());
        assertFalse(evidence.exactIntegers().containsKey(ReceiptField.GOLD_BEFORE.wire()), "Gold must never be rounded into integer cents");
        assertEquals(output, SaveJson.read(SaveJson.write(output), FinancialSaveAuditMain.Output.class));
        assertFalse(output.financialCertified());
    }

    @Test void plainAndZipSameStateColdComparisonIncludesReceiptAndKeepsOriginalEofCoverage() throws Exception {
        Path plain = save("plain.txt", allFields()), zipped = directory.resolve("cold.ck3");
        try (var zip = new ZipOutputStream(Files.newOutputStream(zipped))) {
            zip.putNextEntry(new ZipEntry("gamestate")); zip.write(Files.readAllBytes(plain)); zip.closeEntry();
        }
        var first = FinancialProjector.project(FinancialSaveReader.read(plain, MACHINE, STRICT), STRICT);
        var second = FinancialProjector.project(FinancialSaveReader.read(zipped, MACHINE, STRICT), STRICT);
        assertTrue(FinancialAudit.compareCold(first, second).exactSelectedFinancialState());
        assertEquals(coin(first).issuanceReceipt(), coin(second).issuanceReceipt());
        Files.writeString(plain, Files.readString(plain) + "unselected_malformed={");
        assertThrows(IOException.class, () -> FinancialSaveReader.read(plain, MACHINE, STRICT));
    }

    @Test void absentLegacyFieldsAndUncommittedPartialDataNeverReconstructCurrentIssuerIdentity() throws Exception {
        var legacy = FinancialProjector.project(FinancialSaveReader.read(save("legacy.txt", ""), MACHINE, STRICT), STRICT);
        assertTrue(coin(legacy).issuanceReceipt().observed());
        assertTrue(coin(legacy).issuanceReceipt().fields().isEmpty());
        var partial = project(n(ReceiptField.FREE_BEFORE, 40) + n(ReceiptField.IS_AI, 1), STRICT);
        assertEquals(2, partial.story().orElseThrow().issuanceReceipt().fields().size());
        assertFalse(partial.story().orElseThrow().issuanceReceipt().fields().containsKey(ReceiptField.VERSION));
        assertFalse(partial.story().orElseThrow().issuanceReceipt().fields().containsKey(ReceiptField.IS_LANDED));
        assertFalse(partial.story().orElseThrow().issuanceReceipt().fields().containsKey(ReceiptField.GOLD_BEFORE));
    }

    @Test void explicitZeroOmittedIdentityAndAbsentVariableRemainThreeDistinctRawStates() {
        var explicit = project(raw(ReceiptField.IS_LANDED, "value", "0"), ZERO).story().orElseThrow().issuanceReceipt();
        var omitted = project(raw(ReceiptField.IS_LANDED, "value", null), ZERO).story().orElseThrow().issuanceReceipt();
        var absent = project("", ZERO).story().orElseThrow().issuanceReceipt();
        assertTrue(explicit.fields().get(ReceiptField.IS_LANDED).identityPresent());
        assertEquals("0", explicit.fields().get(ReceiptField.IS_LANDED).rawIdentity());
        assertFalse(omitted.fields().get(ReceiptField.IS_LANDED).identityPresent());
        assertEquals("", omitted.fields().get(ReceiptField.IS_LANDED).rawIdentity());
        assertFalse(absent.fields().containsKey(ReceiptField.IS_LANDED));
        assertNotEquals(explicit, omitted); assertNotEquals(omitted, absent);
        var rejected = project(raw(ReceiptField.IS_LANDED, "value", null), STRICT);
        assertFalse(rejected.issues().isEmpty());
        assertFalse(rejected.story().orElseThrow().issuanceReceipt().fields().containsKey(ReceiptField.IS_LANDED));
    }

    @Test void wrongNumericAndReferenceTypesFractionalIntegersAndMalformedEnvelopesAreNotAccepted() {
        for (String invalid : List.of(
                raw(ReceiptField.GOLD_BEFORE, "story", "812345"),
                raw(ReceiptField.FEE_CENTS, "char", "100"),
                raw(ReceiptField.FEE_CENTS, "value", "10000001"),
                raw(ReceiptField.FEE_CENTS, "value", "\"10000000\""),
                raw(ReceiptField.ACTOR, "story", "31254"),
                raw(ReceiptField.PAYER, "char", "2"),
                raw(ReceiptField.ACTOR, "char", null),
                raw(ReceiptField.PAYER, "story", "-1"),
                raw(ReceiptField.GOLD_BEFORE, "value", "{bad=yes}"),
                raw(ReceiptField.GOLD_BEFORE, "value", "812345 identity=812345"),
                raw(ReceiptField.GOLD_BEFORE, "value", "812345 extra=1"))) {
            var rejected = project(invalid, STRICT);
            assertFalse(rejected.issues().isEmpty(), invalid);
            assertTrue(rejected.story().orElseThrow().issuanceReceipt().fields().isEmpty(), invalid);
        }
        var duplicate = project(n(ReceiptField.FEE_CENTS, 100) + n(ReceiptField.FEE_CENTS, 100), STRICT);
        assertTrue(duplicate.issues().stream().anyMatch(i -> i.severity() == FinancialSnapshot.Severity.VIOLATION));
    }

    @Test void unsignedIdentityAndCharacterStoryIdsRemainExactTextPastJavascriptSafeIntegers() throws Exception {
        String unsignedMinusOne = "18446744073709451616";
        String actor = "9007199254740993", payer = "18446744073709551615";
        var p = project(raw(ReceiptField.HIGHEST_TIER, "value", unsignedMinusOne)
                + raw(ReceiptField.ACTOR, "char", actor) + raw(ReceiptField.PAYER, "story", payer), ZERO);
        assertTrue(p.issues().isEmpty());
        var receipt = p.story().orElseThrow().issuanceReceipt();
        assertEquals(unsignedMinusOne, receipt.fields().get(ReceiptField.HIGHEST_TIER).rawIdentity());
        assertEquals(actor, receipt.fields().get(ReceiptField.ACTOR).rawIdentity());
        assertEquals(payer, receipt.fields().get(ReceiptField.PAYER).rawIdentity());
        assertEquals(receipt, SaveJson.read(SaveJson.write(receipt), ReceiptProjection.class));
        var json = SaveJson.read(SaveJson.write(receipt), JsonNode.class);
        assertTrue(json.get("fields").get(ReceiptField.HIGHEST_TIER.wire()).get("rawIdentity").isTextual());
        assertFalse(project(raw(ReceiptField.GOLD_BEFORE, "value", "18446744073709551616"), ZERO).issues().isEmpty());
    }

    @Test void legacyReportSchemaDecodesOnlyAbsentNewFieldAsUnknownAndKeepsOldDataExact() throws Exception {
        var report = inspect(save("old-schema.txt", ""));
        ObjectNode oldJson = (ObjectNode) SaveJson.read(SaveJson.write(report), JsonNode.class);
        oldJson.get("first").get("stories").forEach(s -> ((ObjectNode) s).remove("issuanceReceipt"));
        var old = SaveJson.read(SaveJson.write(oldJson), FinancialSaveAuditMain.Output.class);
        assertEquals(report.schema(), old.schema());
        assertEquals(report.layoutHypothesis(), old.layoutHypothesis());
        assertEquals(report.first().audit(), old.first().audit());
        for (int i = 0; i < report.first().stories().size(); i++) {
            var before = old.first().stories().get(i); var now = report.first().stories().get(i);
            assertEquals(now.exactIntegers(), before.exactIntegers());
            assertEquals(now.scopeReferences(), before.scopeReferences());
            assertEquals(now.permanentId(), before.permanentId());
            assertFalse(before.issuanceReceipt().observed());
        }
        var currentCoin = report.first().stories().stream().filter(s -> s.type().equals("xfm_finance_coin")).findFirst().orElseThrow();
        var oldCoin = old.first().stories().stream().filter(s -> s.type().equals("xfm_finance_coin")).findFirst().orElseThrow();
        assertNotEquals(currentCoin, oldCoin, "An old unprojected report cannot silently become a complete new baseline");
    }

    @Test void legacyCompatibilityDoesNotAdmitPresentNullUnknownFieldsOrNumericJsonIdentities() throws Exception {
        var report = inspect(save("boundary.txt", allFields()));
        var story = report.first().stories().stream().filter(s -> s.type().equals("xfm_finance_coin")).findFirst().orElseThrow();
        byte[] encoded = SaveJson.write(story);
        for (String change : List.of("null", "true", "0", "[]", "{}")) {
            ObjectNode node = (ObjectNode) SaveJson.read(encoded, JsonNode.class);
            node.set("issuanceReceipt", SaveJson.read(("{\"value\":" + change + "}").getBytes(StandardCharsets.UTF_8), JsonNode.class).get("value"));
            assertThrows(IOException.class, () -> SaveJson.read(SaveJson.write(node), FinancialSaveAuditMain.StoryEvidence.class));
        }
        ObjectNode unknown = (ObjectNode) SaveJson.read(encoded, JsonNode.class); unknown.put("unknown", true);
        assertThrows(IOException.class, () -> SaveJson.read(SaveJson.write(unknown), FinancialSaveAuditMain.StoryEvidence.class));
        ObjectNode numericId = (ObjectNode) SaveJson.read(encoded, JsonNode.class);
        ((ObjectNode) numericId.get("issuanceReceipt").get("fields").get(ReceiptField.ACTOR.wire())).put("rawIdentity", 31254);
        assertThrows(IOException.class, () -> SaveJson.read(SaveJson.write(numericId), FinancialSaveAuditMain.StoryEvidence.class));
        ObjectNode unknownFlag = (ObjectNode) SaveJson.read(encoded, JsonNode.class);
        ((ObjectNode) unknownFlag.get("issuanceReceipt").get("fields")).putObject("xfm_issue_receipt_unknown");
        assertThrows(IOException.class, () -> SaveJson.read(SaveJson.write(unknownFlag), FinancialSaveAuditMain.StoryEvidence.class));
        assertThrows(IllegalArgumentException.class, () -> new ReceiptProjection(false, story.issuanceReceipt().fields()));
    }

    @Test void coldComparisonRejectsReceiptChangeAndUnobservedHistoryWithoutDroppingOtherCoinChanges() throws Exception {
        var before = FinancialProjector.project(FinancialSaveReader.read(save("before.txt", allFields()), MACHINE, STRICT), STRICT);
        var changed = FinancialProjector.project(FinancialSaveReader.read(save("changed.txt", allFields().replace("identity=812345", "identity=812346")), MACHINE, STRICT), STRICT);
        assertFalse(FinancialAudit.compareCold(before, changed).exactSelectedFinancialState());
        List<Story> oldStories = new ArrayList<>(before.stories());
        Story coin = coin(before);
        oldStories.set(oldStories.indexOf(coin), new Story(coin.type(), coin.nativeId(), coin.permanentId(), coin.numbers(), coin.references()));
        var old = new FinancialSnapshot(before.machineId(), before.saveSha256(), before.gameVersion(), before.saveFormat(), before.gameDate(), oldStories, before.issues());
        assertFalse(FinancialAudit.compareCold(old, before).exactSelectedFinancialState());
        Path supply = save("supply.txt", allFields());
        Files.writeString(supply, Files.readString(supply).replace("flag=xfm_supply_units data={type=value identity=100000000}", "flag=xfm_supply_units data={type=value identity=99900000}"));
        var mismatched = FinancialProjector.project(FinancialSaveReader.read(supply, MACHINE, STRICT), STRICT);
        assertFalse(FinancialAudit.compareCold(before, mismatched).exactSelectedFinancialState());
    }

    @Test void twentyOneAdditionalProjectedFieldsConsumeExistingFiniteBudget() throws Exception {
        Path legacy = save("budget-old.txt", ""), receipt = save("budget-new.txt", allFields());
        var oldRead = FinancialSaveReader.read(legacy, MACHINE, STRICT);
        var newRead = FinancialSaveReader.read(receipt, MACHINE, STRICT);
        assertEquals(oldRead.coverage().projectedFields() + 21, newRead.coverage().projectedFields());
        var standard = FinancialSaveReader.Budgets.standard();
        var exact = new FinancialSaveReader.Budgets(standard.maxTableRecords(), standard.maxFinancialRecords(), standard.maxRecordBytes(), standard.maxStreamedBytes(), newRead.coverage().projectedFields());
        assertEquals(newRead.coverage().projectedFields(), FinancialSaveReader.read(receipt, MACHINE, STRICT, exact).coverage().projectedFields());
        var shortBudget = new FinancialSaveReader.Budgets(standard.maxTableRecords(), standard.maxFinancialRecords(), standard.maxRecordBytes(), standard.maxStreamedBytes(), newRead.coverage().projectedFields() - 1);
        assertThrows(IOException.class, () -> FinancialSaveReader.read(receipt, MACHINE, STRICT, shortBudget));
    }

    private FinancialSaveAuditMain.Output inspect(Path save) throws IOException {
        return FinancialSaveAuditMain.inspect(new FinancialSaveAuditMain.Inputs(MACHINE, FilePins.pin(save), List.of(), STRICT, List.of()));
    }
    private Path save(String name, String receipt) throws IOException {
        Path target = directory.resolve(name);
        String anchor = "4={story_cycle=xfm_finance_coin owner=31254 variables={data={";
        String scene = FinancialSaveAuditSelfTest.scene();
        assertTrue(scene.contains(anchor)); Files.writeString(target, scene.replace(anchor, anchor + receipt)); return target;
    }
    private static Story coin(FinancialSnapshot snapshot) { return snapshot.stories().stream().filter(s -> s.type() == Type.COIN).findFirst().orElseThrow(); }
    private static FinancialProjector.RecordProjection project(String variables, LayoutHypothesis layout) {
        return FinancialProjector.projectRecord(new NativeId("85"), Clausewitz.parse("story_cycle=xfm_finance_coin variables={data={{flag=xfm_coin_id data={type=value identity=100000}}" + variables + "}}"), layout);
    }
    private static String raw(ReceiptField field, String type, String identity) {
        return "{flag=" + field.wire() + " data={type=" + type + (identity == null ? "" : " identity=" + identity) + "}}";
    }
    private static String n(ReceiptField field, long number) { return raw(field, "value", BigInteger.valueOf(number).multiply(BigInteger.valueOf(100000)).toString()); }
    private static String allFields() {
        return n(ReceiptField.COIN_ID, 1) + raw(ReceiptField.ACTOR, "char", "31254") + raw(ReceiptField.PAYER, "story", "2")
                + n(ReceiptField.PAYER_ID, 1) + n(ReceiptField.DAY, 2) + n(ReceiptField.IS_AI, 1) + n(ReceiptField.IS_LANDED, 0)
                + n(ReceiptField.HIGHEST_TIER, 1) + n(ReceiptField.FEE_CENTS, 100)
                + raw(ReceiptField.GOLD_BEFORE, "value", "812345") + raw(ReceiptField.GOLD_PRE_FEE, "value", "752345") + raw(ReceiptField.GOLD_AFTER, "value", "752345")
                + n(ReceiptField.FREE_BEFORE, 40) + n(ReceiptField.FREE_PRE_FEE, 100) + n(ReceiptField.FREE_AFTER, 0)
                + n(ReceiptField.RESERVED_BEFORE, 7) + n(ReceiptField.RESERVED_AFTER, 7)
                + n(ReceiptField.FEES_BEFORE, 20) + n(ReceiptField.FEES_AFTER, 120) + n(ReceiptField.TOPUP_CENTS, 60) + n(ReceiptField.VERSION, 1);
    }
}
