package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ordinary.OrdinaryClaimDomain;
import org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.DataRole.*;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SourceRole.*;

/** Constructs one Guardian/ordinary-claim Prepared from the actual shared Army claim-source facts.
 * Source selection creates no historical claim seed, release permission, Core, Driver or Game qualification.
 */
public final class RootGuardianSourcesFactory {
    private RootGuardianSourcesFactory() { }
    public static RootGuardianRuntimeFactory.Prepared prepare(RootRuntimeDefinitions.Inputs inputs,
            RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals,
            RootRuntimeDomainSettings.Bound settings,RootOrdinaryClaimRuntime.Sources sameClaimSources)throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(selected);Objects.requireNonNull(originals);
        Objects.requireNonNull(settings);Objects.requireNonNull(sameClaimSources);
        if(!inputs.data(NATIVE_DOMAIN_ORIGINALS).equals(originals.original())
                ||!inputs.data(REMAINING_DOMAIN_SETTINGS).equals(settings.original())
                ||!inputs.application().machineId().equals(originals.configuration().machineId())
                ||!inputs.application().machineId().equals(settings.configuration().machineId()))
            throw new IOException("Guardian sources are not the identical configured Root originals/settings");
        for(var role:List.of(RootRuntimeNativeOriginals.Role.CLAIM_PRODUCER,RootRuntimeNativeOriginals.Role.CLAIM_HOST_RELEASE)) {
            var original=originals.configuration().source(role);ExactRef actual=selected.original(original.original(),role.kind());
            ExactRef expected=role==RootRuntimeNativeOriginals.Role.CLAIM_PRODUCER?sameClaimSources.legacyClaimProducer():sameClaimSources.legacyHostRelease();
            if(!actual.equals(expected))throw new IOException("shared ordinary claim sources changed their actual Python provenance");
        }
        var ordinaryPin=inputs.configuration().sources().stream().filter(value->value.role()==INTERACTION_ORDINARY).findFirst().orElseThrow();
        var ordinaryRef=ordinaryPin.selected().sourceRef();
        ExactRef ordinary=selected.original(new org.xar.ck3.control.build.ControlBuild.FileRef(
                ordinaryRef.path(),ordinaryRef.bytes(),ordinaryRef.sha256()),RootRuntimeSelectedSources.OriginalKind.NATIVE_CPP);
        var decoderPin=inputs.configuration().sources().stream().filter(value->value.role()==INTERACTION_READ_DECODER).findFirst().orElseThrow();
        ExactRef decoder=selected.javaTarget(decoderPin.selected().targetRelative());
        if(!ordinary.equals(inputs.source(INTERACTION_ORDINARY))||!decoder.equals(inputs.source(INTERACTION_READ_DECODER)))
            throw new IOException("Guardian did not retain the shared configured ordinary query/decoder originals");
        var sources=sources(inputs.application().ledger().lock(),selected,sameClaimSources,ordinary,decoder);
        selected.requireCurrent();return new RootGuardianRuntimeFactory.Prepared(sources);
    }
    /** Source-only constructor shared by prepare and regression. This creates one claims definition, never an import. */
    static RootGuardianRuntimeFactory.Sources sources(Path originalWriterLock,RootRuntimeSelectedSources selected,
            RootOrdinaryClaimRuntime.Sources sameClaimSources,ExactRef actualOrdinaryDefinition,ExactRef actualReadDecoder)throws IOException {
        Objects.requireNonNull(originalWriterLock);Objects.requireNonNull(selected);Objects.requireNonNull(sameClaimSources);
        Objects.requireNonNull(actualOrdinaryDefinition);Objects.requireNonNull(actualReadDecoder);
        if(!selected.javaSource(LOCAL_SERVICE,RootOrdinaryClaimRuntime.class).equals(sameClaimSources.runtime())
                ||!selected.javaSource(LOCAL_SERVICE,RootOrdinaryClaimOriginals.class).equals(sameClaimSources.originalProducer())
                ||!selected.javaSource(APPLICATION,OrdinaryClaimDomain.class).equals(sameClaimSources.domainReducer())
                ||!selected.javaSource(APPLICATION,OrdinaryOnceClaims.class).equals(sameClaimSources.pureClaimReducer()))
            throw new IOException("shared ordinary claim sources differ from the identical selected Java producers");
        var complete=new LinkedHashSet<ExactRef>(sameClaimSources.completeProducers());
        complete.add(selected.javaSource(LOCAL_SERVICE,RootGuardianSourcesFactory.class));
        complete.add(selected.javaSource(LOCAL_SERVICE,RootGuardianRuntimeFactory.class));
        complete.add(selected.javaSource(LOCAL_SERVICE,RootGuardianReconciliationReads.class));
        complete.add(selected.javaSource(NATIVE_TRANSPORT,GuardianOutgoingInstaller.class));
        complete.add(selected.javaSource(NATIVE_TRANSPORT,OrdinaryPendingPublication.class));
        ExactRef preparation=selected.javaSource(NATIVE_TRANSPORT,OrdinaryInitiationPreparation.class);
        ExactRef effects=selected.javaSource(NATIVE_TRANSPORT,GuardianOutgoingEffects.class);
        ExactRef decoder=selected.javaSource(NATIVE_TRANSPORT,GuardianOutgoingCodec.class);
        ExactRef profile=selected.javaSource(NATIVE_TRANSPORT,GuardianReconciliationQueries.class);
        complete.addAll(List.of(preparation,effects,decoder,profile,actualOrdinaryDefinition,actualReadDecoder));
        var claims=new RootOrdinaryClaimRuntime.Prepared(originalWriterLock,sameClaimSources);
        var result=new RootGuardianRuntimeFactory.Sources(claims,preparation,effects,decoder,profile,List.copyOf(complete));
        selected.requireCurrent();return result;
    }
}
