package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Collection;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;

/** Public adapter for the one real Root operator source. No fallback source is manufactured here. */
public final class RootSetPlayedCharacterRuntime {
    private RootSetPlayedCharacterRuntime() { }
    @FunctionalInterface public interface RuntimePort {
        RawJson execute(RootApplicationSession same,OperatorPlayerSwitch.Request request,Instant deadline)throws IOException,InterruptedException;
    }
    public record Completed(OperatorPlayerSwitch.Completion completion,Long originalFromActor) {
        public Completed {Objects.requireNonNull(completion);if(originalFromActor!=null)NativeCharacterId.of(originalFromActor);}
    }
    /** Implemented by the actual private Root issuer, including canonical settlement, independent after and persisted identity. */
    public interface Source {
        void requireOwner(RootRuntimeContext same)throws IOException;
        RootDomainInstallation installation();
        Completed execute(RootApplicationSession same,OperatorPlayerSwitch.Request request,Instant deadline)throws IOException,InterruptedException;
    }
    /** Mandatory actual pre-Core product. Metadata cannot substitute for an unavailable private issuer. */
    public interface SourceFactory {
        List<DomainBodies.Registration> domainRegistrations();
        Collection<NativePrivateActionPermission> privatePermissions();
        void bindCore(RootApplicationAssembly.Core same)throws IOException;
        Source install(RootRuntimeContext same)throws IOException;
        Class<?> implementationType();
    }
    public static Prepared prepare(RootRuntimeDefinitions.Inputs actual,RootRuntimeSelectedSources sameSelected,SourceFactory actualSource)throws IOException {
        return new Prepared(actual,sameSelected,actualSource);
    }
    public static Prepared prepareOrdinary(SourceFactory sources,RootAdditionalDomains.ImplementationMetadata metadata)throws IOException {
        return new Prepared(sources,metadata);
    }
    public static final class Prepared {
        private final java.util.Optional<RootRuntimeSelectedSources> selected;private final SourceFactory sources;private final List<ExactRef> closure;
        private final IdentityHashMap<RootRuntimeContext,Attempt> installed=new IdentityHashMap<>();private RootApplicationAssembly.Core core;
        private Prepared(RootRuntimeDefinitions.Inputs actual,RootRuntimeSelectedSources selected,SourceFactory sources)throws IOException {
            Objects.requireNonNull(actual);this.selected=java.util.Optional.of(Objects.requireNonNull(selected));this.sources=Objects.requireNonNull(sources);
            closure=List.of(selected.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,OperatorPlayerSwitch.class),
                    selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootSetPlayedCharacterRuntime.class),
                    selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,Objects.requireNonNull(sources.implementationType())));
        }
        private Prepared(SourceFactory sources,RootAdditionalDomains.ImplementationMetadata metadata)throws IOException {
            this.selected=java.util.Optional.empty();this.sources=Objects.requireNonNull(sources);
            closure=List.of(metadata.implementation(OperatorPlayerSwitch.class),
                    metadata.implementation(RootSetPlayedCharacterRuntime.class),
                    metadata.implementation(Objects.requireNonNull(sources.implementationType())));
        }
        public List<DomainBodies.Registration> domainRegistrations(){return List.copyOf(sources.domainRegistrations());}
        public Collection<NativePrivateActionPermission> privatePermissions(){return List.copyOf(sources.privatePermissions());}
        public synchronized void bindCore(RootApplicationAssembly.Core same)throws IOException {
            if(core!=null&&core!=same)throw new IOException("operator Prepared belongs to another actual Core");sources.bindCore(Objects.requireNonNull(same));core=same;
        }
        public synchronized Installed install(RootRuntimeContext same)throws IOException {
            Objects.requireNonNull(same);if(core==null||core!=same.core())throw new IOException("operator requires its identical privately bound Core");
            Attempt prior=installed.get(same);if(prior!=null){if(prior.value!=null)return prior.value;throw new IOException("partial operator installation is never replayed",prior.failure);}
            if(installed.size()>=64)throw new IOException("operator per-context installation bound exhausted");var attempt=new Attempt();installed.put(same,attempt);
            try {
                Source source=Objects.requireNonNull(sources.install(same));source.requireOwner(same);
                RuntimePort port=(owner,request,deadline)->{
                    if(owner!=same.actions())throw new IOException("operator request crossed the actual Root owner");
                    same.requireCurrent(deadline);source.requireOwner(same);
                    Completed actual=Objects.requireNonNull(source.execute(owner,request,deadline));
                    if(!actual.completion().request().equals(request))throw new IOException("actual operator completion belongs to another public request");
                    source.requireOwner(same);
                    return OperatorPlayerSwitch.publicResult(actual.completion(),actual.originalFromActor());
                };
                attempt.value=new Installed(Objects.requireNonNull(source.installation()),port);return attempt.value;
            }catch(IOException|RuntimeException failure){attempt.failure=failure;throw failure;}
        }
        private static final class Attempt {private Installed value;private Throwable failure;}
    }
    public record Installed(RootDomainInstallation installation,RuntimePort runtime) {
        public Installed {Objects.requireNonNull(installation);Objects.requireNonNull(runtime);}
    }
}
