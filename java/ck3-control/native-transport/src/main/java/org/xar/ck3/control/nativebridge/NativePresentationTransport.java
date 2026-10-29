package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.PresentationPermit;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.presentation.OriginalOutcome;
import org.xar.ck3.control.contracts.presentation.OriginalOutcome.Phase;
import org.xar.ck3.control.contracts.presentation.PresentationObservation;
import org.xar.ck3.control.contracts.presentation.PresentationOriginals;
import org.xar.ck3.control.contracts.presentation.PresentationOriginals.ArtifactRole;
import org.xar.ck3.control.contracts.presentation.PresentationOriginals.OriginalArtifact;
import org.xar.ck3.control.contracts.presentation.PresentationRequest;
import org.xar.ck3.control.contracts.presentation.PresentationIntent;
import org.xar.ck3.control.contracts.presentation.PresentationCapture;

/** One canonical permitted original mapping post. Publication, native ACK and camera effect are distinct. */
public final class NativePresentationTransport implements AutoCloseable {
    public record SourceUnit(String targetRelative,Class<?> actualClass) { }
    /** Exact physical units for the sole pre-Core source inventory, including the private Win32 implementation. */
    public static List<SourceUnit> sourceUnits(){
        String root="native-transport/src/main/java/org/xar/ck3/control/nativebridge/";
        return List.of(new SourceUnit(root+"NativePresentationTransport.java",NativePresentationTransport.class),
                new SourceUnit(root+"NativePresentationMemoryPort.java",NativePresentationMemoryPort.class),
                new SourceUnit(root+"NativePresentationWin32.java",NativePresentationWin32.class));
    }
    public record Inspection(PresentationRequest.Owner owner,Instant observedAt,long previousRequestSequence,
            long baselineResultSequence,String uptimeMillis,String hwnd,byte[] originalHeader) {
        public Inspection{originalHeader=originalHeader.clone();}
        @Override public byte[] originalHeader(){return originalHeader.clone();}
    }
    /** Bounded in-memory failure custody, including when the actual finite archive itself fails. */
    public record Retained(PresentationRequest request,Phase phase,byte[] originalRequest,byte[] beforeHeader,byte[] afterHeader) {
        public Retained{originalRequest=originalRequest.clone();beforeHeader=beforeHeader.clone();afterHeader=afterHeader.clone();}
        @Override public byte[] originalRequest(){return originalRequest.clone();}
        @Override public byte[] beforeHeader(){return beforeHeader.clone();}
        @Override public byte[] afterHeader(){return afterHeader.clone();}
    }
    private final NativePipeEndpoint.Config config;private final PresentationRequest.Owner owner;
    private final NativePresentationMemoryPort memory;private final PresentationOriginals originals;
    private boolean closed,uncertain;private Optional<Retained> retained=Optional.empty();
    NativePresentationTransport(NativePipeEndpoint.Config config,PresentationRequest.Owner owner,
            NativePresentationMemoryPort memory,PresentationOriginals originals)throws IOException {
        this.config=Objects.requireNonNull(config);this.owner=Objects.requireNonNull(owner);
        this.memory=Objects.requireNonNull(memory);this.originals=Objects.requireNonNull(originals);requireOwner(owner);
    }
    /** Actual Root calls after adoption; this never launches, injects or creates a mapping. */
    public static NativePresentationTransport open(NativePipeEndpoint.Config actual,PresentationRequest.Owner owner,
            NativeProcessGuard actualGuard,PresentationOriginals sameWriterArchive)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(owner);Objects.requireNonNull(actualGuard);Objects.requireNonNull(sameWriterArchive);
        if(!actual.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("presentation machine is not this execution machine");
        if(!owner.machineId().equals(actual.machineId())||!owner.sessionId().equals(actual.sessionId())||owner.processId()!=actual.game().pid()
                ||!owner.processBirthFiletime().equals(actual.game().creationFiletime().value().toString())
                ||!PresentationRequest.EXECUTABLE_SHA256.equalsIgnoreCase(actual.expectedGameSha256()))
            throw new IOException("original exact reviewed presentation owner required before mapping access");
        NativePresentationWin32 memory=new NativePresentationWin32(actual,actualGuard);
        try{return new NativePresentationTransport(actual,owner,memory,sameWriterArchive);}
        catch(IOException|RuntimeException failure){try{memory.close();}catch(IOException close){failure.addSuppressed(close);}throw failure;}
    }
    private void requireOwner(PresentationRequest.Owner candidate)throws IOException {
        if(!owner.equals(candidate)||!candidate.machineId().equals(config.machineId())||!candidate.sessionId().equals(config.sessionId())
                ||candidate.processId()!=config.game().pid()||!candidate.processBirthFiletime().equals(config.game().creationFiletime().value().toString())
                ||!candidate.executableSha256().equalsIgnoreCase(config.expectedGameSha256())||new BigInteger(candidate.connectionGeneration()).signum()<=0)
            throw new IOException("presentation crossed actual original machine/process/birth/session/EXE/episode/connection");
    }
    private void check(Instant deadline)throws IOException {
        Objects.requireNonNull(deadline);Duration remaining=Duration.between(Instant.now(),deadline);
        if(closed||Thread.currentThread().isInterrupted()||remaining.isNegative()||remaining.isZero()||remaining.compareTo(Duration.ofMinutes(2))>0)
            throw new IOException("finite current presentation IO deadline unavailable");memory.verify();
    }
    public synchronized Inspection inspect(Instant deadline)throws IOException {
        check(deadline);byte[] first=memory.read(0,24);long request=u32(first,16),result=u32(first,20);
        if((request&1)!=0||(result&1)!=0)throw new IOException("original mapping publication in progress; no prepared source invented");
        String hwnd=memory.ownedDesktopOneWindow(),uptime=Long.toUnsignedString(memory.uptimeMillis());
        byte[] after=memory.read(0,24);check(deadline);
        if(!java.util.Arrays.equals(first,after))throw new IOException("actual presentation preparation crossed a publication");
        return new Inspection(owner,Instant.now(),request,result,uptime,hwnd,first);
    }
    /** The central private permit is consumed immediately before the first physical CAS. No public DATA grants post. */
    public synchronized OriginalOutcome post(PresentationPermit permit,PresentationRequest request,Instant deadline) {
        Objects.requireNonNull(permit);Objects.requireNonNull(request);Objects.requireNonNull(deadline);
        List<ExactRef> evidence=new ArrayList<>();byte[] before=new byte[0],after=new byte[0],raw=request.nativeBytes();
        boolean attempted=false;Phase phase=Phase.BEFORE_ODD;
        try {
            check(deadline);requireOwner(request.owner());
            if(uncertain)throw new IOException("original physical outcome unresolved; no new mapping post");
            if(request.mode()!=PresentationRequest.Mode.REALM&&request.mode()!=PresentationRequest.Mode.QUERY)
                throw new IOException("this actual producer supports reviewed original realm/query only; other Native modes require their actual scoped producer");
            if(request.preparedAt().isAfter(Instant.now())||request.paddingFloatBits()!=Float.floatToRawIntBits(request.mode()==PresentationRequest.Mode.REALM?.32f:.15f))
                throw new IOException("original actual preparation time and realm/query padding required");
            before=memory.read(0,24);
            if(u32(before,16)!=request.previousRequestSequence())throw new IOException("original request sequence changed before post");
            BigInteger now=new BigInteger(Long.toUnsignedString(memory.uptimeMillis())),expires=new BigInteger(request.expiresUptimeMs());
            if(expires.compareTo(now)<=0||expires.subtract(now).compareTo(BigInteger.valueOf(10000))>0)
                throw new IOException("original ten-second Native uptime lease unavailable");
            if(!request.hwnd().equals(memory.ownedDesktopOneWindow()))throw new IOException("prepared HWND differs from actual owned Desktop1 window");
            ExactRef requestRef=preserve(ArtifactRole.REQUEST,raw);evidence.add(requestRef);
            ExactRef beforeRef=preserve(ArtifactRole.HEADER,before);evidence.add(beforeRef);check(deadline);
            if(new BigInteger(Long.toUnsignedString(memory.uptimeMillis())).compareTo(expires)>=0)
                throw new IOException("actual Native uptime lease expired before first physical attempt");
            permit.consume(request,deadline);
            attempted=true;
            long odd=(request.requestSequence()-1)&0xffff_ffffL;
            if(!memory.compareAndSetSequence(16,request.previousRequestSequence(),odd))
                return new OriginalOutcome.NotPosted(request,Instant.now(),"actual request CAS did not acquire the original even sequence",evidence);
            phase=Phase.ODD_STORED;check(deadline);memory.flush();
            memory.writeRequest(raw);phase=Phase.REQUEST_COPIED;check(deadline);memory.flush();
            phase=Phase.EVEN_PUBLICATION_UNCERTAIN;
            if(!memory.compareAndSetSequence(16,odd,request.requestSequence()))throw new IOException("original request publication was preempted");
            memory.flush();after=memory.read(0,24);check(deadline);
            if(u32(after,16)!=request.requestSequence())throw new IOException("actual even publication was replaced");
            phase=Phase.POSTED_OUTCOME_UNPERSISTED;Instant postedAt=Instant.now();
            ExactRef afterRef=preserve(ArtifactRole.HEADER,after);evidence.add(afterRef);
            var metadata=new OriginalOutcome.PostEvidence(owner,request.requestId(),postedAt,request.previousRequestSequence(),request.requestSequence(),
                    beforeRef,afterRef,requestRef,Optional.empty());
            byte[] originalMetadata=metadata.encode();ExactRef metadataRef=preserve(ArtifactRole.POST_METADATA,originalMetadata);evidence.add(metadataRef);
            var posted=new OriginalOutcome.Posted(request,postedAt,requestRef,Optional.empty(),metadataRef);
            posted.verifyOriginal(raw,Optional.empty(),originalMetadata,before,after);
            return posted;
        } catch(IOException|RuntimeException failure) {
            if(!attempted)return new OriginalOutcome.NotPosted(request,Instant.now(),reason(failure),evidence);
            uncertain=true;retained=Optional.of(new Retained(request,phase,raw,before,after));
            return new OriginalOutcome.Unknown(request,Instant.now(),phase,reason(failure),evidence);
        }
    }
    /** One source-checked sample only. Pending and late ACK reads never write or clear canonical UNKNOWN. */
    public synchronized PresentationObservation observe(PresentationRequest request,Instant deadline) {
        Objects.requireNonNull(request);List<ExactRef> evidence=new ArrayList<>();
        try {
            check(deadline);requireOwner(request.owner());byte[] header=memory.read(0,24);
            long sequence=u32(header,20);byte[] result=memory.read(192,65640),diagnostics=memory.read(0x18000,168);
            long trailing=u32(memory.read(20,4),0);check(deadline);
            ExactRef h=preserve(ArtifactRole.HEADER,header);evidence.add(h);
            ExactRef r=preserve(ArtifactRole.RESULT,result);evidence.add(r);
            ExactRef d=preserve(ArtifactRole.DIAGNOSTICS,diagnostics);evidence.add(d);
            var capture=new PresentationObservation.Capture(owner,Instant.now(),u32(header,16),sequence,trailing,h,r,d);
            return PresentationObservation.fromOriginal(request,capture,header,result,diagnostics);
        } catch(IOException|RuntimeException failure) {
            return new PresentationObservation.Unavailable(request,Instant.now(),reason(failure),evidence);
        }
    }

