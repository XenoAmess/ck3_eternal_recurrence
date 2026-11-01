package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintWriter;
import java.io.Writer;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.platform.GameSupervisorControl;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.platform.NativeGameAttachment;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** One actual independent full Native READ. The archived result grants no business or Game ownership. */
public final class NativeOwnerSnapshotMain268 {
    private static final int SMALL = 1 << 20;
    private static String stage = "ARGUMENTS";
    private static Path createdOutput;
    private NativeOwnerSnapshotMain268() { }

    public static void main(String[] args) {
        try {
            if (args.length != 3) throw new IOException("expected descriptorPath configPath freshOutputDirectory");
            run(Path.of(args[0]).toAbsolutePath().normalize(), Path.of(args[1]).toAbsolutePath().normalize(),
                    Path.of(args[2]).toAbsolutePath().normalize());
        } catch (Exception | LinkageError failure) {
            if (failure instanceof InterruptedException) Thread.currentThread().interrupt();
            ObjectNode diagnostic = StrictJson.object().put("schema", "xar.native-owner-snapshot-failure/v1")
                    .put("status", "FAILED").put("stage", stage).put("at_utc", Instant.now().toString())
                    .put("exception", failure.getClass().getName()).put("message", bounded(failure.getMessage(), 4096));
            if (createdOutput != null) try { write(createdOutput, "failure.json", FullJsonTree.encode(diagnostic, SMALL)); }
            catch (IOException | RuntimeException saving) { failure.addSuppressed(saving); }
            System.err.println(diagnostic);
            printBounded(failure);
            System.exit(1);
        }
    }

