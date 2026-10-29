package org.xar.ck3.control.nativebridge.capabilities.family;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** Original current4 education DTO, including pending/unknown and independently published later post-observation. */
public final class ChildEducationFocus {
    public static final String SCHEMA = "child-education-focus-private-12004-v1";
    public static final String QUERY_STEP = "private-query-child-education-focus-v1";
    public static final String SUBMIT_STEP = "private-select-child-education-focus-v1";
    public static final String RECEIPT_STEP = "private-query-child-education-focus-receipt-v1";
    public static final String PERMISSION = "allow_private_lifestyle_formal_trial";
    private static final Set<String> SUBMISSION = keys("status unavailable_reason action_request_id accepted child_full_id requested_focus_key pre_frame");
    private ChildEducationFocus() { }
    public enum Key { EDUCATION_DIPLOMACY, EDUCATION_MARTIAL, EDUCATION_STEWARDSHIP, EDUCATION_INTRIGUE, EDUCATION_LEARNING;
        public String wire() { return name().toLowerCase(Locale.ROOT); }
    }
    public enum QueryStatus { AVAILABLE, UNAVAILABLE }
    public enum SubmitStatus { SUBMITTED_VERIFICATION_PENDING, REJECTED_BEFORE_SUBMIT, SUBMIT_UNKNOWN }
    public enum PendingStatus { ACTION_STATE_UNKNOWN, SUBMIT_UNKNOWN, SUBMITTED_VERIFICATION_PENDING }
    public enum ReceiptStatus { OBSERVED_APPLIED, VERIFICATION_PENDING, UNAVAILABLE }
    public enum Presence { PRESENT, ABSENT, UNAVAILABLE }
    public record Selection(long child, Key target) { public Selection { fullId(child); Objects.requireNonNull(target); } }
    public record Frame(String snapshotId, String episode, BigInteger nativeRevision, int dateRaw, long controller) {
        public Frame {
            text(snapshotId); text(episode); FamilyObligations.positive64(nativeRevision); fullId(controller);
            StrictJson.require(snapshotId.equals("native:" + nativeRevision) && dateRaw >= 0, "original child-focus paused native frame required");
        }
    }
    public record Context(Frame frame, BigInteger publicRevision) {
        public Context { Objects.requireNonNull(frame); FamilyObligations.positive64(publicRevision); }
    }
    public record Focus(boolean available, Optional<String> reason, Presence presence, Optional<String> key) {
        public Focus { Objects.requireNonNull(reason); Objects.requireNonNull(presence); Objects.requireNonNull(key); reason.ifPresent(ChildEducationFocus::string); key.ifPresent(ChildEducationFocus::text); }
    }
    public record Submission(SubmitStatus status, Optional<String> reason, String actionRequestId, boolean accepted,
            Selection selection, Frame preFrame) {
        public Submission { Objects.requireNonNull(status); Objects.requireNonNull(reason); text(actionRequestId); Objects.requireNonNull(selection); Objects.requireNonNull(preFrame); }
    }
    public record Post(String actionRequestId, boolean independentlyPublishedAfterSubmission, Frame frame, long child, Focus focus) {
        public Post { text(actionRequestId); Objects.requireNonNull(frame); fullId(child); Objects.requireNonNull(focus); }
    }
    public sealed interface NativeResult permits Query, Submitted, Receipt { RawJson original(); }
    public record Query(QueryStatus status, Optional<String> reason, Frame frame, Selection selection, Optional<Boolean> nativeLegal,
            Focus focus, RawJson original) implements NativeResult {
        public Query { Objects.requireNonNull(status); Objects.requireNonNull(reason); Objects.requireNonNull(frame); Objects.requireNonNull(selection); Objects.requireNonNull(nativeLegal); Objects.requireNonNull(focus); Objects.requireNonNull(original); }
    }
    public record Submitted(Submission submission, RawJson original) implements NativeResult {
        public Submitted { Objects.requireNonNull(submission); Objects.requireNonNull(original); }
    }
    public record Receipt(ReceiptStatus status, Optional<String> reason, boolean observedApplied, Submission submission,
            Optional<Post> post, RawJson original) implements NativeResult {
        public Receipt { Objects.requireNonNull(status); Objects.requireNonNull(reason); Objects.requireNonNull(submission); Objects.requireNonNull(post); Objects.requireNonNull(original); }
    }
    /** Actual durable wrapper may have null acceptance after an unknown submit. It is never resubmitted by this model. */
    public record Pending(PendingStatus status, Optional<String> reason, String actionRequestId, Optional<Boolean> accepted,
            Selection selection, Frame preFrame, Optional<Boolean> nativeCommandSubmitted, Context sourceContext, RawJson original) {
        public Pending {
            Objects.requireNonNull(status); Objects.requireNonNull(reason); text(actionRequestId); Objects.requireNonNull(accepted); Objects.requireNonNull(selection);
            Objects.requireNonNull(preFrame); Objects.requireNonNull(nativeCommandSubmitted); Objects.requireNonNull(sourceContext); Objects.requireNonNull(original);
        }
    }
    public static Frame decodeFrame(JsonNode value) {
        ObjectNode n = StrictJson.object(value, keys("snapshot_id episode_run_id native_revision date_raw controller_full_id paused"));
        StrictJson.trueValue(n.get("paused"));
        return new Frame(text(n.get("snapshot_id")), text(n.get("episode_run_id")), StrictJson.integer(n.get("native_revision"), BigInteger.ONE, StrictJson.UINT64_MAX),
                (int) StrictJson.integer(n.get("date_raw"), 0, Integer.MAX_VALUE), StrictJson.integer(n.get("controller_full_id"), 1, 0xffff_fffeL));
    }
    public static ObjectNode encodeFrame(Frame frame) {
        return StrictJson.object().put("snapshot_id", frame.snapshotId()).put("episode_run_id", frame.episode()).put("native_revision", frame.nativeRevision())
                .put("date_raw", frame.dateRaw()).put("controller_full_id", frame.controller()).put("paused", true);
    }
    public static Context decodeContext(JsonNode value) {
        ObjectNode n = StrictJson.object(value, keys("snapshot_id episode_run_id native_revision date_raw controller_full_id paused public_revision exact_ck3_build exe_sha256"));
        StrictJson.require(FamilyObligations.Build.CURRENT4.version().equals(text(n.get("exact_ck3_build")))
                && FamilyObligations.Build.CURRENT4.sha256().equalsIgnoreCase(text(n.get("exe_sha256"))), "original current4 child-focus source context required");
        ObjectNode frame = n.deepCopy(); frame.remove(List.of("public_revision", "exact_ck3_build", "exe_sha256"));
        return new Context(decodeFrame(frame), StrictJson.integer(n.get("public_revision"), BigInteger.ONE, StrictJson.UINT64_MAX));
    }
    public static ObjectNode encodeContext(Context context) {
        return encodeFrame(context.frame()).put("public_revision", context.publicRevision()).put("exact_ck3_build", FamilyObligations.Build.CURRENT4.version())
                .put("exe_sha256", FamilyObligations.Build.CURRENT4.sha256().toUpperCase(Locale.ROOT));
    }
    public static Focus decodeFocus(JsonNode value) {
        ObjectNode n = StrictJson.object(value, keys("available unavailable_reason presence key")); boolean available = bool(n.get("available"));
        String presence = string(n.get("presence")); Optional<String> key = nullableText(n.get("key"), false); Presence state;
        if (available) {
            StrictJson.require(presence.equals("present") || presence.equals("absent"), "available source focus has unknown presence");
            state = presence.equals("present") ? Presence.PRESENT : Presence.ABSENT;
            StrictJson.require((state == Presence.PRESENT) == key.isPresent(), "focus source key/presence disagree");
        } else { StrictJson.require(presence.isEmpty() && key.isEmpty(), "unavailable focus must not become an observed value"); state = Presence.UNAVAILABLE; }
        return new Focus(available, nullableText(n.get("unavailable_reason"), true), state, key);
    }
    public static Query decodeQuery(RawJson original, Frame frame, Selection selection) {
        ObjectNode n = StrictJson.object(StrictJson.parse(original.bytes()), keys("schema kind status unavailable_reason source_frame child_full_id target_key native_legal current_focus"));
        header(n, "query"); QueryStatus status = enumValue(QueryStatus.class, n.get("status"));
        StrictJson.require(decodeFrame(n.get("source_frame")).equals(frame) && selection(n, "target_key").equals(selection), "child-focus query belongs to another child/key/frame");
        Optional<Boolean> legal = nullableBool(n.get("native_legal")); StrictJson.require(status != QueryStatus.AVAILABLE || legal.isPresent(), "available focus query lacks observed native legality");
        return new Query(status, nullableText(n.get("unavailable_reason"), true), frame, selection, legal, decodeFocus(n.get("current_focus")), original);
    }
    public static Submitted decodeSubmitted(RawJson original, Frame frame, Selection selection, String actionRequestId) {
        Set<String> fields = new HashSet<>(SUBMISSION); fields.addAll(keys("schema kind")); ObjectNode n = StrictJson.object(StrictJson.parse(original.bytes()), fields); header(n, "submit");
        ObjectNode actual = n.deepCopy(); actual.remove(List.of("schema", "kind")); Submission submission = decodeSubmission(actual);
        StrictJson.require(submission.preFrame().equals(frame) && submission.selection().equals(selection) && submission.actionRequestId().equals(actionRequestId), "child-focus submit belongs to another original action/child/key/frame");
        return new Submitted(submission, original);
    }
    public static Receipt decodeReceipt(RawJson original, Frame frame, Pending pending) {
        ObjectNode n = StrictJson.object(StrictJson.parse(original.bytes()), keys("schema kind status unavailable_reason observed_applied submission post_observation")); header(n, "receipt");
        ReceiptStatus status = enumValue(ReceiptStatus.class, n.get("status")); boolean applied = bool(n.get("observed_applied"));
        StrictJson.require(applied == (status == ReceiptStatus.OBSERVED_APPLIED), "observed_applied/status mismatch");
        Submission submission = decodeSubmission(n.get("submission"));
        StrictJson.require(submission.actionRequestId().equals(pending.actionRequestId()) && submission.selection().equals(pending.selection()) && submission.preFrame().equals(pending.preFrame()), "focus receipt differs from original submitted action/child/key/pre-frame");
        JsonNode rawPost = n.get("post_observation"); required(rawPost); Optional<Post> post = Optional.empty();
        if (!rawPost.isNull()) {
            ObjectNode p = StrictJson.object(rawPost, keys("action_request_id independently_published_after_submission source_frame child_full_id current_focus"));
            String actionId = text(p.get("action_request_id")); long child = StrictJson.integer(p.get("child_full_id"), 1, 0xffff_fffeL); Frame actual = decodeFrame(p.get("source_frame"));
            StrictJson.require(actionId.equals(pending.actionRequestId()) && child == pending.selection().child() && actual.equals(frame), "child-focus independent post observation binding differs");
            post = Optional.of(new Post(actionId, bool(p.get("independently_published_after_submission")), actual, child, decodeFocus(p.get("current_focus"))));
        }
        if (applied) {
            Post actual = post.orElseThrow(() -> new IllegalArgumentException("observed focus needs independent post publication")); Frame pre = pending.preFrame();
            StrictJson.require(submission.accepted() && submission.status() == SubmitStatus.SUBMITTED_VERIFICATION_PENDING && actual.independentlyPublishedAfterSubmission() && frame.nativeRevision().compareTo(pre.nativeRevision()) > 0
                    && !frame.snapshotId().equals(pre.snapshotId()) && frame.episode().equals(pre.episode()) && frame.controller() == pre.controller()
                    && actual.focus().available() && actual.focus().presence() == Presence.PRESENT && actual.focus().key().orElseThrow().equals(pending.selection().target().wire()), "observed focus lacks the actual later same-controller/episode target-focus postcondition");
        }
        return new Receipt(status, nullableText(n.get("unavailable_reason"), true), applied, submission, post, original);
    }
    public static Pending decodePending(RawJson original) {
        ObjectNode n = StrictJson.object(StrictJson.parse(original.bytes()), keys("schema kind status unavailable_reason action_request_id accepted child_full_id requested_focus_key pre_frame native_command_submitted request_id source_public_revision source_context")); header(n, "submit");
        PendingStatus status = enumValue(PendingStatus.class, n.get("status")); String actionId = text(n.get("action_request_id"));
        StrictJson.require(actionId.equals(text(n.get("request_id"))), "persisted focus action/request identity changed");
        Context context = decodeContext(n.get("source_context")); Frame pre = decodeFrame(n.get("pre_frame")); StrictJson.require(context.frame().equals(pre), "persisted focus source/pre-frame mismatch");
        StrictJson.integer(n.get("source_public_revision"), context.publicRevision(), context.publicRevision());
        Optional<Boolean> accepted = nullableBool(n.get("accepted")), submitted = nullableBool(n.get("native_command_submitted"));
        if (status == PendingStatus.ACTION_STATE_UNKNOWN) StrictJson.require(accepted.isEmpty() && submitted.isEmpty(), "unknown focus intent cannot claim native acceptance or dispatch");
        else {
            StrictJson.require(accepted.isPresent(), "native focus response needs original acceptance boolean");
            if (status == PendingStatus.SUBMITTED_VERIFICATION_PENDING) StrictJson.require(accepted.orElseThrow(), "pending focus must retain original queue acceptance");
            StrictJson.require(accepted.orElseThrow() ? submitted.equals(Optional.of(true)) : submitted.isEmpty(), "unresolved focus dispatch marker differs from native response");
        }
        return new Pending(status, nullableText(n.get("unavailable_reason"), true), actionId, accepted, selection(n, "requested_focus_key"), pre, submitted, context, original);
    }
    public static RawJson verifyPending(Pending pending) {
        StrictJson.require(pending.equals(decodePending(pending.original())), "typed pending focus differs from original durable input"); return pending.original();
    }
    private static Submission decodeSubmission(JsonNode value) {
        ObjectNode n = StrictJson.object(value, SUBMISSION); SubmitStatus status = enumValue(SubmitStatus.class, n.get("status")); boolean accepted = bool(n.get("accepted"));
        StrictJson.require(status != SubmitStatus.SUBMITTED_VERIFICATION_PENDING || accepted, "native pending focus lacks queue acceptance");
        StrictJson.require(status != SubmitStatus.REJECTED_BEFORE_SUBMIT || !accepted, "native rejected focus cannot claim queue acceptance");
        return new Submission(status, nullableText(n.get("unavailable_reason"), true), text(n.get("action_request_id")), accepted, selection(n, "requested_focus_key"), decodeFrame(n.get("pre_frame")));
    }
    private static Selection selection(ObjectNode n, String key) { return new Selection(StrictJson.integer(n.get("child_full_id"), 1, 0xffff_fffeL), enumValue(Key.class, n.get(key))); }
    private static void header(ObjectNode n, String kind) { StrictJson.require(SCHEMA.equals(text(n.get("schema"))) && kind.equals(text(n.get("kind"))), "original child-focus schema/kind required"); }
    private static Optional<String> nullableText(JsonNode n, boolean empty) { required(n); return n.isNull() ? Optional.empty() : Optional.of(empty ? string(n) : text(n)); }
    private static Optional<Boolean> nullableBool(JsonNode n) { required(n); return n.isNull() ? Optional.empty() : Optional.of(bool(n)); }
    private static boolean bool(JsonNode n) { StrictJson.require(n != null && n.isBoolean(), "actual source boolean required"); return n.booleanValue(); }
    private static String string(JsonNode n) { StrictJson.require(n != null && n.isTextual(), "source string required"); String value = n.textValue(); string(value); return value; }
    private static String text(JsonNode n) { String value = string(n); text(value); return value; }
    private static void string(String value) { StrictJson.require(value != null && value.length() <= 4096, "bounded source string required"); if (!value.isEmpty()) StrictJson.text(value); }
    private static void text(String value) { string(value); StrictJson.require(!value.isEmpty(), "nonempty source string required"); }
    private static void fullId(long value) { StrictJson.require(value > 0 && value <= 0xffff_fffeL, "valid native child/controller full ID required"); }
    private static void required(JsonNode n) { StrictJson.require(n != null, "native field missing"); }
    private static Set<String> keys(String words) { return new HashSet<>(List.of(words.split(" "))); }
    private static <E extends Enum<E>> E enumValue(Class<E> type, JsonNode n) {
        String key = text(n); for (E value : type.getEnumConstants()) if (value.name().toLowerCase(Locale.ROOT).equals(key)) return value;
        throw new IllegalArgumentException("unknown authored child-focus " + type.getSimpleName() + ": " + key);
    }
}
