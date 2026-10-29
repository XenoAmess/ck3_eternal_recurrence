package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.battleadvance.*;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.history.*;
import org.xar.ck3.control.application.routecontact.*;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.DataRole.*;

/** One actual source composition for the two Route operations over the already installed Life owner.
 * Explicit existing capability/deadline originals grant neither a new clock nor a native permission. */
public final class RootRouteContactAdvanceSourcesFactory {
    private RootRouteContactAdvanceSourcesFactory(){ }
    public static RootRouteContactAdvanceRuntime.Prepared prepare(RootRuntimeDefinitions.Inputs inputs,
            RootRuntimeSelectedSources selected,RootCampaignPoliciesFactory.BoundDeadline sameDeadline)throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(selected);Objects.requireNonNull(sameDeadline);
        selected.requireInputs(inputs);
        var configuredDeadline=RootRuntimeSourceProducts.exact(inputs.data(CAMPAIGN_DEADLINE));
        if(!sameDeadline.original().equals(configuredDeadline))throw new IOException("Route product crossed the actual campaign deadline original");
        var readers=new ArrayList<ExactRef>();
        for(Class<?> type:List.of(RouteContactComposite.class,RouteContactSteps.class,RouteContactProofs.class,
                RouteContactModel.class,RouteContactCodec.class,RouteContactPostconditions.class,
                RouteContactEvidenceCodec.class,RouteContactEvidenceArchive.class,RouteContactArchivedVerifier.class,
                RouteContactArchivedFrames.class,RouteContactArchivedHistory.class,SharedRouteContactClocks.class,
                SharedRouteContactArchivedClocks.class,DriverHistoryAccess.class,RouteContactHistoryAdapter.class,
                DriverSurvivingHistory.class,DriverHistoryImport.class,BattleAdvanceComposite.class,
                BattleAdvanceArchive.class,BattleAdvanceResultCodec.class,BattleAdvanceArchivedReplay.class,
                BattleAdvancePlan.class,BattleAdvanceFrame.class,BattleAdvanceStep.class,AdvanceClock.class,
                AdvanceWait.class,AdvanceResult.class,AdvanceClockArchivedReplay.class,LifeAdvanceRootReplay.class,
                NativeEffectEvidence.class,RootGuardEvidence.class,DriverObservationEvidenceReader.class,
                DynamicCapabilities.class,AdvancePrimitiveEvidence.class))
            readers.add(selected.javaSource(APPLICATION,type));
        for(Class<?> type:List.of(RootRouteContactAdvanceRuntime.class,RootRouteContactAdvanceResult.class,
                RootRouteContactAdvancePublicProducts.class,RootRuntimeDomainAssembly.class,RootPublicStepExecution.class,RootPublicStepFailureOriginals.class,
                RootLifeAdvancePublicResult.class,RootBattleAdvancePublicResult.class,RootAdvanceInfrastructureFactory.class,
                RootLifeRuntimeFactory.class,RootRouteContactAdvanceSourcesFactory.class))
            readers.add(selected.javaSource(LOCAL_SERVICE,type));
        var sources=new RootRouteContactAdvanceRuntime.Sources(selected.javaSource(APPLICATION,RouteContactComposite.class),
                selected.javaSource(APPLICATION,RouteContactEvidenceCodec.class),selected.javaSource(APPLICATION,RouteContactArchivedVerifier.class),
                readers.stream().distinct().toList());
        var capability=inputs.data(CAPABILITY_CONFIGURATION);
        var actualBytes=new RawJson(RootRuntimeDefinitions.readData(new RootRuntimeDefinitionModel.DataPin(CAPABILITY_CONFIGURATION,capability)));
        var configuration=new RootRouteContactAdvanceRuntime.Configuration(RootRuntimeSourceProducts.exact(capability),actualBytes,sameDeadline);
        selected.requireInputs(inputs);selected.requireCurrent();
        return new RootRouteContactAdvanceRuntime.Prepared(sources,configuration);
    }
}
