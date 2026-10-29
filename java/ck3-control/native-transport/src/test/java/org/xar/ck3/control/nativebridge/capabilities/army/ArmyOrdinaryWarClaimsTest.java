package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

final class ArmyOrdinaryWarClaimsTest {
    private static Obj object(String json) {
        return org.xar.ck3.control.application.driver.DriverJson.object(json.getBytes(java.nio.charset.StandardCharsets.UTF_8), 65536);
    }
    private static Complete actual(String wars) {
        var source = ArmyOrdinaryActionBoundaryTest.context();
        return new Complete(source.before(), source.source(), source.sessionId(), BigInteger.ONE,
                object("{\"active_wars\":" + wars + "}"), ArmyOrdinaryActionBoundaryTest.REF,
                ArmyOrdinaryActionBoundaryTest.NOW, "a".repeat(64));
    }
    @Test void actualTerminalPreparationRetainsAllOriginalLegacyResourceClaims() {
        var source = ArmyOrdinaryActionBoundaryTest.context(); var war = BigInteger.valueOf(23);
        var legacy = ArmyOrdinaryWarClaims.of(source.playerId(), war, Optional.of(BigInteger.valueOf(42)));
        for (var method : java.util.List.of(PublicMethod.ENFORCE_DEMANDS, PublicMethod.SURRENDER_WAR, PublicMethod.OFFER_WHITE_PEACE)) {
            var call = new ArmyCalls.War(method, ArmyOrdinaryActionBoundaryTest.REV, war);
            var claims = ArmyOrdinaryActionPreparation.claims(call, source, actual("[{\"war_id\":23,\"primary_opponent_character_id\":42}]"));
            assertEquals(legacy.characterIds(), claims.characterIds());
            assertTrue(claims.commitmentKeys().containsAll(legacy.commitmentKeys()));
            assertEquals(Set.of(source.playerId(), BigInteger.valueOf(42)), claims.characterIds());
            assertTrue(ArmyOrdinaryActionPreparation.claims(call, source).overlaps(legacy));
        }
    }
    @Test void absentPrimaryOpponentKeepsOnlyTheObservedPlayerAndNeverGuessesAnotherField() {
        var source = ArmyOrdinaryActionBoundaryTest.context();
        var call = new ArmyCalls.War(PublicMethod.SURRENDER_WAR, ArmyOrdinaryActionBoundaryTest.REV, BigInteger.valueOf(23));
        var claims = ArmyOrdinaryActionPreparation.claims(call, source, actual("[{\"war_id\":23,\"opponent_character_id\":42}]"));
        assertEquals(Set.of(source.playerId()), claims.characterIds());
        assertTrue(claims.commitmentKeys().contains("war:23"));
    }
    @Test void malformedDuplicateMissingOrForeignWarSourceCannotSupplyTerminalClaims() {
        var source = ArmyOrdinaryActionBoundaryTest.context();
        var call = new ArmyCalls.War(PublicMethod.OFFER_WHITE_PEACE, ArmyOrdinaryActionBoundaryTest.REV, BigInteger.valueOf(23));
        for (String rows : java.util.List.of("[]", "[{\"war_id\":24,\"primary_opponent_character_id\":42}]",
                "[{\"war_id\":23},{\"war_id\":23}]", "[{\"war_id\":23,\"primary_opponent_character_id\":true}]",
                "[{\"war_id\":23,\"primary_opponent_character_id\":42.0}]"))
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionPreparation.claims(call, source, actual(rows)));
        var before = actual("[{\"war_id\":23,\"primary_opponent_character_id\":42}]");
        var foreign = new Complete(before.identity(), before.source(), before.sessionId() + "-other", before.connectionGeneration(), before.semantic(), before.originalEvidence(), before.observedAt(), before.fullBindingSha256());
        assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionPreparation.claims(call, source, foreign));
    }
}
