package org.xar.ck3.control.wave2.prisoners.releasepreview;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.NativeFixtureBuild;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleaseCollectionProjection12003.SupportedBuild;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;

/**
 * Shared-execution-owner test artifact producer. Replaces only validated leaves in real native fixture
 * envelopes, so existing registered MCP consumers can consume actual Java serialization.
 * Registered consumers run separately in the admitted CI Python process with its current config.
 */
public final class ReleasePreviewCompatibilityCapture {
    private static final List<String> RELEASE_CASES = List.of("gate_true", "gate_false", "old11",
            "selected_change_prison", "puppet_role_mismatch");
    private static final List<String> KINSHIP_CASES = List.of("nonchild_close_family", "unrelated",
            "sample_drift", "wrong_generation", "wrong_jailer", "not_paused");

    private ReleasePreviewCompatibilityCapture() { }

    /** Arguments: machine ID, fresh output directory, optional native directory and matching v2 producer actual. */
    public static void main(String[] args) throws IOException {
        StrictJson.require(args.length == 2 || args.length == 4,
                "usage: ReleasePreviewCompatibilityCapture MACHINE_ID OUTPUT_DIRECTORY [KINSHIP_NATIVE_DIRECTORY KINSHIP_NATIVE_ACTUAL_FILE]; "
                + "separate-process registered consumer mode is unavailable; run original mains in the admitted CI Python process");
        String machineId = StrictJson.text(args[0]);
        Path outputRoot = Path.of(args[1]).toAbsolutePath().normalize();
        StrictJson.require(outputRoot.getParent() != null && !Files.exists(outputRoot),
                "fresh approved external output directory required");
        Path nativeDirectory = args.length == 4 ? Path.of(args[2]).toAbsolutePath().normalize() : null;
        Path nativeActualPath = args.length == 4 ? Path.of(args[3]).toAbsolutePath().normalize() : null;
        if (nativeActualPath != null) {
            StrictJson.require(Files.size(nativeActualPath) <= 1_048_576, "native actual exceeds bounded receipt size");
        }
        ControlBuild.FileRef actualPin = nativeActualPath == null ? null : ControlBuild.FileRef.measure(nativeActualPath);
        NativeFixtureBuild.Actual nativeActual = nativeActualPath == null ? null
                : verifyNativeKinshipInput(machineId, nativeDirectory, nativeActualPath);
        if (actualPin != null) {
            actualPin.verify();
            StrictJson.require(!outputRoot.startsWith(nativeDirectory) && !nativeDirectory.startsWith(outputRoot),
                    "native input and Java output directories must be disjoint");
        }
        Files.createDirectory(outputRoot);
        ObjectNode manifest = StrictJson.object();
        manifest.put("schema", "xar.java.releasepreview.compatibility-capture.v2");
        manifest.put("machine_id", machineId);
        manifest.put("observed_at_utc", Instant.now().toString());
        manifest.put("projection_not_original", true);
        manifest.put("game_actions", 0);
        manifest.put("release_effect_or_save_qualified", false);
        ArrayNode vectors = manifest.putArray("vectors");
        for (SupportedBuild build : SupportedBuild.values()) {
            String directory = build == SupportedBuild.CK3_12003 ? "native12003" : "native12004";
            Path output = Files.createDirectory(outputRoot.resolve(directory));
            for (String name : RELEASE_CASES) {
                byte[] original = resource(directory + "/" + name + ".json");
                writeVector(original, output.resolve(name + ".json"), build, vectors,
                        "classpath:/releasepreview/" + directory + "/" + name + ".json", false);
            }
        }
        if (nativeActual != null) {
            Path input = nativeDirectory;
            Path output = Files.createDirectory(outputRoot.resolve("kinship12003"));
            for (String name : KINSHIP_CASES) {
                Path source = input.resolve(name + ".json");
                writeVector(readMatchedNative(nativeActual, source), output.resolve(name + ".json"),
                        SupportedBuild.CK3_12003, vectors, source.toString(), true);
            }
        } else {
            manifest.put("kinship_capture_status", "NOT_RUN_NO_NATIVE_PRODUCER_DIRECTORY_SUPPLIED");
        }
        if (nativeActual != null) {
            verifyNativeKinshipInput(machineId, nativeDirectory, nativeActualPath);
            actualPin.verify();
        }
        manifest.put("registered_consumer_status", "NOT_RUN_REQUIRES_ADMITTED_SAME_PYTHON_PROCESS");
        manifest.put("registered_consumer_qualification_granted", false);
        writeManifest(outputRoot, manifest);
    }


