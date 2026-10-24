package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SdkSourceAssembly.*;

/** Exact source selection only. Assembly, deployment rebinding, imports and host lifetime stay with their owners. */
public final class SdkSourceIntent {
    public static final String SCHEMA = "xar.sdk-source-intent/v2";
    public static final String PLAN_SCHEMA = "xar.sdk-source-intent-plan/v2";
    private static final int MAX_METADATA = 2 << 20, MAX_LEAF = 8 << 20;
    private SdkSourceIntent() { }
    public enum View { BASELINE, LEGACY, CONSUMER }
    public enum SelectionKind { REPLACE_CONTENT, APPLY_EXACT_PATCH, ADD_SOURCE }
    public record RequiredReactorSource(String relativePath, Digest content) {
        public RequiredReactorSource { ExactSourcePatch.relative(relativePath); Objects.requireNonNull(content); }
    }
    public record Cohort(String owner, List<String> producers, List<String> consumers,
                         List<String> serialization, List<FileRef> evidenceRefs) {
        public Cohort {
            ownerName(owner); producers = paths(producers); consumers = paths(consumers); serialization = paths(serialization);
            evidenceRefs = List.copyOf(evidenceRefs);
            if (producers.isEmpty() || consumers.isEmpty() || serialization.isEmpty() || evidenceRefs.isEmpty())
                throw new IllegalArgumentException("Explicit producer, all consumer and serialization source intent plus evidence required");
        }
    }
    public record Selection(SelectionKind kind, String owner, String relativePath, SourceRole role,
                            Source expectedTemplateSource, FileRef selectedSource, List<Overlay> selectedOverlays,
                            List<ImportRoute> importRoutes) {
        public Selection {
            Objects.requireNonNull(kind); ownerName(owner); ExactSourcePatch.relative(relativePath);
            Objects.requireNonNull(role); Objects.requireNonNull(selectedSource); selectedOverlays = List.copyOf(selectedOverlays); importRoutes = List.copyOf(importRoutes);
            if (selectedSource.bytes() > MAX_LEAF || (kind == SelectionKind.ADD_SOURCE) != (expectedTemplateSource == null))
                throw new IllegalArgumentException("Explicit absent or exact template preimage required");
            if (kind == SelectionKind.REPLACE_CONTENT && !selectedOverlays.isEmpty()) throw new IllegalArgumentException("Replacement selects an exact full postimage");
            if (kind == SelectionKind.APPLY_EXACT_PATCH && (selectedOverlays.size() != 1 || !selectedSource.equals(expectedTemplateSource.original())))
                throw new IllegalArgumentException("Patch selection retains the exact original source and one explicit original-base overlay");
            if (expectedTemplateSource != null && (!expectedTemplateSource.relativePath().equals(relativePath) || expectedTemplateSource.role() != role))
                throw new IllegalArgumentException("Template role and source address must be retained");
            for (var route : importRoutes) if (!route.relativeSource().equals(relativePath) || route.location() != ImportSourceLocation.FRESH_GRAPH)
                throw new IllegalArgumentException("Selected module must bind this fresh physical source");
        }
    }
    public record ReferenceInputs(List<Source> additions, List<ImportRoute> importRoutes) {
        public ReferenceInputs {
            additions = List.copyOf(additions); importRoutes = List.copyOf(importRoutes);
            if (additions.size() > 64 || importRoutes.size() > 128) throw new IllegalArgumentException("Bounded original reference inputs required");
            for (Source source : additions) if (!originalReference(source)) throw new IllegalArgumentException("Reference additions must preserve exact unpatched canonical original tests");
            for (ImportRoute route : importRoutes) if (route.location() != ImportSourceLocation.FRESH_GRAPH) throw new IllegalArgumentException("Reference imports must use the reviewed view path");
        }
    }
    private static boolean originalReference(Source source) {
        String file = Path.of(source.relativePath()).getFileName().toString();
        return source.role() == SourceRole.ORIGINAL_CONSUMER_TEST && source.origin() == InputOrigin.CURRENT_CANONICAL && source.overlays().isEmpty()
                && file.startsWith("test_") && file.endsWith(".py");
    }
    public record Plan(String schema, String machineId, String reviewAtUtc, FileRef baselineTemplateRef,
                       FileRef legacyTemplateRef, FileRef consumerTemplateRef, ReferenceInputs referenceInputs, List<Selection> consumerSelections,
                       List<Cohort> cohorts, List<RequiredReactorSource> requiredReactorSources) {
        public Plan {
            if (!PLAN_SCHEMA.equals(schema)) throw new IllegalArgumentException("Versioned source selection plan required");
            machine(machineId); Instant.parse(reviewAtUtc); Objects.requireNonNull(baselineTemplateRef);
            Objects.requireNonNull(legacyTemplateRef); Objects.requireNonNull(consumerTemplateRef); Objects.requireNonNull(referenceInputs);
            consumerSelections = List.copyOf(consumerSelections); cohorts = List.copyOf(cohorts);
            requiredReactorSources = reactorSources(requiredReactorSources);
            if (consumerSelections.isEmpty() || consumerSelections.size() > 512 || cohorts.isEmpty() || cohorts.size() > 32)
                throw new IllegalArgumentException("Finite explicit current consumer selection and cohorts required");
            var seen = new LinkedHashSet<String>();
            for (var selection : consumerSelections) if (!seen.add(key(selection.relativePath()))) throw new IllegalArgumentException("Conflicting selected target");
        }
    }
    public record Replacement(SelectionKind kind, Source expectedTemplateSource, FileRef selectedSource, Overlay overlay) {
        public Replacement {
            Objects.requireNonNull(kind); Objects.requireNonNull(expectedTemplateSource); Objects.requireNonNull(selectedSource); Objects.requireNonNull(overlay);
            if (kind == SelectionKind.ADD_SOURCE || (kind == SelectionKind.APPLY_EXACT_PATCH && !selectedSource.equals(expectedTemplateSource.original())))
                throw new IllegalArgumentException("Explicit full-content or retained-original patch replacement required");
        }
    }
    public record Intent(String schema, String machineId, String reviewAtUtc, View view, FileRef templateRequestRef,
                         List<Replacement> replacements, List<Source> additions, List<ImportRoute> importRoutes,
                         List<String> approvedSourceRoots, List<Cohort> cohorts, List<RequiredReactorSource> requiredReactorSources) {
        public Intent {
            if (!SCHEMA.equals(schema)) throw new IllegalArgumentException("Versioned exact source intent required");
            machine(machineId); Instant.parse(reviewAtUtc); Objects.requireNonNull(view); Objects.requireNonNull(templateRequestRef);
            replacements = List.copyOf(replacements); additions = List.copyOf(additions); importRoutes = List.copyOf(importRoutes);
            approvedSourceRoots = List.copyOf(approvedSourceRoots); cohorts = List.copyOf(cohorts);
            requiredReactorSources = reactorSources(requiredReactorSources);
            if (replacements.size() + additions.size() > 512 || approvedSourceRoots.size() > 32 || cohorts.size() > 32)
                throw new IllegalArgumentException("Finite source intent required");
            if (view != View.CONSUMER && (!replacements.isEmpty() || additions.stream().anyMatch(source -> !originalReference(source))))
                throw new IllegalArgumentException("Reference views permit only exact unpatched canonical original test additions");
            for (String root : approvedSourceRoots) absolute(root);
        }
    }
    public record ResolvedIntent(Request request, List<FileRef> inputRefs, List<RequiredReactorSource> requiredReactorSources) {
        public ResolvedIntent { Objects.requireNonNull(request); inputRefs = List.copyOf(inputRefs); requiredReactorSources = reactorSources(requiredReactorSources); }
    }
    public record PreparedIntents(FileRef baselineIntentRef, FileRef legacyIntentRef, FileRef consumerIntentRef,
                                  List<FileRef> generatedRefs, List<FileRef> inputRefs) {
        public PreparedIntents { generatedRefs = List.copyOf(generatedRefs); inputRefs = List.copyOf(inputRefs); }
    }
    @FunctionalInterface public interface MetadataGuard { void revalidate(long pendingBytes) throws IOException; }

