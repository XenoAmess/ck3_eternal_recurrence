package org.xar.ck3.control.continuity.writer;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

final class HistoricalFinishPrimaryTest {
    @Test
    void preservesEscapingPrimaryAndFirstFailureAfterHostileCauseAccess(@TempDir Path temporary) throws Exception {
        Path root = temporary.resolve("writer").toAbsolutePath().normalize();
        assertTrue(root.startsWith(Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize()),
                "software fixture must remain inside the temporary directory");
        Files.createDirectory(root);
        String machine = "historical-finish-primary-software";
        ObjectNode initial = StrictJson.object().put("schema", "root.ck3.continuity-window/v1")
                .put("machine_id", machine).put("sequence", 0).put("window_id", 1)
                .put("start_date_raw", 1000).put("target_date_raw", 1024).put("target_days", 1)
                .put("status", "running").put("last_settled_cycles", 0).put("last_settled_date_raw", 1000);
        initial.putArray("unknown_requests").add("keep-exact");
        initial.put("NEXT", 73).putNull("pending_checkpoint");
        byte[] initialBytes = ContinuityJson.canonical(initial);
        Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json");
        Path anchor = root.resolve("anchor.json");
        Files.write(snapshot, initialBytes);
        Files.write(anchor, initialBytes);
        Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0]);
        Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        Path source = root.resolve("owned-source.txt");
        Files.writeString(source, "finite original software input");
        byte[] anchorBytes = Files.readAllBytes(anchor);
        ExactRef anchorRef = new ExactRef(anchor.toString(), anchorBytes.length,
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(anchorBytes)));
        byte[] sourceBytes = Files.readAllBytes(source);
        ExactRef sourceRef = new ExactRef(source.toString(), sourceBytes.length,
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(sourceBytes)));
        Layout layout = new Layout(snapshot, anchorRef, machine);
        ActionPorts.HistoricalReadLimits limits = new ActionPorts.HistoricalReadLimits(1, 1, 4);
        Throwable[] firstFailures = new Throwable[2];
        Throwable[] callbackFailures = new Throwable[2];
        Throwable[] causeFailures = new Throwable[2];
        Throwable[] escaped = new Throwable[2];
        Throwable[] sameSessionProblems = new Throwable[2];
        Throwable[] nextSessionProblems = new Throwable[2];
        boolean[] controlCompleted = new boolean[2];
        boolean[] nestedCallbackRan = new boolean[2];
        boolean[] sameSessionCompleted = new boolean[2];
        boolean[] nextSessionCompleted = new boolean[2];

        try (StorageWriteGuardTestSupport storage = StorageWriteGuardTestSupport.create(layout)) {
            ImmutableArtifactStore store = new ImmutableArtifactStore(
                    new ImmutableArtifactStore.Config(root.resolve("archive"), layout.lock(), 64L * 1024 * 1024), storage);
            ContinuityWriter writer = new ContinuityWriter(layout, List.of(sourceRef), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) {
                    throw new AssertionError("This fixture performs no Writer state transition");
                }
                @Override public ContinuityState reduce(ContinuityState before, Request request) {
                    throw new AssertionError("This fixture performs no Writer state transition");
                }
            }, Clock.fixed(Instant.parse("2023-01-01T00:00:00Z"), ZoneOffset.UTC),
                    new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
            NativeOutcomeArchive archive = new NativeOutcomeArchive(store, writer);

            for (int caseNumber = 0; caseNumber < 2; caseNumber++) {
                final int index = caseNumber;
                final boolean throwSelf = index == 1;
                final Error diagnostic = new Error("cause accessor diagnostic " + index);
                final Error original = new Error("callback primary " + index) {
                    private static final long serialVersionUID = 1L;
                    @Override public synchronized Throwable getCause() {
                        if (throwSelf) throw this;
                        throw diagnostic;
                    }
                };
                callbackFailures[index] = original;
                causeFailures[index] = diagnostic;

                writer.locked(session -> {
                    archive.inHistoricalReadScope(session, limits, unused -> {
                        controlCompleted[index] = true;
                        return null;
                    });
                    // This capture contains only the public target invocation, never an assertion.
                    try {
                        archive.inHistoricalReadScope(session, limits, borrowed -> {
                            try {
                                borrowed.inHistoricalReadScope(session, limits, inner -> {
                                    nestedCallbackRan[index] = true;
                                    return null;
                                });
                            } catch (IOException first) {
                                firstFailures[index] = first;
                            }
                            throw original;
                        });
                    } catch (Throwable actual) {
                        escaped[index] = actual;
                    }
                    // Use the original Archive after the callback-bound view has ended.
                    try {
                        archive.inHistoricalReadScope(session, limits, unused -> {
                            sameSessionCompleted[index] = true;
                            return null;
                        });
                    } catch (Throwable problem) {
                        sameSessionProblems[index] = problem;
                    }
                    return null;
                });
                try {
                    writer.locked(session -> {
                        archive.inHistoricalReadScope(session, limits, unused -> {
                            nextSessionCompleted[index] = true;
                            return null;
                        });
                        return null;
                    });
                } catch (Throwable problem) {
                    nextSessionProblems[index] = problem;
                }
            }
        }

        // Check all captured problems after both finite cases and real resource cleanup.
        // Fixed messages avoid asking the hostile Error for its cause while reporting failures.
        List<String> defects = new ArrayList<>();
        for (int index = 0; index < 2; index++) {
            String label = index == 0 ? "distinct diagnostic: " : "throw self: ";
            Throwable first = firstFailures[index];
            Throwable original = callbackFailures[index];
            Throwable diagnostic = causeFailures[index];
            if (!controlCompleted[index]) defects.add(label + "empty control scope did not complete");
            if (!(first instanceof IOException)) defects.add(label + "public nested rejection did not yield IOException F");
            if (nestedCallbackRan[index]) defects.add(label + "nested callback was reached");
            if (first == original || first == diagnostic || original == diagnostic)
                defects.add(label + "F/E/G object identities are not distinct");
            if (escaped[index] != original) defects.add(label + "the exact callback Error E was replaced");
            boolean firstSuppressed = false;
            for (Throwable suppressed : original.getSuppressed()) {
                if (first != null && suppressed == first) firstSuppressed = true;
            }
            if (!firstSuppressed) defects.add(label + "the exact recorded F was not retained as suppressed");
            if (!sameSessionCompleted[index] || sameSessionProblems[index] != null)
                defects.add(label + "same-Session empty scope did not recover cleanly");
            if (!nextSessionCompleted[index] || nextSessionProblems[index] != null)
                defects.add(label + "new-Session empty scope did not recover cleanly");
        }
        assertTrue(defects.isEmpty(), () -> String.join(System.lineSeparator(), defects));
    }
}
