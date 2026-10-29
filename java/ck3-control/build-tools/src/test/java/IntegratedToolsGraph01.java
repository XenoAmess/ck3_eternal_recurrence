import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ExactSourcePatch;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Materialize a new source graph from exact historical inputs; never alter a qualified runtime. */
public final class IntegratedToolsGraph01 {
    private IntegratedToolsGraph01() { }
    private static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";
    private static final Path J = Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1");
    private static final Path OWN = J.resolve("scratch/resume-current-20261023/bootstrap_integrated_tools");
    private static final Path EXTERNAL = Path.of("D:/codex-ck3-demos/2026-10-23-sharedwire-tools88-source01");
    private static final ControlBuild.FileRef HOLD = new ControlBuild.FileRef(
            J.resolve("scratch/resume56-20261023/sharedwire-host06-source01/HOLD-SOURCE-MAP01.json").toString(),
            36362, "67649fcb6e8ad51e1510084eb781aad26a3008c88417f045567467189256e147");
    public enum Group { TOOLS, HOST }
    public enum PreimageKind { ABSENT, EXACT_REF }
    public record Preimage(PreimageKind kind, ControlBuild.FileRef ref) {
        public Preimage {
            if (kind == null || (kind == PreimageKind.EXACT_REF) != (ref != null)) {
                throw new IllegalArgumentException("Explicit preimage kind and matching reference required");
            }
        }
    }
    public record Overlay(Group group, String targetRelative, ControlBuild.FileRef expectedCandidateRef,
            Preimage originalPreimage, ControlBuild.FileRef sourceRef, String reason) {
        public Overlay {
            if (group == null || sourceRef == null || reason == null || reason.isBlank()) {
                throw new IllegalArgumentException("Explicit group, selected source and provenance reason required");
            }
            if ((expectedCandidateRef == null) != (originalPreimage != null)) {
                throw new IllegalArgumentException("New graph rows need explicit original preimages; existing rows use the HOLD preimage");
            }
            checkedTarget(targetRelative);
        }
    }
    public record Request(String schema, String machineId, String reviewAtUtc, ControlBuild.FileRef sourceAuthorityRef,
            String outputRoot, long chargedSourceCapBytes, List<ControlBuild.FileRef> provenanceRefs, List<Overlay> overlays) {
        public Request {
            if (!"xar.integrated-tools-source-request/v1".equals(schema) || !MACHINE.equals(machineId)
                    || sourceAuthorityRef == null || chargedSourceCapBytes <= 0 || chargedSourceCapBytes > (3L << 20)) {
                throw new IllegalArgumentException("Exact bounded same-machine source request required");
            }
            Instant.parse(reviewAtUtc);
            if (!Path.of(outputRoot).isAbsolute() || !(Path.of(outputRoot).normalize().startsWith(OWN)
                    || Path.of(outputRoot).normalize().equals(EXTERNAL))) {
                throw new IllegalArgumentException("Only the assigned fresh source root may be materialized");
            }
            overlays = List.copyOf(overlays);
            provenanceRefs = List.copyOf(provenanceRefs);
        }
    }
    public record Selection(Group group, String targetRelative, Preimage originalPreimage, Preimage source03Preimage,
            ControlBuild.FileRef historicalCandidateRef, ControlBuild.FileRef selectedSourceRef,
            String reason, ControlBuild.FileRef materializedRef) { }
    public record Actual(String schema, String machineId, String observedAtUtc, String status,
            ControlBuild.FileRef requestRef, ControlBuild.FileRef sourceAuthorityRef,
            ControlBuild.FileRef historicalHoldRef, ControlBuild.FileRef historicalToolsReceiptRef,
            String originalQualificationBoundary, int toolsSources, int hostOverlaySources,
            long logicalBytes, long conservativeSourceChargeBytes, List<ControlBuild.FileRef> provenanceRefs, List<Selection> sources) {
        public Actual { provenanceRefs = List.copyOf(provenanceRefs); sources = List.copyOf(sources); }
    }
    public record Derivation(String schema, String machineId, String observedAtUtc, String status,
            ControlBuild.FileRef preimageRef, ControlBuild.FileRef sdk08PatchRef,
            ControlBuild.FileRef sdk08IntermediateRef, ControlBuild.FileRef finalRef,
            String qualification) { }

