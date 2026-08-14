"""
Multilingual citizen RAG prompts, colloquial query expanders, intent classifiers, and text sanitizers.
"""

from __future__ import annotations

import re
from typing import Any

LEGAL_QUERY_HINTS = (
    "իրավունք", "չափորոշիչ", "հոդված", "մերժում", "ստաժ", "կարգ", "որոշում",
    "օրենք", "պահանջ", "փաստաթղթ", "eligibility", "criteria", "article", "reject",
    "document", "law", "procedure",
)

SUMMARY_QUERY_HINTS = (
    "որքան", "ինչքան", "ինչպես դիմել", "որտեղ", "պարզ", "կարճ", "how much",
    "how to apply", "where", "simple", "amount", "documents needed",
)

QUICK_FACT_HINTS = (
    "հեռախոս", "թեժ գիծ", "համար", "հասցե", "կոնտակտ", "կայք", "էլեկտրոնային",
    "phone", "hotline", "number", "address", "contact", "website", "email",
    "телефон", "горячая линия", "номер", "адрес", "сайт",
)

# Colloquial Armenian Citizen Slang → Official Welfare Program Keywords
COLLOQUIAL_EXPANSIONS: dict[str, list[str]] = {
    "երեխայի փող": ["երեխայի ծննդյան միանվագ նպաստ", "խնամքի նպաստ մինչև 2 տարեկան"],
    "երեխու փող": ["երեխայի ծննդյան միանվագ նպաստ", "խնամքի նպաստ մինչև 2 տարեկան"],
    "երեխայի նպաստ": ["խնամքի նպաստ մինչև 2 տարեկան", "երեխայի ծննդյան միանվագ նպաստ"],
    "թոշակ": ["տարիքային աշխատանքային կենսաթոշակ", "հաշմանդամության կենսաթոշակ"],
    "թոշակի տարիք": ["տարիքային աշխատանքային կենսաթոշակ 63 տարի"],
    "թոշակի ստաժ": ["տարիքային աշխատանքային կենսաթոշակ աշխատանքային ստաժ 10 տարի"],
    "փարոս": ["ընտանեկան նպաստ", "անապահովության գնահատման համակարգ"],
    "դեկրետ": ["մայրության նպաստ", "հղիության և ծննդաբերության նպաստ"],
    "դեկրետի փող": ["մայրության նպաստ", "ժամանակավոր անաշխատունակություն"],
    "լույսի փող": ["էլեկտրաէներգիայի սակագնի փոխհատուցում", "սոցիալապես անապահով ընտանիքներ"],
    "գազի փող": ["բնական գազի սակագնի փոխհատուցում", "սոցիալական աջակցություն"],
    "բնակվարձ": ["բնակարանային ապահովման աջակցություն", "տեղահանված անձանց բնակվարձի փոխհատուցում"],
    "տան փող": ["բնակարանային ապահովման աջակցություն", "տեղահանվածներ"],
    "ուսման վարձ": ["ուսման վարձի փոխհատուցում զոհվածների երեխաներ", "հաշմանդամություն ուսանողներ"],
    "գործազուրկ": ["գործազրկության կարգավիճակ", "զբաղվածության պետական ծրագրեր"],
    "հաշմանդամություն": ["հաշմանդամության կենսաթոշակ", "ֆունկցիոնալության գնահատում"],
}

_IMAGE_REF_RE = re.compile(r'\b[\w\-]+\.(?:png|jpg|jpeg|gif|svg|webp|bmp|ico)\b', re.I)


def strip_image_refs(text: str) -> str:
    """Strip image file references so the model prompt contains clean prose."""
    return _IMAGE_REF_RE.sub('', text or '')


def is_quick_factual_query(query: str) -> bool:
    """Detects whether the question is a direct lookup for a phone number, address, or single fact."""
    q = (query or "").lower().strip()
    if len(q.split()) <= 4 and any(h in q for h in QUICK_FACT_HINTS):
        return True
    return False


