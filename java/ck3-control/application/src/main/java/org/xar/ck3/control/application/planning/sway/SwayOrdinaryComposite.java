package org.xar.ck3.control.application.planning.sway;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService;

/** The actual registered parent. Native Start alone uses Children; full ordinary continuation belongs to Root after settlement. */
public final class SwayOrdinaryComposite implements CompositeActionPort {
    public static final String HANDLER = "ordinary-sway-canonical-scheduler/v1";
    public static final String OBSERVER = "xar.java.sway-scheduler-terminal/v1";
    private final SwayOrdinaryExecutor executor; private final SwayCanonicalDomain domain; private final Supplier<ContinuityStorePort.Session> sessions;
    public SwayOrdinaryComposite(SwayOrdinaryExecutor executor, SwayCanonicalDomain domain, Supplier<ContinuityStorePort.Session> sessions) { this.executor = Objects.requireNonNull(executor); this.domain = Objects.requireNonNull(domain); this.sessions = Objects.requireNonNull(sessions); }
    @Override public String handlerId() { return HANDLER; }
    @Override public boolean supports(OperationKey operation) { return OrdinarySwayPolicy.OPERATION.equals(operation); }
    @Override public void validate(ActionCommand parent) {
        StrictJson.require(supports(parent.operation()) && parent.expected().observerSchema().equals(OBSERVER) && parent.expected().before().equals(parent.before()) && parent.expected().source().equals(parent.source()), "ordinary Sway parent contract/source differs");
        OrdinarySwayPolicy.restoreStaged(parent);
    }
    public static ExpectedPostcondition expected(PlanningRequest request, OrdinarySwayService.Staged staged) {
        Objects.requireNonNull(staged); return new ExpectedPostcondition(1, request.before(), request.source(), OBSERVER, List.of(new ExpectedBoolean(new FieldKey("sway.scheduler_completed"), true)));
    }
    @Override public ActionPorts.PostconditionResult run(ActionCommand parent, Children children) {
        validate(parent);
        try { var actual = executor.execute(parent, children); return actual.completion().<ActionPorts.PostconditionResult>map(ActionPorts.SwaySchedulerObserved::new).orElseGet(() -> new ActionPorts.Pending("actual scheduler publication or independent final proof unavailable", actual.originalRun().stream().toList())); }
        catch (ReadPublicationRequiredException required) { throw required; }
        catch (OrdinarySwayService.Unavailable | IllegalArgumentException | IllegalStateException failure) { return new ActionPorts.Pending(message(failure), List.of()); }
    }
    @Override public ActionPorts.PostconditionResult observe(ActionCommand parent, CompositeExecution retained) {
        validate(parent);
        try { return executor.observe(parent, retained).<ActionPorts.PostconditionResult>map(ActionPorts.SwaySchedulerObserved::new).orElseGet(() -> new ActionPorts.Pending("no actual SchedulerSaved event for retained original parent; no retry permission", List.of())); }
        catch (ReadPublicationRequiredException required) { throw required; }
        catch (OrdinarySwayService.Unavailable | IllegalArgumentException | IllegalStateException failure) { return new ActionPorts.Pending(message(failure), List.of()); }
    }
    public NativeRecordedEvidenceVerifier.Binding recorded(ExactRef implementation) {
        return new NativeRecordedEvidenceVerifier.Binding(OrdinarySwayPolicy.OPERATION, implementation, (head, proposed, sameArchive) -> {
            validate(proposed.command()); StrictJson.require(proposed.state() instanceof ActionState.CompositeSettled settled && settled.settlement() instanceof ActionState.SwaySchedulerCompleted, "ordinary Sway requires its dedicated scheduler terminal");
            var settled = (ActionState.CompositeSettled)proposed.state(); var proof = ((ActionState.SwaySchedulerCompleted)settled.settlement()).proof();
            try { var session = Objects.requireNonNull(sessions.get()); StrictJson.require(session.head().digest().equals(head.digest()) && session.head().documents().equals(head.documents()), "Sway recorded verifier escaped actual original writer head"); domain.verifySchedulerCompleted(session, proposed.command(), settled.execution(), proof); StrictJson.require(session.head().digest().equals(head.digest()), "Sway read-only recorded verifier changed the original writer"); }
            catch (IOException failure) { throw new UncheckedIOException(failure); }
        });
    }
    private static String message(Exception failure) { return failure.getMessage() == null || failure.getMessage().isBlank() ? failure.getClass().getSimpleName() : failure.getMessage(); }
}
