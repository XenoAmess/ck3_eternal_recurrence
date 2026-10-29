package org.xar.ck3.control.wave2.finance.feastterminal;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.StampObserved;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.StampUnobserved;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastCodec;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.AbsentJournal;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.AbsentText;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.BooleanObservation;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.JournalField;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.NullText;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.Outcome;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.ParsedJournal;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.Post;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.PresentText;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.Provenance;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.Request;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.TextField;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.UnusableJournal;

/** Strict request projection and legacy outcome encoder; original payload extensions stay outside the model. */
public final class FeastTerminalCodec {
    public static final String REQUEST_SCHEMA = "xar.java.feast-terminal-request/v1";
    // Post containers may carry both 64-slot journals in addition to the hosted leaf.
    // This request budget is independent from the smaller counter/hosted projections.
    public static final int MAX_INPUT_BYTES = 1_048_576;
    public static final int MAX_OUTPUT_BYTES = 2_097_152;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(24).maxNumberLength(4096).build()).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);

    private FeastTerminalCodec() { }

    public static Request decodeRequest(byte[] bytes) {
        JsonNode root = parse(bytes);
        TerminalJson.fields(root, Set.of("schema", "activity_id", "actor_character_id", "post"));
        TerminalJson.require(TerminalJson.text(root.get("schema")).equals(REQUEST_SCHEMA));
        long activity = TerminalJson.number(root.get("activity_id"), 1, HostedFeastActivities.MAX_U32);
        long actor = TerminalJson.number(root.get("actor_character_id"), 1, HostedFeastActivities.MAX_U32);
        JsonNode post = root.get("post");
        TerminalJson.require(post != null && post.isObject());
        TerminalJson.require(TerminalJson.text(post.get("schema")).equals(FeastTerminalOutcome.POST_SCHEMA));
        var revision = TerminalJson.nonnegative(post.get("snapshot_revision"), true);
        var date = TerminalJson.nonnegative(post.get("date_raw"), false);
        TerminalJson.require(TerminalJson.bool(post.get("read_only")));
        HostedFeastActivities hosted = HostedFeastCodec.decodeTree(post.get("hosted_activities"));
        JsonNode frameActor = post.get("actor_character_id");
        Optional<Long> knownActor = frameActor == null || frameActor.isNull() ? Optional.empty()
                : Optional.of(TerminalJson.number(frameActor, 1, HostedFeastActivities.MAX_U32));
        JournalField journal = post.has("native_terminal_observations")
                ? NativeTerminalJournalCodec.readOptional(post.get("native_terminal_observations"), actor) : new AbsentJournal();
        Provenance provenance = new Provenance(textField(post, "exact_ck3_build"), textField(post, "exe_sha256"),
                textField(post, "queried_snapshot_id"));
        return new Request(activity, actor, new Post(revision, date, knownActor, hosted, journal, provenance));
    }

    /** Encodes a normalized projection, never a replacement for the retained source payload. */
    public static byte[] encodeRequest(Request request) {
        ObjectNode root = JSON.createObjectNode(); root.put("schema", REQUEST_SCHEMA);
        root.put("activity_id", request.activityId()); root.put("actor_character_id", request.actorId());
        Post value = request.post(); ObjectNode post = root.putObject("post");
        post.put("schema", FeastTerminalOutcome.POST_SCHEMA); post.put("snapshot_revision", value.revision());
        post.put("date_raw", value.dateRaw()); post.put("read_only", true);
        value.frameActor().ifPresent(actor -> post.put("actor_character_id", actor));
        try { post.set("hosted_activities", JSON.readTree(HostedFeastCodec.encode(value.hosted()))); }
        catch (IOException exception) { throw new IllegalStateException("hosted encoding could not be decoded", exception); }
        putProvenance(post, value.provenance());
        if (value.journal() instanceof ParsedJournal parsed) post.set("native_terminal_observations", NativeTerminalJournalCodec.write(JSON, parsed.value(), true));
        else if (value.journal() instanceof UnusableJournal) post.putNull("native_terminal_observations");
        return bytes(root, MAX_INPUT_BYTES);
    }

    public static byte[] encodeOutcome(Outcome outcome) {
        ObjectNode root = JSON.createObjectNode(); root.put("schema", FeastTerminalOutcome.SCHEMA);
        root.put("activity_id", outcome.activityId()); root.put("actor_character_id", outcome.actorId());
        root.put("snapshot_revision", outcome.revision()); root.put("date_raw", outcome.dateRaw());
        root.put("status", lower(outcome.status())); root.put("terminal_flags_observed", outcome.terminalFlagsObserved());
        putBoolean(root, "native_completed", outcome.completed()); putBoolean(root, "native_invalidated", outcome.invalidated());
        if (outcome.unknownReason().isPresent()) root.put("unknown_reason", lower(outcome.unknownReason().orElseThrow()));
        else root.putNull("unknown_reason");
        root.put("read_only", true); putProvenance(root, outcome.provenance());
        if (outcome.journalCoverage() instanceof ParsedJournal parsed) {
            root.set("native_terminal_observations_coverage", NativeTerminalJournalCodec.write(JSON, parsed.value(), false));
        } else if (outcome.journalCoverage() instanceof UnusableJournal) root.putNull("native_terminal_observations_coverage");
        if (outcome.completionStamp() instanceof StampObserved stamp) {
            root.put("native_completion_stamp_observed", true); root.put("native_completion_stamp_raw", stamp.raw());
        } else if (outcome.completionStamp() instanceof StampUnobserved) {
            root.put("native_completion_stamp_observed", false); root.putNull("native_completion_stamp_raw");
        }
        outcome.historicalObservation().ifPresent(cut -> root.set("native_terminal_observation", NativeTerminalJournalCodec.writeCut(JSON, cut)));
        return bytes(root, MAX_OUTPUT_BYTES);
    }

    private static JsonNode parse(byte[] bytes) {
        if (bytes == null || bytes.length == 0 || bytes.length > MAX_INPUT_BYTES) throw new IllegalArgumentException("terminal request byte budget exceeded or empty");
        try {
            String source = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            JsonNode root = JSON.readTree(source);
            TerminalJson.require(root != null); return root;
        } catch (IOException exception) {
            throw new IllegalArgumentException("terminal request is not strict UTF-8 JSON", exception);
        }
    }
    private static TextField textField(JsonNode post, String key) {
        if (!post.has(key)) return new AbsentText();
        return post.get(key).isNull() ? new NullText() : new PresentText(TerminalJson.text(post.get(key)));
    }
    private static void putProvenance(ObjectNode root, Provenance provenance) {
        putText(root, "exact_ck3_build", provenance.exactBuild()); putText(root, "exe_sha256", provenance.exeSha256());
        putText(root, "queried_snapshot_id", provenance.queriedSnapshotId());
    }
    private static void putText(ObjectNode root, String key, TextField value) {
        if (value instanceof PresentText text) root.put(key, text.value()); else if (value instanceof NullText) root.putNull(key);
    }
    private static void putBoolean(ObjectNode root, String key, BooleanObservation value) {
        switch (value) { case TRUE -> root.put(key, true); case FALSE -> root.put(key, false); case UNKNOWN -> root.putNull(key); }
    }
    private static String lower(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
    private static byte[] bytes(JsonNode node, int maximum) {
        try {
            byte[] bytes = JSON.writeValueAsBytes(node);
            if (bytes.length > maximum) throw new IllegalArgumentException("terminal JSON output byte budget exceeded");
            return bytes;
        } catch (IOException exception) {
            throw new IllegalStateException("terminal JSON encoding failed", exception);
        }
    }
}
