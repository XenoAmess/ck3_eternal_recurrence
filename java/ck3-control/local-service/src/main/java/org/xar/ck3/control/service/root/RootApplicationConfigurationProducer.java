package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** First immutable application input from explicit actual fields. No Core, ledger writer, template or Native permit is created. */
public final class RootApplicationConfigurationProducer {
    public static final String REQUEST_SCHEMA="xar.java-application-configuration-publication-request/v1";
    public static final int MAXIMUM_REQUEST_BYTES=RootJavaBootstrapInputs.MAXIMUM_REQUEST_BYTES;
    private RootApplicationConfigurationProducer() { }

    /** Missing actual input is an error, never a default configuration or a qualification result. */
    public static final class Missing extends IOException {
        public Missing(String reason){super(reason);}
        public Missing(String reason,Throwable cause){super(reason,cause);}
    }

    public static final class Prepared {
        private final RootApplicationConfiguration configuration;
        private final Path target;private final Clock clock;private final byte[] bytes;
        private final SharedSourceFiles.DirectoryIdentity parent;
        private final List<SharedSourceFiles.Witness> originals;
        private boolean attempted;
        private Prepared(RootApplicationConfiguration configuration,Path target,Clock clock,
                SharedSourceFiles.DirectoryIdentity parent,List<SharedSourceFiles.Witness> originals)throws IOException {
            this.configuration=configuration;this.target=target;this.clock=clock;this.parent=parent;this.originals=List.copyOf(originals);
            // This is the sole existing App representation and canonical encoder, without a parallel DTO.
            bytes=StrictJson.canonical(configuration.toJson(),RootApplicationConfiguration.MAXIMUM_BYTES);
            if(!RootApplicationConfiguration.fromJson(StrictJson.parse(bytes,RootApplicationConfiguration.MAXIMUM_BYTES)).equals(configuration))
                throw new Missing("actual application fields changed through their sole App codec");
        }
        public RootApplicationConfiguration configuration(){return configuration;}
        public Path target(){return target;}
        public byte[] bytes(){return bytes.clone();}
        public FileRef expected(){return new FileRef(target.toString(),bytes.length,DriverJson.sha256(bytes));}
        /** A read-only quote grants neither a write nor runtime admission. */
        public RootBootstrapOutputContract.Output quote()throws IOException {
            requireCurrent();return new RootBootstrapOutputContract.Output(RootBootstrapOutputContract.Kind.APPLICATION,
                    target.getFileName().toString(),bytes.length,DriverJson.sha256(bytes));
        }
        public void requireCurrent()throws IOException {
            configuration.requireCurrent(clock);validateTarget(configuration,target);
            if(!parent.equals(SharedSourceFiles.nativeDirectory(target.getParent())))throw new Missing("actual application output directory identity changed");
            for(var original:originals)unchanged(original);
        }
        /** The actual independently issued concrete guard is the only physical writer. Unknown writes are not retried. */
        public synchronized Published createNew(FileRef actualBinding)throws IOException {
            if(attempted)throw new Missing("application publication already attempted; reconcile the original unknown write, never replay");
            if(actualBinding==null)throw new Missing("actual finite APPLICATION output binding is required");
            var output=quote();
            try(var authority=RootBootstrapOutputGuard.readExact(actualBinding,clock)) {
                authority.requirePlan(target.getParent(),List.of(output),List.of(),List.of());
                authority.requireTargets(List.of(target));requireCurrent();
                var files=authority.files();attempted=true;
                var created=files.createNew(target,bytes);files.verify(created);
                if(!same(expected(),created.reference())||!Arrays.equals(bytes,files.read(created,RootApplicationConfiguration.MAXIMUM_BYTES)))
                    throw new Missing("actual immutable application readback differs from its sole typed producer");
                var nativeBefore=SharedSourceFiles.nativeFile(target);var witness=SharedSourceFiles.observe(target);
                if(!expected().equals(witness.source())||!nativeBefore.equals(witness.nativeFile()))
                    throw new Missing("actual application publication changed native file identity");
                var decoded=RootApplicationConfiguration.readExact(expected());decoded.requireCurrent(clock);
                if(!decoded.equals(configuration))throw new Missing("sole application reader did not consume the original actual typed fields");
                unchanged(witness);requireCurrent();files.verify(created);authority.requireTargets(List.of(target));
                if(files!=authority.files()||authority.accounting().completedOutputs()!=1)
                    throw new Missing("application publication did not finish its one exact priced output");
                return new Published(configuration,expected(),witness,originals);
            }
        }
    }

