import secrets
from flask import Blueprint, render_template, request, jsonify, current_app, session
from routes.auth_routes import login_required
from services.candidate_service import CandidateService, CandidateException
from services.campaign_service import CampaignService, CampaignException
from services.group_service import get_user_groups
from common.logger import Logger
from common.recalculation_score_service import RecalculationScoreService
from common.email_service import EmailService
from common.config import Config
import json
from datetime import datetime

candidate_bp = Blueprint("candidate", __name__, url_prefix="/candidates")
logger = Logger.instance()

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

@candidate_bp.route("/")
@login_required
def list():
    try:
        # Get filter parameters from request
        campaign_codes = request.args.get("campaigns", "").split(",")
        statuses = request.args.get("statuses", "").split(",")
        search = request.args.get("search", "").strip()
        
        # Clean up empty values
        campaign_codes = [c for c in campaign_codes if c]
        statuses = [s for s in statuses if s]
        
        # Get user's groups
        user_id = session.get('user_id')
        user_groups = get_user_groups(user_id)
        user_group_ids = [group['id'] for group in user_groups]
        
        candidates = CandidateService.get_candidates(
            user_group_ids=user_group_ids,
            campaign_codes=campaign_codes,
            statuses=statuses,
            sort_by=request.args.get("sort_by", "created_at"),
            sort_order=request.args.get("sort_order", "desc"),
            search=search
        )
        
        campaigns = CampaignService.get_campaigns_for_dropdown()
        
        return render_template(
            "candidates/list.html",
            candidates=candidates,
            campaigns=campaigns
        )
        
    except CandidateException as e:
        logger.error(f"Błąd podczas pobierania listy kandydatów: {str(e)}")
        return render_template(
            "candidates/list.html",
            candidates=[],
            campaigns=[],
            error_message=e.message
        )
    except Exception as e:
        logger.error(f"Nieznany błąd podczas pobierania listy kandydatów: {str(e)}")
        return render_template(
            "candidates/list.html",
            candidates=[],
            campaigns=[],
            error_message="Wystąpił nieznany błąd podczas pobierania listy kandydatów"
        )


@candidate_bp.route("/<int:id>")
def view(id):
    try:
        candidate_data = CandidateService.get_candidate_details(id)
        return render_template(
            "candidates/views/details.html",
            **candidate_data
        )
        
    except CandidateException as e:
        logger.error(f"Błąd podczas pobierania danych kandydata {id}: {str(e)}")
        if "Nie znaleziono kandydata" in str(e):
            return jsonify({"error": e.message}), 404
        return jsonify({"error": e.message}), 500
        
    except Exception as e:
        logger.error(f"Nieznany błąd podczas pobierania danych kandydata {id}: {str(e)}")
        return jsonify({
            "error": "Wystąpił nieznany błąd podczas pobierania danych kandydata"
        }), 500


