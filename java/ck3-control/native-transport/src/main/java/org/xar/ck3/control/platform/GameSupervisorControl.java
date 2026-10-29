package org.xar.ck3.control.platform;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

/** Ordinary owner/worker data. These records do not attest sources or grant Game mutation. */
public final class GameSupervisorControl {
    public static final String DESCRIPTOR_FILE = "owner.json";
    public static final String STOP_FILE = "stop-request.json";
    public static final String TERMINAL_FILE = "terminal.json";
    public static final int MAXIMUM_DESCRIPTOR_BYTES = StrictJson.EXPLICIT_MAX_BYTES;
    public static final int MAXIMUM_STOP_BYTES = 16384;

    public record Descriptor(String machineId, String sessionId,
            WindowsJobProcess.ProcessIdentity supervisorIdentity,
            WindowsJobProcess.ProcessIdentity gameIdentity,
            NativeLaunchPlanCodec.Configuration configuration,
            ExactRef nativeHello, ExactRef launchEvidence,
            Path stopRequestPath, Path terminalPath) {
        public Descriptor {
            text(machineId); text(sessionId);
            Objects.requireNonNull(supervisorIdentity); Objects.requireNonNull(gameIdentity);
            Objects.requireNonNull(configuration); Objects.requireNonNull(nativeHello); Objects.requireNonNull(launchEvidence);
            Objects.requireNonNull(stopRequestPath); Objects.requireNonNull(terminalPath);
            if (!sessionId.equals(configuration.sessionId()) || !machineId.equals(configuration.review().machineId())
                    || !stopRequestPath.isAbsolute() || !terminalPath.isAbsolute()
                    || !STOP_FILE.equals(stopRequestPath.getFileName().toString())
                    || !TERMINAL_FILE.equals(terminalPath.getFileName().toString())
                    || !stopRequestPath.getParent().equals(terminalPath.getParent()))
                throw new IllegalArgumentException("one owner session and its local control paths required");
        }
        public GameGeneration generation() { return ManagedGameSession.generation(gameIdentity); }
    }

    public record StopRequest(String requestId, String sessionId,
            WindowsJobProcess.ProcessIdentity gameIdentity, Instant deadline) {
        public StopRequest {
            text(requestId); text(sessionId);
            Objects.requireNonNull(gameIdentity); Objects.requireNonNull(deadline);
        }
        void requireTarget(String expectedSession, WindowsJobProcess.ProcessIdentity expectedGame, Instant now)
                throws IOException {
            if (!sessionId.equals(expectedSession) || !gameIdentity.equals(expectedGame))
                throw new IOException("STOP does not target this owner's actual Game generation");
            if (!now.isBefore(deadline)) throw new IOException("STOP operation deadline expired");
        }
    }

    private GameSupervisorControl() { }

    public static Descriptor readDescriptor(Path source) throws IOException {
        try {
            ObjectNode row = StrictJson.object(StrictJson.parse(readBounded(source, MAXIMUM_DESCRIPTOR_BYTES),
                    MAXIMUM_DESCRIPTOR_BYTES), Set.of("schema", "machine_id", "session_id", "supervisor", "game",
                    "configuration", "native_hello", "launch_evidence", "stop_request_path", "terminal_path"));
            schema(row, "xar.java-game-supervisor-owner/v1");
            Descriptor actual = new Descriptor(StrictJson.text(row.get("machine_id")), StrictJson.text(row.get("session_id")),
                    identity(row.get("supervisor")), identity(row.get("game")),
                    NativeLaunchPlanCodec.fromJson(row.get("configuration")),
                    ExactRef.fromJson(row.get("native_hello")), ExactRef.fromJson(row.get("launch_evidence")),
                    Path.of(StrictJson.text(row.get("stop_request_path"))), Path.of(StrictJson.text(row.get("terminal_path"))));
            Path parent = source.toAbsolutePath().normalize().getParent();
            if (!actual.stopRequestPath().normalize().equals(parent.resolve(STOP_FILE))
                    || !actual.terminalPath().normalize().equals(parent.resolve(TERMINAL_FILE)))
                throw new IOException("owner control files must be siblings of the descriptor");
            return actual;
        } catch (IllegalArgumentException invalid) {
            throw new IOException("Invalid Game owner descriptor", invalid);
        }
    }

