package org.xar.ck3.markets.saveaudit;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.markets.saveaudit.FinancialProjector.LayoutHypothesis;
import org.xar.ck3.markets.saveaudit.FinancialProjector.NumberIdentityEncoding;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.NumberField;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.SaveContracts.NativeId;

/** Authored typed token fixtures through the production projector; no physical SAVE or Game credit. */
final class FuturesCancellationProjectionTest {
    private static final LayoutHypothesis STRICT=new LayoutHypothesis("1.21.0","19",BigInteger.valueOf(100000),"story","char");
    private static final LayoutHypothesis ZERO=new LayoutHypothesis("1.21.0","19",BigInteger.valueOf(100000),"story","char",NumberIdentityEncoding.unsigned64OmittedZero);
    @Test void historicalCancellationHasNoInferredCauseDayOrRefund() {
        var p=project(number("xfm_status",3)+number("xfm_archived_day",213),STRICT);
        assertTrue(p.issues().isEmpty());var order=p.story().orElseThrow();
        for(NumberField f:NumberField.values())if(f.name().startsWith("CANCEL_"))assertTrue(order.number(f).isEmpty(),f.name());
        assertEquals(BigInteger.valueOf(3),order.number(NumberField.STATUS).orElseThrow());
    }
    @Test void receiptFieldsProjectExactlyAndExplicitObservedZeroRemainsDistinctFromAbsence() {
        String vars=number("xfm_cancel_receipt_version",1)+number("xfm_cancel_reason",5)+number("xfm_cancel_day",213)
            +number("xfm_cancel_recovery",1)+number("xfm_cancel_release_api_called",1)+number("xfm_cancel_release_result",1)
            +number("xfm_cancel_release_verified",1)+number("xfm_cancel_released_cents",62)
            +number("xfm_cancel_before_free_cents",8220)+number("xfm_cancel_after_free_cents",8282)
            +number("xfm_cancel_before_reserved_cents",454)+number("xfm_cancel_after_reserved_cents",392)
            +number("xfm_cancel_before_remaining_cents",62)+"{flag=xfm_cancel_after_remaining_cents data={type=value}}";
        var p=project(vars,ZERO);assertTrue(p.issues().isEmpty());var order=p.story().orElseThrow();
        assertEquals(BigInteger.valueOf(62),order.number(NumberField.CANCEL_RELEASED_CENTS).orElseThrow());
        assertEquals(BigInteger.ZERO,order.number(NumberField.CANCEL_AFTER_REMAINING_CENTS).orElseThrow());
        assertEquals(BigInteger.valueOf(5),order.number(NumberField.CANCEL_REASON).orElseThrow());
        assertEquals(BigInteger.valueOf(213),order.number(NumberField.CANCEL_DAY).orElseThrow());
        assertEquals(BigInteger.valueOf(1),order.number(NumberField.CANCEL_RELEASE_API_CALLED).orElseThrow());
        var absent=project(number("xfm_cancel_receipt_version",1)+number("xfm_cancel_release_verified",0),ZERO).story().orElseThrow();
        assertTrue(absent.number(NumberField.CANCEL_RELEASED_CENTS).isEmpty());assertTrue(absent.number(NumberField.CANCEL_RELEASE_RESULT).isEmpty());
    }
    @Test void malformedFractionalAndDuplicateReceiptAmountsRemainRejectedByExistingRules() {
        for(String data:List.of("type=story identity=6200000","type=value identity=6200001","type=value identity=6200000 identity=6200000")) {
            var p=project("{flag=xfm_cancel_released_cents data={"+data+"}}",STRICT);
            assertTrue(p.story().orElseThrow().number(NumberField.CANCEL_RELEASED_CENTS).isEmpty(),data);
            assertFalse(p.issues().isEmpty(),data);
        }
        var duplicate=project(number("xfm_cancel_released_cents",62)+number("xfm_cancel_released_cents",62),STRICT);
        assertFalse(duplicate.issues().isEmpty());
    }
    private static String number(String name,long n) {return "{flag="+name+" data={type=value identity="+BigInteger.valueOf(n).multiply(BigInteger.valueOf(100000))+"}}";}
    private static FinancialProjector.RecordProjection project(String vars,LayoutHypothesis layout) {
        return FinancialProjector.projectRecord(new NativeId("83886782"),Clausewitz.parse("story_cycle=xfm_futures_order variables={data={"+number("xfm_order_id",205)+vars+"}}"),layout);
    }
}
