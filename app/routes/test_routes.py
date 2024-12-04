import json
from flask import Blueprint, render_template, request, jsonify, session
from database import supabase
from datetime import datetime, timezone
from routes.auth_routes import login_required
from services.group_service import get_user_groups, get_test_groups
import time
from contextlib import contextmanager
import asyncio

test_bp = Blueprint("test", __name__, url_prefix="/tests")

# Add helper function for retrying database operations
def retry_on_disconnect(operation, max_retries=3):
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            if "Server disconnected" in str(e) and attempt < max_retries - 1:
                print(f"Connection lost, retrying... (attempt {attempt + 1})")
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
                print(f"Error fetching user groups: {str(e)}")
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
                print(f"Error fetching tests: {str(e)}")
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
            print(f"Error in test list (attempt {retry_count + 1}): {str(e)}")
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
        passing_threshold = request.form.get("passing_threshold")
        time_limit = request.form.get("time_limit_minutes")
        groups = request.form.getlist("groups[]")
        
        if not groups:
            return jsonify(
                {
                    "success": False,
                    "error": "Należy wybrać co najmniej jedną grupę",
                }
            )

        passing_threshold = (
            int(passing_threshold)
            if passing_threshold and passing_threshold.strip()
            else 0
        )
        time_limit = (
            int(time_limit) if time_limit and time_limit.strip() else None
        )

        test_id = None
        try:
            # Create test
            current_time = datetime.now(timezone.utc)
            test_data = {
                "title": request.form.get("title"),
                "test_type": request.form.get("test_type"),
                "description": request.form.get("description"),
                "passing_threshold": passing_threshold,
                "time_limit_minutes": time_limit,
                "created_at": current_time.isoformat(),
                "updated_at": current_time.isoformat()
            }

            # Insert test and get ID
            def create_test_operation():
                result = supabase.from_("tests").insert(test_data).execute()
                if not result.data:
                    raise Exception("Nie udało się utworzyć testu")
                return result
            
            result = retry_on_disconnect(create_test_operation)
            test_id = result.data[0]["id"]
            
            # Bulk insert group associations
            group_links = [
                {"group_id": int(group_id), "test_id": test_id} for group_id in groups
            ]
            
            if group_links:
                def create_group_links_operation():
                    result = supabase.from_("link_groups_tests").insert(group_links).execute()
                    if not result.data:
                        raise Exception("Nie udało się powiązać testu z wybranymi grupami")
                    return result
                
                retry_on_disconnect(create_group_links_operation)
                
            # Process questions
            questions = json.loads(request.form.get("questions", "[]"))
            
            if questions:
                question_data = []
                for i, question in enumerate(questions, 1):
                    try:
                        clean_question = {
                            "test_id": test_id,
                            "question_text": question["question_text"],
                            "answer_type": question["answer_type"],
                            "points": int(question.get("points", 0)),
                            "order_number": question["order_number"],
                            "is_required": question.get("is_required", True),
                            "image": question.get("image"),
                        }

                        # Handle AH_POINTS type specifically
                        if question["answer_type"] == "AH_POINTS":
                            if "options" in question and isinstance(question["options"], dict):
                                clean_question["options"] = {
                                    k: v for k, v in question["options"].items()
                                    if k in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and v
                                }
                        elif question["answer_type"] == "SALARY":
                            salary_value = question.get("correct_answer_salary")
                            clean_question["correct_answer_salary"] = (
                                float(salary_value) if salary_value is not None else None
                            )
                        else:
                            answer_field = f'correct_answer_{question["answer_type"].lower()}'
                            if (
                                answer_field in question
                                and question[answer_field] is not None
                            ):
                                clean_question[answer_field] = question[answer_field]

                        question_data.append(clean_question)
                    except Exception as e:
                        raise Exception(f"Błąd podczas przetwarzania pytania {i}: {str(e)}")

                # Bulk insert questions in batches
                BATCH_SIZE = 3
                for i in range(0, len(question_data), BATCH_SIZE):
                    batch = question_data[i:i + BATCH_SIZE]
                    
                    def insert_questions_operation():
                        result = supabase.from_("questions").insert(batch).execute()
                        if not result.data:
                            raise Exception("Nie udało się zapisać pytań do testu")
                        return result
                    
                    retry_on_disconnect(insert_questions_operation)
                    
                    if i + BATCH_SIZE < len(question_data):
                        time.sleep(0.5)  # Small delay between batches
                
            return jsonify(
                {"success": True, "message": "Test został dodany pomyślnie"}
            )

        except Exception as e:
            print(f"Error during test creation, starting rollback. Error: {str(e)}")
            # Clean up on any error
            if test_id:
                try:
                    print("Rolling back - deleting questions")
                    supabase.from_("questions").delete().eq("test_id", test_id).execute()
                    
                    print("Rolling back - deleting group associations")
                    supabase.from_("link_groups_tests").delete().eq("test_id", test_id).execute()
                    
                    print("Rolling back - deleting test")
                    supabase.from_("tests").delete().eq("id", test_id).execute()
                    
                    print("Rollback completed successfully")
                except Exception as rollback_error:
                    print(f"Error during rollback: {str(rollback_error)}")
                
            raise Exception(f"Błąd podczas tworzenia testu: {str(e)}")

    except Exception as e:
        print(f"Error adding test: {str(e)}")
        return jsonify({"success": False, "error": str(e)})