    public static void main(String[] args) throws Exception {
        if (!MACHINE.equals(WindowsJobProcess.currentMachineId())) throw new IOException("Source machine mismatch");
        if (args.length == 1 && args[0].equals("derive-control-ci")) {
            deriveControlCi();
        } else if (args.length == 2 && args[0].equals("assemble")) {
            assemble(Path.of(args[1]));
        } else throw new IllegalArgumentException("derive-control-ci | assemble exact-request-path");
    }

    private static void deriveControlCi() throws Exception {
        ControlBuild.FileRef base = new ControlBuild.FileRef(
                "D:/codex-ck3-demos/2026-10-23-java-tools27-source01/src/main/java/org/xar/ck3/control/build/ControlCi.java",
                18786, "2174c5fb099296266ed986e16b4113378a365a1aeb763a7a210c8e59d62d10c6");
        ControlBuild.FileRef patch = new ControlBuild.FileRef(
                J.resolve("scratch/resume56-20261023/persistent_ci_routes/sdk-stage-source08/control-ci-fresh-sdk08.patch").toString(),
                3645, "fa72cce3070bc3769987837792827fb1decbc9d5a4d70b5e8d888160ad5cb3e5");
        base.verify(); patch.verify(); HOLD.verify();
        byte[] staged = ExactSourcePatch.apply(Files.readAllBytes(Path.of(base.path())), Files.readAllBytes(Path.of(patch.path())),
                ExactSourcePatch.Syntax.UNIFIED_DIFF, "java/ck3-control/build-tools/src/main/java/org/xar/ck3/control/build/ControlCi.java").bytes();
        Path stagePath = OWN.resolve("ControlCi-sdk08.java");
        source(stagePath, staged);
        ControlBuild.FileRef intermediate = ControlBuild.FileRef.measure(stagePath);
        if (intermediate.bytes() != 19222 || !intermediate.sha256().equals("d0d5beba476cd69ca4f595e97c1df2fee80678fdfefa4ea7b8c284c0f2ee4254")) {
            throw new IOException("SDK08 intermediate differs from the historical explicit postimage");
        }
        String text = new String(staged, StandardCharsets.UTF_8);
        text = once(text, "requireJUnit(Path.of(tools.deploymentRoot()).resolve(\"surefire-reports\"), 144);",
                "requireJUnit(Path.of(tools.deploymentRoot()).resolve(\"surefire-reports\"), 175);");
        text = once(text,
                "if (suite.getAttribute(\"name\").equals(\"org.xar.ck3.control.build.CiBootstrapTest\") && !count.equals(\"22\")) throw new IOException(\"Complete22 bootstrap regression methods required\");",
                "if (suite.getAttribute(\"name\").equals(\"org.xar.ck3.control.build.CiBootstrapTest\") && !count.equals(\"25\")) throw new IOException(\"Complete25 bootstrap regression methods required\");\n"
                + suite("ProjectionArtifactOwnerV3Test", 11) + suite("MapAdmissionCiSessionTest", 1)
                + suite("ProjectionArtifactNestedCodecTest", 3) + suite("G2SourceLimitProfileTest", 4)
                + suite("NativeDirectoryIdentityTest", 3) + suite("SdkFrozenInventoryTest", 6).stripTrailing());
        text = once(text, "\"org.xar.ck3.control.build.FreshSdkFixtureStageTest\")))",
                "\"org.xar.ck3.control.build.FreshSdkFixtureStageTest\",\n"
                + "                \"org.xar.ck3.control.build.ProjectionArtifactOwnerV3Test\",\n"
                + "                \"org.xar.ck3.control.build.MapAdmissionCiSessionTest\",\n"
                + "                \"org.xar.ck3.control.build.ProjectionArtifactNestedCodecTest\",\n"
                + "                \"org.xar.ck3.control.build.G2SourceLimitProfileTest\",\n"
                + "                \"org.xar.ck3.control.build.NativeDirectoryIdentityTest\",\n"
                + "                \"org.xar.ck3.control.build.SdkFrozenInventoryTest\")))");
        Path finalPath = OWN.resolve("ControlCi-hold175.java");
        source(finalPath, text.getBytes(StandardCharsets.UTF_8));
        base.verify(); patch.verify(); HOLD.verify();
        publish(OWN.resolve("CONTROL-CI-DERIVED01.json"), new Derivation("xar.integrated-tools-control-ci-derivation/v1", MACHINE,
                Instant.now().toString(), "SOURCE_MATERIALIZED_UNCOMPILED", base, patch, intermediate,
                ControlBuild.FileRef.measure(finalPath), "Historical175/21 candidate only; final Bootstrap28 and new-suite routing still required. No runtime qualification."));
        System.out.println("ControlCi historical derivation materialized; final integrated qualification NOT_RUN");
    }

