package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.wave2.military.sharedwire.ArmyManagerSharedWire;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** The original internal Driver result, independently encoded from typed numeric projections.
 * This DATA producer neither records a read nor converts public decimal strings back to numbers.
 */
public final class ArmyStrengthsDriverResult {
    private ArmyStrengthsDriverResult() { }

    /** Immutable typed query DATA with lazy complete numeric encoding. Construction never serializes a full
     * Driver result. The source-owned sidecar store can build its finite summary from source() first, and
     * explicit budget0 must not call original(). This carrier grants no current/read/history authority.
     */
    public static final class NumericResult {
        private final ArmyStrengthsService.Reply source;
        private RawJson encoded;
        private NumericResult(ArmyStrengthsService.Reply actual) { source = Objects.requireNonNull(actual); }
        public ArmyStrengthsService.Reply source() { return source; }
        public synchronized RawJson original() {
            if (encoded == null) encoded = ArmyStrengthsDriverResult.encode(source);
            return encoded;
        }
    }
    public static NumericResult numeric(ArmyStrengthsService.Reply actual) { return new NumericResult(actual); }


    /** The same pure selection/pipeline computation used by the live service and archival history projection. */
    public static ArmyStrengthsService.Reply project(ArmyStrengthsContracts.Selection selection, Read original,
            ArmyStrengthsPipeline pipeline) {
        Objects.requireNonNull(selection); Objects.requireNonNull(original); Objects.requireNonNull(pipeline);
        var context = selection.snapshot().context(); var request = original.original().request();
        require(request.before().equals(context.before()) && request.source().equals(context.source())
                && request.sessionId().equals(context.sessionId()) && request.operation().value().equals(STEP),
                "Army Driver projection crossed its actual selected original source/frame/session");
        List<Row> rows = original.rows();
        if (selection.query().requestedArmies() instanceof Present<List<PublicUnitId>> requested)
            rows = requested.value().stream().map(id -> original.rows().stream()
                    .filter(row -> row.core().army().equals(id)).findFirst().orElseThrow()).toList();
        var scopeStatus = original.publishedScopeStatus() instanceof Present<Status> value ? value.value() : original.status();
        ArmyStrengthsPipeline.Results projections;
        if (selection.query().mode() == Mode.EXPLICIT_RICH) {
            pipeline.requireComplete();
            projections = pipeline.project(new ArmyStrengthsPipeline.Input(selection.snapshot(), original,
                    selection.query(), rows, Optional.of(selection.originalHello())));
        } else projections = new ArmyStrengthsPipeline.Results(List.of());
        return new ArmyStrengthsService.Reply(selection, original, rows, ArmyStrengths.status(rows), scopeStatus, projections);
    }

    /** Numeric internal wire, matching the legacy complete Driver result before history sidecar compaction.
     * The caller separately proves original receipt/source custody and invokes the installed pure replay.
     */
    public static RawJson encode(ArmyStrengthsService.Reply actual) {
        Objects.requireNonNull(actual);
        Read original = actual.original(); var selection = actual.selection(); var frame = selection.snapshot().binding();
        var context = selection.snapshot().context(); var receipt = original.original();
        require(receipt.request().before().equals(context.before()) && receipt.request().source().equals(context.source())
                && receipt.request().sessionId().equals(context.sessionId()) && receipt.request().operation().value().equals(STEP),
                "Army Driver result crossed its actual original selected read");
        ObjectNode nativeResult = ArmyJson.parse(receipt.original().originalResultToken().orElseThrow(
                () -> new IllegalArgumentException("Army Driver result lacks its original native query token")).bytes());
        require(ArmyJson.text(nativeResult.get("step")).equals(STEP) && ArmyJson.bool(nativeResult.get("accepted"))
                && ArmyJson.integer(nativeResult.get("query_sequence")).equals(original.sequence()),
                "Army Driver result changed its actual native query identity");
        ObjectNode out = selection.query().mode() == Mode.EXPLICIT_RICH
                ? ArmyManagerSharedWire.expand(nativeResult, false).deepCopy() : nativeResult.deepCopy();
        if (selection.query().mode() != Mode.EXPLICIT_RICH) out.remove(ArmyManagerSharedWire.SHARED_KEY);
        // This Java-only Native input is retained in the original receipt. Legacy Driver results retain its typed projections.
        out.remove("observed_army_stage_inputs_12004");
        out.put("status", ArmyStrengthsCodec.wire(actual.status()));
        out.put("army_strengths_profile", original.profile().wire());
        out.put("army_observed_phase_coverage", original.profile().coverage());
        out.put("query_sequence", original.sequence());
        var rows = out.putArray("army_strengths");
        actual.selected().forEach(row -> rows.add(actual.projections().rowJson(row)));
        out.setAll(actual.projections().topLevelJson());
        out.put("queried_snapshot_id", frame.snapshotId()).put("queried_revision", frame.publicRevision())
                .put("queried_native_revision", frame.nativeRevision()).put("queried_date_raw", frame.dateRaw())
                .put("queried_connection_generation", frame.connectionGeneration());
        frame.episodeRunId().ifPresentOrElse(value -> out.put("queried_episode_run_id", value),
                () -> out.putNull("queried_episode_run_id"));
        return new RawJson(ArmyJson.bytes(out));
    }

