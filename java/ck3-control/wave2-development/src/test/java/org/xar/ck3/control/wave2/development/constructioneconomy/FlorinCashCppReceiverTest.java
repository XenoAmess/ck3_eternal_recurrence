package org.xar.ck3.control.wave2.development.constructioneconomy;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;
import static org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.*;

/** Actual C++ NoGame packets plus explicitly synthetic joined snapshot DATA; no Full/Root/Native authority. */
final class FlorinCashCppReceiverTest {
    private static final String SHA = ExactCk3Build.CK3_1210.executableSha256();
    private static final Map<String, String> PACKETS = Map.of(
            "producer-json.json", "6d6a9fc8b3d58d015be44dafeed34e98437ec2ba70415c2480be1383c93871d5",
            "producer-overflow-json.json", "ef5dade61767c28f96cad431d6e3770710e0492ea5cd91961aef3b0230d35839",
            "producer-wallet-only-json.json", "8d1ca975cb64a8484efec8285a74ddc32d9ad13c84f842c34c2305a52bab1e89",
            "producer-empty-scope-json.json", "31f66be75a6d5a589af4aa5db9e021608271584bcf56d2ccbce0d7e4c0fad024");

    @Test void fourActualCppPacketsRetainTheirPartialValuesAndUnknownMilitaryRows() throws Exception {
        for (String name : PACKETS.keySet()) {
            ObjectNode raw = cash(name); byte[] original = bytes(raw);
            var normalized = RawCashCodec.normalize(original, bytes(snapshot(raw)));
            assertEquals(raw, StrictJson.parse(normalized.toJson()));
            assertArrayEquals(original, bytes(raw));
            assertEquals(-2130706431, normalized.frame().playedCharacterId());
            assertEquals(new BigInteger("18446744073709551615"), normalized.frame().snapshotRevision());
            assertEquals(Boolean.valueOf(raw.get("readiness").get("same_frame_ready").booleanValue()),
                    normalized.metrics().readiness().sameFrameReady().value());
            assertFalse(normalized.metrics().currentMilitaryExpenses().available());
            assertFalse(normalized.metrics().allRaisedMilitaryExpenses().available());
            assertFalse(normalized.metrics().currentMilitaryExpenses().goldRaw().known());
            var decoded = ConstructionEconomyCodec.decodeCash(original);
            assertEquals(BigInteger.valueOf(-2130706431), decoded.frame().actor().orElseThrow());
            assertTrue(decoded.currentMilitary().orElseThrow().gold().isEmpty());
            assertTrue(decoded.allRaisedMilitary().orElseThrow().gold().isEmpty());
            assertFalse(raw.get("complete_snapshot").booleanValue());
            assertFalse(raw.get("formal_action_ready").booleanValue());
        }
    }

    @Test void actualWalletAndNetSupportOnlyTheCurrentScenarioWhileMissingRatesStayUnknown() throws Exception {
        var raw = cash("producer-json.json");
        var normalized = RawCashCodec.normalize(bytes(raw), bytes(snapshot(raw)));
        assertEquals(BigInteger.valueOf(-450000), normalized.metrics().currentTreasury().value().raw());
        assertEquals(BigInteger.valueOf(500000), normalized.metrics().monthlyGrossIncome().value().raw());
        assertEquals(BigInteger.valueOf(720000), normalized.metrics().monthlyTotalExpenses().value().raw());
        assertEquals(BigInteger.valueOf(-220000), normalized.metrics().monthlyNetIncome().value().raw());
        var policy = new BudgetPolicy(BigInteger.ZERO, BigInteger.ZERO, BigInteger.ZERO, 1);
        var budget = ConstructionEconomy.projectBudget(ConstructionEconomyCodec.decodeCash(bytes(raw)), policy);
        assertTrue(budget.current().ready());
        assertFalse(budget.allRaised().ready());
        assertTrue(budget.allRaised().netRate().isEmpty());
        assertTrue(budget.allRaised().missingInputs().containsKey(MissingInput.CURRENT_MILITARY));
        assertTrue(budget.allRaised().missingInputs().containsKey(MissingInput.ALL_RAISED_MILITARY));
        var overflow = cash("producer-overflow-json.json");
        var overflowCash = ConstructionEconomyCodec.decodeCash(bytes(overflow));
        assertTrue(overflowCash.value(CashField.NET).raw().isEmpty());
        assertEquals("war_cash_monthly_net_income_overflow", overflowCash.value(CashField.NET).unavailableReason().orElseThrow());
        assertFalse(ConstructionEconomy.projectBudget(overflowCash, policy).current().ready());
        var walletOnly = RawCashCodec.normalize(bytes(cash("producer-wallet-only-json.json")),
                bytes(snapshot(cash("producer-wallet-only-json.json"))));
        assertTrue(walletOnly.metrics().currentTreasury().known());
        assertFalse(walletOnly.metrics().monthlyNetIncome().known());
    }

