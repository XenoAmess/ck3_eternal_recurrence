package org.xar.ck3.control.nativebridge.capabilities.frontend_coa;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.Base64;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaFramebufferExtension;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec;

/** Required original Python producer differential. No desktop methods are invoked or monkeypatched. */
class CoaFramebufferOriginalProducerTest {
    private static final String SHA="abc75bfc0e2aeee9dfc7dcfcb29e0f7b9932f4b53f969069d8187fc6ebca31d0";
    private static final String ORACLE="""
        import base64, hashlib, importlib.util, io, json, pathlib, sys
        from PIL import Image
        import numpy as np
        source=pathlib.Path(sys.argv[1]).resolve()
        assert hashlib.sha256(source.read_bytes()).hexdigest()==sys.argv[2]
        spec=importlib.util.spec_from_file_location('xar_original_coa_framebuffer',source)
        m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
        assert pathlib.Path(m.derive_two_state_calibration_v2.__code__.co_filename).resolve()==source
        data=json.loads(sys.stdin.buffer.read())
        def image(name): return Image.open(io.BytesIO(base64.b64decode(data[name]))).convert('RGB')
        def digest(png,mode): return hashlib.sha256(np.asarray(Image.open(io.BytesIO(base64.b64decode(png))).convert(mode),dtype=np.uint8).tobytes()).hexdigest()
        surface=m.derive_two_state_calibration_v2('oracle',1234,image('begin'),image('solid'))
        uv=m.derive_anchor_calibration_v3(surface,image('solid'),image('markers'))
        capture=m.capture_calibrated_framebuffer_v3(image('texture'),uv,side=64)
        c2=m.compare_reference_to_calibrated_framebuffer_v2(image('reference'),image('texture'),surface)
        c3=m.compare_reference_to_calibrated_framebuffer_v3(image('reference'),image('texture'),uv)
        c1=m.compare_reference_to_framebuffer_v1(image('small_reference'),image('small_frame'),search_sides=(32,))
        failures=[]
        for op in (lambda:m.derive_two_state_calibration_v2('../bad',1234,image('begin'),image('solid')),
                   lambda:m.derive_two_state_calibration_v2('x',1234,image('begin'),image('begin')),
                   lambda:m.derive_anchor_calibration_v3(surface,image('solid'),image('solid'))):
            try:op();failures.append(False)
            except (ValueError,m.CoatOfArmsFramebufferError):failures.append(True)
        output={'surface':m._calibration_receipt_v2(surface),'uv':m._calibration_receipt_v3(uv),
                'capture_rgb':digest(capture['alignedContentPngBase64'],'RGB'),
                'capture_rgba':digest(capture['alignedContentPngBase64'],'RGBA'),
                'mask':hashlib.sha256(surface.mask.tobytes()).hexdigest(),
                'c2':c2,'c3':c3,'c1':c1,'failures':failures}
        assert hashlib.sha256(source.read_bytes()).hexdigest()==sys.argv[2]
        print(json.dumps(output,allow_nan=False,separators=(',',':')))
        """;
    @Test void originalSurfaceUvCaptureComparisonsAndWireConsumersAgreeOnRealProducerImages()throws Exception {
        Path repository=Path.of(required("xar.repository.root")).toAbsolutePath().normalize();
        Path source=repository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/coat_of_arms_framebuffer.py");
        assertEquals(SHA,CoaData.sha256(Files.readAllBytes(source)),"exact original producer source required");
        var begin=CoaFramebufferFlowTest.blank();var solid=CoaFramebufferFlowTest.solid();var markers=CoaFramebufferFlowTest.markers();
        var texture=CoaFramebufferFlowTest.solid();for(int y=30;y<110;y++)for(int x=40;x<140;x++)texture.setRGB(x,y,((x*3&255)<<16)|((y*5&255)<<8)|(x+y&255));
        var reference=new BufferedImage(64,64,BufferedImage.TYPE_INT_RGB);for(int y=0;y<64;y++)for(int x=0;x<64;x++)reference.setRGB(x,y,((x*4&255)<<16)|((y*4&255)<<8)|(x+y));
        var small=new BufferedImage(32,32,BufferedImage.TYPE_INT_RGB);for(int y=0;y<32;y++)for(int x=0;x<32;x++)small.setRGB(x,y,((x*7&255)<<16)|((y*6&255)<<8)|(x*3+y*2));
        var smallFrame=new BufferedImage(100,90,BufferedImage.TYPE_INT_RGB);for(int y=0;y<32;y++)for(int x=0;x<32;x++)smallFrame.setRGB(x+40,y+20,small.getRGB(x,y));
        var request=FrontendCoaCodec.empty();put(request,"begin",begin);put(request,"solid",solid);put(request,"markers",markers);put(request,"texture",texture);put(request,"reference",reference);put(request,"small_reference",small);put(request,"small_frame",smallFrame);
        JsonNode original=oracle(source,FullJsonTree.encode(request,RawJson.MAXIMUM_BYTES));
        var surface=CoaFramebuffer.deriveSurface("oracle",1234,new CoaFramebuffer.Image(begin),new CoaFramebuffer.Image(solid));
        var uv=CoaFramebuffer.deriveUv(surface,new CoaFramebuffer.Image(solid),new CoaFramebuffer.Image(markers));
        var javaSurface=CoaFramebufferExtension.surface(surface);var javaUv=CoaFramebufferExtension.uv(uv);
        for(String field:List.of("calibrationId","bridgePid","framebufferSize","rect","differenceThreshold","candidateComponentCount","changedPixels","selectedPixels","beginPixelSha256","completePixelSha256"))
            compareDomain(original.path("surface").get(field),javaSurface.get(field));
        assertEquals(original.get("mask").textValue(),CoaData.sha256(surface.mask().values));
        compareNumbers(original.path("uv").get("observedAnchorCenters"),javaUv.get("observedAnchorCenters"),0);
        compareNumbers(original.path("uv").get("canonicalToFramebufferAffine"),javaUv.get("canonicalToFramebufferAffine"),1e-4);
        var captured=CoaFramebuffer.capture(new CoaFramebuffer.Image(texture),uv,64);
        assertEquals(original.get("capture_rgba").textValue(),pixelDigest(captured.alignedContent(),true));
        assertEquals(original.get("capture_rgb").textValue(),pixelDigest(captured.alignedContent(),false));
        var c2=CoaFramebuffer.compareV2(new CoaFramebuffer.Image(reference),new CoaFramebuffer.Image(texture),surface);
        var c3=CoaFramebuffer.compareV3(new CoaFramebuffer.Image(reference),new CoaFramebuffer.Image(texture),uv);
        var c1=CoaFramebuffer.compareV1(new CoaFramebuffer.Image(small),new CoaFramebuffer.Image(smallFrame),List.of(32),CoaFramebuffer.SearchBudget.until(Clock.systemUTC(),Instant.now().plusSeconds(20)));
        compareMetrics(original.path("c2").get("metrics"),c2.metrics());compareMetrics(original.path("c3").get("metrics"),c3.metrics());compareMetrics(original.path("c1").get("metrics"),c1.metrics());
        var rect=c1.bestMatch().rect();assertEquals(List.of(rect.left(),rect.top(),rect.right(),rect.bottom()).toString(),integers(original.path("c1").path("bestMatch").path("rect")).toString());
        assertEquals(3,original.get("failures").size());for(var rejected:original.get("failures"))assertTrue(rejected.booleanValue());
        assertEquals(SHA,CoaData.sha256(Files.readAllBytes(source)));
    }
    private static void compareMetrics(JsonNode original,CoaFramebuffer.Metrics actual){
        assertEquals(original.path("maskPixels").intValue(),actual.maskPixels());var encoded=CoaFramebufferExtension.metrics(actual);
        for(String field:List.of("meanAbsoluteError","colorMse","edgeLoss","spatialMeanAbsoluteError8x8"))compareNumbers(original.get(field),encoded.get(field),5e-7);
        assertArrayEquals(FullJsonTree.encode(encoded,RawJson.MAXIMUM_BYTES),FullJsonTree.encode(FrontendCoaCodec.object(FrontendCoaCodec.encode(FrontendCoaCodec.response(encoded))),RawJson.MAXIMUM_BYTES));
    }
    private static void compareDomain(JsonNode expected,JsonNode actual){
        if(expected.isArray()){assertTrue(actual.isArray());assertEquals(expected.size(),actual.size());for(int i=0;i<expected.size();i++)compareDomain(expected.get(i),actual.get(i));}
        else if(expected.isIntegralNumber()){assertTrue(actual.isIntegralNumber());assertEquals(expected.bigIntegerValue(),actual.bigIntegerValue());}
        else assertEquals(expected,actual);
    }
    private static void compareNumbers(JsonNode expected,JsonNode actual,double tolerance){
        if(expected.isArray()){assertTrue(actual.isArray());assertEquals(expected.size(),actual.size());for(int i=0;i<expected.size();i++)compareNumbers(expected.get(i),actual.get(i),tolerance);}
        else if(expected.isNull())assertTrue(actual.isNull());else {assertTrue(expected.isNumber()&&actual.isNumber());assertEquals(expected.doubleValue(),actual.doubleValue(),tolerance);}
    }
    private static List<Integer> integers(JsonNode raw){var values=new java.util.ArrayList<Integer>();raw.forEach(value->values.add(value.intValue()));return List.copyOf(values);}
    private static void put(com.fasterxml.jackson.databind.node.ObjectNode row,String field,BufferedImage value){row.put(field,CoaFramebuffer.pngRgb(new CoaFramebuffer.Image(value)).base64());}
    private static String pixelDigest(CoaFramebuffer.Png png,boolean alpha)throws Exception {
        var image=ImageIO.read(new ByteArrayInputStream(Base64.getDecoder().decode(png.base64())));var bytes=new java.io.ByteArrayOutputStream();
        for(int y=0;y<image.getHeight();y++)for(int x=0;x<image.getWidth();x++){int pixel=image.getRGB(x,y);bytes.write(pixel>>>16&255);bytes.write(pixel>>>8&255);bytes.write(pixel&255);if(alpha)bytes.write(pixel>>>24&255);}return CoaData.sha256(bytes.toByteArray());
    }
    private static JsonNode oracle(Path source,byte[] input)throws Exception {
        String python=required("xar.python");var process=new ProcessBuilder(python,"-B","-c",ORACLE,source.toString(),SHA).redirectErrorStream(true).start();
        try {
            process.getOutputStream().write(input);process.getOutputStream().close();
            if(!process.waitFor(60,TimeUnit.SECONDS)){process.destroyForcibly();throw new AssertionError("original framebuffer oracle timed out");}
            byte[] output=process.getInputStream().readNBytes(1024*1024+1);assertTrue(output.length<=1024*1024,"bounded oracle output required");
            assertEquals(0,process.exitValue(),()->new String(output,StandardCharsets.UTF_8));return FullJsonTree.parse(output,1024*1024);
        }finally{if(process.isAlive())process.destroyForcibly();}
    }
    private static String required(String key){String value=System.getProperty(key);assertNotNull(value,"required canonical CI property "+key);assertFalse(value.isBlank());return value;}
}
