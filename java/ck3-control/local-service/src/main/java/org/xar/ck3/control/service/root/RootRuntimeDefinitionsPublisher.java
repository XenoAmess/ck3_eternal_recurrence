package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** First physical runtime-definitions original, using the existing finite immutable DATA publisher.
 * No preexisting definitions file, continuity writer, configured callback, Core or Game authority is needed or minted. */
public final class RootRuntimeDefinitionsPublisher {
    public static final String SCHEMA="xar.java-root-runtime-definitions-publication/v1";
    public static final int MAXIMUM_REQUEST_BYTES=StrictJson.EXPLICIT_MAX_BYTES;
    private static final Set<String> FIELDS=Set.of("schema","configuration","output_binding_ref","target");

    private RootRuntimeDefinitionsPublisher(){ }

    public static final String SOURCE_DECLARATION_SCHEMA="xar.root-runtime-definitions-source-declaration/v1";
    private static final Set<String> SOURCE_DECLARATION_FIELDS=Set.of(
            "schema","machine_id","observed_at_utc","review_at_utc","physical","domains");

    /** Independent original inputs only; neither Configuration nor a prior Definitions template is accepted. */
    public record SourceDeclaration(String schema,String machineId,String observedAtUtc,String reviewAtUtc,
            RootRuntimeDefinitionConfigurationAssembler.PhysicalOriginals physical,
            RootRuntimeDefinitionConfigurationAssembler.DeclaredDomainInputs domains) {
        public SourceDeclaration {
            require(SOURCE_DECLARATION_SCHEMA.equals(schema),"exact definitions source-declaration version required");
            require(machineId!=null&&machineId.matches("[a-z0-9][a-z0-9-]{0,127}")&&!machineId.equals("unknown"),
                    "known definitions source-declaration machine required");
            var observed=instant(observedAtUtc);var review=instant(reviewAtUtc);
            require(observed.isBefore(review)&&java.time.Duration.between(observed,review).compareTo(java.time.Duration.ofDays(7))<=0,
                    "finite explicit source-declaration review required");
            Objects.requireNonNull(physical);Objects.requireNonNull(domains);
        }
    }

    public static byte[] encodeSourceDeclaration(SourceDeclaration value)throws IOException {
        Objects.requireNonNull(value);
        byte[] encoded=StrictJson.canonical(ControlBuild.strictMapper().valueToTree(value),MAXIMUM_REQUEST_BYTES);
        require(value.equals(decodeSourceDeclaration(encoded)),"source-declaration sole-codec roundtrip changed");
        return encoded;
    }
    public static SourceDeclaration decodeSourceDeclaration(byte[] raw)throws IOException {
        try {
            var object=StrictJson.object(StrictJson.parse(raw,MAXIMUM_REQUEST_BYTES),SOURCE_DECLARATION_FIELDS);
            return ControlBuild.strictMapper().treeToValue(object,SourceDeclaration.class);
        }catch(IllegalArgumentException|NullPointerException invalid) {
            throw new IOException("invalid strict definitions source declaration",invalid);
        }
    }

    /** Pure DATA rebinding only; no referenced originals are reopened for this composition. */
    public static SourceDeclaration withPublicAdmissionSource(SourceDeclaration original,FileRef actualAdmission) {
        Objects.requireNonNull(original);RootRuntimeDefinitionModel.file(actualAdmission,maximumDataBytes(DataRole.MCP_ADMISSION));
        var data=new ArrayList<DataPin>();int replacements=0;
        for(var pin:original.physical().originalData()) {
            if(pin.role()==DataRole.MCP_ADMISSION){data.add(new DataPin(pin.role(),actualAdmission));replacements++;}
            else data.add(pin);
        }
        require(replacements==1,"one existing public admission DATA role required for the explicit successor");
        var physical=original.physical();
        var selected=new RootRuntimeDefinitionConfigurationAssembler.PhysicalOriginals(physical.applicationRef(),physical.storageLeaseRef(),
                physical.nativeLaunchPlanRef(),physical.runtimePackageRequestRef(),physical.sourceIndex(),physical.sources(),physical.closures(),data);
        return new SourceDeclaration(original.schema(),original.machineId(),original.observedAtUtc(),original.reviewAtUtc(),selected,original.domains());
    }

