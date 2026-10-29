package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;

/**
 * Mechanical late binding of a separately issuer-approved exact batch. No financial issuer,
 * Plan selection, capture execution, EXE access, renewal, recovery or UNKNOWN replay.
 */
public final class RawWindowAdmissionBatchMain {
    public static final String SCHEMA="xar.native-raw-window-admission-batch-authorization/v1";
    private static final int MAXIMUM_BYTES=65_536, MAXIMUM_PLANS=8;
    private static final String ISSUER="/root/budget_fast_lane";
    private RawWindowAdmissionBatchMain() { }

    /** Locator bytes are a distinct dedicated budget, never ordinary window CODE. */
    public record ReadCaps(Amounts windows,long locatorBytes,long locatorMetadataBytes,
            long identityApiBufferBytes,long admissionLogicalBytes) {
        public ReadCaps {
            Objects.requireNonNull(windows);nonnegative(locatorBytes);nonnegative(locatorMetadataBytes);
            nonnegative(identityApiBufferBytes);nonnegative(admissionLogicalBytes);
            require(admissionLogicalBytes>0 && admissionLogicalBytes<=MAXIMUM_PLANS*(long)MAXIMUM_BYTES,
                    "finite total Admission logical-byte cap required; not an allocated-byte measurement");
        }
        boolean contains(ReadCaps actual) {
            return windows.contains(actual.windows) && locatorBytes>=actual.locatorBytes
                    && locatorMetadataBytes>=actual.locatorMetadataBytes
                    && identityApiBufferBytes>=actual.identityApiBufferBytes
                    && admissionLogicalBytes>=actual.admissionLogicalBytes;
        }
    }
    /** Exact Plan approval also pins every offset, source proof, category limit, root and deadline. */
    public record ApprovedPlan(RawWindowPreparation.Mode mode,FileRef planRef,Consumer consumer,String requestRunId,
            String captureRunId,String preparedRequestPath,String admissionPath,String captureRoot,long wholeTopicCapBytes) {
        public ApprovedPlan {
            require(mode==RawWindowPreparation.Mode.WINDOWS || mode==RawWindowPreparation.Mode.LOCATOR,
                    "an exact existing capture Plan branch is required");
            bounded(planRef);Objects.requireNonNull(consumer);identifier(requestRunId);identifier(captureRunId);
            absolute(preparedRequestPath);absolute(admissionPath);absolute(captureRoot);
            nonnegative(wholeTopicCapBytes);require(wholeTopicCapBytes>0,"explicit issuer-approved whole-topic ceiling required");
        }
    }
    /** This file must be approved and pinned by the sole budget issuer before this program runs. */
    public record BatchAuthorization(String schema,String machineId,String issuer,String batchId,
            String observedAtUtc,String reviewAtUtc,FileRef financialGrantRef,FileRef operationalStandingRef,FileRef source17ProofRef,
            String admissionRoot,ReadCaps maximum,List<ApprovedPlan> plans) {
        public BatchAuthorization {
            require(SCHEMA.equals(schema),"exact admission batch schema required");machine(machineId);
            require(ISSUER.equals(issuer),"one independent budget issuer required");identifier(batchId);
            Instant observed=canonical(observedAtUtc), review=canonical(reviewAtUtc);
            require(observed.isBefore(review),"finite ordered batch review window required");
            Objects.requireNonNull(financialGrantRef);Objects.requireNonNull(operationalStandingRef);bounded(source17ProofRef);absolute(admissionRoot);
            Objects.requireNonNull(maximum);plans=List.copyOf(plans);
            require(!plans.isEmpty() && plans.size()<=MAXIMUM_PLANS,"one finite complete approved batch required");
            require(financialGrantRef.bytes()>0 && financialGrantRef.bytes()<=MAX_OUTPUT_BYTES,
                    "exact existing financial original required, never generated here");
            require(operationalStandingRef.bytes()>0 && operationalStandingRef.bytes()<=MAX_OUTPUT_BYTES,
                    "same-batch existing operational standing required; its live guards remain in the sole executor");
            var planRefs=new HashSet<FileRef>();var runs=new HashSet<String>();var captureRuns=new HashSet<String>();
            var paths=new HashSet<Path>();Path root=absolute(admissionRoot);
            for(ApprovedPlan plan:plans) {
                require(planRefs.add(plan.planRef()) && runs.add(plan.requestRunId()) && captureRuns.add(plan.captureRunId()),
                        "unique exact Plan and request/capture runs per approved batch");
                Path request=absolute(plan.preparedRequestPath()), admission=absolute(plan.admissionPath());
                require(!request.equals(admission) && paths.add(request) && paths.add(admission),
                        "unique fixed prepared-request and Admission paths required");
                require(admission.startsWith(root) && !admission.equals(root),"approved Admission must remain under its allowed root");
                require(!admission.equals(Path.of(plan.planRef().path())) && !admission.equals(Path.of(financialGrantRef.path()))
                        && !admission.equals(Path.of(source17ProofRef.path())) && !admission.equals(Path.of(operationalStandingRef.path())),
                        "output cannot replace an approved original");
            }
        }
    }
    /** Runtime supplies only exact prepared request originals, not new Plans, paths or caps. */
    public record PreparedRequestBinding(FileRef planRef,FileRef preparedRequestRef) {
        public PreparedRequestBinding {bounded(planRef);bounded(preparedRequestRef);}
    }
    public record PublishedAdmission(Consumer consumer,String requestRunId,String captureRunId,String captureRoot,
            long wholeTopicCapBytes,FileRef planRef,FileRef requestRef,FileRef admissionRef) {
        public PublishedAdmission {
            Objects.requireNonNull(consumer);identifier(requestRunId);identifier(captureRunId);absolute(captureRoot);
            nonnegative(wholeTopicCapBytes);require(wholeTopicCapBytes>0,"approved whole-topic ceiling required");
            bounded(planRef);bounded(requestRef);bounded(admissionRef);
        }
    }
    public record PreparedAdmissions(String batchId,FileRef authorizationRef,FileRef bindingsRef,
            FileRef operationalStandingRef,List<PublishedAdmission> admissions) {
        public PreparedAdmissions {identifier(batchId);bounded(authorizationRef);bounded(bindingsRef);Objects.requireNonNull(operationalStandingRef);admissions=List.copyOf(admissions);}
    }
    private record Checked(ApprovedPlan approved,PreparedRequestBinding binding,CaptureRequest request,
            Admission admission,SharedSourceFiles.DirectoryIdentity admissionParent) { }

