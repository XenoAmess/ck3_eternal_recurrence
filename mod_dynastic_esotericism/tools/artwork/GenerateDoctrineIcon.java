import java.awt.AlphaComposite;
import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.geom.Ellipse2D;
import java.awt.geom.Path2D;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;

/** Original procedural artwork, 2026-10-24. No game or third-party pixels. */
public final class GenerateDoctrineIcon {
    private static final int SIZE = 120;
    private static final int SCALE = 4;

    private GenerateDoctrineIcon() {}

    public static void main(String[] arguments) throws IOException {
        if (arguments.length != 1) {
            throw new IllegalArgumentException("Expected the output DDS path");
        }
        BufferedImage canvas = new BufferedImage(SIZE * SCALE, SIZE * SCALE,
                BufferedImage.TYPE_INT_ARGB);
        Graphics2D brush = canvas.createGraphics();
        try {
            brush.scale(SCALE, SCALE);
            brush.setRenderingHint(RenderingHints.KEY_ANTIALIASING,
                    RenderingHints.VALUE_ANTIALIAS_ON);
            brush.setColor(new Color(44, 27, 23, 222));
            brush.fill(new Ellipse2D.Double(8, 8, 104, 104));
            brush.setColor(new Color(195, 153, 83));
            brush.setStroke(new BasicStroke(3.0f));
            brush.draw(new Ellipse2D.Double(9, 9, 102, 102));
            brush.setColor(new Color(129, 89, 48));
            brush.setStroke(new BasicStroke(1.0f));
            brush.draw(new Ellipse2D.Double(14, 14, 92, 92));
            brush.setColor(new Color(235, 210, 156));
            brush.setStroke(new BasicStroke(4.0f, BasicStroke.CAP_ROUND,
                    BasicStroke.JOIN_ROUND));
            Path2D tree = new Path2D.Double();
            tree.moveTo(60, 92);
            tree.lineTo(60, 60);
            tree.moveTo(29, 42);
            tree.lineTo(29, 60);
            tree.lineTo(91, 60);
            tree.lineTo(91, 42);
            tree.moveTo(60, 60);
            tree.lineTo(60, 31);
            tree.moveTo(44, 92);
            tree.lineTo(76, 92);
            brush.draw(tree);
            for (double horizontal : new double[] {29, 60, 91}) {
                double vertical = horizontal == 60 ? 27 : 36;
                brush.setColor(new Color(111, 37, 38));
                brush.fill(new Ellipse2D.Double(horizontal - 7, vertical - 7, 14, 14));
                brush.setColor(new Color(235, 210, 156));
                brush.setStroke(new BasicStroke(2.2f));
                brush.draw(new Ellipse2D.Double(horizontal - 7, vertical - 7, 14, 14));
            }
            Path2D seal = new Path2D.Double();
            seal.moveTo(60, 66);
            seal.lineTo(68, 76);
            seal.lineTo(60, 86);
            seal.lineTo(52, 76);
            seal.closePath();
            brush.setColor(new Color(111, 37, 38));
            brush.fill(seal);
            brush.setColor(new Color(235, 210, 156));
            brush.setStroke(new BasicStroke(1.7f));
            brush.draw(seal);
        } finally {
            brush.dispose();
        }
        BufferedImage icon = new BufferedImage(SIZE, SIZE, BufferedImage.TYPE_INT_ARGB);
        Graphics2D downsample = icon.createGraphics();
        try {
            downsample.setComposite(AlphaComposite.Src);
            downsample.setRenderingHint(RenderingHints.KEY_INTERPOLATION,
                    RenderingHints.VALUE_INTERPOLATION_BICUBIC);
            downsample.drawImage(canvas, 0, 0, SIZE, SIZE, null);
        } finally {
            downsample.dispose();
        }
        Path destination = Path.of(arguments[0]).toAbsolutePath().normalize();
        Files.createDirectories(destination.getParent());
        Files.write(destination, encodeDds(icon));
        System.out.println("Created original " + SIZE + "x" + SIZE + " RGBA DDS: " + destination);
    }

    private static byte[] encodeDds(BufferedImage icon) {
        ByteBuffer result = ByteBuffer.allocate(128 + SIZE * SIZE * 4)
                .order(ByteOrder.LITTLE_ENDIAN);
        result.putInt(0x20534444).putInt(124).putInt(0x100f);
        result.putInt(SIZE).putInt(SIZE).putInt(SIZE * 4).putInt(0).putInt(0);
        for (int reserved = 0; reserved < 11; reserved++) {
            result.putInt(0);
        }
        result.putInt(32).putInt(0x41).putInt(0).putInt(32);
        result.putInt(0x00ff0000).putInt(0x0000ff00).putInt(0x000000ff).putInt(0xff000000);
        result.putInt(0x1000).putInt(0).putInt(0).putInt(0).putInt(0);
        for (int vertical = 0; vertical < SIZE; vertical++) {
            for (int horizontal = 0; horizontal < SIZE; horizontal++) {
                result.putInt(icon.getRGB(horizontal, vertical));
            }
        }
        return result.array();
    }
}
