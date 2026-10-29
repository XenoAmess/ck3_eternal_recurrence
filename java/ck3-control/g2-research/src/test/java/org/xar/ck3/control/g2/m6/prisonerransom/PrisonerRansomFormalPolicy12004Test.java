package org.xar.ck3.control.g2.m6.prisonerransom;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.CollectionRead;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.Frame;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.NoEligibleOffer;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.Reason;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.Selected;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.Unavailable;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.UnavailableWarRetention;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.Catalog;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.Source;

/** Original bytes stay original; every complete multi-query positive is explicitly synthetic. */
public final class PrisonerRansomFormalPolicy12004Test {
    private static final Frame FRAME = new Frame(BigInteger.valueOf(37), BigInteger.valueOf(1014), 53286360, 29829, List.of());
    private static Catalog catalog;
    private static byte[] original;
    private static final long[] IDS = {54235, 56063, 61540, 70766};

    @BeforeAll static void originals() throws IOException {
        JsonNode manifest = StrictJson.parse(resource("fixture-source.json"));
        byte[] stock = resource("00_prison_interactions.txt");
        G2Source source = new G2Source(StrictJson.text(manifest.get("machine_id")), StrictJson.text(manifest.get("observed_at_utc")),
                StrictJson.text(manifest.get("exact_build")), ExactRef.fromJson(manifest.get("stock_ref")));
        catalog = PrisonerVanillaResearch.inspect(stock, new Source(source, PrisonerVanillaResearch.EXE_SHA256));
        original = resource("releasepreview/native12004/gate_true.json");
        assertEquals("694a8a87d141e982ccda9b602d6b6211726fa9f17564f1d8aaffedb9cc560443", PrisonerVanillaResearch.sha256(original));
        System.out.println("PRISONER_FORMAL original_native_fixture=1 complete_multiquote_inputs=SYNTHETIC native_execution=NOT_RUN");
    }

    @Test void originalSingleNativeReadCannotQualifyTheMissingOtherQuoteReads() {
        CollectionRead read = PrisonerRansomFormalPolicy12004.read(original, FRAME, 61540, catalog);
        assertEquals(2, read.selectedOrdinal());
        assertEquals(new Unavailable(Reason.INCOMPLETE_COLLECTION_READS), PrisonerRansomFormalPolicy12004.select(FRAME, List.of(read), List.of()));
        assertEquals(9_000_000, assertInstanceOf(PrisonerVanillaResearch.AvailableQuote.class,
                read.explanation().candidates().get(2).ransomQuote()).quotedGoldRaw());
    }

    @Test void syntheticCompleteQueriesChooseHighestPositiveUnrelatedLandlessOffer() {
        Selected result = chosen(complete());
        assertEquals(61540, result.choice().prisonerCharacterId());
        assertEquals(9_000_000, result.choice().quotedGoldRaw());
        assertEquals(2, result.choice().sourceOrdinal());
    }

    @Test void countyTitleIsExcludedButBaronTitleAndMeasuredNullRemainEligible() {
        List<ObjectNode> wires = complete();
        for (ObjectNode wire : wires) {
            row(wire, 0).put("primary_title_tier_raw", 2);
            row(wire, 1).put("primary_title_tier_raw", 1);
            row(wire, 2).put("primary_title_tier_raw", 2);
        }
        assertEquals(56063, chosen(wires).choice().prisonerCharacterId());
        for (ObjectNode wire : wires) row(wire, 1).put("primary_title_tier_raw", 2);
        assertInstanceOf(NoEligibleOffer.class, select(wires, FRAME, List.of()));
        for (ObjectNode wire : wires) row(wire, 1).remove("primary_title_tier_raw");
        assertThrows(IllegalArgumentException.class, () -> reads(wires, FRAME));
    }

    @Test void sameDynastyAndPlayerChildNeverEnterTheFormalChoice() {
        List<ObjectNode> wires = complete();
        for (ObjectNode wire : wires) {
            row(wire, 2).put("is_child_of_played_character", true);
            row(wire, 0).put("house_id", 174).put("dynasty_id", 174).put("same_house", true).put("same_dynasty", true);
        }
        assertEquals(56063, chosen(wires).choice().prisonerCharacterId());
    }