    /** The same complete Driver field tree, using the owning row/stage public codecs for every numeric role. */
    public static RawJson encodeHistoryPublic(ArmyStrengthsService.Reply actual) {
        Objects.requireNonNull(actual);
        ObjectNode out = ArmyJson.parse(encode(actual).bytes());
        Read original = actual.original(); var frame = actual.selection().snapshot().binding();
        out.put("query_sequence", original.sequence().toString());
        out.put("queried_revision", frame.publicRevision().toString());
        out.put("queried_native_revision", frame.nativeRevision().toString());
        out.put("queried_date_raw", frame.dateRaw().toString());
        out.put("queried_connection_generation", frame.connectionGeneration().toString());
        var rows = out.putArray("army_strengths");
        actual.selected().forEach(row -> rows.add(actual.projections().rowPublicV2Json(row)));
        out.setAll(actual.projections().topLevelPublicV2Json());
        if (original.timing() instanceof Present<NativeTiming> timing) {
            NativeTiming value = timing.value();
            out.putObject("army_native_timing_v1").put("read_total_ns", value.readTotalNs().toString())
                    .put("owner_query_ns", value.ownerQueryNs().toString()).put("baseline_read_ns", value.baselineReadNs().toString())
                    .put("rich_attach_ns", value.richAttachNs().toString()).put("serialize_ns", value.serializeNs().toString());
        } else if (original.timing() instanceof NullValue<?>) out.putNull("army_native_timing_v1");
        return new RawJson(ArmyJson.bytes(out));
    }


    /** Source-owned lazy sidecar history. Pure construction does not record, encode a complete result or
     * inspect directories. Only the sole publisher's final original capture can run the actual store.
     */
    public static DriverReadHistoryRichMaterial.ArmySummaryPlan historySummary(ArmyStrengthsService.Reply actual,
            ArmyQueryHistoryStore sameStore, ExactRef actualSettingsOriginal, List<ExactRef> completeSources) {
        Objects.requireNonNull(actual); Objects.requireNonNull(sameStore); Objects.requireNonNull(actualSettingsOriginal);
        List<ExactRef> sources=List.copyOf(completeSources);
        require(sources.contains(actualSettingsOriginal),"summary settings must belong to the actual source closure");
        NumericResult input=numeric(actual); Captured[] captured={null};
        return new DriverReadHistoryRichMaterial.ArmySummaryPlan(() -> {
            ArmyQueryHistoryStore.Result result=sameStore.record(input);result.requireInput(input);
            require(result.issuedBy(sameStore),"summary capture changed its actual installed store");
            RawJson storage=storageOriginal(result,actualSettingsOriginal);
            var projection=summaryProjection(result.summary(),storage,sources);
            captured[0]=new Captured(input,result,projection);return projection;
        },storage -> replaySummary(input,sameStore,actualSettingsOriginal,sources,storage),projection -> {
            Captured owned=captured[0];
            require(owned!=null&&owned.projection()==projection&&owned.input()==input&&owned.result().issuedBy(sameStore),
                    "summary DATA lacks this installed source's identical private store capture");
            owned.result().requireInput(input);
            // A privately captured storage denial remains a successful read's finite diagnostic, as in the original producer.
            // Native/writer/current-source qualification remains the sole publisher's independent responsibility.
            if (!(owned.result() instanceof ArmyQueryHistoryStore.AdmissionRejected)) sameStore.requireCurrentAdmission();
            require(owned.result().summary().equals(projection.summary())
                    &&storageOriginal(owned.result(),actualSettingsOriginal).equals(projection.storageOriginal()),
                    "actual private summary/store/settings original changed");
            var roles=DriverReadHistoryRichMaterial.PublicNumbers.fromResults(owned.result().summary(),owned.result().publicSummary());
            require(roles.equals(projection.publicNumbers()),"private summary public roles changed");
        },sources);
    }
    private record Captured(NumericResult input,ArmyQueryHistoryStore.Result result,
            DriverReadHistoryRichMaterial.SummaryProjection projection) { }
    private static final String STORAGE_SCHEMA="xar.ck3.army-history-storage-original/v1";
    private enum StorageKind { DISABLED,FULL_STORED,ADMISSION_REJECTED,BUDGET_EXHAUSTED,IO_ERROR }
    private static StorageKind kind(ArmyQueryHistoryStore.Result result) {
        if(result instanceof ArmyQueryHistoryStore.Disabled)return StorageKind.DISABLED;
        if(result instanceof ArmyQueryHistoryStore.FullStored)return StorageKind.FULL_STORED;
        if(result instanceof ArmyQueryHistoryStore.AdmissionRejected)return StorageKind.ADMISSION_REJECTED;
        if(result instanceof ArmyQueryHistoryStore.BudgetExhausted)return StorageKind.BUDGET_EXHAUSTED;
        if(result instanceof ArmyQueryHistoryStore.IoError)return StorageKind.IO_ERROR;
        throw new IllegalArgumentException("numeric original capture cannot be an already-compact caller result");
    }
    private static RawJson storageOriginal(ArmyQueryHistoryStore.Result result,ExactRef settings) {
        ObjectNode summary=ArmyJson.parse(result.summary().bytes());var configuration=result.settings();
        ObjectNode out=ArmyJson.empty().put("schema",STORAGE_SCHEMA).put("outcome",kind(result).name())
                .put("evidence_directory",configuration.evidenceDirectory().toString()).put("limit_bytes",configuration.limitBytes());
        out.set("settings_original",settings.toJson());
        for(String key:List.of("raw_result_reference","unavailable_reason","history_storage_diagnostic"))
            out.set(key,summary.has(key)?summary.get(key).deepCopy():com.fasterxml.jackson.databind.node.NullNode.instance);
        return new RawJson(ArmyJson.bytes(out));
    }
    private static DriverReadHistoryRichMaterial.SummaryProjection summaryProjection(RawJson summary,RawJson storage,
            List<ExactRef> sources) {
        var publicNumbers=DriverReadHistoryRichMaterial.PublicNumbers.fromResults(summary,ArmyQueryHistoryStore.publicSummary(summary));
        // Raw sidecar paths are not canonical OutcomeArchive artifacts. The fixed readonly replay owns their reader.
        return new DriverReadHistoryRichMaterial.SummaryProjection(summary,publicNumbers,storage,List.of(),sources);
    }

