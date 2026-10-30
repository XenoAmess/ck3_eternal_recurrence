package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Function;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertsBoundary;
import org.xar.ck3.control.wave2.finance.giftoutcome.ExistingGiftOutcomeAdapter;
import org.xar.ck3.control.wave2.finance.giftoutcome.GiftOutcomeCodec;
import org.xar.ck3.control.wave2.finance.giftoutcome.GiftOutcomeModel;

/** Recomputable logical observation DATA. Archive, installed-source and writer authority remain with the sole publisher. */
public final class GiftResolvedEvidence {
    public static final OperationKey OPERATION=new OperationKey(GiftOutcomeModel.STEP);
    private GiftResolvedEvidence() { }

    public record Inputs(Complete frame,DriverStateSnapshot.Complete driver,PlanningReadReceipt pair,
                         Optional<PlanningReadReceipt> alert,String requestId) {
        public Inputs {
            Objects.requireNonNull(frame);Objects.requireNonNull(driver);Objects.requireNonNull(pair);
            Objects.requireNonNull(alert);StrictJson.text(requestId);
            require(frame.identity().game().pid()==driver.session().bridgePid()
                    &&frame.identity().frame().episodeRunId().equals(driver.session().episodeRunId())
                    &&frame.identity().frame().identity().player().equals(driver.session().actorId()),
                    "resolved Gift actual frame differs from the complete original Driver owner");
            requireReadFrame(frame,pair,GiftColdReadService.OPERATION);
            alert.ifPresent(read->requireReadFrame(frame,read,FinanceReadContracts.Query.FACTION_ALERTS.operation()));
            var snapshot=GiftOutcomeCodec.snapshot(DriverJson.encode(frame.semantic()));
            var proposal=frame.identity().frame();var nativeFrame=proposal.identity();
            require(snapshot.snapshotId().filter(proposal.snapshotId()::equals).isPresent()
                    &&snapshot.revision().filter(proposal.revision()::equals).isPresent()
                    &&snapshot.nativeRevision().filter(nativeFrame.nativeRevision()::equals).isPresent()
                    &&snapshot.dateRaw().filter(nativeFrame.dateRaw()::equals).isPresent()
                    &&snapshot.actorId().filter(nativeFrame.player()::equals).isPresent()
                    &&snapshot.episodeRunId().filter(proposal.episodeRunId()::equals).isPresent(),
                    "resolved Gift original SEM differs from the exact query frame");
        }
    }
    /** Only the owning pure query's Observed branch can mint this value; it still carries no live authority. */
    public static final class Observed {
        private final Inputs originals;private final RawJson result;
        private Observed(Inputs originals,RawJson result) {this.originals=originals;this.result=result;}
        public Inputs originals() {return originals;}
        public RawJson result() {return result;}
        public OperationKey operation() {return OPERATION;}
    }

    private static void requireReadFrame(Complete actual,PlanningReadReceipt read,OperationKey operation) {
        var old=read.request().before();var current=actual.identity();
        // DATA compatibility only. The sole publisher MUST prove complete native-byte/SEM equality and
        // the actual archived receipt's READ-only writer ancestry even when public revisions are equal.
        require(read.request().operation().equals(operation)&&old.game().equals(current.game())
                &&old.machineId().equals(current.machineId())&&old.observationVersion()==current.observationVersion()
                &&old.frame().snapshotId().equals(current.frame().snapshotId())
                &&old.frame().episodeRunId().equals(current.frame().episodeRunId())
                &&old.frame().identity().equals(current.frame().identity())
                &&old.frame().revision().compareTo(current.frame().revision())<=0
                &&read.request().source().equals(actual.source())&&read.request().sessionId().equals(actual.sessionId())
                &&read.before().binding().connectionGeneration().equals(actual.connectionGeneration()),
                "resolved Gift independent original read crossed operation/source/session/native query frame");
    }
    private static void replay(ReadContract<?> owner,PlanningReadReceipt read) {
        Objects.requireNonNull(owner);
        require(owner.hasPureReplay()&&owner.contractId().equals(read.contractId())
                &&owner.operation().equals(read.request().operation()),"actual installed owning pure read contract required");
        Objects.requireNonNull(owner.replay(read),"owning original parser returned no material");
    }

    /** Exact declared compatibility rows, exported individually so unrelated large Army history is never reserialized. */
    public static List<RawJson> relevantHistory(DriverStateSnapshot.Complete actual) {
        Objects.requireNonNull(actual);var rows=new ArrayList<RawJson>();
        for(var archived:actual.commandHistory()) {
            byte[] original=archived.originalRow().json();Obj row=DriverJson.object(original,DriverJson.MAX_NATIVE_BYTES);
            Value command=row.get("command");
            boolean relevant=new Text(GiftOutcomeModel.SUBMIT_STEP).equals(command)
                    ||new Text(GiftOutcomeModel.RECEIPT_STEP).equals(command)||new Text(GiftOutcomeModel.ALERT_STEP).equals(command);
            if(new Text("auto-turn").equals(command)&&row.get("result") instanceof Obj result
                    &&result.get("auto_turn") instanceof Obj turn) {
                relevant=new Text(GiftOutcomeModel.SUBMIT_STEP).equals(turn.get("selected_step"))
                        ||new Text(GiftOutcomeModel.RECEIPT_STEP).equals(turn.get("selected_step"));
            }
            if(relevant) {
                // The sole owning parser applies its existing one-row budget and declared JSON type domain.
                GiftOutcomeCodec.historyEntry(original);rows.add(new RawJson(original));
            }
        }
        return List.copyOf(rows);
    }