    private static String suite(String name, int count) {
        return "                    if (suite.getAttribute(\"name\").equals(\"org.xar.ck3.control.build." + name
                + "\") && !count.equals(\"" + count + "\")) throw new IOException(\"Complete" + count + " " + name + " invocations required\");\n";
    }

    private static void assemble(Path requestPath) throws Exception {
        ControlBuild.FileRef requestRef = ControlBuild.FileRef.measure(requestPath); requestRef.verify();
        Request request = ControlBuild.strictMapper().readValue(Files.readAllBytes(requestPath), Request.class);
        if (!Instant.now().isBefore(Instant.parse(request.reviewAtUtc()))) throw new IOException("Source request expired");
        request.sourceAuthorityRef().verify(); HOLD.verify();
        for (ControlBuild.FileRef ref : request.provenanceRefs()) ref.verify();
        JsonNode hold = ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(HOLD.path())));
        ControlBuild.FileRef baseActual = pin(hold.path("tools28").path("base_actual_ref")); baseActual.verify();
        JsonNode historical = ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(baseActual.path())));
        Path toolsBase = Path.of(requiredText(historical, "source_root")).toRealPath();
        Map<String, ControlBuild.FileRef> originals = new LinkedHashMap<>();
        for (JsonNode value : array(historical, "source_pins")) {
            ControlBuild.FileRef ref = pin(value); ref.verify(); Path source = Path.of(ref.path()).toRealPath();
            if (!source.startsWith(toolsBase)) throw new IOException("Historical tool source escapes its source root");
            String relative = toolsBase.relativize(source).toString().replace('\\', '/'); checkedTarget(relative);
            if (originals.putIfAbsent(relative, ref) != null) throw new IOException("Duplicate historical source target");
        }
        Map<String, Overlay> overlays = new LinkedHashMap<>();
        for (Overlay overlay : request.overlays()) {
            overlay.sourceRef().verify();
            if (overlays.putIfAbsent(key(overlay.group(), overlay.targetRelative()), overlay) != null) throw new IOException("Duplicate overlay target");
        }
        List<Selection> selected = new ArrayList<>(); Set<String> seen = new java.util.HashSet<>();
        for (Group group : Group.values()) {
            String section = group == Group.TOOLS ? "tools28" : "host06";
            for (JsonNode row : array(hold.path(section), "source_rows")) {
                String relative = requiredText(row, "target_relative"); checkedTarget(relative);
                String key = key(group, relative); if (!seen.add(key)) throw new IOException("Duplicate HOLD target");
                ControlBuild.FileRef candidate = pin(row.has("source_ref") ? row.get("source_ref") : row.get("preimage_ref"));
                Preimage original;
                if (group == Group.TOOLS) {
                    ControlBuild.FileRef base = originals.get(relative);
                    original = new Preimage(base == null ? PreimageKind.ABSENT : PreimageKind.EXACT_REF, base);
                } else {
                    JsonNode previous = row.path("source03_preimage");
                    PreimageKind kind = PreimageKind.valueOf(requiredText(previous, "kind"));
                    original = new Preimage(kind, kind == PreimageKind.ABSENT ? null : pin(previous.path("ref")));
                    if (original.ref() != null) original.ref().verify();
                    else if (Files.exists(Path.of(requiredText(hold.path("host06"), "source03_root")).resolve(relative))) {
                        throw new IOException("Host original ABSENT preimage now exists: " + relative);
                    }
                }
                Overlay overlay = overlays.remove(key);
                if (overlay == null) {
                    if (row.path("post_kind").asText().equals("DERIVE_NOT_MATERIALIZED")) throw new IOException("Unmaterialized derived source needs an explicit overlay");
                    candidate.verify();
                } else if (!sameContent(candidate, overlay.expectedCandidateRef())) {
                    throw new IOException("Overlay candidate preimage differs: " + relative);
                }
                Preimage source03 = group == Group.HOST ? original : source03Preimage(hold, relative);
                selected.add(new Selection(group, relative, original, source03, candidate, overlay == null ? candidate : overlay.sourceRef(),
                        overlay == null ? "Exact historical candidate retained" : overlay.reason(), null));
            }
        }
        for (Overlay overlay : overlays.values()) {
            if (overlay.expectedCandidateRef() != null || originals.containsKey(overlay.targetRelative())) throw new IOException("Additional source target collides with a historical tools target");
            if (overlay.originalPreimage().ref() != null) overlay.originalPreimage().ref().verify();
            else {
                Path originalRoot = overlay.group() == Group.TOOLS ? toolsBase : Path.of(requiredText(hold.path("host06"), "source03_root"));
                if (Files.exists(originalRoot.resolve(overlay.targetRelative()))) throw new IOException("Additional ABSENT preimage now exists");
            }
            Preimage source03 = overlay.group() == Group.HOST ? overlay.originalPreimage() : source03Preimage(hold, overlay.targetRelative());
            selected.add(new Selection(overlay.group(), overlay.targetRelative(), overlay.originalPreimage(), source03,
                    null, overlay.sourceRef(), overlay.reason(), null));
        }
        selected.sort(Comparator.comparing((Selection value) -> value.group().name()).thenComparing(Selection::targetRelative));
        Path output = Path.of(request.outputRoot()).normalize();
        if (Files.exists(output)) throw new IOException("New source output already exists; retain it for diagnosis");
        long logical = 0, charged = 0; Set<Path> directories = new java.util.HashSet<>(); directories.add(output);
        for (Selection value : selected) {
            value.selectedSourceRef().verify(); logical = Math.addExact(logical, value.selectedSourceRef().bytes());
            charged = Math.addExact(charged, Math.multiplyExact(Math.floorDiv(Math.addExact(value.selectedSourceRef().bytes(), 4095), 4096), 4096));
            Path target = output.resolve(value.group() == Group.TOOLS ? "tools" : "host-overlay").resolve(value.targetRelative());
            for (Path parent = target.getParent(); parent != null && parent.startsWith(output); parent = parent.getParent()) directories.add(parent);
        }
        charged = Math.addExact(charged, Math.multiplyExact(directories.size(), 4096L));
        if (charged > request.chargedSourceCapBytes()) throw new IOException("Conservative complete graph source charge exceeds its cap");
        List<Selection> written = new ArrayList<>();
        Files.createDirectory(output);
        for (Selection value : selected) {
            Path target = output.resolve(value.group() == Group.TOOLS ? "tools" : "host-overlay").resolve(value.targetRelative());
            Files.createDirectories(target.getParent());
            Files.write(target, Files.readAllBytes(Path.of(value.selectedSourceRef().path())), StandardOpenOption.CREATE_NEW);
            ControlBuild.FileRef actual = ControlBuild.FileRef.measure(target);
            if (!sameContent(value.selectedSourceRef(), actual)) throw new IOException("Materialized source differs: " + value.targetRelative());
            value.selectedSourceRef().verify();
            written.add(new Selection(value.group(), value.targetRelative(), value.originalPreimage(), value.source03Preimage(), value.historicalCandidateRef(),
                    value.selectedSourceRef(), value.reason(), actual));
        }
        requestRef.verify(); request.sourceAuthorityRef().verify(); HOLD.verify(); baseActual.verify();
        for (ControlBuild.FileRef ref : request.provenanceRefs()) ref.verify();
        for (Selection value : written) if (value.source03Preimage().ref() != null) value.source03Preimage().ref().verify();
        publish(output.resolve("SOURCE-MAP01.json"), new Actual("xar.integrated-host-tools-source-map/v1", MACHINE,
                Instant.now().toString(), "MATERIALIZED_UNCOMPILED_UNQUALIFIED", requestRef, request.sourceAuthorityRef(), HOLD, baseActual,
                "Historical tools27 PASS covers its original37 sources only; this integrated graph requires full fresh Maven and real Host/SDK/CI qualification.",
                (int) written.stream().filter(value -> value.group() == Group.TOOLS).count(),
                (int) written.stream().filter(value -> value.group() == Group.HOST).count(), logical, charged, request.provenanceRefs(), written));
        System.out.println("new_source_files=" + written.size() + ";logical_bytes=" + logical + ";conservative_source_charge_bytes=" + charged + ";qualification=NOT_RUN");
    }

    private static Iterable<JsonNode> array(JsonNode node, String field) throws IOException {
        JsonNode value = node.get(field); if (value == null || !value.isArray() || value.isEmpty()) throw new IOException("Required nonempty source array: " + field); return value;
    }
    private static Preimage source03Preimage(JsonNode hold, String relative) throws IOException {
        Path path = Path.of(requiredText(hold.path("host06"), "source03_root")).resolve("build-tools").resolve(relative);
        return Files.exists(path) ? new Preimage(PreimageKind.EXACT_REF, ControlBuild.FileRef.measure(path)) : new Preimage(PreimageKind.ABSENT, null);
    }
    private static ControlBuild.FileRef pin(JsonNode node) throws IOException {
        if (node == null || !node.isObject()) throw new IOException("Exact source FileRef required");
        return ControlBuild.strictMapper().treeToValue(node, ControlBuild.FileRef.class);
    }
    private static String requiredText(JsonNode node, String field) throws IOException {
        JsonNode value = node.get(field); if (value == null || !value.isTextual() || value.textValue().isBlank()) throw new IOException("Required text: " + field); return value.textValue();
    }
    private static void checkedTarget(String target) {
        if (target == null || target.isBlank() || target.indexOf('\\') >= 0 || target.startsWith("/")
                || target.indexOf(':') >= 0 || !Path.of(target).normalize().toString().replace('\\', '/').equals(target)
                || target.equals("..") || target.startsWith("../")) throw new IllegalArgumentException("Canonical relative source target required");
    }
    private static String key(Group group, String target) { return group.name() + ":" + target; }
    private static boolean sameContent(ControlBuild.FileRef left, ControlBuild.FileRef right) {
        return left != null && right != null && left.bytes() == right.bytes() && left.sha256().equals(right.sha256());
    }
    private static String once(String text, String before, String after) throws IOException {
        int at = text.indexOf(before);
        if (at < 0 || text.indexOf(before, at + before.length()) >= 0) throw new IOException("One exact ControlCi transform required");
        return text.substring(0, at) + after + text.substring(at + before.length());
    }
    private static void publish(Path path, Record value) throws IOException {
        Files.write(path, ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(value), StandardOpenOption.CREATE_NEW);
    }
    private static void source(Path path, byte[] bytes) throws IOException {
        if (Files.exists(path)) {
            if (!java.util.Arrays.equals(Files.readAllBytes(path), bytes)) throw new IOException("Existing derived source differs; retain both the source and diagnostic");
        } else Files.write(path, bytes, StandardOpenOption.CREATE_NEW);
    }
}
