package org.xar.ck3.control.contracts.source;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.file.attribute.FileTime;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class IdentityBearingFileAttributesTest {
    @TempDir Path temporary;
    @Test void directoryNioSizeDriftWithUnchangedRealNativeStampsIsAccepted() throws Exception {
        Path directory = Files.createDirectory(temporary.resolve("nio-directory-size"));
        BasicFileAttributes observed = Files.readAttributes(directory, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        Object first = nativeStamp(directory), second = nativeStamp(directory);
        assertEquals(first, second, "both native observations must be actual unchanged metadata");
        var result = validated(directory, new NioSize(observed, 0), new NioSize(observed, 4096), first, second);
        assertTrue(result.isDirectory()); assertEquals(4096, result.size());
        assertEquals(IdentityBearingFileAttributes.read(directory).fileKey(), result.fileKey());
    }
    @Test void regularFileNioSizeDriftAndNativeSizeMismatchRemainRejected() throws Exception {
        Path source = Files.writeString(temporary.resolve("nio-file-size.txt"), "exact file bytes");
        BasicFileAttributes observed = Files.readAttributes(source, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        Object first = nativeStamp(source), second = nativeStamp(source);
        assertEquals(first, second);
        var changed = new NioSize(observed, observed.size() + 1);
        assertThrows(IOException.class, () -> validated(source, observed, changed, first, second));
        assertThrows(IOException.class, () -> validated(source, changed, changed, first, second));
    }
    @Test void realDirectoryNativeTimeAndIdentityChangesRemainRejected() throws Exception {
        Path directory = Files.createDirectory(temporary.resolve("native-directory-change"));
        BasicFileAttributes before = Files.readAttributes(directory, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        Object original = nativeStamp(directory);
        Files.setLastModifiedTime(directory, FileTime.fromMillis(before.lastModifiedTime().toMillis() + 2000));
        BasicFileAttributes changedTime = Files.readAttributes(directory, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        Object changedStamp = nativeStamp(directory);
        assertNotEquals(original, changedStamp, "real native last-write change must remain observable");
        assertThrows(IOException.class, () -> validated(directory, new NioSize(before, 0),
                new NioSize(changedTime, 4096), original, changedStamp));
        Files.move(directory, temporary.resolve("retained-native-directory"));
        Files.createDirectory(directory);
        Files.setLastModifiedTime(directory, before.lastModifiedTime());
        BasicFileAttributes replaced = Files.readAttributes(directory, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        Object replacement = nativeStamp(directory);
        assertNotEquals(original, replacement, "replacement native identity must not reuse the old stamp");
        assertThrows(IOException.class, () -> validated(directory, new NioSize(before, 0),
                new NioSize(replaced, 4096), original, replacement));
    }

    /** Native stamps always come from the production reader; only the NIO size is varied. */
    private static Object nativeStamp(Path path) throws ReflectiveOperationException {
        var method = IdentityBearingFileAttributes.class.getDeclaredMethod("windows", Path.class);
        method.setAccessible(true); return method.invoke(null, path);
    }
    private static BasicFileAttributes validated(Path path, BasicFileAttributes before, BasicFileAttributes after,
            Object first, Object second) throws ReflectiveOperationException, IOException {
        var method = IdentityBearingFileAttributes.class.getDeclaredMethod("validated", Path.class,
                BasicFileAttributes.class, BasicFileAttributes.class, first.getClass(), second.getClass());
        method.setAccessible(true);
        try { return assertInstanceOf(BasicFileAttributes.class, method.invoke(null, path, before, after, first, second)); }
        catch (InvocationTargetException failure) {
            if (failure.getCause() instanceof IOException expected) throw expected;
            throw failure;
        }
    }
    private record NioSize(BasicFileAttributes original, long size) implements BasicFileAttributes {
        @Override public FileTime lastModifiedTime() { return original.lastModifiedTime(); }
        @Override public FileTime lastAccessTime() { return original.lastAccessTime(); }
        @Override public FileTime creationTime() { return original.creationTime(); }
        @Override public boolean isRegularFile() { return original.isRegularFile(); }
        @Override public boolean isDirectory() { return original.isDirectory(); }
        @Override public boolean isSymbolicLink() { return original.isSymbolicLink(); }
        @Override public boolean isOther() { return original.isOther(); }
        @Override public Object fileKey() { return original.fileKey(); }
    }
    @Test void realFilesDirectoriesAndCopiesHaveStableDistinctIdentity() throws IOException {
        Path directory = Files.createDirectory(temporary.resolve("directory"));
        var dir = IdentityBearingFileAttributes.read(directory);
        assertTrue(dir.isDirectory()); assertNotNull(dir.fileKey());
        assertEquals(dir.fileKey(), IdentityBearingFileAttributes.read(directory).fileKey());
        Path source = Files.writeString(directory.resolve("source.txt"), "retained exact bytes");
        var first = IdentityBearingFileAttributes.read(source);
        assertEquals(first.fileKey(), IdentityBearingFileAttributes.read(source).fileKey());
        assertTrue(first.isRegularFile()); assertNotNull(first.fileKey());
        Path copy = Files.copy(source, directory.resolve("copy.txt"), StandardCopyOption.COPY_ATTRIBUTES);
        assertArrayEquals(Files.readAllBytes(source), Files.readAllBytes(copy));
        assertNotEquals(first.fileKey(), IdentityBearingFileAttributes.read(copy).fileKey());
        assertNotEquals(dir.fileKey(), first.fileKey());
    }
    @Test void wholePathReadsTheActualLeafAndDirectoriesWithoutCachingTheirIdentity() throws IOException {
        Path directory = Files.createDirectory(temporary.resolve("whole-path"));
        Path source = Files.writeString(directory.resolve("source.txt"), "whole-path source");
        var original = IdentityBearingFileAttributes.read(source);
        var actual = IdentityBearingFileAttributes.readWithOrdinaryParents(source);
        assertEquals(original.fileKey(), actual.fileKey());
        assertEquals(original.size(), actual.size());
        assertEquals(original.lastModifiedTime(), actual.lastModifiedTime());
        assertTrue(IdentityBearingFileAttributes.readWithOrdinaryParents(directory).isDirectory());
        assertThrows(IOException.class, () -> IdentityBearingFileAttributes.readWithOrdinaryParents(source.resolve("child")));
    }
    @Test void parentReplacementWithTheIdenticalHardlinkedLeafIsRejectedBetweenWholePathObservations() throws IOException {
        Path directory = Files.createDirectory(temporary.resolve("original-parent"));
        Path source = Files.writeString(directory.resolve("source.txt"), "same native leaf and bytes");
        var leaf = IdentityBearingFileAttributes.read(source);
        var originalParent = IdentityBearingFileAttributes.read(directory);
        FileTime containerMtime = Files.getLastModifiedTime(temporary);
        var observation = IdentityBearingFileAttributes.beginOrdinaryPathObservation(source);
        Path retained = temporary.resolve("retained-parent");
        Files.move(directory, retained);
        Files.createDirectory(directory);
        Files.createLink(source, retained.resolve("source.txt"));
        Files.setLastModifiedTime(directory, originalParent.lastModifiedTime());
        Files.setLastModifiedTime(temporary, containerMtime);
        var sameLeaf = IdentityBearingFileAttributes.read(source);
        assertEquals(leaf.fileKey(), sameLeaf.fileKey());
        assertEquals(leaf.size(), sameLeaf.size());
        assertEquals(leaf.lastModifiedTime(), sameLeaf.lastModifiedTime());
        assertNotEquals(originalParent.fileKey(), IdentityBearingFileAttributes.read(directory).fileKey());
        assertArrayEquals(Files.readAllBytes(retained.resolve("source.txt")), Files.readAllBytes(source));
        String rejection = assertThrows(IOException.class, observation::complete).getMessage();
        assertTrue(rejection.contains("path=" + directory));
        assertTrue(rejection.contains("before_nio=") && rejection.contains("after_nio="));
        assertTrue(rejection.contains("first_native=") && rejection.contains("second_native="));
        assertTrue(rejection.contains(originalParent.fileKey().toString()), "exact decimal native identity retained");
        assertEquals(leaf.fileKey(), IdentityBearingFileAttributes.readWithOrdinaryParents(source).fileKey());
    }
    @Test void wholePathRejectsSameBytesSameMtimeLeafReplacementDuringItsObservation() throws IOException {
        Path directory = Files.createDirectory(temporary.resolve("leaf-parent"));
        Path source = Files.writeString(directory.resolve("source.txt"), "same bytes");
        var original = IdentityBearingFileAttributes.read(source);
        Path replacement = Files.writeString(directory.resolve("replacement.txt"), "same bytes");
        Files.setLastModifiedTime(replacement, original.lastModifiedTime());
        FileTime parentMtime = Files.getLastModifiedTime(directory);
        var observation = IdentityBearingFileAttributes.beginOrdinaryPathObservation(source);
        Files.move(replacement, source, StandardCopyOption.REPLACE_EXISTING);
        Files.setLastModifiedTime(directory, parentMtime);
        var changed = IdentityBearingFileAttributes.read(source);
        assertEquals(original.size(), changed.size());
        assertEquals(original.lastModifiedTime(), changed.lastModifiedTime());
        assertNotEquals(original.fileKey(), changed.fileKey());
        assertThrows(IOException.class, observation::complete);
    }
    @Test void actualReparseParentCannotQualifyAnOrdinaryWholePath() throws Exception {
        Path directory = Files.createDirectory(temporary.resolve("reparse-target"));
        Files.writeString(directory.resolve("source.txt"), "real reparse target");
        Path alias = temporary.resolve("reparse-parent");
        // Fixed fixture command inherits the owning Maven Job; no symbolic-link privilege is required.
        Process process = new ProcessBuilder("cmd.exe", "/d", "/c", "mklink", "/J", alias.toString(), directory.toString())
                .redirectErrorStream(true).start();
        if (!process.waitFor(10, java.util.concurrent.TimeUnit.SECONDS)) {
            process.destroyForcibly();
            assertTrue(process.waitFor(5, java.util.concurrent.TimeUnit.SECONDS), "owned reparse fixture process did not terminate");
            fail("owned reparse fixture creation timed out");
        }
        assertEquals(0, process.exitValue(), new String(process.getInputStream().readNBytes(8192), java.nio.charset.StandardCharsets.UTF_8));
        try {
            int attributes = com.sun.jna.platform.win32.Kernel32.INSTANCE.GetFileAttributes(IdentityBearingFileAttributes.nativePath(alias.toString()));
            assertNotEquals(-1, attributes, "actual directory junction attributes must be readable");
            assertEquals(0x410, attributes & 0x410, "actual ordinary-directory and reparse flags required");
            assertTrue(Files.isSameFile(directory, alias));
            var target = IdentityBearingFileAttributes.read(directory.resolve("source.txt"));
            var viaJunction = IdentityBearingFileAttributes.read(alias.resolve("source.txt"));
            assertEquals(target.fileKey(), viaJunction.fileKey(), "ordinary target through actual junction must have same native identity");
            assertEquals(target.size(), viaJunction.size(), "ordinary target through actual junction must have same size");
            assertEquals(target.lastModifiedTime(), viaJunction.lastModifiedTime(), "ordinary target through actual junction must have same modified time");
            assertThrows(IOException.class, () -> IdentityBearingFileAttributes.readWithOrdinaryParents(alias.resolve("source.txt")));
            assertThrows(IOException.class, () -> IdentityBearingFileAttributes.read(alias));
        } finally { Files.delete(alias); }
    }
    @Test void replacementWithTheSameBytesAndTimestampCannotReuseOldIdentity() throws IOException {
        Path source = Files.writeString(temporary.resolve("source.txt"), "same bytes");
        var original = IdentityBearingFileAttributes.read(source);
        Path replacement = Files.writeString(temporary.resolve("replacement.txt"), "same bytes");
        Files.setLastModifiedTime(replacement, original.lastModifiedTime());
        Files.move(replacement, source, StandardCopyOption.REPLACE_EXISTING);
        var changed = IdentityBearingFileAttributes.read(source);
        assertEquals(original.size(), changed.size());
        assertEquals(original.lastModifiedTime(), changed.lastModifiedTime());
        assertNotEquals(original.fileKey(), changed.fileKey());
    }
    @Test void directoryReplacementAndRealMetadataDriftRemainObservable() throws IOException {
        Path directory = Files.createDirectory(temporary.resolve("directory"));
        Object oldDirectory = IdentityBearingFileAttributes.read(directory).fileKey();
        Files.move(directory, temporary.resolve("old-directory"));
        Files.createDirectory(directory);
        assertNotEquals(oldDirectory, IdentityBearingFileAttributes.read(directory).fileKey());
        Path source = Files.writeString(directory.resolve("source.txt"), "first");
        var before = IdentityBearingFileAttributes.read(source);
        Files.writeString(source, "different and longer");
        Files.setLastModifiedTime(source, FileTime.fromMillis(before.lastModifiedTime().toMillis() + 2000));
        var after = IdentityBearingFileAttributes.read(source);
        assertEquals(before.fileKey(), after.fileKey());
        assertNotEquals(before.size(), after.size()); assertNotEquals(before.lastModifiedTime(), after.lastModifiedTime());
        assertThrows(IOException.class, () -> IdentityBearingFileAttributes.read(directory.resolve("missing")));
    }
}

