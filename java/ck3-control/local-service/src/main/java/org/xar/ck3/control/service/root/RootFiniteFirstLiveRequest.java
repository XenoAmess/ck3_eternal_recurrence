package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Finite acceptance data selecting original startup inputs; never a Game, saved pair or restore authority.
 * stepTimeout bounds independent read/RESTORE steps. The complete original startup batch retains its
 * own BatchLimits wall time and the original native plan lifetime; this request does not truncate it.
 */
public record RootFiniteFirstLiveRequest(String requestId,String machineId,Instant observedAt,Instant reviewAt,
        RootStartupInputsProducer.Request startup,int minimumForwardSavedDays,Duration stepTimeout) {
    public static final String SCHEMA="xar.java-root-finite-first-live-request/v1";
    public static final int MAXIMUM_BYTES=16384;
    public RootFiniteFirstLiveRequest {
        StrictJson.require(requestId!=null&&requestId.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}"),
                "bounded finite run request identity required");
        StrictJson.require(machineId!=null&&machineId.matches("[a-z0-9][a-z0-9-]{0,63}")&&!machineId.equals("unknown"),
                "explicit finite run machine required");
        Objects.requireNonNull(observedAt);Objects.requireNonNull(reviewAt);Objects.requireNonNull(startup);
        Objects.requireNonNull(stepTimeout);
        StrictJson.require(observedAt.isBefore(reviewAt),"finite run observation must precede review");
        StrictJson.require(minimumForwardSavedDays>=1&&minimumForwardSavedDays<=36500,
                "finite positive saved forward-day requirement required");
        StrictJson.require(!stepTimeout.isNegative()&&!stepTimeout.isZero()
                &&stepTimeout.getNano()%1_000_000==0&&stepTimeout.compareTo(Duration.ofMinutes(30))<=0,
                "finite whole-millisecond step timeout within thirty minutes required");
    }
    public void requireCurrent(Clock clock)throws IOException {
        Objects.requireNonNull(clock);var now=clock.instant();
        if(!machineId.equals(WindowsJobProcess.currentMachineId())||now.isBefore(observedAt)||!now.isBefore(reviewAt))
            throw new IOException("finite first-live request requires its actual machine and current review");
        var original=RootStartupConfiguration.readExact(startup.startup());original.requireCurrent(clock);
        if(!machineId.equals(original.machineId())||reviewAt.isAfter(original.reviewAt())||original.batches().size()!=1)
            throw new IOException("finite caller requires this same machine, one original batch and bounded startup review");
    }
    public byte[] encode() {
        var row=StrictJson.object();row.put("schema",SCHEMA);row.put("request_id",requestId);row.put("machine_id",machineId);
        row.put("observed_at_utc",observedAt.toString());row.put("review_at_utc",reviewAt.toString());
        row.set("startup_inputs",StrictJson.parse(RootStartupInputsProducer.encode(startup),RootStartupInputsProducer.MAXIMUM_BYTES));
        row.put("minimum_forward_saved_days",minimumForwardSavedDays);row.put("step_timeout_ms",stepTimeout.toMillis());
        return StrictJson.canonical(row,MAXIMUM_BYTES);
    }
    public static RootFiniteFirstLiveRequest decode(byte[] bytes) {
        var row=StrictJson.object(StrictJson.parse(Objects.requireNonNull(bytes),MAXIMUM_BYTES),
                Set.of("schema","request_id","machine_id","observed_at_utc","review_at_utc","startup_inputs",
                        "minimum_forward_saved_days","step_timeout_ms"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact finite first-live request schema required");
        return new RootFiniteFirstLiveRequest(StrictJson.text(row.get("request_id")),StrictJson.text(row.get("machine_id")),
                canonicalInstant(StrictJson.text(row.get("observed_at_utc"))),canonicalInstant(StrictJson.text(row.get("review_at_utc"))),
                RootStartupInputsProducer.decode(StrictJson.canonical(row.get("startup_inputs"),RootStartupInputsProducer.MAXIMUM_BYTES)),
                (int)StrictJson.integer(row.get("minimum_forward_saved_days"),1,36500),
                Duration.ofMillis(StrictJson.integer(row.get("step_timeout_ms"),1,1800000)));
    }
    private static Instant canonicalInstant(String text) {
        var value=Instant.parse(text);StrictJson.require(value.toString().equals(text),"canonical UTC request instant required");return value;
    }
    public static RootFiniteFirstLiveRequest readExact(FileRef original)throws IOException {
        Objects.requireNonNull(original);
        if(original.bytes()<1||original.bytes()>MAXIMUM_BYTES)throw new IOException("bounded exact finite first-live request required");
        try{return decode(RootRuntimeDefinitions.read(original,MAXIMUM_BYTES));}
        catch(IllegalArgumentException|java.time.DateTimeException invalid){throw new IOException("invalid finite first-live request",invalid);}
    }
    /** Three exact request arguments; measuring a newly selected path is not authorization. */
    public static FileRef arguments(String... args)throws IOException {
        if(args==null||args.length!=3||args[0]==null||args[1]==null||args[2]==null
                ||!args[1].matches("[1-9][0-9]{0,4}")||!args[2].matches("[0-9a-f]{64}"))
            throw new IOException("MISSING_FINITE_FIRST_LIVE_INPUTS: exact request path/bytes/SHA required");
        try {
            var path=Path.of(args[0]);long bytes=Long.parseLong(args[1]);
            if(!path.isAbsolute()||!path.normalize().equals(path)||bytes>MAXIMUM_BYTES)
                throw new IllegalArgumentException("normalized absolute bounded request reference required");
            return new FileRef(args[0],bytes,args[2]);
        }catch(IllegalArgumentException invalid){throw new IOException("invalid finite first-live request reference",invalid);}
    }
}
