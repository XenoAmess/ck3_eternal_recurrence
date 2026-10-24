package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.net.URI;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class ProjectStoragePolicyTest {
    @TempDir Path temporary;

    @Test void disabledMachinesKeepTheirExistingBehaviorWithoutResolvingOutput() throws IOException {
        var disabled = ProjectStoragePolicy.configuration(name -> null, name -> null);
        assertFalse(disabled.forbidSystemVolumeBulk());
        assertDoesNotThrow(() -> ProjectStoragePolicy.requireBulkOutput(disabled,
                Path.of("relative-and-nonexistent/output"), temporary.resolve("missing-system")));
        var explicitDisabled = ProjectStoragePolicy.configuration(
                Map.of(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK, "false")::get,
                Map.of(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK, "true",
                        ProjectStoragePolicy.PROJECT_STORAGE_ROOT, "relative-invalid-root")::get);
        assertEquals(disabled, explicitDisabled);
    }

    @Test void systemPropertyOverridesEnvironmentAndProjectRootPrecedesStateRoot() throws IOException {
        Path propertyRoot = temporary.resolve("property"), environmentRoot = temporary.resolve("environment");
        var configuration = ProjectStoragePolicy.configuration(
                Map.of(ProjectStoragePolicy.PROJECT_STORAGE_ROOT, propertyRoot.toString())::get,
                Map.of(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK, "true",
                        ProjectStoragePolicy.PROJECT_STORAGE_ROOT, environmentRoot.toString(),
                        ProjectStoragePolicy.AUTOPLAYER_STATE_DIR, temporary.resolve("state").toString())::get);
        assertTrue(configuration.forbidSystemVolumeBulk());
        assertEquals(Optional.of(propertyRoot), configuration.preferredBulkRoot());
        var fallback = ProjectStoragePolicy.configuration(name -> null,
                Map.of(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK, "true",
                        ProjectStoragePolicy.AUTOPLAYER_STATE_DIR, environmentRoot.toString())::get);
        assertEquals(Optional.of(environmentRoot), fallback.preferredBulkRoot());
    }

    @Test void malformedEnabledConfigurationCannotSilentlyDisableTheGuard() {
        for (String value : new String[]{"", "TRUE", "1", "yes"}) {
            assertThrows(IOException.class, () -> ProjectStoragePolicy.configuration(name -> null,
                    Map.of(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK, value)::get));
        }
        assertThrows(IOException.class, () -> ProjectStoragePolicy.configuration(name -> null,
                Map.of(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK, "true",
                        ProjectStoragePolicy.PROJECT_STORAGE_ROOT, "relative")::get));
    }

    @Test void explicitProcessConfigurationPrecedesGitLocalWithoutQueryingIt() throws IOException {
        var disabled = ProjectStoragePolicy.configuration(
                Map.of(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK, "false")::get,
                Map.of(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK, "true")::get,
                key -> { throw new IOException("explicit disabled setting must not query Git"); });
        assertFalse(disabled.forbidSystemVolumeBulk());
        Path root = temporary.resolve("environment-root");
        var enabled = ProjectStoragePolicy.configuration(name -> null,
                Map.of(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK, "true",
                        ProjectStoragePolicy.PROJECT_STORAGE_ROOT, root.toString())::get,
                key -> { throw new IOException("complete explicit settings must not query Git"); });
        assertTrue(enabled.forbidSystemVolumeBulk());
        assertEquals(Optional.of(root), enabled.preferredBulkRoot());
    }

    @Test void gitLocalFallbackValidatesValuesAndMissingSettingsKeepOldBehavior() throws IOException {
        Path root = temporary.resolve("git-root");
        var fallback = ProjectStoragePolicy.configuration(name -> null, name -> null,
                Map.of("xar.projectForbidSystemVolumeBulk", "true", "xar.projectStorageRoot", root.toString())::get);
        assertTrue(fallback.forbidSystemVolumeBulk());
        assertEquals(Optional.of(root), fallback.preferredBulkRoot());
        assertFalse(ProjectStoragePolicy.configuration(name -> null, name -> null, key -> null)
                .forbidSystemVolumeBulk());
        assertThrows(IOException.class, () -> ProjectStoragePolicy.configuration(name -> null, name -> null,
                Map.of("xar.projectForbidSystemVolumeBulk", "invalid")::get));
        assertThrows(IOException.class, () -> ProjectStoragePolicy.configuration(name -> null, name -> null,
                Map.of("xar.projectForbidSystemVolumeBulk", "true", "xar.projectStorageRoot", "relative")::get));
    }

    @Test void actualGitLocalQueryHandlesMissingRepositoryMissingKeyAndDuplicateValues() throws Exception {
        Path checkout = Files.createDirectory(temporary.resolve("checkout"));
        assertEquals(null, ProjectStoragePolicy.repositorySetting(checkout, "xar.projectForbidSystemVolumeBulk"));
        git(checkout, "init", "--quiet");
        assertEquals(null, ProjectStoragePolicy.repositorySetting(checkout, "xar.projectForbidSystemVolumeBulk"));
        git(checkout, "config", "--local", "xar.projectForbidSystemVolumeBulk", "true");
        assertEquals("true", ProjectStoragePolicy.repositorySetting(checkout, "xar.projectForbidSystemVolumeBulk"));
        git(checkout, "config", "--local", "--add", "xar.projectForbidSystemVolumeBulk", "false");
        assertThrows(IOException.class,
                () -> ProjectStoragePolicy.repositorySetting(checkout, "xar.projectForbidSystemVolumeBulk"));
    }

    private static void git(Path checkout, String... arguments) throws IOException, InterruptedException {
        var command = new java.util.ArrayList<String>();
        command.add("git"); command.addAll(java.util.List.of(arguments));
        Process child = new ProcessBuilder(command).directory(checkout.toFile()).redirectErrorStream(true).start();
        try {
            assertTrue(child.waitFor(5, TimeUnit.SECONDS), "bounded local Git fixture command");
            assertEquals(0, child.exitValue(), new String(child.getInputStream().readNBytes(8192),
                    java.nio.charset.StandardCharsets.UTF_8));
        } finally {
            if (child.isAlive()) child.destroyForcibly();
        }
    }

    @Test void rejectsExistingAndProspectiveSystemVolumeOutputsBeforeWriting() throws IOException {
        var enabled = new ProjectStoragePolicy.Configuration(true, Optional.of(temporary.resolve("preferred")));
        Path output = temporary.resolve("not-created/nested/output");
        IOException error = assertThrows(IOException.class,
                () -> ProjectStoragePolicy.requireBulkOutput(enabled, output, temporary));
        assertTrue(error.getMessage().contains("system volume is forbidden"));
        assertTrue(error.getMessage().contains("preferred"));
        assertFalse(Files.exists(output.getParent().getParent()));
        assertThrows(IOException.class,
                () -> ProjectStoragePolicy.requireBulkOutput(enabled, temporary, temporary));
    }

    @Test void virtualFilesystemCannotDisguiseItsBackingSystemVolume() throws IOException {
        Path archive = temporary.resolve("separate-filesystem.zip");
        try (var filesystem = FileSystems.newFileSystem(URI.create("jar:" + archive.toUri()), Map.of("create", "true"))) {
            Path output = filesystem.getPath("/not-created/nested/output");
            var enabled = new ProjectStoragePolicy.Configuration(true, Optional.empty());
            assertThrows(IOException.class, () -> ProjectStoragePolicy.requireBulkOutput(enabled, output, temporary));
            assertFalse(Files.exists(output.getParent()));
        }
    }

    @Test void nearestAncestorIsResolvedWithoutCreatingDirectories() throws IOException {
        Path parent = Files.createDirectory(temporary.resolve("existing"));
        assertEquals(parent.toRealPath(), ProjectStoragePolicy.nearestExistingAncestor(parent.resolve("future/leaf")));
        assertFalse(Files.exists(parent.resolve("future")));
        assertThrows(IOException.class, () -> ProjectStoragePolicy.nearestExistingAncestor(Path.of("relative")));
    }

    @Test void actualBuildEntryRejectsSystemVolumeBeforeNativeScratchOrLeaseAccess() {
        Path output = Path.of(Objects.requireNonNull(System.getenv("SystemRoot")))
                .getRoot().resolve("xar-storage-guard-must-not-create");
        String previous = System.getProperty(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK);
        try {
            System.setProperty(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK, "true");
            var config = new ControlBuild.Config(temporary, output, temporary.resolve("missing-release.json"),
                    "storage-guard", "test", null, temporary, "3.10.0", 60,
                    ControlBuild.TargetKind.SERVICE_FAST_JAR, ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
            IOException error = assertThrows(IOException.class, () -> ControlBuild.build(config));
            assertTrue(error.getMessage().contains("system volume is forbidden"));
            assertFalse(Files.exists(output));
        } finally {
            if (previous == null) System.clearProperty(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK);
            else System.setProperty(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK, previous);
        }
    }
}
