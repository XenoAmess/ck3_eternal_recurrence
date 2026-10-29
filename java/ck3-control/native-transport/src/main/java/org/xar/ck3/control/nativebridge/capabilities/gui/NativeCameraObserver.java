package org.xar.ck3.control.nativebridge.capabilities.gui;

import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.BaseTSD.SIZE_T;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.win32.StdCallLibrary;
import com.sun.jna.win32.W32APIOptions;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.nativebridge.NativePipeEndpoint;
import org.xar.ck3.control.nativebridge.NativeProcessGuard;

/** Original presentation mapping, opened FILE_MAP_READ only. This class cannot submit an action. */
public final class NativeCameraObserver implements AutoCloseable {
    interface Api extends StdCallLibrary {
        HANDLE OpenFileMappingW(int desiredAccess,boolean inherit,String name);
        Pointer MapViewOfFile(HANDLE mapping,int access,int offsetHigh,int offsetLow,SIZE_T bytes);
        boolean UnmapViewOfFile(Pointer view);boolean CloseHandle(HANDLE handle);
    }
    public static final int MAPPING_BYTES=131072,RESULT_OFFSET=192,RESULT_BYTES=65640;
    public static final int DIAGNOSTICS_OFFSET=0x18000,DIAGNOSTICS_BYTES=168;
    private static final int FILE_MAP_READ=4,MAGIC=0x43524158;
    private final NativePipeEndpoint.Config config;private final NativeProcessGuard guard;private final Api api;
    private HANDLE handle;private Pointer view;private boolean closed;
    public NativeCameraObserver(NativePipeEndpoint.Config config,NativeProcessGuard guard)throws IOException{
        this.config=java.util.Objects.requireNonNull(config);this.guard=java.util.Objects.requireNonNull(guard);
        if(!System.getProperty("os.name","").startsWith("Windows")||Native.POINTER_SIZE!=8||!System.getProperty("os.arch","").matches("(?i)(amd64|x86_64)"))throw new IOException("original camera mapping is reviewed Windows AMD64 only");
        if(!config.expectedGameSha256().equalsIgnoreCase(GuiModels.Build.CROZIER4.sha256()))throw new IOException("camera mapping requires exact reviewed .4 executable");
        api=Native.load("kernel32",Api.class,W32APIOptions.UNICODE_OPTIONS);
    }
    public enum Status {
        IDLE(0),SUBMITTED(1),SETTLED(2),CANCELLED(3),STALE_ACTOR(4),PREEMPTED(5),UNAVAILABLE(6),TARGET_CHANGED(7),BOUNDS_AVAILABLE(8),
        WINDOW_UNAVAILABLE(16),CAMERA_RESOLVE_UNAVAILABLE(17),TARGET_WRITE_BLOCKED(18),TRANSIENT_X_UNAVAILABLE(19),TRANSIENT_Z_UNAVAILABLE(20),
        VIEWPORT_UNAVAILABLE(21),BUCKET_TABLE_UNAVAILABLE(22),BUCKET_READ_UNAVAILABLE(23),ZOOM_INDEX_UNAVAILABLE(24),ZOOM_STATE_UNAVAILABLE(25),
        ANGLE_UNAVAILABLE(26),CANONICAL_TARGET_UNAVAILABLE(27),TARGET_READBACK_UNAVAILABLE(28);
        private final int code;Status(int c){code=c;}public static Status parse(int code){for(Status s:values())if(s.code==code)return s;throw new IllegalArgumentException("unknown actual camera status");}
    }
    public record Bounds(int minX,int minY,int maxX,int maxY) { }
    public record Result(long requestSequence,Status status,int actor,int dateRaw,List<Integer> countyIds,Bounds bounds,
            long clientWidth,long clientHeight,int zoomIndex,List<Float> target,List<Float> current,long elapsedMicros,boolean coverageVerified) {
        public Result{countyIds=List.copyOf(countyIds);target=List.copyOf(target);current=List.copyOf(current);}
        public boolean cameraPostconditionVerified(){return status==Status.SETTLED&&zoomIndex>=0&&sameFloats(target,current);}
        public boolean sameFrameGameplayClaim(){return false;}
    }
    public record Capture(String machineId,long gamePid,String sessionId,long resultSequence,Instant observedAt,Result result,byte[] originalResult) {
        public Capture{originalResult=originalResult.clone();}@Override public byte[] originalResult(){return originalResult.clone();}
    }
    private static boolean sameFloats(List<Float> left,List<Float> right){
        if(left.size()!=right.size())return false;
        for(int i=0;i<left.size();i++)if(left.get(i).floatValue()!=right.get(i).floatValue())return false;
        return true;
    }
    /** The base result and optional extension were copied under the identical seqlock. */
    public record DetailedCapture(Capture base,byte[] originalDiagnostics) {
        public DetailedCapture {
            java.util.Objects.requireNonNull(base);
            GuiJson.need(originalDiagnostics!=null&&originalDiagnostics.length==DIAGNOSTICS_BYTES,"complete actual diagnostic region required");
            originalDiagnostics=originalDiagnostics.clone();
        }
        @Override public byte[] originalDiagnostics(){return originalDiagnostics.clone();}
    }
    /** Existing consumers retain the exact base projection from the same producer. */
    public synchronized Optional<Capture> observe()throws IOException{
        return observeDetailed().map(DetailedCapture::base);
    }
    /** One bounded seqlock sample. A concurrent writer returns empty; no polling thread or stale-tail promotion. */
    public synchronized Optional<DetailedCapture> observeDetailed()throws IOException{
        if(closed)throw new IOException("camera observer closed");guard.verify(config.game());open();identity();
        long before=Integer.toUnsignedLong(view.getInt(20));if((before&1)!=0)return Optional.empty();
        byte[] original=view.getByteArray(RESULT_OFFSET,RESULT_BYTES);
        byte[] diagnostics=view.getByteArray(DIAGNOSTICS_OFFSET,DIAGNOSTICS_BYTES);long after=Integer.toUnsignedLong(view.getInt(20));identity();guard.verify(config.game());
        if(before!=after||(after&1)!=0)return Optional.empty();
        return Optional.of(new DetailedCapture(new Capture(config.machineId(),config.game().pid(),config.sessionId(),after,Instant.now(),decodeResult(original),original),diagnostics));
    }
    private void open()throws IOException{
        if(view!=null)return;handle=api.OpenFileMappingW(FILE_MAP_READ,false,"Local\\XarCK3CameraPresentationV1-"+config.game().pid());
        if(handle==null||Pointer.nativeValue(handle.getPointer())==0)throw new IOException("original native camera presentation mapping not deployed");
        view=api.MapViewOfFile(handle,FILE_MAP_READ,0,0,new SIZE_T(MAPPING_BYTES));if(view==null){api.CloseHandle(handle);handle=null;throw new IOException("native camera readonly mapping unavailable");}
    }
    private void identity()throws IOException{if(view.getInt(0)!=MAGIC||view.getInt(4)!=1||Integer.toUnsignedLong(view.getInt(8))!=config.game().pid())throw new IOException("original camera mapping identity drift");}
    public static Result decodeResult(byte[] original){
        GuiJson.need(original!=null&&original.length==RESULT_BYTES,"complete original native camera result required");ByteBuffer b=ByteBuffer.wrap(original).order(ByteOrder.LITTLE_ENDIAN);
        long request=Integer.toUnsignedLong(b.getInt());Status status=Status.parse(b.getInt());int actor=b.getInt(),date=b.getInt();long n=Integer.toUnsignedLong(b.getInt());
        GuiJson.need(n<=16384,"native camera county capacity exceeded");long width=Integer.toUnsignedLong(b.getInt()),height=Integer.toUnsignedLong(b.getInt());int zoom=b.getInt();
        Bounds bounds=new Bounds(b.getInt(),b.getInt(),b.getInt(),b.getInt());List<Float> target=new ArrayList<>(),current=new ArrayList<>();
        for(int i=0;i<6;i++){float f=b.getFloat();GuiJson.need(Float.isFinite(f),"nonfinite actual camera target");target.add(f);}for(int i=0;i<6;i++){float f=b.getFloat();GuiJson.need(Float.isFinite(f),"nonfinite actual camera current");current.add(f);}
        long elapsed=Integer.toUnsignedLong(b.getInt()),coverage=Integer.toUnsignedLong(b.getInt());GuiJson.need(coverage<=1,"native coverage boolean outside original domain");List<Integer> counties=new ArrayList<>();for(int i=0;i<n;i++)counties.add(b.getInt());
        return new Result(request,status,actor,date,counties,bounds,width,height,zoom,target,current,elapsed,coverage==1);
    }

