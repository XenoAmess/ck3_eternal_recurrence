package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.Optional;
import java.util.OptionalInt;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiCameraCapabilities;
import org.xar.ck3.control.nativebridge.capabilities.gui.NativeCameraObserver;
import org.xar.ck3.control.nativebridge.publicmethods.gui.GuiRealmCameraStatus;
import org.xar.ck3.control.nativebridge.publicmethods.gui.GuiRealmCameraStatus.*;

/** Original binary DATA -> shared signed identity -> actual status filter -> sole wire producer. No mapping/Game grant. */
final class GuiRealmCameraStatusSignedActorTest {
    private static final Instant TIME=Instant.parse("2026-10-24T06:00:00Z");
    private static Owner owner(int actor){return new Owner(actor,"signed-camera",314,BigInteger.ONE);}
    private static Submission submission(Owner owner){return new Submission(
            new GuiCameraCapabilities.Binding(2,owner.actor(),1000,owner.episodeRunId()),owner,Mode.REALM,OptionalInt.empty());}
    private static byte[] result(int actor){
        ByteBuffer b=ByteBuffer.allocate(NativeCameraObserver.RESULT_BYTES).order(ByteOrder.LITTLE_ENDIAN);
        b.putInt(2).putInt(7).putInt(actor).putInt(1024).putInt(0).putInt(1280).putInt(720).putInt(3);
        for(int i=0;i<4;i++)b.putInt(0);
        for(int twice=0;twice<2;twice++)for(int i=1;i<=6;i++)b.putFloat(i);
        b.putInt(456).putInt(0);return b.array();
    }
    private static byte[] tail(int actor){
        ByteBuffer b=ByteBuffer.allocate(168).order(ByteOrder.LITTLE_ENDIAN);
        b.putInt(0x44434158).putInt(1).putInt(168).putInt(2).putInt(7).putInt(4).putInt(314).putInt(actor);
        b.putInt(1024).putInt(1000).putInt(1).putInt(15).putInt(1).putInt(0).putInt(1280).putInt(720).putInt(3);
        for(int i=0;i<4;i++)b.putInt(0);
        for(int twice=0;twice<2;twice++)for(int i=1;i<=6;i++)b.putFloat(i);
        for(int i=1;i<=6;i++)b.putFloat(i==1?8:i);
        b.putInt(0).putLong(9000);assertEquals(168,b.position());return b.array();
    }
    private static StatusData project(Owner owner,Submission original,int resultActor,int tailActor){
        byte[] raw=result(resultActor);
        var actual=new NativeCameraObserver.DetailedCapture(new NativeCameraObserver.Capture(
                "explicit-software-camera-test",314,"camera-session",4,TIME,NativeCameraObserver.decodeResult(raw),raw),tail(tailActor));
        return GuiRealmCameraStatus.project(true,owner,Optional.of(original),Optional.of(actual));
    }
    @Test void signedNativeActorSurvivesOriginalResultAndOptionalDiagnosticsWithoutUnsignedAliasing(){
        for(int actor:new int[]{Integer.MIN_VALUE,-270001,0,Integer.MAX_VALUE}){
            var owner=owner(actor);var state=project(owner,submission(owner),actor,actor);
            assertTrue(state.nativeActual().isPresent());
            var wire=PublicDataJson.object(GuiRealmCameraStatus.encode(state));var actual=wire.get("native_actual");
            assertEquals(actor,NativeCharacterId.fromJson(actual.get("actor_character_id")).value());
            var diagnostics=actual.get("settle_diagnostics");assertTrue(diagnostics.get("available").booleanValue());
            assertEquals(actor,NativeCharacterId.fromJson(diagnostics.get("request_source_frame").get("actor_character_id")).value());
            assertEquals(actor,ByteBuffer.wrap(state.nativeActual().orElseThrow().capture().base().originalResult()).order(ByteOrder.LITTLE_ENDIAN).getInt(8));
            assertFalse(actual.get("same_frame_with_gameplay_claim").booleanValue());
        }
    }
    @Test void absentOwnerFailsBeforeBindingAndOptionalAbsentTailCannotReplaceActualNegativeActor(){
        assertThrows(IllegalArgumentException.class,()->owner(-1));
        var owner=owner(-270001);var state=project(owner,submission(owner),owner.actor(),-1);
        assertTrue(state.nativeActual().isPresent());
        var actual=PublicDataJson.object(GuiRealmCameraStatus.encode(state)).get("native_actual");
        assertEquals(owner.actor(),actual.get("actor_character_id").intValue());
        assertFalse(actual.get("settle_diagnostics").get("available").booleanValue());
        assertEquals("result_binding_mismatch",actual.get("settle_diagnostics").get("reason").textValue());
    }
    @Test void sameSignedNumericDomainStillRequiresExactOriginalActorAndEpisode(){
        var owner=owner(-270001);var original=submission(owner);
        assertTrue(project(owner,original,270001,270001).nativeActual().isEmpty());
        assertTrue(project(owner(270001),original,270001,270001).nativeActual().isEmpty());
        var anotherEpisode=new Owner(owner.actor(),"other-signed-camera",314,BigInteger.ONE);
        assertTrue(project(anotherEpisode,original,owner.actor(),owner.actor()).nativeActual().isEmpty());
    }
}
