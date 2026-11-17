package org.xar.ck3.control.wave2.events.unhandledevent;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.TreeMap;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.interactionsourceblocks.InteractionSourceBlocks;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.sourcecatalog.EventSourceCatalogue;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceCompatibilityReview.*;

/** Bounded Java producer over the real retained registry and the two exact authored-source roots. */
public final class SourceCompatibilityReviewCompiler {
    private SourceCompatibilityReviewCompiler() { }
    private static final Map<String, String> TARGET_STOCK = Map.of(
            "gui/event_windows/letter_event.gui", "1560357e8df9e34e125423d8f2dd3db16976add8ce4fa11b469cd5e225dda43d",
            "gui/shared/event_windows.gui", "0a546945dd9e1c379fb4a4cee6ced901b69f28bc0fcc2eb63e9e777cd6210f2e",
            "events/factions/faction_demands.txt", "da8f9298f0ada9b49c69cad5356603ded4dc7ef3c9a10acdebb5a8bb07b3ab5b",
            "events/activities/ecumenical_council_activity/pam_ecumenical_council_events.txt", "c0b376664c1ce72a706ff59a81326ebc80aef4e7e96376d4458516d42be33400",
            "events/scheme_events/sway_scheme/sway_ongoing_events.txt", "cac2328a721aae13c5c60dbe81eccdf83cd8bf06eca1f51f247a098c0f435adc");

    public static SourceCompatibilityReview compile(Path baselineStock, Path targetStock) throws IOException {
        Path oldRoot = baselineStock.toRealPath(), currentRoot = targetStock.toRealPath();
        StrictJson.require(!oldRoot.equals(currentRoot), "separate actual source revisions required");
        requireVersion(oldRoot, "1.20.0.4"); requireVersion(currentRoot, BUILD);
        RegisteredEventKnowledge registry = RegisteredEventKnowledge.load();
        var index = registry.sourceIndex("1.20.0.4");
        Map<Path, byte[]> loaded = new LinkedHashMap<>(); Map<Path, String> readPins = new LinkedHashMap<>();
        Map<String, FileReview> files = new TreeMap<>(); Map<String, EventReview> events = new TreeMap<>();
        for (String key : registry.keys("1.20.0.4").stream().sorted().toList()) {
            ObjectValue legacy = registry.query("1.20.0.4", key);
            Value analysis = legacy.get("analysis"); List<String> dependencies = new ArrayList<>();
            if (analysis instanceof ObjectValue body && body.get("source_sha256") instanceof ObjectValue hashes) {
                for (var entry : new TreeMap<>(hashes.fields()).entrySet()) {
                    StrictJson.require(entry.getValue() instanceof StringValue, "original source digest string required");
                    String expected = ((StringValue) entry.getValue()).value().toLowerCase(Locale.ROOT);
                    byte[] old = read(oldRoot, entry.getKey(), loaded, readPins);
                    StrictJson.require(sha(old).equals(expected), "actual baseline source differs: " + entry.getKey());
                    byte[] current = read(currentRoot, entry.getKey(), loaded, readPins);
                    FileReview review = new FileReview(entry.getKey(), expected, sha(current));
                    FileReview previous = files.putIfAbsent(entry.getKey(), review);
                    StrictJson.require(previous == null || previous.equals(review), "original source digest conflicts");
                    dependencies.add(entry.getKey());
                }
            }
            var entry = index.find(key);
            Optional<DefinitionReview> definition = Optional.empty(); Classification classification;
            if (entry.isEmpty()) {
                StrictJson.require(dependencies.isEmpty(), "indexed source is absent for an available legacy row");
                classification = Classification.LEGACY_SOURCE_UNAVAILABLE;
            } else {
                String relative = entry.orElseThrow().definition().relativePath();
                byte[] oldRaw = read(oldRoot, relative, loaded, readPins);
                StrictJson.require(sha(oldRaw).equalsIgnoreCase(entry.orElseThrow().definition().fileSha256()), "baseline source index/file differs");
                String oldDefinition = definition(oldRaw, key), currentDefinition = definition(read(currentRoot, relative, loaded, readPins), key);
                List<String> oldOptions = EventSourceCatalogue.blocks(oldDefinition, "option");
                List<String> currentOptions = EventSourceCatalogue.blocks(currentDefinition, "option");
                List<List<String>> names = currentOptions.stream().map(option -> EventSourceCatalogue.scalars(option, "name")).toList();
                DefinitionReview selected = new DefinitionReview(relative, EventSourceCatalogue.sourceTokenSha256(oldDefinition),
                        EventSourceCatalogue.sourceTokenSha256(currentDefinition), oldOptions.size(), currentOptions.size(), names);
                definition = Optional.of(selected);
                classification = !selected.identical() ? Classification.DEFINITION_CHANGED
                        : dependencies.stream().allMatch(path -> files.get(path).identical()) ? Classification.DEPENDENCIES_IDENTICAL
                        : Classification.DEFINITION_IDENTICAL_DEPENDENCIES_CHANGED;
            }
            events.put(key, new EventReview(key, classification, dependencies, definition));
        }
        for (var entry : ReviewedLetterSourceRebind.installedSourceHashes().entrySet())
            StrictJson.require(sha(read(oldRoot, entry.getKey(), loaded, readPins)).equals(entry.getValue()), "baseline global stock source differs");
        for (var entry : TARGET_STOCK.entrySet())
            StrictJson.require(sha(read(currentRoot, entry.getKey(), loaded, readPins)).equals(entry.getValue()), "target global stock source differs");
        // Recheck the complete actual read set, rather than treating the first file read as a persistent permission.
        for (var entry : readPins.entrySet())
            StrictJson.require(sha(SourceReviewedEventConsumer.read(entry.getKey(), 2097152)).equals(entry.getValue()), "source changed during compilation");
        return new SourceCompatibilityReview(files, events, TARGET_STOCK);
    }

