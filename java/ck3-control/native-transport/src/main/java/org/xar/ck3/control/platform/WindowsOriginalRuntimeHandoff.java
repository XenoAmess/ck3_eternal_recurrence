package org.xar.ck3.control.platform;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.platform.OriginalRuntimeHandoffProof.Reason;

/** Sole Windows issuer for an actually retained original owned Python producer. */
public final class WindowsOriginalRuntimeHandoff {
    private final WindowsJobProcess.OwnedStdio original;
    private final StoreKind storeKind;
    private enum StoreKind {
        RITE("rite-creation-actions"), RELIC("holy-site-relic-action-intents"),
        HOLY_CREATION("holy-site-creation-create-once-intents"), GRANT("grant-title-picker-actions");
        final String directory;
        StoreKind(String directory) { this.directory = directory; }
    }
    private WindowsOriginalRuntimeHandoff(WindowsJobProcess.OwnedStdio original, StoreKind storeKind) {
        this.original = original; this.storeKind = storeKind;
    }
    /** Only the actual launch producer can supply this original opaque object. */
    public static OriginalRuntimeHandoffProof.Provider originalOwnedLaunch(
            Optional<WindowsJobProcess.OwnedStdio> actualOriginal) {
        Objects.requireNonNull(actualOriginal);
        return actualOriginal.map(value -> OriginalRuntimeHandoffProof.bound(new WindowsOriginalRuntimeHandoff(value, StoreKind.RITE)))
                .orElseGet(OriginalRuntimeHandoffProof::unavailable);
    }
    /** Exact second finite old store; a Rite scope cannot authorize a Relic census. */
    public static OriginalRuntimeHandoffProof.Provider relicOriginalOwnedLaunch(
            Optional<WindowsJobProcess.OwnedStdio> actualOriginal) {
        Objects.requireNonNull(actualOriginal);
        return actualOriginal.map(value -> OriginalRuntimeHandoffProof.bound(
                new WindowsOriginalRuntimeHandoff(value, StoreKind.RELIC)))
                .orElseGet(OriginalRuntimeHandoffProof::unavailable);
    }
    /** Creation callback has its own cross-generation once store, independently source-bound. */
    public static OriginalRuntimeHandoffProof.Provider holyCreationOriginalOwnedLaunch(
            Optional<WindowsJobProcess.OwnedStdio> actualOriginal) {
        Objects.requireNonNull(actualOriginal);
        return actualOriginal.map(value -> OriginalRuntimeHandoffProof.bound(
                new WindowsOriginalRuntimeHandoff(value, StoreKind.HOLY_CREATION)))
                .orElseGet(OriginalRuntimeHandoffProof::unavailable);
    }
    /** Grant's original prepare/select/send once store is independently source-bound. */
    public static OriginalRuntimeHandoffProof.Provider grantOriginalOwnedLaunch(
            Optional<WindowsJobProcess.OwnedStdio> actualOriginal) {
        Objects.requireNonNull(actualOriginal);
        return actualOriginal.map(value -> OriginalRuntimeHandoffProof.bound(
                new WindowsOriginalRuntimeHandoff(value, StoreKind.GRANT)))
                .orElseGet(OriginalRuntimeHandoffProof::unavailable);
    }
    sealed interface Acquisition permits Held, Missing { }
    record Missing(Reason reason, String detail, List<ExactRef> evidence) implements Acquisition {
        Missing { evidence = List.copyOf(evidence); }
    }
    private record SourceRule(String relative, long bytes, String sha256) { }
    // Exact retained original producer contracts. New revisions require a new source cut.
    private static final List<SourceRule> ORIGINAL = List.of(
        new SourceRule("mcp_server.py", 356, "fc1d56d94501c4eed30efa2573c2b0d72152cf41604d9c9df68a572419ff5d32"),
        new SourceRule("src/xar_autoplayer/bridge/mcp_server.py", 283568, "b7569231226484b0bdd98c40ace14a82672b2138a0aab77711e559a4d9b8ccbc"),
        new SourceRule("src/xar_autoplayer/bridge/native_driver.py", 1658471, "eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"),
        new SourceRule("src/xar_autoplayer/bridge/rite_creation_action_private_v1.py", 28208, "1712e0de76e2975baa9e8185bf7ee7746c1b8697e2369349f5d807085a2c9f81"));
    private static final List<SourceRule> RELIC = List.of(
        ORIGINAL.get(0), ORIGINAL.get(1), ORIGINAL.get(2),
        new SourceRule("src/xar_autoplayer/bridge/relic_action_private_transport.py", 22414, "3eb97756cfb36629d2a71f89ae88105e809028ada0c01df9840f0594751db386"),
        new SourceRule("src/xar_autoplayer/bridge/title_map_navigation_contract.py", 22336, "e556fc2347c5fff4acbf4aedd2a09821a9f68a84ad0ac9adf2a1994cea6151d6"),
        new SourceRule("src/xar_autoplayer/bridge/version_identity.py", 2114, "9f7665ed680238f6904bc3ef22e1d67ef9b4ccd047e699542d5dbaff24b01086"),
        new SourceRule("src/xar_autoplayer/bridge/player_holy_site_relic_permissions_private_transport.py", 18559, "339f727311d7714b1fbad44ddbe5a6912c0fb9a89b1a310aa8c2f883ee6605f1"),
        new SourceRule("src/xar_autoplayer/bridge/driver.py", 20803, "eed449063debf1a84216a350f0178d64a9a6602bbfcc266298a810a9bb736fb6"),
        new SourceRule("src/xar_autoplayer/bridge/ingame_ui_contract.py", 44182, "74608d05074a48e1139a17fea360e34cf65cb01144d0a9a0e1dcf4ca49065ed4"),
        new SourceRule("src/xar_autoplayer/bridge/nonwar_private_build.py", 2663, "fe1a53ca0f01e60ae37231e3b1a566442454f3bb77afd33b616849b25f6d53e9"),
        new SourceRule("src/xar_autoplayer/bridge/player_holy_site_private_transport.py", 10830, "162e77f92086e57ee09fc152ec196edfa07f4a4f56fbdd3903c0297a8a8da299"));
    private static final List<SourceRule> HOLY_CREATION = holySources();
    private static final List<SourceRule> GRANT = List.of(
        ORIGINAL.get(0), ORIGINAL.get(1), ORIGINAL.get(2),
        new SourceRule("src/xar_autoplayer/bridge/grant_title_picker_v1.py", 14768, "4d1f7e4f7c1fcabaaa8cfaf8c7ac1592c072f989418da31b7bbaff3ea9e9bbb3"),
        new SourceRule("src/xar_autoplayer/bridge/ingame_decisions_open_contract.py", 5071, "86559e259b64c541909e75835f016822a8bb6fd7c4febb5a822f23fa1dad863d"),
        new SourceRule("src/xar_autoplayer/bridge/nonwar_private_build.py", 2663, "fe1a53ca0f01e60ae37231e3b1a566442454f3bb77afd33b616849b25f6d53e9"),
        new SourceRule("src/xar_autoplayer/bridge/version_identity.py", 2114, "9f7665ed680238f6904bc3ef22e1d67ef9b4ccd047e699542d5dbaff24b01086"),
        new SourceRule("src/xar_autoplayer/bridge/service.py", 897392, "a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e"),
        new SourceRule("src/xar_autoplayer/bridge/driver.py", 20803, "eed449063debf1a84216a350f0178d64a9a6602bbfcc266298a810a9bb736fb6"));
    private static List<SourceRule> holySources() {
        var rules = new ArrayList<>(RELIC);
        rules.addAll(List.of(
        new SourceRule("src/xar_autoplayer/bridge/holy_site_creation_create_once_private_transport.py", 13267, "b156b9795d31d5ef81cd4ede1bcadb879b8896e7cced982853301292f717e24c"),
        new SourceRule("src/xar_autoplayer/bridge/player_holy_site_creation_context_private_transport.py", 12714, "f4ea7b57d927077b71d334a74b7fbba189e2de87fb70b7809eb3369c91cd2db8")));
        return List.copyOf(rules);
    }
    private record Launch(Path store, List<ExactRef> evidence) { }
    private static Launch launch(WindowsJobProcess.OwnedStdioSpec spec, StoreKind kind) throws IOException {
        List<ExactRef> evidence = new ArrayList<>();
        evidence.add(exact(spec.executableRef()));
        for (ControlBuild.FileRef ref : spec.programSourceRefs()) evidence.add(exact(ref));
        return launch(spec.command().arguments(), spec.command().executable(), evidence, kind);
    }
    /** Pure original launch DATA check, shared with the strict archive decoder; never an issuer. */
    static Path originalStore(OriginalRuntimeHandoffObservation.Scope scope, List<String> args, Path executable, List<ExactRef> evidence) throws IOException {
        StoreKind kind = switch (scope) {
            case RELIC -> StoreKind.RELIC;
            case HOLY_CREATION -> StoreKind.HOLY_CREATION;
            case GRANT -> StoreKind.GRANT;
        };
        return launch(args, executable, evidence, kind).store();
    }
    private static Launch launch(List<String> args, Path executablePath, List<ExactRef> evidence,
            StoreKind kind) throws IOException {
        if (args.size() != 7 || !args.get(0).equals("-I") || !args.get(1).equals("-B")
                || !args.get(3).equals("--driver") || !args.get(4).equals("native-headless")
                || !args.get(5).equals("--state-dir"))
            throw new IOException("Unsupported original isolated explicit native-headless bootstrap");
        Path bootstrap = exactPath(args.get(2));
        if (!bootstrap.getFileName().toString().equals("mcp_server.py") || bootstrap.getParent() == null)
            throw new IOException("Original repository bootstrap is not exact");
        Path state = exactPath(args.get(6));
        String executable = executablePath.getFileName().toString();
        if (!executable.matches("(?i)python(?:[0-9]+(?:\\.[0-9]+)?)?\\.exe"))
            throw new IOException("Original command is not a direct pinned Python interpreter");
        if (evidence.isEmpty()) throw new IOException("Original executable source missing");
        List<ExactRef> program = evidence.subList(1, evidence.size());
        if (kind != StoreKind.RITE && (evidence.size() < 2 || evidence.size() > 256))
            throw new IOException("Complete bounded original source evidence required");
        List<SourceRule> required = switch (kind) {
            case RITE -> ORIGINAL;
            case RELIC -> RELIC;
            case HOLY_CREATION -> HOLY_CREATION;
            case GRANT -> GRANT;
        };
        for (SourceRule rule : required) {
            Path expected = bootstrap.getParent().resolve(rule.relative()).normalize();
            long matches = program.stream().filter(ref -> Path.of(ref.path()).toAbsolutePath().normalize().equals(expected)
                    && ref.bytes() == rule.bytes() && ref.sha256().equals(rule.sha256())).count();
            if (matches != 1) throw new IOException("Original actual launch lacks producer source: " + rule.relative());
        }
        if (program.stream().map(ref -> Path.of(ref.path()).toAbsolutePath().normalize()).distinct().count() != program.size())
            throw new IOException("Original launch repeats program source identities");
        if (evidence.isEmpty() || !Path.of(evidence.get(0).path()).equals(executablePath))
            throw new IOException("Original executable source differs from the actual launch");
        return new Launch(state.resolve("native-session").resolve(kind.directory), List.copyOf(evidence));
    }
    private static ExactRef exact(ControlBuild.FileRef ref) { return new ExactRef(ref.path(), ref.bytes(), ref.sha256()); }
    private static Path exactPath(String raw) throws IOException {
        Path path = Path.of(raw);
        if (!path.isAbsolute() || !path.normalize().equals(path) || !path.toString().equals(raw)
                || raw.startsWith("\\\\?\\") || raw.indexOf('\0') >= 0)
            throw new IOException("Ordinary normalized absolute original launch path required");
        return path;
    }
    Acquisition acquire(Path requestedStore, String requestedMachine) {
        Launch launch;
        try { launch = launch(original.spec(), storeKind); }
        catch (IOException | RuntimeException failure) {
            return missing(Reason.ORIGINAL_LAUNCH_UNSUPPORTED, failure, List.of());
        }
        if (!launch.store().equals(requestedStore)) return new Missing(Reason.ORIGINAL_STORE_OR_MACHINE_DIFFERS,
                "Requested store differs from original executed --state-dir/native-session/" + storeKind.directory, launch.evidence());
        WindowsJobProcess.RetiredCustody custody = null;
        try {
            custody = original.observeRetiredCustody();
            WindowsJobProcess.RetirementObservation observed = custody.observation();
            if (!observed.machineId().equals(requestedMachine)) {
                custody.close();
                return new Missing(Reason.ORIGINAL_STORE_OR_MACHINE_DIFFERS,
                        "Actual machine differs from original held OS process observation", launch.evidence());
            }
            // A reparse check is never treated as exclusive directory custody.
            SharedSourceFiles.plainAncestors(launch.store());
            Held held = new Held(custody, launch, observed, original.spec(), storeKind);
            held.requireCurrent();
            return held;
        } catch (IOException | RuntimeException failure) {
            if (custody != null) try { custody.close(); } catch (RuntimeException cleanup) { failure.addSuppressed(cleanup); }
            return missing(Reason.ORIGINAL_RETIREMENT_UNAVAILABLE, failure, launch.evidence());
        }
    }
    private static Missing missing(Reason reason, Exception failure, List<ExactRef> evidence) {
        String detail = failure.getClass().getSimpleName() + ": " + String.valueOf(failure.getMessage());
        return new Missing(reason, detail.substring(0, Math.min(detail.length(), 1024)), evidence);
    }
    private record ProcessData(String pidDecimal, String creationFiletimeDecimal, String executable,
            String sessionNonce, String observedAtUtc, String exitCodeDecimal, String activeProcessesDecimal,
            String memoryLimitBytesDecimal, String peakJobMemoryBytesDecimal, int limitFlags) { }
    private record Observation(String schema, String machineId, String scope, String originalStore,
            String originalCwd, List<String> originalArguments, List<ExactRef> originalSources, ProcessData retirement) { }
    /** Actual archived producer shared by Held and software DATA regressions; cannot issue custody. */
    static byte[] encodeObservation(Path store, List<ExactRef> evidence, Path cwd, List<String> arguments,
            WindowsJobProcess.RetirementObservation first) throws IOException {
        var identity = first.identity(); var counts = first.accounting();
        var process = new ProcessData(Long.toString(identity.pid()), identity.creationFiletimeDecimal(), identity.executable(),
                first.sessionNonce(), first.observedAtUtc(), Long.toString(first.exitCode()),
                Integer.toString(counts.activeProcesses()), Long.toString(counts.memoryLimitBytes()),
                Long.toString(counts.peakJobMemoryBytes()), counts.limitFlags());
        byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(new Observation(
                "xar.original-python-runtime-retirement/v1", first.machineId(), "ORIGINAL_OWNED_JOB_RETIRED",
                store.toString(), cwd.toString(), List.copyOf(arguments), List.copyOf(evidence), process));
        if (raw.length > (1 << 20)) throw new IOException("Original retirement observation exceeds finite archive limit");
        return raw;
    }
    static final class Held implements Acquisition, AutoCloseable {
        private final WindowsJobProcess.RetiredCustody custody;
        private final Launch launch;
        private final WindowsJobProcess.RetirementObservation first;
        private final byte[] observation;
        private Held(WindowsJobProcess.RetiredCustody custody, Launch launch,
                WindowsJobProcess.RetirementObservation first, WindowsJobProcess.OwnedStdioSpec spec, StoreKind kind) throws IOException {
            this.custody = custody; this.launch = launch; this.first = first;
            observation = encodeObservation(launch.store(), launch.evidence(), spec.command().cwd(),
                    spec.command().arguments(), first);
            if (kind != StoreKind.RITE) {
                var scope = switch (kind) {
                    case RELIC -> OriginalRuntimeHandoffObservation.Scope.RELIC;
                    case HOLY_CREATION -> OriginalRuntimeHandoffObservation.Scope.HOLY_CREATION;
                    case GRANT -> OriginalRuntimeHandoffObservation.Scope.GRANT;
                    case RITE -> throw new IOException("Rite uses its original archived DATA contract");
                };
                OriginalRuntimeHandoffObservation.decode(scope, observation, launch.store(), first.machineId(), launch.evidence());
            }
        }
        Path store() { return launch.store(); }
        String machine() { return first.machineId(); }
        List<ExactRef> evidence() { return launch.evidence(); }
        byte[] originalObservation() { return observation.clone(); }
        void requireCurrent() throws IOException {
            custody.requireCurrent();
            SharedSourceFiles.plainAncestors(launch.store());
            if (!WindowsJobProcess.currentMachineId().equals(first.machineId())) throw new IOException("Original machine identity drift");
        }
        @Override public void close() { custody.close(); }
    }
}
