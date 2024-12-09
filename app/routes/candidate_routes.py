import secrets
from flask import Blueprint, render_template, request, jsonify, current_app
from database import supabase
from datetime import datetime, timedelta, timezone
from routes.auth_routes import login_required
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo
import logging

candidate_bp = Blueprint("candidate", __name__, url_prefix="/candidates")
logger = logging.getLogger('candidate_routes')


@candidate_bp.route("/")
@login_required
def list():
    logger.info("Rozpoczęcie pobierania listy kandydatów")
    campaign_code = request.args.get("campaign_code")
    status = request.args.get("status")
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "desc")
    search = request.args.get("search", "").strip()
    logger.debug(f"Parametry filtrowania: campaign={campaign_code}, status={status}, sort={sort_by} {sort_order}")

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
        logger.debug(f"Zastosowano wyszukiwanie: '{search}'")
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
    logger.info(f"Pobrano {len(candidates.data)} kandydatów")

    return render_template(
        "candidates/candidate_list.html",
        candidates=candidates.data,
        campaigns=campaigns.data,
    )


@candidate_bp.route("/<int:id>")
def view(id):
    logger.info(f"Rozpoczęcie pobierania szczegółów kandydata {id}")
    try:
        # Get all data in a single query using the function
        result = supabase.rpc(
            'get_candidate_with_tests',
            {'p_candidate_id': id}
        ).execute()

        if not result.data or not result.data[0]['candidate_data']:
            logger.warning(f"Nie znaleziono kandydata o ID {id}")
            return jsonify({"error": "Candidate not found"}), 404

        logger.debug(f"Pobrano dane kandydata {id} wraz z testami")
        candidate_data = result.data[0]['candidate_data']
        tests_data = result.data[0]['tests_data'] or {}
        notes_data = result.data[0]['notes_data'] or []

        # Process test data to add question count and total points
        logger.debug(f"Rozpoczęcie przetwarzania danych testów dla kandydata {id}")
        for stage, test_data in tests_data.items():
            logger.debug(f"Przetwarzanie testu dla etapu {stage}")
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
            "candidates/candidate_view.html",
            candidate=candidate_data,
            tests=tests_data,
            notes_data=notes_data,
        )

    except Exception as e:
        logger.error(f"Błąd podczas pobierania danych kandydata {id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@candidate_bp.route("/<int:id>/reject", methods=["POST"])
def reject(id):
    logger.info(f"Rozpoczęcie procesu odrzucenia kandydata {id}")
    try:
        result = (
            supabase.from_("candidates")
            .update({"recruitment_status": "REJECTED"})
            .eq("id", id)
            .execute()
        )
        logger.info(f"Kandydat {id} został odrzucony")
        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Błąd podczas odrzucania kandydata {id}: {str(e)}")
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
    logger.info(f"Rozpoczęcie procesu usuwania kandydata {id}")
    try:
        # First delete all candidate answers
        logger.debug(f"Usuwanie odpowiedzi kandydata {id}")
        supabase.from_("candidate_answers").delete().eq("candidate_id", id).execute()
        
        # Then delete the candidate
        logger.debug(f"Usuwanie danych kandydata {id}")
        supabase.from_("candidates").delete().eq("id", id).execute()
        
        logger.info(f"Kandydat {id} został pomyślnie usunięty")
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
    logger.info(f"Rozpoczęcie procesu przenoszenia kandydata {id} do następnego etapu")
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
            logger.warning(f"Nie znaleziono kandydata {id}")
            return jsonify({"success": False, "error": "Nie znaleziono kandydata"}), 404

        current_status = candidate.data["recruitment_status"]
        logger.debug(f"Obecny status kandydata {id}: {current_status}")
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

       
        logger.debug(f"Przygotowanie aktualizacji dla kandydata {id}") 
        updates = {
            "recruitment_status": next_status,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        if next_status in ["PO2", "PO3"] and test_id:
            logger.debug(f"Generowanie tokenu dla kandydata {id}")

            expiry_days = {
                'PO1': campaign.get('po1_token_expiry_days'),
                'PO2': campaign.get('po2_token_expiry_days'),
                'PO3': campaign.get('po3_token_expiry_days')
            }.get(current_status, 7) 
                
            current_time = datetime.now(timezone.utc)
            token_expiry = (current_time + timedelta(days=expiry_days)).replace(hour=23, minute=59, second=59)
            formatted_expiry = token_expiry.astimezone(ZoneInfo("Europe/Warsaw")).strftime("%Y-%m-%d %H:%M")
            
            updates = {
                f"access_token_{next_status.lower()}_expires_at": token_expiry.isoformat(),
                f"access_token_{next_status.lower()}_is_used": False,
                'updated_at': current_time.isoformat()
            }
            
            logger.info(f"Przygotowanie emaila z dostępem do testu dla kandydata {id}")
            # Generate token and expiry date
            token = secrets.token_urlsafe(32) 

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
                logger.debug(f"Wysyłanie emaila do kandydata {id}")
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
                logger.info(f"Email został wysłany do kandydata {id}")
            except Exception as e:
                logger.error(f"Błąd podczas wysyłania emaila do kandydata {id}: {str(e)}")
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

        logger.info(f"Kandydat {id} został przeniesiony do etapu {next_status}")
        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Błąd podczas przenoszenia kandydata {id} do następnego etapu: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500 


@candidate_bp.route("/<int:id>/notes", methods=["POST"])
@login_required
def add_note(id):
    try:
        data = request.get_json()
        note_type = data.get('note_type')
        content = data.get('content')
        
        if not note_type or not content:
            return jsonify({"error": "Brak wymaganych pól"}), 400
        
        # Insert note into database
        result = supabase.from_("candidate_notes").insert({
            "candidate_id": id,
            "note_type": note_type,
            "content": content
        }).execute()
        
        return jsonify({"success": True, "data": result.data[0]})
    
    except Exception as e:
        logger.error(f"Błąd podczas dodawania notatki: {str(e)}")
        return jsonify({"error": "Wystąpił błąd podczas zapisywania notatki"}), 500 


@candidate_bp.route("/<int:id>/notes/<int:note_id>", methods=["DELETE"])
@login_required
def delete_note(id, note_id):
    try:
        result = supabase.from_("candidate_notes").delete().eq("id", note_id).eq("candidate_id", id).execute()
        
        if not result.data:
            return jsonify({"error": "Notatka nie została znaleziona"}), 404
             
        return jsonify({"success": True})
    
    except Exception as e:
        logger.error(f"Błąd podczas usuwania notatki: {str(e)}")
        return jsonify({"error": "Wystąpił błąd podczas usuwania notatki"}), 500


@candidate_bp.route("/<int:id>/notes/<int:note_id>", methods=["PUT"])
@login_required
def update_note(id, note_id):
    try:
        data = request.get_json()
        note_type = data.get('note_type')
        content = data.get('content')
        
        if not note_type or not content:
            return jsonify({"error": "Brak wymaganych pól"}), 400
        
        result = (supabase.from_("candidate_notes")
                 .update({
                     "note_type": note_type,
                     "content": content,
                     "updated_at": datetime.now(timezone.utc).isoformat()
                 })
                 .eq("id", note_id)
                 .eq("candidate_id", id)
                 .execute())
        
        if not result.data:
            return jsonify({"error": "Notatka nie została znaleziona"}), 404
             
        return jsonify({"success": True, "data": result.data[0]})
    
    except Exception as e:
        logger.error(f"Błąd podczas aktualizacji notatki: {str(e)}")
        return jsonify({"error": "Wystąpił błąd podczas aktualizacji notatki"}), 500