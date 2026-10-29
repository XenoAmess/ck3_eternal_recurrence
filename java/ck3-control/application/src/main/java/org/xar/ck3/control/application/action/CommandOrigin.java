package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Closed origin family for the one coordinator, journal and submit capability. */
public sealed interface CommandOrigin permits CommandOrigin.Gameplay, CommandOrigin.Frontend, CommandOrigin.LifecycleTerminal, CommandOrigin.Reconciliation, CommandOrigin.PhysicalStatusOnly {
    String machineId();
    GameGeneration game();
    BigInteger expectedRevision();
    record Gameplay(ObservationIdentity before) implements CommandOrigin {
        public Gameplay { Objects.requireNonNull(before); }
        @Override public String machineId() { return before.machineId(); }
        @Override public GameGeneration game() { return before.game(); }
        @Override public BigInteger expectedRevision() { return before.frame().identity().nativeRevision(); }
    }
    record Frontend(FrontendIdentity identity) implements CommandOrigin {
        public Frontend { Objects.requireNonNull(identity); }
        @Override public String machineId() { return identity.machineId(); }
        @Override public GameGeneration game() { return identity.game(); }
        @Override public BigInteger expectedRevision() { return identity.frame().expectedRevision(); }
    }
    record LifecycleTerminal(LifecycleIdentity identity) implements CommandOrigin {
        public LifecycleTerminal { Objects.requireNonNull(identity); }
        @Override public String machineId() { return identity.machineId(); }
        @Override public GameGeneration game() { return identity.game(); }
        @Override public BigInteger expectedRevision() { return identity.frame().nativeRevision(); }
    }
    /** Factual read-only scope; never a gameplay or action submission origin. */
    record Reconciliation(ReconciliationIdentity identity) implements CommandOrigin {
        public Reconciliation { Objects.requireNonNull(identity); }
        @Override public String machineId() { return identity.factual().machineId(); }
        @Override public GameGeneration game() { return identity.factual().game(); }
        @Override public BigInteger expectedRevision() { return identity.factual().frame().identity().nativeRevision(); }
    }
    /** Source-bound factual native status only. Never an action, ordinary plan or save origin. */
    record PhysicalStatusOnly(PhysicalStatusIdentity identity) implements CommandOrigin {
        public PhysicalStatusOnly { Objects.requireNonNull(identity); }
        @Override public String machineId() { return identity.machineId(); }
        @Override public GameGeneration game() { return identity.game(); }
        @Override public BigInteger expectedRevision() { return identity.nativeRevision(); }
    }
    default PhysicalStatusIdentity requirePhysicalStatusOnly() {
        if (this instanceof PhysicalStatusOnly physical) return physical.identity();
        throw new IllegalStateException("an actual read-only physical status identity is required");
    }
    /** Same-phase comparison only. Starting or replacing a Game requires the dedicated lifecycle proof branch. */
    default boolean acceptsGuard(CommandOrigin actual) {
        if (this instanceof Gameplay gameplay)
            return actual instanceof Gameplay observed && gameplay.before().equals(observed.before());
        if (this instanceof LifecycleTerminal lifecycle)
            return actual instanceof LifecycleTerminal observed && lifecycle.identity().sameGuardFrame(observed.identity());
        if (this instanceof Reconciliation reconciliation)
            return actual instanceof Reconciliation observed && reconciliation.identity().sameGuardFrame(observed.identity());
        if (this instanceof PhysicalStatusOnly physical)
            return actual instanceof PhysicalStatusOnly observed && physical.identity().sameGuardFrame(observed.identity());
        return actual instanceof Frontend observed && ((Frontend) this).identity().sameGuardFrame(observed.identity());
    }
    default ReconciliationIdentity requireReconciliation() {
        if (this instanceof Reconciliation reconciliation) return reconciliation.identity();
        throw new IllegalStateException("a real read-only reconciliation origin is required");
    }
    default ObservationIdentity requireGameplay() {
        if (this instanceof Gameplay gameplay) return gameplay.before();
        throw new IllegalStateException("non-gameplay origin has no ordinary observation identity");
    }
    default FrontendIdentity requireFrontend() {
        if (this instanceof Frontend frontend) return frontend.identity();
        throw new IllegalStateException("gameplay origin is not a frontend session");
    }
    default LifecycleIdentity requireLifecycleTerminal() {
        if (this instanceof LifecycleTerminal lifecycle) return lifecycle.identity();
        throw new IllegalStateException("a real lifecycle terminal origin is required");
    }
}