    /** Finite mechanical CLI; process ownership and the full input-manifest guard belong to the shared caller. */
    public static void main(String[] args) throws IOException {
        if (args.length != 5) throw new IllegalArgumentException("PLAN_PATH BYTES SHA256 NEW_OUTPUT_ROOT MAX_NATIVE_BYTES");
        FileRef plan = new FileRef(args[0], Long.parseLong(args[1]), args[2]); Path output = absolute(args[3]);
        long maximum = Long.parseLong(args[4]);
        if (maximum < 1 || maximum > 16L << 20) throw new IllegalArgumentException("Explicit metadata-only native bound required");
        MetadataGuard guard = pending -> {
            long used = 0;
            if (Files.exists(output)) try (var entries = Files.walk(output)) {
                for (Path path : entries.toList()) {
                    SharedSourceFiles.plainAncestors(path);
                    used = Math.addExact(used, Files.isDirectory(path) ? 4096 : SharedSourceFiles.nativeFile(path).allocatedBytes());
                }
            }
            long reserved = pending == 0 ? 0 : Math.addExact(pending, 4095) / 4096 * 4096;
            if (Math.addExact(used, reserved) > maximum) throw new IOException("Mechanical intent output exceeds admitted native bound");
        };
        PreparedIntents prepared = prepare(plan, output, guard);
        byte[] encoded = ControlBuild.strictMapper().writeValueAsBytes(prepared); guard.revalidate(encoded.length);
        Path receipt = output.resolve("prepared-intents.json"); Files.write(receipt, encoded, StandardOpenOption.CREATE_NEW); guard.revalidate(0);
        System.out.println(ControlBuild.strictMapper().writeValueAsString(FileRef.measure(receipt)));
    }

