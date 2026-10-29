package org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaCalibrations;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaFramebuffer;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureOutcome;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec.*;

/** Pure image and original wire extension. Root supplies the actual source-bound capture port.
 * Neither its constructor, phase state nor decoded image DATA grants desktop/current-Game permission. */
public final class CoaFramebufferExtension implements FrontendCoaService.NativeAccess {
    public static final Set<Method> METHODS=Set.of(Method.PREPARE,Method.CAPTURE,Method.CALIBRATE2,Method.CALIBRATE3,
            Method.COMPARE1,Method.COMPARE2,Method.COMPARE3);
    public enum Backend {
        WINDOWS_AWT_AUTHENTICATED_CLIENT("windows-awt-authenticated-client-framebuffer"),
        SOFTWARE_IMAGE_DOMAIN("software-image-domain-no-desktop-qualification");
        private final String wire;Backend(String wire){this.wire=wire;}public String wire(){return wire;}
    }
    private final long pid;private final CoaCalibrations calibrations;
    private final CoaCalibrations.CaptureSource captures;private final Backend backend;
    public CoaFramebufferExtension(long pid,CoaCalibrations calibrations,CoaCalibrations.CaptureSource captures,Backend backend) {
        need(pid>0&&pid<=0xffff_ffffL,"actual positive DWORD bridge PID required");this.pid=pid;
        this.calibrations=Objects.requireNonNull(calibrations);this.captures=Objects.requireNonNull(captures);this.backend=Objects.requireNonNull(backend);
    }
    @Override public synchronized Response execute(Request request)throws IOException {
        return execute(request,CoaFramebuffer.SearchBudget.until(java.time.Clock.systemUTC(),java.time.Instant.now().plusSeconds(30)));
    }
    /** Root passes the same actual request/review deadline used for native route reads. */
    public synchronized Response execute(Request request,CoaFramebuffer.SearchBudget budget)throws IOException {
        Objects.requireNonNull(budget).check();
        Objects.requireNonNull(request);need(METHODS.contains(request.method()),"not one of the seven framebuffer methods");
        if(request.method()==Method.PREPARE)throw new IOException("framebuffer foreground preparation requires the actual central WIN32_FRONTEND_CAPTURE action, not a read callback");
        if(request instanceof Calibration c) {
            var result=c.method()==Method.CALIBRATE2
                    ?calibrations.calibrateV2(c.calibrationId(),CoaCalibrations.PhaseV2.valueOf(c.phase().toUpperCase(java.util.Locale.ROOT)),pid,captures)
                    :calibrations.calibrateV3(c.calibrationId(),CoaCalibrations.PhaseV3.valueOf(c.phase().toUpperCase(java.util.Locale.ROOT)),pid,captures);
            return response(calibration(result));
        }
        if(request instanceof Capture c)return response(capture(calibrations.capture(c.calibrationId(),c.side(),pid,captures)));
        if(request instanceof Compare c) {
            var result=switch(c.method()) {
                case COMPARE1->calibrations.compareV1(pid,captures,c.referencePngBase64(),c.referencePngSha256(),budget);
                case COMPARE2->calibrations.compareV2(c.calibrationId(),pid,captures,c.referencePngBase64(),c.referencePngSha256());
                case COMPARE3->calibrations.compareV3(c.calibrationId(),pid,captures,c.referencePngBase64(),c.referencePngSha256());
                default->throw new IllegalArgumentException("not a comparison request");
            };return response(comparison(result));
        }
        throw new IllegalArgumentException("framebuffer request type and operation differ");
    }
    public ObjectNode comparison(CoaCalibrations.ComparisonReceipt result) {
        var row=envelope("ck3-coat-of-arms-framebuffer-comparison-v"+result.version(),result.version(),result.bridgePid(),result.capturedAt().toString(),result.framebufferSize(),result.framebufferPixelSha256());
        row.set("reference",empty().put("width",result.referenceSize().width()).put("height",result.referenceSize().height()).put("pngSha256",result.referencePngSha256()));
        if(result.version()==2)row.set("calibration",surface(result.surface().orElseThrow()));
        if(result.version()==3)row.set("calibration",uv(result.uv().orElseThrow()));
        var comparison=comparison(result.version(),result.comparison());
        if(result.version()==2)comparison.put("calibrationId",result.surface().orElseThrow().calibrationId());
        if(result.version()==3)comparison.put("calibrationId",result.uv().orElseThrow().surface().calibrationId());
        row.set("comparison",comparison);return readOnly(row);
    }
    public ObjectNode capture(CoaCalibrations.CaptureReceipt result) {
        var row=envelope("ck3-coat-of-arms-framebuffer-capture-v1",1,result.bridgePid(),result.capturedAt().toString(),result.framebufferSize(),result.framebufferPixelSha256());
        row.set("calibration",uv(result.calibration()));var captured=result.capture();
        var body=flags(empty().put("locatorContract","two-solid-state-surface-nine-marker-affine-uv-v3").put("calibrationId",result.calibration().surface().calibrationId())
                .put("searchedWholeFramebuffer",false).put("referenceImageAccepted",false).put("referenceUsedForLocalization",false).put("referenceUsedForRegistration",false)
                .put("captureSide",captured.captureSide()).put("surfaceMaskPixels",captured.surfaceMaskPixels()).put("fixedScreenCoordinatesUsed",false));
        body.set("rect",rect(captured.rect()));png(body,"crop",captured.crop());png(body,"alignedContent",captured.alignedContent());row.set("capture",body);return readOnly(row);
    }
    /** Wire DATA only. Root must separately verify its canonical permit/receipt and independent native after-read. */
    public static ObjectNode preparation(FrontendWindowCaptureOutcome result){
        Objects.requireNonNull(result);need(result.status()==FrontendWindowCaptureOutcome.Status.VERIFIED,"unresolved physical original cannot encode a successful preparation");
        var row=flags(empty().put("schema","ck3-coat-of-arms-framebuffer-preparation-v1").put("schemaVersion",1)
                .put("bridgePid",result.request().owner().processId()).put("hwnd",result.windowBefore().hwnd())
                .put("foregroundRootBefore",result.foregroundBefore()).put("foregroundRootAfter",result.foregroundAfter().orElseThrow())
                .put("presentationOnly",true).put("mode",result.mode().orElseThrow().name().toLowerCase(java.util.Locale.ROOT))
                .put("attachedForegroundThread",result.attachedForegroundThread()).put("attachedTargetThread",result.attachedTargetThread()));
        var rect=result.windowBefore().clientRect();row.putArray("clientRect").add(rect.left()).add(rect.top()).add(rect.right()).add(rect.bottom());
        if(result.detachSucceeded().isPresent())row.put("detachSucceeded",result.detachSucceeded().orElseThrow());else row.putNull("detachSucceeded");
        if(result.directActivationError().isPresent())row.put("directActivationError",result.directActivationError().orElseThrow());else row.putNull("directActivationError");
        if(result.attachedActivationError().isPresent())row.put("attachedActivationError",result.attachedActivationError().orElseThrow());else row.putNull("attachedActivationError");
        return row;
    }
    public static ObjectNode calibration(CoaCalibrations.CalibrationReceipt result) {
        if(result instanceof CoaCalibrations.Stage stage) {
            var row=flags(empty().put("schema","ck3-coat-of-arms-framebuffer-calibration-stage-v"+stage.version()).put("schemaVersion",stage.version())
                    .put("calibrationId",stage.calibrationId()).put("phase",stage.phase()).put("bridgePid",stage.bridgePid()).put("pixelSha256",stage.pixelSha256()).put("readOnlyCapture",true));
            row.set("framebufferSize",size(stage.framebufferSize()));if(stage.version()==2)row.put("readyForComplete",true);else row.put("nextPhase",stage.nextPhase());return row;
        }
        if(result instanceof CoaCalibrations.SurfaceReady ready) {
            var row=surface(ready.surface());row.put("phase",ready.phase());
            if(ready.version()==3)row.put("schema","ck3-coat-of-arms-framebuffer-calibration-stage-v3").put("schemaVersion",3).put("nextPhase",ready.nextPhase()).put("readyForAnchorBase",true);
            else row.put("readyForComparison",true);return row;
        }
        var ready=(CoaCalibrations.UvReady)result;return uv(ready.calibration()).put("phase","anchors_complete").put("readyForComparison",true);
    }
    public static ObjectNode surface(CoaFramebuffer.Surface surface) {
        var row=flags(empty().put("schema","ck3-coat-of-arms-framebuffer-calibration-v2").put("schemaVersion",2).put("calibrationId",surface.calibrationId()).put("bridgePid",surface.bridgePid())
                .put("differenceThreshold",48).put("candidateComponentCount",surface.componentCount()).put("changedPixels",surface.changedPixels()).put("selectedPixels",surface.selectedPixels())
                .put("beginPixelSha256",surface.beginPixelSha256()).put("completePixelSha256",surface.completePixelSha256()).put("referenceIndependent",true).put("fixedScreenCoordinatesUsed",false));
        row.set("framebufferSize",size(surface.framebufferSize()));row.set("rect",rect(surface.rect()));png(row,"mask",surface.mask().png());return row;
    }
    public static ObjectNode uv(CoaFramebuffer.UvCalibration uv) {
        var row=flags(empty().put("schema","ck3-coat-of-arms-framebuffer-calibration-v3").put("schemaVersion",3).put("calibrationId",uv.surface().calibrationId()).put("bridgePid",uv.surface().bridgePid())
                .put("maximumAllowedReprojectionError",2.5).put("anchorDifferenceThreshold",48).put("anchorBasePixelSha256",uv.anchorBasePixelSha256()).put("anchorsCompletePixelSha256",uv.anchorsCompletePixelSha256())
                .put("referenceIndependent",true).put("uvRegistered",true).put("fixedScreenCoordinatesUsed",false));
        row.set("framebufferSize",size(uv.surface().framebufferSize()));row.set("rect",rect(uv.surface().rect()));row.set("surface",surface(uv.surface()));
        var canonical=row.putArray("anchorPositions");uv.anchorPositions().forEach(point->canonical.add(point(point)));
        var observed=row.putArray("observedAnchorCenters");uv.observedAnchorCenters().forEach(point->observed.add(point(point)));
        var map=row.putArray("canonicalToFramebufferAffine");var affine=uv.affine();
        map.add(array(affine.xx(),affine.xy(),affine.x0()));map.add(array(affine.yx(),affine.yy(),affine.y0()));
        var errors=row.putArray("reprojectionErrors");double max=0;for(double value:uv.reprojectionErrors()){finite(value);errors.add(value);max=Math.max(max,value);}row.put("maximumReprojectionError",max);return row;
    }
    private static ObjectNode comparison(int version,CoaFramebuffer.Comparison value) {
        var row=empty().put("locatorContract",value.locatorContract()).put("searchedWholeFramebuffer",value.searchedWholeFramebuffer()).put("fixedScreenCoordinatesUsed",false);
        // Calibration ID is added by the receipt's exact private store, never inferred from a reference.
        if(version!=1){row.put("referenceUsedForLocalization",false);if(version==3)row.put("referenceUsedForRegistration",false);}
        var best=empty();best.set("rect",rect(value.bestMatch().rect()));png(best,"crop",value.bestMatch().crop());png(best,"alignedContent",value.bestMatch().alignedContent());
        if(version==1) {
            var sides=row.putArray("searchSides");CoaFramebuffer.SEARCH_SIDES.forEach(sides::add);
            var candidates=row.putArray("scaleCandidates");value.scaleCandidates().forEach(candidate->candidates.add(scale(candidate)));
            var winner=value.scaleCandidates().stream().filter(candidate->candidate.side()==value.bestMatch().rect().width()&&candidate.x()==value.bestMatch().rect().left()&&candidate.y()==value.bestMatch().rect().top()).findFirst().orElseThrow();
            best.setAll(scale(winner));var alignment=value.alignment().orElseThrow();var aligned=empty().put("contract","outer-frame-local-square-alignment-v1").put("candidateCount",alignment.candidateCount())
                    .put("contentToOuterRatio",alignment.contentToOuterRatio()).put("alignmentLoss",alignment.alignmentLoss());
            aligned.set("outerRect",rect(alignment.outerRect()));aligned.set("contentRect",rect(alignment.contentRect()));best.set("alignment",aligned);
        }
        row.set("bestMatch",best);row.set("comparisonMask",empty().put("contract",version==1?"shield-polygon-alpha-eroded-v1":version==2?"two-solid-state-dynamic-surface-eroded-v2":"native-surface-affine-uv-eroded-v3")
                .put("erosionRadiusPixels",value.erosionRadiusPixels()).put("maskPixels",value.metrics().maskPixels()));row.set("metrics",metrics(value.metrics()));return row;
    }
    public static ObjectNode metrics(CoaFramebuffer.Metrics value) {
        var row=empty().put("contract",value.contract()).put("maskPixels",value.maskPixels()).put("meanAbsoluteError",value.meanAbsoluteError()).put("colorMse",value.colorMse()).put("edgeLoss",value.edgeLoss());
        finite(value.meanAbsoluteError());finite(value.colorMse());finite(value.edgeLoss());var grid=row.putArray("spatialMeanAbsoluteError8x8");
        for(var source:value.spatialMeanAbsoluteError8x8()){var cells=grid.addArray();for(var cell:source)if(cell.isPresent()){finite(cell.orElseThrow());cells.add(cell.orElseThrow());}else cells.addNull();}return row;
    }
    private ObjectNode envelope(String schema,int version,long bridgePid,String at,CoaFramebuffer.Size size,String sha) {
        var row=empty().put("schema",schema).put("schemaVersion",version).put("capturedAt",at).put("captureBackend",backend.wire()).put("bridgePid",bridgePid);
        row.set("framebuffer",empty().put("width",size.width()).put("height",size.height()).put("pixelFormat","RGB8").put("pixelSha256",sha));return row;
    }
    private static ObjectNode readOnly(ObjectNode row){return flags(row.put("readOnly",true));}
    private static ObjectNode flags(ObjectNode row){return row.put("usesOcr",false).put("usesKeyboard",false).put("usesMouse",false);}
    private static void png(ObjectNode row,String prefix,CoaFramebuffer.Png value){row.put(prefix+"PngSha256",value.sha256()).put(prefix+"PngBase64",value.base64());}
    private static ArrayNode size(CoaFramebuffer.Size value){var row=empty().putArray("value");row.add(value.width()).add(value.height());return row;}
    private static ArrayNode rect(CoaFramebuffer.Rect value){var row=empty().putArray("value");row.add(value.left()).add(value.top()).add(value.right()).add(value.bottom());return row;}
    private static ArrayNode point(CoaFramebuffer.Point value){return array(value.x(),value.y());}
    private static ArrayNode array(double...values){var row=empty().putArray("value");for(double value:values){finite(value);row.add(value);}return row;}
    private static ObjectNode scale(CoaFramebuffer.ScaleCandidate value){finite(value.locatorLoss());finite(value.secondDistinctLoss());finite(value.distinctMargin());return empty().put("side",value.side()).put("x",value.x()).put("y",value.y())
            .put("locatorLoss",value.locatorLoss()).put("secondDistinctX",value.secondDistinctX()).put("secondDistinctY",value.secondDistinctY()).put("secondDistinctLoss",value.secondDistinctLoss()).put("distinctMargin",value.distinctMargin());}
    private static void finite(double value){need(Double.isFinite(value),"finite original image-domain score required");}
}
