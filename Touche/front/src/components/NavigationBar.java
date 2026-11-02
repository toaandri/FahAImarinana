package components;

import utils.Colors;
import utils.Responsive;
import javax.microedition.lcdui.Graphics;

public class NavigationBar {
    public int selected = 0;
    private String[] labels = {"IA", "SMS", "Pubs"};

    public void paint(Graphics g, int width, int height) {
        int barH = Responsive.scale(40);
        int y = height - barH;
        g.setColor(Colors.PETROL_BLUE);
        g.fillRect(0, y, width, barH);
        // top separator
        g.setColor(Colors.TURQUOISE);
        g.fillRect(0, y, width, 2);
        int itemW = width / 3;
        for (int i = 0; i < 3; i++) {
            int x = i * itemW;
            if (i == selected) {
                g.setColor(Colors.TURQUOISE);
                g.fillRect(x + 2, y + 2, itemW - 4, barH - 4);
            }
            g.setColor(i == selected ? Colors.PETROL_BLUE : Colors.WHITE);
            g.drawString(labels[i], x + itemW / 2, y + barH / 2, Graphics.BASELINE | Graphics.HCENTER);
            // vertical separator
            if (i < 2) {
                g.setColor(Colors.SECONDARY_GRAY);
                g.drawLine(x + itemW, y + 4, x + itemW, y + barH - 4);
            }
        }
    }

    public int getBarHeight() {
        return Responsive.scale(40);
    }

    public int hitTest(int px, int py, int width, int height) {
        int barH = getBarHeight();
        int y = height - barH;
        if (py < y) return -1;
        int itemW = width / 3;
        int idx = px / itemW;
        if (idx < 0) idx = 0;
        if (idx > 2) idx = 2;
        return idx;
    }
}
