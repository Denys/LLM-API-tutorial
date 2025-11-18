# Track C, Section 2: Database Integration

**Duration:** 45-60 minutes | **Level:** Intermediate

## Why This Matters for LLM APIs

Database integration enables:
- **Conversation persistence:** Save and resume chats
- **Response caching:** Reduce API costs
- **Usage tracking:** Store metrics for analytics
- **User management:** Track per-user usage

## Concepts

### SQLAlchemy Models

```python
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String)
    content = Column(String)
    tokens = Column(Integer)
    conversation = relationship("Conversation", back_populates="messages")
```

### Async Database Operations

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine("sqlite+aiosqlite:///app.db")

async with AsyncSession(engine) as session:
    result = await session.execute(select(Conversation))
    conversations = result.scalars().all()
```

## Examples

### Conversation Storage

```python
# examples/conversation_storage.py
"""Store and retrieve conversations."""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, select
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime
from typing import Optional

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), index=True, nullable=False)
    title = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class ConversationStore:
    """Async conversation storage."""

    def __init__(self, database_url: str = "sqlite+aiosqlite:///conversations.db"):
        self.engine = create_async_engine(database_url)
        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession)

    async def init_db(self):
        """Create tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def create_conversation(self, user_id: str, title: str = None) -> int:
        """Create a new conversation."""
        async with self.async_session() as session:
            conv = Conversation(user_id=user_id, title=title)
            session.add(conv)
            await session.commit()
            await session.refresh(conv)
            return conv.id

    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        tokens_in: int = 0,
        tokens_out: int = 0
    ):
        """Add message to conversation."""
        async with self.async_session() as session:
            msg = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                tokens_in=tokens_in,
                tokens_out=tokens_out
            )
            session.add(msg)
            await session.commit()

    async def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """Get conversation with messages."""
        async with self.async_session() as session:
            result = await session.execute(
                select(Conversation)
                .where(Conversation.id == conversation_id)
            )
            return result.scalar_one_or_none()

    async def get_messages(self, conversation_id: int) -> list[dict]:
        """Get messages for API call format."""
        async with self.async_session() as session:
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
            )
            messages = result.scalars().all()
            return [{"role": m.role, "content": m.content} for m in messages]

    async def get_user_conversations(self, user_id: str) -> list[Conversation]:
        """Get all conversations for a user."""
        async with self.async_session() as session:
            result = await session.execute(
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(Conversation.updated_at.desc())
            )
            return result.scalars().all()


# Usage
async def main():
    store = ConversationStore()
    await store.init_db()

    # Create conversation
    conv_id = await store.create_conversation("user_123", "Chat about Python")

    # Add messages
    await store.add_message(conv_id, "user", "What is Python?", tokens_in=10)
    await store.add_message(conv_id, "assistant", "Python is...", tokens_out=50)

    # Get messages for API
    messages = await store.get_messages(conv_id)
    print(messages)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Response Caching

```python
# examples/response_cache.py
"""Cache LLM responses to reduce API costs."""

from sqlalchemy import Column, Integer, String, Text, DateTime, select
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime, timedelta
import hashlib

Base = declarative_base()

class CachedResponse(Base):
    __tablename__ = "cached_responses"

    id = Column(Integer, primary_key=True)
    prompt_hash = Column(String(64), unique=True, index=True)
    prompt = Column(Text)
    response = Column(Text)
    model = Column(String(50))
    tokens_in = Column(Integer)
    tokens_out = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)


class ResponseCache:
    """LLM response cache."""

    def __init__(self, database_url: str = "sqlite+aiosqlite:///cache.db"):
        self.engine = create_async_engine(database_url)
        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession)

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def _hash_prompt(self, prompt: str, model: str) -> str:
        """Create hash key for prompt+model."""
        content = f"{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def get(self, prompt: str, model: str) -> Optional[dict]:
        """Get cached response if exists and not expired."""
        prompt_hash = self._hash_prompt(prompt, model)

        async with self.async_session() as session:
            result = await session.execute(
                select(CachedResponse)
                .where(CachedResponse.prompt_hash == prompt_hash)
                .where(CachedResponse.expires_at > datetime.utcnow())
            )
            cached = result.scalar_one_or_none()

            if cached:
                return {
                    "response": cached.response,
                    "tokens_in": cached.tokens_in,
                    "tokens_out": cached.tokens_out,
                    "cached": True
                }
            return None

    async def set(
        self,
        prompt: str,
        response: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        ttl_hours: int = 24
    ):
        """Cache a response."""
        prompt_hash = self._hash_prompt(prompt, model)

        async with self.async_session() as session:
            # Delete existing if any
            await session.execute(
                delete(CachedResponse)
                .where(CachedResponse.prompt_hash == prompt_hash)
            )

            cached = CachedResponse(
                prompt_hash=prompt_hash,
                prompt=prompt,
                response=response,
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                expires_at=datetime.utcnow() + timedelta(hours=ttl_hours)
            )
            session.add(cached)
            await session.commit()

    async def clear_expired(self):
        """Remove expired cache entries."""
        async with self.async_session() as session:
            await session.execute(
                delete(CachedResponse)
                .where(CachedResponse.expires_at < datetime.utcnow())
            )
            await session.commit()
```

---

## Exercises

### Simple: Basic CRUD Operations

**Task:** Create a simple usage log table:
1. Define model with timestamp, tokens, cost
2. Implement insert and query methods

<details>
<summary>Solution</summary>

```python
from sqlalchemy import Column, Integer, Float, DateTime, select
from datetime import datetime

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True)
    tokens_in = Column(Integer)
    tokens_out = Column(Integer)
    cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class UsageLogger:
    async def log(self, tokens_in: int, tokens_out: int, cost: float):
        async with self.async_session() as session:
            log = UsageLog(tokens_in=tokens_in, tokens_out=tokens_out, cost=cost)
            session.add(log)
            await session.commit()

    async def get_total_cost(self) -> float:
        async with self.async_session() as session:
            result = await session.execute(
                select(func.sum(UsageLog.cost))
            )
            return result.scalar() or 0.0
```
</details>

---

### Intermediate: FastAPI + Database

**Task:** Integrate database with FastAPI:
1. Create conversation on first message
2. Store all messages
3. Retrieve conversation history

<details>
<summary>Solution</summary>

```python
from fastapi import FastAPI, Depends

app = FastAPI()

# Dependency
async def get_store():
    store = ConversationStore()
    await store.init_db()
    return store

@app.post("/conversations")
async def create_conversation(
    user_id: str,
    store: ConversationStore = Depends(get_store)
):
    conv_id = await store.create_conversation(user_id)
    return {"conversation_id": conv_id}

@app.post("/conversations/{conv_id}/messages")
async def add_message(
    conv_id: int,
    request: ChatRequest,
    store: ConversationStore = Depends(get_store)
):
    # Save user message
    await store.add_message(conv_id, "user", request.message)

    # Get history
    messages = await store.get_messages(conv_id)

    # Call LLM
    response = await llm_call(messages)

    # Save response
    await store.add_message(conv_id, "assistant", response.text)

    return {"response": response.text}

@app.get("/conversations/{conv_id}")
async def get_conversation(
    conv_id: int,
    store: ConversationStore = Depends(get_store)
):
    messages = await store.get_messages(conv_id)
    return {"messages": messages}
```
</details>

---

### Advanced: Full Production System

**Task:** Build a complete system with:
1. Conversation storage
2. Response caching
3. Usage tracking with cost calculation
4. Admin endpoints for analytics

<details>
<summary>Solution</summary>

See complete examples in the examples directory. Key components:

```python
# Combined system
class LLMService:
    def __init__(self):
        self.store = ConversationStore()
        self.cache = ResponseCache()
        self.logger = UsageLogger()

    async def chat(self, conv_id: int, message: str) -> str:
        # Check cache
        cached = await self.cache.get(message, "claude-sonnet")
        if cached:
            return cached["response"]

        # Get history
        messages = await self.store.get_messages(conv_id)
        messages.append({"role": "user", "content": message})

        # Call API
        response = await self.llm.messages.create(...)

        # Store message
        await self.store.add_message(conv_id, "user", message)
        await self.store.add_message(conv_id, "assistant", response.text)

        # Cache response
        await self.cache.set(message, response.text, ...)

        # Log usage
        await self.logger.log(tokens_in, tokens_out, cost)

        return response.text
```
</details>

---

## Pro Tips

### 1. Use Migrations with Alembic

```bash
alembic init migrations
alembic revision --autogenerate -m "Initial"
alembic upgrade head
```

### 2. Connection Pooling

```python
engine = create_async_engine(
    database_url,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)
```

### 3. Soft Deletes

```python
class Conversation(Base):
    deleted_at = Column(DateTime, nullable=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None
```

### 4. Indexes for Performance

```python
class Message(Base):
    __table_args__ = (
        Index("ix_messages_conv_created", "conversation_id", "created_at"),
    )
```

---

## Track C Complete!

You've learned:
- FastAPI for LLM-powered APIs
- Database integration for persistence

Return to [Part 2 Overview](../../README.md) or proceed to [Module 1](../../../01-basic-api/).
