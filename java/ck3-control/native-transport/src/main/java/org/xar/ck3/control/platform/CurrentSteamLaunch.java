package org.xar.ck3.control.platform;

import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/** Explicit single Saved launch in the user's unchanged current Steam mode, never an offline observation. */
public final class CurrentSteamLaunch {
    public static final String SCHEMA = "xar.current-steam-mode-saved-launch-authorization/v1";
    public static final int MAXIMUM_BYTES = 16384;
    private CurrentSteamLaunch() { }

    /** A bounded user declaration and original evidence references; this record is not a launch capability. */
    public record Authorization(String schema, String requestId, String sessionId, String machineId,
            long steamPid, String steamBirthFiletimeDecimal, ControlBuild.FileRef steamExecutable,
            ControlBuild.FileRef selectedSave, ControlBuild.FileRef userDirective,
            ControlBuild.FileRef accountSessionEvidence, String issuedAtUtc, String deadlineUtc) {
        public Authorization {
            Objects.requireNonNull(steamExecutable); Objects.requireNonNull(selectedSave);
            Objects.requireNonNull(userDirective); Objects.requireNonNull(accountSessionEvidence);
            if (!SCHEMA.equals(schema) || requestId == null || requestId.isBlank() || requestId.length() > 256
                    || sessionId == null || sessionId.isBlank() || sessionId.length() > 256
                    || machineId == null || machineId.isBlank() || machineId.length() > 256)
                throw new IllegalArgumentException("Explicit current-mode Saved authorization and exact identities required");
            new WindowsJobProcess.ProcessIdentity(steamPid, steamBirthFiletimeDecimal, steamExecutable.path());
            Instant issued = Instant.parse(issuedAtUtc), until = Instant.parse(deadlineUtc);
            if (!issued.isBefore(until) || Duration.between(issued, until).compareTo(Duration.ofMinutes(30)) > 0)
                throw new IllegalArgumentException("One finite current-mode authorization window of at most30minutes required");
        }

        /** Pure binding checks; no Steam observation, capability minting, process access, or mode change. */
        public void requireTarget(String request, String session, String machine,
                ControlBuild.FileRef steam, ControlBuild.FileRef save, Instant planDeadline, Instant now) throws IOException {
            Objects.requireNonNull(now);
            if (!requestId.equals(request) || !sessionId.equals(session) || !machineId.equals(machine)
                    || !steamExecutable.equals(steam) || !selectedSave.equals(save)
                    || !Instant.parse(deadlineUtc).equals(planDeadline)
                    || now.isBefore(Instant.parse(issuedAtUtc)) || !now.isBefore(Instant.parse(deadlineUtc)))
                throw new IOException("Current-mode authorization differs from exact request/session/machine/Steam/save/deadline or expired");
        }

        void requirePlan(NativeLaunchPlan plan, Instant now) throws IOException {
            if (!(plan.load() instanceof NativeLaunchPlan.SavedGame saved))
                throw new IOException("Explicit current-mode authorization is Saved-only");
            requireTarget(plan.requestId(), plan.sessionId(), plan.sources().review().machineId(),
                    plan.steam().steamExecutable(), saved.save(), plan.deadline(), now);
            if (!machineId.equals(plan.steam().machineId())) throw new IOException("Steam plan machine differs");
        }
    }

    public static ControlBuild.FileRef authorizationSource(Path path) throws IOException {
        byte[] raw = GameSupervisorControl.readBounded(path, MAXIMUM_BYTES);
        ControlBuild.FileRef ref = ControlBuild.FileRef.measure(path);
        if (raw.length != ref.bytes()) throw new IOException("Authorization changed while selecting its source");
        ref.verify();
        return ref;
    }

    public static Authorization readAuthorization(ControlBuild.FileRef source) throws IOException {
        if (source.bytes() < 1 || source.bytes() > MAXIMUM_BYTES) throw new IOException("Bounded authorization required");
        source.verify();
        byte[] raw = GameSupervisorControl.readBounded(Path.of(source.path()), MAXIMUM_BYTES);
        var body = StrictJson.parse(raw, MAXIMUM_BYTES);
        Authorization value = ControlBuild.strictMapper()
                .setPropertyNamingStrategy(com.fasterxml.jackson.databind.PropertyNamingStrategies.LOWER_CAMEL_CASE)
                .treeToValue(body, Authorization.class);
        source.verify();
        return value;
    }

