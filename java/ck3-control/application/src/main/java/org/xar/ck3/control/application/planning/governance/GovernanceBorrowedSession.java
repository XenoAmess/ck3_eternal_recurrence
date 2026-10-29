package org.xar.ck3.control.application.planning.governance;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Objects;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** A live Root-owned writer scope. This class never opens a second lock or creates a writer. */
public final class GovernanceBorrowedSession {
    @FunctionalInterface public interface Authority {
        /** Root must bind the concrete sole writer's requireSession, including exact instance custody. */
        void requireSession(ContinuityStorePort.Session session) throws IOException;
    }
    private final java.util.function.Supplier<ContinuityStorePort.Session> borrowed;
    private final Path writerLock;
    private final Authority authority;

    public GovernanceBorrowedSession(ContinuityStorePort.Session borrowed, Path writerLock, Authority authority) {
        Objects.requireNonNull(borrowed); this.borrowed = () -> borrowed;
        this.writerLock = Objects.requireNonNull(writerLock);
        this.authority = Objects.requireNonNull(authority);
    }
    /** One runtime installation may span many writer leases; it resolves the live original session for every call. */
    public GovernanceBorrowedSession(java.util.function.Supplier<ContinuityStorePort.Session> borrowed, Path writerLock, Authority authority) {
        this.borrowed = Objects.requireNonNull(borrowed); this.writerLock = Objects.requireNonNull(writerLock); this.authority = Objects.requireNonNull(authority);
    }
    public <T> T use(PlanningRequest request, ContinuityStorePort.SessionWork<T> work) throws IOException {
        Objects.requireNonNull(request); Objects.requireNonNull(work);
        ContinuityStorePort.Session borrowed = this.borrowed.get();
        if (borrowed == null) throw new IOException("Root has no current borrowed writer Session");
        authority.requireSession(borrowed);
        borrowed.requireWriter(writerLock);
        StrictJson.require(borrowed.head().state().machineId().equals(request.before().machineId()),
                "borrowed governance writer machine differs");
        return work.run(borrowed);
    }
}
