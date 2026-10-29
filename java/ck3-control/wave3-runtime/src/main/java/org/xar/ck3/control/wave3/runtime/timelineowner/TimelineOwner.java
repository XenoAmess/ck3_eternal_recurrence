package org.xar.ck3.control.wave3.runtime.timelineowner;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Facts used by the existing timeline authority; no submission, retry or source-admission capability. */
public final class TimelineOwner {
    private TimelineOwner() { }

    public enum Presence { MISSING, NULL, PRESENT }

    /** Missing, explicit null and an actual typed value remain distinct in every source projection. */
    public record Field<T>(Presence presence, Optional<T> value) {
        public Field {
            Objects.requireNonNull(presence, "presence"); Objects.requireNonNull(value, "value");
            require((presence == Presence.PRESENT) == value.isPresent(), "field presence and typed value differ");
        }
        public static <T> Field<T> missing() { return new Field<>(Presence.MISSING, Optional.empty()); }
        public static <T> Field<T> explicitNull() { return new Field<>(Presence.NULL, Optional.empty()); }
        public static <T> Field<T> of(T value) { return new Field<>(Presence.PRESENT, Optional.of(value)); }
        public boolean present() { return presence == Presence.PRESENT; }
        public T required() { return value.orElseThrow(() -> new IllegalArgumentException("actual field value required")); }
    }

    public record Diagnostics(Field<BigInteger> bridgePid, Field<BigInteger> connectionGeneration) {
        public Diagnostics { Objects.requireNonNull(bridgePid); Objects.requireNonNull(connectionGeneration); }
    }

    public record PlayedCharacter(Field<BigInteger> characterId, Field<Boolean> alive) {
        public PlayedCharacter { Objects.requireNonNull(characterId); Objects.requireNonNull(alive); }
    }

    /** Only the fields read by the actual pure producer closure; unrelated SDK extensions remain outside scope. */
    public record Frame(Field<BigInteger> dateRaw, Field<Boolean> paused, Field<BigInteger> speed,
            Field<Boolean> mapReady, Field<UiIdentity> activeEvent, Field<UiIdentity> pendingInteraction,
            Field<String> terminalReason, Field<BigInteger> episodeCharacterId, Field<String> episodeRunId,
            Field<BigInteger> localPlayerId, Field<PlayedCharacter> playedCharacter, Field<Diagnostics> diagnostics,
            Field<BigInteger> revision, Field<BigInteger> nativeRevision) {
        public Frame {
            List.of(dateRaw, paused, speed, mapReady, activeEvent, pendingInteraction, terminalReason,
                    episodeCharacterId, episodeRunId, localPlayerId, playedCharacter, diagnostics,
                    revision, nativeRevision).forEach(Objects::requireNonNull);
            if (speed.present()) {
                require(speed.required().compareTo(BigInteger.ONE) >= 0 && speed.required().compareTo(BigInteger.valueOf(5)) <= 0,
                        "actual policy speed must be1..5");
            }
            if (episodeRunId.present()) { require(!episodeRunId.required().isEmpty(), "nonempty episode run ID required"); }
        }
    }

    public enum Kind { SAME_FACTS, CHANGED, UNAVAILABLE }
    public enum Reason {
        SAME_TIMELINE, SAME_PAUSED_OWNER, SAME_RUNNING_OWNER, SAME_POPUP_OWNER,
        INCOMPLETE_PROJECTION, DATE_REGRESSED, CONTROL_CHANGED, EVENT_CHANGED, MAP_NOT_READY,
        PAUSE_STATE_CHANGED, TERMINAL_PRESENT, OWNER_CHANGED, POPUP_NOT_VALID, POPUP_CHANGED,
        POPUP_DATE_UNSETTLED, ACTOR_NOT_ALIVE, REVISION_REGRESSED
    }

    public record Assessment(Kind kind, Reason reason) {
        public Assessment {
            Objects.requireNonNull(kind); Objects.requireNonNull(reason);
            boolean same = reason == Reason.SAME_TIMELINE || reason == Reason.SAME_PAUSED_OWNER
                    || reason == Reason.SAME_RUNNING_OWNER || reason == Reason.SAME_POPUP_OWNER;
            require((kind == Kind.SAME_FACTS) == same, "assessment kind/reason differs");
            require((kind == Kind.UNAVAILABLE) == (reason == Reason.INCOMPLETE_PROJECTION),
                    "unavailable requires incomplete projection reason");
        }
        public boolean sameFacts() { return kind == Kind.SAME_FACTS; }
        public boolean replayAllowed() { return false; }
        public boolean actionAdmissionGranted() { return false; }
        public boolean sourceAdmissionGranted() { return false; }
        public int savedDayCredit() { return 0; }
    }

    public static Assessment change(Frame previous, Frame refreshed) {
        Objects.requireNonNull(previous); Objects.requireNonNull(refreshed);
        if (!previous.dateRaw().present() || !refreshed.dateRaw().present()
                || !previous.paused().present() || !refreshed.paused().present()
                || !previous.speed().present() || !refreshed.speed().present()
                || missing(previous.activeEvent()) || missing(refreshed.activeEvent())) { return unavailable(); }
        if (refreshed.dateRaw().required().compareTo(previous.dateRaw().required()) < 0) { return changed(Reason.DATE_REGRESSED); }
        if (!previous.activeEvent().equals(refreshed.activeEvent())) { return changed(Reason.EVENT_CHANGED); }
        if (!previous.paused().equals(refreshed.paused()) || !previous.speed().equals(refreshed.speed())) {
            return changed(Reason.CONTROL_CHANGED);
        }
        return same(Reason.SAME_TIMELINE);
    }

