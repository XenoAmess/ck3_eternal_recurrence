package org.xar.ck3.control.g2.m0;

import java.math.BigInteger;
import java.util.Objects;

/** The original fourteen-field paused Raiktor identity, shared by the M0 producer and evaluator. */
public record M0Frame(String snapshotId, BigInteger snapshotRevision, BigInteger nativeRevision,
        int dateRaw, String connectionId, String episodeId, int ck3Pid, boolean paused, int warId,
        int activeCasusBelliDatabaseIndex, String activeCasusBelliKey,
        int primaryAttackerCharacterId, int primaryDefenderCharacterId, int claimantCharacterId) {
    private static final BigInteger UINT64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);

    public M0Frame {
        nonempty(snapshotId, "snapshot_id"); nonempty(connectionId, "connection_id"); nonempty(episodeId, "episode_id");
        positiveUint64(snapshotRevision, "snapshot_revision"); positiveUint64(nativeRevision, "native_revision");
        require(ck3Pid > 0, "ck3_pid must be positive");
        require(activeCasusBelliDatabaseIndex >= 0, "active_casus_belli_database_index must be nonnegative");
        require(paused && "raiktor_claim_cb".equals(activeCasusBelliKey)
            && primaryAttackerCharacterId != primaryDefenderCharacterId, "frame is not an exact paused Raiktor frame");
        fullId(warId, "war_id"); fullId(primaryAttackerCharacterId, "primary_attacker_character_id");
        fullId(primaryDefenderCharacterId, "primary_defender_character_id"); fullId(claimantCharacterId, "claimant_character_id");
    }

    private static void positiveUint64(BigInteger value, String name) {
        Objects.requireNonNull(value, name);
        require(value.signum() > 0 && value.compareTo(UINT64_MAX) <= 0, name + " must be positive uint64");
    }

    private static void fullId(int value, String name) {
        // The original full-generation identity is signed32; only -1 is the invalid sentinel.
        require(value != -1, name + " is the invalid sentinel");
    }

    private static void nonempty(String value, String name) {
        Objects.requireNonNull(value, name);
        require(value.codePoints().anyMatch(code -> !Character.isWhitespace(code) && !Character.isSpaceChar(code) && code != 0x85),
                name + " must be a nonempty string");
    }

    private static void require(boolean condition, String reason) {
        if (!condition) { throw new IllegalArgumentException(reason); }
    }
}
