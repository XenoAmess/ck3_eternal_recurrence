package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaVfs;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings;

/** Real settings and sole codec documents; historical normal-exit/war refs grant no Native or Game permission. */
class RootRuntimeDomainSettingsSourceHistoryTest {
    @TempDir Path root;
    private static final Instant AT=Instant.parse("2026-10-29T12:00:00Z");
    private static final Clock CLOCK=Clock.fixed(AT,ZoneOffset.UTC);

    @Test void missingHistoricalPolicyRequestAndProducerFilesDoNotBlockSettingsData()throws Exception {
        var f=fixture(root,WindowsJobProcess.currentMachineId());
        for(FileRef ref:f.history())Files.delete(Path.of(ref.path()));
        var bound=RootRuntimeDomainSettings.readExact(f.original(),CLOCK);
        assertEquals(f.configuration(),bound.configuration());
        assertTrue(bound.retainedOriginals().containsAll(f.history()));
        assertEquals(10,bound.retainedOriginals().size());
        assertEquals(new CoaVfs.Limits(65536,32768),bound.configuration().coaReadLimits().limits());
        assertThrows(UnsupportedOperationException.class,()->bound.retainedOriginals().clear());
    }
    @Test void retainedDataSurvivesDeletedInputsAndExpiredHistoricalReview()throws Exception {
        var f=fixture(root,WindowsJobProcess.currentMachineId());
        var bound=RootRuntimeDomainSettings.readExact(f.original(),CLOCK);
        var refs=bound.retainedOriginals();
        for(FileRef ref:refs)Files.delete(Path.of(ref.path()));
        bound.requireCurrent(Clock.fixed(AT.plus(Duration.ofDays(2)),ZoneOffset.UTC));
        assertEquals(f.configuration(),bound.configuration());assertEquals(refs,bound.retainedOriginals());
        assertEquals(f.original(),bound.original());
    }
    @Test void historicalReviewTimesDoNotQualifyInitialSettingsRead()throws Exception {
        var f=fixture(root,WindowsJobProcess.currentMachineId());
        assertEquals(f.configuration(),RootRuntimeDomainSettings.readExact(f.original(),
                Clock.fixed(AT.plus(Duration.ofDays(2)),ZoneOffset.UTC)).configuration());
        assertEquals(f.configuration(),RootRuntimeDomainSettings.readExact(f.original(),
                Clock.fixed(AT.minus(Duration.ofDays(2)),ZoneOffset.UTC)).configuration());
    }
    @Test void requiredCoaAndQueryDocumentContentStillUsesItsActualCodec()throws Exception {
        var coa=fixture(root.resolve("coa"),WindowsJobProcess.currentMachineId());
        Path coaPath=Path.of(coa.configuration().coaReadLimits().original().path());Files.writeString(coaPath,"{");
        var badCoa=withRequired(coa.configuration(),FileRef.measure(coaPath),coa.configuration().queryHistorySettings());
        FileRef badCoaSettings=write(root.resolve("bad-coa-settings.json"),RootRuntimeDomainSettings.encode(badCoa));
        assertThrows(IllegalArgumentException.class,()->RootRuntimeDomainSettings.readExact(badCoaSettings,CLOCK));
        var query=fixture(root.resolve("query"),WindowsJobProcess.currentMachineId());
        Path queryPath=Path.of(query.configuration().queryHistorySettings().path());Files.writeString(queryPath,"{");
        var badQuery=withRequired(query.configuration(),query.configuration().coaReadLimits().original(),exact(FileRef.measure(queryPath)));
        FileRef badQuerySettings=write(root.resolve("bad-query-settings.json"),RootRuntimeDomainSettings.encode(badQuery));
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.readExact(badQuerySettings,CLOCK));
    }
    @Test void queryRequestMachineMustAgreeWithTheActualSettingsMachine()throws Exception {
        var f=fixture(root,"foreign-machine");
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.readExact(f.original(),CLOCK));
    }
    @Test void conflictingHistoricalRefsStillRejectAsAnAmbiguousMetadataContract()throws Exception {
        var f=fixture(root,WindowsJobProcess.currentMachineId());var c=f.configuration();
        var actual=c.normalExit().inventory();
        FileRef conflict=new FileRef(actual.path(),actual.bytes()+1,actual.sha256());
        var changed=new RootRuntimeDomainSettings.Configuration(c.schema(),c.machineId(),c.observedAtUtc(),c.reviewAtUtc(),
                c.lifecycle(),c.familyRelationExportRoot(),
                new RootRuntimeDomainSettings.FormalWar(conflict,c.formalWar().defaultModel(),null,null),
                c.peacetime(),c.offline(),c.normalExit(),c.coaReadLimits(),c.queryHistorySettings(),c.planFlags(),c.stockRead());
        FileRef source=write(root.resolve("conflicting-settings.json"),RootRuntimeDomainSettings.encode(changed));
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.readExact(source,CLOCK));
    }

    private record Fixture(RootRuntimeDomainSettings.Configuration configuration,FileRef original,List<FileRef> history) {
        private Fixture {history=List.copyOf(history);}
    }
    private static Fixture fixture(Path root,String queryMachine)throws IOException {
        Files.createDirectories(root);
        FileRef budget=write(root.resolve("formal-budget.json"),"metadata-only budget"),
                model=write(root.resolve("formal-model.json"),"metadata-only model"),
                inventory=write(root.resolve("normal-inventory.json"),"metadata-only normal inventory"),
                profile=write(root.resolve("normal-profile.json"),"metadata-only profile"),
                snapshot=write(root.resolve("normal-snapshot.txt"),"metadata-only settings snapshot");
        FileRef coa=write(root.resolve("coa-limits.json"),CoaVfs.encodeLimits(new CoaVfs.Limits(65536,32768)).bytes());
        var request=new OriginalDriverQueryHistorySettings.Request(queryMachine,AT,AT.plusSeconds(3600),
                new OriginalDriverQueryHistorySettings.JavaConfigured(new OriginalDriverQueryHistorySettings.Directory(root.resolve("query-state")),
                        4096,OriginalDriverQueryHistorySettings.Admission.ROOT_STORAGE));
        FileRef rawRequest=write(root.resolve("query-request.json"),OriginalDriverQueryHistorySettings.encodeRequest(request)),
                producer=write(root.resolve("historical-query-producer.txt"),"metadata-only historical producer");
        var document=new OriginalDriverQueryHistorySettings.Document(
                new OriginalDriverQueryHistorySettings.SourceRefs(exact(rawRequest),exact(producer)),request);
        FileRef query=write(root.resolve("query-document.json"),OriginalDriverQueryHistorySettings.encode(document));
        var configuration=new RootRuntimeDomainSettings.Configuration(RootRuntimeDomainSettings.SCHEMA,WindowsJobProcess.currentMachineId(),
                AT.toString(),AT.plusSeconds(3600).toString(),
                new RootRuntimeDomainSettings.Lifecycle(root.resolve("state").toString(),root.resolve("saves").toString(),
                        root.resolve("tutorial").toString(),root.resolve("evidence").toString(),List.of("fixture.clock"),1000),
                root.resolve("relations").toString(),new RootRuntimeDomainSettings.FormalWar(budget,model,null,null),
                new RootRuntimeDomainSettings.Peacetime(true,true,true),
                new RootRuntimeDomainSettings.Offline(root.resolve("offline-work").toString(),root.resolve("knowledge").toString(),
                        root.resolve("grants.json").toString(),2,16),
                new RootRuntimeDomainSettings.NormalExitOriginals(exact(inventory),exact(profile),exact(snapshot)),
                new RootRuntimeDomainSettings.CoaReadLimits(coa),exact(query),
                new RootRuntimeDomainSettings.PlanFlags(true,false,true,false,true,false,true),null);
        FileRef original=write(root.resolve("settings.json"),RootRuntimeDomainSettings.encode(configuration));
        return new Fixture(configuration,original,List.of(budget,model,inventory,profile,snapshot,rawRequest,producer));
    }
    private static RootRuntimeDomainSettings.Configuration withRequired(RootRuntimeDomainSettings.Configuration c,
            FileRef coa,ExactRef query) {
        return new RootRuntimeDomainSettings.Configuration(c.schema(),c.machineId(),c.observedAtUtc(),c.reviewAtUtc(),
                c.lifecycle(),c.familyRelationExportRoot(),c.formalWar(),c.peacetime(),c.offline(),c.normalExit(),
                new RootRuntimeDomainSettings.CoaReadLimits(coa),query,c.planFlags(),c.stockRead());
    }
    private static FileRef write(Path path,String content)throws IOException {return write(path,content.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    private static FileRef write(Path path,byte[] content)throws IOException {return FileRef.measure(Files.write(path,content));}
    private static ExactRef exact(FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
}
