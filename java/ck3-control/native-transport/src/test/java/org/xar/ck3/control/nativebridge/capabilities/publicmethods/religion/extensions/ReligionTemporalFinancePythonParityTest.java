package org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionContract;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContext.Build;
import org.xar.ck3.control.nativebridge.capabilities.religion.EpidemicOriginalDecoder;

/**
 * Full Python wrapper differential, using retained native command-result packets.
 * This test creates DATA only. It never constructs a Root, Session, guard, permission,
 * installation, or action authority. Python is the existing production oracle, not a
 * second implementation. The oracle subprocess runs only when this test is executed.
 */
final class ReligionTemporalFinancePythonParityTest {
    private static final String ACTIVITIES = ReligionPilgrimage.ACTIVITIES_METHOD;
    private static final String PLANNER = ReligionPilgrimage.QUERY_METHOD;
    private static final String SUBMIT = ReligionPilgrimage.SUBMIT_METHOD;
    private static final String EPIDEMIC = "ck3_query_player_epidemic_recovery_private_v1";
    private static final BigInteger U64 = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final BigInteger I64_MIN = BigInteger.ONE.shiftLeft(63).negate();
    private static final BigInteger I64_MAX = BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE);
    private static final Set<String> METHODS = methods();
    private static final Set<String> ORIGINALS = Set.of(
            "native_driver.py", "g2_private_query_transport.py", "nonwar_private_build.py", "version_identity.py",
            "timeline_blocker_private_transport.py", "player_clergy_appointment_private_transport.py",
            "player_county_conversion_private_observation.py", "player_clergy_candidate_terms_private_observation.py",
            "player_clergy_mode0_source_12004.py", "player_head_of_faith_gold_context_private_transport.py",
            "player_holy_order_loan_context_private_transport.py", "player_holy_order_selected_title_terms_private_transport.py",
            "player_repentance_context_private_transport.py", "player_rite_governance_private_transport.py",
            "player_rite_members_private_transport.py", "player_pilgrimage_activities_private_transport.py",
            "player_pilgrimage_planner_private_transport.py", "epidemic_recovery_private_transport.py");

    private record Vector(String id, String method, ObjectNode packet, ObjectNode before,
            ObjectNode after, ObjectNode arguments) {
        private Vector copy(String suffix) {
            return new Vector(id + suffix, method, packet.deepCopy(), before.deepCopy(),
                    after.deepCopy(), arguments.deepCopy());
        }
        private ObjectNode envelope() { return object(packet.get("result")); }
        private ObjectNode payload() {
            String key = method.equals(EPIDEMIC) ? "player_epidemic_recovery"
                    : method.equals(ACTIVITIES) ? "player_pilgrimage_activities"
                    : (method.equals(PLANNER) || method.equals(SUBMIT)) ? "player_pilgrimage_planner"
                    : "player_" + method.substring("ck3_query_player_".length(), method.length() - 3);
            return object(envelope().get(key));
        }
        private ReligionContract.Request request() {
            return ReligionCodec.decode(method, ReligionCodec.raw(arguments));
        }
        private ReligionTemporalFinance.Frame frame() {
            ObjectNode hello = object(object(before.get("diagnostics")).get("hello"));
            Build build = Build.exact(text(hello, "expected_ck3_version"), text(hello, "expected_ck3_sha256"));
            return new ReligionTemporalFinance.Frame(build, integer(before, "revision"),
                    integer(before, "native_revision"), integer(before, "date_raw"),
                    integer(object(before.get("played_character")), "character_id"),
                    1234L, BigInteger.ONE, text(before, "snapshot_id"), "python-parity-data");
        }
        private ObjectNode oracleInput() {
            ObjectNode n = json().put("id", id).put("method", method);
            n.set("packet", packet); n.set("before", before); n.set("after", after);
            // Public decimal revisions are decoded once; original Python receives its native integer ABI.
            n.set("arguments", ReligionCodec.nativeArguments(request()));
            return n;
        }
    }

    @Test void completeOriginalResponsesReachTheActualPublicFormatterAndSerde() throws Exception {
        List<Vector> vectors = vectors();
        assertEquals(METHODS, vectors.stream().map(Vector::method).collect(java.util.stream.Collectors.toSet()),
                "the fixture manifest must cover every implemented full-response entry point");
        ArrayNode original = oracle(vectors);
        for (int i = 0; i < vectors.size(); i++) {
            Vector v = vectors.get(i); ObjectNode reply = object(original.get(i));
            assertTrue(reply.path("ok").asBoolean(), () -> v.id + ": Python rejected retained packet: " + reply);
            ObjectNode retained = v.packet.deepCopy();
            ObjectNode actual = javaResponse(v, reply);
            ObjectNode expected = publicWidths(v.method, object(reply.get("business")));
            assertEquals(expected, actual, v.id + ": complete wrapper response differs");
            RawJson encoded = ReligionCodec.encode(new ReligionContract.Response(v.request().method(), ReligionCodec.raw(actual)));
            assertEquals(expected, ReligionCodec.object(new RawJson(encoded.bytes())), v.id + ": response serde differs");
            assertEquals(actual, javaResponse(v, reply), v.id + ": formatter mutated retained native input");
            assertEquals(retained, v.packet, v.id + ": original native packet was changed");
            assertEquals(ReligionCodec.nativeArguments(v.request()),
                    ReligionCodec.nativeArguments(ReligionCodec.decode(v.method, ReligionCodec.encode(v.request()))),
                    v.id + ": public request serde changes native arguments");
            assertEquals(1, reply.path("requests").size(), v.id + ": wrapper retried a private read");
        }
    }

    @Test void missingNullBooleanAndFractionalRequiredNativeFieldsAreNotSilentlyDefaulted() throws Exception {
        List<Vector> invalid = new ArrayList<>();
        for (Vector original : vectors()) {
            Vector missing = original.copy("/missing-schema"); missing.payload().remove("schema"); invalid.add(missing);
            Vector nil = original.copy("/null-schema"); nil.payload().putNull("schema"); invalid.add(nil);
            Vector flag = original.copy("/numeric-read-only"); flag.envelope().put("read_only", 1); invalid.add(flag);
            Vector decimal = original.copy("/fractional-native-revision");
            if (decimal.method.equals(ACTIVITIES) || decimal.method.equals(PLANNER) || decimal.method.equals(SUBMIT))
                decimal.payload().put("snapshot_revision", 1.5d);
            else decimal.envelope().put("snapshot_revision", 1.5d);
            invalid.add(decimal);
        }
        ArrayNode original = oracle(invalid);
        for (int i = 0; i < invalid.size(); i++) {
            Vector v = invalid.get(i); ObjectNode reply = object(original.get(i));
            assertFalse(reply.path("ok").asBoolean(), v.id + ": original Python accepted malformed required field");
            assertThrows(RuntimeException.class, () -> javaResponse(v, reply), v.id);
        }
    }

    @Test void fullWidthEpochAndSignedCostsSurviveThePythonToPublicBoundary() throws Exception {
        Vector loan = vectors().stream().filter(v -> v.method.equals("ck3_query_player_holy_order_loan_context_v1")
                && v.payload().path("available").asBoolean()).findFirst().orElseThrow(
                        () -> new AssertionError("an available original loan packet is required"));
        List<Vector> wide = new ArrayList<>();
        for (BigInteger amount : List.of(I64_MIN, BigInteger.valueOf(9007199254740991L),
                BigInteger.valueOf(9007199254740992L), I64_MAX)) {
            Vector v = loan.copy("/wide-" + amount);
            v.payload().put("capture_epoch", U64).put("loan_amount_quote_raw", amount);
            wide.add(v);
        }
        ArrayNode original = oracle(wide);
        for (int i = 0; i < wide.size(); i++) {
            Vector v = wide.get(i); ObjectNode reply = object(original.get(i));
            assertTrue(reply.path("ok").asBoolean(), v.id + ": original oracle rejected exact int64 DATA");
            ObjectNode actual = javaResponse(v, reply);
            assertEquals(publicWidths(v.method, object(reply.get("business"))), actual, v.id);
            assertEquals(U64.toString(), actual.path("capture_epoch").textValue());
            assertTrue(actual.path("loan_amount_quote_raw").isTextual());
            assertTrue(actual.path("played_character_id").isIntegralNumber(), "bounded role IDs remain numeric");
        }
    }

    @Test void publicRevisionInputPreservesItsDeclaredIntegerDomain() {
        String name = "ck3_query_player_holy_order_loan_context_v1";
        for (String token : List.of("\"18446744073709551615\"", "9007199254740991")) {
            ReligionContract.Request request = ReligionCodec.decode(name, raw("{\"expected_revision\":" + token + "}"));
            assertEquals(request, ReligionCodec.decode(name, ReligionCodec.encode(request)));
        }
        for (String token : List.of("null", "true", "1.0", "0", "9007199254740992",
                "\"01\"", "\"18446744073709551616\""))
            assertThrows(IllegalArgumentException.class,
                    () -> ReligionCodec.decode(name, raw("{\"expected_revision\":" + token + "}")), token);
        assertThrows(IllegalArgumentException.class, () -> ReligionCodec.decode(name, raw("{}")));
        ReligionContract.Request missing = ReligionCodec.decode(EPIDEMIC,
                raw("{\"expected_revision\":\"1\",\"requested_title_id\":7}"));
        ReligionContract.Request nil = ReligionCodec.decode(EPIDEMIC,
                raw("{\"expected_revision\":\"1\",\"requested_title_id\":7,\"expected_event_instance_id\":null}"));
        assertEquals(new ReligionContract.Absent(ReligionContract.Presence.MISSING),
                missing.value(ReligionContract.Field.EXPECTED_EVENT_INSTANCE_ID));
        assertEquals(new ReligionContract.Absent(ReligionContract.Presence.NULL),
                nil.value(ReligionContract.Field.EXPECTED_EVENT_INSTANCE_ID));
        assertFalse(ReligionCodec.object(ReligionCodec.encode(missing)).has("expected_event_instance_id"));
        assertTrue(ReligionCodec.object(ReligionCodec.encode(nil)).get("expected_event_instance_id").isNull());
        assertEquals(missing, ReligionCodec.decode(EPIDEMIC, ReligionCodec.encode(missing)));
        assertEquals(nil, ReligionCodec.decode(EPIDEMIC, ReligionCodec.encode(nil)));
    }

    @Test void everyOriginalPilgrimageOperationAndOptionRetainsUnknownOutcome() throws Exception {
        Vector base = vectors().stream().filter(v -> v.method.equals(PLANNER)).findFirst().orElseThrow();
        List<Vector> variants = new ArrayList<>();
        // These are explicit DATA mutations of one retained original wire body, not observed game results.
        for (ReligionPilgrimage.Operation operation : ReligionPilgrimage.Operation.values())
            for (ReligionPilgrimage.Option option : ReligionPilgrimage.Option.values()) {
                String method = operation.submit() ? SUBMIT : PLANNER;
                ObjectNode args = json().put("expected_revision", base.frame().publicRevision().toString())
                        .put("operation", operation.wire()).put("option_key", option.key());
                if (Set.of(ReligionPilgrimage.Operation.CAN_SELECT, ReligionPilgrimage.Operation.SELECT,
                        ReligionPilgrimage.Operation.START).contains(operation)) args.put("province_id", 2147488308L);
                if (operation.submit()) args.put("policy_positive", true);
                Vector v = new Vector(base.id + "/" + operation.wire() + "/" + option.key(), method,
                        base.packet.deepCopy(), base.before.deepCopy(), base.after.deepCopy(), args);
                ObjectNode envelope = v.envelope(), body = v.payload();
                envelope.put("step", operation.submit() ? ReligionPilgrimage.SUBMIT_STEP : ReligionPilgrimage.QUERY_STEP)
                        .put("read_only", !operation.submit());
                body.put("operation", operation.wire()).put("special_option_key", option.key())
                        .put("read_only", !operation.submit());
                if (body.hasNonNull("planner")) object(body.get("planner")).put("selected_option_key", option.key());
                if (body.hasNonNull("quote")) {
                    ObjectNode quote = object(body.get("quote")); quote.put("special_option_key", option.key());
                    object(quote.get("selected_option")).put("key", option.key());
                }
                if (operation.submit()) body.put("operation_status", "submission_outcome_unknown")
                        .put("ledger_state", "submission_outcome_unknown").put("needs_recovery", true).put("invoked", true);
                variants.add(v);
            }
        ArrayNode original = oracle(variants);
        for (int i = 0; i < variants.size(); i++) {
            Vector v = variants.get(i); ObjectNode reply = object(original.get(i));
            assertTrue(reply.path("ok").asBoolean(), () -> v.id + ": original operation rejected DATA: " + reply);
            ObjectNode actual = javaResponse(v, reply);
            assertEquals(publicWidths(v.method, object(reply.get("business"))), actual, v.id);
            for (String flag : List.of("automatic_retry", "business_outcome_observed", "action_ready"))
                assertTrue(actual.get(flag).isBoolean() && !actual.get(flag).booleanValue(), v.id + "/" + flag);
            if (v.method.equals(SUBMIT)) {
                assertEquals("submission_outcome_unknown", actual.path("operation_status").textValue());
                assertTrue(actual.path("needs_recovery").booleanValue());
            }
            assertEquals(1, reply.path("requests").size(), "UNKNOWN must not cause a second native send");
        }
    }

    private static ObjectNode javaResponse(Vector v, ObjectNode oracleReply) {
        ReligionContract.Request request = v.request(); ObjectNode result;
        if (v.method.equals(ACTIVITIES) || v.method.equals(PLANNER) || v.method.equals(SUBMIT)) {
            // Nonce comes from the actual existing Python wrapper's transmitted packet.
            String nonce = oracleReply.path("requests").isArray() && !oracleReply.path("requests").isEmpty()
                    ? text(object(oracleReply.path("requests").get(0)), "request_id") : "rejected-data";
            if (v.method.equals(SUBMIT)) {
                // Formatting an already retained native response is DATA, never canonical submission qualification.
                result = ReligionPilgrimage.publicSubmission(ReligionCodec.raw(v.envelope()), v.frame(),
                        ReligionPilgrimage.Request.from(request), nonce, text(v.after, "snapshot_id"));
            } else {
                ReligionPilgrimage.ReadSelection selected = v.method.equals(ACTIVITIES)
                        ? new ReligionPilgrimage.Activities(request.expectedRevision())
                        : new ReligionPilgrimage.PlannerRead(ReligionPilgrimage.Request.from(request));
                result = ReligionPilgrimage.normalizeEnvelope(selected, v.frame(), v.envelope(), nonce,
                        text(v.after, "snapshot_id")).publicResult();
            }
        } else if (v.method.equals(EPIDEMIC)) {
            ReligionContract.Value event = request.value(ReligionContract.Field.EXPECTED_EVENT_INSTANCE_ID);
            result = EpidemicOriginalDecoder.publicResult(v.envelope(), v.frame(),
                    event instanceof ReligionContract.IntegerValue exact ? exact.value() : null);
        } else {
            ReligionTemporalFinance.Kind kind = ReligionTemporalFinance.Kind.method(v.method);
            BigInteger candidate = kind == ReligionTemporalFinance.Kind.CLERGY
                    ? request.integer(ReligionContract.Field.CANDIDATE_CHARACTER_ID) : BigInteger.ZERO;
            result = ReligionTemporalFinance.normalizeEnvelope(new ReligionTemporalFinance.Selection(kind, candidate),
                    v.frame(), v.envelope()).publicResult();
        }
        return ReligionCodec.object(ReligionCodec.encode(new ReligionContract.Response(request.method(), ReligionCodec.raw(result))));
    }

    /** Independent, explicit representation delta; never use the production width projector as the oracle. */
    private static ObjectNode publicWidths(String method, ObjectNode original) {
        ObjectNode n = original.deepCopy();
        decimal(n, "/queried_revision", false); decimal(n, "/queried_native_revision", false);
        decimal(n, "/snapshot_revision", false);
        if (method.equals(EPIDEMIC)) {
            decimal(n, "/query_sequence", false); decimal(n, "/observation_revision", false);
            decimal(n, "/player_epidemic_recovery/snapshot_revision", false);
            return n;
        }
        if (method.equals(ACTIVITIES) || method.equals(PLANNER) || method.equals(SUBMIT)) {
            if (method.equals(ACTIVITIES)) for (JsonNode row : n.path("activities")) activityWidths(object(row));
            else {
                if (n.hasNonNull("new_identity")) activityWidths(object(n.get("new_identity")));
                if (n.hasNonNull("quote")) {
                    ObjectNode quote = object(n.get("quote"));
                    for (String field : List.of("snapshot_revision", "normal_refresh_sequence", "configuration_fingerprint"))
                        decimal(quote, "/" + field, field.equals("configuration_fingerprint"));
                    signedArray(quote, "configured_cost_raw"); signedArray(quote, "diagnostic_aggregate_raw");
                }
            }
            return n;
        }
        decimal(n, "/capture_epoch", method.contains("clergy_") || method.contains("rite_"));
        if (method.contains("clergy_")) {
            if (n.hasNonNull("county_conversion")) {
                ObjectNode county = object(n.get("county_conversion")); decimal(county, "/capture_epoch", true);
                signed(county, "current_percentage_progress_raw"); signed(county, "current_conversion_monthly_rate_raw");
                for (JsonNode row : county.path("candidates")) signed(object(row), "native_monthly_rate_raw");
            }
            if (n.hasNonNull("candidate_terms")) for (String key : List.of("capture_epoch", "public_revision", "native_revision"))
                decimal(object(n.get("candidate_terms")), "/" + key, true);
            if (n.hasNonNull("clergy_mode0_source")) {
                ObjectNode source = object(n.get("clergy_mode0_source")); decimal(source, "/capture_epoch", true);
                for (String key : List.of("native_revision", "query_sequence", "proof_epoch"))
                    decimal(source, "/source_read_frame/" + key, true);
                optionalDecimal(source, "/generic_trigger/scope_full_id_payload");
            }
        } else if (method.contains("rite_governance")) {
            for (String key : List.of("state_rite", "heads", "organization")) decimal(n, "/" + key + "/capture_epoch", true);
        } else if (method.contains("loan_context")) {
            for (String key : List.of("loan_amount_quote_raw", "loan_amount_owed_raw", "borrower_years_raw", "lender_years_raw")) signed(n, key);
            if (n.path("available").asBoolean()) for (String decision : List.of("borrow_decision", "repay_decision"))
                for (String resource : List.of("gold", "treasury", "prestige", "piety")) signed(object(n.path(decision).get("costs_raw")), resource);
        } else if (method.contains("selected_title_terms")) {
            for (JsonNode decision : n.path("decisions")) for (JsonNode candidate : decision.path("candidates"))
                signedArray(object(candidate), "resource_costs_raw");
        } else if (method.contains("head_of_faith_gold") || method.contains("repentance")) {
            financeWidths(n, method.contains("repentance"));
        }
        return n;
    }
    private static void financeWidths(ObjectNode n, boolean repentance) {
        signedArray(object(n.get("declared_costs")), "raw");
        ObjectNode acceptance = object(n.get("acceptance_preview"));
        signed(acceptance, "recipient_score_raw"); signed(acceptance, "intermediary_score_raw");
        if (!repentance) {
            signed(object(n.get("gold_proceeds")), "amount_raw");
            signed(object(n.get("acceptance_effect_consequence")), "piety_raw");
        } else {
            for (String key : List.of("repentance_fallback_sources", "repentance_recovery_inputs",
                    "repentance_pam_route", "ordinary_recovery_readiness"))
                if (n.hasNonNull(key)) decimal(n, "/" + key + "/capture_epoch", false);
            if (n.hasNonNull("recipient_candidates")) {
                decimal(n, "/recipient_candidates/capture_epoch", false);
                for (JsonNode row : n.path("recipient_candidates").path("candidates")) {
                    ObjectNode terms = object(row.get("terms")); decimal(terms, "/capture_epoch", false); financeWidths(terms, true);
                }
            }
        }
    }
    private static void activityWidths(ObjectNode n) {
        if (n.path("native_completion_stamp_observed").asBoolean()) decimal(n, "/native_completion_stamp_raw", true);
        else assertTrue(n.has("native_completion_stamp_raw") && n.get("native_completion_stamp_raw").isNull());
    }
    private static void optionalDecimal(ObjectNode n, String pointer) {
        JsonNode value = n.at(pointer); if (!value.isMissingNode() && !value.isNull()) decimal(n, pointer, true);
    }
    private static void decimal(ObjectNode root, String pointer, boolean zero) {
        int split = pointer.lastIndexOf('/'); ObjectNode parent = object(root.at(pointer.substring(0, split)));
        String key = pointer.substring(split + 1); JsonNode value = parent.get(key);
        assertNotNull(value, pointer); assertTrue(value.isIntegralNumber(), pointer);
        BigInteger exact = value.bigIntegerValue();
        assertTrue(exact.compareTo(zero ? BigInteger.ZERO : BigInteger.ONE) >= 0 && exact.compareTo(U64) <= 0, pointer);
        parent.put(key, exact.toString());
    }
    private static void signed(ObjectNode n, String key) {
        if (!n.hasNonNull(key)) return; JsonNode value = n.get(key); assertTrue(value.isIntegralNumber(), key);
        BigInteger exact = value.bigIntegerValue(); assertTrue(exact.compareTo(I64_MIN) >= 0 && exact.compareTo(I64_MAX) <= 0, key);
        n.put(key, exact.toString());
    }
    private static void signedArray(ObjectNode n, String key) {
        if (!n.hasNonNull(key)) return; JsonNode original = n.get(key); assertTrue(original.isArray(), key);
        ArrayNode values = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();
        for (JsonNode value : original) {
            assertTrue(value.isIntegralNumber(), key); BigInteger exact = value.bigIntegerValue();
            assertTrue(exact.compareTo(I64_MIN) >= 0 && exact.compareTo(I64_MAX) <= 0, key); values.add(exact.toString());
        }
        n.set(key, values);
    }

    private static List<Vector> vectors() throws Exception {
        Path manifest = Path.of(required("xar.religion.r1.fixtureManifest")).toAbsolutePath().normalize();
        byte[] bytes = Files.readAllBytes(manifest);
        assertEquals(required("xar.religion.r1.fixtureManifestSha256"), sha(bytes), "original fixture manifest changed");
        ObjectNode root = ReligionCodec.object(new RawJson(bytes));
        assertEquals("xar.test.religion-r1-full-response-vectors/v1", text(root, "schema"));
        Path bridge = repository().resolve("ck3_autonomous_player/src/xar_autoplayer/bridge");
        JsonNode sources = root.get("python_sources"); assertNotNull(sources); assertTrue(sources.isArray());
        Set<String> originals = new HashSet<>();
        for (JsonNode source : sources) {
            ObjectNode ref = object(source); String name = text(ref, "name");
            assertTrue(ORIGINALS.contains(name) && originals.add(name), "unexpected/duplicate original Python source");
            assertEquals(text(ref, "sha256"), sha(Files.readAllBytes(bridge.resolve(name))), name + ": original normalizer changed");
        }
        assertEquals(ORIGINALS, originals, "full original wrapper/normalizer closure must be pinned");
        JsonNode cases = root.get("cases"); assertNotNull(cases); assertTrue(cases.isArray() && !cases.isEmpty());
        List<Vector> result = new ArrayList<>(); Set<String> ids = new HashSet<>();
        for (JsonNode row : cases) {
            ObjectNode item = object(row); String id = text(item, "id"), method = text(item, "method");
            assertTrue(ids.add(id), "duplicate vector identity"); assertTrue(METHODS.contains(method), method);
            ObjectNode ref = object(item.get("packet"));
            Path packet = manifest.getParent().resolve(text(ref, "path")).normalize();
            byte[] original = Files.readAllBytes(packet); assertEquals(text(ref, "sha256"), sha(original), id + ": original native packet changed");
            ObjectNode value = ReligionCodec.object(new RawJson(original));
            assertEquals("command_result", text(value, "type")); assertTrue(value.path("ok").isBoolean() && value.path("ok").booleanValue());
            result.add(new Vector(id, method, value, object(item.get("before")).deepCopy(),
                    object(item.get("after")).deepCopy(), object(item.get("arguments")).deepCopy()));
        }
        return List.copyOf(result);
    }

    private static ArrayNode oracle(List<Vector> vectors) throws Exception {
        ArrayNode input = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();
        vectors.forEach(v -> input.add(v.oracleInput()));
        Path repo = repository();
        assertTrue(Files.isRegularFile(repo.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py")));
        Path python = Path.of(required("xar.python"));
        assertTrue(python.isAbsolute() && Files.isRegularFile(python), "same absolute admitted Python is required");
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-B", "-c", PYTHON, repo.toString())
                .directory(repo.toFile()).redirectErrorStream(true);
        builder.environment().put("PYTHONPATH", repo.resolve("ck3_autonomous_player/src").toString());
        builder.environment().put("XAR_SOURCE_REPOSITORY", repo.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONUTF8", "1");
        Process process = builder.start();
        var reader = Executors.newSingleThreadExecutor();
        try {
            var output = reader.submit(() -> process.getInputStream().readAllBytes());
            try (var stdin = process.getOutputStream()) {
                stdin.write(new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(input));
            }
            assertTrue(process.waitFor(Duration.ofSeconds(60).toMillis(), TimeUnit.MILLISECONDS), "original Python oracle timed out");
            byte[] bytes = output.get(5, TimeUnit.SECONDS);
            assertEquals(0, process.exitValue(), () -> new String(bytes, StandardCharsets.UTF_8));
            JsonNode value = org.xar.ck3.control.nativebridge.NativeWire.parse(bytes);
            assertTrue(value.isArray()); assertEquals(vectors.size(), value.size()); return (ArrayNode) value;
        } finally { process.destroyForcibly(); reader.shutdownNow(); }
    }
    private static Set<String> methods() {
        Set<String> result = new HashSet<>();
        for (ReligionTemporalFinance.Kind kind : ReligionTemporalFinance.Kind.values()) result.add(kind.method());
        result.add(ACTIVITIES); result.add(PLANNER); result.add(SUBMIT); result.add(EPIDEMIC); return Set.copyOf(result);
    }
    private static String required(String property) {
        String value = System.getProperty(property); assertNotNull(value, "required CI input: -D" + property);
        assertFalse(value.isBlank(), property); return value;
    }
    private static Path repository() {
        Path root = Path.of(required("xar.repository.root"));
        assertTrue(root.isAbsolute() && Files.isDirectory(root), "same absolute admitted repository is required");
        return root.normalize();
    }
    private static String sha(byte[] bytes) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
    private static ObjectNode json() { return com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode(); }
    private static ObjectNode object(JsonNode n) { assertNotNull(n); assertTrue(n.isObject(), String.valueOf(n)); return (ObjectNode) n; }
    private static String text(ObjectNode n, String key) { assertNotNull(n.get(key), key); assertTrue(n.get(key).isTextual(), key); return n.get(key).textValue(); }
    private static BigInteger integer(ObjectNode n, String key) { assertNotNull(n.get(key), key); assertTrue(n.get(key).isIntegralNumber(), key); return n.get(key).bigIntegerValue(); }
    private static RawJson raw(String json) { return new RawJson(json.getBytes(StandardCharsets.UTF_8)); }

    private static final String PYTHON = """
            import copy, importlib, json, pathlib, sys
            sys.dont_write_bytecode = True
            root = pathlib.Path(sys.argv[1])
            sys.path.insert(0, str(root / 'ck3_autonomous_player' / 'src'))
            from xar_autoplayer.bridge.native_driver import NativeProtocolState
            modules = {
                'ck3_query_player_clergy_appointment_v1': ('player_clergy_appointment_private_transport', 'query_player_clergy_appointment_private_v1', 'allow_private_player_clergy_appointment_query'),
                'ck3_query_player_head_of_faith_gold_context_v1': ('player_head_of_faith_gold_context_private_transport', 'query_player_head_of_faith_gold_context_private_v1', 'allow_private_player_religion_context_query'),
                'ck3_query_player_holy_order_loan_context_v1': ('player_holy_order_loan_context_private_transport', 'query_player_holy_order_loan_context_private_v1', 'allow_private_player_religion_context_query'),
                'ck3_query_player_holy_order_selected_title_terms_v1': ('player_holy_order_selected_title_terms_private_transport', 'query_player_holy_order_selected_title_terms_private_v1', 'allow_private_player_religion_context_query'),
                'ck3_query_player_repentance_context_v1': ('player_repentance_context_private_transport', 'query_player_repentance_context_private_v1', 'allow_private_player_religion_context_query'),
                'ck3_query_player_rite_governance_v1': ('player_rite_governance_private_transport', 'query_player_rite_governance_private_v1', 'allow_private_player_rite_governance_query'),
                'ck3_query_player_rite_members_v1': ('player_rite_members_private_transport', 'query_player_rite_members_private_v1', 'allow_private_player_rite_members_query'),
                'ck3_query_player_pilgrimage_activities_v1': ('player_pilgrimage_activities_private_transport', 'query_player_pilgrimage_activities_private_v1', 'allow_private_player_pilgrimage_activities_query'),
                'ck3_query_player_pilgrimage_planner_v1': ('player_pilgrimage_planner_private_transport', 'query_player_pilgrimage_planner_private_v1', 'allow_private_player_pilgrimage_execution'),
                'ck3_submit_player_pilgrimage_planner_v1': ('player_pilgrimage_planner_private_transport', 'submit_player_pilgrimage_planner_private_v1', 'allow_private_player_pilgrimage_execution'),
                'ck3_query_player_epidemic_recovery_private_v1': ('epidemic_recovery_private_transport', 'query_player_epidemic_recovery_private_v1', 'allow_private_epidemic_recovery_query'),
            }
            class Driver:
                def __init__(self, case, permission):
                    self.case, self.sent = case, []
                    self.endpoint = self
                    self.state = NativeProtocolState('offline-fixture:religion-r1-parity')
                    setattr(self, permission, True)
                def take_snapshot(self):
                    return copy.deepcopy(self.case['after'] if self.sent else self.case['before'])
                def take_snapshot_without_native_command_history(self):
                    return self.take_snapshot()
                def capabilities(self):
                    return {}
                def send(self, request):
                    self.sent.append(copy.deepcopy(request))
                    packet = copy.deepcopy(self.case['packet'])
                    packet['request_id'] = request['request_id']
                    if self.state.ingest(packet) != 'command_result':
                        raise AssertionError('retained packet was not ingested by the actual protocol cache')
            replies = []
            for case in json.load(sys.stdin):
                module, function, permission = modules[case['method']]
                driver = Driver(case, permission)
                try:
                    fn = getattr(importlib.import_module('xar_autoplayer.bridge.' + module), function)
                    arguments = dict(case['arguments'])
                    arguments.setdefault('timeout_seconds', 1)
                    business = fn(driver, **arguments)
                    replies.append({'ok': True, 'business': business, 'requests': driver.sent})
                except Exception as error:
                    replies.append({'ok': False, 'exception_type': type(error).__name__, 'message': str(error), 'requests': driver.sent})
            print(json.dumps(replies, ensure_ascii=True, separators=(',', ':')))
            """;
}