    public static ResolvedIntent resolve(FileRef intentRef) throws IOException {
        Intent intent = read(intentRef, Intent.class); current(intent.reviewAtUtc());
        Request template = SdkSourceAssembly.readRequest(intent.templateRequestRef());
        if (!template.machineId().equals(intent.machineId())) throw new IOException("Intent/template machine mismatch");
        var sources = sourceMap(template); var refs = new ArrayList<FileRef>(List.of(intentRef, intent.templateRequestRef()));
        collect(template, refs);
        var modified = new LinkedHashSet<String>();
        for (var replacement : intent.replacements()) {
            Source before = replacement.expectedTemplateSource(); String name = key(before.relativePath());
            if (!before.equals(sources.get(name)) || !modified.add(name)) throw new IOException("Exact source preimage differs or target repeats");
            replacement.selectedSource().verify(); refs.add(replacement.selectedSource()); refs.add(replacement.overlay().patchRef());
            byte[] original = bytes(before.original()); Overlay overlay = replacement.overlay();
            if (overlay.baseMode() != OverlayBase.ORIGINAL_SOURCE || !overlay.patchTarget().equals(before.relativePath())
                    || !overlay.standaloneBase().equals(Digest.of(original)))
                throw new IOException("Selected overlay does not bind the retained original source");
            byte[] actual = ExactSourcePatch.apply(original, bytes(overlay.patchRef()), overlay.syntax(), overlay.patchTarget()).bytes();
            if (!Digest.of(actual).equals(overlay.standaloneResult()) || Digest.of(actual).equals(Digest.of(original)))
                throw new IOException("Selected patch exact postimage digest differs or is unchanged");
            if (replacement.kind() == SelectionKind.REPLACE_CONTENT && !Arrays.equals(actual, bytes(replacement.selectedSource())))
                throw new IOException("Selected patch differs from the actual supplied full postimage");
            sources.put(name, new Source(before.relativePath(), before.role(), before.origin(), before.original(), List.of(overlay)));
        }
        for (Source addition : intent.additions()) {
            if ((addition.origin() != InputOrigin.STAGED_NEW_SOURCE && !originalReference(addition))
                    || sources.putIfAbsent(key(addition.relativePath()), addition) != null) throw new IOException("New source must be an absent exact staged input");
            addition.original().verify(); refs.add(addition.original());
            for (int index = 0; index < addition.overlays().size(); index++) {
                refs.add(addition.overlays().get(index).patchRef());
                SdkSourceAssembly.standaloneMaterial(addition, bytes(addition.original()), index);
            }
        }
        var routes = new LinkedHashMap<String, ImportRoute>();
        for (var route : template.importRoutes()) routes.put(route.module(), route);
        for (var route : intent.importRoutes()) {
            if (!sources.containsKey(key(route.relativeSource())) || route.location() != ImportSourceLocation.FRESH_GRAPH)
                throw new IOException("Import route must select an existing fresh source");
            Source selected = sources.get(key(route.relativeSource()));
            if (intent.view() != View.CONSUMER && (selected.role() != SourceRole.ORIGINAL_CONSUMER_TEST || selected.origin() != InputOrigin.CURRENT_CANONICAL))
                throw new IOException("Reference route may expose only an exact canonical original test through its view");
            ImportRoute prior = routes.putIfAbsent(route.module(), route);
            if (prior != null && !prior.equals(route)) throw new IOException("Conflicting selected import route");
        }
        var roots = new LinkedHashSet<String>(template.approvedInputSourceRoots()); roots.addAll(intent.approvedSourceRoots());
        if (roots.size() > 32) throw new IOException("Explicit approved input roots exceed existing assembly contract");
        for (var cohort : intent.cohorts()) {
            for (var group : List.of(cohort.producers(), cohort.consumers(), cohort.serialization()))
                for (String path : group) if (!sources.containsKey(key(path))) throw new IOException("Selected cohort closure source absent: " + path);
            refs.addAll(cohort.evidenceRefs());
        }
        if (intent.view() == View.BASELINE && sources.values().stream().anyMatch(value -> !value.overlays().isEmpty()))
            throw new IOException("Baseline must remain exact and unpatched");
        Request result = new Request(template.schema(), template.machineId(), template.canonicalRepository(), template.canonicalCommit(),
                template.canonicalTestRepository(), template.outputRoot(), template.sdkInputRoot(), template.sdkRelativeRoot(), template.importRoots(),
                List.copyOf(roots), template.protectedRoots(), List.copyOf(sources.values()), List.copyOf(routes.values()), template.deployments(),
                template.producerReuse(), template.outputHardBytes());
        for (Source addition : intent.additions()) if (originalReference(addition)) SdkSourceAssembly.validateSourceOrigin(result, addition);
        for (var ref : unique(refs)) ref.verify(); current(intent.reviewAtUtc());
        return new ResolvedIntent(result, unique(refs), intent.requiredReactorSources());
    }

