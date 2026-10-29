package org.xar.ck3.control.nativebridge.capabilities.frontend_coa;

import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData.require;
import java.time.Instant;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Four-calibration stores preserve the producer's consume-on-stage-transition semantics and exact PID checks. */
public final class CoaCalibrations {
    public enum PhaseV2 { BEGIN, COMPLETE }
    public enum PhaseV3 { BEGIN, SURFACE_COMPLETE, ANCHOR_BASE, ANCHORS_COMPLETE }
    public sealed interface CalibrationReceipt permits Stage, SurfaceReady, UvReady { String calibrationId(); long bridgePid(); }
    public record Stage(String calibrationId, long bridgePid, int version, String phase, String nextPhase,
            CoaFramebuffer.Size framebufferSize, String pixelSha256) implements CalibrationReceipt {
        public Stage { CoaFramebuffer.identifier(calibrationId); require(version == 2 || version == 3, "stage version outside contract"); Objects.requireNonNull(framebufferSize); }
    }
    public record SurfaceReady(String calibrationId, long bridgePid, int version, String phase, String nextPhase,
            CoaFramebuffer.Surface surface, boolean readyForComparison, boolean readyForAnchorBase) implements CalibrationReceipt {
        public SurfaceReady { Objects.requireNonNull(surface); require(surface.calibrationId().equals(calibrationId) && surface.bridgePid() == bridgePid, "surface receipt identity drift"); }
    }
    public record UvReady(String calibrationId, long bridgePid, CoaFramebuffer.UvCalibration calibration) implements CalibrationReceipt {
        public UvReady { Objects.requireNonNull(calibration); require(calibration.surface().calibrationId().equals(calibrationId) && calibration.surface().bridgePid() == bridgePid, "UV receipt identity drift"); }
    }
    public record ComparisonReceipt(int version, long bridgePid, Instant capturedAt, CoaFramebuffer.Size framebufferSize,
            String framebufferPixelSha256, CoaFramebuffer.Size referenceSize, String referencePngSha256,
            Optional<CoaFramebuffer.Surface> surface, Optional<CoaFramebuffer.UvCalibration> uv,
            CoaFramebuffer.Comparison comparison) {
        public ComparisonReceipt { require(version >= 1 && version <= 3, "comparison version invalid"); Objects.requireNonNull(capturedAt); surface = Objects.requireNonNull(surface); uv = Objects.requireNonNull(uv); Objects.requireNonNull(comparison); }
        public boolean readOnly() { return true; } public boolean usesOcr() { return false; } public boolean usesKeyboard() { return false; } public boolean usesMouse() { return false; }
    }
    public record CaptureReceipt(long bridgePid, Instant capturedAt, CoaFramebuffer.Size framebufferSize,
            String framebufferPixelSha256, CoaFramebuffer.UvCalibration calibration, CoaFramebuffer.SurfaceCapture capture) {
        public CaptureReceipt { Objects.requireNonNull(capturedAt); Objects.requireNonNull(framebufferSize); Objects.requireNonNull(calibration); Objects.requireNonNull(capture); }
        public boolean readOnly() { return true; } public boolean usesOcr() { return false; } public boolean usesKeyboard() { return false; } public boolean usesMouse() { return false; }
    }
    private record Pending(String id, long pid, CoaFramebuffer.Image image) { }
    private final List<Pending> beginsV2 = new ArrayList<>(), beginsV3 = new ArrayList<>(), anchorBases = new ArrayList<>();
    private final List<CoaFramebuffer.Surface> surfacesV2 = new ArrayList<>(), surfacesV3 = new ArrayList<>();
    private final List<CoaFramebuffer.UvCalibration> completedV3 = new ArrayList<>();
    /** Deferred pixels preserve original validation/pop-before-capture ordering; this callback grants no OS permission. */
    @FunctionalInterface public interface CaptureSource { CoaWindowCapture.Captured capture() throws IOException; }
    public synchronized CalibrationReceipt calibrateV2(String calibrationId, PhaseV2 phase, CoaWindowCapture.Captured captured) {
        try{return calibrateV2(calibrationId,phase,captured.bridgePid(),()->captured);}catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    public synchronized CalibrationReceipt calibrateV2(String calibrationId,PhaseV2 phase,long pid,CaptureSource source)throws IOException {
        String id=CoaFramebuffer.identifier(calibrationId);Objects.requireNonNull(phase);Objects.requireNonNull(source);
        if (phase == PhaseV2.BEGIN) {
            require(beginsV2.stream().noneMatch(item -> item.id.equals(id)) && surfacesV2.stream().noneMatch(item -> item.calibrationId().equals(id)), "calibration ID already in use");
            require(beginsV2.size() + surfacesV2.size() < 4, "calibration store full");CoaFramebuffer.Image frame=checked(source,pid).image(); beginsV2.add(new Pending(id, pid, frame)); return new Stage(id, pid, 2, "begin", "complete", frame.size(), frame.pixelSha256());
        }
        Pending begin = take(beginsV2, id, "calibration begin missing"); require(begin.pid == pid, "native PID changed during calibration");
        CoaFramebuffer.Image frame=checked(source,pid).image();
        CoaFramebuffer.Surface surface = CoaFramebuffer.deriveSurface(id, pid, begin.image, frame); surfacesV2.add(surface); return new SurfaceReady(id, pid, 2, "complete", "", surface, true, false);
    }
    public synchronized CalibrationReceipt calibrateV3(String calibrationId, PhaseV3 phase, CoaWindowCapture.Captured captured) {
        try{return calibrateV3(calibrationId,phase,captured.bridgePid(),()->captured);}catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    public synchronized CalibrationReceipt calibrateV3(String calibrationId,PhaseV3 phase,long pid,CaptureSource source)throws IOException {
        String id=CoaFramebuffer.identifier(calibrationId);Objects.requireNonNull(phase);Objects.requireNonNull(source);
        switch (phase) {
            case BEGIN -> {
                require(!activeV3().contains(id), "calibration ID already in use"); require(activeV3().size() < 4, "calibration store full");
                CoaFramebuffer.Image frame=checked(source,pid).image();
                beginsV3.add(new Pending(id, pid, frame)); return new Stage(id, pid, 3, "begin", "surface_complete", frame.size(), frame.pixelSha256());
            }
            case SURFACE_COMPLETE -> {
                Pending begin = take(beginsV3, id, "surface calibration begin missing"); require(begin.pid == pid, "native PID changed during calibration");
                CoaFramebuffer.Image frame=checked(source,pid).image();
                CoaFramebuffer.Surface surface = CoaFramebuffer.deriveSurface(id, pid, begin.image, frame); surfacesV3.add(surface); return new SurfaceReady(id, pid, 3, "surface_complete", "anchor_base", surface, false, true);
            }
            case ANCHOR_BASE -> {
                CoaFramebuffer.Surface surface = surface(surfacesV3, id); require(surface.bridgePid() == pid, "native PID changed during calibration"); require(anchorBases.stream().noneMatch(item -> item.id.equals(id)), "anchor base already captured");
                CoaFramebuffer.Image frame=checked(source,pid).image();
                anchorBases.add(new Pending(id, pid, frame)); return new Stage(id, pid, 3, "anchor_base", "anchors_complete", frame.size(), frame.pixelSha256());
            }
            case ANCHORS_COMPLETE -> {
                Optional<CoaFramebuffer.Surface> found = surfacesV3.stream().filter(item -> item.calibrationId().equals(id)).findFirst(); found.ifPresent(surfacesV3::remove);
                Optional<Pending> base = anchorBases.stream().filter(item -> item.id.equals(id)).findFirst(); base.ifPresent(anchorBases::remove);
                require(found.isPresent() && base.isPresent(), "anchor calibration state incomplete"); CoaFramebuffer.Surface surface = found.orElseThrow(); Pending before = base.orElseThrow();
                require(surface.bridgePid() == pid && before.pid == pid, "native PID changed during calibration");
                CoaFramebuffer.Image frame=checked(source,pid).image();
                CoaFramebuffer.UvCalibration calibration = CoaFramebuffer.deriveUv(surface, before.image, frame); completedV3.add(calibration); return new UvReady(id, pid, calibration);
            }
        }
        throw new IllegalArgumentException("calibration phase invalid");
    }
    public ComparisonReceipt compareV1(CoaWindowCapture.Captured captured, String referenceBase64, String referenceSha256) {
        try{return compareV1(captured.bridgePid(),()->captured,referenceBase64,referenceSha256);}catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    public ComparisonReceipt compareV1(long pid,CaptureSource source,String referenceBase64,String referenceSha256)throws IOException {
        return compareV1(pid,source,referenceBase64,referenceSha256,()->{});
    }
    public ComparisonReceipt compareV1(long pid,CaptureSource source,String referenceBase64,String referenceSha256,CoaFramebuffer.SearchBudget budget)throws IOException {
        budget.check();CoaFramebuffer.Image reference=CoaFramebuffer.reference(referenceBase64,referenceSha256);var captured=checked(source,pid);
        return comparison(1,captured,reference,referenceSha256,Optional.empty(),Optional.empty(),CoaFramebuffer.compareV1(reference,captured.image(),CoaFramebuffer.SEARCH_SIDES,budget));
    }
    public synchronized ComparisonReceipt compareV2(String calibrationId, CoaWindowCapture.Captured captured, String referenceBase64, String referenceSha256) {
        try{return compareV2(calibrationId,captured.bridgePid(),()->captured,referenceBase64,referenceSha256);}catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    public synchronized ComparisonReceipt compareV2(String calibrationId,long pid,CaptureSource source,String referenceBase64,String referenceSha256)throws IOException {
        CoaFramebuffer.Surface surface=surface(surfacesV2,CoaFramebuffer.identifier(calibrationId));require(surface.bridgePid()==pid,"native PID differs from calibration");
        CoaFramebuffer.Image reference=CoaFramebuffer.reference(referenceBase64,referenceSha256);var captured=checked(source,pid);
        return comparison(2, captured, reference, referenceSha256, Optional.of(surface), Optional.empty(), CoaFramebuffer.compareV2(reference, captured.image(), surface));
    }
    public synchronized ComparisonReceipt compareV3(String calibrationId, CoaWindowCapture.Captured captured, String referenceBase64, String referenceSha256) {
        try{return compareV3(calibrationId,captured.bridgePid(),()->captured,referenceBase64,referenceSha256);}catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    public synchronized ComparisonReceipt compareV3(String calibrationId,long pid,CaptureSource source,String referenceBase64,String referenceSha256)throws IOException {
        CoaFramebuffer.UvCalibration uv=uv(calibrationId,pid);CoaFramebuffer.Image reference=CoaFramebuffer.reference(referenceBase64,referenceSha256);var captured=checked(source,pid);
        return comparison(3, captured, reference, referenceSha256, Optional.of(uv.surface()), Optional.of(uv), CoaFramebuffer.compareV3(reference, captured.image(), uv));
    }
    public synchronized CaptureReceipt capture(String calibrationId, int side, CoaWindowCapture.Captured captured) {
        try{return capture(calibrationId,side,captured.bridgePid(),()->captured);}catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    public synchronized CaptureReceipt capture(String calibrationId,int side,long pid,CaptureSource source)throws IOException {
        CoaFramebuffer.UvCalibration uv=uv(calibrationId,pid);var captured=checked(source,pid);return new CaptureReceipt(captured.bridgePid(),captured.observedAt(),captured.image().size(),captured.image().pixelSha256(),uv,CoaFramebuffer.capture(captured.image(),uv,side));
    }
    private static CoaWindowCapture.Captured checked(CaptureSource source,long pid)throws IOException {
        require(pid>0&&pid<=0xffff_ffffL,"positive DWORD actual bridge PID required");var captured=Objects.requireNonNull(source.capture());require(captured.bridgePid()==pid,"captured native PID changed");return captured;
    }
    private List<String> activeV3() { List<String> ids = new ArrayList<>(); beginsV3.forEach(item -> ids.add(item.id)); surfacesV3.forEach(item -> ids.add(item.calibrationId())); anchorBases.forEach(item -> ids.add(item.id)); completedV3.forEach(item -> ids.add(item.surface().calibrationId())); return ids.stream().distinct().toList(); }
    private CoaFramebuffer.UvCalibration uv(String calibrationId, long pid) { String id = CoaFramebuffer.identifier(calibrationId); CoaFramebuffer.UvCalibration uv = completedV3.stream().filter(item -> item.surface().calibrationId().equals(id)).findFirst().orElseThrow(() -> new IllegalArgumentException("completed calibration missing")); require(uv.surface().bridgePid() == pid, "native PID differs from calibration"); return uv; }
    private static CoaFramebuffer.Surface surface(List<CoaFramebuffer.Surface> store, String id) { return store.stream().filter(item -> item.calibrationId().equals(id)).findFirst().orElseThrow(() -> new IllegalArgumentException("surface calibration missing")); }
    private static Pending take(List<Pending> store, String id, String reason) { Pending item = store.stream().filter(row -> row.id.equals(id)).findFirst().orElseThrow(() -> new IllegalArgumentException(reason)); store.remove(item); return item; }
    private static ComparisonReceipt comparison(int version, CoaWindowCapture.Captured captured, CoaFramebuffer.Image reference, String digest, Optional<CoaFramebuffer.Surface> surface, Optional<CoaFramebuffer.UvCalibration> uv, CoaFramebuffer.Comparison comparison) {
        return new ComparisonReceipt(version, captured.bridgePid(), captured.observedAt(), captured.image().size(), captured.image().pixelSha256(), reference.size(), digest, surface, uv, comparison);
    }
}
