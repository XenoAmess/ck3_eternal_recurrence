package org.xar.ck3.control.g2.m6.prisonerransom;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.CollectionRead;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.Frame;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.Selected;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.Unavailable;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.WarRetention;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003;

/** Byte-preserving protocol adapter for the existing resident host. No file or native access. */
public final class PrisonerRansomEndpoint12004 {
    public static final String PATH = "/v1/research/prisoner-ransom";
    public static final String REQUEST_SCHEMA = "xar.prisoner-ransom-formal-request/v1";
    public static final String RESULT_SCHEMA = "xar.prisoner-ransom-formal-result/v1";
    public static final int MAX_REQUEST_BYTES = StrictJson.EXPLICIT_MAX_BYTES;
    private PrisonerRansomEndpoint12004() { }

    public record OriginalCollection(long selectedPrisonerId, byte[] original) {
        public OriginalCollection {
            StrictJson.require(selectedPrisonerId > 0 && selectedPrisonerId <= ReleasePreviewValues12003.UINT32_MAX, "selected full ID required");
            original = original.clone();
        }
        @Override public byte[] original() { return original.clone(); }
    }
    public record Request(Frame frame, List<OriginalCollection> collections, List<byte[]> warReads,
                          Optional<OriginalCollection> refresh) {
        public Request {
            Objects.requireNonNull(frame); collections = List.copyOf(collections);
            warReads = warReads.stream().map(row -> row.clone()).toList(); Objects.requireNonNull(refresh);
        }
        @Override public List<byte[]> warReads() { return warReads.stream().map(row -> row.clone()).toList(); }
    }

    public static Request decode(byte[] raw) {
        JsonNode value = StrictJson.parse(raw, MAX_REQUEST_BYTES);
        StrictJson.object(value, Set.of("schema", "frame", "collections", "war_reads", "refresh"));
        StrictJson.require(REQUEST_SCHEMA.equals(StrictJson.text(value.get("schema"))), "formal request schema required");
        JsonNode frame = value.get("frame");
        StrictJson.object(frame, Set.of("public_revision", "native_revision", "date_raw", "player_character_id", "active_war_ids", "paused", "map_ready"));
        StrictJson.trueValue(frame.get("paused")); StrictJson.trueValue(frame.get("map_ready"));
        List<Long> wars = new ArrayList<>();
        JsonNode warIds = frame.get("active_war_ids"); array(warIds, 64);
        for (JsonNode war : warIds) wars.add(StrictJson.integer(war, 1, ReleasePreviewValues12003.UINT32_MAX));
        Frame typedFrame = new Frame(decimal(frame.get("public_revision")), decimal(frame.get("native_revision")),
                (int) StrictJson.integer(frame.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE),
                StrictJson.integer(frame.get("player_character_id"), 1, ReleasePreviewValues12003.UINT32_MAX), wars);
        List<OriginalCollection> collections = new ArrayList<>();
        array(value.get("collections"), 64);
        for (JsonNode collection : value.get("collections")) collections.add(collection(collection));
        List<byte[]> warReads = new ArrayList<>(); array(value.get("war_reads"), 64);
        for (JsonNode war : value.get("war_reads")) warReads.add(original(war));
        JsonNode refresh = value.get("refresh");
        return new Request(typedFrame, collections, warReads, refresh.isNull() ? Optional.empty() : Optional.of(collection(refresh)));
    }

