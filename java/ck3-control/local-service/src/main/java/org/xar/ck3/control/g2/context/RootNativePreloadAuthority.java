package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.WeakHashMap;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.NativeServerLocator;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.WindowsPreloadCustody;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.wave2.runtime.closedadoption.RootColdResumeSession;

/** Root's concrete authority composer over original Game, DLL, owner and endpoint resources. */
public final class RootNativePreloadAuthority {
    private RootNativePreloadAuthority() { }
    private static final java.util.Map<WindowsJobProcess.OwnedStdio, Boolean> CONSUMED_CHANNELS = new WeakHashMap<>();
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .streamReadConstraints(StreamReadConstraints.builder().maxStringLength(G2RetainedNativeSourceProvider.MAX_NATIVE_ARTIFACT_BYTES).build())
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS, DeserializationFeature.USE_BIG_INTEGER_FOR_INTS,
                    DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);
    public enum Phase { AWAITING_CAPABILITIES, ACTIVE, CLOSED, UNKNOWN }
    /** HANDLE is a locator, not a credential; the resource producer performs all kernel checks. */
    public record EndpointLocator(String serverHandleDecimal) {
        public EndpointLocator {
            if (serverHandleDecimal == null || !serverHandleDecimal.matches("[1-9][0-9]{0,19}")
                    || new BigInteger(serverHandleDecimal).bitLength() > 64) throw new IllegalArgumentException("Canonical unsigned pointer-sized HANDLE locator required");
        }
    }
    public record SourcePlan(String sessionId, Optional<String> expectedEpisode,
            ExactRef launcherSettings, List<G2WindowsRootSources.RuntimeSource> runtimeSources,
            Path evidenceRoot, long executableBudget, long runtimeFileBudget) {
        public SourcePlan {
            StrictJson.text(sessionId); expectedEpisode = Objects.requireNonNull(expectedEpisode);
            expectedEpisode.ifPresent(StrictJson::text); Objects.requireNonNull(launcherSettings);
            runtimeSources = List.copyOf(runtimeSources); Objects.requireNonNull(evidenceRoot);
            if (!evidenceRoot.isAbsolute() || executableBudget < 1 || runtimeFileBudget < 1) throw new IllegalArgumentException("Root's finite actual EXE/runtime source plan required");
        }
    }
    public static final class CallWitness {
        private final NativeAdmission issuer;
        private final long sequence;
        private final Instant started, deadline;
        private final G2WindowsRootSources.Captured capture;
        private boolean consumed;
        private CallWitness(NativeAdmission issuer, long sequence, Instant started, Instant deadline, G2WindowsRootSources.Captured capture) {
            this.issuer = issuer; this.sequence = sequence; this.started = started; this.deadline = deadline; this.capture = capture;
        }
    }
    /** Private construction cannot be replaced by a JSON Native flag or a SOFTWARE completion. */
    public static final class NativeAdmission implements AutoCloseable {
        private final RootColdResumeSession.HeldGame game;
        private final WindowsJobProcess.OwnedStdio channel;
        private final WindowsPreloadCustody.Endpoint endpoint;
        private final SourcePlan plan;
        private final String version;
        private Phase phase = Phase.AWAITING_CAPABILITIES;
        private G2WindowsRootSources sources;
        private String episode, generation;
        private long lastRootSequence, lastArrival;
        private boolean initializationClaimed;
        private boolean rawPreflightPassed;
        private boolean capabilitiesClaimed;
        private boolean firstSemanticAccepted;
        private CallWitness pending;
        private NativeAdmission(RootColdResumeSession.HeldGame game, WindowsJobProcess.OwnedStdio channel,
                WindowsPreloadCustody.Endpoint endpoint, SourcePlan plan, String version) {
            this.game = game; this.channel = channel; this.endpoint = endpoint; this.plan = plan; this.version = version;
        }
        public synchronized Phase phase() { return phase; }
        public synchronized void markUnknown() {
            if (phase != Phase.CLOSED) phase = Phase.UNKNOWN;
            if (pending != null) pending.consumed = true;
            pending = null;
        }
        /** Consumed before any initialize bytes; reconnecting cannot reset an UNKNOWN RPC session. */
        public synchronized void claimInitialization(WindowsJobProcess.OwnedStdio actual) throws IOException {
            if (initializationClaimed || phase != Phase.AWAITING_CAPABILITIES) throw new IOException("Native initialization already consumed; no repeated open");
            initializationClaimed = true;
            try { requireTransport(actual); }
            catch (IOException | RuntimeException failure) { phase = Phase.UNKNOWN; throw failure; }
        }
        public synchronized G2WindowsRootSources rootSources() throws IOException {
            requireActive(); requireTransport(channel); return sources;
        }
        /** Direct same-JVM Java map context seam; original opaque arrival and payload bytes stay bound. */
        public synchronized G2CallContextProducer.Result context(Milestone milestone, ProjectionJson originalPayload,
                RootMcpSemanticClient.NativeObservation observation) throws IOException {
            requireActive(); requireTransport(channel); Objects.requireNonNull(observation);
            G2WindowsRootSources.RequestScope scope = sources.bindRequest(milestone, originalPayload, observation.arrival());
            try { return sources.context(milestone, originalPayload); }
            finally { scope.close(); }
        }
        public synchronized void requireTransport(WindowsJobProcess.OwnedStdio actual) throws IOException {
            if (actual != channel || phase == Phase.CLOSED || phase == Phase.UNKNOWN) throw new IOException("Native admission belongs to another or terminal actual owned transport");
            game.verify(); game.runtime().requireOwner(actual); actual.verifyActualIdentityAndSources(); endpoint.verify();
            if (!endpoint.ownerIdentity().equals(actual.identity()) || !endpoint.targetIdentity().equals(game.identity())
                    || !endpoint.pipeName().equals(game.pipeName())) throw new IOException("Actual original server owner/Game/pipe resource differs");
            WindowsPreloadCustody.LoadedObservation loaded = game.custody().observeLoaded();
            if (!loaded.targetIdentity().equals(game.identity()) || !loaded.dll().originalRef().equals(game.runtime().request().nativeDll())
                    || loaded.matchingDll().heldFile().isEmpty()
                    || !loaded.matchingDll().heldFile().orElseThrow().equals(loaded.dll().nativeFile())) {
                throw new IOException("Current full loaded roster does not bind the continuously held pre-load DLL");
            }
        }
        /** Only the original cold-session writer preview can supply this private once ticket. */
        public synchronized void completeRawPreflight(RootMcpSemanticClient.OwnedRawCompletion actual,
                RootColdResumeSession.RawFrameTicket ticket) throws IOException {
            RootColdResumeSession.RawColdFrame projection = projectRawPreflight(actual);
            try {
                Objects.requireNonNull(ticket);
                requireArrival(actual.actualArrival(), actual.originalRpcLine().bytes());
                ticket.consume(game.session(), projection, channel);
                requireTransport(channel); rawPreflightPassed = true;
            } catch (IOException | RuntimeException failure) { markUnknown(); throw failure; }
        }
        /** One shared actual-byte-to-cold-data projection, reused by the original writer preview and ticket consumer. */
        public synchronized RootColdResumeSession.RawColdFrame projectRawPreflight(
                RootMcpSemanticClient.OwnedRawCompletion actual) throws IOException {
            if (!initializationClaimed || phase != Phase.AWAITING_CAPABILITIES || rawPreflightPassed || pending != null)
                throw new IOException("One original initialized raw preflight required before CAP");
            try {
                Objects.requireNonNull(actual); requireTransport(channel);
                verifyArrival(actual.actualArrival(), actual.originalRpcLine().bytes());
                if (actual.isError() || !actual.child().equals(channel.identity())
                        || !actual.sessionNonce().equals(channel.sessionNonce())
                        || !Instant.now().isBefore(actual.arrivalDeadline())) throw new IOException("Original successful bounded raw completion required");
                RootMcpRawWire.Frame frame = actual.frame();
                if (!Arrays.equals(frame.wrapper().bytes(), actual.structuredContent().bytes()))
                    throw new IOException("Raw parsed frame differs from actual response bytes");
                String rawGeneration = validateDiagnostics(object(parse(frame.diagnostics().bytes(), StrictJson.EXPLICIT_MAX_BYTES)), null);
                var played = frame.playedCharacter().orElseThrow(() -> new IOException("Actual raw played character unavailable"));
                return new RootColdResumeSession.RawColdFrame(frame.snapshotId(), frame.publicRevision(),
                        frame.nativeRevision(), frame.dateRaw(), played.characterId(), frame.mapReady(), frame.paused(),
                        game.identity(), game.pipeName(), rawGeneration,
                        G2RetainedNativeSourceProvider.sha256(actual.originalRpcLine().bytes()), actual.arrivalSequence(),
                        frame.ownerColdAdoption());
            } catch (IOException | RuntimeException failure) { markUnknown(); throw failure; }
        }
        public synchronized void requireRawPreflightPassed() throws IOException {
            if (!rawPreflightPassed || phase == Phase.UNKNOWN || phase == Phase.CLOSED)
                throw new IOException("Genuine current original-writer raw ticket required before CAP; no initialization or CAP replay");
            requireTransport(channel);
        }
        /** CAP can persist Driver state. Reserve once before its first byte, never poll or replay it. */
        public synchronized void claimCapabilities() throws IOException {
            requireRawPreflightPassed();
            if (capabilitiesClaimed || phase != Phase.AWAITING_CAPABILITIES) throw new IOException("Original CAP submission already consumed");
            game.session().claimBootstrapCapabilities(channel);
            capabilitiesClaimed = true;
        }
        /** Fixed actual CAP arrival, after independent kernel/source checks; never a JSON loader. */
        public synchronized void completeCapabilities(RootMcpSemanticClient.OwnedCapabilities completion) throws IOException {
            requireRawPreflightPassed();
            if (!initializationClaimed || !capabilitiesClaimed || phase != Phase.AWAITING_CAPABILITIES || pending != null) throw new IOException("Native CAP phase unavailable or consumed");
            try {
                requireTransport(channel); requireArrival(completion.actualArrival(), completion.originalRpcLine().bytes());
                if (completion.isError()) throw new IOException("Actual Native capabilities returned a known tool error");
                JsonNode cap = object(parse(completion.structuredContent().bytes(), RootMcpEnvelope.CAPABILITIES_BODY_MAX_BYTES));
                if (!integer(cap, "format_version", BigInteger.ONE, BigInteger.ONE).equals(BigInteger.ONE)
                        || !text(cap, "backend_id").equals("native-headless") || !text(cap, "mode").equals("native-headless")
                        || !text(cap, "source").equals("injected-dll-named-pipe")) {
                    throw new IOException("Actual capabilities are not the original Native backend");
                }
                JsonNode diagnostics = object(cap.get("diagnostics"));
                if (!text(diagnostics, "pipe_name").equals(game.pipeName())) throw new IOException("Native CAP pipe differs from retained endpoint");
                if (!bool(diagnostics, "connected")) throw new IOException("Completed CAP is disconnected; no repeated CAP submission");
                generation = validateDiagnostics(diagnostics, null);
                if (bool(cap, "episode_identity_pending")) throw new IOException("Completed CAP still pending; new Root qualification required");
                episode = text(cap, "episode_run_id");
                if (!episode.equals(game.session().savedFrame().episodeRunId())
                        || !integer(cap, "episode_character_id", BigInteger.ONE, BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER))
                            .equals(BigInteger.valueOf(game.session().savedFrame().actorCharacterId())))
                    throw new IOException("Actual CAP differs from the genuine original saved episode/character");
                if (plan.expectedEpisode().isPresent() && !episode.equals(plan.expectedEpisode().orElseThrow())) throw new IOException("Actual Native episode differs from Root-selected episode");
                var actual = new RootColdResumeSession.CapabilitiesCompletion(
                        G2RetainedNativeSourceProvider.sha256(completion.originalRpcLine().bytes()), completion.arrivalSequence(),
                        channel.identity(), game.identity(), game.pipeName(), generation);
                try {
                    var ticket = game.session().qualifyCapabilitiesCompletion(actual);
                    ticket.consume(game.session(), actual, channel);
                } catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt(); throw new IOException("Post-CAP original Root qualification interrupted; no repeated CAP", interrupted);
                }
                ControlBuild.FileRef exe = game.runtime().request().gameExecutable();
                sources = new G2WindowsRootSources(new G2WindowsRootSources.Configuration(game.runtime().request().machineId(), plan.sessionId(),
                        new G2RetainedNativeSourceProvider.GameIdentity(game.identity().pid(), game.identity().creationFiletimeDecimal()), episode, generation,
                        new ExactRef(exe.path(), exe.bytes(), exe.sha256()), plan.launcherSettings(), plan.runtimeSources(), plan.evidenceRoot(),
                        plan.executableBudget(), plan.runtimeFileBudget(), RootMcpEnvelope.OWNER_ROW_MAX_BYTES), new G2WindowsReadOnlyObservation());
                requireTransport(channel); phase = Phase.ACTIVE;
            } catch (IOException | RuntimeException failure) { phase = Phase.UNKNOWN; throw failure; }
        }
        public synchronized CallWitness beforeCall(long rootSequence, Instant deadline) throws IOException {
            requireActive(); Objects.requireNonNull(deadline); requireTransport(channel);
            if (pending != null || rootSequence <= lastRootSequence || rootSequence > StrictJson.MAX_SAFE_INTEGER
                    || !Instant.now().isBefore(deadline) || deadline.isAfter(game.deadline())) throw new IOException("One new bounded Root request required");
            Instant started = Instant.now(); G2WindowsRootSources.CaptureResult result = sources.captureBeforeNative();
            if (!(result instanceof G2WindowsRootSources.Captured capture)) throw new IOException("Actual pre-call Root source capture unavailable");
            lastRootSequence = rootSequence;
            pending = new CallWitness(this, rootSequence, started, deadline, capture); return pending;
        }
        public synchronized G2WindowsRootSources.NativeArrival completeNative(CallWitness witness,
                RootMcpSemanticClient.OwnedCompletion completion) throws IOException {
            consume(witness);
            try {
                verifyCompletion(witness, completion);
                if (completion.isError()) throw new IOException("Known tool error grants no Native arrival");
                JsonNode row = object(parse(completion.ownerRow().bytes().bytes(), RootMcpEnvelope.OWNER_ROW_MAX_BYTES));
                JsonNode result = object(row.get("result")), snapshot = object(result.get("structured_content"));
                if (!episode.equals(text(snapshot, "episode_run_id"))) throw new IOException("Native episode changed during original call");
                validateDiagnostics(object(snapshot.get("diagnostics")), generation);
                integer(snapshot, "native_revision", BigInteger.ONE, StrictJson.UINT64_MAX);
                integer(snapshot, "revision", BigInteger.ZERO, StrictJson.UINT64_MAX); text(snapshot, "snapshot_id");
                if (!firstSemanticAccepted) {
                    var saved = game.session().savedFrame();
                    if (!bool(snapshot, "map_ready") || !bool(snapshot, "paused")
                            || !integer(snapshot, "date_raw", BigInteger.ZERO, BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER))
                                .equals(BigInteger.valueOf(saved.dateRaw()))
                            || !integer(object(snapshot.get("played_character")), "character_id", BigInteger.ONE,
                                    BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER)).equals(BigInteger.valueOf(saved.actorCharacterId())))
                        throw new IOException("First actual semantic map differs from the original saved date/character/paused frame");
                    JsonNode expectedLife = object(StrictJson.parse(game.session().runtimeInputs().basis().bytes()).path("checkpoint").get("succession_lifecycle"));
                    JsonNode actualLife = object(snapshot.get("succession_lifecycle"));
                    if (expectedLife.size() != 6 || !Arrays.equals(StrictJson.canonical(expectedLife), StrictJson.canonical(actualLife)))
                        throw new IOException("First actual semantic map differs from the complete original saved lifecycle");
                }
                requireTransport(channel);
                var retained = sources.retainNativeArrival(witness.capture, completion.ownerRow().bytes().bytes(), RootMcpWire.SEMANTIC_TOOL);
                firstSemanticAccepted = true;
                return retained;
            } catch (IOException | RuntimeException failure) { phase = Phase.UNKNOWN; throw failure; }
        }
        public synchronized void completeKnownError(CallWitness witness, RootMcpSemanticClient.OwnedCompletion completion) throws IOException {
            consume(witness);
            try { verifyCompletion(witness, completion); if (!completion.isError()) throw new IOException("Actual known tool error required"); }
            catch (IOException | RuntimeException failure) { phase = Phase.UNKNOWN; throw failure; }
        }
        private void consume(CallWitness witness) throws IOException {
            if (witness == null || witness.issuer != this || witness != pending || witness.consumed) throw new IOException("Original unconsumed pre-call witness required");
            witness.consumed = true; pending = null;
        }
        private void verifyCompletion(CallWitness witness, RootMcpSemanticClient.OwnedCompletion completion) throws IOException {
            requireActive(); requireTransport(channel); Objects.requireNonNull(completion);
            requireArrival(completion.actualArrival(), completion.originalRpcLine().bytes());
            if (!completion.child().equals(channel.identity()) || !completion.sessionNonce().equals(channel.sessionNonce())
                    || completion.arrivalDeadline().isAfter(witness.deadline) || !Instant.now().isBefore(witness.deadline)
                    || completion.ownerRow().sequence() != witness.sequence
                    || completion.ownerRow().startedAtUtc().isBefore(witness.started)
                    || completion.ownerRow().endedAtUtc().isAfter(witness.deadline)) throw new IOException("Actual completion differs from original bounded Root call");
        }
        private void requireArrival(WindowsJobProcess.Arrival arrival, byte[] originalRpc) throws IOException {
            verifyArrival(arrival, originalRpc); lastArrival = arrival.sequence();
        }
        private void verifyArrival(WindowsJobProcess.Arrival arrival, byte[] originalRpc) throws IOException {
            if (arrival == null || !arrival.identity().equals(channel.identity()) || !arrival.sessionNonce().equals(channel.sessionNonce())
                    || arrival.sequence() <= lastArrival || !Arrays.equals(arrival.rawBytes(), originalRpc)
                    || !Instant.now().isBefore(arrival.deadline())) throw new IOException("Original same owned-pipe arrival custody required");
        }
        private String validateDiagnostics(JsonNode diagnostics, String expectedGeneration) throws IOException {
            if (!bool(diagnostics, "connected") || !text(diagnostics, "pipe_name").equals(game.pipeName())
                    || integer(diagnostics, "bridge_pid", BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact() != game.identity().pid()) throw new IOException("Native diagnostics differ from held Game/endpoint");
            String current = integer(diagnostics, "connection_generation", BigInteger.ONE, StrictJson.UINT64_MAX).toString();
            JsonNode hello = object(diagnostics.get("hello"));
            if (integer(hello, "pid", BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact() != game.identity().pid()
                    || !integer(hello, "connection_generation", BigInteger.ONE, StrictJson.UINT64_MAX).toString().equals(current)
                    || expectedGeneration != null && !expectedGeneration.equals(current)
                    || !bool(hello, "ck3_build_match") || !text(hello, "expected_ck3_version").equals(version)
                    || !text(hello, "expected_ck3_sha256").equalsIgnoreCase(game.runtime().request().gameExecutable().sha256())) throw new IOException("Actual Native hello/version/connection differs from original Root binding");
            return current;
        }
        private void requireActive() throws IOException { if (phase != Phase.ACTIVE) throw new IOException("Native capabilities not qualified or session terminal"); }
        @Override public synchronized void close() throws IOException { if (phase != Phase.CLOSED) { phase = Phase.CLOSED; pending = null; endpoint.close(); } }
    }

    public static NativeAdmission prepare(RootColdResumeSession.HeldGame game, WindowsJobProcess.OwnedStdio channel,
            EndpointLocator locator, SourcePlan plan) throws IOException {
        reserve(channel); return prepareReserved(game, channel, Optional.of(locator), plan);
    }
    /** Missing locator is a known pre-operation refusal. The actual route consumes the owned notice. */
    public static NativeAdmission prepare(RootColdResumeSession.HeldGame game, WindowsJobProcess.OwnedStdio channel,
            SourcePlan plan) throws IOException {
        throw new IOException("Actual original owner HANDLE notification required before Native preparation");
    }
    private static synchronized void reserve(WindowsJobProcess.OwnedStdio channel) throws IOException {
        Objects.requireNonNull(channel);
        if (CONSUMED_CHANNELS.putIfAbsent(channel, Boolean.TRUE) != null) throw new IOException("Original owned MCP channel already consumed by Native factory; no admission reset");
    }
    private static NativeAdmission prepareReserved(RootColdResumeSession.HeldGame game, WindowsJobProcess.OwnedStdio channel,
            Optional<EndpointLocator> locator, SourcePlan plan) throws IOException {
        return prepareReserved(game,channel,locator,Optional.empty(),plan);
    }
    private static NativeAdmission prepareReserved(RootColdResumeSession.HeldGame game, WindowsJobProcess.OwnedStdio channel,
            Optional<EndpointLocator> locator, Optional<NativeServerLocator.Received> notification, SourcePlan plan) throws IOException {
        Objects.requireNonNull(game); Objects.requireNonNull(channel); Objects.requireNonNull(locator); Objects.requireNonNull(plan);
        game.runtime().requireColdResumeSession(game.session()); game.session().requireNativeOwner(channel);
        game.verify(); game.runtime().requireOwner(channel);
        if (!plan.expectedEpisode().equals(Optional.of(game.session().savedFrame().episodeRunId())))
            throw new IOException("Source plan must retain the genuine original saved episode");
        for (var source : plan.runtimeSources()) {
            if (game.runtime().completeSources().stream().noneMatch(ref -> source.source().equals(new ExactRef(ref.path(), ref.bytes(), ref.sha256()))))
                throw new IOException("Root runtime source is outside the accepted exact frozen closure");
        }
        if (!plan.launcherSettings().equals(new ExactRef(game.runtime().request().launcherSettings().path(),
                game.runtime().request().launcherSettings().bytes(), game.runtime().request().launcherSettings().sha256()))) throw new IOException("Root source plan differs from retained launcher source");
        G2WindowsReadOnlyObservation observer = new G2WindowsReadOnlyObservation();
        G2WindowsReadOnlyObservation.FileRead launcher = observer.read(Path.of(plan.launcherSettings().path()), StrictJson.EXPLICIT_MAX_BYTES);
        if (!launcher.observation().reference().equals(plan.launcherSettings())) throw new IOException("Root launcher version source differs");
        String version = text(object(parse(launcher.bytes(), StrictJson.EXPLICIT_MAX_BYTES)), "rawVersion");
        WindowsPreloadCustody.Endpoint endpoint;
        if(notification.isPresent()) endpoint=notification.orElseThrow().retain(game.custody());
        else if(locator.isPresent()) endpoint=game.custody().retainOwnerServer(channel,locator.orElseThrow().serverHandleDecimal(),game.pipeName());
        else throw new IOException("Actual original owner HANDLE notification required; no handle-table discovery fallback");
        NativeAdmission admission = new NativeAdmission(game, channel, endpoint, plan, version);
        try { admission.requireTransport(channel); return admission; }
        catch (IOException | RuntimeException failure) {
            try { admission.close(); } catch (IOException closeFailure) { failure.addSuppressed(closeFailure); }
            throw failure;
        }
    }
    /** Bounded read-only readiness; never reconnects, reloads, resumes or launches anything. */
    public static NativeAdmission prepareWhenReady(RootColdResumeSession.HeldGame game, WindowsJobProcess.OwnedStdio channel,
            EndpointLocator locator, SourcePlan plan, Instant deadline) throws IOException {
        return prepareWhenReadyReserved(game, channel, Optional.of(locator), plan, deadline);
    }
    public static NativeAdmission prepareWhenReady(RootColdResumeSession.HeldGame game, WindowsJobProcess.OwnedStdio channel,
            SourcePlan plan, Instant deadline) throws IOException {
        throw new IOException("Actual original owner HANDLE notification required before Native preparation");
    }
    public static NativeAdmission prepareWhenReady(RootColdResumeSession.HeldGame game, WindowsJobProcess.OwnedStdio channel,
            NativeServerLocator.Received notification, SourcePlan plan, Instant deadline) throws IOException {
        Objects.requireNonNull(notification);
        if(!notification.ownerIdentity().equals(channel.identity()) || !notification.sessionNonce().equals(channel.sessionNonce())
                || !notification.pipeName().equals(game.pipeName())) throw new IOException("Original owned startup notification differs from actual Game/owner session");
        return prepareWhenReadyReserved(game,channel,Optional.empty(),Optional.of(notification),plan,deadline);
    }
    private static NativeAdmission prepareWhenReadyReserved(RootColdResumeSession.HeldGame game, WindowsJobProcess.OwnedStdio channel,
            Optional<EndpointLocator> locator, SourcePlan plan, Instant deadline) throws IOException {
        return prepareWhenReadyReserved(game,channel,locator,Optional.empty(),plan,deadline);
    }
    private static NativeAdmission prepareWhenReadyReserved(RootColdResumeSession.HeldGame game, WindowsJobProcess.OwnedStdio channel,
            Optional<EndpointLocator> locator, Optional<NativeServerLocator.Received> notification, SourcePlan plan, Instant deadline) throws IOException {
        reserve(channel);
        Objects.requireNonNull(deadline);
        if (deadline.isAfter(game.deadline())) throw new IOException("Native readiness exceeds original Game lease");
        IOException last = null;
        while (Instant.now().isBefore(deadline)) {
            game.runtime().requireColdResumeSession(game.session()); game.session().requireNativeOwner(channel);
            game.verify(); game.runtime().requireOwner(channel); channel.verifyActualIdentityAndSources();
            try { return prepareReserved(game, channel, locator, notification, plan); }
            catch (WindowsPreloadCustody.PipeNotConnected notReady) { last = notReady; }
            try { Thread.sleep(Math.min(100, Math.max(1, java.time.Duration.between(Instant.now(), deadline).toMillis()))); }
            catch (InterruptedException failure) { Thread.currentThread().interrupt(); throw new IOException("Native readiness interrupted; no action repeated", failure); }
        }
        throw new IOException("Actual Native endpoint/loaded-source readiness unavailable before deadline", last);
    }
    private static JsonNode parse(byte[] raw, int limit) throws IOException {
        if (raw.length < 1 || raw.length > limit || raw.length >= 3 && raw[0] == (byte) 0xef && raw[1] == (byte) 0xbb && raw[2] == (byte) 0xbf) throw new IOException("Bounded original UTF8 JSON required");
        for (byte value : raw) if (value == 0) throw new IOException("Original Native UTF8 contains NUL");
        String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
        return JSON.readTree(text);
    }
    private static JsonNode object(JsonNode value) throws IOException { if (value == null || !value.isObject()) throw new IOException("Native object required"); return value; }
    private static String text(JsonNode value, String key) throws IOException { JsonNode field = value.get(key); if (field == null || !field.isTextual() || field.textValue().isBlank()) throw new IOException("Native text required: " + key); return field.textValue(); }
    private static boolean bool(JsonNode value, String key) throws IOException { JsonNode field = value.get(key); if (field == null || !field.isBoolean()) throw new IOException("Native boolean required: " + key); return field.booleanValue(); }
    private static BigInteger integer(JsonNode value, String key, BigInteger minimum, BigInteger maximum) throws IOException {
        JsonNode field = value.get(key); if (field == null || !field.isIntegralNumber()) throw new IOException("Native integer required: " + key);
        BigInteger number = field.bigIntegerValue(); if (number.compareTo(minimum) < 0 || number.compareTo(maximum) > 0) throw new IOException("Native integer out of range: " + key); return number;
    }
}
