package org.xar.ck3.control.application.history;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Finite original rich-read DATA. Only an installed source-owned pure projector can qualify publication. */
public final class DriverReadHistoryRichMaterial {
    private DriverReadHistoryRichMaterial() { }
    public enum Kind { ARMY_STRENGTHS, ARMY_OBSERVER_SAMPLING, PUBLIC_EXECUTE_QUERY }

    /** Pure installed projector output. A plan contains no result of storage until its explicit private capture. */
    public sealed interface HistoryProjection permits Projection,ArmySummaryPlan,ExecuteProjection {
        Kind kind();
        List<ExactRef> sourceClosure();
    }
    @FunctionalInterface public interface SummaryCapture {
        SummaryProjection capture() throws java.io.IOException;
    }
    @FunctionalInterface public interface SummaryReplay {
        /** Read-only original reconstruction. It must not record, create directories, issue Native reads or alter quota. */
        SummaryProjection replay(RawJson archivedStorageOriginal) throws java.io.IOException;
    }
    @FunctionalInterface public interface SummaryRevalidation {
        /** Source owner checks its actual private captured store/result/input; public DATA alone cannot satisfy this. */
        void requireOriginal(SummaryProjection actualCaptured) throws java.io.IOException;
    }
    /**
     * Constructed only as DATA by the identical installed source-owned pure projector after original receipt replay.
     * The sole publisher separately proves its live Known/component/writer custody before captureOriginal.
     * Capture is memoized once per plan; failed capture is terminal and is never retried by this plan.
     */
    public static final class ArmySummaryPlan implements HistoryProjection {
        private final SummaryCapture capture;
        private final SummaryReplay replay;
        private final SummaryRevalidation original;
        private final List<ExactRef> sourceClosure;
        private boolean entered;
        private SummaryProjection captured;
        public ArmySummaryPlan(SummaryCapture capture,SummaryReplay replay,SummaryRevalidation original,List<ExactRef> sourceClosure) {
            this.capture=Objects.requireNonNull(capture);this.replay=Objects.requireNonNull(replay);this.original=Objects.requireNonNull(original);
            this.sourceClosure=summaryReferences(sourceClosure,1,260);
        }
        @Override public Kind kind(){return Kind.ARMY_STRENGTHS;}
        @Override public List<ExactRef> sourceClosure(){return sourceClosure;}
        public synchronized SummaryProjection captureOriginal() throws java.io.IOException {
            if(captured!=null)return captured;
            StrictJson.require(!entered,"failed original summary capture is terminal; no storage retry");entered=true;
            SummaryProjection actual=Objects.requireNonNull(capture.capture());requireClosure(actual);captured=actual;return actual;
        }
        public SummaryProjection replayOriginal(RawJson archivedStorageOriginal) throws java.io.IOException {
            Objects.requireNonNull(archivedStorageOriginal);SummaryProjection actual=Objects.requireNonNull(replay.replay(archivedStorageOriginal));
            requireClosure(actual);StrictJson.require(actual.storageOriginal().equals(archivedStorageOriginal),
                    "summary replay changed its exact archived storage original");return actual;
        }
        public synchronized void requireOriginal(SummaryProjection actualCaptured) throws java.io.IOException {
            StrictJson.require(captured!=null&&captured==actualCaptured,"summary has no identical private capture in this source-owned plan");
            requireClosure(actualCaptured);original.requireOriginal(actualCaptured);
        }
        private void requireClosure(SummaryProjection projection) {
            StrictJson.require(projection.sourceClosure().containsAll(sourceClosure),"summary omitted its installed plan source closure");
        }
    }
    /**
     * Original numeric small summary, its exact public-role pair and finite recorded storage metadata.
     * This public DATA constructor grants no receipt, store issuance, file custody or publication authority.
     * Guarded full files remain separate from the canonical small-row artifact.
     */
    public record SummaryProjection(RawJson summary,PublicNumbers publicNumbers,RawJson storageOriginal,
            List<ExactRef> materialEvidence,List<ExactRef> sourceClosure) {
        public SummaryProjection {
            Objects.requireNonNull(summary);Objects.requireNonNull(publicNumbers);Objects.requireNonNull(storageOriginal);
            materialEvidence=summaryReferences(materialEvidence,0,64);sourceClosure=summaryReferences(sourceClosure,1,260);
            StrictJson.require(storageOriginal.bytes().length<=131072,"finite original storage metadata required, not a second complete Driver result");
            DriverJson.object(storageOriginal.bytes(),131072);
            Obj value=DriverJson.object(summary.bytes(),RawJson.MAXIMUM_BYTES);publicNumbers.toPublic(value);
            StrictJson.require(new Text("xar.ck3.army-query-history-summary.v1").equals(value.get("history_summary_schema"))
                    &&new Text("query-army-strengths-v1").equals(value.get("step"))&&new Bool(true).equals(value.get("accepted")),
                    "finite original successful Army history summary required");
            StrictJson.text(OpportunityJson.text(value.get("status"),"summary status"));
            List<Value> rows=OpportunityJson.array(value.get("armies"),"actual finite summary armies");
            StrictJson.require(OpportunityJson.integer(value.get("army_count"),"summary army count").equals(BigInteger.valueOf(rows.size())),
                    "summary army count differs from its actual finite rows");
            OpportunityJson.bool(value.get("full_result_preserved"),"original summary full-result preservation");
        }
    }
    private static List<ExactRef> summaryReferences(List<ExactRef> values,int minimum,int maximum) {
        values=List.copyOf(values);StrictJson.require(values.size()>=minimum&&values.size()<=maximum
                &&new HashSet<>(values).size()==values.size()&&values.stream().allMatch(value->value.bytes()>0),
                "finite distinct exact summary source/material references required");return values;
    }

