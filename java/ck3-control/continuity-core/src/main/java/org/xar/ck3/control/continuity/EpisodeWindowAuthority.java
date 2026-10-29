package org.xar.ck3.control.continuity;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Root installs exactly one reviewed verifier of private adoption and private first-checkpoint custody. */
public final class EpisodeWindowAuthority implements TransitionAuthority {
    public interface Verifier {
        /** Recheck the actual private LifecycleComposites adoption using the currently borrowed Session. */
        String requireBegin(Head actual,EpisodeWindow.Begin begin) throws IOException;
        /** Recheck the same original private VerifiedFirstCheckpoint; this method never submits SAVE. */
        String requireBaseline(Head actual,EpisodeWindow.Baseline baseline) throws IOException;
    }
    private final Verifier verifier;
    public EpisodeWindowAuthority(Verifier verifier){this.verifier=Objects.requireNonNull(verifier);}
    @Override public String revalidate(ContinuityState ignored,Request request)throws IOException{
        throw new IOException("EpisodeWindow authority requires the actual same-lock full Head");
    }
    @Override public String revalidate(Head actual,Request request)throws IOException{
        String proof;
        if(EpisodeWindow.BEGIN_KIND.equals(request.kind())){
            EpisodeWindow.Begin begin=EpisodeWindow.begin(request);
            StrictJson.require(request.evidence().equals(begin.request().evidence()),"complete typed BEGIN source closure required");
            proof=verifier.requireBegin(actual,begin);
        }else if(EpisodeWindow.BASELINE_KIND.equals(request.kind())){
            EpisodeWindow.Baseline baseline=EpisodeWindow.baseline(request);
            StrictJson.require(request.evidence().equals(baseline.request().evidence()),"complete typed first SAVE source closure required");
            proof=verifier.requireBaseline(actual,baseline);
        }else throw new IOException("unsupported EpisodeWindow authority route");
        requireDigest(proof);return proof;
    }
    @Override public ContinuityState reduce(ContinuityState before,Request request){return EpisodeWindow.reduce(before,request);}
}
