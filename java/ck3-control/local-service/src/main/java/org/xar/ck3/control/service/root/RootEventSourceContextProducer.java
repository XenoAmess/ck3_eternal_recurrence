package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrant;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;

/** First immutable source-read configuration. It grants no native frame, captured event or Game authority. */
public final class RootEventSourceContextProducer {
    public static final String SCHEMA="xar.java-root-event-source-context-request/v1";
    public static final int MAXIMUM_REQUEST_BYTES=65536;
    private RootEventSourceContextProducer(){ }

    /** Explicit null evidenceManifestRef means no imported external review evidence in a fresh state.
     * A present manifest is read through the shared codec and every real original remains pinned unchanged. */
    public record Request(String schema,String machineId,String observedAtUtc,String reviewAtUtc,
            RootJavaBootstrapInputs.Mode mode,FileRef bindingRef,String stateRoot,String stockGameRoot,
            FileRef evidenceManifestRef,String target) {
        public Request {
            require(SCHEMA.equals(schema),"exact event context request version required");machine(machineId);
            period(observedAtUtc,reviewAtUtc);Objects.requireNonNull(mode);absolute(stateRoot);absolute(stockGameRoot);absolute(target);
            require((mode==RootJavaBootstrapInputs.Mode.QUOTE)==(bindingRef==null),"event context create-new requires actual binding; quote requires explicit null");
            if(bindingRef!=null)file(bindingRef);if(evidenceManifestRef!=null)file(evidenceManifestRef);
            new EventSourceReadContext(machineId,Path.of(stateRoot),Path.of(stockGameRoot));
            require(!Path.of(target).startsWith(Path.of(stockGameRoot)),"event context output cannot write into stock game inputs");
            if(evidenceManifestRef!=null)require(!Path.of(target).equals(Path.of(evidenceManifestRef.path())),"event context cannot overwrite its original grants manifest");
        }
    }
    public record Created(FileRef original,SharedSourceFiles.NativeFile nativeFile) {
        public Created {Objects.requireNonNull(original);Objects.requireNonNull(nativeFile);}
    }
    public static final class Prepared {
        private final Request request;
        private final EventSourceReadContext context;
        private final TrustedEventSourceContext trusted;
        private final List<SharedSourceFiles.Witness> originals;
        private final byte[] bytes;
        private boolean attempted;
        private Prepared(Request request,EventSourceReadContext context,TrustedEventSourceContext trusted,
                List<SharedSourceFiles.Witness> originals) {
            this.request=request;this.context=context;this.trusted=trusted;this.originals=List.copyOf(originals);
            bytes=RootRuntimeDefinitions.encodeEventSources(context);
        }
        public EventSourceReadContext context(){return context;}
        public byte[] bytes(){return bytes.clone();}
        public FileRef expected(){return new FileRef(Path.of(request.target()).toString(),bytes.length,org.xar.ck3.control.application.driver.DriverJson.sha256(bytes));}
        public List<Output> quote(){var expected=expected();return List.of(new Output(Kind.TRUSTED_EVENT_SOURCE_CONTEXT,
                Path.of(request.target()).getFileName().toString(),expected.bytes(),expected.sha256()));}
        public void requireCurrent(Clock clock)throws IOException {
            current(request,clock);for(var original:originals)SharedSourceFiles.assertUnchanged(original);
            trusted.verifyCurrentRoots();
            for(var grant:context.evidenceGrants())trusted.readDeclared(grant.path(),16<<20,grant.role());
        }
        /** The existing sealed guard is the only file writer. A failed attempt is retained and never retried. */
        public synchronized Created createNew(Clock clock)throws IOException {
            if(request.mode()!=RootJavaBootstrapInputs.Mode.CREATE_NEW)throw new IOException("event context quote cannot create an original");
            if(attempted)throw new IOException("event context publication already attempted; retain possible partial original");
            requireCurrent(clock);Path target=Path.of(request.target());
            try(var authority=RootBootstrapOutputGuard.readExact(request.bindingRef(),clock)){
                authority.requirePlan(target.getParent(),quote(),List.of(),List.of());authority.requireTargets(List.of(target));
                var files=authority.files();if(files.observe(target).isPresent())throw new IOException("event context original already exists");
                requireCurrent(clock);attempted=true;
                var created=files.createNew(target,bytes);files.verify(created);
                byte[] actual=files.read(created,ProjectionEvidenceCodec.MAX_BYTES);
                if(!created.reference().equals(new org.xar.ck3.control.contracts.ExactRef(expected().path(),expected().bytes(),expected().sha256()))
                        ||!Arrays.equals(actual,bytes))throw new IOException("event context physical original differs from its sole codec");
                var decoded=RootRuntimeDefinitions.decodeEventSources(actual);
                if(!decoded.machineId().equals(context.machineId())||!decoded.stateRoot().equals(context.stateRoot())
                        ||!decoded.stockGameRoot().equals(context.stockGameRoot())||!decoded.evidenceGrants().equals(context.evidenceGrants()))
                    throw new IOException("event context physical original roundtrip changed");
                var nativeFile=SharedSourceFiles.nativeFile(target);files.verify(created);requireCurrent(clock);
                if(authority.accounting().completedOutputs()!=1)throw new IOException("event context output inventory differs");
                return new Created(expected(),nativeFile);
            }
        }
    }
    public static Request decode(byte[] original)throws IOException {
        try{StrictJson.parse(original,MAXIMUM_REQUEST_BYTES);return ControlBuild.strictMapper().readValue(original,Request.class);}
        catch(IllegalArgumentException invalid){throw new IOException("invalid strict event context request",invalid);}
    }
    public static byte[] encode(Request request)throws IOException {
        byte[] raw=StrictJson.canonical(ControlBuild.strictMapper().valueToTree(Objects.requireNonNull(request)),MAXIMUM_REQUEST_BYTES);
        require(request.equals(decode(raw)),"event context request codec roundtrip changed");return raw;
    }
    public static Prepared prepare(Request request,Clock clock)throws IOException {
        Objects.requireNonNull(request);current(request,clock);var originals=new ArrayList<SharedSourceFiles.Witness>();
        List<ProjectionEvidenceGrant> grants=request.evidenceManifestRef()==null?List.of():ProjectionEvidenceCodec.decode(read(request.evidenceManifestRef(),ProjectionEvidenceCodec.MAX_BYTES,originals));
        var context=new EventSourceReadContext(request.machineId(),Path.of(request.stateRoot()),Path.of(request.stockGameRoot()),grants);
        var trusted=TrustedEventSourceContext.open(context);
        for(var grant:grants){
            require(grant.bytes()>0&&grant.bytes()<=(16<<20),"nonempty bounded actual granted original required");
            var original=new FileRef(grant.path().toString(),grant.bytes(),grant.sha256());read(original,16<<20,originals);
            trusted.readDeclared(grant.path(),16<<20,grant.role());
        }
        var prepared=new Prepared(request,context,trusted,originals);prepared.requireCurrent(clock);return prepared;
    }
    private static byte[] read(FileRef ref,int maximum,List<SharedSourceFiles.Witness> originals)throws IOException {
        require(ref.bytes()>0&&ref.bytes()<=maximum,"bounded nonempty actual event source original required");
        var witness=SharedSourceFiles.observe(Path.of(ref.path()));
        if(!witness.source().equals(ref))throw new IOException("event source original differs from its exact pin");
        byte[] raw=RootRuntimeDefinitions.read(ref,maximum);SharedSourceFiles.assertUnchanged(witness);originals.add(witness);return raw;
    }
    private static void current(Request request,Clock clock)throws IOException {
        RootRuntimeDefinitions.requireCurrent(request.machineId(),request.observedAtUtc(),request.reviewAtUtc(),WindowsJobProcess.currentMachineId(),Objects.requireNonNull(clock),"event source context request");
    }
}