    private static void run(Path descriptorPath, Path configPath, Path output) throws IOException, InterruptedException {
        stage = "INPUTS";
        byte[] configBytes = readBounded(configPath, SMALL);
        ObjectNode config = StrictJson.object(StrictJson.parse(configBytes, SMALL), Set.of("schema", "owner_descriptor",
                "overall_timeout_seconds", "read_timeout_seconds", "maximum_frames_per_operation"));
        StrictJson.require("xar.native-owner-snapshot-config/v1".equals(StrictJson.text(config.get("schema"))), "snapshot config schema differs");
        ExactRef expectedDescriptor = ExactRef.fromJson(config.get("owner_descriptor"));
        StrictJson.require(Path.of(expectedDescriptor.path()).toAbsolutePath().normalize().equals(descriptorPath), "descriptor path differs from explicit config");
        long overall = StrictJson.integer(config.get("overall_timeout_seconds"), 1, 600);
        long readSeconds = StrictJson.integer(config.get("read_timeout_seconds"), 1, 60);
        int frames = Math.toIntExact(StrictJson.integer(config.get("maximum_frames_per_operation"), 1, 65536));
        Instant entered = Instant.now(), deadline = entered.plusSeconds(overall);
        byte[] descriptorBytes = readExact(expectedDescriptor, GameSupervisorControl.MAXIMUM_DESCRIPTOR_BYTES);
        SharedSourceFiles.Witness descriptorWitness = SharedSourceFiles.observe(descriptorPath);
        requireWitnessBytes(descriptorWitness, expectedDescriptor);
        GameSupervisorControl.Descriptor owner = GameSupervisorControl.readDescriptor(descriptorPath);
        if (!descriptorWitness.equals(SharedSourceFiles.observe(descriptorPath))) throw new IOException("descriptor identity changed during parsing");
        if (!Arrays.equals(descriptorBytes, readExact(expectedDescriptor, GameSupervisorControl.MAXIMUM_DESCRIPTOR_BYTES)))
            throw new IOException("descriptor differs from the exact parsed source");
        var plan = owner.configuration().accept();
        if (!(plan.load() instanceof NativeLaunchPlan.SavedGame)) throw new IOException("actual owner must retain its SavedGame plan");
        var saved = (NativeLaunchPlan.SavedGame) plan.load();
        Files.createDirectory(output);
        createdOutput = output;
        ObjectNode originals = StrictJson.object();
        originals.set("owner_descriptor", write(output, "owner-descriptor.json", descriptorBytes));
        originals.set("snapshot_config", write(output, "snapshot-config.json", configBytes));
        originals.set("owner_hello", write(output, "owner-hello.bin", readExact(owner.nativeHello(), SMALL)));
        originals.set("owner_launch_evidence", write(output, "owner-launch-evidence.json", readExact(owner.launchEvidence(), SMALL)));
        ObjectNode result = StrictJson.object().put("schema", "xar.native-owner-snapshot/v1")
                .put("entered_at_utc", entered.toString()).put("operation_deadline_utc", deadline.toString())
                .put("original_launch_deadline_utc", plan.deadline().toString()).put("read_calls", 1)
                .put("business_or_source_admission", false).put("saved_basename", saved.basename());
        result.set("configured_saved_file", new ExactRef(saved.save().path(), saved.save().bytes(), saved.save().sha256()).toJson());
        result.set("owner_descriptor", expectedDescriptor.toJson());
        result.set("owner_descriptor_native_identity", nativeIdentity(descriptorWitness.nativeFile()));
        result.set("supervisor", identity(owner.supervisorIdentity()));
        result.set("game", owner.generation().toJson());
        stage = "ATTACH";
        try (var supervisor = WindowsJobProcess.retainReadOnlyProcess(owner.supervisorIdentity().pid())) {
            requireSupervisor(supervisor, owner.supervisorIdentity());
            var request = new NativeGameAttachment.Request(plan, owner.generation(), List.of(), frames, 1);
            // This factory returns ATTACHED only. Its close releases communication and readonly handles, never a Job.
            try (ManagedGameSession game = NativeGameAttachment.attach(request, deadline, Duration.ofSeconds(readSeconds))) {
                if (game.mode() != ManagedGameSession.Mode.ATTACHED) throw new IOException("actual attachment mode differs");
                requireSupervisor(supervisor, owner.supervisorIdentity());
                var transport = game.nativeTransport();
                var hello = transport.diagnostics().originalHello().orElseThrow(() -> new IOException("actual received HELLO unavailable"));
                originals.set("new_hello", write(output, "new-hello.bin", hello.original().packet().value()));
                result.put("hello_observed_at_utc", hello.observedAt().toString());
                stage = "ONE_FRESH_READ";
                NativeFreshSnapshotPort.Result read = transport.readFreshFullState(deadline);
                originals.set("dispatch", saveDispatch(output, read.dispatch()));
                if (read instanceof NativeFreshSnapshotPort.Unavailable unavailable) {
                    ObjectNode rejected = StrictJson.object().put("reason", unavailable.reason());
                    if (unavailable.originalFrame().isPresent()) rejected.set("frame", saveFrame(output, unavailable.originalFrame().orElseThrow()));
                    if (unavailable.snapshotReceived().isPresent()) rejected.set("snapshot_received", event(unavailable.snapshotReceived().orElseThrow()));
                    rejected.set("originals", originals);
                    write(output, "unavailable.json", FullJsonTree.encode(rejected, FullJsonTree.MAXIMUM_BYTES));
                    throw new IOException("original fresh READ unavailable; no retry: " + unavailable.reason());
                }
                var received = (NativeFreshSnapshotPort.Received) read;
                NativeFreshSnapshotPort.verifyOriginal(received.acknowledgement(), received.originalFrame(), received.snapshotReceived());
                var frame = received.originalFrame();
                if (!frame.session().game().equals(owner.generation()) || !frame.session().machineId().equals(owner.machineId())
                        || !frame.session().sessionId().equals(owner.sessionId())
                        || !transport.diagnostics().session().filter(frame.session()::equals).isPresent()
                        || hello.original().pid() != owner.generation().pid()
                        || !hello.original().connectionGeneration().equals(frame.session().connectionGeneration()))
                    throw new IOException("actual READ/HELLO crossed expected owner Game/session/connection");
                stage = "PRESERVE_READ";
                originals.set("frame", saveFrame(output, frame));
                result.set("session", session(frame.session()));
                result.put("request_id", received.acknowledgement().requestId()).put("snapshot_id", frame.snapshotId())
                        .put("native_revision", frame.nativeRevision().toString()).put("observed_at_utc", frame.observedAt().toString());
                result.set("snapshot_received", event(received.snapshotReceived()));
                JsonNode parsedState = FullJsonTree.parse(frame.state().bytes(), FullJsonTree.MAXIMUM_BYTES);
                if (!(parsedState instanceof ObjectNode)) throw new IOException("actual full state must be an object");
                ObjectNode state = (ObjectNode) parsedState;
                ObjectNode observed = StrictJson.object();
                for (String field : List.of("date_raw", "paused", "map_ready", "speed", "context", "campaign", "campaign_id", "game_id"))
                    observed.set(field, state.has(field) ? state.get(field).deepCopy() : com.fasterxml.jackson.databind.node.TextNode.valueOf("UNKNOWN"));
                JsonNode player = state.get("played_character");
                observed.set("played_character_id", player != null && player.isObject() && player.has("character_id")
                        ? player.get("character_id").deepCopy() : com.fasterxml.jackson.databind.node.TextNode.valueOf("UNKNOWN"));
                result.set("observed", observed);
                var keys = result.putArray("native_state_top_keys");
                for (var field : state.properties()) keys.add(field.getKey());
                requireSupervisor(supervisor, owner.supervisorIdentity());
                game.verify();
                if (!descriptorWitness.equals(SharedSourceFiles.observe(descriptorPath))) throw new IOException("original owner descriptor changed during READ");
                stage = "RELEASE_ENDPOINT";
            }
        }
        // Success is published only after actual ATTACHED endpoint and readonly handles have closed successfully.
        stage = "PUBLISH_ARCHIVED_DATA";
        result.set("originals", originals);
        result.put("status", "ARCHIVED_NATIVE_READ_DATA_ENDPOINT_RELEASED").put("completed_at_utc", Instant.now().toString());
        ObjectNode published = write(output, "summary.json", FullJsonTree.encode(result, FullJsonTree.MAXIMUM_BYTES));
        System.out.println(StrictJson.object().put("schema", "xar.native-owner-snapshot-stage/v1")
                .put("status", "ARCHIVED_NATIVE_READ_DATA_ENDPOINT_RELEASED").put("at_utc", Instant.now().toString()).set("summary", published));
    }

