package org.xar.ck3.markets.saveaudit;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.markets.saveaudit.FinancialProjector.LayoutHypothesis;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.NumberField;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.SaveContracts.NativeId;
import org.xar.ck3.save.SaveJson;

/** Existing integer projection/report only; authored fixture, no historical fill, physical SAVE or Game credit. */
final class FuturesFillReceiptProjectionTest {
    private static final LayoutHypothesis LAYOUT = new LayoutHypothesis("synthetic", "999", BigInteger.valueOf(100000), "story", "char");
    @TempDir Path directory;

    @Test void allThirteenPrimitiveFieldsUseOriginalTwoPassReaderAndExactStringReportSchema() throws Exception {
        StringBuilder fields = new StringBuilder(); int count = 0;
        for (NumberField field : NumberField.values()) if (field.name().startsWith("FILL_")) { fields.append(number(field.wire(), 1)); count++; }
        assertEquals(13, count);
        String base = FinancialSaveAuditSelfTest.scene(), extra = "6={story_cycle=xfm_futures_position variables={data={" + number("xfm_position_id", 1) + fields + "}}}";
        Path save = directory.resolve("primitive-fill.txt"); Files.writeString(save, base.substring(0, base.length() - 2) + extra + "}}");
        var output = FinancialSaveAuditMain.inspect(new FinancialSaveAuditMain.Inputs("synthetic-fill-receipt", FilePins.pin(save), List.of(), LAYOUT, List.of()));
        var story = output.first().stories().stream().filter(s -> s.type().equals("xfm_futures_position")).findFirst().orElseThrow();
        for (NumberField field : NumberField.values()) if (field.name().startsWith("FILL_")) assertEquals("1", story.exactIntegers().get(field.wire()));
        assertTrue(story.scopeReferences().isEmpty(), "No weak archived order reference contract added");
        assertEquals(2, output.first().streamingCoverage().passes());
        assertEquals(output, SaveJson.read(SaveJson.write(output), FinancialSaveAuditMain.Output.class));
        var json = SaveJson.read(SaveJson.write(story), JsonNode.class);
        assertTrue(json.get("exactIntegers").get("xfm_fill_buy_order_id").isTextual()); assertFalse(output.financialCertified());
    }

    @Test void oldAbsentFieldsRemainUnknownAndWrongTypeFractionalIdOrDuplicateDataStillReject() {
        var old = project("").story().orElseThrow();
        for (NumberField field : NumberField.values()) if (field.name().startsWith("FILL_")) assertTrue(old.number(field).isEmpty());
        var explicitOpening = project(number("xfm_fill_receipt_version", 1) + number("xfm_fill_buy_intent", 0)).story().orElseThrow();
        assertEquals(BigInteger.ZERO, explicitOpening.number(NumberField.FILL_BUY_INTENT).orElseThrow());
        assertTrue(explicitOpening.number(NumberField.FILL_BUY_CLOSE_SOURCE_ID).isEmpty());
        for (String invalid : List.of(
                "{flag=xfm_fill_buy_order_id data={type=value identity=23100001}}",
                "{flag=xfm_fill_buy_order_id data={type=story identity=231}}",
                "{flag=xfm_fill_slice_source_position_id data={type=char identity=150}}",
                number("xfm_fill_buy_order_id", 231) + number("xfm_fill_buy_order_id", 231))) assertFalse(project(invalid).issues().isEmpty());
    }

    @Test void changedFillKeyChangesWholeTypedStoryWhileOriginalPositionDataIsRetained() {
        var before = project(number("xfm_fill_buy_order_id", 231) + number("xfm_fill_receipt_version", 1)).story().orElseThrow();
        var after = project(number("xfm_fill_buy_order_id", 232) + number("xfm_fill_receipt_version", 1)).story().orElseThrow();
        assertNotEquals(before, after, "Existing cold comparison compares the entire Story, not selected old integer keys");
        assertEquals(before.nativeId(), after.nativeId()); assertEquals(before.permanentId(), after.permanentId());
        assertEquals(BigInteger.ONE, before.number(NumberField.POSITION_ID).orElseThrow());
        assertEquals(BigInteger.valueOf(231), before.number(NumberField.FILL_BUY_ORDER_ID).orElseThrow());
        assertTrue(project("").story().orElseThrow().number(NumberField.FILL_BUY_ORDER_ID).isEmpty());
    }

    private static FinancialProjector.RecordProjection project(String fields) {
        return FinancialProjector.projectRecord(new NativeId("999999"), Clausewitz.parse("story_cycle=xfm_futures_position variables={data={" + number("xfm_position_id", 1) + fields + "}}"), LAYOUT);
    }
    private static String number(String name, long value) { return "{flag=" + name + " data={type=value identity=" + BigInteger.valueOf(value).multiply(BigInteger.valueOf(100000)) + "}}"; }
}
