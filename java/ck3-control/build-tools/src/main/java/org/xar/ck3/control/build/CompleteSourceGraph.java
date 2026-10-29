package org.xar.ck3.control.build;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.zip.GZIPInputStream;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Shared selection contract. A resolved plan is never a compiled or accepted source manifest. */
public final class CompleteSourceGraph {
    public static final String PLAN_SCHEMA = "xar.complete-java-source-graph-plan/v1";
    public static final String RELOCATION_PLAN_SCHEMA = "xar.complete-java-source-graph-plan/v2";
    public static final String SELECTION_SCHEMA = "xar.complete-java-source-selection/v1";
    public static final String COMPONENT_SCHEMA = "xar.complete-java-source-component/v1";
    private static final int JSON_LIMIT = 8 << 20;
    private static final List<String> BASE_MODULES = List.of("contracts", "governance-policy", "wave2-governance",
            "closed-failure-recovery", "admission-contracts", "late-outcome-reconciliation", "build-tools",
            "wave2-runtime", "wave2-development", "wave3-governance", "planning-runtime", "finance-policy",
            "campaign-score", "war-budget", "wave2-finance", "wave2-planning", "military-policy", "war-policy",
            "replenishment-policy", "wave2-military", "wave3-planning", "local-service", "native-diagnostics",
            "event-policy", "wave2-events", "wave2-prisoners", "wave3-development", "wave3-runtime", "wave3-military");

    /** These are the already designed independent profiles; the old extent is unchanged. */
    public enum Profile {
        JAVA29_REPAIR_20261023(1536, 24L << 20, 29L << 20),
        G2_RESEARCH_20261023(2304, 32L << 20, 36L << 20),
        G2_STABILIZATION_20261023(2304, 32L << 20, 44L << 20),
        G2_FULL_PARITY_20261024(3072, 40L << 20, 56L << 20),
        G2_FULL_PARITY_20261024_R2(4096, 64L << 20, 80L << 20),
        G2_FULL_PARITY_20261024_R3(4096, 64L << 20, 80L << 20),
        G2_FULL_PARITY_20261024_R4(5120, 64L << 20, 80L << 20),
        G2_FULL_PARITY_20261024_R5(6144, 96L << 20, 112L << 20),
        G2_FULL_PARITY_20261024_R6(6144, 96L << 20, 112L << 20),
        G2_FULL_PARITY_20261025_R7(6144, 96L << 20, 112L << 20);
        private final int files;
        private final long logicalBytes;
        private final long nativeBytes;
        Profile(int files, long logicalBytes, long nativeBytes) {
            this.files = files; this.logicalBytes = logicalBytes; this.nativeBytes = nativeBytes;
        }
        public int maxFiles() { return files; }
        public long maxLogicalBytes() { return logicalBytes; }
        public long maxNativeBytes() { return nativeBytes; }
        public boolean completeG2() { return this != JAVA29_REPAIR_20261023; }
        public boolean fullParity() { return this == G2_FULL_PARITY_20261024 || resumedParity(); }
        private boolean resumedParity() { return this == G2_FULL_PARITY_20261024_R2 || this == G2_FULL_PARITY_20261024_R3
                || this == G2_FULL_PARITY_20261024_R4 || this == G2_FULL_PARITY_20261024_R5 || this == G2_FULL_PARITY_20261024_R6 || this == G2_FULL_PARITY_20261025_R7; }
        public int copyProofMaxBytes() { return resumedParity() ? 16 << 20 : 8 << 20; }
        public int childModules() { return modules(this).size(); }
        public int reactorProjects() { return childModules() + 1; }
        public ControlBuild.SourceLimitProfile sourceLimitProfile() {
            return switch (this) {
                case JAVA29_REPAIR_20261023 -> ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022;
                case G2_RESEARCH_20261023 -> ControlBuild.SourceLimitProfile.G2_RESEARCH_20261023;
                case G2_STABILIZATION_20261023 -> ControlBuild.SourceLimitProfile.G2_STABILIZATION_20261023;
                case G2_FULL_PARITY_20261024 -> ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024;
                case G2_FULL_PARITY_20261024_R2 -> ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R2;
                case G2_FULL_PARITY_20261024_R3 -> ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R3;
                case G2_FULL_PARITY_20261024_R4 -> ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R4;
                case G2_FULL_PARITY_20261024_R5 -> ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R5;
                case G2_FULL_PARITY_20261024_R6 -> ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R6;
                case G2_FULL_PARITY_20261025_R7 -> ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261025_R7;
            };
        }
    }
    public enum Component { COMMON, M0, M1, M2, M3, M4, M5, M6, M7, RECOVERY22, BUILD_TOOLS, HTTP_HOST }
    public enum PreimageState { ABSENT, EXACT_REF }
    public enum SelectionStatus { SOURCE_SELECTION_ONLY }
    public enum VerificationStatus { EXACT_MATERIALIZED_SOURCES_ONLY }

