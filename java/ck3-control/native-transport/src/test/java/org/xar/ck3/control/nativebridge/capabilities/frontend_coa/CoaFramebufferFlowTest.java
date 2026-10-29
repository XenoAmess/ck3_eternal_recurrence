package org.xar.ck3.control.nativebridge.capabilities.frontend_coa;

import static org.junit.jupiter.api.Assertions.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.Base64;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaFramebufferExtension;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaService;

/** Software image-domain producer -> phase store -> shared public codec. No desktop/current-Game qualification. */
class CoaFramebufferFlowTest {
    static final Instant AT=Instant.parse("2026-10-24T00:00:00Z");
    static final long PID=1234;
    static CoaWindowCapture.Captured captured(CoaFramebuffer.Image image){
        return new CoaWindowCapture.Captured(PID,new CoaWindowCapture.WindowIdentity("9007199254740993",new CoaWindowCapture.ScreenRect(-2560,0,0,1440)),AT,image);
    }
    static BufferedImage blank(){return new BufferedImage(180,140,BufferedImage.TYPE_INT_RGB);}
    static BufferedImage solid(){var result=blank();for(int y=30;y<110;y++)for(int x=40;x<140;x++)result.setRGB(x,y,0x00dddddd);return result;}
    static BufferedImage markers(){var result=solid();for(int row=0;row<3;row++)for(int col=0;col<3;col++){
        int cx=70+col*20,cy=54+row*16;for(int y=cy-2;y<=cy+2;y++)for(int x=cx-2;x<=cx+2;x++)result.setRGB(x,y,0x00112233);
    }return result;}
    static CoaFramebuffer.Image image(BufferedImage value){return new CoaFramebuffer.Image(value);}
    @Test void validationAndConsumedPhaseFailureDoNotReadAnotherScreenshot()throws Exception {
        var store=new CoaCalibrations();var reads=new AtomicInteger();CoaCalibrations.CaptureSource source=()->{reads.incrementAndGet();return captured(image(blank()));};
        assertThrows(IllegalArgumentException.class,()->store.calibrateV2("../bad",CoaCalibrations.PhaseV2.BEGIN,PID,source));
        assertThrows(IllegalArgumentException.class,()->store.calibrateV2("x",CoaCalibrations.PhaseV2.COMPLETE,PID,source));
        assertEquals(0,reads.get());
        store.calibrateV2("x",CoaCalibrations.PhaseV2.BEGIN,PID,source);assertEquals(1,reads.get());
        assertThrows(IOException.class,()->store.calibrateV2("x",CoaCalibrations.PhaseV2.COMPLETE,PID,()->{throw new IOException("actual capture unavailable");}));
        assertThrows(IllegalArgumentException.class,()->store.calibrateV2("x",CoaCalibrations.PhaseV2.COMPLETE,PID,source));
        assertEquals(1,reads.get(),"consumed failed completion never retries the pixel source");
        assertThrows(IllegalArgumentException.class,()->store.compareV2("missing",PID,source,"bad","0".repeat(64)));assertEquals(1,reads.get());
        assertThrows(IllegalArgumentException.class,()->store.compareV1(PID,source,"bad","0".repeat(64)));assertEquals(1,reads.get());
    }
    @Test void fourCalibrationLimitAndAnchorCompletionPopAreOriginalPhaseSemantics()throws Exception {
        var store=new CoaCalibrations();CoaCalibrations.CaptureSource blank=()->captured(image(blank()));
        for(int i=0;i<4;i++)store.calibrateV3("x"+i,CoaCalibrations.PhaseV3.BEGIN,PID,blank);
        var calls=new AtomicInteger();assertThrows(IllegalArgumentException.class,()->store.calibrateV3("fifth",CoaCalibrations.PhaseV3.BEGIN,PID,()->{calls.incrementAndGet();return blank.capture();}));assertEquals(0,calls.get());
        store.calibrateV3("x0",CoaCalibrations.PhaseV3.SURFACE_COMPLETE,PID,()->captured(image(solid())));
        store.calibrateV3("x0",CoaCalibrations.PhaseV3.ANCHOR_BASE,PID,()->captured(image(solid())));
        assertThrows(IllegalArgumentException.class,()->store.calibrateV3("x0",CoaCalibrations.PhaseV3.ANCHORS_COMPLETE,PID,()->captured(image(solid()))));
        assertThrows(IllegalArgumentException.class,()->store.calibrateV3("x0",CoaCalibrations.PhaseV3.ANCHORS_COMPLETE,PID,()->{calls.incrementAndGet();return blank.capture();}));assertEquals(0,calls.get());
        store.calibrateV3("fifth",CoaCalibrations.PhaseV3.BEGIN,PID,blank);
    }
    @Test void realImageStagesFlowThroughTheOnlySharedRequestResponseCodec()throws Exception {
        var pixels=new ArrayDeque<CoaFramebuffer.Image>(List.of(image(blank()),image(solid()),image(solid()),image(markers()),image(solid()),image(blank()),image(solid())));
        var extension=new CoaFramebufferExtension(PID,new CoaCalibrations(),()->captured(pixels.removeFirst()),CoaFramebufferExtension.Backend.SOFTWARE_IMAGE_DOMAIN);
        var service=new FrontendCoaService(List.of(new FrontendCoaService.ComponentBinding(CoaFramebufferExtension.METHODS,extension)));
        for(String phase:List.of("begin","surface_complete","anchor_base","anchors_complete")){
            var args=FrontendCoaCodec.empty().put("calibration_id","uv").put("phase",phase);
            var response=service.execute(FrontendCoaCodec.decode(FrontendCoaContract.Method.CALIBRATE3,FrontendCoaCodec.raw(args)));
            var parsed=FrontendCoaCodec.object(FrontendCoaCodec.encode(response));
            assertEquals(phase,parsed.get("phase").textValue());assertEquals(PID,parsed.get("bridgePid").longValue());assertFalse(parsed.get("usesOcr").booleanValue());
        }
        var capture=service.execute(FrontendCoaCodec.decode(FrontendCoaContract.Method.CAPTURE,FrontendCoaCodec.raw(FrontendCoaCodec.empty().put("calibration_id","uv").put("side",64))));
        var publicCapture=FrontendCoaCodec.object(FrontendCoaCodec.encode(capture));
        assertEquals("software-image-domain-no-desktop-qualification",publicCapture.get("captureBackend").textValue());
        assertEquals("RGB8",publicCapture.path("framebuffer").path("pixelFormat").textValue());
        assertTrue(publicCapture.get("readOnly").booleanValue());assertFalse(publicCapture.has("routeStable"),"pure DATA cannot mint Root route evidence");
        var encodedCrop=publicCapture.path("capture").path("cropPngBase64").textValue();
        assertFalse(ImageIO.read(new ByteArrayInputStream(Base64.getDecoder().decode(encodedCrop))).getColorModel().hasAlpha());
        var aligned=ImageIO.read(new ByteArrayInputStream(Base64.getDecoder().decode(publicCapture.path("capture").path("alignedContentPngBase64").textValue())));
        assertTrue(aligned.getColorModel().hasAlpha());assertEquals(64,aligned.getWidth());
        for(String phase:List.of("begin","complete"))service.execute(FrontendCoaCodec.decode(FrontendCoaContract.Method.CALIBRATE2,FrontendCoaCodec.raw(FrontendCoaCodec.empty().put("calibration_id","surface").put("phase",phase))));
        assertTrue(pixels.isEmpty());
        assertThrows(IOException.class,()->service.execute(new FrontendCoaContract.Empty(FrontendCoaContract.Method.PREPARE)),"a decoded request is never a central presentation permit");
        assertThrows(IllegalArgumentException.class,()->FrontendCoaCodec.decode(FrontendCoaContract.Method.CAPTURE,FrontendCoaCodec.raw(FrontendCoaCodec.empty().put("calibration_id","uv").put("side",true))));
        assertThrows(IllegalArgumentException.class,()->FrontendCoaCodec.decode(FrontendCoaContract.Method.CALIBRATE3,FrontendCoaCodec.raw(FrontendCoaCodec.empty().put("calibration_id","uv").putNull("phase"))));
    }
    @Test void exhaustiveSearchHonorsActualDeadlineAndPublishesNoPartialWinner()throws Exception {
        var ref=image(new BufferedImage(32,32,BufferedImage.TYPE_INT_RGB));var frame=image(new BufferedImage(96,80,BufferedImage.TYPE_INT_RGB));
        var checks=new AtomicInteger();assertThrows(IOException.class,()->CoaFramebuffer.compareV1(ref,frame,List.of(32),()->{if(checks.incrementAndGet()>3)throw new IOException("deadline");}));
        assertTrue(checks.get()>3);
        assertThrows(IOException.class,()->CoaFramebuffer.compareV1(ref,frame,List.of(32),CoaFramebuffer.SearchBudget.until(Clock.fixed(AT,ZoneOffset.UTC),AT)));
    }
    @Test void referenceBoundaryRejectsWrongIdentityTypesAndNonPngBeforeAnyPixelsAreRead() {
        var png=CoaFramebuffer.pngRgb(image(new BufferedImage(32,32,BufferedImage.TYPE_INT_RGB)));
        assertEquals(new CoaFramebuffer.Size(32,32),CoaFramebuffer.reference(png.base64(),png.sha256()).size());
        assertThrows(IllegalArgumentException.class,()->CoaFramebuffer.reference(png.base64(),png.sha256().toLowerCase(java.util.Locale.ROOT)));
        assertThrows(IllegalArgumentException.class,()->CoaFramebuffer.reference(png.base64(),"0".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->CoaFramebuffer.reference("!!",png.sha256()));
        var nonsquare=new BufferedImage(32,33,BufferedImage.TYPE_INT_RGB);var bad=CoaFramebuffer.pngRgb(image(nonsquare));assertThrows(IllegalArgumentException.class,()->CoaFramebuffer.reference(bad.base64(),bad.sha256()));
    }
}
