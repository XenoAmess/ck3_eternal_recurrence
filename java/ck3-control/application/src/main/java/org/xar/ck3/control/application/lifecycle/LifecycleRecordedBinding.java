package org.xar.ck3.control.application.lifecycle;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;

/** Root installs this dedicated branch for LifecycleApplied; ordinary effect comparison cannot approve a lifecycle transition. */
public final class LifecycleRecordedBinding implements NativeRecordedEvidenceVerifier.ArchivedVerifier {
    @FunctionalInterface public interface WriterAuthority { void require(ContinuityStorePort.Session borrowed) throws IOException; }
    private final LifecycleComposites actual;
    private final LifecycleComposites.BorrowedWriter writer;
    private final WriterAuthority authority;
    public LifecycleRecordedBinding(LifecycleComposites actual,LifecycleComposites.BorrowedWriter writer,WriterAuthority authority) {
        this.actual=Objects.requireNonNull(actual);this.writer=Objects.requireNonNull(writer);this.authority=Objects.requireNonNull(authority);
    }
    @Override public void verify(WriterContracts.Head actualLockedHead,ActionReceipt proposed,ActionPorts.OutcomeArchive sameWriterArchive) {
        Objects.requireNonNull(sameWriterArchive);
        try { verifyApplied(actualLockedHead,proposed); } catch(IOException failure) { throw new UncheckedIOException(failure); }
    }
    public void verifyApplied(WriterContracts.Head actualLockedHead,ActionReceipt proposed) throws IOException {
        Objects.requireNonNull(actualLockedHead);Objects.requireNonNull(proposed);var borrowed=writer.current();authority.require(borrowed);
        StrictJson.require(borrowed.head().digest().equals(actualLockedHead.digest()),"lifecycle evidence binding requires exact actual original writer head");
        ActionState.Settlement settlement;
        if(proposed.state() instanceof ActionState.CompositeSettled composite)settlement=composite.settlement();
        else throw new IOException("lifecycle proof can settle only its registered composite parent");
        if(!(settlement instanceof ActionState.LifecycleApplied applied))throw new IOException("dedicated lifecycle binding received another settlement kind");
        actual.verifyRecorded(proposed.command(),applied.proof(),actualLockedHead);
        StrictJson.require(borrowed.head().digest().equals(actualLockedHead.digest()),"original writer head changed during lifecycle provenance verification");
    }
}
