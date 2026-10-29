package org.xar.ck3.control.governance.activity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.governance.activity.ActivityConfigurationModels.*;

/** Exact producer schemas from native_auto_run and activity_stage1_option_read_private_transport_v1.cpp. */
public final class ActivityConfigurationCodec {
    private ActivityConfigurationCodec() { }
    private static final String COMMON = "schema snapshot_revision date_raw actor_character_id activity_key planning_stage selected_option_key read_only raw_pointer_fields_persisted";
    public static StageOne stageOne(byte[] raw, Frame frame) {
        ObjectNode row = exact(raw, COMMON + " selected_option_shown selected_option_valid can_progress_stage1 generic_feast_confirm_ready");
        bind(row, frame, "activity-stage1-option-private-read-v1", 1);
        return new StageOne(frame, bool(row,"selected_option_shown"), bool(row,"selected_option_valid"), bool(row,"can_progress_stage1"), bool(row,"generic_feast_confirm_ready"), original(row));
    }
    public static StageTwo stageTwo(byte[] raw, Frame frame) {
        ObjectNode row = exact(raw, COMMON + " generic_feast_selected advertised"); bind(row, frame, "activity-stage2-option-private-read-v1", 2); no(row,"advertised");
        return new StageTwo(frame,bool(row,"generic_feast_selected"),original(row));
    }
    public static Location location(byte[] raw, Frame frame, List<Integer> expectedCandidates) {
        expectedCandidates = List.copyOf(expectedCandidates); need(!expectedCandidates.isEmpty() && expectedCandidates.size() <= 8 && expectedCandidates.stream().distinct().count() == expectedCandidates.size(), "explicit distinct native location candidates required");
        ObjectNode row = exact(raw, COMMON + " configuration_rows active_row_index activity_single_location_flag previous_planning_stage candidates can_progress_stage2 advertised");
        bind(row, frame, "activity-stage2-location-private-read-v1", 2); no(row,"advertised");
        JsonNode entries = row.get("configuration_rows"); need(entries.isArray() && entries.size() <= 128, "configuration rows"); List<ConfigurationRow> rows = new ArrayList<>();
        for (JsonNode item : entries) {
            exact(item,"index phase_kind province_id is_active"); JsonNode phase = item.get("phase_kind");
            rows.add(new ConfigurationRow(integer(item,"index",0,127), phase.isNull() ? Optional.empty() : Optional.of(integer(item,"phase_kind",0,Integer.MAX_VALUE)), number(item,"province_id",BigInteger.ZERO,U32).longValueExact(),bool(item,"is_active")));
        }
        JsonNode candidateRows = row.get("candidates"); need(candidateRows.isArray() && candidateRows.size() == expectedCandidates.size(), "candidate result coverage"); List<Candidate> candidates = new ArrayList<>();
        for (int index = 0; index < candidateRows.size(); index++) {
            JsonNode item = candidateRows.get(index); exact(item,"province_id can_select"); int province = integer(item,"province_id",1,Integer.MAX_VALUE);
            need(province == expectedCandidates.get(index), "native candidate order/identity differs"); candidates.add(new Candidate(province,bool(item,"can_select")));
        }
        return new Location(frame,rows,row.get("active_row_index").isNull() ? Optional.empty() : Optional.of(integer(row,"active_row_index",0,127)),bool(row,"activity_single_location_flag"),integer(row,"previous_planning_stage",0,5),candidates,bool(row,"can_progress_stage2"),original(row));
    }
    public static StageTwoGate gate(byte[] raw, Frame frame) {
        ObjectNode row = exact(raw, COMMON + " configuration_row_count failing_rows can_progress_stage2 generic_feast_stage2_advance_ready advertised");
        bind(row,frame,"activity-stage2-gate-private-read-v1",2); no(row,"advertised"); int count = integer(row,"configuration_row_count",0,128);
        JsonNode entries = row.get("failing_rows"); need(entries.isArray() && entries.size() <= count,"gate failed rows"); List<Integer> indices = new ArrayList<>();
        for (JsonNode item : entries) { exact(item,"index raw_dword"); indices.add(integer(item,"index",0,Math.max(0,count-1))); number(item,"raw_dword",BigInteger.ZERO,U32); }
        boolean progress = bool(row,"can_progress_stage2"); need(progress == indices.isEmpty(),"gate failed rows disagree");
        return new StageTwoGate(frame,count,indices,progress,bool(row,"generic_feast_stage2_advance_ready"),original(row));
    }
    public static byte[] encode(StageOne value) { return OpportunityJson.encode(value.original()); }
    public static byte[] encode(StageTwo value) { return OpportunityJson.encode(value.original()); }
    public static byte[] encode(Location value) { return OpportunityJson.encode(value.original()); }
    public static byte[] encode(StageTwoGate value) { return OpportunityJson.encode(value.original()); }
    private static final BigInteger U32 = BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE);
    private static void bind(JsonNode row, Frame frame, String schema, int stage) {
        need(text(row,"schema").equals(schema) && text(row,"activity_key").equals("activity_feast") && text(row,"selected_option_key").equals("feast_type_generic"),"configuration schema/type/option");
        need(number(row,"snapshot_revision",BigInteger.ONE,StrictJson.UINT64_MAX).equals(frame.nativeRevision()) && number(row,"date_raw",BigInteger.ZERO,BigInteger.valueOf(Integer.MAX_VALUE)).equals(frame.dateRaw()) && number(row,"actor_character_id",BigInteger.ONE,U32).equals(frame.actorId()),"configuration source frame drift");
        need(integer(row,"planning_stage",stage,stage) == stage,"configuration stage"); yes(row,"read_only"); no(row,"raw_pointer_fields_persisted");
    }
    private static OpportunityJson.Obj original(JsonNode row) { return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row)),"validated native configuration"); }
    private static ObjectNode exact(byte[] raw,String keys) { return exact(StrictJson.parse(raw),keys); }
    private static ObjectNode exact(JsonNode row,String keys) { Set<String> fields = keys.isEmpty() ? Set.of() : Set.of(keys.split(" ")); return StrictJson.object(row,fields); }
    private static BigInteger number(JsonNode row,String key,BigInteger minimum,BigInteger maximum) { return StrictJson.integer(row.get(key),minimum,maximum); }
    private static int integer(JsonNode row,String key,int minimum,int maximum) { return (int)StrictJson.integer(row.get(key),minimum,maximum); }
    private static String text(JsonNode row,String key) { return StrictJson.text(row.get(key)); }
    private static boolean bool(JsonNode row,String key) { JsonNode value=row.get(key); need(value!=null && value.isBoolean(),"boolean required: "+key); return value.booleanValue(); }
    private static void yes(JsonNode row,String key) { need(bool(row,key),key+" must be true"); }
    private static void no(JsonNode row,String key) { need(!bool(row,key),key+" must be false"); }
    private static void need(boolean condition,String reason) { if(!condition)throw new IllegalArgumentException(reason); }
}