    private static ObjectNode saveDispatch(Path output, NativeActionPort.DispatchOutcome dispatch) throws IOException {
        ObjectNode row = StrictJson.object().put("request_id", dispatch.requestId()).put("class", dispatch.getClass().getSimpleName());
        if (dispatch instanceof NativeActionPort.AckReceived ack) {
            row.put("native_ok", ack.nativeOk());
            row.set("ack_packet", write(output, "read-ack.bin", ack.originalPacket()));
            row.set("ack_payload", write(output, "read-ack-payload.json", ack.originalFrame().bytes()));
            if (ack.originalResultToken().isPresent()) row.set("result_token", write(output, "read-result-token.json", ack.originalResultToken().orElseThrow().bytes()));
            if (ack.outbound().isPresent()) row.set("outbound", write(output, "read-outbound.bin", ack.outbound().orElseThrow().originalPacket()));
            if (ack.custody().isPresent()) {
                var custody = ack.custody().orElseThrow(); custody.verify(ack);
                ObjectNode actual = StrictJson.object().put("request_id", custody.requestId()).put("custody_epoch", custody.custodyEpoch().toString());
                actual.set("session", session(custody.session()));
                actual.set("original_request", packet(custody.originalRequest())); actual.set("original_response", packet(custody.originalResponse()));
                actual.set("write_entered", event(custody.writeEntered())); actual.set("write_completed", event(custody.writeCompleted()));
                actual.set("response_received", event(custody.responseReceived()));
                row.set("actual_custody", actual);
                row.set("custody_material", write(output, "read-custody.json", FullJsonTree.encode(actual, SMALL)));
            }
        } else if (dispatch instanceof NativeActionPort.Unknown unknown) {
            row.put("reason", unknown.reason()).put("original_request_bytes", unknown.originalRequestPacket().length);
            if (unknown.originalRequestPacket().length > 0) row.set("outbound", write(output, "read-outbound.bin", unknown.originalRequestPacket()));
            if (unknown.rawReturn().isPresent()) row.set("raw_return", write(output, "read-raw-return.json", unknown.rawReturn().orElseThrow().bytes()));
            if (unknown.failureCause().isPresent()) {
                var cause = unknown.failureCause().orElseThrow();
                row.put("failure_kind", cause.kind().name()).put("failure_stage", cause.stage().name());
                if (cause.originalException().isPresent()) row.put("original_exception", cause.originalException().orElseThrow().javaType()).put("original_message", cause.originalException().orElseThrow().message());
                if (cause.originalCause().isPresent()) row.put("original_cause", cause.originalCause().orElseThrow().javaType()).put("original_cause_message", cause.originalCause().orElseThrow().message());
                if (cause.deadline().isPresent()) {
                    var observed = cause.deadline().orElseThrow();
                    row.put("supplied_deadline", observed.suppliedDeadline().toString()).put("deadline_observed_at", observed.observedAt().toString()).put("monotonic_expired", observed.monotonicExpired());
                }
            }
        } else {
            var zero = ((NativeActionPort.RejectedBeforeDispatch) dispatch).proof();
            row.put("stage", zero.stage().name()).put("request_bytes_written", zero.requestBytesWritten()).put("reason", zero.reason());
            if (zero.diagnostic().isPresent()) row.set("diagnostic", write(output, "read-zero-diagnostic.json", zero.diagnostic().orElseThrow().bytes()));
        }
        row.set("dispatch_material", write(output, "read-dispatch.json", FullJsonTree.encode(row, FullJsonTree.MAXIMUM_BYTES)));
        return row;
    }

