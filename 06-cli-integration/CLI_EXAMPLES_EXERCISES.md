# CLI Tools for LLM-Assisted Development

**Focus:** Practical examples and exercises for Claude Code and Gemini CLI in engineering workflows.

---

## Claude Code Examples

### Example 1: Automated Design Review with Hooks

Create a pre-commit hook that uses Claude Code to review power electronics calculations before committing.

**Setup:**

```bash
# Create hook directory
mkdir -p .claude/hooks

# Create pre-commit hook
cat > .claude/hooks/pre-commit-review.sh << 'EOF'
#!/bin/bash
# Pre-commit hook for design calculation review

# Get staged Python files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

echo "Reviewing staged calculation files..."

for FILE in $STAGED_FILES; do
    # Check if file contains power electronics calculations
    if grep -q "def calculate\|efficiency\|loss\|ripple" "$FILE"; then
        echo "Reviewing: $FILE"

        # Use Claude Code to review
        claude -p "Review this power electronics calculation for:
1. Unit consistency (V, A, W, Ω)
2. Physical validity (positive losses, efficiency < 100%)
3. Missing error handling
4. Hardcoded values that should be parameters

File: $FILE

Only report issues, be concise." --file "$FILE"

        if [ $? -ne 0 ]; then
            echo "Review found issues in $FILE"
            exit 1
        fi
    fi
done

echo "Design review passed"
exit 0
EOF

chmod +x .claude/hooks/pre-commit-review.sh
```

**Register in Claude Code settings:**

```json
{
    "hooks": {
        "pre-commit": ".claude/hooks/pre-commit-review.sh"
    }
}
```

**Example Output:**

```
$ git commit -m "Add buck converter efficiency calculation"

Reviewing staged calculation files...
Reviewing: src/converters/buck.py

Issues found:
1. Line 45: Division by zero possible when i_load=0
2. Line 67: Hardcoded Rds_on=0.001 should be parameter
3. Line 89: efficiency can exceed 1.0 if p_loss negative

Review found issues in src/converters/buck.py
```

---

### Example 2: Custom Slash Command for Component Lookup

Create a slash command that searches component databases and datasheets.

**Setup:**

```bash
# Create commands directory
mkdir -p .claude/commands

# Create component lookup command
cat > .claude/commands/component.md << 'EOF'
---
description: Look up component specifications from datasheets
arguments:
  - name: part_number
    description: Component part number (e.g., BSC010N04LS)
  - name: parameter
    description: Specific parameter to find (optional)
---

Search for specifications of component: $ARGUMENTS.part_number

{{#if ARGUMENTS.parameter}}
Focus on finding: $ARGUMENTS.parameter
{{/if}}

Steps:
1. Search the project's datasheet directory for matching PDFs
2. If found, extract the requested specifications
3. Format as a table with: Parameter | Value | Unit | Conditions

If the datasheet is not in the project:
- Suggest the user download it
- Provide the likely manufacturer (Infineon, TI, ON Semi, etc.)

For MOSFETs, always include:
- Vds_max, Id_max, Rds_on (with Vgs condition), Qg, Qgd, Rth_jc

For inductors:
- Inductance, DCR, Isat, Irms, package size

Return results in markdown table format.
EOF
```

**Usage:**

```bash
# Look up MOSFET specs
claude /component BSC010N04LS

# Look up specific parameter
claude /component BSC010N04LS Rds_on

# Look up inductor
claude /component XAL7070-152
```

**Example Session:**

```
$ claude /component BSC010N04LS

Searching for BSC010N04LS specifications...

Found: datasheets/BSC010N04LS.pdf (Infineon)

| Parameter | Min | Typ | Max | Unit | Conditions |
|-----------|-----|-----|-----|------|------------|
| Vds_max | - | - | 40 | V | - |
| Vgs_max | - | - | ±20 | V | - |
| Id_25C | - | - | 100 | A | Tc=25°C |
| Id_100C | - | - | 70 | A | Tc=100°C |
| Rds_on | - | 1.0 | 1.4 | mΩ | Vgs=10V, Id=50A |
| Vgs_th | 1.5 | 2.5 | 3.5 | V | Vds=Vgs, Id=100µA |
| Qg | - | 15 | - | nC | Vds=20V, Vgs=10V |
| Qgd | - | 3.5 | - | nC | - |
| Rth_jc | - | 1.0 | - | K/W | - |

Package: TDSON-8
FOM (Rds×Qg): 15 mΩ·nC
```

