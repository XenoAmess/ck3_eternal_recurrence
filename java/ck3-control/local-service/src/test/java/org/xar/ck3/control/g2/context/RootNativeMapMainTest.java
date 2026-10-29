package org.xar.ck3.control.g2.context;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.CampaignMapComposeRequest;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.build.RootNativePlanJson;
import java.util.List;

final class RootNativeMapMainTest {
    @TempDir Path directory;

    @Test void rootReviewUsesTheSharedRequestCodecAndPreservesFullUnsignedBirth() {
        var challenge=new ControlBuild.FileRef(directory.resolve("challenge.json").toString(),1,"0".repeat(64));
        var request=new CampaignMapComposeRequest("software-map-review-test",
                new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("18446744073709551615"))),
                "software-recording",new SavedFrame("native:7",8,7,12345,168372,"software-episode"),"2026-10-23T08:00:00Z");
        var actual=new RootNativeMapMain.MapReview("xar.root-native-map-visibility-review/v1",challenge,request);
        byte[] original=actual.toCanonicalBytes();
        assertEquals(actual,RootNativeMapMain.MapReview.fromBytes(original));
        assertTrue(new String(original,java.nio.charset.StandardCharsets.UTF_8).contains("18446744073709551615"));
        assertFalse(new String(original,java.nio.charset.StandardCharsets.UTF_8).contains("1.844674"));
    }

    @Test void rootReviewCannotCoerceVisibilityOrAcceptAnAliasOutsideTheSharedWire() {
        var challenge=new ControlBuild.FileRef(directory.resolve("challenge.json").toString(),1,"0".repeat(64));
        var request=new CampaignMapComposeRequest("software-map-review-test",
                new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),"software-recording",
                new SavedFrame("native:7",8,7,12345,168372,"software-episode"),"2026-10-23T08:00:00Z");
        var value=StrictJson.parse(new RootNativeMapMain.MapReview("xar.root-native-map-visibility-review/v1",challenge,request).toCanonicalBytes());
        var wrong=value.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode)wrong.get("request")).put("game_map_visible",1);
        assertThrows(IllegalArgumentException.class,()->RootNativeMapMain.MapReview.fromBytes(StrictJson.canonical(wrong)));
        var alias=value.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode)alias).put("expectedEpisode","software-episode");
        assertThrows(IllegalArgumentException.class,()->RootNativeMapMain.MapReview.fromBytes(StrictJson.canonical(alias)));
    }
    @Test void nullableEpisodeWireUsesExplicitNullAndRejectsMissingOrBooleanWithoutOptionalCoercion() throws Exception {
        var input=new RootNativeMapMain.SourcePlanInput("software-source-plan",null,
                new ExactRef(directory.resolve("launcher.json").toString(),1,"0".repeat(64)),
                List.of(),directory.resolve("evidence"),1,1);
        var mapper=RootNativePlanJson.mapper();
        byte[] bytes=mapper.writeValueAsBytes(input);
        assertEquals(input,mapper.readValue(bytes,RootNativeMapMain.SourcePlanInput.class));
        assertTrue(input.toSourcePlan().expectedEpisode().isEmpty());
        var json=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(bytes);
        assertTrue(json.get("expectedEpisode").isNull());
        var missing=json.deepCopy(); missing.remove("expectedEpisode");
        assertThrows(java.io.IOException.class,()->mapper.readValue(StrictJson.canonical(missing),RootNativeMapMain.SourcePlanInput.class));
        var wrong=json.deepCopy(); wrong.put("expectedEpisode",true);
        assertThrows(java.io.IOException.class,()->mapper.readValue(StrictJson.canonical(wrong),RootNativeMapMain.SourcePlanInput.class));
    }
}
