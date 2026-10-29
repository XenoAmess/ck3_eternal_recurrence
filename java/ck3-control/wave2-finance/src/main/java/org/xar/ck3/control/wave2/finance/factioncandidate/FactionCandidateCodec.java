package org.xar.ck3.control.wave2.finance.factioncandidate;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.DecimalNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.finance.factiongift.FactionGiftChoice;
import org.xar.ck3.control.finance.factiongift.FactionGiftPolicy;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;

import static org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy.*;

/** Closed operation envelopes around declared projections of extensible SDK documents. */
public final class FactionCandidateCodec {
    public static final int MAX_BYTES = 1_048_576;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(64)
                    .maxNumberLength(4300).maxStringLength(65_536).build()).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);

    private FactionCandidateCodec() { }

    /** Parses a declared root projection only; it grants no same-frame selection qualification. */
    public static RootProjection decodeRootProjection(byte[] bytes) {
        JsonNode root = parse(bytes);
        if (!root.isObject()) throw invalid("root must be object");
        return projectRoot(root);
    }

    public static RootSearch decodeRootSearch(byte[] bytes) {
        JsonNode request = parse(bytes);
        exact(request, Set.of("snapshot", "history"));
        JsonNode snapshot = request.get("snapshot");
        Optional<Frame> snapshotFrame = snapshotFrame(snapshot);
        JsonNode actor = snapshot.isObject() ? snapshot.get("played_character") : null;
        boolean qualified = snapshot.isObject() && trueToken(snapshot.get("paused"))
                && trueToken(snapshot.get("map_ready")) && actor != null && actor.isObject()
                && trueToken(actor.get("alive"));
        if (!qualified || snapshotFrame.isEmpty()) return new RootSearch(Optional.empty(), List.of());
        JsonNode history = request.get("history");
        if (!history.isArray() || history.size() > MAX_HISTORY) throw invalid("history must be bounded array");
        List<RootHistory> histories = new ArrayList<>();
        for (JsonNode row : history) {
            if (!row.isObject()) throw invalid("history row must be object");
            JsonNode result = row.get("result");
            JsonNode context = result != null && result.isObject() ? result.get("campaign_root_context") : null;
            if (!textIs(row.get("command"), ROOT_STEP) || !trueToken(row.get("ok"))
                    || context == null || !context.isObject()) continue;
            histories.add(new RootHistory(textIs(result.get("status"), "available"), projectRoot(context)));
        }
        return new RootSearch(snapshotFrame, histories);
    }

    public static CandidateInput decodeCandidateInput(byte[] bytes) {
        JsonNode request = parse(bytes);
        exact(request, Set.of("snapshot", "root", "private_result", "minimum_gold_reserve_raw"));
        JsonNode root = request.get("root");
        if (!root.isObject()) throw invalid("root must be object");
        return new CandidateInput(snapshotFrame(request.get("snapshot")), projectRoot(root),
                projectPreview(request.get("private_result")), integer(request.get("minimum_gold_reserve_raw"), false));
    }

    /** Application entry shared by existing-driver consumers; all four wire names stay centralized. */
    public static CandidateResult evaluatePrivateCandidate(byte[] snapshotJson, RootProjection root,
                                                            byte[] privateResultJson, BigInteger minimumGoldReserveRaw) {
        java.util.Objects.requireNonNull(root, "root");
        java.util.Objects.requireNonNull(minimumGoldReserveRaw, "minimumGoldReserveRaw");
        ObjectNode request = JSON.createObjectNode();
        request.set("snapshot", parse(snapshotJson));
        request.set("root", parse(root.original().json()));
        request.set("private_result", parse(privateResultJson));
        request.put("minimum_gold_reserve_raw", minimumGoldReserveRaw);
        return choosePrivateCandidate(decodeCandidateInput(encodeTree(request)), existingJavaGiftDecision());
    }

    public static byte[] encodeRootView(RootView view) {
        ObjectNode result = JSON.createObjectNode();
        result.put("status", view.status().wire());
        if (view.root().isEmpty()) result.putNull("root");
        else result.set("root", parse(view.root().get().original().json()));
        return encodeTree(result);
    }

    public static byte[] encodeCandidateResult(CandidateResult candidate) {
        ObjectNode result = JSON.createObjectNode();
        if (candidate instanceof Rejected rejected) {
            result.put("status", rejected.reason() == RejectionReason.NO_DIRECT_LANDED_MEMBER ? "no_legal_candidate" : "unavailable");
            result.put("reason", rejected.reason().wire());
        } else {
            Evaluated evaluated = (Evaluated) candidate;
            FactionGiftChoice choice = evaluated.choice();
            result.put("status", choice.status().wire());
            result.put("reason", choice.reason().wire());
            result.set("observation", parse(evaluated.observation().original().json()));
            result.put("candidate_source", "exact_full_targeting_vector_native_selected_one_direct_member");
            result.put("public_capability_advertised", false);
            result.put("gift_submission_enabled", false);
            if (choice instanceof FactionGiftChoice.Selected) {
                ObjectNode selected = (ObjectNode) parse(FactionGiftPolicy.encode(choice));
                selected.remove("status");
                selected.remove("reason");
                selected.put("minimum_gold_reserve_raw", evaluated.minimumGoldReserveRaw().orElseThrow());
                result.set("choice", selected);
            }
        }
        return encodeTree(result);
    }

    /** Application-side implementation; domain depends on the port, not this JSON adapter. */
    public static GiftDecisionPort existingJavaGiftDecision() {
        return (observation, minimumGoldReserveRaw) -> {
            ObjectNode request = JSON.createObjectNode();
            request.putArray("observations").add(parse(observation.json()));
            request.put("complete_native_enumeration", true);
            request.put("minimum_gold_reserve_raw", minimumGoldReserveRaw);
            return FactionGiftPolicy.choose(encodeTree(request));
        };
    }

    private static RootProjection projectRoot(JsonNode context) {
        Optional<String> government = context.path("government").path("key").isTextual()
                ? Optional.of(context.path("government").path("key").textValue()) : Optional.empty();
        return new RootProjection(document(context), frame(context, "snapshot_revision", "date_raw", "player_character_id"),
                textIs(context.get("status"), "available"), trueToken(context.get("player_character_alive")),
                government, integer(context.get("player_targeting_faction_count"), false),
                idVector(context.get("direct_landed_vassal_character_ids")));
    }

    private static PrivatePreview projectPreview(JsonNode result) {
        if (!result.isObject()) throw invalid("private_result must be object");
        boolean envelope = textIs(result.get("step"), PRIVATE_STEP) && trueToken(result.get("accepted"))
                && trueToken(result.get("private_build")) && falseToken(result.get("advertised"));
        PreviewStatus status = textIs(result.get("status"), "preview_ready") ? PreviewStatus.PREVIEW_READY
                : textIs(result.get("status"), "no_legal_candidate") ? PreviewStatus.NO_LEGAL_CANDIDATE
                : textIs(result.get("status"), "no_eligible_direct_vassal") ? PreviewStatus.NO_ELIGIBLE_DIRECT_VASSAL : PreviewStatus.OTHER;
        JsonNode nativeResult = result.get("native");
        if (nativeResult == null || !nativeResult.isObject()) {
            return new PrivatePreview(envelope, status, false, false, Optional.empty(), Optional.empty(), Optional.empty());
        }
        Optional<BigInteger> flags = integer(nativeResult.get("failure_flags"), false);
        boolean ready = flags.filter(BigInteger.ZERO::equals).isPresent() && textIs(nativeResult.get("completion"), "preview_ready");
        JsonNode observation = nativeResult.get("observation");
        Optional<Observation> projected = observation == null || !observation.isObject() ? Optional.empty()
                : Optional.of(new Observation(document(observation),
                frame(observation, "snapshot_revision", "observed_date_raw", "player_character_id"),
                integer(observation.get("recipient_character_id"), true),
                integer(observation.get("queried_source_faction_id"), true)));
        return new PrivatePreview(envelope, status, true, ready,
                integer(nativeResult.get("source_faction_id"), true),
                integer(nativeResult.get("recipient_character_id"), true), projected);
    }

    private static Optional<Frame> snapshotFrame(JsonNode snapshot) {
        if (snapshot == null || !snapshot.isObject()) return Optional.empty();
        JsonNode actor = snapshot.get("played_character");
        if (actor == null || !actor.isObject()) return Optional.empty();
        Optional<BigInteger> revision = integer(snapshot.get("native_revision"), true);
        Optional<BigInteger> date = integer(snapshot.get("date_raw"), false);
        Optional<BigInteger> player = integer(actor.get("character_id"), true);
        if (revision.isEmpty() || date.isEmpty() || player.isEmpty()) return Optional.empty();
        return Optional.of(new Frame(revision.get(), date.get(), player.get()));
    }

    private static Optional<Frame> frame(JsonNode value, String revisionField, String dateField, String playerField) {
        Optional<BigInteger> revision = integer(value.get(revisionField), true);
        Optional<BigInteger> date = integer(value.get(dateField), false);
        Optional<BigInteger> player = integer(value.get(playerField), true);
        if (revision.isEmpty() || date.isEmpty() || player.isEmpty()) return Optional.empty();
        return Optional.of(new Frame(revision.get(), date.get(), player.get()));
    }

    private static IdVector idVector(JsonNode value) {
        if (value == null || !value.isArray()) return new IdVector(Optional.empty());
        if (value.size() > MAX_IDS) throw invalid("direct vassal vector limit");
        List<BigInteger> ids = new ArrayList<>();
        for (JsonNode node : value) {
            Optional<BigInteger> id = integer(node, true);
            if (id.isEmpty()) return new IdVector(Optional.empty());
            ids.add(id.get());
        }
        return new IdVector(Optional.of(ids));
    }

    private static Optional<BigInteger> integer(JsonNode value, boolean positive) {
        if (value == null || !value.isIntegralNumber()) return Optional.empty();
        BigInteger number = value.bigIntegerValue();
        return positive && number.signum() <= 0 ? Optional.empty() : Optional.of(number);
    }

    private static boolean trueToken(JsonNode node) { return node != null && node.isBoolean() && node.booleanValue(); }
    private static boolean falseToken(JsonNode node) { return node != null && node.isBoolean() && !node.booleanValue(); }
    private static boolean textIs(JsonNode node, String expected) { return node != null && node.isTextual() && expected.equals(node.textValue()); }
    private static JsonObjectDocument document(JsonNode node) { return new JsonObjectDocument(encodeTree(node)); }

    private static void exact(JsonNode node, Set<String> fields) {
        if (!node.isObject() || node.size() != fields.size()) throw invalid("operation envelope fields");
        for (String field : fields) if (!node.has(field)) throw invalid("operation missing " + field);
    }

    private static JsonNode parse(byte[] bytes) {
        if (bytes == null || bytes.length == 0 || bytes.length > MAX_BYTES) throw invalid("JSON byte limit");
        try {
            String utf8 = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            JsonNode node = JSON.readTree(utf8);
            if (node == null) throw invalid("empty JSON");
            return node;
        } catch (IOException failure) { throw new IllegalArgumentException("invalid faction candidate JSON", failure); }
    }

    private static byte[] encodeTree(JsonNode node) {
        try {
            byte[] result = JSON.writeValueAsBytes(preserveFloatDomain(node));
            if (result.length > MAX_BYTES) throw invalid("encoded JSON byte limit");
            return result;
        }
        catch (IOException failure) { throw new IllegalStateException("candidate encoding failed", failure); }
    }

    /** Preserve opaque decimal precision and floating token identity across downstream validation. */
    private static JsonNode preserveFloatDomain(JsonNode node) {
        if (node.isObject()) {
            ObjectNode copy = JSON.createObjectNode();
            node.properties().forEach(entry -> copy.set(entry.getKey(), preserveFloatDomain(entry.getValue())));
            return copy;
        }
        if (node.isArray()) {
            ArrayNode copy = JSON.createArrayNode();
            node.forEach(value -> copy.add(preserveFloatDomain(value)));
            return copy;
        }
        if (node.isFloatingPointNumber()) {
            var decimal = node.decimalValue();
            return DecimalNode.valueOf(decimal.scale() == 0 ? decimal.setScale(1) : decimal);
        }
        return node;
    }

    private static IllegalArgumentException invalid(String message) { return new IllegalArgumentException(message); }
}
