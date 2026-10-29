package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SdkSourceAssembly.Digest;
import org.xar.ck3.control.build.SdkSourceAssembly.Source;
import org.xar.ck3.control.build.SdkSourceAssembly.SourceCost;
import org.xar.ck3.control.build.SdkSourceAssembly.SourceViewCosts;

/** Prices declared source digests through the assembly's own algorithm. Never invents reviews or native witnesses. */
public final class SdkSharedQuoteProducer {
    public static final String REQUEST_SCHEMA = "xar.sdk-source-cost-request/v1";
    public static final String REPORT_SCHEMA = "xar.sdk-source-cost-report/v1";
    private static final int MAX_INPUT = 2 << 20;
    private static final int MAX_OUTPUT = 32768;
    private SdkSharedQuoteProducer() { }
    public enum Evidence { DECLARED_DIGEST_FORECAST_NO_REUSE_CREDIT, ACTUAL_REVIEW_AND_NATIVE_REUSE }
    public enum ReusePolicy { EXISTING_ORIGINALS_READ_ONLY }
    public record ServiceBound(long logicalHardBytes, long allocationHardBytes, int visitedEntriesHard) {
        public ServiceBound {
            if (logicalHardBytes < 1 || logicalHardBytes > 512L * 1024 * 1024 || allocationHardBytes < logicalHardBytes
                    || allocationHardBytes > 2L << 30 || visitedEntriesHard < 1 || visitedEntriesHard > 10000)
                throw new IllegalArgumentException("Finite future accepted normal deployment bounds required");
        }
    }
    public record Request(String schema, String machineId, String reviewAtUtc, FileRef sourceIntentPlanRef,
            FileRef canonicalInventoryRef, FileRef dependencyInventoryRef, String groupRoot,
            long allocationUnitBytes, long perDirectoryGuardBytes, long sharedViewPhysicalHardBytes,
            ServiceBound futureServiceBound, ReusePolicy originalReusePolicy) {
        public Request {
            if (!REQUEST_SCHEMA.equals(schema) || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,127}") || machineId.equals("unknown"))
                throw new IllegalArgumentException("Exact source cost schema and machine required");
            Instant.parse(reviewAtUtc); absolute(groupRoot); Objects.requireNonNull(sourceIntentPlanRef);
            Objects.requireNonNull(canonicalInventoryRef); Objects.requireNonNull(dependencyInventoryRef);
            Objects.requireNonNull(futureServiceBound); Objects.requireNonNull(originalReusePolicy);
            if (allocationUnitBytes < 1 || allocationUnitBytes > 1L << 20 || perDirectoryGuardBytes < 0
                    || perDirectoryGuardBytes > 1L << 20 || sharedViewPhysicalHardBytes < 1
                    || sharedViewPhysicalHardBytes > 2L << 30)
                throw new IllegalArgumentException("Finite declared native geometry and artifact bounds required");
        }
    }
    /** Page sums and directory sets are calculated from pinned metadata; native allocation is unobserved. */
    public record InventoryCost(FileRef inventoryRef, int files, long logicalBytes, long pageUpperBytes,
            int rootedDirectories, ReusePolicy reusePolicy, long newCopyChargeBytes) { }
    public record ViewCost(int files, long logicalBytes, long pageUpperBytes, int directories) { }
    public record Forecast(String schema, String machineId, String reviewAtUtc, Evidence evidence, FileRef requestRef,
            FileRef sourceIntentPlanRef, List<FileRef> templateRefs, List<ViewCost> views,
            SdkSourceAssembly.SharedQuote sharedQuote, long allocationUnitBytes, long perDirectoryGuardBytes,
            long sharedSourceAllocationUpperBytes, long artifactSourceGateIncrementBytes,
            InventoryCost canonicalOriginals, InventoryCost interpreterDependencies,
            ServiceBound futureServiceBound, long futureServiceAndSharedSourceUpperBytes,
            boolean acceptedServiceDeploymentObserved, boolean sourceViewsMaterialized, boolean executionAuthorized) {
        public Forecast {
            templateRefs = List.copyOf(templateRefs); views = List.copyOf(views);
            if (!REPORT_SCHEMA.equals(schema) || evidence != Evidence.DECLARED_DIGEST_FORECAST_NO_REUSE_CREDIT
                    || templateRefs.size() != 3 || views.size() != 3 || acceptedServiceDeploymentObserved
                    || sourceViewsMaterialized || executionAuthorized) throw new IllegalArgumentException("Forecast cannot claim actual deployment, views or authority");
        }
    }