    /** Catalog is server-owned. Missing current-build source is explicitly unavailable. */
    public static byte[] evaluate(byte[] raw, Optional<PrisonerVanillaResearch.Catalog> catalog) {
        Request request = decode(raw); Objects.requireNonNull(catalog);
        PrisonerRansomFormalPolicy12004.Decision decision;
        if (catalog.isEmpty()) {
            decision = new Unavailable(PrisonerRansomFormalPolicy12004.Reason.SOURCE_PROVIDER_UNAVAILABLE);
        } else {
            List<CollectionRead> collections = new ArrayList<>();
            for (OriginalCollection collection : request.collections()) collections.add(PrisonerRansomFormalPolicy12004.read(
                    collection.original(), request.frame(), collection.selectedPrisonerId(), catalog.orElseThrow()));
            List<WarRetention> wars = new ArrayList<>();
            List<byte[]> originalWarReads = request.warReads();
            if (originalWarReads.size() != request.frame().activeWarIds().size()) {
                decision = new Unavailable(PrisonerRansomFormalPolicy12004.Reason.WAR_RETENTION_UNAVAILABLE);
            } else {
                for (int index = 0; index < originalWarReads.size(); index++) wars.add(PrisonerRansomFormalPolicy12004.readWar(
                        originalWarReads.get(index), request.frame(), request.frame().activeWarIds().get(index)));
                decision = PrisonerRansomFormalPolicy12004.select(request.frame(), collections, wars);
                if (request.refresh().isPresent() && decision instanceof Selected selected) {
                    OriginalCollection refresh = request.refresh().orElseThrow();
                    decision = PrisonerRansomFormalPolicy12004.refresh(selected, collections,
                            PrisonerRansomFormalPolicy12004.read(refresh.original(), request.frame(), refresh.selectedPrisonerId(), catalog.orElseThrow()), wars);
                }
            }
        }
        ObjectNode result = toJson(decision);
        result.put("quote_refresh_match", request.refresh().isPresent() && decision instanceof Selected);
        result.put("request_sha256", PrisonerVanillaResearch.sha256(raw));
        result.putObject("frame").put("public_revision", request.frame().publicRevision().toString())
                .put("native_revision", request.frame().nativeRevision().toString()).put("date_raw", request.frame().dateRaw())
                .put("player_character_id", request.frame().playerCharacterId());
        if (catalog.isPresent()) result.put("stock_source_sha256", catalog.orElseThrow().source().provenance().sourceRef().sha256());
        else result.putNull("stock_source_sha256");
        return StrictJson.canonical(result);
    }

    public static ObjectNode toJson(PrisonerRansomFormalPolicy12004.Decision decision) {
        Objects.requireNonNull(decision);
        ObjectNode result = StrictJson.object().put("schema", RESULT_SCHEMA).put("submission_authority", false)
                .put("material_result", false).put("native_ninth_bit_qualified", false).put("current_build_kinship_qualified", false);
        if (decision instanceof Unavailable unavailable) {
            result.put("status", "unavailable").put("unavailable_reason", unavailable.reason().name()).putNull("choice");
        } else if (decision instanceof Selected selected) {
            result.put("status", "selected_read_only").putNull("unavailable_reason");
            var choice = selected.choice();
            result.putObject("choice").put("source_ordinal", choice.sourceOrdinal()).put("prisoner_character_id", choice.prisonerCharacterId())
                    .put("payer_character_id", choice.payerCharacterId()).put("selected_option", choice.option() == PrisonerVanillaResearch.Option.GOLD ? "gold" : "current_gold")
                    .put("quoted_gold_raw", Long.toString(choice.quotedGoldRaw())).put("amount_is_acceptance_time_quote", choice.amountIsAcceptanceTimeQuote())
                    .put("collection_sha256", choice.collectionSha256()).put("proof_epoch", choice.proofEpoch().toString());
        } else {
            result.put("status", "no_eligible_offer").putNull("unavailable_reason").putNull("choice");
        }
        return result;
    }
    private static OriginalCollection collection(JsonNode value) {
        StrictJson.object(value, Set.of("selected_prisoner_character_id", "original_collection_base64"));
        return new OriginalCollection(StrictJson.integer(value.get("selected_prisoner_character_id"), 1, ReleasePreviewValues12003.UINT32_MAX),
                original(value.get("original_collection_base64")));
    }
    private static byte[] original(JsonNode value) {
        StrictJson.require(value != null && value.isTextual(), "base64 original wire string required");
        String encoded = value.textValue();
        StrictJson.require(!encoded.isEmpty() && encoded.length() <= 174_764, "bounded original wire required");
        byte[] bytes;
        try { bytes = Base64.getDecoder().decode(encoded); }
        catch (IllegalArgumentException error) { throw new IllegalArgumentException("canonical base64 original wire required", error); }
        StrictJson.require(bytes.length > 0 && bytes.length <= 131_072
                && Base64.getEncoder().encodeToString(bytes).equals(encoded), "canonical bounded original wire required");
        return bytes;
    }
    private static BigInteger decimal(JsonNode value) {
        String text = StrictJson.text(value);
        StrictJson.require(text.matches("[1-9][0-9]{0,19}"), "canonical uint64 decimal string required");
        BigInteger integer = new BigInteger(text);
        StrictJson.require(integer.compareTo(StrictJson.UINT64_MAX) <= 0, "uint64 revision required");
        return integer;
    }
    private static void array(JsonNode value, int maximum) {
        StrictJson.require(value != null && value.isArray() && value.size() <= maximum, "bounded JSON array required");
    }
}
