package org.xar.ck3.control.application.routecontact;

import static org.xar.ck3.control.application.routecontact.RouteContactModel.*;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy;

/** NativeDriver 31527/31546/34305/34477. A closed endpoint marker is deliberately not actual contact. */
public final class RouteContactPostconditions {
    private RouteContactPostconditions() { }
    public static boolean newer(Frame previous, Frame next) {
        return next.revision().compareTo(previous.revision()) > 0 && next.nativeRevision().compareTo(previous.nativeRevision()) > 0;
    }
    public static boolean samePausedRefreshOwner(Frame previous, Frame next) {
        return newer(previous, next) && next.owner().equals(previous.owner()) && next.mapReady() && next.paused()
                && next.dateRaw() == previous.dateRaw() && next.speed() == previous.speed() && next.activeEvent().equals(previous.activeEvent());
    }
    public static Optional<Transition> observed(Frame starting, Frame ending, Proof proof) {
        if (!ending.paused() || ending.dateRaw() < starting.dateRaw() || (long)ending.dateRaw() > (long)starting.dateRaw() + 24) return Optional.empty();
        TransitionKind kind = null; List<Integer> changed = List.of();
        if (ending.oneLifeTerminal() || !ending.playedCharacterAlive()) kind = TransitionKind.EPISODE_TERMINAL;
        else if (!starting.activeWarIds().equals(ending.activeWarIds())) kind = TransitionKind.ACTIVE_WAR_SET_CHANGED;
        else {
            Optional<Army> subject = ending.own(proof.subjectId());
            if (subject.isEmpty()) kind = TransitionKind.SUBJECT_ARMY_REMOVED;
            else if (subject.orElseThrow().inCombat()) kind = TransitionKind.ACTIVE_COMBAT_OBSERVED;
            else if (subject.orElseThrow().retreating()) kind = TransitionKind.RETREAT_OBSERVED;
            else if (!proof.strictFollowup()) {
                int province = proof.query().subjectRoute().currentProvinceId();
                List<Integer> conflictIds = conflictIds(proof);
                changed = conflictIds.stream().filter(id -> starting.own(proof.subjectId()).filter(army -> army.currentProvinceId() == province).isPresent()
                        && subject.orElseThrow().currentProvinceId() == province
                        && starting.hostile(id).filter(army -> army.currentProvinceId() != province).isPresent()
                        && ending.hostile(id).filter(army -> army.currentProvinceId() == province).isPresent()).toList();
                if (!changed.isEmpty()) kind = TransitionKind.HOSTILE_ENTERED_CONTACT_PROVINCE;
                else {
                    changed = conflictIds.stream().filter(id -> !intentEquals(starting.hostile(id), ending.hostile(id))).toList();
                    if (!changed.isEmpty()) kind = TransitionKind.HOSTILE_INTENT_CHANGED;
                }
            }
        }
        return kind == null ? Optional.empty() : Optional.of(transition(starting, ending, proof, kind, changed));
    }
    public static Optional<Transition> predictedEndpoint(Frame starting, Frame ending, Proof proof) {
        if (proof.strictFollowup() || !starting.owner().equals(ending.owner()) || !starting.mapReady() || !starting.paused()
                || !ending.mapReady() || !ending.paused() || (long)ending.dateRaw() != (long)starting.dateRaw() + 24
                || proof.query().dateRaw() != starting.dateRaw()) return Optional.empty();
        int province = proof.query().subjectRoute().currentProvinceId();
        Optional<Army> before = starting.own(proof.subjectId()); Optional<Army> after = ending.own(proof.subjectId());
        if (before.isEmpty() || after.isEmpty()) return Optional.empty(); Army left = before.orElseThrow(); Army right = after.orElseThrow();
        List<Integer> arrivals = proof.query().subjectRoute().arrivalDateRaws();
        boolean movingCannotClear = !proof.query().subjectRoute().provinceIds().isEmpty() && !arrivals.isEmpty()
                && arrivals.getFirst() > ending.dateRaw() && left.targetProvinceId().equals(Optional.of(proof.targetProvinceId()))
                && right.targetProvinceId().equals(Optional.of(proof.targetProvinceId())) && !left.remainingRoute().isEmpty()
                && right.remainingRoute().equals(left.remainingRoute());
        boolean hold = proof.query().subjectRoute().provinceIds().isEmpty() && arrivals.isEmpty() && proof.targetProvinceId() == province
                && left.targetProvinceId().isEmpty() && right.targetProvinceId().isEmpty()
                && left.remainingRoute().isEmpty() && right.remainingRoute().isEmpty();
        if (!left.controllable() || !right.controllable() || left.currentProvinceId() != province || right.currentProvinceId() != province
                || !(movingCannotClear || hold) || left.inCombat() || right.inCombat() || left.retreating() || right.retreating()
                || proof.query().nativeConflicts().isEmpty() || !proof.query().nativeConflicts().stream().allMatch(value ->
                    value instanceof RouteWindowPolicy.SameProvince same && same.provinceId() == province
                    && same.overlapStartDateRaw() == ending.dateRaw() && same.overlapEndDateRaw() == ending.dateRaw())) return Optional.empty();
        return Optional.of(transition(starting, ending, proof, TransitionKind.PREDICTED_CONTACT_BOUNDARY_REACHED, conflictIds(proof)));
    }
    private static List<Integer> conflictIds(Proof proof) {
        int province = proof.query().subjectRoute().currentProvinceId();
        return proof.query().nativeConflicts().stream().filter(value -> value instanceof RouteWindowPolicy.SameProvince same && same.provinceId() == province)
                .map(RouteWindowPolicy.Conflict::hostileArmyId).distinct().sorted().toList();
    }
    private static Transition transition(Frame before, Frame after, Proof proof, TransitionKind kind, List<Integer> changed) {
        return new Transition(kind, kind == TransitionKind.ACTIVE_COMBAT_OBSERVED, before.owner().episodeRunId(), proof.subjectId(),
                proof.query().subjectRoute().currentProvinceId(), before.dateRaw(), after.dateRaw(), changed);
    }
    private static boolean intentEquals(Optional<Army> before, Optional<Army> after) {
        if (before.isEmpty() || after.isEmpty()) return before.isEmpty() && after.isEmpty();
        Army left = before.orElseThrow(); Army right = after.orElseThrow();
        return left.targetProvinceId().equals(right.targetProvinceId()) && left.remainingRoute().equals(right.remainingRoute())
                && left.state().equals(right.state()) && left.stateCode().equals(right.stateCode())
                && left.inCombat() == right.inCombat() && left.retreating() == right.retreating();
    }
}
