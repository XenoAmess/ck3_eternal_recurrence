package org.xar.ck3.control.build;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Publishes software-host input from explicit legacy or current-checkout producer sources.
 * It preserves the exact original payload token and creates no host or Game authority. */
public final class RootSoftwareFixtureInputsProducer {
    private static final int MAX_REQUEST_BYTES = 8 << 20;
    private static final int MAX_HOST_INPUT_BYTES = 1 << 20;
    private RootSoftwareFixtureInputsProducer() { }

    public record Produced(FileRef requestRef, FileRef probePayloadRef) {
        public Produced { Objects.requireNonNull(requestRef); Objects.requireNonNull(probePayloadRef); }
    }

    public static Produced produce(FileRef producerGoldenPlanRef, Path freshOutputRoot) throws IOException {
        Objects.requireNonNull(producerGoldenPlanRef); Objects.requireNonNull(freshOutputRoot);
        if (!freshOutputRoot.isAbsolute() || !freshOutputRoot.normalize().equals(freshOutputRoot))
            throw new IOException("One absolute normalized fresh software-fixture output root required");
        ProjectStoragePolicy.requireBulkOutput(freshOutputRoot);
        SharedSourceFiles.plainAncestors(freshOutputRoot);
        var plan = FreshSdkFixtureStage.readProducerGoldenSources(producerGoldenPlanRef);
        FreshSdkFixtureStage.requireDeclaredProducerMachine(plan, WindowsJobProcess.currentMachineId());
        List<FileRef> originalInputs = FreshSdkFixtureStage.producerGoldenInputs(plan);
        var requests = new ArrayList<FileRef>();
        byte[] probe = null;
        for (var vector : plan.vectors()) {
            byte[] payload = payload(vector.request(), "G2-" + vector.milestone().name());
            requests.add(vector.request());
            if (probe == null) probe = payload;
        }
        if (probe == null) throw new IOException("Original ordered producer request inventory is empty");
        var originals = new ArrayList<FileRef>(originalInputs);
        originals.addAll(FreshSdkFixtureStage.producerGoldenMetadataInputs(plan)); originals.add(producerGoldenPlanRef);
        if (originals.stream().distinct().count() != originals.size())
            throw new IOException("Golden source metadata and original fixture roles must have independent files");
        for (var reference : originals) reference.verify();
        return publish(originals, requests, probe, freshOutputRoot);
    }