    /**
     * A complete original execute-query report with two explicitly different operation roles.
     * The same installed source-owned pure decoder/formatter must reconstruct the encoded original command;
     * the finite registry independently checks the exact logical operation and declared report-step rule.
     * A DATA constructor supplies neither an actual receipt nor a publication permit.
     */
    public record ExecuteProjection(org.xar.ck3.control.application.action.OperationKey logicalOperation,
            org.xar.ck3.control.application.action.OperationKey originalCommand,RawJson fullResult,
            PublicNumbers publicNumbers,List<ExactRef> sourceClosure) implements HistoryProjection {
        public ExecuteProjection {
            Objects.requireNonNull(logicalOperation);Objects.requireNonNull(originalCommand);Objects.requireNonNull(fullResult);Objects.requireNonNull(publicNumbers);
            sourceClosure=summaryReferences(sourceClosure,1,260);
            Obj report=DriverJson.object(fullResult.bytes(),RawJson.MAXIMUM_BYTES);publicNumbers.toPublic(report);
            StrictJson.text(OpportunityJson.text(report.get("step"),"original execute report step"));
        }
        @Override public Kind kind(){return Kind.PUBLIC_EXECUTE_QUERY;}
    }

    /** Complete internal numeric Driver result, never a Native ACK or a decoded public response.
     * Constructor validation supplies no receipt, freshness, writer, archive or planning authority.
     */
    public record Projection(Kind kind, RawJson fullResult, PublicNumbers publicNumbers, List<ExactRef> sourceClosure) implements HistoryProjection {
        public Projection {
            Objects.requireNonNull(kind); Objects.requireNonNull(fullResult); Objects.requireNonNull(publicNumbers);
            sourceClosure = List.copyOf(sourceClosure);
            StrictJson.require(!sourceClosure.isEmpty() && sourceClosure.size() <= 260
                    && new HashSet<>(sourceClosure).size() == sourceClosure.size()
                    && sourceClosure.stream().allMatch(ref -> ref.bytes() > 0),
                    "complete distinct original rich projection sources required");
            Obj result = DriverJson.object(fullResult.bytes(), RawJson.MAXIMUM_BYTES);
            publicNumbers.toPublic(result);
            if (kind == Kind.ARMY_STRENGTHS) {
                StrictJson.require(new Text("query-army-strengths-v1").equals(result.get("step"))
                        && new Bool(true).equals(result.get("accepted")) && result.get("army_strengths") instanceof Arr,
                        "complete successful internal Army Driver result required");
                StrictJson.text(OpportunityJson.text(result.get("army_strengths_profile"), "Army profile"));
                StrictJson.text(OpportunityJson.text(result.get("status"), "Army status"));
                positive(result.get("query_sequence"), "original query sequence");
            } else {
                StrictJson.require(kind==Kind.ARMY_OBSERVER_SAMPLING,"public execute queries require their explicit ExecuteProjection command roles");
                requireSampling(result);
            }
            nonnegative(result.get("queried_revision"), "original public revision");
            positive(result.get("queried_native_revision"), "original native revision");
            positive(result.get("queried_connection_generation"), "original connection generation");
            StrictJson.text(OpportunityJson.text(result.get("queried_snapshot_id"), "original snapshot"));
            if (kind == Kind.ARMY_STRENGTHS) OpportunityJson.integer(result.get("queried_date_raw"), "original date").intValueExact();
            else nonnegative(result.get("queried_date_raw"), "original sampling date");
            Value episode = result.get("queried_episode_run_id");
            StrictJson.require(episode == Nil.INSTANCE || episode instanceof Text,
                    "original queried episode must retain its explicit text/null domain");
            if (episode instanceof Text value) StrictJson.text(value.value());
        }
    }

