package org.xar.ck3.control.continuity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Pure saved-campaign binding transition. The original writer owns sequence/commit. */
public final class SavedContinuityAttachment {
    public static final String REQUEST_SCHEMA = "xar.java-saved-continuity-reduce-request/v1";
    public static final String FIRST_REQUEST_SCHEMA = "xar.java-saved-continuity-reduce-request/v2";
    public static final String FIRST_BASIS_SCHEMA = "xar.java-first-saved-continuity-basis/v1";
    public static final String LEGACY_BASIS_SCHEMA = "xar.current-saved-basis/v1";
    public static final String FIRST_ATTACHMENT_KIND = "JAVA_FIRST_SAVED_CHECKPOINT_COLD_VERIFIED_V1";
    private static final Set<String> FIELDS = Set.of("schema", "previous", "details", "expected_details",
            "expected_predecessor", "basis", "game", "opening", "progress");
    private static final Set<String> CHANGED = Set.of("status", "game_binding", "latest_binding",
            "last_settled_cycles", "last_settled_date_raw", "cold_handoff_count", "last_current_saved_cold",
            "last_settled_source", "current_saved_reconciliation", "previous_interruption");
    private SavedContinuityAttachment() { }

    /** Real first-pair facts, never an ordinary CompletedCycleProof with a fabricated zero count. */
    public record FirstBasis(String machineId,ContinuityState.Origin origin,FirstBasis.Frame frame,EpisodeWindow.CommittedBaseline baseline,
            ExactRef driverRef,FileStatIdentity driverIdentity,ExactRef saveRef,FileStatIdentity saveIdentity,
            ExactRef firstSaveReceiptRef,ExactRef firstPairRef,ExactRef firstMaterialRef,String checkpointBindingSha256,
            String lineageId,long historyIndex) {
        public record Frame(String snapshotId,BigInteger revision,BigInteger nativeRevision,long dateRaw,
                            long actorCharacterId,String episodeRunId) {
            public Frame {
                StrictJson.text(snapshotId);uint64(revision);uint64(nativeRevision);StrictJson.safe(dateRaw,0);
                NativeCharacterId.of(actorCharacterId);StrictJson.text(episodeRunId);
            }
            public ObjectNode toJson(){
                ObjectNode row=StrictJson.object();row.put("snapshot_id",snapshotId);row.put("revision",revision.toString());row.put("native_revision",nativeRevision.toString());
                row.put("date_raw",dateRaw);row.put("actor_character_id",actorCharacterId);row.put("episode_run_id",episodeRunId);return row;
            }
            public static Frame fromJson(JsonNode value){
                ObjectNode row=StrictJson.object(value,Set.of("snapshot_id","revision","native_revision","date_raw","actor_character_id","episode_run_id"));
                return new Frame(StrictJson.text(row.get("snapshot_id")),decimal(row.get("revision")),decimal(row.get("native_revision")),
                        number(row,"date_raw"),NativeCharacterId.fromJson(row.get("actor_character_id")).value(),StrictJson.text(row.get("episode_run_id")));
            }
            private static BigInteger decimal(JsonNode value){
                String text=StrictJson.text(value);StrictJson.require(text.matches("0|[1-9][0-9]*")&&text.length()<=20,"canonical uint64 revision decimal text required");
                BigInteger result=new BigInteger(text);uint64(result);return result;
            }
            private static void uint64(BigInteger value){StrictJson.require(value!=null&&value.signum()>=0&&value.bitLength()<=64,"exact uint64 revision required");}
        }
        public FirstBasis {
            StrictJson.text(machineId);Objects.requireNonNull(origin);Objects.requireNonNull(frame);Objects.requireNonNull(baseline);
            Objects.requireNonNull(driverRef);Objects.requireNonNull(driverIdentity);Objects.requireNonNull(saveRef);Objects.requireNonNull(saveIdentity);
            Objects.requireNonNull(firstSaveReceiptRef);Objects.requireNonNull(firstPairRef);Objects.requireNonNull(firstMaterialRef);
            org.xar.ck3.control.continuity.writer.WriterContracts.requireDigest(checkpointBindingSha256);StrictJson.text(lineageId);StrictJson.safe(historyIndex,1);
            EpisodeWindow.Baseline first=baseline.baseline();EpisodeWindow.Identity identity=first.savedIdentity();
            StrictJson.require(machineId.equals(identity.machineId())&&origin.windowId()==first.begin().begin().newWindowId()
                    &&origin.startDateRaw()==identity.dateRaw()&&frame.dateRaw()==identity.dateRaw()&&frame.actorCharacterId()==identity.actorId()
                    &&frame.episodeRunId().equals(identity.episodeRunId())&&firstSaveReceiptRef.equals(first.canonicalSaveReceiptRef())
                    &&firstPairRef.equals(first.pairRef())&&checkpointBindingSha256.equals(first.proofDigest()),"FIRST basis must retain its actual same original BASELINE and first pair");
            StrictJson.require(driverIdentity.bytes().equals(BigInteger.valueOf(driverRef.bytes()))&&saveIdentity.bytes().equals(BigInteger.valueOf(saveRef.bytes())),"original FIRST Driver/SAVE references and physical witness sizes differ");
        }
        public ObjectNode toJson(){
            ObjectNode row=StrictJson.object();row.put("schema",FIRST_BASIS_SCHEMA);row.put("machine_id",machineId);row.put("completed_cycles",0);
            ObjectNode from=row.putObject("origin");from.put("window_id",origin.windowId());from.put("start_date_raw",origin.startDateRaw());
            from.put("target_date_raw",origin.targetDateRaw());from.put("target_days",origin.targetDays());row.set("frame",frame.toJson());row.set("committed_baseline",baseline.toJson());
            ObjectNode refs=row.putObject("refs");refs.set("driver",driverRef.toJson());refs.set("save",saveRef.toJson());
            refs.set("first_save_receipt",firstSaveReceiptRef.toJson());refs.set("first_pair",firstPairRef.toJson());refs.set("first_material",firstMaterialRef.toJson());
            row.put("identity_schema",FileStatIdentity.SCHEMA);row.set("driver_identity",driverIdentity.toJson());row.set("save_identity",saveIdentity.toJson());
            ObjectNode checkpoint=row.putObject("checkpoint");checkpoint.put("path",saveRef.path());checkpoint.put("size",saveRef.bytes());checkpoint.put("sha256",saveRef.sha256());
            checkpoint.put("history_index",historyIndex);checkpoint.put("saved_date_raw",frame.dateRaw());ObjectNode goal=row.putObject("campaign_goal_anchor");
            goal.put("campaign_id",lineageId);goal.put("current_character_id",frame.actorCharacterId());row.put("checkpoint_binding_sha256",checkpointBindingSha256);return row;
        }
        public static FirstBasis fromJson(JsonNode value){
            ObjectNode row=StrictJson.object(value,Set.of("schema","machine_id","completed_cycles","origin","frame","committed_baseline","refs",
                    "identity_schema","driver_identity","save_identity","checkpoint","campaign_goal_anchor","checkpoint_binding_sha256"));
            StrictJson.require(FIRST_BASIS_SCHEMA.equals(StrictJson.text(row.get("schema")))&&number(row,"completed_cycles")==0,"explicit first-pair schema and zero factual completed frontier required");
            ObjectNode origin=StrictJson.object(row.get("origin"),Set.of("window_id","start_date_raw","target_date_raw","target_days"));
            ObjectNode refs=StrictJson.object(row.get("refs"),Set.of("driver","save","first_save_receipt","first_pair","first_material"));
            ObjectNode checkpoint=StrictJson.object(row.get("checkpoint"),Set.of("path","size","sha256","history_index","saved_date_raw"));
            ObjectNode goal=StrictJson.object(row.get("campaign_goal_anchor"),Set.of("campaign_id","current_character_id"));
            String identitySchema=StrictJson.text(row.get("identity_schema"));
            FirstBasis result=new FirstBasis(StrictJson.text(row.get("machine_id")),new ContinuityState.Origin(number(origin,"window_id"),number(origin,"start_date_raw"),number(origin,"target_date_raw"),number(origin,"target_days")),
                    Frame.fromJson(row.get("frame")),EpisodeWindow.CommittedBaseline.fromJson(row.get("committed_baseline")),ExactRef.fromJson(refs.get("driver")),FileStatIdentity.fromJson(row.get("driver_identity"),identitySchema),
                    ExactRef.fromJson(refs.get("save")),FileStatIdentity.fromJson(row.get("save_identity"),identitySchema),ExactRef.fromJson(refs.get("first_save_receipt")),ExactRef.fromJson(refs.get("first_pair")),ExactRef.fromJson(refs.get("first_material")),
                    StrictJson.text(row.get("checkpoint_binding_sha256")),StrictJson.text(goal.get("campaign_id")),number(checkpoint,"history_index"));
            StrictJson.require(ContinuityJson.same(row,result.toJson()),"FIRST basis contains inconsistent original frame/checkpoint/lineage facts");return result;
        }
        public void requirePredecessor(ContinuityState predecessor){
            EpisodeWindow.State active=EpisodeWindow.requireActive(predecessor);
            StrictJson.require(predecessor.machineId().equals(machineId)&&predecessor.origin().equals(origin)
                    &&active.baseline().filter(baseline.baseline()::equals).isPresent()&&predecessor.sequence()>=baseline.sequence(),"FIRST restoration must retain this actual current window's original BASELINE");
            StrictJson.require(predecessor.settledCycles()==0&&predecessor.settledDateRaw()==frame.dateRaw(),
                    "an older FIRST frontier requires the dedicated actual rollback authority before restoration");
        }
    }

