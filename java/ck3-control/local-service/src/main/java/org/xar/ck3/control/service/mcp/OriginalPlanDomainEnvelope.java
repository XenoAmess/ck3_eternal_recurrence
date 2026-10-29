package org.xar.ck3.control.service.mcp;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.root.RootRuntimeDomainSettings.PlanFlags;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneCodec;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.*;
import org.xar.ck3.control.wave3.governance.lifestylescope.LifestyleScopePolicy;

/**
 * Original service.py plan_from_view private DATA envelope and consumer removals.
 * This projection makes no Native read and mints no scope, action or receipt authority.
 * Draft.detail remains the inner plan; source-frame/camera/Sway are owned separately.
 */
public final class OriginalPlanDomainEnvelope {
    private OriginalPlanDomainEnvelope() { }
    private static final String LIFE_SCOPE = "_private_lifestyle_scope_v1";
    private static final String LIFE_PENDING = "_private_lifestyle_pending_v1";
    private static final String LIFE_WAR = "_private_lifestyle_war_frame_v1";
    private static final String WINDOW = "_private_window_priority_v1";
    /** The exact boundary evidenced by this actual planner trace, not by the last phase alone. */
    public enum Branch {
        BEFORE_PLAN(false), PENDING_MATERIAL(false), WINDOW_PRIORITY(true),
        OPENING_FOCUS(true), ORDINARY(true);
        private final boolean commonAnnotations;
        Branch(boolean commonAnnotations) { this.commonAnnotations = commonAnnotations; }
        public boolean commonAnnotations() { return commonAnnotations; }
    }
    public record Projection(Branch branch, Obj beforeConsumers, Obj survivingTopLevel) {
        public Projection {
            Objects.requireNonNull(branch); Objects.requireNonNull(beforeConsumers);
            Objects.requireNonNull(survivingTopLevel);
        }
    }

    public static Obj produce(PlanningRequest original, PlanningResult actual, PlanFlags flags) {
        return project(original, actual, flags).survivingTopLevel();
    }

    public static Branch branch(PlanningRequest original, PlanningResult actual) {
        requireSame(original, actual);
        if (actual.trace().finalPlan().isEmpty()) return Branch.BEFORE_PLAN;
        OrdinaryPolicy.Draft draft = actual.trace().finalPlan().orElseThrow();
        if (visited(actual, PlanningStage.ORDINARY_CORE) || visited(actual, PlanningStage.THREE_WAY_WAR_EXIT))
            return Branch.ORDINARY;
        if (visited(actual, PlanningStage.OPENING_LIFESTYLE_FOCUS)) return Branch.OPENING_FOCUS;
        if (draft.kind() == OrdinaryPolicy.Kind.FOREGROUND || draft.kind() == OrdinaryPolicy.Kind.TERMINAL)
            return Branch.WINDOW_PRIORITY;
        if (draft.kind() == OrdinaryPolicy.Kind.MATERIAL_RECEIPT
                || draft.phase().equals("foreground_window_unavailable_before_pending_receipt")
                || draft.phase().equals("pending_material_independent_receipt")) return Branch.PENDING_MATERIAL;
        return Branch.BEFORE_PLAN;
    }