    public static void writeStop(Path target, StopRequest request) throws IOException {
        publish(target, encodeStop(Objects.requireNonNull(request)), true);
    }

    public static StopRequest readStop(Path source) throws IOException {
        return decodeStop(readBounded(source, MAXIMUM_STOP_BYTES));
    }

    static StopRequest decodeStop(byte[] raw) throws IOException {
        try {
            ObjectNode row = StrictJson.object(StrictJson.parse(raw, MAXIMUM_STOP_BYTES),
                    Set.of("schema", "request_id", "session_id", "game", "deadline"));
            schema(row, "xar.java-game-supervisor-stop/v1");
            return new StopRequest(StrictJson.text(row.get("request_id")), StrictJson.text(row.get("session_id")),
                    identity(row.get("game")), Instant.parse(StrictJson.text(row.get("deadline"))));
        } catch (IllegalArgumentException | java.time.DateTimeException invalid) {
            throw new IOException("Invalid Game owner STOP request", invalid);
        }
    }

    static byte[] encodeStop(StopRequest request) {
        ObjectNode row = StrictJson.object().put("schema", "xar.java-game-supervisor-stop/v1")
                .put("request_id", request.requestId()).put("session_id", request.sessionId())
                .put("deadline", request.deadline().toString());
        row.set("game", identity(request.gameIdentity()));
        return StrictJson.canonical(row, MAXIMUM_STOP_BYTES);
    }

    static void writeDescriptor(Path target, Descriptor actual) throws IOException {
        ObjectNode row = StrictJson.object().put("schema", "xar.java-game-supervisor-owner/v1")
                .put("machine_id", actual.machineId()).put("session_id", actual.sessionId())
                .put("stop_request_path", actual.stopRequestPath().toString())
                .put("terminal_path", actual.terminalPath().toString());
        row.set("supervisor", identity(actual.supervisorIdentity()));
        row.set("game", identity(actual.gameIdentity()));
        row.set("configuration", NativeLaunchPlanCodec.toJson(actual.configuration()));
        row.set("native_hello", actual.nativeHello().toJson());
        row.set("launch_evidence", actual.launchEvidence().toJson());
        publish(target, StrictJson.canonical(row, MAXIMUM_DESCRIPTOR_BYTES), false);
    }

    static ObjectNode identity(WindowsJobProcess.ProcessIdentity actual) {
        return ManagedGameSession.generation(actual).toJson().put("executable", actual.executable());
    }

    private static WindowsJobProcess.ProcessIdentity identity(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("pid", "creation_filetime", "executable"));
        return new WindowsJobProcess.ProcessIdentity(StrictJson.integer(row.get("pid"), 1, 4294967295L),
                GameGeneration.parseCreationFiletime(row.get("creation_filetime")).value().toString(),
                StrictJson.text(row.get("executable")));
    }

    private static void schema(ObjectNode row, String expected) {
        if (!expected.equals(StrictJson.text(row.get("schema")))) throw new IllegalArgumentException("owner schema required");
    }

    private static void text(String value) {
        if (value == null || value.isBlank() || value.length() > 256)
            throw new IllegalArgumentException("bounded nonempty owner identity required");
    }

    static byte[] readBounded(Path source, int maximum) throws IOException {
        byte[] raw;
        try (var input = Files.newInputStream(source)) { raw = input.readNBytes(maximum + 1); }
        if (raw.length == 0 || raw.length > maximum) throw new IOException("bounded nonempty owner data required");
        return raw;
    }

    /** One publication, not a source-proof or a launch admission operation. */
    static void publish(Path target, byte[] raw, boolean replace) throws IOException {
        Path absolute = target.toAbsolutePath();
        Path temporary = absolute.resolveSibling(absolute.getFileName() + "." + UUID.randomUUID() + ".tmp");
        try {
            try (FileChannel output = FileChannel.open(temporary, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
                ByteBuffer bytes = ByteBuffer.wrap(raw);
                while (bytes.hasRemaining()) output.write(bytes);
                output.force(true);
            }
            if (replace) Files.move(temporary, absolute, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            else Files.move(temporary, absolute, StandardCopyOption.ATOMIC_MOVE);
        } finally { Files.deleteIfExists(temporary); }
    }
}
