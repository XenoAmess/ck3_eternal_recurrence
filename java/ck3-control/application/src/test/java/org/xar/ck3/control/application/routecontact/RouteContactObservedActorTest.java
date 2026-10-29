package org.xar.ck3.control.application.routecontact;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.routecontact.RouteContactModel.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual existing semantic-frame producer -> sole parser/model -> existing route proof consumers.
 * These controlled DATA originals grant no Native/Root/clock/action eligibility; no Python oracle is run.
 */
final class RouteContactObservedActorTest {
    @Test void signedPublicEpisodeIdentitySurvivesProducerCodecModelAndRouteConsumers() {
        for (int actor : List.of(Integer.MIN_VALUE, -2, 0, Integer.MAX_VALUE)) {
            Frame source = frame(actor, 1, 100);
            AdvanceObservationPort.Frame produced = RouteContactCompositeTest.raw(source);
            var complete = new DriverObservationAssembler.Complete(produced.identity(), produced.source(), produced.sessionId(),
                    source.owner().connectionGeneration(), produced.semantic(), produced.originalEvidence(), produced.observedAt(), "b".repeat(64));
            Frame parsed = RouteContactCodec.frame(complete.identity(), complete.source(), complete.sessionId(), complete.semantic());
            assertEquals(source, parsed); assertEquals(actor, parsed.owner().episodeCharacterId());
            assertEquals(BigInteger.valueOf(actor), integer(complete.semantic().get("episode_character_id"), "original actor"));
            Obj durable = object(OpportunityJson.parse(OpportunityJson.encode(complete.semantic())), "original semantic roundtrip");
            assertEquals(parsed, RouteContactCodec.frame(complete.identity(), complete.source(), complete.sessionId(), durable));
            RouteQuery query = RouteContactProofsTest.query(parsed);
            assertTrue(RouteContactProofs.sameFrame(parsed, query));
            var proof = RouteContactProofs.oneDay(parsed, List.of(query), List.of());
            assertEquals(ProofKind.CONTACT_FREE, proof.values().iterator().next().kind());
            Frame newer = RouteContactCodec.frame(RouteContactCompositeTest.raw(frame(actor, 2, 100)));
            assertTrue(RouteContactPostconditions.samePausedRefreshOwner(parsed, newer));
            Frame different = frame(actor == 0 ? -2 : 0, 1, 100);
            assertFalse(RouteContactProofs.sameFrame(different, query), "signed owner changes cannot reuse an old route proof");
        }
    }

    @Test void absenceSentinelOutsideSigned32AndWrongJsonTypesCannotAliasAnActor() {
        AdvanceObservationPort.Frame raw = RouteContactCompositeTest.raw(frame(0, 1, 100));
        List<Value> invalid = List.of(n(-1), n(BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE)),
                n(BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE)), n(new BigInteger("4294967294")),
                new Bool(true), new Text("-2"), new DecimalValue("0.0"), Nil.INSTANCE);
        for (Value actor : invalid) {
            Obj material = raw.semantic().with("episode_character_id", actor);
            Obj durable = object(OpportunityJson.parse(OpportunityJson.encode(material)), "malformed original material");
            assertThrows(IllegalArgumentException.class, () -> RouteContactCodec.frame(raw.identity(), raw.source(), raw.sessionId(), durable));
        }
        var missing = new LinkedHashMap<>(raw.semantic().members()); missing.remove("episode_character_id");
        assertThrows(IllegalArgumentException.class, () -> RouteContactCodec.frame(raw.identity(), raw.source(), raw.sessionId(), new Obj(missing)));
        var prior = RouteContactProofsTest.OWNER;
        assertThrows(IllegalArgumentException.class, () -> new Owner(prior.machineId(), prior.game(), prior.sessionId(), prior.connectionGeneration(),
                prior.bridgePid(), prior.episodeRunId(), -1, prior.localPlayerId()));
    }

    @Test void observedSignedActorNeverWidensArmyWarProvinceOrTransportDomains() {
        AdvanceObservationPort.Frame raw = RouteContactCompositeTest.raw(frame(-2, 1, 100));
        Obj army = object(array(raw.semantic().get("player_armies"), "actual own armies").getFirst(), "actual own army");
        for (Obj invalidArmy : List.of(army.with("army_id", n(-2)), army.with("current_province_id", n(0)))) {
            Obj changed = raw.semantic().with("player_armies", new Arr(List.of(invalidArmy)));
            assertThrows(IllegalArgumentException.class, () -> RouteContactCodec.frame(raw.identity(), raw.source(), raw.sessionId(), changed));
        }
        Obj war = object(array(raw.semantic().get("active_wars"), "actual wars").getFirst(), "actual war");
        Obj changed = raw.semantic().with("active_wars", new Arr(List.of(war.with("war_id", n(-2)))));
        assertThrows(IllegalArgumentException.class, () -> RouteContactCodec.frame(raw.identity(), raw.source(), raw.sessionId(), changed));
        var owner = rawOwner(-2);
        assertThrows(IllegalArgumentException.class, () -> new Owner(owner.machineId(), owner.game(), owner.sessionId(), BigInteger.ZERO,
                owner.bridgePid(), owner.episodeRunId(), owner.episodeCharacterId(), owner.localPlayerId()));
        assertThrows(IllegalArgumentException.class, () -> new Owner(owner.machineId(), owner.game(), owner.sessionId(), owner.connectionGeneration(),
                owner.bridgePid(), owner.episodeRunId(), owner.episodeCharacterId(), -1));
        assertEquals(0, RouteContactCodec.frame(raw).ownArmies().getFirst().armyId());
    }

    private static Owner rawOwner(int actor) {
        var old = RouteContactProofsTest.OWNER;
        return new Owner(old.machineId(), old.game(), old.sessionId(), old.connectionGeneration(), old.bridgePid(), old.episodeRunId(), actor, old.localPlayerId());
    }
    private static Frame frame(int actor, int revision, int date) {
        Frame old = RouteContactProofsTest.starting();
        return new Frame(rawOwner(actor), "native-" + revision, BigInteger.valueOf(revision), BigInteger.valueOf(revision), date,
                old.mapReady(), old.paused(), old.speed(), old.oneLifeTerminal(), old.playedCharacterAlive(), old.activeEvent(), old.pendingInteraction(),
                old.modal(), old.activeWarIds(), old.ownArmies(), old.hostileArmies());
    }
    private static IntegerValue n(long value) { return n(BigInteger.valueOf(value)); }
    private static IntegerValue n(BigInteger value) { return new IntegerValue(value); }
}
