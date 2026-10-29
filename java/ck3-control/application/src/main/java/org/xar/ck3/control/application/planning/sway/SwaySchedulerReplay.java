package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.application.planning.sway.SwayFormalState.*;
import static org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService;

/** Reexecutes the actual stage and service producers from archived inputs. Never dispatches on replay. */
public final class SwaySchedulerReplay implements SwayCanonicalDomain.SchedulerVerifier {
    public static final String STAGE_SCHEMA = "xar.java.sway-original-stage/v1";
    public static final String RUN_SCHEMA = "xar.java.sway-original-execution/v1";
    private final NativeEffectEvidence.FrameLoader frames;
    private final Capabilities capabilities;
    private final String rootContractId;
    public SwaySchedulerReplay(NativeEffectEvidence.FrameLoader frames, Capabilities capabilities, String rootContractId) {
        this.frames = Objects.requireNonNull(frames); this.capabilities = Objects.requireNonNull(capabilities); this.rootContractId = StrictJson.text(rootContractId);
    }
    public record Stage(ActionCommand command, ExactRef inputDomain, ExactRef rootRead) {
        public Stage { Objects.requireNonNull(command); Objects.requireNonNull(inputDomain); Objects.requireNonNull(rootRead); }
    }
    public record Run(ExactRef stage, CheckResult result, List<ExactRef> reads, Optional<ExactRef> child) {
        public Run { Objects.requireNonNull(stage); Objects.requireNonNull(result); reads = List.copyOf(reads); require(reads.size() <= 4, "bounded optional-work reads"); Objects.requireNonNull(child); }
    }
    public static byte[] encodeStage(Stage value) {
        ObjectNode row = StrictJson.object(); row.put("schema", STAGE_SCHEMA); row.set("command", StrictJson.parse(ActionCodec.encodeCommand(value.command()))); row.set("input_domain", value.inputDomain().toJson()); row.set("root_read", value.rootRead().toJson()); return StrictJson.canonical(row, SwayFormalCodec.MAX);
    }
    public static Stage decodeStage(byte[] bytes) {
        JsonNode row = StrictJson.object(StrictJson.parse(bytes, SwayFormalCodec.MAX), Set.of("schema", "command", "input_domain", "root_read")); SwayNativeWire.equals(row, "schema", STAGE_SCHEMA);
        return new Stage(ActionCodec.decodeCommand(StrictJson.canonical(row.get("command"))), ExactRef.fromJson(row.get("input_domain")), ExactRef.fromJson(row.get("root_read")));
    }
    public static byte[] encodeRun(Run value) {
        ObjectNode row = StrictJson.object(); row.put("schema", RUN_SCHEMA); row.set("stage", value.stage().toJson()); row.set("result", encodeResult(value.result()));
        var refs = row.putArray("reads"); value.reads().forEach(ref -> refs.add(ref.toJson())); SwayFormalCodec.nullable(row, "child", value.child().map(ExactRef::toJson)); return StrictJson.canonical(row, SwayFormalCodec.MAX);
    }
    public static Run decodeRun(byte[] bytes) {
        JsonNode row = StrictJson.object(StrictJson.parse(bytes, SwayFormalCodec.MAX), Set.of("schema", "stage", "result", "reads", "child")); SwayNativeWire.equals(row, "schema", RUN_SCHEMA);
        require(row.get("reads").isArray(), "original result read refs required"); var refs = new java.util.ArrayList<ExactRef>(); row.get("reads").forEach(value -> refs.add(ExactRef.fromJson(value)));
        return new Run(ExactRef.fromJson(row.get("stage")), decodeResult(row.get("result")), refs, SwayFormalCodec.optional(row.get("child")).map(ExactRef::fromJson));
    }
    @Override public void verifyStage(Ledger prior, StageRecorded change, SwayTransitionCodec.Proofs proofs, ActionPorts.OutcomeArchive originals) {
        Stage stage = decodeStage(originals.loadMaterial(change.basis()).bytes());
        require(proofs.reads().equals(List.of(stage.rootRead())) && proofs.materials().equals(List.of(change.basis())) && proofs.dispatch().isEmpty() && proofs.nativeFrame().isEmpty(), "stage exact original evidence differs");
        require(Arrays.equals(SwayFormalCodec.encode(prior), originals.loadMaterial(stage.inputDomain()).bytes()), "stage original domain differs from actual predecessor");
        require(staged(stage, prior, originals).equals(OrdinarySwayPolicy.restoreStaged(stage.command())), "proposal job differs from actual ordinary stage producer");
    }
    @Override public void verifyFinal(ActionCommand parent, SwaySchedulerCompletion completion, ActionPorts.OutcomeArchive originals) {
        var finalFrame = frames.load(completion.finalFrame(), originals); var identity = finalFrame.identity();
        require(identity.machineId().equals(parent.before().machineId()) && identity.game().equals(parent.before().game()) && identity.frame().episodeRunId().equals(parent.before().frame().episodeRunId()) && identity.frame().identity().player().equals(parent.before().frame().identity().player()) && finalFrame.source().equals(parent.source()) && finalFrame.sessionId().equals(parent.sessionId()), "actual final Sway SEM crossed original parent scope");
        require(identity.frame().revision().compareTo(parent.before().frame().revision()) >= 0 && identity.frame().identity().dateRaw().compareTo(parent.before().frame().identity().dateRaw()) >= 0, "actual final Sway SEM predates its parent");
        require(completion.finalReads().size() == 1, "one actual independently guarded campaign root read required at final SEM");
        var root = originals.loadRead(completion.finalReads().getFirst()); read(root, originals);SwaySharedRoot.requirePublicCapture(root);
        require(root.contractId().equals(rootContractId) && root.request().operation().equals(OrdinarySwayReadSource.ROOT) && root.request().before().equals(identity) && root.request().source().equals(parent.source()) && root.request().sessionId().equals(parent.sessionId()), "final independent campaign read differs from actual rebuilt SEM or installed definition");
        OrdinarySwayReadSource.originalResult(root);
        completion.exactContinuation().ifPresent(command -> require(command.before().equals(identity) && command.source().equals(finalFrame.source()) && command.sessionId().equals(finalFrame.sessionId()), "recorded fresh fullplan continuation differs from its exact actual final source"));
        completion.fullPlanOriginals().ifPresent(refs -> {
            var request = org.xar.ck3.control.application.planning.PlanningWire.decodeRequest(originals.loadMaterial(refs.request()).bytes());
            var result = org.xar.ck3.control.application.planning.PlanningWire.decodeResult(originals.loadMaterial(refs.result()).bytes());
            require(request.before().equals(identity) && request.source().equals(finalFrame.source()) && request.sessionId().equals(finalFrame.sessionId()), "recorded fullplan input differs from actual final source");
            Optional<ActionCommand> selected = result instanceof org.xar.ck3.control.application.planning.PlanningResult.ActionSelected value ? Optional.of(value.command()) : Optional.empty();
            require(selected.isPresent() == completion.exactContinuation().isPresent() && (selected.isEmpty() || Arrays.equals(ActionCodec.encodeCommand(selected.orElseThrow()), ActionCodec.encodeCommand(completion.exactContinuation().orElseThrow()))), "recorded fullplan result differs from exact continuation command");
            // This preserves real producer output only. Root must run the full planner on a new Ready after parent settlement.
        });
    }
    private Staged staged(Stage stage, Ledger inputs, ActionPorts.OutcomeArchive originals) {
        PlanningReadReceipt root = originals.loadRead(stage.rootRead()); read(root, originals);SwaySharedRoot.requirePublicCapture(root);
        require(root.contractId().equals(rootContractId) && root.request().before().equals(stage.command().before()) && root.request().source().equals(stage.command().source()) && root.request().sessionId().equals(stage.command().sessionId()), "stage root read crossed exact registered definition or command origin");
        var restored = OrdinarySwayPolicy.restoreStaged(stage.command());
        var projected = OrdinarySwayPolicy.project(stage.command().before(), OrdinarySwayReadSource.originalResult(root), capabilities, () -> Optional.of(SwaySessionInputs.project(inputs, stage.command().before())));
        var captured = new Captured(stage.command().source(), new Wrapper(stage.command().before().frame().snapshotId(), stage.command().before().frame().revision()), OrdinarySwaySchedule.Step.LIFE_ADVANCE, Optional.of(restored.frame()), projected.root(), capabilities);
        return new OrdinarySwayService().stage(captured, projected.inputs()).staged().orElseThrow(() -> new IllegalArgumentException("original source no longer produces the retained Sway job"));
    }
    @Override public SwaySchedulerCompletion.Continuation verify(ContinuityState head, Ledger prior, SchedulerSaved change, SwayTransitionCodec.Proofs proofs, ActionPorts.OutcomeArchive originals) {
        Run run = decodeRun(originals.loadMaterial(change.replay()).bytes());
        require(prior.activeStage().equals(Optional.of(run.stage())) && proofs.reads().equals(run.reads()) && proofs.dispatch().isEmpty() && proofs.nativeFrame().isEmpty(), "scheduler result has no exact actual stage/read basis");
        var materials = new java.util.ArrayList<ExactRef>(List.of(run.stage(), change.replay())); run.child().ifPresent(materials::add); require(proofs.materials().equals(materials), "scheduler original material closure differs");
        Stage stage = decodeStage(originals.loadMaterial(run.stage()).bytes()); Ledger original = SwayFormalCodec.decode(originals.loadMaterial(stage.inputDomain()).bytes()); Staged staged = staged(stage, original, originals);
        verifyResult(head, prior, original, staged, run, originals);
        final OrdinarySwaySchedule.State[] produced = new OrdinarySwaySchedule.State[1];
        Execution replayed = new OrdinarySwayService().execute(staged, new ExecutionPort() {
            @Override public Optional<Inputs> loadInputs() { return Optional.of(SwaySessionInputs.project(original, stage.command().before())); }
            @Override public FormalResult queryAndConsume(OrdinarySwaySchedule.Frame expected, long target) { return result(FormalResult.class); }
            @Override public LifecycleResult observeLifecycle(OrdinarySwaySchedule.Frame expected) { return result(LifecycleResult.class); }
            private <T extends CheckResult> T result(Class<T> type) {
                if (run.result() instanceof LocalResult local && local.status() == LocalStatus.UNAVAILABLE) throw new Unavailable(local.error().orElse("original optional work unavailable"));
                require(type.isInstance(run.result()), "replay selected another actual consumer branch"); return type.cast(run.result());
            }
            @Override public Optional<String> saveScheduler(OrdinarySwaySchedule.State value) { produced[0] = value; return Optional.empty(); }
            @Override public OrdinaryContinuation executeFreshOrdinary() { var receipt = ProjectionJson.object("{\"status\":\"archived_scheduler_replay_only\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8), 128); return new OrdinaryContinuation(receipt, receipt); }
        });
        Receipt receipt = replayed instanceof Started start ? start.receipt() : ((Continued)replayed).receipt().orElseThrow();
        require(change.state().equals(produced[0]) && change.state().equals(receipt.schedulerState()) && Arrays.equals(StrictJson.canonical(encodeResult(receipt.result())), StrictJson.canonical(encodeResult(run.result()))), "scheduler output differs from full original service replay");
        return continuation(replayed);
    }
    public static SwaySchedulerCompletion.Continuation continuation(Execution actual) { return actual instanceof Started ? SwaySchedulerCompletion.Continuation.NOT_NEEDED : SwaySchedulerCompletion.Continuation.FRESH_FULL_PLAN_REQUIRED; }
    private void verifyResult(ContinuityState head, Ledger current, Ledger original, Staged staged, Run run, ActionPorts.OutcomeArchive archive) {
        for (ExactRef ref : run.reads()) read(archive.loadRead(ref), archive);
        if (run.result() instanceof FormalResult formal) {
            if (formal.status() == FormalStatus.APPLIED && formal.postconditionVerified()) {
                Episode episode = current.resolved().orElseThrow(); require(formal.actionId().equals(Optional.of(episode.identity().actionId())), "formal result differs from canonical current identity");
                if (staged.decision().job().orElseThrow() == OrdinarySwaySchedule.Job.QUERY_SELECTED_TARGET) {
                    ActionReceipt child = archive.loadReceipt(run.child().orElseThrow()); require(child.command().actionId().equals(episode.identity().actionId()) && child.command().operation().value().equals(SwayNativeWire.START + episode.identity().targetCharacterId()), "scheduler new Start is not its actual child");
                    SwayActionLifecycle.verifyArchived(frames, head, child, archive);
                } else require(original.pending().isPresent() || historicalPendingUnresolved(original), "recovery result had no original pending");
            } else if (formal.status() == FormalStatus.NO_POSITIVE_OPPORTUNITY) {
                var target = target(run, archive); require(!target.startable(true), "positive opportunity cannot become a no-operation result");
            } else if (formal.status() == FormalStatus.ALREADY_APPLIED) {
                var target = target(run, archive); var followup = SwayFormalState.followup(current, target); require(current.resolved().isPresent() && followup != FollowupDecision.FIRST_SELECTED_RELATION && followup != FollowupDecision.RETARGET_SELECTED_RELATION && followup != FollowupDecision.REPEAT_SELECTED_TARGET, "already-applied result requires actual retained relation followup");
                require(formal.followup().equals(Optional.of(followup(followup))), "scheduler followup differs from actual reducer");
            } else if (formal.status() == FormalStatus.RECEIPT_PENDING || formal.status() == FormalStatus.POSTCONDITION_PENDING || formal.status() == FormalStatus.SUBMISSION_UNRESOLVED || formal.status() == FormalStatus.PENDING_RECOVERY) {
                require(current.pending().isPresent() || historicalPendingUnresolved(current), "pending result must retain original UNKNOWN state");
            } else require(!formal.postconditionVerified(), "unclassified result cannot grant a verified effect");
        } else if (run.result() instanceof LifecycleResult lifecycle && lifecycle.status() == LifecycleStatus.OBSERVED) {
            var episode = current.resolved().orElseThrow(); require(!run.reads().isEmpty() && episode.lifecycle().latest().isPresent(), "observed lifecycle needs canonical actual native proof");
            require(run.reads().stream().map(archive::loadRead).allMatch(value -> value.request().before().equals(episode.lifecycle().latest().orElseThrow().source())), "scheduler observation differs from actual latest source");
        }
    }
    private static SwayNativeWire.TargetRead target(Run run, ActionPorts.OutcomeArchive archive) {
        return run.reads().stream().map(archive::loadRead).filter(value -> value.request().operation().value().startsWith(SwayNativeWire.TARGET)).map(value -> {
            long target = SwayNativeWire.integer(StrictJson.parse(OpportunityJson.encode(value.request().arguments())), "target_character_id", 1, 0xffff_ffffL);
            return SwayNativeWire.target(value.original().originalFrame().bytes(), value.requestId(), SwayNativeBindings.bind(value, new OperationKey(SwayNativeWire.TARGET + target)), target);
        }).findFirst().orElseThrow(() -> new IllegalArgumentException("formal result requires actual original target read"));
    }
    public static Followup followup(FollowupDecision value) { return switch(value) { case FINISH_SELECTED_RELATION -> Followup.FINISH_SELECTED_RELATION; case RETURN_TO_OPPORTUNITY_SELECTION -> Followup.RETURN_TO_OPPORTUNITY_SELECTION; default -> Followup.OTHER; }; }
    private void read(PlanningReadReceipt value, ActionPorts.OutcomeArchive archive) { NativeRecordedEvidenceVerifier.requireRead(value, archive); for (var guard : List.of(value.before().binding(), value.after().binding())) RootGuardEvidence.loadFrame(guard, archive, frames); }
    static ObjectNode encodeResult(CheckResult value) {
        ObjectNode row = StrictJson.object();
        if (value instanceof FormalResult formal) { row.put("kind", "formal"); row.put("status", formal.status().name()); row.put("verified", formal.postconditionVerified()); SwayFormalCodec.nullable(row, "action", formal.actionId().map(text -> StrictJson.object().put("value", text))); SwayFormalCodec.nullable(row, "followup", formal.followup().map(item -> StrictJson.object().put("value", item.name()))); row.set("evidence", SwayFormalCodec.chunks(formal.evidence().bytes())); }
        else if (value instanceof LifecycleResult lifecycle) { row.put("kind", "lifecycle"); row.put("status", lifecycle.status().name()); row.set("evidence", SwayFormalCodec.chunks(lifecycle.evidence().bytes())); }
        else { LocalResult local = (LocalResult)value; row.put("kind", "local"); row.put("status", local.status().name()); if (local.error().isPresent()) row.put("error", local.error().orElseThrow()); else row.putNull("error"); }
        return row;
    }
    static CheckResult decodeResult(JsonNode row) {
        return switch (SwayNativeWire.string(row, "kind")) {
            case "formal" -> { StrictJson.object(row, Set.of("kind", "status", "verified", "action", "followup", "evidence")); yield new FormalResult(FormalStatus.valueOf(SwayNativeWire.string(row, "status")), SwayNativeWire.bool(row, "verified"), SwayFormalCodec.optional(row.get("action")).map(value -> SwayNativeWire.string(StrictJson.object(value, Set.of("value")), "value")), SwayFormalCodec.optional(row.get("followup")).map(value -> Followup.valueOf(SwayNativeWire.string(StrictJson.object(value, Set.of("value")), "value"))), ProjectionJson.object(SwayFormalCodec.bytes(row.get("evidence")), SwayFormalCodec.MAX)); }
            case "lifecycle" -> { StrictJson.object(row, Set.of("kind", "status", "evidence")); yield new LifecycleResult(LifecycleStatus.valueOf(SwayNativeWire.string(row, "status")), ProjectionJson.object(SwayFormalCodec.bytes(row.get("evidence")), SwayFormalCodec.MAX)); }
            case "local" -> { StrictJson.object(row, Set.of("kind", "status", "error")); yield new LocalResult(LocalStatus.valueOf(SwayNativeWire.string(row, "status")), SwayFormalCodec.optional(row.get("error")).map(StrictJson::text)); }
            default -> throw new IllegalArgumentException("unknown original optional consumer result");
        };
    }
}
