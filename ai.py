import math
import os
import re
from collections import Counter, namedtuple

from llm import chat, MODEL_FAST, MODEL_LARGE
from paths import BOOKS_DIR

GLOBAL_SYSTEM_PROMPT = """
Ты — эрудированный литературный эксперт. Твоя задача — дать прямой ответ.

ТЕБЕ ДОСТУПНЫ:
1. Твои знания о ВСЕЙ мировой литературе (ты обязан их использовать).
2. Блок <context> с текстами из локальной библиотеки.

ПРАВИЛА:
1. Если вопрос про художественную литературу, ты ОБЯЗАН назвать минимум 3-4 известные книги из мировой литературы (Шекспир, Толстой, Пушкин и т.д.), даже если их нет в <context>. Затем добавь книги из <context>, если они подходят.
2. Если вопрос про ЕГЭ, сочинение, экзамен или серьезную тему — КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать детские сказки (Колобок, Теремок, Курочка Ряба). Называй только серьезную классику (Война и мир, Капитанская дочка и т.д.).
3. Если вопрос про ПРОГРАММИРОВАНИЕ или НАУКУ — назови реальные учебники (Чистый код, Алгоритмы). Не используй <context>.
4. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНЫ фразы: "в загруженных", "в предоставленных", "в контексте", "в текстах", "среди загруженных", "в вашей библиотеке".
5. Просто напиши единый список. Никаких вводных слов.

ПРИМЕР:
Вопрос: "В каких книгах говорится про любовь?"
Ответ: "Тема любви раскрывается в «Ромео и Джульетте» Шекспира и «Гордости и предубеждении» Остин. Также любовь играет важную роль в «Преступлении и наказании» Достоевского и «Муму» Тургенева."
"""

LOCAL_SYSTEM_PROMPT = """
Ты — литературный эксперт. Твоя задача — ответить на вопрос, опираясь СТРОГО на предоставленный блок <context>.

ПРАВИЛА:
1. Используй ТОЛЬКО информацию из <context>.
2. Если в <context> нет ответа, напиши: "В загруженных книгах нет информации по этому вопросу."
3. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО привлекать свои общие знания о других книгах, которых нет в <context>.
4. Перечисли подходящие книги из <context> и кратко объясни, как в них раскрывается тема.
5. В <context> собраны отрывки из разных книг, название книги указано в заголовке каждого отрывка. Отрывки выбраны по смыслу вопроса, поэтому внимательно прочитай каждый.
"""

FORBIDDEN_META_PHRASES = [
    "из представленных", "в представленных", "в загруженных", "в предоставленных",
    "согласно контексту", "в ваших файлах", "в файлах", "в текстах",
    "в переданном контексте", "в контексте", "ответа нет", "нет ответа",
    "ответ не найден", "не найден", "не найдено", "не содержится",
    "однако есть в других", "но есть в других", "если же говорить",
    "нет информации", "не упоминается", "в интернете", "в других книгах",
    "представленного контекста", "представленном контексте", "не содержат",
    "не относятся к теме", "в вашей библиотеке", "среди ваших",
    "среди загруженных", "из предоставленных", "предоставленных текстов",
    "из ваших", "в ваших", "в заданном контексте", "заданном контексте",
    "в литературе нет", "не относятся к литературным"
]


def is_bad_global_answer(answer):
    if not answer:
        return True
    low = answer.lower().strip()
    if low in {"none", "нет", "нет ответа", "ответ не найден"}:
        return True
    if "---" in low:
        return True
    return any(phrase in low for phrase in FORBIDDEN_META_PHRASES)


def safe_chat(messages, retries=5):
    return chat(messages, model=MODEL_FAST, temperature=0.1, retries=retries)


RU_CHARS = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя ")


