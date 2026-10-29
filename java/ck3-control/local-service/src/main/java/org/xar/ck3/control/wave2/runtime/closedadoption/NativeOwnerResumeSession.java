package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.StrictJson;

/** Limited cold owner custody. Only the real retained Root writer handoff can create this resource. */
public final class NativeOwnerResumeSession implements AutoCloseable {
    public enum Phase { RESERVED, SUBMITTED, STARTED, UNKNOWN, CLOSED }
    public enum Reason { INDEPENDENT_MCP_STAGE_REQUIRED, ROOT_RESTORE_SCOPE_UNAVAILABLE, OWNER_ATTEMPT_CONSUMED, MCP_SPEC_REJECTED, OWNER_SUBMISSION_UNKNOWN }
    public sealed interface StartResult permits Started, Unavailable, Unknown { }
    public static final class Started implements StartResult {
        private final NativeOwnerResumeSession session;
        private Started(NativeOwnerResumeSession session) { this.session = Objects.requireNonNull(session); }
        public NativeOwnerResumeSession session() { return session; }
    }
    public record Unavailable(Reason reason, String detail,
            @com.fasterxml.jackson.annotation.JsonIgnore Optional<OriginalWriterTransaction.ColdStageNotSubmitted> cleanBeforeSubmission) implements StartResult {
        public Unavailable { Objects.requireNonNull(reason); detail = bounded(detail);Objects.requireNonNull(cleanBeforeSubmission); }
        public Unavailable(Reason reason,String detail) { this(reason,detail,Optional.empty()); }
    }
    /** Submission may have read or changed Driver state. The original attempt is never replayed. */
    public record Unknown(Reason reason, String detail, Optional<NativeOwnerResumeSession> retainedOwner) implements StartResult {
        public Unknown { Objects.requireNonNull(reason); detail = bounded(detail); Objects.requireNonNull(retainedOwner); }
        public boolean replayAllowed() { return false; }
    }
    /** Root-supplied work, invoked only with a private-minted session after original writer handoff exit0. */
    public interface Workflow {
        WindowsJobProcess.OwnedStdioSpec specification(ClosedInputsSessionAuthority.NativeRestoreInputs inputs)
                throws IOException, InterruptedException;
        void started(NativeOwnerResumeSession session) throws IOException, InterruptedException;
    }
    /** Original shared state, distinct from the new Prepared graph's runtime directory. Data only. */
    public record SharedStatePaths(Path stateRoot, Path profileRoot, Path saveDirectory,
            Path environmentManifest, ExactRef driver) { }
    public record SavedCheckpoint(String name, String loadSaveName, ExactRef save,
            long savedDateRaw, long historyIndex) { }
    private record RestoreTuple(SharedStatePaths paths, SavedCheckpoint checkpoint, SavedFrame frame, String lifecycle) { }
    @FunctionalInterface interface OwnerCreation<T> { T create() throws IOException, InterruptedException; }

    /** Stored by the original authority, not a process-wide cache or a deserializable permission. */
    static final class OwnerAttempt {
        private Phase phase = Phase.RESERVED;
        private Optional<WindowsJobProcess.OwnedStdio> actual = Optional.empty();
        private Optional<String> cleanupFailure = Optional.empty();
        private OwnerAttempt() { }
        void close() {
            if (phase == Phase.CLOSED) { return; }
            phase = Phase.CLOSED;
            actual.ifPresent(owner -> {
                try { owner.close(); }
                catch (RuntimeException failure) { cleanupFailure = Optional.of(bounded(failure.toString())); }
            });
        }
    }

    private final Thread thread = Thread.currentThread();
    private final ClosedInputsSessionAuthority authority;
    private final int preparedSequence;
    private final ClosedInputsSessionAuthority.NativeRestoreInputs inputs;
    private final OwnerAttempt attempt;
    private final WindowsJobProcess.OwnedStdio owner;
    private final WindowsJobProcess.ProcessIdentity identity;
    private final String nonce;

