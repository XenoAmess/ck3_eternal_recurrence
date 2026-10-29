package org.xar.ck3.control.wave3.governance.educationoptions;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Ordered native bank observations. These facts grant no ordinary-context or dispatch qualification. */
public final class EducationOptionsModel {
    private EducationOptionsModel() { }
    public enum Availability {
        AVAILABLE("available"), UNAVAILABLE("unavailable");
        private final String wire;
        Availability(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record Row(long declaredOrdinal, long flagFullU32, String canonicalFlagKey,
                      boolean selected, int bankValueU8, boolean ordinalSelected) {
        public Row {
            unsigned(declaredOrdinal, 4_294_967_295L); unsigned(flagFullU32, 4_294_967_295L);
            StrictJson.require(bankValueU8 >= 0 && bankValueU8 <= 255, "native bank byte outside u8");
            StrictJson.require(ordinalSelected == (bankValueU8 == 1), "ordinal selection must reflect this ordinal's byte == 1");
            if (canonicalFlagKey != null) { key(canonicalFlagKey); }
        }
    }
    public record Rows(Availability status, List<Row> rows, String unavailableReason) {
        public Rows {
            Objects.requireNonNull(status); rows = List.copyOf(rows);
            StrictJson.require(rows.size() <= 4096, "native education option row limit");
            if (status == Availability.UNAVAILABLE) {
                StrictJson.require(rows.isEmpty(), "unavailable rows must be empty"); reason(unavailableReason);
            } else {
                StrictJson.require(unavailableReason == null, "available rows carry no unavailable reason");
                Map<Long, Boolean> firstSelectedByFlag = new HashMap<>();
                for (int ordinal = 0; ordinal < rows.size(); ordinal++) {
                    Row row = rows.get(ordinal);
                    StrictJson.require(row.declaredOrdinal() == ordinal, "declared ordinal must retain source order");
                    boolean first = firstSelectedByFlag.computeIfAbsent(row.flagFullU32(), ignored -> row.ordinalSelected());
                    StrictJson.require(row.selected() == first, "legacy selected observes the first equal flag's byte");
                }
            }
        }
    }
    public record Pair(long childFullId, long guardianFullId) {
        public Pair { identity(childFullId); identity(guardianFullId); }
    }
    public record RowsValidation(String exactBuild, String interactionKey, Availability contextStatus, Rows rows) {
        public RowsValidation {
            educationContext(exactBuild, interactionKey); Objects.requireNonNull(contextStatus); Objects.requireNonNull(rows);
            StrictJson.require(rows.status() != Availability.AVAILABLE || contextStatus == Availability.AVAILABLE, "available rows require available owning context");
        }
    }
    public record MaterializationValidation(String exactBuild, String interactionKey, Availability contextStatus,
                                             Materialization materialization, Optional<Availability> owningRowsStatus,
                                             Optional<Pair> finalRoles) {
        public MaterializationValidation {
            educationContext(exactBuild, interactionKey); Objects.requireNonNull(contextStatus); Objects.requireNonNull(materialization);
            owningRowsStatus = Objects.requireNonNull(owningRowsStatus); finalRoles = Objects.requireNonNull(finalRoles);
            if (materialization.status() == Availability.AVAILABLE) {
                StrictJson.require(contextStatus == Availability.AVAILABLE && owningRowsStatus.orElse(null) == Availability.AVAILABLE,
                        "available materialization requires available owned rows");
                StrictJson.require(materialization.pair().isEmpty() || materialization.pair().equals(finalRoles), "materialized pair must equal final secondary roles");
            }
            boolean consumesRoles = materialization.status() == Availability.AVAILABLE && materialization.pair().isPresent();
            StrictJson.require(consumesRoles || finalRoles.isEmpty(), "only consumed role facts belong to this projection");
        }
    }
    /** Optional list distinguishes unspecified keys from an explicit all-off empty list; duplicates retain order. */
    public record Materialization(Availability status, Optional<Pair> pair, Optional<List<String>> requestedOptionKeys,
                                  Boolean pairMatches, Boolean optionKeysMatch, String unavailableReason) {
        public Materialization {
            Objects.requireNonNull(status); pair = Objects.requireNonNull(pair);
            requestedOptionKeys = Objects.requireNonNull(requestedOptionKeys).map(List::copyOf);
            requestedOptionKeys.ifPresent(keys -> keys.forEach(EducationOptionsModel::key));
            StrictJson.require(pair.isPresent() || pairMatches == null, "unspecified pair match must remain null");
            StrictJson.require(requestedOptionKeys.isPresent() || optionKeysMatch == null, "unspecified option match must remain null");
            if (status == Availability.UNAVAILABLE) { reason(unavailableReason); }
            else {
                StrictJson.require(unavailableReason == null, "available materialization carries no unavailable reason");
                StrictJson.require(pair.isEmpty() || Boolean.TRUE.equals(pairMatches), "available supplied pair requires actual match");
                StrictJson.require(requestedOptionKeys.isEmpty() || Boolean.TRUE.equals(optionKeysMatch), "available supplied keys require actual match");
            }
        }
    }
    public record Input(String exactBuild, String interactionKey, Availability contextStatus,
                        Optional<Rows> rows, Optional<Materialization> materialization, Optional<Pair> finalRoles) {
        public Input {
            Objects.requireNonNull(exactBuild); Objects.requireNonNull(interactionKey); Objects.requireNonNull(contextStatus);
            rows = Objects.requireNonNull(rows); materialization = Objects.requireNonNull(materialization); finalRoles = Objects.requireNonNull(finalRoles);
            if (rows.isPresent()) { new RowsValidation(exactBuild, interactionKey, contextStatus, rows.orElseThrow()); }
            if (materialization.isPresent()) { new MaterializationValidation(exactBuild, interactionKey, contextStatus, materialization.orElseThrow(), rows.map(Rows::status), finalRoles); }
            boolean consumesRoles = materialization.isPresent() && materialization.get().status() == Availability.AVAILABLE
                    && materialization.get().pair().isPresent();
            StrictJson.require(consumesRoles || finalRoles.isEmpty(), "only consumed role facts belong to this projection");
        }
    }
    public static String key(String value) {
        StrictJson.require(value != null && value.matches("[A-Za-z0-9_]{1,128}"), "exact ASCII interaction key required"); return value;
    }
    private static void reason(String value) {
        StrictJson.text(value); StrictJson.require(value.codePointCount(0, value.length()) <= 512, "bounded reason required");
    }
    private static void identity(long value) { StrictJson.require(value >= 1 && value <= 4_294_967_294L, "full recipient identity outside native range"); }
    private static void educationContext(String exactBuild, String interactionKey) {
        StrictJson.require("1.20.0.4".equals(exactBuild) && "educate_child_interaction".equals(interactionKey), "actual .4 education context required");
    }
    private static void unsigned(long value, long maximum) { StrictJson.require(value >= 0 && value <= maximum, "native unsigned value outside range"); }
}
