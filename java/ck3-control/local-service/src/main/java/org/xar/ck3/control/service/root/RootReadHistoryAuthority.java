package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.driver.DriverReadHistoryPublisher;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;

/** One pre-registered writer route. A constructed replacement cannot acquire the current Driver's publication authority. */
final class RootReadHistoryAuthority implements WriterContracts.TransitionAuthority {
    private final ContinuityWriter writer;
    private volatile DriverReadHistoryPublisher current;
    RootReadHistoryAuthority(ContinuityWriter writer) { this.writer=Objects.requireNonNull(writer); }
    synchronized void initial(DriverReadHistoryPublisher actual) {
        StrictJson.require(current==null||current==actual,"initial read-history cannot replace its actual producer");current=Objects.requireNonNull(actual);
    }
    synchronized void requireCurrent(ContinuityStorePort.Session same,DriverReadHistoryPublisher previous)throws IOException {
        writer.requireSession(same);
        StrictJson.require(current==previous,"actual read-history producer changed before restored host publication");
        StrictJson.require(!previous.hasPending(same),"unpublished original READ history cannot be discarded by a physical replacement");
    }
    synchronized void publish(DriverReadHistoryPublisher previous,DriverReadHistoryPublisher replacement) {
        StrictJson.require(current==previous && previous!=replacement,"actual read-history producer changed during restored host publication");
        current=Objects.requireNonNull(replacement);
    }
    PreparedPublication preparePublication(ContinuityStorePort.Session same,DriverReadHistoryPublisher previous,
            DriverReadHistoryPublisher replacement)throws IOException {
        requireCurrent(same,previous);Objects.requireNonNull(replacement);
        StrictJson.require(previous!=replacement,"replacement read history must belong to its actual distinct per-Game producer");
        return new PreparedPublication(this,replacement);
    }
    static final class PreparedPublication {
        private final RootReadHistoryAuthority owner;private final DriverReadHistoryPublisher replacement;
        private PreparedPublication(RootReadHistoryAuthority owner,DriverReadHistoryPublisher replacement){this.owner=owner;this.replacement=replacement;}
        void commit(){owner.current=replacement;}
    }
    private DriverReadHistoryPublisher required()throws IOException {
        var actual=current;if(actual==null)throw new IOException("actual read-history producer is not installed");return actual;
    }
    @Override public String revalidate(ContinuityState predecessor,WriterContracts.Request request)throws IOException {
        throw new IOException("read publication requires its actual original writer Head and private batch");
    }
    @Override public String revalidate(WriterContracts.Head head,WriterContracts.Request request)throws IOException {
        writer.requireSession(writer.borrowedSession());return required().revalidate(head,request);
    }
    @Override public ContinuityState reduce(ContinuityState predecessor,WriterContracts.Request request)throws IOException {
        writer.requireSession(writer.borrowedSession());return required().reduce(predecessor,request);
    }
}