    public record Input(ContinuityState predecessor, byte[] details, byte[] basis, byte[] game,
                        byte[] opening, byte[] progress) {
        public Input {
            details = checked(details); basis = checked(basis); game = checked(game);
            opening = checked(opening); progress = checked(progress);
            java.util.Objects.requireNonNull(predecessor);
        }
        private static byte[] checked(byte[] raw) {
            return ContinuityJson.canonical(ContinuityJson.parseObject(raw, ContinuityJson.DOCUMENT_MAX_BYTES));
        }
        @Override public byte[] details() { return details.clone(); }
        @Override public byte[] basis() { return basis.clone(); }
        @Override public byte[] game() { return game.clone(); }
        @Override public byte[] opening() { return opening.clone(); }
        @Override public byte[] progress() { return progress.clone(); }
    }

    public static Input decode(byte[] raw) {
        ObjectNode row = StrictJson.object(ContinuityJson.parseObject(raw, ContinuityJson.TRANSPORT_MAX_BYTES), FIELDS);
        String schema=StrictJson.text(row.get("schema"));ObjectNode basis=ContinuityJson.object(row.get("basis"));
        boolean first=schema.equals(FIRST_REQUEST_SCHEMA);
        StrictJson.require(first||schema.equals(REQUEST_SCHEMA),"exact ordinary or explicit FIRST saved continuity request schema");
        if(first)FirstBasis.fromJson(basis);else StrictJson.require(!isFirstBasis(basis),"ordinary request cannot masquerade as the explicit FIRST basis");
        ObjectNode old = ContinuityJson.object(row.get("previous"));
        StrictJson.require(ContinuityJson.same(old, row.get("expected_predecessor"))
                && ContinuityJson.same(row.get("details"), row.get("expected_details")), "exact frozen predecessor");
        String machine = StrictJson.text(old.get("machine_id"));
        return new Input(ContinuityState.fromJson(old, machine), bytes(row.get("expected_details")),
                bytes(row.get("basis")), bytes(row.get("game")), bytes(row.get("opening")), bytes(row.get("progress")));
    }

