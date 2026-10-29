package org.xar.ck3.control.application.action;

import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One immutable command contract. Origins never create submit or writer authority. */
public record ActionCommand(String actionId, CommandOrigin origin, G2Source source, String sessionId,
        OperationKey operation, OpportunityJson.Obj arguments, CommandExpectation expectation, Claims claims,
        Instant deadline, ProtocolRequestIdentity protocolIdentity) {
    /** Composed original construction request/result and candidate, distinct from the full Driver bound. */
    public static final int MAX_ARGUMENT_BYTES = 768 * 1024;
    public ActionCommand {
        StrictJson.require(actionId != null && actionId.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"), "bounded action ID required");
        Objects.requireNonNull(origin); Objects.requireNonNull(source); StrictJson.text(sessionId);
        StrictJson.require(!(origin instanceof CommandOrigin.Reconciliation || origin instanceof CommandOrigin.PhysicalStatusOnly), "read-only reconciliation or physical status can never construct or submit an ActionCommand");
        Objects.requireNonNull(operation); Objects.requireNonNull(arguments); Objects.requireNonNull(expectation);
        Objects.requireNonNull(claims); Objects.requireNonNull(deadline); Objects.requireNonNull(protocolIdentity);
        if (protocolIdentity instanceof ExplicitOriginalProtocolId explicit)
            StrictJson.require(origin instanceof CommandOrigin.Gameplay && explicit.contract().operation().equals(operation),
                    "explicit original protocol ID crossed its closed tool/origin/operation contract");
        StrictJson.require(origin.machineId().equals(source.machineId()) && expectation.origin().equals(origin)
                && expectation.source().equals(source), "command, expected origin and source must be identical");
        if (origin instanceof CommandOrigin.Frontend frontend) {
            StrictJson.require(frontend.identity().frontendSessionId().equals(sessionId), "frontend session drift");
            StrictJson.require(claims.armyIds().isEmpty() && claims.allyCharacterIds().isEmpty()
                    && claims.characterIds().isEmpty() && claims.commitmentKeys().isEmpty(), "frontend has no gameplay resource claims");
        }
        if (origin instanceof CommandOrigin.LifecycleTerminal lifecycle && !(expectation instanceof CommandExpectation.OperatorRebind)) {
            var expected = expectation.requireLifecycleTerminal();
            StrictJson.require(lifecycle.identity().sessionId().equals(sessionId) && expected.operation().key().equals(operation),
                    "lifecycle command changed its actual session or exact registered composite operation");
            StrictJson.require(claims.armyIds().isEmpty() && claims.allyCharacterIds().isEmpty()
                    && claims.characterIds().isEmpty() && claims.commitmentKeys().isEmpty(), "lifecycle command cannot borrow ordinary gameplay resource claims");
        }
        if (expectation instanceof CommandExpectation.OperatorRebind operator) {
            StrictJson.require(operation.value().equals(operator.expected().request().step())
                    && protocolIdentity instanceof ProtocolRequestIdentity.BodyDerived, "operator requires its exact original step and body-derived protocol identity");
            StrictJson.require(claims.armyIds().isEmpty() && claims.allyCharacterIds().isEmpty()
                    && claims.characterIds().isEmpty() && claims.commitmentKeys().isEmpty(), "operator has no ordinary resource claims");
        }
        byte[] originalArguments = DriverJson.encode(arguments);
        ProjectionJson.object(originalArguments, MAX_ARGUMENT_BYTES);
        DriverJson.object(originalArguments, MAX_ARGUMENT_BYTES);
    }
    /** Existing schemas retain the original implicit body-derived protocol identity. */
    public ActionCommand(String actionId, CommandOrigin origin, G2Source source, String sessionId,
            OperationKey operation, OpportunityJson.Obj arguments, CommandExpectation expectation, Claims claims, Instant deadline) {
        this(actionId, origin, source, sessionId, operation, arguments, expectation, claims, deadline, ProtocolRequestIdentity.BodyDerived.INSTANCE);
    }
    /** Existing gameplay callers keep their strict original observation and expected-postcondition constructor. */
    public ActionCommand(String actionId, ObservationIdentity before, G2Source source, String sessionId,
            OperationKey operation, OpportunityJson.Obj arguments, ExpectedPostcondition expected, Claims claims, Instant deadline) {
        this(actionId, new CommandOrigin.Gameplay(before), source, sessionId, operation, arguments,
                new CommandExpectation.Gameplay(expected), claims, deadline);
    }
    public ObservationIdentity before() { return origin.requireGameplay(); }
    public ExpectedPostcondition expected() { return expectation.requireGameplay(); }
    public LifecycleIdentity lifecycleBefore() { return origin.requireLifecycleTerminal(); }
    public LifecycleExpectedPostcondition lifecycleExpected() { return expectation.requireLifecycleTerminal(); }
}
