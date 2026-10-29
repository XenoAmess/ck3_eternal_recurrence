package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ContactScopeReads;

/** Installed once per actual physical Game, before the sole Root READ inventory freezes. Construction performs no Game query. */
public final class RootContactRuntime {
    public record Sources(ExactRef reads,ExactRef strictDecoder) {
        public Sources {Objects.requireNonNull(reads);Objects.requireNonNull(strictDecoder);StrictJson.require(reads.bytes()>0&&strictDecoder.bytes()>0,"actual Contact READ/decoder sources required");}
    }
    public static final class Prepared {
        private final Sources sources;
        private Prepared(Sources actual){sources=Objects.requireNonNull(actual);}
        public Sources sources(){return sources;}
        public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        public RootContactRuntime install(RootRuntimeContext context){return new RootContactRuntime(context,sources);}
    }
    public static Prepared prepare(Sources sources){return new Prepared(sources);}
    private final RootRuntimeContext context;
    private final ContactScopeReads reads;
    private RootContactRuntime(RootRuntimeContext current,Sources sources) {
        context=Objects.requireNonNull(current);
        reads=new ContactScopeReads(sources.reads(),sources.strictDecoder(),context.reads(),context.archive(),context.frameLoader(),this::borrowed);
    }
    private ContinuityStorePort.Session borrowed(){try{return context.borrowedSession();}catch(IOException failure){throw new UncheckedIOException(failure);}}
    public ContactScopeReads reads(){return reads;}
    public RootRuntimeContext context(){return context;}
    public RootDomainInstallation readInstallation() {
        return new RootDomainInstallation("contact-scope-reads",List.of(),List.of(),reads.families(),List.of(),List.of(),List.of(),List.of(),List.of(),
                List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
    }
}
