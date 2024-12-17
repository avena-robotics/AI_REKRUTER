from logger import Logger
from typing import Optional
from supabase import Client
from datetime import datetime, timedelta
from datetime import timezone
from services.openai_service import OpenAIService

class TestService:
    """Serwis do obliczania wyników testów kandydatów"""
    
    def __init__(self, supabase: Client, openai_service: OpenAIService):
        self.supabase = supabase
        self.openai_service = openai_service
        self.logger = Logger.instance()

    def calculate_test_score(self, candidate_id: int, test_id: int, stage: str) -> Optional[dict]:
        """
        Oblicza wynik testu dla kandydata
        """
        try:
            self.logger.info(f"[TEST {test_id}] Rozpoczęcie obliczania wyniku dla kandydata {candidate_id} w etapie {stage}")
            
            # First get test type
            test_response = self.supabase.table('tests')\
                .select('test_type')\
                .eq('id', test_id)\
                .single()\
                .execute()
                
            if not test_response.data:
                self.logger.warning(f"[TEST {test_id}] Nie znaleziono testu")
                return None
                
            test_type = test_response.data['test_type']
            self.logger.info(f"[TEST {test_id}] Typ testu: {test_type}")

            answers_response = self.supabase.table('candidate_answers')\
                .select('''
                    id,
                    question_id,
                    answer,
                    points_per_option
                ''')\
                .eq('candidate_id', candidate_id)\
                .eq('stage', stage)\
                .execute()
            
            if not answers_response.data:
                self.logger.warning(f"[TEST {test_id}] Brak odpowiedzi dla kandydata {candidate_id} w etapie {stage}")
                return None
                
            self.logger.info(f"[TEST {test_id}] Pobrano {len(answers_response.data)} odpowiedzi dla kandydata {candidate_id}")
                
            question_ids = [answer['question_id'] for answer in answers_response.data]
            self.logger.debug(f"[TEST {test_id}] Identyfikatory pytań do pobrania: {question_ids}")
            
            questions_response = self.supabase.table('questions')\
                .select('*, tests!inner(*)')\
                .eq('test_id', test_id)\
                .in_('id', question_ids)\
                .execute()
                            
            if not questions_response.data:
                self.logger.warning(f"[TEST {test_id}] Nie znaleziono pytań dla podanych identyfikatorów")
                return None
                
            questions = {q['id']: q for q in questions_response.data}
            self.logger.info(f"[TEST {test_id}] Pobrano {len(questions)} pytań")

            # Handle different test types
            if test_type == 'EQ':
                # Only process AH_POINTS questions for EQ tests
                eq_questions = [q for q in questions.values() if q['answer_type'] == 'AH_POINTS']
                if eq_questions:
                    self.logger.info(f"[TEST {test_id}] Wykryto test EQ z {len(eq_questions)} pytaniami typu AH_POINTS")
                    eq_scores = self.calculate_eq_scores(answers_response.data, eq_questions)
                    self.logger.info(f"[TEST {test_id}] Obliczono wyniki EQ dla kandydata {candidate_id}: {eq_scores}")
                    return eq_scores
                else:
                    self.logger.warning(f"[TEST {test_id}] Test oznaczony jako EQ, ale nie znaleziono pytań typu AH_POINTS")
                    return None
            else:
                # For non-EQ tests, calculate regular score
                self.logger.info(f"[TEST {test_id}] Wykryto standardowy test typu {test_type}")
                total_score = self.calculate_total_score(answers_response, questions)
                self.logger.info(f"[TEST {test_id}] Obliczono wynik standardowy dla kandydata {candidate_id}: {total_score}")
                return total_score or 0  # Test został wykonany, więc zwracamy wynik (nawet 0)
                
        except Exception as e:
            self.logger.error(f"[TEST {test_id}] Krytyczny błąd podczas obliczania wyniku dla kandydata {candidate_id}: {str(e)}")
            return None

    def calculate_eq_scores(self, answers, questions) -> dict:
        """
        Oblicza wyniki testu EQ dla wszystkich kategorii.
        """
        self.logger.info("Rozpoczęcie obliczania wyników EQ")
        self.logger.debug(f"Liczba odpowiedzi do przeanalizowania: {len(answers)}")
        self.logger.debug(f"Liczba pytań do przeanalizowania: {len(questions)}")
        
        eq_mapping = {
            'KO': ['d', 'b', 'a', 'h', 'f', 'c', 'g'],
            'RE': ['g', 'a', 'h', 'd', 'b', 'f', 'e'],
            'W':  ['f', 'e', 'c', 'b', 'd', 'g', 'a'],
            'IN': ['c', 'g', 'd', 'e', 'h', 'a', 'f'],
            'PZ': ['a', 'c', 'f', 'g', 'e', 'h', 'd'],
            'KZ': ['h', 'd', 'g', 'c', 'a', 'e', 'b'],
            'DZ': ['b', 'f', 'e', 'a', 'c', 'b', 'h'],
            'SW': ['e', 'h', 'b', 'f', 'g', 'd', 'c']
        }
        
        eq_scores = {
            'score_ko': 0, 'score_re': 0, 'score_w': 0, 'score_in': 0,
            'score_pz': 0, 'score_kz': 0, 'score_dz': 0, 'score_sw': 0
        }

        # Create a mapping of question_id to order_number
        question_orders = {q['id']: q['order_number'] - 1 for q in questions}
        self.logger.debug(f"Utworzono mapowanie pytań do numerów sekcji: {question_orders}")
        
        for answer in answers:
            question_id = answer['question_id']
            if question_id not in question_orders:
                self.logger.warning(f"Pominięto odpowiedź dla pytania {question_id} - brak w mapowaniu sekcji")
                continue
                
            section_number = question_orders[question_id]
            points_per_option = answer.get('points_per_option', {})
            
            if not points_per_option:
                self.logger.warning(f"Pominięto pytanie {question_id} - brak przydzielonych punktów w odpowiedzi")
                continue
            
            self.logger.debug(f"Analiza sekcji {section_number + 1}, przydzielone punkty: {points_per_option}")
            
            # Calculate scores for each category
            for category, letters in eq_mapping.items():
                if section_number < len(letters):
                    expected_letter = letters[section_number]
                    score_key = f'score_{category.lower()}'
                    points = points_per_option.get(expected_letter, 0)
                    eq_scores[score_key] += points
                    self.logger.debug(f"Kategoria {category}: dodano {points} punktów za odpowiedź '{expected_letter}'")
            
            self.logger.debug(f"Stan wyników po sekcji {section_number + 1}: {eq_scores}")
        
        self.logger.info(f"Zakończono obliczanie wyników EQ. Wyniki końcowe: {eq_scores}")
        return eq_scores

    def calculate_score(self, answer: dict, question: dict) -> float:
        """
        Oblicza wynik dla pojedynczej odpowiedzi.
        
        Args:
            answer: Odpowiedź kandydata
            question: Pytanie z parametrami oceny
            
        Returns:
            float: Wynik za odpowiedź (zawsze zaokrąglony do 1 miejsca po przecinku)
        """
        try:
            self.logger.debug(f"Rozpoczęcie obliczania wyniku dla pytania typu {question['answer_type']}")
            
            # Validate and convert max points
            try:
                max_points = float(question.get('points', 0))
                if max_points < 0:
                    self.logger.warning(f"Wykryto ujemną wartość punktów: {max_points}, ustawiam na 0")
                    max_points = 0
            except (ValueError, TypeError):
                self.logger.error(f"Nieprawidłowa wartość punktów: {question.get('points')}, ustawiam na 0")
                max_points = 0
            
            # Jeśli pytanie nie ma punktów, nie ma sensu liczyć
            if max_points == 0:
                return 0.0
                
            algorithm_type = question.get('algorithm_type', 'NO_ALGORITHM')
            algorithm_params = question.get('algorithm_params', {})
            
            # Handle empty/None answers
            if not answer:
                self.logger.warning("Otrzymano pustą odpowiedź, zwracam 0 punktów")
                return 0.0

            # Obliczamy wynik w zależności od typu odpowiedzi
            raw_score = self._calculate_raw_score(
                answer, 
                question, 
                max_points, 
                algorithm_type, 
                algorithm_params
            )
            
            # Zawsze zaokrąglamy do 1 miejsca po przecinku
            final_score = round(float(raw_score), 1)
            
            self.logger.debug(
                f"Wynik dla pytania {question['id']}: {final_score}/{max_points} "
                f"({(final_score/max_points * 100):.1f}% maksymalnej wartości)"
            )
            
            return final_score
            
        except Exception as e:
            self.logger.error(f"Błąd podczas obliczania wyniku: {str(e)}")
            return 0.0
            
    def _calculate_raw_score(
        self, 
        answer: dict, 
        question: dict, 
        max_points: float,
        algorithm_type: str,
        algorithm_params: dict
    ) -> float:
        """
        Oblicza surowy wynik dla odpowiedzi przed zaokrągleniem.
        
        Returns:
            float: Surowy wynik przed zaokrągleniem
        """
        answer_type = question['answer_type']
        
        self.logger.debug(f"Obliczanie wyniku dla pytania {question['id']} typu {answer_type} z algorytmem {algorithm_type}")
                
        if answer_type == 'TEXT':
            if algorithm_type == 'NO_ALGORITHM':
                return 0.0
            elif algorithm_type == 'EXACT_MATCH':
                user_answer = str(answer.get('answer', '')).strip().lower()
                correct_answer = str(algorithm_params.get('correct_answer', '')).strip().lower()
                return float(max_points) if user_answer == correct_answer else 0.0
            elif algorithm_type == 'EVALUATION_BY_AI':
                try:
                    result = self.openai_service.evaluate_answer(
                        question_text=question['question_text'],
                        answer_text=answer.get('answer', ''),
                        max_points=float(max_points),
                        algorithm_params=algorithm_params
                    )
                    if result and isinstance(result, dict):
                        score = result.get('score')
                        explanation = result.get('explanation')
                        if score is not None:
                            score = max(0.0, min(float(score), max_points))
                            self.update_answer_ai_explanation(answer['id'], explanation)
                            return score
                    return 0.0
                except Exception as e:
                    self.logger.error(f"Błąd podczas oceny AI: {str(e)}")
                    return 0.0
                    
        elif answer_type == 'BOOLEAN':
            if algorithm_type == 'EXACT_MATCH':
                try:
                    user_answer = str(answer.get('answer', '')).lower()
                    correct_answer = algorithm_params.get('correct_answer')
                    self.logger.debug(f"Odpowiedź użytkownika: {user_answer}, odpowiedź poprawna: {correct_answer}")
                    self.logger.debug(f"Wynik: {float(max_points) if user_answer == correct_answer else 0.0}")
                    return float(max_points) if user_answer == correct_answer else 0.0
                except:
                    return 0.0
                    
        elif answer_type in ['SCALE', 'SALARY', 'NUMERIC']:
            try:
                user_answer = float(str(answer.get('answer', '')).replace(',', '.'))
            except (ValueError, TypeError):
                return 0.0
                
            if algorithm_type == 'EXACT_MATCH':
                try:
                    correct_answer = float(str(algorithm_params.get('correct_answer', 0)).replace(',', '.'))
                    epsilon = 0.001 if answer_type == 'SCALE' else 0.01
                    return float(max_points) if abs(user_answer - correct_answer) < epsilon else 0.0
                except (ValueError, TypeError):
                    return 0.0
                    
            elif algorithm_type == 'RANGE':
                try:
                    min_value = float(str(algorithm_params.get('min_value', '')).replace(',', '.'))
                    max_value = float(str(algorithm_params.get('max_value', '')).replace(',', '.'))
                    return float(max_points) if min_value <= user_answer <= max_value else 0.0
                except (ValueError, TypeError):
                    return 0.0
                    
            elif algorithm_type in ['LEFT_SIDED', 'RIGHT_SIDED', 'CENTER']:
                try:
                    if algorithm_type != 'RIGHT_SIDED':
                        min_value = float(str(algorithm_params.get('min_value', '')).replace(',', '.'))
                    if algorithm_type != 'LEFT_SIDED':
                        max_value = float(str(algorithm_params.get('max_value', '')).replace(',', '.'))
                    correct_answer = float(str(algorithm_params.get('correct_answer', '')).replace(',', '.'))
                    
                    if algorithm_type == 'LEFT_SIDED':
                        if user_answer <= min_value:
                            return 0.0
                        elif user_answer >= correct_answer:
                            return float(max_points)
                        return max_points * (user_answer - min_value) / (correct_answer - min_value)
                        
                    elif algorithm_type == 'RIGHT_SIDED':
                        if user_answer >= max_value:
                            return 0.0
                        elif user_answer <= correct_answer:
                            return float(max_points)
                        return max_points * (max_value - user_answer) / (max_value - correct_answer)
                        
                    else:  # CENTER
                        if user_answer == correct_answer:
                            return float(max_points)
                        elif user_answer <= min_value or user_answer >= max_value:
                            return 0.0
                        elif user_answer < correct_answer:
                            return max_points * (user_answer - min_value) / (correct_answer - min_value)
                        else:
                            return max_points * (max_value - user_answer) / (max_value - correct_answer)
                            
                except (ValueError, TypeError, ZeroDivisionError):
                    return 0.0
                    
        elif answer_type == 'DATE':
            user_date_str = answer.get('answer')
            if not user_date_str:
                return 0.0
                
            try:
                user_date = datetime.strptime(user_date_str, '%Y-%m-%d').date()
                
                correct_date = algorithm_params.get('correct_answer')
                min_date = algorithm_params.get('min_value')
                max_date = algorithm_params.get('max_value')
                
                if algorithm_type == 'EXACT_MATCH':
                    if not correct_date:
                        return 0.0
                    if isinstance(correct_date, str):
                        correct_date = datetime.strptime(correct_date, '%Y-%m-%d').date()
                    return float(max_points) if user_date == correct_date else 0.0
                    
                elif algorithm_type == 'RANGE':
                    if not min_date or not max_date:
                        return 0.0
                    if isinstance(min_date, str):
                        min_date = datetime.strptime(min_date, '%Y-%m-%d').date()
                    if isinstance(max_date, str):
                        max_date = datetime.strptime(max_date, '%Y-%m-%d').date()
                    return float(max_points) if min_date <= user_date <= max_date else 0.0
                    
                elif algorithm_type in ['LEFT_SIDED', 'RIGHT_SIDED', 'CENTER']:
                    if algorithm_type != 'RIGHT_SIDED':
                        if not min_date or not correct_date:
                            return 0.0
                        if isinstance(min_date, str):
                            min_date = datetime.strptime(min_date, '%Y-%m-%d').date()
                    if algorithm_type != 'LEFT_SIDED':
                        if not max_date or not correct_date:
                            return 0.0
                        if isinstance(max_date, str):
                            max_date = datetime.strptime(max_date, '%Y-%m-%d').date()
                    if isinstance(correct_date, str):
                        correct_date = datetime.strptime(correct_date, '%Y-%m-%d').date()
                        
                    if algorithm_type == 'LEFT_SIDED':
                        if user_date <= min_date:
                            return 0.0
                        elif user_date >= correct_date:
                            return float(max_points)
                        total_days = (correct_date - min_date).days
                        if total_days <= 0:
                            return 0.0
                        user_days = (user_date - min_date).days
                        return max_points * (user_days / total_days)
                        
                    elif algorithm_type == 'RIGHT_SIDED':
                        if user_date >= max_date:
                            return 0.0
                        elif user_date <= correct_date:
                            return float(max_points)
                        total_days = (max_date - correct_date).days
                        if total_days <= 0:
                            return 0.0
                        user_days = (max_date - user_date).days
                        return max_points * (user_days / total_days)
                        
                    else:  # CENTER
                        if user_date == correct_date:
                            return float(max_points)
                        elif user_date <= min_date or user_date >= max_date:
                            return 0.0
                        elif user_date < correct_date:
                            total_days = (correct_date - min_date).days
                            if total_days <= 0:
                                return 0.0
                            user_days = (user_date - min_date).days
                            return max_points * (user_days / total_days)
                        else:
                            total_days = (max_date - correct_date).days
                            if total_days <= 0:
                                return 0.0
                            user_days = (max_date - user_date).days
                            return max_points * (user_days / total_days)
                            
            except (ValueError, TypeError) as e:
                self.logger.error(f"Błąd podczas obliczania wyniku dla daty: {str(e)}")
                return 0.0
                
        elif answer_type == 'ABCDEF':
            if algorithm_type == 'EXACT_MATCH':
                user_answer = str(answer.get('answer', '')).strip().lower()
                correct_answer = str(algorithm_params.get('correct_answer', '')).strip().lower()
                return float(max_points) if user_answer == correct_answer else 0.0
                
        return 0.0

    def calculate_total_score(self, answers_response: dict, questions: dict) -> float:
        """
        Oblicza łączny wynik dla wszystkich odpowiedzi.
        
        Args:
            answers_response: Odpowiedzi kandydata
            questions: Słownik z pytaniami i ich parametrami
            
        Returns:
            float: Całkowity wynik zaokrąglony do 1 miejsca po przecinku
        """
        try:
            if not answers_response.data:
                self.logger.warning("Brak odpowiedzi do oceny")
                return 0.0
                
            self.logger.info(f"Rozpoczęcie obliczania łącznego wyniku dla {len(answers_response.data)} odpowiedzi")
            
            # Przechowujemy wyniki cząstkowe dla lepszego logowania
            partial_scores = []
            total_points_possible = 0.0
            
            for answer in answers_response.data:
                question = questions.get(answer['question_id'])
                if not question:
                    self.logger.warning(f"Nie znaleziono pytania dla odpowiedzi {answer['id']}")
                    continue
                
                # Skip EQ questions as they're handled separately
                if question['answer_type'] == 'AH_POINTS':
                    self.logger.debug(f"Pominięto pytanie EQ {question['id']}")
                    continue
                
                try:
                    max_points = float(question.get('points', 0))
                    if max_points > 0:
                        total_points_possible += max_points
                        score = self.calculate_score(answer, question)
                        if score is not None and score >= 0:
                            # Zaokrąglamy każdy wynik cząstkowy do 1 miejsca po przecinku
                            rounded_score = round(score, 1)
                            partial_scores.append({
                                'question_id': question['id'],
                                'max_points': max_points,
                                'score': rounded_score
                            })
                            # Aktualizujemy wynik w bazie danych
                            self.update_answer_score(answer['id'], rounded_score)
                            self.logger.debug(
                                f"Pytanie {question['id']}: {rounded_score}/{max_points} punktów "
                                f"({(rounded_score/max_points * 100):.1f}%)"
                            )
                        else:
                            self.logger.warning(f"Otrzymano nieprawidłowy wynik {score} dla odpowiedzi {answer['id']}")
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Błąd podczas przetwarzania punktów dla pytania {question['id']}: {str(e)}")
                    continue
            
            if total_points_possible > 0:
                # Obliczamy procent zdobytych punktów
                raw_total = sum(p['score'] for p in partial_scores)
                
                # Zaokrąglamy wynik końcowy do 1 miejsca po przecinku
                final_score = round(raw_total, 1)
                
                # Logujemy szczegółowe informacje o punktacji
                self.logger.info(
                    f"Zakończono obliczanie łącznego wyniku:\n"
                    f"- Suma punktów: {raw_total:.1f}/{total_points_possible:.1f}\n"
                    f"- Wynik końcowy: {final_score}"
                )
                
                # Logujemy wyniki cząstkowe dla debugowania
                for partial in partial_scores:
                    self.logger.debug(
                        f"Pytanie {partial['question_id']}: "
                        f"{partial['score']}/{partial['max_points']} punktów"
                    )
                
                return final_score
            else:
                self.logger.warning("Brak pytań z punktami do oceny")
                return 0.0
            
        except Exception as e:
            self.logger.error(f"Błąd podczas obliczania łącznego wyniku: {str(e)}")
            return 0.0
    
    def update_answer_ai_explanation(self, answer_id: int, explanation: str) -> None:
        """
        Aktualizuje wynik dla konkretnej odpowiedzi.
        
        Args:
            answer_id: ID odpowiedzi
            score: Wynik (może być float, zostanie zaokrąglony do int)
        """
        try:
            self.supabase.table('candidate_answers').update({
                'ai_explanation': explanation
            }).eq('id', answer_id).execute()
        except Exception as e:
            self.logger.error(f"Błąd podczas aktualizowania wyniku dla odpowiedzi {answer_id}: {str(e)}")

    def update_answer_score(self, answer_id: int, score: float) -> None:
        """
        Aktualizuje wynik dla konkretnej odpowiedzi.
        
        Args:
            answer_id: ID odpowiedzi
            score: Wynik (może być float, zostanie zaokrąglony do int)
        """
        try:
            self.logger.debug(f"Aktualizacja wyniku dla odpowiedzi {answer_id}: {score} punktów")
            self.supabase.table('candidate_answers').update({
                'score': round(score)  # Round float to integer
            }).eq('id', answer_id).execute()
            self.logger.info(f"Pomyślnie zaktualizowano wynik dla odpowiedzi {answer_id}")
        except Exception as e:
            self.logger.error(f"Błąd podczas aktualizowania wyniku dla odpowiedzi {answer_id}: {str(e)}")
        
    def simulate_eq_evaluation(self, candidate_id: int, campaign_id: int, eq_scores: dict) -> None:
        """
        Symuluje odpowiedzi na test EQ_EVALUATION na podstawie wyników testu EQ.
        
        Args:
            candidate_id: ID kandydata
            campaign_id: ID kampanii
            eq_scores: Słownik z wynikami EQ (score_ko, score_re, etc.)
        """
        self.logger.info(f"Rozpoczęcie symulacji oceny EQ dla kandydata {candidate_id}")
        self.logger.debug(f"Wyniki EQ do zasymulowania: {eq_scores}")
        
        try:
            # Get campaign PO2_5 test ID
            campaign_response = self.supabase.table('campaigns')\
                .select('po2_5_test_id')\
                .eq('id', campaign_id)\
                .single()\
                .execute()
            
            if not campaign_response.data or not campaign_response.data.get('po2_5_test_id'):
                self.logger.warning(f"Nie znaleziono testu PO2_5 dla kampanii {campaign_id}")
                return
            
            po2_5_test_id = campaign_response.data['po2_5_test_id']
            
            # Get PO2_5 test questions
            questions_response = self.supabase.table('questions')\
                .select('id, question_text')\
                .eq('test_id', po2_5_test_id)\
                .execute()
            
            if not questions_response.data:
                self.logger.warning(f"Nie znaleziono pytań dla testu PO2_5 (ID: {po2_5_test_id})")
                return
            
            # Mapping of EQ scores to question_text
            eq_mapping = {
                'score_ko': 'KO',
                'score_re': 'RE',
                'score_w': 'W',
                'score_in': 'IN',
                'score_pz': 'PZ',
                'score_kz': 'KZ',
                'score_dz': 'DZ',
                'score_sw': 'SW'
            }
            
            # Create answers for each matching question
            answers_to_insert = []
            current_time = datetime.now(timezone.utc)
            
            for question in questions_response.data:
                # Find matching EQ score
                matching_score = None
                question_text_upper = question['question_text'].upper()
                
                for score_key, eq_code in eq_mapping.items():
                    if eq_code == question_text_upper:
                        matching_score = eq_scores.get(score_key)
                        break
                
                if matching_score is not None:
                    # Create answer entry
                    answer = {
                        'candidate_id': candidate_id,
                        'question_id': question['id'],
                        'stage': 'PO2_5',
                        'answer': str(matching_score),
                        'score': matching_score,
                        'created_at': current_time.isoformat()
                    }
                    answers_to_insert.append(answer)
                    self.logger.debug(f"Przygotowano odpowiedź dla pytania {question_text_upper}: {matching_score}")
                else:
                    self.logger.warning(f"Nie znaleziono odpowiadającego wyniku EQ dla pytania: {question['question_text']}")
            
            if answers_to_insert:
                # Insert all answers
                self.supabase.table('candidate_answers')\
                    .insert(answers_to_insert)\
                    .execute()
                self.logger.info(f"Pomyślnie zapisano {len(answers_to_insert)} symulowanych odpowiedzi")

                # Update candidate status
                self.supabase.table('candidates')\
                    .update({
                        'recruitment_status': 'PO2_5',
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    })\
                    .eq('id', candidate_id)\
                    .execute()
                self.logger.info(f"Zaktualizowano status kandydata {candidate_id} na PO2_5")
            else:
                self.logger.warning("Nie utworzono żadnych odpowiedzi do zapisania")
            
        except Exception as e:
            self.logger.error(f"Błąd podczas symulacji odpowiedzi EQ_EVALUATION: {str(e)}")
        