    /** Family bindings after the shared strict v2 stage, terminal and complete source/tool reader. */
    static NativeFixtureBuild.Actual verifyNativeKinshipInput(
            String machineId, Path nativeDirectory, Path actualPath) throws IOException {
        NativeFixtureBuild.Actual actual = NativeFixtureBuild.readActual(
                actualPath, NativeFixtureBuild.ActualStage.KINSHIP_PRODUCER);
        Path input = nativeDirectory.toAbsolutePath().normalize();
        StrictJson.require(actual.machineId().equals(machineId), "native producer machine differs");
        StrictJson.require(Files.isDirectory(input, LinkOption.NOFOLLOW_LINKS)
                && !Files.isSymbolicLink(input), "plain native input directory required");
        StrictJson.require(actual.command().size() == 2, "kinship producer requires exact EXE/output argv");
        Path executable = Path.of(actual.command().getFirst());
        StrictJson.require(executable.isAbsolute() && Path.of(actual.command().get(1)).isAbsolute(),
                "absolute kinship producer EXE/output argv required");
        executable = executable.normalize();
        Path exactExecutable = executable;
        StrictJson.require(executable.getFileName() != null
                && executable.getFileName().toString().equals("ck3_12003_prisoner_native_kinship_test.exe")
                && Path.of(actual.command().get(1)).toAbsolutePath().normalize().equals(input)
                && Path.of(actual.ownerIdentity().executable()).toAbsolutePath().normalize().equals(executable),
                "kinship producer EXE, process image or output directory differs");
        List<ControlBuild.FileRef> executablePins = actual.linkedArtifactRefs().stream()
                .filter(pin -> Path.of(pin.path()).toAbsolutePath().normalize().equals(exactExecutable)).toList();
        StrictJson.require(executablePins.size() == 1, "one exact linked kinship EXE reference required");
        executablePins.getFirst().verify();
        Set<Path> expected = new HashSet<>();
        for (String name : KINSHIP_CASES) { expected.add(input.resolve(name + ".json")); }
        Set<Path> outputs = new HashSet<>();
        StrictJson.require(actual.outputRefs().size() == KINSHIP_CASES.size(), "exact six native output refs required");
        for (ControlBuild.FileRef pin : actual.outputRefs()) {
            Path path = Path.of(pin.path()).toAbsolutePath().normalize();
            StrictJson.require(expected.contains(path) && outputs.add(path)
                    && pin.bytes() > 0 && pin.bytes() <= ReleaseCollectionProjection12003.MAX_BYTES,
                    "native output ref is duplicate, foreign, empty or oversized");
        }
        StrictJson.require(outputs.equals(expected), "native output refs omit a mandatory case");
        try (var entries = Files.list(input)) {
            List<Path> files = entries.limit(KINSHIP_CASES.size() + 1L).toList();
            StrictJson.require(files.size() == expected.size()
                    && files.stream().allMatch(path -> expected.contains(path.toAbsolutePath().normalize())),
                    "native input directory has missing or extra entries");
        }
        return actual;
    }