    public record Baseline(String root, FileRef inventoryRef) {
        public Baseline {
            absolute(root); Objects.requireNonNull(inventoryRef, "baseline inventory");
        }
    }
    public record Preimage(PreimageState state, FileRef ref) {
        public Preimage {
            Objects.requireNonNull(state, "preimage state");
            if ((state == PreimageState.EXACT_REF) != (ref != null)) {
                throw new IllegalArgumentException("EXACT_REF requires a ref; ABSENT requires null");
            }
        }
        public static Preimage absent() { return new Preimage(PreimageState.ABSENT, null); }
        public static Preimage exact(FileRef ref) { return new Preimage(PreimageState.EXACT_REF, ref); }
    }
    public record SelectedFile(String targetRelative, FileRef sourceRef) {
        public SelectedFile { canonicalTarget(targetRelative); Objects.requireNonNull(sourceRef, "selected source"); }
    }
    /** Original move authority and independently pinned current owner revision; neither is an alias for the other. */
    public record Relocation(String oldTargetRelative, String newTargetRelative, FileRef sourceRef, FileRef selectionRef,
                             FileRef finalSourceRef, FileRef finalSelectionRef, String finalOwnerTargetRelative) {
        public Relocation {
            canonicalTarget(oldTargetRelative); canonicalTarget(newTargetRelative);
            Objects.requireNonNull(sourceRef, "relocated source"); Objects.requireNonNull(selectionRef, "relocation authority");
            Objects.requireNonNull(finalSourceRef, "final relocated source"); Objects.requireNonNull(finalSelectionRef, "current owner authority");
            if (!oldTargetRelative.equals(finalOwnerTargetRelative) && !newTargetRelative.equals(finalOwnerTargetRelative)) {
                throw new IllegalArgumentException("current owner must explicitly export the old or new physical target");
            }
            String oldKind = javaSourceKind(oldTargetRelative), newKind = javaSourceKind(newTargetRelative);
            boolean sameName=oldTargetRelative.substring(oldTargetRelative.lastIndexOf('/')+1)
                    .equals(newTargetRelative.substring(newTargetRelative.lastIndexOf('/')+1));
            // Test renames retain both exact source revisions and both explicit relocation/owner authorities.
            // Production main renames remain forbidden; resolve still verifies every original/final content pin.
            if (!oldKind.equals(newKind) || oldTargetRelative.equalsIgnoreCase(newTargetRelative)
                    || (!oldKind.equals("test") && !sameName)) {
                throw new IllegalArgumentException("Same main/test role and distinct module targets required; only explicit test authorities may rename");
            }
        }
        public Relocation(String oldTargetRelative, String newTargetRelative, FileRef sourceRef, FileRef selectionRef) {
            this(oldTargetRelative, newTargetRelative, sourceRef, selectionRef, sourceRef, selectionRef, newTargetRelative);
        }
    }
    /** One final producer per target. Intermediate patch chains must be resolved by their owner first. */
    public record Overlay(String targetRelative, Preimage preimage, FileRef postimage,
                          Component component, FileRef selectionRef) {
        public Overlay {
            canonicalTarget(targetRelative); Objects.requireNonNull(preimage, "preimage");
            Objects.requireNonNull(postimage, "postimage"); Objects.requireNonNull(component, "component");
            Objects.requireNonNull(selectionRef, "selection ref");
        }
    }
    /** The owner explicitly supplies the complete selected target set, including retained consumers. */
    public record ComponentSelection(Component component, FileRef selectionRef, List<SelectedFile> files) {
        public ComponentSelection {
            Objects.requireNonNull(component, "component"); Objects.requireNonNull(selectionRef, "selection ref");
            files = List.copyOf(files);
            if (files.isEmpty()) throw new IllegalArgumentException("explicit nonempty component selection required");
            Set<String> targets = new HashSet<>();
            for (SelectedFile file : files) {
                if (!targets.add(file.targetRelative())) throw new IllegalArgumentException("duplicate component target");
                if (component == Component.BUILD_TOOLS && !file.targetRelative().startsWith("build-tools/")) {
                    throw new IllegalArgumentException("tool selections require build-tools/ target prefix");
                }
            }
        }
    }
    /** Shared producer format for one domain's final adoption rows and its complete retained target set. */
    public record ComponentInput(String schema, String machineId, String observedAtUtc,
                                 ComponentSelection selection, List<Overlay> overlays) {
        public ComponentInput {
            if (!COMPONENT_SCHEMA.equals(schema) || machineId == null || machineId.isBlank()) {
                throw new IllegalArgumentException("explicit component schema and observed machine required");
            }
            Instant.parse(observedAtUtc); Objects.requireNonNull(selection, "component selection");
            overlays = List.copyOf(overlays);
            for (Overlay overlay : overlays) {
                if (overlay.component() != selection.component() || !overlay.selectionRef().equals(selection.selectionRef())
                        || !selection.files().contains(new SelectedFile(overlay.targetRelative(), overlay.postimage()))) {
                    throw new IllegalArgumentException("component overlays must match their owner's final selected files");
                }
            }
        }
    }
    public record Plan(String schema, String machineId, String observedAtUtc, SelectionStatus status,
                       Profile profile, Baseline baseline, List<String> modules,
                       List<ComponentSelection> selections, List<Overlay> overlays, List<Relocation> relocations) {
        public Plan {
            if ((!PLAN_SCHEMA.equals(schema) && !RELOCATION_PLAN_SCHEMA.equals(schema)) || machineId == null || machineId.isBlank()) {
                throw new IllegalArgumentException("explicit source plan schema and observed machine required");
            }
            Instant.parse(observedAtUtc);
            Objects.requireNonNull(status, "source selection status"); Objects.requireNonNull(profile, "profile");
            Objects.requireNonNull(baseline, "baseline");
            modules = List.copyOf(modules); selections = List.copyOf(selections); overlays = List.copyOf(overlays);
            relocations = List.copyOf(relocations);
            requireRelocationVersion(schema, PLAN_SCHEMA, RELOCATION_PLAN_SCHEMA, relocations);
            Set<String> expected = new HashSet<>(CompleteSourceGraph.modules(profile));
            if (modules.size() != expected.size() || !new HashSet<>(modules).equals(expected)) {
                throw new IllegalArgumentException("complete explicit " + profile.childModules() + " child module roster required");
            }
            EnumSet<Component> components = EnumSet.noneOf(Component.class);
            for (ComponentSelection selection : selections) {
                if (!components.add(selection.component())) throw new IllegalArgumentException("duplicate component selection");
            }
            if (profile.completeG2() && !components.equals(EnumSet.allOf(Component.class))) {
                throw new IllegalArgumentException("G2 requires final M0-M7, common, recovery22, tools and host selections");
            }
        }
        public Plan(String schema, String machineId, String observedAtUtc, SelectionStatus status,
                    Profile profile, Baseline baseline, List<String> modules,
                    List<ComponentSelection> selections, List<Overlay> overlays) {
            this(schema, machineId, observedAtUtc, status, profile, baseline, modules, selections, overlays, List.of());
        }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static Plan fromWire(JsonNode node) throws IOException {
            if (wireSchema(node).equals(PLAN_SCHEMA)) {
                LegacyPlan wire = ControlBuild.strictMapper().treeToValue(node, LegacyPlan.class);
                return new Plan(wire.schema(), wire.machineId(), wire.observedAtUtc(), wire.status(), wire.profile(),
                        wire.baseline(), wire.modules(), wire.selections(), wire.overlays());
            }
            RelocatedPlan wire = ControlBuild.strictMapper().treeToValue(node, RelocatedPlan.class);
            return new Plan(wire.schema(), wire.machineId(), wire.observedAtUtc(), wire.status(), wire.profile(),
                    wire.baseline(), wire.modules(), wire.selections(), wire.overlays(), wire.relocations());
        }
        @JsonValue public JsonNode toWire() {
            if (schema.equals(PLAN_SCHEMA)) return ControlBuild.strictMapper().valueToTree(new LegacyPlan(schema,
                    machineId, observedAtUtc, status, profile, baseline, modules, selections, overlays));
            return ControlBuild.strictMapper().valueToTree(new RelocatedPlan(schema, machineId, observedAtUtc,
                    status, profile, baseline, modules, selections, overlays, relocations));
        }
    }
    private record LegacyPlan(String schema, String machineId, String observedAtUtc, SelectionStatus status,
            Profile profile, Baseline baseline, List<String> modules, List<ComponentSelection> selections, List<Overlay> overlays) { }
    private record RelocatedPlan(String schema, String machineId, String observedAtUtc, SelectionStatus status,
            Profile profile, Baseline baseline, List<String> modules, List<ComponentSelection> selections,
            List<Overlay> overlays, List<Relocation> relocations) { }
    public record ResolvedFile(String targetRelative, FileRef sourceRef) {
        public ResolvedFile { canonicalTarget(targetRelative); Objects.requireNonNull(sourceRef, "source"); }
    }
    public record SelectionProof(String schema, SelectionStatus status, Profile profile,
                                 List<ResolvedFile> files, List<ComponentSelection> selections, long logicalBytes) {
        public SelectionProof {
            if (!SELECTION_SCHEMA.equals(schema) || status != SelectionStatus.SOURCE_SELECTION_ONLY) {
                throw new IllegalArgumentException("source selection proof only");
            }
            Objects.requireNonNull(profile, "profile");
            files = List.copyOf(files); selections = List.copyOf(selections);
            if (logicalBytes < 0) throw new IllegalArgumentException("logical bytes must be nonnegative");
        }
    }
    public record MaterializedSources(VerificationStatus status, String root, Profile profile,
                                      List<FileRef> sourcePins) {
        public MaterializedSources {
            if (status != VerificationStatus.EXACT_MATERIALIZED_SOURCES_ONLY) {
                throw new IllegalArgumentException("materialized source verification only");
            }
            absolute(root); Objects.requireNonNull(profile, "profile"); sourcePins = List.copyOf(sourcePins);
        }
    }
    private CompleteSourceGraph() { }

