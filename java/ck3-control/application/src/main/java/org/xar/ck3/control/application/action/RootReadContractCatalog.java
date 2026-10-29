package org.xar.ck3.control.application.action;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Fixed typed factories issue exact dynamic contracts; callers cannot register a freshly forged contract. */
public final class RootReadContractCatalog {
    public record InstalledRead(ReadContract<?> contract, ExactRef decoderSource) {
        public InstalledRead {
            Objects.requireNonNull(contract); Objects.requireNonNull(decoderSource);
            StrictJson.require(decoderSource.bytes() > 0, "actual read decoder source required");
        }
    }

    public static final class Family<A, R> {
        private final String id;
        private final Class<A> argumentType;
        private final ReadContract.GuardMode guardMode;
        private final Optional<String> capability;
        private final ExactRef definitionSource;
        private final ExactRef decoderSource;
        private final Function<A, RawJson> encodeArguments;
        private final Function<A, OperationKey> operation;
        private final Function<A, ReadContract<R>> factory;
        private final Map<RawJson, ReadContract<R>> issued = new HashMap<>();
        public Family(String id, Class<A> argumentType, ReadContract.GuardMode guardMode, Optional<String> capability,
                ExactRef definitionSource, ExactRef decoderSource, Function<A, RawJson> encodeArguments,
                Function<A, OperationKey> operation, Function<A, ReadContract<R>> factory) {
            this.id = StrictJson.text(id); this.argumentType = Objects.requireNonNull(argumentType);
            this.guardMode = Objects.requireNonNull(guardMode); this.capability = Objects.requireNonNull(capability);
            capability.ifPresent(StrictJson::text); this.definitionSource = Objects.requireNonNull(definitionSource);
            this.decoderSource = Objects.requireNonNull(decoderSource); this.encodeArguments = Objects.requireNonNull(encodeArguments);
            this.operation = Objects.requireNonNull(operation); this.factory = Objects.requireNonNull(factory);
            StrictJson.require(definitionSource.bytes() > 0 && decoderSource.bytes() > 0, "actual dynamic read implementation/decoder sources required");
        }
        public String id() { return id; }
        public ExactRef definitionSource() { return definitionSource; }
        public ExactRef decoderSource() { return decoderSource; }
        public ReadContract.GuardMode guardMode() { return guardMode; }
        public Optional<String> requiredCapability() { return capability; }
        private synchronized ReadContract<R> issue(A arguments) {
            StrictJson.require(argumentType.isInstance(arguments), "dynamic read arguments have the wrong runtime type");
            A exact = argumentType.cast(arguments);
            RawJson key = Objects.requireNonNull(encodeArguments.apply(exact));
            StrictJson.require(key.bytes().length <= 65_536, "finite exact dynamic read argument body required");
            OperationKey expected = Objects.requireNonNull(operation.apply(exact));
            ReadContract<R> prior = issued.get(key);
            if (prior != null) {
                StrictJson.require(prior.operation().equals(expected), "same dynamic read arguments changed their native operation"); return prior;
            }
            StrictJson.require(issued.size() < 4096, "bounded dynamic read family requires a new qualified session");
            ReadContract<R> actual = Objects.requireNonNull(factory.apply(exact));
            StrictJson.require(actual.operation().equals(expected) && actual.sourceRef().equals(definitionSource)
                    && actual.guardMode() == guardMode && actual.requiredCapability().equals(capability),
                    "dynamic read factory changed its fixed source/origin/operation/permission");
            actual.bindOriginalContracts(this::original);
            issued.put(key, actual); return actual;
        }
        private synchronized Optional<ReadContract<R>> original(String contractId) {
            List<ReadContract<R>> matches=issued.values().stream().filter(actual -> actual.contractId().equals(contractId)).toList();
            StrictJson.require(matches.size()<=1,"one original typed contract per family identity required");
            return matches.isEmpty()?Optional.empty():Optional.of(matches.getFirst());
        }
    }

    private final List<InstalledRead> fixed;
    private final List<Family<?, ?>> families;
    private final Set<ReadContract<?>> identities = Collections.newSetFromMap(new IdentityHashMap<>());
    private final List<InstalledRead> dynamic = new ArrayList<>();
    private final Map<String, ReadContract<?>> contractIds = new HashMap<>();