    public static byte[] reduce(byte[] request) { return ContinuityJson.canonical(reduce(decode(request)).toJson()); }

    /** One response/source contract discriminator after runtime validation, with no field aliases. */
    public static String requestSchema(Input input) {
        ObjectNode basis=object(input.basis());
        if(isFirstBasis(basis)){FirstBasis.fromJson(basis);return FIRST_REQUEST_SCHEMA;}
        return REQUEST_SCHEMA;
    }

    /**
     * Pure identity/frontier preflight before replacing an ordinary SAVE. The actual private material,
     * physical replacement, complete reducer preview and original-writer commitment remain mandatory.
     */
    public static void requireOrdinaryPredecessor(ContinuityState actual,byte[] actualBasis) {
        Objects.requireNonNull(actual);ObjectNode basis=object(actualBasis);
        requireOrdinaryOrigin(actual,basis);
        ObjectNode frame=ContinuityJson.object(basis.get("frame"));
        StrictJson.require(number(basis,"completed_cycles")>=actual.settledCycles()&&number(frame,"date_raw")>=actual.settledDateRaw(),
                "older settled frontier requires the dedicated rollback transaction before ordinary SAVE replacement");
    }

    private static boolean isLegacyBasis(ObjectNode basis) {
        return basis.has("schema")&&LEGACY_BASIS_SCHEMA.equals(StrictJson.text(basis.get("schema")));
    }

