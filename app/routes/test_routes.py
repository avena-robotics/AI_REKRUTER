import json
from flask import Blueprint, render_template, request, jsonify, session
from database import supabase
from datetime import datetime, timezone
from routes.auth_routes import login_required
from services.group_service import get_user_groups, get_test_groups
from logger import Logger
import time

test_bp = Blueprint("test", __name__, url_prefix="/tests")
logger = Logger.instance()

# Add helper function for retrying database operations
def retry_on_disconnect(operation, max_retries=3):
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            if "Server disconnected" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Utracono połączenie z serwerem, ponowne próby... (próba {attempt + 1})")
                time.sleep(1)  # Wait before retry
                continue
            raise


@test_bp.route("/")
@login_required
def list():
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            user_id = session.get("user_id")
            logger.debug(f"Pobieranie test��w dla user_id: {user_id}")
            
            # Get user groups
            try:
                user_groups = get_user_groups(user_id)
            except Exception as e:
                logger.error(f"Błąd podczas pobierania grup użytkownika: {str(e)}")
                if retry_count == max_retries - 1:
                    raise
                retry_count += 1
                time.sleep(1)  # Wait 1 second before retrying
                continue

            user_group_ids = [group["id"] for group in user_groups]
            logger.debug(f"Użytkownik należy do grup: {user_group_ids}")

            # Get tests with a single query
            try:
                tests_response = (
                    supabase.from_("tests")
                    .select(
                        "*, questions(*), link_groups_tests(group_id)",
                        count="exact",
                    )
                    .order("created_at", desc=True)
                    .execute()
                )
            except Exception as e:
                logger.error(f"Błąd podczas pobierania testów: {str(e)}")
                if retry_count == max_retries - 1:
                    raise
                retry_count += 1
                time.sleep(1)
                continue

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

            logger.debug(f"Znaleziono {len(filtered_tests)} testów dla użytkownika")
            return render_template(
                "tests/test_list.html", tests=filtered_tests, groups=user_groups
            )

        except Exception as e:
            logger.error(f"Błąd w liście testów (próba {retry_count + 1}): {str(e)}")
            if retry_count == max_retries - 1:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f"Wystąpił błąd podczas pobierania testów: {str(e)}",
                        }
                    ),
                    500,
                )
            retry_count += 1
            time.sleep(1)


