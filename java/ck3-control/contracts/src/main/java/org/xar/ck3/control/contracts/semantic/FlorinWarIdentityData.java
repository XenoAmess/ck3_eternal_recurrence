package org.xar.ck3.control.contracts.semantic;

import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.OptionalInt;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** Florin War-only read DATA. Identity and optional score never construct a legacy rich War or action permit. */
public final class FlorinWarIdentityData {
    public static final String SCHEMA = "ck3_1210_active_wars_identity_v1";
    public static final String RICH_UNAVAILABLE_REASON = "active_wars_rich_fields_not_observed";
    public static final int MAX_OWNED_WARS = 4096, MAX_SIDE = 65_536, MAX_PARTICIPANTS = 1_048_576;
    private FlorinWarIdentityData() { }

    /** A signed full-generation CWar identity, distinct from a Character ID and from a legacy nonnegative ID. */
    public record WarFullId(int value) {
        public WarFullId { need(value != -1, "absent War sentinel cannot identify an observed War"); }
    }
    public enum Side { ATTACKER, DEFENDER }

    public sealed interface Score permits AvailableScore, UnavailableScore { }
    /** Native raw score has no invented clamp or GUI scaling. Its relative sign is checked against the observed side. */
    public record AvailableScore(int nativeAttackerRaw, int playerRelative) implements Score { }
    /** A guarded read can retain raw INT_MIN on defender sign overflow; missing score never means zero. */
    public record UnavailableScore(OptionalInt nativeAttackerRaw, String reason) implements Score {
        public UnavailableScore {
            Objects.requireNonNull(nativeAttackerRaw);
            need(reason != null && !reason.isEmpty(), "original score-unavailable reason required");
        }
    }

    public enum RichField {
        TARGETED_TITLE_IDS, WAR_OBJECTIVE_PROVINCE_IDS, OBJECTIVE_PROVINCE_STATES,
        ALLIED_ARMIES, ENEMY_ARMIES, ENEMY_PRIMARY_DEFAULT_RAISE_PROVINCE_ID
    }
    /** The named missing field is retained as a gap, never represented by a manufactured empty collection or zero. */
    public record UnavailableField(RichField field, String reason) {
        public UnavailableField {
            Objects.requireNonNull(field);
            need(RICH_UNAVAILABLE_REASON.equals(reason), "the frozen War reader leaves every rich field unavailable");
        }
    }

    public record Identity(WarFullId warId, NativeCharacterId actualPlayerCharacterId, Side playerSide,
            NativeCharacterId primaryAttackerCharacterId, NativeCharacterId primaryDefenderCharacterId,
            NativeCharacterId primaryOpponentCharacterId, boolean playerIsPrimaryWarLeader,
            List<NativeCharacterId> attackerParticipantIds, List<NativeCharacterId> defenderParticipantIds,
            Score score, List<UnavailableField> richFields) {
        public Identity {
            Objects.requireNonNull(warId); Objects.requireNonNull(actualPlayerCharacterId); Objects.requireNonNull(playerSide);
            Objects.requireNonNull(primaryAttackerCharacterId); Objects.requireNonNull(primaryDefenderCharacterId);
            Objects.requireNonNull(primaryOpponentCharacterId); Objects.requireNonNull(score);
            attackerParticipantIds = List.copyOf(attackerParticipantIds);
            defenderParticipantIds = List.copyOf(defenderParticipantIds);
            richFields = List.copyOf(richFields);
            need(attackerParticipantIds.size() <= MAX_SIDE && defenderParticipantIds.size() <= MAX_SIDE,
                    "bounded complete native participant sides required");
            boolean attack = attackerParticipantIds.contains(actualPlayerCharacterId);
            boolean defend = defenderParticipantIds.contains(actualPlayerCharacterId);
            need(attack != defend && attack == (playerSide == Side.ATTACKER),
                    "exact played Character must occur on its observed War side only");
            NativeCharacterId expectedOpponent = playerSide == Side.ATTACKER
                    ? primaryDefenderCharacterId : primaryAttackerCharacterId;
            NativeCharacterId expectedLeader = playerSide == Side.ATTACKER
                    ? primaryAttackerCharacterId : primaryDefenderCharacterId;
            need(expectedOpponent.equals(primaryOpponentCharacterId)
                    && playerIsPrimaryWarLeader == expectedLeader.equals(actualPlayerCharacterId),
                    "primary opponent and leader flag must follow full identities and observed side");
            if (score instanceof AvailableScore available) {
                long relative = playerSide == Side.ATTACKER ? (long) available.nativeAttackerRaw()
                        : -(long) available.nativeAttackerRaw();
                need(relative == available.playerRelative(), "observed player-relative score differs from checked native sign");
            } else if (((UnavailableScore) score).nativeAttackerRaw().isPresent()) {
                UnavailableScore unavailable = (UnavailableScore) score;
                need(playerSide == Side.DEFENDER && unavailable.nativeAttackerRaw().getAsInt() == Integer.MIN_VALUE
                        && "active_wars_relative_score_overflow".equals(unavailable.reason()),
                        "only native defender INT_MIN overflow retains raw score without a relative value");
            }
            var fields = new HashSet<RichField>();
            for (UnavailableField field : richFields) need(fields.add(field.field()), "duplicate rich-field gap");
            need(fields.equals(java.util.Set.of(RichField.values())), "every unobserved rich War field must remain unavailable");
        }
    }

