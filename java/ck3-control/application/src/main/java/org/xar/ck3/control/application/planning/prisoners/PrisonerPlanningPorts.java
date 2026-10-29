package org.xar.ck3.control.application.planning.prisoners;

import java.math.BigInteger;
import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.Catalog;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.ReleaseOption;

/** Typed composition ports. Collection contracts come from the one native-family producer. */
public final class PrisonerPlanningPorts {
    private PrisonerPlanningPorts() { }
    public enum Family { RELEASE, RANSOM }
    public record Pending(Family family, OpportunityJson.Obj original, ExactRef source) {
        public Pending { Objects.requireNonNull(family); Objects.requireNonNull(original); Objects.requireNonNull(source);
            StrictJson.require(source.bytes() > 0, "actual pending evidence required"); }
    }
    public sealed interface LedgerView permits KnownLedger, LedgerUnavailable { }
    public record KnownLedger(ExactRef head, Optional<Pending> release, Optional<Pending> ransom) implements LedgerView {
        public KnownLedger { Objects.requireNonNull(head); Objects.requireNonNull(release); Objects.requireNonNull(ransom);
            StrictJson.require(head.bytes() > 0, "actual ledger head required");
            release.ifPresent(value -> StrictJson.require(value.family() == Family.RELEASE, "release family differs"));
            ransom.ifPresent(value -> StrictJson.require(value.family() == Family.RANSOM, "ransom family differs")); }
    }
    public record LedgerUnavailable(String reason) implements LedgerView { public LedgerUnavailable { StrictJson.text(reason); } }
    @FunctionalInterface public interface LedgerReadPort { LedgerView read(PlanningRequest request); }
    @FunctionalInterface public interface CommandBinding {
        Optional<ActionCommand> bind(PlanningRequest request, OperationKey operation,
                OpportunityJson.Obj arguments, Claims claims, OpportunityJson.Obj originalChoice);
    }
    /** Omitted intent is explicit Unconditional; null/empty authored options cannot become unconditional. */
    public record CollectionQuery(ReadContract<RawJson> contract, PrisonerOptionIntent.Arguments intent) {
        public CollectionQuery { Objects.requireNonNull(contract); Objects.requireNonNull(intent); }
        public List<ReleaseOption> options() { return intent.options() instanceof PrisonerOptionIntent.Negotiated value ? value.options() : List.of(); }
        public int mask() { return intent.options() instanceof PrisonerOptionIntent.Negotiated value ? value.mask() : 0; }
        public OpportunityJson.Obj arguments() { return object(PrisonerOptionIntent.encode(intent)); }
    }
    @FunctionalInterface public interface WarContracts { ReadContract<RawJson> get(long warId); }
    public sealed interface TurnBundleRead permits ObservedTurnBundle, TurnBundleUnavailable { }
    public record ObservedTurnBundle(org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before,
            org.xar.ck3.control.g2.common.G2Source source,String sessionId,RawJson value,
            PlanningReadReceipt rootReceipt,ExactRef originalRoot) implements TurnBundleRead {
        public ObservedTurnBundle { Objects.requireNonNull(before);Objects.requireNonNull(source);StrictJson.text(sessionId);
            Objects.requireNonNull(value);Objects.requireNonNull(rootReceipt);Objects.requireNonNull(originalRoot);
            StrictJson.require(originalRoot.bytes()>0&&rootReceipt.request().source().equals(source)
                    &&rootReceipt.request().sessionId().equals(sessionId)&&rootReceipt.request().before().game().equals(before.game()),
                    "aggregate must retain its actual ROOT original and target physical source/session"); }
    }
    public record TurnBundleUnavailable(String reason) implements TurnBundleRead {
        public TurnBundleUnavailable { StrictJson.text(reason); }
    }
    @FunctionalInterface public interface TurnBundlePort { TurnBundleRead read(PlanningRequest request)throws IOException; }
    /** Collections exist before Finance/Known; the genuine service aggregate binds once after their actual construction. */
    public static final class Queries {
        private final List<ReadContract<RawJson>> collections;
        private final WarContracts wars;
        private TurnBundlePort turnBundle;
        public Queries(List<ReadContract<RawJson>> collections,Map<Long,ReadContract<RawJson>> wars) {
            this(collections,fixedWars(wars));
        }
        public Queries(List<ReadContract<RawJson>> collections,WarContracts wars) {
            this.collections = List.copyOf(collections); this.wars=Objects.requireNonNull(wars);
            StrictJson.require(collections.size() == 64, "all 64 exact native-family collection contracts required");
            for (int ordinal = 0; ordinal < 64; ordinal++) StrictJson.require(
                    collections.get(ordinal).operation().value().equals(collectionStep(ordinal)), "collection ordinal registration differs");
        }
        public List<ReadContract<RawJson>> collections(){return collections;}
        public WarContracts wars(){return wars;}
        public synchronized void bindTurnBundle(TurnBundlePort actual) {
            Objects.requireNonNull(actual);StrictJson.require(turnBundle==null,"the actual turn bundle service binds exactly once");turnBundle=actual;
        }
        public synchronized void requireTurnBundleBound(){StrictJson.require(turnBundle!=null,"actual turn bundle service has not been bound");}
        public TurnBundleRead readTurnBundle(PlanningRequest request)throws IOException {
            TurnBundlePort actual;synchronized(this){requireTurnBundleBound();actual=turnBundle;}
            return Objects.requireNonNull(actual.read(Objects.requireNonNull(request)));
        }
        public CollectionQuery collection(int ordinal, PrisonerOptionIntent options) {
            return collection(ordinal, new PrisonerOptionIntent.Arguments(options, OptionalLong.empty()));
        }
        public CollectionQuery collection(int ordinal, PrisonerOptionIntent.Arguments intent) {
            StrictJson.require(ordinal >= 0 && ordinal < 64, "bounded ordinal required");
            return new CollectionQuery(collections.get(ordinal), intent);
        }
    }
    private static WarContracts fixedWars(Map<Long, ReadContract<RawJson>> source) {
        Map<Long, ReadContract<RawJson>> actual = Map.copyOf(source);
        actual.forEach((id, contract) -> StrictJson.require(contract.operation().value().equals(warStep(id)), "war query registration differs"));
        return actual::get;
    }
    /** Non-collection reads retain their registered exact source/permission/wire profile. */
    public static ReadContract<RawJson> privateQuery(String id, OperationKey operation, String permission,
            ExactRef source, ReadContract.WireProfile profile, OpportunityJson.Obj additionalFields) {
        StrictJson.require(!operation.value().startsWith(collectionStep(0)), "native-family is the sole collection-contract producer");
        RawJson fields = new RawJson(bytes(additionalFields));
        return new ReadContract<>(id, operation, Optional.empty(), permission,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, profile, source,
                request -> { StrictJson.require(request.arguments().equals(EMPTY), "fixed query arguments cannot override its source");
                    return new NativeRequest(operation.value(), Optional.empty(), fields); },
                receipt -> receipt.original().originalResultToken().orElseThrow(() -> new IllegalArgumentException("original native result token absent")));
    }
    public enum RecordOperation { RETAIN, RECONCILE }
    public record SuccessionRecord(RecordOperation operation, RawJson producerRequest, RawJson produced, List<ExactRef> sourceEvidence) {
        public SuccessionRecord { Objects.requireNonNull(operation); Objects.requireNonNull(producerRequest); Objects.requireNonNull(produced);
            sourceEvidence = List.copyOf(sourceEvidence); StrictJson.require(!sourceEvidence.isEmpty() && sourceEvidence.size() <= 64, "actual succession evidence required");
            sourceEvidence.forEach(reference -> StrictJson.require(reference.bytes() > 0, "nonempty source reference required")); }
    }
    public sealed interface RecordResult permits Recorded, RecordUnavailable { }
    public record Recorded(org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before,
            ExactRef persistedHead, RawJson observedProjection) implements RecordResult {
        public Recorded { Objects.requireNonNull(before); Objects.requireNonNull(persistedHead); Objects.requireNonNull(observedProjection);
            StrictJson.require(persistedHead.bytes() > 0, "actual persisted readback required"); }
    }
    public record RecordUnavailable(String reason) implements RecordResult { public RecordUnavailable { StrictJson.text(reason); } }
    @FunctionalInterface public interface SuccessionRecordPort { RecordResult record(PlanningRequest request, SuccessionRecord value); }
    public record Bindings(PlanningReadPort reads, Queries queries, Optional<Catalog> catalog,
            LedgerReadPort ledgers, CommandBinding commands, SuccessionRecordPort succession) {
        public Bindings { Objects.requireNonNull(reads); Objects.requireNonNull(queries); Objects.requireNonNull(catalog);
            Objects.requireNonNull(ledgers); Objects.requireNonNull(commands); Objects.requireNonNull(succession); }
    }
    public static String collectionStep(int ordinal) {
        StrictJson.require(ordinal >= 0 && ordinal < 64, "collection ordinal outside 0..63");
        return "query-player-prisoner-collection-private-v1" + (ordinal == 0 ? "" : "-ransom-ordinal-" + ordinal);
    }
    public static String warStep(long id) { StrictJson.require(id > 0 && id < 0xffffffffL, "valid full war ID required"); return "query-war-prisoner-release-pairs-v1-" + id; }
    public static Claims claims(long prisoner, long player) {
        StrictJson.require(prisoner > 0 && prisoner < 0xffffffffL && player > 0 && player < 0xffffffffL && prisoner != player, "valid actor-target IDs required");
        return new Claims(Set.of(), Set.of(), Set.of(BigInteger.valueOf(prisoner), BigInteger.valueOf(player)), Set.of("player-prisoner-custody"));
    }
    static OpportunityJson.Obj object(byte[] bytes) { return OpportunityJson.object(OpportunityJson.parse(bytes), "original object"); }
    static byte[] bytes(OpportunityJson.Obj value) { return OpportunityJson.encode(value); }
    static OrdinaryPolicy.Replace annotation(OrdinaryPolicy.Draft previous, String key, OpportunityJson.Value value, String reason) {
        return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft(previous.policy(), previous.phase(), previous.reason(), previous.kind(),
                previous.command(), previous.purpose(), previous.domain(), previous.detail().with(key, value)), reason);
    }
    static PlanningReadRequest request(PlanningRequest request, ReadContract<?> contract, OpportunityJson.Obj arguments) {
        return new PlanningReadRequest(request.before(), request.source(), request.sessionId(), contract.operation(), arguments, request.deadline());
    }
    static final OpportunityJson.Obj EMPTY = new OpportunityJson.Obj(Map.of());
}
