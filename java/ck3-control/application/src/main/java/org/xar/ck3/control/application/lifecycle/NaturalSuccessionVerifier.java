package org.xar.ck3.control.application.lifecycle;

import java.io.IOException;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** Installed actual M3 natural-control authority. A title MATCHED result or actor change alone cannot implement this contract. */
@FunctionalInterface
public interface NaturalSuccessionVerifier {
    /** Recheck original GetPlayerHeir, actual natural cause/control and any required legal modal clearance under this original writer head. */
    String verify(ActionCommand originalParent,LifecycleObservationPort.Snapshot actual,WriterContracts.Head actualWriter) throws IOException;
}
