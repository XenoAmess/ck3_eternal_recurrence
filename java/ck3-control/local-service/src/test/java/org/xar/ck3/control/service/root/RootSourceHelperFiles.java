package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SelectedSource;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;

/** Exact readable source bodies only; no fabricated Native cut, Runtime Inputs or loaded-class qualification. */
final class RootSourceHelperFiles {
    private RootSourceHelperFiles() { }
    static SelectedSource java(Class<?> type,Module module)throws Exception {
        String target=module.directory()+"/src/main/java/"+type.getName().replace('.','/')+".java";
        Path location=Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath();
        for(Path cursor=location;cursor!=null;cursor=cursor.getParent()) {
            Path actual=cursor.resolve(target);
            if(Files.isRegularFile(actual))return new SelectedSource(target,exact(actual));
        }
        throw new IOException("NOT_EXECUTED: actual selected Java source is unavailable: "+target);
    }
    static List<SelectedSource> java(List<Class<?>> types,Module module)throws Exception {
        var rows=new ArrayList<SelectedSource>();for(Class<?> type:types)rows.add(java(type,module));return List.copyOf(rows);
    }
    static ExactRef original(String relative)throws IOException {
        String configured=System.getProperty("xar.repository.root");
        if(configured==null||configured.isBlank())throw new IOException("NOT_EXECUTED: required original source property xar.repository.root is unavailable");
        Path repository=Path.of(configured).toAbsolutePath().normalize();Path actual=repository.resolve(relative).normalize();
        if(!actual.startsWith(repository))throw new IOException("original fixture source escaped its required repository");
        return exact(actual);
    }
    static ExactRef exact(Path path)throws IOException {
        FileRef value=FileRef.measure(path);return new ExactRef(value.path(),value.bytes(),value.sha256());
    }
}
