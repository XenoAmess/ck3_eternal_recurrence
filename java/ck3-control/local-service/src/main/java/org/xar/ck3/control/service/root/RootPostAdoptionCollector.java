package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Clock;
import java.math.BigInteger;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.platform.ManagedGameSession;

/** Phase one publishes only actual raw Native/Driver/source/4SEM.
 * Phase two retains the admitted physical runtime. Core finishes the stage and binds its real session
 * before importing the twelve domains, initializing planning and publishing the ordinary host. */
public final class RootPostAdoptionCollector implements RootRestoreAdapters.PostAdoptionPort {
    private static final class Attempt {
        final RestoreCheckpointService.Request request;
        final DriverBootstrap.Adopted adopted;
        final ManagedGameSession replacement;
        final RootPlanningReads reads;
        final RetainedRuntimeCreation<RootInstalledCatalog> installation=new RetainedRuntimeCreation<>();
        final RetainedRuntimeCreation<RootRestoreAdapters.RestoredRuntime> ordinary=new RetainedRuntimeCreation<>();
        RestoreCheckpointService issuer;
        RestoreCheckpointService.RestoreBinding binding;
        SavedAttachmentSourceStore sources;
        Attempt(RestoreCheckpointService.Request request,DriverBootstrap.Adopted adopted,ManagedGameSession replacement,
                RootPlanningReads reads){
            this.request=request;this.adopted=adopted;this.replacement=replacement;this.reads=reads;
        }
        void requireSame(RestoreCheckpointService.Request actual,DriverBootstrap.Adopted driver,ManagedGameSession game)throws IOException{
            if(!request.equals(actual)||adopted!=driver||replacement!=game)
                throw new IOException("retained restoration request cannot replace its original Driver/Game/source/deadline");
        }
        void bindAdmission(RestoreCheckpointService actualIssuer,RestoreCheckpointService.RestoreBinding actual,
                SavedAttachmentSourceStore actualSources)throws IOException{
            if(binding==null){issuer=actualIssuer;binding=actual;sources=actualSources;}
            else if(issuer!=actualIssuer||binding!=actual||sources!=actualSources)
                throw new IOException("entered restored runtime cannot replace its private issuer/binding/source store");
        }
    }
    private final RootApplicationAssembly.Core core;
    private final RootCoreBoundPorts ports;
    private final RootRuntimeCatalogFactory catalogs;
    private final RootRuntimeReadiness readiness;
    private final Duration freshness;
    private final Clock clock;
    private final Optional<RootFrozenRunProfile.FrozenRunProfile> originalFrozen;
    private final Map<String,Attempt> attempts=new HashMap<>();

    public RootPostAdoptionCollector(RootApplicationAssembly.Core core,RootCoreBoundPorts ports,
            RootRuntimeCatalogFactory catalogs,RootRuntimeReadiness readiness,Duration freshness,Clock clock,
            RootFrozenRunProfile.FrozenRunProfile originalFrozen)throws IOException {
        this(core,ports,catalogs,readiness,freshness,clock,Optional.of(originalFrozen));
    }

    public static RootPostAdoptionCollector ordinary(RootApplicationAssembly.Core core,RootCoreBoundPorts ports,
            RootRuntimeCatalogFactory catalogs,RootRuntimeReadiness readiness,Duration freshness,Clock clock)throws IOException {
        return new RootPostAdoptionCollector(core,ports,catalogs,readiness,freshness,clock,Optional.empty());
    }

    private RootPostAdoptionCollector(RootApplicationAssembly.Core core,RootCoreBoundPorts ports,
            RootRuntimeCatalogFactory catalogs,RootRuntimeReadiness readiness,Duration freshness,Clock clock,
            Optional<RootFrozenRunProfile.FrozenRunProfile> originalFrozen)throws IOException {
        this.core=Objects.requireNonNull(core);this.ports=Objects.requireNonNull(ports);
        this.catalogs=Objects.requireNonNull(catalogs);this.readiness=Objects.requireNonNull(readiness);
        this.freshness=Objects.requireNonNull(freshness);this.clock=Objects.requireNonNull(clock);
        this.originalFrozen=Objects.requireNonNull(originalFrozen);
        if(ports.requireCore()!=core||core.archive().writer()!=core.writer())
            throw new IOException("two-phase restoration must retain its exact original Core/writer/archive");
    }