    /** forecast REQUEST_PATH BYTES SHA NEW_REPORT MAX_NATIVE; actual VIEWS_PATH BYTES SHA UNIT DIR_GUARD NEW_REPORT MAX_NATIVE. */
    public static void main(String[] args) throws IOException {
        if (args.length == 6 && args[0].equals("forecast")) {
            FileRef request = reference(args, 1); Request value = read(request, Request.class);
            Forecast report = forecast(request, value);
            System.out.println(ControlBuild.strictMapper().writeValueAsString(write(report, Path.of(args[4]), positive(args[5]))));
        } else if (args.length == 8 && args[0].equals("actual")) {
            FileRef request = reference(args, 1);
            var report = SdkSourceAssembly.priceViews(request, positive(args[4]), positive(args[5]));
            System.out.println(ControlBuild.strictMapper().writeValueAsString(write(report, Path.of(args[6]), positive(args[7]))));
        } else throw new IllegalArgumentException("Exact finite forecast or actual price arguments required");
    }

    public static Forecast forecast(FileRef requestRef, Request request) throws IOException {
        requestRef.verify();
        if (!request.equals(read(requestRef, Request.class))) throw new IOException("Cost request differs from its exact persisted input");
        if (!request.machineId().equals(WindowsJobProcess.currentMachineId()) || !Instant.now().isBefore(Instant.parse(request.reviewAtUtc())))
            throw new IOException("Current machine and unexpired metadata review required; this grants no execution");
        SdkSourceIntent.Plan plan = read(request.sourceIntentPlanRef(), SdkSourceIntent.Plan.class);
        if (!plan.machineId().equals(request.machineId()) || Instant.parse(plan.reviewAtUtc()).isBefore(Instant.parse(request.reviewAtUtc())))
            throw new IOException("Source intent machine/review differs");
        List<FileRef> templates = List.of(plan.baselineTemplateRef(), plan.legacyTemplateRef(), plan.consumerTemplateRef());
        var base = SdkSourceAssembly.readRequest(templates.get(0));
        var legacy = SdkSourceAssembly.readRequest(templates.get(1));
        var consumer = SdkSourceAssembly.readRequest(templates.get(2));
        if (!base.machineId().equals(request.machineId()) || !legacy.machineId().equals(request.machineId())
                || !consumer.machineId().equals(request.machineId())) throw new IOException("Template machine differs");
        var baseSources = sources(base.sources()); var legacySources = sources(legacy.sources()); var consumerSources = sources(consumer.sources());
        for (Source source : plan.referenceInputs().additions()) {
            add(baseSources, source); add(legacySources, source); add(consumerSources, source);
        }
        Map<String, Source> preimages = sources(consumer.sources());
        var selectedCosts = new LinkedHashMap<String, SourceCost>();
        for (var selection : plan.consumerSelections()) {
            String key = key(selection.relativePath());
            if (!Objects.equals(preimages.get(key), selection.expectedTemplateSource()))
                throw new IOException("Selected exact template preimage differs: " + selection.relativePath());
            Digest result = selection.kind() == SdkSourceIntent.SelectionKind.REPLACE_CONTENT
                    ? digest(selection.selectedSource()) : declaredResult(selection.selectedSource(), selection.selectedOverlays());
            Source previous = consumerSources.get(key);
            if (selection.kind() == SdkSourceIntent.SelectionKind.ADD_SOURCE && previous != null)
                throw new IOException("Selected addition overlaps a reference addition");
            // Cost leaves retain the declared result digest; they are never passed as reviewed source evidence.
            selectedCosts.put(key, new SourceCost(selection.relativePath(), result));
        }
        var baselineCosts = costs(baseSources, Map.of());
        var legacyCosts = costs(legacySources, Map.of());
        var consumerCosts = costs(consumerSources, selectedCosts);
        return assembleForecast(requestRef, request, plan, templates, baselineCosts, legacyCosts, consumerCosts);
    }