    private static ObjectNode saveFrame(Path output, NativeObservationPort.ObservedFrame frame) throws IOException {
        ObjectNode row = StrictJson.object().put("snapshot_id", frame.snapshotId()).put("native_revision", frame.nativeRevision().toString()).put("observed_at_utc", frame.observedAt().toString());
        row.set("session", session(frame.session()));
        row.set("packet", write(output, "native-frame.bin", frame.originalPacket()));
        row.set("raw_state", write(output, "native-state.json", frame.state().bytes()));
        return row;
    }
    private static ObjectNode session(NativeObservationPort.TransportSession session) {
        ObjectNode row = StrictJson.object().put("machine_id", session.machineId()).put("session_id", session.sessionId()).put("connection_generation", session.connectionGeneration().toString());
        row.set("game", session.game().toJson()); return row;
    }
    private static ObjectNode event(NativeRequestChronology.Event event) { return StrictJson.object().put("order", event.order().toString()).put("observed_at_utc", event.observedAt().toString()); }
    private static ObjectNode packet(NativeRequestChronology.PacketIdentity packet) { return StrictJson.object().put("bytes", packet.bytes()).put("sha256", packet.sha256()); }
    private static ObjectNode identity(WindowsJobProcess.ProcessIdentity identity) {
        return StrictJson.object().put("pid", identity.pid()).put("creation_filetime", identity.creationFiletimeDecimal()).put("executable", identity.executable());
    }
    private static ObjectNode nativeIdentity(SharedSourceFiles.NativeFile actual) {
        return StrictJson.object().put("volume_serial_decimal", actual.volumeSerialDecimal()).put("file_id_decimal", actual.fileIdDecimal())
                .put("creation_filetime_decimal", actual.creationFiletimeDecimal()).put("last_write_filetime_decimal", actual.lastWriteFiletimeDecimal())
                .put("change_filetime_decimal", actual.changeFiletimeDecimal()).put("logical_bytes", actual.logicalBytes()).put("allocated_bytes", actual.allocatedBytes()).put("link_count", actual.linkCount());
    }
    private static ObjectNode write(Path directory, String name, byte[] original) throws IOException {
        Path target = directory.resolve(name);
        try (FileChannel file = FileChannel.open(target, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            ByteBuffer buffer = ByteBuffer.wrap(original); while (buffer.hasRemaining()) file.write(buffer); file.force(true);
        }
        var witness = SharedSourceFiles.observe(target);
        var expected = new ExactRef(target.toString(), original.length, sha256(original));
        requireWitnessBytes(witness, expected);
        ObjectNode row = StrictJson.object(); row.set("reference", expected.toJson()); row.set("native_identity", nativeIdentity(witness.nativeFile())); return row;
    }
    private static byte[] readBounded(Path path, int maximum) throws IOException {
        try (InputStream input = Files.newInputStream(path)) {
            byte[] bytes = input.readNBytes(maximum + 1);
            if (bytes.length == 0 || bytes.length > maximum) throw new IOException("bounded nonempty source required: " + path);
            return bytes;
        }
    }
    private static byte[] readExact(ExactRef ref, int maximum) throws IOException {
        if (ref.bytes() < 1 || ref.bytes() > maximum) throw new IOException("exact source exceeds its finite role");
        byte[] raw = readBounded(Path.of(ref.path()), maximum);
        if (raw.length != ref.bytes() || !sha256(raw).equals(ref.sha256())) throw new IOException("exact source bytes/SHA differ: " + ref.path()); return raw;
    }
    private static void requireWitnessBytes(SharedSourceFiles.Witness witness, ExactRef ref) throws IOException {
        if (witness.source().bytes() != ref.bytes() || !witness.source().sha256().equals(ref.sha256())) throw new IOException("source witness differs from exact bytes/SHA");
    }
    private static void requireSupervisor(WindowsJobProcess.ReadOnlyProcessHandle actual, WindowsJobProcess.ProcessIdentity expected) throws IOException {
        if (!actual.identity().equals(expected) || actual.waitZero() != 258L) throw new IOException("actual supervisor exited or changed identity");
    }
    private static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException impossible) { throw new AssertionError(impossible); }
    }
    private static String bounded(String value, int limit) { return value == null ? null : value.substring(0, Math.min(limit, value.length())); }
    private static void printBounded(Throwable failure) {
        PrintWriter sink = new PrintWriter(new Writer() {
            private int remaining = 32768;
            @Override public void write(char[] chars, int offset, int length) { int count = Math.min(length, remaining); if (count > 0) { System.err.print(new String(chars, offset, count)); remaining -= count; } }
            @Override public void flush() { System.err.flush(); }
            @Override public void close() { flush(); }
        });
        failure.printStackTrace(sink); sink.flush();
    }
}