    public RootReadContractCatalog(List<InstalledRead> fixed, List<Family<?, ?>> families) {
        this.fixed = List.copyOf(fixed); this.families = List.copyOf(families);
        StrictJson.require(this.fixed.size() <= 4096 && this.families.size() <= 256, "bounded fixed Root read factory catalog required");
        Set<String> familyIds = new HashSet<>();
        for (Family<?, ?> family : this.families) StrictJson.require(familyIds.add(family.id()), "duplicate installed dynamic read family ID");
        for (InstalledRead binding : this.fixed) retain(binding.contract());
    }

    public static RootReadContractCatalog staticOnly(List<ReadContract<?>> contracts) {
        return new RootReadContractCatalog(List.copyOf(contracts).stream().map(contract -> new InstalledRead(contract, contract.sourceRef())).toList(), List.of());
    }

    public synchronized <A, R> ReadContract<R> issue(Family<A, R> installedFamily, A arguments) {
        StrictJson.require(families.stream().anyMatch(family -> family == installedFamily), "dynamic read factory is not the identical Root-installed family");
        ReadContract<R> actual = installedFamily.issue(arguments);
        if (!identities.contains(actual)) {
            StrictJson.require(identities.size() < 4096, "bounded Root dynamic read registrations exhausted");
            retain(actual); dynamic.add(new InstalledRead(actual, installedFamily.decoderSource()));
        }
        return actual;
    }

    public synchronized boolean containsIdentity(ReadContract<?> contract) { return identities.contains(Objects.requireNonNull(contract)); }
    /** Resolves the exact original typed object from the current contract's Root-owned family escrow. No cast, new contract or deadline is minted. */
    public synchronized <T> Optional<ReadContract<T>> originalContract(ReadContract<T> identicalCurrent,String originalId) {
        StrictJson.require(identities.contains(Objects.requireNonNull(identicalCurrent)),"current read contract is not the identical installed object");
        if(fixed.stream().anyMatch(binding -> binding.contract()==identicalCurrent))
            return identicalCurrent.contractId().equals(StrictJson.text(originalId))?Optional.of(identicalCurrent):Optional.empty();
        Optional<ReadContract<T>> found=identicalCurrent.originalContract(StrictJson.text(originalId));
        if(found.isEmpty())return Optional.empty();ReadContract<T> original=found.orElseThrow();
        StrictJson.require(identities.contains(original)&&original.contractId().equals(originalId)
                &&original.operation().equals(identicalCurrent.operation())&&original.sourceRef().equals(identicalCurrent.sourceRef())
                &&original.guardMode()==identicalCurrent.guardMode()&&original.wireProfile()==identicalCurrent.wireProfile()
                &&original.permissionMode()==identicalCurrent.permissionMode()&&original.permissionKey().equals(identicalCurrent.permissionKey())
                &&original.requiredCapability().equals(identicalCurrent.requiredCapability()),"original read escrow crossed its installed source/origin/operation/permission");
        StrictJson.require(decoderSource(original).equals(decoderSource(identicalCurrent)),"original typed escrow crossed the exact installed decoder source");
        return found;
    }
    private ExactRef decoderSource(ReadContract<?> identical) {
        List<InstalledRead> matches=installed().stream().filter(binding -> binding.contract()==identical).toList();
        StrictJson.require(matches.size()==1,"one identical installed read decoder source required");return matches.getFirst().decoderSource();
    }
    public synchronized List<InstalledRead> installed() {
        List<InstalledRead> all = new ArrayList<>(fixed); all.addAll(dynamic); return List.copyOf(all);
    }
    public List<Family<?, ?>> families() { return families; }
    public synchronized List<ReadContract<?>> contracts() { return installed().stream().map(InstalledRead::contract).toList(); }

    private void retain(ReadContract<?> actual) {
        ReadContract<?> prior = contractIds.putIfAbsent(actual.contractId(), actual);
        StrictJson.require(prior == null || prior == actual, "distinct actual read contracts claim one contract ID");
        StrictJson.require(identities.add(actual), "same exact read contract object registered twice");
    }
}
