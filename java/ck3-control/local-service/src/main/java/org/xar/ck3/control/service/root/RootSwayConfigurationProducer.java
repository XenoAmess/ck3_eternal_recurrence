package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** First role10 DATA publisher. The shared bootstrap Main owns request IO/dispatch; no separate runner exists. */
public final class RootSwayConfigurationProducer {
    public static final String SCHEMA="xar.java-root-sway-initial-configuration-request/v1";
    public static final int MAXIMUM_BYTES=65536;
    private RootSwayConfigurationProducer() { }
    public record Request(String schema,String machineId,String reviewAtUtc,RootJavaBootstrapInputs.Mode mode,
            FileRef bindingRef,String target,RootSwaySourcesFactory.SourceConfiguration configuration) {
        public Request {
            require(SCHEMA.equals(schema),"exact first Sway configuration request schema required");
            Objects.requireNonNull(configuration);require(configuration.machineId().equals(machineId),"initial Sway request and configuration machine differ");
            var review=instant(reviewAtUtc);require(!review.isAfter(configuration.reviewAt())&&configuration.observedAt().isBefore(review),"initial Sway request must remain inside its original configuration review");
            Objects.requireNonNull(mode);require((mode==RootJavaBootstrapInputs.Mode.QUOTE)==(bindingRef==null),"first Sway CREATE_NEW requires an actual finite binding; QUOTE requires explicit null");
            if(bindingRef!=null){absolute(bindingRef.path());require(bindingRef.bytes()>0&&bindingRef.bytes()<=RootBootstrapOutputContract.MAXIMUM_BYTES&&bindingRef.sha256().matches("[0-9a-f]{64}"),"exact first Sway output binding required");}
            absolute(target);
        }
    }
    public record Published(FileRef original,SharedSourceFiles.NativeFile nativeFile) {
        public Published {Objects.requireNonNull(original);Objects.requireNonNull(nativeFile);}
    }
    public static final class Prepared {
        private final Request request;
        private final byte[] bytes;
        private Prepared(Request request){this.request=request;bytes=RootSwaySourcesFactory.encode(request.configuration());}
        public FileRef expected(){return new FileRef(request.target(),bytes.length,ActionCodec.sha256(bytes));}
        public List<RootBootstrapOutputContract.Output> quote(){return List.of(new RootBootstrapOutputContract.Output(RootBootstrapOutputContract.Kind.SWAY_CONFIGURATION,Path.of(request.target()).getFileName().toString(),bytes.length,ActionCodec.sha256(bytes)));}
        public Published createNew(Clock clock)throws IOException {
            if(request.mode()!=RootJavaBootstrapInputs.Mode.CREATE_NEW)throw new IOException("an initial Sway quote cannot create DATA");
            current(request,clock);
            try(var authority=RootBootstrapOutputGuard.readExact(request.bindingRef(),clock)) {
                var target=Path.of(request.target());authority.requirePlan(target.getParent(),quote(),List.of(),List.of());
                FileRef actual=RootSwaySourcesFactory.publish(request.configuration(),target,authority);
                if(!actual.equals(expected())||authority.accounting().completedOutputs()!=1)throw new IOException("initial Sway publisher changed its priced bytes or output count");
                var identity=SharedSourceFiles.nativeFile(target);authority.requireTargets(List.of(target));current(request,clock);
                return new Published(actual,identity);
            }
        }
    }
    public static Prepared prepare(Request request,Clock clock)throws IOException {current(Objects.requireNonNull(request),clock);return new Prepared(request);}
    public static byte[] encode(Request request) {
        Objects.requireNonNull(request);var row=StrictJson.object();row.put("schema",SCHEMA);row.put("machine_id",request.machineId());row.put("review_at_utc",request.reviewAtUtc());row.put("mode",request.mode().name());
        if(request.bindingRef()==null)row.putNull("binding_ref");else row.set("binding_ref",new ExactRef(request.bindingRef().path(),request.bindingRef().bytes(),request.bindingRef().sha256()).toJson());
        row.put("target",request.target());row.set("configuration",StrictJson.parse(RootSwaySourcesFactory.encode(request.configuration()),RootSwaySourcesFactory.MAXIMUM_BYTES));return StrictJson.canonical(row,MAXIMUM_BYTES);
    }
    public static Request decode(byte[] raw)throws IOException {
        try {
            var row=StrictJson.object(StrictJson.parse(raw,MAXIMUM_BYTES),Set.of("schema","machine_id","review_at_utc","mode","binding_ref","target","configuration"));
            require(row.has("binding_ref"),"initial Sway binding must be explicit, including quote null");
            require(row.get("configuration")!=null&&row.get("configuration").isObject(),"complete typed initial Sway configuration required");
            var binding=row.get("binding_ref").isNull()?null:ExactRef.fromJson(row.get("binding_ref"));
            return new Request(StrictJson.text(row.get("schema")),StrictJson.text(row.get("machine_id")),StrictJson.text(row.get("review_at_utc")),RootJavaBootstrapInputs.Mode.valueOf(StrictJson.text(row.get("mode"))),
                    binding==null?null:new FileRef(binding.path(),binding.bytes(),binding.sha256()),StrictJson.text(row.get("target")),RootSwaySourcesFactory.decode(StrictJson.canonical(row.get("configuration"),RootSwaySourcesFactory.MAXIMUM_BYTES)));
        }catch(IllegalArgumentException invalid){throw new IOException("invalid strict first Sway configuration request",invalid);}
    }
    private static void current(Request request,Clock clock)throws IOException {
        Instant now=Objects.requireNonNull(clock).instant();
        if(!request.machineId().equals(WindowsJobProcess.currentMachineId())||now.isBefore(request.configuration().observedAt())||!now.isBefore(instant(request.reviewAtUtc())))
            throw new IOException("initial Sway configuration request is foreign, not observed yet or expired");
    }
    private static Instant instant(String raw){Instant parsed=Instant.parse(Objects.requireNonNull(raw));require(raw.equals(parsed.toString()),"canonical UTC Sway request review required");return parsed;}
    private static void absolute(String raw){Path path=Path.of(Objects.requireNonNull(raw));require(path.isAbsolute()&&path.normalize().equals(path),"absolute normalized initial Sway path required");}
}
