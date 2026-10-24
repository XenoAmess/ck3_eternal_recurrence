package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Reissues selected static consumer bindings from measured sources; never rewrites an oracle. */
public final class RealmConsumerSourceBindingProducer {
    public static final String INPUT_SCHEMA = "xar.ck3.realm-consumer-binding-input/v1";
    public static final String BINDING_SCHEMA = "xar.ck3.realm-java-consumer-source-bindings/v1";
    private static final ObjectMapper JSON = ControlBuild.strictMapper();
    private static final int MAX_INPUT = 65536;

    public enum SourceId {
        REALM_CODEC("java/ck3-control/wave2-planning/src/main/java/org/xar/ck3/control/wave2/planning/realmcompare/RealmDifferenceCodec.java"),
        DATED_CODEC("java/ck3-control/wave3-planning/src/main/java/org/xar/ck3/control/wave3/planning/datedsummary/DatedSummaryCodec.java"),
        FEEDBACK("java/ck3-control/wave3-planning/src/main/java/org/xar/ck3/control/wave3/planning/realmmembership/RealmMembershipFeedback.java"),
        PY_FEEDBACK("ck3_autonomous_player/src/xar_autoplayer/realm_membership_feedback_v1.py"),
        PY_AFTER_QUERY("ck3_autonomous_player/src/xar_autoplayer/bridge/realm_membership_after_query_v1.py"),
        APPLICATION("java/ck3-control/wave3-planning/src/main/java/org/xar/ck3/control/wave3/planning/realmmembership/RealmFeedbackApplication.java"),
        CATALOG("java/ck3-control/wave3-planning/src/main/java/org/xar/ck3/control/wave3/planning/realmmembership/RealmProjectionCatalog.java"),
        CLIENT("tools/g2_saved_campaign/java_map_admission_client_v1.py"),
        CASH("ck3_autonomous_player/src/xar_autoplayer/campaign_score_existing_inputs_v1.py");
        private final String logicalPath;
        SourceId(String logicalPath) { this.logicalPath = logicalPath; }
        public String logicalPath() { return logicalPath; }
        public String fileName() { return logicalPath.substring(logicalPath.lastIndexOf('/') + 1); }
        public static SourceId fromLogicalPath(String path) {
            for (SourceId value : values()) if (value.logicalPath.equals(path)) return value;
            throw new IllegalArgumentException("Unknown consumer logical source: " + path);
        }
    }

    public record SelectedSource(String logicalPath, FileRef sourceRef) {
        public SelectedSource {
            SourceId id = SourceId.fromLogicalPath(logicalPath);
            Objects.requireNonNull(sourceRef, "exact selected source");
            if (sourceRef.bytes() < 1 || sourceRef.bytes() > 1_048_576
                    || !Path.of(sourceRef.path()).getFileName().toString().equals(id.fileName()))
                throw new IllegalArgumentException("Bounded exact source of declared logical type required");
        }
    }
    public record Input(String schema, String machineId, String observedAtUtc, FileRef producerSourceRef,
            List<SelectedSource> selectedSources, List<FileRef> protectedArtifacts) {
        public Input {
            if (!INPUT_SCHEMA.equals(schema) || machineId == null || machineId.isBlank())
                throw new IllegalArgumentException("Input schema and observed machine required");
            Instant.parse(observedAtUtc);
            Objects.requireNonNull(producerSourceRef, "producer source");
            if (!Path.of(producerSourceRef.path()).getFileName().toString()
                    .equals("RealmConsumerSourceBindingProducer.java"))
                throw new IllegalArgumentException("Exact Java producer source required");
            selectedSources = List.copyOf(selectedSources);
            EnumSet<SourceId> seen = EnumSet.noneOf(SourceId.class);
            for (SelectedSource source : selectedSources)
                if (!seen.add(SourceId.fromLogicalPath(source.logicalPath())))
                    throw new IllegalArgumentException("Duplicate source logical identity");
            if (!seen.equals(EnumSet.allOf(SourceId.class)))
                throw new IllegalArgumentException("Complete exact nine-source consumer closure required");
            protectedArtifacts = List.copyOf(protectedArtifacts);
            if (protectedArtifacts.size() < 2 || protectedArtifacts.size() > 16
                    || protectedArtifacts.stream().map(FileRef::path).distinct().count() != protectedArtifacts.size())
                throw new IllegalArgumentException("Distinct original binding/oracle witnesses required");
        }
    }
    public record LogicalRef(String path, long bytes, String sha256) { }
    public record Origin(String logicalPath, String sourcePath) { }
    public record Origins(String schema, String machineId, String observedAtUtc, List<Origin> sourceOrigins) {
        public Origins { sourceOrigins = List.copyOf(sourceOrigins); }
    }
    public record Bindings(String schema, String machineId, String observedAtUtc,
            List<LogicalRef> candidateSourceRefs, List<LogicalRef> relatedConsumerSourceRefs,
            FileRef producerSourceRef, FileRef inputRef, String scope) {
        public Bindings {
            candidateSourceRefs = List.copyOf(candidateSourceRefs);
            relatedConsumerSourceRefs = List.copyOf(relatedConsumerSourceRefs);
        }
    }
    public record Receipt(String schema, String machineId, String observedAtUtc, FileRef inputRef,
            FileRef producerSourceRef, List<FileRef> outputRefs, List<FileRef> protectedArtifacts,
            String qualification) {
        public Receipt { outputRefs = List.copyOf(outputRefs); protectedArtifacts = List.copyOf(protectedArtifacts); }
    }

