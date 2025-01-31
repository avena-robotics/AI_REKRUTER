from database import supabase
from common.logger import Logger
from typing import Dict, List, Optional, Union
from datetime import datetime, timezone
import json
import time

logger = Logger.instance()

class TestException(Exception):
    """Wyjątek używany do obsługi błędów związanych z testami."""
    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class TestService:

    @staticmethod
    def get_tests_for_groups(group_ids: List[int]) -> List[Dict]:
        """
        Pobiera testy dla podanych grup bezpośrednio z tabel, bez użycia funkcji get_group_tests.
        """
        try:
            response = supabase \
                .from_("link_groups_tests") \
                .select("test_id, tests!inner(id, test_type, title, description)") \
                .in_("group_id", group_ids) \
                .execute()

            data = response.data or []

            # W danych zwracanych przez powyższe zapytanie każdy rekord zawiera
            # link_groups_tests.test_id oraz obiekt tests z kluczami: id, test_type, title, description
            # Zduplikowane testy trzeba zmergować w pojedynczą listę:
            tests_by_id = {}
            for row in data:
                t = row["tests"]
                tests_by_id[t["id"]] = t

            # Sortowanie wg test_type (aby odzwierciedlić ORDER BY z oryginalnej funkcji):
            sorted_tests = sorted(tests_by_id.values(), key=lambda x: x["test_type"])
            return sorted_tests

        except Exception as e:
            logger.error(f"Błąd podczas pobierania testów dla grup {group_ids}: {str(e)}")
            raise TestException(
                message="Błąd podczas pobierania testów dla grup.",
                original_error=e
            )
    
    # @staticmethod
    # def get_tests_for_groups(group_ids: List[int]) -> List[Dict]:
    #     """
    #     Pobiera testy dla podanych grup.
    
    #     Args:
    #         group_ids (List[int]): Lista ID grup
            
    #     Returns:
    #         List[Dict]: Lista testów
            
    #     Raises:
    #         TestException: Gdy wystąpi błąd podczas pobierania testów
    #     """
    #     try:
    #         tests_response = supabase.rpc('get_group_tests', {
    #             'p_group_ids': group_ids
    #         }).execute()
            
    #         return tests_response.data or []
            
    #     except Exception as e:
    #         logger.error(f"Błąd podczas pobierania testów dla grup {group_ids}: {str(e)}")
    #         raise TestException(
    #             message="Błąd podczas pobierania testów dla grup.",
    #             original_error=e
    #         )

    @staticmethod
    def create_test(
        title: str,
        test_type: str,
        description: str,
        passing_threshold: int,
        time_limit_minutes: Optional[int],
        groups: List[int],
        questions: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Tworzy nowy test wraz z powiązaniami do grup i pytaniami.
        
        Args:
            title (str): Tytuł testu
            test_type (str): Typ testu
            description (str): Opis testu
            passing_threshold (int): Próg zaliczenia
            time_limit_minutes (Optional[int]): Limit czasu w minutach
            groups (List[int]): Lista ID grup
            questions (Optional[List[Dict]]): Lista pytań
            
        Returns:
            Dict: Dane utworzonego testu
            
        Raises:
            TestException: Gdy wystąpi błąd podczas tworzenia testu
        """
        try:
            # Create test
            test_data = {
                "title": title,
                "test_type": test_type,
                "description": description,
                "passing_threshold": passing_threshold,
                "time_limit_minutes": time_limit_minutes,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

            # Insert test
            test_result = supabase.from_("tests").insert(test_data).execute()
            if not test_result.data:
                logger.error(f"Nie udało się utworzyć testu: {test_result.error}")
                raise TestException(message="Nie udało się utworzyć testu")

            test_id = test_result.data[0]["id"]
            logger.info(f"Pomyślnie utworzono test z ID: {test_id}")

            # Add group associations
            group_links = [{"group_id": int(gid), "test_id": test_id} for gid in groups]
            supabase.from_("link_groups_tests").insert(group_links).execute()

            # Add questions if provided
            if questions:
                # Add test_id to each question
                for question in questions:
                    question['test_id'] = test_id
                
                questions_result = supabase.from_("questions").insert(questions).execute()
                if not questions_result.data:
                    logger.error(f"Nie udało się dodać pytań do testu: {questions_result.error}")
                    raise TestException(message="Nie udało się dodać pytań do testu")
                
                logger.info(f"Pomyślnie dodano {len(questions)} pytań do testu {test_id}")

            return {"test_id": test_id}

        except TestException:
            raise
        except Exception as e:
            logger.error(f"Błąd podczas tworzenia testu: {str(e)}")
            raise TestException(
                message="Wystąpił błąd podczas tworzenia testu",
                original_error=e
            )

    @staticmethod
    def get_test_details(test_id: int) -> Dict:
        """
        Pobiera szczegółowe dane testu wraz z pytaniami i grupami.
        
        Args:
            test_id (int): ID testu
            
        Returns:
            Dict: Dane testu z pytaniami i grupami
            
        Raises:
            TestException: Gdy wystąpi błąd podczas pobierania danych testu
        """
        try:
            # Single query to get test with questions and groups
            test = (
                supabase.from_("tests")
                .select("*, questions(id, question_text, answer_type, points, order_number, is_required, image, options, algorithm_type, algorithm_params), link_groups_tests(group_id)")
                .eq("id", test_id)
                .single()
                .execute()
            )

            if not test.data:
                logger.warning(f"Nie znaleziono testu o ID: {test_id}")
                raise TestException(message="Test nie został znaleziony")

            # Process questions
            questions = test.data.pop("questions", [])
            test.data["questions"] = sorted(
                questions, key=lambda x: x.get("order_number", 0)
            )

            # Process groups
            test.data["groups"] = TestService.get_test_groups(test_id)

            return test.data

        except TestException:
            raise
        except Exception as e:
            logger.error(f"Błąd podczas pobierania danych testu {test_id}: {str(e)}")
            raise TestException(
                message="Wystąpił błąd podczas pobierania danych testu",
                original_error=e
            )

    @staticmethod
    def update_test(
        test_id: int,
        title: Optional[str] = None,
        test_type: Optional[str] = None,
        description: Optional[str] = None,
        passing_threshold: Optional[int] = None,
        time_limit_minutes: Optional[int] = None,
        groups: Optional[List[int]] = None,
        questions: Optional[Dict] = None
    ) -> None:
        """
        Aktualizuje dane testu.
        
        Args:
            test_id (int): ID testu
            title (Optional[str]): Nowy tytuł
            test_type (Optional[str]): Nowy typ
            description (Optional[str]): Nowy opis
            passing_threshold (Optional[int]): Nowy próg
            time_limit_minutes (Optional[int]): Nowy limit czasu
            groups (Optional[List[int]]): Nowa lista grup
            questions (Dict): Słownik zawierający pytania do dodania, modyfikacji lub usunięcia
            
        Raises:
            TestException: Gdy wystąpi błąd podczas aktualizacji
        """
        try:
            # Get original test
            original_test = supabase.from_("tests").select("*").eq("id", test_id).single().execute()
            if not original_test.data:
                raise TestException(message="Test nie istnieje")

            # Prepare update data
            test_data = {}
            if title is not None and original_test.data['title'] != title:
                test_data['title'] = title
            if test_type is not None and original_test.data['test_type'] != test_type:
                test_data['test_type'] = test_type
            if description is not None and original_test.data['description'] != description:
                test_data['description'] = description
            if passing_threshold is not None and original_test.data['passing_threshold'] != passing_threshold:
                test_data['passing_threshold'] = passing_threshold
            if time_limit_minutes is not None:
                try:
                    time_limit_value = int(time_limit_minutes) if time_limit_minutes else None
                    if original_test.data['time_limit_minutes'] != time_limit_value:
                        test_data['time_limit_minutes'] = time_limit_value
                except (ValueError, TypeError):
                    logger.warning(f"Invalid time_limit_minutes value: {time_limit_minutes}")
                    test_data['time_limit_minutes'] = None

            # Update test if there are changes
            if test_data:
                test_data['updated_at'] = datetime.now(timezone.utc).isoformat()
                test_result = supabase.from_("tests").update(test_data).eq("id", test_id).execute()
                if not test_result.data:
                    raise TestException(message="Nie udało się zaktualizować testu")

            # Update groups if provided
            if groups is not None:
                # Delete old links
                current_groups = supabase.from_("link_groups_tests")\
                    .select("group_id")\
                    .eq("test_id", test_id)\
                    .execute()
                
                current_group_ids = {str(g['group_id']) for g in current_groups.data}
                new_group_ids = set(groups)
                
                # Remove groups that are no longer associated
                groups_to_remove = current_group_ids - new_group_ids
                if groups_to_remove:
                    supabase.from_("link_groups_tests")\
                        .delete()\
                        .eq("test_id", test_id)\
                        .in_("group_id", list(groups_to_remove))\
                        .execute()
                
                # Add new group associations
                groups_to_add = new_group_ids - current_group_ids
                if groups_to_add:
                    group_links = [{"group_id": int(gid), "test_id": test_id} for gid in groups_to_add]
                    supabase.from_("link_groups_tests").insert(group_links).execute()

            # Update questions if provided
            if questions is not None:
                # Process added questions
                if questions.get('added'):
                    new_questions = [{
                        'test_id': test_id,
                        **question
                    } for question in questions['added']]
                    if new_questions:
                        supabase.from_("questions").insert(new_questions).execute()
                
                # Process modified questions
                if questions.get('modified'):
                    for mod in questions['modified']:
                        if mod['changes']:  # Only update if there are actual changes
                            supabase.from_("questions")\
                                .update(mod['changes'])\
                                .eq("id", mod['id'])\
                                .execute()
                
                # Process deleted questions
                if questions.get('deleted'):
                    supabase.from_("questions")\
                        .delete()\
                        .in_("id", questions['deleted'])\
                        .execute()

        except TestException:
            raise
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji testu {test_id}: {str(e)}")
            raise TestException(
                message="Wystąpił błąd podczas aktualizacji testu",
                original_error=e
            )

    @staticmethod
    def delete_test(test_id: int) -> None:
        """
        Usuwa test jeśli nie jest używany w żadnej kampanii.
        
        Args:
            test_id (int): ID testu
            
        Raises:
            TestException: Gdy test jest używany lub wystąpił błąd
        """
        try:
            # Check campaign usage
            campaigns = (
                supabase.from_("campaigns")
                .select("id")
                .or_(
                    f"po1_test_id.eq.{test_id},po2_test_id.eq.{test_id},po3_test_id.eq.{test_id}"
                )
                .execute()
            )

            if campaigns.data:
                raise TestException(
                    message="Test nie może zostać usunięty, ponieważ jest używany w kampanii"
                )

            # Delete test
            result = supabase.from_("tests").delete().eq("id", test_id).execute()
            if not result.data:
                raise TestException(message="Nie udało się usunąć testu")

            logger.info(f"Pomyślnie usunięto test {test_id}")

        except TestException:
            raise
        except Exception as e:
            logger.error(f"Błąd podczas usuwania testu {test_id}: {str(e)}")
            raise TestException(
                message="Wystąpił błąd podczas usuwania testu",
                original_error=e
            )

    @staticmethod
    def add_questions(test_id: int, questions: List[Dict]) -> None:
        """
        Dodaje pytania do testu.
        
        Args:
            test_id (int): ID testu
            questions (List[Dict]): Lista pytań do dodania
            
        Raises:
            TestException: Gdy wystąpi błąd podczas dodawania pytań
        """
        try:
            questions_to_insert = []
            for question in questions:
                clean_question = {
                    "test_id": test_id,
                    "question_text": question["question_text"],
                    "answer_type": question["answer_type"],
                    "points": int(question.get("points", 0)),
                    "order_number": int(question.get("order_number", 1)),
                    "is_required": question.get("is_required", True),
                    "image": question.get("image"),
                    "algorithm_type": question.get("algorithm_type", "NO_ALGORITHM"),
                    "algorithm_params": TestService.clean_algorithm_params(
                        question["answer_type"],
                        question.get("algorithm_params", {})
                    )
                }
                
                if question["answer_type"] == "AH_POINTS":
                    if "options" in question and isinstance(question["options"], dict):
                        clean_question["options"] = {
                            k: v for k, v in question["options"].items()
                            if k in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and v
                        }

                questions_to_insert.append(clean_question)

            if questions_to_insert:
                result = supabase.from_("questions").insert(questions_to_insert).execute()
                if not result.data:
                    raise TestException(message="Nie udało się dodać pytań")

                logger.info(f"Pomyślnie dodano {len(questions_to_insert)} pytań do testu {test_id}")

        except TestException:
            raise
        except Exception as e:
            logger.error(f"Błąd podczas dodawania pytań do testu {test_id}: {str(e)}")
            raise TestException(
                message="Wystąpił błąd podczas dodawania pytań",
                original_error=e
            )

    @staticmethod
    def clean_algorithm_params(answer_type: str, params: Dict) -> Dict:
        """Helper method to clean algorithm parameters based on answer type."""
        if not params:
            return {}
            
        clean_params = {}
        
        # Handle min_value and max_value based on answer_type
        if 'min_value' in params:
            if answer_type == 'DATE':
                clean_params['min_value'] = params['min_value'] if params['min_value'] else None
            else:
                try:
                    clean_params['min_value'] = float(params['min_value'])
                except (ValueError, TypeError):
                    clean_params['min_value'] = None
                
        if 'max_value' in params:
            if answer_type == 'DATE':
                clean_params['max_value'] = params['max_value'] if params['max_value'] else None
            else:
                try:
                    clean_params['max_value'] = float(params['max_value'])
                except (ValueError, TypeError):
                    clean_params['max_value'] = None
        
        # Handle correct_answer based on answer_type
        if 'correct_answer' in params:
            value = params['correct_answer']
            if answer_type == 'BOOLEAN':
                clean_params['correct_answer'] = value.lower() == 'true' if isinstance(value, str) else bool(value)
            elif answer_type in ('SCALE', 'SALARY', 'NUMERIC'):
                try:
                    clean_params['correct_answer'] = float(value)
                except (ValueError, TypeError):
                    clean_params['correct_answer'] = None
            elif answer_type == 'DATE':
                clean_params['correct_answer'] = value if value else None
            else:
                clean_params['correct_answer'] = str(value) if value else None
                
        return clean_params

    @staticmethod
    def get_test_groups(test_id: int) -> List[Dict]:
        """
        Pobiera pełne dane grup przypisanych do testu.
        
        Args:
            test_id (int): ID testu
            
        Returns:
            List[Dict]: Lista grup z pełnymi danymi
        """
        try:
            result = supabase.from_("link_groups_tests")\
                .select("groups:group_id(*)")\
                .eq("test_id", test_id)\
                .execute()
            
            return [item["groups"] for item in (result.data or [])]
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania grup testu {test_id}: {str(e)}")
            return []

    @staticmethod
    def edit_questions(test_id: int, questions: List[Dict]) -> None:
        """
        Edytuje pytania w teście.
        
        Args:
            test_id (int): ID testu
            questions (List[Dict]): Lista pytań do edycji
            
        Raises:
            TestException: Gdy wystąpi błąd podczas edycji pytań
        """
        try:
            # Get existing questions
            existing_questions = supabase.from_("questions")\
                .select("*")\
                .eq("test_id", test_id)\
                .execute()
                
            existing_ids = {q["id"] for q in existing_questions.data}
            questions_to_update = []
            questions_to_insert = []
            questions_to_delete = set(existing_ids)
 
            for i, question in enumerate(questions): 
                question_id = question.get("id")
                if question_id and str(question_id).strip():
                    # Update existing question 
                    try:
                        question_id = int(question_id)
                    except ValueError as e:
                        logger.error(f"Nieprawidłowe ID pytania: {question_id}")
                        raise TestException(message="Nieprawidłowe ID pytania")
                    
                    if question_id in existing_ids:
                        original = next(q for q in existing_questions.data if q["id"] == question_id) 
                        
                        changed_fields = {}
                        # Check each field for changes
                        for field in ["question_text", "answer_type", "points", "order_number", 
                                    "is_required", "image", "algorithm_type", "algorithm_params", "options"]:
                            new_value = question.get(field)
                            if new_value is not None and new_value != original.get(field):
                                changed_fields[field] = new_value
                        
                        if changed_fields:
                            questions_to_update.append({
                                "id": question_id,
                                "data": changed_fields
                            }) 
                        questions_to_delete.remove(question_id)
                else:
                    # New question 
                    try:
                        new_question = {
                            "test_id": test_id,
                            "question_text": question["question_text"],
                            "answer_type": question["answer_type"],
                            "points": int(question.get("points", 0)),
                            "order_number": int(question.get("order_number", 1)),
                            "is_required": question.get("is_required", True),
                            "image": question.get("image"),
                            "algorithm_type": question.get("algorithm_type", "NO_ALGORITHM"),
                            "algorithm_params": TestService.clean_algorithm_params(
                                question["answer_type"],
                                question.get("algorithm_params", {})
                            )
                        }
                        
                        if question["answer_type"] == "AH_POINTS":
                            if "options" in question and isinstance(question["options"], dict):
                                new_question["options"] = {
                                    k: v for k, v in question["options"].items()
                                    if k in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and v
                                }
                    
                        questions_to_insert.append(new_question)
                    except Exception as e:
                        logger.error(f"Błąd podczas przetwarzania nowego pytania: {str(e)}")
                        logger.error(f"Dane pytania: {json.dumps(question, indent=2)}")
                        raise TestException(message="Błąd podczas przetwarzania nowego pytania")

            # Process updates
            for question in questions_to_update: 
                try:
                    supabase.from_("questions")\
                        .update(question["data"])\
                        .eq("id", question["id"])\
                        .execute()
                except Exception as e:
                    logger.error(f"Błąd podczas aktualizacji pytania {question['id']}: {str(e)}")
                    raise TestException(message=f"Błąd podczas aktualizacji pytania {question['id']}")

            # Process inserts
            if questions_to_insert: 
                try:
                    supabase.from_("questions")\
                        .insert(questions_to_insert)\
                        .execute() 
                except Exception as e:
                    logger.error(f"Błąd podczas dodawania pytań: {str(e)}")
                    logger.error(f"Dane do dodania: {json.dumps(questions_to_insert, indent=2)}")
                    raise TestException(message="Błąd podczas dodawania nowych pytań")

            # Process deletes
            if questions_to_delete: 
                try:
                    questions_to_delete_list = list(questions_to_delete)
                    supabase.from_("questions")\
                        .delete()\
                        .in_("id", questions_to_delete_list)\
                        .execute()
                except Exception as e:
                    logger.error(f"Błąd podczas usuwania pytań: {str(e)}")
                    raise TestException(message="Błąd podczas usuwania pytań")

        except TestException:
            raise
        except Exception as e:
            logger.error(f"Błąd podczas edycji pytań testu {test_id}: {str(e)}")
            raise TestException(
                message="Wystąpił błąd podczas edycji pytań",
                original_error=e
            )

    @staticmethod
    def get_tests_with_details(user_groups: List[Dict], max_retries: int = 3) -> List[Dict]:
        """
        Pobiera szczegółowe dane testów dla podanych grup użytkownika.
        
        Args:
            user_groups (List[Dict]): Lista grup użytkownika
            max_retries (int): Maksymalna liczba prób pobrania danych
            
        Returns:
            List[Dict]: Lista testów z przetworzonymi danymi
            
        Raises:
            TestException: Gdy wystąpi błąd podczas pobierania testów
        """
        retry_count = 0
        user_group_ids = [group["id"] for group in user_groups]
        
        while retry_count < max_retries:
            try:
                # Get tests with a single query
                tests_response = (
                    supabase.from_("tests")
                    .select(
                        "*, questions(*), link_groups_tests(group_id)",
                        count="exact",
                    )
                    .order("created_at", desc=True)
                    .execute()
                )

                filtered_tests = []
                for test in tests_response.data:
                    # Process questions data
                    questions = test.pop("questions", [])
                    test["questions"] = questions
                    test["question_count"] = len(questions)
                    test["total_points"] = sum(q.get("points", 0) for q in questions)

                    # Process groups data
                    test_group_ids = [
                        link["group_id"] for link in test.pop("link_groups_tests", [])
                    ]
                    test["groups"] = [g for g in user_groups if g["id"] in test_group_ids]

                    # Filter tests based on user groups
                    if any(group_id in user_group_ids for group_id in test_group_ids):
                        filtered_tests.append(test)

                return filtered_tests

            except Exception as e:
                logger.error(f"Błąd podczas pobierania testów (próba {retry_count + 1}): {str(e)}")
                if retry_count == max_retries - 1:
                    raise TestException(
                        message=f"Wystąpił błąd podczas pobierania testów: {str(e)}",
                        original_error=e
                    )
                retry_count += 1
                time.sleep(1)