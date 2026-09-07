#!/usr/bin/env python3
"""Aggregate the attendee survey answers for the sponsorship page tables.

    python3 scripts/attendee_stats.py

Prints the `attendeesExperience` and `attendeesCountries` arrays that live in
src/pages/[lang]/sponsors.astro, so next year's survey can be dropped into the
tables below and re-run instead of being aggregated by hand.

Only Count and "% of tickets" are used; "% of answers" is ignored, so the
columns stay comparable across questions that not everybody answered. The
ticket denominator is recovered from the count/percentage pairs rather than
assumed, which also double-checks the input: every experience row reproduces
its published percentage exactly at 914 tickets.

The country question was free text, so spelling variants, casing, native names,
abbreviations and unambiguous city answers are folded together before ranking.
Place names shared by several countries are left unattributed and fall into
Other.
"""
import statistics
import unicodedata

# ---------------------------------------------------------------- experience
EXPERIENCE = [
    ("Student", 160, 17.5),
    ("Mid-level", 155, 17.0),
    ("Junior", 136, 14.9),
    ("Senior", 123, 13.5),
    ("Associate", 48, 5.3),
    ("Lead", 45, 4.9),
    ("Manager", 34, 3.7),
    ("Other", 22, 2.4),
    ("Director", 17, 1.9),
    ("Executive", 12, 1.3),
]

# ------------------------------------------------------------------- country
# raw answer -> count, exactly as supplied
COUNTRY_RAW = [
    ("United States", 147), ("USA", 57), ("Germany", 44), ("India", 43),
    ("Ghana", 28), ("Netherlands", 28), ("Nigeria", 25), ("Canada", 22),
    ("Ireland", 22), ("United Kingdom", 20), ("Uganda", 19), ("Chile", 19),
    ("Philippines", 17), ("US", 16), ("France", 16), ("Greece", 15),
    ("Australia", 15), ("Colombia", 15), ("UK", 14),
    ("United States of America", 13), ("Malaysia", 13), ("Argentina", 12),
    ("Czechia", 12), ("South Africa", 12), ("Finland", 11), ("Spain", 10),
    ("México", 10), ("Brazil", 9), ("Nepal", 9), ("Indonesia", 9),
    ("Namibia", 8), ("Mexico", 8), ("Poland", 8), ("Italy", 7),
    ("Switzerland", 7), ("Bolivia", 6), ("Japan", 5), ("Mozambique", 5),
    ("Cameroon", 5), ("Sweden", 5), ("The Netherlands", 4), ("Kenya", 4),
    ("Taiwan", 4), ("Brasil", 4), ("india", 4), ("Portugal", 3),
    ("Singapore", 3), ("Ecuador", 3), ("Italia", 3), ("Deutschland", 3),
    ("usa", 3), ("Moçambique", 3), ("日本", 2), ("Belgium", 2), ("Berlin", 2),
    ("Czech Republic", 2), ("Egypt", 2), ("England", 2), ("España", 2),
    ("germany", 2), ("Hong Kong", 2), ("Hungary", 2), ("MALAYSIA", 2),
    ("nepal", 2), ("New Zealand", 2), ("Pakistan", 2), ("Panama", 2),
    ("Peru", 2), ("PERU", 2), ("Perú", 2), ("Rwanda", 2), ("Thailand", 2),
    ("Togo", 2), ("Uk", 2), ("Unitd States", 2), ("Venezuela", 2),
    ("Palestine", 1), ("U.S", 1), ("Ciudad de Panamá", 1),
    ("Ciudad de México", 1), ("Usa", 1), ("japan", 1), ("Israel", 1),
    ("Germny", 1), ("Republica Dominicana", 1), ("Romania", 1),
    ("România", 1), ("Russia", 1), ("Accra", 1), ("Saarbrücken", 1),
    ("San Miguel de Tucumán", 1), ("Santa Cruz", 1), ("Saudi", 1),
    ("Senegal", 1), ("france", 1), ("Slovakia", 1), ("españa", 1),
    ("South Korea", 1), ("Dominican Republic", 1), ("Spain/Poland", 1),
    ("Denmark", 1), ("DE", 1), ("Czech republic", 1), ("Taiwan Taipei", 1),
    ("한국", 1), ("Currently, Thailand", 1), ("Yogyakarta", 1),
    ("Tunisia", 1), ("turkey", 1), ("Turkey", 1), ("Türkiye", 1), ("UAE", 1),
    ("uganda", 1), ("Croatia", 1), ("Zimbabwe", 1), ("Costa Rica", 1),
    ("台灣", 1), ("United Arab Emirates", 1), ("Colorado", 1),
    ("united states", 1), ("colombia", 1), ("Martinique", 1),
    ("Montenegro", 1), ("Morocco", 1), ("Maputo", 1), ("Lebanon", 1),
    ("Colombi", 1), ("Las Palmas", 1), ("Laguna", 1), ("Unites States", 1),
    ("KENYA", 1), ("Nigrria", 1), ("Pais", 1), ("Uruguay", 1),
]

