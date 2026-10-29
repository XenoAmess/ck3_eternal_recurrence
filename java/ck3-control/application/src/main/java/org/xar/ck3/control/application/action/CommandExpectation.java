package org.xar.ck3.control.application.action;

import java.util.Objects;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;

/** Each expectation belongs to exactly one origin phase. */
public sealed interface CommandExpectation permits CommandExpectation.Gameplay, CommandExpectation.Frontend, CommandExpectation.GameplayEntry, CommandExpectation.LifecycleTerminal, CommandExpectation.OperatorRebind {
    CommandOrigin origin();
    G2Source source();
    record Gameplay(ExpectedPostcondition expected) implements CommandExpectation {
        public Gameplay { Objects.requireNonNull(expected); }
        @Override public CommandOrigin origin() { return new CommandOrigin.Gameplay(expected.before()); }
        @Override public G2Source source() { return expected.source(); }
    }
    record Frontend(FrontendExpectedPostcondition expected) implements CommandExpectation {
        public Frontend { Objects.requireNonNull(expected); }
        @Override public CommandOrigin origin() { return new CommandOrigin.Frontend(expected.before()); }
        @Override public G2Source source() { return expected.source(); }
    }
    /** Starting gameplay remains a frontend command until the actual bootstrap is verified. */
    record GameplayEntry(FrontendGameplayExpectedPostcondition expected) implements CommandExpectation {
        public GameplayEntry { Objects.requireNonNull(expected); }
        @Override public CommandOrigin origin() { return new CommandOrigin.Frontend(expected.before()); }
        @Override public G2Source source() { return expected.source(); }
    }
    record LifecycleTerminal(LifecycleExpectedPostcondition expected) implements CommandExpectation {
        public LifecycleTerminal { Objects.requireNonNull(expected); }
        @Override public CommandOrigin origin() { return new CommandOrigin.LifecycleTerminal(expected.before()); }
        @Override public G2Source source() { return expected.source(); }
    }
    record OperatorRebind(OperatorRebindExpectation expected) implements CommandExpectation {
        public OperatorRebind { Objects.requireNonNull(expected); }
        @Override public CommandOrigin origin() { return expected.origin(); }
        @Override public G2Source source() { return expected.source(); }
    }
    default OperatorRebindExpectation requireOperatorRebind() {
        if (this instanceof OperatorRebind operator) return operator.expected();
        throw new IllegalStateException("dedicated operator rebind expectation required");
    }
    default ExpectedPostcondition requireGameplay() {
        if (this instanceof Gameplay gameplay) return gameplay.expected();
        throw new IllegalStateException("frontend expectation is not a gameplay postcondition");
    }
    default FrontendExpectedPostcondition requireFrontend() {
        if (this instanceof Frontend frontend) return frontend.expected();
        throw new IllegalStateException("gameplay expectation is not a frontend postcondition");
    }
    default FrontendGameplayExpectedPostcondition requireGameplayEntry() {
        if (this instanceof GameplayEntry entry) return entry.expected();
        throw new IllegalStateException("dedicated frontend to gameplay expectation required");
    }
    default LifecycleExpectedPostcondition requireLifecycleTerminal() {
        if (this instanceof LifecycleTerminal lifecycle) return lifecycle.expected();
        throw new IllegalStateException("dedicated lifecycle terminal expectation required");
    }
}
