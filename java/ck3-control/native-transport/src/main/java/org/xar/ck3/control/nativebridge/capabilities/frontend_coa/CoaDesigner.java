package org.xar.ck3.control.nativebridge.capabilities.frontend_coa;

import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.BiFunction;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaPostconditions.*;

/** Three fixed semantic mutations and two actual reads; no clipboard, framebuffer or gameplay route. */
public final class CoaDesigner implements ActionPorts.PreparationPort, NativeEffectRegistry.Observer {
    public static final String SCHEMA = "xar.java.coa-designer-independent-ui-effect/v1";
    private static final String BASIS = "xar.java.coa-designer-original-basis/v1";
    /** The exact two new R1 read contracts are built once before Core and shared with framebuffer consumers. */
    public record ReadDefinitions(ReadContract<Tree> tree,ReadContract<Tree> grid) {
        public ReadDefinitions {
            Objects.requireNonNull(tree);Objects.requireNonNull(grid);
            require(tree.operation().value().equals("inspect-frontend-coat-of-arms-tree-v1")
                    &&grid.operation().value().equals("inspect-frontend-coat-of-arms-pattern-grid-v1")
                    &&tree.guardMode()==ReadContract.GuardMode.FRONTEND_SESSION&&grid.guardMode()==ReadContract.GuardMode.FRONTEND_SESSION,
                    "exact original CoA Menu tree/grid definitions required");
        }
    }
    public static ReadDefinitions readDefinitions(ExactRef actualOriginalDriverSource) {
        Objects.requireNonNull(actualOriginalDriverSource);
        return new ReadDefinitions(readContract(false,actualOriginalDriverSource),readContract(true,actualOriginalDriverSource));
    }
    private static ReadContract<Tree> readContract(boolean grid, ExactRef source) {
        String step = grid ? "inspect-frontend-coat-of-arms-pattern-grid-v1" : "inspect-frontend-coat-of-arms-tree-v1";
        return new ReadContract<>("coa." + step, new OperationKey(step), Optional.of("game.command." + step), step,
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP, ReadContract.GuardMode.FRONTEND_SESSION,
                source, request -> { require(request.arguments().members().isEmpty(), "CoA tree inspector accepts no arguments"); return CoaCodec.primitive(step); },
                receipt -> CoaCodec.tree(receipt.original().originalResultToken().orElseThrow(() -> new IllegalArgumentException("original native tree result missing")), grid));
    }
    public record Definitions(ReadContract<FrontendRulesData.ObservedRoute> route,
            ReadContract<FrontendRulesData.GuiTree> rulerTree, ReadContract<Tree> tree, ReadContract<Tree> grid) {
        public Definitions(ReadContract<FrontendRulesData.ObservedRoute> route,ReadContract<FrontendRulesData.GuiTree> rulerTree,ReadDefinitions own) {
            this(route,rulerTree,own.tree(),own.grid());
        }
        public Definitions {
            Objects.requireNonNull(route); Objects.requireNonNull(rulerTree); Objects.requireNonNull(tree); Objects.requireNonNull(grid);
            require(route.operation().value().equals("query-frontend-gui-route-v1")
                    && rulerTree.operation().value().equals("inspect-frontend-gui-tree-v1")
                    && tree.operation().value().equals("inspect-frontend-coat-of-arms-tree-v1")
                    && grid.operation().value().equals("inspect-frontend-coat-of-arms-pattern-grid-v1"), "exact original designer read definitions required");
            for (ReadContract<?> value : List.of(route, rulerTree, tree, grid))
                require(value.guardMode() == ReadContract.GuardMode.FRONTEND_SESSION
                        && value.wireProfile() == ReadContract.WireProfile.EXECUTE_STEP, "designer is an actual frontend Menu read profile");
        }
    }
    public record Preconditions(ExactRef route, ExactRef tree) {
        public Preconditions { Objects.requireNonNull(route); Objects.requireNonNull(tree); }
    }
    private final Definitions definitions;
    private final PlanningReadPort reads;
    private final ActionPorts.OutcomeArchive archive;
    private final BiFunction<DesignerVerified,RawJson,RawJson> formatter;
    public CoaDesigner(Definitions actualDefinitions, PlanningReadPort actualReads, ActionPorts.OutcomeArchive actualArchive,
            BiFunction<DesignerVerified,RawJson,RawJson> originalPublicFormatter) {
        definitions=Objects.requireNonNull(actualDefinitions); reads=Objects.requireNonNull(actualReads);
        archive=Objects.requireNonNull(actualArchive); formatter=Objects.requireNonNull(originalPublicFormatter);
    }
    public Definitions definitions() { return definitions; }
    public static DesignerAction action(OperationKey operation) {
        return List.of(DesignerAction.values()).stream().filter(value -> value.step().equals(operation.value())).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("operation is not one of the three original CoA designer actions"));
    }
    public List<NativeEffectRegistry.Binding> bindings(ExactRef actualImplementation) {
        return List.of(DesignerAction.values()).stream().map(value -> new NativeEffectRegistry.Binding(
                new OperationKey(value.step()), actualImplementation, this, this)).toList();
    }
    public List<NativeRecordedEvidenceVerifier.Binding> archivedVerifiers(ExactRef actualImplementation) {
        return List.of(DesignerAction.values()).stream().map(value -> new NativeRecordedEvidenceVerifier.Binding(
                new OperationKey(value.step()), actualImplementation, (head,receipt,bound) -> replay(receipt,bound))).toList();
    }
    public static OpportunityJson.Obj arguments(Preconditions actual) {
        var row=StrictJson.object(); row.set("before_route",actual.route().toJson()); row.set("before_tree",actual.tree().toJson());
        return OpportunityJson.object(OpportunityJson.parse(org.xar.ck3.control.contracts.FullJsonTree.encode(row,65536)),"designer preconditions");
    }
    public static Preconditions arguments(OpportunityJson.Obj actual) {
        var row=StrictJson.object(OpportunityJson.toNode(actual),Set.of("before_route","before_tree"));
        return new Preconditions(ExactRef.fromJson(row.get("before_route")),ExactRef.fromJson(row.get("before_tree")));
    }
    public FrontendExpectedPostcondition expected(FrontendIdentity actual, org.xar.ck3.control.g2.common.G2Source source, DesignerAction action) {
        require(actual.frame() instanceof FrontendFrame.Menu,"designer action needs the actual zero revision Menu profile");
        return new FrontendExpectedPostcondition(actual,source,SCHEMA,values(action));
    }
    private static List<ExpectedValue> values(DesignerAction action) {
        return action==DesignerAction.CUSTOM_MODE
                ? List.of(new ExpectedText(new FieldKey("route"),action.afterRoute().wire()),new ExpectedBoolean(new FieldKey("background_patterns_ready"),true))
                : List.of(new ExpectedText(new FieldKey("route"),action.afterRoute().wire()));
    }
    /** Receipts are issued by the actual read coordinator. This method creates only the full canonical command. */
    public ActionCommand command(String actionId, DesignerAction action, PlanningReadResult.Known<FrontendRulesData.ObservedRoute> route,
            PlanningReadResult.Known<?> tree, Instant deadline) {
        var origin=tree.receipt().after().binding().origin().requireFrontend();
        var source=route.receipt().request().source();
        var command=new ActionCommand(actionId,new CommandOrigin.Frontend(origin),source,origin.frontendSessionId(),new OperationKey(action.step()),
                arguments(new Preconditions(route.originalReceipt(),tree.originalReceipt())),
                new CommandExpectation.Frontend(expected(origin,source,action)),new Claims(Set.of(),Set.of(),Set.of(),Set.of()),deadline);
        requirePreconditions(command,action,archive); return command;
    }
    @Override public NativeRequest prepare(ActionCommand command) {
        var action=action(command.operation()); requireMenu(command); requireExpected(command,action); requirePreconditions(command,action,archive);
        return CoaCodec.primitive(action.step());
    }
    private void requirePreconditions(ActionCommand command, DesignerAction action, ActionPorts.OutcomeArchive same) {
        var refs=arguments(command.arguments()); var before=original(command,refs.route(),definitions.route(),same);
        PlanningReadReceipt tree=checkedRead(command,refs.tree(),action==DesignerAction.CUSTOM_MODE?definitions.tree():definitions.rulerTree(),same);
        Tree parsed=action==DesignerAction.CUSTOM_MODE?definitions.tree().decode(tree):CoaCodec.rulerDesignerTree(token(tree));
        designerReady(action,before,parsed);
    }
    private static void requireMenu(ActionCommand command) {
        require(command.origin() instanceof CommandOrigin.Frontend && command.origin().requireFrontend().frame() instanceof FrontendFrame.Menu,
                "designer accepts only its source-qualified actual Menu origin");
    }
    private void requireExpected(ActionCommand command,DesignerAction action) {
        require(command.expectation() instanceof CommandExpectation.Frontend value
                &&value.expected().equals(expected(command.origin().requireFrontend(),command.source(),action)),
                "designer command changed its exact original UI postcondition");
    }
    private PlanningReadReceipt checkedRead(ActionCommand command,ExactRef ref,ReadContract<?> contract,ActionPorts.OutcomeArchive same) {
        var receipt=same.loadRead(ref); require(ref.equals(same.readReferenceOf(receipt)),"original designer read reference changed");
        NativeRecordedEvidenceVerifier.requireRead(receipt,same); requireBinding(command,receipt,contract);
        require(receipt.after().binding().origin().requireFrontend().frame().querySequence().compareTo(command.origin().requireFrontend().frame().querySequence())<=0,
                "designer precondition cites a future frontend read");
        contract.decode(receipt); return receipt;
    }
    private <T> T original(ActionCommand command,ExactRef ref,ReadContract<T> contract,ActionPorts.OutcomeArchive same) {
        return contract.decode(checkedRead(command,ref,contract,same));
    }
    private static void requireBinding(ActionCommand command,PlanningReadReceipt read,ReadContract<?> contract) {
        require(read.contractId().equals(contract.contractId()) && read.request().operation().equals(contract.operation())
                && read.request().source().equals(command.source()) && read.request().sessionId().equals(command.sessionId())
                && read.request().origin() instanceof CommandOrigin.Frontend && read.after().binding().origin() instanceof CommandOrigin.Frontend
                && command.origin().requireFrontend().sameSession(read.request().origin().requireFrontend())
                && command.origin().requireFrontend().sameSession(read.after().binding().origin().requireFrontend())
                && read.after().binding().origin().requireFrontend().frame() instanceof FrontendFrame.Menu
                && read.original().nativeOk(),"designer read crossed exact contract/source/session/Menu origin");
    }
    private static RawJson token(PlanningReadReceipt read) {
        return read.original().originalResultToken().orElseThrow(() -> new IllegalArgumentException("original designer query token missing"));
    }
    private <T> PlanningReadResult.Known<T> query(ReadContract<T> contract,ActionCommand command,ActionState.Attempt attempt) {
        var request=new PlanningReadRequest(attempt.guard().origin(),command.source(),command.sessionId(),contract.operation(),
                new OpportunityJson.Obj(java.util.Map.of()),ActionObservationWindow.deadline(command));
        var result=reads.read(contract,request);
        if(result instanceof PlanningReadResult.Known<T> known)return known;
        throw new IllegalStateException("independent original designer read unavailable: "+((PlanningReadResult.Unavailable<T>)result).reason());
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
        var action=action(command.operation()); requireMenu(command);
        if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk())
            return NativeEffectRegistry.Projected.pending("designer submit unresolved; retain original action without replay",List.of(attempt.guard().nativeEvidence()));
        PlanningReadResult.Known<FrontendRulesData.ObservedRoute> after;
        Optional<PlanningReadReceipt> tree;
        try {
            after=query(definitions.route(),command,attempt);
            tree=action==DesignerAction.CUSTOM_MODE?Optional.of(query(definitions.tree(),command,attempt).receipt()):Optional.empty();
        } catch(IllegalStateException unavailable) {
            return NativeEffectRegistry.Projected.pending("designer ACK lacks its independent native post-read",List.of(attempt.guard().nativeEvidence()));
        }
        var raw=project(command,attempt,ack,after.receipt(),tree,archive,List.of());
        var compatible=raw.compatibleResult().orElseThrow(); var output=archive.preserveMaterial(compatible);
        var row=StrictJson.object(); row.put("schema",BASIS);row.put("body_sha256",ActionCodec.bodySha256(command));row.put("request_id",attempt.requestId());
        row.set("after_route",archive.preserveRead(after.receipt()).toJson());
        if(tree.isPresent())row.set("after_tree",archive.preserveRead(tree.orElseThrow()).toJson());else row.putNull("after_tree");
        row.set("public_result",output.toJson());
        var basis=new RawJson(org.xar.ck3.control.contracts.FullJsonTree.encode(row,65536));var basisRef=archive.preserveMaterial(basis);
        require(basis.equals(archive.loadMaterial(basisRef))&&compatible.equals(archive.loadMaterial(output)),"designer original proof archive changed");
        return project(command,attempt,ack,after.receipt(),tree,archive,List.of(basisRef));
    }
    private NativeEffectRegistry.Projected project(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,
            PlanningReadReceipt after,Optional<PlanningReadReceipt> afterTree,ActionPorts.OutcomeArchive same,List<ExactRef> support) {
        var action=action(command.operation()); requireMenu(command);requireExpected(command,action);requirePreconditions(command,action,same);
        require(ack.nativeOk()&&ack.requestId().equals(attempt.requestId())&&attempt.preparedRequest().equals(CoaCodec.primitive(action.step())),
                "designer effect changed its original successful ACK or exact empty-field native preparation");
        require(afterTree.isPresent()==(action==DesignerAction.CUSTOM_MODE),"designer after-tree branch differs from the exact original operation");
        requireBinding(command,after,definitions.route());NativeRecordedEvidenceVerifier.requireRead(after,same);
        require(!after.requestId().equals(attempt.requestId()) && !after.after().binding().observedAt().isBefore(attempt.submittedAt())
                && after.after().binding().origin().requireFrontend().frame().querySequence().compareTo(attempt.guard().origin().requireFrontend().frame().querySequence())>0,
                "designer effect needs a distinct later original native read");
        var pre=arguments(command.arguments());var before=checkedRead(command,pre.route(),definitions.route(),same);
        var beforeTree=checkedRead(command,pre.tree(),action==DesignerAction.CUSTOM_MODE?definitions.tree():definitions.rulerTree(),same);
        Tree parsed=action==DesignerAction.CUSTOM_MODE?definitions.tree().decode(beforeTree):CoaCodec.rulerDesignerTree(token(beforeTree));
        Optional<ReadEvidence<Tree>> treeProof=afterTree.map(read->{
            requireBinding(command,read,definitions.tree());NativeRecordedEvidenceVerifier.requireRead(read,same);
            require(read.after().binding().origin().requireFrontend().frame().querySequence().compareTo(attempt.guard().origin().requireFrontend().frame().querySequence())>0,
                    "custom mode needs its distinct later original tree observation");
            return evidence(definitions.tree().decode(read),read,same);
        });
        var verified=designer(action,evidence(definitions.route().decode(before),before,same),evidence(parsed,beforeTree,same),
                CoaCodec.activationAck(ack.originalResultToken().orElseThrow(),action.step()),attempt.requestId(),attempt.submittedAt(),
                evidence(definitions.route().decode(after),after,same),treeProof);
        var identity=after.after().binding().origin().requireFrontend();
        var observed=new FrontendEffectObservation(identity,command.source(),command.sessionId(),SCHEMA,values(action),after.requestId(),
                after.after().binding().observedAt(),identity.nativeEvidence(),support);
        if(!support.isEmpty())ActionEffects.validate(command,attempt,ack,new ActionState.FrontendApplied(observed));
        return new NativeEffectRegistry.Projected(new ActionPorts.FrontendObserved(observed),Optional.of(Objects.requireNonNull(formatter.apply(verified,ack.originalResultToken().orElseThrow()))));
    }
    private static <T> ReadEvidence<T> evidence(T value,PlanningReadReceipt read,ActionPorts.OutcomeArchive same) {
        return new ReadEvidence<>(value,read.requestId(),read.after().binding().observedAt(),same.readReferenceOf(read));
    }
    private void replay(ActionReceipt receipt,ActionPorts.OutcomeArchive same) {
        require(receipt.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.FrontendApplied,
                "designer replay needs its original primitive frontend settlement");
        var settled=(ActionState.Settled)receipt.state();var observed=((ActionState.FrontendApplied)settled.settlement()).observation();
        require(observed.supportingEvidence().size()==1,"designer settlement lacks original basis");
        var row=StrictJson.object(org.xar.ck3.control.contracts.FullJsonTree.parse(same.loadMaterial(observed.supportingEvidence().getFirst()).bytes(),65536),
                Set.of("schema","body_sha256","request_id","after_route","after_tree","public_result"));
        require(BASIS.equals(StrictJson.text(row.get("schema")))&&receipt.bodySha256().equals(StrictJson.text(row.get("body_sha256")))
                &&settled.attempt().requestId().equals(StrictJson.text(row.get("request_id")))&&settled.dispatch() instanceof NativeActionPort.AckReceived,
                "designer original basis crossed command/request/ACK");
        var after=same.loadRead(ExactRef.fromJson(row.get("after_route")));
        var tree=row.get("after_tree").isNull()?Optional.<PlanningReadReceipt>empty():Optional.of(same.loadRead(ExactRef.fromJson(row.get("after_tree"))));
        var replayed=project(receipt.command(),settled.attempt(),(NativeActionPort.AckReceived)settled.dispatch(),after,tree,same,observed.supportingEvidence());
        require(replayed.result() instanceof ActionPorts.FrontendObserved result&&observed.equals(result.observation())
                &&replayed.compatibleResult().equals(Optional.of(same.loadMaterial(ExactRef.fromJson(row.get("public_result"))))),
                "designer original replay differs from proposed effect or public result");
    }
    /** Return only the independently settled original public material, including after a cold archive read. */
    public RawJson publicResult(ActionReceipt original,ActionPorts.OutcomeArchive same) {
        replay(original,same);
        var state=(ActionState.Settled)original.state();var observed=((ActionState.FrontendApplied)state.settlement()).observation();
        var row=StrictJson.object(org.xar.ck3.control.contracts.FullJsonTree.parse(same.loadMaterial(observed.supportingEvidence().getFirst()).bytes(),65536),
                Set.of("schema","body_sha256","request_id","after_route","after_tree","public_result"));
        return same.loadMaterial(ExactRef.fromJson(row.get("public_result")));
    }
}
