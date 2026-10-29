package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionCoordinatorPort;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.governance.council.CouncilModels;
import org.xar.ck3.control.governance.development.DevelopmentModels;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Concrete public handlers. Only the Root's existing coordinator may submit an actual qualified action. */
public final class GovernancePublicService {
    public record CouncilRequest(CouncilModels.Frame requested) { public CouncilRequest { Objects.requireNonNull(requested); } }
    public record DevelopmentRequest(BigInteger expectedRevision) {
        public DevelopmentRequest { CouncilModels.uint64(expectedRevision, false); }
    }
    public record ChangeRequest(int councillorId, int countyTitleId, BigInteger expectedRevision, boolean replaceExisting) {
        public ChangeRequest { StrictJson.require(councillorId > 0 && countyTitleId > 0, "positive int32 development action identities required"); CouncilModels.uint64(expectedRevision, true); }
    }
    public record CouncilReply(CouncilModels.Candidates value, PlanningReadResult.Known<CouncilModels.Candidates> original) {
        public CouncilReply { Objects.requireNonNull(value); Objects.requireNonNull(original); StrictJson.require(value.equals(original.value()), "public council result differs from the actual read"); }
    }
    public record DevelopmentReply(DevelopmentModels.Observation value, PlanningReadResult.Known<DevelopmentModels.Observation> original, Optional<String> sourceBackendId) {
        public DevelopmentReply { Objects.requireNonNull(value); Objects.requireNonNull(original); Objects.requireNonNull(sourceBackendId); sourceBackendId.ifPresent(StrictJson::text); StrictJson.require(value.equals(original.value()), "public development result differs from the actual read"); }
    }
    @FunctionalInterface public interface CurrentPlanningFrame { PlanningRequest current(); }
    /** Optional only because the old .4 Python driver has no action executor; no fallback or fake ACK. */
    @FunctionalInterface public interface QualifiedDevelopmentAction {
        ActionCommand prepare(ChangeRequest request, PlanningRequest current, DevelopmentModels.Legacy actualCandidate);
    }
    private final CurrentPlanningFrame current;
    private final PlanningReadPort reads;
    private final GovernanceNativeReads contracts;
    private final ActionCoordinatorPort actions;
    private final Optional<QualifiedDevelopmentAction> developmentAction;
    public GovernancePublicService(CurrentPlanningFrame current, PlanningReadPort reads, GovernanceNativeReads contracts,
            ActionCoordinatorPort actions, Optional<QualifiedDevelopmentAction> developmentAction) {
        this.current = Objects.requireNonNull(current); this.reads = Objects.requireNonNull(reads); this.contracts = Objects.requireNonNull(contracts);
        this.actions = Objects.requireNonNull(actions); this.developmentAction = Objects.requireNonNull(developmentAction);
    }
    public CouncilReply query_council_composition_candidates_v1(CouncilRequest input) {
        PlanningRequest request = Objects.requireNonNull(current.current());
        var contract = contracts.council(); var readRequest = request(request, contract.operation());
        StrictJson.require(GovernanceNativeReads.frame(readRequest).equals(input.requested()), "public council request does not match current planning frame");
        var result = reads.read(contract, readRequest);
        if (result instanceof PlanningReadResult.Known<CouncilModels.Candidates> known) return new CouncilReply(known.value(), known);
        throw new IllegalStateException(((PlanningReadResult.Unavailable<CouncilModels.Candidates>) result).reason());
    }
    public DevelopmentReply query_steward_develop_county_candidates_v1(DevelopmentRequest input) {
        PlanningRequest request = Objects.requireNonNull(current.current());
        StrictJson.require(request.before().frame().revision().equals(input.expectedRevision()), "public development revision mismatch");
        return development(request);
    }
    public ActionReceipt change_steward_develop_county_task_v1(ChangeRequest input) {
        PlanningRequest request = Objects.requireNonNull(current.current());
        StrictJson.require(request.before().frame().revision().equals(input.expectedRevision()), "development action source revision is stale");
        DevelopmentReply observed = development(request);
        if (!(observed.value() instanceof DevelopmentModels.Legacy candidate))
            throw new UnsupportedOperationException("current native material has no legacy action-legality evidence; source-qualified .4 development executor is unavailable");
        StrictJson.require(candidate.stewardId() == input.councillorId()
                && candidate.candidates().stream().anyMatch(row -> row.countyTitleId() == input.countyTitleId()),
                "development action lacks the same-frame native-legal legacy candidate");
        QualifiedDevelopmentAction factory = developmentAction.orElseThrow(() -> new UnsupportedOperationException("the connected native driver has no qualified development action executor"));
        ActionCommand command = Objects.requireNonNull(factory.prepare(input, request, candidate));
        StrictJson.require(command.before().equals(request.before()) && command.source().equals(request.source())
                && command.sessionId().equals(request.sessionId()) && command.operation().value().equals("change-steward-develop-county-task-v1"),
                "development preparation crossed the original frame or exact action operation");
        var fields = command.arguments();
        StrictJson.require(fields.members().keySet().equals(Set.of("councillor_character_id", "task_key", "target_county_title_id", "replace_existing_task"))
                && new OpportunityJson.IntegerValue(BigInteger.valueOf(input.councillorId())).equals(fields.get("councillor_character_id"))
                && new OpportunityJson.IntegerValue(BigInteger.valueOf(input.countyTitleId())).equals(fields.get("target_county_title_id"))
                && new OpportunityJson.Text("task_develop_county").equals(fields.get("task_key"))
                && new OpportunityJson.Bool(input.replaceExisting()).equals(fields.get("replace_existing_task")),
                "qualified action encoder changed the public development request");
        // ACK and independent postcondition semantics remain entirely inside the sole action coordinator.
        return actions.execute(command);
    }
    private DevelopmentReply development(PlanningRequest request) {
        var result = reads.read(contracts.development(), request(request, contracts.development().operation()));
        if (result instanceof PlanningReadResult.Known<DevelopmentModels.Observation> known) {
            var backend = request.observations().snapshot().get("backend_id");
            StrictJson.require(backend == null || backend == OpportunityJson.Nil.INSTANCE || backend instanceof OpportunityJson.Text, "native snapshot backend identity is malformed");
            Optional<String> sourceBackend = backend instanceof OpportunityJson.Text text ? Optional.of(text.value()) : Optional.empty();
            return new DevelopmentReply(known.value(), known, sourceBackend);
        }
        throw new IllegalStateException(((PlanningReadResult.Unavailable<DevelopmentModels.Observation>) result).reason());
    }
    private static PlanningReadRequest request(PlanningRequest request, org.xar.ck3.control.application.action.OperationKey operation) {
        return new PlanningReadRequest(request.before(), request.source(), request.sessionId(), operation,
                new OpportunityJson.Obj(java.util.Map.of()), request.deadline());
    }
    public static CouncilRequest decodeCouncil(RawJson raw) {
        ObjectNode value = CouncilCodec.object(StrictJson.parse(raw.bytes()));
        exactOptional(value, Set.of("expected_snapshot_id", "public_revision", "native_revision", "date_raw", "owner_character_id"), "position_key");
        if (value.has("position_key")) StrictJson.require(CouncilCodec.text(value, "position_key").equals("councillor_steward"), "public Council19 supports only the Steward");
        return new CouncilRequest(new CouncilModels.Frame(CouncilCodec.text(value, "expected_snapshot_id"), GovernancePublicWire.unsigned64(value.get("public_revision"), true),
                GovernancePublicWire.unsigned64(value.get("native_revision"), true), (int) CouncilCodec.number(value, "date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE), CouncilCodec.id(value.get("owner_character_id"))));
    }
    public static DevelopmentRequest decodeDevelopment(RawJson raw) {
        ObjectNode value = StrictJson.object(StrictJson.parse(raw.bytes()), Set.of("expected_revision"));
        return new DevelopmentRequest(GovernancePublicWire.unsigned64(value.get("expected_revision"), false));
    }
    public static RawJson encodeCouncilRequest(CouncilRequest input) {
        var frame=Objects.requireNonNull(input).requested();
        var value=StrictJson.object().put("expected_snapshot_id",frame.snapshotId()).put("public_revision",frame.publicRevision().toString())
                .put("native_revision",frame.nativeRevision().toString()).put("date_raw",frame.dateRaw()).put("owner_character_id",frame.ownerId()).put("position_key","councillor_steward");
        return new RawJson(StrictJson.canonical(value));
    }
    public static RawJson encodeDevelopmentRequest(DevelopmentRequest input) {
        return new RawJson(StrictJson.canonical(StrictJson.object().put("expected_revision",Objects.requireNonNull(input).expectedRevision().toString())));
    }
    public static ChangeRequest decodeChange(RawJson raw) {
        ObjectNode value = CouncilCodec.object(StrictJson.parse(raw.bytes()));
        exactOptional(value, Set.of("councillor_character_id", "target_county_title_id", "expected_revision", "replace_existing_task"), "task_key");
        if (value.has("task_key")) StrictJson.require(CouncilCodec.text(value, "task_key").equals("task_develop_county"), "arbitrary task not accepted");
        return new ChangeRequest((int) CouncilCodec.number(value, "councillor_character_id", 1, Integer.MAX_VALUE),
                (int) CouncilCodec.number(value, "target_county_title_id", 1, Integer.MAX_VALUE), GovernancePublicWire.unsigned64(value.get("expected_revision"), true), CouncilCodec.bool(value.get("replace_existing_task")));
    }
    public static RawJson encodeChangeRequest(ChangeRequest input) {
        Objects.requireNonNull(input);var value=StrictJson.object().put("councillor_character_id",input.councillorId()).put("target_county_title_id",input.countyTitleId())
                .put("expected_revision",input.expectedRevision().toString()).put("replace_existing_task",input.replaceExisting()).put("task_key","task_develop_county");
        return new RawJson(StrictJson.canonical(value));
    }
    private static void exactOptional(ObjectNode value, Set<String> required, String optional) {
        Set<String> fields = new HashSet<>(); value.properties().forEach(entry->fields.add(entry.getKey()));
        StrictJson.require(fields.containsAll(required), "missing public governance request fields");
        fields.removeAll(required); StrictJson.require(Set.of(optional).containsAll(fields), "unknown public governance request field");
    }
    public static RawJson encodeCouncil(CouncilReply reply) {
        ObjectNode result = publicBody(reply.original(), "council_composition_candidates", reply.value().original().bytes());
        var frame = reply.value().frame();
        result.put("council_composition_candidates_ready", true).put("schema_version", 1)
                .put("schema", "xar.ck3.council-composition-candidates/v1").put("scope", "exact-council-composition-candidates");
        result.set("request", StrictJson.object().put("expected_snapshot_id", frame.snapshotId()).put("public_revision", frame.publicRevision())
                .put("native_revision", frame.nativeRevision()).put("date_raw", frame.dateRaw()).put("owner_character_id", frame.ownerId()).put("position_key", "councillor_steward"));
        return GovernancePublicWire.council(result);
    }
    public static RawJson encodeDevelopment(DevelopmentReply reply) {
        ObjectNode result = publicBody(reply.original(), "steward_develop_county_candidates", reply.value().original().bytes());
        var frame = reply.original().receipt().request().before().frame(); var identity = frame.identity();
        result.put("steward_develop_county_candidates_ready", !(reply.value() instanceof DevelopmentModels.Unavailable))
                .put("schema_version", 1).put("scope", "exact-steward-develop-county-candidates");
        result.set("build", StrictJson.object().put("version", reply.value().provenance().gameVersion()).put("exe_sha256", reply.value().provenance().executableSha256()));
        ObjectNode source = StrictJson.object().put("snapshot_id", frame.snapshotId()).put("revision", frame.revision())
                .put("native_revision", identity.nativeRevision()).put("date_raw", identity.dateRaw()).put("paused", true);
        if (reply.sourceBackendId().isPresent()) source.put("backend_id", reply.sourceBackendId().orElseThrow()); else source.putNull("backend_id");
        result.set("source", source);
        result.set("binding", StrictJson.object().put("snapshot_id", frame.snapshotId()).put("revision", frame.revision())
                .put("native_revision", identity.nativeRevision()).put("date_raw", identity.dateRaw()).put("expected_revision", frame.revision()));
        return GovernancePublicWire.development(result);
    }
    /** Original generic execute_step result; no dedicated MCP scope/build/source/binding wrapper. */
    public static RawJson encodeCouncilExecution(CouncilReply actual) {
        Objects.requireNonNull(actual);
        var receipt=actual.original().receipt();
        var nativeResult=GovernanceNativeReads.envelope(receipt,GovernanceNativeReads.COUNCIL_STEP,"council_composition_candidates");
        var nativePayload=CouncilCodec.object(nativeResult.get("council_composition_candidates"));
        var build=CouncilCodec.object(nativePayload.get("exact_build"));
        var replayed=CouncilCodec.decodeNative(StrictJson.canonical(nativePayload),GovernanceNativeReads.frame(receipt.request()),
                CouncilModels.Position.STEWARD,receipt.request().source().exactBuild(),CouncilCodec.text(build,"executable_sha256"));
        StrictJson.require(replayed.equals(actual.value()),"execute Council result differs from its actual original decoder");
        ObjectNode result=publicBody(actual.original(),"council_composition_candidates",actual.value().original().bytes());
        result.put("council_composition_candidates_ready",true);
        return GovernancePublicWire.councilExecution(result);
    }
    /** Original driver returns the complete normalized readiness value, including its field domain. */
    public static RawJson encodeDevelopmentExecution(DevelopmentReply actual) {
        Objects.requireNonNull(actual);
        var receipt=actual.original().receipt();
        var nativeResult=GovernanceNativeReads.envelope(receipt,GovernanceNativeReads.DEVELOPMENT_STEP,"steward_develop_county_candidates");
        var identity=receipt.request().before().frame().identity();
        var replayed=org.xar.ck3.control.governance.development.DevelopmentCodec.decode(StrictJson.canonical(nativeResult.get("steward_develop_county_candidates")),
                new DevelopmentModels.Frame(identity.nativeRevision(),identity.dateRaw().intValueExact()));
        StrictJson.require(replayed.equals(actual.value())&&replayed.provenance().gameVersion().equals(receipt.request().source().exactBuild()),
                "execute development result differs from its actual original decoder/source build");
        ObjectNode result=publicBody(actual.original(),"steward_develop_county_candidates",actual.value().original().bytes());
        var payload=CouncilCodec.object(result.get("steward_develop_county_candidates"));
        StrictJson.require(payload.has("readiness"),"validated development readiness missing");
        result.set("steward_develop_county_candidates_ready",payload.get("readiness"));
        return GovernancePublicWire.developmentExecution(result);
    }
    private static <T> ObjectNode publicBody(PlanningReadResult.Known<T> actual, String field, byte[] payload) {
        ObjectNode result = CouncilCodec.object(StrictJson.parse(actual.receipt().original().originalResultToken().orElseThrow().bytes())).deepCopy();
        result.set(field, StrictJson.parse(payload)); var before = actual.receipt().request().before().frame();
        result.put("queried_snapshot_id", before.snapshotId()).put("queried_revision", before.revision()).put("queried_native_revision", before.identity().nativeRevision());
        return result;
    }
}
