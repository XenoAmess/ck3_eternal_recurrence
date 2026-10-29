package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.FileTime;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;

final class NativeSavedGameFilesTest {
    @TempDir Path temporary;

    @Test void externalSavedOriginalIsMaterializedAtTheActualLoadsaveArgumentTarget() throws Exception {
        Path source=temporary.resolve("external/罗贝尔 1066.ck3");
        Files.createDirectories(source.getParent());
        byte[] selected="selected software-only save\0body".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Files.write(source,selected);
        var original=ControlBuild.FileRef.measure(source);
        var load=new NativeLaunchPlan.SavedGame("罗贝尔 1066",original);
        Path profile=temporary.resolve("isolated-profile");

        var actual=NativeSavedGameFiles.materialize(profile,load);

        Path target=profile.resolve("save games/罗贝尔 1066.ck3");
        assertEquals(List.of("-gdpr-compliant","-userdir="+profile,"-loadsave=罗贝尔 1066"),
                NativeLaunchPlan.arguments(profile,load,false));
        assertEquals(target.toString(),actual.path());
        assertArrayEquals(selected,Files.readAllBytes(target));
        assertEquals(original.bytes(),actual.bytes());
        assertEquals(original.sha256(),actual.sha256());
        assertSame(original,load.save(),"The original source remains the checkpoint/seed role");
        assertNotEquals(original.path(),actual.path());
        assertEquals(original,ControlBuild.FileRef.measure(source));
        assertOnlyTarget(target);
    }

    @Test void existingIdenticalTargetIsPreserved() throws Exception {
        var load=external("same",new byte[]{3,1,4,1,5});
        Path profile=temporary.resolve("profile");
        Path target=profile.resolve("save games/same.ck3");
        Files.createDirectories(target.getParent());
        Files.copy(Path.of(load.save().path()),target);
        Files.setLastModifiedTime(target,FileTime.fromMillis(946684800000L));
        FileTime before=Files.getLastModifiedTime(target);

        var actual=NativeSavedGameFiles.materialize(profile,load);

        assertEquals(ControlBuild.FileRef.measure(target),actual);
        assertEquals(before,Files.getLastModifiedTime(target));
        assertOnlyTarget(target);
    }

    @Test void conflictingTargetIsNotOverwritten() throws Exception {
        var load=external("conflict",new byte[]{7,8,9});
        Path profile=temporary.resolve("profile");
        Path target=profile.resolve("save games/conflict.ck3");
        Files.createDirectories(target.getParent());
        byte[] prior={9,8,7};Files.write(target,prior);
        var originalTarget=ControlBuild.FileRef.measure(target);
        Files.setLastModifiedTime(target,FileTime.fromMillis(946684800000L));
        FileTime before=Files.getLastModifiedTime(target);

        assertThrows(IOException.class,()->NativeSavedGameFiles.materialize(profile,load));

        assertEquals(originalTarget,ControlBuild.FileRef.measure(target));
        assertArrayEquals(prior,Files.readAllBytes(target));
        assertEquals(before,Files.getLastModifiedTime(target));
        assertOnlyTarget(target);
    }

    @Test void sourceAlreadyAtConfiguredTargetIsPreserved() throws Exception {
        Path profile=temporary.resolve("profile");
        Path target=profile.resolve("save games/current.ck3");
        Files.createDirectories(target.getParent());Files.write(target,new byte[]{1,2,3});
        var original=ControlBuild.FileRef.measure(target);
        var load=new NativeLaunchPlan.SavedGame("current",original);
        Files.setLastModifiedTime(target,FileTime.fromMillis(946684800000L));
        FileTime before=Files.getLastModifiedTime(target);

        assertEquals(original,NativeSavedGameFiles.materialize(profile,load));

        assertEquals(before,Files.getLastModifiedTime(target));
        assertOnlyTarget(target);
    }

    @Test void changedSourceCannotPublishTheExpectedSavedOriginal() throws Exception {
        var load=external("changed",new byte[]{1,2,3});
        Path source=Path.of(load.save().path());
        byte[] changed={1,2,4};Files.write(source,changed);
        Path profile=temporary.resolve("profile");

        assertThrows(IOException.class,()->NativeSavedGameFiles.materialize(profile,load));

        assertFalse(Files.exists(profile.resolve("save games/changed.ck3")));
        assertArrayEquals(changed,Files.readAllBytes(source));
        Path saves=profile.resolve("save games");
        if(Files.exists(saves))try(var files=Files.list(saves)){assertEquals(0L,files.count());}
    }

    @Test void changedSourceAlreadyAtTargetCannotBeAcceptedAsTheSelectedOriginal() throws Exception {
        Path profile=temporary.resolve("profile");
        Path target=profile.resolve("save games/current.ck3");
        Files.createDirectories(target.getParent());Files.write(target,new byte[]{1,2,3});
        var load=new NativeLaunchPlan.SavedGame("current",ControlBuild.FileRef.measure(target));
        byte[] changed={1,2,4};Files.write(target,changed);

        assertThrows(IOException.class,()->NativeSavedGameFiles.materialize(profile,load));

        assertArrayEquals(changed,Files.readAllBytes(target),"Failure must not delete or restore an in-place source");
        assertOnlyTarget(target);
    }

    private NativeLaunchPlan.SavedGame external(String basename,byte[] content) throws IOException {
        Path source=temporary.resolve("external/"+basename+".ck3");
        Files.createDirectories(source.getParent());Files.write(source,content);
        return new NativeLaunchPlan.SavedGame(basename,ControlBuild.FileRef.measure(source));
    }

    private static void assertOnlyTarget(Path target) throws IOException {
        try(var files=Files.list(target.getParent())){assertEquals(List.of(target),files.toList());}
    }
}
