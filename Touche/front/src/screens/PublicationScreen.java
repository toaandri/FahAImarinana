package screens;

import utils.Colors;
import utils.Responsive;
import utils.ScreenManager;
import utils.TextWrap;
import screens.ChatScreen;
import screens.SmsNewsScreen;
import components.NavigationBar;
import javax.microedition.lcdui.Canvas;
import javax.microedition.lcdui.Graphics;
import java.util.Vector;

public class PublicationScreen extends Canvas {
    private Vector publications = new Vector();
    private NavigationBar nav = new NavigationBar();
    private int scrollY = 0;
    private int lastDragY = 0;
    private int maxScroll = 0;

    public PublicationScreen() {
        setFullScreenMode(true);
        nav.selected = 2;
        publications.addElement("Publication: Manifestation a Antananarivo");
        publications.addElement("Publication: Coupure d'electricite");
        publications.addElement("Publication: Election communale");
    }

    protected void paint(Graphics g) {
        Responsive.init(this);
        int w = getWidth();
        int h = getHeight();
        g.setColor(Colors.WHITE);
        g.fillRect(0, 0, w, h);
        int barH = Responsive.scale(32);
        g.setColor(Colors.PETROL_BLUE);
        g.fillRect(0, 0, w, barH);
        g.setColor(Colors.WHITE);
        g.drawString("PUBLICATIONS", w / 2, barH / 2, Graphics.BASELINE | Graphics.HCENTER);
        int navH = nav.getBarHeight();
        int y = barH + Responsive.scale(4) - scrollY;
        for (int i = 0; i < publications.size(); i++) {
            String txt = (String) publications.elementAt(i);
            g.setColor(Colors.WHITE);
            g.fillRoundRect(Responsive.scale(6), y - Responsive.scale(2), w - Responsive.scale(12), g.getFont().getHeight() * 2 + Responsive.scale(10), 6, 6);
            g.setColor(Colors.SECONDARY_GRAY);
            g.drawRoundRect(Responsive.scale(6), y - Responsive.scale(2), w - Responsive.scale(12), g.getFont().getHeight() * 2 + Responsive.scale(10), 6, 6);
            g.setColor(Colors.PETROL_BLUE);
            int th = TextWrap.draw(g, txt, Responsive.scale(10), y, w - Responsive.scale(20));
            y += th + Responsive.scale(8);
        }
        maxScroll = Math.max(0, y + scrollY - (h - navH));
        if (scrollY > maxScroll) scrollY = maxScroll;
        nav.paint(g, w, h);
    }

    protected void keyPressed(int keyCode) {
        int action = getGameAction(keyCode);
        if (action == UP) { scrollY = Math.max(0, scrollY - Responsive.scale(20)); repaint(); }
        else if (action == DOWN) { scrollY = Math.min(maxScroll, scrollY + Responsive.scale(20)); repaint(); }
    }

    protected void pointerPressed(int x, int y) {
        lastDragY = y;
        int w = getWidth();
        int h = getHeight();
        int idx = nav.hitTest(x, y, w, h);
        if (idx >= 0) { nav.selected = idx; navigate(idx); repaint(); }
    }

    protected void pointerDragged(int x, int y) {
        int delta = lastDragY - y;
        scrollY = Math.max(0, Math.min(maxScroll, scrollY + delta));
        lastDragY = y;
        repaint();
    }

    private void navigate(int idx) {
        if (idx == 0) ScreenManager.show(new ChatScreen());
        else if (idx == 1) ScreenManager.show(new SmsNewsScreen());
    }
}
