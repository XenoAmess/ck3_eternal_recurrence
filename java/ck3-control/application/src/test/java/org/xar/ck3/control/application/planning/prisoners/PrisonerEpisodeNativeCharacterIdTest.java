package org.xar.ck3.control.application.planning.prisoners;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Pure DATA contract contrast; not a Root proof, Native dispatch or live Game result. */
final class PrisonerEpisodeNativeCharacterIdTest {
    private static final String MACHINE = "controlled-prisoner-owner-machine";
    private static final ExactRef BASIS = new ExactRef("controlled/owner-basis", 1, "1".repeat(64));
    private static final SessionIdentity SESSION = new SessionIdentity(MACHINE,
            new GameGeneration(42, new PythonOnlyUInt64(BigInteger.valueOf(1234))), "controlled-owner-session");
    private static final G2Source SOURCE = new G2Source(MACHINE, "2026-10-29T00:00:00Z", "controlled-owner-data", BASIS);

    private static PrisonerEpisodeLedger12004.Owner owner(long actor) {
        return new PrisonerEpisodeLedger12004.Owner(SESSION, actor, "controlled-owner-episode", SOURCE);
    }

    @Test void positiveControlPreservesBothFamilyFreshBodySerde() {
        var owner = owner(73);
        assertEquals(owner, PrisonerEpisodeLedger12004.owner(PrisonerEpisodeLedger12004.owner(owner)));
        for (var family : PrisonerPlanningPorts.Family.values()) {
            var original = PrisonerEpisodeLedger12004.fresh(family, owner, BASIS);
            var decoded = PrisonerEpisodeLedger12004.decode(family, original);
            assertEquals(owner, decoded.epoch().owner());
            assertArrayEquals(original.bytes(), PrisonerEpisodeLedger12004.encode(decoded).bytes());
        }
    }

    @Test void modernNativeRolesReachCurrentOwnerAndBothFamilyFreshBodies() {
        for (int actor : new int[] {0, -2, Integer.MIN_VALUE, Integer.MAX_VALUE}) {
            assertEquals(actor, NativeCharacterId.of(actor).value());
            var current = assertDoesNotThrow(() -> owner(actor), "modern role=" + actor);
            assertEquals(current, PrisonerEpisodeLedger12004.owner(PrisonerEpisodeLedger12004.owner(current)));
            for (var family : PrisonerPlanningPorts.Family.values()) {
                var body = PrisonerEpisodeLedger12004.fresh(family, current, BASIS);
                assertEquals(actor, PrisonerEpisodeLedger12004.decode(family, body).epoch().owner().player());
            }
        }
    }

    @Test void unsignedAliasesDoNotBecomeModernCurrentOwnerRoles() {
        for (long invalid : new long[] {-1, 2147483648L, 4294967294L}) {
            assertThrows(IllegalArgumentException.class, () -> NativeCharacterId.of(invalid));
            assertThrows(IllegalArgumentException.class, () -> owner(invalid), "current actor=" + invalid);
        }
    }

    @Test void rawOwnerRolesKeepStrictIntegerTypesAndNativeSignedBounds() {
        for (int actor : new int[] {0, -2, Integer.MIN_VALUE, Integer.MAX_VALUE}) {
            var raw = PrisonerEpisodeLedger12004.owner(owner(73));
            raw.put("player_id", BigInteger.valueOf(actor));
            assertEquals(actor, PrisonerEpisodeLedger12004.owner(raw).player());
        }
        for (String token : List.of("-1", "-2147483649", "2147483648", "4294967294",
                "true", "2.0", "\"0\"", "null")) {
            var raw = PrisonerEpisodeLedger12004.owner(owner(73));
            raw.set("player_id", StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> PrisonerEpisodeLedger12004.owner(raw), token);
        }
        var absent = PrisonerEpisodeLedger12004.owner(owner(73)); absent.remove("player_id");
        assertThrows(IllegalArgumentException.class, () -> PrisonerEpisodeLedger12004.owner(absent));
    }

    @Test void privateCustodyUint32AndQueryUint64DomainsRemainUnchanged() {
        var identity = new JointBudgetSelector.Frame(BigInteger.valueOf(73), BigInteger.ONE, BigInteger.valueOf(53144328));
        var frame = new JointBudgetSelector.ProposalFrame(identity, "controlled-collection", BigInteger.ONE, "controlled-owner-episode");
        var observed = new ObservationIdentity(MACHINE, SESSION.game(), frame, 1);
        var collection = new PrisonerEpisodeLedger12004.Collection(BASIS, observed, StrictJson.UINT64_MAX, List.of(4294967294L));
        var encoded = PrisonerEpisodeLedger12004.collection(collection);
        assertEquals("18446744073709551615", encoded.path("query_sequence").textValue());
        assertTrue(encoded.path("prisoner_ids").get(0).isIntegralNumber());
        assertEquals(collection, PrisonerEpisodeLedger12004.collection(encoded));
        for (long invalid : new long[] {0, -2, 4294967295L}) {
            assertThrows(IllegalArgumentException.class,
                    () -> new PrisonerEpisodeLedger12004.Collection(BASIS, observed, StrictJson.UINT64_MAX, List.of(invalid)));
        }
    }
}