---

## Claude Code Exercises

### Exercise 1: Build a Design Calculator Command (45 min)

**Objective:** Create a slash command that calculates buck converter parameters interactively.

**Requirements:**

1. Create `.claude/commands/buck-calc.md` with these capabilities:
   - Calculate duty cycle from Vin/Vout
   - Calculate inductance for target ripple
   - Calculate output capacitance for voltage ripple
   - Estimate efficiency from component parameters

2. The command should:
   - Accept specs as arguments or prompt interactively
   - Show all calculations with formulas
   - Validate inputs (Vout < Vin, positive values)
   - Suggest component values (standard E12/E24 series)

3. Test with:
   ```bash
   claude /buck-calc --vin 48 --vout 12 --iout 20 --fsw 200000
   ```

**Expected Output:**
```
Buck Converter Design Calculator
================================

Input Specifications:
- Vin: 48V
- Vout: 12V
- Iout: 20A
- fsw: 200kHz

Calculations:

1. Duty Cycle
   D = Vout/Vin = 12/48 = 0.25 (25%)

2. Inductor (30% ripple)
   ΔI = 0.3 × 20A = 6A
   L = (Vin-Vout) × D / (fsw × ΔI)
   L = (48-12) × 0.25 / (200000 × 6)
   L = 7.5µH

   Recommended: 10µH (standard value)
   Peak current: 20 + 6/2 = 23A
   Select inductor with Isat > 28A

3. Output Capacitor (50mV ripple)
   C = ΔI / (8 × fsw × ΔV)
   C = 6 / (8 × 200000 × 0.05)
   C = 75µF

   Recommended: 100µF ceramic (2× 47µF)

4. Efficiency Estimate
   (Requires MOSFET parameters - use /component to look up)
```

**Deliverables:**
- `.claude/commands/buck-calc.md`
- Test results for 3 different designs
- Screenshot of interactive session

---

### Exercise 2: Automated Test Generation (60 min)

**Objective:** Create a workflow that generates pytest tests for converter calculation functions.

**Requirements:**

1. Create a hook that triggers when calculation files are modified:
   ```bash
   .claude/hooks/generate-tests.sh
   ```

2. The hook should:
   - Detect modified calculation functions
   - Generate pytest tests covering:
     - Normal operation
     - Edge cases (zero current, max voltage)
     - Invalid inputs (negative values, Vout > Vin)
   - Include expected values with tolerances

3. Use Claude Code to analyze function signatures and generate appropriate tests

**Starter Code:**

```bash
#!/bin/bash
# .claude/hooks/generate-tests.sh

MODIFIED_FILES=$(git diff --name-only HEAD~1 | grep 'src/.*\.py$')

for FILE in $MODIFIED_FILES; do
    # Extract function names
    FUNCTIONS=$(grep -E "^def (calculate|compute)" "$FILE" | sed 's/def \([^(]*\).*/\1/')

    for FUNC in $FUNCTIONS; do
        TEST_FILE="tests/test_$(basename $FILE)"

        claude -p "Generate pytest tests for function '$FUNC' in $FILE.

Include tests for:
1. Typical operating point
2. Minimum load (1% of max)
3. Maximum input voltage
4. Invalid inputs (should raise ValueError)

Use pytest.approx() for float comparisons.
Follow existing test style in tests/ directory." --file "$FILE" >> "$TEST_FILE"
    done
done
```

**Example Generated Test:**

