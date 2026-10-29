package org.xar.ck3.control.application.planning.military;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedInteger;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedNull;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.commander.CommanderQuality;

/** Original native assignment normalization plus an independent current-commander read. */
public final class CommanderAssignmentPostcondition implements ActionPorts.PostconditionPort {
    public static final String OBSERVER_SCHEMA = "xar.java.commander-assignment-independent-readback/v1";
    private static final Set<String> ARGUMENTS = Set.of(
            "army_id", "commander_character_id", "native_carmy_id", "owner_character_id", "date_raw");
    private static final FieldKey VERIFIED = new FieldKey("verified");
    private static final FieldKey ARMY = new FieldKey("army_id");
    private static final FieldKey NATIVE_ARMY = new FieldKey("native_carmy_id");
    private static final FieldKey OWNER = new FieldKey("owner_character_id");
    private static final FieldKey COMMANDER = new FieldKey("commander_character_id");
    private static final FieldKey DATE = new FieldKey("date_raw");

    public record Arguments(BigInteger army, BigInteger character, BigInteger nativeArmy, BigInteger owner, BigInteger date) {
        public Arguments {
            id(army); id(character); id(nativeArmy); id(owner); Objects.requireNonNull(date);
            OpportunityJson.require(nativeArmy.signum()>0&&owner.signum()>0,"private CArmy and owner CharacterID must remain positive");
        }
        public String step() { return "assign-army-commander-v1-army-" + army + "-to-character-" + character; }
    }
    public sealed interface CurrentFrame permits Current, ReconciliationCurrent, FrameUnavailable { }
    public record Current(CommanderObservationCollector.ObservedInput input) implements CurrentFrame {
        public Current {Objects.requireNonNull(input);}
        public Current(PlanningRequest request){this(CommanderObservationCollector.ObservedInput.of(request));}
    }
    public record FrameUnavailable(String reason) implements CurrentFrame { public FrameUnavailable { StrictJson.text(reason); } }
    public record ReconciliationCurrent(CommanderReconciliationCollector.Input input,java.time.Instant deadline) implements CurrentFrame {
        public ReconciliationCurrent {Objects.requireNonNull(input);Objects.requireNonNull(deadline);}
    }
    @FunctionalInterface public interface CurrentFramePort { CurrentFrame observe(ActionCommand original); }
    /** Root registers a fresh collector on the same endpoint for this independently observed frame. */
    @FunctionalInterface public interface CurrentCommanderPort {
        PlanningReadResult<CommanderObservationCollector.Observation> read(CommanderObservationCollector.ObservedInput current, int armyId);
    }
    @FunctionalInterface public interface ReconciliationCommanderPort {
        PlanningReadResult<CommanderObservationCollector.Observation> read(CommanderReconciliationCollector.Input input,int armyId,java.time.Instant deadline);
    }
    private final CurrentFramePort frames;
    private final CurrentCommanderPort commanders;
    private final ActionPorts.OutcomeArchive archive;
    private final ReconciliationCommanderPort reconciliation;