    private NativeOwnerResumeSession(ClosedInputsSessionAuthority authority, int preparedSequence,
            ClosedInputsSessionAuthority.NativeRestoreInputs inputs, OwnerAttempt attempt,
            WindowsJobProcess.OwnedStdio owner) {
        this.authority = authority; this.preparedSequence = preparedSequence; this.inputs = inputs;
        this.attempt = attempt; this.owner = owner; this.identity = owner.identity(); this.nonce = owner.sessionNonce();
    }

    /** Historical route retains its signature, but closed-read approval cannot create a side-effecting MCP owner. */
    public static StartResult startOwner(ClosedInputsSessionAuthority authority, int preparedSequence,
            WindowsJobProcess.OwnedStdioSpec requested) throws InterruptedException {
        Objects.requireNonNull(authority);Objects.requireNonNull(requested);
        return new Unavailable(Reason.INDEPENDENT_MCP_STAGE_REQUIRED,
                "same genuine RootColdResumeSession, actual saved Game/mod proof and independently reviewed MCP stage required before owner creation");
    }
    static StartResult startOwnerAfterStageReview(ClosedInputsSessionAuthority authority,int preparedSequence,
            WindowsJobProcess.OwnedStdioSpec requested,RootColdStageReview.Reviewed stage,ColdStageAttempts submissions) throws InterruptedException {
        StrictJson.require(stage.stage()==RootColdStageReview.Stage.MCP_OWNER
                && stage.command().command().equals(requested.command())
                && stage.command().executable().equals(new ExactRef(requested.executableRef().path(),requested.executableRef().bytes(),requested.executableRef().sha256()))
                && stage.command().immutableInputs().equals(requested.programSourceRefs().stream()
                    .map(ref->new ExactRef(ref.path(),ref.bytes(),ref.sha256())).toList()),"same independently reviewed concrete MCP invocation");
        return startOwnerUsing(authority,preparedSequence,requested,stage,submissions);
    }
    private static StartResult startOwnerUsing(ClosedInputsSessionAuthority authority,int preparedSequence,
            WindowsJobProcess.OwnedStdioSpec requested,RootColdStageReview.Reviewed reviewed,
            ColdStageAttempts submissions) throws InterruptedException {
        Objects.requireNonNull(authority); Objects.requireNonNull(requested);
        ClosedInputsSessionAuthority.NativeRestoreInputs inputs;
        try { inputs = authority.nativeRestoreInputs(preparedSequence); }
        catch (RuntimeException failure) { return unavailable(Reason.ROOT_RESTORE_SCOPE_UNAVAILABLE, failure); }
        try { validateMcpSpecification(inputs, requested, authority.deadline()); }
        catch (RuntimeException failure) { return unavailable(Reason.MCP_SPEC_REJECTED, failure); }
        OwnerAttempt attempt = new OwnerAttempt();
        try { authority.registerNativeOwnerAttempt(attempt); }
        catch (RuntimeException failure) { return unavailable(Reason.OWNER_ATTEMPT_CONSUMED, failure); }
        WindowsJobProcess.OwnedStdioSpec guarded = new WindowsJobProcess.OwnedStdioSpec(requested.command(), requested.consoleMode(),
                requested.executableRef(), requested.programSourceRefs(), requested.deadline(), requested.maxFrameBytes(),
                requested.maxSentBytes(), requested.maxReceivedBytes(), () -> {
                    authority.requireNativeOwnerInputs(preparedSequence);
                    requested.guard().verify();
                });
        try {
            OwnerCreation<WindowsJobProcess.OwnedStdio> actualCreation = () -> {
                // The original lock is held now. Mark before entering CREATE_SUSPENDED; any later failure is unknown.
                attempt.phase = Phase.SUBMITTED;
                WindowsJobProcess.OwnedStdio created = WindowsJobProcess.startOwnedStdio(guarded);
                attempt.actual = Optional.of(created);
                return created;
            };
            OwnerCreation<WindowsJobProcess.OwnedStdio> creation=() -> submissions.submit(
                    RootColdStageReview.Stage.MCP_OWNER,()->{},actualCreation::create);
            WindowsJobProcess.OwnedStdio actual=authority.withColdStageOwnerReadLock(preparedSequence,reviewed,guarded,creation);
            StrictJson.require(attempt.actual.isPresent() && actual == attempt.actual.orElseThrow(), "same actual owner from original writer lock");
            attempt.phase = Phase.STARTED;
            return new Started(new NativeOwnerResumeSession(authority, preparedSequence, inputs, attempt, actual));
        } catch (IOException | RuntimeException failure) {
            if(attempt.phase==Phase.RESERVED && failure instanceof OriginalWriterTransaction.ColdStageNotSubmitted clean) {
                authority.releaseNativeOwnerAttemptBeforeSubmission(attempt,clean);
                return new Unavailable(Reason.ROOT_RESTORE_SCOPE_UNAVAILABLE,failure.toString(),Optional.of(clean));
            }
            if (attempt.phase == Phase.RESERVED) { return unavailable(Reason.ROOT_RESTORE_SCOPE_UNAVAILABLE, failure); }
            attempt.phase = Phase.UNKNOWN;
            Optional<NativeOwnerResumeSession> retained = attempt.actual.map(actual ->
                    new NativeOwnerResumeSession(authority, preparedSequence, inputs, attempt, actual));
            return new Unknown(Reason.OWNER_SUBMISSION_UNKNOWN, failure.toString(), retained);
        } catch (InterruptedException failure) {
            if (attempt.phase != Phase.RESERVED) { attempt.phase = Phase.UNKNOWN; }
            Thread.currentThread().interrupt();
            throw failure;
        }
    }

