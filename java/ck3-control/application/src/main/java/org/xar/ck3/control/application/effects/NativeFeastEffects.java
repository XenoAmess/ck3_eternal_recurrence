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
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.governance.OrdinaryFeastPolicy;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.governance.activity.ActivityPlannerDiagnostic;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastCodec;

/** Actual fresh native reads and archived replay for the four ordinary Feast primitives. */
public final class NativeFeastEffects implements NativeEffectRegistry.Observer, OrdinaryFeastPolicy.Effects {
    public static final String SCHEMA = "xar.java.feast-native-post/v1";
    public enum Query {
        DIAGNOSTIC("query-activity-planner-diag-v1-private", "activity_planner_diag"),
        HOSTED("query-activity-feast-hosted-post-v1-private", "activity_feast_hosted_post");
        private final OperationKey operation; private final String payload;
        Query(String operation, String payload) { this.operation = new OperationKey(operation); this.payload = payload; }
        public OperationKey operation() { return operation; }
        public String payload() { return payload; }
    }
    /** Root adapts the unique Activity installation, including its actual source/build/hello validation. */
    public interface Reads {
        PlanningReadResult<RawJson> read(Query query, PlanningReadRequest request);
        /** Replay calls the same installed contract decoder on the archived original receipt. */
        RawJson decode(Query query, PlanningReadReceipt original);
    }
    private enum Kind { OPEN, CONFIRM, DESTINATION, START }
    private final NativeEffectSnapshots snapshots;
    private final Reads reads;
    public NativeFeastEffects(NativeEffectSnapshots snapshots, Reads reads) {
        this.snapshots = Objects.requireNonNull(snapshots); this.reads = Objects.requireNonNull(reads);
    }
    public List<NativeEffectRegistry.Binding> bindings(ExactRef implementation, ActionPorts.PreparationPort actualPreparation) {
        Objects.requireNonNull(implementation); Objects.requireNonNull(actualPreparation);
        return OrdinaryFeastPolicy.OWNED.stream().sorted(java.util.Comparator.comparing(OperationKey::value))
                .map(operation -> new NativeEffectRegistry.Binding(operation, implementation, actualPreparation, this)).toList();
    }
    public List<NativeRecordedEvidenceVerifier.Binding> archivedBindings(ExactRef implementation, NativeEffectEvidence.FrameLoader frames) {
        Objects.requireNonNull(frames);
        return OrdinaryFeastPolicy.OWNED.stream().sorted(java.util.Comparator.comparing(OperationKey::value))
                .map(operation -> archivedVerifier(operation, implementation, frames, reads)).toList();
    }
    private static Kind kind(OperationKey operation) {
        if (operation.equals(OrdinaryFeastPolicy.CONFIGURE)) return Kind.OPEN;
        if (operation.equals(OrdinaryFeastPolicy.CONFIRM)) return Kind.CONFIRM;
        if (operation.equals(OrdinaryFeastPolicy.DESTINATION)) return Kind.DESTINATION;
        if (operation.equals(OrdinaryFeastPolicy.START)) return Kind.START;
        throw new IllegalArgumentException("not an ordinary Feast primitive");
    }
    @Override public Optional<ExpectedPostcondition> expected(OperationKey operation, PlanningRequest request, OpportunityJson.Obj arguments) {
        if (!OrdinaryFeastPolicy.OWNED.contains(operation)) return Optional.empty();
        Kind selected = kind(operation); var fields = new ArrayList<ExpectedValue>();
        if (selected == Kind.START) {
            fields.add(flag("feast.new_hosted_instance", true)); fields.add(flag("feast.actual_costs_debited", true));
        } else {
            StrictJson.require(EffectJson.bool(balance(EffectJson.object(EffectJson.object(arguments).get("hosted_observation")), "gold").get("available")),
                    "configuration needs the actual pre-submission gold observation for its independent postcondition");
            fields.add(flag("feast.planner_visible", true)); fields.add(flag("feast.no_activity_started", true));
            fields.add(flag("feast.gold_unchanged", true));
            if (selected != Kind.OPEN) fields.add(number("feast.planning_stage", selected == Kind.CONFIRM ? 2 : 5));
            if (selected == Kind.DESTINATION) fields.add(new ExpectedInteger(new FieldKey("feast.destination_province_id"),
                    integer(EffectJson.object(EffectJson.object(arguments).get("native_arguments")).get("province_id"))));
        }
        fields.add(flag("native.gameplay_verified", true));
        return Optional.of(new ExpectedPostcondition(1, request.before(), request.source(), SCHEMA, fields));
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch) {
        kind(command.operation()); var pair = snapshots.read(command, attempt); Complete after = pair.after();
        var originals = new ArrayList<PlanningReadReceipt>();
        for (Query query : Query.values()) {
            var request = new PlanningReadRequest(after.identity(), after.source(), after.sessionId(), query.operation(),
                    new OpportunityJson.Obj(java.util.Map.of()), command.deadline());
            var result = reads.read(query, request);
            if (!(result instanceof PlanningReadResult.Known<RawJson> known))
                return NativeEffectRegistry.Projected.pending("actual independent Feast read unavailable; preserve the original action without replay", List.of(after.originalEvidence()));
            originals.add(known.receipt());
        }
        NativeEffectRegistry.Projected projected = project(command, attempt, dispatch, pair, originals, reads);
        return NativeEffectSnapshots.withEvidence(projected, List.of(snapshots.evidence(command, attempt, pair, originals,
                projected.compatibleResult().orElseThrow())));
    }
    private static NativeEffectRegistry.Projected project(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch, NativeEffectSnapshots.Pair frames, List<PlanningReadReceipt> originals, Reads reads) {
        StrictJson.require(originals.size() == Query.values().length, "two independent Feast reads required");
        var material = new ArrayList<RawJson>();
        for (int index = 0; index < Query.values().length; index++) {
            Query query = Query.values()[index]; PlanningReadReceipt original = originals.get(index);
            NativeEffectSnapshots.requireAfterRead(command, attempt, frames.after(), original, query.operation());
            RawJson raw = Objects.requireNonNull(reads.decode(query, original));
            StrictJson.require(original.original().originalResultToken().filter(raw::equals).isPresent(), "Feast decoder did not preserve the actual original result token");
            material.add(raw);
        }
        StrictJson.require(dispatch instanceof NativeActionPort.AckReceived, "Feast original native action receipt is required separately from the independent post reads");
        var ack = (NativeActionPort.AckReceived) dispatch;
        StrictJson.require(ack.nativeOk() && ack.requestId().equals(attempt.requestId())
                && attempt.preparedRequest().step().equals(command.operation().value()), "Feast original action request identity differs");
        RawJson originalAction = ack.originalResultToken().orElseThrow(() -> new IllegalArgumentException("Feast native action result missing"));
        List<ExpectedValue> actual = materialValues(command.operation(), command.arguments(), command.before(), frames.after().identity(),
                originalAction, material.get(0), material.get(1));
        ObjectNode compatible = StrictJson.object().put("step", command.operation().value()).put("accepted", true)
                .put("status", "applied").put("postcondition_verified", true);
        compatible.set("original_action", EffectJson.parse(originalAction)); compatible.set("independent_diagnostic", EffectJson.parse(material.get(0)));
        compatible.set("independent_hosted_post", EffectJson.parse(material.get(1)));
        RawJson result = EffectJson.raw(compatible);
        return NativeEffectSnapshots.observed(command, attempt, frames.after(), SCHEMA, actual,
                originals.getLast().requestId(), result, List.of());
    }
    public static NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation, ExactRef implementation,
            NativeEffectEvidence.FrameLoader frames, Reads actualReads) {
        kind(operation); Objects.requireNonNull(actualReads);
        return new NativeRecordedEvidenceVerifier.Binding(operation, implementation, (head, receipt, archive) -> {
            var original = NativeEffectEvidence.load(receipt, archive, frames); var settled = (ActionState.Settled) receipt.state();
            var replayed = project(receipt.command(), settled.attempt(), settled.dispatch(), original.frames(), original.independentReads(), actualReads);
            replayed = NativeEffectSnapshots.withEvidence(replayed, ((ActionState.Applied) settled.settlement()).observation().supportingEvidence());
            NativeEffectEvidence.requireSame(settled.settlement(), replayed, original.compatibleResult());
        });
    }
    /** Shared pure projection used by live observation and the durable original-evidence replay. */
    public static List<ExpectedValue> materialValues(OperationKey operation, OpportunityJson.Obj arguments,
            ObservationIdentity before, ObservationIdentity after, RawJson action, RawJson diagnosticResult, RawJson hostedResult) {
        Kind selected = kind(operation); sameGame(before, after);
        ObjectNode args = EffectJson.object(arguments), actionEnvelope = EffectJson.object(EffectJson.parse(action));
        requireEnvelope(actionEnvelope, operation, false);
        textEquals(actionEnvelope, "status", selected == Kind.START ? "pending" : "available");
        var actionFields = new HashSet<>(Set.of("step", "accepted", "status", "private_build", "read_only", "advertised", "backend_id",
                selected == Kind.OPEN ? "activity_feast_planner_open" : selected == Kind.CONFIRM ? "activity_stage1_confirm"
                        : selected == Kind.DESTINATION ? "activity_stage2_destination_select" : "activity_feast_stage5_start"));
        if (selected == Kind.OPEN && actionEnvelope.has("same_frame")) { actionFields.add("same_frame"); yes(actionEnvelope, "same_frame"); }
        StrictJson.object(actionEnvelope, actionFields);
        ObjectNode diagnostic = payload(diagnosticResult, Query.DIAGNOSTIC), post = payload(hostedResult, Query.HOSTED);
        var afterFrame = after.frame().identity();
        var planner = ActivityPlannerDiagnostic.decode(StrictJson.canonical(diagnostic),
                new ActivityPlannerDiagnostic.Frame(afterFrame.nativeRevision(), afterFrame.dateRaw(), afterFrame.player()));
        bind(post, after, "activity-feast-hosted-post-private-read-v1");
        ObjectNode pre = selected == Kind.START ? EffectJson.object(args.get("inputs")) : EffectJson.object(args.get("hosted_observation"));
        bind(pre, before, selected == Kind.START ? "activity-feast-stage5-start-inputs-private-v1" : "activity-feast-hosted-post-private-read-v1");
        List<HostedFeastActivities.Activity> oldRows = hosted(pre), current = hosted(post);
        Set<Long> oldIds = new HashSet<>(); oldRows.forEach(row -> oldIds.add(row.activityId()));
        Set<Long> newIds = new HashSet<>(); current.forEach(row -> newIds.add(row.activityId()));
        StrictJson.require(newIds.containsAll(oldIds), "a previous hosted activity disappeared during the Feast action");
        var added = current.stream().filter(row -> !oldIds.contains(row.activityId())).toList();
        var actual = new ArrayList<ExpectedValue>();
        if (selected == Kind.START) {
            StrictJson.require(new OpportunityJson.Bool(true).equals(arguments.get("new_attempt")), "Start must retain its original new attempt intent");
            ObjectNode ack = StrictJson.object(actionEnvelope.get("activity_feast_stage5_start"), Set.of("schema", "submitted", "native_status", "failure", "precondition"));
            textEquals(ack, "schema", "activity-feast-stage5-start-private-action-v1"); yes(ack, "submitted"); textEquals(ack, "native_status", "submitted_pending");
            StrictJson.require(ack.get("failure").isTextual() && ack.get("failure").textValue().isEmpty(), "pending native Start contains a failure");
            ObjectNode submitted = EffectJson.object(ack.get("precondition"));
            bind(submitted, before, "activity-feast-stage5-start-inputs-private-v1"); yes(submitted, "final_can_start"); yes(submitted, "native_guest_route_qualified");
            for (String field : List.of("resources", "balances", "hosted_activities"))
                StrictJson.require(java.util.Arrays.equals(StrictJson.canonical(submitted.get(field)), StrictJson.canonical(pre.get(field))),
                        "native Start submission precondition differs from the original source-bound quote");
            StrictJson.require(added.size() == 1 && added.getFirst().hostCharacterId() == before.frame().identity().player().longValueExact()
                    && added.getFirst().activityTypeKey().equals("activity_feast"), "Start lacks exactly one newly observed hosted Feast");
            debit(pre, post); actual.add(flag("feast.new_hosted_instance", true)); actual.add(flag("feast.actual_costs_debited", true));
            actual.add(new ExpectedInteger(new FieldKey("feast.activity_id"),BigInteger.valueOf(added.getFirst().activityId())));
            actual.add(new ExpectedInteger(new FieldKey("feast.host_character_id"),BigInteger.valueOf(added.getFirst().hostCharacterId())));
        } else {
            StrictJson.require(added.isEmpty(), "Feast configuration unexpectedly started an activity");
            int stage = selected == Kind.CONFIRM ? 2 : 5;
            StrictJson.require(selected == Kind.OPEN ? planner.kind() == ActivityPlannerDiagnostic.Kind.FEAST_STAGE_ONE
                    || planner.kind() == ActivityPlannerDiagnostic.Kind.FEAST_STAGE_TWO
                    : selected == Kind.CONFIRM ? planner.kind() == ActivityPlannerDiagnostic.Kind.FEAST_STAGE_TWO
                    : planner.kind() == ActivityPlannerDiagnostic.Kind.FEAST_STAGE_FIVE, "independent current Feast planner stage differs");
            yes(diagnostic, "widget_attached"); yes(diagnostic, "widget_visible"); unchanged(pre, post);
            ObjectNode receipt = EffectJson.object(actionEnvelope.get(selected == Kind.OPEN ? "activity_feast_planner_open"
                    : selected == Kind.CONFIRM ? "activity_stage1_confirm" : "activity_stage2_destination_select"));
            bindAction(receipt, before);
            if (selected == Kind.OPEN) {
                exact(receipt, "schema snapshot_revision date_raw actor_character_id open_status native_dispatch_invoked selected_feast_verified widget_attached widget_visible planning_stage configured_cost_state final_can_start_state raw_pointer_fields_persisted");
                textEquals(receipt, "schema", "activity-feast-planner-open-private-v1");
                StrictJson.require(Set.of("opened", "already_open").contains(StrictJson.text(receipt.get("open_status"))), "native Feast planner did not open");
                yes(receipt, "selected_feast_verified"); yes(receipt, "widget_attached"); yes(receipt, "widget_visible");
                StrictJson.require(EffectJson.bool(receipt.get("native_dispatch_invoked")) == StrictJson.text(receipt.get("open_status")).equals("opened"), "native Open dispatch/status differs");
                textEquals(receipt, "configured_cost_state", "unknown"); textEquals(receipt, "final_can_start_state", "unknown"); no(receipt, "raw_pointer_fields_persisted");
                StrictJson.require(Set.of(BigInteger.ONE, BigInteger.TWO).contains(integer(receipt.get("planning_stage"))), "native Open stage differs");
                StrictJson.require(integer(receipt.get("planning_stage")).equals(integer(diagnostic.get("planning_stage"))), "Open action and independent planner stage differ");
            } else if (selected == Kind.CONFIRM) {
                exact(receipt, "schema snapshot_revision date_raw actor_character_id activity_key expected_option_key selected_option_key precondition_status selected_option_shown selected_option_valid can_progress_stage1 generic_feast_confirm_ready status submitted stage_two_visible selected_option_retained planning_stage_after gold_before_raw gold_after_raw snapshot_unchanged activity_start_state next_turn_verified raw_pointer_fields_persisted advertised");
                textEquals(receipt, "schema", "activity-stage1-confirm-private-v1"); textEquals(receipt, "status", "stage_two_verified");
                textEquals(receipt, "activity_key", "activity_feast"); textEquals(receipt, "expected_option_key", "feast_type_generic"); textEquals(receipt, "precondition_status", "observed");
                for (String field : List.of("selected_option_shown", "selected_option_valid", "can_progress_stage1", "generic_feast_confirm_ready", "snapshot_unchanged")) yes(receipt, field);
                no(receipt, "next_turn_verified"); no(receipt, "raw_pointer_fields_persisted"); no(receipt, "advertised");
                yes(receipt, "submitted"); yes(receipt, "stage_two_visible"); yes(receipt, "selected_option_retained");
                textEquals(receipt, "selected_option_key", "feast_type_generic"); textEquals(receipt, "activity_start_state", "not_started_immediate");
                StrictJson.require(integer(receipt.get("planning_stage_after")).equals(BigInteger.TWO)
                        && signed(receipt.get("gold_before_raw")).equals(signed(receipt.get("gold_after_raw"))), "Confirm immediate stage/gold differs");
            } else {
                exact(receipt, "schema snapshot_revision date_raw actor_character_id activity_key selected_option_key selected_province_id status submitted needs_recovery stage_five_visible rows_filled selected_option_retained gold_unchanged frame_unchanged no_activity_started planning_stage_before planning_stage_after configuration_province_ids_before configuration_province_ids_after player_gold_before_raw player_gold_after_raw read_only advertised");
                textEquals(receipt, "schema", "activity-stage2-destination-private-action-v1"); textEquals(receipt, "status", "verified_stage_five");
                textEquals(receipt, "activity_key", "activity_feast"); textEquals(receipt, "selected_option_key", "feast_type_generic"); no(receipt, "read_only"); no(receipt, "advertised");
                for (String field : List.of("submitted", "stage_five_visible", "rows_filled", "selected_option_retained", "gold_unchanged", "frame_unchanged", "no_activity_started")) yes(receipt, field);
                StrictJson.require(!EffectJson.bool(receipt.get("needs_recovery")), "destination still needs recovery");
                BigInteger province = integer(EffectJson.object(args.get("native_arguments")).get("province_id"));
                StrictJson.require(integer(receipt.get("selected_province_id")).equals(province)
                        && integer(receipt.get("planning_stage_before")).equals(BigInteger.TWO)
                        && integer(receipt.get("planning_stage_after")).equals(BigInteger.valueOf(5)), "destination identity/stage differs");
                requirePair(receipt.get("configuration_province_ids_before"), BigInteger.ZERO); requirePair(receipt.get("configuration_province_ids_after"), province);
                StrictJson.require(signed(receipt.get("player_gold_before_raw")).equals(signed(receipt.get("player_gold_after_raw"))), "destination immediate gold differs");
                actual.add(new ExpectedInteger(new FieldKey("feast.destination_province_id"), integer(receipt.get("selected_province_id"))));
            }
            actual.add(flag("feast.planner_visible", true)); actual.add(flag("feast.no_activity_started", true)); actual.add(flag("feast.gold_unchanged", true));
            if (selected != Kind.OPEN) actual.add(number("feast.planning_stage", stage));
        }
        actual.add(flag("native.gameplay_verified", true)); return List.copyOf(actual);
    }
    private static void sameGame(ObservationIdentity before, ObservationIdentity after) {
        StrictJson.require(before.machineId().equals(after.machineId()) && before.game().equals(after.game())
                && before.frame().episodeRunId().equals(after.frame().episodeRunId()) && before.frame().identity().player().equals(after.frame().identity().player())
                && before.frame().identity().dateRaw().equals(after.frame().identity().dateRaw())
                && after.frame().revision().compareTo(before.frame().revision()) > 0
                && after.frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision()) > 0,
                "Feast material crossed original Game/actor/episode/date or lacks a fresh later frame");
    }
    private static ObjectNode payload(RawJson raw, Query query) {
        ObjectNode root = EffectJson.object(EffectJson.parse(raw)); requireEnvelope(root, query.operation(), true);
        return EffectJson.object(root.get(query.payload()));
    }
    private static void requireEnvelope(ObjectNode root, OperationKey operation, boolean readOnly) {
        textEquals(root, "step", operation.value()); yes(root, "accepted"); yes(root, "private_build");
        StrictJson.require(EffectJson.bool(root.get("read_only")) == readOnly && !EffectJson.bool(root.get("advertised")), "Feast native envelope flags differ");
        textEquals(root, "backend_id", "native-headless");
    }
    private static void bind(ObjectNode payload, ObservationIdentity observed, String schema) {
        textEquals(payload, "schema", schema); bindAction(payload, observed); yes(payload, "read_only");
        StrictJson.require(!EffectJson.bool(payload.get("advertised")), "Feast payload advertised");
    }
    private static void bindAction(ObjectNode payload, ObservationIdentity observed) {
        var frame = observed.frame().identity();
        StrictJson.require(integer(payload.get("snapshot_revision")).equals(frame.nativeRevision()) && integer(payload.get("date_raw")).equals(frame.dateRaw())
                && integer(payload.get("actor_character_id")).equals(frame.player()), "Feast native payload source frame differs");
    }
    private static List<HostedFeastActivities.Activity> hosted(ObjectNode payload) {
        return HostedFeastCodec.decode(StrictJson.canonical(payload.get("hosted_activities"))).activities();
    }
    private static void unchanged(ObjectNode before, ObjectNode after) {
        for (String key : List.of("gold", "treasury", "piety", "barter_goods")) {
            ObjectNode pre = balance(before, key), post = balance(after, key);
            if (key.equals("gold")) StrictJson.require(EffectJson.bool(pre.get("available")) && EffectJson.bool(post.get("available")), "independent gold before/after unavailable");
            if (EffectJson.bool(pre.get("available")) && EffectJson.bool(post.get("available")))
                StrictJson.require(integer(pre.get("raw")).equals(integer(post.get("raw"))), "configuration changed an independently observed resource");
        }
    }
    private static void debit(ObjectNode before, ObjectNode after) {
        ObjectNode resources = StrictJson.object(before.get("resources"), Set.of("gold", "treasury", "piety", "barter_goods"));
        for (String key : List.of("gold", "treasury", "piety", "barter_goods")) {
            ObjectNode costRow = StrictJson.object(resources.get(key), Set.of("resource_index", "configured_cost_raw"));
            StrictJson.integer(costRow.get("resource_index"), 0, 9); BigInteger cost = StrictJson.integer(costRow.get("configured_cost_raw"), BigInteger.ZERO, BigInteger.valueOf(Long.MAX_VALUE));
            ObjectNode pre = balance(before, key), post = balance(after, key);
            if (cost.signum() > 0) StrictJson.require(EffectJson.bool(pre.get("available")) && EffectJson.bool(post.get("available"))
                    && integer(pre.get("raw")).subtract(integer(post.get("raw"))).equals(cost), "actual native debit differs from the pre-submission configured cost");
            else if (EffectJson.bool(pre.get("available")) && EffectJson.bool(post.get("available")))
                StrictJson.require(integer(pre.get("raw")).equals(integer(post.get("raw"))), "zero-cost resource changed during Start");
        }
    }
    private static ObjectNode balance(ObjectNode payload, String key) {
        ObjectNode balances = StrictJson.object(payload.get("balances"), Set.of("gold", "treasury", "piety", "barter_goods"));
        ObjectNode result = StrictJson.object(balances.get(key), Set.of("available", "raw"));
        if (EffectJson.bool(result.get("available"))) signed(result.get("raw"));
        else StrictJson.require(result.get("raw").isNull(), "unavailable native balance requires explicit null");
        return result;
    }
    private static void requirePair(JsonNode values, BigInteger expected) {
        StrictJson.require(values != null && values.isArray() && values.size() == 2
                && integer(values.get(0)).equals(expected) && integer(values.get(1)).equals(expected), "exact two-row native destination required");
    }
    private static BigInteger integer(JsonNode value) { return StrictJson.integer(value, BigInteger.valueOf(Long.MIN_VALUE), StrictJson.UINT64_MAX); }
    private static BigInteger signed(JsonNode value) { return StrictJson.integer(value, BigInteger.valueOf(Long.MIN_VALUE), BigInteger.valueOf(Long.MAX_VALUE)); }
    private static void textEquals(JsonNode value, String key, String expected) { StrictJson.require(StrictJson.text(value.get(key)).equals(expected), "Feast text field differs: " + key); }
    private static void yes(JsonNode value, String key) { StrictJson.trueValue(value.get(key)); }
    private static void no(JsonNode value, String key) { StrictJson.require(!EffectJson.bool(value.get(key)), "Feast field must be false: " + key); }
    private static void exact(ObjectNode value, String fields) { StrictJson.object(value, Set.of(fields.split(" "))); }
    private static ExpectedBoolean flag(String key, boolean value) { return new ExpectedBoolean(new FieldKey(key), value); }
    private static ExpectedInteger number(String key, int value) { return new ExpectedInteger(new FieldKey(key), BigInteger.valueOf(value)); }
}
