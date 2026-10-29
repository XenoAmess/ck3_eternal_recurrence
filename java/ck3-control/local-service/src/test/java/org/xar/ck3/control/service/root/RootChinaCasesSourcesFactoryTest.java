package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JavaType;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesFacade;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesService;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SelectedSource;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;
import static org.junit.jupiter.api.Assertions.*;

/** Actual temporary source-file custody and the original strict source-index serde. No Inputs, Core, Game or loaded-class proof is fabricated. */
final class RootChinaCasesSourcesFactoryTest {
    @TempDir Path directory;
    private record Producer(Module module,Class<?> type) {
        String target(){return module.directory()+"/src/main/java/"+type.getName().replace('.','/')+".java";}
    }
    private static final List<Producer> ACTUAL=List.of(
            new Producer(Module.NATIVE_TRANSPORT,ChinaCasesFacade.class),
            new Producer(Module.NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.class),
            new Producer(Module.NATIVE_TRANSPORT,ChinaCasesContract.class),
            new Producer(Module.NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesCodec.class),
            new Producer(Module.NATIVE_TRANSPORT,ChinaCasesService.class),
            new Producer(Module.LOCAL_SERVICE,RootChinaCasesPublicProducts.class),
            new Producer(Module.LOCAL_SERVICE,RootChinaCasesSourcesFactory.class),
            new Producer(Module.APPLICATION,org.xar.ck3.control.application.action.ReadContract.class),
            new Producer(Module.APPLICATION,org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.class));

    @Test void originalSelectorFeedsAllSixExactSourcesAndTheActualExistingPreparedWithoutASecondRegistry()throws Exception {
        List<SelectedSource> winners=sources(directory.resolve("selected"));var selector=new RootRuntimeSelectedSources(winners);
        RootChinaCasesPublicProducts.Prepared prepared=RootChinaCasesSourcesFactory.prepareSourceSelection(winners,selector);
        var actual=prepared.sources();
        assertEquals(winners.get(0).sourceRef(),actual.facade());assertEquals(winners.get(1).sourceRef(),actual.originalDecoder());
        assertEquals(winners.get(2).sourceRef(),actual.publicContract());assertEquals(winners.get(3).sourceRef(),actual.publicCodec());
        assertEquals(winners.get(4).sourceRef(),actual.publicService());assertEquals(winners.get(5).sourceRef(),actual.rootProduct());
        assertEquals(winners.stream().map(SelectedSource::sourceRef).toList(),selector.retainedSources());
        assertTrue(selector.retainedSources().contains(winners.get(6).sourceRef()),"helper class must reach the caller's final same-plan custody inventory");
        assertTrue(selector.retainedSources().contains(winners.get(7).sourceRef()),"actual fixed-projector contract source must be retained");
        assertTrue(selector.retainedSources().contains(winners.get(8).sourceRef()),"actual rich projection source must be retained");
        assertTrue(prepared.privatePermissions().isEmpty());assertTrue(prepared.domainRegistrations().isEmpty());
        assertThrows(NullPointerException.class,()->prepared.install(null),"source selection cannot invent the actual Core/context needed for Installed");
        assertThrows(NullPointerException.class,()->prepared.bindCore(null));selector.requireCurrent();
        assertThrows(NullPointerException.class,()->RootChinaCasesSourcesFactory.prepare(null,selector));
    }

    @Test void everyMissingInputOrSelectorRoleRejectsAndSameFilenameFromAnotherInputCannotBeBorrowed()throws Exception {
        List<SelectedSource> winners=sources(directory.resolve("original"));
        for(int omitted=0;omitted<ACTUAL.size();omitted++) {
            var incomplete=new ArrayList<>(winners);incomplete.remove(omitted);
            var completeSelector=new RootRuntimeSelectedSources(winners);
            assertThrows(IOException.class,()->RootChinaCasesSourcesFactory.prepareSourceSelection(incomplete,completeSelector));
            assertTrue(completeSelector.retainedSources().isEmpty(),"all required Inputs rows are checked before retaining any source");
            var incompleteSelector=new RootRuntimeSelectedSources(incomplete);
            assertThrows(IOException.class,()->RootChinaCasesSourcesFactory.prepareSourceSelection(winners,incompleteSelector));
        }
        List<SelectedSource> foreign=sources(directory.resolve("foreign"));
        var foreignSelector=new RootRuntimeSelectedSources(foreign);
        assertThrows(IOException.class,()->RootChinaCasesSourcesFactory.prepareSourceSelection(winners,foreignSelector));
        assertNotEquals(winners.getFirst().sourceRef(),foreign.getFirst().sourceRef(),"identical DATA bytes do not replace exact source path/file custody");
        var wrongModule=new ArrayList<>(winners);SelectedSource first=wrongModule.getFirst();
        wrongModule.set(0,new SelectedSource(first.targetRelative().replace("native-transport/","local-service/"),first.sourceRef()));
        assertThrows(IOException.class,()->RootChinaCasesSourcesFactory.prepareSourceSelection(wrongModule,new RootRuntimeSelectedSources(winners)));
        var duplicate=new ArrayList<>(winners);duplicate.add(first);
        assertThrows(IOException.class,()->RootChinaCasesSourcesFactory.prepareSourceSelection(duplicate,new RootRuntimeSelectedSources(winners)));
        var alias=new ArrayList<>(winners);alias.add(new SelectedSource(first.targetRelative().replace("native-transport/","Native-Transport/"),first.sourceRef()));
        assertThrows(IOException.class,()->RootChinaCasesSourcesFactory.prepareSourceSelection(alias,new RootRuntimeSelectedSources(winners)));
    }

