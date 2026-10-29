package org.xar.ck3.control.wave2.military.warresultssource;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.Availability;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.Binding;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.Build;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.Dispatch;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.DismissStage;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.DismissTrace;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.Input;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.LeafOwner;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.LookupSource;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.NativeFrame;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.NativeLeaf;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.Operation;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.OwnerReceipt;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.PostObservation;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.Status;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.ValidatedWire;
import org.xar.ck3.control.wave2.military.warresultssource.WarResultsSourceContract.Visibility;

/** Exact legacy/B15 leaf schemas; the independent TOP receipt is a separate root field. */
public final class WarResultsSourceCodec {
    public static final String SCHEMA = "xar.ck3.war-results-native-source-input/v1";
    private static final Set<String> LEAF_FIELDS = Set.of("schema", "operation", "window_name", "available", "accepted", "status",
            "unavailable_reason", "root_observed", "window_present", "effective_visible", "dispatch_attempted", "dispatch_invoked",
            "native_handled", "post_observed", "post_window_present", "post_effective_visible", "scope_unchanged", "closure_verified",
            "application_owner_thread_verified", "paused", "button_name", "played_character_id", "date_raw", "native_revision",
            "connection_generation", "pump_epoch", "thread_id", "game_version", "executable_sha256", "request_id", "ticket_sequence",
            "root_observation_source", "post_observation_source");
    private static final Set<String> TRACE_FIELDS;
    static { Set<String> fields = new HashSet<>(LEAF_FIELDS); fields.add("dismiss_stage"); fields.add("dismiss_exception_code"); TRACE_FIELDS = Set.copyOf(fields); }

    private WarResultsSourceCodec() { }