    @Override public synchronized RootLifecycleAuthority physical(ContinuityStorePort.Session same,DriverBootstrap.Adopted adopted,
            ManagedGameSession replacement,RestoreCheckpointService.Request original,RestoreCheckpointService.ReadWindow window)throws IOException{
        Objects.requireNonNull(window).requireOriginal(original);requireOwner(same,adopted,replacement,original,window);
        Attempt selected=attempts.get(original.requestId());
        if(selected==null){
            for(Attempt prior:attempts.values())
                if(prior.adopted==adopted||prior.replacement==replacement)
                    throw new IOException("another request ID cannot replay entered restoration construction");
            if(attempts.size()>=64)throw new IOException("bounded retained restoration attempts require original reconciliation");
            selected=new Attempt(original,adopted,replacement,new RootPlanningReads(core.writer()));
            attempts.put(original.requestId(),selected);
        }
        selected.requireSame(original,adopted,replacement);
        Attempt retained=selected;
        RootInstalledCatalog installed=selected.installation.obtain(()->install(same,retained,window));
        // No capability observer, ordinary collector, planning input or domain import is constructed here.
        // This exact catalog is retained by the private physical installation, before public Host adoption.
        // A public currentRoot lookup would still resolve the retired prior physical Game here.
        var actualLifecycle=installed.remainingDomains().lifecycle();actualLifecycle.requireContext(installed.context());
        RootLifecycleAuthority actual=actualLifecycle.physical();
        requireOwner(same,adopted,replacement,original,window);return actual;
    }

    @Override public synchronized RootRestoreAdapters.RestoredRuntime create(ContinuityStorePort.Session same,
            DriverBootstrap.Adopted adopted,ManagedGameSession replacement,RestoreCheckpointService.Request original,
            RestoreCheckpointService actualIssuer,RestoreCheckpointService.RestoreBinding actualBinding,
            SavedAttachmentSourceStore actualSources)throws IOException{
        Objects.requireNonNull(actualIssuer);Objects.requireNonNull(actualBinding);Objects.requireNonNull(actualSources);
        var window=actualBinding.readWindow();window.requireOriginal(original);
        requireOwner(same,adopted,replacement,original,window);
        Attempt selected=attempts.get(original.requestId());
        if(selected==null)throw new IOException("ordinary restoration requires its retained original phase-one physical owner");
        selected.requireSame(original,adopted,replacement);
        actualIssuer.requireRetainedOriginal(same,actualBinding);
        if(!actualBinding.pair().equals(original.pair())||!actualBinding.source().equals(adopted.source())
                ||!actualBinding.session().game().equals(replacement.generation())
                ||!actualBinding.session().sessionId().equals(replacement.sessionId()))
            throw new IOException("actual private restoration admission differs from its phase-one native Driver");
        requireDriverSession(actualBinding.driver().session(),adopted.session(),actualBinding.session(),
                replacement.launchPlan().pipeName(),adopted.first().identity().frame().identity().player(),
                adopted.first().identity().frame().episodeRunId());
        selected.bindAdmission(actualIssuer,actualBinding,actualSources);
        Attempt retained=selected;
        RootRestoreAdapters.RestoredRuntime result=selected.ordinary.obtain(()->{
            RootInstalledCatalog installed=retained.installation.obtain(()->install(same,retained,window));
            RootRuntimeContext context=installed.context();
            // actualSources is the preceding physical runtime's retained source store, not this new
            // Root session's store. The new session binds its own saved sources/materials after Staged.finish.
            context.bindRetainedRestoration(same,actualIssuer,actualBinding);
            // Staged does not exist yet. Its actual session/material/first-save proof is bound by Core.finish.
            // This producer cannot import domains or obtain ordinary Ready before that binding exists.
            context.requireRestorationOriginal(same,actualBinding);
            if(originalFrozen.isPresent()) bindRestoredPlanning(same,installed,originalFrozen.orElseThrow());
            return readiness.restored(same,installed,adopted,actualBinding,window.deadline());
        });
        result.capabilities().requireOwner(adopted.authority(),core.archive(),result.bindings());
        actualIssuer.requireRetainedOriginal(same,actualBinding);
        requireOwner(same,adopted,replacement,original,window);return result;
    }

