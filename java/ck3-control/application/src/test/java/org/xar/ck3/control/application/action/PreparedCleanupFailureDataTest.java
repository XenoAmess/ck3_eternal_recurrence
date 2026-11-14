package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure failure DATA only: no writer, Session, SDK, control outcome, Guard or
 * dispatch inference. All Throwable objects are explicitly software fixtures. */
final class PreparedCleanupFailureDataTest {
    private static final Instant CAPTURED=Instant.parse("2026-11-14T00:00:00Z");

    @Test void completeNestedThrowableIsArchivedExactlyWithItsTimeAndFullTraceHash() throws Exception {
        var actual=nested();var originalCause=actual.getCause();var originalSuppressed=actual.getSuppressed();
        var nestedSuppressed=originalCause.getSuppressed();String expected=trace(actual);var archive=new Memory();
        var ref=PreparedCleanupFailure.preserve(actual,CAPTURED,archive.port);
        assertEquals(1,archive.publications);assertEquals(ref.bytes(),archive.bytes.get(ref).length);
        assertEquals(ref.sha256(),sha(archive.bytes.get(ref)));
        var row=(ObjectNode)StrictJson.parse(archive.bytes.get(ref),StrictJson.EXPLICIT_MAX_BYTES);
        assertEquals(Set.of("schema","java_type","message","captured_at","complete_java_stacktrace","stacktrace_sha256"),keys(row));
        assertEquals("xar.prepared-cleanup-actual-throwable/v1",row.get("schema").textValue());
        assertEquals(IOException.class.getName(),row.get("java_type").textValue());
        assertEquals(actual.getMessage(),row.get("message").textValue());assertEquals(CAPTURED.toString(),row.get("captured_at").textValue());
        assertEquals(expected,row.get("complete_java_stacktrace").textValue());
        assertEquals(sha(expected.getBytes(StandardCharsets.UTF_8)),row.get("stacktrace_sha256").textValue());
        assertEquals(expected,trace(actual));assertEquals(2,actual.getSuppressed().length);
        assertSame(originalCause,actual.getCause());assertArrayEquals(originalSuppressed,actual.getSuppressed());
        assertArrayEquals(nestedSuppressed,actual.getCause().getSuppressed());
        assertFalse(row.has("before_write"));assertFalse(row.has("request_id"));
    }

    @Test void rawTraceAndJsonEscapedBudgetsFailClosedWithoutReplacingTheOriginalThrowable() throws Exception {
        var rawTooLarge=new IOException("x".repeat(StrictJson.EXPLICIT_MAX_BYTES+1));rawTooLarge.setStackTrace(new StackTraceElement[0]);
        assertTrue(trace(rawTooLarge).getBytes(StandardCharsets.UTF_8).length>StrictJson.EXPLICIT_MAX_BYTES);
        var rawArchive=new Memory();String originalMessage=rawTooLarge.getMessage();
        var rawFailure=assertThrows(IllegalStateException.class,()->PreparedCleanupFailure.preserve(rawTooLarge,CAPTURED,rawArchive.port));
        assertSame(rawTooLarge,rawFailure.getCause());assertEquals(1,rawFailure.getSuppressed().length);
        assertInstanceOf(IllegalArgumentException.class,rawFailure.getSuppressed()[0]);
        assertEquals(originalMessage,rawTooLarge.getMessage());assertNull(rawTooLarge.getCause());assertEquals(0,rawTooLarge.getSuppressed().length);
        assertEquals(0,rawArchive.publications);assertTrue(rawArchive.bytes.isEmpty());
        // Two complete JSON string fields encode these actual control characters;
        // the original raw stack is comfortably inside the independent raw budget.
        var escapedTooLarge=new IOException(String.valueOf((char)1).repeat(100_000));escapedTooLarge.setStackTrace(new StackTraceElement[0]);
        assertTrue(trace(escapedTooLarge).getBytes(StandardCharsets.UTF_8).length<StrictJson.EXPLICIT_MAX_BYTES);
        var escapedArchive=new Memory();String escapedMessage=escapedTooLarge.getMessage();
        var escapedFailure=assertThrows(IllegalStateException.class,()->PreparedCleanupFailure.preserve(escapedTooLarge,CAPTURED,escapedArchive.port));
        assertSame(escapedTooLarge,escapedFailure.getCause());assertEquals(1,escapedFailure.getSuppressed().length);
        assertInstanceOf(IllegalArgumentException.class,escapedFailure.getSuppressed()[0]);
        assertEquals(escapedMessage,escapedTooLarge.getMessage());assertEquals(100_000,escapedTooLarge.getMessage().length());
        assertNull(escapedTooLarge.getCause());assertEquals(0,escapedTooLarge.getSuppressed().length);
        assertEquals(0,escapedArchive.publications);assertTrue(escapedArchive.bytes.isEmpty());
    }

