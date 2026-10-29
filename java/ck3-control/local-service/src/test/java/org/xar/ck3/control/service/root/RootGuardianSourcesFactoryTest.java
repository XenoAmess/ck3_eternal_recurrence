package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ordinary.OrdinaryClaimDomain;
import org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;

/** Actual source refs feed the one real claims/Guardian Sources constructors; no historical seed or permit is invented. */
final class RootGuardianSourcesFactoryTest {
    @TempDir Path temporary;
    private static List<RootRuntimeDefinitionModel.SelectedSource> rows()throws Exception {
        var rows=new ArrayList<>(RootSourceHelperFiles.java(List.of(GuardianOutgoingInstaller.class,GuardianReconciliationQueries.class,
                GuardianOutgoingEffects.class,OrdinaryInitiationPreparation.class,OrdinaryPendingPublication.class,GuardianOutgoingCodec.class,InteractionCapabilities.class),NATIVE_TRANSPORT));
        rows.addAll(RootSourceHelperFiles.java(List.of(RootGuardianSourcesFactory.class,RootGuardianRuntimeFactory.class,
                RootGuardianReconciliationReads.class,RootOrdinaryClaimRuntime.class,RootOrdinaryClaimOriginals.class,RootArmySourcesFactory.class),LOCAL_SERVICE));
        rows.addAll(RootSourceHelperFiles.java(List.of(OrdinaryClaimDomain.class,OrdinaryOnceClaims.class),APPLICATION));
        return List.copyOf(rows);
    }
    private static RootOrdinaryClaimRuntime.Sources claimSources()throws Exception {
        ExactRef runtime=RootSourceHelperFiles.java(RootOrdinaryClaimRuntime.class,LOCAL_SERVICE).sourceRef();
        ExactRef original=RootSourceHelperFiles.java(RootOrdinaryClaimOriginals.class,LOCAL_SERVICE).sourceRef();
        ExactRef domain=RootSourceHelperFiles.java(OrdinaryClaimDomain.class,APPLICATION).sourceRef();
        ExactRef pure=RootSourceHelperFiles.java(OrdinaryOnceClaims.class,APPLICATION).sourceRef();
        ExactRef legacy=RootSourceHelperFiles.original("ck3_autonomous_player/src/xar_autoplayer/bridge/ordinary_interaction_contract.py");
        ExactRef release=RootSourceHelperFiles.original("ck3_autonomous_player/src/xar_autoplayer/bridge/ordinary_interaction_host_release.py");
        ExactRef constructor=RootSourceHelperFiles.java(RootArmySourcesFactory.class,LOCAL_SERVICE).sourceRef();
        return new RootOrdinaryClaimRuntime.Sources(runtime,original,domain,pure,legacy,release,List.of(runtime,original,domain,pure,legacy,release,constructor));
    }
    @Test void actualSourcesPreserveTheSameClaimProducerObjectAndEverySharedOrdinaryOriginal()throws Exception {
        var selected=new RootRuntimeSelectedSources(rows());var shared=claimSources();
        ExactRef ordinary=RootSourceHelperFiles.original("ck3_autonomous_player/native_bridge/src/bridge.cpp");
        ExactRef readDecoder=RootSourceHelperFiles.java(InteractionCapabilities.class,NATIVE_TRANSPORT).sourceRef();
        var sources=RootGuardianSourcesFactory.sources(temporary.resolve("actual-root.lock"),selected,shared,ordinary,readDecoder);
        assertSame(shared,sources.claims().sources());assertTrue(sources.completeProducers().containsAll(shared.completeProducers()));
        assertTrue(sources.completeProducers().containsAll(List.of(ordinary,readDecoder,sources.preparation(),sources.effects(),sources.decoder(),sources.reconciliationProfile())));
        for(ExactRef actual:sources.completeProducers())assertEquals(actual,ExactRef.fromJson(actual.toJson()));
        var prepared=new RootGuardianRuntimeFactory.Prepared(sources);assertSame(sources,prepared.sources());
        assertSame(sources.claims().registration(),prepared.domainRegistrations().getFirst());selected.requireCurrent();
    }
    @Test void missingActualGuardianCodecRejectsBeforeAClaimDefinitionCanBeInstalled()throws Exception {
        var missing=rows().stream().filter(row->!row.targetRelative().endsWith("/GuardianOutgoingCodec.java")).toList();
        var selected=new RootRuntimeSelectedSources(missing);var shared=claimSources();
        ExactRef ordinary=RootSourceHelperFiles.original("ck3_autonomous_player/native_bridge/src/bridge.cpp");
        ExactRef decoder=RootSourceHelperFiles.java(InteractionCapabilities.class,NATIVE_TRANSPORT).sourceRef();
        assertThrows(IOException.class,()->RootGuardianSourcesFactory.sources(temporary.resolve("missing-root.lock"),selected,shared,ordinary,decoder));
    }
    @Test void aReadableDifferentRuntimeCannotReplaceTheSharedActualClaimProducer()throws Exception {
        var selected=new RootRuntimeSelectedSources(rows());var shared=claimSources();
        ExactRef other=RootSourceHelperFiles.java(RootGuardianSourcesFactory.class,LOCAL_SERVICE).sourceRef();
        var complete=new ArrayList<>(shared.completeProducers());complete.add(other);
        var changed=new RootOrdinaryClaimRuntime.Sources(other,shared.originalProducer(),shared.domainReducer(),shared.pureClaimReducer(),
                shared.legacyClaimProducer(),shared.legacyHostRelease(),complete);
        ExactRef ordinary=RootSourceHelperFiles.original("ck3_autonomous_player/native_bridge/src/bridge.cpp");
        ExactRef decoder=RootSourceHelperFiles.java(InteractionCapabilities.class,NATIVE_TRANSPORT).sourceRef();
        assertThrows(IOException.class,()->RootGuardianSourcesFactory.sources(temporary.resolve("changed-root.lock"),selected,changed,ordinary,decoder));
    }
}