@candidate_bp.route("/<int:id>/interview-email-template")
@login_required
def get_interview_email_template(id):
    try:
        logger.info(f"Pobieranie szablonu email dla kandydata {id}")
        
        # Get candidate details
        candidate = CandidateService.get_candidate_email_data(id)
        logger.debug(f"Pobrano dane kandydata: {json.dumps(candidate, indent=2, cls=DateTimeEncoder)}")
        
        if not candidate:
            logger.error(f"Brak danych kandydata {id}")
            return jsonify({"error": "Nie znaleziono kandydata"}), 404
            
        campaign = candidate.get('campaign')
        if not campaign:
            logger.error(f"Brak danych kampanii dla kandydata {id}")
            return jsonify({"error": "Nie znaleziono kampanii dla kandydata"}), 404
            
        campaign_id = campaign.get('id')
        if not campaign_id:
            logger.error(f"Brak ID kampanii dla kandydata {id}")
            return jsonify({"error": "Nieprawidłowe dane kampanii"}), 404
        
        logger.info(f"Pobieranie szablonu email dla kampanii {campaign_id}")
        template = CampaignService.get_interview_email_template(campaign_id)
        logger.debug(f"Pobrany szablon: {json.dumps(template, indent=2, cls=DateTimeEncoder)}")
        
        return jsonify(template)
        
    except CandidateException as e:
        logger.error(f"Błąd podczas pobierania szablonu dla kandydata {id}: {str(e)}")
        if hasattr(e, 'original_error'):
            logger.error(f"Oryginalny błąd: {str(e.original_error)}")
        return jsonify({"error": str(e)}), 404
    except CampaignException as e:
        logger.error(f"Błąd podczas pobierania szablonu dla kandydata {id}: {str(e)}")
        if hasattr(e, 'original_error'):
            logger.error(f"Oryginalny błąd: {str(e.original_error)}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Nieznany błąd podczas pobierania szablonu email dla kandydata {id}: {str(e)}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return jsonify({"error": "Wystąpił błąd podczas pobierania szablonu email"}), 500


@candidate_bp.route("/<int:id>/next-stage", methods=["POST"])
@login_required
def next_stage(id):
    try:
        smtp_config = {
            "sender_email": current_app.config["SENDER_EMAIL"],
            "server": current_app.config["SMTP_SERVER"],
            "port": current_app.config["SMTP_PORT"],
            "username": current_app.config["SMTP_USERNAME"],
            "password": current_app.config["SMTP_PASSWORD"],
            "host_url": request.host_url
        }
        
        CandidateService.move_to_next_stage(id, smtp_config)
        return jsonify({"success": True})
        
    except CandidateException as e:
        return jsonify({"success": False, "error": e.message})


@candidate_bp.route("/<int:id>/reject", methods=["POST"])
@login_required
def reject(id):
    try:
        CandidateService.reject_candidate(id)
        return jsonify({"success": True})
        
    except CandidateException as e:
        return jsonify({"success": False, "error": e.message})
    except Exception as e:
        return jsonify({"success": False, "error": "Wystąpił nieznany błąd podczas odrzucania kandydata"}), 500


@candidate_bp.route("/<int:id>/accept", methods=["POST"])
@login_required
def accept(id):
    try:
        CandidateService.accept_candidate(id)
        return jsonify({"success": True})
        
    except CandidateException as e:
        return jsonify({"success": False, "error": e.message})
    except Exception as e:
        return jsonify({"success": False, "error": "Wystąpił nieznany błąd podczas akceptowania kandydata"}), 500


@candidate_bp.route("/<int:id>/send-interview-email", methods=["POST"])
@login_required
def send_interview_email(id):
    try:
        logger.info(f"Wysyłanie zaproszenia na rozmowę dla kandydata {id}")
        
        data = request.get_json()
        subject = data.get('subject')
        content = data.get('content')
        
        logger.debug(f"Dane żądania dla kandydata {id}: {json.dumps(data, indent=2)}")
        
        if not subject or not content:
            logger.error(f"Brak wymaganych pól dla kandydata {id}. Subject: {bool(subject)}, Content: {bool(content)}")
            return jsonify({"error": "Brak wymaganych pól"}), 400
            
        # Get candidate and campaign details
        candidate = CandidateService.get_candidate_email_data(id)
        logger.debug(f"Pobrano dane kandydata: {json.dumps(candidate, indent=2, cls=DateTimeEncoder)}")
        
        if not candidate:
            logger.error(f"Brak danych kandydata {id}")
            return jsonify({"error": "Nie znaleziono kandydata"}), 404
            
        campaign = candidate.get('campaign')
        if not campaign:
            logger.error(f"Brak danych kampanii dla kandydata {id}")
            return jsonify({"error": "Nie znaleziono kampanii dla kandydata"}), 404
            
        candidate_email = candidate.get('email')
        if not candidate_email:
            logger.error(f"Brak adresu email dla kandydata {id}")
            return jsonify({"error": "Brak adresu email kandydata"}), 400
        
        # Save template for future use
        logger.info(f"Aktualizacja szablonu email dla kampanii {campaign['id']}")
        CampaignService.update_interview_email_template(
            campaign['id'], 
            subject, 
            content
        )
        
        # Send email
        logger.info(f"Wysyłanie emaila do kandydata {id} na adres {candidate_email}")
        email_service = EmailService(Config.instance())
        success = email_service.send_interview_invitation(
            to_email=candidate_email,
            subject=subject,
            content=content,
            campaign_title=campaign['title']
        )
        
        if not success:
            logger.error(f"Nie udało się wysłać emaila do kandydata {id}")
            raise CandidateException("Nie udało się wysłać emaila")
            
        # Update candidate status
        logger.info(f"Aktualizacja statusu kandydata {id} na INVITED_TO_INTERVIEW")
        CandidateService.invite_to_interview(id)
        
        logger.info(f"Pomyślnie wysłano zaproszenie do kandydata {id}")
        return jsonify({"success": True})
        
    except (CandidateException, CampaignException) as e:
        logger.error(f"Błąd podczas wysyłania zaproszenia dla kandydata {id}: {str(e)}")
        if hasattr(e, 'original_error'):
            logger.error(f"Oryginalny błąd: {str(e.original_error)}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(f"Nieznany błąd podczas wysyłania zaproszenia dla kandydata {id}: {str(e)}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return jsonify({"error": "Wystąpił błąd podczas wysyłania zaproszenia"}), 500


@candidate_bp.route("/<int:id>/invite-to-interview", methods=["POST"])
@login_required
def invite_to_interview(id):
    try:
        CandidateService.invite_to_interview(id)
        return jsonify({"success": True})
        
    except CandidateException as e:
        return jsonify({"success": False, "error": e.message})
    except Exception as e:
        return jsonify({"success": False, "error": "Wystąpił nieznany błąd podczas zapraszania kandydata na rozmowę"}), 500


@candidate_bp.route("/<int:id>/set-awaiting-decision", methods=["POST"])
@login_required
def set_awaiting_decision(id):
    try:
        CandidateService.set_awaiting_decision(id)
        return jsonify({"success": True})
        
    except CandidateException as e:
        return jsonify({"success": False, "error": e.message})
    except Exception as e:
        return jsonify({"success": False, "error": "Wystąpił nieznany błąd podczas ustawiania statusu oczekiwania na decyzję"}), 500


@candidate_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    try:
        CandidateService.delete_candidate(id)
        return jsonify({"success": True})
        
    except CandidateException as e:
        return jsonify({"success": False, "error": e.message})
    except Exception as e:
        return jsonify({"success": False, "error": "Wystąpił nieznany błąd podczas usuwania kandydata"}), 500


@candidate_bp.route("/<int:id>/notes", methods=["POST"])
@login_required
def add_note(id):
    try:
        data = request.get_json()
        note_type = data.get('note_type')
        content = data.get('content')
        
        if not note_type or not content:
            return jsonify({"error": "Brak wymaganych pól"}), 400
        
        note = CandidateService.add_note(
            candidate_id=id, 
            note_type=note_type, 
            content=content,
            user_id=session['user_id'],
            user_email=session['user_email']
        )
        return jsonify({"success": True, "data": note})
        
    except CandidateException as e:
        return jsonify({"error": e.message}), 500
    except Exception as e:
        return jsonify({"error": "Wystąpił nieznany błąd podczas dodawania notatki"}), 500


@candidate_bp.route("/<int:id>/notes/<int:note_id>", methods=["DELETE"])
@login_required
def delete_note(id, note_id):
    try:
        CandidateService.delete_note(id, note_id)
        return jsonify({"success": True})
        
    except CandidateException as e:
        return jsonify({"error": e.message}), 404
    except Exception as e:
        return jsonify({"error": "Wystąpił nieznany błąd podczas usuwania notatki"}), 500


@candidate_bp.route("/<int:id>/notes/<int:note_id>", methods=["PUT"])
@login_required
def update_note(id, note_id):
    try:
        data = request.get_json()
        note_type = data.get('note_type')
        content = data.get('content')
        
        if not note_type or not content:
            return jsonify({"error": "Brak wymaganych pól"}), 400
        
        note = CandidateService.update_note(
            candidate_id=id, 
            note_id=note_id, 
            note_type=note_type, 
            content=content,
            user_id=session['user_id'],
            user_email=session['user_email']
        )
        return jsonify({"success": True, "data": note})
        
    except CandidateException as e:
        return jsonify({"error": e.message}), 404
    except Exception as e:
        return jsonify({"error": "Wystąpił nieznany błąd podczas aktualizowania notatki"}), 500


@candidate_bp.route("/<int:id>/recalculate", methods=["POST"])
@login_required
def recalculate_scores(id):
    try:
        result = CandidateService.recalculate_candidate_scores(id)
        return jsonify(result)
        
    except CandidateException as e:
        return jsonify({"success": False, "error": e.message}), 500
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": "Wystąpił nieznany błąd podczas przeliczania punktów"
        }), 500