    private static void requireVersion(Path stock, String expected) throws IOException {
        Path settings = stock.getParent().resolve("launcher/launcher-settings.json");
        Value raw = RetainedJson.parse(SourceReviewedEventConsumer.read(settings, 65536));
        StrictJson.require(raw instanceof ObjectValue object && object.get("rawVersion") instanceof StringValue version
                && expected.equals(version.value()), "actual source launcher version differs");
    }
    private static byte[] read(Path root, String relative, Map<Path, byte[]> loaded, Map<Path, String> readPins) throws IOException {
        Path selected = root.resolve(relative).normalize();
        StrictJson.require(selected.startsWith(root) && !selected.equals(root) && selected.toRealPath().equals(selected), "exact source remains beneath its observed root");
        byte[] bytes = loaded.get(selected);
        if (bytes == null) {
            bytes = SourceReviewedEventConsumer.read(selected, 2097152); loaded.put(selected, bytes); readPins.put(selected, sha(bytes));
        }
        return bytes;
    }
    private static String definition(byte[] raw, String key) throws IOException {
        String source = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
        if (source.startsWith("\ufeff")) source = source.substring(1);
        var extracted = InteractionSourceBlocks.extractEventDefinition(source, key);
        StrictJson.require(extracted instanceof InteractionSourceBlocks.Found, "actual unique selected definition unavailable: " + key);
        return ((InteractionSourceBlocks.Found) extracted).text();
    }
    public static void main(String[] arguments) throws IOException {
        StrictJson.require(arguments.length == 3, "baseline stock, target stock and new output required");
        SourceCompatibilityReview review = compile(Path.of(arguments[0]), Path.of(arguments[1]));
        byte[] encoded = RetainedJson.pythonCanonical(review.json(), new RetainedJson.CanonicalBudget(MAXIMUM_BYTES, 100000, 32)).bytes();
        StrictJson.require(encoded.length <= MAXIMUM_BYTES, "compiled source review exceeds its bound");
        Path output = Path.of(arguments[2]);
        Files.write(output, encoded, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        Map<Classification, Long> counts = new TreeMap<>();
        review.events().values().forEach(event -> counts.merge(event.classification(), 1L, Long::sum));
        System.out.println("source_only=true bytes=" + encoded.length + " sha256=" + sha(encoded) + " classifications=" + counts);
    }
}