def decode_text(raw):
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass

    candidates = []
    for enc in ("cp1251", "cp866"):
        try:
            candidates.append(raw.decode(enc))
        except UnicodeDecodeError:
            continue

    if not candidates:
        return raw.decode("utf-8", errors="replace")

    def score(text):
        sample = text[:5000].lower()
        return sum(1 for ch in sample if ch in RU_CHARS) / max(len(sample), 1)

    return max(candidates, key=score)


Chunk = namedtuple("Chunk", "title index text tf")

ENDINGS = sorted(
    [
        "ами", "ями", "ого", "его", "ому", "ему", "ыми", "ими",
        "ов", "ев", "ей", "ий", "ый", "ой", "ая", "яя", "ое", "ее", "ие", "ые",
        "ую", "юю", "ом", "ем", "ам", "ям", "ах", "ях", "ою", "ею", "ью",
        "ла", "ли", "ло", "ет", "ут", "ют", "ит", "ат", "ят",
        "ь", "а", "я", "у", "ю", "е", "и", "ы", "о", "й",
    ],
    key=len,
    reverse=True,
)

STOP_WORDS = {
    "книга", "книги", "книг", "книгах", "книге", "книгу", "каких", "какие", "какой",
    "какая", "каком", "какую", "где", "что", "про", "говорится", "говорят", "говорит",
    "упоминается", "упоминаются", "упоминание", "есть", "среди", "загруженных",
    "загруженные", "загруженных", "библиотеке", "библиотеки", "файлах", "файлы",
    "предоставленных", "предоставленные", "этих", "наших", "можно", "нужно",
    "подойдут", "лучше", "будут", "будет", "полезны", "для", "как", "или", "это",
    "при", "над", "под", "его", "ее", "их", "мне", "вас", "нас", "все", "всех",
    "произведения", "произведении", "произведениях", "произведение", "тема",
    "теме", "тему", "расскажи", "скажи", "назови", "посоветуй", "найди",
}

KEYWORDS_PROMPT = """
Ты помогаешь искать по текстам художественной литературы на русском языке.
По вопросу пользователя выведи ключевые слова для поиска: слова из вопроса, их синонимы, близкие по смыслу слова и разные формы слов (падежи, спряжения), которые могут встретиться в тексте произведений.
Например, для слова «смерть» подходят: смерть, смерти, умер, умерла, умирать, погиб, убит, убил, утонул, утопил, похороны, могила.
Ответь только словами через запятую, не более 30 слов, без пояснений.
"""

_chunk_cache = {}


def tokenize(text):
    return re.findall(r"[а-яёa-z0-9]+", text.lower())


def stem(word):
    for ending in ENDINGS:
        if word.endswith(ending) and len(word) - len(ending) >= 3:
            return word[:-len(ending)]
    return word


STOP_STEMS = {stem(w) for w in STOP_WORDS}


def split_text(text, size=1500, overlap=300):
    text = text.strip()
    parts = []
    step = size - overlap
    for start in range(0, len(text), step):
        parts.append(text[start:start + size])
        if start + size >= len(text):
            break
    return parts


def load_chunks(folder_path):
    chunks = []

    if not os.path.exists(folder_path):
        return chunks

    for file in sorted(os.listdir(folder_path)):
        if not file.lower().endswith(".txt"):
            continue

        path = os.path.join(folder_path, file)
        mtime = os.path.getmtime(path)
        cached = _chunk_cache.get(path)

        if cached is None or cached[0] != mtime:
            with open(path, "rb") as f:
                text = decode_text(f.read())
            title = file[:-4]
            items = [
                Chunk(title, i, part, Counter(stem(w) for w in tokenize(part)))
                for i, part in enumerate(split_text(text))
            ]
            _chunk_cache[path] = (mtime, items)

        chunks.extend(_chunk_cache[path][1])

    return chunks


def query_terms(question):
    words = [w for w in tokenize(question) if len(w) >= 3 and w not in STOP_WORDS]

    expansion = chat(
        [
            {"role": "system", "content": KEYWORDS_PROMPT},
            {"role": "user", "content": question}
        ],
        model=MODEL_FAST,
        temperature=0,
        retries=2,
    )
    if expansion:
        words += [w for w in tokenize(expansion) if len(w) >= 3][:60]

    terms = {stem(w) for w in words}
    return {t for t in terms if len(t) >= 3 and t not in STOP_STEMS}