    @Test void florinPreservesFullSignedCharacterIdsButRefusesSentinelUnsignedAliasesAndCoercions() throws Exception {
        for (int actor : List.of(0, Integer.MIN_VALUE, -2130706431, Integer.MAX_VALUE)) {
            ObjectNode raw = cash("producer-json.json"); actor(raw, actor);
            var normalized = RawCashCodec.normalize(bytes(raw), bytes(snapshot(raw)));
            assertEquals(actor, normalized.frame().playedCharacterId());
            assertEquals(BigInteger.valueOf(actor), ConstructionEconomyCodec.decodeCash(bytes(raw)).frame().actor().orElseThrow());
        }
        for (String token : List.of("-1", "2147483648", "4294967295", "true", "null", "0.0", "\"-2130706431\"")) {
            ObjectNode raw = cash("producer-json.json"); raw.set("played_character_id", StrictJson.parse(token.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            reject(raw);
        }
    }

    @Test void exactBuildAndMonthlyMarkerCannotBeReplacedByMissingOrLegacyClaims() throws Exception {
        for (String field : List.of("game_version", "executable_sha256", "monthly_income_semantics")) {
            ObjectNode raw = cash("producer-json.json"); raw.remove(field); reject(raw);
        }
        ObjectNode wrongSha = cash("producer-json.json"); wrongSha.put("executable_sha256", ExactCk3Build.CK3_12004.executableSha256()); reject(wrongSha);
        ObjectNode wrongVersion = cash("producer-json.json"); wrongVersion.put("game_version", "1.21.0.0"); reject(wrongVersion);
        ObjectNode wrongMarker = cash("producer-json.json");
        ((ObjectNode) wrongMarker.get("monthly_income_semantics")).put("version", "ck3-1.20.0.4-native-income-minus-total-expenses-v2"); reject(wrongMarker);
        ObjectNode wrongSource = cash("producer-json.json");
        ((ObjectNode) wrongSource.get("monthly_income_semantics")).put("military_expenses_included", false); reject(wrongSource);
        assertThrows(IllegalArgumentException.class, () -> RawCashCodec.validateMonthlyFlow(bytes(wrongSha)));
        ObjectNode omitted = cash("producer-json.json");
        omitted.remove(List.of("monthly_income_semantics", "player_monthly_gross_income", "player_monthly_total_expenses"));
        assertThrows(IllegalArgumentException.class, () -> RawCashCodec.validateMonthlyFlow(bytes(omitted)));
    }

    @Test void nativeFrameAndMilitaryOwnershipBindingsRemainStrict() throws Exception {
        ObjectNode raw = cash("producer-json.json");
        for (String field : List.of("native_revision", "date_raw")) {
            ObjectNode wrong = snapshot(raw); wrong.put(field, 1);
            assertThrows(IllegalArgumentException.class, () -> RawCashCodec.normalize(bytes(raw), bytes(wrong)));
        }
        ObjectNode wrongActor = snapshot(raw); ((ObjectNode) wrongActor.get("played_character")).put("character_id", 7);
        assertThrows(IllegalArgumentException.class, () -> RawCashCodec.normalize(bytes(raw), bytes(wrongActor)));
        ObjectNode wrongHello = snapshot(raw); ((ObjectNode) wrongHello.get("diagnostics").get("hello")).put("expected_ck3_sha256", "0".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> RawCashCodec.normalize(bytes(raw), bytes(wrongHello)));
        for (String row : List.of("current", "all_raised")) {
            ObjectNode wrongOwner = cash("producer-json.json");
            ((ObjectNode) wrongOwner.get("military_expenses").get(row)).put("owner_character_id", 7); reject(wrongOwner);
        }
    }

    @Test void historicalThreeAndFourKeepTheirOriginalPositiveActorAndExactBuildRules() throws Exception {
        for (var version : Map.of("1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
                "1.20.0.4", ExactCk3Build.CK3_12004.executableSha256()).entrySet()) {
            ObjectNode raw = cash("producer-json.json"); actor(raw, 29829);
            raw.put("game_version", version.getKey()); raw.put("executable_sha256", version.getValue());
            ((ObjectNode) raw.get("monthly_income_semantics")).put("version", "ck3-" + version.getKey() + "-native-income-minus-total-expenses-v2");
            RawCashCodec.validateMonthlySourceContract(bytes(raw));
            assertEquals(29829, RawCashCodec.normalize(bytes(raw), bytes(snapshot(raw))).frame().playedCharacterId());
            assertEquals(BigInteger.valueOf(29829), ConstructionEconomyCodec.decodeCash(bytes(raw)).frame().actor().orElseThrow());
            actor(raw, -2130706431); reject(raw);
        }
    }

    private static void reject(ObjectNode raw) {
        assertThrows(IllegalArgumentException.class, () -> RawCashCodec.validateMonthlySourceContract(bytes(raw)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyCodec.decodeCash(bytes(raw)));
    }
    private static ObjectNode cash(String name) throws Exception {
        try (var input = FlorinCashCppReceiverTest.class.getResourceAsStream("/cash1210/" + name)) {
            if (input == null) throw new IOException("actual C++ packet resource absent");
            byte[] bytes = input.readNBytes(16385);
            assertTrue(bytes.length > 0 && bytes.length <= 16384);
            assertEquals(PACKETS.get(name), java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)));
            var packet = StrictJson.parse(bytes);
            assertEquals("query-war-cash-current-resources-v1", packet.get("step").textValue());
            assertTrue(packet.get("accepted").booleanValue());
            return (ObjectNode) packet.get("war_cash_current_resources");
        }
    }
    private static void actor(ObjectNode raw, int actor) {
        raw.put("played_character_id", actor);
        for (String row : List.of("current", "all_raised")) {
            var military = (ObjectNode) raw.get("military_expenses").get(row);
            military.put("owner_character_id", actor); military.put("resource_id", Integer.toString(actor));
        }
    }
    private static ObjectNode snapshot(ObjectNode cash) {
        ObjectNode snapshot = StrictJson.object();
        snapshot.set("native_revision", cash.get("snapshot_revision")); snapshot.set("date_raw", cash.get("date_raw"));
        snapshot.put("paused", true); snapshot.put("map_ready", true);
        snapshot.putObject("played_character").set("character_id", cash.get("played_character_id"));
        var hello = snapshot.putObject("diagnostics").putObject("hello");
        hello.set("expected_ck3_version", cash.get("game_version")); hello.set("expected_ck3_sha256", cash.get("executable_sha256"));
        return snapshot;
    }
    private static byte[] bytes(JsonNode value) { return StrictJson.canonical(value); }
}
