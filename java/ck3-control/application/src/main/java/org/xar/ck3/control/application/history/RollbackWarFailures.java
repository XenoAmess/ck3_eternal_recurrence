package org.xar.ck3.control.application.history;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.regex.Pattern;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original discarded-branch route advisory. No game mutation, history rewrite or retry permission. */
public final class RollbackWarFailures {
    private RollbackWarFailures() { }
    public static final int MAX_FAILURES = 2;
    private static final Pattern MOVE = Pattern.compile("move-army-(0|[1-9][0-9]*)-to-([1-9][0-9]*)");
    private static final Pattern PREVIEW = Pattern.compile("preview-move-army-(0|[1-9][0-9]*)-to-([1-9][0-9]*)");
    // Original historical parser accepts positive ASCII decimals, including leading zeroes; zero is never an option.
    // This recognizes DATA already recorded by the original consumer, not a new action or replay permission.
    private static final Pattern EVENT_OPTION = Pattern.compile("select-event-option-0*[1-9][0-9]*");
    public record Scope(String episodeRunId, String checkpointSha256, int warId, int armyId, int restoredOriginProvinceId) {
        public Scope {
            require(episodeRunId != null && !episodeRunId.isEmpty(), "episode required");
            require(checkpointSha256 != null && checkpointSha256.matches("[0-9a-f]{64}"), "canonical checkpoint SHA required");
            require(warId > 0 && armyId >= 0 && restoredOriginProvinceId > 0, "full War/public Unit/Province required");
        }
    }
    public record Route(int targetProvinceId, int originProvinceId, List<Integer> provinceIds) {
        public Route {
            provinceIds = List.copyOf(provinceIds);
            require(targetProvinceId > 0 && originProvinceId > 0 && !provinceIds.isEmpty(), "nonempty native route required");
            provinceIds.forEach(id -> require(id > 0, "positive route Province required"));
        }
    }
    /** Factory-only to prevent a caller's typed scope from disagreeing with persisted evidence. */
    public static final class Failure {
        private final Scope scope;
        private final Route entry;
        private final Optional<Route> terminal;
        private final Obj document;
        private Failure(Scope scope, Route entry, Optional<Route> terminal, Obj document) {
            this.scope = scope; this.entry = entry; this.terminal = terminal; this.document = document;
        }
        public Scope scope() { return scope; }
        public Route entry() { return entry; }
        public Optional<Route> terminal() { return terminal; }
        @Override public boolean equals(Object other) { return other instanceof Failure f && document.equals(f.document); }
        @Override public int hashCode() { return document.hashCode(); }
    }
    private enum DocumentMode { TYPED_RUNTIME, LEGACY_RESUME_DATA }
    private record Move(int armyId, int targetId) { }
    private record Submitted(Move move, Obj preview) { }
    private record RouteKey(int targetId, List<Integer> route) { }

    /** Strict JSON token validation; legacy optional fields preserve missing versus explicit null. */
    public static Optional<Failure> decode(Value value) {
        if (!(value instanceof Obj row) || !text(row.get("status"), "rolled_back_active_route")) return Optional.empty();
        if (!FIELDS.containsAll(row.members().keySet())) return Optional.empty();
        Optional<Integer> war = id(row.get("war_id"), false), army = id(row.get("army_id"), true),
                origin = id(row.get("restored_origin_province_id"), false), target = id(row.get("target_province_id"), false),
                routeOrigin = id(row.get("route_origin_province_id"), false);
        Optional<List<Integer>> route = route(row.get("route_province_ids"));
        if (war.isEmpty() || army.isEmpty() || origin.isEmpty() || target.isEmpty() || routeOrigin.isEmpty()
                || route.isEmpty() || !origin.equals(routeOrigin)
                || !(row.get("episode_run_id") instanceof Text episode) || episode.value().isEmpty()
                || !(row.get("checkpoint_sha256") instanceof Text sha) || !sha.value().matches("[0-9a-f]{64}")) return Optional.empty();
        if (row.members().containsKey("source") && !text(row.get("source"), "checkpoint_discarded_branch")) return Optional.empty();
        for (String key : DATES) if (row.members().containsKey(key) && row.get(key) != Nil.INSTANCE
                && !(row.get(key) instanceof IntegerValue)) return Optional.empty();
        Optional<Route> terminal = Optional.empty();
        if (TERMINAL.stream().anyMatch(row.members()::containsKey)) {
            Optional<Integer> terminalTarget = id(row.get(TERMINAL.get(0)), false), terminalOrigin = id(row.get(TERMINAL.get(1)), false);
            Optional<List<Integer>> terminalRoute = route(row.get(TERMINAL.get(2)));
            if (terminalTarget.isEmpty() || terminalOrigin.isEmpty() || terminalRoute.isEmpty()) return Optional.empty();
            terminal = Optional.of(new Route(terminalTarget.orElseThrow(), terminalOrigin.orElseThrow(), terminalRoute.orElseThrow()));
        }
        Scope scope = new Scope(episode.value(), sha.value(), war.orElseThrow(), army.orElseThrow(), origin.orElseThrow());
        return Optional.of(new Failure(scope, new Route(target.orElseThrow(), routeOrigin.orElseThrow(), route.orElseThrow()), terminal, row));
    }
    public static Obj encode(Failure failure) { return Objects.requireNonNull(failure).document; }

