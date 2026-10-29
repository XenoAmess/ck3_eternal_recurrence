package org.xar.ck3.control.wave2.military.combatwire;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;

/** An immutable, revalidated production-v3 observation. Its scope is precontact, not an actual phase fire. */
public final class CombatPhaseInputs {
    public enum Status { AVAILABLE, UNAVAILABLE }
    public record Completeness(boolean phaseRawObservationReady, boolean offlineExactStateRefsReady,
            boolean inputObservationReady, boolean astEvaluatorReady, List<String> missingFidelityGates) {
        public Completeness { missingFidelityGates = List.copyOf(missingFidelityGates); }
        public boolean monteCarloReady() { return false; }
        public boolean transitionFidelityGate() { return false; }
        public boolean plannerUsable() { return false; }
        public boolean activeAttackAllowed() { return false; }
    }
    private final CombatSimulationInputs baseInputs;
    private final Completeness completeness;
    private final ObjectNode normalized;

    CombatPhaseInputs(CombatSimulationInputs baseInputs, Completeness completeness, ObjectNode normalized) {
        this.baseInputs = Objects.requireNonNull(baseInputs);
        this.completeness = Objects.requireNonNull(completeness);
        this.normalized = normalized.deepCopy();
    }
    public CombatSimulationInputs baseInputs() { return baseInputs; }
    public Completeness completeness() { return completeness; }
    public Status status() { return completeness.inputObservationReady() ? Status.AVAILABLE : Status.UNAVAILABLE; }
    public String wireStatus() { return status() == Status.AVAILABLE ? "available" : "unavailable"; }
    /** JSON is a detached serialization, never mutable backing storage. */
    public ObjectNode toJson() { return normalized.deepCopy(); }
}
