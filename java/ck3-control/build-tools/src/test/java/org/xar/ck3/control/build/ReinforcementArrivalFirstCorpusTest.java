package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Controlled malformed inputs cannot become original C++ producer evidence. */
final class ReinforcementArrivalFirstCorpusTest {
    @TempDir Path temporary;
    private static final List<String> CASES = List.of("already_participating", "help_attacker_en_route", "help_defender_en_route", "help_empty_en_route", "help_retreating_arrived", "ordinary_last_compatible", "ordinary_no_compatible");
    @Test void strictManifestConsumerKeepsAllSevenOriginalNamesAndRejectsWrongTypesMissingOrDuplicateCases() throws Exception {
        var source = new ControlBuild.FileRef(temporary.resolve("battle_reinforcement_arrival_first_12003.cpp").toString(), ReinforcementArrivalFirstCorpus.PRODUCER_SOURCE_BYTES, ReinforcementArrivalFirstCorpus.PRODUCER_SOURCE_SHA256); var exe = pin("producer.exe"); var terminal = pin("actual-terminal.json");
        Path root = Files.createDirectory(temporary.resolve("originals")); var rows = new ArrayList<ReinforcementArrivalFirstCorpus.CaseFile>();
        for (String name : CASES) { Path file = root.resolve(name + ".json"); Files.writeString(file, "{}"); rows.add(new ReinforcementArrivalFirstCorpus.CaseFile(name, ControlBuild.FileRef.measure(file))); }
        var manifest = new ReinforcementArrivalFirstCorpus.Manifest(ReinforcementArrivalFirstCorpus.SCHEMA, "contract-fixture", "2026-10-24T00:00:00Z", root.toString(), source, exe, terminal, rows);
        var mapper = ControlBuild.strictMapper(); Path path = temporary.resolve("manifest.json"); Files.write(path, mapper.writeValueAsBytes(manifest));
        assertEquals(manifest, ReinforcementArrivalFirstCorpus.readManifest(ControlBuild.FileRef.measure(path)));
        assertThrows(IllegalArgumentException.class, () -> new ReinforcementArrivalFirstCorpus.Manifest(manifest.schema(), manifest.machineId(), manifest.observedAtUtc(), manifest.corpusRoot(), source, exe, terminal, rows.subList(0, 6)));
        var duplicate = new ArrayList<>(rows); duplicate.set(6, rows.getFirst());
        assertThrows(IllegalArgumentException.class, () -> new ReinforcementArrivalFirstCorpus.Manifest(manifest.schema(), manifest.machineId(), manifest.observedAtUtc(), manifest.corpusRoot(), source, exe, terminal, duplicate));
        var json = mapper.valueToTree(manifest); ((com.fasterxml.jackson.databind.node.ObjectNode)json.get("files").get(0).get("source_ref")).put("bytes", 1.0);
        assertThrows(IOException.class, () -> mapper.treeToValue(json, ReinforcementArrivalFirstCorpus.Manifest.class));
        assertThrows(IllegalArgumentException.class, () -> ReinforcementArrivalFirstCorpus.require(ControlBuild.FileRef.measure(path), temporary.toString()));
    }
    @Test void actualPublisherRejectsUnexecutedMetadataAndNeverWritesAManifestForFabricatedWholeWires() throws Exception {
        Path root = Files.createDirectory(temporary.resolve("unqualified"));
        for (String name : CASES) Files.writeString(root.resolve(name + ".json"), "{\"case_name\":\"" + name + "\",\"fixture\":{},\"hello\":{},\"semantic_snapshot\":{},\"result\":{}}");
        var source = pin("battle_reinforcement_arrival_first_12003.cpp"); var exe = pin("producer.exe"); var terminal = pin("actual-terminal.json"); Path output = temporary.resolve("must-not-exist.json");
        assertThrows(IllegalArgumentException.class, () -> ReinforcementArrivalFirstCorpus.produce(root, source, exe, terminal, output)); assertFalse(Files.exists(output));
        Files.writeString(root.resolve("extra.json"), "{}");
        assertThrows(IllegalArgumentException.class, () -> ReinforcementArrivalFirstCorpus.produce(root, source, exe, terminal, output)); assertFalse(Files.exists(output));
    }
    private ControlBuild.FileRef pin(String filename) throws Exception { Path file = temporary.resolve(filename); if (!Files.exists(file)) Files.writeString(file, "controlled metadata; never executed"); return ControlBuild.FileRef.measure(file); }
}
