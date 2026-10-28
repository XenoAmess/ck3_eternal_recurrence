package org.xar.ck3.rrf.acceptance;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import com.fasterxml.jackson.databind.JsonNode;
import org.xar.ck3.rrf.Contracts.Catalog;
import org.xar.ck3.rrf.Json;
import org.xar.ck3.rrf.ReleaseBuilder;
import org.xar.ck3.rrf.acceptance.FixtureContracts.FileContent;
import org.xar.ck3.rrf.acceptance.FixtureContracts.FilePin;
import org.xar.ck3.rrf.acceptance.FixtureContracts.Manifest;
import org.xar.ck3.rrf.acceptance.FixtureContracts.Request;

/** Reload the closed manifest consumed by public prepare, never a detached request sidecar. */
public final class FrozenFixtureReader {
    private FrozenFixtureReader() { }
    public record BoundRequest(FilePin manifestPin, FilePin requestPin, Request request) { }
    public record PreparedBinding(FilePin inventoryPin, FilePin requestPin, FilePin caseContractPin) { }
    /** Bind to the public prepare output, including its unchanged copied request and exact emitter manifest. */
    public static PreparedBinding readPrepared(FilePin expected, BoundRequest fixture) throws IOException {
        JsonNode inventory = jsonFile(expected);
        if (!text(inventory, "schema").equals("ck3-mod-acceptance-prepared-fixture-v1") || !text(inventory, "runtime_status").equals("NOT_RUN")
                || !text(inventory, "business_acceptance").equals("NOT_ASSESSED")) throw new IOException("actual public fixture preparation inventory required");
        Path declaredProfile = Path.of(text(inventory, "profile_dir"));
        if (!declaredProfile.isAbsolute()) throw new IOException("absolute prepared profile required");
        Path profile = declaredProfile.toRealPath();
        JsonNode files = inventory.get("files");
        if (files == null || !files.isObject()) throw new IOException("prepared file inventory required");
        FilePin request = jsonPin(files.get("mod-content/fixture/" + FixtureContracts.REQUEST_FILE));
        FilePin contract = jsonPin(files.get("mod-content/fixture/_case_contract.json"));
        if (!Path.of(request.path()).toRealPath().equals(profile.resolve("mod-content/fixture/" + FixtureContracts.REQUEST_FILE).toRealPath())
                || !Path.of(contract.path()).toRealPath().equals(profile.resolve("mod-content/fixture/_case_contract.json").toRealPath())
                || !Path.of(request.path()).toRealPath().startsWith(profile) || !Path.of(contract.path()).toRealPath().startsWith(profile)) throw new IOException("prepared fixture path crossed profile");
        if (request.bytes() != fixture.requestPin().bytes() || !request.sha256().equals(fixture.requestPin().sha256())
                || !pin(Path.of(request.path())).equals(request)) throw new IOException("prepared canonical selection differs from manifest");
        JsonNode compiled = jsonFile(contract);
        if (!text(compiled, "schema").equals("ck3-mod-acceptance-product-assertions-v1") || !text(compiled, "product").equals("religious-ritual-fusion")
                || !text(compiled, "case").equals(fixture.request().kind().wire())) throw new IOException("prepared fixture product/case differs");
        JsonNode emitter = compiled.get("emitter");
        if (emitter == null || !emitter.isObject() || !jsonPin(emitter.get("manifest")).equals(fixture.manifestPin())) throw new IOException("prepared fixture emitter manifest differs");
        if (fixture.request().schemaVersion() == 4) {
            FilePin receipt = inputReceipt(fixture.manifestPin(), fixture.requestPin(), fixture.request());
            if (!jsonPin(emitter.get("input_receipt")).equals(receipt)
                    || !jsonPin(emitter.get("fixture_request")).equals(fixture.requestPin()))
                throw new IOException("prepared snapshot external input closure differs");
            List<FilePin> inputs = ColdSnapshotReader.inputPins(fixture.request());
            JsonNode rows = emitter.get("input_pins");
            if (rows == null || !rows.isArray() || rows.size() != inputs.size()) throw new IOException("prepared snapshot input pin array differs");
            for (int index = 0; index < inputs.size(); index++)
                if (!jsonPin(rows.get(index)).equals(inputs.get(index))) throw new IOException("prepared snapshot input pin differs");
        }
        return new PreparedBinding(expected, request, contract);
    }
    public static BoundRequest read(FilePin expected, String machineId, Path repository) throws IOException {
        Path manifestPath = Path.of(expected.path());
        if (expected.bytes() > 2 * 1024 * 1024 || !pin(manifestPath).equals(expected)) throw new IOException("fixture manifest pin changed");
        Manifest manifest = Json.read(Files.readAllBytes(manifestPath), Manifest.class);
        Path repo = repository.toRealPath(), declaredRoot = Path.of(manifest.fixtureRoot()), root = declaredRoot.toRealPath();
        if (!manifest.machineId().equals(machineId) || manifest.files().size() > 1024 || Files.isSymbolicLink(declaredRoot)) throw new IOException("fixture machine/closure changed");
        for (FilePin source : manifest.producerSourcePins()) {
            if (!Path.of(source.path()).toRealPath().startsWith(repo) || !pin(Path.of(source.path())).equals(source)) throw new IOException("fixture producer source changed");
        }
        Path java = repo.resolve("mod_religious_ritual_fusion/tools/src/main/java/org/xar/ck3/rrf");
        Path catalog = repo.resolve("mod_religious_ritual_fusion/catalog/generated-catalog.json");
        for (Path required : List.of(catalog, java.resolve("ExpectedSelection.java"), java.resolve("acceptance/FixtureContracts.java"), java.resolve("acceptance/FixtureEmitter.java"), java.resolve("acceptance/ColdSnapshotReader.java"))) {
            if (!manifest.producerSourcePins().contains(pin(required))) throw new IOException("fixture selection/catalog producer is not source-bound");
        }
        for (org.xar.ck3.save.SaveContracts.Pin source : org.xar.ck3.save.ProducerSources.verify(repo).repositorySources()) {
            if (!manifest.producerSourcePins().contains(new FilePin(source.path(), source.bytes(), source.sha256()))) throw new IOException("fixture shared parser producer is not source-bound");
        }
        Set<String> actual = new LinkedHashSet<>();
        try (var paths = Files.walk(root)) {
            for (Path path : paths.toList()) {
                if (Files.isSymbolicLink(path) || !path.toRealPath().startsWith(root)) throw new IOException("linked fixture payload rejected");
                if (Files.isRegularFile(path)) actual.add(root.relativize(path).toString().replace('\\', '/'));
            }
        }
        if (!actual.equals(manifest.files().keySet())) throw new IOException("fixture closed inventory differs");
        long total = 0;
        for (Map.Entry<String, FileContent> entry : manifest.files().entrySet()) {
            FileContent content = entry.getValue();
            if (content.bytes() > 2 * 1024 * 1024 || content.bytes() > 8 * 1024 * 1024 - total) throw new IOException("fixture read budget exceeded");
            total += content.bytes(); Path path = root.resolve(entry.getKey()).normalize();
            if (!path.startsWith(root) || !pin(path).equals(new FilePin(path.toRealPath().toString(), content.bytes(), content.sha256()))) throw new IOException("fixture payload pin changed");
        }
        if (!manifest.files().containsKey(FixtureContracts.REQUEST_FILE)) throw new IOException("manifest-frozen fixture request missing");
        Path requestPath = root.resolve(FixtureContracts.REQUEST_FILE);
        if (Files.size(requestPath) > 65536) throw new IOException("fixture request exceeds budget");
        byte[] requestBytes = Files.readAllBytes(requestPath); Request request = Json.read(requestBytes, Request.class);
        if (!manifest.caseId().equals(request.kind().wire()) || !Arrays.equals(requestBytes, Json.write(request))) throw new IOException("fixture request case/canonical JSON differs");
        Catalog definitions = Json.read(Files.readAllBytes(catalog), Catalog.class);
        FixtureEmitter.validateCatalog(definitions); request.expectedSelection().requireCatalog(definitions);
        ColdSnapshotReader.verify(request, machineId, repo);
        if (request.schemaVersion() == 4) inputReceipt(expected, pin(requestPath), request);
        return new BoundRequest(expected, pin(requestPath), request);
    }
    private static FilePin inputReceipt(FilePin manifest, FilePin requestPin, Request request) throws IOException {
        String suffix = ".fixture.json";
        if (!manifest.path().endsWith(suffix)) throw new IOException("snapshot fixture manifest suffix differs");
        Path path = Path.of(manifest.path().substring(0, manifest.path().length() - suffix.length()) + ".inputs.json");
        FilePin receipt = pin(path);
        FixtureContracts.PrebuiltInputs actual = Json.read(Files.readAllBytes(path), FixtureContracts.PrebuiltInputs.class);
        if (!actual.manifest().equals(manifest) || !actual.request().equals(requestPin)
                || !actual.inputPins().equals(ColdSnapshotReader.inputPins(request))) throw new IOException("snapshot input receipt crossed its canonical request");
        return receipt;
    }
    private static FilePin pin(Path path) throws IOException {
        Path actual = path.toRealPath();
        if (!Files.isRegularFile(actual) || Files.size(actual) > 2 * 1024 * 1024) throw new IOException("bounded regular fixture input required");
        byte[] bytes = Files.readAllBytes(actual); return new FilePin(actual.toString(), bytes.length, ReleaseBuilder.sha256(bytes));
    }
    private static JsonNode jsonFile(FilePin expected) throws IOException {
        if (expected.bytes() > 2 * 1024 * 1024 || !pin(Path.of(expected.path())).equals(expected)) throw new IOException("prepared file pin changed");
        return Json.read(Files.readAllBytes(Path.of(expected.path())), JsonNode.class);
    }
    private static String text(JsonNode row, String key) throws IOException {
        JsonNode value = row.get(key);
        if (value == null || !value.isTextual() || value.textValue().isEmpty()) throw new IOException("prepared string required: " + key);
        return value.textValue();
    }
    private static FilePin jsonPin(JsonNode row) throws IOException {
        if (row == null || !row.isObject() || row.size() != 3) throw new IOException("exact prepared file pin required");
        JsonNode bytes = row.get("bytes");
        if (bytes == null || !bytes.isIntegralNumber() || !bytes.canConvertToLong() || bytes.longValue() < 0) throw new IOException("exact prepared byte length required");
        return new FilePin(text(row, "path"), bytes.longValue(), text(row, "sha256"));
    }
}
