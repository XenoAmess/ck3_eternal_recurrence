package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Locale;
import java.util.ArrayList;
import java.util.Objects;
import java.util.Optional;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.military.ActiveRetreatProposal;
import org.xar.ck3.control.application.planning.military.ActiveRetreatState;
import org.xar.ck3.control.application.planning.military.ActiveRetreatPost;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatMoveRequest;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatPreflightVerifier;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatPostReadCollector;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original _execute_typed_move_army/_army_move_postcondition semantics; route admission is not arrival. */
public final class NativeArmyMoveEffects implements NativeEffectRegistry.Observer {
    public static final String SCHEMA = "xar.ck3.native-army-move-postcondition/v1";
    public static final String RETREAT_SCHEMA = "xar.ck3.native-active-retreat-move-postcondition/v1";
    private static final Pattern STEP = Pattern.compile("move-army-(0|[1-9][0-9]{0,9})-to-([1-9][0-9]{0,9})");
    public record Move(int armyId, int provinceId) {
        public Move { StrictJson.require(armyId >= 0 && provinceId > 0, "public CUnit including zero and positive province identity required"); }
    }
    public enum State { MOVING, ARRIVED, RETREATING, NOT_OBSERVED }
    @FunctionalInterface private interface MaterialReader { RawJson load(ExactRef reference); }
    private final NativeEffectSnapshots snapshots;
    private final Optional<ArmyRetreatPreflightVerifier> retreatPreflight;
    private final Optional<ArmyRetreatPostReadCollector> retreatPost;
    public NativeArmyMoveEffects(NativeEffectSnapshots snapshots) { this.snapshots = Objects.requireNonNull(snapshots); this.retreatPreflight = Optional.empty(); this.retreatPost = Optional.empty(); }
    public NativeArmyMoveEffects(NativeEffectSnapshots snapshots, ArmyRetreatPreflightVerifier actualRetreatPreflight) {
        this.snapshots = Objects.requireNonNull(snapshots); this.retreatPreflight = Optional.of(Objects.requireNonNull(actualRetreatPreflight));
        this.retreatPost = Optional.empty();
    }
    public NativeArmyMoveEffects(NativeEffectSnapshots snapshots, ArmyRetreatPreflightVerifier actualRetreatPreflight,
            ArmyRetreatPostReadCollector actualRetreatPost) {
        this.snapshots = Objects.requireNonNull(snapshots); this.retreatPreflight = Optional.of(Objects.requireNonNull(actualRetreatPreflight));
        this.retreatPost = Optional.of(Objects.requireNonNull(actualRetreatPost));
    }
    public static Move parse(OperationKey operation) {
        var match = STEP.matcher(operation.value()); StrictJson.require(match.matches(), "canonical exact move-army operation required");
        return new Move(new BigInteger(match.group(1)).intValueExact(), new BigInteger(match.group(2)).intValueExact());
    }
    public static ExpectedPostcondition expected(ObservationIdentity before, G2Source source, OperationKey operation) {
        Move move = parse(operation);
        return new ExpectedPostcondition(1, before, source, SCHEMA, List.of(
                new ExpectedInteger(new FieldKey("army_id"), BigInteger.valueOf(move.armyId())),
                new ExpectedInteger(new FieldKey("target_province_id"), BigInteger.valueOf(move.provinceId())),
                new ExpectedBoolean(new FieldKey("order_observed"), true)));
    }
    public static ExpectedPostcondition expectedRetreat(ObservationIdentity before, G2Source source, OperationKey operation) {
        Move move = parse(operation);
        return new ExpectedPostcondition(1, before, source, RETREAT_SCHEMA, List.of(
                new ExpectedInteger(new FieldKey("army_id"), BigInteger.valueOf(move.armyId())),
                new ExpectedInteger(new FieldKey("target_province_id"), BigInteger.valueOf(move.provinceId())),
                new ExpectedBoolean(new FieldKey("retreat_order_observed"), true)));
    }
    private static boolean retreat(ActionCommand command) { return command.expected().observerSchema().equals(RETREAT_SCHEMA); }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        if (retreat(command) && !ActionReconciliationScope.activeFor(command))
            return NativeEffectRegistry.Projected.pending("retreat requires its actual original-pending lifecycle observation lease", List.of(attempt.guard().nativeEvidence()));
        var pair = snapshots.read(command, attempt);
        var request = retreat(command) ? Optional.of(ArmyRetreatMoveRequest.decode(command.arguments())) : Optional.<ArmyRetreatMoveRequest>empty();
        var retained = new ArrayList<PlanningReadReceipt>();
        request.ifPresent(value -> retained.addAll(snapshots.reads(value.preflightReads())));
        if (request.isPresent()) snapshots.withArchive(archive -> {
            var actualPost = retreatPost.orElseThrow(() -> new IllegalStateException("actual retreat lifecycle post reader is not installed"));
            List<PlanningReadReceipt> actualReads = List.copyOf(actualPost.collect(command, attempt, pair, archive));
            StrictJson.require(actualReads.size() >= 1 && actualReads.size() <= 2, "retreat requires its transition and only conditionally its terminal query");
            actualReads.forEach(read -> NativeRecordedEvidenceVerifier.requireRead(read, archive)); retained.addAll(actualReads); return null;
        });
        List<PlanningReadReceipt> reads = List.copyOf(retained);
        var projected = snapshots.withArchive(archive -> project(command, attempt, dispatch, pair, snapshots::material, reads, retreatPreflight, retreatPost, archive));
        if (!(projected.result() instanceof ActionPorts.EffectObserved)) return projected;
        List<ExactRef> materials = request.map(value -> List.of(value.previewBody())).orElseGet(List::of);
        ExactRef basis = snapshots.evidence(command, attempt, pair, reads, projected.compatibleResult().orElseThrow(), materials);
        List<ExactRef> closure = new ArrayList<>(); closure.add(basis); closure.addAll(materials);
        return NativeEffectSnapshots.withEvidence(projected, closure);
    }
    private static NativeEffectRegistry.Projected project(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch, NativeEffectSnapshots.Pair pair, MaterialReader materials,
            List<PlanningReadReceipt> originalReads, Optional<ArmyRetreatPreflightVerifier> preflight,
            Optional<ArmyRetreatPostReadCollector> post, ActionPorts.OutcomeArchive archive) {
        Move move = parse(command.operation());
        ObjectNode before = EffectJson.object(pair.before().semantic()), after = EffectJson.object(pair.after().semantic());
        boolean retreat = retreat(command);
        State state;
        if (retreat) {
            StrictJson.require(originalReads.size() >= 3 && originalReads.size() <= 4, "retreat original closure requires two preflight and one or two post reads");
            List<PlanningReadReceipt> preflightReads = originalReads.subList(0, 2), postReads = originalReads.subList(2, originalReads.size());
            var request = ArmyRetreatMoveRequest.decode(command.arguments()); RawJson raw = materials.load(request.previewBody());
            RootGuardChecks.exact(request.previewBody(), raw.bytes());
            StrictJson.require(preflightReads.size() == 2 && request.preflightReads().equals(preflightReads.stream().map(archive::readReferenceOf).toList()), "retreat original preflight receipt identities changed");
            preflight.orElseThrow(() -> new IllegalStateException("actual source-bound retreat preflight decoder is not installed")).verify(request, pair.before(), preflightReads, archive);
            var domain = ActiveRetreatState.decode(org.xar.ck3.control.application.driver.DriverJson.object(raw.bytes(), org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES));
            var preview = domain.preview().orElseThrow(() -> new IllegalArgumentException("original pre-claim retreat preview is missing"));
            StrictJson.require(domain.pending().isEmpty(), "retreat child must retain the original pre-claim preview body");
            StrictJson.require(request.order().source().connectionGeneration().equals(pair.before().connectionGeneration()), "retreat source connection changed");
            state = verifyRetreat(move, request.order(), preview, before, after);
            ActiveRetreatPost.Result actualPost = Objects.requireNonNull(post.orElseThrow(
                    () -> new IllegalStateException("actual retreat lifecycle archived verifier is not installed"))
                    .verifyArchived(command, attempt, pair, postReads, archive));
            if (actualPost instanceof ActiveRetreatPost.Pending pending) {
                var originals = new ArrayList<ExactRef>(); originals.add(pair.after().originalEvidence());
                postReads.forEach(read -> originals.add(archive.readReferenceOf(read)));
                return NativeEffectRegistry.Projected.pending(pending.reason(), List.copyOf(originals));
            }
            StrictJson.require(actualPost instanceof ActiveRetreatPost.Observed observed
                    && observed.after().equals(ActiveRetreatProposal.SourceFrame.read(pair.after().semantic())),
                    "retreat lifecycle result differs from the actual after frame");
        } else {
            StrictJson.require(command.expected().observerSchema().equals(SCHEMA) && originalReads.isEmpty(), "ordinary move cannot borrow a different postcondition schema");
            state = verify(move, before, after);
        }
        if (state == State.NOT_OBSERVED) return NativeEffectRegistry.Projected.pending("requested owned army route/arrival is not independently observed", List.of(pair.after().originalEvidence()));
        ObjectNode result = StrictJson.object(); result.put("step", command.operation().value());
        // This records the independent material observation, not a manufactured Native ACK.
        result.put("native_ack_verified", dispatch instanceof NativeActionPort.AckReceived ack && ack.nativeOk());
        String status = state == State.RETREATING ? "retreating" : state == State.ARRIVED ? "arrived" : "moving";
        ObjectNode action = result.putObject("war_action"); action.put("status", status);
        action.put("army_id", move.armyId()); action.put("target_province_id", move.provinceId()); action.put("postcondition_verified", true);
        result.put("snapshot_id", pair.after().identity().frame().snapshotId());
        var actual = List.<ExpectedValue>of(new ExpectedInteger(new FieldKey("army_id"), BigInteger.valueOf(move.armyId())),
                new ExpectedInteger(new FieldKey("target_province_id"), BigInteger.valueOf(move.provinceId())),
                new ExpectedBoolean(new FieldKey(retreat ? "retreat_order_observed" : "order_observed"), true),
                new ExpectedText(new FieldKey("war_action.status"), status));
        return NativeEffectSnapshots.observed(command, attempt, pair.after(), retreat ? RETREAT_SCHEMA : SCHEMA, actual,
                NativeEffectSnapshots.publication(pair.after()), EffectJson.raw(result), List.of());
    }
    public static NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation, org.xar.ck3.control.contracts.ExactRef source, NativeEffectEvidence.FrameLoader frames) {
        return archivedVerifier(operation, source, frames, Optional.empty(), Optional.empty());
    }
    public static NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation, ExactRef source, NativeEffectEvidence.FrameLoader frames, ArmyRetreatPreflightVerifier actualRetreatPreflight) {
        return archivedVerifier(operation, source, frames, Optional.of(Objects.requireNonNull(actualRetreatPreflight)), Optional.empty());
    }
    public static NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation, ExactRef source, NativeEffectEvidence.FrameLoader frames,
            ArmyRetreatPreflightVerifier actualRetreatPreflight, ArmyRetreatPostReadCollector actualRetreatPost) {
        return archivedVerifier(operation, source, frames, Optional.of(Objects.requireNonNull(actualRetreatPreflight)), Optional.of(Objects.requireNonNull(actualRetreatPost)));
    }
    private static NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation, ExactRef source, NativeEffectEvidence.FrameLoader frames,
            Optional<ArmyRetreatPreflightVerifier> actualRetreatPreflight, Optional<ArmyRetreatPostReadCollector> actualRetreatPost) {
        parse(operation); java.util.Objects.requireNonNull(frames);
        return new NativeRecordedEvidenceVerifier.Binding(operation, source, (head, receipt, archive) -> {
            var original = NativeEffectEvidence.load(receipt, archive, frames); var settled = (ActionState.Settled) receipt.state();
            if (retreat(receipt.command())) {
                var request = ArmyRetreatMoveRequest.decode(receipt.command().arguments());
                StrictJson.require(original.supportingMaterials().equals(List.of(request.previewBody())), "retreat preview custody differs from its original command");
            } else StrictJson.require(original.independentReads().isEmpty() && original.supportingMaterials().isEmpty(), "ordinary army route projection cannot borrow retreat evidence");
            var replayed = project(receipt.command(), settled.attempt(), settled.dispatch(), original.frames(), archive::loadMaterial, original.independentReads(), actualRetreatPreflight, actualRetreatPost, archive);
            replayed = NativeEffectSnapshots.withEvidence(replayed, ((ActionState.Applied) settled.settlement()).observation().supportingEvidence());
            NativeEffectEvidence.requireSame(settled.settlement(), replayed, original.compatibleResult());
        });
    }
    public static State verify(Move move, ObjectNode before, ObjectNode after) {
        long actor = EffectJson.id(EffectJson.object(before.get("played_character")).get("character_id"));
        StrictJson.require(actor == EffectJson.id(EffectJson.object(after.get("played_character")).get("character_id")), "army actor drift");
        for (ObjectNode frame : List.of(before, after)) {
            StrictJson.trueValue(frame.get("paused")); StrictJson.trueValue(frame.get("map_ready"));
            StrictJson.trueValue(EffectJson.object(frame.get("played_character")).get("alive"));
            StrictJson.require(EffectJson.integer(frame.get("date_raw")).equals(EffectJson.integer(before.get("date_raw"))), "move crossed its paused action date");
        }
        JsonNode original = army(before, move.armyId());
        JsonNode current = army(after, move.armyId());
        StrictJson.require(original != null, "original selected army missing"); owned(original, actor);
        if (current == null) return State.NOT_OBSERVED; owned(current, actor);
        long position = EffectJson.id(current.get("current_province_id"));
        if (EffectJson.id(original.get("current_province_id")) == move.provinceId()) {
            boolean clear = current.has("move_target_province_id") && current.get("move_target_province_id").isNull()
                    && current.has("route_province_ids") && current.get("route_province_ids").isArray() && current.get("route_province_ids").isEmpty();
            return position == move.provinceId() && clear && stationary(current)
                    && EffectJson.integer(after.get("revision")).compareTo(EffectJson.integer(before.get("revision"))) > 0
                    && EffectJson.integer(after.get("native_revision")).compareTo(EffectJson.integer(before.get("native_revision"))) > 0 ? State.ARRIVED : State.NOT_OBSERVED;
        }
        if (position == move.provinceId()) return State.ARRIVED;
        JsonNode target = current.get("move_target_province_id"), route = current.get("route_province_ids");
        if (target == null || target.isNull() || EffectJson.id(target) != move.provinceId()) return State.NOT_OBSERVED;
        StrictJson.require(route != null && route.isArray(), "actual route list missing");
        for (JsonNode province : route) EffectJson.id(province);
        return !route.isEmpty() && EffectJson.id(route.get(route.size() - 1)) == move.provinceId() ? State.MOVING : State.NOT_OBSERVED;
    }
    /** Explicit retreat semantics are not an exception inside ordinary movement. */
    public static State verifyRetreat(Move move, ActiveRetreatProposal.Order order, OpportunityJson.Obj preview,
            ObjectNode before, ObjectNode after) {
        long actor = EffectJson.id(EffectJson.object(before.get("played_character")).get("character_id"));
        StrictJson.require(actor == order.selectedOwnerCharacterId() && actor == EffectJson.id(EffectJson.object(after.get("played_character")).get("character_id")), "retreat actor/owner changed");
        for (var frame : List.of(before, after)) {
            StrictJson.trueValue(frame.get("paused")); StrictJson.trueValue(frame.get("map_ready"));
            StrictJson.trueValue(EffectJson.object(frame.get("played_character")).get("alive"));
            StrictJson.require(EffectJson.integer(frame.get("date_raw")).equals(order.source().dateRaw()), "retreat child crossed its original paused date");
        }
        var beforeSource = source(before); var afterSource = source(after);
        StrictJson.require(order.source().equals(beforeSource) && afterSource.episodeRunId().equals(beforeSource.episodeRunId())
                && afterSource.connectionGeneration().equals(beforeSource.connectionGeneration()) && afterSource.revision().compareTo(beforeSource.revision()) > 0
                && afterSource.nativeRevision().compareTo(beforeSource.nativeRevision()) > 0 && !afterSource.snapshotId().equals(beforeSource.snapshotId()), "retreat lacks its exact original and later same-episode publication");
        var arguments = order.arguments();
        StrictJson.require(move.armyId() == arguments.selectedPublicCunitId() && move.provinceId() == arguments.targetProvinceId()
                && arguments.expectedRevision().equals(beforeSource.revision()), "retreat primitive differs from the exact original subject/target/revision");
        ObjectNode body = EffectJson.object(preview);
        StrictJson.trueValue(body.get("action_ready")); StrictJson.require(StrictJson.text(body.get("status")).equals("available")
                && OpportunityJson.object(preview.get("source_binding"), "preview source").equals(beforeSource.json()), "original ready preview source changed");
        sameInteger(body.get("selected_public_cunit_id"), move.armyId()); sameInteger(body.get("selected_owner_character_id"), actor);
        sameInteger(body.get("combat_id"), arguments.expectedCombatId()); sameInteger(body.get("side_index"), arguments.expectedSideIndex());
        StrictJson.require(StrictJson.text(body.get("side_scope")).equals(arguments.expectedScope().wire()), "retreat preview scope changed");
        sameInteger(body.get("target_province_id"), move.provinceId());
        StrictJson.require(publicUnits(body.get("affected_public_cunit_ids_in_stored_order")).equals(order.affectedInStoredOrder())
                && publicUnits(body.get("unaffected_same_side_public_cunit_ids_in_stored_order")).equals(order.unaffectedInStoredOrder()), "retreat affected/unaffected stored-order roster changed");
        ObjectNode control = EffectJson.object(body.get("battle_control_snapshot")), target = EffectJson.object(body.get("target_preview"));
        sameInteger(control.get("selected_public_cunit_id"), move.armyId()); sameInteger(control.get("selected_owner_character_id"), actor);
        sameInteger(control.get("combat_id"), arguments.expectedCombatId()); sameInteger(control.get("side_index"), arguments.expectedSideIndex());
        StrictJson.require(EffectJson.integer(control.get("snapshot_revision")).equals(beforeSource.nativeRevision())
                && EffectJson.integer(control.get("observed_date_raw")).equals(beforeSource.dateRaw())
                && StrictJson.text(control.get("side_scope")).equals(arguments.expectedScope().wire()), "native control differs from original retreat source/scope");
        StrictJson.trueValue(EffectJson.object(control.get("legality")).get("legal_now"));
        long origin = EffectJson.id(body.get("combat_province_id")); sameInteger(control.get("combat_province_id"), origin);
        StrictJson.require(origin != move.provinceId(), "retreat target does not leave the original combat province");
        sameInteger(target.get("army_id"), move.armyId()); sameInteger(target.get("origin_province_id"), origin); sameInteger(target.get("target_province_id"), move.provinceId());
        StrictJson.require(StrictJson.text(target.get("status")).equals("available") && StrictJson.text(target.get("candidate_token")).equals(arguments.candidateToken())
                && provinces(target.get("route_province_ids")).equals(order.routeProvinceIds()), "original native route/token changed");
        for (int unit : order.affectedInStoredOrder()) {
            JsonNode original = army(before, unit); StrictJson.require(original != null, "original affected public CUnit is missing");
            StrictJson.trueValue(original.get("controllable")); sameInteger(original.get("owner_character_id"), actor);
            StrictJson.trueValue(original.get("in_combat")); StrictJson.require(!EffectJson.bool(original.get("retreating")), "original affected unit was already retreating");
            sameInteger(original.get("current_province_id"), origin);
            JsonNode current = army(after, unit);
            if (current == null || EffectJson.id(current.get("owner_character_id")) != actor || !EffectJson.bool(current.get("retreating")) || EffectJson.bool(current.get("in_combat"))) return State.NOT_OBSERVED;
            JsonNode requestedTarget = current.get("move_target_province_id");
            if (requestedTarget == null || requestedTarget.isNull() || EffectJson.id(requestedTarget) != move.provinceId()
                    || !provinces(current.get("route_province_ids")).equals(order.routeProvinceIds())) return State.NOT_OBSERVED;
        }
        for (int unit : order.unaffectedInStoredOrder()) {
            JsonNode original = army(before, unit), current = army(after, unit);
            StrictJson.require(original != null && EffectJson.bool(original.get("in_combat")) && !EffectJson.bool(original.get("retreating")), "original unaffected scope roster is unavailable");
            if (current == null || !EffectJson.bool(current.get("in_combat")) || EffectJson.bool(current.get("retreating"))
                    || !EffectJson.integer(current.get("owner_character_id")).equals(EffectJson.integer(original.get("owner_character_id")))
                    || !EffectJson.integer(current.get("current_province_id")).equals(EffectJson.integer(original.get("current_province_id")))) return State.NOT_OBSERVED;
        }
        return State.RETREATING;
    }
    private static void sameInteger(JsonNode value, long expected) { StrictJson.require(EffectJson.integer(value).equals(BigInteger.valueOf(expected)), "retreat full integer identity changed"); }
    private static ActiveRetreatProposal.SourceFrame source(ObjectNode value) {
        return new ActiveRetreatProposal.SourceFrame(StrictJson.text(value.get("snapshot_id")), EffectJson.integer(value.get("revision")),
                EffectJson.integer(value.get("native_revision")), EffectJson.integer(value.get("date_raw")), StrictJson.text(value.get("episode_run_id")),
                EffectJson.integer(EffectJson.object(value.get("diagnostics")).get("connection_generation")));
    }
    private static List<Integer> publicUnits(JsonNode values) {
        StrictJson.require(values != null && values.isArray() && values.size() <= 65536, "bounded actual public CUnit roster required");
        List<Integer> result = new ArrayList<>();
        for (JsonNode value : values) {
            BigInteger id = EffectJson.integer(value); StrictJson.require(id.signum() >= 0 && id.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "public CUnit outside exact nonnegative int32 domain"); result.add(id.intValueExact());
        }
        StrictJson.require(result.stream().distinct().count() == result.size(), "duplicate public CUnit in actual roster"); return List.copyOf(result);
    }
    private static List<Integer> provinces(JsonNode values) {
        StrictJson.require(values != null && values.isArray() && values.size() <= 65536, "bounded actual province route required");
        List<Integer> result = new ArrayList<>(); for (JsonNode value : values) result.add(Math.toIntExact(EffectJson.id(value))); return List.copyOf(result);
    }
    private static JsonNode army(ObjectNode frame, int publicCunit) {
        JsonNode found = null;
        for (JsonNode candidate : EffectJson.rows(frame.get("player_armies"))) {
            BigInteger id = EffectJson.integer(candidate.get("army_id")); StrictJson.require(id.signum() >= 0 && id.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "actual public CUnit identity must be nonnegative int32");
            if (id.intValueExact() == publicCunit) { StrictJson.require(found == null, "duplicate actual public CUnit"); found = candidate; }
        }
        return found;
    }
    private static void owned(JsonNode army, long actor) {
        StrictJson.trueValue(army.get("controllable")); StrictJson.require(EffectJson.id(army.get("owner_character_id")) == actor, "army ownership changed");
        StrictJson.require(!EffectJson.bool(army.get("in_combat")) && !EffectJson.bool(army.get("retreating")), "army is in combat/retreat");
        JsonNode state = army.get("army_state"), code = army.get("army_state_code");
        if (state != null && state.isTextual()) StrictJson.require(!List.of("combat", "retreating").contains(state.textValue().toLowerCase(Locale.ROOT)), "army state blocks movement");
        if (code != null) StrictJson.require(!List.of(2L, 6L).contains(EffectJson.nonnegative(code)), "army state code blocks movement");
    }
    private static boolean stationary(JsonNode army) {
        JsonNode state = army.get("army_state");
        if (state != null && state.isTextual()) return List.of("regular", "sieging").contains(state.textValue().toLowerCase(Locale.ROOT));
        JsonNode code = army.get("army_state_code"); return code != null && List.of(1L, 3L).contains(EffectJson.nonnegative(code));
    }
}
