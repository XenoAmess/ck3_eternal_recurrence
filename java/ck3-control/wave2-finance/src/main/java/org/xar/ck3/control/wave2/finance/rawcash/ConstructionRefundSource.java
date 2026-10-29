package org.xar.ck3.control.wave2.finance.rawcash;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanCodec;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec.PlanningFrame;

/** One native producer and one strict copied-observation consumer. No cancellation or funding authority. */
public final class ConstructionRefundSource {
    public static final String NATIVE_SCHEMA = "ck3_12004_construction_refund_source_v1";
    public static final String SCHEMA = "xar.ck3.construction-refund-source.v2";
    public static final String OPERATION = "query-player-construction-refund-source-v1";
    private static final BigInteger UINT32_MAX = new BigInteger("4294967295");
    private static final Set<String> NATIVE_FIELDS = Set.of("schema", "game_version", "executable_sha256",
            "read_only", "scope", "available", "unavailable_reason", "native_revision", "capture_epoch",
            "date_raw", "actor_character_id", "province_id", "copied_cancel_gate_allows", "active_record",
            "receiver", "final_action_gate_observed", "submission_qualified", "received_funds_verified", "funding_credit_raw");
    private static final Set<String> FRAME_FIELDS = Set.of("snapshot_id", "revision", "native_revision", "date_raw",
            "actor_character_id", "episode_run_id", "bridge_pid", "connection_generation");
    private ConstructionRefundSource() { }

