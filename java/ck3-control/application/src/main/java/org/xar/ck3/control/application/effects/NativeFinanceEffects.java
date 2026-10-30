package org.xar.ck3.control.application.effects;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.finance.factiongift.FactionGiftChoice;
import org.xar.ck3.control.finance.factiongift.FactionGiftPolicy;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingCodec;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingReducer;
import java.util.function.Supplier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;

/** Native hire employment and exact same-process gift material. A submit ACK proves neither effect. */
public final class NativeFinanceEffects implements NativeEffectRegistry.Observer {
    public static final String HIRE_SCHEMA="xar.java.mercenary-employment-material/v1";
    public static final String GIFT_SCHEMA="xar.java.faction-gift-material/v1";
    private static final BigInteger COMPANY_SENTINEL=new BigInteger("4294967295");
    private static final String HIRE_REJECTION="original native hire rejected without command submission";
    private final NativeEffectSnapshots snapshots;
    private final PlanningReadPort reads;
    private final FinanceReadContracts definitions;
    private final FinanceEvidenceArchive quoteEvidence;
    private final Supplier<Session> borrowed;
    private final NativeEffectEvidence.FrameLoader frames;
    public NativeFinanceEffects(NativeEffectSnapshots snapshots,PlanningReadPort reads,FinanceReadContracts definitions,FinanceEvidenceArchive quoteEvidence,Supplier<Session> borrowed,NativeEffectEvidence.FrameLoader frames) {
        this.snapshots=Objects.requireNonNull(snapshots);this.reads=Objects.requireNonNull(reads);this.definitions=Objects.requireNonNull(definitions);
        this.quoteEvidence=Objects.requireNonNull(quoteEvidence);
        this.borrowed=Objects.requireNonNull(borrowed);
        this.frames=Objects.requireNonNull(frames);
    }
    public static Optional<ExpectedPostcondition> expected(OperationKey operation,PlanningRequest request,Obj arguments) {
        if(operation.equals(OrdinaryFinancePolicies.MERCENARY)||operation.equals(OrdinaryFinancePolicies.GIFT))FinanceEvidenceArchive.reference(arguments);
        if(operation.equals(OrdinaryFinancePolicies.MERCENARY))
            return Optional.of(new ExpectedPostcondition(1,request.before(),request.source(),HIRE_SCHEMA,
                    hireValues(company(arguments),request.before().frame().identity().player())));
        if(operation.equals(OrdinaryFinancePolicies.GIFT)) {
            FactionGiftChoice.Selected choice=giftChoice(arguments);
            giftBaseline(arguments);
            require(choice.playerCharacterId().equals(request.before().frame().identity().player())
                    &&choice.nativeSnapshotRevision().equals(request.before().frame().identity().nativeRevision())
                    &&choice.dateRaw().equals(request.before().frame().identity().dateRaw()),"gift expected source drift");
            return Optional.of(new ExpectedPostcondition(1,request.before(),request.source(),GIFT_SCHEMA,giftValues(choice)));
        }
        return Optional.empty();
    }
    /** Called after the original writer-lock policy revalidation. All native wire names come from the original producer. */
    public static NativeRequest prepare(ActionCommand command,String requestId) {
        StrictJson.text(requestId);
        FinanceEvidenceArchive.reference(command.arguments());
        var frame=command.before().frame().identity();
        if(command.operation().equals(OrdinaryFinancePolicies.MERCENARY))
            return new NativeRequest(command.operation().value(),Optional.of("game.command.hire-mercenary-v1"),
                    new RawJson(encode(obj("company_id",new IntegerValue(company(command.arguments()))))));
        require(command.operation().equals(OrdinaryFinancePolicies.GIFT),"unowned finance action");
        FactionGiftChoice.Selected choice=giftChoice(command.arguments());
        require(choice.playerCharacterId().equals(frame.player())&&choice.nativeSnapshotRevision().equals(frame.nativeRevision())
                &&choice.dateRaw().equals(frame.dateRaw()),"gift native preparation source drift");
        GiftPendingModel.Baseline baseline=giftBaseline(command.arguments());
        BigInteger minimum=integer(command.arguments().get("minimum_gold_reserve_raw"),"minimum reserve");
        require(minimum.signum()>=0&&baseline.playerGoldRaw().subtract(baseline.goldCostRaw()).compareTo(minimum)>=0,
                "original gift reserve is not retained");
        Obj args=obj("expected_date_raw",new IntegerValue(frame.dateRaw()),
                "expected_player_character_id",new IntegerValue(GiftPendingModel.rawCharacterIdFromPublic(choice.playerCharacterId())),
                "expected_native_revision",new IntegerValue(choice.nativeSnapshotRevision()),
                "source_faction_id",new IntegerValue(choice.sourceFactionId()),"recipient_character_id",new IntegerValue(GiftPendingModel.rawCharacterIdFromPublic(choice.recipientCharacterId())),
                "membership_role",new Text(choice.membershipRole().wire()),"definition_stable_hash",new IntegerValue(choice.definitionStableHash()),
                "gold_cost_raw",new IntegerValue(choice.goldCostRaw()),"opinion_delta",new IntegerValue(choice.opinionDelta()),
                "minimum_gold_reserve_raw",new IntegerValue(minimum));
        return new NativeRequest(command.operation().value(),Optional.empty(),new RawJson(encode(args)));
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
        require(dispatch.requestId().equals(attempt.requestId()),"finance action ACK identity drift");
        quoteEvidence.verify(command);
        if(command.operation().equals(OrdinaryFinancePolicies.MERCENARY)&&dispatch instanceof NativeActionPort.AckReceived ack) {
            var rejected=snapshots.withArchive(original->{
                var archive=original.withSession(Objects.requireNonNull(borrowed.get(),"actual held writer Session required"));
                Complete before=RootGuardEvidence.loadFrame(attempt.guard(),archive,frames);
                if(!HireMercenaryAck.decode(command,attempt,ack,before).knownRejectedWithoutSubmission())return Optional.<NativeEffectRegistry.Projected>empty();
                ExactRef evidence=archive.referenceOf(dispatch);
                require(dispatch.equals(archive.load(evidence)),"original rejected hire ACK archive readback differs");
                return Optional.of(new NativeEffectRegistry.Projected(new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),HIRE_REJECTION,evidence)),Optional.empty()));
            });
            if(rejected.isPresent())return rejected.orElseThrow();
        }
        var pair=snapshots.read(command,attempt);Complete after=pair.after();
        FinanceReadContracts.Query query=query(command.operation());
        Optional<ReconciliationIdentity> reconciliation=Optional.empty();
        if(command.operation().equals(OrdinaryFinancePolicies.MERCENARY)&&ActionReconciliationScope.activeFor(command)) {
            try { reconciliation=Optional.of(ActionReconciliationScope.requireIdentity(command,attempt)); }
            catch(java.io.IOException failure) { throw new java.io.UncheckedIOException("actual mercenary reconciliation scope unavailable",failure); }
        }
        ReadContract<FinanceReadContracts.Packet> contract=reconciliation.isPresent()?definitions.mercenaryEmployerContract():definitions.contract(query);
        var deadline=ActionObservationWindow.deadline(command);
        var request=reconciliation.isPresent()?PlanningReadRequest.newReconciliation(reconciliation.orElseThrow(),query.operation(),new Obj(java.util.Map.of()),deadline)
                :new PlanningReadRequest(after.identity(),after.source(),after.sessionId(),query.operation(),new Obj(java.util.Map.of()),deadline);
        PlanningReadResult<FinanceReadContracts.Packet> observed=reads.read(Objects.requireNonNull(borrowed.get(),"actual held writer Session required"),contract,request);
        if(!(observed instanceof PlanningReadResult.Known<FinanceReadContracts.Packet> known))
            return NativeEffectRegistry.Projected.pending("independent finance material read unavailable; original command is not replayed",List.of(after.originalEvidence()));
        var projected=project(command,attempt,pair,known.receipt(),known.value());
        if(!(projected.result() instanceof ActionPorts.EffectObserved))return projected;
        ExactRef basis=snapshots.evidence(command,attempt,pair,List.of(known.receipt()),projected.compatibleResult().orElseThrow());
        return NativeEffectSnapshots.withEvidence(projected,List.of(basis));
    }
    /** Pure owning material replay shared by live observation and archived verification.
     * This DATA projection grants no quote, Native permission, current writer or Root qualification. */
    public static NativeEffectRegistry.Projected project(ActionCommand command,ActionState.Attempt attempt,
            NativeEffectSnapshots.Pair pair,PlanningReadReceipt read,FinanceReadContracts.Packet packet) {
        Complete after=pair.after();
        NativeEffectSnapshots.requireAfterRead(command,attempt,after,read,query(command.operation()).operation());
        require(packet.receipt().equals(read),"finance typed material differs from original read");
        if(command.operation().equals(OrdinaryFinancePolicies.MERCENARY)) {
            NativeMercenaryMarket.Observation market=NativeMercenaryMarket.decode(packet,after.identity(),after.source(),after.sessionId(),after.semantic());
            BigInteger selected=company(command.arguments()),actor=command.before().frame().identity().player();
            var matches=market.companies().stream().filter(row->row.id().equals(selected)).toList();
            require(matches.size()<=1,"duplicate native company full identity");
            BigInteger preEpoch=integer(command.arguments().get("pre_capture_epoch"),"pre capture epoch");
            if(!market.available()||market.captureEpoch().compareTo(preEpoch)<=0||matches.isEmpty()
                    ||!matches.getFirst().employedBy(org.xar.ck3.control.contracts.NativeCharacterId.of(actor)))
                return NativeEffectRegistry.Projected.pending("fresh native collection does not yet prove selected company employment",List.of(after.originalEvidence()));
            Obj result=obj("schema",new Text(HIRE_SCHEMA),"status",new Text("employment_observed"),
                    "action_request_id",new Text(attempt.requestId()),"company_id",new IntegerValue(selected),
                    "employer_character_id",new IntegerValue(actor),"capture_epoch",new IntegerValue(market.captureEpoch()),
                    "source_frame",command.arguments().get("source_frame"),"observed_source_frame",frame(after),
                    "pre_capture_epoch",new IntegerValue(preEpoch),"pre_player_army_ids",command.arguments().get("pre_player_army_ids"),
                    "decision",command.arguments().get("decision"),"native_company",matches.getFirst().original(),
                    "employment_verified",new Bool(true),"payment_verified",new Bool(false),"army_creation_verified",new Bool(false),
                    "company_to_new_army_binding_verified",new Bool(false));
            return NativeEffectSnapshots.observed(command,attempt,after,HIRE_SCHEMA,hireValues(selected,actor),read.requestId(),
                    new RawJson(encode(result)),List.of());
        }
        Obj result=packet.result();
        require(new Text("applied").equals(result.get("status"))&&new Bool(true).equals(result.get("private_build"))
                &&new Bool(false).equals(result.get("advertised")),"gift receipt route has not proved material application");
        var receipt=GiftPendingCodec.decodeReceipt(encode(object(result.get("receipt"),"actual independent gift receipt")));
        var choice=giftChoice(command.arguments());
        GiftPendingReducer.verifyReceipt(giftBaseline(command.arguments()),attempt.requestId(),receipt);
        require(receipt.playerCharacterId().equals(GiftPendingModel.rawCharacterIdFromPublic(after.identity().frame().identity().player()))
                &&receipt.postObservedDateRaw().equals(after.identity().frame().identity().dateRaw())
                &&receipt.postNativeSnapshotRevision().compareTo(after.identity().frame().identity().nativeRevision())<=0,
                "gift material receipt belongs to another current actor/date/native frame");
        Obj wallet=object(after.semantic().get("played_character_gold"),"actual post gift wallet");
        require(new IntegerValue(BigInteger.valueOf(100000)).equals(wallet.get("scale"))
                &&new IntegerValue(receipt.postPlayerGoldRaw()).equals(wallet.get("raw")),"gift independent wallet differs from material receipt");
        Obj compatible=result.with("postcondition_verified",new Bool(true)).with("source_frame",frame(after));
        return NativeEffectSnapshots.observed(command,attempt,after,GIFT_SCHEMA,giftValues(choice),read.requestId(),
                new RawJson(encode(compatible)),List.of());
    }
    public NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation,ExactRef source,NativeEffectEvidence.FrameLoader frames) {
        FinanceReadContracts.Query query=query(operation);
        return new NativeRecordedEvidenceVerifier.Binding(operation,source,(head,receipt,archive)->{
            quoteEvidence.verify(receipt.command(),archive);
            if(operation.equals(OrdinaryFinancePolicies.MERCENARY)&&receipt.state() instanceof ActionState.Settled terminal&&terminal.settlement() instanceof ActionState.Rejected rejected) {
                require(terminal.dispatch() instanceof NativeActionPort.AckReceived,"native hire rejection requires its original typed ACK");
                var ack=(NativeActionPort.AckReceived)terminal.dispatch();Complete before=RootGuardEvidence.loadFrame(terminal.attempt().guard(),archive,frames);
                require(HireMercenaryAck.decode(receipt.command(),terminal.attempt(),ack,before).knownRejectedWithoutSubmission()
                        &&rejected.requestId().equals(terminal.attempt().requestId())&&rejected.reason().equals(HIRE_REJECTION)
                        &&rejected.originalEvidence().equals(archive.referenceOf(ack))&&ack.equals(archive.load(rejected.originalEvidence())),"native hire terminal rejection differs from actual original no-submit ACK");return;
            }
            var original=NativeEffectEvidence.load(receipt,archive,frames);var settled=(ActionState.Settled)receipt.state();
            require(original.independentReads().size()==1,"finance material has exactly its original independent native read");
            PlanningReadReceipt read=original.independentReads().getFirst();
            var replayed=project(receipt.command(),settled.attempt(),original.frames(),read,definitions.decodeOriginal(query,read,original.frames().after().semantic()));
            replayed=NativeEffectSnapshots.withEvidence(replayed,((ActionState.Applied)settled.settlement()).observation().supportingEvidence());
            NativeEffectEvidence.requireSame(settled.settlement(),replayed,original.compatibleResult());
        });
    }
    /** Pure binding of this read to its retained UNKNOWN hire. Descriptor construction never grants Root authority. */
    public static void requireCanonicalMercenaryReconciliation(ActionReceipt original,ActionState.Attempt attempt,
            ReconciliationIdentity identity,ReadContract<?> actual,PlanningReadRequest request) {
        FinanceReadContracts.requireMercenaryEmployerProfile(actual);
        require(original.state() instanceof ActionState.Unknown unknown&&unknown.attempt().filter(attempt::equals).isPresent()
                &&original.command().origin() instanceof CommandOrigin.Gameplay
                &&original.bodySha256().equals(ActionCodec.bodySha256(original.command())),
                "mercenary employer read requires the exact retained UNKNOWN gameplay Attempt");
        var command=original.command();BigInteger selected=company(command.arguments());
        require(command.operation().equals(OrdinaryFinancePolicies.MERCENARY)
                &&command.expected().equals(new ExpectedPostcondition(1,command.before(),command.source(),HIRE_SCHEMA,
                    hireValues(selected,command.before().frame().identity().player()))),
                "mercenary employer read changed its original selected company or employer-only expected profile");
        var rebound=identity.driverRelation()==ReconciliationIdentity.DriverRelation.EXACT
                ?ReconciliationIdentity.fromCanonical(original,identity.factual(),identity.source(),identity.sessionId(),identity.connectionGeneration(),
                    identity.pending().originalReceipt(),identity.pending().originalBeforeDriver(),identity.evidence(),identity.observedAt())
                :ReconciliationIdentity.fromCanonicalHistoryAppend(original,identity.factual(),identity.source(),identity.sessionId(),identity.connectionGeneration(),
                    identity.pending().originalReceipt(),identity.pending().originalBeforeDriver(),identity.evidence(),identity.observedAt(),identity.historyPoint().orElseThrow());
        require(rebound.equals(identity)&&request.origin() instanceof CommandOrigin.Reconciliation
                &&request.origin().requireReconciliation().sameGuardFrame(identity)
                &&FinanceReadContracts.mercenaryFrame(request).equals(identity.factual())
                &&request.source().equals(identity.source())&&request.sessionId().equals(identity.sessionId()),
                "mercenary employer read crossed its actual original pending/factual source binding");
        var prepared=attempt.preparedRequest();
        require(prepared.step().equals(OrdinaryFinancePolicies.MERCENARY.value())
                &&prepared.requiredCapability().filter("game.command.hire-mercenary-v1"::equals).isPresent(),
                "mercenary original prepared request changed its operation/capability");
        var fields=StrictJson.object(StrictJson.parse(prepared.additionalFields().bytes()),java.util.Set.of("company_id"));
        require(StrictJson.integer(fields.get("company_id"),0,0xffff_fffeL)==selected.longValueExact(),
                "mercenary original prepared full company identity changed");
    }
    private static FinanceReadContracts.Query query(OperationKey operation) {
        if(operation.equals(OrdinaryFinancePolicies.MERCENARY))return FinanceReadContracts.Query.MERCENARIES;
        require(operation.equals(OrdinaryFinancePolicies.GIFT),"unowned finance material operation");
        return FinanceReadContracts.Query.FACTION_GIFT_RECEIPT;
    }
    public static BigInteger company(Obj arguments) {
        BigInteger value=integer(arguments.get("company_id"),"selected company");
        require(value.signum()>=0&&value.compareTo(COMPANY_SENTINEL)<0,"actual full CompanyID; native sentinel refused");
        return value;
    }
    private static FactionGiftChoice.Selected giftChoice(Obj arguments) {
        FactionGiftChoice choice=FactionGiftPolicy.decodeChoice(encode(object(arguments.get("choice"),"actual gift choice")));
        require(choice instanceof FactionGiftChoice.Selected,"gift choice is not selected");
        return (FactionGiftChoice.Selected)choice;
    }
    public static GiftPendingModel.Baseline giftBaseline(Obj arguments) {
        var selected=giftChoice(arguments);Obj candidate=object(arguments.get("candidate"),"actual gift candidate");
        Obj observation=object(candidate.get("observation"),"native original gift observation");
        Obj preview=object(observation.get("gift_preview"),"native original gift preview");
        require(new Bool(false).equals(observation.get("gift_opinion_present"))
                &&new Bool(true).equals(observation.get("source_faction_targeting_player")),"gift original baseline source flags differ");
        var baseline=new GiftPendingModel.Baseline(integer(observation.get("queried_source_faction_id"),"faction"),
                integer(observation.get("recipient_character_id"),"recipient"),integer(observation.get("snapshot_revision"),"public pre revision"),
                integer(observation.get("native_snapshot_revision"),"native pre revision"),integer(observation.get("observed_date_raw"),"pre date"),
                integer(observation.get("player_character_id"),"player"),integer(observation.get("player_gold_raw"),"pre wallet"),
                integer(observation.get("recipient_opinion_of_player"),"pre opinion"),integer(observation.get("source_faction_power_raw"),"pre power"),
                integer(observation.get("source_faction_discontent_raw"),"pre discontent"),
                array(observation.get("source_faction_member_character_ids"),"actual members").stream().map(v->integer(v,"member")).toList(),
                integer(preview.get("gold_cost_raw"),"quoted gift gold"),integer(preview.get("opinion_delta"),"quoted opinion delta"));
        require(baseline.sourceFactionId().equals(selected.sourceFactionId())&&baseline.recipientCharacterId().equals(GiftPendingModel.rawCharacterIdFromPublic(selected.recipientCharacterId()))
                &&baseline.playerCharacterId().equals(GiftPendingModel.rawCharacterIdFromPublic(selected.playerCharacterId()))&&baseline.nativeSnapshotRevision().equals(selected.nativeSnapshotRevision())
                &&baseline.dateRaw().equals(selected.dateRaw())&&baseline.goldCostRaw().equals(selected.goldCostRaw())
                &&baseline.opinionDelta().equals(selected.opinionDelta()),"selected gift differs from actual original baseline");
        return baseline;
    }
    private static List<ExpectedValue> hireValues(BigInteger company,BigInteger actor) {
        return List.of(new ExpectedInteger(new FieldKey("company_id"),company),new ExpectedInteger(new FieldKey("actor_id"),actor),
                new ExpectedText(new FieldKey("status"),"employment_observed"));
    }
    private static List<ExpectedValue> giftValues(FactionGiftChoice.Selected choice) {
        return List.of(new ExpectedInteger(new FieldKey("source_faction_id"),choice.sourceFactionId()),
                new ExpectedInteger(new FieldKey("recipient_character_id"),choice.recipientCharacterId()),
                new ExpectedInteger(new FieldKey("actor_id"),choice.playerCharacterId()),new ExpectedText(new FieldKey("status"),"applied"));
    }
    private static Obj frame(Complete after) {
        var f=after.identity().frame();return obj("played_character_id",new IntegerValue(f.identity().player()),
                "native_revision",new IntegerValue(f.identity().nativeRevision()),"date_raw",new IntegerValue(f.identity().dateRaw()),
                "snapshot_id",new Text(f.snapshotId()),"revision",new IntegerValue(f.revision()),"episode_run_id",new Text(f.episodeRunId()));
    }
}

