package org.xar.ck3.control.application.history;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.routecontact.RouteContactModel;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

public final class HistoryFixtures {
    public static final String QUERY = "query-route-contact-horizon-v1-1-to-10-h-1-2";
    public static final String ADVANCE = "advance-route-contact-horizon-v1-1-to-10-h-1-2";
    // Synthetic exact 100 ns fixture token; it is never presented as an observed process identity.
    public static GameGeneration game() { return new GameGeneration(9, new PythonOnlyUInt64(new BigInteger("134373229053165471"))); }
    private HistoryFixtures() { }
    public static Obj json(String raw) { return DriverJson.object(raw.getBytes(StandardCharsets.UTF_8), DriverJson.MAX_NATIVE_BYTES); }
    public static Obj row(int index, String command, boolean ok, String result) {
        return json("{\"index\":" + index + ",\"command\":\"" + command + "\",\"ok\":" + ok
                + (result == null ? "" : ",\"result\":" + result) + "}");
    }
    public static Obj checkpoint(int index) {
        return json("{\"history_index\":" + index + ",\"sha256\":\"" + "a".repeat(64)
                + "\",\"size\":4096,\"date_raw\":100,\"name\":\"xar_checkpoint.ck3\",\"episode_character_id\":1,\"episode_run_id\":\"ep\"}");
    }
    public static String result(Obj checkpoint, String source, int previous, int pid) {
        return "{\"step\":\"restore-checkpoint\",\"accepted\":true,\"status\":\"restored\",\"backend_id\":\"native-headless\",\"source\":\""
                + source + "\",\"restored_date_raw\":100,\"map_ready\":true,\"checkpoint\":"
                + new String(OpportunityJson.encode(checkpoint), StandardCharsets.UTF_8)
                + ",\"lifecycle\":{\"previous_pid\":" + previous + ",\"pid\":" + pid + "}}";
    }
    public static Obj anchor(int index) {
        return row(index, "save-checkpoint", true, "{\"checkpoint\":" + new String(OpportunityJson.encode(checkpoint(index)), StandardCharsets.UTF_8) + "}");
    }
    public static DriverStateSnapshot.Complete driver(List<Obj> history) {
        var entries = history.stream().map(row -> new DriverStateSnapshot.HistoryEntry(
                OpportunityJson.integer(row.get("index"), "index").longValueExact(), new DriverStateSnapshot.Value(OpportunityJson.encode(row)))).toList();
        return new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("pipe", 9, BigInteger.ONE, "ep"), entries,
                new DriverStateSnapshot.NullValue(), new DriverStateSnapshot.NullValue(), new DriverStateSnapshot.NullValue(),
                new DriverStateSnapshot.NullValue(), new DriverStateSnapshot.Missing(), new DriverStateSnapshot.NullValue(), new DriverStateSnapshot.Missing());
    }
    public static RouteContactModel.Frame frame() {
        var generation = game();
        var owner = new RouteContactModel.Owner("machine", generation, "session", BigInteger.ONE, 9, "ep", 1, 0);
        var own = new RouteContactModel.Army(1, true, 10, Optional.empty(), List.of(), Optional.of("regular"), Optional.of(1), false, false);
        var hostile = new RouteContactModel.Army(2, false, 20, Optional.of(10), List.of(10), Optional.of("moving"), Optional.of(4), false, false);
        return new RouteContactModel.Frame(owner, "snap", BigInteger.valueOf(3), BigInteger.valueOf(7), 100, true, true, 1, false, true,
                OpportunityJson.Nil.INSTANCE, OpportunityJson.Nil.INSTANCE, OpportunityJson.Nil.INSTANCE, List.of(4), List.of(own), List.of(hostile));
    }
    public static String queryResult() {
        return """
                {"queried_snapshot_id":"snap","queried_revision":3,"queried_native_revision":7,"queried_connection_generation":1,"queried_episode_run_id":"ep",
                 "route_contact_horizon":{"status":"available","date_raw":100,"snapshot_revision":7,"subject_army_id":1,"target_province_id":10,
                  "hostile_army_ids":[2],"horizon_start_date_raw":100,"horizon_end_date_raw":124,"one_day_contact_free":false,
                  "subject_route":{"timeline_observable":true,"army_id":1,"current_province_id":10,"effective_origin_province_id":10,"route_province_ids":[],"arrival_date_raws":[]},
                  "hostile_routes":[{"timeline_observable":true,"army_id":2,"current_province_id":20,"effective_origin_province_id":20,"route_province_ids":[10],"arrival_date_raws":[100]}],
                  "conflicts":[{"kind":"same_province","hostile_army_id":2,"province_id":10,"overlap_start_date_raw":100,"overlap_end_date_raw":124}]}}
                """;
    }
    public static String endpoint() {
        return """
                {"ending_date_raw":100,"contact_transition":{"status":"predicted_only","proof_kind":"unavoidable_current_province_contact",
                "postcondition":"predicted_contact_boundary_reached","contact_observed":false,"episode_run_id":"ep","subject_army_id":1,
                "contact_province_id":10,"starting_date_raw":76,"ending_date_raw":100,"conflict_hostile_army_ids":[2]}}
                """;
    }
    public static String strictFailure() {
        return """
                {"ending_date_raw":100,"contact_followup":{"status":"exhausted_without_strong_transition","episode_run_id":"ep",
                 "subject_army_id":1,"contact_province_id":10,"starting_date_raw":76,"ending_date_raw":100}}
                """;
    }
}
