package org.xar.ck3.control.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.offline.OfflineAnalysisFiles;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisWire;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;

/** One Core-owned bounded worker. Queue ACK follows immutable work publication; completion follows
 * the actual original analyzer, source-bound knowledge publication and original journal acknowledgement.
 * This class has no Game/MCP/OBS/action port and performs no Python or network invocation. */
public final class OfflineAnalysisWorker implements AutoCloseable {
    private static final int MAX = 2_097_152;
    private static final String WORK = "xar.offline-analysis-work/v1";
    private static final String DONE = "xar.offline-analysis-completion/v1";
    private static final String FAILED = "xar.offline-analysis-failure/v1";
    public record Settings(Path workRoot, int queueCapacity, int retainedWorkMaximum) {
        public Settings {
            workRoot = fixed(workRoot);
            if (queueCapacity < 1 || queueCapacity > 32 || retainedWorkMaximum < queueCapacity + 1 || retainedWorkMaximum > 4096)
                throw new IllegalArgumentException("finite offline queue and retained work bounds required");
        }
    }
    /** Fixed host roots, never output paths supplied by the queued request. */
    public record Binding(String machineId, Path stateRoot, Path stockRoot, Path incidentRoot, Path scanRoot,
            Path knowledgeRoot, Path grantsManifest) {
        public Binding {
            if (machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{0,63}") || machineId.equals("unknown"))
                throw new IllegalArgumentException("actual offline source machine required");
            stateRoot=fixed(stateRoot);stockRoot=fixed(stockRoot);incidentRoot=fixed(incidentRoot);scanRoot=fixed(scanRoot);
            knowledgeRoot=fixed(knowledgeRoot);grantsManifest=fixed(grantsManifest);
        }
    }
    public static final class AnalysisIncomplete extends IOException {
        private static final long serialVersionUID = 1L;
        private final Optional<ExactRef> evidence;
        AnalysisIncomplete(String message, Optional<ExactRef> evidence) { super(message); this.evidence=evidence; }
        public Optional<ExactRef> evidence() { return evidence; }
    }
    private record Engine(OfflineEventAnalysisHost host, Binding binding, OfflineAnalysisFiles.Port io) { }
    private record Work(Binding binding, BatchRequest request) { }
    private static final class Job {
        final Work work; final ExactRef durable; final CompletableFuture<SessionPorts.AnalysisCompletion> done=new CompletableFuture<>();
        Job(Work work,ExactRef durable){this.work=work;this.durable=durable;}
        SessionPorts.AnalysisTicket ticket(){return new SessionPorts.AnalysisTicket(work.request().batchId(),done.minimalCompletionStage());}
    }
    private final Settings settings;
    private final CheckpointFiles files;
    private final FileChannel lockChannel;
    private final FileLock lock;
    private final FileWitness lockWitness;
    private final Map<String,Job> jobs=new LinkedHashMap<>();
    private final ThreadPoolExecutor executor;
    private final CompletableFuture<Void> drained=new CompletableFuture<>();
    private final CompletionStage<Void> drainStage=drained.minimalCompletionStage();
    private volatile boolean closed;
    private volatile Optional<String> recoveryDiagnostic=Optional.empty();

    public OfflineAnalysisWorker(Settings settings, CheckpointFiles actualFiles, OfflineAnalysisFiles.Port actualWorkIo) throws IOException {
        this.settings=Objects.requireNonNull(settings);files=Objects.requireNonNull(actualFiles);
        Objects.requireNonNull(actualWorkIo).directories(settings.workRoot());
        Path lockPath=settings.workRoot().resolve("OFFLINE-WORKER.lock");actualWorkIo.beforeLock(lockPath);
        lockChannel=FileChannel.open(lockPath,StandardOpenOption.CREATE,StandardOpenOption.WRITE,LinkOption.NOFOLLOW_LINKS);
        FileLock acquired;
        // Keep the ownership byte beyond file-content reads; the legacy whole-file lock still overlaps it.
        try { acquired=lockChannel.tryLock(Long.MAX_VALUE-1,1,false); }
        catch(IOException|RuntimeException failure){lockChannel.close();throw failure;}
        if(acquired==null){lockChannel.close();throw new IOException("another actual offline worker owns the fixed work root");}
        lock=acquired;
        try {lockWitness=files.observe(lockPath).orElseThrow(()->new IOException("actual offline worker ownership file is missing"));}
        catch(IOException|RuntimeException failure){lock.release();lockChannel.close();throw failure;}
        executor=new ThreadPoolExecutor(1,1,0,TimeUnit.MILLISECONDS,new ArrayBlockingQueue<>(settings.queueCapacity()),task->{
            // Core owns graceful shutdown. Accepted analysis keeps a normally exiting JVM alive
            // after the host's finite wait expires; PENDING is never reported as completed research.
            Thread thread=new Thread(task,"xar-offline-source-analysis");thread.setDaemon(false);return thread;
        },new ThreadPoolExecutor.AbortPolicy()) {
            @Override protected void terminated() {
                Throwable failure=null;
                try { lock.release(); } catch(IOException|RuntimeException|Error closing) { failure=closing; }
                try { lockChannel.close(); } catch(IOException|RuntimeException|Error closing) { if(failure==null)failure=closing;else if(failure!=closing)failure.addSuppressed(closing); }
                // The executor enters this hook only after its accepted tasks have returned. No analysis
                // or output remains in flight; releasing the ownership resources precedes this signal.
                // Per-job success/failure remains exclusively on its original AnalysisTicket.
                if(failure==null)drained.complete(null);else drained.completeExceptionally(failure);
            }
        };
    }

    /** Each Game receives a distinct port bound to its actual same journal/configuration; the pool is shared.
     * Recovery queues only same fixed-root pending originals, never substitutes a new source binding. */
    public synchronized SessionPorts.OfflineAnalysisPort bind(OfflineEventAnalysisHost actualHost,Binding binding,
            OfflineAnalysisFiles.Port actualOutputIo) throws IOException {
        requireOpen();Objects.requireNonNull(actualHost);Objects.requireNonNull(binding);Objects.requireNonNull(actualOutputIo);
        var scope=actualHost.batchScope().orElseThrow(()->new IOException("actual offline host has no batch analysis producer"));
        if(!scope.incidentRoot().equals(binding.incidentRoot())||!scope.knowledgeRoot().equals(binding.knowledgeRoot())
                ||!scope.grantsManifest().equals(binding.grantsManifest())||!scope.scanRoot().equals(Optional.of(binding.scanRoot())))
            throw new IOException("offline host and actual fixed source roots differ");
        Engine engine=new Engine(actualHost,binding,actualOutputIo);
        List<Path> originals;
        try(var entries=Files.list(settings.workRoot())) {
            originals=entries.filter(path->path.getFileName().toString().endsWith(".request.json"))
                    .limit((long)settings.retainedWorkMaximum()+1).sorted().toList();
        }
        if(originals.size()>settings.retainedWorkMaximum())throw new IOException("retained offline originals exceed the admitted bound; review retention before enqueue");
        for(Path path:originals) {
            String filename=path.getFileName().toString();
            if(filename.length()==64+".request.json".length()&&jobs.containsKey(filename.substring(0,64)))continue;
            Work original=decodeWork(readPath(path,MAX));
            if(!path.equals(path(original,"request")))throw new IOException("offline original filename does not bind its exact typed work");
            if(!original.binding().equals(binding))continue;
            String key=key(original);if(jobs.containsKey(key))continue;
            if(executor.getQueue().remainingCapacity()==0)break;
            Job job=new Job(original,ref(path));jobs.put(key,job);
            restoreOrSubmit(engine,job);
        }
        return request->enqueue(engine,request);
    }

    private synchronized SessionPorts.AnalysisTicket enqueue(Engine engine,BatchRequest original) throws IOException {
        requireOpen();Objects.requireNonNull(original);Work work=new Work(engine.binding(),original);String key=key(work);
        Job retained=jobs.get(key);
        if(retained!=null){if(!retained.work.equals(work))throw new IOException("offline batch ID already binds different captured originals");return retained.ticket();}
        if(executor.getQueue().remainingCapacity()==0)throw new IOException("bounded offline queue is full; captured original remains available for a later batch");
        long count;
        try(var entries=Files.list(settings.workRoot())) {count=entries.filter(path->path.getFileName().toString().endsWith(".request.json")).limit((long)settings.retainedWorkMaximum()+1).count();}
        Path requestPath=path(work,"request");
        if(count>=settings.retainedWorkMaximum()&&!Files.exists(requestPath,LinkOption.NOFOLLOW_LINKS))
            throw new IOException("finite offline work retention requires policy review before another durable job");
        // Validate real immutable inputs before the durable ACK. The original analyzer revalidates them again.
        readExact(original.manifestRef(),MAX);for(ExactRef captured:original.capturedRefs())readExact(captured,MAX);
        ExactRef durable=publish(requestPath,encodeWork(work));
        Job job=new Job(work,durable);jobs.put(key,job);restoreOrSubmit(engine,job);
        return job.ticket();
    }
    private void restoreOrSubmit(Engine engine,Job job) throws IOException {
        Path done=path(job.work,"complete"),failed=path(job.work,"failure");
        if(Files.exists(done,LinkOption.NOFOLLOW_LINKS)&&Files.exists(failed,LinkOption.NOFOLLOW_LINKS))
            throw new IOException("offline work has conflicting terminal originals");
        if(Files.exists(done,LinkOption.NOFOLLOW_LINKS)) {
            try { job.done.complete(readCompletion(job,readPath(done,MAX))); }
            catch(IOException|RuntimeException invalid){job.done.completeExceptionally(invalid);}
        } else if(Files.exists(failed,LinkOption.NOFOLLOW_LINKS)) {
            ObjectNode failure=StrictJson.object(OfflineEventAnalysisWire.parseMetadataObject(readPath(failed,MAX)),
                    Set.of("schema","machine_id","batch_id","request_ref","observed_at_utc","reason","result_ref"));
            requireTerminal(failure,FAILED,job);ExactRef evidence=ref(failed);
            job.done.completeExceptionally(new AnalysisIncomplete(StrictJson.text(failure.get("reason")),Optional.of(evidence)));
        } else {
            try { executor.execute(()->{
                try { analyze(engine,job); }
                finally {
                    // Restart recovery may contain more originals than the current executor queue. Refill one
                    // bounded queue from disk as slots become free; never create a second unbounded executor.
                    if(!closed)try { bind(engine.host(),engine.binding(),engine.io());recoveryDiagnostic=Optional.empty(); }
                    catch(IOException|RuntimeException unavailable){recoveryDiagnostic=Optional.of("INCOMPLETE_PENDING_OFFLINE_RECOVERY: "+unavailable.getMessage());}
                }
            }); }
            catch(java.util.concurrent.RejectedExecutionException unavailable){jobs.remove(key(job.work));throw new IOException("durable offline original retained; executor admission rejected",unavailable);}
        }
    }
    private void analyze(Engine engine,Job job) {
        ExactRef result=null;
        try {
            readExact(job.durable,MAX);
            byte[] raw=OfflineAnalysisFiles.with(engine.io(),()->engine.host().batch(job.work.request()));
            raw=OfflineEventAnalysisWire.validateBatchResult(raw,job.work.request().batchId());
            // A crash may have published a prior idempotent attempt's result. Retain both exact outputs;
            // the final terminal selects this actual result rather than overwriting the prior evidence.
            result=publish(path(job.work,"result-"+DriverJson.sha256(raw)),raw);
            ObjectNode body=OfflineEventAnalysisWire.parseMetadataObject(raw);
            List<ExactRef> reviews=reviews(job.work,body);
            ObjectNode publication=StrictJson.object(body.get("grants_manifest"),Set.of("path","bytes","sha256","grants","added"));
            ExactRef actualPublication=new ExactRef(StrictJson.text(publication.get("path")),StrictJson.integer(publication.get("bytes"),0,1_048_576),StrictJson.text(publication.get("sha256")));
            if(!Path.of(actualPublication.path()).equals(engine.binding().grantsManifest()))throw new IOException("source analysis published a foreign knowledge manifest");
            // The live shared manifest is mutable. Retain its exact original committed bytes under an immutable snapshot role.
            ExactRef snapshot=OfflineAnalysisFiles.with(engine.io(),()->EvidenceGrantManifestPublisher.transaction(engine.binding().grantsManifest(),writer->
                    publish(path(job.work,"knowledge-"+actualPublication.sha256()),readExact(actualPublication,1_048_576))));
            var completion=new SessionPorts.AnalysisCompletion(job.work.request().batchId(),reviews,snapshot);
            publish(path(job.work,"complete"),encodeCompletion(job,completion,result));
            job.done.complete(completion);
        } catch(IOException|RuntimeException failure) {
            try {
                ObjectNode record=terminal(FAILED,job);String reason=failure.getMessage();
                if(reason==null||reason.isBlank())reason=failure.getClass().getSimpleName();
                record.put("reason",reason.substring(0,Math.min(1024,reason.length())));
                if(result==null)record.putNull("result_ref");else record.set("result_ref",result.toJson());
                ExactRef evidence=publish(path(job.work,"failure"),encode(record));
                job.done.completeExceptionally(new AnalysisIncomplete(reason,Optional.of(evidence)));
            } catch(IOException|RuntimeException persistenceFailure) {
                failure.addSuppressed(persistenceFailure);job.done.completeExceptionally(failure);
            }
        }
    }
    private List<ExactRef> reviews(Work work,ObjectNode body)throws IOException {
        Binding binding=work.binding();BatchRequest request=work.request();
        if(!binding.machineId().equals(StrictJson.text(body.get("machine_id"))))throw new IOException("actual analyzer returned another machine");
        ObjectNode report=OfflineEventAnalysisWire.parseMetadataObject(encode(body.get("report")));
        ExactRef reportRef=ExactRef.fromJson(body.get("report_ref"));
        if(!Path.of(reportRef.path()).equals(binding.knowledgeRoot().resolve(request.batchId()).resolve("EVENT-SOURCE-REVIEW.json")))
            throw new IOException("actual source review escaped its fixed batch report role");
        if(!OfflineEventAnalysisWire.parseMetadataObject(readExact(reportRef,1_048_576)).equals(report))throw new IOException("embedded analysis report differs from its immutable original");
        JsonNode manifest=report.get("manifest");
        Set<String> manifestFields=manifest!=null&&manifest.has("bytes")?Set.of("path","bytes","sha256"):Set.of("path","sha256");
        var originalManifest=StrictJson.object(manifest,manifestFields);
        if(!StrictJson.text(originalManifest.get("path")).equals(request.manifestRef().path())
                ||!StrictJson.text(originalManifest.get("sha256")).equals(request.manifestRef().sha256())
                ||(originalManifest.has("bytes")&&StrictJson.integer(originalManifest.get("bytes"),0,MAX)!=request.manifestRef().bytes()))
            throw new IOException("source report changed its captured manifest binding");
        var unresolved=report.get("unresolved");
        if(unresolved==null||!unresolved.isArray())throw new IOException("actual source analysis lacks its unresolved inventory");
        if(!unresolved.isEmpty())throw new AnalysisIncomplete("UNRESOLVED_SOURCE_RESEARCH: "+unresolved.size()+" original incidents require the exact source/materials recorded in "+reportRef.path(),Optional.of(reportRef));
        requireCoverage(report,request);
        for(ExactRef captured:request.capturedRefs())readExact(captured,MAX);
        List<ExactRef> reviews=new ArrayList<>();reviews.add(reportRef);
        for(JsonNode row:body.get("outputs")) {
            ExactRef output=ExactRef.fromJson(row);Path target=Path.of(output.path());
            if(!target.startsWith(binding.knowledgeRoot())&&!target.startsWith(binding.stateRoot().resolve("evidence/event-source-registry"))
                    &&!target.startsWith(binding.stateRoot().resolve("evidence/interaction-source-registry"))
                    &&!target.startsWith(binding.stateRoot().resolve("evidence/unknown-mandatory-choice-reviews/root-known-ui-recovery")))throw new IOException("source knowledge output escaped its actual fixed roots");
            readExact(output,1_048_576);if(!reviews.contains(output))reviews.add(output);
        }
        return List.copyOf(reviews);
    }
    private SessionPorts.AnalysisCompletion readCompletion(Job job,byte[] raw) throws IOException {
        ObjectNode done=StrictJson.object(OfflineEventAnalysisWire.parseMetadataObject(raw),Set.of("schema","machine_id","batch_id","request_ref","observed_at_utc","result_ref","persisted_reviews","published_knowledge"));
        requireTerminal(done,DONE,job);ExactRef result=ExactRef.fromJson(done.get("result_ref"));
        if(!Path.of(result.path()).equals(path(job.work,"result-"+result.sha256())))throw new IOException("retained result is not this work's immutable actual analyzer output");
        ObjectNode actual=OfflineEventAnalysisWire.parseMetadataObject(OfflineEventAnalysisWire.validateBatchResult(readExact(result,MAX),job.work.request().batchId()));
        List<ExactRef> originalReviews=reviews(job.work,actual);
        var rows=done.get("persisted_reviews");if(rows==null||!rows.isArray()||rows.size()<1||rows.size()>4609)throw new IOException("finite persisted original reviews required");
        List<ExactRef> reviews=new ArrayList<>();for(JsonNode row:rows){ExactRef original=ExactRef.fromJson(row);readExact(original,1_048_576);reviews.add(original);}
        if(!reviews.equals(originalReviews))throw new IOException("retained completion changed the original analyzer's entire persisted output inventory");
        ExactRef knowledge=ExactRef.fromJson(done.get("published_knowledge"));
        if(!Path.of(knowledge.path()).equals(path(job.work,"knowledge-"+knowledge.sha256())))throw new IOException("retained completion selected a foreign knowledge snapshot");
        JsonNode committed=actual.get("grants_manifest");
        if(!Path.of(StrictJson.text(committed.get("path"))).equals(job.work.binding().grantsManifest())
                ||knowledge.bytes()!=StrictJson.integer(committed.get("bytes"),0,1_048_576)||!knowledge.sha256().equals(StrictJson.text(committed.get("sha256"))))
            throw new IOException("retained completion changed the actual committed shared knowledge publication");
        org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec.decode(readExact(knowledge,1_048_576));
        return new SessionPorts.AnalysisCompletion(job.work.request().batchId(),reviews,knowledge);
    }
    private void requireCoverage(JsonNode report,BatchRequest request)throws IOException {
        JsonNode original=OfflineEventAnalysisWire.parseMetadataObject(readExact(request.manifestRef(),MAX));
        JsonNode incidents=original.get("new_incidents");
        if(incidents==null||!incidents.isArray()||incidents.size()>256)throw new IOException("actual original incident inventory is unavailable");
        var expected=new java.util.HashSet<String>();var actual=new java.util.HashSet<String>();
        for(JsonNode incident:incidents)if(!expected.add(StrictJson.text(incident.get("incident_id"))))throw new IOException("duplicate original incident identity");
        for(String field:List.of("entries","already_known")) {
            JsonNode rows=report.get(field);if(rows==null||!rows.isArray()||rows.size()>256)throw new IOException("actual analysis lost its finite classification inventory");
            for(JsonNode row:rows)if(!actual.add(StrictJson.text(row.get("incident_id"))))throw new IOException("incident classified more than once by source analysis");
        }
        if(!actual.equals(expected))throw new IOException("actual source review does not classify every captured incident");
    }
    private static byte[] encodeCompletion(Job job,SessionPorts.AnalysisCompletion completion,ExactRef result) {
        ObjectNode done=terminal(DONE,job);done.set("result_ref",result.toJson());
        var refs=done.putArray("persisted_reviews");completion.persistedReviews().forEach(ref->refs.add(ref.toJson()));
        done.set("published_knowledge",completion.publishedKnowledge().toJson());return encode(done);
    }
    private static ObjectNode terminal(String schema,Job job) {
        ObjectNode root=StrictJson.object();root.put("schema",schema);root.put("machine_id",job.work.binding().machineId());
        root.put("batch_id",job.work.request().batchId());root.set("request_ref",job.durable.toJson());root.put("observed_at_utc",Instant.now().toString());return root;
    }
    private static void requireTerminal(ObjectNode root,String schema,Job job) throws IOException {
        if(!schema.equals(StrictJson.text(root.get("schema")))||!job.work.binding().machineId().equals(StrictJson.text(root.get("machine_id")))
                ||!job.work.request().batchId().equals(StrictJson.text(root.get("batch_id")))||!job.durable.equals(ExactRef.fromJson(root.get("request_ref"))))
            throw new IOException("offline terminal crossed its exact original work/source binding");
        StrictJson.utc(StrictJson.text(root.get("observed_at_utc")));
    }
    private byte[] readPath(Path path,int maximum) throws IOException {
        var witness=files.observe(path).orElseThrow(()->new IOException("actual offline original is missing: "+path));return files.read(witness,maximum);
    }
    private ExactRef ref(Path path) throws IOException {return files.observe(path).orElseThrow(()->new IOException("actual offline file missing: "+path)).reference();}
    private byte[] readExact(ExactRef original,int maximum) throws IOException {
        var witness=files.observe(Path.of(original.path())).orElseThrow(()->new IOException("required original missing: "+original.path()));
        if(!witness.reference().equals(original))throw new IOException("SOURCE_CHANGED: exact offline original differs: "+original.path());
        return files.read(witness,maximum);
    }
    private ExactRef publish(Path path,byte[] raw) throws IOException {
        var existing=files.observe(path);
        if(existing.isPresent()) {
            if(!Arrays.equals(files.read(existing.orElseThrow(),MAX),raw))throw new IOException("immutable offline work/result already differs: "+path);
            return existing.orElseThrow().reference();
        }
        return files.createNew(path,raw.clone()).reference();
    }
    private static byte[] encodeWork(Work work) {
        ObjectNode root=StrictJson.object();root.put("schema",WORK);root.set("binding",binding(work.binding()));
        root.set("request",OfflineEventAnalysisWire.parseMetadataObject(OfflineEventAnalysisWire.encode(work.request())));return encode(root);
    }
    private static Work decodeWork(byte[] raw) {
        ObjectNode root=StrictJson.object(OfflineEventAnalysisWire.parseMetadataObject(raw),Set.of("schema","binding","request"));
        StrictJson.require(WORK.equals(StrictJson.text(root.get("schema"))),"exact offline durable work schema required");
        ObjectNode b=StrictJson.object(root.get("binding"),Set.of("machine_id","state_root","stock_root","incident_root","scan_root","knowledge_root","grants_manifest"));
        Binding binding=new Binding(StrictJson.text(b.get("machine_id")),path(b,"state_root"),path(b,"stock_root"),path(b,"incident_root"),path(b,"scan_root"),path(b,"knowledge_root"),path(b,"grants_manifest"));
        return new Work(binding,OfflineEventAnalysisWire.decodeBatch(encode(root.get("request"))));
    }
    private static ObjectNode binding(Binding b) {
        ObjectNode root=StrictJson.object();root.put("machine_id",b.machineId());root.put("state_root",b.stateRoot().toString());root.put("stock_root",b.stockRoot().toString());
        root.put("incident_root",b.incidentRoot().toString());root.put("scan_root",b.scanRoot().toString());root.put("knowledge_root",b.knowledgeRoot().toString());root.put("grants_manifest",b.grantsManifest().toString());return root;
    }
    private String key(Work work){return DriverJson.sha256((DriverJson.sha256(encode(binding(work.binding())))+":"+work.request().batchId()).getBytes(StandardCharsets.UTF_8));}
    private Path path(Work work,String role){return settings.workRoot().resolve(key(work)+"."+role+".json");}
    private static Path path(ObjectNode root,String field){return Path.of(StrictJson.text(root.get(field)));}
    private static Path fixed(Path path){Objects.requireNonNull(path);if(!path.isAbsolute()||!path.equals(path.normalize()))throw new IllegalArgumentException("canonical fixed absolute offline root required");return path;}
    private static byte[] encode(JsonNode root){byte[] raw=root.toString().getBytes(StandardCharsets.UTF_8);OfflineEventAnalysisWire.parseMetadataObject(raw);return raw;}
    private void requireOpen()throws IOException {
        if(closed||!lock.isValid())throw new IOException("actual Core offline worker is closed or its ownership lock is invalid");
        files.verify(lockWitness);
    }
    /** Stop accepting work, drain already admitted pure analysis, and retain originals across process termination.
     * No interrupt, cancellation or shutdown ACK is reported as completed research. */
    @Override public synchronized void close(){if(!closed){closed=true;executor.shutdown();}}
    /** Actual accepted-work drain and ownership-resource closure, never merely shutdown admission ACK.
     * It does not wait, create another pool, cancel work or certify that any particular analysis succeeded. */
    public CompletionStage<Void> drainCompletion(){return drainStage;}
    public boolean isTerminated(){return executor.isTerminated();}
    public Optional<String> recoveryDiagnostic(){return recoveryDiagnostic;}
}
