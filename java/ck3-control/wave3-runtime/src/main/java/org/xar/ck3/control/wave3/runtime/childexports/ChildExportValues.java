package org.xar.ck3.control.wave3.runtime.childexports;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.providerchain.OriginReadbackValues.ProcessKey;

/** Pure message and already-observed values. No value here owns or qualifies an OS handle. */
public final class ChildExportValues {
    private ChildExportValues() { }

    /** Original opaque positive Python integer, not a PID, FileID or uint64 assertion. */
    public record RemoteLocation(BigInteger value) {
        public RemoteLocation {
            StrictJson.require(value != null && value.signum() > 0, "positive remote handle location required");
        }
    }

    public record Export(ChildRole role, RemoteLocation location) {
        public Export {
            StrictJson.require(role != null && location != null, "complete child export values required");
        }
    }

    /** The exporting role comes from the local retained edge; it is absent from the private message. */
    public record Packet(ChildRole exportingRole, List<Export> exports) {
        public Packet {
            StrictJson.require(exportingRole != null && exports != null, "complete child export packet required");
            List<ChildRole> expected = exportingRole.exportedRoles();
            StrictJson.require(exports.size() == expected.size(), "actual child export count differs");
            StrictJson.require(exports.stream().allMatch(row -> row != null), "complete child export rows required");
            exports = List.copyOf(exports);
            for (int index = 0; index < expected.size(); index++) {
                StrictJson.require(exports.get(index).role() == expected.get(index), "private child role/order differs");
            }
            // Equal location integers are not process-identity observations. The original reader checks actual PIDs later.
        }
    }

    /**
     * Direct child first, then each exported process in message order. These are caller-supplied
     * value observations, not evidence that DuplicateHandle or observe_process was performed.
     */
    public record ProcessReadbacks(ChildRole directRole, List<ProcessKey> processes) {
        public ProcessReadbacks {
            StrictJson.require(directRole != null && processes != null, "complete process-key values required");
            StrictJson.require(processes.size() == directRole.exportedRoles().size() + 1,
                    "direct and exported process-key count differs");
            StrictJson.require(processes.stream().allMatch(row -> row != null), "complete process-key rows required");
            processes = List.copyOf(processes);
            HashSet<BigInteger> pids = new HashSet<>();
            for (ProcessKey process : processes) {
                StrictJson.require(pids.add(process.pid()), "creation chain aliases a process PID");
            }
        }
    }
}
