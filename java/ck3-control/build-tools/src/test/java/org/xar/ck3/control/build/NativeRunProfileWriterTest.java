package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Strict explicit routing and real unqualified-source rejection; no fake deployment, issuer or positive. */
final class NativeRunProfileWriterTest {
    @TempDir Path temporary;
    @Test void exactInputsRouteBothExplicitModesToTheOriginalGuardedCommand()throws Exception{
        for(var mode:NativeRunProfileWriter.Mode.values()){
            var arguments=arguments(mode);var invocation=NativeRunProfileWriter.argument(arguments);
            assertEquals(mode,invocation.mode());
            assertEquals(List.of(arguments),invocation.exactArguments());
            assertEquals(invocation,NativeRunProfileWriter.argument(invocation.exactArguments().toArray(String[]::new)));
            assertEquals(new FileRef(arguments[1],7,arguments[3]),invocation.request());
            assertEquals(new FileRef(arguments[4],9,arguments[6]),invocation.bootstrapBuild());
            assertEquals(List.of(mode.name(),arguments[1],"7",arguments[3]),invocation.originalArguments());
            assertThrows(UnsupportedOperationException.class,()->invocation.originalArguments().add("--skip-guard"));
        }
        assertEquals("org.xar.ck3.control.service.root.RootProfileBootstrapCommand",NativeRunProfileWriter.ORIGINAL_MAIN);
    }
    @Test void commandRejectsMissingModeAliasesExtraCoercedAndUnboundedExactReferences()throws Exception{
        for(int index:List.of(2,5))for(String invalid:List.of("0","07","+7","7.0","true","-1","4194305")){
            var arguments=arguments(NativeRunProfileWriter.Mode.FORMAL_RELEASE);arguments[index]=invalid;
            assertThrows(IOException.class,()->NativeRunProfileWriter.argument(arguments));
        }
        var tooLarge=arguments(NativeRunProfileWriter.Mode.FORMAL_RELEASE);tooLarge[2]="65537";
        assertThrows(IOException.class,()->NativeRunProfileWriter.argument(tooLarge));
        assertThrows(IOException.class,()->NativeRunProfileWriter.argument(new String[0]));
        var relative=arguments(NativeRunProfileWriter.Mode.PROFILE);relative[1]="relative-request.json";
        assertThrows(IOException.class,()->NativeRunProfileWriter.argument(relative));
        var extra=java.util.Arrays.copyOf(arguments(NativeRunProfileWriter.Mode.PROFILE),8);extra[7]="SKIP";
        assertThrows(IOException.class,()->NativeRunProfileWriter.argument(extra));
        var wrongHash=arguments(NativeRunProfileWriter.Mode.PROFILE);wrongHash[6]="placeholder";
        assertThrows(IOException.class,()->NativeRunProfileWriter.argument(wrongHash));
        for(String wrongMode:List.of("profile","FORMAL","SAVED_PROFILE","PROFILE_STAGING","")){
            var arguments=arguments(NativeRunProfileWriter.Mode.PROFILE);arguments[0]=wrongMode;
            assertThrows(IOException.class,()->NativeRunProfileWriter.argument(arguments));
        }
        var oldImplicit=java.util.Arrays.copyOfRange(arguments(NativeRunProfileWriter.Mode.PROFILE),1,7);
        assertThrows(IOException.class,()->NativeRunProfileWriter.argument(oldImplicit));
    }
    @Test void publicInvocationCannotBypassTheSameBoundsAsTheActualCommand()throws Exception{
        var arguments=arguments(NativeRunProfileWriter.Mode.FORMAL_RELEASE);var request=new FileRef(arguments[1],7,arguments[3]);
        assertThrows(IllegalArgumentException.class,()->new NativeRunProfileWriter.Invocation(NativeRunProfileWriter.Mode.FORMAL_RELEASE,
                new FileRef(arguments[1],65537,arguments[3]),new FileRef(arguments[4],9,arguments[6])));
        assertThrows(IllegalArgumentException.class,()->new NativeRunProfileWriter.Invocation(NativeRunProfileWriter.Mode.FORMAL_RELEASE,request,
                new FileRef(arguments[4],ControlBuild.BUILD_RECEIPT_ENVELOPE_MAX_BYTES+1L,arguments[6])));
    }
    @Test void realUnqualifiedBuildNeverLoadsEitherBootstrapOrWritesOutputs()throws Exception{
        Path request=Files.writeString(temporary.resolve("bootstrap-request.json"),"{}");
        Path unqualified=Files.writeString(temporary.resolve("not-completed-host-build.json"),"{}");
        for(var mode:NativeRunProfileWriter.Mode.values()){
            var invocation=new NativeRunProfileWriter.Invocation(mode,FileRef.measure(request),FileRef.measure(unqualified));
            assertThrows(IOException.class,()->NativeRunProfileWriter.write(invocation));
        }
        assertEquals("{}",Files.readString(request));assertEquals("{}",Files.readString(unqualified));
        try(var files=Files.list(temporary)){assertEquals(2,files.count());}
    }
    @Test void formalModeRequiresTheExactProducerSchemaAndGitClassesInTheSameActualDeployment(){
        List<String> ordinary=NativeRunProfileWriter.requiredClasses(NativeRunProfileWriter.Mode.PROFILE);
        List<String> formal=NativeRunProfileWriter.requiredClasses(NativeRunProfileWriter.Mode.FORMAL_RELEASE);
        assertTrue(formal.containsAll(ordinary));
        for(Class<?> type:List.of(FormalReleaseProducer.class,FormalReleaseGit.class,FormalReleaseDescriptor.class,NativeRunProfileManifest.class))
            assertTrue(formal.contains(type.getName()));
        assertEquals(ordinary.size()+4,formal.size());
        assertThrows(UnsupportedOperationException.class,()->formal.add("other"));
    }
    private String[] arguments(NativeRunProfileWriter.Mode mode){
        return new String[]{mode.name(),temporary.resolve("actual-bootstrap-request.json").toString(),"7","a".repeat(64),
                temporary.resolve("actual-host-build.json").toString(),"9","b".repeat(64)};
    }
}

