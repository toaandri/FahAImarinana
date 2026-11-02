package screens;

import javax.microedition.lcdui.*;
import java.util.Hashtable;
import java.util.Vector;
import network.Api;
import network.Json;
import utils.ScreenManager;

/** Shared form for validated server inputs. */
public class EntryForm extends ApiForm {
    private Vector fields = new Vector();
    private Vector keys = new Vector();
    private Vector numbers = new Vector();
    private String path;
    private Hashtable defaults = Json.object();
    private Api.Listener after;
    private Displayable parent;
    private Command save = new Command("Enregistrer",Command.OK,1);
    public EntryForm(String title,String endpoint,Displayable back,Api.Listener listener) {
        super(title); path = endpoint; parent = back; after = listener; addCommand(save);
    }
    public EntryForm fixed(String key,Object value) { defaults.put(key,value); return this; }
    public EntryForm field(String key,String label,int maximum,boolean number) {
        TextField field = new TextField(label,"",maximum,number ? TextField.NUMERIC : TextField.ANY);
        append(field); fields.addElement(field); keys.addElement(key); numbers.addElement(number ? Boolean.TRUE : Boolean.FALSE);
        return this;
    }
    public void commandAction(Command command,Displayable view) {
        if (busy) return;
        if (command == home) ScreenManager.show(parent); else act(command);
    }
    protected void act(Command command) {
        if (command != save) return;
        Hashtable body = Json.object();
        java.util.Enumeration names = defaults.keys();
        while (names.hasMoreElements()) { Object key = names.nextElement(); body.put(key,defaults.get(key)); }
        try {
            for (int i = 0; i < fields.size(); i++) {
                String value = ((TextField)fields.elementAt(i)).getString();
                Object data = value;
                if (Boolean.TRUE.equals(numbers.elementAt(i))) data = Long.valueOf(value);
                body.put(keys.elementAt(i),data);
            }
        } catch (Exception ex) { status.setText("Une reference numerique valide est requise."); return; }
        call("POST",path,body,after);
    }
}
