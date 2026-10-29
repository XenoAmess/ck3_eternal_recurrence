package org.xar.ck3.control.wave3.military.holyobservation;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.math.BigInteger;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract.Choice;
import org.xar.ck3.control.wave2.military.holycost.HolyCostObservation.Build;

/** Complete observed native joiner set; faith/fervor inputs never become a final join score. */
public record HolyDefenderInputs(Build build, boolean available, String unavailableReason,
        BigInteger captureEpoch, BigInteger nativeRevision, BigInteger publicRevision, int dateRaw,
        int playedCharacterId, String declarationId, Choice selectedDeclaration,
        Long primaryAttackerCharacterId, Long primaryDefenderCharacterId,
        boolean primaryDefenderFaithAvailable, String primaryDefenderFaithUnavailableReason,
        Long primaryDefenderRiteId, Long primaryDefenderFaithId, Long cbFlagsRaw, Boolean defenderFaithCanJoin,
        boolean nativeJoinerSetObserved, long joinerCount, List<Joiner> joiners) {
    public HolyDefenderInputs {
        require(build != null && selectedDeclaration != null, "typed native owner required");
        StrictJson.text(declarationId);
        positiveUint64(captureEpoch); positiveUint64(nativeRevision); positiveUint64(publicRevision);
        require(available == nativeJoinerSetObserved, "availability describes complete native set observation");
        reason(unavailableReason, available);
        unsigned32Nullable(primaryAttackerCharacterId); unsigned32Nullable(primaryDefenderCharacterId);
        unsigned32Nullable(primaryDefenderRiteId); unsigned32Nullable(primaryDefenderFaithId); unsigned32Nullable(cbFlagsRaw);
        reason(primaryDefenderFaithUnavailableReason, primaryDefenderFaithAvailable);
        require(!primaryDefenderFaithAvailable || primaryDefenderRiteId != null && primaryDefenderFaithId != null,
                "observed primary defender faith requires both identities");
        require(cbFlagsRaw == null ? defenderFaithCanJoin == null
                : defenderFaithCanJoin != null && defenderFaithCanJoin == ((cbFlagsRaw & (1L << 15)) != 0),
                "CB joining permission must preserve actual bit 15");
        require(!nativeJoinerSetObserved || cbFlagsRaw != null, "observed native set requires the actual CB flag");
        require(joiners != null && joinerCount >= 0 && joinerCount <= 0xffff_ffffL && joinerCount == joiners.size(),
                "complete ordered native joiner list required");
        joiners = List.copyOf(joiners);
        require(nativeJoinerSetObserved || joiners.isEmpty(), "unobserved native set cannot carry fabricated rows");
        require(!Boolean.FALSE.equals(defenderFaithCanJoin) || joiners.isEmpty(), "disabled CB branch must have an empty set");
        for (Joiner row : joiners) {
            if (row.faithAvailable() && primaryDefenderFaithAvailable) {
                require(row.matchesPrimaryDefenderFaith() != null
                        && row.matchesPrimaryDefenderFaith() == row.faithId().equals(primaryDefenderFaithId),
                        "faith match must compare the observed FaithIDs");
            } else { require(row.matchesPrimaryDefenderFaith() == null, "unknown faith identity requires unknown match"); }
        }
    }
    public record Joiner(long characterId, boolean faithAvailable, boolean fervorAvailable,
                         String unavailableReason, Long riteId, Long faithId, Long faithFervorRaw,
                         Boolean matchesPrimaryDefenderFaith) {
        public Joiner {
            require(characterId >= 0 && characterId <= 0xffff_ffffL, "native uint32 CharacterID required");
            unsigned32Nullable(riteId); unsigned32Nullable(faithId);
            require(!faithAvailable || riteId != null && faithId != null, "observed row faith requires both identities");
            require(!fervorAvailable || faithAvailable && faithFervorRaw != null, "observed fervor requires faith and raw value");
            require(fervorAvailable || faithFervorRaw == null, "failed fervor must remain null");
            reason(unavailableReason, faithAvailable && fervorAvailable);
        }
    }
    static void positiveUint64(BigInteger value) {
        require(value != null && value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 required");
    }
    static void unsigned32Nullable(Long value) { require(value == null || value >= 0 && value <= 0xffff_ffffL, "nullable uint32 required"); }
    static void reason(String value, boolean available) {
        require(available ? value == null : value != null && value.codePoints().anyMatch(point ->
                !(Character.isWhitespace(point) || Character.isSpaceChar(point) || point == 0x85)),
                "unavailable reason must identify its stage");
    }
}
