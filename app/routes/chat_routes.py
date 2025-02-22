from flask import Blueprint, render_template, request
from flask_socketio import emit, join_room
from flask_login import login_required, current_user
from flask_babel import _
from app import socketio
import redis
import json
from datetime import datetime
from ..models import User
from config import Config

# Create a Blueprint for the chat routes
chat_bp = Blueprint("chat", __name__)

# Initialize Redis client
redis_client = redis.StrictRedis(
    host=Config.ELASTIC_CACHE or "localhost",
    port=6379,
    decode_responses=True,
)


def get_chat_room(user1, user2):
    """
    Return a normalized room key for the two users.

    Args:
        user1 (int): ID of the first user.
        user2 (int): ID of the second user.

    Returns:
        str: Normalized room key.
    """
    return f"chat:{min(int(user1), int(user2))}:{max(int(user1), int(user2))}"


@chat_bp.route("/chat")
@login_required
def chat():
    """
    Chat page for the current user.

    Returns:
        Rendered template for the chat page with other users and messages.
    """
    new_user_id = request.args.get("new_user", type=int)
    receiver, messages = None, []

    if new_user_id:
        receiver = User.query.get_or_404(new_user_id)
        room = get_chat_room(current_user.id, new_user_id)
        serialized_messages = redis_client.lrange(room, 0, -1)
        messages = [
            {
                **json.loads(msg),
                "timestamp": redis_client.hget(f"{room}:timestamps", idx),
            }
            for idx, msg in enumerate(serialized_messages)
        ]
        redis_client.delete(f"{room}:unread")

    other_users = [
        {
            "id": user.id,
            "username": user.username,
            "unread_count": redis_client.get(
                f"{get_chat_room(current_user.id, user.id)}:unread"
            )
            or 0,
            "recent_message": (
                json.loads(
                    redis_client.lindex(get_chat_room(current_user.id, user.id), -1)
                )["message"]
                if redis_client.lindex(get_chat_room(current_user.id, user.id), -1)
                else _("No recent messages")
            ),
        }
        for user in User.query.filter(User.id != current_user.id).all()
    ]

    return render_template(
        "chat.html", other_users=other_users, messages=messages, receiver=receiver
    )


@socketio.on("connect")
def handle_connect():
    """
    Handle WebSocket connection.

    Returns:
        bool: False if the user is not authenticated.
    """
    if not current_user.is_authenticated:
        print(f"Unauthorized connection attempt by {request.sid}", flush=True)
        return False
    print(
        f"User connected: {current_user.username} (ID: {current_user.id})", flush=True
    )


@socketio.on("disconnect")
def handle_disconnect():
    print(
        f"User disconnected: {current_user.username} (ID: {current_user.id})",
        flush=True,
    )


@socketio.on("send_message")
@login_required
def send_message(data):
    """
    Handle sending a message.

    Args:
        data (dict): Data containing the receiver ID and message content.
    """
    if "message" not in data or not data["message"].strip():
        emit("error", {"message": "Message cannot be empty"})
        return

    if len(data["message"]) > 1000:  # Adjust the limit as needed
        emit("error", {"message": "Message is too long"})
        return

    room = get_chat_room(current_user.id, int(data["receiver_id"]))
    message = {
        "username": current_user.username,
        "message": data["message"],
        "sender_id": current_user.id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    redis_client.rpush(room, json.dumps(message))
    redis_client.hset(
        f"{room}:timestamps", redis_client.llen(room) - 1, message["timestamp"]
    )
    redis_client.incr(f"{room}:unread")
    emit("receive_message", message, room=room)


@socketio.on("join_room")
@login_required
def join_room_handler(data):
    """
    Handle user joining a chat room.

    Args:
        data (dict): Data containing the receiver ID.
    """
    if "receiver_id" not in data or not data["receiver_id"].isdigit():
        emit("error", {"message": "Invalid receiver ID"})
        return

    receiver_id = int(data["receiver_id"])
    if receiver_id == current_user.id:
        emit("error", {"message": "Cannot chat with yourself"})
        return

    receiver = User.query.get(receiver_id)
    if not receiver:
        emit("error", {"message": "Receiver not found"})
        return

    room = get_chat_room(current_user.id, int(data["receiver_id"]))
    join_room(room)
    messages = [json.loads(msg) for msg in redis_client.lrange(room, 0, -1)]
    emit("load_messages", {"messages": messages})
