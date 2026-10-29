package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.root.RootBootstrapOutputContract.Output;
import org.xar.ck3.control.service.root.RootBootstrapOutputContract.RetainedInput;
import org.xar.ck3.control.service.root.RootProfileBootstrapInputs.Created;

/** One wire contract for the original writer and the finite duplex consumer. No capacity is minted here. */
public final class RootBootstrapProtocol {
    private RootBootstrapProtocol() { }
    public static final int FRAME_BYTES=(1<<20)+1, BINDING_BYTES=65536;
    public enum Mode {
        PROFILE(List.of("PROFILE_PRODUCTION_INVENTORY","PROFILE_ASSETS","PROFILE_ENVIRONMENT"),8L<<20,196611),
        FORMAL_RELEASE(List.of("FORMAL_RELEASE_PAYLOAD_AND_MANIFEST"),4L<<20,65537),
        ORIGINAL_DRIVER_RUN_PROFILE(List.of("ORIGINAL_DRIVER_RUN_PROFILE"),4L<<20,65537),
        NORMAL_EXIT(List.of("ORIGINAL_SETTINGS_SNAPSHOT","NORMAL_EXIT_TARGET_BINDING","NORMAL_EXIT_INVENTORY_AND_PROJECTION","NORMAL_EXIT_MANAGED_PROFILE"),12L<<20,262148);
        private final List<String> phases; private final long received,sent;
        Mode(List<String> phases,long received,long sent){this.phases=phases;this.received=received;this.sent=sent;}
        public List<String> phases(){return phases;} public long receivedBytes(){return received;} public long sentBytes(){return sent;}
    }
    public sealed interface Quote permits OrdinaryQuote,FormalQuote {
        String schema();String phase();String machineId();String reviewAtUtc();String assetRoot();
        List<Output> outputs();List<String> outputDirectories();List<RetainedInput> retainedInputs();String authority();
    }
    public record OrdinaryQuote(String schema,String phase,String machineId,String reviewAtUtc,String assetRoot,
            List<Output> outputs,List<String> outputDirectories,List<RetainedInput> retainedInputs,String authority) implements Quote {
        public OrdinaryQuote {
            outputs=List.copyOf(outputs);outputDirectories=List.copyOf(outputDirectories);retainedInputs=List.copyOf(retainedInputs);
            require("xar.java-root-bootstrap-phase-quote/v1".equals(schema),"ordinary quote schema");
            quoteCommon(phase,machineId,reviewAtUtc,assetRoot,outputs,authority);
        }
    }
    public record FormalQuote(String schema,String phase,String machineId,String reviewAtUtc,String assetRoot,
            List<Output> outputs,List<String> outputDirectories,List<RetainedInput> retainedInputs,
            String layout,String purpose,long assetPeakUpperBytes,long branchAssetCeilingBytes,
            long branchControlCeilingBytes,long maximumSingleWriteBytes,int maximumEntries,String authority) implements Quote {
        public FormalQuote {
            outputs=List.copyOf(outputs);outputDirectories=List.copyOf(outputDirectories);retainedInputs=List.copyOf(retainedInputs);
            require("xar.java-root-bootstrap-formal-release-phase-quote/v2".equals(schema),"formal quote schema");
            quoteCommon(phase,machineId,reviewAtUtc,assetRoot,outputs,authority);
            org.xar.ck3.control.build.FormalReleaseProducer.Layout.valueOf(layout);
            require(RootBootstrapOutputContract.FORMAL_PURPOSE.equals(purpose)&&assetPeakUpperBytes>0
                    &&assetPeakUpperBytes<=branchAssetCeilingBytes&&branchAssetCeilingBytes==RootBootstrapOutputContract.FORMAL_MAXIMUM_ASSET_BYTES
                    &&branchControlCeilingBytes==RootBootstrapOutputContract.MAXIMUM_CONTROL_BYTES
                    &&maximumSingleWriteBytes==outputs.stream().mapToLong(Output::bytes).max().orElseThrow()
                    &&maximumEntries==outputs.size()+outputDirectories.size(),"formal quote limits differ from its exact branch plan");
        }
    }
    public record Stage(List<Created> created,RootBootstrapOutputGuard.Accounting accounting) {
        public Stage {created=List.copyOf(created);Objects.requireNonNull(accounting);require(!created.isEmpty(),"created originals required");
            require(accounting.status()!=null&&accounting.assetChargedUpperBytes()>=0&&accounting.controlChargedUpperBytes()>=0
                    &&accounting.unresolvedPeakBytes()>=0&&accounting.completedOutputs()>=0&&accounting.retainedAllocatedUpperBytes()>=0,"actual nonnegative accounting required");}
    }
    public record Emission<T>(String status,String machineId,String observedAtUtc,T originals) {
        public Emission {Objects.requireNonNull(status);Objects.requireNonNull(machineId);instant(observedAtUtc);Objects.requireNonNull(originals);}
    }
    public record ClassOrigin(String className,FileRef archive) {
        public ClassOrigin {Objects.requireNonNull(className);Objects.requireNonNull(archive);}
    }
    public record Origin(String schema,Mode mode,String machineId,FileRef request,List<ClassOrigin> classes,ClassOrigin carrier) {
        public Origin {require("xar.java-root-bootstrap-child-origins/v1".equals(schema),"origin schema");Objects.requireNonNull(mode);
            Objects.requireNonNull(machineId);Objects.requireNonNull(request);Objects.requireNonNull(carrier);classes=List.copyOf(classes);require(!classes.isEmpty(),"actual child origins required");}
    }
    public record IssuerQuote(String schema,Mode mode,String phase,FileRef sessionRequest,FileRef quote,
            WindowsJobProcess.ProcessIdentity child,String sessionNonce,long arrivalSequence,String deadline) {
        public IssuerQuote {require("xar.java-root-bootstrap-issuer-quote/v1".equals(schema),"issuer quote schema");Objects.requireNonNull(mode);
            Objects.requireNonNull(sessionRequest);Objects.requireNonNull(quote);Objects.requireNonNull(child);instant(deadline);
            require(mode.phases().contains(phase)&&arrivalSequence>0&&sessionNonce!=null&&sessionNonce.matches("[0-9a-f]{64}"),"exact opaque arrival correlation required");}
    }
    public record IssuerReply(String schema,IssuerQuote original,FileRef binding) {
        public IssuerReply {require("xar.java-root-bootstrap-issuer-reply/v1".equals(schema),"issuer reply schema");Objects.requireNonNull(original);Objects.requireNonNull(binding);
            java.nio.file.Path path=java.nio.file.Path.of(binding.path());
            long maximum=original.mode()==Mode.FORMAL_RELEASE?RootBootstrapOutputContract.FORMAL_MAXIMUM_AUTHORITY_BYTES:RootBootstrapOutputContract.MAXIMUM_BYTES;
            require(path.isAbsolute()&&path.normalize().equals(path)&&binding.bytes()>0&&binding.bytes()<=maximum,"bounded canonical exact issuer binding original required");}
    }
    /** A direct Command reads this exact channel; it is not an OwnedStdio Session or a write receipt. */
    public record FileReplyChannel(String schema,String machineId,String deadline,
            RootProfileBootstrapCommand.Mode mode,FileRef bootstrapRequest,String issuerReplyRoot,
            SharedSourceFiles.DirectoryIdentity issuerReplyDirectory) {
        public FileReplyChannel {
            require("xar.java-root-bootstrap-file-reply-channel/v1".equals(schema),"file reply channel schema");
            require(machineId!=null&&!machineId.isBlank(),"actual channel machine required");instant(deadline);
            Objects.requireNonNull(mode);commandPhases(mode);bounded(bootstrapRequest,65536);
            absolute(issuerReplyRoot);Objects.requireNonNull(issuerReplyDirectory);
        }
    }
    /** Exact files and Native witnesses replace only the binding transport, never the original Guard. */
    public record FileReply(String schema,FileRef channel,FileRef bootstrapRequest,
            RootProfileBootstrapCommand.Mode mode,String phase,int phaseIndex,String deadline,
            FileRef quote,SharedSourceFiles.NativeFile quoteNativeFile,FileRef binding) {
        public FileReply {
            require("xar.java-root-bootstrap-file-reply/v1".equals(schema),"file reply schema");
            bounded(channel,65536);bounded(bootstrapRequest,65536);Objects.requireNonNull(mode);instant(deadline);
            var phases=commandPhases(mode);
            require(phaseIndex>=0&&phaseIndex<phases.size()&&phases.get(phaseIndex).equals(phase),"exact command phase/order required");
            bounded(quote,FRAME_BYTES);Objects.requireNonNull(quoteNativeFile);
            bounded(binding,mode==RootProfileBootstrapCommand.Mode.FORMAL_RELEASE
                    ?RootBootstrapOutputContract.FORMAL_MAXIMUM_AUTHORITY_BYTES:RootBootstrapOutputContract.MAXIMUM_BYTES);
        }
    }
    static List<String> commandPhases(RootProfileBootstrapCommand.Mode mode) {
        return switch(Objects.requireNonNull(mode)){
            case PROFILE->Mode.PROFILE.phases();case FORMAL_RELEASE->Mode.FORMAL_RELEASE.phases();
            case ORIGINAL_DRIVER_RUN_PROFILE->Mode.ORIGINAL_DRIVER_RUN_PROFILE.phases();case NORMAL_EXIT->Mode.NORMAL_EXIT.phases();
            case EXPLICIT_SAVED_PROFILE,EXPLICIT_FIXTURE_PROFILE->List.of(mode.name()+"_ENVIRONMENT");
            case INITIAL_POLICY,INITIAL_FIXTURE_POLICY,INITIAL_SAVED_NATIVE_POLICY->List.of(mode.name());
            default->throw new IllegalArgumentException("issuer/census command cannot consume a binding reply channel");
        };
    }
    public static byte[] encode(Object value,int maximum)throws IOException {
        return StrictJson.canonical(ControlBuild.strictMapper().valueToTree(value),maximum);
    }
    public static <T>T decode(byte[] bytes,int maximum,Class<T> type)throws IOException {
        var node=StrictJson.parse(bytes,maximum);
        if(type==Quote.class){
            Quote quote=switch(node.path("schema").asText()){
                case "xar.java-root-bootstrap-phase-quote/v1"->ControlBuild.strictMapper().readValue(bytes,OrdinaryQuote.class);
                case "xar.java-root-bootstrap-formal-release-phase-quote/v2"->ControlBuild.strictMapper().readValue(bytes,FormalQuote.class);
                default->throw new IOException("unknown exact phase quote schema");
            };return type.cast(quote);
        }
        return ControlBuild.strictMapper().readValue(bytes,type);
    }
    public static <T>T line(byte[] raw,Class<T> type)throws IOException {
        if(raw.length<2||raw.length>FRAME_BYTES||raw[raw.length-1]!='\n')throw new IOException("bounded complete LF frame required");
        byte[] bytes=java.util.Arrays.copyOf(raw,raw.length-1);return decode(bytes,FRAME_BYTES-1,type);
    }
    public static Stage stage(byte[] raw,String expectedMachine)throws IOException {
        var node=StrictJson.parse(trim(raw),FRAME_BYTES-1);
        var type=ControlBuild.strictMapper().getTypeFactory().constructParametricType(Emission.class,Stage.class);
        Emission<Stage> emission=ControlBuild.strictMapper().readValue(encode(node,FRAME_BYTES-1),type);
        requireIo("STAGE_CREATED_NO_GAME_ADMISSION".equals(emission.status()),"expected original stage completion");
        requireIo(emission.machineId().equals(expectedMachine),"original stage machine differs from its actual quote");
        return emission.originals();
    }
    public static byte[] trim(byte[] raw)throws IOException {
        if(raw.length<2||raw.length>FRAME_BYTES||raw[raw.length-1]!='\n')throw new IOException("bounded complete LF frame required");
        return java.util.Arrays.copyOf(raw,raw.length-1);
    }
    public static void emit(Object value)throws IOException {System.out.write(encode(value,FRAME_BYTES-1));System.out.write('\n');System.out.flush();}
    public static byte[] quoteLine(Quote quote)throws IOException {
        byte[] bytes=encode(quote,FRAME_BYTES-1),line=java.util.Arrays.copyOf(bytes,bytes.length+1);
        line[bytes.length]='\n';return line;
    }
    public static byte[] bindingLine(FileRef binding)throws IOException {
        byte[] bytes=encode(binding,BINDING_BYTES);byte[] line=java.util.Arrays.copyOf(bytes,bytes.length+1);line[bytes.length]='\n';return line;
    }
    static void instant(String value){require(value!=null&&Instant.parse(value).toString().equals(value),"canonical UTC instant required");}
    private static void absolute(String value){
        require(value!=null,"canonical absolute path required");var path=java.nio.file.Path.of(value);
        require(path.isAbsolute()&&path.normalize().equals(path),"canonical absolute path required");
    }
    private static void bounded(FileRef ref,long maximum){
        Objects.requireNonNull(ref);absolute(ref.path());require(ref.bytes()>0&&ref.bytes()<=maximum,"bounded exact original required");
    }
    private static void quoteCommon(String phase,String machine,String review,String root,List<Output> outputs,String authority){
        require(phase!=null&&!phase.isBlank()&&machine!=null&&!machine.isBlank(),"actual quote phase/machine required");instant(review);
        require(root!=null&&java.nio.file.Path.of(root).isAbsolute()&&!outputs.isEmpty()
                &&outputs.stream().map(Output::fileName).distinct().count()==outputs.size()
                &&"AWAITING_REAL_INDEPENDENT_ISSUER_BINDING".equals(authority),"bounded exact quote plan and independent authority required");
    }
    static void require(boolean valid,String reason){if(!valid)throw new IllegalArgumentException(reason);}
    static void requireIo(boolean valid,String reason)throws IOException {if(!valid)throw new IOException(reason);}
}
