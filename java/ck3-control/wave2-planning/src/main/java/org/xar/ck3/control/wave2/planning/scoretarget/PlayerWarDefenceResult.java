package org.xar.ck3.control.wave2.planning.scoretarget;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** A proof over supplied saved fields, not current native state or an action capability. */
public sealed interface PlayerWarDefenceResult permits PlayerWarDefenceResult.Known,
        PlayerWarDefenceResult.Unknown {
    List<BigInteger> listedWarIds();

    record Known(boolean ownDefence, List<BigInteger> listedWarIds) implements PlayerWarDefenceResult {
        public Known { listedWarIds = checked(listedWarIds); }
    }
    record Unknown(Reason reason, List<BigInteger> listedWarIds) implements PlayerWarDefenceResult {
        public Unknown { Objects.requireNonNull(reason, "unknown reason required"); listedWarIds = checked(listedWarIds); }
    }
    enum Reason {
        CONFLICT_OR_TRUNCATED_LIST, MISSING_LIST, INVALID_LIST_TYPE, EMPTY_WITHOUT_PRESENCE,
        INVALID_OR_DUPLICATE_WAR_IDS, MISSING_OR_CONFLICTING_WAR, MISSING_CB_DEFENDER
    }

    private static List<BigInteger> checked(List<BigInteger> identities) {
        List<BigInteger> copy = List.copyOf(identities);
        StrictJson.require(copy.size() <= 1024 && new HashSet<>(copy).size() == copy.size()
                && copy.stream().allMatch(value -> value.signum() >= 0), "invalid listed war identities");
        return copy;
    }
}
