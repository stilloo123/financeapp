# Complete Strategy Comparison

## The Question
**How to optimally fund a $500K mortgage at 3% over 25 years?**

Annual payment: $28,713.94

## Executive Summary

Tested across **75 rolling 25-year historical periods** (1926-2025):

| Strategy | Capital | Success Rate | Avg Payoff | vs Treasury | Best For |
|----------|---------|--------------|------------|-------------|----------|
| **Treasury Ladder** | $433K | 100% | 25 years | Baseline | Risk-averse ✅ |
| **Smart $380K** | $380K | 91% | 4 years | -$53K (12%) | Moderate risk 🏆 |
| **Smart $300K** | $300K | 71% | 6 years | -$133K (31%) | Higher risk 💰 |
| **Smart $250K** | $250K | 47% | 8 years | -$183K (42%) | High risk ⚡ |
| **Stock-only $241K** | $241K | 49% | 7 years | -$192K (44%) | Very high risk |

**Key Insight**: Any strategy requiring ≥$500K is pointless - just pay off the mortgage directly!

---

## The Strategies in Detail

### 1. Treasury Ladder (Risk-Free) ✅
Using actual October 2025 treasury rates (1yr: 3.70%, 5yr: 3.71%, 10yr: 4.11%, etc.)

- **Capital needed**: $433,032
- **Success rate**: 100% (guaranteed by US government)
- **Outcome**: Mortgage paid off in exactly 25 years
- **Savings vs. payoff**: $66,968 (13.4%)
- **Verdict**: **BEST risk-free option** - saves $67K with zero risk

---

### 2. Smart Withdrawal Strategy ⭐

**The Logic:**
1. Market DOWN (negative return)? → Withdraw from CASH (never sell stocks at a loss)
2. Market UP (positive return)? → Withdraw from STOCKS (if above $100K base, else cash)

This protects stocks during crashes while letting them compound.

Tested across ALL 75 historical 25-year periods (1926-2025):

#### Option A: $380K ($290K stocks + $90K cash) - **RECOMMENDED FOR MODERATE RISK** 🏆

- **Capital needed**: $380,000
- **Success rate**: 90.7% (68 out of 75 historical periods)
- **Average payoff time**: 4.2 years (when successful)
- **Savings vs. treasury**: $53,032 (12%)
- **Failed scenarios**: 7 periods (mostly Great Depression era)
- **Verdict**: **Best balance of success rate and capital efficiency**

#### Option B: $340K ($260K stocks + $80K cash)

- **Capital needed**: $340,000
- **Success rate**: 81.3% (61 out of 75 periods)
- **Average payoff time**: 5.3 years
- **Savings vs. treasury**: $93,032 (21%)
- **Failed scenarios**: 14 periods
- **Verdict**: Higher savings but ~1 in 5 chance of needing more capital

#### Option C: $300K ($240K stocks + $60K cash) - **BEST VALUE** 💰

- **Capital needed**: $300,000
- **Success rate**: 70.7% (53 out of 75 periods)
- **Average payoff time**: 6.1 years
- **Savings vs. treasury**: $133,032 (31%)
- **Failed scenarios**: 22 periods
- **Verdict**: Highest savings with acceptable risk (~30% chance of failure)

#### Option D: $250K ($200K stocks + $50K cash) - **HIGHEST RISK** ⚡

- **Capital needed**: $250,000
- **Success rate**: 46.7% (35 out of 75 periods) - **basically a coin flip**
- **Average payoff time**: 8.1 years (when successful)
- **Savings vs. treasury**: $183,032 (42%)
- **Failed scenarios**: 40 periods (53%)
- **Verdict**: Great savings when it works, but fails more than it succeeds

---

### 3. Stock-Only Strategy (100% stocks)

- **Capital needed**: $241,000
- **Success rate**: 49.3% (37 out of 75 periods)
- **Average payoff time**: 7.2 years (when successful)
- **Savings vs. treasury**: $192,032 (44%)
- **Verdict**: Similar to Smart $250K but without crash protection

---

## Risk/Reward Comparison

### Visual Breakdown

```
Success Rate vs. Capital Required:

100% ██████████ Treasury $433K (guaranteed)
 96% ████████▓▓ Smart $430K
 93% ████████▒▒ Smart $410K
 92% ████████░░ Smart $400K
 91% ████████   Smart $380K ← SWEET SPOT
 81% ███████░░░ Smart $340K
 71% ██████░░░░ Smart $300K ← BEST VALUE
 47% ████░░░░░░ Smart $250K (coin flip)
 49% ████░░░░░░ Stock-only $241K

      Savings vs. Treasury:
$0    $53K  $93K  $133K $183K $192K
```

---

## Historical Worst Case: 2000-2024

This period (dot-com crash + housing crisis) represents one of the worst scenarios:

| Strategy | Minimum Capital | Years | vs Treasury |
|----------|-----------------|-------|-------------|
| Smart Withdrawal | $490K | 8 | **-$57K** (costs MORE) |
| Treasury Ladder | $433K | 25 | Baseline |

**Key learning**: For worst-case scenarios, treasury ladder is superior. But 2000-2024 is only 1 out of 75 historical periods.

**Critical years (2000-2024 with $490K):**
- Year 1-3 (2000-2002): Used CASH during crashes (-9%, -12%, -22%)
- Stocks protected from forced selling
- Year 4-8 (2003-2008): Used STOCKS during recovery
- Paid off in year 8

---

## What Makes "Smart Withdrawal" Work?

The critical insight (identified by the user):

**WRONG approach** (what I initially coded):
```
if stocks > $100K base:
    withdraw from stocks  ← Sells during crashes!
else:
    withdraw from cash
```

**CORRECT approach** (user's insight):
```
if market is DOWN:
    withdraw from cash  ← Never sell at a loss!
else if stocks > $100K base:
    withdraw from stocks
else:
    withdraw from cash
```

**Why it matters:**
- 2000-2002: -9%, -12%, -22% returns
- WRONG: Withdraws from stocks → compounds the losses
- CORRECT: Uses cash → protects stock recovery potential

This single change is what enables the strategy to work with less capital.

---

## Recommendations by Risk Profile

### 🛡️ CONSERVATIVE (Risk-Averse)
**→ Treasury Ladder: $433K**
- ✅ 100% success rate across ALL scenarios
- ✅ Guaranteed outcome, zero stress
- ✅ Saves $67K vs. paying off mortgage
- ❌ Requires 25 years (no early payoff)
- ❌ Misses stock market upside

**Best for**: Retirees, those who can't afford any risk, peace-of-mind seekers

---

### ⚖️ MODERATE RISK
**→ Smart Withdrawal: $380K ($290K stocks + $90K cash)** 🏆
- ✅ 91% historical success rate
- ✅ Pays off in ~4 years on average
- ✅ Saves $53K vs. treasury (12%)
- ⚠️ 9% chance of needing more capital
- ❌ Lower savings than riskier options

**Best for**: Most people seeking balance between safety and returns

**Hedge option**: Keep an additional $110K in reserve earning 3.7%
- Total allocated: $490K (but only $380K committed)
- If markets crash badly in first 5 years → use reserve
- If markets do well → never need reserve, invest elsewhere
- Effective capital efficiency better than treasury

---

### 💰 CALCULATED RISK
**→ Smart Withdrawal: $300K ($240K stocks + $60K cash)**
- ✅ 71% historical success rate
- ✅ Pays off in ~6 years average
- ✅ Saves $133K vs. treasury (31%)
- ⚠️ 29% chance of needing more capital (roughly 1 in 3)
- ✅ Best "value" proposition (success rate × savings)

**Best for**: Younger investors, those with backup capital, moderate risk tolerance

---

### ⚡ HIGH RISK
**→ Smart Withdrawal: $250K ($200K stocks + $50K cash)**
- ⚠️ 47% success rate (basically a coin flip)
- ✅ Saves $183K vs. treasury when successful (42%)
- ✅ Pays off in ~8 years when successful
- ❌ Fails in 53% of historical scenarios
- ❌ Requires backup capital for ~half of scenarios

**Best for**: High net worth individuals who can afford failure, aggressive investors

---

## Bottom Line

### The Three-Tier Strategy

1. **100% Certainty → Treasury at $433K**
   - No risk, guaranteed outcome
   - Best choice if you value certainty above all

2. **~90% Certainty → Smart $380K** 🏆
   - Near-guaranteed success (91%)
   - Pays off in 4 years, saves $53K
   - **Best choice for most people**

3. **~70% Certainty → Smart $300K** 💰
   - Good odds (7 in 10)
   - Pays off in 6 years, saves $133K
   - Best choice if you can handle 30% risk

4. **~50% Certainty → Smart $250K** ⚡
   - Coin flip odds
   - Highest savings when successful
   - Only if you have backup capital

### The User's Key Insight

"If we had $500K we will just pay it off now right?"

This eliminates any strategy requiring ≥$500K. For the 2000-2024 worst case:
- Smart withdrawal needs $490K
- Treasury needs $433K
- **Treasury wins** by $57K

But 2000-2024 is only **1 out of 75** historical periods (worst 1.3%).

### Final Recommendation

**For most people**: Smart Withdrawal at **$380K**
- 91% success rate is excellent
- 4-year average payoff is fast
- $53K savings is meaningful
- Only 9% downside risk

**For very conservative**: Treasury at **$433K**
- 100% guaranteed
- Worth the extra $53K for zero risk

**For risk-takers with backup capital**: Smart at **$300K**
- 71% success rate is decent
- $133K savings is substantial
- Can afford the 29% chance of needing more
