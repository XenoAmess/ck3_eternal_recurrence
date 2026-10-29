package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ordinary.OrdinaryClaimDomain;
import org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims;
import org.xar.ck3.control.application.effects.NativeArmyMoveEffects;
import org.xar.ck3.control.application.effects.NativeArmyOrdinaryEffects;
import org.xar.ck3.control.application.effects.NativeArmyWarWindowEffects;
import org.xar.ck3.control.application.effects.NativeWarExitEffects;
import org.xar.ck3.control.application.effects.HolyHirePoststate;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContextRead;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SelectedSource;
import org.xar.ck3.control.service.root.RootRuntimeNativeOriginals.Role;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;

/** Production source-fact constructors over real temporary Windows witnesses and the actual strict Original codec.
 * Controlled source text proves custody/typed routing only. It does not prove compiled-class/native-cut admission,
 * final Startup/Input/Army installation, claims import, private permission, Core, Ready or Game behavior.
 */
final class RootArmySourcesFactoryTest {
    @TempDir Path temporary;
    private record Fixture(Path root,Clock clock,List<SelectedSource> index,RootRuntimeSelectedSources selected,
            RootRuntimeNativeOriginals.Bound originals) { }
    private static String target(Module module,Class<?> type) {return module.directory()+"/src/main/java/"+type.getName().replace('.','/')+".java";}
    private static ExactRef exact(Path source)throws IOException {var ref=FileRef.measure(source);return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static void add(Path root,List<SelectedSource> rows,Module module,Class<?> type)throws IOException {
        Path file=root.resolve(type.getSimpleName()+".java");Files.writeString(file,"controlled source custody fixture for "+type.getName());
        rows.add(new SelectedSource(target(module,type),exact(file)));
    }
    private Fixture fixture(String name)throws IOException {
        assertTrue(com.sun.jna.Platform.isWindows(),"actual selected-source native identity tests require Windows");
        Path root=Files.createDirectory(temporary.resolve(name));var rows=new ArrayList<SelectedSource>();
        add(root,rows,NATIVE_TRANSPORT,ArmyOrdinaryActionPreparation.class);add(root,rows,APPLICATION,ArmyOrdinaryActionArguments.class);
        add(root,rows,NATIVE_TRANSPORT,ArmyOrdinaryActionService.class);add(root,rows,LOCAL_SERVICE,RootArmyOrdinaryRuntimeInputs.class);
        add(root,rows,APPLICATION,NativeArmyOrdinaryEffects.class);add(root,rows,APPLICATION,NativeArmyMoveEffects.class);
        add(root,rows,APPLICATION,NativeWarExitEffects.class);add(root,rows,APPLICATION,NativeArmyWarWindowEffects.class);
        add(root,rows,NATIVE_TRANSPORT,PlayerHolyOrderContextRead.class);add(root,rows,LOCAL_SERVICE,RootOrdinaryClaimRuntime.class);
        add(root,rows,APPLICATION,HolyHirePoststate.class);add(root,rows,LOCAL_SERVICE,RootHolyHirePoststate.class);
        add(root,rows,LOCAL_SERVICE,RootOrdinaryClaimOriginals.class);add(root,rows,APPLICATION,OrdinaryClaimDomain.class);
        add(root,rows,APPLICATION,OrdinaryOnceClaims.class);add(root,rows,LOCAL_SERVICE,RootArmySourcesFactory.class);
        add(root,rows,LOCAL_SERVICE,RootRuntimeDomainSettings.class);
        add(root,rows,APPLICATION,ArmyWarSupplementalReads.class);add(root,rows,APPLICATION,ArmyWarSupplementalReadCodec.class);
        var originalRows=new ArrayList<RootRuntimeNativeOriginals.Original>();
        for(var role:Role.values()){
            Path file=root.resolve(Path.of(role.repositoryRelative()).getFileName());Files.writeString(file,"controlled provenance fixture for "+role);
            originalRows.add(new RootRuntimeNativeOriginals.Original(role,role.repositoryRelative(),FileRef.measure(file)));
        }
        Instant now=Instant.now();Clock clock=Clock.fixed(now,ZoneOffset.UTC);
        var configuration=new RootRuntimeNativeOriginals.Configuration(RootRuntimeNativeOriginals.SCHEMA,WindowsJobProcess.currentMachineId(),
                now.minusSeconds(1).toString(),now.plusSeconds(3600).toString(),originalRows);
        Path document=root.resolve("native-originals.json");Files.write(document,RootRuntimeNativeOriginals.encode(configuration));
        return new Fixture(root,clock,List.copyOf(rows),new RootRuntimeSelectedSources(rows),RootRuntimeNativeOriginals.readExact(FileRef.measure(document),clock));
    }
    @Test void actualJavaAndTypedOriginalWitnessesReachTheOrdinaryAndClaimConsumers()throws IOException {
        var f=fixture("typed-consumers");var ordinary=RootArmySourcesFactory.ordinarySources(f.selected(),f.originals());
        assertEquals(f.selected().javaSource(NATIVE_TRANSPORT,ArmyOrdinaryActionPreparation.class),ordinary.actions().producer());
        assertEquals(f.selected().javaSource(APPLICATION,ArmyOrdinaryActionArguments.class),ordinary.actions().decoder());
        assertEquals(f.selected().javaSource(NATIVE_TRANSPORT,ArmyOrdinaryActionService.class),ordinary.actions().service());
        assertEquals(f.originals().source(Role.REGULAR_MAA_PRODUCER),ordinary.regularMaa().pythonProducer());
        assertEquals(f.originals().source(Role.REGULAR_MAA_MAILBOX),ordinary.regularMaa().nativeMailbox());
        assertEquals(f.originals().source(Role.REGULAR_MAA_CREATE),ordinary.regularMaa().nativeCreate());
        assertEquals(f.originals().source(Role.REGULAR_MAA_BUILD4_BINDING),ordinary.regularMaa().nativeBuild4Binding());
        assertEquals(8,ordinary.holyOrders().all().size());assertEquals(f.originals().source(Role.HOLY_BUILD4_BINDING),ordinary.holyOrders().nativeBuild4Binding());
        var claims=RootArmySourcesFactory.claimSources(f.selected(),f.originals());
        assertEquals(f.originals().source(Role.CLAIM_PRODUCER),claims.legacyClaimProducer());
        assertEquals(f.originals().source(Role.CLAIM_HOST_RELEASE),claims.legacyHostRelease());
        assertEquals(7,claims.completeProducers().size());assertEquals(7,claims.completeProducers().stream().distinct().count());
        f.originals().requireCurrent(f.clock());f.selected().requireCurrent();
    }
    @Test void strictOriginalProducerSerializationRoundTripPreservesEveryTypedSourceConsumer()throws IOException {
        var f=fixture("source-serde");byte[] raw=RootRuntimeNativeOriginals.encode(f.originals().configuration());
        var decoded=RootRuntimeNativeOriginals.decode(raw);assertEquals(f.originals().configuration(),decoded);
        Path copy=f.root().resolve("roundtrip-native-originals.json");Files.write(copy,RootRuntimeNativeOriginals.encode(decoded));
        var replay=RootRuntimeNativeOriginals.readExact(FileRef.measure(copy),f.clock());
        assertEquals(RootArmySourcesFactory.ordinarySources(f.selected(),f.originals()),RootArmySourcesFactory.ordinarySources(f.selected(),replay));
        assertEquals(RootArmySourcesFactory.claimSources(f.selected(),f.originals()),RootArmySourcesFactory.claimSources(f.selected(),replay));
    }
    @Test void supplementalNativeProducerRoundTripReachesBothActualConsumerFields()throws IOException {
        var f=fixture("supplemental-serde");
        var sources=RootArmySourcesFactory.supplementalSources(f.selected(),f.originals(),Optional.empty());
        assertEquals("ck3_autonomous_player/native_bridge/src/ck3_11906.cpp",Role.ARMY_SUPPLEMENTAL_WAR_NATIVE.repositoryRelative());
        assertEquals(RootRuntimeSelectedSources.OriginalKind.NATIVE_CPP,Role.ARMY_SUPPLEMENTAL_WAR_NATIVE.kind());
        assertEquals(f.selected().javaSource(APPLICATION,ArmyWarSupplementalReads.class),sources.definition());
        assertEquals(f.selected().javaSource(APPLICATION,ArmyWarSupplementalReadCodec.class),sources.decoder());
        assertEquals(f.originals().source(Role.ARMY_SUPPLEMENTAL_WAR_NATIVE),sources.provinceNative());
        assertEquals(f.originals().source(Role.ARMY_SUPPLEMENTAL_WAR_NATIVE),sources.deJureNative());
        assertTrue(sources.stockSources().isEmpty());
        var decoded=RootRuntimeNativeOriginals.decode(RootRuntimeNativeOriginals.encode(f.originals().configuration()));
        Path copy=f.root().resolve("supplemental-originals.json");Files.write(copy,RootRuntimeNativeOriginals.encode(decoded));
        var replay=RootRuntimeNativeOriginals.readExact(FileRef.measure(copy),f.clock());
        assertEquals(sources,RootArmySourcesFactory.supplementalSources(f.selected(),replay,Optional.empty()));
    }
    @Test void supplementalRoleIsMandatoryAndCannotBorrowTheDispatcherOrTheOldSchema()throws IOException {
        var f=fixture("supplemental-required");var config=f.originals().configuration();
        var missing=config.originals().stream().filter(row->row.role()!=Role.ARMY_SUPPLEMENTAL_WAR_NATIVE).toList();
        assertThrows(IllegalArgumentException.class,()->new RootRuntimeNativeOriginals.Configuration(config.schema(),config.machineId(),
                config.observedAtUtc(),config.reviewAtUtc(),missing));
        assertThrows(IllegalArgumentException.class,()->new RootRuntimeNativeOriginals.Configuration("xar.java-root-native-originals/v6",config.machineId(),
                config.observedAtUtc(),config.reviewAtUtc(),config.originals()));
        byte[] oldWire=new String(RootRuntimeNativeOriginals.encode(config),java.nio.charset.StandardCharsets.UTF_8)
                .replace(RootRuntimeNativeOriginals.SCHEMA,"xar.java-root-native-originals/v6").getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IOException.class,()->RootRuntimeNativeOriginals.decode(oldWire));
        var dispatcher=config.source(Role.NATIVE_DISPATCHER);
        assertThrows(IllegalArgumentException.class,()->new RootRuntimeNativeOriginals.Original(Role.ARMY_SUPPLEMENTAL_WAR_NATIVE,
                Role.ARMY_SUPPLEMENTAL_WAR_NATIVE.repositoryRelative(),dispatcher.original()));
        assertThrows(IllegalArgumentException.class,()->new RootRuntimeNativeOriginals.Original(Role.ARMY_SUPPLEMENTAL_WAR_NATIVE,
                dispatcher.repositoryRelative(),config.source(Role.ARMY_SUPPLEMENTAL_WAR_NATIVE).original()));
    }
    @Test void nativeOriginalDriftRemainsRejectedWhileHistoricalJavaDecoderMetadataStaysStable()throws IOException {
        var f=fixture("supplemental-native-drift");var nativeBefore=RootArmySourcesFactory.supplementalSources(f.selected(),f.originals(),Optional.empty());
        replace(Path.of(f.originals().source(Role.ARMY_SUPPLEMENTAL_WAR_NATIVE).path()));
        assertEquals(nativeBefore,RootArmySourcesFactory.supplementalSources(f.selected(),f.originals(),Optional.empty()));
        assertThrows(IOException.class,()->f.originals().requireCurrent(f.clock()));
        var decoder=fixture("supplemental-decoder-drift");
        var before=RootArmySourcesFactory.supplementalSources(decoder.selected(),decoder.originals(),Optional.empty());
        Path javaFile=decoder.root().resolve("ArmyWarSupplementalReadCodec.java");replace(javaFile);
        assertEquals(before,RootArmySourcesFactory.supplementalSources(decoder.selected(),decoder.originals(),Optional.empty()));
        Files.delete(javaFile);decoder.selected().requireCurrent();
        assertEquals(before,RootArmySourcesFactory.supplementalSources(decoder.selected(),decoder.originals(),Optional.empty()));
    }
    @Test void javaHistoryRetainsItsRefsWhileMaaOriginalReplacementStillRejects()throws IOException {
        var java=fixture("java-identity");var before=RootArmySourcesFactory.ordinarySources(java.selected(),java.originals());
        Path javaFile=java.root().resolve("ArmyOrdinaryActionPreparation.java");replace(javaFile);
        assertEquals(before,RootArmySourcesFactory.ordinarySources(java.selected(),java.originals()));
        Files.delete(javaFile);java.selected().requireCurrent();
        assertEquals(before,RootArmySourcesFactory.ordinarySources(java.selected(),java.originals()));
        var nativeOriginal=fixture("maa-identity");var nativeBefore=RootArmySourcesFactory.ordinarySources(nativeOriginal.selected(),nativeOriginal.originals());
        replace(Path.of(nativeOriginal.originals().source(Role.REGULAR_MAA_CREATE).path()));
        assertEquals(nativeBefore,RootArmySourcesFactory.ordinarySources(nativeOriginal.selected(),nativeOriginal.originals()));
        assertThrows(IOException.class,()->nativeOriginal.originals().requireCurrent(nativeOriginal.clock()));
    }
    @Test void claimProducerClosureDoesNotDependOnOtherStartupHelpersConsumptionOrder()throws IOException {
        var f=fixture("fixed-closure");var before=RootArmySourcesFactory.claimSources(f.selected(),f.originals());
        f.selected().javaSource(LOCAL_SERVICE,RootRuntimeDomainSettings.class);
        RootArmySourcesFactory.ordinarySources(f.selected(),f.originals());
        assertEquals(before,RootArmySourcesFactory.claimSources(f.selected(),f.originals()));
        assertFalse(before.completeProducers().contains(f.selected().javaSource(LOCAL_SERVICE,RootRuntimeDomainSettings.class)));
    }
    @Test void missingJavaWinnerStillRejectsWhileHistoricalDecoderFileChangesKeepTheirOriginalRef()throws IOException {
        var f=fixture("missing-winner");var rows=f.index().stream().filter(row->!row.targetRelative().equals(target(NATIVE_TRANSPORT,ArmyOrdinaryActionService.class))).toList();
        var selected=new RootRuntimeSelectedSources(rows);
        assertThrows(IOException.class,()->RootArmySourcesFactory.ordinarySources(selected,f.originals()));
        var changed=fixture("changed-winner");var before=RootArmySourcesFactory.ordinarySources(changed.selected(),changed.originals());
        Files.writeString(changed.root().resolve("ArmyOrdinaryActionArguments.java"),"different historical decoder source DATA");
        assertEquals(before,RootArmySourcesFactory.ordinarySources(changed.selected(),changed.originals()));
    }
    private static void replace(Path source)throws IOException {
        Path replacement=source.resolveSibling("replacement-"+source.getFileName());Files.copy(source,replacement);Files.setLastModifiedTime(replacement,Files.getLastModifiedTime(source));
        Files.move(replacement,source,StandardCopyOption.REPLACE_EXISTING);
    }
}
