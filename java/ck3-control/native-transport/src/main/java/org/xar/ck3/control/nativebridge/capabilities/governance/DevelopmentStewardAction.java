package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** The original fixed-task producer contract; decoding historical data grants no native permission. */
public final class DevelopmentStewardAction {
    public static final String STEP = "change-steward-develop-county-task-v1";
    public static final String QUERY_STEP = "query-steward-develop-county-candidates-v1";
    public static final String CAPABILITY = "game.command." + STEP;
    public static final String TRANSPORT_CAPABILITY = "game.contract." + STEP + "-fail-closed";
    public static final String TASK = "task_develop_county";
    public static final String VERSION = "1.19.0.6";
    public static final String SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    public static final String BACKEND = "ck3-1.19.0.6-native-steward-develop-county-action-v1";
    public static final String STAGE = "exact_build_action_seam_pending_command_abi_certification";
    private static final Set<String> ACK_FIELDS = Set.of("schema_version", "contract_stage", "status",
            "verification_pending", "request_id", "pre_snapshot_revision", "pre_native_snapshot_revision",
            "councillor_character_id", "task_key", "target_county_title_id", "submitted_target_province_id",
            "replaced_existing_task", "failure_class", "rejection_reason", "native_reason_key", "exact_build");
    private static final Set<String> RECEIPT_FIELDS = Set.of("schema_version", "status", "request_id", "reason",
            "post_snapshot_revision", "post_native_snapshot_revision", "post_observed_date_raw",
            "councillor_character_id", "active_task_key", "target_county_title_id", "target_province_id",
            "progress_kind", "progress_current_raw", "progress_max_raw", "progress_frozen", "postcondition_verified");
    private DevelopmentStewardAction() { }

