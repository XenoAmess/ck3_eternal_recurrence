package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.SavedProofReadTicket;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;

/** Small parameter/preseed producer. No method launches Main, a writer or an SDK measurement. */
public final class ClosedAdoptionPreparation {
    public static final String NOTE_SCHEMA="xar.closed-adoption-preparation-note/v2";
    public static final String ROSTER_SCHEMA="xar.closed-adoption-preparation-roster/v2";
    private static final String STATUS="PENDING_UNSIGNED_NOT_AUTHORIZATION";
    private static final int SOURCE_CAP=2*1024*1024;
    private static final String PRIOR="java/ck3-control/admission-contracts/src/test/resources/closedpartial/original-sources.json";
    private static final String BUSINESS="java/ck3-control/wave2-runtime/src/test/resources/closedadoption/original-business-sources.json";
    private static final String MECHANICAL="tools/g2_saved_campaign/current_saved_continuity_v1.py";
    private static final String OWNER="tools/g2_saved_campaign/root_current_saved_campaign_cold_owner_v1.py";
    private static final String PRIOR_SHA="9a05399247539be0856428cc2916927a97edcede313cf2f131c277b18582bc47";
    private static final String BUSINESS_SHA="d9e8e4be972a62ba339b457382b3a38a769f74c02672c7809a6da84ab353de7d";
    private ClosedAdoptionPreparation() { }

    /** Original immutable provenance is independent of the repo used for current transport sources. */
    public record OriginalManifests(ExactRef prior,ExactRef business) {
        public OriginalManifests {
            positive(prior,RecoveryEvidence.MAX_BYTES);positive(business,RecoveryEvidence.MAX_BYTES);
            smallPath(Path.of(prior.path()));smallPath(Path.of(business.path()));
            StrictJson.require(prior.bytes()==15697 && prior.sha256().equals(PRIOR_SHA)
                    && business.bytes()==18010 && business.sha256().equals(BUSINESS_SHA),"two original pinned manifests");
        }
    }

    public record Prepared(Path repo,Path outputRoot,ClosedAdoptionRequest request,ExactRef requestRef,
            ExactRef sourceRosterRef,ExactRef actualProductionPredecessor,FileStatIdentity productionIdentity,
            ExactRef event240Source,ExactRef mechanicalSource,ExactRef coldOwnerSource) {
        public Prepared {
            absolute(repo);absolute(outputRoot);Objects.requireNonNull(request);
            for(ExactRef ref:List.of(requestRef,sourceRosterRef,actualProductionPredecessor,event240Source,mechanicalSource,coldOwnerSource)){positive(ref,SOURCE_CAP);}
            Objects.requireNonNull(productionIdentity);sameSize(actualProductionPredecessor,productionIdentity);
        }
    }
    public record Limits(long writerMemoryBytes,Duration timeout,Instant deadlineUtc,long minimumFreeBytes,long maximumOutputBytes) {
        public Limits {
            Objects.requireNonNull(timeout);Objects.requireNonNull(deadlineUtc);
            StrictJson.require(writerMemoryBytes>0 && writerMemoryBytes<=512L*1024*1024
                    && timeout.equals(Duration.ofSeconds(timeout.toSeconds())) && timeout.toSeconds()>0 && timeout.toSeconds()<=120
                    && minimumFreeBytes>0 && minimumFreeBytes<=StrictJson.MAX_SAFE_INTEGER
                    && maximumOutputBytes>0 && maximumOutputBytes<=16L*1024*1024,"finite whole-second Root limits");
        }
    }
    public record BoundParameters(ExactRef invocationRef,ExactRef reviewPlanRef) {
        public BoundParameters {positive(invocationRef,RecoveryEvidence.MAX_BYTES);positive(reviewPlanRef,RecoveryEvidence.MAX_BYTES);}
    }

