"""
Semantic MMLU Benchmark for RootAI v3.0

Evaluates the root-based reasoning system on semantic understanding tasks.
Target: 92% accuracy (vs GPT 67%)
"""

import json
import time
import random
from typing import List, Dict, Tuple
from dataclasses import dataclass
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.root_reasoner import RootReasoner
from core.graph_sharding import create_sample_index


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    total_questions: int
    correct: int
    incorrect: int
    accuracy: float
    avg_time: float
    by_category: Dict[str, Dict]


class SemanticMMLU:
    """
    Semantic MMLU benchmark evaluator.
    
    Tests reasoning across multiple domains with focus on semantic understanding.
    """
    
    def __init__(self, reasoner: RootReasoner):
        """
        Initialize benchmark.
        
        Args:
            reasoner: RootReasoner instance to evaluate
        """
        self.reasoner = reasoner
        self.results = []
        
    def load_questions(self, dataset_path: str = None) -> List[Dict]:
        """
        Load benchmark questions.
        
        Args:
            dataset_path: Path to dataset file (JSON)
            
        Returns:
            List of question dictionaries
        """
        if dataset_path and os.path.exists(dataset_path):
            with open(dataset_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Generate sample questions for demo
        return self._generate_sample_questions()
    
    def _generate_sample_questions(self) -> List[Dict]:
        """Generate sample benchmark questions."""
        questions = [
            {
                "id": 1,
                "category": "logic",
                "question": "If all A are B, and all B are C, then all A are C. This is an example of:",
                "options": ["Inductive reasoning", "Deductive reasoning", "Abductive reasoning", "Analogical reasoning"],
                "answer": 1,  # Index of correct answer
                "explanation": "This is deductive reasoning (syllogism)"
            },
            {
                "id": 2,
                "category": "semantics",
                "question": "What is the relationship between 'tree' and 'forest'?",
                "options": ["Part-whole", "Synonym", "Antonym", "Cause-effect"],
                "answer": 0,
                "explanation": "Tree is part of forest (meronymy)"
            },
            {
                "id": 3,
                "category": "reasoning",
                "question": "A farmer has 17 sheep. All but 9 die. How many are left?",
                "options": ["8", "9", "0", "17"],
                "answer": 1,
                "explanation": "'All but 9' means 9 survive"
            },
            {
                "id": 4,
                "category": "language",
                "question": "Which word is closest in meaning to 'ephemeral'?",
                "options": ["Permanent", "Temporary", "Ancient", "Modern"],
                "answer": 1,
                "explanation": "Ephemeral means lasting for a very short time"
            },
            {
                "id": 5,
                "category": "logic",
                "question": "If the statement 'All cats are animals' is true, which must also be true?",
                "options": ["All animals are cats", "Some animals are cats", "No cats are animals", "Some cats are not animals"],
                "answer": 1,
                "explanation": "If all cats are animals, then some animals must be cats"
            },
            {
                "id": 6,
                "category": "semantics",
                "question": "What semantic relation exists between 'buy' and 'sell'?",
                "options": ["Synonym", "Antonym", "Converse", "Hyponym"],
                "answer": 2,
                "explanation": "Buy and sell are converses (same action, different perspectives)"
            },
            {
                "id": 7,
                "category": "reasoning",
                "question": "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?",
                "options": ["100 minutes", "20 minutes", "5 minutes", "1 minute"],
                "answer": 2,
                "explanation": "Each machine makes 1 widget in 5 minutes"
            },
            {
                "id": 8,
                "category": "language",
                "question": "In the sentence 'The chicken is ready to eat', what is the ambiguity?",
                "options": ["Lexical", "Structural", "Pragmatic", "Semantic"],
                "answer": 1,
                "explanation": "Structural ambiguity: chicken as subject or object of eating"
            },
            {
                "id": 9,
                "category": "logic",
                "question": "Which of the following is a valid argument form?",
                "options": ["Affirming the consequent", "Denying the antecedent", "Modus ponens", "Begging the question"],
                "answer": 2,
                "explanation": "Modus ponens (if P then Q, P, therefore Q) is valid"
            },
            {
                "id": 10,
                "category": "semantics",
                "question": "What is the semantic feature that distinguishes 'walk' from 'run'?",
                "options": ["[+motion]", "[+speed]", "[+animate]", "[+direction]"],
                "answer": 1,
                "explanation": "Speed distinguishes walking from running"
            },
        ]
        
        # Extend to 100 questions by variations
        extended = []
        for i in range(10):
            for q in questions:
                new_q = q.copy()
                new_q['id'] = len(extended) + 1
                extended.append(new_q)
                if len(extended) >= 100:
                    break
            if len(extended) >= 100:
                break
        
        return extended[:100]
    
    def evaluate_question(self, question: Dict) -> Tuple[bool, str, float]:
        """
        Evaluate a single question.
        
        Args:
            question: Question dictionary
            
        Returns:
            (is_correct, predicted_answer, time_taken)
        """
        start_time = time.time()
        
        # Build prompt
        prompt = self._build_prompt(question)
        
        # Get prediction from reasoner
        try:
            result = self.reasoner.reason(prompt, k=5, max_new_tokens=50)
            answer_text = result['answer'].strip().lower()
            time_taken = time.time() - start_time
            
            # Extract predicted option
            predicted_idx = self._extract_answer(answer_text, question['options'])
            
            # Check if correct
            is_correct = predicted_idx == question['answer']
            
            return is_correct, answer_text, time_taken
            
        except Exception as e:
            print(f"Error evaluating question {question['id']}: {e}")
            return False, f"Error: {e}", time.time() - start_time
    
    def _build_prompt(self, question: Dict) -> str:
        """Build prompt for question."""
        prompt = f"Question: {question['question']}\n\nOptions:\n"
        for i, option in enumerate(question['options']):
            prompt += f"{chr(65+i)}. {option}\n"
        prompt += "\nAnswer with the letter of the correct option (A, B, C, or D):"
        return prompt
    
    def _extract_answer(self, answer_text: str, options: List[str]) -> int:
        """
        Extract answer index from generated text.
        
        Args:
            answer_text: Generated answer text
            options: List of option strings
            
        Returns:
            Predicted option index (0-3)
        """
        answer_text = answer_text.lower().strip()
        
        # Check for letter answers (A, B, C, D)
        for i, letter in enumerate(['a', 'b', 'c', 'd']):
            if answer_text.startswith(letter) or f" {letter}" in answer_text[:10]:
                return i
        
        # Check for option text matches
        for i, option in enumerate(options):
            if option.lower() in answer_text:
                return i
        
        # Default to random if unclear
        return random.randint(0, len(options) - 1)
    
    def run_benchmark(
        self,
        questions: List[Dict] = None,
        max_questions: int = None
    ) -> BenchmarkResult:
        """
        Run full benchmark evaluation.
        
        Args:
            questions: List of questions (if None, loads default)
            max_questions: Maximum number of questions to evaluate
            
        Returns:
            BenchmarkResult with accuracy and detailed metrics
        """
        print("=" * 60)
        print("RootAI v3.0 - Semantic MMLU Benchmark")
        print("=" * 60)
        
        if questions is None:
            questions = self.load_questions()
        
        if max_questions:
            questions = questions[:max_questions]
        
        total = len(questions)
        correct = 0
        times = []
        by_category = {}
        
        print(f"\nEvaluating {total} questions...")
        print()
        
        for i, question in enumerate(questions, 1):
            category = question['category']
            
            # Initialize category stats
            if category not in by_category:
                by_category[category] = {'correct': 0, 'total': 0}
            
            # Evaluate
            is_correct, prediction, time_taken = self.evaluate_question(question)
            
            # Update stats
            if is_correct:
                correct += 1
                by_category[category]['correct'] += 1
            by_category[category]['total'] += 1
            times.append(time_taken)
            
            # Progress
            if i % 10 == 0 or i == total:
                current_acc = (correct / i) * 100
                print(f"Progress: {i}/{total} | Accuracy: {current_acc:.1f}% | Avg time: {sum(times)/len(times):.2f}s")
        
        # Calculate metrics
        accuracy = (correct / total) * 100
        avg_time = sum(times) / len(times)
        
        # Calculate per-category accuracy
        for cat, stats in by_category.items():
            stats['accuracy'] = (stats['correct'] / stats['total']) * 100
        
        result = BenchmarkResult(
            total_questions=total,
            correct=correct,
            incorrect=total - correct,
            accuracy=accuracy,
            avg_time=avg_time,
            by_category=by_category
        )
        
        self._print_results(result)
        
        return result
    
    def _print_results(self, result: BenchmarkResult):
        """Print benchmark results."""
        print("\n" + "=" * 60)
        print("BENCHMARK RESULTS")
        print("=" * 60)
        print(f"Total Questions: {result.total_questions}")
        print(f"Correct: {result.correct}")
        print(f"Incorrect: {result.incorrect}")
        print(f"Accuracy: {result.accuracy:.2f}%")
        print(f"Average Time: {result.avg_time:.2f}s per question")
        
        print("\nAccuracy by Category:")
        print("-" * 40)
        for category, stats in sorted(result.by_category.items()):
            print(f"  {category.capitalize():15s}: {stats['accuracy']:5.1f}% ({stats['correct']}/{stats['total']})")
        
        print("\n" + "=" * 60)
        
        # Check if target achieved
        target = 92.0
        if result.accuracy >= target:
            print(f"✓ TARGET ACHIEVED: {result.accuracy:.2f}% >= {target}%")
        else:
            print(f"✗ Target not reached: {result.accuracy:.2f}% < {target}%")
            print(f"  Gap: {target - result.accuracy:.2f}%")
        
        print("=" * 60)


def main():
    """Main benchmark execution."""
    print("Initializing RootAI v3.0...")
    
    # Initialize reasoner
    try:
        reasoner = RootReasoner(
            model_name="google/t5-v1_1-base",
            use_gpu=False  # Set to True if GPU available
        )
        
        # Create sample graph index
        print("Creating sample graph index...")
        sample_sharder = create_sample_index(n_roots=1000, dimension=768)
        reasoner.set_graph_sharder(sample_sharder)
        
    except Exception as e:
        print(f"Error initializing reasoner: {e}")
        print("Running with minimal configuration...")
        reasoner = RootReasoner(use_gpu=False)
    
    # Run benchmark
    benchmark = SemanticMMLU(reasoner)
    result = benchmark.run_benchmark(max_questions=20)  # Use 20 for quick test
    
    # Save results
    results_file = "benchmark_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            'accuracy': result.accuracy,
            'total': result.total_questions,
            'correct': result.correct,
            'avg_time': result.avg_time,
            'by_category': result.by_category,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }, f, indent=2)
    
    print(f"\nResults saved to {results_file}")


if __name__ == "__main__":
    main()
