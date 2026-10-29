package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.action.LifecycleOriginFactory;
import org.xar.ck3.control.application.history.DriverReadHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverObservedHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverFailedReadHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverReturnedControlHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer;
import org.xar.ck3.control.application.history.DriverReturnedActionHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverReturnedPublicReadHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverPostKnownReadFailureRowProducer;
import org.xar.ck3.control.application.history.DriverEarlyExecuteFailureRowProducer;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicCodec;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicContract;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort.HistoryExportMode;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort.SnapshotExport;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort.OrdinarySnapshotExport;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort.FullSnapshotExport;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.application.capabilities.FactionReadReplay;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertsCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyPublicWire;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsReadValue;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRequests;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original snapshot layout. Only proved public identity roles change integer JSON to decimal strings. */
public final class PublicSnapshotCodec {
    private static final BigInteger SAFE=BigInteger.valueOf(9_007_199_254_740_991L);
    private static final String OPTIONAL_HEIR_ENCODING="xar_public_root_heir_revision";
    private static final String OPTIONAL_HEIR_DECIMAL="decimal-u64/v1";
    private static final String OPTIONAL_HEIR_RAW="raw-json/v1";
    private static final String PROJECTION_FIELD="xar_java_snapshot_projection";
    private static final String PROJECTION_SCHEMA="xar.java-public-snapshot-projection/v1";
    private static final int SEMANTIC_MAXIMUM_BYTES=8*1024*1024;
    private static final List<String> TRANSCRIPT_FIELDS=List.of("native_command_history","native_rollback_war_failure","native_rollback_war_failures");
    /* Exact roles: NativeWire.Snapshot.revision; DriverObservationFacts.publicRevision;
       NativeWire.Hello.connectionGeneration; bridge.cpp HeartbeatFrame uint64 sequence/GetTickCount64
       and CommandEntryTraceV1.monotonic_ms at the four explicit published routes; actual
       NativeTransportDiagnostics.Production's two uint64 counters via the sole Driver formatter.
       Rejected raw revision retains its original type and is not an admitted identity role. */
    private static final List<List<String>> IDENTITY_PATHS=List.of(List.of("revision"),List.of("native_revision"),
            List.of("diagnostics","connection_generation"),List.of("diagnostics","hello","connection_generation"),
            List.of("diagnostics","last_heartbeat","sequence"),List.of("diagnostics","last_heartbeat","monotonic_ms"),
            List.of("diagnostics","last_heartbeat","command_entry_trace_v1","timeline","monotonic_ms"),
            List.of("diagnostics","last_heartbeat","command_entry_trace_v1","war_termination_options","monotonic_ms"),
            List.of("diagnostics","last_heartbeat","command_entry_trace_v1","war_termination_terms","monotonic_ms"),
            List.of("diagnostics","last_heartbeat","command_entry_trace_v1","faction_gift_query","monotonic_ms"),
            List.of("diagnostics","rejected_state_snapshot_count"),
            List.of("diagnostics","snapshot_publish_diagnostic_count"));
    private PublicSnapshotCodec() { }
    private record History(Obj semantic,HistoryExportMode mode,long totalCount,long includedCount) { }

