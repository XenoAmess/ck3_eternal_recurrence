package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Explicit self-owned Java DATA; no Native frame, lease or Game qualification. */
class NativeOwnerSnapshotCurrentZg361CombinedSelectionTest {
    private static com.fasterxml.jackson.databind.node.ObjectNode config(int version,String mode,int overall) {
        var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v"+version).put("mode",mode)
                .put("overall_timeout_seconds",overall).put("read_timeout_seconds",60).put("maximum_frames_per_operation",65536);
        c.putObject("owner_descriptor").put("path","D:/java-data/combined/owner.json").put("bytes",1).put("sha256","0".repeat(64));
        return c;
    }
    @Test void explicitV51CommonSixAndThirtyTwoLeaveTheTwoOldModesIndependent() {
        var combined=config(51,"current_zg361_review_ae2_case_once",900);
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_ZG361_REVIEW_AE2,NativeOwnerSnapshotMain268.observationMode(combined));
        assertEquals(32,NativeOwnerSnapshotMain268.currentZg361CombinedConfig(combined).submissions());
        assertEquals(900,NativeOwnerSnapshotMain268.currentZg361OverallTimeoutLimit(NativeOwnerSnapshotMain268.observationMode(combined)));
        for(String key:List.of("combined","actor","phase_bound","cap","maximum_claims","pay","confirm","days","text")) {
            var c=combined.deepCopy();c.put(key,1);
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentZg361CombinedConfig(c),key);
        }
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentZg361CombinedConfig(config(51,"current_zg361_review_requirements_once",900)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentZg361CombinedConfig(config(51,"current_zg361_review_ae2_case_once",901)));
        var pay=config(49,"current_zg361_ae2_case_once",600);
        var review=config(50,"current_zg361_review_requirements_once",600);
        assertEquals(24,NativeOwnerSnapshotMain268.currentZg361Ae2Config(pay).submissions());
        assertEquals(8,NativeOwnerSnapshotMain268.currentZg361ReviewConfig(review).submissions());
        assertEquals(600,NativeOwnerSnapshotMain268.currentZg361OverallTimeoutLimit(NativeOwnerSnapshotMain268.observationMode(pay)));
        assertEquals(600,NativeOwnerSnapshotMain268.currentZg361OverallTimeoutLimit(NativeOwnerSnapshotMain268.observationMode(review)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentZg361Ae2Config(pay.deepCopy().put("overall_timeout_seconds",900)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentZg361ReviewConfig(review.deepCopy().put("overall_timeout_seconds",900)));
    }
    @Test void theProductionCheckedSequenceBeginsOncePassesOneOpaqueContextAndNeverPaysAfterReviewFailure()throws Exception {
        Object opaque=new Object();var order=new ArrayList<String>();int[] begins={0},payments={0};
        var actual=NativeOwnerSnapshotMain268.currentZg361ReviewBeforeAe2(new NativeOwnerSnapshotMain268.CheckedZg361ReviewAe2Sequence<Object>() {
            public Object begin(){begins[0]++;order.add("begin");return opaque;}
            public void review(Object same){assertSame(opaque,same);order.add("actual-review");}
            public void payment(Object same){assertSame(opaque,same);payments[0]++;order.add("original-ae2");}
        });
        assertSame(opaque,actual);assertEquals(1,begins[0]);assertEquals(1,payments[0]);
        assertEquals(List.of("begin","actual-review","original-ae2"),order);
        order.clear();begins[0]=0;payments[0]=0;
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentZg361ReviewBeforeAe2(new NativeOwnerSnapshotMain268.CheckedZg361ReviewAe2Sequence<Object>() {
            public Object begin(){begins[0]++;order.add("begin");return opaque;}
            public void review(Object same)throws IOException {assertSame(opaque,same);order.add("incomplete-review");throw new IOException("self-owned DATA review refused");}
            public void payment(Object same){payments[0]++;fail("Payment cannot follow an unsuccessful actual review");}
        }));
        assertEquals(1,begins[0]);assertEquals(0,payments[0]);assertEquals(List.of("begin","incomplete-review"),order);
    }
}
