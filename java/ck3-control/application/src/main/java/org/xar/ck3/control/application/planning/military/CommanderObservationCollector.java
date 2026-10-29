package org.xar.ck3.control.application.planning.military;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.time.Instant;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.commander.CommanderQuality;
import org.xar.ck3.control.wave2.military.commander.CommanderQualityCodec;
import org.xar.ck3.control.wave2.military.commander.ArmyCommanderCandidatesCodec;

/** The original synchronous collector, restricted to exact registered per-Army reads. */
public final class CommanderObservationCollector {
    public record ObservedInput(ObservationIdentity before,G2Source source,String sessionId,Instant deadline,
            OpportunityJson.Obj snapshot,Set<String> capabilities) {
        public ObservedInput {Objects.requireNonNull(before);Objects.requireNonNull(source);StrictJson.text(sessionId);Objects.requireNonNull(deadline);Objects.requireNonNull(snapshot);capabilities=Set.copyOf(capabilities);}
        public static ObservedInput of(PlanningRequest request){return new ObservedInput(request.before(),request.source(),request.sessionId(),request.deadline(),request.observations().snapshot(),request.observations().bridgeCapabilities());}
    }
    public static final String TARGET_CAPABILITY="game.command.query-army-commander-candidates-v1-for-army-N-at-province-P";
    @FunctionalInterface public interface ContractIssuer {ReadContract<Observation> issue(ObservedInput request,int army,Optional<Integer> target,ExactRef source);}
    public record Observation(ArmyCommanderCandidatesCodec.ObservedQuery observed, OpportunityJson.Obj proposalInput) {
        public Observation { Objects.requireNonNull(observed); Objects.requireNonNull(proposalInput); }
        public CommanderQuality.Proposal proposal(){return observed.proposal();}
    }
    private final ObservedInput bound;
    private final Optional<Integer> target;
    private final Map<Integer, ReadContract<Observation>> contracts;

