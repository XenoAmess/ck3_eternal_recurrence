package org.xar.ck3.control.wave2.military.combatroles;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Builds seven-field shared capture requests from real artifact references. This helper never launches a process. */
public final class PrepareManagedMilitaryRequest {
    private PrepareManagedMilitaryRequest() { }
    public enum Entry {
        COMBAT_ORIGINAL_CAPTURE("org.xar.ck3.control.wave2.military.combatroles.CaptureCombatRolesGolden"),
        COMBAT_COMPILED_CONSUMERS("org.xar.ck3.control.wave2.military.combatroles.ProbeCompiledCombatConsumers"),
        OBSERVED_MILITARY_COMPILED_CONSUMERS("org.xar.ck3.control.wave2.military.commander.ProbeCompiledObservedMilitaryConsumers");
        private final String className;
        Entry(String className) { this.className = className; }
        public String className() { return className; }
    }
    public record Profile(String machineId, Instant observedAtUtc, Instant leaseExpiresAtUtc, String id,
            Entry entry, Path javaExecutable, Path repository, Path logsRoot, Path taskRoot,
            List<Path> classpath, List<CombatWholeWire.FileReference> artifactReferences,
            List<CombatWholeWire.FileReference> sourceReferences, List<CombatWholeWire.FileReference> inputReferences,
            CombatWholeWire.FileReference qualificationReference) {
        public Profile {
            classpath = List.copyOf(classpath); artifactReferences = List.copyOf(artifactReferences);
            sourceReferences = List.copyOf(sourceReferences); inputReferences = List.copyOf(inputReferences);
            if (machineId == null || machineId.isBlank() || machineId.equals("unknown") || !id.matches("[a-z0-9-]{1,60}")
                    || sourceReferences.isEmpty() || sourceReferences.size() > 64 || inputReferences.size() > 32
                    || classpath.isEmpty() || !observedAtUtc.isBefore(leaseExpiresAtUtc)) {
                throw new IllegalArgumentException("finite actual-machine/profile references required");
            }
        }
    }

    public static void main(String[] args) throws IOException {
        if (args.length != 2) throw new IllegalArgumentException("actual compiled profile JSON and fresh batch JSON required");
        Profile profile = decode(StrictJson.parse(readBounded(Path.of(args[0]), 131072), 131072));
        Path output = Path.of(args[1]).toAbsolutePath().normalize();
        if (!output.startsWith(profile.logsRoot()) || Files.exists(output)) throw new IllegalArgumentException("fresh approved request path required");
        ObjectNode batch = build(profile);
        byte[] encoded = batch.toString().getBytes(StandardCharsets.UTF_8);
        if (encoded.length > 65536) throw new IllegalArgumentException("compact request metadata budget");
        Files.write(output, encoded, StandardOpenOption.CREATE_NEW);
    }

    static ObjectNode build(Profile p) throws IOException {
        if (!Instant.now().isBefore(p.leaseExpiresAtUtc()) || !p.logsRoot().startsWith(p.taskRoot())
                || !Files.isRegularFile(p.javaExecutable())) throw new IllegalArgumentException("fresh profile lease/executable required");
        for (var ref : p.artifactReferences()) CombatWholeWire.readPinned(ref, p.taskRoot());
        Set<Path> artifacts = new HashSet<>(); p.artifactReferences().forEach(ref -> artifacts.add(ref.path()));
        for (Path entry : p.classpath()) {
            if (!entry.startsWith(p.taskRoot()) || !Files.exists(entry)) throw new IllegalArgumentException("actual task classpath required");
            if (Files.isRegularFile(entry) && !artifacts.contains(entry)) throw new IllegalArgumentException("classpath jar omitted from actual artifact references");
            if (Files.isDirectory(entry)) {
                boolean hasActualClass = p.artifactReferences().stream().anyMatch(ref -> ref.path().startsWith(entry) && ref.path().toString().endsWith(".class"));
                if (!hasActualClass) throw new IllegalArgumentException("uncompiled test classpath cannot become an executable request");
            }
        }
        for (var ref : p.sourceReferences()) {
            Path root = ref.path().startsWith(p.repository()) ? p.repository() : p.taskRoot();
            CombatWholeWire.readPinned(ref, root);
        }
        for (var ref : p.inputReferences()) {
            if (ref.bytes() > 8L * 1024 * 1024) throw new IllegalArgumentException("shared worker input profile is 8 MiB; coordinate a distinct narrow profile for a larger original wire");
            Path root = ref.path().startsWith(p.repository()) ? p.repository() : p.taskRoot();
            CombatWholeWire.readPinned(ref, root);
        }
        byte[] qualificationBytes = CombatWholeWire.readPinned(p.qualificationReference(), p.taskRoot());
        JsonNode q = StrictJson.parse(qualificationBytes, 131072);
        Path result;
        List<String> arguments = new ArrayList<>();
        if (p.entry() == Entry.COMBAT_ORIGINAL_CAPTURE) {
            if (!"xar.original-combat-capture-input/v1".equals(q.path("schema").textValue())) throw new IllegalArgumentException("original capture qualification schema");
            result = path(q, "output");
            arguments.add(path(q,"repository").toString()); arguments.add(path(q,"python").toString());
            arguments.add(path(q,"task_root").toString()); arguments.add(path(q,"original_wire_reference").toString());
            arguments.add(path(q,"native_receipt_reference").toString()); arguments.add(result.toString());
        } else {
            String expected = p.entry() == Entry.COMBAT_COMPILED_CONSUMERS
                    ? "xar.compiled-combat-probe-input/v1" : "xar.compiled-observed-military-input/v1";
            if (!expected.equals(q.path("schema").textValue())) throw new IllegalArgumentException("compiled qualification schema");
            result = path(q, p.entry() == Entry.COMBAT_COMPILED_CONSUMERS ? "fresh_output" : "output");
            arguments.add(p.qualificationReference().path().toString());
        }
        if (!result.startsWith(p.logsRoot()) || Files.exists(result)) throw new IllegalArgumentException("fresh profile-owned consumer output required");
        boolean qualificationPinned = p.inputReferences().contains(p.qualificationReference());
        if (!qualificationPinned) throw new IllegalArgumentException("shared worker must bind the exact actual qualification JSON");
        ObjectNode batch = StrictJson.object().put("schema","xar.shared-golden-capture-batch/v1")
                .put("machine_id",p.machineId()).put("observed_at_utc",p.observedAtUtc().toString())
                .put("review_at_utc",p.leaseExpiresAtUtc().toString());
        ObjectNode capture = batch.putArray("captures").addObject().put("id",p.id());
        ArrayNode command = capture.putArray("command"); command.add(p.javaExecutable().toString())
                .add("-Xms16m").add("-Xmx128m").add("-cp");
        command.add(String.join(java.io.File.pathSeparator, p.classpath().stream().map(Path::toString).toList()));
        command.add(p.entry().className()); arguments.forEach(command::add);
        capture.put("cwd",p.repository().toString());
        ArrayNode sources = capture.putArray("source_refs"); p.sourceReferences().forEach(ref -> append(sources,ref));
        ArrayNode inputs = capture.putArray("input_refs"); p.inputReferences().forEach(ref -> append(inputs,ref));
        capture.put("output_path",result.toString()).put("max_output_bytes",32768);
        return batch;
    }

