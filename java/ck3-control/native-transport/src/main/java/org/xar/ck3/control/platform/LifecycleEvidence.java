package org.xar.ck3.control.platform;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameLifecycle;

/** Finite immutable evidence rows. Inner terminal/accounting is retained before interpreting success. */
final class LifecycleEvidence {
    enum Event { INTENT, SUSPENDED, INJECTOR_EXIT, HELLO, RUNNING, EXITED, STOP_REQUESTED, STOPPED, UNAVAILABLE }
    private sealed interface EvidenceRow permits Row,InventoryRow { }
    record Row(String schema,String machineId,String observedAtUtc,String requestId,String sessionId,
            Event event,WindowsJobProcess.ProcessIdentity game,WindowsJobProcess.Accounting accounting,
            WindowsJobProcess.CommandResult terminal,GameLifecycle.TerminalKind terminalKind,String detail) implements EvidenceRow {
        Row { Instant.parse(observedAtUtc); }
    }
    record InventoryRow(String schema,String machineId,String observedAtUtc,String requestId,String sessionId,
            String phase,Win32Host.ProcessInventory inventory) implements EvidenceRow {
        InventoryRow { Instant.parse(observedAtUtc); }
    }
    private final NativeLaunchPlan plan;
    private final Path outputRoot;
    private final String actualMachine;
    private int rows;
    LifecycleEvidence(NativeLaunchPlan plan){this.plan=plan;this.outputRoot=plan.evidenceRoot();this.actualMachine=plan.sources().review().machineId();}
    LifecycleEvidence(NativeLaunchPlan plan,Path outputRoot,String actualMachine){this.plan=plan;this.outputRoot=outputRoot;this.actualMachine=actualMachine;}
    synchronized ExactRef writeInventory(String phase,Win32Host.ProcessInventory inventory)throws IOException{
        if(phase==null||!phase.matches("[A-Z_]{1,64}")||inventory==null)throw new IOException("Bounded inventory phase and actual inventory required");
        return persist(new InventoryRow("xar.java-game-process-inventory/v1",actualMachine,Instant.now().toString(),
                plan.requestId(),plan.sessionId(),phase,inventory));
    }
    synchronized ExactRef write(Event event,WindowsJobProcess.ProcessIdentity game,WindowsJobProcess.Accounting accounting,
            WindowsJobProcess.CommandResult terminal,GameLifecycle.TerminalKind kind,String detail)throws IOException{
        if(detail==null||detail.length()>2048)throw new IOException("Bounded lifecycle detail required");
        Row row=new Row("xar.java-game-lifecycle-event/v1",actualMachine,Instant.now().toString(),plan.requestId(),plan.sessionId(),event,game,accounting,terminal,kind,detail);
        return persist(row);
    }
    private ExactRef persist(EvidenceRow row)throws IOException{
        if(rows>=plan.maximumEvidenceRows())throw new IOException("Lifecycle evidence row limit exhausted; no silent eviction");
        Path file=outputRoot.resolve(String.format(java.util.Locale.ROOT,"event-%06d.json",++rows));
        SharedSourceFiles.plainAncestors(file.getParent());
        byte[] raw=ControlBuild.strictMapper().writeValueAsBytes(row);
        if(raw.length>65536)throw new IOException("Lifecycle row exceeds64KiB");
        Files.write(file,raw,StandardOpenOption.CREATE_NEW);return exact(ControlBuild.FileRef.measure(file));
    }
    static ExactRef exact(ControlBuild.FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
}