def expand_colloquial_query(query: str) -> list[str]:
    """Expands citizen slang terms into formal legal act keywords."""
    q_lower = query.lower().strip()
    expanded = [query]
    for slang, formal_terms in COLLOQUIAL_EXPANSIONS.items():
        if slang in q_lower:
            for term in formal_terms:
                expanded.append(f"{query} {term}")
    return list(dict.fromkeys(expanded))


def reorder_context_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Mitigates the 'Lost in the Middle' attention drop in LLMs by placing
    the highest-relevance chunks at the top and bottom of the context window.
    """
    if len(chunks) <= 2:
        return chunks
    
    reordered: list[dict[str, Any]] = [None] * len(chunks)
    left = 0
    right = len(chunks) - 1
    
    for i, chunk in enumerate(chunks):
        if i % 2 == 0:
            reordered[left] = chunk
            left += 1
        else:
            reordered[right] = chunk
            right -= 1
            
    return [c for c in reordered if c is not None]


def build_follow_ups(query: str, lang: str, chunks: list[dict[str, Any]]) -> list[str]:
    """Generates relevant follow-up questions tailored to categories in retrieved chunks."""
    cats = {c.get("category") for c in chunks if c.get("category")}
    if lang == "en":
        base = [
            "Who is eligible?",
            "What documents are required?",
            "How and where do I apply?",
            "What is the amount?",
        ]
        if "pensions" in cats:
            base.append("What is the minimum work history?")
        if "employment" in cats:
            base.append("How do I register as unemployed?")
        return base[:4]
    if lang == "ru":
        base = [
            "Кто имеет право?",
            "Какие документы нужны?",
            "Как и куда обратиться?",
            "Какой размер выплаты?",
        ]
        if "pensions" in cats:
            base.append("Какой минимальный стаж?")
        if "employment" in cats:
            base.append("Как получить статус безработного?")
        return base[:4]
    base = [
        "Ո՞վ ունի իրավունք",
        "Ի՞նչ փաստաթղթեր են պետք",
        "Ինչպե՞ս և որտե՞ղ դիմել",
        "Որքա՞ն է չափը",
    ]
    if "pensions" in cats:
        base.append("Որքա՞ն է նվազագույն ստաժը")
    if "employment" in cats:
        base.append("Ինչպե՞ս ձևակերպել գործազրկության կարգավիճակ")
    return base[:4]


def build_rag_prompt(
    query: str,
    context_str: str,
    user_lang: str = "hy",
    history: list[dict[str, str]] | None = None,
) -> str:
    """Builds an adaptive, strictly-grounded citizen system prompt in Armenian, English, or Russian."""
    quick_fact = is_quick_factual_query(query)

    if user_lang == "en":
        hist_block = ""
        if history:
            lines = []
            for turn in history[-6:]:
                role = (turn.get("role") or "user").lower()
                content = (turn.get("content") or "").strip()
                if not content:
                    continue
                label = "Citizen" if role == "user" else "Assistant"
                lines.append(f"{label}: {content[:500]}")
            if lines:
                hist_block = "\n\nPRIOR TURNS:\n" + "\n".join(lines)

        if quick_fact:
            return f"""You are a helpful citizen guide for Armenia's social protection programs.
Answer the question directly and concisely (2–4 sentences or bullet points) based strictly on the CONTEXT below.

RULES:
1) Use ONLY the CONTEXT below. Never guess phone numbers, addresses, or amounts.
2) Cite the official contact or document name at the end.

CONTEXT:
{context_str}
{hist_block}

QUESTION:
{query}

Direct Answer:"""

        return f"""You are a careful citizen guide for Armenia's social protection programs (MLSA / Unified Social Service).

GOAL: Give a COMPLETE, practical explanation so a person understands how the program works end-to-end.

RULES:
1) Use ONLY the CONTEXT below. Never invent amounts, ages, documents, deadlines, or article numbers.
2) If a detail is missing in CONTEXT, write clearly: "This is not specified in the available materials" and suggest hotline 114 / e-soc.am / USS office.
3) Write FULL sentences. Finish every section.
4) Prefer concrete numbers and lists FROM the context. Prefer [legal] facts over [summary].
5) For any money amount, age threshold, or deadline: if it comes only from a citizen summary, add: "Please verify the current amount with hotline 114 or e-social.am."

