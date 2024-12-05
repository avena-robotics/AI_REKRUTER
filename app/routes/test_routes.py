import json
from flask import Blueprint, render_template, request, jsonify, session
from database import supabase
from datetime import datetime, timezone
from routes.auth_routes import login_required
from services.group_service import get_user_groups, get_test_groups
import time

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
        # Validate basic test data
        if not request.form.get("title"):
            return jsonify({"success": False, "error": "Tytuł testu jest wymagany"})

        groups = request.form.getlist("groups[]")
        if not groups:
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
            raise Exception("Nie udało się utworzyć testu")

        test_id = test_result.data[0]["id"]

        # Add group associations
        group_links = [{"group_id": int(gid), "test_id": test_id} for gid in groups]
        supabase.from_("link_groups_tests").insert(group_links).execute()

        return jsonify({
            "success": True, 
            "message": "Test został utworzony",
            "test_id": test_id
        })

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
            print(f"Processing {len(questions)} questions")
            
            original_questions = {q["id"]: q for q in supabase.from_("questions")
                                .select("*")
                                .eq("test_id", test_id)
                                .execute().data}
            print(f"Found {len(original_questions)} existing questions")

            questions_to_update = []
            questions_to_insert = []
            questions_to_delete = set(original_questions.keys())

            for question in questions:
                question_id = question.get("id")
                
                if question_id and str(question_id).isdigit():
                    question_id = int(question_id)
                    if question_id in original_questions:
                        # Compare with original question
                        original = original_questions[question_id]
                        changed_fields = {}
                        
                        # Prepare base question data with only fields that exist in original
                        clean_question = {
                            "question_text": question["question_text"],
                            "answer_type": question["answer_type"],
                            "points": int(question.get("points", 0)),
                            "order_number": question.get("order_number", 1),
                            "is_required": question.get("is_required", True)
                        }

                        # Compare and collect only changed fields
                        for key, value in clean_question.items():
                            if original.get(key) != value:
                                changed_fields[key] = value
                                print(f"Question {question_id} field '{key}' changed from '{original.get(key)}' to '{value}'")

                        # Handle image separately to avoid unnecessary updates
                        if "image" in question and question["image"]:
                            # Only update image if it's new or changed
                            if question_id not in original_questions or \
                               original_questions[question_id].get("image") != question["image"]:
                                changed_fields["image"] = question["image"]
                                print(f"Question {question_id} image changed")

                        # Handle answer type specific data only if changed
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
                            print(f"Question {question_id} will be updated with: {changed_fields}")
                        questions_to_delete.remove(question_id)
                else:
                    # This is a new question
                    questions_to_insert.append(question)
                    print(f"New question will be inserted")

            print(f"Questions to update: {len(questions_to_update)}")
            print(f"Questions to insert: {len(questions_to_insert)}")
            print(f"Questions to delete: {len(questions_to_delete)}")

            # Process questions in smaller batches
            BATCH_SIZE = 3

            # Update modified questions one at a time to minimize payload size
            for question in questions_to_update:
                print(f"Updating question {question['id']} with data: {question['data']}")
                supabase.from_("questions").update(
                    question["data"]
                ).eq("id", question["id"]).execute()

            # Insert new questions in small batches
            for i in range(0, len(questions_to_insert), BATCH_SIZE):
                batch = questions_to_insert[i:i + BATCH_SIZE]
                print(f"Inserting batch of {len(batch)} questions")
                supabase.from_("questions").insert(batch).execute()
                # Add small delay between batches
                if i + BATCH_SIZE < len(questions_to_insert):
                    time.sleep(0.5)

            # Delete removed questions only if explicitly requested
            if questions_to_delete and len(questions) > 0:  # Only delete if questions were actually sent
                print(f"Deleting questions: {questions_to_delete}")
                supabase.from_("questions").delete().in_("id", list(questions_to_delete)).execute()

        return jsonify({
            "success": True,
            "message": "Test został zaktualizowany pomyślnie"
        })

    except Exception as e:
        print(f"Error editing test: {str(e)}")
        print(f"Request form data size: {len(str(request.form))} bytes")
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


@test_bp.route("/<int:test_id>/edit/questions", methods=["POST"])
def edit_questions(test_id):
    try:
        questions = json.loads(request.form.get("questions", "[]"))
        print(f"Processing batch of {len(questions)} questions")
        
        original_questions = {q["id"]: q for q in supabase.from_("questions")
                            .select("*")
                            .eq("test_id", test_id)
                            .execute().data}

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
                            print(f"Question {question_id} field '{key}' changed")
                    
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
            print(f"Updating question {question['id']}")
            supabase.from_("questions").update(
                question["data"]
            ).eq("id", question["id"]).execute()

        if questions_to_insert:
            print(f"Inserting {len(questions_to_insert)} new questions")
            supabase.from_("questions").insert(questions_to_insert).execute()

        return jsonify({
            "success": True,
            "message": "Pytania zostały zaktualizowane"
        })

    except Exception as e:
        print(f"Error processing questions: {str(e)}")
        return jsonify({"success": False, "error": str(e)})


@test_bp.route("/add/questions", methods=["POST"])
def add_questions():
    try:
        questions = json.loads(request.form.get("questions", "[]"))
        print(f"Processing batch of {len(questions)} questions for new test")
        
        # Get test_id from the request
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
                "order_number": question.get("order_number", 1),
                "is_required": question.get("is_required", True),
                "image": question.get("image")
            }

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
            print(f"Inserting {len(questions_to_insert)} questions")
            supabase.from_("questions").insert(questions_to_insert).execute()

        return jsonify({
            "success": True,
            "message": "Pytania zostały dodane"
        })

    except Exception as e:
        print(f"Error processing questions: {str(e)}")
        return jsonify({"success": False, "error": str(e)})