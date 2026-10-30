package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual LIFE/council/crown receipt consumers. Native helper ACKs never manufacture gameplay_verified. */
public final class NativeGovernanceEffects implements NativeEffectRegistry.Observer {
    public static final String SCHEMA = "xar.java.governance-independent-effect/v1";
    public enum Kind { FOCUS, PERK, COUNCIL, PRIVATE_COUNCIL, CROWN }
    public interface SessionPort {
        org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session current(ActionCommand command);
        List<PlanningReadReceipt> preflight(ActionCommand command);
    }
    @FunctionalInterface public interface PreparationEvidencePort {
        void verify(ActionCommand command, ActionState.Attempt attempt, List<PlanningReadReceipt> originalReads, ActionPorts.OutcomeArchive archive);
        default List<PlanningReadReceipt> originals(ActionCommand command, ActionState.Attempt attempt, ActionPorts.OutcomeArchive archive) { return List.of(); }
    }
    public record Contracts(ReadContract<RawJson> lifestyle, ReadContract<RawJson> council, ReadContract<RawJson> crown) {
        public Contracts { Objects.requireNonNull(lifestyle); Objects.requireNonNull(council); Objects.requireNonNull(crown); }
        public List<ReadContract<?>> all() { return List.of(lifestyle, council, crown); }
    }
    public static final String FOCUS_STATE_READ = "private-query-player-lifestyle-current-state-v1";
    public static final String FOCUS_STATE_CONTRACT = "governance.focus-state-reconciliation/v1";
    private static final String FOCUS_STATE_MATERIAL = "xar.java.focus-current-state-reconciliation/v1";
    private static final String LIFE_READ = "private-query-player-lifestyle-receipt-v1";
    private static final String COUNCIL_READ = "query-assign-councillor-receipt-v1";
    private static final String CROWN_READ = "verify-realm-law-crown-v1-private";
    private final NativeEffectSnapshots snapshots; private final PlanningReadPort reads; private final Contracts contracts;
    private final SessionPort sessions;
    private final NativeEffectRegistry.Observer privateCouncil;
    private final PreparationEvidencePort preparationEvidence;
    private final Optional<ReadContract<OpportunityJson.Obj>> focusStateReconciliation;
    public NativeGovernanceEffects(NativeEffectSnapshots snapshots, PlanningReadPort reads, Contracts contracts,
            SessionPort sessions, NativeEffectRegistry.Observer privateCouncil, PreparationEvidencePort preparationEvidence) {
        this(snapshots,reads,contracts,sessions,privateCouncil,preparationEvidence,Optional.empty());
    }
    public NativeGovernanceEffects(NativeEffectSnapshots snapshots, PlanningReadPort reads, Contracts contracts,
            SessionPort sessions, NativeEffectRegistry.Observer privateCouncil, PreparationEvidencePort preparationEvidence,
            Optional<ReadContract<OpportunityJson.Obj>> focusStateReconciliation) {
        this.snapshots = Objects.requireNonNull(snapshots); this.reads = Objects.requireNonNull(reads); this.contracts = Objects.requireNonNull(contracts);
        this.sessions = Objects.requireNonNull(sessions); this.privateCouncil = Objects.requireNonNull(privateCouncil);
        this.preparationEvidence = Objects.requireNonNull(preparationEvidence);
        this.focusStateReconciliation=Objects.requireNonNull(focusStateReconciliation);
        focusStateReconciliation.ifPresent(NativeGovernanceEffects::requireFocusStateReconciliationProfile);
    }
    /** Stable Native correlation key; logical Root episodes and archived wire originals are unchanged. */
    public static String lifestyleWireEpisode(org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity actual) {
        Objects.requireNonNull(actual);
        var frame = actual.frame();
        ObjectNode stable = StrictJson.object().put("machine_id", actual.machineId())
                .put("episode_run_id", frame.episodeRunId()).put("player_character_id", frame.identity().player());
        stable.set("game", actual.game().toJson());
        return "native-" + frame.identity().player() + "-" + ActionCodec.sha256(StrictJson.canonical(stable)).substring(0,32);
    }
    public static Optional<Kind> kind(OperationKey operation) {
        return switch (operation.value()) {
            case "private-select-player-lifestyle-stock-focus-v1" -> Optional.of(Kind.FOCUS);
            case "private-select-player-lifestyle-perk-v1" -> Optional.of(Kind.PERK);
            case "assign-councillor-v1" -> Optional.of(Kind.COUNCIL);
            case "private-assign-councillor-v1" -> Optional.of(Kind.PRIVATE_COUNCIL);
            case "enact-realm-law-crown-v1-private" -> Optional.of(Kind.CROWN);
            default -> Optional.empty();
        };
    }
    public static Contracts readContracts(ExactRef lifestyleSource, ExactRef councilSource, ExactRef crownSource) {
        return new Contracts(contract(LIFE_READ, Optional.empty(), lifestyleSource),
                contract(COUNCIL_READ, Optional.of("game.action.assign-councillor-v1"), councilSource),
                contract(CROWN_READ, Optional.empty(), crownSource));
    }
    private static ReadContract<RawJson> contract(String step, Optional<String> capability, ExactRef source) {
        return new ReadContract<>("governance.receipt." + step, new OperationKey(step), capability, step,
                capability.isPresent() ? ReadContract.PermissionMode.ADVERTISED_CAPABILITY : ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                ReadContract.WireProfile.EXECUTE_STEP, source,
                request -> new NativeRequest(step, capability, new RawJson(OpportunityJson.encode(request.arguments()))),
                receipt -> {
                    ObjectNode original = StrictJson.object(StrictJson.parse(receipt.original().originalFrame().bytes()), Set.of("type", "protocol_version", "request_id", "ok", "result"));
                    StrictJson.require(StrictJson.text(original.get("type")).equals("command_result")
                            && StrictJson.integer(original.get("protocol_version"), 1, 1) == 1
                            && StrictJson.text(original.get("request_id")).equals(receipt.requestId())
                            && receipt.request().operation().value().equals(step), "governance receipt original correlation drift");
                    StrictJson.trueValue(original.get("ok"));
                    RawJson token = receipt.original().originalResultToken().orElseThrow(() -> new IllegalArgumentException("independent governance result token missing"));
                    StrictJson.require(receipt.original().nativeOk() && StrictJson.parse(token.bytes()).equals(original.get("result")), "governance receipt token differs from the full original packet");
                    return token;
                });
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        Kind selected = kind(command.operation()).orElseThrow(() -> new IllegalArgumentException("not a registered governance operation"));
        if (selected == Kind.PRIVATE_COUNCIL) return privateCouncil.observe(command, attempt, dispatch);
        var rejected = snapshots.withArchive(bound -> originalRejection(command, attempt, dispatch, bound));
        if (rejected.isPresent()) return rejected.orElseThrow();
        List<PlanningReadReceipt> originalPreflight = List.of();
        if (selected == Kind.FOCUS || selected == Kind.PERK) {
            try {
                originalPreflight = snapshots.withArchive(bound -> {
                    var retained = preparationEvidence.originals(command, attempt, bound);
                    StrictJson.require(!retained.isEmpty(), "complete original LIFE preparation custody is unavailable");
                    preparationEvidence.verify(command, attempt, retained, bound);
                    if (dispatch instanceof NativeActionPort.AckReceived submit) for (var original : retained) NativeRequestChronology.requireBeforeSubmission(original, attempt, submit);
                    return retained;
                });
                var live = ActionReconciliationScope.activeFor(command) ? List.<PlanningReadReceipt>of() : sessions.preflight(command);
                StrictJson.require(live.isEmpty() || live.equals(originalPreflight), "LIFE live preflight differs from canonical prepared originals");
            } catch (IllegalArgumentException | IllegalStateException unavailable) {
                return NativeEffectRegistry.Projected.pending("original LIFE preflight custody is unavailable; do not consume or repeat an independent native receipt: " + unavailable.getMessage(), attempt.preparedRequest().preparationEvidence());
            }
        }
        requirePreparedTarget(selected, command, attempt);
        var pair = snapshots.read(command, attempt); Complete after = pair.after();
        if(selected==Kind.FOCUS&&ActionReconciliationScope.activeFor(command)) {
            if(focusStateReconciliation.isEmpty())return NativeEffectRegistry.Projected.pending(
                    "actual original FOCUS current-state reconciliation contract is not installed",List.of(after.originalEvidence()));
            var contract=focusStateReconciliation.orElseThrow();
            ReconciliationIdentity identity;
            try { identity=ActionReconciliationScope.requireIdentity(command,attempt); }
            catch(java.io.IOException failure){throw new java.io.UncheckedIOException("actual FOCUS reconciliation scope unavailable",failure);}
            lifestyleAck(command,attempt,dispatch);
            var request=focusStateReconciliationRequest(command,attempt,identity,contract,ActionObservationWindow.deadline(command));
            var read=reads.read(sessions.current(command),contract,request);
            if(!(read instanceof PlanningReadResult.Known<OpportunityJson.Obj> known))
                return NativeEffectRegistry.Projected.pending("actual FOCUS current-state getter unavailable; original UNKNOWN retained: "
                        + ((PlanningReadResult.Unavailable<?>) read).reason(),List.of(after.originalEvidence()));
            var projected=projectFocusState(command,attempt,dispatch,pair,known.receipt(),known.value());
            if(!(projected.result() instanceof ActionPorts.EffectObserved))return projected;
            var originalReads=new ArrayList<PlanningReadReceipt>(originalPreflight);originalReads.add(known.receipt());
            return NativeEffectSnapshots.withEvidence(projected,List.of(snapshots.evidence(command,attempt,pair,originalReads,
                    projected.compatibleResult().orElseThrow())));
        }
        ReadContract<RawJson> contract = switch (selected) { case FOCUS, PERK -> contracts.lifestyle(); case COUNCIL -> contracts.council(); case CROWN -> contracts.crown(); case PRIVATE_COUNCIL -> throw new IllegalStateException("private Council uses its actual continuation evidence"); };
        ObjectNode fields = StrictJson.object(); String originalId = originalId(selected, attempt);
        if (selected == Kind.CROWN) fields.put("submitted_request_id", originalId);
        else if (selected == Kind.FOCUS || selected == Kind.PERK) {
            fields.put("action_request_id", originalId); fields.put("expected_snapshot_id", "native:" + after.identity().frame().identity().nativeRevision());
            fields.put("expected_episode_run_id", lifestyleWireEpisode(after.identity()));
        }
        if (selected != Kind.COUNCIL) {
            fields.put("expected_date_raw", after.identity().frame().identity().dateRaw());
            fields.put("expected_player_character_id", after.identity().frame().identity().player());
        }
        var request = new PlanningReadRequest(after.identity(), after.source(), after.sessionId(), contract.operation(),
                (OpportunityJson.Obj) OpportunityJson.parse(StrictJson.canonical(fields)), ActionObservationWindow.deadline(command));
        PlanningReadResult<RawJson> read = reads.read(sessions.current(command), contract, request);
        if (!(read instanceof PlanningReadResult.Known<RawJson> known))
            return NativeEffectRegistry.Projected.pending("actual independent governance receipt is unavailable; no effect/replay credit", List.of(after.originalEvidence()));
        var projected = project(command, attempt, dispatch, pair, known.receipt(), known.value());
        if (!(projected.result() instanceof ActionPorts.EffectObserved)) return projected;
        var originalReads = new ArrayList<PlanningReadReceipt>();
        if (selected == Kind.FOCUS || selected == Kind.PERK) originalReads.addAll(originalPreflight);
        originalReads.add(known.receipt());
        return NativeEffectSnapshots.withEvidence(projected, List.of(snapshots.evidence(command, attempt, pair, originalReads, projected.compatibleResult().orElseThrow())));
    }
    public static void requireFocusStateReconciliationProfile(ReadContract<?> contract) {
        Objects.requireNonNull(contract);
        StrictJson.require(contract.contractId().equals(FOCUS_STATE_CONTRACT)&&contract.operation().value().equals(FOCUS_STATE_READ)
                &&contract.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                &&contract.permissionMode()==ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                &&contract.permissionKey().equals(FOCUS_STATE_READ)&&contract.requiredCapability().isEmpty()
                &&contract.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP&&contract.hasPureReplay(),
                "only the installed original FOCUS current-state getter profile is eligible");
    }
    /** Pure original-intent request DATA; the private Root pending/current lease still supplies query authority. */
    public static PlanningReadRequest focusStateReconciliationRequest(ActionCommand command,ActionState.Attempt attempt,
            ReconciliationIdentity identity,ReadContract<?> contract,java.time.Instant deadline) {
        requireFocusStateReconciliationProfile(contract);Objects.requireNonNull(identity);
        StrictJson.require(kind(command.operation()).filter(Kind.FOCUS::equals).isPresent(),"current-state reconciliation is FOCUS only");
        requirePreparedTarget(Kind.FOCUS,command,attempt);
        var pending=identity.pending();var factual=identity.factual();
        StrictJson.require(pending.actionId().equals(command.actionId())&&pending.bodySha256().equals(ActionCodec.bodySha256(command))
                &&pending.requestId().equals(attempt.requestId())&&pending.originalBefore().equals(command.before())
                &&identity.source().equals(command.source())&&identity.sessionId().equals(command.sessionId())
                &&factual.machineId().equals(command.before().machineId())&&factual.game().equals(command.before().game())
                &&factual.frame().episodeRunId().equals(command.before().frame().episodeRunId())
                &&factual.frame().identity().player().equals(command.before().frame().identity().player()),
                "FOCUS getter changed its original pending request/body or actual same-actor Game");
        return PlanningReadRequest.newReconciliation(identity,contract.operation(),new OpportunityJson.Obj(java.util.Map.of()),deadline);
    }
    public static void requireCanonicalFocusStateReconciliation(ActionReceipt original,ActionState.Attempt attempt,
            ReconciliationIdentity identity,ReadContract<?> contract,PlanningReadRequest request) {
        StrictJson.require(original.state() instanceof ActionState.Unknown
                &&ActionTransitions.attempt(original.state()).filter(attempt::equals).isPresent(),
                "FOCUS getter requires the actual original UNKNOWN Attempt");
        var dispatch=ActionTransitions.dispatch(original.state()).orElseThrow(()->new IllegalArgumentException("original FOCUS ACK is absent"));
        StrictJson.require(dispatch instanceof NativeActionPort.AckReceived,"original FOCUS successful ACK is absent");
        actualOriginal(original.command(),attempt,(NativeActionPort.AckReceived)dispatch);
        lifestyleAck(original.command(),attempt,dispatch);
        StrictJson.require(request.equals(focusStateReconciliationRequest(original.command(),attempt,identity,contract,request.deadline())),
                "FOCUS getter request changed its exact original pending/current factual binding");
    }
    /** Pure complete decoded getter projection. It does not grant Native or Root observation authority. */
    static Optional<List<ExpectedValue>> focusStateValues(String target,OpportunityJson.Obj normalized) {
        ObjectNode state=EffectJson.object(normalized);
        equal(state.get("step"),FOCUS_STATE_READ);equal(state.get("status"),"available");
        ObjectNode snapshot=EffectJson.object(state.get("snapshot")),focus=EffectJson.object(snapshot.get("current_focus"));
        equal(snapshot.get("status"),"available");
        String presence=StrictJson.text(focus.get("presence"));
        StrictJson.require(Set.of("present","absent").contains(presence),"complete current FOCUS presence required");
        if(!presence.equals("present"))return Optional.empty();
        String current=StrictJson.text(focus.get("key"));StrictJson.text(focus.get("lifestyle_key"));
        ObjectNode ready=EffectJson.object(snapshot.get("readiness")),progress=EffectJson.object(snapshot.get("current_lifestyle_progress"));
        if(!EffectJson.bool(ready.get("current_focus_ready"))||!EffectJson.bool(ready.get("lifestyle_progress_ready"))
                ||!EffectJson.bool(ready.get("same_frame_ready"))||!StrictJson.text(progress.get("presence")).equals("present"))return Optional.empty();
        StrictJson.require(StrictJson.text(progress.get("lifestyle_key")).equals(StrictJson.text(focus.get("lifestyle_key"))),
                "FOCUS current lifestyle progress belongs to another observed focus");
        if(!current.equals(target))return Optional.empty();
        return Optional.of(List.of(new ExpectedText(new FieldKey("lifestyle.target_key"),target),
                new ExpectedBoolean(new FieldKey("lifestyle.has_current_focus"),true),
                new ExpectedText(new FieldKey("lifestyle.current_focus_key"),current),
                new ExpectedBoolean(new FieldKey("native.gameplay_verified"),true)));
    }
    private static NativeEffectRegistry.Projected projectFocusState(ActionCommand command,ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch,NativeEffectSnapshots.Pair pair,PlanningReadReceipt read,OpportunityJson.Obj material) {
        StrictJson.require(kind(command.operation()).filter(Kind.FOCUS::equals).isPresent()
                &&read.request().origin() instanceof CommandOrigin.Reconciliation&&read.contractId().equals(FOCUS_STATE_CONTRACT),
                "fresh getter material belongs only to original FOCUS reconciliation");
        requirePreparedTarget(Kind.FOCUS,command,attempt);lifestyleAck(command,attempt,dispatch);
        actualOriginal(command,attempt,(NativeActionPort.AckReceived)dispatch);
        Complete after=pair.after();
        NativeEffectSnapshots.requireAfterRead(command,attempt,after,read,new OperationKey(FOCUS_STATE_READ));
        ObjectNode state=EffectJson.object(material),snapshot=EffectJson.object(state.get("snapshot"));
        var frame=after.identity().frame();var id=frame.identity();
        equal(state.get("episode_run_id"),frame.episodeRunId());equal(snapshot.get("snapshot_id"),frame.snapshotId());
        equal(snapshot.get("public_revision"),frame.revision());equal(snapshot.get("native_revision"),id.nativeRevision());
        equal(snapshot.get("date_raw"),id.dateRaw());equal(snapshot.get("player_character_id"),id.player());
        String target=StrictJson.text(EffectJson.object(command.arguments()).get("target_key"));
        var actual=focusStateValues(target,material);
        if(actual.isEmpty())return NativeEffectRegistry.Projected.pending(
                "actual current FOCUS getter does not prove the original selected target; UNKNOWN retained",List.of(after.originalEvidence()));
        ObjectNode compatible=StrictJson.object().put("schema",FOCUS_STATE_MATERIAL)
                .put("evidence_kind","CURRENT_STATE_GETTER_RECONCILIATION").put("kind","focus")
                .put("original_request_id",attempt.requestId()).put("state_query_request_id",read.requestId()).put("target_key",target)
                .put("episode_run_id",command.before().frame().episodeRunId()).put("post_date_raw",id.dateRaw());
        compatible.set("state",state.deepCopy());
        return NativeEffectSnapshots.observed(command,attempt,after,SCHEMA,actual.orElseThrow(),read.requestId(),EffectJson.raw(compatible),List.of());
    }
    private static NativeEffectRegistry.Projected project(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch, NativeEffectSnapshots.Pair pair, PlanningReadReceipt read, RawJson material) {
        Kind selected = kind(command.operation()).orElseThrow(() -> new IllegalArgumentException("not a registered governance operation"));
        requirePreparedTarget(selected, command, attempt); Complete after = pair.after(); String originalId = originalId(selected, attempt);
        OperationKey operation = new OperationKey(switch (selected) { case FOCUS, PERK -> LIFE_READ; case COUNCIL -> COUNCIL_READ; case CROWN -> CROWN_READ; case PRIVATE_COUNCIL -> throw new IllegalArgumentException("private Council replay requires its continuation basis"); });
        NativeEffectSnapshots.requireAfterRead(command, attempt, after, read, operation);
        ObjectNode result = EffectJson.object(EffectJson.parse(material));
        StrictJson.require(StrictJson.text(result.get("step")).equals(operation.value()), "governance receipt query step drift");
        // LIFE's real native serializer has no accepted member; command_result.ok and its typed receipt bind it.
        if (selected != Kind.FOCUS && selected != Kind.PERK) StrictJson.trueValue(result.get("accepted"));
        List<ExpectedValue> actual;
        if (selected == Kind.FOCUS || selected == Kind.PERK) {
            lifestyleAck(command, attempt, dispatch);
            actual = lifestyle(selected, command, originalId, after, result);
        }
        else if (selected == Kind.COUNCIL) actual = council(command, attempt, dispatch, originalId, after, result);
        else actual = crown(command, attempt, dispatch, originalId, after, result);
        ObjectNode compatible = result.deepCopy();
        if (selected == Kind.FOCUS || selected == Kind.PERK) compatible.put("kind", selected == Kind.FOCUS ? "focus" : "perk")
                .put("target_key", StrictJson.text(EffectJson.object(command.arguments()).get("target_key")))
                .put("episode_run_id", command.before().frame().episodeRunId())
                .put("post_date_raw", after.identity().frame().identity().dateRaw());
        return NativeEffectSnapshots.observed(command, attempt, after, SCHEMA, actual, read.requestId(), EffectJson.raw(compatible), List.of());
    }
    public static NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation, ExactRef source,
            NativeEffectEvidence.FrameLoader frames, Contracts actualContracts, PreparationEvidencePort preparationEvidence) {
        return archivedVerifier(operation,source,frames,actualContracts,preparationEvidence,Optional.empty());
    }
    public static NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation, ExactRef source,
            NativeEffectEvidence.FrameLoader frames, Contracts actualContracts, PreparationEvidencePort preparationEvidence,
            Optional<ReadContract<OpportunityJson.Obj>> focusStateReconciliation) {
        Objects.requireNonNull(focusStateReconciliation);
        focusStateReconciliation.ifPresent(NativeGovernanceEffects::requireFocusStateReconciliationProfile);
        Kind selected = kind(operation).orElseThrow(() -> new IllegalArgumentException("exact governance operation required"));
        StrictJson.require(selected != Kind.PRIVATE_COUNCIL, "private Council requires its actual continuation archived verifier");
        Objects.requireNonNull(frames); Objects.requireNonNull(actualContracts);
        ReadContract<RawJson> contract = switch (selected) { case FOCUS, PERK -> actualContracts.lifestyle(); case COUNCIL -> actualContracts.council(); case CROWN -> actualContracts.crown(); case PRIVATE_COUNCIL -> throw new IllegalArgumentException("private Council continuation proof required"); };
        return new NativeRecordedEvidenceVerifier.Binding(operation, source, (head, receipt, archive) -> {
            var settled = (ActionState.Settled) receipt.state();
            if (settled.settlement() instanceof ActionState.Rejected rejected) {
                var replayed = originalRejection(receipt.command(), settled.attempt(), settled.dispatch(), archive)
                        .orElseThrow(() -> new IllegalArgumentException("original governance submit did not prove native rejection"));
                StrictJson.require(replayed.result() instanceof ActionPorts.RejectionObserved actual && actual.rejection().equals(rejected),
                        "archived governance rejection differs from its original typed native result");
                return;
            }
            var original = NativeEffectEvidence.load(receipt, archive, frames);
            StrictJson.require(!original.independentReads().isEmpty(), "governance effect requires its original independent receipt");
            var read = original.independentReads().getLast();
            var preflight = original.independentReads().subList(0, original.independentReads().size() - 1);
            if (selected == Kind.FOCUS || selected == Kind.PERK) {
                preparationEvidence.verify(receipt.command(), settled.attempt(), preflight, archive);
                StrictJson.require(settled.dispatch() instanceof NativeActionPort.AckReceived, "LIFE material requires original successful submission custody");
                for (var originalRead : preflight) NativeRequestChronology.requireBeforeSubmission(originalRead, settled.attempt(), (NativeActionPort.AckReceived) settled.dispatch());
            }
            else StrictJson.require(preflight.isEmpty(), "non-LIFE governance basis carried unrelated preflight reads");
            NativeEffectRegistry.Projected replayed;
            if(selected==Kind.FOCUS&&read.request().origin() instanceof CommandOrigin.Reconciliation
                    &&read.contractId().equals(FOCUS_STATE_CONTRACT)) {
                var getter=focusStateReconciliation.orElseThrow(()->new IllegalArgumentException("actual original FOCUS getter decoder is not installed"));
                var identity=read.request().origin().requireReconciliation();
                focusStateReconciliationRequest(receipt.command(),settled.attempt(),identity,getter,read.request().deadline());
                replayed=projectFocusState(receipt.command(),settled.attempt(),settled.dispatch(),original.frames(),read,getter.replay(read));
            } else replayed=project(receipt.command(), settled.attempt(), settled.dispatch(), original.frames(), read, contract.decode(read));
            replayed = NativeEffectSnapshots.withEvidence(replayed, ((ActionState.Applied) settled.settlement()).observation().supportingEvidence());
            NativeEffectEvidence.requireSame(settled.settlement(), replayed, original.compatibleResult());
        });
    }
    /** The native producer rejected before its helper call. An ambiguous catch/dispatch failure remains unresolved. */
    public static Optional<NativeEffectRegistry.Projected> originalRejection(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch, ActionPorts.OutcomeArchive archive) {
        Kind selected = kind(command.operation()).orElseThrow();
        if (selected == Kind.PRIVATE_COUNCIL || !(dispatch instanceof NativeActionPort.AckReceived ack)
                || !ack.nativeOk() || ack.originalResultToken().isEmpty()) return Optional.empty();
        ObjectNode result = actualOriginal(command, attempt, ack);
        if (!"rejected_before_submit".equals(StrictJson.text(result.get("status")))) return Optional.empty();
        requirePreparedTarget(selected, command, attempt);
        String reason;
        if (selected == Kind.FOCUS || selected == Kind.PERK) {
            StrictJson.object(result, Set.of("step", "private_build", "advertised", "status", "verification_pending", "action_request_id", "target_key", "pre_snapshot_id", "episode_run_id", "pre_public_revision", "failure_class", "rejection_reason"));
            equal(result.get("step"), command.operation().value()); StrictJson.trueValue(result.get("private_build"));
            StrictJson.require(!EffectJson.bool(result.get("advertised")) && !EffectJson.bool(result.get("verification_pending")), "rejected LIFE ACK is pending/advertised");
            equal(result.get("action_request_id"), attempt.requestId()); equal(result.get("target_key"), StrictJson.text(EffectJson.object(command.arguments()).get("target_key")));
            empty(result.get("pre_snapshot_id")); empty(result.get("episode_run_id")); StrictJson.integer(result.get("pre_public_revision"), 0, 0);
            String failure = StrictJson.text(result.get("failure_class")); String nativeReason = StrictJson.text(result.get("rejection_reason"));
            boolean known = switch (failure) {
                case "request_contract" -> Set.of("invalid_request", "invalid_target_key").contains(nativeReason);
                case "exact_build_binding" -> nativeReason.equals("exact_command_adapter_unavailable");
                case "snapshot_binding" -> Set.of("application_main_precondition_unavailable", "paused_snapshot_mismatch", "state_changed_before_submit").contains(nativeReason);
                case "final_legality" -> Set.of("target_not_finally_selectable", "target_already_applied").contains(nativeReason);
                case "state_observation" -> nativeReason.equals("complete_pre_state_unavailable");
                case "native_command_dispatch" -> Set.of("native_command_submit_failed", "action_executor_exception").contains(nativeReason);
                default -> false;
            };
            StrictJson.require(known, "unknown native LIFE rejection class/reason");
            if (failure.equals("native_command_dispatch")) return Optional.of(NativeEffectRegistry.Projected.pending("native LIFE command dispatch/catch does not prove that the engine received no command", List.of(archive.referenceOf(ack))));
            reason = "native_lifestyle_rejected_before_submit:" + failure + ":" + nativeReason;
        } else if (selected == Kind.COUNCIL) {
            StrictJson.object(result, Set.of("schema", "step", "accepted", "status", "query_sequence", "snapshot_revision", "council_assign_councillor_ack", "backend_id"));
            equal(result.get("schema"), "xar.ck3.council-application-main/v1"); equal(result.get("step"), "assign-councillor-v1");
            equal(result.get("backend_id"), "native-headless"); StrictJson.trueValue(result.get("accepted"));
            org.xar.ck3.control.governance.council.CouncilCodec.u64(result.get("query_sequence"), true); StrictJson.integer(result.get("snapshot_revision"), 0, 0);
            ObjectNode args = EffectJson.object(command.arguments()); var frame = command.before().frame();
            boolean had = EffectJson.bool(args.get("expected_has_incumbent")); int previous = (int) StrictJson.integer(args.get("expected_incumbent_character_id"), -1, Integer.MAX_VALUE);
            StrictJson.require(had ? previous > 0 : previous == -1, "Council original vacancy changed");
            var expected = new org.xar.ck3.control.governance.council.CouncilActionCodec.Request(attempt.requestId(),
                    new org.xar.ck3.control.governance.council.CouncilModels.Frame(frame.snapshotId(), frame.revision(), frame.identity().nativeRevision(), frame.identity().dateRaw().intValueExact(), frame.identity().player().intValueExact()),
                    org.xar.ck3.control.governance.council.CouncilModels.Position.exact(StrictJson.text(args.get("position_key"))),
                    Math.toIntExact(EffectJson.id(args.get("candidate_character_id"))), had ? java.util.OptionalInt.of(previous) : java.util.OptionalInt.empty());
            var helper = org.xar.ck3.control.governance.council.CouncilActionCodec.decodeAck(StrictJson.canonical(result.get("council_assign_councillor_ack")), expected);
            StrictJson.require(helper.status() == org.xar.ck3.control.governance.council.CouncilActionCodec.AckStatus.REJECTED_BEFORE_SUBMIT, "Council rejected envelope contains a submitted helper");
            if (helper.disposition() != org.xar.ck3.control.governance.council.CouncilActionCodec.HelperDisposition.REJECTED_WITHOUT_INVOCATION)
                return Optional.of(NativeEffectRegistry.Projected.pending("Council original helper remains unresolved: " + helper.disposition(), List.of(archive.referenceOf(ack))));
            reason = "native_council_rejected_before_submit:" + helper.failure();
        } else {
            var source = org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec.decodeReadback(StrictJson.canonical(EffectJson.object(command.arguments()).get("readback"))).sourceFrame();
            crownEnvelope(result, command.operation().value(), false, source.exactCk3Build(), source.exeSha256());
            var value = StrictJson.object(result.get("ack"), Set.of("submitted_request_id", "verification_pending", "failure", "player_character_id", "group_key", "previous_effective_law_key", "requested_law_key", "pre_public_revision", "pre_native_revision", "pre_proof_epoch", "pre_date_raw", "charges", "title_successors"));
            equal(value.get("submitted_request_id"), originalId(selected, attempt)); StrictJson.require(!EffectJson.bool(value.get("verification_pending")), "rejected Crown helper remains pending");
            equal(value.get("group_key"), "crown_authority"); equal(value.get("requested_law_key"), StrictJson.text(EffectJson.object(command.arguments()).get("law_key")));
            empty(value.get("previous_effective_law_key")); StrictJson.integer(value.get("player_character_id"), -1, -1);
            for (String key : List.of("pre_public_revision", "pre_native_revision", "pre_proof_epoch", "pre_date_raw")) StrictJson.integer(value.get(key), 0, 0);
            StrictJson.require(value.get("charges").isArray() && value.get("charges").isEmpty(), "rejected Crown ACK invented observed charges");
            var titles = StrictJson.object(value.get("title_successors"), Set.of("primary_title_id", "held_titles"));
            StrictJson.integer(titles.get("primary_title_id"), -1, -1); StrictJson.require(titles.get("held_titles").isArray() && titles.get("held_titles").isEmpty(), "rejected Crown ACK invented title successors");
            String failure = StrictJson.text(value.get("failure"));
            StrictJson.require(Set.of("request_contract_invalid", "exact_build_mismatch", "application_main_thread_required", "callbacks_unavailable", "observation_unavailable", "not_paused", "snapshot_unavailable", "stale_snapshot", "candidate_not_found", "authority_denied", "final_legality_denied", "resource_observation_invalid", "budget_not_authorized", "insufficient_resources", "state_changed_before_submit", "working_storage_unavailable", "native_submit_rejected").contains(failure), "unknown Crown rejection failure");
            if (failure.equals("working_storage_unavailable") || failure.equals("native_submit_rejected"))
                return Optional.of(NativeEffectRegistry.Projected.pending("Crown dispatch/catch failure retains its original request until independently reconciled", List.of(archive.referenceOf(ack))));
            reason = "native_crown_rejected_before_submit:" + failure;
        }
        var rejected = new ActionState.Rejected(attempt.requestId(), reason, archive.referenceOf(ack));
        ActionEffects.validate(command, attempt, rejected);
        return Optional.of(new NativeEffectRegistry.Projected(new ActionPorts.RejectionObserved(rejected), Optional.empty()));
    }
    private static void empty(JsonNode value) { StrictJson.require(value != null && value.isTextual() && value.textValue().isEmpty(), "exact empty native default string required"); }
    private static ObjectNode packet(byte[] bytes) {
        StrictJson.require(bytes != null && bytes.length >= 5 && bytes.length <= RawJson.MAXIMUM_BYTES + 4, "bounded complete actual Native packet required");
        int size = java.nio.ByteBuffer.wrap(bytes, 0, 4).order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt();
        StrictJson.require(size > 0 && size == bytes.length - 4, "actual Native packet length changed");
        return EffectJson.object(StrictJson.parse(java.util.Arrays.copyOfRange(bytes, 4, bytes.length)));
    }
    private static ObjectNode actualOriginal(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.AckReceived ack) {
        StrictJson.require(ack.requestId().equals(attempt.requestId()) && ack.outbound().isPresent(), "original native rejection outbound is missing or belongs to another attempt");
        ObjectNode actual = packet(ack.originalPacket());
        StrictJson.object(actual, Set.of("type", "protocol_version", "request_id", "ok", "result"));
        equal(actual.get("type"), "command_result"); StrictJson.integer(actual.get("protocol_version"), 1, 1); equal(actual.get("request_id"), attempt.requestId()); StrictJson.trueValue(actual.get("ok"));
        StrictJson.require(actual.equals(EffectJson.parse(ack.originalFrame())) && actual.get("result").equals(EffectJson.parse(ack.originalResultToken().orElseThrow())), "native rejection token/full packet differs");
        var wire = packet(ack.outbound().orElseThrow().originalPacket());
        var expected = EffectJson.object(EffectJson.parse(attempt.preparedRequest().additionalFields())).deepCopy();
        expected.put("type", "execute_step").put("protocol_version", 1).put("request_id", attempt.requestId()).put("step", attempt.preparedRequest().step()).put("expected_revision", attempt.guard().observed().frame().identity().nativeRevision());
        StrictJson.require(sameNativeWire(wire, expected) && attempt.preparedRequest().step().equals(command.operation().value()), "native rejection outbound differs from the canonical prepared primitive");
        var custody = ack.custody().orElseThrow(() -> new IllegalArgumentException("actual native rejection write/receive custody is unavailable"));
        custody.verify(ack, attempt.guard());
        StrictJson.require(!custody.writeEntered().observedAt().isBefore(attempt.submittedAt()), "native rejection dispatch predates the original canonical submission");
        return EffectJson.object(actual.get("result"));
    }
    static boolean sameNativeWire(ObjectNode actual, ObjectNode expected) {
        return java.util.Arrays.equals(StrictJson.canonical(actual), StrictJson.canonical(expected));
    }
    private static String originalId(Kind kind, ActionState.Attempt attempt) {
        ObjectNode prepared = EffectJson.object(EffectJson.parse(attempt.preparedRequest().additionalFields()));
        return kind == Kind.CROWN ? StrictJson.text(prepared.get("submitted_request_id")) : attempt.requestId();
    }
    private static void requirePreparedTarget(Kind kind, ActionCommand command, ActionState.Attempt attempt) {
        ObjectNode prepared = EffectJson.object(EffectJson.parse(attempt.preparedRequest().additionalFields()));
        ObjectNode args = EffectJson.object(command.arguments());
        StrictJson.require(attempt.preparedRequest().step().equals(command.operation().value()), "governance primitive differs from durable operation");
        if (kind == Kind.FOCUS || kind == Kind.PERK) {
            equal(prepared.get("target_key"), StrictJson.text(args.get("target_key")));
            equal(prepared.get("kind"), kind == Kind.FOCUS ? "focus" : "perk");
        } else if (kind == Kind.COUNCIL || kind == Kind.PRIVATE_COUNCIL) {
            equal(prepared.get("position_key"), StrictJson.text(args.get("position_key")));
            equal(prepared.get("candidate_character_id"), args.get("candidate_character_id"));
        } else equal(prepared.get("law_key"), StrictJson.text(args.get("law_key")));
    }
    private static void equal(JsonNode actual, String expected) { StrictJson.require(StrictJson.text(actual).equals(expected), "native receipt text identity changed"); }
    private static void equal(JsonNode actual, BigInteger expected) { StrictJson.require(EffectJson.integer(actual).equals(expected), "native receipt integer/frame identity changed"); }
    private static List<ExpectedValue> lifestyle(Kind kind, ActionCommand command, String requestId, Complete after, ObjectNode result) {
        StrictJson.object(result, Set.of("step", "private_build", "advertised", "status", "action_request_id", "post_snapshot_id", "episode_run_id", "post_public_revision", "post_target_perk_owned", "post_has_current_focus", "post_current_focus_key", "postcondition_verified", "reason"));
        ObjectNode args = EffectJson.object(command.arguments()); String target = StrictJson.text(args.get("target_key"));
        StrictJson.trueValue(result.get("private_build")); StrictJson.require(!EffectJson.bool(result.get("advertised")), "private LIFE flag drift");
        equal(result.get("action_request_id"), requestId); equal(result.get("post_snapshot_id"), "native:" + after.identity().frame().identity().nativeRevision());
        equal(result.get("post_public_revision"), after.identity().frame().identity().nativeRevision());
        equal(result.get("episode_run_id"), lifestyleWireEpisode(after.identity())); equal(result.get("status"), "applied");
        StrictJson.trueValue(result.get("postcondition_verified"));
        StrictJson.require(result.get("reason").isTextual() && result.get("reason").textValue().isEmpty(), "applied LIFE receipt carries a failure reason");
        EffectJson.bool(result.get("post_target_perk_owned")); EffectJson.bool(result.get("post_has_current_focus"));
        StrictJson.require(result.get("post_current_focus_key").isTextual(), "exact LIFE focus string required, including empty for absence");
        ArrayList<ExpectedValue> actual = new ArrayList<>(); actual.add(new ExpectedText(new FieldKey("lifestyle.target_key"), target));
        if (kind == Kind.FOCUS) {
            StrictJson.trueValue(result.get("post_has_current_focus")); equal(result.get("post_current_focus_key"), target);
            actual.add(new ExpectedBoolean(new FieldKey("lifestyle.has_current_focus"), true));
            actual.add(new ExpectedText(new FieldKey("lifestyle.current_focus_key"), StrictJson.text(result.get("post_current_focus_key"))));
        } else StrictJson.trueValue(result.get("post_target_perk_owned"));
        if (kind == Kind.PERK) actual.add(new ExpectedBoolean(new FieldKey("lifestyle.target_perk_owned"), true));
        actual.add(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true)); return List.copyOf(actual);
    }
    private static void lifestyleAck(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        StrictJson.require(dispatch instanceof NativeActionPort.AckReceived, "LIFE material receipt requires its original typed submit ACK");
        var ack = (NativeActionPort.AckReceived) dispatch;
        StrictJson.require(ack.nativeOk() && ack.originalResultToken().isPresent(), "LIFE submit result is unknown; no repeat or success attribution");
        ObjectNode result = StrictJson.object(EffectJson.parse(ack.originalResultToken().orElseThrow()), Set.of("step", "private_build", "advertised", "status", "verification_pending", "action_request_id", "target_key", "pre_snapshot_id", "episode_run_id", "pre_public_revision", "failure_class", "rejection_reason"));
        equal(result.get("step"), command.operation().value()); StrictJson.trueValue(result.get("private_build"));
        StrictJson.require(!EffectJson.bool(result.get("advertised")), "private LIFE submit advertised flag drift");
        equal(result.get("action_request_id"), attempt.requestId()); equal(result.get("status"), "submitted_verification_pending");
        StrictJson.trueValue(result.get("verification_pending")); equal(result.get("failure_class"), "none");
        StrictJson.require(result.get("rejection_reason").isTextual() && result.get("rejection_reason").textValue().isEmpty(), "pending LIFE ACK carries a rejection");
        equal(result.get("target_key"), StrictJson.text(EffectJson.object(command.arguments()).get("target_key")));
        equal(result.get("pre_snapshot_id"), "native:" + command.before().frame().identity().nativeRevision());
        equal(result.get("pre_public_revision"), command.before().frame().identity().nativeRevision());
        equal(result.get("episode_run_id"), lifestyleWireEpisode(command.before()));
    }
    private static List<ExpectedValue> council(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch,
            String id, Complete after, ObjectNode result) {
        StrictJson.require(dispatch instanceof NativeActionPort.AckReceived, "council original helper ACK required by its genuine receipt contract");
        NativeActionPort.AckReceived ack = (NativeActionPort.AckReceived) dispatch;
        StrictJson.require(ack.nativeOk() && ack.originalResultToken().isPresent(), "public Council native submit ACK is unconfirmed");
        ObjectNode original = EffectJson.object(EffectJson.parse(ack.originalResultToken().orElseThrow()));
        ObjectNode args = EffectJson.object(command.arguments()); String position = StrictJson.text(args.get("position_key")); long candidate = EffectJson.id(args.get("candidate_character_id"));
        var before = command.before().frame();
        boolean incumbentPresent = EffectJson.bool(args.get("expected_has_incumbent"));
        int incumbent = (int) StrictJson.integer(args.get("expected_incumbent_character_id"), -1, Integer.MAX_VALUE);
        StrictJson.require(incumbentPresent ? incumbent > 0 : incumbent == -1, "Council durable vacancy binding is inconsistent");
        var expected = new org.xar.ck3.control.governance.council.CouncilActionCodec.Request(id,
                new org.xar.ck3.control.governance.council.CouncilModels.Frame(before.snapshotId(), before.revision(), before.identity().nativeRevision(), before.identity().dateRaw().intValueExact(), before.identity().player().intValueExact()),
                org.xar.ck3.control.governance.council.CouncilModels.Position.exact(position), Math.toIntExact(candidate), incumbentPresent ? java.util.OptionalInt.of(incumbent) : java.util.OptionalInt.empty());
        var helper = org.xar.ck3.control.governance.council.CouncilActionCodec.decodeAck(StrictJson.canonical(original.get("council_assign_councillor_ack")), expected);
        StrictJson.require(helper.status() == org.xar.ck3.control.governance.council.CouncilActionCodec.AckStatus.HELPER_INVOKED_VERIFICATION_PENDING, "Council helper was rejected");
        var receipt = org.xar.ck3.control.governance.council.CouncilActionCodec.decodeReceipt(StrictJson.canonical(result.get("council_assign_councillor_receipt")), helper);
        StrictJson.require(receipt.status() == org.xar.ck3.control.governance.council.CouncilActionCodec.ReceiptStatus.APPLIED
                && receipt.postSnapshotId().equals(after.identity().frame().snapshotId()) && receipt.postPublicRevision().equals(after.identity().frame().revision())
                && receipt.postNativeRevision().equals(after.identity().frame().identity().nativeRevision()) && receipt.postDateRaw() == after.identity().frame().identity().dateRaw().intValueExact(), "Council independently observed post-frame drift");
        StrictJson.require(org.xar.ck3.control.governance.council.CouncilCodec.u64(result.get("query_sequence"), true)
                .compareTo(org.xar.ck3.control.governance.council.CouncilCodec.u64(original.get("query_sequence"), true)) > 0, "council receipt not later than helper mailbox sequence");
        equal(result.get("snapshot_revision"), after.identity().frame().identity().nativeRevision()); equal(result.get("status"), "applied");
        return List.of(new ExpectedText(new FieldKey("council.position_key"), position), new ExpectedInteger(new FieldKey("council.incumbent_character_id"), BigInteger.valueOf(candidate)), new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true));
    }
    private static void equal(JsonNode first, JsonNode second) {
        StrictJson.require(first != null && second != null && java.util.Arrays.equals(StrictJson.canonical(first), StrictJson.canonical(second)), "exact JSON-domain receipt binding changed");
    }
    private static List<ExpectedValue> crown(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch, String requestId, Complete after, ObjectNode result) {
        var readback = org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec.decodeReadback(StrictJson.canonical(EffectJson.object(command.arguments()).get("readback")));
        var source = readback.sourceFrame();
        crownEnvelope(result, CROWN_READ, true, source.exactCk3Build(), source.exeSha256());
        StrictJson.require(dispatch instanceof NativeActionPort.AckReceived, "Crown material receipt requires its original typed submit ACK");
        var ackDispatch = (NativeActionPort.AckReceived) dispatch;
        StrictJson.require(ackDispatch.nativeOk() && ackDispatch.originalResultToken().isPresent(), "Crown original submit result remains unknown");
        ObjectNode original = EffectJson.object(EffectJson.parse(ackDispatch.originalResultToken().orElseThrow()));
        crownEnvelope(original, command.operation().value(), false, source.exactCk3Build(), source.exeSha256());
        equal(original.get("status"), "submitted_verification_pending");
        ObjectNode ack = StrictJson.object(original.get("ack"), Set.of("submitted_request_id", "verification_pending", "failure", "player_character_id", "group_key", "previous_effective_law_key", "requested_law_key", "pre_public_revision", "pre_native_revision", "pre_proof_epoch", "pre_date_raw", "charges", "title_successors"));
        equal(ack.get("submitted_request_id"), requestId); StrictJson.trueValue(ack.get("verification_pending")); equal(ack.get("failure"), "none");
        equal(ack.get("player_character_id"), command.before().frame().identity().player()); equal(ack.get("group_key"), "crown_authority");
        equal(ack.get("previous_effective_law_key"), readback.activeLawKey());
        equal(ack.get("requested_law_key"), StrictJson.text(EffectJson.object(command.arguments()).get("law_key")));
        equal(ack.get("pre_public_revision"), command.before().frame().identity().nativeRevision()); equal(ack.get("pre_native_revision"), source.nativeSnapshotRevision());
        equal(ack.get("pre_proof_epoch"), source.proofEpoch()); equal(ack.get("pre_date_raw"), command.before().frame().identity().dateRaw());
        validateTitles(ack.get("title_successors"));
        StrictJson.trueValue(result.get("private_build")); StrictJson.require(!EffectJson.bool(result.get("advertised")), "private crown flag drift");
        StrictJson.trueValue(result.get("read_only")); equal(result.get("backend_id"), "native-headless"); equal(result.get("status"), "enacted");
        // The exact source-qualified contract plus assembler hello provenance binds the .4 build; no receipt self-reported build grants it.
        ObjectNode receipt = StrictJson.object(result.get("receipt"), Set.of("submitted_request_id", "failure", "post_public_revision", "post_native_revision", "post_proof_epoch", "post_date_raw", "effective_law_key", "effective_law_verified", "resources_verified", "succession_verified", "charges", "title_successors")); equal(receipt.get("submitted_request_id"), requestId);
        equal(receipt.get("failure"), "none"); equal(receipt.get("post_public_revision"), after.identity().frame().identity().nativeRevision());
        equal(receipt.get("post_native_revision"), after.identity().frame().identity().nativeRevision()); equal(receipt.get("post_date_raw"), after.identity().frame().identity().dateRaw());
        StrictJson.require(EffectJson.integer(receipt.get("post_proof_epoch")).compareTo(source.proofEpoch()) > 0, "Crown receipt is not a later proof epoch");
        equal(receipt.get("effective_law_key"), StrictJson.text(EffectJson.object(command.arguments()).get("law_key")));
        StrictJson.trueValue(receipt.get("effective_law_verified")); StrictJson.trueValue(receipt.get("resources_verified")); StrictJson.trueValue(receipt.get("succession_verified"));
        validateTitles(receipt.get("title_successors"));
        ArrayList<ExpectedValue> actual = new ArrayList<>(); actual.add(new ExpectedText(new FieldKey("crown.effective_law_key"), StrictJson.text(receipt.get("effective_law_key"))));
        var quotedCosts = org.xar.ck3.control.governance.crownauthority.CrownCallerSelection.quotedCosts(EffectJson.object(command.arguments()),readback);
        java.util.EnumMap<org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Currency, BigInteger> quoted = new java.util.EnumMap<>(org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Currency.class);
        quotedCosts.forEach(amount -> quoted.put(amount.currency(), amount.amountRaw()));
        java.util.EnumMap<org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Currency, BigInteger> balances = new java.util.EnumMap<>(org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Currency.class);
        readback.resources().forEach(balance -> balances.put(balance.currency(), balance.amountRaw()));
        Set<String> seen = new HashSet<>(); for (JsonNode rawCharge : EffectJson.rows(receipt.get("charges"))) {
            ObjectNode charge = StrictJson.object(rawCharge, Set.of("currency_key", "cost_raw", "pre_balance_raw", "post_balance_raw"));
            String currency = StrictJson.text(charge.get("currency_key")); StrictJson.require(List.of("gold", "prestige", "piety", "influence", "merit").contains(currency) && seen.add(currency), "duplicate/unsupported actual crown charge");
            BigInteger before = signed(charge.get("pre_balance_raw")), cost = signed(charge.get("cost_raw")), balance = signed(charge.get("post_balance_raw"));
            StrictJson.require(cost.signum() >= 0 && before.compareTo(cost) >= 0 && balance.equals(before.subtract(cost)), "crown exact observed charge did not match wallet debit");
            var key = org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Currency.fromWire(currency);
            StrictJson.require(cost.equals(quoted.get(key)) && before.equals(balances.get(key)), "Crown actual debit differs from its bound native quote/pre-wallet");
            actual.add(new ExpectedText(new FieldKey("crown.balance_" + currency + "_raw"), balance.toString()));
        }
        StrictJson.require(seen.equals(quoted.keySet().stream().map(org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Currency::wire).collect(java.util.stream.Collectors.toSet())), "Crown receipt omitted or invented a quoted resource");
        actual.add(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true)); return List.copyOf(actual);
    }
    private static void crownEnvelope(ObjectNode value, String step, boolean readOnly, String version, String sha256) {
        StrictJson.object(value, Set.of("step", "accepted", "private_build", "advertised", "backend_id", "game_version", "executable_sha256", "read_only", "status", "observation", "ack", "receipt"));
        equal(value.get("step"), step); StrictJson.trueValue(value.get("accepted")); StrictJson.trueValue(value.get("private_build"));
        StrictJson.require(!EffectJson.bool(value.get("advertised")) && EffectJson.bool(value.get("read_only")) == readOnly, "Crown private/read-only envelope drift");
        equal(value.get("backend_id"), "native-headless"); equal(value.get("game_version"), version); equal(value.get("executable_sha256"), sha256);
        org.xar.ck3.control.governance.council.CouncilCodec.requireBuild(version, sha256);
        StrictJson.require(value.get("observation").isNull() && (readOnly ? value.get("ack").isNull() : value.get("receipt").isNull()), "Crown action/receipt envelope mixes observation or another phase");
    }
    private static BigInteger signed(JsonNode value) { return StrictJson.integer(value, BigInteger.valueOf(Long.MIN_VALUE), BigInteger.valueOf(Long.MAX_VALUE)); }
    public static void validateTitles(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("primary_title_id", "held_titles")); long primary = EffectJson.id(row.get("primary_title_id")); List<JsonNode> titles = EffectJson.rows(row.get("held_titles"));
        StrictJson.require(!titles.isEmpty() && titles.size() <= 32, "complete bounded held-title successor observation required");
        Set<Long> ids = new HashSet<>(); int primaryCount = 0;
        for (JsonNode title : titles) {
            StrictJson.object(title, Set.of("title_id", "primary", "successor_character_ids"));
            long id = EffectJson.id(title.get("title_id")); StrictJson.require(ids.add(id), "duplicate held title identity");
            if (EffectJson.bool(title.get("primary"))) { primaryCount++; StrictJson.require(id == primary, "primary title identity drift"); }
            JsonNode successors = title.get("successor_character_ids"); StrictJson.require(successors != null && successors.isArray() && successors.size() <= 32, "bounded ordered successor IDs required");
            Set<Long> unique = new HashSet<>(); for (JsonNode successor : successors) StrictJson.require(unique.add(EffectJson.id(successor)), "duplicate successor full identity");
        }
        StrictJson.require(primaryCount == 1, "exact one current primary title required");
    }
}

