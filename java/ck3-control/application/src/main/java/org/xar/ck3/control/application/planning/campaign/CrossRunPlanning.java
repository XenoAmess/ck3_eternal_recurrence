package org.xar.ck3.control.application.planning.campaign;

import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Predicate;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original one-life memory and opening priorities. Pure data reduction, never an action or writer. */
public final class CrossRunPlanning {
    private CrossRunPlanning() { }
    public static final int MAX_BYTES = 131_072;
    private static final String POLICY = "one-life-visible-outcomes-v1";

    /** Missing directive fields retain their original absence; focus alone interprets the old defaults. */
    public record Directive(Optional<BigInteger> priority, Optional<String> action, Optional<String> reason) {
        public Directive {
            Objects.requireNonNull(priority); Objects.requireNonNull(action); Objects.requireNonNull(reason);
            action.ifPresent(StrictJson::text); reason.ifPresent(StrictJson::text);
        }
    }
    public record Plan(String policy, boolean continueAsHeirAfterDeath, List<Directive> priorities) {
        public Plan {
            StrictJson.text(policy); priorities = List.copyOf(priorities);
            StrictJson.require(!continueAsHeirAfterDeath, "one-life memory never grants heir continuation");
        }
    }
    public record Achievements(boolean palermoHolyWarWon, boolean armiesDisbanded,
            boolean danishBetrothalAccepted, boolean partitionRiskVisible) { }
    public record Terminal(String reason, boolean technicalSettlementHandoff, Value score) {
        public Terminal { StrictJson.text(reason); Objects.requireNonNull(score); }
    }
    public record Checkpoint(Optional<String> name, Optional<BigInteger> size, Optional<String> sha256) {
        public Checkpoint {
            Objects.requireNonNull(name); Objects.requireNonNull(size); Objects.requireNonNull(sha256);
            name.ifPresent(StrictJson::text);
            size.ifPresent(value -> StrictJson.require(value.signum() >= 0, "nonnegative checkpoint size required"));
            sha256.ifPresent(value -> StrictJson.require(value.matches("[0-9a-f]{64}"), "exact checkpoint SHA256 required"));
        }
    }
    public record Episode(String runId, Instant finishedAt, String terminalReason, boolean technicalSettlementHandoff,
            Value score, Achievements achievements, Optional<Checkpoint> latestCheckpoint, List<String> successfulSteps) {
        public Episode {
            StrictJson.text(runId); Objects.requireNonNull(finishedAt); StrictJson.text(terminalReason);
            Objects.requireNonNull(score); Objects.requireNonNull(achievements); Objects.requireNonNull(latestCheckpoint);
            successfulSteps = List.copyOf(successfulSteps); successfulSteps.forEach(StrictJson::text);
        }
    }
    public record State(List<Episode> episodes, Plan nextRunPlan, Optional<Instant> updatedAt) {
        public State {
            episodes = List.copyOf(episodes); Objects.requireNonNull(nextRunPlan); Objects.requireNonNull(updatedAt);
            StrictJson.require(episodes.stream().map(Episode::runId).distinct().count() == episodes.size(),
                    "one retained episode per exact run identity required");
        }
    }

    public static Plan nextRunPlan(Achievements value) {
        Objects.requireNonNull(value); List<Directive> rows = new ArrayList<>();
        rows.add(value.palermoHolyWarWon()
                ? directive(100, "repeat_palermo_opening_war_when_visible_conditions_match", "the previous life converted the Palermo holy war into a confirmed win")
                : directive(70, "reassess_first_low_cost_expansion", "the previous life did not prove a completed Palermo victory"));
        rows.add(value.danishBetrothalAccepted()
                ? directive(80, "repeat_high_value_child_alliance_review", "the previous life secured the visible Danish betrothal")
                : directive(100, "seek_current_life_marriage_alliance", "the previous life has no confirmed alliance marriage"));
        if (value.partitionRiskVisible()) rows.add(directive(60, "reduce_current_ruler_partition_loss", "succession review exposed title loss during the current life"));
        rows.add(directive(10, "finish_on_player_death_and_record_score", "this is a one-generation roguelike; death ends the episode"));
        return new Plan(POLICY, false, rows);
    }
    public static State empty() {
        return new State(List.of(), nextRunPlan(new Achievements(false, false, false, false)), Optional.empty());
    }

