package org.xar.ck3.markets.acceptance;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.MapperFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.HashSet;
import org.xar.ck3.markets.acceptance.AcceptanceContracts.Content;
import org.xar.ck3.markets.acceptance.AcceptanceContracts.Manifest;
import org.xar.ck3.markets.acceptance.AcceptanceContracts.Pin;
import org.xar.ck3.markets.acceptance.AcceptanceContracts.Request;

/** Emits the shared prebuilt-fixture contract. Owns no host, engine identity or business dispatch. */
public final class FixtureEmitter {
    private FixtureEmitter() { }
    static final JsonMapper JSON = JsonMapper.builder(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build()).disable(MapperFeature.ALLOW_COERCION_OF_SCALARS)
            .disable(DeserializationFeature.ACCEPT_FLOAT_AS_INT).enable(DeserializationFeature.FAIL_ON_NULL_FOR_PRIMITIVES)
            .enable(DeserializationFeature.FAIL_ON_NUMBERS_FOR_ENUMS).build();
    private static final String SOURCE = "mod_financial_markets/tools/src/main/java/org/xar/ck3/markets/acceptance/";
    private static final List<String> PRODUCERS = List.of("AcceptanceContracts.java", "ObservationScripts.java", "FixtureEmitter.java", "AcceptanceCommand.java", "FollowupContracts.java", "FollowupObservationScripts.java");

    public static AcceptanceContracts.Emission emit(Path repository, Path output, String machineId, Request request) throws IOException {
        return emit(repository, output, machineId, new FollowupContracts.LegacyInput(request));
    }

    public static AcceptanceContracts.Emission emit(Path repository, Path output, String machineId, FollowupContracts.Input input) throws IOException {
        java.util.Objects.requireNonNull(input, "fixture input");
        AcceptanceContracts.require(machineId != null && machineId.matches("[A-Za-z0-9][A-Za-z0-9_-]{1,99}"), "explicit machine identity required");
        Path repo = repository.toRealPath();
        Path destination = output.toAbsolutePath().normalize();
        Path manifestPath = Path.of(destination + ".fixture.json");
        AcceptanceContracts.require(!destination.startsWith(repo) && !repo.startsWith(destination), "fixture output must remain outside repository");
        AcceptanceContracts.require(!Files.exists(destination, LinkOption.NOFOLLOW_LINKS) && !Files.exists(manifestPath, LinkOption.NOFOLLOW_LINKS), "unused fixture and manifest paths required");
        Path parent = destination.getParent();
        AcceptanceContracts.require(parent != null && Files.isDirectory(parent), "existing external output parent required");
        AcceptanceContracts.require(!destination.getFileName().toString().equals(".") && !parent.toRealPath().startsWith(repo), "output parent resolves inside repository");
        List<Pin> producerPins = new ArrayList<>();
        for (String source : PRODUCERS) {
            Path actual = repo.resolve(SOURCE).resolve(source).toRealPath();
            byte[] bytes = Files.readAllBytes(actual);
            try (var packaged = FixtureEmitter.class.getResourceAsStream("/producer-source/org/xar/ck3/markets/acceptance/" + source)) {
                if (packaged == null || !Arrays.equals(bytes, packaged.readAllBytes())) throw new IOException("loaded producer source differs: " + source);
            }
            producerPins.add(pin(actual));
        }
        Map<String, byte[]> payloads;
        byte[] requestBytes;
        String caseId;
        List<String> markers;
        if (input instanceof FollowupContracts.LegacyInput legacy) {
            payloads = new LinkedHashMap<>(ObservationScripts.render(legacy.request()));
            requestBytes = JSON.writeValueAsBytes(legacy.request());
            caseId = "core";
            markers = ObservationScripts.MARKERS;
        } else if (input instanceof FollowupContracts.Request followup) {
            payloads = new LinkedHashMap<>(FollowupObservationScripts.render(followup));
            requestBytes = JSON.writeValueAsBytes(followup);
            caseId = followup.caseId().wire();
            markers = followup.markers();
        } else throw new IllegalArgumentException("unsupported fixture input");
        payloads.put("_xfma_request.json", requestBytes);
        Map<String, Content> contents = new LinkedHashMap<>();
        Files.createDirectory(destination);
        for (var payload : payloads.entrySet()) {
            Path target = destination.resolve(payload.getKey()); Files.createDirectories(target.getParent());
            Files.write(target, payload.getValue(), StandardOpenOption.CREATE_NEW);
            contents.put(payload.getKey(), new Content(payload.getValue().length, hash(payload.getValue())));
        }
        Manifest manifest = new Manifest("ck3-mod-acceptance-prebuilt-fixture-v1", "financial-markets", caseId, machineId,
                Instant.now().toString(), destination.toString(), producerPins, contents,
                new AcceptanceContracts.Receipt(markers, Map.of(), false));
        Files.write(manifestPath, JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(manifest), StandardOpenOption.CREATE_NEW);
        return new AcceptanceContracts.Emission(destination.toString(), pin(manifestPath), false, "NOT_RUN");
    }

