package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact file mutation after the owning Root session consumed a successful COMPOSE_BUNDLE.
 * Junction preparation uses the same retained Root scope and a Java native producer; Prepared qualification remains separate. */
public final class RootNativeMapMaterializer implements RootColdResumeSession.Workflow {
    public record Permit(String machineId, ExactRef planRef, Path runtimeRoot, Path quoteOutput,
                         List<Path> externalWriteRoots, Instant deadline, long allocationUpperLimitBytes,
                         ExactRef storageEvidence) {
        public Permit {
            StrictJson.text(machineId); Objects.requireNonNull(planRef); Objects.requireNonNull(storageEvidence);
            normalized(runtimeRoot); normalized(quoteOutput); Objects.requireNonNull(deadline);
            externalWriteRoots = List.copyOf(externalWriteRoots);
            if (allocationUpperLimitBytes < 1 || allocationUpperLimitBytes > 16L * 1024 * 1024
                    || externalWriteRoots.size() > 8 || quoteOutput.startsWith(runtimeRoot))
                throw new IllegalArgumentException("finite independent Root materialization scope required");
            List<Path> roots = new ArrayList<>(); roots.add(runtimeRoot);
            for (Path root : externalWriteRoots) {
                normalized(root);
                for (Path prior : roots) if (root.startsWith(prior) || prior.startsWith(root))
                    throw new IllegalArgumentException("independent exact output scopes required");
                roots.add(root);
            }
            for (Path root : roots) if (quoteOutput.startsWith(root))
                throw new IllegalArgumentException("quote must be outside all materialized source scopes");
        }
    }
    private enum Mode { CREATE_ONLY, HARDLINK }
    private record Row(Path path, Mode mode, FileRef source, long bytes, String sha256) { }
    private final Permit permit;
    private final RootColdResumeSession.Workflow continuation;
    private final Runnable finitePermitGuard;
    private boolean consumed;
    public RootNativeMapMaterializer(Permit permit, RootColdResumeSession.Workflow continuation,
                                     Runnable finitePermitGuard) {
        this.permit = Objects.requireNonNull(permit); this.continuation = Objects.requireNonNull(continuation);
        this.finitePermitGuard = Objects.requireNonNull(finitePermitGuard);
    }
    @Override public void run(RootColdResumeSession session) throws IOException, InterruptedException {
        continuation.run(session);
    }
    @Override public synchronized JunctionScope materialize(OriginalColdConsumerSession.ComposedBundle bundle) throws IOException {
        if (consumed) throw new IOException("materialization is one-use; partial output is never replayed");
        consumed = true; Objects.requireNonNull(bundle); guard(0);
        if (!bundle.plan().equals(permit.planRef())) throw new IOException("COMPOSE_BUNDLE plan differs from the selected Root plan");
        FileRef planRef = file(permit.planRef()); planRef.verify();
        JsonNode plan = StrictJson.parse(Files.readAllBytes(Path.of(planRef.path())), 1_048_576);
        if (!StrictJson.text(plan.get("machine_id")).equals(permit.machineId())
                || !absolute(StrictJson.text(plan.get("runtime_root"))).equals(permit.runtimeRoot())
                || permit.deadline().isAfter(Instant.parse(StrictJson.text(plan.get("review_at_utc")))))
            throw new IOException("materialization plan machine/root/review differs");
        JsonNode quote = StrictJson.parse(bundle.quote(), 1_048_576);
        StrictJson.object(quote, Set.of("schema","machine_id","observed_at_utc","plan_ref","basis_ref","validation_ref",
                "producer_ref","runtime_root","files","campaign_score_junction","canonical_entry_paths","closure_entry_paths",
                "import_roots","canonical_entry_limit","logical_bytes","allocation_upper","prepare_peak_upper",
                "native32_current_sdk_override","artifact_cap_bytes","renderer_override_ref","ordinary_cycle_credit",
                "game_day_credit","original_actions_replayed"));
        if (!StrictJson.text(quote.get("schema")).equals("xar.current-saved-cold-quote/v5")
                || !StrictJson.text(quote.get("machine_id")).equals(permit.machineId())
                || !ExactRef.fromJson(quote.get("plan_ref")).equals(permit.planRef())
                || !absolute(StrictJson.text(quote.get("runtime_root"))).equals(permit.runtimeRoot())
                || !quote.get("original_actions_replayed").isBoolean() || quote.get("original_actions_replayed").booleanValue())
            throw new IOException("exact source-only quote contract required");
        StrictJson.integer(quote.get("ordinary_cycle_credit"),0,0); StrictJson.integer(quote.get("game_day_credit"),0,0);
        StrictJson.integer(quote.get("canonical_entry_limit"),8,8);
        for (String field : List.of("basis_ref","validation_ref","producer_ref")) {
            ExactRef reference = ExactRef.fromJson(quote.get(field));
            if (!reference.equals(ExactRef.fromJson(plan.get(field)))) throw new IOException("quoted original input differs: " + field);
            file(reference).verify();
        }
        Path junction = permit.runtimeRoot().resolve("campaign-score");
        if (!absolute(StrictJson.text(quote.get("campaign_score_junction").get("path"))).equals(junction))
            throw new IOException("quoted score junction mapping differs");
        CampaignScoreJunction.Binding binding=CampaignScoreJunction.Binding.decode(quote.get("campaign_score_junction"));
        Map<Path,byte[]> supplied = new HashMap<>();
        for (OriginalColdConsumerSession.ComposedFile file : bundle.files()) {
            Path path = absolute(file.path());
            if (supplied.put(path,file.content()) != null) throw new IOException("duplicate composed file path");
        }
        JsonNode files = quote.get("files");
        if (!files.isArray() || files.isEmpty() || files.size() > 192 || files.size() != supplied.size())
            throw new IOException("complete bounded quoted/composed file bijection required");
        List<Row> rows = new ArrayList<>(); Set<Path> paths = new HashSet<>(); Set<Path> directories = new HashSet<>();
        long logical = 0, allocated = 0;
        for (JsonNode value : files) {
            JsonNode row = StrictJson.object(value, Set.of("path","relative_path","bytes","sha256","mode","source_ref"));
            Path path = absolute(StrictJson.text(row.get("path"))); byte[] content = supplied.get(path);
            long bytes = StrictJson.integer(row.get("bytes"),1,1_048_576);
            String sha = StrictJson.text(row.get("sha256")); FileRef expected = new FileRef(path.toString(),bytes,sha);
            if (!paths.add(path) || content == null || content.length != bytes
                    || !org.xar.ck3.control.build.SdkSourceAssembly.Digest.of(content).sha256().equals(sha)
                    || path.startsWith(junction)) throw new IOException("quoted path/content/bijection differs");
            Path scope;
            if (row.get("relative_path").isNull()) {
                if (path.startsWith(permit.runtimeRoot())) throw new IOException("null relative path must be external");
                scope = permit.externalWriteRoots().stream().filter(path::startsWith).findFirst()
                        .orElseThrow(() -> new IOException("quoted external output is outside the finite Root scopes"));
            } else {
                String relative = StrictJson.text(row.get("relative_path"));
                Path rel = Path.of(relative);
                if (rel.isAbsolute() || !rel.normalize().equals(rel) || relative.contains("\\") || relative.contains(":")
                        || rel.startsWith("..") || !permit.runtimeRoot().resolve(rel).equals(path))
                    throw new IOException("exact runtime-relative mapping required");
                scope = permit.runtimeRoot();
            }
            if (path.equals(scope)) throw new IOException("a quoted file cannot replace its output scope");
            for (Path parent=path.getParent(); parent!=null && parent.startsWith(scope); parent=parent.getParent()) directories.add(parent);
            SharedSourceFiles.plainAncestors(path);
            if (Files.exists(path,LinkOption.NOFOLLOW_LINKS)) throw new IOException("create-only quoted destination already exists");
            String mode = StrictJson.text(row.get("mode")); FileRef source = null; Mode typed;
            if ("hardlink".equals(mode)) {
                source = file(ExactRef.fromJson(row.get("source_ref"))); source.verify();
                if (source.bytes()!=expected.bytes() || !source.sha256().equals(expected.sha256())
                        || absolute(source.path()).equals(path)) throw new IOException("exact immutable hardlink source required");
                typed=Mode.HARDLINK;
            } else if ("create-only".equals(mode) && row.get("source_ref").isNull()) {
                typed=Mode.CREATE_ONLY; allocated=Math.addExact(allocated,round(bytes));
            } else throw new IOException("explicit quoted output mode/source provenance required");
            logical=Math.addExact(logical,bytes); rows.add(new Row(path,typed,source,bytes,sha));
        }
        StrictJson.integer(quote.get("logical_bytes"),logical,logical);
        StrictJson.integer(quote.get("allocation_upper"),allocated,allocated);
        long charge = Math.addExact(allocated,Math.addExact(round(bundle.quote().length),4096L*(directories.size()+1)));
        guard(charge);
        List<Path> scopes = new ArrayList<>(permit.externalWriteRoots()); scopes.add(permit.runtimeRoot());
        for (Path scope : scopes) {
            SharedSourceFiles.plainAncestors(scope);
            if (Files.exists(scope,LinkOption.NOFOLLOW_LINKS)) throw new IOException("Root output scope must be fresh: " + scope);
        }
        SharedSourceFiles.plainAncestors(permit.quoteOutput());
        if (Files.exists(permit.quoteOutput(),LinkOption.NOFOLLOW_LINKS) || !Files.isDirectory(permit.quoteOutput().getParent()))
            throw new IOException("fresh quote in an existing admitted metadata directory required");
        for (Row row : rows) {
            guard(charge); Files.createDirectories(row.path().getParent()); SharedSourceFiles.plainAncestors(row.path());
            if (row.mode()==Mode.HARDLINK) SharedSourceFiles.linkObserved(Path.of(row.source().path()),row.path());
            else Files.write(row.path(),supplied.get(row.path()),StandardOpenOption.CREATE_NEW);
            FileRef actual=FileRef.measure(row.path());
            if (actual.bytes()!=row.bytes() || !actual.sha256().equals(row.sha256())) throw new IOException("materialized file readback differs");
        }
        planRef.verify(); for (Row row : rows) { if (row.source()!=null) row.source().verify(); new FileRef(row.path().toString(),row.bytes(),row.sha256()).verify(); }
        Set<Path> actual = new HashSet<>();
        try (var walk=Files.walk(permit.runtimeRoot())) {
            for (Path path : walk.toList()) {
                SharedSourceFiles.plainAncestors(path);
                if (Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS)) actual.add(path);
                else if (!Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS)) throw new IOException("unquoted special runtime entry");
            }
        }
        Set<Path> expectedRuntime=new HashSet<>(); for (Row row:rows) if(row.path().startsWith(permit.runtimeRoot())) expectedRuntime.add(row.path());
        if (!actual.equals(expectedRuntime) || Files.exists(junction,LinkOption.NOFOLLOW_LINKS))
            throw new IOException("exact materialized runtime files required; junction remains a separate original operation");
        guard(charge); Files.write(permit.quoteOutput(),bundle.quote(),StandardOpenOption.CREATE_NEW);
        FileRef result=FileRef.measure(permit.quoteOutput()); guard(charge);
        ExactRef quoteRef=new ExactRef(result.path(),result.bytes(),result.sha256());
        JunctionScope scope=new JunctionScope(this,bundle,quoteRef,List.copyOf(rows),charge,binding);
        scope.requireIssuedCurrent();
        return scope;
    }
    /**
     * Concrete, non-serializable continuation issued only after this materializer's actual
     * create/readback succeeded. A public Permit or quote ref cannot construct this scope.
     */
    public static final class JunctionScope {
        private final Thread thread=Thread.currentThread();
        private final RootNativeMapMaterializer issuer;
        private final OriginalColdConsumerSession.ComposedBundle bundle;
        private final ExactRef quote;
        private final List<Row> rows;
        private final long charge;
        private final CampaignScoreJunction.Binding binding;
        private ClosedInputsSessionAuthority session;
        private OriginalColdConsumerSession.PrepareJunction selected;
        private boolean submitted;
        private CampaignScoreJunction.Prepared javaPrepared;
        private WindowsFileWriterSession handoff;
        private JunctionScope(RootNativeMapMaterializer issuer,OriginalColdConsumerSession.ComposedBundle bundle,
                ExactRef quote,List<Row> rows,long charge,CampaignScoreJunction.Binding binding) {
            this.issuer=issuer;this.bundle=bundle;this.quote=quote;this.rows=rows;this.charge=charge;
            this.binding=binding;
        }
        public ExactRef quoteRef() throws IOException { requireIssuedCurrent(); return quote; }
        private void requireThread() {
            StrictJson.require(Thread.currentThread()==thread,"actual materialization scope belongs to its issuing Root thread");
        }
        private void requireIssuedCurrent() throws IOException {
            requireThread();issuer.guard(charge);
            verifySmall(bundle.plan(),1_048_576);
            JsonNode wire=StrictJson.parse(bundle.quote(),1_048_576);
            for(String field:List.of("basis_ref","validation_ref","producer_ref")) verifySmall(ExactRef.fromJson(wire.get(field)),1_048_576);
            verifySmall(binding.anchor(),16_384);
            byte[] actual=verifySmall(quote,1_048_576);
            StrictJson.require(java.util.Arrays.equals(actual,bundle.quote()),"same actual materialized quote bytes");
            for (Row row:rows) {
                SharedSourceFiles.plainAncestors(row.path());
                if(row.source()!=null) row.source().verify();
                new FileRef(row.path().toString(),row.bytes(),row.sha256()).verify();
            }
            SharedSourceFiles.plainAncestors(issuer.permit.runtimeRoot());
            SharedSourceFiles.plainAncestors(issuer.permit.quoteOutput());
        }
        void bind(ClosedInputsSessionAuthority authority,OriginalColdConsumerSession.Consumed actual) throws IOException {
            requireIssuedCurrent();
            StrictJson.require(session==null && actual.composedBundle().isPresent()
                    && actual.composedBundle().orElseThrow()==bundle && actual.processExit().kernelExitObserved()
                    && actual.processExit().exitCode()==0,"one actual successful same-session original composition");
            JsonNode result=StrictJson.parse(actual.originalConsumerReceipt(),OriginalWriterTransaction.MAX_PROTOCOL_BYTES);
            StrictJson.require("COMPOSE_BUNDLE".equals(StrictJson.text(result.get("operation")))
                    && java.util.Arrays.equals(StrictJson.canonical(result.get("operation_result"),1_048_576),bundle.quote()),
                    "scope retains actual original producer quote bytes");
            JsonNode wire=StrictJson.parse(bundle.quote(),1_048_576);
            StrictJson.require(issuer.permit.machineId().equals(authority.machineId())
                    && bundle.plan().equals(ExactRef.fromJson(wire.get("plan_ref")))
                    && authority.basisRef().equals(ExactRef.fromJson(wire.get("basis_ref")))
                    && authority.qualificationRef().equals(ExactRef.fromJson(wire.get("validation_ref")))
                    && !issuer.permit.deadline().isAfter(authority.deadline()),"actual Root preparation scope and owning session agree");
            session=authority;
        }
        void select(ClosedInputsSessionAuthority authority,OriginalColdConsumerSession.PrepareJunction operation) throws IOException {
            requireThread();
            StrictJson.require(session==authority && selected==null,"one junction attempt; UNKNOWN or failed preparation never replays");
            selected=Objects.requireNonNull(operation);
            requireCurrent(authority);
        }
        void requireCurrent(ClosedInputsSessionAuthority authority) throws IOException {
            requireThread();
            StrictJson.require(session==authority && selected!=null
                    && selected.plan().equals(bundle.plan()) && selected.quote().equals(quote)
                    && selected.runtimeRoot().equals(issuer.permit.runtimeRoot()),"same actual materialization plan, quote, runtime and Root session");
            requireIssuedCurrent();
        }
        void consumeInsideOriginalLock(ClosedInputsSessionAuthority authority) throws IOException {
            requireCurrent(authority);
            StrictJson.require(!submitted,"one original-lock junction submission; UNKNOWN is never retried");
            submitted=true;
        }
        CampaignScoreJunction.Prepared prepareJavaInsideOriginalLock(ClosedInputsSessionAuthority authority,
                OriginalColdConsumerSession.PrepareJunction operation) throws IOException {
            requireCurrent(authority);
            StrictJson.require(submitted && javaPrepared==null && selected.equals(operation),
                    "one concrete Java producer under the original writer lock");
            javaPrepared=CampaignScoreJunction.prepare(binding,authority.basisBytes(),issuer.permit.runtimeRoot(),
                    issuer.permit.deadline(),()-> {
                        try { requireCurrent(authority); }
                        catch(IOException failure) { throw new java.io.UncheckedIOException(failure); }
                    });
            requireJavaPhysicalCurrent(authority);
            return javaPrepared;
        }
        void requireJavaPhysicalCurrent(ClosedInputsSessionAuthority authority) throws IOException {
            requireCurrent(authority);
            StrictJson.require(submitted && javaPrepared!=null,"actual Java filesystem producer completed");
            javaPrepared.requireCurrent();
            StrictJson.require(javaPrepared.receipt().binding().equals(binding)
                    && javaPrepared.receipt().machineId().equals(issuer.permit.machineId()),
                    "actual Java result retains the exact quoted source binding");
        }
        void recordHandoff(ClosedInputsSessionAuthority authority,WindowsFileWriterSession process) throws IOException {
            requireCurrent(authority);
            StrictJson.require(javaPrepared!=null && handoff==null && process.actualCommandResult().isPresent()
                    && process.actualCommandResult().orElseThrow().passed()
                    && process.actualCommandResult().orElseThrow().accounting().activeProcesses()==0,
                    "actual original writer release, exit zero and Job zero before accepting junction");
            requireJavaPhysicalCurrent(authority);
            handoff=process;
        }
        void requireCompleted(ClosedInputsSessionAuthority authority,OriginalColdConsumerSession.PrepareOffline operation)
                throws IOException {
            requireJavaPhysicalCurrent(authority);
            StrictJson.require(handoff!=null && javaPrepared!=null && selected.plan().equals(operation.plan())
                    && selected.quote().equals(operation.quote()) && selected.runtimeRoot().equals(operation.runtimeRoot()),
                    "offline producer follows this actual completed one-use junction submission");
        }
        com.fasterxml.jackson.databind.node.ObjectNode handoffEvidence(ClosedInputsSessionAuthority authority) throws IOException {
            requireJavaPhysicalCurrent(authority);StrictJson.require(handoff!=null && javaPrepared!=null,"actual junction writer terminal required");
            var actual=handoff.actualCommandResult().orElseThrow();
            var row=StrictJson.object();row.put("schema","xar.java-junction-original-writer-handoff/v1");row.put("machine_id",issuer.permit.machineId());
            row.put("terminal_path",handoff.terminalPath().toString());row.put("stdout_path",handoff.stdoutPath().toString());
            row.put("status",actual.passed()?"PASSED":"FAILED");row.put("pid",actual.identity().pid());
            row.put("creation_filetime",actual.identity().creationFiletimeDecimal());row.put("exit_code",actual.exitCode());
            row.put("active_processes",actual.accounting().activeProcesses());
            row.put("peak_job_memory_bytes",actual.accounting().peakJobMemoryBytes());
            row.put("ledger_modified",false);row.put("raw_pending_modified",false);row.put("original_actions_replayed",false);
            return row;
        }
    }
    private static byte[] verifySmall(ExactRef reference,int maximum) throws IOException {
        StrictJson.require(reference.bytes()>0 && reference.bytes()<=maximum,"bounded materialization source");
        SharedSourceFiles.plainAncestors(Path.of(reference.path()));file(reference).verify();
        byte[] raw;
        try(var input=Files.newInputStream(Path.of(reference.path()))) {raw=input.readNBytes(maximum+1);}
        StrictJson.require(raw.length==reference.bytes()
                && org.xar.ck3.control.recovery.RecoveryEvidence.sha256(raw).equals(reference.sha256()),"exact actual materialization source bytes");
        file(reference).verify();return raw;
    }
    private void guard(long charge) throws IOException {
        if (!permit.machineId().equals(WindowsJobProcess.currentMachineId()) || !Instant.now().isBefore(permit.deadline())
                || charge>permit.allocationUpperLimitBytes()) throw new IOException("Root materialization scope expired or exhausted");
        file(permit.storageEvidence()).verify();
        try { finitePermitGuard.run(); } catch (RuntimeException error) { throw new IOException("supplemental finite materialization guard failed",error); }
    }
    private static FileRef file(ExactRef reference) { return new FileRef(reference.path(),reference.bytes(),reference.sha256()); }
    private static long round(long bytes) { return ((bytes+4095)/4096)*4096; }
    private static Path absolute(String value) { Path path=Path.of(value); normalized(path); return path; }
    private static void normalized(Path path) {
        if (path==null || !path.isAbsolute() || !path.normalize().equals(path)) throw new IllegalArgumentException("normalized absolute materialization path required");
    }
}
