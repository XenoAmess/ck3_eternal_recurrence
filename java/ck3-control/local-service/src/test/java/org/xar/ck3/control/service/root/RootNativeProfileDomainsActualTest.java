package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.NativeRunProfileManifest;
import org.xar.ck3.control.build.NativeRunProfileProducer;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture;
import org.xar.ck3.control.platform.NativeBridgeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;

/** Mandatory actual source-bound producer inputs; absent inputs fail, and no software adapter grants qualification. */
public final class RootNativeProfileDomainsActualTest {
    @TempDir Path output;
    public record Case(FileRef requestSource,NativeLaunchPlanCodec.Configuration launch,
            List<FileRef> lateInputs,Optional<PreparedFixture> identicalFixture) {
        public Case {lateInputs=List.copyOf(lateInputs);java.util.Objects.requireNonNull(identicalFixture);}
    }
    public interface InputsProducer {List<Case> produce(Path ownedOutput)throws Exception;}
    private List<Case> actualCases()throws Exception {
        String name=System.getProperty("xar.test.nativeProfileDomainsInputsProducer");
        assertNotNull(name,"Mandatory genuine qualified-tools/native-source profile inputs are unavailable; do not skip");
        Class<?> type=Class.forName(name);
        assertTrue(InputsProducer.class.isAssignableFrom(type),"Actual typed input producer required");
        var cases=List.copyOf(((InputsProducer)type.getDeclaredConstructor().newInstance()).produce(output.resolve("inputs")));
        assertEquals(3,cases.size(),"Actual vanilla, product-only and fresh frontend fixture inputs required");
        return cases;
    }
    private record Produced(Case inputs,FileRef environment,NativeRunProfileManifest.ExplicitManifest actual,
            NativeLaunchPlan.PreparedProfile prepared,NativeLaunchPlanCodec.Configuration launch) { }
    private Produced produce(Case row,Path directory)throws Exception {
        Files.createDirectories(directory);
        var request=NativeRunProfileProducer.readExplicitRequest(row.requestSource());
        var privatePrepared=request.source() instanceof NativeRunProfileManifest.SavedSource
                ?NativeRunProfileProducer.prepareSaved(request,Clock.systemUTC())
                :NativeRunProfileProducer.prepareFixture(request,Clock.systemUTC());
        var actual=NativeRunProfileProducer.finishExplicit(privatePrepared,Clock.systemUTC());
        byte[] bytes=NativeRunProfileManifest.encodeEnvironment(actual);
        Path file=directory.resolve("ENV.json");Files.write(file,bytes,StandardOpenOption.CREATE_NEW);
        FileRef exact=FileRef.measure(file);var held=SharedSourceFiles.observe(file);
        assertEquals(actual,NativeRunProfileProducer.readEnvironmentVerified(exact));
        var prepared=RootNativeLaunchPlanInputs.preparedProfile(exact,row.lateInputs());
        var launch=withPrepared(row.launch(),prepared);
        byte[] encoded=RootNativeLaunchPlanInputs.encodeConfiguration(launch);
        Path plan=directory.resolve("native-launch-plan.json");Files.write(plan,encoded,StandardOpenOption.CREATE_NEW);
        assertEquals(launch,NativeLaunchPlanCodec.fromJson(StrictJson.parse(Files.readAllBytes(plan),NativeLaunchPlanCodec.MAXIMUM_BYTES)));
        SharedSourceFiles.assertUnchanged(held);
        return new Produced(row,exact,actual,prepared,launch);
    }
    @Test void actualPublicProducerAndAllLaunchConsumersPersistEachExplicitDomainWithoutStartingAProcess()throws Exception {
        var kinds=new java.util.HashSet<NativeRunProfileManifest.ProfileKind>();int index=0;
        for(var row:actualCases()) {
            var built=produce(row,output.resolve("case-"+index++));
            kinds.add(built.actual().kind());
            assertEquals(built.actual().kind(),built.prepared().kind());
            assertEquals(built.actual().productionRoots().stream().map(Path::of).toList(),built.prepared().productionRoots());
            assertTrue(built.prepared().preparedInputs().containsAll(row.lateInputs()));
            assertTrue(built.prepared().preparedInputs().containsAll(built.actual().requiredPreparedFileRefs()));
            assertEquals(built.prepared(),RootNativeLaunchPlanInputs.preparedProfile(built.environment(),built.prepared().preparedInputs()));
            var accepted=built.launch().accept(new NativeBridgeLaunchEvidence());built.prepared().verify(accepted);
            if(built.actual().kind()==NativeRunProfileManifest.ProfileKind.FRESH_FRONTEND_FIXTURE)
                row.identicalFixture().orElseThrow().requireEnvironment(built.actual());
            else assertTrue(row.identicalFixture().isEmpty());
            if(built.actual().kind()==NativeRunProfileManifest.ProfileKind.SAVED_VANILLA)assertTrue(built.prepared().productionRoots().isEmpty());
        }
        assertEquals(Set.of(NativeRunProfileManifest.ProfileKind.SAVED_VANILLA,NativeRunProfileManifest.ProfileKind.SAVED_PRODUCT_ONLY,
                NativeRunProfileManifest.ProfileKind.FRESH_FRONTEND_FIXTURE),kinds);
    }
    @Test void actualChangedLateOriginalFailsTheSamePhysicalConsumer()throws Exception {
        var rows=actualCases();var row=rows.stream().filter(value->!value.lateInputs().isEmpty()).findFirst().orElseThrow();
        var built=produce(row,output.resolve("mutation"));var late=row.lateInputs().getFirst();
        assertTrue(built.prepared().preparedInputs().contains(late));
        Path original=Path.of(late.path());assertTrue(original.toRealPath().startsWith(output.toRealPath()),"Mutation regression inputs must be owned temporary originals");
        Files.writeString(original,"changed owned regression original");
        assertThrows(Exception.class,()->RootNativeLaunchPlanInputs.preparedProfile(built.environment(),row.lateInputs()),
                "The actual late input FileRef must still match its independently retained bytes and SHA");
    }
    private static NativeLaunchPlanCodec.Configuration withPrepared(NativeLaunchPlanCodec.Configuration old,NativeLaunchPlan.PreparedProfile profile) {
        return new NativeLaunchPlanCodec.Configuration(old.requestId(),old.sessionId(),old.review(),old.profileDirectory(),old.stateDirectory(),old.evidenceRoot(),
                old.pipeName(),old.bridgeVersion(),old.adapterId(),old.load(),old.debugMode(),old.windowPolicy(),old.environment(),old.gameMemoryBytes(),old.injectorMemoryBytes(),
                old.deadline(),old.injectorTimeout(),old.startupTimeout(),old.steam(),profile,old.maximumEvidenceRows());
    }
}

