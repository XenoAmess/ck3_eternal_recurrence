package org.xar.ck3.control.platform;

import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.WinDef.HWND;
import com.sun.jna.win32.StdCallLibrary;
import com.sun.jna.win32.W32APIOptions;
import java.io.IOException;
import java.nio.file.InvalidPathException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.build.ProjectStoragePolicy;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Shared read-only launch policy. It creates no path, process, window or admission. */
public final class NativeLaunchPolicy {
    public static final String RETIRED_WINDOW_CLASS_PREFIX = "XARG2DecisionOverlay_";
    private static final int MAXIMUM_WINDOWS = 32768;

    private NativeLaunchPolicy() { }

    /** Validate the explicit inherited environment before accepting or serializing a launch body. */
    public static Map<String, String> requireEnvironment(Map<String, String> environment, String pipeName) {
        TreeMap<String, String> keys = windowsEnvironment(environment);
        String mode = keys.get("XAR_CK3_BRIDGE_MODE");
        if (mode != null && !mode.equals("native-headless")) {
            throw new IllegalArgumentException("Java Game launch requires the native-headless MCP backend");
        }
        String pipe = keys.get("XAR_CK3_BRIDGE_PIPE");
        if (pipe != null && !pipe.equals(pipeName)) {
            throw new IllegalArgumentException("Explicit Native pipe differs from the launch plan");
        }
        return Map.copyOf(environment);
    }

    private static TreeMap<String, String> windowsEnvironment(Map<String, String> environment) {
        Objects.requireNonNull(environment);
        TreeMap<String, String> keys = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        for (Map.Entry<String, String> entry : environment.entrySet()) {
            String key = Objects.requireNonNull(entry.getKey());
            String value = Objects.requireNonNull(entry.getValue());
            if (key.isBlank() || key.indexOf('=') >= 0 || key.indexOf('\0') >= 0
                    || value.indexOf('\0') >= 0 || keys.putIfAbsent(key, value) != null) {
                throw new IllegalArgumentException("One valid explicit Windows environment value per key required");
            }
        }
        return keys;
    }

    /** Called before lifecycle control writes and again by the actual prepared-profile consumer. */
    public static void requireCurrent(NativeLaunchPlan plan) throws IOException {
        Objects.requireNonNull(plan);
        plan.sources().requireLoadedClass(NativeLaunchPolicy.class);
        plan.sources().requireLoadedClass(ProjectStoragePolicy.class);
        requireOutputs(plan.profileDirectory(),plan.stateDirectory(),plan.evidenceRoot(),
                plan.preparedProfile().productionRoots(), plan.environment(),
                ProjectStoragePolicy.currentConfiguration().forbidSystemVolumeBulk(),
                ProjectStoragePolicy::requireBulkOutput);
        requireNoRetiredDecisionPanel(plan.deadline());
    }

    /** Reusable by the native recorder owner before it consumes a new take name. */
    public static void requireNoRetiredDecisionPanel(Instant deadline) throws IOException {
        requireNoRetiredDecisionPanel(deadline, NativeLaunchPolicy::windowClasses);
    }

    /** Guard the retained direct Root creator using its actual command, without inventing a state root. */
    public static void requireGameCommand(WindowsJobProcess.CommandSpec command, String pipeName,
            List<Path> additionalOutputs, Instant deadline) throws IOException {
        requireOutputLocations(gameOutputs(command, pipeName, additionalOutputs), command.environment(), deadline);
    }

    /** Explicit real session/output paths from a caller; this grants no source or execution authority. */
    public static void requireOutputLocations(List<Path> outputs, Map<String, String> environment, Instant deadline)
            throws IOException {
        requireDeadline(deadline);
        try { requireEnvironment(environment, windowsEnvironment(environment).get("XAR_CK3_BRIDGE_PIPE")); }
        catch (IllegalArgumentException invalid) { throw new IOException("Invalid actual launch process environment", invalid); }
        requireOutputPaths(outputs, environment, ProjectStoragePolicy.currentConfiguration().forbidSystemVolumeBulk(),
                ProjectStoragePolicy::requireBulkOutput);
        requireNoRetiredDecisionPanel(deadline);
    }

