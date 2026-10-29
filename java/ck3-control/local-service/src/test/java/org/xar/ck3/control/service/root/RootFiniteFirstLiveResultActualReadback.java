package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Arrays;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedOwnedCommand;

/** Actual existing Shared.execute outcome -> original child stdout -> sole Work decoder. No process starts here. */
public final class RootFiniteFirstLiveResultActualReadback {
    private RootFiniteFirstLiveResultActualReadback(){ }
    public static RootFiniteFirstLiveResultReader.Result requireActual(SharedOwnedCommand.Outcome actual,
            FileRef actualRequest,int maximumStdoutBytes)throws IOException {
        return requireRequest(RootFiniteFirstLiveResultReader.consume(actual,maximumStdoutBytes),actualRequest);
    }
    private static RootFiniteFirstLiveResultReader.Result requireRequest(RootFiniteFirstLiveResultReader.Result result,
            FileRef originalRequest)throws IOException {
        var request=RootFiniteFirstLiveRequest.readExact(originalRequest);
        var line=result.report().orElseThrow(()->new IOException("MISSING_NOT_RUN: actual CLI Work report is absent"));
        var report=line.report();
        if(!report.requestId().equals(request.requestId())||!report.machineId().equals(request.machineId()))
            throw new IOException("actual first-live report belongs to another original request");
        if(result.command().child().isEmpty())throw new IOException("MISSING_NOT_RUN: actual CLI child terminal is absent");
        return result;
    }
    /** A readback acceptance entry only. Six exact refs arguments: terminal path/bytes/SHA, original request path/bytes/SHA. */
    public static void main(String... args)throws Exception {
        if(args==null||args.length!=6||args[1]==null||!args[1].matches("[1-9][0-9]{0,6}"))
            throw new IOException("MISSING_NOT_RUN: actual terminal and original finite request references required");
        FileRef terminal=new FileRef(args[0],Long.parseLong(args[1]),args[2]);
        FileRef request=RootFiniteFirstLiveRequest.arguments(Arrays.copyOfRange(args,3,6));
        var result=requireRequest(RootFiniteFirstLiveResultReader.read(terminal,16<<20),request);
        System.out.println("ACTUAL_FIRST_LIVE_READBACK child="+result.mainExitCode().orElseThrow()
                +" outcome="+result.report().orElseThrow().report().outcome()
                +" completed="+result.completedSuccessfully());
        if(!result.completedSuccessfully())throw new IOException("actual first-live did not complete; original child and report retained independently");
    }
}