```python
# tests/test_buck_calculator.py

import pytest
from src.converters.buck_calculator import calculate_duty_cycle

class TestCalculateDutyCycle:
    """Tests for duty cycle calculation."""

    def test_typical_operation(self):
        """Test normal 48V to 12V conversion."""
        result = calculate_duty_cycle(v_in=48, v_out=12)
        assert result == pytest.approx(0.25, rel=0.01)

    def test_high_duty(self):
        """Test high duty cycle (36V to 24V)."""
        result = calculate_duty_cycle(v_in=36, v_out=24)
        assert result == pytest.approx(0.667, rel=0.01)

    def test_low_duty(self):
        """Test low duty cycle (60V to 5V)."""
        result = calculate_duty_cycle(v_in=60, v_out=5)
        assert result == pytest.approx(0.083, rel=0.01)

    def test_invalid_vout_greater_than_vin(self):
        """Test that Vout > Vin raises error."""
        with pytest.raises(ValueError, match="Vout must be less than Vin"):
            calculate_duty_cycle(v_in=12, v_out=48)

    def test_invalid_negative_voltage(self):
        """Test that negative voltage raises error."""
        with pytest.raises(ValueError):
            calculate_duty_cycle(v_in=-48, v_out=12)
```

**Deliverables:**
- `.claude/hooks/generate-tests.sh`
- Generated tests for at least 3 functions
- Passing pytest run screenshot

---

## Gemini CLI Examples

### Example 1: Batch Datasheet Analysis

Use Gemini CLI to analyze multiple datasheets and extract parameters into a comparison table.

**Script:**

```bash
#!/bin/bash
# analyze_datasheets.sh - Batch datasheet analysis with Gemini CLI

DATASHEET_DIR="./datasheets"
OUTPUT_FILE="component_comparison.md"

# Initialize output
cat > "$OUTPUT_FILE" << 'EOF'
# Component Comparison Table

| Part Number | Manufacturer | Vds (V) | Id (A) | Rds_on (mΩ) | Qg (nC) | FOM |
|-------------|--------------|---------|--------|-------------|---------|-----|
EOF

# Process each PDF
for PDF in "$DATASHEET_DIR"/*.pdf; do
    FILENAME=$(basename "$PDF" .pdf)
    echo "Processing: $FILENAME"

    # Use Gemini to extract parameters
    RESULT=$(gemini -f "$PDF" << 'PROMPT'
Extract these MOSFET parameters from the datasheet:
- Part number
- Manufacturer
- Vds_max (V)
- Id_max at 25°C (A)
- Rds_on typical (mΩ) at Vgs=10V
- Qg total (nC)

Return ONLY a single line in this exact format:
PART|MANUFACTURER|VDS|ID|RDSON|QG

No other text or explanation.
PROMPT
)

    # Parse result and calculate FOM
    if [[ "$RESULT" =~ ^[A-Z0-9] ]]; then
        IFS='|' read -r PART MFG VDS ID RDSON QG <<< "$RESULT"
        FOM=$(echo "scale=1; $RDSON * $QG" | bc)
        echo "| $PART | $MFG | $VDS | $ID | $RDSON | $QG | $FOM |" >> "$OUTPUT_FILE"
    else
        echo "  Warning: Could not parse $FILENAME"
    fi
done

echo ""
echo "Comparison table saved to $OUTPUT_FILE"
cat "$OUTPUT_FILE"
```

**Usage:**

```bash
chmod +x analyze_datasheets.sh
./analyze_datasheets.sh
```

**Example Output:**

```markdown
# Component Comparison Table

| Part Number | Manufacturer | Vds (V) | Id (A) | Rds_on (mΩ) | Qg (nC) | FOM |
|-------------|--------------|---------|--------|-------------|---------|-----|
| BSC010N04LS | Infineon | 40 | 100 | 1.0 | 15 | 15.0 |
| CSD18540Q5B | TI | 60 | 100 | 1.8 | 18 | 32.4 |
| IPD90N04S4L | Infineon | 40 | 120 | 0.9 | 12 | 10.8 |
| NVMFS5C604NL | ON Semi | 40 | 90 | 1.2 | 14 | 16.8 |
```

---

### Example 2: Interactive Design Assistant

Create a conversational design session using Gemini CLI with context persistence.

**Script:**