Required markdown structure:
## Short answer
(2–4 sentences: what the program is and who it is for)

## How the program works
(Explain the mechanism / process in plain language)

## Who is eligible
(Bullet criteria)

## Amount / calculation
(All amounts or formula found in context)

## Required documents
(Bullet list)

## How / where to apply
(e-soc.am, USS centers, hotline 114 when relevant)

## Deadlines
(If any)

## Important notes
(Exceptions, border villages, working vs non-working, etc. if in context)

## Sources
(Titles from context only)

CONTEXT:
{context_str}
{hist_block}

CITIZEN QUESTION:
{query}

Write a complete answer in clear English:"""

    if user_lang == "ru":
        hist_ru = ""
        if history:
            lines = []
            for turn in history[-6:]:
                role = (turn.get("role") or "user").lower()
                content = (turn.get("content") or "").strip()
                if not content:
                    continue
                label = "Гражданин" if role == "user" else "Помощник"
                lines.append(f"{label}: {content[:500]}")
            if lines:
                hist_ru = "\n\nПРЕДЫДУЩИЕ ВОПРОСЫ:\n" + "\n".join(lines)

        if quick_fact:
            return f"""Вы — гражданский гид по программам социальной защиты Армении.
Ответьте на вопрос прямо и кратко (2–4 предложения или списком), опираясь исключительно на КОНТЕКСТ ниже.

ПРАВИЛА:
1) Используйте ТОЛЬКО КОНТЕКСТ. Никогда не выдумывайте номера телефонов, адреса или суммы.
2) В конце укажите официальный источник или контакт.

КОНТЕКСТ:
{context_str}
{hist_ru}

ВОПРОС:
{query}

Краткий ответ:"""

        return f"""Вы — гражданский гид по программам социальной защиты Армении (МТСЗ / Единая социальная служба).

ЦЕЛЬ: дайте ПОЛНОЕ, практическое объяснение, чтобы человек понял, как работает программа от начала до конца.

ПРАВИЛА:
1) Используйте ТОЛЬКО КОНТЕКСТ ниже. Никогда не выдумывайте суммы, возрасты, документы, сроки или номера статей.
2) Если деталь отсутствует в контексте, напишите ясно: «В имеющихся материалах это не указано» и предложите горячую линию 114 / e-soc.am / офис ЕСС.
3) Пишите ПОЛНЫМИ предложениями. Завершайте каждый раздел.
4) Предпочитайте конкретные цифры и списки ИЗ контекста. Отдавайте предпочтение [legal] фактам перед [summary].
5) Для любой денежной суммы, возрастного порога или срока: если он указан только в [summary], добавьте: «Пожалуйста, уточните актуальный размер по горячей линии 114 или на e-social.am».

Обязательная структура markdown:
## Краткий ответ
(2–4 предложения: что это за программа и для кого)

## Как работает программа
(Объясните механизм / процедуру простым языком)

## Кто имеет право
(Критерии списком)

## Размер / расчёт
(Все суммы или формулы из контекста)

## Необходимые документы
(Список)

## Как и куда обратиться
(e-soc.am, центры ЕСС, горячая линия 114 при необходимости)

## Сроки
(Если есть)

## Важные замечания
(Исключения, приграничные сёла, рабочие/нерабочие и т.д., если есть в контексте)

## Источники
(Только названия из контекста)

КОНТЕКСТ:
{context_str}
{hist_ru}

ВОПРОС ГРАЖДАНИНА:
{query}

Напишите полный ответ понятным русским языком:"""

    # Armenian (Default)
    hist_hy = ""
    if history:
        lines = []
        for turn in history[-6:]:
            role = (turn.get("role") or "user").lower()
            content = (turn.get("content") or "").strip()
            if not content:
                continue
            label = "Քաղաքացի" if role == "user" else "Օգնական"
            lines.append(f"{label}: {content[:500]}")
        if lines:
            hist_hy = "\n\nՆԱԽՈՐԴ ՀԱՐՑՈՒՄՆԵՐ (միայն համատեքստի համար):\n" + "\n".join(lines)

    if quick_fact:
        return f"""Դուք Հայաստանի սոցիալական պաշտպանության ծրագրերի քաղաքացիական ուղեցույցն եք։
