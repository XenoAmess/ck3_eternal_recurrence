package org.xar.ck3.control.application.planning.finance;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;

/** One manual diagnostic invocation of the unchanged consumer Main, not an A/B benchmark.
 * JDK-only code deliberately keeps the target class and its dependencies uninitialized until
 * the measured Class.forName call. All nano checkpoints are relative to wrapper main entry;
 * the separately bracketed UTC sample does not synchronize child and parent clock domains.
 * Class.forName includes loading/linking/dependency initialization, not just a static initializer.
 * The invoke span includes reflection, the complete target call, its output, and return overhead.
 * Wrapper class loading, summary output, stdout, and VM exit have separate or external boundaries.
 */
public final class ConstructionMainClock131Main {
    private static final String TARGET =
            "org.xar.ck3.control.application.planning.finance.ConstructionExactResult114ConsumerMain";

    private ConstructionMainClock131Main() { }

    /** DATA_ROOT ORIGINAL_MAIN_REPORT WRAPPER_CLOCK_REPORT; both reports must be absent. */
    public static void main(String[] args) throws Throwable {
        long entry = System.nanoTime();
        long utcBefore = System.nanoTime() - entry;
        Instant utc = Instant.now();
        long utcAfter = System.nanoTime() - entry;
        if (args.length != 3) throw new IllegalArgumentException("three diagnostic arguments required");
        Path root = Path.of(args[0]).toRealPath();
        Path mainReport = newOutput(args[1], root);
        Path clockReport = newOutput(args[2], root);
        if (mainReport.equals(clockReport)) throw new IllegalArgumentException("distinct report paths required");
        // Native owns an exclusive new metadata directory. Main's original output implementation is unchanged.
        String[] mainArgs = {"run", root.toString(), "B0", mainReport.toString()};
        long initStart = -1, initEnd = -1, lookupStart = -1, lookupEnd = -1;
        long invokeStart = -1, invokeEnd = -1;
        boolean initCompleted = false, lookupCompleted = false, invokeCompleted = false;
        int invocations = 0;
        Throwable failed = null;
        try {
            Class<?> target;
            initStart = System.nanoTime() - entry;
            try {
                target = Class.forName(TARGET, true, ClassLoader.getSystemClassLoader());
                initCompleted = true;
            } finally {
                initEnd = System.nanoTime() - entry;
            }
            Method main;
            lookupStart = System.nanoTime() - entry;
            try {
                main = target.getMethod("main", String[].class);
                lookupCompleted = true;
            } finally {
                lookupEnd = System.nanoTime() - entry;
            }
            invokeStart = System.nanoTime() - entry;
            invocations++;
            try {
                main.invoke(null, (Object) mainArgs);
                invokeCompleted = true;
            } catch (InvocationTargetException wrapper) {
                Throwable cause = wrapper.getCause();
                throw cause == null ? wrapper : cause;
            } finally {
                invokeEnd = System.nanoTime() - entry;
            }
        } catch (Throwable failure) {
            failed = failure;
        } finally {
            long reportStart = System.nanoTime() - entry;
            try {
                // Only fixed JSON keys, numbers, and booleans: no JSON library or error-message escaping.
                String report = "{\n"
                        + "  \"schema\":\"ck3.p131.single-main-clock/v1\",\n"
                        + "  \"nano_checkpoints_relative_to_wrapper_entry\":true,\n"
                        + "  \"utc_anchor_before_ns\":" + utcBefore + ",\n"
                        + "  \"utc_anchor_after_ns\":" + utcAfter + ",\n"
                        + "  \"utc_anchor_epoch_second\":" + utc.getEpochSecond() + ",\n"
                        + "  \"utc_anchor_nano\":" + utc.getNano() + ",\n"
                        + "  \"target_init_start_ns\":" + initStart + ",\n"
                        + "  \"target_init_end_ns\":" + initEnd + ",\n"
                        + "  \"target_init_completed\":" + initCompleted + ",\n"
                        + "  \"get_method_start_ns\":" + lookupStart + ",\n"
                        + "  \"get_method_end_ns\":" + lookupEnd + ",\n"
                        + "  \"get_method_completed\":" + lookupCompleted + ",\n"
                        + "  \"invoke_start_ns\":" + invokeStart + ",\n"
                        + "  \"invoke_end_ns\":" + invokeEnd + ",\n"
                        + "  \"invoke_completed\":" + invokeCompleted + ",\n"
                        + "  \"main_invocations\":" + invocations + ",\n"
                        + "  \"target_failed\":" + (failed != null) + ",\n"
                        + "  \"summary_prepare_start_ns\":" + reportStart + ",\n"
                        + "  \"production_or_main_modified\":false,\n"
                        + "  \"Game_Native_HTTP_SAVE\":0\n"
                        + "}\n";
                long writeStart = System.nanoTime() - entry;
                boolean written = false;
                try {
                    Files.writeString(clockReport, report, StandardCharsets.UTF_8,
                            StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
                    written = true;
                } finally {
                    long writeEnd = System.nanoTime() - entry;
                    // A post-write clock cannot be put in the already-written report without rewriting it.
                    String line = "P131_WRAPPER_OUTPUT_CLOCK {\"schema\":\"ck3.p131.wrapper-output-clock/v1\","
                            + "\"summary_prepare_start_ns\":" + reportStart + ","
                            + "\"summary_write_start_ns\":" + writeStart + ","
                            + "\"summary_write_end_ns\":" + writeEnd + ","
                            + "\"summary_written\":" + written + ","
                            + "\"clock_line_sample_ns\":" + (System.nanoTime() - entry) + "}";
                    System.out.println(line);
                }
            } catch (Throwable outputFailure) {
                if (failed == null) failed = outputFailure;
                else if (failed != outputFailure) failed.addSuppressed(outputFailure);
            }
        }
        if (failed != null) throw failed;
    }

    private static Path newOutput(String argument, Path root) throws Exception {
        Path requested = Path.of(argument).toAbsolutePath().normalize();
        Path parent = requested.getParent();
        if (parent == null || !Files.isDirectory(parent))
            throw new IllegalArgumentException("existing report parent directory required");
        Path output = parent.toRealPath().resolve(requested.getFileName());
        if (output.startsWith(root)) throw new IllegalArgumentException("report must be outside fixed DATA root");
        if (Files.exists(output, LinkOption.NOFOLLOW_LINKS))
            throw new IllegalArgumentException("report already exists");
        return output;
    }
}
