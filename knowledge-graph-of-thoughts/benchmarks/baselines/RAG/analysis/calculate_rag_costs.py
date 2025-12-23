







import argparse
import json
import os
import subprocess
import tiktoken

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
def calculate_corpus_embedding_cost(corpus_path, cost_per_1k=0.0001):

    with open(corpus_path, 'r', encoding='utf-8') as f:
        text = f.read()


    encoding = tiktoken.encoding_for_model('text-embedding-ada-002')
    token_count = len(encoding.encode(text))


    cost = (token_count / 1000) * cost_per_1k

    return {
        'token_count': token_count,
        'cost_per_1k': cost_per_1k,
        'total_cost': cost
    }
def get_average_tokens_per_question(results_dir):


    cost_summary_file = None
    for file in os.listdir(results_dir):
        if file == 'cost_summary.json':
            cost_summary_file = os.path.join(results_dir, file)
            break
        elif file == 'cost_summary_detailed.json':
            cost_summary_file = os.path.join(results_dir, file)
            break

    if not cost_summary_file:
        raise FileNotFoundError(f"No cost summary file found in {results_dir}")

    with open(cost_summary_file, 'r') as f:
        cost_data = json.load(f)


    return {
        'total_tokens': cost_data.get('total_tokens', 0),
        'prompt_tokens': cost_data.get('prompt_tokens', 0),
        'completion_tokens': cost_data.get('completion_tokens', 0),
        'total_cost': cost_data.get('total_cost', 0),
        'num_questions': cost_data.get('num_questions', 0),
        'cost_per_question': cost_data.get('cost_per_question', 0)
    }
def calculate_query_embedding_cost(num_queries, avg_query_tokens=100, cost_per_1k=0.0001):

    total_tokens = num_queries * avg_query_tokens
    cost = (total_tokens / 1000) * cost_per_1k

    return {
        'num_queries': num_queries,
        'avg_query_tokens': avg_query_tokens,
        'total_tokens': total_tokens,
        'cost_per_1k': cost_per_1k,
        'total_cost': cost
    }
def estimate_full_dataset_cost(avg_cost_per_question, num_questions):

    total_cost = avg_cost_per_question * num_questions

    return {
        'avg_cost_per_question': avg_cost_per_question,
        'num_questions': num_questions,
        'total_cost': total_cost
    }
def count_gaia_questions(gaia_file):

    with open(gaia_file, 'r') as f:
        gaia_data = json.load(f)

    return len(gaia_data.get('rows', []))
def run_small_benchmark(index_path, gaia_file, num_questions=3, output_dir='results/cost_analysis'):


    if not os.path.isabs(output_dir):
        output_dir = os.path.join(PROJECT_ROOT, output_dir)

    os.makedirs(output_dir, exist_ok=True)


    benchmark_script = os.path.join(PROJECT_ROOT, "src/benchmark/rag_gaia_benchmark.py")

    cmd = [
        "python", benchmark_script,
        "--index_path", index_path,
        "--log_folder_base", output_dir,
        "--max_questions", str(num_questions),
        "--gaia_file", gaia_file
    ]


    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_ROOT + os.pathsep + env.get("PYTHONPATH", "")


    subprocess.run(cmd, check=True, env=env)


    result_dirs = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
    if not result_dirs:
        raise FileNotFoundError(f"No result directories found in {output_dir}")


    result_dirs.sort(key=lambda d: os.path.getctime(os.path.join(output_dir, d)), reverse=True)
    return os.path.join(output_dir, result_dirs[0])
