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

        # Create test
        test_data = {
            "test_type": request.form.get("test_type"),
            "stage": request.form.get("stage"),
            "description": request.form.get("description"),
            "passing_threshold": passing_threshold,
            "time_limit_minutes": time_limit,
        }

        # Insert test and get ID
        result = supabase.from_("tests").insert(test_data).execute()
        test_id = result.data[0]["id"]

        # Bulk insert group associations
        group_links = [
            {"group_id": int(group_id), "test_id": test_id} for group_id in groups
        ]
        if group_links:
            supabase.from_("link_groups_tests").insert(group_links).execute()

        # Process questions
        questions = json.loads(request.form.get("questions", "[]"))
        if questions:
            question_data = []
            for question in questions:
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
                    numeric_value = question.get("correct_answer_numeric")
                    clean_question["correct_answer_numeric"] = (
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

            # Bulk insert questions
            if question_data:
                supabase.from_("questions").insert(question_data).execute()

        return jsonify(
            {"success": True, "message": "Test został dodany pomyślnie"}
        )

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
        test_data = {
            "test_type": request.form.get("test_type"),
            "stage": request.form.get("stage"),
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

        # Update test
        supabase.from_("tests").update(test_data).eq("id", test_id).execute()

        # Bulk update group associations
        supabase.from_("link_groups_tests").delete().eq(
            "test_id", test_id
        ).execute()

        group_links = [
            {"group_id": int(group_id), "test_id": test_id} for group_id in groups
        ]
        if group_links:
            supabase.from_("link_groups_tests").insert(group_links).execute()

        # Process questions
        questions = json.loads(request.form.get("questions", "[]"))
        existing_questions = [q["id"] for q in questions if q.get("id")]

        # Bulk delete removed questions
        if existing_questions:
            supabase.from_("questions").delete().eq("test_id", test_id).not_.in_(
                "id", existing_questions
            ).execute()
        else:
            supabase.from_("questions").delete().eq(
                "test_id", test_id
            ).execute()

        # Prepare questions for bulk operations
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
                numeric_value = question.get("correct_answer_numeric")
                clean_question["correct_answer_numeric"] = (
                    float(numeric_value) if numeric_value is not None else None
                )
            else:
                answer_field = f'correct_answer_{question["answer_type"].lower()}'
                if (
                    answer_field in question
                    and question[answer_field] is not None
                ):
                    clean_question[answer_field] = question[answer_field]

            if question.get("id"):
                questions_to_update.append(
                    {"id": question["id"], **clean_question}
                )
            else:
                questions_to_insert.append(clean_question)

        # Bulk update existing questions
        if questions_to_update:
            for q in questions_to_update:
                q_id = q.pop("id")
                supabase.from_("questions").update(q).eq("id", q_id).execute()

        # Bulk insert new questions
        if questions_to_insert:
            supabase.from_("questions").insert(questions_to_insert).execute()

        return jsonify(
            {
                "success": True,
                "message": "Test został zaktualizowany pomyślnie",
            }
        )

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