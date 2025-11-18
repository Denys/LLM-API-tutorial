# Track B, Section 2: Pandas for LLM Analytics

**Duration:** 45-60 minutes | **Level:** Intermediate

## Why This Matters for LLM APIs

Pandas enables:
- **Usage tracking:** Analyze token consumption over time
- **Cost optimization:** Identify expensive patterns
- **Quality analysis:** Track response metrics
- **Reporting:** Generate dashboards and exports

## Concepts

### DataFrame Basics

```python
import pandas as pd

# Create from API logs
df = pd.DataFrame([
    {"timestamp": "2024-01-01", "model": "sonnet", "tokens_in": 100, "tokens_out": 50},
    {"timestamp": "2024-01-02", "model": "opus", "tokens_in": 200, "tokens_out": 100},
])

# Access data
df["tokens_in"]        # Column
df.loc[0]              # Row by label
df.iloc[0]             # Row by position
df[df["model"] == "sonnet"]  # Filter
```

### Aggregation

```python
# Group and aggregate
df.groupby("model")["tokens_in"].sum()
df.groupby("model").agg({
    "tokens_in": "sum",
    "tokens_out": "mean"
})
```

## Examples

### Token Usage Analysis

```python
# examples/usage_analysis.py
"""Analyze LLM token usage patterns."""

import pandas as pd
import numpy as np


def create_sample_data(n_rows: int = 1000) -> pd.DataFrame:
    """Generate sample API usage data."""
    np.random.seed(42)

    models = ["claude-sonnet", "claude-opus", "claude-haiku"]
    model_probs = [0.6, 0.2, 0.2]

    data = {
        "timestamp": pd.date_range("2024-01-01", periods=n_rows, freq="h"),
        "model": np.random.choice(models, n_rows, p=model_probs),
        "tokens_in": np.random.randint(10, 1000, n_rows),
        "tokens_out": np.random.randint(10, 500, n_rows),
        "latency_ms": np.random.randint(100, 5000, n_rows),
        "user_id": np.random.choice(["user_1", "user_2", "user_3"], n_rows),
    }

    return pd.DataFrame(data)


def analyze_usage(df: pd.DataFrame) -> dict:
    """Analyze token usage patterns."""
    # Model pricing (per 1M tokens)
    pricing = {
        "claude-sonnet": {"input": 3.0, "output": 15.0},
        "claude-opus": {"input": 15.0, "output": 75.0},
        "claude-haiku": {"input": 0.25, "output": 1.25},
    }

    # Calculate costs
    def calc_cost(row):
        p = pricing[row["model"]]
        return (row["tokens_in"] * p["input"] + row["tokens_out"] * p["output"]) / 1_000_000

    df["cost"] = df.apply(calc_cost, axis=1)

    # Summary statistics
    summary = {
        "total_requests": len(df),
        "total_tokens": df["tokens_in"].sum() + df["tokens_out"].sum(),
        "total_cost": df["cost"].sum(),
        "by_model": df.groupby("model").agg({
            "tokens_in": "sum",
            "tokens_out": "sum",
            "cost": "sum",
            "latency_ms": "mean"
        }).to_dict(),
        "by_user": df.groupby("user_id")["cost"].sum().to_dict(),
        "daily_trend": df.groupby(df["timestamp"].dt.date)["cost"].sum().to_dict()
    }

    return summary


# Usage
if __name__ == "__main__":
    df = create_sample_data()
    analysis = analyze_usage(df)

    print(f"Total requests: {analysis['total_requests']}")
    print(f"Total tokens: {analysis['total_tokens']:,}")
    print(f"Total cost: ${analysis['total_cost']:.2f}")

    print("\nBy model:")
    for model, stats in analysis["by_model"].items():
        print(f"  {model}: ${stats:.2f}")
```

### Cost Optimization Report

