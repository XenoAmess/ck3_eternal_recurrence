package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.StrictJson;

/** The sole saved-attachment reducer keeps its writer; only an admitted physical session's source loader changes. */
final class RootSavedAttachmentLoader implements SavedAttachmentAuthority.SourceLoader {
    private final ContinuityWriter writer;
    private volatile SavedAttachmentAuthority.SourceLoader active;
    RootSavedAttachmentLoader(ContinuityWriter writer) { this.writer = Objects.requireNonNull(writer); }
    synchronized void initial(SavedAttachmentAuthority.SourceLoader actual) {
        StrictJson.require(active == null, "saved attachment source authority already installed"); active = Objects.requireNonNull(actual);
    }
    void requireCurrent(SavedAttachmentAuthority.SourceLoader expected) { StrictJson.require(active == expected, "saved attachment source authority changed"); }
    void publish(SavedAttachmentAuthority.SourceLoader expected, SavedAttachmentAuthority.SourceLoader replacement) {
        requireCurrent(expected); active = Objects.requireNonNull(replacement);
    }
    /** Prepared under the sole writer before the final fallible candidate activation. */
    PreparedPublication preparePublication(ContinuityStorePort.Session same,SavedAttachmentAuthority.SourceLoader expected,
            SavedAttachmentAuthority.SourceLoader replacement)throws IOException {
        writer.requireSession(same);requireCurrent(expected);return new PreparedPublication(this,Objects.requireNonNull(replacement));
    }
    static final class PreparedPublication {
        private final RootSavedAttachmentLoader owner;private final SavedAttachmentAuthority.SourceLoader replacement;
        private PreparedPublication(RootSavedAttachmentLoader owner,SavedAttachmentAuthority.SourceLoader replacement){this.owner=owner;this.replacement=replacement;}
        /** Only Root's writer-held host-publication callback consumes this private producer token. */
        void commit(){owner.active=replacement;}
    }
    @Override public SavedAttachmentAuthority.Loaded load(ContinuityState predecessor, WriterContracts.Request request) throws IOException {
        writer.requireSession(writer.borrowedSession()); SavedAttachmentAuthority.SourceLoader actual = active;
        if (actual == null) throw new IOException("actual saved attachment source authority is not installed");
        return actual.load(predecessor, request);
    }
}
