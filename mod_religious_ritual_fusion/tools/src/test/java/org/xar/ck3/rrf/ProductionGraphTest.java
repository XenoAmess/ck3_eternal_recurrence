package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.rrf.Contracts.Catalog;
import org.xar.ck3.rrf.Contracts.Product;

/** CI has no CK3 installation: replays the pinned native producer into the entire real mod consumer graph. */
final class ProductionGraphTest {
    @TempDir Path directory;
    @Test void pinnedNativeCatalogToAllRealConsumersAndFormalStaging() throws IOException {
        Path actual = Path.of(System.getProperty("rrf.source"));
        ContentValidator.Validation before = ContentValidator.validate(actual);
        Product product = Json.read(Files.readAllBytes(actual.resolve("tools/product.json")), Product.class);
        Catalog catalog = Json.read(Files.readAllBytes(actual.resolve("catalog/generated-catalog.json")), Catalog.class);
        assertTrue(catalog.sources().stream().anyMatch(s -> s.path().equals("common/scripted_triggers/00_religious_triggers.txt") && s.sha256().equals("e9d0b56130464eabdcd670fa6cf814534d11c99da1e8b3fc1e69e9c3e36d2bb2")));
        assertTrue(catalog.definitions().stream().anyMatch(d -> d.id().equals("tenet_christian_syncretism") && d.canPick().contains("unique_syncretism_trigger")));
        Path replay = directory.resolve("source");
        for (String relative : product.runtimeFiles()) {
            Path target = replay.resolve(relative); Files.createDirectories(target.getParent()); Files.copy(actual.resolve(relative), target);
        }
        Files.createDirectories(replay.resolve("tools")); Files.write(replay.resolve("tools/product.json"), Json.write(product));
        new CatalogGenerator().generate(catalog, replay);
        assertEquals(before, ContentValidator.validate(replay));
        Contracts.Provenance provenance = new Contracts.Provenance(Contracts.ProvenanceKind.SYNTHETIC_FIXTURE, "synthetic-fixture-machine", "2026-10-24T00:00:00Z");
        ReleaseBuilder.BuildResult built = new ReleaseBuilder().build(replay, directory.resolve("staging"), "b".repeat(40), provenance);
        assertEquals(before.runtimeFiles(), new ReleaseBuilder().verify(replay, Path.of(built.staging()), Path.of(built.manifest())).files());
        assertEquals(List.copyOf(ContentValidator.inventory(actual, false).keySet()).stream().sorted().toList(), List.copyOf(ContentValidator.inventory(Path.of(built.staging()), true).keySet()).stream().sorted().toList());
    }
}
