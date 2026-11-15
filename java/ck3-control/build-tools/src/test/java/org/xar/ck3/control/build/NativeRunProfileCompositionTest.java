package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.build.NativeRunProfileManifest.*;
import static org.xar.ck3.control.build.NativeRunProfileProducer.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** The exact composition byte/codec consumers only; these fixtures never grant a completed Maven or loaded-runtime qualification. */
final class NativeRunProfileCompositionTest {
    @TempDir Path temporary;

    @Test void stagedCompilerSourcesOutputsAndThreeFamilyJarAreConsumedWithoutRecompilingTheirInputs()throws Exception{
        var composition=fixture(false,false);
        var before=composition.patchedSources().stream().map(FileRef::sha256).toList();
        NativeRunProfileProducer.verifyCompilationEvidence(composition,new ArrayList<>());
        NativeRunProfileProducer.verifyPatchArchive(composition);
        assertEquals(2,composition.compilations().size());
        assertEquals(before,composition.patchedSources().stream().map(FileRef::sha256).toList());
        for(var source:composition.patchedSources())source.verify();
        assertEquals(composition,ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(composition),ToolComposition.class));
        Files.writeString(Path.of(composition.patchedSources().getLast().path()),"actual source drift after the selected compilation");
        assertThrows(IOException.class,()->NativeRunProfileProducer.verifyCompilationEvidence(composition,new ArrayList<>()));
    }
    @Test void patchJarMustContainEveryExactCompiledEntryAndNoUnrequestedFamily()throws Exception{
        var changed=fixture(true,false);
        assertThrows(IOException.class,()->NativeRunProfileProducer.verifyPatchArchive(changed));
        Path extra=temporary.resolve("extra.jar");
        try(var zip=new ZipOutputStream(Files.newOutputStream(extra))){
            for(var row:changed.patchedClasses()){zip.putNextEntry(new ZipEntry(row.binaryName()+".class"));zip.write(Files.readAllBytes(Path.of(row.output().path())));zip.closeEntry();}
            zip.putNextEntry(new ZipEntry("org/xar/ck3/control/build/Other.class"));zip.write(new byte[]{1});zip.closeEntry();
        }
        assertThrows(IOException.class,()->NativeRunProfileProducer.verifyPatchArchive(withJar(changed,FileRef.measure(extra))));
    }
    @Test void compilationPostcheckAndExactSourceHashRemainRequiredByTheSameConsumer()throws Exception{
        var invalid=fixture(false,true);
        assertThrows(IOException.class,()->NativeRunProfileProducer.verifyCompilationEvidence(invalid,new ArrayList<>()));
    }
    @Test void newRequestDataCannotMintASevenFilePreparedProducerOrWeakenOldRequestVersions()throws Exception{
        var composition=fixture(false,false);FileRef pin=composition.sourceReady();
        var source=new SavedSource(SavedKind.VANILLA,pin);
        var request=new ExplicitRequest(COMPOSED_SAVED_REQUEST_SCHEMA,"fixture-machine",Instant.now().plusSeconds(60).toString(),
                temporary.resolve("state").toString(),temporary.toString(),pin,pin,pin,pin,false,source,temporary.resolve("profile").toString());
        assertEquals(request,decodeExplicitRequest(encodeExplicitRequest(request)));
        assertThrows(IOException.class,()->NativeRunProfileProducer.deriveExplicit(request,composition.completeRuntime()));
        assertThrows(IllegalArgumentException.class,()->new ExplicitRequest(COMPOSED_SAVED_REQUEST_SCHEMA,request.machineId(),request.reviewAtUtc(),
                request.stateDir(),request.sourceWorkingDirectory(),pin,pin,pin,pin,false,source));
        var wire=(ObjectNode)ControlBuild.strictMapper().readTree(encodeExplicitRequest(request));wire.put("schema",EXPLICIT_REQUEST_SCHEMA);
        assertThrows(IOException.class,()->decodeExplicitRequest(canonical(wire)));
        assertTrue(isCurrentVersion(ControlBuild.strictMapper().readTree("{\"schema\":\"xar.java-native-run-profile-environment/v5\"}")));
    }
    @Test void rootAuthorityUsesOneIntegerWireDomainAndStillRejectsFloatBooleanAndChangedFields()throws Exception{
        var composition=fixture(false,false);var mapper=ControlBuild.strictMapper();
        var expected=NativeRunProfileProducer.compositionAuthority(composition,"2026-11-15T21:25:09Z");
        var actual=(ObjectNode)mapper.readTree(mapper.writeValueAsBytes(expected));
        assertTrue(expected.path("base_tools_build").path("bytes").isInt());
        assertEquals(expected,actual,"Java long fields and parsed JSON integers must share the original wire domain");
        var floating=actual.deepCopy();((ObjectNode)floating.get("base_tools_build")).put("bytes",composition.baseToolsBuild().bytes()+0.0);
        assertNotEquals(expected,floating);
        var booleanSize=actual.deepCopy();((ObjectNode)booleanSize.get("base_tools_build")).put("bytes",true);
        assertNotEquals(expected,booleanSize);
        var changed=actual.deepCopy();changed.put("issuer_task","foreign-source");assertNotEquals(expected,changed);
    }
    @Test void laterProducerFamilySupersedesItsOldRowsWhileTheSameOldPhaseStillOwnsUnchangedManifest()throws Exception{
        var old=fixture(false,false);var mapper=ControlBuild.strictMapper();Path root=Files.createDirectory(temporary.resolve("producer-fix"));
        FileRef source=write(root.resolve("NativeRunProfileProducer.java"),"corrected producer wire reader".getBytes(StandardCharsets.UTF_8));
        var output=new PatchedClass("org/xar/ck3/control/build/NativeRunProfileProducer",write(root.resolve("NativeRunProfileProducer.class"),"corrected producer output".getBytes(StandardCharsets.UTF_8)));
        ObjectNode config=mapper.createObjectNode();config.putObject("phases").putObject("prod").set("sources",mapper.valueToTree(List.of(source)));
        FileRef configRef=write(root.resolve("config.json"),mapper.writeValueAsBytes(config));
        ObjectNode outputs=mapper.createObjectNode();outputs.put("phase","prod");outputs.put("success",true);outputs.putArray("errors");
        var row=outputs.putArray("classes").addObject();row.set("pin",mapper.valueToTree(output.output()));
        row.putObject("metadata").put("name",output.binaryName()).put("SourceFile","NativeRunProfileProducer.java");
        FileRef outputsRef=write(root.resolve("outputs.json"),mapper.writeValueAsBytes(outputs));
        ObjectNode post=mapper.createObjectNode();post.put("inputs_unchanged",true);post.put("contract_accepted",true);post.set("output_manifest",mapper.valueToTree(outputsRef));
        FileRef postRef=write(root.resolve("post.json"),mapper.writeValueAsBytes(post));
        ObjectNode actual=mapper.createObjectNode();actual.put("schema","composite-operator-integration-actual/v1");actual.put("phase","prod");actual.put("exit_code",0);
        actual.put("timeout",false);actual.put("contract_accepted",true);actual.set("output_manifest",mapper.valueToTree(outputsRef));actual.set("config",mapper.valueToTree(configRef));actual.set("post",mapper.valueToTree(postRef));
        var phases=new ArrayList<>(old.compilations());phases.add(new CompileEvidence(write(root.resolve("actual.json"),mapper.writeValueAsBytes(actual)),outputsRef));
        var sources=new ArrayList<>(old.patchedSources());sources.set(1,source);var classes=new ArrayList<>(old.patchedClasses());classes.set(1,output);
        Path jar=root.resolve("patch.jar");try(var zip=new ZipOutputStream(Files.newOutputStream(jar))){
            for(var selected:classes){zip.putNextEntry(new ZipEntry(selected.binaryName()+".class"));zip.write(Files.readAllBytes(Path.of(selected.output().path())));zip.closeEntry();}
        }
        FileRef patch=FileRef.measure(jar);var runtime=new ArrayList<>(old.completeRuntime());runtime.set(0,patch);
        var selected=new ToolComposition(old.schema(),old.machineId(),old.reviewAtUtc(),old.baseToolsBuild(),old.completionSource(),old.rootAuthorization(),old.sourceReady(),
                phases,sources,classes,patch,old.runtimeCopies(),runtime);
        NativeRunProfileProducer.verifyCompilationEvidence(selected,new ArrayList<>());NativeRunProfileProducer.verifyPatchArchive(selected);
        old.patchedSources().get(1).verify();old.patchedClasses().get(1).output().verify();
        var unselected=new ToolComposition(selected.schema(),selected.machineId(),selected.reviewAtUtc(),selected.baseToolsBuild(),selected.completionSource(),selected.rootAuthorization(),selected.sourceReady(),
                phases,sources,old.patchedClasses(),patch,old.runtimeCopies(),runtime);
        assertThrows(IOException.class,()->NativeRunProfileProducer.verifyCompilationEvidence(unselected,new ArrayList<>()));
    }

    private ToolComposition fixture(boolean omitLast,boolean failedPost)throws Exception{
        Path root=Files.createDirectory(temporary.resolve("composition"));var mapper=ControlBuild.strictMapper();
        var sources=new ArrayList<FileRef>();var classes=new ArrayList<PatchedClass>();
        for(String family:List.of("ControlBuild","NativeRunProfileProducer","NativeRunProfileManifest")){
            sources.add(write(root.resolve(family+".java"),("software source "+family).getBytes(StandardCharsets.UTF_8)));
            classes.add(new PatchedClass("org/xar/ck3/control/build/"+family,write(root.resolve(family+".class"),("software output "+family).getBytes(StandardCharsets.UTF_8))));
        }
        var phases=new ArrayList<CompileEvidence>();
        for(int phase=0;phase<2;phase++){
            List<FileRef> currentSources=phase==0?sources.subList(0,1):sources.subList(1,3);
            List<PatchedClass> currentClasses=phase==0?classes.subList(0,1):classes.subList(1,3);
            ObjectNode config=mapper.createObjectNode();config.putObject("phases").putObject("prod").set("sources",mapper.valueToTree(currentSources));
            FileRef configRef=write(root.resolve("config"+phase+".json"),mapper.writeValueAsBytes(config));
            ObjectNode outputs=mapper.createObjectNode();outputs.put("phase","prod");outputs.put("success",true);outputs.putArray("errors");var rows=outputs.putArray("classes");
            for(var row:currentClasses){var item=rows.addObject();item.set("pin",mapper.valueToTree(row.output()));
                var metadata=item.putObject("metadata");metadata.put("name",row.binaryName());metadata.put("SourceFile",row.binaryName().substring(row.binaryName().lastIndexOf('/')+1)+".java");}
            FileRef outputsRef=write(root.resolve("outputs"+phase+".json"),mapper.writeValueAsBytes(outputs));
            ObjectNode post=mapper.createObjectNode();post.put("inputs_unchanged",!(failedPost&&phase==1));post.put("contract_accepted",true);post.set("output_manifest",mapper.valueToTree(outputsRef));
            FileRef postRef=write(root.resolve("post"+phase+".json"),mapper.writeValueAsBytes(post));
            ObjectNode actual=mapper.createObjectNode();actual.put("schema","composite-operator-integration-actual/v1");actual.put("phase","prod");actual.put("exit_code",0);
            actual.put("timeout",false);actual.put("contract_accepted",true);actual.set("output_manifest",mapper.valueToTree(outputsRef));actual.set("config",mapper.valueToTree(configRef));actual.set("post",mapper.valueToTree(postRef));
            phases.add(new CompileEvidence(write(root.resolve("actual"+phase+".json"),mapper.writeValueAsBytes(actual)),outputsRef));
        }
        Path jar=root.resolve("patch.jar");try(var zip=new ZipOutputStream(Files.newOutputStream(jar))){
            for(int i=0;i<classes.size()-(omitLast?1:0);i++){var row=classes.get(i);zip.putNextEntry(new ZipEntry(row.binaryName()+".class"));zip.write(Files.readAllBytes(Path.of(row.output().path())));zip.closeEntry();}
        }
        FileRef patch=FileRef.measure(jar),dummy=write(root.resolve("not-qualified.json"),"{}".getBytes(StandardCharsets.UTF_8));
        var copies=new ArrayList<RuntimeCopy>();var runtime=new ArrayList<FileRef>();runtime.add(patch);Files.createDirectory(root.resolve("lib"));
        for(int i=0;i<6;i++){byte[] bytes=("old runtime "+i).getBytes(StandardCharsets.UTF_8);copies.add(new RuntimeCopy(write(root.resolve("old"+i+".jar"),bytes),write(root.resolve("lib/runtime"+i+".jar"),bytes)));runtime.add(copies.getLast().copy());}
        return new ToolComposition(TOOL_COMPOSITION_SCHEMA,"fixture-machine",Instant.now().plusSeconds(60).toString(),dummy,dummy,dummy,dummy,phases,sources,classes,patch,copies,runtime);
    }
    private static ToolComposition withJar(ToolComposition old,FileRef jar){
        var runtime=new ArrayList<>(old.completeRuntime());runtime.set(0,jar);
        return new ToolComposition(old.schema(),old.machineId(),old.reviewAtUtc(),old.baseToolsBuild(),old.completionSource(),old.rootAuthorization(),old.sourceReady(),
                old.compilations(),old.patchedSources(),old.patchedClasses(),jar,old.runtimeCopies(),runtime);
    }
    private static FileRef write(Path path,byte[] bytes)throws IOException{Files.write(path,bytes);return FileRef.measure(path);}
}