    public static Request readRequest(Path path) throws IOException {
        var node = JSON.readTree(Files.readAllBytes(path));
        return readCore(node);
    }

    public static FollowupContracts.Input readInput(Path path) throws IOException {
        var node = JSON.readTree(Files.readAllBytes(path));
        if (node == null || !node.isObject()) throw new IOException("fixture input object required");
        integral(node, "schemaVersion");
        int schema = node.get("schemaVersion").intValue();
        if (schema == 1) return new FollowupContracts.LegacyInput(readCore(node));
        if (schema != 2) throw new IOException("unsupported fixture schemaVersion");
        closed(node, "schemaVersion", "caseId", "observationEpoch", "actor", "targets", "coldBaseline", "scaleTier");
        integral(node, "observationEpoch"); textual(node, "caseId", false); textual(node, "scaleTier", true);
        var actor = node.get("actor");
        closed(actor, "mode", "historyId"); textual(actor, "mode", false); textual(actor, "historyId", true);
        var targets = node.get("targets");
        closed(targets, "accountId", "coinId", "contractId", "positionId", "debtId", "newsId", "indexId");
        for (String field : List.of("accountId", "coinId", "contractId", "positionId", "debtId", "newsId", "indexId")) textual(targets, field, !field.equals("accountId"));
        var baseline = node.get("coldBaseline");
        if (!baseline.isNull()) {
            closed(baseline, "day", "account", "coin", "position", "debt"); integral(baseline, "day");
            var account = baseline.get("account");
            closed(account, "freeCents", "reservedCents", "systemAccount", "inheritanceState", "frozen");
            for (String field : List.of("freeCents", "reservedCents", "systemAccount", "inheritanceState", "frozen")) integral(account, field);
            var coin = baseline.get("coin");
            if (!coin.isNull()) {
                closed(coin, "supplyUnits", "listingState", "priceVersion");
                for (String field : List.of("supplyUnits", "listingState", "priceVersion")) integral(coin, field);
            }
            var position = baseline.get("position");
            if (!position.isNull()) {
                closed(position, "lots", "markCents", "status", "createdDay", "settledDay", "longAccountId", "shortAccountId", "longReservationId", "shortReservationId", "longRemainingCents", "shortRemainingCents");
                for (String field : List.of("lots", "markCents", "status", "createdDay", "settledDay", "longReservationId", "shortReservationId", "longRemainingCents", "shortRemainingCents")) integral(position, field);
                textual(position, "longAccountId", false); textual(position, "shortAccountId", false);
            }
            var debt = baseline.get("debt");
            if (!debt.isNull()) {
                closed(debt, "originalCents", "outstandingCents", "winnerUnpaidCents", "fundRecourseCents", "fundPaidCents", "repaidCents", "writtenOffCents", "sourceDay", "sourceKind", "dueDay", "debtorAccountId", "creditorAccountId");
                for (String field : List.of("originalCents", "outstandingCents", "winnerUnpaidCents", "fundRecourseCents", "fundPaidCents", "repaidCents", "writtenOffCents", "sourceDay", "sourceKind", "dueDay")) integral(debt, field);
                textual(debt, "debtorAccountId", false); textual(debt, "creditorAccountId", false);
            }
        }
        return JSON.treeToValue(node, FollowupContracts.Request.class);
    }

    private static Request readCore(JsonNode node) throws IOException {
        if (node == null || !node.isObject() || node.size() != 2 || !node.has("schemaVersion") || !node.has("actorHistoryId")
                || !node.get("schemaVersion").isIntegralNumber() || !node.get("schemaVersion").canConvertToInt()
                || !node.get("actorHistoryId").isTextual()) throw new IOException("strict fixture integer version and textual history key required");
        return JSON.treeToValue(node, Request.class);
    }
    private static void closed(JsonNode node, String... expected) throws IOException {
        if (node == null || !node.isObject()) throw new IOException("fixture object required");
        Set<String> actual = new HashSet<>(); node.fieldNames().forEachRemaining(actual::add);
        if (!actual.equals(Set.of(expected))) throw new IOException("unknown or missing fixture fields");
    }
    private static void integral(JsonNode node, String field) throws IOException {
        if (!node.has(field) || !node.get(field).isIntegralNumber() || !node.get(field).canConvertToLong()) throw new IOException("strict fixture integer required: " + field);
        if ((field.equals("schemaVersion") || field.equals("observationEpoch")) && !node.get(field).canConvertToInt()) throw new IOException("fixture integer exceeds int range");
    }
    private static void textual(JsonNode node, String field, boolean nullable) throws IOException {
        if (!node.has(field) || !(node.get(field).isTextual() || nullable && node.get(field).isNull())) throw new IOException("strict fixture text required: " + field);
    }
    public static Pin pin(Path path) throws IOException {
        Path actual = path.toRealPath(); byte[] bytes = Files.readAllBytes(actual);
        return new Pin(actual.toString(), bytes.length, hash(bytes));
    }
    private static String hash(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
}
