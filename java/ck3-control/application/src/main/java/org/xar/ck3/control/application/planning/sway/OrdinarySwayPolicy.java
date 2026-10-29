package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule;
import org.xar.ck3.control.vanilla.schemesway.SwayScheduleWire;

/** Actual ordinary Sway staging adapter. Proposal construction never dispatches the composite. */
public final class OrdinarySwayPolicy implements OrdinaryPolicy {
    public static final OperationKey OPERATION = new OperationKey(OrdinarySwayService.STEP);
    public static final String ARGUMENT_SCHEMA = "xar.java-ordinary-sway-command/v1";
    private final ExactRef source;
    private final CopiedSource collector;
    private final CompositePostcondition postcondition;
    private final OrdinarySwayService service = new OrdinarySwayService();

    /** Reads a frozen planning view; native reading uses the sole admitted PlanningReadPort outside this leaf. */
    @FunctionalInterface public interface CopiedSource { CapturedView collect(PlanningRequest request); }
    /** The sole composite dispatcher supplies its actual observer contract, not a job-echo or ACK condition. */
    @FunctionalInterface public interface CompositePostcondition {
        ExpectedPostcondition expected(PlanningRequest request, OrdinarySwayService.Staged staged);
    }
    public record CapturedView(ObservationIdentity origin, Optional<Root> root,
            OrdinarySwayService.Capabilities capabilities, OrdinarySwayService.InputPort inputs) {
        public CapturedView {
            Objects.requireNonNull(origin); Objects.requireNonNull(root);
            Objects.requireNonNull(capabilities); Objects.requireNonNull(inputs);
        }
    }
    public OrdinarySwayPolicy(ExactRef implementationSource, CopiedSource collector, CompositePostcondition postcondition) {
        source = Objects.requireNonNull(implementationSource); require(source.bytes() > 0, "admitted policy source pin required");
        this.collector = Objects.requireNonNull(collector); this.postcondition = Objects.requireNonNull(postcondition);
    }
    @Override public PlanningStage stage() { return PlanningStage.ORDINARY_SWAY; }
    @Override public ExactRef implementationSource() { return source; }

    @Override public OrdinaryPolicy.Decision evaluate(PlanningRequest request, Draft previous) {
        Objects.requireNonNull(request); Objects.requireNonNull(previous);
        if (previous.command().isEmpty() || !previous.command().orElseThrow().operation().value().equals("life-advance")) {
            return new Keep("ordinary Sway preserves the selected non-life-advance step");
        }
        OrdinarySwayService.StageResult result;
        try {
            CapturedView captured = collector.collect(request);
            if (!captured.origin().equals(request.before())) return new Keep("ordinary Sway captured frame changed");
            Frame frame = frame(request);
            var input = new OrdinarySwayService.Captured(request.source(),
                    new OrdinarySwayService.Wrapper(request.before().frame().snapshotId(), request.before().frame().revision()),
                    Step.LIFE_ADVANCE, Optional.of(frame), captured.root(), captured.capabilities());
            result = service.stage(input, captured.inputs());
        } catch (OrdinarySwayService.Unavailable | IllegalArgumentException failure) {
            return new Keep("ordinary Sway optional inputs unavailable: " + failure.getMessage());
        }
        if (result.staged().isEmpty()) return new Keep("ordinary Sway " + result.reason().name().toLowerCase(Locale.ROOT));
        if (!request.observations().actionSteps().contains(OPERATION)) {
            return new Keep("ordinary Sway composite is not registered for this observed frame");
        }
        var staged = result.staged().orElseThrow();
        ExpectedPostcondition expected = postcondition.expected(request, staged);
        if (expected == null || !expected.before().equals(request.before()) || !expected.source().equals(request.source())) {
            return new Stop(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN,
                    "ordinary Sway composite postcondition is not bound to this frame and source");
        }
        OpportunityJson.Obj arguments = arguments(staged);
        Set<BigInteger> characters = new HashSet<>(); characters.add(BigInteger.valueOf(staged.frame().actorCharacterId()));
        staged.decision().targetCharacterId().ifPresent(value -> characters.add(BigInteger.valueOf(value)));
        Set<String> commitments = new HashSet<>(); commitments.add("ordinary-sway-schedule:" + staged.frame().actorCharacterId());
        staged.decision().actionId().ifPresent(value -> commitments.add("sway-original:" + value));
        Claims claims = new Claims(Set.of(), Set.of(), characters, commitments);
        String id = "ordinary-sway-" + sha((source.sha256() + request.before() + request.sessionId() + expected)
                .getBytes(StandardCharsets.UTF_8), OpportunityJson.encode(arguments)).substring(0, 40);
        ActionCommand command = new ActionCommand(id, request.before(), request.source(), request.sessionId(),
                OPERATION, arguments, expected, claims, request.deadline());
        // Every optional job may reach executeFreshOrdinary; none is mislabeled as a read-only dispatch.
        return new Replace(new Draft("ordinary-sway-java-v1", "ordinary-sway",
                staged.decision().reason().name().toLowerCase(Locale.ROOT), Kind.ORDINARY, Optional.of(command),
                Purpose.WORLD_ACTION, Optional.empty(), arguments), "current ordinary Sway job staged");
    }