    public static Projection project(PlanningRequest original, PlanningResult actual, PlanFlags flags) {
        requireSame(original, actual); Objects.requireNonNull(flags);
        StrictJson.require(flags.initialLifestyleFocusRequired()
                == original.observations().initialLifestyleFocusRequired(),
                "original opening flag differs from the actual PlanningRequest");
        Branch branch = branch(original, actual);
        if (!branch.commonAnnotations()) return new Projection(branch, object(), object());
        Obj snapshot = original.observations().snapshot();
        Arr history = new Arr(new ArrayList<Value>(original.observations().history()));
        boolean opening = flags.initialLifestyleFocusRequired();
        Value scope = flags.lifestyleFormalTrial() ? lifestyleScope(original, opening) : Nil.INSTANCE;
        Value pending = flags.lifestyleFormalTrial() ? unresolvedLifestyle(original) : Nil.INSTANCE;
        Value warFrame = flags.lifestyleFormalTrial() && !opening && original.observations().warInProgress()
            ? new Arr(List.of(optional(snapshot, "episode_run_id"),
                optional(OpportunityJson.object(snapshot.get("played_character"), "played_character"), "character_id"),
                optional(snapshot, "date_raw"), optional(snapshot, "native_revision"))) : Nil.INSTANCE;
        Obj before = object(WINDOW, new Bool(branch == Branch.WINDOW_PRIORITY),
            LIFE_SCOPE, scope, LIFE_PENDING, pending, LIFE_WAR, warFrame,
            "_private_faction_snapshot_v1", enabled(flags.factionGiftFormalTrial(), snapshot),
            "_private_faction_history_v1", enabled(flags.factionGiftFormalTrial(), history),
            "_private_construction_snapshot_v1", enabled(flags.constructionFormalTrial(), snapshot),
            "_private_construction_history_v1", enabled(flags.constructionFormalTrial(), history),
            "_private_family_marriage_snapshot_v1", enabled(flags.familyMarriageFormalTrial(), snapshot),
            "_private_council_snapshot_v1", enabled(flags.councilAction(), snapshot),
            "_private_council_history_v1", enabled(flags.councilAction(), history),
            "_private_m5_snapshot_v1", enabled(flags.m5JointCollector(), snapshot),
            "_private_m5_history_v1", enabled(flags.m5JointCollector(), history));
        var surviving = new LinkedHashMap<String, Value>(before.members());
        surviving.remove(WINDOW); // service.py2826 always consumes this priority marker.
        if (branch == Branch.WINDOW_PRIORITY) surviving.clear();
        else if (branch == Branch.OPENING_FOCUS) {
            surviving.keySet().retainAll(Set.of(LIFE_SCOPE, LIFE_PENDING, LIFE_WAR));
            // Only the actual receipt consumer pops LIFE inputs; normal opening observation/new focus retains them.
            // Opening consumption-query phase itself does NOT mean the receipt helper ran.
            String step = actual.trace().finalPlan().orElseThrow().command()
                .map(command -> command.operation().value()).orElse("");
            if (step.equals("private-query-player-lifestyle-receipt-v1"))
                removeLife(surviving);
        } else {
            if (visited(actual, PlanningStage.M5_JOINT_PEACETIME)) removePair(surviving, "m5");
            if (visited(actual, PlanningStage.LIFESTYLE)) removeLife(surviving);
            if (visited(actual, PlanningStage.FACTION_GIFT)) removePair(surviving, "faction");
            if (visited(actual, PlanningStage.CONSTRUCTION)) removePair(surviving, "construction");
            if (visited(actual, PlanningStage.FAMILY_AND_EDUCATION))
                surviving.remove("_private_family_marriage_snapshot_v1");
            if (visited(actual, PlanningStage.COUNCIL)) removePair(surviving, "council");
        }
        return new Projection(branch, before, new Obj(surviving));
    }

    /** Exact old reverse selection, detached DATA only; status 'applied' is never material authority. */
    private static Value unresolvedLifestyle(PlanningRequest request) {
        String episode = request.before().frame().episodeRunId();
        List<Obj> history = request.observations().history();
        for (int index = history.size() - 1; index >= 0; index--) {
            Obj row = history.get(index); Value command = row.get("command");
            boolean submit = textIs(command, "private-select-player-lifestyle-perk-v1")
                || textIs(command, "private-select-player-lifestyle-stock-focus-v1");
            boolean receipt = textIs(command, "private-query-player-lifestyle-receipt-v1");
            if ((!submit && !receipt) || !(row.get("result") instanceof Obj result)
                    || !textIs(result.get("episode_run_id"), episode)) continue;
            if (receipt && textIs(result.get("status"), "applied")) return Nil.INSTANCE;
            if (submit) return textIs(result.get("status"), "action_state_unknown")
                    || textIs(result.get("status"), "submitted_verification_pending") ? result : Nil.INSTANCE;
        }
        return Nil.INSTANCE;
    }

