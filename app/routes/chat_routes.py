from flask import Blueprint, render_template, request
from flask_socketio import emit, join_room
from flask_login import login_required, current_user
from app import socketio
import redis
import json
from ..models import User

chat_bp = Blueprint("chat", __name__)

# Redis client
redis_client = redis.StrictRedis(host="redis", port=6379, decode_responses=True)

def get_chat_room(user1, user2):
    """Return a normalized room key for the two users."""
    user1 = int(user1)  # Convert to integer
    user2 = int(user2)  # Convert to integer
    return f"chat:{min(user1, user2)}:{max(user1, user2)}"

@chat_bp.route("/chat")
@login_required
def chat():
    """Chat page for the current user."""
    new_user_id = request.args.get("new_user", type=int)
    receiver = None
    messages = []

    if new_user_id:
        receiver = User.query.get_or_404(new_user_id)
        # Fetch messages from Redis
        room = get_chat_room(current_user.id, new_user_id)
        messages = redis_client.lrange(room, 0, -1)

    other_users = User.query.filter(User.id != current_user.id).all()

    return render_template("chat.html", other_users=other_users, messages=messages, receiver=receiver)

@socketio.on("connect")
def handle_connect():
    """Handle WebSocket connection."""
    if not current_user.is_authenticated:
        print(f"Unauthorized connection attempt by {request.sid}")
        return False
    print(f"User connected: {current_user.username} (ID: {current_user.id})")

@socketio.on("send_message")
@login_required
def send_message(data):
    """Handle sending a message."""
    if "receiver_id" not in data or not data["receiver_id"].isdigit():
        emit("error", {"message": "Invalid receiver ID"})
        return

    receiver_id = int(data["receiver_id"])  # Convert to integer
    room = get_chat_room(current_user.id, receiver_id)
    message = {
        "username": current_user.username,
        "message": data["message"]
    }

    # Serialize the message to a JSON string
    serialized_message = json.dumps(message)

    # Save serialized message to Redis
    redis_client.rpush(room, serialized_message)
    redis_client.expire(room, 604800)  # Set TTL to 7 days

    # Emit the message to the room
    emit("receive_message", message, room=room)

@socketio.on("join_room")
@login_required
def join_room_handler(data):
    """Handle user joining a chat room."""
    if "receiver_id" not in data or not data["receiver_id"].isdigit():
        emit("error", {"message": "Invalid receiver ID"})
        return

    receiver_id = int(data["receiver_id"])  # Convert to integer
    room = get_chat_room(current_user.id, receiver_id)
    join_room(room)

    # Load chat history from Redis
    serialized_messages = redis_client.lrange(room, 0, -1)
    messages = [json.loads(msg) for msg in serialized_messages]  # Deserialize messages

    # Emit the chat history to the client
    emit("load_messages", {"messages": messages})

