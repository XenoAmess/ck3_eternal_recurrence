package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentZg361Ae2Source;

/** Self-owned Source DATA only, never a Native response/claim or Game proof. */
class NativeOwnerSnapshotCurrentZg361ReviewSelectionTest {
    private static com.fasterxml.jackson.databind.node.ObjectNode config() {
        var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v50").put("mode","current_zg361_review_requirements_once")
                .put("overall_timeout_seconds",600).put("read_timeout_seconds",60).put("maximum_frames_per_operation",1024);
        c.putObject("owner_descriptor").put("path","D:/java-data/review/owner.json").put("bytes",1).put("sha256","0".repeat(64));return c;
    }
    private static CurrentZg361Ae2Source controls(boolean visible,boolean detail,boolean open) {
        return new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.CONTROLS,Optional.of(new CurrentZg361Ae2Source.Controls(true,visible,detail,true,true,false,open,Optional.empty(),List.of())),Optional.empty());
    }
    private static CurrentZg361Ae2Source review(boolean complete,boolean canOpen,Boolean has,String description)throws IOException {
        var s=StrictJson.object().put("schema","ck3.zg361_ae2.current267_source.v1").put("kind","review");
        var r=s.putObject("review").put("definition_key","zg361_review_now_decision").put("resident_available",true)
                .put("list_visible",true).put("detail_visible",complete).put("detail_enabled",false).put("actor_bound",true)
                .put("model_complete",true).put("blocked_by_visible_modal",false).put("row_present",true)
                .put("selected_review",complete).put("open_detail_admissible",canOpen).put("requirements_complete",complete);
        if(complete)r.put("selected_definition_key","zg361_review_now_decision");else r.put("selected_definition_key","unrelated_decision");
        if(has==null)r.putNull("has_requirements");else r.put("has_requirements",has);
        if(description==null)r.putNull("requirements_description");else r.put("requirements_description",description);
        return CurrentZg361Ae2Source.decode(s);
    }
    @Test void strictV50Common6AndFiniteEightPreserveV49PaymentMode() {
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_ZG361_REVIEW,NativeOwnerSnapshotMain268.observationMode(config()));
        assertEquals(8,NativeOwnerSnapshotMain268.currentZg361ReviewConfig(config()).submissions());
        assertEquals(4,NativeOwnerSnapshotMain268.currentZg361ReviewSubmissionBound(false,false));
        assertEquals(5,NativeOwnerSnapshotMain268.currentZg361ReviewSubmissionBound(true,false));
        assertEquals(7,NativeOwnerSnapshotMain268.currentZg361ReviewSubmissionBound(false,true));
        for(String key:List.of("definition_key","actor","phase_bound","has_requirements","pay","confirm","days","text")) {
            var c=config();c.put(key,1);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentZg361ReviewConfig(c),key);
        }
        var original=config().put("schema","xar.native-owner-snapshot-config/v49").put("mode","current_zg361_ae2_case_once");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_ZG361_AE2,NativeOwnerSnapshotMain268.observationMode(original));
        assertEquals(24,NativeOwnerSnapshotMain268.currentZg361Ae2Config(original).submissions());
    }
    @Test void actualSequenceSkipsUnneededListAndAlreadyCompleteDetail()throws IOException {
        assertTrue(NativeOwnerSnapshotMain268.currentZg361ReviewShouldOpenList(controls(false,false,true)));
        assertFalse(NativeOwnerSnapshotMain268.currentZg361ReviewShouldOpenList(controls(true,false,false)));
        // Old controls cannot export review-selected. Hidden/no-list-permission
        // still allows the independent typed Review query, rather than failure.
        assertFalse(NativeOwnerSnapshotMain268.currentZg361ReviewShouldOpenList(controls(false,true,false)));
        assertFalse(NativeOwnerSnapshotMain268.currentZg361ReviewNeedsOpen(review(true,false,false,"")));
        assertTrue(NativeOwnerSnapshotMain268.currentZg361ReviewNeedsOpen(review(false,true,null,null)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentZg361ReviewNeedsOpen(review(false,false,null,null)));
    }
    @Test void falseAndEmptyAreCompleteDataButTargetMetadataDoesNotReplaceSelection()throws IOException {
        var empty=NativeOwnerSnapshotMain268.requireCurrentZg361ReviewComplete(review(true,false,false,""));
        assertEquals(Optional.of(false),empty.hasRequirements());assertEquals(Optional.of(""),empty.requirementsDescription());
        String actual=String.valueOf((char)0)+(char)0x15+"actual description\n";
        assertEquals(Optional.of(actual),NativeOwnerSnapshotMain268.requireCurrentZg361ReviewComplete(review(true,false,true,actual)).requirementsDescription());
        var wrongSelected=review(false,false,null,null);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361ReviewComplete(wrongSelected));
        var result=StrictJson.object();NativeOwnerSnapshotMain268.initializeCurrentZg361ReviewResult(result,"java-data");
        for(String flag:List.of("four_localized_labels_observed","business_contract_pass","wholeproduct_pass","new_date_observed","physical_save_confirmed"))assertFalse(result.path(flag).booleanValue(),flag);
        assertEquals(0,result.path("pay_calls").intValue());assertEquals(0,result.path("confirmation_calls").intValue());
    }
}
