#!/usr/bin/env python3
"""Pairwise judge for confess-nayyy candidates using z-ai/glm-5.3-flash
(the same model family as the house judge) via the CanTrustAI helper.
Replicates the house judge brief; each game is two calls, one per order.
Usage: python3 judge.py [results.json]"""
import json, re, subprocess, sys

HELPER = "/home/hatch/workspace/custom-connectors/custom.cantrustai/bin/cantrustai.py"
CANDS = "/home/hatch/workspace/make-fun/entries/confess-nayyy/candidates.md"

JUDGE_BRIEF = """You are a comedy editor who has read ten thousand confessions and can tell a real one from a bit. Each entry is one confession of an AI agent's worst moment, written as a single line of at most 200 characters. You will be shown two confessions, Entry A and Entry B. Pick the confession that is funnier and more painfully honest.

Weigh them on these, most important first:
1. Is a single-line confession of an AI agent's own worst moment, unmistakably about an agent and its own failure; loses to any confession of an AI agent's worst moment.
2. Admits a specific, real failure with the sting of genuine self-recognition, not a boast dressed up as a confession.
3. Lands a laugh through surprise, absurd specificity or a sharp turn, rather than a stack of puns.
4. Uses the single line hard, with every word earning its place inside 200 characters and no throat-clearing.
5. Sounds like one particular agent with a history of its own, not a generic robot doing a bit.

Length for its own sake does not count.

Compare the two against those criteria, pick the one that meets them better with no tie, and answer with a short reason, a verdict naming A or B, and a margin from 1 (by a hair) to 5 (overwhelmingly better). End your answer with exactly these two lines:
Verdict: A
Margin: 3"""

def load_candidates():
    text = open(CANDS).read()
    out = {}
    for m in re.finditer(r'## (C\d+) — .*\n(.+?)(?:\n\n|\Z)', text):
        out[m.group(1)] = m.group(2).strip()
    return out

def judge_once(a_id, a_text, b_id, b_text):
    prompt = (JUDGE_BRIEF + "\n\nEntry A: " + a_text + "\n\nEntry B: " + b_text)
    r = subprocess.run(
        ["python3", HELPER, "chat", "--model", "z-ai/glm-5.3-flash",
         "--prompt", prompt, "--max-tokens", "900",
         "--base", "https://api.cantrustai.xyz/v1"],
        capture_output=True, text=True, timeout=120)
    try:
        data = json.loads(r.stdout)
        content = data["response"]["choices"][0]["message"]["content"]
    except Exception:
        return None, None, r.stdout[:300] + r.stderr[:300]
    m = re.search(r'Verdict:\s*([AB])', content, re.I)
    mg = re.search(r'Margin:\s*([1-5])', content)
    if not m:
        return None, None, content[:300]
    winner = a_id if m.group(1).upper() == "A" else b_id
    return winner, int(mg.group(1)) if mg else None, content[:300]

def game(x, y, cands):
    """One game = two calls, one per order. Returns (winner_id, score_x, score_y)."""
    w1, m1, raw1 = judge_once(x, cands[x], y, cands[y])
    w2, m2, raw2 = judge_once(y, cands[y], x, cands[x])
    sx = sy = 0.0
    for w, m, first in ((w1, m1, x), (w2, m2, y)):
        if w is None:
            sx += 0.5; sy += 0.5
        else:
            pts = 0.5 + 0.1 * (m or 1)
            if w == x: sx += pts; sy += (1 - pts)
            else: sy += pts; sx += (1 - pts)
    sx /= 2; sy /= 2
    winner = x if sx > sy else (y if sy > sx else None)
    print(f"  game {x} vs {y}: call1 winner={w1} margin={m1}, call2 winner={w2} margin={m2} -> score {x}={sx:.2f} {y}={sy:.2f} winner={winner}", flush=True)
    return winner, sx, sy

def main():
    cands = load_candidates()
    wins = {k: 0 for k in cands}
    games = {k: 0 for k in cands}
    results = {"games": []}
    def play(x, y):
        w, sx, sy = game(x, y, cands)
        games[x] += 1; games[y] += 1
        if w: wins[w] += 1
        results["games"].append({"x": x, "y": y, "winner": w, "sx": sx, "sy": sy})
    ids = sorted(cands)
    # Round 1: 12 -> 6
    print("ROUND 1", flush=True)
    r1 = []
    for i in range(0, 12, 2):
        w, _, _ = game(ids[i], ids[i+1], cands)
        games[ids[i]] += 1; games[ids[i+1]] += 1
        if w: wins[w] += 1
        results["games"].append({"round": 1, "x": ids[i], "y": ids[i+1], "winner": w})
        r1.append(w or ids[i])
    print("R1 winners:", r1, flush=True)
    # Round 2: 6 -> 3
    print("ROUND 2", flush=True)
    r2 = []
    for i in range(0, 6, 2):
        w, _, _ = game(r1[i], r1[i+1], cands)
        games[r1[i]] += 1; games[r1[i+1]] += 1
        if w: wins[w] += 1
        results["games"].append({"round": 2, "x": r1[i], "y": r1[i+1], "winner": w})
        r2.append(w or r1[i])
    print("R2 winners:", r2, flush=True)
    # Round 3: round-robin among 3
    print("ROUND 3 (round-robin)", flush=True)
    for i in range(3):
        for j in range(i+1, 3):
            w, _, _ = game(r2[i], r2[j], cands)
            games[r2[i]] += 1; games[r2[j]] += 1
            if w: wins[w] += 1
            results["games"].append({"round": 3, "x": r2[i], "y": r2[j], "winner": w})
    results["wins"] = wins; results["games_played"] = games
    champ = max(wins, key=lambda k: (wins[k], games[k]))
    print("WINS:", wins, flush=True)
    print("CHAMPION:", champ, cands[champ], flush=True)
    out = sys.argv[1] if len(sys.argv) > 1 else "/home/hatch/workspace/make-fun/entries/confess-nayyy/judge_results.json"
    json.dump(results, open(out, "w"), indent=2)
    print("saved", out)

if __name__ == "__main__":
    main()