    /** Carries original constructor provenance after genuine restoration publication and before planning/Ready. */
    static void bindRestoredPlanning(ContinuityStorePort.Session same,RootInstalledCatalog installed,
            RootFrozenRunProfile.FrozenRunProfile original)throws IOException {
        Objects.requireNonNull(installed);Objects.requireNonNull(original);
        if(original.importMode() instanceof RootFrozenRunProfile.DisabledFreshFixture
                ||original.importMode() instanceof RootFrozenRunProfile.EnabledNativeCampaign) {
            // This Frozen belongs to the original run; its private issuer validates the replacement separately.
            installed.bindRestoredNativeCampaignPlanning(same,original,installed.context().requireRestoredOrigin(same));
        }
    }

    private RootInstalledCatalog install(ContinuityStorePort.Session same,Attempt attempt,RestoreCheckpointService.ReadWindow window)throws IOException{
        core.writer().requireSession(same);window.requireOriginal(attempt.request);
        RootInstalledCatalog installed=catalogs.install(core,attempt.replacement,attempt.adopted.source(),attempt.reads,clock,
                window.deadline());
        RootRuntimeContext context=installed.context();
        if(context.core()!=core||context.writer()!=core.writer()||context.archive()!=core.archive()
                ||context.game()!=attempt.replacement||context.reads()!=attempt.reads||context.clock()!=clock
                ||!context.source().equals(attempt.adopted.source()))
            throw new IOException("restoration installation captured another physical runtime or original writer");
        installed.bindPhysicalDriver(attempt.adopted);
        return installed;
    }

    /** Cross-type projection only. This data check grants no private restore admission. */
    static void requireDriverSession(DriverStateSnapshot.Session driver,TransportSession transport,SessionIdentity admitted,
            String actualPipe,BigInteger actualActor,String actualEpisode)throws IOException {
        Objects.requireNonNull(driver);Objects.requireNonNull(transport);Objects.requireNonNull(admitted);
        if(!admitted.machineId().equals(transport.machineId())||!admitted.game().equals(transport.game())
                ||!admitted.sessionId().equals(transport.sessionId())||driver.bridgePid()!=transport.game().pid()
                ||!driver.pipeName().equals(actualPipe)||!driver.actorId().equals(actualActor)
                ||!driver.episodeRunId().equals(actualEpisode))
            throw new IOException("restored Driver differs from admitted transport/Game/pipe/player/episode");
    }

    private void requireOwner(ContinuityStorePort.Session same,DriverBootstrap.Adopted adopted,
            ManagedGameSession replacement,RestoreCheckpointService.Request original,RestoreCheckpointService.ReadWindow window)throws IOException{
        core.writer().requireSession(same);Objects.requireNonNull(adopted);Objects.requireNonNull(replacement);Objects.requireNonNull(original);
        window.requireOriginal(original);
        if(!clock.instant().isBefore(window.deadline()))throw new IOException("actual restoration read window expired");
        replacement.verify();
        if(adopted.status()!=DriverBootstrap.AdoptionStatus.QUALIFICATION_REQUIRED
                ||!adopted.session().game().equals(replacement.generation())
                ||!adopted.session().sessionId().equals(replacement.sessionId())
                ||!adopted.session().machineId().equals(replacement.machineId())
                ||!adopted.source().machineId().equals(replacement.machineId()))
            throw new IOException("actual adopted Driver differs from its replacement physical owner");
        adopted.producer().requireSameTransport(replacement.nativeTransport(),adopted.source());
        replacement.launchPlan().sources().requireLoadedClass(RootPostAdoptionCollector.class);
        replacement.launchPlan().sources().requireLoadedClass(RootCoreBoundPorts.class);
        replacement.launchPlan().sources().requireLoadedClass(RetainedRuntimeCreation.class);
    }
}

