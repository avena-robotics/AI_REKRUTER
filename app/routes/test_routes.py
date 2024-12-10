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
            return jsonify({"error": "Test not found"}), 404

        # Process questions
        questions = test.data.pop("questions", [])
        test.data["questions"] = sorted(
            questions, key=lambda x: x.get("order_number", 0)
        )

        # Process groups
        test.data["groups"] = get_test_groups(test_id) 

        return jsonify(test.data)

    except Exception as e:
        logger.error(f"Błąd podczas pobierania danych testu {test_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


@test_bp.route("/<int:test_id>/edit", methods=["POST"])
def edit(test_id):
    try:
        # Get original test data for comparison
        original_test = supabase.from_("tests").select("*").eq("id", test_id).single().execute()
        if not original_test.data:
            return jsonify({"success": False, "error": "Test nie istnieje"})

        # Process basic test data changes
        test_data = {}
        for field in ['title', 'test_type', 'description', 'passing_threshold', 'time_limit_minutes']:
            if field in request.form:
                new_value = request.form.get(field)
                if field == 'passing_threshold':
                    new_value = int(new_value or 0)
                elif field == 'time_limit_minutes':
                    new_value = int(new_value) if new_value else None
                
                if original_test.data.get(field) != new_value:
                    test_data[field] = new_value

        # Update test if there are changes
        if test_data:
            test_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            test_result = supabase.from_("tests").update(test_data).eq("id", test_id).execute()
            if not test_result.data:
                raise Exception("Nie udało się zaktualizować testu")

        # Process groups if present in request
        if 'groups[]' in request.form:
            new_groups = request.form.getlist('groups[]')
            current_groups = supabase.from_("link_groups_tests")\
                .select("group_id")\
                .eq("test_id", test_id)\
                .execute()
            
            current_group_ids = {str(g['group_id']) for g in current_groups.data}
            new_group_ids = set(new_groups)
            
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
                group_links = [{"group_id": int(gid), "test_id": test_id} 
                             for gid in groups_to_add]
                supabase.from_("link_groups_tests").insert(group_links).execute()

        # Process questions if present
        questions_data = request.form.get('questions')
        if questions_data:
            questions = json.loads(questions_data)
            
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
                    logger.error(f"Invalid question ID: {question_id}")
                    raise
                    
                if question_id in existing_ids:
                    original = next(q for q in existing_questions.data if q["id"] == question_id) 
                    
                    changed_fields = {}
                    # Process changes...
                    
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
                        "algorithm_params": clean_algorithm_params(
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
                    logger.error(f"Error processing new question: {str(e)}")
                    logger.error(f"Question data: {json.dumps(question, indent=2)}")
                    raise

        # Process updates
        for question in questions_to_update: 
            try:
                result = supabase.from_("questions").update(
                    question["data"]
                ).eq("id", question["id"]).execute()
            except Exception as e:
                logger.error(f"Error updating question {question['id']}: {str(e)}")
                raise

        # Process inserts
        if questions_to_insert: 
            try:
                result = supabase.from_("questions").insert(questions_to_insert).execute() 
            except Exception as e:
                logger.error(f"Error inserting questions: {str(e)}")
                logger.error(f"Insert data: {json.dumps(questions_to_insert, indent=2)}")
                raise

        # Process deletes
        if questions_to_delete: 
            try:
                # Convert set to list properly
                questions_to_delete_list = [id for id in questions_to_delete]
                result = supabase.from_("questions")\
                    .delete()\
                    .in_("id", questions_to_delete_list)\
                    .execute()
            except Exception as e:
                logger.error(f"Error deleting questions: {str(e)}")
                raise

        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Error processing questions for test {test_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)})


def clean_algorithm_params(answer_type, params):
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
        elif answer_type in ('SCALE', 'SALARY'):
            try:
                clean_params['correct_answer'] = float(value)
            except (ValueError, TypeError):
                clean_params['correct_answer'] = None
        elif answer_type == 'DATE':
            clean_params['correct_answer'] = value if value else None
        else:
            clean_params['correct_answer'] = str(value) if value else None
            
    return clean_params


@test_bp.route("/add/questions", methods=["POST"])
def add_questions():
    try:
        questions = json.loads(request.form.get("questions", "[]"))
        test_id = request.form.get("test_id")
        
        if not test_id:
            raise Exception("Missing test_id parameter")

        questions_to_insert = []
        for question in questions:
            clean_question = {
                "test_id": int(test_id),
                "question_text": question["question_text"],
                "answer_type": question["answer_type"],
                "points": int(question.get("points", 0)),
                "order_number": int(question.get("order_number", 1)),
                "is_required": question.get("is_required", True),
                "image": question.get("image"),
                "algorithm_type": question.get("algorithm_type", "NO_ALGORITHM"),
                "algorithm_params": clean_algorithm_params(
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
            logger.info(f"Pomyślnie dodano pytania do testu {test_id}")

        return jsonify({
            "success": True,
            "message": "Pytania zostały dodane"
        })

    except Exception as e:
        logger.error(f"Błąd podczas dodawania pytań: {str(e)}")
        return jsonify({"success": False, "error": str(e)})