package org.xar.ck3.control.service.mcp;

import java.io.IOException;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.OrdinaryHistory;
import org.xar.ck3.control.service.root.RootRuntimeDomainSettings.PlanFlags;
import org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskCodec;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.OriginalTerminalPlanning;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Value;

/**
 * The original public PLAN envelope over the complete ordinary producer result.
 * A plan is detached DATA: this class neither prepares another action nor executes a policy.
 */
public final class RootPublicPlanPresentation implements RootMcpPlanning.PlanPresentation {
    private static final Set<String> BASE = Set.of("snapshot_id", "revision", "planning_source_frame", "plan");
    private static final Set<String> FRAME = Set.of("schema", "status", "snapshot_id", "revision",
            "native_revision", "date_raw", "actor_character_id", "episode_run_id",
            "connection_generation", "bridge_pid");

    /** Exact immutable original tree; no source-owned plan members are whitelisted away. */
    public static final class PublicPlan {
        private final Obj original;
        private PublicPlan(Obj original) { this.original = Objects.requireNonNull(original); validate(original); }
        public Obj original() { return original; }
        public Obj plan() { return object(original.get("plan"), "plan"); }
        public Obj sourceFrame() { return object(original.get("planning_source_frame"), "planning_source_frame"); }
        public RawJson bytes() { return PublicDataJson.encodeFullMaterial(original); }
    }

    @Override public RawJson encode(PlanningRequest original, PlanningResult actual, PlanFlags flags) throws IOException {
        return produce(original, actual, flags).bytes();
    }

    public static PublicPlan produce(PlanningRequest original, PlanningResult actual, PlanFlags flags) throws IOException {
        Objects.requireNonNull(original); Objects.requireNonNull(actual);
        if (!actual.trace().before().equals(original.before()))
            throw new IOException("public PLAN result belongs to another actual original frame");
        if (actual instanceof PlanningResult.IncompleteMigration incomplete)
            throw new IOException("INCOMPLETE_PUBLIC_PLAN: missing actual ordinary producers " + incomplete.missingStages());
        OrdinaryPolicy.Draft draft = actual.trace().finalPlan().orElseThrow(() ->
                new IOException("INCOMPLETE_PUBLIC_PLAN: actual ordinary result has no retained complete plan"));
        Obj plan = completePlan(draft);
        if (actual instanceof PlanningResult.ActionSelected selected) {
            if (!draft.command().equals(Optional.of(selected.command())))
                throw new IOException("public PLAN lost the exact prepared original action");
            plan = sameOrPut(plan, "selected_step", new Text(selected.command().operation().value()));
        } else if (draft.command().isPresent()) {
            // A stopped/refresh/reconciliation result must never advertise the discarded draft command.
            throw new IOException("INCOMPLETE_PUBLIC_PLAN: no-action result retained a prepared action");
        } else if (!plan.members().containsKey("selected_step")) {
            plan = plan.with("selected_step", Nil.INSTANCE);
        }
        var fields = new LinkedHashMap<String, Value>();
        fields.put("snapshot_id", new Text(original.before().frame().snapshotId()));
        fields.put("revision", new Text(original.before().frame().revision().toString()));
        fields.put("planning_source_frame", publicFrame(OriginalPlanningFrameProjection.sourceFrame(original)));
        fields.put("plan", plan);
        // The original early return path determines presence; a missing member is not a null alias.
        var envelope = OriginalPlanDomainEnvelope.project(original, actual, Objects.requireNonNull(flags));
        if (envelope.branch().commonAnnotations()) {
            fields.put("_declaration_opportunity_cooldown_v1", optional(original.observations().snapshot(),
                    "declaration_opportunity_cooldown_v1"));
            fields.put("_auto_camera_hotspot_input", publicCamera(OriginalPlanningFrameProjection.cameraInput(original)));
            Value rootResult = currentRootResult(original);
            fields.put("_ordinary_sway_input_v1", publicSway(OriginalPlanningFrameProjection.ordinarySwayInput(original, rootResult), true));
            var riskContext = PlayerRiskCodec.projectObserved(DriverJson.toNode(original.observations().snapshot()),
                    rootResult == Nil.INSTANCE ? null : DriverJson.toNode(rootResult));
            fields.put("plan", plan.with("player_risk_context", DriverJson.fromNode(PlayerRiskCodec.encodePublic(riskContext))));
        }
        for (var entry : publicExtras(envelope.survivingTopLevel(), true).members().entrySet()) {
            StrictJson.require(!fields.containsKey(entry.getKey()), "domain envelope must not replace the original public frame or plan");
            fields.put(entry.getKey(), entry.getValue());
        }
        return new PublicPlan(new Obj(fields));
    }

