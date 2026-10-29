package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.*;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SelectedSource;
import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;

/** Historical Java source DATA -> selector -> typed Sources -> original Prepared. No fabricated Core or Game. */
public final class RootChinaCareerSourcesFactoryTest {
    @TempDir Path temporary;
    private List<SelectedSource> rows()throws IOException {
        return List.of(source(NATIVE_TRANSPORT,ChinaCareerService.class),source(NATIVE_TRANSPORT,ChinaCareerCodec.class),
                source(NATIVE_TRANSPORT,ChinaCareerContract.class),source(LOCAL_SERVICE,RootChinaCareerSourcesFactory.class),
                source(LOCAL_SERVICE,RootChinaCareerPublicProducts.class));
    }
    private SelectedSource source(RootRuntimeSelectedSources.Module module,Class<?> type)throws IOException {
        Path body=temporary.resolve(type.getSimpleName()+".java");Files.writeString(body,"historical Java source DATA for "+type.getName());
        FileRef original=FileRef.measure(body);
        String target=module.directory()+"/src/main/java/"+type.getName().replace('.','/')+".java";
        return new SelectedSource(target,new ExactRef(original.path(),original.bytes(),original.sha256()));
    }
    @Test void actualSourcePairsReachOriginalPreparedAndExactRefSerialization()throws Exception {
        var rows=rows();var selected=new RootRuntimeSelectedSources(rows);
        var sources=RootChinaCareerSourcesFactory.sources(selected,rows);
        assertEquals(selected.javaSource(NATIVE_TRANSPORT,ChinaCareerService.class),sources.service());
        assertEquals(selected.javaSource(NATIVE_TRANSPORT,ChinaCareerCodec.class),sources.codec());
        assertEquals(sources.service(),ExactRef.fromJson(sources.service().toJson()));
        assertEquals(sources.codec(),ExactRef.fromJson(sources.codec().toJson()));
        for(var ref:List.of(sources.service(),sources.codec())) {
            var wrong=ref.toJson().put("bytes",true);
            assertThrows(IllegalArgumentException.class,()->ExactRef.fromJson(wrong));
            var fractional=ref.toJson().put("bytes",1.0);
            assertThrows(IllegalArgumentException.class,()->ExactRef.fromJson(fractional));
            var missing=ref.toJson();missing.remove("sha256");
            assertThrows(IllegalArgumentException.class,()->ExactRef.fromJson(missing));
        }
        var actual=sources.prepared();
        assertTrue(actual.domainRegistrations().isEmpty());assertTrue(actual.privatePermissions().isEmpty());
        assertEquals(5,selected.retainedSources().size());selected.requireCurrent();
    }
    @Test void missingDuplicateAndForeignInputsSelectionsNeverMakePartialProducts()throws Exception {
        var complete=rows();
        for(String leaf:List.of("ChinaCareerService.java","ChinaCareerCodec.java","ChinaCareerContract.java","RootChinaCareerPublicProducts.java","RootChinaCareerSourcesFactory.java")) {
            var missing=complete.stream().filter(row->!row.targetRelative().endsWith("/"+leaf)).toList();
            assertThrows(IOException.class,()->RootChinaCareerSourcesFactory.sources(new RootRuntimeSelectedSources(missing),complete));
            assertThrows(IOException.class,()->RootChinaCareerSourcesFactory.sources(new RootRuntimeSelectedSources(complete),missing));
        }
        var duplicate=new ArrayList<>(complete);duplicate.add(complete.getFirst());
        assertThrows(IOException.class,()->new RootRuntimeSelectedSources(duplicate));
        var foreign=new ArrayList<>(complete);SelectedSource actual=foreign.getFirst();
        foreign.set(0,new SelectedSource(actual.targetRelative(),new ExactRef(actual.sourceRef().path(),actual.sourceRef().bytes(),"0".repeat(64))));
        assertThrows(IOException.class,()->RootChinaCareerSourcesFactory.sources(new RootRuntimeSelectedSources(complete),foreign));
    }
    @Test void historicalJavaMetadataReachesTheSameConsumerAfterDriftReplacementOrDeletion()throws Exception {
        for(boolean replace:new boolean[]{false,true}) {
            var actual=new ArrayList<>(rows());int index=0;
            while(!actual.get(index).targetRelative().endsWith("/ChinaCareerCodec.java"))index++;
            var original=actual.get(index);Path copy=temporary.resolve(replace?"replacement-case":"content-case").resolve("ChinaCareerCodec.java");
            Files.createDirectories(copy.getParent());Files.copy(Path.of(original.sourceRef().path()),copy);
            FileRef measured=FileRef.measure(copy);var ref=new ExactRef(measured.path(),measured.bytes(),measured.sha256());
            actual.set(index,new SelectedSource(original.targetRelative(),ref));
            var selected=new RootRuntimeSelectedSources(actual);var before=RootChinaCareerSourcesFactory.sources(selected,actual);
            if(replace){Path second=copy.resolveSibling("same-bytes.java");Files.copy(copy,second);Files.setLastModifiedTime(second,Files.getLastModifiedTime(copy));Files.move(second,copy,StandardCopyOption.REPLACE_EXISTING);}
            else Files.writeString(copy,"changed historical ChinaCareer source DATA");
            selected.requireCurrent();assertEquals(before,RootChinaCareerSourcesFactory.sources(selected,actual));
            assertEquals(ref,before.codec());Files.delete(copy);
            assertEquals(before,RootChinaCareerSourcesFactory.sources(selected,actual));
        }
    }
    /** Real managed fixture only: the supplied Prepared must be the identical object installed by the sole aggregate. */
    public static void assertActualInstalled(RootChinaCareerPublicProducts.Prepared actualPrepared,
            RootRuntimeDefinitions.Inputs actualInputs,RootRuntimeSelectedSources sameSelected,RootInstalledCatalog actualCatalog)throws Exception {
        var sources=RootChinaCareerSourcesFactory.sources(sameSelected,actualInputs.sourceIndex());
        var installed=actualPrepared.install(actualCatalog.context());
        assertSame(installed,actualCatalog.additionalDomains().chinaCareer());
        assertEquals(6,installed.installation().reads().size());
        for(var read:installed.installation().reads()) {
            assertTrue(actualCatalog.context().readCatalog().containsIdentity(read.contract()));
            assertEquals(sources.service(),read.contract().sourceRef());assertEquals(sources.codec(),read.decoderSource());
            assertTrue(installed.service().registration().all().stream().anyMatch(same->same==read.contract()));
        }
        sameSelected.requireCurrent();
    }
}
