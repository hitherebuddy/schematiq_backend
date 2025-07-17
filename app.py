from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from services.plan_service import plan_service
from services.auth_service import auth_service
from services.research_service import research_service
from services.gemini_service import gemini_service
from prompts import PromptLibrary
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# --- MOCK DATA SEEDING ---
def seed_data():
    """Create a sample plan for the mock user."""
    if not any(p for p in Config.DATABASE['plans'].values() if p['title'] == "Apartment Deep Clean"):
        plan_service.create_new_plan(user_id="mock_user_123", user_input="Apartment Deep Clean", mode="free")
    if not any(p for p in Config.DATABASE['plans'].values() if p['title'] == "Launch a new SaaS product"):
        plan_service.create_new_plan(user_id="mock_user_123", user_input="Launch a new SaaS product", mode="paid")

# --- API DECORATOR ---
def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        payload = auth_service.validate_token(token.split(" ")[1])
        if not payload:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(*args, **kwargs, current_user_payload=payload)
    decorated.__name__ = f.__name__
    return decorated

# --- API ROUTES ---

@app.route('/api/auth/get_token', methods=['GET'])
def get_token():
    """Mock endpoint to get a token. Can pass ?tier=free for testing."""
    user_tier = request.args.get('tier', 'paid') 
    token = auth_service.get_mock_token(tier=user_tier)
    return jsonify({"token": token, "tier": user_tier})

@app.route('/api/plans', methods=['GET'])
@token_required
def get_plans(current_user_payload):
    user_id = current_user_payload['user_id']
    plans = plan_service.get_user_plans(user_id)
    return jsonify(plans)

@app.route('/api/generate_plan', methods=['POST'])
@token_required
def generate_plan(current_user_payload):
    user_id = current_user_payload['user_id']
    data = request.get_json()
    if not data or 'user_input' not in data or 'mode' not in data:
        return jsonify({"error": "Missing user_input or mode"}), 400

    plan = plan_service.create_new_plan(
        user_id=user_id,
        user_input=data['user_input'],
        mode=data['mode'],
        extras=data.get('extras')
    )
    if isinstance(plan, dict) and "error" in plan:
        return jsonify(plan), 500
    return jsonify(plan), 201

@app.route('/api/plan/<plan_id>/step/<step_id>', methods=['PATCH'])
@token_required
def toggle_step(current_user_payload, plan_id, step_id):
    user_id = current_user_payload['user_id']
    plan = Config.DATABASE['plans'].get(plan_id)
    if not plan or plan.get('user_id') != user_id:
        return jsonify({"error": "Plan not found or unauthorized"}), 403

    result, status_code = plan_service.toggle_step_status(plan_id, step_id)
    return jsonify(result), status_code

@app.route('/api/plan/<plan_id>/step/<step_id>/replan', methods=['POST'])
@token_required
def replan_from_step(current_user_payload, plan_id, step_id):
    user_id = current_user_payload['user_id']
    data = request.get_json()
    if not data or 'outcome' not in data:
        return jsonify({"error": "Missing 'outcome' (success/failure) in request"}), 400

    plan = Config.DATABASE['plans'].get(plan_id)
    if not plan or plan.get('user_id') != user_id:
        return jsonify({"error": "Plan not found or unauthorized"}), 403

    reason = data.get('reason')
    result, status_code = plan_service.get_dynamic_replan(plan_id, step_id, data['outcome'], reason)
    return jsonify(result), status_code

@app.route('/api/plan/<plan_id>/simulate_agent', methods=['POST'])
@token_required
def simulate_agent(current_user_payload, plan_id):
    user_id = current_user_payload['user_id']
    data = request.get_json()
    if not data or 'persona' not in data or 'argument' not in data:
        return jsonify({"error": "Missing 'persona' or 'argument' in request"}), 400

    plan = Config.DATABASE['plans'].get(plan_id)
    if not plan or plan.get('user_id') != user_id:
        return jsonify({"error": "Plan not found or unauthorized"}), 403

    plan_json_str = json.dumps(plan, indent=2)
    prompt = PromptLibrary.agent_simulation(plan_json_str, data['persona'], data['argument'])
    response = gemini_service.generate_text_response(prompt)
    return jsonify({"agent_response": response})

@app.route('/api/plan/<plan_id>/forecast', methods=['GET'])
@token_required
def get_plan_forecast(current_user_payload, plan_id):
    user_id = current_user_payload['user_id']
    plan = Config.DATABASE['plans'].get(plan_id)
    if not plan or plan.get('user_id') != user_id:
        return jsonify({"error": "Plan not found or unauthorized"}), 403

    forecast_data = []
    current_date = datetime.now()
    for step in plan['steps']:
        estimate_obj = step.get('time_estimate', {'min': 1, 'max': 1, 'unit': 'days'})
        avg_duration = (estimate_obj.get('min', 1) + estimate_obj.get('max', 1)) / 2
        
        if estimate_obj.get('unit') == 'weeks':
            duration_delta = timedelta(weeks=avg_duration)
        elif estimate_obj.get('unit') == 'hours':
            duration_delta = timedelta(hours=avg_duration)
        else:
            duration_delta = timedelta(days=avg_duration)

        end_date = current_date + duration_delta
        forecast_data.append({
            "step_title": step['title'],
            "start_date": current_date.isoformat(),
            "end_date": end_date.isoformat(),
            "effort": step.get('effort', 'medium'),
            "is_milestone": step.get('is_milestone', False)
        })
        current_date = end_date + timedelta(days=1)
    return jsonify(forecast_data)

@app.route('/api/discover_idea', methods=['POST'])
@token_required
def discover_idea(current_user_payload):
    data = request.get_json()
    if not data or 'niche' not in data:
        return jsonify({"error": "Missing 'niche' in request"}), 400
    prompt = PromptLibrary.discover_idea(data['niche'])
    idea = gemini_service.generate_text_response(prompt)
    return jsonify({"idea": idea})

@app.route('/api/research', methods=['POST'])
@token_required
def research(current_user_payload):
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Missing 'query' in request"}), 400
    query = data['query']
    result = research_service.perform_research(query)
    if isinstance(result, dict) and 'error' in result:
        return jsonify(result), 500
    return jsonify({"research_summary": result})

@app.route('/api/decompose_step', methods=['POST'])
@token_required
def decompose_step(current_user_payload):
    data = request.get_json()
    if not data or 'parent_step_title' not in data:
        return jsonify({"error": "Missing parent_step_title"}), 400
    result = plan_service.get_step_decomposition(data['parent_step_title'])
    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 500
    return jsonify({"micro_steps": result})

# --- APP RUN ---
if __name__ == '__main__':
    with app.app_context():
        seed_data()
    app.run(host='0.0.0.0', port=5000, debug=True)