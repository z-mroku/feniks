# -*- coding: utf-8 -*-

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from google.genai.errors import ServerError


class ModelCallState(Enum):
    """
    Stan wykonania zewnętrznego wywołania modelu.

    SUCCESS:
        Otrzymano rzeczywistą odpowiedź modelu.

    UNAVAILABLE:
        Nie otrzymano odpowiedzi, ponieważ dostępne
        modele były chwilowo niedostępne.
    """

    SUCCESS = "SUCCESS"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class ModelCallResult:
    """
    Techniczny wynik próby użycia zewnętrznego modelu.

    Ten obiekt NIE jest wynikiem poznawczym FENIKSA.
    Nie mówi, czy hipoteza jest prawdziwa ani czy
    rozumowanie jest poprawne.
    """

    state: ModelCallState
    text: Optional[str]
    model_used: Optional[str]
    fallback_used: bool

    primary_error: Optional[str] = None
    fallback_error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.state is ModelCallState.SUCCESS

    @property
    def unavailable(self) -> bool:
        return self.state is ModelCallState.UNAVAILABLE


class ModelGateway:
    """
    Wspólna polityka dostępności modeli zewnętrznych.

    Gateway:
    - nie buduje promptów,
    - nie interpretuje odpowiedzi,
    - nie zna schematów poznawczych,
    - nie uznaje niczego za prawdę,
    - nie zapisuje wiedzy.

    Odpowiada wyłącznie za kontrolowane wykonanie:

        primary -> ewentualny fallback -> wynik techniczny
    """

    def __init__(self) -> None:
        self.call_count = 0
        self.fallback_count = 0
        self.unavailable_count = 0

    def execute(
        self,
        primary_model: str,
        fallback_model: Optional[str],
        generate: Callable[[str], str],
    ) -> ModelCallResult:
        """
        Próbuje wykonać wywołanie na modelu podstawowym.

        Fallback jest dopuszczony wyłącznie dla błędu 503,
        czyli chwilowej niedostępności usługi.

        Jeżeli również fallback zwróci 503, gateway nie
        wymyśla odpowiedzi. Zwraca jawny stan UNAVAILABLE.

        Inne błędy pozostają błędami programistycznymi,
        konfiguracyjnymi lub API i są propagowane wyżej.
        """

        if not isinstance(primary_model, str):
            raise TypeError(
                "primary_model musi być tekstem."
            )

        if not primary_model.strip():
            raise ValueError(
                "primary_model nie może być pusty."
            )

        if fallback_model is not None:
            if not isinstance(fallback_model, str):
                raise TypeError(
                    "fallback_model musi być tekstem albo None."
                )

            if not fallback_model.strip():
                raise ValueError(
                    "fallback_model nie może być pustym tekstem."
                )

        if not callable(generate):
            raise TypeError(
                "generate musi być funkcją wywołującą model."
            )

        self.call_count += 1

        try:
            text = generate(primary_model)

            return ModelCallResult(
                state=ModelCallState.SUCCESS,
                text=text,
                model_used=primary_model,
                fallback_used=False,
            )

        except ServerError as primary_error:
            if primary_error.code != 503:
                raise

            if (
                not fallback_model
                or fallback_model == primary_model
            ):
                self.unavailable_count += 1

                return ModelCallResult(
                    state=ModelCallState.UNAVAILABLE,
                    text=None,
                    model_used=None,
                    fallback_used=False,
                    primary_error=str(primary_error),
                )

            self.fallback_count += 1

            try:
                text = generate(fallback_model)

                return ModelCallResult(
                    state=ModelCallState.SUCCESS,
                    text=text,
                    model_used=fallback_model,
                    fallback_used=True,
                    primary_error=str(primary_error),
                )

            except ServerError as fallback_error:
                if fallback_error.code != 503:
                    raise

                self.unavailable_count += 1

                return ModelCallResult(
                    state=ModelCallState.UNAVAILABLE,
                    text=None,
                    model_used=None,
                    fallback_used=True,
                    primary_error=str(primary_error),
                    fallback_error=str(fallback_error),
                )

    def stats(self) -> dict:
        """
        Zwraca techniczne statystyki działania gatewaya.
        """

        return {
            "modul_gotowy": True,
            "liczba_wywolan": self.call_count,
            "liczba_fallbackow": self.fallback_count,
            "liczba_niedostepnosci": self.unavailable_count,
        }