    @Test void equalAmountsUseLowerFullPrisonerIdAndKeepSourceOrdinal() {
        List<ObjectNode> wires = complete(); quote(wires.get(0), 0).put("quoted_gold_raw", 9_000_000);
        Selected result = chosen(wires);
        assertEquals(54235, result.choice().prisonerCharacterId()); assertEquals(0, result.choice().sourceOrdinal());
    }

    @Test void recipientRefusalIsIndependentFromNativeCanSendAndUnrelatedReleaseGate() {
        List<ObjectNode> wires = complete(); quote(wires.get(2), 2).put("recipient_answer_status_raw", 2).put("would_accept_now", false);
        assertEquals(54235, chosen(wires).choice().prisonerCharacterId());
        quote(wires.get(0), 0).put("can_send", false);
        assertThrows(IllegalArgumentException.class, () -> chosen(wires));
    }

    @Test void currentGoldRetainsAcceptanceTimeAmountAcrossPolicyAndSerialization() {
        List<ObjectNode> wires = complete(); quote(wires.get(2), 2).put("selected_option", "current_gold").put("amount_is_acceptance_time_quote", true);
        Selected selected = chosen(wires);
        assertEquals(PrisonerVanillaResearch.Option.CURRENT_GOLD, selected.choice().option());
        assertEquals(true, selected.choice().amountIsAcceptanceTimeQuote());
        JsonNode json = PrisonerRansomEndpoint12004.toJson(selected);
        assertEquals("9000000", json.get("choice").get("quoted_gold_raw").textValue());
        assertEquals("1926335", json.get("choice").get("proof_epoch").textValue());
        assertFalse(json.get("material_result").booleanValue());
        quote(wires.get(2), 2).put("amount_is_acceptance_time_quote", false);
        assertThrows(IllegalArgumentException.class, () -> chosen(wires));
    }

    @Test void syntheticNinthBitDiagnosticIsUnavailableAndCannotBecomeAnOffer() {
        for (int mask : List.of(256, 511)) {
            List<ObjectNode> wires = complete();
            ObjectNode diagnostic = unavailable("option_mask_unexpected").put("requested_option_index", 0).put("observed_option_mask_bits", mask);
            row(wires.get(2), 2).set("ransom_quote_preview", diagnostic);
            assertEquals(54235, chosen(wires).choice().prisonerCharacterId());
        }
        List<ObjectNode> wires = complete();
        row(wires.get(2), 2).set("ransom_quote_preview", unavailable("option_mask_unexpected").put("requested_option_index", 0).put("observed_option_mask_bits", 512));
        assertThrows(IllegalArgumentException.class, () -> chosen(wires));
    }

    @Test void nativeWarRetentionExcludesBothCandidateListsAndActualPairRows() {
        Frame warFrame = warFrame(); ObjectNode war = war();
        object(war, "war_prisoner_release_pairs_v1").withArray("release_pairs").addObject().put("jailer_character_id", 30470)
                .put("prisoner_character_id", 61540).put("reason", "opposite_primary_or_first_three_successors");
        object(war, "war_prisoner_release_pairs_v1").withArray("attacker_release_candidate_ids").add(54235).add(61540);
        var retained = PrisonerRansomFormalPolicy12004.readWar(bytes(war), warFrame, 16777231);
        assertEquals(56063, assertInstanceOf(Selected.class, select(complete(), warFrame, List.of(retained))).choice().prisonerCharacterId());
    }