    public sealed interface PathPart permits Field,Element { }
    public record Field(String name) implements PathPart {
        public Field {Objects.requireNonNull(name);StrictJson.require(name.length()<=65536,"bounded original JSON field required");}
    }
    public record Element(int index) implements PathPart {
        public Element {StrictJson.require(index>=0,"original JSON array index required");}
    }
    public record NumberPath(List<PathPart> parts) {
        public NumberPath {parts=List.copyOf(parts);StrictJson.require(!parts.isEmpty()&&parts.size()<=64,"bounded explicit integer role path required");}
    }
    /** Lossless transport roles from the SAME source-owned internal/public computation, never field-name inference. */
    public record PublicNumbers(List<NumberPath> decimalIntegers) {
        private static final BigInteger SAFE=BigInteger.valueOf(9007199254740991L);
        public PublicNumbers {
            decimalIntegers=List.copyOf(decimalIntegers);
            StrictJson.require(decimalIntegers.size()<=65536&&new HashSet<>(decimalIntegers).size()==decimalIntegers.size(),
                    "finite distinct original integer public roles required");
            decimalIntegers=decimalIntegers.stream().sorted(java.util.Comparator.comparing(PublicNumbers::pathKey)).toList();
        }
        public static PublicNumbers fromResults(RawJson internal,RawJson publicResult) {
            Obj original=DriverJson.object(internal.bytes(),RawJson.MAXIMUM_BYTES);
            Obj exposed=DriverJson.object(publicResult.bytes(),RawJson.MAXIMUM_BYTES);
            var roles=new java.util.ArrayList<NumberPath>();compare(original,exposed,List.of(),roles);
            PublicNumbers result=new PublicNumbers(roles);
            StrictJson.require(result.toPublic(original).equals(exposed),"public rich formatter changed a non-integer value");return result;
        }
        public Obj toPublic(Obj internal) {
            Value value=internal;for(NumberPath path:decimalIntegers)value=change(value,path.parts(),0,true);
            requireSafe(value);return OpportunityJson.object(value,"typed public rich result");
        }
        public Obj fromPublic(Obj exposed) {
            Value value=exposed;for(NumberPath path:decimalIntegers)value=change(value,path.parts(),0,false);
            Obj internal=OpportunityJson.object(value,"original numeric rich result");
            StrictJson.require(toPublic(internal).equals(exposed),"public rich integer transport is not canonical");return internal;
        }
        public Arr toJson() {
            return new Arr(decimalIntegers.stream().<Value>map(path->new Arr(path.parts().stream().<Value>map(PublicNumbers::partJson).toList())).toList());
        }
        public static PublicNumbers fromJson(Value value) {
            PublicNumbers result=new PublicNumbers(OpportunityJson.array(value,"declared rich public integer roles").stream().map(path->
                    new NumberPath(OpportunityJson.array(path,"integer role path").stream().map(PublicNumbers::part).toList())).toList());
            StrictJson.require(result.toJson().equals(value),"canonical explicit integer role order required");return result;
        }
        private static String pathKey(NumberPath path) {
            return new String(OpportunityJson.encode(new Arr(path.parts().stream().<Value>map(PublicNumbers::partJson).toList())),java.nio.charset.StandardCharsets.UTF_8);
        }
        private static Obj partJson(PathPart part) {
            return switch(part) {
                case Field field->new Obj(java.util.Map.of("field",new Text(field.name())));
                case Element element->new Obj(java.util.Map.of("index",new IntegerValue(BigInteger.valueOf(element.index()))));
            };
        }
        private static PathPart part(Value value) {
            Obj item=OpportunityJson.object(value,"typed integer path part");
            if(item.members().keySet().equals(Set.of("field")))return new Field(OpportunityJson.text(item.get("field"),"integer path field"));
            StrictJson.require(item.members().keySet().equals(Set.of("index")),"exact integer path discriminator required");
            return new Element(OpportunityJson.integer(item.get("index"),"integer path index").intValueExact());
        }
        private static void compare(Value original,Value exposed,List<PathPart> path,List<NumberPath> roles) {
            if(original instanceof Obj left&&exposed instanceof Obj right) {
                StrictJson.require(left.members().keySet().equals(right.members().keySet()),"rich public object shape changed");
                for(String key:left.members().keySet())compare(left.get(key),right.get(key),next(path,new Field(key)),roles);return;
            }
            if(original instanceof Arr left&&exposed instanceof Arr right) {
                StrictJson.require(left.items().size()==right.items().size(),"rich public array shape changed");
                for(int i=0;i<left.items().size();i++)compare(left.items().get(i),right.items().get(i),next(path,new Element(i)),roles);return;
            }
            if(original instanceof IntegerValue integer&&exposed instanceof Text text) {
                StrictJson.require(integer.value().toString().equals(text.value()),"public integer differs from its original exact value");
                roles.add(new NumberPath(path));return;
            }
            StrictJson.require(Objects.equals(original,exposed),"public rich formatter changed an original non-integer JSON domain/value");
        }
        private static List<PathPart> next(List<PathPart> path,PathPart part) {
            var result=new java.util.ArrayList<>(path);result.add(part);return List.copyOf(result);
        }
        private static Value change(Value value,List<PathPart> path,int position,boolean encode) {
            if(position==path.size()) {
                if(encode)return new Text(OpportunityJson.integer(value,"declared original public integer").toString());
                String exact=OpportunityJson.text(value,"declared public decimal integer");
                StrictJson.require(exact.length()<=4300&&exact.matches("0|-?[1-9][0-9]*"),"canonical exact public integer string required");
                return new IntegerValue(new BigInteger(exact));
            }
            PathPart part=path.get(position);
            return switch(part) {
                case Field field -> {
                    Obj object=OpportunityJson.object(value,"integer role object parent");
                    StrictJson.require(object.members().containsKey(field.name()),"declared integer role field is absent");
                    yield object.with(field.name(),change(object.get(field.name()),path,position+1,encode));
                }
                case Element element -> {
                    List<Value> items=OpportunityJson.array(value,"integer role array parent");
                    StrictJson.require(element.index()<items.size(),"declared integer role index is absent");
                    var copy=new java.util.ArrayList<>(items);copy.set(element.index(),change(copy.get(element.index()),path,position+1,encode));yield new Arr(copy);
                }
            };
        }
        private static void requireSafe(Value value) {
            if(value instanceof IntegerValue integer)StrictJson.require(integer.value().abs().compareTo(SAFE)<=0,
                    "source-owned public formatter omitted a wide integer role");
            else if(value instanceof Obj object)object.members().values().forEach(PublicNumbers::requireSafe);
            else if(value instanceof Arr array)array.items().forEach(PublicNumbers::requireSafe);
        }
    }
    /** Canonical artifact retention only; this does not claim legacy sidecar policy/configuration parity. */
    public sealed interface StorageOutcome permits FullStored, StorageDiagnostic, SummaryStored { }
    /** Canonical small row retained; this does not claim a current full sidecar or legacy policy success. */
    public record SummaryStored(ExactRef originalRow) implements StorageOutcome {
        public SummaryStored {Objects.requireNonNull(originalRow);StrictJson.require(originalRow.bytes()>0,"actual retained summary row required");}
    }
    public record FullStored(ExactRef fullResult) implements StorageOutcome {
        public FullStored { Objects.requireNonNull(fullResult); StrictJson.require(fullResult.bytes() > 0,
                "actual retained complete Driver result reference required"); }
    }
    /** An unavailable history artifact must not change the successful live read/cache result. */
    public record StorageDiagnostic(Optional<ExactRef> originalDiagnostic, String failureType, String message)
            implements StorageOutcome {
        public StorageDiagnostic {
            originalDiagnostic = Objects.requireNonNull(originalDiagnostic);
            originalDiagnostic.ifPresent(ref -> StrictJson.require(ref.bytes() > 0, "actual diagnostic reference required"));
            StrictJson.text(failureType); Objects.requireNonNull(message);
        }
    }
    /** Exact public DATA roles only. Native row semantics remain owned by the installed observer decoder. */
    private static void requireSampling(Obj result) {
        StrictJson.require(result.members().keySet().equals(Set.of("step","accepted","status","army_observer_research_sampling_v1",
                "backend_id","observer_family","queried_snapshot_id","queried_revision","queried_native_revision","queried_date_raw",
                "queried_connection_generation","queried_episode_run_id","queried_player_character_id"))
                && new Text("query-army-observer-research-sampling-v1").equals(result.get("step"))
                && new Bool(true).equals(result.get("accepted")) && new Text("completed").equals(result.get("status"))
                && new Text("native-headless").equals(result.get("backend_id")), "exact completed original sampling Driver result required");
        Set<String> families=Set.of("natural_phase","regular_core","daily_assault_preparation","assault_placement","assault_consumer",
                "assault_group_release","gathering","cleanup","pre_date_prefix");
        String selected=OpportunityJson.text(result.get("observer_family"), "original sampling family");
        StrictJson.require(selected.equals("all")||families.contains(selected), "finite original sampling family required");
        Obj rows=OpportunityJson.object(result.get("army_observer_research_sampling_v1"), "original sampling families");
        StrictJson.require(rows.members().keySet().equals(selected.equals("all")?families:Set.of(selected)), "exact selected sampling family rows required");
        for (Value value:rows.members().values()) {
            Obj row=OpportunityJson.object(value,"original sampling row");
            StrictJson.require(row.members().keySet().equals(Set.of("installed","available","capture_enabled","busy","clear_completed",
                    "epoch","active_captures","retained_records","qualified_records","status","readiness")), "exact original sampling DATA roles required");
            for (String field:List.of("installed","available","capture_enabled","busy","clear_completed"))
                OpportunityJson.bool(row.get(field),field);
            for (String field:List.of("epoch","active_captures","retained_records","qualified_records")) nonnegative(row.get(field),field);
            StrictJson.text(OpportunityJson.text(row.get("status"),"sampling status"));
            StrictJson.text(OpportunityJson.text(row.get("readiness"),"sampling readiness"));
        }
        BigInteger player=OpportunityJson.integer(result.get("queried_player_character_id"), "original sampling player");
        org.xar.ck3.control.contracts.NativeCharacterId.of(player);
    }
    private static void nonnegative(Value value, String field) {
        BigInteger exact = OpportunityJson.integer(value, field);
        StrictJson.require(exact.signum() >= 0 && exact.compareTo(StrictJson.UINT64_MAX) <= 0,
                field + " requires exact nonnegative uint64");
    }
    private static void positive(Value value, String field) {
        BigInteger exact = OpportunityJson.integer(value, field);
        StrictJson.require(exact.signum() > 0 && exact.compareTo(StrictJson.UINT64_MAX) <= 0,
                field + " requires exact positive uint64");
    }
}
