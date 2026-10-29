package org.xar.ck3.control.wave2.planning.scoretarget;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.planning.scoretarget.PlayerWarDefenceResult.Reason;

/** Exact pure player_war_defence order: verify every listed war before returning known. */
public final class PlayerWarDefence {
    private PlayerWarDefence() { }

    public static PlayerWarDefenceResult project(PlayerWarInput input) {
        PlayerWarInput.CharacterWars fields = input.character();
        if (fields.conflicting() || fields.incomplete()) { return unknown(Reason.CONFLICT_OR_TRUNCATED_LIST); }
        if (fields.list() instanceof ScalarField.Missing && !fields.explicitPresence()) { return unknown(Reason.MISSING_LIST); }
        String list;
        if (fields.list() instanceof ScalarField.Missing) { list = ""; }
        else if (fields.list() instanceof ScalarField.Text text) { list = text.value(); }
        else { return unknown(Reason.INVALID_LIST_TYPE); }
        List<String> tokens = pythonSplit(list);
        if (tokens.isEmpty() && !fields.explicitPresence()) { return unknown(Reason.EMPTY_WITHOUT_PRESENCE); }
        if (tokens.size() > 1024) { return unknown(Reason.INVALID_OR_DUPLICATE_WAR_IDS); }
        List<BigInteger> identities = new ArrayList<>();
        HashSet<BigInteger> seen = new HashSet<>();
        for (String token : tokens) {
            Optional<BigInteger> identity = savedInteger(token);
            if (identity.isEmpty() || !seen.add(identity.orElseThrow())) { return unknown(Reason.INVALID_OR_DUPLICATE_WAR_IDS); }
            identities.add(identity.orElseThrow());
        }
        boolean ownDefence = false;
        for (BigInteger identity : identities) {
            // SaveProjection has integer keys; its exact JSON projection has canonical string keys.
            PlayerWarInput.WarEntry row = input.wars().get(identity.toString());
            if (!(row instanceof PlayerWarInput.ObservedWar war) || war.conflictingDefender()) {
                return new PlayerWarDefenceResult.Unknown(Reason.MISSING_OR_CONFLICTING_WAR, identities);
            }
            Optional<BigInteger> defender = war.defender().integer();
            if (defender.isEmpty()) { return new PlayerWarDefenceResult.Unknown(Reason.MISSING_CB_DEFENDER, identities); }
            ownDefence |= defender.orElseThrow().equals(input.actor());
        }
        return new PlayerWarDefenceResult.Known(ownDefence, identities);
    }

    private static PlayerWarDefenceResult.Unknown unknown(Reason reason) {
        return new PlayerWarDefenceResult.Unknown(reason, List.of());
    }

    /** Python re.fullmatch(r'\d+', text) + int(text), without bool/float coercion. */
    static Optional<BigInteger> savedInteger(String text) {
        if (text.isEmpty()) { return Optional.empty(); }
        StringBuilder ascii = new StringBuilder();
        int[] points = text.codePoints().toArray();
        for (int point : points) {
            if (Character.getType(point) != Character.DECIMAL_DIGIT_NUMBER) { return Optional.empty(); }
            int digit = Character.digit(point, 10);
            if (digit < 0) { return Optional.empty(); }
            ascii.append((char) ('0' + digit));
        }
        if (ascii.length() > 4300) {
            throw new ProjectionDomainRejection("saved integer exceeds qualified Python decimal-string digit limit");
        }
        return Optional.of(new BigInteger(ascii.toString()));
    }

    private static List<String> pythonSplit(String value) {
        List<String> tokens = new ArrayList<>();
        int start = -1;
        for (int index = 0; index < value.length();) {
            int point = value.codePointAt(index);
            boolean whitespace = Character.isWhitespace(point) || Character.isSpaceChar(point) || point == 0x85;
            if (whitespace && start >= 0) { tokens.add(value.substring(start, index)); start = -1; }
            else if (!whitespace && start < 0) { start = index; }
            index += Character.charCount(point);
        }
        if (start >= 0) { tokens.add(value.substring(start)); }
        return tokens;
    }
}
