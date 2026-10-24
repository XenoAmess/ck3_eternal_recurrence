package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.RealmConsumerSourceBindingProducer.Input;
import org.xar.ck3.control.build.RealmConsumerSourceBindingProducer.SelectedSource;
import org.xar.ck3.control.build.RealmConsumerSourceBindingProducer.SourceId;

final class RealmConsumerSourceBindingProducerTest {
    private static final ObjectMapper JSON = ControlBuild.strictMapper();
    private static final String MACHINE = "binding-producer-test-machine";
    @TempDir Path temporary;
    private record Fixture(Input input, FileRef inputRef) { }

    private Fixture fixture() throws IOException {
        Path sources = Files.createDirectory(temporary.resolve("sources"));
        List<SelectedSource> selected = new ArrayList<>();
        for (SourceId id : SourceId.values()) {
            Path directory = Files.createDirectory(sources.resolve(id.name()));
            Path source = directory.resolve(id.fileName());
            Files.writeString(source, "actual selected " + id.name());
            selected.add(new SelectedSource(id.logicalPath(), FileRef.measure(source)));
        }
        Path producer = temporary.resolve("RealmConsumerSourceBindingProducer.java");
        Files.writeString(producer, "exact Java producer source witness");
        Path oracle = temporary.resolve("immutable-producer-golden.json");
        Files.writeString(oracle, "{\"original\":true}");
        Path oldBinding = temporary.resolve("historical-binding.json");
        Files.writeString(oldBinding, "{\"historical\":true}");
        Input input = new Input(RealmConsumerSourceBindingProducer.INPUT_SCHEMA, MACHINE,
                "2026-10-23T07:30:00Z", FileRef.measure(producer), selected,
                List.of(FileRef.measure(oracle), FileRef.measure(oldBinding)));
        Path declaration = temporary.resolve("input.json");
        Files.write(declaration, JSON.writeValueAsBytes(input));
        return new Fixture(input, FileRef.measure(declaration));
    }

    @Test void actualProducerEmitsBothBindingsOriginsAndProtectedReadback() throws IOException {
        Fixture fixture = fixture();
        Path output = temporary.resolve("output");
        var receipt = RealmConsumerSourceBindingProducer.produce(fixture.input(), fixture.inputRef(), output, MACHINE);
        assertEquals(3, receipt.outputRefs().size());
        assertEquals(Files.readString(output.resolve("realmcompare/java-consumer-bindings-v1.json")),
                Files.readString(output.resolve("datedsummary/java-consumer-bindings-v1.json")));
        JsonNode bindings = JSON.readTree(Files.readAllBytes(output.resolve("datedsummary/java-consumer-bindings-v1.json")));
        assertEquals(8, bindings.path("candidate_source_refs").size());
        assertEquals(1, bindings.path("related_consumer_source_refs").size());
        for (JsonNode row : bindings.path("candidate_source_refs")) {
            SourceId id = SourceId.fromLogicalPath(row.path("path").textValue());
            FileRef source = fixture.input().selectedSources().stream()
                    .filter(value -> value.logicalPath().equals(id.logicalPath())).findFirst().orElseThrow().sourceRef();
            assertEquals(source.bytes(), row.path("bytes").longValue());
            assertEquals(source.sha256(), row.path("sha256").textValue());
        }
        JsonNode origins = JSON.readTree(Files.readAllBytes(output.resolve("candidate-source-origins.json")));
        assertEquals(9, origins.path("source_origins").size());
        for (FileRef original : fixture.input().protectedArtifacts()) original.verify();
        for (FileRef result : receipt.outputRefs()) result.verify();
        assertTrue(Files.isRegularFile(output.resolve("generation-receipt.json")));
    }

    @Test void staleSelectedSourceFailsBeforeExport() throws IOException {
        Fixture fixture = fixture();
        Files.writeString(Path.of(fixture.input().selectedSources().getFirst().sourceRef().path()), "changed");
        Path output = temporary.resolve("not-created");
        assertThrows(IOException.class, () -> RealmConsumerSourceBindingProducer.produce(
                fixture.input(), fixture.inputRef(), output, MACHINE));
        assertFalse(Files.exists(output));
    }

    @Test void runtimeInputRejectsMissingDuplicateAndUnknownLogicalSource() throws IOException {
        Fixture fixture = fixture();
        List<SelectedSource> sources = fixture.input().selectedSources();
        assertThrows(IllegalArgumentException.class, () -> new Input(
                fixture.input().schema(), MACHINE, fixture.input().observedAtUtc(),
                fixture.input().producerSourceRef(), sources.subList(0, 8), fixture.input().protectedArtifacts()));
        List<SelectedSource> duplicates = new ArrayList<>(sources);
        duplicates.add(sources.getFirst());
        assertThrows(IllegalArgumentException.class, () -> new Input(
                fixture.input().schema(), MACHINE, fixture.input().observedAtUtc(),
                fixture.input().producerSourceRef(), duplicates, fixture.input().protectedArtifacts()));
        assertThrows(IllegalArgumentException.class, () -> new SelectedSource(
                "unknown.py", sources.getFirst().sourceRef()));
    }

    @Test void strictJsonRejectsBooleanFloatNullAndDuplicateIntegerFields() throws IOException {
        Fixture fixture = fixture();
        String original = Files.readString(Path.of(fixture.inputRef().path()));
        String byteField = "\"bytes\":" + fixture.input().producerSourceRef().bytes();
        assertTrue(original.contains(byteField));
        for (String invalid : List.of("\"bytes\":true", "\"bytes\":1.0", "\"bytes\":null",
                byteField + "," + byteField)) {
            byte[] raw = original.replace(byteField, invalid).getBytes(java.nio.charset.StandardCharsets.UTF_8);
            assertThrows(IOException.class, () -> RealmConsumerSourceBindingProducer.readInput(raw));
        }
    }

    @Test void wrongMachineExistingOutputAndUnboundInputAreRejected() throws IOException {
        Fixture fixture = fixture();
        assertThrows(IllegalArgumentException.class, () -> RealmConsumerSourceBindingProducer.produce(
                fixture.input(), fixture.inputRef(), temporary.resolve("wrong-machine"), "another-machine"));
        Path exists = Files.createDirectory(temporary.resolve("exists"));
        assertThrows(IOException.class, () -> RealmConsumerSourceBindingProducer.produce(
                fixture.input(), fixture.inputRef(), exists, MACHINE));
        Input other = new Input(fixture.input().schema(), MACHINE, "2026-10-23T07:31:00Z",
                fixture.input().producerSourceRef(), fixture.input().selectedSources(), fixture.input().protectedArtifacts());
        assertThrows(IOException.class, () -> RealmConsumerSourceBindingProducer.produce(
                other, fixture.inputRef(), temporary.resolve("unbound"), MACHINE));
        assertFalse(Files.exists(temporary.resolve("unbound")));
    }

    @Test void protectedOriginalDriftRejectsGenerationWithoutReplacement() throws IOException {
        Fixture fixture = fixture();
        Path original = Path.of(fixture.input().protectedArtifacts().getFirst().path());
        Files.writeString(original, "real historical artifact drift");
        Path output = temporary.resolve("not-created");
        assertThrows(IOException.class, () -> RealmConsumerSourceBindingProducer.produce(
                fixture.input(), fixture.inputRef(), output, MACHINE));
        assertFalse(Files.exists(output));
        assertEquals("real historical artifact drift", Files.readString(original));
    }
}
