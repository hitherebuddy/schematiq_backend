from .gemini_service import gemini_service
from prompts import PromptLibrary
import uuid

# Mock database
from config import Config
db = Config.DATABASE

class PlanService:
    def get_user_plans(self, user_id):
        return [plan for plan in db['plans'].values() if plan.get('user_id') == user_id]

    def create_new_plan(self, user_id, user_input, mode, extras=None):
        prompt = PromptLibrary.generate_base_plan(user_input, mode, extras)
        plan_steps_json = gemini_service.generate_json_response(prompt)
        
        if isinstance(plan_steps_json, dict) and 'error' in plan_steps_json:
            return plan_steps_json

        plan_id = str(uuid.uuid4())
        new_plan = {
            "id": plan_id,
            "user_id": user_id,
            "title": user_input,
            "mode": mode,
            "steps": plan_steps_json,
            "created_at": "timestamp_placeholder"
        }
        
        db['plans'][plan_id] = new_plan
        return new_plan
        
    def toggle_step_status(self, plan_id, step_id):
        plan = db['plans'].get(plan_id)
        if not plan:
            return {"error": "Plan not found"}, 404

        step_found = False
        for step in plan.get('steps', []):
            if step.get('id') == step_id:
                step['is_complete'] = not step.get('is_complete', False)
                step_found = True
                break
        
        if not step_found:
            return {"error": "Step not found"}, 404
        
        return plan, 200

    def get_dynamic_replan(self, plan_id, step_id, outcome, reason=None):
        plan = db['plans'].get(plan_id)
        if not plan:
            return {"error": "Plan not found"}, 404

        import json
        plan_json_str = json.dumps(plan, indent=2)

        completed_step_title = ""
        for step in plan['steps']:
            if step['id'] == step_id:
                completed_step_title = step['title']
                break
        
        if not completed_step_title:
            return {"error": "Step to replan from not found"}, 404
        
        prompt = PromptLibrary.replan_based_on_outcome(plan_json_str, completed_step_title, outcome, reason)
        new_steps_json = gemini_service.generate_json_response(prompt)
        
        if 'error' in new_steps_json:
            return new_steps_json, 500

        original_steps = plan['steps']
        new_plan_steps = []
        for step in original_steps:
            if step['id'] == step_id:
                step['is_complete'] = True
                new_plan_steps.append(step)
            elif step['is_complete']:
                new_plan_steps.append(step)

        new_plan_steps.extend(new_steps_json)
        plan['steps'] = new_plan_steps
        
        return plan, 200

    def get_ai_step_assistance(self, step_description, user_question):
        prompt = PromptLibrary.ask_ai_on_step(step_description, user_question)
        return gemini_service.generate_text_response(prompt)

    def get_step_decomposition(self, parent_step_title):
        prompt = PromptLibrary.decompose_step(parent_step_title)
        return gemini_service.generate_json_response(prompt)

# Singleton instance
plan_service = PlanService()