    public static final class Published {
        private final RootApplicationConfiguration configuration;private final FileRef original;
        private final SharedSourceFiles.Witness witness;
        private final List<SharedSourceFiles.Witness> sourceOriginals;
        private Published(RootApplicationConfiguration configuration,FileRef original,SharedSourceFiles.Witness witness,
                List<SharedSourceFiles.Witness> sourceOriginals) {
            this.configuration=configuration;this.original=original;this.witness=witness;this.sourceOriginals=List.copyOf(sourceOriginals);
        }
        public FileRef original(){return original;}
        /** Captured file metadata; call readExact for a fresh original-custody check. */
        public SharedSourceFiles.NativeFile nativeFile(){return witness.nativeFile();}
        public RootApplicationConfiguration readExact(Clock clock)throws IOException {
            if(clock==null)throw new Missing("actual application review clock is required");
            unchanged(witness);for(var source:sourceOriginals)unchanged(source);
            var decoded=RootApplicationConfiguration.readExact(original);decoded.requireCurrent(clock);
            if(!decoded.equals(configuration))throw new Missing("retained application configuration fields changed");
            for(var source:sourceOriginals)unchanged(source);unchanged(witness);return decoded;
        }
    }

    /** Quote-before-binding avoids requiring an already-created App or Core to produce the first App file. */
    public static Prepared prepare(RootApplicationConfiguration actual,Path target,Clock clock)throws IOException {
        if(actual==null||target==null||clock==null)throw new Missing("explicit actual application fields, output target and clock are required");
        validateTarget(actual,target);
        if(Files.exists(target,LinkOption.NOFOLLOW_LINKS))throw new Missing("immutable application target already exists; no overwrite or implicit publication retry");
        var sources=new LinkedHashMap<Path,ExactRef>();
        add(sources,actual.nativeLaunchPlan());add(sources,actual.ledger().anchor());
        if(actual.writerSources().isEmpty()||actual.writerSources().size()>WriterContracts.MAXIMUM_CONFIGURED_SOURCES)throw new Missing("explicit complete finite writer sources are required");
        for(ExactRef source:actual.writerSources())add(sources,source);
        actual.requireCurrent(clock);SharedSourceFiles.plainAncestors(target);
        var parent=SharedSourceFiles.nativeDirectory(target.getParent());
        var originals=new ArrayList<SharedSourceFiles.Witness>();
        for(ExactRef source:sources.values()) {
            var before=SharedSourceFiles.nativeFile(Path.of(source.path()));var witness=SharedSourceFiles.observe(Path.of(source.path()));
            if(!same(witness.source(),source)||!before.equals(witness.nativeFile()))throw new Missing("actual application input reference or native identity changed: "+source.path());
            unchanged(witness);originals.add(witness);
        }
        var prepared=new Prepared(actual,target,clock,parent,originals);prepared.requireCurrent();return prepared;
    }
    private static void add(LinkedHashMap<Path,ExactRef> sources,ExactRef source)throws IOException {
        if(source==null||source.bytes()<1)throw new Missing("nonempty exact application source is required");
        Path path=Path.of(source.path());absolute(path);var previous=sources.putIfAbsent(path,source);
        if(previous!=null&&!previous.equals(source))throw new Missing("one application source path has conflicting actual identities");
    }
    private static void validateTarget(RootApplicationConfiguration configuration,Path target)throws IOException {
        absolute(target);
        var layout=configuration.ledger();
        if(target.equals(layout.snapshot())||target.equals(layout.lock())||target.startsWith(layout.events()))
            throw new Missing("immutable application output cannot replace any canonical mutable ledger path");
        for(ExactRef source:configuration.writerSources())if(target.equals(Path.of(source.path())))throw new Missing("application output cannot replace a writer source original");
        if(target.equals(Path.of(configuration.nativeLaunchPlan().path()))||target.equals(Path.of(layout.anchor().path())))
            throw new Missing("application output cannot replace native-plan or ledger-anchor originals");
    }
    private static void absolute(Path path)throws IOException {
        if(path==null||!path.isAbsolute()||!path.normalize().equals(path)||path.getParent()==null||path.getFileName()==null)
            throw new Missing("actual application source/output needs an absolute normalized file path");
    }
    private static boolean same(FileRef left,ExactRef right) {
        return Path.of(left.path()).equals(Path.of(right.path()))&&left.bytes()==right.bytes()&&left.sha256().equalsIgnoreCase(right.sha256());
    }
    private static void unchanged(SharedSourceFiles.Witness original)throws IOException {
        if(!SharedSourceFiles.nativeFile(Path.of(original.source().path())).equals(original.nativeFile()))throw new Missing("application original native file identity changed");
        SharedSourceFiles.assertUnchanged(original);
    }

