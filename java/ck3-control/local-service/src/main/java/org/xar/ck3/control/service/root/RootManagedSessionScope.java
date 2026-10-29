package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.platform.ManagedGameSession;

/** Physical Java origin only: no store clearance, action permission, writer or native submission is issued. */
public final class RootManagedSessionScope {
    public static final String SCHEMA = "xar.java.managed-root-session-observation/v1";
    public static final int MAX_BYTES = 65536;
    private final RootRuntimeContext context;
    private final RootApplicationAssembly.Core core;
    private final ManagedGameSession game;
    private final NativeGameTransport transport;
    private final G2Source source;
    private final String sessionId;
    private final List<ExactRef> implementationSources;
    private final ThreadLocal<Lease> active = new ThreadLocal<>();

    private RootManagedSessionScope(RootRuntimeContext context,
            List<ExactRef> implementationSources) throws IOException {
        this.context = Objects.requireNonNull(context);
        this.core = context.core(); this.game = context.game(); this.source = context.source();
        this.sessionId = game.sessionId(); this.implementationSources = checkedSources(implementationSources);
        game.verify(); transport = game.nativeTransport();
        requireOwner();
    }
    /** Retains the actual Root's opaque Java-created Game. This does not install or authorize any domain operation. */
    public static RootManagedSessionScope bind(RootRuntimeContext context,
            List<ExactRef> implementationSources) throws IOException {
        return new RootManagedSessionScope(context, implementationSources);
    }
    private void requireOwner() throws IOException {
        need(context.core() == core && context.game() == game && context.writer() == core.writer()
                && context.archive() == core.archive() && context.source().equals(source)
                && game.sessionId().equals(sessionId), "Managed scope crossed its original Core/Game/source/session");
        game.verify();
        need(game.nativeTransport() == transport, "Managed scope crossed its original Native transport");
    }
    private final class Lease implements AutoCloseable {
        private final Thread thread = Thread.currentThread();
        private boolean closed;
        private Complete frame;
        private void requireCurrent() throws IOException {
            need(!closed && Thread.currentThread() == thread && active.get() == this,
                    "Managed scope is closed, recursive or on another thread");
            requireOwner();
            context.adopted().producer().requireSameTransport(transport, source);
        }
        @Override public void close() { closed = true; }
    }
    @FunctionalInterface public interface Work<T> { T run() throws IOException, InterruptedException; }
    public <T> T withScope(Work<T> work) throws IOException, InterruptedException {
        Objects.requireNonNull(work);
        need(active.get() == null, "Managed scope may not replace an active original lease");
        try (Lease lease = new Lease()) {
            active.set(lease);
            try { lease.requireCurrent(); T value = work.run(); lease.requireCurrent(); return value; }
            finally { active.remove(); }
        }
    }
    public void requireCurrent() throws IOException {
        Lease lease = active.get(); need(lease != null, "Actual managed-session scope required");
        lease.requireCurrent();
    }
    public void requireFrame(Session same, Complete actual) throws IOException {
        requireCurrent(); context.writer().requireSession(same);
        context.collector().requireHeldFrame(same, actual);
        need(actual.identity().game().equals(game.generation()) && actual.source().equals(source)
                && actual.sessionId().equals(sessionId)
                && actual.identity().machineId().equals(game.machineId()), "Frame crossed the held Java native session");
        active.get().frame = actual;
    }
    public byte[] observe(Session same, Complete actual) throws IOException {
        requireFrame(same, actual); var head = same.head();
        Observation observed = new Observation(game.machineId(), sessionId, actual.identity(), source,
                game.launchPlan().requestId(), game.launchPlan().stateDirectory(), game.launchPlan().profileDirectory(),
                context.writer().originalLockPath(), implementationSources, head.state().sequence(), head.digest(), Optional.empty());
        byte[] raw = encode(observed); requireCurrent(); context.writer().requireSession(same); return raw;
    }
    public byte[] observe(Session same, ActionCommand command) throws IOException {
        requireCurrent(); context.writer().requireSession(same);
        need(command != null && command.origin() instanceof CommandOrigin.Gameplay && command.before().game().equals(game.generation())
                && command.source().equals(source) && command.sessionId().equals(sessionId),
                "Managed scope observation does not belong to its actual original command");
        Complete originalFrame = active.get().frame;
        need(originalFrame != null && originalFrame.identity().equals(command.before()), "Actual held frame was not bound to this original command");
        context.collector().requireHeldFrame(same, originalFrame);
        var head = same.head();
        Observation observed = new Observation(game.machineId(), sessionId, command.before(), source,
                game.launchPlan().requestId(), game.launchPlan().stateDirectory(), game.launchPlan().profileDirectory(),
                context.writer().originalLockPath(), implementationSources, head.state().sequence(), head.digest(),
                Optional.of(ActionCodec.bodySha256(command)));
        byte[] raw = encode(observed);
        need(decode(raw, command, implementationSources).equals(observed), "Managed observation producer/decoder differ");
        requireCurrent(); context.writer().requireSession(same); return raw;
    }
    /** Pure association of already captured frame DATA to the later exact command; never a live scope issuer. */
    public static byte[] bindCommand(byte[] originalFrameObservation, ActionCommand command,
            List<ExactRef> expectedSources) {
        Observation frame = decode(originalFrameObservation, command, expectedSources);
        need(frame.actionBodySha256().isEmpty(), "Original frame-only observation required; command bindings cannot be replaced");
        return encode(new Observation(frame.machineId(), frame.sessionId(), frame.before(), frame.source(),
                frame.lifecycleRequestId(), frame.stateDirectory(), frame.profileDirectory(), frame.writerLock(),
                frame.implementationSources(), frame.headSequence(), frame.headDigest(), Optional.of(ActionCodec.bodySha256(command))));
    }
    /** Replay checks a real canonical predecessor in the same writer; DATA is not a new live lease. */
    public void verifyArchived(byte[] original, ActionCommand command, String actualCaptureHead) throws IOException {
        verifyArchived(original, command, implementationSources, actualCaptureHead);
    }
    public void verifyArchived(byte[] original, ActionCommand command, List<ExactRef> expectedSources,
            String actualCaptureHead) throws IOException {
        need(checkedSources(expectedSources).equals(implementationSources), "Archived business source closure differs from this actual binding");
        context.withSession(same -> {
            verifyArchived(core,same,original,command,implementationSources,actualCaptureHead);
            return null;
        });
    }
    /** Historical DATA consumer; requires the real original Core/Session, but no living Game or new scope. */
    public static Observation verifyArchived(RootApplicationAssembly.Core actualCore, Session same, byte[] original,
            ActionCommand command, List<ExactRef> expectedSources, String actualCaptureHead) throws IOException {
        Objects.requireNonNull(actualCore); actualCore.writer().requireSession(same);
        need(actualCore.archive().writer()==actualCore.writer(), "Historical managed observation crossed the original writer/archive");
        Observation observed = decode(original,command,expectedSources);
        need(observed.actionBodySha256().isPresent()&&observed.headDigest().equals(actualCaptureHead),
                "Command-bound original managed observation and exact census predecessor required");
        need(observed.writerLock().equals(actualCore.writer().originalLockPath()), "Managed archived writer differs");
        var originalHead=same.requireHistoricalState(observed.headSequence(),observed.headDigest());
        need(originalHead.machineId().equals(observed.machineId()), "Managed predecessor machine differs");
        actualCore.writer().requireSession(same);return observed;
    }

