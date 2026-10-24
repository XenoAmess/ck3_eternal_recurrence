package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.DateTimeException;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.CompleteSourceGraph.SelectedFile;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Shared source-index wire only. No compilation, native admission, installed runtime or Game authority. */
public record SingleWinnerSourceIndex(String schema, String machineId, String owner, String observedAtUtc,
        String status, FileRef inputRef, boolean parentPomOrderOnlySupersedesInput02,
        List<SelectedFile> selectedFiles) {
    public static final String SCHEMA = "xar.java.single-winner-source-index/v1";
    public static final int MAX_BYTES = 8 << 20;
    public static final int MAX_FILES = 16384;

    public SingleWinnerSourceIndex {
        if (!SCHEMA.equals(schema) || !"/root/source_graph".equals(owner)
                || status == null || status.isBlank())
            throw new IllegalArgumentException("Exact source-index schema, machine, owner and nonempty status required");
        requireMachineId(machineId);
        utc(observedAtUtc);
        requireRef(inputRef, MAX_BYTES);
        selectedFiles = List.copyOf(selectedFiles);
        if (selectedFiles.isEmpty() || selectedFiles.size() > MAX_FILES)
            throw new IllegalArgumentException("Finite complete selected source index required");
        Set<String> folded = new HashSet<>();
        for (SelectedFile row : selectedFiles) {
            Objects.requireNonNull(row, "selected source");
            requireRef(row.sourceRef(), 64L << 20);
            if (!folded.add(row.targetRelative().toLowerCase(Locale.ROOT)))
                throw new IllegalArgumentException("Duplicate or case-aliased selected source target");
        }
    }

    /** Same closed eight-field wire for producer and SDK; unknown, missing and coercible fields fail. */
    public static SingleWinnerSourceIndex decode(byte[] bytes) throws IOException {
        if (bytes == null || bytes.length == 0 || bytes.length > MAX_BYTES)
            throw new IOException("Finite nonempty source index bytes required");
        return ControlBuild.strictMapper().readValue(bytes, SingleWinnerSourceIndex.class);
    }

    public byte[] encode() throws IOException {
        byte[] bytes = ControlBuild.strictMapper().writeValueAsBytes(this);
        if (bytes.length > MAX_BYTES || !equals(decode(bytes)))
            throw new IOException("Bounded source index strict serialization roundtrip differs");
        return bytes;
    }

    /** The data owner and original input grant no current-machine or runtime qualification by themselves. */
    public void validateFor(String currentMachine, Clock clock) throws IOException {
        Objects.requireNonNull(clock, "clock");
        if (!machineId.equals(currentMachine) || utc(observedAtUtc).isAfter(clock.instant()))
            throw new IOException("Current machine and nonfuture source-index observation required");
    }

    /** Existing SDK machine wire domain, shared by producer request/receipt and this index. */
    static void requireMachineId(String machineId) {
        if (machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{0,127}") || machineId.equals("unknown"))
            throw new IllegalArgumentException("Known source-index machine must use 1..128 lowercase letters, digits or hyphens and start with a letter or digit");
    }

    private static Instant utc(String text) {
        if (text == null || !text.endsWith("Z"))
            throw new IllegalArgumentException("UTC source-index observation required");
        try {
            Instant value = Instant.parse(text);
            if (!value.toString().equals(text))
                throw new IllegalArgumentException("Canonical UTC source-index observation required");
            return value;
        }
        catch (DateTimeException error) {
            throw new IllegalArgumentException("Valid UTC source-index observation required", error);
        }
    }

    private static void requireRef(FileRef ref, long maximum) {
        Objects.requireNonNull(ref, "exact source reference");
        if (!Path.of(ref.path()).isAbsolute() || ref.bytes() <= 0 || ref.bytes() > maximum)
            throw new IllegalArgumentException("Bounded positive absolute source reference required");
    }
}