    static List<Path> gameOutputs(WindowsJobProcess.CommandSpec command, String pipeName,
            List<Path> additionalOutputs) throws IOException {
        Objects.requireNonNull(command); Objects.requireNonNull(additionalOutputs);
        try { requireEnvironment(command.environment(), pipeName); }
        catch (IllegalArgumentException invalid) { throw new IOException("Invalid actual Native Game environment", invalid); }
        TreeMap<String, String> environment = windowsEnvironment(command.environment());
        if (!"native-headless".equals(environment.get("XAR_CK3_BRIDGE_MODE"))
                || pipeName == null || !pipeName.equals(environment.get("XAR_CK3_BRIDGE_PIPE"))) {
            throw new IOException("Actual direct Game command requires its exact native-headless pipe");
        }
        Path profile = null;
        for (String argument : command.arguments()) {
            if (!argument.startsWith("-userdir=")) continue;
            if (profile != null) throw new IOException("One exact actual Game userdir argument required");
            try { profile = Path.of(argument.substring("-userdir=".length())); }
            catch (InvalidPathException invalid) { throw new IOException("Invalid actual Game userdir", invalid); }
        }
        if (profile == null || !profile.isAbsolute() || !profile.normalize().equals(profile)) {
            throw new IOException("Normalized absolute actual Game userdir argument required");
        }
        List<Path> outputs = new ArrayList<>();
        outputs.add(profile); outputs.add(command.stdout()); outputs.add(command.stderr());
        outputs.addAll(additionalOutputs);
        if (outputs.size() > 64) throw new IOException("Finite explicit Game output paths required");
        return List.copyOf(outputs);
    }

    @FunctionalInterface
    interface OutputCheck {
        void require(Path path) throws IOException;
    }

    /** The same finite path consumer is used in production and deterministic regressions. */
    static void requireOutputs(Path profile, Path state, Path evidence, Path production,
            Map<String, String> environment, boolean requireExplicitTemporaryPaths, OutputCheck outputCheck)
            throws IOException {
        requireOutputPaths(List.of(profile, state, evidence, production), environment,
                requireExplicitTemporaryPaths, outputCheck);
    }

    /** Actual explicit roots; vanilla contributes none and every mounted product remains checked. */
    static void requireOutputs(Path profile,Path state,Path evidence,List<Path> productions,
            Map<String,String> environment,boolean requireExplicitTemporaryPaths,OutputCheck outputCheck)throws IOException {
        if(productions.size()>128)throw new IOException("Finite complete explicit production roots required");
        var outputs=new ArrayList<Path>();outputs.add(profile);outputs.add(state);outputs.add(evidence);outputs.addAll(productions);
        for(int first=0;first<outputs.size();first+=64)
            requireOutputPaths(List.copyOf(outputs.subList(first,Math.min(first+64,outputs.size()))),environment,
                    requireExplicitTemporaryPaths,outputCheck);
    }

    private static void requireOutputPaths(List<Path> outputs, Map<String, String> environment,
            boolean requireExplicitTemporaryPaths, OutputCheck outputCheck) throws IOException {
        Objects.requireNonNull(outputCheck);
        if (outputs.isEmpty() || outputs.size() > 64) throw new IOException("Finite explicit launch output paths required");
        for (Path path : outputs) {
            if (!path.isAbsolute() || !path.normalize().equals(path)) {
                throw new IOException("Normalized absolute launch output path required");
            }
            outputCheck.require(path);
        }
        TreeMap<String, String> keys = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        keys.putAll(environment);
        for (String key : List.of("TEMP", "TMP")) {
            String raw = keys.get(key);
            if (raw == null && !requireExplicitTemporaryPaths) continue;
            if (raw == null || raw.isBlank()) {
                throw new IOException("Explicit project-scoped " + key + " required for the enabled storage policy");
            }
            try {
                Path temporary = Path.of(raw);
                if (!temporary.isAbsolute() || !temporary.normalize().equals(temporary)) {
                    throw new IOException("Normalized absolute project-scoped " + key + " required");
                }
                outputCheck.require(temporary);
            } catch (InvalidPathException invalid) {
                throw new IOException("Invalid project-scoped " + key, invalid);
            }
        }
    }