    /** First declaration starts from explicit typed request data, never from a Definitions/Configuration template. */
    public static SourcePrepared prepareSourceDeclaration(FileRef explicitSourceRequest,Clock clock)throws IOException {
        return prepareSourceDeclaration(explicitSourceRequest,java.util.Optional.empty(),clock);
    }
    /** Only the separately produced admission original changes; captured public files and all other DATA remain selected. */
    public static SourcePrepared prepareSourceDeclarationWithAdmission(FileRef actualDeclaration,FileRef actualAdmission,Clock clock)throws IOException {
        return prepareSourceDeclaration(actualDeclaration,java.util.Optional.of(Objects.requireNonNull(actualAdmission)),clock);
    }
    private static SourcePrepared prepareSourceDeclaration(FileRef source,java.util.Optional<FileRef> replacement,Clock clock)throws IOException {
        Objects.requireNonNull(clock);Objects.requireNonNull(replacement);
        var declaration=decodeSourceDeclaration(readData(source,MAXIMUM_REQUEST_BYTES));
        if(replacement.isPresent())declaration=withPublicAdmissionSource(declaration,replacement.orElseThrow());
        // Validate the shared typed configuration without reopening its historical references.
        configuration(declaration);
        return new SourcePrepared(declaration,encodeSourceDeclaration(declaration));
    }
    /** Immutable source declaration DATA; this object supplies no runtime or output authority. */
    public static final class SourcePrepared {
        private final SourceDeclaration declaration;
        private final byte[] bytes;
        private SourcePrepared(SourceDeclaration declaration,byte[] bytes){this.declaration=declaration;this.bytes=bytes.clone();}
        public SourceDeclaration declaration(){return declaration;}
        public byte[] bytes(){return bytes.clone();}
        public RootBootstrapOutputContract.Output quote(Path target) {
            fileTarget(target);
            return new RootBootstrapOutputContract.Output(RootBootstrapOutputContract.Kind.RUNTIME_DEFINITIONS_SOURCE_DECLARATION,
                    target.getFileName().toString(),bytes.length,sha(bytes));
        }
        public void requireCurrent(Clock clock)throws IOException {Objects.requireNonNull(clock);}
        /** Create one explicit DATA file; an unknown or existing output is never retried. */
        public SharedSourceFiles.Witness publish(Path target,Clock clock)throws IOException {
            requireCurrent(clock);fileTarget(target);
            Files.write(target,bytes,java.nio.file.StandardOpenOption.CREATE_NEW);
            var ref=new FileRef(target.toString(),bytes.length,sha(bytes));byte[] actual=readData(ref,MAXIMUM_REQUEST_BYTES);
            require(Arrays.equals(bytes,actual)&&declaration.equals(decodeSourceDeclaration(actual)),"physical source declaration or sole-codec roundtrip differs");
            return outputWitness(ref);
        }
        /** Compatibility metadata is retained by callers; publication no longer requires an issuer. */
        public SharedSourceFiles.Witness publish(FileRef outputBinding,Path target,Clock clock)throws IOException {
            return publish(target,clock);
        }
    }
    private static Configuration configuration(SourceDeclaration declaration) {
        return RootRuntimeDefinitionConfigurationAssembler.configuration(declaration.physical(),declaration.domains(),declaration.machineId(),
                instant(declaration.observedAtUtc()),instant(declaration.reviewAtUtc()));
    }
    private record Declared(Configuration configuration) { }
    private static Declared declared(FileRef original,Clock clock)throws IOException {
        Objects.requireNonNull(clock);
        return new Declared(configuration(decodeSourceDeclaration(readData(original,MAXIMUM_REQUEST_BYTES))));
    }
    private record Requested(RootRuntimeDefinitionsPublicationRequestProducer.Prepared prepared) { }
    private static Requested request(Declared actual,FileRef definitionsBinding,Path definitionsTarget)throws IOException {
        normalized(definitionsTarget);
        return new Requested(RootRuntimeDefinitionsPublicationRequestProducer.prepare(
                new Request(SCHEMA,actual.configuration(),definitionsBinding,definitionsTarget.toString())));
    }