    @SafeVarargs public static List<Failure> bounded(List<Failure>... groups) {
        List<Failure> result = new ArrayList<>(); Scope scope = null; Set<RouteKey> seen = new LinkedHashSet<>();
        for (List<Failure> group : groups) for (Failure failure : List.copyOf(group)) {
            if (scope == null) scope = failure.scope();
            else if (!scope.equals(failure.scope())) continue;
            if (seen.add(new RouteKey(failure.entry().targetProvinceId(), failure.entry().provinceIds()))) result.add(failure);
            if (result.size() == MAX_FAILURES) return List.copyOf(result);
        }
        return List.copyOf(result);
    }
    public static Optional<Failure> deriveCurrent(List<Obj> history, Obj checkpoint, Obj restoredSnapshot,
            String episodeRunId, Optional<Obj> abandonedSnapshot, int completedRestoreEpochLimit) {
        var index = DriverHistoryProjection.checkpointHistoryIndex(checkpoint, history);
        if (index.isEmpty()) return Optional.empty();
        List<Obj> rows = List.copyOf(history); int start = index.getAsInt();
        for (int pos = start; pos < rows.size(); pos++) if (successfulRestore(rows.get(pos))) start = pos + 1;
        Optional<Failure> current = deriveEpoch(rows.subList(start, rows.size()), checkpoint, restoredSnapshot, episodeRunId, abandonedSnapshot);
        if (current.isPresent() || completedRestoreEpochLimit <= 0) return current;
        return deriveCompleted(rows, checkpoint, restoredSnapshot, episodeRunId, completedRestoreEpochLimit).stream().findFirst();
    }
    /** Original legacy DATA current epoch, with the same bounded completed-epoch fallback engine. */
    public static Optional<Obj> deriveCurrentLegacyDriverFailure(List<Obj> history,Obj checkpoint,Obj restoredSnapshot,
            String episodeRunId,Optional<Obj> abandonedSnapshot,int completedRestoreEpochLimit) {
        var index=DriverHistoryProjection.checkpointHistoryIndex(checkpoint,history);
        if(index.isEmpty())return Optional.empty();
        List<Obj> rows=List.copyOf(history);int start=index.getAsInt();
        for(int pos=start;pos<rows.size();pos++)if(successfulRestore(rows.get(pos)))start=pos+1;
        Optional<Obj> current=deriveEpochDocument(rows.subList(start,rows.size()),checkpoint,restoredSnapshot,episodeRunId,
                abandonedSnapshot,DocumentMode.LEGACY_RESUME_DATA).flatMap(RollbackWarFailures::normalizeLegacyDriverFailure);
        if(current.isPresent()||completedRestoreEpochLimit<=0)return current;
        return deriveCompletedLegacyDriverFailures(rows,checkpoint,restoredSnapshot,episodeRunId,completedRestoreEpochLimit).stream().findFirst();
    }
    public static List<Failure> deriveCompleted(List<Obj> history, Obj checkpoint, Obj restoredSnapshot,
            String episodeRunId, int completedRestoreEpochLimit) {
        List<Failure> failures=new ArrayList<>();
        for(Obj document:completedEpochDocuments(history,checkpoint,restoredSnapshot,episodeRunId,completedRestoreEpochLimit,DocumentMode.TYPED_RUNTIME))decode(document).ifPresent(failures::add);
        return bounded(failures);
    }
    /** Legacy resume DATA has its original wide advisory validation; it grants no typed retry permission. */
    public static List<Obj> deriveCompletedLegacyDriverFailures(List<Obj> history,Obj checkpoint,Obj restoredSnapshot,
            String episodeRunId,int completedRestoreEpochLimit) {
        List<Obj> failures=new ArrayList<>();
        for(Obj document:completedEpochDocuments(history,checkpoint,restoredSnapshot,episodeRunId,completedRestoreEpochLimit,DocumentMode.LEGACY_RESUME_DATA))normalizeLegacyDriverFailure(document).ifPresent(failures::add);
        return boundedLegacyDriverFailures(failures);
    }
    private static List<Obj> completedEpochDocuments(List<Obj> history, Obj checkpoint, Obj restoredSnapshot,
            String episodeRunId, int completedRestoreEpochLimit,DocumentMode mode) {
        var index = DriverHistoryProjection.checkpointHistoryIndex(checkpoint, history);
        if (index.isEmpty() || completedRestoreEpochLimit <= 0) return List.of();
        List<Obj> rows = List.copyOf(history); List<Integer> positions = new ArrayList<>();
        for (int pos = index.getAsInt(); pos < rows.size(); pos++) if (successfulRestore(rows.get(pos))) positions.add(pos);
        List<Obj> failures = new ArrayList<>();
        for (int offset = positions.size() - 1; offset >= Math.max(0, positions.size() - completedRestoreEpochLimit); offset--) {
            int start = offset > 0 ? positions.get(offset - 1) + 1 : index.getAsInt();
            deriveEpochDocument(rows.subList(start, positions.get(offset)), checkpoint, restoredSnapshot, episodeRunId, Optional.empty(),mode).ifPresent(failures::add);
        }
        return List.copyOf(failures);
    }
    /** Complete original epoch producer, also exposed for an original-producer differential test. */
    public static Optional<Failure> deriveEpoch(List<Obj> history,Obj checkpoint,Obj restoredSnapshot,
            String episodeRunId,Optional<Obj> abandonedSnapshot) {
        return deriveEpochDocument(history,checkpoint,restoredSnapshot,episodeRunId,abandonedSnapshot,DocumentMode.TYPED_RUNTIME).flatMap(RollbackWarFailures::decode);
    }
    private static Optional<Obj> deriveEpochDocument(List<Obj> history, Obj checkpoint, Obj restoredSnapshot,
            String episodeRunId, Optional<Obj> abandonedSnapshot,DocumentMode mode) {
        Objects.requireNonNull(abandonedSnapshot); List<Obj> rows = List.copyOf(history);
        Map<Move, Obj> previews = new LinkedHashMap<>(); List<Submitted> submitted = new ArrayList<>();
        Map<Integer, Obj> latestArmies = new LinkedHashMap<>(); Submitted failed = null;
        for (Obj row : rows) {
            var effective = DriverSurvivingHistory.effective(row);
            if (!yes(row.get("ok")) || effective.result().isEmpty()) continue;
            Obj result = effective.result().orElseThrow(); String step = effective.command().orElse("");
            Optional<Move> previewStep = parse(PREVIEW, step);
            if (previewStep.isPresent() && result.get("route_preview") instanceof Obj preview
                    && text(preview.get("status"), "available") && identity(preview, previewStep.orElseThrow())
                    && originForDocument(preview.get("origin_province_id"),mode).isPresent() && routeForDocument(preview.get("route_province_ids"),mode))
                previews.put(previewStep.orElseThrow(), preview);
            Optional<Move> move = parse(MOVE, step);
            if (move.isPresent() && result.get("war_action") instanceof Obj action) {
                if (text(action.get("status"), "move_submitted") || text(action.get("status"), "moving")) {
                    Obj preview = previews.get(move.orElseThrow());
                    failed = preview != null && identity(action, move.orElseThrow())
                            && matchingSubmissionDate(action.get("submitted_date_raw"),preview.get("previewed_date_raw"),mode)
                            ? new Submitted(move.orElseThrow(), preview) : null;
                    if (failed != null) submitted.add(failed);
                } else if (text(action.get("status"), "arrived")) failed = null;
            }
            for (Obj army : observations(result)) id(army.get("army_id"), true).ifPresent(value -> latestArmies.put(value, army));
        }
        if (failed == null || endedAtUnresolvedPlayerEvent(rows,mode)) return Optional.empty();
        int armyId = failed.move().armyId(), terminalTarget = failed.move().targetId();
        Obj active = abandonedSnapshot.isPresent() ? army(abandonedSnapshot.orElseThrow(), armyId).orElse(null) : latestArmies.get(armyId);
        if (active == null || !id(active.get("move_target_province_id"), false).equals(Optional.of(terminalTarget))
                || !routeForDocument(active.get("route_province_ids"),mode)) return Optional.empty();
        Optional<Obj> restoredArmy = army(restoredSnapshot, armyId);
        Optional<BigInteger> origin = restoredArmy.flatMap(value -> originForDocument(value.get("current_province_id"),mode));
        Optional<BigInteger> war = mode==DocumentMode.TYPED_RUNTIME?warForArmy(restoredSnapshot,armyId).map(BigInteger::valueOf):warForArmyWide(restoredSnapshot,armyId);
        if (origin.isEmpty() || war.isEmpty() || episodeRunId == null || episodeRunId.isEmpty()
                || !(checkpoint.get("sha256") instanceof Text sha) || !sha.value().matches("[0-9a-f]{64}")) return Optional.empty();
        Submitted entry = submitted.stream().filter(value -> value.move().armyId() == armyId
                && originForDocument(value.preview().get("origin_province_id"),mode).equals(origin)).findFirst().orElse(null);
        if (entry == null) return Optional.empty();
        var fields = new LinkedHashMap<String, Value>();
        fields.put("status", new Text("rolled_back_active_route")); fields.put("source", new Text("checkpoint_discarded_branch"));
        fields.put("episode_run_id", new Text(episodeRunId)); fields.put("checkpoint_sha256", sha);
        fields.put("checkpoint_date_raw", dateForDocument(checkpoint.get("date_raw"),mode)); fields.put("war_id", number(war.orElseThrow()));
        fields.put("army_id", number(armyId)); fields.put("restored_origin_province_id", number(origin.orElseThrow()));
        fields.put("target_province_id", number(entry.move().targetId())); fields.put("route_origin_province_id", number(origin.orElseThrow()));
        fields.put("route_province_ids", entry.preview().get("route_province_ids"));
        fields.put("previewed_date_raw", dateForDocument(entry.preview().get("previewed_date_raw"),mode));
        fields.put(TERMINAL.get(0), number(terminalTarget)); fields.put(TERMINAL.get(1), failed.preview().get("origin_province_id"));
        fields.put(TERMINAL.get(2), failed.preview().get("route_province_ids"));
        fields.put("abandoned_date_raw", abandonedSnapshot.<Value>map(value -> dateForDocument(value.get("date_raw"),mode)).orElse(Nil.INSTANCE));
        fields.put("restored_date_raw", dateForDocument(restoredSnapshot.get("date_raw"),mode));
        return Optional.of(new Obj(fields));
    }
    public static boolean endedAtUnresolvedPlayerEvent(List<Obj> rows) {return endedAtUnresolvedPlayerEvent(rows,DocumentMode.TYPED_RUNTIME);}
    private static boolean endedAtUnresolvedPlayerEvent(List<Obj> rows,DocumentMode mode) {
        String lastStep = null; Obj lastResult = null; boolean selected = false;
        for (Obj row : rows) {
            var effective = DriverSurvivingHistory.effective(row);
            if (!yes(row.get("ok")) || effective.result().isEmpty()) continue;
            lastStep = effective.command().orElse(null); lastResult = effective.result().orElseThrow();
            if (lastStep != null && EVENT_OPTION.matcher(lastStep).matches()) selected = true;
        }
        if (selected || !"query-current-event-window-context-v1".equals(lastStep) || lastResult == null
                || !yes(lastResult.get("accepted")) || !text(lastResult.get("status"), "available")
                || !(lastResult.get("current_event_window_context") instanceof Obj context)) return false;
        Optional<BigInteger> instance = originForDocument(lastResult.get("current_event_instance_id"),mode);
        return instance.isPresent() && text(context.get("status"), "available") && number(1).equals(context.get("window_match_count"))
                && originForDocument(context.get("current_event_instance_id"),mode).equals(instance)
                && context.get("event_definition_key") instanceof Text key && !key.value().isEmpty();
    }
    private static boolean successfulRestore(Obj row) {
        return yes(row.get("ok")) && DriverSurvivingHistory.effective(row).command().equals(Optional.of(DriverSurvivingHistory.RESTORE));
    }
    private static List<Obj> observations(Obj result) {
        List<Obj> values = new ArrayList<>(objects(result.get("player_armies")));
        if (result.get("war_progress_after") instanceof Obj progress)
            for (Obj war : objects(progress.get("wars"))) values.addAll(objects(war.get("player_armies")));
        return List.copyOf(values);
    }
    private static Optional<Obj> army(Obj snapshot, int armyId) {
        return objects(snapshot.get("player_armies")).stream().filter(value -> id(value.get("army_id"), true).equals(Optional.of(armyId))).findFirst();
    }
    private static Optional<Integer> warForArmy(Obj snapshot, int armyId) {
        for (Obj war : objects(snapshot.get("active_wars"))) if (objects(war.get("allied_armies")).stream()
                .anyMatch(value -> yes(value.get("controllable")) && id(value.get("army_id"), true).equals(Optional.of(armyId))))
            return id(war.get("war_id"), false);
        return Optional.empty();
    }
    private static Optional<BigInteger> warForArmyWide(Obj snapshot,int armyId) {
        for(Obj war:objects(snapshot.get("active_wars")))if(objects(war.get("allied_armies")).stream()
                .anyMatch(value->yes(value.get("controllable"))&&id(value.get("army_id"),true).equals(Optional.of(armyId))))
            return positiveWide(war.get("war_id"));
        return Optional.empty();
    }
    private static Optional<BigInteger> originForDocument(Value value,DocumentMode mode){return mode==DocumentMode.TYPED_RUNTIME?id(value,false).map(BigInteger::valueOf):positiveWide(value);}
    private static boolean routeForDocument(Value value,DocumentMode mode){return mode==DocumentMode.TYPED_RUNTIME?route(value).isPresent():routeWide(value);}
    /** Legacy history DATA permits absent/null dates; live derivation still requires an integer date.
     * Compare in the JSON type domain, so booleans/decimals cannot impersonate integer tokens. */
    private static boolean matchingSubmissionDate(Value submitted,Value previewed,DocumentMode mode) {
        return (mode==DocumentMode.LEGACY_RESUME_DATA||submitted instanceof IntegerValue)
                &&originalValue(submitted).equals(originalValue(previewed));
    }
    private static Value dateForDocument(Value value,DocumentMode mode){return mode==DocumentMode.TYPED_RUNTIME?date(value):originalValue(value);}
    private static Value originalValue(Value value){return value==null?Nil.INSTANCE:value;}
    private static Optional<BigInteger> positiveWide(Value value){return value instanceof IntegerValue integer&&integer.value().signum()>0?Optional.of(integer.value()):Optional.empty();}
    private static boolean routeWide(Value value){return value instanceof Arr array&&!array.items().isEmpty()&&array.items().stream().allMatch(item->positiveWide(item).isPresent());}
    private static IntegerValue number(BigInteger value){return new IntegerValue(value);}