    /** Reuse the unique shared same-frame scope algorithm on a typed projection of the original history. */
    private static Obj lifestyleScope(PlanningRequest request, boolean opening) {
        var frame = request.before().frame();
        Snapshot snapshot = new Snapshot(Field.of(request.observations().paused()),
            Field.of(OpportunityJson.array(request.observations().snapshot().get("active_wars"), "active_wars").size()),
            Field.of(frame.identity().player()), Field.of(frame.identity().nativeRevision()), Field.of(frame.revision()),
            Field.of(frame.snapshotId()), Field.of(frame.identity().dateRaw()));
        List<HistoryRow> rows = new ArrayList<>();
        for (Obj row : request.observations().history()) {
            if (!textIs(row.get("command"), "query-campaign-root-context-v1")) continue;
            Value root = row.get("result") instanceof Obj result ? result.get("campaign_root_context") : null;
            rows.add(new HistoryRow(Field.of("query-campaign-root-context-v1"), boolField(row.get("ok")),
                root instanceof Obj observed ? Field.of(root(observed)) : absent(root)));
        }
        SceneInput input = new SceneInput(snapshot, rows);
        var assessed = opening || !request.observations().bridgeCapabilities().contains(LifestyleScopePolicy.ALL_LIFESTYLE_CAPABILITY)
            ? LifestyleScopePolicy.sameFrameFeudalLifestyleScope(input)
            : LifestyleScopePolicy.sameFramePlayerLifestylePerkScope(input);
        return OpportunityJson.object(OpportunityJson.parse(ConstructionSceneCodec.encodeRootScope(assessed.root())), "LIFE scope");
    }
    private static Root root(Obj root) {
        Value gov = root.get("government"), council = root.get("council");
        Field<GovernmentObservation> government = gov instanceof Obj value
            ? Field.of(new GovernmentObservation(textField(value.get("key")), strings(value.get("flags")))) : absent(gov);
        Field<Council> observedCouncil = absent(council);
        if (council instanceof Obj value) {
            Value raw = value.get("positions"); Field<List<Position>> positions = absent(raw);
            if (raw instanceof Arr list && list.items().stream().allMatch(Obj.class::isInstance)) {
                List<Position> projected = new ArrayList<>();
                for (Value item : list.items()) {
                    Obj p = (Obj) item;
                    projected.add(new Position(textField(p.get("position_key")), integerField(p.get("incumbent_character_id")),
                        textField(p.get("task_key")), boolField(p.get("frozen"))));
                }
                positions = Field.of(projected);
            }
            observedCouncil = Field.of(new Council(textField(value.get("status")), positions));
        }
        return new Root(textField(root.get("status")), integerField(root.get("snapshot_revision")),
            integerField(root.get("date_raw")), integerField(root.get("player_character_id")), government, observedCouncil);
    }
    private static Field<List<String>> strings(Value value) {
        if (!(value instanceof Arr array)) return absent(value);
        List<String> result = new ArrayList<>();
        for (Value item : array.items()) if (item instanceof Text text) result.add(text.value());
        return Field.of(result);
    }
    private static Field<String> textField(Value value) { return value instanceof Text text ? Field.of(text.value()) : absent(value); }
    private static Field<BigInteger> integerField(Value value) { return value instanceof IntegerValue integer ? Field.of(integer.value()) : absent(value); }
    private static Field<Boolean> boolField(Value value) { return value instanceof Bool bool ? Field.of(bool.value()) : absent(value); }
    private static <T> Field<T> absent(Value value) { return value == Nil.INSTANCE ? Field.nil() : Field.missing(); }
    private static boolean visited(PlanningResult result, PlanningStage stage) {
        return result.trace().visits().stream().anyMatch(visit -> visit.stage() == stage
            && visit.outcome() != PlanTrace.Outcome.MISSING_PRODUCER);
    }
    private static void requireSame(PlanningRequest original, PlanningResult actual) {
        Objects.requireNonNull(original); Objects.requireNonNull(actual);
        StrictJson.require(original.before().equals(actual.trace().before()), "PLAN envelope crossed the actual source frame");
    }
    private static void removeLife(LinkedHashMap<String, Value> result) { result.remove(LIFE_SCOPE); result.remove(LIFE_PENDING); result.remove(LIFE_WAR); }
    private static void removePair(LinkedHashMap<String, Value> result, String domain) {
        result.remove("_private_" + domain + "_snapshot_v1"); result.remove("_private_" + domain + "_history_v1");
    }
    private static Value enabled(boolean enabled, Value value) { return enabled ? value : Nil.INSTANCE; }
    private static Value optional(Obj object, String key) { Value value = object.get(key); return value == null ? Nil.INSTANCE : value; }
    private static boolean textIs(Value value, String expected) { return value instanceof Text text && text.value().equals(expected); }
    private static Obj object(Object... pairs) {
        LinkedHashMap<String, Value> values = new LinkedHashMap<>();
        for (int i = 0; i < pairs.length; i += 2) {
            StrictJson.require(pairs[i] instanceof String && pairs[i + 1] instanceof Value, "typed JSON pair required");
            values.put((String) pairs[i], (Value) pairs[i + 1]);
        }
        return new Obj(values);
    }
}