    private static FileRef cliRef(String[] args,int offset,int maximum) {
        long count=Long.parseLong(args[offset+1]);
        require(count>0&&count<=maximum&&Long.toString(count).equals(args[offset+1]),"canonical bounded positive exact length required");
        var ref=new FileRef(args[offset],count,args[offset+2]);
        RootRuntimeDefinitionModel.file(ref,maximum);return ref;
    }
    private static void flags(String[] args) {
        require("--definitions-binding".equals(args[4])&&"--definitions-target".equals(args[8])
                &&"--request-target".equals(args[10]),"exact ordered publication-request options required");
        if(args.length==16)require("--request-binding".equals(args[12]),"actual separate request binding required");
    }

    /** Configuration is the existing unique SDK model. No parallel field roster or default-valued template. */
    public record Request(String schema,Configuration configuration,FileRef outputBindingRef,String target) {
        public Request {
            require(SCHEMA.equals(schema),"exact definitions publication request schema required");
            Objects.requireNonNull(configuration);RootRuntimeDefinitionModel.file(outputBindingRef,RootBootstrapOutputContract.MAXIMUM_BYTES);
            absolute(target);
        }
    }

    /** Pure encoded Configuration DATA. A quote is metadata and grants no runtime qualification. */
    public static final class Prepared {
        private final Configuration configuration;
        private final byte[] bytes;
        private Prepared(Configuration configuration,byte[] bytes){this.configuration=configuration;this.bytes=bytes.clone();}
        public Configuration configuration(){return configuration;}
        public byte[] bytes(){return bytes.clone();}
        public RootBootstrapOutputContract.Output quote(Path target) {
            fileTarget(target);
            return new RootBootstrapOutputContract.Output(RootBootstrapOutputContract.Kind.RUNTIME_DEFINITIONS,
                    target.getFileName().toString(),bytes.length,sha(bytes));
        }
        public void requireCurrent(Clock clock)throws IOException {Objects.requireNonNull(clock);}
        public Published publish(Path target,Clock clock)throws IOException {
            requireCurrent(clock);fileTarget(target);
            Files.write(target,bytes,java.nio.file.StandardOpenOption.CREATE_NEW);
            var ref=new FileRef(target.toString(),bytes.length,sha(bytes));byte[] actual=readData(ref,RootRuntimeDefinitions.MAXIMUM_BYTES);
            require(Arrays.equals(bytes,actual)&&configuration.equals(RootRuntimeDefinitions.decodeConfiguration(actual)),
                    "physical definitions bytes or sole-codec roundtrip changed");
            return new Published(this,outputWitness(ref));
        }
        /** The old card parameter is passive compatibility DATA. */
        public Published publish(FileRef actualOutputBinding,Path target,Clock clock)throws IOException {return publish(target,clock);}
    }
    /** Successful CREATE_NEW/readback report; this value is not a Ready proof. */
    public static final class Published {
        private final Prepared prepared;private final SharedSourceFiles.Witness original;
        private Published(Prepared prepared,SharedSourceFiles.Witness original){this.prepared=prepared;this.original=original;}
        public FileRef original(){return original.source();}
        public SharedSourceFiles.Witness actualWitness(){return original;}
        public Configuration readConfiguration(Clock clock)throws IOException {
            Objects.requireNonNull(clock);
            Configuration actual=RootRuntimeDefinitions.decodeConfiguration(readData(original(),RootRuntimeDefinitions.MAXIMUM_BYTES));
            require(prepared.configuration.equals(actual),"published configuration changed");return actual;
        }
        public void requireCurrent(Clock clock)throws IOException {readConfiguration(clock);}
        /** Runtime input assembly and its eager Startup are a separate remaining consumer cut. */
        public RootRuntimeDefinitions readExact(Clock clock)throws IOException {
            Configuration expected=readConfiguration(clock);
            var loaded=RootRuntimeDefinitions.readExact(original(),clock);
            require(loaded.inputs().configuration().equals(expected),"actual definitions consumer selected another configuration");return loaded;
        }
    }
    public static Prepared prepare(Configuration configuration,Clock clock)throws IOException {
        Objects.requireNonNull(configuration);Objects.requireNonNull(clock);
        byte[] bytes=RootRuntimeDefinitions.encodeConfiguration(configuration);
        require(configuration.equals(RootRuntimeDefinitions.decodeConfiguration(bytes)),"sole configuration codec roundtrip changed");
        return new Prepared(configuration,bytes);
    }
    /** Compatibility parameters no longer qualify immutable DATA publication. */
    public static Prepared prepare(Configuration configuration,NativeLaunchPlan sameActualPlan,
            RootOriginalMcpCapture.Retained sameCapturedOriginals,Clock clock)throws IOException {return prepare(configuration,clock);}

