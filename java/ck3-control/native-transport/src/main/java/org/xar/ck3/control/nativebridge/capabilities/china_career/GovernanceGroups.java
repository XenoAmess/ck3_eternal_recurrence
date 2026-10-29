package org.xar.ck3.control.nativebridge.capabilities.china_career;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import java.util.Objects;
import static org.xar.ck3.control.nativebridge.capabilities.china_career.CareerJson.*;
public final class GovernanceGroups {
    private GovernanceGroups() { }
    static final Set<String> REASONS = Set.of("case_unavailable", "lifecycle_not_reached", "not_applicable", "receipt_not_recorded", "value_out_of_range", "value_type_mismatch", "variable_absent");
    public record Case(Datum<Boolean> active, Datum<BigInteger> case_serial, Datum<BigInteger> cycle_serial, Datum<BigInteger> owner_character_id, Datum<BigInteger> revision, Datum<BigInteger> state, Datum<BigInteger> subject_character_id) implements Group {
        public Case { Objects.requireNonNull(active); Objects.requireNonNull(case_serial); Objects.requireNonNull(cycle_serial); Objects.requireNonNull(owner_character_id); Objects.requireNonNull(revision); Objects.requireNonNull(state); Objects.requireNonNull(subject_character_id); }
        public List<Datum<?>> fields() { return List.<Datum<?>>of(active, case_serial, cycle_serial, owner_character_id, revision, state, subject_character_id); }
        static Case parse(JsonNode row) {
            exact(row, "active", "case_serial", "cycle_serial", "owner_character_id", "revision", "state", "subject_character_id");
            return new Case(flag(row.get("active"), REASONS), number(row.get("case_serial"), REASONS), number(row.get("cycle_serial"), REASONS), number(row.get("owner_character_id"), REASONS), number(row.get("revision"), REASONS), number(row.get("state"), REASONS), number(row.get("subject_character_id"), REASONS));
        }
    }
    public record Aggregates(Datum<BigInteger> appeal_overturn, Datum<BigInteger> calibration, Datum<BigInteger> hc_efficiency, Datum<BigInteger> jingcha, Datum<BigInteger> pip_success, Datum<BigInteger> retention, Datum<BigInteger> targets) implements Group {
        public Aggregates { Objects.requireNonNull(appeal_overturn); Objects.requireNonNull(calibration); Objects.requireNonNull(hc_efficiency); Objects.requireNonNull(jingcha); Objects.requireNonNull(pip_success); Objects.requireNonNull(retention); Objects.requireNonNull(targets); }
        public List<Datum<?>> fields() { return List.<Datum<?>>of(appeal_overturn, calibration, hc_efficiency, jingcha, pip_success, retention, targets); }
        static Aggregates parse(JsonNode row) {
            exact(row, "appeal_overturn", "calibration", "hc_efficiency", "jingcha", "pip_success", "retention", "targets");
            return new Aggregates(number(row.get("appeal_overturn"), REASONS), number(row.get("calibration"), REASONS), number(row.get("hc_efficiency"), REASONS), number(row.get("jingcha"), REASONS), number(row.get("pip_success"), REASONS), number(row.get("retention"), REASONS), number(row.get("targets"), REASONS));
        }
    }
    public record Receipt(Datum<BigInteger> case_serial, Datum<BigInteger> choice, Datum<BigInteger> cycle_serial, Datum<BigInteger> owner_character_id, Datum<BigInteger> state, Datum<BigInteger> subject_character_id) implements Group {
        public Receipt { Objects.requireNonNull(case_serial); Objects.requireNonNull(choice); Objects.requireNonNull(cycle_serial); Objects.requireNonNull(owner_character_id); Objects.requireNonNull(state); Objects.requireNonNull(subject_character_id); }
        public List<Datum<?>> fields() { return List.<Datum<?>>of(case_serial, choice, cycle_serial, owner_character_id, state, subject_character_id); }
        static Receipt parse(JsonNode row) {
            exact(row, "case_serial", "choice", "cycle_serial", "owner_character_id", "state", "subject_character_id");
            return new Receipt(number(row.get("case_serial"), REASONS), number(row.get("choice"), REASONS), number(row.get("cycle_serial"), REASONS), number(row.get("owner_character_id"), REASONS), number(row.get("state"), REASONS), number(row.get("subject_character_id"), REASONS));
        }
    }
    public record Distribution(Datum<Boolean> available, Datum<BigInteger> bottom_slots, Datum<BigInteger> conserved_slots, Datum<BigInteger> middle_slots, Datum<BigInteger> mode, Datum<BigInteger> rule_source, Datum<BigInteger> top_slots) implements Group {
        public Distribution { Objects.requireNonNull(available); Objects.requireNonNull(bottom_slots); Objects.requireNonNull(conserved_slots); Objects.requireNonNull(middle_slots); Objects.requireNonNull(mode); Objects.requireNonNull(rule_source); Objects.requireNonNull(top_slots); }
        public List<Datum<?>> fields() { return List.<Datum<?>>of(available, bottom_slots, conserved_slots, middle_slots, mode, rule_source, top_slots); }
        static Distribution parse(JsonNode row) {
            exact(row, "available", "bottom_slots", "conserved_slots", "middle_slots", "mode", "rule_source", "top_slots");
            return new Distribution(flag(row.get("available"), REASONS), number(row.get("bottom_slots"), REASONS), number(row.get("conserved_slots"), REASONS), number(row.get("middle_slots"), REASONS), number(row.get("mode"), REASONS), number(row.get("rule_source"), REASONS), number(row.get("top_slots"), REASONS));
        }
    }
    public record Policy(Datum<BigInteger> due_cycle, Datum<BigInteger> input_revision, Datum<BigInteger> mode, Datum<BigInteger> owner_character_id, Datum<BigInteger> rule_source, Datum<BigInteger> source_case, Datum<BigInteger> source_cycle, Datum<BigInteger> source_reviewer_character_id, Datum<BigInteger> source_revision, Datum<BigInteger> status, Datum<BigInteger> subject_character_id) implements Group {
        public Policy { Objects.requireNonNull(due_cycle); Objects.requireNonNull(input_revision); Objects.requireNonNull(mode); Objects.requireNonNull(owner_character_id); Objects.requireNonNull(rule_source); Objects.requireNonNull(source_case); Objects.requireNonNull(source_cycle); Objects.requireNonNull(source_reviewer_character_id); Objects.requireNonNull(source_revision); Objects.requireNonNull(status); Objects.requireNonNull(subject_character_id); }
        public List<Datum<?>> fields() { return List.<Datum<?>>of(due_cycle, input_revision, mode, owner_character_id, rule_source, source_case, source_cycle, source_reviewer_character_id, source_revision, status, subject_character_id); }
        static Policy parse(JsonNode row) {
            exact(row, "due_cycle", "input_revision", "mode", "owner_character_id", "rule_source", "source_case", "source_cycle", "source_reviewer_character_id", "source_revision", "status", "subject_character_id");
            return new Policy(number(row.get("due_cycle"), REASONS), number(row.get("input_revision"), REASONS), number(row.get("mode"), REASONS), number(row.get("owner_character_id"), REASONS), number(row.get("rule_source"), REASONS), number(row.get("source_case"), REASONS), number(row.get("source_cycle"), REASONS), number(row.get("source_reviewer_character_id"), REASONS), number(row.get("source_revision"), REASONS), number(row.get("status"), REASONS), number(row.get("subject_character_id"), REASONS));
        }
    }
    public record Effective(Datum<BigInteger> actual_bottom_slots, Datum<BigInteger> actual_cohort_n, Datum<BigInteger> cycle, Datum<BigInteger> input_revision, Datum<BigInteger> mode, Datum<BigInteger> settled_cycle, Datum<BigInteger> settlement_receipt, Datum<BigInteger> source_case, Datum<BigInteger> source_cycle) implements Group {
        public Effective { Objects.requireNonNull(actual_bottom_slots); Objects.requireNonNull(actual_cohort_n); Objects.requireNonNull(cycle); Objects.requireNonNull(input_revision); Objects.requireNonNull(mode); Objects.requireNonNull(settled_cycle); Objects.requireNonNull(settlement_receipt); Objects.requireNonNull(source_case); Objects.requireNonNull(source_cycle); }
        public List<Datum<?>> fields() { return List.<Datum<?>>of(actual_bottom_slots, actual_cohort_n, cycle, input_revision, mode, settled_cycle, settlement_receipt, source_case, source_cycle); }
        static Effective parse(JsonNode row) {
            exact(row, "actual_bottom_slots", "actual_cohort_n", "cycle", "input_revision", "mode", "settled_cycle", "settlement_receipt", "source_case", "source_cycle");
            return new Effective(number(row.get("actual_bottom_slots"), REASONS), number(row.get("actual_cohort_n"), REASONS), number(row.get("cycle"), REASONS), number(row.get("input_revision"), REASONS), number(row.get("mode"), REASONS), number(row.get("settled_cycle"), REASONS), number(row.get("settlement_receipt"), REASONS), number(row.get("source_case"), REASONS), number(row.get("source_cycle"), REASONS));
        }
    }
    public record Score(Datum<BigInteger> mode, Datum<BigInteger> sum) implements Group {
        public Score { Objects.requireNonNull(mode); Objects.requireNonNull(sum); }
        public List<Datum<?>> fields() { return List.<Datum<?>>of(mode, sum); }
        static Score parse(JsonNode row) {
            exact(row, "mode", "sum");
            return new Score(number(row.get("mode"), REASONS), number(row.get("sum"), REASONS));
        }
    }
    public record Component(Datum<BigInteger> component, Datum<BigInteger> due_cycle, Datum<BigInteger> input_revision, Datum<BigInteger> owner_character_id, Datum<BigInteger> settled_by_owner_character_id, Datum<BigInteger> settled_cycle, Datum<BigInteger> settled_value, Datum<BigInteger> settlement_receipt, Datum<BigInteger> source_case, Datum<BigInteger> source_cycle, Datum<BigInteger> source_revision, Datum<BigInteger> status, Datum<BigInteger> subject_character_id, Datum<BigInteger> value) implements Group {
        public Component { Objects.requireNonNull(component); Objects.requireNonNull(due_cycle); Objects.requireNonNull(input_revision); Objects.requireNonNull(owner_character_id); Objects.requireNonNull(settled_by_owner_character_id); Objects.requireNonNull(settled_cycle); Objects.requireNonNull(settled_value); Objects.requireNonNull(settlement_receipt); Objects.requireNonNull(source_case); Objects.requireNonNull(source_cycle); Objects.requireNonNull(source_revision); Objects.requireNonNull(status); Objects.requireNonNull(subject_character_id); Objects.requireNonNull(value); }
        public List<Datum<?>> fields() { return List.<Datum<?>>of(component, due_cycle, input_revision, owner_character_id, settled_by_owner_character_id, settled_cycle, settled_value, settlement_receipt, source_case, source_cycle, source_revision, status, subject_character_id, value); }
        static Component parse(JsonNode row) {
            exact(row, "component", "due_cycle", "input_revision", "owner_character_id", "settled_by_owner_character_id", "settled_cycle", "settled_value", "settlement_receipt", "source_case", "source_cycle", "source_revision", "status", "subject_character_id", "value");
            return new Component(number(row.get("component"), REASONS), number(row.get("due_cycle"), REASONS), number(row.get("input_revision"), REASONS), number(row.get("owner_character_id"), REASONS), number(row.get("settled_by_owner_character_id"), REASONS), number(row.get("settled_cycle"), REASONS), number(row.get("settled_value"), REASONS), number(row.get("settlement_receipt"), REASONS), number(row.get("source_case"), REASONS), number(row.get("source_cycle"), REASONS), number(row.get("source_revision"), REASONS), number(row.get("status"), REASONS), number(row.get("subject_character_id"), REASONS), number(row.get("value"), REASONS));
        }
    }
    public record Team(Datum<BigInteger> case_serial, Datum<BigInteger> cohort_n, Datum<BigInteger> cycle_serial, Datum<BigInteger> owner_character_id, Datum<BigInteger> revision, Datum<BigInteger> source_cycle, Datum<BigInteger> status, Datum<BigInteger> subject_character_id, Aggregates aggregates) implements Group {
        public Team { Objects.requireNonNull(case_serial); Objects.requireNonNull(cohort_n); Objects.requireNonNull(cycle_serial); Objects.requireNonNull(owner_character_id); Objects.requireNonNull(revision); Objects.requireNonNull(source_cycle); Objects.requireNonNull(status); Objects.requireNonNull(subject_character_id); Objects.requireNonNull(aggregates); }
        public List<Datum<?>> fields() { return java.util.stream.Stream.of(List.<Datum<?>>of(case_serial, cohort_n, cycle_serial, owner_character_id, revision, source_cycle, status, subject_character_id), aggregates.fields()).flatMap(List::stream).toList(); }
        static Team parse(JsonNode row) {
            exact(row, "case_serial", "cohort_n", "cycle_serial", "owner_character_id", "revision", "source_cycle", "status", "subject_character_id", "aggregates");
            return new Team(number(row.get("case_serial"), REASONS), number(row.get("cohort_n"), REASONS), number(row.get("cycle_serial"), REASONS), number(row.get("owner_character_id"), REASONS), number(row.get("revision"), REASONS), number(row.get("source_cycle"), REASONS), number(row.get("status"), REASONS), number(row.get("subject_character_id"), REASONS), Aggregates.parse(row.get("aggregates")));
        }
    }
}