    /** Exact old persisted advisory normalization, retaining every unknown extension and JSON type. */
    public static Optional<Obj> normalizeLegacyDriverFailure(Value value) {
        if(!(value instanceof Obj row)||!text(row.get("status"),"rolled_back_active_route"))return Optional.empty();
        for(String key:List.of("war_id","army_id","restored_origin_province_id","target_province_id","route_origin_province_id"))
            if(positiveWide(row.get(key)).isEmpty())return Optional.empty();
        if(!row.get("route_origin_province_id").equals(row.get("restored_origin_province_id"))||!routeWide(row.get("route_province_ids")))return Optional.empty();
        if(TERMINAL.stream().anyMatch(row.members()::containsKey)&&
                (positiveWide(row.get(TERMINAL.get(0))).isEmpty()||positiveWide(row.get(TERMINAL.get(1))).isEmpty()||!routeWide(row.get(TERMINAL.get(2)))))return Optional.empty();
        if(!(row.get("episode_run_id") instanceof Text run)||run.value().isEmpty()
                ||!(row.get("checkpoint_sha256") instanceof Text sha)||!sha.value().matches("[0-9a-f]{64}"))return Optional.empty();
        return Optional.of(row);
    }
    private record LegacyRoute(Value target,Value route) { }
    @SafeVarargs public static List<Obj> boundedLegacyDriverFailures(List<Obj>... groups) {
        List<Obj> result=new ArrayList<>();List<Value> scope=null;Set<LegacyRoute> seen=new LinkedHashSet<>();
        for(List<Obj> group:groups)for(Obj input:List.copyOf(group)) {
            Optional<Obj> normalized=normalizeLegacyDriverFailure(input);if(normalized.isEmpty())continue;Obj row=normalized.orElseThrow();
            List<Value> actual=List.of(row.get("episode_run_id"),row.get("checkpoint_sha256"),row.get("war_id"),row.get("army_id"),row.get("restored_origin_province_id"));
            if(scope==null)scope=actual;else if(!scope.equals(actual))continue;
            if(seen.add(new LegacyRoute(row.get("target_province_id"),row.get("route_province_ids"))))result.add(row);
            if(result.size()==MAX_FAILURES)return List.copyOf(result);
        }return List.copyOf(result);
    }
    private static boolean identity(Obj row, Move move) {
        return id(row.get("army_id"), true).equals(Optional.of(move.armyId()))
                && id(row.get("target_province_id"), false).equals(Optional.of(move.targetId()));
    }
    private static Optional<Move> parse(Pattern pattern, String value) {
        var matcher = pattern.matcher(value); if (!matcher.matches()) return Optional.empty();
        try { return Optional.of(new Move(Integer.parseInt(matcher.group(1)), Integer.parseInt(matcher.group(2)))); }
        catch (NumberFormatException invalid) { return Optional.empty(); }
    }
    private static Optional<Integer> id(Value value, boolean zeroAllowed) {
        if (!(value instanceof IntegerValue integer) || integer.value().signum() < (zeroAllowed ? 0 : 1)
                || integer.value().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) > 0) return Optional.empty();
        return Optional.of(integer.value().intValueExact());
    }
    private static Optional<List<Integer>> route(Value value) {
        if (!(value instanceof Arr array) || array.items().isEmpty()) return Optional.empty();
        List<Integer> ids = new ArrayList<>();
        for (Value item : array.items()) { var id = id(item, false); if (id.isEmpty()) return Optional.empty(); ids.add(id.orElseThrow()); }
        return Optional.of(List.copyOf(ids));
    }
    private static List<Obj> objects(Value value) {
        if (!(value instanceof Arr array)) return List.of();
        return array.items().stream().filter(Obj.class::isInstance).map(Obj.class::cast).toList();
    }
    private static Value date(Value value) {
        require(value == null || value == Nil.INSTANCE || value instanceof IntegerValue, "native date must retain an integer token or null");
        return value == null ? Nil.INSTANCE : value;
    }
    private static IntegerValue number(int value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static boolean yes(Value value) { return value instanceof Bool flag && flag.value(); }
    private static boolean text(Value value, String expected) { return value instanceof Text token && token.value().equals(expected); }
    private static void require(boolean condition, String message) { OpportunityJson.require(condition, message); }
    private static final List<String> TERMINAL = List.of("terminal_failure_target_province_id", "terminal_failure_route_origin_province_id", "terminal_failure_route_province_ids");
    private static final Set<String> DATES = Set.of("checkpoint_date_raw", "previewed_date_raw", "abandoned_date_raw", "restored_date_raw");
    private static final Set<String> FIELDS = Set.of("status", "source", "episode_run_id", "checkpoint_sha256", "checkpoint_date_raw", "war_id", "army_id",
            "restored_origin_province_id", "target_province_id", "route_origin_province_id", "route_province_ids", "previewed_date_raw",
            "terminal_failure_target_province_id", "terminal_failure_route_origin_province_id", "terminal_failure_route_province_ids", "abandoned_date_raw", "restored_date_raw");
}