    /** Re-run the original producer, including independent selection of submit, receipt and current alert history. */
    public static Observed recompute(Inputs originals,ReadContract<?> installedPair,
                                     Optional<ReadContract<?>> installedAlert) {
        Objects.requireNonNull(originals);Objects.requireNonNull(installedAlert);
        replay(installedPair,originals.pair());
        require(installedAlert.isPresent()==originals.alert().isPresent(),"actual alert receipt and owning contract must be paired");
        originals.alert().ifPresent(read->replay(installedAlert.orElseThrow(),read));
        Obj pair=GiftColdReadService.requireHistoryResult(result(originals.pair()),originals.pair().request().arguments(),
                originals.frame().identity());
        Optional<byte[]> alert=originals.alert().map(read->FactionAlertsBoundary.normalizeCurrentNativeResult(
                encode(result(read)),new FactionAlertModel.ExpectedFrame(
                    originals.frame().identity().frame().identity().dateRaw().intValueExact(),
                    originals.frame().identity().frame().identity().nativeRevision(),Optional.of(FactionAlertModel.Build.CK3_12004)),
                encode(originals.frame().semantic().get("active_wars"))).projection().consumerProjectionJson());
        var driver=new ReplayDriver(originals,pair,alert);
        Obj request=OrdinaryFinanceCollector.obj("request_id",new Text(originals.requestId()),"expected_revision",
                new IntegerValue(originals.frame().identity().frame().revision()));
        RawJson result=new RawJson(new ExistingGiftOutcomeAdapter(driver).queryResolvedFactionGiftOutcome(encode(request)));
        require(driver.recorded.isPresent()&&java.util.Arrays.equals(driver.recorded.orElseThrow().bytes(),result.bytes()),
                "only the original resolved Gift Observed branch may produce history material");
        require(driver.usedPair&&driver.usedAlert==originals.alert().isPresent(),
                "resolved Gift supplied unused or missing independent read originals");
        return new Observed(originals,result);
    }
    private static Obj result(PlanningReadReceipt read) {
        require(read.original().originalResultToken().isPresent(),"actual native original result token required");
        return DriverJson.object(read.original().originalResultToken().orElseThrow().bytes(),RawJson.MAXIMUM_BYTES);
    }
    private static final class ReplayDriver implements ExistingGiftOutcomeAdapter.OwnedDriverPort {
        private final Inputs originals;private final Obj pair;private final Optional<byte[]> alert;
        private final List<RawJson> history;private Optional<RawJson> recorded=Optional.empty();
        private boolean usedPair,usedAlert;
        private ReplayDriver(Inputs originals,Obj pair,Optional<byte[]> alert) {
            this.originals=originals;this.pair=pair;this.alert=alert;this.history=relevantHistory(originals.driver());
        }
        @Override public byte[] takeInternalSemanticSnapshot() {return DriverJson.encode(originals.frame().semantic());}
        @Override public <T>T underOriginalHistoryLock(Function<Iterable<byte[]>,T> projection) {
            return projection.apply(history.stream().map(RawJson::bytes).toList());
        }
        @Override public ExistingGiftOutcomeAdapter.Invocation readOriginalIndependentPair(byte[] request) {
            require(!usedPair,"resolved Gift pure producer attempted a second independent pair read");usedPair=true;
            Obj expected=object(parse(request),"owning resolved Gift pair request");
            var nativeFrame=originals.frame().identity().frame().identity();
            require(new IntegerValue(nativeFrame.nativeRevision()).equals(expected.get("expected_revision"))
                    &&new IntegerValue(nativeFrame.dateRaw()).equals(expected.get("expected_date_raw"))
                    &&new IntegerValue(org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.rawCharacterIdFromPublic(nativeFrame.player()))
                        .equals(expected.get("expected_player_character_id"))
                    &&originals.pair().request().arguments().get("source_faction_id").equals(expected.get("source_faction_id"))
                    &&originals.pair().request().arguments().get("recipient_character_id").equals(expected.get("recipient_character_id")),
                    "actual independent pair differs from the original history-selected Gift");
            return new ExistingGiftOutcomeAdapter.Packet(encode(pair));
        }
        @Override public ExistingGiftOutcomeAdapter.Invocation queryOriginalPlayerFactionAlerts(BigInteger expectedRevision) {
            require(!usedAlert&&expectedRevision.equals(originals.frame().identity().frame().revision()),
                    "resolved Gift pure alert query repeated or changed public revision");usedAlert=true;
            require(alert.isPresent(),"resolved Gift requires its actual independently read current alert");
            return new ExistingGiftOutcomeAdapter.Packet(alert.orElseThrow());
        }
        @Override public void recordOriginalObservedCommand(String step,boolean ok,byte[] result) {
            require(GiftOutcomeModel.STEP.equals(step)&&ok&&recorded.isEmpty(),"one owning Observed result required");
            recorded=Optional.of(new RawJson(result));
        }
    }
}
