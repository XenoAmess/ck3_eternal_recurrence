package org.xar.ck3.markets.saveaudit;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.NumberField;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.Story;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.SaveContracts.NativeId;

/** Synthetic envelope tests only; an actual financial 1.21 SAVE layout remains unqualified. */
final class ModelQuoteSaveAuditTest {
    private static final FinancialProjector.LayoutHypothesis LAYOUT = new FinancialProjector.LayoutHypothesis(
            "1.21.0", "19", BigInteger.valueOf(100000), "story", "char");

    @Test void optionalUnitIdentityProjectsExactlyAndColdComparisonDetectsItsLoss() {
        Story before = project("{ flag=xfm_model_quote_divisor data={ type=value identity=10000000 } }");
        Story legacy = project("");
        assertEquals(BigInteger.valueOf(100), before.number(NumberField.MODEL_QUOTE_DIVISOR).orElseThrow());
        assertTrue(legacy.number(NumberField.MODEL_QUOTE_DIVISOR).isEmpty());
        var exact = FinancialAudit.compareCold(snapshot(before), snapshot(before));
        assertTrue(exact.exactSelectedFinancialState()); assertFalse(exact.financialCertified());
        var lost = FinancialAudit.compareCold(snapshot(before), snapshot(legacy));
        assertFalse(lost.exactSelectedFinancialState()); assertFalse(lost.financialCertified());
        assertTrue(lost.differences().stream().anyMatch(d -> d.identity().equals("INDEX:1")));
        Story changed = project("{ flag=xfm_model_quote_divisor data={ type=value identity=100000 } }");
        assertFalse(FinancialAudit.compareCold(snapshot(before), snapshot(changed)).exactSelectedFinancialState());
    }

    @Test void explicitUnitWrongTypeOrNonIntegralValueStaysIncompleteInsteadOfDefaulting() {
        for (String data : List.of("type=story identity=10000000", "type=value identity=10000001", "type=value")) {
            var result = FinancialProjector.projectRecord(new NativeId("99"), body("{ flag=xfm_model_quote_divisor data={ " + data + " } }"), LAYOUT);
            assertTrue(result.story().orElseThrow().number(NumberField.MODEL_QUOTE_DIVISOR).isEmpty());
            assertTrue(result.issues().stream().anyMatch(i -> i.field().equals("xfm_model_quote_divisor")));
        }
    }

    private static Story project(String variable) {
        var result = FinancialProjector.projectRecord(new NativeId("99"), body(variable), LAYOUT);
        assertTrue(result.issues().isEmpty()); return result.story().orElseThrow();
    }
    private static Clausewitz.Block body(String variable) {
        return Clausewitz.parse("story_cycle=xfm_oracle_index variables={ data={ { flag=xfm_index_id data={ type=value identity=100000 } } " + variable + " } }");
    }
    private static FinancialSnapshot snapshot(Story story) {
        return new FinancialSnapshot("4-8e1c2f1861", "a".repeat(64), "1.21.0", "19", "1066.9.16", List.of(story), List.of());
    }
}
