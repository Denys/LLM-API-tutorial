# Track A, Section 2: Testing LLM Applications

**Duration:** 60-90 minutes | **Level:** Intermediate

## Why This Matters for LLM APIs

Testing LLM applications is challenging because:
- API calls are expensive and slow
- Responses are non-deterministic
- Rate limits affect test runs
- You need to test error handling

Solution: **Mock the API layer**, test your logic.

## Concepts

### pytest Basics

```python
# test_client.py
def test_token_counting():
    """Test token counter adds correctly."""
    counter = TokenCounter()
    counter.add(100, 50)
    assert counter.total == 150

def test_invalid_model():
    """Test error on invalid model."""
    with pytest.raises(ValueError, match="Unknown model"):
        TokenCounter(model="invalid")
```

### Fixtures

```python
import pytest

@pytest.fixture
def client():
    """Provide configured client for tests."""
    return LLMClient(api_key="test-key")

@pytest.fixture
def sample_messages():
    """Provide sample conversation."""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"}
    ]

def test_chat(client, sample_messages):
    # client and sample_messages injected automatically
    pass
```

### Mocking

```python
from unittest.mock import Mock, patch, MagicMock

# Mock a method
with patch.object(client, 'call_api') as mock:
    mock.return_value = "mocked response"
    result = client.chat("test")
    assert result == "mocked response"
    mock.assert_called_once()
```

## Examples

### Testing with Mocked API

```python
# examples/test_with_mocks.py
"""Testing LLM client with mocked API responses."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from anthropic import RateLimitError


# The client we're testing
class LLMClient:
    def __init__(self, api_key: str):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)

    def chat(self, prompt: str) -> str:
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text


# Fixtures
@pytest.fixture
def mock_anthropic():
    """Mock Anthropic client."""
    with patch('anthropic.Anthropic') as mock:
        yield mock


@pytest.fixture
def client(mock_anthropic):
    """Provide client with mocked API."""
    return LLMClient(api_key="test-key")


# Tests
class TestLLMClient:

    def test_chat_success(self, client, mock_anthropic):
        """Test successful chat completion."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="Hello! How can I help?")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 8

        mock_anthropic.return_value.messages.create.return_value = mock_response

        # Test
        result = client.chat("Hi there")

        # Assertions
        assert result == "Hello! How can I help?"
        mock_anthropic.return_value.messages.create.assert_called_once()

    def test_chat_with_specific_args(self, client, mock_anthropic):
        """Test that correct arguments are passed to API."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]

        mock_anthropic.return_value.messages.create.return_value = mock_response

        client.chat("Test prompt")

        # Check call arguments
        call_args = mock_anthropic.return_value.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-sonnet-4-20250514"
        assert call_args.kwargs["messages"][0]["content"] == "Test prompt"

    def test_rate_limit_error(self, client, mock_anthropic):
        """Test handling of rate limit errors."""
        # Setup mock to raise error
        mock_anthropic.return_value.messages.create.side_effect = RateLimitError(
            message="Rate limited",
            response=Mock(status_code=429),
            body={}
        )

        with pytest.raises(RateLimitError):
            client.chat("Test")
```

### Fixtures for Complex Setup

```python
# examples/test_fixtures.py
"""Advanced fixtures for LLM testing."""

import pytest
import json
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_conversation():
    """Sample multi-turn conversation."""
    return [
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": "Python is a programming language."},
        {"role": "user", "content": "What are its main features?"},
    ]


@pytest.fixture
def mock_response_factory():
    """Factory for creating mock API responses."""
    def _create(text: str, input_tokens: int = 10, output_tokens: int = 20):
        from unittest.mock import Mock
        response = Mock()
        response.content = [Mock(text=text)]
        response.usage.input_tokens = input_tokens
        response.usage.output_tokens = output_tokens
        response.model = "claude-sonnet-4-20250514"
        response.stop_reason = "end_turn"
        return response
    return _create


@pytest.fixture
def client_with_history():
    """Client with pre-populated conversation history."""
    client = ConversationClient()
    client.add_message("user", "Hello")
    client.add_message("assistant", "Hi there!")
    return client


# Using fixtures in tests
class TestConversation:

    def test_history_maintained(self, client_with_history):
        """Test that history is maintained."""
        assert len(client_with_history.history) == 2

    def test_custom_response(self, mock_response_factory):
        """Test with custom mock response."""
        response = mock_response_factory(
            text="Custom response",
            input_tokens=50,
            output_tokens=100
        )
        assert response.content[0].text == "Custom response"
        assert response.usage.output_tokens == 100
```

