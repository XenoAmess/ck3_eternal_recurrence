package org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.OptionalInt;
import java.util.Set;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.china_career.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.ChinaCareerContract.*;

/** One public request codec and original service projection. Domain algorithms remain the existing typed producers. */
public final class ChinaCareerCodec {
    private ChinaCareerCodec() { }
    public static Request decodeRequest(Kind kind, RawJson original) {
        Set<String> fields = new HashSet<>(Set.of("request_nonce", "expected_revision"));
        if (kind.ownerArgument()) fields.add("owner_character_id");
        if (kind.subjectArgument()) fields.add("subject_character_id");
        ObjectNode row = StrictJson.object(StrictJson.parse(original.bytes()), fields);
        JsonNode nonce = row.get("request_nonce");
        StrictJson.require(nonce != null && nonce.isTextual(), "request_nonce must be a JSON string");
        return new Request(kind, nonce.textValue(), PublicUnsigned64.parse(row.get("expected_revision"),
                PublicUnsigned64.Minimum.ZERO, PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL),
                kind.ownerArgument() ? OptionalInt.of(id(row.get("owner_character_id"))) : OptionalInt.empty(),
                kind.subjectArgument() ? OptionalInt.of(id(row.get("subject_character_id"))) : OptionalInt.empty());
    }
    public static RawJson encodeRequest(Request request) {
        Objects.requireNonNull(request);
        ObjectNode row = StrictJson.object().put("request_nonce", request.requestNonce())
                .put("expected_revision", decimal(request.expectedRevision(), false));
        request.ownerCharacterId().ifPresent(value -> row.put("owner_character_id", value));
        request.subjectCharacterId().ifPresent(value -> row.put("subject_character_id", value));
        return raw(row);
    }
    /** Same exact native fields as the unchanged Python primitive producer; no encoded public alias reaches Native. */
    public static RawJson nativeFields(Request request, Frame frame) {
        ObjectNode row = StrictJson.object().put("request_nonce", request.requestNonce());
        if (request.kind() != Kind.MANAGER_SELECTOR) row.put("owner_character_id", request.owner(frame));
        if (request.kind().subjectArgument()) row.put("subject_character_id", request.subject(frame));
        return raw(row);
    }
    public static DomainFrame decodeDomain(Kind kind, RawJson nativeOriginal, CareerJson.FrameBinding binding) {
        return switch (kind) {
            case OWNER -> new Owner(OwnerCareerFrames.decodeOwner(nativeOriginal, binding));
            case CAREER_HC -> new Career(OwnerCareerFrames.decodeCareer(nativeOriginal, binding));
            case COLLECTIVE -> new Collective(CollectiveWorkforceFrame.decode(nativeOriginal, binding));
            case NORMAL_EXIT -> new NormalExit(NormalExitWorkforceFrame.decode(nativeOriginal, binding));
            case MANAGER_SELECTOR -> new Selector(ManagerSelectorFrame.decode(nativeOriginal, binding));
            case MANAGER_GOVERNANCE -> new Governance(ManagerGovernanceFrame.decode(nativeOriginal, binding));
        };
    }
    public static NativeObservation nativeObservation(Kind kind, RawJson token, CareerJson.FrameBinding binding,
            BigInteger sequence, String backend) {
        return new NativeObservation(kind, binding, decodeDomain(kind, token, binding), token, sequence, backend);
    }
    public static Response response(Request request, Frame frame, NativeObservation nativeValue) {
        StrictJson.require(request.kind() == nativeValue.kind() && frame.binding(request).equals(nativeValue.binding()),
                "public response crossed the actual requested same-frame owner/subject binding");
        DomainFrame decoded = decodeDomain(request.kind(), nativeValue.originalFrame(), nativeValue.binding());
        StrictJson.require(decoded.equals(nativeValue.domain()), "typed China career facts differ from their actual original token");
        ObjectNode row = object(nativeValue.originalFrame()).deepCopy();
        row.put("snapshot_revision", decimal(frame.nativeRevision(), true));
        ObjectNode binding = StrictJson.object().put("request_nonce", request.requestNonce())
                .put("snapshot_id", frame.snapshotId()).put("revision", decimal(frame.publicRevision(), false))
                .put("native_revision", decimal(frame.nativeRevision(), true)).put("date_raw", frame.dateRaw())
                .put("paused", true).put("player_character_id", frame.playerId());
        if (request.kind() == Kind.MANAGER_SELECTOR) {
            JsonNode selection = row.get("selection");
            if (selection.isNull()) { row.putNull("manager_character_id"); row.putNull("subordinate_character_id"); }
            else { row.set("manager_character_id", selection.get("manager_character_id")); row.set("subordinate_character_id", selection.get("subordinate_character_id")); }
            row.set("binding", binding); row.put("query_sequence", decimal(nativeValue.querySequence(), true));
            row.put("backend_id", nativeValue.backendId());
            return new Response(request, frame, nativeValue, raw(row));
        }
        binding.put("connection_generation", decimal(frame.generation(), true))
                .put("subject_character_id", decoded.header().subject_character_id())
                .put("expected_revision", decimal(request.expectedRevision(), false));
        boolean unavailableCollective = request.kind() == Kind.COLLECTIVE
                && decoded.header().status() == CareerJson.Availability.UNAVAILABLE;
        if (unavailableCollective) binding.putNull("owner_character_id");
        else binding.put("owner_character_id", request.owner(frame));
        ObjectNode source = StrictJson.object().put("bridge_version", frame.originalHello().bridgeVersion())
                .put("game_adapter_id", frame.originalHello().adapterId()).put("backend_id", nativeValue.backendId())
                .put("connection_generation", decimal(frame.generation(), true)).put("snapshot_id", frame.snapshotId())
                .put("revision", decimal(frame.publicRevision(), false)).put("native_revision", decimal(frame.nativeRevision(), true))
                .put("date_raw", frame.dateRaw()).put("paused", true).put("player_character_id", frame.playerId());
        if (request.kind() == Kind.OWNER || request.kind() == Kind.CAREER_HC) row.put("source_backend_id", "native-headless");
        else {
            ObjectNode provenance = assertObject(row.get("provenance"));
            source.set("consumer_id", provenance.get("consumer_id"));
            if (request.kind() == Kind.MANAGER_GOVERNANCE) {
                JsonNode subject = row.get("subject_binding"); binding.set("subject_binding_kind", subject.get("kind"));
                JsonNode dependency = subject.get("bounded_ai_manager_dependency");
                binding.set("bounded_ai_manager_dependency", dependency.get("status").textValue().equals("available")
                        ? dependency.get("value") : com.fasterxml.jackson.databind.node.NullNode.getInstance());
            }
        }
        row.set("build", StrictJson.object().put("version", CareerJson.VERSION).put("exe_sha256", CareerJson.EXE_SHA256));
        row.set(request.kind() == Kind.NORMAL_EXIT ? "bridge_source" : "source", source);
        row.set("binding", binding);
        return new Response(request, frame, nativeValue, raw(row));
    }
    public static RawJson encodeResponse(Response value) {
        Response rebuilt = response(value.request(), value.frame(), value.nativeObservation());
        StrictJson.require(rebuilt.publicJson().equals(value.publicJson()), "public response lost original native/typed source binding");
        return value.publicJson();
    }
    /** Internal typed diagnostic serialization; the sole MCP adapter retains its existing error envelope. */
    public static RawJson encodeFault(Fault value) {
        ObjectNode row = StrictJson.object().put("kind", value.kind().name())
                .put("python_error", value.pythonName()).put("message", value.originalMessage());
        if (value.originalRead().isEmpty()) row.putNull("original_read");
        else {
            ExactRef ref = value.originalRead().orElseThrow();
            row.putObject("original_read").put("path", ref.path()).put("bytes", ref.bytes()).put("sha256", ref.sha256());
        }
        return raw(row);
    }
    public static Fault decodeFault(RawJson original) {
        ObjectNode row = StrictJson.object(StrictJson.parse(original.bytes()), Set.of("kind", "python_error", "message", "original_read"));
        ErrorKind kind = ErrorKind.valueOf(StrictJson.text(row.get("kind")));
        Optional<ExactRef> ref = Optional.empty();
        if (!row.get("original_read").isNull()) {
            ObjectNode value = StrictJson.object(row.get("original_read"), Set.of("path", "bytes", "sha256"));
            ref = Optional.of(new ExactRef(StrictJson.text(value.get("path")), StrictJson.integer(value.get("bytes"), 1, Long.MAX_VALUE),
                    StrictJson.text(value.get("sha256"))));
        }
        Fault fault = new Fault(kind, StrictJson.text(row.get("message")), ref);
        StrictJson.require(fault.pythonName().equals(StrictJson.text(row.get("python_error"))), "China career fault class changed");
        return fault;
    }
    /** Original legacy encoded steps are compatibility DATA only; registered native reads use fixed step + typed fields. */
    public static String encodedLegacyStep(Request request, Frame frame) {
        String token = java.util.HexFormat.of().formatHex(request.requestNonce().getBytes(StandardCharsets.US_ASCII));
        if (request.kind() == Kind.MANAGER_SELECTOR) return request.kind().step() + "-" + token;
        if (request.kind() == Kind.MANAGER_GOVERNANCE)
            return request.kind().step() + "-" + request.subject(frame) + "-" + request.owner(frame) + "-" + token;
        return request.kind().step() + "-" + request.owner(frame) + "-" + token;
    }
    /** The sole original numeric formatter is also consumed by the fixed registered READ history projection. */
    public static RawJson numericExecuteResult(NativeObservation nativeValue,RawJson originalEnvelope) {
        Objects.requireNonNull(nativeValue);Kind kind=nativeValue.kind();var binding=nativeValue.binding();
        StrictJson.require(ChinaCareerCodec.decodeDomain(kind,nativeValue.originalFrame(),binding).equals(nativeValue.domain()),
                "original EXECUTE numeric payload differs from its existing typed decoder");
        ObjectNode row=StrictJson.object(ChinaCareerCodec.object(originalEnvelope),Set.of("step","accepted","status","query_sequence","snapshot_revision",kind.payload(),"backend_id")).deepCopy();
        StrictJson.trueValue(row.get("accepted"));StrictJson.require(StrictJson.text(row.get("step")).equals(kind.step())
                &&StrictJson.integer(row.get("query_sequence"),BigInteger.ONE,StrictJson.UINT64_MAX).equals(nativeValue.querySequence())
                &&StrictJson.integer(row.get("snapshot_revision"),BigInteger.ONE,StrictJson.UINT64_MAX).equals(binding.native_revision())
                &&StrictJson.text(row.get("status")).equals(nativeValue.domain().header().status().name().toLowerCase(java.util.Locale.ROOT))
                &&StrictJson.text(row.get("backend_id")).equals(nativeValue.backendId())
                &&row.get(kind.payload()).equals(ChinaCareerCodec.object(nativeValue.originalFrame())),"original EXECUTE envelope and decoded payload differ");
        ObjectNode normalized=ChinaCareerCodec.object(nativeValue.originalFrame()).deepCopy();
        row.set(kind.payload(),normalized);
        if(kind==Kind.MANAGER_SELECTOR){
            normalized.properties().forEach(field->row.set(field.getKey(),field.getValue()));
            JsonNode selection=normalized.get("selection");
            if(selection.isNull()){row.putNull("manager_character_id");row.putNull("subordinate_character_id");}
            else{row.set("manager_character_id",selection.get("manager_character_id"));row.set("subordinate_character_id",selection.get("subordinate_character_id"));}
        }
        row.put("query_sequence",nativeValue.querySequence()).put("snapshot_revision",binding.native_revision())
                .put("queried_snapshot_id",binding.snapshot_id()).put("queried_revision",binding.revision())
                .put("queried_native_revision",binding.native_revision()).put("queried_connection_generation",binding.connection_generation());
        return new RawJson(StrictJson.canonical(row,StrictJson.EXPLICIT_MAX_BYTES));
    }
    public static RawJson publicExecuteResult(NativeObservation nativeValue,RawJson originalEnvelope) {
        ObjectNode row=ChinaCareerCodec.object(numericExecuteResult(nativeValue,originalEnvelope));
        for(String field:List.of("query_sequence","snapshot_revision","queried_native_revision","queried_connection_generation"))
            row.put(field,decimal(StrictJson.integer(row.get(field),BigInteger.ONE,StrictJson.UINT64_MAX),true));
        row.put("queried_revision",decimal(StrictJson.integer(row.get("queried_revision"),BigInteger.ZERO,StrictJson.UINT64_MAX),false));
        ((ObjectNode)row.get(nativeValue.kind().payload())).put("snapshot_revision",decimal(nativeValue.binding().native_revision(),true));
        PublicSnapshotCodec.publicNumbers(row,"$");return new RawJson(StrictJson.canonical(row,StrictJson.EXPLICIT_MAX_BYTES));
    }
    public static String encodedExecuteStep(NativeObservation nativeValue) {
        // The registered decoder proved these typed original request fields before this finite reconstruction.
        var binding=Objects.requireNonNull(nativeValue).binding();String nonce=HexFormat.of().formatHex(binding.request_nonce().getBytes(StandardCharsets.US_ASCII));
        return nativeValue.kind().step()+"-"+(nativeValue.kind()==Kind.MANAGER_SELECTOR?nonce:
                nativeValue.kind()==Kind.MANAGER_GOVERNANCE?binding.subject_character_id()+"-"+binding.owner_character_id()+"-"+nonce:
                binding.owner_character_id()+"-"+nonce);
    }

    public static ObjectNode object(RawJson raw) {
        try { return NativeWire.object(NativeWire.parse(raw.bytes())); }
        catch (IOException error) { throw new IllegalArgumentException("invalid China career original JSON", error); }
    }
    private static ObjectNode assertObject(JsonNode row) {
        StrictJson.require(row instanceof ObjectNode, "original object required"); return (ObjectNode) row;
    }
    private static int id(JsonNode value) { return (int) StrictJson.integer(value, 1, Integer.MAX_VALUE); }
    private static RawJson raw(ObjectNode value) { return new RawJson(StrictJson.canonical(value, StrictJson.EXPLICIT_MAX_BYTES)); }
    private static String decimal(BigInteger value, boolean positive) {
        return PublicUnsigned64.canonical(value, positive ? PublicUnsigned64.Minimum.ONE : PublicUnsigned64.Minimum.ZERO);
    }
}
