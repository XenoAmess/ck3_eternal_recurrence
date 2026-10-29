package org.xar.ck3.control.nativebridge.capabilities.aub;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Exact original AUB four-flag observation. A read grants neither selection nor Confirm. */
public final class AubBusinessStateRead {
    public static final String STEP = "query-aub-business-state-v1";
    public static final String CAPABILITY = "game.command.query-aub-business-state-v1";
    public static final String CONTRACT_ID = "java.aub.business-state.v1";
    public static final String GAME_VERSION = "1.20.0.3";
    public static final String GAME_SHA256 = "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6";
    private static final BigInteger I32_MAX = BigInteger.valueOf(Integer.MAX_VALUE);
    private static final BigInteger I32_MIN = BigInteger.valueOf(Integer.MIN_VALUE);
    private static final BigInteger U32_MAX = new BigInteger("4294967295");
    static final Set<String> RESULT_FIELDS = Set.of("schema", "step", "read_only", "game_version", "executable_sha256",
            "native_revision", "connection_generation", "game_pid", "played_character_id", "date_raw", "available",
            "owner_thread_verified", "frame_verified", "source_abi_pins_verified", "gui_owner_binding_verified", "stable_two_pass_verified",
            "detail_census_verified", "detail_root_available", "detail_tree_complete", "detail_effectively_visible", "flags", "unavailable_reason",
            "rendered_text_available", "rendered_down_available", "product_acceptance_proven");
    private static final Set<String> FLAG_FIELDS = Set.of("key", "available", "atom_registered", "present", "unavailable_reason");
    private AubBusinessStateRead() { }

