package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof;
import org.xar.ck3.control.application.session.OrdinaryEpisodeContinuation;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.application.session.SessionPorts.CompletedCycleProof;
import org.xar.ck3.control.application.session.SessionPorts.EpisodeContinuation;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.StrictJson;

/** Resolves the admitted same-Game Root at invocation time, after construction has finished. */
public final class RootEpisodeContinuationRuntime implements EpisodeContinuation {
    private final RootApplicationAssembly.Core core;
    private final RootRuntimeCatalogFactory catalogs;

    public RootEpisodeContinuationRuntime(RootApplicationAssembly.Core actualCore,RootRuntimeCatalogFactory actualCatalogs) throws IOException {
        core=Objects.requireNonNull(actualCore);catalogs=Objects.requireNonNull(actualCatalogs);
        catalogs.requireBoundCore(core);
    }

    /** Startup retains these exact producer objects; identity alone grants no current session or lifecycle proof. */
    public void requireCore(RootApplicationAssembly.Core identicalCore,RootRuntimeCatalogFactory identicalCatalogs) throws IOException {
        StrictJson.require(core==Objects.requireNonNull(identicalCore)&&catalogs==Objects.requireNonNull(identicalCatalogs),
                "episode continuation factory belongs to another original Core/catalog factory");
        catalogs.requireBoundCore(core);
    }

    @Override public CompletedCycleProof continueSameGame(SessionIdentity owner,ActionReceipt receipt,Instant deadline) throws IOException {
        return continueAdmittedSameGame(owner,receipt,deadline).proof();
    }
    @Override public ContinuityBatchJournal.AdmittedEpisode continueAdmittedSameGame(SessionIdentity owner,ActionReceipt receipt,Instant deadline) throws IOException {
        Objects.requireNonNull(owner);Objects.requireNonNull(receipt);Objects.requireNonNull(deadline);
        requireNaturalParent(owner,receipt);
        try {
            return core.withBorrowed(()->{
                var same=core.activeBorrowedSession();core.writer().requireSession(same);
                var root=core.sessionAccess().current();
                StrictJson.require(root.ownedBy(core)&&root.hasInstalledHost()&&!root.isRetired()&&root.identity().equals(owner)
                        &&root.writer()==core.writer()&&root.archive()==core.archive(),
                        "natural continuation requires the admitted original Core/Root/physical Game/session");
                var installed=catalogs.requireCurrentCatalog(root);var context=installed.context();
                StrictJson.require(context.adopted()==root.driver()&&context.writer()==root.writer()&&context.archive()==root.archive()
                        &&context.borrowedSession()==same&&context.source().equals(receipt.command().source()),
                        "natural continuation catalog/source/Driver differs from the admitted Root");
                var lifecycle=installed.remainingDomains().lifecycle();lifecycle.requireContext(context);
                ContinuityBatchJournal.AdmittedEpisode admitted;
                var current=lifecycle.admittedCurrent(same,receipt,deadline);
                if(current.isPresent()) {
                    admitted=root.batchJournal().admitCurrentEpisode(same,current.orElseThrow());
                }else {
                    var committed=lifecycle.composite().requireCommittedEpisode(same,receipt);
                    StrictJson.require(((LifecycleTransitionProof)committed).kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR,
                            "only the original private committed natural successor can continue the same Game");
                    var inputs=new LifecycleEpisodeInputs(core.writer(),core.writer()::requireSession,lifecycle.composite(),
                            root.driver().authority(),core.archive(),core.semanticVerifier());
                    var delegate=new OrdinaryEpisodeContinuation(root.batchJournal(),inputs,root.readiness()::semanticAfterLifecycle);
                    admitted=delegate.continueAdmittedSameGame(same,owner,receipt,deadline);
                }
                var proof=admitted.proof();
                core.requireCurrentForAccess(same,root);
                StrictJson.require(!root.isRetired()&&proof.frame().machineId().equals(owner.machineId())&&proof.frame().game().equals(owner.game()),
                        "natural continuation changed Root or physical owner during its original writer transaction");
                return admitted;
            });
        }catch(InterruptedException interrupted){
            Thread.currentThread().interrupt();var failure=new InterruptedIOException("actual same-Game continuation interrupted");
            failure.initCause(interrupted);throw failure;
        }
    }

