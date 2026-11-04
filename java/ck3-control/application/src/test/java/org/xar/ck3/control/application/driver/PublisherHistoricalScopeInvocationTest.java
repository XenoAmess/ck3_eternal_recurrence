package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Package-level DATA seam tests for callback custody. No Session/UNKNOWN/Root proof issuer is fabricated. */
public final class PublisherHistoricalScopeInvocationTest {
    @Test void returnsOnlyThisWorkResultAfterScopeExit()throws IOException {
        var value=new Object();var calls=new AtomicInteger();var order=new StringBuilder();
        var actual=DriverUnresolvedHistoryLineage.verifyWithinScope(null,null,(session,work)->{
            order.append("enter/");work.read();order.append("exit");
        },bound->{calls.incrementAndGet();order.append("work/");return value;});
        assertSame(value,actual);assertEquals(1,calls.get());assertEquals("enter/work/exit",order.toString());
    }
    @Test void skippedWorkCannotIssueResult() {
        var calls=new AtomicInteger();
        assertThrows(IOException.class,()->DriverUnresolvedHistoryLineage.verifyWithinScope(null,null,(session,work)->{},
                bound->{calls.incrementAndGet();return new Object();}));
        assertEquals(0,calls.get());
    }
    @Test void swallowedDuplicateStillRejectsAndNeverRepeatsWork() {
        var calls=new AtomicInteger();var duplicate=new AtomicReference<IOException>();
        var actual=assertThrows(IOException.class,()->DriverUnresolvedHistoryLineage.verifyWithinScope(null,null,(session,work)->{
            work.read();try {work.read();}catch(IOException denied){duplicate.set(denied);}
        },bound->{calls.incrementAndGet();return new Object();}));
        assertSame(duplicate.get(),actual);assertEquals(1,calls.get());
    }
    @Test void swallowedForeignThreadAttemptPoisonsLaterInlineAttempt() {
        var calls=new AtomicInteger();var denied=new AtomicReference<IOException>();
        var actual=assertThrows(IOException.class,()->DriverUnresolvedHistoryLineage.verifyWithinScope(null,null,(session,work)->{
            var thread=new Thread(()->{try {work.read();}catch(IOException original){denied.set(original);}});
            thread.start();
            try {thread.join();}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
            work.read();
        },bound->{calls.incrementAndGet();return new Object();}));
        assertNotNull(denied.get());assertSame(denied.get(),actual);assertEquals(1,calls.get());
    }
    @Test void retainedCallbackRejectsBeforeWorkAfterReturn()throws IOException {
        var saved=new AtomicReference<DriverReadHistoryPublisher.CheckedHistoricalRead>();var calls=new AtomicInteger();
        var value=new Object();
        assertSame(value,DriverUnresolvedHistoryLineage.verifyWithinScope(null,null,(session,work)->{saved.set(work);work.read();},
                bound->{calls.incrementAndGet();return value;}));
        assertThrows(IOException.class,()->saved.get().read());assertEquals(1,calls.get());
    }
    @Test void originalIoRuntimeAndErrorCannotBeSwallowed() {
        Throwable[] originals={new IOException("original io"),new IllegalArgumentException("original runtime"),new AssertionError("original error")};
        for(var original:originals){
            var actual=assertThrows(Throwable.class,()->DriverUnresolvedHistoryLineage.verifyWithinScope(null,null,(session,work)->{
                try {work.read();}catch(IOException|RuntimeException|Error swallowed){assertSame(original,swallowed);}
            },bound->{
                if(original instanceof IOException io)throw io;
                if(original instanceof RuntimeException runtime)throw runtime;
                throw (Error)original;
            }));
            assertSame(original,actual);
        }
    }
    @Test void nativeMissingOriginalWrapperRemainsNonOptional() {
        var missing=new java.nio.file.NoSuchFileException("original historical material");
        var wrapped=new IOException("historical original validation failed; not optional absence",missing);
        var actual=assertThrows(IOException.class,()->DriverUnresolvedHistoryLineage.verifyWithinScope(null,null,(session,work)->{
            try {work.read();}catch(java.nio.file.NoSuchFileException original){assertSame(missing,original);throw wrapped;}
        },bound->{throw missing;}));
        assertSame(wrapped,actual);assertSame(missing,actual.getCause());
    }
    @Test void scopeExitFailurePreventsCompletedResult() {
        var close=new IOException("scope exit");var calls=new AtomicInteger();
        var actual=assertThrows(IOException.class,()->DriverUnresolvedHistoryLineage.verifyWithinScope(null,null,(session,work)->{
            work.read();throw close;
        },bound->{calls.incrementAndGet();return new Object();}));
        assertSame(close,actual);assertEquals(1,calls.get());
    }
}