    /** Single shared ordinary-core/family/event reader. Priorities are intent, not the current selected action. */
    public static Optional<String> focus(Optional<Obj> plan) {
        Objects.requireNonNull(plan);
        if (plan.isEmpty()) return Optional.empty();
        Obj value = plan.orElseThrow();
        if (value.get("policy") != null) text(value.get("policy"), "policy");
        if (value.get("continue_as_heir_after_death") != null) bool(value.get("continue_as_heir_after_death"), "continue_as_heir_after_death");
        if (value.get("priorities") == null) return Optional.empty();
        return focus(directives(value.get("priorities")));
    }
    public static Optional<String> focus(Plan plan) { return focus(Objects.requireNonNull(plan).priorities()); }
    private static Optional<String> focus(List<Directive> rows) {
        List<Directive> ranked = rows.stream().sorted(Comparator
                .comparing((Directive row) -> row.priority().orElse(BigInteger.ZERO)).reversed()
                .thenComparing(row -> row.action().orElse(""), JointBudgetSelector::comparePythonText)).toList();
        for (Directive row : ranked) {
            String action = row.action().orElse("").toLowerCase(Locale.ROOT);
            if (contains(action, "war", "expansion", "palermo")) return Optional.of("war");
            if (contains(action, "marriage", "alliance", "betrothal")) return Optional.of("marriage");
            if (contains(action, "succession", "partition")) return Optional.of("succession");
        }
        return Optional.empty();
    }

    /** The authoritative owner supplies the original surviving command rows and actual terminal result. */
    public static State recordEpisode(State previous, String runId, List<Obj> commands, Obj terminal, Instant finishedAt) {
        Objects.requireNonNull(previous); StrictJson.text(runId); Objects.requireNonNull(commands);
        Objects.requireNonNull(terminal); Objects.requireNonNull(finishedAt);
        Terminal actualTerminal = parseTerminal(terminal);
        commands.forEach(CrossRunPlanning::validateCommand);
        List<Obj> expanded = expand(commands);
        expanded.forEach(CrossRunPlanning::validateCommand);
        Optional<Obj> war = last(expanded, step -> step.equals("war-enforce-demands") || step.startsWith("enforce-demands-"));
        Optional<Obj> disband = last(expanded, step -> step.equals("war-disband-armies") || step.startsWith("disband-army-"));
        Optional<Obj> succession = last(expanded, "succession-review"::equals);
        Achievements achievements = new Achievements(
                war.filter(row -> status(row, "war_victory", "victory_enforced")).isPresent(),
                disband.filter(row -> status(row, "army_disband", "disbanded") || status(row, "war_action", "disbanded")).isPresent(),
                acceptedMarriage(expanded),
                succession.filter(row -> child(row, "succession_state").filter(value -> yes(value.get("partition_risk_visible"))).isPresent()).isPresent());
        Optional<Checkpoint> checkpoint = last(expanded, "save-checkpoint"::equals)
                .flatMap(row -> child(row, "checkpoint")).map(CrossRunPlanning::checkpoint);
        // Original successful_steps is deliberately the outer list, not the expanded auto-run turns.
        List<String> successful = commands.stream().filter(row -> yes(row.get("ok")) && row.get("command") instanceof Text)
                .map(row -> text(row.get("command"), "command")).toList();
        Episode episode = new Episode(runId, finishedAt, actualTerminal.reason(), actualTerminal.technicalSettlementHandoff(), actualTerminal.score(), achievements, checkpoint, successful);
        List<Episode> episodes = new ArrayList<>(previous.episodes().stream().filter(row -> !row.runId().equals(runId)).toList());
        episodes.add(episode);
        return new State(episodes, nextRunPlan(achievements), Optional.of(finishedAt));
    }
    /** The actual death producer appends its successful terminal row exactly once before reducing history. */
    public static State recordScoredTerminal(State previous, String runId, List<Obj> originalBefore,
            Obj terminal, Instant finishedAt) {
        Objects.requireNonNull(originalBefore); Objects.requireNonNull(terminal);
        Value score=parseTerminal(terminal).score();
        StrictJson.require("complete".equals(text(terminal.get("settlement_status"), "settlement_status"))
                && (score instanceof IntegerValue || score instanceof DecimalValue), "complete actual numeric scored terminal required");
        StrictJson.require(originalBefore.stream().noneMatch(row -> "death-terminal".equals(string(row.get("command")))),
                "original terminal predecessor already contains a death-terminal; do not record it twice");
        var complete = new ArrayList<Obj>(originalBefore);
        complete.add(obj().with("command", new Text("death-terminal")).with("ok", new Bool(true)).with("result", terminal));
        return recordEpisode(previous, runId, List.copyOf(complete), terminal, finishedAt);
    }
    public static Terminal parseTerminal(Obj row) {
        Objects.requireNonNull(row);
        StrictJson.require(bool(row.get("terminal"), "terminal"), "one-life episode requires a terminal death result");
        String reason = row.get("terminal_reason") == null || row.get("terminal_reason") == Nil.INSTANCE
                ? "player_death" : text(row.get("terminal_reason"), "terminal_reason");
        boolean handoff = row.get("technical_settlement_handoff") != null && bool(row.get("technical_settlement_handoff"), "technical_settlement_handoff");
        return new Terminal(reason, handoff, row.get("score") == null ? Nil.INSTANCE : row.get("score"));
    }

