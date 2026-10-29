package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Function;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeFinanceEffects;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.application.planning.finance.publicgift.*;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicContract.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidateCodec;
import org.xar.ck3.control.wave2.finance.giftoutcome.ExistingGiftOutcomeAdapter;
import org.xar.ck3.control.wave2.finance.giftoutcome.GiftOutcomeModel;
import org.xar.ck3.control.wave2.finance.giftpending.*;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.*;

/** Per-current-Game public view over the installed finance graph. No second ledger, action writer or publisher. */
public final class FactionGiftPublicService implements FactionGiftPublicPort {
    private final RootRuntimeContext context;
    private final OrdinaryFinancePolicies policies;
    private final FinanceReadContracts definitions;
    private final GiftDomainSource gifts;
    private final GiftColdReadService coldReads;
    private final CanonicalGiftColdProvider cold;

    public FactionGiftPublicService(RootRuntimeContext context,OrdinaryFinancePolicies policies,
            FinanceReadContracts definitions,GiftDomainSource gifts,GiftColdReadService coldReads,
            CanonicalGiftColdProvider cold) {
        this.context=Objects.requireNonNull(context);this.policies=Objects.requireNonNull(policies);
        this.definitions=Objects.requireNonNull(definitions);this.gifts=Objects.requireNonNull(gifts);
        this.coldReads=Objects.requireNonNull(coldReads);this.cold=Objects.requireNonNull(cold);
    }

    @Override public RawJson invoke(Request request,Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(request);Objects.requireNonNull(deadline);
        RootApplicationSession root=currentRoot();
        RawJson nativeBusiness=switch(request) {
            case CandidateQuery selected -> candidate(root,selected,deadline);
            case Send selected -> send(root,selected,deadline);
            case ReceiptQuery selected -> receipt(root,selected,deadline);
            case ColdRecoveryQuery selected -> cold(root,selected,deadline);
            case ResolvedQuery selected -> resolved(root,selected,deadline);
        };
        return FactionGiftPublicCodec.businessPublic(request.method(),nativeBusiness);
    }

    private RootApplicationSession currentRoot()throws IOException,InterruptedException {
        RootApplicationSession root=context.core().sessionAccess().current();
        StrictJson.require(root.identity().game().equals(context.game().generation())
                &&root.identity().sessionId().equals(context.game().sessionId()),
                "public Gift service belongs to another actual Game/session");
        context.game().verify();return root;
    }
    private static void revision(PlanningRequest actual,BigInteger expected) {
        StrictJson.require(actual.before().frame().revision().equals(expected),"public Gift revision changed");
    }
    @FunctionalInterface private interface PlanningWork<T> {
        T read(Session same,PlanningRequest actual,Complete frame,DriverSnapshotFacts.Known known)throws IOException;
    }
    private <T>T planning(RootApplicationSession root,BigInteger expected,Instant deadline,PlanningWork<T> work)throws IOException {
        return context.withSession(same->{
            context.core().requireCurrentForAccess(same,root);
            T value=context.collector().withOwnedPlanning(same,root.identity(),deadline,(actual,lease)->{
                revision(actual,expected);return work.read(same,actual,lease.frame(),lease.driver());
            });
            context.core().requireCurrentForAccess(same,root);
            context.readHistoryPublisher().flushActualReads(same);
            return value;
        });
    }
    private FinanceReadContracts.Packet query(Session same,PlanningRequest actual,FinanceReadContracts.Query query)throws IOException {
        var result=definitions.read(same,query,context.finance().readPort(),actual);
        if(result instanceof PlanningReadResult.Known<FinanceReadContracts.Packet> known)return known.value();
        throw new IOException("actual public Gift read unavailable: "+((PlanningReadResult.Unavailable<FinanceReadContracts.Packet>)result).reason());
    }

