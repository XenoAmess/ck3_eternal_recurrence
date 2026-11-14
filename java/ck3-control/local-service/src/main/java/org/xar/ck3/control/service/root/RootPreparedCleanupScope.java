package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.driver.DriverPersistentPlanningState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.*;

/** Only the actual Root installer can enter this lexical capability. Public
 * preparation/late DATA or a package-owned permit cannot create this Held value.
 * Every canonical/original/backend replay and dependency walk finishes BEFORE
 * the late physical read. Kept CAS leases remain open through volatile capture.
 * No material publication or canonical append occurs inside that read scope. */
final class RootPreparedCleanupScope {
    private record Held(RootRuntimeContext context,RootLifeRuntimeFactory.Installed installed,
            RootApplicationSession session,ContinuityStorePort.Session writer,LifeAdvanceComposite source,
            LifePreparedCleanupContinuation token,PreparedCleanupEvidence.Prepared prepared,long sequence,String digest,
            org.xar.ck3.control.continuity.writer.NativeOutcomeArchive.TransientOwnedCASLeaseScope originals){}
    private static final ThreadLocal<Held> CURRENT=new ThreadLocal<>();
    private record Preparing(RootRuntimeContext context,ContinuityStorePort.Session writer,
            org.xar.ck3.control.continuity.writer.NativeOutcomeArchive.TransientOwnedCASLeaseScope originals){}
    private static final ThreadLocal<Preparing> PREPARING=new ThreadLocal<>();
    static void retainVerifiedBackendSource(ExactRef ref)throws IOException {
        var preparing=PREPARING.get();if(preparing==null)return;
        preparing.context().writer().requireSession(preparing.writer());
        preparing.originals().retainQualifiedSource(ref,Math.toIntExact(ref.bytes()));
    }
    private static final class ActualInterrupted extends RuntimeException {private static final long serialVersionUID=1L;ActualInterrupted(InterruptedException original){super(original);}}
    private RootPreparedCleanupScope(){}
    static void requireClosedForProjection(){StrictJson.require(CURRENT.get()==null,"captured projection cannot run inside the historical write scope");}
    static <T>T run(RootRuntimeContext context,RootLifeRuntimeFactory.Installed installed,LifeAdvanceComposite source,
            LifePreparedCleanupContinuation token,PreparedCleanupEvidence.Prepared prepared,CompositeActionPort.PreparedCleanupWork<T> work)
            throws IOException,InterruptedException {
        StrictJson.require(CURRENT.get()==null&&PREPARING.get()==null,"prepared Root write scope cannot nest or replace an actual capability");
        installed.requireContext(context);
        if(!(context.actions() instanceof RootApplicationSession session))throw new IOException("actual prepared Root session is absent");
        try{return context.withSession(same->{
            context.writer().requireSession(same);session.requirePreparedCleanupScopeOwner(context,installed,source);
            var head=same.head();
            var durable=context.core().actions().find(prepared.command().actionId()).orElseThrow();
            StrictJson.require(durable.state() instanceof PreparedCleanupAction current
                    &&current.phase()==PreparedCleanupAction.Phase.PREPARED&&current.preparationReference().equals(prepared.reference())
                    &&durable.sequence()==head.state().sequence()&&durable.command().equals(prepared.command()),
                    "prepared Root capability requires its exact fresh canonical PREPARED claim; existing/UNKNOWN cannot remint");
            return context.archive().inHistoricalReadScope(same,new ActionPorts.HistoricalReadLimits(8192,256L*1024*1024,16384),bound->{
                var bridge=context.game().launchPlan().sources().review().bridgeDll();
                try(var originals=context.archive().openTransientOwnedCASLeaseScope(bound,same)){
                    PREPARING.set(new Preparing(context,same,originals));
                    try{
                        var replayed=PreparedCleanupEvidence.loadPrepared(prepared.reference(),bound,installed.replay());
                        StrictJson.require(replayed.command().equals(prepared.command())&&replayed.preparationNonce().equals(prepared.preparationNonce()),
                                "prepared Root scope changed complete durable preparation");
                        source.requirePreparedCleanup(prepared.command(),token);
                        RootLifeRuntimeFactory.requireQualifiedPreparedCleanupBackend(context,replayed);
                        for(var pin:same.captureSources())originals.retainQualifiedSource(pin,Math.toIntExact(pin.reference().bytes()));
                        originals.retainQualifiedSource(prepared.command().source().sourceRef(),org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES);
                        originals.retainQualifiedSource(new ExactRef(bridge.path(),bridge.bytes(),bridge.sha256()),org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES);
                        originals.requirePreparedCustody();
                        var current=same.head();
                        StrictJson.require(current.state().sequence()==head.state().sequence()&&current.digest().equals(head.digest()),
                                "prepared Root scope changed the actual durable head before late observation");
                        var held=new Held(context,installed,session,same,source,token,prepared,head.state().sequence(),head.digest(),originals);
                        Throwable primary=null;CURRENT.set(held);
                        try{return work.run();}
                        catch(InterruptedException interrupted){primary=interrupted;throw new ActualInterrupted(interrupted);}
                        catch(IOException|RuntimeException|Error failure){primary=failure;throw failure;}
                        finally{
                            CURRENT.remove();
                            try{
                                context.writer().requireSession(same);session.requirePreparedCleanupScopeOwner(context,installed,source);
                                StrictJson.require(same.head().digest().equals(held.digest()),"prepared world/capture callback changed its held canonical head");
                                RootLifeRuntimeFactory.requireQualifiedPreparedCleanupBackend(context,prepared);
                                for(var pin:same.captureSources())originals.retainQualifiedSource(pin,Math.toIntExact(pin.reference().bytes()));
                                originals.retainQualifiedSource(prepared.command().source().sourceRef(),org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES);
                                originals.retainQualifiedSource(new ExactRef(bridge.path(),bridge.bytes(),bridge.sha256()),org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES);
                                originals.verifyAndClose();
                            }catch(IOException|RuntimeException|Error closing){if(primary!=null){if(closing!=primary)primary.addSuppressed(closing);}else throw closing;}
                        }
                    }finally{PREPARING.remove();}
                }
            });
            // inHistoricalReadScope finishes and closes every retained lease before
            // returning to the coordinator's material/outcome publication code.
        });}catch(ActualInterrupted interrupted){throw (InterruptedException)interrupted.getCause();}
    }
    /** Fixed private source registration, not a user switch or a capability
     * advertised by arbitrary DATA. Legacy submit is explicitly rejected. */
    static NativePrivateActionPermission permission(ExactRef actualSource){
        var operation=new OperationKey(ClockStatusRead.CANCEL_PREFIX+"79");
        return new NativePrivateActionPermission(operation,"source_owned_prepared_cleanup",actualSource,request->{
            if(!request.step().equals(operation.value())||!request.additionalFields().objectFieldNames().isEmpty())
                throw new IOException("prepared Root private registration changed its exact generation-bound request");
        },(config,hello,guard,request)->{throw new IOException("prepared Root registration grants no legacy SubmissionPermit route");})
        .withPreparedQualification(new NativePrivateActionPermission.PreparedQualification(){
            @Override public ExactRef requireObservation(NativePipeEndpoint.Config config,NativeWire.Hello hello,PreparedCleanupObservationPermit permit)throws IOException {
                var held=require(config,hello);requirePermit(held,permit.preparation(),permit.sourceToken(),permit.preparationSequence(),permit.issuedBy(held.source()));
                return held.prepared().reference();
            }
            @Override public ExactRef requireWrite(NativePipeEndpoint.Config config,NativeWire.Hello hello,PreparedCleanupPermit permit,NativeRequest request)throws IOException {
                var held=require(config,hello);requirePermit(held,permit.preparation(),permit.sourceToken(),permit.preparationSequence(),permit.issuedBy(held.source()));
                StrictJson.require(ActionCommandScope.current().filter(permit.command()::equals).isPresent()
                        &&permit.preparedRequest().equals(request)&&permit.actualExpectedRevision().equals(permit.binding().writeFrame().nativeRevision()),
                        "prepared actual SDK write lost its exact child command or actual late revision");
                permit.requireFresh();PreparedCleanupEvidence.requireLateBinding(permit.binding(),held.context().clock().instant());
                return held.prepared().reference();
            }
        });
    }
    private static Held require(NativePipeEndpoint.Config config,NativeWire.Hello hello)throws IOException {
        var held=CURRENT.get();if(held==null)throw new IOException("actual Root prepared write capability is not active on this thread");
        var context=held.context();context.writer().requireSession(held.writer());held.originals().requireActive();
        held.session().requirePreparedCleanupScopeOwner(context,held.installed(),held.source());
        var now=context.clock().instant();
        StrictJson.require(now.isBefore(held.prepared().deadline())&&held.writer().head().digest().equals(held.digest())
                &&config.machineId().equals(context.game().machineId())&&config.game().equals(context.game().generation())
                &&config.sessionId().equals(context.game().sessionId())&&config.pipeName().equals(context.game().launchPlan().pipeName())
                &&context.source().equals(held.prepared().command().source())&&hello==context.transport().originalHello()
                &&hello.buildMatch()&&hello.pid()==config.game().pid(),"actual prepared Root/source/Game/held-head/transport ownership changed");
        return held;
    }
    private static void requirePermit(Held held,PreparedCleanupEvidence.Prepared prepared,CompositeContinuationToken token,long sequence,boolean sameSource){
        StrictJson.require(sameSource&&prepared==held.prepared()&&token==held.token()&&sequence==held.sequence()
                &&prepared.preparationNonce().equals(held.prepared().preparationNonce())
                &&prepared.command().equals(held.prepared().command()),"prepared permit is not the actual held Root source/preparation/head/nonce");
    }
}
