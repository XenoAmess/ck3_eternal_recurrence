package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Native;
import com.sun.jna.Platform;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.SharedSourceFiles.DirectoryIdentity;
import org.xar.ck3.control.build.SharedSourceFiles.NativeFile;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyQueryHistoryStore.StoredFile;

/**
 * Read one complete Driver sidecar through its successful numeric history summary.
 * No directory discovery, latest-file selection, retry, write, repair, current query or Game qualification.
 */
public final class ArmyQueryHistoryReference {
    private static final int CHUNK=1024*1024;
    /** Exactly one producer LF may follow the maximum complete numeric Driver JSON. */
    public static final int MAXIMUM_ARTIFACT_BYTES=RawJson.MAXIMUM_BYTES+1;
    private ArmyQueryHistoryReference(){}

    /** Native identity and time remain exact decimal text, independent of JavaScript Number. */
    public record FileStamp(String device,String inode,String creationFiletime,String modifiedFiletime,long bytes) {
        public FileStamp {
            decimal(device,64);decimal(inode,128);decimal(creationFiletime,64);decimal(modifiedFiletime,64);
            if(bytes<0)throw new IllegalArgumentException("actual nonnegative held file size required");
        }
    }
    public record Resolved(Path evidenceDirectory,Path file,DirectoryIdentity directoryIdentity,FileStamp fileIdentity) {
        public Resolved {
            absolute(evidenceDirectory);absolute(file);Objects.requireNonNull(directoryIdentity);Objects.requireNonNull(fileIdentity);
            if(!file.getParent().equals(evidenceDirectory))throw new IllegalArgumentException("one exact resolved evidence leaf required");
        }
    }
    /** The same continuously retained file handle supplies bytes and both metadata observations. */
    public interface ReadHandle extends AutoCloseable {
        FileStamp stamp()throws IOException;
        int read(byte[] target,int offset,int length)throws IOException;
        @Override void close()throws IOException;
    }
    public interface FileIO {
        Resolved resolve(Path suppliedFile,Path actualEvidenceDirectory)throws IOException;
        ReadHandle open(Resolved actual)throws IOException;
        void verify(Resolved actual,FileStamp actualHeldFile)throws IOException;
    }
    /** Issued only after exact physical and original Driver identity checks; still observational DATA. */
    public static final class ReadResult {
        private final RawJson completeDriver;
        private final StoredFile reference;
        private final FileStamp identity;
        private final RawJson summary;
        private ReadResult(RawJson completeDriver,StoredFile reference,FileStamp identity,RawJson summary) {
            this.completeDriver=completeDriver;this.reference=reference;this.identity=identity;this.summary=summary;
        }
        public RawJson completeDriver(){return completeDriver;}
        public StoredFile reference(){return reference;}
        public FileStamp observedIdentity(){return identity;}
        public RawJson originalSummary(){return summary;}
    }

