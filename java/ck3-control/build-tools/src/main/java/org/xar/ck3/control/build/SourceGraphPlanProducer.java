package org.xar.ck3.control.build;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import org.xar.ck3.control.build.CompleteSourceGraph.Baseline;
import org.xar.ck3.control.build.CompleteSourceGraph.Component;
import org.xar.ck3.control.build.CompleteSourceGraph.ComponentSelection;
import org.xar.ck3.control.build.CompleteSourceGraph.Overlay;
import org.xar.ck3.control.build.CompleteSourceGraph.Plan;
import org.xar.ck3.control.build.CompleteSourceGraph.Preimage;
import org.xar.ck3.control.build.CompleteSourceGraph.Profile;
import org.xar.ck3.control.build.CompleteSourceGraph.Relocation;
import org.xar.ck3.control.build.CompleteSourceGraph.SelectedFile;
import org.xar.ck3.control.build.CompleteSourceGraph.SelectionStatus;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Actual typed Plan producer. Root supplies final source rows and resolves every producer conflict explicitly. */
public final class SourceGraphPlanProducer {
    public static final String REQUEST_SCHEMA = "xar.complete-java-source-assembly-request/v1";
    public static final String RELOCATION_REQUEST_SCHEMA = "xar.complete-java-source-assembly-request/v2";
    private static final int JSON_LIMIT = 8 << 20;
    public record Layer(String key, Component component, FileRef ownerMapRef, List<SelectedFile> files) {
        public Layer {
            if (key == null || !key.matches("[a-z0-9][a-z0-9_-]{0,79}")) throw new IllegalArgumentException("explicit layer key required");
            Objects.requireNonNull(component, "component"); Objects.requireNonNull(ownerMapRef, "owner source map");
            files = List.copyOf(files);
            if (files.isEmpty()) throw new IllegalArgumentException("nonempty owner source selection required");
            Set<String> targets = new HashSet<>();
            for (SelectedFile file : files) {
                if (!targets.add(file.targetRelative())) throw new IllegalArgumentException("duplicate owner map target");
                if (component == Component.BUILD_TOOLS && !file.targetRelative().startsWith("build-tools/")) {
                    throw new IllegalArgumentException("tools-only rows must be explicitly relocated to build-tools/");
                }
            }
        }
    }
    public record Winner(String targetRelative, String layerKey) {
        public Winner {
            if (targetRelative == null || targetRelative.isBlank() || layerKey == null || layerKey.isBlank()) {
                throw new IllegalArgumentException("explicit contested target and selected layer required");
            }
        }
    }
    public record Request(String schema, String machineId, String observedAtUtc, Profile profile, Baseline baseline,
                          List<String> modules, List<Layer> layers, List<Winner> winners, List<Relocation> relocations) {
        public Request {
            if ((!REQUEST_SCHEMA.equals(schema) && !RELOCATION_REQUEST_SCHEMA.equals(schema)) || machineId == null || machineId.isBlank()) {
                throw new IllegalArgumentException("explicit source assembly schema and machine required");
            }
            Instant.parse(observedAtUtc); Objects.requireNonNull(profile, "profile"); Objects.requireNonNull(baseline, "baseline");
            modules = List.copyOf(modules); layers = List.copyOf(layers); winners = List.copyOf(winners);
            relocations = List.copyOf(relocations);
            CompleteSourceGraph.requireRelocationVersion(schema, REQUEST_SCHEMA, RELOCATION_REQUEST_SCHEMA, relocations);
            Set<String> keys = new HashSet<>();
            for (Layer layer : layers) if (!keys.add(layer.key())) throw new IllegalArgumentException("duplicate owner layer key");
            Set<String> targets = new HashSet<>();
            for (Winner winner : winners) if (!targets.add(winner.targetRelative())) throw new IllegalArgumentException("two explicit winners for target");
        }
        public Request(String schema, String machineId, String observedAtUtc, Profile profile, Baseline baseline,
                       List<String> modules, List<Layer> layers, List<Winner> winners) {
            this(schema, machineId, observedAtUtc, profile, baseline, modules, layers, winners, List.of());
        }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static Request fromWire(JsonNode node) throws IOException {
            if (CompleteSourceGraph.wireSchema(node).equals(REQUEST_SCHEMA)) {
                LegacyRequest wire = ControlBuild.strictMapper().treeToValue(node, LegacyRequest.class);
                return new Request(wire.schema(), wire.machineId(), wire.observedAtUtc(), wire.profile(), wire.baseline(),
                        wire.modules(), wire.layers(), wire.winners());
            }
            RelocatedRequest wire = ControlBuild.strictMapper().treeToValue(node, RelocatedRequest.class);
            return new Request(wire.schema(), wire.machineId(), wire.observedAtUtc(), wire.profile(), wire.baseline(),
                    wire.modules(), wire.layers(), wire.winners(), wire.relocations());
        }
        @JsonValue public JsonNode toWire() {
            if (schema.equals(REQUEST_SCHEMA)) return ControlBuild.strictMapper().valueToTree(new LegacyRequest(schema,
                    machineId, observedAtUtc, profile, baseline, modules, layers, winners));
            return ControlBuild.strictMapper().valueToTree(new RelocatedRequest(schema, machineId, observedAtUtc,
                    profile, baseline, modules, layers, winners, relocations));
        }
    }
    private record LegacyRequest(String schema, String machineId, String observedAtUtc, Profile profile, Baseline baseline,
            List<String> modules, List<Layer> layers, List<Winner> winners) { }
    private record RelocatedRequest(String schema, String machineId, String observedAtUtc, Profile profile, Baseline baseline,
            List<String> modules, List<Layer> layers, List<Winner> winners, List<Relocation> relocations) { }
    private SourceGraphPlanProducer() { }