@candidate_bp.route("/<int:id>/regenerate-token/<stage>", methods=["POST"])
@login_required
def regenerate_token(id, stage):
    try:
        logger.info(f"Rozpoczęcie regeneracji tokenu dla kandydata {id}, etap {stage}")
        result = CandidateService.regenerate_token(id, stage)
        logger.info(f"Token został wygenerowany: {result}")
        return jsonify(result)
        
    except CandidateException as e:
        logger.error(f"Błąd CandidateException podczas regeneracji tokenu: {str(e)}")
        return jsonify({
            "success": False,
            "error": e.message
        }), 500
    except Exception as e:
        logger.error(f"Nieoczekiwany błąd podczas regeneracji tokenu: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Wystąpił nieznany błąd podczas generowania nowego tokenu"
        }), 500


@candidate_bp.route("/<int:id>/notes/list")
@login_required
def get_notes_list(id):
    try:
        candidate_data = CandidateService.get_candidate_details(id)
        return render_template(
            'candidates/components/notes/list.html',
            notes_data=candidate_data['notes_data'],
            candidate={'id': id}
        )
        
    except CandidateException as e:
        return jsonify({"error": e.message}), 500
    except Exception as e:
        return jsonify({"error": "Wystąpił nieznany błąd podczas pobierania notatek"}), 500
