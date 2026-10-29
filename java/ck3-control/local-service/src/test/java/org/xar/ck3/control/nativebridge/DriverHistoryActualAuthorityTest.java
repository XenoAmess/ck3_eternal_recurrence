package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.application.history.DriverHistoryAccess;

/** Real adopted assembler, original writer and physical archive; the only delayed value is the actual Root owner reference. */
final class DriverHistoryActualAuthorityTest {
    @TempDir Path temporary;
    @Test void constructionDoesNotResolveAnUnadoptedDriverAndUseResolvesExactlyOnceUnderTheRealWriter()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("lazy-actual-history"),false)) {
            var adopted=new AtomicReference<DriverStateAssembler>();var resolutions=new AtomicInteger();
            var history=new DriverHistoryAccess(()->{
                resolutions.incrementAndGet();var actual=adopted.get();
                if(actual==null)throw new IllegalStateException("actual Root Driver has not been adopted");return actual;
            },fixture.archive);
            assertEquals(0,resolutions.get(),"pre-adoption construction must not resolve current Driver");
            var parent=fixture.command("lazy-history-parent");
            assertThrows(IllegalStateException.class,()->history.read(parent));assertEquals(1,resolutions.get());assertEquals(0,fixture.nativeActionWrites());
            adopted.set(fixture.driverAuthority());
            var view=history.withView(parent,actual->{
                try{fixture.writer.requireSession(fixture.writer.borrowedSession());}catch(java.io.IOException failed){throw new java.io.UncheckedIOException(failed);}
                assertEquals(2,resolutions.get(),"one concrete owner resolution per withView");return actual;
            });
            assertEquals(2,resolutions.get());assertEquals(view.stamp().driverSha256(),view.currentDriverEvidence().sha256());
            assertArrayEquals(fixture.archive.loadMaterial(view.currentDriverEvidence()).bytes(),
                    fixture.archive.loadMaterial(history.read(parent).currentDriverEvidence()).bytes());
            assertEquals(3,resolutions.get());assertEquals(0,fixture.nativeActionWrites(),"history access cannot submit a gameplay action");
        }
    }
    @Test void stableConstructorAndActualAuthorityReadTheSameCompleteOriginalSerialization()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("stable-actual-history"),false)) {
            var parent=fixture.command("stable-history-parent");
            var stable=new DriverHistoryAccess(fixture.driverAuthority(),fixture.archive);
            var delayed=new DriverHistoryAccess(fixture::driverAuthority,fixture.archive);
            var expected=stable.read(parent);var actual=delayed.read(parent);
            assertEquals(expected,actual);
            byte[] original=fixture.archive.loadMaterial(actual.currentDriverEvidence()).bytes();
            assertEquals(DriverJson.object(original,DriverJson.MAX_NATIVE_BYTES),DriverJson.object(fixture.archive.loadMaterial(expected.currentDriverEvidence()).bytes(),DriverJson.MAX_NATIVE_BYTES));
            assertEquals(0,fixture.nativeActionWrites());
        }
    }
    @Test void lazyBindingCannotSubstituteAForeignArchiveOrReturnANullAuthority()throws Exception {
        try(var first=new ActionWriterIntegrationFixture(temporary.resolve("history-owner"),false);
                var other=new ActionWriterIntegrationFixture(temporary.resolve("foreign-archive"),false)) {
            var parent=first.command("cross-writer-history-parent");other.ready();
            var cross=new DriverHistoryAccess(first::driverAuthority,other.archive);
            assertThrows(Exception.class,()->cross.read(parent),"actual assembler lease cannot borrow another canonical writer/archive");
            var absent=new DriverHistoryAccess((DriverHistoryAccess.ActualAuthority)()->null,first.archive);
            assertThrows(NullPointerException.class,()->absent.read(parent));
            assertEquals(0,first.nativeActionWrites());assertEquals(0,other.nativeActionWrites());
        }
    }
}
