package org.xar.ck3.control.nativebridge.capabilities.frontend_coa;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;

/** Software read/no-write transcript; positive presentation needs the real central private permit fixture. */
class CoaWindowCaptureReadTest {
    private static final GameGeneration GAME=new GameGeneration(1234,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final Clock CLOCK=Clock.fixed(Instant.parse("2026-10-24T00:00:00Z"),ZoneOffset.UTC);
    @Test void preflightPreservesSignedDesktopRectAndExactWindowBirthWithoutAnyWrite()throws Exception {
        var fixture=CoaWindowCaptureSoftwareFixture.create(GAME,CoaWindowCaptureSoftwareFixture.Script.DIRECT,CLOCK);
        var before=fixture.capture().preflightReadOnly();assertEquals(GAME,before.game());
        assertEquals("9007199254740993",before.window().hwnd());assertEquals(-2560,before.window().clientRect().left());
        assertEquals("9",before.foregroundRoot());assertEquals(0,fixture.writes().get());assertEquals(0,fixture.captures().get());
        assertThrows(IllegalArgumentException.class,()->fixture.capture().captureReadOnly());
        assertEquals(0,fixture.writes().get());assertEquals(0,fixture.captures().get());
    }
    @Test void readOnlyPixelsUseActualTranscriptWindowAndNeverAutoprepareForeground()throws Exception {
        var fixture=CoaWindowCaptureSoftwareFixture.create(GAME,CoaWindowCaptureSoftwareFixture.Script.ALREADY_FOREGROUND,CLOCK);
        var frame=fixture.capture().captureReadOnly();assertEquals(new CoaFramebuffer.Size(2560,1440),frame.image().size());
        assertEquals(GAME.pid(),frame.bridgePid());assertEquals(CLOCK.instant(),frame.observedAt());assertEquals(1,fixture.captures().get());assertEquals(0,fixture.writes().get());
        assertThrows(IllegalArgumentException.class,()->new CoaWindowCapture.ScreenRect(Integer.MIN_VALUE,0,Integer.MAX_VALUE,1440));
    }
}