@test_bp.route("/add", methods=["POST"])
def add():
    try:
        logger.debug("Rozpoczęcie tworzenia nowego testu")
        # Validate basic test data
        if not request.form.get("title"):
            logger.warning("Tytuł testu jest wymagany, ale nie został podany")
            return jsonify({"success": False, "error": "Tytuł testu jest wymagany"})

        groups = request.form.getlist("groups[]")
        if not groups:
            logger.warning("Nie wybrano żadnej grupy dla testu")
            return jsonify({"success": False, "error": "Należy wybrać co najmniej jedną grupę"})

        # Create test
        test_data = {
            "title": request.form.get("title"),
            "test_type": request.form.get("test_type"),
            "description": request.form.get("description"),
            "passing_threshold": int(request.form.get("passing_threshold", 0)),
            "time_limit_minutes": int(request.form.get("time_limit_minutes"))
            if request.form.get("time_limit_minutes")
            else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        # Insert test
        test_result = supabase.from_("tests").insert(test_data).execute()
        if not test_result.data:
            logger.error("Nie udało się utworzyć testu w bazie danych")
            raise Exception("Nie udało się utworzyć testu")

        test_id = test_result.data[0]["id"]
        logger.info(f"Pomyślnie utworzono test z ID: {test_id}")

        # Add group associations
        group_links = [{"group_id": int(gid), "test_id": test_id} for gid in groups]
        supabase.from_("link_groups_tests").insert(group_links).execute()
        logger.debug(f"Dodano powiązania grup dla testu {test_id}: {groups}")

        return jsonify({
            "success": True, 
            "message": "Test został utworzony",
            "test_id": test_id
        })

    except Exception as e:
        logger.error(f"Błąd podczas dodawania testu: {str(e)}")
        return jsonify({"success": False, "error": str(e)})


@test_bp.route("/<int:test_id>/data")
def get_test_data(test_id):
    try:
        logger.debug(f"Pobieranie danych testu o ID: {test_id}")
        # Single query to get test with questions and groups
        test = (
            supabase.from_("tests")
            .select("*, questions(id, question_text, answer_type, points, order_number, is_required, image, options, algorithm_type, algorithm_params, correct_answer_text, correct_answer_boolean, correct_answer_salary, correct_answer_scale, correct_answer_date, correct_answer_abcdef), link_groups_tests(group_id)")
            .eq("id", test_id)
            .single()
            .execute()
        )

        if not test.data:
            logger.warning(f"Nie znaleziono testu o ID: {test_id}")
            return jsonify({"error": "Test not found"}), 404

        # Process questions
        questions = test.data.pop("questions", [])
        test.data["questions"] = sorted(
            questions, key=lambda x: x.get("order_number", 0)
        )
        logger.debug(f"Przetworzono {len(questions)} pytań dla testu {test_id}")
        # Log first question details for debugging
        if questions:
            logger.debug(f"Przykładowe pytanie:")
            logger.debug(f"- ID: {questions[0].get('id')}")
            logger.debug(f"- Typ algorytmu: {questions[0].get('algorithm_type')}")
            logger.debug(f"- Parametry algorytmu: {questions[0].get('algorithm_params')}")

        # Process groups
        test.data["groups"] = get_test_groups(test_id)
        logger.debug(f"Pobrano grupy dla testu {test_id}")

        return jsonify(test.data)

    except Exception as e:
        logger.error(f"Błąd podczas pobierania danych testu {test_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


@test_bp.route("/<int:test_id>/edit", methods=["POST"])
def edit(test_id):
    try:
        print(f"Starting edit process for test ID: {test_id}")
        
        # Log the entire request form data
        logger.debug("Request form data:")
        for key, value in request.form.items():
            logger.debug(f"- {key}: {value[:100] if isinstance(value, str) else value}")  # Limit long strings

        # Get original test data for comparison
        original_test = supabase.from_("tests").select("*").eq("id", test_id).single().execute()
        if not original_test.data:
            return jsonify({"success": False, "error": "Test nie istnieje"})

        print(f"Original test data loaded: {original_test.data}")

        # Prepare only changed test data
        test_data = {}
        form_data = {
            "title": request.form.get("title"),
            "test_type": request.form.get("test_type"),
            "description": request.form.get("description"),
            "passing_threshold": int(request.form.get("passing_threshold", 0)),
            "time_limit_minutes": int(request.form.get("time_limit_minutes", 0))
            if request.form.get("time_limit_minutes")
            else None,
        }

        # Only include changed fields
        for key, value in form_data.items():
            if original_test.data.get(key) != value:
                test_data[key] = value
                print(f"Field '{key}' changed from '{original_test.data.get(key)}' to '{value}'")

        # Only update test if there are changes
        if test_data:
            print(f"Updating test with data: {test_data}")
            test_result = supabase.from_("tests").update(test_data).eq("id", test_id).execute()
            if not test_result.data:
                raise Exception("Nie udało się zaktualizować testu")

        # Process questions only if they are present in the request
        questions_json = request.form.get("questions")
        if questions_json:
            questions = json.loads(questions_json)
            logger.debug(f"Received questions data (raw):")
            logger.debug(json.dumps(questions, indent=2))
            
            original_questions = {q["id"]: q for q in supabase.from_("questions")
                                .select("*")
                                .eq("test_id", test_id)
                                .execute().data}
            logger.debug(f"Original questions data:")
            logger.debug(json.dumps(original_questions, indent=2))

            questions_to_update = []
            questions_to_insert = []
            questions_to_delete = set(original_questions.keys())

            for question in questions:
                question_id = question.get("id")
                logger.debug(f"\nProcessing question {question_id}:")
                logger.debug(f"Received question data:")
                logger.debug(json.dumps(question, indent=2))

                # Clean algorithm params - convert empty strings to None and strings to integers
                if "algorithm_params" in question and isinstance(question["algorithm_params"], dict):
                    cleaned_params = {}
                    for key, value in question["algorithm_params"].items():
                        if value is None or value == "":
                            cleaned_params[key] = None
                        else:
                            try:
                                cleaned_params[key] = int(value)
                            except (TypeError, ValueError):
                                cleaned_params[key] = None
                    question["algorithm_params"] = cleaned_params
                
                if question_id and str(question_id).isdigit():
                    question_id = int(question_id)
                    if question_id in original_questions:
                        original = original_questions[question_id]
                        logger.debug(f"Original question data:")
                        logger.debug(json.dumps(original, indent=2))

                        changed_fields = {}
                        
                        # Prepare base question data with only fields that exist in original
                        clean_question = {
                            "question_text": question["question_text"],
                            "answer_type": question["answer_type"],
                            "points": int(question.get("points", 0)),
                            "order_number": question.get("order_number", 1),
                            "is_required": question.get("is_required", True),
                            "algorithm_type": question.get("algorithm_type", "NO_ALGORITHM"),
                            "algorithm_params": question.get("algorithm_params", {})
                        }

                        # Compare and collect only changed fields
                        for key, value in clean_question.items():
                            # Special handling for algorithm_params as it's a JSON field
                            if key == 'algorithm_params':
                                orig_params = original.get(key) or {}
                                if orig_params != value:
                                    logger.debug(f"Zmiana w parametrach algorytmu:")
                                    logger.debug(f"- Oryginalne: {orig_params}")
                                    logger.debug(f"- Nowe: {value}")
                                    changed_fields[key] = value
                            elif original.get(key) != value:
                                changed_fields[key] = value
                                logger.debug(f"Zmiana w polu '{key}': '{original.get(key)}' -> '{value}'")

                        # Handle image separately
                        if "image" in question and question["image"]:
                            if question_id not in original_questions or \
                               original_questions[question_id].get("image") != question["image"]:
                                changed_fields["image"] = question["image"]
                                print(f"Question {question_id} image changed")

                        # Handle answer type specific data
                        if question["answer_type"] == "AH_POINTS":
                            if "options" in question and isinstance(question["options"], dict):
                                new_options = {
                                    k: v for k, v in question["options"].items()
                                    if k in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and v
                                }
                                if original.get("options") != new_options:
                                    changed_fields["options"] = new_options
                                    print(f"Question {question_id} options changed")
                        else:
                            answer_field = f'correct_answer_{question["answer_type"].lower()}'
                            if answer_field in question and question[answer_field] is not None:
                                if original.get(answer_field) != question[answer_field]:
                                    changed_fields[answer_field] = question[answer_field]
                                    print(f"Question {question_id} answer changed")
                        
                        if changed_fields:
                            questions_to_update.append({
                                "id": question_id,
                                "data": changed_fields
                            })
                            logger.debug(f"Pytanie {question_id} będzie zaktualizowane z danymi: {changed_fields}")
                        questions_to_delete.remove(question_id)
                else:
                    # This is a new question
                    new_question = {
                        "test_id": test_id,
                        "question_text": question["question_text"],
                        "answer_type": question["answer_type"],
                        "points": int(question.get("points", 0)),
                        "order_number": question.get("order_number", 1),
                        "is_required": question.get("is_required", True),
                        "image": question.get("image"),
                        "algorithm_type": question.get("algorithm_type", "NO_ALGORITHM"),
                        "algorithm_params": question.get("algorithm_params", {})
                    }

                    # Handle answer type specific data
                    if question["answer_type"] == "AH_POINTS":
                        if "options" in question and isinstance(question["options"], dict):
                            new_question["options"] = {
                                k: v for k, v in question["options"].items()
                                if k in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and v
                            }
                    else:
                        answer_field = f'correct_answer_{question["answer_type"].lower()}'
                        if answer_field in question and question[answer_field] is not None:
                            new_question[answer_field] = question[answer_field]

                    questions_to_insert.append(new_question)
                    logger.debug(f"New question prepared for insertion: {json.dumps(new_question, indent=2)}")

            # Process updates and inserts with additional logging
            for question in questions_to_update:
                logger.debug(f"Updating question {question['id']}:")
                logger.debug(f"Update data: {json.dumps(question['data'], indent=2)}")
                try:
                    result = supabase.from_("questions").update(
                        question["data"]
                    ).eq("id", question["id"]).execute()
                    logger.debug(f"Update result: {json.dumps(result.data, indent=2)}")
                except Exception as e:
                    logger.error(f"Error updating question {question['id']}: {str(e)}")
                    raise

            if questions_to_insert:
                logger.debug("Inserting new questions:")
                logger.debug(json.dumps(questions_to_insert, indent=2))
                try:
                    result = supabase.from_("questions").insert(questions_to_insert).execute()
                    logger.debug(f"Insert result: {json.dumps(result.data, indent=2)}")
                except Exception as e:
                    logger.error(f"Error inserting questions: {str(e)}")
                    raise

            # Delete removed questions only if explicitly requested
            if questions_to_delete and len(questions) > 0:  # Only delete if questions were actually sent
                print(f"Deleting questions: {questions_to_delete}")
                supabase.from_("questions").delete().in_("id", list(questions_to_delete)).execute()

        return jsonify({
            "success": True,
            "message": "Test został zaktualizowany pomyślnie"
        })

    except Exception as e:
        logger.error(f"Błąd podczas edycji testu: {str(e)}")
        return jsonify({"success": False, "error": str(e)})


@test_bp.route("/<int:test_id>/delete", methods=["POST"])
def delete(test_id):
    try:
        logger.debug(f"Próba usunięcia testu {test_id}")
        # Single query to check campaign usage
        campaigns = (
            supabase.from_("campaigns")
            .select("id")
            .or_(
                f"po1_test_id.eq.{test_id},po2_test_id.eq.{test_id},po3_test_id.eq.{test_id}"
            )
            .execute()
        )

        if campaigns.data:
            return jsonify(
                {
                    "success": False,
                    "error": "Test nie może zostać usunięty, ponieważ jest używany w kampanii",
                }
            )

        supabase.from_("tests").delete().eq("id", test_id).execute()
        logger.info(f"Pomyślnie usunięto test {test_id}")
        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Błąd podczas usuwania testu {test_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)})


