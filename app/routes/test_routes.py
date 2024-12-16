import json
from flask import Blueprint, render_template, request, jsonify, session
from routes.auth_routes import login_required
from services.test_service import TestService, TestException
from services.group_service import get_user_groups
from logger import Logger 
import time
from database import supabase

test_bp = Blueprint("test", __name__, url_prefix="/tests")
logger = Logger.instance()

@test_bp.route("/")
@login_required
def list():
    try:
        user_id = session.get("user_id")
        
        # Get user groups
        try:
            user_groups = get_user_groups(user_id)
        except Exception as e:
            logger.error(f"Błąd podczas pobierania grup użytkownika: {str(e)}")
            raise TestException(
                message="Nie udało się pobrać grup użytkownika",
                original_error=e
            )

        # Get tests with details
        filtered_tests = TestService.get_tests_with_details(user_groups)
        
        return render_template(
            "tests/test_list.html", 
            tests=filtered_tests, 
            groups=user_groups
        )

    except TestException as e:
        logger.error(f"Błąd podczas pobierania testów: {str(e)}")
        return render_template(
            "tests/test_list.html",
            tests=[],
            groups=[],
            error_message=e.message
        )
    except Exception as e:
        logger.error(f"Nieznany błąd podczas pobierania testów: {str(e)}")
        return render_template(
            "tests/test_list.html",
            tests=[],
            groups=[],
            error_message="Wystąpił nieznany błąd podczas pobierania testów"
        )

@test_bp.route("/add", methods=["POST"])
@login_required
def add():
    try: 
        # Validate basic test data
        if not request.form.get("title"):
            logger.warning("Tytuł testu jest wymagany, ale nie został podany")
            return jsonify({"success": False, "error": "Tytuł testu jest wymagany"})

        groups = request.form.getlist("groups[]")
        if not groups:
            logger.warning("Nie wybrano żadnej grupy dla testu")
            return jsonify({"success": False, "error": "Należy wybrać co najmniej jedną grupę"})

        # Create test
        questions = json.loads(request.form.get('questions', '[]'))
        result = TestService.create_test(
            title=request.form.get("title"),
            test_type=request.form.get("test_type"),
            description=request.form.get("description"),
            passing_threshold=int(request.form.get("passing_threshold", 0)),
            time_limit_minutes=int(request.form.get("time_limit_minutes")) if request.form.get("time_limit_minutes") else None,
            groups=[int(g) for g in groups],
            questions=questions
        )

        return jsonify({
            "success": True, 
            "message": "Test został utworzony",
            "test_id": result["test_id"]
        })

    except TestException as e:
        return jsonify({"success": False, "error": e.message})
    except Exception as e:
        logger.error(f"Błąd podczas dodawania testu: {str(e)}")
        return jsonify({"success": False, "error": "Wystąpił nieoczekiwany błąd podczas dodawania testu."})


@test_bp.route("/<int:test_id>/data")
@login_required
def get_test_data(test_id):
    try:
        test_data = TestService.get_test_details(test_id)
        return jsonify(test_data)
        
    except TestException as e:
        return jsonify({"error": e.message}), 404
    except Exception as e:
        logger.error(f"Błąd podczas pobierania danych testu {test_id}: {str(e)}")
        return jsonify({"error": "Wystąpił błąd podczas pobierania danych testu"}), 500


@test_bp.route("/<int:test_id>/edit", methods=["POST", "PUT"])
@login_required
def edit(test_id):
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Convert groups list if present
            if 'groups[]' in request.form:
                data['groups'] = request.form.getlist('groups[]')
            # Parse questions if present
            if 'questions' in data:
                data['questions'] = json.loads(data['questions'])

        TestService.update_test(
            test_id=test_id,
            title=data.get("title"),
            test_type=data.get("test_type"),
            description=data.get("description"),
            passing_threshold=data.get("passing_threshold"),
            time_limit_minutes=data.get("time_limit_minutes"),
            groups=data.get("groups"),
            questions=data.get("questions")
        )
        
        return jsonify({"success": True})
        
    except TestException as e:
        return jsonify({"success": False, "error": e.message})
    except Exception as e:
        logger.error(f"Błąd podczas aktualizacji testu {test_id}: {str(e)}")
        return jsonify({
            "success": False, 
            "error": "Wystąpił nieoczekiwany błąd podczas aktualizacji testu."
        })


@test_bp.route("/<int:test_id>/delete", methods=["POST", "DELETE"])
@login_required
def delete_test(test_id):
    try:
        TestService.delete_test(test_id)
        return jsonify({"success": True})
        
    except TestException as e:
        return jsonify({"success": False, "error": e.message})
    except Exception as e:
        logger.error(f"Błąd podczas usuwania testu {test_id}: {str(e)}")
        return jsonify({
            "success": False, 
            "error": "Wystąpił nieoczekiwany błąd podczas usuwania testu."
        })


@test_bp.route("/add/questions", methods=["POST"])
@login_required
def add_questions():
    try:
        test_id = request.form.get("test_id")
        questions = json.loads(request.form.get("questions", "[]"))
        
        if not test_id:
            raise TestException(message="Brak parametru test_id")

        TestService.add_questions(int(test_id), questions)
        
        return jsonify({
            "success": True,
            "message": "Pytania zostały dodane"
        })

    except TestException as e:
        return jsonify({"success": False, "error": e.message})
    except Exception as e:
        logger.error(f"Błąd podczas dodawania pytań: {str(e)}")
        return jsonify({"success": False, "error": "Wystąpił nieoczekiwany błąd podczas dodawania pytań."})


@test_bp.route("/<int:test_id>/edit/questions", methods=["POST"])
@login_required
def edit_questions(test_id):
    try:
        questions = json.loads(request.form.get("questions", "[]"))
        TestService.edit_questions(test_id, questions)
        return jsonify({"success": True})
        
    except TestException as e:
        return jsonify({"success": False, "error": e.message})
    except Exception as e:
        logger.error(f"Błąd podczas edycji pytań testu {test_id}: {str(e)}")
        return jsonify({
            "success": False, 
            "error": "Wystąpił nieoczekiwany błąd podczas edycji pytań."
        })