### Parametrized Tests

```python
# examples/test_parametrize.py
"""Parametrized tests for multiple scenarios."""

import pytest


class TokenCounter:
    PRICING = {
        "claude-sonnet": {"input": 3.0, "output": 15.0},
        "claude-opus": {"input": 15.0, "output": 75.0},
        "claude-haiku": {"input": 0.25, "output": 1.25},
    }

    def __init__(self, model: str):
        if model not in self.PRICING:
            raise ValueError(f"Unknown model: {model}")
        self.model = model
        self.input_tokens = 0
        self.output_tokens = 0

    def add(self, input_tokens: int, output_tokens: int):
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    @property
    def cost(self) -> float:
        p = self.PRICING[self.model]
        return (self.input_tokens * p["input"] + self.output_tokens * p["output"]) / 1_000_000


# Parametrized tests
class TestTokenCounter:

    @pytest.mark.parametrize("model", ["claude-sonnet", "claude-opus", "claude-haiku"])
    def test_valid_models(self, model):
        """Test all valid models can be instantiated."""
        counter = TokenCounter(model)
        assert counter.model == model

    @pytest.mark.parametrize("invalid_model", ["gpt-4", "gemini", "invalid", ""])
    def test_invalid_models(self, invalid_model):
        """Test invalid models raise errors."""
        with pytest.raises(ValueError):
            TokenCounter(invalid_model)

    @pytest.mark.parametrize("input_tokens,output_tokens,expected_total", [
        (0, 0, 0),
        (100, 0, 100),
        (0, 100, 100),
        (100, 100, 200),
        (1000, 500, 1500),
    ])
    def test_token_totals(self, input_tokens, output_tokens, expected_total):
        """Test token counting with various inputs."""
        counter = TokenCounter("claude-sonnet")
        counter.add(input_tokens, output_tokens)
        assert counter.input_tokens + counter.output_tokens == expected_total

    @pytest.mark.parametrize("model,input_tokens,output_tokens,expected_cost", [
        ("claude-sonnet", 1_000_000, 0, 3.0),
        ("claude-sonnet", 0, 1_000_000, 15.0),
        ("claude-opus", 1_000_000, 1_000_000, 90.0),
        ("claude-haiku", 1_000_000, 1_000_000, 1.5),
    ])
    def test_cost_calculation(self, model, input_tokens, output_tokens, expected_cost):
        """Test cost calculation for different models."""
        counter = TokenCounter(model)
        counter.add(input_tokens, output_tokens)
        assert counter.cost == pytest.approx(expected_cost)
```

### Async Testing

```python
# examples/test_async.py
"""Testing async LLM operations."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch


class AsyncLLMClient:
    async def chat_async(self, prompt: str) -> str:
        # Actual implementation would call API
        pass

    async def batch_async(self, prompts: list[str]) -> list[str]:
        tasks = [self.chat_async(p) for p in prompts]
        return await asyncio.gather(*tasks)


# Async fixtures
@pytest.fixture
async def async_client():
    """Async client fixture."""
    client = AsyncLLMClient()
    yield client


# Async tests
class TestAsyncClient:

    @pytest.mark.asyncio
    async def test_single_call(self, async_client):
        """Test single async call."""
        with patch.object(async_client, 'chat_async', new_callable=AsyncMock) as mock:
            mock.return_value = "Mocked response"

            result = await async_client.chat_async("Test")

            assert result == "Mocked response"
            mock.assert_awaited_once_with("Test")

    @pytest.mark.asyncio
    async def test_batch_processing(self, async_client):
        """Test batch async processing."""
        with patch.object(async_client, 'chat_async', new_callable=AsyncMock) as mock:
            mock.side_effect = ["Response 1", "Response 2", "Response 3"]

            results = await async_client.batch_async(["P1", "P2", "P3"])

            assert results == ["Response 1", "Response 2", "Response 3"]
            assert mock.await_count == 3

    @pytest.mark.asyncio
    async def test_concurrent_execution(self, async_client):
        """Test that calls execute concurrently."""
        call_times = []

        async def mock_chat(prompt):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)
            return f"Response to {prompt}"

        with patch.object(async_client, 'chat_async', side_effect=mock_chat):
            start = asyncio.get_event_loop().time()
            results = await async_client.batch_async(["A", "B", "C"])
            elapsed = asyncio.get_event_loop().time() - start

        # Should complete in ~0.1s if concurrent, ~0.3s if sequential
        assert elapsed < 0.2, "Calls should execute concurrently"
        assert len(results) == 3
```