```python
# examples/cost_report.py
"""Generate cost optimization report."""

import pandas as pd


def identify_optimization_opportunities(df: pd.DataFrame) -> pd.DataFrame:
    """Find high-cost requests that could use cheaper models."""
    # Add cost column
    pricing = {
        "claude-sonnet": {"input": 3.0, "output": 15.0},
        "claude-opus": {"input": 15.0, "output": 75.0},
        "claude-haiku": {"input": 0.25, "output": 1.25},
    }

    def calc_cost(row, model=None):
        m = model or row["model"]
        p = pricing[m]
        return (row["tokens_in"] * p["input"] + row["tokens_out"] * p["output"]) / 1_000_000

    df["actual_cost"] = df.apply(calc_cost, axis=1)

    # Calculate cost if using Haiku instead
    df["haiku_cost"] = df.apply(lambda r: calc_cost(r, "claude-haiku"), axis=1)
    df["potential_savings"] = df["actual_cost"] - df["haiku_cost"]

    # Identify optimization candidates
    # High-cost requests with short outputs (likely simple queries)
    candidates = df[
        (df["model"] != "claude-haiku") &
        (df["tokens_out"] < 100) &
        (df["potential_savings"] > 0.001)
    ].copy()

    candidates = candidates.sort_values("potential_savings", ascending=False)

    return candidates[["timestamp", "model", "tokens_in", "tokens_out",
                       "actual_cost", "haiku_cost", "potential_savings"]]


def generate_report(df: pd.DataFrame) -> str:
    """Generate optimization report."""
    candidates = identify_optimization_opportunities(df)

    report = []
    report.append("# Cost Optimization Report\n")

    total_savings = candidates["potential_savings"].sum()
    report.append(f"**Potential Monthly Savings:** ${total_savings:.2f}\n")

    report.append("\n## Top Optimization Opportunities\n")

    for _, row in candidates.head(10).iterrows():
        report.append(
            f"- {row['timestamp']}: {row['model']} → haiku "
            f"(save ${row['potential_savings']:.4f})"
        )

    report.append("\n## Model Usage Distribution\n")
    model_costs = df.groupby("model")["actual_cost"].sum()
    for model, cost in model_costs.items():
        pct = cost / model_costs.sum() * 100
        report.append(f"- {model}: ${cost:.2f} ({pct:.1f}%)")

    return "\n".join(report)


if __name__ == "__main__":
    df = create_sample_data(1000)
    report = generate_report(df)
    print(report)
```

---

## Exercises

### Simple: Basic DataFrame Operations

**Task:** Given API logs, calculate:
1. Total tokens per model
2. Average latency per model
3. Most active user

<details>
<summary>Solution</summary>

```python
import pandas as pd

# Assuming df is loaded
# 1. Total tokens per model
tokens_by_model = df.groupby("model")[["tokens_in", "tokens_out"]].sum()
tokens_by_model["total"] = tokens_by_model["tokens_in"] + tokens_by_model["tokens_out"]
print(tokens_by_model)

# 2. Average latency per model
avg_latency = df.groupby("model")["latency_ms"].mean()
print(avg_latency)

# 3. Most active user
most_active = df["user_id"].value_counts().idxmax()
print(f"Most active: {most_active}")
```
</details>

---

### Intermediate: Time Series Analysis

**Task:** Analyze usage patterns:
1. Calculate daily/weekly aggregates
2. Identify peak usage hours
3. Detect unusual spikes

<details>
<summary>Solution</summary>

```python
import pandas as pd

# Daily aggregates
daily = df.groupby(df["timestamp"].dt.date).agg({
    "tokens_in": "sum",
    "tokens_out": "sum",
    "cost": "sum"
})

# Weekly aggregates
weekly = df.groupby(df["timestamp"].dt.isocalendar().week).agg({
    "cost": "sum"
})

# Peak hours
df["hour"] = df["timestamp"].dt.hour
hourly = df.groupby("hour")["tokens_in"].sum()
peak_hour = hourly.idxmax()
print(f"Peak hour: {peak_hour}:00")

# Detect spikes (> 2 std from mean)
daily_costs = df.groupby(df["timestamp"].dt.date)["cost"].sum()
mean_cost = daily_costs.mean()
std_cost = daily_costs.std()
spikes = daily_costs[daily_costs > mean_cost + 2 * std_cost]
print(f"Spike days: {list(spikes.index)}")
```
</details>

---

### Advanced: Complete Analytics Dashboard

**Task:** Build a complete analytics module:
1. Load/save data from JSON/CSV
2. Calculate all metrics with caching
3. Generate formatted report
4. Export to Excel with multiple sheets

