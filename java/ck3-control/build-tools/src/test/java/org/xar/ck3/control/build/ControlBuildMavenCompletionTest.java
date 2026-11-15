package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Bounded completion arithmetic and mandatory evidence shape; no fixture grants a successful build. */
final class ControlBuildMavenCompletionTest {
    @TempDir Path temporary;

    @Test void exactMetadataFitsWhileTheMaximumEnvelopeFailsAndEachNewFileStillCostsACluster() throws Exception {
        var base = fixture("exact"); var accounting = ControlBuild.accountWorkpackage(base.config(), () -> {});
        var old = base.release().workpackageAccounting();
        var logical = new HashMap<>(old.logicalCapsByScope()); logical.put("logs", accounting.logicalBytesByScope().get("logs") + 1024);
        var nativeBytes = new HashMap<>(old.nativeCapsByScope()); nativeBytes.put("logs", accounting.nativeAllocatedBytesByScope().get("logs") + 8192);
        var authority = new ControlBuild.AttemptAccountingAuthority(old.schema(), old.attempt(), old.financialLayout(), old.financialSourceRef(), old.reservationSourceRefs(),
                old.measuredRoots(), logical, accounting.peakNewLogicalBytes() + 1024, nativeBytes, accounting.peakNewNativeAllocatedBytes() + 8192,
                old.canonicalM2GrowthReservationBytes());
        invoke("requirePendingAttemptExact", accounting, authority, 512, 4096L);
        IOException envelope = assertThrows(IOException.class, () -> invoke("requirePendingAttempt", accounting, authority, 2L << 20, null));
        for (String field : List.of("scope=logs", "logical_current=", "logical_pending=", "logical_cap=", "native_current=", "native_pending=", "native_cap=",
                "whole_logical_peak=", "whole_logical_pending=", "whole_logical_max=", "whole_native_peak=", "whole_native_pending=", "whole_native_max="))
            assertTrue(envelope.getMessage().contains(field), field);
        invoke("requirePendingAttempt", accounting, authority, 48, null);
        assertThrows(IOException.class, () -> invoke("requirePendingAttemptExact", accounting, authority, 48, 3L * 4096));
    }

    @Test void provenanceConsumerRejectsKnownOrZeroHistoricalPeakAndAnyHistoricalScopeForTheCurrentCensus() throws Exception {
        var fixture = fixture("unknown"); var accounting = ControlBuild.accountWorkpackage(fixture.config(), () -> {});
        var mapper = ControlBuild.strictMapper(); Path evidence = temporary.resolve("retained-input.json"); Files.writeString(evidence, "{}");
        var ref = ControlBuild.FileRef.measure(evidence); ObjectNode source = mapper.createObjectNode();
        source.put("schema", "xar.java-control.successful-maven-completion-source/v1").put("observed_at_utc", accounting.observedAtUtc())
                .put("historical_maven_filesystem_peak_state", "UNKNOWN_NOT_PERSISTED")
                .putNull("historical_maven_logical_filesystem_peak_bytes").putNull("historical_maven_native_filesystem_peak_bytes")
                .put("original_guard_policy_caps_semantics", "AUTHORITY_AND_SAMPLE_CHECK_LIMITS_NOT_PROVEN_HISTORICAL_UPPER")
                .put("completion_accounting_scope", "CURRENT_COMPLETION_PHASE_ONLY");
        for (String field : List.of("completion_authority_ref", "original_red_ref", "completed_receipt_ref", "accounting_ref", "original_capacity_release_ref")) source.set(field, mapper.valueToTree(ref));
        source.set("completion_producer_runtime_pins", mapper.valueToTree(List.of(ref)));
        source.set("original_guard_policy_caps", mapper.valueToTree(fixture.release().workpackageAccounting())); source.set("completion_census", mapper.valueToTree(accounting));
        for (String field : List.of("historical_maven_filesystem_peak_state", "historical_maven_logical_filesystem_peak_bytes", "historical_maven_native_filesystem_peak_bytes", "completion_accounting_scope")) {
            ObjectNode changed = source.deepCopy();
            if (field.endsWith("_bytes")) changed.put(field, 0); else changed.put(field, "ORIGINAL_MAVEN_WINDOW_MEASURED");
            Path path = temporary.resolve(field + ".json"); Files.write(path, mapper.writeValueAsBytes(changed));
            IOException rejected = assertThrows(IOException.class, () -> ControlBuild.verifyCompletionSource(ControlBuild.FileRef.measure(path)));
            assertTrue(rejected.getMessage().contains("UNKNOWN historical peak"), rejected.getMessage());
        }
    }

