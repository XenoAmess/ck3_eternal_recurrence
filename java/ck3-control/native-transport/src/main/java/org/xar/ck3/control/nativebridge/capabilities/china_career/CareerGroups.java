package org.xar.ck3.control.nativebridge.capabilities.china_career;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import java.util.Objects;
import static org.xar.ck3.control.nativebridge.capabilities.china_career.CareerJson.*;
public final class CareerGroups {
  private CareerGroups() { }
  static final Set<String> REASONS = null;
  public record Identity(Datum<BigInteger> case_serial, Datum<BigInteger> cycle_serial, Datum<BigInteger> owner_character_id, Datum<BigInteger> subject_character_id) implements Group {
    public Identity { Objects.requireNonNull(case_serial); Objects.requireNonNull(cycle_serial); Objects.requireNonNull(owner_character_id); Objects.requireNonNull(subject_character_id); }
    public List<Datum<?>> fields() { return List.<Datum<?>>of(case_serial, cycle_serial, owner_character_id, subject_character_id); }
    static Identity parse(JsonNode row) {
      exact(row, "case_serial", "cycle_serial", "owner_character_id", "subject_character_id");
      return new Identity(number(row.get("case_serial"), REASONS), number(row.get("cycle_serial"), REASONS), number(row.get("owner_character_id"), REASONS), number(row.get("subject_character_id"), REASONS));
    }
  }
  public record Receipt(Datum<BigInteger> case_serial, Datum<BigInteger> cycle_serial, Datum<BigInteger> owner_character_id, Datum<BigInteger> subject_character_id, Datum<BigInteger> state, Datum<BigInteger> choice, boolean provider_observed) implements Group {
    public Receipt { Objects.requireNonNull(case_serial); Objects.requireNonNull(cycle_serial); Objects.requireNonNull(owner_character_id); Objects.requireNonNull(subject_character_id); Objects.requireNonNull(state); Objects.requireNonNull(choice); }
    public List<Datum<?>> fields() { return List.<Datum<?>>of(case_serial, cycle_serial, owner_character_id, subject_character_id, state, choice); }
    static Receipt parse(JsonNode row) {
      exact(row, "case_serial", "cycle_serial", "owner_character_id", "subject_character_id", "state", "choice", "provider_observed");
      return new Receipt(number(row.get("case_serial"), REASONS), number(row.get("cycle_serial"), REASONS), number(row.get("owner_character_id"), REASONS), number(row.get("subject_character_id"), REASONS), number(row.get("state"), REASONS), number(row.get("choice"), REASONS), bool(row.get("provider_observed")));
    }
  }
  public record Partition(Datum<BigInteger> authorized, Datum<BigInteger> available, Datum<BigInteger> reserved, Datum<BigInteger> occupied, Datum<BigInteger> frozen, Datum<BigInteger> reclaimed, Datum<Boolean> conserved, boolean provider_observed) implements Group {
    public Partition { Objects.requireNonNull(authorized); Objects.requireNonNull(available); Objects.requireNonNull(reserved); Objects.requireNonNull(occupied); Objects.requireNonNull(frozen); Objects.requireNonNull(reclaimed); Objects.requireNonNull(conserved); }
    public List<Datum<?>> fields() { return List.<Datum<?>>of(authorized, available, reserved, occupied, frozen, reclaimed, conserved); }
    static Partition parse(JsonNode row) {
      exact(row, "authorized", "available", "reserved", "occupied", "frozen", "reclaimed", "conserved", "provider_observed");
      return new Partition(number(row.get("authorized"), REASONS), number(row.get("available"), REASONS), number(row.get("reserved"), REASONS), number(row.get("occupied"), REASONS), number(row.get("frozen"), REASONS), number(row.get("reclaimed"), REASONS), flag(row.get("conserved"), REASONS), bool(row.get("provider_observed")));
    }
  }
  public record Cost(Datum<BigInteger> manager_cost_total, boolean provider_observed) implements Group {
    public Cost { Objects.requireNonNull(manager_cost_total); }
    public List<Datum<?>> fields() { return List.<Datum<?>>of(manager_cost_total); }
    static Cost parse(JsonNode row) {
      exact(row, "manager_cost_total", "provider_observed");
      return new Cost(number(row.get("manager_cost_total"), REASONS), bool(row.get("provider_observed")));
    }
  }
}