    public static Request readRequest(FileRef requestRef) throws IOException {
        requestRef.verify();
        if (requestRef.bytes() > JSON_LIMIT) throw new IOException("finite assembly request bound exceeded");
        Request result = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(requestRef.path())), Request.class);
        requestRef.verify(); return result;
    }

    /** Preserves original move authority and separately verifies each explicit current owner revision. */
    public static Plan produce(FileRef requestRef) throws IOException {
        Request request = readRequest(requestRef);
        // The protected baseline decoder and validator have one implementation in the shared contract.
        Path baselineRoot = Path.of(request.baseline().root()).toAbsolutePath().normalize();
        TreeMap<String, FileRef> originals = new TreeMap<>();
        for (FileRef ref : CompleteSourceGraph.baselineFiles(request.baseline())) {
            String target = baselineRoot.relativize(Path.of(ref.path()).toAbsolutePath().normalize()).toString().replace('\\', '/');
            originals.put(target, ref);
        }
        TreeMap<String, List<Layer>> producers = new TreeMap<>();
        for (Layer layer : request.layers()) {
            layer.ownerMapRef().verify();
            for (SelectedFile file : layer.files()) {
                file.sourceRef().verify(); producers.computeIfAbsent(file.targetRelative(), unused -> new ArrayList<>()).add(layer);
            }
        }
        for (Relocation move : request.relocations()) {
            boolean originalAuthority = request.layers().stream().anyMatch(layer -> layer.ownerMapRef().equals(move.selectionRef())
                    && layer.files().contains(new SelectedFile(move.newTargetRelative(), move.sourceRef())));
            boolean currentAuthority = request.layers().stream().anyMatch(layer -> layer.ownerMapRef().equals(move.finalSelectionRef())
                    && layer.files().contains(new SelectedFile(move.finalOwnerTargetRelative(), move.finalSourceRef())));
            if (!originalAuthority || !currentAuthority) throw new IOException("relocation authorities must be actual explicit source layers");
        }
        TreeMap<String, String> winners = new TreeMap<>();
        for (Winner winner : request.winners()) winners.put(winner.targetRelative(), winner.layerKey());
        Set<String> consumedWinners = new HashSet<>();
        EnumMap<Component, List<SelectedFile>> componentFiles = new EnumMap<>(Component.class);
        List<Overlay> overlays = new ArrayList<>();
        for (Map.Entry<String, List<Layer>> target : producers.entrySet()) {
            List<Layer> candidates = target.getValue();
            Layer selected;
            if (candidates.size() == 1) {
                if (winners.containsKey(target.getKey())) throw new IOException("winner supplied for uncontested target: " + target.getKey());
                selected = candidates.getFirst();
            } else {
                String winner = winners.get(target.getKey());
                if (winner == null) throw new IOException("explicit final producer required: " + target.getKey());
                selected = candidates.stream().filter(layer -> layer.key().equals(winner)).findFirst()
                        .orElseThrow(() -> new IOException("selected winner does not produce contested target: " + target.getKey()));
                consumedWinners.add(target.getKey());
            }
            SelectedFile file = selected.files().stream().filter(row -> row.targetRelative().equals(target.getKey())).findFirst().orElseThrow();
            componentFiles.computeIfAbsent(selected.component(), unused -> new ArrayList<>()).add(file);
            FileRef before = originals.get(file.targetRelative());
            if (!file.sourceRef().equals(before)) {
                overlays.add(new Overlay(file.targetRelative(), before == null ? Preimage.absent() : Preimage.exact(before),
                        file.sourceRef(), selected.component(), requestRef));
            }
        }
        if (!consumedWinners.equals(winners.keySet())) throw new IOException("unconsumed or stale winner declaration");
        List<ComponentSelection> selections = new ArrayList<>();
        for (Map.Entry<Component, List<SelectedFile>> component : componentFiles.entrySet()) {
            selections.add(new ComponentSelection(component.getKey(), requestRef, component.getValue()));
        }
        Plan result = new Plan(request.relocations().isEmpty() ? CompleteSourceGraph.PLAN_SCHEMA : CompleteSourceGraph.RELOCATION_PLAN_SCHEMA,
                request.machineId(), request.observedAtUtc(), SelectionStatus.SOURCE_SELECTION_ONLY, request.profile(),
                request.baseline(), request.modules(), selections, overlays, request.relocations());
        CompleteSourceGraph.resolve(result);
        for (Layer layer : request.layers()) {
            layer.ownerMapRef().verify(); for (SelectedFile file : layer.files()) file.sourceRef().verify();
        }
        requestRef.verify(); return result;
    }

    /** Root executes only under its admitted metadata output allocation; this does not copy the graph. */
    public static void main(String[] arguments) throws IOException {
        if (arguments.length != 2) throw new IllegalArgumentException("assembly-request.json plan-output.json");
        FileRef requestRef = FileRef.measure(Path.of(arguments[0]));
        Plan plan = produce(requestRef);
        Path output = Path.of(arguments[1]).toAbsolutePath().normalize();
        SharedSourceFiles.plainAncestors(output);
        if (!Files.isDirectory(output.getParent())) throw new IOException("preallocated metadata parent required");
        byte[] bytes = CompleteSourceGraph.encodePlan(plan);
        Files.write(output, bytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        FileRef actual = FileRef.measure(output);
        if (!plan.equals(CompleteSourceGraph.readPlan(actual))) throw new IOException("actual Plan roundtrip differs");
        System.out.println("SOURCE_SELECTION_PLAN_ONLY bytes=" + actual.bytes() + " sha256=" + actual.sha256());
    }
}
