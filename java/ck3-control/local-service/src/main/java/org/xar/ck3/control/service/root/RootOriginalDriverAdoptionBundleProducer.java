package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeTransportDiagnostics.AdoptionRefusalReason;
import org.xar.ck3.control.service.root.RootOriginalDriverColdFixture.AdoptionFixture;
import org.xar.ck3.control.service.root.RootOriginalDriverColdFixture.Expected;

/** Original held HELLO + actual private import classifier -> immutable regression DATA.
 * No packet, expected classification, private load, process or Game is manufactured here. */
public final class RootOriginalDriverAdoptionBundleProducer {
    private RootOriginalDriverAdoptionBundleProducer(){ }
    public static String caseName(org.xar.ck3.control.platform.NativeLaunchPlan actual) {
        String request=Objects.requireNonNull(actual).requestId();
        return request.length()<=64?request:"original-"+OriginalDriverJournal.sha256(request.getBytes(java.nio.charset.StandardCharsets.UTF_8)).substring(0,32);
    }
    public static final class Captured {
        private final Expected expected;private final ExactRef classification;
        private final RootOriginalDriverJournal.Status status;private final Optional<String> originalFullSha;
        private final ExactRef request;private final String session;private final List<SharedSourceFiles.Witness> originals;
        private final Optional<DriverBootstrap.OriginalAdoptionRefused> refusal;
        private Captured(Expected expected,ExactRef classification,RootOriginalDriverJournal.Status status,Optional<String> originalFullSha,
                ExactRef request,String session,List<SharedSourceFiles.Witness> originals,Optional<DriverBootstrap.OriginalAdoptionRefused> refusal) {
            this.expected=expected;this.classification=classification;this.status=status;this.originalFullSha=originalFullSha;
            this.request=request;this.session=session;this.originals=List.copyOf(originals);this.refusal=refusal;
        }
        public Expected expected(){return expected;}
        public ExactRef classificationEvidence(){return classification;}
        public void requireAccepted()throws DriverBootstrap.OriginalAdoptionRefused {if(refusal.isPresent())throw refusal.orElseThrow();}
        private void requireOriginals()throws IOException {for(var source:originals)SharedSourceFiles.assertUnchanged(source);}
    }
    /** The actual Root keeps this collector through failed first adoption, retaining original refusal evidence. */
    public static final class Collector {
        private final RootRuntimeContext context;private final List<Captured> captured=new ArrayList<>();
        public Collector(RootRuntimeContext actual)throws IOException {
            context=Objects.requireNonNull(actual);context.game().verify();
            StrictJson.require(context.archive().writer()==context.writer(),"actual original writer archive required");
        }
        public synchronized List<Captured> captured(){return List.copyOf(captured);}
        public synchronized Captured classify(Session same,RootOriginalDriverJournal.OriginalJournalLoad original,String caseName)throws IOException {
            context.writer().requireSession(same);context.game().verify();original.requireRetained(same);
            StrictJson.require(caseName!=null&&caseName.matches("[A-Za-z0-9_-]{1,64}"),"exact finite original case name required");
            var transport=context.transport();var actual=original.requireActualHello(same,transport);
            StrictJson.require(actual.game().equals(context.game().generation())&&actual.sessionId().equals(context.game().sessionId()),"actual captured HELLO belongs to another physical Game/session");
            byte[] packet=transport.originalHello().packet().value();
            ExactRef hello=context.archive().preserveArtifact(same,packet,1<<20);
            Optional<DriverBootstrap.OriginalAdoptionRefused> failure=Optional.empty();
            try {DriverBootstrap.requireOriginalAdoption(same,transport,original);}
            catch(DriverBootstrap.OriginalAdoptionRefused refused){failure=Optional.of(refused);}
            // Generic IO/source/resource errors propagate; they never become one of the four cases.
            original.requireRetained(same);context.game().verify();
            AdoptionRefusalReason reason=failure.map(DriverBootstrap.OriginalAdoptionRefused::reason).orElse(null);
            if(reason!=null) {
                var diagnostic=transport.diagnostics().production().orElseThrow(()->new IOException("actual adoption refusal diagnostics absent"));
                var observed=diagnostic.adoption();
                StrictJson.require(observed instanceof org.xar.ck3.control.nativebridge.NativeTransportDiagnostics.Observed,"actual refusal was not recorded by the sole adopter");
                var recorded=((org.xar.ck3.control.nativebridge.NativeTransportDiagnostics.Observed)observed).refusal().orElseThrow();
                StrictJson.require(recorded.reason()==reason&&recorded.session().equals(actual)
                        &&java.util.Arrays.equals(recorded.originalHello().original().packet().value(),packet),"captured classification differs from actual source-bound refusal");
            }
            var body=StrictJson.object();body.put("schema","xar.java-original-adoption-classification/v1");body.put("machine_id",actual.machineId());
            body.put("observed_at_utc",context.clock().instant().toString());body.put("case_name",caseName);body.put("session_id",actual.sessionId());
            body.set("original_hello",hello.toJson());body.put("game_pid",actual.game().pid());body.put("game_creation_filetime",actual.game().creationFiletime().value().toString());
            body.put("original_status",original.status().name());body.set("frozen_run_request",original.frozenProfile().requestReference().toJson());
            body.set("source",context.source().sourceRef().toJson());
            if(reason==null){body.putNull("refusal");body.put("positive_scope","original four-guard acceptance only; no Known/Ready/PONG or gameplay credit");}
            else {var rejected=body.putObject("refusal");rejected.put("reason",reason.wire());rejected.put("exception_type",failure.orElseThrow().getClass().getName());rejected.put("message",failure.orElseThrow().getMessage());}
            var inputs=body.putArray("original_inputs");original.originalReferences().forEach(ref->inputs.add(ref.toJson()));
            ExactRef classification=context.archive().preserveArtifact(same,ContinuityJson.canonical(body),1<<20);
            var sources=new ArrayList<SharedSourceFiles.Witness>();
            for(ExactRef ref:original.originalReferences())sources.add(retain(ref));sources.add(retain(hello));sources.add(retain(classification));
            Optional<String> full=(original.status()==RootOriginalDriverJournal.Status.MISSING||original.status()==RootOriginalDriverJournal.Status.JOURNAL_INVALID)
                    ?Optional.empty():Optional.of(OriginalDriverJournal.sha256(original.fullBytes()));
            var expected=new Expected(caseName,hello,actual.game().pid(),actual.game().creationFiletime().value().toString(),reason);
            Captured result=new Captured(expected,classification,original.status(),full,original.frozenProfile().requestReference(),actual.sessionId(),sources,failure);
            result.requireOriginals();captured.add(result);return result;
        }
    }
    public record Produced(FileWitness fixture,AdoptionFixture data,List<ExactRef> actualClassifications) {
        public Produced {Objects.requireNonNull(fixture);Objects.requireNonNull(data);actualClassifications=List.copyOf(actualClassifications);}
        public ExactRef reference(){return fixture.reference();}
    }
    /** Root calls with source-issued captures and an independently admitted output root. No JSON capture constructor exists. */
    public static Produced produce(ExactRef actualColdFixture,List<Captured> actualCaptures,ContinuityWriter publicationWriter,
            RootRuntimeStorageGuard actualStorage,CheckpointFiles sameGuardedFiles,Path target,Clock clock)throws IOException {
        Objects.requireNonNull(clock);Objects.requireNonNull(publicationWriter);Objects.requireNonNull(actualStorage);Objects.requireNonNull(sameGuardedFiles);
        RootOriginalDriverColdFixture.Fixture cold=RootOriginalDriverColdFixture.readExact(actualColdFixture);
        actualCaptures=List.copyOf(actualCaptures);StrictJson.require(!actualCaptures.isEmpty()&&actualCaptures.size()<=32,"finite source-issued actual captures required");
        var reasons=EnumSet.noneOf(AdoptionRefusalReason.class);var expected=new ArrayList<Expected>();var refs=new ArrayList<ExactRef>();int positive=0;
        for(Captured capture:actualCaptures) {
            capture.requireOriginals();var one=cold.cases().stream().filter(item->item.name().equals(capture.expected.caseName())).findFirst()
                    .orElseThrow(()->new IOException("actual classification has no matching original cold case"));
            StrictJson.require(one.runRequest().equals(capture.request)&&one.expectedStatus()==capture.status,"actual classifier and cold issuer refer to different originals");
            StrictJson.require(Objects.equals(one.expectedFullPayloadSha256(),capture.originalFullSha.orElse(null)),"actual complete original Driver changed between cold and adoption producers");
            var lease=RootOriginalDriverColdFixture.record(one.storageLease(),1<<20,RootRuntimeDefinitionModel.StorageLease.class);
            for(var root:lease.roots())StrictJson.require(!target.startsWith(Path.of(root.path())),"publication must be outside every actual case's signed census roots");
            var request=RootFrozenRunProfile.decode(RootRuntimeDefinitions.read(new ControlBuild.FileRef(one.runRequest().path(),one.runRequest().bytes(),one.runRequest().sha256()),65536));
            StrictJson.require(request.sessionId().equals(capture.session)&&request.machineId().equals(cold.machineId()),"actual classification crossed the exact configured session/machine");
            expected.add(capture.expected);refs.add(capture.classification);
            if(capture.expected.expectedReason()==null)positive++;else reasons.add(capture.expected.expectedReason());
        }
        StrictJson.require(positive>0&&reasons.equals(EnumSet.allOf(AdoptionRefusalReason.class)),"all four actual refusals and a guard-positive original are mandatory");
        AdoptionFixture data=new AdoptionFixture(RootOriginalDriverColdFixture.ADOPTION_SCHEMA,cold.machineId(),expected);
        byte[] encoded=ControlBuild.strictMapper().writeValueAsBytes(data);StrictJson.parse(encoded,RootOriginalDriverColdFixture.MAXIMUM_BYTES);
        RootOriginalDriverColdFixture.absolute(target);actualStorage.requireFilePort(sameGuardedFiles);
        actualStorage.requireManagedRoots(List.of(target.getParent()));actualStorage.requireCompleteAdmission();
        for(Captured capture:actualCaptures)capture.requireOriginals();
        FileWitness published=publicationWriter.locked(same->{
            publicationWriter.requireSession(same);FileWitness actual=sameGuardedFiles.createNew(target,encoded);sameGuardedFiles.verify(actual);
            var readback=RootOriginalDriverColdFixture.readExact(actual.reference(),AdoptionFixture.class);
            StrictJson.require(data.equals(readback),"actual immutable adoption DATA readback differs");return actual;
        });
        return new Produced(published,data,refs);
    }
    private static SharedSourceFiles.Witness retain(ExactRef ref)throws IOException {
        var observed=SharedSourceFiles.observe(Path.of(ref.path()));var actual=observed.source();
        StrictJson.require(actual.bytes()==ref.bytes()&&actual.sha256().equals(ref.sha256())&&Path.of(actual.path()).equals(Path.of(ref.path())),"actual captured original source differs");return observed;
    }
}
