package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.*;
import org.xar.ck3.control.nativebridge.capabilities.religion.ReligionCapabilities;
import org.xar.ck3.control.nativebridge.capabilities.religion.ReligionCapabilities.*;
import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;

/** Concrete pre-Core source composition. Every original is taken from the actual configured exact target. */
public final class RootReligionSourcesFactory {
    private static final String BRIDGE="ck3_autonomous_player/src/xar_autoplayer/bridge/";
    private RootReligionSourcesFactory(){ }
    /** Actual Java request producers and all seven domain extensions; metadata grants no native permission. */
    public static RootReligionPublicProducts.Prepared ordinary(RootReligionPublicProducts.Config config,RootAdditionalDomains.ImplementationMetadata metadata) {
        Objects.requireNonNull(config);Objects.requireNonNull(metadata);
        ExactRef nativeProducer=metadata.implementation(ReligionCapabilities.class);
        var reads=new ArrayList<ReadSource>();for(ReadKind kind:ReadKind.values())reads.add(new ReadSource(kind,nativeProducer));
        var actions=new ArrayList<ActionSource>();for(MutationSource kind:MutationSource.values())actions.add(new ActionSource(kind,nativeProducer));
        List<RootReligionPublicProducts.ExtensionPrepared> extensions=List.of(
                RootReligionTemporalFinance.ordinary(metadata),RootReligionPilgrimage.ordinary(metadata),
                RootReligionDoctrineData.ordinary(metadata),RootReligionReformDraft.ordinary(metadata),
                RootReligionConversion.ordinary(metadata),RootReligionCounty.ordinary(metadata),
                RootReligionHolyPublicProducts.ordinary(config.holyCreationUi(),config.holyCreationOnce(),metadata));
        return new RootReligionPublicProducts.Prepared(new RootReligionPublicProducts.Sources(
                metadata.implementation(RootReligionPublicProducts.class),metadata.implementation(ReligionContract.class),
                metadata.implementation(ReligionCodec.class),metadata.implementation(ReligionService.class),nativeProducer,reads,actions,
                actual->new ReligionService.ExistingReads(actual.remainingDomains().events().religion(),actual.remainingDomains().armyOrdinary().holyOrders()),extensions));
    }
    public static RootReligionPublicProducts.Prepared prepare(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,
            RootRuntimeNativeOriginals.Bound originals,RootSelectedRegistrationConfiguration.Bound actualRegistration,Clock clock)throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(selected);Objects.requireNonNull(originals);Objects.requireNonNull(actualRegistration);Objects.requireNonNull(clock);
        actualRegistration.requireCurrent(inputs,clock);originals.requireCurrent(clock);selected.requireCurrent();
        selected.javaSource(LOCAL_SERVICE,RootReligionSourcesFactory.class);
        var reads=new ArrayList<ReadSource>();
        for(ReadKind kind:ReadKind.values())reads.add(new ReadSource(kind,original(inputs,selected,BRIDGE+switch(kind){
            case CREATION->"player_holy_site_creation_context_private_transport.py";
            case GHW->"faith_observers_private_transport_v1.py";
            case DETAIL->"holy_site_adoption_detail_private_transport.py";
            case COOLDOWN->"holy_site_decision_cooldown_private_transport.py";
            case INDULGENCES->"player_seek_indulgences_terms_private_transport.py";
            case RELIGION_RESULT->"player_religion_conversion_private_action_v1.py";
            case COUNTY_RESULT->"county_conversion_task_private_action_v1.py";
            case ASSEMBLY,TITLE->"confucian_readonly_private_v1.py";
            case CHALLENGERS->"confucian_challenger_graph_v1.py";
            case STRESS->"current_actor_stress_adjustment_contract.py";
            case EPIDEMIC->"epidemic_recovery_private_transport.py";
        })));
        var actions=new ArrayList<ActionSource>();
        for(MutationSource kind:MutationSource.values())actions.add(new ActionSource(kind,original(inputs,selected,BRIDGE+switch(kind){
            case UI->"native_driver.py";
            case CREATION->"holy_site_creation_create_once_private_transport.py";
            case RELIGION_CONVERSION->"player_religion_conversion_private_action_v1.py";
            case COUNTY_TASK->"county_conversion_task_private_action_v1.py";
        })));
        List<RootReligionPublicProducts.ExtensionPrepared> extensions=List.of(
                RootReligionTemporalFinance.prepare(inputs,selected,originals,clock),
                RootReligionPilgrimage.prepare(inputs,selected,originals,clock),
                RootReligionDoctrineData.prepare(inputs,selected,originals,clock),
                RootReligionReformDraft.prepare(inputs,selected,originals,clock),
                RootReligionConversion.prepare(inputs,selected,originals,clock),
                RootReligionCounty.prepare(inputs,selected,originals,clock),
                RootReligionHolyPublicProducts.prepare(inputs,selected,originals,actualRegistration,clock));
        var prepared=new RootReligionPublicProducts.Prepared(new RootReligionPublicProducts.Sources(
                selected.javaSource(LOCAL_SERVICE,RootReligionPublicProducts.class),selected.javaSource(NATIVE_TRANSPORT,ReligionContract.class),
                selected.javaSource(NATIVE_TRANSPORT,ReligionCodec.class),selected.javaSource(NATIVE_TRANSPORT,ReligionService.class),
                selected.javaSource(NATIVE_TRANSPORT,ReligionCapabilities.class),reads,actions,
                actual->new ReligionService.ExistingReads(actual.remainingDomains().events().religion(),actual.remainingDomains().armyOrdinary().holyOrders()),extensions));
        actualRegistration.requireCurrent(inputs,clock);originals.requireCurrent(clock);selected.requireCurrent();return prepared;
    }
    /** No basename search, scratch fallback, Python invocation or source-reference-as-permission shortcut. */
    public static ExactRef original(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,String repositoryRelative)throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(selected);Objects.requireNonNull(repositoryRelative);
        if(!repositoryRelative.startsWith("ck3_autonomous_player/src/xar_autoplayer/")||!repositoryRelative.endsWith(".py")
                ||repositoryRelative.contains("\\")||repositoryRelative.contains(".."))throw new IOException("exact original Python repository target required");
        var matches=RootRuntimeDefinitions.configuredSources(inputs.configuration()).stream().filter(source->source.targetRelative().equals(repositoryRelative)).map(source->source.sourceRef()).distinct().toList();
        if(matches.size()!=1)throw new IOException("one configured original Python producer is required: "+repositoryRelative);
        ExactRef expected=matches.getFirst();return selected.original(new FileRef(expected.path(),expected.bytes(),expected.sha256()),RootRuntimeSelectedSources.OriginalKind.ORIGINAL_PYTHON);
    }
}