---

## Exercises

### Simple: Test Token Counter

**Task:** Write tests for the `TokenCounter` class:
- Test initialization with valid/invalid models
- Test adding tokens
- Test cost calculation
- Test reset functionality

Use `pytest.mark.parametrize` for multiple model tests.

<details>
<summary>Solution</summary>

```python
import pytest

class TestTokenCounter:
    @pytest.fixture
    def counter(self):
        return TokenCounter("claude-sonnet")

    def test_init_valid(self, counter):
        assert counter.model == "claude-sonnet"
        assert counter.input_tokens == 0

    @pytest.mark.parametrize("model", ["invalid", "gpt-4"])
    def test_init_invalid(self, model):
        with pytest.raises(ValueError):
            TokenCounter(model)

    def test_add_tokens(self, counter):
        counter.add(100, 50)
        assert counter.input_tokens == 100
        assert counter.output_tokens == 50

    def test_cost(self, counter):
        counter.add(1_000_000, 0)
        assert counter.cost == 3.0

    def test_reset(self, counter):
        counter.add(100, 100)
        counter.reset()
        assert counter.total_tokens == 0
```
</details>

---

### Intermediate: Mock API Client

**Task:** Write tests for an LLM client that:
- Mocks the Anthropic API
- Tests successful responses
- Tests error handling (rate limit, timeout)
- Verifies correct parameters are passed

<details>
<summary>Hints</summary>

1. Use `@patch('anthropic.Anthropic')` to mock
2. Create a fixture for mock responses
3. Use `side_effect` for errors
4. Check `call_args` for parameter verification
</details>

<details>
<summary>Solution</summary>

```python
import pytest
from unittest.mock import Mock, patch
from anthropic import RateLimitError, APITimeoutError

class TestLLMClient:
    @pytest.fixture
    def mock_api(self):
        with patch('anthropic.Anthropic') as mock:
            yield mock

    @pytest.fixture
    def client(self, mock_api):
        return LLMClient(api_key="test")

    @pytest.fixture
    def mock_success_response(self):
        response = Mock()
        response.content = [Mock(text="Success")]
        response.usage.input_tokens = 10
        response.usage.output_tokens = 20
        return response

    def test_successful_call(self, client, mock_api, mock_success_response):
        mock_api.return_value.messages.create.return_value = mock_success_response

        result = client.chat("Hello")

        assert result == "Success"

    def test_rate_limit_handling(self, client, mock_api):
        mock_api.return_value.messages.create.side_effect = RateLimitError(
            "Rate limited", Mock(status_code=429), {}
        )

        with pytest.raises(RateLimitError):
            client.chat("Test")

    def test_parameters_passed(self, client, mock_api, mock_success_response):
        mock_api.return_value.messages.create.return_value = mock_success_response

        client.chat("Test prompt", max_tokens=500)

        call_kwargs = mock_api.return_value.messages.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 500
        assert call_kwargs["messages"][0]["content"] == "Test prompt"
```
</details>

---

### Advanced: Integration Test Suite

**Task:** Create a comprehensive test suite that:
- Uses fixtures for different configurations
- Tests retry logic with multiple failures then success
- Tests conversation history management
- Tests streaming responses (mock the stream)
- Includes performance benchmarks

<details>
<summary>Hints</summary>

1. Use `side_effect` with a list for retry testing
2. Mock stream with a generator
3. Use `pytest-benchmark` for performance
4. Create a `conftest.py` for shared fixtures
</details>

<details>
<summary>Solution</summary>