    public static ReadResult read(RawJson numericSummary,Path actualEvidenceDirectory,long maximumBytes)throws IOException {
        return read(numericSummary,actualEvidenceDirectory,maximumBytes,new WindowsFileIO());
    }
    /** Explicit installed I/O boundary, also used by tests to exercise real failure and identity drift paths. */
    public static ReadResult read(RawJson numericSummary,Path actualEvidenceDirectory,long maximumBytes,FileIO io)throws IOException {
        Objects.requireNonNull(numericSummary);Objects.requireNonNull(io);absolute(actualEvidenceDirectory);
        if(maximumBytes<=0)throw new IllegalArgumentException("positive explicitly admitted Army sidecar read limit required");
        ObjectNode summary=ArmyJson.parse(numericSummary.bytes());
        require(text(summary,"history_summary_schema").equals(ArmyQueryHistoryStore.SUMMARY_SCHEMA)
                &&bool(summary,"full_result_preserved")&&text(summary,"step").equals(ArmyStrengths.STEP),
                "no successful complete Army sidecar reference is available");
        ObjectNode reference=object(required(summary,"raw_result_reference"));
        require(text(reference,"kind").equals(ArmyQueryHistoryStore.REFERENCE_KIND)&&!bool(reference,"wire_bytes_preserved"),
                "Army sidecar reference kind or wire-byte claim differs");
        BigInteger size=positive(reference,"bytes");
        require(size.compareTo(BigInteger.valueOf(maximumBytes))<=0,"Army sidecar exceeds caller admitted read budget");
        // The Store writes the original numeric JSON plus exactly one LF; RawJson itself remains bounded.
        require(size.compareTo(BigInteger.valueOf(MAXIMUM_ARTIFACT_BYTES))<=0,"Army sidecar exceeds numeric Driver plus producer delimiter contract");
        long expected=size.longValueExact();
        String expectedHash=text(reference,"sha256");
        require(expectedHash.matches("[0-9a-fA-F]{64}"),"exact Army sidecar SHA-256 required");
        Path supplied=Path.of(text(reference,"path"));
        require(supplied.isAbsolute()&&supplied.getFileName()!=null
                &&supplied.getFileName().toString().matches("army-query-[0-9a-f]{32}\\.json"),
                "absolute exact Army sidecar filename required");
        Resolved resolved=io.resolve(supplied,actualEvidenceDirectory);
        require(resolved.file().getFileName().toString().matches("army-query-[0-9a-f]{32}\\.json"),
                "resolved Army sidecar filename differs");
        MessageDigest hash=digest();ByteArrayOutputStream bytes=new ByteArrayOutputStream((int)Math.min(expected,65_536));
        FileStamp before;long total=0;
        try(ReadHandle held=io.open(resolved)){
            before=held.stamp();
            require(before.equals(resolved.fileIdentity())&&before.bytes()==expected,
                    "Army sidecar actual identity/size disagrees with successful receipt");
            io.verify(resolved,before);
            byte[] chunk=new byte[CHUNK];
            while(true){
                int requested=(int)Math.min(CHUNK,expected-total+1);
                int count=held.read(chunk,0,requested);
                if(count==-1)break;
                if(count<=0||count>requested)throw new IOException("Army sidecar read made no valid bounded progress");
                total+=count;
                require(total<=expected,"Army sidecar grew beyond its successful receipt");
                hash.update(chunk,0,count);bytes.write(chunk,0,count);
            }
            FileStamp after=held.stamp();
            require(before.equals(after),"Army sidecar held identity, size or modification time changed");
            io.verify(resolved,after);
        }
        String observedHash=HexFormat.of().formatHex(hash.digest());
        require(total==expected&&observedHash.equalsIgnoreCase(expectedHash),"Army sidecar bytes disagree with successful receipt");
        byte[] original=bytes.toByteArray();strictUtf8(original);
        int jsonBytes=jsonLength(original.length,original[original.length-1]&255);
        byte[] numeric=jsonBytes==original.length?original:Arrays.copyOf(original,jsonBytes);
        ObjectNode body=ArmyJson.parse(numeric);
        requireBody(summary,body);
        return new ReadResult(new RawJson(numeric),new StoredFile(resolved.file(),total,observedHash),before,numericSummary);
    }

    /** Remove only the one terminal producer LF, never whitespace-trim or expand RawJson. */
    static int jsonLength(long artifactBytes,int lastByte){
        require(artifactBytes>0&&artifactBytes<=MAXIMUM_ARTIFACT_BYTES,"bounded original Army artifact required");
        long numeric=artifactBytes-(lastByte==10?1:0);
        require(numeric>0&&numeric<=RawJson.MAXIMUM_BYTES,"complete Driver exceeds RawJson without the sole producer LF");
        return Math.toIntExact(numeric);
    }

    private static void requireBody(ObjectNode summary,ObjectNode body){
        for(String key:List.of("step","accepted","query_sequence","queried_snapshot_id","queried_revision","queried_native_revision")){
            JsonNode expected=required(summary,key),actual=required(body,key);
            require(expected.equals(actual),"Army sidecar body disagrees with exact query summary: "+key);
        }
        require(text(body,"step").equals(ArmyStrengths.STEP),"Army sidecar body step differs");
        bool(body,"accepted");bool(summary,"accepted"); // false remains an original failed Driver result, not Game success.
        for(String key:List.of("query_sequence","queried_revision","queried_native_revision")){
            positive(summary,key);positive(body,key); // queried_revision is strictly >0 in the original reader.
        }
        require(!text(body,"queried_snapshot_id").isEmpty(),"Army sidecar queried snapshot ID is empty");
        JsonNode armies=required(body,"army_strengths");
        require(armies.isArray(),"complete original Driver Army collection required");
        JsonNode count=required(summary,"army_count");
        require(count.isIntegralNumber()&&count.bigIntegerValue().equals(BigInteger.valueOf(armies.size())),
                "Army sidecar Army count differs from actual body");
        for(String key:List.of("status","backend_id","army_strengths_profile","army_observed_phase_coverage"))
            if(summary.has(key))require(summary.get(key).equals(body.has(key)?body.get(key):NullNode.instance),
                    "Army sidecar source/profile differs from summary: "+key);
    }
    private static void strictUtf8(byte[] bytes)throws IOException {
        try {
            String text=StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            if((!text.isEmpty()&&text.charAt(0)=='\ufeff')||text.indexOf(0)>=0)
                throw new IOException("Army sidecar must be original UTF-8 JSON without BOM/NUL encoding substitution");
        }catch(CharacterCodingException invalid){throw new IOException("Army sidecar is not strict original UTF-8",invalid);}
    }
    private static ObjectNode object(JsonNode value){require(value instanceof ObjectNode,"Army sidecar reference object required");return (ObjectNode)value;}
    private static JsonNode required(ObjectNode row,String key){require(row.has(key),"missing original Army sidecar field: "+key);return row.get(key);}
    private static String text(ObjectNode row,String key){JsonNode value=required(row,key);require(value.isTextual(),"Army sidecar text field required: "+key);return value.textValue();}
    private static boolean bool(ObjectNode row,String key){JsonNode value=required(row,key);require(value.isBoolean(),"Army sidecar strict Boolean required: "+key);return value.booleanValue();}
    private static BigInteger positive(ObjectNode row,String key){JsonNode value=required(row,key);require(value.isIntegralNumber()&&value.bigIntegerValue().signum()>0,"Army sidecar positive original integer required: "+key);return value.bigIntegerValue();}
    private static void require(boolean condition,String message){if(!condition)throw new IllegalArgumentException(message);}
    private static Path absolute(Path path){Objects.requireNonNull(path);require(path.isAbsolute()&&path.normalize().equals(path)&&path.getParent()!=null,"actual absolute normalized evidence path required");return path;}
    private static void decimal(String value,int bits){require(value!=null&&value.matches("0|[1-9][0-9]*")&&new BigInteger(value).bitLength()<=bits,"exact native file identity/time decimal required");}
    private static MessageDigest digest(){try{return MessageDigest.getInstance("SHA-256");}catch(NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}}
    private static FileStamp stamp(NativeFile file){return new FileStamp(file.volumeSerialDecimal(),file.fileIdDecimal(),file.creationFiletimeDecimal(),file.lastWriteFiletimeDecimal(),file.logicalBytes());}

