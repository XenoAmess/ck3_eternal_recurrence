package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedCommandOutputReader;
import org.xar.ck3.control.build.SharedOwnedCommand;
import org.xar.ck3.control.contracts.StrictJson;

/** Consumes the existing Shared command terminal; it never starts or retries first-live. */
public final class RootFiniteFirstLiveResultReader {
    private RootFiniteFirstLiveResultReader(){ }
    private static final String REPORT_SCHEMA="xar.java-finite-first-live-result/v1";
    public record ReportLine(RootFiniteFirstLiveWork.DecodedReport report,byte[] originalJson) {
        public ReportLine {Objects.requireNonNull(report);originalJson=Objects.requireNonNull(originalJson).clone();}
        @Override public byte[] originalJson(){return originalJson.clone();}
    }
    public record Result(SharedCommandOutputReader.Readback command,Optional<ReportLine> report) {
        public Result {Objects.requireNonNull(command);Objects.requireNonNull(report);}
        public OptionalInt mainExitCode(){return command.child().isPresent()?OptionalInt.of(command.child().orElseThrow().exitCode()):OptionalInt.empty();}
        public boolean completedSuccessfully(){
            return command.status()==SharedOwnedCommand.Status.PASS
                    &&command.child().map(value->value.passed()).orElse(false)
                    &&report.filter(value->value.report().outcome()==RootFiniteFirstLiveWork.Outcome.COMPLETED
                        &&value.report().exitCode()==0).isPresent();
        }
    }
    public static Result consume(SharedOwnedCommand.Outcome actual,int maximumStdoutBytes)throws IOException {
        return consume(SharedCommandOutputReader.read(actual,maximumStdoutBytes));
    }
    public static Result read(FileRef actualTerminal,int maximumStdoutBytes)throws IOException {
        return consume(SharedCommandOutputReader.read(actualTerminal,maximumStdoutBytes));
    }
    private static Result consume(SharedCommandOutputReader.Readback actual)throws IOException {
        Optional<ReportLine> found=Optional.empty();
        if(actual.stdout().isPresent()) {
            byte[] stdout=actual.stdout().orElseThrow().bytes();int start=0;
            for(int end=0;end<=stdout.length;end++) {
                if(end<stdout.length&&stdout[end]!=10)continue;
                int length=end-start;
                if(length>0&&length<=RootFiniteFirstLiveWork.MAXIMUM_REPORT_BYTES&&stdout[start]==123) {
                    byte[] line=Arrays.copyOfRange(stdout,start,end);
                    com.fasterxml.jackson.databind.JsonNode json=null;
                    try {json=StrictJson.parse(line,RootFiniteFirstLiveWork.MAXIMUM_REPORT_BYTES);}
                    catch(IllegalArgumentException nonJsonLog){ }
                    if(json!=null&&json.isObject()&&json.path("schema").isTextual()
                            &&REPORT_SCHEMA.equals(json.path("schema").textValue())) {
                        if(found.isPresent())throw new IOException("multiple finite first-live report lines in actual stdout");
                        try {found=Optional.of(new ReportLine(RootFiniteFirstLiveWork.decodeReport(line),line));}
                        catch(IllegalArgumentException invalid){throw new IOException("invalid finite first-live report line",invalid);}
                    }
                }
                start=end+1;
            }
        }
        // Work may not exist after an early startup failure. Cleanup failure may also follow Report exit0.
        // Keep the original child exit/stop reason and business outcome independently in all cases.
        return new Result(actual,found);
    }
}
