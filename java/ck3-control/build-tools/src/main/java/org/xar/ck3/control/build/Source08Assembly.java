package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import org.xar.ck3.control.build.CompleteSourceGraph.Component;
import org.xar.ck3.control.build.CompleteSourceGraph.Profile;
import org.xar.ck3.control.build.CompleteSourceGraph.Relocation;
import org.xar.ck3.control.build.CompleteSourceGraph.SelectedFile;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SourceGraphPlanProducer.Layer;
import org.xar.ck3.control.build.SourceGraphPlanProducer.Request;
import org.xar.ck3.control.build.SourceGraphPlanProducer.Winner;

/** Metadata producer feeding the existing typed SourceGraphPlanProducer; it never copies source bodies. */
public final class Source08Assembly {
    public static final String INPUT_SCHEMA = "xar.source08.owner-assembly-input/v1";
    public static final String RELOCATION_INPUT_SCHEMA = "xar.source08.owner-assembly-input/v2";
    public static final String AUDIT_SCHEMA = "xar.source08.owner-assembly-audit/v1";
    private static final int JSON_LIMIT = 8 << 20;

    /** A tools delivery can expose two disjoint layers without relocating any host target. */
    public enum TargetScope {
        ALL, BUILD_TOOLS_ONLY, EXCEPT_BUILD_TOOLS, REACTOR_ONLY;
        public boolean includes(String target) {
            boolean tools = target.startsWith("build-tools/");
            boolean reactor = target.equals("pom.xml") || target.matches("[a-z0-9-]+/(?:pom\\.xml|src/.+|\\.mvn/.+)");
            return this == ALL || this == BUILD_TOOLS_ONLY && tools || this == EXCEPT_BUILD_TOOLS && !tools
                    || this == REACTOR_ONLY && reactor;
        }
    }

    /** selected_files is the only accepted owner export field; no alias or recursive directory discovery. */
    public record OwnerInput(String key, String owner, Component component, TargetScope targetScope,
                             FileRef ownerMapRef) {
        public OwnerInput {
            if (key == null || !key.matches("[a-z0-9][a-z0-9_-]{0,79}")) {
                throw new IllegalArgumentException("explicit finite layer key required");
            }
            if (owner == null || !owner.matches("/root/[a-z0-9_]+")) {
                throw new IllegalArgumentException("explicit current owner required");
            }
            Objects.requireNonNull(component, "component");
            Objects.requireNonNull(targetScope, "target scope");
            Objects.requireNonNull(ownerMapRef, "complete owner map ref");
        }
    }

