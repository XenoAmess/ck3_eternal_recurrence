package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Locale;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;

/** Measured file digest DATA only: no Loaded/Received, process, Native or Root capability is constructed. */
final class RootLoadedExecutableBuildIdentityTest {
    @TempDir Path directory;
    private static final String MACHINE="loaded-digest-software-fixture";
    private static final Instant OLD=Instant.parse("2026-11-15T01:00:00Z"),NOW=Instant.parse("2026-11-16T01:00:00Z");
    private ControlBuild.FileRef file(String name,String bytes)throws IOException {
        Path path=directory.resolve(name);Files.writeString(path,bytes);return ControlBuild.FileRef.measure(path);
    }
    private static ExactRef exact(ControlBuild.FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static G2Source historical(String build,ExactRef source){return new G2Source(MACHINE,OLD.toString(),build,source);}
    private static String mixed(String digest){
        var result=new StringBuilder(digest);int letters=0;
        for(int index=0;index<result.length();index++){
            char value=result.charAt(index);
            if(value>='a'&&value<='f'&&(letters++%2)==0)result.setCharAt(index,Character.toUpperCase(value));
        }
        return result.toString();
    }
    @Test void measuredExecutableAcceptsUpperAndMixedAsciiHexWithoutChangingHistoricalSpelling()throws Exception {
        var executable=file("software-executable.bin","abc");
        var oldSource=exact(file("historical-source.txt","historical source DATA"));
        var implementation=exact(file("implementation-source.txt","current implementation DATA"));
        String lower=executable.sha256(),upper=lower.toUpperCase(Locale.ROOT),mixed=mixed(lower);
        assertNotEquals(lower,upper);assertNotEquals(lower,mixed);assertNotEquals(upper,mixed);
        for(String spelling:List.of(lower,upper,mixed)){
            var original=historical(spelling,oldSource);
            var loaded=RootOrdinaryRuntimeAssembly.loadedExecutionSource(MACHINE,NOW,executable,original,implementation);
            assertEquals(MACHINE,loaded.machineId());assertEquals(NOW.toString(),loaded.observedAtUtc());
            assertEquals(spelling,loaded.exactBuild());assertEquals(original.exactBuild(),loaded.exactBuild());
            assertEquals(implementation,loaded.sourceRef());assertNotEquals(oldSource,loaded.sourceRef());
            assertEquals(OLD.toString(),original.observedAtUtc());assertEquals(oldSource,original.sourceRef());
            assertEquals(spelling,original.exactBuild(),"general historical G2Source retains its original literal");
        }
        executable.verify();
    }
    @Test void remeasuredChangedContentAndAnotherMeasuredDigestCannotMatchTheHistoricalBuild()throws Exception {
        var executable=file("software-executable.bin","abc");var source=exact(file("source.txt","source DATA"));
        var original=historical(executable.sha256().toUpperCase(Locale.ROOT),source);
        var other=file("other-executable.bin","different actual bytes");assertNotEquals(executable.sha256(),other.sha256());
        assertThrows(IOException.class,()->RootOrdinaryRuntimeAssembly.loadedExecutionSource(MACHINE,NOW,executable,
                historical(other.sha256(),source),source));
        Files.writeString(Path.of(executable.path()),"physically changed software executable bytes");
        var remeasured=ControlBuild.FileRef.measure(Path.of(executable.path()));
        assertNotEquals(executable.sha256(),remeasured.sha256());
        assertThrows(IOException.class,()->RootOrdinaryRuntimeAssembly.loadedExecutionSource(MACHINE,NOW,remeasured,original,source));
        assertEquals(executable.sha256().toUpperCase(Locale.ROOT),original.exactBuild());
    }
    @Test void loadedFactoryRejectsNonShaAndUnicodeDomainsWhileOrdinaryG2SourceKeepsThemAsData()throws Exception {
        var executable=file("software-executable.bin","abc");var source=exact(file("source.txt","source DATA"));
        for(String spelling:List.of("1.20.0.4","a".repeat(63),"g".repeat(64),"0x"+executable.sha256(),
                " "+executable.sha256(),"\uFF21".repeat(64),"a".repeat(63)+"\u00E9")){
            var original=historical(spelling,source);assertEquals(spelling,original.exactBuild());
            assertThrows(IOException.class,()->RootOrdinaryRuntimeAssembly.loadedExecutionSource(MACHINE,NOW,executable,original,source),spelling);
            assertEquals(spelling,new G2Source(MACHINE,NOW.toString(),spelling,source).exactBuild(),
                    "the general nonloaded source contract remains literal DATA");
        }
    }
}
