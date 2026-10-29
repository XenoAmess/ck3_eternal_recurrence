package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.service.root.RootBootstrapProtocol.FileReply;
import org.xar.ck3.control.service.root.RootBootstrapProtocol.FileReplyChannel;
import org.xar.ck3.control.service.root.RootBootstrapProtocol.Quote;

/** Read-only transport for one actual Command and its retained Prepared objects. No Session is fabricated. */
final class RootBootstrapFileReply {
    private final FileRef channelRef;
    private final FileReplyChannel channel;
    private final SharedSourceFiles.Witness channelOriginal,requestOriginal;
    private final Clock clock;
    private final long startedNanos,maximumWaitNanos;
    private int nextPhase;

    private RootBootstrapFileReply(FileRef channelRef,FileReplyChannel channel,
            SharedSourceFiles.Witness channelOriginal,SharedSourceFiles.Witness requestOriginal,Clock clock) {
        this.channelRef=channelRef;this.channel=channel;this.channelOriginal=channelOriginal;
        this.requestOriginal=requestOriginal;this.clock=clock;
        this.startedNanos=System.nanoTime();
        this.maximumWaitNanos=java.time.Duration.between(clock.instant(),Instant.parse(channel.deadline())).toNanos();
    }
    static RootBootstrapFileReply open(FileRef channelRef,RootProfileBootstrapCommand.Mode mode,
            SharedSourceFiles.Witness requestOriginal,Clock clock)throws IOException {
        Objects.requireNonNull(clock);Objects.requireNonNull(requestOriginal);
        var original=observeExact(channelRef,65536);
        var channel=decode(channelRef,FileReplyChannel.class);
        if(channel.mode()!=mode||!channel.bootstrapRequest().equals(requestOriginal.source()))
            throw new IOException("file reply channel selects another actual Command or exact outer request");
        var available=java.time.Duration.between(clock.instant(),Instant.parse(channel.deadline()));
        if(available.isNegative()||available.isZero()||available.compareTo(java.time.Duration.ofMinutes(30))>0)
            throw new IOException("file reply requires the original finite channel window up to thirty minutes");
        var result=new RootBootstrapFileReply(channelRef,channel,original,requestOriginal,clock);
        result.current(channel.deadline());return result;
    }
    BindingEvidence await(Quote actual,String review)throws IOException,InterruptedException {
        Objects.requireNonNull(actual);current(review);
        var phases=RootBootstrapProtocol.commandPhases(channel.mode());
        if(nextPhase>=phases.size()||!phases.get(nextPhase).equals(actual.phase())
                ||!actual.machineId().equals(channel.machineId())||!actual.reviewAtUtc().equals(review))
            throw new IOException("file reply cannot repeat or reorder this actual Command phase");
        Path asset=Path.of(actual.assetRoot()),replies=Path.of(channel.issuerReplyRoot());
        if(overlap(asset,replies)||Path.of(channelRef.path()).startsWith(asset)
                ||Path.of(requestOriginal.source().path()).startsWith(asset))
            throw new IOException("file reply channel and originals must be outside the actual immutable asset root");
        int index=nextPhase;Path target=replyPath(channel,index);
        while(true){
            current(review);
            if(Files.exists(target,LinkOption.NOFOLLOW_LINKS)){
                // NativeCheckpointFiles publishes a complete hard link before removing its private name.
                // Wait for that narrow finalization; never accept or retain a two-name witness.
                if(SharedSourceFiles.nativeFile(target).linkCount()==1){
                    var replyOriginal=SharedSourceFiles.observe(target);
                    if(replyOriginal.source().bytes()>65536)throw new IOException("file reply envelope exceeds its finite bound");
                    FileReply reply=decode(replyOriginal.source(),FileReply.class);
                    BindingEvidence result=validate(actual,index,reply,replyOriginal,review);
                    result.verify();nextPhase++;return result;
                }
            }
            Thread.sleep(25);
        }
    }
    private BindingEvidence validate(Quote actual,int index,FileReply reply,
            SharedSourceFiles.Witness replyOriginal,String review)throws IOException {
        if(!reply.channel().equals(channelRef)||!reply.bootstrapRequest().equals(requestOriginal.source())
                ||reply.mode()!=channel.mode()||reply.phaseIndex()!=index||!reply.phase().equals(actual.phase())
                ||!reply.deadline().equals(channel.deadline()))
            throw new IOException("file reply differs from the exact outer request/channel/mode/phase/order/deadline");
        if(!Path.of(reply.quote().path()).equals(quotePath(channel,index))
                ||Path.of(reply.binding().path()).startsWith(Path.of(actual.assetRoot())))
            throw new IOException("file reply must retain the fixed actual quote original and external issuer binding");
        var quoteOriginal=observeExact(reply.quote(),RootBootstrapProtocol.FRAME_BYTES);
        if(!quoteOriginal.nativeFile().equals(reply.quoteNativeFile()))
            throw new IOException("actual phase quote Native identity differs from the issuer reply");
        byte[] raw=RootRuntimeDefinitions.read(reply.quote(),RootBootstrapProtocol.FRAME_BYTES);
        var decoded=RootBootstrapProtocol.line(raw,Quote.class);
        if(!Arrays.equals(raw,RootBootstrapProtocol.quoteLine(decoded))
                ||!Arrays.equals(raw,RootBootstrapProtocol.quoteLine(actual)))
            throw new IOException("issuer quote original is not the canonical LF frame emitted by this same Prepared phase");
        var bindingOriginal=observeExact(reply.binding(),channel.mode()==RootProfileBootstrapCommand.Mode.FORMAL_RELEASE
                ?RootBootstrapOutputContract.FORMAL_MAXIMUM_AUTHORITY_BYTES:RootBootstrapOutputContract.MAXIMUM_BYTES);
        current(review);
        return new BindingEvidence(reply.binding(),review,List.of(replyOriginal,quoteOriginal,bindingOriginal));
    }
    final class BindingEvidence {
        private final FileRef binding;
        private final String review;
        private final List<SharedSourceFiles.Witness> originals;
        private BindingEvidence(FileRef binding,String review,List<SharedSourceFiles.Witness> originals){
            this.binding=binding;this.review=review;this.originals=List.copyOf(originals);
        }
        FileRef binding(){return binding;}
        void verify()throws IOException {current(review);for(var original:originals)verifyOriginal(original);}
    }
    private void current(String review)throws IOException {
        Instant deadline=Instant.parse(channel.deadline()),until=Instant.parse(review);
        if(!channel.machineId().equals(WindowsJobProcess.currentMachineId())||!clock.instant().isBefore(deadline)
                ||deadline.isAfter(until)||java.time.Duration.between(clock.instant(),deadline).toMillis()>1800000
                ||maximumWaitNanos<=0||System.nanoTime()-startedNanos>=maximumWaitNanos)
            throw new IOException("file reply actual machine or finite original request/channel deadline expired or drifted");
        verifyOriginal(channelOriginal);verifyOriginal(requestOriginal);
        if(!SharedSourceFiles.nativeDirectory(Path.of(channel.issuerReplyRoot())).equals(channel.issuerReplyDirectory()))
            throw new IOException("file reply original Native directory identity changed");
    }
    static Path replyPath(FileReplyChannel channel,int index){return Path.of(channel.issuerReplyRoot()).resolve("phase-"+index+"-reply.json");}
    static Path quotePath(FileReplyChannel channel,int index){return Path.of(channel.issuerReplyRoot()).resolve("phase-"+index+"-quote.jsonl");}
    static <T>T decode(FileRef ref,Class<T> type)throws IOException {
        try{return RootBootstrapProtocol.decode(RootRuntimeDefinitions.read(ref,65536),65536,type);}
        catch(IllegalArgumentException invalid){throw new IOException("invalid exact typed file reply input",invalid);}
    }
    static SharedSourceFiles.Witness observeExact(FileRef ref,int maximum)throws IOException {
        if(ref==null||ref.bytes()<1||ref.bytes()>maximum)throw new IOException("bounded exact file reply original required");
        var original=SharedSourceFiles.observe(Path.of(ref.path()));
        if(!original.source().equals(ref)||original.nativeFile().linkCount()!=1)
            throw new IOException("file reply exact original or sole native name differs");
        verifyOriginal(original);return original;
    }
    private static void verifyOriginal(SharedSourceFiles.Witness original)throws IOException {
        if(!SharedSourceFiles.nativeFile(Path.of(original.source().path())).equals(original.nativeFile()))
            throw new IOException("file reply original Native identity or allocation drifted");
        SharedSourceFiles.assertUnchanged(original);
    }
    private static boolean overlap(Path left,Path right){return left.startsWith(right)||right.startsWith(left);}
}