    @Test void archiveAndLaterEvidenceCallbacksKeepTheSamePrimaryCauseAndAllDiagnostics() throws Exception {
        var actual=nested();String originalTrace=trace(actual);var originalCause=actual.getCause();var originalSuppressed=actual.getSuppressed();
        var sentinel=new IllegalStateException("software preserveMaterial failed before a failure reference existed");
        var failedArchive=new Memory();failedArchive.archiveFailure=sentinel;
        var failed=assertThrows(IllegalStateException.class,()->PreparedCleanupFailure.preserve(actual,CAPTURED,failedArchive.port));
        assertSame(actual,failed.getCause());assertArrayEquals(new Throwable[]{sentinel},failed.getSuppressed());
        assertEquals(1,failedArchive.publications);assertTrue(failedArchive.bytes.isEmpty());
        var unchanged=assertThrows(IllegalStateException.class,()->PreparedCleanupFailure.retainingOriginal(actual,()->{throw failed;}));
        assertSame(failed,unchanged,"the actual Support outer boundary must not nest its already retained wrapper again");
        assertArrayEquals(new Throwable[]{sentinel},unchanged.getSuppressed());
        var acceptedArchive=new Memory();var afterReference=new ExactRef[1];
        var later=new IllegalArgumentException("software later FailureData publication callback rejected its material");
        var after=assertThrows(IllegalStateException.class,()->PreparedCleanupFailure.retainingOriginal(actual,()->{
            afterReference[0]=PreparedCleanupFailure.preserve(actual,CAPTURED,acceptedArchive.port);
            throw later;
        }));
        assertSame(actual,after.getCause());assertArrayEquals(new Throwable[]{later},after.getSuppressed());
        assertEquals(1,acceptedArchive.publications);assertNotNull(afterReference[0]);
        var original=(ObjectNode)StrictJson.parse(acceptedArchive.bytes.get(afterReference[0]),StrictJson.EXPLICIT_MAX_BYTES);
        assertEquals(originalTrace,original.get("complete_java_stacktrace").textValue());
        assertEquals(sha(originalTrace.getBytes(StandardCharsets.UTF_8)),original.get("stacktrace_sha256").textValue());
        var diagnosticError=new AssertionError("software diagnostic Error must not mask the original checked exception");
        var error=assertThrows(IllegalStateException.class,()->PreparedCleanupFailure.retainingOriginal(actual,()->{throw diagnosticError;}));
        assertSame(actual,error.getCause());assertArrayEquals(new Throwable[]{diagnosticError},error.getSuppressed());
        var same=new IllegalStateException("software publication throws the identical original RuntimeException");
        assertSame(same,assertThrows(IllegalStateException.class,()->PreparedCleanupFailure.retainingOriginal(same,()->{throw same;})));
        assertEquals(0,same.getSuppressed().length);assertNull(same.getCause());
        assertSame(originalCause,actual.getCause());assertArrayEquals(originalSuppressed,actual.getSuppressed());assertEquals(originalTrace,trace(actual));
    }

    private static IOException nested(){
        var cause=new IOException("software cause: original transport was unavailable");
        cause.setStackTrace(new StackTraceElement[]{new StackTraceElement("software.Endpoint","read","Endpoint.java",17)});
        cause.addSuppressed(new IllegalArgumentException("software nested suppressed"));
        var original=new IOException("software primary \"quoted\" \n\t \u0001 \u6d4b\u8bd5",cause);
        original.setStackTrace(new StackTraceElement[]{new StackTraceElement("software.Coordinator","capture","Coordinator.java",29)});
        original.addSuppressed(new IllegalStateException("software first suppressed"));
        original.addSuppressed(new IOException("software second suppressed"));return original;
    }
    private static String trace(Throwable actual){var text=new StringWriter();actual.printStackTrace(new PrintWriter(text));return text.toString();}
    private static String sha(byte[] bytes)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
    private static Set<String> keys(ObjectNode row){var result=new java.util.HashSet<String>();row.fieldNames().forEachRemaining(result::add);return result;}
    private static final class Memory {
        final Map<ExactRef,byte[]> bytes=new HashMap<>();int publications;RuntimeException archiveFailure;
        final ActionPorts.OutcomeArchive port=ActionPorts.OutcomeArchive.class.cast(Proxy.newProxyInstance(
                ActionPorts.OutcomeArchive.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
                    if(method.getName().equals("preserveMaterial")){
                        publications++;if(archiveFailure!=null)throw archiveFailure;
                        byte[] data=((RawJson)args[0]).bytes();String digest=sha(data);
                        var ref=new ExactRef("software-failure-data:"+digest,data.length,digest);bytes.put(ref,data.clone());return ref;
                    }
                    if(method.getName().equals("loadMaterial"))return RawJson.fullMaterial(bytes.get((ExactRef)args[0]));
                    if(method.isDefault())return InvocationHandler.invokeDefault(proxy,method,args);
                    throw new AssertionError("pure failure test cannot call "+method.getName());
                }));
    }
}