    /**
     * Original terminal window-priority DATA over the actual full snapshot, including a missing or
     * changed player. No PlanningRequest, ActionCommand or lifecycle lease is reconstructed here.
     */
    public static PublicPlan produceTerminal(OriginalTerminalPlanning.Input actual, Obj terminalPlan) throws IOException {
        Objects.requireNonNull(actual); Objects.requireNonNull(terminalPlan);
        Obj snapshot = actual.snapshot();
        if (!OriginalTerminalPlanning.terminalFrame(snapshot)
                || !new Text("one-life-turn-v1").equals(terminalPlan.get("policy")))
            throw new IOException("public terminal presentation requires the actual original terminal branch");
        var fields = new LinkedHashMap<String, Value>();
        fields.put("snapshot_id", snapshot.get("snapshot_id"));
        fields.put("revision", new Text(OpportunityJson.integer(snapshot.get("revision"), "revision").toString()));
        fields.put("planning_source_frame", publicFrame(OriginalPlanningFrameProjection.sourceFrame(snapshot)));
        fields.put("_declaration_opportunity_cooldown_v1", optional(snapshot, "declaration_opportunity_cooldown_v1"));
        fields.put("_auto_camera_hotspot_input", publicCamera(OriginalPlanningFrameProjection.cameraInput(snapshot)));
        Value rootResult = currentRootResult(snapshot, actual.history());
        fields.put("_ordinary_sway_input_v1", publicSway(
                OriginalPlanningFrameProjection.ordinarySwayInput(snapshot, rootResult), true));
        var risk = PlayerRiskCodec.projectObserved(DriverJson.toNode(snapshot),
                rootResult == Nil.INSTANCE ? null : DriverJson.toNode(rootResult));
        fields.put("plan", terminalPlan.with("player_risk_context", DriverJson.fromNode(PlayerRiskCodec.encodePublic(risk))));
        // WINDOW_PRIORITY consumes its private domain inputs; only these actual common annotations survive.
        return new PublicPlan(new Obj(fields));
    }

    /** Cold DATA validation uses the same codec; it never upgrades a decoded plan to a current command. */
    public static PublicPlan decode(RawJson original) {
        Objects.requireNonNull(original);
        return new PublicPlan(DriverJson.object(original.bytes(), RawJson.MAXIMUM_BYTES));
    }

    /** Exact original same-frame root selection over the sole normalized command-history expansion. */
    private static Value currentRootResult(PlanningRequest original) {
        return currentRootResult(original.observations().snapshot(), original.observations().history());
    }
    private static Value currentRootResult(Obj snapshot, List<Obj> history) {
        var rows = OrdinaryHistory.collect(history).rows();
        for (int index = rows.size() - 1; index >= 0; index--) {
            var row = rows.get(index);
            if (!OrdinaryHistory.successful(row) || !OrdinaryHistory.effectiveCommand(row)
                    .filter("query-campaign-root-context-v1"::equals).isPresent()) continue;
            var found = OrdinaryHistory.effectiveCommandResult(row);
            if (found.isEmpty()) continue;
            Obj result = found.orElseThrow();
            if (!(result.get("campaign_root_context") instanceof Obj root)
                    || !new Text("available").equals(result.get("status"))
                    || !new Text("available").equals(root.get("status"))) continue;
            Value player = snapshot.get("played_character") instanceof Obj actor ? optional(actor, "character_id") : Nil.INSTANCE;
            if (Objects.equals(result.get("queried_snapshot_id"), snapshot.get("snapshot_id"))
                    && Objects.equals(result.get("queried_revision"), snapshot.get("revision"))
                    && Objects.equals(result.get("queried_native_revision"), snapshot.get("native_revision"))
                    && Objects.equals(root.get("snapshot_revision"), snapshot.get("native_revision"))
                    && Objects.equals(root.get("date_raw"), snapshot.get("date_raw"))
                    && Objects.equals(root.get("player_character_id"), player)
                    && result.get("query_sequence") instanceof IntegerValue sequence && sequence.value().signum() > 0)
                return result;
        }
        return Nil.INSTANCE;
    }

