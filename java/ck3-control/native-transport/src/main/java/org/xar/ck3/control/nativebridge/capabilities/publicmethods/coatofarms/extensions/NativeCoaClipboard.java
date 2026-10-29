package org.xar.ck3.control.nativebridge.capabilities.publicmethods.coatofarms.extensions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.BaseTSD.SIZE_T;
import com.sun.jna.platform.win32.WinDef.HWND;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.win32.StdCallLibrary;
import com.sun.jna.win32.W32APIOptions;
import java.io.IOException;
import java.time.Clock;
import java.time.Instant;
import java.util.Base64;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.need;

/** Independent bounded Win32 clipboard read. It never writes the clipboard, sends a Game action, or reads a path. */
public final class NativeCoaClipboard {
    private static final int CF_UNICODETEXT=13,MAXIMUM_UNICODE_BYTES=2*(CoaData.V2_MAX_BYTES+1);
    public interface ClipboardUser extends StdCallLibrary {
        boolean OpenClipboard(HWND owner);boolean CloseClipboard();boolean IsClipboardFormatAvailable(int format);
        HANDLE GetClipboardData(int format);int GetClipboardSequenceNumber();
    }
    public interface ClipboardKernel extends StdCallLibrary {SIZE_T GlobalSize(HANDLE memory);Pointer GlobalLock(HANDLE memory);boolean GlobalUnlock(HANDLE memory);}
    private static final class Api {
        static final ClipboardUser USER=Native.load("user32",ClipboardUser.class,W32APIOptions.DEFAULT_OPTIONS);
        static final ClipboardKernel KERNEL=Native.load("kernel32",ClipboardKernel.class,W32APIOptions.DEFAULT_OPTIONS);
    }
    public enum Status {TEXT,NO_UNICODE,NON_ASCII}
    public record Sample(long sequenceBefore,long sequenceAfter,Instant observedAt,Status status,String unicodeBase64){
        public Sample{
            need(sequenceBefore>=0&&sequenceBefore<=0xffff_ffffL&&sequenceBefore==sequenceAfter,"independent clipboard sequence changed during observation");Objects.requireNonNull(observedAt);Objects.requireNonNull(status);Objects.requireNonNull(unicodeBase64);
            byte[] original=Base64.getDecoder().decode(unicodeBase64);need(Base64.getEncoder().encodeToString(original).equals(unicodeBase64),"clipboard original base64 is not canonical");
            need(original.length<=MAXIMUM_UNICODE_BYTES,"clipboard original exceeds source bound");
            if(status==Status.NO_UNICODE)need(original.length==0,"absent Unicode clipboard cannot expose bytes");
            else {need(original.length>=2&&original.length%2==0&&original[original.length-1]==0&&original[original.length-2]==0,"clipboard original requires its aligned Unicode terminator");
                boolean ascii=true;for(int i=0;i<original.length-2;i+=2){int character=(original[i]&255)|((original[i+1]&255)<<8);need(character!=0,"clipboard original includes bytes after an earlier terminator");ascii&=character<128;}
                need((status==Status.TEXT)==ascii,"clipboard text status differs from actual UTF16 bytes");
            }
        }
        public Optional<String> source(){if(status!=Status.TEXT)return Optional.empty();byte[] bytes=Base64.getDecoder().decode(unicodeBase64);StringBuilder text=new StringBuilder(bytes.length/2-1);for(int i=0;i<bytes.length-2;i+=2)text.append((char)(bytes[i]&255));return Optional.of(text.toString());}
        public RawJson encode(){return raw(empty().put("schema","xar.independent-coa-clipboard/v1").put("sequence_before",sequenceBefore).put("sequence_after",sequenceAfter).put("observed_at",observedAt.toString()).put("status",status.name()).put("unicode_base64",unicodeBase64).put("read_only",true));}
        public static Sample decode(RawJson original){ObjectNode n=object(original);Set<String> fields=Set.of("schema","sequence_before","sequence_after","observed_at","status","unicode_base64","read_only");need(n.properties().stream().map(java.util.Map.Entry::getKey).collect(java.util.stream.Collectors.toSet()).equals(fields),"clipboard original fields differ");need(string(n,"schema").equals("xar.independent-coa-clipboard/v1")&&n.get("read_only").isBoolean()&&n.get("read_only").booleanValue(),"clipboard original schema/read-only flag differs");
            return new Sample(u32(n,"sequence_before"),u32(n,"sequence_after"),Instant.parse(string(n,"observed_at")),Status.valueOf(string(n,"status")),string(n,"unicode_base64"));
        }
        private static long u32(ObjectNode n,String field){JsonNode value=n.get(field);need(value!=null&&value.isIntegralNumber()&&value.canConvertToLong()&&value.longValue()>=0&&value.longValue()<=0xffff_ffffL,"exact unsigned32 clipboard sequence required");return value.longValue();}
    }
    private final Clock clock;
    public NativeCoaClipboard(Clock actualClock){clock=Objects.requireNonNull(actualClock);}
    public Sample read()throws IOException{
        if(!System.getProperty("os.name").startsWith("Windows"))throw new IOException("independent Win32 clipboard observation unavailable");
        long before=Integer.toUnsignedLong(Api.USER.GetClipboardSequenceNumber());
        if(!Api.USER.OpenClipboard(null))throw new IOException("independent clipboard is busy/unavailable; native source completion remains unresolved");
        byte[] original;Status status;long after;IOException closing=null;
        try{
            if(!Api.USER.IsClipboardFormatAvailable(CF_UNICODETEXT)){original=new byte[0];status=Status.NO_UNICODE;}
            else {
                HANDLE memory=Api.USER.GetClipboardData(CF_UNICODETEXT);if(memory==null||memory.getPointer()==null)throw new IOException("independent clipboard Unicode handle unavailable");
                long bytes=Api.KERNEL.GlobalSize(memory).longValue();if(bytes<2||bytes>MAXIMUM_UNICODE_BYTES+65536L||bytes%2!=0)throw new IOException("independent clipboard Unicode allocation exceeds finite source bound");
                Pointer pointer=Api.KERNEL.GlobalLock(memory);if(pointer==null)throw new IOException("independent clipboard Unicode memory cannot be read");
                byte[] allocated;try{allocated=pointer.getByteArray(0,(int)Math.min(bytes,MAXIMUM_UNICODE_BYTES));}finally{Api.KERNEL.GlobalUnlock(memory);}
                int end=-1;boolean ascii=true;for(int i=0;i<allocated.length;i+=2){int character=(allocated[i]&255)|((allocated[i+1]&255)<<8);if(character==0){end=i+2;break;}ascii&=character<128;}
                if(end<0)throw new IOException("independent clipboard has no bounded UTF16 terminator");original=java.util.Arrays.copyOf(allocated,end);status=ascii?Status.TEXT:Status.NON_ASCII;
            }
            after=Integer.toUnsignedLong(Api.USER.GetClipboardSequenceNumber());if(before!=after)throw new IOException("independent clipboard changed while being read");
        }finally{if(!Api.USER.CloseClipboard())closing=new IOException("independent clipboard close failed; result cannot be accepted");}
        if(closing!=null)throw closing;return new Sample(before,after,clock.instant(),status,Base64.getEncoder().encodeToString(original));
    }
}