    /** Rebuild only from the actual receipt-derived typed input and its immutable recorded storage metadata.
     * No record(), directory scan, mkdir, quota mutation or Native operation occurs here.
     */
    private static DriverReadHistoryRichMaterial.SummaryProjection replaySummary(NumericResult input,
            ArmyQueryHistoryStore store,ExactRef settings,List<ExactRef> sources,RawJson storage)throws IOException {
        ObjectNode meta=ArmyJson.parse(storage.bytes());
        require(fields(meta).equals(
                Set.of("schema","outcome","evidence_directory","limit_bytes","settings_original","raw_result_reference",
                        "unavailable_reason","history_storage_diagnostic")),"exact finite storage original fields required");
        require(STORAGE_SCHEMA.equals(ArmyJson.text(meta.get("schema")))&&ExactRef.fromJson(meta.get("settings_original")).equals(settings)
                &&store.settings().evidenceDirectory().toString().equals(ArmyJson.text(meta.get("evidence_directory")))
                &&ArmyJson.integer(meta.get("limit_bytes")).equals(java.math.BigInteger.valueOf(store.settings().limitBytes())),
                "summary original crossed its actual installed settings/source/path/limit");
        StorageKind outcome=StorageKind.valueOf(ArmyJson.text(meta.get("outcome")));
        JsonNode rawReference=meta.get("raw_result_reference"),rawReason=meta.get("unavailable_reason"),rawDiagnostic=meta.get("history_storage_diagnostic");
        Optional<ArmyQueryHistoryStore.StoredFile> reference=Optional.empty();Optional<String> reason=Optional.empty();
        Optional<ObjectNode> diagnostic=Optional.empty();
        if(outcome==StorageKind.FULL_STORED) {
            require(store.settings().limitBytes()>0&&rawReason.isNull()&&rawDiagnostic.isNull()&&rawReference instanceof ObjectNode,
                    "successful full storage original has inconsistent configuration/diagnostics");
            ObjectNode ref=(ObjectNode)rawReference;
            require(fields(ref).equals(Set.of("path","bytes","sha256","kind","wire_bytes_preserved"))
                    &&ArmyQueryHistoryStore.REFERENCE_KIND.equals(ArmyJson.text(ref.get("kind")))
                    &&ref.get("wire_bytes_preserved").isBoolean()&&!ref.get("wire_bytes_preserved").booleanValue(),
                    "actual complete Driver sidecar reference required, not original wire evidence");
            long bytes=ArmyJson.integer(ref.get("bytes")).longValueExact();require(bytes>0,"positive actual stored sidecar bytes required");
            reference=Optional.of(new ArmyQueryHistoryStore.StoredFile(Path.of(ArmyJson.text(ref.get("path"))),bytes,ArmyJson.text(ref.get("sha256"))));
        } else {
            require(rawReference.isNull()&&rawDiagnostic instanceof ObjectNode,"failed/disabled sidecar cannot acquire a complete reference");
            String expected=switch(outcome) {
                case DISABLED -> "sidecar_disabled_by_session_budget";
                case ADMISSION_REJECTED -> "sidecar_admission_rejected";
                case BUDGET_EXHAUSTED -> "sidecar_budget_exhausted";
                case IO_ERROR -> "sidecar_io_error";
                default -> throw new IllegalArgumentException("unexpected complete storage branch");
            };
            require(expected.equals(ArmyJson.text(rawReason)),"summary storage reason crossed its finite actual branch");
            ObjectNode info=(ObjectNode)rawDiagnostic;validateDiagnostic(outcome,info,store.settings().limitBytes());
            reason=Optional.of(expected);diagnostic=Optional.of(info);
        }
        RawJson finite=new RawJson(ArmyJson.bytes(ArmyQueryHistoryStore.finite(input)));
        RawJson summary=ArmyQueryHistoryStore.buildSummary(finite,reference,reason,diagnostic);
        if(reference.isPresent()) {
            var stored=reference.orElseThrow();
            var actual=ArmyQueryHistoryReference.read(summary,store.settings().evidenceDirectory(),stored.bytes());
            require(actual.reference().equals(stored),"readonly sidecar reader changed the original exact reference");
            byte[] expected=input.original().bytes(),retained=actual.completeDriver().bytes();
            // The bounded reader removes the producer's sole final LF from the DATA view.
            // Its reference still authenticates all artifact bytes, including that delimiter.
            require(stored.bytes()==(long)expected.length+1&&Arrays.equals(expected,retained),
                    "readonly complete sidecar differs from its original source-owned pure Driver projection");
        }
        return summaryProjection(summary,storage,sources);
    }
    private static Set<String> fields(ObjectNode value) {
        var names=new java.util.HashSet<String>();value.fieldNames().forEachRemaining(names::add);return Set.copyOf(names);
    }
    private static void validateDiagnostic(StorageKind outcome,ObjectNode actual,long limit) {
        Set<String> expected=switch(outcome) {
            case DISABLED,BUDGET_EXHAUSTED -> Set.of("limit_bytes","charged_bytes");
            case ADMISSION_REJECTED -> Set.of("limit_bytes","reason");
            case IO_ERROR -> Set.of("limit_bytes","charged_bytes","error_type","message","errno");
            default -> throw new IllegalArgumentException("full stored branch has no storage diagnostic");
        };
        require(fields(actual).equals(expected)&&ArmyJson.integer(actual.get("limit_bytes")).equals(java.math.BigInteger.valueOf(limit)),
                "finite original diagnostic fields and actual configured limit required");
        if(outcome==StorageKind.DISABLED)require(limit==0&&ArmyJson.integer(actual.get("charged_bytes")).signum()==0,
                "disabled summary requires explicit zero before any sidecar/full encoding");
        if(outcome==StorageKind.ADMISSION_REJECTED)boundedText(actual.get("reason"),1000,false);
        if(outcome==StorageKind.BUDGET_EXHAUSTED||outcome==StorageKind.IO_ERROR) {
            require(limit>0,"positive configured budget required for actual storage failure");
            JsonNode charged=actual.get("charged_bytes");if(!charged.isNull())require(ArmyJson.integer(charged).signum()>=0
                    &&ArmyJson.integer(charged).bitLength()<=63,"nonnegative original charged-byte diagnostic required");
        }
        if(outcome==StorageKind.IO_ERROR) {
            boundedText(actual.get("error_type"),256,false);boundedText(actual.get("message"),2048,true);
            JsonNode errno=actual.get("errno");if(!errno.isNull())ArmyJson.integer(errno).intValueExact();
        }
    }
    private static void boundedText(JsonNode original,int maximum,boolean emptyAllowed) {
        String value=ArmyJson.text(original);require((emptyAllowed||!value.isEmpty())&&value.codePointCount(0,value.length())<=maximum,
                "finite original storage diagnostic text required");
    }
}