    /** Pure archive DATA. Constructing or decoding this record cannot issue authority or access a store/process. */
    public record Observation(String machineId, String sessionId, ObservationIdentity before, G2Source source,
            String lifecycleRequestId, Path stateDirectory, Path profileDirectory, Path writerLock,
            List<ExactRef> implementationSources, long headSequence, String headDigest, Optional<String> actionBodySha256) {
        public Observation {
            Objects.requireNonNull(before); Objects.requireNonNull(source);
            need(machineId != null && machineId.matches("[a-z0-9][a-z0-9-]{0,63}") && !machineId.equals("unknown")
                    && machineId.equals(before.machineId()) && machineId.equals(source.machineId()), "Known same Java source machine required");
            need(sessionId != null && sessionId.matches("[A-Za-z0-9_-]{1,128}")
                    && lifecycleRequestId != null && lifecycleRequestId.matches("[A-Za-z0-9_-]{1,128}"), "Exact Java launch/session identities required");
            stateDirectory = exactPath(stateDirectory); profileDirectory = exactPath(profileDirectory); writerLock = exactPath(writerLock);
            implementationSources = checkedSources(implementationSources);
            need(headSequence >= 0 && headDigest != null && headDigest.matches("[0-9a-f]{64}"), "Actual canonical writer predecessor required");
            Objects.requireNonNull(actionBodySha256); actionBodySha256.ifPresent(hash -> need(hash.matches("[0-9a-f]{64}"), "Exact original action body digest required"));
        }
    }
    public static byte[] encode(Observation value) {
        Objects.requireNonNull(value);
        ObjectNode n = StrictJson.object().put("schema", SCHEMA).put("kind", "JAVA_MANAGED_NATIVE_SESSION")
                .put("machine_id", value.machineId()).put("session_id", value.sessionId())
                .put("lifecycle_request_id", value.lifecycleRequestId()).put("state_directory", value.stateDirectory().toString())
                .put("profile_directory", value.profileDirectory().toString()).put("writer_lock", value.writerLock().toString())
                .put("head_sequence", Long.toString(value.headSequence())).put("head_digest", value.headDigest())
                .put("binding", value.actionBodySha256().isPresent()?"COMMAND_BOUND":"FRAME_ONLY");
        if(value.actionBodySha256().isPresent())n.put("action_body_sha256",value.actionBodySha256().orElseThrow());else n.putNull("action_body_sha256");
        n.set("before", ProposalLifecycleCodec.observation(value.before())); n.set("source", ProposalLifecycleCodec.source(value.source()));
        var sources = n.putArray("implementation_sources"); value.implementationSources().forEach(ref -> sources.add(ref.toJson()));
        return StrictJson.canonical(n, MAX_BYTES);
    }
    public static Observation decode(byte[] original, ActionCommand expected, List<ExactRef> expectedSources) {
        Objects.requireNonNull(expected); List<ExactRef> required = checkedSources(expectedSources);
        ObjectNode n = StrictJson.object(StrictJson.parse(original, MAX_BYTES), Set.of("schema", "kind", "machine_id",
                "session_id", "lifecycle_request_id", "state_directory", "profile_directory", "writer_lock",
                "head_sequence", "head_digest", "before", "source", "implementation_sources", "binding", "action_body_sha256"));
        need(SCHEMA.equals(StrictJson.text(n.get("schema"))) && "JAVA_MANAGED_NATIVE_SESSION".equals(StrictJson.text(n.get("kind"))),
                "Exact Java managed-session observation branch required");
        JsonNode rows = n.get("implementation_sources"); need(rows.isArray() && rows.size() > 0 && rows.size() <= 16,
                "Complete actual implementation source closure required");
        var refs = new ArrayList<ExactRef>(); rows.forEach(row -> refs.add(ExactRef.fromJson(row)));
        String sequence = StrictJson.text(n.get("head_sequence"));
        need(sequence.matches("0|[1-9][0-9]{0,18}"), "Canonical Java writer sequence decimal string required");
        BigInteger parsedSequence = new BigInteger(sequence); need(parsedSequence.compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0, "Writer sequence overflows its original signed-long domain");
        long head = parsedSequence.longValueExact();
        String binding = StrictJson.text(n.get("binding")); Optional<String> body;
        if("COMMAND_BOUND".equals(binding))body=Optional.of(StrictJson.text(n.get("action_body_sha256")));
        else {need("FRAME_ONLY".equals(binding)&&n.get("action_body_sha256").isNull(),"Exact frame-only observation branch required");body=Optional.empty();}
        Observation actual = new Observation(StrictJson.text(n.get("machine_id")), StrictJson.text(n.get("session_id")),
                ProposalLifecycleCodec.decodeObservation(n.get("before")), G2Wire.source(n.get("source")),
                StrictJson.text(n.get("lifecycle_request_id")), Path.of(StrictJson.text(n.get("state_directory"))),
                Path.of(StrictJson.text(n.get("profile_directory"))), Path.of(StrictJson.text(n.get("writer_lock"))),
                refs, head, StrictJson.text(n.get("head_digest")), body);
        need(actual.before().equals(expected.before()) && actual.source().equals(expected.source())
                && actual.sessionId().equals(expected.sessionId()) && actual.implementationSources().equals(required),
                "Managed observation differs from the original command or selected source closure");
        actual.actionBodySha256().ifPresent(hash -> need(hash.equals(ActionCodec.bodySha256(expected)), "Managed observation belongs to another action body"));
        return actual;
    }
    private static Path exactPath(Path value) {
        Objects.requireNonNull(value);
        need(value.isAbsolute() && value.normalize().equals(value) && !value.toString().startsWith("\\\\?\\")
                && value.toString().indexOf('\0') < 0, "Exact absolute Java runtime path required");
        return value;
    }
    private static List<ExactRef> checkedSources(List<ExactRef> sources) {
        List<ExactRef> result = List.copyOf(sources);
        need(!result.isEmpty() && result.size() <= 16 && result.stream().distinct().count() == result.size()
                && result.stream().allMatch(ref -> ref.bytes() > 0), "Complete unique actual business producer sources required");
        return result;
    }
    private static void need(boolean value, String reason) { StrictJson.require(value, reason); }
}
