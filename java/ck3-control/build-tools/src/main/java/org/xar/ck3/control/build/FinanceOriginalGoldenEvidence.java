package org.xar.ck3.control.build;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.JsonNode;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.zip.GZIPInputStream;

/**
 * Consumes genuine shared capture receipts and verifies the original sample
 * boundary before producing a resource adoption map. No process is started.
 * Content acceptance is separate from final default-reactor/consumer acceptance.
 */
public final class FinanceOriginalGoldenEvidence {
    private static final String PACKAGE = "org.xar.ck3.control.wave2.finance.";
    private static final String BOUNDARY_SCHEMA = "xar.finance-original-source-boundary/v1";
    private static final String MAP_SCHEMA = "xar.finance-original-resource-adoption/v1";

    public enum Leaf {
        PENDING_READERS("giftpendingreaders", "CaptureGiftPendingReadersGolden",
                "xar.giftpendingreaders.original-producer-consumers-golden/v1",
                "original-producer-golden.json", 65_536, 65_536, 8, List.of()),
        READ_TRANSPORT("giftreadtransport", "GiftReadGoldenCapture",
                "xar.gift-read-transport-original-producer-golden.v1",
                "producer-golden.json.gz", 48_000, 180_000, 5,
                List.of("selected", "private_route_off", "source_changed",
                        "ordinary_unpaused", "ordinary_terminal", "root_government",
                        "root_stale", "root_empty_count", "timed_out",
                        "wrong_response_id", "wrong_response_type", "native_red",
                        "result_missing", "frame_crossed", "active_event_after",
                        "null_get_missing_equivalence", "terminal_reason_not_in_after_binding")),
        ROUTE("giftroute", "GiftRouteGoldenCapture",
                "xar.faction-gift-route-original-producer-golden.v1",
                "producer-golden.json.gz", 48_000, 240_000, 13,
                List.of("needs_checkpoint", "checkpoint_missing_capability",
                        "ready_typed_submit_plan", "checkpoint_wrong_episode",
                        "inactive_plan", "absent_plan", "missing_managed_directory",
                        "root_not_observed", "root_query_unavailable", "known_empty",
                        "government_out_of_scope", "candidate_reader_absent",
                        "private_route_off", "candidate_unavailable", "stock_not_dangerous",
                        "war_cash_floor_preserves_clock", "query_native_frame_crossed_defer",
                        "market_unknown_preserves_clock", "pending_receipt_precedes_cash",
                        "pending_cold_process", "pending_unknown_birth",
                        "pending_equivalent_cim_birth",
                        "pending_fresh_frame_requires_whole_turn_replan",
                        "pending_wait_absent", "pending_wait_stale")),
        PENDING_ROUTE("giftpendingroute", "CaptureGiftPendingReadRouteGolden",
                "xar.giftpendingroute.original-producer-consumer-golden/v1",
                "original-producer-golden.json", 98_304, 98_304, 7,
                List.of("receipt_applied", "receipt_wrong_gold", "receipt_timeout",
                        "receipt_wrong_process", "receipt_revision_changed",
                        "cold_applied", "cold_unchanged", "cold_unknown",
                        "cold_timeout", "cold_same_process", "cold_invalid_birth"));

        private final String directory;
        private final String main;
        private final String schema;
        private final String filename;
        private final int compressedLimit;
        private final int uncompressedLimit;
        private final int sourceCount;
        private final List<String> cases;

        Leaf(String directory, String main, String schema, String filename,
                int compressedLimit, int uncompressedLimit, int sourceCount, List<String> cases) {
            this.directory = directory; this.main = main; this.schema = schema;
            this.filename = filename; this.compressedLimit = compressedLimit;
            this.uncompressedLimit = uncompressedLimit; this.sourceCount = sourceCount;
            this.cases = List.copyOf(cases);
        }

        public String mainClass() { return PACKAGE + directory + "." + main; }
        public String resourceRelativePath() {
            return "wave2-finance/src/test/resources/" + directory + "/" + filename;
        }
    }