@test_bp.route("/<int:test_id>/edit/questions", methods=["POST"])
def edit_questions(test_id):
    try:
        questions = json.loads(request.form.get("questions", "[]"))
        logger.debug(f"Rozpoczęto przetwarzanie {len(questions)} pytań dla testu {test_id}")
        
        original_questions = {q["id"]: q for q in supabase.from_("questions")
                            .select("*")
                            .eq("test_id", test_id)
                            .execute().data}
        logger.debug(f"Pobrano {len(original_questions)} istniejących pytań")

        questions_to_update = []
        questions_to_insert = []
        questions_to_delete = set()

        for question in questions:
            question_id = question.get("id")
            
            if question_id and str(question_id).isdigit():
                question_id = int(question_id)
                if question_id in original_questions:
                    # Compare with original question
                    original = original_questions[question_id]
                    changed_fields = {}
                    
                    # Compare and collect only changed fields
                    for key, value in question.items():
                        if key != 'id' and original.get(key) != value:
                            changed_fields[key] = value
                            logger.debug(f"Wykryto zmianę w pytaniu {question_id}, pole '{key}'")
                    
                    if changed_fields:
                        questions_to_update.append({
                            "id": question_id,
                            "data": changed_fields
                        })
            else:
                # This is a new question
                question['test_id'] = test_id
                questions_to_insert.append(question)

        # Process updates and inserts
        for question in questions_to_update:
            logger.info(f"Aktualizacja pytania {question['id']}")
            supabase.from_("questions").update(
                question["data"]
            ).eq("id", question["id"]).execute()

        if questions_to_insert:
            logger.info(f"Dodawanie {len(questions_to_insert)} nowych pytań")
            supabase.from_("questions").insert(questions_to_insert).execute()

        logger.info(f"Pomyślnie zaktualizowano pytania dla testu {test_id}")
        return jsonify({
            "success": True,
            "message": "Pytania zostały zaktualizowane"
        })

    except Exception as e:
        logger.error(f"Błąd podczas przetwarzania pytań dla testu {test_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)})


@test_bp.route("/add/questions", methods=["POST"])
def add_questions():
    try:
        questions = json.loads(request.form.get("questions", "[]"))
        test_id = request.form.get("test_id")
        logger.debug(f"Rozpoczęto dodawanie pytań do testu {test_id}")
        logger.debug(f"Otrzymane pytania: {json.dumps(questions, indent=2)}")

        if not test_id:
            logger.error("Brak parametru test_id")
            raise Exception("Missing test_id parameter")

        questions_to_insert = []
        for i, question in enumerate(questions):
            logger.debug(f"Przetwarzanie pytania {i + 1}:")
            logger.debug(f"- Typ algorytmu: {question.get('algorithm_type', 'NO_ALGORITHM')}")
            logger.debug(f"- Parametry algorytmu: {question.get('algorithm_params', {})}")

            clean_question = {
                "test_id": int(test_id),
                "question_text": question["question_text"],
                "answer_type": question["answer_type"],
                "points": int(question.get("points", 0)),
                "order_number": question.get("order_number", 1),
                "is_required": question.get("is_required", True),
                "image": question.get("image"),
                "algorithm_type": question.get("algorithm_type", "NO_ALGORITHM"),
                "algorithm_params": question.get("algorithm_params", {})
            }
            
            logger.debug(f"Oczyszczone pytanie {i + 1}:")
            logger.debug(f"- Typ algorytmu (po czyszczeniu): {clean_question['algorithm_type']}")
            logger.debug(f"- Parametry algorytmu (po czyszczeniu): {clean_question['algorithm_params']}")

            if question["answer_type"] == "AH_POINTS":
                if "options" in question and isinstance(question["options"], dict):
                    clean_question["options"] = {
                        k: v for k, v in question["options"].items()
                        if k in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and v
                    }
            else:
                answer_field = f'correct_answer_{question["answer_type"].lower()}'
                if answer_field in question and question[answer_field] is not None:
                    clean_question[answer_field] = question[answer_field]

            questions_to_insert.append(clean_question)

        if questions_to_insert:
            logger.info(f"Dodawanie {len(questions_to_insert)} pytań do testu {test_id}")
            logger.debug("Pytania do wstawienia:")
            for i, q in enumerate(questions_to_insert):
                logger.debug(f"Pytanie {i + 1}:")
                logger.debug(f"- Tekst: {q['question_text'][:50]}...")
                logger.debug(f"- Typ algorytmu: {q['algorithm_type']}")
                logger.debug(f"- Parametry algorytmu: {q['algorithm_params']}")

            result = supabase.from_("questions").insert(questions_to_insert).execute()
            logger.debug(f"Wynik zapytania do bazy: {result.data}")
            logger.info(f"Pomyślnie dodano pytania do testu {test_id}")

        return jsonify({
            "success": True,
            "message": "Pytania zostały dodane"
        })

    except Exception as e:
        logger.error(f"Błąd podczas dodawania pytań: {str(e)}")
        return jsonify({"success": False, "error": str(e)})