    public static List<String> modules(Profile profile) {
        Objects.requireNonNull(profile, "profile");
        List<String> result = new ArrayList<>(BASE_MODULES);
        if (profile.completeG2()) result.add(result.indexOf("local-service"), "g2-research");
        if (profile == Profile.G2_STABILIZATION_20261023 || profile.fullParity())
            result.add(result.indexOf("contracts") + 1, "continuity-core");
        if (profile.fullParity())
            result.addAll(List.of("adapters-storage", "application", "native-transport"));
        return List.copyOf(result);
    }

    /** Converts a tools-only root row; already-prefixed rows are rejected to prevent double relocation. */
    public static String buildToolsTarget(String toolsRelative) {
        canonicalTarget(toolsRelative);
        if (toolsRelative.startsWith("build-tools/") || !(toolsRelative.equals("pom.xml")
                || toolsRelative.startsWith("src/") || toolsRelative.startsWith(".mvn/"))) {
            throw new IllegalArgumentException("canonical tools-root pom/src/.mvn target required");
        }
        return "build-tools/" + toolsRelative;
    }

    public static Plan readPlan(FileRef ref) throws IOException {
        byte[] bytes = verifiedBytes(ref);
        return ControlBuild.strictMapper().readValue(bytes, Plan.class);
    }
    public static ComponentInput readComponent(FileRef ref) throws IOException {
        return ControlBuild.strictMapper().readValue(verifiedBytes(ref), ComponentInput.class);
    }
    public static Plan combine(String machineId, String observedAtUtc, Profile profile, Baseline baseline,
                               List<ComponentInput> components) {
        List<ComponentSelection> selections = new ArrayList<>(); List<Overlay> overlays = new ArrayList<>();
        for (ComponentInput component : components) {
            if (!machineId.equals(component.machineId())) throw new IllegalArgumentException("component observed machine differs");
            selections.add(component.selection()); overlays.addAll(component.overlays());
        }
        return new Plan(PLAN_SCHEMA, machineId, observedAtUtc, SelectionStatus.SOURCE_SELECTION_ONLY,
                profile, baseline, modules(profile), selections, overlays);
    }
    /** Complete protected baseline, including originals replaced by overlays, for native copy witnesses. */
    public static List<FileRef> baselineFiles(Plan plan) throws IOException {
        Objects.requireNonNull(plan, "plan");
        return baselineFiles(plan.baseline());
    }
    public static List<FileRef> baselineFiles(Baseline baseline) throws IOException {
        Objects.requireNonNull(baseline, "baseline");
        return List.copyOf(baseline(baseline).values());
    }

