package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.CiBootstrap.JavaUtf8Invocation;

/** Real caller/envelope/reader and one failing Java main before any UAC request; no Native registration qualification. */
final class NativeFixtureRegistrationInvocationTest {
    @TempDir Path temporary;

    private record Fixture(JavaUtf8Invocation.ClassTarget target, JavaUtf8Invocation.DirectoryIdentity root,
            ControlBuild.FileRef plan, String deadline) { }

    private Fixture fixture(String name, boolean unicode) throws Exception {
        Path root=temporary.resolve(name);Files.createDirectory(root);
        Path plans=root.resolve("plans");Files.createDirectory(plans);
        Path plan=plans.resolve(unicode ? "计划-β-é-😀.json" : "original-plan.json");
        Files.writeString(plan,"{",StandardCharsets.UTF_8,
                StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
        Path origin=Path.of(NativeProjectExeUac.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        List<JavaUtf8Invocation.ClasspathPin> classpath=new ArrayList<>();
        var mainOrigin=JavaUtf8Invocation.captureClasspath(origin);classpath.add(mainOrigin);
        var seen=new LinkedHashSet<Path>();seen.add(origin.toRealPath());
        for(var pin:JavaUtf8InvocationTest.carrier().classpath()){
            Path file=Path.of(pin.path()).toRealPath();
            if(seen.add(file))classpath.add(pin);
        }
        return new Fixture(new JavaUtf8Invocation.ClassTarget(NativeProjectExeUac.class.getName(),mainOrigin,classpath),
                JavaUtf8Invocation.captureOutputRoot(root),ControlBuild.FileRef.measure(plan),Instant.now().plusSeconds(120).toString());
    }

    @Test void realCallerPublishesUnicodeArgumentsForTheSoleReaderWithoutChangingLogicalStageInputs() throws Exception {
        Fixture f=fixture("roundtrip",true);AtomicLong quoted=new AtomicLong();
        var launch=NativeFixtureBuild.registrationInvocation(f.target(),f.root(),f.plan(),f.deadline(),pending->{
            if(pending<=0 || pending>((8L<<20)+8192))throw new IOException("finite owned test envelope budget exceeded");
            quoted.accumulateAndGet(pending,Math::max);
        });
        assertTrue(quoted.get()>0);assertTrue(launch.physicalArguments().stream().allMatch(value->value.chars().allMatch(c->c<128)));
        assertFalse(launch.physicalArguments().contains(f.plan().path()));
        var carrier=new JavaUtf8Invocation.ClassCarrier(f.target().classpath());
        var actual=JavaUtf8Invocation.inspect(launch.physicalArguments(),carrier,
                NativeFixtureBuild.registrationVmOptions(Path.of(f.root().path())));
        NativeFixtureBuild.requireRegistrationRequest(actual,f.target(),f.root(),f.plan(),f.deadline());
        assertEquals(List.of("execute-approved-plan",f.plan().path(),f.plan().sha256(),f.deadline()),actual.arguments());
        assertEquals(launch.logicalRequest(),actual);
        List<String> wrong=new ArrayList<>(actual.arguments());wrong.set(0,"review");
        var wrongMode=new JavaUtf8Invocation.Request(actual.target(),actual.properties(),wrong,actual.evidenceRoot());
        assertThrows(IOException.class,()->NativeFixtureBuild.requireRegistrationRequest(wrongMode,f.target(),f.root(),f.plan(),f.deadline()));
        var wrongProperty=new JavaUtf8Invocation.Request(actual.target(),List.of(new JavaUtf8Invocation.Property("xar.extra","不允许")),actual.arguments(),actual.evidenceRoot());
        assertThrows(IOException.class,()->NativeFixtureBuild.requireRegistrationRequest(wrongProperty,f.target(),f.root(),f.plan(),f.deadline()));
        var otherTarget=new JavaUtf8Invocation.ClassTarget(NativeFixtureBuild.class.getName(),f.target().mainOrigin(),f.target().classpath());
        var wrongMain=new JavaUtf8Invocation.Request(otherTarget,List.of(),actual.arguments(),actual.evidenceRoot());
        assertThrows(IOException.class,()->NativeFixtureBuild.requireRegistrationRequest(wrongMain,f.target(),f.root(),f.plan(),f.deadline()));
    }

    @Test void deniedEnvelopeWriteAndMutatedOriginalCannotBeReinterpretedAsAnAcceptedInvocation() throws Exception {
        Fixture denied=fixture("denied",true);
        assertThrows(IOException.class,()->NativeFixtureBuild.registrationInvocation(denied.target(),denied.root(),denied.plan(),denied.deadline(),
                pending->{throw new IOException("owned test output budget denied");}));
        assertFalse(Files.exists(Path.of(denied.root().path()).resolve("DEFENDER-JAVA-INVOCATION01.bin")));
        Fixture f=fixture("mutation",true);
        var launch=NativeFixtureBuild.registrationInvocation(f.target(),f.root(),f.plan(),f.deadline(),NativeFixtureRegistrationInvocationTest::requireTestOutput);
        Path envelope=Path.of(launch.publication().envelope().path());byte[] wire=Files.readAllBytes(envelope);wire[0]^=1;Files.write(envelope,wire);
        assertThrows(IOException.class,()->JavaUtf8Invocation.inspect(launch.physicalArguments(),
                new JavaUtf8Invocation.ClassCarrier(f.target().classpath()),NativeFixtureBuild.registrationVmOptions(Path.of(f.root().path()))));
    }

    @Test void actualJavaChildReadsUnicodePlanThenNaturallyRejectsBeforeAnyUacApi() throws Exception {
        Fixture f=fixture("physical",true);Path root=Path.of(f.root().path());
        var launch=NativeFixtureBuild.registrationInvocation(f.target(),f.root(),f.plan(),f.deadline(),NativeFixtureRegistrationInvocationTest::requireTestOutput);
        Path java=Path.of(System.getProperty("java.home"),"bin","java.exe").toRealPath();
        Path stdout=root.resolve("java.stdout"),stderr=root.resolve("java.stderr");
        var environment=new HashMap<>(System.getenv());
        for(String key:List.of("TEMP","TMP","TMPDIR"))environment.put(key,root.toString());
        WindowsJobProcess.CommandResult result;
        JavaUtf8NativeCustody.Evidence nativeSources;
        SharedSourceFiles.Witness preparationWitness;
        var carrier=new JavaUtf8Invocation.ClassCarrier(f.target().classpath());
        try(var held=JavaUtf8NativeCustody.acquire(launch,carrier)){
            held.requireCurrent();long quoted=held.maximumEvidenceBytes(java);
            try(var child=WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(java,launch.physicalArguments(),root,
                    environment,stdout,stderr,512L<<20),WindowsJobProcess.ConsoleMode.NO_WINDOW)){
                held.attach(child);
                result=child.await(Duration.ofSeconds(30),Instant.now().plusSeconds(45),held.guard(()->{ }));
                nativeSources=held.verifyTerminal(result).evidence();
                assertTrue(JavaUtf8NativeCustody.encodeEvidence(nativeSources).length<=quoted);
                preparationWitness=NativeFixtureBuild.registrationPreparationWitness(launch);
                NativeFixtureBuild.requireRegistrationSources(launch,carrier,result,preparationWitness,nativeSources);
            }
        }
        assertEquals(nativeSources,JavaUtf8NativeCustody.decodeEvidence(JavaUtf8NativeCustody.encodeEvidence(nativeSources)));
        assertEquals(preparationWitness,ControlBuild.strictMapper().readValue(
                ControlBuild.strictMapper().writeValueAsBytes(preparationWitness),SharedSourceFiles.Witness.class));
        NativeFixtureBuild.requireRegistrationSources(launch,carrier,result,preparationWitness,nativeSources);
        assertThrows(IOException.class,()->{
            var missingWitness=ControlBuild.strictMapper().readValue("{}",SharedSourceFiles.Witness.class);
            NativeFixtureBuild.requireRegistrationSources(launch,carrier,result,missingWitness,nativeSources);
        });
        var alteredTerminal=new WindowsJobProcess.CommandResult(result.identity(),0,result.elapsedSeconds(),result.accounting(),null);
        assertThrows(IOException.class,()->NativeFixtureBuild.requireRegistrationSources(launch,carrier,alteredTerminal,preparationWitness,nativeSources));
        assertEquals(1,result.exitCode());assertNull(result.stopReason());assertEquals(0,result.accounting().activeProcesses());
        assertEquals(8704,result.accounting().limitFlags());assertTrue(result.accounting().peakJobMemoryBytes()<=result.accounting().memoryLimitBytes());
        String error=Files.readString(stderr,StandardCharsets.UTF_8);
        assertTrue(error.contains("JsonEOFException") || error.contains("Unexpected end-of-input"),error);
        assertFalse(error.contains("NoSuchFileException"),error);
        Path preparationPath=JavaUtf8Invocation.preparationPath(launch.logicalRequest());
        var preparationPin=JavaUtf8Invocation.captureFile(preparationPath);
        var preparation=JavaUtf8Invocation.inspectPreparation(preparationPin,launch.publication());
        assertEquals(NativeProjectExeUac.class.getName(),preparation.mainClass());
        assertEquals(launch.publication().envelope(),preparation.envelope());
        record Observation(String schema,String machineId,String observedAtUtc,WindowsJobProcess.CommandResult terminal,
                ControlBuild.FileRef plan,ControlBuild.FileRef invocation,SharedSourceFiles.Witness preparation,
                JavaUtf8NativeCustody.Evidence nativeSources,ControlBuild.FileRef stdout,ControlBuild.FileRef stderr) { }
        var actual=new Observation("xar.native-fixture-registration-utf8-negative-main/v2",WindowsJobProcess.currentMachineId(),Instant.now().toString(),
                result,f.plan(),ControlBuild.FileRef.measure(Path.of(launch.publication().envelope().path())),
                preparationWitness,nativeSources,ControlBuild.FileRef.measure(stdout),ControlBuild.FileRef.measure(stderr));
        Files.write(root.resolve("actual-java-negative-main.json"),ControlBuild.strictMapper().writeValueAsBytes(actual),StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
        byte[] originalPreparation=Files.readAllBytes(preparationPath);byte[] changedPreparation=originalPreparation.clone();
        changedPreparation[0]^=1;Files.write(preparationPath,changedPreparation);
        assertThrows(IOException.class,()->JavaUtf8Invocation.inspectPreparation(preparationPin,launch.publication()));
        assertThrows(IOException.class,()->NativeFixtureBuild.requireRegistrationSources(launch,carrier,result,preparationWitness,nativeSources));
    }

    @Test void nativeCustodyActuallyBlocksEnvelopeWritesAndReplacementWithoutStartingAChild() throws Exception {
        Fixture f=fixture("native-lock",true);
        var launch=NativeFixtureBuild.registrationInvocation(f.target(),f.root(),f.plan(),f.deadline(),NativeFixtureRegistrationInvocationTest::requireTestOutput);
        var carrier=new JavaUtf8Invocation.ClassCarrier(f.target().classpath());Path envelope=Path.of(launch.publication().envelope().path());
        byte[] original=Files.readAllBytes(envelope);
        NativeFixtureBuild.requireRegistrationSourceOutputsAbsent(launch);
        try(var held=JavaUtf8NativeCustody.acquire(launch,carrier)){
            held.requireCurrent();
            assertThrows(IOException.class,()->Files.write(envelope,original,StandardOpenOption.WRITE));
            assertThrows(IOException.class,()->Files.move(envelope,envelope.resolveSibling("moved-original.bin"),java.nio.file.StandardCopyOption.ATOMIC_MOVE));
            held.requireCurrent();
        }
        assertArrayEquals(original,Files.readAllBytes(envelope));
        Path unknown=JavaUtf8Invocation.preparationPath(launch.logicalRequest());
        Files.writeString(unknown,"unknown original output",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        var unknownRef=ControlBuild.FileRef.measure(unknown);
        assertThrows(IOException.class,()->NativeFixtureBuild.requireRegistrationSourceOutputsAbsent(launch));
        unknownRef.verify();
        NativeFixtureBuild.requireRegistrationRequest(JavaUtf8Invocation.inspect(launch.physicalArguments(),carrier,
                NativeFixtureBuild.registrationVmOptions(Path.of(f.root().path()))),f.target(),f.root(),f.plan(),f.deadline());
    }

    @Test void onlyTheOriginalAsciiClassShapeRemainsAHistoricalReaderBranch() throws Exception {
        Fixture f=fixture("history",false);
        List<String> command=new ArrayList<>();command.add("C:/historical-exact-runtime/java.exe");
        command.addAll(NativeFixtureBuild.registrationVmOptions(Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1/scratch")));
        command.addAll(List.of("-cp","C:/historical-tools/original.jar",NativeProjectExeUac.class.getName()));
        command.addAll(NativeFixtureBuild.registrationLogicalArguments(f.plan(),f.deadline()));
        assertTrue(NativeFixtureBuild.historicalRegistrationCommand(command,f.plan(),f.deadline()));
        List<String> wrong=new ArrayList<>(command);wrong.set(10,NativeFixtureBuild.class.getName());
        assertFalse(NativeFixtureBuild.historicalRegistrationCommand(wrong,f.plan(),f.deadline()));
        wrong=new ArrayList<>(command);wrong.add("extra");assertFalse(NativeFixtureBuild.historicalRegistrationCommand(wrong,f.plan(),f.deadline()));
        wrong=new ArrayList<>(command);wrong.set(9,"C:/历史/old.jar");assertFalse(NativeFixtureBuild.historicalRegistrationCommand(wrong,f.plan(),f.deadline()));
        Fixture unicode=fixture("history-unicode",true);
        assertFalse(NativeFixtureBuild.historicalRegistrationCommand(command,unicode.plan(),f.deadline()));
    }

    private static void requireTestOutput(long pending) throws IOException {
        if(pending<=0 || pending>((8L<<20)+8192))throw new IOException("finite owned test envelope budget exceeded");
    }
}
