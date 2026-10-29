package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/** File-driven actual-input fixture. The real independent issuer runs before this suite; this
 * reader never creates a Native plan, private profile, billing fact or output authority. */
public final class RootSelectedRegistrationFileInputsProducer
        implements RootSelectedRegistrationInputsProducerTest.ActualInputsProducer {
    public static final String SCHEMA="xar.test-selected-registration-actual-inputs/v1";
    public record Inputs(String schema,String machineId,String ownedOutput,FileRef quoteRequest,FileRef outputBinding) {
        public Inputs {
            if(!SCHEMA.equals(schema)||!WindowsJobProcess.currentMachineId().equals(machineId))
                throw new IllegalArgumentException("actual selected fixture schema/machine required");
            absolute(ownedOutput);bounded(quoteRequest);bounded(outputBinding);
        }
    }
    @Override public RootSelectedRegistrationInputsProducerTest.ActualInputs produce(Path ownedOutput)throws Exception {
        ownedOutput=ownedOutput.toAbsolutePath().normalize();
        FileRef map=propertyRef();var mapWitness=SharedSourceFiles.observe(Path.of(map.path()));
        Inputs inputs=ControlBuild.strictMapper().readValue(read(map),Inputs.class);
        if(!inputs.ownedOutput().equals(ownedOutput.toString()))
            throw new IOException("actual fixture owned output differs from independently quoted directory");
        SharedSourceFiles.plainAncestors(ownedOutput);var directory=SharedSourceFiles.nativeDirectory(ownedOutput);
        var quoteWitness=SharedSourceFiles.observe(Path.of(inputs.quoteRequest().path()));
        var bindingWitness=SharedSourceFiles.observe(Path.of(inputs.outputBinding().path()));
        var request=RootJavaBootstrapInputs.decodeSelectedRegistrationRequest(read(inputs.quoteRequest()));
        if(request.mode()!=RootJavaBootstrapInputs.Mode.QUOTE||request.bindingRef()!=null
                ||!Path.of(request.target()).equals(ownedOutput.resolve("selected-configuration.json")))
            throw new IOException("actual fixture requires source-bound QUOTE for the identical owned target");
        var prepared=RootJavaBootstrapInputs.prepareSelectedRegistration(inputs.quoteRequest(),Clock.systemUTC());
        // Read the independently produced binding through the original Guard, never synthesize one.
        try(var guard=RootBootstrapOutputGuard.readExact(inputs.outputBinding(),Clock.systemUTC())){
            guard.requirePlan(ownedOutput,prepared.quote(),List.of(),List.of());
            guard.requireTargets(List.of(Path.of(request.target())));prepared.requireCurrent(Clock.systemUTC());
        }
        if(!directory.equals(SharedSourceFiles.nativeDirectory(ownedOutput)))throw new IOException("actual fixture directory drift");
        for(var witness:List.of(mapWitness,quoteWitness,bindingWitness))SharedSourceFiles.assertUnchanged(witness);
        return new RootSelectedRegistrationInputsProducerTest.ActualInputs(request,inputs.outputBinding());
    }
    private static FileRef propertyRef(){
        String path=required("path"),bytes=required("bytes"),sha=required("sha256");
        if(!bytes.matches("[1-9][0-9]{0,4}")||!sha.matches("[0-9a-f]{64}"))
            throw new IllegalArgumentException("canonical actual fixture exact3 required");
        var ref=new FileRef(path,Long.parseLong(bytes),sha);bounded(ref);return ref;
    }
    private static String required(String part){
        String value=System.getProperty("xar.test.selectedRegistration.inputs."+part);
        if(value==null||value.isBlank())throw new AssertionError("NOT_RUN_REQUIRED: actual selected input-map exact3 missing "+part);
        return value;
    }
    private static byte[] read(FileRef ref)throws IOException {
        bounded(ref);var witness=SharedSourceFiles.observe(Path.of(ref.path()));
        if(!witness.source().equals(ref))throw new IOException("actual fixture original exact ref mismatch");
        byte[] bytes;try(var input=Files.newInputStream(Path.of(ref.path()))){bytes=input.readNBytes(65537);}
        if(bytes.length!=ref.bytes()||!org.xar.ck3.control.application.driver.DriverJson.sha256(bytes).equals(ref.sha256()))
            throw new IOException("actual fixture original changed");
        StrictJson.parse(bytes,65536);SharedSourceFiles.assertUnchanged(witness);return bytes;
    }
    private static void bounded(FileRef ref){
        Objects.requireNonNull(ref);absolute(ref.path());
        if(ref.bytes()<1||ref.bytes()>65536)throw new IllegalArgumentException("bounded actual fixture original required");
    }
    private static void absolute(String raw){
        Path value=Path.of(Objects.requireNonNull(raw));
        if(!value.isAbsolute()||!value.normalize().equals(value))throw new IllegalArgumentException("canonical actual fixture path required");
    }
}