    /** Full actual preparation schema; unknown/coerced/missing fields are rejected. */
    public record Boundary(String schema, String machineId, String observedAtUtc, String status,
            String originalRepository, String frozenJavaSourceModule,
            List<ControlBuild.FileRef> originalSourceRefs,
            List<ControlBuild.FileRef> frozenJavaSourceRefs,
            ControlBuild.FileRef interpreterRef, String scope, int originalRefCount,
            long sourceBytes, String execution) {
        public Boundary {
            Objects.requireNonNull(schema); Objects.requireNonNull(machineId);
            Objects.requireNonNull(observedAtUtc); Objects.requireNonNull(status);
            Objects.requireNonNull(originalRepository); Objects.requireNonNull(frozenJavaSourceModule);
            Objects.requireNonNull(interpreterRef); Objects.requireNonNull(scope); Objects.requireNonNull(execution);
            if (!BOUNDARY_SCHEMA.equals(schema) || !status.equals("SOURCE_ONLY_NOT_EXECUTABLE")) {
                throw new IllegalArgumentException("An original source-only preparation boundary is required");
            }
            OffsetDateTime.parse(observedAtUtc);
            originalSourceRefs = List.copyOf(originalSourceRefs);
            frozenJavaSourceRefs = List.copyOf(frozenJavaSourceRefs);
            if (originalRefCount != originalSourceRefs.size() || originalRefCount < 1
                    || originalRefCount > 60 || frozenJavaSourceRefs.size() != 5
                    || sourceBytes != originalSourceRefs.stream().mapToLong(ControlBuild.FileRef::bytes).sum()) {
                throw new IllegalArgumentException("Exact finite original and Java source boundary required");
            }
            Set<String> paths = new HashSet<>();
            for (ControlBuild.FileRef ref : originalSourceRefs) {
                if (!paths.add(ref.path())) throw new IllegalArgumentException("Duplicate original source path");
            }
        }
    }

    public record SampleSource(String path, long bytes, String sha256) {
        public SampleSource {
            Objects.requireNonNull(path); Objects.requireNonNull(sha256);
            if (bytes < 1 || !sha256.matches("[0-9a-f]{64}")) {
                throw new IllegalArgumentException("Exact real sampled source required");
            }
        }
    }

    public record AcceptedGolden(Leaf leaf, String resourceRelativePath,
            ControlBuild.FileRef sourceRef, ControlBuild.FileRef captureReceiptRef,
            String originalObservedAtUtc, int uncompressedBytes, int sampleCount,
            List<SampleSource> emittedOriginalSources) {
        public AcceptedGolden {
            Objects.requireNonNull(leaf); Objects.requireNonNull(resourceRelativePath);
            Objects.requireNonNull(sourceRef); Objects.requireNonNull(captureReceiptRef);
            Objects.requireNonNull(originalObservedAtUtc);
            emittedOriginalSources = List.copyOf(emittedOriginalSources);
        }
    }

    public record AdoptionMap(String schema, String machineId, String observedAtUtc, String status,
            ControlBuild.FileRef originalBoundaryRef, List<AcceptedGolden> resources,
            String fullDefaultVerify, String postDelegatePythonConsumers) {
        public AdoptionMap {
            if (!MAP_SCHEMA.equals(schema)) throw new IllegalArgumentException("Adoption map schema differs");
            Objects.requireNonNull(machineId); Objects.requireNonNull(observedAtUtc);
            Objects.requireNonNull(status); Objects.requireNonNull(originalBoundaryRef);
            Objects.requireNonNull(fullDefaultVerify); Objects.requireNonNull(postDelegatePythonConsumers);
            Instant.parse(observedAtUtc); resources = List.copyOf(resources);
            if (resources.size() != 4 || resources.stream().map(AcceptedGolden::leaf).distinct().count() != 4) {
                throw new IllegalArgumentException("Four different actual original resources required");
            }
        }
    }

    private FinanceOriginalGoldenEvidence() { }

