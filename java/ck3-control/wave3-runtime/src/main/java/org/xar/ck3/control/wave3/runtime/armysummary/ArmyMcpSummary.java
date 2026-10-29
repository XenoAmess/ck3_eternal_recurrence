package org.xar.ck3.control.wave3.runtime.armysummary;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Observational MCP projection. No frame qualification, decision or native query authority. */
public final class ArmyMcpSummary {
    public static final String RESULT_LOCATION = "compact_mcp_summary";
    public static final String ARMY_STEP = "query-army-strengths-v1";
    private ArmyMcpSummary() { }

    public enum QueryStatus {
        AVAILABLE("available"), PARTIAL("partial"), UNAVAILABLE("unavailable");
        private final String wire;
        QueryStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum RowStatus {
        AVAILABLE("available"), UNAVAILABLE("unavailable");
        private final String wire;
        RowStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum Profile {
        ORDINARY_CORE("ordinary_core_v1"), OBSERVED_HISTORY_FULL("observed_history_full_v1");
        private final String wire;
        Profile(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum Coverage {
        NOT_REQUESTED("not_requested"), EXPORTED_RETAINED("exported_retained");
        private final String wire;
        Coverage(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    /** All members are nullable: old producer's dict.get emits explicit JSON null. */
    public record ArmyRow(RowStatus status, Long armyId, Long nativeCarmyId, Long regimentCount,
                          Long currentSoldiers, Long maximumSoldiers, Long aiBasePowerRaw,
                          Long aiBasePowerScale, Long currentSupplyRaw, Long currentSupplyScale,
                          Long currentAttritionFractionRaw, Long currentAttritionFractionScale,
                          String unavailableReason) {
        public ArmyRow {
            nonnegative(armyId); nonnegative(nativeCarmyId); nonnegative(regimentCount);
            nonnegative(currentSoldiers); nonnegative(maximumSoldiers);
            signed(aiBasePowerRaw); nonnegative(aiBasePowerScale); signed(currentSupplyRaw);
            nonnegative(currentSupplyScale); signed(currentAttritionFractionRaw);
            nonnegative(currentAttritionFractionScale); nullableText(unavailableReason);
        }
    }
    public record SourceRevision(Long revision, Long nativeRevision) {
        public SourceRevision { nonnegative(revision); nonnegative(nativeRevision); }
    }
    public sealed interface ArmyIds permits DerivedArmyIds, NullArmyIds, ExplicitArmyIds { }
    public record DerivedArmyIds() implements ArmyIds { }
    public record NullArmyIds() implements ArmyIds { }
    /** Order, duplicates, null entries and an empty list remain distinct; this is not request validation. */
    public record ExplicitArmyIds(List<Long> values) implements ArmyIds {
        public ExplicitArmyIds {
            Objects.requireNonNull(values); values.forEach(ArmyMcpSummary::nonnegative);
            values = Collections.unmodifiableList(new ArrayList<>(values));
        }
    }
    /** Nanoseconds in the existing numeric MCP interface must be exact safe integers. */
    public record NativeTiming(long readTotalNs, long ownerQueryNs, long baselineReadNs,
                               long richAttachNs, long serializeNs) {
        public NativeTiming {
            for (long value : new long[]{readTotalNs, ownerQueryNs, baselineReadNs, richAttachNs, serializeNs}) {
                StrictJson.safe(value, 0);
            }
            StrictJson.require(Math.max(baselineReadNs, richAttachNs) <= ownerQueryNs
                    && ownerQueryNs <= readTotalNs, "native timing nesting disagrees");
            // serialize_ns is a separate interval: the original producer does not cap it by owner/read.
        }
    }
    /** Nullable scalar fields preserve the old summary, while collection shape is mandatory. */
    public record Query(Boolean accepted, QueryStatus status, Long querySequence, Profile profile,
                        Coverage coverage, SourceRevision source, ArmyIds armyIds,
                        List<ArmyRow> armies, NativeTiming nativeTiming) {
        public Query {
            nonnegative(querySequence); Objects.requireNonNull(source); Objects.requireNonNull(armyIds);
            armies = List.copyOf(armies);
        }
    }
    public record Plan(String selectedStep, String phase) {
        public Plan { nullableText(selectedStep); nullableText(phase); }
    }
    public record AutoTurn(String status, String selectedStep, Plan plan, Query result) {
        public AutoTurn {
            nullableText(status); nullableText(selectedStep); Objects.requireNonNull(plan); Objects.requireNonNull(result);
        }
    }

    static void nonnegative(Long value) { if (value != null) { StrictJson.safe(value, 0); } }
    static void signed(Long value) {
        if (value != null) {
            StrictJson.require(value >= -StrictJson.MAX_SAFE_INTEGER && value <= StrictJson.MAX_SAFE_INTEGER,
                    "MCP numeric value outside exact safe integer domain");
        }
    }
    static void nullableText(String value) { if (value != null && !value.isEmpty()) { StrictJson.text(value); } }
}