<details>
<summary>Solution</summary>

```python
import pandas as pd
from pathlib import Path

class LLMAnalytics:
    """Complete LLM usage analytics."""

    def __init__(self, data_path: str = None):
        self.df = None
        self._cache = {}
        if data_path:
            self.load(data_path)

    def load(self, path: str):
        """Load data from file."""
        path = Path(path)
        if path.suffix == ".csv":
            self.df = pd.read_csv(path, parse_dates=["timestamp"])
        elif path.suffix == ".json":
            self.df = pd.read_json(path)
        self._cache = {}

    def _calculate_costs(self):
        """Calculate costs if not already done."""
        if "cost" in self.df.columns:
            return

        pricing = {
            "claude-sonnet": (3.0, 15.0),
            "claude-opus": (15.0, 75.0),
            "claude-haiku": (0.25, 1.25),
        }

        def calc(row):
            p = pricing.get(row["model"], (3.0, 15.0))
            return (row["tokens_in"] * p[0] + row["tokens_out"] * p[1]) / 1e6

        self.df["cost"] = self.df.apply(calc, axis=1)

    def summary(self) -> dict:
        """Get summary statistics."""
        if "summary" in self._cache:
            return self._cache["summary"]

        self._calculate_costs()

        result = {
            "total_requests": len(self.df),
            "total_tokens": self.df["tokens_in"].sum() + self.df["tokens_out"].sum(),
            "total_cost": self.df["cost"].sum(),
            "avg_latency_ms": self.df["latency_ms"].mean(),
            "date_range": (self.df["timestamp"].min(), self.df["timestamp"].max()),
        }

        self._cache["summary"] = result
        return result

    def by_model(self) -> pd.DataFrame:
        """Aggregate by model."""
        self._calculate_costs()
        return self.df.groupby("model").agg({
            "tokens_in": "sum",
            "tokens_out": "sum",
            "cost": "sum",
            "latency_ms": "mean",
            "timestamp": "count"
        }).rename(columns={"timestamp": "requests"})

    def by_user(self) -> pd.DataFrame:
        """Aggregate by user."""
        self._calculate_costs()
        return self.df.groupby("user_id").agg({
            "cost": "sum",
            "timestamp": "count"
        }).rename(columns={"timestamp": "requests"}).sort_values("cost", ascending=False)

    def daily_trend(self) -> pd.DataFrame:
        """Daily usage trend."""
        self._calculate_costs()
        return self.df.groupby(self.df["timestamp"].dt.date).agg({
            "tokens_in": "sum",
            "tokens_out": "sum",
            "cost": "sum"
        })

    def export_excel(self, path: str):
        """Export all analytics to Excel."""
        with pd.ExcelWriter(path) as writer:
            # Summary sheet
            summary_df = pd.DataFrame([self.summary()])
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

            # By model
            self.by_model().to_excel(writer, sheet_name="By Model")

            # By user
            self.by_user().to_excel(writer, sheet_name="By User")

            # Daily trend
            self.daily_trend().to_excel(writer, sheet_name="Daily Trend")

        print(f"Exported to {path}")
```
</details>

---

## Pro Tips

### 1. Use Categorical for Models

```python
df["model"] = df["model"].astype("category")  # Less memory
```

### 2. Method Chaining

```python
result = (df
    .query("model == 'claude-sonnet'")
    .groupby("user_id")
    .agg({"cost": "sum"})
    .sort_values("cost", ascending=False)
    .head(10)
)
```

### 3. Efficient Date Operations

```python
# Extract date parts once
df["date"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour
df["weekday"] = df["timestamp"].dt.dayofweek
```

### 4. Memory-Efficient Loading

```python
# Specify dtypes to reduce memory
df = pd.read_csv("large_file.csv", dtype={
    "model": "category",
    "user_id": "category",
    "tokens_in": "int32",
    "tokens_out": "int32"
})
```

---

## Track B Complete!

You've learned:
- NumPy for embedding operations
- Pandas for usage analytics

Continue to [Track C: Web Integration](../../track-c-web-integration/) or return to [Module 1](../../../01-basic-api/).
