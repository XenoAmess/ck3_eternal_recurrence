package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.OriginalMcpCapture;
import org.xar.ck3.control.build.OriginalMcpCapture.Role;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.service.mcp.McpCoverage;

/** Actual source-pinned original registration -> finite existing immutable bootstrap writer.
 * No decision is manufactured for Java admission, and no current Game/readiness/Bound is granted. */
public final class RootOriginalMcpCapture {
    public static final String TARGETS_SCHEMA="xar.original-mcp-capture-five-targets/v1";
    public static final String ACTUAL_SCHEMA="xar.original-mcp-capture-installed/v1";
    private static final ObjectMapper JSON=dataMapper();
    private static ObjectMapper dataMapper(){
        var mapper=ControlBuild.strictMapper().disable(com.fasterxml.jackson.databind.DeserializationFeature.ACCEPT_FLOAT_AS_INT)
            .enable(com.fasterxml.jackson.databind.DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES,
                com.fasterxml.jackson.databind.DeserializationFeature.FAIL_ON_MISSING_CREATOR_PROPERTIES,
                com.fasterxml.jackson.databind.DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
        mapper.setConfig(mapper.getDeserializationConfig().without(com.fasterxml.jackson.databind.MapperFeature.ALLOW_COERCION_OF_SCALARS));
        return mapper;
    }
    private RootOriginalMcpCapture(){ }
    public record Targets(String schema,String catalog,String tools,String resources,String registrationFacts,String inventoryProof){
        public Targets{
            require(TARGETS_SCHEMA.equals(schema),"unknown exact original capture targets");
            List<Path> values=List.of(path(catalog),path(tools),path(resources),path(registrationFacts),path(inventoryProof));
            require(values.stream().distinct().count()==5,"five distinct stable original MCP targets required");
        }
        public Path get(Role role){return path(switch(role){case CATALOG->catalog;case TOOLS->tools;case RESOURCES->resources;case REGISTRATION_FACTS->registrationFacts;case INVENTORY_PROOF->inventoryProof;});}
        public List<Path> paths(){return java.util.Arrays.stream(Role.values()).map(this::get).toList();}
    }
    public record Actual(String schema,String machineId,String observedAtUtc,String status,
            FileRef capturePlanRef,FileRef measuredReceiptRef,FileRef outputBindingRef,FileRef targetsRef,
            OriginalMcpCapture.FiveFiles documents,OriginalMcpCapture.OriginalMcpSourceSet sourceSet,OriginalMcpCapture.ProcessEvidence captureProcess,
            OriginalMcpCapture.Transport actualTransport,String javaAdmission,String gameQualification,String wireRetention){
        public Actual{
            require(ACTUAL_SCHEMA.equals(schema)&&"PASS_ORIGINAL_REGISTRATION_ONLY_NOT_JAVA_OR_GAME".equals(status),"unknown original capture actual scope");
            require(machineId!=null&&!machineId.equals("unknown")&&machineId.matches("[a-z0-9][a-z0-9-]{0,63}")&&observedAtUtc!=null,"explicit original capture machine/time required");
            java.time.Instant.parse(observedAtUtc);
            require("NOT_PRODUCED".equals(javaAdmission)&&"NOT_RUN".equals(gameQualification)&&"FINITE_TEMP_RECLAIMABLE_ONLY_BY_ROOT_ISSUER_EXACT_PLAN".equals(wireRetention),"actual registration capture cannot grant Java/Game admission or silently discard its wire");
            Objects.requireNonNull(documents);Objects.requireNonNull(sourceSet);Objects.requireNonNull(captureProcess);Objects.requireNonNull(actualTransport);
            for(var ref:List.of(capturePlanRef,measuredReceiptRef,outputBindingRef,targetsRef))Objects.requireNonNull(ref);
        }
    }
    /** Immutable decoded receipt DATA; this value grants no process, dispatch or Game permission. */
    public static final class Retained {
        private final FileRef original;private final Actual actual;
        private Retained(FileRef original,Actual actual){this.original=Objects.requireNonNull(original);this.actual=Objects.requireNonNull(actual);}
        public FileRef original(){return original;}public Actual actual(){return actual;}
        public OriginalMcpCapture.OriginalMcpSourceSet sourceSet(){return actual.sourceSet();}
        public void requireUnchanged()throws IOException{
            if(!readActual(original).equals(actual))throw new IOException("actual original capture receipt DATA changed");
        }
        /** Compatibility DATA read only; historical selected-configuration periods grant no permission. */
        public void requireCurrent(Clock clock)throws IOException {Objects.requireNonNull(clock);requireUnchanged();}
        /** Compare the selected metadata without reopening source files, application or signing inputs. */
        public void requireInputs(RootRuntimeDefinitions.Inputs same,Clock clock)throws IOException{
            Objects.requireNonNull(same);Objects.requireNonNull(clock);
            require(sameRef(same.data(RootRuntimeDefinitionModel.DataRole.ORIGINAL_MCP_CAPTURE_RECEIPT),original),"runtime definitions selected a different capture receipt");
            require(same.application().machineId().equals(actual.machineId()),"capture metadata differs from configured runtime machine");
            require(sameRef(same.data(RootRuntimeDefinitionModel.DataRole.MCP_CATALOG),actual.documents().catalog().original())
                &&sameRef(same.data(RootRuntimeDefinitionModel.DataRole.MCP_TOOLS),actual.documents().tools().original())
                &&sameRef(same.data(RootRuntimeDefinitionModel.DataRole.MCP_RESOURCES),actual.documents().resources().original()),"runtime definitions selected different captured public originals");
        }
    }
    public static Retained readRetained(FileRef original)throws IOException {return new Retained(original,readActual(original));}

    /** Capture configuration data is decoded by its single Java owner; this does not invoke readExact or construct Bound. */
    public static FileRef measure(FileRef actualPlanRef)throws IOException,InterruptedException{
        var original=observe(actualPlanRef);var plan=readPlan(actualPlanRef);decodeConfiguration(plan);
        var measured=OriginalMcpCapture.measure(plan);
        // Exactly one random session receipt, containing the complete actual Job/source/config/measurement product.
        var receipt=OriginalMcpCapture.writeSessionReceipt(plan,measured.evidence(),OriginalMcpCapture.encodeMeasured(measured));
        SharedSourceFiles.assertUnchanged(original);return receipt.source();
    }
    public static FileRef capture(FileRef actualPlanRef,FileRef measuredReceiptRef,FileRef actualOutputBindingRef,FileRef actualTargetsRef,Clock clock)throws IOException,InterruptedException{
        Objects.requireNonNull(clock);var originals=new ArrayList<SharedSourceFiles.Witness>();
        for(var ref:List.of(actualPlanRef,measuredReceiptRef,actualOutputBindingRef,actualTargetsRef))originals.add(observe(ref));
        var plan=readPlan(actualPlanRef);decodeConfiguration(plan);var measured=OriginalMcpCapture.readMeasured(measuredReceiptRef);
        Targets targets=decodeTargets(read(actualTargetsRef,65536));
        // The existing sealed guard reads the actual declaration/census/capacity/binding and exact priced extents.
        // Config12 construction is never substituted for this actual finite write admission.
        try(var authority=RootBootstrapOutputGuard.readExact(actualOutputBindingRef,clock)){
            authority.requireTargets(targets.paths());
            for(var target:targets.paths())require(authority.files().observe(target).isEmpty(),"existing/unknown stable MCP target cannot be overwritten or recaptured");
            var captured=OriginalMcpCapture.capture(measured,plan);
            // Actual shared Java consumers, no synthetic admission document.
            var catalog=McpCoverage.readCatalog(new RawJson(captured.documents().get(Role.CATALOG)));
            var tools=RootPublicCatalogCodec.decodeTools(new RawJson(captured.documents().get(Role.TOOLS)));
            require(catalog.declarations().size()==measured.summary().counts().declarations()
                &&tools.size()==measured.summary().counts().registeredTools(),"actual shared catalog/descriptor consumer counts differ");
            var created=new java.util.EnumMap<Role,OriginalMcpCapture.DataFile>(Role.class);
            for(Role role:Role.values()){
                byte[] bytes=captured.documents().get(role);var expected=measured.summary().documents().get(role);
                require(bytes.length==expected.bytes()&&OriginalMcpCapture.sha256(bytes).equals(expected.sha256()),"actual original body differs from issuer-priced measurement");
                FileWitness witness=authority.files().createNew(targets.get(role),bytes);
                authority.files().verify(witness);byte[] actual=authority.files().read(witness,OriginalMcpCapture.DOCUMENT_MAX);
                require(java.util.Arrays.equals(bytes,actual),"actual stable original MCP data readback differs");
                var nativeWitness=SharedSourceFiles.observe(targets.get(role));
                created.put(role,new OriginalMcpCapture.DataFile(role,nativeWitness.source(),nativeWitness.nativeFile()));
            }
            var data=new OriginalMcpCapture.FiveFiles(created.get(Role.CATALOG),created.get(Role.TOOLS),created.get(Role.RESOURCES),created.get(Role.REGISTRATION_FACTS),created.get(Role.INVENTORY_PROOF));
            OriginalMcpCapture.verify(data);authority.requireTargets(targets.paths());
            var actual=new Actual(ACTUAL_SCHEMA,plan.machineId(),clock.instant().toString(),"PASS_ORIGINAL_REGISTRATION_ONLY_NOT_JAVA_OR_GAME",
                actualPlanRef,measuredReceiptRef,actualOutputBindingRef,actualTargetsRef,data,OriginalMcpCapture.sourceSet(captured),captured.evidence(),captured.transport(),
                "NOT_PRODUCED","NOT_RUN","FINITE_TEMP_RECLAIMABLE_ONLY_BY_ROOT_ISSUER_EXACT_PLAN");
            for(var original:originals)SharedSourceFiles.assertUnchanged(original);
            byte[] receipt=JSON.writeValueAsBytes(actual);
            var saved=OriginalMcpCapture.writeSessionReceipt(plan,captured.evidence(),receipt);
            // Serde/physical consumer check is mandatory after publication; unknown write is not retried.
            Actual reopened=readActual(saved.source());require(reopened.equals(actual),"actual installed capture receipt roundtrip differs");
            return saved.source();
        }
    }
    /** Decode this receipt only; explicit capture and measurement own their actual execution separately. */
    public static Actual readActual(FileRef exactReceipt)throws IOException{return decodeActual(read(exactReceipt,OriginalMcpCapture.CONTROL_MAX));}

    public static byte[] encodeTargets(Targets value)throws IOException{return JSON.writeValueAsBytes(value);}
    public static Targets decodeTargets(byte[] bytes)throws IOException{return JSON.readValue(bytes,Targets.class);}
    public static byte[] encodeActual(Actual value)throws IOException{return JSON.writeValueAsBytes(Objects.requireNonNull(value));}
    /** Sole receipt DATA codec; decoding grants no capture, dispatch or Game qualification. */
    public static Actual decodeActual(byte[] bytes)throws IOException{require(bytes!=null&&bytes.length>0&&bytes.length<=OriginalMcpCapture.CONTROL_MAX,"bounded original capture actual receipt required");return JSON.readValue(bytes,Actual.class);}
    private static OriginalMcpCapture.Plan readPlan(FileRef ref)throws IOException{return OriginalMcpCapture.decodePlan(read(ref,OriginalMcpCapture.CONTROL_MAX));}
    private static void decodeConfiguration(OriginalMcpCapture.Plan plan)throws IOException{
        var selected=RootSelectedRegistrationConfiguration.decode(read(plan.selectedConfigurationRef(),65536));
        require(selected.machineId().equals(plan.machineId()),"actual selected registration configuration is for another machine");
        // The actual frozen profile/NativeLaunchPlan semantic rederivation is solely readExact's responsibility.
        // This pre-Core capture requires Configuration original data, and does not claim it is Bound.
    }
    private static SharedSourceFiles.Witness observe(FileRef ref)throws IOException{
        Objects.requireNonNull(ref);ref.verify();var actual=SharedSourceFiles.observe(Path.of(ref.path()));
        require(actual.source().bytes()==ref.bytes()&&actual.source().sha256().equals(ref.sha256()),"actual capture input witness differs");return actual;
    }
    private static byte[] read(FileRef ref,int maximum)throws IOException{
        Objects.requireNonNull(ref);Path selected=path(ref.path());
        if(ref.bytes()<1||ref.bytes()>maximum)throw new IOException("bounded actual capture DATA input required");
        byte[] bytes;try(var input=Files.newInputStream(selected)){bytes=input.readNBytes(Math.addExact(maximum,1));}
        if(bytes.length!=ref.bytes()||bytes.length>maximum||!OriginalMcpCapture.sha256(bytes).equalsIgnoreCase(ref.sha256()))
            throw new IOException("actual capture DATA bytes/SHA differ: "+ref.path());
        return bytes;
    }

    private static Path path(String value){require(value!=null&&Path.of(value).isAbsolute()&&Path.of(value).normalize().equals(Path.of(value)),"exact absolute captured DATA path required");return Path.of(value);}
    private static boolean sameRef(FileRef a,FileRef b){return Path.of(a.path()).toAbsolutePath().normalize().equals(Path.of(b.path()).toAbsolutePath().normalize())&&a.bytes()==b.bytes()&&a.sha256().equals(b.sha256());}
    private static void require(boolean value,String why){if(!value)throw new IllegalArgumentException(why);}
    private static FileRef cli(String p,String n,String sha){long bytes=Long.parseLong(n);require(Long.toString(bytes).equals(n),"canonical exact reference byte count required");return new FileRef(path(p).toString(),bytes,sha);}
    /** Root runs this real entry under the shared qualified command producer; stdout is only a small exact receipt ref. */
    public static void main(String[] args)throws Exception{
        FileRef result;
        if(args.length==4&&args[0].equals("measure"))result=measure(cli(args[1],args[2],args[3]));
        else if(args.length==13&&args[0].equals("capture"))result=capture(cli(args[1],args[2],args[3]),cli(args[4],args[5],args[6]),
            cli(args[7],args[8],args[9]),cli(args[10],args[11],args[12]),Clock.systemUTC());
        else throw new IllegalArgumentException("measure PLAN_PATH BYTES SHA | capture PLAN_REF MEASURED_REF ACTUAL_OUTPUT_BINDING_REF FIVE_TARGETS_REF (each ref: PATH BYTES SHA)");
        System.out.println(JSON.writeValueAsString(result));
    }
}