    private static Source originalTestAddition(Selection selection, Request template) throws IOException {
        Source original = new Source(selection.relativePath(), selection.role(), InputOrigin.CURRENT_CANONICAL,
                selection.selectedSource(), selection.selectedOverlays());
        if (!originalReference(original)) throw new IOException("Original consumer additions require an exact unpatched canonical test source");
        SdkSourceAssembly.validateSourceOrigin(template, original);
        return original;
    }

    /** Writes mechanical patches/intents and small exact input byte copies; never synthesizes source code or assembles a graph. */
    public static PreparedIntents prepare(FileRef planRef, Path outputRoot, MetadataGuard guard) throws IOException {
        Plan plan = read(planRef, Plan.class); current(plan.reviewAtUtc()); Objects.requireNonNull(guard);
        Request baseline = SdkSourceAssembly.readRequest(plan.baselineTemplateRef()), legacy = SdkSourceAssembly.readRequest(plan.legacyTemplateRef()),
                consumer = SdkSourceAssembly.readRequest(plan.consumerTemplateRef());
        requireTemplates(plan.machineId(), baseline, legacy, consumer);
        Path output = outputRoot.toAbsolutePath().normalize(); SharedSourceFiles.plainAncestors(output);
        if (Files.exists(output) || !Files.isDirectory(output.getParent())) throw new IOException("New exact metadata output with existing admitted parent required");
        var replacements = new ArrayList<Replacement>(); var additions = new ArrayList<Source>(); var routes = new ArrayList<ImportRoute>();
        var roots = new LinkedHashSet<String>(); var inputs = new ArrayList<FileRef>(List.of(planRef, plan.baselineTemplateRef(), plan.legacyTemplateRef(), plan.consumerTemplateRef()));
        var sourceMap = sourceMap(consumer); var generated = new ArrayList<FileRef>();
        var reference = plan.referenceInputs();
        for (Source source : reference.additions()) {
            for (Request template : List.of(baseline, legacy, consumer)) {
                if (sourceMap(template).containsKey(key(source.relativePath()))) throw new IOException("Reference addition must be absent from every preserved template");
                SdkSourceAssembly.validateSourceOrigin(template, source);
            }
            inputs.add(source.original());
        }
        for (var template : List.of(baseline, legacy, consumer)) collect(template, inputs);
        for (var selection : plan.consumerSelections()) {
            if (!Objects.equals(sourceMap.get(key(selection.relativePath())), selection.expectedTemplateSource())) throw new IOException("Plan selected source preimage differs");
            selection.selectedSource().verify(); inputs.add(selection.selectedSource()); routes.addAll(selection.importRoutes());
            if (selection.kind() == SelectionKind.ADD_SOURCE && selection.role() == SourceRole.ORIGINAL_CONSUMER_TEST)
                originalTestAddition(selection, consumer);
            roots.add(Path.of(selection.selectedSource().path()).toAbsolutePath().normalize().getParent().toString());
            for (var overlay : selection.selectedOverlays()) { inputs.add(overlay.patchRef()); roots.add(absolute(overlay.patchRef().path()).getParent().toString()); }
        }
        for (var cohort : plan.cohorts()) inputs.addAll(cohort.evidenceRefs());
        for (var input : unique(inputs)) input.verify();
        guard.revalidate(8192); Files.createDirectory(output);
        int index = 0;
        for (var selection : plan.consumerSelections()) {
            current(plan.reviewAtUtc());
            if (selection.kind() == SelectionKind.ADD_SOURCE) {
                if (selection.role() == SourceRole.ORIGINAL_CONSUMER_TEST) {
                    additions.add(originalTestAddition(selection, consumer));
                    continue;
                }
                FileRef selected = selection.selectedSource();
                if (absolute(selected.path()).startsWith(absolute(consumer.canonicalRepository()))) {
                    byte[] raw = bytes(selected); guard.revalidate(raw.length);
                    Path copy = output.resolve(String.format(Locale.ROOT, "selected-input-%04d.bin", index++));
                    Files.write(copy, raw, StandardOpenOption.CREATE_NEW); FileRef copied = FileRef.measure(copy);
                    if (!Digest.of(raw).equals(new Digest(copied.bytes(), copied.sha256()))) throw new IOException("Exact support input staging changed bytes");
                    generated.add(copied); selected = copied;
                }
                additions.add(new Source(selection.relativePath(), selection.role(), InputOrigin.STAGED_NEW_SOURCE, selected, selection.selectedOverlays()));
            } else if (selection.kind() == SelectionKind.APPLY_EXACT_PATCH) {
                Source before = selection.expectedTemplateSource(); Overlay overlay = selection.selectedOverlays().getFirst();
                if (!overlay.owner().equals(selection.owner()) || overlay.baseMode() != OverlayBase.ORIGINAL_SOURCE
                        || !overlay.patchTarget().equals(before.relativePath()) || !overlay.standaloneBase().equals(new Digest(before.original().bytes(), before.original().sha256())))
                    throw new IOException("Patch selection must bind the exact retained original owner, target and source digest");
                byte[] merged = ExactSourcePatch.apply(bytes(before.original()), bytes(overlay.patchRef()), overlay.syntax(), overlay.patchTarget()).bytes();
                if (!Digest.of(merged).equals(overlay.standaloneResult()) || overlay.standaloneResult().equals(overlay.standaloneBase()))
                    throw new IOException("Patch selection exact postimage differs or has no change");
                replacements.add(new Replacement(selection.kind(), before, selection.selectedSource(), overlay));
            } else {
                Source before = selection.expectedTemplateSource(); byte[] original = bytes(before.original()), selected = bytes(selection.selectedSource());
                byte[] patch = exactPatch(selection.relativePath(), original, selected);
                if (patch.length > 1024 * 1024) throw new IOException("Mechanical patch exceeds existing assembly overlay bound");
                Path path = output.resolve(String.format(Locale.ROOT, "source-%04d.patch", index++)); guard.revalidate(patch.length);
                Files.write(path, patch, StandardOpenOption.CREATE_NEW); FileRef patchRef = FileRef.measure(path); generated.add(patchRef);
                Overlay overlay = new Overlay(selection.owner(), OverlayBase.ORIGINAL_SOURCE, patchRef, ExactSourcePatch.Syntax.UNIFIED_DIFF,
                        selection.relativePath(), Digest.of(original), Digest.of(selected));
                replacements.add(new Replacement(selection.kind(), before, selection.selectedSource(), overlay));
            }
        }
        roots.removeIf(root -> consumer.approvedInputSourceRoots().stream()
                .anyMatch(inherited -> absolute(root).startsWith(absolute(inherited))));
        roots.add(output.toString()); List<String> approved = minimalRoots(List.copyOf(roots));
        var consumerAdditions = new ArrayList<Source>(reference.additions()); consumerAdditions.addAll(additions);
        var consumerRoutes = new ArrayList<ImportRoute>(reference.importRoutes()); consumerRoutes.addAll(routes);
        var views = List.of(new Intent(SCHEMA, plan.machineId(), plan.reviewAtUtc(), View.BASELINE, plan.baselineTemplateRef(), List.of(), reference.additions(), reference.importRoutes(), List.of(), List.of(), List.of()),
                new Intent(SCHEMA, plan.machineId(), plan.reviewAtUtc(), View.LEGACY, plan.legacyTemplateRef(), List.of(), reference.additions(), reference.importRoutes(), List.of(), List.of(), List.of()),
                new Intent(SCHEMA, plan.machineId(), plan.reviewAtUtc(), View.CONSUMER, plan.consumerTemplateRef(), replacements, consumerAdditions, consumerRoutes, approved, plan.cohorts(), plan.requiredReactorSources()));
        var intentRefs = new ArrayList<FileRef>();
        for (Intent intent : views) {
            byte[] encoded = ControlBuild.strictMapper().writeValueAsBytes(intent);
            if (encoded.length > MAX_METADATA) throw new IOException("Bounded intent metadata required"); guard.revalidate(encoded.length);
            Path path = output.resolve(intent.view().name().toLowerCase(Locale.ROOT) + "-intent.json"); Files.write(path, encoded, StandardOpenOption.CREATE_NEW);
            FileRef ref = FileRef.measure(path); resolve(ref); intentRefs.add(ref); generated.add(ref);
        }
        for (FileRef ref : unique(inputs)) ref.verify(); current(plan.reviewAtUtc()); guard.revalidate(0);
        return new PreparedIntents(intentRefs.get(0), intentRefs.get(1), intentRefs.get(2), generated, unique(inputs));
    }

