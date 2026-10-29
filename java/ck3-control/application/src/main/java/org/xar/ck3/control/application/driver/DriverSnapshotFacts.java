package org.xar.ck3.control.application.driver;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Facts from the actual sole producers, including full legacy history rather than a WAL tail. */
public final class DriverSnapshotFacts {
    private DriverSnapshotFacts() { }
    public static final String ORIGINAL_SCHEMA="xar.java-driver-known-original/v1";
    /** One original archive material, independent of the larger full-Driver checkpoint limit. */
    public static final int MAX_ORIGINAL_BYTES=DriverJson.MAX_NATIVE_BYTES;
    public record Stamp(long driverVersion, long episodeEpoch, GameGeneration game, String episodeRunId, String driverSha256) {
        public Stamp {
            StrictJson.safe(driverVersion,0); StrictJson.safe(episodeEpoch,0); Objects.requireNonNull(game); StrictJson.text(episodeRunId);
            StrictJson.require(driverSha256 != null && driverSha256.matches("[0-9a-f]{64}"), "complete Driver SHA required");
        }
    }
    public sealed interface CoverageSource permits LegacyHistoryRow, CanonicalOnly { }
    public record LegacyHistoryRow(long historyIndex,ExactRef originalRow) implements CoverageSource {
        public LegacyHistoryRow {StrictJson.safe(historyIndex,1);Objects.requireNonNull(originalRow);StrictJson.require(originalRow.bytes()>0,"original full compatible history row required");}
    }
    /** An interface that never recorded Python compatibility history keeps its actual canonical source instead. */
    public record CanonicalOnly(ExactRef originalSource) implements CoverageSource {
        public CanonicalOnly {Objects.requireNonNull(originalSource);StrictJson.require(originalSource.bytes()>0,"original canonical action source required");}
    }
    public record ActionRow(String actionId,String bodySha256,long durableSequence,CoverageSource coverageSource) {
        public ActionRow {
            StrictJson.text(actionId);StrictJson.safe(durableSequence,1);Objects.requireNonNull(coverageSource);
            StrictJson.require(bodySha256!=null&&bodySha256.matches("[0-9a-f]{64}"),"actual durable action binding required");
        }
        public ActionRow(String actionId,String bodySha256,long durableSequence,long historyIndex,ExactRef originalRow) {
            this(actionId,bodySha256,durableSequence,new LegacyHistoryRow(historyIndex,originalRow));
        }
        public long historyIndex() {
            if(coverageSource instanceof LegacyHistoryRow legacy)return legacy.historyIndex();
            throw new IllegalStateException("canonical-only action has no Python compatibility history ordinal");
        }
        public ExactRef originalResult() {
            if(coverageSource instanceof LegacyHistoryRow legacy)return legacy.originalRow();
            throw new IllegalStateException("canonical-only action has no Python compatibility history row");
        }
    }
    /** Optional loop evidence is auxiliary; these fields are not added to the original thirteen-field Driver wire. */
    public record LoopWitness(String batchId, long turn, long epoch, boolean dirty, long eligibleSinceSave,
            boolean quarantined, ExactRef originalFacts) {
        public LoopWitness { StrictJson.text(batchId); StrictJson.safe(turn,0); StrictJson.safe(epoch,0); StrictJson.safe(eligibleSinceSave,0); Objects.requireNonNull(originalFacts); }
    }
    public sealed interface State permits Known, Unavailable { }
    public record Known(DriverStateSnapshot.Complete driver, Stamp stamp, ExactRef originalHistoryBasis,
            List<ActionRow> actionRows, OpportunityJson.Obj auxiliary, Optional<LoopWitness> loop,
            Optional<DriverObservationFacts> observation) implements State {
        public Known {
            Objects.requireNonNull(driver); Objects.requireNonNull(stamp); Objects.requireNonNull(originalHistoryBasis);
            actionRows=List.copyOf(actionRows); Objects.requireNonNull(auxiliary); Objects.requireNonNull(loop); Objects.requireNonNull(observation);
            StrictJson.require(originalHistoryBasis.bytes()>0 && stamp.driverSha256().equals(DriverJson.sha256(driver.encode()))
                    && stamp.episodeRunId().equals(driver.session().episodeRunId()) && stamp.game().pid()==driver.session().bridgePid(),
                    "full Driver facts/stamp mismatch");
            java.util.Set<String> actions=new java.util.HashSet<>();
            for(ActionRow row:actionRows) {
                StrictJson.require(actions.add(row.actionId()),"unique actual action coverage required");
                if(row.coverageSource() instanceof LegacyHistoryRow legacy)
                    StrictJson.require(legacy.historyIndex()<=driver.commandHistory().size(),"original legacy history ordinal exceeds the complete Driver");
            }
            observation.ifPresent(value -> StrictJson.require(value.driverVersion()==stamp.driverVersion()
                    && value.episodeEpoch()==stamp.episodeEpoch()
                    && value.transport().game().equals(stamp.game())
                    && java.util.Arrays.equals(value.driver().encode(),driver.encode()),"semantic facts crossed Driver version"));
        }
    }
    public record Unavailable(List<String> reasons) implements State {
        public Unavailable { reasons=List.copyOf(reasons); StrictJson.require(!reasons.isEmpty(),"explicit missing full Driver facts required"); }
    }

