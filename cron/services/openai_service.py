from logger import Logger
from openai import OpenAI
from typing import Optional 
from config import Config

class OpenAIService:
    """Serwis do obsługi interakcji z API OpenAI"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(api_key=self.config.OPENAI_API_KEY)
        self.logger = Logger.instance()
        
    def evaluate_answer(
        self,
        question_text: str,
        answer_text: str,
        max_points: int,
        algorithm_params: dict = None,
        custom_prompt: Optional[str] = None
    ) -> Optional[float]:
        """
        Ocenia odpowiedź używając API OpenAI i zwraca wynik między 0 a max_points.
        
        Args:
            question_text: Treść pytania
            answer_text: Odpowiedź kandydata
            max_points: Maksymalna liczba punktów możliwa do zdobycia
            algorithm_params: Słownik zawierający evaluation_focus i scoring_criteria
            custom_prompt: Opcjonalny własny prompt zastępujący domyślny
        """
        try:
            self.logger.info(f"Rozpoczęcie oceny odpowiedzi przez AI")
            self.logger.debug(f"Długość odpowiedzi do oceny: {len(answer_text)} znaków")
            
            if custom_prompt:
                self.logger.debug("Użyto niestandardowego promptu")
            else:
                self.logger.debug("Użyto domyślnego promptu")
                
            self.logger.debug(f"Parametry algorytmu oceny: {algorithm_params}")
            
            # Before API call
            self.logger.info("Wysyłanie zapytania do API OpenAI...")
            
            # Domyślne kryteria oceny jeśli nie podano własnych
            default_evaluation_focus = 'Oceń kompletność i dokładność odpowiedzi.'
            default_scoring_criteria = f'''
            - {max_points} punktów: Doskonała odpowiedź, która w pełni odpowiada na pytanie
            - {max_points * 0.75} punktów: Bardzo dobra odpowiedź z drobnymi pominięciami
            - {max_points * 0.5} punktów: Odpowiedź zadowalająca, która częściowo odpowiada na pytanie
            - {max_points * 0.25} punktów: Słaba odpowiedź z istotnymi brakami
            - 0 punktów: Całkowicie niepoprawna lub nieadekwatna odpowiedź
            '''
            
            # Domyślny prompt jeśli nie podano własnego
            default_prompt = f"""
            Jesteś ekspertem oceniającym w procesie rekrutacji. Oceń następującą odpowiedź na pytanie.
            
            Pytanie: {question_text}
            
            Odpowiedź: {answer_text}
            
            Maksymalna liczba punktów: {max_points}
            
            Na co zwrócić uwagę: {algorithm_params.get('evaluation_focus', default_evaluation_focus)}
            
            Kryteria przyznawania punktów: {algorithm_params.get('scoring_criteria', default_scoring_criteria)}
            
            WAŻNE: Odpowiedz w formacie JSON:
            {{
                "score": <liczba_punktów>,
                "explanation": "<krótkie uzasadnienie oceny w oparciu o kryteria>"
            }}
            
            Bądź surowy, ale sprawiedliwy i obiektywny w swojej ocenie. Liczba punktów musi być między 0 a {max_points}.
            """
            
            prompt = custom_prompt if custom_prompt else default_prompt
            
            # Wywołanie API
            self.logger.debug("Wysyłanie zapytania do modelu GPT-4")
            completion = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                # response_format={"type": "json_object"},
            )
            
            # Parsowanie odpowiedzi
            self.logger.debug("Otrzymano odpowiedź od API, rozpoczęcie parsowania")
            response = completion.choices[0].message.content
            try:
                import json
                result = json.loads(response)
                self.logger.debug(f"Pomyślnie sparsowano JSON: {result}")
            except json.JSONDecodeError as e:
                self.logger.error(f"Błąd parsowania JSON: {str(e)}")
                self.logger.debug(f"Otrzymana odpowiedź: {response}")
                return None
            
            score = float(result['score'])
            
            # Walidacja czy wynik mieści się w zakresie
            if not 0 <= score <= max_points:
                self.logger.warning(f"Wynik {score} jest poza dozwolonym zakresem [0, {max_points}]")
                raise ValueError(f"Wynik {score} jest poza dozwolonym zakresem [0, {max_points}]")
                
            # After API call
            self.logger.debug(f"Otrzymano odpowiedź od API")
            
            # Before parsing
            self.logger.debug("Rozpoczęcie parsowania odpowiedzi JSON")
            
            # After validation
            self.logger.info(
                f"Zakończono ocenę odpowiedzi. "
                f"Przyznano {score}/{max_points} punktów. "
                f"Uzasadnienie: {result['explanation']}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Wystąpił błąd podczas oceny odpowiedzi: {str(e)}")
            self.logger.debug(f"Szczegóły błędu: {e.__class__.__name__}")
            return None
