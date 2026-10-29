package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;

/** One pure resource contract for the actual terminal proposal and Native preparation consumers. */
public final class ArmyOrdinaryWarClaims {
    private ArmyOrdinaryWarClaims() { }
    public static Claims of(BigInteger playerCharacterId, BigInteger fullWarId, Optional<BigInteger> primaryOpponentCharacterId) {
        Objects.requireNonNull(playerCharacterId); Objects.requireNonNull(fullWarId); Objects.requireNonNull(primaryOpponentCharacterId);
        StrictJson.require(playerCharacterId.signum() > 0 && fullWarId.signum() >= 0, "terminal claims require the actual played character and complete WarID");
        primaryOpponentCharacterId.ifPresent(opponent -> StrictJson.require(opponent.signum() > 0 && !opponent.equals(playerCharacterId), "terminal claims require a distinct positive original primary opponent"));
        Set<BigInteger> characters = primaryOpponentCharacterId.map(opponent -> Set.of(playerCharacterId, opponent)).orElseGet(() -> Set.of(playerCharacterId));
        return new Claims(Set.of(), Set.of(), characters, Set.of("war:" + fullWarId));
    }
}