    public static byte[] encodeRequest(Request request)throws IOException {
        Objects.requireNonNull(request);ObjectNode root=StrictJson.object();root.put("schema",request.schema());
        root.set("configuration",StrictJson.parse(RootRuntimeDefinitions.encodeConfiguration(request.configuration()),RootRuntimeDefinitions.MAXIMUM_BYTES));
        root.set("output_binding_ref",ControlBuild.strictMapper().valueToTree(request.outputBindingRef()));root.put("target",request.target());
        return StrictJson.canonical(root,MAXIMUM_REQUEST_BYTES);
    }
    public static Request decodeRequest(byte[] bytes)throws IOException {
        try {
            var root=StrictJson.object(StrictJson.parse(bytes,MAXIMUM_REQUEST_BYTES),FIELDS);
            return new Request(StrictJson.text(root.get("schema")),RootRuntimeDefinitions.decodeConfiguration(
                    StrictJson.canonical(root.get("configuration"),RootRuntimeDefinitions.MAXIMUM_BYTES)),
                    ControlBuild.strictMapper().treeToValue(root.get("output_binding_ref"),FileRef.class),StrictJson.text(root.get("target")));
        }catch(IllegalArgumentException|NullPointerException invalid){throw new IOException("invalid exact runtime definitions publication request",invalid);}
    }
    public static Published execute(FileRef actualRequest,Clock clock)throws IOException {
        Objects.requireNonNull(clock);Request request=decodeRequest(readData(actualRequest,MAXIMUM_REQUEST_BYTES));
        return prepare(request.configuration(),clock).publish(Path.of(request.target()),clock);
    }

