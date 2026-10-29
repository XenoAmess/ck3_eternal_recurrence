package org.xar.ck3.control.nativebridge.capabilities.china_career;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import java.util.Objects;
import static org.xar.ck3.control.nativebridge.capabilities.china_career.CareerJson.*;
public final class OwnerGroups {
    private OwnerGroups() { }
    static final Set<String> REASONS = null;
    public record Central(Datum<BigInteger> subject_character_id, Datum<BigInteger> cycle_serial, Datum<BigInteger> case_serial, Datum<BigInteger> stage11_status) implements Group {
        public Central { Objects.requireNonNull(subject_character_id); Objects.requireNonNull(cycle_serial); Objects.requireNonNull(case_serial); Objects.requireNonNull(stage11_status); }
        public List<Datum<?>> fields() { return List.<Datum<?>>of(subject_character_id, cycle_serial, case_serial, stage11_status); }
        static Central parse(JsonNode row) {
            exact(row, "subject_character_id", "cycle_serial", "case_serial", "stage11_status");
            return new Central(number(row.get("subject_character_id"), REASONS), number(row.get("cycle_serial"), REASONS), number(row.get("case_serial"), REASONS), number(row.get("stage11_status"), REASONS));
        }
    }
    public record Source(Datum<BigInteger> status, Datum<BigInteger> owner_character_id, Datum<BigInteger> subject_character_id, Datum<BigInteger> p2c_cycle_serial, Datum<BigInteger> p2c_case_serial, Datum<BigInteger> al_cycle_serial, Datum<BigInteger> al_case_serial) implements Group {
        public Source { Objects.requireNonNull(status); Objects.requireNonNull(owner_character_id); Objects.requireNonNull(subject_character_id); Objects.requireNonNull(p2c_cycle_serial); Objects.requireNonNull(p2c_case_serial); Objects.requireNonNull(al_cycle_serial); Objects.requireNonNull(al_case_serial); }
        public List<Datum<?>> fields() { return List.<Datum<?>>of(status, owner_character_id, subject_character_id, p2c_cycle_serial, p2c_case_serial, al_cycle_serial, al_case_serial); }
        static Source parse(JsonNode row) {
            exact(row, "status", "owner_character_id", "subject_character_id", "p2c_cycle_serial", "p2c_case_serial", "al_cycle_serial", "al_case_serial");
            return new Source(number(row.get("status"), REASONS), number(row.get("owner_character_id"), REASONS), number(row.get("subject_character_id"), REASONS), number(row.get("p2c_cycle_serial"), REASONS), number(row.get("p2c_case_serial"), REASONS), number(row.get("al_cycle_serial"), REASONS), number(row.get("al_case_serial"), REASONS));
        }
    }
    public record AlCase(Datum<BigInteger> owner_character_id, Datum<BigInteger> subject_character_id, Datum<BigInteger> cycle_serial, Datum<BigInteger> case_serial, Datum<BigInteger> state, Datum<Boolean> active, Datum<BigInteger> revision) implements Group {
        public AlCase { Objects.requireNonNull(owner_character_id); Objects.requireNonNull(subject_character_id); Objects.requireNonNull(cycle_serial); Objects.requireNonNull(case_serial); Objects.requireNonNull(state); Objects.requireNonNull(active); Objects.requireNonNull(revision); }
        public List<Datum<?>> fields() { return List.<Datum<?>>of(owner_character_id, subject_character_id, cycle_serial, case_serial, state, active, revision); }
        static AlCase parse(JsonNode row) {
            exact(row, "owner_character_id", "subject_character_id", "cycle_serial", "case_serial", "state", "active", "revision");
            return new AlCase(number(row.get("owner_character_id"), REASONS), number(row.get("subject_character_id"), REASONS), number(row.get("cycle_serial"), REASONS), number(row.get("case_serial"), REASONS), number(row.get("state"), REASONS), flag(row.get("active"), REASONS), number(row.get("revision"), REASONS));
        }
    }
    public record M360Receipt(Datum<BigInteger> owner_character_id, Datum<BigInteger> subject_character_id, Datum<BigInteger> cycle_serial, Datum<BigInteger> case_serial, Datum<BigInteger> state, Datum<BigInteger> choice) implements Group {
        public M360Receipt { Objects.requireNonNull(owner_character_id); Objects.requireNonNull(subject_character_id); Objects.requireNonNull(cycle_serial); Objects.requireNonNull(case_serial); Objects.requireNonNull(state); Objects.requireNonNull(choice); }
        public List<Datum<?>> fields() { return List.<Datum<?>>of(owner_character_id, subject_character_id, cycle_serial, case_serial, state, choice); }
        static M360Receipt parse(JsonNode row) {
            exact(row, "owner_character_id", "subject_character_id", "cycle_serial", "case_serial", "state", "choice");
            return new M360Receipt(number(row.get("owner_character_id"), REASONS), number(row.get("subject_character_id"), REASONS), number(row.get("cycle_serial"), REASONS), number(row.get("case_serial"), REASONS), number(row.get("state"), REASONS), number(row.get("choice"), REASONS));
        }
    }
    public record Portfolio(Datum<Boolean> closed, Datum<BigInteger> status, Datum<BigInteger> cycle_serial, Datum<Boolean> final_conservation_ok, Datum<Boolean> terminal_history_accruing, Datum<BigInteger> history_cycle_count, Datum<Boolean> terminal_success, Datum<Boolean> terminal_na, Datum<BigInteger> terminal_reason, Datum<BigInteger> terminal_owned_operations, Datum<BigInteger> terminal_skipped_manager_only, Datum<BigInteger> terminal_skipped_charter) implements Group {
        public Portfolio { Objects.requireNonNull(closed); Objects.requireNonNull(status); Objects.requireNonNull(cycle_serial); Objects.requireNonNull(final_conservation_ok); Objects.requireNonNull(terminal_history_accruing); Objects.requireNonNull(history_cycle_count); Objects.requireNonNull(terminal_success); Objects.requireNonNull(terminal_na); Objects.requireNonNull(terminal_reason); Objects.requireNonNull(terminal_owned_operations); Objects.requireNonNull(terminal_skipped_manager_only); Objects.requireNonNull(terminal_skipped_charter); }
        public List<Datum<?>> fields() { return List.<Datum<?>>of(closed, status, cycle_serial, final_conservation_ok, terminal_history_accruing, history_cycle_count, terminal_success, terminal_na, terminal_reason, terminal_owned_operations, terminal_skipped_manager_only, terminal_skipped_charter); }
        static Portfolio parse(JsonNode row) {
            exact(row, "closed", "status", "cycle_serial", "final_conservation_ok", "terminal_history_accruing", "history_cycle_count", "terminal_success", "terminal_na", "terminal_reason", "terminal_owned_operations", "terminal_skipped_manager_only", "terminal_skipped_charter");
            return new Portfolio(flag(row.get("closed"), REASONS), number(row.get("status"), REASONS), number(row.get("cycle_serial"), REASONS), flag(row.get("final_conservation_ok"), REASONS), flag(row.get("terminal_history_accruing"), REASONS), number(row.get("history_cycle_count"), REASONS), flag(row.get("terminal_success"), REASONS), flag(row.get("terminal_na"), REASONS), number(row.get("terminal_reason"), REASONS), number(row.get("terminal_owned_operations"), REASONS), number(row.get("terminal_skipped_manager_only"), REASONS), number(row.get("terminal_skipped_charter"), REASONS));
        }
    }
}
