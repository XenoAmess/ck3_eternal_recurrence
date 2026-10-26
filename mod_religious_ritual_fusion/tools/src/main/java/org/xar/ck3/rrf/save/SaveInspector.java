package org.xar.ck3.rrf.save;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.rrf.Json;
import org.xar.ck3.rrf.acceptance.FixtureContracts;
import org.xar.ck3.rrf.acceptance.FrozenFixtureReader;
import org.xar.ck3.rrf.acceptance.FrozenFixtureReader.BoundRequest;
import org.xar.ck3.rrf.acceptance.FrozenFixtureReader.PreparedBinding;
import org.xar.ck3.rrf.save.SaveContracts.*;

/** Offline Rakaly stdout oracle. No temp melt, copied save, game process, or business mutation. */
public final class SaveInspector {
    private SaveInspector() { }
    public record Receipt(Pin report, int selectedScopes, boolean gameStarted) { }
    public static void main(String[] args) { System.exit(run(args)); }
    public static int run(String[] args) {
        try {
            if (args.length != 4 || !args[0].equals("--inputs") || !args[2].equals("--output")) throw new IllegalArgumentException("inspect-save requires --inputs request.json --output unused-report.json");
            Path inputs = Path.of(args[1]); Path output = Path.of(args[3]).toAbsolutePath().normalize();
            if (Files.size(inputs) > 65536 || Files.exists(output)) throw new IllegalArgumentException("bounded request and unused output required");
            Request request = Json.read(Files.readAllBytes(inputs), Request.class);
            Report report = inspect(request); byte[] bytes = Json.write(report);
            if (bytes.length > 1024 * 1024) throw new IOException("report exceeds one MiB output budget");
            Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
            System.out.println(new String(Json.write(new Receipt(pin(output), report.scopes().size(), false)), StandardCharsets.UTF_8));
            return 0;
        } catch (IOException | IllegalArgumentException error) { System.err.println("RRF SAVE INSPECTION FAILED: " + error.getMessage()); return 1; }
    }
    public static Report inspect(Request request) throws IOException {
        return inspect(request, org.xar.ck3.save.SaveDecoder::launch);
    }
    @FunctionalInterface interface DecoderLauncher { Process start(Path decoder, Path save) throws IOException; }
    static Report inspect(Request request, DecoderLauncher launcher) throws IOException {
        org.xar.ck3.save.ProducerSources.Binding producer = org.xar.ck3.save.ProducerSources.verify(Path.of(request.repository()));
        BoundRequest fixture = null;
        PreparedBinding prepared = null;
        if (request.expectation() instanceof FusionSelection expected) {
            fixture = fixture(request, expected); prepared = prepared(expected, fixture);
        }
        org.xar.ck3.save.SaveContracts.Decoded decoded = org.xar.ck3.save.SaveDecoder.inspect(
                shared(request.save()), shared(request.decoder()), SaveStream.selection(request),
                org.xar.ck3.save.SaveContracts.DecoderLimits.standard(), launcher::start);
        SaveStream.Projection projection = SaveStream.fromShared(decoded.projection());
        Assessment assessment = new NotAssessed();
        if (request.expectation() instanceof FusionSelection expected) {
            if (fixture == null || prepared == null || !fixture.equals(fixture(request, expected)) || !prepared.equals(prepared(expected, fixture))) throw new IOException("fixture selection/preparation changed during save inspection");
            assessment = SavedSelectionComparator.compare(request, projection.scopes(), fixture, prepared, expected.resultRiteId());
        }
        if (!producer.equals(org.xar.ck3.save.ProducerSources.verify(Path.of(request.repository())))) throw new IOException("save-core producer changed during inspection");
        return new Report("rrf-save-inspection-v2", request.machineId(), Instant.now().toString(), request, decoded.exitCode(), decoded.stderr(),
                new StreamEvidence(decoded.streamSha256(), decoded.streamBytes(), Long.toString(projection.tokens()), Integer.toString(projection.selectedTokenBytes()), projection.rootKeys(), projection.rootScalars()),
                projection.inventories(), projection.scopes(), producerPins(Path.of(request.repository()), producer), true, false, assessment);
    }
    private static org.xar.ck3.save.SaveContracts.Pin shared(Pin pin) {
        return new org.xar.ck3.save.SaveContracts.Pin(pin.path(), pin.bytes(), pin.sha256());
    }
    private static BoundRequest fixture(Request request, FusionSelection expected) throws IOException {
        Pin pin = expected.fixtureManifest();
        return FrozenFixtureReader.read(new FixtureContracts.FilePin(pin.path(), pin.bytes(), pin.sha256()), request.machineId(), Path.of(request.repository()));
    }
    private static PreparedBinding prepared(FusionSelection expected, BoundRequest fixture) throws IOException {
        Pin pin = expected.preparedProfileInventory();
        return FrozenFixtureReader.readPrepared(new FixtureContracts.FilePin(pin.path(), pin.bytes(), pin.sha256()), fixture);
    }
    private static List<Pin> producerPins(Path repository, org.xar.ck3.save.ProducerSources.Binding producer) throws IOException {
        Path javaSources = repository.resolve("mod_religious_ritual_fusion/tools/src/main/java/org/xar/ck3/rrf"); List<Pin> pins = new ArrayList<>();
        for (String source : List.of("save/SaveContracts.java", "save/SaveStream.java", "save/SaveInspector.java", "save/SavedSelectionComparator.java", "acceptance/FixtureContracts.java", "acceptance/FixtureEmitter.java", "acceptance/FrozenFixtureReader.java", "ExpectedSelection.java", "Command.java", "Clausewitz.java", "Contracts.java", "Json.java", "ReleaseBuilder.java")) {
            Path path = javaSources.resolve(source);
            try (var embedded = SaveInspector.class.getResourceAsStream("/producer-source/org/xar/ck3/rrf/" + source)) {
                if (embedded == null || !java.util.Arrays.equals(Files.readAllBytes(path), embedded.readAllBytes())) throw new IOException("loaded RRF save producer source differs: " + source);
            }
            pins.add(pin(path));
        }
        for (org.xar.ck3.save.SaveContracts.Pin source : producer.repositorySources()) pins.add(new Pin(source.path(), source.bytes(), source.sha256()));
        return List.copyOf(pins);
    }
    public static Pin pin(Path path) throws IOException {
        org.xar.ck3.save.SaveContracts.Pin pin = org.xar.ck3.save.FilePins.pin(path);
        return new Pin(pin.path(), pin.bytes(), pin.sha256());
    }
}
