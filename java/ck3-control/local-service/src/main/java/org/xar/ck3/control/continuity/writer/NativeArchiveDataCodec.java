package org.xar.ck3.control.continuity.writer;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Sole strict DATA parser extracted from the live archive. No writer or gameplay qualification. */
public final class NativeArchiveDataCodec {
    private static final int META_LIMIT = StrictJson.EXPLICIT_MAX_BYTES;
    private static final String DISPATCH_SCHEMA = "xar.native-dispatch-archive/v1";
    private static final String DISPATCH_WITH_OUTBOUND_SCHEMA = "xar.native-dispatch-archive/v2";
    private static final String DISPATCH_WITH_CUSTODY_SCHEMA = "xar.native-dispatch-archive/v3";
    private static final String DISPATCH_WITH_FAILURE_SCHEMA = "xar.native-dispatch-archive/v4";
    private static final String REQUEST_SCHEMA = "xar.native-request-archive/v1";
    private static final String REQUEST_WITH_PREPARATION_SCHEMA = "xar.native-request-archive/v2";
    private static final String READ_SCHEMA = "xar.planning-read-archive/v1";
    private static final String READ_WITH_ADOPTION_SCHEMA = "xar.planning-read-archive/v2";
    private static final String PHYSICAL_STATUS_READ_SCHEMA = "xar.planning-read-archive/v3";
    private static final String RETAINED_MATERIAL_READ_SCHEMA = "xar.planning-read-archive/v4";
    /** Byte lookup only. Every return is independently bounded and matched to its exact ref.
     * This port carries no writer, source, transport, replay or Game authority. */
    @FunctionalInterface public interface OriginalBytes {
        byte[] read(ExactRef original, int maximumBytes) throws IOException;
    }
    /** A DATA receipt is not a live archived-read qualification or historical-head proof. */
    public record ReadData(ExactRef original, PlanningReadReceipt receipt) {
        public ReadData { Objects.requireNonNull(original); Objects.requireNonNull(receipt); }
    }
    private final OriginalBytes originals;
    public NativeArchiveDataCodec(OriginalBytes originals) { this.originals = Objects.requireNonNull(originals); }
    /** Uses the existing held native exact-file reader; no store, writer, lock or file is created.
     * Each read retains its actual native identity before/after. Original historical identity,
     * canonical membership, source admission and late-adoption head are not granted here. */
    public static NativeArchiveDataCodec retainedFiles() {
        return new NativeArchiveDataCodec((original, maximum) -> LedgerFiles.exact(original, maximum).bytes());
    }
    /** Reopens the actual READ metadata, args, dispatch packet/outbound/custody and guard byte
     * closure. The original contract may pure-replay these DATA; its real domain verifier must
     * still establish source/history/qualification. Missing input throws, never skips or repairs. */
    public ReadData readData(ExactRef original) throws IOException {
        PlanningReadReceipt read = decodeRead(original);
        for (PlanningReadGuard guard : List.of(read.before(), read.after())) {
            readBytes(guard.binding().nativeEvidence(), WriterContracts.MAX_PIN_BYTES);
            readBytes(guard.binding().capabilityEvidence(), WriterContracts.MAX_PIN_BYTES);
            for (ExactRef basis : guard.binding().supportingEvidence()) readBytes(basis, WriterContracts.MAX_PIN_BYTES);
             if (guard.binding().origin() instanceof CommandOrigin.PhysicalStatusOnly physical) {
                 var identity = physical.identity();
                 readBytes(identity.heartbeatEvidence(), WriterContracts.MAX_PIN_BYTES);
                 if(identity.sourceQualification().isPresent())readBytes(identity.sourceQualification().orElseThrow(), WriterContracts.MAX_PIN_BYTES);
                 if(identity.epochManifest().isPresent())readBytes(identity.epochManifest().orElseThrow(), WriterContracts.MAX_PIN_BYTES);
             }
        }
        readBytes(read.request().source().sourceRef(), WriterContracts.MAX_PIN_BYTES);
        if (read.adoption().isPresent())
            readBytes(read.adoption().orElseThrow().currentRequest().source().sourceRef(), WriterContracts.MAX_PIN_BYTES);
        if (read.retainedMaterial().isPresent())
            readBytes(read.retainedMaterial().orElseThrow().original(), RawJson.MAXIMUM_BYTES);
        return new ReadData(original, read);
    }
    private byte[] readBytes(ExactRef original, int maximumBytes) throws IOException {
        Objects.requireNonNull(original);
        if (maximumBytes < 1 || maximumBytes > WriterContracts.MAX_PIN_BYTES
                || original.bytes() < 0 || original.bytes() > maximumBytes)
            throw new IOException("explicit finite original DATA bound required");
        byte[] bytes = Objects.requireNonNull(originals.read(original, maximumBytes)).clone();
        if (bytes.length != original.bytes() || bytes.length > maximumBytes)
            throw new IOException("retained DATA length differs from original ref");
        try {
            String digest = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes));
            if (!digest.equals(original.sha256())) throw new IOException("retained DATA hash differs from original ref");
        } catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
        return bytes;
    }
    private RawJson token(ExactRef original) throws IOException { return new RawJson(readBytes(original, RawJson.MAXIMUM_BYTES)); }
    public NativeActionPort.DispatchOutcome decodeDispatchData(ExactRef original) throws IOException {
            ObjectNode row = metadata(original); String archiveSchema = text(row, "schema");
            StrictJson.require(DISPATCH_SCHEMA.equals(archiveSchema) || DISPATCH_WITH_OUTBOUND_SCHEMA.equals(archiveSchema)
                    || DISPATCH_WITH_CUSTODY_SCHEMA.equals(archiveSchema) || DISPATCH_WITH_FAILURE_SCHEMA.equals(archiveSchema), "exact dispatch archive schema required");
            boolean failurePresent = DISPATCH_WITH_FAILURE_SCHEMA.equals(archiveSchema);
            boolean custodyPresent = DISPATCH_WITH_CUSTODY_SCHEMA.equals(archiveSchema);
            boolean outboundPresent = custodyPresent || DISPATCH_WITH_OUTBOUND_SCHEMA.equals(archiveSchema); String id = text(row, "request_id");
            StrictJson.require(!outboundPresent || text(row, "kind").equals("ACK"), "outbound dispatch schema is an actual ACK branch");
            StrictJson.require(!failurePresent || text(row, "kind").equals("UNKNOWN"), "failure-cause dispatch schema is an actual UNKNOWN branch");
            return switch (text(row, "kind")) {
                case "ACK" -> {
                    fields(row, custodyPresent ? Set.of("schema", "kind", "request_id", "native_ok", "frame_ref", "packet_ref", "outbound_packet_ref", "custody")
                            : outboundPresent ? Set.of("schema", "kind", "request_id", "native_ok", "frame_ref", "packet_ref", "outbound_packet_ref")
                            : Set.of("schema", "kind", "request_id", "native_ok", "frame_ref", "packet_ref"), "result_ref");
                    var ack = new NativeActionPort.AckReceived(id, bool(row, "native_ok"),
                            row.has("result_ref") ? Optional.of(token(ref(row, "result_ref"))) : Optional.empty(),
                            token(ref(row, "frame_ref")), readBytes(ref(row, "packet_ref"), WriterContracts.MAX_PIN_BYTES),
                            outboundPresent ? Optional.of(new NativeActionPort.OutboundPacket(id, readBytes(ref(row, "outbound_packet_ref"), WriterContracts.MAX_PIN_BYTES))) : Optional.empty(),
                            custodyPresent ? Optional.of(NativeRequestChronologyCodec.decode(row.get("custody"))) : Optional.empty());
                    verifyAck(ack); yield ack;
                }
                case "REJECTED_BEFORE_DISPATCH" -> {
                    fields(row, Set.of("schema", "kind", "request_id", "stage", "request_bytes_written", "reason"), "diagnostic_ref");
                    StrictJson.require(text(row, "stage").equals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE.name()), "exact zero-dispatch stage required");
                    yield new NativeActionPort.RejectedBeforeDispatch(id, new NativeActionPort.ZeroDispatchProof(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,
                            StrictJson.integer(row.get("request_bytes_written"), 0, 0), text(row, "reason"),
                            row.has("diagnostic_ref") ? Optional.of(token(ref(row, "diagnostic_ref"))) : Optional.empty()));
                }
                case "UNKNOWN" -> {
                    fields(row, failurePresent ? Set.of("schema", "kind", "request_id", "reason", "request_packet_ref", "failure_cause")
                            : Set.of("schema", "kind", "request_id", "reason", "request_packet_ref"), "raw_return_ref");
                    yield new NativeActionPort.Unknown(id, text(row, "reason"), readBytes(ref(row, "request_packet_ref"), WriterContracts.MAX_PIN_BYTES),
                            row.has("raw_return_ref") ? Optional.of(token(ref(row, "raw_return_ref"))) : Optional.empty(),
                            failurePresent ? Optional.of(NativeFailureCauseCodec.decodeValue(row.get("failure_cause"))) : Optional.empty());
                }
                default -> throw new IOException("unrecognized archived dispatch kind");
            };
    }
    public NativeRequest decodePreparedRequestData(ExactRef original) throws IOException {
            ObjectNode row = metadata(original); String actualSchema = text(row, "schema");
            StrictJson.require(REQUEST_SCHEMA.equals(actualSchema) || REQUEST_WITH_PREPARATION_SCHEMA.equals(actualSchema), "exact native request archive schema required");
            boolean hasPreparation = REQUEST_WITH_PREPARATION_SCHEMA.equals(actualSchema);
            fields(row, hasPreparation ? Set.of("schema", "step", "additional_fields_ref", "preparation_evidence")
                    : Set.of("schema", "step", "additional_fields_ref"), "required_capability");
            List<ExactRef> evidence = List.of();
            if (hasPreparation) {
                JsonNode values = row.get("preparation_evidence");
                StrictJson.require(values != null && values.isArray() && !values.isEmpty() && values.size() <= 32, "nonempty bounded native preparation evidence array required");
                var refs = new java.util.ArrayList<ExactRef>(); values.forEach(value -> refs.add(ExactRef.fromJson(value))); evidence = List.copyOf(refs);
            }
            var result = new NativeRequest(text(row, "step"), row.has("required_capability") ? Optional.of(text(row, "required_capability")) : Optional.empty(), token(ref(row, "additional_fields_ref")), evidence);
            verifyPreparationOriginals(result); return result;
    }
    private void verifyPreparationOriginals(NativeRequest original) throws IOException {
        // Exact originals are custody metadata. Their role/schema and transitive proof closure are
        // replayed by the installed preparation owner, never inferred from command arguments here.
        for (ExactRef retained : original.preparationEvidence()) readBytes(retained, WriterContracts.MAX_PIN_BYTES);
    }

    private PlanningReadRequest planningRequest(JsonNode request) throws IOException {
        StrictJson.require(request != null && request.isObject(), "archived typed planning request required");
        return CommandOriginCodec.planningRequest(request,
                OpportunityJson.object(OpportunityJson.parse(token(ExactRef.fromJson(request.get("arguments_ref"))).bytes()), "archived planning arguments"));
    }
    private Optional<PlanningReadAdoption> adoption(JsonNode value) throws IOException {
        StrictJson.require(value != null, "v2 read requires explicit adoption object or null");
        if (value.isNull()) return Optional.empty();
        ObjectNode row = StrictJson.object(value, Set.of("current_request", "current_semantic_ref", "original_unknown_ref",
                "prepared_request_ref", "original_head_sequence", "original_head_digest"));
        NativeActionPort.DispatchOutcome unknown = decodeDispatchData(ref(row, "original_unknown_ref"));
        if (!(unknown instanceof NativeActionPort.Unknown originalUnknown))
            throw new IOException("late read requires its actual archived UNKNOWN dispatch");
        return Optional.of(new PlanningReadAdoption(planningRequest(row.get("current_request")),
                DriverJson.object(token(ref(row, "current_semantic_ref")).bytes(), RawJson.MAXIMUM_BYTES),
                originalUnknown, decodePreparedRequestData(ref(row, "prepared_request_ref")),
                StrictJson.integer(row.get("original_head_sequence"), 0, StrictJson.MAX_SAFE_INTEGER), text(row, "original_head_digest")));
    }
    PlanningReadReceipt decodeRead(ExactRef original) throws IOException {
            ObjectNode row = metadata(original); String version = text(row, "schema");
              StrictJson.require(READ_SCHEMA.equals(version) || READ_WITH_ADOPTION_SCHEMA.equals(version)
                      || PHYSICAL_STATUS_READ_SCHEMA.equals(version) || RETAINED_MATERIAL_READ_SCHEMA.equals(version), "exact planning-read archive version required");
            boolean historical = READ_SCHEMA.equals(version);
             boolean physical = PHYSICAL_STATUS_READ_SCHEMA.equals(version);
              boolean material = RETAINED_MATERIAL_READ_SCHEMA.equals(version);
             StrictJson.object(row, historical || physical ? Set.of("schema", "contract_id", "request_id", "request", "before", "after", "original_ref")
                     : material ? Set.of("schema", "contract_id", "request_id", "request", "before", "after", "original_ref", "adoption", "retained_material")
                     : Set.of("schema", "contract_id", "request_id", "request", "before", "after", "original_ref", "adoption"));
            PlanningReadRequest request = planningRequest(row.get("request"));
            NativeActionPort.DispatchOutcome dispatch = decodeDispatchData(ref(row, "original_ref"));
            if (!(dispatch instanceof NativeActionPort.AckReceived ack)) throw new IOException("planning read requires its actual original ACK");
            PlanningReadReceipt result = new PlanningReadReceipt(request, text(row, "contract_id"), text(row, "request_id"),
                     CommandOriginCodec.planningGuard(row.get("before")), CommandOriginCodec.planningGuard(row.get("after")), ack,
                     historical || physical ? Optional.empty() : adoption(row.get("adoption")), historical
                             ? PlanningReadReceipt.ArchiveVersion.HISTORICAL_V1 : physical
                                      ? PlanningReadReceipt.ArchiveVersion.PHYSICAL_STATUS_V3 : material
                                              ? PlanningReadReceipt.ArchiveVersion.RETAINED_MATERIAL_V4 : PlanningReadReceipt.ArchiveVersion.CURRENT_V2,
                     material ? Optional.of(retainedMaterial(row.get("retained_material"))) : Optional.empty());
            return result;
    }
    private static PlanningReadReceipt.RetainedMaterial retainedMaterial(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("kind", "original"));
        PlanningReadReceipt.RetainedMaterial.Kind kind = PlanningReadReceipt.RetainedMaterial.Kind.valueOf(text(row, "kind"));
        return new PlanningReadReceipt.RetainedMaterial(kind, ref(row, "original"));
    }
    static void verifyAck(NativeActionPort.AckReceived ack) throws IOException {
        NativeWire.Frame decoded = NativeWire.decode(ack.originalPacket());
        if (!(decoded instanceof NativeWire.CommandResult result) || !result.requestId().equals(ack.requestId())
                || result.nativeOk() != ack.nativeOk() || !Arrays.equals(result.payload().value(), ack.originalFrame().bytes()))
            throw new IOException("ACK metadata must bind the complete original Native packet");
        Optional<RawJson> actualToken = result.result().token().map(value -> new RawJson(value.value()));
        if (!actualToken.equals(ack.originalResultToken())) throw new IOException("ACK missing/null/value token differs from original packet");
        if (ack.outbound().isPresent()) {
            NativeActionPort.OutboundPacket original = ack.outbound().orElseThrow();
            NativeWire.ExecuteRequest sent = NativeWire.decodeExecuteRequest(original.originalPacket());
            if (!original.requestId().equals(ack.requestId()) || !sent.requestId().equals(ack.requestId()))
                throw new IOException("ACK must bind the actual original outbound execute request ID");
        }
        ack.custody().ifPresent(value -> value.verify(ack));
    }

    private ObjectNode metadata(ExactRef ref) throws IOException {
        JsonNode value = StrictJson.parse(readBytes(ref, META_LIMIT), META_LIMIT);
        StrictJson.require(value instanceof ObjectNode, "typed archive metadata object required"); return (ObjectNode) value;
    }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    private static boolean bool(ObjectNode row, String field) {
        JsonNode node = row.get(field); StrictJson.require(node != null && node.isBoolean(), "exact archive boolean required: " + field); return node.booleanValue();
    }
    private static ExactRef ref(ObjectNode row, String field) { return ExactRef.fromJson(row.get(field)); }
    private static void fields(ObjectNode row, Set<String> required, String... optional) {
        Set<String> expected = new HashSet<>(required);
        for (String key : optional) if (row.has(key)) expected.add(key);
        StrictJson.object(row, Set.copyOf(expected));
    }
    private static void schema(ObjectNode row, String expected) { StrictJson.require(text(row, "schema").equals(expected), "exact archive schema required"); }

}