    public enum FlagKey {
        ENABLED("enable_auto_build"), TREASURY_ONLY("aub_funding_treasury_only"), PERSONAL_ONLY("aub_funding_personal_only"),
        PAUSE_OVER_DOMAIN_LIMIT("aub_pause_when_over_domain_limit");
        private final String wire;
        FlagKey(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record Flag(FlagKey key, boolean atomRegistered, boolean present) {
        public Flag { Objects.requireNonNull(key); need(!present || atomRegistered, "present flag requires its actual registered atom"); }
    }
    public record DetailCensus(boolean rootAvailable, boolean effectivelyVisible) {
        public DetailCensus { need(rootAvailable || !effectivelyVisible, "absent detail root cannot be visible"); }
    }
    public record State(ObservationIdentity before, BigInteger connectionGeneration, DetailCensus detail,
            List<Flag> flags, RawJson original) {
        public State {
            Objects.requireNonNull(before); Objects.requireNonNull(connectionGeneration); Objects.requireNonNull(detail); Objects.requireNonNull(original);
            need(connectionGeneration.signum() > 0 && connectionGeneration.compareTo(NativeWire.UINT64_MAX) <= 0, "AUB connection generation outside uint64");
            flags = List.copyOf(flags); need(flags.size() == FlagKey.values().length, "complete four-flag census required");
            for (int index = 0; index < flags.size(); index++) need(flags.get(index).key() == FlagKey.values()[index], "native fixed flag order changed");
        }
    }

    /** Root installs this exact object in its catalog and passes the same physical archive/session binding. */
    public static final class Registration {
        private final NativeGameTransport transport;
        private final ActionPorts.OutcomeArchive archive;
        private final ExactRef definition;
        private final ReadContract<State> contract;
        public Registration(NativeGameTransport actualTransport, ActionPorts.OutcomeArchive actualArchive, ExactRef actualNativeDefinition) {
            transport = Objects.requireNonNull(actualTransport); archive = Objects.requireNonNull(actualArchive);
            definition = Objects.requireNonNull(actualNativeDefinition); need(definition.bytes() > 0, "actual native AUB definition source required");
            contract = new ReadContract<>(CONTRACT_ID, new OperationKey(STEP), Optional.of(CAPABILITY), CAPABILITY,
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, definition, (request, requestId) -> prepare(request), this::decode, this::decode);
        }
        public ReadContract<State> contract() { return contract; }
        private NativeRequest prepare(PlanningReadRequest request) {
            return prepareFixed(request, STEP, CAPABILITY);
        }
        NativeRequest prepareFixed(PlanningReadRequest request, String step, String capability) {
            need(request.arguments().members().isEmpty(), "AUB fixed state read has no caller native fields");
            try {
                var witness = SharedSourceFiles.observe(Path.of(definition.path()));
                need(witness.source().bytes() == definition.bytes() && witness.source().sha256().equals(definition.sha256()), "AUB definition source changed");
                var current = transport.latestObservedSnapshot().orElseThrow(() -> new IOException("actual held snapshot unavailable"));
                NativeWire.Hello hello = transport.originalHello();
                need(current.session().sessionId().equals(request.sessionId()) && current.session().game().equals(request.before().game())
                        && current.session().machineId().equals(request.before().machineId()), "AUB read crossed actual transport identity");
                validateFrame(request.before(), current.session().connectionGeneration(),
                        (NativeWire.Snapshot) NativeWire.decode(current.originalPacket()), hello, capability);
                ObjectNode arguments = NativeWire.object(NativeWire.parse(new byte[] {'{', '}'}));
                arguments.put("expected_player_character_id", request.before().frame().identity().player());
                arguments.put("expected_game_pid", request.before().game().pid());
                arguments.put("expected_connection_generation", current.session().connectionGeneration());
                SharedSourceFiles.assertUnchanged(witness);
                return new NativeRequest(step, Optional.of(capability), new RawJson(arguments.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            } catch (IOException failure) { throw new UncheckedIOException("actual AUB fixed read preparation unavailable", failure); }
        }
        private State decode(PlanningReadReceipt receipt) {
            try {
                verifyReadWire(receipt, STEP);
                validateOriginals(receipt.request().before(), receipt.before().binding());
                validateOriginals(receipt.request().before(), receipt.after().binding());
                RawJson original = receipt.original().originalResultToken().orElseThrow(() -> new IllegalArgumentException("actual AUB result token absent"));
                return decodeMaterial(original, receipt.request().before(), receipt.before().binding().connectionGeneration());
            } catch (IOException failure) { throw new UncheckedIOException("original archived AUB frame unavailable", failure); }
        }
        void verifyReadWire(PlanningReadReceipt receipt, String step) throws IOException {
            need(receipt.request().arguments().members().isEmpty() && receipt.request().operation().value().equals(step), "AUB fixed query changed its registered request arguments/operation");
            NativeActionPort.AckReceived ack = receipt.original();
            NativeWire.Frame frame = NativeWire.decode(ack.originalPacket());
            need(frame instanceof NativeWire.CommandResult, "AUB original query ACK packet required");
            NativeWire.CommandResult result = (NativeWire.CommandResult) frame;
            need(result.requestId().equals(receipt.requestId()) && ack.requestId().equals(receipt.requestId()) && result.nativeOk() && ack.nativeOk()
                    && java.util.Arrays.equals(result.payload().value(), ack.originalFrame().bytes()) && result.result().presence() == NativeWire.Presence.VALUE
                    && java.util.Arrays.equals(result.result().token().orElseThrow().value(), ack.originalResultToken().orElseThrow().bytes()), "AUB original query packet/frame/result token differ");
            NativeWire.ExecuteRequest request = NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow(() -> new IllegalArgumentException("AUB actual outgoing query packet absent")).originalPacket());
            need(request.requestId().equals(receipt.requestId()) && request.step().equals(step)
                    && request.expectedRevision().equals(Optional.of(receipt.request().before().frame().identity().nativeRevision()))
                    && receipt.before().binding().connectionGeneration().equals(receipt.after().binding().connectionGeneration()), "AUB original query outgoing identity/revision/generation differs");
            ObjectNode actual = NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));
            ObjectNode wanted = NativeWire.object(NativeWire.parse(new byte[] {'{', '}'}));
            wanted.put("expected_player_character_id", receipt.request().before().frame().identity().player()); wanted.put("expected_game_pid", receipt.request().before().game().pid());
            wanted.put("expected_connection_generation", receipt.before().binding().connectionGeneration());
            need(actual.equals(NativeWire.parse(wanted.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8))), "AUB actual outgoing query semantic stamps differ");
        }
        void validateOriginals(ObservationIdentity before, GuardEvidence guard) throws IOException {
            validateOriginals(before, guard, CAPABILITY);
        }
        void validateOriginals(ObservationIdentity before, GuardEvidence guard, String capability) throws IOException {
            NativeWire.Frame snapshot = NativeWire.decode(original(guard.nativeEvidence()));
            NativeWire.Frame hello = NativeWire.decode(original(guard.capabilityEvidence()));
            need(snapshot instanceof NativeWire.Snapshot && hello instanceof NativeWire.Hello, "AUB guard originals must be snapshot and HELLO");
            validateFrame(before, guard.connectionGeneration(), (NativeWire.Snapshot) snapshot, (NativeWire.Hello) hello, capability);
        }
        private byte[] original(ExactRef ref) throws IOException {
            byte[] actual = archive.readOriginalPacket(ref);
            var identity = NativeRequestChronology.PacketIdentity.of(actual);
            need(identity.bytes() == ref.bytes() && identity.sha256().equals(ref.sha256()), "AUB original archive bytes changed");
            return actual;
        }
    }

