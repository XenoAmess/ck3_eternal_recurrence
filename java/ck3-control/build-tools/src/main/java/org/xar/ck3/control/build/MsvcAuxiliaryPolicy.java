package org.xar.ck3.control.build;

import com.sun.jna.Native;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.win32.W32APIOptions;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.function.LongSupplier;
import java.util.function.Supplier;

/** Explicit exact-MSVC cleanup policy. Only WindowsJobProcess supplies a production owned-Job backend. */
public final class MsvcAuxiliaryPolicy {
    public static final String SCHEMA = "xar.exact-msvc-owned-auxiliaries/v1";
    public static final int MAXIMUM_MEMBERS = 16;
    public static final int TERMINATION_EXIT_CODE = 74;
    private static final long MAXIMUM_IMAGE_BYTES = 64L << 20;
    private static final long GRACE_NANOS = 1_000_000_000L;
    private static final long CLEANUP_NANOS = 5_000_000_000L;
    private static final long IMAGE_SOURCE_GUARD_NANOS = 1_000_000_000L;
    private MsvcAuxiliaryPolicy() { }

    public enum Tool { VCTIP, MSPDBSRV }
    public enum State { NOT_ENTERED, NATURAL_DRAIN, FORCED_AUXILIARY_CLEANUP, FAILED }
    public record Termination(boolean acknowledged, Long win32Error, String error) {
        public Termination {
            if(win32Error!=null)dword(win32Error);
            if(error!=null&&error.length()>2048)throw new IllegalArgumentException("Bounded native termination diagnostic required");
            if(acknowledged?(win32Error!=null||error!=null):(error==null||error.isBlank()))
                throw new IllegalArgumentException("Actual termination ACK or explicit unknown submission required");
        }
    }
    public record Image(String canonicalPath, String volumeSerialDecimal, String fileIdDecimal, long bytes, String sha256) {
        public Image {
            if (canonicalPath == null || !Path.of(canonicalPath).isAbsolute()
                    || !Path.of(canonicalPath).normalize().toString().equals(canonicalPath) || bytes <= 0 || bytes > MAXIMUM_IMAGE_BYTES
                    || sha256 == null || !sha256.matches("[0-9a-f]{64}"))
                throw new IllegalArgumentException("Exact bounded canonical tool image required");
            decimal(volumeSerialDecimal, 64); decimal(fileIdDecimal, 128);
        }
    }
    public record Binding(String schema, Image compiler, Image vctip, Image mspdbsrv) {
        public Binding {
            if (!SCHEMA.equals(schema)) throw new IllegalArgumentException("Exact MSVC auxiliary binding schema required");
            Objects.requireNonNull(compiler); Objects.requireNonNull(vctip); Objects.requireNonNull(mspdbsrv);
            Path directory = Path.of(compiler.canonicalPath()).getParent();
            if (!Path.of(compiler.canonicalPath()).getFileName().toString().equalsIgnoreCase("cl.exe")
                    || !Path.of(vctip.canonicalPath()).getFileName().toString().equalsIgnoreCase("vctip.exe")
                    || !Path.of(mspdbsrv.canonicalPath()).getFileName().toString().equalsIgnoreCase("mspdbsrv.exe")
                    || !samePath(directory.toString(), Path.of(vctip.canonicalPath()).getParent().toString())
                    || !samePath(directory.toString(), Path.of(mspdbsrv.canonicalPath()).getParent().toString()))
                throw new IllegalArgumentException("Exact cl and both auxiliaries in one canonical compiler directory required");
        }
        Tool match(Image actual) throws IOException {
            boolean first = sameImage(vctip, actual), second = sameImage(mspdbsrv, actual);
            if (first == second) throw new IOException("Unknown or ambiguous exact owned auxiliary image");
            return first ? Tool.VCTIP : Tool.MSPDBSRV;
        }
        public void requireCompiler(ControlBuild.FileRef executable) throws IOException {
            if (!samePath(compiler.canonicalPath(), executable.path()) || compiler.bytes() != executable.bytes()
                    || !compiler.sha256().equals(executable.sha256()))
                throw new IOException("Auxiliary binding differs from exact admitted compiler executable");
        }
    }
    public record ExecutionBinding(String schema, Binding toolchain, ControlBuild.FileRef rootExecutable) {
        public ExecutionBinding {
            if(!"xar.exact-msvc-owned-execution/v1".equals(schema))throw new IllegalArgumentException("Exact MSVC execution binding schema required");
            Objects.requireNonNull(toolchain);Objects.requireNonNull(rootExecutable);
        }
        public void requireRequest(ControlBuild.FileRef executable,List<ControlBuild.FileRef> inputs)throws IOException {
            if(!sameRef(executable,rootExecutable))throw new IOException("Auxiliary execution root differs from exact admitted executable");
            Image compiler=toolchain.compiler();
            if(samePath(compiler.canonicalPath(),executable.path()))toolchain.requireCompiler(executable);
            else {
                boolean found=false;
                for(ControlBuild.FileRef input:inputs)if(samePath(compiler.canonicalPath(),input.path())) {
                    toolchain.requireCompiler(input);if(found)throw new IOException("Duplicate exact compiler input");found=true;
                }
                if(!found)throw new IOException("Noncompiler root opt-in requires the explicit exact cl input");
            }
        }
    }
    public record Root(WindowsJobProcess.ProcessIdentity identity, long waitZero, long exitCode) {
        public Root { Objects.requireNonNull(identity); dword(waitZero); dword(exitCode); }
    }
    public record MemberObservation(WindowsJobProcess.ProcessIdentity identity, Image image, boolean inOwnedJob, long waitZero) {
        public MemberObservation {
            Objects.requireNonNull(identity); Objects.requireNonNull(image); dword(waitZero);
            requireKernelImage(identity.executable(), image, "Same kernel image path and held file required");
        }
    }
    /** A request ACK and the independently observed termination/exit remain separate fields. */
    public record ForcedCleanup(Tool tool, WindowsJobProcess.ProcessIdentity identity, Image image,
            Termination termination, Long actualWaitZero, Long actualExitCode) {
        public ForcedCleanup {
            Objects.requireNonNull(tool); Objects.requireNonNull(identity); Objects.requireNonNull(image);Objects.requireNonNull(termination);
            requireKernelImage(identity.executable(), image, "Forced cleanup retains its exact process image");
            if (actualWaitZero != null) dword(actualWaitZero);
            if (actualExitCode != null) dword(actualExitCode);
            if (actualExitCode != null && (actualWaitZero == null || actualWaitZero != 0L))
                throw new IllegalArgumentException("Auxiliary exit code requires independent signalled handle");
        }
    }
    public record Outcome(String schema, State state, ExecutionBinding binding, Root originalRoot,
            List<ForcedCleanup> forcedCleanup, Integer ownedActiveAfter, boolean failureJobTerminationRequested, String error) {
        public Outcome {
            if (!"xar.exact-msvc-owned-auxiliary-outcome/v1".equals(schema))
                throw new IllegalArgumentException("Exact auxiliary outcome schema required");
            Objects.requireNonNull(state); Objects.requireNonNull(binding); forcedCleanup = List.copyOf(forcedCleanup);
            if (forcedCleanup.size() > MAXIMUM_MEMBERS || (ownedActiveAfter != null && ownedActiveAfter < 0)
                    || (error != null && (error.isBlank() || error.length() > 2048)))
                throw new IllegalArgumentException("Finite original auxiliary outcome required");
            if((state==State.NATURAL_DRAIN||state==State.FORCED_AUXILIARY_CLEANUP)&&originalRoot!=null
                    &&!samePath(originalRoot.identity().executable(),binding.rootExecutable().path()))
                throw new IllegalArgumentException("Original report root differs from bound compiler");
            if(forcedCleanup.stream().map(row->row.identity().pid()).distinct().count()!=forcedCleanup.size())
                throw new IllegalArgumentException("Each exact auxiliary mutation handle is recorded once");
            for(ForcedCleanup row:forcedCleanup)try {
                if(binding.toolchain().match(row.image())!=row.tool())throw new IllegalArgumentException("Auxiliary report tool differs from exact image binding");
            }catch(IOException invalidImage){throw new IllegalArgumentException("Unknown image cannot be a forced auxiliary report",invalidImage);}
            if (state == State.NATURAL_DRAIN || state == State.FORCED_AUXILIARY_CLEANUP) {
                if (originalRoot == null || originalRoot.waitZero() != 0 || originalRoot.exitCode() != 0
                        || ownedActiveAfter == null || ownedActiveAfter != 0 || error != null || failureJobTerminationRequested
                        || (state == State.NATURAL_DRAIN ? !forcedCleanup.isEmpty() : forcedCleanup.isEmpty())
                        || forcedCleanup.stream().anyMatch(row -> !row.termination().acknowledged()
                            || row.actualWaitZero() == null || row.actualWaitZero() != 0
                            || row.actualExitCode() == null || row.actualExitCode() != TERMINATION_EXIT_CODE))
                    throw new IllegalArgumentException("Successful policy requires actual root0, complete auxiliary terminals and Job0");
            } else if (error == null) throw new IllegalArgumentException("Explicit non-success reason required");
        }
        public boolean completed() { return state == State.NATURAL_DRAIN || state == State.FORCED_AUXILIARY_CLEANUP; }
        public Outcome withFailureTermination() {
            return new Outcome(schema, State.FAILED, binding, originalRoot, forcedCleanup, ownedActiveAfter, true,
                    error == null ? "Original owned Job required failure cleanup" : error);
        }
    }
    static Outcome notEntered(ExecutionBinding binding, String reason) {
        return outcome(State.NOT_ENTERED, binding, null, List.of(), null, reason);
    }
    private static Outcome outcome(State state, ExecutionBinding binding, Root root, List<ForcedCleanup> forced, Integer active, String error) {
        return new Outcome("xar.exact-msvc-owned-auxiliary-outcome/v1", state, binding, root, forced, active, false,
                error == null ? null : error.substring(0, Math.min(2048, error.length())));
    }

