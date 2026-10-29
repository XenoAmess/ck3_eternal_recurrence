package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.OriginalMcpCapture;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.root.RootJavaBootstrapInputs.Mode;
import org.xar.ck3.control.service.root.RootJavaBootstrapInputs.SelectedRegistrationRequest;
import org.xar.ck3.control.service.root.RootSelectedRegistrationConfiguration.SourceInput;
import org.xar.ck3.control.service.root.RootSelectedRegistrationConfiguration.SourceRole;

/** Shape-only inputs below cannot mint Native/FrozenProfile/Bound. The final regression requires actual
 * qualified inputs and a separately issued real Guard binding; absence fails explicitly, never skips. */
public final class RootSelectedRegistrationInputsProducerTest {
    @TempDir Path root;
    public record ActualInputs(SelectedRegistrationRequest quote,FileRef outputBinding) {
        public ActualInputs {java.util.Objects.requireNonNull(quote);java.util.Objects.requireNonNull(outputBinding);}
    }
    public interface ActualInputsProducer {ActualInputs produce(Path ownedOutput)throws Exception;}
    private SelectedRegistrationRequest data(){
        var sources=new ArrayList<SourceInput>();
        for(var role:SourceRole.values())sources.add(new SourceInput(role,ref(role.name()+".json")));
        return new SelectedRegistrationRequest(RootJavaBootstrapInputs.SELECTED_REGISTRATION_SCHEMA,
                WindowsJobProcess.currentMachineId(),Instant.now().plusSeconds(300).toString(),Mode.QUOTE,null,
                root.resolve("selected-configuration.json").toString(),ref("RootSelectedRegistrationConfiguration.java"),
                sources,ref("native-launch-plan.json"),ref("initial-policy.json"));
    }
    private ExactRef ref(String name){return new ExactRef(root.resolve(name).toString(),2,"1".repeat(64));}
    private static ExactRef exact(FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static FileRef write(Path path,byte[] body)throws IOException{
        var files=new org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles();
        var actual=files.createNew(path,body);files.verify(actual);var r=actual.reference();
        return new FileRef(r.path(),r.bytes(),r.sha256());
    }
    @Test void strictRequestRoundTripHasOnlyPhysicalInputsAndNoHandFilledConstructorOrPriorConfiguration()throws Exception {
        var request=data();byte[] encoded=RootJavaBootstrapInputs.encodeSelectedRegistrationRequest(request);
        assertEquals(request,RootJavaBootstrapInputs.decodeSelectedRegistrationRequest(encoded));
        var object=(ObjectNode)StrictJson.parse(encoded);
        assertEquals(9,object.withArray("source_inputs").size());
        assertFalse(object.has("constructor_keywords"));assertFalse(object.has("configuration"));
        assertFalse(object.has("registration_attributes"));assertTrue(object.get("binding_ref").isNull());
        assertArrayEquals(encoded,RootJavaBootstrapInputs.encodeSelectedRegistrationRequest(
                RootJavaBootstrapInputs.decodeSelectedRegistrationRequest(encoded)));
    }
    @Test void missingExtraWrongTypeAndDuplicateRoleCannotEnterTheNewProducer()throws Exception {
        byte[] encoded=RootJavaBootstrapInputs.encodeSelectedRegistrationRequest(data());
        for(String defect:List.of("missing-policy","missing-binding","extra-config","float-plan-bytes","boolean-plan-bytes","numeric-mode","duplicate-role","null-producer")){
            ObjectNode object=(ObjectNode)StrictJson.parse(encoded);
            switch(defect){
                case "missing-policy"->object.remove("initial_policy");
                case "missing-binding"->object.remove("binding_ref");
                case "extra-config"->object.putObject("configuration");
                case "float-plan-bytes"->((ObjectNode)object.get("native_launch_plan")).put("bytes",2.0);
                case "boolean-plan-bytes"->((ObjectNode)object.get("native_launch_plan")).put("bytes",true);
                case "numeric-mode"->object.put("mode",1);
                case "duplicate-role"->((ObjectNode)object.withArray("source_inputs").get(1)).put("role","ROOT_INTENT");
                case "null-producer"->object.putNull("configuration_producer");
                default->throw new AssertionError(defect);
            }
            assertThrows(IOException.class,()->RootJavaBootstrapInputs.decodeSelectedRegistrationRequest(
                    ControlBuild.strictMapper().writeValueAsBytes(object)),defect);
        }
    }
    @Test void missingActualOriginalsFailBeforeAnyQuoteCaptureOrOutput()throws Exception {
        var request=data();FileRef original=write(root.resolve("request.json"),RootJavaBootstrapInputs.encodeSelectedRegistrationRequest(request));
        assertThrows(Exception.class,()->RootJavaBootstrapInputs.prepareSelectedRegistration(original,Clock.systemUTC()));
        assertFalse(Files.exists(Path.of(request.target())));
    }
    @Test void anExistingTargetIsPreservedBeforeAnySourceOrNativePreparation()throws Exception {
        var request=data();FileRef original=write(root.resolve("request.json"),RootJavaBootstrapInputs.encodeSelectedRegistrationRequest(request));
        FileRef retained=write(Path.of(request.target()),"unknown original outcome".getBytes(StandardCharsets.UTF_8));
        assertThrows(IOException.class,()->RootJavaBootstrapInputs.prepareSelectedRegistration(original,Clock.systemUTC()));
        retained.verify();
    }
    @Test void oldGenericDataQuoteAndCodecRemainReadableWithoutFirstProductionAuthority()throws Exception {
        var request=data();
        var old=new RootSelectedRegistrationConfiguration.Configuration(request.machineId(),Instant.now().minusSeconds(1),
                Instant.parse(request.reviewAtUtc()),RootSelectedRegistrationConfiguration.Intent.FRESH_ROBERT_1066_ALL_ORDINARY,
                request.configurationProducer(),request.sourceInputs(),
                new RootSelectedRegistrationConfiguration.ConstructorKeywords(1,false,false,true,Optional.of(
                        new org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding(
                                org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding.Profile.ORDINARY_FROZEN_OFF,
                                "data-only-no-private-profile","2".repeat(64)))));
        FileRef raw=write(root.resolve("raw-selected-data.json"),RootSelectedRegistrationConfiguration.encode(old));
        var generic=new RootJavaBootstrapInputs.Request(RootJavaBootstrapInputs.SCHEMA,request.machineId(),request.reviewAtUtc(),
                Mode.QUOTE,null,List.of(new RootJavaBootstrapInputs.Item(RootBootstrapOutputContract.Kind.SELECTED_REGISTRATION,raw,request.target())));
        assertEquals(old,RootSelectedRegistrationConfiguration.decode(Files.readAllBytes(Path.of(raw.path()))));
        var dataOnly=RootJavaBootstrapInputs.prepare(generic,Clock.systemUTC());
        assertEquals(List.of(RootBootstrapOutputContract.Kind.SELECTED_REGISTRATION),dataOnly.quote().stream().map(RootBootstrapOutputContract.Output::kind).toList());
        assertEquals(raw.sha256(),dataOnly.files().getFirst().expected().sha256());
        assertFalse(Files.exists(Path.of(request.target())));
    }
    void actualSourceBoundProducerMainQuoteCreateAndOriginalCaptureConsumerUseTheSamePhysicalOriginal()throws Exception {
        ActualInputs actual=new RootSelectedRegistrationFileInputsProducer().produce(root.resolve("actual-inputs"));
        var quote=actual.quote();assertEquals(Mode.QUOTE,quote.mode());assertNull(quote.bindingRef());
        Path output=Path.of(quote.target());assertTrue(output.toAbsolutePath().normalize().startsWith(root.toAbsolutePath().normalize()),
                "regression publication must stay inside its actually owned output root");
        FileRef quotedRequest=write(root.resolve("actual-quote-request.json"),RootJavaBootstrapInputs.encodeSelectedRegistrationRequest(quote));
        var prepared=RootJavaBootstrapInputs.prepareSelectedRegistration(quotedRequest,Clock.systemUTC());prepared.requireCurrent(Clock.systemUTC());
        var emitted=RootBootstrapProtocol.line(run(quotedRequest),RootBootstrapProtocol.Quote.class);
        assertEquals("SELECTED_REGISTRATION",emitted.phase());assertEquals(prepared.quote(),emitted.outputs());
        assertFalse(Files.exists(output));
        var create=new SelectedRegistrationRequest(quote.schema(),quote.machineId(),quote.reviewAtUtc(),Mode.CREATE_NEW,actual.outputBinding(),
                quote.target(),quote.configurationProducer(),quote.sourceInputs(),quote.nativeLaunchPlan(),quote.initialPolicy());
        FileRef createdRequest=write(root.resolve("actual-create-request.json"),RootJavaBootstrapInputs.encodeSelectedRegistrationRequest(create));
        byte[] receipt=run(createdRequest);var report=StrictJson.parse(receipt,RootJavaBootstrapInputs.MAXIMUM_REQUEST_BYTES);
        assertEquals("CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION",report.get("status").textValue());
        ExactRef published=ExactRef.fromJson(report.get("original_ref"));assertEquals(exact(prepared.expected()),published);
        FileRef original=new FileRef(published.path(),published.bytes(),published.sha256());original.verify();
        var witness=SharedSourceFiles.observe(output);assertEquals(original,witness.source());
        byte[] body=Files.readAllBytes(output);var selected=RootSelectedRegistrationConfiguration.decode(body);
        assertEquals(prepared.configuration(),selected);
        var consumer=OriginalMcpCapture.decodeSelectedConfiguration(body,quote.machineId(),
                new FileRef(quote.configurationProducer().path(),quote.configurationProducer().bytes(),quote.configurationProducer().sha256()));
        assertEquals(selected.intent().name(),consumer.intent().name());
        assertEquals(9,consumer.sources().size());assertEquals(79,StrictJson.parse(body).get("registration_attributes").size());
        for(var source:consumer.sources())source.original().verify();
        assertEquals(selected.constructorKeywords().routeContactTimelineSpeed(),consumer.constructorArguments().routeContactTimelineSpeed());
        assertEquals(selected.constructorKeywords().warDailyWatchEnabled(),consumer.constructorArguments().warDailyWatchEnabled());
        SharedSourceFiles.assertUnchanged(witness);
        assertThrows(Exception.class,()->RootJavaBootstrapInputs.prepareSelectedRegistration(createdRequest,Clock.systemUTC()));
        SharedSourceFiles.assertUnchanged(witness);
    }
    private static byte[] run(FileRef request)throws Exception {
        var bytes=new ByteArrayOutputStream();PrintStream previous=System.out;
        try(var capture=new PrintStream(bytes,true,StandardCharsets.UTF_8)){
            try{System.setOut(capture);RootJavaBootstrapInputs.main(new String[]{request.path(),Long.toString(request.bytes()),request.sha256()});}
            finally{System.setOut(previous);}
        }
        return bytes.toByteArray();
    }
}
