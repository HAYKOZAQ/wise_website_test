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


STANDARD_REFUSAL_HY = (
    "Տվյալների բազայում այս հարցի վերաբերյալ հստակ տեղեկատվություն չի գտնվել: "
    "Խնդրում ենք դիմել Միասնական սոցիալական ծառայության թեժ գծին՝ **114** հեռախոսահամարով, "
    "կամ այցելել [e-soc.am](https://e-soc.am) պաշտոնական կայքը:"
)

STANDARD_REFUSAL_EN = (
    "No verified information was found in the database for this specific inquiry. "
    "Please contact the Unified Social Service hotline at **114** or visit [e-soc.am](https://e-soc.am)."
)

STANDARD_REFUSAL_RU = (
    "В базе данных не найдено проверенной информации по данному вопросу. "
    "Пожалуйста, обратитесь на горячую линию Единой социальной службы по номеру **114** "
    "или посетите официальный сайт [e-soc.am](https://e-soc.am)."
)


def get_standard_refusal(lang: str = "hy") -> str:
    """Return the official 114 hotline refusal message in the requested language."""
    if lang == "en":
        return STANDARD_REFUSAL_EN
    if lang == "ru":
        return STANDARD_REFUSAL_RU
    return STANDARD_REFUSAL_HY


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

        refusal_sample = STANDARD_REFUSAL_EN

        return f"""You are the official citizen AI assistant for Armenia's social protection system (MLSA / Unified Social Service).

STRICT SAFETY & GROUNDING RULES:
1. Use ONLY the facts directly stated in the CONTEXT below. NEVER invent or assume numbers, age limits, dates, legal articles, or requirements.
2. IF THE CONTEXT DOES NOT CONTAIN THE ANSWER to the user's question, or if the question is out of scope / unanswerable from the context, DO NOT GUESS OR FABRICATE. You MUST reply ONLY with:
"{refusal_sample}"
3. If the context contains sufficient verified information:
   - Provide a clear, polite, and helpful explanation tailored to the citizen.
   - Use clean Markdown with headers only where relevant:
     ## Summary
     ## Eligibility (if available in context)
     ## Amount & Benefits (if available in context)
     ## Required Documents (if available in context)
     ## How to Apply (e-soc.am, USS office, hotline 114)
   - Do NOT include empty sections or speculative claims.
4. NEVER copy or quote the CONTEXT text verbatim (no "Ակտ՝" tags, no full article text). Write a clear, concise answer in your own words, based only on the facts stated in the context. Start with a direct 1-2 sentence answer to the question, then add short sections only where the context supports them.

CONTEXT:
{context_str}
{hist_block}

CITIZEN QUESTION:
{query}

Response:"""

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

        refusal_sample = STANDARD_REFUSAL_RU

        return f"""Вы — официальный гражданский ИИ-консультант по системе социальной защиты Армении (МТСЗ / Единая социальная служба).

СТРОГИЕ ПРАВИЛА ДОСТОВЕРНОСТИ:
1. Используйте ТОЛЬКО факты, прямо указанные в КОНТЕКСТЕ ниже. Никогда не выдумывайте суммы, возрастные пороги, даты, номера статей или документы.
2. ЕСЛИ В КОНТЕКСТЕ НЕТ ОТВЕТА на вопрос гражданина или контекст недостаточен, НЕ ПЫТАЙТЕСЬ УГАДЫВАТЬ. Ответьте ИСКЛЮЧИТЕЛЬНО следующим текстом:
"{refusal_sample}"
3. Если контекст содержит достоверный ответ:
   - Дайте четкий, структурированный и понятный ответ на русском языке.
   - Используйте заголовки Markdown только для тех разделов, по которым есть данные в контексте:
     ## Краткий ответ
     ## Кто имеет право
     ## Размер и расчёт
     ## Необходимые документы
     ## Как и куда обратиться (e-soc.am, центры ЕСС, горячая линия 114)
   - Не создавайте пустых или предположительных разделов.
4. НИКОГДА не копируйте и не цитируйте текст КОНТЕКСТА дословно (без тегов «Ակտ՝», без полного текста статей). Напишите чёткий, краткий ответ своими словами, опираясь только на факты из контекста. Начните с прямого ответа в 1-2 предложения.

КОНТЕКСТ:
{context_str}
{hist_ru}

ВОПРОС ГРАЖДАНИНА:
{query}

Ответ:"""

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

    refusal_sample = STANDARD_REFUSAL_HY

    return f"""Դուք Հայաստանի Հանրապետության սոցիալական պաշտպանության համակարգի (ԱՍՀՆ / Միասնական սոցիալական ծառայություն) պաշտոնական քաղաքացիական ուղեցույցն եք։

ԱՆՎՏԱՆԳՈՒԹՅԱՆ ԵՎ ՓԱՍՏԱՑԻՈՒԹՅԱՆ ԽԻՍՏ ԿԱՆՈՆՆԵՐ.
1. Օգտագործեք ԲԱՑԱՌԱՊԵՍ ստորև տրված ՀԱՄԱՏԵՔՍՏԻ փաստերը։ Երբեք մի հորինեք գումարների չափեր, տարիքային շեմեր, ժամկետներ, փաստաթղթեր կամ օրենքի հոդվածներ։
2. ԵԹԵ ՀԱՄԱՏԵՔՍՏՈՒՄ ՉԿԱ ԼԻԱՐԺԵՔ ՊԱՏԱՍԽԱՆԸ կամ հարցը տվյալների բազայի շրջանակից դուրս է, ԵՐԲԵՔ ՄԻ ԵՆԹԱԴՐԵՔ ԿԱՄ ՀՈՐԻՆԵՔ։ Պատասխանեք ԲԱՑԱՌԱՊԵՍ հետևյալ տեքստով.
"{refusal_sample}"
3. Եթե համատեքստում առկա է հարցի հստակ պատասխանը.
   - Տվեք գործնական, հստակ և մարդակենտրոն պատասխան։
   - Օգտագործեք Markdown վերնագրեր միայն այն բաժինների համար, որոնց վերաբերյալ կան փաստեր համատեքստում.
     ## Կարճ պատասխան
     ## Ովքե՞ր կարող են դիմել (իրավասության չափանիշներ)
     ## Նպաստի/վճարի չափը (եթե նշված է)
     ## Անհրաժեշտ փաստաթղթերը
     ## Ինչպե՞ս և որտե՞ղ դիմել (e-soc.am, ՄՍԾ կենտրոններ, թեժ գիծ 114)
   - Մի ավելացրեք դատարկ կամ ենթադրական բաժիններ։
4. ԵՐԲԵՔ ՄԻ արտագրեք կամ մեջբերեք ՀԱՄԱՏԵՔՍՏԻ տեքստը բառացի (ոչ «Ակտ՝» պիտակները, ոչ հոդվածների ամբողջական տեքստը)։ Գրեք հստակ, կարճ պատասխան Ձեր իսկ խոսքերով՝ հիմնվելով միայն համատեքստի փաստերի վրա։ Սկսեք ուղիղ պատասխանից (1–2 նախադասություն)։

ՀԱՄԱՏԵՔՍՏ.
{context_str}
{hist_hy}

ՔԱՂԱՔԱՑՈՒ ՀԱՐՑ.
{query}

Պատասխան՝"""