    public record Request(String requestId, int councillorId, int countyTitleId,
                          BigInteger expectedRevision, boolean replaceExisting) {
        public Request {
            StrictJson.require(requestId != null && requestId.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,63}"),
                    "invalid fixed-task request ID");
            StrictJson.require(councillorId > 0 && countyTitleId > 0, "positive int32 steward/county IDs required");
            uint64(expectedRevision, true);
        }
    }

    public enum AckStatus { SUBMITTED_VERIFICATION_PENDING, REJECTED_BEFORE_SUBMIT }
    public enum Failure {
        NONE("none"), REQUEST_CONTRACT("request_contract"), SNAPSHOT_BINDING("snapshot_binding"),
        COUNCILLOR_BINDING("councillor_binding"), TASK_OR_TARGET_LEGALITY("task_or_target_legality"),
        NATIVE_COMMAND_DISPATCH("native_command_dispatch");
        private final String wire;
        Failure(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static Failure parse(String value) {
            for (Failure item : values()) if (item.wire.equals(value)) return item;
            throw new IllegalArgumentException("unknown steward failure class");
        }
    }

    public record Ack(Request request, AckStatus status, BigInteger preRevision, BigInteger preNativeRevision,
                      int submittedProvinceId, boolean replacedExisting, Failure failure,
                      Optional<String> rejectionReason, Optional<String> nativeReason, RawJson original) {
        public Ack {
            Objects.requireNonNull(request); Objects.requireNonNull(status); Objects.requireNonNull(failure);
            Objects.requireNonNull(rejectionReason); Objects.requireNonNull(nativeReason); Objects.requireNonNull(original);
            uint64(preRevision, false); uint64(preNativeRevision, false);
            rejectionReason.ifPresent(StrictJson::text); nativeReason.ifPresent(StrictJson::text);
            if (status == AckStatus.SUBMITTED_VERIFICATION_PENDING) {
                StrictJson.require(failure == Failure.NONE && rejectionReason.isEmpty() && nativeReason.isEmpty()
                        && preRevision.equals(request.expectedRevision()) && preNativeRevision.signum() > 0
                        && submittedProvinceId > 0, "submitted ACK is inconsistent; it remains pending");
            } else {
                StrictJson.require(failure != Failure.NONE && rejectionReason.isPresent() && preRevision.signum() == 0
                        && preNativeRevision.signum() == 0 && submittedProvinceId == -1 && !replacedExisting,
                        "pre-submit rejection ACK is inconsistent");
            }
        }
        public boolean verificationPending() { return status == AckStatus.SUBMITTED_VERIFICATION_PENDING; }
    }

    public enum ReceiptStatus { REJECTED, APPLIED, POSTCONDITION_FAILED }

    public record Receipt(Ack ack, ReceiptStatus status, Optional<String> reason,
                          BigInteger postRevision, BigInteger postNativeRevision, int dateRaw,
                          int councillorId, String activeTaskKey, OptionalInt countyTitleId,
                          OptionalInt provinceId, String progressKind, OptionalLong progressCurrent,
                          OptionalLong progressMaximum, Optional<Boolean> progressFrozen,
                          boolean postconditionVerified, RawJson original) {
        public Receipt {
            Objects.requireNonNull(ack); Objects.requireNonNull(status); Objects.requireNonNull(reason);
            Objects.requireNonNull(countyTitleId); Objects.requireNonNull(provinceId);
            Objects.requireNonNull(progressCurrent); Objects.requireNonNull(progressMaximum);
            Objects.requireNonNull(progressFrozen); Objects.requireNonNull(original);
            uint64(postRevision, false); uint64(postNativeRevision, false);
            textAllowEmpty(activeTaskKey); textAllowEmpty(progressKind); reason.ifPresent(StrictJson::text);
            countyTitleId.ifPresent(value -> StrictJson.require(value > 0, "positive optional county title required"));
            provinceId.ifPresent(value -> StrictJson.require(value > 0, "positive optional province required"));
            switch (status) {
                case REJECTED -> StrictJson.require(ack.status() == AckStatus.REJECTED_BEFORE_SUBMIT
                        && !postconditionVerified && reason.equals(ack.rejectionReason())
                        && postRevision.signum() == 0 && postNativeRevision.signum() == 0 && councillorId == -1
                        && activeTaskKey.isEmpty() && countyTitleId.isEmpty() && provinceId.isEmpty()
                        && progressKind.isEmpty() && progressCurrent.isEmpty() && progressMaximum.isEmpty()
                        && progressFrozen.isEmpty(), "rejected receipt is inconsistent");
                case APPLIED -> StrictJson.require(ack.status() == AckStatus.SUBMITTED_VERIFICATION_PENDING
                        && postconditionVerified && reason.isEmpty()
                        && postRevision.compareTo(ack.preRevision()) > 0
                        && postNativeRevision.compareTo(ack.preNativeRevision()) > 0
                        && councillorId == ack.request().councillorId() && activeTaskKey.equals(TASK)
                        && countyTitleId.equals(OptionalInt.of(ack.request().countyTitleId()))
                        && provinceId.equals(OptionalInt.of(ack.submittedProvinceId()))
                        && progressKind.equals("value") && progressCurrent.isPresent()
                        && progressMaximum.isPresent() && progressFrozen.isPresent(),
                        "applied receipt lacks the independently observed later task/target/progress");
                case POSTCONDITION_FAILED -> StrictJson.require(ack.status() == AckStatus.SUBMITTED_VERIFICATION_PENDING
                        && !postconditionVerified && reason.isPresent(), "unverified receipt is inconsistent");
            }
        }
    }

    public static Request decodeRequest(RawJson raw) {
        ObjectNode value = StrictJson.object(StrictJson.parse(raw.bytes()), Set.of("request_id", "councillor_character_id",
                "task_key", "target_county_title_id", "expected_revision", "replace_existing_task"));
        StrictJson.require(TASK.equals(text(value, "task_key")), "arbitrary task is forbidden");
        return new Request(text(value, "request_id"), id(value.get("councillor_character_id")),
                id(value.get("target_county_title_id")), unsigned(value.get("expected_revision"), true),
                bool(value.get("replace_existing_task")));
    }

    public static RawJson encodeRequest(Request request) {
        Objects.requireNonNull(request);
        return raw(StrictJson.object().put("request_id", request.requestId())
                .put("councillor_character_id", request.councillorId()).put("task_key", TASK)
                .put("target_county_title_id", request.countyTitleId()).put("expected_revision", request.expectedRevision())
                .put("replace_existing_task", request.replaceExisting()));
    }

    public static Ack decodeAck(RawJson raw, Request expected) {
        Objects.requireNonNull(expected);
        ObjectNode value = StrictJson.object(StrictJson.parse(raw.bytes()), ACK_FIELDS);
        StrictJson.integer(value.get("schema_version"), 1, 1);
        StrictJson.require(STAGE.equals(text(value, "contract_stage"))
                && expected.requestId().equals(text(value, "request_id"))
                && expected.councillorId() == id(value.get("councillor_character_id"))
                && TASK.equals(text(value, "task_key"))
                && expected.countyTitleId() == id(value.get("target_county_title_id")), "ACK request binding differs");
        ObjectNode build = StrictJson.object(value.get("exact_build"), Set.of("game_version", "executable_sha256", "backend_id"));
        StrictJson.require(VERSION.equals(text(build, "game_version")) && SHA.equals(text(build, "executable_sha256"))
                && BACKEND.equals(text(build, "backend_id")), "ACK changed the original uncertified exact build");
        AckStatus status = switch (text(value, "status")) {
            case "submitted_verification_pending" -> AckStatus.SUBMITTED_VERIFICATION_PENDING;
            case "rejected_before_submit" -> AckStatus.REJECTED_BEFORE_SUBMIT;
            default -> throw new IllegalArgumentException("unknown steward ACK status");
        };
        StrictJson.require(bool(value.get("verification_pending")) == (status == AckStatus.SUBMITTED_VERIFICATION_PENDING),
                "ACK pending flag disagrees");
        return new Ack(expected, status, unsigned(value.get("pre_snapshot_revision"), false),
                unsigned(value.get("pre_native_snapshot_revision"), false),
                integer32(value.get("submitted_target_province_id")), bool(value.get("replaced_existing_task")),
                Failure.parse(text(value, "failure_class")), optionalText(value.get("rejection_reason")),
                optionalText(value.get("native_reason_key")), raw);
    }

    public static RawJson encodeAck(Ack ack) {
        Objects.requireNonNull(ack);
        ObjectNode value = StrictJson.object().put("schema_version", 1).put("contract_stage", STAGE)
                .put("status", ack.verificationPending() ? "submitted_verification_pending" : "rejected_before_submit")
                .put("verification_pending", ack.verificationPending()).put("request_id", ack.request().requestId())
                .put("pre_snapshot_revision", ack.preRevision()).put("pre_native_snapshot_revision", ack.preNativeRevision())
                .put("councillor_character_id", ack.request().councillorId()).put("task_key", TASK)
                .put("target_county_title_id", ack.request().countyTitleId()).put("submitted_target_province_id", ack.submittedProvinceId())
                .put("replaced_existing_task", ack.replacedExisting()).put("failure_class", ack.failure().wire());
        put(value, "rejection_reason", ack.rejectionReason()); put(value, "native_reason_key", ack.nativeReason());
        value.set("exact_build", StrictJson.object().put("game_version", VERSION).put("executable_sha256", SHA).put("backend_id", BACKEND));
        return raw(value);
    }

    public static Receipt decodeReceipt(RawJson raw, Ack ack) {
        Objects.requireNonNull(ack);
        ObjectNode value = StrictJson.object(StrictJson.parse(raw.bytes()), RECEIPT_FIELDS);
        StrictJson.integer(value.get("schema_version"), 1, 1);
        StrictJson.require(ack.request().requestId().equals(text(value, "request_id")), "receipt request ID differs");
        ReceiptStatus status = switch (text(value, "status")) {
            case "rejected" -> ReceiptStatus.REJECTED;
            case "applied" -> ReceiptStatus.APPLIED;
            case "postcondition_failed" -> ReceiptStatus.POSTCONDITION_FAILED;
            default -> throw new IllegalArgumentException("unknown steward receipt status");
        };
        return new Receipt(ack, status, optionalText(value.get("reason")), unsigned(value.get("post_snapshot_revision"), false),
                unsigned(value.get("post_native_snapshot_revision"), false), integer32(value.get("post_observed_date_raw")),
                integer32(value.get("councillor_character_id")), textAllowEmpty(value.get("active_task_key")),
                optionalId(value.get("target_county_title_id")), optionalId(value.get("target_province_id")),
                textAllowEmpty(value.get("progress_kind")), optionalLong(value.get("progress_current_raw")),
                optionalLong(value.get("progress_max_raw")), optionalBoolean(value.get("progress_frozen")),
                bool(value.get("postcondition_verified")), raw);
    }

    public static RawJson encodeReceipt(Receipt receipt) {
        Objects.requireNonNull(receipt);
        String status = switch (receipt.status()) { case REJECTED -> "rejected"; case APPLIED -> "applied"; case POSTCONDITION_FAILED -> "postcondition_failed"; };
        ObjectNode value = StrictJson.object().put("schema_version", 1).put("status", status)
                .put("request_id", receipt.ack().request().requestId()).put("post_snapshot_revision", receipt.postRevision())
                .put("post_native_snapshot_revision", receipt.postNativeRevision()).put("post_observed_date_raw", receipt.dateRaw())
                .put("councillor_character_id", receipt.councillorId()).put("active_task_key", receipt.activeTaskKey())
                .put("progress_kind", receipt.progressKind()).put("postcondition_verified", receipt.postconditionVerified());
        put(value, "reason", receipt.reason());
        if (receipt.countyTitleId().isPresent()) value.put("target_county_title_id", receipt.countyTitleId().getAsInt()); else value.putNull("target_county_title_id");
        if (receipt.provinceId().isPresent()) value.put("target_province_id", receipt.provinceId().getAsInt()); else value.putNull("target_province_id");
        if (receipt.progressCurrent().isPresent()) value.put("progress_current_raw", receipt.progressCurrent().getAsLong()); else value.putNull("progress_current_raw");
        if (receipt.progressMaximum().isPresent()) value.put("progress_max_raw", receipt.progressMaximum().getAsLong()); else value.putNull("progress_max_raw");
        if (receipt.progressFrozen().isPresent()) value.put("progress_frozen", receipt.progressFrozen().orElseThrow()); else value.putNull("progress_frozen");
        return raw(value);
    }

    private static void uint64(BigInteger value, boolean positive) {
        StrictJson.require(value != null && value.compareTo(positive ? BigInteger.ONE : BigInteger.ZERO) >= 0
                && value.compareTo(StrictJson.UINT64_MAX) <= 0, "exact uint64 revision required");
    }
    private static BigInteger unsigned(JsonNode value, boolean positive) {
        return StrictJson.integer(value, positive ? BigInteger.ONE : BigInteger.ZERO, StrictJson.UINT64_MAX);
    }
    private static int id(JsonNode value) { return (int) StrictJson.integer(value, 1, Integer.MAX_VALUE); }
    private static int integer32(JsonNode value) { return (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static String text(ObjectNode value, String field) { return StrictJson.text(value.get(field)); }
    private static String textAllowEmpty(JsonNode value) {
        StrictJson.require(value != null && value.isTextual(), "actual JSON string required"); return textAllowEmpty(value.textValue());
    }
    private static String textAllowEmpty(String value) {
        StrictJson.require(value != null, "actual string required"); if (!value.isEmpty()) StrictJson.text(value); return value;
    }
    private static boolean bool(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "actual JSON boolean required"); return value.booleanValue();
    }
    private static Optional<String> optionalText(JsonNode value) {
        StrictJson.require(value != null, "nullable field must be present"); return value.isNull() ? Optional.empty() : Optional.of(StrictJson.text(value));
    }
    private static OptionalInt optionalId(JsonNode value) {
        StrictJson.require(value != null, "nullable ID field must be present"); return value.isNull() ? OptionalInt.empty() : OptionalInt.of(id(value));
    }
    private static OptionalLong optionalLong(JsonNode value) {
        StrictJson.require(value != null, "nullable raw field must be present"); return value.isNull() ? OptionalLong.empty()
                : OptionalLong.of(StrictJson.integer(value, Long.MIN_VALUE, Long.MAX_VALUE));
    }
    private static Optional<Boolean> optionalBoolean(JsonNode value) {
        StrictJson.require(value != null, "nullable boolean field must be present"); return value.isNull() ? Optional.empty() : Optional.of(bool(value));
    }
    private static void put(ObjectNode object, String key, Optional<String> value) {
        if (value.isPresent()) object.put(key, value.orElseThrow()); else object.putNull(key);
    }
    private static RawJson raw(ObjectNode value) { return new RawJson(StrictJson.canonical(value)); }
}
