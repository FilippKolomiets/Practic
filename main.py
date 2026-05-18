import fitz
import json
import os

class DatasetBuilder:
    def __init__(self, folder, roots):
        self.folder = folder
        self.roots = roots
        self.files = self.get_pdf_files()

    def get_pdf_files(self):
        files = []
        for file_name in os.listdir(self.folder):
            if file_name.endswith(".pdf"):
                full_path = self.folder + "/" + file_name
                files.append(full_path)
        return files

    def read_pdf(self, pdf_path):
        document = fitz.open(pdf_path)
        whole_text = ""
        for page_number in range(len(document)):
            page = document[page_number]
            whole_text = whole_text + page.get_text()
        return whole_text

    def clean_word(self, dirty_word):
        symbols_to_remove = '.,!?;:()[]{}"«»-' + "'"
        cleaned = dirty_word
        for symbol in symbols_to_remove:
            cleaned = cleaned.replace(symbol, "")
        return cleaned

    def process_text(self, raw_text):
        all_words = raw_text.split()
        matched_words = []
        for one_word in all_words:
            cleaned_word = self.clean_word(one_word)
            lowered_word = cleaned_word.lower()
            for root in self.roots:
                if root in lowered_word:
                    matched_words.append(lowered_word)
                    break
        return matched_words

    def save_result(self, file_name, result_words):
        output_data = {
            "file": file_name,
            "matches": result_words
        }
        output_file = open("dataset.jsonl", "a", encoding="utf-8")
        json_line = json.dumps(output_data, ensure_ascii=False)
        output_file.write(json_line + "\n")
        output_file.close()

    def run(self):
        for one_pdf in self.files:
            extracted_text = self.read_pdf(one_pdf)
            found_words = self.process_text(extracted_text)
            self.save_result(one_pdf, found_words)


folder = "assets"
roots = [
    "существ",
    "единствен"
]

builder = DatasetBuilder(folder, roots)
builder.run()