package org.xar.ck3.control.contracts.source;

import static org.junit.jupiter.api.Assertions.*;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.FileTime;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Owned temporary-file metadata only. Independent three-buffer native oracle, no Game/source permission. */
final class IdentityMemory335Test {
    @TempDir Path temporary;
    private static final IdentityBearingFileAttributes.AttributeApi API =
            Native.load("kernel32", IdentityBearingFileAttributes.AttributeApi.class);

    @Test void fileMetadataMatchesIndependentThreeBufferWin32Oracle() throws Exception {
        Path path=Files.writeString(temporary.resolve("metadata.txt"),"exact fresh owned metadata");
        HANDLE handle=open(path);
        try {
            Oracle before=oracle(handle);
            Object actual=stamp(handle,true);
            Oracle after=oracle(handle);
            assertEquals(before,after,"owned fixture must stay stable between independent native observations");
            compare(before,actual);
            assertFalse(before.directory());
            assertEquals(Files.size(path),before.bytes());
            assertTrue(new BigInteger(before.key().fileIdDecimal()).signum()>=0);
            assertEquals(IdentityBearingFileAttributes.read(path).fileKey(),before.key());
        } finally {close(handle);}
    }

    @Test void directoryKindAndOrdinaryFileRejectionKeepTheirRealNativeFields() throws Exception {
        Path path=Files.createDirectory(temporary.resolve("directory"));
        HANDLE handle=open(path);
        try {
            Oracle expected=oracle(handle);assertTrue(expected.directory());
            compare(expected,stamp(handle,false));
            IOException failure=assertThrows(IOException.class,()->stamp(handle,true));
            assertEquals("ordinary identity-bearing ledger file required",failure.getMessage());
            compare(oracle(handle),stamp(handle,false));
        } finally {close(handle);}
    }

    @Test void firstImmutableStampSurvivesLaterFreshQueryAfterRealMetadataChange() throws Exception {
        Path path=Files.writeString(temporary.resolve("changing.txt"),"old");
        HANDLE handle=open(path);
        try {
            Oracle before=oracle(handle);Object first=stamp(handle,true);compare(before,first);
            Files.writeString(path,"new and longer owned material");
            Files.setLastModifiedTime(path,FileTime.fromMillis(Files.getLastModifiedTime(path).toMillis()+2000));
            Oracle changed=oracle(handle);Object second=stamp(handle,true);compare(changed,second);
            assertEquals(before.key(),changed.key());assertNotEquals(before.bytes(),changed.bytes());
            assertNotEquals(before.modified(),changed.modified());
            compare(before,first);
            assertNotEquals(value(first,"bytes"),value(second,"bytes"));
            assertEquals(IdentityBearingFileAttributes.read(path).fileKey(),changed.key());
        } finally {close(handle);}
    }

    private static HANDLE open(Path path) throws IOException {
        HANDLE handle=Kernel32.INSTANCE.CreateFile(IdentityBearingFileAttributes.nativePath(path.toString()),0x80,7,null,3,0x02200000,null);
        if(WinBase.INVALID_HANDLE_VALUE.equals(handle))throw new IOException("fixture open Win32="+Native.getLastError());
        return handle;
    }
    private static void close(HANDLE handle) throws IOException {
        if(!Kernel32.INSTANCE.CloseHandle(handle))throw new IOException("fixture close Win32="+Native.getLastError());
    }
    private static Object stamp(HANDLE handle,boolean ordinary) throws Exception {
        var method=IdentityBearingFileAttributes.class.getDeclaredMethod("windowsStamp",HANDLE.class,boolean.class);
        method.setAccessible(true);
        try{return method.invoke(null,handle,ordinary);}
        catch(InvocationTargetException failure){
            if(failure.getCause() instanceof IOException error)throw error;
            if(failure.getCause() instanceof RuntimeException error)throw error;
            if(failure.getCause() instanceof Error error)throw error;
            throw failure;
        }
    }
    private static Object value(Object stamp,String name) throws ReflectiveOperationException {
        var accessor=stamp.getClass().getDeclaredMethod(name);accessor.setAccessible(true);return accessor.invoke(stamp);
    }
    private static void compare(Oracle expected,Object actual) throws ReflectiveOperationException {
        assertEquals(expected.key(),value(actual,"key"));assertEquals(expected.bytes(),value(actual,"bytes"));
        assertEquals(expected.creation(),value(actual,"creation"));assertEquals(expected.modified(),value(actual,"modified"));
        assertEquals(expected.directory(),value(actual,"directory"));
    }
    private record Oracle(IdentityBearingFileAttributes.WindowsFileIdentity key,long bytes,long creation,long modified,boolean directory) { }

    /** Original independent allocation layout, retained before reading model candidate. */
    private static Oracle oracle(HANDLE handle) throws IOException {
        try(Memory id=new Memory(24);Memory basic=new Memory(40);Memory standard=new Memory(24)) {
            if(!API.GetFileInformationByHandleEx(handle,18,id,24)
                    ||!API.GetFileInformationByHandleEx(handle,0,basic,40)
                    ||!API.GetFileInformationByHandleEx(handle,1,standard,24))
                throw new IOException("fixture native oracle Win32="+Native.getLastError());
            byte[] little=id.getByteArray(8,16),big=new byte[16];
            for(int i=0;i<16;i++)big[i]=little[15-i];
            var key=new IdentityBearingFileAttributes.WindowsFileIdentity(Long.toUnsignedString(id.getLong(0)),
                    new BigInteger(1,big).toString(),Long.toUnsignedString(basic.getLong(0)));
            return new Oracle(key,standard.getLong(8),basic.getLong(0),basic.getLong(16),standard.getByte(21)!=0);
        }
    }
}
