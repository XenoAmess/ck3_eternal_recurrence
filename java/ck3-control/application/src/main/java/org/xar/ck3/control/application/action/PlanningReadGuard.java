package org.xar.ck3.control.application.action;

import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete exact binding from the real source-bound observer. Frontend has no fake living-map flags. */
public record PlanningReadGuard(GuardEvidence binding, Readiness readiness, String originalBindingSha256) {
    public sealed interface Readiness permits Gameplay, Frontend, LifecycleTerminal, Reconciliation, PhysicalStatus { }
    public record Gameplay(boolean paused, boolean mapReady, boolean playerAlive) implements Readiness { }
    public record Frontend() implements Readiness { }
    public record LifecycleTerminal() implements Readiness { }
    public record Reconciliation() implements Readiness { }
    public record PhysicalStatus(PhysicalStatusIdentity identity) implements Readiness {
        public PhysicalStatus { Objects.requireNonNull(identity); }
    }
    public PlanningReadGuard {
        Objects.requireNonNull(binding); Objects.requireNonNull(readiness);
        StrictJson.require(binding.origin() instanceof CommandOrigin.Gameplay && readiness instanceof Gameplay
                || binding.origin() instanceof CommandOrigin.Frontend && readiness instanceof Frontend
                || binding.origin() instanceof CommandOrigin.LifecycleTerminal && readiness instanceof LifecycleTerminal
                || binding.origin() instanceof CommandOrigin.Reconciliation && readiness instanceof Reconciliation
                || binding.origin() instanceof CommandOrigin.PhysicalStatusOnly physical && readiness instanceof PhysicalStatus status
                    && physical.identity().sameGuardFrame(status.identity()),
                "read readiness crossed its exact origin phase");
        StrictJson.require(originalBindingSha256 != null && originalBindingSha256.matches("[0-9a-f]{64}"), "complete original binding digest required");
    }
    public PlanningReadGuard(GuardEvidence binding, boolean paused, boolean mapReady, boolean playerAlive, String originalBindingSha256) {
        this(binding, new Gameplay(paused, mapReady, playerAlive), originalBindingSha256);
    }
    public PlanningReadGuard(GuardEvidence binding, String originalBindingSha256) {
        this(binding, new Frontend(), originalBindingSha256);
    }
    public ReadContract.GuardMode guardMode() {
        return switch (readiness) {
            case Gameplay ignored -> ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP;
            case Frontend ignored -> ReadContract.GuardMode.FRONTEND_SESSION;
            case LifecycleTerminal ignored -> ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION;
            case Reconciliation ignored -> ReadContract.GuardMode.RECONCILIATION_OBSERVATION;
            case PhysicalStatus ignored -> ReadContract.GuardMode.STATUS_ONLY;
        };
    }
    public boolean paused() { return gameplay().paused(); }
    public boolean mapReady() { return gameplay().mapReady(); }
    public boolean playerAlive() { return gameplay().playerAlive(); }
    private Gameplay gameplay() {
        if (readiness instanceof Gameplay gameplay) return gameplay;
        throw new IllegalStateException("non-gameplay query has no ordinary readiness flags");
    }
}

