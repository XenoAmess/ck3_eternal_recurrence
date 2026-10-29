package org.xar.ck3.control.wave3.planning.constructionrelease;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Value;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Frame;
import org.xar.ck3.control.wave3.planning.constructionrelease.ConstructionRelease.AppliedStatus;
import org.xar.ck3.control.wave3.planning.constructionrelease.ConstructionRelease.Details;
import org.xar.ck3.control.wave3.planning.constructionrelease.ConstructionRelease.Flag;
import org.xar.ck3.control.wave3.planning.constructionrelease.ConstructionRelease.PriorReceipt;
import org.xar.ck3.control.wave3.planning.constructionrelease.ConstructionRelease.ProcessObservation;

/** Original receipt and identity-adapter observations enter here; no wire release or process-match flag exists. */
public final class ConstructionReleaseCodec {
    public static final String SCHEMA = "xar.java.m5-construction-release.v1";
    private ConstructionReleaseCodec() { }
    public record Request(Frame frame, PriorReceipt applied, ProcessObservation processObservation) {
        public Request { Objects.requireNonNull(frame); Objects.requireNonNull(applied); Objects.requireNonNull(processObservation); }
    }
    public static Request decode(byte[] raw) {
        Obj root = object(OpportunityJson.parse(raw), "request");
        exact(root, Set.of("schema", "frame", "applied", "process_observation"));
        require(text(root.get("schema"), "schema").equals(SCHEMA), "unsupported construction release schema");
        Obj rawFrame = object(root.get("frame"), "frame");
        exact(rawFrame, Set.of("played_character_id", "native_revision", "date_raw", "snapshot_id", "revision", "episode_run_id"));
        Frame frame = new Frame(integer(rawFrame.get("played_character_id"), "played_character_id"), integer(rawFrame.get("native_revision"), "native_revision"),
                integer(rawFrame.get("date_raw"), "date_raw"), text(rawFrame.get("snapshot_id"), "snapshot_id"),
                integer(rawFrame.get("revision"), "revision"), text(rawFrame.get("episode_run_id"), "episode_run_id"));
        PriorReceipt prior = project(root.get("applied"), frame);
        if (!ConstructionRelease.sameEpisode(frame, prior)) { return new Request(frame, prior, ConstructionRelease.IdentityUnused.INSTANCE); }
        Obj observation = object(root.get("process_observation"), "process_observation");
        String kind = text(observation.get("kind"), "process_observation.kind"); ProcessObservation process;
        if (kind.equals("unavailable")) { exact(observation, Set.of("kind")); process = ConstructionRelease.IdentityUnavailable.INSTANCE; }
        else {
            require(kind.equals("observed"), "identity kind must be observed or unavailable"); exact(observation, Set.of("kind", "pid", "creation_date"));
            process = new ConstructionRelease.ObservedIdentity(new ConstructionRelease.ProcessIdentity(integer(observation.get("pid"), "observed.pid"), text(observation.get("creation_date"), "observed.creation_date")));
        }
        return new Request(frame, prior, process);
    }
    public static ConstructionRelease.Decision assess(byte[] raw) {
        Request request = decode(raw); return ConstructionRelease.assess(request.frame, request.applied, request.processObservation);
    }
    public static byte[] encode(ConstructionRelease.Decision decision) {
        Map<String, Value> fields = new LinkedHashMap<>(); fields.put("status", new Text(decision.status().name()));
        fields.put("reason", new Text(decision.reason().name())); fields.put("blocks_candidate", new Bool(decision.blocksCandidate()));
        fields.put("formal_action_ready", new Bool(false)); return OpportunityJson.encode(new Obj(fields));
    }
    public static byte[] assessAndEncode(byte[] raw) { return encode(assess(raw)); }

    public static PriorReceipt project(Value applied, Frame frame) {
        if (!(applied instanceof Obj row)) { return ConstructionRelease.NoReceipt.INSTANCE; }
        Optional<String> episode = optionalText(row.get("episode_run_id"), "episode_run_id");
        if (episode.isEmpty() || !episode.orElseThrow().equals(frame.episodeRunId())) {
            return new ConstructionRelease.Receipt(episode, Optional.empty());
        }
        Details details = new Details(status(row), flag(row, "postcondition_verified"), optionalInteger(row.get("actor_character_id"), "actor_character_id"),
                optionalInteger(row.get("post_bridge_pid"), "post_bridge_pid"), optionalText(row.get("post_bridge_creation_date"), "post_bridge_creation_date"),
                optionalInteger(row.get("post_native_revision"), "post_native_revision"), optionalInteger(row.get("post_date_raw"), "post_date_raw"));
        return new ConstructionRelease.Receipt(episode, Optional.of(details));
    }
    private static AppliedStatus status(Obj row) {
        Value value = row.get("status"); if (value == null) { return AppliedStatus.MISSING; } if (value == Nil.INSTANCE) { return AppliedStatus.NULL; }
        return text(value, "receipt.status").equals("applied") ? AppliedStatus.APPLIED : AppliedStatus.OTHER;
    }
    private static Flag flag(Obj row, String key) {
        Value value = row.get(key); if (value == null) { return Flag.MISSING; } if (value == Nil.INSTANCE) { return Flag.NULL; }
        require(value instanceof Bool, key + " must be a boolean token"); return ((Bool) value).value() ? Flag.TRUE : Flag.FALSE;
    }
    private static Optional<BigInteger> optionalInteger(Value value, String key) { return value == null || value == Nil.INSTANCE ? Optional.empty() : Optional.of(integer(value, key)); }
    private static Optional<String> optionalText(Value value, String key) { return value == null || value == Nil.INSTANCE ? Optional.empty() : Optional.of(text(value, key)); }
    private static Obj object(Value value, String name) { return OpportunityJson.object(value, name); }
    private static BigInteger integer(Value value, String name) { return OpportunityJson.integer(value, name); }
    private static String text(Value value, String name) { return OpportunityJson.text(value, name); }
    private static void exact(Obj row, Set<String> keys) { require(row.members().keySet().equals(keys), "missing or extra wrapper fields"); }
    private static void require(boolean condition, String message) { OpportunityJson.require(condition, message); }
}
