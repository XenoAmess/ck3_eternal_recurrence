package org.xar.ck3.control.wave2.planning.scoretarget;

import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Narrow writes performed by _project_metrics:825–842, before later metric stages. */
public record RebellionMetricDelta(WarScope scope, Update update) {
    public RebellionMetricDelta { Objects.requireNonNull(scope); Objects.requireNonNull(update); }
    public sealed interface WarScope permits ListedScope, WorldScope { String sourceRef(); }
    public record ListedScope(PlayerWarDefenceResult result, String sourceRef) implements WarScope {
        public ListedScope { Objects.requireNonNull(result); StrictJson.text(sourceRef); }
    }
    public record WorldScope(boolean ownDefence, String sourceRef) implements WarScope {
        public WorldScope { StrictJson.text(sourceRef); }
    }
    public sealed interface Update permits Unchanged, ObservedNoRebellion, UnknownControl { }
    public record Unchanged() implements Update { }
    public record ObservedNoRebellion(String sourceRef, String locator) implements Update {
        public ObservedNoRebellion { StrictJson.text(sourceRef); StrictJson.text(locator); }
    }
    public record UnknownControl(String sourceRef) implements Update {
        public UnknownControl { StrictJson.text(sourceRef); }
    }
}