    public record TrackingActual(long requestSequence,long state,String ownerEpoch,String scopeGeneration,int actor,int army,int dateRaw,
            int province,int combat,long updates,String readerMicros) {
        public boolean active(){return state==1;}
        public com.fasterxml.jackson.databind.node.ObjectNode toJson(){return org.xar.ck3.control.contracts.StrictJson.object()
            .put("schema","xar.ck3.camera-tracking-actual/v1").put("request_sequence",requestSequence).put("state",state).put("owner_epoch",ownerEpoch)
            .put("scope_generation",scopeGeneration).put("actor_character_id",actor).put("fullarmy_id",army).put("date_raw",dateRaw)
            .put("province_id",province).put("combat_id",combat).put("target_updates",updates).put("reader_elapsed_us",readerMicros)
            .put("tracking_active",active()).put("camera_postcondition_verified",false).put("continuous_frame_coverage_verified",false).put("same_frame_with_gameplay_claim",false);}
    }
    public static Optional<TrackingActual> trackingActual(org.xar.ck3.control.contracts.presentation.PresentationRequest request,
            org.xar.ck3.control.contracts.presentation.PresentationCapture.NativeSample sample){
        if(request.tracking().isEmpty()||sample.trackingHeader().isEmpty()||sample.trackingResult().isEmpty())return Optional.empty();
        var h=ByteBuffer.wrap(sample.trackingHeader().orElseThrow()).order(ByteOrder.LITTLE_ENDIAN);
        var r=ByteBuffer.wrap(sample.trackingResult().orElseThrow()).order(ByteOrder.LITTLE_ENDIAN);var binding=request.tracking().orElseThrow();
        long seq=Integer.toUnsignedLong(h.getInt(32)),ack=Integer.toUnsignedLong(r.getInt(0)),state=Integer.toUnsignedLong(r.getInt(4));
        String epoch=Long.toUnsignedString(r.getLong(8)),generation=Long.toUnsignedString(r.getLong(16));
        if(h.getInt(0)!=0x54434158||h.getInt(4)!=1||h.getInt(8)!=4384||Integer.toUnsignedLong(h.getInt(12))!=request.owner().processId()
            ||seq==0||(seq&1)!=0||ack!=request.requestSequence()||state>12||!epoch.equals(binding.ownerEpoch())||!generation.equals(binding.scopeGeneration())
            ||r.getInt(32)!=request.frame().actor()||r.getInt(36)!=binding.fullArmyId())return Optional.empty();
        return Optional.of(new TrackingActual(ack,state,epoch,generation,r.getInt(32),r.getInt(36),r.getInt(40),r.getInt(44),r.getInt(48),
            Integer.toUnsignedLong(r.getInt(52)),Long.toUnsignedString(r.getLong(64))));
    }
    @Override public synchronized void close()throws IOException{
        if(closed)return;closed=true;boolean ok=true;if(view!=null){ok=api.UnmapViewOfFile(view);view=null;}if(handle!=null){ok=api.CloseHandle(handle)&&ok;handle=null;}if(!ok)throw new IOException("camera readonly mapping cleanup failed");
    }
}