    public static byte[] encodePlan(Plan plan) throws IOException {
        byte[] bytes = ControlBuild.strictMapper().writeValueAsBytes(plan);
        if (bytes.length > JSON_LIMIT) throw new IOException("finite plan JSON bound exceeded");
        if (!plan.equals(ControlBuild.strictMapper().readValue(bytes, Plan.class))) {
            throw new IOException("source plan strict serialization roundtrip differs");
        }
        return bytes;
    }

    /** Resolves all bytes and exact preimages without writing a source tree or granting build authority. */
    public static SelectionProof resolve(Plan plan) throws IOException {
        Objects.requireNonNull(plan, "plan");
        Path baselineRoot = absolute(plan.baseline().root());
        TreeMap<String, FileRef> baseline = baseline(plan.baseline());
        TreeMap<String, FileRef> selected = new TreeMap<>(baseline);
        Set<String> changed = new HashSet<>();
        Map<Component, ComponentSelection> components = new java.util.EnumMap<>(Component.class);
        for (ComponentSelection selection : plan.selections()) {
            selection.selectionRef().verify(); components.put(selection.component(), selection);
            for (SelectedFile file : selection.files()) file.sourceRef().verify();
        }
        for (Overlay overlay : plan.overlays()) {
            if (!changed.add(overlay.targetRelative())) throw new IOException("two final producers selected: " + overlay.targetRelative());
            FileRef original = baseline.get(overlay.targetRelative());
            if (overlay.preimage().state() == PreimageState.ABSENT ? original != null
                    : original == null || !original.equals(overlay.preimage().ref())) {
                throw new IOException("exact baseline preimage differs: " + overlay.targetRelative());
            }
            ComponentSelection component = components.get(overlay.component());
            if (component == null || !component.selectionRef().equals(overlay.selectionRef())
                    || !component.files().contains(new SelectedFile(overlay.targetRelative(), overlay.postimage()))) {
                throw new IOException("overlay is outside the owner's explicit final selection");
            }
            overlay.postimage().verify(); selected.put(overlay.targetRelative(), overlay.postimage());
        }
        for (ComponentSelection component : plan.selections()) {
            for (SelectedFile expected : component.files()) {
                FileRef actual = selected.get(expected.targetRelative());
                if (actual == null || !sameContent(actual, expected.sourceRef())) {
                    throw new IOException("complete owner selection not adopted: " + component.component() + ":" + expected.targetRelative());
                }
            }
        }
        verifyRelocations(plan, selected);
        for (Relocation relocation : plan.relocations()) {
            selected.remove(relocation.oldTargetRelative());
            selected.put(relocation.newTargetRelative(), relocation.finalSourceRef());
        }
        for (String module : plan.modules()) {
            if (!selected.containsKey(module + "/pom.xml")) throw new IOException("declared child POM missing: " + module);
        }
        long logicalBytes = 0;
        List<ResolvedFile> result = new ArrayList<>();
        for (Map.Entry<String, FileRef> entry : selected.entrySet()) {
            targetModule(entry.getKey(), plan.modules());
            logicalBytes = Math.addExact(logicalBytes, entry.getValue().bytes());
            result.add(new ResolvedFile(entry.getKey(), entry.getValue()));
        }
        if (!selected.containsKey("pom.xml") || result.size() > plan.profile().maxFiles()
                || logicalBytes > plan.profile().maxLogicalBytes()) throw new IOException("finite selected source extent exceeded");
        validatePoms(selected, plan.modules());
        // Recheck all source authorities around resolution. Native copy/identity proof remains with SharedSourceFiles.
        if (!baseline.equals(baseline(plan.baseline()))) throw new IOException("baseline inventory changed during selection");
        requireOrdinarySet(baselineRoot, baseline.keySet());
        for (ComponentSelection component : plan.selections()) {
            component.selectionRef().verify(); for (SelectedFile file : component.files()) file.sourceRef().verify();
        }
        for (Relocation relocation : plan.relocations()) {
            relocation.sourceRef().verify(); relocation.selectionRef().verify();
            relocation.finalSourceRef().verify(); relocation.finalSelectionRef().verify();
        }
        return new SelectionProof(SELECTION_SCHEMA, SelectionStatus.SOURCE_SELECTION_ONLY,
                plan.profile(), result, finalSelections(plan), logicalBytes);
    }

