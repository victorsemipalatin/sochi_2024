from transformers import BertTokenizer, BertForSequenceClassification, AutoTokenizer, AutoModel
import torch


def remove_spaces(arr): # удаление пустых элементов
    p = []
    for i, el in enumerate(arr):
        if len(el) == 0 or el == '\n' or el == '\t' or el == ' ':
            p.append(i)
    for el in reversed(p):
        arr.pop(el)
    return arr


def numero(string): # проверка строки на возможность содержания нумерованного заголовка
    try:
        num = string.split()[0]
        if "." in num:
            num = int(num.split(".")[-1])
        else:
            num = int(num)
        return num
    except:
        return None


def search_candidates(model: AutoModel, tokenizer: AutoTokenizer, threshold: float, device: str, text: str) -> list[str]: # выделение заголовков
    candidates = []
    lines = text.split("\n")
    rows = [row.strip().replace('_', ' ') for row in lines if len(row.strip()) > 0]
    batch_size = len(lines)
    for i in range(0, len(rows), len(lines)):
        batch = rows[i:i + batch_size]
        inputs = tokenizer(batch, max_length=32, truncation=True, padding=True, return_tensors='pt').to(device)
        outputs = model(**inputs)
        predictions = torch.softmax(outputs.logits, dim=-1)

        for j in range(len(batch)):
            phrase = tokenizer.decode(inputs['input_ids'][j].tolist(), skip_special_tokens=True)
            if len(phrase) != 0:
                try:
                    while phrase[0] in " -+.,;:><\t\n": # удаление мусорных символов из начала строки
                        phrase = phrase[1:]
                except:
                    pass
                try:
                    x = numero(phrase) # проверка строки на содержание нумерованного заголовка
                    y = numero(candidates[-1][0]) # проверка предыдущего заголовка на содержание нумерации
                except:
                    x = y = None
                if x == None or y == None:
                    if predictions[j][1] > threshold and sum(char.isalpha() for char in phrase) > 4: # если отсутсвует нумерация
                        candidates.append([phrase.strip(), j])
                elif x != None and y != None:
                    if predictions[j][1] > threshold and sum(char.isalpha() for char in phrase) > 4 or x == y + 1: # если есть упорядоченная нумерация, добавляем к заголовкам
                        candidates.append([phrase.strip(), j])

    for i in range(len(candidates) - 1, 0, -1):
        if candidates[i][0][0].lower() == candidates[i][0][0] and candidates[i][0][0].isalpha():
            if candidates[i][1] == candidates[i - 1][1] + 1:
                candidates[i - 1][0] += ' ' + candidates[i][0] # слияние разорванных заголовков
                candidates[i][0] = ''
            else:
                candidates[i][0] = ''
        elif candidates[i][0].upper() == candidates[i][0] and candidates[i - 1][0].upper() == candidates[i - 1][0]:
            if candidates[i][1] == candidates[i - 1][1] + 1:
                candidates[i - 1][0] += ' ' + candidates[i][0] # слияние разорванных заголовков
                candidates[i][0] = ''
    candidates = [cand[0] for cand in candidates if len(cand[0]) > 0]
    return candidates


def get_key_words(text):
    with torch.no_grad():
        candidates = search_candidates(model, tokenizer, threshold, device, text) # поиск заголовков
    return candidates
   

threshold = 0.9965 # <---- EXPERIMENT WITH THIS PARAMETER
tokenizer = BertTokenizer.from_pretrained("JamradisePalms/bert_sentence_classifier_tuned", num_labels=2,
                                      output_attentions=False, output_hidden_states=False)
model = BertForSequenceClassification.from_pretrained("JamradisePalms/bert_sentence_classifier_tuned")
# model.load_state_dict(torch.load(path_to_pt, weights_only=True))
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)