    /** Decisions name the actual final producer; a missing or stale contested decision is fatal. */
    public record Input(String schema, String machineId, String observedAtUtc, FileRef plan16RequestRef,
                        FileRef source07RequestRef, Profile profile, List<String> modules,
                        List<OwnerInput> owners, List<Winner> replacementWinners, List<Relocation> relocations) {
        public Input {
            if ((!INPUT_SCHEMA.equals(schema) && !RELOCATION_INPUT_SCHEMA.equals(schema)) || machineId == null || machineId.isBlank()) {
                throw new IllegalArgumentException("explicit source08 input schema and machine required");
            }
            Instant.parse(observedAtUtc);
            Objects.requireNonNull(plan16RequestRef, "plan16 request");
            Objects.requireNonNull(source07RequestRef, "source07 request");
            Objects.requireNonNull(profile, "source profile");
            modules = List.copyOf(modules);
            owners = List.copyOf(owners);
            replacementWinners = List.copyOf(replacementWinners);
            relocations = List.copyOf(relocations);
            CompleteSourceGraph.requireRelocationVersion(schema, INPUT_SCHEMA, RELOCATION_INPUT_SCHEMA, relocations);
            if (owners.isEmpty()) throw new IllegalArgumentException("explicit nonempty current owner roster required");
            Set<String> keys = new HashSet<>();
            for (OwnerInput owner : owners) {
                if (!keys.add(owner.key())) throw new IllegalArgumentException("duplicate current owner layer key");
            }
            Set<String> targets = new HashSet<>();
            for (Winner winner : replacementWinners) {
                if (!targets.add(winner.targetRelative())) throw new IllegalArgumentException("duplicate final target decision");
            }
        }
        public Input(String schema, String machineId, String observedAtUtc, FileRef plan16RequestRef,
                     FileRef source07RequestRef, Profile profile, List<String> modules,
                     List<OwnerInput> owners, List<Winner> replacementWinners) {
            this(schema, machineId, observedAtUtc, plan16RequestRef, source07RequestRef, profile, modules,
                    owners, replacementWinners, List.of());
        }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static Input fromWire(JsonNode node) throws IOException {
            if (CompleteSourceGraph.wireSchema(node).equals(INPUT_SCHEMA)) {
                LegacyInput wire = ControlBuild.strictMapper().treeToValue(node, LegacyInput.class);
                return new Input(wire.schema(), wire.machineId(), wire.observedAtUtc(), wire.plan16RequestRef(), wire.source07RequestRef(),
                        wire.profile(), wire.modules(), wire.owners(), wire.replacementWinners());
            }
            RelocatedInput wire = ControlBuild.strictMapper().treeToValue(node, RelocatedInput.class);
            return new Input(wire.schema(), wire.machineId(), wire.observedAtUtc(), wire.plan16RequestRef(), wire.source07RequestRef(),
                    wire.profile(), wire.modules(), wire.owners(), wire.replacementWinners(), wire.relocations());
        }
        @JsonValue public JsonNode toWire() {
            if (schema.equals(INPUT_SCHEMA)) return ControlBuild.strictMapper().valueToTree(new LegacyInput(schema, machineId,
                    observedAtUtc, plan16RequestRef, source07RequestRef, profile, modules, owners, replacementWinners));
            return ControlBuild.strictMapper().valueToTree(new RelocatedInput(schema, machineId, observedAtUtc,
                    plan16RequestRef, source07RequestRef, profile, modules, owners, replacementWinners, relocations));
        }
    }
    private record LegacyInput(String schema, String machineId, String observedAtUtc, FileRef plan16RequestRef,
            FileRef source07RequestRef, Profile profile, List<String> modules, List<OwnerInput> owners, List<Winner> replacementWinners) { }
    private record RelocatedInput(String schema, String machineId, String observedAtUtc, FileRef plan16RequestRef,
            FileRef source07RequestRef, Profile profile, List<String> modules, List<OwnerInput> owners,
            List<Winner> replacementWinners, List<Relocation> relocations) { }

    public record OwnerReadback(String key, String owner, Component component, TargetScope targetScope,
                                FileRef ownerMapRef, int files, long logicalBytes) { }

    public record Audit(String schema, String machineId, String observedAtUtc, String qualification,
                        FileRef inputRef, FileRef plan16RequestRef, FileRef source07RequestRef,
                        int plan16LayersRetained, int source07LayersRetained, List<OwnerReadback> owners,
                        int totalLayers, int contestedTargets, FileRef assemblyRequestRef,
                        boolean sourceBodiesCopied, boolean typedPlanProduced, boolean compiled,
                        boolean gameRun, int ledgerWrites) {
        public Audit { owners = List.copyOf(owners); }
    }

    private Source08Assembly() { }

