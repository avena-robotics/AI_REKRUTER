from flask import Blueprint, render_template, request, jsonify
from database import supabase
from datetime import datetime, timedelta
from routes.auth_routes import login_required

candidate_bp = Blueprint("candidate", __name__, url_prefix="/candidates")


@candidate_bp.route("/")
@login_required
def list():
    campaign_code = request.args.get("campaign_code")
    status = request.args.get("status")
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "desc")

    # Single query to get campaigns for dropdown
    campaigns = (
        supabase.from_("campaigns")
        .select("code, title")
        .order("code", desc=False)
        .execute()
    )

    # Build query for candidates with campaign data
    query = supabase.from_("candidates").select("*, campaigns!inner(*)")

    # Apply filters
    if campaign_code:
        query = query.eq("campaigns.code", campaign_code)
    if status:
        query = query.eq("recruitment_status", status)

    # Apply sorting
    query = query.order(sort_by, desc=(sort_order == "desc"))

    # Execute query
    candidates = query.execute()

    return render_template(
        "candidates/list.html",
        candidates=candidates.data,
        campaigns=campaigns.data,
    )


@candidate_bp.route("/<int:id>")
def view(id):
    try:
        # Single query to get candidate with campaign data
        candidate = (
            supabase.from_("candidates")
            .select("*, campaign:campaigns(*)")
            .eq("id", id)
            .single()
            .execute()
        )

        if not candidate.data:
            return jsonify({"error": "Candidate not found"}), 404

        tests_data = {}
        for stage in ["PO1", "PO2", "PO3"]:
            test_id = candidate.data["campaign"].get(f"{stage.lower()}_test_id")
            if not test_id:
                continue

            # Single query to get test with questions and answers
            test_data = (
                supabase.from_("tests")
                .select(
                    """
                    *,
                    questions:questions(
                        *,
                        answers:candidate_answers!candidate_id=eq.{id}(*)
                    )
                    """.format(
                        id=id
                    )
                )
                .eq("id", test_id)
                .single()
                .execute()
            )

            if not test_data.data:
                continue

            # Process questions and answers
            questions = test_data.data.pop("questions", [])
            processed_questions = []

            for question in questions:
                answers = question.pop("answers", [])
                if answers:
                    question["answer"] = answers[0]
                processed_questions.append(question)

            tests_data[stage] = {
                "test": test_data.data,
                "questions": processed_questions,
                "question_count": len(processed_questions),
                "total_points": sum(q.get("points", 0) for q in processed_questions),
                "score": candidate.data.get(f"{stage.lower()}_score"),
                "completed_at": candidate.data.get(f"{stage.lower()}_completed_at"),
            }

        return render_template(
            "candidates/view.html",
            candidate=candidate.data,
            tests=tests_data,
        )

    except Exception as e:
        print(f"Error viewing candidate: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@candidate_bp.route("/<int:id>/reject", methods=["POST"])
def reject(id):
    try:
        result = (
            supabase.from_("candidates")
            .update({"recruitment_status": "REJECTED"})
            .eq("id", id)
            .execute()
        )
        return jsonify({"success": True})

    except Exception as e:
        print(f"Error rejecting candidate: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@candidate_bp.route("/<int:id>/accept", methods=["POST"])
def accept(id):
    try:
        result = (
            supabase.from_("candidates")
            .update({"recruitment_status": "ACCEPTED"})
            .eq("id", id)
            .execute()
        )
        return jsonify({"success": True})

    except Exception as e:
        print(f"Error accepting candidate: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@candidate_bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    try:
        # First delete all candidate answers
        supabase.from_("candidate_answers").delete().eq("candidate_id", id).execute()
        
        # Then delete the candidate
        supabase.from_("candidates").delete().eq("id", id).execute()
        
        return jsonify({"success": True})

    except Exception as e:
        print(f"Error deleting candidate: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@candidate_bp.route("/<int:id>/extend-token/<stage>", methods=["POST"])
def extend_token(id, stage):
    try:
        if stage not in ["PO2", "PO3"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Nieprawidłowy etap rekrutacji",
                    }
                ),
                400,
            )

        # Get candidate with single query and validate token status
        token_field = f"access_token_{stage.lower()}"
        is_used_field = f"{token_field}_is_used"
        expires_field = f"{token_field}_expires_at"

        candidate = (
            supabase.from_("candidates")
            .select(f"id, {token_field}, {is_used_field}, {expires_field}")
            .eq("id", id)
            .single()
            .execute()
        )

        if not candidate.data:
            return (
                jsonify(
                    {"success": False, "error": "Nie znaleziono kandydata"}
                ),
                404,
            )

        if not candidate.data.get(token_field):
            return (
                jsonify(
                    {"success": False, "error": "Brak tokenu do przedłużenia"}
                ),
                400,
            )

        if candidate.data.get(is_used_field):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Token został już wykorzystany",
                    }
                ),
                400,
            )

        # Calculate new expiration date
        current_expires = candidate.data.get(expires_field)
        if current_expires:
            current_expires = datetime.fromisoformat(
                current_expires.replace("Z", "")
            )
        else:
            current_expires = datetime.now()

        new_expires = current_expires + timedelta(days=7)

        # Update expiration date
        result = (
            supabase.from_("candidates")
            .update({expires_field: new_expires.isoformat()})
            .eq("id", id)
            .execute()
        )

        return jsonify(
            {
                "success": True,
                "message": "Token został przedłużony o tydzień",
            }
        )

    except Exception as e:
        print(f"Error extending token: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Wystąpił błąd podczas przedłużania tokenu",
                }
            ),
            500,
        ) 