    public enum Mode { QUOTE,CREATE_NEW }
    /** Publication invocation holds the same App value, never a second set of configuration fields. */
    public record Request(Mode mode,RootApplicationConfiguration actual,Path target,FileRef binding) {
        public Request {
            Objects.requireNonNull(mode);Objects.requireNonNull(actual);Objects.requireNonNull(target);
            argumentPath(target.toString());
            StrictJson.require((mode==Mode.QUOTE)==(binding==null),"application quote requires explicit null binding; create-new requires its actual binding");
            if(binding!=null){argumentPath(binding.path());new ExactRef(binding.path(),binding.bytes(),binding.sha256());}
        }
    }
    /** Strict request entry reuses the sole App codec; no preexisting application original is required. */
    public static Request decodeRequest(byte[] original) {
        var row=StrictJson.object(StrictJson.parse(original,MAXIMUM_REQUEST_BYTES),Set.of("schema","mode","actual","target","binding_ref"));
        StrictJson.require(REQUEST_SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact application publication request schema required");
        ExactRef binding=row.get("binding_ref").isNull()?null:ExactRef.fromJson(row.get("binding_ref"));
        return new Request(Mode.valueOf(StrictJson.text(row.get("mode"))),RootApplicationConfiguration.fromJson(row.get("actual")),
                argumentPath(StrictJson.text(row.get("target"))),binding==null?null:new FileRef(binding.path(),binding.bytes(),binding.sha256()));
    }
    public static byte[] encodeRequest(Request request) {
        Objects.requireNonNull(request);var row=StrictJson.object().put("schema",REQUEST_SCHEMA).put("mode",request.mode().name());
        row.set("actual",request.actual().toJson());row.put("target",request.target().toString());
        if(request.binding()==null)row.putNull("binding_ref");
        else row.set("binding_ref",new ExactRef(request.binding().path(),request.binding().bytes(),request.binding().sha256()).toJson());
        return StrictJson.canonical(row,MAXIMUM_REQUEST_BYTES);
    }
    static Request arguments(String[] args) {
        if(args==null||args.length<18)throw new IllegalArgumentException("explicit application fields and at least one writer source are required");
        Mode mode=Mode.valueOf(args[0]);
        if(!args[14].matches("[1-9][0-9]*"))throw new IllegalArgumentException("canonical actual writer-source count required");
        int count=Integer.parseInt(args[14]);if(count>WriterContracts.MAXIMUM_CONFIGURED_SOURCES)
            throw new IllegalArgumentException("at most "+WriterContracts.MAXIMUM_CONFIGURED_SOURCES+" actual writer sources");
        int end=15+3*count;
        if(args.length!=end+(mode==Mode.CREATE_NEW?3:0))throw new IllegalArgumentException("exact application fields/source triplets and CREATE_NEW binding required");
        Instant review=Instant.parse(args[3]);if(!review.toString().equals(args[3]))throw new IllegalArgumentException("canonical explicit UTC application review required");
        if(!args[12].matches("[1-9][0-9]{0,12}"))throw new IllegalArgumentException("canonical explicit artifact byte budget required");
        var writers=new ArrayList<ExactRef>();for(int index=0;index<count;index++)writers.add(argumentRef(args,15+3*index));
        var actual=new RootApplicationConfiguration(args[1],HostMode.valueOf(args[2]),review,argumentRef(args,4),
                new WriterContracts.Layout(argumentPath(args[7]),argumentRef(args,8),args[1]),writers,argumentPath(args[11]),Long.parseLong(args[12]));
        ExactRef binding=mode==Mode.CREATE_NEW?argumentRef(args,end):null;
        return new Request(mode,actual,argumentPath(args[13]),binding==null?null:new FileRef(binding.path(),binding.bytes(),binding.sha256()));
    }
    private static ExactRef argumentRef(String[] args,int offset) {
        if(!args[offset+1].matches("[1-9][0-9]{0,15}")||!args[offset+2].matches("[0-9a-f]{64}"))
            throw new IllegalArgumentException("actual application source needs canonical positive bytes and lowercase SHA-256");
        return new ExactRef(argumentPath(args[offset]).toString(),Long.parseLong(args[offset+1]),args[offset+2]);
    }
    private static Path argumentPath(String raw) {
        Path path=Path.of(raw);if(!path.isAbsolute()||!path.normalize().equals(path))
            throw new IllegalArgumentException("explicit absolute normalized application path required");
        return path;
    }
    /** No preexisting App is required. Arguments in order:
     * mode machine HostMode review nativePlan-triplet ledgerSnapshot anchor-triplet artifactRoot maximumArtifactBytes
     * target writerSourceCount writerSource-triplets [CREATE_NEW binding-triplet]. All fields are explicit.
     */
    static byte[] execute(String[] args,Clock clock)throws IOException {
        return execute(arguments(args),clock);
    }
    /** The shared bootstrap CLI and legacy explicit-fields CLI consume this one actual publisher. */
    public static byte[] execute(Request invocation,Clock clock)throws IOException {
        Objects.requireNonNull(invocation);Objects.requireNonNull(clock);
        Prepared prepared=prepare(invocation.actual(),invocation.target(),clock);
        if(invocation.mode()==Mode.QUOTE) {
            var quote=new RootBootstrapProtocol.OrdinaryQuote("xar.java-root-bootstrap-phase-quote/v1","APPLICATION",
                    invocation.actual().machineId(),invocation.actual().reviewAt().toString(),invocation.target().getParent().toString(),
                    List.of(prepared.quote()),List.of(),List.of(),"AWAITING_REAL_INDEPENDENT_ISSUER_BINDING");
            prepared.requireCurrent();return RootBootstrapProtocol.encode(quote,RootBootstrapProtocol.FRAME_BYTES-1);
        }
        var receipt=StrictJson.object().put("schema","xar.java-application-configuration-publication/v1")
                .put("machine_id",invocation.actual().machineId()).put("observed_at_utc",clock.instant().toString())
                .put("scope","IMMUTABLE_APPLICATION_FILE_ONLY_NO_CORE_NATIVE_OR_GAME_ADMISSION");
        Published actual=prepared.createNew(invocation.binding());actual.readExact(clock);
        receipt.put("status","CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION");
        receipt.set("original",ControlBuild.strictMapper().valueToTree(actual.original()));
        receipt.set("native_file",ControlBuild.strictMapper().valueToTree(actual.nativeFile()));
        prepared.requireCurrent();return StrictJson.canonical(receipt,65536);
    }
    public static void main(String[] args)throws Exception {
        byte[] output=execute(args,Clock.systemUTC());
        System.out.write(output);System.out.write('\n');System.out.flush();
        if(System.out.checkError())throw new IOException("application publication receipt output failed; preserve the original publication, never retry its write");
    }
}
