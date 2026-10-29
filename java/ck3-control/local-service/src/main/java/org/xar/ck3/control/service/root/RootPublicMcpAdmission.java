package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.OriginalMcpCapture;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.platform.NativeBridgeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.service.mcp.McpCoverage;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpNativeAdapter;

/** Sole initial admission DATA producer. Both phases run without Core, Native calls or Game queries.
 * Bootstrap output is explicitly unqualified; only actual typed Java bindings can become ADMITTED.
 * Final runtime definitions select the final file. The bootstrap admission/definitions are retained
 * preparation inputs and never acquire dispatch or complete-migration authority. */
public final class RootPublicMcpAdmission {
    private static final String TARGET="local-service/src/main/java/org/xar/ck3/control/service/root/RootPublicMcpAdmission.java";
    private RootPublicMcpAdmission() { }

    /** Real original capture plus its identical selected-configuration original. No synthetic registration table. */
    public static FileRef bootstrap(FileRef captureReceipt,FileRef nativePlan,FileRef outputBinding,Path target,Clock clock)throws IOException {
        RawJson bootstrap=bootstrapDocument(captureReceipt,nativePlan,clock);
        try(var authority=RootBootstrapOutputGuard.readExact(outputBinding,clock)) {
            FileRef actual=write(authority,target,bootstrap);
            require(java.util.Arrays.equals(bootstrap.bytes(),bootstrapDocument(captureReceipt,nativePlan,clock).bytes()),"bootstrap sources changed during actual publication");
            return actual;
        }
    }
    /** Real read-only quote for the existing issuer; this is not a created DATA file or output permission. */
    public static RootBootstrapOutputContract.Output quoteBootstrap(FileRef captureReceipt,FileRef nativePlan,Path target,Clock clock)throws IOException {
        return quote(target,bootstrapDocument(captureReceipt,nativePlan,clock));
    }
    private record BootstrapPrepared(RawJson document,String machineId,String reviewAtUtc) { }
    private static RawJson bootstrapDocument(FileRef captureReceipt,FileRef nativePlan,Clock clock)throws IOException {
        return prepareBootstrap(captureReceipt,nativePlan,clock).document();
    }
    private static BootstrapPrepared prepareBootstrap(FileRef captureReceipt,FileRef nativePlan,Clock clock)throws IOException {
        Objects.requireNonNull(clock);var captured=RootOriginalMcpCapture.readRetained(captureReceipt);captured.requireCurrent(clock);
        var plan=NativeLaunchPlan.readExact(exact(nativePlan),new NativeBridgeLaunchEvidence());
        plan.sources().requireLoadedClass(RootPublicMcpAdmission.class);
        var own=plan.sources().review().completeRuntimeSources().stream()
            .filter(ref->Path.of(ref.path()).getFileName().toString().equals("RootPublicMcpAdmission.java")).toList();
        require(own.size()==1,"one source-qualified admission producer required");own.getFirst().verify();
        var originalPlan=OriginalMcpCapture.decodePlan(read(captured.actual().capturePlanRef(),OriginalMcpCapture.CONTROL_MAX));
        var configurationRef=originalPlan.selectedConfigurationRef();
        var configuration=RootSelectedRegistrationConfiguration.decode(read(configurationRef,65536));
        require(configuration.machineId().equals(captured.actual().machineId()),"captured registration/configuration machine differs");
        var catalog=McpCoverage.readCatalog(new RawJson(read(captured.actual().documents().catalog().original(),OriginalMcpCapture.DOCUMENT_MAX)));
        var registered=RootPublicCatalogCodec.decodeTools(new RawJson(read(captured.actual().documents().tools().original(),OriginalMcpCapture.DOCUMENT_MAX)))
            .stream().map(value->value.name()).collect(java.util.stream.Collectors.toUnmodifiableSet());
        RawJson bootstrap=bootstrapDocument(catalog,registered,configuration,exact(configurationRef),exact(own.getFirst()));
        captured.requireCurrent(clock);plan.sources().verify();
        var review=configuration.reviewAt().isBefore(plan.deadline())?configuration.reviewAt():plan.deadline();
        require(clock.instant().isBefore(review),"actual bootstrap quote/source period expired");
        return new BootstrapPrepared(bootstrap,captured.actual().machineId(),review.toString());
    }

