package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.china_career.CareerJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.*;
import org.xar.ck3.control.service.mcp.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.ChinaCareerContract.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Actual original MCP adapter/service/native primitive/normalizers -> typed producers -> real public binding.
 * Enclosing protocol facts are software DATA, never an actual managed Root or Native qualification. */
final class RootChinaCareerPublicProductsTest {
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    private static final ExactRef REF = new ExactRef("software-data-not-Root-qualification", 1, "a".repeat(64));

    @Test void actualOriginalProducersAllSixDescriptorConsumersAndCurrentUnsupportedBranches() throws Exception {
        List<ToolDescriptor> originalTools = RootOriginalPublicTestInputs.tools();
        JsonNode oracle = oracle();
        assertTrue(oracle.get("whole_original_tests").intValue() >= 8);
        assertEquals(0, oracle.get("whole_original_skipped").intValue());
        assertTrue(oracle.get("rows").size() >= 15);
        var registration = new ChinaCareerService.Registration(REF);
        var service = new ChinaCareerService(registration);
        for (JsonNode row : oracle.get("rows")) {
            Kind kind = kind(row.get("kind").textValue());
            Frame frame = frame(row.get("frame"), row.get("service"), true, BigInteger.valueOf(7));
            Request input = input(kind, row.get("frame"), frame.publicRevision());
            var context = planning(input, frame);
            AtomicInteger calls = new AtomicInteger();
            RootChinaCareerPublicProducts.QueryPort producer = request -> {
                Response result = service.query(request, frame, context, (contract, actual) -> {
                    calls.incrementAndGet();
                    return read(contract, actual, row.get("frame"), frame, row.get("request_fields"));
                });
                return ChinaCareerCodec.encodeResponse(result);
            };
            var binding = RootChinaCareerPublicProducts.bindings(producer, REF).stream()
                    .filter(value -> value.name().equals(kind.publicName())).findFirst().orElseThrow();
            ToolDescriptor descriptor = RootPublicCatalogCodec.executableTool(originalTools.stream()
                    .filter(value -> value.name().equals(kind.publicName())).findFirst().orElseThrow(
                            () -> new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: " + kind.publicName())));
            // Original SDK safe integer input, plus the sole typed canonical-string roundtrip.
            ObjectNode originalArguments = ChinaCareerCodec.object(ChinaCareerCodec.encodeRequest(input));
            originalArguments.put("expected_revision", frame.publicRevision());
            RawJson arguments = raw(originalArguments);
            CallResult actual = invoke(binding, descriptor, arguments);
            JsonNode produced = NativeWire.parse(actual.bytes()).get("structuredContent");
            JsonNode expected = publicProjection(row.get("service"));
            assertEquals(expected, produced, kind.name());
            assertEquals(1, calls.get());
            assertEquals(input, ChinaCareerCodec.decodeRequest(kind, ChinaCareerCodec.encodeRequest(input)));
            assertEquals(row.get("request_fields"), ChinaCareerCodec.object(ChinaCareerCodec.nativeFields(input, frame)));
            assertEquals(row.get("step").textValue(), kind.step());
            var observed = ChinaCareerCodec.nativeObservation(kind, raw((ObjectNode) row.get("frame")), frame.binding(input), BigInteger.ONE, "native-headless");
            assertEquals(row.get("frame"), ChinaCareerCodec.object(observed.originalFrame()), "native original retained unchanged");
            assertArrayEquals(ChinaCareerCodec.encodeResponse(ChinaCareerCodec.response(input, frame, observed)).bytes(),
                    ChinaCareerCodec.response(input, frame, observed).publicJson().bytes());
            for (String field : List.of("schema_version", "snapshot_revision")) {
                ObjectNode bad = ((ObjectNode) row.get("frame")).deepCopy().put(field, true);
                assertThrows(IllegalArgumentException.class, () -> ChinaCareerCodec.decodeDomain(kind, raw(bad), frame.binding(input)));
            }
            ObjectNode missing = ((ObjectNode) row.get("frame")).deepCopy(); missing.remove("paused");
            assertThrows(IllegalArgumentException.class, () -> ChinaCareerCodec.decodeDomain(kind, raw(missing), frame.binding(input)));
            ObjectNode extra = ((ObjectNode) row.get("frame")).deepCopy().put("unregistered_field", 1);
            assertThrows(IllegalArgumentException.class, () -> ChinaCareerCodec.decodeDomain(kind, raw(extra), frame.binding(input)));
        }
        assertEquals(30, oracle.get("faults").size());
        for (JsonNode row : oracle.get("faults")) {
            Kind kind = kind(row.get("kind").textValue());
            Request request = input(kind, row.get("frame"), row.get("public_revision").bigIntegerValue());
            request = new Request(kind, row.get("nonce").textValue(), request.expectedRevision(), request.ownerCharacterId(), request.subjectCharacterId());
            final Request currentRequest = request;
            Frame source = frame(row.get("frame"), null, row.get("paused").booleanValue(), row.get("current_revision").bigIntegerValue());
            byte[] originalHello = source.originalHello().packet().value();
            ObjectNode absentFields = (ObjectNode) NativeWire.parse(Arrays.copyOfRange(originalHello, 4, originalHello.length));
            absentFields.putArray("capabilities");
            byte[] absentPacket = NativeWire.packet(StrictJson.canonical(absentFields));
            NativeWire.Hello absent = (NativeWire.Hello) NativeWire.decode(absentPacket);
            var absentIdentity = NativeRequestChronology.PacketIdentity.of(absentPacket);
            Frame unsupported = new Frame(source.snapshotId(), source.publicRevision(), source.nativeRevision(), source.generation(),
                    source.dateRaw(), source.playerId(), source.paused(), source.mapReady(), source.episode(), absent,
                    new ExactRef("software-DATA/unsupported-hello.packet", absentIdentity.bytes(), absentIdentity.sha256()));
            Failure fault = assertThrows(Failure.class, () -> {
                ChinaCareerService.precheck(currentRequest, unsupported);
                ChinaCareerService.capability(currentRequest, unsupported);
            });
            assertEquals(row.get("python_error").textValue(), fault.fault().pythonName(), kind.name());
            assertEquals(row.get("message").textValue(), fault.getMessage(), kind.name());
            assertEquals(fault.fault(), ChinaCareerCodec.decodeFault(ChinaCareerCodec.encodeFault(fault.fault())));
            assertEquals(0, row.get("query_calls").intValue());
        }
    }

    @Test void exactRequestsRejectMissingNullExtraBooleanFloatAndUnsafeNumericU64() throws Exception {
        for (Kind kind : Kind.values()) {
            ObjectNode valid = StrictJson.object().put("request_nonce", "proof:1").put("expected_revision", 0);
            if (kind.ownerArgument()) valid.put("owner_character_id", 1);
            if (kind.subjectArgument()) valid.put("subject_character_id", 2);
            assertEquals(BigInteger.ZERO, ChinaCareerCodec.decodeRequest(kind, raw(valid)).expectedRevision());
            var maximum = valid.deepCopy().put("expected_revision", PublicUnsigned64.MAXIMUM.toString());
            assertEquals(PublicUnsigned64.MAXIMUM, ChinaCareerCodec.decodeRequest(kind, raw(maximum)).expectedRevision());
            assertThrows(IllegalArgumentException.class, () -> ChinaCareerCodec.decodeRequest(kind,
                    raw(valid.deepCopy().put("expected_revision", PublicUnsigned64.MAXIMUM))));
            for (String field : List.of("request_nonce", "expected_revision")) {
                ObjectNode missing = valid.deepCopy(); missing.remove(field);
                assertThrows(IllegalArgumentException.class, () -> ChinaCareerCodec.decodeRequest(kind, raw(missing)));
                ObjectNode nil = valid.deepCopy().putNull(field);
                assertThrows(IllegalArgumentException.class, () -> ChinaCareerCodec.decodeRequest(kind, raw(nil)));
            }
            assertThrows(IllegalArgumentException.class, () -> ChinaCareerCodec.decodeRequest(kind, raw(valid.deepCopy().put("expected_revision", true))));
            byte[] floating = new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(valid.deepCopy().put("expected_revision", 0.0));
            assertThrows(IllegalArgumentException.class, () -> ChinaCareerCodec.decodeRequest(kind, new RawJson(floating)));
            assertThrows(IllegalArgumentException.class, () -> ChinaCareerCodec.decodeRequest(kind, raw(valid.deepCopy().put("expected_revision", "00"))));
            assertThrows(IllegalArgumentException.class, () -> ChinaCareerCodec.decodeRequest(kind, raw(valid.deepCopy().put("unregistered", 1))));
            for (String field : List.of("owner_character_id", "subject_character_id")) if (valid.has(field)) {
                ObjectNode missing = valid.deepCopy(); missing.remove(field);
                assertThrows(IllegalArgumentException.class, () -> ChinaCareerCodec.decodeRequest(kind, raw(missing)));
                assertThrows(IllegalArgumentException.class, () -> ChinaCareerCodec.decodeRequest(kind, raw(valid.deepCopy().putNull(field))));
                assertThrows(IllegalArgumentException.class, () -> ChinaCareerCodec.decodeRequest(kind, raw(valid.deepCopy().put(field, true))));
                assertThrows(IllegalArgumentException.class, () -> ChinaCareerCodec.decodeRequest(kind, raw(valid.deepCopy().put(field, "1"))));
                assertThrows(IllegalArgumentException.class, () -> ChinaCareerCodec.decodeRequest(kind, raw(valid.deepCopy().put(field, 2147483648L))));
                byte[] decimal = new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(valid.deepCopy().put(field, 1.0));
                assertThrows(IllegalArgumentException.class, () -> ChinaCareerCodec.decodeRequest(kind, new RawJson(decimal)));
            }
        }
        assertEquals(6, new ChinaCareerService.Registration(REF).all().size());
    }

    private static <Q,R> CallResult invoke(McpExecutableDirectory.DirectBinding<Q,R> binding, ToolDescriptor descriptor, RawJson input) throws Exception {
        var call = new ToolCall(binding.name(), new Arguments(Presence.VALUE, Optional.of(input)), Optional.empty(), new McpCancellation());
        descriptor.validateArguments(call.arguments());
        Q request = binding.decoder().decode(call);
        R result = binding.actual().invoke(request);
        CallResult encoded = binding.encoder().encode(result);
        descriptor.validateResult(encoded);
        return encoded;
    }
    private static Kind kind(String name) {
        return switch (name) {
            case "owner" -> Kind.OWNER; case "career" -> Kind.CAREER_HC; case "normal" -> Kind.NORMAL_EXIT;
            case "collective" -> Kind.COLLECTIVE; case "governance" -> Kind.MANAGER_GOVERNANCE; case "selector" -> Kind.MANAGER_SELECTOR;
            default -> throw new IllegalArgumentException("unknown original kind");
        };
    }
    private static Request input(Kind kind, JsonNode nativeFrame, BigInteger revision) {
        return new Request(kind, nativeFrame.get("request_nonce").textValue(), revision,
                kind.ownerArgument() ? OptionalInt.of(nativeFrame.get("requested_owner_character_id").intValue()) : OptionalInt.empty(),
                kind.subjectArgument() ? OptionalInt.of(nativeFrame.get("subject_character_id").intValue()) : OptionalInt.empty());
    }
    private static Frame frame(JsonNode nativeFrame, JsonNode response, boolean paused, BigInteger defaultRevision) throws Exception {
        BigInteger revision = response == null ? defaultRevision : response.get("binding").get("revision").bigIntegerValue();
        ObjectNode hello = StrictJson.object().put("type", "hello").put("protocol_version", 1).put("pid", 123).put("connection_generation", 4)
                .put("bridge_version", CareerJson.BRIDGE).put("expected_ck3_sha256", CareerJson.EXE_SHA256)
                .put("game_adapter_id", CareerJson.ADAPTER).put("game_adapter_status", "ready").put("ck3_build_match", true);
        for (Kind kind : Kind.values()) hello.withArray("capabilities").add(kind.capability());
        byte[] packet = NativeWire.packet(StrictJson.canonical(hello));
        var identity = NativeRequestChronology.PacketIdentity.of(packet);
        return new Frame("original-oracle-frame", revision, nativeFrame.get("snapshot_revision").bigIntegerValue(), BigInteger.valueOf(4),
                nativeFrame.get("date_raw").intValue(), nativeFrame.get("player_character_id").intValue(), paused, true, "original-oracle-episode",
                (NativeWire.Hello) NativeWire.decode(packet), new ExactRef("software-DATA/original-hello.packet", identity.bytes(), identity.sha256()));
    }
    private static PlanningReadRequest planning(Request input, Frame frame) {
        var source = new G2Source("software-China-career-DATA", NOW.toString(), CareerJson.VERSION, REF);
        var before = new ObservationIdentity(source.machineId(), new GameGeneration(123,
                new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(frame.playerId()), frame.nativeRevision(),
                        BigInteger.valueOf(frame.dateRaw())), frame.snapshotId(), frame.publicRevision(), frame.episode()), 1);
        return new PlanningReadRequest(before, source, "software-only-session", new OperationKey(input.kind().step()),
                ChinaCareerService.arguments(input, frame), NOW.plusSeconds(30));
    }
    private static PlanningReadResult.Known<NativeObservation> read(ReadContract<NativeObservation> contract,
            PlanningReadRequest request, JsonNode originalFrame, Frame frame, JsonNode originalFields) {
        try {
            String id = "actual-original-software-query";
            NativeRequest actual = contract.prepare(request, id);
            assertEquals(originalFields, ChinaCareerCodec.object(actual.additionalFields()));
            byte[] outbound = NativeWire.execute(id, actual.step(), frame.nativeRevision(), actual.additionalFields().bytes());
            ObjectNode result = StrictJson.object().put("step", actual.step()).put("accepted", true).put("status", originalFrame.get("status").textValue())
                    .put("query_sequence", 1).put("snapshot_revision", frame.nativeRevision()).put("backend_id", "native-headless");
            Kind kind = Arrays.stream(Kind.values()).filter(value -> value.step().equals(actual.step())).findFirst().orElseThrow();
            result.set(kind.payload(), originalFrame.deepCopy());
            ObjectNode wire = StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", id).put("ok", true);
            wire.set("result", result); byte[] bytes = StrictJson.canonical(wire, StrictJson.EXPLICIT_MAX_BYTES);
            var evidence = new GuardEvidence(request.before(), request.source(), request.sessionId(), frame.generation(), request.operation(),
                    REF, frame.helloOriginal(), "software-protocol-DATA-not-qualification", NOW, NOW.plusSeconds(30));
            var guard = new PlanningReadGuard(evidence, true, true, true, "b".repeat(64));
            var ack = new NativeActionPort.AckReceived(id, true, Optional.of(raw(result)), new RawJson(bytes), NativeWire.packet(bytes),
                    Optional.of(new NativeActionPort.OutboundPacket(id, outbound)));
            var receipt = new PlanningReadReceipt(request, contract.contractId(), id, guard, guard, ack);
            NativeObservation decoded = contract.decode(receipt);
            assertEquals(decoded, contract.replay(receipt), "original read pure replay consumer changed typed native facts");
            assertEquals(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, contract.guardMode());
            assertTrue(contract.hasPureReplay());
            return new PlanningReadResult.Known<>(decoded, receipt, REF);
        } catch (IOException failure) { throw new UncheckedIOException(failure); }
    }
    private static JsonNode publicProjection(JsonNode original) {
        ObjectNode row = ((ObjectNode) original).deepCopy();
        if (row.has("snapshot_revision")) row.put("snapshot_revision", row.get("snapshot_revision").bigIntegerValue().toString());
        if (row.has("query_sequence")) row.put("query_sequence", row.get("query_sequence").bigIntegerValue().toString());
        for (String name : List.of("source", "bridge_source", "binding")) if (row.get(name) instanceof ObjectNode group) {
            for (String field : List.of("revision", "native_revision", "connection_generation", "expected_revision"))
                if (group.has(field)) group.put(field, group.get(field).bigIntegerValue().toString());
        }
        return row;
    }
    private static RawJson raw(ObjectNode value) { return new RawJson(StrictJson.canonical(value, StrictJson.EXPLICIT_MAX_BYTES)); }
    private static JsonNode oracle() throws Exception {
        Path python = Path.of(required("xar.python")).toRealPath(), repository = Path.of(required("xar.repository.root")).toRealPath();
        var process = new ProcessBuilder(python.toString(), "-I", "-B", "-X", "utf8", "-c", ORACLE, repository.toString(), INDEX)
                .directory(repository.toFile()).start();
        byte[] output;
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = executor.submit(() -> bounded(process.getInputStream(), 4 * 1024 * 1024));
            var stderr = executor.submit(() -> bounded(process.getErrorStream(), 1024 * 1024));
            try {
                process.getOutputStream().close();
                if (!process.waitFor(60, TimeUnit.SECONDS)) throw new IOException("actual China career producer oracle timeout");
                output = stdout.get(10, TimeUnit.SECONDS);
                assertEquals(0, process.exitValue(), new String(stderr.get(10, TimeUnit.SECONDS), StandardCharsets.UTF_8));
            } finally {
                if (process.isAlive()) { process.destroyForcibly(); assertTrue(process.waitFor(10, TimeUnit.SECONDS)); }
            }
        }
        return NativeWire.parse(output);
    }
    private static String required(String property) {
        String value = System.getProperty(property);
        if (value == null || value.isBlank()) throw new IllegalStateException(property + " required; actual original producer NOT_RUN, no skip/fallback");
        return value;
    }
    private static byte[] bounded(InputStream input, int maximum) throws IOException {
        try (input; var output = new ByteArrayOutputStream()) {
            byte[] bytes = new byte[4096]; int count;
            while ((count = input.read(bytes)) != -1) { if (output.size() + count > maximum) throw new IOException("bounded oracle output exceeded"); output.write(bytes, 0, count); }
            return output.toByteArray();
        }
    }
    private static final String INDEX = """
{"repository_root":".","oracle_sources":[{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_workforce_owner_snapshot_contract.py","bytes":7926,"sha256":"2678b31a11e25db5cb1aa59c948f8a7efb74b6c067770dd5308fbd916cc7bb78"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_career_hc_workforce_postcondition_contract.py","bytes":14671,"sha256":"398210553c74fdefa800b77f1287570598e4c2c4c73be35f243bec889bc14c76"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_workforce_collective_snapshot_contract.py","bytes":31932,"sha256":"e91ac95ec075959610060db0b5335201b5d0d952da931a2495aa1ba4ce7faa31"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_workforce_normal_exit_snapshot_contract.py","bytes":36181,"sha256":"60261c642d5500f2e465986e64cd43389e5bfeff6cecfa8ca91d2da8abb08eb3"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_manager_subordinate_selector_contract.py","bytes":8166,"sha256":"26e5e2ce6ddc13c496ac497c476de3ebf935788b386ae6fdf5a58c049332a7b7"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_manager_governance_snapshot_contract.py","bytes":33526,"sha256":"c7f07a53c4752cc11e859e47176124e092a791b8d87880ee3882ac88f31e767a"},{"path":"ck3_autonomous_player/tests/unit/test_zhongguo_career_hc_workforce_postcondition_v1_contract.py","bytes":13034,"sha256":"2e8a7e40b2396433bdefe0e0112a193a6819808008fff8fc4d5d2e3d254d448d"},{"path":"ck3_autonomous_player/tests/unit/test_zhongguo_workforce_collective_snapshot_v1_contract.py","bytes":16814,"sha256":"46a9e66c4cbb11e92e8d1f31b54f3c65dd954b214281419c2aca87606570fd38"},{"path":"ck3_autonomous_player/tests/unit/test_zhongguo_workforce_normal_exit_snapshot_contract.py","bytes":29212,"sha256":"95787785286752ba5fca2ce2a725b77f2f52fd14b6c2388d370ecdbe9afcd56d"},{"path":"ck3_autonomous_player/tests/unit/test_zhongguo_manager_subordinate_selector_contract.py","bytes":14358,"sha256":"c2feb72f22a683d869d111eb3d684d342476bfa5dab163e903d170bc140d4aba"},{"path":"ck3_autonomous_player/tests/unit/test_zhongguo_manager_governance_snapshot_contract.py","bytes":27889,"sha256":"1c9cdd6dc5b3644e27cc039dd8a6058a04462f0e09471ea828d716721c5698e9"},{"path":"ck3_autonomous_player/tests/fixtures/zhongguo_workforce_owner_snapshot_v1.json","bytes":24976,"sha256":"1b733ce9f6bce9c15e730e8fe31c98b87ea6bec8f1de20737b804c7bff12c12c"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/service.py","bytes":897392,"sha256":"a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py","bytes":1658471,"sha256":"eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py","bytes":283568,"sha256":"b7569231226484b0bdd98c40ace14a82672b2138a0aab77711e559a4d9b8ccbc"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py","bytes":20803,"sha256":"eed449063debf1a84216a350f0178d64a9a6602bbfcc266298a810a9bb736fb6"},{"path":"ck3_autonomous_player/tests/unit/test_zhongguo_workforce_collective_snapshot_v1_bridge.py","bytes":16879,"sha256":"5a6fb0a79b9d9e9898a1a4adcdf1426d514dc157a76135c7cf8124b7f7785c7c"},{"path":"ck3_autonomous_player/tests/unit/test_zhongguo_workforce_normal_exit_snapshot_v1_bridge.py","bytes":16773,"sha256":"cb7afea0eca5ced8ee2a6c4da3e902027a067326b4a2e88241e204105d8ba0aa"},{"path":"ck3_autonomous_player/tests/unit/test_zhongguo_workforce_owner_snapshot_v1_bridge.py","bytes":9986,"sha256":"e98b63b1a5ae476f31eb47a45f02f86ecc1c1f78b0a89568f45fdd8492c5922c"}],"methods":[{"kind":"owner","public_method":"query_zhongguo_workforce_owner_snapshot_v1","driver_method":"_execute_zhongguo_workforce_owner_snapshot_v1_query","parse_query":"parse_query_zhongguo_workforce_owner_snapshot_v1_step","contract_module":"zhongguo_workforce_owner_snapshot_contract","fixture_file":null,"step":"query-zhongguo-workforce-owner-snapshot-v1","capability":"game.command.query-zhongguo-workforce-owner-snapshot-v1","payload":"zhongguo_workforce_owner_snapshot","response":"OwnerCareerFrames.Owner","service_range":[11174,11348],"driver_range":[19790,19930]},{"kind":"career","public_method":"query_zhongguo_career_hc_workforce_postcondition_v1","driver_method":"_execute_zhongguo_career_hc_workforce_v1_query","parse_query":"parse_query_zhongguo_career_hc_workforce_v1_step","contract_module":"zhongguo_career_hc_workforce_postcondition_contract","fixture_file":"test_zhongguo_career_hc_workforce_postcondition_v1_contract.py","step":"query-zhongguo-career-hc-workforce-postcondition-v1","capability":"game.command.query-zhongguo-career-hc-workforce-postcondition-v1","payload":"zhongguo_career_hc_workforce_postcondition","response":"OwnerCareerFrames.Career","service_range":[11555,11736],"driver_range":[20077,20217]},{"kind":"collective","public_method":"query_zhongguo_workforce_collective_snapshot_v1","driver_method":"_execute_zhongguo_workforce_collective_snapshot_v1_query","parse_query":"parse_query_zhongguo_workforce_collective_snapshot_v1_step","contract_module":"zhongguo_workforce_collective_snapshot_contract","fixture_file":"test_zhongguo_workforce_collective_snapshot_v1_contract.py","step":"query-zhongguo-workforce-collective-snapshot-v1","capability":"game.command.query-zhongguo-workforce-collective-snapshot-v1","payload":"zhongguo_workforce_collective_snapshot","response":"CollectiveWorkforceFrame","service_range":[11740,12029],"driver_range":[20223,20382]},{"kind":"normal","public_method":"query_zhongguo_workforce_normal_exit_snapshot_v1","driver_method":"_execute_zhongguo_workforce_normal_exit_snapshot_v1_query","parse_query":"parse_query_zhongguo_workforce_normal_exit_snapshot_v1_step","contract_module":"zhongguo_workforce_normal_exit_snapshot_contract","fixture_file":"test_zhongguo_workforce_normal_exit_snapshot_contract.py","step":"query-zhongguo-workforce-normal-exit-snapshot-v1","capability":"game.command.query-zhongguo-workforce-normal-exit-snapshot-v1","payload":"zhongguo_workforce_normal_exit_snapshot","response":"NormalExitWorkforceFrame","service_range":[12031,12318],"driver_range":[20384,20543]},{"kind":"selector","public_method":"query_zhongguo_manager_subordinate_selector_v1","driver_method":"_execute_zhongguo_manager_subordinate_selector_v1_query","parse_query":"parse_query_zhongguo_manager_subordinate_selector_v1_step","contract_module":"zhongguo_manager_subordinate_selector_contract","fixture_file":"test_zhongguo_manager_subordinate_selector_contract.py","step":"query-zhongguo-manager-subordinate-selector-v1","capability":"game.command.query-zhongguo-manager-subordinate-selector-v1","payload":"zhongguo_manager_subordinate_selector","response":"ManagerSelectorFrame","service_range":[12609,12738],"driver_range":[20852,20987]},{"kind":"governance","public_method":"query_zhongguo_manager_governance_snapshot_v1","driver_method":"_execute_zhongguo_manager_governance_snapshot_v1_query","parse_query":"parse_query_zhongguo_manager_governance_snapshot_v1_step","contract_module":"zhongguo_manager_governance_snapshot_contract","fixture_file":"test_zhongguo_manager_governance_snapshot_contract.py","step":"query-zhongguo-manager-governance-snapshot-v1","capability":"game.command.query-zhongguo-manager-governance-snapshot-v1","payload":"zhongguo_manager_governance_snapshot","response":"ManagerGovernanceFrame","service_range":[12740,13033],"driver_range":[20691,20850]}]}
""";
    private static final String ORACLE = """
from __future__ import annotations
import ast,copy,hashlib,importlib,importlib.util,json,sys,types,unittest,contextlib
from pathlib import Path
repo=Path(sys.argv[1]).resolve()
manifest=json.loads(sys.argv[2])
manifest['repository_root']=str(repo)
for ref in manifest['oracle_sources']:ref['path']=str(repo/ref['path'])
for ref in manifest['oracle_sources']:
 p=Path(ref['path'])
 if p.stat().st_size!=ref['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=ref['sha256']:
  raise RuntimeError('pinned original producer changed: '+str(p))
base=Path(manifest['repository_root'])/'ck3_autonomous_player'
sys.path.insert(0,str(base/'src'))
def compiled(path,names):
 t=ast.parse(path.read_text(encoding='utf-8-sig'))
 found=[]
 for node in ast.walk(t):
  if isinstance(node,ast.FunctionDef) and node.name in names:
   node.decorator_list=[]; found.append(node)
 if set(n.name for n in found)!=set(names):raise RuntimeError('actual original body missing')
 return compile(ast.fix_missing_locations(ast.Module(body=ast.parse('from __future__ import annotations').body+found,type_ignores=[])),str(path),'exec')
def fixture(path,contract):
 env=dict(vars(contract),copy=copy,json=json,Path=Path,sys=sys,__file__=str(path))
 nodes=[]
 for node in ast.parse(path.read_text(encoding='utf-8-sig')).body:
  if isinstance(node,ast.ClassDef):break
  if isinstance(node,(ast.Assign,ast.AnnAssign,ast.FunctionDef)):nodes.append(node)
 exec(compile(ast.fix_missing_locations(ast.Module(body=ast.parse('from __future__ import annotations').body+nodes,type_ignores=[])),str(path),'exec'),env)
 return env
from xar_autoplayer.bridge.driver import BridgeUnavailableError,UnsupportedStepError
fault_rows=[]
rows=[]
for method in manifest['methods']:
 kind=method['kind']
 contract=importlib.import_module('xar_autoplayer.bridge.'+method['contract_module'])
 env=dict(vars(contract),BridgeUnavailableError=BridgeUnavailableError,UnsupportedStepError=UnsupportedStepError)
 driver_path=base/'src/xar_autoplayer/bridge/native_driver.py'
 service_path=base/'src/xar_autoplayer/bridge/service.py'
 exec(compiled(driver_path,[method['driver_method'],'_date_raw','_same_paused_native_frame']),env)
 exec(compiled(service_path,[method['public_method']]),env)
 mcp_path=base/'src/xar_autoplayer/bridge/mcp_server.py'
 helper='_ck3_'+method['public_method']
 exec(compiled(mcp_path,[helper]),env)
 for key,path in ((method['public_method'],service_path),(method['driver_method'],driver_path),(helper,mcp_path)):
  if Path(env[key].__code__.co_filename).resolve()!=path.resolve():raise RuntimeError('actual source producer substitution')
 if kind=='owner':
  fixtures=list(json.loads((base/'tests/fixtures/zhongguo_workforce_owner_snapshot_v1.json').read_text(encoding='utf-8-sig'))['frames'].values())
  constants={}
 else:
  constants=fixture(base/'tests/unit'/method['fixture_file'],contract)
  if kind=='career':fixtures=[constants['frame']()]
  elif kind=='collective':fixtures=[constants['frame'](route=r,history_count=h) for r in (1,2,3) for h in (0,1,3)]
  elif kind=='normal':fixtures=[constants['frame'](s) for s in ('offered','pending','accepted','migrating','sealed','rehire')]
  elif kind=='selector':fixtures=[constants['_frame'](),constants['_frame'](status='unavailable')]
  else:fixtures=[constants['_frame']()]
 for frame in fixtures:
  native=frame['snapshot_revision'];public=constants.get('PUBLIC_REVISION',7);player=frame['player_character_id']
  snapshot=dict(paused=True,map_ready=True,snapshot_id='original-oracle-frame',revision=public,native_revision=native,
   date_raw=frame['date_raw'],played_character=dict(character_id=player,alive=True),episode_run_id='original-oracle-episode',
   diagnostics=dict(connection_generation=4,bridge_version='0.1.0',hello=dict(bridge_version='0.1.0',
    game_adapter_id='ck3-1.19.0.6-msvc-x64',expected_ck3_version='1.19.0.6',
    expected_ck3_sha256='2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86')))
  captured={}
  query_calls=[0]
  def primitive(step,**kwargs):
   query_calls[0]+=1
   captured.update(step=step,request_fields=kwargs['request_fields'])
   if kwargs['expected_revision']!=public:raise RuntimeError('original public/native revision crossed')
   return dict(step=step,accepted=True,status=frame['status'],query_sequence=1,snapshot_revision=native,
    backend_id='native-headless',**{method['payload']:copy.deepcopy(frame)})
  driver=types.SimpleNamespace(take_snapshot=lambda:copy.deepcopy(snapshot),_execute_primitive_step=primitive)
  def execute(step,**kwargs):
   q=env[method['parse_query']](step)
   return env[method['driver_method']](driver,q,**kwargs)
  service=types.SimpleNamespace(snapshot=lambda:copy.deepcopy(snapshot),execute_step=execute,
   capabilities=lambda:dict(bridge_capabilities=[method['capability']]))
  kwargs=dict(expected_revision=public)
  if kind in ('career','collective','normal','governance'):kwargs['owner_character_id']=frame['requested_owner_character_id']
  if kind=='governance':kwargs['subject_character_id']=frame['subject_character_id']
  setattr(service,method['public_method'],lambda nonce,**args:env[method['public_method']](service,nonce,**args))
  result=env[helper](service,frame['request_nonce'],**kwargs)
  rows.append(dict(kind=kind,frame=frame,service=result,**captured))
  if frame is fixtures[0]:
   for fault_case in ('paused','stale','capability','nonce','paused_nonce'):
    broken=copy.deepcopy(snapshot)
    if fault_case in ('paused','paused_nonce'):broken['paused']=False
    if fault_case=='stale':broken['revision']=public+1
    calls_before=query_calls[0]
    service.snapshot=lambda:copy.deepcopy(broken)
    service.capabilities=lambda:dict(bridge_capabilities=[])
    selected_nonce='' if fault_case in ('nonce','paused_nonce') else frame['request_nonce']
    try:env[helper](service,selected_nonce,**kwargs)
    except (BridgeUnavailableError,UnsupportedStepError,ValueError) as failure:
     fault_rows.append(dict(kind=kind,case=fault_case,python_error=type(failure).__name__,message=str(failure),
      frame=frame,nonce=selected_nonce,public_revision=public,current_revision=broken['revision'],paused=broken['paused'],query_calls=query_calls[0]-calls_before))
    else:raise RuntimeError('actual unsupported original branch unexpectedly succeeded')
   service.snapshot=lambda:copy.deepcopy(snapshot)
   service.capabilities=lambda:dict(bridge_capabilities=[method['capability']])
whole_tests=0
whole_skipped=0
unit_paths=[Path(ref['path']) for ref in manifest['oracle_sources'] if '/tests/unit/' in ref['path'].replace(chr(92),'/')]
if len(unit_paths)!=8:raise RuntimeError('complete original China career unit-module set is required')
for index,path in enumerate(unit_paths):
 with contextlib.redirect_stdout(sys.stderr):
  name='actual_china_career_compatibility_'+str(index)
  spec=importlib.util.spec_from_file_location(name,path)
  module=importlib.util.module_from_spec(spec)
  sys.modules[name]=module
  spec.loader.exec_module(module)
  tested=unittest.TextTestRunner(stream=sys.stderr).run(unittest.defaultTestLoader.loadTestsFromModule(module))
 if not tested.wasSuccessful() or tested.skipped:raise RuntimeError('whole original China career module failed/skipped: '+str(path))
 whole_tests+=tested.testsRun
 whole_skipped+=len(tested.skipped)
for ref in manifest['oracle_sources']:
 p=Path(ref['path'])
 if p.stat().st_size!=ref['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=ref['sha256']:raise RuntimeError('original producer changed during oracle')
json.dump(dict(rows=rows,faults=fault_rows,whole_original_tests=whole_tests,whole_original_skipped=whole_skipped),sys.stdout,separators=(',',':'))
""";
}