    interface Member extends AutoCloseable {
        MemberObservation observe() throws IOException;
        Termination terminate74() throws IOException;
        long waitZero() throws IOException;
        long exitCode() throws IOException;
        @Override void close() throws IOException;
    }
    interface Backend {
        Root root() throws IOException;
        int active() throws IOException;
        List<Long> members() throws IOException;
        Member retain(long pid) throws IOException;
    }
    @FunctionalInterface interface Sleep { void sleep(long milliseconds) throws InterruptedException; }
    static final class Budget {
        final long commandDeadline;
        long effectiveDeadline;
        final Instant leaseDeadline;
        final LongSupplier clock;
        final Supplier<Instant> utc;
        final Sleep sleep;
        Budget(long commandDeadline, Instant leaseDeadline) { this(commandDeadline, leaseDeadline, System::nanoTime, Instant::now, Thread::sleep); }
        Budget(long commandDeadline, Instant leaseDeadline, LongSupplier clock, Supplier<Instant> utc, Sleep sleep) {
            this.commandDeadline = commandDeadline; this.leaseDeadline = Objects.requireNonNull(leaseDeadline);
            this.effectiveDeadline = commandDeadline;
            this.clock = clock; this.utc = utc; this.sleep = sleep;
        }
        void check() throws IOException {
            if (clock.getAsLong() - effectiveDeadline >= 0 || !utc.get().isBefore(leaseDeadline))
                throw new IOException("Original command, lease or bounded auxiliary phase deadline exhausted");
            if (Thread.currentThread().isInterrupted()) throw new IOException("Auxiliary policy interrupted");
        }
        long until(long nanos) { return Math.min(effectiveDeadline, Math.addExact(clock.getAsLong(), nanos)); }
        void limitTo(long phaseDeadline) { effectiveDeadline=Math.min(effectiveDeadline,phaseDeadline); }
        void pause() throws IOException, InterruptedException {
            check(); long remaining = Math.min((effectiveDeadline - clock.getAsLong()) / 1_000_000L,
                    Duration.between(utc.get(), leaseDeadline).toMillis());
            if (remaining <= 0) throw new IOException("No original finite sleep budget remains");
            sleep.sleep(Math.min(50, remaining)); check();
        }
    }
    private record HeldMember(Member handle, MemberObservation original, Tool tool) { }

