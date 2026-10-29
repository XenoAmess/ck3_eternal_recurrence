package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;
import static org.xar.ck3.control.build.RawWindowPreparation.*;

/** Shared producer/codec/file-output tests. Software directory ports never grant actual native qualification. */
final class RawWindowPreparationTest {
    @TempDir Path temporary;
    private static final String MACHINE="software-machine-0001";
    private static final String REVIEW="2099-01-01T00:00:00Z";
    private static final SharedSourceFiles.DirectoryIdentity SOFTWARE=new SharedSourceFiles.DirectoryIdentity("18446744073709551615","340282366920938463463374607431768211455","132537600000000001");
    private static final SharedSourceFiles.DirectoryIdentity DIFFERENT=new SharedSourceFiles.DirectoryIdentity("18446744073709551615","340282366920938463463374607431768211454","132537600000000001");
    private ControlBuild.FileRef proof(){return new ControlBuild.FileRef(temporary.resolve("retained-source17-not-opened.json").toString(),6746,RawWindowLocatorContract.FULL_HASH_ORIGINAL_SHA256);}
    private WindowPlan window(){return new WindowPlan(WINDOW_PLAN_SCHEMA,MACHINE,Consumer.M5,"m5-metadata",temporary.resolve("NOT_OPENED-ck3.exe").toString(),proof(),temporary.toString(),List.of(new Window("rf-records",Kind.METADATA,97853184,8184)),new Amounts(0,8184,0),8192,18432,32768,REVIEW);}
    private LocatorPlan locator(){return new LocatorPlan(LOCATOR_PLAN_SCHEMA,MACHINE,Consumer.M1,"m1-exact",temporary.resolve("NOT_OPENED-ck3.exe").toString(),proof(),temporary.toString(),RawWindowLocatorContract.Locator.M1_MANAGER_QUEUE_TEXT,new RawWindowLocatorContract.Segment(1024,4096,71141888,71141448),new RawWindowLocatorContract.Targets(0x5cc1240L,0x5cc1610L),1048576,256,16384,475136,196608,REVIEW);}
    private static DirectoryPort stable(AtomicInteger calls){return new DirectoryPort(){public String machineId(){return MACHINE;}public SharedSourceFiles.DirectoryIdentity directory(Path ignored){calls.incrementAndGet();return SOFTWARE;}};}
    private static byte[] fixture(Object value)throws IOException{return ControlBuild.strictMapper().writeValueAsBytes(value);}
    private static ObjectNode object(Object value)throws IOException{return (ObjectNode)ControlBuild.strictMapper().readTree(fixture(value));}
    @Test void persistentCiAlsoRunsTheLimitedQualificationProducerRegressions()throws Exception {RawWindowPrepareRegressionMain.run(temporary.resolve("shared-regressions"));}
    @Test void actualWindowProducerUsesExistingStrictCodecAndCreateNewWithoutOpeningExeOrProof()throws Exception {
        AtomicInteger calls=new AtomicInteger();Plan plan=decodePlan(Mode.WINDOWS,fixture(window()));Path output=temporary.resolve("new-request.json");
        Prepared prepared=prepare(plan,output,stable(calls));assertEquals(3,calls.get());
        assertEquals(plan.request(SOFTWARE),prepared.request());assertEquals(prepared.request(),RawWindowCaptureJson.decodeRequest(Files.readAllBytes(output)));
        assertEquals(prepared.encodedRequest(),RawWindowCaptureJson.readOriginal(output,65536).reference());
        assertArrayEquals(encode(prepared.request()),Files.readAllBytes(output));
        assertTrue(new String(Files.readAllBytes(output),java.nio.charset.StandardCharsets.UTF_8).contains("\"file_id_decimal\":\"340282366920938463463374607431768211455\""));
        assertFalse(Files.exists(temporary.resolve("NOT_OPENED-ck3.exe")));assertFalse(Files.exists(Path.of(proof().path())));
    }
    @Test void locatorProducerRoundtripsTheClosedBranchWithoutChargingItAsWholeRfCode()throws Exception {
        Plan plan=decodePlan(Mode.LOCATOR,fixture(locator()));Prepared prepared=prepare(plan,temporary.resolve("locator.json"),stable(new AtomicInteger()));
        var actual=assertInstanceOf(RawWindowLocatorContract.Request.class,prepared.request());
        assertEquals(CaptureScope.M1_EXACT_TEXT_RIPREL_LOCATOR,actual.scope());assertEquals(71141888,actual.segment().bytes());
        assertEquals(actual,RawWindowCaptureJson.decodeRequest(Files.readAllBytes(Path.of(prepared.encodedRequest().path()))));
        assertFalse(Files.exists(temporary.resolve("NOT_OPENED-ck3.exe")));
    }
    @Test void strictConfigurationRejectsUnknownMissingBooleanFloatAliasAndIdentityInput()throws Exception {
        for(String wrong:List.of("extra_alias","output_root_identity")) {
            ObjectNode value=object(window());value.put(wrong,false);assertThrows(IOException.class,()->decodePlan(Mode.WINDOWS,fixture(value)));
        }
        for(String missing:List.of("machine_id","windows","journal_maximum_bytes")) {
            ObjectNode value=object(window());value.remove(missing);assertThrows(IOException.class,()->decodePlan(Mode.WINDOWS,fixture(value)));
        }
        ObjectNode bool=object(window());bool.put("file_identity_api_buffer_cap",true);assertThrows(IOException.class,()->decodePlan(Mode.WINDOWS,fixture(bool)));
        ObjectNode floating=object(window());floating.put("file_identity_api_buffer_cap",8192.0);assertThrows(IOException.class,()->decodePlan(Mode.WINDOWS,fixture(floating)));
        assertThrows(IOException.class,()->decodePlan(Mode.LOCATOR,fixture(window())));
    }
    @Test void currentContractsRejectInsufficientCategoryBudgetAndInvalidClosedLocator()throws Exception {
        WindowPlan base=window();WindowPlan bad=new WindowPlan(base.schema(),base.machineId(),base.consumer(),base.runId(),base.inputPath(),base.fullHashEvidenceRef(),base.outputRoot(),base.windows(),new Amounts(0,8183,0),base.fileIdentityApiBufferCap(),base.journalMaximumBytes(),base.bodyMaximumBytes(),base.reviewAtUtc());
        Path output=temporary.resolve("bad-budget.json");assertThrows(IllegalArgumentException.class,()->prepare(bad,output,stable(new AtomicInteger())));assertFalse(Files.exists(output));
        assertThrows(IllegalArgumentException.class,()->new RawWindowLocatorContract.Targets(0x5cc1241L,0x5cc1610L));
        ObjectNode value=object(locator());value.put("chunk_bytes",8192);Plan invalid=decodePlan(Mode.LOCATOR,fixture(value));
        assertThrows(IllegalArgumentException.class,()->prepare(invalid,temporary.resolve("bad-locator.json"),stable(new AtomicInteger())));
    }
    @Test void missingActualIdentityOrMachineMismatchPublishesNothing()throws Exception {
        Path absent=temporary.resolve("absent.json");assertThrows(NullPointerException.class,()->prepare(window(),absent,new DirectoryPort(){public String machineId(){return MACHINE;}public SharedSourceFiles.DirectoryIdentity directory(Path ignored){return null;}}));assertFalse(Files.exists(absent));
        AtomicInteger calls=new AtomicInteger();DirectoryPort wrong=new DirectoryPort(){public String machineId(){return "other-machine-0002";}public SharedSourceFiles.DirectoryIdentity directory(Path ignored){calls.incrementAndGet();return SOFTWARE;}};
        assertThrows(IOException.class,()->prepare(window(),absent,wrong));assertEquals(0,calls.get());assertFalse(Files.exists(absent));
    }
    @Test void identityDriftBeforePublicationRejectsAndPostPublicationDriftLeavesUnadmittedEvidence()throws Exception {
        for(int driftAt:List.of(2,3)) {
            AtomicInteger calls=new AtomicInteger();Path output=temporary.resolve("drift-"+driftAt+".json");
            DirectoryPort drift=new DirectoryPort(){public String machineId(){return MACHINE;}public SharedSourceFiles.DirectoryIdentity directory(Path ignored){return calls.incrementAndGet()>=driftAt?DIFFERENT:SOFTWARE;}};
            assertThrows(IOException.class,()->prepare(window(),output,drift));assertEquals(driftAt==3,Files.exists(output));
            if(Files.exists(output))assertEquals(SOFTWARE,RawWindowCaptureJson.decodeRequest(Files.readAllBytes(output)).outputRootIdentity());
        }
    }
    @Test void existingOutputAndInvalidParentAreNeverOverwrittenOrTreatedAsPrepared()throws Exception {
        Path output=temporary.resolve("old.json");byte[] original={1,2,3};Files.write(output,original);AtomicInteger calls=new AtomicInteger();
        assertThrows(IOException.class,()->prepare(window(),output,stable(calls)));assertArrayEquals(original,Files.readAllBytes(output));assertEquals(0,calls.get());
        assertThrows(IOException.class,()->prepare(window(),output.resolve("child.json"),stable(calls)));
    }
    @Test void admissionUsesTheExistingIssuerContractAndNeverBecomesAnAutomaticAuthorization()throws Exception {
        var admission=new Admission(ADMISSION_SCHEMA,MACHINE,Consumer.M5,"/root/budget_fast_lane",CaptureScope.BOUNDED_READ_ONLY_FILE_WINDOWS,proof(),proof(),REVIEW);
        assertEquals(admission,RawWindowCaptureJson.decode(RawWindowCaptureJson.encode(admission),Admission.class,65536));
        assertThrows(IllegalArgumentException.class,()->new Admission(ADMISSION_SCHEMA,MACHINE,Consumer.M5,"another-issuer",CaptureScope.BOUNDED_READ_ONLY_FILE_WINDOWS,proof(),proof(),REVIEW));
        assertThrows(IOException.class,()->decodePlan(Mode.ADMISSION,fixture(admission)));
    }
}