def main():
    parser = argparse.ArgumentParser(description='Calculate costs for RAG approach')
    parser.add_argument('--corpus_path', type=str, default=os.path.join(PROJECT_ROOT, 'corpus/corpus_1.txt'),
                      help='Path to the corpus file')
    parser.add_argument('--index_path', type=str, default=os.path.join(PROJECT_ROOT, 'vector_db/corpus_1.txt_faiss_index'),
                      help='Path to the FAISS index')
    parser.add_argument('--gaia_file', type=str, default=os.path.join(PROJECT_ROOT, '../../datasets/GAIA/validation/merged_dataset.json'),
                      help='Path to the GAIA dataset file')
    parser.add_argument('--run_benchmark', action='store_true',
                      help='Run a small benchmark to get token usage statistics')
    parser.add_argument('--num_benchmark_questions', type=int, default=3,
                      help='Number of questions to run for the benchmark')
    parser.add_argument('--results_dir', type=str, default=None,
                      help='Path to existing benchmark results directory (if not running a new benchmark)')
    parser.add_argument('--prompt_cost_per_1k', type=float, default=0.00015,
                      help='Cost per 1K tokens for LLM prompts')
    parser.add_argument('--completion_cost_per_1k', type=float, default=0.0006,
                      help='Cost per 1K tokens for LLM completions')
    parser.add_argument('--embedding_cost_per_1k', type=float, default=0.0001,
                      help='Cost per 1K tokens for embeddings')

    args = parser.parse_args()


    corpus_results = calculate_corpus_embedding_cost(
        args.corpus_path,
        cost_per_1k=args.embedding_cost_per_1k
    )
    print("\n=== Corpus Embedding Cost ===")
    print(f"Corpus file: {args.corpus_path}")
    print(f"Total tokens: {corpus_results['token_count']:,}")
    print(f"Cost per 1K tokens: ${corpus_results['cost_per_1k']}")
    print(f"Total cost: ${corpus_results['total_cost']:.6f}")


    if args.run_benchmark:
        print("\nRunning small benchmark to estimate token usage...")
        results_dir = run_small_benchmark(
            args.index_path,
            args.gaia_file,
            num_questions=args.num_benchmark_questions
        )
    else:
        results_dir = args.results_dir

    benchmark_results = None
    if results_dir and os.path.exists(results_dir):
        print(f"\nUsing benchmark results from: {results_dir}")
        try:
            benchmark_results = get_average_tokens_per_question(results_dir)
        except Exception as e:
            print(f"Error getting benchmark results: {e}")


    total_questions = count_gaia_questions(args.gaia_file)
    print("\n=== GAIA Dataset ===")
    print(f"Total questions: {total_questions}")


    query_results = calculate_query_embedding_cost(
        total_questions,
        avg_query_tokens=100,
        cost_per_1k=args.embedding_cost_per_1k
    )
    print("\n=== Query Embedding Cost ===")
    print(f"Number of queries: {query_results['num_queries']}")
    print(f"Average tokens per query: {query_results['avg_query_tokens']}")
    print(f"Total tokens: {query_results['total_tokens']:,}")
    print(f"Cost per 1K tokens: ${query_results['cost_per_1k']}")
    print(f"Total cost: ${query_results['total_cost']:.6f}")


    if benchmark_results:
        avg_tokens_per_question = benchmark_results['total_tokens'] / max(1, benchmark_results['num_questions'])
        avg_prompt_tokens = benchmark_results['prompt_tokens'] / max(1, benchmark_results['num_questions'])
        avg_completion_tokens = benchmark_results['completion_tokens'] / max(1, benchmark_results['num_questions'])


        avg_cost_per_question = (
            (avg_prompt_tokens / 1000) * args.prompt_cost_per_1k +
            (avg_completion_tokens / 1000) * args.completion_cost_per_1k
        )

        dataset_results = estimate_full_dataset_cost(avg_cost_per_question, total_questions)

        print("\n=== LLM Processing Cost ===")
        print(f"Average tokens per question: {avg_tokens_per_question:.2f}")
        print(f"  - Prompt tokens: {avg_prompt_tokens:.2f}")
        print(f"  - Completion tokens: {avg_completion_tokens:.2f}")
        print(f"Average cost per question: ${avg_cost_per_question:.6f}")
        print(f"Total cost for {total_questions} questions: ${dataset_results['total_cost']:.6f}")


        total_cost = (
            corpus_results['total_cost'] +
            query_results['total_cost'] +
            dataset_results['total_cost']
        )

        print("\n=== Total RAG Cost ===")
        print(f"Corpus embedding: ${corpus_results['total_cost']:.6f} ({corpus_results['total_cost'] / total_cost * 100:.2f}%)")
        print(f"Query embeddings: ${query_results['total_cost']:.6f} ({query_results['total_cost'] / total_cost * 100:.2f}%)")
        print(f"LLM processing: ${dataset_results['total_cost']:.6f} ({dataset_results['total_cost'] / total_cost * 100:.2f}%)")
        print(f"TOTAL: ${total_cost:.6f}")


        results = {
            "corpus_embedding": corpus_results,
            "query_embedding": query_results,
            "llm_processing": {
                "avg_tokens_per_question": avg_tokens_per_question,
                "avg_prompt_tokens": avg_prompt_tokens,
                "avg_completion_tokens": avg_completion_tokens,
                "avg_cost_per_question": avg_cost_per_question,
                "num_questions": total_questions,
                "total_cost": dataset_results['total_cost']
            },
            "total_cost": total_cost,
            "cost_breakdown": {
                "corpus_embedding_pct": corpus_results['total_cost'] / total_cost * 100,
                "query_embedding_pct": query_results['total_cost'] / total_cost * 100,
                "llm_processing_pct": dataset_results['total_cost'] / total_cost * 100
            }
        }


        output_file = os.path.join(SCRIPT_DIR, "rag_cost_analysis.json")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed results saved to: {output_file}")
    else:
        print("\nWarning: No benchmark results available. Cannot estimate LLM processing cost.")
        print("Please either run a benchmark with --run_benchmark or provide --results_dir")
if __name__ == "__main__":
    main()