    static RawJson bootstrapDocument(McpCoverage.Catalog catalog,Set<String> registered,
            RootSelectedRegistrationConfiguration.Configuration configuration,ExactRef configurationRef,ExactRef producer) {
        var decisions=new ArrayList<McpCoverage.Decision>();
        for(var declaration:catalog.declarations()) {
            String falseClause=RootSelectedRegistrationConfiguration.fixtureFalseClause(configuration,declaration);
            boolean excluded=!registered.contains(declaration.name())&&falseClause!=null
                &&declaration.source().equals(configuration.source(RootSelectedRegistrationConfiguration.SourceRole.ORIGINAL_MCP_SERVER));
            decisions.add(new McpCoverage.Decision(declaration.name(),excluded?McpCoverage.Admission.EXCLUDED_BY_CURRENT_CONFIGURATION:McpCoverage.Admission.UNMIGRATED,
                excluded?configurationRef:producer,excluded?falseClause:"BOOTSTRAP_ONLY: original registration captured; actual Java typed binding has not yet been constructed"));
        }
        return RootPublicCatalogCodec.encodeAdmission(decisions);
    }

    /** Called only by the retained Startup which constructed these same typed products from real provisional Inputs. */
    static FileRef publish(RootRuntimeDefinitions.Inputs inputs,RootRuntimePublicCatalog.HandlerProducts handlers,
            RootSelectedRegistrationConfiguration.Bound configuration,RootBootstrapInputFiles authority,Path target,Clock clock)throws IOException {
        RawJson document=prepared(inputs,handlers,configuration,clock);
        require(!Path.of(inputs.data(RootRuntimeDefinitionModel.DataRole.MCP_ADMISSION).path()).equals(target),"final admission needs a distinct immutable target");
        FileRef actual=write(authority,target,document);
        configuration.requireInputs(inputs);return actual;
    }
    static RootBootstrapOutputContract.Output quote(RootRuntimeDefinitions.Inputs inputs,RootRuntimePublicCatalog.HandlerProducts handlers,
            RootSelectedRegistrationConfiguration.Bound configuration,Path target,Clock clock)throws IOException {
        return quote(target,prepared(inputs,handlers,configuration,clock));
    }
    private static RawJson prepared(RootRuntimeDefinitions.Inputs inputs,RootRuntimePublicCatalog.HandlerProducts handlers,
            RootSelectedRegistrationConfiguration.Bound configuration,Clock clock)throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(configuration);Objects.requireNonNull(clock);
        configuration.requireInputs(inputs);
        var original=RootRuntimePublicCatalog.Sources.readOriginals(inputs);
        Set<String> exclusions=RootRuntimePublicCatalog.configurationExclusions(inputs,original,configuration);
        var own=inputs.sourceIndex().stream().filter(row->row.targetRelative().equals(TARGET)).toList();
        require(own.size()==1,"one selected admission producer required");
        var selected=inputs.sourceIndex().stream().map(row->row.sourceRef()).collect(java.util.stream.Collectors.toUnmodifiableSet());
        var finalDecisions=derive(original,handlers,exclusions,selected,own.getFirst().sourceRef());
        configuration.requireInputs(inputs);
        return RootPublicCatalogCodec.encodeAdmission(finalDecisions);
    }

    /** Actual typed binding evidence is required; source declarations, enum entries and old ADMITTED labels are insufficient. */
    static List<McpCoverage.Decision> derive(RootPublicCatalogCodec.PublicCatalog original,
            RootRuntimePublicCatalog.HandlerProducts handlers,Set<String> exclusions,Set<ExactRef> selected,ExactRef producer) {
        require(selected.contains(producer),"admission producer is outside the selected source graph");
        var direct=new HashMap<String,McpExecutableDirectory.DirectBinding<?,?>>();
        for(var binding:handlers.actualDirect())require(direct.putIfAbsent(binding.name(),binding)==null,"duplicate actual direct binding");
        Set<String> descriptors=original.tools().stream().map(value->value.name()).collect(java.util.stream.Collectors.toUnmodifiableSet());
        var decisions=new ArrayList<McpCoverage.Decision>();
        for(var declaration:original.catalog().declarations()) {
            if(exclusions.contains(declaration.name())) {
                var excluded=original.admission().stream().filter(row->row.name().equals(declaration.name())
                    &&row.admission()==McpCoverage.Admission.EXCLUDED_BY_CURRENT_CONFIGURATION).toList();
                require(excluded.size()==1&&!descriptors.contains(declaration.name()),"validated exclusion must retain its exact absent original registration");
                decisions.add(excluded.getFirst());continue;
            }
            Optional<PublicBindings.BoundBinding> service=service(handlers.actualServices(),declaration.name());
            var binding=direct.get(declaration.name());
            require(service.isEmpty()||binding==null,"same original identity has both service and direct typed bindings");
            if(service.isEmpty()&&binding==null&&retired(declaration.name())) {
                var retirementSources=selected.stream().filter(ref->Path.of(ref.path()).getFileName().toString().equals("PublicMethod.java")).toList();
                require(retirementSources.size()==1,"source-owned retirement requires its exact selected PublicMethod producer");
                decisions.add(new McpCoverage.Decision(declaration.name(),McpCoverage.Admission.RETIRED,retirementSources.getFirst(),
                    "The selected PublicMethod producer explicitly retires this service identity; no callable or native success inferred"));
                continue;
            }
            ExactRef actual=service.isPresent()?service.orElseThrow().info().target().orElseThrow().implementationSource()
                :binding!=null?binding.target().implementationSource():null;
            if(actual!=null)require(selected.contains(actual),"actual typed admission source is outside the selected graph");
            boolean admitted=actual!=null&&descriptors.contains(declaration.name());
            decisions.add(new McpCoverage.Decision(declaration.name(),admitted?McpCoverage.Admission.ADMITTED:McpCoverage.Admission.UNMIGRATED,
                admitted?actual:producer,admitted?"Actual pre-Core typed Java binding constructed; invocation retains its independent Core, Native and Game guards"
                :"No actual typed Java binding and matching original descriptor; no dispatch, retirement or configured exclusion inferred"));
        }
        return List.copyOf(decisions);
    }
    private static Optional<PublicBindings.BoundBinding> service(PublicBindings registry,String name) {
        final PublicMethod method;
        try{method=PublicMcpNativeAdapter.expectedServiceMethod(name);}catch(IllegalArgumentException notService){return Optional.empty();}
        return registry.lookup(method);
    }
    private static boolean retired(String name) {
        try{return PublicMcpNativeAdapter.expectedServiceMethod(name).retired();}
        catch(IllegalArgumentException notService){return false;}
    }
    private static FileRef write(RootBootstrapInputFiles authority,Path target,RawJson document)throws IOException {
        Objects.requireNonNull(authority);Objects.requireNonNull(target);
        if(!(authority instanceof RootBootstrapOutputGuard actual))throw new IOException("admission publisher requires the original immutable output guard");
        requireOutputPlan(actual,target,quote(target,document));authority.requireTargets(List.of(target));
        byte[] bytes=document.bytes();require(bytes.length<=RootRuntimeDefinitionModel.maximumDataBytes(RootRuntimeDefinitionModel.DataRole.MCP_ADMISSION),"bounded final admission document required");
        require(authority.files().observe(target).isEmpty(),"admission output already exists or is unknown; no replay/overwrite");
        var witness=authority.files().createNew(target,bytes);authority.files().verify(witness);
        require(java.util.Arrays.equals(bytes,authority.files().read(witness,bytes.length)),"actual admission output readback differs");
        var source=SharedSourceFiles.observe(target);authority.requireTargets(List.of(target));
        require(source.source().bytes()==bytes.length&&RootPublicCatalogCodec.decodeAdmission(new RawJson(read(source.source(),bytes.length)))
            .equals(RootPublicCatalogCodec.decodeAdmission(document)),"actual admission serialization roundtrip differs");
        return source.source();
    }
    /** The sole actual publisher binds semantic output Kind as well as the already guarded bytes/SHA. */
    static void requireOutputPlan(RootBootstrapOutputGuard authority,Path target,RootBootstrapOutputContract.Output expected)throws IOException {
        Objects.requireNonNull(authority);Objects.requireNonNull(target);Objects.requireNonNull(expected);
        require(expected.kind()==RootBootstrapOutputContract.Kind.MCP_ADMISSION,"actual admission output kind required");
        authority.requirePlan(target.getParent(),List.of(expected),List.of(),List.of());
    }
    private static byte[] read(FileRef source,int maximum)throws IOException {
        source.verify();require(source.bytes()>0&&source.bytes()<=maximum,"bounded exact admission input required");
        byte[] bytes=Files.readAllBytes(Path.of(source.path()));source.verify();return bytes;
    }
    private static ExactRef exact(FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static RootBootstrapOutputContract.Output quote(Path target,RawJson document) {
        require(target.isAbsolute()&&target.normalize().equals(target),"absolute normalized admission target required");
        require(document.bytes().length<=RootRuntimeDefinitionModel.maximumDataBytes(RootRuntimeDefinitionModel.DataRole.MCP_ADMISSION),"bounded admission quote required");
        return new RootBootstrapOutputContract.Output(RootBootstrapOutputContract.Kind.MCP_ADMISSION,target.getFileName().toString(),document.bytes().length,
            OriginalMcpCapture.sha256(document.bytes()));
    }
    private static void require(boolean value,String why){if(!value)throw new IllegalArgumentException(why);}
    private static FileRef ref(String path,String count,String sha){long bytes=Long.parseLong(count);require(Long.toString(bytes).equals(count),"canonical reference byte count required");return new FileRef(path,bytes,sha);}
    private static void emitQuote(String machine,String review,Path target,RootBootstrapOutputContract.Output output)throws IOException {
        require(target.isAbsolute()&&target.normalize().equals(target)&&target.getParent()!=null
                &&target.getFileName().toString().equals(output.fileName()),"exact issuer admission quote target required");
        RootBootstrapProtocol.emit(new RootBootstrapProtocol.OrdinaryQuote("xar.java-root-bootstrap-phase-quote/v1",output.kind().name(),
                machine,review,target.getParent().toString(),List.of(output),List.of(),List.of(),"AWAITING_REAL_INDEPENDENT_ISSUER_BINDING"));
    }
    /** Existing qualified Root command entry only; neither mode installs public dispatch or starts the Game. */
    public static void main(String[] args)throws Exception {
        if(args.length==8&&args[0].equals("quote-bootstrap")) {
            var prepared=prepareBootstrap(ref(args[1],args[2],args[3]),ref(args[4],args[5],args[6]),Clock.systemUTC());
            Path target=Path.of(args[7]);emitQuote(prepared.machineId(),prepared.reviewAtUtc(),target,quote(target,prepared.document()));return;
        }
        if(args.length==5&&args[0].equals("quote-qualify")) {
            var definitions=RootRuntimeDefinitions.readExact(ref(args[1],args[2],args[3]),Clock.systemUTC());Path target=Path.of(args[4]);
            var quote=definitions.quotePublicAdmission(target);var configuration=definitions.inputs().configuration();
            emitQuote(configuration.machineId(),configuration.reviewAtUtc(),target,quote);return;
        }
        FileRef result;
        if(args.length==11&&args[0].equals("bootstrap"))result=bootstrap(ref(args[1],args[2],args[3]),ref(args[4],args[5],args[6]),
            ref(args[7],args[8],args[9]),Path.of(args[10]),Clock.systemUTC());
        else if(args.length==8&&args[0].equals("qualify"))result=RootRuntimeDefinitions.readExact(ref(args[1],args[2],args[3]),Clock.systemUTC())
            .publishPublicAdmission(ref(args[4],args[5],args[6]),Path.of(args[7]));
        else throw new IllegalArgumentException("bootstrap CAPTURE_REF NATIVE_PLAN_REF OUTPUT_BINDING_REF TARGET | qualify PROVISIONAL_DEFINITIONS_REF OUTPUT_BINDING_REF TARGET | quote-bootstrap CAPTURE_REF NATIVE_PLAN_REF TARGET | quote-qualify PROVISIONAL_DEFINITIONS_REF TARGET (each ref: PATH BYTES SHA)");
        System.out.println(ControlBuild.strictMapper().writeValueAsString(result));
    }
}