    /** Runtime-checks the narrow heterogeneous metadata boundary before producing shared selected-file records. */
    public static List<SelectedFile> readOwner(OwnerInput owner, String machineId) throws IOException {
        byte[] bytes = verifiedBytes(owner.ownerMapRef());
        JsonNode root = ControlBuild.strictMapper().readTree(bytes);
        if (!root.isObject() || !root.path("machine_id").isTextual()
                || !machineId.equals(root.path("machine_id").textValue())
                || !root.path("owner").isTextual() || !owner.owner().equals(root.path("owner").textValue())) {
            throw new IOException("owner export machine or owner differs: " + owner.key());
        }
        JsonNode exported = root.get("selected_files");
        if (exported == null || !exported.isArray() || exported.isEmpty()) {
            throw new IOException("complete selected_files array required, not missing/null/empty: " + owner.key());
        }
        List<SelectedFile> files = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        for (JsonNode row : exported) {
            if (!row.isObject() || !row.has("target_relative") || !row.has("source_ref")) {
                throw new IOException("selected_files row requires exact target_relative/source_ref fields");
            }
            JsonNode target = row.get("target_relative");
            if (!target.isTextual() || !row.get("source_ref").isObject()) throw new IOException("typed target/ref required");
            SelectedFile file = new SelectedFile(target.textValue(),
                    ControlBuild.strictMapper().treeToValue(row.get("source_ref"), FileRef.class));
            JsonNode group = row.get("group");
            if (group != null && (!group.isTextual() || !Set.of("TOOLS", "HOST").contains(group.textValue())
                    || group.textValue().equals("TOOLS") != file.targetRelative().startsWith("build-tools/"))) {
                throw new IOException("explicit TOOLS/HOST group must agree with canonical reactor target");
            }
            if (!seen.add(file.targetRelative())) throw new IOException("duplicate exported target: " + file.targetRelative());
            if (!Path.of(file.sourceRef().path()).isAbsolute()) throw new IOException("absolute source path required");
            file.sourceRef().verify();
            if (owner.targetScope().includes(file.targetRelative())) files.add(file);
        }
        if (files.isEmpty()) throw new IOException("owner target scope selects no files: " + owner.key());
        owner.ownerMapRef().verify();
        return List.copyOf(files);
    }

    /** Produces the existing shared Request while retaining every protected original and ancestral owner layer. */
    public static Request prepare(Input input) throws IOException {
        Request plan16 = SourceGraphPlanProducer.readRequest(input.plan16RequestRef());
        Request source07 = SourceGraphPlanProducer.readRequest(input.source07RequestRef());
        if (!input.machineId().equals(plan16.machineId()) || !input.machineId().equals(source07.machineId())
                || !plan16.baseline().equals(source07.baseline()) || source07.layers().size() < plan16.layers().size()
                || !plan16.relocations().isEmpty() || !source07.relocations().isEmpty()
                || !source07.layers().subList(0, plan16.layers().size()).equals(plan16.layers())) {
            throw new IOException("original baseline or complete Plan16 -> Source07 layer ancestry differs");
        }
        // Validate every historical body, including losing candidates, rather than only the final physical tree.
        verifyLayers(plan16.layers());
        verifyLayers(source07.layers());
        List<Layer> layers = new ArrayList<>(source07.layers());
        Set<String> keys = new HashSet<>();
        for (Layer layer : layers) keys.add(layer.key());
        for (OwnerInput owner : input.owners()) {
            if (!keys.add(owner.key())) throw new IOException("current owner key conflicts with historical layer: " + owner.key());
            layers.add(new Layer(owner.key(), owner.component(), owner.ownerMapRef(), readOwner(owner, input.machineId())));
        }
        TreeMap<String, List<String>> producers = producers(layers);
        TreeMap<String, String> winners = new TreeMap<>();
        for (Winner winner : source07.winners()) winners.put(winner.targetRelative(), winner.layerKey());
        for (Winner winner : input.replacementWinners()) winners.put(winner.targetRelative(), winner.layerKey());
        List<Winner> finalWinners = new ArrayList<>();
        for (Map.Entry<String, List<String>> row : producers.entrySet()) {
            if (row.getValue().size() == 1) {
                if (winners.containsKey(row.getKey())) throw new IOException("winner supplied for uncontested target: " + row.getKey());
                continue;
            }
            String chosen = winners.remove(row.getKey());
            if (chosen == null || !row.getValue().contains(chosen)) {
                throw new IOException("explicit actual final producer required: " + row.getKey());
            }
            finalWinners.add(new Winner(row.getKey(), chosen));
        }
        if (!winners.isEmpty()) throw new IOException("stale final decisions outside actual target graph: " + winners.keySet());
        Set<FileRef> currentMaps = new HashSet<>();
        for (OwnerInput owner : input.owners()) currentMaps.add(owner.ownerMapRef());
        for (Relocation move : input.relocations()) {
            if (!currentMaps.contains(move.selectionRef()) || !currentMaps.contains(move.finalSelectionRef())) {
                throw new IOException("original relocation and current revision authorities must be explicit current owner maps");
            }
        }
        return new Request(input.relocations().isEmpty() ? SourceGraphPlanProducer.REQUEST_SCHEMA : SourceGraphPlanProducer.RELOCATION_REQUEST_SCHEMA,
                input.machineId(), input.observedAtUtc(), input.profile(), source07.baseline(), input.modules(), layers,
                finalWinners, input.relocations());
    }