@test_bp.route("/<int:test_id>/data")
def get_test_data(test_id):
    try:
        # Single query to get test with questions and groups
        test = (
            supabase.from_("tests")
            .select("*, questions(*), link_groups_tests(group_id)")
            .eq("id", test_id)
            .single()
            .execute()
        )

        if not test.data:
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
        print(f"Debug - Error in get_test_data: {str(e)}")
        return jsonify({"error": str(e)}), 500


@test_bp.route("/<int:test_id>/edit", methods=["POST"])
def edit(test_id):
    try:
        # Get original test data for comparison
        original_test = supabase.from_("tests").select("*").eq("id", test_id).single().execute()
        if not original_test.data:
            return jsonify({"success": False, "error": "Test nie istnieje"})

        # Prepare test data
        test_data = {
            "title": request.form.get("title"),
            "test_type": request.form.get("test_type"),
            "description": request.form.get("description"),
            "passing_threshold": int(request.form.get("passing_threshold", 0)),
            "time_limit_minutes": int(request.form.get("time_limit_minutes", 0))
            if request.form.get("time_limit_minutes")
            else None,
        }

        # Check if test data actually changed
        test_changed = any(
            original_test.data.get(key) != value 
            for key, value in test_data.items()
        )

        groups = request.form.getlist("groups[]")
        if not groups:
            return jsonify(
                {
                    "success": False,
                    "error": "Należy wybrać co najmniej jedną grupę",
                }
            )

        try:
            # Only update test if data changed
            if test_changed:
                test_result = supabase.from_("tests").update(test_data).eq("id", test_id).execute()
                if not test_result.data:
                    raise Exception("Nie udało się zaktualizować testu")

            # Get original groups for comparison
            original_groups = supabase.from_("link_groups_tests").select("*").eq("test_id", test_id).execute()
            original_group_ids = {g["group_id"] for g in original_groups.data}
            new_group_ids = {int(gid) for gid in groups}

            # Only process groups if they changed
            if original_group_ids != new_group_ids:
                groups_to_add = new_group_ids - original_group_ids
                groups_to_remove = original_group_ids - new_group_ids

                # Remove old group associations
                if groups_to_remove:
                    supabase.from_("link_groups_tests").delete().eq("test_id", test_id).in_("group_id", list(groups_to_remove)).execute()

                # Add new group associations
                if groups_to_add:
                    group_links = [{"group_id": gid, "test_id": test_id} for gid in groups_to_add]
                    supabase.from_("link_groups_tests").insert(group_links).execute()

            # Process questions
            questions = json.loads(request.form.get("questions", "[]"))
            
            # Get original questions for comparison
            original_questions = supabase.from_("questions").select("*").eq("test_id", test_id).execute()
            original_questions_dict = {q["id"]: q for q in original_questions.data}

            questions_to_update = []
            questions_to_insert = []
            questions_to_delete = set(original_questions_dict.keys())

            for question in questions:
                clean_question = {
                    "test_id": test_id,
                    "question_text": question["question_text"],
                    "answer_type": question["answer_type"],
                    "points": int(question.get("points", 0)),
                    "order_number": question.get("order_number", 1),
                    "is_required": question.get("is_required", True),
                    "image": question.get("image"),
                }

                # Handle answer type specific data
                if question["answer_type"] == "AH_POINTS":
                    if "options" in question and isinstance(question["options"], dict):
                        clean_question["options"] = {
                            k: v for k, v in question["options"].items()
                            if k in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and v
                        }
                elif question["answer_type"] == "SALARY":
                    salary_value = question.get("correct_answer_salary")
                    clean_question["correct_answer_salary"] = (
                        float(salary_value) if salary_value is not None else None
                    )
                else:
                    answer_field = f'correct_answer_{question["answer_type"].lower()}'
                    if answer_field in question and question[answer_field] is not None:
                        # Add debug logging
                        print(f"Processing {answer_field}")
                        print(f"Raw value: {question[answer_field]}")
                        print(f"Type: {type(question[answer_field])}")
                        
                        # Add special handling for boolean answers
                        if answer_field == 'correct_answer_boolean':
                            # Convert string 'true'/'false' to Python boolean
                            bool_value = str(question[answer_field]).lower() == 'true'
                            print(f"Converted boolean value: {bool_value}")
                            clean_question[answer_field] = bool_value
                        else:
                            clean_question[answer_field] = question[answer_field]

                question_id = question.get("id")
                if question_id and str(question_id).isdigit():
                    question_id = int(question_id)
                    if question_id in original_questions_dict:
                        # Compare with original question to see if it changed
                        original = original_questions_dict[question_id]
                        if any(original.get(k) != v for k, v in clean_question.items()):
                            questions_to_update.append({
                                "id": question_id,
                                "data": clean_question
                            })
                        questions_to_delete.remove(question_id)
                else:
                    questions_to_insert.append(clean_question)

            # Process questions in optimized batches
            BATCH_SIZE = 10

            # Update modified questions in batches
            if questions_to_update:
                for i in range(0, len(questions_to_update), BATCH_SIZE):
                    batch = questions_to_update[i:i + BATCH_SIZE]
                    
                    # Execute updates in parallel using asyncio
                    for question in batch:
                        supabase.from_("questions").update(
                            question["data"]
                        ).eq("id", question["id"]).execute()

            # Insert new questions in batches
            if questions_to_insert:
                for i in range(0, len(questions_to_insert), BATCH_SIZE):
                    batch = questions_to_insert[i:i + BATCH_SIZE]
                    supabase.from_("questions").insert(batch).execute()

            # Delete removed questions
            if questions_to_delete:
                try:
                    delete_ids = [int(id) for id in questions_to_delete]
                    supabase.from_("questions").delete().in_("id", delete_ids).execute()
                except Exception as e:
                    error_data = getattr(e, 'args', [{}])[0]
                    if isinstance(error_data, dict) and error_data.get('code') == '23503' and 'candidate_answers' in str(error_data):
                        raise Exception("Nie można usunąć pytania, ponieważ jest ono wykorzystywane w odpowiedziach kandydatów")
                    raise e

            return jsonify({
                "success": True,
                "message": "Test został zaktualizowany pomyślnie",
            })

        except Exception as e:
            print(f"Error during test update: {str(e)}")
            raise Exception(f"Błąd podczas aktualizacji testu: {str(e)}")

    except Exception as e:
        print(f"Error editing test: {str(e)}")
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
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})