    private static Obj completePlan(OrdinaryPolicy.Draft draft) {
        Obj result = sameOrPut(draft.detail(), "policy", new Text(draft.policy()));
        result = sameOrPut(result, "phase", new Text(draft.phase()));
        return sameOrPut(result, "reason", new Text(draft.reason()));
    }

    private static Obj sameOrPut(Obj row, String field, Value expected) {
        if (row.members().containsKey(field)) {
            StrictJson.require(Objects.equals(row.get(field), expected), "complete original plan conflicts with actual " + field);
            return row;
        }
        return row.with(field, expected);
    }

    private static Obj publicCamera(Obj camera) {
        return camera.with("source_frame", publicFrame(object(camera.get("source_frame"), "camera source_frame")));
    }

    private static Obj publicFrame(Obj frame) {
        Obj result = frame;
        for (String field : List.of("revision", "native_revision", "connection_generation")) {
            Value value = frame.get(field);
            if (value instanceof IntegerValue integer) {
                StrictJson.require(integer.value().signum() >= 0
                        && integer.value().compareTo(StrictJson.UINT64_MAX) <= 0, "public planning frame uint64 required");
                result = result.with(field, new Text(integer.value().toString()));
            } else StrictJson.require(value == Nil.INSTANCE, "original planning identity must be an integer or null");
        }
        return result;
    }


    private static final List<String> SNAPSHOT_FIELDS = List.of("_private_faction_snapshot_v1",
            "_private_construction_snapshot_v1", "_private_family_marriage_snapshot_v1",
            "_private_council_snapshot_v1", "_private_m5_snapshot_v1");
    private static final List<String> HISTORY_FIELDS = List.of("_private_faction_history_v1",
            "_private_construction_history_v1", "_private_council_history_v1", "_private_m5_history_v1");

    /** Only these original envelope members carry complete snapshot/recorder DATA. */
    private static Obj publicExtras(Obj original, boolean encode) {
        Obj result = original;
        for (String field : SNAPSHOT_FIELDS) {
            Value value = original.get(field);
            if (value == null || value == Nil.INSTANCE) continue;
            Obj snapshot = object(value, field);
            RawJson input = RawJson.fullMaterial(DriverJson.encode(snapshot));
            RawJson converted = encode ? PublicSnapshotCodec.encodePlanningSnapshotData(input)
                    : PublicSnapshotCodec.decodePlanningSnapshotData(input);
            result = result.with(field, DriverJson.object(converted.bytes(), RawJson.MAXIMUM_BYTES));
        }
        for (String field : HISTORY_FIELDS) {
            Value value = original.get(field);
            if (value == null || value == Nil.INSTANCE) continue;
            StrictJson.require(value instanceof OpportunityJson.Arr, "original PLAN recorder array required: " + field);
            var history = (OpportunityJson.Arr)value;
            result = result.with(field, encode ? PublicSnapshotCodec.encodePlanningHistoryData(history)
                    : PublicSnapshotCodec.decodePlanningHistoryData(history));
        }
        Value scope = original.get("_private_lifestyle_scope_v1");
        if (scope instanceof Obj object)
            result = result.with("_private_lifestyle_scope_v1", role(object, "snapshot_revision", true, encode));
        else StrictJson.require(scope == null || scope == Nil.INSTANCE, "original LIFE scope object/null required");
        Value war = original.get("_private_lifestyle_war_frame_v1");
        if (war instanceof OpportunityJson.Arr frame) {
            StrictJson.require(frame.items().size() == 4, "original LIFE war frame must have four entries");
            var fields = new java.util.ArrayList<Value>(frame.items());
            fields.set(3, identity(fields.get(3), true, encode));
            result = result.with("_private_lifestyle_war_frame_v1", new OpportunityJson.Arr(fields));
        } else StrictJson.require(war == null || war == Nil.INSTANCE, "original LIFE war tuple/null required");
        Value pending = original.get("_private_lifestyle_pending_v1");
        if (pending instanceof Obj retained)
            result = result.with("_private_lifestyle_pending_v1", publicLifestylePending(retained, encode));
        else StrictJson.require(pending == null || pending == Nil.INSTANCE, "original LIFE pending object/null required");
        return result;
    }