    /** Shared origin/type checks; the explicit P37 wire never declared a window_id. */
    private static void requireOrdinaryOrigin(ContinuityState actual,ObjectNode basis) {
        StrictJson.require(!isFirstBasis(basis),"ordinary preflight cannot grant a FIRST saved-material branch");
        ObjectNode origin=ContinuityJson.object(basis.get("origin")),frame=ContinuityJson.object(basis.get("frame"));
        boolean legacy=isLegacyBasis(basis);
        if(legacy){
            StrictJson.object(origin,Set.of("start_date_raw","target_date_raw","target_days","original_wall_origin_utc","campaign_id"));
            StrictJson.text(origin.get("original_wall_origin_utc"));StrictJson.text(origin.get("campaign_id"));
        }
        StrictJson.require(StrictJson.text(basis.get("machine_id")).equals(actual.machineId())
                &&number(origin,"start_date_raw")==actual.origin().startDateRaw()
                &&number(origin,"target_date_raw")==actual.origin().targetDateRaw()
                &&number(origin,"target_days")==actual.origin().targetDays()
                &&(legacy||number(origin,"window_id")==actual.origin().windowId()),
                "ordinary saved material changed the actual machine/window/origin/target");
        NativeCharacterId.fromJson(frame.get("actor_character_id"));StrictJson.text(frame.get("episode_run_id"));
    }

