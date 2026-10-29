package org.xar.ck3.control.nativebridge.capabilities.army;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.military.ForecastReadObservation;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Public typed service and ordinary callers share the exact same finite read families and writer session. */
public final class ArmyForecastService {
    @FunctionalInterface public interface Deadline {Instant current();}
    public record Reply(ArmyRetreatFrames.Current before,ArmyRetreatFrames.Current after,
            PlanningReadResult.Known<ForecastReadObservation> actual,Optional<CombatLoadedPlaysetProof.Evidence> loadedPlaysetEvidence) {
        /** Historical/native-candidate construction carries no loaded-source authority. */
        public Reply(ArmyRetreatFrames.Current before,ArmyRetreatFrames.Current after,PlanningReadResult.Known<ForecastReadObservation> actual){this(before,after,actual,Optional.empty());}
        public Reply {
            Objects.requireNonNull(before);Objects.requireNonNull(after);Objects.requireNonNull(actual);Objects.requireNonNull(loadedPlaysetEvidence);sameFrame(before,after);
            if(loadedPlaysetEvidence.isPresent()) {
                need(actual.value() instanceof ForecastReadObservation.CombatInputs combat
                        &&combat.observation().version()==org.xar.ck3.control.wave2.military.forecast.CombatObservationCache.Version.V3,"loaded playset evidence belongs only to original CombatV3");
                loadedPlaysetEvidence.orElseThrow().requireFrame(after.actual());
            }
        }
    }
    private final ContinuityStorePort writer;
    private final ArmyRetreatFrames frames;
    private final ArmyForecastReads reads;
    private final java.util.function.Supplier<RootReadContractCatalog> catalog;
    private final Deadline deadline;
    private final Optional<CombatPublicProjection.LoadedPlaysetSource> loadedPlaysetSource;
    public ArmyForecastService(ContinuityStorePort originalWriter,ArmyRetreatFrames currentFrames,ArmyForecastReads actualReads,
            RootReadContractCatalog installedCatalog,Deadline currentDeadline) {
        this(originalWriter,currentFrames,actualReads,()->installedCatalog,currentDeadline);
    }
    public ArmyForecastService(ContinuityStorePort originalWriter,ArmyRetreatFrames currentFrames,ArmyForecastReads actualReads,
            java.util.function.Supplier<RootReadContractCatalog> onceBoundCatalog,Deadline currentDeadline) {
        this(originalWriter,currentFrames,actualReads,onceBoundCatalog,currentDeadline,Optional.empty());
    }
    public ArmyForecastService(ContinuityStorePort originalWriter,ArmyRetreatFrames currentFrames,ArmyForecastReads actualReads,
            RootReadContractCatalog installedCatalog,Deadline currentDeadline,CombatPublicProjection.LoadedPlaysetSource actualLoadedSource) {
        this(originalWriter,currentFrames,actualReads,()->installedCatalog,currentDeadline,Optional.of(Objects.requireNonNull(actualLoadedSource)));
    }
    public ArmyForecastService(ContinuityStorePort originalWriter,ArmyRetreatFrames currentFrames,ArmyForecastReads actualReads,
            java.util.function.Supplier<RootReadContractCatalog> onceBoundCatalog,Deadline currentDeadline,CombatPublicProjection.LoadedPlaysetSource actualLoadedSource) {
        this(originalWriter,currentFrames,actualReads,onceBoundCatalog,currentDeadline,Optional.of(Objects.requireNonNull(actualLoadedSource)));
    }
    private ArmyForecastService(ContinuityStorePort originalWriter,ArmyRetreatFrames currentFrames,ArmyForecastReads actualReads,
            java.util.function.Supplier<RootReadContractCatalog> onceBoundCatalog,Deadline currentDeadline,Optional<CombatPublicProjection.LoadedPlaysetSource> actualLoadedSource) {
        writer=Objects.requireNonNull(originalWriter);frames=Objects.requireNonNull(currentFrames);reads=Objects.requireNonNull(actualReads);
        catalog=Objects.requireNonNull(onceBoundCatalog);deadline=Objects.requireNonNull(currentDeadline);loadedPlaysetSource=Objects.requireNonNull(actualLoadedSource);
    }
    public Reply read(ContinuityStorePort.Session borrowed,ArmyCalls.Call input,Instant end)throws IOException,InterruptedException {
        if(input.method()==PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS_V3&&loadedPlaysetSource.isEmpty())
            throw new IOException("CombatV3 public result requires the actual Root loaded-playset source before issuing a Native query");
        var before=frames.current(end);input.revision().requireCurrent(before.context().before().frame().revision());
        var result=reads.collect(borrowed,Objects.requireNonNull(catalog.get(),"forecast requires installed actual Root catalog"),new ArmyForecastReads.Selection(input,before.context()));
        if(!(result instanceof PlanningReadResult.Known<ForecastReadObservation> known))throw new IOException(((PlanningReadResult.Unavailable<ForecastReadObservation>)result).reason());
        // The sole KnownReadObserver may publish newly observed cache fields before this recapture.
        var after=frames.current(end);sameFrame(before,after);
        Optional<CombatLoadedPlaysetProof.Evidence> proof=input.method()==PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS_V3
                ?Optional.of(loadedPlaysetSource.orElseThrow().observe(new CombatPublicProjection.Input(before.actual(),after.actual(),known))):Optional.empty();
        return new Reply(before,after,known,proof);
    }
    public Reply query_combat_simulation_inputs(ArmyCalls.Combat input)throws InterruptedException {need(input.method()==PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS,"v2 public method differs");return query(input);}
    public Reply query_combat_simulation_inputs_v3(ArmyCalls.Combat input)throws InterruptedException {need(input.method()==PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS_V3,"v3 public method differs");return query(input);}
    public Reply query_war_entry_assessments(ArmyCalls.WarEntry input)throws InterruptedException {return query(input);}
    public Reply query_current_battle_knight_v1(ArmyCalls.Knight input)throws InterruptedException {return query(input);}
    public Reply query_combat_phase_event_trace_v1(ArmyCalls.CombatId input)throws InterruptedException {need(input.method()==PublicMethod.QUERY_COMBAT_PHASE_EVENT_TRACE_V1,"phase trace public method differs");return query(input);}
    private Reply query(ArmyCalls.Call input)throws InterruptedException {
        try{return writer.locked(session->{try{return read(session,input,deadline.current());}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new InterruptedIo(interrupted);}});}
        catch(InterruptedIo interrupted){throw (InterruptedException)interrupted.getCause();}catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    public List<PublicBindings.BoundBinding> install(PublicBindings publicBindings,ExactRef actualServiceSource) {
        List<PublicBindings.BoundBinding> result=new ArrayList<>();
        result.add(bind(publicBindings,PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS,ArmyCalls.Combat.class,this::query_combat_simulation_inputs,"query_combat_simulation_inputs",actualServiceSource));
        result.add(bind(publicBindings,PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS_V3,ArmyCalls.Combat.class,this::query_combat_simulation_inputs_v3,"query_combat_simulation_inputs_v3",actualServiceSource));
        result.add(bind(publicBindings,PublicMethod.QUERY_WAR_ENTRY_ASSESSMENTS,ArmyCalls.WarEntry.class,this::query_war_entry_assessments,"query_war_entry_assessments",actualServiceSource));
        result.add(bind(publicBindings,PublicMethod.QUERY_CURRENT_BATTLE_KNIGHT_V1,ArmyCalls.Knight.class,this::query_current_battle_knight_v1,"query_current_battle_knight_v1",actualServiceSource));
        result.add(bind(publicBindings,PublicMethod.QUERY_COMBAT_PHASE_EVENT_TRACE_V1,ArmyCalls.CombatId.class,this::query_combat_phase_event_trace_v1,"query_combat_phase_event_trace_v1",actualServiceSource));
        return List.copyOf(result);
    }
    private static <A extends ArmyCalls.Call>PublicBindings.BoundBinding bind(PublicBindings bindings,PublicMethod method,Class<A> type,
            PublicRoutes.Handler<A,Reply> invoke,String actualMethod,ExactRef actualSource) {
        String resultProfile=switch(ArmyForecastPublicResultCodec.profile(method)) {
            case ORIGINAL_PUBLIC_RESULT -> "source-bound original public result; action/business qualification remains independent";
            case NATIVE_CANDIDATE_PENDING_SERVICE_DERIVATIONS -> "typed native candidate only; original Service knight/playset/physical-association derivations remain incomplete";
        };
        return bindings.register(method,type,Reply.class,invoke,args->{if(!(args instanceof PublicBindings.Value value))throw new IllegalArgumentException("forecast read requires exact named arguments");return type.cast(ArmyCallCodec.decode(method,value.original()));},
                reply->encode(method,reply),new PublicRoutes.Target(ArmyForecastService.class.getName(),actualMethod,actualSource),PublicRoutes.Status.IMPLEMENTED,
                "actual native read handler; "+resultProfile);
    }
    public static RawJson encode(PublicMethod actualMethod,Reply reply){
        return ArmyForecastPublicResultCodec.encode(actualMethod,reply,reply.loadedPlaysetEvidence());
    }
    private static void sameFrame(ArmyRetreatFrames.Current before,ArmyRetreatFrames.Current after) {
        need(before.actual().identity().equals(after.actual().identity())&&before.actual().source().equals(after.actual().source())
                &&before.actual().sessionId().equals(after.actual().sessionId())&&before.actual().connectionGeneration().equals(after.actual().connectionGeneration())
                &&before.source().equals(after.source()),"forecast service crossed original physical frame/episode/connection during publication");
    }
    private static void need(boolean condition,String reason){if(!condition)throw new IllegalArgumentException(reason);}
    private static final class InterruptedIo extends IOException { @java.io.Serial private static final long serialVersionUID = 1L;InterruptedIo(InterruptedException cause){super(cause);}}
}