    private RawJson candidate(RootApplicationSession root,CandidateQuery selected,Instant deadline)throws IOException {
        return planning(root,selected.expectedRevision(),deadline,(same,actual,frame,known)->{
            Obj supplied=DriverJson.object(FactionGiftPublicCodec.rootNative(selected.sameFrameRoot().original()).bytes(),RawJson.MAXIMUM_BYTES);
            Obj actualRoot=object(query(same,actual,FinanceReadContracts.Query.ROOT).result().get("campaign_root_context"),"actual campaign root");
            StrictJson.require(supplied.equals(actualRoot),"public Gift root differs from this installed same-frame original");
            var packet=query(same,actual,FinanceReadContracts.Query.FACTION_GIFT);
            return new RawJson(FactionCandidateCodec.encodeCandidateResult(FactionCandidateCodec.evaluatePrivateCandidate(
                    DriverJson.encode(frame.semantic()),FactionCandidateCodec.decodeRootProjection(encode(actualRoot)),
                    DriverJson.encode(packet.result()),selected.minimumGoldReserveRaw())));
        });
    }
    private RawJson send(RootApplicationSession root,Send selected,Instant deadline)throws IOException,InterruptedException {
        Obj candidate=DriverJson.object(FactionGiftPublicCodec.candidateNative(selected.candidate().original()).bytes(),RawJson.MAXIMUM_BYTES);
        Obj checkpoint=DriverJson.object(FactionGiftPublicCodec.checkpointNative(selected.checkpoint().original()).bytes(),RawJson.MAXIMUM_BYTES);
        return root.executePublicPlanningAction(deadline,(actual,frame,known,same)->{
            revision(actual,selected.expectedRevision());
            StrictJson.require(context.finance().policies()==policies,"public Gift lost its sole installed policy/quote producer");
            return policies.publicGift(same,actual,candidate,checkpoint,"public-faction-gift-"+java.util.UUID.randomUUID());
        },(actual,archive,same)->present(actual,archive,same));
    }
    private RawJson receipt(RootApplicationSession root,ReceiptQuery selected,Instant deadline)throws IOException,InterruptedException {
        PendingAction supplied=pending(FactionGiftPublicCodec.pendingNative(selected.pending().original()));
        String actionId=planning(root,selected.expectedRevision(),deadline,(same,actual,frame,known)->{
            StrictJson.require(CanonicalGiftColdProvider.sameProcess(supplied,context.game().generation()),"same-process receipt cannot cross the original process identity");
            return matchingAction(same,supplied).command().actionId();
        });
        ActionReceipt actual=root.reconcile(actionId);
        return context.withSession(same->present(actual,context.archive().withSession(same),same));
    }
    private RawJson cold(RootApplicationSession root,ColdRecoveryQuery selected,Instant deadline)throws IOException {
        PendingAction supplied=pending(FactionGiftPublicCodec.pendingNative(selected.pending().original()));
        return context.withSession(same->{
            context.core().requireCurrentForAccess(same,root);
            PlanningRequest original=context.collector().withOwnedPlanning(same,root.identity(),deadline,(actual,lease)->{
                revision(actual,selected.expectedRevision());
                StrictJson.require(!CanonicalGiftColdProvider.sameProcess(supplied,context.game().generation()),"cold Gift requires an actual different process birth");
                StrictJson.require(gifts.read(same).pending().filter(supplied::equals).isPresent(),"public cold request differs from the actual original pending body");
                return actual;
            });
            // DOMAIN_IMPORT takes place only after the physical planning freeze has ended.
            var outcome=gifts.afterPlanningCold(context,same,original,cold);
            context.readHistoryPublisher().flushActualReads(same);
            String status=outcome instanceof GiftDomainSource.ColdClassified?"cold_classified":
                    outcome instanceof GiftDomainSource.ColdNotRequired?"cold_not_required":"awaiting_canonical_cold_material";
            Obj result=obj("status",new Text(status),"unknown_replay_allowed",new Bool(false),
                    "pending_ledger",ledger(same));
            if(outcome instanceof GiftDomainSource.ColdReadOnly waiting)result=result.with("reason",new Text(waiting.reason()));
            return raw(result);
        });
    }
    private ActionReceipt matchingAction(Session same,PendingAction pending)throws IOException {
        Ledger ledger=gifts.read(same);
        StrictJson.require(ledger.pending().filter(pending::equals).isPresent()
                ||ledger.resolvedRequestOutcomes().containsKey(pending.requestId()),"public pending has no actual current or resolved original ledger identity");
        return context.core().actions().withFrozen(same,lease->{
            var matches=lease.snapshot().actions().stream().filter(receipt->receipt.command().operation().equals(OrdinaryFinancePolicies.GIFT)
                    &&RequestIds.forActionBody(receipt.bodySha256()).equals(pending.requestId())).toList();
            StrictJson.require(matches.size()==1,"one actual canonical Gift command must own this request");
            ActionReceipt actual=matches.getFirst();
            StrictJson.require(actual.command().before().frame().episodeRunId().equals(pending.episodeRunId())
                    &&NativeFinanceEffects.giftBaseline(actual.command().arguments()).equals(pending.baseline())
                    &&GiftProcessIdentity.actual(actual.command().before().game()).equals(pending.sourceProcess())
                    &&actual.command().arguments().get("checkpoint_sha256").equals(new Text(pending.checkpointSha256BeforeSubmit()))
                    &&actual.command().arguments().get("minimum_gold_reserve_raw").equals(new IntegerValue(pending.minimumGoldReserveRaw())),
                    "pending fields do not match the sole original submitted command");
            lease.assertCurrent();return actual;
        });
    }
    private RawJson present(ActionReceipt actual,ActionPorts.OutcomeArchive archive,Session same)throws IOException {
        return presentOriginal(actual,archive,context.frameLoader(),gifts.read(same));
    }
    /** The same actual archived settlement projection used by the installed service and full-writer regressions. */
    public static RawJson presentOriginal(ActionReceipt actual,ActionPorts.OutcomeArchive archive,
            NativeEffectEvidence.FrameLoader frames,Ledger actualLedger) {
        Objects.requireNonNull(actual);Objects.requireNonNull(archive);Objects.requireNonNull(frames);Objects.requireNonNull(actualLedger);
        StrictJson.require(actual.command().operation().equals(OrdinaryFinancePolicies.GIFT)
                &&java.util.Arrays.equals(ActionReceiptCodec.encodeReceipt(actual,archive),
                    ActionReceiptCodec.encodeReceipt(archive.loadReceipt(archive.receiptReferenceOf(actual)),archive)),
                "public Gift result must be the actual archived canonical receipt");
        Obj result;
        if(actual.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.Applied) {
            result=DriverJson.object(NativeEffectEvidence.load(actual,archive,frames).compatibleResult().bytes(),RawJson.MAXIMUM_BYTES);
        } else if(actual.ack().isPresent()&&actual.ack().orElseThrow().originalResultToken().isPresent()) {
            result=DriverJson.object(actual.ack().orElseThrow().originalResultToken().orElseThrow().bytes(),RawJson.MAXIMUM_BYTES);
        } else {
            result=obj("step",new Text(OrdinaryFinancePolicies.GIFT.value()),"status",new Text(actual.settled()?"rejected_before_dispatch":"unknown"),
                    "business_credit",new Bool(false));
        }
        return raw(result.with("request_id",new Text(RequestIds.forActionBody(actual.bodySha256()))).with("pending_ledger",
                object(parse(GiftPendingCodec.encodeLedger(actualLedger)),"actual Gift ledger")));
    }
    private Obj ledger(Session same)throws IOException {return object(parse(GiftPendingCodec.encodeLedger(gifts.read(same))),"actual Gift ledger");}
    private static PendingAction pending(RawJson original) {
        Obj body=obj("schema",new Text(GiftPendingModel.SCHEMA),"format_version",new IntegerValue(BigInteger.ONE),
                "pending",DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES),"resolved_request_outcomes",new Obj(java.util.Map.of()));
        return GiftPendingCodec.decodeLedger(encode(body)).pending().orElseThrow();
    }
    private static RawJson raw(Obj value){return new RawJson(DriverJson.encode(value));}

    private RawJson resolved(RootApplicationSession root,ResolvedQuery selected,Instant deadline)throws IOException {
        return context.withSession(same->{
            context.core().requireCurrentForAccess(same,root);
            record Captured(OutcomeDriver driver,RawJson result) { }
            Captured captured=context.collector().withOwnedPlanning(same,root.identity(),deadline,(actual,lease)->{
                revision(actual,selected.expectedRevision());
                var driver=new OutcomeDriver(same,actual,lease.frame(),lease.driver());
                RawJson result=new RawJson(new ExistingGiftOutcomeAdapter(driver).queryResolvedFactionGiftOutcome(encode(obj(
                        "request_id",new Text(selected.requestId()),"expected_revision",new IntegerValue(selected.expectedRevision())))));
                return new Captured(driver,result);
            });
            // Only the sole publisher mutates Driver history, outside the physical capture freeze.
            context.core().requireCurrentForAccess(same,root);
            RawJson actualResult=captured.driver().requireRecorded(captured.result());
            context.readHistoryPublisher().flushActualReads(same);
            return actualResult;
        });
    }
    private final class OutcomeDriver implements ExistingGiftOutcomeAdapter.OwnedDriverPort {
        private final Session same;private final PlanningRequest actual;private final Complete frame;
        private final DriverSnapshotFacts.Known known;
        private Optional<PlanningReadReceipt> pair=Optional.empty(),alert=Optional.empty();
        private Optional<RawJson> recorded=Optional.empty();
        private OutcomeDriver(Session same,PlanningRequest actual,Complete frame,DriverSnapshotFacts.Known known) {
            this.same=same;this.actual=actual;this.frame=frame;this.known=known;
        }
        @Override public byte[] takeInternalSemanticSnapshot() {
            try{return context.collector().current(same,actual.before(),actual.deadline(),lease->DriverJson.encode(lease.frame().semantic()));}
            catch(IOException unavailable){throw new java.io.UncheckedIOException(unavailable);}
        }
        @Override public <T>T underOriginalHistoryLock(Function<Iterable<byte[]>,T> projection) {
            var rows=new ArrayList<byte[]>();GiftResolvedEvidence.relevantHistory(known.driver()).forEach(row->rows.add(row.bytes()));
            return projection.apply(List.copyOf(rows));
        }
        @Override public ExistingGiftOutcomeAdapter.Invocation readOriginalIndependentPair(byte[] request) {
            try {
                Obj arguments=object(parse(request),"actual pair request");
                var query=new PlanningReadRequest(actual.before(),actual.source(),actual.sessionId(),GiftColdReadService.OPERATION,
                        obj("source_faction_id",arguments.get("source_faction_id"),"recipient_character_id",arguments.get("recipient_character_id")),actual.deadline());
                var value=context.reads().read(same,coldReads.contract(),query);
                if(value instanceof PlanningReadResult.Known<GiftColdReadService.Observation> observed) {
                    pair=Optional.of(observed.receipt());return new ExistingGiftOutcomeAdapter.Packet(encode(observed.value().originalResult()));
                }
                return new ExistingGiftOutcomeAdapter.Unavailable(ExistingGiftOutcomeAdapter.ReadFailure.BRIDGE_UNAVAILABLE,
                        ((PlanningReadResult.Unavailable<GiftColdReadService.Observation>)value).reason());
            }catch(IllegalArgumentException rejected){return new ExistingGiftOutcomeAdapter.Unavailable(ExistingGiftOutcomeAdapter.ReadFailure.BRIDGE_UNAVAILABLE,rejected.getMessage());}
        }
        @Override public ExistingGiftOutcomeAdapter.Invocation queryOriginalPlayerFactionAlerts(BigInteger expectedRevision) {
            try {
                StrictJson.require(expectedRevision.equals(actual.before().frame().revision()),"resolved alert expected revision changed");
                var packet=query(same,actual,FinanceReadContracts.Query.FACTION_ALERTS);alert=Optional.of(packet.receipt());
                return new ExistingGiftOutcomeAdapter.Packet(encode(packet.result()));
            }catch(IOException unavailable){return new ExistingGiftOutcomeAdapter.Unavailable(ExistingGiftOutcomeAdapter.ReadFailure.BRIDGE_UNAVAILABLE,unavailable.getMessage());}
        }
        @Override public void recordOriginalObservedCommand(String step,boolean ok,byte[] result) {
            StrictJson.require(ok&&GiftOutcomeModel.STEP.equals(step)&&recorded.isEmpty(),"one actual resolved Gift observation publication required");
            recorded=Optional.of(new RawJson(result));
        }
        private RawJson requireRecorded(RawJson result)throws IOException {
            if(recorded.isEmpty())return result; // The owning pure query records only its Observed branch.
            StrictJson.require(java.util.Arrays.equals(recorded.orElseThrow().bytes(),result.bytes()),"recorded resolved result differs from the actual query producer");
            var originals=new GiftResolvedEvidence.Inputs(frame,known.driver(),pair.orElseThrow(),alert,
                    text(DriverJson.object(result.bytes(),RawJson.MAXIMUM_BYTES).get("request_id"),"owning Gift outcome request"));
            return context.readHistoryPublisher().publishGiftResolved(same,known,originals,result);
        }
    }
}