    /** Pre-relocation selections remain exact ancestry; only this final projection omits declared old targets. */
    public static List<ComponentSelection> finalSelections(Plan plan) {
        Set<String> retired = new HashSet<>();
        for (Relocation relocation : plan.relocations()) retired.add(relocation.oldTargetRelative());
        Map<String, FileRef> revised = new TreeMap<>();
        for (Relocation relocation : plan.relocations()) revised.put(relocation.newTargetRelative(), relocation.finalSourceRef());
        List<ComponentSelection> result = new ArrayList<>();
        for (ComponentSelection component : plan.selections()) {
            List<SelectedFile> files = component.files().stream().filter(file -> !retired.contains(file.targetRelative()))
                    .map(file -> new SelectedFile(file.targetRelative(), revised.getOrDefault(file.targetRelative(), file.sourceRef()))).toList();
            if (!files.isEmpty()) result.add(new ComponentSelection(component.component(), component.selectionRef(), files));
        }
        return List.copyOf(result);
    }

    /** Shared producer/auditor check: a moved source must never survive at both physical module targets. */
    public static void requireRelocatedTargetsAbsent(Plan plan, Path root) throws IOException {
        Path normalized = root.toAbsolutePath().normalize();
        for (Relocation relocation : plan.relocations()) {
            Path old = normalized.resolve(relocation.oldTargetRelative()).normalize();
            if (!old.startsWith(normalized) || Files.exists(old, LinkOption.NOFOLLOW_LINKS)) {
                throw new IOException("retired relocation target exists in final tree: " + relocation.oldTargetRelative());
            }
        }
    }

