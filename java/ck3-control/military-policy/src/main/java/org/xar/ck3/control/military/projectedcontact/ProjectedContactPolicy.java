package org.xar.ck3.control.military.projectedcontact;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.xar.ck3.control.contracts.StrictJson;

/** Selects native hypothetical contact inputs; it never predicts actual arrival. */
public final class ProjectedContactPolicy {
    public static final String STEP_PREFIX = "query-projected-contact-scope-v1-";
    public static final String SCOPE_KIND = "hypothetical_arrival_against_current_target_state";
    private static final Pattern STEP = Pattern.compile(
            STEP_PREFIX + "(0|[1-9][0-9]*)-to-([1-9][0-9]*)-from-([1-9][0-9]*)");

    private ProjectedContactPolicy() { }

    public enum Transition { NONE, JOIN_EXISTING, CREATE_NEW }
    public enum Side { NONE, ATTACKER, DEFENDER }

    public record QueryKey(int subjectArmyId, int targetProvinceId, int incomingEntryProvinceId) {
        public QueryKey {
            publicUnit(subjectArmyId); positive(targetProvinceId); positive(incomingEntryProvinceId);
            require(targetProvinceId != incomingEntryProvinceId, "incoming entry must differ from target");
        }
        public String step() {
            return STEP_PREFIX + subjectArmyId + "-to-" + targetProvinceId + "-from-" + incomingEntryProvinceId;
        }
    }

    public record Request(QueryKey key, int subjectCurrentProvinceId, Integer subjectOwnerCharacterId) {
        public Request {
            Objects.requireNonNull(key, "query key"); positive(subjectCurrentProvinceId);
            if (subjectOwnerCharacterId != null) { positive(subjectOwnerCharacterId); }
        }
    }

    public record Capture(String snapshotId, BigInteger revision, BigInteger nativeRevision,
                          BigInteger connectionGeneration, String episodeRunId) {
        public Capture {
            StrictJson.text(snapshotId); StrictJson.text(episodeRunId);
            uint64(revision, false); uint64(nativeRevision, true); uint64(connectionGeneration, true);
        }
    }

    public record Snapshot(Capture capture, int dateRaw) {
        public Snapshot { Objects.requireNonNull(capture, "snapshot capture"); }
    }

    /** Native array order, including selected Combat array index, is significant. */
    public record Scope(BigInteger snapshotRevision, int dateRaw, int subjectArmyId,
                        int subjectNativeCarmyId, int subjectOwnerCharacterId,
                        int subjectCurrentProvinceId, int targetProvinceId, int incomingEntryProvinceId,
                        List<Integer> observedTargetPublicCunitIds, List<Integer> observedTargetCombatIds,
                        Transition transition, Integer selectedCurrentCombatId,
                        Integer selectedCurrentCombatArrayIndex, Side subjectSide,
                        boolean initiatorIsDefenderObservable, Boolean initiatorIsDefender,
                        int incomingAdjacencyKindRaw, List<Integer> attackerArmyIds,
                        List<Integer> defenderArmyIds) {
        public Scope {
            uint64(snapshotRevision, true); publicUnit(subjectArmyId); positive(subjectNativeCarmyId);
            positive(subjectOwnerCharacterId); positive(subjectCurrentProvinceId);
            positive(targetProvinceId); positive(incomingEntryProvinceId);
            require(targetProvinceId != incomingEntryProvinceId, "incoming entry equals target");
            observedTargetPublicCunitIds = ids(observedTargetPublicCunitIds, true);
            observedTargetCombatIds = ids(observedTargetCombatIds, false);
            attackerArmyIds = ids(attackerArmyIds, true); defenderArmyIds = ids(defenderArmyIds, true);
            Objects.requireNonNull(transition, "transition"); Objects.requireNonNull(subjectSide, "side");
            require(attackerArmyIds.stream().noneMatch(defenderArmyIds::contains), "contact sides overlap");
            if (selectedCurrentCombatId != null) { positive(selectedCurrentCombatId); }
            if (selectedCurrentCombatArrayIndex != null) {
                require(selectedCurrentCombatArrayIndex >= 0, "negative selected Combat index");
            }
            require(initiatorIsDefenderObservable ? initiatorIsDefender != null : initiatorIsDefender == null,
                    "initiator role availability disagrees");
            require(incomingAdjacencyKindRaw >= 0 && incomingAdjacencyKindRaw <= 3, "adjacency outside native enum");
            if (transition == Transition.NONE) {
                require(selectedCurrentCombatId == null && selectedCurrentCombatArrayIndex == null
                        && subjectSide == Side.NONE && !initiatorIsDefenderObservable
                        && attackerArmyIds.isEmpty() && defenderArmyIds.isEmpty(), "none has participants");
            } else {
                List<Integer> own = subjectSide == Side.ATTACKER ? attackerArmyIds
                        : subjectSide == Side.DEFENDER ? defenderArmyIds : List.of();
                List<Integer> other = subjectSide == Side.ATTACKER ? defenderArmyIds : attackerArmyIds;
                require(!own.isEmpty() && !other.isEmpty() && own.contains(subjectArmyId)
                        && !other.contains(subjectArmyId), "subject side membership disagrees");
                if (transition == Transition.JOIN_EXISTING) {
                    require(selectedCurrentCombatId != null && selectedCurrentCombatArrayIndex != null
                            && selectedCurrentCombatArrayIndex < observedTargetCombatIds.size()
                            && observedTargetCombatIds.get(selectedCurrentCombatArrayIndex).equals(selectedCurrentCombatId)
                            && !initiatorIsDefenderObservable && own.getLast() == subjectArmyId,
                            "join requires selected current Combat and native append order");
                } else {
                    require(selectedCurrentCombatId == null && selectedCurrentCombatArrayIndex == null
                            && initiatorIsDefenderObservable && own.equals(List.of(subjectArmyId))
                            && initiatorIsDefender == (subjectSide == Side.DEFENDER)
                            && observedTargetPublicCunitIds.containsAll(other), "new contact role or target participants disagree");
                }
            }
        }
        public boolean matches(Snapshot snapshot, Request request) {
            return subjectArmyId == request.key().subjectArmyId()
                    && targetProvinceId == request.key().targetProvinceId()
                    && incomingEntryProvinceId == request.key().incomingEntryProvinceId()
                    && dateRaw == snapshot.dateRaw() && snapshotRevision.equals(snapshot.capture().nativeRevision())
                    && subjectCurrentProvinceId == request.subjectCurrentProvinceId()
                    && (request.subjectOwnerCharacterId() == null
                        || subjectOwnerCharacterId == request.subjectOwnerCharacterId());
        }
    }

