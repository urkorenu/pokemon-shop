from flask import Blueprint, request
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user, login_required
from app import db, socketio
from ..models import Message, User

chat_bp = Blueprint("chat", __name__)

# Route to load the chat page
@chat_bp.route("/chat/<int:user_id>")
@login_required
def chat(user_id):
    receiver = User.query.get_or_404(user_id)
    messages = Message.query.filter(
        (Message.sender_id == current_user.id) & (Message.receiver_id == user_id) |
        (Message.sender_id == user_id) & (Message.receiver_id == current_user.id)
    ).order_by(Message.timestamp.asc()).all()
    return render_template("chat.html", receiver=receiver, messages=messages)

# Socket.IO event for sending messages
@socketio.on("send_message")
@login_required
def send_message(data):
    receiver_id = data["receiver_id"]
    message_text = data["message"]

    # Save message to database
    message = Message(sender_id=current_user.id, receiver_id=receiver_id, message=message_text)
    db.session.add(message)
    db.session.commit()

    # Send message to the receiver's room
    room = f"user_{receiver_id}"
    emit("receive_message", {
        "sender_id": current_user.id,
        "message": message_text,
        "timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M")
    }, room=room)

# Join room for real-time chat
@socketio.on("join_room")
@login_required
def join_user_room():
    room = f"user_{current_user.id}"
    join_room(room)