    /**
     * Shape is insufficient: the real shared accepted reader rechecks compilation,
     * actual source/binary origins, native terminal Job0 and exact output bytes.
     */
    public static AcceptedGolden accept(ControlBuild.FileRef captureReceiptRef,
            ControlBuild.FileRef boundaryRef, Leaf leaf) throws IOException {
        Boundary boundary = readBoundary(boundaryRef);
        CompiledGoldenCapture.Receipt capture = CompiledGoldenCapture.acceptedReceipt(
                captureReceiptRef, CompiledGoldenCapture.Mode.CAPTURE);
        require(capture.batch().captures().size() == 1, "One actual original per capture receipt required");
        CompiledGoldenCapture.Request request = capture.batch().captures().getFirst();
        require(capture.batch().profileFor(request.id()).launcher().binaryName().equals(leaf.mainClass()),
                "Actual qualified launcher differs from adopted original leaf");
        require(capture.machineId().equals(boundary.machineId())
                && capture.machineId().equals(WindowsJobProcess.currentMachineId()),
                "Source boundary and actual capture must belong to this machine");
        require(request.cwd().equals(canonical(boundary.originalRepository()).toString()),
                "Actual original repository differs from the pinned boundary");
        require(request.inputRefs().contains(boundary.interpreterRef()),
                "Actual pinned original interpreter must be a request input");
        require(request.sourceRefs().containsAll(boundary.originalSourceRefs()),
                "Actual request omitted original producers, consumers or fixture boundaries");
        for (ControlBuild.FileRef ref : boundary.originalSourceRefs()) ref.verify();
        for (ControlBuild.FileRef ref : boundary.frozenJavaSourceRefs()) ref.verify();
        boundary.interpreterRef().verify();

        ControlBuild.FileRef output = capture.observations().getFirst().outputRef();
        require(output != null && output.bytes() > 0 && output.bytes() <= leaf.compressedLimit,
                "Actual bounded original golden output required");
        byte[] raw = CompiledGoldenCapture.readPinned(output, leaf.compressedLimit);
        if (leaf.filename.endsWith(".gz")) {
            try (var stream = new GZIPInputStream(new ByteArrayInputStream(raw))) {
                raw = stream.readNBytes(leaf.uncompressedLimit + 1);
                require(raw.length <= leaf.uncompressedLimit, "Uncompressed original golden cap exceeded");
            }
        }
        JsonNode golden = strictTree(raw);
        require(golden.isObject(), "Original golden must be an object");
        require(text(golden, "schema").equals(leaf.schema), "Original golden schema differs");
        require(text(golden, "machine_id").equals(capture.machineId()), "Golden machine differs from actual capture");
        String observed = text(golden, "observed_at_utc");
        Instant sampledAt;
        try { sampledAt = OffsetDateTime.parse(observed).toInstant(); }
        catch (RuntimeException error) { throw new IOException("Actual original observation timestamp required", error); }
        Instant preparedAt = OffsetDateTime.parse(boundary.observedAtUtc()).toInstant();
        require(!sampledAt.isBefore(preparedAt)
                && !sampledAt.isAfter(Instant.parse(capture.observedAtUtc())),
                "Original sample timestamp must follow source preparation and precede its actual receipt");
        List<SampleSource> sampleSources = sources(golden, boundary, leaf, request.sourceRefs());
        int samples = validateSamples(golden, leaf);
        for (ControlBuild.FileRef ref : boundary.originalSourceRefs()) ref.verify();
        output.verify(); boundaryRef.verify(); captureReceiptRef.verify();
        return new AcceptedGolden(leaf, leaf.resourceRelativePath(), output, captureReceiptRef,
                observed, raw.length, samples, sampleSources);
    }

    public static AdoptionMap acceptAll(ControlBuild.FileRef boundary,
            List<ControlBuild.FileRef> orderedReceipts) throws IOException {
        require(orderedReceipts != null && orderedReceipts.size() == 4,
                "Reader, transport, route and pending-route real receipts required in order");
        var resources = new ArrayList<AcceptedGolden>();
        Leaf[] order = {Leaf.PENDING_READERS, Leaf.READ_TRANSPORT, Leaf.ROUTE, Leaf.PENDING_ROUTE};
        for (int index = 0; index < order.length; index++) {
            resources.add(accept(orderedReceipts.get(index), boundary, order[index]));
        }
        Boundary source = readBoundary(boundary);
        return new AdoptionMap(MAP_SCHEMA, source.machineId(), Instant.now().toString(),
                "ACTUAL_ORIGINAL_CONTENT_ACCEPTED", boundary, resources,
                "NOT_RUN_BY_CONTENT_ACCEPTANCE; require complete default reactor with zero failures/errors/skips",
                "NOT_RUN_BY_CONTENT_ACCEPTANCE; original fixtures cannot prove later Java delegates");
    }

    private static Boundary readBoundary(ControlBuild.FileRef reference) throws IOException {
        byte[] raw = CompiledGoldenCapture.readPinned(reference, 65_536);
        Boundary result = ControlBuild.strictMapper().readValue(raw, Boundary.class);
        require(canonical(result.originalRepository()).toRealPath().toString().equals(result.originalRepository()),
                "Original source boundary repository must be canonical");
        reference.verify(); return result;
    }