    /** A distinct actual same-OS-Game route after canonical transport custody; the old strict same-session entry is unchanged. */
    @Override public ContinuityBatchJournal.AdmittedEpisode continueTransportedSameGame(SessionIdentity owner,ActionReceipt receipt,
            ContinuityBatchJournal.ReboundTransport transport,Instant deadline)throws IOException {
        Objects.requireNonNull(owner);Objects.requireNonNull(receipt);Objects.requireNonNull(transport);Objects.requireNonNull(deadline);
        requireTransportedNaturalParent(owner,receipt,transport);
        try {
            return core.withBorrowed(()->{
                var same=core.activeBorrowedSession();core.writer().requireSession(same);
                var root=core.sessionAccess().current();
                StrictJson.require(root.ownedBy(core)&&root.hasInstalledHost()&&!root.isRetired()&&root.identity().equals(owner)
                        &&root.writer()==core.writer()&&root.archive()==core.archive(),
                        "transported continuation requires the actual admitted new transport Root and original physical Game");
                root.batchJournal().requireHistoricalTransport(same,transport);
                var installed=catalogs.requireCurrentCatalog(root);var context=installed.context();
                StrictJson.require(context.adopted()==root.driver()&&context.writer()==root.writer()&&context.archive()==root.archive()
                        &&context.borrowedSession()==same&&context.source().equals(receipt.command().source()),
                        "transported continuation catalog, installed software source or current Driver differs");
                var lifecycle=installed.remainingDomains().lifecycle();lifecycle.requireContext(context);
                var current=lifecycle.admittedTransportedCurrent(same,receipt,transport,deadline)
                        .orElseThrow(()->new IOException("actual fresh transported-current NS/M7 source is unavailable; no exact-post fallback"));
                var admitted=root.batchJournal().admitCurrentEpisode(same,current);
                core.requireCurrentForAccess(same,root);
                StrictJson.require(admitted.owner().equals(owner)&&!root.isRetired()
                        &&admitted.proof().frame().machineId().equals(owner.machineId())&&admitted.proof().frame().game().equals(owner.game()),
                        "transported continuation changed its actual Root or physical owner in the original writer transaction");
                return admitted;
            });
        }catch(InterruptedException interrupted){
            Thread.currentThread().interrupt();var failure=new InterruptedIOException("actual transported same-Game continuation interrupted");
            failure.initCause(interrupted);throw failure;
        }
    }
    /** Shape consistency only. Actual Journal, NS source and M7 current revalidation are required by the route above. */
    static void requireTransportedNaturalParent(SessionIdentity owner,ActionReceipt receipt,ContinuityBatchJournal.ReboundTransport transport) {
        StrictJson.require(owner.equals(transport.owner())&&owner.machineId().equals(receipt.command().origin().machineId())
                &&owner.game().equals(receipt.command().origin().game())
                &&java.util.Arrays.equals(ActionCodec.encodeCommand(transport.parent()),ActionCodec.encodeCommand(receipt.command())),
                "transported natural parent changed the exact historical command or actual same-Game owner");
        var settlement=receipt.state() instanceof ActionState.Settled settled?settled.settlement()
                :receipt.state() instanceof ActionState.CompositeSettled settled?settled.settlement():null;
        StrictJson.require(settlement instanceof ActionState.LifecycleApplied applied
                &&applied.proof().kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR,
                "UNKNOWN or another lifecycle cannot invoke transported-current final admission");
    }

    /** Shape rejection is early only; the live path also requires the private canonical lifecycle issuer above. */
    static void requireNaturalParent(SessionIdentity owner,ActionReceipt receipt) {
        Objects.requireNonNull(owner);Objects.requireNonNull(receipt);var command=receipt.command();
        StrictJson.require(command.origin().machineId().equals(owner.machineId())&&command.origin().game().equals(owner.game())
                &&command.sessionId().equals(owner.sessionId()),"natural parent crossed physical Game/session owner");
        var settlement=receipt.state() instanceof ActionState.Settled settled?settled.settlement()
                :receipt.state() instanceof ActionState.CompositeSettled settled?settled.settlement():null;
        StrictJson.require(settlement instanceof ActionState.LifecycleApplied applied
                &&applied.proof().kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR,
                "UNKNOWN, ordinary/no-op, DEATH and NEXT receipts cannot invoke same-Game continuation");
    }
}