    public sealed interface QueryRow permits UnusableRow, CapturedRow { }
    public record UnusableRow() implements QueryRow { }
    public record CapturedRow(QueryKey key, Capture capture, Scope scope) implements QueryRow {
        public CapturedRow {
            Objects.requireNonNull(key, "query key"); Objects.requireNonNull(capture, "capture");
            Objects.requireNonNull(scope, "scope");
        }
    }

    public sealed interface Selection permits QueryRequired, Available {
        QueryKey key();
    }
    public record QueryRequired(QueryKey key) implements Selection {
        public QueryRequired { Objects.requireNonNull(key, "query key"); }
    }
    public record Available(QueryKey key, Scope projection) implements Selection {
        public Available { Objects.requireNonNull(key, "query key"); Objects.requireNonNull(projection, "scope"); }
        public boolean incomingAttackerGeometryReady() {
            return projection.transition() == Transition.CREATE_NEW && projection.subjectSide() == Side.ATTACKER;
        }
        public boolean actualArrivalObserved() { return false; }
        public boolean futureContactAuthorized() { return false; }
    }

    public static Selection select(Snapshot snapshot, List<QueryRow> queryRows, Request request) {
        Objects.requireNonNull(snapshot, "snapshot"); Objects.requireNonNull(request, "request");
        List<QueryRow> rows = List.copyOf(queryRows);
        for (int index = rows.size() - 1; index >= 0; index--) {
            if (rows.get(index) instanceof CapturedRow row && row.key().equals(request.key())
                    && row.capture().equals(snapshot.capture()) && row.scope().matches(snapshot, request)) {
                return new Available(request.key(), row.scope());
            }
        }
        return new QueryRequired(request.key());
    }

    public static Optional<QueryKey> parseStep(String text) {
        if (text == null) { return Optional.empty(); }
        Matcher matcher = STEP.matcher(text);
        if (!matcher.matches()) { return Optional.empty(); }
        try {
            return Optional.of(new QueryKey(Integer.parseInt(matcher.group(1)),
                    Integer.parseInt(matcher.group(2)), Integer.parseInt(matcher.group(3))));
        } catch (IllegalArgumentException error) { return Optional.empty(); }
    }

    private static List<Integer> ids(List<Integer> values, boolean publicUnits) {
        List<Integer> result = List.copyOf(values);
        for (Integer value : result) { if (publicUnits) { publicUnit(value); } else { positive(value); } }
        require(new HashSet<>(result).size() == result.size(), "duplicate identity in native array");
        return result;
    }
    private static void uint64(BigInteger value, boolean positive) {
        require(value != null && value.compareTo(positive ? BigInteger.ONE : BigInteger.ZERO) >= 0
                && value.compareTo(StrictJson.UINT64_MAX) <= 0, "exact uint64 outside range");
    }
    private static void publicUnit(int value) { require(value >= 0, "public CUnit must be nonnegative int32"); }
    private static void positive(int value) { require(value > 0, "positive int32 identity required"); }
    private static void require(boolean condition, String message) { StrictJson.require(condition, message); }
}
