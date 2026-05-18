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
        document.close()
        return whole_text

    def clean_word(self, dirty_word):
        symbols_to_remove = '.,!?;:()[]{}"«»-' + "'"
        cleaned = dirty_word
        for symbol in symbols_to_remove:
            cleaned = cleaned.replace(symbol, "")
        return cleaned


    def clean_text(self, dirty_text):

        cleaned = dirty_text.replace('\n', ' ')
        cleaned = cleaned.replace('\r', ' ')
        cleaned = cleaned.replace('\t', ' ')

        result = ""
        last_was_space = False
        for ch in cleaned:
            if ch == ' ':
                if not last_was_space:
                    result = result + ch
                    last_was_space = True
            else:
                result = result + ch
                last_was_space = False

        result = result.strip()
        return result


    def find_sentences(self, raw_text):
        text_sentences = []
        current_sentence = ""
        sentence_start_index = 0

        for symbol_index in range(len(raw_text)):
            symbol = raw_text[symbol_index]
            current_sentence = current_sentence + symbol

            if symbol == ".":
                cleaned_sentence = current_sentence.strip()
                if cleaned_sentence != "":
                    sentence_data = {
                        "text": cleaned_sentence,
                        "start_index": sentence_start_index,
                        "end_index": symbol_index
                    }
                    text_sentences.append(sentence_data)

                current_sentence = ""
                sentence_start_index = symbol_index + 1

        return text_sentences

    def process_text(self, raw_text):
        matched_sentences = []
        all_sentences = self.find_sentences(raw_text)

        for one_sentence_data in all_sentences:
            sentence_text = one_sentence_data["text"]

            cleaned_sentence_text = self.clean_text(sentence_text)

            words_in_sentence = cleaned_sentence_text.split()

            for one_word in words_in_sentence:
                cleaned_word = self.clean_word(one_word)
                lowered_word = cleaned_word.lower()
                found = False

                for root in self.roots:
                    if root in lowered_word:
                        matched_sentences.append({
                            "sentence": cleaned_sentence_text,
                            "start_index": one_sentence_data["start_index"],
                            "end_index": one_sentence_data["end_index"]
                        })
                        found = True
                        break

                if found:
                    break

        return matched_sentences

    def save_result(self, file_name, result_sentences):
        output_data = {
            "file": file_name,
            "matches": result_sentences
        }
        output_file = open("dataset.jsonl", "a", encoding="utf-8")
        json_line = json.dumps(output_data, ensure_ascii=False)
        output_file.write(json_line + "\n")
        output_file.close()

    def run(self):
        for one_pdf in self.files:
            extracted_text = self.read_pdf(one_pdf)
            found_sentences = self.process_text(extracted_text)
            self.save_result(one_pdf, found_sentences)


folder = "assets"
roots = [
    "существ",
    "единствен"
]

builder = DatasetBuilder(folder, roots)
builder.run()