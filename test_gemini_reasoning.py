import json
import os

from google import genai
from google.genai import types
from pydantic import BaseModel, Field


class ReasoningResult(BaseModel):
    problem_understood_as: str
    known_facts: list[str]
    unknowns: list[str]
    hypothesis: str
    variable_under_test: str
    controlled_variables: list[str]
    experiment: str
    expected_observations: list[str]
    conclusion_rule: str
    cannot_conclude_yet: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


PROBLEMS = [
    {
        "id": 1001,
        "title": "Słaby dowód przeciwny",
        "description": (
            "Silnik Prawdy klasyfikuje twierdzenie jako SPRZECZNOŚĆ, "
            "gdy istnieje jeden bardzo mocny dowód za i jeden bardzo "
            "słaby dowód przeciw."
        ),
        "evidence": [
            "Siła poparcia wyniosła około 89%.",
            "Siła sprzeciwu wyniosła około 9%.",
            "System mimo dużej różnicy zaklasyfikował stan jako SPRZECZNOŚĆ.",
        ],
        "unknowns": [
            "Nie wiadomo, czy sama obecność słabego dowodu przeciwnego "
            "powinna wystarczać do klasyfikacji SPRZECZNOŚĆ."
        ],
    },
    {
        "id": 1002,
        "title": "Brak dowodów po obu stronach",
        "description": (
            "Silnik Prawdy otrzymuje twierdzenie, dla którego nie istnieją "
            "ani dowody wspierające, ani dowody przeciwne."
        ),
        "evidence": [],
        "unknowns": [
            "Nie wiadomo, jak system powinien odróżniać brak wiedzy "
            "od słabego poparcia albo słabego sprzeciwu."
        ],
    },
    {
        "id": 1003,
        "title": "Duża liczba przeciętnych dowodów",
        "description": (
            "Nie wiadomo, czy duża liczba przeciętnych dowodów może "
            "niesłusznie zdominować jeden dowód bardzo wysokiej jakości."
        ),
        "evidence": [
            "Liczba dowodów wpływa na niektóre elementy obecnego algorytmu.",
            "Jakość dowodów również wpływa na wynik.",
        ],
        "unknowns": [
            "Nie wiadomo, jaka powinna być relacja pomiędzy liczbą "
            "dowodów a ich jakością."
        ],
    },
    {
        "id": 1004,
        "title": "Źródła zależne od siebie",
        "description": (
            "Kilka dowodów może pochodzić z różnych dokumentów, ale wszystkie "
            "mogą ostatecznie opierać się na tym samym pierwotnym źródle."
        ),
        "evidence": [
            "Obecna liczba dowodów nie opisuje ich wzajemnej zależności.",
            "Powielenie jednej informacji może wyglądać jak wiele dowodów.",
        ],
        "unknowns": [
            "Nie wiadomo, jak wykrywać zależność źródeł i jak uwzględniać "
            "ją podczas agregacji dowodów."
        ],
    },
]


SYSTEM_INSTRUCTION = """
Jesteś zewnętrzną warstwą analityczną systemu FENIKS.

Nie jesteś źródłem prawdy i nie wolno ci udawać, że hipoteza jest faktem.
Twoim zadaniem jest zaprojektowanie uczciwego sposobu zbadania problemu.

Rozdzielaj:
- to, co wynika z dostarczonych danych,
- niewiadome,
- hipotezę wymagającą sprawdzenia,
- projekt eksperymentu,
- kryterium rozstrzygnięcia.

Nie wymyślaj brakujących wyników eksperymentów.
Jeżeli czegoś nie można ustalić, zaznacz to jawnie.
Nie stosuj jednej ogólnej recepty do różnych problemów.
"""


def analyze_problem(client, problem):
    prompt = f"""
Przeanalizuj następujący problem FENIKSA.

ID: {problem['id']}
TYTUŁ: {problem['title']}

OPIS:
{problem['description']}

DOSTĘPNE DOWODY:
{json.dumps(problem['evidence'], ensure_ascii=False, indent=2)}

NIEWIADOME ZAPISANE PRZEZ SYSTEM:
{json.dumps(problem['unknowns'], ensure_ascii=False, indent=2)}

Zaprojektuj badanie dotyczące dokładnie tego problemu.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=ReasoningResult,
            temperature=0.2,
        ),
    )

    return ReasoningResult.model_validate_json(
        response.text
    )


def print_result(problem, result):
    print("\n" + "=" * 70)
    print(f"PROBLEM {problem['id']}: {problem['title']}")
    print("=" * 70)

    print("\nROZUMIENIE PROBLEMU:")
    print(result.problem_understood_as)

    print("\nHIPOTEZA:")
    print(result.hypothesis)

    print("\nZMIENNA BADANA:")
    print(result.variable_under_test)

    print("\nZMIENNE KONTROLOWANE:")
    for item in result.controlled_variables:
        print(f"- {item}")

    print("\nEKSPERYMENT:")
    print(result.experiment)

    print("\nOCZEKIWANE OBSERWACJE:")
    for item in result.expected_observations:
        print(f"- {item}")

    print("\nKRYTERIUM ROZSTRZYGNIĘCIA:")
    print(result.conclusion_rule)

    print("\nCZEGO NADAL NIE WOLNO UZNAĆ ZA USTALONE:")
    for item in result.cannot_conclude_yet:
        print(f"- {item}")

    print(
        f"\nPEWNOŚĆ ANALIZY: "
        f"{result.confidence * 100:.1f}%"
    )


def main():
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError(
            "Brak GEMINI_API_KEY w środowisku."
        )

    client = genai.Client()

    results = []

    print("=" * 70)
    print("MOCNY TEST ZEWNĘTRZNEJ WARSTWY ROZUMOWANIA FENIKSA")
    print("=" * 70)

    for problem in PROBLEMS:
        result = analyze_problem(
            client,
            problem,
        )

        results.append(result)
        print_result(
            problem,
            result,
        )

    experiments = [
        result.experiment.strip().casefold()
        for result in results
    ]

    hypotheses = [
        result.hypothesis.strip().casefold()
        for result in results
    ]

    print("\n" + "=" * 70)
    print("TEST RÓŻNICOWANIA")
    print("=" * 70)

    print(
        "\nLICZBA PROBLEMÓW:",
        len(PROBLEMS),
    )

    print(
        "UNIKALNE EKSPERYMENTY:",
        len(set(experiments)),
    )

    print(
        "UNIKALNE HIPOTEZY:",
        len(set(hypotheses)),
    )

    print(
        "\nCZTERY RÓŻNE EKSPERYMENTY:",
        "TAK"
        if len(set(experiments)) == 4
        else "NIE",
    )

    print(
        "CZTERY RÓŻNE HIPOTEZY:",
        "TAK"
        if len(set(hypotheses)) == 4
        else "NIE",
    )

    print("\n" + "=" * 70)
    print("WAŻNE")
    print("=" * 70)

    print(
        "\nTen test NIE dowodzi, że odpowiedzi Gemini są prawdziwe."
    )

    print(
        "Sprawdza, czy warstwa semantyczna potrafi rozpoznać "
        "różne problemy i zaprojektować dla nich różne badania."
    )

    print(
        "Ocena poprawności tych badań należy do FENIKSA "
        "i jego mechanizmów kontroli."
    )


if __name__ == "__main__":
    main()