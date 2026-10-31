package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;
import static org.xar.ck3.control.build.RawWindowAdmissionBatchMain.*;

/** Actual Windows directory/temp-file metadata plus Source17-shaped software DATA and Collector ports.
 * The retained real EXE original remains a separate parser fixture and is never relabeled or opened here. */
final class RawWindowAdmissionBatchMainTest {

    private record LauncherFailure(String uniqueId,String exceptionType,String message) { }
    private record LauncherResult(String machineId,String observedAtUtc,String status,List<String> methods,
            long found,long started,long succeeded,long failed,long skipped,long aborted,
            long containersFailed,long containersSkipped,long containersAborted,List<LauncherFailure> failures) { }
    /** Test-scope only: exact nine existing methods, no arguments or alternate test selection. */
    public static void main(String[] args)throws IOException {
        if(args.length!=0)throw new IllegalArgumentException("no arguments; exact nine Raw admission batch tests");
        var expected=java.util.Set.of("actualExistingPlanProducerBatchPublisherAndCollectorConsumeTheSameStrictAdmission","omittedExtraDuplicateOrUnapprovedPlanBindingsPublishNothing","actualRequestDriftAfterPreparationAndExactReferenceDriftAreBothRejected","directoryReplacementCannotReusePreparedNativeDirectoryIdentity","wrongIssuerMissingNullWrongTypesAliasesAndCanonicalTimeAreStrictlyRejected","capsExpiredReviewOutsideRootOrExistingOutputRejectTheCompleteBatchBeforePublication","publishedFixedPathsCannotReplayAnUnknownNativeOutcomeOrOverwriteAnyOriginal","operationalOrFinancialOriginalDriftIsNotHiddenByAnUnchangedApprovedRequest","driftAfterTheFirstPublicationRetainsEvidenceAndNeverResumesThePartiallyPublishedBatch");
        var config=org.junit.platform.launcher.core.LauncherConfig.builder().enableTestEngineAutoRegistration(false)
                .enableLauncherSessionListenerAutoRegistration(false).enableLauncherDiscoveryListenerAutoRegistration(false)
                .enableTestExecutionListenerAutoRegistration(false).enablePostDiscoveryFilterAutoRegistration(false)
                .addTestEngines(new org.junit.jupiter.engine.JupiterTestEngine()).build();
        var request=org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(RawWindowAdmissionBatchMainTest.class))
                .configurationParameter("junit.jupiter.execution.parallel.enabled","false")
                .configurationParameter("junit.jupiter.extensions.autodetection.enabled","false").build();
        var launcher=org.junit.platform.launcher.core.LauncherFactory.create(config);
        var plan=launcher.discover(request);var discovered=new java.util.TreeSet<String>();
        for(var root:plan.getRoots())for(var test:plan.getDescendants(root))if(test.isTest()) {
            var source=test.getSource().orElseThrow(()->new IllegalStateException("missing exact test method source"));
            if(!(source instanceof org.junit.platform.engine.support.descriptor.MethodSource method)
                    || !method.getClassName().equals(RawWindowAdmissionBatchMainTest.class.getName())
                    || !discovered.add(method.getMethodName()))throw new IllegalStateException("foreign/non-method/duplicate test");
        }
        if(!discovered.equals(expected))throw new IllegalStateException("exact nine persistent tests were not discovered");
        var listener=new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.execute(plan,listener);var summary=listener.getSummary();var failures=new ArrayList<LauncherFailure>();
        for(var failure:summary.getFailures()) {
            Throwable error=failure.getException();String message=String.valueOf(error.getMessage());
            failures.add(new LauncherFailure(failure.getTestIdentifier().getUniqueId(),error.getClass().getName(),
                    message.length()<=1024?message:message.substring(0,1024)));
        }
        boolean pass=summary.getTestsFoundCount()==9 && summary.getTestsStartedCount()==9 && summary.getTestsSucceededCount()==9
                && summary.getTestsFailedCount()==0 && summary.getTestsSkippedCount()==0 && summary.getTestsAbortedCount()==0
                && summary.getContainersFailedCount()==0 && summary.getContainersSkippedCount()==0
                && summary.getContainersAbortedCount()==0 && summary.getTotalFailureCount()==0;
        var result=new LauncherResult(WindowsJobProcess.currentMachineId(),Instant.now().toString(),pass?"PASS":"FAIL",
                List.copyOf(discovered),summary.getTestsFoundCount(),summary.getTestsStartedCount(),summary.getTestsSucceededCount(),
                summary.getTestsFailedCount(),summary.getTestsSkippedCount(),summary.getTestsAbortedCount(),
                summary.getContainersFailedCount(),summary.getContainersSkippedCount(),summary.getContainersAbortedCount(),List.copyOf(failures));
        byte[] output=ControlBuild.strictMapper().writeValueAsBytes(result);
        if(output.length>65536)throw new IOException("bounded exact test result exceeded");
        System.out.write(output);System.out.write('\n');System.out.flush();
        if(System.out.checkError())throw new IOException("actual test result output failed");
        if(!pass)System.exit(2);
    }

    @TempDir Path temporary;
    private static final String REVIEW="2099-01-01T00:00:00Z";
    private static final Clock FRESH=Clock.fixed(Instant.parse("2026-10-24T09:00:00Z"),ZoneOffset.UTC);
    private record Fixture(BatchAuthorization authorization,FileRef authorizationRef,FileRef bindingsRef,
            List<PreparedRequestBinding> bindings,List<CaptureRequest> requests) { }
    private FileRef write(String name,Object value)throws IOException {
        Path path=temporary.resolve(name);byte[] bytes=ControlBuild.strictMapper().writeValueAsBytes(value);
        Files.write(path,bytes,StandardOpenOption.CREATE_NEW);
        return RawWindowCaptureJson.reference(path,bytes);
    }
    private Fixture fixture(int count)throws Exception {
        String machine=WindowsJobProcess.currentMachineId();
        // Software-only local fixture: current actual Windows runner, bounded temp input, no retained EXE access.
        Path input=temporary.resolve("software-input.bin");
        Files.write(input,new byte[4096],StandardOpenOption.CREATE_NEW);
        SharedSourceFiles.NativeFile nativeFile=SharedSourceFiles.nativeFile(input);
        FileRef proofRef=write("source17.json",softwareSource17(machine,input,nativeFile));
        RawWindowImageProof.Proof proof=RawWindowImageProof.load(proofRef);
        if(!proof.machineId().equals(machine))
            throw new IOException("software fixture machine must match current actual Windows runner");
        // Software originals only. No actual financial/operational authority is issued by a test.
        FileRef financial=write("software-financial.json",new SoftwareOriginal("NO_EXECUTION_AUTHORITY"));
        FileRef standing=write("software-standing.json",new SoftwareOriginal("NO_EXECUTION_AUTHORITY"));
        List<ApprovedPlan> approved=new ArrayList<>();List<PreparedRequestBinding> bindings=new ArrayList<>();
        List<CaptureRequest> requests=new ArrayList<>();
        for(int index=0;index<count;index++) {
            Path output=Files.createDirectory(temporary.resolve("capture-"+index));
            String run="software-raw-"+index;
            var plan=new RawWindowPreparation.WindowPlan(RawWindowPreparation.WINDOW_PLAN_SCHEMA,machine,Consumer.values()[index],
                    run,proof.inputPath(),proofRef,output.toString(),List.of(new Window("metadata",Kind.METADATA,1024,4)),
                    new Amounts(0,4,0),8192,18432,32768,REVIEW);
            FileRef planRef=write("plan-"+index+".json",plan);
            Path requestPath=temporary.resolve("request-"+index+".json");
            var prepared=RawWindowPreparation.prepare(plan,requestPath);
            approved.add(new ApprovedPlan(RawWindowPreparation.Mode.WINDOWS,planRef,plan.consumer(),run,"capture-"+index,
                    requestPath.toString(),temporary.resolve("admission-"+index+".json").toString(),output.toString(),1_048_576));
            bindings.add(new PreparedRequestBinding(planRef,prepared.encodedRequest()));requests.add(prepared.request());
        }
        var maximum=new ReadCaps(new Amounts(0,count*4L,0),0,0,count*8192L,count*65536L);
        var authorization=new BatchAuthorization(SCHEMA,machine,"/root/budget_fast_lane","software-batch",
                "2026-10-24T08:59:00Z",REVIEW,financial,standing,proofRef,temporary.toString(),maximum,approved);
        return new Fixture(authorization,write("batch.json",authorization),write("bindings.json",bindings),List.copyOf(bindings),List.copyOf(requests));
    }

    private record SoftwareIdentity(String fileId64Decimal,String fileId128Decimal,String volumeSerial64Decimal,long size,String creationFiletime,
            String lastwriteFiletime,String changeFiletime,int attributes,long links) { }

    private ObjectNode softwareSource17(String machine,Path input,SharedSourceFiles.NativeFile nativeFile) throws IOException {
        String path=input.toString();
        String finalPath=SharedSourceFiles.nativePathValue(path);
        String legacyDecimal=new BigInteger(nativeFile.legacyFileIdHex(),16).toString();
        // Identity/time/size/link fields below are the actual newly created SOFTWARE input observation.
        // attributes=32 is explicit parser-fixture DATA, not an independently observed attribute value.
        SoftwareIdentity identity=new SoftwareIdentity(legacyDecimal,nativeFile.fileIdDecimal(),nativeFile.volumeSerialDecimal(),nativeFile.logicalBytes(),
                nativeFile.creationFiletimeDecimal(),nativeFile.lastWriteFiletimeDecimal(),nativeFile.changeFiletimeDecimal(),32,nativeFile.linkCount());
        ObjectNode root=ControlBuild.strictMapper().createObjectNode();
        root.put("schema","xar.g2.m7.native-static-window-source/v1");
        root.put("machine_id",machine);
        root.put("observed_at_utc",Instant.now().toString());
        // These required schema/status/handle-policy wire literals exercise the strict parser.
        // They do not assert a real CK3 producer, two native samples, or a retained hash/objdump handle.
        root.put("status","FRESH_SOURCE_MAPPED_STATIC_WINDOWS_ONLY");
        root.put("input",path);
        root.put("final_path",finalPath);
        root.putArray("ancestor_paths_checked_no_reparse");
        root.put("handle_policy","GENERIC_READ + FILE_SHARE_READ only; denied write/delete, same handle held across hash/read/objdump/prepost");
        root.set("before",ControlBuild.strictMapper().valueToTree(identity));
        root.set("after",ControlBuild.strictMapper().valueToTree(identity));
        root.put("sha256",RawWindowCaptureJson.hash(Files.readAllBytes(input)));
        root.put("file_version","SOFTWARE_TEST_NO_EXECUTABLE_VERSION");
        root.set("pe",ControlBuild.strictMapper().createObjectNode());
        root.put("objdump_version","SOFTWARE_TEST_NOT_RUN");
        root.putArray("spans");
        ObjectNode budget=ControlBuild.strictMapper().createObjectNode();
        budget.put("one_full_sha_stream_bytes",nativeFile.logicalBytes());
        budget.put("code_bytes",0);
        budget.put("metadata_bytes_including_version_buffer",0);
        budget.putNull("physical_io_total_bytes");
        budget.put("physical_io_note","SOFTWARE TEST ONLY; no real EXE or objdump run");
        root.set("budget",budget);
        root.put("game_pid","SOFTWARE_TEST_NOT_RUN");
        root.put("authority","SOFTWARE TEST DATA ONLY; current temp-file identity and SHA, not a CK3 producer or same-handle hash/objdump qualification; no execution authority");
        return root;
    }
    private record SoftwareOriginal(String status) { }
    private FileRef changedBatch(Fixture fixture,String name,List<ApprovedPlan> plans,ReadCaps maximum)throws IOException {
        var old=fixture.authorization();
        return write(name,new BatchAuthorization(old.schema(),old.machineId(),old.issuer(),old.batchId(),old.observedAtUtc(),
                old.reviewAtUtc(),old.financialGrantRef(),old.operationalStandingRef(),old.source17ProofRef(),old.admissionRoot(),maximum,plans));
    }
    @Test void actualExistingPlanProducerBatchPublisherAndCollectorConsumeTheSameStrictAdmission()throws Exception {
        Fixture fixture=fixture(2);PreparedAdmissions prepared=prepare(fixture.authorizationRef(),fixture.bindingsRef(),FRESH);
        assertEquals(2,prepared.admissions().size());assertEquals(fixture.authorization().operationalStandingRef(),prepared.operationalStandingRef());
        assertEquals(prepared,RawWindowCaptureJson.decode(ControlBuild.strictMapper().writeValueAsBytes(prepared),PreparedAdmissions.class,65536));
        for(int index=0;index<2;index++) {
            PublishedAdmission published=prepared.admissions().get(index);CaptureRequest request=fixture.requests().get(index);
            Admission admission=RawWindowCaptureJson.decode(RawWindowCaptureJson.exactBytes(published.admissionRef(),65536),Admission.class,65536);
            assertEquals(request.consumer(),published.consumer());assertEquals(request.runId(),published.requestRunId());
            assertEquals(fixture.authorization().plans().get(index).captureRunId(),published.captureRunId());
            assertEquals(request.outputRoot(),published.captureRoot());assertEquals(1_048_576,published.wholeTopicCapBytes());
            assertEquals(fixture.bindings().get(index).preparedRequestRef(),admission.requestRef());
            assertEquals(fixture.authorization().financialGrantRef(),admission.financialGrantRef());
            assertEquals(request,RawWindowCaptureJson.decodeRequest(RawWindowCaptureJson.exactBytes(admission.requestRef(),65536)));
            var proof=RawWindowImageProof.load(request.fullHashEvidenceRef());
            var ports=new SoftwarePorts((Request)request,proof,false);
            Result actual=RawWindowCollector.execute(admission,published.admissionRef(),(Request)request,proof,ports);
            assertEquals(Status.COMPLETE,actual.status());assertEquals(1,ports.reads);
            assertEquals(new Amounts(0,4,0),actual.counts().reportedRead());
            assertFalse(actual.counts().physicalIoMeasured());assertNull(actual.counts().totalPhysicalIoBytes());
        }
    }
    @Test void omittedExtraDuplicateOrUnapprovedPlanBindingsPublishNothing()throws Exception {
        Fixture fixture=fixture(2);
        for(List<PreparedRequestBinding> bad:List.of(List.of(fixture.bindings().getFirst()),
                List.of(fixture.bindings().getFirst(),fixture.bindings().getFirst()),
                List.of(fixture.bindings().getFirst(),fixture.bindings().getLast(),fixture.bindings().getLast()))) {
            FileRef table=write("bad-bindings-"+bad.size()+"-"+System.nanoTime()+".json",bad);
            assertThrows(IOException.class,()->prepare(fixture.authorizationRef(),table,FRESH));
        }
        for(ApprovedPlan plan:fixture.authorization().plans())assertFalse(Files.exists(Path.of(plan.admissionPath())));
    }
    @Test void actualRequestDriftAfterPreparationAndExactReferenceDriftAreBothRejected()throws Exception {
        Fixture fixture=fixture(1);var binding=fixture.bindings().getFirst();Path path=Path.of(binding.preparedRequestRef().path());
        ObjectNode original=(ObjectNode)ControlBuild.strictMapper().readTree(Files.readAllBytes(path));
        ((ObjectNode)original.withArray("windows").get(0)).put("file_offset",2048);
        byte[] drifted=ControlBuild.strictMapper().writeValueAsBytes(original);Files.write(path,drifted);
        assertThrows(IOException.class,()->prepare(fixture.authorizationRef(),fixture.bindingsRef(),FRESH));
        FileRef rehashed=RawWindowCaptureJson.reference(path,drifted);
        FileRef table=write("rehashed-bindings.json",List.of(new PreparedRequestBinding(binding.planRef(),rehashed)));
        assertThrows(IOException.class,()->prepare(fixture.authorizationRef(),table,FRESH));
        assertFalse(Files.exists(Path.of(fixture.authorization().plans().getFirst().admissionPath())));
    }
    @Test void directoryReplacementCannotReusePreparedNativeDirectoryIdentity()throws Exception {
        Fixture fixture=fixture(1);Path root=Path.of(fixture.requests().getFirst().outputRoot());
        Files.move(root,root.resolveSibling("retained-old-directory"));Files.createDirectory(root);
        assertThrows(IOException.class,()->prepare(fixture.authorizationRef(),fixture.bindingsRef(),FRESH));
        assertFalse(Files.exists(Path.of(fixture.authorization().plans().getFirst().admissionPath())));
    }
    @Test void wrongIssuerMissingNullWrongTypesAliasesAndCanonicalTimeAreStrictlyRejected()throws Exception {
        Fixture fixture=fixture(1);byte[] valid=ControlBuild.strictMapper().writeValueAsBytes(fixture.authorization());
        for(String key:List.of("issuer","plans","source17_proof_ref","operational_standing_ref","maximum")) {
            ObjectNode node=(ObjectNode)ControlBuild.strictMapper().readTree(valid);node.remove(key);
            ObjectNode missingNode=node;
            assertThrows(IOException.class,()->RawWindowCaptureJson.decode(ControlBuild.strictMapper().writeValueAsBytes(missingNode),BatchAuthorization.class,65536),key);
            node=(ObjectNode)ControlBuild.strictMapper().readTree(valid);node.putNull(key);ObjectNode nullNode=node;
            assertThrows(IOException.class,()->RawWindowCaptureJson.decode(ControlBuild.strictMapper().writeValueAsBytes(nullNode),BatchAuthorization.class,65536),key);
        }
        for(String field:List.of("issuer","review_at_utc","admission_root")) {
            ObjectNode node=(ObjectNode)ControlBuild.strictMapper().readTree(valid);node.put(field,true);
            assertThrows(IOException.class,()->RawWindowCaptureJson.decode(ControlBuild.strictMapper().writeValueAsBytes(node),BatchAuthorization.class,65536));
        }
        ObjectNode wrong=(ObjectNode)ControlBuild.strictMapper().readTree(valid);wrong.put("issuer","/root/executor");
        assertThrows(IOException.class,()->RawWindowCaptureJson.decode(ControlBuild.strictMapper().writeValueAsBytes(wrong),BatchAuthorization.class,65536));
        ObjectNode alias=(ObjectNode)ControlBuild.strictMapper().readTree(valid);alias.put("automatic_renewal",true);
        assertThrows(IOException.class,()->RawWindowCaptureJson.decode(ControlBuild.strictMapper().writeValueAsBytes(alias),BatchAuthorization.class,65536));
        ObjectNode offset=(ObjectNode)ControlBuild.strictMapper().readTree(valid);offset.put("review_at_utc","2099-01-01T00:00:00+00:00");
        assertThrows(IOException.class,()->RawWindowCaptureJson.decode(ControlBuild.strictMapper().writeValueAsBytes(offset),BatchAuthorization.class,65536));
        for(String token:List.of("true","1.0","\"1048576\"","null")) {
            ObjectNode node=(ObjectNode)ControlBuild.strictMapper().readTree(valid);
            ((ObjectNode)node.withArray("plans").get(0)).set("whole_topic_cap_bytes",ControlBuild.strictMapper().readTree(token));
            assertThrows(IOException.class,()->RawWindowCaptureJson.decode(ControlBuild.strictMapper().writeValueAsBytes(node),BatchAuthorization.class,65536));
        }
    }
    @Test void capsExpiredReviewOutsideRootOrExistingOutputRejectTheCompleteBatchBeforePublication()throws Exception {
        Fixture fixture=fixture(2);var auth=fixture.authorization();
        var insufficient=new ReadCaps(new Amounts(0,7,0),0,0,16384,131072);
        FileRef badCaps=changedBatch(fixture,"bad-caps.json",auth.plans(),insufficient);
        assertThrows(IOException.class,()->prepare(badCaps,fixture.bindingsRef(),FRESH));
        ApprovedPlan approved=auth.plans().getFirst();
        ApprovedPlan impossible=new ApprovedPlan(approved.mode(),approved.planRef(),approved.consumer(),approved.requestRunId(),
                approved.captureRunId(),approved.preparedRequestPath(),approved.admissionPath(),approved.captureRoot(),1);
        FileRef badTopic=changedBatch(fixture,"bad-topic-cap.json",List.of(impossible,auth.plans().getLast()),auth.maximum());
        assertThrows(IOException.class,()->prepare(badTopic,fixture.bindingsRef(),FRESH));
        assertThrows(IOException.class,()->prepare(fixture.authorizationRef(),fixture.bindingsRef(),Clock.fixed(Instant.parse(REVIEW),ZoneOffset.UTC)));
        ApprovedPlan first=auth.plans().getFirst();
        assertThrows(IllegalArgumentException.class,()->new BatchAuthorization(auth.schema(),auth.machineId(),auth.issuer(),auth.batchId(),
                auth.observedAtUtc(),auth.reviewAtUtc(),auth.financialGrantRef(),auth.operationalStandingRef(),auth.source17ProofRef(),temporary.resolve("capture-0").toString(),
                auth.maximum(),auth.plans()));
        Path existing=Path.of(auth.plans().getLast().admissionPath());byte[] retained={1,2,3};Files.write(existing,retained,StandardOpenOption.CREATE_NEW);
        assertThrows(IOException.class,()->prepare(fixture.authorizationRef(),fixture.bindingsRef(),FRESH));
        assertFalse(Files.exists(Path.of(first.admissionPath())));assertArrayEquals(retained,Files.readAllBytes(existing));
    }
    @Test void publishedFixedPathsCannotReplayAnUnknownNativeOutcomeOrOverwriteAnyOriginal()throws Exception {
        Fixture fixture=fixture(1);PreparedAdmissions prepared=prepare(fixture.authorizationRef(),fixture.bindingsRef(),FRESH);
        PublishedAdmission published=prepared.admissions().getFirst();byte[] original=Files.readAllBytes(Path.of(published.admissionRef().path()));
        Admission admission=RawWindowCaptureJson.decode(original,Admission.class,65536);
        Request request=(Request)fixture.requests().getFirst();var proof=RawWindowImageProof.load(request.fullHashEvidenceRef());
        var ports=new SoftwarePorts(request,proof,true);
        Result uncertain=RawWindowCollector.execute(admission,published.admissionRef(),request,proof,ports);
        assertEquals(Status.READ_OUTCOME_UNKNOWN,uncertain.status());assertEquals(1,ports.reads);
        assertThrows(IOException.class,()->prepare(fixture.authorizationRef(),fixture.bindingsRef(),FRESH));
        assertEquals(1,ports.reads);assertArrayEquals(original,Files.readAllBytes(Path.of(published.admissionRef().path())));
    }
    @Test void operationalOrFinancialOriginalDriftIsNotHiddenByAnUnchangedApprovedRequest()throws Exception {
        Fixture fixture=fixture(1);
        for(FileRef ref:List.of(fixture.authorization().operationalStandingRef(),fixture.authorization().financialGrantRef())) {
            Path path=Path.of(ref.path());byte[] original=Files.readAllBytes(path);Files.writeString(path,"drift");
            assertThrows(IOException.class,()->prepare(fixture.authorizationRef(),fixture.bindingsRef(),FRESH));
            Files.write(path,original);
        }
        assertFalse(Files.exists(Path.of(fixture.authorization().plans().getFirst().admissionPath())));
    }
    @Test void driftAfterTheFirstPublicationRetainsEvidenceAndNeverResumesThePartiallyPublishedBatch()throws Exception {
        Fixture fixture=fixture(2);Path first=Path.of(fixture.authorization().plans().getFirst().admissionPath());
        var changed=new java.util.concurrent.atomic.AtomicBoolean();
        Clock drift=new Clock() {
            public java.time.ZoneId getZone(){return ZoneOffset.UTC;}
            public Clock withZone(java.time.ZoneId zone){return FRESH.withZone(zone);}
            public Instant instant() {
                if(Files.exists(first) && changed.compareAndSet(false,true)) {
                    try {Files.writeString(Path.of(fixture.authorization().financialGrantRef().path()),"changed-after-first");}
                    catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
                }
                return FRESH.instant();
            }
        };
        assertThrows(IOException.class,()->prepare(fixture.authorizationRef(),fixture.bindingsRef(),drift));
        assertTrue(changed.get());assertTrue(Files.exists(first));
        assertFalse(Files.exists(Path.of(fixture.authorization().plans().getLast().admissionPath())));
        assertThrows(IOException.class,()->prepare(fixture.authorizationRef(),fixture.bindingsRef(),FRESH));
    }
    private static final class SoftwarePorts implements RawWindowCollector.Ports {
        private final Request request;private final RawWindowImageProof.Proof proof;private final boolean unknown;
        private final SharedSourceFiles.NativeFile file;int reads;
        SoftwarePorts(Request request,RawWindowImageProof.Proof proof,boolean unknown) {
            this.request=request;this.proof=proof;this.unknown=unknown;var id=proof.identity();
            String legacy=new BigInteger(id.fileId64Decimal()).toString(16);
            legacy="0".repeat(16-legacy.length())+legacy;
            // Source17 has no legacy 32-bit volume field. This software-only port uses an independent zero;
            // it never truncates the actual 64-bit serial or claims a newly observed native file.
            file=new SharedSourceFiles.NativeFile(id.volumeSerial64Decimal(),id.fileId128Decimal(),"0",
                    legacy,id.creationFiletime(),id.lastwriteFiletime(),id.changeFiletime(),id.size(),id.size(),id.links());
        }
        public String machineId(){return request.machineId();}
        public void startJournal(Started ignored) { }
        public void append(Event ignored) { }
        public void openInput() { }
        public FileProbe held(){return new FileProbe(ProbeStatus.OBSERVED,file,proof.inputPath(),"");}
        public FileProbe path(){return held();}
        public DirectoryProbe directory(){return new DirectoryProbe(ProbeStatus.OBSERVED,request.outputRootIdentity(),"");}
        public ReadResult read(ReadRange range) {
            reads++;return unknown?new ReadResult(ReadStatus.OUTCOME_UNKNOWN,null,0,"software unknown"):
                    new ReadResult(ReadStatus.COMPLETE,new byte[range.length()],0,"");
        }
        public RawArtifact preserveRaw(int index,byte[] actual){return new RawArtifact(OutputStatus.CREATED_VERIFIED,
                String.format(java.util.Locale.ROOT,"window-%03d.raw",index),(long)actual.length,RawWindowCaptureJson.hash(actual),"");}
        public void publishBody(byte[] actual)throws IOException {RawWindowCaptureJson.decode(actual,Body.class,MAX_OUTPUT_BYTES);}
        public long fileIdentityApiBufferChargeUpper(){return request.fileIdentityApiBufferCap();}
        public CloseStatus closeInput(){return CloseStatus.CLOSED;}
        public void close() { }
    }
}