Պատասխանեք հարցին ՈՒՂԻՂ ԵՎ ՀԱԿԻՐՃ (2–4 նախադասություն կամ ցանկով)՝ հիմնվելով ԲԱՑԱՌԱՊԵՍ ստորև տրված ՀԱՄԱՏԵՔՍՏԻ վրա։

ԿԱՆՈՆՆԵՐ.
1) Օգտագործեք ՄԻԱՅՆ ՀԱՄԱՏԵՔՍՏԸ։ Երբեք մի հորինեք հեռախոսահամարներ, հասցեներ կամ գումարներ։
2) Նշեք պաշտոնական կոնտակտը կամ փաստաթուղթը։

ՀԱՄԱՏԵՔՍՏ.
{context_str}
{hist_hy}

ՀԱՐՑ.
{query}

Ուղիղ պատասխան՝"""

    return f"""Դուք Հայաստանի սոցիալական պաշտպանության ծրագրերի (ԱՍՀՆ / Միասնական սոցիալական ծառայություն) քաղաքացիական ուղեցույցն եք։

ՆՊԱՏԱԿ. տվեք ԱՄԲՈՂՋԱԿԱՆ, գործնական բացատրություն, որպեսզի մարդը հասկանա՝ ինչպես է ծրագիրն աշխատում սկզբից մինչև վերջ։

ԿԱՆՈՆՆԵՐ.
1) Օգտագործեք ՄԻԱՅՆ ստորև տրված ՀԱՄԱՏԵՔՍՏԸ։ Երբեք մի հորինեք գումարներ, տարիք, փաստաթղթեր, ժամկետներ կամ հոդվածների համարներ։
2) Եթե որևէ մանրամասն չկա համատեքստում, գրեք հստակ՝ «Առկա նյութերում սա նշված չէ» և առաջարկեք թեժ գիծ 114 / e-soc.am / ՄՍԾ տարածքային կենտրոն։
3) Գրեք ԼՐԻՎ նախադասություններ։ Ավարտեք յուրաքանչյուր բաժին։
3ա) Եթե [legal] և [summary] հակասում են, նախընտրեք [legal]։ Summary-ի գումարները պայմանական են.
3բ) Յուրաքանչյուր գումար/տարիք/ժամկետ summary-ից՝ ավելացրեք. «Ստուգեք ակտուալ չափը 114 կամ e-social.am»։
4) Նախընտրեք համատեքստի կոնկրետ թվերն ու ցուցակները։

Պարտադիր markdown կառուցվածք.
## Կարճ պատասխան
(2–4 նախադասություն՝ ինչ է ծրագիրը և ում համար է)

## Ինչպես է աշխատում ծրագիրը
(Պարզ լեզվով մեխանիզմը / ընթացակարգը)

## Ով ունի իրավունք
(Չափորոշիչների ցուցակ)

## Չափ / հաշվարկ
(Բոլոր գումարները կամ բանաձևը համատեքստից)

## Անհրաժեշտ փաստաթղթեր
(Ցուցակ)

## Ինչպես և որտեղ դիմել
(e-soc.am, ՄՍԾ կենտրոններ, թեժ գիծ 114)

## Ժամկետներ
(Եթե կան)

## Կարևոր նշումներ
(Բացառություններ, սահմանամերձ, աշխատող/չաշխատող և այլն՝ եթե կա համատեքստում)

## Աղբյուրներ
(Միայն համատեքստի վերնագրերը)

ՀԱՄԱՏԵՔՍՏ.
{context_str}
{hist_hy}

ՔԱՂԱՔԱՑՈՒ ՀԱՐՑ.
{query}

Գրեք ամբողջական պատասխանը պարզ հայերենով՝"""
