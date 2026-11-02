package models;

public class Message {
    public String text;
    public boolean fromUser;

    public Message(String text, boolean fromUser) {
        this.text = text;
        this.fromUser = fromUser;
    }
}
