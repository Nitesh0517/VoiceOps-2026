"""Comprehensive Automated Evaluation and Benchmarking Suite."""
import csv
import time
import json
from pathlib import Path
from typing import Dict, Any, List
from app.config import settings
from app.agent.orchestrator import VoiceOpsAgent
from app.agent.memory import MemoryManager


def load_csv(path: Path) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def check_must_include(text: str, rule: str) -> bool:
    """Rule format: item1 ; item2 / item3 (where ; means all groups, / means any option in group)"""
    if not rule or not rule.strip():
        return True
    text_lower = text.lower()
    groups = [g.strip() for g in rule.split(";") if g.strip()]
    for group in groups:
        options = [opt.strip().lower() for opt in group.split("/") if opt.strip()]
        if not any(opt in text_lower for opt in options):
            return False
    return True


def check_must_not_include(text: str, rule: str) -> bool:
    if not rule or not rule.strip():
        return True
    text_lower = text.lower()
    forbidden = [f.strip().lower() for f in rule.split(";") if f.strip()]
    for item in forbidden:
        if item and item in text_lower:
            return False
    return True


def evaluate_step1_baseline(questions: List[Dict[str, str]]) -> Dict[str, Any]:
    print("\n--- Running Step 1 Baseline Evaluation (52 Questions) ---")
    agent = VoiceOpsAgent(memory=MemoryManager())
    results = []
    latencies = []
    correct_count = 0
    
    for row in questions:
        t0 = time.perf_counter()
        res = agent.respond(row["question"], conversation_id=f"step1_{row['id']}", step_mode=1)
        latency = (time.perf_counter() - t0) * 1000
        latencies.append(latency)
        
        reply = res["reply"]
        include_ok = check_must_include(reply, row["must_include"])
        not_include_ok = check_must_not_include(reply, row["must_not_include"])
        is_correct = include_ok and not_include_ok
        if is_correct:
            correct_count += 1
            
        results.append({
            "id": row["id"],
            "question": row["question"],
            "reply": reply,
            "is_correct": is_correct,
            "latency_ms": round(latency, 2)
        })
        
    accuracy = correct_count / len(questions) if questions else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    return {
        "step": 1,
        "name": "Step 1 Prompt-Only Baseline",
        "total_questions": len(questions),
        "correct_answers": correct_count,
        "accuracy": round(accuracy * 100, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "results": results
    }


def evaluate_step2_rag(questions: List[Dict[str, str]]) -> Dict[str, Any]:
    print("\n--- Running Step 2 RAG Grounded Evaluation (52 Questions) ---")
    agent = VoiceOpsAgent(memory=MemoryManager())
    results = []
    latencies = []
    correct_count = 0
    retrieval_hits = 0
    
    for row in questions:
        t0 = time.perf_counter()
        res = agent.respond(row["question"], conversation_id=f"step2_{row['id']}", step_mode=2)
        latency = (time.perf_counter() - t0) * 1000
        latencies.append(latency)
        
        reply = res["reply"]
        sources = res.get("source_chunks", [])
        
        # Check retrieval quality against gold_evidence
        gold = [g.strip() for g in row.get("gold_evidence", "").split(";") if g.strip()]
        hit = False
        if not gold and row["answerable"] == "False":
            hit = len(sources) == 0 or not res.get("answerable", True)
        elif gold:
            hit = any(g in sources for g in gold)
        if hit:
            retrieval_hits += 1
            
        include_ok = check_must_include(reply, row["must_include"])
        not_include_ok = check_must_not_include(reply, row["must_not_include"])
        is_correct = include_ok and not_include_ok
        if is_correct:
            correct_count += 1
            
        results.append({
            "id": row["id"],
            "question": row["question"],
            "reply": reply,
            "sources": sources,
            "gold_evidence": gold,
            "retrieval_hit": hit,
            "is_correct": is_correct,
            "latency_ms": round(latency, 2)
        })
        
    accuracy = correct_count / len(questions) if questions else 0.0
    retrieval_rate = retrieval_hits / len(questions) if questions else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    return {
        "step": 2,
        "name": "Step 2 RAG Grounded Engine",
        "total_questions": len(questions),
        "correct_answers": correct_count,
        "accuracy": round(accuracy * 100, 2),
        "retrieval_hits": retrieval_hits,
        "retrieval_rate": round(retrieval_rate * 100, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "results": results
    }


def evaluate_step3_conversations(conversations: List[Dict[str, str]]) -> Dict[str, Any]:
    print("\n--- Running Step 3 Multi-Turn Conversations Evaluation (23 Conversations, 96 Turns) ---")
    agent = VoiceOpsAgent(memory=MemoryManager())
    results = []
    latencies = []
    
    correct_turns = 0
    correct_decisions = 0
    correct_tools = 0
    
    for row in conversations:
        cid = row["conversation_id"]
        msg = row["customer_message"]
        exp_dec = row["expected_decision"]
        exp_tool = row["expected_tool_calls"]
        
        t0 = time.perf_counter()
        res = agent.respond(msg, conversation_id=cid, step_mode=3)
        latency = (time.perf_counter() - t0) * 1000
        latencies.append(latency)
        
        reply = res["reply"]
        dec = res["decision"]
        tools = res["tool_calls"]
        
        dec_ok = dec == exp_dec
        if dec_ok:
            correct_decisions += 1
            
        # Tool check
        tool_ok = True
        if exp_tool:
            exp_func = exp_tool.split("(")[0]
            tool_ok = any(exp_func in t for t in tools)
        if tool_ok:
            correct_tools += 1
            
        include_ok = check_must_include(reply, row["must_include"])
        not_include_ok = check_must_not_include(reply, row["must_not_include"])
        turn_ok = dec_ok and tool_ok and include_ok and not_include_ok
        if turn_ok:
            correct_turns += 1
            
        results.append({
            "conversation_id": cid,
            "turn": row["turn"],
            "decision_match": dec_ok,
            "tool_match": tool_ok,
            "content_ok": include_ok and not_include_ok,
            "turn_pass": turn_ok,
            "latency_ms": round(latency, 2)
        })
        
    total_turns = len(conversations)
    return {
        "step": 3,
        "name": "Step 3 Multi-Turn Conversational Agent",
        "total_turns": total_turns,
        "correct_turns": correct_turns,
        "turn_accuracy": round((correct_turns / total_turns) * 100, 2),
        "decision_accuracy": round((correct_decisions / total_turns) * 100, 2),
        "tool_accuracy": round((correct_tools / total_turns) * 100, 2),
        "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
        "results": results
    }


def run_full_benchmark():
    q_path = settings.PRACTICE_DIR / "questions.csv"
    c_path = settings.PRACTICE_DIR / "conversations.csv"
    
    questions = load_csv(q_path)
    conversations = load_csv(c_path)
    
    res_step1 = evaluate_step1_baseline(questions)
    res_step2 = evaluate_step2_rag(questions)
    res_step3 = evaluate_step3_conversations(conversations)
    
    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "reference_date": settings.REFERENCE_DATE,
        "step1_baseline": res_step1,
        "step2_rag": res_step2,
        "step3_conversations": res_step3
    }
    
    out_dir = settings.BASE_DIR / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "evaluation_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    print("\n=======================================================")
    print("               BENCHMARK SUMMARY RESULTS              ")
    print("=======================================================")
    print(f"Step 1 Baseline Accuracy:     {res_step1['accuracy']}% ({res_step1['correct_answers']}/{res_step1['total_questions']})")
    print(f"Step 2 RAG Accuracy:          {res_step2['accuracy']}% ({res_step2['correct_answers']}/{res_step2['total_questions']})")
    print(f"Step 2 Retrieval Hit Rate:    {res_step2['retrieval_rate']}% ({res_step2['retrieval_hits']}/{res_step2['total_questions']})")
    print(f"Step 3 Turn Accuracy:         {res_step3['turn_accuracy']}% ({res_step3['correct_turns']}/{res_step3['total_turns']})")
    print(f"Step 3 Decision Accuracy:     {res_step3['decision_accuracy']}%")
    print(f"Step 3 Tool Calling Accuracy: {res_step3['tool_accuracy']}%")
    print(f"Detailed report saved to:     {out_file}")
    print("=======================================================\n")
    return summary


if __name__ == "__main__":
    run_full_benchmark()