    private static Forecast assembleForecast(FileRef requestRef, Request request, SdkSourceIntent.Plan plan, List<FileRef> templates,
            SourceViewCosts baseline, SourceViewCosts legacy, SourceViewCosts consumer) throws IOException {
        var quote = SdkSourceAssembly.sourceQuote(request.machineId(), request.groupRoot(), baseline, legacy, consumer,
                0, 0, request.sharedViewPhysicalHardBytes());
        long physical = SdkSourceAssembly.sourceAllocationUpper(quote, baseline, legacy, consumer, Set.of(),
                request.allocationUnitBytes(), request.perDirectoryGuardBytes(), baseline.sources().size());
        if (physical > request.sharedViewPhysicalHardBytes()) throw new IOException("Declared source views exceed their complete native hard bound");
        long artifacts = Math.addExact(quote.allViewLogicalBytes(), Math.addExact(quote.metadataHardBytes(),
                Math.multiplyExact(quote.directories(), request.perDirectoryGuardBytes())));
        InventoryCost canonical = inventory(request.canonicalInventoryRef(), true, request.machineId(), request.allocationUnitBytes());
        InventoryCost dependencies = inventory(request.dependencyInventoryRef(), false, request.machineId(), request.allocationUnitBytes());
        requestRef.verify(); request.sourceIntentPlanRef().verify(); for (FileRef ref : templates) ref.verify();
        return new Forecast(REPORT_SCHEMA, request.machineId(), request.reviewAtUtc(), Evidence.DECLARED_DIGEST_FORECAST_NO_REUSE_CREDIT,
                requestRef, request.sourceIntentPlanRef(), templates, List.of(view(baseline, request.allocationUnitBytes()),
                view(legacy, request.allocationUnitBytes()), view(consumer, request.allocationUnitBytes())), quote,
                request.allocationUnitBytes(), request.perDirectoryGuardBytes(), physical, artifacts, canonical, dependencies,
                request.futureServiceBound(), Math.addExact(physical, request.futureServiceBound().allocationHardBytes()), false, false, false);
    }

    public static InventoryCost inventory(FileRef ref, boolean canonical, String machine, long unit) throws IOException {
        JsonNode root = readTree(ref);
        String schema = canonical ? "xar.canonical-source-inventory-preparation/v1" : "xar.sdk-interpreter-dependency-source-inventory/v1";
        if (!root.path("schema").isTextual() || !schema.equals(root.path("schema").textValue())
                || !root.path("machine_id").isTextual() || !machine.equals(root.path("machine_id").textValue())
                || !root.path("files").isArray()) throw new IOException("Pinned inventory schema/machine/files required");
        var roots = new ArrayList<Path>();
        if (canonical) roots.add(absolute(text(root, "repository")));
        else {
            JsonNode entries = root.path("dependency_roots_in_search_order");
            if (!entries.isArray() || entries.isEmpty()) throw new IOException("Actual declared dependency roots required");
            for (JsonNode entry : entries) {
                if (!entry.isTextual()) throw new IOException("Dependency root must be text");
                roots.add(absolute(entry.textValue()));
            }
        }
        var files = new LinkedHashMap<String, FileRef>(); var directories = new HashSet<String>();
        long logical = 0, pages = 0;
        for (JsonNode entry : root.path("files")) {
            FileRef file = ControlBuild.strictMapper().treeToValue(entry, FileRef.class);
            Path path = absolute(file.path()); Path owning = null;
            for (Path candidate : roots) if (path.startsWith(candidate) && (owning == null || candidate.getNameCount() < owning.getNameCount())) owning = candidate;
            if (owning == null || path.equals(owning) || files.putIfAbsent(key(path.toString()), file) != null)
                throw new IOException("Distinct original file beneath an exact inventory root required");
            logical = Math.addExact(logical, file.bytes()); pages = Math.addExact(pages, round(file.bytes(), unit));
            for (Path parent = path.getParent(); parent != null && parent.startsWith(owning); parent = parent.getParent())
                directories.add(key(parent.toString()));
        }
        JsonNode declared = root.path("logical_bytes");
        if (!declared.isIntegralNumber() || !declared.canConvertToLong() || declared.longValue() != logical)
            throw new IOException("Inventory logical byte sum differs");
        ref.verify();
        return new InventoryCost(ref, files.size(), logical, pages, directories.size(), ReusePolicy.EXISTING_ORIGINALS_READ_ONLY, 0);
    }

