package components;

import utils.Colors;
import utils.Responsive;
import javax.microedition.lcdui.Graphics;

public class CustomButton {
    public int x, y, w, h;
    public String label;
    public boolean selected;
    public boolean pressed;

    public CustomButton(String label, int x, int y, int w, int h) {
        this.label = label;
        this.x = x;
        this.y = y;
        this.w = w;
        this.h = h;
    }

    public void paint(Graphics g) {
        int r = Responsive.scale(8);
        int bg = pressed ? Colors.TURQUOISE : (selected ? Colors.TURQUOISE : Colors.PETROL_BLUE);
        int fg = Colors.WHITE;
        g.setColor(bg);
        fillRoundRect(g, x, y, w, h, r);
        g.setColor(fg);
        g.drawString(label, x + w / 2, y + h / 2, Graphics.BASELINE | Graphics.HCENTER);
    }

    private void fillRoundRect(Graphics g, int x, int y, int w, int h, int r) {
        g.fillRoundRect(x, y, w, h, r, r);
    }

    public boolean contains(int px, int py) {
        return px >= x && px <= x + w && py >= y && py <= y + h;
    }
}
