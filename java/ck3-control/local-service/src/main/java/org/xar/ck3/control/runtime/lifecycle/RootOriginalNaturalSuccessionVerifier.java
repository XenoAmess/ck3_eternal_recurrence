package org.xar.ck3.control.runtime.lifecycle;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.lifecycle.LifecycleObservationPort;
import org.xar.ck3.control.application.lifecycle.NaturalSuccessionVerifier;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.Session;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerTerminalQueries;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Frame;
import org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerMaterial12004;

/** Re-derives the M3 leaves from retained originals during lifecycle's original writer transaction. */
public final class RootOriginalNaturalSuccessionVerifier implements NaturalSuccessionVerifier {
    /** Root owns the actual lease, archive, loaded-source/epoch and actor authority. There is no permissive implementation here. */
    public interface RootOriginals {
        /**
         * Hold the actual parent action/writer lease; verify the supplied head is the actual held head.
         * Resolve the original engine-clock transition and exclude a manual/control-switch/reload origin.
         * Qualify each original against the actual loaded .4 DLL, source epoch, connection and Game.
         * Unknown cause, missing predecessor capture or absent qualification must throw IOException.
         */
        Originals openQualified(ActionCommand parent, LifecycleObservationPort.Snapshot actual,
                WriterContracts.Head actualWriter) throws IOException;
        byte[] readExact(ExactRef original) throws IOException;
        /** Re-resolve the same retained object/cause, original request/ACK/archive, head, source and actor after all leaf reads. */
        void requireCurrent(Originals original, ActionCommand parent, LifecycleObservationPort.Snapshot actual,
                WriterContracts.Head actualWriter) throws IOException;
    }
    /** Data returned by the Root port is never authority by construction; openQualified/requireCurrent remain mandatory. */
    public record Packet(ExactRef original, String requestId, Frame actualFrame, NativeTimelineBlocker12004.Scene actualScene) {
        public Packet { Objects.requireNonNull(original); StrictJson.text(requestId); Objects.requireNonNull(actualFrame); Objects.requireNonNull(actualScene); }
    }
    public record Originals(Session session, Frame predecessorFrame, ExactRef predecessorRoot,
            ExactRef engineClockAndActorProof, PlanningReadReceipt predecessorDeath,
            Packet initialTimeline, Optional<Packet> close, List<Packet> subsequentTimeline) {
        public Originals {
            Objects.requireNonNull(session); Objects.requireNonNull(predecessorFrame); Objects.requireNonNull(predecessorRoot);
            Objects.requireNonNull(engineClockAndActorProof); Objects.requireNonNull(predecessorDeath);
            Objects.requireNonNull(initialTimeline); Objects.requireNonNull(close); subsequentTimeline = List.copyOf(subsequentTimeline);
            StrictJson.require(close.isPresent() ? !subsequentTimeline.isEmpty() && subsequentTimeline.size() <= 8
                    : subsequentTimeline.isEmpty(), "native Close has one to eight actual postqueries; no-Close has no synthetic postqueries");
        }
    }
    private final RootOriginals root;
    public RootOriginalNaturalSuccessionVerifier(RootOriginals actualRootOriginals) {
        root = Objects.requireNonNull(actualRootOriginals);
    }
    @Override public String verify(ActionCommand parent, LifecycleObservationPort.Snapshot actual,
            WriterContracts.Head actualWriter) throws IOException {
        Objects.requireNonNull(parent); Objects.requireNonNull(actual); Objects.requireNonNull(actualWriter);
        try {
            StrictJson.require(parent.operation().value().equals("continue-as-reconciled-successor"), "natural continuation parent required");
            Originals held = Objects.requireNonNull(root.openQualified(parent, actual, actualWriter));
            var transport = actual.actual().session(); Session session = held.session();
            StrictJson.require(session.machineId().equals(transport.machineId()) && session.sessionId().equals(transport.sessionId())
                    && session.game().pid() == transport.game().pid()
                    && session.game().creationFiletime().equals(transport.game().creationFiletime().value().toString())
                    && session.connectionGeneration().equals(transport.connectionGeneration().toString())
                    && session.episodeRunId().equals(actual.facts().driver().session().episodeRunId())
                    && session.executable().sha256().equals(NativePlayerHeirObservation12004.EXE_SHA256)
                    && parent.source().equals(actual.source()), "actual held Game/session/source/episode differs");
            JsonNode semantic = OpportunityJson.toNode(actual.semantic());
            JsonNode player = required(semantic, "played_character"); StrictJson.trueValue(required(player, "alive"));
            int successor = (int) StrictJson.integer(required(player, "character_id"), 1, Integer.MAX_VALUE);
            int predecessor = actual.facts().driver().session().actorId().intValueExact();
            StrictJson.require(predecessor > 0 && predecessor != successor
                    && "played_character_changed".equals(StrictJson.text(required(semantic, "one_life_terminal_reason")))
                    && actual.paused() && actual.mapReady(), "actual paused living controlled successor required");
            Frame before = held.predecessorFrame();
            StrictJson.require(before.actorCharacterId() == predecessor && actual.dateRaw().compareTo(BigInteger.valueOf(before.dateRaw())) >= 0,
                    "original predecessor or time differs");
            byte[] rootBytes = exact(held.predecessorRoot());
            requireOriginalPlayerHeir(rootBytes, before, successor);
            Frame now = new Frame(actual.actual().snapshotId(), actual.revision(), actual.actual().nativeRevision(),
                    actual.dateRaw().intValueExact(), successor, before.localPlayerId());
            var deathReceipt = held.predecessorDeath(); var deathRequest = deathReceipt.request();
            var terminal = deathRequest.origin().requireLifecycleTerminal(); var deathFrame = terminal.frame();
            StrictJson.require(deathRequest.source().equals(actual.source()) && deathRequest.sessionId().equals(parent.sessionId())
                    && deathReceipt.before().binding().connectionGeneration().equals(transport.connectionGeneration())
                    && deathReceipt.after().binding().connectionGeneration().equals(transport.connectionGeneration())
                    && terminal.machineId().equals(transport.machineId()) && terminal.game().equals(transport.game())
                    && terminal.subject().episodeRunId().equals(session.episodeRunId())
                    && terminal.subject().characterId().intValueExact()==predecessor
                    && terminal.subject().episodeEpoch()==actual.facts().stamp().episodeEpoch()
                    && terminal.subject().driverVersion()==actual.facts().stamp().driverVersion()
                    && deathFrame.revision().compareTo(now.publicRevision())<=0 && deathFrame.nativeRevision().compareTo(now.nativeRevision())<=0
                    && deathFrame.dateRaw().intValueExact()==now.dateRaw() && deathFrame.paused() && deathFrame.mapReady()
                    && terminal.currentPlayer() instanceof LifecycleIdentity.Character controlled
                    && controlled.alive() && controlled.characterId().intValueExact()==successor,
                    "retained predecessor death crossed the actual terminal subject/frame");
            var arguments = PrisonerOptionIntent.decode(OpportunityJson.encode(deathRequest.arguments()));
            StrictJson.require(arguments.materialTarget().isPresent() && arguments.materialTarget().getAsLong() == Integer.toUnsignedLong(predecessor),
                    "original query did not independently retain the predecessor ID");
            var custody = PrisonerTerminalQueries.decode(deathReceipt).retainedCustody();
            StrictJson.require(custody.isPresent() && custody.orElseThrow() instanceof PrisonerMaterial12004.Dead,
                    "actual independently resolved predecessor death unavailable");
            var finalBinding = new NativeTimelineBlocker12004.BoundFrame(session, now,
                    NativeTimelineBlocker12004.Scene.fromSnapshot(semantic));
            var first = query(held.initialTimeline(), session); String clearance;
            if (held.close().isEmpty()) {
                StrictJson.require(first.context().clearedObserved() && NativeTimelineBlocker12004.sameContinuation(first.binding(),finalBinding),
                        "no native surface clearance on the actual continuation observed"); clearance = "already_clear";
            } else {
                Packet close = held.close().orElseThrow();
                var submitted = NativeTimelineBlocker12004.parseClose(exact(close.original()), close.original(), binding(close,session), close.requestId());
                NativeTimelineBlocker12004.Clearance last = null;
                BigInteger lastSequence = first.sequence(), lastObservation = first.observationRevision();
                var lastBinding=submitted.binding();
                for (Packet packet : held.subsequentTimeline()) {
                    var next = query(packet, session);
                    StrictJson.require(next.sequence().compareTo(lastSequence) > 0 && next.observationRevision().compareTo(lastObservation) > 0,
                            "postquery sequence and observation must increase independently");
                    StrictJson.require(NativeTimelineBlocker12004.sameContinuation(lastBinding,next.binding()),"actual postquery frame regressed or changed");
                    lastSequence = next.sequence(); lastObservation = next.observationRevision();
                    lastBinding=next.binding();
                    last = NativeTimelineBlocker12004.compareClearance(first, submitted, next);
                }
                StrictJson.require(last != null && last.state() == NativeTimelineBlocker12004.ClearanceState.CLEARED_OBSERVED
                                && NativeTimelineBlocker12004.sameContinuation(lastBinding,finalBinding),
                        "actual native legal Close and material surface clearance unavailable"); clearance = "legal_close_observed_clear";
            }
            byte[] origin = exact(held.engineClockAndActorProof());
            NaturalEngineClockProof.decode(origin).requireBoundTo(transport.machineId(), actual.actual().observedAt(), actualWriter.digest(), held.predecessorRoot(), actual.originalEvidence());
            StrictJson.require(java.util.Arrays.equals(rootBytes, exact(held.predecessorRoot())), "retained original drift");
            root.requireCurrent(held, parent, actual, actualWriter);
            ObjectNode proof = StrictJson.object(); proof.put("schema", "xar.java.natural-succession-rederived/v1")
                    .put("parent_body_sha256", ActionCodec.bodySha256(parent)).put("writer_head_sha256", actualWriter.digest())
                    .put("predecessor_character_id", predecessor).put("actual_successor_character_id", successor).put("modal", clearance);
            proof.set("predecessor_root", held.predecessorRoot().toJson()); proof.set("engine_clock_actor_authority", held.engineClockAndActorProof().toJson());
            proof.set("actual_snapshot", actual.originalEvidence().toJson()); proof.put("retained_death_request_id", deathReceipt.requestId());
            proof.put("retained_death_original_sha256", G2RetainedNativeSourceProvider.sha256(deathReceipt.original().originalPacket()));
            proof.set("initial_timeline", held.initialTimeline().original().toJson());
            var packets = proof.putArray("subsequent_timeline"); held.subsequentTimeline().forEach(packet -> packets.add(packet.original().toJson()));
            held.close().ifPresent(packet -> proof.set("close", packet.original().toJson()));
            return G2RetainedNativeSourceProvider.sha256(StrictJson.canonical(proof));
        } catch (IllegalArgumentException | ArithmeticException failure) {
            throw new IOException("natural succession remains unqualified: " + failure.getMessage(), failure);
        }
    }
    /**
     * Actual executor material +8 retains Character.GetPlayerHeir, separately from its +4 estate recipient.
     * The original seven-field native root and its independently held frame are required here: title
     * first-heir rows, modal visibility and a static source CALL cannot substitute for this observation.
     * This guard alone grants neither natural cause, source custody, writer authority nor an episode.
     */
    static void requireOriginalPlayerHeir(byte[] originalRoot, Frame before, int controlledSuccessor) {
        Objects.requireNonNull(before);
        StrictJson.require(controlledSuccessor > 0 && controlledSuccessor != before.actorCharacterId(),
                "distinct positive controlled successor required");
        var selected = NativePlayerHeirObservation12004.parseNativeResult(originalRoot, before);
        StrictJson.require(selected.state() == NativePlayerHeirObservation12004.State.LIVING_CANDIDATE
                && selected.component().observation().candidateCharacterId() == controlledSuccessor,
                "actual original GetPlayerHeir is not the controlled successor");
    }
    private NativeTimelineBlocker12004.Query query(Packet packet, Session session) throws IOException {
        return NativeTimelineBlocker12004.parseQuery(exact(packet.original()), packet.original(), binding(packet,session), packet.requestId());
    }
    private static NativeTimelineBlocker12004.BoundFrame binding(Packet packet,Session session) {
        return new NativeTimelineBlocker12004.BoundFrame(session,packet.actualFrame(),packet.actualScene());
    }
    private byte[] exact(ExactRef ref) throws IOException {
        StrictJson.require(ref.bytes() > 0 && ref.bytes() <= NativeTimelineBlocker12004.MAX_BYTES, "bounded original required");
        byte[] bytes = root.readExact(ref);
        if (bytes == null || bytes.length != ref.bytes() || !G2RetainedNativeSourceProvider.sha256(bytes).equals(ref.sha256()))
            throw new IOException("actual original bytes/SHA changed: " + ref.path());
        return bytes.clone();
    }
    private static JsonNode required(JsonNode node, String name) {
        StrictJson.require(node != null && node.isObject() && node.has(name), "missing original field: " + name); return node.get(name);
    }
}