    /** Complete immutable facts DATA. The observation manifest is replayed by its existing sole codec. */
    public static org.xar.ck3.control.application.action.RawJson encodeKnownOriginal(Known value) {
        Objects.requireNonNull(value);
        java.util.Map<String,OpportunityJson.Value> row=new java.util.LinkedHashMap<>();
        row.put("schema",text(ORIGINAL_SCHEMA));row.put("driver",DriverJson.object(value.driver().encode(),MAX_ORIGINAL_BYTES));
        Stamp stamp=value.stamp();row.put("stamp",obj(java.util.Map.of("driver_version",integer(stamp.driverVersion()),"episode_epoch",integer(stamp.episodeEpoch()),
                "game",DriverJson.fromNode(stamp.game().toJson()),"episode_run_id",text(stamp.episodeRunId()),"driver_sha256",text(stamp.driverSha256()))));
        row.put("original_history_basis",reference(value.originalHistoryBasis()));
        var actions=new java.util.ArrayList<OpportunityJson.Value>();
        for(ActionRow action:value.actionRows()) {
            OpportunityJson.Obj source;
            if(action.coverageSource() instanceof LegacyHistoryRow legacy)
                source=obj(java.util.Map.of("kind",text("legacy-history-row"),"history_index",integer(legacy.historyIndex()),"original_row",reference(legacy.originalRow())));
            else source=obj(java.util.Map.of("kind",text("canonical-only"),"original_source",reference(((CanonicalOnly)action.coverageSource()).originalSource())));
            actions.add(obj(java.util.Map.of("action_id",text(action.actionId()),"body_sha256",text(action.bodySha256()),"durable_sequence",integer(action.durableSequence()),"coverage_source",source)));
        }
        row.put("action_rows",new OpportunityJson.Arr(actions));row.put("auxiliary",value.auxiliary());
        row.put("loop",value.loop().<OpportunityJson.Value>map(loop->obj(java.util.Map.of("batch_id",text(loop.batchId()),"turn",integer(loop.turn()),
                "epoch",integer(loop.epoch()),"dirty",new OpportunityJson.Bool(loop.dirty()),"eligible_since_save",integer(loop.eligibleSinceSave()),
                "quarantined",new OpportunityJson.Bool(loop.quarantined()),"original_facts",reference(loop.originalFacts())))).orElse(OpportunityJson.Nil.INSTANCE));
        row.put("observation",value.observation().<OpportunityJson.Value>map(observation->reference(observation.semanticFactsEvidence())).orElse(OpportunityJson.Nil.INSTANCE));
        return originalKnownJson(DriverJson.encode(new OpportunityJson.Obj(row)));
    }

    /** Complete Known material ingress. Closed wire validation selects no current Native or cold authority. */
    public static org.xar.ck3.control.application.action.RawJson originalKnownJson(byte[] original) {
        var material=org.xar.ck3.control.application.action.RawJson.fullMaterial(original);
        observationOriginalReference(material);
        return material;
    }

