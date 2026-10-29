package org.xar.ck3.control.build;

import com.sun.jna.Native;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinDef.DWORDByReference;
import java.io.IOException;
import java.nio.file.Path;

/** Actual allocation unit shared by profile custody and runtime inventory; FileStore block size is only sector size on Windows. */
public final class NativeStorageGeometry {
    private NativeStorageGeometry(){ }
    public record Volume(Path root,long sectorsPerCluster,long bytesPerSector,long clusterBytes){
        public Volume{
            if(root==null||!root.isAbsolute()||!root.equals(root.getRoot())||sectorsPerCluster<1||bytesPerSector<1
                    ||clusterBytes!=Math.multiplyExact(sectorsPerCluster,bytesPerSector)||clusterBytes<512||clusterBytes>2L<<20)
                throw new IllegalArgumentException("actual finite Windows volume geometry required");
        }
    }
    public static Volume read(Path path)throws IOException{
        if(path==null||!path.isAbsolute()||!path.normalize().equals(path))throw new IOException("canonical absolute native volume path required");
        SharedSourceFiles.plainAncestors(path);Path root=path.getRoot();
        var sectors=new DWORDByReference();var bytes=new DWORDByReference();var free=new DWORDByReference();var total=new DWORDByReference();
        if(!Kernel32.INSTANCE.GetDiskFreeSpace(root.toString(),sectors,bytes,free,total))
            throw new IOException("actual native cluster geometry Win32="+Native.getLastError());
        try{return new Volume(root,sectors.getValue().longValue(),bytes.getValue().longValue(),
                Math.multiplyExact(sectors.getValue().longValue(),bytes.getValue().longValue()));}
        catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("unsupported actual native cluster geometry",invalid);}
    }
}