# variant -> canonical country. Anything not listed keeps its own name after
# case/accent folding. Cities and regions are mapped to their country; answers
# that are genuinely ambiguous or not a country are left to fall into Other.
ALIASES = {
    # United States
    "usa": "United States", "us": "United States",
    "u.s": "United States", "united states of america": "United States",
    "unitd states": "United States", "unites states": "United States",
    "colorado": "United States",
    # United Kingdom
    "uk": "United Kingdom", "england": "United Kingdom",
    # Germany
    "deutschland": "Germany", "germny": "Germany", "de": "Germany",
    "berlin": "Germany", "saarbrucken": "Germany",
    # Netherlands
    "the netherlands": "Netherlands",
    # Mexico — "México" and "Mexico" both appear
    "mexico": "Mexico", "ciudad de mexico": "Mexico",
    # Brazil / Portugal-language spellings
    "brasil": "Brazil",
    # Spain
    "espana": "Spain", "las palmas": "Spain",
    # Italy
    "italia": "Italy",
    # Mozambique
    "mocambique": "Mozambique", "maputo": "Mozambique",
    # Czechia
    "czech republic": "Czechia",
    # Japan / Korea / Taiwan native names
    "日本": "Japan", "한국": "South Korea", "台灣": "Taiwan",
    "taiwan taipei": "Taiwan",
    # Turkey
    "turkiye": "Turkey",
    # UAE
    "uae": "United Arab Emirates",
    # Dominican Republic
    "republica dominicana": "Dominican Republic",
    # Romania
    "romania": "Romania",
    # Peru
    "peru": "Peru",
    # Nigeria typo
    "nigrria": "Nigeria",
    # Colombia typo
    "colombi": "Colombia",
    # cities/regions -> country
    "accra": "Ghana",
    "san miguel de tucuman": "Argentina",
    "ciudad de panama": "Panama",
    "yogyakarta": "Indonesia",
    "currently, thailand": "Thailand",
    "martinique": "France",
    # not a country / ambiguous -> keep distinct so they land in Other
    "pais": "(unspecified)",
    "spain/poland": "(unspecified)",
    # place names shared by several countries — not attributed to one
    "santa cruz": "(unspecified)",
    "laguna": "(unspecified)",
    "saudi": "Saudi Arabia",
}


def fold(name: str) -> str:
    """Lowercase and strip accents so variants collapse."""
    n = unicodedata.normalize("NFKD", name.strip().lower())
    return "".join(c for c in n if not unicodedata.combining(c))


# Display spelling for each folded key, so answers that differ only by accent
# or case ("México"/"Mexico", "india"/"India") land in the same bucket. Built
# from the raw answers: prefer the spelling that is already capitalised.
_DISPLAY: dict[str, str] = {}
for _raw, _ in COUNTRY_RAW:
    _key = fold(_raw)
    _cur = _DISPLAY.get(_key)
    if _cur is None or (_raw[:1].isupper() and not _cur[:1].isupper()):
        _DISPLAY[_key] = _raw.strip()


# Both sides of the lookup go through fold(), otherwise an alias key written in
# composed form can never match an answer that fold() decomposed. NFKD splits
# Hangul syllables into Jamo ("한국"), which is how South Korea was missed.
_ALIASES_FOLDED = {fold(k): v for k, v in ALIASES.items()}


def canonical(name: str) -> str:
    key = fold(name)
    if key in _ALIASES_FOLDED:
        return _ALIASES_FOLDED[key]
    return _DISPLAY.get(key, name.strip().title())


def estimate_tickets():
    """Recover the ticket denominator from count/percentage pairs."""
    est = [c / (p / 100) for _, c, p in EXPERIENCE if p]
    return round(statistics.median(est))


def main():
    tickets = estimate_tickets()
    print(f"ticket denominator (median of count/pct): {tickets}")
    print(f"experience answers: {sum(c for _, c, _ in EXPERIENCE)}")

    print("\n--- Experience Level (count, % of tickets) ---")
    for name, count, given in EXPERIENCE:
        pct = count / tickets * 100
        print(f'  {{ position: "{name}", count: "{count}", percentage: "{pct:.1f}%" }},'
              f"   (given {given}%)")

    # ---- countries
    merged = {}
    for raw, count in COUNTRY_RAW:
        merged[canonical(raw)] = merged.get(canonical(raw), 0) + count

    total_answers = sum(merged.values())
    assert total_answers == sum(c for _, c in COUNTRY_RAW), "lost answers while merging"

    ranked = sorted(merged.items(), key=lambda kv: (-kv[1], kv[0]))
    top, rest = ranked[:15], ranked[15:]

    print(f"\ncountry answers: {total_answers}  "
          f"({len(COUNTRY_RAW)} raw answers -> {len(merged)} countries)")
    print("\n--- Residence Country: top 15 + Other (count, % of tickets) ---")
    for name, count in top:
        print(f'  {{ position: "{name}", count: "{count}", percentage: "{count / tickets * 100:.1f}%" }},')
    other = sum(c for _, c in rest)
    print(f'  {{ position: "Other", count: "{other}", percentage: "{other / tickets * 100:.1f}%" }},')
    print(f"\n  Other covers {len(rest)} countries; "
          f"top15={sum(c for _, c in top)} + other={other} = {sum(c for _, c in top) + other}")
    print("\n  merged groups with more than one source answer:")
    for name, count in ranked:
        sources = [r for r, _ in COUNTRY_RAW if canonical(r) == name]
        if len(sources) > 1:
            print(f"    {name:24s} {count:4d}  <- {', '.join(sources)}")


if __name__ == "__main__":
    main()
