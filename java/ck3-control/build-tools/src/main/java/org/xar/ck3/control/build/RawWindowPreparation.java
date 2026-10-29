package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;

/** Permanent configuration producer. It never opens inputPath or the historical EXE proof. */
public final class RawWindowPreparation {
    public static final String WINDOW_PLAN_SCHEMA="xar.native-raw-window-preparation/v1";
    public static final String LOCATOR_PLAN_SCHEMA="xar.native-exact-locator-preparation/v1";
    public enum Mode { WINDOWS, LOCATOR, ADMISSION }
    private RawWindowPreparation() { }
    public sealed interface Plan permits WindowPlan, LocatorPlan {
        String machineId(); String outputRoot(); CaptureRequest request(SharedSourceFiles.DirectoryIdentity actualIdentity);
    }
    /** Configuration has no directory identity field. Only the actual native producer supplies it. */
    public record WindowPlan(String schema,String machineId,Consumer consumer,String runId,String inputPath,
                             FileRef fullHashEvidenceRef,String outputRoot,List<Window> windows,Amounts windowCaps,
                             long fileIdentityApiBufferCap,int journalMaximumBytes,int bodyMaximumBytes,String reviewAtUtc) implements Plan {
        public WindowPlan {
            require(WINDOW_PLAN_SCHEMA.equals(schema),"exact window preparation schema required");
            machine(machineId);absolute(outputRoot);windows=List.copyOf(windows);
        }
        @Override public Request request(SharedSourceFiles.DirectoryIdentity actualIdentity) {
            return new Request(REQUEST_SCHEMA,machineId,consumer,runId,inputPath,fullHashEvidenceRef,outputRoot,
                    Objects.requireNonNull(actualIdentity),windows,windowCaps,fileIdentityApiBufferCap,journalMaximumBytes,bodyMaximumBytes,reviewAtUtc);
        }
    }
    public record LocatorPlan(String schema,String machineId,Consumer consumer,String runId,String inputPath,
                              FileRef fullHashEvidenceRef,String outputRoot,RawWindowLocatorContract.Locator locator,
                              RawWindowLocatorContract.Segment segment,RawWindowLocatorContract.Targets targets,int chunkBytes,
                              int candidateLimit,long fileIdentityApiBufferCap,int journalMaximumBytes,int bodyMaximumBytes,String reviewAtUtc) implements Plan {
        public LocatorPlan {
            require(LOCATOR_PLAN_SCHEMA.equals(schema),"exact locator preparation schema required");machine(machineId);absolute(outputRoot);
        }
        @Override public RawWindowLocatorContract.Request request(SharedSourceFiles.DirectoryIdentity actualIdentity) {
            return new RawWindowLocatorContract.Request(RawWindowLocatorContract.REQUEST_SCHEMA,machineId,consumer,runId,inputPath,
                    fullHashEvidenceRef,outputRoot,Objects.requireNonNull(actualIdentity),locator,segment,targets,chunkBytes,candidateLimit,
                    fileIdentityApiBufferCap,journalMaximumBytes,bodyMaximumBytes,reviewAtUtc);
        }
    }
    /** A configuration output is not an execution Admission or a claim that the EXE was read. */
    public record Prepared(FileRef encodedRequest,CaptureRequest request) {
        public Prepared {Objects.requireNonNull(encodedRequest);Objects.requireNonNull(request);}
    }
    interface DirectoryPort {
        String machineId()throws IOException;
        SharedSourceFiles.DirectoryIdentity directory(Path path)throws IOException;
    }
    public static Plan decodePlan(Mode mode,byte[] original)throws IOException {
        return switch(mode) {
            case WINDOWS->RawWindowCaptureJson.decode(original,WindowPlan.class,65_536);
            case LOCATOR->RawWindowCaptureJson.decode(original,LocatorPlan.class,65_536);
            case ADMISSION->throw new IOException("Admission is an existing issuer contract, not a capture preparation plan");
        };
    }
    public static Prepared prepare(Plan plan,Path newRequest)throws IOException {
        return prepare(plan,newRequest,new DirectoryPort(){
            public String machineId()throws IOException{return WindowsJobProcess.currentMachineId();}
            public SharedSourceFiles.DirectoryIdentity directory(Path path)throws IOException{return SharedSourceFiles.nativeDirectory(path);}
        });
    }
    static Prepared prepare(Plan plan,Path newRequest,DirectoryPort port)throws IOException {
        Objects.requireNonNull(plan);Objects.requireNonNull(port);newOutput(newRequest);
        if(!plan.machineId().equals(port.machineId()))throw new IOException("actual prepare machine differs from configuration");
        Path root=Path.of(plan.outputRoot());var before=Objects.requireNonNull(port.directory(root),"actual native directory identity required");
        CaptureRequest request=plan.request(before);byte[] encoded=encode(request);
        if(encoded.length>65_536||!request.equals(RawWindowCaptureJson.decodeRequest(encoded)))throw new IOException("qualified capture codec did not roundtrip the typed request");
        if(!before.equals(port.directory(root)))throw new IOException("capture directory identity changed before publication");
        publish(newRequest,encoded);
        if(!before.equals(port.directory(root)))throw new IOException("capture directory changed after publication; retain unadmitted request, do not execute");
        return new Prepared(RawWindowCaptureJson.reference(newRequest,encoded),request);
    }
    /** Mechanical issuer-config encoding only. This does not issue permission or validate a financial grant. */
    public static FileRef prepareAdmission(Admission issuerProvided,Path newAdmission)throws IOException {
        Objects.requireNonNull(issuerProvided);newOutput(newAdmission);
        if(!issuerProvided.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("issuer configuration machine differs from actual prepare machine");
        byte[] encoded=RawWindowCaptureJson.encode(issuerProvided);
        if(encoded.length>65_536||!issuerProvided.equals(RawWindowCaptureJson.decode(encoded,Admission.class,65_536)))throw new IOException("qualified Admission codec did not roundtrip");
        publish(newAdmission,encoded);return RawWindowCaptureJson.reference(newAdmission,encoded);
    }
    public static byte[] encode(CaptureRequest request)throws IOException {
        return switch(request) {
            case Request windows->RawWindowCaptureJson.encode(windows);
            case RawWindowLocatorContract.Request locator->RawWindowCaptureJson.encode(locator);
        };
    }
    private static void newOutput(Path path)throws IOException {
        if(path==null||!path.isAbsolute()||!path.normalize().equals(path)||path.getParent()==null)throw new IOException("new absolute normalized prepared configuration output required");
        SharedSourceFiles.plainAncestors(path.getParent());
        if(!Files.isDirectory(path.getParent(),LinkOption.NOFOLLOW_LINKS)||Files.exists(path,LinkOption.NOFOLLOW_LINKS))throw new IOException("existing ordinary parent and absent CREATE_NEW output required");
    }
    private static void publish(Path path,byte[] encoded)throws IOException {
        try(FileChannel channel=FileChannel.open(path,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)) {
            ByteBuffer bytes=ByteBuffer.wrap(encoded);while(bytes.hasRemaining())channel.write(bytes);channel.force(true);
        }
        var actual=RawWindowCaptureJson.readOriginal(path,65_536);
        if(!Arrays.equals(encoded,actual.bytes()))throw new IOException("prepared configuration exact readback mismatch");
    }
}
