package org.xar.ck3.control.application.planning.finance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.management.ManagementFactory;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;

/** Separate continuing-JVM DATA diagnostic cohort, never a replacement for the fixed P120 ABBA.
 * DRAFT ONLY: finite runner resource/output admission is required before any compilation/execution.
 * Calls the original unchanged Main exactly three times. No PREP, new warmup, cache or business action.
 */
public final class ConstructionContinuingData121Main {
    private static final int PASSES = 3;
    private static final int REPORT_BYTES = 262_144;
    private ConstructionContinuingData121Main() { }

    public static void main(String[] args) throws Throwable {
        long wrapperStart = System.nanoTime();
        Instant entered = Instant.now();
        if (args.length != 2) throw new IllegalArgumentException("root exclusive-new-output-directory required");
        Path root = Path.of(args[0]).toAbsolutePath().normalize().toRealPath();
        Path output = Path.of(args[1]).toAbsolutePath().normalize();
        if (output.startsWith(root)) throw new IllegalArgumentException("diagnostic output must be outside immutable input/CAS root");
        // This intentionally fails for any existing file, directory or link. No reuse or cleanup fallback.
        Files.createDirectory(output);
        if (!output.toRealPath().equals(output)) throw new IllegalArgumentException("canonical exclusive output required");
        ObjectNode summary = StrictJson.object(); summary.put("schema", "ck3.continuing-main-data-121.v1");
        summary.put("cohort", "single-JVM-fixed3-original-Main-invocations-all18calls-retained");
        summary.put("primary_ABBA_replaced", false); summary.put("actual_Policy_Native_Runtime_SAVE", false);
        summary.put("original_Main_modified", false); summary.put("PREP", false);
        summary.put("declared_variant", "P120 current B18; actual class origins must be verified by the runner"); summary.put("root", root.toString());
        summary.put("output", output.toString()); summary.put("enteredUtc", entered.toString());
        summary.put("auxiliary_MX_note", "Approximate VM cumulative counters, not thread CPU or exact pause durations. Never add to Main wall or process CPU.");
        var passes = summary.putArray("passes"); Throwable failure = null;
        var seenCards = new java.util.HashSet<String>();
        try {
            Path expectedPath = root.resolve("EXPECTED.json"); byte[] expectedBytes = readBounded(expectedPath);
            JsonNode expected = StrictJson.parse(expectedBytes, REPORT_BYTES);
            summary.put("EXPECTED_sha256", sha256(expectedBytes));
            for (int pass = 0; pass < PASSES; pass++) {
                ObjectNode row = passes.addObject(); row.put("pass", pass); row.put("startedUtc", Instant.now().toString());
                Path report = output.resolve("pass-" + pass + ".json");
                if (Files.exists(report, LinkOption.NOFOLLOW_LINKS)) throw new IllegalArgumentException("new pass report required");
                row.set("auxiliary_MX_before", auxiliaryVmCounters());
                long invocationStart = System.nanoTime(); Throwable invocationFailure = null;
                try {
                    // Direct call to the existing frozen public Main, not a copied DATA algorithm.
                    ConstructionExactResult114ConsumerMain.main(new String[]{"run", root.toString(), "B0", report.toString()});
                    row.put("main_returned_normally", true);
                } catch (Throwable mainFailure) {
                    invocationFailure = mainFailure;
                    row.put("main_returned_normally", false); row.put("failure_class", mainFailure.getClass().getName());
                    throw mainFailure;
                } finally {
                    row.put("main_invocation_wall_ns", System.nanoTime() - invocationStart);
                    row.put("invocation_endedUtc", Instant.now().toString());
                    try { row.set("auxiliary_MX_after", auxiliaryVmCounters()); }
                    catch (Throwable observationFailure) {
                        if (invocationFailure != null) invocationFailure.addSuppressed(observationFailure);
                        else throw observationFailure;
                    }
                }
                long reviewStart = System.nanoTime();
                byte[] bytes = readBounded(report);
                JsonNode value = StrictJson.parse(bytes, REPORT_BYTES);
                require(value.path("root").asText().equals(root.toString()), "same original root");
                require(value.path("label").asText().equals("B0"), "original internal cache-lane label");
                require(value.path("all_calls").isArray() && value.path("all_calls").size() == 6, "all six calls required");
                JsonNode cards = value.path("software_allocation_cards");
                require(cards.isArray() && cards.size() == 1 && cards.get(0).isTextual(), "one actual allocation card per original Main invocation");
                require(seenCards.add(cards.get(0).textValue()), "distinct original software allocation cards");
                row.set("software_allocation_cards", cards);
                int warm = 0, measured = 0;
                for (JsonNode call : value.path("all_calls")) {
                    require(call.path("failure").isNull(), "original call failure retained");
                    require(call.path("cache_api_used").isBoolean() && call.path("cache_api_used").booleanValue(), "current B cache lane");
                    require(call.path("cas_existed_before_preserve").isBoolean() && call.path("cas_existed_before_preserve").booleanValue(), "original warm-existing CAS");
                    require(call.path("markers").equals(expected), "all original marker fields equal fixed EXPECTED");
                    String kind = call.path("kind").asText();
                    if (kind.equals("warmup")) warm++; else if (kind.equals("measured")) measured++;
                    else throw new IllegalArgumentException("unknown Main call kind");
                    require(call.path("phases").isObject() && call.path("phases").size() == 11, "all eleven original phases required");
                    for (String metric : new String[]{"wall_ns", "cpu_ns", "thread_allocated_bytes"}) {
                        JsonNode whole = call.path("whole").get(metric); require(whole != null, "explicit Main metric");
                        if (whole.isNull()) continue;
                        require(whole.isIntegralNumber(), "exact integral Main metric"); BigInteger sum = BigInteger.ZERO;
                        for (JsonNode phase : call.path("phases")) {
                            JsonNode counter = phase.get(metric); require(counter != null && counter.isIntegralNumber(), "supported phase metric");
                            sum = sum.add(counter.bigIntegerValue());
                        }
                        require(whole.bigIntegerValue().equals(sum), "Main disjoint phase sums");
                    }
                }
                require(warm == 2 && measured == 4, "original warm2 measure4 per invocation");
                row.put("report_path", report.toString()); row.put("report_bytes", bytes.length); row.put("report_sha256", sha256(bytes));
                row.put("all_calls_retained", 6); row.put("original_warmup_calls", warm); row.put("original_measured_calls", measured);
                row.put("report_review_wall_ns", System.nanoTime() - reviewStart); row.put("accepted", true);
                // Storage allocation cards and exact source/CAS identities remain in each original report/runner pins.
            }
            require(seenCards.size() == PASSES, "three distinct actual allocation cards");
            summary.put("distinct_new_allocation_cards", seenCards.size()); summary.put("completed_passes", PASSES); summary.put("all_calls_retained", 18);
            summary.put("original_warmup_calls", 6); summary.put("original_measured_calls", 12); summary.put("success", true);
        } catch (Throwable failed) {
            failure = failed; summary.put("success", false); summary.put("failure_class", failed.getClass().getName());
            summary.put("stop_first_failure", true); throw failed;
        } finally {
            summary.put("endedUtc_before_output", Instant.now().toString());
            summary.put("wrapper_ns_before_summary_output", System.nanoTime() - wrapperStart);
            try {
                Files.write(output.resolve("WRAPPER.json"), FullJsonTree.encode(summary, REPORT_BYTES), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
            } catch (Throwable outputFailure) {
                if (failure != null) failure.addSuppressed(outputFailure); else throw outputFailure;
            }
        }
    }

    private static ObjectNode auxiliaryVmCounters() {
        ObjectNode result = StrictJson.object();
        var compilation = ManagementFactory.getCompilationMXBean();
        boolean supported = compilation != null && compilation.isCompilationTimeMonitoringSupported();
        result.put("compilation_monitoring_supported", supported);
        if (supported) result.put("compilation_elapsed_ms_approx_cumulative", compilation.getTotalCompilationTime());
        else result.putNull("compilation_elapsed_ms_approx_cumulative");
        var collectors = result.putArray("collectors");
        for (var bean : ManagementFactory.getGarbageCollectorMXBeans()) {
            ObjectNode row = collectors.addObject(); row.put("name", bean.getName());
            row.put("collection_count_cumulative_raw", bean.getCollectionCount());
            row.put("collection_elapsed_ms_approx_cumulative_raw", bean.getCollectionTime());
        }
        return result;
    }
    private static byte[] readBounded(Path path) throws Exception {
        long expected = Files.size(path);
        require(expected > 0 && expected <= REPORT_BYTES, "bounded complete metadata file required");
        byte[] bytes = Files.readAllBytes(path);
        require(bytes.length == expected && bytes.length <= REPORT_BYTES, "same bounded metadata bytes required");
        return bytes;
    }
    private static String sha256(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
}