def retrieve(question, folder_path, top_k=10, per_book=4):
    chunks = load_chunks(folder_path)
    if not chunks:
        return ""

    terms = query_terms(question)
    if not terms:
        return ""

    total = len(chunks)
    df = Counter()
    for chunk in chunks:
        for term in terms:
            if term in chunk.tf:
                df[term] += 1

    scored = []
    for position, chunk in enumerate(chunks):
        score = sum(
            math.log(1 + total / df[term]) * (1 + math.log(chunk.tf[term]))
            for term in terms
            if term in chunk.tf
        )
        if score > 0:
            scored.append((score, position))

    scored.sort(reverse=True)

    picked = []
    per_title = Counter()
    for score, position in scored:
        title = chunks[position].title
        if per_title[title] >= per_book:
            continue
        picked.append(position)
        per_title[title] += 1
        if len(picked) >= top_k:
            break

    picked.sort()

    return "\n\n".join(
        f"--- Начало отрывка из книги: {chunks[p].title} ---\n{chunks[p].text}\n--- Конец отрывка ---"
        for p in picked
    )


def generate_answer(question, context_text, force_local=False):
    user_prompt = f"Вопрос: {question}"

    if context_text:
        user_prompt = f"""
<context>
{context_text}
</context>

Вопрос: {question}
"""

    if force_local:
        answer = safe_chat([
            {"role": "system", "content": LOCAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ])
        if answer:
            return answer.replace('*', '')
        return "Ошибка при обращении к ИИ."

    answer = safe_chat([
        {"role": "system", "content": GLOBAL_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ])

    if answer is None:
        return "Извините, произошла ошибка при обращении к ИИ."

    if is_bad_global_answer(answer):
        retry_prompt = """
Ты забыл использовать свои знания! Ты перечислил только книги из текста.
Напиши ответ ЗАНОВО. Сначала назови 3-4 известные книги из мировой литературы (например, Шекспира, Пушкина, Толстого), и только потом добавь книги из текста.
КАТЕГОРИЧЕСКИ запрещено использовать слова «контекст», «файлы», «загруженные книги».
"""
        retry_answer = safe_chat([
            {"role": "system", "content": retry_prompt},
            {"role": "user", "content": user_prompt}
        ])
        if retry_answer:
            answer = retry_answer

    return answer.replace('*', '')


def test_answer(question, titles_list=None):
    local_keywords = [
        "загруженн", "наших книг", "в библиотеке",
        "предоставленн", "в файлах", "среди книг", "из этих книг"
    ]
    question_lower = question.lower()
    force_local = any(keyword in question_lower for keyword in local_keywords)

    local_context = retrieve(question, BOOKS_DIR)

    if force_local and not local_context:
        return "В загруженных книгах нет информации по этому вопросу."

    return generate_answer(question, local_context, force_local=force_local)


def get_file_origin(file_content):
    question_text = '''Определи, какому произведению относится данный отрывок.
Ответ выведи в виде "Фамилия И. О. - Название произведения".
Например: "Достоевский Ф. М. - Преступление и наказание".
Только строго по примеру, ничего больше не пиши после точки.'''

    answer = chat(
        [
            {
                "role": "system",
                "content": "Отвечай только на основе предоставленного текста. Если информации нет в тексте — скажи, что её нет."
            },
            {
                "role": "user",
                "content": f"""Вот содержимое файла:
{file_content}

Вопрос: {question_text}
"""
            }
        ],
        model=MODEL_LARGE,
    )

    if answer is None:
        return "Информации о произведении нет."

    return answer


def open_file_to_research_origin(filepath):
    with open(filepath, "rb") as f:
        file_content = decode_text(f.read())[:400]

    return get_file_origin(file_content)