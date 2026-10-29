package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.jar.Attributes;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import java.util.jar.Manifest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.CiBootstrap.JavaUtf8Invocation;

/** Actual producer/envelope/owned Java process tests. No CK3 or ManagedGame qualification. */
final class JavaUtf8InvocationTest {
    @TempDir Path temporary;
    private static final List<String> ARGUMENTS=List.of("","a b","中文 Ω 😀 e\u0301","\"quoted\"","trailing\\","slash\\\"mix");
    private static final String PROPERTY="配置/中文 Ω 😀";

    @Test void realOwnedClassJarAndSourceEntrypointsKeepLogicalUnicodeAndOriginalTerminals()throws Exception {
        Fixture fixture=fixture();
        for(String mode:List.of("CLASS","JAR","SOURCE","FAIL42")){
            boolean failure=mode.equals("FAIL42");
            Path evidence=Files.createDirectory(temporary.resolve("proof-"+mode));
            JavaUtf8Invocation.Target target;
            if(mode.equals("CLASS")||failure){
                var classes=JavaUtf8Invocation.captureClasspath(fixture.classes());var dependencies=JavaUtf8Invocation.captureClasspath(fixture.dependencies());
                target=new JavaUtf8Invocation.ClassTarget("UnicodeMain",classes,List.of(classes,dependencies,classes));
            }else if(mode.equals("JAR"))target=JavaUtf8Invocation.captureJar(fixture.jar());
            else target=new JavaUtf8Invocation.SourceTarget(JavaUtf8Invocation.captureFile(fixture.source()),"UnicodeMain",List.of(JavaUtf8Invocation.captureClasspath(fixture.dependencies())),JavaUtf8Invocation.captureOutputRoot(Files.createDirectory(temporary.resolve("compiled-source"))),1<<20);
            var request=new JavaUtf8Invocation.Request(target,List.of(new JavaUtf8Invocation.Property("xar.unicode.test",PROPERTY)),failure?List.of("--fail42"):ARGUMENTS,JavaUtf8Invocation.captureOutputRoot(evidence));
            long[] admitted={0};var publication=JavaUtf8Invocation.publish(request,request.evidenceRoot(),"invocation.bin",pending->admitted[0]=pending);
            assertEquals(JavaUtf8Invocation.maximumOutputBytes(request),admitted[0]);
            JavaUtf8Invocation.Carrier carrier=mode.equals("SOURCE")?new JavaUtf8Invocation.SourceCarrier(JavaUtf8Invocation.captureFile(bootstrapSource())):carrier();
            List<String> vm=vm();var launch=JavaUtf8Invocation.launch(publication,carrier,vm);
            assertEquals(request,JavaUtf8Invocation.inspect(launch.physicalArguments(),carrier,vm));
            assertTrue(launch.physicalArguments().stream().allMatch(value->value.codePoints().allMatch(code->code>=32&&code<=126)));
            assertFalse(launch.physicalArguments().stream().anyMatch(value->value.contains("中文")));
            Path stdout=evidence.resolve("stdout.bin");var environment=new TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);environment.putAll(System.getenv());
            for(String key:List.of("JAVA_TOOL_OPTIONS","JDK_JAVA_OPTIONS","_JAVA_OPTIONS"))environment.remove(key);
            var spec=new WindowsJobProcess.CommandSpec(Path.of(System.getProperty("java.home"),"bin/java.exe"),launch.physicalArguments(),temporary.toAbsolutePath(),environment,stdout,evidence.resolve("stderr.log"),384L<<20);
            try(var nativeInputs=JavaUtf8NativeCustody.acquire(launch,carrier)){
              nativeInputs.requireCurrent();
              // The actual retained file handle must prevent writes and replacement throughout this scope.
              assertThrows(IOException.class,()->Files.writeString(Path.of(publication.envelope().path()),"tamper"));
              try(var child=WindowsJobProcess.start(spec,WindowsJobProcess.ConsoleMode.DETACHED)){
                long quotedEvidence=nativeInputs.maximumEvidenceBytes(spec.executable());assertTrue(quotedEvidence>0&&quotedEvidence<JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES);
                nativeInputs.attach(child);var original=child.identity();var result=child.await(Duration.ofSeconds(55),Instant.now().plusSeconds(60),nativeInputs.guard(()->{}));
                var continuity=nativeInputs.verifyTerminal(result);assertEquals(original,continuity.identity());assertEquals(result,continuity.terminal());
                byte[] recorded=JavaUtf8NativeCustody.encodeEvidence(continuity.evidence());assertTrue(recorded.length<=quotedEvidence);
                var cold=JavaUtf8NativeCustody.decodeEvidence(recorded);assertEquals(continuity.evidence(),cold);JavaUtf8NativeCustody.requireCurrent(cold,launch,carrier);
                var mapper=ControlBuild.strictMapper();var missing=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(recorded);missing.remove("machine_id");assertThrows(IOException.class,()->JavaUtf8NativeCustody.decodeEvidence(mapper.writeValueAsBytes(missing)));
                var wrong=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(recorded);((com.fasterxml.jackson.databind.node.ObjectNode)wrong.get("files").get(0).get("native_file")).put("file_id_decimal","0");
                var wrongIdentity=JavaUtf8NativeCustody.decodeEvidence(mapper.writeValueAsBytes(wrong));assertThrows(IOException.class,()->JavaUtf8NativeCustody.requireCurrent(wrongIdentity,launch,carrier));
                assertEquals(!failure,result.passed(),()->"Actual child terminal differed: "+result+" stderr="+readQuietly(spec.stderr()));
                assertEquals(original,result.identity());assertEquals(failure?42:0,result.exitCode());assertNull(result.stopReason());assertEquals(0,result.accounting().activeProcesses());
              }
            }
            if(failure){var prepared=JavaUtf8Invocation.inspectPreparation(JavaUtf8Invocation.captureFile(JavaUtf8Invocation.preparationPath(request)),publication);assertEquals("CLASS",prepared.mode());assertEquals(publication.envelope(),prepared.envelope());continue;}
            String[] rows=Files.readString(stdout,StandardCharsets.UTF_8).split("\n",-1);assertEquals(ARGUMENTS.size()+4,rows.length);
            for(int index=0;index<ARGUMENTS.size();index++)assertEquals(ARGUMENTS.get(index),fromBase64(rows[index]));
            assertEquals(PROPERTY,fromBase64(rows[ARGUMENTS.size()]));assertEquals("dependency-中文",fromBase64(rows[ARGUMENTS.size()+1]));
            String logicalClasspath=fromBase64(rows[ARGUMENTS.size()+2]);assertTrue(logicalClasspath.contains(mode.equals("JAR")?fixture.jar().toString():mode.equals("CLASS")?fixture.classes().toString():"compiled-source"));
            if(target instanceof JavaUtf8Invocation.ClassTarget classes)assertEquals(String.join(java.io.File.pathSeparator,classes.classpath().stream().map(JavaUtf8Invocation.ClasspathPin::path).toList()),logicalClasspath);
            var actualProof=JavaUtf8Invocation.captureFile(JavaUtf8Invocation.preparationPath(request));var prepared=JavaUtf8Invocation.inspectPreparation(actualProof,publication);
            assertEquals(publication.envelope(),prepared.envelope());assertEquals(mode,prepared.mode());assertEquals("UnicodeMain",prepared.mainClass());
            assertEquals(mode.equals("SOURCE"),!prepared.compiledClasses().isEmpty());
            if(target instanceof JavaUtf8Invocation.JarTarget jar)assertEquals(jar.manifestClasspath(),prepared.effectiveClasspath());
            Path copied=evidence.resolve("copied-invocation.bin");Files.copy(Path.of(publication.envelope().path()),copied);var copiedPublication=new JavaUtf8Invocation.Publication(JavaUtf8Invocation.captureFile(copied));
            assertThrows(IOException.class,()->JavaUtf8Invocation.inspectPreparation(actualProof,copiedPublication));
            assertThrows(IOException.class,()->JavaUtf8Invocation.publish(request,request.evidenceRoot(),"occupied.bin",pending->{}));assertFalse(Files.exists(evidence.resolve("occupied.bin")));
        }
    }

    @Test void actualBootstrapProducerPreservesFixturePathsAndItsOriginalPinnedRuntime()throws Exception {
        Fixture fixture=fixture();Path evidence=Files.createDirectory(temporary.resolve("bootstrap-proof"));Path request=temporary.resolve("中文请求.json");Files.writeString(request,"{}",StandardCharsets.UTF_8);
        Path plan=temporary.resolve("原计划.json");Files.writeString(plan,"{}",StandardCharsets.UTF_8);
        // Producer argument/pin regression only: these owned fixture jars do not qualify or execute a tools bundle.
        // Physical carrier paths remain ASCII in both standalone and Maven target/classes runs.
        Path carrierRoot=Files.createDirectory(temporary.resolve("bootstrap-carrier"));
        Path dependencyJar=carrierRoot.resolve("dependency.jar");jar(dependencyJar,new Manifest(),fixture.dependencies());
        var carrierManifest=new Manifest();carrierManifest.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION,"1.0");
        carrierManifest.getMainAttributes().put(Attributes.Name.MAIN_CLASS,"UnicodeMain");carrierManifest.getMainAttributes().put(Attributes.Name.CLASS_PATH,"dependency.jar");
        Path primaryJar=carrierRoot.resolve("primary.jar");jar(primaryJar,carrierManifest,fixture.classes());
        var runtime=List.of(pin(primaryJar),pin(dependencyJar));
        var launch=CiBootstrap.qualifiedInvocation(runtime,plan,pin(request),evidence,temporary,pending->assertTrue(pending>0));
        var target=(JavaUtf8Invocation.ClassTarget)launch.logicalRequest().target();
        assertEquals("org.xar.ck3.control.build.ControlCi",target.mainClass());assertEquals(runtime.getFirst().path(),target.mainOrigin().path());
        assertEquals(List.of("--bootstrap-plan",plan.toString(),"--fixture-production-request",request.toString(),"2",pin(request).sha256()),launch.logicalRequest().arguments());
        var consumed=ControlCi.invocation(launch.logicalRequest().arguments().toArray(String[]::new));
        assertEquals(plan.toRealPath(),consumed.planPath());
        assertEquals(ControlBuild.FileRef.measure(request),consumed.fixtureProductionRequestRef());
        assertNull(consumed.fixtureRequestRef());
        assertEquals(launch.logicalRequest(),JavaUtf8Invocation.read(launch.publication()));

        Path plannedEvidence=Files.createDirectory(temporary.resolve("bootstrap-planned-proof"));
        var planned=CiBootstrap.qualifiedInvocation(runtime,plan,null,pin(request),plannedEvidence,temporary,pending->assertTrue(pending>0));
        assertEquals(List.of("--bootstrap-plan",plan.toString(),"--planned-fixture-production-request",
                request.toString(),"2",pin(request).sha256()),planned.logicalRequest().arguments());
        var plannedConsumer=ControlCi.invocation(planned.logicalRequest().arguments().toArray(String[]::new));
        assertEquals(ControlBuild.FileRef.measure(request),plannedConsumer.plannedFixtureProductionRequestRef());
        assertNull(plannedConsumer.fixtureRequestRef());assertNull(plannedConsumer.fixtureProductionRequestRef());
        assertEquals(planned.logicalRequest(),JavaUtf8Invocation.read(planned.publication()));
        assertTrue(planned.physicalArguments().stream().allMatch(value->value.codePoints().allMatch(code->code>=32&&code<=126)));
        assertThrows(IllegalArgumentException.class,()->CiBootstrap.qualifiedInvocation(runtime,plan,pin(request),pin(request),
                plannedEvidence,temporary,pending->{}));
        Files.writeString(dependencyJar,"changed");assertThrows(IOException.class,()->CiBootstrap.qualifiedInvocation(runtime,plan,pin(request),evidence,temporary,pending->{}));
    }

    @Test void classpathDependenciesIgnoreModuleLauncherAttributesButExecutableJarRootsStillRejectThem()throws Exception {
        Fixture fixture=fixture();
        for(String attribute:List.of("Add-Exports","Add-Opens","Enable-Native-Access")) {
            var dependencyManifest=new Manifest();
            dependencyManifest.getMainAttributes().put(Attributes.Name.MAIN_CLASS,"UnicodeDependency");
            dependencyManifest.getMainAttributes().putValue(attribute,attribute.equals("Enable-Native-Access")?"ALL-UNNAMED":"java.base/java.lang");
            Path dependency=temporary.resolve(attribute+"-dependency.jar");jar(dependency,dependencyManifest,fixture.dependencies());
            var actual=(JavaUtf8Invocation.JarClasspath)JavaUtf8Invocation.captureClasspath(dependency);
            assertEquals(List.of(new JavaUtf8Invocation.FileClasspath(JavaUtf8Invocation.captureFile(dependency))),actual.manifestClasspath());
            IOException rejected=assertThrows(IOException.class,()->JavaUtf8Invocation.captureJar(dependency));
            assertTrue(rejected.getMessage().contains(attribute));
            var applicationManifest=new Manifest();applicationManifest.getMainAttributes().put(Attributes.Name.MAIN_CLASS,"UnicodeMain");
            applicationManifest.getMainAttributes().put(Attributes.Name.CLASS_PATH,dependency.getFileName().toString());
            Path application=temporary.resolve(attribute+"-application.jar");jar(application,applicationManifest,fixture.classes());
            var target=JavaUtf8Invocation.captureJar(application);
            assertEquals(List.of(application.toRealPath().toString(),dependency.toRealPath().toString()),
                    target.manifestClasspath().stream().map(JavaUtf8Invocation.ClasspathPin::path).toList());
        }
    }

    @Test void classpathAgentAndBootDeclarationsAndRemoteManifestDependenciesRemainRejected()throws Exception {
        Fixture fixture=fixture();
        for(String attribute:List.of("Launcher-Agent-Class","Boot-Class-Path")) {
            var manifest=new Manifest();manifest.getMainAttributes().put(Attributes.Name.MAIN_CLASS,"UnicodeDependency");
            manifest.getMainAttributes().putValue(attribute,attribute.equals("Launcher-Agent-Class")?"UnexpectedAgent":"unexpected.jar");
            Path dependency=temporary.resolve(attribute+"-blocked.jar");jar(dependency,manifest,fixture.dependencies());
            assertThrows(IOException.class,()->JavaUtf8Invocation.captureClasspath(dependency));
            assertThrows(IOException.class,()->JavaUtf8Invocation.captureJar(dependency));
        }
        var remote=new Manifest();remote.getMainAttributes().put(Attributes.Name.CLASS_PATH,"https://invalid.example/remote.jar");
        Path dependency=temporary.resolve("remote-dependency.jar");jar(dependency,remote,fixture.dependencies());
        assertThrows(IOException.class,()->JavaUtf8Invocation.captureClasspath(dependency));
    }

    @Test void ignoredNativeAccessMetadataDoesNotWeakenPinnedManifestDependencyCustody()throws Exception {
        Fixture fixture=fixture();var origin=JavaUtf8Invocation.captureClasspath(fixture.classes());
        var dependency=JavaUtf8Invocation.captureClasspath(fixture.dependencyJar());
        Path evidence=Files.createDirectory(temporary.resolve("ignored-native-proof"));
        var request=new JavaUtf8Invocation.Request(new JavaUtf8Invocation.ClassTarget("UnicodeMain",origin,List.of(origin,dependency)),
                List.of(),ARGUMENTS,JavaUtf8Invocation.captureOutputRoot(evidence));
        var publication=JavaUtf8Invocation.publish(request,request.evidenceRoot(),"native-attribute.bin",pending->{});
        var launch=JavaUtf8Invocation.launch(publication,carrier(),vm());
        assertEquals(request,JavaUtf8Invocation.inspect(launch.physicalArguments(),carrier(),vm()));
        Files.writeString(fixture.dependencyJar(),"changed after publication",StandardCharsets.UTF_8);
        assertThrows(IOException.class,()->JavaUtf8Invocation.launch(publication,carrier(),vm()));
    }

    @Test void strictBinaryAndPhysicalReadersRejectWrongVersionTrailingMalformedUtf8AndChangedWitnesses()throws Exception {
        Fixture fixture=fixture();var origin=JavaUtf8Invocation.captureClasspath(fixture.classes());var dependency=JavaUtf8Invocation.captureClasspath(fixture.dependencies());
        var request=new JavaUtf8Invocation.Request(new JavaUtf8Invocation.ClassTarget("UnicodeMain",origin,List.of(origin,dependency)),List.of(),ARGUMENTS,JavaUtf8Invocation.captureOutputRoot(temporary));
        byte[] raw=JavaUtf8Invocation.encode(request);assertEquals(request,JavaUtf8Invocation.decode(raw));
        Path actualExecutable=Path.of(System.getProperty("java.home"),"bin/java.exe");
        long terminalAllowance=JavaUtf8NativeCustody.evidenceUpperBound(1,actualExecutable)-1;
        assertEquals(JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES,JavaUtf8NativeCustody.evidenceUpperBound(JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES-terminalAllowance,actualExecutable));
        assertThrows(IOException.class,()->JavaUtf8NativeCustody.evidenceUpperBound(JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES-terminalAllowance+1,actualExecutable));
        assertThrows(IOException.class,()->JavaUtf8NativeCustody.evidenceUpperBound(Long.MAX_VALUE,actualExecutable));
        assertThrows(IOException.class,()->JavaUtf8NativeCustody.evidenceUpperBound(0,actualExecutable));
        var jdkPin=JavaUtf8Invocation.captureFile(fixture.source());assertEquals(JavaUtf8Invocation.WitnessScope.JDK_METADATA_AND_CONTENT,jdkPin.witnessScope());
        var absent=new JavaUtf8Invocation.PinnedFile(jdkPin.path(),jdkPin.bytes(),jdkPin.sha256(),new JavaUtf8Invocation.JdkFileMetadata(jdkPin.metadata().createdAt(),jdkPin.metadata().modifiedAt(),java.util.Optional.empty()));
        assertEquals(JavaUtf8Invocation.WitnessScope.JDK_METADATA_AND_CONTENT,absent.witnessScope());
        byte[] legacy=raw.clone();legacy[7]=1;assertThrows(IOException.class,()->JavaUtf8Invocation.decode(legacy));
        byte[] wrong=raw.clone();wrong[7]=3;assertThrows(IOException.class,()->JavaUtf8Invocation.decode(wrong));
        assertThrows(IOException.class,()->JavaUtf8Invocation.decode(Arrays.copyOf(raw,raw.length+1)));
        assertThrows(IOException.class,()->JavaUtf8Invocation.decode(Arrays.copyOf(raw,raw.length-1)));
        byte[] malformed=raw.clone();malformed[13]=(byte)0xff;assertThrows(IOException.class,()->JavaUtf8Invocation.decode(malformed));
        assertThrows(IllegalArgumentException.class,()->new JavaUtf8Invocation.Property("java.io.tmpdir","中文"));
        var invalid=new JavaUtf8Invocation.Request(request.target(),List.of(),List.of("\ud800"),request.evidenceRoot());assertThrows(IOException.class,()->JavaUtf8Invocation.encode(invalid));
        var publication=JavaUtf8Invocation.publish(request,request.evidenceRoot(),"strict.bin",pending->{});var carrier=carrier();var launch=JavaUtf8Invocation.launch(publication,carrier,vm());
        var changed=new ArrayList<>(launch.physicalArguments());changed.set(0,"-Xmx32m");assertThrows(IOException.class,()->JavaUtf8Invocation.inspect(changed,carrier,vm()));
        assertThrows(IOException.class,()->JavaUtf8Invocation.launch(publication,carrier,List.of("-version")));
        assertThrows(IOException.class,()->JavaUtf8Invocation.launch(publication,carrier,List.of("-Djava.io.tmpdir=中文")));
        try(var nativeInputs=JavaUtf8NativeCustody.acquire(launch,carrier)){
            nativeInputs.requireCurrent();
            assertThrows(IOException.class,()->Files.writeString(fixture.classes().resolve("UnicodeMain.class"),"tamper"));
            Path renamed=fixture.classes().resolveSibling("renamed");assertThrows(IOException.class,()->Files.move(fixture.classes(),renamed));
        }
        Files.writeString(fixture.classes().resolve("extra.class"),"changed");assertThrows(IOException.class,()->JavaUtf8Invocation.launch(publication,carrier,vm()));
        Files.write(Path.of(publication.envelope().path()),raw,java.nio.file.StandardOpenOption.APPEND);assertThrows(IOException.class,()->JavaUtf8Invocation.read(publication));
    }

    private record Fixture(Path source,Path classes,Path dependencies,Path jar,Path dependencyJar) { }
    private Fixture fixture()throws Exception {
        Path logical=Files.createDirectories(temporary.resolve("逻辑 中文 Ω 😀"));Path dependencies=Files.createDirectory(logical.resolve("依赖类"));Path classes=Files.createDirectory(logical.resolve("业务类"));
        Path dependency=logical.resolve("UnicodeDependency.java");Files.writeString(dependency,"public class UnicodeDependency { public static String value(){return \"dependency-中文\";} }",StandardCharsets.UTF_8);
        var compiler=javax.tools.ToolProvider.getSystemJavaCompiler();assertNotNull(compiler);assertEquals(0,compiler.run(null,null,null,"-encoding","UTF-8","-proc:none","-d",dependencies.toString(),dependency.toString()));
        Path source=logical.resolve("UnicodeMain.java");Files.writeString(source,"""
                public class UnicodeMain {
                  public static void main(String[] args) throws Exception {
                    if(args.length==1&&args[0].equals("--fail42")){System.exit(42);return;}
                    var values=new java.util.ArrayList<String>(java.util.List.of(args));
                    values.add(System.getProperty("xar.unicode.test"));values.add(UnicodeDependency.value());values.add(System.getProperty("java.class.path"));
                    for(String value:values){System.out.write(java.util.Base64.getEncoder().encode(value.getBytes(java.nio.charset.StandardCharsets.UTF_8)));System.out.write('\\n');}
                    System.out.flush();
                  }
                }
                """,StandardCharsets.UTF_8);
        assertEquals(0,compiler.run(null,null,null,"-encoding","UTF-8","-proc:none","-cp",dependencies.toString(),"-d",classes.toString(),source.toString()));
        // Reproduce the actual Aesh terminal-tty dependency manifest from the complete Root runtime.
        // Its launcher-only native-access attribute is ignored when this JAR is a classpath dependency.
        var dependencyManifest=new Manifest();dependencyManifest.getMainAttributes().putValue("Enable-Native-Access","ALL-UNNAMED");
        Path dependencyJar=logical.resolve("依赖.jar");jar(dependencyJar,dependencyManifest,dependencies);
        var manifest=new Manifest();manifest.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION,"1.0");manifest.getMainAttributes().put(Attributes.Name.MAIN_CLASS,"UnicodeMain");
        manifest.getMainAttributes().put(Attributes.Name.CLASS_PATH,new java.net.URI(null,null,dependencyJar.getFileName().toString(),null).toASCIIString());
        Path mainJar=logical.resolve("业务.jar");jar(mainJar,manifest,classes);return new Fixture(source,classes,dependencies,mainJar,dependencyJar);
    }
    private static void jar(Path destination,Manifest manifest,Path classes)throws IOException {
        if(manifest.getMainAttributes().getValue(Attributes.Name.MANIFEST_VERSION)==null)manifest.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION,"1.0");
        try(var jar=new JarOutputStream(Files.newOutputStream(destination),manifest);var files=Files.walk(classes)){
            for(Path file:files.filter(Files::isRegularFile).sorted().toList()){jar.putNextEntry(new JarEntry(classes.relativize(file).toString().replace('\\','/')));Files.copy(file,jar);jar.closeEntry();}
        }
    }
    static JavaUtf8Invocation.ClassCarrier carrier()throws IOException {
        String raw=System.getProperty("surefire.test.class.path",System.getProperty("java.class.path"));var pins=new ArrayList<JavaUtf8Invocation.ClasspathPin>();
        for(String path:raw.split(java.util.regex.Pattern.quote(java.io.File.pathSeparator)))pins.add(JavaUtf8Invocation.captureClasspath(Path.of(path)));
        return new JavaUtf8Invocation.ClassCarrier(pins);
    }
    private List<String> vm(){return List.of("-Xms16m","-Xmx96m","-XX:MaxMetaspaceSize=96m","-XX:ReservedCodeCacheSize=32m","-Djava.io.tmpdir="+temporary,"-Djna.tmpdir="+temporary);}
    private static CiBootstrap.FilePin pin(Path path)throws IOException {var pin=JavaUtf8Invocation.captureFile(path);return new CiBootstrap.FilePin(pin.path(),pin.bytes(),pin.sha256());}
    private static Path bootstrapSource()throws IOException {
        for(Path path:List.of(Path.of("src/main/java/org/xar/ck3/control/build/CiBootstrap.java"),Path.of("java/ck3-control/build-tools/src/main/java/org/xar/ck3/control/build/CiBootstrap.java")))if(Files.isRegularFile(path))return path.toRealPath();
        throw new IOException("Actual selected single-source CiBootstrap is required; this test cannot substitute another entry");
    }
    private static String fromBase64(String value){return new String(java.util.Base64.getDecoder().decode(value),StandardCharsets.UTF_8);}
    private static String readQuietly(Path path){try{return Files.readString(path,StandardCharsets.UTF_8);}catch(IOException error){return error.toString();}}
}
