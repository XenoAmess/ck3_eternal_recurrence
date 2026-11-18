package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Secondary family view of the one actual typed ordinary producer; no independent Native contract. */
public final class RootFamilyEducationRead implements FamilyPorts.ProjectedSource {
    @FunctionalInterface public interface OrdinaryRead {
        PlanningReadResult<InteractionModels.OrdinaryContext> read(InteractionModels.Context actual,
                InteractionModels.OrdinaryRequest intent) throws IOException;
    }
    private final RootRuntimeContext context;
    private final InteractionCapabilities interactions;
    private final RootFamilyInteractionContext projection;
    public RootFamilyEducationRead(RootRuntimeContext context, InteractionCapabilities actualInteractions,
            RootInteractionContextProjection actualProjection) {
        this(context,actualInteractions,RootFamilyInteractionContext.qualified(actualProjection));
    }
    public RootFamilyEducationRead(RootRuntimeContext context, InteractionCapabilities actualInteractions,
            RootFamilyInteractionContext actualProjection) {
        this.context=Objects.requireNonNull(context);interactions=Objects.requireNonNull(actualInteractions);
        projection=Objects.requireNonNull(actualProjection);
    }
    /** Recognition selects a negative source for unmigrated builds, never a legacy Context or Native permit. */
    public RootFamilyEducationRead(RootRuntimeContext context, InteractionCapabilities actualInteractions,
            KnownInteractionsRuntimeInstaller.ConfiguredBuild actualBuild) {
        this(context,actualInteractions,configuredContext(actualBuild));
    }
    public static RootFamilyInteractionContext configuredContext(KnownInteractionsRuntimeInstaller.ConfiguredBuild build) {
        Objects.requireNonNull(build);
        return build.qualified()
                ?RootFamilyInteractionContext.qualified(new RootInteractionContextProjection(build.requireQualified()))
                :RootFamilyInteractionContext.configuredUnavailable(build);
    }
    @Override public FamilyPorts.ProjectedRead read(PlanningRequest request,Obj familyArguments) {
        try {
            context.requireCurrent(request.deadline());var same=context.borrowedSession();context.writer().requireSession(same);
            return context.collector().currentPlanning(same,request,request.deadline(),(original,lease)->{
                var result=projectHeld(projection,request,lease.frame(),familyArguments,interactions::queryCharacterInteractionOrdinaryV1);
                context.writer().requireSession(same);return result;
            });
        } catch(IOException failure) {throw new UncheckedIOException("actual shared ordinary education read unavailable",failure);}
    }
    /** Same held callback used by the live reader. Public DATA does not replace the caller's collector/writer custody. */
    public static FamilyPorts.ProjectedRead projectHeld(RootFamilyInteractionContext source,PlanningRequest request,
            Complete held,Obj familyArguments,OrdinaryRead actualRead) throws IOException {
        Objects.requireNonNull(source);Objects.requireNonNull(actualRead);
        return source.projected(request,held,familyArguments,actual->{
            Obj canonical=FamilyEducationNativeProjection.applicationArguments(actual,familyArguments);
            var result=actualRead.read(actual,FamilyEducationNativeProjection.intent(actual,familyArguments));
            return new FamilyPorts.ProjectedRead(canonical,FamilyEducationNativeProjection.projectResult(result));
        });
    }
    @Override public Obj decode(PlanningReadReceipt original) {return FamilyEducationNativeProjection.project(RootFamilyTypedReplay.read(context,original,InteractionModels.OrdinaryContext.class)).value();}
}