    public ClosedInputsSessionAuthority.NativeRestoreInputs restoreInputs() throws IOException {
        requireBeforeHelloOrCapabilities(owner); return inputs;
    }
    public WindowsJobProcess.OwnedStdio ownedStdio() throws IOException {
        requireBeforeHelloOrCapabilities(owner); return owner;
    }
    public SharedStatePaths statePaths() throws IOException {
        requireBeforeHelloOrCapabilities(owner); return restoreTuple(inputs).paths();
    }
    public SavedCheckpoint checkpoint() throws IOException {
        requireBeforeHelloOrCapabilities(owner); return restoreTuple(inputs).checkpoint();
    }
    public SavedFrame savedFrame() throws IOException {
        requireBeforeHelloOrCapabilities(owner); return restoreTuple(inputs).frame();
    }
    public void requireBeforeHelloOrCapabilities(WindowsJobProcess.OwnedStdio actualOwner) throws IOException {
        if (Thread.currentThread() != thread || attempt.phase != Phase.STARTED || actualOwner != owner) {
            throw new IOException("same original live Root cold-owner session and actual retained owner required; no replay");
        }
        authority.requireNativeOwnerInputs(preparedSequence);
        if (!identity.equals(owner.identity()) || !nonce.equals(owner.sessionNonce())) {
            throw new IOException("original held MCP process generation or stdio session changed");
        }
        owner.verifyActualIdentityAndSources();
        // This scope permits the admitted cold bootstrap only. Actual saved-load/frame proof is still required before mutating CAP.
    }
    public Phase phase() { return attempt.phase; }
    public Optional<String> cleanupFailure() { return attempt.cleanupFailure; }
    public boolean grantsWarmAttachment() { return false; }
    public boolean replayAllowed() { return false; }
    @Override public void close() {
        if (Thread.currentThread() != thread) { throw new IllegalStateException("original Root owner thread required for close"); }
        attempt.close();
    }

