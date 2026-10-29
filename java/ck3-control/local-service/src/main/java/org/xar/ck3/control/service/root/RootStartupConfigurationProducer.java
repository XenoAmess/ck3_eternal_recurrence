package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** First startup original from explicit typed fields, through the existing immutable Bootstrap writer.
 * This does not create Core, Native, Game, a seed or canonical ledger state. */
public final class RootStartupConfigurationProducer {
    public static final String SCHEMA="xar.java-root-bootstrap-startup-request/v1";
    public static final int MAXIMUM_REQUEST_BYTES=65536;
    private RootStartupConfigurationProducer(){ }
    public record Request(RootJavaBootstrapInputs.Mode mode,FileRef bindingRef,Path target,RootStartupConfiguration startup) {
        public Request {
            Objects.requireNonNull(mode);Objects.requireNonNull(target);Objects.requireNonNull(startup);
            StrictJson.require(target.isAbsolute()&&target.normalize().equals(target)&&target.getParent()!=null,
                    "absolute normalized startup publication path required");
            StrictJson.require((mode==RootJavaBootstrapInputs.Mode.QUOTE)==(bindingRef==null),
                    "startup creation requires its actual immutable binding; quote requires explicit null");
            if(bindingRef!=null)RootBootstrapOutputContract.file(bindingRef);
        }
    }
    public static final class Prepared {
        private final Request request;
        private final Clock clock;
        private final byte[] bytes;
        private final SharedSourceFiles.DirectoryIdentity parent;
        private final List<SharedSourceFiles.Witness> originals;
        private boolean attempted;
        private Prepared(Request request,Clock clock,SharedSourceFiles.DirectoryIdentity parent,
                List<SharedSourceFiles.Witness> originals) {
            this.request=request;this.clock=clock;this.parent=parent;this.originals=List.copyOf(originals);
            bytes=StrictJson.canonical(request.startup().toJson(),RootStartupConfiguration.MAXIMUM_BYTES);
        }
        public FileRef expected(){return new FileRef(request.target().toString(),bytes.length,
                org.xar.ck3.control.application.driver.DriverJson.sha256(bytes));}
        public RootBootstrapOutputContract.Output quote()throws IOException {
            requireCurrent();var ref=expected();return new RootBootstrapOutputContract.Output(RootBootstrapOutputContract.Kind.STARTUP,
                    request.target().getFileName().toString(),ref.bytes(),ref.sha256());
        }
        public void requireCurrent()throws IOException {
            request.startup().requireCurrent(clock);
            if(!parent.equals(SharedSourceFiles.nativeDirectory(request.target().getParent())))
                throw new IOException("startup publication parent changed");
            for(var original:originals)unchanged(original);
        }
        public synchronized Published createNew()throws IOException {
            if(request.mode()!=RootJavaBootstrapInputs.Mode.CREATE_NEW)throw new IOException("startup quote cannot create an original");
            if(attempted)throw new IOException("startup publication already attempted; preserve its original result without replay");
            var output=quote();
            try(var authority=RootBootstrapOutputGuard.readExact(request.bindingRef(),clock)){
                authority.requirePlan(request.target().getParent(),List.of(output),List.of(),List.of());
                authority.requireTargets(List.of(request.target()));requireCurrent();
                var files=authority.files();attempted=true;var actual=files.createNew(request.target(),bytes);files.verify(actual);
                if(!actual.reference().equals(exact(expected()))||!Arrays.equals(bytes,files.read(actual,RootStartupConfiguration.MAXIMUM_BYTES)))
                    throw new IOException("startup original differs from its sole typed representation");
                var witness=SharedSourceFiles.observe(request.target());
                if(!witness.source().equals(expected()))throw new IOException("startup publication original changed");
                var decoded=RootStartupConfiguration.readExact(expected());decoded.requireCurrent(clock);
                if(!decoded.equals(request.startup()))throw new IOException("actual startup reader changed the published typed fields");
                unchanged(witness);requireCurrent();files.verify(actual);authority.requireTargets(List.of(request.target()));
                if(files!=authority.files()||authority.accounting().completedOutputs()!=1)
                    throw new IOException("startup publication did not complete its exact priced output");
                return new Published(request.startup(),witness,originals);
            }
        }
    }
    public static final class Published {
        private final RootStartupConfiguration startup;
        private final SharedSourceFiles.Witness original;
        private final List<SharedSourceFiles.Witness> inputs;
        private Published(RootStartupConfiguration startup,SharedSourceFiles.Witness original,List<SharedSourceFiles.Witness> inputs){
            this.startup=startup;this.original=original;this.inputs=List.copyOf(inputs);
        }
        public FileRef original(){return original.source();}
        public SharedSourceFiles.NativeFile nativeFile(){return original.nativeFile();}
        public RootStartupConfiguration readExact(Clock clock)throws IOException {
            unchanged(original);for(var input:inputs)unchanged(input);
            var decoded=RootStartupConfiguration.readExact(original());decoded.requireCurrent(Objects.requireNonNull(clock));
            if(!decoded.equals(startup))throw new IOException("published startup fields changed");
            return decoded;
        }
    }
    public static Prepared prepare(Request request,Clock clock)throws IOException {
        Objects.requireNonNull(request);Objects.requireNonNull(clock);request.startup().requireCurrent(clock);
        if(Files.exists(request.target(),LinkOption.NOFOLLOW_LINKS))throw new IOException("immutable startup target already exists");
        SharedSourceFiles.plainAncestors(request.target());
        var witnesses=new ArrayList<SharedSourceFiles.Witness>();
        var source=request.startup().source().sourceRef();
        for(FileRef ref:List.of(request.startup().application(),request.startup().runtimeDefinitions(),
                new FileRef(source.path(),source.bytes(),source.sha256()))){
            if(request.target().equals(Path.of(ref.path())))throw new IOException("startup cannot replace an input original");
            var witness=SharedSourceFiles.observe(Path.of(ref.path()));
            if(!witness.source().equals(ref))throw new IOException("startup input original differs from its explicit reference");
            unchanged(witness);witnesses.add(witness);
        }
        var prepared=new Prepared(request,clock,SharedSourceFiles.nativeDirectory(request.target().getParent()),witnesses);
        prepared.requireCurrent();return prepared;
    }
    public static byte[] encode(Request request){
        var row=StrictJson.object();row.put("schema",SCHEMA);row.put("mode",request.mode().name());
        if(request.bindingRef()==null)row.putNull("binding_ref");else row.set("binding_ref",exact(request.bindingRef()).toJson());
        row.put("target",request.target().toString());row.set("startup",request.startup().toJson());
        return StrictJson.canonical(row,MAXIMUM_REQUEST_BYTES);
    }
    public static Request decode(byte[] bytes){
        var row=StrictJson.object(StrictJson.parse(bytes,MAXIMUM_REQUEST_BYTES),Set.of("schema","mode","binding_ref","target","startup"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact first startup publication schema required");
        FileRef binding=null;
        if(!row.get("binding_ref").isNull()){var ref=ExactRef.fromJson(row.get("binding_ref"));binding=new FileRef(ref.path(),ref.bytes(),ref.sha256());}
        return new Request(RootJavaBootstrapInputs.Mode.valueOf(StrictJson.text(row.get("mode"))),binding,
                Path.of(StrictJson.text(row.get("target"))),RootStartupConfiguration.fromJson(row.get("startup")));
    }
    private static ExactRef exact(FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static void unchanged(SharedSourceFiles.Witness witness)throws IOException {
        if(!SharedSourceFiles.nativeFile(Path.of(witness.source().path())).equals(witness.nativeFile()))
            throw new IOException("startup source native file identity changed");
        SharedSourceFiles.assertUnchanged(witness);
    }
}