    private RealmConsumerSourceBindingProducer() { }

    public static Input readInput(byte[] raw) throws IOException {
        if (raw == null || raw.length < 2 || raw.length > MAX_INPUT)
            throw new IOException("Bounded complete producer input required");
        return JSON.readValue(raw, Input.class);
    }

    public static Receipt produce(Input input, FileRef inputRef, Path outputRoot, String observedMachine)
            throws IOException {
        Objects.requireNonNull(input, "input");
        if (!input.machineId().equals(observedMachine))
            throw new IllegalArgumentException("Observed execution machine must match input");
        inputRef.verify();
        if (!readInput(Files.readAllBytes(Path.of(inputRef.path()))).equals(input))
            throw new IOException("Input record must match the exact complete input reference");
        input.producerSourceRef().verify();
        for (SelectedSource source : input.selectedSources()) source.sourceRef().verify();
        for (FileRef original : input.protectedArtifacts()) original.verify();
        Path root = outputRoot.toAbsolutePath().normalize();
        Files.createDirectory(root);
        List<LogicalRef> candidates = new ArrayList<>();
        List<LogicalRef> related = new ArrayList<>();
        List<Origin> origins = new ArrayList<>();
        for (SourceId id : SourceId.values()) {
            SelectedSource source = input.selectedSources().stream()
                    .filter(value -> value.logicalPath().equals(id.logicalPath())).findFirst().orElseThrow();
            FileRef actual = FileRef.measure(Path.of(source.sourceRef().path()));
            if (actual.bytes() != source.sourceRef().bytes()
                    || !actual.sha256().equals(source.sourceRef().sha256()))
                throw new IOException("Selected source changed during production");
            LogicalRef logical = new LogicalRef(id.logicalPath(), actual.bytes(), actual.sha256());
            (id == SourceId.CASH ? related : candidates).add(logical);
            origins.add(new Origin(id.logicalPath(), actual.path()));
        }
        Bindings bindings = new Bindings(BINDING_SCHEMA, input.machineId(), input.observedAtUtc(),
                candidates, related, input.producerSourceRef(), inputRef,
                "Measured selected static sources only; no Python execution, Native, HTTP, SDK or Game grant");
        byte[] bytes = JSON.writeValueAsBytes(bindings);
        List<FileRef> outputs = new ArrayList<>();
        for (String domain : List.of("realmcompare", "datedsummary")) {
            Path directory = Files.createDirectory(root.resolve(domain));
            Path target = directory.resolve("java-consumer-bindings-v1.json");
            Files.write(target, bytes, StandardOpenOption.CREATE_NEW);
            outputs.add(FileRef.measure(target));
        }
        Path declaration = root.resolve("candidate-source-origins.json");
        Origins originDeclaration = new Origins("xar.ck3.candidate-source-origins/v1", input.machineId(),
                input.observedAtUtc(), origins);
        Files.write(declaration, JSON.writeValueAsBytes(originDeclaration), StandardOpenOption.CREATE_NEW);
        outputs.add(FileRef.measure(declaration));
        inputRef.verify();
        input.producerSourceRef().verify();
        for (SelectedSource source : input.selectedSources()) source.sourceRef().verify();
        for (FileRef original : input.protectedArtifacts()) original.verify();
        Receipt receipt = new Receipt("xar.ck3.realm-consumer-binding-generation/v1", input.machineId(),
                Instant.now().toString(), inputRef, input.producerSourceRef(), outputs,
                input.protectedArtifacts(), "GENERATED_SELECTED_STATIC_SOURCE_BINDINGS_ONLY");
        Files.write(root.resolve("generation-receipt.json"), JSON.writeValueAsBytes(receipt),
                StandardOpenOption.CREATE_NEW);
        return receipt;
    }

    public static void main(String[] arguments) throws IOException {
        if (arguments.length != 2) throw new IllegalArgumentException("input.json absent-output-root");
        Path inputPath = Path.of(arguments[0]).toAbsolutePath().normalize();
        FileRef inputRef = FileRef.measure(inputPath);
        Input input = readInput(Files.readAllBytes(inputPath));
        Receipt receipt = produce(input, inputRef, Path.of(arguments[1]), System.getenv("XAR_MACHINE_ID"));
        System.out.println(JSON.writeValueAsString(receipt));
    }
}
