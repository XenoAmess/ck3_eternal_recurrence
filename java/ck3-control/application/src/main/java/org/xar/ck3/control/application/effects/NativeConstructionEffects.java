package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Migrated start material check from query_construction_receipt. No cold recovery or income is inferred. */
public final class NativeConstructionEffects implements NativeEffectRegistry.Observer {
    public static final String SCHEMA = "xar.construction-material-receipt.v1";
    public static final OperationKey QUERY = new OperationKey("g2_player_construction_view_probe_v1");
    public record Tuple(long baronyTitleId, long provinceId, long buildingTypeId, long slotIndex) {
        public Tuple { StrictJson.require(baronyTitleId > 0 && provinceId > 0 && buildingTypeId > 0 && slotIndex >= 0
                && baronyTitleId <= Integer.MAX_VALUE && provinceId <= Integer.MAX_VALUE && buildingTypeId <= Integer.MAX_VALUE && slotIndex <= Integer.MAX_VALUE,
                "canonical full construction tuple required"); }
        static Tuple decode(JsonNode value) { var row = EffectJson.object(value); return new Tuple(EffectJson.id(row.get("barony_title_id")),
                EffectJson.id(row.get("province_id")), EffectJson.id(row.get("building_type_id")), EffectJson.nonnegative(row.get("slot_index"))); }
        void write(ObjectNode row) { row.put("barony_title_id", baronyTitleId); row.put("province_id", provinceId); row.put("building_type_id", buildingTypeId); row.put("slot_index", slotIndex); }
    }
    public record Candidate(Tuple tuple, BigInteger goldBefore, BigInteger cost, BigInteger preProofEpoch) {
        public Candidate { Objects.requireNonNull(tuple); StrictJson.require(goldBefore != null && goldBefore.signum() >= 0 && cost != null && cost.signum() > 0
                && goldBefore.compareTo(cost) >= 0 && goldBefore.compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0
                && cost.compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0 && preProofEpoch != null && preProofEpoch.signum() > 0 && preProofEpoch.compareTo(StrictJson.UINT64_MAX) <= 0, "actual quoted construction resources/proof required"); }
        public static Candidate decode(OpportunityJson.Obj value) {
            ObjectNode row = EffectJson.object(value), candidate = EffectJson.object(row.get("candidate"));
            return new Candidate(Tuple.decode(candidate), EffectJson.integer(candidate.get("gold_before_raw")),
                    EffectJson.integer(candidate.get("stock_gold_cost_raw")), EffectJson.integer(row.get("pre_proof_epoch")));
        }
    }
    public record Active(Tuple tuple, long initiator, boolean active) { }
    public record World(BigInteger proofEpoch, BigInteger nativeRevision, BigInteger dateRaw, long actorId, BigInteger gold,
            List<Active> active, List<Tuple> completed, boolean completedObserved) {
        public World { Objects.requireNonNull(proofEpoch); Objects.requireNonNull(nativeRevision); Objects.requireNonNull(dateRaw); Objects.requireNonNull(gold);
            active = List.copyOf(active); completed = List.copyOf(completed); StrictJson.require(proofEpoch.signum() > 0 && proofEpoch.compareTo(StrictJson.UINT64_MAX) <= 0
                    && nativeRevision.signum() > 0 && nativeRevision.compareTo(StrictJson.UINT64_MAX) <= 0 && gold.signum() >= 0
                    && gold.compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0 && actorId > 0
                    && (completedObserved || completed.isEmpty()), "actual material world required"); }
    }
    public enum Material { ACTIVE, COMPLETED, UNOBSERVED }
    private final NativeEffectSnapshots snapshots; private final PlanningReadPort reads; private final ReadContract<?> contract;
    public NativeConstructionEffects(NativeEffectSnapshots snapshots, PlanningReadPort reads, ReadContract<?> contract) {
        this.snapshots = Objects.requireNonNull(snapshots); this.reads = Objects.requireNonNull(reads); this.contract = Objects.requireNonNull(contract);
        StrictJson.require(contract.operation().equals(QUERY), "construction observer requires the actual registered Native query");
    }
    public static ReadContract<World> readContract(ExactRef actualDefinitionSource) {
        return new ReadContract<>("construction.material-world.v1", QUERY, Optional.empty(), QUERY.value(), ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                ReadContract.WireProfile.EXECUTE_STEP, actualDefinitionSource,
                request -> new NativeRequest(QUERY.value(), Optional.empty(), new RawJson(new byte[]{'{','}'})), NativeConstructionEffects::decodeWorld);
    }
    public static ExpectedPostcondition expected(ObservationIdentity before, G2Source source, OpportunityJson.Obj arguments) {
        Candidate candidate = Candidate.decode(arguments);
        return new ExpectedPostcondition(1, before, source, SCHEMA, values(candidate, before.frame().identity().player().longValueExact()));
    }
    private static List<ExpectedValue> values(Candidate candidate, long actor) {
        return List.of(new ExpectedInteger(new FieldKey("barony_title_id"), BigInteger.valueOf(candidate.tuple().baronyTitleId())),
                new ExpectedInteger(new FieldKey("province_id"), BigInteger.valueOf(candidate.tuple().provinceId())),
                new ExpectedInteger(new FieldKey("building_type_id"), BigInteger.valueOf(candidate.tuple().buildingTypeId())),
                new ExpectedInteger(new FieldKey("slot_index"), BigInteger.valueOf(candidate.tuple().slotIndex())),
                new ExpectedInteger(new FieldKey("actor_id"), BigInteger.valueOf(actor)), new ExpectedText(new FieldKey("status"), "applied"));
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        Candidate candidate = Candidate.decode(command.arguments()); var pair = snapshots.read(command, attempt); Complete after = pair.after();
        var requested = new PlanningReadRequest(after.identity(), after.source(), after.sessionId(), QUERY,
                (OpportunityJson.Obj) OpportunityJson.parse(new byte[]{'{','}'}), command.deadline());
        PlanningReadResult<?> read = reads.read(contract, requested);
        if (!(read instanceof PlanningReadResult.Known<?> known)) return NativeEffectRegistry.Projected.pending("construction Native material read unavailable; original submit remains unresolved", List.of(after.originalEvidence()));
        var projected = project(command, attempt, pair, known.receipt(), decodeWorld(known.receipt()));
        if (!(projected.result() instanceof ActionPorts.EffectObserved)) return projected;
        return NativeEffectSnapshots.withEvidence(projected, List.of(snapshots.evidence(command, attempt, pair, List.of(known.receipt()), projected.compatibleResult().orElseThrow())));
    }
    private static NativeEffectRegistry.Projected project(ActionCommand command, ActionState.Attempt attempt,
            NativeEffectSnapshots.Pair pair, PlanningReadReceipt read, World world) {
        Candidate candidate = Candidate.decode(command.arguments()); Complete after = pair.after();
        NativeEffectSnapshots.requireAfterRead(command, attempt, after, read, QUERY);
        long actor = command.before().frame().identity().player().longValueExact();
        Material material = verify(candidate, actor, command.before().frame().identity().dateRaw(), after.identity().frame().identity().nativeRevision(), after.identity().frame().identity().dateRaw(), world);
        if (material == Material.UNOBSERVED) return NativeEffectRegistry.Projected.pending("requested exact construction tuple not independently observed", List.of(after.originalEvidence()));
        ObjectNode result = StrictJson.object(); result.put("status", "applied"); result.put("postcondition_verified", true);
        result.put("completion_status", material == Material.COMPLETED ? "completed" : "in_progress");
        result.put("action_request_id", attempt.requestId()); result.put("episode_run_id", after.identity().frame().episodeRunId());
        result.put("actor_character_id", actor); result.put("post_player_gold_raw", world.gold()); result.put("post_proof_epoch", world.proofEpoch());
        result.put("post_native_revision", world.nativeRevision()); result.put("post_date_raw", world.dateRaw());
        candidate.tuple().write(result.putObject("candidate")); result.put("native_query_request_id", read.requestId());
        return NativeEffectSnapshots.observed(command, attempt, after, SCHEMA, values(candidate, actor), read.requestId(), EffectJson.raw(result), List.of());
    }
    public static NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation, ExactRef source,
            NativeEffectEvidence.FrameLoader frames, ReadContract<?> actualReadContract) {
        StrictJson.require(operation.value().equals("g2_player_world_building_action_private_v1") && actualReadContract.operation().equals(QUERY), "exact construction producer and query required");
        Objects.requireNonNull(frames);
        return new NativeRecordedEvidenceVerifier.Binding(operation, source, (head, receipt, archive) -> {
            var original = NativeEffectEvidence.load(receipt, archive, frames); var settled = (ActionState.Settled) receipt.state();
            StrictJson.require(original.independentReads().size() == 1, "construction effect requires exactly its original independent material read");
            var read = original.independentReads().getFirst();
            StrictJson.require(actualReadContract.contractId().equals(read.contractId()), "construction archived material contract differs from the single Root read registration");
            actualReadContract.decode(read);
            var replayed = project(receipt.command(), settled.attempt(), original.frames(), read, decodeWorld(read));
            replayed = NativeEffectSnapshots.withEvidence(replayed, ((ActionState.Applied) settled.settlement()).observation().supportingEvidence());
            NativeEffectEvidence.requireSame(settled.settlement(), replayed, original.compatibleResult());
        });
    }
    public static Material verify(Candidate candidate, long actor, BigInteger actionDate, BigInteger afterNativeRevision, BigInteger afterDate, World world) {
        StrictJson.require(afterDate.compareTo(actionDate) >= 0 && world.actorId() == actor && world.nativeRevision().equals(afterNativeRevision) && world.dateRaw().equals(afterDate)
                && world.proofEpoch().compareTo(candidate.preProofEpoch()) > 0, "construction query crossed actor/frame/proof epoch");
        long active = world.active().stream().filter(row -> row.active() && row.initiator() == actor && row.tuple().equals(candidate.tuple())).count();
        long complete = world.completed().stream().filter(candidate.tuple()::equals).count();
        StrictJson.require(active <= 1 && complete <= 1 && !(active > 0 && complete > 0), "construction material duplicate/active-completed conflict");
        if (active == 0 && complete == 0) return Material.UNOBSERVED;
        if (active > 0 && afterDate.equals(actionDate)) StrictJson.require(world.gold().equals(candidate.goldBefore().subtract(candidate.cost())), "same-date exact construction wallet debit not observed");
        return active > 0 ? Material.ACTIVE : Material.COMPLETED;
    }
    private static World decodeWorld(PlanningReadReceipt receipt) {
        ObjectNode result = EffectJson.object(EffectJson.parse(receipt.original().originalResultToken().orElseThrow(() -> new IllegalArgumentException("Native query result token missing"))));
        StrictJson.require(StrictJson.text(result.get("step")).equals(QUERY.value()), "construction read step drift"); StrictJson.trueValue(result.get("accepted"));
        ObjectNode probe = EffectJson.object(result.get("private_probe")); StrictJson.require(!EffectJson.bool(probe.get("advertised")), "private query advertised flag drift");
        ObjectNode world = EffectJson.object(probe.get("player_world_building_sources"));
        StrictJson.require(StrictJson.text(world.get("status")).equals("source_available"), "construction source unavailable");
        var frame = receipt.request().before().frame().identity();
        StrictJson.require(EffectJson.integer(probe.get("snapshot_revision")).equals(frame.nativeRevision()) && EffectJson.integer(probe.get("date_raw")).equals(frame.dateRaw()), "construction probe frame drift");
        StrictJson.trueValue(world.get("native_final_legality_evaluated")); EffectJson.bool(world.get("native_cost_evaluated"));
        for (JsonNode sample : EffectJson.rows(world.get("legal_samples"))) {
            StrictJson.trueValue(sample.get("native_cost_observed")); JsonNode costs = sample.get("cost_raw_native");
            StrictJson.require(costs != null && costs.isArray() && costs.size() == 10, "complete original ten-resource cost observations required"); for (JsonNode cost : costs) EffectJson.integer(cost);
        }
        boolean completedObserved = EffectJson.bool(world.get("completed_buildings_observed"));
        StrictJson.require(completedObserved || world.has("completed_buildings") && world.get("completed_buildings").isNull(), "unobserved completed inventory must be explicit null");
        List<Active> active = new ArrayList<>(); for (JsonNode row : EffectJson.rows(world.get("active_constructions"))) {
            boolean enabled = EffectJson.bool(row.get("active"));
            if (enabled) active.add(new Active(Tuple.decode(row), EffectJson.id(row.get("initiator_character_id")), true));
        }
        List<Tuple> built = completedObserved ? EffectJson.rows(world.get("completed_buildings")).stream().map(Tuple::decode).toList() : List.of();
        World observed = new World(EffectJson.integer(probe.get("proof_epoch")), EffectJson.integer(world.get("snapshot_revision")), EffectJson.integer(world.get("date_raw")),
                EffectJson.id(world.get("player_character_id")), EffectJson.integer(world.get("player_gold_raw")), active, built, completedObserved);
        StrictJson.require(observed.nativeRevision().equals(frame.nativeRevision()) && observed.dateRaw().equals(frame.dateRaw()) && BigInteger.valueOf(observed.actorId()).equals(frame.player()), "material world frame drift");
        return observed;
    }
}