    public CommanderObservationCollector(PlanningRequest request, ExactRef definitionSource) {
        this(request,definitionSource,CommanderObservationCollector::contract);
    }
    public CommanderObservationCollector(PlanningRequest request,ExactRef definitionSource,ContractIssuer installedIssuer) {
        this(ObservedInput.of(request),definitionSource,installedIssuer);
    }
    public CommanderObservationCollector(ObservedInput request,ExactRef definitionSource,ContractIssuer installedIssuer) {
        this(request,Optional.empty(),definitionSource,installedIssuer);
    }
    public CommanderObservationCollector(ObservedInput request,Optional<Integer> target,ExactRef definitionSource,ContractIssuer installedIssuer) {
        bound = Objects.requireNonNull(request); Objects.requireNonNull(definitionSource);
        this.target=Objects.requireNonNull(target);target.ifPresent(value->StrictJson.require(value>0,"target Province must remain positive"));
        Objects.requireNonNull(installedIssuer);
        Map<Integer, ReadContract<Observation>> built = new LinkedHashMap<>();
        if (request.snapshot().get("player_armies") instanceof OpportunityJson.Arr armies) {
            for (OpportunityJson.Value value : armies.items()) {
                if (!(value instanceof OpportunityJson.Obj army)
                        || !new OpportunityJson.Bool(true).equals(army.get("controllable"))) continue;
                Integer id = publicId(army.get("army_id"));
                if (id != null) built.computeIfAbsent(id, ignored -> installedIssuer.issue(request, id,target, definitionSource));
            }
        }
        contracts = Map.copyOf(built);
    }
    /** The composition root installs these same instances before calling this collector. */
    public List<ReadContract<?>> registeredContracts() {
        List<ReadContract<?>> result = new ArrayList<>(); result.addAll(contracts.values()); return List.copyOf(result);
    }
    public PlanningReadResult<Observation> collect(PlanningReadPort port, PlanningRequest request, int armyId) {
        return collect(port,ObservedInput.of(request),armyId);
    }
    public PlanningReadResult<Observation> collect(PlanningReadPort port,ObservedInput request,int armyId) {
        Objects.requireNonNull(port);
        StrictJson.require(bound.equals(request), "commander collector belongs to a different actual request");
        ReadContract<Observation> contract = contracts.get(armyId);
        if (contract == null) return new PlanningReadResult.Unavailable<>(
                "commander query subject is outside the current controllable Army scope", Optional.empty());
        var arguments = arguments(armyId,target);
        var readRequest=new PlanningReadRequest(request.before(),request.source(),request.sessionId(),contract.operation(),arguments,request.deadline());
        var result = port.read(contract,readRequest);
        if (result instanceof PlanningReadResult.Known<Observation> known) {
            if(port instanceof OriginalMilitaryReadPort original) {
                try{return new PlanningReadResult.Known<>(original.replayOriginal(contract,readRequest,known),known.receipt(),known.originalReceipt());}
                catch(java.io.UncheckedIOException|IllegalArgumentException|IllegalStateException invalid){return new PlanningReadResult.Unavailable<>("actual original commander read cannot be reused: "+invalid.getMessage(),Optional.of(known.receipt().original()));}
            }
            return new PlanningReadResult.Known<>(contract.decode(known.receipt()),known.receipt(),known.originalReceipt());
        }
        return result;
    }
    static ReadContract<Observation> contract(ObservedInput request, int army,Optional<Integer> target, ExactRef source) {
        OperationKey operation = operation(army,target);String capability=target.isPresent()?TARGET_CAPABILITY:CommanderQuality.QUERY_CAPABILITY;
        return new ReadContract<>(contractId(request,army,target), operation, Optional.of(capability),
                "commander_candidates_current_army", ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, source, (read,id) -> {
                    StrictJson.require(read.before().equals(request.before()) && read.source().equals(request.source())
                            && read.sessionId().equals(request.sessionId()),
                            "registered commander read crossed its source request");
                    StrictJson.require(read.arguments().equals(arguments(army,target)),
                            "commander read arguments differ from registered subject");
                    return new NativeRequest(operation.value(), capability,
                            new RawJson(StrictJson.canonical(StrictJson.object())));
                }, receipt -> decode(request, army,target, operation, receipt),receipt -> decode(request,army,target,operation,receipt),
                (original,value,current,semantic)->{
                    StrictJson.require(original.request().before().equals(current.before())&&current.before().equals(request.before())
                            &&current.source().equals(request.source())&&current.sessionId().equals(request.sessionId())
                            &&current.operation().equals(operation)&&current.arguments().equals(arguments(army,target)),"commander canonical source/arguments differ");
                    StrictJson.require(NativeMilitaryInputView.sameNativeOperands(request.snapshot(),semantic),"commander native operands changed after original read");
                    StrictJson.require(value.equals(decode(request,army,target,operation,original)),"commander canonical value differs from original decoder");
                });
    }
    static Observation admit(PlanningRequest request, int army, PlanningReadReceipt receipt) {
        return admit(ObservedInput.of(request),army,receipt);
    }
    static Observation admit(ObservedInput request,int army,PlanningReadReceipt receipt) {
        return decode(request,army,Optional.empty(),operation(army,Optional.empty()),receipt);
    }
    private static Observation decode(PlanningRequest request, int army, OperationKey operation, PlanningReadReceipt receipt) {
        return decode(ObservedInput.of(request),army,Optional.empty(),operation,receipt);
    }
    private static Observation decode(ObservedInput request,int army,Optional<Integer> target,OperationKey operation,PlanningReadReceipt receipt) {
        StrictJson.require(receipt.request().before().equals(request.before())
                && receipt.request().source().equals(request.source())
                && receipt.request().sessionId().equals(request.sessionId())
                && receipt.request().operation().equals(operation)
                && receipt.contractId().equals(contractId(request,army,target))
                && receipt.request().arguments().equals(arguments(army,target)),
                "commander receipt is not this original read");
        var before = receipt.before().binding(); var after = receipt.after().binding();
        StrictJson.require(before.observed().equals(request.before()) && after.observed().equals(request.before())
                && before.source().equals(request.source()) && after.source().equals(request.source())
                && before.sessionId().equals(request.sessionId()) && after.sessionId().equals(request.sessionId())
                && before.connectionGeneration().equals(after.connectionGeneration())
                && before.operation().equals(operation) && after.operation().equals(operation)
                && receipt.before().paused() && receipt.after().paused()
                && receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),
                "commander read crossed the exact paused Game/session/frame/generation");
        StrictJson.require(receipt.original().nativeOk() && receipt.original().originalResultToken().isPresent(),
                "commander read has no successful original native result");
        OpportunityJson.Obj nativeResult = DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);
        return normalizeObserved(request.snapshot(),request.before(),army,nativeResult,request.capabilities(),target);
    }
    /** One complete native normalizer for ordinary and explicitly guarded reconciliation observations. */
    static Observation normalizeObserved(OpportunityJson.Obj snapshot,ObservationIdentity factual,int army,
            OpportunityJson.Obj nativeResult,Set<String> advertised,Optional<Integer> target) {
        List<OpportunityJson.Value> capabilities = advertised.stream()
                .sorted().<OpportunityJson.Value>map(OpportunityJson.Text::new).toList();
        OpportunityJson.Obj input = empty().with("schema", new OpportunityJson.Text("xar.java.commander-quality-observed-query.v1"))
                .with("army_id", number(BigInteger.valueOf(army)))
                .with("expected_revision", number(factual.frame().revision()))
                .with("snapshot_before", snapshot)
                .with("snapshot_after", frame(factual, OpportunityJson.bool(snapshot.get("paused"),"paused")))
                .with("bridge_capabilities", new OpportunityJson.Arr(capabilities)).with("native_result", nativeResult);
        // Encode the original token domain directly: a decimal 1.0 must never become an integer 1.
        var observed=target.isPresent()?CommanderQualityCodec.admitObservedTargetObservation(DriverJson.encode(input),target.orElseThrow()):CommanderQualityCodec.admitObservedObservation(DriverJson.encode(input));
        var normalized=DriverJson.object(org.xar.ck3.control.wave2.military.commander.ArmyCommanderCandidatesCodec.encodeJson(observed.normalizedJson()),DriverJson.MAX_NATIVE_BYTES);
        OpportunityJson.Obj proposalInput = empty().with("schema", new OpportunityJson.Text(CommanderQualityCodec.INPUT_SCHEMA))
                .with("snapshot", snapshot)
                .with("query_sequence", nativeResult.get("query_sequence"))
                .with("candidates", normalized);
        return new Observation(observed, proposalInput);
    }
    static RawJson key(ObservedInput request,int army) {
        return key(request,army,Optional.empty());
    }
    static RawJson key(ObservedInput request,int army,Optional<Integer> target) {
        OpportunityJson.Obj value=empty().with("army_id",number(BigInteger.valueOf(army)))
                .with("target_province_id",target.<OpportunityJson.Value>map(valueTarget->number(BigInteger.valueOf(valueTarget))).orElse(OpportunityJson.Nil.INSTANCE))
                .with("observation_identity",new OpportunityJson.Text(request.before().toString()))
                .with("source",new OpportunityJson.Text(request.source().toString()))
                .with("session",new OpportunityJson.Text(request.sessionId()))
                .with("snapshot_sha256",new OpportunityJson.Text(DriverJson.sha256(DriverJson.encode(request.snapshot()))));
        return new RawJson(DriverJson.encode(value));
    }
    private static String contractId(ObservedInput request,int army,Optional<Integer> target){return "commander-candidates-v1-army-"+army+"-"+DriverJson.sha256(key(request,army,target).bytes());}
    static OperationKey operation(int army,Optional<Integer> target){return new OperationKey("query-army-commander-candidates-v1-for-army-"+army+target.map(value->"-at-province-"+value).orElse(""));}
    private static OpportunityJson.Obj arguments(int army,Optional<Integer> target){var value=empty().with("army_id",number(BigInteger.valueOf(army)));return target.isPresent()?value.with("target_province_id",number(BigInteger.valueOf(target.orElseThrow()))):value;}
    private static OpportunityJson.Obj frame(ObservationIdentity identity, boolean paused) {
        var frame = identity.frame();
        return empty().with("paused", new OpportunityJson.Bool(paused)).with("snapshot_id", new OpportunityJson.Text(frame.snapshotId()))
                .with("revision", number(frame.revision())).with("native_revision", number(frame.identity().nativeRevision()))
                .with("date_raw", number(frame.identity().dateRaw()));
    }
    private static OpportunityJson.IntegerValue number(BigInteger value) { return new OpportunityJson.IntegerValue(value); }
    private static OpportunityJson.Obj empty() { return new OpportunityJson.Obj(Map.of()); }
    private static Integer publicId(OpportunityJson.Value value) {
        if (!(value instanceof OpportunityJson.IntegerValue integer) || integer.value().signum() < 0
                || integer.value().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) > 0) return null;
        return integer.value().intValueExact();
    }
}
