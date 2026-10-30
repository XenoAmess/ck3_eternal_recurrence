package org.xar.ck3.control.wave2.finance.factionalerts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel.*;
import static org.xar.ck3.control.wave2.finance.factionalerts.FactionThreatAdmission.*;

/** Actual native reader/serializer output from authored owned memory; no live Game/action.
 * The outer command_result projection below is authored to the current public result contract.
 */
final class FactionThreatAdmissionNativeCharacterTest {
    private static JsonNode corpus() throws IOException {
        try (var stream = FactionThreatAdmissionNativeCharacterTest.class.getResourceAsStream(
                "/factionalerts/native-member-generation06.json")) {
            assertNotNull(stream);
            return StrictJson.parse(stream.readAllBytes(), FactionAlertsCodec.MAX_BYTES);
        }
    }
    private static byte[] packet(JsonNode body) {
        ObjectNode result = StrictJson.object().put("step", STEP).put("accepted", true)
                .put("status", body.get("status").textValue()).put("query_sequence", 1)
                .put("snapshot_revision", body.get("snapshot_revision").bigIntegerValue())
                .put("player_faction_alerts_ready", body.at("/readiness/alert_ready").booleanValue())
                .put("backend_id", "native-headless");
        result.set("player_faction_alerts", body);
        return StrictJson.canonical(result, FactionAlertsCodec.MAX_BYTES);
    }
    private static ExpectedFrame expected(JsonNode body) {
        return new ExpectedFrame(body.get("date_raw").intValue(),
                body.get("snapshot_revision").bigIntegerValue(), Optional.of(Build.CK3_12004));
    }
    @Test void nativeSerializerSignedAndZeroMembersReachPublicThreatAdmission() throws Exception {
        int count = 0;
        for (JsonNode item : corpus().get("cases")) {
            if (!item.get("actual_available").booleanValue()) continue;
            JsonNode body = item.get("receipt");
            int recipient = item.get("requested_member_id").intValue();
            int actor = body.get("player_character_id").intValue();
            int faction = body.at("/targeting_factions/0/faction_id").intValue();
            var request = new Request(expected(body), actor, faction, recipient);
            var result = fromExistingDriverResult(packet(body), request, "[]".getBytes(java.nio.charset.StandardCharsets.UTF_8));
            Admitted admitted = assertInstanceOf(Admitted.class, result, item.get("case").textValue());
            assertEquals(recipient, admitted.request().recipientCharacterId());
            assertEquals(Optional.of(recipient), admitted.faction().leaderCharacterId());
            assertTrue(admitted.faction().characterMemberIds().contains(recipient));
            assertEquals(item.get("human_id_bits").bigIntegerValue(),
                    BigInteger.valueOf(Integer.toUnsignedLong(recipient)));
            assertEquals(new Missing(MissingReason.RECIPIENT_NOT_LEADER_OR_MEMBER),
                    fromExistingDriverResult(packet(body), new Request(expected(body), actor, faction, 99),
                            "[]".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            count++;
        }
        assertEquals(2, count);
    }
    @Test void publicThreatRequestUsesExactNativeCharacterDomainWithoutChangingFactionDomain() {
        var expected = new ExpectedFrame(1, BigInteger.ONE, Optional.of(Build.CK3_12004));
        for (int actor : new int[]{Integer.MIN_VALUE, -2147483646, 0, Integer.MAX_VALUE}) {
            Request request = new Request(expected, actor, 1, 99);
            assertEquals(actor, request.actorCharacterId());
        }
        assertThrows(IllegalArgumentException.class, () -> new Request(expected, -1, 1, 99));
        assertThrows(IllegalArgumentException.class, () -> new Request(expected, 99, 1, -1));
        assertThrows(IllegalArgumentException.class, () -> new Request(expected, 99, 0, 0));
        assertThrows(IllegalArgumentException.class, () -> new Request(expected, 0, 1, 0));
    }
    @Test void privatePreviewAndPendingActionDoNotInheritPublicAlertReadEligibility() {
        var id = new GiftReadTransport.ReadId("faction-gift-read-00000000000000000000000000000000");
        for (BigInteger recipient : new BigInteger[]{BigInteger.ZERO, BigInteger.valueOf(-2147483646)}) {
            assertThrows(IllegalArgumentException.class,
                    () -> new GiftReadTransport.Command(id, BigInteger.ONE, BigInteger.ZERO, recipient));
            assertThrows(IllegalArgumentException.class,
                    () -> new GiftPendingModel.Baseline(BigInteger.ONE, recipient, BigInteger.ONE,
                            BigInteger.ONE, BigInteger.ZERO, BigInteger.TEN, BigInteger.valueOf(1_000_000),
                            BigInteger.ZERO, BigInteger.ONE, BigInteger.ZERO, java.util.List.of(recipient),
                            BigInteger.ONE, BigInteger.ONE));
        }
    }
}
