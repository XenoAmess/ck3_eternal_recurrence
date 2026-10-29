package org.xar.ck3.control.platform;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.win32.StdCallLibrary;
import com.sun.jna.win32.W32APIOptions;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.platform.SteamOfflineObservation.Common;
import org.xar.ck3.control.platform.SteamOfflineObservation.Endpoint;
import org.xar.ck3.control.platform.SteamOfflineObservation.Method;
import org.xar.ck3.control.platform.SteamOfflineObservation.Offline;
import org.xar.ck3.control.platform.SteamOfflineObservation.Online;
import org.xar.ck3.control.platform.SteamOfflineObservation.Reason;
import org.xar.ck3.control.platform.SteamOfflineObservation.Result;
import org.xar.ck3.control.platform.SteamOfflineObservation.Source;
import org.xar.ck3.control.platform.SteamOfflineObservation.SteamProcess;
import org.xar.ck3.control.platform.SteamOfflineObservation.Unavailable;

/** Original CEF path: existing owned loopback debugger only, exact installed JS source, fixed getters. */
final class SteamOfflineCefProvider {
    static final String VERSION = "10.96.30.42";
    static final long SOURCE_BYTES = 14382868;
    static final String SOURCE_SHA256 = "f9606b111203c9140dcdd6fc016a0ee00e4c8406aeb786187c42873f08d071fb";
    private static final Pattern PORT = Pattern.compile("(?:^|\\s)--remote-debugging-port(?:=|\\s+)([0-9]{1,5})(?=\\s|$)");
    record Observation(Result result, Optional<SteamOfflineProbe.ObservationLease> lease) { }
    private record Row(long pid, long parent, String name) { }
    private record Listener(long pid, int port) { }
    private record Candidate(WindowsJobProcess.ProcessIdentity owner, int port) { }
    private record Getter(boolean offline, Candidate candidate, SteamOfflineCefWire.Target target) { }
    interface Kernel extends StdCallLibrary {
        HANDLE CreateToolhelp32Snapshot(int flags, int pid);
        boolean Process32FirstW(HANDLE snapshot, Win32Host.ProcessEntry entry);
        boolean Process32NextW(HANDLE snapshot, Win32Host.ProcessEntry entry);
        HANDLE OpenProcess(int rights, boolean inherit, int pid);
        boolean CloseHandle(HANDLE handle);
    }
    interface Nt extends StdCallLibrary {
        int NtQueryInformationProcess(HANDLE process, int kind, Pointer data, int size, IntByReference returned);
    }
    interface Ip extends StdCallLibrary {
        int GetExtendedTcpTable(Pointer data, IntByReference size, boolean order, int family, int table, int reserved);
    }
    private static final class Api {
        private static final Kernel KERNEL = Native.load("kernel32", Kernel.class, W32APIOptions.UNICODE_OPTIONS);
        private static final Nt NT = Native.load("ntdll", Nt.class);
        private static final Ip IP = Native.load("iphlpapi", Ip.class);
    }
    private SteamOfflineCefProvider() { }

