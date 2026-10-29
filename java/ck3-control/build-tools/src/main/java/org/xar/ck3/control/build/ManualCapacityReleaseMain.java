package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.AttemptCapacityRelease;
import org.xar.ck3.control.build.ControlBuild.Config;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.ManualBuildCapacityReleaseProducer.IssuerDomain;

/** Exact typed issuer adapter only. It never runs Maven, reserves resources or grants issuer delegation. */
public final class ManualCapacityReleaseMain {
    private static final int MAXIMUM_INPUT_BYTES=128<<10;
    private ManualCapacityReleaseMain() {}

    /** CLI: configPath configBytes configSHA releasePath releaseBytes releaseSHA issuerPath issuerBytes issuerSHA. */
    public static void main(String[] args)throws IOException {
        FileRef prepared=prepareArguments(args,Clock.systemUTC());
        // Only the existing pure3 contract is output; Prepared's Instant is not sent to a mapper without JavaTimeModule.
        System.out.write(ControlBuild.strictMapper().writeValueAsBytes(prepared));System.out.write('\n');
    }

    /** All three inputs are original exact pins, not paths implicitly trusted by this adapter. */
    public static FileRef prepare(FileRef configRef,FileRef releaseRef,FileRef issuerRef,Clock clock)throws IOException {
        Objects.requireNonNull(clock);
        Config config=readPinned(configRef,Config.class);
        AttemptCapacityRelease release=readPinned(releaseRef,AttemptCapacityRelease.class);
        IssuerDomain issuer=readPinned(issuerRef,IssuerDomain.class);
        String machine=WindowsJobProcess.currentMachineId();
        if(!machine.equals(release.machineId()))throw new IOException("Capacity issuer inputs do not match the actual machine");
        requireWindow(release,clock.instant());
        var originals=List.of(configRef,releaseRef,issuerRef);
        for(FileRef original:originals)original.verify();
        var prepared=ManualBuildCapacityReleaseProducer.prepare(config,release,clock,issuer);
        Instant checkedAt=clock.instant();requireWindow(release,checkedAt);
        // This is the same production reader, with the actual fresh authority time; no copied validator or private Lease is minted.
        ControlBuild.readLeaseAt(config,machine,checkedAt);
        for(FileRef original:originals)original.verify();prepared.release().verify();
        Instant completedAt=clock.instant();
        if(completedAt.isBefore(checkedAt))throw new IOException("Issuer adapter clock moved backwards");
        requireWindow(release,completedAt);
        return prepared.release();
    }

    static FileRef prepareArguments(String[] args,Clock clock)throws IOException {
        if(args==null||args.length!=9)throw new IOException("Expected exact config, v2 release and issuer reference triples");
        return prepare(reference(args,0),reference(args,3),reference(args,6),clock);
    }

    private static FileRef reference(String[] args,int offset)throws IOException {
        try {
            String number=args[offset+1];
            if(number==null||!number.matches("0|[1-9][0-9]{0,18}"))throw new IllegalArgumentException("Canonical byte count required");
            return new FileRef(args[offset],Long.parseLong(number),args[offset+2]);
        } catch(IllegalArgumentException|NullPointerException failure) {
            throw new IOException("Canonical exact input reference required",failure);
        }
    }

    private static <T> T readPinned(FileRef exact,Class<T> type)throws IOException {
        Objects.requireNonNull(exact);Objects.requireNonNull(type);
        if(exact.bytes()<2||exact.bytes()>MAXIMUM_INPUT_BYTES)throw new IOException("Bounded typed issuer input required");
        Path path=Path.of(exact.path());
        if(!Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS)||!path.toRealPath().equals(path)||Files.size(path)!=exact.bytes())
            throw new IOException("Ordinary exact issuer input required");
        byte[] bytes;
        try(var input=Files.newInputStream(path)){bytes=input.readNBytes(Math.toIntExact(exact.bytes())+1);}
        BoundedSourceInputGuard.verifyReadBytes(exact,bytes,MAXIMUM_INPUT_BYTES);
        if(Files.size(path)!=exact.bytes())throw new IOException("Issuer input size changed during its bounded read");
        exact.verify();
        T decoded=ControlBuild.strictMapper().readValue(bytes,type);
        if(decoded==null)throw new IOException("Typed issuer input cannot be null");
        return decoded;
    }

    private static void requireWindow(AttemptCapacityRelease release,Instant now)throws IOException {
        if(now.isBefore(Instant.parse(release.observedAtUtc()))||!now.isBefore(Instant.parse(release.reviewAtUtc())))
            throw new IOException("Issuer adapter outside the original finite release interval");
    }
}
