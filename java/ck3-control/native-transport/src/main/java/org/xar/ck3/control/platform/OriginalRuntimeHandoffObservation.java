package org.xar.ck3.control.platform;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;

/** Pure archived DATA verification. This class never opens a process/store or issues a live Lease. */
public final class OriginalRuntimeHandoffObservation {
    private OriginalRuntimeHandoffObservation() { }
    public enum Scope { RELIC, HOLY_CREATION, GRANT }
    /** All wide process identity/time/accounting values retain canonical decimal text. */
    public record Data(String machineId, String originalStore, List<ExactRef> originalEvidence,
            String pidDecimal, String creationFiletimeDecimal, String observedAtUtc, String exitCodeDecimal) {
        public Data { originalEvidence = List.copyOf(originalEvidence); }
    }
    /** Decode the exact archived producer bytes against the same census manifest, without fresh I/O. */
    public static Data decode(Scope scope, byte[] original, Path expectedStore, String expectedMachine,
            List<ExactRef> originalEvidence) throws IOException {
        Objects.requireNonNull(scope); Objects.requireNonNull(original); Objects.requireNonNull(expectedStore);
        Objects.requireNonNull(expectedMachine); Objects.requireNonNull(originalEvidence);
        try {
            need(original.length > 0 && original.length <= (1 << 20), "Bounded original OS observation required");
            need(expectedMachine.matches("[a-z0-9][a-z0-9-]{0,63}") && !expectedMachine.equals("unknown"),
                    "Known original machine required");
            JsonNode root = ControlBuild.strictMapper().readTree(original);
            shape(root, Set.of("schema", "machine_id", "scope", "original_store", "original_cwd",
                    "original_arguments", "original_sources", "retirement"));
            need(text(root.get("schema")).equals("xar.original-python-runtime-retirement/v1"), "Original schema differs");
            need(text(root.get("scope")).equals("ORIGINAL_OWNED_JOB_RETIRED"), "Original retirement kind differs");
            String machine = text(root.get("machine_id"));
            need(machine.equals(expectedMachine), "Original machine differs from archived census");
            Path store = path(text(root.get("original_store")));
            need(store.equals(path(expectedStore.toString())), "Original store differs from archived census");
            path(text(root.get("original_cwd")));
            JsonNode argsNode = root.get("original_arguments");
            need(argsNode.isArray() && argsNode.size() == 7, "Exact original isolated launch arguments required");
            var args = new ArrayList<String>();
            for (JsonNode item : argsNode) args.add(text(item));
            JsonNode refsNode = root.get("original_sources");
            need(refsNode.isArray() && refsNode.size() > 1 && refsNode.size() <= 256,
                    "Complete bounded original executable/program sources required");
            var refs = new ArrayList<ExactRef>();
            var paths = new HashSet<Path>();
            for (JsonNode item : refsNode) {
                shape(item, Set.of("path", "bytes", "sha256"));
                need(item.get("bytes").isIntegralNumber() && item.get("bytes").canConvertToLong()
                        && item.get("bytes").longValue() > 0, "Original source byte count must be an exact positive integer");
                ExactRef ref = ExactRef.fromJson(item);
                need(paths.add(path(ref.path())), "Duplicate original native source path");
                refs.add(ref);
            }
            need(refs.equals(originalEvidence), "Original source evidence differs from complete captured manifest");
            JsonNode r = root.get("retirement");
            shape(r, Set.of("pid_decimal", "creation_filetime_decimal", "executable", "session_nonce", "observed_at_utc",
                    "exit_code_decimal", "active_processes_decimal", "memory_limit_bytes_decimal",
                    "peak_job_memory_bytes_decimal", "limit_flags"));
            Path executable = path(text(r.get("executable")));
            need(Path.of(refs.get(0).path()).equals(executable), "Original process executable source differs");
            need(WindowsOriginalRuntimeHandoff.originalStore(scope, args, executable, refs).equals(store),
                    "Original store is not this exact executed finite old scope");
            String pid = decimal(r.get("pid_decimal"), 32, true);
            String birth = decimal(r.get("creation_filetime_decimal"), 64, true);
            String exit = decimal(r.get("exit_code_decimal"), 32, false);
            need(decimal(r.get("active_processes_decimal"), 32, false).equals("0"), "Original Job was not empty");
            String memory = decimal(r.get("memory_limit_bytes_decimal"), 63, true);
            String peak = decimal(r.get("peak_job_memory_bytes_decimal"), 63, false);
            need(new BigInteger(peak).compareTo(new BigInteger(memory)) <= 0, "Original Job memory exceeded limit");
            JsonNode flags = r.get("limit_flags");
            need(flags.isIntegralNumber() && flags.canConvertToInt()
                    && flags.intValue() == WindowsJobProcess.REQUIRED_FLAGS, "Original no-breakaway Job limits differ");
            need(text(r.get("session_nonce")).matches("[0-9a-f]{64}"), "Original owned session identity differs");
            String observed = text(r.get("observed_at_utc"));
            need(Instant.parse(observed).toString().equals(observed), "Canonical original UTC observation required");
            return new Data(machine, store.toString(), refs, pid, birth, observed, exit);
        } catch (IllegalArgumentException | ArithmeticException | java.time.DateTimeException failure) {
            throw new IOException("Original finite-scope retirement DATA is invalid", failure);
        }
    }
    private static void need(boolean condition, String message) throws IOException {
        if (!condition) throw new IOException(message);
    }
    private static String text(JsonNode node) throws IOException {
        need(node != null && node.isTextual() && !node.textValue().isEmpty() && node.textValue().length() <= 32768,
                "Bounded exact text required");
        return node.textValue();
    }
    private static Path path(String raw) throws IOException {
        Path value = Path.of(raw);
        need(value.isAbsolute() && value.normalize().equals(value) && value.toString().equals(raw)
                && !raw.startsWith("\\?\\") && raw.indexOf('\0') < 0, "Ordinary normalized absolute path required");
        return value;
    }
    private static String decimal(JsonNode node, int bits, boolean positive) throws IOException {
        String value = text(node);
        need(value.matches(positive ? "[1-9][0-9]{0,19}" : "0|[1-9][0-9]{0,19}")
                && new BigInteger(value).bitLength() <= bits, "Canonical original unsigned decimal identity required");
        return value;
    }
    private static void shape(JsonNode node, Set<String> fields) throws IOException {
        need(node != null && node.isObject(), "Exact original object required");
        var found = new HashSet<String>(); node.fieldNames().forEachRemaining(found::add);
        need(found.equals(fields), "Original retirement field roster differs");
    }
}
