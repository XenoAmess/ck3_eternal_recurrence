package org.xar.ck3.control.build;

import java.nio.file.Path;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;

/** MODE absolute-plan.json absolute-new-output.json; emits the same qualified contract bytes, never EXE input. */
public final class RawWindowPrepareMain {
    private RawWindowPrepareMain() { }
    public static void main(String[] args)throws java.io.IOException {
        int exit=0;byte[] output;String machine="unknown";
        try {
            machine=WindowsJobProcess.currentMachineId();
            if(args.length!=3)throw new IllegalArgumentException("WINDOWS|LOCATOR|ADMISSION absolute-config.json absolute-CREATE_NEW-output.json required");
            var mode=RawWindowPreparation.Mode.valueOf(args[0]);
            var original=RawWindowCaptureJson.readOriginal(Path.of(args[1]),65_536);Path target=Path.of(args[2]);
            if(mode==RawWindowPreparation.Mode.ADMISSION) {
                var admission=RawWindowCaptureJson.decode(original.bytes(),Admission.class,65_536);
                RawWindowPreparation.prepareAdmission(admission,target);output=RawWindowCaptureJson.encode(admission);
            }else {
                var prepared=RawWindowPreparation.prepare(RawWindowPreparation.decodePlan(mode,original.bytes()),target);
                output=RawWindowPreparation.encode(prepared.request());
            }
        }catch(java.io.IOException|RuntimeException failure) {
            exit=2;output=RawWindowCaptureJson.encode(new RawWindowCaptureJson.CliFailure(CLI_FAILURE_SCHEMA,machine,java.time.Instant.now().toString(),"PREPARATION_REJECTED_NO_EXECUTION_AUTHORITY",shortError(failure.toString())));
        }
        System.out.write(output);System.out.write('\n');System.out.flush();if(exit!=0)System.exit(exit);
    }
}