    public static Obj planJson(Plan value) {
        return obj().with("policy", new Text(value.policy())).with("continue_as_heir_after_death", new Bool(value.continueAsHeirAfterDeath()))
                .with("priorities", new Arr(value.priorities().stream().map(CrossRunPlanning::directiveJson).map(Value.class::cast).toList()));
    }
    public static Plan parsePlan(Obj row) {
        exact(row, Set.of("policy", "continue_as_heir_after_death", "priorities"));
        return new Plan(text(row.get("policy"), "policy"), bool(row.get("continue_as_heir_after_death"), "continue_as_heir_after_death"), directives(row.get("priorities")));
    }
    public static byte[] encodeState(State value) {
        Obj row = obj().with("format_version", number(1)).with("mode", new Text("one_life_roguelike"))
                .with("continue_as_heir_after_death", new Bool(false))
                .with("episodes", new Arr(value.episodes().stream().map(CrossRunPlanning::episodeJson).map(Value.class::cast).toList()))
                .with("next_run_plan", planJson(value.nextRunPlan()));
        if (value.updatedAt().isPresent()) row = row.with("updated_at", new Text(value.updatedAt().orElseThrow().toString()));
        byte[] raw = OpportunityJson.encode(row);
        StrictJson.require(raw.length <= MAX_BYTES, "one-life history exceeds explicit application boundary"); return raw;
    }
    public static State decodeState(byte[] raw) {
        Obj row = object(OpportunityJson.parse(raw), "cross-run state");
        Set<String> fields = row.get("updated_at") == null
                ? Set.of("format_version", "mode", "continue_as_heir_after_death", "episodes", "next_run_plan")
                : Set.of("format_version", "mode", "continue_as_heir_after_death", "episodes", "next_run_plan", "updated_at");
        exact(row, fields);
        StrictJson.require(integer(row.get("format_version"), "format_version").equals(BigInteger.ONE)
                && text(row.get("mode"), "mode").equals("one_life_roguelike")
                && !bool(row.get("continue_as_heir_after_death"), "continue_as_heir_after_death"), "one-life history constants differ");
        return new State(array(row.get("episodes"), "episodes").stream().map(value -> parseEpisode(object(value, "episode"))).toList(),
                parsePlan(object(row.get("next_run_plan"), "next_run_plan")),
                row.get("updated_at") == null ? Optional.empty() : Optional.of(Instant.parse(text(row.get("updated_at"), "updated_at"))));
    }
    public static Obj episodeJson(Episode value) {
        Achievements a = value.achievements();
        Obj achievements = obj().with("palermo_holy_war_won", new Bool(a.palermoHolyWarWon())).with("armies_disbanded", new Bool(a.armiesDisbanded()))
                .with("danish_betrothal_accepted", new Bool(a.danishBetrothalAccepted())).with("partition_risk_visible", new Bool(a.partitionRiskVisible()));
        Value checkpoint = value.latestCheckpoint().<Value>map(item -> obj().with("name", nullableText(item.name()))
                .with("size", item.size().<Value>map(IntegerValue::new).orElse(Nil.INSTANCE)).with("sha256", nullableText(item.sha256()))).orElse(Nil.INSTANCE);
        return obj().with("run_id", new Text(value.runId())).with("finished_at", new Text(value.finishedAt().toString()))
                .with("terminal_reason", new Text(value.terminalReason())).with("continue_as_heir_after_death", new Bool(false))
                .with("technical_settlement_handoff", new Bool(value.technicalSettlementHandoff())).with("heir_gameplay_actions", number(0))
                .with("score", value.score()).with("achievements", achievements).with("latest_checkpoint", checkpoint)
                .with("successful_steps", new Arr(value.successfulSteps().stream().map(Text::new).map(Value.class::cast).toList()));
    }
    private static Episode parseEpisode(Obj row) {
        exact(row, Set.of("run_id", "finished_at", "terminal_reason", "continue_as_heir_after_death", "technical_settlement_handoff", "heir_gameplay_actions", "score", "achievements", "latest_checkpoint", "successful_steps"));
        StrictJson.require(!bool(row.get("continue_as_heir_after_death"), "continue_as_heir_after_death")
                && integer(row.get("heir_gameplay_actions"), "heir_gameplay_actions").signum() == 0, "historical one-life episode cannot grant heir actions");
        Obj a = object(row.get("achievements"), "achievements");
        exact(a, Set.of("palermo_holy_war_won", "armies_disbanded", "danish_betrothal_accepted", "partition_risk_visible"));
        return new Episode(text(row.get("run_id"), "run_id"), Instant.parse(text(row.get("finished_at"), "finished_at")), text(row.get("terminal_reason"), "terminal_reason"),
                bool(row.get("technical_settlement_handoff"), "technical_settlement_handoff"), Objects.requireNonNull(row.get("score")),
                new Achievements(bool(a.get("palermo_holy_war_won"), "palermo_holy_war_won"), bool(a.get("armies_disbanded"), "armies_disbanded"),
                        bool(a.get("danish_betrothal_accepted"), "danish_betrothal_accepted"), bool(a.get("partition_risk_visible"), "partition_risk_visible")),
                row.get("latest_checkpoint") == Nil.INSTANCE ? Optional.empty() : Optional.of(parseCheckpoint(object(row.get("latest_checkpoint"), "latest_checkpoint"))),
                array(row.get("successful_steps"), "successful_steps").stream().map(value -> text(value, "successful_step")).toList());
    }
    private static List<Directive> directives(Value raw) {
        return array(raw, "priorities").stream().map(value -> {
            Obj row = object(value, "priority row");
            StrictJson.require(Set.of("priority", "action", "reason").containsAll(row.members().keySet()), "unexpected cross-run directive field");
            return new Directive(row.get("priority") == null ? Optional.empty() : Optional.of(integer(row.get("priority"), "priority")),
                    optionalText(row, "action"), optionalText(row, "reason"));
        }).toList();
    }
    private static Obj directiveJson(Directive row) {
        Obj result = obj();
        if (row.priority().isPresent()) result = result.with("priority", new IntegerValue(row.priority().orElseThrow()));
        if (row.action().isPresent()) result = result.with("action", new Text(row.action().orElseThrow()));
        if (row.reason().isPresent()) result = result.with("reason", new Text(row.reason().orElseThrow()));
        return result;
    }
    private static Directive directive(int rank, String action, String reason) {
        return new Directive(Optional.of(BigInteger.valueOf(rank)), Optional.of(action), Optional.of(reason));
    }
    private static List<Obj> expand(List<Obj> commands) {
        List<Obj> result = new ArrayList<>();
        for (Obj row : commands) {
            String command = string(row.get("command"));
            Optional<Obj> execution = child(row, "result");
            if ((command.equals("auto-run") || command.matches("auto-run [0-9]+"))
                    && execution.isPresent() && execution.orElseThrow().get("turns") instanceof Arr turns) {
                for (Value turn : turns.items()) if (turn instanceof Obj item) result.add(item);
            } else result.add(row);
        }
        return List.copyOf(result);
    }
    private static void validateCommand(Obj row) {
        Objects.requireNonNull(row);
        if (row.get("command") != null) text(row.get("command"), "command");
        if (row.get("ok") != null) bool(row.get("ok"), "ok");
        if (row.get("result") != null && row.get("result") != Nil.INSTANCE) object(row.get("result"), "result");
    }
    private static String command(Obj row) {
        String outer = string(row.get("command"));
        return outer.equals("auto-turn") ? child(row, "result").flatMap(value -> child(value, "auto_turn"))
                .map(value -> string(value.get("selected_step"))).orElse("") : outer;
    }
    private static Optional<Obj> last(List<Obj> rows, Predicate<String> matching) {
        for (int i = rows.size() - 1; i >= 0; --i) {
            Obj row = rows.get(i);
            if (yes(row.get("ok")) && matching.test(command(row)) && row.get("result") instanceof Obj result) return Optional.of(result);
        }
        return Optional.empty();
    }
    private static boolean acceptedMarriage(List<Obj> rows) {
        for (int i = rows.size() - 1; i >= 0; --i) {
            Obj row = rows.get(i); String step = command(row);
            if (!yes(row.get("ok")) || !(row.get("result") instanceof Obj result)) continue;
            Optional<Obj> outcome = child(result, "marriage_result");
            if (outcome.isEmpty()) continue;
            Obj value = outcome.orElseThrow(); String status = string(value.get("status"));
            if (!Set.of("accepted_betrothal", "accepted_marriage").contains(status)) continue;
            if (step.equals("marriage-confirm-response")) return true;
            if (step.matches("arrange-marriage-[0-9]+-[0-9]+")
                    && string(value.get("source")).equals("native_relationship_snapshot") && value.get("candidate_character_id") instanceof IntegerValue) return true;
        }
        return false;
    }
    private static Checkpoint checkpoint(Obj row) {
        return new Checkpoint(nullableText(row, "name"), row.get("size") == null || row.get("size") == Nil.INSTANCE
                ? Optional.empty() : Optional.of(integer(row.get("size"), "size")), nullableText(row, "sha256"));
    }
    private static Checkpoint parseCheckpoint(Obj row) {
        exact(row, Set.of("name", "size", "sha256")); return checkpoint(row);
    }
    private static Optional<Obj> child(Obj row, String key) { return row.get(key) instanceof Obj value ? Optional.of(value) : Optional.empty(); }
    private static boolean status(Obj row, String key, String expected) { return child(row, key).filter(value -> expected.equals(string(value.get("status")))).isPresent(); }
    private static String string(Value raw) { return raw instanceof Text value ? value.value() : ""; }
    private static boolean yes(Value raw) { return raw instanceof Bool value && value.value(); }
    private static boolean contains(String value, String... tokens) { for (String token : tokens) if (value.contains(token)) return true; return false; }
    private static Obj obj() { return new Obj(java.util.Map.of()); }
    private static IntegerValue number(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static Value nullableText(Optional<String> value) { return value.<Value>map(Text::new).orElse(Nil.INSTANCE); }
    private static Optional<String> nullableText(Obj row, String field) { return row.get(field) == null || row.get(field) == Nil.INSTANCE ? Optional.empty() : Optional.of(text(row.get(field), field)); }
    private static Optional<String> optionalText(Obj row, String field) { return row.get(field) == null ? Optional.empty() : Optional.of(text(row.get(field), field)); }
    private static void exact(Obj row, Set<String> fields) { StrictJson.require(row.members().keySet().equals(fields), "exact cross-run fields required: " + fields); }
}