    /** Produces original host inputs directly from the current checkout fixtures. */
    public static Produced produceFromCheckout(Path javaSourceRoot, Path freshOutputRoot) throws IOException {
        Objects.requireNonNull(javaSourceRoot); Objects.requireNonNull(freshOutputRoot);
        if (!javaSourceRoot.isAbsolute() || !javaSourceRoot.normalize().equals(javaSourceRoot))
            throw new IOException("One absolute normalized Java source root required");
        if (!freshOutputRoot.isAbsolute() || !freshOutputRoot.normalize().equals(freshOutputRoot))
            throw new IOException("One absolute normalized fresh software-fixture output root required");
        ProjectStoragePolicy.requireBulkOutput(freshOutputRoot);
        SharedSourceFiles.plainAncestors(javaSourceRoot);
        SharedSourceFiles.plainAncestors(freshOutputRoot);
        if (!Files.isDirectory(javaSourceRoot, LinkOption.NOFOLLOW_LINKS))
            throw new IOException("Actual Java source root directory required");

        List<FileRef> requests = new ArrayList<>();
        byte[] probe = null;
        for (var milestone : FreshSdkFixtureStage.GoldenMilestone.values()) {
            Path path = javaSourceRoot.resolve("g2-research/src/test/resources/g2-http/" + milestone.name() + ".request.json");
            if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS))
                throw new IOException("Actual original G2 request missing: " + path);
            FileRef ref = FileRef.measure(path);
            byte[] payload = payload(ref, "G2-" + milestone.name());
            requests.add(ref);
            if (probe == null) probe = payload;
        }
        if (probe == null) throw new IOException("Original ordered producer request inventory is empty");

        List<FileRef> originals = new ArrayList<>(requests);
        return publish(originals, requests, probe, freshOutputRoot);
    }

    /** Uses the original host source-plan exports directly; it does not manufacture an SDK golden plan. */
    public static Produced produceFromHostFixturePlan(FileRef originalPlanRef, Path freshOutputRoot) throws IOException {
        Objects.requireNonNull(originalPlanRef); Objects.requireNonNull(freshOutputRoot);
        if (!freshOutputRoot.isAbsolute() || !freshOutputRoot.normalize().equals(freshOutputRoot))
            throw new IOException("One absolute normalized fresh software-fixture output root required");
        ProjectStoragePolicy.requireBulkOutput(freshOutputRoot);
        SharedSourceFiles.plainAncestors(freshOutputRoot);
        JsonNode plan = ControlBuild.strictMapper().readTree(read(originalPlanRef, MAX_HOST_INPUT_BYTES));
        fields(plan, Set.of("schema", "machine_id", "observed_at_utc", "status", "supersedes", "ready_rows",
                "pending", "host_map", "upstream_artifact_indexes", "fixture_target_note", "server_context_note", "actual", "new_game_days"));
        if (!"xar.g2-host-actual-fixture-plan/v1".equals(text(plan.get("schema")))
                || !WindowsJobProcess.currentMachineId().equals(text(plan.get("machine_id"))))
            throw new IOException("Original same-machine host fixture source plan required");
        JsonNode rows = plan.get("ready_rows");
        if (rows == null || !rows.isArray() || rows.isEmpty() || rows.size() > 4095)
            throw new IOException("Finite original host fixture source rows required");
        var originals = new ArrayList<FileRef>();
        var selected = new EnumMap<FreshSdkFixtureStage.GoldenMilestone, FileRef>(FreshSdkFixtureStage.GoldenMilestone.class);
        for (JsonNode row : rows) {
            fields(row, Set.of("milestone", "source_ref", "target_relative", "qualification"));
            String milestone = text(row.get("milestone"));
            String target = text(row.get("target_relative"));
            text(row.get("qualification"));
            FileRef source = ControlBuild.strictMapper().treeToValue(row.get("source_ref"), FileRef.class);
            read(source, MAX_REQUEST_BYTES); originals.add(source);
            for (var value : FreshSdkFixtureStage.GoldenMilestone.values()) {
                if (target.equals("g2-research/src/test/resources/g2-http/" + value.name() + ".request.json")) {
                    if (!milestone.equals(value.name()) || selected.put(value, source) != null)
                        throw new IOException("Original host request target has a crossed or duplicate milestone");
                }
            }
        }
        if (selected.size() != FreshSdkFixtureStage.GoldenMilestone.values().length)
            throw new IOException("Every original main G2-M0 through G2-M7 request is required");
        var requests = new ArrayList<FileRef>(); byte[] probe = null;
        for (var value : FreshSdkFixtureStage.GoldenMilestone.values()) {
            FileRef source = selected.get(value); byte[] payload = payload(source, "G2-" + value.name());
            requests.add(source); if (probe == null) probe = payload;
        }
        originals.add(originalPlanRef);
        return publish(originals.stream().distinct().toList(), requests, Objects.requireNonNull(probe), freshOutputRoot);
    }

    private static Produced publish(List<FileRef> originals, List<FileRef> requests, byte[] probe,
            Path freshOutputRoot) throws IOException {
        for (var reference : originals) reference.verify();
        Files.createDirectory(freshOutputRoot);
        Path payloadPath = freshOutputRoot.resolve("probe-payload.json");
        Files.write(payloadPath, probe, StandardOpenOption.CREATE_NEW);
        FileRef payloadRef = FileRef.measure(payloadPath);
        var request = new RootSoftwareFixtureHandoff.Request(List.copyOf(originals), List.copyOf(requests),
                requests.getFirst(), payloadRef);
        byte[] encoded = ControlBuild.strictMapper().writeValueAsBytes(request);
        if (encoded.length == 0 || encoded.length > MAX_HOST_INPUT_BYTES)
            throw new IOException("Bounded actual software-fixture input required");
        Path requestPath = freshOutputRoot.resolve("software-fixture-inputs.json");
        Files.write(requestPath, encoded, StandardOpenOption.CREATE_NEW);
        FileRef requestRef = FileRef.measure(requestPath);
        var reread = ControlBuild.strictMapper().readValue(Files.readAllBytes(requestPath), RootSoftwareFixtureHandoff.Request.class);
        if (!request.equals(reread) || !Arrays.equals(probe, Files.readAllBytes(payloadPath)))
            throw new IOException("Persisted original software-fixture input or payload token changed");
        for (var reference : originals) reference.verify();
        payloadRef.verify(); requestRef.verify();
        return new Produced(requestRef, payloadRef);
    }

    private static void fields(JsonNode value, Set<String> expected) throws IOException {
        if (value == null || !value.isObject()) throw new IOException("Original source-plan object required");
        var actual = new HashSet<String>(); value.fieldNames().forEachRemaining(actual::add);
        if (!actual.equals(expected)) throw new IOException("Original source-plan fields changed");
    }

    private static String text(JsonNode value) throws IOException {
        if (value == null || !value.isTextual() || value.textValue().isBlank())
            throw new IOException("Original source-plan text required");
        return value.textValue();
    }

    private static byte[] read(FileRef original, int maximum) throws IOException {
        Objects.requireNonNull(original);
        if (original.bytes() < 1 || original.bytes() > maximum)
            throw new IOException("Bounded nonempty original fixture required");
        original.verify(); byte[] raw;
        try (var input = Files.newInputStream(Path.of(original.path()))) { raw = input.readNBytes(maximum + 1); }
        original.verify();
        if (raw.length != original.bytes() || raw.length > maximum)
            throw new IOException("Original fixture changed its extent");
        return raw;
    }

    /** Selects an original token; the actual host's G2Wire remains the request schema authority. */
    static byte[] payload(FileRef original, String expectedMilestone) throws IOException {
        byte[] raw = read(original, MAX_REQUEST_BYTES);
        byte[] selected = null;
        String milestone = null;
        var fields = new HashSet<String>();
        try (JsonParser parser = ControlBuild.strictMapper().getFactory().createParser(raw)) {
            if (parser.nextToken() != JsonToken.START_OBJECT)
                throw new IOException("Original G2 request must be an object");
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                if (parser.currentToken() != JsonToken.FIELD_NAME || !fields.add(parser.currentName()))
                    throw new IOException("Original G2 request has a malformed or duplicate field");
                String field = parser.currentName();
                JsonToken token = parser.nextToken();
                if (token == null) throw new IOException("Incomplete original G2 request field");
                if (field.equals("milestone")) {
                    if (token != JsonToken.VALUE_STRING) throw new IOException("Original G2 milestone must be text");
                    milestone = parser.getText();
                } else if (field.equals("payload")) {
                    if (token != JsonToken.START_OBJECT) throw new IOException("Original G2 payload must be an object token");
                    long first = parser.currentTokenLocation().getByteOffset();
                    parser.skipChildren();
                    long last = parser.currentLocation().getByteOffset();
                    if (first < 0 || last <= first || last > raw.length)
                        throw new IOException("Original G2 payload token has no exact byte extent");
                    selected = Arrays.copyOfRange(raw, Math.toIntExact(first), Math.toIntExact(last));
                } else parser.skipChildren();
            }
            if (parser.nextToken() != null) throw new IOException("Trailing content after original G2 request");
        }
        if (!Objects.requireNonNull(expectedMilestone).equals(milestone) || selected == null)
            throw new IOException("Original producer milestone or exact payload token is absent or crossed");
        original.verify();
        return selected;
    }
}
