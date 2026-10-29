package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.governance.CrownRetryPublication;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual same-Core original receipt replay and independently current Driver/Native READ-only join. */
final class RootCrownActualMaterialPort implements CrownRetryPublication.MaterialPort {
    private final RootCrownRetryRuntime.Prepared owner;
    RootCrownActualMaterialPort(RootCrownRetryRuntime.Prepared owner) {this.owner=owner;}

    @Override public CrownRetryPublication.Material capture(WriterContracts.Head head,CrownRetryPublication.Input input,Instant callerDeadline)throws IOException {
        var installed=owner.active();var context=installed.context;var same=owner.session();
        context.requireCurrent(callerDeadline);
        StrictJson.require(head.digest().equals(same.head().digest()),"retry material must use its original actual writer head");
        var archive=context.archive().withSession(same);
        var crown=archive.loadRead(input.crownReceipt());var terms=archive.loadRead(input.finalTermsReceipt());
        var crownContract=installed.nativeGovernance.planningReads().crown();
        var termsProducer=installed.nativeGovernance.crownFinalTermsRead();
        StrictJson.require(context.readCatalog().containsIdentity(crownContract) && context.readCatalog().containsIdentity(termsProducer.contract())
                && crown.contractId().equals(crownContract.contractId()) && terms.contractId().equals(termsProducer.contract().contractId()),
                "retry material requires the identical actually installed native Crown/final-terms decoders");
        requireOriginal(same,archive,crown);requireOriginal(same,archive,terms);
        StrictJson.require(crown.request().source().equals(terms.request().source())
                && crown.request().sessionId().equals(terms.request().sessionId()) && crown.request().source().equals(input.source())
                && terms.after().binding().observed().equals(input.queryObserved()),"retry query originals crossed their exact source/session/query observation");
        CrownRetryPublication.requireQueryJoin(crown.after().binding().observed(),input.queryObserved());
        var actualCrown=OpportunityJson.encode(crownContract.decode(crown));var actualTerms=termsProducer.consumeTerms(terms).completeConsume().bytes();
        byte[] retainedCrown=archive.loadMaterial(input.crownReadback()).bytes(),retainedTerms=archive.loadMaterial(input.finalTermsConsume()).bytes();
        StrictJson.require(Arrays.equals(actualCrown,retainedCrown) && Arrays.equals(actualTerms,retainedTerms),
                "retry retained raw inputs differ from actual original receipt decoders");
        var query=RootGuardEvidence.loadFrame(terms.after().binding(),archive,context.frameLoader());
        var result=context.readiness().current(same,input.currentObserved(),callerDeadline,lease->{
            context.requireCurrent(lease.validUntil());
            StrictJson.require(lease.frame().source().equals(context.source()) && lease.frame().source().equals(input.source())
                    && lease.frame().identity().equals(input.currentObserved()) && lease.frame().sessionId().equals(terms.request().sessionId()),
                    "retry material did not independently read its exact current Native/full Driver frame");
            var lineage=context.readHistoryPublisher().requireReadOnlyExtension(same,terms.after().binding(),query,lease.driver());
            lineage=lineage.requireCurrent(same);
            StrictJson.require(lineage.queryObserved().identity().equals(input.queryObserved())
                    && lineage.currentObserved().identity().equals(lease.frame().identity())
                    && lineage.currentObserved().semantic().equals(lease.frame().semantic()),"retry query/current full observations have no actual canonical READ-only lineage");
            byte[] previous=context.archive().readArtifact(same,input.previousBody(),CrownRetryPublication.MAX_BODY_BYTES);
            return new CrownRetryPublication.Material(lease.frame().identity(),lease.frame().source(),previous,actualCrown,actualTerms);
        });
        StrictJson.require(head.digest().equals(same.head().digest()),"retry material capture must not change its original canonical head");return result;
    }
    private static void requireOriginal(ContinuityStorePort.Session same,ActionPorts.OutcomeArchive archive,PlanningReadReceipt receipt)throws IOException {
        StrictJson.require(receipt.request().origin() instanceof CommandOrigin.Gameplay && receipt.original().nativeOk()
                && receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"retry requires an actual unchanged living paused query receipt");
        for(var guard:List.of(receipt.before(),receipt.after())) {
            StrictJson.require(guard.paused() && guard.mapReady() && guard.playerAlive()
                    && guard.binding().observed().equals(receipt.request().before())
                    && guard.binding().source().equals(receipt.request().source())
                    && guard.binding().sessionId().equals(receipt.request().sessionId()),"retry original query crossed full source/frame/session or gameplay readiness");
            RootGuardEvidence.requireHistory(guard.binding(),archive,same);
        }
    }
    /** After its own canonical publication, private proof reuse checks the actual fresh frame and source, not a fictitious all-READ suffix. */
    @Override public void requireCurrent(WriterContracts.Head head,CrownRetryPublication.Input original,
            ObservationIdentity expected,G2Source source,Instant callerDeadline)throws IOException {
        var installed=owner.active();var context=installed.context;var same=owner.session();
        context.requireCurrent(callerDeadline);
        StrictJson.require(head.digest().equals(same.head().digest()),"retry proof requires the actual current canonical head");
        context.readiness().current(same,expected,callerDeadline,lease->{
            context.requireCurrent(lease.validUntil());
            StrictJson.require(lease.frame().identity().equals(expected) && lease.frame().source().equals(source)
                    && source.equals(context.source()) && expected.game().equals(context.game().generation())
                    && lease.frame().sessionId().equals(context.game().sessionId()),"retry proof current physical Native/Driver/source identity unavailable");
            return null;
        });
        StrictJson.require(head.digest().equals(same.head().digest()),"retry proof revalidation changed its current canonical head");
    }
}
