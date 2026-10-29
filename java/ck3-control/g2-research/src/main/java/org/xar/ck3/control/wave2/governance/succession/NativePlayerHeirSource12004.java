package org.xar.ck3.control.wave2.governance.succession;

import static org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.context.G2CallContextProducer;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.RootOwnedSources;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.Session;

/** Bounded read of Root-selected originals. Same provider as other G2 consumers; zero RPC or writes. */
public final class NativePlayerHeirSource12004 {
    public sealed interface Result permits Observed, Unavailable { }
    public record Observed(Session session, Frame frame, BigInteger querySequence, Parsed component, G2Source source,
            ExactRef originalRootResult) implements Result {
        public Observed {
            Objects.requireNonNull(session); Objects.requireNonNull(frame); Objects.requireNonNull(component);
            Objects.requireNonNull(source); Objects.requireNonNull(originalRootResult);
            StrictJson.require(querySequence != null && querySequence.signum() > 0
                    && querySequence.compareTo(StrictJson.UINT64_MAX) <= 0, "positive original root query sequence required");
        }
    }
    public record Unavailable(String reason) implements Result {
        public Unavailable { StrictJson.text(reason); StrictJson.require(reason.length() <= 1024, "bounded rejection required"); }
    }
    public enum PairState { SELECTED_PLAYER_HEIR_NOW_CONTROLLED, CANDIDATE_NOT_OBSERVED, CONTROL_DIFFERS, GAME_CHANGED, FRAME_REGRESSED, EPISODE_NOT_REBOUND }
    /** Observation pair only. Natural death, modal legality, title outcome and saved continuation remain separate. */
    public record ControlPair(PairState state, Observed before, Observed after) {
        public ControlPair { Objects.requireNonNull(state); Objects.requireNonNull(before); Objects.requireNonNull(after); }
        public boolean submissionAuthorized() { return false; }
        public boolean naturalDeathProven() { return false; }
        public boolean realmPreservationProven() { return false; }
    }
    private NativePlayerHeirSource12004() { }

    public static Result read(RootOwnedSources owner, G2RetainedNativeSourceProvider.Limits limits, ExactRef rootResult) {
        Objects.requireNonNull(owner); Objects.requireNonNull(limits); Objects.requireNonNull(rootResult);
        ObjectNode request = StrictJson.object(); request.put("schema", "xar.java.player-heir-original-root-request12004/v1");
        request.set("root_result", rootResult.toJson());
        ProjectionJson token = ProjectionJson.object(StrictJson.canonical(request), 16384);
        try {
            var selected = owner.selectedSource(Milestone.M3, token);
            if (selected.isEmpty()) return new Unavailable("root_selected_original_snapshot_missing");
            var artifact = selected.orElseThrow();
            G2CallContextProducer.Result qualified = new G2RetainedNativeSourceProvider(owner, limits).context(Milestone.M3, token);
            if (qualified instanceof G2CallContextProducer.Unavailable rejected) return unavailable(rejected.reason() + ":" + rejected.detail());
            var context = ((G2CallContextProducer.Available) qualified).context();
            StrictJson.require(context.source().sourceRef().equals(artifact.nativeObservation())
                    && artifact.retainedSession().executable().sha256().equals(EXE_SHA256), "exact .4 selected original required");
            byte[] original = exact(owner, artifact.nativeObservation(), Math.min(limits.nativeArtifactBytes(), MAX_BYTES));
            JsonNode snapshot = field(field(StrictJson.parse(original, MAX_BYTES), "result"), "structured_content");
            JsonNode actor = field(snapshot, "played_character");
            StrictJson.trueValue(field(snapshot, "paused")); StrictJson.trueValue(field(snapshot, "map_ready"));
            StrictJson.trueValue(field(actor, "alive"));
            byte[] rawRoot = exact(owner, rootResult, MAX_BYTES);
            JsonNode rootEnvelope = StrictJson.parse(rawRoot, MAX_BYTES);
            JsonNode root = field(rootEnvelope, "campaign_root_context");
            Frame frame = new Frame(text(snapshot, "snapshot_id"), uint(snapshot, "revision", false),
                    uint(snapshot, "native_revision", true), signed(snapshot, "date_raw"), signed(actor, "character_id"),
                    signed(root, "local_player_id"));
            Parsed observation = parse(rawRoot, frame);
            StrictJson.require(artifact.retainedSession().episodeRunId().equals(text(snapshot, "episode_run_id")), "original episode changed");
            StrictJson.require(Arrays.equals(rawRoot, exact(owner, rootResult, MAX_BYTES))
                    && Arrays.equals(original, exact(owner, artifact.nativeObservation(), Math.min(limits.nativeArtifactBytes(), MAX_BYTES)))
                    && owner.currentSession().equals(Optional.of(artifact.retainedSession()))
                    && owner.selectedSource(Milestone.M3, token).equals(selected), "original source/session changed while reading");
            return new Observed(artifact.retainedSession(), frame, uint(rootEnvelope, "query_sequence", true), observation, context.source(), rootResult);
        } catch (IOException | IllegalArgumentException failure) {
            return unavailable(failure.getMessage() == null ? "original player-heir source read failed" : failure.getMessage());
        }
    }

    /** A new episode must be an observed fact, never predicted by the selected heir or title roster. */
    public static ControlPair compareControl(Observed before, Observed after) {
        Objects.requireNonNull(before); Objects.requireNonNull(after);
        if (!sameGame(before.session(), after.session())) return pair(PairState.GAME_CHANGED, before, after);
        Frame first = before.frame(), last = after.frame();
        if (last.dateRaw() < first.dateRaw() || last.publicRevision().compareTo(first.publicRevision()) < 0
                || last.nativeRevision().compareTo(first.nativeRevision()) < 0) return pair(PairState.FRAME_REGRESSED, before, after);
        if (before.component().state() != State.LIVING_CANDIDATE) return pair(PairState.CANDIDATE_NOT_OBSERVED, before, after);
        int selected = before.component().component().observation().candidateCharacterId();
        if (selected != last.actorCharacterId() || last.actorCharacterId() == first.actorCharacterId()) return pair(PairState.CONTROL_DIFFERS, before, after);
        if (before.session().episodeRunId().equals(after.session().episodeRunId())) return pair(PairState.EPISODE_NOT_REBOUND, before, after);
        return pair(PairState.SELECTED_PLAYER_HEIR_NOW_CONTROLLED, before, after);
    }
    private static boolean sameGame(Session a, Session b) {
        return a.machineId().equals(b.machineId()) && a.sessionId().equals(b.sessionId()) && a.game().equals(b.game())
                && a.connectionGeneration().equals(b.connectionGeneration()) && a.executable().equals(b.executable())
                && a.executableFileId().equals(b.executableFileId()) && a.executableMtimeNs().equals(b.executableMtimeNs());
    }
    private static ControlPair pair(PairState state, Observed a, Observed b) { return new ControlPair(state, a, b); }
    private static byte[] exact(RootOwnedSources owner, ExactRef ref, int maximum) throws IOException {
        StrictJson.require(ref.bytes() > 0 && ref.bytes() <= maximum, "bounded original source required");
        byte[] raw = owner.readExact(ref, maximum);
        StrictJson.require(raw != null && raw.length == ref.bytes() && ref.sha256().equals(G2RetainedNativeSourceProvider.sha256(raw)),
                "original source exact bytes/SHA differ");
        return raw;
    }
    private static Unavailable unavailable(String reason) { return new Unavailable(reason.substring(0, Math.min(reason.length(), 1024))); }
}