```bash
#!/bin/bash
# design_session.sh - Interactive converter design with Gemini CLI

SESSION_FILE="/tmp/gemini_design_session.txt"

# Initialize session with system context
cat > "$SESSION_FILE" << 'EOF'
You are a power electronics design assistant. You help engineers design DC-DC converters.

Current design context:
- Topology: Not specified
- Input voltage: Not specified
- Output voltage: Not specified
- Output current: Not specified
- Switching frequency: Not specified

When the user provides specifications, update the context and provide:
1. Calculated parameters (duty cycle, ripple, etc.)
2. Component recommendations
3. Potential issues to watch for

Always show your calculations with formulas.
EOF

echo "Power Electronics Design Assistant"
echo "==================================="
echo "Type 'quit' to exit, 'reset' to start over"
echo ""

while true; do
    read -p "You: " USER_INPUT

    case "$USER_INPUT" in
        quit|exit)
            echo "Session ended."
            break
            ;;
        reset)
            # Reset session context
            cat > "$SESSION_FILE" << 'EOF'
You are a power electronics design assistant...
EOF
            echo "Session reset."
            continue
            ;;
        "")
            continue
            ;;
    esac

    # Append user input to session
    echo -e "\nUser: $USER_INPUT" >> "$SESSION_FILE"

    # Get response from Gemini
    RESPONSE=$(gemini -f "$SESSION_FILE" -p "Continue the conversation. Respond to the user's latest message.")

    # Display and save response
    echo -e "\nAssistant: $RESPONSE\n"
    echo -e "\nAssistant: $RESPONSE" >> "$SESSION_FILE"
done
```

**Example Session:**

```
$ ./design_session.sh

Power Electronics Design Assistant
===================================
Type 'quit' to exit, 'reset' to start over

You: I need to design a buck converter: 48V to 12V, 20A output
Assistant: Great! Let me help you design this buck converter.

**Design Parameters:**
- Vin: 48V
- Vout: 12V
- Iout: 20A
- Pout: 240W

**Calculated Values:**

1. **Duty Cycle**
   D = Vout/Vin = 12/48 = 0.25 (25%)

2. **Inductor Selection** (assuming 200kHz, 30% ripple)
   �I = 0.3 � 20A = 6A
   L = (48-12) � 0.25 / (200kHz � 6A) = 7.5�H

   Recommend: 10�H, Isat > 25A

3. **Key Considerations:**
   - Need 60V MOSFETs (48V + margin)
   - Watch dead time for efficiency
   - Consider current mode control for stability

What switching frequency would you like to use?

You: 200kHz
Assistant: At 200kHz with 10µH inductor:

**Updated Calculations:**
- Ripple current: ΔI = (48-12) × 0.25 / (200kHz × 10µH) = 4.5A
- Peak current: 20 + 4.5/2 = 22.25A
- Ripple ratio: 4.5/20 = 22.5% ✓

**Output Capacitor** (for 50mV ripple):
- C = ΔI / (8 × fsw × ΔV) = 4.5 / (8 × 200kHz × 0.05V)
- C = 56µF minimum
- Recommend: 100µF ceramic (2× 47µF in parallel)

Would you like me to recommend specific MOSFETs?
```

---

## Gemini CLI Exercises

### Exercise 1: Parallel Component Analysis (45 min)

**Objective:** Create a script that analyzes multiple datasheets in parallel using Gemini CLI.

**Requirements:**

1. Create `parallel_analysis.sh` that:
   - Processes multiple PDFs concurrently (using `&` and `wait`)
   - Extracts parameters from each datasheet
   - Computes derived metrics (FOM, thermal resistance)
   - Generates a ranked comparison table

2. Handle errors gracefully:
   - Skip files that fail to parse
   - Report which files had issues
   - Continue processing remaining files

3. Output formats:
   - Markdown table (default)
   - CSV export option
   - JSON for programmatic use

**Starter Code:**

```bash
#!/bin/bash
# parallel_analysis.sh

MAX_PARALLEL=4
OUTPUT_FORMAT="${1:-markdown}"

process_datasheet() {
    local PDF="$1"
    local TEMP_FILE=$(mktemp)

    # Call Gemini to extract parameters
    gemini -f "$PDF" -p "Extract MOSFET parameters..." > "$TEMP_FILE"

    # Parse and return result
    cat "$TEMP_FILE"
    rm "$TEMP_FILE"
}

# Process files in parallel with limit
PIDS=()
for PDF in datasheets/*.pdf; do
    process_datasheet "$PDF" &
    PIDS+=($!)

    # Limit parallel processes
    if [ ${#PIDS[@]} -ge $MAX_PARALLEL ]; then
        wait ${PIDS[0]}
        PIDS=("${PIDS[@]:1}")
    fi
done

# Wait for remaining
wait
```

