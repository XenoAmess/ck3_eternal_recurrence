package org.xar.ck3.control.application.battleadvance;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Value;

/** Narrow typed projection of the actual complete semantic frame; the unmodified source remains in Frame. */
public final class BattleAdvanceFrame {
    private BattleAdvanceFrame() { }
    public record Owner(int dateRaw, BigInteger bridgePid, BigInteger connectionGeneration, BigInteger episodeCharacterId,
            String episodeRunId, BigInteger playedCharacterId) {
        boolean same(Owner other, boolean terminal, boolean includeDate) {
            return bridgePid.equals(other.bridgePid) && connectionGeneration.equals(other.connectionGeneration)
                    && episodeCharacterId.equals(other.episodeCharacterId) && episodeRunId.equals(other.episodeRunId)
                    && (terminal || playedCharacterId.equals(other.playedCharacterId)) && (!includeDate || dateRaw == other.dateRaw);
        }
    }
    public enum Kind { ACTIVE_EVENT, PENDING_CHARACTER_INTERACTION, ONE_LIFE_TERMINAL, ACTIVE_WAR_SET_CHANGED }
    public record Boundary(Kind kind, Optional<Value> instanceId, Optional<String> terminalReason, Optional<Boolean> playedCharacterAlive,
            Owner owner, List<Integer> beforeWarIds, List<Integer> afterWarIds) {
        public Boundary {
            Objects.requireNonNull(kind); instanceId = Objects.requireNonNull(instanceId); terminalReason = Objects.requireNonNull(terminalReason);
            playedCharacterAlive = Objects.requireNonNull(playedCharacterAlive); Objects.requireNonNull(owner);
            beforeWarIds = List.copyOf(beforeWarIds); afterWarIds = List.copyOf(afterWarIds);
        }
        public boolean validIdentity() {
            return switch (kind) {
                case ACTIVE_EVENT, PENDING_CHARACTER_INTERACTION -> instanceId.isPresent();
                case ONE_LIFE_TERMINAL -> terminalReason.isPresent() && (playedCharacterAlive.equals(Optional.of(false))
                        || !owner.playedCharacterId.equals(owner.episodeCharacterId));
                case ACTIVE_WAR_SET_CHANGED -> !beforeWarIds.equals(afterWarIds) && normalizedWarIds(beforeWarIds) && normalizedWarIds(afterWarIds)
                        && instanceId.equals(Optional.of(new OpportunityJson.Text("active-wars:" + csv(beforeWarIds) + "->" + csv(afterWarIds))));
            };
        }
        public boolean same(Boundary other) {
            boolean terminal = kind == Kind.ONE_LIFE_TERMINAL && other.kind == Kind.ONE_LIFE_TERMINAL;
            return kind == other.kind && (terminal ? terminalReason.isPresent() && other.terminalReason.isPresent() : instanceId.equals(other.instanceId))
                    && owner.same(other.owner, terminal, !terminal);
        }
    }
    public record Army(Optional<Integer> id, boolean controllable, Optional<String> state, Optional<Integer> stateCode,
            Optional<BigInteger> combatId, boolean inCombat, boolean retreating, Optional<Integer> moveTarget,
            Optional<List<Integer>> route, Optional<Integer> currentProvince) {
        public Army {
            Objects.requireNonNull(id); Objects.requireNonNull(state); Objects.requireNonNull(stateCode); Objects.requireNonNull(combatId);
            Objects.requireNonNull(moveTarget); route = Objects.requireNonNull(route).map(List::copyOf); Objects.requireNonNull(currentProvince);
        }
        boolean combat() { return state.equals(Optional.of("combat")) || stateCode.equals(Optional.of(2)) || inCombat
                || combatId.filter(value -> !value.equals(BigInteger.valueOf(-1))).isPresent(); }
        boolean retreat() { return retreating || state.equals(Optional.of("retreating")) || stateCode.equals(Optional.of(6)); }
        boolean movingTo(int target) { return moveTarget.equals(Optional.of(target)) && route.isPresent() && !route.orElseThrow().isEmpty()
                && route.orElseThrow().stream().allMatch(province -> province > 0) && route.orElseThrow().getLast() == target && (state.equals(Optional.of("moving")) || state.equals(Optional.of("embarked"))
                    || stateCode.equals(Optional.of(4)) || stateCode.equals(Optional.of(7))); }
        boolean stationary() { return (state.equals(Optional.of("regular")) || state.isEmpty() && stateCode.equals(Optional.of(1)))
                && moveTarget.isEmpty() && route.isPresent() && route.orElseThrow().isEmpty() && currentProvince.filter(province -> province > 0).isPresent() && !inCombat && !retreating; }
    }
    public record War(int id, Optional<List<Integer>> objectiveProvinceIds, boolean playerSiege, boolean playerAssault) {
        public War { objectiveProvinceIds = Objects.requireNonNull(objectiveProvinceIds).map(List::copyOf); }
    }
    public record Snapshot(Frame original, Owner owner, BigInteger revision, BigInteger nativeRevision, boolean paused,
            boolean mapReady, int speed, List<Army> armies, List<War> wars, Optional<Boundary> decision) {
        public Snapshot { armies = List.copyOf(armies); wars = List.copyOf(wars); decision = Objects.requireNonNull(decision); }
        public List<Integer> watch() {
            List<Integer> result = controllableIds();
            StrictJson.require(!result.isEmpty() && result.size() <= 64, "complete 1..64 controllable public CUnit watch required");
            return result;
        }
        public List<Integer> controllableIds() {
            List<Integer> result = new ArrayList<>();
            for (Army army : armies) if (army.controllable) {
                int id = army.id.orElseThrow(() -> new IllegalArgumentException("controllable public CUnit identity unavailable"));
                StrictJson.require(id >= 0, "controllable public CUnit ID is outside the canonical native domain");
                StrictJson.require(!result.contains(id), "duplicate controllable public CUnit identity"); result.add(id);
            }
            result.sort(Integer::compareTo);
            return List.copyOf(result);
        }
        public boolean activeCombat(List<Integer> watch) { return armies.stream().anyMatch(army -> army.controllable && army.id.filter(watch::contains).isPresent() && army.combat()); }
        public boolean activeRetreat(List<Integer> watch) { return armies.stream().anyMatch(army -> army.controllable && army.id.filter(watch::contains).isPresent() && army.retreat()); }
        public boolean committedRoute(List<Integer> watch, int armyId, int target) {
            List<Army> matches = armies.stream().filter(army -> army.controllable && army.id.equals(Optional.of(armyId)) && watch.contains(armyId)).toList();
            return matches.size() == 1 && matches.getFirst().movingTo(target);
        }
        public HoldState hold(List<Integer> watch, BattleAdvanceStep.Hold request) {
            // Malformed identities mean unavailable; actual state transitions mean invalidated.
            Set<Integer> allIds = new HashSet<>();
            for (Army army : armies) if (army.id.isEmpty() || army.id.orElseThrow() < 0 || !allIds.add(army.id.orElseThrow())) return new HoldState(HoldStatus.UNAVAILABLE, "player_army_identity_unavailable");
            List<War> requested = wars.stream().filter(war -> war.id == request.warId()).toList();
            if (requested.size() > 1) return new HoldState(HoldStatus.UNAVAILABLE, "duplicate_requested_war");
            if (!requested.isEmpty() && requested.getFirst().objectiveProvinceIds.isEmpty()) return new HoldState(HoldStatus.UNAVAILABLE, "war_objective_scope_unavailable");
            if (!paused || !mapReady) return new HoldState(HoldStatus.INVALIDATED, "paused_map_required");
            if (decision.isPresent()) return new HoldState(HoldStatus.INVALIDATED, "pending_player_decision");
            if (!watch.equals(controllableIds())) return new HoldState(HoldStatus.INVALIDATED, "controllable_watch_set_changed");
            if (armies.isEmpty() || armies.stream().anyMatch(army -> !army.stationary())) return new HoldState(HoldStatus.INVALIDATED, "player_army_not_regular_idle_stationary");
            if (wars.stream().anyMatch(War::playerSiege)) return new HoldState(HoldStatus.INVALIDATED, "player_active_siege");
            if (wars.stream().anyMatch(War::playerAssault)) return new HoldState(HoldStatus.INVALIDATED, "player_active_assault");
            if (requested.isEmpty()) return new HoldState(HoldStatus.INVALIDATED, "war_not_active");
            if (!requested.getFirst().objectiveProvinceIds.orElseThrow().contains(request.objectiveProvinceId())) return new HoldState(HoldStatus.INVALIDATED, "objective_not_in_requested_war");
            Optional<Army> subject = armies.stream().filter(army -> army.id.equals(Optional.of(request.armyId()))).findFirst();
            if (subject.isEmpty() || !subject.orElseThrow().controllable || !watch.contains(request.armyId())) return new HoldState(HoldStatus.INVALIDATED, "subject_not_controllable");
            if (!subject.orElseThrow().currentProvince.equals(Optional.of(request.objectiveProvinceId()))) return new HoldState(HoldStatus.INVALIDATED, "subject_not_at_objective");
            return new HoldState(HoldStatus.MATCHED, "matched");
        }
    }
    public enum HoldStatus { MATCHED, INVALIDATED, UNAVAILABLE }
    public record HoldState(HoldStatus status, String reason) { }