    /** Only this live producer retains a genuine Steam process HANDLE and can create QualifiedCurrent. */
    static QualifiedCurrent observe(NativeLaunchPlan plan, ControlBuild.FileRef source) throws IOException {
        Authorization authorization = readAuthorization(source);
        authorization.requirePlan(plan, Instant.now());
        if (!authorization.machineId().equals(WindowsJobProcess.currentMachineId()))
            throw new IOException("Current-mode launch is on a different physical machine");
        for (Class<?> type : List.of(CurrentSteamLaunch.class, Authorization.class, QualifiedCurrent.class))
            plan.sources().requireLoadedClass(type);
        verifyEvidence(authorization);
        WindowsJobProcess.ReadOnlyProcessHandle steam = WindowsJobProcess.retainReadOnlyProcess(authorization.steamPid());
        try {
            var identity = steam.identity();
            if (identity.pid() != authorization.steamPid()
                    || !identity.creationFiletimeDecimal().equals(authorization.steamBirthFiletimeDecimal())
                    || !Path.of(identity.executable()).toRealPath().equals(Path.of(authorization.steamExecutable().path()).toRealPath())
                    || steam.waitZero() != 258L)
                throw new IOException("Actual current Steam process generation/image differs or exited");
            return new QualifiedCurrent(plan, authorization, source, steam, identity);
        } catch (IOException | RuntimeException failure) {
            try { steam.close(); } catch (RuntimeException cleanup) { failure.addSuppressed(cleanup); }
            throw failure;
        }
    }

    private static void verifyEvidence(Authorization value) throws IOException {
        value.userDirective().verify(); value.accountSessionEvidence().verify();
        value.steamExecutable().verify(); value.selectedSave().verify();
        if (value.userDirective().bytes() > 4096)
            throw new IOException("Finite original user directive required");
        String directive = Files.readString(Path.of(value.userDirective().path()), StandardCharsets.UTF_8).strip();
        if (!directive.equals("我要求你这次不进入离线，直接开启ck3"))
            throw new IOException("This explicit current-mode entry requires the original direct user instruction");
        // The referenced account/session observation is bounded evidence only, not global remote absence or online proof.
    }

    public static final class QualifiedCurrent implements AutoCloseable {
        private final NativeLaunchPlan plan;
        private final Authorization authorization;
        private final ControlBuild.FileRef source;
        private final WindowsJobProcess.ReadOnlyProcessHandle steam;
        private final WindowsJobProcess.ProcessIdentity identity;
        private final Instant observed = Instant.now();
        private final long observedNanos = System.nanoTime();
        private boolean consumed, closed;
        private QualifiedCurrent(NativeLaunchPlan plan, Authorization authorization, ControlBuild.FileRef source,
                WindowsJobProcess.ReadOnlyProcessHandle steam, WindowsJobProcess.ProcessIdentity identity) {
            this.plan=plan; this.authorization=authorization; this.source=source; this.steam=steam; this.identity=identity;
        }
        public synchronized void consumeBeforeGameCreate() throws IOException {
            if (consumed || closed) throw new IOException("Current-mode launch qualification already consumed/closed");
            consumed=true;
            Win32Host.deadline(plan.deadline());
            if (!Instant.now().isBefore(observed.plusSeconds(10)) || System.nanoTime()-observedNanos >= 10_000_000_000L)
                throw new IOException("Current Steam identity observation stale before CREATE");
            authorization.requirePlan(plan, Instant.now()); source.verify(); verifyEvidence(authorization);
            if (steam.waitZero()!=258L || !identity.equals(steam.identity()))
                throw new IOException("Held current Steam generation changed/exited before CREATE");
            var receipt=StrictJson.object().put("schema","xar.current-steam-mode-launch-consumed/v1")
                    .put("request_id",plan.requestId()).put("session_id",plan.sessionId())
                    .put("machine_id",authorization.machineId()).put("consumed_at_utc",Instant.now().toString())
                    .put("steam_mode","CURRENT_UNCHANGED_NOT_QUERIED")
                    .put("offline_qualification",false).put("remote_absence_or_online_proof",false);
            receipt.set("authorization",ControlBuild.strictMapper().valueToTree(source));
            receipt.set("steam_process",ControlBuild.strictMapper().valueToTree(identity));
            receipt.set("selected_save",ControlBuild.strictMapper().valueToTree(authorization.selectedSave()));
            Path file=plan.evidenceRoot().resolve("steam-current-mode-consumed.json");
            SharedSourceFiles.plainAncestors(file.getParent());
            byte[] raw=StrictJson.canonical(receipt,65536);
            Files.write(file,raw,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
            try(FileChannel channel=FileChannel.open(file,StandardOpenOption.WRITE)){channel.force(true);}
            if(!java.util.Arrays.equals(raw,Files.readAllBytes(file)))throw new IOException("Current-mode consumption readback differs");
        }
        @Override public synchronized void close() throws IOException {
            if(!closed){closed=true;steam.close();}
        }
    }
}