    /** Existing shared native metadata provider, with reads from the very same retained Win32 handle. */
    public static final class WindowsFileIO implements FileIO {
        @Override public Resolved resolve(Path suppliedFile,Path actualEvidenceDirectory)throws IOException {
            if(!Platform.isWindows())throw new IOException("actual retained Windows sidecar identity provider unavailable");
            SharedSourceFiles.plainAncestors(suppliedFile);SharedSourceFiles.plainAncestors(actualEvidenceDirectory);
            Path folder=actualEvidenceDirectory.toRealPath(),file=suppliedFile.toRealPath();
            if(!file.getParent().equals(folder))throw new IOException("Army sidecar is outside the exact session evidence leaf");
            return new Resolved(folder,file,SharedSourceFiles.nativeDirectory(folder),stamp(SharedSourceFiles.nativeFile(file)));
        }
        @Override public ReadHandle open(Resolved actual)throws IOException {
            Objects.requireNonNull(actual);
            HANDLE handle=Kernel32.INSTANCE.CreateFile(extended(actual.file()),0x80000080,7,null,3,0x08200000,null);
            if(WinBase.INVALID_HANDLE_VALUE.equals(handle))throw new IOException("Army sidecar open Win32="+Native.getLastError());
            try {return new WindowsHandle(handle);}
            catch(IOException|RuntimeException|Error failure){if(!Kernel32.INSTANCE.CloseHandle(handle))failure.addSuppressed(new IOException("Army sidecar close Win32="+Native.getLastError()));throw failure;}
        }
        @Override public void verify(Resolved actual,FileStamp held)throws IOException {
            SharedSourceFiles.plainAncestors(actual.file());
            if(!actual.directoryIdentity().equals(SharedSourceFiles.nativeDirectory(actual.evidenceDirectory()))
                    ||!held.equals(stamp(SharedSourceFiles.nativeFile(actual.file()))))
                throw new IOException("Army sidecar exact path, directory identity or held file changed");
        }
        private static String extended(Path path){
            String value=path.toString();if(value.startsWith("\\\\?\\"))return value;
            return value.startsWith("\\\\")?"\\\\?\\UNC\\"+value.substring(2):"\\\\?\\"+value;
        }
    }
    private static final class WindowsHandle implements ReadHandle {
        private final HANDLE actual;private boolean closed;
        WindowsHandle(HANDLE actual)throws IOException {this.actual=actual;SharedSourceFiles.nativeHeldFile(actual);}
        @Override public FileStamp stamp()throws IOException {requireOpen();return ArmyQueryHistoryReference.stamp(SharedSourceFiles.nativeHeldFile(actual));}
        @Override public int read(byte[] target,int offset,int length)throws IOException {
            requireOpen();Objects.checkFromIndexSize(offset,length,target.length);
            byte[] nativeBuffer=offset==0&&length==target.length?target:new byte[length];IntByReference read=new IntByReference();
            if(!Kernel32.INSTANCE.ReadFile(actual,nativeBuffer,length,read,null))throw new IOException("Army sidecar read Win32="+Native.getLastError());
            int count=read.getValue();if(count<0||count>length)throw new IOException("invalid actual held sidecar read size");
            if(count>0&&nativeBuffer!=target)System.arraycopy(nativeBuffer,0,target,offset,count);
            return count==0?-1:count;
        }
        private void requireOpen()throws IOException {if(closed)throw new IOException("original Army sidecar handle is closed");}
        @Override public void close()throws IOException {
            if(closed)return;closed=true;if(!Kernel32.INSTANCE.CloseHandle(actual))throw new IOException("Army sidecar close Win32="+Native.getLastError());
        }
    }
}