    public static ContinuityState reduce(Input input) {
        ObjectNode old = input.predecessor().toJson();
        ObjectNode basis = object(input.basis()), details = object(input.details()), progress = object(input.progress());
        FirstBasis first=isFirstBasis(basis)?FirstBasis.fromJson(basis):null;
        if(first!=null){
            first.requirePredecessor(input.predecessor());
            var replacement=org.xar.ck3.control.contracts.GameGeneration.fromJson(object(input.game()));ObjectNode opening=object(input.opening());
            StrictJson.require(!replacement.equals(org.xar.ck3.control.contracts.GameGeneration.fromJson(old.get("game_binding")))
                    &&replacement.equals(org.xar.ck3.control.contracts.GameGeneration.fromJson(opening.get("game")))
                    &&first.machineId().equals(StrictJson.text(opening.get("machine_id")))
                    &&first.frame().episodeRunId().equals(StrictJson.text(opening.get("episode_run_id")))
                    &&first.frame().actorCharacterId()==NativeCharacterId.fromJson(opening.get("actor_character_id")).value()
                    &&first.frame().dateRaw()==number(opening,"date_raw"),"FIRST restore must retain its paired episode/actor/date in an actual distinct replacement Game");
            StrictJson.text(opening.get("session_id"));
            StrictJson.text(opening.get("snapshot_id"));FirstBasis.Frame.decimal(opening.get("native_revision"));
        }else if(isLegacyBasis(basis)){
            // Historical P37 reductions can record a negative already-settled alignment. New physical
            // replacements still require the public strict preflight before any SAVE is replaced.
            requireOrdinaryOrigin(input.predecessor(),basis);
        }else requireOrdinaryPredecessor(input.predecessor(),input.basis());
        ObjectNode origin = ContinuityJson.object(basis.get("origin")), frame = ContinuityJson.object(basis.get("frame"));
        // The typed FIRST basis and the shared ordinary origin checks above preserve each wire contract.
        StrictJson.require(number(old, "last_settled_cycles") == number(progress, "ledger_cycles")
                && number(old, "last_settled_date_raw") == number(progress, "ledger_date_raw"),
                "exact original predecessor progress coordinates");
        for (String field : Set.of("new_ordinary_cycle_credit", "game_day_credit")) {
            StrictJson.require(number(details, field) == 0, "attachment grants no new credit");
        }
        falseValue(details.get("original_actions_replayed")); falseValue(details.get("window_origin_reset"));
        long completed = number(basis, "completed_cycles"), date = number(frame, "date_raw");
        ObjectNode changed = old.deepCopy();
        changed.put("status", date >= number(origin, "target_date_raw") ? "complete" : "running");
        changed.set("game_binding", object(input.game())); changed.set("latest_binding", object(input.opening()));
        changed.put("last_settled_cycles", completed); changed.put("last_settled_date_raw", date);
        long handoffs = old.has("cold_handoff_count") ? number(old, "cold_handoff_count") : 0;
        changed.put("cold_handoff_count", StrictJson.safe(handoffs + 1, 0));
        changed.set("last_current_saved_cold", details);
        changed.set("last_settled_source",first==null?ContinuityJson.object(ContinuityJson.object(basis.get("refs")).get("settled_full_response")).deepCopy()
                :first.firstSaveReceiptRef().toJson());
        ObjectNode reconciliation = StrictJson.object(); reconciliation.set("progress", progress);
        reconciliation.put("already_settled_alignment_cycles", completed - number(progress, "ledger_cycles"));
        reconciliation.put("already_settled_alignment_date_raw", date - number(progress, "ledger_date_raw"));
        reconciliation.put("ordinary_cycle_credit", 0); reconciliation.put("game_day_credit", 0);
        reconciliation.put("original_actions_replayed", false); changed.set("current_saved_reconciliation", reconciliation);
        if (old.has("interruption")) { changed.set("previous_interruption", old.get("interruption").deepCopy()); }
        old.fieldNames().forEachRemaining(field -> {
            if (!CHANGED.contains(field)) {
                StrictJson.require(ContinuityJson.same(old.get(field), changed.get(field)),
                        "origin/window/unknown history must remain exact");
            }
        });
        return ContinuityState.fromJson(changed, input.predecessor().machineId());
    }

    private static ObjectNode object(byte[] raw) { return ContinuityJson.parseObject(raw, ContinuityJson.DOCUMENT_MAX_BYTES); }
    private static boolean isFirstBasis(ObjectNode basis) {
        if(!basis.has("schema"))return false; // Existing Java ordinary producer has no nested basis schema.
        String schema=StrictJson.text(basis.get("schema"));
        StrictJson.require(schema.equals(FIRST_BASIS_SCHEMA)||schema.equals(LEGACY_BASIS_SCHEMA),"explicit known FIRST or original P37 basis schema required");
        return schema.equals(FIRST_BASIS_SCHEMA);
    }
    private static byte[] bytes(JsonNode node) { return ContinuityJson.canonical(ContinuityJson.object(node)); }
    private static long number(ObjectNode row, String field) { return ContinuityState.number(row, field, 0); }
    private static void falseValue(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean() && !value.booleanValue(), "no replay or window reset");
    }
}