    public enum NativeEffect { READ_ONLY_GATE_STATIC_ONLY, MUTATION, UNKNOWN }
    public enum Refusal { WRONG_EXACT_BUILD, FRAME_DRIFT }
    public enum Failure {
        EXACT_BUILD("exact_build"), APPLICATION_MAIN("application_main"), REQUEST("request"), PAUSED_FRAME("paused_frame"),
        NATIVE_GATE_SOURCE("native_gate_source"), PROVINCE_SOURCE("province_source"), CHARACTER_SOURCE("character_source"),
        RECORD_SOURCE("record_source"), GATE_READ("gate_read"), FRAME_CHANGED("frame_changed"), EXCEPTION("exception");
        private final String wire;
        Failure(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Failure exact(String wire) {
            for (Failure failure : values()) { if (failure.wire.equals(wire)) { return failure; } }
            throw new IllegalArgumentException("unknown native cancellation source failure");
        }
    }
    public sealed interface Result permits Candidate, Unavailable, Refused { }
    public record Refused(Refusal reason) implements Result {
        public Refused { Objects.requireNonNull(reason, "reason"); }
    }
    public record Pointer(BigInteger value) {
        public Pointer {
            unsigned(value, BigInteger.ONE, StrictJson.UINT64_MAX);
            StrictJson.require(value.mod(BigInteger.valueOf(8)).signum() == 0, "aligned exact native pointer required");
        }
        public String decimal() { return value.toString(); }
    }
    /** Pointer/start word bookends identify a current copy, not a durable construction incarnation. */
    public record ActiveRecord(Pointer recordPointer, Pointer definitionPointer, int slotIndex,
            BigInteger startWord, long recordedBuilderCharacterId, List<Long> recordedCostRawNative) {
        public ActiveRecord {
            Objects.requireNonNull(recordPointer, "recordPointer"); Objects.requireNonNull(definitionPointer, "definitionPointer");
            unsigned(startWord, BigInteger.ZERO, StrictJson.UINT64_MAX);
            StrictJson.require(recordedBuilderCharacterId >= 0 && recordedBuilderCharacterId <= 0xffff_ffffL,
                    "exact copied full uint32 builder bits required");
            recordedCostRawNative = List.copyOf(recordedCostRawNative);
            StrictJson.require(recordedCostRawNative.size() == 10, "all ten stored signed resource slots required");
        }
    }
    public record Receiver(long characterId, Optional<Pointer> componentPointer, OptionalLong currentGoldRaw) {
        public Receiver {
            StrictJson.require(characterId >= 0 && characterId < 0xffff_ffffL, "actual command actor full ID required");
            Objects.requireNonNull(componentPointer, "componentPointer"); Objects.requireNonNull(currentGoldRaw, "currentGoldRaw");
            StrictJson.require(componentPointer.isPresent() == currentGoldRaw.isPresent(),
                    "missing receiver component differs from an observed zero balance");
        }
    }
    public static final class Candidate implements Result {
        private final PlanningFrame frame;
        private final BigInteger captureEpoch;
        private final int provinceId;
        private final Optional<ActiveRecord> activeRecord;
        private final Receiver receiver;
        private final boolean copiedCancelGateAllows;
        private final byte[] wire;
        private final RefundAssessment refundAssessment;
        private Candidate(PlanningFrame frame, BigInteger epoch, int province, Optional<ActiveRecord> active,
                Receiver receiver, boolean gate, byte[] wire) {
            this.frame = frame; this.captureEpoch = epoch; this.provinceId = province; this.activeRecord = active;
            this.receiver = receiver; this.copiedCancelGateAllows = gate; this.wire = wire.clone();
            this.refundAssessment = new RefundAssessment(frame, epoch, province, active, receiver, gate, wire);
        }
        public RefundAssessment refundAssessment() { return refundAssessment; }
        public PlanningFrame frame() { return frame; }
        public BigInteger captureEpoch() { return captureEpoch; }
        public int provinceId() { return provinceId; }
        public Optional<ActiveRecord> activeRecord() { return activeRecord; }
        public Receiver receiver() { return receiver; }
        public boolean copiedCancelGateAllows() { return copiedCancelGateAllows; }
        /** A query-time copied gate is never the action's final same-writer-lock gate. */
        public boolean finalCancelGateObserved() { return false; }
        public boolean submissionQualified() { return false; }
        public boolean receivedFundsVerified() { return false; }
        public long fundingCreditRaw() { return 0; }
        public byte[] toJson() { return wire.clone(); }
    }
    /** Native resource indices, not the AI eight-slot budget view or invented resource names. */
    public enum ResourceSlot {
        SLOT_0, SLOT_1, SLOT_2, SLOT_3, SLOT_4, SLOT_5, SLOT_6, SLOT_7, SLOT_8, SLOT_9;
        public int nativeIndex() { return ordinal(); }
    }
    public enum ResourceDestination {
        CURRENT_COMMAND_ACTOR_GOLD, CURRENT_COMMAND_ACTOR_COMPONENT_130,
        CURRENT_COMMAND_ACTOR_COMPONENT_110, NO_HANDLER_IN_THIS_DISPATCH,
        CURRENT_COMMAND_ACTOR_COMPONENT_150, ACTOR_DOMAIN_INDIRECT,
        ACTOR_PRIMARY_TITLE_INDIRECT, ACTOR_INDIRECT_28B9700,
        CURRENT_COMMAND_ACTOR_COMPONENT_170;
        private static ResourceDestination forSlot(ResourceSlot slot) {
            return switch (slot) {
                case SLOT_0 -> CURRENT_COMMAND_ACTOR_GOLD;
                case SLOT_1 -> CURRENT_COMMAND_ACTOR_COMPONENT_130;
                case SLOT_2 -> CURRENT_COMMAND_ACTOR_COMPONENT_110;
                case SLOT_3 -> NO_HANDLER_IN_THIS_DISPATCH;
                case SLOT_4 -> CURRENT_COMMAND_ACTOR_COMPONENT_150;
                case SLOT_5 -> ACTOR_DOMAIN_INDIRECT;
                case SLOT_6 -> ACTOR_PRIMARY_TITLE_INDIRECT;
                case SLOT_7, SLOT_9 -> ACTOR_INDIRECT_28B9700;
                case SLOT_8 -> CURRENT_COMMAND_ACTOR_COMPONENT_170;
            };
        }
    }
    public record StoredResourceInput(ResourceSlot slot, long storedRaw, ResourceDestination destination) {
        public StoredResourceInput {
            Objects.requireNonNull(slot, "slot"); Objects.requireNonNull(destination, "destination");
            StrictJson.require(destination == ResourceDestination.forSlot(slot), "native resource consumer differs");
        }
    }
    public enum RefundKnowledge {
        NO_ACTIVE_RECORD, COPIED_NATIVE_GATE_REFUSED, CURRENT_RECEIVER_COMPONENT_UNAVAILABLE,
        DIRECT_VECTOR_COPIED_FULL_NET_REFUND_UNQUALIFIED
    }
    /** Actual caller structure: definition effect and callback payload handoff to the EventManager.
     * Its nested context path includes ownership transfer: source/destination containers can be
     * swapped, cleared, relocated or registered. It is not a read-only copy/quote entry.
     * This is static source knowledge; callback execution, queue state and full effects remain unobserved. */
    public enum FollowupContract { DEFINITION_EFFECT_AND_EVENT_MANAGER_HANDOFF_PATHS }
    public static final class RefundAssessment {
        public static final String SCHEMA = "xar.ck3.construction-refund-assessment.v1";
        private final PlanningFrame frame;
        private final BigInteger captureEpoch;
        private final int provinceId;
        private final Receiver receiver;
        private final OptionalLong recordedBuilderCharacterId;
        private final List<StoredResourceInput> storedInputs;
        private final RefundKnowledge knowledge;
        private final String sourceCopySha256;
        private RefundAssessment(PlanningFrame frame, BigInteger epoch, int province,
                Optional<ActiveRecord> active, Receiver receiver, boolean gate, byte[] sourceCopy) {
            this.frame = frame; this.captureEpoch = epoch; this.provinceId = province;
            this.receiver = receiver;
            this.recordedBuilderCharacterId = active.isPresent()
                    ? OptionalLong.of(active.orElseThrow().recordedBuilderCharacterId()) : OptionalLong.empty();
            List<StoredResourceInput> inputs = new ArrayList<>();
            if (active.isPresent()) for (ResourceSlot slot : ResourceSlot.values()) {
                inputs.add(new StoredResourceInput(slot, active.orElseThrow().recordedCostRawNative().get(slot.nativeIndex()),
                        ResourceDestination.forSlot(slot)));
            }
            this.storedInputs = List.copyOf(inputs);
            this.knowledge = active.isEmpty() ? RefundKnowledge.NO_ACTIVE_RECORD
                    : !gate ? RefundKnowledge.COPIED_NATIVE_GATE_REFUSED
                    : receiver.componentPointer().isEmpty() ? RefundKnowledge.CURRENT_RECEIVER_COMPONENT_UNAVAILABLE
                    : RefundKnowledge.DIRECT_VECTOR_COPIED_FULL_NET_REFUND_UNQUALIFIED;
            try { this.sourceCopySha256 = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(sourceCopy)); }
            catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException("required SHA-256 unavailable", impossible); }
        }
        public PlanningFrame frame() { return frame; }
        public BigInteger captureEpoch() { return captureEpoch; }
        public int provinceId() { return provinceId; }
        public Receiver receiver() { return receiver; }
        public OptionalLong recordedBuilderCharacterId() { return recordedBuilderCharacterId; }
        public List<StoredResourceInput> storedInputs() { return storedInputs; }
        public RefundKnowledge knowledge() { return knowledge; }
        public String sourceCopySha256() { return sourceCopySha256; }
        public FollowupContract followupContract() { return FollowupContract.DEFINITION_EFFECT_AND_EVENT_MANAGER_HANDOFF_PATHS; }
        public boolean completeNetRefundQuote() { return false; }
        public OptionalLong refundQuoteRaw() { return OptionalLong.empty(); }
        public boolean receivedFundsVerified() { return false; }
        public boolean submissionQualified() { return false; }
        public long fundingCreditRaw() { return 0; }
        /** A separate derived observation codec; original source/persistence schemas remain exact and unchanged. */
        public byte[] toJson() {
            ObjectNode out = StrictJson.object().put("schema", SCHEMA);
            out.set("planning_frame", frameJson(frame)); out.put("capture_epoch", captureEpoch.toString());
            out.put("province_id", provinceId); out.put("source_copy_sha256", sourceCopySha256);
            out.put("knowledge", knowledge.name()); out.put("followup_contract", followupContract().name());
            ObjectNode who = out.putObject("copied_receiver"); who.put("character_id", receiver.characterId());
            if (receiver.componentPointer().isPresent()) who.put("component_pointer", receiver.componentPointer().orElseThrow().decimal());
            else who.putNull("component_pointer");
            if (receiver.currentGoldRaw().isPresent()) who.put("current_gold_raw", receiver.currentGoldRaw().orElseThrow());
            else who.putNull("current_gold_raw");
            if (recordedBuilderCharacterId.isPresent()) out.put("recorded_builder_character_id", recordedBuilderCharacterId.orElseThrow());
            else out.putNull("recorded_builder_character_id");
            var resources = out.putArray("stored_resource_inputs");
            for (StoredResourceInput input : storedInputs)
                resources.addObject().put("native_slot", input.slot().nativeIndex()).put("stored_raw", input.storedRaw())
                        .put("destination", input.destination().name());
            out.put("complete_net_refund_quote", false).putNull("refund_quote_raw");
            out.put("received_funds_verified", false).put("submission_qualified", false).put("funding_credit_raw", 0);
            return StrictJson.canonical(out);
        }
    }
    /** Import only against the actual same copied Candidate. A serialized assessment cannot mint its source. */
    public static RefundAssessment decodeRefundAssessment(byte[] bytes, Candidate currentSource) {
        Objects.requireNonNull(currentSource, "actual current copied source required");
        ObjectNode row = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "planning_frame", "capture_epoch",
                "province_id", "source_copy_sha256", "knowledge", "followup_contract", "copied_receiver",
                "recorded_builder_character_id", "stored_resource_inputs", "complete_net_refund_quote",
                "refund_quote_raw", "received_funds_verified", "submission_qualified", "funding_credit_raw"));
        RefundAssessment expected = currentSource.refundAssessment();
        StrictJson.require(StrictJson.parse(expected.toJson()).equals(row),
                "refund assessment differs from actual source, native consumer map or unqualified funding boundary");
        return expected;
    }

    public static final class Unavailable implements Result {
        private final Failure reason;
        private final byte[] wire;
        private Unavailable(Failure reason, byte[] wire) { this.reason = reason; this.wire = wire.clone(); }
        public Failure reason() { return reason; }
        public byte[] toJson() { return wire.clone(); }
    }

    /** Runtime-boundary validation. The original native receipt's origin is verified by the Root read contract. */
    public static Result projectNative(byte[] nativeBytes, PlanningFrame expected, BigInteger expectedCaptureEpoch,
            int expectedProvinceId) {
        validateExpected(expected, expectedCaptureEpoch, expectedProvinceId);
        ObjectNode node = StrictJson.object(StrictJson.parse(nativeBytes), NATIVE_FIELDS);
        StrictJson.require(NATIVE_SCHEMA.equals(StrictJson.text(node.get("schema"))), "exact native construction source schema required");
        if (!HolyLoanCodec.VERSION.equals(StrictJson.text(node.get("game_version")))
                || !HolyLoanCodec.SHA256.equalsIgnoreCase(StrictJson.text(node.get("executable_sha256")))) {
            return new Refused(Refusal.WRONG_EXACT_BUILD);
        }
        StrictJson.trueValue(node.get("read_only"));
        StrictJson.require("copied_province_construction_source".equals(StrictJson.text(node.get("scope"))), "copied construction source scope required");
        for (String key : List.of("final_action_gate_observed", "submission_qualified", "received_funds_verified")) { falseValue(node.get(key)); }
        StrictJson.integer(node.get("funding_credit_raw"), 0, 0);
        BigInteger epoch = decimal(node.get("capture_epoch"), BigInteger.ONE, StrictJson.UINT64_MAX);
        int province = (int) StrictJson.integer(node.get("province_id"), 1, Integer.MAX_VALUE);
        if (!epoch.equals(expectedCaptureEpoch) || province != expectedProvinceId) { return new Refused(Refusal.FRAME_DRIFT); }
        boolean available = bool(node.get("available"));
        byte[] persisted = persisted(expected, node);
        if (!available) {
            for (String key : List.of("native_revision", "date_raw", "actor_character_id", "copied_cancel_gate_allows", "active_record", "receiver")) {
                StrictJson.require(node.get(key).isNull(), "unavailable source must preserve null for " + key);
            }
            return new Unavailable(Failure.exact(StrictJson.text(node.get("unavailable_reason"))), persisted);
        }
        StrictJson.require(node.get("unavailable_reason").isNull(), "available source cannot carry an unavailable reason");
        BigInteger revision = decimal(node.get("native_revision"), BigInteger.ONE, StrictJson.UINT64_MAX);
        BigInteger actor = StrictJson.integer(node.get("actor_character_id"), BigInteger.ZERO, UINT32_MAX.subtract(BigInteger.ONE));
        BigInteger date = StrictJson.integer(node.get("date_raw"), BigInteger.ZERO, BigInteger.valueOf(Integer.MAX_VALUE));
        if (!revision.equals(expected.nativeRevision()) || !actor.equals(expected.actorCharacterId()) || !date.equals(expected.dateRaw())) {
            return new Refused(Refusal.FRAME_DRIFT);
        }
        Optional<ActiveRecord> active = active(node.get("active_record"));
        Receiver receiver = receiver(node.get("receiver"));
        StrictJson.require(receiver.characterId() == actor.longValueExact(), "actual receiver must be the complete command actor ID");
        boolean gate = bool(node.get("copied_cancel_gate_allows"));
        StrictJson.require(active.isPresent() || !gate, "no active record cannot accompany a successful native cancel gate");
        return new Candidate(expected, epoch, province, active, receiver, gate, persisted);
    }

    /** Persistence uses the same native schema/body and the exact full planning frame, with decimal uint64 fields. */
    public static Result decode(byte[] bytes, PlanningFrame expected, BigInteger expectedCaptureEpoch, int expectedProvinceId) {
        validateExpected(expected, expectedCaptureEpoch, expectedProvinceId);
        ObjectNode node = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "planning_frame", "native_observation"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(node.get("schema"))), "construction source persistence schema required");
        if (!frame(node.get("planning_frame")).equals(expected)) { return new Refused(Refusal.FRAME_DRIFT); }
        return projectNative(StrictJson.canonical(node.get("native_observation")), expected, expectedCaptureEpoch, expectedProvinceId);
    }

    /** Exact static effect classification is never execution or ABI qualification. */
    public static NativeEffect nativeEffect(String version, String sha256, long rva) {
        if (!HolyLoanCodec.VERSION.equals(version) || !HolyLoanCodec.SHA256.equalsIgnoreCase(sha256)) { return NativeEffect.UNKNOWN; }
        if (rva == 0x2982630L || rva == 0x310DB20L || rva == 0x24677B0L || rva == 0x285EE40L
                || rva == 0x12A38C0L || rva == 0x246CE30L || rva == 0x310D5B0L
                // Whole original RFs: nested context transfer and support registration, never quote getters.
                || rva == 0x3728020L || rva == 0x373C320L || rva == 0x3728590L || rva == 0x3727EC0L) {
            return NativeEffect.MUTATION;
        }
        return (rva == 0x2982700L || rva == 0x12AEC90L) ? NativeEffect.READ_ONLY_GATE_STATIC_ONLY : NativeEffect.UNKNOWN;
    }

    private static Optional<ActiveRecord> active(JsonNode value) {
        if (value.isNull()) { return Optional.empty(); }
        ObjectNode node = StrictJson.object(value, Set.of("record_pointer", "definition_pointer", "slot_index", "start_word",
                "recorded_builder_character_id", "recorded_cost_raw_native"));
        List<Long> vector = new ArrayList<>();
        JsonNode costs = node.get("recorded_cost_raw_native");
        StrictJson.require(costs.isArray() && costs.size() == 10, "all ten copied signed native slots required");
        for (JsonNode raw : costs) { vector.add(StrictJson.integer(raw, Long.MIN_VALUE, Long.MAX_VALUE)); }
        return Optional.of(new ActiveRecord(pointer(node.get("record_pointer")), pointer(node.get("definition_pointer")),
                (int) StrictJson.integer(node.get("slot_index"), Integer.MIN_VALUE, Integer.MAX_VALUE),
                decimal(node.get("start_word"), BigInteger.ZERO, StrictJson.UINT64_MAX),
                StrictJson.integer(node.get("recorded_builder_character_id"), 0, 0xffff_ffffL), vector));
    }
    private static Receiver receiver(JsonNode value) {
        ObjectNode node = StrictJson.object(value, Set.of("character_id", "component_pointer", "current_gold_raw"));
        Optional<Pointer> component = node.get("component_pointer").isNull() ? Optional.empty() : Optional.of(pointer(node.get("component_pointer")));
        OptionalLong gold = node.get("current_gold_raw").isNull() ? OptionalLong.empty()
                : OptionalLong.of(StrictJson.integer(node.get("current_gold_raw"), Long.MIN_VALUE, Long.MAX_VALUE));
        return new Receiver(StrictJson.integer(node.get("character_id"), 0, 0xffff_fffeL), component, gold);
    }
    private static Pointer pointer(JsonNode value) { return new Pointer(decimal(value, BigInteger.ONE, StrictJson.UINT64_MAX)); }
    private static BigInteger decimal(JsonNode value, BigInteger minimum, BigInteger maximum) {
        String raw = StrictJson.text(value);
        StrictJson.require(raw.matches("0|[1-9][0-9]{0,19}"), "canonical decimal uint64 string required");
        BigInteger result = new BigInteger(raw); unsigned(result, minimum, maximum); return result;
    }
    private static void unsigned(BigInteger value, BigInteger minimum, BigInteger maximum) {
        StrictJson.require(value != null && value.compareTo(minimum) >= 0 && value.compareTo(maximum) <= 0, "exact unsigned value outside contract range");
    }
    private static void falseValue(JsonNode value) { StrictJson.require(value.isBoolean() && !value.booleanValue(), "copied source cannot assert action or funds"); }
    private static boolean bool(JsonNode value) { StrictJson.require(value.isBoolean(), "exact boolean required"); return value.booleanValue(); }
    private static void validateExpected(PlanningFrame frame, BigInteger epoch, int province) {
        Objects.requireNonNull(frame, "frame"); StrictJson.text(frame.snapshotId()); StrictJson.text(frame.episodeRunId());
        unsigned(frame.revision(), BigInteger.ZERO, StrictJson.UINT64_MAX); unsigned(frame.nativeRevision(), BigInteger.ONE, StrictJson.UINT64_MAX);
        unsigned(frame.connectionGeneration(), BigInteger.ZERO, StrictJson.UINT64_MAX); unsigned(epoch, BigInteger.ONE, StrictJson.UINT64_MAX);
        unsigned(frame.actorCharacterId(), BigInteger.ZERO, UINT32_MAX.subtract(BigInteger.ONE));
        unsigned(frame.bridgePid(), BigInteger.ONE, UINT32_MAX); unsigned(frame.dateRaw(), BigInteger.ZERO, BigInteger.valueOf(Integer.MAX_VALUE));
        StrictJson.require(province > 0, "positive requested province required");
    }
    private static byte[] persisted(PlanningFrame source, JsonNode nativeNode) {
        ObjectNode output = StrictJson.object(); output.put("schema", SCHEMA); output.set("planning_frame", frameJson(source));
        output.set("native_observation", nativeNode); return StrictJson.canonical(output);
    }
    private static ObjectNode frameJson(PlanningFrame frame) {
        ObjectNode node = StrictJson.object(); node.put("snapshot_id", frame.snapshotId()); node.put("revision", frame.revision().toString());
        node.put("native_revision", frame.nativeRevision().toString()); node.put("date_raw", frame.dateRaw());
        node.put("actor_character_id", frame.actorCharacterId()); node.put("episode_run_id", frame.episodeRunId());
        node.put("bridge_pid", frame.bridgePid()); node.put("connection_generation", frame.connectionGeneration().toString()); return node;
    }
    private static PlanningFrame frame(JsonNode value) {
        ObjectNode node = StrictJson.object(value, FRAME_FIELDS);
        return new PlanningFrame(StrictJson.text(node.get("snapshot_id")), decimal(node.get("revision"), BigInteger.ZERO, StrictJson.UINT64_MAX),
                decimal(node.get("native_revision"), BigInteger.ONE, StrictJson.UINT64_MAX),
                StrictJson.integer(node.get("date_raw"), BigInteger.ZERO, BigInteger.valueOf(Integer.MAX_VALUE)),
                StrictJson.integer(node.get("actor_character_id"), BigInteger.ZERO, UINT32_MAX.subtract(BigInteger.ONE)),
                StrictJson.text(node.get("episode_run_id")), StrictJson.integer(node.get("bridge_pid"), BigInteger.ONE, UINT32_MAX),
                decimal(node.get("connection_generation"), BigInteger.ZERO, StrictJson.UINT64_MAX));
    }
}
