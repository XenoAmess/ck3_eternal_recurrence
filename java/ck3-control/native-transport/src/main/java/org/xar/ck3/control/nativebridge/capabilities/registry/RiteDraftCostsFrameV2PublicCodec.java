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
public final class RiteDraftCostsFrameV2PublicCodec {
    private RiteDraftCostsFrameV2PublicCodec() { }
    public record Request(CoreFrame.Partial expectedCore, BigInteger deadlineUnixMs, long expectedSourceRiteId) {
        public Request {
            GuiRootIndexFrame.requireExpectedCore(expectedCore); Objects.requireNonNull(deadlineUnixMs); RiteDraftCostsFrameV2.sourceRiteId(expectedSourceRiteId);
            RegistryJson.require(deadlineUnixMs.signum() > 0 && deadlineUnixMs.compareTo(RegistryJson.U64) <= 0, "positive uint64 query deadline required");
        }
    }
    public static Request request(CoreFrame.Partial expected, Instant deadline, long expectedSourceRiteId) {
        return new Request(expected, BigInteger.valueOf(Objects.requireNonNull(deadline).toEpochMilli()),expectedSourceRiteId);
    }
    public static RawJson additionalFields(Request request) {
        Objects.requireNonNull(request); var row = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();
        row.putObject("arguments"); var claim = row.putObject("rite_draft"); var build = RiteDraftCostsFrameV2.BUILD;
        claim.put("schema", RiteDraftCostsFrameV2.REQUEST_SCHEMA).put("game_version", build.version())
                .put("executable_sha256", build.executableSha256().toUpperCase(java.util.Locale.ROOT))
                .put("adapter_id", build.coreFrameAdapterId()).put("backend", RiteDraftCostsFrameV2.BACKEND).put("deadline_unix_ms", request.deadlineUnixMs()).put("expected_source_rite_id",request.expectedSourceRiteId());
        var p = request.expectedCore().prefix(); var core = claim.putObject("expected_core");
        core.put("date_raw", p.dateRaw()).put("speed", p.speed()).put("paused", p.paused()).put("local_player_id", p.localPlayerId())
                .put("map_ready", p.mapReady()).put("has_played_character", p.hasPlayedCharacter()).put("played_character_id", p.playedCharacterId()).put("played_character_alive", p.playedCharacterAlive());
        RawJson result = RegistryJson.encode(row); RegistryJson.require(decodeFields(result).equals(request), "rite-draft-costs request roundtrip drift"); return result;
    }
    public static Request decodeRequestPacket(byte[] packet) throws IOException {
        RegistryJson.require(packet!=null&&packet.length>=5&&packet.length-4<=16384,"Native rite-draft-costs request requires a bounded16KiB payload");
        var request = NativeWire.decodeExecuteRequest(packet);
        boolean quoted=false;
        for(int i=4;i<packet.length;i++) {
            int value=Byte.toUnsignedInt(packet[i]);
            RegistryJson.require(value<128&&value!='\\',"Native rite-draft-costs request excludes escapes/non-ASCII");
            if(value=='"')quoted=!quoted;
            if(!quoted&&value=='-'&&i+1<packet.length&&packet[i+1]=='0'
                    &&(i+2==packet.length||packet[i+2]<'0'||packet[i+2]>'9'))
                throw new IllegalArgumentException("Native rite-draft-costs request excludes negative zero");
        }
        var row = RegistryJson.object(new RawJson(Arrays.copyOfRange(packet, 4, packet.length)));
        RegistryJson.keys(row, Set.of("type", "protocol_version", "request_id", "step", "expected_revision", "arguments", "rite_draft"));
        RegistryJson.require(request.requestId().matches("[A-Za-z0-9_.-]{1,96}") && request.step().equals(RiteDraftCostsFrameV2.STEP)
                && request.expectedRevision().equals(Optional.of(BigInteger.ZERO)) && request.expectedSnapshotRevision().isEmpty(), "exact rite-draft-costs request envelope required");
        return decodeFields(new RawJson(request.normalizedAdditionalFields().value()));
    }
    private static Request decodeFields(RawJson additional) {
        var row = RegistryJson.object(additional); RegistryJson.keys(row, Set.of("arguments", "rite_draft"));
        RegistryJson.keys(RegistryJson.object(row.get("arguments")), Set.of());
        var claim = RegistryJson.object(row.get("rite_draft"));
        RegistryJson.keys(claim, Set.of("schema", "game_version", "executable_sha256", "adapter_id", "backend", "deadline_unix_ms", "expected_core", "expected_source_rite_id"));
        var build = RiteDraftCostsFrameV2.BUILD;
        RegistryJson.require(RiteDraftCostsFrameV2.REQUEST_SCHEMA.equals(RegistryJson.text(claim.get("schema")))
                && build.matches(RegistryJson.text(claim.get("game_version")), RegistryJson.text(claim.get("executable_sha256")))
                && build.coreFrameAdapterId().equals(RegistryJson.text(claim.get("adapter_id")))
                && RiteDraftCostsFrameV2.BACKEND.equals(RegistryJson.text(claim.get("backend"))), "rite-draft-costs request exact source mismatch");
        var core = RegistryJson.object(claim.get("expected_core"));
        RegistryJson.keys(core, Set.of("date_raw", "speed", "paused", "local_player_id", "map_ready", "has_played_character", "played_character_id", "played_character_alive"));
        return new Request(new CoreFrame.Partial(build, new CoreFrame.Prefix(RegistryJson.int32(core.get("date_raw")), RegistryJson.int32(core.get("speed")),
                RegistryJson.bool(core.get("paused")), RegistryJson.int32(core.get("local_player_id")), RegistryJson.bool(core.get("map_ready")),
                RegistryJson.bool(core.get("has_played_character")), RegistryJson.int32(core.get("played_character_id")), RegistryJson.bool(core.get("played_character_alive")))),
                RegistryJson.integer(claim.get("deadline_unix_ms"), BigInteger.ONE, RegistryJson.U64), RegistryJson.integer(claim.get("expected_source_rite_id"),BigInteger.ZERO,BigInteger.valueOf(0xffff_fffeL)).longValueExact());
    }
    public static RiteDraftCostsFrameV2 decodePacket(RawJson original, String expectedRequestId) throws IOException {
        var row = RegistryJson.object(original);
        RegistryJson.keys(row, Set.of("type", "protocol_version", "request_id", "ok", "result"));
        RegistryJson.require("command_result".equals(RegistryJson.text(row.get("type")))
                && RegistryJson.integer(row.get("protocol_version"), BigInteger.ONE, BigInteger.ONE).equals(BigInteger.ONE)
                && Objects.requireNonNull(expectedRequestId).equals(RegistryJson.text(row.get("request_id"))) && RegistryJson.bool(row.get("ok")), "original positive rite-draft-costs envelope required");
        var decoded = NativeWire.decode(NativeWire.packet(original.bytes()));
        if (!(decoded instanceof NativeWire.CommandResult result) || result.result().presence() != NativeWire.Presence.VALUE)
            throw new IOException("original rite-draft-costs result token required");
        return RiteDraftCostsFrameV2.decode(new RawJson(result.result().token().orElseThrow().value()));
    }
    public static RiteDraftCostsFrameV2 decodeOutcome(NativeActionPort.DispatchOutcome actual) throws IOException {
        Objects.requireNonNull(actual);
        if (!(actual instanceof NativeActionPort.AckReceived ack)) throw new IOException("actual rite-draft-costs ACK unavailable; original outcome retained, never replayed");
        var outbound = ack.outbound().orElseThrow(() -> new IOException("actual rite-draft-costs outbound missing"));
        Request request = decodeRequestPacket(outbound.originalPacket());
        var decodedRequest = NativeWire.decodeExecuteRequest(outbound.originalPacket());
        if (!outbound.requestId().equals(ack.requestId()) || !decodedRequest.requestId().equals(ack.requestId())) throw new IOException("rite-draft-costs original request id drift");
        var decoded = NativeWire.decode(ack.originalPacket());
        if (!(decoded instanceof NativeWire.CommandResult result) || result.nativeOk() != ack.nativeOk()
                || !result.requestId().equals(ack.requestId()) || !Arrays.equals(result.payload().value(), ack.originalFrame().bytes()))
            throw new IOException("rite-draft-costs original command_result envelope drift");
        if (!ack.nativeOk() || result.result().presence() != NativeWire.Presence.VALUE || ack.originalResultToken().isEmpty()
                || !Arrays.equals(result.result().token().orElseThrow().value(), ack.originalResultToken().orElseThrow().bytes()))
            throw new IOException("rite-draft-costs original Native result rejected, missing or changed");
        RiteDraftCostsFrameV2 frame = decodePacket(new RawJson(result.payload().value()), ack.requestId());
        var custody = ack.custody().orElseThrow(() -> new IOException("rite-draft-costs actual ACK custody missing")); custody.verify(ack);
        if (frame instanceof RiteDraftCostsFrameV2.Partial p && (!p.coreFrame().equals(request.expectedCore()) || p.draft().sourceRiteId()!=request.expectedSourceRiteId()
                || !p.ownerWitness().connectionGeneration().equals(custody.session().connectionGeneration())))
            throw new IOException("rite-draft-costs result crossed its actual expected Core or connection");
        return frame;
    }
    public static RawJson encode(RiteDraftCostsFrameV2 actual) {
        Objects.requireNonNull(actual);var row=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();var build=RiteDraftCostsFrameV2.BUILD;
        row.put("step",RiteDraftCostsFrameV2.STEP).put("schema",RiteDraftCostsFrameV2.SCHEMA).put("game_version",build.version())
                .put("executable_sha256",build.executableSha256().toUpperCase(java.util.Locale.ROOT)).put("adapter_id",build.coreFrameAdapterId()).put("backend",RiteDraftCostsFrameV2.BACKEND);
        row.put("addresses_redacted",true).put("complete_snapshot",false).put("complete_gui_tree",false).put("control_actions_available",false).put("observer_guard_evaluated",false).put("physical_save_confirmed",false);
        row.set("core_frame",RegistryJson.object(CoreFramePublicCodec.encode(actual.coreFrame())));
        if(actual instanceof RiteDraftCostsFrameV2.Partial p) {
            row.put("status","partial").put("draft_available",true).put("application_main_observed",true).put("source_abi_pins_verified",true).put("full_native_can_edit_evaluated",true).putNull("unavailable_reason");
            var d=p.draft();row.putObject("draft").put("source_rite_id",d.sourceRiteId()).put("played_character_id",d.playedCharacterId()).put("window_name",RiteDraftCostsFrameV2.WINDOW_NAME)
                    .put("can_edit_rite_native",d.canEditRiteNative()).put("piety_cost_raw",Long.toString(d.pietyCostRaw())).put("piety_missing_signed_raw",Long.toString(d.pietyMissingSignedRaw())).put("raw_scale",100000).put("has_enough_piety",d.hasEnoughPiety());
            var w=p.ownerWitness();row.putObject("owner_witness").put("connection_generation",w.connectionGeneration().toString()).put("ticket_sequence",w.ticketSequence().toString()).put("pump_epoch",w.pumpEpoch().toString()).put("thread_id",w.threadId());
        }else {
            var u=(RiteDraftCostsFrameV2.Unavailable)actual;row.put("status","unavailable").put("draft_available",false).put("application_main_observed",u.coreFrame().applicationMainObserved())
                    .put("source_abi_pins_verified",false).put("full_native_can_edit_evaluated",false).putNull("draft").putNull("owner_witness").put("unavailable_reason",u.reason());
        }
        var raw=RegistryJson.encode(row);RegistryJson.require(RiteDraftCostsFrameV2.decode(raw).equals(actual),"draft-cost response roundtrip drift");return raw;
    }
}
