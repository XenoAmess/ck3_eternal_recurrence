package org.xar.ck3.markets.acceptance;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.MapperFeature;
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
import org.xar.ck3.markets.acceptance.AcceptanceContracts.Content;
import org.xar.ck3.markets.acceptance.AcceptanceContracts.Manifest;
import org.xar.ck3.markets.acceptance.AcceptanceContracts.Pin;
import org.xar.ck3.markets.acceptance.AcceptanceContracts.Request;

/** Emits the shared prebuilt-fixture contract. Owns no host, engine identity or business dispatch. */
public final class FixtureEmitter {
    private FixtureEmitter() { }
    static final JsonMapper JSON = JsonMapper.builder(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build()).disable(MapperFeature.ALLOW_COERCION_OF_SCALARS)
            .disable(DeserializationFeature.ACCEPT_FLOAT_AS_INT).enable(DeserializationFeature.FAIL_ON_NULL_FOR_PRIMITIVES).build();
    private static final String SOURCE = "mod_financial_markets/tools/src/main/java/org/xar/ck3/markets/acceptance/";
    private static final List<String> PRODUCERS = List.of("AcceptanceContracts.java", "ObservationScripts.java", "FixtureEmitter.java", "AcceptanceCommand.java");

    public static AcceptanceContracts.Emission emit(Path repository, Path output, String machineId, Request request) throws IOException {
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
        Map<String, byte[]> payloads = new LinkedHashMap<>(ObservationScripts.render(request));
        payloads.put("_xfma_request.json", JSON.writeValueAsBytes(request));
        Map<String, Content> contents = new LinkedHashMap<>();
        Files.createDirectory(destination);
        for (var payload : payloads.entrySet()) {
            Path target = destination.resolve(payload.getKey()); Files.createDirectories(target.getParent());
            Files.write(target, payload.getValue(), StandardOpenOption.CREATE_NEW);
            contents.put(payload.getKey(), new Content(payload.getValue().length, hash(payload.getValue())));
        }
        Manifest manifest = new Manifest("ck3-mod-acceptance-prebuilt-fixture-v1", "financial-markets", "core", machineId,
                Instant.now().toString(), destination.toString(), producerPins, contents,
                new AcceptanceContracts.Receipt(ObservationScripts.MARKERS, Map.of(), false));
        Files.write(manifestPath, JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(manifest), StandardOpenOption.CREATE_NEW);
        return new AcceptanceContracts.Emission(destination.toString(), pin(manifestPath), false, "NOT_RUN");
    }

    public static Request readRequest(Path path) throws IOException {
        var node = JSON.readTree(Files.readAllBytes(path));
        if (node == null || !node.isObject() || node.size() != 2 || !node.has("schemaVersion") || !node.has("actorHistoryId")
                || !node.get("schemaVersion").isIntegralNumber() || !node.get("schemaVersion").canConvertToInt()
                || !node.get("actorHistoryId").isTextual()) throw new IOException("strict fixture integer version and textual history key required");
        return JSON.treeToValue(node, Request.class);
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
