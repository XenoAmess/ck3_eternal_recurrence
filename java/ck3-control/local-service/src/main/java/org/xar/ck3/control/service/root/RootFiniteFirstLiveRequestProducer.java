package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;

/** First publication of the finite caller's explicit data through the existing immutable bootstrap authority.
 * It selects an actual startup original. It creates no Game, writer, admission or saved state. */
public final class RootFiniteFirstLiveRequestProducer {
    public static final String SCHEMA="xar.java-root-bootstrap-finite-first-live-request/v1";
    public static final int MAXIMUM_BYTES=32768;
    private RootFiniteFirstLiveRequestProducer(){ }

    public record Request(RootJavaBootstrapInputs.Mode mode,FileRef bindingRef,Path target,
            RootFiniteFirstLiveRequest finite) {
        public Request {
            Objects.requireNonNull(mode);Objects.requireNonNull(target);Objects.requireNonNull(finite);
            StrictJson.require(target.isAbsolute()&&target.normalize().equals(target),"normalized absolute finite request target required");
            StrictJson.require((mode==RootJavaBootstrapInputs.Mode.QUOTE)==(bindingRef==null),
                    "finite input creation requires its actual binding; quote requires explicit null");
            if(bindingRef!=null)RootBootstrapOutputContract.file(bindingRef);
            StrictJson.require(!target.equals(Path.of(finite.startup().startup().path())),"finite request cannot overwrite startup");
        }
    }
    public record Created(FileRef original,SharedSourceFiles.NativeFile nativeFile) {
        public Created {Objects.requireNonNull(original);Objects.requireNonNull(nativeFile);}
    }
    public static final class Prepared {
        private final Request request;
        private final byte[] bytes;
        private final SharedSourceFiles.Witness startup;
        private Prepared(Request request,SharedSourceFiles.Witness startup){
            this.request=request;this.startup=startup;bytes=request.finite().encode();
        }
        public FileRef expected(){return new FileRef(request.target().toString(),bytes.length,
                org.xar.ck3.control.application.driver.DriverJson.sha256(bytes));}
        public List<Output> quote(){var exact=expected();return List.of(new Output(Kind.FINITE_FIRST_LIVE_REQUEST,
                request.target().getFileName().toString(),exact.bytes(),exact.sha256()));}
        public Created createNew(Clock clock)throws IOException {
            if(request.mode()!=RootJavaBootstrapInputs.Mode.CREATE_NEW)throw new IOException("finite request quote cannot create an original");
            current(clock);
            try(var authority=RootBootstrapOutputGuard.readExact(request.bindingRef(),clock)){
                authority.requirePlan(request.target().getParent(),quote(),List.of(),List.of());
                var files=authority.files();var actual=files.createNew(request.target(),bytes);files.verify(actual);
                if(!actual.reference().equals(exact(expected()))||!Arrays.equals(bytes,files.read(actual,RootFiniteFirstLiveRequest.MAXIMUM_BYTES)))
                    throw new IOException("finite request original differs from its actual typed producer");
                var nativeFile=SharedSourceFiles.nativeFile(request.target());files.verify(actual);current(clock);
                if(authority.accounting().completedOutputs()!=1)throw new IOException("finite request output inventory is incomplete");
                return new Created(expected(),nativeFile);
            }
        }
        private void current(Clock clock)throws IOException {
            SharedSourceFiles.assertUnchanged(startup);request.finite().requireCurrent(Objects.requireNonNull(clock));
        }
    }
    public static Prepared prepare(Request request,Clock clock)throws IOException {
        Objects.requireNonNull(request);request.finite().requireCurrent(Objects.requireNonNull(clock));
        var startup=SharedSourceFiles.observe(Path.of(request.finite().startup().startup().path()));
        if(!startup.source().equals(request.finite().startup().startup()))throw new IOException("finite input startup differs from its selected original");
        request.finite().requireCurrent(clock);SharedSourceFiles.assertUnchanged(startup);return new Prepared(request,startup);
    }
    public static byte[] encode(Request request){
        Objects.requireNonNull(request);var row=StrictJson.object();row.put("schema",SCHEMA);row.put("mode",request.mode().name());
        if(request.bindingRef()==null)row.putNull("binding_ref");else row.set("binding_ref",exact(request.bindingRef()).toJson());
        row.put("target",request.target().toString());row.set("finite_request",StrictJson.parse(request.finite().encode(),RootFiniteFirstLiveRequest.MAXIMUM_BYTES));
        return StrictJson.canonical(row,MAXIMUM_BYTES);
    }
    public static Request decode(byte[] bytes){
        var row=StrictJson.object(StrictJson.parse(bytes,MAXIMUM_BYTES),Set.of("schema","mode","binding_ref","target","finite_request"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact finite input publisher request required");
        FileRef binding=row.get("binding_ref").isNull()?null:file(ExactRef.fromJson(row.get("binding_ref")));
        return new Request(RootJavaBootstrapInputs.Mode.valueOf(StrictJson.text(row.get("mode"))),binding,
                Path.of(StrictJson.text(row.get("target"))),RootFiniteFirstLiveRequest.decode(
                        StrictJson.canonical(row.get("finite_request"),RootFiniteFirstLiveRequest.MAXIMUM_BYTES)));
    }
    private static ExactRef exact(FileRef value){return new ExactRef(value.path(),value.bytes(),value.sha256());}
    private static FileRef file(ExactRef value){return new FileRef(value.path(),value.bytes(),value.sha256());}
}