    public static Input decode(byte[] bytes) {
        ObjectNode node = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "expected_request_id", "operation", "binding", "native_generation", "owner_receipt", "leaf"));
        StrictJson.require(SCHEMA.equals(text(node, "schema")), "unsupported native-source input schema");
        ObjectNode binding = StrictJson.object(node.get("binding"), Set.of("actor_character_id", "date_raw", "native_revision"));
        return new Input(StrictJson.text(node.get("expected_request_id")), operation(text(node, "operation")),
                new Binding(int32(binding, "actor_character_id"), int32(binding, "date_raw"), uint64(binding, "native_revision", false)),
                uint64(node, "native_generation", false), owner(node.get("owner_receipt")), leaf(node.get("leaf")));
    }

    public static ValidatedWire validate(byte[] bytes) { return WarResultsSourceContract.validate(decode(bytes)); }

    public static byte[] encodeInput(Input input) {
        ObjectNode node = StrictJson.object(); node.put("schema", SCHEMA); node.put("expected_request_id", input.expectedRequestId());
        node.put("operation", operation(input.operation())); node.put("native_generation", input.nativeGeneration());
        ObjectNode binding = node.putObject("binding"); binding.put("actor_character_id", input.binding().actorId());
        binding.put("date_raw", input.binding().dateRaw()); binding.put("native_revision", input.binding().nativeRevision());
        node.set("owner_receipt", encodeOwner(input.ownerReceipt())); node.set("leaf", encodeLeaf(input.leaf())); return StrictJson.canonical(node);
    }

    public static byte[] encodeNormalized(ValidatedWire validated) { return StrictJson.canonical(encodeLeaf(validated.leaf())); }

    /** Shared standalone TOP receipt codec; validation against the original request remains validateOwner. */
    public static OwnerReceipt decodeOwnerReceipt(byte[] raw) { return owner(StrictJson.parse(raw)); }

    public static byte[] encodeOwnerReceipt(OwnerReceipt receipt) { return StrictJson.canonical(encodeOwner(receipt)); }

    private static OwnerReceipt owner(JsonNode value) {
        ObjectNode node = StrictJson.object(value, Set.of("request_id", "ticket_sequence", "executor_started_sequence", "completed_sequence", "pump_epoch", "thread_id", "date_raw", "connection_generation"));
        return new OwnerReceipt(StrictJson.text(node.get("request_id")), uint64(node, "ticket_sequence", true),
                uint64(node, "executor_started_sequence", true), uint64(node, "completed_sequence", true), uint64(node, "pump_epoch", true),
                uint32(node, "thread_id", true), int32(node, "date_raw"), uint64(node, "connection_generation", true));
    }

    private static NativeLeaf leaf(JsonNode value) {
        StrictJson.require(value != null && value.isObject(), "native leaf object required"); Set<String> actual = new HashSet<>(); value.fieldNames().forEachRemaining(actual::add);
        StrictJson.require(actual.equals(LEAF_FIELDS) || actual.equals(TRACE_FIELDS), "exact legacy or complete B15 leaf fields required");
        ObjectNode node = (ObjectNode) value;
        StrictJson.require("ck3-war-results-window-v1".equals(text(node, "schema")) && "war_results".equals(text(node, "window_name")), "different fixed native schema/window");
        Optional<DismissTrace> trace = node.has("dismiss_stage") ? Optional.of(new DismissTrace(stage(text(node, "dismiss_stage")), uint32(node, "dismiss_exception_code", false))) : Optional.empty();
        return new NativeLeaf(operation(text(node, "operation")), new NativeFrame(int32(node, "played_character_id"), int32(node, "date_raw"),
                bool(node, "paused"), uint64(node, "native_revision", false), uint64(node, "connection_generation", false)),
                new Build(text(node, "game_version"), text(node, "executable_sha256")),
                new LeafOwner(text(node, "request_id"), uint64(node, "ticket_sequence", false), uint64(node, "pump_epoch", false), uint32(node, "thread_id", false)),
                new Visibility(bool(node, "root_observed"), bool(node, "window_present"), bool(node, "effective_visible"), lookup(text(node, "root_observation_source"))),
                new PostObservation(new Visibility(bool(node, "post_observed"), bool(node, "post_window_present"), bool(node, "post_effective_visible"), lookup(text(node, "post_observation_source"))), bool(node, "scope_unchanged")),
                new Availability(bool(node, "available"), bool(node, "accepted"), status(text(node, "status")), text(node, "unavailable_reason"), bool(node, "closure_verified")),
                new Dispatch(bool(node, "dispatch_attempted"), bool(node, "dispatch_invoked"), bool(node, "native_handled"), bool(node, "application_owner_thread_verified"), text(node, "button_name"), trace));
    }

    private static ObjectNode encodeOwner(OwnerReceipt owner) {
        ObjectNode node = StrictJson.object(); node.put("request_id", owner.requestId()); node.put("ticket_sequence", owner.ticketSequence());
        node.put("executor_started_sequence", owner.executorStartedSequence()); node.put("completed_sequence", owner.completedSequence());
        node.put("pump_epoch", owner.pumpEpoch()); node.put("thread_id", owner.threadId()); node.put("date_raw", owner.dateRaw());
        node.put("connection_generation", owner.connectionGeneration()); return node;
    }

    private static ObjectNode encodeLeaf(NativeLeaf leaf) {
        ObjectNode node = StrictJson.object(); node.put("schema", "ck3-war-results-window-v1"); node.put("window_name", "war_results");
        node.put("operation", operation(leaf.operation())); node.put("available", leaf.availability().available()); node.put("accepted", leaf.availability().accepted());
        node.put("status", status(leaf.availability().status())); node.put("unavailable_reason", leaf.availability().unavailableReason());
        node.put("closure_verified", leaf.availability().closureVerified()); node.put("root_observed", leaf.before().observed());
        node.put("window_present", leaf.before().windowPresent()); node.put("effective_visible", leaf.before().effectiveVisible());
        node.put("root_observation_source", lookup(leaf.before().source())); node.put("post_observed", leaf.post().visibility().observed());
        node.put("post_window_present", leaf.post().visibility().windowPresent()); node.put("post_effective_visible", leaf.post().visibility().effectiveVisible());
        node.put("post_observation_source", lookup(leaf.post().visibility().source())); node.put("scope_unchanged", leaf.post().scopeUnchanged());
        node.put("dispatch_attempted", leaf.dispatch().attempted()); node.put("dispatch_invoked", leaf.dispatch().invoked()); node.put("native_handled", leaf.dispatch().nativeHandled());
        node.put("application_owner_thread_verified", leaf.dispatch().ownerThreadVerified()); node.put("button_name", leaf.dispatch().buttonName());
        node.put("played_character_id", leaf.frame().actorId()); node.put("date_raw", leaf.frame().dateRaw()); node.put("paused", leaf.frame().paused());
        node.put("native_revision", leaf.frame().revision()); node.put("connection_generation", leaf.frame().connectionGeneration());
        node.put("request_id", leaf.owner().requestId()); node.put("ticket_sequence", leaf.owner().ticketSequence());
        node.put("pump_epoch", leaf.owner().pumpEpoch()); node.put("thread_id", leaf.owner().threadId());
        node.put("game_version", leaf.build().gameVersion()); node.put("executable_sha256", leaf.build().executableSha256());
        leaf.dispatch().dismissTrace().ifPresent(trace -> { node.put("dismiss_stage", stage(trace.stage())); node.put("dismiss_exception_code", trace.exceptionCode()); });
        return node;
    }

    private static boolean bool(ObjectNode node, String key) { JsonNode value = node.get(key); StrictJson.require(value != null && value.isBoolean(), "exact boolean required: " + key); return value.booleanValue(); }
    private static String text(ObjectNode node, String key) { JsonNode value = node.get(key); StrictJson.require(value != null && value.isTextual(), "exact text required: " + key); String text = value.textValue(); if (!text.isEmpty()) { StrictJson.text(text); } return text; }
    private static int int32(ObjectNode node, String key) { return StrictJson.integer(node.get(key), BigInteger.valueOf(Integer.MIN_VALUE), BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact(); }
    private static BigInteger uint64(ObjectNode node, String key, boolean positive) { return StrictJson.integer(node.get(key), positive ? BigInteger.ONE : BigInteger.ZERO, StrictJson.UINT64_MAX); }
    private static long uint32(ObjectNode node, String key, boolean positive) { return StrictJson.integer(node.get(key), positive ? 1 : 0, 0xffff_ffffL); }
    private static Operation operation(String value) { return switch (value) { case "query" -> Operation.QUERY; case "close" -> Operation.CLOSE; default -> throw new IllegalArgumentException("unknown fixed operation"); }; }
    private static String operation(Operation value) { return value == Operation.QUERY ? "query" : "close"; }
    private static LookupSource lookup(String value) { return switch (value) { case "" -> LookupSource.NONE; case "guarded_registered_top_level" -> LookupSource.GUARDED_REGISTERED_TOP_LEVEL; case "guarded_top_level_and_complete_owner_tree" -> LookupSource.GUARDED_TOP_LEVEL_AND_COMPLETE_OWNER_TREE; default -> throw new IllegalArgumentException("unknown lookup source"); }; }
    private static String lookup(LookupSource value) { return switch (value) { case NONE -> ""; case GUARDED_REGISTERED_TOP_LEVEL -> "guarded_registered_top_level"; case GUARDED_TOP_LEVEL_AND_COMPLETE_OWNER_TREE -> "guarded_top_level_and_complete_owner_tree"; }; }
    private static DismissStage stage(String value) { return switch (value) { case "not_attempted" -> DismissStage.NOT_ATTEMPTED; case "preflight_rejected" -> DismissStage.PREFLIGHT_REJECTED; case "callback_entered" -> DismissStage.CALLBACK_ENTERED; case "callback_returned" -> DismissStage.CALLBACK_RETURNED; case "callback_exception" -> DismissStage.CALLBACK_EXCEPTION; default -> throw new IllegalArgumentException("unknown Dismiss stage"); }; }
    private static String stage(DismissStage value) { return switch (value) { case NOT_ATTEMPTED -> "not_attempted"; case PREFLIGHT_REJECTED -> "preflight_rejected"; case CALLBACK_ENTERED -> "callback_entered"; case CALLBACK_RETURNED -> "callback_returned"; case CALLBACK_EXCEPTION -> "callback_exception"; }; }
    private static Status status(String value) { return switch (value) { case "absent" -> Status.ABSENT; case "visible" -> Status.VISIBLE; case "hidden" -> Status.HIDDEN; case "closed_verified" -> Status.CLOSED_VERIFIED; case "already_absent" -> Status.ALREADY_ABSENT; case "already_hidden" -> Status.ALREADY_HIDDEN; case "verification_pending" -> Status.VERIFICATION_PENDING; case "unavailable" -> Status.UNAVAILABLE; default -> throw new IllegalArgumentException("unknown native status"); }; }
    private static String status(Status value) { return switch (value) { case ABSENT -> "absent"; case VISIBLE -> "visible"; case HIDDEN -> "hidden"; case CLOSED_VERIFIED -> "closed_verified"; case ALREADY_ABSENT -> "already_absent"; case ALREADY_HIDDEN -> "already_hidden"; case VERIFICATION_PENDING -> "verification_pending"; case UNAVAILABLE -> "unavailable"; }; }
}