    private record DeclaredMove(String oldTargetRelative, String newTargetRelative, FileRef sourceRef) { }

    private static void verifyRelocations(Plan plan, Map<String, FileRef> selected) throws IOException {
        validateRelocations(plan.machineId(),plan.modules(),plan.relocations(),selected);
    }

    /** The same complete authority validation for bounded producers using an existing selected graph. */
    public static void validateRelocations(String machineId,List<String> modules,List<Relocation> relocations,
            Map<String,FileRef> selected)throws IOException {
        if(machineId==null||machineId.isBlank())throw new IllegalArgumentException("Explicit source machine required");
        modules=List.copyOf(modules);relocations=List.copyOf(relocations);selected=Map.copyOf(selected);
        Set<String> oldTargets = new HashSet<>(), newTargets = new HashSet<>();
        for (Relocation move : relocations) {
            String oldKey = move.oldTargetRelative().toLowerCase(java.util.Locale.ROOT);
            String newKey = move.newTargetRelative().toLowerCase(java.util.Locale.ROOT);
            if (!oldTargets.add(oldKey) || !newTargets.add(newKey)) throw new IOException("duplicate or case-aliased relocation endpoint");
            targetModule(move.oldTargetRelative(), modules); targetModule(move.newTargetRelative(), modules);
            FileRef old = selected.get(move.oldTargetRelative()), next = selected.get(move.newTargetRelative());
            if (old == null || next == null
                    || !(sameSource(old, move.sourceRef()) || move.finalOwnerTargetRelative().equals(move.oldTargetRelative())
                            && sameSource(old, move.finalSourceRef()))
                    || !(sameSource(next, move.sourceRef()) || move.finalOwnerTargetRelative().equals(move.newTargetRelative())
                            && sameSource(next, move.finalSourceRef()))
                    || !sameSource(selected.get(move.finalOwnerTargetRelative()), move.finalSourceRef())) {
                throw new IOException("relocation original or explicit current winner differs: " + move.oldTargetRelative());
            }
            move.sourceRef().verify(); move.selectionRef().verify();
            move.finalSourceRef().verify(); move.finalSelectionRef().verify();
            JsonNode current = ControlBuild.strictMapper().readTree(verifiedBytes(move.finalSelectionRef()));
            if (!validOwner(current, machineId)) throw new IOException("current revision owner/machine differs");
            requireOwnerFile(current, move.finalOwnerTargetRelative(), move.finalSourceRef());
        }
        for (String old : oldTargets) if (newTargets.contains(old)) throw new IOException("relocation chains and cycles are forbidden");
        Set<String> checkedAuthorities = new HashSet<>();
        for (Relocation move : relocations) {
            String authority = absolute(move.selectionRef().path()).toString();
            if (!checkedAuthorities.add(authority)) continue;
            JsonNode root = ControlBuild.strictMapper().readTree(verifiedBytes(move.selectionRef()));
            if (!validOwner(root, machineId)
                    || !root.path("relocations").isArray() || root.path("relocations").isEmpty()
                    || !root.path("selected_files").isArray()) throw new IOException("exact relocation owner/machine/declaration required");
            List<Relocation> expected = relocations.stream().filter(row -> sameSource(row.selectionRef(), move.selectionRef())).toList();
            if (expected.size() != root.path("relocations").size()) throw new IOException("complete authority relocation set required");
            Set<String> declared = new HashSet<>();
            for (JsonNode row : root.path("relocations")) {
                DeclaredMove source = ControlBuild.strictMapper().treeToValue(row, DeclaredMove.class);
                if (!declared.add(source.oldTargetRelative()) || expected.stream().noneMatch(item ->
                        item.oldTargetRelative().equals(source.oldTargetRelative())
                        && item.newTargetRelative().equals(source.newTargetRelative()) && sameSource(item.sourceRef(), source.sourceRef()))) {
                    throw new IOException("relocation authority exact row differs");
                }
                requireOwnerFile(root, source.newTargetRelative(), source.sourceRef());
            }
            move.selectionRef().verify();
        }
    }