    /** Six exact scalar arguments: batch path/bytes/SHA followed by binding-table path/bytes/SHA. */
    public static void main(String[] args)throws IOException {
        if(args.length!=6)throw new IllegalArgumentException("batchPath canonicalBytes SHA bindingTablePath canonicalBytes SHA required");
        PreparedAdmissions prepared=prepare(argument(args,0),argument(args,3),Clock.systemUTC());
        System.out.write(ControlBuild.strictMapper().writeValueAsBytes(prepared));System.out.write('\n');System.out.flush();
        if(System.out.checkError())throw new IOException("prepared Admission references could not be reported");
    }
    public static PreparedAdmissions prepare(FileRef authorizationRef,FileRef bindingsRef,Clock clock)throws IOException {
        Objects.requireNonNull(clock);bounded(authorizationRef);bounded(bindingsRef);
        byte[] original=exact(authorizationRef,MAXIMUM_BYTES);
        BatchAuthorization batch=RawWindowCaptureJson.decode(original,BatchAuthorization.class,MAXIMUM_BYTES);
        byte[] bindingBytes=exact(bindingsRef,MAXIMUM_BYTES);
        PreparedRequestBinding[] rawBindings=RawWindowCaptureJson.decode(bindingBytes,PreparedRequestBinding[].class,MAXIMUM_BYTES);
        if(rawBindings==null || rawBindings.length!=batch.plans().size())
            throw new IOException("every approved Plan must have exactly one binding");
        List<PreparedRequestBinding> bindings=List.of(rawBindings);
        fresh(batch,clock);
        if(!batch.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("actual prepare machine differs from batch");
        SharedSourceFiles.plainAncestors(absolute(batch.admissionRoot()));
        var rootIdentity=SharedSourceFiles.nativeDirectory(absolute(batch.admissionRoot()));
        exact(batch.financialGrantRef(),MAX_OUTPUT_BYTES);
        exact(batch.operationalStandingRef(),MAX_OUTPUT_BYTES);
        RawWindowImageProof.Proof proof=RawWindowImageProof.load(batch.source17ProofRef());
        if(!proof.machineId().equals(batch.machineId()))throw new IOException("Source17 proof belongs to another machine");
        List<Checked> checked=new ArrayList<>();var seen=new HashSet<FileRef>();
        Amounts windowCaps=new Amounts(0,0,0);long locator=0,locatorMetadata=0,identity=0,admissionBytes=0;
        for(ApprovedPlan approved:batch.plans()) {
            PreparedRequestBinding binding=bindings.stream().filter(value->value.planRef().equals(approved.planRef())).findFirst()
                    .orElseThrow(()->new IOException("approved Plan has no prepared request binding"));
            if(!seen.add(binding.planRef()) || bindings.stream().filter(value->value.planRef().equals(binding.planRef())).count()!=1)
                throw new IOException("duplicate Plan binding is not a complete authorized batch");
            RawWindowPreparation.Plan plan=RawWindowPreparation.decodePlan(approved.mode(),
                    exact(approved.planRef(),MAXIMUM_BYTES));
            CaptureRequest request=RawWindowCaptureJson.decodeRequest(exact(binding.preparedRequestRef(),MAXIMUM_BYTES));
            if(!Path.of(binding.preparedRequestRef().path()).equals(absolute(approved.preparedRequestPath()))
                    || !request.equals(plan.request(request.outputRootIdentity())) || !request.machineId().equals(batch.machineId())
                    || request.consumer()!=approved.consumer() || !request.runId().equals(approved.requestRunId())
                    || !request.outputRoot().equals(approved.captureRoot())
                    || !request.fullHashEvidenceRef().equals(batch.source17ProofRef()))
                throw new IOException("prepared request differs from its exact approved Plan/run/consumer/source");
            if(Instant.parse(request.reviewAtUtc()).isBefore(canonical(batch.reviewAtUtc())))
                throw new IOException("batch cannot extend the exact request review");
            if(!proof.inputPath().equals(request.inputPath()))throw new IOException("approved input spelling differs from original Source17 proof");
            requireDirectory(request);Path output=absolute(approved.admissionPath());absent(output);
            if(output.equals(Path.of(authorizationRef.path())) || output.equals(Path.of(bindingsRef.path())))
                throw new IOException("output collides with batch original");
            var parent=SharedSourceFiles.nativeDirectory(output.getParent());
            Admission admission=new Admission(ADMISSION_SCHEMA,batch.machineId(),request.consumer(),ISSUER,request.scope(),
                    binding.preparedRequestRef(),batch.financialGrantRef(),batch.reviewAtUtc());
            byte[] encoded=RawWindowCaptureJson.encode(admission);admissionBytes=Math.addExact(admissionBytes,encoded.length);
            // The financial issuer already checked current use/holds against this ceiling. This is only
            // a necessary lower bound, never a claim of whole-topic allocated usage or new permission.
            if(encoded.length>approved.wholeTopicCapBytes())throw new IOException("new Admission alone exceeds approved whole-topic ceiling");
            switch(request) {
                case Request windows -> {
                    windowCaps=new Amounts(Math.addExact(windowCaps.code(),windows.windowCaps().code()),
                            Math.addExact(windowCaps.metadata(),windows.windowCaps().metadata()),
                            Math.addExact(windowCaps.data(),windows.windowCaps().data()));
                }
                case RawWindowLocatorContract.Request exact -> {
                    locator=Math.addExact(locator,exact.segment().bytes());locatorMetadata=Math.addExact(locatorMetadata,1216);
                }
            }
            identity=Math.addExact(identity,request.fileIdentityApiBufferCap());
            checked.add(new Checked(approved,binding,request,admission,parent));
        }
        if(!batch.maximum().contains(new ReadCaps(windowCaps,locator,locatorMetadata,identity,admissionBytes)))
            throw new IOException("complete batch exceeds separately approved read or Admission byte caps");
        revalidate(batch,authorizationRef,bindingsRef,checked,rootIdentity,clock);
        List<PublishedAdmission> published=new ArrayList<>();
        for(Checked item:checked) {
            revalidate(batch,authorizationRef,bindingsRef,checked,rootIdentity,clock);
            absent(absolute(item.approved().admissionPath()));
            FileRef result=RawWindowPreparation.prepareAdmission(item.admission(),absolute(item.approved().admissionPath()));
            Admission actual=RawWindowCaptureJson.decode(exact(result,MAXIMUM_BYTES),Admission.class,MAXIMUM_BYTES);
            if(!item.admission().equals(actual))throw new IOException("actual shared Admission readback differs");
            published.add(new PublishedAdmission(item.request().consumer(),item.request().runId(),item.approved().captureRunId(),
                    item.request().outputRoot(),item.approved().wholeTopicCapBytes(),item.approved().planRef(),item.binding().preparedRequestRef(),result));
        }
        revalidate(batch,authorizationRef,bindingsRef,checked,rootIdentity,clock);
        for(PublishedAdmission item:published)exact(item.admissionRef(),MAXIMUM_BYTES);
        return new PreparedAdmissions(batch.batchId(),authorizationRef,bindingsRef,batch.operationalStandingRef(),published);
    }
    private static void revalidate(BatchAuthorization batch,FileRef authorization,FileRef bindings,List<Checked> checked,
            SharedSourceFiles.DirectoryIdentity rootIdentity,Clock clock)throws IOException {
        fresh(batch,clock);exact(authorization,MAXIMUM_BYTES);
        exact(bindings,MAXIMUM_BYTES);exact(batch.financialGrantRef(),MAX_OUTPUT_BYTES);
        exact(batch.operationalStandingRef(),MAX_OUTPUT_BYTES);
        exact(batch.source17ProofRef(),MAXIMUM_BYTES);
        if(!rootIdentity.equals(SharedSourceFiles.nativeDirectory(absolute(batch.admissionRoot()))))
            throw new IOException("approved admission root native identity drift");
        for(Checked item:checked) {
            exact(item.approved().planRef(),MAXIMUM_BYTES);
            exact(item.binding().preparedRequestRef(),MAXIMUM_BYTES);
            requireDirectory(item.request());
            if(!item.admissionParent().equals(SharedSourceFiles.nativeDirectory(absolute(item.approved().admissionPath()).getParent())))
                throw new IOException("Admission parent native identity drift; retain any partial output and do not retry");
        }
        fresh(batch,clock);
    }
    private static byte[] exact(FileRef ref,int maximum)throws IOException {
        SharedSourceFiles.plainAncestors(absolute(ref.path()));
        return RawWindowCaptureJson.exactBytes(ref,maximum);
    }
    private static void requireDirectory(CaptureRequest request)throws IOException {
        Path path=absolute(request.outputRoot());SharedSourceFiles.plainAncestors(path);
        if(!request.outputRootIdentity().equals(SharedSourceFiles.nativeDirectory(path)))
            throw new IOException("actual prepared-request output directory identity changed");
    }
    private static void absent(Path path)throws IOException {
        SharedSourceFiles.plainAncestors(path.getParent());
        if(!Files.isDirectory(path.getParent(),LinkOption.NOFOLLOW_LINKS) || Files.exists(path,LinkOption.NOFOLLOW_LINKS))
            throw new IOException("existing plain parent and absent fixed CREATE_NEW output required; no replay/resume");
    }
    private static void fresh(BatchAuthorization batch,Clock clock)throws IOException {
        Instant now=clock.instant();
        if(now.isBefore(canonical(batch.observedAtUtc())) || !now.isBefore(canonical(batch.reviewAtUtc())))
            throw new IOException("approved batch is not fresh; no implicit renewal");
    }
    private static Instant canonical(String value) {
        Objects.requireNonNull(value);Instant parsed=Instant.parse(value);
        require(parsed.toString().equals(value),"canonical UTC instant required");return parsed;
    }
    private static void bounded(FileRef ref) {
        Objects.requireNonNull(ref);absolute(ref.path());require(ref.bytes()>0 && ref.bytes()<=MAXIMUM_BYTES,"bounded exact metadata FileRef required");
    }
    private static FileRef argument(String[] args,int at) {
        require(args[at+1].matches("[1-9][0-9]*"),"canonical positive byte count required");
        FileRef ref=new FileRef(absolute(args[at]).toString(),Long.parseLong(args[at+1]),args[at+2]);bounded(ref);return ref;
    }
}

