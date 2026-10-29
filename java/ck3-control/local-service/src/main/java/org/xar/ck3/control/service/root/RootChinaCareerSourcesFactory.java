package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.ChinaCareerCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.ChinaCareerContract;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.ChinaCareerService;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SelectedSource;
import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;

/** Concrete pre-Core source wiring for ChinaCareer06. Source selection grants no Core, Game or native permission. */
public final class RootChinaCareerSourcesFactory {
    private RootChinaCareerSourcesFactory() { }
    public record Sources(ExactRef service,ExactRef codec) {
        public Sources {
            Objects.requireNonNull(service);Objects.requireNonNull(codec);
            if(service.bytes()<=0||codec.bytes()<=0)throw new IllegalArgumentException("actual nonempty selected China career sources required");
        }
        public RootChinaCareerPublicProducts.Prepared prepared() {
            return new RootChinaCareerPublicProducts.Prepared(service,codec);
        }
    }
    public static RootChinaCareerPublicProducts.Prepared prepare(RootRuntimeDefinitions.Inputs inputs,
            RootRuntimeSelectedSources selected)throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(selected);
        RootRuntimeDefinitions.verifySources(inputs.configuration(),inputs.sourceIndex());
        Sources actual=sources(selected,inputs.sourceIndex());
        selected.requireCurrent();return actual.prepared();
    }
    /** Same production source path, usable on actual source DATA without constructing Runtime Inputs or a Core. */
    static Sources sources(RootRuntimeSelectedSources selected,List<SelectedSource> sameInputIndex)throws IOException {
        Objects.requireNonNull(selected);sameInputIndex=List.copyOf(sameInputIndex);selected.requireCurrent();
        same(selected.javaSource(LOCAL_SERVICE,RootChinaCareerSourcesFactory.class),sameInputIndex,target(LOCAL_SERVICE,RootChinaCareerSourcesFactory.class));
        same(selected.javaSource(LOCAL_SERVICE,RootChinaCareerPublicProducts.class),sameInputIndex,target(LOCAL_SERVICE,RootChinaCareerPublicProducts.class));
        same(selected.javaSource(NATIVE_TRANSPORT,ChinaCareerContract.class),sameInputIndex,target(NATIVE_TRANSPORT,ChinaCareerContract.class));
        ExactRef service=selected.javaSource(NATIVE_TRANSPORT,ChinaCareerService.class);
        ExactRef codec=selected.javaSource(NATIVE_TRANSPORT,ChinaCareerCodec.class);
        same(service,sameInputIndex,target(NATIVE_TRANSPORT,ChinaCareerService.class));
        same(codec,sameInputIndex,target(NATIVE_TRANSPORT,ChinaCareerCodec.class));
        Sources result=new Sources(service,codec);selected.requireCurrent();return result;
    }
    private static String target(RootRuntimeSelectedSources.Module module,Class<?> type) {
        return module.directory()+"/src/main/java/"+type.getName().replace('.','/')+".java";
    }
    private static void same(ExactRef retained,List<SelectedSource> inputs,String target)throws IOException {
        var rows=inputs.stream().filter(source->source.targetRelative().equals(target)).toList();
        if(rows.size()!=1||!rows.getFirst().sourceRef().equals(retained))
            throw new IOException("China career producer is not the identical unique actual Inputs selection: "+target);
    }
}