    /** Same finite reducer is used by the actual retained-Job backend and deterministic failure-path tests. */
    static Outcome finish(Backend backend, ExecutionBinding binding, Budget budget, Runnable guard) {
        Root root = null; Integer active = null; String failure = null; State state = State.FAILED;
        List<HeldMember> retained = new ArrayList<>(); List<ForcedCleanup> forced = new ArrayList<>();
        try {
            budget.check(); root = backend.root(); budget.check();
            if (root.waitZero() != 0 || root.exitCode() != 0) throw new IOException("Original retained root must be signalled with exit0");
            if (!samePath(root.identity().executable(), binding.rootExecutable().path())) throw new IOException("Original root image differs from bound executable");
            long graceEnd = budget.until(GRACE_NANOS);
            while ((active = backend.active()) != 0 && budget.clock.getAsLong() - graceEnd < 0) {
                budget.check(); guard.run(); budget.check(); budget.pause();
            }
            budget.check(); active = backend.active();
            if (active == 0) {
                if (!backend.members().isEmpty()) throw new IOException("Job0 accounting disagrees with complete owned member list");
                budget.check(); state = State.NATURAL_DRAIN;
            } else {
                List<Long> pids = completeMembers(backend.members()); budget.check();
                if (pids.isEmpty()) throw new IOException("Nonzero Job has an empty member list");
                // Every handle is retained and verified before the first mutation of even one member.
                for (long pid : pids) {
                    budget.check(); guard.run(); budget.check();
                    Member member = backend.retain(pid);
                    retained.add(new HeldMember(member, null, null));
                    MemberObservation observed = member.observe(); budget.check();
                    if (observed.identity().pid() != pid || !observed.inOwnedJob() || observed.waitZero() != 258)
                        throw new IOException("Owned member is not the original live enumerated generation");
                    Tool tool = binding.toolchain().match(observed.image());
                    retained.set(retained.size() - 1, new HeldMember(member, observed, tool));
                }
                // Complete source and handle verification uses the original command/lease budget.
                for (HeldMember held : retained) {
                    budget.check(); guard.run(); budget.check();
                    MemberObservation current = held.handle().observe(); budget.check();
                    if (!current.equals(held.original()) || !current.inOwnedJob() || current.waitZero() != 258)
                        throw new IOException("Retained member identity or membership changed before cleanup");
                }
                if (!new HashSet<>(pids).equals(new HashSet<>(completeMembers(backend.members()))))
                    throw new IOException("Owned member set changed before auxiliary cleanup");
                budget.check(); long cleanupEnd = budget.until(CLEANUP_NANOS);
                budget.limitTo(cleanupEnd);
                for (HeldMember held : retained) {
                    budget.check();
                    Termination submission=held.handle().terminate74();
                    forced.add(new ForcedCleanup(held.tool(), held.original().identity(), held.original().image(), submission, null, null));
                    if(!submission.acknowledged())throw new IOException("Exact auxiliary termination submission is unknown; no retry: "+submission.error());
                    budget.check();
                }
                while ((active = backend.active()) != 0 && budget.clock.getAsLong() - cleanupEnd < 0) {
                    // Every retained exact auxiliary has acknowledged termination. The
                    // five-second drain observes that original Job and those handles;
                    // repeating the complete source/output walk here can consume the
                    // phase before its terminal observations. The original command,
                    // lease and interruption budget still apply on every poll. Complete
                    // source/resource postchecks remain the caller's responsibility.
                    budget.check(); budget.pause();
                }
                budget.check(); active = backend.active();
                if (active != 0 || !backend.members().isEmpty()) throw new IOException("New or remaining owned member after exact auxiliary cleanup");
                for (int index = 0; index < retained.size(); index++) {
                    budget.check(); long wait = retained.get(index).handle().waitZero(); budget.check();
                    if (wait != 0) throw new IOException("Terminated auxiliary handle is not signalled");
                    long exit = retained.get(index).handle().exitCode(); budget.check();
                    ForcedCleanup original = forced.get(index);
                    forced.set(index, new ForcedCleanup(original.tool(), original.identity(), original.image(), original.termination(), wait, exit));
                    if (exit != TERMINATION_EXIT_CODE) throw new IOException("Auxiliary actual exit differs from requested74");
                }
                state = State.FORCED_AUXILIARY_CLEANUP;
            }
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt(); failure = interrupted.toString();
        } catch (IOException | RuntimeException rejected) { failure = rejected.toString(); }
        finally {
            for (HeldMember held : retained) try { held.handle().close(); }
            catch (IOException | RuntimeException closeFailure) {
                state = State.FAILED; failure = Objects.toString(failure, "") + "; retained handle close: " + closeFailure;
            }
        }
        if (failure != null) state = State.FAILED;
        return outcome(state, binding, root, forced, active, failure);
    }
    private static List<Long> completeMembers(List<Long> values) throws IOException {
        if (values.size() > MAXIMUM_MEMBERS || values.stream().anyMatch(pid -> pid == null || pid <= 0 || pid > 0xffff_ffffL)
                || new HashSet<>(values).size() != values.size()) throw new IOException("Incomplete, duplicate or oversized owned auxiliary set");
        return List.copyOf(values);
    }

