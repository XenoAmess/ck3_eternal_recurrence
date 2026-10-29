package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.lifecycle.LifecycleComposites;
import org.xar.ck3.control.application.planning.family.FamilyDomainSource;
import org.xar.ck3.control.application.planning.family.FamilyNaturalEpisodeMigration;
import org.xar.ck3.control.application.planning.family.FamilyOrdinaryRestoreMigration;
import org.xar.ck3.control.application.planning.family.FamilyNextEpisodeMigration;
import org.xar.ck3.control.application.planning.family.FamilyOrdinaryPolicy;
import org.xar.ck3.control.application.planning.family.FamilyPendingStore;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocusEffects;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocusQueries;
import org.xar.ck3.control.nativebridge.capabilities.family.FamilyObligationsCodec;
import org.xar.ck3.control.nativebridge.capabilities.family.EpidemicTreatmentPresenceQueries;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;

/** Pre-Core source wiring only. Actual cut, file identity, domain import, permissions and Game qualification remain separate. */
public final class RootNativeFamilySourcesFactory {
    private RootNativeFamilySourcesFactory(){ }
    /** Full original documents, explicitly named by their real domain slot; historical SDK names are not aliases. */
    public record OriginalDocuments(ExactRef family,ExactRef childMatrilineal,ExactRef defaultMarriage) {
        public OriginalDocuments {
            for(var source:List.of(family,childMatrilineal,defaultMarriage))
                StrictJson.require(source.bytes()>0,"three actual full original family domain documents required");
        }
        public Map<DomainBodies.Slot,ExactRef> selected(){return Map.of(
                DomainBodies.Slot.FAMILY,family,DomainBodies.Slot.CHILD_MATRILINEAL,childMatrilineal,
                DomainBodies.Slot.DEFAULT_MARRIAGE,defaultMarriage);}
    }
    public static RootFamilyRuntimeFactory.Prepared prepare(RootRuntimeDefinitions.Inputs inputs,
            RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound nativeOriginals,
            RootRuntimeDomainSettings.Bound actualSettings,OriginalDocuments originals)throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(selected);Objects.requireNonNull(nativeOriginals);
        Objects.requireNonNull(actualSettings);Objects.requireNonNull(originals);
        StrictJson.require(inputs.configuration().machineId().equals(nativeOriginals.configuration().machineId())
                &&inputs.configuration().machineId().equals(actualSettings.configuration().machineId()),
                "Family sources and settings must belong to the same explicit runtime machine");
        selected.requireCurrent();
        var named=new ArrayList<ExactRef>();
        source(selected,LOCAL_SERVICE,RootNativeFamilySourcesFactory.class,named);
        // The natural producer, its canonical consumer and the real installation/publication callers
        // must be exact selected witnesses in the same registered Family replay closure.
        source(selected,APPLICATION,FamilyNaturalEpisodeMigration.class,named);
        source(selected,APPLICATION,FamilyNextEpisodeMigration.class,named);
        source(selected,APPLICATION,FamilyOrdinaryRestoreMigration.class,named);
        source(selected,APPLICATION,FamilyDomainSource.class,named);
        source(selected,APPLICATION,LifecycleComposites.class,named);
        source(selected,LOCAL_SERVICE,RootFamilyOriginalDomains.class,named);
        source(selected,LOCAL_SERVICE,RootFamilyOrdinaryRestoreDomains.class,named);
        source(selected,LOCAL_SERVICE,FamilyRuntimeInstaller.class,named);
        source(selected,LOCAL_SERVICE,RootFamilyRuntimeFactory.class,named);
        source(selected,LOCAL_SERVICE,RootRuntimeDomainAssembly.class,named);
        ExactRef nativeEntry=nativeOriginals.source(RootRuntimeNativeOriginals.Role.NATIVE_DISPATCHER);named.add(nativeEntry);
        ExactRef ordinary=source(selected,APPLICATION,FamilyOrdinaryPolicy.class,named);
        ExactRef pending=selected.javaSourceAt("local-service/src/main/java/org/xar/ck3/control/application/planning/family/FamilyPendingStore.java",FamilyPendingStore.class);named.add(pending);
        ExactRef obligations=source(selected,NATIVE_TRANSPORT,FamilyObligationsCodec.class,named);
        ExactRef focusDecoder=source(selected,NATIVE_TRANSPORT,ChildEducationFocus.class,named);
        var reads=new RootFamilyReadProducts.Sources(nativeEntry,obligations,nativeEntry,focusDecoder);
        var nativeReads=new RootFamilyNativeReadProducts.Sources(
                leaf(selected,nativeEntry,FamilyCurrentRelation.class,named),
                leaf(selected,nativeEntry,FamilyMarriageProjectionQueries.class,named),
                leaf(selected,nativeEntry,FamilyChildMarriageSubject.class,named),
                leaf(selected,nativeEntry,FamilyChildMarriageQueries.class,named),
                leaf(selected,nativeEntry,FamilyMarriageResults.class,named),
                leaf(selected,nativeEntry,FamilyMarriageResults.class,named),
                leaf(selected,nativeEntry,FamilyMarriageAlliance.class,named),
                leaf(selected,nativeEntry,FamilyMarriageAlliance.class,named),
                leaf(selected,nativeEntry,FamilyMarriageAlliance.class,named));
        ExactRef outgoing=source(selected,NATIVE_TRANSPORT,FamilyOutgoingCodec.class,named);
        ExactRef preparation=source(selected,NATIVE_TRANSPORT,FamilyMarriageNativeRequests.class,named);
        ExactRef fresh=source(selected,LOCAL_SERVICE,RootFamilyMarriageFreshPreparation.class,named);
        ExactRef effects=source(selected,NATIVE_TRANSPORT,MarriageSendEffects.class,named);
        ExactRef replay=source(selected,LOCAL_SERVICE,RootFamilyMarriageSendRuntime.class,named);
        var configured=inputs.configuration().family();
        boolean focusEnabled=configured.familyEnabled()&&configured.childFocusEnabled();
        Optional<FocusSources> focus;
        if(focusEnabled)focus=Optional.of(new FocusSources(
                source(selected,LOCAL_SERVICE,RootChildEducationFocusRuntime.class,named),
                source(selected,NATIVE_TRANSPORT,ChildEducationFocusEffects.class,named),focusDecoder,
                source(selected,NATIVE_TRANSPORT,ChildEducationFocusQueries.class,named)));
        else focus=Optional.empty();
        ExactRef treatmentDecoder=source(selected,NATIVE_TRANSPORT,EpidemicTreatmentPresenceQueries.class,named);
        source(selected,LOCAL_SERVICE,RootEpidemicTreatmentRead.class,named);
        List<ExactRef> closure=completeClosure(inputs,selected);
        StrictJson.require(closure.containsAll(named),"configured Family closure omits an actual named native/decoder/preparation/replay producer");
        var marriages=new RootFamilyMarriageSendRuntime.Sources(nativeEntry,outgoing,preparation,fresh,effects,outgoing,replay,closure);
        var submissions=new FamilyNativePrivatePermissions.Sources(nativeEntry,nativeEntry,nativeEntry,nativeEntry);
        var childFocus=focus.map(value->new RootChildEducationFocusRuntime.Sources(
                value.preparation(),value.effects(),value.decoder(),value.profile(),closure));
        var sources=new RootFamilyRuntimeFactory.Sources(new FamilyRuntimeInstaller.Sources(ordinary,pending,reads,closure),
                nativeReads,marriages,submissions,childFocus,new RootEpidemicTreatmentRead.Sources(nativeEntry,treatmentDecoder,treatmentClosure(inputs,closure)));
        var pair=Optional.ofNullable(configured.matrilinealPair()).map(value->new FamilyPorts.Pair(
                BigInteger.valueOf(value.subjectCharacterId()),BigInteger.valueOf(value.candidateCharacterId())));
        var settings=new FamilyPorts.Settings(configured.familyEnabled(),configured.fulfillCurrentBetrothal(),
                configured.childFocusEnabled(),configured.childDefaultEnabled(),pair);
        selected.requireCurrent();
        return new RootFamilyRuntimeFactory.Prepared(inputs.application().ledger().lock(),originals.selected(),sources,settings,
                Path.of(actualSettings.configuration().familyRelationExportRoot()));
    }
    /** Exact configured witnesses for the independent read; no filename scan or focus permission alias. */
    private static List<ExactRef> treatmentClosure(RootRuntimeDefinitions.Inputs inputs,List<ExactRef> verifiedFamily)throws IOException {
        String base="ck3_autonomous_player/native_bridge/";
        var required=List.of(base+"src/bridge.cpp",base+"src/player_epidemic_treatment_presence_v1.cpp",
                base+"src/player_epidemic_treatment_presence_v1_mailbox.cpp",base+"include/xar_bridge/player_epidemic_treatment_presence_v1.hpp",
                base+"src/ck3_12002_epidemic_treatment_presence.cpp",base+"include/xar_bridge/ck3_12002_epidemic_treatment_presence.hpp",
                "native-transport/src/main/java/org/xar/ck3/control/nativebridge/capabilities/family/EpidemicTreatmentPresenceQueries.java",
                "local-service/src/main/java/org/xar/ck3/control/service/root/RootEpidemicTreatmentRead.java");
        var groups=inputs.configuration().closures().stream().filter(value->value.role()==RootRuntimeDefinitionModel.ClosureRole.FAMILY).toList();
        StrictJson.require(groups.size()==1,"one actual configured Family source witness group required");var result=new ArrayList<ExactRef>();
        for(String target:required){var matches=groups.getFirst().sources().stream().filter(value->value.targetRelative().equals(target)).toList();
            if(matches.size()!=1||!verifiedFamily.contains(matches.getFirst().sourceRef()))throw new IOException("independent treatment read lacks its exact verified producer: "+target);
            result.add(matches.getFirst().sourceRef());}
        return List.copyOf(result);
    }
    private record FocusSources(ExactRef preparation,ExactRef effects,ExactRef decoder,ExactRef profile){ }
    private static ExactRef source(RootRuntimeSelectedSources selected,RootRuntimeSelectedSources.Module module,
            Class<?> actual,List<ExactRef> named)throws IOException {
        ExactRef original=selected.javaSource(module,actual);named.add(original);return original;
    }
    private static RootFamilyNativeReadProducts.Source leaf(RootRuntimeSelectedSources selected,ExactRef nativeEntry,
            Class<?> actualDecoder,List<ExactRef> named)throws IOException {
        return new RootFamilyNativeReadProducts.Source(nativeEntry,source(selected,NATIVE_TRANSPORT,actualDecoder,named));
    }
    /** Retains the actual complete configured closure; missing named leaves are rejected rather than repaired or truncated. */
    private static List<ExactRef> completeClosure(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected)throws IOException {
        var configured=inputs.configuration().closures().stream()
                .filter(value->value.role()==RootRuntimeDefinitionModel.ClosureRole.FAMILY).toList();
        StrictJson.require(configured.size()==1,"one actual complete configured Family source closure required");
        var complete=new LinkedHashSet<ExactRef>();
        for(var source:configured.getFirst().sources()) {
            String target=source.targetRelative();ExactRef expected=source.sourceRef(),actual;
            if(target.endsWith(".java"))actual=selected.javaTarget(target);
            else {
                var kind=target.endsWith(".cpp")?RootRuntimeSelectedSources.OriginalKind.NATIVE_CPP:
                        target.endsWith(".hpp")?RootRuntimeSelectedSources.OriginalKind.NATIVE_HEADER:
                        target.endsWith(".py")?RootRuntimeSelectedSources.OriginalKind.ORIGINAL_PYTHON:
                        target.endsWith(".txt")?RootRuntimeSelectedSources.OriginalKind.STOCK_SCRIPT:null;
                if(kind==null)throw new IOException("unsupported actual Family producer source kind: "+target);
                actual=selected.original(new FileRef(expected.path(),expected.bytes(),expected.sha256()),kind);
            }
            StrictJson.require(actual.equals(expected)&&complete.add(actual),"Family closure source differs from its sole winner or repeats an exact original");
        }
        StrictJson.require(!complete.isEmpty()&&complete.size()<=64,"complete unique Family producer closure exceeds its actual contract bound");
        return List.copyOf(complete);
    }
}