    private static SourceViewCosts costs(Map<String, Source> sources, Map<String, SourceCost> selected) throws IOException {
        var result = new LinkedHashMap<String, SourceCost>();
        for (var row : sources.entrySet()) result.put(row.getKey(), new SourceCost(row.getValue().relativePath(),
                declaredResult(row.getValue().original(), row.getValue().overlays())));
        result.putAll(selected);
        var directories = new LinkedHashSet<String>(List.of(".", ".assembly"));
        for (SourceCost source : result.values()) {
            String parent = source.relativePath();
            while (parent.contains("/")) { parent = parent.substring(0, parent.lastIndexOf('/')); directories.add(parent); }
        }
        return new SourceViewCosts(List.copyOf(result.values()), directories.size());
    }
    private static Digest declaredResult(FileRef original, List<SdkSourceAssembly.Overlay> overlays) throws IOException {
        Digest result = digest(original);
        for (var overlay : overlays) {
            if (!overlay.standaloneBase().equals(result))
                throw new IOException("Composed overlay lacks a declared exact digest chain; actual source review required");
            result = overlay.standaloneResult();
        }
        return result;
    }
    private static Map<String, Source> sources(List<Source> rows) throws IOException {
        var result = new LinkedHashMap<String, Source>();
        for (Source source : rows) if (result.putIfAbsent(key(source.relativePath()), source) != null) throw new IOException("Duplicate template path");
        return result;
    }
    private static void add(Map<String, Source> sources, Source source) throws IOException {
        if (sources.putIfAbsent(key(source.relativePath()), source) != null) throw new IOException("Duplicate reference input");
    }
    private static ViewCost view(SourceViewCosts costs, long unit) {
        long pages = 0; for (SourceCost source : costs.sources()) pages = Math.addExact(pages, round(source.result().bytes(), unit));
        return new ViewCost(costs.sources().size(), costs.logicalBytes(), pages, costs.directories());
    }
    private static Digest digest(FileRef ref) { return new Digest(ref.bytes(), ref.sha256()); }
    private static JsonNode readTree(FileRef ref) throws IOException {
        if (ref.bytes() < 1 || ref.bytes() > MAX_INPUT) throw new IOException("Bounded pinned metadata required");
        ref.verify(); JsonNode value = ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(ref.path()))); ref.verify(); return value;
    }
    private static <T> T read(FileRef ref, Class<T> type) throws IOException { return ControlBuild.strictMapper().treeToValue(readTree(ref), type); }
    private static String text(JsonNode node, String field) throws IOException {
        if (!node.path(field).isTextual()) throw new IOException("Text field required: " + field); return node.path(field).textValue();
    }
    private static FileRef reference(String[] args, int offset) { return new FileRef(args[offset], positive(args[offset + 1]), args[offset + 2]); }
    private static long positive(String value) {
        if (!value.matches("[1-9][0-9]{0,11}")) throw new IllegalArgumentException("Canonical positive integer required");
        return Long.parseLong(value);
    }
    private static long round(long value, long unit) {
        if (value < 0 || unit < 1 || unit > 1L << 20) throw new IllegalArgumentException("Bounded nonnegative bytes and native unit required");
        return Math.multiplyExact(Math.floorDiv(Math.addExact(value, unit - 1), unit), unit);
    }
    private static String key(String value) { return value.replace('\\', '/').toLowerCase(Locale.ROOT); }
    private static Path absolute(String value) {
        Path result = Path.of(value);
        if (!result.isAbsolute() || !result.equals(result.normalize())) throw new IllegalArgumentException("Canonical absolute path required"); return result;
    }
    private static FileRef write(Object report, Path destination, long hard) throws IOException {
        byte[] bytes = ControlBuild.strictMapper().writeValueAsBytes(report);
        if (bytes.length > MAX_OUTPUT || hard > 1L << 20 || !destination.isAbsolute() || !destination.equals(destination.normalize())
                || destination.getParent() == null || !Files.isDirectory(destination.getParent()) || Files.exists(destination))
            throw new IOException("Finite fresh metadata output beneath an existing admitted parent required");
        ProjectStoragePolicy.requireBulkOutput(destination.getParent()); SharedSourceFiles.plainAncestors(destination);
        long unit = NativeStorageGeometry.read(destination.getParent()).clusterBytes();
        if (Math.addExact(unit, round(bytes.length, unit)) > hard) throw new IOException("Complete native metadata bound exceeded");
        Files.write(destination, bytes, StandardOpenOption.CREATE_NEW); FileRef ref = FileRef.measure(destination);
        if (!java.util.Arrays.equals(bytes, Files.readAllBytes(destination))) throw new IOException("Persisted quote metadata differs");
        ref.verify(); return ref;
    }
}