    static Profile decode(JsonNode value) throws IOException {
        Set<String> fields = new HashSet<>(); value.fieldNames().forEachRemaining(fields::add);
        if (!value.isObject() || !fields.equals(Set.of("schema","status","machine_id","observed_at_utc","lease_expires_at_utc",
                "id","entry","java_executable","repository","logs_root","task_root","classpath","artifact_refs","source_refs","input_refs","qualification_ref"))
                || !"xar.military-managed-request-profile/v1".equals(value.path("schema").textValue())
                || !"COMPILED_QUALIFIED".equals(value.path("status").textValue())) {
            throw new IllegalArgumentException("SOURCE_READY_UNCOMPILED/HOLD cannot become an executable request");
        }
        List<Path> classpath = new ArrayList<>();
        if (!value.path("classpath").isArray()) throw new IllegalArgumentException("explicit actual classpath required");
        for (JsonNode entry : value.get("classpath")) classpath.add(absolute(entry));
        return new Profile(text(value,"machine_id"),Instant.parse(text(value,"observed_at_utc")),Instant.parse(text(value,"lease_expires_at_utc")),
                text(value,"id"),Entry.valueOf(text(value,"entry")),path(value,"java_executable"),path(value,"repository"),
                path(value,"logs_root"),path(value,"task_root"),classpath,references(value.get("artifact_refs")),
                references(value.get("source_refs")),references(value.get("input_refs")),reference(value.get("qualification_ref")));
    }
    private static List<CombatWholeWire.FileReference> references(JsonNode value) throws IOException {
        if (value == null || !value.isArray()) throw new IllegalArgumentException("actual reference array required");
        List<CombatWholeWire.FileReference> result = new ArrayList<>(); for (JsonNode ref : value) result.add(reference(ref)); return List.copyOf(result);
    }
    private static CombatWholeWire.FileReference reference(JsonNode value) throws IOException { return CombatWholeWire.reference(value.toString().getBytes(StandardCharsets.UTF_8)); }
    private static void append(ArrayNode values,CombatWholeWire.FileReference ref) { values.addObject().put("path",ref.path().toString()).put("bytes",ref.bytes()).put("sha256",ref.sha256()); }
    private static String text(JsonNode value,String key) { if (!value.path(key).isTextual() || value.path(key).textValue().isBlank()) throw new IllegalArgumentException("actual nonempty text required"); return value.get(key).textValue(); }
    private static Path path(JsonNode value,String key) { return absolute(value.get(key)); }
    private static Path absolute(JsonNode value) { if (value == null || !value.isTextual()) throw new IllegalArgumentException("actual path string required"); Path p=Path.of(value.textValue());if(!p.isAbsolute()||!p.normalize().equals(p))throw new IllegalArgumentException("normalized absolute path required");return p; }
    private static byte[] readBounded(Path path,int maximum)throws IOException{try(var in=Files.newInputStream(path)){byte[] raw=in.readNBytes(maximum+1);if(raw.length>maximum)throw new IllegalArgumentException("finite profile required");return raw;}}
}
