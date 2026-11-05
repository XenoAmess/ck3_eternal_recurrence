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
public final class SwayOrdinaryComposite implements CompositeActionPort.ZeroGameplayBeforeChildren {
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
    /** Unissued DATA only. Actual no-write authority also requires this installed domain's historical proof. */
    public static void requireNoGameplayWriteData(ActionCommand parent, CompositeExecution retained) {
        Objects.requireNonNull(parent);Objects.requireNonNull(retained);
        StrictJson.require(OrdinarySwayPolicy.OPERATION.equals(parent.operation())
                &&parent.expected().observerSchema().equals(OBSERVER)
                &&parent.expected().before().equals(parent.before())&&parent.expected().source().equals(parent.source())
                &&HANDLER.equals(retained.handlerId()),"no-write Sway retains its original exact parent/source/handler");
        OrdinarySwayPolicy.restoreStaged(parent);
        var wire=StrictJson.parse(ActionCodec.encodeCommand(parent),ActionCodec.MAX_COMMAND_BYTES);
        var arguments=wire.path("arguments");var decision=arguments.path("decision");
        StrictJson.require("xar.java-ordinary-sway-command/v1".equals(arguments.path("schema").asText())
                &&"query_selected_target".equals(decision.path("job").asText())
                &&decision.path("submit_allowed").isBoolean()&&!decision.path("submit_allowed").booleanValue()
                &&!retained.startedAt().isAfter(parent.deadline()),"only the original read-only unstarted Sway query may close without gameplay writes");
        new CompositeNoGameplayWriteObservation(parent.actionId(),ActionCodec.bodySha256(parent),retained).validate(parent,retained);
    }
    @Override public void requireNoGameplayWrite(ActionCommand parent, CompositeExecution retained) {
        requireNoGameplayWriteData(parent,retained);
        try {
            var same=Objects.requireNonNull(sessions.get());var head=same.head();
            domain.requireUnstartedScheduler(same,parent,retained);
            StrictJson.require(same.head().digest().equals(head.digest())&&same.head().documents().equals(head.documents()),
                    "Sway no-write observation changed its original writer head/documents");
        } catch(IOException failure) {throw new OrdinarySwayService.Unavailable("actual Sway no-write history unavailable: "+failure.getMessage());}
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
        try {
            var completed=executor.observe(parent,retained);
            if(completed.isPresent())return new ActionPorts.SwaySchedulerObserved(completed.orElseThrow());
            requireNoGameplayWrite(parent,retained);
            return new ActionPorts.CompositeNoGameplayWriteObserved(new CompositeNoGameplayWriteObservation(parent.actionId(),ActionCodec.bodySha256(parent),retained));
        }
        catch (ReadPublicationRequiredException required) { throw required; }
        catch (OrdinarySwayService.Unavailable | IllegalArgumentException | IllegalStateException failure) { return new ActionPorts.Pending(message(failure), List.of()); }
    }
    public NativeRecordedEvidenceVerifier.Binding recorded(ExactRef implementation) {
        return new NativeRecordedEvidenceVerifier.Binding(OrdinarySwayPolicy.OPERATION, implementation, (head, proposed, sameArchive) -> {
            if(proposed.state() instanceof ActionState.CompositeSettled noWrite
                    &&noWrite.settlement() instanceof ActionState.CompositeNoGameplayWrite terminal) {
                terminal.observation().validate(proposed.command(),noWrite.execution());
                try {
                    var same=Objects.requireNonNull(sessions.get());
                    StrictJson.require(same.head().digest().equals(head.digest())&&same.head().documents().equals(head.documents()),
                            "Sway no-write cold verifier escaped the actual original writer head");
                    requireNoGameplayWrite(proposed.command(),noWrite.execution());
                    StrictJson.require(same.head().digest().equals(head.digest())&&same.head().documents().equals(head.documents()),
                            "Sway no-write cold verifier changed its actual original writer");
                } catch(IOException failure) {throw new UncheckedIOException(failure);}
                return;
            }
            validate(proposed.command()); StrictJson.require(proposed.state() instanceof ActionState.CompositeSettled settled && settled.settlement() instanceof ActionState.SwaySchedulerCompleted, "ordinary Sway requires its dedicated scheduler terminal");
            var settled = (ActionState.CompositeSettled)proposed.state(); var proof = ((ActionState.SwaySchedulerCompleted)settled.settlement()).proof();
            try { var session = Objects.requireNonNull(sessions.get()); StrictJson.require(session.head().digest().equals(head.digest()) && session.head().documents().equals(head.documents()), "Sway recorded verifier escaped actual original writer head"); domain.verifySchedulerCompleted(session, proposed.command(), settled.execution(), proof); StrictJson.require(session.head().digest().equals(head.digest()), "Sway read-only recorded verifier changed the original writer"); }
            catch (IOException failure) { throw new UncheckedIOException(failure); }
        });
    }
    private static String message(Exception failure) { return failure.getMessage() == null || failure.getMessage().isBlank() ? failure.getClass().getSimpleName() : failure.getMessage(); }
}
