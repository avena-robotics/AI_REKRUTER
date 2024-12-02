import logging
from typing import Optional
from supabase import Client

class TestService:
    """Serwis do obliczania wyników testów kandydatów"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.logger = logging.getLogger('candidate_check')

    def calculate_test_score(self, candidate_id: int, test_id: int) -> Optional[dict]:
        """
        Oblicza wynik testu dla kandydata
        """
        try:
            self.logger.info(f"Rozpoczęcie obliczania wyniku testu {test_id} dla kandydata {candidate_id}")
            
            answers_response = self.supabase.table('candidate_answers')\
                .select('''
                    id,
                    question_id,
                    text_answer,
                    boolean_answer,
                    salary_answer,
                    scale_answer,
                    date_answer,
                    abcdef_answer,
                    points_per_option
                ''')\
                .eq('candidate_id', candidate_id)\
                .execute()
            
            if not answers_response.data:
                self.logger.warning(f"Nie znaleziono odpowiedzi dla kandydata {candidate_id} w teście {test_id}")
                return None
                
            self.logger.info(f"Znaleziono {len(answers_response.data)} odpowiedzi dla kandydata {candidate_id}")
                
            question_ids = [answer['question_id'] for answer in answers_response.data]
            questions_response = self.supabase.table('questions')\
                .select('*, tests!inner(*)')\
                .eq('test_id', test_id)\
                .in_('id', question_ids)\
                .execute()
            
            if not questions_response.data:
                self.logger.warning(f"Nie znaleziono pytań dla testu {test_id}")
                return None
                
            questions = {q['id']: q for q in questions_response.data}
            self.logger.info(f"Znaleziono {len(questions)} pytań dla testu {test_id}")
            
            # Check if there are any AH_POINTS questions
            ah_points_questions = [q for q in questions.values() if q['answer_type'] == 'AH_POINTS']
            
            if ah_points_questions:
                self.logger.info(f"Test {test_id} zawiera {len(ah_points_questions)} pytań typu AH_POINTS")
                # Calculate EQ scores for AH_POINTS questions
                eq_scores = self.calculate_eq_scores(answers_response.data, ah_points_questions)
                self.logger.info(f"Obliczone wyniki EQ dla kandydata {candidate_id}: {eq_scores}")
                return eq_scores
            else:
                self.logger.info(f"Test {test_id} nie zawiera pytań typu AH_POINTS, obliczanie standardowego wyniku")
                # Handle regular test scoring
                total_score = self.calculate_total_score(answers_response, questions)
                self.logger.info(f"Obliczony wynik standardowy dla kandydata {candidate_id}: {total_score}")
                return total_score
            
        except Exception as e:
            self.logger.error(f"Błąd podczas obliczania wyniku testu {test_id} dla kandydata {candidate_id}: {str(e)}")
            return None

    def calculate_eq_scores(self, answers, questions) -> dict:
        """
        Oblicza wyniki testu EQ dla wszystkich kategorii.
        """
        self.logger.info("Rozpoczęcie obliczania wyników EQ")
        
        eq_mapping = {
            'KO': ['d', 'b', 'a', 'h', 'f', 'c', 'g'],  # Section I to VII
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
        self.logger.debug(f"Mapowanie pytań do numerów sekcji: {question_orders}")
        
        for answer in answers:
            question_id = answer['question_id']
            if question_id not in question_orders:
                self.logger.warning(f"Pominięto odpowiedź dla pytania {question_id} - brak w mapowaniu")
                continue
                
            section_number = question_orders[question_id]
            points_per_option = answer.get('points_per_option', {})
            
            if not points_per_option:
                self.logger.warning(f"Brak przydzielonych punktów dla odpowiedzi na pytanie {question_id}")
                continue
            
            self.logger.debug(f"Przetwarzanie sekcji {section_number + 1}, punkty: {points_per_option}")
            
            # Calculate scores for each category
            for category, letters in eq_mapping.items():
                if section_number < len(letters):  # Ensure we don't exceed array bounds
                    expected_letter = letters[section_number]
                    score_key = f'score_{category.lower()}'
                    points = points_per_option.get(expected_letter, 0)
                    eq_scores[score_key] += points
                    self.logger.debug(f"Kategoria {category}: +{points} punktów za literę {expected_letter}")
            
            self.logger.debug(f"Wyniki po sekcji {section_number + 1}: {eq_scores}")
        
        self.logger.info(f"Zakończono obliczanie wyników EQ: {eq_scores}")
        return eq_scores

    def calculate_score(self, answer, question):
        """Oblicza wynik dla pojedynczej odpowiedzi na podstawie typu pytania i poprawnej odpowiedzi."""
        answer_type = question['answer_type']
        max_points = question.get('points', 0)
        
        if answer_type == 'TEXT':    
            # if not question.get('correct_answer_text'):
            #     return 0
            
            # user_answer = answer.get('text_answer', '').lower().strip()
            # correct_phrases = [
            #     phrase.lower().strip() 
            #     for phrase in question['correct_answer_text'].split(',')
            # ]
            
            # # Sprawdzenie, czy któraś z poprawnych fraz znajduje się w odpowiedzi użytkownika
            # return max_points if any(phrase in user_answer for phrase in correct_phrases) else 0
            return 0;
        
        elif answer_type == 'BOOLEAN':
            return max_points if answer.get('boolean_answer') == question.get('correct_answer_boolean') else 0
            
        elif answer_type == 'SCALE':
            user_answer = answer.get('scale_answer')
            correct_answer = question.get('correct_answer_scale')
            if user_answer is None or correct_answer is None:
                return 0
            
            max_difference = 5  # Maksymalna możliwa różnica w skali
            difference = abs(user_answer - correct_answer)
            return max(0, max_points - (difference * max_points / max_difference))
            
        elif answer_type == 'SALARY':
            user_salary = answer.get('salary_answer')
            expected_salary = question.get('correct_answer_salary')
            if user_salary is None or expected_salary is None:
                return 0
            
            # Jeśli zarobki kandydata są niższe niż oczekiwane, przyznaj maksymalną liczbę punktów
            if user_salary <= expected_salary:
                return max_points
            
            # W przeciwnym razie, oblicz proporcjonalny wynik
            return min(max_points, (expected_salary / user_salary) * max_points)
            
        elif answer_type == 'DATE':
            user_date = answer.get('date_answer')
            correct_date = question.get('correct_answer_date')
            if user_date is None or correct_date is None:
                return 0
            
            max_days = 60  # Maksymalna dopuszczalna różnica w dniach
            days_difference = abs((user_date - correct_date).days)
            
            if days_difference > max_days:
                return 0
            return max(1, max_points * (1 - days_difference / max_days))
            
        elif answer_type == 'ABCDEF':
            return max_points if answer.get('abcdef_answer') == question.get('correct_answer_abcdef') else 0
            
        return 0

    def calculate_total_score(self, answers_response, questions):
        """Oblicza łączny wynik dla wszystkich odpowiedzi."""
        total_score = 0
        
        for answer in answers_response.data:
            question = questions.get(answer['question_id'])
            if not question:
                self.logger.warning(f"Question not found for answer {answer['id']}")
                continue
            
            # Skip EQ questions as they're handled separately
            if question['answer_type'] == 'AH_POINTS':
                continue
            
            score = self.calculate_score(answer, question)
            total_score += score
            self.update_answer_score(answer['id'], score)
        
        return total_score

    def update_answer_score(self, answer_id, score):
        """Aktualizuje wynik dla konkretnej odpowiedzi."""
        try:
            self.supabase.table('candidate_answers').update({
                'score': score
            }).eq('id', answer_id).execute()
        except Exception as e:
            self.logger.error(f"Błąd podczas aktualizowania wyniku dla odpowiedzi {answer_id}: {str(e)}") 