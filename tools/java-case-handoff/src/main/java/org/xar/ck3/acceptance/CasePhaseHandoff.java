package org.xar.ck3.acceptance;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.*;

/** Reads the existing controller's ownership boundary. Never submits Game commands. */
public final class CasePhaseHandoff {
    private CasePhaseHandoff() {}
    public enum Decision { ROOT_OWNS_NEXT_CHECKPOINT, CONTROLLER_OWNS, TERMINAL_OR_INVALID }
    public record Pin(String path, long bytes, String sha256) {}
    public record Request(int schemaVersion, String machineId, String sourceHead, String runId,
                          Pin runContext, Pin caseDefinition, String previousPhase, String nextPhase,
                          String originalHoldDeadlineDecimal, int timeoutSeconds) {}
    public record Facts(boolean previousAccepted, boolean nextAwaiting, boolean nextAlreadyConsumed,
                        boolean liveHealthy, boolean identityAndBudgetMatch, boolean allControlsFinished) {}
    public record Result(String schema, String machineId, String sourceHead, String runId,
                         String observedAtUtc, Decision decision, String reason,
                         Pin request, Pin previousAccepted, Pin nextAwaiting, Pin nativeReport,
                         boolean sourceCapacityOrGameAdmissionGranted) {}
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private static void need(boolean value, String message) throws IOException {
        if (!value) throw new IOException(message);
    }
    public static Decision evaluate(Facts facts) {
        Objects.requireNonNull(facts);
        if (!facts.liveHealthy || !facts.identityAndBudgetMatch || facts.nextAlreadyConsumed)
            return Decision.TERMINAL_OR_INVALID;
        if (!facts.previousAccepted || !facts.nextAwaiting || !facts.allControlsFinished)
            return Decision.CONTROLLER_OWNS;
        return Decision.ROOT_OWNS_NEXT_CHECKPOINT;
    }
    private static String text(JsonNode node) throws IOException {
        need(node != null && node.isTextual() && !node.textValue().isBlank(), "Nonblank text required");
        return node.textValue();
    }
    private static long integer(JsonNode node) throws IOException {
        need(node != null && node.isIntegralNumber() && node.canConvertToLong(), "Exact integer required");
        return node.longValue();
    }
    private static boolean yes(JsonNode node) { return node != null && node.isBoolean() && node.booleanValue(); }
    private static BigDecimal decimal(JsonNode node) throws IOException {
        need(node != null && node.isNumber(), "Original numeric deadline required");
        return node.decimalValue();
    }
    private static Path path(String value) throws IOException {
        Path p = Path.of(value); need(p.isAbsolute() && p.normalize().equals(p), "Absolute normalized path");
        return p;
    }
    private static byte[] stable(Path p, int maximum) throws Exception {
        BasicFileAttributes before = Files.readAttributes(p, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        need(before.isRegularFile() && !before.isSymbolicLink() && before.size() <= maximum, "Bounded regular file");
        byte[] bytes = Files.readAllBytes(p);
        BasicFileAttributes after = Files.readAttributes(p, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        need(before.size() == bytes.length && after.size() == bytes.length
                && before.lastModifiedTime().equals(after.lastModifiedTime())
                && Objects.equals(before.fileKey(), after.fileKey()), "Current producer changed during read; no grant");
        return bytes;
    }
    private static Pin pin(Path p, byte[] bytes) throws Exception {
        return new Pin(p.toString(), bytes.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    }
    private static JsonNode checked(Pin expected, int maximum) throws Exception {
        need(expected != null && expected.bytes >= 0 && expected.bytes <= maximum
                && expected.sha256.matches("[0-9a-f]{64}"), "Strict bounded Pin");
        byte[] bytes = stable(path(expected.path), maximum);
        need(pin(path(expected.path), bytes).equals(expected), "Original pinned input differs");
        return JSON.readTree(bytes);
    }
    private static Set<String> strings(JsonNode array) throws Exception {
        need(array != null && array.isArray(), "String array required");
        Set<String> values = new LinkedHashSet<>();
        for (JsonNode v : array) need(values.add(text(v)), "Duplicate identifier");
        return Set.copyOf(values);
    }
    private static Pin nullablePin(Path p, int maximum) throws Exception {
        return Files.exists(p) ? pin(p, stable(p, maximum)) : null;
    }
    public static Result inspect(Request request, Pin requestPin, Instant now) throws Exception {
        need(request.schemaVersion == 1 && request.machineId.matches("[a-z0-9-]+")
                && request.sourceHead.matches("[0-9a-f]{40}") && request.runId.startsWith(request.machineId + "--")
                && request.timeoutSeconds > 0 && request.timeoutSeconds <= 300, "Finite same-machine request");
        BigDecimal deadline = new BigDecimal(request.originalHoldDeadlineDecimal);
        BigDecimal epoch = BigDecimal.valueOf(now.getEpochSecond()).add(BigDecimal.valueOf(now.getNano(), 9));
        need(deadline.subtract(epoch).compareTo(BigDecimal.valueOf(180)) > 0, "Original quit reserve; no deadline extension");
        JsonNode context = checked(request.runContext, 4 * 1024 * 1024);
        need(text(context.get("run_id")).equals(request.runId), "Actual immutable run context");
        Path live = path(text(context.get("run_dir")));
        need(live.getFileName().toString().equals(request.runId)
                && path(request.runContext.path).getParent().equals(live), "Actual context directory");
        JsonNode definition = checked(request.caseDefinition, 1024 * 1024);
        JsonNode phases = definition.get("gui_phases"); need(phases != null && phases.isArray(), "Original phase catalog");
        List<String> order = new ArrayList<>(); Map<String, Set<String>> requirements = new LinkedHashMap<>();
        for (JsonNode phase : phases) {
            String id = text(phase.get("id")); need(id.matches("[a-z0-9-]+") && !requirements.containsKey(id), "Exact phase ids");
            order.add(id); requirements.put(id, strings(phase.get("requirements")));
        }
        int index = order.indexOf(request.previousPhase);
        need(index >= 0 && index + 1 < order.size() && order.get(index + 1).equals(request.nextPhase), "Original adjacent phases only");
        Path output = live.resolve("case-output"), previous = output.resolve(request.previousPhase + "-accepted.json");
        Path next = output.resolve(request.nextPhase + "-awaiting.json"), nativePath = live.resolve("native-report.json");
        Pin previousPin = nullablePin(previous, 4 * 1024 * 1024), nextPin = nullablePin(next, 8 * 1024 * 1024);
        byte[] raw = stable(nativePath, 256 * 1024 * 1024); JsonNode report = JSON.readTree(raw);
        boolean healthy = report.path("status").asText().equals("RUNNING") && report.path("phase").asText().equals("hold")
                && (!report.has("error") || report.get("error").isNull())
                && !report.hasNonNull("finished_at") && !yes(report.get("managed_session_done"));
        JsonNode binding = report.path("readiness").path("managed_campaign_run_binding");
        boolean identity = report.has("hold_until_utc_estimated")
                && decimal(report.get("hold_until_utc_estimated")).compareTo(deadline) == 0
                && text(binding.get("run_id")).equals(request.runId)
                && text(binding.get("frozen_argv_sha256")).equals(text(context.path("frozen_argv").get("sha256")));
        if (previousPin != null) {
            JsonNode value = checked(previousPin, 4 * 1024 * 1024);
            identity &= text(value.get("run_id")).equals(request.runId)
                    && text(value.get("machine_id")).equals(request.machineId)
                    && text(value.get("reviewer")).equals("/root");
            JsonNode assertions = value.get("assertions"); need(assertions != null && assertions.isObject(), "Actual accepted assertions");
            Set<String> keys = new HashSet<>(); assertions.fieldNames().forEachRemaining(keys::add);
            identity &= keys.equals(requirements.get(request.previousPhase));
            for (JsonNode valueFlag : assertions) identity &= yes(valueFlag);
        }
        if (nextPin != null) {
            JsonNode value = checked(nextPin, 8 * 1024 * 1024);
            identity &= text(value.get("run_id")).equals(request.runId)
                    && text(value.get("operator_reviewer")).equals("/root")
                    && decimal(value.get("original_hold_deadline")).compareTo(deadline) == 0
                    && strings(value.get("required_assertions")).equals(requirements.get(request.nextPhase));
        }
        boolean consumed = Files.exists(output.resolve(request.nextPhase + "-root-result.json"))
                || Files.exists(output.resolve(request.nextPhase + "-accepted.json"));
        Set<String> finished = new HashSet<>(); boolean complete = true;
        JsonNode rows = report.get("steps"); need(rows != null && rows.isArray(), "Actual native rows");
        for (JsonNode row : rows) {
            String id = text(row.get("id")); boolean done = row.hasNonNull("finished_at") && yes(row.get("ok"));
            complete &= done; if (done) need(finished.add(id), "Unique finished row ids");
        }
        int count = 0;
        try (var controls = Files.newDirectoryStream(live.resolve("controls"), "*.json")) {
            for (Path control : controls) {
                need(++count <= 8192, "Finite exact control inventory");
                JsonNode steps = JSON.readTree(stable(control, 1024 * 1024)).get("steps");
                need(steps != null && steps.isArray(), "Published original control steps");
                for (JsonNode step : steps) complete &= finished.contains(text(step.get("id")));
            }
        }
        Decision decision = evaluate(new Facts(previousPin != null, nextPin != null, consumed, healthy, identity, complete));
        return new Result("xar.original-case-phase-handoff.v1", request.machineId, request.sourceHead, request.runId,
                now.toString(), decision, decision == Decision.ROOT_OWNS_NEXT_CHECKPOINT
                ? "Original controller is waiting for the next Root result; all published controls finished"
                : "Previous acceptance alone never grants Root; next awaiting, exact original budget and quiescence are required",
                requestPin, previousPin, nextPin, pin(nativePath, raw), false);
    }
    public static Request readRequest(Pin pin) throws Exception {
        JsonNode n = checked(pin, 65536);
        Set<String> names = new HashSet<>(); n.fieldNames().forEachRemaining(names::add);
        need(names.equals(Set.of("schemaVersion","machineId","sourceHead","runId","runContext","caseDefinition",
                "previousPhase","nextPhase","originalHoldDeadlineDecimal","timeoutSeconds")), "Exact request fields");
        integer(n.get("schemaVersion")); integer(n.get("timeoutSeconds"));
        for (String key : List.of("machineId","sourceHead","runId","previousPhase","nextPhase","originalHoldDeadlineDecimal")) text(n.get(key));
        for (String key : List.of("runContext","caseDefinition")) {
            JsonNode p = n.get(key); need(p != null && p.isObject() && p.size() == 3, "Exact Pin object");
            text(p.get("path")); integer(p.get("bytes")); text(p.get("sha256"));
        }
        return JSON.treeToValue(n, Request.class);
    }
    public static void main(String[] args) throws Exception {
        need(args.length == 5 && args[0].equals("--wait"), "--wait RequestPath bytes sha256 uniqueOutput");
        Pin input = new Pin(path(args[1]).toString(), Long.parseLong(args[2]), args[3]); Request value = readRequest(input);
        Path out = path(args[4]); need(!Files.exists(out), "Never overwrite prior result");
        Instant until = Instant.now().plusSeconds(value.timeoutSeconds); Result result;
        do {
            result = inspect(value, input, Instant.now());
            if (result.decision != Decision.CONTROLLER_OWNS || !Instant.now().isBefore(until)) break;
            Thread.sleep(200);
        } while (true);
        Files.write(out, JSON.writeValueAsBytes(result), StandardOpenOption.CREATE_NEW);
        System.out.println(JSON.writeValueAsString(result));
        if (result.decision != Decision.ROOT_OWNS_NEXT_CHECKPOINT) System.exit(2);
    }
}

