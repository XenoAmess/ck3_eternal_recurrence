package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.governance.council.CouncilModels;
import org.xar.ck3.control.governance.development.DevelopmentCodec;
import org.xar.ck3.control.governance.development.DevelopmentModels;

/** The actual two public wire producers. A constructor/hello is not an installed Root permission. */
public final class GovernanceNativeReads {
    public static final String COUNCIL_STEP = "query-council-composition-candidates-v1";
    public static final String COUNCIL_ENVELOPE_SCHEMA = "xar.ck3.council-application-main/v1";
    public static final String DEVELOPMENT_STEP = "query-steward-develop-county-candidates-v1";
    private final ReadContract<CouncilModels.Candidates> council;
    private final ReadContract<DevelopmentModels.Observation> development;
    public GovernanceNativeReads(ExactRef source, String connectedVersion, String connectedSha256) {
        Objects.requireNonNull(source); CouncilCodec.requireBuild(connectedVersion, connectedSha256);
        council = new ReadContract<>("public-council-composition-v1", new OperationKey(COUNCIL_STEP),
                Optional.of("game.query.council-composition-candidates-v1"), "public-council-composition-v1",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP, source,
                request -> {
                    requireNoArguments(request); CouncilModels.Frame frame = frame(request);
                    ObjectNode fields = StrictJson.object().put("expected_snapshot_id", frame.snapshotId())
                            .put("public_revision", frame.publicRevision()).put("native_revision", frame.nativeRevision())
                            .put("date_raw", frame.dateRaw()).put("owner_character_id", frame.ownerId())
                            .put("position_key", "councillor_steward");
                    return new NativeRequest(COUNCIL_STEP, Optional.of("game.query.council-composition-candidates-v1"), new RawJson(StrictJson.canonical(fields)));
                }, receipt -> {
                    ObjectNode result = envelope(receipt, COUNCIL_STEP, "council_composition_candidates");
                    StrictJson.require(CouncilCodec.text(result, "status").equals("available"), "public council result is unavailable");
                    return CouncilCodec.decodeNative(StrictJson.canonical(result.get("council_composition_candidates")), frame(receipt.request()), CouncilModels.Position.STEWARD, connectedVersion, connectedSha256);
                });
        development = new ReadContract<>("public-steward-develop-county-candidates-v1", new OperationKey(DEVELOPMENT_STEP),
                Optional.of("game.command.query-steward-develop-county-candidates-v1"), "public-steward-develop-county-candidates-v1",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP, source,
                request -> {
                    requireNoArguments(request);
                    return new NativeRequest(DEVELOPMENT_STEP, Optional.of("game.command.query-steward-develop-county-candidates-v1"), new RawJson(new byte[] {'{', '}'}));
                }, receipt -> {
                    ObjectNode result = envelope(receipt, DEVELOPMENT_STEP, "steward_develop_county_candidates");
                    var identity = receipt.request().before().frame().identity();
                    var value = DevelopmentCodec.decode(StrictJson.canonical(result.get("steward_develop_county_candidates")),
                            new DevelopmentModels.Frame(identity.nativeRevision(), identity.dateRaw().intValueExact()));
                    StrictJson.require(value.provenance().gameVersion().equals(connectedVersion)
                            && value.provenance().executableSha256().equalsIgnoreCase(connectedSha256), "development result belongs to another connected build");
                    String expectedStatus = value instanceof DevelopmentModels.Unavailable ? "unavailable" : "available";
                    StrictJson.require(CouncilCodec.text(result, "status").equals(expectedStatus), "development envelope/payload status mismatch");
                    return value;
                });
    }
    public ReadContract<CouncilModels.Candidates> council() { return council; }
    public ReadContract<DevelopmentModels.Observation> development() { return development; }
    public List<ReadContract<?>> registeredContracts() { return List.of(council, development); }
    public static CouncilModels.Frame frame(PlanningReadRequest request) {
        var current = request.before().frame();
        return new CouncilModels.Frame(current.snapshotId(), current.revision(), current.identity().nativeRevision(),
                current.identity().dateRaw().intValueExact(), current.identity().player().intValueExact());
    }
    private static void requireNoArguments(PlanningReadRequest request) {
        StrictJson.require(request.arguments().members().isEmpty(), "fixed public governance read accepts no injected native fields");
    }
    static ObjectNode envelope(PlanningReadReceipt receipt, String step, String payloadField) {
        verifyGuards(receipt);
        ObjectNode frame = StrictJson.object(StrictJson.parse(receipt.original().originalFrame().bytes()),
                Set.of("type", "protocol_version", "request_id", "ok", "result"));
        StrictJson.require(CouncilCodec.text(frame, "type").equals("command_result")
                && CouncilCodec.number(frame, "protocol_version", 1, 1) == 1
                && CouncilCodec.text(frame, "request_id").equals(receipt.requestId()), "governance original command-result correlation mismatch");
        StrictJson.trueValue(frame.get("ok"));
        boolean council = COUNCIL_STEP.equals(step);
        ObjectNode result = StrictJson.object(frame.get("result"), council
                ? Set.of("schema", "step", "accepted", "status", "query_sequence", "snapshot_revision", payloadField, "backend_id")
                : Set.of("step", "accepted", "status", "query_sequence", "snapshot_revision", payloadField, "backend_id"));
        if (council) StrictJson.require(COUNCIL_ENVELOPE_SCHEMA.equals(CouncilCodec.text(result, "schema")), "actual Council application-main result schema mismatch");
        StrictJson.require(CouncilCodec.text(result, "step").equals(step) && receipt.request().operation().value().equals(step), "governance read operation mismatch");
        StrictJson.trueValue(result.get("accepted"));
        CouncilCodec.u64(result.get("query_sequence"), true);
        var actual = receipt.request().before().frame();
        BigInteger expectedOuterRevision = council ? actual.revision() : actual.identity().nativeRevision();
        StrictJson.require(CouncilCodec.u64(result.get("snapshot_revision"), true).equals(expectedOuterRevision),
                council ? "Council outer public revision differs from actual frame" : "development outer native revision differs from actual frame");
        CouncilCodec.text(result, "backend_id");
        StrictJson.require(receipt.original().nativeOk() && receipt.original().originalResultToken().isPresent()
                && StrictJson.parse(receipt.original().originalResultToken().orElseThrow().bytes()).equals(result), "governance original token differs from full native frame");
        return result;
    }
    public static void verifyGuards(PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt);
        for (var guard : List.of(receipt.before(), receipt.after())) {
            StrictJson.require(guard.binding().observed().equals(receipt.request().before())
                    && guard.binding().source().equals(receipt.request().source())
                    && guard.binding().sessionId().equals(receipt.request().sessionId())
                    && guard.paused() && guard.mapReady() && guard.playerAlive(), "governance query crossed its living paused Game/frame");
        }
        StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()), "complete governance semantic binding drift");
    }
}
