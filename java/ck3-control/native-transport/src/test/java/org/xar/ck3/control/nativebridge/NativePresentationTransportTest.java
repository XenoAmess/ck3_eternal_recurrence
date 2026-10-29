package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.presentation.*;

/** Real transport read/physical-preparation algorithms over one self-owned software memory, never a fabricated canonical permit. */
final class NativePresentationTransportTest {
    private static PresentationRequest.Owner owner(){return new PresentationRequest.Owner("presentation-software-test","software-session",314,
            "133444444444444444",PresentationRequest.EXECUTABLE_SHA256,"software-episode","1");}
    private static Instant deadline(){return Instant.now().plusSeconds(10);}
    private static final class Originals implements PresentationOriginals {
        final Map<ExactRef,OriginalArtifact> saved=new LinkedHashMap<>();long charged;
        @Override public ExactRef preservePresentationArtifact(OriginalArtifact value) {
            ExactRef ref=reference(value);if(!saved.containsKey(ref)){
                if(charged+value.bytes().length>2*1024*1024)throw new IllegalStateException("finite software original budget exceeded");
                saved.put(ref,value);charged+=value.bytes().length;
            }return ref;
        }
        @Override public OriginalArtifact loadPresentationArtifact(ArtifactRole role,ExactRef ref){var value=saved.get(ref);if(value==null||value.role()!=role)throw new IllegalArgumentException("actual software original missing");return value;}
        @Override public ExactRef presentationArtifactReferenceOf(OriginalArtifact value){ExactRef ref=reference(value);if(!saved.containsKey(ref))throw new IllegalArgumentException("unpreserved software original");return ref;}
        private static ExactRef reference(OriginalArtifact value){try{
            byte[] raw=value.bytes();String sha=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
            return new ExactRef("explicit-software-original/"+value.role()+"/"+sha,raw.length,sha);
        }catch(java.security.NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}}
    }
    @Test void actualPreparationReadsOriginalHeaderUptimeAndOwnedWindowWithoutPhysicalPost()throws Exception {
        try(var scenario=NativePresentationMemoryFixture.create(owner(),new Originals())) {
            var actual=scenario.transport().inspect(deadline());assertEquals(owner(),actual.owner());
            assertEquals("100000",actual.uptimeMillis());assertEquals("4096",actual.hwnd());
            assertEquals(0,actual.previousRequestSequence());assertEquals(0,actual.baselineResultSequence());
            assertArrayEquals(scenario.originalHeader(),actual.originalHeader());assertEquals(0,scenario.actualWriteAttempts());
            actual.originalHeader()[0]=0;assertEquals(0x43524158,ByteBuffer.wrap(actual.originalHeader()).order(ByteOrder.LITTLE_ENDIAN).getInt());
        }
    }
    @Test void untouchedBaselineIsPendingAndPollingDoesNotSubmitOrAdvanceNative()throws Exception {
        try(var scenario=NativePresentationMemoryFixture.create(owner(),new Originals())) {
            var request=scenario.request("pending-original");
            var pending=assertInstanceOf(PresentationObservation.Pending.class,scenario.transport().observe(request,deadline()));
            assertEquals("no_fresh_even_result",pending.reason());assertEquals(0,scenario.actualWriteAttempts());
            assertEquals(pending,PresentationObservation.decode(pending.encode()));
        }
    }
    @Test void softwareNativeResultSamplingAcknowledgesRawSequenceButDoesNotProveAPostOrCameraEffect()throws Exception {
        var originals=new Originals();
        try(var scenario=NativePresentationMemoryFixture.create(owner(),originals)) {
            var request=scenario.request("result-original");scenario.publishResult(request.requestSequence(),1);
            var ack=assertInstanceOf(PresentationObservation.Acknowledged.class,scenario.transport().observe(request,deadline()));
            assertEquals(PresentationObservation.Status.SUBMITTED,ack.status());assertEquals(request.requestSequence(),ack.acknowledgedRequestSequence());
            var capture=ack.capture();ack.verifyOriginal(originals.loadPresentationArtifact(PresentationOriginals.ArtifactRole.HEADER,capture.originalHeader()).bytes(),
                    originals.loadPresentationArtifact(PresentationOriginals.ArtifactRole.RESULT,capture.originalResult()).bytes(),
                    originals.loadPresentationArtifact(PresentationOriginals.ArtifactRole.DIAGNOSTICS,capture.originalDiagnostics()).bytes());
            assertEquals(ack,PresentationObservation.decode(ack.encode()));assertEquals(0,scenario.actualWriteAttempts());
            assertTrue(scenario.transport().retainedFailure().isEmpty()); // No posted proof or canonical permission is manufactured by this read-only fixture.
        }
    }
    @Test void oddOrChangedResultSeqlockRetainsTornBytesWithoutParsingAnAck()throws Exception {
        for(boolean race:new boolean[]{false,true})try(var scenario=NativePresentationMemoryFixture.create(owner(),new Originals())) {
            var request=scenario.request("torn-original");byte[] raw=new byte[65640];ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN).putInt(4,-1);
            scenario.publishOriginalResult(raw,new byte[168]);if(race)scenario.raceResultDuringCopy();else scenario.oddResultPublication();
            var pending=assertInstanceOf(PresentationObservation.Pending.class,scenario.transport().observe(request,deadline()));
            assertEquals("no_fresh_even_result",pending.reason());assertEquals(0,scenario.actualWriteAttempts());
        }
    }
    @Test void malformedFreshResultAndDifferentRequestNeverBecomeThisRequestsAck()throws Exception {
        try(var scenario=NativePresentationMemoryFixture.create(owner(),new Originals())) {
            var request=scenario.request("matching-original");scenario.publishResult(request.requestSequence()+2,1);
            assertEquals("different_original_request",assertInstanceOf(PresentationObservation.Pending.class,scenario.transport().observe(request,deadline())).reason());
            scenario.publishResult(request.requestSequence(),9);
            var unavailable=assertInstanceOf(PresentationObservation.Unavailable.class,scenario.transport().observe(request,deadline()));
            assertEquals(3,unavailable.originals().size());assertEquals(0,scenario.actualWriteAttempts());
        }
    }
    @Test void actualSourceFailureOrExpiredDeadlineIsUnavailableWithoutReadingAnotherChannel()throws Exception {
        try(var scenario=NativePresentationMemoryFixture.create(owner(),new Originals())) {
            var request=scenario.request("unavailable-original");int reads=scenario.actualReads();
            assertInstanceOf(PresentationObservation.Unavailable.class,scenario.transport().observe(request,Instant.now().minusSeconds(1)));
            assertEquals(reads,scenario.actualReads());scenario.failSource();
            assertInstanceOf(PresentationObservation.Unavailable.class,scenario.transport().observe(request,deadline()));
            assertEquals(0,scenario.actualWriteAttempts());
        }
    }
    @Test void missingCanonicalPermitCannotReachTheMappingWriterOrArchive()throws Exception {
        var originals=new Originals();
        try(var scenario=NativePresentationMemoryFixture.create(owner(),originals)) {
            var request=scenario.request("no-permit");
            assertThrows(NullPointerException.class,()->scenario.transport().post(null,request,deadline()));
            assertEquals(0,scenario.actualWriteAttempts());assertEquals(0,scenario.actualReads());assertTrue(originals.saved.isEmpty());
        }
    }

    @Test void automaticDataWithoutOriginalPermitCannotReadOrWriteMapping()throws Exception{
        var i=new PresentationIntent("no-permit",Instant.now().minusMillis(1),owner(),new PresentationRequest.Frame("snapshot","2","7",73,1000),
          PresentationRequest.Mode.HOTSPOT,"b_test",java.util.Optional.empty(),deadline());
        try(var scenario=NativePresentationMemoryFixture.create(owner(),new Originals())){
            assertThrows(NullPointerException.class,()->scenario.transport().capture(null,i));
            assertEquals(0,scenario.actualWriteAttempts());assertEquals(0,scenario.actualReads());
        }
    }
    @Test void trackingSamplesReadActualEightyBytesAndRejectTornOrForeignBinding()throws Exception{
        try(var scenario=NativePresentationMemoryFixture.create(owner(),new Originals())){
            scenario.publishTrackingCapability(false);var request=scenario.trackingRequest("tracking-read");
            scenario.publishTrackingResult(request,false);
            var sample=scenario.transport().sample(request,deadline());
            assertEquals(80,sample.trackingResult().orElseThrow().length);
            var actual=org.xar.ck3.control.nativebridge.capabilities.gui.NativeCameraObserver.trackingActual(request,sample).orElseThrow();
            assertEquals("9007199254740993",actual.scopeGeneration());assertTrue(actual.active());
            assertFalse(actual.toJson().get("camera_postcondition_verified").booleanValue());
            scenario.publishTrackingResult(request,true);
            assertTrue(org.xar.ck3.control.nativebridge.capabilities.gui.NativeCameraObserver.trackingActual(request,scenario.transport().sample(request,deadline())).isEmpty());
            scenario.publishTrackingResult(request,false);scenario.raceTrackingDuringCopy();
            assertTrue(scenario.transport().sample(request,deadline()).trackingResult().isEmpty());
            assertEquals(0,scenario.actualWriteAttempts());
        }
    }
}
