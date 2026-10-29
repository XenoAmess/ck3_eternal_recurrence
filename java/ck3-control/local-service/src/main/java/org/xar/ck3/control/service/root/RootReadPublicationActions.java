package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverReadHistoryPublisher;
import org.xar.ck3.control.application.driver.DriverActionHistoryPublisher;
import org.xar.ck3.control.application.planning.OrdinaryPlanCompletion;
import org.xar.ck3.control.application.session.ReadPublicationRefreshException;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** The sole coordinator keeps its original writer lease until queued READs have left every native/Driver freeze. */
final class RootReadPublicationActions implements ActionCoordinatorPort {
    private final RootApplicationAssembly.Core core;
    private final ActionCoordinatorPort actual;
    private final DriverReadHistoryPublisher reads;
    private final DriverActionHistoryPublisher histories;
    RootReadPublicationActions(RootApplicationAssembly.Core core,ActionCoordinatorPort actual,DriverReadHistoryPublisher reads,DriverActionHistoryPublisher histories) {
        this.core=Objects.requireNonNull(core);this.actual=Objects.requireNonNull(actual);this.reads=Objects.requireNonNull(reads);this.histories=Objects.requireNonNull(histories);
    }
    @Override public ActionReceipt execute(ActionCommand command) {
        try{return core.withBorrowed(()->executeInSession(core.writer().borrowedSession(),command));}
        catch(IOException failure){throw new UncheckedIOException(failure);}
        catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IllegalStateException("original action scope interrupted; no replay",interrupted);}
    }
    @Override public ActionReceipt execute(ContinuityStorePort.Session same,ActionCommand command) {
        return core.journal().locked(same,locked->executeInSession(same,command));
    }
    private ActionReceipt executeInSession(ContinuityStorePort.Session same,ActionCommand command) {
        try {
            core.writer().requireSession(same);
            try {
                ActionReceipt receipt=actual.execute(same,command);
                histories.completed(same,receipt);reads.flushActualReads(same);return receipt;
            } catch(ReadPublicationRequiredException pending) {
                throw refreshed(same,command,pending);
            } catch(RuntimeException|Error failure) {
                flushFailure(same,failure);throw failure;
            }
        }catch(IOException failure){throw new UncheckedIOException("actual action/query outcome retained; READ publication unavailable, no replay",failure);}
    }
    @Override public ActionReceipt reconcile(String actionId) {
        try{return core.withBorrowed(()->reconcileInSession(core.writer().borrowedSession(),actionId));}
        catch(IOException failure){throw new UncheckedIOException(failure);}
        catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IllegalStateException("original reconciliation interrupted; no replay",interrupted);}
    }
    @Override public ActionReceipt reconcile(ContinuityStorePort.Session same,String actionId) {
        return core.journal().locked(same,locked->reconcileInSession(same,actionId));
    }
    private ActionReceipt reconcileInSession(ContinuityStorePort.Session same,String actionId) {
        try {
            core.writer().requireSession(same);
            var original=core.journal().locked(same,locked->locked.find(actionId).orElseThrow()).command();
            try {var receipt=actual.reconcile(same,actionId);histories.completed(same,receipt);reads.flushActualReads(same);return receipt;}
            catch(ReadPublicationRequiredException pending){throw refreshed(same,original,pending);}
            catch(RuntimeException|Error failure){flushFailure(same,failure);throw failure;}
        }catch(IOException failure){throw new UncheckedIOException("original reconciliation retained; READ publication unavailable",failure);}
    }
    @Override public CompositeContinuationReport continueOriginalComposite(CompositeContinuationToken token)throws IOException {
        try{return core.withBorrowed(()->continueInSession(core.writer().borrowedSession(),token));}
        catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("original composite continuation interrupted; no replay",interrupted);}
    }
    @Override public CompositeContinuationReport continueOriginalComposite(ContinuityStorePort.Session same,CompositeContinuationToken token)throws IOException {
        core.writer().requireSession(same);
        try{return core.journal().locked(same,locked->{
            try{return continueInSession(same,token);}catch(IOException failure){throw new UncheckedIOException(failure);}
        });}catch(UncheckedIOException failure){throw failure.getCause();}
    }
    private CompositeContinuationReport continueInSession(ContinuityStorePort.Session same,CompositeContinuationToken token)throws IOException {
        core.writer().requireSession(same);Objects.requireNonNull(token);
        try {
            var report=actual.continueOriginalComposite(same,token);
            histories.completed(same,report.parent());reads.flushActualReads(same);return report;
        }catch(ReadPublicationRequiredException pending){throw refreshed(same,token.originalParent(),pending);}
        catch(IOException|RuntimeException|Error failure){flushFailure(same,failure);throw failure;}
    }
    private void flushFailure(ContinuityStorePort.Session same,Throwable original) {
        // A failed preparer may already have made genuine reads. Its stack has left all freezes;
        // retain those reads in this actual Session without inventing a zero-dispatch outcome or retrying the command.
        try { reads.flushActualReads(same); }
        catch(IOException|RuntimeException publicationFailure) { if(publicationFailure!=original)original.addSuppressed(publicationFailure); }
    }
    private RuntimeException refreshed(ContinuityStorePort.Session same,ActionCommand original,ReadPublicationRequiredException pending)throws IOException {
        boolean direct=Arrays.equals(ActionCodec.encodeCommand(original),ActionCodec.encodeCommand(pending.command()));
        if(!direct) {
            // A child can request publication while its retained parent is already UNKNOWN. The exact durable reservation proves ancestry.
            var parent=core.journal().locked(same,locked->locked.find(original.actionId()).orElseThrow());
            StrictJson.require(Arrays.equals(ActionCodec.encodeCommand(original),ActionCodec.encodeCommand(parent.command()))
                    &&parent.state() instanceof ActionState.CompositeUnknown,"child READ publication has no original canonical unresolved parent");
            var execution=ActionTransitions.composite(parent.state()).orElseThrow();
            StrictJson.require(execution.children().stream().anyMatch(child->child.actionId().equals(pending.command().actionId())
                    &&child.bodySha256().equals(ActionCodec.bodySha256(pending.command()))),"READ publication child was not reserved by this actual parent");
        }
        var publication=reads.flushActualReads(same);if(publication.isEmpty())return pending;
        var committed=publication.orElseThrow();
        return new ReadPublicationRefreshException(original,direct?pending.zeroDispatchReceipt():java.util.Optional.empty(),
                new OrdinaryPlanCompletion.Published(committed.predecessor(),committed.actual()),
                direct?java.util.Optional.empty():java.util.Optional.of(original.actionId()));
    }
}