    interface ImageApi extends Kernel32 { int GetFinalPathNameByHandleW(HANDLE file, char[] output, int count, int flags); }
    private static final class NativeFiles { static final ImageApi API = Native.load("kernel32", ImageApi.class, W32APIOptions.UNICODE_OPTIONS); }
    private record HeldImage(HANDLE handle, Image image) { }
    /** All three exact input handles disallow writes/replacement continuously before child creation through cleanup. */
    public static final class HeldBinding implements AutoCloseable {
        private final ExecutionBinding binding;
        private final List<HeldImage> images;
        private final long acquiredNanos = System.nanoTime();
        private boolean closed;
        private HeldBinding(ExecutionBinding binding, List<HeldImage> images) { this.binding = binding; this.images = List.copyOf(images); }
        public ExecutionBinding binding() { if (closed) throw new IllegalStateException("MSVC image leases closed"); return binding; }
        void requireBefore(long originalOwnerStarted) throws IOException {
            if (originalOwnerStarted - acquiredNanos < 0) throw new IOException("Continuous MSVC image leases must precede this original Job/process creation");
            verify();
        }
        public void verify() throws IOException {
            if (closed) throw new IOException("Original MSVC image leases are closed");
            for (HeldImage image : images) {
                var nativeFile = SharedSourceFiles.nativeHeldFile(image.handle());
                if (!nativeFile.volumeSerialDecimal().equals(image.image().volumeSerialDecimal())
                        || !nativeFile.fileIdDecimal().equals(image.image().fileIdDecimal()) || nativeFile.logicalBytes() != image.image().bytes())
                    throw new IOException("Held MSVC image identity changed");
            }
        }
        @Override public void close() throws IOException {
            if (closed) return; closed = true; IOException failure = null;
            for (HeldImage image : images) if (!NativeFiles.API.CloseHandle(image.handle())) {
                IOException next = nativeFailure("close held MSVC image");
                if (failure == null) failure = next; else failure.addSuppressed(next);
            }
            if (failure != null) throw failure;
        }
    }
    public static Binding bind(Path compiler, Instant deadline, Runnable guard) throws IOException {
        List<HeldImage> files = new ArrayList<>();
        try {
            HeldImage cl = openImage(compiler, deadline, guard); files.add(cl);
            Path directory = Path.of(cl.image().canonicalPath()).getParent();
            files.add(openImage(directory.resolve("vctip.exe"), deadline, guard));
            files.add(openImage(directory.resolve("mspdbsrv.exe"), deadline, guard));
            return new Binding(SCHEMA, files.get(0).image(), files.get(1).image(), files.get(2).image());
        } finally { closeImages(files); }
    }
    public static HeldBinding retain(ExecutionBinding binding, Instant deadline, Runnable guard) throws IOException {
        Objects.requireNonNull(binding); List<HeldImage> files = new ArrayList<>();
        try {
            for (Image expected : List.of(binding.toolchain().compiler(), binding.toolchain().vctip(), binding.toolchain().mspdbsrv())) {
                HeldImage actual = openImage(Path.of(expected.canonicalPath()), deadline, guard); files.add(actual);
                if (!sameImage(expected, actual.image())) throw new IOException("MSVC input path/FileID/SHA binding drift");
            }
            boolean rootHeld=files.stream().anyMatch(file->samePath(file.image().canonicalPath(),binding.rootExecutable().path()));
            if(!rootHeld)files.add(openImage(Path.of(binding.rootExecutable().path()),deadline,guard));
            HeldImage root=files.stream().filter(file->samePath(file.image().canonicalPath(),binding.rootExecutable().path())).findFirst().orElseThrow();
            if(root.image().bytes()!=binding.rootExecutable().bytes()||!root.image().sha256().equals(binding.rootExecutable().sha256()))
                throw new IOException("Continuously held root executable differs from exact execution pin");
            return new HeldBinding(binding, files);
        } catch (IOException | RuntimeException error) { try { closeImages(files); } catch (IOException close) { error.addSuppressed(close); } throw error; }
    }
    static Image observeImage(Path path, Instant deadline, Runnable guard) throws IOException {
        HeldImage held = openImage(path, deadline, guard);
        try { return held.image(); } finally { if (!NativeFiles.API.CloseHandle(held.handle())) throw nativeFailure("close observed image"); }
    }
    private static HeldImage openImage(Path path, Instant deadline, Runnable guard) throws IOException {
        checkDeadline(deadline); guard.run(); checkDeadline(deadline);
        long nextSourceGuard = System.nanoTime() + IMAGE_SOURCE_GUARD_NANOS;
        SharedSourceFiles.plainAncestors(path);
        HANDLE handle = NativeFiles.API.CreateFile(path.toString(), 0x80000080, 1, null, 3, 0x80, null);
        if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw nativeFailure("open exact tool image");
        try {
            var before = SharedSourceFiles.nativeHeldFile(handle);
            if (before.logicalBytes() <= 0 || before.logicalBytes() > MAXIMUM_IMAGE_BYTES) throw new IOException("Tool image exceeds64MiB");
            char[] full = new char[32768]; int length = NativeFiles.API.GetFinalPathNameByHandleW(handle, full, full.length, 0);
            if (length <= 0 || length >= full.length) throw nativeFailure("canonical held tool path");
            String canonical = new String(full, 0, length);
            if (canonical.startsWith("\\\\?\\UNC\\")) canonical = "\\\\" + canonical.substring(8);
            else if (canonical.startsWith("\\\\?\\")) canonical = canonical.substring(4);
            MessageDigest digest;
            try { digest = MessageDigest.getInstance("SHA-256"); }
            catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
            byte[] buffer = new byte[65536]; long total = 0;
            // Deadline/cancellation stay per chunk; complete source hashing follows elapsed time.
            while (true) {
                checkDeadline(deadline);
                if (System.nanoTime() - nextSourceGuard >= 0) {
                    guard.run(); checkDeadline(deadline);
                    nextSourceGuard = System.nanoTime() + IMAGE_SOURCE_GUARD_NANOS;
                }
                IntByReference received = new IntByReference();
                if (!NativeFiles.API.ReadFile(handle, buffer, buffer.length, received, null)) throw nativeFailure("held tool ReadFile");
                checkDeadline(deadline);
                int count = received.getValue(); if (count < 0 || count > buffer.length) throw new IOException("Invalid actual tool read count");
                if (count == 0) break; total = Math.addExact(total, count);
                if (total > MAXIMUM_IMAGE_BYTES) throw new IOException("Tool image read exceeds64MiB"); digest.update(buffer, 0, count);
            }
            var after = SharedSourceFiles.nativeHeldFile(handle); checkDeadline(deadline);
            if (!before.equals(after) || total != before.logicalBytes()) throw new IOException("Held tool metadata changed during exact digest");
            guard.run(); checkDeadline(deadline);
            return new HeldImage(handle, new Image(canonical, before.volumeSerialDecimal(), before.fileIdDecimal(), total,
                    HexFormat.of().formatHex(digest.digest())));
        } catch (IOException | RuntimeException error) { if (!NativeFiles.API.CloseHandle(handle)) error.addSuppressed(nativeFailure("close failed tool observation")); throw error; }
    }
    private static void closeImages(List<HeldImage> files) throws IOException {
        IOException failure = null;
        for (HeldImage file : files) if (!NativeFiles.API.CloseHandle(file.handle())) {
            IOException next = nativeFailure("close tool binding observation"); if (failure == null) failure = next; else failure.addSuppressed(next);
        }
        if (failure != null) throw failure;
    }
    private static boolean sameRef(ControlBuild.FileRef first,ControlBuild.FileRef second) {
        return samePath(first.path(),second.path())&&first.bytes()==second.bytes()&&first.sha256().equals(second.sha256());
    }
    static boolean sameImage(Image first, Image second) {
        return samePath(first.canonicalPath(), second.canonicalPath()) && first.volumeSerialDecimal().equals(second.volumeSerialDecimal())
                && first.fileIdDecimal().equals(second.fileIdDecimal()) && first.bytes() == second.bytes() && first.sha256().equals(second.sha256());
    }
    /** A kernel image may use its 8.3 spelling. Keep that original spelling and prove the held file instead. */
    private static void requireKernelImage(String kernelPath, Image image, String reason) {
        if (samePath(kernelPath, image.canonicalPath())) return;
        try {
            SharedSourceFiles.plainAncestors(Path.of(kernelPath));
            HANDLE handle = NativeFiles.API.CreateFile(kernelPath, 0x80, 1, null, 3, 0x80, null);
            if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw nativeFailure("open kernel image identity");
            try {
                var actual = SharedSourceFiles.nativeHeldFile(handle);
                char[] full = new char[32768];
                int length = NativeFiles.API.GetFinalPathNameByHandleW(handle, full, full.length, 0);
                if (length <= 0 || length >= full.length) throw nativeFailure("canonical kernel image identity");
                String canonical = new String(full, 0, length);
                if (canonical.startsWith("\\\\?\\UNC\\")) canonical = "\\\\" + canonical.substring(8);
                else if (canonical.startsWith("\\\\?\\")) canonical = canonical.substring(4);
                if (!samePath(canonical, image.canonicalPath())
                        || !actual.volumeSerialDecimal().equals(image.volumeSerialDecimal())
                        || !actual.fileIdDecimal().equals(image.fileIdDecimal()) || actual.logicalBytes() != image.bytes())
                    throw new IOException("Kernel image differs from the held canonical file identity");
            } finally {
                if (!NativeFiles.API.CloseHandle(handle)) throw nativeFailure("close kernel image identity");
            }
        } catch (IOException failure) { throw new IllegalArgumentException(reason, failure); }
    }
    static boolean samePath(String first, String second) { return Path.of(first).toAbsolutePath().normalize().toString().equalsIgnoreCase(Path.of(second).toAbsolutePath().normalize().toString()); }
    private static void decimal(String value, int bits) {
        if (value == null || !value.matches("0|[1-9][0-9]*") || new BigInteger(value).bitLength() > bits)
            throw new IllegalArgumentException("Canonical decimal native file identity required");
    }
    private static void dword(long value) { if (value < 0 || value > 0xffff_ffffL) throw new IllegalArgumentException("Unsigned DWORD required"); }
    private static void checkDeadline(Instant deadline) throws IOException {
        if (Thread.currentThread().isInterrupted()) throw new IOException("Original MSVC binding interrupted");
        if (deadline == null || !Instant.now().isBefore(deadline)) throw new IOException("Original MSVC binding deadline expired");
    }
    private static IOException nativeFailure(String operation) { return new IOException(operation + " Win32=" + Native.getLastError()); }

    /** Java metadata producer only; no compiler or process is started. */
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 4 || !arguments[0].equals("bind")) throw new IOException("bind ABSOLUTE_CL_PATH UTC_DEADLINE NEW_BINDING_JSON required");
        Binding binding = bind(Path.of(arguments[1]), Instant.parse(arguments[2]), () -> { });
        Path output = Path.of(arguments[3]); if (!output.isAbsolute()) throw new IOException("Absolute admitted binding output required");
        SharedSourceFiles.plainAncestors(output.getParent());
        byte[] bytes=ControlBuild.strictMapper().writeValueAsBytes(binding);
        if(bytes.length>65536)throw new IOException("Finite binding metadata exceeds64KiB");
        Files.write(output, bytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
    }
}
