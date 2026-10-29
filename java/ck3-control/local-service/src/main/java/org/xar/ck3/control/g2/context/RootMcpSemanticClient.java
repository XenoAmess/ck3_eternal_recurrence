package org.xar.ck3.control.g2.context;

import java.io.IOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Real Job-owned MCP transport. Native completion additionally consumes the sole concrete preload authority's opaque admission. */
public final class RootMcpSemanticClient {
    private RootMcpSemanticClient() { }
    public enum Reason { SOURCE_UNBOUND, ACCEPTED_NATIVE_RUNTIME_UNAVAILABLE, SOURCE_REJECTED, ADMISSION_UNAVAILABLE, CLOSED }
    /** Ordinary Root-selected pins. Neither this record nor real owned stdio authorizes Native classification. */
    public record SourceRefs(ControlBuild.FileRef queueSource, ControlBuild.FileRef entrySource, ControlBuild.FileRef nativeBindingSource) {
        public SourceRefs {
            for (var ref : List.of(queueSource, entrySource, nativeBindingSource)) {
                Objects.requireNonNull(ref);
                if (ref.bytes() < 1 || ref.bytes() > 32L * 1024 * 1024) { throw new IllegalArgumentException("finite actual owner source pins required"); }
            }
            if (List.of(queueSource.path(), entrySource.path(), nativeBindingSource.path()).stream().distinct().count() != 3) {
                throw new IllegalArgumentException("three distinct actual owner sources required");
            }
        }
    }
    public sealed interface OpenResult permits Unavailable { }
    public sealed interface NativeOpenResult permits NativeSession, Unavailable, Unknown { }
    public sealed interface Observation permits NativeObservation, KnownToolError, Unknown, Unavailable { }
    public sealed interface SoftwareOpenResult permits SoftwareSession, Unavailable, Unknown { }
    public sealed interface SoftwareObservation permits SoftwareSnapshot, SoftwareRawSnapshot, Unknown, Unavailable { }
    public record SoftwareRawSnapshot(OwnedSoftwareRawCompletion completion) implements SoftwareObservation {
        public SoftwareRawSnapshot { Objects.requireNonNull(completion); }
    }
    public sealed interface RawOpenResult permits RawPreflight, Unknown, Unavailable { }
    public sealed interface RawObservation permits RawSnapshot, Unknown, Unavailable { }
    public record RawSnapshot(OwnedRawCompletion completion) implements RawObservation {
        public RawSnapshot { Objects.requireNonNull(completion); }
    }
    public record Unavailable(Reason reason, String detail) implements OpenResult, NativeOpenResult, Observation, SoftwareOpenResult, SoftwareObservation, RawOpenResult, RawObservation { }
    /** Retained actual Native source only; existing context consumer still validates the complete snapshot/business tuple. */
    public static final class NativeObservation implements Observation {
        private final G2WindowsRootSources.NativeArrival arrival;
        private final OwnedCompletion completion;
        private NativeObservation(G2WindowsRootSources.NativeArrival arrival, OwnedCompletion completion) {
            this.arrival = Objects.requireNonNull(arrival); this.completion = Objects.requireNonNull(completion);
            if (completion.isError()) { throw new IllegalArgumentException("known tool error cannot be a Native observation"); }
        }
        public G2WindowsRootSources.NativeArrival arrival() { return arrival; }
        public OwnedCompletion completion() { return completion; }
    }
    public record KnownToolError(OwnedCompletion completion) implements Observation {
        public KnownToolError {
            Objects.requireNonNull(completion);
            if (!completion.isError()) { throw new IllegalArgumentException("actual known error completion required"); }
        }
    }
    public record SoftwareSnapshot(OwnedSoftwareCompletion completion) implements SoftwareObservation {
        public SoftwareSnapshot { Objects.requireNonNull(completion); }
    }
    public record Unknown(String exceptionType, String detail, RootMcpWire.JsonBytes lastFrame) implements Observation, NativeOpenResult, SoftwareObservation, SoftwareOpenResult, RawOpenResult, RawObservation {
        public boolean replayAllowed() { return false; }
    }
    /** Genuine owned-pipe custody, explicitly SOFTWARE. No NativeArrival conversion or public constructor exists. */
    public static final class OwnedSoftwareCompletion {
        private final WindowsJobProcess.ProcessIdentity child;
        private final String sessionNonce;
        private final long arrivalSequence;
        private final List<ControlBuild.FileRef> programSources;
        private final RootMcpExchange.Call call;
        private OwnedSoftwareCompletion(WindowsJobProcess.OwnedStdio channel, WindowsJobProcess.Arrival arrival, RootMcpExchange.Call call) {
            this.child = channel.identity(); this.sessionNonce = channel.sessionNonce(); this.arrivalSequence = arrival.sequence();
            this.programSources = List.copyOf(channel.spec().programSourceRefs()); this.call = call;
        }
        public WindowsJobProcess.ProcessIdentity child() { return child; }
        public String sessionNonce() { return sessionNonce; }
        public long arrivalSequence() { return arrivalSequence; }
        public List<ControlBuild.FileRef> programSources() { return programSources; }
        public RootMcpWire.OwnerRow ownerRow() { return call.row(); }
        public RootMcpWire.JsonBytes originalRpcLine() { return call.originalRpcLine(); }
        public RootMcpWire.JsonBytes originalResult() { return call.result().originalResult(); }
        public List<RootMcpWire.JsonBytes> notifications() { return call.notifications(); }
        public boolean isError() { return call.result().isError(); }
        public RootMcpWire.JsonBytes semanticBody() throws IOException { return RootMcpWire.semanticBody(call.result()); }
    }
    /** Only the admitted actual owned transport can construct this completion. No file/JSON/software conversion exists. */
    public static final class OwnedCompletion {
        private final WindowsJobProcess.ProcessIdentity child;
        private final String sessionNonce;
        private final WindowsJobProcess.Arrival arrival;
        private final RootMcpExchange.Call call;
        private OwnedCompletion(WindowsJobProcess.OwnedStdio channel, WindowsJobProcess.Arrival arrival, RootMcpExchange.Call call) {
            this.child = channel.identity(); this.sessionNonce = channel.sessionNonce(); this.arrival = arrival; this.call = call;
        }
        public WindowsJobProcess.ProcessIdentity child() { return child; }
        public String sessionNonce() { return sessionNonce; }
        public long arrivalSequence() { return arrival.sequence(); }
        public Instant arrivalDeadline() { return arrival.deadline(); }
        public WindowsJobProcess.Arrival actualArrival() { return arrival; }
        public RootMcpWire.OwnerRow ownerRow() { return call.row(); }
        public RootMcpWire.JsonBytes originalRpcLine() { return call.originalRpcLine(); }
        public RootMcpWire.JsonBytes originalResult() { return call.result().originalResult(); }
        public List<RootMcpWire.JsonBytes> notifications() { return call.notifications(); }
        public boolean isError() { return call.result().isError(); }
    }
    /** Fixed CAP bootstrap completion from the same admitted owned stdout. It grants no authority by its JSON fields alone. */
    public static final class OwnedCapabilities {
        private final WindowsJobProcess.ProcessIdentity child;
        private final String sessionNonce;
        private final WindowsJobProcess.Arrival arrival;
        private final RootMcpExchange.Capabilities call;
        private final RootMcpWire.JsonBytes structuredContent;
        private OwnedCapabilities(WindowsJobProcess.OwnedStdio channel, WindowsJobProcess.Arrival arrival,
                RootMcpExchange.Capabilities call) throws IOException {
            this.child = channel.identity(); this.sessionNonce = channel.sessionNonce(); this.arrival = arrival; this.call = call;
            this.structuredContent = RootMcpWire.capabilitiesBody(call.result());
        }
        public WindowsJobProcess.ProcessIdentity child() { return child; }
        public String sessionNonce() { return sessionNonce; }
        public long arrivalSequence() { return arrival.sequence(); }
        public Instant arrivalDeadline() { return arrival.deadline(); }
        public WindowsJobProcess.Arrival actualArrival() { return arrival; }
        public RootMcpWire.JsonBytes originalRpcLine() { return call.originalRpcLine(); }
        public RootMcpWire.JsonBytes originalResult() { return call.result().originalResult(); }
        public RootMcpWire.JsonBytes structuredContent() { return structuredContent; }
        public List<RootMcpWire.JsonBytes> notifications() { return call.notifications(); }
        public boolean isError() { return call.result().isError(); }
    }
    /** Actual owned stdout custody only. This decoded transport-cache observation cannot become a NativeArrival. */
    public static final class OwnedRawCompletion {
        private final WindowsJobProcess.ProcessIdentity child;
        private final String sessionNonce;
        private final WindowsJobProcess.Arrival arrival;
        private final RootMcpExchange.Raw call;
        private OwnedRawCompletion(WindowsJobProcess.OwnedStdio channel, WindowsJobProcess.Arrival arrival, RootMcpExchange.Raw call) {
            this.child = channel.identity(); this.sessionNonce = channel.sessionNonce(); this.arrival = arrival; this.call = call;
        }
        public WindowsJobProcess.ProcessIdentity child() { return child; }
        public String sessionNonce() { return sessionNonce; }
        public long arrivalSequence() { return arrival.sequence(); }
        public Instant arrivalDeadline() { return arrival.deadline(); }
        public WindowsJobProcess.Arrival actualArrival() { return arrival; }
        public RootMcpWire.JsonBytes originalRpcLine() { return call.originalRpcLine(); }
        public RootMcpWire.JsonBytes originalResult() { return call.result().originalResult(); }
        public RootMcpWire.JsonBytes structuredContent() { return call.frame().wrapper(); }
        public RootMcpRawWire.Frame frame() { return call.frame(); }
        public List<RootMcpWire.JsonBytes> notifications() { return call.notifications(); }
        public boolean isError() { return call.result().isError(); }
    }
    /** Software peer custody stays a separate type, even when its JSON has the raw transport schema. */
    public static final class OwnedSoftwareRawCompletion {
        private final WindowsJobProcess.ProcessIdentity child;
        private final String sessionNonce;
        private final RootMcpExchange.Raw call;
        private final long arrivalSequence;
        private OwnedSoftwareRawCompletion(WindowsJobProcess.OwnedStdio channel, WindowsJobProcess.Arrival arrival, RootMcpExchange.Raw call) {
            this.child = channel.identity(); this.sessionNonce = channel.sessionNonce(); this.call = call; this.arrivalSequence = arrival.sequence();
        }
        public WindowsJobProcess.ProcessIdentity child() { return child; }
        public String sessionNonce() { return sessionNonce; }
        public long arrivalSequence() { return arrivalSequence; }
        public RootMcpWire.JsonBytes originalRpcLine() { return call.originalRpcLine(); }
        public RootMcpRawWire.Frame frame() { return call.frame(); }
    }
    public static boolean hasSelectedSourceRefs(Optional<SourceRefs> sources) { return Objects.requireNonNull(sources).isPresent(); }
    /**
     * Native path refuses before any channel access or write, including when all three ordinary pins exist.
     * Existing G2WindowsRootSources.Captured does not bind an accepted Native DLL/runtime/owner.
     * Native callers must instead consume the concrete authority's same-JVM opaque admission through openNative.
     * That admission binds its frozen graph, held DLL, current Game PID/birth/EXE, episode/version and pre-call capture.
     */
    public static OpenResult open(WindowsJobProcess.OwnedStdio channel, Optional<SourceRefs> sources,
            RootMcpWire.Handshake handshake, RootMcpWire.Limits limits, Instant deadline) {
        Objects.requireNonNull(sources);
        if (sources.isEmpty()) { return new Unavailable(Reason.SOURCE_UNBOUND, "Root has not selected qualified actual queue/entry/native-binding sources"); }
        return new Unavailable(Reason.ACCEPTED_NATIVE_RUNTIME_UNAVAILABLE,
                "ordinary source pins and owned transport grant no Native authority; use the concrete authority's opaque admission");
    }
    /** Missing/invalid concrete admission is rejected before initialization writes. Three ordinary pins cannot enter this route. */
    public static NativeOpenResult openNative(WindowsJobProcess.OwnedStdio channel,
            Optional<RootNativePreloadAuthority.NativeAdmission> admission, RootMcpWire.Handshake handshake,
            RootMcpWire.Limits limits, Instant deadline) {
        Objects.requireNonNull(admission);
        if (admission.isEmpty()) {
            return new Unavailable(Reason.ACCEPTED_NATIVE_RUNTIME_UNAVAILABLE, "actual preload/endpoint/runtime authority has not issued Native admission");
        }
        Objects.requireNonNull(channel); Objects.requireNonNull(handshake); Objects.requireNonNull(limits);
        if (limits.maximumLineBytes() != RootMcpEnvelope.RPC_LINE_MAX_BYTES
                || channel.spec().maxFrameBytes() < RootMcpEnvelope.RPC_LINE_MAX_BYTES
                || channel.spec().maxReceivedBytes() > RootMcpEnvelope.SESSION_RECEIVED_MAX_BYTES
                || channel.spec().maxSentBytes() > RootMcpEnvelope.SESSION_SENT_MAX_BYTES) {
            return new Unavailable(Reason.SOURCE_REJECTED, "Native semantic consumer requires the unified finite whole-envelope budgets");
        }
        RootNativePreloadAuthority.NativeAdmission actual = admission.orElseThrow();
        try { actual.requireRawPreflightPassed(); actual.claimInitialization(channel); }
        catch (IOException | RuntimeException error) { return new Unavailable(Reason.ADMISSION_UNAVAILABLE, detail(error)); }
        OwnedPort port = new OwnedPort(channel); RootMcpExchange exchange = new RootMcpExchange(port, limits, handshake);
        try {
            exchange.initialize(earliest(channel, deadline)); actual.requireTransport(channel);
            return activateCapabilitiesOnce(channel, actual, port, exchange, deadline);
        } catch (IOException | RuntimeException error) {
            actual.markUnknown(); RootMcpExchange.Failure failure = exchange.failure(); exchange.close();
            return new Unknown(error.getClass().getName(), detail(error), failure != null ? failure.lastFrame()
                    : lastOwnedFrame(port));
        }
    }
    /** Same actual admission/owner, initialized once, with fixed raw observation before any CAP side effects. */
    public static RawOpenResult openRawPreflight(WindowsJobProcess.OwnedStdio channel,
            Optional<RootNativePreloadAuthority.NativeAdmission> admission, RootMcpWire.Handshake handshake,
            RootMcpWire.Limits limits, Instant deadline) {
        Objects.requireNonNull(admission);
        if (admission.isEmpty()) {
            return new Unavailable(Reason.ACCEPTED_NATIVE_RUNTIME_UNAVAILABLE, "actual runtime/Game/endpoint admission is required before raw initialization");
        }
        Objects.requireNonNull(channel); Objects.requireNonNull(handshake); Objects.requireNonNull(limits);
        if (limits.maximumLineBytes() != RootMcpEnvelope.RPC_LINE_MAX_BYTES
                || channel.spec().maxFrameBytes() < RootMcpEnvelope.RPC_LINE_MAX_BYTES
                || channel.spec().maxReceivedBytes() > RootMcpEnvelope.SESSION_RECEIVED_MAX_BYTES
                || channel.spec().maxSentBytes() > RootMcpEnvelope.SESSION_SENT_MAX_BYTES) {
            return new Unavailable(Reason.SOURCE_REJECTED, "raw preflight requires the same finite 32 MiB RPC/64 MiB session envelope");
        }
        RootNativePreloadAuthority.NativeAdmission actual = admission.orElseThrow();
        try { actual.claimInitialization(channel); }
        catch (IOException | RuntimeException error) { return new Unavailable(Reason.ADMISSION_UNAVAILABLE, detail(error)); }
        OwnedPort port = new OwnedPort(channel); RootMcpExchange exchange = new RootMcpExchange(port, limits, handshake);
        try {
            exchange.initialize(earliest(channel, deadline)); actual.requireTransport(channel);
            return new RawPreflight(channel, actual, port, exchange);
        } catch (IOException | RuntimeException error) {
            actual.markUnknown(); RootMcpExchange.Failure failure = exchange.failure(); exchange.close();
            return new Unknown(error.getClass().getName(), detail(error), failure == null ? new RootMcpWire.JsonBytes(new byte[0]) : failure.lastFrame());
        }
    }
    public static final class RawPreflight implements RawOpenResult, AutoCloseable {
        private final WindowsJobProcess.OwnedStdio channel;
        private final RootNativePreloadAuthority.NativeAdmission admission;
        private final OwnedPort port;
        private final RootMcpExchange exchange;
        private boolean ended;
        private boolean inputClosed;
        private boolean transferred;
        private RawPreflight(WindowsJobProcess.OwnedStdio channel, RootNativePreloadAuthority.NativeAdmission admission,
                OwnedPort port, RootMcpExchange exchange) {
            this.channel = channel; this.admission = admission; this.port = port; this.exchange = exchange;
        }
        public synchronized RawObservation observeRaw(Instant deadline) {
            if (ended) { return new Unavailable(Reason.CLOSED, "raw preflight ended; no initialization or unknown request is replayed"); }
            RootMcpExchange.Raw completed = null;
            try {
                admission.requireTransport(channel); port.lastArrival = null;
                completed = exchange.raw(earliest(channel, deadline)); admission.requireTransport(channel);
                WindowsJobProcess.Arrival arrival = requireOriginalArrival(channel, port, completed.originalRpcLine());
                return new RawSnapshot(new OwnedRawCompletion(channel, arrival, completed));
            } catch (IOException | RuntimeException error) {
                admission.markUnknown(); ended = true; exchange.close(); RootMcpExchange.Failure failure = exchange.failure();
                return new Unknown(error.getClass().getName(), detail(error), failure != null ? failure.lastFrame()
                        : completed == null ? new RootMcpWire.JsonBytes(new byte[0]) : completed.originalRpcLine());
            }
        }
        /** The sole authority must first consume the real original-writer RawFrameTicket for this actual completion. */
        public synchronized NativeOpenResult activateNative(Instant deadline) {
            if (ended) { return new Unavailable(Reason.CLOSED, "raw preflight ended; transport cannot be initialized again"); }
            try { admission.requireRawPreflightPassed(); }
            catch (IOException | RuntimeException error) { return new Unavailable(Reason.ADMISSION_UNAVAILABLE, detail(error)); }
            ended = true;
            try {
                NativeSession activated = activateCapabilitiesOnce(channel, admission, port, exchange, deadline);
                transferred = true; return activated;
            } catch (IOException | RuntimeException error) {
                admission.markUnknown(); exchange.close(); RootMcpExchange.Failure failure = exchange.failure();
                return new Unknown(error.getClass().getName(), detail(error), failure != null ? failure.lastFrame()
                        : lastOwnedFrame(port));
            }
        }
        @Override public synchronized void close() throws IOException {
            // A successful activation transfers the same exchange to NativeSession; closing the former view must not close it.
            if (!transferred) { admission.markUnknown(); ended = true; exchange.close(); if (!inputClosed) { channel.closeInput(); inputClosed = true; } }
        }
    }
    public static final class NativeSession implements NativeOpenResult, AutoCloseable {
        private final WindowsJobProcess.OwnedStdio channel;
        private final RootNativePreloadAuthority.NativeAdmission admission;
        private final OwnedPort port;
        private final RootMcpExchange exchange;
        private boolean closed;
        private boolean inputClosed;
        private NativeSession(WindowsJobProcess.OwnedStdio channel, RootNativePreloadAuthority.NativeAdmission admission,
                OwnedPort port, RootMcpExchange exchange) {
            this.channel = channel; this.admission = admission; this.port = port; this.exchange = exchange;
        }
        public synchronized Observation observe(long rootSequence, Instant deadline) {
            if (closed) { return new Unavailable(Reason.CLOSED, "Root Native MCP session is closed"); }
            RootNativePreloadAuthority.CallWitness witness;
            Instant until;
            try {
                until = earliest(channel, deadline); admission.requireTransport(channel);
                witness = admission.beforeCall(rootSequence, until);
            } catch (IOException | RuntimeException error) {
                admission.markUnknown(); closed = true; exchange.close(); return new Unavailable(Reason.ADMISSION_UNAVAILABLE, detail(error));
            }
            RootMcpExchange.Call completedCall = null;
            try {
                port.lastArrival = null; RootMcpExchange.Call call = exchange.semantic(rootSequence, until); completedCall = call;
                admission.requireTransport(channel); WindowsJobProcess.Arrival arrival = requireOriginalArrival(channel, port, call.originalRpcLine());
                if (!call.result().isError()) { RootMcpWire.semanticBody(call.result()); }
                OwnedCompletion completed = new OwnedCompletion(channel, arrival, call);
                if (completed.isError()) {
                    admission.completeKnownError(witness, completed); admission.requireTransport(channel); return new KnownToolError(completed);
                }
                G2WindowsRootSources.NativeArrival retained = admission.completeNative(witness, completed);
                admission.requireTransport(channel); return new NativeObservation(retained, completed);
            } catch (IOException | RuntimeException error) {
                admission.markUnknown(); closed = true; exchange.close(); RootMcpExchange.Failure failure = exchange.failure();
                return new Unknown(error.getClass().getName(), detail(error),
                        failure != null ? failure.lastFrame() : completedCall != null ? completedCall.originalRpcLine() : new RootMcpWire.JsonBytes(new byte[0]));
            }
        }
        @Override public synchronized void close() throws IOException {
            closed = true; exchange.close(); if (!inputClosed) { channel.closeInput(); inputClosed = true; }
        }
    }
    /** Production protocol/resource path for software qualification; its completion type cannot be promoted to Native. */
    public static SoftwareOpenResult openSoftware(WindowsJobProcess.OwnedStdio channel,
            RootMcpWire.Handshake handshake, RootMcpWire.Limits limits, Instant deadline) {
        Objects.requireNonNull(channel); Objects.requireNonNull(handshake); Objects.requireNonNull(limits);
        if (limits.maximumLineBytes() > channel.spec().maxFrameBytes()) {
            return new Unavailable(Reason.SOURCE_REJECTED, "MCP role frame budget exceeds the owned channel budget");
        }
        OwnedPort port = new OwnedPort(channel); RootMcpExchange exchange = new RootMcpExchange(port, limits, handshake);
        try {
            channel.verifyActualIdentityAndSources(); exchange.initialize(earliest(channel, deadline)); channel.verifyActualIdentityAndSources();
            return new SoftwareSession(channel, port, exchange);
        } catch (IOException | RuntimeException error) {
            RootMcpExchange.Failure failure = exchange.failure(); exchange.close();
            return new Unknown(error.getClass().getName(), detail(error), failure == null ? new RootMcpWire.JsonBytes(new byte[0]) : failure.lastFrame());
        }
    }
    public static final class SoftwareSession implements SoftwareOpenResult, AutoCloseable {
        private final WindowsJobProcess.OwnedStdio channel;
        private final OwnedPort port;
        private final RootMcpExchange exchange;
        private boolean closed;
        private boolean inputClosed;
        private SoftwareSession(WindowsJobProcess.OwnedStdio channel, OwnedPort port, RootMcpExchange exchange) {
            this.channel = channel; this.port = port; this.exchange = exchange;
        }
        public synchronized SoftwareObservation raw(Instant deadline) {
            if (closed) { return new Unavailable(Reason.CLOSED, "Root software MCP session is closed"); }
            RootMcpExchange.Raw completed = null;
            try {
                channel.verifyActualIdentityAndSources(); port.lastArrival = null;
                completed = exchange.raw(earliest(channel, deadline)); channel.verifyActualIdentityAndSources();
                WindowsJobProcess.Arrival arrival = requireOriginalArrival(channel, port, completed.originalRpcLine());
                return new SoftwareRawSnapshot(new OwnedSoftwareRawCompletion(channel, arrival, completed));
            } catch (IOException | RuntimeException error) {
                exchange.close(); closed = true; RootMcpExchange.Failure failure = exchange.failure();
                return new Unknown(error.getClass().getName(), detail(error), failure != null ? failure.lastFrame()
                        : completed == null ? new RootMcpWire.JsonBytes(new byte[0]) : completed.originalRpcLine());
            }
        }
        public synchronized SoftwareObservation snapshot(long rootSequence, Instant deadline) {
            if (closed) { return new Unavailable(Reason.CLOSED, "Root software MCP session is closed"); }
            RootMcpExchange.Call completedCall = null;
            try {
                channel.verifyActualIdentityAndSources(); port.lastArrival = null;
                RootMcpExchange.Call call = exchange.semantic(rootSequence, earliest(channel, deadline)); completedCall = call;
                channel.verifyActualIdentityAndSources(); WindowsJobProcess.Arrival arrival = requireOriginalArrival(channel, port, call.originalRpcLine());
                return new SoftwareSnapshot(new OwnedSoftwareCompletion(channel, arrival, call));
            } catch (IOException | RuntimeException error) {
                exchange.close(); closed = true; RootMcpExchange.Failure failure = exchange.failure();
                return new Unknown(error.getClass().getName(), detail(error),
                        failure != null ? failure.lastFrame() : completedCall != null ? completedCall.originalRpcLine() : new RootMcpWire.JsonBytes(new byte[0]));
            }
        }
        /** Caller still consumes actual exit/timeout/Job0 from the original resource owner. */
        @Override public synchronized void close() throws IOException {
            closed = true; exchange.close(); if (!inputClosed) { channel.closeInput(); inputClosed = true; }
        }
    }
    private static final class OwnedPort implements RootMcpExchange.Port {
        private final WindowsJobProcess.OwnedStdio channel;
        private WindowsJobProcess.Arrival lastArrival;
        private Instant lastReadDeadline;
        private OwnedPort(WindowsJobProcess.OwnedStdio channel) { this.channel = channel; }
        @Override public void verify() throws IOException { channel.verifyActualIdentityAndSources(); }
        @Override public void write(byte[] bytes, Instant deadline) throws IOException {
            try {
                var receipt = channel.write(bytes, deadline);
                if (receipt.bytesWritten() != bytes.length || !receipt.identity().equals(channel.identity())
                        || !receipt.sessionNonce().equals(channel.sessionNonce())) {
                    throw new IOException("partial or changed-owner MCP protocol write; outcome unknown");
                }
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt(); throw new IOException("MCP protocol write interrupted; outcome unknown", interrupted);
            }
        }
        @Override public byte[] readLine(Instant deadline) throws IOException {
            try {
                lastReadDeadline = deadline.isBefore(channel.deadline()) ? deadline : channel.deadline();
                lastArrival = channel.readLine(deadline); return lastArrival.rawBytes();
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt(); throw new IOException("MCP protocol read interrupted; outcome unknown", interrupted);
            }
        }
    }
    /** Both Native entry paths share the one write-before claim and real post-CAP ticket producer. */
    private static NativeSession activateCapabilitiesOnce(WindowsJobProcess.OwnedStdio channel,
            RootNativePreloadAuthority.NativeAdmission admission, OwnedPort port, RootMcpExchange exchange,
            Instant requested) throws IOException {
        port.lastArrival = null; admission.requireTransport(channel);
        admission.claimCapabilities();
        RootMcpExchange.Capabilities completed = exchange.capabilitiesOnce(earliest(channel, requested));
        admission.requireTransport(channel);
        WindowsJobProcess.Arrival arrival = requireOriginalArrival(channel, port, completed.originalRpcLine());
        admission.completeCapabilities(new OwnedCapabilities(channel, arrival, completed));
        admission.requireTransport(channel);
        if (admission.phase() != RootNativePreloadAuthority.Phase.ACTIVE) {
            throw new IOException("single CAP completed without actual post-CAP qualification; a new Root review is required, no replay");
        }
        exchange.finishCapabilities(); return new NativeSession(channel, admission, port, exchange);
    }
    private static RootMcpWire.JsonBytes lastOwnedFrame(OwnedPort port) {
        return new RootMcpWire.JsonBytes(port.lastArrival == null ? new byte[0] : port.lastArrival.rawBytes());
    }
    private static Instant earliest(WindowsJobProcess.OwnedStdio channel, Instant requested) throws IOException {
        if (requested == null) { throw new IOException("explicit finite MCP request deadline required"); }
        Instant result = requested.isBefore(channel.deadline()) ? requested : channel.deadline();
        if (!Instant.now().isBefore(result)) { throw new IOException("MCP request deadline expired"); } return result;
    }
    private static WindowsJobProcess.Arrival requireOriginalArrival(WindowsJobProcess.OwnedStdio channel,
            OwnedPort port, RootMcpWire.JsonBytes originalRpcLine) throws IOException {
        WindowsJobProcess.Arrival arrival = port.lastArrival;
        if (arrival == null || !arrival.identity().equals(channel.identity()) || !arrival.sessionNonce().equals(channel.sessionNonce())
                || !arrival.deadline().equals(port.lastReadDeadline) || arrival.deadline().isAfter(channel.deadline())
                || !Arrays.equals(arrival.rawBytes(), originalRpcLine.bytes())) {
            throw new IOException("completed MCP frame lost its original Job-owned pipe custody");
        }
        return arrival;
    }
    private static String detail(Exception error) { return error.getMessage() == null ? error.getClass().getName() : error.getMessage(); }
}
