import fitz
import json
import os
import ollama

class DatasetBuilder:
    def __init__(self, folder, roots):
        self.folder = folder
        self.roots = roots
        self.files = self.get_pdf_files()
        self.model = "qwen2.5:7b"

    def get_pdf_files(self):
        files = []

        for file_name in os.listdir(self.folder):
            if file_name.endswith(".pdf"):
                full_path = self.folder + "/" + file_name

                files.append(full_path)

        return files

    def ask_ollama(self, prompt):
        response = ollama.generate(
            model=self.model,
            prompt=prompt
        )

        answer = response["response"]

        return answer.strip()

    def clean_word(self, dirty_word):
        symbols_to_remove = '.,!?;:()[]{}"«»-' + "'"

        cleaned = dirty_word

        for symbol in symbols_to_remove:
            cleaned = cleaned.replace(symbol, "")

        return cleaned

    def clean_block_text(self, block_text):
        cleaned_block = block_text.strip()

        cleaned_block = cleaned_block.replace("\n", " ")

        cleaned_block = cleaned_block.replace("\t", " ")

        while "  " in cleaned_block:
            cleaned_block = cleaned_block.replace("  ", " ")

        return cleaned_block

    def block_has_root(self, block_text):
        words = block_text.split()

        for one_word in words:
            cleaned_word = self.clean_word(one_word)

            lowered_word = cleaned_word.lower()

            for root in self.roots:
                if root in lowered_word:
                    return True

        return False

    def find_source_info(self, first_page_text):
        prompt = (
            "Найди название научной статьи и автора или авторов. "
            "Ищи только в тексте первой страницы. "
            "Ответь строго в таком виде:\n"
            "Название: ...\n"
            "Авторы: ...\n"
            "Если данных нет, напиши unknown.\n\n"
            + first_page_text[:3000]
        )

        answer = self.ask_ollama(prompt)

        title = "unknown"
        authors = "unknown"

        lines = answer.split("\n")

        for one_line in lines:
            line = one_line.strip()

            if line.startswith("Название:"):
                title = line.replace("Название:", "").strip()

            if line.startswith("Авторы:"):
                authors = line.replace("Авторы:", "").strip()

        source_data = {
            "title": title,
            "authors": authors
        }

        return source_data

    def read_pdf(self, pdf_path):
        document = fitz.open(pdf_path)

        found_blocks = []

        first_page_text = ""

        global_index = 0

        for page_number in range(len(document)):
            page = document[page_number]

            if page_number == 0:
                first_page_text = page.get_text()

            blocks = page.get_text("blocks")

            for one_block in blocks:
                block_text = one_block[4]

                cleaned_block = self.clean_block_text(block_text)

                if cleaned_block != "":
                    start_index = global_index

                    end_index = global_index + len(cleaned_block)

                    if self.block_has_root(cleaned_block):
                        block_data = {
                            "page": page_number + 1,
                            "type": "text",
                            "start_index": start_index,
                            "end_index": end_index,
                            "fragment": cleaned_block
                        }

                        found_blocks.append(block_data)

                    global_index = end_index + 1

        return found_blocks, first_page_text

    def save_result(self, file_name, source_data, result_blocks):
        output_data = {
            "file": file_name,
            "title": source_data["title"],
            "authors": source_data["authors"],
            "matches": result_blocks
        }

        output_file = open("dataset.jsonl", "a", encoding="utf-8")

        json_line = json.dumps(output_data, ensure_ascii=False)

        output_file.write(json_line + "\n")

        output_file.close()

    def run(self):
        output_file = open("dataset.jsonl", "w", encoding="utf-8")

        output_file.close()

        for one_pdf in self.files:
            found_blocks, first_page_text = self.read_pdf(one_pdf)

            source_data = self.find_source_info(first_page_text)

            self.save_result(one_pdf, source_data, found_blocks)


folder = "assets"

roots = [
    "существ",
    "единствен"
]

builder = DatasetBuilder(folder, roots)

builder.run()