package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Objects;

import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Explicit software fixture inputs only. These values cannot supply Native, Current or private Root authority. */
public final class SdkFixtureProductionInputs {
    public static final String LEGACY_SCHEMA = "xar.sdk-original-software-fixture-inputs/v1";
    public static final String SCHEMA = "xar.sdk-original-software-fixture-inputs/v2";
    public static final String BUNDLE_SCHEMA_PROPERTY = "xar.sdk.original.software.bundle.schema";
    public static final String LOBBY_DIRECTORY = "xar.g2.frontend.lobby.callback.frames";
    public static final List<String> LOBBY_NAMES = List.of("lobby-callback-request.json", "lobby-callback.json",
            "lobby-callback-unavailable.json", "lobby-callback-bad-slot.json", "lobby-callback-bad-pin.json");
    public static final String M7_DIRECTORY = "xar.m7.formalNativeWireDirectory";
    public static final String M7_SCRATCH = "xar.m7.formalNativeWireScratch";
    public static final String M5_WIRE = "xar.nestedQuantity12004.nativeWire";
    public static final String M5_SHA256 = "xar.nestedQuantity12004.nativeWireSha256";
    public static final String M5_MACHINE = "xar.nestedQuantity12004.machineId";
    private static final String M5_BYTES = "xar.sdk.original.software.nestedWire.bytes";
    private static final int MAX_METADATA_BYTES = 65536;
    private SdkFixtureProductionInputs() { }

    /** Metadata producer only; the admitted caller guards every input identity and the complete process lease. */
    public static void main(String[] arguments) throws IOException {
        if (arguments.length != 5 || !arguments[1].matches("[1-9][0-9]{0,8}") || !arguments[4].matches("[1-9][0-9]{0,8}"))
            throw new IllegalArgumentException("INPUT_PATH BYTES SHA256 NEW_BUNDLE_PATH MAX_NATIVE_BYTES required");
        FileRef inputRef = new FileRef(arguments[0], Long.parseLong(arguments[1]), arguments[2]);
        Path destination = absolute(arguments[3]); long maximum = Long.parseLong(arguments[4]);
        if (maximum > 1L << 20 || destination.getParent() == null) throw new IllegalArgumentException("Finite metadata output bound required");
        long unit = NativeStorageGeometry.read(destination.getParent()).clusterBytes();
        if (unit < 1 || unit > 1L << 20) throw new IOException("Bounded actual allocation unit required");
        FreshSdkFixtureStage.ResourceGuard guard = pending -> {
            inputRef.verify();
            if (pending < 0) throw new IOException("Nonnegative metadata allocation required");
            long used = Files.exists(destination) ? SharedSourceFiles.nativeFile(destination).allocatedBytes() : 0;
            long reserved = Math.multiplyExact(Math.floorDiv(Math.addExact(pending, unit - 1), unit), unit);
            if (Math.addExact(unit, Math.addExact(used, reserved)) > maximum) throw new IOException("Fixture metadata exceeds admitted native bound");
        };
        FileRef output = write(read(inputRef), destination, guard); inputRef.verify();
        System.out.println(ControlBuild.strictMapper().writeValueAsString(output));
    }

    public record LawWireSet(String directory, List<FileRef> originals) {
        public LawWireSet {
            absolute(directory); originals = List.copyOf(originals);
            if (originals.size() != 4) throw new IllegalArgumentException("Four original law wire refs required");
            var names = new java.util.HashSet<Path>(); Path root = Path.of(directory);
            for (FileRef original : originals) {
                Path path = absolute(original.path());
                if (!root.equals(path.getParent()) || !names.add(path)) throw new IllegalArgumentException("Distinct original wires in the exact declared directory required");
            }
        }
    }

    public record LobbyWireSet(String directory, List<FileRef> originals) {
        public LobbyWireSet {
            Path root = absolute(directory); originals = List.copyOf(originals);
            if (originals.size() != LOBBY_NAMES.size()) throw new IllegalArgumentException("Five actual original lobby wires required");
            var names = new java.util.HashSet<String>();
            for (FileRef ref : originals) {
                Path path = absolute(ref.path()); String name = path.getFileName().toString();
                if (!root.equals(path.getParent()) || !LOBBY_NAMES.contains(name) || !names.add(name)
                        || ref.bytes() < 1 || ref.bytes() > 1L << 20)
                    throw new IllegalArgumentException("Distinct bounded lobby originals with the five exact basenames required");
            }
        }
    }