    @Test void publicCommandRejectsPartialCompletionAndCaptureReplayBeforeAnyNativeOrMavenWork() {
        String[] common = {"--source-root", temporary.toString(), "--work-root", temporary.toString(), "--capacity-release", temporary.resolve("release.json").toString(),
                "--attempt", "completion", "--owner-task", "fixture"};
        var partial = new java.util.ArrayList<>(List.of(common)); partial.addAll(List.of("--complete-from", temporary.resolve("red.json").toString()));
        assertThrows(IOException.class, () -> ControlBuild.parseArguments(partial.toArray(String[]::new)));
        partial.addAll(List.of("--completion-authority", temporary.resolve("authority.json").toString(), "--build-purpose", "TEST_COMPILED_CAPTURE_ONLY"));
        assertThrows(IOException.class, () -> ControlBuild.parseArguments(partial.toArray(String[]::new)));
    }

    @Test void correctedReaderAcceptsRetainedCreatorClosureAndRejectsUnpinnedOrChangedHistoricalBytes() throws Exception {
        Path creator = Files.createDirectory(temporary.resolve("historical-creator")); Path lib = Files.createDirectory(creator.resolve("lib"));
        Path archive = creator.resolve("completion-creator.jar"), dependency = lib.resolve("original-runtime.jar");
        for (Path file : List.of(archive, dependency)) {
            try (var jar = new java.util.jar.JarOutputStream(Files.newOutputStream(file))) {
                jar.putNextEntry(new java.util.jar.JarEntry("fixture.txt")); jar.write("historical opaque creator bytes".getBytes(java.nio.charset.StandardCharsets.UTF_8)); jar.closeEntry();
            }
        }
        var recorded = new java.util.ArrayList<>(List.of(ControlBuild.FileRef.measure(archive), ControlBuild.FileRef.measure(dependency)));
        recorded.sort(java.util.Comparator.comparing(ControlBuild.FileRef::path));
        assertNotEquals(archive.toUri(), ControlBuild.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        Method reader = ControlBuild.class.getDeclaredMethod("verifyHistoricalCompletionProducer", List.class); reader.setAccessible(true); reader.invoke(null, recorded);
        Path extra = lib.resolve("unrecorded.jar"); Files.writeString(extra, "unrecorded archive");
        assertThrows(InvocationTargetException.class, () -> reader.invoke(null, recorded)); Files.delete(extra);
        reader.invoke(null, recorded); Files.writeString(archive, "changed historical producer");
        var rejected = assertThrows(InvocationTargetException.class, () -> reader.invoke(null, recorded)); assertInstanceOf(IOException.class, rejected.getCause());
    }

    private ControlBuildAccountingTest.Fixture fixture(String attempt) throws Exception {
        var suite = new ControlBuildAccountingTest(); suite.temporary = temporary; return suite.fixture(attempt);
    }

    private static void invoke(String name, ControlBuild.WorkpackageAccounting accounting, ControlBuild.AttemptAccountingAuthority authority,
            long logicalBytes, Long nativeBytes) throws Exception {
        Method method = nativeBytes == null
                ? ControlBuild.class.getDeclaredMethod(name, ControlBuild.WorkpackageAccounting.class, ControlBuild.AttemptAccountingAuthority.class, String.class, long.class)
                : ControlBuild.class.getDeclaredMethod(name, ControlBuild.WorkpackageAccounting.class, ControlBuild.AttemptAccountingAuthority.class, String.class, long.class, long.class);
        method.setAccessible(true);
        try {
            if (nativeBytes == null) method.invoke(null, accounting, authority, "logs", logicalBytes);
            else method.invoke(null, accounting, authority, "logs", logicalBytes, nativeBytes.longValue());
        } catch (InvocationTargetException error) {
            if (error.getCause() instanceof Exception cause) throw cause;
            throw error;
        }
    }
}
