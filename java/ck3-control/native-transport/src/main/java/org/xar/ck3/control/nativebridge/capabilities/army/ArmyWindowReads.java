package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import java.time.Instant;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Both actual fixed-window queries use the sole planning-read coordinator and preserve the full original TOP. */
public final class ArmyWindowReads {
    public record Selection(ArmyCalls.Frame input, Context context, BigInteger connectionGeneration, BigInteger driverConnectionGeneration) {
        public Selection { Objects.requireNonNull(input); Objects.requireNonNull(context); UInt64.positive(connectionGeneration); new UInt64(driverConnectionGeneration); kind(input.method()); input.revision().requireCurrent(context.before().frame().revision()); }
    }
    public record ReconciliationSelection(ReconciliationIdentity identity,ArmyCalls.Frame input,Instant deadline,BigInteger driverConnectionGeneration) {
        public ReconciliationSelection { Objects.requireNonNull(identity);Objects.requireNonNull(input);Objects.requireNonNull(deadline);new UInt64(driverConnectionGeneration);kind(input.method());input.revision().requireCurrent(identity.factual().frame().revision()); }
        public Selection facts(){return new Selection(input,new Context(identity.factual(),identity.source(),identity.sessionId(),deadline),identity.connectionGeneration(),driverConnectionGeneration);}
    }
    private final EnumMap<ArmyWindowCodec.Kind,RootReadContractCatalog.Family<Selection,ArmyWindowCodec.Observation>> families = new EnumMap<>(ArmyWindowCodec.Kind.class);
    private final EnumMap<ArmyWindowCodec.Kind,RootReadContractCatalog.Family<ReconciliationSelection,ArmyWindowCodec.Observation>> reconciliation = new EnumMap<>(ArmyWindowCodec.Kind.class);
    private final PlanningReadPort reads;
    private final ArmyWindowAttempts.Store attempts;
    public ArmyWindowReads(ExactRef definition, ExactRef decoder, PlanningReadPort reads, ActionPorts.OutcomeArchive archive) {
        this.reads = Objects.requireNonNull(reads); this.attempts = new ArmyWindowAttempts.Store(archive);
        for (var kind : ArmyWindowCodec.Kind.values()) {
            var operation = new OperationKey(kind.step(ArmyWindowCodec.Operation.QUERY)); String capability = kind.capability(ArmyWindowCodec.Operation.QUERY);
            families.put(kind, new RootReadContractCatalog.Family<>("army-window-" + kind.name(), Selection.class, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    Optional.of(capability), definition, decoder, ArmyWindowReads::key, s -> operation, s -> {
                        require(kind(s.input().method()) == kind, "window family differs from selected public query");
                        var installed = new java.util.concurrent.atomic.AtomicReference<ReadContract<ArmyWindowCodec.Observation>>();
                        var contract = new ReadContract<ArmyWindowCodec.Observation>("army-window-" + kind.name() + "-" + ArmyReadKey.digest(key(s)), operation, Optional.of(capability), capability,
                                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, definition,
                                (request,requestId) -> { verify(request,s); var original = new NativeRequest(operation.value(), Optional.of(capability), new RawJson(new byte[]{'{','}'})); attempts.prepared(Objects.requireNonNull(installed.get()),kind,s.context(),s.connectionGeneration(),request,requestId,original); return original; },
                                receipt -> {var value=decode(s,receipt);attempts.observed(Objects.requireNonNull(installed.get()),receipt);return value;},receipt -> decode(s,receipt),
                                (original,value,current,semantic) -> ArmyNativeReadEvidence.requireCanonicalEquivalent(original,current));
                        installed.set(contract); return contract;
                    }));
            reconciliation.put(kind,new RootReadContractCatalog.Family<>("army-window-reconciliation-"+kind.name(),ReconciliationSelection.class,
                    ReadContract.GuardMode.RECONCILIATION_OBSERVATION,Optional.of(capability),definition,decoder,ArmyWindowReads::reconciliationKey,s->operation,s->{
                require(kind(s.input().method())==kind,"reconciliation window family changed its exact query");
                return new ReadContract<>("army-window-reconciliation-"+kind.name()+"-"+ArmyReadKey.digest(reconciliationKey(s)),operation,Optional.of(capability),capability,
                        ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.RECONCILIATION_OBSERVATION,definition,
                        (request,id)->{verifyReconciliation(s,request);return new NativeRequest(operation.value(),Optional.of(capability),new RawJson(new byte[]{'{','}'}));},
                        receipt->decodeReconciliation(s.facts(),s.identity(),receipt),receipt->decodeReconciliation(s.facts(),s.identity(),receipt),
                        (original,value,current,semantic)->{verifyReconciliation(s,current);require(original.request().origin().equals(current.origin())&&original.request().arguments().equals(current.arguments()),"window reconciliation reused another original pending selection");});
            }));
        }
    }
    public List<RootReadContractCatalog.Family<?,?>> families() { return java.util.stream.Stream.concat(families.values().stream(),reconciliation.values().stream()).<RootReadContractCatalog.Family<?,?>>map(f -> f).toList(); }
    public ArmyWindowAttempts.Source attempts() { return attempts; }
    public ReadContract<ArmyWindowCodec.Observation> issue(RootReadContractCatalog catalog, Selection s) { return catalog.issue(families.get(kind(s.input().method())), s); }
    public ReadContract<ArmyWindowCodec.Observation> issueReconciliation(RootReadContractCatalog catalog,ReconciliationSelection selected){return catalog.issue(reconciliation.get(kind(selected.input().method())),selected);}
    /** Pure descriptor check. The Root still verifies registered object identity, sources and the private observation lease. */
    public static void requireReconciliationContract(ReadContract<?> contract,ReconciliationSelection selected) {
        Objects.requireNonNull(contract);Objects.requireNonNull(selected);var kind=kind(selected.input().method());
        var operation=new OperationKey(kind.step(ArmyWindowCodec.Operation.QUERY));var capability=kind.capability(ArmyWindowCodec.Operation.QUERY);
        require(contract.contractId().equals("army-window-reconciliation-"+kind.name()+"-"+ArmyReadKey.digest(reconciliationKey(selected)))
                &&contract.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION&&contract.operation().equals(operation)
                &&contract.requiredCapability().equals(Optional.of(capability))&&contract.permissionKey().equals(capability)
                &&contract.permissionMode()==ReadContract.PermissionMode.ADVERTISED_CAPABILITY&&contract.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP,
                "window reconciliation descriptor differs from the original pending selection");
    }
    public PlanningReadRequest requestReconciliation(ReconciliationSelection selected){return PlanningReadRequest.newReconciliation(selected.identity(),new OperationKey(kind(selected.input().method()).step(ArmyWindowCodec.Operation.QUERY)),arguments(selected.input()),selected.deadline());}
    public PlanningReadRequest request(Selection s) { var c = s.context(); return new PlanningReadRequest(c.before(),c.source(),c.sessionId(),new OperationKey(kind(s.input().method()).step(ArmyWindowCodec.Operation.QUERY)),arguments(s.input()),c.deadline()); }
    public record Capture(PlanningReadRequest request, PlanningReadResult<ArmyWindowCodec.Observation> result) {
        public Capture { Objects.requireNonNull(request); Objects.requireNonNull(result); }
    }
    /** Retains the exact issued request on failure; a negative native TOP never becomes a Known observation. */
    public Capture capture(ContinuityStorePort.Session session, RootReadContractCatalog catalog, Selection selected) {
        PlanningReadRequest actualRequest = request(selected);
        return new Capture(actualRequest,reads.read(session,issue(catalog,selected),actualRequest));
    }
    public PlanningReadResult.Known<ArmyWindowCodec.Observation> read(ContinuityStorePort.Session session, RootReadContractCatalog catalog, Selection s) {
        var result = capture(session,catalog,s).result(); if (result instanceof PlanningReadResult.Known<ArmyWindowCodec.Observation> known) return known;
        throw ArmyWindowQueryFailure.from(kind(s.input().method()),(PlanningReadResult.Unavailable<ArmyWindowCodec.Observation>)result);
    }
    public static ArmyWindowCodec.Observation decode(Selection s, PlanningReadReceipt receipt) {
        verify(receipt.request(),s); var current=ArmyNativeReadEvidence.contextForRequest(s.context(),receipt.request()); ArmyNativeReadEvidence.verifyContext(current,receipt);
        return decodePayload(s,receipt,current);
    }
    /** A distinct installed reconciliation contract may reuse this strict decoder; the ordinary family never accepts that origin. */
    public static ArmyWindowCodec.Observation decodeReconciliation(Selection selected,ReconciliationIdentity identity,PlanningReadReceipt receipt) {
        var current=ArmyReconciliationReadEvidence.context(identity,receipt.request());
        require(selected.context().before().equals(identity.factual())&&selected.context().source().equals(identity.source())&&selected.context().sessionId().equals(identity.sessionId())
                &&selected.connectionGeneration().equals(identity.connectionGeneration())&&receipt.request().arguments().equals(arguments(selected.input()))
                &&receipt.request().operation().value().equals(kind(selected.input().method()).step(ArmyWindowCodec.Operation.QUERY)),"window reconciliation crossed its actual typed subject/factual context");
        ArmyReconciliationReadEvidence.verifyContext(identity,receipt);return decodePayload(selected,receipt,current);
    }
    private static ArmyWindowCodec.Observation decodePayload(Selection s,PlanningReadReceipt receipt,Context current) {
        require(receipt.original().nativeOk() && receipt.original().originalResultToken().isPresent(), "window query lacks actual successful Native outer/token");
        var original = ArmyJson.parse(receipt.original().originalFrame().bytes()); require(ArmyJson.parse(receipt.original().originalResultToken().orElseThrow().bytes()).equals(original.get("result")), "window token differs from full original TOP result");
        return ArmyWindowCodec.decode(kind(s.input().method()),ArmyWindowCodec.Operation.QUERY,receipt.original().originalFrame().bytes(),receipt.requestId(),current,s.connectionGeneration(),s.driverConnectionGeneration());
    }
    /** Pure extraction from the same already validated/held Complete; no Native command or observation. */
    public static BigInteger driverGeneration(Complete actual) {
        return ArmyWindowCodec.driverGeneration(actual);
    }
    public static ArmyWindowCodec.Kind kind(PublicMethod method) { return switch(method) { case QUERY_WAR_DECLARED_OVERVIEW_V1 -> ArmyWindowCodec.Kind.OVERVIEW; case QUERY_WAR_RESULTS_WINDOW_V1 -> ArmyWindowCodec.Kind.RESULTS; default -> throw new IllegalArgumentException("not a fixed-window query"); }; }
    public static Obj arguments(ArmyCalls.Frame input) { kind(Objects.requireNonNull(input).method()); return OpportunityJson.object(OpportunityJson.parse(ArmyCallCodec.encode(input).bytes()),"Army fixed-window arguments"); }
    private static RawJson reconciliationKey(ReconciliationSelection selected){var n=ArmyJson.empty();n.set("identity",ReconciliationIdentityCodec.encode(selected.identity()));n.set("public_arguments",OpportunityJson.toNode(arguments(selected.input())));n.put("driver_connection_generation",selected.driverConnectionGeneration().toString());return new RawJson(ArmyJson.bytes(n));}
    private static void verifyReconciliation(ReconciliationSelection selected,PlanningReadRequest request){ArmyReconciliationReadEvidence.context(selected.identity(),request);require(request.arguments().equals(arguments(selected.input()))&&request.operation().value().equals(kind(selected.input().method()).step(ArmyWindowCodec.Operation.QUERY)),"window reconciliation request changed its typed query");}
    private static RawJson key(Selection s) { var n = ArmyJson.parse(ArmyReadKey.key(s.input(),s.context()).bytes()); n.put("connection_generation",s.connectionGeneration().toString());n.put("driver_connection_generation",s.driverConnectionGeneration().toString()); return new RawJson(ArmyJson.bytes(n)); }
    private static void verify(PlanningReadRequest r, Selection s) { var c = s.context(); require(r.before().equals(c.before()) && r.source().equals(c.source()) && r.sessionId().equals(c.sessionId()) && r.arguments().equals(arguments(s.input())) && r.operation().value().equals(kind(s.input().method()).step(ArmyWindowCodec.Operation.QUERY)), "fixed-window query crossed its full source or typed arguments"); }
}
