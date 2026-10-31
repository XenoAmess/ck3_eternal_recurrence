package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Strict canonical ACTION-history DATA. It cannot qualify an action, a current Native frame or a second writer. */
public final class DriverActionHistoryState {
    public static final String SCHEMA="xar.java.driver-action-history-publication/v1";
    private static final Set<String> FIELDS=Set.of("schema","evidence_id","source","predecessor_head_sha256","action_id","body_sha256",
            "action_sequence","before_version","after_version","episode_epoch","before_driver","after_driver","original_source","legacy_row");
    private DriverActionHistoryState() { }
    public record Publication(String evidenceId,ActionCommand command,String bodySha256,long actionSequence,String predecessor,
            long beforeVersion,long afterVersion,long episodeEpoch,ExactRef beforeDriver,ExactRef afterDriver,
            ExactRef originalSource,Optional<ExactRef> legacyRow) {
        public Publication {
            StrictJson.text(evidenceId);Objects.requireNonNull(command);digest(bodySha256);digest(predecessor);
            StrictJson.safe(actionSequence,1);StrictJson.safe(beforeVersion,0);StrictJson.safe(afterVersion,1);StrictJson.safe(episodeEpoch,0);
            StrictJson.require(afterVersion==Math.addExact(beforeVersion,1),"one full Driver version per actual ACTION publication required");
            Objects.requireNonNull(beforeDriver);Objects.requireNonNull(afterDriver);Objects.requireNonNull(originalSource);Objects.requireNonNull(legacyRow);
        }
        public ObjectNode details() {
            ObjectNode row=StrictJson.object();row.put("schema",SCHEMA);row.put("evidence_id",evidenceId);row.set("source",ProposalLifecycleCodec.source(command.source()));
            row.put("predecessor_head_sha256",predecessor);row.put("action_id",command.actionId());row.put("body_sha256",bodySha256);row.put("action_sequence",actionSequence);
            row.put("before_version",beforeVersion);row.put("after_version",afterVersion);row.put("episode_epoch",episodeEpoch);
            row.set("before_driver",beforeDriver.toJson());row.set("after_driver",afterDriver.toJson());row.set("original_source",originalSource.toJson());
            if(legacyRow.isPresent())row.set("legacy_row",legacyRow.orElseThrow().toJson());else row.putNull("legacy_row");return row;
        }
        public WriterContracts.Request request(List<ExactRef> actualEvidence) {
            return new WriterContracts.Request(WriterContracts.DRIVER_ACTION_HISTORY_KIND,StrictJson.canonical(details()),actualEvidence);
        }
    }
    public record CommittedCoverage(ExactRef canonicalEvent,Publication publication) {
        public CommittedCoverage {Objects.requireNonNull(canonicalEvent);Objects.requireNonNull(publication);}
        public ExactRef originalSource(){return publication.originalSource();}
        public Optional<ExactRef> legacyRow(){return publication.legacyRow();}
        public ExactRef beforeDriver(){return publication.beforeDriver();}
        public ExactRef afterDriver(){return publication.afterDriver();}
        public long afterVersion(){return publication.afterVersion();}
        public long episodeEpoch(){return publication.episodeEpoch();}
    }
    public static Publication decode(ObjectNode body,ActionReceipt actual) {
        ObjectNode row=StrictJson.object(body,FIELDS);
        StrictJson.require(StrictJson.text(row.get("schema")).equals(SCHEMA)
                &&StrictJson.text(row.get("action_id")).equals(actual.command().actionId())
                &&StrictJson.text(row.get("body_sha256")).equals(actual.bodySha256())
                &&StrictJson.integer(row.get("action_sequence"),1,StrictJson.MAX_SAFE_INTEGER)==actual.sequence()
                &&row.get("source").equals(ProposalLifecycleCodec.source(actual.command().source())),"canonical ACTION publication crossed its original command/source/sequence");
        return new Publication(StrictJson.text(row.get("evidence_id")),actual.command(),actual.bodySha256(),actual.sequence(),
                StrictJson.text(row.get("predecessor_head_sha256")),StrictJson.integer(row.get("before_version"),0,StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(row.get("after_version"),1,StrictJson.MAX_SAFE_INTEGER),StrictJson.integer(row.get("episode_epoch"),0,StrictJson.MAX_SAFE_INTEGER),
                ExactRef.fromJson(row.get("before_driver")),ExactRef.fromJson(row.get("after_driver")),ExactRef.fromJson(row.get("original_source")),
                row.get("legacy_row").isNull()?Optional.empty():Optional.of(ExactRef.fromJson(row.get("legacy_row"))));
    }
    public static ContinuityState reduce(ContinuityState before,WriterContracts.Request request) {
        StrictJson.require(request.kind().equals(WriterContracts.DRIVER_ACTION_HISTORY_KIND),"explicit ACTION publication kind required");
        ObjectNode next=before.toJson();next.set(WriterContracts.DRIVER_ACTION_HISTORY_FIELD,request.detailsObject());
        ContinuityState after=ContinuityState.fromJson(next,before.machineId());requireReduction(before,after,request,false);return after;
    }
    /** Pure envelope check, shared by original producer and canonical historical replay. */
    public static void requireReduction(ContinuityState before,ContinuityState after,WriterContracts.Request request,boolean sequenced) {
        StrictJson.require(request.kind().equals(WriterContracts.DRIVER_ACTION_HISTORY_KIND),"ACTION history cannot impersonate another canonical event");
        StrictJson.object(request.detailsObject(),FIELDS);
        WriterContracts.requireDriverActionHistoryReduction(before,after,request,sequenced);
    }
    /** Replays complete archived before/after Drivers and the unchanged original recording path, never Receipt-as-Driver. */
    public static void requireOriginal(Session same,Publication data,ActionReceipt actual,ActionPorts.OutcomeArchive originals) throws IOException {
        StrictJson.require(!(actual.command().expectation() instanceof org.xar.ck3.control.application.action.CommandExpectation.OperatorRebind),
                "operator identity receipt has no separate Driver ACTION publication or version increment");
        var source=DriverActionHistoryCodec.decode(material(data.originalSource(),originals));
        DriverActionHistoryCodec.requireCanonicalMembership(same,actual,source,originals);DriverActionHistoryCodec.requireSource(actual,source,originals);
        DriverStateSnapshot.Complete before=DriverStateSnapshot.decodeComplete(fullMaterial(data.beforeDriver(),originals).bytes());
        DriverStateSnapshot.Complete after=DriverStateSnapshot.decodeComplete(fullMaterial(data.afterDriver(),originals).bytes());
        StrictJson.require(actual.command().before().game().pid()==before.session().bridgePid()
                &&actual.command().before().frame().episodeRunId().equals(before.session().episodeRunId()),"ACTION full Driver crossed original Game/episode");
        if(source.material() instanceof DriverActionHistoryCodec.Legacy||source.material() instanceof DriverActionHistoryCodec.GiftLegacyPair) {
            ExactRef rowRef=data.legacyRow().orElseThrow(()->new IllegalArgumentException("legacy recording must retain its actual original row"));
            var row=DriverJson.object(material(rowRef,originals).bytes(),DriverJson.MAX_NATIVE_BYTES);DriverActionHistoryCodec.verifyLegacy(same,actual,row,originals);
            var embeddedSource = DriverActionHistoryCodec.decode(new RawJson(DriverJson.encode(row.get(DriverActionHistoryCodec.SOURCE_FIELD))));
            StrictJson.require(source.equals(embeddedSource), "legacy row changed its canonical original source");
            var history=new ArrayList<>(before.commandHistory());long index=Math.addExact(history.size(),1L);
            StrictJson.require(org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(row.get("index"),"index").longValueExact()==index,"ACTION legacy history index is not contiguous");
            StrictJson.require(row.equals(DriverActionHistoryCodec.legacyRow(index,actual,source,originals)),
                    "ACTION coverage must point to its original primary row, never a Gift receipt part");
            var actualRows=DriverActionHistoryCodec.legacyRows(index,actual,source,originals);
            for(int offset=0;offset<actualRows.size();offset++)history.add(new DriverStateSnapshot.HistoryEntry(Math.addExact(index,offset),
                    new DriverStateSnapshot.Value(DriverJson.encode(actualRows.get(offset)))));
            var expected=new DriverStateSnapshot.Complete(before.session(),history,before.lastCheckpoint(),before.rollbackWarFailure(),before.managedRestoreTransaction(),
                    before.successionExpectation(),before.successionLifecycle(),before.campaignGoal(),before.rollbackWarFailures());
            StrictJson.require(DriverJson.object(expected.encode(),DriverJson.MAX_NATIVE_BYTES)
                    .equals(DriverJson.object(after.encode(),DriverJson.MAX_NATIVE_BYTES)),"ACTION legacy publication changed a non-history full Driver slot");
        } else {
            StrictJson.require(data.legacyRow().isEmpty()&&Arrays.equals(before.encode(),after.encode()),"canonical-only interface cannot manufacture a legacy row or change business Driver fields");
            DriverActionHistoryCodec.verifyCanonicalOnly(same,actual,data.originalSource(),originals);
        }
        // Implementation producers remain archived DATA; business roles are verified by requireSource above.
    }
    /** Reads only actual retained canonical event pins. Archive directory contents grant no coverage. */
    public static Optional<CommittedCoverage> findCommittedCoverage(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive originals) throws IOException {
        var head=same.head();ContinuityActionJournal.requireHistoricalReceipt(head.state(),actual,originals);
        Optional<CommittedCoverage> found=Optional.empty();
        for(var pin:head.documents()) {
            String name=Path.of(pin.reference().path()).getFileName().toString();if(!name.matches("[0-9]{8,16}\\.json"))continue;
            ObjectNode event=ContinuityJson.parseObject(same.readPinned(pin,ContinuityJson.LEDGER_MAX_BYTES),ContinuityJson.LEDGER_MAX_BYTES);
            if(!event.path("kind").asText().equals(WriterContracts.DRIVER_ACTION_HISTORY_KIND))continue;
            ObjectNode details=StrictJson.object(event.get("details"),FIELDS);if(!StrictJson.text(details.get("action_id")).equals(actual.command().actionId()))continue;
            StrictJson.object(event,Set.of("sequence","at_utc","kind","details","identity","previous_sha256","after"));
            long sequence=StrictJson.integer(event.get("sequence"),1,StrictJson.MAX_SAFE_INTEGER);
            StrictJson.require(name.equals(String.format(java.util.Locale.ROOT,"%08d.json",sequence)),"canonical ACTION event path/sequence differs");
            var data=decode(details,actual);String predecessor=StrictJson.text(event.get("previous_sha256"));
            StrictJson.require(data.predecessor().equals(predecessor),"ACTION metadata changed its actual writer predecessor");
            ContinuityState before=same.requireHistoricalState(sequence-1,predecessor);
            ContinuityState after=ContinuityState.fromJson(event.get("after"),head.state().machineId());
            var request=data.request(List.of(data.beforeDriver(),data.afterDriver(),data.originalSource()));
            StrictJson.require(StrictJson.text(event.get("identity")).equals(request.identity()),"canonical ACTION event identity differs");
            requireReduction(before,after,request,true);same.requireHistoricalState(sequence,ContinuityJson.digest(after.toJson()));
            requireOriginal(same,data,actual,originals);StrictJson.require(found.isEmpty(),"same action has conflicting canonical history publications");
            found=Optional.of(new CommittedCoverage(pin.reference(),data));
        }
        StrictJson.require(same.head().digest().equals(head.digest()),"canonical ACTION recovery reader changed its actual writer head");return found;
    }
    private static RawJson fullMaterial(ExactRef ref,ActionPorts.OutcomeArchive originals) {
        RawJson raw=originals.loadFullMaterial(ref);StrictJson.require(raw.bytes().length==ref.bytes()&&DriverJson.sha256(raw.bytes()).equals(ref.sha256()),"canonical full Driver material changed");return raw;
    }
    private static RawJson material(ExactRef ref,ActionPorts.OutcomeArchive originals) {
        RawJson raw=originals.loadMaterial(ref);StrictJson.require(raw.bytes().length==ref.bytes()&&DriverJson.sha256(raw.bytes()).equals(ref.sha256()),"canonical ACTION original artifact changed");return raw;
    }
    private static void digest(String value){StrictJson.require(value!=null&&value.matches("[0-9a-f]{64}"),"exact canonical SHA required");}
}
