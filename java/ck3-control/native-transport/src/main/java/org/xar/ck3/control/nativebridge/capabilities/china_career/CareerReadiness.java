package org.xar.ck3.control.nativebridge.capabilities.china_career;
import com.fasterxml.jackson.databind.JsonNode;
import java.util.List;
import static org.xar.ck3.control.nativebridge.capabilities.china_career.CareerJson.*;
public final class CareerReadiness {
    private CareerReadiness() { }
    public interface Flags { List<Boolean> flags(); }
    public record Owner(boolean case_identity_ready, boolean player_owner_binding_ready, boolean portfolio_subject_binding_ready, boolean ready, boolean same_frame_ready) implements Flags {
        public List<Boolean> flags() { return List.of(case_identity_ready, player_owner_binding_ready, portfolio_subject_binding_ready, ready, same_frame_ready); }
        static Owner parse(JsonNode row) {
            exact(row, "case_identity_ready", "player_owner_binding_ready", "portfolio_subject_binding_ready", "ready", "same_frame_ready");
            return new Owner(bool(row.get("case_identity_ready")), bool(row.get("player_owner_binding_ready")), bool(row.get("portfolio_subject_binding_ready")), bool(row.get("ready")), bool(row.get("same_frame_ready")));
        }
    }
    public record Career(boolean career_hc_conservation_ready, boolean career_hc_partition_ready, boolean m360_identity_ready, boolean m360_route_b_receipt_ready, boolean owner_binding_ready, boolean player_subject_binding_ready, boolean ready, boolean route_b_manager_cost_zero_ready, boolean same_frame_ready) implements Flags {
        public List<Boolean> flags() { return List.of(career_hc_conservation_ready, career_hc_partition_ready, m360_identity_ready, m360_route_b_receipt_ready, owner_binding_ready, player_subject_binding_ready, ready, route_b_manager_cost_zero_ready, same_frame_ready); }
        static Career parse(JsonNode row) {
            exact(row, "career_hc_conservation_ready", "career_hc_partition_ready", "m360_identity_ready", "m360_route_b_receipt_ready", "owner_binding_ready", "player_subject_binding_ready", "ready", "route_b_manager_cost_zero_ready", "same_frame_ready");
            return new Career(bool(row.get("career_hc_conservation_ready")), bool(row.get("career_hc_partition_ready")), bool(row.get("m360_identity_ready")), bool(row.get("m360_route_b_receipt_ready")), bool(row.get("owner_binding_ready")), bool(row.get("player_subject_binding_ready")), bool(row.get("ready")), bool(row.get("route_b_manager_cost_zero_ready")), bool(row.get("same_frame_ready")));
        }
    }
    public record Collective(boolean case_identity_ready, boolean charter_gate_lifecycle_ready, boolean cohort_conservation_ready, boolean cohort_identity_ready, boolean collective_lifecycle_ready, boolean history_ledger_ready, boolean history_order_ready, boolean m360_receipt_projection_ready, boolean owner_binding_ready, boolean player_subject_binding_ready, boolean ready, boolean route_conservation_ready, boolean same_frame_ready, boolean three_cycle_ready) implements Flags {
        public List<Boolean> flags() { return List.of(case_identity_ready, charter_gate_lifecycle_ready, cohort_conservation_ready, cohort_identity_ready, collective_lifecycle_ready, history_ledger_ready, history_order_ready, m360_receipt_projection_ready, owner_binding_ready, player_subject_binding_ready, ready, route_conservation_ready, same_frame_ready, three_cycle_ready); }
        static Collective parse(JsonNode row) {
            exact(row, "case_identity_ready", "charter_gate_lifecycle_ready", "cohort_conservation_ready", "cohort_identity_ready", "collective_lifecycle_ready", "history_ledger_ready", "history_order_ready", "m360_receipt_projection_ready", "owner_binding_ready", "player_subject_binding_ready", "ready", "route_conservation_ready", "same_frame_ready", "three_cycle_ready");
            return new Collective(bool(row.get("case_identity_ready")), bool(row.get("charter_gate_lifecycle_ready")), bool(row.get("cohort_conservation_ready")), bool(row.get("cohort_identity_ready")), bool(row.get("collective_lifecycle_ready")), bool(row.get("history_ledger_ready")), bool(row.get("history_order_ready")), bool(row.get("m360_receipt_projection_ready")), bool(row.get("owner_binding_ready")), bool(row.get("player_subject_binding_ready")), bool(row.get("ready")), bool(row.get("route_conservation_ready")), bool(row.get("same_frame_ready")), bool(row.get("three_cycle_ready")));
        }
    }
    public record NormalExit(boolean current_hc_matches_stage_ready, boolean current_hc_partition_ready, boolean lifecycle_ready, boolean migration_delta_ready, boolean owner_binding_ready, boolean pending_snapshot_ready, boolean player_subject_binding_ready, boolean ready, boolean rehire_capture_ready, boolean same_frame_ready, boolean sealed_receipt_ready, boolean source_object_ready) implements Flags {
        public List<Boolean> flags() { return List.of(current_hc_matches_stage_ready, current_hc_partition_ready, lifecycle_ready, migration_delta_ready, owner_binding_ready, pending_snapshot_ready, player_subject_binding_ready, ready, rehire_capture_ready, same_frame_ready, sealed_receipt_ready, source_object_ready); }
        static NormalExit parse(JsonNode row) {
            exact(row, "current_hc_matches_stage_ready", "current_hc_partition_ready", "lifecycle_ready", "migration_delta_ready", "owner_binding_ready", "pending_snapshot_ready", "player_subject_binding_ready", "ready", "rehire_capture_ready", "same_frame_ready", "sealed_receipt_ready", "source_object_ready");
            return new NormalExit(bool(row.get("current_hc_matches_stage_ready")), bool(row.get("current_hc_partition_ready")), bool(row.get("lifecycle_ready")), bool(row.get("migration_delta_ready")), bool(row.get("owner_binding_ready")), bool(row.get("pending_snapshot_ready")), bool(row.get("player_subject_binding_ready")), bool(row.get("ready")), bool(row.get("rehire_capture_ready")), bool(row.get("same_frame_ready")), bool(row.get("sealed_receipt_ready")), bool(row.get("source_object_ready")));
        }
    }
    public record Governance(boolean actual_bottom_slots_ready, boolean bounded_ai_dependency_ready, boolean case_identity_ready, boolean component8_lifecycle_ready, boolean component8_settlement_ready, boolean component8_token_ready, boolean distribution_conservation_ready, boolean distribution_lifecycle_ready, boolean distribution_settlement_ready, boolean distribution_snapshot_ready, boolean effective_distribution_ready, boolean f032_receipt_ready, boolean f035_receipt_ready, boolean manager_score_ready, boolean next_cycle_policy_ready, boolean ready, boolean same_frame_ready, boolean subject_binding_ready, boolean team_snapshot_ready) implements Flags {
        public List<Boolean> flags() { return List.of(actual_bottom_slots_ready, bounded_ai_dependency_ready, case_identity_ready, component8_lifecycle_ready, component8_settlement_ready, component8_token_ready, distribution_conservation_ready, distribution_lifecycle_ready, distribution_settlement_ready, distribution_snapshot_ready, effective_distribution_ready, f032_receipt_ready, f035_receipt_ready, manager_score_ready, next_cycle_policy_ready, ready, same_frame_ready, subject_binding_ready, team_snapshot_ready); }
        static Governance parse(JsonNode row) {
            exact(row, "actual_bottom_slots_ready", "bounded_ai_dependency_ready", "case_identity_ready", "component8_lifecycle_ready", "component8_settlement_ready", "component8_token_ready", "distribution_conservation_ready", "distribution_lifecycle_ready", "distribution_settlement_ready", "distribution_snapshot_ready", "effective_distribution_ready", "f032_receipt_ready", "f035_receipt_ready", "manager_score_ready", "next_cycle_policy_ready", "ready", "same_frame_ready", "subject_binding_ready", "team_snapshot_ready");
            return new Governance(bool(row.get("actual_bottom_slots_ready")), bool(row.get("bounded_ai_dependency_ready")), bool(row.get("case_identity_ready")), bool(row.get("component8_lifecycle_ready")), bool(row.get("component8_settlement_ready")), bool(row.get("component8_token_ready")), bool(row.get("distribution_conservation_ready")), bool(row.get("distribution_lifecycle_ready")), bool(row.get("distribution_settlement_ready")), bool(row.get("distribution_snapshot_ready")), bool(row.get("effective_distribution_ready")), bool(row.get("f032_receipt_ready")), bool(row.get("f035_receipt_ready")), bool(row.get("manager_score_ready")), bool(row.get("next_cycle_policy_ready")), bool(row.get("ready")), bool(row.get("same_frame_ready")), bool(row.get("subject_binding_ready")), bool(row.get("team_snapshot_ready")));
        }
    }
    public record Selector(boolean direct_subordinate_ready, boolean exact_build_ready, boolean manager_eligibility_ready, boolean player_binding_ready, boolean ready, boolean relationship_enumeration_ready, boolean same_frame_ready) implements Flags {
        public List<Boolean> flags() { return List.of(direct_subordinate_ready, exact_build_ready, manager_eligibility_ready, player_binding_ready, ready, relationship_enumeration_ready, same_frame_ready); }
        static Selector parse(JsonNode row) {
            exact(row, "direct_subordinate_ready", "exact_build_ready", "manager_eligibility_ready", "player_binding_ready", "ready", "relationship_enumeration_ready", "same_frame_ready");
            return new Selector(bool(row.get("direct_subordinate_ready")), bool(row.get("exact_build_ready")), bool(row.get("manager_eligibility_ready")), bool(row.get("player_binding_ready")), bool(row.get("ready")), bool(row.get("relationship_enumeration_ready")), bool(row.get("same_frame_ready")));
        }
    }
}