    private static boolean validOwner(JsonNode root, String machineId) {
        return root.isObject() && root.path("machine_id").isTextual() && machineId.equals(root.path("machine_id").textValue())
                && root.path("owner").isTextual() && root.path("owner").textValue().matches("/root/[a-z0-9_]+")
                && root.path("selected_files").isArray();
    }
    private static void requireOwnerFile(JsonNode owner, String target, FileRef source) throws IOException {
        boolean found = false;
        for (JsonNode file : owner.path("selected_files")) {
            if (file.path("target_relative").isTextual() && target.equals(file.path("target_relative").textValue())) {
                FileRef actual = ControlBuild.strictMapper().treeToValue(file.get("source_ref"), FileRef.class);
                if (found || !sameSource(actual, source)) throw new IOException("owner target/source differs or duplicates: " + target);
                found = true;
            }
        }
        if (!found) throw new IOException("explicit target absent from owner selected_files: " + target);
    }

    static void requireRelocationVersion(String schema, String legacy, String current, List<Relocation> moves) {
        if (legacy.equals(schema) ? !moves.isEmpty() : !current.equals(schema) || moves.isEmpty()) {
            throw new IllegalArgumentException("v1 requires no relocations; v2 requires explicit nonempty relocations");
        }
    }
    static String wireSchema(JsonNode node) throws IOException {
        if (node == null || !node.isObject() || !node.path("schema").isTextual()) throw new IOException("explicit typed wire schema required");
        return node.path("schema").textValue();
    }
    private static String javaSourceKind(String target) {
        if (!target.matches("[a-z0-9-]+/src/(?:main|test)/java/.+\\.java")) {
            throw new IllegalArgumentException("relocation is limited to explicit Java main/test targets");
        }
        return target.contains("/src/main/java/") ? "main" : "test";
    }
    private static boolean sameSource(FileRef first, FileRef second) {
        return first != null && second != null && sameContent(first, second)
                && absolute(first.path()).equals(absolute(second.path()));
    }

    /** Calls the actual Maven source producer, then compares every target's content, not its file count. */
    public static MaterializedSources verifyMaterialized(Plan plan, Path root) throws IOException {
        SelectionProof selection = resolve(plan);
        requireRelocatedTargetsAbsent(plan, root);
        ControlBuild.SourceLimitProfile profile = plan.profile().sourceLimitProfile();
        Path targetRoot = root.toRealPath();
        List<FileRef> actual = ControlBuild.sourceManifest(targetRoot, profile);
        TreeMap<String, FileRef> targets = new TreeMap<>();
        for (FileRef file : actual) {
            String target = relativeTo(targetRoot, file);
            if (targets.putIfAbsent(target, file) != null) throw new IOException("duplicate materialized target");
        }
        Set<String> expectedTargets = new HashSet<>();
        for (ResolvedFile expected : selection.files()) {
            expectedTargets.add(expected.targetRelative());
            FileRef materialized = targets.get(expected.targetRelative());
            if (materialized == null || !sameContent(expected.sourceRef(), materialized)) {
                throw new IOException("materialized source differs: " + expected.targetRelative());
            }
        }
        if (!targets.keySet().equals(expectedTargets)) throw new IOException("materialized source target set differs");
        return new MaterializedSources(VerificationStatus.EXACT_MATERIALIZED_SOURCES_ONLY,
                targetRoot.toString(), plan.profile(), actual);
    }

