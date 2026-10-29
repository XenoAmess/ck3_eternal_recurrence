package org.xar.ck3.control.continuity.writer;

import java.io.IOException;

/** Package-private crash seam, invoked only after the actual production durable write succeeds. */
@FunctionalInterface
interface WriterFaultProbe {
    enum Boundary { EVENT_PUBLISHED, SNAPSHOT_PUBLISHED, SOURCE_INDEX_PUBLISHED }
    WriterFaultProbe NONE = (boundary, sequence) -> { };
    void reached(Boundary boundary, long sequence) throws IOException;
}
