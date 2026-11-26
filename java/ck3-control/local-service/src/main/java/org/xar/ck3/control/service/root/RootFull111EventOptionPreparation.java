package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionIds;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RequestIds;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.events.RegisteredEventCore.Full111EventObservation;
import org.xar.ck3.control.application.planning.events.RegisteredEventCore.Full111EventSelection;
import org.xar.ck3.control.application.planning.events.RegisteredEventCore.Full111RenderedOption;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption.Target;
import org.xar.ck3.control.nativebridge.CurrentFull111EventRenderer;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Proposes from an archived renderer read, then acquires a private lease only for the canonical action. */
final class RootFull111EventOptionPreparation implements Full111EventSelection, ActionPorts.PreparationPort {
    static final OperationKey SELECT = new OperationKey(CurrentFull111EventOption.Action.SELECT.step());
    static final String CAPABILITY = CurrentFull111EventOption.Action.SELECT.capability();
    private static final Set<String> CAPABILITIES = Set.of(CoreFrame.CAPABILITY, CurrentFull111EventRenderer.CAPABILITY,
            CAPABILITY, CurrentFull111EventOption.Action.PREPARE.capability(),
            CurrentFull111EventOption.Action.QUERY_QUEUE.capability());
    private static final Set<String> ARGUMENTS = Set.of("renderer_original", "instance_id", "recipient_character_id",
            "definition_key", "authored_option_index");

    private final RootRuntimeContext context;
    private final NativeGameTransport transport;
    private final RootFull111EventRead rendererReads;

    RootFull111EventOptionPreparation(RootRuntimeContext context, NativeGameTransport transport,
            RootFull111EventRead rendererReads) {
        this.context = Objects.requireNonNull(context);
        this.transport = Objects.requireNonNull(transport);
        this.rendererReads = Objects.requireNonNull(rendererReads);
    }

    @Override public Optional<ActionCommand> propose(PlanningRequest request, Full111EventObservation observation,
            Full111RenderedOption option) {
        var seen = request.observations();
        if (!seen.actionSteps().contains(SELECT) || !seen.bridgeCapabilities().containsAll(CAPABILITIES))
            return Optional.empty();
        var ref = observation.renderer().orElseThrow().originalRead();
        var target = new Target(observation.instanceId(), request.before().frame().identity().player().intValueExact(),
                observation.definitionKey(), option.authoredOptionIndex());
        try {
            var same = context.borrowedSession();
            context.writer().requireSession(same);
            var renderer = renderer(context.archive().withSession(same), ref, target);
            var deadline = CurrentFull111EventOption.rendererDeadline(renderer);
            if (deadline.isAfter(request.deadline()) || !context.clock().instant().isBefore(deadline)) return Optional.empty();
            var encoded = StrictJson.object().put("instance_id", target.instanceId())
                    .put("recipient_character_id", target.recipientCharacterId()).put("definition_key", target.definitionKey())
                    .put("authored_option_index", target.authoredOptionIndex());
            encoded.set("renderer_original", ref.toJson());
            var args = OpportunityJson.object(DriverJson.fromNode(encoded), "Full111 selection arguments");
            var id = ActionIds.forDecision(request.sessionId(), request.before(), SELECT.value() + ":"
                    + ActionCodec.sha256(DriverJson.encode(args)));
            return Optional.of(new ActionCommand(id, request.before(), request.source(), request.sessionId(), SELECT, args,
                    RootFull111EventOptionEffects.expected(request, target), EventRuntimeInstaller.foregroundClaims(request), deadline));
        } catch (IOException | UncheckedIOException | ContractViolationException unavailable) {
            return Optional.empty();
        }
    }

    @Override public NativeRequest prepare(ActionCommand command) {
        throw new IllegalStateException("Full111 option preparation requires the canonical writer session");
    }

    @Override public NativeRequest prepare(Session same, ActionCommand command, String requestId) {
        requireProtocolIdentity(command);
        StrictJson.require(SELECT.equals(command.operation()) && RequestIds.forCommand(command).equals(requestId)
                && context.source().equals(command.source()), "Full111 option preparation changed its operation, source or request");
        var ref = rendererOriginal(command);
        try {
            context.writer().requireSession(same);
            var archive = context.archive().withSession(same);
            var target = target(command);
            var original = renderer(archive, ref, target);
            var acquired = transport.prepareFull111EventOption(command, original, target).orElseThrow(() ->
                    new ContractViolationException("The original Full111 renderer no longer qualifies a private selection lease"));
            var request = acquired.request();
            return new NativeRequest(request.step(), request.requiredCapability(), request.additionalFields(),
                    List.of(ref, archive.preserve(acquired.original())));
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            throw new ContractViolationException("Full111 selection preparation was interrupted", interrupted);
        } catch (IOException | UncheckedIOException unavailable) {
            throw new ContractViolationException("Original Full111 selection preparation is unavailable", unavailable);
        } finally {
            rendererReads.release(ref);
        }
    }

    static ExactRef rendererOriginal(ActionCommand command) {
        var ref = ExactRef.fromJson(arguments(command).get("renderer_original"));
        StrictJson.require(ref.bytes() > 0, "Full111 selection requires an original renderer read");
        return ref;
    }

    static Target target(ActionCommand command) {
        var args = arguments(command);
        return new Target((int) StrictJson.integer(args.get("instance_id"), 1, Integer.MAX_VALUE),
                (int) StrictJson.integer(args.get("recipient_character_id"), Integer.MIN_VALUE, Integer.MAX_VALUE),
                StrictJson.text(args.get("definition_key")), (int) StrictJson.integer(args.get("authored_option_index"), 0, 63));
    }

    private static ObjectNode arguments(ActionCommand command) {
        return StrictJson.object(StrictJson.parse(DriverJson.encode(command.arguments())), ARGUMENTS);
    }

    private static AckReceived renderer(ActionPorts.OutcomeArchive archive, ExactRef ref, Target target) throws IOException {
        if (!(archive.load(ref) instanceof AckReceived ack) || !ref.equals(archive.referenceOf(ack)))
            throw new IOException("The original Full111 renderer ACK is unavailable");
        var read = CurrentFull111EventRenderer.decodeOutcome(ack);
        var source = read.source();
        if (read.status() != CurrentFull111EventRenderer.Status.AVAILABLE || source.isEmpty()
                || !target.matchesSelectable(source.orElseThrow()) || source.orElseThrow().options().stream()
                        .filter(CurrentFull111EventRenderer.Option::widgetVisible).findFirst()
                        .filter(first -> first.authoredOptionIndex() == target.authoredOptionIndex()).isEmpty())
            throw new IOException("The original Full111 renderer does not qualify the first visible stock option");
        return ack;
    }
}
