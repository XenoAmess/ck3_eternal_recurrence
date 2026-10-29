package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.net.JarURLConnection;
import java.net.URISyntaxException;
import java.net.URL;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;

/** Passive implementation-carrier DATA, measured once per carrier in this worker. */
public final class RootOrdinaryImplementationMetadata implements RootAdditionalDomains.ImplementationMetadata {
    private final Map<Path,ExactRef> carriers=new HashMap<>();

    public synchronized ExactRef file(Path actual)throws IOException {
        Path path=Objects.requireNonNull(actual).toAbsolutePath().normalize();
        ExactRef prior=carriers.get(path);if(prior!=null)return prior;
        MessageDigest digest;
        try {digest=MessageDigest.getInstance("SHA-256");}
        catch(NoSuchAlgorithmException unavailable){throw new IllegalStateException(unavailable);}
        long bytes=0;
        try(var input=Files.newInputStream(path)) {
            byte[] buffer=new byte[16384];int count;
            while((count=input.read(buffer))!=-1) {
                bytes=Math.addExact(bytes,count);digest.update(buffer,0,count);
            }
        }catch(ArithmeticException overflow){throw new IOException("implementation carrier is too large",overflow);}
        ExactRef observed=new ExactRef(path.toString(),bytes,HexFormat.of().formatHex(digest.digest()));
        carriers.put(path,observed);return observed;
    }

    @Override public ExactRef implementation(Class<?> actualClass) {
        Objects.requireNonNull(actualClass);
        URL resource=actualClass.getResource("/"+actualClass.getName().replace('.','/')+".class");
        try {
            if(resource==null)throw new IOException("loaded implementation has no class resource: "+actualClass.getName());
            URL carrier;
            if("jar".equals(resource.getProtocol())) {
                var connection=(JarURLConnection)resource.openConnection();connection.setUseCaches(false);
                carrier=connection.getJarFileURL();
            } else carrier=resource;
            if(!"file".equals(carrier.getProtocol()))throw new IOException("unsupported implementation carrier: "+carrier);
            return file(Path.of(carrier.toURI()));
        }catch(IOException failure){throw new UncheckedIOException(failure);}
        catch(URISyntaxException|IllegalArgumentException invalid){throw new UncheckedIOException(new IOException("invalid implementation carrier",invalid));}
    }
}
