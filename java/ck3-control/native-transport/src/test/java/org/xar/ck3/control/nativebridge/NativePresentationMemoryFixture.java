package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.presentation.PresentationOriginals;
import org.xar.ck3.control.contracts.presentation.PresentationRequest;

/** One self-owned software memory boundary for actual transport/central/archive tests. No native mapping or permit mint. */
public final class NativePresentationMemoryFixture {
    private NativePresentationMemoryFixture() { }
    public static final class Scenario implements AutoCloseable {
        private final Memory memory;
        private final NativePresentationTransport transport;
        private final PresentationRequest.Owner owner;
        private Scenario(PresentationRequest.Owner owner,PresentationOriginals sameWriterOriginals)throws IOException {
            this.owner=owner;memory=new Memory(owner.processId());
            var game=new GameGeneration(owner.processId(),new PythonOnlyUInt64(new BigInteger(owner.processBirthFiletime())));
            var config=new NativePipeEndpoint.Config("\\\\.\\pipe\\explicit-presentation-software-test",owner.machineId(),game,owner.sessionId(),
                    "explicit-software",owner.executableSha256(),"explicit-software-only");
            transport=new NativePresentationTransport(config,owner,memory,sameWriterOriginals);
        }
        public NativePresentationTransport transport(){return transport;}
        public PresentationRequest request(String requestId) {
            long previous=memory.u32(16),baseline=memory.u32(20);
            return new PresentationRequest(requestId,Instant.now().minusMillis(1),owner,
                    new PresentationRequest.Frame("explicit-software-snapshot","2","7",73,1000),PresentationRequest.Mode.REALM,
                    previous,PresentationRequest.nextSequence(previous),baseline,Long.toUnsignedString(memory.uptime+10000),"4096",Float.floatToRawIntBits(.32f),"",
                    Optional.empty(),List.of(reference("explicit-software-preparation".getBytes(java.nio.charset.StandardCharsets.UTF_8))));
        }
        public void publishResult(long requestSequence,int status) {
            ByteBuffer result=ByteBuffer.allocate(65640).order(ByteOrder.LITTLE_ENDIAN);
            result.putInt((int)requestSequence).putInt(status).putInt(73).putInt(1000).putInt(1).putInt(1280).putInt(720).putInt(3);
            result.putInt(1).putInt(2).putInt(30).putInt(40);
            for(int i=0;i<12;i++)result.putFloat((i%6)+1);result.putInt(12).putInt(0).putInt(42);
            publishOriginalResult(result.array(),new byte[168]);
        }
        /** Explicit software Native side: exact original bytes, one odd/copy/even publication. */
        public void publishOriginalResult(byte[] result,byte[] diagnostics) {
            if(result.length!=65640||diagnostics.length!=168)throw new IllegalArgumentException("exact original software regions required");
            long next=(memory.u32(20)+2)&0xffff_fffeL;
            memory.bytes.putInt(20,(int)(next-1));memory.put(192,result);memory.put(0x18000,diagnostics);memory.bytes.putInt(20,(int)next);
        }
        public void publishTrackingCapability(boolean torn){
            int base=0x18400;memory.bytes.putInt(base,0x54434158).putInt(base+4,1).putInt(base+8,4384).putInt(base+12,(int)owner.processId())
                .putInt(base+16,torn?1:2).putInt(base+20,1).putLong(base+24,1);
        }
        public PresentationRequest trackingRequest(String id){
            var b=request(id);return new PresentationRequest(id,b.preparedAt(),b.owner(),b.frame(),PresentationRequest.Mode.TRACKED_HOTSPOT,
             b.previousRequestSequence(),b.requestSequence(),b.baselineResultSequence(),b.expiresUptimeMs(),b.hwnd(),Float.floatToRawIntBits(.15f),"",
             Optional.of(new PresentationRequest.Tracking("1","9007199254740993",7,1000,1024,List.of(new PresentationRequest.Province(9,"b_test")))),b.preparationEvidence());
        }
        public void publishTrackingResult(PresentationRequest request,boolean foreign){
            int base=0x18400;var t=request.tracking().orElseThrow();byte[] raw=ByteBuffer.allocate(80).order(ByteOrder.LITTLE_ENDIAN)
             .putInt((int)request.requestSequence()).putInt(1).putLong(new BigInteger(t.ownerEpoch()).longValue()).putLong(new BigInteger(t.scopeGeneration()).longValue())
             .putLong(100000).putInt(foreign?74:request.frame().actor()).putInt(t.fullArmyId()).putInt(Math.addExact(request.frame().dateRaw(),1)).putInt(9).putInt(0).putInt(1)
             .putInt(32).putInt(1).putLong(2).putInt(0).putInt(0).array();
            memory.bytes.putInt(base+32,1);memory.put(base+4304,raw);memory.bytes.putInt(base+32,2);
        }
        public void raceTrackingDuringCopy(){memory.raceTracking=true;}
        public byte[] originalTrackingRequest(){return memory.copy(0x18400+40,4264);}
        public void oddResultPublication(){memory.bytes.putInt(20,1);}
        public void raceResultDuringCopy(){memory.raceDuringCopy=true;}
        public void failSource(){memory.alive=false;}
        public void failAfterPhysicalOdd(){memory.failAfterOdd=true;}
        public void failCopyAfterPartial(){memory.failCopy=true;}
        public void failEvenPublication(){memory.failEven=true;}
        public void replaceWindow(){memory.hwnd="8192";}
        public void advanceUptime(long actualSoftwareUptime){memory.uptime=actualSoftwareUptime;}
        public int actualReads(){return memory.reads;}
        public int actualWriteAttempts(){return memory.writes;}
        public int actualSuccessfulOddClaims(){return memory.oddClaims;}
        public byte[] originalHeader(){return memory.copy(0,24);}
        public byte[] originalRequest(){return memory.copy(24,168);}
        public PresentationRequest.Owner owner(){return owner;}
        @Override public void close()throws IOException {transport.close();}
    }
    public static Scenario create(PresentationRequest.Owner actualSoftwareOwner,PresentationOriginals actualOriginals)throws IOException {
        return new Scenario(actualSoftwareOwner,actualOriginals);
    }
    private static final class Memory implements NativePresentationMemoryPort {
        final ByteBuffer bytes=ByteBuffer.allocateDirect(131072).order(ByteOrder.LITTLE_ENDIAN);
        boolean alive=true,closed,raceDuringCopy,raceTracking,failAfterOdd,failCopy,failEven;int reads,writes,oddClaims;
        long uptime=100000;String hwnd="4096";
        Memory(long pid){bytes.putInt(0,0x43524158).putInt(4,1).putInt(8,(int)pid);}
        @Override public void verify()throws IOException {if(!alive||closed)throw new IOException("actual software mapping source unavailable");}
        @Override public byte[] read(int offset,int length)throws IOException {
            verify();reads++;byte[] copy=copy(offset,length);
            if(raceDuringCopy&&offset==192){bytes.putInt(20,bytes.getInt(20)+2);raceDuringCopy=false;}
            if(raceTracking&&offset==0x18400+4304){bytes.putInt(0x18400+32,bytes.getInt(0x18400+32)+2);raceTracking=false;}
            return copy;
        }
        @Override public boolean compareAndSetSequence(int offset,long expected,long update)throws IOException {
            verify();if(offset!=16)throw new IOException("wrong original sequence field");writes++;
            if(u32(offset)!=expected)return false;
            bytes.putInt(offset,(int)update);
            if((update&1)!=0){oddClaims++;if(failAfterOdd)throw new IOException("actual software fault after odd store");}
            else if(failEven)throw new IOException("actual software fault after even store");
            return true;
        }
        @Override public void writeRequest(byte[] request)throws IOException {
            verify();writes++;
            if(failCopy){put(24,java.util.Arrays.copyOf(request,37));throw new IOException("actual software partial request copy");}
            put(24,request);
        }
        @Override public void writeTracking(byte[] raw)throws IOException{verify();if(raw.length!=4264)throw new IOException("tracking extent");writes++;put(0x18400+40,raw);}
        @Override public void flush()throws IOException {verify();}
        @Override public long uptimeMillis()throws IOException {verify();return uptime;}
        @Override public String ownedDesktopOneWindow()throws IOException {verify();return hwnd;}
        @Override public void close(){closed=true;}
        long u32(int offset){return Integer.toUnsignedLong(bytes.getInt(offset));}
        byte[] copy(int offset,int length){byte[] out=new byte[length];ByteBuffer duplicate=bytes.duplicate();duplicate.position(offset);duplicate.get(out);return out;}
        void put(int offset,byte[] source){ByteBuffer duplicate=bytes.duplicate();duplicate.position(offset);duplicate.put(source);}
    }
    private static ExactRef reference(byte[] raw) {
        try{return new ExactRef("explicit-software-presentation/"+HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)),raw.length,
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));}
        catch(java.security.NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}
    }
}
