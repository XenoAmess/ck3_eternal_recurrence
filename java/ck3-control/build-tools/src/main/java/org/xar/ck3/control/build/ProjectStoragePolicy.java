package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.FileSystems;
import java.nio.file.FileStore;
import java.nio.file.LinkOption;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Function;
import java.util.concurrent.TimeUnit;

/** Machine opt-in guard for new bulk outputs; it does not relocate existing evidence or input files. */
public final class ProjectStoragePolicy {
    public static final String FORBID_SYSTEM_VOLUME_BULK = "XAR_PROJECT_FORBID_SYSTEM_VOLUME_BULK";
    public static final String PROJECT_STORAGE_ROOT = "XAR_PROJECT_STORAGE_ROOT";
    public static final String AUTOPLAYER_STATE_DIR = "XAR_AUTOPLAYER_STATE_DIR";
    private static final String GIT_FORBID_SYSTEM_VOLUME_BULK = "xar.projectForbidSystemVolumeBulk";
    private static final String GIT_PROJECT_STORAGE_ROOT = "xar.projectStorageRoot";

    private ProjectStoragePolicy() {}

    public record Configuration(boolean forbidSystemVolumeBulk, Optional<Path> preferredBulkRoot) {
        public Configuration {
            Objects.requireNonNull(preferredBulkRoot);
            if (preferredBulkRoot.isPresent() && !preferredBulkRoot.orElseThrow().isAbsolute()) {
                throw new IllegalArgumentException("absolute project bulk storage root required");
            }
        }
    }

    /** JVM properties take precedence over process environment, then this checkout's Git-local settings. */
    public static Configuration currentConfiguration() throws IOException {
        Path checkout = Path.of(System.getProperty("user.dir")).toAbsolutePath().normalize();
        return configuration(System::getProperty, System::getenv, key -> repositorySetting(checkout, key));
    }

    static Configuration configuration(Function<String, String> property, Function<String, String> environment)
            throws IOException {
        return configuration(property, environment, key -> null);
    }

    @FunctionalInterface
    interface RepositorySetting {
        String read(String key) throws IOException;
    }

    static Configuration configuration(Function<String, String> property, Function<String, String> environment,
            RepositorySetting repository) throws IOException {
        String enabled = setting(FORBID_SYSTEM_VOLUME_BULK, property, environment);
        if (enabled == null) enabled = repository.read(GIT_FORBID_SYSTEM_VOLUME_BULK);
        if (enabled == null || enabled.equals("false")) return new Configuration(false, Optional.empty());
        if (!enabled.equals("true")) throw new IOException(FORBID_SYSTEM_VOLUME_BULK + " must be true or false");
        String root = setting(PROJECT_STORAGE_ROOT, property, environment);
        if (root == null) root = setting(AUTOPLAYER_STATE_DIR, property, environment);
        if (root == null) root = repository.read(GIT_PROJECT_STORAGE_ROOT);
        Optional<Path> preferred = Optional.empty();
        if (root != null) {
            try {
                Path path = Path.of(root);
                if (!path.isAbsolute()) throw new IOException("absolute " + PROJECT_STORAGE_ROOT + " required");
                preferred = Optional.of(path.normalize());
            } catch (java.nio.file.InvalidPathException error) {
                throw new IOException("invalid project bulk storage root", error);
            }
        }
        return new Configuration(true, preferred);
    }

    /** Read the common local configuration of this ordinary or linked worktree, without a shell. */
    static String repositorySetting(Path checkout, String key) throws IOException {
        if (!repositoryMarkerPresent(checkout)) return null;
        Process child = new ProcessBuilder("git", "config", "--local", "--null", "--get-all", key)
                .directory(checkout.toFile()).redirectErrorStream(true).start();
        try {
            if (!child.waitFor(5, TimeUnit.SECONDS)) throw new IOException("project Git-local storage query timed out");
            byte[] raw = child.getInputStream().readNBytes(8193);
            if (raw.length > 8192) throw new IOException("project Git-local storage value exceeds its limit");
            if (child.exitValue() == 1 && raw.length == 0) return null;
            if (child.exitValue() != 0) throw new IOException("project Git-local storage query failed: " + key);
            String value = StandardCharsets.UTF_8.newDecoder().decode(ByteBuffer.wrap(raw)).toString();
            if (!value.endsWith("\0") || value.indexOf('\0') != value.length() - 1) {
                throw new IOException("one exact Git-local storage value required: " + key);
            }
            return value.substring(0, value.length() - 1);
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            throw new IOException("project Git-local storage query interrupted", error);
        } finally {
            if (child.isAlive()) child.destroyForcibly();
        }
    }