    /** Single shared history-export producer used by held Driver and public Root readers. */
    public static OrdinarySnapshotExport export(DriverObservationAssembler.Complete actual,boolean includeHistory) {
        Objects.requireNonNull(actual);var history=history(actual.semantic(),includeHistory);
        return new OrdinarySnapshotExport(actual,history.semantic(),history.mode(),history.totalCount(),history.includedCount());
    }
    /** Original private semantic lane: no transcript keys or omission placeholders; Root supplies its one actual held Complete. */
    public static RawJson exportSemanticOnly(DriverObservationAssembler.Complete actual) {
        Objects.requireNonNull(actual);boolean campaign=nativeCampaign(actual);validateOriginal(actual.semantic(),campaign);requireCompleteBinding(actual,actual.semantic(),campaign);
        var fields=new LinkedHashMap<>(actual.semantic().members());TRANSCRIPT_FIELDS.forEach(fields::remove);
        Obj semantic=new Obj(fields);validateSemanticOnly(semantic,campaign);return publicValue(semantic,true,campaign);
    }
    private static History history(Obj original,boolean includeHistory) {
        var history=array(original.get("native_command_history"),"native_command_history");
        if(includeHistory)return new History(original,HistoryExportMode.FULL,history.size(),history.size());
        var fields=new LinkedHashMap<>(original.members());fields.put("native_command_history",new Arr(List.of()));
        fields.put("native_command_history_export",new Obj(Map.of("mode",new Text("omitted"),"total_count",new IntegerValue(BigInteger.valueOf(history.size())),"included_count",new IntegerValue(BigInteger.ZERO))));
        return new History(new Obj(fields),HistoryExportMode.OMITTED,history.size(),0);
    }
    /**
     * The exact already-waited physical originals. These are DATA; only the owning
     * Root's private qualifier can authorize their current source/writer scope.
     */
    public record FullSnapshotOriginals(DriverObservationAssembler.FullSnapshot actual,ExactRef originalHello,
            ExactRef originalHeartbeat,java.util.Optional<ExactRef> originalSourceQualification,RawJson originalFacts,RawJson originalDriver) {
        public FullSnapshotOriginals {
            Objects.requireNonNull(actual);Objects.requireNonNull(originalFacts);Objects.requireNonNull(originalDriver);
            Objects.requireNonNull(originalSourceQualification);
            for(ExactRef reference:java.util.stream.Stream.concat(List.of(originalHello,originalHeartbeat).stream(),originalSourceQualification.stream()).toList())
                require(reference.bytes()>0 && java.nio.file.Path.of(reference.path()).isAbsolute(),
                        "actual nonempty original physical source proof role required");
        }
        public FullSnapshotOriginals(DriverObservationAssembler.FullSnapshot actual,ExactRef originalHello,
                ExactRef originalHeartbeat,ExactRef originalSourceQualification,RawJson originalFacts,RawJson originalDriver) {
            this(actual,originalHello,originalHeartbeat,java.util.Optional.of(originalSourceQualification),originalFacts,originalDriver);
        }
    }
    /** Reuses one already-waited FullSnapshot, including null/missing/changed player, without constructing Complete. */
    public static FullSnapshotExport exportFull(FullSnapshotOriginals originals,boolean includeHistory) {
        var actual=replayFull(Objects.requireNonNull(originals));
        var history=history(actual.semantic(),includeHistory);
        return new FullSnapshotExport(originals,history.semantic(),history.mode(),history.totalCount(),history.includedCount());
    }
    private static DriverObservationAssembler.FullSnapshot replayFull(FullSnapshotOriginals originals) {
        var actual=originals.actual();var facts=actual.facts();
        var rebuiltFacts=DriverObservationEvidenceReader.decode(facts.semanticFactsEvidence(),originals.originalFacts(),
                originals.originalDriver(),actual.actual());
        require(rebuiltFacts.driverVersion()==facts.driverVersion() && rebuiltFacts.episodeEpoch()==facts.episodeEpoch()
                &&rebuiltFacts.publicRevision().equals(facts.publicRevision()) &&rebuiltFacts.observationVersion()==facts.observationVersion()
                &&rebuiltFacts.source().equals(facts.source()) &&rebuiltFacts.originalSemanticFields().equals(facts.originalSemanticFields())
                &&java.util.Arrays.equals(rebuiltFacts.driver().encode(),facts.driver().encode()),
                "full snapshot export crossed its exact native/Driver manifest, source or original producer version");
        var rebuilt=new DriverObservationAssembler().projectFull(actual.actual(),rebuiltFacts,actual.originalEvidence());
        require(rebuilt.semantic().equals(actual.semantic()) &&rebuilt.fullBindingSha256().equals(actual.fullBindingSha256()),
                "full snapshot export differs from the same original framed Native/Driver producer");
        return actual;
    }
    public static RawJson encode(SnapshotExport export) {
        Objects.requireNonNull(export);
        return switch(export) {
            case OrdinarySnapshotExport ordinary -> encodeOrdinary(ordinary);
            case FullSnapshotExport full -> encodeFullExport(full);
        };
    }
    private static RawJson encodeFullExport(FullSnapshotExport export) {
        var actual=replayFull(export.originals());
        var expected=exportFull(export.originals(),export.historyMode()==HistoryExportMode.FULL);
        require(expected.semantic().equals(export.semantic()) &&expected.totalCount()==export.totalCount()
                &&expected.includedCount()==export.includedCount(),"full snapshot history export differs from its actual source");
        boolean campaign=actual.facts().observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION;
        var semantic=export.semantic();validateOriginal(semantic,campaign);
        var diagnostics=object(semantic.get("diagnostics"),"diagnostics");
        if(diagnostics.members().containsKey("connection_generation") &&diagnostics.get("connection_generation")!=Nil.INSTANCE)
            require(integer(diagnostics.get("connection_generation"),"connection_generation").equals(actual.actual().session().connectionGeneration()),
                    "full snapshot diagnostic connection differs from its actual original transport");
        return publicValue(semantic,false,campaign);
    }
    private static RawJson encodeOrdinary(OrdinarySnapshotExport export) {
        var actual=export.actual();OrdinarySnapshotExport expected=export(actual,export.historyMode()==HistoryExportMode.FULL);
        require(expected.semantic().equals(export.semantic()) && expected.totalCount()==export.totalCount() && expected.includedCount()==export.includedCount(),"snapshot history export differs from its actual complete source");
        boolean campaign=nativeCampaign(actual);Obj semantic=export.semantic();validateOriginal(semantic,campaign);
        requireCompleteBinding(actual,semantic,campaign);
        return publicValue(semantic,false,campaign);
    }
    /** Only an actual version-4 Complete carrying its original framed projection can issue this representation.
     * The public marker is DATA; decoding it never constructs a Complete or admits a gameplay source. */
    private static boolean nativeCampaign(DriverObservationAssembler.Complete actual) {
        if(actual.identity().observationVersion()!=DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION)return false;
        var original=actual.originalProjection().orElseThrow(()->new IllegalArgumentException("native campaign Complete requires its actual original projection"));
        require(original.facts().observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION,
                "native campaign projection crossed its actual observation profile");
        var rebuilt=new DriverObservationAssembler().assemble(original.actual(),original.facts(),original.originalEvidence());
        require(rebuilt instanceof DriverObservationAssembler.Complete,"native campaign original no longer produces its actual Complete");
        var same=(DriverObservationAssembler.Complete)rebuilt;
        require(same.identity().equals(actual.identity()) &&same.source().equals(actual.source())
                &&same.sessionId().equals(actual.sessionId()) &&same.connectionGeneration().equals(actual.connectionGeneration())
                &&same.semantic().equals(actual.semantic()) &&same.originalEvidence().equals(actual.originalEvidence())
                &&same.observedAt().equals(actual.observedAt()) &&same.fullBindingSha256().equals(actual.fullBindingSha256()),
                "native campaign public export differs from its original framed Native/Driver producer");
        return true;
    }
    private static void requireCompleteBinding(DriverObservationAssembler.Complete actual,Obj semantic,boolean campaign) {
        require(text(semantic.get("snapshot_id"),"snapshot_id").equals(actual.identity().frame().snapshotId())
                && integer(semantic.get("revision"),"revision").equals(actual.identity().frame().revision())
                && integer(semantic.get("native_revision"),"native_revision").equals(actual.identity().frame().identity().nativeRevision())
                && integer(semantic.get("date_raw"),"date_raw").equals(actual.identity().frame().identity().dateRaw())
                && (campaign ||text(semantic.get("episode_run_id"),"episode_run_id").equals(actual.identity().frame().episodeRunId())),"public snapshot crossed actual Complete identity");
        Obj diagnostics=object(semantic.get("diagnostics"),"diagnostics");
        if(diagnostics.members().containsKey("connection_generation") && diagnostics.get("connection_generation")!=Nil.INSTANCE)
            require(integer(diagnostics.get("connection_generation"),"connection_generation").equals(actual.connectionGeneration()),"snapshot diagnostic connection differs from actual Complete");
    }
    /** Actual FullSnapshot terminal scope, without constructing an ordinary gameplay identity. Root owns physical source admission. */
    public static RawJson encodeTerminal(DriverObservationAssembler.FullSnapshot actual,LifecycleIdentity source,boolean includeHistory) {
        Obj semantic=terminalSemantic(actual,source);
        return publicValue(history(semantic,includeHistory).semantic());
    }
    /** Source-qualified terminal semantic DATA; all transcript roots are absent, including after UNKNOWN. */
    public static RawJson exportSemanticOnly(DriverObservationAssembler.FullSnapshot actual,LifecycleIdentity source) {
        var fields=new LinkedHashMap<>(terminalSemantic(actual,source).members());TRANSCRIPT_FIELDS.forEach(fields::remove);
        Obj semantic=new Obj(fields);validateSemanticOnly(semantic);return publicValue(semantic,true);
    }
    private static Obj terminalSemantic(DriverObservationAssembler.FullSnapshot actual,LifecycleIdentity source) {
        Objects.requireNonNull(actual);Objects.requireNonNull(source);
        var rebuilt=new DriverObservationAssembler().projectFull(actual.actual(),actual.facts(),actual.originalEvidence());
        require(rebuilt.semantic().equals(actual.semantic()) && rebuilt.fullBindingSha256().equals(actual.fullBindingSha256()),"terminal snapshot differs from its original framed Native/Driver producer");
        var projected=LifecycleOriginFactory.project(actual,source.evidence().helloPacket(),source.evidence().originalDriver(),source.evidence().completeSourceQualification());
        require(projected instanceof LifecycleOriginFactory.Projected,"actual terminal source cannot be derived from this FullSnapshot");
        require(((LifecycleOriginFactory.Projected)projected).identity().equals(source),"terminal snapshot crossed original lifecycle identity/evidence");
        Obj semantic=actual.semantic();validateOriginal(semantic);
        Obj diagnostics=object(semantic.get("diagnostics"),"diagnostics");
        if(diagnostics.members().containsKey("connection_generation") && diagnostics.get("connection_generation")!=Nil.INSTANCE)
            require(integer(diagnostics.get("connection_generation"),"connection_generation").equals(source.connectionGeneration()),"terminal diagnostic connection differs from actual source");
        return semantic;
    }
    private static RawJson publicValue(Obj semantic) {
        return publicValue(semantic,false);
    }
    private static RawJson publicValue(Obj semantic,boolean semanticOnly) {
        return publicValue(semantic,semanticOnly,false);
    }
    private static RawJson publicValue(Obj semantic,boolean semanticOnly,boolean campaign) {
        require(!semantic.members().containsKey(PROJECTION_FIELD),"public snapshot representation metadata is reserved");
        ObjectNode publicTree=node(semantic);
        if(campaign)publicTree.putObject(PROJECTION_FIELD).put("schema",PROJECTION_SCHEMA)
                .put("observation_version",DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION);
        factionSemantic(publicTree,true);
        for(List<String> path:IDENTITY_PATHS)transform(publicTree,path,true);
        battleControlCache(publicTree,true);armyCoreCache(publicTree,true);
        readHistory(publicTree,true);
        observedHistory(publicTree,true);
        failedReadHistory(publicTree);
        armySummaryHistory(publicTree,true);
        executeQueryHistory(publicTree,true);
        returnedControlHistory(publicTree,true);publicExecuteFailureHistory(publicTree,true);returnedActionHistory(publicTree,true);returnedPublicReadHistory(publicTree,true);earlyExecuteFailureHistory(publicTree,true);postKnownReadFailureHistory(publicTree);
        actionHistory(publicTree,true);
        lifecycleHistory(publicTree,true);
        lifecycleState(publicTree,true);
        rejectedSnapshotDiagnostics(publicTree,true);
        publicNumbers(publicTree,"");RawJson result=PublicDataJson.encodePreservingFullMaterial(publicTree,RawJson.fullMaterial(DriverJson.encode(semantic)));
        if(semanticOnly)require(result.bytes().length<=SEMANTIC_MAXIMUM_BYTES,"private semantic snapshot exceeds the 8 MiB UTF-8 read bound");
        require((semanticOnly?decodeSemanticOnly(result):decode(result)).equals(semantic),"public snapshot serialization roundtrip changed original JSON type/domain/decimal token");return result;
    }
    /** Pure original Driver-snapshot DATA conversion for a retained report field.
     * Shape/roles only: this cannot construct SnapshotExport, Complete, a lifecycle identity or any live authority. */
    public static RawJson encodeSemanticData(RawJson originalNumeric) {
        Objects.requireNonNull(originalNumeric);
        Obj original=DriverJson.object(originalNumeric.bytes(),RawJson.MAXIMUM_BYTES);
        validateOriginal(original);
        return publicValue(original);
    }
    /** Restores the same source-owned number roles and all original history fields; grants no original-source custody. */
    public static RawJson decodeSemanticData(RawJson canonicalPublic) {
        return RawJson.fullMaterial(DriverJson.encode(decode(Objects.requireNonNull(canonicalPublic))));
    }
    /** Pure PLAN snapshot DATA: explicit original history or the original three-transcript-keys-absent lane. */
    public static RawJson encodePlanningSnapshotData(RawJson originalNumeric) {
        Obj original=DriverJson.object(Objects.requireNonNull(originalNumeric).bytes(),RawJson.MAXIMUM_BYTES);
        boolean semanticOnly=!original.members().containsKey("native_command_history");
        if(semanticOnly)validateSemanticOnly(original);else validateOriginal(original);
        return publicValue(original,semanticOnly);
    }
    public static RawJson decodePlanningSnapshotData(RawJson canonicalPublic) {
        Obj original=DriverJson.object(Objects.requireNonNull(canonicalPublic).bytes(),RawJson.MAXIMUM_BYTES);
        return RawJson.fullMaterial(DriverJson.encode(decodePublic(canonicalPublic,!original.members().containsKey("native_command_history"))));
    }
    /** Finite recorder DATA only; this never constructs or admits a Snapshot, observation or source proof. */
    public static Arr encodePlanningHistoryData(Arr originalNumericRows) {
        Arr converted=planningHistoryData(Objects.requireNonNull(originalNumericRows),true);
        require(decodePlanningHistoryData(converted).equals(originalNumericRows),"PLAN history public serialization changed original types or decimal tokens");
        return converted;
    }
    public static Arr decodePlanningHistoryData(Arr canonicalPublicRows) {
        return planningHistoryData(Objects.requireNonNull(canonicalPublicRows),false);
    }
    private static Arr planningHistoryData(Arr original,boolean encode) {
        Obj container=new Obj(Map.of("native_command_history",original));ObjectNode tree=node(container);
        if(!encode)publicNumbers(tree,"");
        readHistory(tree,encode);observedHistory(tree,encode);failedReadHistory(tree);armySummaryHistory(tree,encode);executeQueryHistory(tree,encode);returnedControlHistory(tree,encode);publicExecuteFailureHistory(tree,encode);returnedActionHistory(tree,encode);returnedPublicReadHistory(tree,encode);earlyExecuteFailureHistory(tree,encode);postKnownReadFailureHistory(tree);
        actionHistory(tree,encode);lifecycleHistory(tree,encode);
        if(encode)publicNumbers(tree,"");
        RawJson converted=PublicDataJson.encodePreservingFullMaterial(tree,RawJson.fullMaterial(DriverJson.encode(container)));
        return new Arr(array(DriverJson.object(converted.bytes(),RawJson.MAXIMUM_BYTES).get("native_command_history"),"actual PLAN history rows"));
    }
    /** Public parser restores only the exact roles encoded above; unknown strings never become integers. */
    public static Obj decode(RawJson publicJson) {
        return decodePublic(publicJson,false);
    }
    /** Shared typed decoder for semantic-only roundtrip/tests. It does not admit a Root/source or a transcript-bearing snapshot. */
    static Obj decodeSemanticOnly(RawJson publicJson) {
        return decodePublic(publicJson,true);
    }
    private static Obj decodePublic(RawJson publicJson,boolean semanticOnly) {
        Objects.requireNonNull(publicJson);
        if(semanticOnly)require(publicJson.bytes().length<=SEMANTIC_MAXIMUM_BYTES,"private semantic snapshot exceeds the 8 MiB UTF-8 read bound");
        ObjectNode tree=node(DriverJson.object(publicJson.bytes(),RawJson.MAXIMUM_BYTES));publicNumbers(tree,"");
        JsonNode marker=tree.remove(PROJECTION_FIELD);boolean campaign=marker!=null;
        if(campaign) {
            require(marker instanceof ObjectNode,"explicit public snapshot projection object required");
            ObjectNode projection=(ObjectNode)marker;
            require(projection.size()==2 &&projection.path("schema").isTextual() &&PROJECTION_SCHEMA.equals(projection.path("schema").textValue())
                    &&projection.path("observation_version").isIntegralNumber()
                    &&projection.path("observation_version").bigIntegerValue().equals(BigInteger.valueOf(DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION)),
                    "unsupported public snapshot projection representation");
        }
        if(semanticOnly)for(String field:TRANSCRIPT_FIELDS)require(!tree.has(field),"private semantic snapshot contains transcript field: "+field);
        for(List<String> path:IDENTITY_PATHS)transform(tree,path,false);
        factionSemantic(tree,false);
        battleControlCache(tree,false);armyCoreCache(tree,false);
        readHistory(tree,false);
        observedHistory(tree,false);
        failedReadHistory(tree);
        armySummaryHistory(tree,false);
        executeQueryHistory(tree,false);
        returnedControlHistory(tree,false);publicExecuteFailureHistory(tree,false);returnedActionHistory(tree,false);returnedPublicReadHistory(tree,false);earlyExecuteFailureHistory(tree,false);postKnownReadFailureHistory(tree);
        actionHistory(tree,false);
        lifecycleHistory(tree,false);
        lifecycleState(tree,false);
        rejectedSnapshotDiagnostics(tree,false);
        Obj semantic=DriverJson.object(PublicDataJson.encodePreservingFullMaterial(tree,publicJson).bytes(),RawJson.MAXIMUM_BYTES);
        if(semanticOnly)validateSemanticOnly(semantic,campaign);else validateOriginal(semantic,campaign);return semantic;
    }
    private static void validateOriginal(Obj semantic) {
        validateOriginal(semantic,false);
    }
    private static void validateOriginal(Obj semantic,boolean campaign) {
        validateBase(semantic,campaign);require(semantic.members().containsKey("native_command_history"),"explicit original snapshot field required: native_command_history");
        array(semantic.get("native_command_history"),"native_command_history");
    }
    private static void validateSemanticOnly(Obj semantic) {
        validateSemanticOnly(semantic,false);
    }
    private static void validateSemanticOnly(Obj semantic,boolean campaign) {
        validateBase(semantic,campaign);for(String field:TRANSCRIPT_FIELDS)require(!semantic.members().containsKey(field),"private semantic snapshot contains transcript field: "+field);
    }
    private static void validateBase(Obj semantic,boolean campaign) {
        require(!semantic.members().containsKey(PROJECTION_FIELD),"public snapshot representation metadata is reserved");
        if(campaign)require(text(semantic.get("episode_projection"),"episode_projection").equals("native_campaign"),"actual native campaign projection required");
        require(BigInteger.ONE.equals(integer(semantic.get("format_version"),"format_version")),"original snapshot format version required");
        require(!text(semantic.get("snapshot_id"),"snapshot_id").isBlank() && integer(semantic.get("revision"),"revision").signum()>=0
                && integer(semantic.get("native_revision"),"native_revision").signum()>0,"original snapshot identity required");
        integer(semantic.get("date_raw"),"date_raw");bool(semantic.get("paused"),"paused");bool(semantic.get("map_ready"),"map_ready");
        int speed=integer(semantic.get("speed"),"speed").intValueExact();require(speed>=1 && speed<=5,"actual native speed 1..5 required");
        if(!campaign) {
            require(!text(semantic.get("episode_run_id"),"episode_run_id").isBlank(),"actual episode required");NativeCharacterId.of(integer(semantic.get("episode_character_id"),"episode_character_id"));
        }
        // Original Native terminal snapshots preserve absent/null played_character. Parsing DATA grants no gameplay admission.
        if(semantic.members().containsKey("played_character") && semantic.get("played_character")!=Nil.INSTANCE) {
            Obj player=object(semantic.get("played_character"),"played_character");NativeCharacterId.of(integer(player.get("character_id"),"character_id"));bool(player.get("alive"),"alive");
        }
        array(semantic.get("active_wars"),"active_wars");array(semantic.get("player_armies"),"player_armies");object(semantic.get("diagnostics"),"diagnostics");
        for(String field:campaign?List.of("active_event","pending_character_interaction"):List.of("active_event","pending_character_interaction","one_life_terminal_reason"))require(semantic.members().containsKey(field),"explicit original snapshot field required: "+field);
    }
    /** The same source-owned faction body codec is used by query/execute and the semantic snapshot slot.
     * Exact numeric expected frame and Available actor binding are DATA checks, never original-source custody.
     */
    private static void factionSemantic(ObjectNode snapshot,boolean encode) {
        String field=DriverSemanticReadState.FACTION_ALERTS_FIELD;
        JsonNode value=snapshot.get(field);if(value==null||value.isNull())return;
        require(value instanceof ObjectNode,"faction semantic payload must be an explicit object or null");
        var expected=new FactionAlertModel.ExpectedFrame(
                (int)StrictJson.integer(snapshot.get("date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE),
                StrictJson.integer(snapshot.get("native_revision"),BigInteger.ZERO,StrictJson.UINT64_MAX),java.util.Optional.empty());
        RawJson original=new RawJson(StrictJson.canonical(value,FactionAlertsCodec.MAX_BYTES));
        RawJson publicBody=encode?FactionReadReplay.encodeSemanticBody(original,expected):original;
        RawJson numeric=encode?original:FactionReadReplay.decodeSemanticBody(original,expected);
        JsonNode checked=StrictJson.parse(numeric.bytes(),FactionAlertsCodec.MAX_BYTES);
        if("available".equals(checked.path("status").textValue())) {
            JsonNode player=snapshot.get("played_character");
            require(player instanceof ObjectNode,"available faction semantic payload requires the same actual player");
            require(NativeCharacterId.fromJson(player.get("character_id")).asBigInteger()
                    .equals(StrictJson.integer(checked.get("player_character_id"),BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE))),
                    "faction semantic payload crossed the containing snapshot actor");
        }
        snapshot.set(field,StrictJson.parse((encode?publicBody:numeric).bytes(),FactionAlertsCodec.MAX_BYTES));
    }
    private static void transform(ObjectNode root,List<String> path,boolean encode) {
        transform(root,path,encode,path.size()>1);
    }
    private static void transform(ObjectNode root,List<String> path,boolean encode,boolean uint64) {
        ObjectNode parent=root;
        for(int i=0;i<path.size()-1;i++) {JsonNode next=parent.get(path.get(i));if(next==null || next.isNull())return;require(next instanceof ObjectNode,"identity parent object required: "+String.join("/",path));parent=(ObjectNode)next;}
        String leaf=path.getLast();JsonNode value=parent.get(leaf);
        if(value==null || value.isNull()) {require(path.size()>1,"required snapshot identity absent or null: "+leaf);return;}
        if(encode) {require(value.isIntegralNumber() && value.bigIntegerValue().signum()>=0,"exact nonnegative identity integer required: "+leaf);
            require(!uint64 || value.bigIntegerValue().bitLength()<=64,"source uint64 role out of range: "+String.join("/",path));parent.put(leaf,value.bigIntegerValue().toString());}
        else {require(value.isTextual() && value.textValue().matches("0|[1-9][0-9]*") && value.textValue().length()<=4300,"canonical decimal identity string required: "+leaf);
            BigInteger exact=new BigInteger(value.textValue());require(!uint64 || exact.bitLength()<=64,"source uint64 role out of range: "+String.join("/",path));parent.put(leaf,exact);}
    }
    /** Only the closed eleven-field Core producer owns these snapshot number roles. */
    private static void armyCoreCache(ObjectNode snapshot,boolean encode) {
        var keys=ArmyStrengthsReadValue.SNAPSHOT_FIELDS;long present=keys.stream().filter(snapshot::has).count();
        if(present==0)return;require(present==keys.size(),"complete Army Core cache slots required");
        var slice=StrictJson.object();for(String key:keys)slice.set(key,snapshot.get(key));
        if(slice.get("army_strengths_status").isNull()){
            require(DriverJson.object(PublicDataJson.encodeFullMaterial(slice).bytes(),RawJson.MAXIMUM_BYTES).equals(ArmyStrengthsReadValue.cleared()),"invalid cleared Army Core cache");return;
        }
        if(!encode){positiveRole(slice,List.of("army_strengths_query_sequence"),false);transform(slice,List.of("army_strengths_queried_revision"),false,false);corePowers(slice,false);}
        Obj numeric=DriverJson.object(PublicDataJson.encodeFullMaterial(slice).bytes(),RawJson.MAXIMUM_BYTES);
        require(text(numeric.get("army_strengths_profile"),"profile").equals("ordinary_core_v1")
                &&text(numeric.get("army_observed_phase_coverage"),"coverage").equals("not_requested")
                &&!text(numeric.get("army_strengths_queried_snapshot_id"),"snapshot").isBlank()
                &&integer(numeric.get("army_strengths_queried_revision"),"revision").signum()>=0,"ordinary Core cache binding required");
        var rows=array(numeric.get("army_strengths"),"Core rows").stream().map(row->object(row,"Core row")).toList();
        new ArmyStrengthsReadValue.CoreProjection(ArmyRequests.StrengthProfile.ORDINARY_CORE_V1,ArmyStrengthsReadValue.Scope.FULL_PUBLISHED,
                ArmyTypes.Availability.valueOf(text(numeric.get("army_strengths_status"),"status").toUpperCase(java.util.Locale.ROOT)),
                integer(numeric.get("army_strengths_query_sequence"),"sequence"),rows);
        if(encode){positiveRole(slice,List.of("army_strengths_query_sequence"),true);transform(slice,List.of("army_strengths_queried_revision"),true,false);corePowers(slice,true);}
        for(String key:keys)snapshot.set(key,slice.get(key));
    }
    private static void corePowers(ObjectNode slice,boolean encode) {
        JsonNode rows=slice.get("army_strengths");require(rows.isArray(),"Core rows required");
        for(JsonNode item:rows){require(item instanceof ObjectNode,"Core row required");ObjectNode row=(ObjectNode)item;
            JsonNode power=row.get("ai_base_power_raw");require(power!=null,"Core power slot required");if(power.isNull())continue;
            if(encode){require(power.isIntegralNumber(),"exact Core signed64 required");power.bigIntegerValue().longValueExact();row.put("ai_base_power_raw",power.bigIntegerValue().toString());}
            else{require(power.isTextual()&&power.textValue().matches("0|-?[1-9][0-9]*")&&power.textValue().length()<=20,"canonical Core signed64 required");
                BigInteger value=new BigInteger(power.textValue());require(value.bitLength()<=63,"Core signed64 width");value.longValueExact();row.put("ai_base_power_raw",value);}
        }
    }
    /** Original fixed BattleControl cache DATA, with the same scalar roles as its ordinary public query. */
    private static void battleControlCache(ObjectNode snapshot,boolean encode) {
        long count=BattleControlSemanticProjection.fields().stream().filter(snapshot::has).count();
        if(count==0)return; // Retained snapshots from before this cache family remain unchanged.
        require(count==BattleControlSemanticProjection.fields().size(),"complete original BattleControl cache slots required");
        for(String key:List.of("battle_control_snapshot_v1_query_sequence","battle_control_snapshot_v1_queried_native_revision"))
            if(!snapshot.get(key).isNull())positiveRole(snapshot,List.of(key),encode);
        String revision="battle_control_snapshot_v1_queried_revision";
        if(!snapshot.get(revision).isNull())transform(snapshot,List.of(revision),encode,false);
        ObjectNode payload=StrictJson.object();
        for(String key:List.of("battle_control_snapshot_v1","active_combat_resume_inputs_v1"))payload.set(key,snapshot.get(key));
        Obj original=DriverJson.object(PublicDataJson.encodeFullMaterial(payload).bytes(),RawJson.MAXIMUM_BYTES);
        Obj converted=encode?ArmyPublicWire.encodeBattleControlCache(original):ArmyPublicWire.decodeBattleControlCache(original);
        converted.members().forEach((key,value)->snapshot.set(key,OpportunityJson.toNode(value)));
    }

    /** Only the unique source-owned read row parser selects these roles; unrelated arguments/results remain open and exact. */
    private static void readHistory(ObjectNode snapshot,boolean encode) {
        JsonNode history=snapshot.get("native_command_history");if(history==null)return;require(history.isArray(),"original history array required");
        for(JsonNode value:history) {
            if(!(value instanceof ObjectNode row))continue;
            if(!row.has(DriverReadHistoryRowProducer.SOURCE_FIELD))continue;
            require(!row.has(DriverObservedHistoryRowProducer.SOURCE_FIELD),"one exact history source family required");
            var source=row.get(DriverReadHistoryRowProducer.SOURCE_FIELD);require(source!=null&&source.isObject()&&source.path("kind").isTextual(),"explicit typed read history source required");
            var kind=DriverReadHistoryRowProducer.Kind.valueOf(source.get("kind").textValue());
            require(source.path("schema").isTextual()&&DriverReadHistoryRowProducer.sourceSchema(kind).equals(source.get("schema").textValue()),"unsupported original read history source schema");
            if(encode)require(DriverReadHistoryRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes()).provenance().kind()==kind,"original read source kind changed");
            // Rich result roles already include queried/query-sequence identities. Never apply the legacy result conversion first.
            if(kind.isRich()) {
                var roles=DriverReadHistoryRowProducer.publicNumbersFromSource(DriverJson.object(PublicDataJson.encodeFullMaterial(source).bytes(),RawJson.MAXIMUM_BYTES));
                require(row.get("result") instanceof ObjectNode,"complete original rich Driver result required");
                Obj result=DriverJson.object(PublicDataJson.encodeFullMaterial(row.get("result")).bytes(),RawJson.MAXIMUM_BYTES);
                row.set("result",node(encode?roles.toPublic(result):roles.fromPublic(result)));
            } else {
                transform(row,List.of("result","queried_revision"),encode,false);transform(row,List.of("result","queried_native_revision"),encode,false);
                if(kind.hasQuerySequence())transform(row,List.of("result","query_sequence"),encode,true);
                if(kind.requiresExplicitEpisodeConnection())transform(row,List.of("result","queried_connection_generation"),encode,true);
                if(kind==DriverReadHistoryRowProducer.Kind.CAMPAIGN_ROOT_CONTEXT)rootHistory(row,encode);
                else if(kind==DriverReadHistoryRowProducer.Kind.PROJECTED_CONTACT_SCOPE||kind==DriverReadHistoryRowProducer.Kind.ACTUAL_CONTACT_SCOPE)contactHistory(row,kind,encode);
            }
            transform(row,List.of(DriverReadHistoryRowProducer.SOURCE_FIELD,"connection_generation"),encode,true);
            if(kind.hasQuerySequence())transform(row,List.of(DriverReadHistoryRowProducer.SOURCE_FIELD,"query_sequence"),encode,true);
            if(!encode)DriverReadHistoryRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
        }
    }
    /** The original typed contact producer alone proves both mandatory native revision roles. */
    private static void contactHistory(ObjectNode row,DriverReadHistoryRowProducer.Kind kind,boolean encode) {
        require(row.get("result") instanceof ObjectNode,"actual typed contact result required");
        ObjectNode result=(ObjectNode)row.get("result");
        positiveRole(result,List.of("snapshot_revision"),encode);
        positiveRole(result,List.of(kind.payloadField(),"snapshot_revision"),encode);
    }
    /** Only a typed public ROOT row selects these mandatory native uint64 roles. */
    private static void rootHistory(ObjectNode row,boolean encode) {
        require(row.get("result") instanceof ObjectNode,"actual ROOT result required");
        ObjectNode result=(ObjectNode)row.get("result");
        require(result.get("campaign_root_context") instanceof ObjectNode,"actual ROOT payload required");
        ObjectNode root=(ObjectNode)result.get("campaign_root_context");
        if(encode){require(!row.has(OPTIONAL_HEIR_ENCODING),"original ROOT row collides with reserved public optional identity metadata");rootOptional(row,root,true);}
        positiveRole(result,List.of("snapshot_revision"),encode);
        positiveRole(result,List.of("campaign_root_context","snapshot_revision"),encode);
        if(!encode)rootOptional(row,root,false);
    }
    private static void rootOptional(ObjectNode row,ObjectNode root,boolean encode) {
        String component="player_heir_candidate_v1";
        boolean marked=row.has(OPTIONAL_HEIR_ENCODING);
        if(!encode&&marked)require(row.get(OPTIONAL_HEIR_ENCODING).isTextual()&&List.of(OPTIONAL_HEIR_DECIMAL,OPTIONAL_HEIR_RAW).contains(row.get(OPTIONAL_HEIR_ENCODING).textValue()),"unsupported public optional ROOT revision encoding");
        JsonNode value=root.get(component);
        if(!(value instanceof ObjectNode optional)){require(!marked,"public optional revision metadata has no actual component");return;}
        if(!encode)require(marked,"object optional ROOT component requires explicit public DATA encoding branch");
        boolean decimal=!encode&&OPTIONAL_HEIR_DECIMAL.equals(row.get(OPTIONAL_HEIR_ENCODING).textValue());
        ObjectNode trial=optional.deepCopy();
        if(decimal)positiveRole(trial,List.of("snapshot_revision"),false);
        boolean typed=NativePlayerHeirObservation12004.parseOptionalComponent(trial,root).observation()!=null;
        if(!encode){
            require(decimal==typed,"public optional ROOT revision must carry its exact typed representation metadata");
            if(decimal)positiveRole(optional,List.of("snapshot_revision"),false);
            row.remove(OPTIONAL_HEIR_ENCODING);
            return;
        }
        // A syntactically proved component can still have UNKNOWN business status or be unbound.
        // Malformed text that resembles an integer must not become a typed role during decode.
        if(typed)positiveRole(optional,List.of("snapshot_revision"),true);
        row.put(OPTIONAL_HEIR_ENCODING,typed?OPTIONAL_HEIR_DECIMAL:OPTIONAL_HEIR_RAW);
    }
    private static void positiveRole(ObjectNode root,List<String> path,boolean encode) {
        ObjectNode parent=root;
        for(int index=0;index<path.size()-1;index++){
            require(parent.get(path.get(index)) instanceof ObjectNode,"required ROOT revision parent absent");
            parent=(ObjectNode)parent.get(path.get(index));
        }
        JsonNode value=parent.get(path.getLast());require(value!=null&&!value.isNull(),"required ROOT uint64 revision absent or null");
        transform(root,path,encode,true);
        JsonNode projected=parent.get(path.getLast());BigInteger exact=encode?new BigInteger(projected.textValue()):projected.bigIntegerValue();
        require(exact.signum()>0&&exact.compareTo(StrictJson.UINT64_MAX)<=0,"positive ROOT uint64 revision required");
    }
    /** Logical Gift observations retain their sole typed source and owning business serializer. */
    private static void observedHistory(ObjectNode snapshot,boolean encode) {
        JsonNode history=snapshot.get("native_command_history");if(history==null)return;
        require(history.isArray(),"original observed history array required");
        for(JsonNode value:history) {
            if(!(value instanceof ObjectNode row)||!row.has(DriverObservedHistoryRowProducer.SOURCE_FIELD))continue;
            require(!row.has(DriverReadHistoryRowProducer.SOURCE_FIELD),"one exact history source family required");
            if(encode)DriverObservedHistoryRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
            else require(row.path(DriverObservedHistoryRowProducer.SOURCE_FIELD).path("schema").isTextual()
                    &&DriverObservedHistoryRowProducer.SOURCE_SCHEMA.equals(row.path(DriverObservedHistoryRowProducer.SOURCE_FIELD).path("schema").textValue()),"unsupported observed history source schema");
            require(row.get("result") instanceof ObjectNode,"actual observed business result required");
            var original=PublicDataJson.encodeFullMaterial(row.get("result"));
            RawJson converted=encode?FactionGiftPublicCodec.businessPublic(FactionGiftPublicContract.Method.RESOLVED,original)
                    :FactionGiftPublicCodec.businessNative(FactionGiftPublicContract.Method.RESOLVED,original);
            row.set("result",PublicDataJson.object(converted));
            // Source.frame is already encoded by ProposalLifecycleCodec; never infer numeric roles from its keys.
            if(!encode)DriverObservedHistoryRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
        }
    }
    /** Compact Army history has its own source schema; result roles come only from the fixed owning summary projection. */
    private static void armySummaryHistory(ObjectNode snapshot,boolean encode) {
        JsonNode history=snapshot.get("native_command_history");if(history==null)return;
        require(history.isArray(),"original compact Army history array required");
        for(JsonNode value:history) {
            if(!(value instanceof ObjectNode row)||!row.has(DriverArmySummaryHistoryRowProducer.SOURCE_FIELD))continue;
            if(encode)DriverArmySummaryHistoryRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
            var source=DriverJson.object(PublicDataJson.encodeFullMaterial(row.get(DriverArmySummaryHistoryRowProducer.SOURCE_FIELD)).bytes(),RawJson.MAXIMUM_BYTES);
            var roles=DriverArmySummaryHistoryRowProducer.publicNumbersFromSource(source);
            require(row.get("result") instanceof ObjectNode,"complete original compact Army result required");
            Obj result=DriverJson.object(PublicDataJson.encodeFullMaterial(row.get("result")).bytes(),RawJson.MAXIMUM_BYTES);
            row.set("result",node(encode?roles.toPublic(result):roles.fromPublic(result)));
            // Source.frame/source are already encoded by ProposalLifecycleCodec; only these two source counters are numeric.
            transform(row,List.of(DriverArmySummaryHistoryRowProducer.SOURCE_FIELD,"connection_generation"),encode,true);
            transform(row,List.of(DriverArmySummaryHistoryRowProducer.SOURCE_FIELD,"query_sequence"),encode,true);
            if(!encode)DriverArmySummaryHistoryRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
        }
    }
    /** Source-owned finite public execute-query result roles, independent of ordinary and Army read schemas. */
    private static void executeQueryHistory(ObjectNode snapshot,boolean encode) {
        JsonNode history=snapshot.get("native_command_history");if(history==null)return;
        require(history.isArray(),"original execute-query history array required");
        for(JsonNode value:history) {
            if(!(value instanceof ObjectNode row)||!row.has(DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD))continue;
            if(encode)DriverExecuteQueryHistoryRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
            Obj source=DriverJson.object(PublicDataJson.encodeFullMaterial(row.get(DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD)).bytes(),RawJson.MAXIMUM_BYTES);
            var roles=DriverExecuteQueryHistoryRowProducer.publicNumbersFromSource(source);
            require(row.get("result") instanceof ObjectNode,"complete finite execute-query result required");
            Obj result=DriverJson.object(PublicDataJson.encodeFullMaterial(row.get("result")).bytes(),RawJson.MAXIMUM_BYTES);
            row.set("result",node(encode?roles.toPublic(result):roles.fromPublic(result)));
            transform(row,List.of(DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD,"connection_generation"),encode,true);
            require(source.members().containsKey("query_sequence"),"explicit original query sequence or null required");
            if(source.get("query_sequence")!=Nil.INSTANCE)transform(row,List.of(DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD,"query_sequence"),encode,true);
            if(!encode)DriverExecuteQueryHistoryRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
        }
    }
    /** Original false RETURNED control reports remain history DATA; they are not thrown errors or action settlement. */
    private static void returnedControlHistory(ObjectNode snapshot,boolean encode) {
        JsonNode history=snapshot.get("native_command_history");if(history==null)return;
        require(history.isArray(),"original returned-control history array required");
        for(JsonNode value:history){
            if(!(value instanceof ObjectNode row)||!row.has(DriverReturnedControlHistoryRowProducer.SOURCE_FIELD))continue;
            if(encode)DriverReturnedControlHistoryRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
            Obj source=DriverJson.object(PublicDataJson.encodeFullMaterial(row.get(DriverReturnedControlHistoryRowProducer.SOURCE_FIELD)).bytes(),RawJson.MAXIMUM_BYTES);
            var roles=DriverReturnedControlHistoryRowProducer.publicNumbersFromSource(source);
            require(row.get("result") instanceof ObjectNode,"original complete returned-control report required");
            Obj result=DriverJson.object(PublicDataJson.encodeFullMaterial(row.get("result")).bytes(),RawJson.MAXIMUM_BYTES);
            row.set("result",node(encode?roles.toPublic(result):roles.fromPublic(result)));
            if(!encode)DriverReturnedControlHistoryRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
        }
    }
    /** Failed public execute rows use only the owning producer's optional typed result and exact number roles. */
    private static void publicExecuteFailureHistory(ObjectNode snapshot,boolean encode) {
        JsonNode history=snapshot.get("native_command_history");if(history==null)return;
        require(history.isArray(),"original public execute failure history array required");
        for(JsonNode value:history){
            if(!(value instanceof ObjectNode row)||!row.has(DriverPublicExecuteFailureRowProducer.SOURCE_FIELD))continue;
            if(encode)DriverPublicExecuteFailureRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
            Obj source=DriverJson.object(PublicDataJson.encodeFullMaterial(row.get(DriverPublicExecuteFailureRowProducer.SOURCE_FIELD)).bytes(),RawJson.MAXIMUM_BYTES);
            var roles=DriverPublicExecuteFailureRowProducer.publicNumbersFromSource(source);
            if(row.has("result")){
                require(row.get("result") instanceof ObjectNode&&roles.isPresent(),"original failed execute result requires its source-owned roles");
                Obj result=DriverJson.object(PublicDataJson.encodeFullMaterial(row.get("result")).bytes(),RawJson.MAXIMUM_BYTES);
                row.set("result",node(encode?roles.orElseThrow().toPublic(result):roles.orElseThrow().fromPublic(result)));
            }else require(roles.isEmpty(),"absent failed execute result cannot invent number roles");
            if(!encode)DriverPublicExecuteFailureRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
        }
    }
    private static void returnedActionHistory(ObjectNode snapshot,boolean encode) {
        JsonNode history=snapshot.get("native_command_history");if(history==null)return;
        require(history.isArray(),"original returned-control history array required");
        for(JsonNode value:history){
            if(!(value instanceof ObjectNode row)||!row.has(DriverReturnedActionHistoryRowProducer.SOURCE_FIELD))continue;
            if(encode)DriverReturnedActionHistoryRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
            Obj source=DriverJson.object(PublicDataJson.encodeFullMaterial(row.get(DriverReturnedActionHistoryRowProducer.SOURCE_FIELD)).bytes(),RawJson.MAXIMUM_BYTES);
            var roles=DriverReturnedActionHistoryRowProducer.publicNumbersFromSource(source);
            require(row.get("result") instanceof ObjectNode,"original complete returned-control report required");
            Obj result=DriverJson.object(PublicDataJson.encodeFullMaterial(row.get("result")).bytes(),RawJson.MAXIMUM_BYTES);
            row.set("result",node(encode?roles.toPublic(result):roles.fromPublic(result)));
            if(!encode)DriverReturnedActionHistoryRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
        }
    }
    private static void returnedPublicReadHistory(ObjectNode snapshot,boolean encode) {
        JsonNode history=snapshot.get("native_command_history");if(history==null)return;
        require(history.isArray(),"original returned-control history array required");
        for(JsonNode value:history){
            if(!(value instanceof ObjectNode row)||!row.has(DriverReturnedPublicReadHistoryRowProducer.SOURCE_FIELD))continue;
            if(encode)DriverReturnedPublicReadHistoryRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
            Obj source=DriverJson.object(PublicDataJson.encodeFullMaterial(row.get(DriverReturnedPublicReadHistoryRowProducer.SOURCE_FIELD)).bytes(),RawJson.MAXIMUM_BYTES);
            var roles=DriverReturnedPublicReadHistoryRowProducer.publicNumbersFromSource(source);
            require(row.get("result") instanceof ObjectNode,"original complete returned-control report required");
            Obj result=DriverJson.object(PublicDataJson.encodeFullMaterial(row.get("result")).bytes(),RawJson.MAXIMUM_BYTES);
            row.set("result",node(encode?roles.toPublic(result):roles.fromPublic(result)));
            if(!encode)DriverReturnedPublicReadHistoryRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
        }
    }
    private static void earlyExecuteFailureHistory(ObjectNode snapshot,boolean encode) {
        JsonNode history=snapshot.get("native_command_history");if(history==null)return;
        require(history.isArray(),"original public execute failure history array required");
        for(JsonNode value:history){
            if(!(value instanceof ObjectNode row)||!row.has(DriverEarlyExecuteFailureRowProducer.SOURCE_FIELD))continue;
            if(encode)DriverEarlyExecuteFailureRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
            Obj source=DriverJson.object(PublicDataJson.encodeFullMaterial(row.get(DriverEarlyExecuteFailureRowProducer.SOURCE_FIELD)).bytes(),RawJson.MAXIMUM_BYTES);
            var roles=DriverEarlyExecuteFailureRowProducer.publicNumbersFromSource(source);
            if(row.has("result")){
                require(row.get("result") instanceof ObjectNode&&roles.isPresent(),"original failed execute result requires its source-owned roles");
                Obj result=DriverJson.object(PublicDataJson.encodeFullMaterial(row.get("result")).bytes(),RawJson.MAXIMUM_BYTES);
                row.set("result",node(encode?roles.orElseThrow().toPublic(result):roles.orElseThrow().fromPublic(result)));
            }else require(roles.isEmpty(),"absent failed execute result cannot invent number roles");
            if(!encode)DriverEarlyExecuteFailureRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
        }
    }
    /** Post-Known semantic failure contains no result and already uses canonical source identity text. */
    private static void postKnownReadFailureHistory(ObjectNode snapshot) {
        JsonNode history=snapshot.get("native_command_history");if(history==null)return;
        require(history.isArray(),"original post-Known failure history array required");
        for(JsonNode value:history) {
            if(!(value instanceof ObjectNode row)||!row.has(DriverPostKnownReadFailureRowProducer.SOURCE_FIELD))continue;
            DriverPostKnownReadFailureRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
        }
    }
    /** Failed Army reads retain exact error DATA. The sole producer parser grants no attempt, after-frame or writer authority. */
    private static void failedReadHistory(ObjectNode snapshot) {
        JsonNode history=snapshot.get("native_command_history");if(history==null)return;
        require(history.isArray(),"original failed read history array required");
        for(JsonNode value:history) {
            if(!(value instanceof ObjectNode row)||!row.has(DriverFailedReadHistoryRowProducer.SOURCE_FIELD))continue;
            // Source contains only bounded references/text: preserve every field and apply no numeric result conversion.
            DriverFailedReadHistoryRowProducer.decode(PublicDataJson.encodeFullMaterial(row).bytes());
        }
    }
    /** Sole action-source codec selects the original Gift submit/receipt part and its source-owned number roles. */
    private static void actionHistory(ObjectNode snapshot,boolean encode) {
        JsonNode history=snapshot.get("native_command_history");if(history==null)return;
        require(history.isArray(),"original action history array required");
        for(JsonNode value:history) {
            if(!(value instanceof ObjectNode row))continue;
            var roles=DriverActionHistoryCodec.giftPublicNumbers(DriverJson.object(PublicDataJson.encodeFullMaterial(row).bytes(),RawJson.MAXIMUM_BYTES));
            if(roles.isEmpty())continue;
            require(!row.has(DriverReadHistoryRowProducer.SOURCE_FIELD)&&!row.has(DriverObservedHistoryRowProducer.SOURCE_FIELD),"one exact action history source family required");
            require(row.get("result") instanceof ObjectNode,"complete original Gift recorder result required");
            Obj result=DriverJson.object(PublicDataJson.encodeFullMaterial(row.get("result")).bytes(),RawJson.MAXIMUM_BYTES);
            row.set("result",node(encode?roles.orElseThrow().toPublic(result):roles.orElseThrow().fromPublic(result)));
        }
    }
    /** The same source-owned lifecycle result codec serves AUTO and successful original Driver history rows. */
    private static void lifecycleHistory(ObjectNode snapshot,boolean encode) {
        JsonNode history=snapshot.get("native_command_history");if(history==null)return;
        require(history.isArray(),"original history array required");
        for(JsonNode value:history) {
            if(!(value instanceof ObjectNode row))continue;
            if(!row.path("command").isTextual() || !row.path("ok").isBoolean() || !row.get("ok").booleanValue())continue;
            var kind=LifecyclePublicResultCodec.kindOfOperation(row.get("command").textValue());
            if(kind.isEmpty())continue;
            require(row.get("result") instanceof ObjectNode,"successful lifecycle original result object required");
            var result=PublicDataJson.encodeFullMaterial(row.get("result"));
            RawJson projected=encode?LifecyclePublicResultCodec.encode(kind.orElseThrow(),result):LifecyclePublicResultCodec.decode(kind.orElseThrow(),result);
            row.set("result",PublicDataJson.object(projected));
        }
    }
    /** Direct semantic lifecycle/M3 state uses the identical source-owned contracts as result/history. */
    private static void lifecycleState(ObjectNode snapshot,boolean encode) {
        JsonNode reconciliation=snapshot.get("succession_reconciliation");
        if(reconciliation!=null && !reconciliation.isNull()) {
            require(reconciliation instanceof ObjectNode,"actual M3 reconciliation state must be object or null");
            var original=PublicDataJson.encodeFullMaterial(reconciliation);
            if(LifecyclePublicResultCodec.isAvailableReconciliation(original)) {
                RawJson projected=encode?LifecyclePublicResultCodec.encodeReconciliation(original):LifecyclePublicResultCodec.decodeReconciliation(original);
                snapshot.set("succession_reconciliation",PublicDataJson.object(projected));
            }
        }
        JsonNode terminal=snapshot.get("scored_terminal");
        if(terminal!=null && !terminal.isNull()) {
            require(terminal instanceof ObjectNode,"actual retained scored terminal must be object or null");
            var original=PublicDataJson.encodeFullMaterial(terminal);
            RawJson projected=encode?LifecyclePublicResultCodec.encode(org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof.Kind.DEATH,original)
                    :LifecyclePublicResultCodec.decode(org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof.Kind.DEATH,original);
            snapshot.set("scored_terminal",PublicDataJson.object(projected));
        }
    }
    /** Open Native extensions retain their original JSON type; unknown unsafe numeric roles are rejected, never guessed. */
    public static void publicNumbers(JsonNode value,String path) {
        if(value.isIntegralNumber())require(value.bigIntegerValue().abs().compareTo(SAFE)<=0,"unqualified unsafe numeric public role at "+path);
        if(value.isFloatingPointNumber())require(Double.isFinite(value.doubleValue()),"nonfinite public float at "+path);
        if(value.isObject())value.properties().forEach(entry -> publicNumbers(entry.getValue(),path+"/"+entry.getKey().replace("~","~0").replace("/","~1")));
        else if(value.isArray())for(int i=0;i<value.size();i++)publicNumbers(value.get(i),path+"/"+i);
    }
    private static void rejectedSnapshotDiagnostics(ObjectNode snapshot,boolean encode) {
        JsonNode diagnostics=snapshot.get("diagnostics");
        require(diagnostics instanceof ObjectNode,"original diagnostic object required");
        Obj original=DriverJson.object(PublicDataJson.encodeFullMaterial(diagnostics).bytes(),RawJson.MAXIMUM_BYTES);
        Obj converted=encode?RejectedSnapshotPublicEncoding.toPublic(original):RejectedSnapshotPublicEncoding.fromPublic(original);
        snapshot.set("diagnostics",DriverJson.toNode(converted));
    }
    private static void require(boolean condition,String message){StrictJson.require(condition,message);}
    private static ObjectNode node(Obj value){return (ObjectNode)OpportunityJson.toNode(value);}
}
