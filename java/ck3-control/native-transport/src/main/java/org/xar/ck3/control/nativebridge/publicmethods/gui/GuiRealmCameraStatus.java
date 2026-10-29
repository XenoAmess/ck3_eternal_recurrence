package org.xar.ck3.control.nativebridge.publicmethods.gui;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.OptionalLong;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiCameraCapabilities;
import org.xar.ck3.control.nativebridge.capabilities.gui.NativeCameraObserver;
import org.xar.ck3.control.nativebridge.capabilities.gui.NativeCameraObserver.DetailedCapture;
import org.xar.ck3.control.nativebridge.capabilities.gui.NativeCameraObserver.Result;
import org.xar.ck3.control.nativebridge.capabilities.gui.NativeCameraObserver.Status;

/** Original read-only Service camera status. Presentation DATA grants no gameplay/frame authority. */
public final class GuiRealmCameraStatus {
    private GuiRealmCameraStatus() { }
    public enum Availability { AVAILABLE, NOT_REQUESTED }
    public enum Mode { REALM, HOTSPOT, QUERY, CANCEL, TRACKED_HOTSPOT }
    public record Owner(int actor,String episodeRunId,long gamePid,BigInteger connectionGeneration) {
        public Owner {
            Objects.requireNonNull(episodeRunId);Objects.requireNonNull(connectionGeneration);
            NativeCharacterId.of(actor);
            require(!episodeRunId.isBlank() && episodeRunId.length()<=256
                    && gamePid>0 && gamePid<=0xffff_ffffL && connectionGeneration.signum()>0
                    && connectionGeneration.compareTo(BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE))<=0,
                    "complete actual camera owner required");
        }
    }
    /** Retain this identical object with the actual Root submission; first native target is latched once. */
    public static final class Submission {
        private final GuiCameraCapabilities.Binding original;
        private final Owner owner;
        private final Mode mode;
        private final OptionalInt maximumDateRaw;
        private List<Float> nativeTarget;
        public Submission(GuiCameraCapabilities.Binding original,Owner owner,Mode mode,OptionalInt maximumDateRaw) {
            this.original=Objects.requireNonNull(original);this.owner=Objects.requireNonNull(owner);
            this.mode=Objects.requireNonNull(mode);this.maximumDateRaw=Objects.requireNonNull(maximumDateRaw);
            require(original.actor()==owner.actor() && original.episodeRunId().equals(owner.episodeRunId()),
                    "camera submission owner differs from its actual original binding");
            require(mode==Mode.TRACKED_HOTSPOT ? maximumDateRaw.isPresent()
                    && maximumDateRaw.getAsInt()>=original.submittedDateRaw() : maximumDateRaw.isEmpty(),
                    "tracked camera requires its explicit original maximum date");
        }
        public GuiCameraCapabilities.Binding original(){return original;}
        public Owner owner(){return owner;}
        public Mode mode(){return mode;}
        public OptionalInt maximumDateRaw(){return maximumDateRaw;}
        private synchronized boolean retainsTarget(List<Float> actual) {
            if(nativeTarget==null)nativeTarget=List.copyOf(actual);
            return sameFloats(nativeTarget,actual);
        }
    }
    public sealed interface Diagnostics permits UnknownDiagnostics,ObservedDiagnostics { }
    public enum UnknownReason {
        MAPPING_LAYOUT_OR_IDENTITY_MISMATCH,LEGACY_OR_ABSENT_EXTENSION,DIAGNOSTIC_LAYOUT_OR_STATUS_MISMATCH,
        RESULT_BINDING_MISMATCH,REQUEST_CONTEXT_NOT_OBSERVED,REQUEST_CONTEXT_BINDING_MISMATCH,
        SUBMITTED_GEOMETRY_BINDING_MISMATCH,OBSERVATION_FLAGS_MISMATCH,FAILURE_REASON_OR_DIFFERENCE_MISMATCH;
        String wire(){return name().toLowerCase(java.util.Locale.ROOT);}
    }
    public record UnknownDiagnostics(UnknownReason reason) implements Diagnostics {
        public UnknownDiagnostics{Objects.requireNonNull(reason);}
    }
    public enum FailureReason {
        CURRENT_READ_FAILED(1),TARGET_READ_FAILED(2),CURRENT_NONFINITE(3),TARGET_CHANGED(4);
        final int code;FailureReason(int code){this.code=code;}
        String wire(){return name().toLowerCase(java.util.Locale.ROOT);}
        static Optional<FailureReason> from(int code){for(var r:values())if(r.code==code)return Optional.of(r);return Optional.empty();}
    }
    public record ObservedDiagnostics(FailureReason reason,Owner owner,long requestSequence,int submittedDateRaw,
            int requestDateRaw,int requestMode,int observationFlags,long targetDifferenceMask,long countyCount,
            long width,long height,int zoom,List<Integer> bounds,List<Float> expectedTarget,
            List<Integer> currentBits,List<Integer> targetBits,long observationUptimeBits) implements Diagnostics {
        public ObservedDiagnostics {
            Objects.requireNonNull(reason);Objects.requireNonNull(owner);bounds=List.copyOf(bounds);
            expectedTarget=List.copyOf(expectedTarget);currentBits=List.copyOf(currentBits);targetBits=List.copyOf(targetBits);
        }
    }
    public static final class Actual {
        private final DetailedCapture capture;
        private final Diagnostics diagnostics;
        private Actual(DetailedCapture capture,Diagnostics diagnostics){this.capture=capture;this.diagnostics=diagnostics;}
        public DetailedCapture capture(){return capture;}
        public Diagnostics diagnostics(){return diagnostics;}
    }
    public record StatusData(Availability status,OptionalLong requestedSequence,Optional<Actual> nativeActual) {
        public StatusData {
            Objects.requireNonNull(status);Objects.requireNonNull(requestedSequence);Objects.requireNonNull(nativeActual);
            require(requestedSequence.isEmpty() || requestedSequence.getAsLong()>=0
                    && requestedSequence.getAsLong()<=0xffff_fffeL && (requestedSequence.getAsLong()&1)==0,
                    "actual even camera request sequence required");
            require(nativeActual.isEmpty() || status==Availability.AVAILABLE && requestedSequence.isPresent()
                    && nativeActual.orElseThrow().capture.base().result().requestSequence()==requestedSequence.getAsLong(),
                    "native camera status differs from its original requested sequence");
        }
    }
    /** A single actual mapping sample only when an original submission exists for this current owner. */
    public static StatusData query(Optional<NativeCameraObserver> actualObserver,Owner currentOwner,
            Optional<Submission> originalSubmission)throws IOException {
        Objects.requireNonNull(actualObserver);Objects.requireNonNull(currentOwner);Objects.requireNonNull(originalSubmission);
        boolean installed=actualObserver.isPresent();
        Optional<DetailedCapture> actual=installed && originalSubmission.isPresent()
                && originalSubmission.orElseThrow().owner().equals(currentOwner)
                ? actualObserver.orElseThrow().observeDetailed() : Optional.empty();
        return project(installed,currentOwner,originalSubmission,actual);
    }
    /** Pure DATA consumer used after the actual bounded reader; never creates a mapping or a submission. */
    public static StatusData project(boolean observerInstalled,Owner currentOwner,Optional<Submission> originalSubmission,
            Optional<DetailedCapture> actual) {
        Objects.requireNonNull(currentOwner);Objects.requireNonNull(originalSubmission);Objects.requireNonNull(actual);
        OptionalLong sequence=originalSubmission.isPresent()
                ? OptionalLong.of(originalSubmission.orElseThrow().original().requestSequence()) : OptionalLong.empty();
        Availability availability=observerInstalled?Availability.AVAILABLE:Availability.NOT_REQUESTED;
        if(!observerInstalled || originalSubmission.isEmpty() || actual.isEmpty())return new StatusData(availability,sequence,Optional.empty());
        Submission submission=originalSubmission.orElseThrow();DetailedCapture capture=actual.orElseThrow();
        require(capture.base().result().equals(NativeCameraObserver.decodeResult(capture.base().originalResult())),
                "camera result differs from its actual original bytes");
        Result r=capture.base().result();
        if(!submission.owner().equals(currentOwner) || capture.base().gamePid()!=currentOwner.gamePid()
                || r.requestSequence()!=sequence.getAsLong())return new StatusData(availability,sequence,Optional.empty());
        boolean bound;
        if(submission.mode()==Mode.CANCEL && r.status()==Status.CANCELLED)bound=true;
        else if(submission.mode()==Mode.TRACKED_HOTSPOT) {
            // Tracking has a distinct original producer/receipt. A legacy mapping sample cannot stand in for it.
            bound=false;
        } else {
            bound=r.actor()==currentOwner.actor() && r.dateRaw()>=submission.original().submittedDateRaw()
                    && r.dateRaw()<=(long)submission.original().submittedDateRaw()+7*24;
            if(bound && (r.status()==Status.SUBMITTED || r.status()==Status.SETTLED)) {
                bound=r.target().size()==6 && submission.retainsTarget(r.target());
                if(r.status()==Status.SETTLED)bound &= sameFloats(r.current(),r.target()) && r.cameraPostconditionVerified();
            }
        }
        return new StatusData(availability,sequence,bound?Optional.of(new Actual(capture,decodeDiagnostics(capture,submission))):Optional.empty());
    }
    private static Diagnostics unknown(UnknownReason reason){return new UnknownDiagnostics(reason);}
    private static long u32(ByteBuffer bytes,int offset){return Integer.toUnsignedLong(bytes.getInt(offset));}
    private static List<Integer> bits(ByteBuffer bytes,int offset){return java.util.stream.IntStream.range(0,6).mapToObj(i->bytes.getInt(offset+i*4)).toList();}
    private static List<Float> floats(List<Integer> bits){return bits.stream().map(Float::intBitsToFloat).toList();}
    private static boolean finite(List<Float> values){return values.stream().allMatch(Float::isFinite);}
    private static boolean sameFloats(List<Float> left,List<Float> right){
        if(left.size()!=right.size())return false;
        for(int i=0;i<left.size();i++)if(left.get(i).floatValue()!=right.get(i).floatValue())return false;
        return true;
    }
    private static Diagnostics decodeDiagnostics(DetailedCapture capture,Submission submission) {
        byte[] raw=capture.originalDiagnostics();Result r=capture.base().result();Owner owner=submission.owner();
        if(raw.length!=168 || capture.base().gamePid()<=0 || NativeCameraObserver.RESULT_OFFSET+NativeCameraObserver.RESULT_BYTES!=65832
                || NativeCameraObserver.DIAGNOSTICS_OFFSET<65832)return unknown(UnknownReason.MAPPING_LAYOUT_OR_IDENTITY_MISMATCH);
        ByteBuffer b=ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);
        if(b.getInt(0)==0)return unknown(UnknownReason.LEGACY_OR_ABSENT_EXTENSION);
        Optional<FailureReason> reason=FailureReason.from(b.getInt(20));
        if(b.getInt(0)!=0x44434158 || b.getInt(4)!=1 || b.getInt(8)!=168 || b.getInt(156)!=0
                || b.getInt(16)!=7 || reason.isEmpty())return unknown(UnknownReason.DIAGNOSTIC_LAYOUT_OR_STATUS_MISMATCH);
        long request=u32(b,12),pid=u32(b,24);int actor=b.getInt(28),submitted=b.getInt(32),requested=b.getInt(36);
        try {NativeCharacterId.of(actor);}
        catch(IllegalArgumentException absentActor) {return unknown(UnknownReason.RESULT_BINDING_MISMATCH);}
        if(pid!=capture.base().gamePid() || r.status()!=Status.TARGET_CHANGED || request==0 || (request&1)!=0
                || request!=r.requestSequence() || actor!=r.actor() || submitted!=r.dateRaw())return unknown(UnknownReason.RESULT_BINDING_MISMATCH);
        if(request!=submission.original().requestSequence() || pid!=owner.gamePid() || actor!=owner.actor()
                || requested!=submission.original().submittedDateRaw() || submitted<requested
                || (long)submitted-requested>7*24)return unknown(UnknownReason.REQUEST_CONTEXT_BINDING_MISMATCH);
        int mode=b.getInt(40),flags=b.getInt(44),zoom=b.getInt(64);long mask=u32(b,48),count=u32(b,52),width=u32(b,56),height=u32(b,60);
        List<Integer> bounds=java.util.stream.IntStream.range(0,4).mapToObj(i->b.getInt(68+i*4)).toList();
        List<Float> expected=floats(bits(b,84));List<Integer> currentBits=bits(b,108),targetBits=bits(b,132);
        List<Float> current=floats(currentBits),target=floats(targetBits);
        if((mode!=1 && mode!=2) || mode!=(submission.mode()==Mode.REALM?1:submission.mode()==Mode.HOTSPOT?2:-1)
                || count>16384 || width<320 || height<240 || zoom<0 || count!=r.countyIds().size()
                || width!=r.clientWidth() || height!=r.clientHeight() || zoom!=r.zoomIndex()
                || !bounds.equals(List.of(r.bounds().minX(),r.bounds().minY(),r.bounds().maxX(),r.bounds().maxY()))
                || !sameFloats(expected,r.target()) || bounds.get(0)>bounds.get(2) || bounds.get(1)>bounds.get(3) || !finite(expected))
            return unknown(UnknownReason.SUBMITTED_GEOMETRY_BINDING_MISMATCH);
        boolean currentRead=(flags&1)!=0,targetRead=(flags&2)!=0;
        if((flags&~15)!=0 || targetRead&&!currentRead || ((flags&4)!=0)!=(currentRead&&finite(current))
                || ((flags&8)!=0)!=(targetRead&&finite(target)))return unknown(UnknownReason.OBSERVATION_FLAGS_MISMATCH);
        int actualReason;long differences=0;
        if(!currentRead)actualReason=1;else if(!targetRead)actualReason=2;else if(!finite(current))actualReason=3;
        else {for(int i=0;i<6;i++)if(target.get(i).floatValue()!=expected.get(i).floatValue())differences|=1L<<i;actualReason=differences==0?0:4;}
        if(actualReason!=reason.orElseThrow().code || differences!=mask)return unknown(UnknownReason.FAILURE_REASON_OR_DIFFERENCE_MISMATCH);
        return new ObservedDiagnostics(reason.orElseThrow(),owner,request,submitted,requested,mode,flags,mask,count,width,height,zoom,
                bounds,expected,currentBits,targetBits,b.getLong(160));
    }
    public static RawJson encode(StatusData data) {
        Objects.requireNonNull(data);ObjectNode out=obj().put("status",data.status()==Availability.AVAILABLE?"available":"not_requested");
        if(data.requestedSequence().isPresent())out.put("requested_sequence",data.requestedSequence().getAsLong());else out.putNull("requested_sequence");
        if(data.nativeActual().isPresent())out.set("native_actual",actual(data.nativeActual().orElseThrow()));else out.putNull("native_actual");
        out.put("same_frame_with_gameplay_claim",false);return PublicDataJson.encode(out);
    }
    private static ObjectNode actual(Actual actual) {
        Result r=actual.capture.base().result();ObjectNode out=obj().put("schema","xar.ck3.camera-presentation-actual/v1")
                .put("status",status(r.status())).put("request_sequence",r.requestSequence()).put("actor_character_id",r.actor())
                .put("date_raw",r.dateRaw()).put("county_count",r.countyIds().size()).put("zoom_index",r.zoomIndex())
                .put("native_elapsed_us",r.elapsedMicros()).put("camera_postcondition_verified",r.cameraPostconditionVerified())
                .put("coverage_verified",r.coverageVerified()).put("fit_model","native_bucket_with_viewport_padding")
                .put("same_frame_with_gameplay_claim",false);
        ints(out.putArray("county_title_ids"),r.countyIds());ints(out.putArray("bounds"),List.of(r.bounds().minX(),r.bounds().minY(),r.bounds().maxX(),r.bounds().maxY()));
        out.putArray("client_size").add(r.clientWidth()).add(r.clientHeight());values(out.putArray("target"),r.target());values(out.putArray("current"),r.current());
        out.set("settle_diagnostics",diagnostics(actual.diagnostics));return out;
    }
    private static ObjectNode diagnostics(Diagnostics diagnostics) {
        ObjectNode out=obj().put("schema","xar.ck3.camera-settle-diagnostics/v1");
        if(diagnostics instanceof UnknownDiagnostics missing)return out.put("available",false).put("reason",missing.reason().wire());
        ObservedDiagnostics d=(ObservedDiagnostics)diagnostics;boolean cr=(d.observationFlags()&1)!=0,tr=(d.observationFlags()&2)!=0;
        out.put("available",true).put("reason",d.reason().wire()).put("legacy_status","target_changed").put("request_sequence",d.requestSequence());
        ObjectNode provider=obj().put("channel","native-camera-presentation-v1").put("pid",d.owner().gamePid()).put("mapping_version",1);
        provider.putNull("native_epoch").putNull("game_creation_filetime");out.set("provider",provider);
        ObjectNode frame=obj().put("actor_character_id",d.owner().actor()).put("date_raw",d.requestDateRaw()).put("bridge_pid",d.owner().gamePid())
                .put("connection_generation",d.owner().connectionGeneration().toString()).put("episode_run_id",d.owner().episodeRunId());out.set("request_source_frame",frame);
        out.put("submit_snapshot_date_raw",d.submittedDateRaw()).put("observation_uptime_ms",Long.toUnsignedString(d.observationUptimeBits()));
        out.putNull("observation_game_frame");out.put("current_read_success",cr).put("target_read_success",tr);
        if(cr)out.put("current_finite",(d.observationFlags()&4)!=0);else out.putNull("current_finite");
        if(tr)out.put("target_finite",(d.observationFlags()&8)!=0);else out.putNull("target_finite");
        observed(out,"observed_current",d.currentBits(),cr);observed(out,"observed_target",d.targetBits(),tr);
        out.put("target_difference_mask",d.targetDifferenceMask());ObjectNode geometry=obj().put("county_count",d.countyCount()).put("zoom_index",d.zoom()).put("request_mode",d.requestMode());
        geometry.putArray("client_size").add(d.width()).add(d.height());ints(geometry.putArray("bounds"),d.bounds());values(geometry.putArray("expected_target"),d.expectedTarget());out.set("submitted_geometry",geometry);
        return out.put("same_frame_with_gameplay_claim",false).put("camera_postcondition_verified",false).put("coverage_verified",false);
    }
    private static void observed(ObjectNode out,String key,List<Integer> bits,boolean known) {
        if(!known){out.putNull(key).putNull(key+"_float_bits");return;}
        values(out.putArray(key),floats(bits));ArrayNode raw=out.putArray(key+"_float_bits");bits.forEach(value->raw.add(Integer.toUnsignedLong(value)));
    }
    private static void values(ArrayNode out,List<Float> values){values.forEach(value->{if(Float.isFinite(value))out.add(value.doubleValue());else out.addNull();});}
    private static void ints(ArrayNode out,List<Integer> values){values.forEach(value->out.add(value.intValue()));}
    private static ObjectNode obj(){return JsonNodeFactory.instance.objectNode();}
    private static void require(boolean ok,String message){if(!ok)throw new IllegalArgumentException(message);}
    private static String status(Status status) {
        return switch(status) {
            case TARGET_WRITE_BLOCKED -> "camera_target_write_blocked_or_unreadable";
            case TRANSIENT_X_UNAVAILABLE -> "camera_transient_x_active_or_unreadable";
            case TRANSIENT_Z_UNAVAILABLE -> "camera_transient_z_active_or_unreadable";
            case VIEWPORT_UNAVAILABLE -> "camera_viewport_extent_unavailable";
            case BUCKET_TABLE_UNAVAILABLE -> "camera_bucket_table_unavailable";
            case BUCKET_READ_UNAVAILABLE -> "camera_bucket_read_or_match_unavailable";
            case ZOOM_INDEX_UNAVAILABLE -> "camera_zoom_index_unavailable";
            case ZOOM_STATE_UNAVAILABLE -> "camera_zoom_or_target_state_unavailable";
            case ANGLE_UNAVAILABLE -> "camera_angle_state_unavailable";
            case CANONICAL_TARGET_UNAVAILABLE -> "camera_canonical_target_unavailable";
            case TARGET_READBACK_UNAVAILABLE -> "camera_target_write_or_readback_unavailable";
            default -> status.name().toLowerCase(java.util.Locale.ROOT);
        };
    }
}
