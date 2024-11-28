import json
from flask import Blueprint, render_template, request, jsonify, session
from database import supabase
from datetime import datetime
from routes.auth_routes import login_required
from services.group_service import get_user_groups, get_test_groups

test_bp = Blueprint("test", __name__, url_prefix="/tests")


@test_bp.route("/")
@login_required
def list():
    try:
        user_id = session.get("user_id")
        user_groups = get_user_groups(user_id)
        user_group_ids = [group["id"] for group in user_groups]

        # Single query with JOINs to get tests and their questions
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

        return render_template(
            "tests/list.html", tests=filtered_tests, groups=user_groups
        )

    except Exception as e:
        print(f"Error in test list: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Wystąpił błąd podczas pobierania testów: {str(e)}",
                }
            ),
            500,
        )


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
            test_data = {
                "title": request.form.get("title"),
                "test_type": request.form.get("test_type"),
                "description": request.form.get("description"),
                "passing_threshold": passing_threshold,
                "time_limit_minutes": time_limit,
            }

            # Insert test and get ID
            result = supabase.from_("tests").insert(test_data).execute()
            if not result.data:
                raise Exception("Nie udało się utworzyć testu")
                
            test_id = result.data[0]["id"]

            # Bulk insert group associations
            group_links = [
                {"group_id": int(group_id), "test_id": test_id} for group_id in groups
            ]
            if group_links:
                group_result = supabase.from_("link_groups_tests").insert(group_links).execute()
                if not group_result.data:
                    raise Exception("Nie udało się powiązać testu z wybranymi grupami")

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

                        if question["answer_type"] == "SALARY":
                            numeric_value = question.get("correct_answer_salary")
                            clean_question["correct_answer_salary"] = (
                                float(numeric_value) if numeric_value is not None else None
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

                # Bulk insert questions
                if question_data:
                    question_result = supabase.from_("questions").insert(question_data).execute()
                    if not question_result.data:
                        raise Exception("Nie udało się zapisać pytań do testu")

            return jsonify(
                {"success": True, "message": "Test został dodany pomyślnie"}
            )

        except Exception as e:
            # Clean up on any error
            if test_id:
                # Delete in reverse order to maintain referential integrity
                supabase.from_("questions").delete().eq("test_id", test_id).execute()
                supabase.from_("link_groups_tests").delete().eq("test_id", test_id).execute()
                supabase.from_("tests").delete().eq("id", test_id).execute()
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
        # Get original test data for potential rollback
        original_test = supabase.from_("tests").select("*").eq("id", test_id).single().execute()
        if not original_test.data:
            return jsonify({"success": False, "error": "Test nie istnieje"})

        # Get original groups
        original_groups = supabase.from_("link_groups_tests").select("*").eq("test_id", test_id).execute()
        original_group_ids = [g["group_id"] for g in original_groups.data]

        # Get original questions
        original_questions = supabase.from_("questions").select("*").eq("test_id", test_id).execute()
        original_question_ids = [q["id"] for q in original_questions.data]

        test_data = {
            "title": request.form.get("title"),
            "test_type": request.form.get("test_type"),
            "description": request.form.get("description"),
            "passing_threshold": int(request.form.get("passing_threshold", 0)),
            "time_limit_minutes": int(request.form.get("time_limit_minutes", 0))
            if request.form.get("time_limit_minutes")
            else None,
        }

        groups = request.form.getlist("groups[]")
        if not groups:
            return jsonify(
                {
                    "success": False,
                    "error": "Należy wybrać co najmniej jedną grupę",
                }
            )

        try:
            # Update test
            test_result = supabase.from_("tests").update(test_data).eq("id", test_id).execute()
            if not test_result.data:
                raise Exception("Nie udało się zaktualizować testu")

            # Handle group associations - only add new ones
            new_group_ids = [int(gid) for gid in groups if int(gid) not in original_group_ids]
            if new_group_ids:
                group_links = [{"group_id": gid, "test_id": test_id} for gid in new_group_ids]
                group_result = supabase.from_("link_groups_tests").insert(group_links).execute()
                if not group_result.data:
                    raise Exception("Nie udało się dodać nowych powiązań z grupami")

            # Process questions
            questions = json.loads(request.form.get("questions", "[]"))
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

                if question["answer_type"] == "SALARY":
                    numeric_value = question.get("correct_answer_salary")
                    clean_question["correct_answer_salary"] = (
                        float(numeric_value) if numeric_value is not None else None
                    )
                else:
                    answer_field = f'correct_answer_{question["answer_type"].lower()}'
                    if (
                        answer_field in question
                        and question[answer_field] is not None
                    ):
                        clean_question[answer_field] = question[answer_field]

                if question.get("id") and int(question["id"]) in original_question_ids:
                    questions_to_update.append(
                        {"id": question["id"], **clean_question}
                    )
                else:
                    questions_to_insert.append(clean_question)

            # Update existing questions
            if questions_to_update:
                for q in questions_to_update:
                    q_id = q.pop("id")
                    update_result = supabase.from_("questions").update(q).eq("id", q_id).execute()
                    if not update_result.data:
                        raise Exception(f"Nie udało się zaktualizować pytania {q_id}")

            # Insert new questions
            if questions_to_insert:
                insert_result = supabase.from_("questions").insert(questions_to_insert).execute()
                if not insert_result.data:
                    raise Exception("Nie udało się dodać nowych pytań")

            return jsonify(
                {
                    "success": True,
                    "message": "Test został zaktualizowany pomyślnie",
                }
            )

        except Exception as e:
            # Revert changes in case of error
            supabase.from_("tests").update(original_test.data).eq("id", test_id).execute()
            
            # Remove any new group associations
            if new_group_ids:
                supabase.from_("link_groups_tests").delete().eq("test_id", test_id).in_("group_id", new_group_ids).execute()
            
            # Remove any newly inserted questions
            if questions_to_insert:
                supabase.from_("questions").delete().eq("test_id", test_id).not_.in_("id", original_question_ids).execute()
            
            # Revert updated questions to their original state
            for orig_q in original_questions.data:
                supabase.from_("questions").update(orig_q).eq("id", orig_q["id"]).execute()
                
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