    @Test void missingCoverageUnsupportedWarOrWrongFrameRemainTypedUnavailable() {
        for (String field : List.of("same_frame_stable", "full_participant_scan", "primary_and_first_three_successors_scanned")) {
            ObjectNode wire = war(); object(wire, "war_prisoner_release_pairs_v1").put(field, false);
            var unavailable = PrisonerRansomFormalPolicy12004.readWar(bytes(wire), warFrame(), 16777231);
            assertInstanceOf(UnavailableWarRetention.class, unavailable);
            assertEquals(new Unavailable(Reason.WAR_RETENTION_UNAVAILABLE), select(complete(), warFrame(), List.of(unavailable)));
        }
        ObjectNode wire = war(); object(wire, "war_prisoner_release_pairs_v1").put("active_casus_belli_key", "fp3_free_house_member_cb");
        assertInstanceOf(UnavailableWarRetention.class, PrisonerRansomFormalPolicy12004.readWar(bytes(wire), warFrame(), 16777231));
        wire = war(); wire.put("snapshot_revision", true);
        assertInstanceOf(UnavailableWarRetention.class, PrisonerRansomFormalPolicy12004.readWar(bytes(wire), warFrame(), 16777231));
        assertEquals(new Unavailable(Reason.WAR_RETENTION_UNAVAILABLE), select(complete(), warFrame(), List.of()));
    }

    @Test void collectionOrderAndFullIdentityDriftFailBeforeChoosing() {
        List<ObjectNode> wires = complete();
        row(wires.get(1), 0).put("prisoner_character_id", 80001);
        assertEquals(new Unavailable(Reason.COLLECTION_IDENTITY_DRIFT), select(wires, FRAME, List.of()));
        List<CollectionRead> reads = reads(complete(), FRAME);
        assertEquals(new Unavailable(Reason.COLLECTION_IDENTITY_DRIFT), PrisonerRansomFormalPolicy12004.select(FRAME,
                List.of(reads.get(1), reads.get(0), reads.get(2), reads.get(3)), List.of()));
    }

    @Test void finalRefreshReturnsFreshOriginalProofButRejectsEveryChangedOfferField() {
        List<ObjectNode> wires = complete(); List<CollectionRead> reads = reads(wires, FRAME); Selected planned = chosen(wires);
        ObjectNode latest = wires.get(2).deepCopy(); latest.put("query_sequence", 77);
        Selected refreshed = assertInstanceOf(Selected.class, PrisonerRansomFormalPolicy12004.refresh(planned, reads,
                PrisonerRansomFormalPolicy12004.read(bytes(latest), FRAME, 61540, catalog), List.of()));
        assertNotEquals(planned.choice().collectionSha256(), refreshed.choice().collectionSha256());
        for (String field : List.of("quoted_gold_raw", "payer_character_id", "selected_option")) {
            latest = wires.get(2).deepCopy(); ObjectNode quote = quote(latest, 2);
            if (field.equals("selected_option")) quote.put(field, "current_gold").put("amount_is_acceptance_time_quote", true);
            else quote.put(field, field.equals("quoted_gold_raw") ? 8_999_999 : 73001);
            assertEquals(new Unavailable(Reason.QUOTE_CHANGED_BEFORE_SUBMIT), PrisonerRansomFormalPolicy12004.refresh(planned, reads,
                    PrisonerRansomFormalPolicy12004.read(bytes(latest), FRAME, 61540, catalog), List.of()));
        }
    }

    @Test void endpointPreservesOriginalBytesAndExactUint64DecimalRevisionStrings() {
        ObjectNode request = request(complete());
        var decoded = PrisonerRansomEndpoint12004.decode(bytes(request));
        assertArrayEquals(bytes(complete().getFirst()), decoded.collections().getFirst().original());
        byte[] raw = PrisonerRansomEndpoint12004.evaluate(bytes(request), Optional.of(catalog));
        assertEquals("selected_read_only", StrictJson.parse(raw).get("status").textValue());
        assertFalse(StrictJson.parse(raw).get("quote_refresh_match").booleanValue());
        assertArrayEquals(raw, StrictJson.canonical(StrictJson.parse(raw)));
        ObjectNode refreshedRequest = request.deepCopy(); refreshedRequest.set("refresh", request.get("collections").get(2).deepCopy());
        assertEquals(true, StrictJson.parse(PrisonerRansomEndpoint12004.evaluate(bytes(refreshedRequest), Optional.of(catalog)))
                .get("quote_refresh_match").booleanValue());
        ObjectNode largeOriginal = request(complete()); byte[] boundedOriginal = new byte[60_000];
        ((ObjectNode) largeOriginal.withArray("collections").get(0)).put("original_collection_base64", Base64.getEncoder().encodeToString(boundedOriginal));
        // Explicit 128-KiB original-byte role bypasses generic 32-KiB text validation, without native qualification.
        String largeJson = largeOriginal.toString();
        assertArrayEquals(boundedOriginal, PrisonerRansomEndpoint12004.decode(largeJson.getBytes(java.nio.charset.StandardCharsets.UTF_8))
                .collections().getFirst().original());
        object(request, "frame").put("public_revision", "18446744073709551615");
        assertEquals(StrictJson.UINT64_MAX, PrisonerRansomEndpoint12004.decode(bytes(request)).frame().publicRevision());
        object(request, "frame").put("public_revision", 37);
        assertThrows(IllegalArgumentException.class, () -> PrisonerRansomEndpoint12004.decode(bytes(request)));
    }