    public CommanderAssignmentPostcondition(CurrentFramePort frames, CurrentCommanderPort commanders, ActionPorts.OutcomeArchive archive) {
        this(frames,commanders,archive,(input,army,deadline)->new PlanningReadResult.Unavailable<>("commander reconciliation read is not installed",java.util.Optional.empty()));
    }
    public CommanderAssignmentPostcondition(CurrentFramePort frames, CurrentCommanderPort commanders, ActionPorts.OutcomeArchive archive,
            ReconciliationCommanderPort reconciliation) {
        this.frames = Objects.requireNonNull(frames); this.commanders = Objects.requireNonNull(commanders);
        this.archive = Objects.requireNonNull(archive);
        this.reconciliation=Objects.requireNonNull(reconciliation);
    }
    public static Arguments arguments(OpportunityJson.Obj value) {
        OpportunityJson.require(value.members().keySet().equals(ARGUMENTS), "exact commander assignment argument fields required");
        return new Arguments(integer(value, "army_id"), integer(value, "commander_character_id"),
                integer(value, "native_carmy_id"), integer(value, "owner_character_id"), integer(value, "date_raw"));
    }
    public static ExpectedPostcondition expected(PlanningRequest request, OpportunityJson.Obj rawArguments) {
        Arguments a = arguments(rawArguments);
        OpportunityJson.require(a.date().equals(request.before().frame().identity().dateRaw()), "commander expected date differs");
        return new ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION, request.before(), request.source(), OBSERVER_SCHEMA,
                List.of(new ExpectedBoolean(VERIFIED, true), new ExpectedInteger(ARMY, a.army()),
                        new ExpectedInteger(NATIVE_ARMY, a.nativeArmy()), new ExpectedInteger(OWNER, a.owner()),
                        new ExpectedInteger(COMMANDER, a.character()), new ExpectedInteger(DATE, a.date())));
    }
    private static ExpectedPostcondition expected(ActionCommand command, Arguments a) {
        return new ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION, command.before(), command.source(), OBSERVER_SCHEMA,
                List.of(new ExpectedBoolean(VERIFIED, true), new ExpectedInteger(ARMY, a.army()),
                        new ExpectedInteger(NATIVE_ARMY, a.nativeArmy()), new ExpectedInteger(OWNER, a.owner()),
                        new ExpectedInteger(COMMANDER, a.character()), new ExpectedInteger(DATE, a.date())));
    }
    public static Claims claims(OpportunityJson.Obj rawArguments) {
        Arguments a = arguments(rawArguments);
        // Native character ID zero is valid; the commitment also isolates that ID without inventing a positive ID.
        return new Claims(Set.of(a.army()), Set.of(), a.character().signum() > 0 ? Set.of(a.character()) : Set.of(),
                Set.of("commander-character:" + a.character()));
    }
    public static NativeRequest prepare(ActionCommand command) {
        Arguments a = arguments(command.arguments());
        OpportunityJson.require(command.operation().value().equals(a.step())
                && command.before().frame().identity().dateRaw().equals(a.date())
                && command.expected().equals(expected(command, a)) && command.claims().equals(claims(command.arguments())), "commander action/expected/source fields disagree");
        return new NativeRequest(a.step(), CommanderQuality.ASSIGN_CAPABILITY,
                new RawJson(new byte[] {'{', '}'}));
    }

    @Override public ActionPorts.PostconditionResult observe(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch) {
        if (!(dispatch instanceof NativeActionPort.AckReceived) && !(dispatch instanceof NativeActionPort.Unknown))
            return new ActionPorts.Pending("commander submission has no unresolved or acknowledged write to observe", List.of());
        ExactRef submitted = archive.preserve(dispatch);
        try {
            Arguments a = arguments(command.arguments());
            OpportunityJson.require(attempt.requestId().equals(dispatch.requestId())
                    && attempt.preparedRequest().equals(prepare(command)), "assignment outcome differs from its original prepared attempt");
            Assignment assignment;
            if (dispatch instanceof NativeActionPort.AckReceived ack) {
                if (!ack.nativeOk() || ack.originalResultToken().isEmpty())
                    return pending("commander ACK does not establish native assignment status", submitted);
                OpportunityJson.Obj result = object(OpportunityJson.parse(ack.originalResultToken().orElseThrow().bytes()), "assignment result");
                assignment = normalize(result, command, a);
            } else {
                // UNKNOWN permits independent observation only; no submission or ACK success is inferred.
                assignment = new Assignment("unknown", a.nativeArmy(), a.owner());
            }
            if (assignment.status().equals("unavailable") || assignment.status().equals("rejected")) {
                return new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),
                        "native commander assignment " + assignment.status(), submitted));
            }
            CurrentFrame fresh = frames.observe(command);
            if(fresh instanceof ReconciliationCurrent actual) {
                requirePending(command,attempt,actual.input().identity());
                var read=reconciliation.read(actual.input(),a.army().intValueExact(),actual.deadline());
                if(read instanceof PlanningReadResult.Unavailable<CommanderObservationCollector.Observation> missing)
                    return pending("independent reconciliation commander read unavailable: "+missing.reason(),submitted);
                if(!(read instanceof PlanningReadResult.Known<CommanderObservationCollector.Observation> known))return pending("unrecognized reconciliation commander read",submitted);
                archive.preserve(known.receipt().original());archive.preserveRead(known.receipt());
                return projectReconciliation(command,attempt,dispatch,actual.input(),known.receipt(),archive);
            }
            if(dispatch instanceof NativeActionPort.Unknown)return pending("UNKNOWN commander outcome requires the installed canonical reconciliation scope",submitted);
            if (!(fresh instanceof Current current)) return pending(
                    fresh instanceof FrameUnavailable missing ? missing.reason() : "unrecognized current commander frame", submitted);
            var now = current.input();
            if (!samePlayerAndDate(command, now, a)) return pending(
                    "commander readback crossed the paused Game/session/player/date context", submitted);
            var read = commanders.read(now, a.army().intValueExact());
            if (read instanceof PlanningReadResult.Unavailable<CommanderObservationCollector.Observation> unavailable)
                return pending("independent commander read unavailable: " + unavailable.reason(), submitted);
            if (!(read instanceof PlanningReadResult.Known<CommanderObservationCollector.Observation> known))
                return pending("unrecognized independent commander read", submitted);
            var receipt = known.receipt();
            if (receipt.requestId().equals(attempt.requestId()) || !receipt.request().before().equals(now.before())
                    || !receipt.request().source().equals(command.source())
                    || !receipt.request().sessionId().equals(command.sessionId()))
                return pending("commander read is not an independent original current-frame request", submitted);
            archive.preserve(receipt.original());archive.preserveRead(receipt);
            return project(command,attempt,dispatch,now,receipt,archive);
        } catch (IllegalArgumentException|IllegalStateException malformed) {
            return pending("commander assignment/readback contract rejected: " + malformed.getMessage(), submitted);
        }
    }

    /** The live observer and locked archive verifier run this same original-native projection. */
    static ActionPorts.PostconditionResult project(ActionCommand command,ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch,CommanderObservationCollector.ObservedInput now,
            PlanningReadReceipt receipt,ActionPorts.OutcomeArchive archive) {
            Arguments a=arguments(command.arguments());
            OpportunityJson.require(!(dispatch instanceof NativeActionPort.Unknown),"UNKNOWN commander archive requires its actual reconciliation read origin");
            OpportunityJson.require(attempt.requestId().equals(dispatch.requestId())&&attempt.preparedRequest().equals(prepare(command)),"archived commander original attempt changed");
            ExactRef submitted=archive.referenceOf(dispatch);
            Assignment assignment;
            if(dispatch instanceof NativeActionPort.AckReceived ack) {
                OpportunityJson.require(ack.nativeOk()&&ack.originalResultToken().isPresent(),"original commander ACK unavailable");
                assignment=normalize(object(OpportunityJson.parse(ack.originalResultToken().orElseThrow().bytes()),"assignment result"),command,a);
            } else {
                OpportunityJson.require(dispatch instanceof NativeActionPort.Unknown,"original commander dispatch is not ACK or UNKNOWN");
                assignment=new Assignment("unknown",a.nativeArmy(),a.owner());
            }
            if(assignment.status().equals("unavailable")||assignment.status().equals("rejected"))
                return new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),"native commander assignment "+assignment.status(),submitted));
            OpportunityJson.require(samePlayerAndDate(command,now,a)&&!receipt.requestId().equals(attempt.requestId())
                    &&receipt.request().before().equals(now.before())&&receipt.request().source().equals(command.source())
                    &&receipt.request().sessionId().equals(command.sessionId()),"archived commander read crossed original current context");
            var admitted = CommanderObservationCollector.admit(now, a.army().intValueExact(), receipt);
            return projectAdmitted(command,a,assignment,admitted,receipt,archive,submitted,receipt.after().binding().observed());
    }
    static void requirePending(ActionCommand command,ActionState.Attempt attempt,org.xar.ck3.control.application.action.ReconciliationIdentity identity) {
        var pending=identity.pending();
        OpportunityJson.require(pending.actionId().equals(command.actionId())&&pending.bodySha256().equals(org.xar.ck3.control.application.action.ActionCodec.bodySha256(command))
                &&pending.requestId().equals(attempt.requestId())&&pending.originalBefore().equals(command.before())
                &&identity.source().equals(command.source())&&identity.sessionId().equals(command.sessionId()),
                "commander reconciliation belongs to another canonical action or prepared attempt");
    }
    static ActionPorts.PostconditionResult projectReconciliation(ActionCommand command,ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch,CommanderReconciliationCollector.Input input,PlanningReadReceipt receipt,ActionPorts.OutcomeArchive archive) {
        var a=arguments(command.arguments());requirePending(command,attempt,input.identity());
        OpportunityJson.require(attempt.requestId().equals(dispatch.requestId())&&attempt.preparedRequest().equals(prepare(command))
                &&!receipt.requestId().equals(attempt.requestId()),"commander reconciliation is not an independent original read");
        var factual=input.identity().factual();
        var now=new CommanderObservationCollector.ObservedInput(factual,input.identity().source(),input.identity().sessionId(),receipt.request().deadline(),input.snapshot(),Set.of(CommanderQuality.QUERY_CAPABILITY));
        OpportunityJson.require(samePlayerAndDate(command,now,a),"commander reconciliation crossed original living player/date");
        Assignment assignment;
        if(dispatch instanceof NativeActionPort.AckReceived ack) {
            OpportunityJson.require(ack.nativeOk()&&ack.originalResultToken().isPresent(),"original commander ACK unavailable");
            assignment=normalize(object(OpportunityJson.parse(ack.originalResultToken().orElseThrow().bytes()),"assignment result"),command,a);
        }else{OpportunityJson.require(dispatch instanceof NativeActionPort.Unknown,"commander reconciliation requires original ACK or UNKNOWN");assignment=new Assignment("unknown",a.nativeArmy(),a.owner());}
        OpportunityJson.require(!Set.of("unavailable","rejected").contains(assignment.status()),"rejected assignment does not grant applied reconciliation");
        var admitted=CommanderReconciliationCollector.admit(new CommanderReconciliationCollector.Selection(input,a.army().intValueExact()),receipt);
        return projectAdmitted(command,a,assignment,admitted,receipt,archive,archive.referenceOf(dispatch),factual);
    }
    private static ActionPorts.PostconditionResult projectAdmitted(ActionCommand command,Arguments a,Assignment assignment,
            CommanderObservationCollector.Observation admitted,PlanningReadReceipt receipt,ActionPorts.OutcomeArchive archive,ExactRef submitted,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity factual) {
            var proposal = admitted.proposal(); var context = proposal.context();
            Integer currentId = context.current().characterId() == null ? null : context.current().characterId().value();
            Integer nativeId = context.nativeArmyId() == null ? null : context.nativeArmyId().value();
            Integer ownerId = context.ownerCharacterId() == null ? null : context.ownerCharacterId().value();
            boolean contextMatches = BigInteger.valueOf(context.armyId().value()).equals(a.army())
                    && nativeId != null && ownerId != null
                    && BigInteger.valueOf(nativeId).equals(assignment.nativeArmy())
                    && BigInteger.valueOf(ownerId).equals(assignment.owner())
                    && assignment.nativeArmy().equals(a.nativeArmy()) && assignment.owner().equals(a.owner())
                    && proposal.frame().dateRaw().equals(a.date());
            boolean commanderMatches = context.current().status() == CommanderQuality.RoleStatus.AVAILABLE
                    && currentId != null && BigInteger.valueOf(currentId).equals(a.character());
            List<ExpectedValue> actual = new ArrayList<>();
            actual.add(new ExpectedBoolean(VERIFIED, contextMatches && commanderMatches));
            actual.add(new ExpectedInteger(ARMY, BigInteger.valueOf(context.armyId().value())));
            actual.add(nullable(NATIVE_ARMY, nativeId)); actual.add(nullable(OWNER, ownerId));
            actual.add(nullable(COMMANDER, currentId)); actual.add(new ExpectedInteger(DATE, proposal.frame().dateRaw()));
            ExactRef independent = archive.referenceOf(receipt.original());
            ExactRef independentRead = archive.readReferenceOf(receipt);
            return new ActionPorts.EffectObserved(new ActionState.EffectObservation(
                    factual, receipt.after().binding().source(), command.sessionId(),
                    OBSERVER_SCHEMA, actual, receipt.requestId(), receipt.after().binding().observedAt(), independent,
                    List.of(submitted, independentRead)));
    }

    private record Assignment(String status, BigInteger nativeArmy, BigInteger owner) { }
    static void requireRejection(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,
            ActionState.Rejected proposed,ActionPorts.OutcomeArchive archive) {
        OpportunityJson.require(attempt.preparedRequest().equals(prepare(command))&&attempt.requestId().equals(dispatch.requestId())
                &&dispatch instanceof NativeActionPort.AckReceived,"commander rejection original attempt unavailable");
        var ack=(NativeActionPort.AckReceived)dispatch;
        OpportunityJson.require(ack.nativeOk()&&ack.originalResultToken().isPresent(),"commander rejection original result unavailable");
        Assignment decoded=normalize(object(OpportunityJson.parse(ack.originalResultToken().orElseThrow().bytes()),"assignment result"),command,arguments(command.arguments()));
        OpportunityJson.require(Set.of("unavailable","rejected").contains(decoded.status())&&proposed.equals(new ActionState.Rejected(attempt.requestId(),
                "native commander assignment "+decoded.status(),archive.referenceOf(dispatch))),"commander proposed rejection differs from actual native status/identity");
    }
    private static Assignment normalize(OpportunityJson.Obj root, ActionCommand command, Arguments a) {
        OpportunityJson.require(a.step().equals(OpportunityJson.text(root.get("step"), "step"))
                && integer(root, "snapshot_revision").equals(command.before().frame().identity().nativeRevision())
                && integer(root, "date_raw").equals(a.date()), "assignment result crossed its submitted native frame");
        boolean accepted = OpportunityJson.bool(root.get("accepted"), "accepted");
        OpportunityJson.Obj value = object(root.get("army_commander_assignment"), "army_commander_assignment");
        String schema = OpportunityJson.text(value.get("schema"), "assignment schema");
        OpportunityJson.require(Set.of("ck3_12003_army_commander_assignment_v1", "ck3_12004_army_commander_assignment_v1").contains(schema),
                "unsupported original commander assignment schema");
        String status = OpportunityJson.text(value.get("status"), "assignment status");
        OpportunityJson.require(Set.of("unavailable", "rejected", "submitted", "already_assigned").contains(status)
                && integer(value, "army_id").equals(a.army())
                && integer(value, "requested_commander_character_id").equals(a.character()), "assignment result role/identity differs");
        BigInteger nativeArmy = nullableId(value.get("native_carmy_id")), owner = nullableId(value.get("owner_character_id"));
        nullableId(value.get("prior_commander_character_id"));
        boolean eligibility = OpportunityJson.bool(value.get("final_eligibility_observable"), "final_eligibility_observable");
        boolean validity = OpportunityJson.bool(value.get("native_command_validation_observable"), "native_command_validation_observable");
        Boolean canAssign = nullableBool(value.get("can_assign")), valid = nullableBool(value.get("native_command_valid"));
        OpportunityJson.require(eligibility == (canAssign != null) && validity == (valid != null),
                "assignment eligibility/command validity observation differs");
        boolean submitted = OpportunityJson.bool(value.get("command_submitted"), "command_submitted");
        boolean pending = OpportunityJson.bool(value.get("verification_pending"), "verification_pending");
        OpportunityJson.require(submitted == status.equals("submitted") && pending == status.equals("submitted"),
                "assignment submission and verification flags disagree");
        OpportunityJson.Value reason = value.get("unavailable_reason");
        OpportunityJson.require(reason == null || reason == OpportunityJson.Nil.INSTANCE || reason instanceof OpportunityJson.Text,
                "assignment unavailable reason must be text or null");
        OpportunityJson.require(!submitted || accepted && nativeArmy != null && owner != null
                && Boolean.TRUE.equals(canAssign) && validity && Boolean.TRUE.equals(valid),
                "submitted commander assignment lacks validated native context");
        OpportunityJson.require(!Set.of("submitted","already_assigned").contains(status)||nativeArmy!=null&&nativeArmy.signum()>0&&owner!=null&&owner.signum()>0,
                "available commander assignment lacks positive native CArmy/owner identity");
        return new Assignment(status, nativeArmy, owner);
    }
    private static boolean samePlayerAndDate(ActionCommand command, PlanningRequest now, Arguments a) {
        return samePlayerAndDate(command,CommanderObservationCollector.ObservedInput.of(now),a);
    }
    private static boolean samePlayerAndDate(ActionCommand command,CommanderObservationCollector.ObservedInput now,Arguments a) {
        return OpportunityJson.bool(now.snapshot().get("paused"),"paused") && now.before().machineId().equals(command.before().machineId())
                && now.before().game().equals(command.before().game()) && now.source().equals(command.source())
                && now.sessionId().equals(command.sessionId())
                && now.before().frame().episodeRunId().equals(command.before().frame().episodeRunId())
                && now.before().frame().identity().player().equals(command.before().frame().identity().player())
                && now.before().frame().identity().dateRaw().equals(a.date());
    }
    private static ExpectedValue nullable(FieldKey key, Integer id) {
        return id == null ? new ExpectedNull(key) : new ExpectedInteger(key, BigInteger.valueOf(id));
    }
    private static ActionPorts.Pending pending(String reason, ExactRef evidence) { return new ActionPorts.Pending(reason, List.of(evidence)); }
    private static OpportunityJson.Obj object(OpportunityJson.Value value, String name) { return OpportunityJson.object(value, name); }
    private static BigInteger integer(OpportunityJson.Obj object, String key) { return OpportunityJson.integer(object.get(key), key); }
    private static void id(BigInteger value) {
        OpportunityJson.require(value != null && value.signum() >= 0 && value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0,
                "nonnegative full native int32 identity required");
    }
    private static BigInteger nullableId(OpportunityJson.Value value) {
        if (value == null || value == OpportunityJson.Nil.INSTANCE) return null;
        BigInteger id = OpportunityJson.integer(value, "optional native identity"); id(id); return id;
    }
    private static Boolean nullableBool(OpportunityJson.Value value) {
        return value == null || value == OpportunityJson.Nil.INSTANCE ? null : OpportunityJson.bool(value, "optional native boolean");
    }
}