    static void validateFrame(ObservationIdentity before, BigInteger generation, NativeWire.Snapshot snapshot, NativeWire.Hello hello) throws IOException {
        validateFrame(before, generation, snapshot, hello, CAPABILITY);
    }
    static void validateFrame(ObservationIdentity before, BigInteger generation, NativeWire.Snapshot snapshot, NativeWire.Hello hello, String capability) throws IOException {
        ObjectNode helloFields = NativeWire.object(NativeWire.parse(java.util.Arrays.copyOfRange(hello.packet().value(), 4, hello.packet().value().length)));
        need(hello.gameSha256().equalsIgnoreCase(GAME_SHA256) && text(helloFields, "expected_ck3_version").equals(GAME_VERSION)
                && hello.buildMatch() && hello.adapterStatus().equals("ready") && hello.pid() == before.game().pid()
                && hello.connectionGeneration().equals(generation) && hello.capabilities().contains(capability), "actual AUB HELLO is not the source-qualified exact .3 capability");
        need(snapshot.snapshotId().equals(before.frame().snapshotId()) && snapshot.revision().equals(before.frame().identity().nativeRevision()), "actual AUB snapshot identity drift");
        ObjectNode state = NativeWire.object(NativeWire.parse(snapshot.state().value()));
        need(bool(state, "paused") && bool(state, "map_ready"), "AUB needs actual paused map");
        need(state.has("active_event") && state.get("active_event").isNull() && state.has("pending_character_interaction")
                && state.get("pending_character_interaction").isNull(), "AUB requires explicit null event and pending interaction");
        ObjectNode player = NativeWire.object(state.get("played_character")); need(bool(player, "alive"), "AUB player must be alive");
        equal(integer(player, "character_id", BigInteger.ONE, I32_MAX), before.frame().identity().player(), "actual AUB player");
        equal(integer(state, "date_raw", I32_MIN, I32_MAX), before.frame().identity().dateRaw(), "actual AUB date");
        need(snapshot.revision().signum() > 0 && snapshot.revision().compareTo(NativeWire.UINT64_MAX) <= 0
                && generation.signum() > 0 && generation.compareTo(NativeWire.UINT64_MAX) <= 0, "AUB native generation/revision outside uint64");
    }
    record Material(AubNativeStamp stamp,DetailCensus detail,List<Flag> flags) {
        Material {Objects.requireNonNull(stamp);Objects.requireNonNull(detail);flags=List.copyOf(flags);}
    }
    static State decodeMaterial(RawJson original, ObservationIdentity before, BigInteger generation) throws IOException {
        Material value=material(original);need(value.stamp().equals(AubNativeStamp.expected(before,generation)),"AUB original native stamps differ from the actual observation");
        return new State(before,generation,value.detail(),value.flags(),original);
    }
    static Material material(RawJson original) throws IOException {
        ObjectNode row = NativeWire.object(NativeWire.parse(original.bytes())); Set<String> allowed = new HashSet<>(RESULT_FIELDS);
        if (row.has("backend_id")) { allowed.add("backend_id"); need(text(row, "backend_id").equals("native-headless"), "AUB backend changed"); }
        exact(row, allowed); need(text(row, "schema").equals("ck3-aub-business-state-v1") && text(row, "step").equals(STEP)
                && bool(row, "read_only") && text(row, "game_version").equals(GAME_VERSION)
                && text(row, "executable_sha256").equalsIgnoreCase(GAME_SHA256) && text(row, "unavailable_reason").isEmpty(), "AUB state unavailable or source changed");
        AubNativeStamp stamp=AubNativeStamp.read(row);
        for (String key : List.of("available", "owner_thread_verified", "frame_verified", "source_abi_pins_verified", "gui_owner_binding_verified",
                "stable_two_pass_verified", "detail_census_verified", "detail_tree_complete")) need(bool(row, key), "AUB proof absent: " + key);
        for (String key : List.of("rendered_text_available", "rendered_down_available", "product_acceptance_proven")) need(!bool(row, key), "AUB flag read cannot grant " + key);
        DetailCensus detail = new DetailCensus(bool(row, "detail_root_available"), bool(row, "detail_effectively_visible"));
        JsonNode rows = row.get("flags"); need(rows != null && rows.isArray() && rows.size() == FlagKey.values().length, "AUB complete four-flag census required");
        List<Flag> flags = new ArrayList<>();
        for (int index = 0; index < FlagKey.values().length; index++) {
            ObjectNode flag = NativeWire.object(rows.get(index)); exact(flag, FLAG_FIELDS); FlagKey key = FlagKey.values()[index];
            need(text(flag, "key").equals(key.wire()) && bool(flag, "available") && text(flag, "unavailable_reason").isEmpty(), "AUB fixed native flag unavailable or reordered");
            flags.add(new Flag(key, bool(flag, "atom_registered"), bool(flag, "present")));
        }
        return new Material(stamp,detail,flags);
    }
    public static RawJson normalizedForPublic(State value) { return AubPublicCodec.business(value); }
    private static void exact(ObjectNode row, Set<String> expected) { Set<String> actual = new HashSet<>(); row.fieldNames().forEachRemaining(actual::add); need(actual.equals(expected), "AUB field contract differs"); }
    private static String text(ObjectNode row, String key) { JsonNode value = row.get(key); need(value != null && value.isTextual(), "AUB text field required: " + key); return value.textValue(); }
    private static boolean bool(ObjectNode row, String key) { JsonNode value = row.get(key); need(value != null && value.isBoolean(), "AUB boolean field required: " + key); return value.booleanValue(); }
    private static BigInteger integer(ObjectNode row, String key, BigInteger minimum, BigInteger maximum) throws IOException { return NativeWire.integer(row.get(key), minimum, maximum); }
    private static void equal(BigInteger actual, BigInteger expected, String key) { need(actual.equals(expected), "AUB native stamp changed: " + key); }
    private static void need(boolean value, String message) { if (!value) throw new IllegalArgumentException(message); }
}