    /** Worker-only bounded IO. No archive callback or writer/session is used on this path. */
    public synchronized PresentationCapture capture(PresentationPermit permit,PresentationIntent intent) {
        Objects.requireNonNull(permit);Objects.requireNonNull(intent);
        PresentationIntent.Prepared prepared=null;byte[] after=new byte[0];boolean attempted=false;
        Phase phase=Phase.BEFORE_ODD;
        try {
            check(intent.deadline());requireOwner(intent.owner());if(uncertain)throw new IOException("unresolved mapping post; no replay");
            Inspection i=inspect(intent.deadline());Optional<PresentationRequest.Tracking> tracking=Optional.empty();
            if(intent.tracking().isPresent()){
                byte[] h=memory.read(PresentationRequest.TRACKING_OFFSET,40),tail=memory.read(PresentationRequest.TRACKING_OFFSET+16,4);
                var b=ByteBuffer.wrap(h).order(ByteOrder.LITTLE_ENDIAN);long cap=u32(h,16);
                if(b.getInt()!=0x54434158||b.getInt()!=1||b.getInt()!=4384||Integer.toUnsignedLong(b.getInt())!=owner.processId()
                        ||(cap&1)!=0||u32(tail,0)!=cap||u32(h,20)!=1||ByteBuffer.wrap(h).order(ByteOrder.LITTLE_ENDIAN).getLong(24)==0)
                    throw new IOException("tracking capability unavailable or torn");
                var scope=intent.tracking().orElseThrow();tracking=Optional.of(new PresentationRequest.Tracking(
                    Long.toUnsignedString(ByteBuffer.wrap(h).order(ByteOrder.LITTLE_ENDIAN).getLong(24)),scope.generation(),scope.armyId(),scope.start(),scope.end(),scope.provinces()));
            }
            prepared=new PresentationIntent.Prepared(intent,i.observedAt(),i.previousRequestSequence(),PresentationRequest.nextSequence(i.previousRequestSequence()),
                i.baselineResultSequence(),new BigInteger(i.uptimeMillis()).add(BigInteger.valueOf(10000)).toString(),i.hwnd(),tracking,i.originalHeader());
            check(intent.deadline());if(!java.util.Arrays.equals(i.originalHeader(),memory.read(0,24)))throw new IOException("mapping changed after actual preparation");
            permit.consume(prepared,intent.deadline());attempted=true;long odd=(prepared.sequence()-1)&0xffff_ffffL;
            if(!memory.compareAndSetSequence(16,prepared.previous(),odd))
                return capture(intent,prepared,PresentationCapture.Kind.NOT_POSTED,phase,"actual CAS did not acquire original sequence",after,Optional.empty());
            phase=Phase.ODD_STORED;check(intent.deadline());memory.flush();memory.writeRequest(prepared.requestBytes());phase=Phase.REQUEST_COPIED;
            if(prepared.trackingBytes().isPresent()){memory.writeTracking(prepared.trackingBytes().orElseThrow());phase=Phase.TRACKING_COPIED;}
            check(intent.deadline());memory.flush();phase=Phase.EVEN_PUBLICATION_UNCERTAIN;
            if(!memory.compareAndSetSequence(16,odd,prepared.sequence()))throw new IOException("camera even publication preempted");
            memory.flush();after=memory.read(0,24);check(intent.deadline());if(u32(after,16)!=prepared.sequence())throw new IOException("camera publication replaced");
            phase=Phase.POSTED_OUTCOME_UNPERSISTED;
            return capture(intent,prepared,PresentationCapture.Kind.POSTED,phase,"actual even publication; effect requires independent read",after,Optional.empty());
        }catch(IOException|RuntimeException failure){
            if(attempted){uncertain=true;return capture(intent,prepared,PresentationCapture.Kind.UNKNOWN,phase,reason(failure),after,Optional.empty());}
            return capture(intent,prepared,prepared==null?PresentationCapture.Kind.NOT_ATTEMPTED:PresentationCapture.Kind.NOT_POSTED,phase,reason(failure),after,Optional.empty());
        }
    }
    private static PresentationCapture capture(PresentationIntent intent,PresentationIntent.Prepared prepared,PresentationCapture.Kind kind,
            Phase phase,String reason,byte[] after,Optional<PresentationCapture.NativeSample> sample){
        return new PresentationCapture(intent,Optional.ofNullable(prepared),kind,phase,reason.length()>1000?reason.substring(0,1000):reason,Instant.now(),after,sample);
    }
    /** Later independent bounded mapping read. No post, polling loop or camera-success inference. */
    public synchronized PresentationCapture.NativeSample sample(PresentationRequest request,Instant deadline)throws IOException{
        check(deadline);requireOwner(request.owner());byte[] h=memory.read(0,24),r=memory.read(192,65640),d=memory.read(0x18000,168);
        long tail=u32(memory.read(20,4),0);Optional<byte[]> th=Optional.empty(),tr=Optional.empty();
        if(request.tracking().isPresent()){
            byte[] first=memory.read(PresentationRequest.TRACKING_OFFSET,40),raw=memory.read(PresentationRequest.TRACKING_OFFSET+4304,80);
            long seq=u32(first,32),end=u32(memory.read(PresentationRequest.TRACKING_OFFSET+32,4),0);
            if(seq!=0&&(seq&1)==0&&seq==end){th=Optional.of(first);tr=Optional.of(raw);}
        }
        check(deadline);return new PresentationCapture.NativeSample(Instant.now(),h,r,d,tail,th,tr);
    }

    private ExactRef preserve(ArtifactRole role,byte[] bytes) {
        OriginalArtifact artifact=new OriginalArtifact(role,bytes);ExactRef ref=originals.preservePresentationArtifact(artifact);
        artifact.requireReference(ref);
        if(!artifact.equals(originals.loadPresentationArtifact(role,ref))||!ref.equals(originals.presentationArtifactReferenceOf(artifact)))
            throw new IllegalStateException("actual same-writer presentation original custody changed");
        return ref;
    }
    private static long u32(byte[] bytes,int offset){return Integer.toUnsignedLong(ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).getInt(offset));}
    private static String reason(Exception failure){return failure.getClass().getSimpleName()+": "+String.valueOf(failure.getMessage());}
    public synchronized Optional<Retained> retainedFailure(){return retained;}
    @Override public synchronized void close()throws IOException {if(closed)return;closed=true;memory.close();}
}
