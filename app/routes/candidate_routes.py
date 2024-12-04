import secrets
from flask import Blueprint, render_template, request, jsonify, current_app
from database import supabase
from datetime import datetime, timedelta, timezone
from routes.auth_routes import login_required
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

candidate_bp = Blueprint("candidate", __name__, url_prefix="/candidates")


@candidate_bp.route("/")
@login_required
def list():
    campaign_code = request.args.get("campaign_code")
    status = request.args.get("status")
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "desc")
    search = request.args.get("search", "").strip()

    # Single query to get campaigns for dropdown
    campaigns = (
        supabase.from_("campaigns")
        .select("code, title")
        .order("code", desc=False)
        .execute()
    )

    # Build query for candidates with campaign data
    query = supabase.from_("candidates").select("*, campaigns!inner(*)")

    # Apply search if provided
    if search:
        search_pattern = f"%{search.lower()}%"
        # Build the OR conditions string following PostgREST syntax
        query = query.or_(
            f"first_name.ilike.{search_pattern},"
            f"last_name.ilike.{search_pattern},"
            f"email.ilike.{search_pattern},"
            f"phone.ilike.{search_pattern}"
        )
        # Add campaign search as a separate filter

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
        "candidates/candidate_list.html",
        candidates=candidates.data,
        campaigns=campaigns.data,
    )


@candidate_bp.route("/<int:id>")
def view(id):
    try:
        # Get all data in a single query using the new function
        result = supabase.rpc(
            'get_candidate_with_tests',
            {'p_candidate_id': id}
        ).execute()

        if not result.data or not result.data[0]['candidate_data']:
            return jsonify({"error": "Candidate not found"}), 404

        candidate_data = result.data[0]['candidate_data']
        tests_data = result.data[0]['tests_data'] or {}

        # Process test data to add question count and total points
        for stage, test_data in tests_data.items():
            if test_data and 'questions' in test_data:
                # Calculate question count
                test_data['question_count'] = len(test_data['questions'])
                
                # Calculate total points
                total_points = sum(q['points'] for q in test_data['questions'])
                test_data['total_points'] = total_points
                
                # Calculate scored points
                scored_points = sum(
                    q['answer']['score'] 
                    for q in test_data['questions'] 
                    if q.get('answer') and q['answer'].get('score') is not None
                )
                test_data['scored_points'] = scored_points

                # Add started_at and completed_at from candidate data
                started_at_field = f"{stage.lower()}_started_at"
                completed_at_field = f"{stage.lower()}_completed_at"
                
                # Get timestamps and convert to datetime objects if they exist
                started_at = candidate_data.get(started_at_field)
                completed_at = candidate_data.get(completed_at_field)
                
                if started_at:
                    started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                if completed_at:
                    completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                
                test_data['started_at'] = started_at
                test_data['completed_at'] = completed_at

        return render_template(
            "candidates/view.html",
            candidate=candidate_data,
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
        
        # If candidate is rejected, determine their last completed stage
        if current_status == "REJECTED":
            if candidate.data["po3_score"] is not None:
                current_status = "PO3"
            elif candidate.data["po2_score"] is not None:
                current_status = "PO2"
            elif candidate.data["po1_score"] is not None:
                current_status = "PO1"
            else:
                return jsonify({
                    "success": False, 
                    "error": "Nie można określić ostatniego ukończonego etapu"
                }), 400
        
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
        current_time = datetime.now(timezone.utc)
        token_expiry = current_time + timedelta(days=7)
        formatted_expiry = token_expiry.astimezone(ZoneInfo("Europe/Warsaw")).strftime("%Y-%m-%d %H:%M")
        
        updates = {
            "recruitment_status": next_status,
            f"access_token_{next_status.lower()}_expires_at": token_expiry.isoformat(),
            f"access_token_{next_status.lower()}_is_used": False,
            'updated_at': current_time.isoformat()
        }
        
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