    @Test void residentEndpointReportsTheMissingInstalledCatalogProviderWithoutNativeOrActionClaims() {
        JsonNode result = StrictJson.parse(PrisonerRansomEndpoint12004.evaluate(bytes(request(complete())), Optional.empty()));
        assertEquals("unavailable", result.get("status").textValue());
        assertEquals("SOURCE_PROVIDER_UNAVAILABLE", result.get("unavailable_reason").textValue());
        assertFalse(result.get("submission_authority").booleanValue());
        assertFalse(result.get("native_ninth_bit_qualified").booleanValue());
        assertFalse(result.get("current_build_kinship_qualified").booleanValue());
    }

    @Test void boundaryRejectsMissingExtraDuplicateWrongTokenAndNoncanonicalOriginalEncoding() {
        ObjectNode extra = request(complete()); extra.put("extra", true);
        assertThrows(IllegalArgumentException.class, () -> PrisonerRansomEndpoint12004.decode(bytes(extra)));
        ObjectNode missing = request(complete()); missing.remove("refresh");
        assertThrows(IllegalArgumentException.class, () -> PrisonerRansomEndpoint12004.decode(bytes(missing)));
        ObjectNode malformed = request(complete()); object(malformed, "frame").put("native_revision", "01014");
        assertThrows(IllegalArgumentException.class, () -> PrisonerRansomEndpoint12004.decode(bytes(malformed)));
        ObjectNode base64 = request(complete()); ((ObjectNode) base64.withArray("collections").get(0)).put("original_collection_base64", "e30");
        assertThrows(IllegalArgumentException.class, () -> PrisonerRansomEndpoint12004.decode(bytes(base64)));
        assertThrows(IllegalArgumentException.class, () -> PrisonerRansomEndpoint12004.decode("{\"schema\":1,\"schema\":2}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        ObjectNode war = war(); object(war, "war_prisoner_release_pairs_v1").withArray("attacker_release_candidate_ids").add(true);
        assertThrows(IllegalArgumentException.class, () -> PrisonerRansomFormalPolicy12004.readWar(bytes(war), warFrame(), 16777231));
    }

    private static List<ObjectNode> complete() {
        ObjectNode source = (ObjectNode) StrictJson.parse(original); ObjectNode available = quote(source, 2).deepCopy();
        List<ObjectNode> result = new ArrayList<>(); long[] amounts = {5_000_000, 3_000_000, 9_000_000, 10_000_000};
        for (int selected = 0; selected < 4; selected++) {
            ObjectNode wire = source.deepCopy(); wire.put("step", "query-player-prisoner-collection-private-v1" + (selected == 0 ? "" : "-ransom-ordinal-" + selected));
            wire.put("query_sequence", selected + 1);
            for (int index = 0; index < 4; index++) {
                row(wire, index).set("unconditional_release_preview", unavailable("not_evaluated"));
                row(wire, index).set("ransom_quote_preview", unavailable("not_evaluated"));
            }
            row(wire, selected).set("ransom_quote_preview", available.deepCopy().put("prisoner_character_id", IDS[selected])
                    .put("payer_character_id", 73000 + selected).put("quoted_gold_raw", amounts[selected]));
            result.add(wire);
        }
        return result;
    }
    private static ObjectNode request(List<ObjectNode> wires) {
        ObjectNode request = StrictJson.object().put("schema", PrisonerRansomEndpoint12004.REQUEST_SCHEMA);
        request.putObject("frame").put("public_revision", "37").put("native_revision", "1014").put("date_raw", 53286360)
                .put("player_character_id", 29829).put("paused", true).put("map_ready", true).putArray("active_war_ids");
        ArrayNode collections = request.putArray("collections");
        for (int index = 0; index < wires.size(); index++) collections.addObject().put("selected_prisoner_character_id", IDS[index])
                .put("original_collection_base64", Base64.getEncoder().encodeToString(bytes(wires.get(index))));
        request.putArray("war_reads"); request.putNull("refresh"); return request;
    }
    private static ObjectNode unavailable(String reason) {
        return StrictJson.object().put("private_build", true).put("read_only", true).put("advertised", false).put("action_surface_present", false)
                .put("status", "unavailable").put("unavailable_reason", reason);
    }
    private static Frame warFrame() { return new Frame(FRAME.publicRevision(), FRAME.nativeRevision(), FRAME.dateRaw(), FRAME.playerCharacterId(), List.of(16777231L)); }
    private static ObjectNode war() {
        ObjectNode result = StrictJson.object().put("snapshot_revision", 1014).put("step", "query-war-prisoner-release-pairs-v1-16777231")
                .put("accepted", true).put("status", "available").put("read_only", true).put("backend_id", "native-headless").put("query_sequence", 1);
        ObjectNode proof = result.putObject("war_prisoner_release_pairs_v1").put("war_id", 16777231).put("date_raw", 53286360)
                .put("same_frame_stable", true).put("full_participant_scan", true).put("primary_and_first_three_successors_scanned", true)
                .put("active_casus_belli_key", "individual_county_de_jure_cb").put("active_casus_belli_database_index", 4)
                .put("primary_attacker_character_id", 29829).put("primary_defender_character_id", 30470);
        proof.putArray("attacker_participant_ids").add(29829); proof.putArray("defender_participant_ids").add(30470);
        proof.putArray("attacker_release_candidate_ids").add(29829); proof.putArray("defender_release_candidate_ids").add(30470);
        proof.putArray("release_pairs"); return result;
    }
    private static Selected chosen(List<ObjectNode> wires) { return assertInstanceOf(Selected.class, select(wires, FRAME, List.of())); }
    private static PrisonerRansomFormalPolicy12004.Decision select(List<ObjectNode> wires, Frame frame, List<PrisonerRansomFormalPolicy12004.WarRetention> wars) {
        return PrisonerRansomFormalPolicy12004.select(frame, reads(wires, frame), wars);
    }
    private static List<CollectionRead> reads(List<ObjectNode> wires, Frame frame) {
        List<CollectionRead> result = new ArrayList<>();
        for (int index = 0; index < wires.size(); index++) result.add(PrisonerRansomFormalPolicy12004.read(bytes(wires.get(index)), frame, IDS[index], catalog));
        return result;
    }
    private static ObjectNode row(ObjectNode wire, int ordinal) { return (ObjectNode) wire.get("player_prisoner_collection").get("prisoners").get(ordinal); }
    private static ObjectNode object(ObjectNode parent, String field) { return (ObjectNode) parent.get(field); }
    private static ObjectNode quote(ObjectNode wire, int ordinal) { return (ObjectNode) row(wire, ordinal).get("ransom_quote_preview"); }
    private static byte[] bytes(JsonNode value) { return StrictJson.canonical(value, StrictJson.EXPLICIT_MAX_BYTES); }
    private static byte[] resource(String path) throws IOException {
        try (InputStream input = PrisonerRansomFormalPolicy12004Test.class.getResourceAsStream("/prisoner-research/" + path)) {
            if (input == null) throw new IOException("required original fixture missing: " + path);
            return input.readAllBytes();
        }
    }
}