    /** Transport binding to the actual Prepared quote and saved tuple, not authority minted from argv. */
    static void validateMcpSpecification(ClosedInputsSessionAuthority.NativeRestoreInputs inputs,
            WindowsJobProcess.OwnedStdioSpec spec, Instant deadline) {
        StrictJson.require(!spec.deadline().isAfter(deadline) && Instant.now().isBefore(spec.deadline()), "original earlier cold-owner deadline");
        RestoreTuple tuple = restoreTuple(inputs);
        Path state = tuple.paths().stateRoot();
        ExactRef driver = tuple.paths().driver(), save = tuple.checkpoint().save();
        String life = tuple.lifecycle();
        List<String> args = spec.command().arguments();
        StrictJson.require(!args.isEmpty() && Path.of(args.getFirst()).equals(Path.of(inputs.entrypoint().path())), "actual quoted deployed MCP entry, no caller-selected wrapper");
        Set<String> seen = new HashSet<>();
        boolean ordinaryFlag = false, readOnly = false;
        for (int index = 1; index < args.size(); index++) {
            String flag = args.get(index); StrictJson.require(seen.add(flag), "one original MCP option occurrence");
            if (flag.equals("--ordinary-campaign-no-pact")) { ordinaryFlag = true; continue; }
            if (flag.equals("--private-semantic-snapshot-readonly")) { readOnly = true; continue; }
            StrictJson.require(index + 1 < args.size(), "MCP option value required"); String value = args.get(++index);
            switch (flag) {
                case "--driver" -> StrictJson.require(value.equals("native-headless"), "original native driver only");
                case "--transport" -> StrictJson.require(value.equals("stdio"), "actual owned stdio only");
                case "--pipe-name" -> StrictJson.require(value.equals(inputs.pipeName()), "original pipe tuple");
                case "--state-dir" -> StrictJson.require(Path.of(value).equals(state), "original state tuple");
                case "--environment-manifest" -> StrictJson.require(Path.of(value).equals(tuple.paths().environmentManifest()), "original environment tuple");
                case "--succession-lifecycle" -> StrictJson.require(value.equals(life), "original lifecycle option");
                default -> throw new IllegalArgumentException("unsupported cold MCP option: " + flag);
            }
        }
        StrictJson.require(readOnly && ordinaryFlag == life.equals("ordinary_campaign_succession")
                && seen.containsAll(Set.of("--driver", "--transport", "--pipe-name", "--state-dir", "--environment-manifest", "--succession-lifecycle")),
                "complete original readonly MCP and lifecycle options");
        boolean entry = false, manifest = false;
        for (ControlBuild.FileRef source : spec.programSourceRefs()) {
            Path path = Path.of(source.path());
            StrictJson.require(!path.equals(Path.of(driver.path())) && !path.equals(Path.of(save.path()))
                    && !source.path().toLowerCase(java.util.Locale.ROOT).endsWith(".ck3")
                    && !source.path().toLowerCase(java.util.Locale.ROOT).endsWith(".sav"), "program/source pins cannot hash persistence bodies");
            if (path.equals(Path.of(inputs.entrypoint().path()))) {
                entry = source.bytes() == inputs.entrypoint().bytes() && source.sha256().equals(inputs.entrypoint().sha256());
            }
            if (path.equals(tuple.paths().environmentManifest())) { manifest = true; }
        }
        StrictJson.require(entry && manifest, "quoted entry and original environment manifest must be source-pinned; writer verifies approved closure membership");
    }

