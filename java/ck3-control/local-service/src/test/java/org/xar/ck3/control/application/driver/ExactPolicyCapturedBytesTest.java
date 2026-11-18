package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;

/** Exact captured-input DATA boundary. No policy, environment, Game, SourceRole or admission is fabricated. */
final class ExactPolicyCapturedBytesTest {
    @TempDir Path root;
    private ExactRef original(byte[] raw)throws IOException {
        Path file=root.resolve("captured-policy-data.json");Files.write(file,raw,StandardOpenOption.CREATE_NEW);
        var ref=ControlBuild.FileRef.measure(file);return new ExactRef(ref.path(),ref.bytes(),ref.sha256());
    }
    @Test void restoredOriginalPathCannotBlessOtherSameLengthCapturedBytes()throws Exception {
        byte[] a="{\"data\":\"A\"}".getBytes(StandardCharsets.UTF_8),b="{\"data\":\"B\"}".getBytes(StandardCharsets.UTF_8);
        var source=original(a);assertEquals(a.length,b.length);
        // The path is the original A; B represents bytes captured during a transient replacement.
        new ControlBuild.FileRef(source.path(),source.bytes(),source.sha256()).verify();
        InitialEpisodePolicy.requireCapturedExact(source,a);
        assertThrows(IOException.class,()->InitialEpisodePolicy.requireCapturedExact(source,b));
        assertArrayEquals(a,Files.readAllBytes(Path.of(source.path())));
    }
    @Test void completeCapturedByteCountAndDigestAreBothRequired()throws Exception {
        byte[] a="abcd".getBytes(StandardCharsets.UTF_8);var source=original(a);
        assertThrows(IOException.class,()->InitialEpisodePolicy.requireCapturedExact(source,new byte[]{'a','b','c'}));
        assertThrows(IOException.class,()->InitialEpisodePolicy.requireCapturedExact(source,new byte[]{'a','b','c','d','e'}));
        assertThrows(IOException.class,()->InitialEpisodePolicy.requireCapturedExact(source,new byte[]{'a','b','c','e'}));
        InitialEpisodePolicy.requireCapturedExact(source,a.clone());
    }
    @Test void exactCaptureDoesNotAcceptUnboundedOrEmptyPolicySources()throws Exception {
        byte[] a=new byte[]{'x'};var source=original(a);
        var large=new ExactRef(source.path(),(1<<20)+1,source.sha256());
        var empty=new ExactRef(source.path(),0,source.sha256());
        assertThrows(IOException.class,()->InitialEpisodePolicy.requireCapturedExact(large,a));
        assertThrows(IOException.class,()->InitialEpisodePolicy.requireCapturedExact(empty,new byte[0]));
    }
}
