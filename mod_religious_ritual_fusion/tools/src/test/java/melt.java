import java.nio.file.Files;
import java.nio.file.Path;
/** Owned test-only decoder boundary for the production argv. It is not Rakaly or game evidence. */
public final class melt {
    private melt() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 6 || !args[1].equals("-c") || !args[2].equals("--format") || !args[3].equals("ck3")
                || !args[4].equals("--unknown-key") || !args[5].equals("error")) throw new IllegalArgumentException("unchanged production decoder argv required");
        byte[] data=Files.readAllBytes(Path.of(args[0]));
        if (!new String(data,java.nio.charset.StandardCharsets.UTF_8).startsWith("CK3txt # AUTHORED_CANCEL_SOFTWARE_ONLY")) throw new IllegalArgumentException("owned synthetic bytes only");
        System.out.write(data);
    }
}
