package org.xar.ck3.rrf.save;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.WString;
import com.sun.jna.win32.StdCallLibrary;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import org.xar.ck3.rrf.save.SaveContracts.PhysicalIdentity;

/** Ordinary file metadata only. Java's Windows BasicFileAttributes.fileKey is null.
 * Use the project's existing FILE_ID_INFO/FILE_BASIC_INFO pattern, never a timestamp substitute. */
final class SavedFileIdentity {
    private SavedFileIdentity() { }
    private interface Api extends StdCallLibrary {
        Pointer CreateFileW(WString path,int access,int share,Pointer security,int disposition,int flags,Pointer template);
        boolean GetFileInformationByHandleEx(Pointer handle,int kind,Pointer data,int bytes);
        boolean CloseHandle(Pointer handle);
    }
    private static final class Windows { private static final Api API=Native.load("kernel32",Api.class); }
    static PhysicalIdentity read(Path path) throws IOException {
        if (!System.getProperty("os.name").startsWith("Windows")) {
            var info=Files.readAttributes(path,BasicFileAttributes.class);
            if(info.fileKey()==null||!info.isRegularFile())throw new IOException("physical file identity unavailable");
            return new PhysicalIdentity("java-fileKey:"+info.fileKey(),info.size(),"created="+info.creationTime()+";modified="+info.lastModifiedTime());
        }
        var api=Windows.API;
        Pointer h=api.CreateFileW(new WString(path.toString()),0x80,7,null,3,0x00200000,null);
        if(h==null||Pointer.nativeValue(h)==-1L)throw new IOException("read-only physical metadata open Win32="+Native.getLastError());
        try(Memory id=new Memory(24);Memory basic=new Memory(40);Memory standard=new Memory(24)) {
            if(!api.GetFileInformationByHandleEx(h,18,id,24)||!api.GetFileInformationByHandleEx(h,0,basic,40)||!api.GetFileInformationByHandleEx(h,1,standard,24))
                throw new IOException("physical identity query Win32="+Native.getLastError());
            if((basic.getInt(32)&0x400)!=0||standard.getByte(20)!=0||standard.getByte(21)!=0)throw new IOException("ordinary non-reparse non-delete-pending file required");
            byte[] value=id.getByteArray(8,16),reverse=new byte[16];for(int i=0;i<16;i++)reverse[i]=value[15-i];
            String key="win32-file-id-info:u64-volume="+Long.toUnsignedString(id.getLong(0))+";u128-id="+new BigInteger(1,reverse);
            String times="filetime-created="+Long.toUnsignedString(basic.getLong(0))+";written="+Long.toUnsignedString(basic.getLong(16))+";changed="+Long.toUnsignedString(basic.getLong(24));
            return new PhysicalIdentity(key,standard.getLong(8),times);
        } finally {if(!api.CloseHandle(h))throw new IOException("physical metadata handle close failed");}
    }
}
