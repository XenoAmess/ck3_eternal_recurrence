package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.service.OrdinarySessionHost;
import org.xar.ck3.control.service.mcp.PublicMcpHost;

/** Actual Saved exact-six-argument Main adapter. Test data selects originals, never an issuer or authority. */
public final class RootStartupLegacyActualInputs {
    public static final String INPUTS_PREFIX="XAR_ROOT_LEGACY_INPUTS_REQUEST";
    public static final String SAVED_PREFIX="XAR_ROOT_LEGACY_SAVED_ROUTE";
    public record Request(RootStartupInputsProducer.Request inputs,FileRef savedRoute) {
        public Request {
            Objects.requireNonNull(inputs);Objects.requireNonNull(savedRoute);
            requireReference(savedRoute,65536,"actual Saved route");
        }
    }
    private RootStartupLegacyActualInputs() { }
    private static void requireReference(FileRef ref,long maximum,String role) {
        Path path=Path.of(ref.path());
        if(!path.isAbsolute()||!path.normalize().equals(path)||ref.bytes()<1||ref.bytes()>maximum
                ||!ref.sha256().matches("[0-9a-f]{64}"))throw new IllegalArgumentException("exact bounded "+role+" reference required");
    }
    private static FileRef reference(Map<String,String> environment,String prefix,long maximum)throws IOException {
        String path=environment.get(prefix),bytes=environment.get(prefix+"_BYTES"),sha=environment.get(prefix+"_SHA256");
        if(path==null||bytes==null||sha==null||!bytes.matches("[1-9][0-9]{0,7}")||!sha.matches("[0-9a-f]{64}"))
            throw new IOException("MISSING_ACTUAL_LEGACY_MAIN_INPUTS_NOT_RUN: "+prefix+" path/bytes/SHA required");
        try {
            var actual=new FileRef(path,Long.parseLong(bytes),sha);requireReference(actual,maximum,prefix);return actual;
        }catch(IllegalArgumentException invalid){throw new IOException("invalid actual Legacy Main source reference: "+prefix,invalid);}
    }
    public static Request fromEnvironment(Map<String,String> environment)throws IOException {
        Objects.requireNonNull(environment);
        var inputs=RootStartupInputsProducer.readExact(reference(environment,INPUTS_PREFIX,RootStartupInputsProducer.MAXIMUM_BYTES));
        return new Request(inputs,reference(environment,SAVED_PREFIX,65536));
    }
    public static void executeFromEnvironment(RootStartupInputsProducer.Work work)throws Exception {
        execute(fromEnvironment(System.getenv()),new OrdinarySessionHost(),new PublicMcpHost(),work);
    }
    public static void execute(Request request,OrdinarySessionHost host,PublicMcpHost publicHost,
            RootStartupInputsProducer.Work work)throws Exception {
        Objects.requireNonNull(request);Objects.requireNonNull(host);Objects.requireNonNull(publicHost);Objects.requireNonNull(work);
        var startup=RootStartupConfiguration.readExact(request.inputs().startup());startup.requireCurrent(Clock.systemUTC());
        if(host.current().isPresent()||publicHost.current().isPresent())
            throw new IOException("actual Legacy Main fixture cannot replace an installed host");
        var main=new RootApplicationMain();main.ordinaryHost=host;main.publicHost=publicHost;
        var source=request.inputs().startup();var saved=request.savedRoute();boolean[] entered={false};
        int exit=main.runWithAdmitted(actual->{
            if(entered[0])throw new IOException("actual Saved Main delivered its lifetime twice");entered[0]=true;
            if(actual.host()!=host||actual.original()!=actual.core().sessionAccess().current()
                    ||!actual.privateInputs().configuration().applicationRef().equals(startup.application()))
                throw new IOException("actual Saved Main input crossed its original host/Core/startup");
            // Main constructed Actual only after SavedCoordinator -> Core's held writer adoption -> full readiness.
            work.consume(actual);
        },source.path(),Long.toString(source.bytes()),source.sha256(),
                saved.path(),Long.toString(saved.bytes()),saved.sha256());
        if(exit!=0||!entered[0])throw new IOException("actual Saved Main did not deliver admitted original inputs; terminal="+exit);
    }
}
