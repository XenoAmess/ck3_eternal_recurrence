package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.service.root.RootBootstrapProtocol.*;

/** The mechanical exchange used by the production Session and real pipe regressions. No writer or issuer implementation. */
public final class RootBootstrapDuplex {
    public interface Handler {
        FileRef authorize(String phase,WindowsJobProcess.Arrival arrival,Quote quote)throws Exception;
        void beforeSend(String phase,FileRef binding)throws Exception;
        void sent(String phase,WindowsJobProcess.WriteReceipt receipt)throws Exception;
        void created(String phase,WindowsJobProcess.Arrival arrival,Quote quote,Stage stage)throws Exception;
    }
    private final Mode mode;private final WindowsJobProcess.OwnedStdio io;private final WindowsJobProcess.StdioGuard guard;
    private boolean entered,sendAttempted;private long sequence;
    public RootBootstrapDuplex(Mode mode,WindowsJobProcess.OwnedStdio io,WindowsJobProcess.StdioGuard guard,long previousSequence){
        this.mode=Objects.requireNonNull(mode);this.io=Objects.requireNonNull(io);this.guard=Objects.requireNonNull(guard);
        if(previousSequence<0)throw new IllegalArgumentException("actual prior arrival sequence required");sequence=previousSequence;
    }
    public boolean sendAttempted(){return sendAttempted;}
    public long sequence(){return sequence;}
    public WindowsJobProcess.Arrival next()throws Exception {
        guard.verify();var value=io.readLine(io.deadline());sequence=RootProfileBootstrapSession.arrival(value,io,sequence);return value;
    }
    public void exchange(Handler handler)throws Exception {
        if(entered)throw new IOException("original duplex exchange cannot replay");entered=true;
        for(String phase:mode.phases()){
            var arrival=next();var quote=RootBootstrapProtocol.line(arrival.rawBytes(),Quote.class);
            if(!phase.equals(quote.phase())||(mode==Mode.FORMAL_RELEASE)!=quote.schema().equals("xar.java-root-bootstrap-formal-release-phase-quote/v2"))
                throw new IOException("wrong mode, phase, duplicate or reordered original quote");
            FileRef binding=Objects.requireNonNull(handler.authorize(phase,arrival,quote));guard.verify();
            byte[] line=RootBootstrapProtocol.bindingLine(binding);sendAttempted=true;handler.beforeSend(phase,binding);guard.verify();
            var receipt=io.write(line,io.deadline());
            if(receipt.bytesWritten()!=line.length||!receipt.identity().equals(io.identity())||!receipt.sessionNonce().equals(io.sessionNonce()))
                throw new IOException("opaque original pipe write receipt differs");
            handler.sent(phase,receipt);arrival=next();
            handler.created(phase,arrival,quote,RootBootstrapProtocol.stage(arrival.rawBytes(),quote.machineId()));
        }
    }
}