**Test Cases:**
1. Process 5 datasheets with MAX_PARALLEL=2
2. Include one corrupted PDF (should skip gracefully)
3. Generate all three output formats

**Deliverables:**
- `parallel_analysis.sh` script
- Sample output in each format
- Performance comparison (parallel vs sequential)

---

### Exercise 2: Design Documentation Generator (60 min)

**Objective:** Create a tool that generates design documentation from code and calculations.

**Requirements:**

1. Create `generate_docs.sh` that:
   - Scans Python calculation files
   - Extracts function docstrings and formulas
   - Generates markdown documentation
   - Includes example calculations

2. Use Gemini to:
   - Explain complex formulas in plain English
   - Generate usage examples
   - Create block diagrams (as ASCII art)
   - Add engineering notes and warnings

3. Documentation structure:
   ```markdown
   # Function Name

   ## Description
   [From docstring + Gemini enhancement]

   ## Formula
   [LaTeX or ASCII math]

   ## Parameters
   | Name | Type | Unit | Description |

   ## Example
   [Generated calculation]

   ## Engineering Notes
   [Gemini-generated considerations]
   ```

**Script Template:**

```bash
#!/bin/bash
# generate_docs.sh

SRC_DIR="./src"
DOC_DIR="./docs/api"

mkdir -p "$DOC_DIR"

for PY_FILE in "$SRC_DIR"/**/*.py; do
    # Extract functions
    FUNCTIONS=$(grep -E "^def " "$PY_FILE" | sed 's/def \([^(]*\).*/\1/')

    for FUNC in $FUNCTIONS; do
        echo "Documenting: $FUNC"

        # Use Gemini to generate documentation
        gemini -f "$PY_FILE" -p "Generate documentation for function '$FUNC'.

Include:
1. Clear description of what it calculates
2. The mathematical formula used
3. Parameter table with units
4. Example calculation with realistic values
5. Engineering considerations (assumptions, limitations)

Format as markdown." > "$DOC_DIR/${FUNC}.md"
    done
done

echo "Documentation generated in $DOC_DIR"
```

**Example Output:**

```markdown
# calculate_inductor_ripple

## Description
Calculates the peak-to-peak inductor current ripple in a buck converter
operating in continuous conduction mode (CCM).

## Formula
```
ΔI = (Vin - Vout) × D / (fsw × L)
```

Where:
- ΔI = Peak-to-peak ripple current (A)
- D = Duty cycle = Vout/Vin
- fsw = Switching frequency (Hz)
- L = Inductance (H)

## Parameters

| Name | Type | Unit | Description |
|------|------|------|-------------|
| v_in | float | V | Input voltage |
| v_out | float | V | Output voltage |
| f_sw | float | Hz | Switching frequency |
| l_value | float | H | Inductance |

## Example

```python
# 48V to 12V buck at 200kHz with 10µH inductor
ripple = calculate_inductor_ripple(
    v_in=48,
    v_out=12,
    f_sw=200e3,
    l_value=10e-6
)
# Result: 4.5 A peak-to-peak
```

## Engineering Notes

- Formula assumes CCM operation; verify I_valley > 0
- Actual ripple may be higher due to inductance drop at DC bias
- Consider core saturation: I_peak should be < 80% of I_sat
- Temperature affects inductance: recheck at operating temperature
```

**Deliverables:**
- `generate_docs.sh` script
- Generated documentation for at least 5 functions
- Screenshot of documentation in markdown viewer

---

## Summary

| Tool | Strengths | Best For |
|------|-----------|----------|
| **Claude Code** | Deep code understanding, hooks, slash commands | Interactive development, code review, test generation |
| **Gemini CLI** | Fast batch processing, file handling | Document analysis, bulk operations, scripting |

**Integration Tips:**
- Use Claude Code for interactive design sessions
- Use Gemini CLI for batch processing and automation
- Combine both in CI/CD pipelines
- Store context/history for multi-turn interactions
