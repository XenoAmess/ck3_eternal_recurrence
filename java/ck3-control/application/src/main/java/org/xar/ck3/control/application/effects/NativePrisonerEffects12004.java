package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.prisoners.PrisonerActionBinding12004;
import org.xar.ck3.control.application.planning.prisoners.PrisonerOrdinaryPolicy12004;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerMaterial12004;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;

/** Independent current custody and actual-wallet consumer. ACK/generic RED never supplies a material result. */
public final class NativePrisonerEffects12004 implements NativeEffectRegistry.Observer {
    private final NativeEffectSnapshots snapshots;
    private final PlanningReadPort reads;
    private final ReadContract<RawJson> collection;
    private final PrisonerActionBinding12004 preparation;
    private final ActionPorts.OutcomeArchive archive;
    public NativePrisonerEffects12004(NativeEffectSnapshots snapshots, PlanningReadPort reads,
            ReadContract<RawJson> collection, PrisonerActionBinding12004 preparation, ActionPorts.OutcomeArchive archive) {
        this.snapshots = Objects.requireNonNull(snapshots); this.reads = Objects.requireNonNull(reads);
        this.collection = Objects.requireNonNull(collection); this.preparation = Objects.requireNonNull(preparation);
        this.archive = Objects.requireNonNull(archive);
        StrictJson.require(collection.operation().value().equals("query-player-prisoner-collection-private-v1"), "actual native-family ordinal-zero contract required");
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        requirePrepared(command, attempt); var pair = snapshots.read(command, attempt);
        JsonNode args = parse(command.arguments()); long target = PrisonerActionBinding12004.id(args.get("prisoner_character_id"));
        boolean release = command.operation().equals(PrisonerOrdinaryPolicy12004.RELEASE);
        var intent = new PrisonerOptionIntent.Arguments(new PrisonerOptionIntent.Unconditional(), release ? OptionalLong.of(target) : OptionalLong.empty());
        var arguments = OpportunityJson.object(OpportunityJson.parse(PrisonerOptionIntent.encode(intent)), "actual postcondition query arguments");
        var after = pair.after(); var request = new PlanningReadRequest(after.identity(), after.source(), after.sessionId(), collection.operation(), arguments, ActionObservationWindow.deadline(command));
        PlanningReadResult<RawJson> result = reads.read(collection, request);
        if (!(result instanceof PlanningReadResult.Known<RawJson> known))
            return NativeEffectRegistry.Projected.pending("independent prisoner collection unavailable; original UNKNOWN retained", List.of(after.originalEvidence()));
        var projected = project(command, attempt, dispatch, pair, known.receipt(), collection.decode(known.receipt()), preparation, collection, archive, Optional.empty());
        if (!(projected.result() instanceof ActionPorts.EffectObserved)) return projected;
        return NativeEffectSnapshots.withEvidence(projected, List.of(snapshots.evidence(command, attempt, pair,
                List.of(known.receipt()), projected.compatibleResult().orElseThrow())));
    }
    private static NativeEffectRegistry.Projected project(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch,
            NativeEffectSnapshots.Pair pair, PlanningReadReceipt read, RawJson normalized,
            PrisonerActionBinding12004 preparation, ReadContract<RawJson> collection, ActionPorts.OutcomeArchive archive, Optional<ExactRef> terminalReplayBasis) {
        requirePrepared(command, attempt); StrictJson.require(preparation.prepare(command).equals(attempt.preparedRequest()), "prepared prisoner primitive differs from original selected offer");
        var after = pair.after(); NativeEffectSnapshots.requireAfterRead(command, attempt, after, read, collection.operation());
        StrictJson.require(read.contractId().equals(collection.contractId()), "independent collection registration differs");
        JsonNode args = parse(command.arguments()); long target = PrisonerActionBinding12004.id(args.get("prisoner_character_id"));
        boolean release = command.operation().equals(PrisonerOrdinaryPolicy12004.RELEASE);
        var intent = PrisonerOptionIntent.decode(OpportunityJson.encode(read.request().arguments()));
        StrictJson.require(intent.options() instanceof PrisonerOptionIntent.Unconditional
                && (release ? intent.materialTarget().isPresent() && intent.materialTarget().getAsLong() == target : intent.materialTarget().isEmpty()),
                "independent collection changed exact original receipt target");
        JsonNode value = StrictJson.parse(normalized.bytes(), 1_048_576);
        var post = new PrisonerMaterial12004.Frame(after.identity().frame().identity().nativeRevision(),
                after.identity().frame().identity().dateRaw().intValueExact(), after.identity().frame().identity().player().longValueExact(), target);
        ObjectNode compatible;
        if (release) {
            var custody = PrisonerMaterial12004.decodeCustody(value.get("prisoner_retained_target_state"), post);
            if (!(custody instanceof PrisonerMaterial12004.Free)) {
                String status = custody instanceof PrisonerMaterial12004.Dead ? "dead" : custody instanceof PrisonerMaterial12004.HeldByOther
                        ? "transferred" : custody instanceof PrisonerMaterial12004.UnavailableCustody ? "unavailable" : "pending";
                if (custody instanceof PrisonerMaterial12004.Dead || custody instanceof PrisonerMaterial12004.HeldByOther) {
                    ObjectNode terminal = base(command, target, after).put("schema", "xar.ck3.prisoner-release-independent-receipt-12004-v1")
                            .put("status", status).put("material_result", false).put("postcondition_verified", false)
                            .put("release_causation_observed", false).put("command_costs_verified", false).put("unavailable_reason", "");
                    terminal.set("current_target_state", value.get("prisoner_retained_target_state")); terminal.set("independent_readback", value);
                    var selected = preparation.selected(command);
                    material(selected.normalized(), value, command, target, post, terminal);
                    return PrisonerTerminalEvidence12004.project(command, attempt, dispatch, pair, selected.receipt(), read, custody,
                            new RawJson(StrictJson.canonical(terminal, 1_048_576)), archive, terminalReplayBasis);
                }
                return NativeEffectRegistry.Projected.pending("independent prisoner custody=" + status + "; no freedom or causation credited; original action is never replayed", List.of(after.originalEvidence()));
            }
            compatible = base(command, target, after).put("schema", "xar.ck3.prisoner-release-independent-receipt-12004-v1")
                    .put("release_causation_observed", false).put("command_costs_verified", false).put("unavailable_reason", "");
            compatible.set("current_target_state", value.get("prisoner_retained_target_state"));
            material(preparation.selected(command).normalized(), value, command, target, post, compatible);
        } else {
            BigInteger observedBefore = PrisonerActionBinding12004.gold(pair.before().semantic());
            BigInteger observedAfter = PrisonerActionBinding12004.gold(after.semantic());
            StrictJson.require(observedBefore.equals(PrisonerActionBinding12004.signed(args.get("pre_player_gold_raw"))), "retained actual wallet baseline differs from durable ransom command");
            JsonNode rows = value.path("player_prisoner_collection").get("prisoners");
            StrictJson.require(rows != null && rows.isArray() && value.path("player_prisoner_collection").path("collection_complete").isBoolean()
                    && value.path("player_prisoner_collection").path("collection_complete").booleanValue(), "complete independent custody collection unavailable");
            boolean held = false;
            for (JsonNode row : rows) if (PrisonerActionBinding12004.id(row.get("prisoner_character_id")) == target) held = true;
            BigInteger gain = observedAfter.subtract(observedBefore);
            boolean acceptanceTime = booleanValue(args.get("amount_is_acceptance_time_quote"));
            StrictJson.require(acceptanceTime == StrictJson.text(args.get("selected_option")).equals("current_gold"), "durable ransom option timing differs");
            BigInteger quoted = StrictJson.integer(args.get("quoted_gold_raw"), BigInteger.ONE, BigInteger.valueOf(Long.MAX_VALUE));
            if (!ransomMaterialObserved(held, observedBefore, observedAfter, quoted, acceptanceTime))
                return NativeEffectRegistry.Projected.pending("independent ransom custody/wallet remains " + (held ? "pending" : "ambiguous")
                        + "; disappearance or ACK alone is not payment", List.of(after.originalEvidence()));
            compatible = base(command, target, after).put("prisoner_no_longer_held", true)
                    .put("observed_player_gold_gain_raw", gain).put("quoted_gold_raw", quoted)
                    .put("amount_is_acceptance_time_quote", acceptanceTime);
        }
        compatible.set("independent_readback", value);
        List<ExpectedValue> actual = PrisonerActionBinding12004.expected(command.before(), command.source(), command.operation(), target).values();
        return NativeEffectSnapshots.observed(command, attempt, after, PrisonerActionBinding12004.SCHEMA, actual,
                read.requestId(), new RawJson(StrictJson.canonical(compatible, 1_048_576)), List.of());
    }
    /** Same actual receipt consumer used by held observation; original producers/physical archive remain mandatory. */
    public static NativeEffectRegistry.Projected projectOriginals(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch, NativeEffectSnapshots.Pair pair, PlanningReadReceipt afterRead,
            PrisonerActionBinding12004 preparation, ReadContract<RawJson> actualCollection, ActionPorts.OutcomeArchive archive) {
        return project(command, attempt, dispatch, pair, afterRead, actualCollection.decode(afterRead), preparation,
                actualCollection, archive, Optional.empty());
    }
    public static NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation, ExactRef source,
            NativeEffectEvidence.FrameLoader frames, ReadContract<RawJson> actualCollection, PrisonerActionBinding12004 preparation) {
        PrisonerActionBinding12004.requireOperation(operation); Objects.requireNonNull(frames); Objects.requireNonNull(actualCollection); Objects.requireNonNull(preparation);
        return new NativeRecordedEvidenceVerifier.Binding(operation, source, (head, receipt, archive) -> {
            if (receipt.state() instanceof ActionState.Settled terminalState && terminalState.settlement() instanceof ActionState.NonAppliedTerminal terminal) {
                var original = PrisonerTerminalEvidence12004.load(receipt, archive, frames);
                var replayed = project(receipt.command(), terminalState.attempt(), original.dispatch(), original.frames(), original.after(),
                        actualCollection.decode(original.after()), preparation.withArchive(archive), actualCollection, archive, Optional.of(original.basis()));
                PrisonerTerminalEvidence12004.requireSame(terminal, replayed, original.compatible(), archive); return;
            }
            var originals = NativeEffectEvidence.load(receipt, archive, frames); var settled = (ActionState.Settled) receipt.state();
            StrictJson.require(originals.independentReads().size() == 1, "one original independent prisoner collection required");
            var read = originals.independentReads().getFirst();
            var replayed = project(receipt.command(), settled.attempt(), settled.dispatch(), originals.frames(), read, actualCollection.decode(read), preparation.withArchive(archive), actualCollection, archive, Optional.empty());
            replayed = NativeEffectSnapshots.withEvidence(replayed, ((ActionState.Applied) settled.settlement()).observation().supportingEvidence());
            NativeEffectEvidence.requireSame(settled.settlement(), replayed, originals.compatibleResult());
        });
    }
    private static void material(RawJson selected, JsonNode after, ActionCommand command, long target,
            PrisonerMaterial12004.Frame post, ObjectNode result) {
        JsonNode before = StrictJson.parse(selected.bytes(), 1_048_576).get("prisoner_release_material_opinion");
        if (before == null) {
            result.putNull("release_material_opinion_comparison").put("release_material_opinion_comparison_unavailable_reason", "before_material_not_observed"); return;
        }
        try {
            var frame = command.before().frame().identity();
            var pre = new PrisonerMaterial12004.Frame(frame.nativeRevision(), frame.dateRaw().intValueExact(), frame.player().longValueExact(), target);
            var one = PrisonerMaterial12004.decodeReleaseMaterial(before, pre);
            var two = PrisonerMaterial12004.decodeReleaseMaterial(after.get("prisoner_release_material_opinion"), post);
            if (!(one instanceof PrisonerMaterial12004.AvailableMaterial initial) || !(two instanceof PrisonerMaterial12004.AvailableMaterial current)) {
                result.putNull("release_material_opinion_comparison").put("release_material_opinion_comparison_unavailable_reason", "material_pair_unavailable"); return;
            }
            var comparison = PrisonerMaterial12004.compare(initial, current);
            result.putObject("release_material_opinion_comparison").put("schema", "xar.ck3.prisoner-release-material-opinion-comparison-12004-v1")
                    .put("actor_character_id", pre.actor()).put("target_character_id", target)
                    .put("pre_date_raw", pre.dateRaw()).put("post_date_raw", post.dateRaw())
                    .put("observed_total_opinion_delta", comparison.totalOpinionDelta())
                    .put("observed_released_from_prison_delta", comparison.namedModifierDelta()).put("named_relation_improved", comparison.namedRelationImproved())
                    .put("release_causation_observed", false).put("custody_change_observed", false);
            result.putNull("release_material_opinion_comparison_unavailable_reason");
        } catch (IllegalArgumentException rejected) {
            result.putNull("release_material_opinion_comparison").put("release_material_opinion_comparison_unavailable_reason", "material_pair_source_or_target_rejected");
        }
    }
    private static ObjectNode base(ActionCommand command, long target, org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete after) {
        ObjectNode result = StrictJson.object().put("status", "applied").put("material_result", true).put("postcondition_verified", true)
                .put("player_character_id", command.before().frame().identity().player()).put("prisoner_character_id", target)
                .put("post_native_revision", after.identity().frame().identity().nativeRevision()).put("post_date_raw", after.identity().frame().identity().dateRaw());
        result.set("source_pending", parse(command.arguments())); return result;
    }
    private static void requirePrepared(ActionCommand command, ActionState.Attempt attempt) {
        PrisonerActionBinding12004.requireOperation(command.operation());
        StrictJson.require(attempt.preparedRequest().step().equals(command.operation().value()), "durable prisoner primitive differs from operation");
    }
    /** Original Python current_gold observes acceptance-time gain; a paused quote is not its exact later payment. */
    public static boolean ransomMaterialObserved(boolean held, BigInteger before, BigInteger after, BigInteger quoted, boolean acceptanceTime) {
        Objects.requireNonNull(before); Objects.requireNonNull(after); Objects.requireNonNull(quoted);
        StrictJson.require(quoted.signum() > 0, "positive actual quote required");
        BigInteger gain = after.subtract(before);
        return !held && (acceptanceTime ? gain.signum() > 0 : gain.compareTo(quoted) >= 0);
    }
    private static JsonNode parse(OpportunityJson.Obj value) { return StrictJson.parse(OpportunityJson.encode(value), ActionCommand.MAX_ARGUMENT_BYTES); }
    private static boolean booleanValue(JsonNode value) { StrictJson.require(value != null && value.isBoolean(), "actual boolean required"); return value.booleanValue(); }
}
