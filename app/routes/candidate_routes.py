import secrets
from flask import Blueprint, render_template, request, jsonify, current_app
from database import supabase
from datetime import datetime, timedelta, timezone
from routes.auth_routes import login_required
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
        # 1. Get candidate with campaign data
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
        for stage in ["PO1", "PO2", "PO3", "PO4"]:
            test_id = candidate.data["campaign"].get(f"{stage.lower()}_test_id")
            if not test_id:
                continue

            # 2. Get test data
            test = (
                supabase.from_("tests")
                .select("*")
                .eq("id", test_id)
                .single()
                .execute()
            )
            
            if not test.data:
                continue

            # 3. Get questions for this test
            questions = (
                supabase.from_("questions")
                .select("*")
                .eq("test_id", test_id)
                .order("order_number")
                .execute()
            )

            # 4. Get answers for this candidate and test
            answers = (
                supabase.from_("candidate_answers")
                .select("*")
                .eq("candidate_id", id)
                .in_("question_id", [q["id"] for q in questions.data])
                .execute()
            )

            # Process questions and match with answers
            processed_questions = []
            answers_dict = {a["question_id"]: a for a in answers.data}

            for question in questions.data:
                question_id = question["id"]
                if question_id in answers_dict:
                    question["answer"] = answers_dict[question_id]
                else:
                    question["answer"] = None
                processed_questions.append(question)

            tests_data[stage] = {
                "test": test.data,
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


@candidate_bp.route("/<int:id>/next-stage", methods=["POST"])
def next_stage(id):
    try:
        # Get current candidate data
        candidate = (
            supabase.from_("candidates")
            .select("*, campaigns(*)")
            .eq("id", id)
            .single()
            .execute()
        )
        
        if not candidate.data:
            return jsonify({"success": False, "error": "Nie znaleziono kandydata"}), 404

        current_status = candidate.data["recruitment_status"]
        campaign = candidate.data["campaigns"]
        
        # Define next stage based on current status
        if current_status == "PO1":
            next_status = "PO2"
            test_id = campaign.get("po2_test_id")
        elif current_status == "PO2":
            next_status = "PO3"
            test_id = campaign.get("po3_test_id")
        elif current_status == "PO3":
            next_status = "PO4"
            test_id = None
        else:
            return jsonify({"success": False, "error": "Nieprawidłowy obecny etap"}), 400

        # Generate token and send email for PO2 and PO3
        updates = {"recruitment_status": next_status}
        
        if next_status in ["PO2", "PO3"] and test_id:
            # Generate token and expiry date
            token = secrets.token_urlsafe(32) 
            token_expiry = datetime.now(timezone.utc) + timedelta(days=7)
            formatted_expiry = token_expiry.strftime("%Y-%m-%d %H:%M")
            
            # Add token fields to updates
            updates.update({
                f"access_token_{next_status.lower()}": token,
                f"access_token_{next_status.lower()}_expires_at": token_expiry.isoformat(),
                f"access_token_{next_status.lower()}_is_used": False,
            })
            
            # Prepare and send email
            test_url = f"{request.host_url.rstrip('/')}/test/candidate/{token}"
            email_body = (
                f"Gratulacje! Pomyślnie ukończyłeś/aś etap {current_status} "
                f"i otrzymujesz dostęp do kolejnego etapu rekrutacji.\n"
                f"Link do testu: {test_url}\n"
                f"Link jest ważny do: {formatted_expiry}"
            )
            
            # Send email using SMTP
            try:
                msg = MIMEMultipart()
                msg["From"] = current_app.config["SENDER_EMAIL"]
                msg["To"] = candidate.data["email"]
                msg["Subject"] = f"Dostęp do etapu {next_status}"
                msg.attach(MIMEText(email_body, "plain"))
                
                with smtplib.SMTP(
                    current_app.config["SMTP_SERVER"],
                    current_app.config["SMTP_PORT"]
                ) as server:
                    server.starttls()
                    server.login(
                        current_app.config["SMTP_USERNAME"],
                        current_app.config["SMTP_PASSWORD"]
                    )
                    server.send_message(msg)
            except Exception as e:
                print(f"Error sending email: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": "Nie udało się wysłać emaila"
                }), 500

        # Update candidate in database
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = (
            supabase.from_("candidates")
            .update(updates)
            .eq("id", id)
            .execute()
        )

        return jsonify({"success": True})

    except Exception as e:
        print(f"Error moving candidate to next stage: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500 