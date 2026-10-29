package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** Regression for the actual quote producer/consumer leaf: a supported cap must not reject every payload at entry. */
final class FinanceQuoteJsonBudgetTest {
    private static ObjectNode row() {
        var row=StrictJson.object();
        for(String field:List.of("schema","operation","before","source","session_id","arguments","canonical_head","head_archive","spending","documents","reads","planning_request"))
            row.putNull(field);
        row.put("schema",FinanceEvidenceArchive.SCHEMA);var extension=row.putObject("planning_request").putArray("original_full_semantic_extension");
        for(int i=0;i<1000;i++)extension.add("x".repeat(200));
        return row;
    }
    @Test void actualProducerBytesReachTheActualConsumerBeyondTheProposalParserLimit() {
        var original=row();byte[] produced=FinanceEvidenceArchive.quoteBytes(original);
        assertTrue(produced.length>131072);assertEquals(original,FinanceEvidenceArchive.quoteObject(new RawJson(produced)));
        var missing=original.deepCopy();missing.remove("reads");
        assertThrows(IllegalArgumentException.class,()->FinanceEvidenceArchive.quoteBytes(missing));
        var extra=original.deepCopy().put("unregistered_alias",true);
        assertThrows(IllegalArgumentException.class,()->FinanceEvidenceArchive.quoteObject(new RawJson(StrictJson.canonical(extra,1048576))));
    }
    @Test void theDeliberateOneMiBLeafStillRejectsOversizeAndUnsupportedNumericTokens() {
        var huge=row();var extension=huge.putArray("arguments");for(int i=0;i<6000;i++)extension.add("x".repeat(200));
        assertThrows(IllegalArgumentException.class,()->FinanceEvidenceArchive.quoteBytes(huge));
        var decimal=row();decimal.put("operation",1.0);
        assertThrows(IllegalArgumentException.class,()->FinanceEvidenceArchive.quoteBytes(decimal));
    }
}