    public static Assessment resumeOwner(Frame previous, Frame refreshed) { return timeline(previous, refreshed, true); }
    public static Assessment pauseOwner(Frame previous, Frame refreshed) { return timeline(previous, refreshed, false); }

    private static Assessment timeline(Frame previous, Frame refreshed, boolean expectedPaused) {
        Objects.requireNonNull(previous); Objects.requireNonNull(refreshed);
        if (!refreshed.mapReady().present() || !refreshed.paused().present() || missing(refreshed.terminalReason())
                || !completeOwner(previous) || !completeOwner(refreshed)) { return unavailable(); }
        if (!refreshed.mapReady().required()) { return changed(Reason.MAP_NOT_READY); }
        if (refreshed.paused().required() != expectedPaused) { return changed(Reason.PAUSE_STATE_CHANGED); }
        if (refreshed.terminalReason().presence() != Presence.NULL) { return changed(Reason.TERMINAL_PRESENT); }
        if (!sameOwner(previous, refreshed)) { return changed(Reason.OWNER_CHANGED); }
        Assessment change = change(previous, refreshed);
        return change.sameFacts() ? same(expectedPaused ? Reason.SAME_PAUSED_OWNER : Reason.SAME_RUNNING_OWNER) : change;
    }

    public static Assessment popupOwner(Frame starting, Frame refreshed, Frame settled) {
        Objects.requireNonNull(starting); Objects.requireNonNull(refreshed); Objects.requireNonNull(settled);
        if (!completeOwner(starting) || !completeOwner(refreshed) || !completeOwner(settled)
                || !starting.dateRaw().present() || !refreshed.dateRaw().present() || !settled.dateRaw().present()
                || !starting.playedCharacter().present() || !starting.localPlayerId().present()
                || missing(refreshed.activeEvent()) || missing(settled.activeEvent())
                || missing(refreshed.pendingInteraction()) || missing(settled.pendingInteraction())) { return unavailable(); }
        boolean event = refreshed.activeEvent().present() && refreshed.activeEvent().required().validEvent();
        boolean interaction = refreshed.pendingInteraction().present() && refreshed.pendingInteraction().required().nonempty();
        if (!event && !interaction) { return changed(Reason.POPUP_NOT_VALID); }
        if (!refreshed.activeEvent().equals(settled.activeEvent())
                || !refreshed.pendingInteraction().equals(settled.pendingInteraction())) { return changed(Reason.POPUP_CHANGED); }
        if (refreshed.dateRaw().required().compareTo(starting.dateRaw().required()) < 0
                || !settled.dateRaw().equals(refreshed.dateRaw())) { return changed(Reason.POPUP_DATE_UNSETTLED); }
        PlayedCharacter actor = starting.playedCharacter().required();
        if (!actor.characterId().present() || !actor.alive().present()) { return unavailable(); }
        if (!actor.alive().required() || actor.characterId().required().signum() <= 0
                || !actor.characterId().equals(starting.episodeCharacterId())) { return changed(Reason.ACTOR_NOT_ALIVE); }
        for (Frame candidate : List.of(refreshed, settled)) {
            if (!candidate.mapReady().present() || !candidate.paused().present() || missing(candidate.terminalReason())
                    || !candidate.localPlayerId().present() || !candidate.playedCharacter().present()
                    || !candidate.revision().present() || !candidate.nativeRevision().present()) { return unavailable(); }
            if (!candidate.mapReady().required()) { return changed(Reason.MAP_NOT_READY); }
            if (candidate.terminalReason().presence() != Presence.NULL) { return changed(Reason.TERMINAL_PRESENT); }
            PlayedCharacter played = candidate.playedCharacter().required();
            if (!played.characterId().present() || !played.alive().present()) { return unavailable(); }
            if (!sameOwner(starting, candidate) || !candidate.localPlayerId().equals(starting.localPlayerId())
                    || !played.characterId().equals(actor.characterId())) { return changed(Reason.OWNER_CHANGED); }
            if (!played.alive().required()) { return changed(Reason.ACTOR_NOT_ALIVE); }
        }
        if (settled.revision().required().compareTo(refreshed.revision().required()) < 0
                || settled.nativeRevision().required().compareTo(refreshed.nativeRevision().required()) < 0) {
            return changed(Reason.REVISION_REGRESSED);
        }
        return same(Reason.SAME_POPUP_OWNER);
    }

    private static boolean completeOwner(Frame frame) {
        return frame.episodeCharacterId().present() && frame.episodeCharacterId().required().signum() > 0
                && frame.episodeRunId().present() && frame.diagnostics().present()
                && positive(frame.diagnostics().required().bridgePid())
                && positive(frame.diagnostics().required().connectionGeneration());
    }
    private static boolean positive(Field<BigInteger> field) { return field.present() && field.required().signum() > 0; }
    private static boolean sameOwner(Frame first, Frame second) {
        return first.episodeCharacterId().equals(second.episodeCharacterId()) && first.episodeRunId().equals(second.episodeRunId())
                && first.diagnostics().required().bridgePid().equals(second.diagnostics().required().bridgePid())
                && first.diagnostics().required().connectionGeneration().equals(second.diagnostics().required().connectionGeneration());
    }
    private static boolean missing(Field<?> field) { return field.presence() == Presence.MISSING; }
    private static Assessment unavailable() { return new Assessment(Kind.UNAVAILABLE, Reason.INCOMPLETE_PROJECTION); }
    private static Assessment changed(Reason reason) { return new Assessment(Kind.CHANGED, reason); }
    private static Assessment same(Reason reason) { return new Assessment(Kind.SAME_FACTS, reason); }
}
