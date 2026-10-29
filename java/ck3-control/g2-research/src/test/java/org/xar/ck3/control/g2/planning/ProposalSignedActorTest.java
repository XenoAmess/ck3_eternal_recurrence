package org.xar.ck3.control.g2.planning;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure actual request producer -> selectors -> ObservationIdentity -> persisted observation field contract.
 * This signed-domain repair does not certify a negative-ID Game or relax a private positive-ID tool. */
final class ProposalSignedActorTest {
    private static void replaceActor(JsonNode node, JsonNode actor) {
        if (node instanceof ObjectNode object && object.has("played_character_id")) object.set("played_character_id", actor);
        if (node.isContainerNode()) node.forEach(child -> replaceActor(child, actor));
    }
    @Test void signedPublicActorSurvivesActualRequestAndCommandCodecWithoutMaskOrAlias() {
        for (int actor : new int[] {Integer.MIN_VALUE, -2, 0, 1, Integer.MAX_VALUE}) {
            var request = ProposalLifecycleFixtures.request(); replaceActor(request, com.fasterxml.jackson.databind.node.IntNode.valueOf(actor));
            var source = ProposalLifecycleFixtures.source();
            var actual = ProposalLifecycleCodec.decode(StrictJson.canonical(request), source).observed();
            assertEquals(BigInteger.valueOf(actor), actual.frame().identity().player());
            assertEquals(actual, ProposalLifecycleCodec.decodeObservation(ProposalLifecycleCodec.observation(actual)));

        }
    }
    @Test void persistentObservationActorHasOneStrictCanonicalTextRepresentation() {
        var base = ProposalLifecycleCodec.decode(StrictJson.canonical(ProposalLifecycleFixtures.request()), ProposalLifecycleFixtures.source()).observed();
        for (JsonNode value : List.of(com.fasterxml.jackson.databind.node.TextNode.valueOf("+1"),
                com.fasterxml.jackson.databind.node.TextNode.valueOf("-0"), com.fasterxml.jackson.databind.node.TextNode.valueOf("01"),
                com.fasterxml.jackson.databind.node.TextNode.valueOf("-01"), com.fasterxml.jackson.databind.node.TextNode.valueOf("-1"),
                com.fasterxml.jackson.databind.node.TextNode.valueOf("2147483648"), com.fasterxml.jackson.databind.node.IntNode.valueOf(-2),
                com.fasterxml.jackson.databind.node.BooleanNode.TRUE, com.fasterxml.jackson.databind.node.NullNode.instance)) {
            var encoded = ProposalLifecycleCodec.observation(base); ((ObjectNode) encoded.get("frame")).set("played_character_id", value);
            assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.decodeObservation(encoded));
        }
    }
    @Test void sentinelOutOfRangeAndNonIntegralPublicActorAreRejectedAtTheActualRequestBoundary() {
        for (JsonNode value : List.of(com.fasterxml.jackson.databind.node.IntNode.valueOf(-1),
                com.fasterxml.jackson.databind.node.LongNode.valueOf((long) Integer.MAX_VALUE + 1),
                com.fasterxml.jackson.databind.node.LongNode.valueOf((long) Integer.MIN_VALUE - 1),
                com.fasterxml.jackson.databind.node.BooleanNode.TRUE, com.fasterxml.jackson.databind.node.DoubleNode.valueOf(-2.0),
                com.fasterxml.jackson.databind.node.TextNode.valueOf("-2"), com.fasterxml.jackson.databind.node.NullNode.instance)) {
            var request = ProposalLifecycleFixtures.request(); replaceActor(request, value);
            assertThrows(IllegalArgumentException.class, () -> ProposalLifecycleCodec.decode(StrictJson.canonical(request), ProposalLifecycleFixtures.source()));
        }
    }
}
