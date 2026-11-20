package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Pure strict wire DATA. Only NativeGameTransport may bind a request to an actual CoreReceived occurrence. */
public final class GuiRootIndexFramePublicCodec {
    private GuiRootIndexFramePublicCodec() { }
    public record Request(CoreFrame.Partial expectedCore, BigInteger deadlineUnixMs) {
        public Request {
            GuiRootIndexFrame.requireExpectedCore(expectedCore); Objects.requireNonNull(deadlineUnixMs);
            RegistryJson.require(deadlineUnixMs.signum() > 0 && deadlineUnixMs.compareTo(RegistryJson.U64) <= 0, "positive uint64 query deadline required");
        }
    }
    public static Request request(CoreFrame.Partial expected, Instant deadline) {
        return new Request(expected, BigInteger.valueOf(Objects.requireNonNull(deadline).toEpochMilli()));
    }
    public static RawJson additionalFields(Request request) {
        Objects.requireNonNull(request); var row = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();
        row.putObject("arguments"); var claim = row.putObject("gui_root_index"); var build = GuiRootIndexFrame.BUILD;
        claim.put("schema", GuiRootIndexFrame.REQUEST_SCHEMA).put("game_version", build.version())
                .put("executable_sha256", build.executableSha256().toUpperCase(java.util.Locale.ROOT))
                .put("adapter_id", build.coreFrameAdapterId()).put("backend", GuiRootIndexFrame.BACKEND).put("deadline_unix_ms", request.deadlineUnixMs());
        var p = request.expectedCore().prefix(); var core = claim.putObject("expected_core");
        core.put("date_raw", p.dateRaw()).put("speed", p.speed()).put("paused", p.paused()).put("local_player_id", p.localPlayerId())
                .put("map_ready", p.mapReady()).put("has_played_character", p.hasPlayedCharacter()).put("played_character_id", p.playedCharacterId()).put("played_character_alive", p.playedCharacterAlive());
        RawJson result = RegistryJson.encode(row); RegistryJson.require(decodeFields(result).equals(request), "root-index request roundtrip drift"); return result;
    }
    public static Request decodeRequestPacket(byte[] packet) throws IOException {
        RegistryJson.require(packet!=null&&packet.length>=5&&packet.length-4<=16384,"Native root-index request requires a bounded16KiB payload");
        var request = NativeWire.decodeExecuteRequest(packet);
        boolean quoted=false;
        for(int i=4;i<packet.length;i++) {
            int value=Byte.toUnsignedInt(packet[i]);
            RegistryJson.require(value<128&&value!='\\',"Native root-index request excludes escapes/non-ASCII");
            if(value=='"')quoted=!quoted;
            if(!quoted&&value=='-'&&i+1<packet.length&&packet[i+1]=='0'
                    &&(i+2==packet.length||packet[i+2]<'0'||packet[i+2]>'9'))
                throw new IllegalArgumentException("Native root-index request excludes negative zero");
        }
        var row = RegistryJson.object(new RawJson(Arrays.copyOfRange(packet, 4, packet.length)));
        RegistryJson.keys(row, Set.of("type", "protocol_version", "request_id", "step", "expected_revision", "arguments", "gui_root_index"));
        RegistryJson.require(request.requestId().matches("[A-Za-z0-9_.-]{1,96}") && request.step().equals(GuiRootIndexFrame.STEP)
                && request.expectedRevision().equals(Optional.of(BigInteger.ZERO)) && request.expectedSnapshotRevision().isEmpty(), "exact root-index request envelope required");
        return decodeFields(new RawJson(request.normalizedAdditionalFields().value()));
    }
    private static Request decodeFields(RawJson additional) {
        var row = RegistryJson.object(additional); RegistryJson.keys(row, Set.of("arguments", "gui_root_index"));
        RegistryJson.keys(RegistryJson.object(row.get("arguments")), Set.of());
        var claim = RegistryJson.object(row.get("gui_root_index"));
        RegistryJson.keys(claim, Set.of("schema", "game_version", "executable_sha256", "adapter_id", "backend", "deadline_unix_ms", "expected_core"));
        var build = GuiRootIndexFrame.BUILD;
        RegistryJson.require(GuiRootIndexFrame.REQUEST_SCHEMA.equals(RegistryJson.text(claim.get("schema")))
                && build.matches(RegistryJson.text(claim.get("game_version")), RegistryJson.text(claim.get("executable_sha256")))
                && build.coreFrameAdapterId().equals(RegistryJson.text(claim.get("adapter_id")))
                && GuiRootIndexFrame.BACKEND.equals(RegistryJson.text(claim.get("backend"))), "root-index request exact source mismatch");
        var core = RegistryJson.object(claim.get("expected_core"));
        RegistryJson.keys(core, Set.of("date_raw", "speed", "paused", "local_player_id", "map_ready", "has_played_character", "played_character_id", "played_character_alive"));
        return new Request(new CoreFrame.Partial(build, new CoreFrame.Prefix(RegistryJson.int32(core.get("date_raw")), RegistryJson.int32(core.get("speed")),
                RegistryJson.bool(core.get("paused")), RegistryJson.int32(core.get("local_player_id")), RegistryJson.bool(core.get("map_ready")),
                RegistryJson.bool(core.get("has_played_character")), RegistryJson.int32(core.get("played_character_id")), RegistryJson.bool(core.get("played_character_alive")))),
                RegistryJson.integer(claim.get("deadline_unix_ms"), BigInteger.ONE, RegistryJson.U64));
    }
    public static GuiRootIndexFrame decodePacket(RawJson original, String expectedRequestId) throws IOException {
        var row = RegistryJson.object(original);
        RegistryJson.keys(row, Set.of("type", "protocol_version", "request_id", "ok", "result"));
        RegistryJson.require("command_result".equals(RegistryJson.text(row.get("type")))
                && RegistryJson.integer(row.get("protocol_version"), BigInteger.ONE, BigInteger.ONE).equals(BigInteger.ONE)
                && Objects.requireNonNull(expectedRequestId).equals(RegistryJson.text(row.get("request_id"))) && RegistryJson.bool(row.get("ok")), "original positive root-index envelope required");
        var decoded = NativeWire.decode(NativeWire.packet(original.bytes()));
        if (!(decoded instanceof NativeWire.CommandResult result) || result.result().presence() != NativeWire.Presence.VALUE)
            throw new IOException("original root-index result token required");
        return GuiRootIndexFrame.decode(new RawJson(result.result().token().orElseThrow().value()));
    }
    public static GuiRootIndexFrame decodeOutcome(NativeActionPort.DispatchOutcome actual) throws IOException {
        Objects.requireNonNull(actual);
        if (!(actual instanceof NativeActionPort.AckReceived ack)) throw new IOException("actual root-index ACK unavailable; original outcome retained, never replayed");
        var outbound = ack.outbound().orElseThrow(() -> new IOException("actual root-index outbound missing"));
        Request request = decodeRequestPacket(outbound.originalPacket());
        var decodedRequest = NativeWire.decodeExecuteRequest(outbound.originalPacket());
        if (!outbound.requestId().equals(ack.requestId()) || !decodedRequest.requestId().equals(ack.requestId())) throw new IOException("root-index original request id drift");
        var decoded = NativeWire.decode(ack.originalPacket());
        if (!(decoded instanceof NativeWire.CommandResult result) || result.nativeOk() != ack.nativeOk()
                || !result.requestId().equals(ack.requestId()) || !Arrays.equals(result.payload().value(), ack.originalFrame().bytes()))
            throw new IOException("root-index original command_result envelope drift");
        if (!ack.nativeOk() || result.result().presence() != NativeWire.Presence.VALUE || ack.originalResultToken().isEmpty()
                || !Arrays.equals(result.result().token().orElseThrow().value(), ack.originalResultToken().orElseThrow().bytes()))
            throw new IOException("root-index original Native result rejected, missing or changed");
        GuiRootIndexFrame frame = decodePacket(new RawJson(result.payload().value()), ack.requestId());
        var custody = ack.custody().orElseThrow(() -> new IOException("root-index actual ACK custody missing")); custody.verify(ack);
        if (frame instanceof GuiRootIndexFrame.Partial p && (!p.coreFrame().equals(request.expectedCore())
                || !p.ownerWitness().connectionGeneration().equals(custody.session().connectionGeneration())))
            throw new IOException("root-index result crossed its actual expected Core or connection");
        return frame;
    }
    public static RawJson encode(GuiRootIndexFrame actual) {
        Objects.requireNonNull(actual); var row = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode(); var build = GuiRootIndexFrame.BUILD;
        row.put("step", GuiRootIndexFrame.STEP).put("schema", GuiRootIndexFrame.SCHEMA).put("game_version", build.version())
                .put("executable_sha256", build.executableSha256().toUpperCase(java.util.Locale.ROOT)).put("adapter_id", build.coreFrameAdapterId()).put("backend", GuiRootIndexFrame.BACKEND);
        row.put("addresses_redacted", true).put("complete_snapshot", false).put("complete_gui_tree", false).put("control_actions_available", false);
        row.set("core_frame", RegistryJson.object(CoreFramePublicCodec.encode(actual.coreFrame())));
        if (actual instanceof GuiRootIndexFrame.Partial p) {
            row.put("status", "partial").put("root_index_available", true).put("application_main_observed", true).put("source_abi_pins_verified", true).putNull("unavailable_reason");
            row.putObject("root_index").put("entry_count", p.rootIndex().entryCount()).put("materialized_root_count", p.rootIndex().materializedRootCount())
                    .put("empty_entry_count", p.rootIndex().emptyEntryCount()).put("all_entries_current_context", true);
            var w = p.ownerWitness(); row.putObject("owner_witness").put("connection_generation", w.connectionGeneration().toString())
                    .put("ticket_sequence", w.ticketSequence().toString()).put("pump_epoch", w.pumpEpoch().toString()).put("thread_id", w.threadId());
        } else {
            var unavailable = (GuiRootIndexFrame.Unavailable) actual;
            row.put("status", "unavailable").put("root_index_available", false).put("application_main_observed", unavailable.coreFrame().applicationMainObserved())
                    .put("source_abi_pins_verified", false).put("unavailable_reason", unavailable.reason()).putNull("root_index").putNull("owner_witness");
        }
        RawJson encoded = RegistryJson.encode(row); RegistryJson.require(GuiRootIndexFrame.decode(encoded).equals(actual), "root-index frame roundtrip drift"); return encoded;
    }
}
