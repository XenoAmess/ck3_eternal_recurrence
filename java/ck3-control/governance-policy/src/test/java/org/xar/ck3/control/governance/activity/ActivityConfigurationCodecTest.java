package org.xar.ck3.control.governance.activity;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.activity.ActivityConfigurationModels.Frame;

/** Exact configuration shapes used by the stock producer and the ordinary Java consumer. */
final class ActivityConfigurationCodecTest {
    private static Frame frame() { return new Frame(BigInteger.valueOf(17),BigInteger.valueOf(53219928),BigInteger.valueOf(29829)); }
    private static ObjectNode body(String schema,int stage) { return StrictJson.object().put("schema",schema).put("snapshot_revision",17).put("date_raw",53219928).put("actor_character_id",29829).put("activity_key","activity_feast").put("planning_stage",stage).put("selected_option_key","feast_type_generic").put("read_only",true).put("raw_pointer_fields_persisted",false); }
    private static byte[] raw(ObjectNode row) { return StrictJson.canonical(row); }
    @Test void stageOneRetainsThreeIndependentNativePredicates() {
        ObjectNode row=body("activity-stage1-option-private-read-v1",1).put("selected_option_shown",true).put("selected_option_valid",false).put("can_progress_stage1",true).put("generic_feast_confirm_ready",false);
        var decoded=ActivityConfigurationCodec.stageOne(raw(row),frame()); assertFalse(decoded.ready()); assertTrue(decoded.shown()); assertFalse(decoded.valid()); assertEquals(row,StrictJson.parse(ActivityConfigurationCodec.encode(decoded)));
        row.put("generic_feast_confirm_ready",true); assertThrows(IllegalArgumentException.class,()->ActivityConfigurationCodec.stageOne(raw(row),frame()));
        row.put("generic_feast_confirm_ready",false).put("planning_stage",1.0); assertThrows(IllegalArgumentException.class,()->ActivityConfigurationCodec.stageOne(raw(row),frame()));
    }
    @Test void locationPreservesEmptyRowsAndNullActiveAndActualCandidateOrder() {
        ObjectNode row=body("activity-stage2-location-private-read-v1",2).put("advertised",false).putNull("active_row_index").put("activity_single_location_flag",true).put("previous_planning_stage",1).put("can_progress_stage2",false);
        row.putArray("configuration_rows"); var candidates=row.putArray("candidates"); candidates.addObject().put("province_id",101).put("can_select",false); candidates.addObject().put("province_id",102).put("can_select",true);
        var decoded=ActivityConfigurationCodec.location(raw(row),frame(),List.of(101,102)); assertTrue(decoded.activeRowIndex().isEmpty()); assertTrue(decoded.rows().isEmpty()); assertEquals(102,decoded.candidates().get(1).provinceId()); assertEquals(row,StrictJson.parse(ActivityConfigurationCodec.encode(decoded)));
        assertThrows(IllegalArgumentException.class,()->ActivityConfigurationCodec.location(raw(row),frame(),List.of(102,101))); row.put("active_row_index",0); assertThrows(IllegalArgumentException.class,()->ActivityConfigurationCodec.location(raw(row),frame(),List.of(101,102)));
    }
    @Test void strictConfigurationRejectsWrongKeysAndBooleanIDs() {
        ObjectNode row=body("activity-stage2-option-private-read-v1",2).put("generic_feast_selected",true).put("advertised",false);
        assertTrue(ActivityConfigurationCodec.stageTwo(raw(row),frame()).genericFeastSelected());
        row.put("actor_character_id",true); assertThrows(IllegalArgumentException.class,()->ActivityConfigurationCodec.stageTwo(raw(row),frame()));
        row.put("actor_character_id",29829).put("unknown",1); assertThrows(IllegalArgumentException.class,()->ActivityConfigurationCodec.stageTwo(raw(row),frame()));
    }
}
