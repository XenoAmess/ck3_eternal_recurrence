package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesFacade;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesService;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SelectedSource;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;

/** Resolves the original six ChinaCases Java source roles from the same actual Inputs and selector.
 * This records actual classes for the caller's final same-plan loaded-class custody check; it grants no Game authority. */
public final class RootChinaCasesSourcesFactory {
    private RootChinaCasesSourcesFactory() { }

    private enum Role {
        FACADE(Module.NATIVE_TRANSPORT,ChinaCasesFacade.class),
        ORIGINAL_DECODER(Module.NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.class),
        PUBLIC_CONTRACT(Module.NATIVE_TRANSPORT,ChinaCasesContract.class),
        PUBLIC_CODEC(Module.NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesCodec.class),
        PUBLIC_SERVICE(Module.NATIVE_TRANSPORT,ChinaCasesService.class),
        ROOT_PRODUCT(Module.LOCAL_SERVICE,RootChinaCasesPublicProducts.class),
        SOURCE_FACTORY(Module.LOCAL_SERVICE,RootChinaCasesSourcesFactory.class),
        READ_CONTRACT(Module.APPLICATION,org.xar.ck3.control.application.action.ReadContract.class),
        HISTORY_MATERIAL(Module.APPLICATION,org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.class);
        private final Module module;
        private final Class<?> actualClass;
        Role(Module module,Class<?> actualClass){this.module=module;this.actualClass=actualClass;}
        String target(){return module.directory()+"/src/main/java/"+actualClass.getName().replace('.','/')+".java";}
    }

    /** Inputs have already passed the actual Root definitions boundary; no replacement Inputs/selector is constructed here. */
    public static RootChinaCasesPublicProducts.Prepared prepare(RootRuntimeDefinitions.Inputs inputs,
            RootRuntimeSelectedSources selected)throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(selected);
        return prepareSourceSelection(inputs.sourceIndex(),selected);
    }

    /** Same production resolution path, with a source-DATA-only test seam; it cannot create Inputs, Core or an Installed runtime. */
    static RootChinaCasesPublicProducts.Prepared prepareSourceSelection(List<SelectedSource> inputWinners,
            RootRuntimeSelectedSources selected)throws IOException {
        Objects.requireNonNull(selected);List<SelectedSource> stable=List.copyOf(inputWinners);
        if(stable.isEmpty()||stable.size()>8192)throw new IOException("bounded actual ChinaCases winner index required");
        var index=new HashMap<String,SelectedSource>();var folded=new HashSet<String>();
        for(SelectedSource row:stable)if(index.putIfAbsent(row.targetRelative(),row)!=null||!folded.add(row.targetRelative().toLowerCase(Locale.ROOT)))
            throw new IOException("duplicate or case-aliased actual source target in ChinaCases Inputs");
        var expected=new EnumMap<Role,ExactRef>(Role.class);
        for(Role role:Role.values()) {
            SelectedSource row=index.get(role.target());
            if(row==null)throw new IOException("actual Inputs lack the required ChinaCases source: "+role.target());
            expected.put(role,row.sourceRef());
        }
        selected.requireCurrent();var actual=new EnumMap<Role,ExactRef>(Role.class);
        for(Role role:Role.values()) {
            // Retain the real class, not a basename or caller-provided FQN, in the original selector's loaded-class inventory.
            ExactRef resolved=selected.javaSource(role.module,role.actualClass);
            if(!resolved.equals(expected.get(role)))throw new IOException("ChinaCases selector differs from the actual Inputs source role: "+role.target());
            actual.put(role,resolved);
        }
        selected.requireCurrent();
        return RootChinaCasesPublicProducts.prepare(new RootChinaCasesPublicProducts.Sources(
                actual.get(Role.FACADE),actual.get(Role.ORIGINAL_DECODER),actual.get(Role.PUBLIC_CONTRACT),actual.get(Role.PUBLIC_CODEC),
                actual.get(Role.PUBLIC_SERVICE),actual.get(Role.ROOT_PRODUCT)));
    }
}