    private static byte[] readMatchedNative(NativeFixtureBuild.Actual actual, Path source) throws IOException {
        Path absolute = source.toAbsolutePath().normalize();
        ControlBuild.FileRef pin = actual.outputRefs().stream()
                .filter(value -> Path.of(value.path()).toAbsolutePath().normalize().equals(absolute))
                .findFirst().orElseThrow(() -> new IOException("native vector is not bound by producer actual"));
        pin.verify();
        byte[] raw;
        try (var input = Files.newInputStream(absolute)) {
            raw = input.readNBytes(ReleaseCollectionProjection12003.MAX_BYTES + 1);
        }
        StrictJson.require(raw.length == pin.bytes() && raw.length <= ReleaseCollectionProjection12003.MAX_BYTES
                && hash(raw).equals(pin.sha256()), "native vector changed while reading");
        return raw;
    }

    private static void writeManifest(Path outputRoot, ObjectNode manifest) throws IOException {
        Files.write(outputRoot.resolve("CAPTURE.json"), StrictJson.canonical(manifest, 131_072),
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
    }

    private static void writeVector(byte[] original, Path output, SupportedBuild build,
                                    ArrayNode manifest, String source, boolean nativeKinshipRequired) throws IOException {
        ObjectNode envelope = (ObjectNode) StrictJson.parse(original, ReleaseCollectionProjection12003.MAX_BYTES);
        JsonNode value = envelope.get("player_prisoner_collection");
        JsonNode rows = value.get("prisoners");
        if (nativeKinshipRequired) {
            StrictJson.require(StrictJson.integer(value.get("schema_version"), 7, 7) == 7,
                    "native kinship input requires schema seven");
        }
        // All retained real producer vectors explicitly selected source ordinal 2.
        FrameBinding selected = new FrameBinding(
                StrictJson.integer(envelope.get("snapshot_revision"), BigInteger.ONE, StrictJson.UINT64_MAX),
                (int) StrictJson.integer(value.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE),
                StrictJson.integer(value.get("played_character_id"), 1, ReleasePreviewValues12003.UINT32_MAX),
                StrictJson.integer(rows.get(2).get("prisoner_character_id"), 1, ReleasePreviewValues12003.UINT32_MAX));
        ReleaseCollectionProjection12003.Observation observed =
                ReleaseCollectionProjection12003.decode(original, build, selected);
        StrictJson.require(observed.selectedOrdinal() == 2, "real producer selected ordinal changed");
        if (nativeKinshipRequired) {
            StrictJson.require(observed.rows().size() == 4, "native kinship producer requires the whole four-row collection");
        }
        for (ReleaseCollectionProjection12003.Row row : observed.rows()) {
            ObjectNode wireRow = (ObjectNode) rows.get(row.sourceOrdinal());
            wireRow.set("unconditional_release_preview", ReleasePreviewCodec12003.toNode(row.preview()));
            if (!(row.nativeKinship() instanceof NativeKinship12003.Missing)) {
                wireRow.set("native_kinship", NativeKinshipCodec12003.toNode(row.nativeKinship()));
            }
        }
        byte[] generated = StrictJson.canonical(envelope, ReleaseCollectionProjection12003.MAX_BYTES);
        StrictJson.require(StrictJson.parse(original, ReleaseCollectionProjection12003.MAX_BYTES)
                .equals(StrictJson.parse(generated, ReleaseCollectionProjection12003.MAX_BYTES)),
                "Java serialization changed a real producer value");
        Files.write(output, generated, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        ObjectNode vector = manifest.addObject();
        vector.put("original_source", source);
        vector.put("original_sha256", hash(original));
        vector.put("java_output", output.toString());
        vector.put("java_output_sha256", hash(generated));
        vector.put("projection_not_original", true);
        vector.put("build", build.version());
    }

    private static byte[] resource(String name) throws IOException {
        try (var input = ReleasePreviewCompatibilityCapture.class.getResourceAsStream("/releasepreview/" + name)) {
            if (input == null) { throw new IOException("missing real producer vector: " + name); }
            return input.readAllBytes();
        }
    }
    private static String hash(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("SHA-256 unavailable", error); }
    }
}
