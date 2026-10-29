package org.xar.ck3.control.wave3.planning.scorestate;

/** Single scoring-name/unit registry, matching the unchanged Python producer. */
public enum MetricName {
    REALM("Q_realm", "quality_county_equivalent"), DYNASTY("K_dynasty", "quality_county_equivalent"),
    LEGACY("legacy_ranks", "rank"), CONTROL("control_average", "fraction"), REBELS("rebel_share", "fraction"),
    GOLD("gold", "gold"), INCOME("gross_income", "gold/month"), EXPENSES("total_expenses", "gold/month"),
    MILITARY("military_current", "gold/month"), RAISED("military_all_raised", "gold/month"),
    DUE("due_commitments", "gold"), POWER("P_quality", "standard_soldier_equivalent"),
    CONTINUATION("continuation_legal", "boolean"), BACKUP("backup_heirs", "person"),
    DISCRETIONARY("u_discretionary", "gold/month"), REALM_COUNT("realm_county_count", "county"),
    DYNASTY_COUNT("dynasty_county_count", "county"), HOUSE("house_anchor_id", "id"),
    DYNASTY_ANCHOR("dynasty_anchor_id", "id"), BRANCHES("active_family_branches", "house");

    private final String wire;
    private final String unit;
    MetricName(String wire, String unit) { this.wire = wire; this.unit = unit; }
    public String wire() { return wire; }
    public String unit() { return unit; }
}
