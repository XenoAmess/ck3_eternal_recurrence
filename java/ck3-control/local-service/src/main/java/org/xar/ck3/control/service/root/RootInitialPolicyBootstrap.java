package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;

/** Typed noninteractive adapter for the existing initial-policy producer and CREATE_NEW guard. */
public final class RootInitialPolicyBootstrap {
    public static final String SCHEMA="xar.java-root-bootstrap-initial-policy-request/v1";
    public static final int MAXIMUM_REQUEST_BYTES=65536;
    private RootInitialPolicyBootstrap(){ }

    /** Both lifecycle and fresh-pact choice are supplied explicitly and checked against the actual ENV. */
    public record Request(String schema,String machineId,String observedAtUtc,String reviewAtUtc,
            RootJavaBootstrapInputs.Mode mode,FileRef bindingRef,FileRef actualEnvironment,
            InitialEpisodePolicy.Lifecycle lifecycle,InitialEpisodePolicy.FreshPact fresh,String target) {
        public Request {
            require(SCHEMA.equals(schema),"exact initial policy bootstrap request version required");
            machine(machineId);period(observedAtUtc,reviewAtUtc);Objects.requireNonNull(mode);
            require((mode==RootJavaBootstrapInputs.Mode.QUOTE)==(bindingRef==null),
                    "initial policy create-new requires actual binding; quote requires explicit null");
            if(bindingRef!=null)file(bindingRef);file(actualEnvironment);absolute(target);
            Objects.requireNonNull(lifecycle);Objects.requireNonNull(fresh);
        }
    }
    public static final class Prepared {
        private final Request request;
        private final RootProfileBootstrapInputs.Prepared original;
        private Prepared(Request request,RootProfileBootstrapInputs.Prepared original){this.request=request;this.original=original;}
        public List<Output> quote(){return original.quote();}
        public FileRef expected(){
            Output output=quote().getFirst();
            return new FileRef(Path.of(request.target()).toString(),output.bytes(),output.sha256());
        }
        /** The identical staged producer retains ENV custody; the sealed guard owns all physical writes. */
        public RootProfileBootstrapInputs.Created createNew(Clock clock)throws IOException {
            if(request.mode()!=RootJavaBootstrapInputs.Mode.CREATE_NEW)throw new IOException("initial policy quote cannot create an original");
            current(request,clock);
            try(var authority=RootBootstrapOutputGuard.readExact(request.bindingRef(),clock)){
                var created=original.createNew(authority);
                if(created.size()!=1||created.getFirst().kind()!=Kind.INITIAL_POLICY||authority.accounting().completedOutputs()!=1)
                    throw new IOException("initial policy publisher did not complete its sole declared output");
                var output=created.getFirst();
                var accepted=InitialEpisodePolicy.readExact(output.exact(),request.actualEnvironment());accepted.verify();
                if(accepted.kind()!=request.lifecycle()||!output.original().equals(expected()))
                    throw new IOException("initial policy actual reader differs from its explicit source selection");
                current(request,clock);return output;
            }
        }
    }
    public static Request decode(byte[] raw)throws IOException {
        try{StrictJson.parse(raw,MAXIMUM_REQUEST_BYTES);return ControlBuild.strictMapper().readValue(raw,Request.class);}
        catch(IllegalArgumentException invalid){throw new IOException("invalid strict initial policy request",invalid);}
    }
    public static byte[] encode(Request request)throws IOException {
        byte[] raw=StrictJson.canonical(ControlBuild.strictMapper().valueToTree(Objects.requireNonNull(request)),MAXIMUM_REQUEST_BYTES);
        require(request.equals(decode(raw)),"initial policy request codec roundtrip changed");return raw;
    }
    public static Prepared prepare(Request request,Clock clock)throws IOException {
        Objects.requireNonNull(request);current(request,clock);
        var original=RootProfileBootstrapInputs.initialPolicy(request.actualEnvironment(),request.lifecycle(),request.fresh(),Path.of(request.target()));
        return new Prepared(request,original);
    }
    private static void current(Request request,Clock clock)throws IOException {
        RootRuntimeDefinitions.requireCurrent(request.machineId(),request.observedAtUtc(),request.reviewAtUtc(),
                WindowsJobProcess.currentMachineId(),Objects.requireNonNull(clock),"initial policy bootstrap request");
    }
}
