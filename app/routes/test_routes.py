import json
from flask import Blueprint, render_template, request, jsonify, session
from database import supabase
from datetime import datetime
from routes.auth_routes import login_required
from services.group_service import get_user_groups, get_test_groups
import time
from contextlib import contextmanager

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
            print(f"Fetching data for user_id: {user_id}")
            
            # Get user groups
            try:
                user_groups = get_user_groups(user_id)
                print(f"Successfully fetched {len(user_groups)} user groups")
            except Exception as e:
                print(f"Error fetching user groups: {str(e)}")
                if retry_count == max_retries - 1:
                    raise
                retry_count += 1
                time.sleep(1)  # Wait 1 second before retrying
                continue

            user_group_ids = [group["id"] for group in user_groups]
            print(f"User group IDs: {user_group_ids}")

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
                print(f"Successfully fetched {len(tests_response.data)} tests")
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

            print(f"Filtered to {len(filtered_tests)} tests for user")
            return render_template(
                "tests/list.html", tests=filtered_tests, groups=user_groups
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
        print("Starting test creation process")
        
        passing_threshold = request.form.get("passing_threshold")
        time_limit = request.form.get("time_limit_minutes")
        groups = request.form.getlist("groups[]")
        
        print(f"Received groups: {groups}")

        if not groups:
            print("No groups selected - returning error")
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
            test_data = {
                "title": request.form.get("title"),
                "test_type": request.form.get("test_type"),
                "description": request.form.get("description"),
                "passing_threshold": passing_threshold,
                "time_limit_minutes": time_limit,
            }
            print(f"Creating test with data: {test_data}")

            # Insert test and get ID
            def create_test_operation():
                result = supabase.from_("tests").insert(test_data).execute()
                if not result.data:
                    raise Exception("Nie udało się utworzyć testu")
                return result
            
            result = retry_on_disconnect(create_test_operation)
            test_id = result.data[0]["id"]
            print(f"Test created successfully with ID: {test_id}")

            # Bulk insert group associations
            group_links = [
                {"group_id": int(group_id), "test_id": test_id} for group_id in groups
            ]
            print(f"Creating group associations: {group_links}")
            
            if group_links:
                def create_group_links_operation():
                    result = supabase.from_("link_groups_tests").insert(group_links).execute()
                    if not result.data:
                        raise Exception("Nie udało się powiązać testu z wybranymi grupami")
                    return result
                
                retry_on_disconnect(create_group_links_operation)
                print("Group associations created successfully")

            # Process questions
            questions = json.loads(request.form.get("questions", "[]"))
            print(f"Processing {len(questions)} questions")
            
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
                            print(f"Processing AH_POINTS options for question {i}: {clean_question.get('options')}")
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

                        print(f"Processed question {i}: {clean_question}")
                        question_data.append(clean_question)
                    except Exception as e:
                        raise Exception(f"Błąd podczas przetwarzania pytania {i}: {str(e)}")

                # Bulk insert questions in batches
                BATCH_SIZE = 3
                for i in range(0, len(question_data), BATCH_SIZE):
                    batch = question_data[i:i + BATCH_SIZE]
                    print(f"Processing question batch {i//BATCH_SIZE + 1} of {(len(question_data) + BATCH_SIZE - 1)//BATCH_SIZE}")
                    
                    def insert_questions_operation():
                        result = supabase.from_("questions").insert(batch).execute()
                        if not result.data:
                            raise Exception("Nie udało się zapisać pytań do testu")
                        return result
                    
                    retry_on_disconnect(insert_questions_operation)
                    
                    if i + BATCH_SIZE < len(question_data):
                        time.sleep(0.5)  # Small delay between batches
                
                print("All questions created successfully")

            print("Test creation completed successfully")
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
        print(f"Starting edit process for test ID: {test_id}")
        
        # Get original test data for potential rollback
        original_test = supabase.from_("tests").select("*").eq("id", test_id).single().execute()
        if not original_test.data:
            print(f"Test not found with ID: {test_id}")
            return jsonify({"success": False, "error": "Test nie istnieje"})
        print(f"Original test data: {original_test.data}")

        # Get original groups
        original_groups = supabase.from_("link_groups_tests").select("*").eq("test_id", test_id).execute()
        original_group_ids = [g["group_id"] for g in original_groups.data]
        print(f"Original group IDs: {original_group_ids}")

        # Get original questions
        original_questions = supabase.from_("questions").select("*").eq("test_id", test_id).execute()
        original_question_ids = [q["id"] for q in original_questions.data]
        print(f"Original question IDs: {original_question_ids}")

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
        print(f"New test data to be updated: {test_data}")

        groups = request.form.getlist("groups[]")
        print(f"New groups to be assigned: {groups}")
        
        if not groups:
            print("No groups selected - returning error")
            return jsonify(
                {
                    "success": False,
                    "error": "Należy wybrać co najmniej jedną grupę",
                }
            )

        try:
            # Update test
            print(f"Updating test with ID {test_id}")
            test_result = supabase.from_("tests").update(test_data).eq("id", test_id).execute()
            if not test_result.data:
                raise Exception("Nie udało się zaktualizować testu")
            print("Test updated successfully")

            # Handle group associations
            new_group_ids = [int(gid) for gid in groups if int(gid) not in original_group_ids]
            groups_to_remove = [gid for gid in original_group_ids if str(gid) not in groups]
            
            print(f"Groups to add: {new_group_ids}")
            print(f"Groups to remove: {groups_to_remove}")

            # Remove old group associations
            if groups_to_remove:
                print(f"Removing old group associations: {groups_to_remove}")
                remove_result = supabase.from_("link_groups_tests").delete().eq("test_id", test_id).in_("group_id", groups_to_remove).execute()
                print(f"Remove groups result: {remove_result.data}")

            # Add new group associations
            if new_group_ids:
                print(f"Adding new group associations: {new_group_ids}")
                group_links = [{"group_id": gid, "test_id": test_id} for gid in new_group_ids]
                group_result = supabase.from_("link_groups_tests").insert(group_links).execute()
                if not group_result.data:
                    raise Exception("Nie udało się dodać nowych powiązań z grupami")
                print("New group associations added successfully")

            # Process questions
            questions = json.loads(request.form.get("questions", "[]"))
            print(f"Processing {len(questions)} questions")
            
            questions_to_update = []
            questions_to_insert = []

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

                # Handle AH_POINTS type specifically
                if question["answer_type"] == "AH_POINTS":
                    if "options" in question and isinstance(question["options"], dict):
                        clean_question["options"] = {
                            k: v for k, v in question["options"].items()
                            if k in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and v
                        }
                    print(f"Processing AH_POINTS options: {clean_question.get('options')}")
                elif question["answer_type"] == "SALARY":
                    salary_value = question.get("correct_answer_salary")
                    clean_question["correct_answer_salary"] = (
                        float(salary_value) if salary_value is not None else None
                    )
                else:
                    answer_field = f'correct_answer_{question["answer_type"].lower()}'
                    if answer_field in question and question[answer_field] is not None:
                        clean_question[answer_field] = question[answer_field]

                # Store question ID separately instead of including it in clean_question
                if question.get("id") and str(question["id"]).isdigit() and int(question["id"]) in original_question_ids:
                    questions_to_update.append({
                        "id": int(question["id"]),
                        "data": clean_question
                    })
                else:
                    questions_to_insert.append(clean_question)

            print(f"Questions to update: {len(questions_to_update)}")
            print(f"Questions to insert: {len(questions_to_insert)}")

            # Process questions in batches
            BATCH_SIZE = 3
            
            # Update existing questions
            if questions_to_update:
                for i in range(0, len(questions_to_update), BATCH_SIZE):
                    batch = questions_to_update[i:i + BATCH_SIZE]
                    print(f"Processing update batch {i//BATCH_SIZE + 1} of {(len(questions_to_update) + BATCH_SIZE - 1)//BATCH_SIZE}")
                    
                    for question in batch:
                        question_id = question["id"]
                        question_data = question["data"]
                        print(f"Updating question {question_id} with data: {question_data}")
                        
                        def update_operation():
                            result = supabase.from_("questions").update(question_data).eq("id", question_id).execute()
                            if not result.data:
                                raise Exception(f"Nie udało się zaktualizować pytania {question_id}")
                            return result
                        
                        try:
                            retry_on_disconnect(update_operation)
                        except Exception as e:
                            print(f"Failed to update question {question_id}: {str(e)}")
                            raise
                        
                    # Small delay between batches to prevent overload
                    if i + BATCH_SIZE < len(questions_to_update):
                        time.sleep(0.5)
                
                print("Existing questions updated successfully")

            # Insert new questions in batches
            if questions_to_insert:
                for i in range(0, len(questions_to_insert), BATCH_SIZE):
                    batch = questions_to_insert[i:i + BATCH_SIZE]
                    print(f"Processing insert batch {i//BATCH_SIZE + 1}")
                    
                    def insert_operation():
                        result = supabase.from_("questions").insert(batch).execute()
                        if not result.data:
                            raise Exception("Nie udało się dodać nowych pytań")
                        return result
                    
                    retry_on_disconnect(insert_operation)
                    
                    if i + BATCH_SIZE < len(questions_to_insert):
                        time.sleep(0.5)
                
                print("New questions inserted successfully")

            # Remove questions that are no longer present
            current_question_ids = [q["id"] for q in questions_to_update]
            questions_to_delete = [qid for qid in original_question_ids if qid not in current_question_ids]
            
            if questions_to_delete:
                print(f"Deleting removed questions: {questions_to_delete}")
                
                def delete_operation():
                    result = supabase.from_("questions").delete().eq("test_id", test_id).in_("id", questions_to_delete).execute()
                    print(f"Delete questions result: {result.data}")
                    return result
                
                retry_on_disconnect(delete_operation)

            print("Test edit completed successfully")
            return jsonify(
                {
                    "success": True,
                    "message": "Test został zaktualizowany pomyślnie",
                }
            )

        except Exception as e:
            print(f"Error during test update, starting rollback. Error: {str(e)}")
            # Revert changes in case of error
            try:
                print("Rolling back test changes")
                supabase.from_("tests").update(original_test.data).eq("id", test_id).execute()
                
                print("Rolling back group changes")
                # Remove any new group associations
                if new_group_ids:
                    supabase.from_("link_groups_tests").delete().eq("test_id", test_id).in_("group_id", new_group_ids).execute()
                
                print("Rolling back question changes")
                # Remove any newly inserted questions
                if questions_to_insert:
                    supabase.from_("questions").delete().eq("test_id", test_id).not_.in_("id", original_question_ids).execute()
                
                # Revert updated questions to their original state
                for orig_q in original_questions.data:
                    supabase.from_("questions").update(orig_q).eq("id", orig_q["id"]).execute()
                
                print("Rollback completed successfully")
            except Exception as rollback_error:
                print(f"Error during rollback: {str(rollback_error)}")
                
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