    /** Original project_ordinary_sway_input_v1 root projection; no native query or storage read. */
    public static CapturedView project(ObservationIdentity origin, OpportunityJson.Value rootResult,
            OrdinarySwayService.Capabilities capabilities, OrdinarySwayService.InputPort inputs) {
        Optional<Root> root = Optional.empty();
        if (rootResult instanceof OpportunityJson.Obj result && result.get("campaign_root_context") instanceof OpportunityJson.Obj value) {
            var ids = value.get("direct_landed_vassal_character_ids");
            Optional<List<Long>> frontier = ids == null || ids == OpportunityJson.Nil.INSTANCE ? Optional.empty()
                    : Optional.of(OpportunityJson.array(ids, "direct_landed_vassal_character_ids").stream()
                            .map(OrdinarySwayPolicy::character).toList());
            root = Optional.of(new Root("available".equals(OpportunityJson.text(value.get("status"), "status")),
                    character(value.get("player_character_id")), OpportunityJson.bool(value.get("player_character_alive"), "player_character_alive"),
                    OpportunityJson.integer(value.get("snapshot_revision"), "snapshot_revision"),
                    OpportunityJson.integer(value.get("date_raw"), "date_raw"), frontier));
        }
        return new CapturedView(origin, root, capabilities, inputs);
    }
    private static Frame frame(PlanningRequest request) {
        OpportunityJson.Obj snapshot = request.observations().snapshot();
        OpportunityJson.Obj actor = OpportunityJson.object(snapshot.get("played_character"), "played_character");
        OpportunityJson.Value context = snapshot.get("active_context");
        OpportunityJson.Value event = null, interaction = null;
        if (context instanceof OpportunityJson.Obj active) {
            event = active.get("active_event"); interaction = active.get("pending_character_interaction");
        } else {
            event = snapshot.get("active_event"); interaction = snapshot.get("pending_character_interaction");
        }
        Context kind = event == null || interaction == null ? Context.UNAVAILABLE
                : event == OpportunityJson.Nil.INSTANCE && interaction == OpportunityJson.Nil.INSTANCE ? Context.CLEAR : Context.MANDATORY;
        var held = request.before().frame();
        return new Frame(held.snapshotId(), held.revision(), held.identity().nativeRevision(), held.identity().dateRaw(),
                character(actor.get("character_id")), request.observations().paused(), request.observations().mapReady(),
                OpportunityJson.bool(actor.get("alive"), "alive"), kind);
    }
    private static OpportunityJson.Obj arguments(OrdinarySwayService.Staged staged) {
        ObjectNode row = StrictJson.object(); row.put("schema", ARGUMENT_SCHEMA);
        row.set("decision", StrictJson.parse(SwayScheduleWire.encode(staged.decision())));
        ObjectNode flags = row.putObject("frame_flags"); flags.put("paused", staged.frame().paused());
        flags.put("map_ready", staged.frame().mapReady()); flags.put("alive", staged.frame().alive());
        flags.put("context", staged.frame().context().name());
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row)), "ordinary Sway command");
    }

    /** Pure dispatcher decoder. Only the sole coordinator may subsequently invoke the existing ExecutionPort. */
    public static OrdinarySwayService.Staged restoreStaged(ActionCommand command) {
        Objects.requireNonNull(command); require(command.operation().equals(OPERATION), "foreign Sway operation");
        ObjectNode row = StrictJson.object(StrictJson.parse(OpportunityJson.encode(command.arguments())),
                Set.of("schema", "decision", "frame_flags"));
        require(ARGUMENT_SCHEMA.equals(StrictJson.text(row.get("schema"))), "Sway argument schema differs");
        ObjectNode flags = StrictJson.object(row.get("frame_flags"), Set.of("paused", "map_ready", "alive", "context"));
        var held = command.before().frame();
        Frame frame = new Frame(held.snapshotId(), held.revision(), held.identity().nativeRevision(), held.identity().dateRaw(),
                held.identity().player().longValueExact(), flag(flags.get("paused")), flag(flags.get("map_ready")),
                flag(flags.get("alive")), Context.valueOf(StrictJson.text(flags.get("context"))));
        JsonNode value = row.get("decision"); require(value != null && value.isObject(), "Sway staged decision required");
        Job job = Job.valueOf(StrictJson.text(value.get("job")).toUpperCase(Locale.ROOT));
        Set<String> fields = new HashSet<>(Set.of("job", "reason", "state", "submit_allowed"));
        if (value.has("target_character_id")) fields.add("target_character_id");
        if (value.has("action_id")) fields.add("action_id");
        if (job == Job.QUERY_SELECTED_TARGET) fields.add("native_ai_rank_claimed");
        StrictJson.object(value, fields); require(!flag(value.get("submit_allowed")), "proposal is not submit authority");
        if (job == Job.QUERY_SELECTED_TARGET) require(!flag(value.get("native_ai_rank_claimed")), "native rank is not claimed");
        var target = value.has("target_character_id") ? Optional.of(StrictJson.integer(value.get("target_character_id"), 1, 0xffff_ffffL))
                : Optional.<Long>empty();
        var action = value.has("action_id") ? Optional.of(StrictJson.text(value.get("action_id"))) : Optional.<String>empty();
        var stagedDecision = new OrdinarySwaySchedule.Decision(Optional.of(job),
                Reason.valueOf(StrictJson.text(value.get("reason")).toUpperCase(Locale.ROOT)), target, action,
                Optional.of(SwayScheduleWire.decodeState(StrictJson.canonical(value.get("state")))));
        return new OrdinarySwayService.Staged(frame, stagedDecision);
    }
    private static long character(OpportunityJson.Value value) {
        BigInteger id = OpportunityJson.integer(value, "character_id");
        require(id.signum() > 0 && id.compareTo(BigInteger.valueOf(0xffff_ffffL)) <= 0, "full character identity required");
        return id.longValueExact();
    }
    private static boolean flag(JsonNode value) {
        require(value != null && value.isBoolean(), "actual Sway boolean required"); return value.booleanValue();
    }
    private static String sha(byte[] first, byte[] second) {
        try { MessageDigest digest = MessageDigest.getInstance("SHA-256"); digest.update(first); return HexFormat.of().formatHex(digest.digest(second)); }
        catch (NoSuchAlgorithmException failure) { throw new IllegalStateException(failure); }
    }
}
