






import glob
import os
import re
import sys
def process_log_file(log_file_path):

    chunks = []
    with open(log_file_path, 'r', encoding='utf-8') as file:
        content = file.read()


        matches = []
        start_pos = 0
        while True:

            start_idx = content.find("Tool call to '", start_pos)
            if start_idx == -1:
                break


            returned_idx = content.find("returned:", start_idx)
            if returned_idx == -1:
                start_pos = start_idx + 1
                continue


            response_start = content.find("\n'", returned_idx)
            if response_start == -1:
                start_pos = start_idx + 1
                continue


            response_start += 2


            end_pos = response_start
            while True:
                line_end = content.find("\n", end_pos)
                if line_end == -1:
                    break


                line = content[end_pos:line_end].strip()
                if line == "'":

                    tool_type = re.search(r"Tool call to '([^']+)'", content[start_idx:returned_idx]).group(1)
                    args_part = content[start_idx:returned_idx + len("returned:")]
                    args_match = re.search(r"with arguments (\{[^}]+\})", args_part)
                    arguments = args_match.group(1) if args_match else "{}"
                    response = content[response_start:end_pos].strip()

                    matches.append((tool_type, arguments, response))
                    start_pos = line_end + 1
                    break

                end_pos = line_end + 1

            if end_pos == response_start:
                start_pos = start_idx + 1


        for tool_type, arguments, response in matches:

            if tool_type == 'extract_zip':
                continue


            query = ""
            if 'question' in arguments:
                query_match = re.search(r"'question': '([^']*)'", arguments)
                if query_match:
                    query = query_match.group(1)


            if tool_type in ['ask_search_agent', 'llm_query']:

                chunks.append(response.strip())
            elif tool_type in ['inspect_file_as_text', 'image_inspector', 'run_python_code']:

                if query:
                    chunks.append(f"Question: {query}\nAnswer: {response.strip()}")
                else:
                    chunks.append(response.strip())

    return chunks
def process_logs(num_files=None):

    Args:
        num_files: Number of files to process. If None or -1, process all files.

    if num_files is None:
        num_files = -1


    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(project_root, "data", "success_log")


    if not os.path.exists(log_dir):

        alt_paths = [
            os.path.join(project_root, "logs", "fail"),
            os.path.join(project_root, "logs"),
            os.path.join(project_root, "raw_logs")
        ]

        for path in alt_paths:
            if os.path.exists(path):
                log_dir = path
                break

    print(f"Searching for log files in: {log_dir}")


    all_log_files = glob.glob(os.path.join(log_dir, 'cmd_log_*.log'))
    if not all_log_files:

        all_log_files = glob.glob(os.path.join(log_dir, '*.log'))

    print(f"Found {len(all_log_files)} log files")


    all_log_files = sorted(all_log_files)


    log_files = all_log_files if num_files <= 0 else all_log_files[:num_files]
    actual_num_files = len(log_files)

    print(f"Processing {actual_num_files} files...")


    corpus_dir = os.path.join(project_root, 'corpus')
    os.makedirs(corpus_dir, exist_ok=True)


    corpus_path = os.path.join(corpus_dir, f'corpus_{actual_num_files}.txt')

    all_chunks = []


    for log_file in log_files:
        print(f"Processing {log_file}...")
        chunks = process_log_file(log_file)
        all_chunks.extend(chunks)


    with open(corpus_path, 'w', encoding='utf-8') as f:
        for i, chunk in enumerate(all_chunks, 1):
            f.write(f"--- Chunk {i} ---\n{chunk}\n\n")

    print(f"Processed {len(log_files)} log files and extracted {len(all_chunks)} chunks.")
    print(f"Chunks saved to {corpus_path}")

    return corpus_path
def main():

    num_files = -1


    if len(sys.argv) > 1:
        try:
            num_files = int(sys.argv[1])
            print(f"Will process {num_files} log files")
        except ValueError:
            print("Invalid number provided. Using all files.")
            num_files = -1

    process_logs(num_files)
if __name__ == "__main__":
    main()