    /** Explicit source-declaration and publication-request preparation precedes the original Definitions execution.
     * Quotes preserve the existing metadata protocol. Preparation publication emits its actual witness and never executes Definitions. */
    public static void main(String[] args)throws Exception {
        Objects.requireNonNull(args);Clock clock=Clock.systemUTC();
        if(args.length>0&&Set.of("quote-source-declaration","publish-source-declaration",
                "quote-admission-source-declaration","publish-admission-source-declaration").contains(args[0])) {
            boolean replacement=args[0].contains("admission");boolean publish=args[0].startsWith("publish");
            int expected=6+(replacement?4:0)+(publish?4:0);
            require(args.length==expected,"exact source request, optional admission, output binding and target arguments required");
            var source=cliRef(args,1,MAXIMUM_REQUEST_BYTES);int offset=4;FileRef admission=null;
            if(replacement){require("--admission".equals(args[offset]),"exact admission source option required");
                admission=cliRef(args,offset+1,maximumDataBytes(DataRole.MCP_ADMISSION));offset+=4;}
            FileRef binding=null;
            if(publish){require("--output-binding".equals(args[offset]),"actual source-declaration output binding required");
                binding=cliRef(args,offset+1,RootBootstrapOutputContract.MAXIMUM_BYTES);offset+=4;}
            require("--target".equals(args[offset]),"exact source-declaration target option required");Path target=Path.of(args[offset+1]);normalized(target);
            require(target.getParent()!=null&&target.getFileName()!=null,"explicit source-declaration file target required");
            SourcePrepared prepared=replacement?prepareSourceDeclarationWithAdmission(source,Objects.requireNonNull(admission),clock):prepareSourceDeclaration(source,clock);
            if(publish) {
                var result=prepared.publish(Objects.requireNonNull(binding),target,clock);
                prepared.requireCurrent(clock);System.out.println(ControlBuild.strictMapper().writeValueAsString(result));
            } else {
                var output=prepared.quote(target);prepared.requireCurrent(clock);
                emitQuote(prepared.declaration().machineId(),prepared.declaration().reviewAtUtc(),target,output);
            }
            return;
        }
        if(args.length==6&&"quote-definitions".equals(args[0])) {
            require("--target".equals(args[4]),"exact definitions target option required");
            Path target=Path.of(args[5]);normalized(target);
            var actual=declared(cliRef(args,1,MAXIMUM_REQUEST_BYTES),clock);
            var prepared=prepare(actual.configuration(),clock);
            var output=prepared.quote(target);prepared.requireCurrent(clock);
            emitQuote(actual.configuration().machineId(),actual.configuration().reviewAtUtc(),target,output);return;
        }
        if((args.length==12&&"quote-request".equals(args[0]))||(args.length==16&&"publish-request".equals(args[0]))) {
            flags(args);
            var declarationRef=cliRef(args,1,MAXIMUM_REQUEST_BYTES);
            var definitionsBinding=cliRef(args,5,RootBootstrapOutputContract.MAXIMUM_BYTES);
            Path definitionsTarget=Path.of(args[9]),requestTarget=Path.of(args[11]);
            normalized(definitionsTarget);normalized(requestTarget);
            FileRef requestBinding=args.length==16?cliRef(args,13,RootBootstrapOutputContract.MAXIMUM_BYTES):null;
            var actual=declared(declarationRef,clock);
            var requested=request(actual,definitionsBinding,definitionsTarget);var prepared=requested.prepared();
            if(requestBinding==null) {
                var output=prepared.quote(requestTarget);
                emitQuote(actual.configuration().machineId(),actual.configuration().reviewAtUtc(),requestTarget,output);
            } else {
                var published=prepared.publish(requestBinding,requestTarget,clock);
                System.out.println(ControlBuild.strictMapper().writeValueAsString(published.actualWitness()));
            }
            return;
        }
        if(args.length!=3)throw new IllegalArgumentException(
                "quote-definitions DECL_PATH BYTES SHA --target TARGET; quote-request DECL_EXACT3 --definitions-binding BIND_EXACT3 --definitions-target TARGET --request-target TARGET; publish-request adds --request-binding BIND_EXACT3; or ACTUAL_PUBLICATION_REQUEST_PATH BYTES SHA256");
        long bytes=Long.parseLong(args[1]);require(Long.toString(bytes).equals(args[1]),"canonical request length required");
        var published=execute(new FileRef(args[0],bytes,args[2]),clock);
        System.out.println(ControlBuild.strictMapper().writeValueAsString(published.actualWitness()));
    }
    private static void emitQuote(String machine,String review,Path target,RootBootstrapOutputContract.Output output)throws IOException {
        normalized(target);require(target.getParent()!=null&&target.getFileName()!=null
                &&target.getFileName().toString().equals(output.fileName()),"exact issuer quote target required");
        RootBootstrapProtocol.emit(new RootBootstrapProtocol.OrdinaryQuote("xar.java-root-bootstrap-phase-quote/v1",output.kind().name(),
                machine,review,target.getParent().toString(),List.of(output),List.of(),List.of(),"AWAITING_REAL_INDEPENDENT_ISSUER_BINDING"));
    }
    private static byte[] readData(FileRef ref,int maximum)throws IOException {
        RootRuntimeDefinitionModel.file(ref,maximum);byte[] bytes;
        try(var input=Files.newInputStream(Path.of(ref.path()))){bytes=input.readNBytes(Math.addExact(maximum,1));}
        if(bytes.length!=ref.bytes()||bytes.length>maximum||!sha(bytes).equalsIgnoreCase(ref.sha256()))
            throw new IOException("exact definitions DATA bytes/SHA mismatch: "+ref.path());
        return bytes;
    }
    private static SharedSourceFiles.Witness outputWitness(FileRef ref)throws IOException {
        var witness=SharedSourceFiles.observe(Path.of(ref.path()));
        require(witness.source().equals(ref),"published output witness differs from the emitted DATA");return witness;
    }
    private static void fileTarget(Path target){normalized(target);require(target.getParent()!=null&&target.getFileName()!=null,"explicit DATA file target required");}

    private static String sha(byte[] bytes){return org.xar.ck3.control.application.driver.DriverJson.sha256(bytes);}
    private static void normalized(Path path){Objects.requireNonNull(path);absolute(path.toString());}
    private static void require(boolean value,String why){if(!value)throw new IllegalArgumentException(why);}
}
