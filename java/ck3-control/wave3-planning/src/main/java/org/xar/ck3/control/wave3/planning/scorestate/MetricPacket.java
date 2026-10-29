package org.xar.ck3.control.wave3.planning.scorestate;

import java.util.EnumMap;
import java.util.Map;
import java.util.Objects;

/** Immutable typed packet; map absence and an explicit null row remain different. */
public record MetricPacket(Map<MetricName, MetricRow> rows) {
    public MetricPacket {
        Objects.requireNonNull(rows);
        EnumMap<MetricName, MetricRow> copied = new EnumMap<>(MetricName.class);
        rows.forEach((key, value) -> copied.put(Objects.requireNonNull(key), Objects.requireNonNull(value)));
        rows = Map.copyOf(copied);
    }
    public MetricRow row(MetricName name) { return rows.getOrDefault(name, new MetricRow.Missing()); }
}