```python
# conftest.py
import pytest
from unittest.mock import Mock, patch, MagicMock

@pytest.fixture
def mock_anthropic():
    with patch('anthropic.Anthropic') as mock:
        yield mock

@pytest.fixture
def response_factory():
    def _create(text, tokens_in=10, tokens_out=20):
        r = Mock()
        r.content = [Mock(text=text)]
        r.usage.input_tokens = tokens_in
        r.usage.output_tokens = tokens_out
        return r
    return _create


# test_integration.py
import pytest
from anthropic import RateLimitError

class TestRetryLogic:
    def test_retry_then_success(self, mock_anthropic, response_factory):
        """Test retry succeeds after failures."""
        client = ResilientClient(api_key="test", max_retries=3)

        # First 2 calls fail, third succeeds
        mock_anthropic.return_value.messages.create.side_effect = [
            RateLimitError("1", Mock(), {}),
            RateLimitError("2", Mock(), {}),
            response_factory("Success after retries")
        ]

        result = client.chat("Test")

        assert result == "Success after retries"
        assert mock_anthropic.return_value.messages.create.call_count == 3

    def test_max_retries_exceeded(self, mock_anthropic):
        """Test failure after max retries."""
        client = ResilientClient(api_key="test", max_retries=2)

        mock_anthropic.return_value.messages.create.side_effect = RateLimitError(
            "Always fail", Mock(), {}
        )

        with pytest.raises(RateLimitError):
            client.chat("Test")


class TestConversationHistory:
    @pytest.fixture
    def client_with_history(self, mock_anthropic, response_factory):
        mock_anthropic.return_value.messages.create.return_value = response_factory("Hi")
        client = ConversationClient(api_key="test")
        client.chat("Hello")
        return client

    def test_history_maintained(self, client_with_history):
        assert len(client_with_history.history) == 2  # user + assistant

    def test_history_in_api_call(self, client_with_history, mock_anthropic, response_factory):
        mock_anthropic.return_value.messages.create.return_value = response_factory("Response")

        client_with_history.chat("Follow-up")

        call_msgs = mock_anthropic.return_value.messages.create.call_args.kwargs["messages"]
        assert len(call_msgs) == 3  # Previous + new


class TestStreaming:
    def test_stream_chunks(self, mock_anthropic):
        """Test streaming returns chunks."""
        client = StreamingClient(api_key="test")

        # Mock the stream context manager
        mock_stream = MagicMock()
        mock_stream.__enter__.return_value.text_stream = iter(["Hello", " ", "world"])
        mock_anthropic.return_value.messages.stream.return_value = mock_stream

        chunks = list(client.stream("Test"))

        assert chunks == ["Hello", " ", "world"]


class TestPerformance:
    def test_token_counting_performance(self, benchmark):
        """Benchmark token counting."""
        counter = TokenCounter("claude-sonnet")

        def count_tokens():
            for _ in range(1000):
                counter.add(100, 50)

        result = benchmark(count_tokens)
        assert counter.total_tokens == 150_000
```
</details>

---

## Pro Tips

### 1. Use pytest-mock for Cleaner Mocking

```python
def test_with_mocker(mocker):
    mock = mocker.patch('module.function')
    mock.return_value = "value"
    # Auto-cleanup after test
```

### 2. Snapshot Testing for Prompts

```python
def test_prompt_generation(snapshot):
    prompt = generate_prompt(data)
    assert prompt == snapshot
    # Run with --snapshot-update to update
```

### 3. Environment-Based Test Skipping

```python
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="API key required"
)
def test_real_api():
    # Integration test with real API
    pass
```

### 4. Test Markers for Categories

```python
# pytest.ini
[pytest]
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests

# Usage
@pytest.mark.unit
def test_unit():
    pass

# Run specific: pytest -m unit
```

### 5. Coverage Requirements

```bash
# pytest.ini
[pytest]
addopts = --cov=src --cov-fail-under=80
```

---

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Testing implementation | Brittle tests | Test behavior |
| No mocking | Slow, expensive | Mock external calls |
| Missing edge cases | Bugs in production | Test errors, empty inputs |
| Shared state | Flaky tests | Use fixtures, reset state |
| Too many assertions | Hard to debug | One concept per test |

---

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific markers
pytest -m "unit and not slow"

# Run async tests
pytest -v --asyncio-mode=auto

# Parallel execution
pytest -n auto
```

---

## Next Section

[Section 3: Packaging →](../03-packaging/)
