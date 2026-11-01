package org.xar.ck3.control.platform;

import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;

/** Test-only immutable DATA; none of these records is a Root or Native action capability. */
public final class SwayPeer206Contract {
    private SwayPeer206Contract() { }
    public enum Scenario { DYNAMIC_CHAIN, STALE_QUERY }
    public record Settings(Path executable,String softwareExecutableSha256,Path workDirectory,Path evidenceRoot,
            Map<String,String> environment,long actor,long target,String bridgeVersion,String helloExecutableSha256,
            String adapterId,long memoryLimitBytes,long lifetimeMillis,int maximumRequests) {
        public Settings { environment=Map.copyOf(environment); }
    }
    public record Exchange(String label,byte[] originalRequest,NativeWire.CommandResult originalResult) {
        public Exchange { originalRequest=originalRequest.clone(); }
        @Override public byte[] originalRequest() { return originalRequest.clone(); }
    }
    public record Result(Scenario scenario,WindowsJobProcess.ProcessIdentity peer,TransportSession session,
            NativeFreshSnapshotPort.Received before,NativeFreshSnapshotPort.Received after,
            List<Exchange> exchanges,WindowsJobProcess.CommandResult terminal,Path evidenceDirectory) {
        public Result { exchanges=List.copyOf(exchanges); }
    }
}