    @Test void historicalJavaMetadataReachesTheSamePreparedAfterFileDriftReplacementOrDeletion()throws Exception {
        List<SelectedSource> winners=sources(directory.resolve("drift"));var selector=new RootRuntimeSelectedSources(winners);
        var before=RootChinaCasesSourcesFactory.prepareSourceSelection(winners,selector).sources();
        Path codec=Path.of(before.publicCodec().path());Files.writeString(codec,"changed historical source DATA\n");
        selector.requireCurrent();
        assertEquals(before,RootChinaCasesSourcesFactory.prepareSourceSelection(winners,selector).sources());
        Files.delete(codec);
        assertEquals(before,RootChinaCasesSourcesFactory.prepareSourceSelection(winners,selector).sources());
        List<SelectedSource> other=sources(directory.resolve("replace"));var retained=new RootRuntimeSelectedSources(other);
        var otherBefore=RootChinaCasesSourcesFactory.prepareSourceSelection(other,retained).sources();
        Path body=Path.of(other.get(5).sourceRef().path()),replacement=body.resolveSibling("Replacement.java");
        Files.copy(body,replacement);Files.setLastModifiedTime(replacement,Files.getLastModifiedTime(body));
        Files.move(replacement,body,StandardCopyOption.REPLACE_EXISTING);
        retained.requireCurrent();
        assertEquals(otherBefore,RootChinaCasesSourcesFactory.prepareSourceSelection(other,retained).sources());
        Files.delete(body);
        assertEquals(otherBefore,RootChinaCasesSourcesFactory.prepareSourceSelection(other,retained).sources());
    }

    @Test void actualSourceIndexSerdeRoundTripsAndWrongFieldsTypesAndAlteredRefAreRefused()throws Exception {
        List<SelectedSource> winners=sources(directory.resolve("wire"));var mapper=ControlBuild.strictMapper();
        JavaType type=mapper.getTypeFactory().constructCollectionType(List.class,SelectedSource.class);
        byte[] encoded=mapper.writeValueAsBytes(winners);List<SelectedSource> decoded=mapper.readValue(encoded,type);
        assertEquals(winners,decoded);assertArrayEquals(encoded,mapper.writeValueAsBytes(decoded));
        var prepared=RootChinaCasesSourcesFactory.prepareSourceSelection(decoded,new RootRuntimeSelectedSources(winners));
        assertEquals(winners.get(5).sourceRef(),prepared.sources().rootProduct());
        ArrayNode rows=(ArrayNode)mapper.readTree(encoded);
        var missing=rows.deepCopy();((ObjectNode)missing.get(0)).remove("source_ref");
        assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(missing),type));
        var extra=rows.deepCopy();((ObjectNode)extra.get(0)).put("source_alias",true);
        assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(extra),type));
        for(String token:List.of("true","1.0","\"1\"","null")) {
            var wrong=rows.deepCopy();((ObjectNode)wrong.get(0).get("source_ref")).set("bytes",mapper.readTree(token));
            assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(wrong),type));
        }
        var changed=rows.deepCopy();((ObjectNode)changed.get(0).get("source_ref")).put("sha256","0".repeat(64));
        List<SelectedSource> altered=mapper.readValue(mapper.writeValueAsBytes(changed),type);
        assertThrows(IOException.class,()->RootChinaCasesSourcesFactory.prepareSourceSelection(altered,new RootRuntimeSelectedSources(winners)));
    }

    @Test void unconsumedRowsAreNotReadOrPromotedToWholeInputsOrLoadedClassQualification()throws Exception {
        var winners=new ArrayList<>(sources(directory.resolve("finite")));Path unused=directory.resolve("Unused.java");
        Files.writeString(unused,"unconsumed source DATA\n");
        winners.add(new SelectedSource("local-service/src/main/java/example/Unused.java",exact(unused)));
        var selector=new RootRuntimeSelectedSources(winners);RootChinaCasesSourcesFactory.prepareSourceSelection(winners,selector);
        Files.writeString(unused,"changed outside this helper's consumed role set\n");
        selector.requireCurrent();assertEquals(9,selector.retainedSources().size());
        // Historical source DATA does not qualify a loaded class, Inputs, Core or Game.
    }

    private static List<SelectedSource> sources(Path root)throws IOException {
        var rows=new ArrayList<SelectedSource>();
        for(int index=0;index<ACTUAL.size();index++) {
            Producer role=ACTUAL.get(index);Path folder=root.resolve(Integer.toString(index));Files.createDirectories(folder);
            Path body=folder.resolve(role.type().getSimpleName()+".java");
            Files.writeString(body,"// controlled source DATA for "+role.type().getName()+"\n");
            rows.add(new SelectedSource(role.target(),exact(body)));
        }
        return List.copyOf(rows);
    }
    private static ExactRef exact(Path path)throws IOException {FileRef ref=FileRef.measure(path);return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
}