    private static boolean repositoryMarkerPresent(Path checkout) throws IOException {
        for (Path ancestor = checkout; ancestor != null; ancestor = ancestor.getParent()) {
            try {
                Files.readAttributes(ancestor.resolve(".git"), BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
                return true;
            } catch (NoSuchFileException error) {
                // A checkout is optional; other I/O failures must not silently disable a configured guard.
            }
        }
        return false;
    }

    private static String setting(String name, Function<String, String> property,
            Function<String, String> environment) {
        String value = property.apply(name);
        return value == null ? environment.apply(name) : value;
    }

    /** Checks before directory creation; existing inputs, installed tools and small metadata are unaffected. */
    public static void requireBulkOutput(Path output) throws IOException {
        Configuration configuration = currentConfiguration();
        if (!configuration.forbidSystemVolumeBulk()) return;
        String systemRoot = System.getenv("SystemRoot");
        if (systemRoot == null || systemRoot.isBlank()) {
            throw new IOException("current SystemRoot is required for the enabled project storage guard");
        }
        requireBulkOutput(configuration, output, Path.of(systemRoot));
    }

    static void requireBulkOutput(Configuration configuration, Path output, Path systemDirectory)
            throws IOException {
        if (!configuration.forbidSystemVolumeBulk()) return;
        Path existing = nearestExistingAncestor(output);
        FileStore destinationVolume = Files.getFileStore(existing);
        FileStore systemVolume = Files.getFileStore(systemDirectory.toRealPath());
        if (destinationVolume.equals(systemVolume)
                || (System.getProperty("os.name").startsWith("Windows")
                    && volumeSerial(destinationVolume) == volumeSerial(systemVolume))) {
            String destination = configuration.preferredBulkRoot().map(Path::toString)
                    .orElse("a non-system-volume " + PROJECT_STORAGE_ROOT + " or " + AUTOPLAYER_STATE_DIR);
            throw new IOException("project bulk output on the system volume is forbidden: " + output
                    + " (physical ancestor " + existing + "); select an output under " + destination);
        }
    }

    private static int volumeSerial(FileStore volume) throws IOException {
        // The Windows JDK exposes the native DWORD through this filesystem-specific attribute.
        // Validate the dynamic boundary and reject unavailable identity instead of trusting a drive letter.
        try {
            Object attribute = volume.getAttribute("volume:vsn");
            if (attribute instanceof Integer serial) return serial;
            throw new IOException("exact native volume serial required for the project storage guard");
        } catch (UnsupportedOperationException error) {
            throw new IOException("native volume identity unavailable for the project storage guard", error);
        }
    }

    /** Resolves junctions even when the requested leaf and several of its parents do not yet exist. */
    static Path nearestExistingAncestor(Path output) throws IOException {
        Objects.requireNonNull(output);
        if (!output.isAbsolute()) throw new IOException("absolute project bulk output required");
        if (output.getFileSystem() != FileSystems.getDefault()) {
            throw new IOException("native filesystem project bulk output required");
        }
        Path ancestor = output.normalize();
        while (ancestor != null) {
            try {
                Files.readAttributes(ancestor, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
                return ancestor.toRealPath();
            } catch (NoSuchFileException error) {
                ancestor = ancestor.getParent();
            }
        }
        throw new IOException("no existing ancestor for project bulk output: " + output);
    }

    /** Read-only operational probe, also runnable directly with the installed JDK's source launcher. */
    public static void main(String[] arguments) throws IOException {
        if (arguments.length != 2 || !arguments[0].equals("--check-bulk-output")) {
            throw new IllegalArgumentException("usage: --check-bulk-output <absolute-output-path>");
        }
        Path output = Path.of(arguments[1]);
        requireBulkOutput(output);
        System.out.println("Project bulk output permitted: " + output);
    }
}