    public static Snapshot decode(Frame frame) {
        Obj value = frame.semantic(); Obj diagnostics = object(value.get("diagnostics"), "diagnostics");
        Obj played = object(value.get("played_character"), "played_character");
        int date = integer(value.get("date_raw"), "date_raw", 0, Integer.MAX_VALUE);
        Owner owner = new Owner(date, big(diagnostics.get("bridge_pid"), "bridge_pid", true),
                big(diagnostics.get("connection_generation"), "connection_generation", true), big(value.get("episode_character_id"), "episode_character_id", true),
                OpportunityJson.text(value.get("episode_run_id"), "episode_run_id"), big(played.get("character_id"), "played_character.character_id", true));
        List<Army> armies = new ArrayList<>();
        for (Value row : OpportunityJson.array(value.get("player_armies"), "player_armies")) {
            Obj army = object(row, "player_army");
            armies.add(new Army(optionalInt(army.get("army_id"), "army_id", Integer.MIN_VALUE), truth(army.get("controllable"), "controllable"),
                    optionalText(army.get("army_state"), "army_state").map(text -> text.toLowerCase(Locale.ROOT)),
                    optionalInt(army.get("army_state_code"), "army_state_code", Integer.MIN_VALUE), optionalBig(army.get("combat_id"), "combat_id"),
                    truth(army.get("in_combat"), "in_combat"), truth(army.get("retreating"), "retreating"),
                    optionalInt(army.get("move_target_province_id"), "move_target_province_id", Integer.MIN_VALUE), optionalIds(army.get("route_province_ids"), "route_province_ids", Integer.MIN_VALUE),
                    optionalInt(army.get("current_province_id"), "current_province_id", Integer.MIN_VALUE)));
        }
        List<War> wars = new ArrayList<>();
        for (Value row : OpportunityJson.array(value.get("active_wars"), "active_wars")) {
            Obj war = object(row, "active_war"); boolean siege = false, assault = false;
            Value states = war.get("objective_province_states");
            if (states instanceof OpportunityJson.Arr rows) for (Value state : rows.items()) {
                if (!(state instanceof Obj objective) || !(objective.get("active_siege") instanceof Obj active)) continue;
                if (truth(active.get("player_army_besieging"), "player_army_besieging")) { siege = true; assault |= truth(active.get("assault_in_progress"), "assault_in_progress"); }
            }
            wars.add(new War(integer(war.get("war_id"), "war_id", 1, Integer.MAX_VALUE), optionalIds(war.get("war_objective_province_ids"), "war_objective_province_ids", 1), siege, assault));
        }
        boolean paused = OpportunityJson.bool(value.get("paused"), "paused"), ready = OpportunityJson.bool(value.get("map_ready"), "map_ready");
        return new Snapshot(frame, owner, big(value.get("revision"), "revision", false), big(value.get("native_revision"), "native_revision", false), paused, ready,
                integer(value.get("speed"), "speed", 1, 5), armies, wars, decision(value, played, owner));
    }
    public static void bind(ActionCommand command, Snapshot snapshot, boolean entry) {
        Frame frame = snapshot.original;
        StrictJson.require(command.source().equals(frame.source()) && command.sessionId().equals(frame.sessionId())
                && command.before().game().equals(frame.identity().game()) && command.before().machineId().equals(frame.identity().machineId())
                && command.before().frame().episodeRunId().equals(frame.identity().frame().episodeRunId())
                && command.before().frame().identity().player().equals(snapshot.owner.episodeCharacterId), "same source/session/Game/episode required");
        if (entry) StrictJson.require(command.before().equals(frame.identity()), "pre-submission paused-frame revision mismatch");
    }
    public static Optional<Boundary> boundary(Snapshot start, Snapshot current) {
        if (current.decision.isPresent()) return current.decision;
        List<Integer> before = warIds(start), after = warIds(current);
        if (before.equals(after) || !current.paused || !current.mapReady || current.revision.compareTo(start.revision) <= 0
                || current.owner.dateRaw < start.owner.dateRaw || (current.owner.dateRaw - start.owner.dateRaw) % 24 != 0
                || !start.owner.same(current.owner, false, false)) return Optional.empty();
        String id = "active-wars:" + csv(before) + "->" + csv(after);
        return Optional.of(new Boundary(Kind.ACTIVE_WAR_SET_CHANGED, Optional.of(new OpportunityJson.Text(id)), Optional.empty(), Optional.empty(), current.owner, before, after));
    }
    public static boolean isNew(Snapshot start, Snapshot current) {
        if (current.decision.isEmpty()) return false;
        Boundary boundary = current.decision.orElseThrow();
        return (start.decision.isEmpty() || !start.decision.orElseThrow().same(boundary)) && current.revision.compareTo(start.revision) > 0
                && start.owner.same(current.owner, boundary.kind == Kind.ONE_LIFE_TERMINAL, false);
    }
    public static boolean freshPausedBoundary(Snapshot start, Snapshot before, Snapshot after, Optional<Boundary> expected, int pauseCount) {
        Optional<Boundary> boundary = after.decision;
        if (boundary.isEmpty() || pauseCount > 1 || pauseCount < 0 || !after.paused || !after.mapReady || after.revision.compareTo(before.revision) <= 0
                || after.nativeRevision.compareTo(before.nativeRevision) < 0 || !isNew(start, after)) return false;
        boolean terminal = boundary.orElseThrow().kind == Kind.ONE_LIFE_TERMINAL && expected.filter(item -> item.kind == Kind.ONE_LIFE_TERMINAL).isPresent();
        if (!before.owner.same(after.owner, terminal, !terminal) || terminal && after.owner.dateRaw < before.owner.dateRaw) return false;
        if (expected.isPresent() && !expected.orElseThrow().same(boundary.orElseThrow())) return false;
        return pauseCount != 0 || expected.isPresent() && !before.paused && before.decision.filter(expected.orElseThrow()::same).isPresent();
    }
    private static Optional<Boundary> decision(Obj value, Obj played, Owner owner) {
        Value event = requiredNullable(value, "active_event"), pending = requiredNullable(value, "pending_character_interaction");
        if (event != OpportunityJson.Nil.INSTANCE) return Optional.of(new Boundary(Kind.ACTIVE_EVENT, instance(object(event, "active_event")), Optional.empty(), Optional.empty(), owner, List.of(), List.of()));
        if (pending != OpportunityJson.Nil.INSTANCE) return Optional.of(new Boundary(Kind.PENDING_CHARACTER_INTERACTION, instance(object(pending, "pending_character_interaction")), Optional.empty(), Optional.empty(), owner, List.of(), List.of()));
        Optional<String> reason = optionalText(requiredNullable(value, "one_life_terminal_reason"), "one_life_terminal_reason");
        Optional<Boolean> alive = optionalBool(played.get("alive"), "played_character.alive");
        if (reason.isPresent() || alive.equals(Optional.of(false)) || !owner.playedCharacterId.equals(owner.episodeCharacterId))
            return Optional.of(new Boundary(Kind.ONE_LIFE_TERMINAL, Optional.empty(), Optional.of(reason.orElse(alive.equals(Optional.of(false)) ? "played_character_dead" : "played_character_changed")), alive, owner, List.of(), List.of()));
        return Optional.empty();
    }
    private static Optional<Value> instance(Obj object) {
        Value value = object.get("instance_id");
        if (absent(value)) return Optional.empty();
        StrictJson.require(value instanceof OpportunityJson.Text || value instanceof OpportunityJson.IntegerValue, "actual native instance ID string/integer required");
        return Optional.of(value);
    }
    private static List<Integer> warIds(Snapshot snapshot) {
        List<Integer> ids = snapshot.wars.stream().map(War::id).sorted().toList();
        StrictJson.require(normalizedWarIds(ids), "complete unique active WarID set required"); return ids;
    }
    private static boolean normalizedWarIds(List<Integer> ids) { return ids.stream().allMatch(id -> id > 0) && ids.equals(ids.stream().distinct().sorted().toList()); }
    private static String csv(List<Integer> ids) { return ids.isEmpty() ? "-" : String.join(",", ids.stream().map(String::valueOf).toList()); }
    private static Value requiredNullable(Obj value, String key) { StrictJson.require(value.members().containsKey(key), "missing differs from explicit null: " + key); return value.get(key); }
    private static Obj object(Value value, String key) { return OpportunityJson.object(value, key); }
    private static boolean absent(Value value) { return value == null || value == OpportunityJson.Nil.INSTANCE; }
    private static Optional<String> optionalText(Value value, String key) { return absent(value) ? Optional.empty() : Optional.of(OpportunityJson.text(value, key)); }
    private static Optional<Boolean> optionalBool(Value value, String key) { return absent(value) ? Optional.empty() : Optional.of(OpportunityJson.bool(value, key)); }
    private static boolean truth(Value value, String key) { return optionalBool(value, key).orElse(false); }
    private static Optional<BigInteger> optionalBig(Value value, String key) { return absent(value) ? Optional.empty() : Optional.of(OpportunityJson.integer(value, key)); }
    private static Optional<Integer> optionalInt(Value value, String key, int minimum) { return absent(value) ? Optional.empty() : Optional.of(integer(value, key, minimum, Integer.MAX_VALUE)); }
    private static Optional<List<Integer>> optionalIds(Value value, String key, int minimum) {
        if (absent(value)) return Optional.empty();
        return Optional.of(OpportunityJson.array(value, key).stream().map(item -> integer(item, key, minimum, Integer.MAX_VALUE)).toList());
    }
    private static BigInteger big(Value value, String key, boolean positive) { BigInteger result = OpportunityJson.integer(value, key); StrictJson.require(result.signum() >= (positive ? 1 : 0), "nonnegative integer required: " + key); return result; }
    private static int integer(Value value, String key, int minimum, int maximum) { BigInteger result = OpportunityJson.integer(value, key); StrictJson.require(result.compareTo(BigInteger.valueOf(minimum)) >= 0 && result.compareTo(BigInteger.valueOf(maximum)) <= 0, "native integer range: " + key); return result.intValueExact(); }
}