    /** Original Core prefix, including its explicit absent-actor metadata on an unavailable War read. */
    public record Prefix(int dateRaw, int speed, boolean paused, int localPlayerId, boolean mapReady,
            boolean hasPlayedCharacter, int playedCharacterId, boolean playedCharacterAlive) {
        public Prefix {
            need(speed >= 1 && speed <= 5, "Core speed 1..5 required");
            need(hasPlayedCharacter ? playedCharacterId != -1 : playedCharacterId == -1 && !playedCharacterAlive,
                    "Core played-character absence metadata differs");
        }
    }
    public sealed interface Core permits AvailableCore, UnavailableCore { }
    public record AvailableCore(Prefix prefix) implements Core {
        public AvailableCore { Objects.requireNonNull(prefix); }
    }
    public record UnavailableCore(boolean applicationMainObserved, String reason) implements Core {
        public UnavailableCore { need(reason != null && !reason.isEmpty(), "original Core unavailable reason required"); }
    }
    public record ScanMetrics(int warSlotsScanned, int activeWarRows, int endedWarRows, int participantRecords) {
        public ScanMetrics {
            need(warSlotsScanned >= 0 && warSlotsScanned <= 1_048_576 && activeWarRows >= 0 && endedWarRows >= 0
                    && (long) activeWarRows + endedWarRows <= warSlotsScanned
                    && participantRecords >= 0 && participantRecords <= MAX_PARTICIPANTS,
                    "native War scan counts outside their proven scope");
        }
    }
    public sealed interface Observation permits Partial, Unavailable {
        Core coreFrame();
        boolean applicationMainObserved();
        int nativeScoreCallsAttempted();
    }
    public record Partial(AvailableCore coreFrame, List<Identity> activeWars, boolean scoreComplete,
            ScanMetrics metrics, int nativeScoreCallsAttempted) implements Observation {
        public Partial {
            Objects.requireNonNull(coreFrame); Objects.requireNonNull(metrics); activeWars = List.copyOf(activeWars);
            Prefix prefix = coreFrame.prefix();
            need(prefix.paused() && prefix.localPlayerId() >= 0 && prefix.mapReady()
                    && prefix.hasPlayedCharacter() && prefix.playedCharacterAlive(),
                    "War identity DATA requires its actual paused living played-character prefix");
            need(activeWars.size() <= MAX_OWNED_WARS && activeWars.size() <= metrics.activeWarRows(),
                    "owned War observation scope exceeded");
            var identities = new HashSet<WarFullId>(); int participantCount = 0, rowsWithRawScore = 0;
            for (Identity row : activeWars) {
                need(row.actualPlayerCharacterId().value() == prefix.playedCharacterId(), "War row crossed its actual played Character");
                need(identities.add(row.warId()), "duplicate complete War identity");
                if (row.score() instanceof AvailableScore || ((UnavailableScore) row.score()).nativeAttackerRaw().isPresent()) rowsWithRawScore++;
                participantCount += row.attackerParticipantIds().size() + row.defenderParticipantIds().size();
                need(participantCount <= MAX_PARTICIPANTS, "War participant collection scope exceeded");
            }
            need(participantCount <= metrics.participantRecords(), "War scan participant count lost an observed owned row");
            need(scoreComplete == activeWars.stream().allMatch(row -> row.score() instanceof AvailableScore),
                    "score completeness must agree with every observed row, including known-empty scope");
            calls(nativeScoreCallsAttempted);
            need(nativeScoreCallsAttempted >= 2 * rowsWithRawScore && nativeScoreCallsAttempted <= 2 * activeWars.size(),
                    "observed score values require both Native capture calls; identity-only rows cannot invent calls");
        }
        @Override public boolean applicationMainObserved() { return true; }
    }
    /** Identity failure retains its original Core, reason and call count, never a stale or pretend-empty War collection. */
    public record Unavailable(Core coreFrame, boolean applicationMainObserved, int nativeScoreCallsAttempted,
            String reason) implements Observation {
        public Unavailable {
            Objects.requireNonNull(coreFrame);
            need(reason != null && !reason.isEmpty(), "original War identity unavailable reason required");
            need(applicationMainObserved == (coreFrame instanceof AvailableCore
                    || ((UnavailableCore) coreFrame).applicationMainObserved()), "War and Core application-main observations differ");
            calls(nativeScoreCallsAttempted);
        }
    }
    private static void calls(int value) { need(value >= 0 && value <= 2 * MAX_OWNED_WARS, "bounded native score call count required"); }
    private static void need(boolean condition, String message) { StrictJson.require(condition, message); }
}