    public record SourceRow(ExactRef expectedRef,FileStatIdentity actualIdentity,List<String> labels) {
        public SourceRow {
            positive(expectedRef,SOURCE_CAP);smallPath(Path.of(expectedRef.path()));sameSize(expectedRef,actualIdentity);
            labels=List.copyOf(labels);
            StrictJson.require(!labels.isEmpty() && labels.size()<=8 && new HashSet<>(labels).size()==labels.size(),"unique bounded source labels");
            for(String label:labels){StrictJson.require(StrictJson.text(label).matches("(prior|business)(/[A-Za-z0-9_-]+)+"),"source label grammar");}
        }
        public ObjectNode toJson(){
            ObjectNode row=StrictJson.object();row.set("expected_ref",expectedRef.toJson());row.set("actual_identity",actualIdentity.toJson());
            var values=row.putArray("labels");labels.forEach(values::add);row.put("status","MATCH");return row;
        }
        private static SourceRow decode(JsonNode value){
            ObjectNode row=StrictJson.object(value,Set.of("expected_ref","actual_identity","labels","status"));token(row,"status","MATCH");
            List<String> labels=new ArrayList<>();for(JsonNode label:array(row.get("labels"))){labels.add(StrictJson.text(label));}
            return new SourceRow(ExactRef.fromJson(row.get("expected_ref")),FileStatIdentity.fromJson(row.get("actual_identity"),FileStatIdentity.SCHEMA),labels);
        }
    }
    public record SourceRoster(int revision,String machineId,Instant observedAtUtc,ExactRef priorManifestRef,
            ExactRef businessManifestRef,List<SourceRow> sourceRoster) {
        public SourceRoster {
            ClosedAdoptionPreparation.revision(revision);StrictJson.text(machineId);Objects.requireNonNull(observedAtUtc);
            positive(priorManifestRef,RecoveryEvidence.MAX_BYTES);positive(businessManifestRef,RecoveryEvidence.MAX_BYTES);
            smallPath(Path.of(priorManifestRef.path()));smallPath(Path.of(businessManifestRef.path()));
            sourceRoster=List.copyOf(sourceRoster);StrictJson.require(sourceRoster.size()==88,"complete 88-source cohort");
            Set<String> paths=new HashSet<>();for(SourceRow row:sourceRoster){StrictJson.require(paths.add(row.expectedRef().path()),"unique source path");}
        }
        public ObjectNode toJson(){
            ObjectNode row=StrictJson.object();row.put("schema",ROSTER_SCHEMA);row.put("revision",revision);row.put("machine_id",machineId);
            row.put("observed_at_utc",observedAtUtc.toString());row.set("prior_manifest_ref",priorManifestRef.toJson());row.set("business_manifest_ref",businessManifestRef.toJson());
            var sources=row.putArray("source_roster");sourceRoster.forEach(value->sources.add(value.toJson()));
            row.put("driver_body_reads",0);row.put("save_body_reads",0);return row;
        }
        public static SourceRoster decode(byte[] raw){
            ObjectNode row=StrictJson.object(StrictJson.parse(raw),Set.of("schema","revision","machine_id","observed_at_utc","prior_manifest_ref","business_manifest_ref","source_roster","driver_body_reads","save_body_reads"));
            token(row,"schema",ROSTER_SCHEMA);zero(row,"driver_body_reads","save_body_reads");
            List<SourceRow> sources=new ArrayList<>();for(JsonNode value:array(row.get("source_roster"))){sources.add(SourceRow.decode(value));}
            return new SourceRoster(revisionValue(row),text(row,"machine_id"),instant(row,"observed_at_utc"),
                    ExactRef.fromJson(row.get("prior_manifest_ref")),ExactRef.fromJson(row.get("business_manifest_ref")),sources);
        }
    }
    public record Note(int revision,String machineId,Instant observedAtUtc,String requestObservedAtUtc,Path repo,Path outputRoot,
            ExactRef requestRef,ExactRef sourceRosterRef,ExactRef immutablePredecessorRef,ExactRef actualProductionPredecessorRef,
            FileStatIdentity actualProductionPredecessorIdentity,OriginalWriterTransaction.Target actualProductionTarget,
            ExactRef event240PreseedSource,FileStatIdentity event240SourceIdentity,ExactRef mechanicalSourceRef,ExactRef coldOwnerSourceRef) {
        public Note {
            ClosedAdoptionPreparation.revision(revision);StrictJson.text(machineId);Objects.requireNonNull(observedAtUtc);StrictJson.utc(requestObservedAtUtc);
            StrictJson.require(!observedAtUtc.isBefore(Instant.parse(requestObservedAtUtc)),"fresh observation does not precede retained request observation");
            absolute(repo);absolute(outputRoot);Objects.requireNonNull(actualProductionTarget);
            positive(actualProductionTarget.originalWriter(),SOURCE_CAP);smallPath(Path.of(actualProductionTarget.originalWriter().path()));
            for(ExactRef ref:List.of(requestRef,sourceRosterRef,immutablePredecessorRef,actualProductionPredecessorRef,event240PreseedSource)){positive(ref,RecoveryEvidence.MAX_BYTES);}
            positive(mechanicalSourceRef,SOURCE_CAP);positive(coldOwnerSourceRef,SOURCE_CAP);
            path(requestRef,outputRoot.resolve("adoption-request.json"));path(sourceRosterRef,outputRoot.resolve(rosterName(revision)));
            path(immutablePredecessorRef,outputRoot.resolve("immutable-head240.json"));
            absolute(actualProductionTarget.canonicalPath());path(actualProductionPredecessorRef,actualProductionTarget.canonicalPath());
            StrictJson.require(!actualProductionTarget.canonicalPath().startsWith(outputRoot),"independent production target");
            StrictJson.require(immutablePredecessorRef.bytes()==actualProductionPredecessorRef.bytes()
                    && immutablePredecessorRef.sha256().equals(actualProductionPredecessorRef.sha256()),"same exact predecessor content at independent paths");
            sameSize(actualProductionPredecessorRef,actualProductionPredecessorIdentity);sameSize(event240PreseedSource,event240SourceIdentity);
            path(event240PreseedSource,actualProductionTarget.canonicalPath().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS/00000240.json"));
            path(mechanicalSourceRef,repo.resolve(MECHANICAL));path(coldOwnerSourceRef,repo.resolve(OWNER));
        }
        public ObjectNode toJson(){
            ObjectNode row=StrictJson.object();row.put("schema",NOTE_SCHEMA);row.put("revision",revision);row.put("status",STATUS);row.put("machine_id",machineId);
            row.put("observed_at_utc",observedAtUtc.toString());row.put("request_observed_at_utc",requestObservedAtUtc);row.put("repo",repo.toString());row.put("output_root",outputRoot.toString());
            row.set("request_ref",requestRef.toJson());row.set("source_roster_ref",sourceRosterRef.toJson());row.set("immutable_predecessor_ref",immutablePredecessorRef.toJson());
            row.set("actual_production_predecessor_ref",actualProductionPredecessorRef.toJson());row.set("actual_production_predecessor_identity",actualProductionPredecessorIdentity.toJson());
            ObjectNode target=row.putObject("actual_production_target");target.put("canonical_path",actualProductionTarget.canonicalPath().toString());target.set("writer_source_ref",actualProductionTarget.originalWriter().toJson());
            row.set("event240_preseed_source",event240PreseedSource.toJson());row.set("event240_source_identity",event240SourceIdentity.toJson());
            row.set("mechanical_source_ref",mechanicalSourceRef.toJson());row.set("cold_owner_source_ref",coldOwnerSourceRef.toJson());
            for(String field:List.of("driver_body_reads","save_body_reads","writer_launches","game_launches")){row.put(field,0);}
            row.put("java_preparation_executed",true);row.put("invocation_created",false);row.put("review_plan_created",false);row.put("grants_warm_attachment",false);return row;
        }
        public static Note decode(byte[] raw){
            ObjectNode row=StrictJson.object(StrictJson.parse(raw),Set.of("schema","revision","status","machine_id","observed_at_utc","request_observed_at_utc","repo","output_root",
                    "request_ref","source_roster_ref","immutable_predecessor_ref","actual_production_predecessor_ref","actual_production_predecessor_identity","actual_production_target",
                    "event240_preseed_source","event240_source_identity","mechanical_source_ref","cold_owner_source_ref","driver_body_reads","save_body_reads","writer_launches","game_launches",
                    "java_preparation_executed","invocation_created","review_plan_created","grants_warm_attachment"));
            token(row,"schema",NOTE_SCHEMA);token(row,"status",STATUS);zero(row,"driver_body_reads","save_body_reads","writer_launches","game_launches");
            StrictJson.trueValue(row.get("java_preparation_executed"));falseValue(row,"invocation_created","review_plan_created","grants_warm_attachment");
            ObjectNode target=StrictJson.object(row.get("actual_production_target"),Set.of("canonical_path","writer_source_ref"));
            return new Note(revisionValue(row),text(row,"machine_id"),instant(row,"observed_at_utc"),text(row,"request_observed_at_utc"),Path.of(text(row,"repo")),Path.of(text(row,"output_root")),
                    ExactRef.fromJson(row.get("request_ref")),ExactRef.fromJson(row.get("source_roster_ref")),ExactRef.fromJson(row.get("immutable_predecessor_ref")),
                    ExactRef.fromJson(row.get("actual_production_predecessor_ref")),FileStatIdentity.fromJson(row.get("actual_production_predecessor_identity"),FileStatIdentity.SCHEMA),
                    new OriginalWriterTransaction.Target(Path.of(text(target,"canonical_path")),ExactRef.fromJson(target.get("writer_source_ref"))),
                    ExactRef.fromJson(row.get("event240_preseed_source")),FileStatIdentity.fromJson(row.get("event240_source_identity"),FileStatIdentity.SCHEMA),
                    ExactRef.fromJson(row.get("mechanical_source_ref")),ExactRef.fromJson(row.get("cold_owner_source_ref")));
        }
    }
    public static Note parseNote(byte[] raw){return Note.decode(raw);}
    public static SourceRoster parseRoster(byte[] raw){return SourceRoster.decode(raw);}
    public static String noteName(int revision){revision(revision);return String.format(java.util.Locale.ROOT,"PREPARATION-refresh%04d.json",revision);}
    public static String rosterName(int revision){revision(revision);return String.format(java.util.Locale.ROOT,"source-roster-refresh%04d.json",revision);}

    private record Checked(ExactRef ref,FileStatIdentity identity,byte[] raw){ }
    private record Captured(Checked prior,Checked business,List<SourceRow> rows,Checked head,Checked event,Checked mechanical,Checked owner){ }

    /** Initial producer. Existing request/preseed files are never overwritten; use refresh for a retained package. */
    public static Prepared prepare(Path repo,Path outputRoot,Instant observedAtUtc,Runnable capacityGuard)throws IOException{
        return prepare(repo,outputRoot,repoRelativeManifests(repo),observedAtUtc,capacityGuard);
    }
    /** Explicit original provenance; only current mechanical/owner transport sources are resolved under repo. */
    public static Prepared prepare(Path repo,Path outputRoot,OriginalManifests manifests,Instant observedAtUtc,Runnable capacityGuard)throws IOException{
        Objects.requireNonNull(manifests);Objects.requireNonNull(capacityGuard);Objects.requireNonNull(observedAtUtc);
        StrictJson.require(!observedAtUtc.isAfter(Instant.now()),"actual initial observation time");
        capacityGuard.run();repo=realDirectory(repo);outputRoot=realDirectory(outputRoot);
        var ids=new WindowsSavedProofIdentityReader();Captured data=capture(repo,manifests,ids,capacityGuard);
        Path canonical=outputRoot.resolve("fixture-canonical/ROOT-CONTINUITY-WINDOW.json"),events=canonical.resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS");
        Files.createDirectories(events);Files.createDirectories(outputRoot.resolve("metadata"));
        publishOnce(outputRoot.resolve("immutable-head240.json"),data.head().raw(),capacityGuard);
        publishOnce(canonical,data.head().raw(),capacityGuard);publishOnce(events.resolve("00000240.json"),data.event().raw(),capacityGuard);
        byte[] requestRaw=StrictJson.canonical(buildRequestJson(data,outputRoot,observedAtUtc.toString()));
        ClosedAdoptionRequest request=ClosedAdoptionRequest.decode(requestRaw);
        ExactRef requestRef=publishOnce(outputRoot.resolve("adoption-request.json"),requestRaw,capacityGuard);
        return publishRefresh(repo,outputRoot,request,requestRef,1,observedAtUtc,data,capacityGuard);
    }
    /**
     * Revalidates original manifests and every small source, retaining the exact request observation and all three original preseed files.
     * Publishes only a new strict roster and note. No ticket, nonce, invocation or review approval is created.
     */
    public static Prepared refreshTransportSources(Path repo,Path outputRoot,ExactRef originalRequestRef,int revision,
            Instant freshObservedAtUtc,Runnable capacityGuard)throws IOException{
        return refreshTransportSources(repo,outputRoot,repoRelativeManifests(repo),originalRequestRef,revision,freshObservedAtUtc,capacityGuard);
    }
    /** Retains exact manifest provenance while refreshing transport sources from a separate current repo. */
    public static Prepared refreshTransportSources(Path repo,Path outputRoot,OriginalManifests manifests,ExactRef originalRequestRef,int revision,
            Instant freshObservedAtUtc,Runnable capacityGuard)throws IOException{
        Objects.requireNonNull(manifests);Objects.requireNonNull(capacityGuard);revision(revision);capacityGuard.run();repo=realDirectory(repo);outputRoot=realDirectory(outputRoot);
        var ids=new WindowsSavedProofIdentityReader();path(originalRequestRef,outputRoot.resolve("adoption-request.json"));
        ClosedAdoptionRequest request=ClosedAdoptionRequest.decode(exact(originalRequestRef,RecoveryEvidence.MAX_BYTES,ids).raw());
        Captured data=capture(repo,manifests,ids,capacityGuard);verifyRetained(request,outputRoot,data,ids);
        return publishRefresh(repo,outputRoot,request,originalRequestRef,revision,freshObservedAtUtc,data,capacityGuard);
    }
    private static Prepared publishRefresh(Path repo,Path root,ClosedAdoptionRequest request,ExactRef requestRef,int revision,Instant fresh,
            Captured data,Runnable guard)throws IOException{
        Objects.requireNonNull(fresh);
        StrictJson.require(!fresh.isAfter(Instant.now()) && !fresh.isBefore(Instant.parse(request.observedAtUtc())),"actual fresh observation with retained request time");
        noExecutionArtifacts(root);
        Path notePath=root.resolve(noteName(revision)),rosterPath=root.resolve(rosterName(revision));
        StrictJson.require(!Files.exists(notePath,LinkOption.NOFOLLOW_LINKS) && !Files.exists(rosterPath,LinkOption.NOFOLLOW_LINKS),"create-only fresh revision paths");
        SourceRoster roster=new SourceRoster(revision,request.machineId(),fresh,data.prior().ref(),data.business().ref(),data.rows());
        byte[] rosterRaw=StrictJson.canonical(roster.toJson());ExactRef rosterRef=new ExactRef(rosterPath.toString(),rosterRaw.length,RecoveryEvidence.sha256(rosterRaw));
        Note note=new Note(revision,request.machineId(),fresh,request.observedAtUtc(),repo,root,requestRef,rosterRef,request.inputs().predecessor(),data.head().ref(),data.head().identity(),
                new OriginalWriterTransaction.Target(Path.of(data.head().ref().path()),request.writerSource()),data.event().ref(),data.event().identity(),data.mechanical().ref(),data.owner().ref());
        byte[] noteRaw=StrictJson.canonical(note.toJson());publishOnce(rosterPath,rosterRaw,guard);
        publishOnce(notePath,noteRaw,guard);guard.run();
        return prepared(repo,root,request,requestRef,rosterRef,data);
    }
    /** Old schema-less PREPARATION.json is historical evidence and cannot enter this loader. */
    public static Prepared inspectPrepared(Path repo,Path outputRoot,ExactRef preparationRef,Runnable capacityGuard)throws IOException{
        Objects.requireNonNull(capacityGuard);capacityGuard.run();repo=realDirectory(repo);outputRoot=realDirectory(outputRoot);
        var ids=new WindowsSavedProofIdentityReader();Note note=parseNote(exact(preparationRef,RecoveryEvidence.MAX_BYTES,ids).raw());
        path(preparationRef,outputRoot.resolve(noteName(note.revision())));
        StrictJson.require(repo.equals(note.repo()) && outputRoot.equals(note.outputRoot()) && note.machineId().equals(WindowsJobProcess.currentMachineId())
                && !note.observedAtUtc().isAfter(Instant.now()),"actual note roots, observation and machine");
        SourceRoster roster=parseRoster(exact(note.sourceRosterRef(),RecoveryEvidence.MAX_BYTES,ids).raw());
        StrictJson.require(roster.revision()==note.revision() && roster.machineId().equals(note.machineId()) && roster.observedAtUtc().equals(note.observedAtUtc()),"one note/roster revision and observation");
        Captured data=capture(repo,new OriginalManifests(roster.priorManifestRef(),roster.businessManifestRef()),ids,capacityGuard);verifyRoster(roster,data);
        ClosedAdoptionRequest request=ClosedAdoptionRequest.decode(exact(note.requestRef(),RecoveryEvidence.MAX_BYTES,ids).raw());
        verifyRetained(request,outputRoot,data,ids);
        StrictJson.require(request.observedAtUtc().equals(note.requestObservedAtUtc()) && request.inputs().predecessor().equals(note.immutablePredecessorRef())
                && data.head().ref().equals(note.actualProductionPredecessorRef()) && data.head().identity().equals(note.actualProductionPredecessorIdentity())
                && request.writerSource().equals(note.actualProductionTarget().originalWriter()) && data.event().ref().equals(note.event240PreseedSource())
                && data.event().identity().equals(note.event240SourceIdentity()) && data.mechanical().ref().equals(note.mechanicalSourceRef())
                && data.owner().ref().equals(note.coldOwnerSourceRef()),"fresh exact source pins; historical green JSON supplies no authority");
        return prepared(repo,outputRoot,request,note.requestRef(),note.sourceRosterRef(),data);
    }
    private static Prepared prepared(Path repo,Path root,ClosedAdoptionRequest request,ExactRef requestRef,ExactRef rosterRef,Captured data){
        return new Prepared(repo,root,request,requestRef,rosterRef,data.head().ref(),data.head().identity(),data.event().ref(),data.mechanical().ref(),data.owner().ref());
    }
    private static void verifyRoster(SourceRoster roster,Captured data){
        StrictJson.require(roster.priorManifestRef().equals(data.prior().ref()) && roster.businessManifestRef().equals(data.business().ref())
                && roster.sourceRoster().equals(data.rows()),"all original manifest refs, complete roster and native identities remain exact");
    }
    private static void verifyRetained(ClosedAdoptionRequest request,Path root,Captured data,WindowsSavedProofIdentityReader ids)throws IOException{
        StrictJson.require(request.equals(ClosedAdoptionRequest.decode(StrictJson.canonical(buildRequestJson(data,root,request.observedAtUtc())))),"retained strict request is exactly the original manifest mapping");
        StrictJson.require(Arrays.equals(exact(request.inputs().predecessor(),RecoveryEvidence.MAX_BYTES,ids).raw(),data.head().raw())
                && Arrays.equals(measure(request.canonicalPath(),RecoveryEvidence.MAX_BYTES,ids).raw(),data.head().raw())
                && Arrays.equals(measure(request.canonicalPath().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS/00000240.json"),RecoveryEvidence.MAX_BYTES,ids).raw(),data.event().raw()),
                "original immutable snapshot, fixture head and event preseed are reused byte-for-byte");
        StrictJson.require(request.metadataRoot().toRealPath().equals(root.resolve("metadata")),"existing metadata directory");
    }
    private static OriginalManifests repoRelativeManifests(Path repo){
        absolute(repo);
        return new OriginalManifests(new ExactRef(repo.resolve(PRIOR).toString(),15697,PRIOR_SHA),
                new ExactRef(repo.resolve(BUSINESS).toString(),18010,BUSINESS_SHA));
    }
    private static Captured capture(Path repo,OriginalManifests manifests,WindowsSavedProofIdentityReader ids,Runnable guard)throws IOException{
        Checked prior=exact(manifests.prior(),RecoveryEvidence.MAX_BYTES,ids),business=exact(manifests.business(),RecoveryEvidence.MAX_BYTES,ids);
        StrictJson.require(prior.ref().bytes()==15697 && prior.ref().sha256().equals(PRIOR_SHA)
                && business.ref().bytes()==18010 && business.ref().sha256().equals(BUSINESS_SHA),"two original pinned manifests");
        ObjectNode p=object(StrictJson.parse(prior.raw())),b=object(StrictJson.parse(business.raw()));
        StrictJson.require(text(p,"machine_id").equals(WindowsJobProcess.currentMachineId()) && text(p,"machine_id").equals(text(b,"machine_id"))
                && ExactRef.fromJson(object(b.get("prior_fixture_manifest")).get("ref")).equals(prior.ref()),"actual machine and outer manifest source binding");
        Map<ExactRef,List<String>> refs=new LinkedHashMap<>();collect(p,"prior",refs);collect(b,"business",refs);
        StrictJson.require(refs.size()==88,"exact original source cohort");List<SourceRow> rows=new ArrayList<>();
        for(var entry:refs.entrySet()){guard.run();Checked current=exact(entry.getKey(),SOURCE_CAP,ids);rows.add(new SourceRow(entry.getKey(),current.identity(),entry.getValue()));}
        Checked head=exact(ref(object(p.get("inputs")),"head"),RecoveryEvidence.MAX_BYTES,ids),event=exact(ref(object(b.get("sources")),"lastCommittedEvent"),RecoveryEvidence.MAX_BYTES,ids);
        StrictJson.integer(StrictJson.parse(head.raw()).get("sequence"),240,240);
        StrictJson.require(StrictJson.parse(event.raw()).get("after").equals(StrictJson.parse(head.raw())),"original committed event240 after equals current head");
        return new Captured(prior,business,List.copyOf(rows),head,event,measure(repo.resolve(MECHANICAL),SOURCE_CAP,ids),measure(repo.resolve(OWNER),SOURCE_CAP,ids));
    }
    private static ObjectNode buildRequestJson(Captured data,Path root,String observed){
        ObjectNode p=object(StrictJson.parse(data.prior().raw())),b=object(StrictJson.parse(data.business().raw()));
        ObjectNode inputs=object(p.get("inputs")),sources=object(p.get("sources")),bs=object(b.get("sources")),row=StrictJson.object();
        row.put("schema","xar.java-closed-partial-adoption-request/v1");row.put("machine_id",text(p,"machine_id"));row.put("observed_at_utc",observed);
        ObjectNode ri=row.putObject("inputs");ri.set("predecessor",new ExactRef(root.resolve("immutable-head240.json").toString(),data.head().ref().bytes(),data.head().ref().sha256()).toJson());
        pairs(ri,inputs,"saved_basis:basis","prior_qualification:qualification","full_request:fullRequest","failed_full:failedFull","auto_request:autoRequest","failed_auto:failedAuto","raw_state:state","raw_governance:governance","actual_next:next");
        pairs(row.putObject("closed"),sources,"sdk:sdk","game_exit:game","supervisor:supervisor","recording:recording","capture:capture","screen:screen");
        var tasks=row.putArray("tasks");for(JsonNode value:array(p.get("tasks"))){ObjectNode from=object(value),to=tasks.addObject();to.put("role",text(from,"role"));pairs(to,from,"spec:spec","closed:closed","unregistered:unregistered");}
        JsonNode pc=array(p.get("cycles")),bc=array(b.get("cycles"));StrictJson.require(pc.size()==7 && bc.size()==7,"seven source-bound actual settled pairs");
        var cycles=row.putArray("cycles");for(int i=0;i<7;i++){ObjectNode to=cycles.addObject(),from=object(bc.get(i));pairs(to,object(pc.get(i)),"auto:auto","metrics:metrics");
            pairs(to,from,"event:event","ordinary_credit:ordinaryCredit","auto_after:autoAfter","metrics_after:metricsAfter","before_plan:beforePlan");
            if(from.get("readonlySaveSkip").isNull()){to.putNull("readonly_save_skip");}else{to.set("readonly_save_skip",ref(from,"readonlySaveSkip").toJson());}}
        pairs(row.putObject("business"),bs,"saved_seed:seed","saved_governance:governance","cold_bound:bound","opening_semantic:semantic","opening_capabilities:capabilities","classifier_pin:classifierPin","classifier_source:classifierSource","queue_source:queueSource","capture_probe:captureProbe","capture_cleanup:captureCleanup");
        row.put("canonical_path",root.resolve("fixture-canonical/ROOT-CONTINUITY-WINDOW.json").toString());row.put("metadata_root",root.resolve("metadata").toString());
        row.set("writer_source",ref(bs,"writerSource").toJson());return row;
    }
    /** Root separately supplies an actual fresh ticket; this binds parameters without executing either stage. */
    public static BoundParameters bind(Prepared prepared,RecoveryEvidence actualRootTicket,Limits limits,Runnable capacityGuard)throws IOException{
        Objects.requireNonNull(prepared);Objects.requireNonNull(limits);Objects.requireNonNull(capacityGuard);capacityGuard.run();noExecutionArtifacts(prepared.outputRoot());
        SavedProofReadTicket ticket=SavedProofReadTicket.parse(actualRootTicket);
        StrictJson.require(ticket.machineId().equals(prepared.request().machineId()) && ticket.outputRoot().toRealPath().equals(prepared.outputRoot().toRealPath())
                && !Instant.now().isBefore(ticket.observedAt()) && Instant.now().isBefore(limits.deadlineUtc()) && !limits.deadlineUtc().isAfter(ticket.reviewAt()),"fresh Root ticket and earliest finite lease");
        var ids=new WindowsSavedProofIdentityReader();exact(actualRootTicket.reference(),RecoveryEvidence.MAX_BYTES,ids);
        SourceRoster roster=parseRoster(exact(prepared.sourceRosterRef(),RecoveryEvidence.MAX_BYTES,ids).raw());
        Captured data=capture(prepared.repo(),new OriginalManifests(roster.priorManifestRef(),roster.businessManifestRef()),ids,capacityGuard);verifyRoster(roster,data);
        ClosedAdoptionRequest request=ClosedAdoptionRequest.decode(exact(prepared.requestRef(),RecoveryEvidence.MAX_BYTES,ids).raw());verifyRetained(request,prepared.outputRoot(),data,ids);
        StrictJson.require(request.equals(prepared.request()) && data.mechanical().ref().equals(prepared.mechanicalSource()) && data.owner().ref().equals(prepared.coldOwnerSource())
                && data.head().ref().equals(prepared.actualProductionPredecessor()) && data.head().identity().equals(prepared.productionIdentity())
                && ids.stat(ticket.driverPath()).equals(ticket.driverIdentity()) && ids.stat(Path.of(ticket.save().path())).equals(ticket.saveIdentity()),"fresh exact transport and predecessor bindings; persistence stat only");
        var target=new OriginalWriterTransaction.Target(Path.of(data.head().ref().path()),request.writerSource());
        var plan=new ClosedAdoptionReview.Plan(ticket.machineId(),actualRootTicket.reference(),ticket.nonce(),target,data.head().ref(),data.head().identity(),limits.deadlineUtc());
        ObjectNode row=StrictJson.object();row.put("schema","xar.closed-partial-temporary-invocation/v1");row.put("machine_id",ticket.machineId());row.set("adoption_request_ref",prepared.requestRef().toJson());
        row.set("sdk_read_ticket_ref",actualRootTicket.reference().toJson());row.put("repo",prepared.repo().toString());row.put("python_executable",ticket.pythonExecutable().toString());row.put("output_root",prepared.outputRoot().toString());
        row.put("memory_limit_bytes",limits.writerMemoryBytes());row.put("timeout_seconds",limits.timeout().toSeconds());row.put("lease_deadline_utc",limits.deadlineUtc().toString());row.put("minimum_free_bytes",limits.minimumFreeBytes());row.put("maximum_output_bytes",limits.maximumOutputBytes());
        row.set("mechanical_source_ref",prepared.mechanicalSource().toJson());row.set("cold_owner_source_ref",prepared.coldOwnerSource().toJson());byte[] raw=StrictJson.canonical(row);ClosedAdoptionMain.Invocation.decode(raw);
        ExactRef invocation=publishOnce(prepared.outputRoot().resolve("root-invocation.json"),raw,capacityGuard);
        return new BoundParameters(invocation,publishOnce(prepared.outputRoot().resolve("root-review-plan.json"),StrictJson.canonical(plan.toJson()),capacityGuard));
    }
    private static void collect(JsonNode value,String label,Map<ExactRef,List<String>> refs){
        if(value.isObject()){if(value.has("path") && value.has("bytes") && value.has("sha256")){
                ExactRef ref=ExactRef.fromJson(value);StrictJson.require(refs.keySet().stream().noneMatch(old->old.path().equals(ref.path()) && !old.equals(ref)),"one exact ref per source path");
                refs.computeIfAbsent(ref,key->new ArrayList<>()).add(label);}
            value.properties().forEach(entry->collect(entry.getValue(),label+"/"+entry.getKey(),refs));
        }else if(value.isArray()){for(int i=0;i<value.size();i++){collect(value.get(i),label+"/"+i,refs);}}
    }
    private static void pairs(ObjectNode into,ObjectNode from,String... pairs){for(String pair:pairs){String[] fields=pair.split(":",-1);into.set(fields[0],ref(from,fields[1]).toJson());}}
    private static ExactRef ref(ObjectNode row,String field){return ExactRef.fromJson(object(row.get(field)).get("ref"));}
    private static ObjectNode object(JsonNode value){StrictJson.require(value instanceof ObjectNode,"JSON object required");return (ObjectNode)value;}
    private static JsonNode array(JsonNode value){StrictJson.require(value!=null && value.isArray(),"JSON array required");return value;}
    private static String text(ObjectNode row,String field){return StrictJson.text(row.get(field));}
    private static Instant instant(ObjectNode row,String field){return Instant.parse(StrictJson.utc(text(row,field)));}
    private static void token(ObjectNode row,String field,String expected){StrictJson.require(expected.equals(text(row,field)),"exact "+field+" token");}
    private static void zero(ObjectNode row,String... fields){for(String field:fields){StrictJson.integer(row.get(field),0,0);}}
    private static void falseValue(ObjectNode row,String... fields){for(String field:fields){JsonNode value=row.get(field);StrictJson.require(value!=null && value.isBoolean() && !value.booleanValue(),"exact false "+field);}}
    private static int revisionValue(ObjectNode row){return (int)StrictJson.integer(row.get("revision"),1,9999);}
    private static void revision(int value){StrictJson.require(value>=1 && value<=9999,"bounded positive revision");}
    private static void positive(ExactRef ref,int cap){Objects.requireNonNull(ref);StrictJson.require(ref.bytes()>0 && ref.bytes()<=cap,"positive complete bounded ref");absolute(Path.of(ref.path()));}
    private static void sameSize(ExactRef ref,FileStatIdentity identity){Objects.requireNonNull(identity);StrictJson.require(identity.bytes().equals(BigInteger.valueOf(ref.bytes())),"ref and native identity byte size");}
    private static void absolute(Path path){StrictJson.require(path!=null && path.isAbsolute() && path.normalize().equals(path),"absolute normalized path");}
    private static void path(ExactRef ref,Path expected){StrictJson.require(Path.of(ref.path()).equals(expected),"fixed source/publication path");}
    private static Path realDirectory(Path value)throws IOException{
        absolute(value);StrictJson.require(Files.isDirectory(value,LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(value) && value.toRealPath().equals(value),"existing owned normalized directory");return value;
    }
    private static void smallPath(Path path){absolute(path);String name=path.toString().replace('\\','/').toLowerCase(java.util.Locale.ROOT);
        StrictJson.require(!name.endsWith("/driver-state.json") && !name.endsWith(".ck3") && !name.endsWith(".sav"),"metadata/source only; no persistence body");}
    private static Checked exact(ExactRef ref,int cap,WindowsSavedProofIdentityReader ids)throws IOException{
        positive(ref,cap);Checked checked=measure(Path.of(ref.path()),cap,ids);StrictJson.require(checked.ref().equals(ref),"exact original source bytes and SHA");return checked;
    }
    private static Checked measure(Path path,int cap,WindowsSavedProofIdentityReader ids)throws IOException{
        smallPath(path);FileStatIdentity before=ids.stat(path);StrictJson.require(before.bytes().signum()>0 && before.bytes().longValueExact()<=cap,"bounded complete source");
        byte[] raw;try(var input=Files.newInputStream(path)){raw=input.readNBytes(cap+1);}
        StrictJson.require(raw.length==before.bytes().longValueExact() && raw.length<=cap && before.equals(ids.stat(path)),"stable native source read");
        return new Checked(new ExactRef(path.toString(),raw.length,RecoveryEvidence.sha256(raw)),before,raw);
    }
    private static ExactRef publishOnce(Path path,byte[] raw,Runnable guard)throws IOException{
        guard.run();StrictJson.require(raw.length>0 && raw.length<=RecoveryEvidence.MAX_BYTES && !Files.exists(path,LinkOption.NOFOLLOW_LINKS),"create-only bounded preparation publication");
        if(guard instanceof PreparationMain.CapacityGuard bounded){bounded.beforeWrite(path,raw.length);}
        Files.write(path,raw,StandardOpenOption.CREATE_NEW);guard.run();return new ExactRef(path.toString(),raw.length,RecoveryEvidence.sha256(raw));
    }
    private static void noExecutionArtifacts(Path root)throws IOException{
        for(String name:List.of("closed-adoption-result.json","root-invocation.json","root-review-plan.json","root-review-challenge.json","root-review-approval.json","root-review-approval-consumed.json","root-production-committed.json","root-two-stage-result.json","root-consumer-session")){
            StrictJson.require(!Files.exists(root.resolve(name),LinkOption.NOFOLLOW_LINKS),"preparation cannot refresh an executed or bound session");}
        try(var files=Files.newDirectoryStream(root,"sdk-*.consumed.json")){StrictJson.require(!files.iterator().hasNext(),"no consumed SDK nonce may be refreshed");}
    }

    /** Fixed metadata-only CLI. It neither issues tickets nor executes a transaction. */
    public static final class PreparationMain {
        public static final String CONFIG_SCHEMA="xar.closed-adoption-preparation-cli-config/v1";
        public static final String RESULT_SCHEMA="xar.closed-adoption-preparation-cli-result/v1";
        public enum Action { PREPARE, REFRESH, BIND }
        public record Capacity(long minimumFreeBytes,long maximumOutputBytes,Instant deadlineUtc) {
            public Capacity {
                StrictJson.require(minimumFreeBytes>0 && minimumFreeBytes<=StrictJson.MAX_SAFE_INTEGER
                        && maximumOutputBytes>0 && maximumOutputBytes<=16L*1024*1024,"finite preparation CLI capacity");
                Objects.requireNonNull(deadlineUtc);
            }
        }
        public record Context(String machineId,Path repo,Path outputRoot,Capacity capacity) {
            public Context {
                StrictJson.require(StrictJson.text(machineId).equals(WindowsJobProcess.currentMachineId()),"actual preparation CLI machine");
                absolute(repo);absolute(outputRoot);Objects.requireNonNull(capacity);
            }
        }
        public sealed interface Configuration permits PrepareConfiguration,RefreshConfiguration,BindConfiguration { Context context(); }
        public record PrepareConfiguration(Context context,OriginalManifests manifests,Instant observedAtUtc) implements Configuration {
            public PrepareConfiguration {Objects.requireNonNull(context);Objects.requireNonNull(manifests);Objects.requireNonNull(observedAtUtc);}
        }
        public record RefreshConfiguration(Context context,OriginalManifests manifests,ExactRef requestRef,int revision,Instant freshObservedAtUtc) implements Configuration {
            public RefreshConfiguration {
                Objects.requireNonNull(context);Objects.requireNonNull(manifests);positive(requestRef,RecoveryEvidence.MAX_BYTES);
                ClosedAdoptionPreparation.revision(revision);Objects.requireNonNull(freshObservedAtUtc);
            }
        }
        public record BindConfiguration(Context context,ExactRef preparationRef,ExactRef sdkReadTicketRef,Limits limits) implements Configuration {
            public BindConfiguration {
                Objects.requireNonNull(context);positive(preparationRef,RecoveryEvidence.MAX_BYTES);
                positive(sdkReadTicketRef,RecoveryEvidence.MAX_BYTES);Objects.requireNonNull(limits);
            }
        }
        public sealed interface Output permits PreparedOutput,BoundOutput { ObjectNode toJson(); }
        public record PreparedOutput(Action action,ExactRef preparationRef,ExactRef sourceRosterRef,ExactRef requestRef) implements Output {
            public PreparedOutput {
                StrictJson.require(action==Action.PREPARE || action==Action.REFRESH,"preparation output action");
                positive(preparationRef,RecoveryEvidence.MAX_BYTES);positive(sourceRosterRef,RecoveryEvidence.MAX_BYTES);positive(requestRef,RecoveryEvidence.MAX_BYTES);
            }
            public ObjectNode toJson(){
                ObjectNode row=result(action);row.set("preparation_ref",preparationRef.toJson());
                row.set("source_roster_ref",sourceRosterRef.toJson());row.set("request_ref",requestRef.toJson());return row;
            }
        }
        public record BoundOutput(BoundParameters parameters) implements Output {
            public BoundOutput {Objects.requireNonNull(parameters);}
            public ObjectNode toJson(){
                ObjectNode row=result(Action.BIND);row.set("invocation_ref",parameters.invocationRef().toJson());
                row.set("review_plan_ref",parameters.reviewPlanRef().toJson());return row;
            }
        }
        private PreparationMain(){ }
        public static Configuration decode(byte[] raw){
            ObjectNode initial=object(StrictJson.parse(raw));
            Action action=switch(text(initial,"action")){
                case "PREPARE"->Action.PREPARE;case "REFRESH"->Action.REFRESH;case "BIND"->Action.BIND;
                default->throw new org.xar.ck3.control.contracts.ContractViolationException("preparation CLI action");
            };
            Set<String> fields=switch(action){
                case PREPARE->Set.of("schema","action","machine_id","repo","output_root","capacity","original_manifests","observed_at_utc");
                case REFRESH->Set.of("schema","action","machine_id","repo","output_root","capacity","original_manifests","original_request_ref","revision","fresh_observed_at_utc");
                case BIND->Set.of("schema","action","machine_id","repo","output_root","capacity","preparation_ref","sdk_read_ticket_ref","limits");
            };
            ObjectNode row=StrictJson.object(initial,fields);token(row,"schema",CONFIG_SCHEMA);
            ObjectNode cap=StrictJson.object(row.get("capacity"),Set.of("minimum_free_bytes","maximum_output_bytes","deadline_utc"));
            Context context=new Context(text(row,"machine_id"),Path.of(text(row,"repo")),Path.of(text(row,"output_root")),
                    new Capacity(StrictJson.integer(cap.get("minimum_free_bytes"),1,StrictJson.MAX_SAFE_INTEGER),
                            StrictJson.integer(cap.get("maximum_output_bytes"),1,16L*1024*1024),instant(cap,"deadline_utc")));
            if(action==Action.PREPARE){return new PrepareConfiguration(context,manifests(row),instant(row,"observed_at_utc"));}
            if(action==Action.REFRESH){return new RefreshConfiguration(context,manifests(row),ExactRef.fromJson(row.get("original_request_ref")),revisionValue(row),instant(row,"fresh_observed_at_utc"));}
            ObjectNode limits=StrictJson.object(row.get("limits"),Set.of("writer_memory_bytes","timeout_seconds","deadline_utc","minimum_free_bytes","maximum_output_bytes"));
            return new BindConfiguration(context,ExactRef.fromJson(row.get("preparation_ref")),ExactRef.fromJson(row.get("sdk_read_ticket_ref")),
                    new Limits(StrictJson.integer(limits.get("writer_memory_bytes"),1,512L*1024*1024),
                            Duration.ofSeconds(StrictJson.integer(limits.get("timeout_seconds"),1,120)),instant(limits,"deadline_utc"),
                            StrictJson.integer(limits.get("minimum_free_bytes"),1,StrictJson.MAX_SAFE_INTEGER),
                            StrictJson.integer(limits.get("maximum_output_bytes"),1,16L*1024*1024)));
        }
        private static OriginalManifests manifests(ObjectNode row){
            ObjectNode value=StrictJson.object(row.get("original_manifests"),Set.of("prior","business"));
            return new OriginalManifests(ExactRef.fromJson(value.get("prior")),ExactRef.fromJson(value.get("business")));
        }
        public static Output execute(ExactRef configRef)throws IOException{
            var ids=new WindowsSavedProofIdentityReader();Configuration config=decode(exact(configRef,RecoveryEvidence.MAX_BYTES,ids).raw());
            Context context=config.context();Path repo=realDirectory(context.repo()),root=realDirectory(context.outputRoot());
            int revision=config instanceof RefreshConfiguration refresh?refresh.revision():1;
            Action action=config instanceof PrepareConfiguration?Action.PREPARE:config instanceof RefreshConfiguration?Action.REFRESH:Action.BIND;
            Instant deadline=context.capacity().deadlineUtc();
            if(config instanceof BindConfiguration bind && bind.limits().deadlineUtc().isBefore(deadline)){deadline=bind.limits().deadlineUtc();}
            try{
                var guard=new CapacityGuard(root,context.capacity(),deadline,publications(action,root,revision));
                guard.run();
                if(config instanceof PrepareConfiguration prepare){
                    Prepared prepared=prepare(repo,root,prepare.manifests(),prepare.observedAtUtc(),guard);
                    return preparedOutput(action,root,revision,prepared,ids);
                }
                if(config instanceof RefreshConfiguration refresh){
                    Prepared prepared=refreshTransportSources(repo,root,refresh.manifests(),refresh.requestRef(),refresh.revision(),refresh.freshObservedAtUtc(),guard);
                    return preparedOutput(action,root,revision,prepared,ids);
                }
                BindConfiguration bind=(BindConfiguration)config;
                Prepared prepared=inspectPrepared(repo,root,bind.preparationRef(),guard);
                RecoveryEvidence ticket=new RecoveryEvidence(bind.sdkReadTicketRef(),exact(bind.sdkReadTicketRef(),RecoveryEvidence.MAX_BYTES,ids).raw());
                return new BoundOutput(bind(prepared,ticket,bind.limits(),guard));
            }catch(java.io.UncheckedIOException error){throw error.getCause();}
        }
        public static void main(String[] args)throws IOException{
            StrictJson.require(args.length==3 && args[1].matches("[1-9][0-9]*") && args[2].matches("[0-9a-f]{64}"),"three exact preparation CLI arguments");
            Output output=execute(new ExactRef(args[0],Long.parseLong(args[1]),args[2]));
            System.out.write(StrictJson.canonical(output.toJson()));System.out.write('\n');
        }
        private static ObjectNode result(Action action){
            ObjectNode row=StrictJson.object();row.put("schema",RESULT_SCHEMA);row.put("action",action.name());
            row.put("machine_id",WindowsJobProcess.currentMachineId());row.put("observed_at_utc",Instant.now().toString());return row;
        }
        private static PreparedOutput preparedOutput(Action action,Path root,int revision,Prepared prepared,WindowsSavedProofIdentityReader ids)throws IOException{
            return new PreparedOutput(action,measure(root.resolve(noteName(revision)),RecoveryEvidence.MAX_BYTES,ids).ref(),prepared.sourceRosterRef(),prepared.requestRef());
        }
        private static List<Path> publications(Action action,Path root,int revision){
            return switch(action){
                case PREPARE->List.of(root.resolve("immutable-head240.json"),root.resolve("fixture-canonical/ROOT-CONTINUITY-WINDOW.json"),
                        root.resolve("fixture-canonical/ROOT-CONTINUITY-WINDOW-EVENTS/00000240.json"),root.resolve("adoption-request.json"),root.resolve(rosterName(1)),root.resolve(noteName(1)));
                case REFRESH->List.of(root.resolve(rosterName(revision)),root.resolve(noteName(revision)));
                case BIND->List.of(root.resolve("root-invocation.json"),root.resolve("root-review-plan.json"));
            };
        }
        private static final class CapacityGuard implements Runnable {
            private final Path root;private final Capacity capacity;private final Instant deadline;private final List<Path> publications;
            private CapacityGuard(Path root,Capacity capacity,Instant deadline,List<Path> publications)throws IOException{
                this.root=root;this.capacity=capacity;this.deadline=deadline;this.publications=List.copyOf(publications);
                for(Path path:publications){StrictJson.require(!Files.exists(path,LinkOption.NOFOLLOW_LINKS),"create-only preparation CLI outputs");}
                run();
            }
            public void run(){
                try{
                    StrictJson.require(Instant.now().isBefore(deadline),"preparation CLI earliest deadline");
                    long written=written();
                    StrictJson.require(written<=capacity.maximumOutputBytes(),"preparation CLI maximum output");
                    StrictJson.require(Files.getFileStore(root).getUsableSpace()>=capacity.minimumFreeBytes()+capacity.maximumOutputBytes()-written,"preparation CLI minimum free capacity");
                }catch(IOException error){throw new java.io.UncheckedIOException(error);}
            }
            private long written()throws IOException{
                long bytes=0;for(Path path:publications){if(Files.exists(path,LinkOption.NOFOLLOW_LINKS)){
                    StrictJson.require(Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS),"regular preparation CLI output");
                    bytes=Math.addExact(bytes,Files.size(path));
                }}return bytes;
            }
            private void beforeWrite(Path path,int bytes){
                run();
                try{
                    StrictJson.require(publications.contains(path) && Math.addExact(written(),bytes)<=capacity.maximumOutputBytes(),"preparation CLI maximum output");
                }catch(IOException error){throw new java.io.UncheckedIOException(error);}
            }
        }
    }
}