    static List<SampleSource> sources(JsonNode golden, Boundary boundary, Leaf leaf,
            List<ControlBuild.FileRef> requestSources) throws IOException {
        boolean lengthsEmitted = leaf == Leaf.PENDING_READERS || leaf == Leaf.PENDING_ROUTE;
        JsonNode refs = golden.get(lengthsEmitted ? "source_refs" : "source_bindings");
        require(refs != null && refs.isArray() && refs.size() == leaf.sourceCount,
                "Exact original emitted source count required");
        Map<Path, ControlBuild.FileRef> pinned = new HashMap<>();
        Path repository = canonical(boundary.originalRepository());
        for (ControlBuild.FileRef ref : boundary.originalSourceRefs()) {
            require(pinned.put(canonical(ref.path()), ref) == null, "Repeated original source pin");
        }
        Set<String> seen = new HashSet<>(); var accepted = new ArrayList<SampleSource>();
        for (JsonNode value : refs) {
            require(value.isObject(), "Sampled source must be an object");
            Set<String> keys = new HashSet<>(); value.fieldNames().forEachRemaining(keys::add);
            require(keys.equals(lengthsEmitted ? Set.of("path", "bytes", "sha256") : Set.of("path", "sha256")),
                    "Sampled source field contract differs");
            String relative = text(value, "path");
            Path relativePath = Path.of(relative);
            require(!relativePath.isAbsolute() && relative.indexOf('\\') < 0
                    && relativePath.equals(relativePath.normalize()) && seen.add(relative),
                    "Unique canonical relative sampled source path required");
            Path actual = repository.resolve(relativePath).normalize();
            require(actual.startsWith(repository), "Sampled source escaped original repository");
            ControlBuild.FileRef expected = pinned.get(actual);
            require(expected != null && requestSources.contains(expected)
                    && expected.sha256().equals(text(value, "sha256")),
                    "Original sample source differs from actual boundary/request pin");
            if (lengthsEmitted) {
                JsonNode length = value.get("bytes");
                require(length != null && length.isIntegralNumber() && length.canConvertToLong()
                        && length.longValue() == expected.bytes(), "Original source byte count differs");
            }
            expected.verify();
            accepted.add(new SampleSource(relative, expected.bytes(), expected.sha256()));
        }
        return List.copyOf(accepted);
    }

    static int validateSamples(JsonNode golden, Leaf leaf) throws IOException {
        if (leaf != Leaf.PENDING_READERS) {
            JsonNode cases = golden.get("cases");
            require(cases != null && cases.isArray() && cases.size() == leaf.cases.size(),
                    "Every actual original case required");
            for (int index = 0; index < leaf.cases.size(); index++) {
                require(text(cases.get(index), "name").equals(leaf.cases.get(index)),
                        "Original case order or identity differs");
            }
            return cases.size();
        }
        JsonNode reads = golden.get("new_proposal_source_reads");
        require(reads != null && reads.isIntegralNumber() && reads.canConvertToInt()
                && reads.intValue() == 0, "Pending readers must perform zero new proposal source reads");
        String before = text(golden, "ledger_sha256_before"), after = text(golden, "ledger_sha256_after");
        require(before.matches("[0-9a-f]{64}") && before.equals(after),
                "Actual original ledger must remain byte-identical through readers");
        require(golden.path("ledger").path("pending").isObject(), "Actual producer pending ledger required");
        require(golden.path("feast_budget").path("reason").isTextual()
                && golden.path("feast_budget").path("reason").textValue().equals("faction_gift_pending"),
                "Actual feast consumer pending block required");
        require(golden.path("formal_collector").path("plan").path("selected_step").isTextual()
                && golden.path("formal_collector").path("plan").path("selected_step").textValue()
                        .equals("private-query-faction-gift-receipt-v1"),
                "Actual full collector must choose fixed pending verification read");
        return 1;
    }

    private static JsonNode strictTree(byte[] raw) throws IOException {
        try (JsonParser parser = ControlBuild.strictMapper().createParser(raw)) {
            JsonNode result = ControlBuild.strictMapper().readTree(parser);
            require(result != null && parser.nextToken() == null, "One strict golden JSON value required");
            return result;
        }
    }

    private static String text(JsonNode node, String key) throws IOException {
        JsonNode value = node == null ? null : node.get(key);
        require(value != null && value.isTextual() && !value.textValue().isEmpty(),
                "Nonempty text required: " + key);
        return value.textValue();
    }

    private static Path canonical(String value) throws IOException {
        require(value != null, "Explicit path required"); Path path = Path.of(value);
        require(path.isAbsolute() && path.equals(path.toAbsolutePath().normalize()),
                "Canonical absolute path required"); return path;
    }

    private static void require(boolean condition, String message) throws IOException {
        if (!condition) throw new IOException(message);
    }

    /** Data-only CLI on the complete qualified tools classpath; starts no child. */
    public static void main(String[] args) throws IOException {
        if (args.length != 6) throw new IllegalArgumentException(
                "boundary output-map reader-receipt transport-receipt route-receipt pending-route-receipt");
        Path destination = canonical(args[1]);
        require(Files.isDirectory(destination.getParent())
                && !Files.exists(destination), "Create-only adoption map in existing admitted output root required");
        List<ControlBuild.FileRef> receipts = new ArrayList<>();
        for (int index = 2; index < args.length; index++) {
            receipts.add(ControlBuild.FileRef.measure(canonical(args[index])));
        }
        AdoptionMap accepted = acceptAll(ControlBuild.FileRef.measure(canonical(args[0])), receipts);
        byte[] json = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(accepted);
        require(json.length <= 32_768, "Finite original resource adoption map required");
        Files.write(destination, json, StandardOpenOption.CREATE_NEW);
        System.out.println(ControlBuild.strictMapper().writeValueAsString(ControlBuild.FileRef.measure(destination)));
    }
}