    /** Original private LIFE intent/ACK DATA; this is neither a receipt nor an advance result. */
    private static Obj publicLifestylePending(Obj original, boolean encode) {
        StrictJson.require(original.members().keySet().containsAll(Set.of("status", "action_request_id",
                "target_key", "kind", "pre_public_revision", "episode_run_id", "source_frame",
                "native_command_submitted")), "complete original LIFE pending intent required");
        StrictJson.require(original.get("status") instanceof Text status
                && Set.of("action_state_unknown", "submitted_verification_pending").contains(status.value()),
                "original LIFE unresolved status required");
        Obj frame = object(original.get("source_frame"), "LIFE pending source_frame");
        StrictJson.require(frame.members().keySet().equals(Set.of("snapshot_id", "revision", "native_revision",
                "date_raw", "player_character_id")), "original LIFE pending source-frame fields differ");
        frame = role(role(frame, "revision", true, encode), "native_revision", true, encode);
        Obj result = role(original, "pre_public_revision", true, encode).with("source_frame", frame);
        Value submitted = original.get("native_command_submitted");
        StrictJson.require(submitted == Nil.INSTANCE || submitted instanceof OpportunityJson.Bool,
                "original LIFE submitted marker must preserve boolean/null");
        if (original.get("native_ack") instanceof Obj ack)
            result = result.with("native_ack", role(ack, "pre_public_revision", true, encode));
        else StrictJson.require(!original.members().containsKey("native_ack") || original.get("native_ack") == Nil.INSTANCE,
                "original LIFE ACK object/null required");
        // An invalid original ACK retained by the UNKNOWN error path remains separate from the intent.
        if (original.get("native_frame") instanceof Obj frameWithAck && frameWithAck.get("result") instanceof Obj ack)
            result = result.with("native_frame", frameWithAck.with("result",
                    role(ack, "pre_public_revision", true, encode)));
        return result;
    }

    /** Original compact Sway schema, separately owned from a complete snapshot export. */
    private static Obj publicSway(Obj original, boolean encode) {
        Obj snapshot = object(original.get("snapshot"), "Sway snapshot");
        snapshot = role(role(snapshot, "revision", false, encode), "native_revision", true, encode);
        Obj result = original.with("snapshot", snapshot);
        if (original.get("root") instanceof Obj root)
            result = result.with("root", role(root, "snapshot_revision", true, encode));
        else StrictJson.require(original.get("root") == Nil.INSTANCE, "Sway root must be an object or null");
        return result;
    }

    private static Obj role(Obj original, String field, boolean positive, boolean encode) {
        if (!original.members().containsKey(field)) return original;
        return original.with(field, identity(original.get(field), positive, encode));
    }

    private static Value identity(Value value, boolean positive, boolean encode) {
        if (value == Nil.INSTANCE) return value;
        BigInteger exact;
        if (encode) {
            StrictJson.require(value instanceof IntegerValue, "original PLAN identity must be a JSON integer");
            exact = ((IntegerValue)value).value();
            StrictJson.require(exact.signum() >= (positive ? 1 : 0)
                    && exact.compareTo(StrictJson.UINT64_MAX) <= 0, "original PLAN identity exceeds its uint64 domain");
        } else exact = PublicUnsigned64.parse(DriverJson.toNode(value),
                positive ? PublicUnsigned64.Minimum.ONE : PublicUnsigned64.Minimum.ZERO,
                PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL);
        return encode ? new Text(exact.toString()) : new IntegerValue(exact);
    }