    private static TreeMap<String, FileRef> baseline(Baseline baseline) throws IOException {
        baseline.inventoryRef().verify();
        byte[] raw;
        try (InputStream file = Files.newInputStream(Path.of(baseline.inventoryRef().path()));
             InputStream input = new GZIPInputStream(file)) {
            raw = input.readNBytes(JSON_LIMIT + 1);
        }
        if (raw.length > JSON_LIMIT) throw new IOException("finite baseline inventory JSON bound exceeded");
        List<FileRef> refs = ControlBuild.strictMapper().readValue(raw, new TypeReference<List<FileRef>>() { });
        if (refs.isEmpty()) throw new IOException("nonempty complete baseline inventory required");
        Path root = absolute(baseline.root());
        TreeMap<String, FileRef> result = new TreeMap<>();
        for (FileRef ref : refs) {
            String relative = relativeTo(root, ref); ref.verify();
            if (result.putIfAbsent(relative, ref) != null) throw new IOException("duplicate baseline target");
        }
        requireOrdinarySet(root, result.keySet());
        return result;
    }
    private static byte[] verifiedBytes(FileRef ref) throws IOException {
        ref.verify();
        if (ref.bytes() > JSON_LIMIT) throw new IOException("finite typed JSON bound exceeded");
        byte[] bytes = Files.readAllBytes(Path.of(ref.path())); ref.verify(); return bytes;
    }
    private static String relativeTo(Path root, FileRef file) throws IOException {
        Path path = absolute(file.path());
        if (!path.startsWith(root) || path.equals(root)) throw new IOException("inventory source escapes explicit baseline root");
        return canonicalTarget(root.relativize(path).toString().replace('\\', '/'));
    }
    private static void requireOrdinarySet(Path root, Set<String> expected) throws IOException {
        Set<String> actual = new HashSet<>(); SharedSourceFiles.plainAncestors(root);
        try (var walk = Files.walk(root)) {
            for (Path path : walk.toList()) {
                SharedSourceFiles.plainAncestors(path);
                if (Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS)) continue;
                if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) throw new IOException("nonordinary source graph entry");
                actual.add(canonicalTarget(root.relativize(path).toString().replace('\\', '/')));
            }
        }
        if (!actual.equals(expected)) throw new IOException("complete baseline ordinary target set differs");
    }
    private static void targetModule(String target, List<String> modules) throws IOException {
        if (target.equals("pom.xml")) return;
        int slash = target.indexOf('/');
        if (slash <= 0 || !modules.contains(target.substring(0, slash))) throw new IOException("undeclared source module: " + target);
    }
    private static void validatePoms(Map<String, FileRef> selected, List<String> modules) throws IOException {
        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, "");
            factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            Element parent = factory.newDocumentBuilder().parse(Path.of(selected.get("pom.xml").path()).toFile()).getDocumentElement();
            List<String> actualModules = new ArrayList<>();
            for (Node child = parent.getFirstChild(); child != null; child = child.getNextSibling()) {
                if (child instanceof Element roster && roster.getTagName().equals("modules")) {
                    for (Node item = roster.getFirstChild(); item != null; item = item.getNextSibling()) {
                        if (item instanceof Element module) {
                            if (!module.getTagName().equals("module")) throw new IOException("unexpected parent module node");
                            actualModules.add(module.getTextContent().strip());
                        }
                    }
                }
            }
            if (!actualModules.equals(modules)) throw new IOException("selected parent direct module order differs");
            for (String module : modules) {
                Element child = factory.newDocumentBuilder().parse(Path.of(selected.get(module + "/pom.xml").path()).toFile()).getDocumentElement();
                String artifact = null;
                for (Node item = child.getFirstChild(); item != null; item = item.getNextSibling()) {
                    if (item instanceof Element element && element.getTagName().equals("artifactId")) artifact = element.getTextContent().strip();
                }
                String expected = module.equals("build-tools") ? "ck3-control-build-tools"
                        : module.equals("local-service") ? "ck3-control-local-service" : module;
                if (!expected.equals(artifact)) throw new IOException("selected module artifact differs: " + module);
            }
        } catch (javax.xml.parsers.ParserConfigurationException | org.xml.sax.SAXException error) {
            throw new IOException("selected POM XML is invalid", error);
        }
    }
    private static boolean sameContent(FileRef first, FileRef second) {
        return first.bytes() == second.bytes() && first.sha256().equals(second.sha256());
    }
    private static Path absolute(String value) {
        if (value == null || !Path.of(value).isAbsolute()) throw new IllegalArgumentException("absolute source root required");
        return Path.of(value).toAbsolutePath().normalize();
    }
    private static String canonicalTarget(String value) {
        if (value == null || value.isEmpty() || value.indexOf('\\') >= 0 || value.indexOf(':') >= 0
                || value.startsWith("/") || value.equals(".") || value.equals("..") || value.startsWith("../")
                || !Path.of(value).normalize().toString().replace('\\', '/').equals(value)) {
            throw new IllegalArgumentException("canonical relative target required");
        }
        return value;
    }
}

