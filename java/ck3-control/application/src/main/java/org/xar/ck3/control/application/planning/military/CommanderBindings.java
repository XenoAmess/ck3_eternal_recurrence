package org.xar.ck3.control.application.planning.military;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.commander.CommanderQuality;

/** Actual dynamic catalog families; the same issued object is used for preparation, observation and recovery. */
public final class CommanderBindings {
    public record Sources(ExactRef query,ExactRef queryDecoder,ExactRef assignment,ExactRef assignmentDecoder,ExactRef archivedVerifier,ExactRef reconciliationQuery) {
        public Sources {for(ExactRef ref:java.util.List.of(query,queryDecoder,assignment,assignmentDecoder,archivedVerifier,reconciliationQuery))StrictJson.require(ref.bytes()>0,"exact commander source required");}
    }
    public record Selection(CommanderObservationCollector.ObservedInput request,int army,Optional<Integer> targetProvince) {
        public Selection(CommanderObservationCollector.ObservedInput request,int army){this(request,army,Optional.empty());}
        public Selection {Objects.requireNonNull(request);Objects.requireNonNull(targetProvince);StrictJson.require(army>=0,"public Army ID must be nonnegative");targetProvince.ifPresent(value->StrictJson.require(value>0,"target Province must remain positive"));}
    }
    private final Sources sources;
    private final PlanningReadPort reads;
    private final RootReadContractCatalog.Family<Selection,CommanderObservationCollector.Observation> readFamily;
    private final RootReadContractCatalog.Family<Selection,CommanderObservationCollector.Observation> targetReadFamily;
    private final RootReadContractCatalog.Family<CommanderReconciliationCollector.Selection,CommanderObservationCollector.Observation> reconciliationFamily;
    private final RootExecutableBindings.Family<CommanderAssignmentPostcondition.Arguments> actionFamily;
    public CommanderBindings(Sources sources,PlanningReadPort actualReads,CommanderAssignmentPostcondition actualObserver,
            NativeEffectEvidence.FrameLoader actualFrameLoader) {
        this(sources,actualReads,actualObserver,actualFrameLoader,(guard,archive)->{throw new java.io.IOException("commander reconciliation archive authority is not installed");});
    }
    public CommanderBindings(Sources sources,PlanningReadPort actualReads,CommanderAssignmentPostcondition actualObserver,
            NativeEffectEvidence.FrameLoader actualFrameLoader,CommanderArchivedVerifier.ReconciliationFrames actualReconciliationFrames) {
        this.sources=Objects.requireNonNull(sources);reads=Objects.requireNonNull(actualReads);Objects.requireNonNull(actualObserver);Objects.requireNonNull(actualFrameLoader);
        readFamily=family(false);targetReadFamily=family(true);
        reconciliationFamily=new RootReadContractCatalog.Family<>("commander-reconciliation-observation",CommanderReconciliationCollector.Selection.class,
                ReadContract.GuardMode.RECONCILIATION_OBSERVATION,Optional.of(CommanderQuality.QUERY_CAPABILITY),sources.reconciliationQuery(),sources.queryDecoder(),
                CommanderReconciliationCollector::key,selected->CommanderReconciliationCollector.operation(selected.army()),
                selected->CommanderReconciliationCollector.contract(selected,sources.reconciliationQuery()));
        actionFamily=new RootExecutableBindings.Family<>("ordinary-commander-native-assignment",CommanderAssignmentPostcondition.Arguments.class,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(CommanderQuality.ASSIGN_CAPABILITY),sources.assignment(),sources.assignmentDecoder(),sources.archivedVerifier(),
                CommanderBindings::identity,a->new OperationKey(a.step()),a->{
                    OperationKey operation=new OperationKey(a.step());
                    var effect=NativeEffectRegistry.Binding.existing(operation,sources.assignment(),CommanderAssignmentPostcondition::prepare,actualObserver);
                    return new RootExecutableBindings.IssuedAction(new RootExecutableBindings.ActionBinding(effect,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                            Optional.of(CommanderQuality.ASSIGN_CAPABILITY),sources.assignmentDecoder()),CommanderArchivedVerifier.binding(operation,sources.archivedVerifier(),actualFrameLoader,actualReconciliationFrames));
                });
    }
    public RootReadContractCatalog.Family<Selection,CommanderObservationCollector.Observation> readFamily(){return readFamily;}
    public java.util.List<RootReadContractCatalog.Family<?,?>> readFamilies(){return java.util.List.of(readFamily,targetReadFamily,reconciliationFamily);}
    public CommanderReconciliationCollector.Issued reconciliation(CommanderReconciliationCollector.Input input,int army,java.time.Instant actualDeadline,RootReadContractCatalog catalog) {
        var selected=new CommanderReconciliationCollector.Selection(input,army);
        return new CommanderReconciliationCollector.Issued(catalog.issue(reconciliationFamily,selected),CommanderReconciliationCollector.request(selected,actualDeadline));
    }
    public PlanningReadResult<CommanderObservationCollector.Observation> readReconciliation(CommanderReconciliationCollector.Input input,int army,java.time.Instant actualDeadline,
            RootReadContractCatalog catalog,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same) {
        var issued=reconciliation(input,army,actualDeadline,catalog);return reads.read(same,issued.contract(),issued.request());
    }
    private RootReadContractCatalog.Family<Selection,CommanderObservationCollector.Observation> family(boolean targeted) {
        return new RootReadContractCatalog.Family<>(targeted?"ordinary-commander-target-query":"ordinary-commander-current-query",Selection.class,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(targeted?CommanderObservationCollector.TARGET_CAPABILITY:CommanderQuality.QUERY_CAPABILITY),sources.query(),sources.queryDecoder(),
                selection->{StrictJson.require(selection.targetProvince().isPresent()==targeted,"commander family target scope differs");return CommanderObservationCollector.key(selection.request(),selection.army(),selection.targetProvince());},
                selection->CommanderObservationCollector.operation(selection.army(),selection.targetProvince()),
                selection->CommanderObservationCollector.contract(selection.request(),selection.army(),selection.targetProvince(),sources.query()));
    }
    public RootExecutableBindings.Family<CommanderAssignmentPostcondition.Arguments> actionFamily(){return actionFamily;}
    public CommanderObservationCollector collector(PlanningRequest request,RootReadContractCatalog catalog) {
        return collector(CommanderObservationCollector.ObservedInput.of(request),catalog);
    }
    public CommanderObservationCollector collector(CommanderObservationCollector.ObservedInput request,RootReadContractCatalog catalog) {
        return collector(request,Optional.empty(),catalog);
    }
    public CommanderObservationCollector collector(CommanderObservationCollector.ObservedInput request,Optional<Integer> target,RootReadContractCatalog catalog) {
        Objects.requireNonNull(catalog);
        return new CommanderObservationCollector(request,target,sources.query(),(actual,army,actualTarget,source)->{
            StrictJson.require(source.equals(sources.query()),"commander collector changed installed source");
            return catalog.issue(actualTarget.isPresent()?targetReadFamily:readFamily,new Selection(actual,army,actualTarget));
        });
    }
    public PlanningReadResult<CommanderObservationCollector.Observation> read(PlanningRequest request,int army,
            RootReadContractCatalog catalog,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed) {
        return read(CommanderObservationCollector.ObservedInput.of(request),army,catalog,borrowed);
    }
    public PlanningReadResult<CommanderObservationCollector.Observation> read(CommanderObservationCollector.ObservedInput request,int army,
            RootReadContractCatalog catalog,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed) {
        return read(request,army,Optional.empty(),catalog,borrowed);
    }
    public PlanningReadResult<CommanderObservationCollector.Observation> read(PlanningRequest request,int army,Optional<Integer> target,
            RootReadContractCatalog catalog,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed) {
        return read(CommanderObservationCollector.ObservedInput.of(request),army,target,catalog,borrowed);
    }
    public PlanningReadResult<CommanderObservationCollector.Observation> read(CommanderObservationCollector.ObservedInput request,int army,Optional<Integer> target,
            RootReadContractCatalog catalog,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed) {
        var collector=collector(request,target,catalog);
        PlanningReadPort sameSession=new PlanningReadPort(){
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest actual){return reads.read(borrowed,contract,actual);}
        };
        return collector.collect(sameSession,request,army);
    }
    public ActionCommand command(PlanningRequest request,MilitaryPlanningDecision.Select selection,
            RootExecutableBindings installed,MilitaryPlanningDecision.CommandFactory originalCommands) {
        var arguments=CommanderAssignmentPostcondition.arguments(selection.arguments());
        StrictJson.require(selection.operation().value().equals(arguments.step()),"commander selection operation differs");
        installed.issue(actionFamily,arguments);
        ActionCommand command=Objects.requireNonNull(originalCommands.create(request,selection));
        CommanderAssignmentPostcondition.prepare(command);return command;
    }
    /** Public Assign and the ordinary producer issue the identical installed family; the caller owns its actual action ID. */
    public ActionCommand assignment(PlanningRequest request,CommanderAssignmentPostcondition.Arguments input,
            RootExecutableBindings installed,String actualActionId) {
        var raw=OpportunityJson.object(OpportunityJson.parse(arguments(input).bytes()),"commander arguments");
        StrictJson.require(input.date().equals(request.before().frame().identity().dateRaw()),"commander arguments crossed current native date");
        installed.issue(actionFamily,input);
        ActionCommand command=new ActionCommand(actualActionId,request.before(),request.source(),request.sessionId(),new OperationKey(input.step()),raw,
                CommanderAssignmentPostcondition.expected(request,raw),CommanderAssignmentPostcondition.claims(raw),request.deadline());
        CommanderAssignmentPostcondition.prepare(command);return command;
    }
    private static RawJson arguments(CommanderAssignmentPostcondition.Arguments a) {
        var n=org.xar.ck3.control.contracts.StrictJson.object().put("army_id",a.army()).put("commander_character_id",a.character())
                .put("native_carmy_id",a.nativeArmy()).put("owner_character_id",a.owner()).put("date_raw",a.date());
        return new RawJson(StrictJson.canonical(n));
    }
    private static RawJson identity(CommanderAssignmentPostcondition.Arguments a) {
        // The installed handler is context-generic; date/native owner remain in each independently guarded command body.
        return new RawJson(StrictJson.canonical(StrictJson.object().put("army_id",a.army()).put("commander_character_id",a.character())));
    }
}