    /**
     * Restores all seven facts slots without inventing auxiliary/history/coverage. A non-null observation
     * requires the caller's actual original-manifest replay; decoding these DATA grants no current Native authority.
     */
    public static Known decodeKnownOriginal(org.xar.ck3.control.application.action.RawJson original,
            Optional<DriverObservationFacts> actualReplayedObservation) {
        Objects.requireNonNull(original);Objects.requireNonNull(actualReplayedObservation);
        var row=checked(DriverJson.object(original.bytes(),MAX_ORIGINAL_BYTES),java.util.Set.of("schema","driver","stamp","original_history_basis","action_rows","auxiliary","loop","observation"));
        StrictJson.require(ORIGINAL_SCHEMA.equals(string(row,"schema")),"exact complete Known original version required");
        var driver=DriverStateSnapshot.decodeComplete(DriverJson.encode(row.get("driver")));
        var stampRow=checked(row.get("stamp"),java.util.Set.of("driver_version","episode_epoch","game","episode_run_id","driver_sha256"));
        var stamp=new Stamp(number(stampRow,"driver_version",0),number(stampRow,"episode_epoch",0),
                GameGeneration.fromJson(DriverJson.toNode(stampRow.get("game"))),string(stampRow,"episode_run_id"),string(stampRow,"driver_sha256"));
        StrictJson.require(row.get("action_rows") instanceof OpportunityJson.Arr,"complete Known action rows must be an array");
        var actions=new java.util.ArrayList<ActionRow>();
        for(var item:((OpportunityJson.Arr)row.get("action_rows")).items()) {
            var action=checked(item,java.util.Set.of("action_id","body_sha256","durable_sequence","coverage_source"));
            var source=OpportunityJson.object(action.get("coverage_source"),"coverage_source");CoverageSource coverage;
            switch(string(source,"kind")) {
                case "legacy-history-row" -> {checked(source,java.util.Set.of("kind","history_index","original_row"));coverage=new LegacyHistoryRow(number(source,"history_index",1),reference(source.get("original_row")));}
                case "canonical-only" -> {checked(source,java.util.Set.of("kind","original_source"));coverage=new CanonicalOnly(reference(source.get("original_source")));}
                default -> throw new IllegalArgumentException("unknown complete Known action coverage source");
            }
            actions.add(new ActionRow(string(action,"action_id"),string(action,"body_sha256"),number(action,"durable_sequence",1),coverage));
        }
        Optional<LoopWitness> loop=Optional.empty();
        if(row.get("loop")!=OpportunityJson.Nil.INSTANCE) {
            var fields=checked(row.get("loop"),java.util.Set.of("batch_id","turn","epoch","dirty","eligible_since_save","quarantined","original_facts"));
            loop=Optional.of(new LoopWitness(string(fields,"batch_id"),number(fields,"turn",0),number(fields,"epoch",0),
                    bool(fields,"dirty"),number(fields,"eligible_since_save",0),bool(fields,"quarantined"),reference(fields.get("original_facts"))));
        }
        if(row.get("observation")==OpportunityJson.Nil.INSTANCE)
            StrictJson.require(actualReplayedObservation.isEmpty(),"observation absent in original Known; an unrelated replay cannot be injected");
        else {
            ExactRef manifest=reference(row.get("observation"));
            var facts=actualReplayedObservation.orElseThrow(()->new IllegalArgumentException("actual original observation-manifest replay is required"));
            StrictJson.require(facts.semanticFactsEvidence().equals(manifest),"replayed observation belongs to another original Known manifest");
        }
        return new Known(driver,stamp,reference(row.get("original_history_basis")),actions,
                OpportunityJson.object(row.get("auxiliary"),"auxiliary"),loop,actualReplayedObservation);
    }
    /** Presence only: selects the existing manifest replay path; this does not decode or qualify a full Known. */
    public static Optional<ExactRef> observationOriginalReference(org.xar.ck3.control.application.action.RawJson original){
        var row=checked(DriverJson.object(Objects.requireNonNull(original).bytes(),MAX_ORIGINAL_BYTES),java.util.Set.of("schema","driver","stamp","original_history_basis","action_rows","auxiliary","loop","observation"));
        StrictJson.require(ORIGINAL_SCHEMA.equals(string(row,"schema")),"exact complete Known original version required");
        return row.get("observation")==OpportunityJson.Nil.INSTANCE?Optional.empty():Optional.of(reference(row.get("observation")));
    }
    private static OpportunityJson.Obj checked(OpportunityJson.Value value,java.util.Set<String> fields){
        var row=OpportunityJson.object(value,"Known original object");StrictJson.require(row.members().keySet().equals(fields),"exact Known original fields required");return row;
    }
    private static OpportunityJson.Obj obj(java.util.Map<String,OpportunityJson.Value> fields){return new OpportunityJson.Obj(fields);}
    private static OpportunityJson.Text text(String value){return new OpportunityJson.Text(value);}
    private static OpportunityJson.IntegerValue integer(long value){return new OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(value));}
    private static OpportunityJson.Obj reference(ExactRef value){return DriverObservationEvidenceReader.reference(value);}
    private static ExactRef reference(OpportunityJson.Value value){return DriverObservationEvidenceReader.reference(value);}
    private static String string(OpportunityJson.Obj row,String name){return OpportunityJson.text(row.get(name),name);}
    private static long number(OpportunityJson.Obj row,String name,long minimum){long value=OpportunityJson.integer(row.get(name),name).longValueExact();StrictJson.safe(value,minimum);return value;}
    private static boolean bool(OpportunityJson.Obj row,String name){var value=row.get(name);StrictJson.require(value instanceof OpportunityJson.Bool,"Known original boolean required: "+name);return ((OpportunityJson.Bool)value).value();}
}
