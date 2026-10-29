package org.xar.ck3.control.nativebridge;

import com.sun.jna.Function;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.Advapi32Util;
import com.sun.jna.platform.win32.BaseTSD.SIZE_T;
import com.sun.jna.platform.win32.WinReg;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.ptr.PointerByReference;
import com.sun.jna.win32.StdCallLibrary;
import com.sun.jna.win32.W32APIOptions;
import java.io.IOException;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.UUID;

/** Opens only the Native-created original mapping. Never creates a Game, mapping, desktop or window. */
final class NativePresentationWin32 implements NativePresentationMemoryPort {
    interface Kernel extends StdCallLibrary {
        Pointer OpenFileMappingW(int access,boolean inherit,String name);
        Pointer MapViewOfFile(Pointer mapping,int access,int high,int low,SIZE_T bytes);
        boolean UnmapViewOfFile(Pointer view);boolean CloseHandle(Pointer handle);
        void FlushProcessWriteBuffers();long GetTickCount64();
    }
    interface WindowCallback extends StdCallLibrary.StdCallCallback {boolean invoke(Pointer hwnd,Pointer data);}
    interface User extends StdCallLibrary {
        boolean EnumWindows(WindowCallback callback,Pointer data);boolean IsWindow(Pointer hwnd);
        int GetWindowThreadProcessId(Pointer hwnd,IntByReference pid);
        int GetWindowTextW(Pointer hwnd,char[] text,int maximum);
        boolean GetClientRect(Pointer hwnd,int[] rect);
    }
    interface Ole extends StdCallLibrary {
        int CoInitializeEx(Pointer reserved,int flags);void CoUninitialize();
        int CoCreateInstance(Pointer clsid,Pointer outer,int context,Pointer iid,PointerByReference result);
    }
    private static final int SIZE=131072,ACCESS=6;
    private static final VarHandle INTS=MethodHandles.byteBufferViewVarHandle(int[].class,ByteOrder.LITTLE_ENDIAN);
    private final NativePipeEndpoint.Config config;private final NativeProcessGuard guard;
    private final Kernel kernel;private final User user;private final Ole ole;
    private Pointer mapping,view;private boolean closed;
    NativePresentationWin32(NativePipeEndpoint.Config config,NativeProcessGuard guard)throws IOException {
        this.config=config;this.guard=guard;
        if(!System.getProperty("os.name","").startsWith("Windows")||Native.POINTER_SIZE!=8
                ||!System.getProperty("os.arch","").matches("(?i)(amd64|x86_64)"))throw new IOException("reviewed Windows AMD64 presentation mapping required");
        guard.verify(config.game());
        kernel=Native.load("kernel32",Kernel.class,W32APIOptions.UNICODE_OPTIONS);
        user=Native.load("user32",User.class,W32APIOptions.UNICODE_OPTIONS);
        ole=Native.load("ole32",Ole.class,W32APIOptions.UNICODE_OPTIONS);
        mapping=kernel.OpenFileMappingW(ACCESS,false,"Local\\XarCK3CameraPresentationV1-"+config.game().pid());
        if(nil(mapping))throw new IOException("original Native presentation mapping is not deployed");
        view=kernel.MapViewOfFile(mapping,ACCESS,0,0,new SIZE_T(SIZE));
        if(nil(view)){kernel.CloseHandle(mapping);mapping=null;throw new IOException("original presentation mapping cannot be mapped");}
        try{verify();}catch(IOException|RuntimeException failure){try{close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}throw failure;}
    }
    @Override public void verify()throws IOException {
        if(closed||nil(view))throw new IOException("presentation mapping closed");guard.verify(config.game());
        if(view.getInt(0)!=0x43524158 || view.getInt(4)!=1
                ||Integer.toUnsignedLong(view.getInt(8))!=config.game().pid() || view.getInt(12)!=0)
            throw new IOException("original presentation mapping identity drift");
    }
    @Override public byte[] read(int offset,int length)throws IOException {
        bounds(offset,length);verify();byte[] bytes=view.getByteArray(offset,length);verify();return bytes;
    }
    @Override public boolean compareAndSetSequence(int offset,long expected,long update)throws IOException {
        if(offset!=16)throw new IOException("only the original request sequence is writable");verify();
        ByteBuffer sequence=view.getByteBuffer(offset,4);
        return (boolean)INTS.compareAndSet(sequence,0,(int)expected,(int)update);
    }
    @Override public void writeRequest(byte[] exact168)throws IOException {
        if(exact168.length!=168)throw new IOException("complete original request bytes required");verify();view.write(24,exact168,0,168);verify();
    }
    @Override public void writeTracking(byte[] exact4264)throws IOException {
        if(exact4264.length!=4264)throw new IOException("complete tracking request required");verify();view.write(0x18400+40,exact4264,0,4264);verify();
    }
    @Override public void flush()throws IOException {verify();kernel.FlushProcessWriteBuffers();verify();}
    @Override public long uptimeMillis()throws IOException {verify();long value=kernel.GetTickCount64();verify();return value;}
    @Override public String ownedDesktopOneWindow()throws IOException {
        verify();Pointer[] found={null};int[] visited={0};boolean[] invalid={false};
        WindowCallback callback=(hwnd,data)->{
            if(++visited[0]>4096){invalid[0]=true;return false;}
            IntByReference pid=new IntByReference();char[] title=new char[256];
            if(user.IsWindow(hwnd)&&user.GetWindowThreadProcessId(hwnd,pid)!=0
                    &&Integer.toUnsignedLong(pid.getValue())==config.game().pid()
                    &&user.GetWindowTextW(hwnd,title,title.length)>0&&Native.toString(title).equals("Crusader Kings III")) {
                if(found[0]!=null){invalid[0]=true;return false;}found[0]=hwnd;
            }
            return true;
        };
        boolean enumerated=user.EnumWindows(callback,Pointer.NULL);
        if(!enumerated||invalid[0]||nil(found[0]))throw new IOException("unique actual owned CK3 window unavailable");
        int[] rect=new int[4];if(!user.GetClientRect(found[0],rect)||rect[2]<=rect[0]||rect[3]<=rect[1])throw new IOException("actual camera viewport unavailable");
        byte[] desktops=Advapi32Util.registryGetBinaryValue(WinReg.HKEY_CURRENT_USER,
                "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VirtualDesktops","VirtualDesktopIDs");
        if(desktops.length<16||desktops.length>4096||(desktops.length&15)!=0)throw new IOException("actual Desktop1 registry identity unavailable");
        int initialized=ole.CoInitializeEx(Pointer.NULL,2);if(initialized<0&&initialized!=0x80010106)throw new IOException("COM desktop query initialization unavailable");
        Pointer manager=null;
        try(Memory clsid=guid("AA509086-5CA9-4C25-8F95-589D3C07B48A");Memory iid=guid("A5CD92FF-29BE-454C-8D04-D82879FB3F1B");Memory desktop=new Memory(16)) {
            PointerByReference result=new PointerByReference();int hr=ole.CoCreateInstance(clsid,Pointer.NULL,1,iid,result);
            manager=result.getValue();if(hr<0||nil(manager))throw new IOException("actual virtual desktop manager unavailable");
            // Concentrated typed COM boundary: IVirtualDesktopManager::GetWindowDesktopId is vtable slot4.
            Function getDesktop=Function.getFunction(manager.getPointer(0).getPointer(4L*Native.POINTER_SIZE),Function.ALT_CONVENTION);
            if(getDesktop.invokeInt(new Object[]{manager,found[0],desktop})<0
                    ||!Arrays.equals(Arrays.copyOf(desktops,16),desktop.getByteArray(0,16)))throw new IOException("actual owned CK3 window is outside Desktop1");
            verify();return Long.toUnsignedString(Pointer.nativeValue(found[0]));
        } finally {
            if(!nil(manager))Function.getFunction(manager.getPointer(0).getPointer(2L*Native.POINTER_SIZE),Function.ALT_CONVENTION).invokeInt(new Object[]{manager});
            if(initialized>=0)ole.CoUninitialize();
        }
    }
    private static Memory guid(String text){
        UUID id=UUID.fromString(text);Memory out=new Memory(16);ByteBuffer b=ByteBuffer.allocate(16).order(ByteOrder.LITTLE_ENDIAN);
        long high=id.getMostSignificantBits();b.putInt((int)(high>>>32)).putShort((short)(high>>>16)).putShort((short)high);
        long low=id.getLeastSignificantBits();for(int shift=56;shift>=0;shift-=8)b.put((byte)(low>>>shift));out.write(0,b.array(),0,16);return out;
    }
    private static boolean nil(Pointer value){return value==null||Pointer.nativeValue(value)==0;}
    private static void bounds(int offset,int length)throws IOException{if(offset<0||length<0||offset>SIZE-length)throw new IOException("bounded original mapping read required");}
    @Override public void close()throws IOException {
        if(closed)return;closed=true;boolean ok=true;
        if(!nil(view)){ok=kernel.UnmapViewOfFile(view);view=null;}
        if(!nil(mapping)){ok=kernel.CloseHandle(mapping)&&ok;mapping=null;}
        if(!ok)throw new IOException("presentation mapping cleanup unavailable");
    }
}
