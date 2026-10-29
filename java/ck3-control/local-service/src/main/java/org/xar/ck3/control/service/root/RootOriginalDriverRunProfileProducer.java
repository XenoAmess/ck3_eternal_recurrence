package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.StringValue;

/** First publication of explicit run configuration through the existing bootstrap Body writer.
 * Preparation produces bytes only. The created file remains DATA until readExact binds the real launch plan. */
public final class RootOriginalDriverRunProfileProducer {
    public static final String SCHEMA="xar.java-original-driver-run-profile-producer-request/v1";
    public static final int MAXIMUM_REQUEST_BYTES=RootFrozenRunProfile.MAXIMUM_REQUEST_BYTES+256;
    private static final int MAXIMUM_ENVIRONMENT_BYTES=1<<20;
    private RootOriginalDriverRunProfileProducer(){ }

    /** Explicit configuration, including its already existing environment original; never a Game observation. */
    public record Request(RootFrozenRunProfile.Request profile) {
        public Request {Objects.requireNonNull(profile);}
    }

    /** The nested profile has one codec, shared with its actual ORIGINAL_DRIVER_RUN_PROFILE consumer. */
    public static byte[] encode(Request request) {
        Objects.requireNonNull(request);
        return OriginalDriverJournal.canonical(new ObjectValue(Map.of(
                "schema",new StringValue(SCHEMA),
                "profile",OriginalDriverJournal.parse(RootFrozenRunProfile.encode(request.profile()),
                        RootFrozenRunProfile.MAXIMUM_REQUEST_BYTES))),MAXIMUM_REQUEST_BYTES).bytes();
    }

    public static Request decode(byte[] bytes) {
        var parsed=OriginalDriverJournal.parse(Objects.requireNonNull(bytes),MAXIMUM_REQUEST_BYTES);
        if(!(parsed instanceof ObjectValue root)||!root.fields().keySet().equals(Set.of("schema","profile"))
                ||!(root.get("schema") instanceof StringValue schema)||!SCHEMA.equals(schema.value()))
            throw new IllegalArgumentException("exact versioned run-profile producer request required");
        byte[] profile=OriginalDriverJournal.canonical(root.get("profile"),RootFrozenRunProfile.MAXIMUM_REQUEST_BYTES).bytes();
        return new Request(RootFrozenRunProfile.decode(profile));
    }

    public static Request readRequest(FileRef original)throws IOException {
        try{return decode(RootRuntimeDefinitions.read(Objects.requireNonNull(original),MAXIMUM_REQUEST_BYTES));}
        catch(IllegalArgumentException invalid){throw new IOException("actual run-profile producer request is invalid",invalid);}
    }

    /** No file is created here. Only RootProfileBootstrapInputs' existing guarded Body writer publishes these bytes. */
    public static Prepared prepare(FileRef originalRequest,Path target,Clock clock)throws IOException {
        Objects.requireNonNull(originalRequest);Objects.requireNonNull(clock);absolute(target);
        var requestWitness=SharedSourceFiles.observe(Path.of(originalRequest.path()));
        requireSame(requestWitness.source(),originalRequest);
        Request request=readRequest(originalRequest);
        ExactRef environment=request.profile().environmentManifest();
        FileRef environmentRef=new FileRef(environment.path(),environment.bytes(),environment.sha256());
        var environmentWitness=SharedSourceFiles.observe(Path.of(environment.path()));
        requireSame(environmentWitness.source(),environmentRef);
        RootRuntimeDefinitions.read(environmentRef,MAXIMUM_ENVIRONMENT_BYTES);
        Prepared prepared=new Prepared(target,request.profile(),RootFrozenRunProfile.encode(request.profile()),
                List.of(requestWitness,environmentWitness),clock);
        prepared.verifyOriginals();return prepared;
    }

    /** Privately issued preparation, with no output FileRef, storage permit, launch plan, or FrozenRunProfile authority. */
    public static final class Prepared {
        private final Path target;
        private final RootFrozenRunProfile.Request profile;
        private final byte[] bytes;
        private final List<SharedSourceFiles.Witness> originals;
        private final Clock clock;
        private Prepared(Path target,RootFrozenRunProfile.Request profile,byte[] bytes,
                List<SharedSourceFiles.Witness> originals,Clock clock) {
            this.target=target;this.profile=profile;this.bytes=bytes.clone();this.originals=List.copyOf(originals);this.clock=clock;
        }
        public Path target(){return target;}
        public byte[] bytes(){return bytes.clone();}
        public void verifyOriginals()throws IOException {
            RootRuntimeDefinitions.requireCurrent(profile.machineId(),profile.observedAt().toString(),profile.reviewAt().toString(),
                    WindowsJobProcess.currentMachineId(),clock,"original Driver run-profile configuration");
            for(var original:originals)SharedSourceFiles.assertUnchanged(original);
        }
        /** Called after the existing CREATE_NEW writer and its own readback; does not perform a write. */
        public void verifyCreated()throws IOException {
            verifyOriginals();
            FileRef expected=new FileRef(target.toString(),bytes.length,OriginalDriverJournal.sha256(bytes));
            byte[] actual=RootRuntimeDefinitions.read(expected,RootFrozenRunProfile.MAXIMUM_REQUEST_BYTES);
            if(!Arrays.equals(bytes,actual)||!RootFrozenRunProfile.decode(actual).equals(profile))
                throw new IOException("created original Driver run profile differs from the prepared configuration");
            verifyOriginals();
        }
    }

    private static void absolute(Path path) {
        if(path==null||!path.isAbsolute()||!path.normalize().equals(path))
            throw new IllegalArgumentException("absolute normalized run-profile output path required");
    }
    private static void requireSame(FileRef actual,FileRef expected)throws IOException {
        if(!Path.of(actual.path()).equals(Path.of(expected.path()))||actual.bytes()!=expected.bytes()
                ||!actual.sha256().equals(expected.sha256()))
            throw new IOException("run-profile input differs from its exact original reference");
    }
}