    static Observation observe(SteamOfflineProbe.Plan plan, String nonce, String started, List<String> inheritedDiagnostics,
            Duration queryTimeout) {
        List<String> diagnostics = new ArrayList<>(inheritedDiagnostics);
        Optional<SteamProcess> steamData = Optional.empty(); Optional<Source> sourceData = Optional.empty();
        if (!System.getProperty("os.name", "").startsWith("Windows") || Native.POINTER_SIZE != 8) {
            return missing(plan, started, nonce, steamData, sourceData, diagnostics, Reason.UNSUPPORTED_PLATFORM);
        }
        try {
            Win32Host.deadline(plan.deadline());
            if (!plan.machineId().equals(WindowsJobProcess.currentMachineId())) throw new IOException("Steam observation machine differs");
            plan.steamExecutable().verify(); List<Win32Host.ProcessRow> steamRows = Win32Host.processes("steam.exe", plan.deadline());
            if (steamRows.isEmpty()) return missing(plan, started, nonce, steamData, sourceData, diagnostics, Reason.STEAM_NOT_FOUND);
            if (steamRows.size() != 1) return missing(plan, started, nonce, steamData, sourceData, diagnostics, Reason.AMBIGUOUS_STEAM);
            var steam = steamRows.get(0).identity(); String version = SteamOfflineProbe.version(Path.of(steam.executable()));
            steamData = Optional.of(SteamOfflineProbe.processIdentity(steam, version));
            if (!Path.of(steam.executable()).toRealPath().equals(Path.of(plan.steamExecutable().path()).toRealPath())) throw new IOException("Actual Steam executable differs");
            Path root = Path.of(steam.executable()).getParent(); Path source = root.resolve("steamui/chunk~2dcc5aaf7.js");
            if (!VERSION.equals(version)) {
                return missing(plan, started, nonce, steamData, sourceData, diagnostics, Reason.SOURCE_NOT_QUALIFIED);
            }
            final SharedSourceFiles.Witness witness;
            try {
                if (Files.size(source) != SOURCE_BYTES) return missing(plan, started, nonce, steamData, sourceData, diagnostics, Reason.SOURCE_NOT_QUALIFIED);
                witness = SharedSourceFiles.observe(source);
            } catch (IOException | RuntimeException failure) {
                diagnostics.add("cef_source_not_qualified");
                return missing(plan, started, nonce, steamData, sourceData, diagnostics, Reason.SOURCE_NOT_QUALIFIED);
            }
            if (witness.source().bytes() != SOURCE_BYTES || !witness.source().sha256().equals(SOURCE_SHA256)) {
                return missing(plan, started, nonce, steamData, sourceData, diagnostics, Reason.SOURCE_NOT_QUALIFIED);
            }
            Source sourceIdentity = SteamOfflineProbe.sourceIdentity(witness); sourceData = Optional.of(sourceIdentity);
            Map<Long, Row> rows = processes(plan.deadline()); Set<Long> descendants = descendants(rows, steam.pid());
            List<WindowsJobProcess.ProcessIdentity> helpers = new ArrayList<>();
            for (long pid : descendants.stream().sorted().toList()) {
                Row row = rows.get(pid); if (row == null || !row.name().equalsIgnoreCase("steamwebhelper.exe")) continue;
                try (Win32Host.ReadProcess helper = Win32Host.open(pid)) {
                    var identity = helper.identity();
                    if (!Path.of(identity.executable()).toRealPath().startsWith(root.toRealPath())
                            || !SteamOfflineProbe.version(Path.of(identity.executable())).equals(version)
                            || SteamOfflineObservation.decimal(identity.creationFiletimeDecimal(), 64)
                                .compareTo(SteamOfflineObservation.decimal(steam.creationFiletimeDecimal(), 64)) < 0) continue;
                    helpers.add(identity);
                } catch (IOException failure) { diagnostics.add("webhelper_identity_unavailable"); }
            }
            Set<Listener> listeners = listeners(plan.deadline()); List<Candidate> endpoints = new ArrayList<>(); boolean sawPort = false;
            for (var helper : helpers) {
                try {
                    List<Integer> ports = ports(helper.pid(), plan.deadline()); sawPort |= !ports.isEmpty();
                    for (int port : ports) if (listeners.contains(new Listener(helper.pid(), port))) endpoints.add(new Candidate(helper, port));
                } catch (IOException failure) { diagnostics.add("webhelper_commandline_unavailable"); }
            }
            diagnostics.add("checked_webhelpers=" + helpers.size()); diagnostics.add("owned_debugger_candidates=" + endpoints.size());
            if (endpoints.isEmpty()) {
                requireIdentity(steam);
                return missing(plan, started, nonce, steamData, sourceData, diagnostics, sawPort ? Reason.CDP_NOT_OWNED : Reason.CDP_NOT_ENABLED);
            }
            Instant networkDeadline = Instant.now().plus(queryTimeout);
            if (networkDeadline.isAfter(plan.deadline())) networkDeadline = plan.deadline();
            List<Getter> observations = new ArrayList<>();
            for (Candidate endpoint : endpoints.stream().limit(4).toList()) {
                if (!Instant.now().isBefore(networkDeadline)) break;
                try {
                    for (SteamOfflineCefWire.Target target : SteamOfflineCefWire.discover(endpoint.port(), networkDeadline).stream().limit(8).toList()) {
                        if (!Instant.now().isBefore(networkDeadline)) break;
                        boolean offline = SteamOfflineCefWire.evaluate(target, endpoint.port(), nonce, networkDeadline);
                        requireIdentity(endpoint.owner());
                        if (!listeners(plan.deadline()).contains(new Listener(endpoint.owner().pid(), endpoint.port()))) {
                            return missing(plan, started, nonce, steamData, sourceData, diagnostics, Reason.STEAM_INSTANCE_CHANGED);
                        }
                        observations.add(new Getter(offline, endpoint, target));
                    }
                } catch (IOException | IllegalArgumentException failure) { diagnostics.add("debugger_or_context_query_unavailable"); }
            }
            requireIdentity(steam); SharedSourceFiles.assertUnchanged(witness);
            if (!sourceIdentity.equals(SteamOfflineProbe.sourceIdentity(witness))) throw new IOException("Qualified CEF source identity changed");
            if (observations.isEmpty()) return missing(plan, started, nonce, steamData, sourceData, diagnostics, Reason.CONTEXT_UNAVAILABLE);
            boolean mode = observations.get(0).offline();
            if (observations.stream().anyMatch(value -> value.offline() != mode)) {
                return missing(plan, started, nonce, steamData, sourceData, diagnostics, Reason.INVALID_OBSERVATION);
            }
            Getter selected = observations.get(0); Candidate candidate = selected.candidate();
            Endpoint endpoint = new Endpoint(candidate.owner().pid(), candidate.owner().creationFiletimeDecimal(), candidate.port(), selected.target().id(), selected.target().url());
            Common common = new Common(plan.machineId(), started, nonce, steamData, sourceData, Optional.of(endpoint), diagnostics);
            Win32Host.ReadProcess heldSteam = Win32Host.open(steam.pid());
            try {
                Win32Host.ReadProcess heldHelper = Win32Host.open(candidate.owner().pid());
                var lease = new CefLease(plan, heldSteam, heldHelper, steam, candidate, witness, sourceIdentity);
                try { lease.verify(); return new Observation(mode ? new Offline(common, Method.CEF_APP_GETTERS, Optional.empty()) : new Online(common), Optional.of(lease)); }
                catch (IOException | RuntimeException failure) {
                    try { lease.close(); } catch (IOException cleanup) { failure.addSuppressed(cleanup); } throw failure;
                }
            } catch (IOException | RuntimeException failure) {
                try { heldSteam.close(); } catch (IOException cleanup) { failure.addSuppressed(cleanup); } throw failure;
            }
        } catch (IOException | RuntimeException failure) {
            diagnostics.add(SteamOfflineProbe.bounded("cef_provider_unavailable=" + failure));
            return missing(plan, started, nonce, steamData, sourceData, diagnostics, Reason.NATIVE_QUERY_FAILED);
        }
    }
    private static Observation missing(SteamOfflineProbe.Plan plan, String started, String nonce, Optional<SteamProcess> steam,
            Optional<Source> source, List<String> diagnostics, Reason reason) {
        return new Observation(new Unavailable(new Common(plan.machineId(), started, nonce, steam, source, Optional.empty(),
                diagnostics.stream().limit(256).toList()), reason), Optional.empty());
    }
    private static final class CefLease implements SteamOfflineProbe.ObservationLease {
        private final SteamOfflineProbe.Plan plan;
        private final Win32Host.ReadProcess steam, helper;
        private final WindowsJobProcess.ProcessIdentity steamIdentity;
        private final Candidate candidate;
        private final SharedSourceFiles.Witness source;
        private final Source sourceIdentity;
        private boolean closed;
        private CefLease(SteamOfflineProbe.Plan plan, Win32Host.ReadProcess steam, Win32Host.ReadProcess helper,
                WindowsJobProcess.ProcessIdentity steamIdentity, Candidate candidate, SharedSourceFiles.Witness source, Source sourceIdentity) {
            this.plan = plan; this.steam = steam; this.helper = helper; this.steamIdentity = steamIdentity;
            this.candidate = candidate; this.source = source; this.sourceIdentity = sourceIdentity;
        }
        @Override public void verify() throws IOException {
            Win32Host.deadline(plan.deadline());
            if (closed || !steamIdentity.equals(steam.identity()) || !candidate.owner().equals(helper.identity())
                    || !listeners(plan.deadline()).contains(new Listener(candidate.owner().pid(), candidate.port()))) {
                throw new IOException("Original Steam/CEF debugger ownership changed");
            }
            SharedSourceFiles.assertUnchanged(source);
            if (!sourceIdentity.equals(SteamOfflineProbe.sourceIdentity(source))) throw new IOException("Original CEF source stamp changed");
        }
        @Override public void close() throws IOException {
            if (closed) return; closed = true; IOException failed = null;
            try { helper.close(); } catch (IOException failure) { failed = failure; }
            try { steam.close(); } catch (IOException failure) { if (failed == null) failed = failure; else failed.addSuppressed(failure); }
            if (failed != null) throw failed;
        }
    }
    private static void requireIdentity(WindowsJobProcess.ProcessIdentity expected) throws IOException {
        try (Win32Host.ReadProcess process = Win32Host.open(expected.pid())) {
            if (!expected.equals(process.identity())) throw new IOException("Steam/CEF incarnation changed");
        }
    }
    private static Map<Long, Row> processes(Instant deadline) throws IOException {
        HANDLE snapshot = Api.KERNEL.CreateToolhelp32Snapshot(2, 0);
        if (snapshot == null || WinBase.INVALID_HANDLE_VALUE.equals(snapshot)) throw Win32Host.failure("CEF process snapshot");
        Map<Long, Row> result = new HashMap<>();
        try {
            Win32Host.ProcessEntry entry = new Win32Host.ProcessEntry(); boolean more = Api.KERNEL.Process32FirstW(snapshot, entry);
            while (more) {
                Win32Host.deadline(deadline); if (result.size() >= 32768) throw new IOException("Process snapshot limit exceeded");
                long pid = Integer.toUnsignedLong(entry.pid); result.put(pid, new Row(pid, Integer.toUnsignedLong(entry.parent), Native.toString(entry.exe)));
                more = Api.KERNEL.Process32NextW(snapshot, entry);
            }
            if (Native.getLastError() != 18) throw Win32Host.failure("Complete CEF process snapshot");
            return Map.copyOf(result);
        } finally { if (!Api.KERNEL.CloseHandle(snapshot)) throw Win32Host.failure("CEF process snapshot close"); }
    }
    private static Set<Long> descendants(Map<Long, Row> rows, long steam) {
        Set<Long> result = new HashSet<>(); result.add(steam);
        for (int depth = 0; depth < 32; depth++) {
            Set<Long> additions = new HashSet<>();
            for (Row row : rows.values()) if (result.contains(row.parent())) additions.add(row.pid());
            if (result.containsAll(additions)) break; result.addAll(additions);
        }
        return Set.copyOf(result);
    }
    static List<Integer> parsePorts(String command) {
        Matcher matches = PORT.matcher(command); Set<Integer> ports = new HashSet<>();
        while (matches.find()) { int port = Integer.parseInt(matches.group(1)); if (port >= 1 && port <= 65535) ports.add(port); }
        return ports.stream().sorted().toList();
    }
    private static List<Integer> ports(long pid, Instant deadline) throws IOException {
        Win32Host.deadline(deadline); HANDLE process = Api.KERNEL.OpenProcess(0x1000, false, (int) pid);
        if (process == null || WinBase.INVALID_HANDLE_VALUE.equals(process)) throw Win32Host.failure("CEF command-line query open");
        try {
            IntByReference size = new IntByReference(); Api.NT.NtQueryInformationProcess(process, 60, Pointer.NULL, 0, size);
            if (size.getValue() < 16 || size.getValue() > 65536) throw new IOException("Bounded CEF command-line size unavailable");
            try (Memory data = new Memory(size.getValue())) {
                if (Api.NT.NtQueryInformationProcess(process, 60, data, (int) data.size(), size) < 0) throw new IOException("CEF command-line query unavailable");
                int length = Short.toUnsignedInt(data.getShort(0)); Pointer value = data.getPointer(8);
                long start = Pointer.nativeValue(data), address = Pointer.nativeValue(value);
                if ((length & 1) != 0 || address < start || address > start + data.size() - length) throw new IOException("Invalid CEF command-line buffer");
                String command;
                try { command = StandardCharsets.UTF_16LE.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                        .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(value.getByteArray(0, length))).toString(); }
                catch (CharacterCodingException invalid) { throw new IOException("Invalid CEF command-line encoding", invalid); }
                Win32Host.deadline(deadline); return parsePorts(command);
            }
        } finally { if (!Api.KERNEL.CloseHandle(process)) throw Win32Host.failure("CEF command-line query close"); }
    }
    private static Set<Listener> listeners(Instant deadline) throws IOException {
        Win32Host.deadline(deadline); IntByReference size = new IntByReference(); Api.IP.GetExtendedTcpTable(Pointer.NULL, size, false, 2, 3, 0);
        if (size.getValue() < 4 || size.getValue() > 16 * 1024 * 1024) throw new IOException("Bounded TCP owner table unavailable");
        try (Memory data = new Memory(size.getValue())) {
            if (Api.IP.GetExtendedTcpTable(data, size, false, 2, 3, 0) != 0) throw new IOException("TCP owner table read unavailable");
            long count = Integer.toUnsignedLong(data.getInt(0));
            if (count > (data.size() - 4) / 24) throw new IOException("Invalid TCP owner table");
            Set<Listener> result = new HashSet<>();
            for (long index = 0; index < count; index++) {
                long offset = 4 + index * 24;
                if (data.getInt(offset) == 2 && data.getInt(offset + 4) == 0x0100007f) {
                    int port = Short.toUnsignedInt(Short.reverseBytes((short) data.getInt(offset + 8)));
                    if (port >= 1) result.add(new Listener(Integer.toUnsignedLong(data.getInt(offset + 20)), port));
                }
            }
            Win32Host.deadline(deadline); return Set.copyOf(result);
        }
    }
}