    static byte[] exactPatch(String target, byte[] original, byte[] selected) throws IOException {
        ExactSourcePatch.relative(target);
        if (original.length == 0) throw new IOException("An existing-source delta requires nonempty exact context; new sources use ADD_SOURCE");
        if (Arrays.equals(original, selected)) throw new IOException("No-change selection is not a source delta");
        List<Line> oldLines = lines(original), newLines = lines(selected); int prefix = 0, suffix = 0;
        while (prefix < oldLines.size() && prefix < newLines.size() && oldLines.get(prefix).equals(newLines.get(prefix))) prefix++;
        while (suffix < oldLines.size() - prefix && suffix < newLines.size() - prefix
                && oldLines.get(oldLines.size() - suffix - 1).equals(newLines.get(newLines.size() - suffix - 1))) suffix++;
        int first = Math.max(0, prefix - 3), oldEnd = Math.min(oldLines.size(), oldLines.size() - suffix + 3), newEnd = Math.min(newLines.size(), newLines.size() - suffix + 3);
        int oldCount = oldEnd - first, newCount = newEnd - first;
        var text = new StringBuilder("--- a/" + target + "\n+++ b/" + target + "\n@@ -" + (oldCount == 0 ? first : first + 1) + "," + oldCount
                + " +" + (newCount == 0 ? first : first + 1) + "," + newCount + " @@\n");
        for (int at = first; at < prefix; at++) append(text, ' ', oldLines.get(at));
        for (int at = prefix; at < oldLines.size() - suffix; at++) append(text, '-', oldLines.get(at));
        for (int at = prefix; at < newLines.size() - suffix; at++) append(text, '+', newLines.get(at));
        for (int at = oldLines.size() - suffix; at < oldEnd; at++) append(text, ' ', oldLines.get(at));
        byte[] patch = text.toString().getBytes(StandardCharsets.UTF_8);
        if (!Arrays.equals(selected, ExactSourcePatch.apply(original, patch, ExactSourcePatch.Syntax.UNIFIED_DIFF, target).bytes()))
            throw new IOException("Exact existing patch codec cannot represent supplied source bytes; no newline or encoding normalization allowed");
        return patch;
    }
    private record Line(String text, boolean terminated) { }
    private static List<Line> lines(byte[] raw) throws IOException {
        String value = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
        var result = new ArrayList<Line>(); int start = 0;
        for (int at = 0; at < value.length(); at++) if (value.charAt(at) == '\n') {
            String line = value.substring(start, at); if (line.endsWith("\r")) line = line.substring(0, line.length() - 1);
            result.add(new Line(line, true)); start = at + 1;
        }
        if (start < value.length()) result.add(new Line(value.substring(start), false)); return List.copyOf(result);
    }
    private static void append(StringBuilder text, char prefix, Line line) {
        text.append(prefix).append(line.text()).append('\n'); if (!line.terminated()) text.append("\\ No newline at end of file\n");
    }
    private static void requireTemplates(String machine, Request base, Request legacy, Request consumer) throws IOException {
        if (!base.machineId().equals(machine) || !legacy.machineId().equals(machine) || !consumer.machineId().equals(machine)
                || base.sources().stream().anyMatch(source -> !source.overlays().isEmpty())) throw new IOException("Same-machine original unpatched baseline required");
        var original = sourceMap(base);
        if (!sourceMap(legacy).keySet().equals(original.keySet()) || !sourceMap(consumer).keySet().containsAll(original.keySet())) throw new IOException("Reference closure omitted");
        for (var view : List.of(legacy, consumer)) for (var source : original.values()) {
            Source selected = sourceMap(view).get(key(source.relativePath()));
            if (!selected.original().equals(source.original()) || selected.role() != source.role()) throw new IOException("Reference original source and role must be retained");
        }
    }
    private static LinkedHashMap<String, Source> sourceMap(Request request) {
        var result = new LinkedHashMap<String, Source>(); for (var source : request.sources()) result.put(key(source.relativePath()), source); return result;
    }
    private static void collect(Request request, List<FileRef> refs) {
        for (var source : request.sources()) { refs.add(source.original()); for (var overlay : source.overlays()) refs.add(overlay.patchRef()); }
    }
    private static List<String> minimalRoots(List<String> roots) {
        var result = new ArrayList<String>();
        for (String root : roots) if (roots.stream().noneMatch(other -> !other.equals(root) && absolute(root).startsWith(absolute(other)))) result.add(root);
        return List.copyOf(result);
    }
    private static List<FileRef> unique(List<FileRef> refs) {
        var result = new LinkedHashMap<String, FileRef>();
        for (var ref : refs) {
            String name = key(absolute(ref.path()).toString()); FileRef previous = result.putIfAbsent(name, ref);
            if (previous != null && !previous.equals(ref)) throw new IllegalArgumentException("Conflicting exact source reference");
        }
        return List.copyOf(result.values());
    }
    private static <T> T read(FileRef ref, Class<T> type) throws IOException {
        if (ref.bytes() < 1 || ref.bytes() > MAX_METADATA) throw new IOException("Bounded intent/plan metadata required");
        ref.verify(); T result = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(ref.path())), type); ref.verify(); return result;
    }
    private static byte[] bytes(FileRef ref) throws IOException { if (ref.bytes() > MAX_LEAF) throw new IOException("Bounded existing source required"); ref.verify(); byte[] raw = Files.readAllBytes(Path.of(ref.path())); ref.verify(); return raw; }
    private static void current(String review) throws IOException { if (!Instant.now().isBefore(Instant.parse(review))) throw new IOException("Source intent review expired"); }
    private static List<String> paths(List<String> values) { values = List.copyOf(values); for (String path : values) ExactSourcePatch.relative(path); return values; }
    private static List<RequiredReactorSource> reactorSources(List<RequiredReactorSource> values) {
        values = List.copyOf(values); var names = new LinkedHashSet<String>();
        if (values.size() > 512) throw new IllegalArgumentException("Bounded exact paired reactor source requirements required");
        for (var value : values) if (!names.add(key(value.relativePath()))) throw new IllegalArgumentException("Duplicate paired reactor source requirement");
        return values;
    }
    private static Path absolute(String value) { Path path = Path.of(value); if (!path.isAbsolute()) throw new IllegalArgumentException("Exact absolute input root required"); return path.toAbsolutePath().normalize(); }
    private static String key(String value) { return value.replace('\\', '/').toLowerCase(Locale.ROOT); }
    private static void machine(String value) { if (value == null || !value.matches("[a-z0-9][a-z0-9-]{2,127}")) throw new IllegalArgumentException("Exact machine required"); }
    private static void ownerName(String value) { if (value == null || !value.matches("[a-z0-9][a-z0-9_-]{0,63}")) throw new IllegalArgumentException("Explicit owner required"); }
}
