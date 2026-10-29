package org.xar.ck3.control.wave2.runtime.performancewindows;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Bounded read-only adapter for the four actual recipe paths. It does not qualify Windows file identity. */
public final class HistoricalPerformanceSourceReader {
    private HistoricalPerformanceSourceReader() { }

    /** Complete read-to-report path; the owning application supplies its already observed machine/time labels. */
    public static byte[] project(Path repositoryRoot, HistoricalPerformanceWindows.Context context) {
        Objects.requireNonNull(context, "context");
        return PerformanceWindowsCodec.encode(HistoricalPerformanceWindows.project(
                PerformanceWindowsCodec.decode(context, read(repositoryRoot))));
    }

    public static List<HistoricalPerformanceWindows.SourceInput> read(Path repositoryRoot) {
        Objects.requireNonNull(repositoryRoot, "repositoryRoot");
        try {
            Path root = repositoryRoot.toRealPath();
            Path evidence = root.resolve("docs/ck3-native-ai/evidence").toRealPath();
            StrictJson.require(evidence.startsWith(root), "sealed evidence path escapes selected repository");
            List<HistoricalPerformanceWindows.SourceInput> result = new ArrayList<>();
            for (HistoricalPerformanceWindows.SourceRole role : HistoricalPerformanceWindows.SourceRole.values()) {
                Path path = evidence.resolve(role.filename());
                BasicFileAttributes before = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
                StrictJson.require(before.isRegularFile() && !before.isSymbolicLink()
                        && before.size() > 0 && before.size() <= HistoricalPerformanceWindows.SOURCE_MAX_BYTES,
                        "bounded regular sealed source required");
                byte[] bytes;
                try (InputStream stream = Files.newInputStream(path)) {
                    bytes = stream.readNBytes(HistoricalPerformanceWindows.SOURCE_MAX_BYTES + 1);
                    BasicFileAttributes after = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
                    StrictJson.require(after.isRegularFile() && !after.isSymbolicLink()
                            && before.size() == after.size() && bytes.length == before.size()
                            && before.lastModifiedTime().equals(after.lastModifiedTime())
                            && Objects.equals(before.fileKey(), after.fileKey()), "sealed source changed during bounded read");
                }
                result.add(new HistoricalPerformanceWindows.SourceInput(role, bytes));
            }
            return List.copyOf(result);
        } catch (IOException error) { throw new ContractViolationException("cannot read all four sealed recipe sources", error); }
    }
}
