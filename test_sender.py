"""Test sender agent — sends a chat message and prints the reply."""
from uagents import Agent, Context, Model

class ChatMessage(Model):
    session_id: str
    text: str

class ChatAcknowledgement(Model):
    session_id: str
    status: str = "ok"

TARGET = "agent1qdvt8gkdy3ep24asvq62qdmlaxwf94fj86ccd53ujpgr9wegv6yd2dsmx5m"

sender = Agent(
    name="test-sender",
    seed="test-sender-seed-123",
    port=8002,
    endpoint=["http://127.0.0.1:8002/submit"],
)

@sender.on_event("startup")
async def send(ctx: Context):
    print(f"Sending message to {TARGET}...")
    await ctx.send(TARGET, ChatMessage(
        session_id="test-1",
        text="I want something on-edge, watching solo, loved Parasite",
    ))

@sender.on_message(model=ChatMessage)
async def on_reply(ctx: Context, sender_addr: str, msg: ChatMessage):
    print("\n=== AGENT REPLIED ===")
    print(msg.text)
    print("====================\n")

sender.run()