    /** A complete bundle requires the genuinely produced M5 wire; a pending producer plan is a different artifact. */
    public record Inputs(String schema, String machineId, String reviewAtUtc, FileRef guiConfigurationRef,
            LawWireSet lawWires, String lawScratchDirectory, FileRef nestedQuantityWireRef, LobbyWireSet lobbyWires) {
        public Inputs {
            if ((!SCHEMA.equals(schema) && !LEGACY_SCHEMA.equals(schema)) || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,127}")
                    || machineId.equals("unknown")) throw new IllegalArgumentException("Exact software fixture input schema and machine required");
            Instant.parse(reviewAtUtc); Objects.requireNonNull(guiConfigurationRef); Objects.requireNonNull(lawWires);
            absolute(lawScratchDirectory); Objects.requireNonNull(nestedQuantityWireRef);
            if (SCHEMA.equals(schema) != (lobbyWires != null)) throw new IllegalArgumentException("Current four-package schema requires lobby wires; legacy DATA has none");
            if (guiConfigurationRef.bytes() < 1 || guiConfigurationRef.bytes() > MAX_METADATA_BYTES
                    || nestedQuantityWireRef.bytes() < 1 || nestedQuantityWireRef.bytes() > 1L << 20)
                throw new IllegalArgumentException("Bounded actual fixture artifacts required");
        }
    }

    private record LegacyInputs(String schema, String machineId, String reviewAtUtc, FileRef guiConfigurationRef,
            LawWireSet lawWires, String lawScratchDirectory, FileRef nestedQuantityWireRef) { }

    public static void requireCurrent(Inputs inputs) {
        if (!SCHEMA.equals(inputs.schema()) || inputs.lobbyWires() == null)
            throw new IllegalArgumentException("Legacy three-package fixture data cannot authorize current four-package production");
    }

    public static Inputs decode(byte[] bytes) throws IOException {
        if (bytes.length < 1 || bytes.length > MAX_METADATA_BYTES) throw new IOException("Bounded fixture inputs required");
        var mapper = ControlBuild.strictMapper(); var tree = mapper.readTree(bytes);
        if (tree == null || !tree.isObject() || !tree.path("schema").isTextual()) throw new IOException("Object with exact fixture schema required");
        if (LEGACY_SCHEMA.equals(tree.path("schema").textValue())) {
            LegacyInputs old = mapper.treeToValue(tree, LegacyInputs.class);
            return new Inputs(old.schema(), old.machineId(), old.reviewAtUtc(), old.guiConfigurationRef(), old.lawWires(),
                    old.lawScratchDirectory(), old.nestedQuantityWireRef(), null);
        }
        return mapper.treeToValue(tree, Inputs.class);
    }
    public static byte[] encode(Inputs inputs) throws IOException {
        Object encoded = LEGACY_SCHEMA.equals(inputs.schema())
                ? new LegacyInputs(inputs.schema(), inputs.machineId(), inputs.reviewAtUtc(), inputs.guiConfigurationRef(), inputs.lawWires(),
                        inputs.lawScratchDirectory(), inputs.nestedQuantityWireRef()) : inputs;
        byte[] bytes = ControlBuild.strictMapper().writeValueAsBytes(encoded);
        if (bytes.length > MAX_METADATA_BYTES || !decode(bytes).equals(inputs)) throw new IOException("Fixture input serialization roundtrip differs");
        return bytes;
    }
    public static Inputs read(FileRef ref) throws IOException {
        if (ref.bytes() < 1 || ref.bytes() > MAX_METADATA_BYTES) throw new IOException("Bounded exact fixture input ref required");
        ref.verify(); Inputs value = decode(Files.readAllBytes(Path.of(ref.path()))); ref.verify(); return value;
    }

    public static List<FileRef> inputRefs(Inputs inputs) throws IOException {
        var refs = new ArrayList<FileRef>(List.of(inputs.guiConfigurationRef(), inputs.nestedQuantityWireRef()));
        GuiEightOracleFixture.Config gui = GuiEightOracleFixture.readConfiguration(inputs.guiConfigurationRef());
        if (!gui.machineId().equals(inputs.machineId()) || Instant.parse(gui.reviewAtUtc()).isBefore(Instant.parse(inputs.reviewAtUtc())))
            throw new IOException("One actual fixture machine and sufficient GUI data review required");
        refs.add(gui.python());
        for (GuiEightOracleFixture.Source source : gui.sources()) refs.add(source.original());
        refs.addAll(inputs.lawWires().originals());
        if (inputs.lobbyWires() != null) refs.addAll(inputs.lobbyWires().originals());
        var unique = new LinkedHashMap<String, FileRef>();
        for (FileRef ref : refs) {
            String key = absolute(ref.path()).toString().toLowerCase(Locale.ROOT);
            FileRef previous = unique.putIfAbsent(key, ref);
            if (previous != null && !previous.equals(ref)) throw new IOException("Conflicting original fixture refs");
        }
        return List.copyOf(unique.values());
    }

    public static void verify(Inputs inputs) throws IOException {
        requireCurrent(inputs);
        if (!inputs.machineId().equals(WindowsJobProcess.currentMachineId()) || !Instant.now().isBefore(Instant.parse(inputs.reviewAtUtc())))
            throw new IOException("Current machine and unexpired source data required; no execution authority is inferred");
        Path directory = absolute(inputs.lawWires().directory()); SharedSourceFiles.plainAncestors(directory);
        if (!Files.isDirectory(directory)) throw new IOException("Actual original law wire directory missing");
        Path scratch = absolute(inputs.lawScratchDirectory()); SharedSourceFiles.plainAncestors(scratch);
        if (!Files.isDirectory(scratch) || scratch.startsWith(directory))
            throw new IOException("Existing separately owned scratch outside immutable law inputs required");
        Path lobby = absolute(inputs.lobbyWires().directory()); SharedSourceFiles.plainAncestors(lobby);
        if (!Files.isDirectory(lobby) || scratch.startsWith(lobby)) throw new IOException("Actual immutable lobby directory and separate scratch required");
        ProjectStoragePolicy.requireBulkOutput(scratch);
        for (FileRef input : inputRefs(inputs)) { SharedSourceFiles.plainAncestors(Path.of(input.path())); input.verify(); }
    }

    /** An exact CLI projection, not a second fixture contract. Replay never opens current files or environment. */
    public enum Generation { V1_THREE, V2_FOUR }
    public record CommandArguments(Generation generation, FileRef guiConfigurationRef, String lawWireDirectory, String lawScratchDirectory,
            FileRef nestedQuantityWireRef, String machineId, String lobbyWireDirectory) {
        public CommandArguments {
            Objects.requireNonNull(generation);
            if ((generation == Generation.V2_FOUR) != (lobbyWireDirectory != null)) throw new IllegalArgumentException("Explicit CLI generation and lobby projection required");
            if (lobbyWireDirectory != null) absolute(lobbyWireDirectory);
            Objects.requireNonNull(guiConfigurationRef); Objects.requireNonNull(nestedQuantityWireRef);
            if (guiConfigurationRef.bytes() < 1 || guiConfigurationRef.bytes() > MAX_METADATA_BYTES
                    || nestedQuantityWireRef.bytes() < 1 || nestedQuantityWireRef.bytes() > 1L << 20)
                throw new IllegalArgumentException("Finite exact recorded GUI/native wire refs required");
            absolute(guiConfigurationRef.path()); absolute(nestedQuantityWireRef.path());
            absolute(lawWireDirectory); absolute(lawScratchDirectory);
            if (machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,127}") || machineId.equals("unknown"))
                throw new IllegalArgumentException("Exact recorded fixture machine required");
        }
        public List<String> mavenArguments() {
            var result = new ArrayList<>(List.of(property(GuiEightOracleFixture.PROPERTY, guiConfigurationRef.path()),
                    property(GuiEightOracleFixture.PROPERTY + ".bytes", Long.toString(guiConfigurationRef.bytes())),
                    property(GuiEightOracleFixture.PROPERTY + ".sha256", guiConfigurationRef.sha256()),
                    property(M7_DIRECTORY, lawWireDirectory), property(M7_SCRATCH, lawScratchDirectory),
                    property(M5_WIRE, nestedQuantityWireRef.path()), property(M5_SHA256, nestedQuantityWireRef.sha256()),
                    property(M5_MACHINE, machineId), property(M5_BYTES, Long.toString(nestedQuantityWireRef.bytes()))));
            if (generation == Generation.V2_FOUR) { result.add(property(BUNDLE_SCHEMA_PROPERTY, SCHEMA)); result.add(property(LOBBY_DIRECTORY, lobbyWireDirectory)); }
            return List.copyOf(result);
        }
    }

    public static CommandArguments commandArguments(Inputs inputs) {
        return new CommandArguments(SCHEMA.equals(inputs.schema()) ? Generation.V2_FOUR : Generation.V1_THREE,
                inputs.guiConfigurationRef(), inputs.lawWires().directory(), inputs.lawScratchDirectory(),
                inputs.nestedQuantityWireRef(), inputs.machineId(), inputs.lobbyWires() == null ? null : inputs.lobbyWires().directory());
    }

    public static CommandArguments fromRecordedArguments(List<String> arguments) {
        FileRef gui = new FileRef(one(arguments, GuiEightOracleFixture.PROPERTY),
                bytes(one(arguments, GuiEightOracleFixture.PROPERTY + ".bytes")), one(arguments, GuiEightOracleFixture.PROPERTY + ".sha256"));
        FileRef nested = new FileRef(one(arguments, M5_WIRE), bytes(one(arguments, M5_BYTES)), one(arguments, M5_SHA256));
        boolean current = has(arguments, BUNDLE_SCHEMA_PROPERTY) || has(arguments, LOBBY_DIRECTORY);
        String lobby = null;
        if (current) {
            if (!SCHEMA.equals(one(arguments, BUNDLE_SCHEMA_PROPERTY))) throw new IllegalArgumentException("Exact v2 bundle schema marker required");
            lobby = one(arguments, LOBBY_DIRECTORY);
        }
        return new CommandArguments(current ? Generation.V2_FOUR : Generation.V1_THREE, gui,
                one(arguments, M7_DIRECTORY), one(arguments, M7_SCRATCH), nested, one(arguments, M5_MACHINE), lobby);
    }

    public static boolean hasRecordedArguments(List<String> arguments) {
        return List.of(GuiEightOracleFixture.PROPERTY, GuiEightOracleFixture.PROPERTY + ".bytes", GuiEightOracleFixture.PROPERTY + ".sha256",
                M7_DIRECTORY, M7_SCRATCH, M5_WIRE, M5_SHA256, M5_MACHINE, M5_BYTES, BUNDLE_SCHEMA_PROPERTY, LOBBY_DIRECTORY).stream()
                .anyMatch(name -> arguments.stream().anyMatch(value -> value.startsWith(property(name, ""))));
    }

    /** The Root-owned scratch exists only after its actual resource lease creates it. This method never creates it. */
    public static List<String> arguments(Inputs inputs) throws IOException {
        verify(inputs); return commandArguments(inputs).mavenArguments();
    }

    public static FileRef write(Inputs inputs, Path destination, FreshSdkFixtureStage.ResourceGuard resources) throws IOException {
        verify(inputs); byte[] bytes = encode(inputs);
        if (!destination.isAbsolute() || !destination.equals(destination.normalize()) || destination.getParent() == null
                || !Files.isDirectory(destination.getParent()) || Files.exists(destination)) throw new IOException("Fresh canonical fixture metadata destination required");
        ProjectStoragePolicy.requireBulkOutput(destination.getParent()); SharedSourceFiles.plainAncestors(destination);
        resources.revalidate(bytes.length); Files.write(destination, bytes, StandardOpenOption.CREATE_NEW);
        FileRef actual = FileRef.measure(destination);
        if (!read(actual).equals(inputs)) throw new IOException("Persisted fixture inputs differ");
        verify(inputs); resources.revalidate(0); return actual;
    }

    private static Path absolute(String value) {
        if (value == null || value.length() > 4096 || value.chars().anyMatch(c -> c < 32 || c == 127))
            throw new IllegalArgumentException("Plain bounded fixture path required");
        Path path = Path.of(value);
        if (!path.isAbsolute() || !path.equals(path.normalize())) throw new IllegalArgumentException("Canonical absolute fixture path required");
        return path;
    }
    private static String property(String name, String value) { return "-D" + name + "=" + value; }
    private static long bytes(String value) {
        if (!value.matches("[1-9][0-9]{0,8}")) throw new IllegalArgumentException("Exact recorded fixture bytes required");
        return Long.parseLong(value);
    }
    private static boolean has(List<String> arguments, String name) { return arguments.stream().anyMatch(value -> value.startsWith(property(name, ""))); }
    private static String one(List<String> arguments, String name) {
        String prefix = property(name, "");
        var values = arguments.stream().filter(value -> value.startsWith(prefix)).map(value -> value.substring(prefix.length())).toList();
        if (values.size() != 1 || values.getFirst().isBlank()) throw new IllegalArgumentException("One exact recorded fixture property required: " + name);
        return values.getFirst();
    }
}