    private static TreeMap<String, List<String>> producers(List<Layer> layers) {
        TreeMap<String, List<String>> result = new TreeMap<>();
        for (Layer layer : layers) for (SelectedFile file : layer.files()) {
            result.computeIfAbsent(file.targetRelative(), unused -> new ArrayList<>()).add(layer.key());
        }
        return result;
    }

    private static void verifyLayers(List<Layer> layers) throws IOException {
        for (Layer layer : layers) {
            layer.ownerMapRef().verify();
            for (SelectedFile file : layer.files()) file.sourceRef().verify();
        }
    }

    private static byte[] verifiedBytes(FileRef ref) throws IOException {
        ref.verify();
        if (ref.bytes() > JSON_LIMIT) throw new IOException("finite input JSON bound exceeded");
        byte[] result = Files.readAllBytes(Path.of(ref.path()));
        ref.verify();
        return result;
    }

    private static FileRef writeNew(Path output, byte[] bytes) throws IOException {
        Path target = output.toAbsolutePath().normalize();
        SharedSourceFiles.plainAncestors(target);
        if (!Files.isDirectory(target.getParent())) throw new IOException("preallocated metadata parent required");
        if (bytes.length > JSON_LIMIT) throw new IOException("finite output JSON bound exceeded");
        Files.write(target, bytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        return FileRef.measure(target);
    }

    /** Root invokes only with a fresh metadata execution card. The separate shared producer creates the typed Plan. */
    public static void main(String[] arguments) throws IOException {
        if (arguments.length != 3) throw new IllegalArgumentException("input.json assembly-request.json audit.json");
        FileRef inputRef = FileRef.measure(Path.of(arguments[0]));
        Input input = ControlBuild.strictMapper().readValue(verifiedBytes(inputRef), Input.class);
        Request request = prepare(input);
        byte[] encoded = ControlBuild.strictMapper().writeValueAsBytes(request);
        if (!request.equals(ControlBuild.strictMapper().readValue(encoded, Request.class))) {
            throw new IOException("typed assembly request serialization roundtrip differs");
        }
        FileRef requestRef = writeNew(Path.of(arguments[1]), encoded);
        if (!request.equals(SourceGraphPlanProducer.readRequest(requestRef))) throw new IOException("actual Request roundtrip differs");
        List<OwnerReadback> owners = new ArrayList<>();
        for (OwnerInput owner : input.owners()) {
            List<SelectedFile> files = readOwner(owner, input.machineId());
            long logical = 0;
            for (SelectedFile file : files) logical = Math.addExact(logical, file.sourceRef().bytes());
            owners.add(new OwnerReadback(owner.key(), owner.owner(), owner.component(), owner.targetScope(),
                    owner.ownerMapRef(), files.size(), logical));
        }
        inputRef.verify();
        Audit audit = new Audit(AUDIT_SCHEMA, input.machineId(), Instant.now().toString(),
                "SOURCE_METADATA_REQUEST_ONLY_NOT_TYPED_PLAN_NOT_MATERIALIZED_NOT_COMPILED", inputRef,
                input.plan16RequestRef(), input.source07RequestRef(),
                SourceGraphPlanProducer.readRequest(input.plan16RequestRef()).layers().size(),
                SourceGraphPlanProducer.readRequest(input.source07RequestRef()).layers().size(), owners,
                request.layers().size(), request.winners().size(), requestRef, false, false, false, false, 0);
        FileRef auditRef = writeNew(Path.of(arguments[2]), ControlBuild.strictMapper().writeValueAsBytes(audit));
        System.out.println("SOURCE08_METADATA_ONLY request=" + requestRef.path() + " sha256=" + requestRef.sha256()
                + " audit=" + auditRef.path() + " sha256=" + auditRef.sha256());
    }
}
