package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.military.combatwire.CombatRequest;
import org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Ordinary ReadCatalog executes the original typed families, without casting contracts or registering a second operation. */
public final class MilitaryNativeReadDispatcher implements WarCorePlanner.ReadCatalog {
    private static final Pattern PREVIEW=Pattern.compile("preview-move-army-(0|[1-9][0-9]*)-to-([1-9][0-9]*)");
    private static final Pattern HORIZON=Pattern.compile("query-route-contact-horizon-v1-(0|[1-9][0-9]*)-to-([1-9][0-9]*)-h-([1-9][0-9]*)(.*)");
    private final RootRuntimeContext runtime;private final ArmyPlanningReads routes;private final ArmyForecastReads forecasts;private final ArmyBattleReads battles;private final MilitaryCanonicalReads ordinaryReads;private final ArmyWarReads wars;
    public MilitaryNativeReadDispatcher(RootRuntimeContext actual,ArmyPlanningReads routes,ArmyForecastReads forecasts,ArmyBattleReads battles,MilitaryCanonicalReads ordinaryReads,ArmyWarReads sameWarReads) {
        runtime=Objects.requireNonNull(actual);this.routes=Objects.requireNonNull(routes);this.forecasts=Objects.requireNonNull(forecasts);this.battles=Objects.requireNonNull(battles);this.ordinaryReads=Objects.requireNonNull(ordinaryReads);wars=Objects.requireNonNull(sameWarReads);
    }
    @Override public PlanningReadResult<Obj> read(PlanningRequest request,MilitaryPlanningDecision.Select selected) {
        Objects.requireNonNull(request);Objects.requireNonNull(selected);
        try {
            runtime.requireCurrent(request.deadline());
            if(selected.purpose()!=OrdinaryPolicy.Purpose.READ_ONLY)return unavailable("military read dispatcher cannot execute a world action");
            if(!request.source().equals(runtime.source())||!request.before().game().equals(runtime.game().generation())||!request.sessionId().equals(runtime.game().sessionId()))return unavailable("military read belongs to a predecessor runtime");
            return runtime.withSession(session->{
                String step=selected.operation().value();var context=new Context(request.before(),request.source(),request.sessionId(),request.deadline());
                if(step.equals(FinanceReadContracts.Query.ROOT.operation().value())) {
                    org.xar.ck3.control.contracts.StrictJson.require(selected.arguments().members().isEmpty(),
                            "ordinary campaign-root selection requires its original empty public arguments");
                    var finance=runtime.finance();
                    org.xar.ck3.control.contracts.StrictJson.require(finance.game().equals(runtime.game().generation())
                            &&finance.sessionId().equals(request.sessionId())&&finance.source().equals(request.source()),
                            "ordinary campaign-root read crossed its identical installed finance owner");
                    return root(finance.definitions(),finance.readPort(),session,request);
                }
                var termination=termination(step,revision(request));
                if(termination.isPresent()) {
                    // Copy DATA from the actual held lease, then leave that frozen callback before Native query dispatch.
                    var frame=runtime.collector().current(session,request.before(),request.deadline(),lease->{
                        var actual=lease.frame();
                        org.xar.ck3.control.contracts.StrictJson.require(actual.identity().equals(request.before())&&actual.source().equals(request.source())
                                &&actual.sessionId().equals(request.sessionId())&&actual.semantic().equals(request.observations().snapshot()),
                                "war exit read planning input differs from the actual complete current frame");
                        return new ArmyRetreatFrames.Current(actual,request.deadline());
                    });
                    return termination(wars,ordinaryReads,session,runtime.readCatalog(),new ArmyWarReads.Selection(termination.orElseThrow(),frame,Optional.empty()));
                }
                var preview=PREVIEW.matcher(step);
                if(preview.matches())return route(session,new ArmyPlanningReads.Selection(request,MilitaryReadObservation.Kind.ROUTE_PREVIEW,Integer.parseInt(preview.group(1)),Integer.parseInt(preview.group(2)),List.of()));
                var horizon=HORIZON.matcher(step);
                if(horizon.matches()) {
                    String suffix=horizon.group(4);if(!suffix.matches("(?:-(?:0|[1-9][0-9]*))+"))return unavailable("noncanonical full-hostile H1 operation");
                    List<Integer> ids=java.util.Arrays.stream(suffix.substring(1).split("-")).map(Integer::parseInt).toList();
                    if(ids.size()!=Integer.parseInt(horizon.group(3)))return unavailable("H1 hostile count differs");
                    var input=new ArmyPlanningReads.Selection(request,MilitaryReadObservation.Kind.CONTACT_HORIZON,Integer.parseInt(horizon.group(1)),Integer.parseInt(horizon.group(2)),ids);
                    if(!input.step().equals(step))return unavailable("noncanonical H1 operation");return route(session,input);
                }
                Optional<CombatRequest> v2=CombatRequest.parseStep(step);Optional<CombatRequest> v3=CombatPhaseInputsCodec.parseStep(step);
                if(v2.isPresent()||v3.isPresent()) {
                    CombatRequest encounter=v2.orElseGet(v3::orElseThrow);Field<Integer> ctor=encounter.constructorAdjacencyKindRaw()==null?new Missing<>():new Present<>(encounter.constructorAdjacencyKindRaw());
                    var call=new ArmyCalls.Combat(v2.isPresent()?PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS:PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS_V3,revision(request),encounter,ctor);
                    return forecast(session,new ArmyForecastReads.Selection(call,context),request.observations().snapshot());
                }
                if(step.matches("query-war-entry-assessments-v1-1-[1-9][0-9]*"))return forecast(session,new ArmyForecastReads.Selection(new ArmyCalls.WarEntry(revision(request),List.of(new PositiveId(Integer.parseInt(step.substring("query-war-entry-assessments-v1-1-".length()))))),context),request.observations().snapshot());
                if(step.matches("query-combat-phase-event-trace-v1-[1-9][0-9]*"))return forecast(session,new ArmyForecastReads.Selection(new ArmyCalls.CombatId(PublicMethod.QUERY_COMBAT_PHASE_EVENT_TRACE_V1,revision(request),new FullId(Integer.parseInt(step.substring("query-combat-phase-event-trace-v1-".length())))),context),request.observations().snapshot());
                if(step.matches("query-current-battle-knight-v1-(?:0|[1-9][0-9]*)-[1-9][0-9]*-[1-9][0-9]*")) {
                    var call=ArmyCallCodec.decode(PublicMethod.QUERY_CURRENT_BATTLE_KNIGHT_V1,new RawJson(DriverJson.encode(selected.arguments())));
                    return forecast(session,new ArmyForecastReads.Selection(call,context),request.observations().snapshot());
                }
                if(step.matches("query-battle-control-snapshot-v1-(?:0|[1-9][0-9]*)")) {
                    var call=new ArmyCalls.Unit(PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1,revision(request),new PublicUnitId(Integer.parseInt(step.substring("query-battle-control-snapshot-v1-".length()))));
                    return battle(session,new ArmyBattleReads.Selection(call,context,ArmyBattleReads.Capture.PUBLIC_QUERY));
                }
                if(step.matches("query-battle-transition-v1-(?:0|-?[1-9][0-9]*)"))return battle(session,new ArmyBattleReads.Selection(new ArmyCalls.CombatId(PublicMethod.QUERY_BATTLE_TRANSITION_V1,revision(request),new FullId(Integer.parseInt(step.substring("query-battle-transition-v1-".length())))),context,ArmyBattleReads.Capture.PUBLIC_QUERY));
                var terminal=terminal(step,revision(request));
                if(terminal.isPresent())return battle(session,new ArmyBattleReads.Selection(terminal.orElseThrow(),context,ArmyBattleReads.Capture.PUBLIC_QUERY));
                return unavailable("no installed typed ordinary military read matches this exact operation: "+step);
            });
        } catch(IOException|java.io.UncheckedIOException|IllegalArgumentException|IllegalStateException failure){return unavailable("actual military read unavailable: "+failure.getMessage());}
    }
    /** Reuses the installed finance ROOT owner and its original pure decoder; no second native contract. */
    static PlanningReadResult<Obj> root(FinanceReadContracts definitions,PlanningReadPort port,
            org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,PlanningRequest request) {
        var query=FinanceReadContracts.Query.ROOT;
        var actual=definitions.read(same,query,port,request);
        if(actual instanceof PlanningReadResult.Unavailable<FinanceReadContracts.Packet> missing)
            return new PlanningReadResult.Unavailable<>(missing.reason(),missing.original(),missing.decodeFailure(),missing.observedFailure());
        var known=(PlanningReadResult.Known<FinanceReadContracts.Packet>)actual;
        var replay=definitions.decodeOriginal(query,known.receipt(),request.observations().snapshot());
        org.xar.ck3.control.contracts.StrictJson.require(known.value().receipt().equals(known.receipt())
                &&replay.result().equals(known.value().result())&&replay.originalResult().equals(known.value().originalResult()),
                "ordinary campaign-root result differs from its actual original typed owner");
        return new PlanningReadResult.Known<>(replay.result(),known.receipt(),known.originalReceipt());
    }
    /** Actual shared typed producer, original Root read port and exact cold decoder; no new registry or terms model. */
    static PlanningReadResult<Obj> termination(ArmyWarReads sameWarReads,PlanningReadPort actualReads,
            org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,RootReadContractCatalog catalog,ArmyWarReads.Selection selection) {
        var method=selection.input().method();
        org.xar.ck3.control.contracts.StrictJson.require(method==PublicMethod.QUERY_WAR_TERMINATION_OPTIONS||method==PublicMethod.QUERY_WAR_TERMINATION_TERMS,
                "ordinary war exit reader cannot widen the native read family");
        var contract=sameWarReads.contract(catalog,selection);var current=selection.context();
        var request=new PlanningReadRequest(current.before(),current.source(),current.sessionId(),contract.operation(),ArmyWarReads.arguments(selection.input()),current.deadline());
        var actual=actualReads.read(same,contract,request);
        if(actual instanceof PlanningReadResult.Unavailable<ArmyWarReadCodec.Observation> missing)
            return new PlanningReadResult.Unavailable<>(missing.reason(),missing.original(),missing.decodeFailure(),missing.observedFailure());
        if(!(actual instanceof PlanningReadResult.Known<ArmyWarReadCodec.Observation> known))throw new IllegalStateException("unrecognized actual war read result");
        var replayed=actualReads instanceof OriginalMilitaryReadPort original?original.replayOriginal(contract,request,known):contract.replay(known.receipt());
        org.xar.ck3.control.contracts.StrictJson.require(replayed.equals(known.value())&&replayed.method()==method,
                "war exit value differs from its actual original typed cold replay");
        // In particular, original outer/inner Unsupported on build .4 is preserved as observed data.
        return new PlanningReadResult.Known<>(replayed.normalizedResult(),known.receipt(),known.originalReceipt());
    }
    static Optional<ArmyCalls.War> termination(String step,ArmyCalls.Revision revision) {
        Objects.requireNonNull(step);Objects.requireNonNull(revision);
        var options=Pattern.compile("query-war-termination-options-([1-9][0-9]*)").matcher(step);
        var terms=Pattern.compile("query-war-termination-terms-v1-([1-9][0-9]*)").matcher(step);
        PublicMethod method;String id;
        if(options.matches()){method=PublicMethod.QUERY_WAR_TERMINATION_OPTIONS;id=options.group(1);}
        else if(terms.matches()){method=PublicMethod.QUERY_WAR_TERMINATION_TERMS;id=terms.group(1);}
        else return Optional.empty();
        if(id.length()>10)return Optional.empty();
        var war=new java.math.BigInteger(id);if(war.compareTo(java.math.BigInteger.valueOf(Integer.MAX_VALUE))>0)return Optional.empty();
        return Optional.of(new ArmyCalls.War(method,revision,war));
    }
    private PlanningReadResult<Obj> route(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session session,ArmyPlanningReads.Selection input) {
        var result=routes.collect(session,runtime.readCatalog(),input);if(result instanceof PlanningReadResult.Known<MilitaryReadObservation> known)return new PlanningReadResult.Known<>(known.value().normalizedResult(),known.receipt(),known.originalReceipt());
        var unavailable=(PlanningReadResult.Unavailable<MilitaryReadObservation>)result;return new PlanningReadResult.Unavailable<>(unavailable.reason(),unavailable.original());
    }
    private PlanningReadResult<Obj> forecast(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session session,ArmyForecastReads.Selection input,Obj currentSnapshot)throws IOException {
        if(!(input.input() instanceof ArmyCalls.WarEntry)) {
            var contract=forecasts.contract(runtime.readCatalog(),input);var context=input.context();
            var arguments=DriverJson.object(ArmyCallCodec.encode(input.input()).bytes(),DriverJson.MAX_NATIVE_BYTES);
            var request=new PlanningReadRequest(context.before(),context.source(),context.sessionId(),contract.operation(),arguments,context.deadline());
            var retained=ordinaryReads.find(session,contract,request);
            if(retained.isPresent()) {
                var witness=retained.orElseThrow();var known=witness.requireCurrent(session,contract,request);
                var replayed=witness.originalContract().replay(known.receipt());
                org.xar.ck3.control.contracts.StrictJson.require(replayed.equals(known.value()),"canonical forecast differs from original pure decoder");
                var originalRequest=known.receipt().request();
                var originalSelection=new ArmyForecastReads.Selection(input.input(),new Context(originalRequest.before(),originalRequest.source(),originalRequest.sessionId(),originalRequest.deadline()));
                var active=replayed instanceof ForecastReadObservation.CombatInputs?forecasts.activateCanonical(originalSelection,known.receipt(),currentSnapshot):replayed;
                org.xar.ck3.control.contracts.StrictJson.require(active.equals(replayed),"current canonical activation differs from original pure decoder");
                return new PlanningReadResult.Known<>(active.normalizedResult(),known.receipt(),known.originalReceipt());
            }
        }
        var result=forecasts.collect(session,runtime.readCatalog(),input);if(result instanceof PlanningReadResult.Known<ForecastReadObservation> known)return new PlanningReadResult.Known<>(known.value().normalizedResult(),known.receipt(),known.originalReceipt());
        var unavailable=(PlanningReadResult.Unavailable<ForecastReadObservation>)result;return new PlanningReadResult.Unavailable<>(unavailable.reason(),unavailable.original());
    }
    private PlanningReadResult<Obj> battle(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session session,ArmyBattleReads.Selection input) {
        var queried=ordinaryReads.read(session,battles.issue(runtime.readCatalog(),input),battles.request(input));
        if(queried instanceof PlanningReadResult.Unavailable<ArmyBattleReads.Observation> missing)return new PlanningReadResult.Unavailable<>(missing.reason(),missing.original());
        var result=(PlanningReadResult.Known<ArmyBattleReads.Observation>)queried;Obj raw=DriverJson.object(result.receipt().original().originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);
        var context=input.context();raw=raw.with("queried_snapshot_id",new OpportunityJson.Text(context.before().frame().snapshotId()))
                .with("queried_revision",new OpportunityJson.IntegerValue(context.before().frame().revision())).with("queried_native_revision",new OpportunityJson.IntegerValue(context.nativeRevision()))
                .with("queried_connection_generation",new OpportunityJson.IntegerValue(result.receipt().before().binding().connectionGeneration()))
                .with("queried_episode_run_id",new OpportunityJson.Text(context.before().frame().episodeRunId()));
        return new PlanningReadResult.Known<>(raw,result.receipt(),result.originalReceipt());
    }
    /** Canonical original terminal selection, including character-only capture and an absent zero cursor. */
    static Optional<ArmyCalls.Terminal> terminal(String step,ArmyCalls.Revision revision) {
        String prefix="query-battle-terminal-transition-v1-";if(!step.startsWith(prefix))return Optional.empty();
        String wire=step.substring(prefix.length());String[] components=wire.split(":characters:",-1);
        if(components.length>2)return Optional.empty();List<PositiveId> characters=List.of();
        if(components.length==2) {
            if(!components[1].matches("[1-9][0-9]*(?:,[1-9][0-9]*)*"))return Optional.empty();
            characters=java.util.Arrays.stream(components[1].split(",")).map(Integer::parseInt).map(PositiveId::new).toList();
            if(characters.size()>64||new java.util.HashSet<>(characters).size()!=characters.size())return Optional.empty();
        }
        if(components[0].equals("none"))return characters.isEmpty()?Optional.empty():Optional.of(new ArmyCalls.Terminal(revision,new NullValue<>(),new NullValue<>(),new Missing<>(),new Present<>(characters)));
        var triple=Pattern.compile("(0|-?[1-9][0-9]*)-(0|[1-9][0-9]*)-(0|[1-9][0-9]*)").matcher(components[0]);if(!triple.matches())return Optional.empty();
        var cursor=new java.math.BigInteger(triple.group(3));Field<UInt64> after=cursor.signum()==0?new Missing<>():new Present<>(new UInt64(cursor));
        return Optional.of(new ArmyCalls.Terminal(revision,new Present<>(new FullId(Integer.parseInt(triple.group(1)))),new Present<>(new PublicUnitId(Integer.parseInt(triple.group(2)))),after,new Present<>(characters)));
    }
    private static ArmyCalls.Revision revision(PlanningRequest request){return new ArmyCalls.Revision(new Present<>(request.before().frame().revision()));}
    private static PlanningReadResult.Unavailable<Obj> unavailable(String reason){return new PlanningReadResult.Unavailable<>(reason,Optional.empty());}
}
