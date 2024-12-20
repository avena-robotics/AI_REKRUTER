import secrets
from flask import Blueprint, render_template, request, jsonify, current_app
from routes.auth_routes import login_required
from services.candidate_service import CandidateService, CandidateException
from services.campaign_service import CampaignService, CampaignException
from common.logger import Logger
from common.recalculation_score_service import RecalculationScoreService

candidate_bp = Blueprint("candidate", __name__, url_prefix="/candidates")
logger = Logger.instance()

@candidate_bp.route("/")
@login_required
def list():
    try:
        campaign_code = request.args.get("campaign_code")
        status = request.args.get("status")
        sort_by = request.args.get("sort_by", "created_at")
        sort_order = request.args.get("sort_order", "desc")
        search = request.args.get("search", "").strip()
        
        candidates = CandidateService.get_candidates(
            campaign_code=campaign_code,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search
        )
        
        campaigns = CampaignService.get_campaigns_for_dropdown()
        
        return render_template(
            "candidates/candidate_list.html",
            candidates=candidates,
            campaigns=campaigns
        )
        
    except CandidateException as e:
        logger.error(f"Błąd podczas pobierania listy kandydatów: {str(e)}")
        return render_template(
            "candidates/candidate_list.html",
            candidates=[],
            campaigns=[],
            error_message=e.message
        )
    except Exception as e:
        logger.error(f"Nieznany błąd podczas pobierania listy kandydatów: {str(e)}")
        return render_template(
            "candidates/candidate_list.html",
            candidates=[],
            campaigns=[],
            error_message="Wystąpił nieznany błąd podczas pobierania listy kandydatów"
        )


@candidate_bp.route("/<int:id>")
def view(id):
    try:
        candidate_data = CandidateService.get_candidate_details(id)
        return render_template(
            "candidates/candidate_view.html",
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
        
        note = CandidateService.add_note(id, note_type, content)
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
        
        note = CandidateService.update_note(id, note_id, note_type, content)
        return jsonify({"success": True, "data": note})
        
    except CandidateException as e:
        return jsonify({"error": e.message}), 404
    except Exception as e:
        return jsonify({"error": "Wystąpił nieznany błąd podczas aktualizowania notatki"}), 500


@candidate_bp.route("/<int:id>/extend-token/<stage>", methods=["POST"])
@login_required
def extend_token(id, stage):
    try:
        new_expiry = CandidateService.extend_token(id, stage)
        return jsonify({
            "success": True,
            "message": "Token został przedłużony",
            "new_expiry": new_expiry.isoformat()
        })
        
    except CandidateException as e:
        return jsonify({
            "success": False,
            "error": e.message
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Wystąpił nieznany błąd podczas przedłużania tokenu"
        }), 500


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