    private static void validate(Obj row) {
        StrictJson.require(row.members().keySet().containsAll(BASE), "complete original public PLAN fields required");
        StrictJson.require(row.get("snapshot_id") instanceof Text text && !text.value().isBlank(), "public plan snapshot_id required");
        BigInteger revision = publicUint64(row.get("revision"), "revision");
        Obj frame = object(row.get("planning_source_frame"), "planning_source_frame");
        StrictJson.require(frame.members().keySet().equals(FRAME), "exact original planning-source-frame fields required");
        StrictJson.require(new Text("xar.ck3.planning-source-frame/v1").equals(frame.get("schema")), "planning source schema differs");
        StrictJson.require(frame.get("status") instanceof Text status
                && Set.of("complete", "partial").contains(status.value()), "planning source status required");
        StrictJson.require(row.get("snapshot_id").equals(frame.get("snapshot_id"))
                && revision.equals(publicUint64(frame.get("revision"), "source revision")), "public plan outer/source frame differs");
        if (frame.get("native_revision") != Nil.INSTANCE) publicUint64(frame.get("native_revision"), "native_revision");
        if (frame.get("connection_generation") != Nil.INSTANCE) publicUint64(frame.get("connection_generation"), "connection_generation");
        exactIntegerOrNull(frame.get("date_raw"), "date_raw", true);
        exactIntegerOrNull(frame.get("bridge_pid"), "bridge_pid", false);
        Value actor = frame.get("actor_character_id");
        if (actor != Nil.INSTANCE) {
            StrictJson.require(actor instanceof IntegerValue, "planning actor must preserve a JSON integer");
            NativeCharacterId.of(((IntegerValue) actor).value());
        }
        if (new Text("complete").equals(frame.get("status")))
            StrictJson.require(actor instanceof IntegerValue && frame.get("date_raw") instanceof IntegerValue
                    && frame.get("native_revision") != Nil.INSTANCE
                    && frame.get("connection_generation") != Nil.INSTANCE, "complete planning frame is missing its typed source");
        Obj plan = object(row.get("plan"), "plan");
        for (String name : List.of("policy", "phase", "reason"))
            StrictJson.require(plan.get(name) instanceof Text text && !text.value().isBlank(), "complete plan text required: " + name);
        StrictJson.require(plan.members().containsKey("selected_step")
                && (plan.get("selected_step") == Nil.INSTANCE
                    || plan.get("selected_step") instanceof Text step && !step.value().isBlank()),
                "original selected_step text/null presence required");
        publicExtras(row, false);
        if (row.get("_ordinary_sway_input_v1") instanceof Obj sway) publicSway(sway, false);
        // Validate the complete typed tree, preserving exact decimal tokens and every domain extension.
        PublicDataJson.encodeFullMaterial(row);
    }

    private static void exactIntegerOrNull(Value value, String name, boolean signed) {
        if (value == Nil.INSTANCE) return;
        StrictJson.require(value instanceof IntegerValue, "planning frame JSON integer required: " + name);
        BigInteger number = ((IntegerValue) value).value();
        StrictJson.require(number.compareTo(BigInteger.valueOf(signed ? Integer.MIN_VALUE : 0)) >= 0
                && number.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "planning frame integer range differs: " + name);
    }

    private static BigInteger publicUint64(Value value, String name) {
        StrictJson.require(value != null && value != Nil.INSTANCE, "required public planning uint64: " + name);
        return PublicUnsigned64.parse(DriverJson.toNode(value), PublicUnsigned64.Minimum.ZERO,
                PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL);
    }
    private static Obj object(Value value, String field) {
        StrictJson.require(value instanceof Obj, "original public PLAN object required: " + field); return (Obj) value;
    }
    private static Value optional(Obj object, String field) {
        return object.members().containsKey(field) ? object.get(field) : Nil.INSTANCE;
    }
}
