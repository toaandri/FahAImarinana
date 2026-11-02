package screens;

import utils.Colors;
import utils.Responsive;
import utils.ScreenManager;
import utils.TextWrap;
import components.NavigationBar;
import components.MessageBubble;
import screens.ChatScreen;
import screens.PublicationScreen;
import models.Message;
import javax.microedition.lcdui.Canvas;
import javax.microedition.lcdui.Graphics;
import java.util.Vector;

public class SmsNewsScreen extends Canvas {
    private Vector smsList = new Vector();
    private Vector newsList = new Vector();
    private Vector messages = new Vector();
    private String input = "";
    private NavigationBar nav = new NavigationBar();
    private int scrollY = 0;
    private int lastDragY = 0;
    private int maxScroll = 0;

    public SmsNewsScreen() {
        setFullScreenMode(true);
        nav.selected = 1;
        smsList.addElement("SMS: Alerte coupure d'electricite a Tana");
        smsList.addElement("SMS: Reunion demain 09h");
        newsList.addElement("News: Manifestation a Antananarivo");
        newsList.addElement("News: Election communale 2026");
        messages.addElement(new Message("Bonjour journaliste, que voulez-vous verifier ?", false));
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
        g.drawString("SMS & NEWS", w / 2, barH / 2, Graphics.BASELINE | Graphics.HCENTER);
        int navH = nav.getBarHeight();
        int inputH = Responsive.scale(30);
        int y = barH + Responsive.scale(4) - scrollY;
        // SMS
        g.setColor(Colors.PETROL_BLUE);
        g.drawString("SMS", Responsive.scale(8), y, Graphics.TOP | Graphics.LEFT);
        y += g.getFont().getHeight() + Responsive.scale(2);
        for (int i = 0; i < smsList.size(); i++) {
            g.setColor(Colors.BLACK);
            int th = TextWrap.draw(g, (String) smsList.elementAt(i), Responsive.scale(8), y, w - Responsive.scale(16));
            y += th + Responsive.scale(2);
        }
        // NEWS
        y += Responsive.scale(6);
        g.setColor(Colors.PETROL_BLUE);
        g.drawString("NEWS", Responsive.scale(8), y, Graphics.TOP | Graphics.LEFT);
        y += g.getFont().getHeight() + Responsive.scale(2);
        for (int i = 0; i < newsList.size(); i++) {
            g.setColor(Colors.BLACK);
            int th = TextWrap.draw(g, (String) newsList.elementAt(i), Responsive.scale(8), y, w - Responsive.scale(16));
            y += th + Responsive.scale(2);
        }
        // DISCUSSION IA / JOURNALISTE
        y += Responsive.scale(6);
        g.setColor(Colors.PETROL_BLUE);
        g.drawString("Discussion IA - Journaliste", Responsive.scale(8), y, Graphics.TOP | Graphics.LEFT);
        y += g.getFont().getHeight() + Responsive.scale(2);
        int maxW = w - Responsive.scale(16);
        for (int i = 0; i < messages.size(); i++) {
            Message m = (Message) messages.elementAt(i);
            int bh = MessageBubble.paint(g, m, Responsive.scale(8), y, maxW);
            y += bh + Responsive.scale(4);
        }
        maxScroll = Math.max(0, y + scrollY - (h - navH - inputH));
        if (scrollY > maxScroll) scrollY = maxScroll;
        // input
        int inputY = h - navH - inputH;
        g.setColor(Colors.LIGHT_GRAY);
        g.fillRect(Responsive.scale(8), inputY, w - Responsive.scale(60), inputH);
        g.setColor(Colors.BLACK);
        g.drawString(input, Responsive.scale(12), inputY + 4, Graphics.TOP | Graphics.LEFT);
        g.setColor(Colors.TURQUOISE);
        g.fillRoundRect(w - Responsive.scale(48), inputY, Responsive.scale(40), inputH, 6, 6);
        g.setColor(Colors.WHITE);
        g.drawString(">", w - Responsive.scale(28), inputY + inputH / 2, Graphics.BASELINE | Graphics.HCENTER);
        nav.paint(g, w, h);
    }

    protected void keyPressed(int keyCode) {
        int action = getGameAction(keyCode);
        if (action == UP) { scrollY = Math.max(0, scrollY - Responsive.scale(20)); repaint(); return; }
        if (action == DOWN) { scrollY = Math.min(maxScroll, scrollY + Responsive.scale(20)); repaint(); return; }
        if (keyCode == -8 || keyCode == 8) {
            if (input.length() > 0) input = input.substring(0, input.length() - 1);
            repaint(); return;
        }
        if (action == FIRE) { sendMessage(); return; }
        char c = (char) keyCode;
        if (c >= 32 && c < 127) { input += c; repaint(); }
    }

    protected void pointerPressed(int x, int y) {
        lastDragY = y;
        int w = getWidth();
        int h = getHeight();
        int navH = nav.getBarHeight();
        int idx = nav.hitTest(x, y, w, h);
        if (idx >= 0) { nav.selected = idx; navigate(idx); repaint(); return; }
        int inputY = h - navH - Responsive.scale(30);
        if (x >= w - Responsive.scale(48) && y >= inputY) {
            sendMessage();
        }
    }

    protected void pointerDragged(int x, int y) {
        int delta = lastDragY - y;
        scrollY = Math.max(0, Math.min(maxScroll, scrollY + delta));
        lastDragY = y;
        repaint();
    }

    private void sendMessage() {
        if (input.trim().length() == 0) return;
        messages.addElement(new Message(input, true));
        messages.addElement(new Message("Reponse IA pour le journaliste.", false));
        input = "";
        scrollY = maxScroll;
        repaint();
    }

    private void navigate(int idx) {
        if (idx == 0) ScreenManager.show(new ChatScreen());
        else if (idx == 2) ScreenManager.show(new PublicationScreen());
    }
}