    @FunctionalInterface
    interface WindowClasses {
        List<String> read(Instant deadline) throws IOException;
    }

    /** Exact retired renderer fingerprint, including hidden windows; no title, OCR or focus access. */
    static void requireNoRetiredDecisionPanel(Instant deadline, WindowClasses windows) throws IOException {
        requireDeadline(deadline);
        List<String> classes = List.copyOf(windows.read(deadline));
        if (classes.size() > MAXIMUM_WINDOWS) throw new IOException("Window inventory exceeds finite limit");
        for (String value : classes) {
            if (isRetiredDecisionPanel(value)) {
                throw new IOException("Retired legacy blue decision panel is present: " + value
                        + "; its original owner must close it before launch");
            }
        }
        requireDeadline(deadline);
    }

    static boolean isRetiredDecisionPanel(String className) {
        Objects.requireNonNull(className);
        if (!className.startsWith(RETIRED_WINDOW_CLASS_PREFIX)) return false;
        String suffix = className.substring(RETIRED_WINDOW_CLASS_PREFIX.length());
        if (suffix.isEmpty()) return false;
        boolean positive = false;
        for (int index = 0; index < suffix.length(); index++) {
            char digit = suffix.charAt(index);
            if (digit < '0' || digit > '9') return false;
            positive |= digit != '0';
        }
        return positive;
    }

    interface WindowApi extends StdCallLibrary {
        interface WindowCallback extends StdCallCallback {
            boolean invoke(HWND window, Pointer parameter);
        }
        boolean EnumWindows(WindowCallback callback, Pointer parameter);
        int GetClassNameW(HWND window, char[] className, int maximum);
    }

    private static final class Holder {
        private static final WindowApi WINDOWS = Native.load("user32", WindowApi.class, W32APIOptions.UNICODE_OPTIONS);
    }

    private static List<String> windowClasses(Instant deadline) throws IOException {
        requireDeadline(deadline);
        if (!System.getProperty("os.name", "").startsWith("Windows")) {
            throw new IOException("Native Windows window inventory is required before Game launch");
        }
        List<String> result = new ArrayList<>();
        AtomicReference<IOException> failure = new AtomicReference<>();
        boolean complete = Holder.WINDOWS.EnumWindows((window, ignored) -> {
            try {
                requireDeadline(deadline);
                if (result.size() >= MAXIMUM_WINDOWS) throw new IOException("Window inventory exceeds finite limit");
                char[] name = new char[257];
                int length = Holder.WINDOWS.GetClassNameW(window, name, name.length);
                if (length <= 0 || length >= name.length - 1) {
                    throw new IOException("Exact current window class unavailable; Win32=" + Native.getLastError());
                }
                result.add(new String(name, 0, length));
                return true;
            } catch (IOException error) {
                failure.compareAndSet(null, error);
                return false;
            }
        }, Pointer.NULL);
        if (failure.get() != null) throw failure.get();
        if (!complete) throw new IOException("Current desktop window inventory failed; Win32=" + Native.getLastError());
        requireDeadline(deadline);
        return List.copyOf(result);
    }

    private static void requireDeadline(Instant deadline) throws IOException {
        if (deadline == null || !Instant.now().isBefore(deadline)) {
            throw new IOException("Launch policy observation deadline expired");
        }
    }
}