    private static RestoreTuple restoreTuple(ClosedInputsSessionAuthority.NativeRestoreInputs inputs) {
        JsonNode basis = StrictJson.parse(inputs.basis().bytes());
        SavedFrame frame = SavedFrame.fromJson(basis.get("frame"));
        var refs = SettledQueryClassifier.object(basis.get("refs"));
        ExactRef driver = ExactRef.fromJson(refs.get("driver")), save = ExactRef.fromJson(refs.get("save"));
        Path driverPath = Path.of(driver.path());
        StrictJson.require(driverPath.isAbsolute() && driverPath.getParent() != null && driverPath.getParent().getParent() != null,
                "qualified original shared-state Driver path");
        Path state = driverPath.getParent().getParent();
        StrictJson.require(Path.of(driver.path()).equals(state.resolve("native-session/driver-state.json"))
                && Path.of(save.path()).equals(state.resolve("profile/save games/xar_checkpoint.ck3")), "actual Prepared runtime preserves the qualified Driver/SAVE tuple");
        var checkpoint = StrictJson.object(basis.get("checkpoint"), Set.of("name", "load_save_name", "path", "size", "sha256",
                "saved_date_raw", "history_index", "succession_lifecycle"));
        StrictJson.require(StrictJson.text(checkpoint.get("name")).equals("xar_checkpoint.ck3")
                && StrictJson.text(checkpoint.get("load_save_name")).equals("xar_checkpoint")
                && StrictJson.text(checkpoint.get("path")).equals(save.path())
                && StrictJson.integer(checkpoint.get("size"), 1, StrictJson.MAX_SAFE_INTEGER) == save.bytes()
                && StrictJson.text(checkpoint.get("sha256")).equals(save.sha256()), "actual saved checkpoint anchor, no new-life default");
        var lifecycle = StrictJson.object(checkpoint.get("succession_lifecycle"), Set.of("schema", "lifecycle", "xar_enabled", "pact_contract", "source", "environment_sha256"));
        StrictJson.require(StrictJson.text(lifecycle.get("schema")).equals("xar.ck3.succession-lifecycle-binding/v1"), "original lifecycle binding schema");
        String life = StrictJson.text(lifecycle.get("lifecycle"));
        StrictJson.require(Set.of("rogue_one_life", "ordinary_campaign_succession").contains(life), "known original lifecycle, never legacy/unknown fallback");
        String source = StrictJson.text(lifecycle.get("source"));
        String pact = StrictJson.text(lifecycle.get("pact_contract"));
        JsonNode xar = lifecycle.get("xar_enabled");
        boolean verifiedAbsence = life.equals("ordinary_campaign_succession") && xar.isNull()
                && pact.equals("absent_by_verified_xar_mod_not_loaded") && source.equals(pact);
        boolean configured = xar.isTextual() && (life.equals("rogue_one_life")
                ? xar.textValue().equals("xar_on") && pact.equals("terminal_settlement_required")
                : xar.textValue().equals("xar_off") && pact.equals("absent_by_fresh_campaign_xar_off_contract"));
        StrictJson.require(verifiedAbsence || configured, "original complete lifecycle support profile, no boolean/default interpretation");
        StrictJson.require(StrictJson.text(lifecycle.get("environment_sha256")).matches("[0-9a-f]{64}"), "saved frozen environment binding required");
        long date = StrictJson.integer(checkpoint.get("saved_date_raw"),0,StrictJson.MAX_SAFE_INTEGER);
        long history = StrictJson.integer(checkpoint.get("history_index"),0,StrictJson.MAX_SAFE_INTEGER);
        StrictJson.require(date == frame.dateRaw(), "checkpoint and saved frame date agree");
        Path profile = state.resolve("profile");
        return new RestoreTuple(new SharedStatePaths(state,profile,profile.resolve("save games"),
                profile.resolve("xar-autoplayer-environment.json"),driver),
                new SavedCheckpoint("xar_checkpoint.ck3","xar_checkpoint",save,date,history),frame,life);
    }
    static SharedStatePaths sharedStatePaths(ClosedInputsSessionAuthority.NativeRestoreInputs inputs) {
        return restoreTuple(inputs).paths();
    }
    static SavedCheckpoint savedCheckpoint(ClosedInputsSessionAuthority.NativeRestoreInputs inputs) {
        return restoreTuple(inputs).checkpoint();
    }
    static SavedFrame savedFrame(ClosedInputsSessionAuthority.NativeRestoreInputs inputs) {
        return restoreTuple(inputs).frame();
    }
    private static Unavailable unavailable(Reason reason, Throwable error) { return new Unavailable(reason, error.toString()); }
    private static String bounded(String value) {
        Objects.requireNonNull(value); return value.substring(0, Math.min(value.length(), 2048));
    }
}
